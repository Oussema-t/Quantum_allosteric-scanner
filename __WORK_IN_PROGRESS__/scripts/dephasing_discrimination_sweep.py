#!/usr/bin/env python3
"""TASK-0141 -- Engineered-dephasing (ENAQT) sweep on real targets: does
*any* Haken-Strobl dephasing rate gamma improve pocket **discrimination**
(AUC vs the proximity floor), not transport efficiency (HYP-P11).

The four ENAQT references (Mohseni/Rebentrost/Lloyd/Aspuru-Guzik 2008,
Rebentrost 2009, Caruso 2014, Viciani 2015) establish an optimal
dephasing rate for *transport efficiency to a known trap*. This
project's objective is *discrimination* of an *unknown* pocket -- a
different quantity. This script's own physics prior (this batch's
`enaqt_sanity.py`, not present in this repo -- see the task file's own
"Flagged" note): dephasing de-traps the walker from Anderson
localization by pushing it toward classical diffusion, which *is* the
proximity confound. Predicted verdict: NEGATIVE on all 3 targets. Run
regardless -- a rigorous, literature-anchored negative is the
deliverable either way. Does NOT score transport efficiency and does NOT
tune gamma against pocket labels (the grid below is fixed up front).

Two real, load-bearing gaps in the existing machinery found and closed
while implementing this task (see `src/allostery/propagators.py`):
1. `haken_strobl` had no incoherent-mixture source option -- every
   multi-residue seed used a coherent equal-amplitude superposition,
   which this project's own established GAUGE (TASK-0118/INV-0006) says
   is wrong for a real multi-residue active site (no biophysical basis
   for a specific relative quantum phase between its residues). Added a
   `coherent` kwarg mirroring `ctqw`'s own split; this script always
   passes `coherent=False`.
2. No time-averaged Haken-Strobl occupation existed (`haken_strobl`
   itself only returns one endpoint snapshot) -- this task's own Intent
   Contract scores "time-averaged site occupation", not a snapshot. New
   `haken_strobl_time_averaged` (one `solve_ivp` call with `t_eval`, not
   `n_snapshots` independent re-solves).

Runtime (TASK-0105's own measured precedent, single-endpoint `haken_strobl`
at t=25): KRAS_G12C (N=169) ~11s/gamma, BCR_ABL1 (N=451) ~161s/gamma.
Time-averaging via `t_eval` adds negligible cost on top of a single solve
(interpolation, not re-solving) -- see that function's own docstring.
PTP1B (N=298) has no prior direct measurement; extrapolating N^3 scaling
from the KRAS_G12C point gives ~48s/gamma.
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

from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.diagnostics import classify_failure  # noqa: E402
from allostery.hamiltonians import build_H_new, contact_matrix, laplacian  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as auc_fn, ipr, stratified_auc, stratified_auc_summary  # noqa: E402
from allostery.propagators import haken_strobl_time_averaged, time_averaged_ctqw  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo/DEFAULT_CUTOFF, not re-derived

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0141_dephasing"
TARGETS = ["KRAS_G12C", "BCR_ABL1", "PTP1B"]

# Fixed up front, per this task's own Constraint ("gamma is never tuned
# against pocket labels") -- the task's own suggested grid, in units of
# H's own spectral bandwidth (this repo's established "bandwidth"
# convention, `w.max()-w.min()`, e.g. `propagators.py`'s
# `min_adequate_n_steps`/`degenerate_tol` and
# `scripts/optuna_parameter_scan.py`'s `practical_t_max_max`).
GAMMA_MULTIPLIERS = np.array([0.0, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0])

T_MAX = 25.0  # TASK-0105's own established "long enough to reach each gamma's long-time regime" anchor
N_SNAPSHOTS = 50
# TASK-0105's own feasibility-tuned tolerances (its module docstring:
# default rtol=1e-6/atol=1e-8 is accurate but too slow at protein scale).
ODE_RTOL = 1e-4
ODE_ATOL = 1e-6

MIN_POS_WELL_POWERED = 3  # TASK-0123's own established floor: a single-positive shell is not distinguishable from luck
N_PERM = 1000
N_TARGETS_FOR_BONFERRONI = len(TARGETS)
ALPHA = 0.05


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _well_powered_max(strat: dict, min_pos: int = MIN_POS_WELL_POWERED):
    """TASK-0123's own established filter, reused identically: restrict
    the 'best shell' read to shells with >= min_pos positives."""
    candidates = {s: v for s, v in strat.items() if v["n_pos"] >= min_pos and np.isfinite(v["auc"])}
    if not candidates:
        return None, float("nan")
    best_shell = max(candidates, key=lambda s: candidates[s]["auc"])
    return best_shell, candidates[best_shell]["auc"]


def _permutation_null_for_pocket(occ: np.ndarray, pocket: np.ndarray, n_residues: int, pocket_size: int,
                                  n_reps: int = N_PERM, seed: int = 123) -> dict:
    """Cheap permutation null (TASK-0131/TASK-0123 precedent) for a single
    already-computed occupation vector's whole-graph AUC -- re-labels a
    fixed occ vector, no re-solving of the ODE. Used on the best-scoring
    interior gamma per target: reading 'the best of 8 fixed gamma points'
    off a real-labeled curve is itself a max-of-K selection and gets the
    same winner's-curse scrutiny this project's other max-of-K results
    have needed (TASK-0131 ceiling search, TASK-0138 H14 ceiling,
    TASK-0123 stratified-shell AUC)."""
    rng = np.random.default_rng(seed)
    real_auc = float(auc_fn(occ, pocket))
    null_aucs = np.empty(n_reps)
    for i in range(n_reps):
        perm_idx = rng.choice(n_residues, size=pocket_size, replace=False)
        perm_pocket = np.zeros(n_residues, dtype=int)
        perm_pocket[perm_idx] = 1
        null_aucs[i] = auc_fn(occ, perm_pocket)
    percentile = float((null_aucs <= real_auc).mean())
    p_value = float((null_aucs >= real_auc).mean())
    return {
        "real_auc": real_auc, "null_median": float(np.median(null_aucs)),
        "null_p95": float(np.percentile(null_aucs, 95)), "percentile": percentile,
        "p_value": p_value, "n_reps": n_reps,
    }


def _prepare_target(target_name: str) -> dict:
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

    H = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
    w = np.linalg.eigvalsh(H)
    bandwidth = float(w[-1] - w[0])

    floor_scores = [
        degree_centrality(apo.coords, cutoff=cutoff),
        euclid_from_seed_centroid(apo.coords, source),
        hop_from_seed(apo.coords, source, cutoff=cutoff),
    ]
    A = contact_matrix(apo.coords, cutoff=cutoff, weight="binary")
    H_for_diagnosis = laplacian(A, normalised=False)
    shells = -hop_from_seed(apo.coords, source, cutoff=cutoff)

    return {
        "target": target_name, "H": H, "bandwidth": bandwidth,
        "bfactors": apo.bfactors, "source": source,
        "pocket": labels_obj.pocket.astype(int), "n_residues": len(apo.resnums),
        "cutoff": cutoff, "floor_scores": floor_scores, "H_for_diagnosis": H_for_diagnosis,
        "shells": shells,
        "proximity_score": floor_scores[1],  # euclid_from_seed_centroid = -dist; corr(occ, this) == rho(occ, -dist)
    }


def run_gamma_sweep(prep: dict) -> list:
    H, bandwidth, source = prep["H"], prep["bandwidth"], prep["source"]
    pocket, n_residues = prep["pocket"], prep["n_residues"]
    rows = []
    for mult in GAMMA_MULTIPLIERS:
        gamma = float(mult) * bandwidth
        t0 = time.monotonic()
        if mult == 0.0:
            occ = time_averaged_ctqw(H, T_MAX, source=source, n_steps=N_SNAPSHOTS, coherent=False)
        else:
            occ = haken_strobl_time_averaged(
                H, T_MAX, gamma, source=source, n_snapshots=N_SNAPSHOTS,
                coherent=False, rtol=ODE_RTOL, atol=ODE_ATOL,
            )
        elapsed = time.monotonic() - t0

        auc = float(auc_fn(occ, pocket))
        diag = classify_failure(
            occ, pocket, H=prep["H_for_diagnosis"], bfactors=prep["bfactors"],
            floor_scores=prep["floor_scores"], return_ci=True,
        )
        strat = stratified_auc(occ, pocket, prep["shells"])
        strat_summary = stratified_auc_summary(strat)
        best_shell, best_shell_auc = _well_powered_max(strat)

        participation_ratio = float(ipr(occ))
        proximity_corr = float(np.corrcoef(occ, prep["proximity_score"])[0, 1])

        rows.append({
            "gamma_multiplier": float(mult), "gamma": gamma,
            "auc": auc, "category": diag.category,
            "score_ci": diag.score_ci, "floor_ci": diag.floor_ci, "ci_overlap": diag.ci_overlap,
            "stratified_mean_auc": strat_summary["mean_auc"],
            "stratified_well_powered_max_auc": best_shell_auc, "stratified_well_powered_shell": best_shell,
            "participation_ratio": participation_ratio, "proximity_correlation": proximity_corr,
            "elapsed_s": round(elapsed, 2),
            "_occ": occ,  # stripped before JSON serialization, kept for the verdict pass below
        })
        _log(
            f"{prep['target']}: gamma_mult={mult:.3g} gamma={gamma:.4g} AUC={auc:.4f} "
            f"cat={diag.category} PR={participation_ratio:.4f} rho(occ,-dist)={proximity_corr:.3f} "
            f"({elapsed:.1f}s)"
        )
    return rows


def evaluate_target(prep: dict, rows: list) -> dict:
    gamma0 = rows[0]
    interior = rows[1:]

    # Classical-limit sanity gate (mandatory regardless of verdict): the
    # largest gamma's occupation must show a materially stronger
    # proximity-distance correlation than the coherent walk -- the
    # setup-validity check this task's own Constraints require before
    # trusting any interior point.
    classical_row = rows[-1]
    sanity_pass = bool(classical_row["proximity_correlation"] > gamma0["proximity_correlation"] + 0.1)

    # Best-of-8 (fixed grid, but "which one is best" is read off real
    # labels) -- gets the same permutation-null scrutiny this project's
    # other max-of-K findings have needed.
    best_idx = int(np.argmax([r["auc"] for r in interior]))
    best_row = interior[best_idx]
    null = _permutation_null_for_pocket(
        best_row["_occ"], prep["pocket"], prep["n_residues"], int(prep["pocket"].sum()),
    )

    ci_clears = bool(
        best_row["ci_overlap"] is False
        and best_row["score_ci"] is not None and best_row["floor_ci"] is not None
        and best_row["score_ci"][0] > best_row["floor_ci"][0]
    )
    beats_coherent = bool(best_row["auc"] > gamma0["auc"])
    bonferroni_significant = bool(null["p_value"] < ALPHA / N_TARGETS_FOR_BONFERRONI)

    positive = bool(ci_clears and beats_coherent and bonferroni_significant)

    return {
        "target": prep["target"],
        "gamma0_auc": gamma0["auc"],
        "best_interior_gamma_multiplier": best_row["gamma_multiplier"],
        "best_interior_auc": best_row["auc"],
        "best_interior_category": best_row["category"],
        "ci_clears_floor_non_overlapping": ci_clears,
        "beats_coherent_walk": beats_coherent,
        "permutation_null": {k: v for k, v in null.items()},
        "bonferroni_alpha": ALPHA / N_TARGETS_FOR_BONFERRONI,
        "bonferroni_significant": bonferroni_significant,
        "classical_limit_sanity_pass": sanity_pass,
        "classical_limit_proximity_corr": classical_row["proximity_correlation"],
        "gamma0_proximity_corr": gamma0["proximity_correlation"],
        "verdict": "POSITIVE" if positive else "NEGATIVE",
    }


def _strip_occ(rows: list) -> list:
    return [{k: v for k, v in r.items() if k != "_occ"} for r in rows]


def main() -> int:
    results = {}
    for target_name in TARGETS:
        try:
            _log(f"{target_name}: preparing (labels, H_new, bandwidth)...")
            prep = _prepare_target(target_name)
            _log(f"{target_name}: N={prep['n_residues']} pocket_size={int(prep['pocket'].sum())} "
                 f"bandwidth={prep['bandwidth']:.4g}")
            rows = run_gamma_sweep(prep)
            verdict = evaluate_target(prep, rows)
            _log(f"{target_name}: verdict={verdict['verdict']} "
                 f"(best gamma_mult={verdict['best_interior_gamma_multiplier']}, "
                 f"AUC={verdict['best_interior_auc']:.4f}, p={verdict['permutation_null']['p_value']:.4f})")
            results[target_name] = {
                "N": prep["n_residues"], "pocket_size": int(prep["pocket"].sum()),
                "bandwidth": prep["bandwidth"], "cutoff": prep["cutoff"],
                "sweep": _strip_occ(rows), "verdict": verdict,
            }
        except Exception as exc:
            _log(f"{target_name}: FAILED -- {exc!r}")
            results[target_name] = {"target": target_name, "error": str(exc)}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "dephasing_discrimination_sweep.json", "w") as f:
        json.dump(results, f, indent=2)
    _log(f"wrote {OUTPUT_DIR / 'dephasing_discrimination_sweep.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
