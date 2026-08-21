#!/usr/bin/env python3
"""TASK-0158 -- re-run every affected null under the corrected spatially
compact draw (`allostery.nulls.compact_patch`/`compact_patch_from_pool`),
side by side with the original scattered-draw number, additively (the
scattered numbers already reported elsewhere are not deleted or
overwritten -- this script's own output is a new, separate artifact).

Three families, each reusing its own already-established scoring
machinery unmodified -- only the null-draw step changes:

1. **Lowmode** (`prs_low`/`dcc_low`, TASK-0149 + TASK-0151's own
   generalization-set targets): `stratified_auc` + well-powered-shell-max
   + permutation null, `null_audit.py`'s own exact target case.
2. **Persistent H2** (`void_score`, TASK-0142): plain random-patch null
   on the ungated score's pocket-mean statistic.
3. **Learnability patch control** (`restricted_cumulative_overlap`,
   TASK-0133/TASK-0139/TASK-0152): plain random-patch null on CO(20).

Each null draw is swapped for the SAME statistic's own already-computed
score/curve -- cheap (no re-diagonalization, no re-running ANM/ripser
per replicate) except where the underlying quantity itself must be
recomputed per candidate patch (learnability's `restricted_cumulative_
overlap`, which TASK-0133's own original script already recomputes per
replicate too -- unavoidable, not a new cost this task introduces).
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

from allostery.baselines import hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.lowmode_predictor import dcc_low, prs_low  # noqa: E402
from allostery.metrics import stratified_auc  # noqa: E402
from allostery.nulls import compact_patch, compact_patch_from_pool  # noqa: E402
from allostery.persistent_voids import void_score  # noqa: E402
from allostery.superpose import (  # noqa: E402
    align_apo_holo,
    anm_modes,
    chain_map_from_config,
    restricted_cumulative_overlap,
)

import run_challenge  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0158_compact_null"

LOWMODE_TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "PTP1B", "CASPASE7"]
K_MODES_GRID = [5, 10, 15, 20]
MIN_POS_WELL_POWERED = 3
N_PERM_REPS = 1000
PERM_SEED = 123

H2_TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
H2_N_NULL_REPS = 1000
H2_NULL_SEED = 133

LEARN_TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "GLUCOKINASE"]
LEARN_N_REPLICATES = 1000
LEARN_SEED = 7
LEARN_ANM_CUTOFF = 10.0
LEARN_N_MODES = 20
LEARN_POCKET_CUTOFF = 4.5


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# 1. Lowmode (TASK-0149 / TASK-0151)
# ---------------------------------------------------------------------------

def _lowmode_prepare_target(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))
    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")
    source = np.sort(np.where(labels_obj.active_site)[0])
    if len(source) == 0:
        raise RuntimeError(f"{target_name}: empty active-site seed")
    shells = -hop_from_seed(apo.coords, source, cutoff=cutoff)
    return {
        "coords": apo.coords, "source": source,
        "pocket": labels_obj.pocket.astype(int), "cutoff": cutoff, "shells": shells,
        "n_residues": len(apo.resnums),
    }


def _well_powered_max(strat: dict, min_pos: int = MIN_POS_WELL_POWERED):
    cand = {s: v for s, v in strat.items() if v["n_pos"] >= min_pos and np.isfinite(v["auc"])}
    if not cand:
        return None, float("nan")
    best_shell = max(cand, key=lambda s: cand[s]["auc"])
    return best_shell, cand[best_shell]["auc"]


def _lowmode_null(score: np.ndarray, prep: dict, *, compact: bool, n_reps: int = N_PERM_REPS,
                   seed: int = PERM_SEED) -> dict:
    pocket_size = int(prep["pocket"].sum())
    n_residues = prep["n_residues"]
    shells = prep["shells"]
    coords = prep["coords"]

    real_shell, real_auc = _well_powered_max(stratified_auc(score, prep["pocket"], shells))
    rng = np.random.default_rng(seed)
    null_maxes = []
    for _ in range(n_reps):
        if compact:
            idx = compact_patch(coords, pocket_size, rng)
        else:
            idx = rng.choice(n_residues, size=pocket_size, replace=False)
        lab = np.zeros(n_residues, dtype=int)
        lab[idx] = 1
        _, null_max = _well_powered_max(stratified_auc(score, lab, shells))
        if np.isfinite(null_max):
            null_maxes.append(null_max)
    null_maxes = np.array(null_maxes) if null_maxes else np.array([np.nan])
    percentile = float((null_maxes <= real_auc).mean()) if np.isfinite(real_auc) else float("nan")
    p_value = float((null_maxes >= real_auc).mean()) if np.isfinite(real_auc) else float("nan")
    return {
        "real_well_powered_max_auc": real_auc, "real_shell": real_shell,
        "null_median": float(np.median(null_maxes)), "n_reps": len(null_maxes),
        "percentile": percentile, "p_value": p_value,
    }


def run_lowmode_target(target_name: str) -> dict:
    prep = _lowmode_prepare_target(target_name)
    _log(f"[lowmode] {target_name}: N={prep['n_residues']} n_seed={len(prep['source'])} "
         f"pocket_size={int(prep['pocket'].sum())}")
    cells = []
    for k in K_MODES_GRID:
        for name, fn in (("prs_low", prs_low), ("dcc_low", dcc_low)):
            score = fn(prep["coords"], prep["source"], cutoff=prep["cutoff"], k_modes=k)
            scattered = _lowmode_null(score, prep, compact=False)
            compact = _lowmode_null(score, prep, compact=True)
            cells.append({"observable": name, "k_modes": k, "scattered": scattered, "compact": compact})
            _log(
                f"[lowmode] {target_name} {name} k={k}: "
                f"scattered p={scattered['p_value']:.4f} (max={scattered['real_well_powered_max_auc']:.3f}) | "
                f"compact p={compact['p_value']:.4f} (max={compact['real_well_powered_max_auc']:.3f})"
            )
    return {"target": target_name, "n_residues": prep["n_residues"],
            "pocket_size": int(prep["pocket"].sum()), "cells": cells}


# ---------------------------------------------------------------------------
# 2. Persistent H2 (TASK-0142)
# ---------------------------------------------------------------------------

def _h2_prepare_target(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))
    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")
    source = np.sort(np.where(labels_obj.active_site)[0])
    if len(source) == 0:
        raise RuntimeError(f"{target_name}: empty active-site seed")
    return {"coords": apo.coords, "source": source, "pocket": labels_obj.pocket.astype(int),
            "cutoff": cutoff, "n_residues": len(apo.resnums)}


def run_h2_target(target_name: str) -> dict:
    from allostery.persistent_voids import persistence_h2

    prep = _h2_prepare_target(target_name)
    coords, source = prep["coords"], prep["source"]
    n = prep["n_residues"]
    labels = prep["pocket"]
    mask = np.ones(n, dtype=bool)
    mask[source] = False
    pool = np.where(mask)[0]
    pocket_idx = np.where(labels == 1)[0]

    THRESH = 16.0
    score_ungated = void_score(coords, thresh=THRESH, min_persistence=0.0, top_k=1)
    real_mean = float(score_ungated[pocket_idx].mean())

    def _null(compact: bool, seed: int) -> dict:
        rng = np.random.default_rng(seed)
        null_means = np.empty(H2_N_NULL_REPS)
        for i in range(H2_N_NULL_REPS):
            if compact:
                patch = compact_patch_from_pool(coords, pool, len(pocket_idx), rng)
            else:
                patch = rng.choice(pool, size=len(pocket_idx), replace=False)
            null_means[i] = score_ungated[patch].mean()
        percentile = float((null_means < real_mean).mean() * 100.0)
        p_value = float((null_means >= real_mean).mean())
        return {"null_mean": float(null_means.mean()), "null_sd": float(null_means.std()),
                "percentile": percentile, "p_value": p_value, "n_reps": H2_N_NULL_REPS}

    scattered = _null(compact=False, seed=H2_NULL_SEED)
    compact = _null(compact=True, seed=H2_NULL_SEED + 1)
    _log(f"[H2] {target_name}: real_mean={real_mean:.4f} scattered p={scattered['p_value']:.4f} "
         f"compact p={compact['p_value']:.4f}")
    return {"target": target_name, "real_mean_score": real_mean,
            "scattered": scattered, "compact": compact}


# ---------------------------------------------------------------------------
# 3. Learnability patch control (TASK-0133 / TASK-0139 / TASK-0152)
# ---------------------------------------------------------------------------

def run_learnability_target(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", LEARN_POCKET_CUTOFF))
    anm_cutoff = float(target_config.get("enm_cutoff", LEARN_ANM_CUTOFF))

    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")

    alignment = align_apo_holo(apo, holo, chain_map=chain_map_from_config(target_config))
    eigvals, eigvecs = anm_modes(apo.coords, cutoff=anm_cutoff, n_modes=LEARN_N_MODES)

    in_common = np.zeros(len(labels_obj.pocket), dtype=bool)
    in_common[alignment.apo_idx] = True
    measurable_pocket = np.where(labels_obj.pocket & in_common)[0]
    if len(measurable_pocket) == 0:
        raise RuntimeError(f"{target_name}: no measurable pocket residues in the common set")

    pocket_co_curve = restricted_cumulative_overlap(apo, alignment, eigvecs, measurable_pocket)
    pocket_co20 = float(pocket_co_curve[-1])
    patch_size = len(measurable_pocket)

    def _null(compact: bool, seed: int) -> dict:
        rng = np.random.default_rng(seed)
        patch_co20 = np.empty(LEARN_N_REPLICATES)
        for i in range(LEARN_N_REPLICATES):
            if compact:
                patch = compact_patch_from_pool(apo.coords, alignment.apo_idx, patch_size, rng)
            else:
                patch = rng.choice(alignment.apo_idx, size=patch_size, replace=False)
            co_curve = restricted_cumulative_overlap(apo, alignment, eigvecs, patch)
            patch_co20[i] = co_curve[-1]
        percentile = float((patch_co20 < pocket_co20).mean() * 100.0)
        p_value = float((patch_co20 >= pocket_co20).mean())
        return {"patch_co20_mean": float(patch_co20.mean()), "patch_co20_std": float(patch_co20.std()),
                "percentile": percentile, "p_value": p_value, "n_reps": LEARN_N_REPLICATES}

    scattered = _null(compact=False, seed=LEARN_SEED)
    compact = _null(compact=True, seed=LEARN_SEED + 1)
    _log(f"[learnability] {target_name}: pocket_co20={pocket_co20:.4f} "
         f"scattered percentile={scattered['percentile']:.1f} p={scattered['p_value']:.4f} | "
         f"compact percentile={compact['percentile']:.1f} p={compact['p_value']:.4f}")
    return {"target": target_name, "pocket_co20_restricted": pocket_co20,
            "patch_size": patch_size, "scattered": scattered, "compact": compact}


# ---------------------------------------------------------------------------

def _load_existing(path: Path) -> dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"lowmode": {}, "h2": {}, "learnability": {}}


def main() -> int:
    out_path = OUTPUT_DIR / "compact_null_rerun.json"
    results = _load_existing(out_path)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for target in LOWMODE_TARGETS:
        if target in results["lowmode"] and "error" not in results["lowmode"][target]:
            _log(f"[lowmode] {target}: already computed, skipping")
            continue
        try:
            results["lowmode"][target] = run_lowmode_target(target)
        except Exception as exc:
            results["lowmode"][target] = {"target": target, "error": str(exc)}
            _log(f"[lowmode] {target}: FAILED -- {exc!r}")
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)

    for target in H2_TARGETS:
        if target in results["h2"] and "error" not in results["h2"][target]:
            _log(f"[H2] {target}: already computed, skipping")
            continue
        try:
            results["h2"][target] = run_h2_target(target)
        except Exception as exc:
            results["h2"][target] = {"target": target, "error": str(exc)}
            _log(f"[H2] {target}: FAILED -- {exc!r}")
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)

    for target in LEARN_TARGETS:
        if target in results["learnability"] and "error" not in results["learnability"][target]:
            _log(f"[learnability] {target}: already computed, skipping")
            continue
        try:
            results["learnability"][target] = run_learnability_target(target)
        except Exception as exc:
            results["learnability"][target] = {"target": target, "error": str(exc)}
            _log(f"[learnability] {target}: FAILED -- {exc!r}")
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)

    _log(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
