#!/usr/bin/env python3
"""TASK-0136 -- path-ensemble + percolation connectivity between the
active site and the known allosteric pocket, on the apo contact graph.

Three parts, per this task's own Intent Contract:
  (a) weighted shortest-path + sub-optimal-path ensemble between the
      active-site residue set and the real pocket residue set -- a
      mechanism-characterization diagnostic (real labels, both endpoints
      known), not a blind predictor.
  (b) edge connectivity (Menger's theorem) + percolation threshold between
      the same two sets -- the bottleneck-vs-distributed question.
  (c) `baselines.connectivity_robustness`, generalized from (b)(i) to a
      full blind, AUC-scoreable "seed to every residue" baseline, scored
      against TASK-0094's proximity floor (same floor-candidate formula
      every other observable in this register uses).

All 3 mandatory targets. Purely topological (no propagator, no `t_max`,
no seed coherence, no clock) -- deliberately outside the current P0
gauge-fixing batch's confound axes, per this task's own Priority note.
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

from allostery.baselines import (  # noqa: E402
    connectivity_robustness,
    degree_centrality,
    euclid_from_seed_centroid,
    hop_from_seed,
)
from allostery.clean import load_target_config  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.metrics import stratified_auc, stratified_auc_summary  # noqa: E402
from allostery.percolation import (  # noqa: E402
    percolation_threshold,
    set_edge_connectivity,
    shortest_path_ensemble,
)

import run_challenge  # noqa: E402

TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
PATH_TOL = 0.10  # this task's own Open Question -- Implementer's call, stated here
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0136_percolation"


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _prepare_target(target_name: str):
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))

    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")
    active_idx = np.where(labels_obj.active_site)[0]
    pocket_idx = np.where(labels_obj.pocket)[0]
    if len(active_idx) == 0:
        raise RuntimeError(f"{target_name}: no resolvable active-site seed")

    return apo, labels_obj, active_idx, pocket_idx, cutoff


def run_target(target_name: str) -> dict:
    apo, labels_obj, active_idx, pocket_idx, cutoff = _prepare_target(target_name)
    n = len(apo.resnums)
    _log(f"{target_name}: N={n}, n_active={len(active_idx)}, n_pocket={len(pocket_idx)}, cutoff={cutoff}")

    result = {"target": target_name, "n_residues": n, "n_active": len(active_idx),
              "n_pocket": len(pocket_idx), "cutoff": cutoff}

    # -- Part (a): weighted shortest-path + sub-optimal-path ensemble
    t0 = time.monotonic()
    path_result = shortest_path_ensemble(apo.coords, active_idx, pocket_idx, cutoff=cutoff, tol=PATH_TOL)
    _log(f"{target_name}: (a) shortest path length={path_result['shortest_length']:.3f}, "
         f"n_ensemble={path_result['n_ensemble']} (tol={PATH_TOL}, capped={path_result['ensemble_capped']}) "
         f"({time.monotonic()-t0:.2f}s)")
    result["path_ensemble"] = path_result

    # -- Part (b)(i): edge connectivity (Menger's theorem) + the literal bottleneck
    t0 = time.monotonic()
    conn_result = set_edge_connectivity(apo.coords, active_idx, pocket_idx, cutoff=cutoff)
    _log(f"{target_name}: (b-i) edge_connectivity={conn_result['edge_connectivity']}, "
         f"cut_edges={conn_result['cut_edges']} ({time.monotonic()-t0:.2f}s)")
    result["edge_connectivity"] = conn_result

    # -- Part (b)(ii): percolation threshold
    t0 = time.monotonic()
    perc_result = percolation_threshold(apo.coords, active_idx, pocket_idx, cutoff=cutoff)
    _log(f"{target_name}: (b-ii) merge_distance={perc_result['merge_distance']:.2f}A "
         f"merge_edge={perc_result['merge_edge']} n_edges_added={perc_result['n_edges_added']} "
         f"({time.monotonic()-t0:.2f}s)")
    result["percolation_threshold"] = perc_result

    # -- Part (c): connectivity_robustness as a blind, scoreable baseline
    t0 = time.monotonic()
    cr_score = connectivity_robustness(apo.coords, active_idx, cutoff=cutoff)
    pocket_int = labels_obj.pocket.astype(int)
    cr_auc = float(_auc(cr_score, pocket_int))

    floor_candidates = {
        "degree_centrality": degree_centrality(apo.coords, cutoff=cutoff),
        "euclid_from_seed_centroid": euclid_from_seed_centroid(apo.coords, active_idx),
        "hop_from_seed": hop_from_seed(apo.coords, active_idx, cutoff=cutoff),
    }
    floor_aucs = {name: float(_auc(f, pocket_int)) for name, f in floor_candidates.items()}
    floor = max(floor_aucs.values())

    # TASK-0123 cross-read, per this task's own Constraint ("percolation/
    # connectivity measures are also plausibly degree-dominated and should
    # not be assumed exempt from that confound just because they aren't
    # propagator-based") -- actually run `stratified_auc`, not just cite
    # TASK-0123's own separate finding by analogy. Shells = integer hop
    # distance from the active site (`-hop_from_seed`, that baseline's own
    # negation convention), same construction TASK-0123 itself used.
    shells = -hop_from_seed(apo.coords, active_idx, cutoff=cutoff)
    strat = stratified_auc(cr_score, pocket_int, shells)
    strat_summary = stratified_auc_summary(strat)

    _log(f"{target_name}: (c) connectivity_robustness AUC={cr_auc:.4f}, floor={floor:.4f} "
         f"(floor_aucs={floor_aucs}) ({time.monotonic()-t0:.2f}s) | "
         f"stratified: n_shells={strat_summary['n_scorable_shells']} "
         f"mean_auc={strat_summary['mean_auc']:.3f} max_auc={strat_summary['max_auc']:.3f}")
    result["connectivity_robustness"] = {
        "auc": cr_auc, "floor": floor, "floor_aucs": floor_aucs,
        "beats_floor": cr_auc > floor,
        "stratified_summary": strat_summary,
    }

    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=TARGETS)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "percolation_connectivity.json")
    args = parser.parse_args(argv)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    all_results = {}
    if args.output.exists():
        with open(args.output) as f:
            all_results = json.load(f)
        _log(f"loaded {len(all_results)} existing entries from {args.output} -- merging, not overwriting")

    for name in args.target:
        try:
            all_results[name] = run_target(name)
        except Exception as exc:
            all_results[name] = {"error": str(exc)}
            _log(f"{name}: FAILED -- {exc!r}")

        with open(args.output, "w") as f:
            json.dump(all_results, f, indent=2)
        _log(f"{name}: wrote checkpoint to {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
