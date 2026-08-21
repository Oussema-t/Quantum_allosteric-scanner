#!/usr/bin/env python3
"""TASK-0156 -- primary scoring: control-effort observable vs. the
proximity floor AND the classical PRS baseline (Atilgan & Atilgan 2009),
on the 3 mandatory targets, distance-stratified AUC as the primary lens
(TASK-0123), whole-graph AUC as a secondary readout, block-bootstrap CIs
(TASK-0112) and a label-permutation null (this project's own standing
"any max-of-something or otherwise-surprising number needs a null before
being reported" convention).

Run only after the pre-registered kill-switch (`control_effort_kill_
switch.py`) returned PROCEED -- confirmed 2026-08-03/04, rho=0.56 on
KRAS_G12C, well under the 0.85 STOP threshold.

Long-running (CARDIAC_MYOSIN's N=704 full-residue scan is the expensive
part, ~15-20 min) -- instrumented with `runlog.RunLogger`
(`.ai/reference/LONG_JOB_CONVENTION.md`), run detached.
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
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.control_effort import control_effort_score, scan_control_effort  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.lowmode_predictor import prs_low  # noqa: E402
from allostery.metrics import auc, block_bootstrap_ci, stratified_auc, stratified_auc_summary  # noqa: E402
from allostery.runlog import RunLogger  # noqa: E402

from hop_distance_generalization_audit import _load_apo_holo, DEFAULT_POCKET_CUTOFF  # noqa: E402

HOP_CUTOFF = 8.0
MANDATORY_TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]

# T is NOT a derived physical quantity -- it is a per-target value found
# by a label-blind empirical search (Implementer's call): pick T so the
# feasible FRACTION on an evenly-spaced subsample lands in a comparable
# range across targets (~15-20%), never looking at which residues are
# labelled pocket. A size-blind fixed T (originally T=15 for every
# target, chosen only from KRAS_G12C) left BCR_ABL1/CARDIAC_MYOSIN's
# feasible fraction near zero (1/451, 1/704) -- almost every residue
# collapsed to the same "infeasible" sentinel score, mechanically forcing
# stratified AUC to exactly 0.5 in every shell by ties, a scoring-
# artifact degenerate case, not a physical finding (see the task file's
# own Done section for how this was caught).
#
# **Checked and rejected**: this project's own established gap-based
# horizon prescription (`propagators.min_adequate_t_max`, built exactly
# to stop a single hardcoded time constant like `t_max=15` being applied
# "regardless of its energy scale" -- RESULTS.md rows 36/39/`REVIEW-
# panel-2026-07-16-v2.md` P0#2) does NOT fix this bug: KRAS_G12C and
# BCR_ABL1's H_new spectral gaps are nearly identical (0.0364 vs 0.0374),
# so a `T ~ 1/gap` rule predicts nearly the SAME T for both --
# reproducing BCR_ABL1's degenerate feasibility (2/91 on a subsample,
# checked directly) instead of fixing it. Feasibility here is evidently
# governed by something beyond H_0's spectral gap alone (plausibly the
# seed/control-channel coverage fraction, n_seed/N, which differs far
# more across these targets -- 10.7%/5.8%/2.6%). The empirical linear-
# in-N values used below (`T=15*(N/169)`) were arrived at the same way
# (subsample feasibility search) and happen to roughly track that
# pattern, but are reported here as an empirical calibration, not as a
# derived law -- restores a comparable feasible fraction on KRAS_G12C/
# BCR_ABL1 (~16-18%); CARDIAC_MYOSIN stays lower (~6%) even after
# scaling, reported as a real limitation, not hidden. F lowered from the
# original 0.5 to 0.4 (still above the dumbbell gate's own validated
# F=0.3) for the same reason, uniformly across all 3 targets.
T_BASE = 15.0
N_BASE = 169
N_SLICES = 20
FIDELITY_TARGET = 0.4
PENALTY_WEIGHT = 5000.0
N_ITERS = 500
LR = 0.05

N_PERMUTATIONS = 1000
N_BOOT = 1000


def _score_target(name: str, log: RunLogger) -> dict:
    t0 = time.monotonic()
    target_config = load_target_config(name)
    apo, holo = _load_apo_holo(name, target_config)
    cutoff = float(target_config.get("enm_cutoff", 10.0))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)

    if labels_obj.pocket is None or not labels_obj.pocket.any():
        log.step(f"{name}_skip", reason="no resolvable pocket label")
        return {"target": name, "ok": False, "reason": "no resolvable pocket label"}

    source = np.where(labels_obj.active_site)[0]
    pocket = labels_obj.pocket.astype(int)
    n = len(apo.resnums)
    log.step(f"{name}_loaded", n_residues=n, n_active_site=len(source), n_pocket=int(pocket.sum()))

    H0 = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)

    T = T_BASE * n / N_BASE
    result = scan_control_effort(
        H0, source, T=T, n_slices=N_SLICES, fidelity_target=FIDELITY_TARGET,
        penalty_weight=PENALTY_WEIGHT, n_iters=N_ITERS, lr=LR, chunk_size=200,
    )
    ce_score = control_effort_score(result)
    log.step(f"{name}_control_effort_done", n_feasible=int(result.feasible.sum()),
              elapsed_s=round(time.monotonic() - t0, 1))

    prs_score = prs_low(apo.coords, source, cutoff=cutoff, k_modes=20)
    log.step(f"{name}_prs_done")

    floor_candidates = {
        "degree": degree_centrality(apo.coords, cutoff=cutoff),
        "euclid": euclid_from_seed_centroid(apo.coords, source),
        "hop": hop_from_seed(apo.coords, source, cutoff=cutoff),
    }
    floor_whole_auc = {k: auc(v, pocket) for k, v in floor_candidates.items()}
    floor_max_whole_auc = max(v for v in floor_whole_auc.values() if np.isfinite(v))

    shells = -hop_from_seed(apo.coords, source, cutoff=HOP_CUTOFF)  # positive hop-count shells

    def _score_block(scores, tag):
        whole_auc = auc(scores, pocket)
        strat = stratified_auc(scores, pocket, shells)
        strat_summary = stratified_auc_summary(strat)
        auc_point, lo, hi = block_bootstrap_ci(scores, pocket, n_boot=N_BOOT)
        log.step(f"{name}_{tag}_scored", whole_auc=whole_auc, **strat_summary)
        return {
            "whole_graph_auc": whole_auc,
            "whole_graph_auc_ci": [lo, hi],
            "stratified": strat,
            "stratified_summary": strat_summary,
        }

    control_effort_block = _score_block(ce_score, "control_effort")
    prs_block = _score_block(prs_score, "prs_low")

    # Permutation null on the PRIMARY (stratified) readout: reshuffle the
    # pocket label N_PERMUTATIONS times (control_effort scores/shells are
    # fixed -- the expensive scan runs once, only the label permutes) and
    # recompute stratified_auc_summary's mean_auc each time.
    rng = np.random.default_rng(0)
    null_mean_stratified = np.empty(N_PERMUTATIONS)
    for i in range(N_PERMUTATIONS):
        perm_labels = rng.permutation(pocket)
        strat_perm = stratified_auc(ce_score, perm_labels, shells)
        null_mean_stratified[i] = stratified_auc_summary(strat_perm)["mean_auc"]
    observed_mean = control_effort_block["stratified_summary"]["mean_auc"]
    valid_null = null_mean_stratified[np.isfinite(null_mean_stratified)]
    if np.isfinite(observed_mean) and len(valid_null) > 0:
        perm_p = float((np.sum(valid_null >= observed_mean) + 1) / (len(valid_null) + 1))
    else:
        perm_p = float("nan")
    log.step(f"{name}_permutation_null_done", observed_mean_stratified=observed_mean,
              null_mean=float(np.nanmean(null_mean_stratified)), perm_p=perm_p)

    return {
        "target": name,
        "ok": True,
        "label": "incumbent",
        "n_residues": int(n),
        "n_active_site": int(len(source)),
        "n_pocket": int(pocket.sum()),
        "hyperparameters": {
            "T": T, "n_slices": N_SLICES, "fidelity_target": FIDELITY_TARGET,
            "penalty_weight": PENALTY_WEIGHT, "n_iters": N_ITERS, "lr": LR,
        },
        "n_feasible": int(result.feasible.sum()),
        "proximity_floor_whole_graph_auc": floor_whole_auc,
        "proximity_floor_max_whole_graph_auc": floor_max_whole_auc,
        "control_effort": control_effort_block,
        "prs_low_classical_baseline": prs_block,
        "permutation_null": {
            "n_permutations": N_PERMUTATIONS,
            "observed_mean_stratified_auc": observed_mean,
            "null_mean": float(np.nanmean(null_mean_stratified)),
            "null_std": float(np.nanstd(null_mean_stratified)),
            "p_value": perm_p,
        },
        "elapsed_s": round(time.monotonic() - t0, 1),
    }


def main() -> int:
    out_dir = Path(__file__).resolve().parent.parent / "results/tasks/0156_control_effort"
    out_dir.mkdir(exist_ok=True)
    log = RunLogger(out_dir / "run.jsonl", run_name="control_effort_scoring")

    out = []
    for name in MANDATORY_TARGETS:
        print(f"{name}: running...", file=sys.stderr)
        try:
            r = _score_target(name, log)
        except Exception as exc:  # noqa: BLE001 -- diagnostic script, report and continue
            r = {"target": name, "ok": False, "reason": f"{type(exc).__name__}: {exc}"}
            log.step(f"{name}_failed", reason=str(exc))
        print(f"{name}: ok={r.get('ok')} elapsed={r.get('elapsed_s')}", file=sys.stderr)
        out.append(r)

    out_path = out_dir / "scoring_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nWrote {out_path}")

    print("\n=== summary ===")
    for r in out:
        if not r.get("ok"):
            print(f"{r['target']:16s} FAILED: {r.get('reason')}")
            continue
        ce = r["control_effort"]["stratified_summary"]
        prs = r["prs_low_classical_baseline"]["stratified_summary"]
        floor = r["proximity_floor_max_whole_graph_auc"]
        pval = r["permutation_null"]["p_value"]
        print(
            f"{r['target']:16s} floor_whole={floor:.3f}  "
            f"ce_strat_mean={ce['mean_auc']:.3f} ce_strat_max={ce['max_auc']:.3f} (n_shells={ce['n_scorable_shells']})  "
            f"prs_strat_mean={prs['mean_auc']:.3f}  perm_p={pval:.4f}"
        )

    log.finish(n_targets=len(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
