#!/usr/bin/env python3
"""TASK-0257, rung R2 -- real burial (SASA) vs. `degree_centrality` as the
burial proxy, scored against the same label-free objective as R1: real
deposited B-factor.

Motivation, from the task's own filing: `degree_centrality` is a *poor*
burial proxy -- it scores below 0.5 on 6/9 targets ([[TASK-0246]]). This is
a feature swap, not an ENM change (R2 does not touch the Kirchhoff/GNM
machinery at all, unlike R1), so it is scored directly: buried residues are
expected to be *less* flexible (lower B-factor) than exposed ones, so real
solvent-accessible surface area (SASA, more exposed = higher) should
correlate NEGATIVELY with B-factor, and a *better* burial proxy should
produce a *stronger* |correlation| with B-factor than `degree` (the binary
Cα-contact-count burial proxy `potentials.V_R` actually uses) does. Same 15
targets, same PASS/MARGINAL/FAIL bars, reapplied to |r| against B-factor
directly (not GNM MSF, since neither degree nor SASA is a dynamical
prediction on its own -- they are static burial estimates, exactly what
[[TASK-0250]]'s objective is set up to gate).

Reuses, does not re-derive:
  - `allostery.corex.per_atom_asa`/`per_residue_native_asa` -- the same
    validated BioPython `ShrakeRupley` wrapper [[TASK-0229.006]] already
    uses, not a new SASA implementation.
  - `backend.data_layer.fetch` + `Bio.PDB.PDBParser` -- the exact local-
    file-fetch + parse pattern [[TASK-0229.006]]/[[TASK-0229.007]] use.
  - `allostery.hamiltonians.contact_matrix(weight="binary")` for `degree`
    -- the same quantity `potentials.V_R`/`gnm_context` actually feed into
    H_new, not a re-derived approximation of it.
  - [[TASK-0250]]'s own target list, cutoffs, and unusable-B-factor flag.

Run: ../.venv/bin/python3 scripts/task0257_r2_sasa_burial_vs_degree.py
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
from scipy.stats import pearsonr, spearmanr

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_REPO_ROOT = _ROOT.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import Bio.PDB as PDB  # noqa: E402

from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.corex import per_atom_asa, per_residue_native_asa  # noqa: E402
from allostery.hamiltonians import contact_matrix  # noqa: E402
from backend.data_layer import fetch  # noqa: E402

TARGETS = [
    "KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "CARDIAC_MYOSIN_TABLE1",
    "MYC_MAX", "PTP1B", "GLUCOKINASE", "ATCase", "CASPASE1", "CASPASE7",
    "HEMOGLOBIN", "TAR_RECEPTOR", "GLYCOGEN_PHOSPHORYLASE", "PFK", "GROEL_SUBUNIT",
]
UNUSABLE_BFACTORS = {
    "CARDIAC_MYOSIN_TABLE1": (
        "apo 5TBY is ELECTRON MICROSCOPY, nominal resolution 20.0 A -- "
        "no meaningful per-atom B-factor refinement; excluded from the "
        "pass/fail tally, reported for transparency only (same exclusion "
        "TASK-0250 applied)."
    ),
}
PASS_BAR = 0.6
MARGINAL_BAR = 0.4


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def verdict(abs_r: float) -> str:
    if abs_r >= PASS_BAR:
        return "PASS"
    if abs_r >= MARGINAL_BAR:
        return "MARGINAL"
    return "FAIL"


def per_residue_sasa(cfg: dict, apo) -> np.ndarray:
    """SASA per residue, aligned to `apo.resnums`/`apo.chain_ids` order.
    Computed on the FULL deposited model (every chain), matching the
    biological context SASA needs, then indexed down to only the residues
    `apo` itself kept (same chain-selection convention `clean_from_config`
    already applied for this target)."""
    fp = fetch(cfg["apo_pdb"])
    structure = PDB.PDBParser(QUIET=True).get_structure(cfg["apo_pdb"], fp)
    model = structure[0]
    per_atom_asa(model)
    asa_by_key: dict[tuple[str, int], float] = {}
    for chain in model:
        for resnum, asa in per_residue_native_asa(chain).items():
            asa_by_key[(chain.id, int(resnum))] = asa

    resn = np.asarray(apo.resnums)
    chids = np.asarray(apo.chain_ids)
    out = np.full(len(resn), np.nan)
    for i, (c, r) in enumerate(zip(chids, resn)):
        out[i] = asa_by_key.get((str(c), int(r)), np.nan)
    return out


def compute_target(target_name: str) -> dict:
    t0 = time.monotonic()
    cfg = load_target_config(target_name)
    apo = clean_from_config(target_name, role="apo")
    coords = apo.coords.astype(float)
    bfactors = apo.bfactors
    cutoff = float(cfg["enm_cutoff"])

    A = contact_matrix(coords, cutoff=cutoff, weight="binary")
    degree = A.sum(axis=1)

    sasa = per_residue_sasa(cfg, apo)

    valid = ~np.isnan(bfactors) & ~np.isnan(sasa)
    n_sasa_nan = int(np.isnan(sasa).sum())

    pear_deg, p_deg = pearsonr(degree[valid], bfactors[valid])
    sp_deg, _ = spearmanr(degree[valid], bfactors[valid])
    pear_sasa, p_sasa = pearsonr(sasa[valid], bfactors[valid])
    sp_sasa, _ = spearmanr(sasa[valid], bfactors[valid])

    elapsed = time.monotonic() - t0
    result = dict(
        target=target_name, apo_pdb=cfg["apo_pdb"], N=len(coords),
        n_sasa_unmapped=n_sasa_nan,
        pearson_degree=float(pear_deg), pearson_p_degree=float(p_deg),
        spearman_degree=float(sp_deg), verdict_degree=verdict(abs(pear_deg)),
        pearson_sasa=float(pear_sasa), pearson_p_sasa=float(p_sasa),
        spearman_sasa=float(sp_sasa), verdict_sasa=verdict(abs(pear_sasa)),
        delta_abs_pearson=float(abs(pear_sasa) - abs(pear_deg)),
        unusable_reason=UNUSABLE_BFACTORS.get(target_name),
        elapsed_s=round(elapsed, 2),
    )
    flag = " [UNUSABLE B-FACTORS]" if target_name in UNUSABLE_BFACTORS else ""
    _log(f"{target_name} ({cfg['apo_pdb']}, N={len(coords)}, sasa_unmapped={n_sasa_nan}): "
         f"degree r={pear_deg:+.3f} ({result['verdict_degree']})  "
         f"SASA r={pear_sasa:+.3f} ({result['verdict_sasa']})  "
         f"delta|r|={result['delta_abs_pearson']:+.3f}  [{elapsed:.1f}s]{flag}")
    return result


def main() -> int:
    results = []
    for name in TARGETS:
        results.append(compute_target(name))

    out_dir = _ROOT / "results" / "tasks" / "0257_r2_sasa_burial_vs_degree"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "r2_results.json"
    json.dump(
        dict(pass_bar=PASS_BAR, marginal_bar=MARGINAL_BAR, results=results),
        open(out_path, "w"), indent=1,
    )
    _log(f"wrote {out_path}")

    scored = [r for r in results if r["unusable_reason"] is None]
    print(f"\n{'target':24s} {'N':>5s} {'degree r':>10s} {'degree':>10s} "
          f"{'SASA r':>10s} {'SASA':>10s} {'delta|r|':>9s}")
    print("-" * 85)
    for r in results:
        flag = " *UNUSABLE*" if r["unusable_reason"] else ""
        print(f"{r['target']:24s} {r['N']:5d} {r['pearson_degree']:+10.3f} {r['verdict_degree']:>10s} "
              f"{r['pearson_sasa']:+10.3f} {r['verdict_sasa']:>10s} {r['delta_abs_pearson']:+9.3f}{flag}")

    n_pass_d = sum(1 for r in scored if r["verdict_degree"] == "PASS")
    n_marg_d = sum(1 for r in scored if r["verdict_degree"] == "MARGINAL")
    n_fail_d = sum(1 for r in scored if r["verdict_degree"] == "FAIL")
    n_pass_s = sum(1 for r in scored if r["verdict_sasa"] == "PASS")
    n_marg_s = sum(1 for r in scored if r["verdict_sasa"] == "MARGINAL")
    n_fail_s = sum(1 for r in scored if r["verdict_sasa"] == "FAIL")
    print(f"\ndegree (baseline burial proxy): {n_pass_d} PASS, {n_marg_d} MARGINAL, {n_fail_d} FAIL (of {len(scored)})")
    print(f"SASA (candidate burial proxy):  {n_pass_s} PASS, {n_marg_s} MARGINAL, {n_fail_s} FAIL (of {len(scored)})")
    n_sasa_better = sum(1 for r in scored if r["delta_abs_pearson"] > 0)
    print(f"\nSASA beats degree (|r| higher) on {n_sasa_better}/{len(scored)} targets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
