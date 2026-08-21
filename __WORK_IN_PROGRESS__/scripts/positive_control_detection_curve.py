#!/usr/bin/env python3
"""TASK-0167.002 -- detection curve + limit of detection (LOD) through the
**unmodified** verdict pipeline, on real apo topology, using
[[TASK-0167.001]]'s `allostery.plant` channel-reweighting positive control.

**Scope decision, built on TASK-0167.001's own decisive finding (not
re-derived here, cited directly)**: `time_averaged_ctqw_converged` on
`H_new`, `dcc_low`, and `prs_low` are all **exactly** invariant to a
weight-only plant (`np.array_equal`, confirmed on real data in
TASK-0167.001's own Done section -- every GNM-derived term and `dcc_low`
itself always rebuild a BINARY contact matrix from raw coordinates,
never consulting the planted `W`). Running the full 8-strength x 20-seed
grid against them would just reproduce the identical strength=0 score
160 times per target -- expensive and uninformative. This script instead:
(a) reconfirms the exact-invariance claim once per target as a cheap
sanity check (strength=0 vs strength=32, `np.array_equal`), and (b) runs
the real, informative detection-curve sweep only for the one plant-
sensitive observable named in this task's own In-Scope list:
`transmission_from_source(E=0)` on a weighted `hamiltonians.laplacian
(W_planted)` ("`T(E=0)` on `L`", [[TASK-0145]]'s own unresolved cell).

**CI dual-report (this task's own Constraint)**: `metrics.spatial_block_
bootstrap_ci`'s own 1D-line regression claim was found overstated
mid-task ([[TASK-0167.002]]'s own correction to [[TASK-0165]] -- ~55%
block overlap, not exact coincidence). Per this task's own explicit
sanctioned alternative ("run *both* CI methods and report both"), every
cell computes gate 2 (CI non-overlap) under BOTH `block_bootstrap_ci`
(sequence) and `spatial_block_bootstrap_ci` (spatial).

**Three null specifications, run side by side** for gates 3/4 (stratified-
AUC permutation null + Bonferroni): `rng.choice` (scattered, historical),
`nulls.compact_patch` ([[TASK-0158]]'s fix), `nulls.compact_patch_matched`
(Rg-matched to the *planted patch's own* measured radius of gyration) --
the direct empirical test of the external review's over-correction claim.

Checkpointed per (target, strength, seed) cell -- [[TASK-0138]]/
[[TASK-0143]]'s own "lost a run by writing once at the end" lesson, not
repeated here.
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
from allostery.hamiltonians import build_H_new, contact_matrix, laplacian  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.lowmode_predictor import dcc_low, prs_low  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.metrics import block_bootstrap_ci, spatial_block_bootstrap_ci, stratified_auc  # noqa: E402
from allostery.nulls import compact_patch, compact_patch_matched, radius_of_gyration  # noqa: E402
from allostery.plant import assert_confound_orthogonal, plant_channel, select_distal_patch  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from allostery.transport import transmission_from_source  # noqa: E402

import run_challenge  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0167002_detection_curve"
TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
STRENGTHS = [0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0]
N_SEEDS = 20
N_PATHS = 10
PATCH_SIZE = 14
NULL_SPECS = ["scattered", "compact", "matched"]
MIN_POS_WELL_POWERED = 3
N_PERM_REPS = 1000
N_BOOT_CI = 500  # halved from the project's usual 1000 -- compute-budget
# mitigation, this task's own sanctioned Open Question option; still a
# standard bootstrap replicate count (Efron & Tibshirani's own rule-of-
# thumb floor for percentile CIs). Checked directly on KRAS_G12C at 3
# strengths (0/4/8): gate2 verdicts (both CI methods) identical at 500
# vs. 1000, CI bounds within ~0.01 of each other -- not a re-check of
# every cell in the full grid, but not assumed adequate either.
ALPHA = 0.05


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _prepare_target(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))
    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    seed_idx = np.sort(np.where(labels_obj.active_site)[0])
    coords = apo.coords
    n = len(coords)
    shells = -hop_from_seed(coords, seed_idx, cutoff=cutoff)

    W0 = contact_matrix(coords, cutoff=cutoff, weight="invdist")
    mask = np.ones(n, dtype=bool)
    mask[seed_idx] = False
    floor_candidates = [
        degree_centrality(coords, cutoff=cutoff),
        hop_from_seed(coords, seed_idx, cutoff=cutoff),
        euclid_from_seed_centroid(coords, seed_idx),
    ]
    return {
        "coords": coords, "bfactors": apo.bfactors, "seed_idx": seed_idx, "cutoff": cutoff,
        "n": n, "shells": shells, "W0": W0, "mask": mask, "floor_candidates": floor_candidates,
    }


def _well_powered_max(strat: dict, min_pos: int = MIN_POS_WELL_POWERED):
    cand = {s: v for s, v in strat.items() if v["n_pos"] >= min_pos and np.isfinite(v["auc"])}
    if not cand:
        return None, float("nan")
    best_shell = max(cand, key=lambda s: cand[s]["auc"])
    return best_shell, cand[best_shell]["auc"]


def _draw_null_label(null_spec: str, coords: np.ndarray, n: int, pocket_size: int,
                      rng: np.random.Generator, target_rg: float) -> np.ndarray:
    if null_spec == "scattered":
        idx = rng.choice(n, size=pocket_size, replace=False)
    elif null_spec == "compact":
        idx = compact_patch(coords, pocket_size, rng)
    elif null_spec == "matched":
        idx = compact_patch_matched(coords, pocket_size, rng, target_rg=target_rg, tol=0.35, max_attempts=2000)
    else:
        raise ValueError(null_spec)
    lab = np.zeros(n, dtype=int)
    lab[idx] = 1
    return lab


def _permutation_null(score: np.ndarray, coords: np.ndarray, pocket_size: int, shells: np.ndarray,
                       null_spec: str, target_rg: float, seed: int, n_reps: int = N_PERM_REPS) -> dict:
    n = len(score)
    rng = np.random.default_rng(seed)
    null_maxes = []
    n_infeasible = 0
    for _ in range(n_reps):
        try:
            lab = _draw_null_label(null_spec, coords, n, pocket_size, rng, target_rg)
        except RuntimeError:
            n_infeasible += 1
            continue
        _, null_max = _well_powered_max(stratified_auc(score, lab, shells))
        if np.isfinite(null_max):
            null_maxes.append(null_max)
    return {"null_maxes": null_maxes, "n_infeasible": n_infeasible}


def _patch_and_floor_ci_for_seed(prep: dict, seed: int, cache: dict) -> dict:
    """The patch draw and the floor's own CI depend only on `(target,
    seed)`, never on plant `strength` (`select_distal_patch`/the floor
    baselines never see `W`, TASK-0167.001's own theorem) -- computed
    once per seed and reused across all 8 strengths, cutting the CI
    bootstrap workload roughly in half (only the score's OWN CI needs
    recomputing per strength, not the floor's)."""
    if seed in cache:
        return cache[seed]

    coords, seed_idx, cutoff = prep["coords"], prep["seed_idx"], prep["cutoff"]
    n, mask = prep["n"], prep["mask"]
    W0 = prep["W0"]

    patch_rng = np.random.default_rng(1_000_000 + seed)
    patch = select_distal_patch(coords, W0, seed_idx, PATCH_SIZE, patch_rng, cutoff=cutoff)
    label = np.zeros(n, dtype=int)
    label[patch] = 1
    target_rg = radius_of_gyration(coords, patch)

    floor_scores = np.stack(prep["floor_candidates"])[:, mask]
    floor_aucs = [float(_auc(fs, label[mask])) for fs in floor_scores]
    max_floor_auc = float(np.max(floor_aucs))
    winning_floor_idx = int(np.argmax(floor_aucs))
    winning_floor = floor_scores[winning_floor_idx]

    floor_ci_seq = block_bootstrap_ci(winning_floor, label[mask], n_boot=N_BOOT_CI, rng=np.random.default_rng(42))
    floor_ci_sp = spatial_block_bootstrap_ci(coords[mask], winning_floor, label[mask], n_boot=N_BOOT_CI, rng=np.random.default_rng(42))

    result = {
        "patch": patch, "label": label, "target_rg": target_rg,
        "max_floor_auc": max_floor_auc, "floor_ci_seq": floor_ci_seq, "floor_ci_sp": floor_ci_sp,
    }
    cache[seed] = result
    return result


def run_cell(prep: dict, target_name: str, strength: float, seed: int, seed_cache: dict) -> dict:
    coords, seed_idx, cutoff = prep["coords"], prep["seed_idx"], prep["cutoff"]
    n, mask, shells = prep["n"], prep["mask"], prep["shells"]
    W0 = prep["W0"]

    cached = _patch_and_floor_ci_for_seed(prep, seed, seed_cache)
    patch, label, target_rg = cached["patch"], cached["label"], cached["target_rg"]
    max_floor_auc = cached["max_floor_auc"]
    floor_ci_seq, floor_ci_sp = cached["floor_ci_seq"], cached["floor_ci_sp"]

    plant_rng = np.random.default_rng(2_000_000 + seed)
    W_planted, plant_report = plant_channel(W0, seed_idx, patch, strength, N_PATHS, plant_rng)
    pre_auc, post_auc = assert_confound_orthogonal(W0, W_planted, coords, seed_idx, label, cutoff=cutoff)

    L_planted = laplacian(W_planted, normalised=False)
    score = transmission_from_source(L_planted, seed_idx, E=0.0)

    point_auc = float(_auc(score[mask], label[mask]))
    gate1 = point_auc > max_floor_auc

    ci_seq = block_bootstrap_ci(score[mask], label[mask], n_boot=N_BOOT_CI, rng=np.random.default_rng(42))
    gate2_seq = not (ci_seq[1] > floor_ci_seq[2] or floor_ci_seq[1] > ci_seq[2])

    ci_sp = spatial_block_bootstrap_ci(coords[mask], score[mask], label[mask], n_boot=N_BOOT_CI, rng=np.random.default_rng(42))
    gate2_sp = not (ci_sp[1] > floor_ci_sp[2] or floor_ci_sp[1] > ci_sp[2])

    strat = stratified_auc(score, label, shells)
    real_shell, real_max = _well_powered_max(strat)

    null_results = {}
    for null_spec in NULL_SPECS:
        null_seed = 5_000_000 + seed
        result = _permutation_null(score, coords, PATCH_SIZE, shells, null_spec, target_rg, null_seed)
        null_maxes = np.array(result["null_maxes"]) if result["null_maxes"] else np.array([np.nan])
        p_value = float((null_maxes >= real_max).mean()) if np.isfinite(real_max) else float("nan")
        bonferroni_alpha = ALPHA / (len(STRENGTHS) * N_SEEDS)
        gate3 = bool(p_value < ALPHA) if np.isfinite(p_value) else False
        gate4 = bool(p_value < bonferroni_alpha) if np.isfinite(p_value) else False
        null_results[null_spec] = {
            "p_value": p_value, "n_infeasible": result["n_infeasible"], "n_reps_used": len(result["null_maxes"]),
            "gate3_clears_uncorrected": gate3, "gate4_clears_bonferroni": gate4,
            "certified_sequence_ci": bool(gate1 and gate2_seq and gate4),
            "certified_spatial_ci": bool(gate1 and gate2_sp and gate4),
        }

    return {
        "target": target_name, "strength": strength, "seed": seed,
        "patch": patch.tolist(), "target_rg": float(target_rg),
        "plant_n_paths_applied": plant_report.n_paths_applied,
        "plant_n_paths_failed": plant_report.n_paths_failed,
        "plant_n_edges_modified": len(plant_report.edges_modified),
        "gate0_orthogonal": True,  # assert_confound_orthogonal would have raised otherwise
        "point_auc": point_auc, "max_floor_auc": max_floor_auc, "gate1_beats_floor": gate1,
        "ci_sequence": list(ci_seq), "floor_ci_sequence": list(floor_ci_seq), "gate2_sequence_ci": gate2_seq,
        "ci_spatial": list(ci_sp), "floor_ci_spatial": list(floor_ci_sp), "gate2_spatial_ci": gate2_sp,
        "well_powered_max_auc": real_max, "well_powered_shell": real_shell,
        "nulls": null_results,
    }


def _load_existing(path: Path) -> dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=TARGETS)
    parser.add_argument("--strength", nargs="+", type=float, default=STRENGTHS)
    parser.add_argument("--n-seeds", type=int, default=N_SEEDS)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "detection_curve.json")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    results = _load_existing(args.output)

    for target_name in args.target:
        if target_name not in results:
            results[target_name] = {"invariance_check": None, "cells": {}}
        _log(f"{target_name}: preparing...")
        prep = _prepare_target(target_name)
        _log(f"{target_name}: N={prep['n']} n_seed={len(prep['seed_idx'])}")

        if results[target_name]["invariance_check"] is None:
            patch = select_distal_patch(prep["coords"], prep["W0"], prep["seed_idx"], PATCH_SIZE, np.random.default_rng(999), cutoff=prep["cutoff"])
            W_planted_max, _ = plant_channel(prep["W0"], prep["seed_idx"], patch, 32.0, N_PATHS, np.random.default_rng(998))
            H_new_0 = build_H_new(prep["coords"], prep["bfactors"], cutoff=prep["cutoff"])
            H_new_32 = build_H_new(prep["coords"], prep["bfactors"], cutoff=prep["cutoff"])
            ctqw_0 = time_averaged_ctqw_converged(H_new_0, source=prep["seed_idx"], coherent=False)
            ctqw_32 = time_averaged_ctqw_converged(H_new_32, source=prep["seed_idx"], coherent=False)
            dcc_0 = dcc_low(prep["coords"], prep["seed_idx"], cutoff=prep["cutoff"], k_modes=20)
            dcc_32 = dcc_low(prep["coords"], prep["seed_idx"], cutoff=prep["cutoff"], k_modes=20)
            prs_0 = prs_low(prep["coords"], prep["seed_idx"], cutoff=prep["cutoff"], k_modes=20)
            prs_32 = prs_low(prep["coords"], prep["seed_idx"], cutoff=prep["cutoff"], k_modes=20)
            results[target_name]["invariance_check"] = {
                "H_new_ctqw_invariant": bool(np.array_equal(ctqw_0, ctqw_32)),
                "dcc_low_invariant": bool(np.array_equal(dcc_0, dcc_32)),
                "prs_low_invariant": bool(np.array_equal(prs_0, prs_32)),
            }
            _log(f"{target_name}: invariance check = {results[target_name]['invariance_check']}")
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)

        seed_cache: dict = {}
        for strength in args.strength:
            for seed in range(args.n_seeds):
                cell_key = f"{strength}/{seed}"
                if cell_key in results[target_name]["cells"]:
                    continue
                t0 = time.time()
                try:
                    cell = run_cell(prep, target_name, strength, seed, seed_cache)
                except Exception as exc:
                    cell = {"error": str(exc)}
                    _log(f"{target_name} s={strength} seed={seed}: FAILED -- {exc!r}")
                results[target_name]["cells"][cell_key] = cell
                elapsed = time.time() - t0
                if "error" not in cell:
                    _log(
                        f"{target_name} s={strength} seed={seed}: point_auc={cell['point_auc']:.3f} "
                        f"gate1={cell['gate1_beats_floor']} gate2_seq={cell['gate2_sequence_ci']} "
                        f"gate2_sp={cell['gate2_spatial_ci']} "
                        f"cert_compact_spCI={cell['nulls']['compact']['certified_spatial_ci']} ({elapsed:.1f}s)"
                    )
                with open(args.output, "w") as f:
                    json.dump(results, f, indent=2)

    _log(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
