#!/usr/bin/env python3
"""TASK-0123 -- distance-stratified evaluation of the existing operator
register (REVIEW-panel-2026-07-16-v2.md Sec.2.3/Sec.6's own falsification
test): "distance-matched-decoy AUC on all targets... stratified AUC ~= 0.5
in every shell -> observable dead, switch to co-participation/ENAQT."

Whole-graph AUC cannot distinguish "this operator found the pocket" from
"this operator found distance" -- occupation of a walk seeded at a point
is monotonically decreasing in distance from that point, for any
operator, at any time (the review's own measured table, ~0.83-0.97 on a
bare disorder-free Laplacian). `metrics.stratified_auc` (this task's own
new function) removes the distance axis from the comparison by scoring
each pocket residue only against non-pocket residues at the *same*
hop-shell from the seed.

Applies to every operator already in `analysis._operator_registry()` (16
operators) x both propagators (`ctqw` via TASK-0130's closed form --
the actual current procedure that produces every other headline number
in this repo, not the now-superseded finite-t_max convention;
`ground_state` at t_max=15, unaffected by TASK-0130) x all 3 mandatory
targets = 96 cells, plus [[TASK-0122]]'s `mode_coparticipation` as an
additional row per target (this task's own In Scope: "apply to whatever
new observable TASK-0122 produces, once available").

Hop-shell binning (`baselines.hop_from_seed`, single-hop-distance bins --
this task's own Open Question, Implementer's call, stated here per that
task's own instruction) is computed **once per target** and reused
identically across every operator/propagator/observable comparison in
that target's row (this task's own Constraint -- a per-operator binning
would reintroduce the exact unexamined-knob problem this review is
about).
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

from allostery.analysis import _operator_registry, mode_coparticipation  # noqa: E402
from allostery.baselines import hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as _auc, stratified_auc, stratified_auc_summary  # noqa: E402
from allostery.propagators import ground_state_relaxation, time_averaged_ctqw_converged  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo/DEFAULT_CUTOFF

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0123_distance_stratified"
TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
GSR_T_MAX = 15.0


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

    shells = -hop_from_seed(apo.coords, source, cutoff=cutoff)  # positive integer hop distance
    return {
        "coords": apo.coords, "bfactors": apo.bfactors, "source": source,
        "pocket": labels_obj.pocket.astype(int), "cutoff": cutoff, "shells": shells,
        "n_residues": len(apo.resnums),
    }


def _score_row(name: str, tier, occ: np.ndarray, prep: dict) -> dict:
    whole_auc = _auc(occ, prep["pocket"])
    strat = stratified_auc(occ, prep["pocket"], prep["shells"])
    summary = stratified_auc_summary(strat)
    return {
        "operator": name, "tier": tier,
        "whole_graph_auc": whole_auc,
        "n_scorable_shells": summary["n_scorable_shells"],
        "stratified_mean_auc": summary["mean_auc"],
        "stratified_max_auc": summary["max_auc"],
        "stratified_max_shell": summary["max_shell"],
        "per_shell": strat,
    }


MIN_POS_WELL_POWERED = 3  # a "pass" driven by a single positive residue
# (n_pos=1) is not distinguishable from luck at these shell sizes --
# checked directly on this task's own real results (mode_coparticipation
# hit stratified AUC=1.000 on CARDIAC_MYOSIN at n_pos=1, while its own
# *best-powered* shell, n_pos=7, scored 0.376, below chance) -- the raw
# per-shell max is not read as a claim on its own without this filter.


def _well_powered_max(strat: dict, min_pos: int = MIN_POS_WELL_POWERED):
    """Same idea as `metrics.stratified_auc_summary`, restricted to
    shells with at least `min_pos` positives -- the summary this task's
    own headline reads, not the raw (possibly single-positive-driven)
    max."""
    candidates = {s: v for s, v in strat.items() if v["n_pos"] >= min_pos and np.isfinite(v["auc"])}
    if not candidates:
        return None, float("nan")
    best_shell = max(candidates, key=lambda s: candidates[s]["auc"])
    return best_shell, candidates[best_shell]["auc"]


def run_permutation_null(target_name: str, prep: dict, n_reps: int = 1000, seed: int = 123) -> dict:
    """Cheap permutation null for the well-powered stratified-AUC finding
    -- addresses the real multiple-shells/multiple-operators concern this
    task's own headline raises (16 operators x 2 propagators x up to 4
    shells x 3 targets = many comparisons; a real fraction would clear
    0.65 by chance alone). Unlike TASK-0131's own ceiling-search null
    (which had to re-run a 60-trial search per replicate), this only
    needs to re-label and re-score an *already-computed, fixed*
    occupation vector -- no re-optimization, no re-diagonalization --
    so 1000 replicates per representative operator is cheap.

    Representative operators, not the full 16 x 2 register (a full
    multiple-comparisons-corrected null over every cell is a separate,
    much larger undertaking outside this task's own time budget; these
    three cover the two propagators plus TASK-0122's own observable, the
    cases this task's own headline actually cites): `H_new`/ctqw
    (closed form), `H_new`/ground_state, `mode_coparticipation`.
    """
    coords, bfactors, source, cutoff = prep["coords"], prep["bfactors"], prep["source"], prep["cutoff"]
    pocket_size = int(prep["pocket"].sum())
    n_residues = prep["n_residues"]
    shells = prep["shells"]

    H_new = build_H_new(coords, bfactors, cutoff=cutoff)
    occ_by_name = {
        "H_new_ctqw": time_averaged_ctqw_converged(H_new, source=source, coherent=False),
        "H_new_ground_state": ground_state_relaxation(H_new, GSR_T_MAX, source=source),
        "mode_coparticipation": mode_coparticipation(H_new, source=source, n_low=5),
    }

    rng = np.random.default_rng(seed)
    result = {}
    for name, occ in occ_by_name.items():
        real_shell, real_auc = _well_powered_max(stratified_auc(occ, prep["pocket"], shells))
        null_maxes = []
        for _ in range(n_reps):
            perm_idx = rng.choice(n_residues, size=pocket_size, replace=False)
            perm_pocket = np.zeros(n_residues, dtype=int)
            perm_pocket[perm_idx] = 1
            _, null_max = _well_powered_max(stratified_auc(occ, perm_pocket, shells))
            if np.isfinite(null_max):
                null_maxes.append(null_max)
        null_maxes = np.array(null_maxes) if null_maxes else np.array([np.nan])
        percentile = float((null_maxes <= real_auc).mean()) if np.isfinite(real_auc) else float("nan")
        p_value = float((null_maxes >= real_auc).mean()) if np.isfinite(real_auc) else float("nan")
        result[name] = {
            "real_well_powered_max_auc": real_auc, "real_shell": real_shell,
            "null_median": float(np.median(null_maxes)), "null_sd": float(np.std(null_maxes)),
            "null_max": float(np.max(null_maxes)), "n_reps": len(null_maxes),
            "percentile": percentile, "p_value": p_value,
        }
        _log(
            f"{target_name} permutation-null [{name}]: real={real_auc:.3f} (shell {real_shell}) "
            f"null_median={result[name]['null_median']:.3f} p={p_value:.4f} ({len(null_maxes)} reps)"
        )
    return result


def run_target(target_name: str) -> dict:
    _log(f"{target_name}: preparing (fetch + clean + labels)...")
    prep = _prepare_target(target_name)
    n_shells = len(np.unique(prep["shells"]))
    _log(
        f"{target_name}: N={prep['n_residues']} n_seed={len(prep['source'])} "
        f"pocket_size={int(prep['pocket'].sum())} n_hop_shells={n_shells}"
    )

    registry = _operator_registry()
    rows = {"ctqw": [], "ground_state": []}
    for op_name, (tier, build_fn) in registry.items():
        try:
            H = build_fn(prep["coords"], prep["bfactors"], prep["cutoff"])
        except Exception as exc:
            rows["ctqw"].append({"operator": op_name, "tier": tier, "error": f"H build failed: {exc!r}"})
            rows["ground_state"].append({"operator": op_name, "tier": tier, "error": f"H build failed: {exc!r}"})
            continue
        if H.shape[0] != prep["n_residues"]:
            err = f"H shape {H.shape} incompatible with {prep['n_residues']} residues"
            rows["ctqw"].append({"operator": op_name, "tier": tier, "error": err})
            rows["ground_state"].append({"operator": op_name, "tier": tier, "error": err})
            continue

        occ_ctqw = time_averaged_ctqw_converged(H, source=prep["source"], coherent=False)
        rows["ctqw"].append(_score_row(op_name, tier, occ_ctqw, prep))

        occ_gsr = ground_state_relaxation(H, GSR_T_MAX, source=prep["source"])
        rows["ground_state"].append(_score_row(op_name, tier, occ_gsr, prep))

    # TASK-0122's mode_coparticipation, per this task's own In Scope
    H_new = build_H_new(prep["coords"], prep["bfactors"], cutoff=prep["cutoff"])
    cp = mode_coparticipation(H_new, source=prep["source"], n_low=5)
    rows["mode_coparticipation"] = [_score_row("mode_coparticipation", "A", cp, prep)]

    for kind, kind_rows in rows.items():
        for r in kind_rows:
            if "error" in r:
                _log(f"{target_name} {kind} {r['operator']}: ERROR {r['error']}")
            else:
                _log(
                    f"{target_name} {kind} {r['operator']}: whole_auc={r['whole_graph_auc']:.3f} "
                    f"stratified_max={r['stratified_max_auc']:.3f} (shell {r['stratified_max_shell']}) "
                    f"stratified_mean={r['stratified_mean_auc']:.3f} n_shells={r['n_scorable_shells']}"
                )

    _log(f"{target_name}: running permutation null for representative operators...")
    permutation_null = run_permutation_null(target_name, prep)

    return {
        "target": target_name, "n_residues": prep["n_residues"],
        "pocket_size": int(prep["pocket"].sum()), "n_hop_shells": n_shells,
        "rows": rows,
        "permutation_null": permutation_null,
    }


def render_summary(all_results: dict) -> str:
    """**The permutation-null-corrected picture is the headline, not the
    naive per-cell max** -- a naive ">0.65 in some shell" count is itself
    biased by the same max-over-K winner's-curse effect TASK-0131 found
    for the ceiling search (checked directly here: the permutation
    null's own median sits at ~0.56-0.64, not ~0.5, precisely because
    `stratified_auc_summary` takes a max over several shells). The
    corrected question is whether the *real* well-powered max AUC is a
    surprising outlier against *that* null, not against a naive 0.5."""
    lines = ["# TASK-0123 -- distance-stratified evaluation summary", ""]

    lines.append("## Permutation-null-corrected picture (the actual headline)")
    lines.append("")
    lines.append("| Target | Representative | Real well-powered max AUC | Null median | p-value |")
    lines.append("|---|---|---|---|---|")
    any_significant = []
    for target_name, result in all_results.items():
        if "error" in result or "permutation_null" not in result:
            continue
        for name, stats in result["permutation_null"].items():
            lines.append(
                f"| {target_name} | {name} | {stats['real_well_powered_max_auc']:.3f} "
                f"(shell {stats['real_shell']}) | {stats['null_median']:.3f} | {stats['p_value']:.4f} |"
            )
            if stats["p_value"] < 0.05:
                any_significant.append((target_name, name, stats["p_value"]))
    lines.append("")
    n_tests = sum(len(r.get("permutation_null", {})) for r in all_results.values() if "error" not in r)
    bonferroni = 0.05 / n_tests if n_tests else float("nan")
    if any_significant:
        lines.append(f"**{len(any_significant)}/{n_tests} cells clear p<0.05 (uncorrected)**, "
                      f"none clear a Bonferroni-corrected threshold of {bonferroni:.4f} for {n_tests} tests:")
        for target_name, name, p in sorted(any_significant, key=lambda x: x[2]):
            lines.append(f"- {target_name} / {name}: p={p:.4f}")
        lines.append("")
        lines.append("Real, uncorrected suggestive signal -- candidates for targeted follow-up, "
                      "not confirmed findings.")
    else:
        lines.append(f"**0/{n_tests} cells clear p<0.05** against the permutation null.")

    lines.append("")
    lines.append("## Naive per-cell max (>0.65 in some shell) -- kept for the record, "
                  "NOT the corrected conclusion above")
    lines.append("")
    any_pass = []
    for target_name, result in all_results.items():
        if "error" in result:
            continue
        for kind, kind_rows in result["rows"].items():
            for r in kind_rows:
                if "error" in r or r["n_scorable_shells"] == 0:
                    continue
                if r["stratified_max_auc"] > 0.65:  # a real margin, not noise around 0.5
                    any_pass.append((target_name, kind, r["operator"], r["stratified_max_auc"], r["stratified_max_shell"]))
    if any_pass:
        for target_name, kind, op_name, max_auc, shell in sorted(any_pass, key=lambda x: -x[3]):
            lines.append(f"- {target_name} / {kind} / {op_name}: stratified AUC={max_auc:.3f} at shell {shell}")
    else:
        lines.append("No cell clears stratified AUC > 0.65 in any shell, on any target.")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=TARGETS)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "distance_stratified_evaluation.json")
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

    summary = render_summary(all_results)
    with open(args.output.parent / "summary.md", "w") as f:
        f.write(summary)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
