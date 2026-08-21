#!/usr/bin/env python3
"""TASK-0159 -- direct numerical validation of `time_averaged_ctqw_
converged`'s closed form against a real, full-length finite-time
integration, run all the way out to the AAKV-prescribed `t_max*`
(`propagators.min_adequate_t_max`), for one target.

TASK-0130's closed form (`P_infinity(j|source) = sum_k |v_k(j)|^2
|<v_k|psi0>|^2`) is an exact algebraic derivation of the infinite-time
average, not an approximation -- but it has never been directly checked
against a genuine brute-force finite-time run carried out to real AAKV
convergence on any of this project's actual targets (TASK-0110's own
finding that doing so is 145,000x-3,950,000x the shipped `t_max=15`
default is exactly why the closed form was built instead of ever running
this). Per direct user request (2026-07-25, TASK-0159's own real-target
validation step): run it anyway, computing time in the hours explicitly
authorized as acceptable.

Reuses `propagators._ctqw_mixture_from_eigh` directly (not the public
`time_averaged_ctqw`, which has no progress-logging hook) -- the same
per-step helper TASK-0134's own CPU-time re-verification already
established this pattern for, extended here to a full (not bounded)
run, all 5 mandatory + generalization targets, with `runlog.RunLogger`
periodic instrumentation per `LONG_JOB_CONVENTION.md` (this is exactly
the multi-hour, must-not-block, must-leave-a-trace-if-killed situation
that convention exists for).

Coherent=False (incoherent mixture) throughout, matching TASK-0118's own
established GAUGE for every real scored call site in this project --
the same convention `time_averaged_ctqw_converged` is scored under
elsewhere in this task's own real-target run.
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

from allostery.clean import load_target_config  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as auc_fn  # noqa: E402
from allostery.propagators import (  # noqa: E402
    _ctqw_mixture_from_eigh,
    min_adequate_n_steps,
    min_adequate_t_max,
    time_averaged_ctqw_converged,
)
from allostery.runlog import RunLogger  # noqa: E402

import run_challenge  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "RESULTS" / "results/tasks/0159_finite_time_convergence"
SAMPLE_EVERY = 20000  # RunLogger.step() cadence, in loop iterations


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run_one(target_name: str, tol: float) -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger = RunLogger(OUTPUT_DIR / f"{target_name}.runlog.jsonl", f"task0159_finite_time_{target_name}")

    cfg = load_target_config(target_name)
    cutoff = float(cfg.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    pocket_cutoff = float(cfg.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))
    apo, holo = run_challenge._load_apo_holo(target_name, cfg)
    labels_obj = build_labels(apo, holo, cfg, cutoff=pocket_cutoff)
    source = np.sort(np.where(labels_obj.active_site)[0])
    pocket = labels_obj.pocket.astype(int)

    H = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
    w, v = np.linalg.eigh(H)
    t_star = min_adequate_t_max(w=w, kind="time_averaged_ctqw", tol=tol)
    n_steps = min_adequate_n_steps(w=w, t_max=t_star)
    _log(f"{target_name}: N={H.shape[0]} t_max*={t_star:.1f} n_steps={n_steps} (tol={tol})")

    times = np.linspace(0.0, t_star, n_steps)
    acc = np.zeros(H.shape[0])
    t0 = time.monotonic()
    for i, t in enumerate(times):
        acc += _ctqw_mixture_from_eigh(w, v, t, source)
        if (i + 1) % SAMPLE_EVERY == 0:
            elapsed = time.monotonic() - t0
            rate = (i + 1) / elapsed
            eta_s = (n_steps - (i + 1)) / rate if rate > 0 else float("nan")
            logger.step(
                "progress", iteration=i + 1, n_steps=n_steps,
                fraction=(i + 1) / n_steps, wall_elapsed_s=elapsed,
                steps_per_s=rate, eta_s=eta_s,
            )
            _log(f"{target_name}: {i+1}/{n_steps} ({(i+1)/n_steps*100:.1f}%) "
                 f"rate={rate:.0f} steps/s ETA={eta_s/60:.1f}min")

    finite_occ = acc / n_steps
    finite_elapsed = time.monotonic() - t0

    converged_occ = time_averaged_ctqw_converged(H, source=source, coherent=False)

    finite_auc = float(auc_fn(finite_occ, pocket))
    converged_auc = float(auc_fn(converged_occ, pocket))
    max_abs_diff = float(np.max(np.abs(finite_occ - converged_occ)))
    l2_diff = float(np.linalg.norm(finite_occ - converged_occ))
    spearman_rank_agreement = float(
        np.corrcoef(np.argsort(np.argsort(finite_occ)), np.argsort(np.argsort(converged_occ)))[0, 1]
    )

    result = {
        "target": target_name, "N": H.shape[0], "t_max_star": t_star, "n_steps": n_steps,
        "tol": tol, "finite_run_wall_s": finite_elapsed,
        "finite_auc": finite_auc, "converged_auc": converged_auc,
        "auc_diff": finite_auc - converged_auc,
        "max_abs_occupation_diff": max_abs_diff, "l2_occupation_diff": l2_diff,
        "occupation_rank_correlation": spearman_rank_agreement,
    }
    logger.finish(**result)
    _log(f"{target_name}: DONE finite_auc={finite_auc:.4f} converged_auc={converged_auc:.4f} "
         f"diff={finite_auc-converged_auc:+.5f} max_abs_occ_diff={max_abs_diff:.2e} "
         f"({finite_elapsed/3600:.2f}h)")

    with open(OUTPUT_DIR / f"{target_name}.json", "w") as f:
        json.dump(result, f, indent=2)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", required=True, help="single target name (run one per process)")
    parser.add_argument("--tol", type=float, default=1e-2)
    args = parser.parse_args(argv)
    run_one(args.target, args.tol)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
