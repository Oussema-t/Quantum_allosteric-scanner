#!/usr/bin/env python3
"""TASK-0126 -- run H13 (or its projections) through the ceiling-search
methodology, compared against `H_new`'s already-established ceiling
([[TASK-0130]]'s closed-form infinite-time convention).

`.claude/hypotheses/ceiling.md`'s own "minimum set" names H13 (or its N×N
projection) as a required ceiling-search candidate; `TASK-0046`'s real
ceiling search never included it. `.claude/improvements/hamiltonian_code.md`
IMP-H7 gives two options:

  Option A -- scalar N×N projection: `H_scalar[i,j] = trace(H13[3i:3i+3,
              3j:3j+3])`.
  Option B -- 3N×3N-native propagation, preserving orientational coupling
              (`propagators.ctqw_3n_native`/`time_averaged_ctqw_3n_native`/
              `time_averaged_ctqw_converged_3n_native`, TASK-0126's own new
              capability).

**Option A, checked not assumed, degenerates exactly to `H2_combinatorial_
laplacian`** for this repo's actual `H13_3N_anm_hessian` construction: every
off-diagonal 3x3 block is `-outer(r, r)` for a *unit* vector `r`, and
`trace(outer(r, r)) = |r|^2 = 1` regardless of bond direction -- the
projection discards all orientational information, not just "some" (see
this task's own Done section for the verified `np.allclose` proof). H2 is
already a registered operator with its own real per-cell AUC in the
96-cell sweep; this script still runs H2 through a real cutoff-only
ceiling search for completeness (H2/H14/H13-native all have exactly one
free physical parameter, `cutoff` -- unlike `H_new`'s 8-dimensional
`ceiling.ceiling_search` space, there is no larger DOF space to search
here), rather than silently substituting the 96-cell sweep's single
default-cutoff number for a real search.

`H14_anm_pinv_trace` (already implemented, TASK-0096 follow-up) is the
codebase's own actual non-trivial scalar reduction of H13's physics (the
standard ANM cross-correlation quantity, Bahar/Atilgan/Erman 1997) -- run
alongside H2 as a much more meaningful "Option A in spirit" comparator
than the literal, degenerate formula.

**Closed-form convention (revised 2026-07-18, mid-task)**: TASK-0130 landed
concurrently and replaced `time_averaged_ctqw`'s finite-`t_max` numerical
time-average with `time_averaged_ctqw_converged`'s exact infinite-time
closed form (no `t_max`/`n_steps` to prescribe or cap). This script was
originally written against the finite-`t_max` convention (`min_adequate_
t_max`/`min_adequate_n_steps` from each operator's own spectral gap, TASK-
0129's combined-convention discipline) and hit a real feasibility wall on
that path: H13-native's `O(n_steps * n_seed)` incoherent-mixture time loop
made a full 60-trial search intractable for BCR_ABL1 (~31.5 hours
projected from one measured 1888s trial) and CARDIAC_MYOSIN (not even
attempted). Switching to the closed form removes that loop entirely (a
one-shot spectral sum per trial) -- this both matches the project's new
canonical convention and makes the full 3-target Option B run tractable
for the first time. The old finite-`t_max` numbers and the infeasibility
finding remain real and are kept in this task's Done section for the
record; they are not this script's live behavior anymore.
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
from allostery.clean import load_target_config  # noqa: E402
from allostery.hamiltonians import H2_combinatorial_laplacian, H13_3N_anm_hessian, H14_anm_pinv_trace  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.propagators import (  # noqa: E402
    time_averaged_ctqw_converged,
    time_averaged_ctqw_converged_3n_native,
)
from allostery.protocol import ceiling_context  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo/DEFAULT_CUTOFF

DEFAULT_CUTOFF = run_challenge.DEFAULT_CUTOFF
DEFAULT_POCKET_CUTOFF = run_challenge.DEFAULT_POCKET_CUTOFF
N_TRIALS = 60
SEED = 7
CUTOFF_RANGE = (6.0, 14.0)  # matches ceiling.py's own _PARAM_RANGES["cutoff"] span
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0126"


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _prepare_target(target_name: str):
    """Same convention as TASK-0129's `_prepare_target_combined` (full
    active-site array, TASK-0118/INV-0006) -- reused by value, not by
    import, to keep this task's own script self-contained (matches
    TASK-0129's own choice not to mutate `sweep_operators.py`'s shared
    helper)."""
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))

    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")
    active_site_idx = np.where(labels_obj.active_site)[0]
    if len(active_site_idx) == 0:
        raise RuntimeError(f"{target_name}: no resolvable active-site seed")
    source = np.sort(active_site_idx)

    floor_candidates = [
        degree_centrality(apo.coords, cutoff=cutoff),
        euclid_from_seed_centroid(apo.coords, source),
        hop_from_seed(apo.coords, source, cutoff=cutoff),
    ]
    floor = float(max(_auc(f, labels_obj.pocket.astype(int)) for f in floor_candidates))
    return apo, labels_obj, source, floor, cutoff


def cutoff_only_ceiling_search(build_fn, score_fn, default_cutoff: float, *, n_trials=N_TRIALS, seed=SEED, cutoff_range=CUTOFF_RANGE, on_trial=None):
    """`ceiling.ceiling_search`'s own discipline (real random search, the
    answer key in hand throughout, `ceiling_context()` gating), scaled to
    an operator whose only free physical parameter is `cutoff` -- H2/H14/
    H13-native all take `(coords, cutoff=...)` only, unlike `H_new`'s
    8-dimensional `(lam_B, lam_T, lam_R, lam_C, lam_M, alpha, cutoff,
    n_low)` space. A 1-dimensional random search over a bounded interval
    is not artificially inflated into a fake multi-dimensional one.

    `build_fn(cutoff) -> H`; `score_fn(H) -> auc`. An individual trial's
    exception is caught and recorded as an error row, not fatal (matches
    `ceiling.ceiling_search`'s own per-trial `try/except: continue`).
    `on_trial(i, n_trials, elapsed_s)`, if given, fires after every trial.
    """
    rng = np.random.default_rng(seed)
    trials = []
    t_start = time.monotonic()
    with ceiling_context():
        for i in range(n_trials):
            cutoff = float(rng.uniform(*cutoff_range))
            try:
                H = build_fn(cutoff)
                auc = float(score_fn(H))
            except Exception as exc:
                trials.append({"cutoff": cutoff, "auc": None, "error": f"{type(exc).__name__}: {exc}"})
            else:
                trials.append({"cutoff": cutoff, "auc": auc, "error": None})
            if on_trial is not None:
                on_trial(i + 1, n_trials, time.monotonic() - t_start)
    scored = [t for t in trials if t["auc"] is not None and np.isfinite(t["auc"])]
    best = max(scored, key=lambda t: t["auc"]) if scored else None
    return {"best": best, "trials": trials, "n_trials_scored": len(scored), "default_cutoff": default_cutoff}


def _on_trial_logger(target_name, label, every=10):
    def _cb(i, ntot, elapsed):
        if i % every == 0 or i == ntot:
            avg = elapsed / i
            _log(f"{target_name}: {label} trial {i}/{ntot} ({elapsed:.1f}s elapsed, {avg:.2f}s/trial, ~{avg*(ntot-i):.0f}s remaining)")
    return _cb


def run_target(target_name: str, *, n_trials: int = N_TRIALS) -> dict:
    apo, labels_obj, source, floor, cutoff = _prepare_target(target_name)
    pocket_int = labels_obj.pocket.astype(int)
    n = len(apo.resnums)
    _log(f"{target_name}: N={n}, n_seed={len(source)}, floor={floor:.4f}")

    result = {"target": target_name, "n_residues": n, "floor": floor}

    # -- H2 (== literal Option A, verified degenerate -- see module docstring)
    t0 = time.monotonic()

    def _score_h2(H):
        occ = time_averaged_ctqw_converged(H, source=source, coherent=False)
        return _auc(occ, pocket_int)

    h2_result = cutoff_only_ceiling_search(
        lambda c: H2_combinatorial_laplacian(apo.coords, cutoff=c), _score_h2, cutoff,
        n_trials=n_trials, on_trial=_on_trial_logger(target_name, "H2"),
    )
    result["H2_option_A_equivalent"] = h2_result
    _log(f"{target_name}: H2/Option-A ceiling={h2_result['best']['auc']:.4f} at cutoff={h2_result['best']['cutoff']:.2f} "
         f"({time.monotonic()-t0:.1f}s)")

    # -- H14 (pinv-trace, the codebase's own real scalarization of H13)
    t0 = time.monotonic()

    def _score_h14(H):
        occ = time_averaged_ctqw_converged(H, source=source, coherent=False)
        return _auc(occ, pocket_int)

    h14_result = cutoff_only_ceiling_search(
        lambda c: H14_anm_pinv_trace(apo.coords, cutoff=c), _score_h14, cutoff,
        n_trials=n_trials, on_trial=_on_trial_logger(target_name, "H14"),
    )
    result["H14_pinv_trace"] = h14_result
    _log(f"{target_name}: H14 ceiling={h14_result['best']['auc']:.4f} at cutoff={h14_result['best']['cutoff']:.2f} "
         f"({time.monotonic()-t0:.1f}s)")

    return result


def run_target_h13_native(target_name: str, apo, source, pocket_int, cutoff: float, *, n_trials: int = N_TRIALS) -> dict:
    """H13-native (Option B) under the closed-form convention -- no
    `t_max`/`n_steps`/rigid-body-nullspace handling needed here at all
    (`time_averaged_ctqw_converged`'s own degenerate-eigenvalue grouping
    absorbs H13's 6 near-zero rigid-body modes transparently, see
    `propagators.time_averaged_ctqw_converged_3n_native`'s docstring).
    This is what makes a full 60-trial search tractable for every target,
    unlike the old finite-`t_max` path (see this task's Done section for
    the infeasibility numbers that convention hit)."""
    def _score_h13(H):
        occ = time_averaged_ctqw_converged_3n_native(H, source=source, coherent=False)
        return _auc(occ, pocket_int)

    t0 = time.monotonic()
    h13_result = cutoff_only_ceiling_search(
        lambda c: H13_3N_anm_hessian(apo.coords, cutoff=c), _score_h13, cutoff,
        n_trials=n_trials, on_trial=_on_trial_logger(target_name, "H13-native"),
    )
    _log(f"{target_name}: H13-native ceiling={h13_result['best']['auc']:.4f} at cutoff={h13_result['best']['cutoff']:.2f} "
         f"({time.monotonic()-t0:.1f}s for {n_trials} trials)")
    return h13_result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"])
    parser.add_argument("--skip-h13-native", action="store_true", help="skip the 3N x 3N Option B search")
    parser.add_argument("--h13-native-only", action="store_true", help="skip H2/H14, only run the Option B search (for isolated feasibility probes)")
    parser.add_argument("--n-trials", type=int, default=N_TRIALS, help="trials per operator (default 60); use a small value for a feasibility timing probe")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "h13_ceiling_comparison.json")
    args = parser.parse_args(argv)

    all_results = {}
    for name in args.target:
        try:
            result = {} if args.h13_native_only else run_target(name, n_trials=args.n_trials)
            if not args.skip_h13_native:
                apo, labels_obj, source, floor, cutoff = _prepare_target(name)
                result["H13_native_option_B"] = run_target_h13_native(
                    name, apo, source, labels_obj.pocket.astype(int), cutoff,
                    n_trials=args.n_trials,
                )
            all_results[name] = result
        except Exception as exc:
            all_results[name] = {"error": str(exc)}
            print(f"{name}: FAILED -- {exc}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(all_results, f, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
