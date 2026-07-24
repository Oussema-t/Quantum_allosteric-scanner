#!/usr/bin/env python3
"""TASK-0149 -- real-target execution of the delivered low-mode predictors
(`lowmode_predictor.prs_low`/`dcc_low`) under this project's own current
conventions: full active-site array, incoherent mixture ([[TASK-0118]]/
`INV-0006`) -- NOT the delivered code's own scalar-seed default used for
its synthetic runs (the delivering thread flagged this exact divergence
risk explicitly, see this task's own Context).

The delivering thread's own synthetic prediction (read before writing
this script, not after): mode-filtering should remove the proximity
confound (rho(score,-hop) near 0) but NOT manufacture whole-graph
discrimination on its own (whole-graph AUC ~ chance) -- any real signal,
if present, should only be visible under [[TASK-0123]]'s distance-
stratified lens. This script reports whichever way real data actually
comes out, including "genuinely dead, with a mechanism" if that's what
it shows.

Reuses [[TASK-0123]]'s own machinery directly (`scripts/
distance_stratified_evaluation.py`'s `_prepare_target`/`_well_powered_max`
shape and permutation-null convention: fix the score once, relabel the
pocket via same-size random draws, rescore `stratified_auc` against the
frozen score -- cheap, no re-diagonalization per replicate) rather than
re-deriving a parallel evaluation pipeline, per this task's own
Constraint ("gate through TASK-0123's stratified AUC and its own
permutation null... reused directly, not re-derived").
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
from allostery.labels import build_labels  # noqa: E402
from allostery.lowmode_predictor import dcc_low, prs_low  # noqa: E402
from allostery.metrics import auc as _auc, stratified_auc  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo/DEFAULT_CUTOFF

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0149_lowmode_predictor"
TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
K_MODES_GRID = [5, 10, 15, 20]
MIN_POS_WELL_POWERED = 3  # matches TASK-0123's own `distance_stratified_evaluation.py`
N_PERM_REPS = 1000
PERM_SEED = 123


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _prepare_target(target_name: str) -> dict:
    """TASK-0123's own `_prepare_target`, reused directly (not re-derived) --
    full active-site array as `source` ([[TASK-0118]]'s GAUGE convention),
    hop-shell binning computed once and reused across every k_modes/
    observable cell, matching that task's own Constraint against per-cell
    re-binning."""
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
    floor_candidates = [
        degree_centrality(apo.coords, cutoff=cutoff),
        euclid_from_seed_centroid(apo.coords, source),
        hop_from_seed(apo.coords, source, cutoff=cutoff),
    ]
    floor = float(max(_auc(f, labels_obj.pocket.astype(int)) for f in floor_candidates))
    return {
        "coords": apo.coords, "source": source,
        "pocket": labels_obj.pocket.astype(int), "cutoff": cutoff, "shells": shells,
        "n_residues": len(apo.resnums), "floor": floor,
    }


def _well_powered_max(strat: dict, min_pos: int = MIN_POS_WELL_POWERED):
    """TASK-0123's own filter, reused directly: a "pass" driven by a
    single-positive shell is indistinguishable from luck at these shell
    sizes -- not read as a claim on its own."""
    candidates = {s: v for s, v in strat.items() if v["n_pos"] >= min_pos and np.isfinite(v["auc"])}
    if not candidates:
        return None, float("nan")
    best_shell = max(candidates, key=lambda s: candidates[s]["auc"])
    return best_shell, candidates[best_shell]["auc"]


def _permutation_null(score: np.ndarray, prep: dict, n_reps: int = N_PERM_REPS, seed: int = PERM_SEED) -> dict:
    """TASK-0123's own cheap permutation-null convention: `score` is fixed
    (prs_low/dcc_low do not depend on labels, so nothing needs
    re-diagonalizing per replicate); only the pocket labeling is
    reshuffled (same-size random draw) and `stratified_auc`/
    `_well_powered_max` re-run against the frozen score."""
    pocket_size = int(prep["pocket"].sum())
    n_residues = prep["n_residues"]
    shells = prep["shells"]

    real_shell, real_auc = _well_powered_max(stratified_auc(score, prep["pocket"], shells))
    rng = np.random.default_rng(seed)
    null_maxes = []
    for _ in range(n_reps):
        perm_idx = rng.choice(n_residues, size=pocket_size, replace=False)
        perm_pocket = np.zeros(n_residues, dtype=int)
        perm_pocket[perm_idx] = 1
        _, null_max = _well_powered_max(stratified_auc(score, perm_pocket, shells))
        if np.isfinite(null_max):
            null_maxes.append(null_max)
    null_maxes = np.array(null_maxes) if null_maxes else np.array([np.nan])
    percentile = float((null_maxes <= real_auc).mean()) if np.isfinite(real_auc) else float("nan")
    p_value = float((null_maxes >= real_auc).mean()) if np.isfinite(real_auc) else float("nan")
    return {
        "real_well_powered_max_auc": real_auc, "real_shell": real_shell,
        "null_median": float(np.median(null_maxes)), "null_sd": float(np.std(null_maxes)),
        "n_reps": len(null_maxes), "percentile": percentile, "p_value": p_value,
    }


def _score_cell(name: str, score: np.ndarray, prep: dict) -> dict:
    from scipy.stats import spearmanr

    whole_auc = _auc(score, prep["pocket"])
    strat = stratified_auc(score, prep["pocket"], prep["shells"])
    well_powered_shell, well_powered_auc = _well_powered_max(strat)
    # `prep["shells"]` is the real, non-negative hop distance (see
    # `_prepare_target`'s own comment: `-hop_from_seed(...)`, and
    # `hop_from_seed` itself returns NEGATIVE hop -- double negation).
    # The delivered synthetic control's own convention is rho(score,
    # -hop) (`lowmode_predictor_synthetic_control.py`/`test_lowmode_
    # predictor.py` both compute `spearmanr(score, -hop)` directly) --
    # matched here for a directly comparable number, not the raw-hop sign.
    rho, _ = spearmanr(score, -prep["shells"])
    null = _permutation_null(score, prep)
    return {
        "observable": name,
        "whole_graph_auc": whole_auc,
        "floor_cleared": bool(whole_auc > prep["floor"]) if np.isfinite(whole_auc) else False,
        "rho_score_neg_hop": float(rho),
        "n_scorable_shells": len(strat),
        "well_powered_shell": well_powered_shell,
        "well_powered_max_auc": well_powered_auc,
        "permutation_null": null,
    }


def run_target(target_name: str) -> dict:
    _log(f"{target_name}: preparing (fetch + clean + labels)...")
    prep = _prepare_target(target_name)
    _log(
        f"{target_name}: N={prep['n_residues']} n_seed={len(prep['source'])} "
        f"pocket_size={int(prep['pocket'].sum())} floor={prep['floor']:.4f}"
    )

    cells = []
    for k in K_MODES_GRID:
        t0 = time.time()
        prs = prs_low(prep["coords"], prep["source"], cutoff=prep["cutoff"], k_modes=k)
        dcc = dcc_low(prep["coords"], prep["source"], cutoff=prep["cutoff"], k_modes=k)
        elapsed = time.time() - t0

        row_prs = _score_cell("prs_low", prs, prep)
        row_dcc = _score_cell("dcc_low", dcc, prep)
        row_prs["k_modes"] = k
        row_dcc["k_modes"] = k
        cells.append(row_prs)
        cells.append(row_dcc)
        _log(
            f"{target_name} k={k}: prs_low whole_auc={row_prs['whole_graph_auc']:.3f} "
            f"rho={row_prs['rho_score_neg_hop']:.3f} well_powered_max={row_prs['well_powered_max_auc']:.3f} "
            f"(shell {row_prs['well_powered_shell']}, p={row_prs['permutation_null']['p_value']:.4f}) | "
            f"dcc_low whole_auc={row_dcc['whole_graph_auc']:.3f} rho={row_dcc['rho_score_neg_hop']:.3f} "
            f"well_powered_max={row_dcc['well_powered_max_auc']:.3f} "
            f"(shell {row_dcc['well_powered_shell']}, p={row_dcc['permutation_null']['p_value']:.4f}) "
            f"[{elapsed:.1f}s]"
        )

    return {
        "target": target_name, "n_residues": prep["n_residues"],
        "pocket_size": int(prep["pocket"].sum()), "floor": prep["floor"],
        "cells": cells,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=TARGETS)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "lowmode_predictor_real_run.json")
    args = parser.parse_args(argv)

    all_results = {}
    for name in args.target:
        try:
            all_results[name] = run_target(name)
        except Exception as exc:
            all_results[name] = {"error": str(exc)}
            _log(f"{name}: FAILED -- {exc!r}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(all_results, f, indent=2)
    _log(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
