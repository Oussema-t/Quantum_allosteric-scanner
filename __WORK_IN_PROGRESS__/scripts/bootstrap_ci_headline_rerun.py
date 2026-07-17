#!/usr/bin/env python3
"""TASK-0112 -- re-run the floor-vs-score comparisons `RESULTS.md` already
records as settled, with `diagnostics.classify_failure(return_ci=True)`
attached, and report explicitly whether the verdict is statistically
decisive or the two intervals overlap.

Three named comparisons (this task's own In Scope list):
  - KRAS_G12C: H_new CTQW vs its euclid_from_seed_centroid floor (TASK-0094:
    AUC 0.779 vs floor 0.798, `BEATS_CHANCE_NOT_FLOOR`).
  - BCR_ABL1: H_new CTQW vs its hop_from_seed floor (TASK-0094/TASK-0106:
    AUC 0.525 vs floor 0.565, `NO_SIGNAL_IN_APO` -- never reaches the floor
    check, reported anyway per this task's own "report the CI on both the
    scored operator and the floor baseline").
  - BCR_ABL1: H_new ground_state_relaxation vs the same floor (TASK-0091/
    TASK-0104: AUC 0.7315, floor-clearing, re-framed as a structural prior).

No cached raw occupation-vector arrays exist for any of these (verdict.json/
reproduction.json only store scalar AUCs) -- `block_bootstrap_ci` needs the
full per-residue score array, so this is a live re-run, per this task's own
Out Of Scope ("only re-run live if the cached per-residue score arrays
aren't available").
"""
from __future__ import annotations

import json
import os
import sys
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

from allostery.diagnostics import classify_failure  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.propagators import ground_state_relaxation, time_averaged_ctqw  # noqa: E402
from sweep_operators import _prepare_target  # noqa: E402

T_MAX = 15.0  # unchanged from RESULTS.md's own recorded numbers -- this
# task re-attaches a CI to the *existing* headline numbers, it does not
# also apply TASK-0119's per-operator clock fix (a separate, orthogonal
# correction -- conflating the two here would make it impossible to tell
# which change moved which number).
N_STEPS = 500
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0112"


def _ci_dict(ci):
    if ci is None:
        return None
    auc, lo, hi = ci
    return {"auc": auc, "lo": lo, "hi": hi}


def run_one(target_name: str, propagator_name: str) -> dict:
    coords, bfactors, source, pocket_label, floor_scores, cutoff = _prepare_target(target_name)
    H = build_H_new(coords, bfactors, cutoff=cutoff)
    if propagator_name == "ctqw":
        occ = time_averaged_ctqw(H, T_MAX, source=source, n_steps=N_STEPS)
    elif propagator_name == "ground_state":
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # indefinite-H warning, already documented (TASK-0095)
            occ = ground_state_relaxation(H, T_MAX, source=source)
    else:
        raise ValueError(propagator_name)

    result = classify_failure(
        occ, pocket_label, H=H, bfactors=bfactors, floor_scores=floor_scores, return_ci=True,
    )
    print(
        f"{target_name} H_new/{propagator_name}: category={result.category} "
        f"score_ci={result.score_ci} floor_ci={result.floor_ci} "
        f"ci_overlap={result.ci_overlap}"
    )
    return {
        "target": target_name, "propagator": propagator_name,
        "category": result.category,
        "score_ci": _ci_dict(result.score_ci),
        "floor_ci": _ci_dict(result.floor_ci),
        "ci_overlap": result.ci_overlap,
    }


def main() -> int:
    rows = [
        run_one("KRAS_G12C", "ctqw"),
        run_one("BCR_ABL1", "ctqw"),
        run_one("BCR_ABL1", "ground_state"),
    ]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "headline_ci_rerun.json", "w") as f:
        json.dump(rows, f, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
