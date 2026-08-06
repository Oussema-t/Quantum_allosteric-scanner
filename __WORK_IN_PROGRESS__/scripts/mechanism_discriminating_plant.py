#!/usr/bin/env python3
"""TASK-0168 -- mechanism-discriminating plant: does each observable
family detect the mechanism it claims to?

Plants two physically different constructions into the same real apo
topology (`plant.plant_channel`, Plant A -- a stiff communication channel;
new `plant.plant_mode`, Plant B -- a correlated low-mode/hinge
perturbation) and asks whether the "directed-channel" observable family
(`T(E=0)`, `ctqw`) and the "ensemble/mode" family (`dcc_low`) detect only
the mechanism each is justified on, or both equally (redundant).

**Scope decision, forced by a real structural finding (TASK-0167.002's
own Done section, reconfirmed directly before building on it): this
project's real-pipeline observables (`H_new`-based `ctqw`, `dcc_low`,
`prs_low`, `ground_state_relaxation`, `mode_coparticipation` as actually
called in `run_challenge.py`) are exactly plant-invariant to ANY
weight-only perturbation of `W` -- every one of them rebuilds its own
operator fresh from raw `coords` with a hardcoded unweighted/binary
contact matrix, with no argument through which a planted `W` could ever
reach them.** Only `transmission_from_source` on a directly-built
`hamiltonians.laplacian(W_planted)` responds in the real pipeline. This
script does NOT silently pretend otherwise. It:

  1. Uses `T(E=0)` and `time_averaged_ctqw_converged` -- both operator-
     generic functions -- applied directly to `laplacian(W_planted)`,
     the same convention [[TASK-0103]]'s own 44-node dumbbell test
     already established (operate on the raw planted operator, not
     `build_H_new`) -- not a deviation from precedent, a continuation
     of it.
  2. Adds `ground_state_relaxation` the same way, as the dumbbell's own
     well-tracker control (Planned Validation's mandatory scale-check).
  3. Builds a **new** `dcc_low_from_L` adapter -- the exact same math as
     `lowmode_predictor.dcc_low`, parameterized on an externally-given
     Laplacian instead of an internal coords-rebuild -- to give the
     "ensemble/mode" family a real representative that CAN see a planted
     `W` at all. `dcc_low`/`prs_low` themselves are structurally
     inert to any `W`-only plant (no `W` argument exists) and are
     reported as such, not silently included in a grid that could never
     move for them.

Certification pipeline reused, not reinvented, from
`positive_control_detection_curve.py`/`detection_curve_analysis.py`
(TASK-0167.002): gate1 (beats floor) -> gate2 (CI non-overlap) -> gate3
(stratified-AUC permutation null) -> gate4 (Bonferroni, N=3 real-
deployment family). **Trimmed from that task's own grid, explicit,
stated scope-narrowing given this task's P2/schedule-conditional
priority**: 2 targets (not 3, CARDIAC_MYOSIN's N^3 eigh cost dropped),
10 seeds (this task's own explicit floor, not TASK-0167.002's 20), one CI
method (spatial -- TASK-0167.002 found both methods gave identical LOD
on every cell), two null specs (scattered + compact -- TASK-0167.002
found compact and Rg-matched statistically indistinguishable at this
patch size).
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

from allostery.hamiltonians import build_H_new, laplacian  # noqa: E402
from allostery.lowmode_predictor import dcc_low, prs_low  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.metrics import spatial_block_bootstrap_ci, stratified_auc  # noqa: E402
from allostery.nulls import compact_patch  # noqa: E402
from allostery.plant import assert_confound_orthogonal, plant_channel, plant_mode, select_distal_patch  # noqa: E402
from allostery.propagators import ground_state_relaxation, time_averaged_ctqw_converged  # noqa: E402
from allostery.runlog import RunLogger  # noqa: E402
from allostery.transport import effective_resistance_from_source, transmission_from_source  # noqa: E402

from positive_control_detection_curve import (  # noqa: E402
    N_BOOT_CI,
    N_PERM_REPS,
    PATCH_SIZE,
    _draw_null_label,
    _prepare_target,
    _well_powered_max,
)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0168_mechanism_discriminating_plant"
TARGETS = ["KRAS_G12C", "BCR_ABL1"]  # CARDIAC_MYOSIN dropped -- N=704 eigh cost, explicit scope call
N_SEEDS = 10  # this task's own explicit Constraint floor
N_PATHS = 10  # plant_channel convention, matches TASK-0167.002
NULL_SPECS = ["scattered", "compact"]  # matched/compact indistinguishable per TASK-0167.002 -- dropped
ALPHA = 0.05
REAL_BONFERRONI_ALPHA = ALPHA / 3  # TASK-0145's own N_TARGETS_FOR_BONFERRONI convention
LOD_POWER = 0.80


# --------------------------------------------------------------------------
# New: an "ensemble family" adapter that CAN see a planted W (dcc_low itself
# cannot -- no W argument exists at all, see module docstring).
# --------------------------------------------------------------------------

def dcc_low_from_L(L: np.ndarray, source, k_modes: int = 20) -> np.ndarray:
    """Exactly `lowmode_predictor.dcc_low`'s own math (low-mode GNM
    dynamic cross-correlation magnitude to the seed), parameterized on an
    externally supplied Laplacian-like `L` instead of an internal
    `coords`-rebuild. Verified against `dcc_low` itself in this task's
    own test suite (identical output when `L` = the unweighted binary
    Kirchhoff `dcc_low` would have built itself)."""
    idx = np.atleast_1d(np.asarray(source, dtype=int))
    w, U = np.linalg.eigh(L)
    nz = w > 1e-8
    order = np.argsort(w)
    nz_sorted = [o for o in order if nz[o]]
    low = nz_sorted[:k_modes]
    lam = w[low]
    Uk = U[:, low]
    inv_lam = 1.0 / lam
    cov = (Uk * inv_lam[None, :]) @ Uk.T
    d = np.sqrt(np.clip(np.diag(cov), 1e-12, None))
    corr = cov / np.outer(d, d)
    return np.abs(corr[idx, :]).mean(axis=0)


# --------------------------------------------------------------------------
# Score adapters: all (L, seed_idx) -> (N,) score, operating directly on
# whatever Laplacian is handed in (planted or not) -- TASK-0103's own
# dumbbell adapter convention, not build_H_new.
# --------------------------------------------------------------------------

def score_T(L, seed_idx):
    return transmission_from_source(L, seed_idx, E=0.0)


def score_ctqw(L, seed_idx):
    return time_averaged_ctqw_converged(L, source=seed_idx, coherent=False)


def score_gsr(L, seed_idx):
    w = np.linalg.eigvalsh(L)
    gap = float(w[1] - w[0]) if w[1] > w[0] else 1.0
    t = 1.0 / gap
    return ground_state_relaxation(L, t, source=seed_idx)


def score_dcc(L, seed_idx):
    return dcc_low_from_L(L, seed_idx, k_modes=20)


def score_dcc_k10(L, seed_idx):
    """TASK-0203: [[TASK-0201]]'s actual PTP1B survival is `dcc_low` at
    `k_modes=10`, not this module's own `k_modes=20` default (chosen for
    cross-target consistency with [[TASK-0199]]'s representative set).
    Additive registry entry -- does not touch `score_dcc`/`dcc_low_from_L`
    or any existing KRAS_G12C/BCR_ABL1 cell, which are keyed by observable
    name (`dcc_low_from_L`) and would be unaffected regardless."""
    return dcc_low_from_L(L, seed_idx, k_modes=10)


OBSERVABLES = {
    "T_E0": {"family": "channel", "score_fn": score_T},
    "ctqw_converged": {"family": "channel", "score_fn": score_ctqw},
    "ground_state_relaxation": {"family": "control", "score_fn": score_gsr},
    "dcc_low_from_L": {"family": "ensemble", "score_fn": score_dcc},
    "dcc_low_from_L_k10": {"family": "ensemble", "score_fn": score_dcc_k10},
}

PLANTS = {
    "channel": plant_channel,
    "mode": plant_mode,
}


# --------------------------------------------------------------------------
# Plant B spectral-effect verification (TASK-0168's own explicit
# requirement -- "this is the step most likely to fail silently").
# --------------------------------------------------------------------------

def verify_mode_plant_spectral_effect(W0, W_planted, seed_idx, target_idx, n_check_modes=5):
    L0 = laplacian(W0, normalised=False)
    L1 = laplacian(W_planted, normalised=False)
    w0, v0 = np.linalg.eigh(L0)
    w1, v1 = np.linalg.eigh(L1)

    rows = []
    for k in range(1, 1 + n_check_modes):
        pre_seed = float(np.mean(v0[seed_idx, k]))
        pre_target = float(np.mean(v0[target_idx, k]))
        post_seed = float(np.mean(v1[seed_idx, k]))
        post_target = float(np.mean(v1[target_idx, k]))
        rows.append({
            "mode": k,
            "pre_eigval": float(w0[k]), "post_eigval": float(w1[k]),
            "pre_seed_amp": pre_seed, "pre_target_amp": pre_target,
            "post_seed_amp": post_seed, "post_target_amp": post_target,
            "pre_same_sign": bool(np.sign(pre_seed) == np.sign(pre_target)),
            "post_same_sign": bool(np.sign(post_seed) == np.sign(post_target)),
            "pre_min_abs": float(min(abs(pre_seed), abs(pre_target))),
            "post_min_abs": float(min(abs(post_seed), abs(post_target))),
        })
    return rows


# --------------------------------------------------------------------------
# Generic certification cell, TASK-0167.002's run_cell body parameterized
# by (plant_fn, score_fn) -- one CI method (spatial), two null specs.
# --------------------------------------------------------------------------

def run_cell_generic(prep, mechanism, obs_name, plant_fn, score_fn, strength, seed, seed_cache, plant_kwargs=None):
    coords, seed_idx, cutoff = prep["coords"], prep["seed_idx"], prep["cutoff"]
    n, mask, shells = prep["n"], prep["mask"], prep["shells"]
    W0 = prep["W0"]
    plant_kwargs = plant_kwargs or {}

    if seed not in seed_cache:
        patch_rng = np.random.default_rng(1_000_000 + seed)
        patch = select_distal_patch(coords, W0, seed_idx, PATCH_SIZE, patch_rng, cutoff=cutoff)
        label = np.zeros(n, dtype=int)
        label[patch] = 1
        seed_cache[seed] = {"patch": patch, "label": label}
    patch, label = seed_cache[seed]["patch"], seed_cache[seed]["label"]

    plant_rng = np.random.default_rng(2_000_000 + seed)
    W_planted, plant_report = plant_fn(W0, seed_idx, patch, strength, rng=plant_rng, **plant_kwargs) \
        if mechanism == "mode" else plant_fn(W0, seed_idx, patch, strength, N_PATHS, plant_rng)
    assert_confound_orthogonal(W0, W_planted, coords, seed_idx, label, cutoff=cutoff)

    L_planted = laplacian(W_planted, normalised=False)
    score = score_fn(L_planted, seed_idx)

    floor_scores = np.stack(prep["floor_candidates"])[:, mask]
    floor_aucs = [float(_auc(fs, label[mask])) for fs in floor_scores]
    max_floor_auc = float(np.max(floor_aucs))
    winning_floor = floor_scores[int(np.argmax(floor_aucs))]
    floor_ci_sp = spatial_block_bootstrap_ci(coords[mask], winning_floor, label[mask], n_boot=N_BOOT_CI, rng=np.random.default_rng(42))

    point_auc = float(_auc(score[mask], label[mask]))
    gate1 = point_auc > max_floor_auc

    ci_sp = spatial_block_bootstrap_ci(coords[mask], score[mask], label[mask], n_boot=N_BOOT_CI, rng=np.random.default_rng(42))
    gate2 = not (ci_sp[1] > floor_ci_sp[2] or floor_ci_sp[1] > ci_sp[2])

    strat = stratified_auc(score, label, shells)
    real_shell, real_max = _well_powered_max(strat)
    target_rg = float(np.linalg.norm(coords[patch] - coords[patch].mean(axis=0), axis=1).mean())

    null_results = {}
    for null_spec in NULL_SPECS:
        rng = np.random.default_rng(5_000_000 + seed)
        null_maxes = []
        for _ in range(N_PERM_REPS):
            try:
                lab = _draw_null_label(null_spec, coords, n, PATCH_SIZE, rng, target_rg)
            except RuntimeError:
                continue
            _, null_max = _well_powered_max(stratified_auc(score, lab, shells))
            if np.isfinite(null_max):
                null_maxes.append(null_max)
        null_maxes = np.array(null_maxes) if null_maxes else np.array([np.nan])
        p_value = float((null_maxes >= real_max).mean()) if np.isfinite(real_max) else float("nan")
        gate4 = bool(np.isfinite(p_value) and p_value < REAL_BONFERRONI_ALPHA)
        null_results[null_spec] = {"p_value": p_value, "certified": bool(gate1 and gate2 and gate4)}

    return {
        "mechanism": mechanism, "observable": obs_name, "strength": strength, "seed": seed,
        "point_auc": point_auc, "max_floor_auc": max_floor_auc, "gate1_beats_floor": gate1,
        "ci_spatial": list(ci_sp), "floor_ci_spatial": list(floor_ci_sp), "gate2_ci": gate2,
        "well_powered_max_auc": real_max, "nulls": null_results,
        "plant_n_edges_modified": len(plant_report.edges_modified),
    }


def _certified(cell, null_spec):
    return cell["nulls"][null_spec]["certified"]


def p_certified(cells, null_spec):
    n = len(cells)
    if n == 0:
        return {"n": 0, "p": float("nan")}
    k = sum(1 for c in cells if _certified(c, null_spec))
    return {"n": n, "k": k, "p": k / n}


def extract_lod(by_strength, null_spec):
    for s in sorted(by_strength.keys()):
        stats = p_certified(by_strength[s], null_spec)
        if stats["p"] >= LOD_POWER:
            return s
    return float("inf")


# --------------------------------------------------------------------------
# Dose-axis calibration: induced conductance change for both plants,
# same seed→patch mean-conductance convention as TASK-0167.002.
# --------------------------------------------------------------------------

def calibrate_dose_axis(prep, patch, strengths, n_seeds=3):
    coords, seed_idx, cutoff = prep["coords"], prep["seed_idx"], prep["cutoff"]
    W0 = prep["W0"]
    L0 = laplacian(W0, normalised=False)
    baseline = float(effective_resistance_from_source(L0, seed_idx)[patch].mean())

    out = {}
    for mechanism, plant_fn in PLANTS.items():
        out[mechanism] = {}
        for s in strengths:
            vals = []
            for seed in range(n_seeds):
                rng = np.random.default_rng(2_000_000 + seed)
                if mechanism == "channel":
                    W_planted, _ = plant_fn(W0, seed_idx, patch, s, N_PATHS, rng)
                else:
                    W_planted, _ = plant_fn(W0, seed_idx, patch, s, rng=rng)
                L = laplacian(W_planted, normalised=False)
                cond = float(effective_resistance_from_source(L, seed_idx)[patch].mean())
                vals.append(cond)
            mean_cond = float(np.mean(vals))
            out[mechanism][s] = {
                "mean_conductance": mean_cond, "sd_conductance": float(np.std(vals)),
                "ratio_vs_baseline": mean_cond / baseline if baseline else float("nan"),
            }
    return {"baseline_conductance": baseline, "by_mechanism": out}


# --------------------------------------------------------------------------
# Pre-plant redundancy: Spearman rho between every real (unplanted) score
# vector -- high rho pre-plant already predicts non-discrimination.
# --------------------------------------------------------------------------

def redundancy_matrix(prep):
    coords, bfactors, seed_idx, cutoff = prep["coords"], prep["bfactors"], prep["seed_idx"], prep["cutoff"]
    W0 = prep["W0"]
    L0 = laplacian(W0, normalised=False)

    H_new = build_H_new(coords, bfactors, cutoff=cutoff)
    scores = {
        "T_E0_on_L0": score_T(L0, seed_idx),
        "ctqw_on_L0": score_ctqw(L0, seed_idx),
        "gsr_on_L0": score_gsr(L0, seed_idx),
        "dcc_low_from_L0": score_dcc(L0, seed_idx),
        "ctqw_converged_H_new": time_averaged_ctqw_converged(H_new, source=seed_idx, coherent=False),
        "dcc_low_real": dcc_low(coords, seed_idx, cutoff=cutoff, k_modes=20),
        "prs_low_real": prs_low(coords, seed_idx, cutoff=cutoff, k_modes=20),
    }
    names = list(scores.keys())
    n = len(names)
    rho = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            rho[i, j] = spearmanr(scores[names[i]], scores[names[j]]).statistic
    return {"names": names, "rho": rho.tolist()}


# --------------------------------------------------------------------------
# Protein-scale reproduction of TASK-0103's double dissociation: does GSR
# track a real diagonal well while ctqw tracks the channel plant, at
# N=169-451 instead of the original 44-node dumbbell? Light check --
# point AUCs over n_seeds patches, no CI/permutation (qualitative
# replication of TASK-0103's own C2/C3 assertions, not a new LOD claim).
# --------------------------------------------------------------------------

def well_vs_channel_scale_check(prep, n_seeds=10, well_depth=5.0, channel_strength=8.0):
    coords, seed_idx, cutoff = prep["coords"], prep["seed_idx"], prep["cutoff"]
    n, mask = prep["n"], prep["mask"]
    W0 = prep["W0"]

    gsr_well, ctqw_well, gsr_channel, ctqw_channel = [], [], [], []
    for seed in range(n_seeds):
        patch_rng = np.random.default_rng(1_000_000 + seed)
        patch = select_distal_patch(coords, W0, seed_idx, PATCH_SIZE, patch_rng, cutoff=cutoff)
        label = np.zeros(n, dtype=int)
        label[patch] = 1

        L_well = laplacian(W0, normalised=False).copy()
        for i in patch:
            L_well[i, i] -= well_depth
        s_gsr_well = score_gsr(L_well, seed_idx)
        s_ctqw_well = score_ctqw(L_well, seed_idx)
        gsr_well.append(float(_auc(s_gsr_well[mask], label[mask])))
        ctqw_well.append(float(_auc(s_ctqw_well[mask], label[mask])))

        plant_rng = np.random.default_rng(2_000_000 + seed)
        W_channel, _ = plant_channel(W0, seed_idx, patch, channel_strength, N_PATHS, plant_rng)
        L_channel = laplacian(W_channel, normalised=False)
        s_gsr_channel = score_gsr(L_channel, seed_idx)
        s_ctqw_channel = score_ctqw(L_channel, seed_idx)
        gsr_channel.append(float(_auc(s_gsr_channel[mask], label[mask])))
        ctqw_channel.append(float(_auc(s_ctqw_channel[mask], label[mask])))

    return {
        "well_depth": well_depth, "channel_strength": channel_strength, "n_seeds": n_seeds,
        "gsr_mean_auc_well": float(np.mean(gsr_well)), "ctqw_mean_auc_well": float(np.mean(ctqw_well)),
        "gsr_mean_auc_channel": float(np.mean(gsr_channel)), "ctqw_mean_auc_channel": float(np.mean(ctqw_channel)),
        "double_dissociation": bool(np.mean(gsr_well) > np.mean(ctqw_well) and np.mean(gsr_channel) < np.mean(ctqw_channel)),
    }


# --------------------------------------------------------------------------
# Main grid driver -- checkpointed per cell, resumable.
# --------------------------------------------------------------------------

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--target", nargs="+", default=TARGETS)
    parser.add_argument("--strength", nargs="+", type=float, default=[0.0, 4.0, 16.0])
    parser.add_argument("--n-seeds", type=int, default=N_SEEDS)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "grid.json")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    log = RunLogger(OUTPUT_DIR / "run.jsonl", run_name="task0168_mechanism_discriminating_plant")

    results = {}
    if args.output.exists():
        results = json.loads(args.output.read_text())

    for target_name in args.target:
        if target_name not in results:
            results[target_name] = {"redundancy": None, "dose_axis": None, "well_vs_channel": None, "spectral_check": None, "cells": {}}
        log.step(f"{target_name}:prepare_start")
        prep = _prepare_target(target_name)
        log.step(f"{target_name}:prepare_done", n=prep["n"], n_seed=len(prep["seed_idx"]))

        if results[target_name]["redundancy"] is None:
            results[target_name]["redundancy"] = redundancy_matrix(prep)
            args.output.write_text(json.dumps(results, indent=2, default=str))
            log.step(f"{target_name}:redundancy_done")

        # one fixed patch (seed=0's own select_distal_patch draw) for dose calibration + spectral check
        patch0 = select_distal_patch(prep["coords"], prep["W0"], prep["seed_idx"], PATCH_SIZE, np.random.default_rng(1_000_000), cutoff=prep["cutoff"])

        if results[target_name]["dose_axis"] is None:
            results[target_name]["dose_axis"] = calibrate_dose_axis(prep, patch0, args.strength, n_seeds=3)
            args.output.write_text(json.dumps(results, indent=2, default=str))
            log.step(f"{target_name}:dose_axis_done")

        if results[target_name]["spectral_check"] is None:
            W_moded, _ = plant_mode(prep["W0"], prep["seed_idx"], patch0, max(args.strength), rng=np.random.default_rng(2_000_000))
            results[target_name]["spectral_check"] = verify_mode_plant_spectral_effect(
                prep["W0"], W_moded, prep["seed_idx"], patch0, n_check_modes=5,
            )
            args.output.write_text(json.dumps(results, indent=2, default=str))
            log.step(f"{target_name}:spectral_check_done")

        if results[target_name]["well_vs_channel"] is None:
            results[target_name]["well_vs_channel"] = well_vs_channel_scale_check(prep, n_seeds=10)
            args.output.write_text(json.dumps(results, indent=2, default=str))
            log.step(f"{target_name}:well_vs_channel_done", **results[target_name]["well_vs_channel"])

        seed_cache: dict = {}
        for mechanism in PLANTS:
            for obs_name, obs in OBSERVABLES.items():
                for strength in args.strength:
                    for seed in range(args.n_seeds):
                        cell_key = f"{mechanism}/{obs_name}/{strength}/{seed}"
                        if cell_key in results[target_name]["cells"]:
                            continue
                        t0 = time.time()
                        try:
                            cell = run_cell_generic(prep, mechanism, obs_name, PLANTS[mechanism], obs["score_fn"], strength, seed, seed_cache)
                        except Exception as exc:  # noqa: BLE001
                            cell = {"error": str(exc)}
                        results[target_name]["cells"][cell_key] = cell
                        args.output.write_text(json.dumps(results, indent=2, default=str))
                        if "error" not in cell:
                            log.step(
                                f"{target_name}:{cell_key}", point_auc=cell["point_auc"],
                                gate1=cell["gate1_beats_floor"], gate2=cell["gate2_ci"],
                                cert_scattered=cell["nulls"]["scattered"]["certified"],
                                cert_compact=cell["nulls"]["compact"]["certified"],
                                elapsed_s=round(time.time() - t0, 1),
                            )
                        else:
                            log.step(f"{target_name}:{cell_key}:FAILED", error=cell["error"])

    log.finish()
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
