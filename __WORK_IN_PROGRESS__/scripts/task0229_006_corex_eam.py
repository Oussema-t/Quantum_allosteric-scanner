#!/usr/bin/env python3
"""TASK-0229.006 -- COREX-style Ensemble Allosteric Model (EAM) on
KRAS_G12C + PTP1B (the two TASK-0209-VALID targets, per this task's own
Constraint that an unvalidatable target -- c-Myc, no holo structure --
must not become the headline).

Three steps, in the order the task's own Planned Validation requires:

1. **Sanity check**: kappa_f must be higher for buried/core residues than
   exposed/surface residues (a textbook-level, well-characterised
   qualitative expectation) before any coupling number is trusted.
2. **Coupling score**: for every residue j, "stabilise" j (mimicking
   ligand binding) and measure the resulting shift in the active site's
   own stability (dG_f) -- ranks every residue by how much perturbing it
   destabilises the active site.
3. **Decisive negative control** (this task's own, and the register's own
   right one): does this EAM-based ranking of candidate sites *disagree*
   with a propagation-based ranking (hop-distance from the active site,
   this project's own established proximity baseline)? If they agree
   everywhere (high correlation), EAM adds nothing new here and the
   register's existing propagation-based picture already captures it.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    import os
    os.environ.setdefault(_v, "4")

import numpy as np
from scipy.stats import spearmanr

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import Bio.PDB as PDB  # noqa: E402

from allostery.baselines import hop_from_seed  # noqa: E402
from allostery.corex import (  # noqa: E402
    apolar_max_asa_fraction, build_folding_windows, per_atom_asa,
    per_residue_apolar_native_asa, per_residue_native_asa, window_free_energy,
    R_GAS, TEMPERATURE,
)
from backend.data_layer import fetch  # noqa: E402
from backend.systems import SYSTEMS  # noqa: E402

TARGETS = {
    "KRAS_G12C": dict(pdb="4OBE", chain="A"),
    "PTP1B": dict(pdb="1SUG", chain="A"),
}


def run_sanity_check(model, chain_id: str) -> dict:
    from allostery.corex import corex_ensemble

    kf = corex_ensemble(model, chain_id)
    per_atom_asa(model)
    native_asa = per_residue_native_asa(model[chain_id])
    resnums = sorted(kf.keys())
    asa_vals = np.array([native_asa.get(rn, np.nan) for rn in resnums])
    kf_vals = np.array([kf[rn] for rn in resnums])
    finite = np.isfinite(kf_vals) & np.isfinite(asa_vals)
    rho, p = spearmanr(asa_vals[finite], np.log10(np.clip(kf_vals[finite], 1e-300, None)))
    q25, q75 = np.nanpercentile(asa_vals, [25, 75])
    buried = asa_vals <= q25
    exposed = asa_vals >= q75
    return {
        "spearman_rho_asa_vs_log_kappa_f": round(float(rho), 4),
        "spearman_p": float(p),
        "buried_mean_log10_kappa_f": round(float(np.log10(np.clip(kf_vals[buried], 1e-300, None)).mean()), 3),
        "exposed_mean_log10_kappa_f": round(float(np.log10(np.clip(kf_vals[exposed], 1e-300, None)).mean()), 3),
        "passes": bool(rho < 0 and p < 0.01),  # higher ASA -> lower stability, must be negative and significant
    }


def run_all_candidate_couplings(model, chain_id: str, active_site_resnums: list,
                                 window_sizes=(6, 10, 15), stabilization_bonus: float = 3.0) -> dict:
    """Faster, batched re-implementation of `corex.coupling_score` for
    every candidate residue at once (candidate-by-candidate re-derivation
    of the full ensemble would be the same math, just slower to call
    repeatedly) -- computes the SAME two-term free energy `corex.py`
    itself uses, verified to match it on a spot check before use here."""
    per_atom_asa(model)
    chain = model[chain_id]
    resnums = sorted(r.id[1] for r in chain if r.id[0] == " ")
    resnames = {r.id[1]: r.resname for r in chain if r.id[0] == " "}
    native_total_asa = per_residue_native_asa(chain)
    native_apolar_asa = per_residue_apolar_native_asa(chain)
    apolar_max = {
        rn: apolar_max_asa_fraction(resnames[rn], native_apolar_asa.get(rn, 0.0), native_total_asa.get(rn, 0.0))
        for rn in resnums
    }
    windows = build_folding_windows(resnums, window_sizes)
    base_dg = np.array([
        window_free_energy(w, native_apolar_asa, apolar_max, n_conf_residues=len(w), temperature=TEMPERATURE)
        for w in windows
    ])
    window_sets = [set(w) for w in windows]

    def _dgf_active_site(dg_array):
        weights = np.exp(-dg_array / (R_GAS * TEMPERATURE))
        folded = 1.0
        unfolded = 0.0
        for w_set, k in zip(window_sets, weights):
            if w_set & active_set:
                unfolded += k
            else:
                folded += k
        kf = folded / unfolded if unfolded > 0 else float("inf")
        return -R_GAS * TEMPERATURE * np.log(kf) if np.isfinite(kf) and kf > 0 else float("-inf")

    active_set = set(active_site_resnums)
    native_dgf_active = _dgf_active_site(base_dg)

    coupling = {}
    for j in resnums:
        touched = np.array([j in w_set for w_set in window_sets])
        perturbed_dg = base_dg + np.where(touched, stabilization_bonus, 0.0)
        perturbed_dgf_active = _dgf_active_site(perturbed_dg)
        if np.isfinite(perturbed_dgf_active) and np.isfinite(native_dgf_active):
            coupling[j] = perturbed_dgf_active - native_dgf_active
    return coupling


def run_one(name: str, cfg: dict) -> dict:
    t0 = time.monotonic()
    sysinfo = SYSTEMS[name]
    active_site = sysinfo["active_site"]

    fp = fetch(cfg["pdb"])
    structure = PDB.PDBParser(QUIET=True).get_structure(cfg["pdb"], fp)
    model = structure[0]

    sanity = run_sanity_check(model, cfg["chain"])
    print(f"{name}: sanity check -- {sanity}")
    if not sanity["passes"]:
        return {"target": name, "error": "sanity check failed -- coupling numbers not trusted", "sanity": sanity}

    coupling = run_all_candidate_couplings(model, cfg["chain"], active_site)
    resnums = sorted(coupling.keys())
    eam_scores = np.array([coupling[rn] for rn in resnums])

    coords = np.array([r["CA"].coord for r in model[cfg["chain"]] if r.id[0] == " " and "CA" in r and r.id[1] in coupling])
    active_idx_in_coupling = [i for i, rn in enumerate(resnums) if rn in set(active_site)]
    hop = -hop_from_seed(coords, active_idx_in_coupling, cutoff=10.0)  # negate hop_from_seed's own "-dist" convention back to real hop counts

    finite_mask = np.isfinite(eam_scores) & np.isfinite(hop)
    rho, p = spearmanr(eam_scores[finite_mask], hop[finite_mask])

    order = np.argsort(eam_scores)[::-1]
    top10_eam = [(int(resnums[i]), round(float(eam_scores[i]), 4)) for i in order[:10]]

    result = {
        "target": name, "n_residues": len(resnums), "n_active_site": len(active_site),
        "sanity": sanity,
        "eam_vs_propagation_spearman_rho": round(float(rho), 4), "eam_vs_propagation_p": float(p),
        "top10_eam_coupling_sites": top10_eam,
        "elapsed_s": round(time.monotonic() - t0, 1),
    }
    print(f"{name}: EAM-vs-propagation rho={rho:.4f} (p={p:.2e}), top EAM sites {top10_eam[:5]}")
    return result


def main() -> int:
    results = {}
    for name, cfg in TARGETS.items():
        try:
            results[name] = run_one(name, cfg)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            results[name] = {"target": name, "error": str(exc)}

    out_dir = Path(__file__).resolve().parent.parent / "results/tasks/0229.006"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "corex_eam_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"wrote {out_dir / 'corex_eam_results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
