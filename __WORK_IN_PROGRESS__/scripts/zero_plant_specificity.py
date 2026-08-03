#!/usr/bin/env python3
"""TASK-0167.003 -- zero-plant specificity (measured false-positive rate)
and the null-calibration close-out.

Reuses [[TASK-0167.002]]'s own `_prepare_target`/`_well_powered_max`
helpers directly (`positive_control_detection_curve.py`), not re-derived,
so this task's own `strength=0` measurement is a genuine independent
route to the same number .002's own `strength=0.0` grid row computes --
a disagreement between the two is a bug in one of them (this task's own
Planned Validation).

**A real, documented optimization over naively copying .002's per-cell
loop**: at `strength=0`, `plant_channel` returns `W0` bit-identical by
construction (TASK-0167.001's own identity guarantee, re-verified below,
not assumed) -- so the SCORE is one fixed vector per target, not
recomputed per patch. The permutation null for the "scattered" and
"compact" null specs is *also* patch-independent (the draw only depends
on `pocket_size`, fixed at 14, never on which patch is being tested) --
so those two null distributions are built ONCE per target and reused
across all 500+ test patches, not redrawn 500+ times. Only the "matched"
null genuinely depends on the tested patch's own measured Rg and must be
redrawn per patch -- this is where the real compute cost concentrates,
and it is reduced (documented, not silently cut) for that reason alone.

Part A: measured end-to-end false-positive rate, 3 mandatory targets,
        3 null specs, >=500 distal compact patches each.
Part B: calibration statistic -- for all 7 pocket-scoreable targets, is
        the REAL pocket's own Rg inside each null spec's own draw
        distribution of Rg? (Pure geometry, no scoring, cheap.)
Part C: positive control on the calibration statistic itself (a
        deliberately scattered draw must show up anti-conservative; a
        deliberately over-compact draw, over-conservative).
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

from allostery.clean import load_target_config  # noqa: E402
from allostery.hamiltonians import laplacian  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.metrics import block_bootstrap_ci, spatial_block_bootstrap_ci, stratified_auc  # noqa: E402
from allostery.nulls import compact_patch, compact_patch_matched, radius_of_gyration  # noqa: E402
from allostery.plant import assert_confound_orthogonal, plant_channel, select_distal_patch  # noqa: E402
from allostery.transport import transmission_from_source  # noqa: E402

import run_challenge  # noqa: E402
from positive_control_detection_curve import (  # noqa: E402
    _prepare_target, _well_powered_max, N_BOOT_CI, N_PERM_REPS, ALPHA,
    PATCH_SIZE, N_PATHS, N_SEEDS, STRENGTHS,
)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0167003_specificity"
MANDATORY_TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
POCKET_SCOREABLE_TARGETS = [
    "KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "PTP1B", "GLUCOKINASE", "CASPASE1", "CASPASE7",
]
N_TEST_PATCHES = 500
N_NULL_DRAWS_FOR_CALIBRATION = 2000  # geometry-only, cheap -- Rg distribution resolution
NULL_SPECS = ["scattered", "compact", "matched"]
MATCHED_N_PERM_REPS = 200  # documented reduction: matched null is redrawn per test patch
# (target_rg varies per patch), unlike scattered/compact which are patch-independent
# and precomputed once. 500 patches x 200 reps x rejection-sampled draw is already the
# dominant cost in this script; 1000 would 5x it for a p-value resolution finer than
# this task's own alpha=0.05/Bonferroni thresholds need. State the reduction, don't hide it.


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _draw_null_label_patch_independent(null_spec: str, coords: np.ndarray, n: int,
                                        pocket_size: int, rng: np.random.Generator) -> np.ndarray:
    """Scattered/compact only -- no target_rg dependency, safe to precompute once."""
    if null_spec == "scattered":
        return rng.choice(n, size=pocket_size, replace=False)
    elif null_spec == "compact":
        return compact_patch(coords, pocket_size, rng)
    raise ValueError(f"{null_spec} depends on the tested patch, use the per-patch path")


def _precompute_null_max_distribution(score, coords, pocket_size, shells, null_spec, seed, n_reps):
    rng = np.random.default_rng(seed)
    null_maxes = []
    for _ in range(n_reps):
        idx = _draw_null_label_patch_independent(null_spec, coords, len(score), pocket_size, rng)
        lab = np.zeros(len(score), dtype=int)
        lab[idx] = 1
        _, null_max = _well_powered_max(stratified_auc(score, lab, shells))
        if np.isfinite(null_max):
            null_maxes.append(null_max)
    return np.array(null_maxes)


def _matched_null_max_distribution(score, coords, pocket_size, shells, target_rg, seed, n_reps):
    rng = np.random.default_rng(seed)
    null_maxes = []
    n_infeasible = 0
    for _ in range(n_reps):
        try:
            idx = compact_patch_matched(coords, pocket_size, rng, target_rg=target_rg, tol=0.35, max_attempts=2000)
        except RuntimeError:
            n_infeasible += 1
            continue
        lab = np.zeros(len(score), dtype=int)
        lab[idx] = 1
        _, null_max = _well_powered_max(stratified_auc(score, lab, shells))
        if np.isfinite(null_max):
            null_maxes.append(null_max)
    return np.array(null_maxes), n_infeasible


def part_a_specificity(target_name: str, n_patches: int = N_TEST_PATCHES) -> dict:
    _log(f"{target_name}: Part A -- preparing...")
    prep = _prepare_target(target_name)
    coords, seed_idx, cutoff = prep["coords"], prep["seed_idx"], prep["cutoff"]
    n, mask, shells, W0 = prep["n"], prep["mask"], prep["shells"], prep["W0"]

    # Identity guarantee, re-verified directly (not assumed): strength=0 -> W0 bit-identical.
    dummy_patch = select_distal_patch(coords, W0, seed_idx, PATCH_SIZE, np.random.default_rng(0), cutoff=cutoff)
    W_zero, _ = plant_channel(W0, seed_idx, dummy_patch, 0.0, N_PATHS, np.random.default_rng(0))
    identity_holds = bool(np.array_equal(W0, W_zero))
    if not identity_holds:
        raise RuntimeError("strength=0 plant is not bit-identical to W0 -- TASK-0167.001's own guarantee violated")

    L0 = laplacian(W0, normalised=False)
    score = transmission_from_source(L0, seed_idx, E=0.0)

    floor_scores = np.stack(prep["floor_candidates"])[:, mask]

    _log(f"{target_name}: precomputing patch-independent null distributions (scattered/compact)...")
    null_max_precomputed = {
        spec: _precompute_null_max_distribution(score, coords, PATCH_SIZE, shells, spec,
                                                 seed=9_000_000, n_reps=N_PERM_REPS)
        for spec in ("scattered", "compact")
    }

    # TASK-0189 (Reviewer finding F1, 2026-08-03): this is `.002`'s own
    # COLLECTION-script constant (`positive_control_detection_curve.py:236`),
    # copied here without ever fixing the comment's claim -- it is the wrong
    # deployment-level family (treats this script's own internal
    # strength/seed replicate grid as 160 simultaneous real hypothesis
    # tests, not TASK-0145's "correct across targets" convention), AND at
    # `3.125e-4` it sits below `1/N_PERM_REPS=1e-3` (`1/MATCHED_N_PERM_REPS
    # =5e-3`), so `gate4` could only ever fire at `p_value == 0.0` exactly.
    # `.002` corrects this in a *separate analysis script*
    # (`detection_curve_analysis.py`'s own `REAL_BONFERRONI_ALPHA=0.05/3`);
    # this collection script's own `certified`/`alpha_measured` fields below
    # inherit the same defect and must NOT be read as the deployment-level
    # false-positive rate -- `zero_plant_specificity_analysis.py` is the
    # corrected re-analysis, mirroring `.002`'s own pattern exactly.
    bonferroni_alpha = ALPHA / (len(STRENGTHS) * N_SEEDS)
    cells = []
    rng_patches = np.random.default_rng(3_000_000)
    for i in range(n_patches):
        patch = select_distal_patch(coords, W0, seed_idx, PATCH_SIZE, rng_patches, cutoff=cutoff)
        label = np.zeros(n, dtype=int)
        label[patch] = 1
        target_rg = radius_of_gyration(coords, patch)

        floor_aucs = [float(_auc(fs, label[mask])) for fs in floor_scores]
        max_floor_auc = float(np.max(floor_aucs))
        winning_floor = floor_scores[int(np.argmax(floor_aucs))]

        point_auc = float(_auc(score[mask], label[mask]))
        gate1 = point_auc > max_floor_auc

        ci_seq = block_bootstrap_ci(score[mask], label[mask], n_boot=N_BOOT_CI, rng=np.random.default_rng(42))
        floor_ci_seq = block_bootstrap_ci(winning_floor, label[mask], n_boot=N_BOOT_CI, rng=np.random.default_rng(42))
        gate2_seq = not (ci_seq[1] > floor_ci_seq[2] or floor_ci_seq[1] > ci_seq[2])

        strat = stratified_auc(score, label, shells)
        _, real_max = _well_powered_max(strat)

        cell_nulls = {}
        for spec in NULL_SPECS:
            if spec in ("scattered", "compact"):
                null_maxes = null_max_precomputed[spec]
                n_infeasible = 0
            else:
                null_maxes, n_infeasible = _matched_null_max_distribution(
                    score, coords, PATCH_SIZE, shells, target_rg,
                    seed=7_000_000 + i, n_reps=MATCHED_N_PERM_REPS,
                )
            p_value = float((null_maxes >= real_max).mean()) if (len(null_maxes) and np.isfinite(real_max)) else float("nan")
            gate4 = bool(np.isfinite(p_value) and p_value < bonferroni_alpha)
            cell_nulls[spec] = {
                "p_value": p_value, "n_infeasible": int(n_infeasible), "n_reps_used": int(len(null_maxes)),
                "certified": bool(gate1 and gate2_seq and gate4),
            }
        cells.append({
            "patch": patch.tolist(), "target_rg": float(target_rg),
            "point_auc": point_auc, "max_floor_auc": max_floor_auc, "gate1": gate1,
            "gate2_seq": gate2_seq, "well_powered_max_auc": real_max, "nulls": cell_nulls,
        })
        if (i + 1) % 100 == 0:
            _log(f"{target_name}: {i+1}/{n_patches} patches done")

    # TASK-0189: `certified`/`alpha_measured` below use `bonferroni_alpha`
    # (the uncorrected, unreachable family bar -- see that constant's own
    # comment above). Kept as-is here for provenance/reproducibility of the
    # raw collection output -- `zero_plant_specificity_analysis.py` is
    # where the deployment-level (TASK-0145 family=3) corrected numbers are
    # actually computed, from these same cells' own stored raw `p_value`.
    alpha_measured = {}
    for spec in NULL_SPECS:
        certs = np.array([c["nulls"][spec]["certified"] for c in cells])
        k, m = int(certs.sum()), len(certs)
        p_hat = k / m if m else float("nan")
        # Wilson score interval, 95%
        z = 1.96
        denom = 1 + z**2 / m
        centre = p_hat + z**2 / (2 * m)
        half = z * np.sqrt(p_hat * (1 - p_hat) / m + z**2 / (4 * m**2))
        lo, hi = (centre - half) / denom, (centre + half) / denom
        alpha_measured[spec] = {"k": k, "m": m, "alpha_hat": p_hat, "ci95": [float(lo), float(hi)]}

    return {
        "identity_holds": identity_holds,
        "alpha_measured": alpha_measured,
        "n_patches": n_patches,
        "cells": cells,
    }


def part_b_calibration(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))
    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        return {"error": "no resolvable pocket"}
    coords = apo.coords
    pocket_idx = np.where(labels_obj.pocket)[0]
    real_rg = radius_of_gyration(coords, pocket_idx)
    pocket_size = int(len(pocket_idx))

    rng = np.random.default_rng(4_000_000)
    result = {"real_pocket_rg": real_rg, "pocket_size": pocket_size, "nulls": {}}
    for spec in ("scattered", "compact"):
        rgs = []
        for _ in range(N_NULL_DRAWS_FOR_CALIBRATION):
            idx = _draw_null_label_patch_independent(spec, coords, len(coords), pocket_size, rng)
            rgs.append(radius_of_gyration(coords, idx))
        rgs = np.array(rgs)
        percentile = float((rgs <= real_rg).mean())
        result["nulls"][spec] = {"draw_rg_mean": float(rgs.mean()), "draw_rg_std": float(rgs.std()),
                                  "real_pocket_percentile": percentile}
    return result


def part_c_calibration_statistic_positive_control(coords: np.ndarray) -> dict:
    """Deliberately-bad draws must register as such under this task's own
    calibration statistic -- if it cannot detect known miscalibration, it
    cannot certify calibration it claims to find."""
    n = len(coords)
    size = 14
    rng = np.random.default_rng(11)
    scattered_rgs = np.array([
        radius_of_gyration(coords, rng.choice(n, size=size, replace=False)) for _ in range(1000)
    ])
    compact_rgs = np.array([
        radius_of_gyration(coords, compact_patch(coords, size, rng)) for _ in range(1000)
    ])
    # deliberately over-compact: half the patch size (denser core than any real patch)
    over_compact_rgs = np.array([
        radius_of_gyration(coords, compact_patch(coords, size // 2, rng)) for _ in range(1000)
    ])
    # A "real-pocket-like" reference Rg: the median of the compact draws' own distribution
    # (stand-in for a real pocket's Rg for this synthetic check only).
    ref_rg = float(np.median(compact_rgs))
    return {
        "reference_rg": ref_rg,
        "scattered_percentile_of_reference": float((scattered_rgs <= ref_rg).mean()),
        "over_compact_percentile_of_reference": float((over_compact_rgs <= ref_rg).mean()),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    results = {}

    for target_name in MANDATORY_TARGETS:
        out_path = OUTPUT_DIR / f"part_a_{target_name}.json"
        if out_path.exists():
            _log(f"{target_name}: Part A already computed, loading")
            with open(out_path) as f:
                results.setdefault("part_a", {})[target_name] = json.load(f)
            continue
        part_a = part_a_specificity(target_name)
        results.setdefault("part_a", {})[target_name] = part_a
        with open(out_path, "w") as f:
            json.dump(part_a, f, indent=2)
        _log(f"{target_name}: Part A done, alpha_measured={part_a['alpha_measured']}")

    for target_name in POCKET_SCOREABLE_TARGETS:
        _log(f"{target_name}: Part B (calibration statistic)...")
        try:
            part_b = part_b_calibration(target_name)
        except Exception as exc:
            part_b = {"error": str(exc)}
            _log(f"{target_name}: Part B FAILED -- {exc!r}")
        results.setdefault("part_b", {})[target_name] = part_b

    # Part C -- use KRAS_G12C's coords as a real-topology stand-in.
    prep = _prepare_target("KRAS_G12C")
    results["part_c"] = part_c_calibration_statistic_positive_control(prep["coords"])

    with open(OUTPUT_DIR / "zero_plant_specificity_full.json", "w") as f:
        json.dump(results, f, indent=2)
    _log(f"wrote {OUTPUT_DIR / 'zero_plant_specificity_full.json'}")


if __name__ == "__main__":
    main()
