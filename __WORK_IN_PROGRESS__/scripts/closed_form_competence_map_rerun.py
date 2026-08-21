#!/usr/bin/env python3
"""TASK-0130 -- re-run floor/ceiling/actual (the competence-map numbers)
under `time_averaged_ctqw_converged`'s exact infinite-time closed form,
superseding every prior t_max/t*/n_steps convention for this quantity at
once (TASK-0108/0109/0110/0117/0119/0129, Q-0003).

**Why this fully replaces the clock question, not just adjusts it**:
TASK-0110 measured that `min_adequate_t_max(kind="time_averaged_ctqw")`'s
own AAKV-derived criterion is computationally infeasible to satisfy with
`time_averaged_ctqw`'s O(n_steps) time loop (145,000x-3,950,000x the
shipped `t_max=15` default; a single call did not return after 2+ hours).
This script uses `analysis.benchmark`/`analysis.quantum_vs_classical`/
`analysis.operator_sweep`/`ceiling.consistency_score`/`ceiling.
ceiling_search`'s new `use_converged_limit=True` option (TASK-0130) --
the closed form, no `t_max`/`n_steps`/`t*` to choose, derive, or disclose
for the `"ctqw"` propagator at all. `ground_state_relaxation`'s own,
separate, unaffected convergence criterion still uses `t_max=15` (this
task's own Out Of Scope: "Changing ground_state_relaxation's own
convergence criterion or default t_max").

Standalone script, not an edit to `run_challenge.py`'s live defaults --
same reasoning as `combined_competence_map_rerun.py` (TASK-0129): this
calls the same underlying functions the live pipeline calls, with the
new closed-form option, without promoting a research convention into the
live submission pipeline's defaults (a Tier-2-adjacent decision,
TASK-0100).

TASK-0112's bootstrap CI (`diagnostics.classify_failure(return_ci=True)`)
is already wired into `protocol.run_frozen_verdict`'s own return value
(`_diagnosis_score_ci`/`_diagnosis_floor_ci`/`_diagnosis_ci_overlap`) --
this script surfaces those directly for "actual", and additionally
attaches a `metrics.block_bootstrap_ci` to the ceiling's own winning
trial and the floor's own winning baseline (the same mechanism, applied
at the two other headline-AUC sites this task's own Intent Contract
names), rather than doing a second, separate CI-only pass afterward.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.ceiling import ceiling_search  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.metrics import auc as _auc, block_bootstrap_ci  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from allostery.protocol import run_frozen_verdict  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo/DEFAULT_CUTOFF

DEFAULT_CUTOFF = run_challenge.DEFAULT_CUTOFF
DEFAULT_POCKET_CUTOFF = run_challenge.DEFAULT_POCKET_CUTOFF
CEILING_N_TRIALS = 60
CEILING_SEED = 7
CI_N_BOOT = 1000
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0130_competence"


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run_target(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))

    from allostery.labels import build_labels

    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None:
        raise RuntimeError(f"no resolvable pocket for {target_name!r}")

    active_site_idx = np.where(labels_obj.active_site)[0]
    if len(active_site_idx) == 0:
        raise RuntimeError(f"no active-site residues resolved for {target_name!r}")
    source = np.sort(active_site_idx)  # TASK-0118 full array
    pocket_int = labels_obj.pocket.astype(int)

    _log(f"{target_name}: N={len(apo.resnums)} n_seed={len(source)} -- no t_max/t* to derive (closed form)")

    # --- floor -------------------------------------------------------
    floor_candidates = [
        degree_centrality(apo.coords, cutoff=cutoff),
        euclid_from_seed_centroid(apo.coords, source),
        hop_from_seed(apo.coords, source, cutoff=cutoff),
    ]
    floor_aucs = [_auc(f, pocket_int) for f in floor_candidates]
    floor_idx = int(np.argmax(floor_aucs))
    floor = float(floor_aucs[floor_idx])
    floor_ci = block_bootstrap_ci(floor_candidates[floor_idx], pocket_int, n_boot=CI_N_BOOT, rng=np.random.default_rng(0))

    # --- actual (run_frozen_verdict, use_converged_limit=True) -------
    def build_candidates():
        # `select_frozen_config`'s own internal `unsupervised_score`
        # ranking (label-free candidate selection, deliberately
        # unaffected by this task -- see `run_frozen_verdict`'s own
        # `use_converged_limit` docstring) requires a `"t"` per candidate
        # for its `focusing`/`source_specificity` heuristics; unrelated
        # to the *reported* AUC (which uses the closed form regardless of
        # this value), so the plain shipped default is used rather than
        # deriving a new one -- this task does not touch candidate
        # selection, only what gets reported once a candidate has won.
        H_new = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
        from allostery.hamiltonians import build_H10
        H10 = build_H10(apo.coords, apo.bfactors, cutoff=cutoff)
        return [
            {"H": H_new, "source": source, "t": 15.0, "name": "H_new_default"},
            {"H": H10, "source": source, "t": 15.0, "name": "H10_disorder_suppressed"},
        ]

    t0 = time.monotonic()
    result = run_frozen_verdict(
        target_name, build_candidates,
        apo.coords, apo.bfactors, source, labels_obj.pocket,
        cutoff=cutoff, floor_scores=floor_candidates, coherent=False,
        use_converged_limit=True,
    )
    actual_auc = result.get("AUC_apo_Hnew_optimised")
    _log(
        f"{target_name}: actual (closed-form) AUC={actual_auc} diagnosis={result.get('_diagnosis')} "
        f"in {time.monotonic()-t0:.1f}s"
    )

    # --- ceiling (ceiling_search, use_converged_limit=True) ----------
    t0 = time.monotonic()
    ceiling_result = ceiling_search(
        target_name, apo.coords, apo.bfactors, source, labels_obj.pocket,
        n_trials=CEILING_N_TRIALS, seed=CEILING_SEED, coherent=False,
        use_converged_limit=True,
    )
    ceiling_auc = ceiling_result["best"]["auc_apo"]
    _log(f"{target_name}: ceiling (closed-form) AUC={ceiling_auc:.4f} in {time.monotonic()-t0:.1f}s ({CEILING_N_TRIALS} trials)")

    # TASK-0112: attach a bootstrap CI to the ceiling's own winning
    # trial -- recompute its occupation once more from its own params
    # (ceiling_search's own trial loop does not retain raw occupation
    # vectors, only summary AUC/S/rho, per its own Returns contract).
    best_params = ceiling_result["best"]["params"]
    H_ceiling = build_H_new(
        apo.coords, apo.bfactors,
        cutoff=best_params["cutoff"], alpha=best_params["alpha"],
        lam_B=best_params["lam_B"], lam_T=best_params["lam_T"], lam_R=best_params["lam_R"],
        lam_C=best_params["lam_C"], lam_M=best_params["lam_M"], n_low_modes=best_params["n_low"],
    )
    occ_ceiling = time_averaged_ctqw_converged(H_ceiling, source=source, coherent=False)
    ceiling_ci = block_bootstrap_ci(occ_ceiling, pocket_int, n_boot=CI_N_BOOT, rng=np.random.default_rng(1))

    return {
        "target": target_name,
        "n_residues": len(apo.resnums),
        "n_seed_residues": len(source),
        "floor": floor,
        "floor_ci": floor_ci,
        "floor_winning_baseline": ["degree_centrality", "euclid_from_seed_centroid", "hop_from_seed"][floor_idx],
        "actual_auc": actual_auc,
        "actual_diagnosis": result.get("_diagnosis"),
        "actual_score_ci": result.get("_diagnosis_score_ci"),
        "actual_floor_ci": result.get("_diagnosis_floor_ci"),
        "actual_ci_overlap": result.get("_diagnosis_ci_overlap"),
        "ceiling_auc": ceiling_auc,
        "ceiling_ci": ceiling_ci,
        "ceiling_best_params": best_params,
        "ceiling_n_trials_scored": ceiling_result["n_trials_scored"],
        "headroom": (
            (actual_auc - floor) / (ceiling_auc - floor)
            if actual_auc is not None and ceiling_auc != floor else None
        ),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"])
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "closed_form_competence.json")
    args = parser.parse_args(argv)

    all_results = {}
    for name in args.target:
        try:
            all_results[name] = run_target(name)
            r = all_results[name]
            print(
                f"{name}: floor={r['floor']:.4f} {r['floor_ci']} ceiling={r['ceiling_auc']:.4f} {r['ceiling_ci']} "
                f"actual={r['actual_auc']:.4f} {r['actual_score_ci']} diag={r['actual_diagnosis']} "
                f"ci_overlap(actual_vs_floor)={r['actual_ci_overlap']}"
            )
        except Exception as exc:
            all_results[name] = {"error": str(exc)}
            print(f"{name}: FAILED -- {exc}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(all_results, f, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
