#!/usr/bin/env python3
"""TASK-0229.007(b) -- is the ENM impulse-response transport observable
(`allostery.impulse_response`, ref [7] Stock & Hamm 2018) independent of
the ~3 axes [[TASK-0199]] measured, or does it land inside the existing
equilibrium-observable span?

Reuses, does not re-derive: `observable_effective_rank.py`'s own
`_prepare_target`/`compute_all_observables`/`align_and_stack`/
`correlation_matrix_and_rank`/`run_controls` ([[TASK-0199]]), and
[[TASK-0211]]'s own exact "new axis" rule (delta_real must exceed a
matched-variance noise column's own delta, AND delta_real >= 0.10, on
every evaluated target).

No ensemble sampling needed here (unlike TASK-0211's own ensemble-graph
observable) -- the impulse-response observable is closed-form from a
single Kirchhoff eigendecomposition, so no MSF gate / split-half
reproducibility check applies (there is no sampling noise to control
for); the observable is deterministic given the structure.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np
from scipy.stats import spearmanr

_SRC = Path(__file__).resolve().parent.parent / "src"
_SCRIPTS = Path(__file__).resolve().parent
for _p in (_SRC, _SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from observable_effective_rank import (  # noqa: E402
    TARGETS_EXTRA,
    TARGETS_PRIMARY,
    _prepare_target,
    align_and_stack,
    compute_all_observables,
    correlation_matrix_and_rank,
    run_controls,
)

from allostery.impulse_response import gnm_impulse_response_peak_time  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0229.007"
NEW_AXIS_MIN_DELTA = 0.10  # TASK-0211's own pre-registered bar, reused unchanged


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run_target(target_name: str, rng_seed: int = 0) -> dict:
    _log(f"=== {target_name} ===")
    prep = _prepare_target(target_name)
    coords, source, cutoff = prep["coords"], prep["source"], prep["cutoff"]

    observables = compute_all_observables(prep)
    names28, matrix28 = align_and_stack(observables)
    baseline = correlation_matrix_and_rank(matrix28)
    _log(f"{target_name}: baseline (28 obs) participation_ratio_rank={baseline['participation_ratio_rank']:.3f} "
         "(wiring check vs TASK-0199's own published number)")

    ir = gnm_impulse_response_peak_time(coords, cutoff, source)
    new_col = ir["integrated_response"]

    new_matrix = np.column_stack([matrix28, new_col])
    with_new = correlation_matrix_and_rank(new_matrix)
    delta_real = with_new["participation_ratio_rank"] - baseline["participation_ratio_rank"]

    rng = np.random.default_rng(rng_seed + 1)
    noise_col = rng.normal(loc=new_col.mean(), scale=new_col.std(), size=len(new_col))
    noise_matrix = np.column_stack([matrix28, noise_col])
    with_noise = correlation_matrix_and_rank(noise_matrix)
    delta_noise = with_noise["participation_ratio_rank"] - baseline["participation_ratio_rank"]

    controls_29 = run_controls(new_matrix)
    new_axis = bool(delta_real > delta_noise and delta_real >= NEW_AXIS_MIN_DELTA)

    corr_vs_dcc_low, _p = spearmanr(new_col, observables["dcc_low"])
    corr_vs_peak_time, _p2 = spearmanr(new_col, ir["peak_time"])

    _log(f"{target_name}: delta_real={delta_real:.3f} delta_noise={delta_noise:.3f} "
         f"new_axis={new_axis} rho_vs_dcc_low={corr_vs_dcc_low:.3f}")

    return {
        "target": target_name,
        "n_residues": prep["n_residues"],
        "baseline_rank_28": baseline["participation_ratio_rank"],
        "with_new_rank_29": with_new["participation_ratio_rank"],
        "delta_real": float(delta_real),
        "delta_noise_control": float(delta_noise),
        "new_axis_verdict": new_axis,
        "controls_29col": controls_29,
        "spearman_vs_dcc_low": float(corr_vs_dcc_low),
        "spearman_integrated_vs_peak_time": float(corr_vs_peak_time),
        "lambda1": ir["lambda1"],
        "integrated_response_range": [float(new_col.min()), float(new_col.max())],
        "peak_time_n_unique": int(len(np.unique(ir["peak_time"]))),
        "peak_time_frac_zero": float((ir["peak_time"] == 0).mean()),
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    targets = sys.argv[1:] or (TARGETS_PRIMARY + TARGETS_EXTRA)
    results = {}
    for t in targets:
        try:
            r = run_target(t)
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            r = {"target": t, "error": repr(exc)}
            _log(f"{t} FAILED: {exc!r}")
        results[t] = r
        with open(OUTPUT_DIR / "impulse_response_independence.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
    _log("done")
    for t, r in results.items():
        _log(f"{t}: new_axis={r.get('new_axis_verdict', r.get('error'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
