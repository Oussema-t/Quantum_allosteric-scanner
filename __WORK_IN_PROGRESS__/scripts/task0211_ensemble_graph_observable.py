#!/usr/bin/env python3
"""TASK-0211 -- is an observable computed across an ENSEMBLE of realized
contact graphs (not one static graph) independent of the ~3 axes
[[TASK-0199]] measured, or does it land inside the existing span?

Definition, split-half bar, and the "new axis" rule are all pre-registered
in `.ai/tasks/IN_PROGRESS/TASK-0211-*.md`'s own "In Progress" section,
written before this script existed -- see that file for the reasoning.

Reuses, does not re-derive:
  - `observable_effective_rank.py`'s own `_prepare_target`/
    `compute_all_observables`/`align_and_stack`/`correlation_matrix_and_rank`/
    `run_controls` ([[TASK-0199]]) -- the unmodified 28-observable pipeline.
  - `shortcuts.equipartition_ensemble`/`msf_cross_check` ([[TASK-0187]]) --
    the already-validated, legal (no-trajectory) ensemble sampler + gate.
  - `hamiltonians.contact_matrix` for the per-sample binary contact graph.

Consumes zero multiplicity budget: observable-vs-observable only, no label
is ever read (matches [[TASK-0199]]'s own discipline, restated per this
task's own Out of Scope).
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

from observable_effective_rank import (  # noqa: E402
    TARGETS_EXTRA,
    TARGETS_PRIMARY,
    _prepare_target,
    align_and_stack,
    compute_all_observables,
    correlation_matrix_and_rank,
    run_controls,
)

from allostery.hamiltonians import contact_matrix  # noqa: E402
from allostery.lowmode_predictor import dcc_low  # noqa: E402
from allostery.shortcuts import equipartition_ensemble, msf_cross_check  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0211_ensemble_graph_observable"

# Pre-registered (task file): starting sample count, raised until the
# split-half bar passes or the ceiling is hit.
N_SAMPLES_START = 2000
N_SAMPLES_CEILING = 8000
SPLIT_HALF_BAR = 0.70
NEW_AXIS_MIN_DELTA = 0.10


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _degree_matrix(coords0: np.ndarray, displacements: np.ndarray, cutoff: float) -> np.ndarray:
    """Per-sample, per-residue contact degree (row sum of the rebuilt
    binary contact graph) -- (n_samples, N). Rebuilds a genuinely discrete
    graph per sample (edges form/break), not a continuous displacement
    reduction."""
    n_samples = displacements.shape[0]
    n = coords0.shape[0]
    deg = np.empty((n_samples, n))
    for i in range(n_samples):
        A = contact_matrix(coords0 + displacements[i], cutoff=cutoff, weight="binary")
        deg[i] = A.sum(axis=1)
    return deg


def _seed_covariance_score(degree_matrix: np.ndarray, source: np.ndarray) -> np.ndarray:
    seed_series = degree_matrix[:, source].mean(axis=1)
    n = degree_matrix.shape[1]
    score = np.empty(n)
    for j in range(n):
        r = np.corrcoef(seed_series, degree_matrix[:, j])[0, 1]
        score[j] = abs(r) if np.isfinite(r) else 0.0
    return score


def ensemble_contact_covariance(coords: np.ndarray, source: np.ndarray, cutoff: float, *, rng) -> dict:
    """Runs the pre-registered construction, raising n_samples until the
    split-half bar passes or the ceiling is hit. Returns the full-ensemble
    score plus the MSF gate and split-half diagnostics."""
    n_samples = N_SAMPLES_START
    while True:
        ensemble = equipartition_ensemble(coords, cutoff=cutoff, n_modes=20, n_samples=n_samples, rng=rng)
        msf_gate = msf_cross_check(ensemble)
        if not msf_gate["ok"]:
            return {"error": "msf_cross_check failed", "msf_gate": msf_gate, "n_samples": n_samples}

        deg = _degree_matrix(coords, ensemble.displacements, cutoff)
        score = _seed_covariance_score(deg, source)

        half = n_samples // 2
        score_a = _seed_covariance_score(deg[:half], source)
        score_b = _seed_covariance_score(deg[half:], source)
        rho, _p = spearmanr(score_a, score_b)

        _log(f"  n_samples={n_samples}: msf_ok={msf_gate['ok']} split_half_rho={rho:.3f} (bar {SPLIT_HALF_BAR})")

        if rho >= SPLIT_HALF_BAR or n_samples >= N_SAMPLES_CEILING:
            return {
                "score": score, "msf_gate": msf_gate, "n_samples": n_samples,
                "split_half_rho": float(rho), "split_half_pass": bool(rho >= SPLIT_HALF_BAR),
            }
        n_samples = min(n_samples * 2, N_SAMPLES_CEILING)


def run_target(target_name: str, rng_seed: int = 0) -> dict:
    _log(f"=== {target_name} ===")
    t0 = time.monotonic()
    prep = _prepare_target(target_name)
    coords, source, cutoff = prep["coords"], prep["source"], prep["cutoff"]
    _log(f"{target_name}: prepared in {time.monotonic() - t0:.1f}s (N={prep['n_residues']})")

    observables = compute_all_observables(prep)
    names28, matrix28 = align_and_stack(observables)
    baseline = correlation_matrix_and_rank(matrix28)
    _log(f"{target_name}: baseline (28 obs) participation_ratio_rank={baseline['participation_ratio_rank']:.3f} "
         f"(wiring check vs TASK-0199's own published number)")

    t0 = time.monotonic()
    ens_result = ensemble_contact_covariance(coords, source, cutoff, rng=np.random.default_rng(rng_seed))
    _log(f"{target_name}: ensemble observable done in {time.monotonic() - t0:.1f}s")
    if "error" in ens_result:
        return {"target": target_name, "n_residues": prep["n_residues"], "error": ens_result["error"], "detail": ens_result}

    new_matrix = np.column_stack([matrix28, ens_result["score"]])
    with_new = correlation_matrix_and_rank(new_matrix)
    delta_real = with_new["participation_ratio_rank"] - baseline["participation_ratio_rank"]

    # Noise-column control (matched variance) -- must not mimic the effect.
    rng = np.random.default_rng(rng_seed + 1)
    noise_col = rng.normal(loc=ens_result["score"].mean(), scale=ens_result["score"].std(), size=len(ens_result["score"]))
    noise_matrix = np.column_stack([matrix28, noise_col])
    with_noise = correlation_matrix_and_rank(noise_matrix)
    delta_noise = with_noise["participation_ratio_rank"] - baseline["participation_ratio_rank"]

    # Controls (duplicate/random) must still behave on the 29-column matrix.
    controls_29 = run_controls(new_matrix)

    new_axis = bool(delta_real > delta_noise and delta_real >= NEW_AXIS_MIN_DELTA)

    # Correlation of the new observable against every existing one,
    # dcc_low in particular (this task's own TODO: is it dcc_low-like on
    # PTP1B specifically?).
    corr_vs_dcc_low, _p = spearmanr(ens_result["score"], observables["dcc_low"])

    _log(f"{target_name}: delta_real={delta_real:.3f} delta_noise={delta_noise:.3f} "
         f"new_axis={new_axis} rho_vs_dcc_low={corr_vs_dcc_low:.3f}")

    return {
        "target": target_name,
        "n_residues": prep["n_residues"],
        "baseline_rank_28": baseline["participation_ratio_rank"],
        "with_new_rank_29": with_new["participation_ratio_rank"],
        "delta_real": float(delta_real),
        "delta_noise_control": float(delta_noise),
        "new_axis_verdict": new_axis,
        "msf_gate": ens_result["msf_gate"],
        "n_samples_used": ens_result["n_samples"],
        "split_half_rho": ens_result["split_half_rho"],
        "split_half_pass": ens_result["split_half_pass"],
        "controls_29col": controls_29,
        "spearman_vs_dcc_low": float(corr_vs_dcc_low),
        "score": ens_result["score"].tolist(),
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    targets = sys.argv[1:] or (TARGETS_PRIMARY + TARGETS_EXTRA)
    results = {}
    for t in targets:
        try:
            r = run_target(t)
        except Exception as exc:  # noqa: BLE001
            r = {"target": t, "error": repr(exc)}
            _log(f"{t} FAILED: {exc!r}")
        results[t] = r
        with open(OUTPUT_DIR / "results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
    _log("done")
    for t, r in results.items():
        _log(f"{t}: new_axis={r.get('new_axis_verdict', r.get('error'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
