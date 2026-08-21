#!/usr/bin/env python3
"""TASK-0181 Phase A -- classical QUBO selection vs. greedy top-k, on real
targets, evaluated against the pre-registered gate
(`.ai/tasks/DONE/TASK-0181-*.md`, "Pre-Registered Gate" section, fixed
2026-08-02, before this script existed):

    If the classical QUBO does not beat greedy top-k on hit_at_1
    (>=1 shared residue with the incumbent pocket label), at the
    canonical weight point (1,1,1,1,1), k=5, on >= 2 of the 3
    mandatory targets, Phase A is reported closed.

`--gate-only` runs just the 3 mandatory targets at the canonical weight
point and prints the verdict. Without it, also sweeps the pre-registered
weight/k grid (16 weight combinations x k in {3,5,10,20}, "Weight/k Grid"
section of the same task file) across every target passed via `--target`.

Active-site residues are hard-excluded from the candidate pool for BOTH
greedy top-k and the QUBO selection (matches `report.assemble_hit_list`'s
existing `exclude_idx` convention, used everywhere else in this project's
hit-list output) -- an honest apples-to-apples comparison against the
established ranking baseline, not a strawman that leaves greedy top-k
picking the trivially-highest-occupation seed residues themselves. Term
(e) (`-e * |S intersect active_site|`) is therefore structurally always 0
here (no candidate is ever an active-site residue) -- documented, not a
silent no-op.
"""
from __future__ import annotations

import argparse
import itertools
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

from allostery.analysis import mode_coparticipation  # noqa: E402
from allostery.baselines import euclid_from_seed_centroid, fpocket_baseline  # noqa: E402
from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.hamiltonians import build_H_new, contact_matrix  # noqa: E402
from allostery.labels import build_labels, functional_indices, ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from allostery.report import jaccard_stability  # noqa: E402
from allostery.selection import evaluate_selection, greedy_topk_indices, qubo_objective, sa_solve  # noqa: E402
from allostery.sites import cluster_sites  # noqa: E402

MANDATORY_TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
GATE_WEIGHTS = (1.0, 1.0, 1.0, 1.0, 1.0)
GATE_K = 5
CLUSTER_CUTOFF = 8.0  # TASK-0067's retained clustering/adjacency scale, reused for term (b)
DEFAULT_CUTOFF = 10.0
DEFAULT_POCKET_CUTOFF = 4.5

# Pre-registered grid, "Weight/k Grid" section, TASK-0181 task file.
WEIGHT_LEVELS = (0.0, 1.0)
K_VALUES = (3, 5, 10, 20)


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def build_target_selection_inputs(target_name: str) -> dict:
    """Assemble every array `selection.py` needs for one target -- apo-only
    (label used for scoring only, per this task's own Constraint). Mirrors
    `scripts/run_challenge.py::run_target`'s own recipe (same functions,
    same conventions) rather than inventing a second pipeline."""
    import prody

    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))

    apo = clean_from_config(target_name, role="apo")
    holo = clean_from_config(target_name, role="holo")
    prody.confProDy(verbosity="none")
    holo_id = target_config["holo_pdb"]
    chains = target_config.get("chains") or sorted(set(holo.chain_ids))
    chain_sel = " or ".join(f"chain {c}" for c in chains)
    holo_struct = prody.parsePDB(holo_id, compressed=False).select(chain_sel)
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)
    holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
        holo_struct, chains, holo.resnums
    )

    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None:
        raise RuntimeError(f"{target_name}: build_labels returned pocket=None, cannot score")

    active_site_idx = np.where(labels_obj.active_site)[0]
    source = np.sort(active_site_idx)

    H = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
    w, v = np.linalg.eigh(H)
    occ = time_averaged_ctqw_converged(source=source, coherent=False, w=w, v=v)
    coupling = mode_coparticipation(H, source, n_low=5)
    proximity = euclid_from_seed_centroid(apo.coords, source)
    A = contact_matrix(apo.coords, cutoff=CLUSTER_CUTOFF, weight="binary")

    candidates = np.array([i for i in range(len(apo.resnums)) if i not in set(source.tolist())])
    return {
        "target_name": target_name,
        "apo_pdb": target_config.get("apo_pdb"),
        "holo_pdb": target_config.get("holo_pdb"),
        "coords": apo.coords,
        "resnums": apo.resnums,
        "candidates": candidates,
        "score": occ[candidates],
        "A": A[np.ix_(candidates, candidates)],
        "proximity": proximity[candidates],
        "coupling": coupling[candidates],
        "active_site_mask": np.zeros(len(candidates), dtype=bool),  # excluded by construction
        "pocket_mask_local": labels_obj.pocket[candidates],
        "pocket_mask_full": labels_obj.pocket,
        "coords_local": apo.coords[candidates],
        "occ_full": occ,
        "H": H,
    }


def solve_and_score(inputs: dict, weights, k: int, *, rng, n_iter: int = 2000, n_restarts: int = 1) -> dict:
    """`n_restarts > 1` runs `sa_solve` from `n_restarts` different seeded
    starting points (greedy init, plus random inits) and keeps the
    single best-by-objective-value `S` across all of them -- a single SA
    trajectory is a noisy sample of the objective's argmax, not a
    reliable stand-in for "what the QUBO recommends"; the gate check
    (`run_gate_check`) uses multiple restarts precisely because a single
    run flipped hit/miss on KRAS_G12C between two otherwise-identical
    calls that differed only in `n_iter` (checked interactively before
    landing this parameter, not assumed) -- the argmax-by-objective
    answer across several restarts is far more stable."""
    N = len(inputs["candidates"])
    k_eff = min(k, N)

    def objective_fn(S):
        return qubo_objective(
            S, score=inputs["score"], A=inputs["A"], proximity=inputs["proximity"],
            active_site_mask=inputs["active_site_mask"], coupling=inputs["coupling"], weights=weights,
        )

    greedy_local = greedy_topk_indices(inputs["score"], k_eff)

    best_S, best_value = None, -np.inf
    for restart in range(n_restarts):
        init = greedy_local if restart == 0 else None
        S, value = sa_solve(N, k_eff, objective_fn, rng=rng, n_iter=n_iter, init=init)
        if value > best_value:
            best_S, best_value = S, value
    S_local, value = best_S, best_value

    qubo_hit = evaluate_selection(S_local, inputs["coords_local"], inputs["pocket_mask_local"])
    greedy_hit = evaluate_selection(greedy_local, inputs["coords_local"], inputs["pocket_mask_local"])

    return {
        "weights": weights, "k": k_eff,
        "qubo_indices_local": S_local.tolist(), "qubo_value": value,
        "qubo_hit_at_1": qubo_hit["n_hit_at_1"] > 0, "qubo_hit_at_3": qubo_hit["n_hit_at_3"] > 0,
        "greedy_indices_local": greedy_local.tolist(),
        "greedy_hit_at_1": greedy_hit["n_hit_at_1"] > 0, "greedy_hit_at_3": greedy_hit["n_hit_at_3"] > 0,
    }


def run_gate_check(rng_seed: int = 0) -> dict:
    per_target = {}
    for name in MANDATORY_TARGETS:
        _log(f"{name}: assembling selection inputs (fetch + clean + eigendecompose)...")
        t0 = time.monotonic()
        inputs = build_target_selection_inputs(name)
        _log(f"{name}: inputs ready in {time.monotonic() - t0:.1f}s (N={len(inputs['coords'])}, "
             f"{len(inputs['candidates'])} candidates after active-site exclusion)")
        result = solve_and_score(
            inputs, GATE_WEIGHTS, GATE_K, rng=np.random.default_rng(rng_seed),
            n_iter=3000, n_restarts=8,
        )
        per_target[name] = result
        _log(f"{name}: QUBO hit_at_1={result['qubo_hit_at_1']}, greedy hit_at_1={result['greedy_hit_at_1']}")

    n_qubo_wins = sum(
        1 for r in per_target.values() if r["qubo_hit_at_1"] and not r["greedy_hit_at_1"]
    )
    n_qubo_beats_or_ties = sum(
        1 for r in per_target.values()
        if r["qubo_hit_at_1"] >= r["greedy_hit_at_1"]  # QUBO hits whenever greedy does, or more
    )
    # Gate's own wording: "does not beat greedy top-k" -- beating means
    # QUBO hits and greedy does not (a strict win), on >= 2/3 targets.
    verdict = "OPEN" if n_qubo_wins >= 2 else "CLOSED"

    return {
        "verdict": verdict,
        "canonical_weights": GATE_WEIGHTS,
        "k": GATE_K,
        "n_qubo_strict_wins": n_qubo_wins,
        "n_targets": len(MANDATORY_TARGETS),
        "per_target": per_target,
    }


def run_full_grid(target_names, rng_seed: int = 0) -> dict:
    grid_results = {}
    for name in target_names:
        _log(f"{name}: assembling selection inputs for full grid...")
        try:
            inputs = build_target_selection_inputs(name)
        except Exception as exc:
            # A target-level failure (e.g. MYC_MAX's holo_pdb: null, per
            # TASK-0080's no-ground-truth branch -- this script's
            # selection objective needs a pocket label to score against,
            # unlike run_challenge.py's separate no-ground-truth path)
            # must not abort the whole 14-target run -- logged and
            # skipped, mirrors run_challenge.py::run_target's own
            # per-target error-handling convention.
            _log(f"{name}: FAILED to build inputs ({exc!r}) -- skipping")
            grid_results[name] = {"error": repr(exc)}
            continue

        target_grid = []
        rng = np.random.default_rng(rng_seed)
        for b, c, d, e in itertools.product(WEIGHT_LEVELS, repeat=4):
            weights = (1.0, b, c, d, e)
            for k in K_VALUES:
                result = solve_and_score(inputs, weights, k, rng=rng, n_iter=1500)
                target_grid.append(result)
        # Stability: does the k=5 QUBO selection's member set change
        # identity across the 16 weight combinations? Mirrors sites.py's
        # site_knob_sweep STABLE/UNSTABLE convention.
        k5_sets = [set(r["qubo_indices_local"]) for r in target_grid if r["k"] == 5]
        stability = jaccard_stability([sorted(s) for s in k5_sets])
        verdict = "STABLE" if stability["min"] >= 0.5 else "UNSTABLE"

        fpocket_bar = None
        try:
            import prody

            prody.confProDy(verbosity="none")
            target_config = load_target_config(name)
            pdb_path = prody.fetchPDB(target_config["apo_pdb"], compressed=False)
            fpocket_bar = fpocket_baseline(pdb_path) if pdb_path else {"error": "no local path"}
        except Exception as exc:
            fpocket_bar = {"error": repr(exc)}

        grid_results[name] = {
            "apo_pdb": inputs["apo_pdb"], "holo_pdb": inputs["holo_pdb"],
            "n_combos": len(target_grid), "knob_verdict": verdict,
            "jaccard_min": stability["min"], "jaccard_mean": stability["mean"],
            "grid": target_grid, "fpocket": fpocket_bar,
        }
        _log(f"{name}: grid done, {len(target_grid)} solves, knob_verdict={verdict}")
    return grid_results


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--gate-only", action="store_true")
    parser.add_argument("--target", nargs="+", default=None, help="targets for the full grid (default: config/targets.yaml's full 12)")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent.parent / "results/tasks/0181_selection")
    args = parser.parse_args(argv)

    args.output.mkdir(parents=True, exist_ok=True)
    gate = run_gate_check()
    with open(args.output / "gate.json", "w") as f:
        json.dump(gate, f, indent=2, default=str)
    _log(f"GATE VERDICT: {gate['verdict']} ({gate['n_qubo_strict_wins']}/{gate['n_targets']} strict QUBO wins)")

    if args.gate_only:
        return 0

    if gate["verdict"] == "CLOSED":
        _log("Gate CLOSED -- per this task's own Constraint, stopping here. "
             "Not extending to the full 12-target grid.")
        return 0

    # config/targets.yaml's full 14 real targets -- LDH is deliberately
    # under `omitted_targets` (TASK-0003, "borderline allostery... apo-PDB
    # inconsistency"), not a usable target, excluded here on that basis,
    # not by oversight.
    targets = args.target or [
        "KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "MYC_MAX", "PTP1B", "GLUCOKINASE",
        "ATCase", "CASPASE1", "CASPASE7", "HEMOGLOBIN", "TAR_RECEPTOR",
        "GLYCOGEN_PHOSPHORYLASE", "PFK", "GROEL_SUBUNIT",
    ]
    grid = run_full_grid(targets)
    with open(args.output / "full_grid.json", "w") as f:
        json.dump(grid, f, indent=2, default=str)
    _log(f"Full grid written to {args.output / 'full_grid.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
