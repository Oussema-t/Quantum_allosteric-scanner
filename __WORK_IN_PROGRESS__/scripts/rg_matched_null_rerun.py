#!/usr/bin/env python3
"""TASK-0190 -- re-run `dcc_low` (CARDIAC_MYOSIN, PTP1B) and `T(E=0)` on
`L` (BCR_ABL1) against a null matched to each target's own REAL pocket
radius of gyration, not a synthetic patch's own Rg.

**The defect this fixes** (external review §2.1, Reviewer finding F2):
`nulls.compact_patch_matched`'s only two existing call sites
(`positive_control_detection_curve.py`, `zero_plant_specificity.py`) both
set `target_rg = radius_of_gyration(coords, patch)` where `patch` is
itself drawn from `select_distal_patch`, which draws from `compact_patch`
-- so "matched ~= compact" was true by construction there, not a finding.
This script is the first real call site that sets `target_rg` from a
target's own measured real pocket (`build_labels(...).pocket`).

Reuses `compact_null_rerun.py`'s own `_lowmode_prepare_target`/
`_well_powered_max`/`K_MODES_GRID`/`N_PERM_REPS`/`PERM_SEED` and
`transport_observable_real_run.py`'s own `_prepare_target`/`N_PERM`/
`ALPHA`/`N_TARGETS_FOR_BONFERRONI` directly (imported, not re-derived) --
only the null-draw step is extended to a 3-way scattered/compact/matched
comparison. All three are computed fresh here under an identical seed/
n_reps harness per cell, rather than reusing a historical scattered/
compact number computed under a (possibly) different exact harness --
the comparison is only valid apples-to-apples.
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
from allostery.metrics import auc as auc_fn  # noqa: E402
from allostery.metrics import stratified_auc  # noqa: E402
from allostery.nulls import compact_patch, compact_patch_matched, radius_of_gyration  # noqa: E402
from allostery.transport import transmission_from_source  # noqa: E402

from compact_null_rerun import (  # noqa: E402
    K_MODES_GRID, N_PERM_REPS, PERM_SEED, _lowmode_prepare_target, _well_powered_max,
)
from transport_observable_real_run import (  # noqa: E402
    ALPHA, N_PERM, N_TARGETS_FOR_BONFERRONI, _prepare_target as _transport_prepare_target,
)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0190_rg_matched_null"
NULL_TYPES = ("scattered", "compact", "matched")
TOL = 0.35  # unchanged default, per this task's own Constraint

# Part B's published real-pocket Rg (TASK-0167.003), cross-checked below,
# not trusted blind -- this task's own In-Scope: "recompute rather than
# copy, as a cross-check."
PART_B_RG = {"CARDIAC_MYOSIN": 9.63, "PTP1B": 7.97, "BCR_ABL1": 7.45}

# Pre-registered survival bars (.ai/tasks/DONE/TASK-0190-*.md, fixed before
# any run) -- unchanged from the original tasks that established each cell.
SURVIVAL_BARS = {
    ("dcc_low", "CARDIAC_MYOSIN"): 0.05 / 6,     # TASK-0149 primary 6-comparison
    ("dcc_low", "PTP1B"): 0.05 / 16,             # TASK-0151 16-comparison
    ("T(E=0)_on_L", "BCR_ABL1"): 0.05 / 3,       # TASK-0145 3-target family
}


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _real_pocket_rg(coords: np.ndarray, pocket_int: np.ndarray) -> float:
    pocket_idx = np.where(pocket_int == 1)[0]
    return radius_of_gyration(coords, pocket_idx)


def _draw(null_type: str, coords: np.ndarray, pocket_size: int, n_residues: int,
          rng: np.random.Generator, *, target_rg: float | None = None, max_attempts: int = 200_000):
    """Returns (idx, n_attempts_or_None). Raises RuntimeError on matched
    infeasibility -- caller's job to catch and count, per this task's own
    Constraint (report infeasibility, never silently widen tol)."""
    if null_type == "scattered":
        return rng.choice(n_residues, size=pocket_size, replace=False), None
    if null_type == "compact":
        return compact_patch(coords, pocket_size, rng), None
    if null_type == "matched":
        return compact_patch_matched(
            coords, pocket_size, rng, target_rg=target_rg, tol=TOL,
            max_attempts=max_attempts, return_attempts=True,
        )
    raise ValueError(null_type)


def _lowmode_null_3way(score, prep, null_type, *, target_rg=None,
                        n_reps=N_PERM_REPS, seed=PERM_SEED) -> dict:
    pocket_size = int(prep["pocket"].sum())
    n_residues = prep["n_residues"]
    shells, coords = prep["shells"], prep["coords"]
    real_shell, real_auc = _well_powered_max(stratified_auc(score, prep["pocket"], shells))

    rng = np.random.default_rng(seed)
    null_maxes, attempts, matched_rgs, n_infeasible = [], [], [], 0
    for _ in range(n_reps):
        try:
            idx, n_att = _draw(null_type, coords, pocket_size, n_residues, rng, target_rg=target_rg)
        except RuntimeError:
            n_infeasible += 1
            continue
        if n_att is not None:
            attempts.append(n_att)
            matched_rgs.append(radius_of_gyration(coords, idx))
        lab = np.zeros(n_residues, dtype=int)
        lab[idx] = 1
        _, null_max = _well_powered_max(stratified_auc(score, lab, shells))
        if np.isfinite(null_max):
            null_maxes.append(null_max)

    null_maxes = np.array(null_maxes) if null_maxes else np.array([np.nan])
    percentile = float((null_maxes <= real_auc).mean()) if np.isfinite(real_auc) else float("nan")
    p_value = float((null_maxes >= real_auc).mean()) if np.isfinite(real_auc) else float("nan")
    out = {
        "real_well_powered_max_auc": real_auc, "real_shell": real_shell,
        "null_median": float(np.median(null_maxes)), "n_reps": len(null_maxes),
        "n_infeasible": n_infeasible, "percentile": percentile, "p_value": p_value,
    }
    if attempts:
        out["mean_attempts"] = float(np.mean(attempts))
        out["max_attempts_used"] = int(np.max(attempts))
        out["draw_rg_mean"] = float(np.mean(matched_rgs))
        out["draw_rg_std"] = float(np.std(matched_rgs))
    return out


def _transport_null_3way(score, pocket, n_residues, pocket_size, coords, null_type, *,
                          target_rg=None, n_reps=N_PERM, seed=123) -> dict:
    real_auc = float(auc_fn(score, pocket))
    rng = np.random.default_rng(seed)
    null_aucs, attempts, matched_rgs, n_infeasible = [], [], [], 0
    for _ in range(n_reps):
        try:
            idx, n_att = _draw(null_type, coords, pocket_size, n_residues, rng, target_rg=target_rg)
        except RuntimeError:
            n_infeasible += 1
            continue
        if n_att is not None:
            attempts.append(n_att)
            matched_rgs.append(radius_of_gyration(coords, idx))
        perm_pocket = np.zeros(n_residues, dtype=int)
        perm_pocket[idx] = 1
        null_aucs.append(auc_fn(score, perm_pocket))
    null_aucs = np.array(null_aucs) if null_aucs else np.array([np.nan])
    percentile = float((null_aucs <= real_auc).mean())
    p_value = float((null_aucs >= real_auc).mean())
    out = {
        "real_auc": real_auc, "null_median": float(np.median(null_aucs)),
        "percentile": percentile, "p_value": p_value, "n_reps": len(null_aucs),
        "n_infeasible": n_infeasible,
        "bonferroni_alpha": ALPHA / N_TARGETS_FOR_BONFERRONI,
    }
    if attempts:
        out["mean_attempts"] = float(np.mean(attempts))
        out["max_attempts_used"] = int(np.max(attempts))
        out["draw_rg_mean"] = float(np.mean(matched_rgs))
        out["draw_rg_std"] = float(np.std(matched_rgs))
    return out


def _ordering_ok(p_scattered: float, p_matched: float, p_compact: float) -> bool:
    """Planned Validation: p(scattered) <= p(matched) <= p(compact) is
    expected given Part B's own geometry (matched sits between scattered
    and compact in strictness). Small numerical ties are tolerated (exact
    inequality on a finite-sample p-value is not required)."""
    eps = 1e-9
    return (p_scattered <= p_matched + eps) and (p_matched <= p_compact + eps)


def run_dcc_low_target(target_name: str) -> dict:
    prep = _lowmode_prepare_target(target_name)
    real_rg = _real_pocket_rg(prep["coords"], prep["pocket"])
    _log(f"[dcc_low] {target_name}: N={prep['n_residues']} pocket_size={int(prep['pocket'].sum())} "
         f"real_rg={real_rg:.3f} (Part B published: {PART_B_RG.get(target_name)})")

    cells = []
    for k in K_MODES_GRID:
        score = dcc_low(prep["coords"], prep["source"], cutoff=prep["cutoff"], k_modes=k)
        nulls = {}
        for null_type in NULL_TYPES:
            nulls[null_type] = _lowmode_null_3way(
                score, prep, null_type, target_rg=real_rg if null_type == "matched" else None,
            )
        ordering_ok = _ordering_ok(nulls["scattered"]["p_value"], nulls["matched"]["p_value"], nulls["compact"]["p_value"])
        cells.append({"k_modes": k, "nulls": nulls, "ordering_ok": ordering_ok})
        _log(
            f"[dcc_low] {target_name} k={k}: scattered p={nulls['scattered']['p_value']:.4f} | "
            f"matched p={nulls['matched']['p_value']:.4f} | compact p={nulls['compact']['p_value']:.4f} "
            f"| ordering_ok={ordering_ok}"
        )
    return {
        "target": target_name, "real_pocket_rg": real_rg,
        "part_b_published_rg": PART_B_RG.get(target_name), "cells": cells,
    }


def run_transport_bcr_abl1() -> dict:
    prep = _transport_prepare_target("BCR_ABL1")
    coords = _coords_from_prep(prep)
    real_rg = _real_pocket_rg(coords, prep["pocket"])
    n_residues, pocket_size = prep["n_residues"], int(prep["pocket"].sum())
    _log(f"[T(E=0)] BCR_ABL1: N={n_residues} pocket_size={pocket_size} "
         f"real_rg={real_rg:.3f} (Part B published: {PART_B_RG.get('BCR_ABL1')})")

    score = transmission_from_source(prep["L"], prep["source"], E=0.0)
    nulls = {}
    for null_type in NULL_TYPES:
        nulls[null_type] = _transport_null_3way(
            score, prep["pocket"], n_residues, pocket_size, coords, null_type,
            target_rg=real_rg if null_type == "matched" else None,
        )
    ordering_ok = _ordering_ok(nulls["scattered"]["p_value"], nulls["matched"]["p_value"], nulls["compact"]["p_value"])
    _log(
        f"[T(E=0)] BCR_ABL1: scattered p={nulls['scattered']['p_value']:.4f} | "
        f"matched p={nulls['matched']['p_value']:.4f} | compact p={nulls['compact']['p_value']:.4f} "
        f"| ordering_ok={ordering_ok}"
    )
    return {"target": "BCR_ABL1", "real_pocket_rg": real_rg,
            "part_b_published_rg": PART_B_RG.get("BCR_ABL1"), "nulls": nulls, "ordering_ok": ordering_ok}


def _coords_from_prep(prep: dict) -> np.ndarray:
    """`transport_observable_real_run.py`'s own `_prepare_target` does not
    return `coords` directly (only `L`/`H_new`) -- re-derive the same way
    it does internally (same target_config, same recipe), not a new
    fetch path."""
    from allostery.clean import load_target_config
    import run_challenge

    target_config = load_target_config("BCR_ABL1")
    apo, _holo = run_challenge._load_apo_holo("BCR_ABL1", target_config)
    return apo.coords


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = {"dcc_low": {}, "transport": {}}

    for target in ("CARDIAC_MYOSIN", "PTP1B"):
        try:
            results["dcc_low"][target] = run_dcc_low_target(target)
        except Exception as exc:
            results["dcc_low"][target] = {"target": target, "error": str(exc)}
            _log(f"[dcc_low] {target}: FAILED -- {exc!r}")
        with open(OUTPUT_DIR / "rg_matched_null_rerun.json", "w") as f:
            json.dump(results, f, indent=2)

    try:
        results["transport"]["BCR_ABL1"] = run_transport_bcr_abl1()
    except Exception as exc:
        results["transport"]["BCR_ABL1"] = {"target": "BCR_ABL1", "error": str(exc)}
        _log(f"[T(E=0)] BCR_ABL1: FAILED -- {exc!r}")
    with open(OUTPUT_DIR / "rg_matched_null_rerun.json", "w") as f:
        json.dump(results, f, indent=2)

    _log(f"wrote {OUTPUT_DIR / 'rg_matched_null_rerun.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
