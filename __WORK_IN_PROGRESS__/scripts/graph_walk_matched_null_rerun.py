#!/usr/bin/env python3
"""TASK-0201 -- does a null that can genuinely REACH real pocket Rg
(`allostery.nulls.graph_walk_patch_matched`) change TASK-0190's own
`dcc_low` verdict on CARDIAC_MYOSIN/PTP1B?

TASK-0190 found `compact_patch_matched` cannot reach either target's real
pocket Rg at all (structural ceiling, not a rare tail event) -- the
"matched" null it reported was, in fact, dominated by `compact_patch`'s
own natural upper tail, not genuinely centred on `target_rg`. This script:

  1. Verifies `graph_walk_patch`'s own unconstrained Rg support actually
     contains `target_rg` (>=20,000 draws, matching TASK-0190's own
     diagnostic scale) -- the exact check that caught the original defect,
     run here BEFORE trusting the matched null built on top of it.
  2. Verifies the matched null's own accepted-draw distribution genuinely
     centres near `target_rg`, not merely reaches it in the tail.
  3. Re-runs `dcc_low` (CARDIAC_MYOSIN, PTP1B) against this new null and
     reports whether TASK-0190's own pre-registered survival verdict
     changes.

Reuses `compact_null_rerun.py`'s own `_lowmode_prepare_target`/
`_well_powered_max`/`K_MODES_GRID`/`N_PERM_REPS`/`PERM_SEED` directly
(imported, not re-derived), per that script's own established convention.
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

from allostery.lowmode_predictor import dcc_low  # noqa: E402
from allostery.metrics import stratified_auc  # noqa: E402
from allostery.nulls import (  # noqa: E402
    build_adjacency,
    compact_patch,
    graph_walk_patch,
    graph_walk_patch_matched,
    radius_of_gyration,
)

from compact_null_rerun import (  # noqa: E402
    K_MODES_GRID, N_PERM_REPS, PERM_SEED, _lowmode_null, _lowmode_prepare_target, _well_powered_max,
)

TOL = 0.35  # unchanged default, matching TASK-0190's own Constraint
UNCONSTRAINED_DRAWS = 20_000  # matches TASK-0190's own diagnostic scale
WALK_CUTOFF = 8.0  # TASK-0067's retained contact-graph scale, reused not reinvented
FINAL_N_REPS = 20_000  # raised from TASK-0190's own 1000 once a near-bar p-value
# (PTP1B k=10) was found -- SE at p~0.003 with n=1000 is ~0.0017, too coarse to
# read a boundary call; 20,000 tightens the 95% CI to +/-~0.0007, decisive.

# TASK-0190's own pre-registered survival bars (unchanged, reused not re-derived).
SURVIVAL_BARS = {
    "CARDIAC_MYOSIN": 0.05 / 6,   # TASK-0149 primary 6-comparison
    "PTP1B": 0.05 / 16,           # TASK-0151 16-comparison
}
TARGETS = ["CARDIAC_MYOSIN", "PTP1B"]


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def unconstrained_rg_support(coords, adjacency, size, n_draws, seed):
    rng = np.random.default_rng(seed)
    rgs = np.array([
        radius_of_gyration(coords, graph_walk_patch(adjacency, size, rng))
        for _ in range(n_draws)
    ])
    return rgs


def graph_walk_null(score, prep, adjacency, *, target_rg, n_reps=FINAL_N_REPS, seed=PERM_SEED):
    pocket_size = int(prep["pocket"].sum())
    n_residues = prep["n_residues"]
    shells = prep["shells"]
    coords = prep["coords"]

    real_shell, real_auc = _well_powered_max(stratified_auc(score, prep["pocket"], shells))
    rng = np.random.default_rng(seed)
    null_maxes = []
    accepted_rgs = []
    n_attempts_total = 0
    for _ in range(n_reps):
        idx, n_attempts = graph_walk_patch_matched(
            coords, adjacency, pocket_size, rng, target_rg=target_rg, tol=TOL,
            max_attempts=200_000, return_attempts=True,
        )
        n_attempts_total += n_attempts
        accepted_rgs.append(radius_of_gyration(coords, idx))
        lab = np.zeros(n_residues, dtype=int)
        lab[idx] = 1
        _, null_max = _well_powered_max(stratified_auc(score, lab, shells))
        if np.isfinite(null_max):
            null_maxes.append(null_max)
    null_maxes = np.array(null_maxes) if null_maxes else np.array([np.nan])
    accepted_rgs = np.array(accepted_rgs)
    p_value = float((null_maxes >= real_auc).mean()) if np.isfinite(real_auc) else float("nan")
    se = float(np.sqrt(p_value * (1 - p_value) / n_reps)) if np.isfinite(p_value) else float("nan")
    return {
        "real_well_powered_max_auc": real_auc, "real_shell": real_shell,
        "null_median": float(np.median(null_maxes)), "n_reps": len(null_maxes),
        "p_value": p_value, "p_value_se": se,
        "p_value_ci95": [max(0.0, p_value - 1.96 * se), p_value + 1.96 * se],
        "accepted_draw_mean_rg": float(accepted_rgs.mean()),
        "accepted_draw_median_rg": float(np.median(accepted_rgs)),
        "mean_attempts": n_attempts_total / n_reps,
    }


def run_target(target_name: str) -> dict:
    t0 = time.monotonic()
    prep = _lowmode_prepare_target(target_name)
    coords = prep["coords"]
    pocket_size = int(prep["pocket"].sum())
    target_rg = radius_of_gyration(coords, np.where(prep["pocket"])[0])
    _log(f"{target_name}: N={prep['n_residues']} pocket_size={pocket_size} real_pocket_rg={target_rg:.3f}")

    adjacency = build_adjacency(coords, cutoff=WALK_CUTOFF)

    # --- Step 1: unconstrained Rg support, verified before trusting the matched null ---
    _log(f"{target_name}: drawing {UNCONSTRAINED_DRAWS} unconstrained graph_walk_patch samples...")
    rgs = unconstrained_rg_support(coords, adjacency, pocket_size, UNCONSTRAINED_DRAWS, seed=11)
    support = {
        "max": float(rgs.max()), "mean": float(rgs.mean()),
        "p99_9": float(np.percentile(rgs, 99.9)),
        "target_within_support": bool(target_rg <= rgs.max()),
        "target_percentile": float((rgs <= target_rg).mean()),
    }
    _log(f"{target_name}: unconstrained support max={support['max']:.3f} "
         f"(real={target_rg:.3f}, within_support={support['target_within_support']}, "
         f"percentile={support['target_percentile']:.3f})")

    # --- Step 2 + 3: dcc_low re-run against the matched null, plus
    # scattered/compact at the SAME n_reps/seed for the ordering check
    # (TASK-0190's own Planned Validation: p(scattered)<=p(matched)<=p(compact)) ---
    cells = []
    for k in K_MODES_GRID:
        score = dcc_low(coords, prep["source"], cutoff=prep["cutoff"], k_modes=k)
        matched = graph_walk_null(score, prep, adjacency, target_rg=target_rg)
        scattered = _lowmode_null(score, prep, compact=False, n_reps=FINAL_N_REPS, seed=PERM_SEED)
        compact = _lowmode_null(score, prep, compact=True, n_reps=FINAL_N_REPS, seed=PERM_SEED)
        ordering_ok = scattered["p_value"] <= matched["p_value"] <= compact["p_value"]
        cells.append({
            "k_modes": k, "matched": matched, "scattered": scattered, "compact": compact,
            "ordering_ok": ordering_ok,
        })
        _log(f"{target_name} dcc_low k={k}: p_scattered={scattered['p_value']:.4f} "
             f"p_matched={matched['p_value']:.4f} [{matched['p_value_ci95'][0]:.4f},"
             f"{matched['p_value_ci95'][1]:.4f}] p_compact={compact['p_value']:.4f} "
             f"(auc={matched['real_well_powered_max_auc']:.3f}) ordering_ok={ordering_ok} "
             f"accepted_mean_rg={matched['accepted_draw_mean_rg']:.3f} (target={target_rg:.3f})")

    min_p = min(c["matched"]["p_value"] for c in cells if np.isfinite(c["matched"]["p_value"]))
    bar = SURVIVAL_BARS[target_name]
    survives = bool(min_p < bar)

    return {
        "target": target_name,
        "n_residues": prep["n_residues"],
        "pocket_size": pocket_size,
        "real_pocket_rg": target_rg,
        "unconstrained_support": support,
        "cells": cells,
        "min_p": min_p,
        "survival_bar": bar,
        "survives": survives,
        "elapsed_s": round(time.monotonic() - t0, 1),
    }


def main() -> int:
    out = {}
    for name in TARGETS:
        try:
            out[name] = run_target(name)
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            out[name] = {"target": name, "error": f"{type(exc).__name__}: {exc}"}

    out_dir = Path(__file__).resolve().parent.parent / "results_task0201_graph_walk_matched_null"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(out, indent=2, default=float))
    print(f"\nWrote {out_path}")

    print("\n=== TASK-0201 summary ===")
    for name, r in out.items():
        if "error" in r:
            print(f"{name}: ERROR {r['error']}")
            continue
        print(f"{name}: real_rg={r['real_pocket_rg']:.3f} "
              f"support_max={r['unconstrained_support']['max']:.3f} "
              f"within_support={r['unconstrained_support']['target_within_support']} "
              f"min_p={r['min_p']:.4f} bar={r['survival_bar']:.5f} survives={r['survives']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
