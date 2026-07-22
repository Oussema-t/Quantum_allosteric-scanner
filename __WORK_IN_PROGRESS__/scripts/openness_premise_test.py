#!/usr/bin/env python3
"""TASK-0143 -- coordinated-closure graph-openness premise test (HYP-P10).

Tests, on all 3 mandatory + 4 ASD generalization targets, whether real
holo-defined cryptic-pocket residues carry the "near-in-3D / far-on-apo-
graph" coordinated-closure signature the whole loop/multi-site-closure
observable family (HYP-P9/P10/P12) depends on. This is a premise test with
a pre-registered binary outcome (`.ai/tasks/DONE/TASK-0143-...md`'s own
Planned Validation) -- a clean negative is a complete result, not a
failure to hide.

Runs a synthetic positive-control gate FIRST (a constructed open-cleft
case must land near the ~100th percentile of its own matched-spread null)
before touching real data, so a null real-data result cannot be mistaken
for a silent implementation bug (same falsification-apparatus-before-
real-data discipline as `ceiling.ceiling_context()`/TASK-0103's
`build_dumbbell_network` negative control).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import zlib
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
from allostery.closure import euclid_dist_matrix, graph_dist_matrix, matched_spread_null, pairwise_components  # noqa: E402
from allostery.labels import build_labels  # noqa: E402

import run_challenge  # noqa: E402

TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "PTP1B", "GLUCOKINASE", "CASPASE1", "CASPASE7"]
N_NULL = 500
SPREAD_TOL = 0.35
BASE_SEED = 143
ALPHA = 0.05
# Real proteins' rejection-sampling acceptance rate at +/-35% spread can be
# well under 0.01% for a compact real pocket in a large structure (measured:
# CARDIAC_MYOSIN 75/500 in 5M attempts; BCR_ABL1 0/500 in 5M) -- a compact
# same-size cluster is intrinsically rare among *uniform* random draws over
# a large protein, since most such draws scatter across the whole fold.
# This is a compute-budget parameter, not a statistical-construction one
# (spread tolerance/null size/graph cutoff are untouched), so raising it is
# not "tuning to move a target across the bar" -- it is giving unbiased
# rejection sampling enough tries to find its 500 acceptances.
MAX_ATTEMPTS = 20_000_000
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0143_openness_premise"


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _horseshoe_coords(n: int, radius: float, gap_angle: float) -> np.ndarray:
    theta_total = 2 * np.pi - gap_angle
    theta = np.linspace(0, theta_total, n)
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    return np.column_stack([x, y, np.zeros(n)])


def synthetic_positive_control_gate() -> dict:
    """Reproduces `tests/test_closure.py::TestSyntheticOpenCleftPositiveControl`
    standalone (not imported from the test file -- this script must be
    runnable and self-verifying without pytest), for visibility in this
    script's own log/output rather than only in CI."""
    n = 60
    coords = _horseshoe_coords(n, radius=25.0, gap_angle=0.3)
    GD = graph_dist_matrix(coords, cutoff=8.0)
    D = euclid_dist_matrix(coords)
    pocket = np.array([0, 1, n - 2, n - 1])
    result = matched_spread_null(pocket, D, GD, n_null=200, tol=SPREAD_TOL, seed=1)
    _log(f"synthetic positive control: percentile={result['percentile']:.1f} "
         f"(real_signature={result['real_signature']:.3f}, null_median={result['null_median']:.3f})")
    if result["percentile"] < 95.0:
        raise RuntimeError(
            f"synthetic positive-control gate FAILED: percentile={result['percentile']:.1f}, "
            "expected >=95 -- do not trust real-data results until this is fixed"
        )
    return result


def _prepare_target(target_name: str):
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))

    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")
    pocket_idx = np.where(labels_obj.pocket)[0]
    if len(pocket_idx) < 2:
        raise RuntimeError(f"{target_name}: pocket has <2 residues, openness_signature undefined")

    return apo, pocket_idx, cutoff


def run_target(target_name: str) -> dict:
    apo, pocket_idx, cutoff = _prepare_target(target_name)
    n = len(apo.resnums)
    _log(f"{target_name}: N={n}, pocket_size={len(pocket_idx)}, apo_graph_cutoff={cutoff}")

    GD = graph_dist_matrix(apo.coords, cutoff=cutoff)
    D = euclid_dist_matrix(apo.coords)

    # Raw pairwise components -- always computable independent of whether
    # the matched-spread null itself can be constructed (no rejection
    # sampling here), so these are available even for an INFEASIBLE target.
    components = pairwise_components(pocket_idx, D, GD)
    _log(f"{target_name}: graph_hop_mean={components['graph_hop_mean']:.3f} "
         f"euclid_mean={components['euclid_mean']:.2f}A")

    # zlib.crc32, not Python's built-in `hash()` -- string hashing is
    # randomized per-process (PYTHONHASHSEED salting, since Python 3.3) for
    # security, so `hash(target_name)` gives a *different* seed on every
    # invocation. Found directly (not assumed): re-running the KRAS_G12C
    # smoke test twice gave percentile=100.0 then 99.4 from the same code
    # path -- crc32 is a fixed, deterministic function of its input.
    seed = BASE_SEED + (zlib.crc32(target_name.encode()) & 0xFFFF)
    t0 = time.monotonic()
    try:
        result = matched_spread_null(pocket_idx, D, GD, n_null=N_NULL, tol=SPREAD_TOL, seed=seed, max_attempts=MAX_ATTEMPTS)
    except RuntimeError as exc:
        elapsed = time.monotonic() - t0
        # A real, reportable outcome, not a crash: at this pre-registered
        # tolerance, unbiased rejection sampling could not find enough
        # matched-spread replicates even at MAX_ATTEMPTS. Loosening the
        # tolerance to force a result would violate this task's own
        # Constraint ("do not tune... to move any target across the bar")
        # -- reported as INFEASIBLE instead, distinct from PASS/FAIL/
        # INSUFFICIENT, with the diagnostic message preserved verbatim.
        _log(f"{target_name}: INFEASIBLE -- {exc} ({elapsed:.1f}s)")
        return {
            "target": target_name, "n_residues": n, "pocket_size": len(pocket_idx),
            "apo_graph_cutoff": cutoff, "verdict": "INFEASIBLE", "detail": str(exc),
            "graph_hop_mean": components["graph_hop_mean"], "euclid_mean": components["euclid_mean"],
        }
    elapsed = time.monotonic() - t0

    p_bonferroni = min(1.0, result["p_one_sided"] * len(TARGETS))
    if result["percentile"] > 95.0 and p_bonferroni < ALPHA:
        verdict = "PASS"
    elif result["percentile"] <= 50.0:
        verdict = "FAIL"
    else:
        verdict = "INSUFFICIENT"

    _log(f"{target_name}: signature={result['real_signature']:.3f} spread={result['real_spread']:.2f}A "
         f"percentile={result['percentile']:.1f} p={result['p_one_sided']:.4f} "
         f"p_bonf={p_bonferroni:.4f} verdict={verdict} ({elapsed:.1f}s)")

    return {
        "target": target_name,
        "n_residues": n,
        "pocket_size": len(pocket_idx),
        "apo_graph_cutoff": cutoff,
        "real_signature": result["real_signature"],
        "real_spread": result["real_spread"],
        "graph_hop_mean": components["graph_hop_mean"],
        "euclid_mean": components["euclid_mean"],
        "n_null": result["n_null"],
        "n_attempts": result["n_attempts"],
        "null_median": result["null_median"],
        "null_sd": result["null_sd"],
        "percentile": result["percentile"],
        "p_one_sided": result["p_one_sided"],
        "p_bonferroni": p_bonferroni,
        "verdict": verdict,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=TARGETS)
    parser.add_argument("--skip-synthetic-gate", action="store_true", help="skip the positive-control gate (not recommended)")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "openness_premise.json")
    args = parser.parse_args(argv)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    all_results = {}
    if args.output.exists():
        with open(args.output) as f:
            all_results = json.load(f)
        _log(f"loaded {len(all_results)} existing entries from {args.output} -- merging, not overwriting")

    if not args.skip_synthetic_gate:
        all_results["_synthetic_positive_control"] = synthetic_positive_control_gate()
        with open(args.output, "w") as f:
            json.dump(all_results, f, indent=2)

    for name in args.target:
        try:
            all_results[name] = run_target(name)
        except Exception as exc:
            all_results[name] = {"error": str(exc)}
            _log(f"{name}: FAILED -- {exc!r}")

        # Checkpoint after every target -- some targets (BCR_ABL1: ~18.5min
        # to confirm INFEASIBLE) are expensive enough that losing completed
        # results to an interruption would be a real cost, not a formality
        # (same lesson TASK-0138's null script learned the hard way).
        with open(args.output, "w") as f:
            json.dump(all_results, f, indent=2)
        _log(f"{name}: wrote checkpoint to {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
