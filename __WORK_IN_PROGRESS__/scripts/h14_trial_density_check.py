#!/usr/bin/env python3
"""TASK-0138 -- trial-density justification for H14's cutoff-only ceiling search.

`h13_ceiling_comparison.cutoff_only_ceiling_search` uses 60 trials for
H14 by analogy to `ceiling.ceiling_search`'s own 60-trial convention --
but that convention was chosen for `H_new`'s 8-dimensional space
(TASK-0116's own scope). H14 has exactly one free parameter (`cutoff`,
range [6, 14]), a very different search problem. This script checks
whether 60 trials is actually adequate for a 1-D search, rather than
assuming so by analogy: runs one long random search (300 trials, same
RNG stream `cutoff_only_ceiling_search` itself uses) per target, then
computes the running-max AUC at n=10,20,30,60,100,150,200,300 from that
single ordered trial sequence -- if the running max has already
plateaued by n=60, the existing convention is justified; if it is still
climbing, 60 trials understates the true ceiling.
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

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from allostery.hamiltonians import H14_anm_pinv_trace  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from h13_ceiling_comparison import _prepare_target, cutoff_only_ceiling_search  # noqa: E402

CHECKPOINTS = [10, 20, 30, 60, 100, 150, 200, 300]
N_TRIALS_LONG = 300


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run_target(target_name: str) -> dict:
    apo, labels_obj, source, floor, cutoff = _prepare_target(target_name)
    pocket_int = labels_obj.pocket.astype(int)

    def _score_h14(H):
        occ = time_averaged_ctqw_converged(H, source=source, coherent=False)
        return _auc(occ, pocket_int)

    t0 = time.monotonic()
    result = cutoff_only_ceiling_search(
        lambda c: H14_anm_pinv_trace(apo.coords, cutoff=c), _score_h14, cutoff,
        n_trials=N_TRIALS_LONG,
    )
    elapsed = time.monotonic() - t0

    aucs = [t["auc"] for t in result["trials"]]
    running_max = {}
    best_so_far = -np.inf
    for i, a in enumerate(aucs, start=1):
        if a is not None and np.isfinite(a):
            best_so_far = max(best_so_far, a)
        if i in CHECKPOINTS:
            running_max[i] = float(best_so_far)

    _log(f"{target_name}: {N_TRIALS_LONG} trials in {elapsed:.1f}s -- running max: {running_max}")
    return {
        "target": target_name, "n_trials": N_TRIALS_LONG, "elapsed_s": round(elapsed, 1),
        "running_max_at": running_max,
        "final_max": float(best_so_far),
        "max_at_60_vs_final": float(running_max.get(60, float("nan"))) - float(best_so_far),
    }


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", nargs="+", default=["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"])
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent.parent / "results_task0138_h14_permutation_null" / "trial_density_check.json")
    args = parser.parse_args(argv)

    all_results = {}
    for name in args.target:
        all_results[name] = run_target(name)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(all_results, f, indent=2)
    _log(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
