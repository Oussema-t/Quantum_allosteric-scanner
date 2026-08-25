#!/usr/bin/env python3
"""TASK-0252 -- H4.3 (Motlagh et al. 2014): does intrinsic disorder AMPLIFY
allosteric coupling? Tested here using this project's own already-validated
EAM/COREX machinery ([[TASK-0229.006]]), not a new external disorder
predictor (IUPred/metapredict are not installed in this offline
environment -- checked directly before choosing the fallback the task's
own Scope explicitly allows).

Disorder proxy: kappa_f itself (`allostery.corex.corex_ensemble`), the
EAM's own native per-residue stability constant -- LOWER kappa_f means a
residue spends more of the ensemble's Boltzmann weight in locally-unfolded
microstates, i.e. more locally disordered, by the same formalism this
task's own H4.3/H4.4 claims are stated in. This is a more theoretically
faithful proxy than an external sequence-based disorder predictor would
be for THIS specific claim, since H4.3 is itself an EAM-internal
prediction, not a generic IDR claim.

Reuses `task0229_006_corex_eam.py`'s own `run_all_candidate_couplings`
(coupling[j], the aggregate active-site dG shift from stabilizing j) and
`corex_ensemble` (kappa_f) UNCHANGED -- both already validated
(TASK-0229.006's own sanity check, buried-vs-exposed kappa_f, p<1e-6 both
targets). H4.3's own prediction: |coupling[j]| should be LARGER for
LOWER kappa_f(j) (more disordered candidates couple more strongly) --
tested via Spearman(kappa_f, |coupling|), predicted sign NEGATIVE.
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

_SCRIPTS = Path(__file__).resolve().parent
_SRC = _SCRIPTS.parent / "src"
_ROOT = _SCRIPTS.parent.parent
for _p in (_SRC, _SCRIPTS, _ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import Bio.PDB as PDB  # noqa: E402

from allostery.corex import corex_ensemble  # noqa: E402
from backend.data_layer import fetch  # noqa: E402
from backend.systems import SYSTEMS  # noqa: E402

from task0229_006_corex_eam import TARGETS, run_all_candidate_couplings, run_sanity_check  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0252_h4_3_disorder_coupling"


def run_one(name: str, cfg: dict) -> dict:
    t0 = time.monotonic()
    sysinfo = SYSTEMS[name]
    active_site = sysinfo["active_site"]

    fp = fetch(cfg["pdb"])
    structure = PDB.PDBParser(QUIET=True).get_structure(cfg["pdb"], fp)
    model = structure[0]

    sanity = run_sanity_check(model, cfg["chain"])
    if not sanity["passes"]:
        return {"target": name, "error": "sanity check failed", "sanity": sanity}

    kf = corex_ensemble(model, cfg["chain"])
    coupling = run_all_candidate_couplings(model, cfg["chain"], active_site)

    common = sorted(set(kf.keys()) & set(coupling.keys()) - set(active_site))
    kf_vals = np.array([kf[j] for j in common])
    coupling_vals = np.array([coupling[j] for j in common])
    abs_coupling = np.abs(coupling_vals)

    finite = np.isfinite(kf_vals) & np.isfinite(abs_coupling) & (kf_vals > 0)
    log_kf = np.log10(kf_vals[finite])
    rho, p = spearmanr(log_kf, abs_coupling[finite])

    # disorder-variation power check: is there enough spread in kappa_f
    # (this target's own local-disorder proxy) to have any chance of
    # detecting a real effect, or is the whole structure uniformly ordered?
    log_kf_all = np.log10(np.clip(kf_vals, 1e-300, None))
    iqr = float(np.percentile(log_kf_all, 75) - np.percentile(log_kf_all, 25))

    result = {
        "target": name, "n_candidates": int(finite.sum()),
        "spearman_rho_log_kappa_f_vs_abs_coupling": round(float(rho), 4),
        "spearman_p": float(p),
        "predicted_sign": "negative (lower kappa_f / more disorder -> larger |coupling|)",
        "sign_matches_prediction": bool(rho < 0),
        "log10_kappa_f_iqr": round(iqr, 3),
        "log10_kappa_f_range": [round(float(log_kf_all.min()), 2), round(float(log_kf_all.max()), 2)],
        "elapsed_s": round(time.monotonic() - t0, 1),
    }
    print(f"{name}: rho={rho:.4f} p={p:.4f} sign_matches={result['sign_matches_prediction']} "
          f"log10(kappa_f) IQR={iqr:.2f} range={result['log10_kappa_f_range']}")
    return result


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, cfg in TARGETS.items():
        try:
            results[name] = run_one(name, cfg)
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            results[name] = {"target": name, "error": f"{type(exc).__name__}: {exc}"}
    (OUT_DIR / "results.json").write_text(json.dumps(results, indent=2, default=str))
    print(f"wrote {OUT_DIR / 'results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
