#!/usr/bin/env python3
"""TASK-0140 -- chiral (broken-time-reversal) circulation observable
(HYP-P9), gated real-data run.

Evaluates `allostery.chiral.chiral_circulation_score` on `H_new`'s own
apo graph, seeded at the full active-site array (incoherent mixture,
TASK-0118/INV-0006's convention), on all 3 mandatory + 4 ASD
generalization targets (TASK-0081/TASK-0127's own 7-target register,
`openness_premise_test.py`'s own list) -- the same rigor every other
operator in this program is held to: `diagnostics.classify_failure`
against the proximity floor (TASK-0094), block-bootstrap CIs
(TASK-0112), distance-stratified AUC + permutation null (TASK-0123),
Bonferroni across targets.

**Soft-gated by TASK-0143** (0/7 PASS on the graph-openness premise,
physics.md's own 2026-07-22 status line: "TASK-0140 should treat this
observable as gated on an unsupported premise, not proceed as if the
premise were open"). A FAIL here is the expected, pre-registered-consistent
outcome, not a surprise to explain away -- run anyway, per this task's own
Dependency section ("interpret a FAIL here in light of a FAIL there").

Synthetic GATE 1 (coupling vs well dissociation, loop-dumbbell) and
GATE 2 (beats floor on a distal loop pocket) both pass as regression
tests (`tests/test_chiral.py`) before this real run is trusted -- ported
independently, since the cited reference script (`chiral_observable.py`)
is confirmed not to exist anywhere in this repo (this task's own Context).
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
from scipy.stats import spearmanr

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.chiral import chiral_circulation_score  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.diagnostics import NO_FAILURE_DETECTED, classify_failure  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.metrics import block_bootstrap_ci, stratified_auc, stratified_auc_summary  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo/DEFAULT_CUTOFF

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0140_chiral"
MANDATORY_TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
ASD_TARGETS = ["PTP1B", "GLUCOKINASE", "CASPASE1", "CASPASE7"]
TARGETS = MANDATORY_TARGETS + ASD_TARGETS

FIELD_SCALE = 0.05  # this task's own Implementer's-call default, fixed
# blind to labels (Constraints); sensitivity swept separately below.
FIELD_SCALE_SWEEP = [0.02, 0.05, 0.1, 0.2]
MIN_POS_WELL_POWERED = 3  # TASK-0123's own convention, reused as-is.
N_PERMUTATION_REPS = 1000
PERMUTATION_SEED = 123  # TASK-0123's own fixed seed, reused for the same reason.


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
    source = np.sort(np.where(labels_obj.active_site)[0])
    if len(source) == 0:
        raise RuntimeError(f"{target_name}: empty active-site seed")

    shells = -hop_from_seed(apo.coords, source, cutoff=cutoff)
    return {
        "coords": apo.coords, "bfactors": apo.bfactors, "source": source,
        "pocket": labels_obj.pocket.astype(int), "cutoff": cutoff, "shells": shells,
        "n_residues": len(apo.resnums),
    }


def _well_powered_max(strat: dict, min_pos: int = MIN_POS_WELL_POWERED):
    candidates = {s: v for s, v in strat.items() if v["n_pos"] >= min_pos and np.isfinite(v["auc"])}
    if not candidates:
        return None, float("nan")
    best_shell = max(candidates, key=lambda s: candidates[s]["auc"])
    return best_shell, candidates[best_shell]["auc"]


def _run_permutation_null(score: np.ndarray, prep: dict, n_reps: int = N_PERMUTATION_REPS, seed: int = PERMUTATION_SEED) -> dict:
    """Cheap: re-labels and re-scores an already-computed score vector --
    no re-diagonalization per replicate (TASK-0123's own precedent)."""
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


def run_target(target_name: str) -> dict:
    _log(f"{target_name}: preparing (fetch + clean + labels)...")
    prep = _prepare_target(target_name)
    source, coords, cutoff = prep["source"], prep["coords"], prep["cutoff"]
    _log(f"{target_name}: N={prep['n_residues']} n_seed={len(source)} pocket_size={int(prep['pocket'].sum())}")

    H_new = build_H_new(coords, prep["bfactors"], cutoff=cutoff)

    circ = chiral_circulation_score(coords, source=source, cutoff=cutoff, field_scale=FIELD_SCALE, H_real=H_new)
    occ = time_averaged_ctqw_converged(H_new, source=source, coherent=False)

    mask = np.ones(prep["n_residues"], dtype=bool)
    mask[source] = False
    labels = prep["pocket"]

    floor_scores = np.stack([
        euclid_from_seed_centroid(coords, source)[mask],
        hop_from_seed(coords, source, cutoff=cutoff)[mask],
        degree_centrality(coords, cutoff=cutoff)[mask],
    ])

    circ_auc = _auc(circ[mask], labels[mask])
    occ_auc = _auc(occ[mask], labels[mask])
    floor_aucs = [_auc(c, labels[mask]) for c in floor_scores]
    max_floor_auc = float(np.nanmax(floor_aucs))

    circ_category = classify_failure(circ[mask], labels[mask], floor_scores=floor_scores)
    occ_category = classify_failure(occ[mask], labels[mask], floor_scores=floor_scores)

    circ_ci = block_bootstrap_ci(circ[mask], labels[mask])
    _, winning_floor = max(zip(floor_aucs, floor_scores), key=lambda ac: ac[0] if np.isfinite(ac[0]) else -1)
    floor_ci = block_bootstrap_ci(winning_floor, labels[mask])
    ci_overlap = not (circ_ci[1] > floor_ci[2] or floor_ci[1] > circ_ci[2])

    dist = -euclid_from_seed_centroid(coords, source)
    rho_circ_dist = float(spearmanr(circ[mask], dist[mask]).correlation)
    rho_occ_dist = float(spearmanr(occ[mask], dist[mask]).correlation)

    strat = stratified_auc(circ, labels, prep["shells"])
    strat_summary = stratified_auc_summary(strat)
    perm_null = _run_permutation_null(circ, prep)

    field_scale_sensitivity = {}
    for fs in FIELD_SCALE_SWEEP:
        s = chiral_circulation_score(coords, source=source, cutoff=cutoff, field_scale=fs, H_real=H_new)
        field_scale_sensitivity[fs] = _auc(s[mask], labels[mask])

    result = {
        "target": target_name,
        "n_residues": prep["n_residues"],
        "pocket_size": int(prep["pocket"].sum()),
        "circ_auc": circ_auc, "occ_auc": occ_auc,
        "floor_aucs": {"euclid": floor_aucs[0], "hop": floor_aucs[1], "degree": floor_aucs[2]},
        "max_floor_auc": max_floor_auc,
        "circ_category": circ_category, "occ_category": occ_category,
        "circ_ci": circ_ci, "floor_ci": floor_ci, "ci_overlap": ci_overlap,
        "rho_circ_dist": rho_circ_dist, "rho_occ_dist": rho_occ_dist,
        "stratified_max_auc": strat_summary["max_auc"], "stratified_max_shell": strat_summary["max_shell"],
        "stratified_n_scorable_shells": strat_summary["n_scorable_shells"],
        "permutation_null": perm_null,
        "field_scale_sensitivity": field_scale_sensitivity,
    }
    _log(
        f"{target_name}: circ_auc={circ_auc:.3f} ({circ_category}) occ_auc={occ_auc:.3f} ({occ_category}) "
        f"max_floor={max_floor_auc:.3f} ci_overlap={ci_overlap} "
        f"rho(circ,dist)={rho_circ_dist:.3f} rho(occ,dist)={rho_occ_dist:.3f} "
        f"perm_p={perm_null['p_value']:.4f}"
    )
    return result


def _load_existing(output_path: Path) -> dict:
    if output_path.exists():
        with open(output_path) as f:
            return json.load(f)
    return {}


def render_summary(all_results: dict) -> str:
    n_tests = sum(1 for r in all_results.values() if "error" not in r)
    bonferroni = 0.05 / n_tests if n_tests else float("nan")

    lines = ["# TASK-0140 -- chiral circulation observable, real-data run summary", ""]
    lines.append(f"Bonferroni-corrected threshold: 0.05 / {n_tests} = {bonferroni:.5f}")
    lines.append("")
    lines.append("| Target | circ AUC | occ AUC | max floor AUC | circ category | CI overlap | "
                  "rho(circ,-dist) | rho(occ,-dist) | perm p-value |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    passes = []
    for name in TARGETS:
        r = all_results.get(name)
        if r is None or "error" in r:
            lines.append(f"| {name} | ERROR | | | | | | | |")
            continue
        lines.append(
            f"| {name} | {r['circ_auc']:.3f} | {r['occ_auc']:.3f} | {r['max_floor_auc']:.3f} | "
            f"{r['circ_category']} | {r['ci_overlap']} | {r['rho_circ_dist']:.3f} | "
            f"{r['rho_occ_dist']:.3f} | {r['permutation_null']['p_value']:.4f} |"
        )
        cleared = (
            r["circ_category"] == NO_FAILURE_DETECTED
            and not r["ci_overlap"]
            and r["permutation_null"]["p_value"] < bonferroni
        )
        if cleared:
            passes.append(name)

    lines.append("")
    mandatory_pass = [t for t in passes if t in MANDATORY_TARGETS]
    asd_pass = [t for t in passes if t in ASD_TARGETS]
    if mandatory_pass and asd_pass:
        lines.append(
            f"**PASS**: {', '.join(mandatory_pass)} (mandatory) clear the floor with non-overlapping CIs "
            f"and Bonferroni-significant permutation null; confirmed on the ASD generalization set "
            f"({', '.join(asd_pass)})."
        )
    elif mandatory_pass:
        lines.append(
            f"**INSUFFICIENT**: {', '.join(mandatory_pass)} (mandatory) clears the floor with non-overlapping "
            f"CIs and Bonferroni-significant permutation null, but no ASD generalization target confirms it -- "
            f"per this task's own pre-registered bar ('generalization-set confirmation'), not a PASS."
        )
    else:
        lines.append(
            f"**FAIL**: no target clears the floor with non-overlapping CIs and Bonferroni-significant "
            f"permutation null ({len(passes)}/{n_tests} candidate cells before the CI+null requirement)."
        )
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=TARGETS)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "chiral_circulation_real_run.json")
    args = parser.parse_args(argv)

    all_results = _load_existing(args.output)
    for name in args.target:
        if name in all_results and "error" not in all_results[name]:
            _log(f"{name}: already computed, skipping")
            continue
        try:
            all_results[name] = run_target(name)
        except Exception as exc:
            all_results[name] = {"error": str(exc)}
            _log(f"{name}: FAILED -- {exc!r}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(all_results, f, indent=2)
        _log(f"checkpointed {args.output}")

    summary = render_summary(all_results)
    with open(args.output.parent / "summary.md", "w") as f:
        f.write(summary)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
