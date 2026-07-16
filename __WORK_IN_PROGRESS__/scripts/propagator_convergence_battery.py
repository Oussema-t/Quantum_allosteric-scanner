#!/usr/bin/env python3
"""TASK-0109 -- synthetic propagator-convergence characterization battery.

Empirically finds the minimum adequate `t_max` (for `ground_state_
relaxation` and `time_averaged_ctqw`) and `n_steps` (Nyquist, for
`time_averaged_ctqw`) across a grid of synthetic system sizes and
spectral-gap conditions (`propagators.build_gapped_synthetic_network`),
compares the empirical minimum against this module's own closed-form
predictions (`propagators.min_adequate_t_max`/`min_adequate_n_steps`,
themselves grounded in TASK-0102's spectral-gap precedent and Aharonov-
Ambainis-Kempe-Vazirani's Lemma 4.3, see `propagators.check_convergence`'s
docstring), and fits/reports the scaling relationship -- a power law if
the data actually looks like one, stated plainly if it does not (this
task's own Planned Validation: "find out what's true, not confirm a
hypothesis").

No PDB/network access -- synthetic only, per this task's own Out Of Scope.

Performance note (found running the first version of this script): naively
calling `propagators.time_averaged_ctqw` once per scanned (t_max, n_steps)
candidate re-decomposes nothing extra (it already caches `eigh`) but *does*
re-run its own internal `n_steps`-length Python loop from scratch for every
single candidate -- for a dense candidate grid this is `O(candidates x
n_steps_each)` calls to the O(N^2) per-step evolution formula, which grew
unusably slow at N=500 (a run was killed after 25+ minutes with no cell
complete). This version instead evaluates the CTQW occupation at every
needed time point *once*, in a single vectorized `(M, N) @ (N, N)` batched
matmul (`_vectorized_ctqw_batch`), and derives every candidate's time-
average from group-sums over that one batch -- exact reproduction of
`time_averaged_ctqw`'s own definition (`linspace(0, t_max, n_steps)`), not
an approximation, at a small fraction of the cost.

Usage
-----
  python scripts/propagator_convergence_battery.py
  python scripts/propagator_convergence_battery.py --output-dir results_task0109
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Same rationale as sweep_operators.py/run_challenge.py's identical block
# (found 2026-07-14/15 running uncapped heavy jobs concurrently on this
# shared machine): must run before `import numpy`.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.propagators import (  # noqa: E402
    build_gapped_synthetic_network,
    ground_state_relaxation,
    min_adequate_n_steps,
    min_adequate_t_max,
)

TOL = 1e-2  # total-variation-distance convergence tolerance, this battery's
# own choice -- matches `check_convergence`'s own default, kept identical
# so the analytic-vs-empirical comparison below is apples to apples.
N_GRID = [20, 50, 100, 200, 500]
WELL_DEPTH_GRID = [0.0, 2.0, 10.0, 50.0]
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0109"

T_MAX_SCAN_CAP = 3000.0  # practical ceiling on how far this battery will
# actually *scan* t_max candidates for the time_averaged_ctqw criterion,
# independent of how large the closed-form analytic prediction is. Found
# necessary 2026-07-15, first run: `min_gap` (the smallest eigenvalue gap
# over *all* pairs, what the AAKV-style bound in `check_convergence` uses)
# shrinks roughly as 1/N^2 for this ring-topology construction's
# near-degenerate eigenvalue pairs -- measured 5.2e-2 at N=20 down to
# ~1.3e-4 at N=500 (seed 0). Because `min_adequate_t_max` is `O(1/min_gap)`,
# this makes the *naive* min-over-all-pairs bound predict `t_max` in the
# tens of thousands at N=200+ and past 1e5 at N=500 -- a real, honestly-
# reported finding about this criterion's fragility on near-degenerate
# spectra (most of that minimum gap is between eigenmode pairs the source
# barely overlaps, which the naive bound does not weight down; see this
# task's own Done section), not a bug to silently paper over. This cap
# keeps the *empirical validation scan* tractable -- when the analytic
# prediction exceeds it, empirical search is skipped and reported as
# `None` with an explicit reason recorded, never silently truncated or
# extrapolated past what was actually measured.
N_STEPS_SCAN_CAP = 4000  # matching per-candidate ceiling on n_steps used
# *within* a t_max scan (derived per-candidate-t from `min_adequate_n_
# steps`, not one shared worst-case value for the whole grid -- see
# `empirical_min_t_max_ctqw`).


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _tv_distance(p: np.ndarray, q: np.ndarray) -> float:
    return float(np.abs(p - q).sum() / 2.0)


def _true_ground_state_density(v: np.ndarray, source: int) -> np.ndarray:
    """The exact t->infinity limit of `ground_state_relaxation`.

    Found by debugging 2026-07-15: an earlier version of this function
    used `v[:,0]**2` (the ground eigenvector's *squared* components,
    always non-negative) -- wrong whenever the true limit's *sign*
    matters, which it does here. `ground_state_relaxation`'s actual limit
    is `clip(v[:,0] * <v_0|p0>, 0, None)`, renormalized (see its own
    source: `col = v @ (exp_w * coeffs)`, dominated by the `w[0]` term as
    `t` grows, then clipped/renormalized) -- if `<v_0|p0>` (`v[source,0]`
    for a scalar source) is negative, clipping zeroes out a *different*
    half of the eigenvector than squaring would keep. Using the wrong
    reference produced an apparent non-convergence plateau (total-
    variation distance stuck around 0.31 at large `t` instead of ->0) for
    every case where the sign happened to be negative -- confirmed a
    harness bug, not a `ground_state_relaxation` defect, by checking the
    propagator's real output at `t=1000` against both candidate
    references directly (TV=0.31 vs the wrong one, TV=7e-17 -- machine
    precision -- vs this corrected one)."""
    coeff0 = v[source, 0]
    d = np.clip(v[:, 0] * coeff0, 0.0, None)
    return d / (d.sum() + 1e-300)


def _true_diagonal_ensemble(v: np.ndarray, source: int) -> np.ndarray:
    """The exact infinite-time-average limit of `time_averaged_ctqw`
    (this pipeline's own documented decoherent limit, `RESULTS.md`):
    `sum_k |v_k(j)|^2 |v_k(source)|^2`. Closed-form -- no time integration
    needed, so this battery compares against the *true* limit rather than
    a "10x finer" numerical proxy."""
    d = (v ** 2) @ (v[source, :] ** 2)
    return d / d.sum()


def _vectorized_ctqw_batch(w: np.ndarray, v: np.ndarray, t_values: np.ndarray, source: int) -> np.ndarray:
    """`p(t)` for every `t` in `t_values` (1-D array of length M), in one
    batched `(M, N) @ (N, N)` matmul rather than a per-`t` Python loop --
    the single-`t` formula (`propagators._ctqw_from_eigh`) generalized
    across a whole time array at once. Scalar `source` only (sufficient
    for this synthetic battery; the multi-index case is
    `_ctqw_from_eigh`'s own job, unchanged by this script).

    Returns (M, N): row i is the occupation vector at `t_values[i]`.
    """
    coeffs = v[source, :]
    phase = np.exp(-1j * np.outer(t_values, w))  # (M, N)
    amplitudes = (phase * coeffs[np.newaxis, :]) @ v.T  # (M, N)
    p = np.abs(amplitudes) ** 2
    p /= p.sum(axis=1, keepdims=True) + 1e-300
    return p


def empirical_min_t_max_gsr(H: np.ndarray, v: np.ndarray, source: int, t_grid: np.ndarray):
    """Scan `t_grid` (ascending) for the smallest `t` whose `ground_state_
    relaxation` output is within `TOL` (total-variation distance) of the
    true closed-form ground-state density. `ground_state_relaxation` has
    no internal sub-step loop (a single O(N^2) evaluation per `t`), so a
    plain per-`t` scan is already cheap -- no batching needed here."""
    target = _true_ground_state_density(v, source)
    for t in t_grid:
        p = ground_state_relaxation(H, float(t), source=source)
        if _tv_distance(p, target) <= TOL:
            return float(t)
    return None


def empirical_min_t_max_ctqw(w: np.ndarray, v: np.ndarray, source: int, t_grid: np.ndarray):
    """`time_averaged_ctqw(t_max=t, n_steps=<Nyquist-adequate for t>)` for
    every `t` in `t_grid`, exactly reproduced via one shared batch:
    `linspace(0, t, n_steps(t))` for each candidate `t` is generated
    explicitly (its own `n_steps` derived per-candidate from
    `min_adequate_n_steps`, capped at `N_STEPS_SCAN_CAP` -- not one
    shared worst-case `n_steps` applied to every candidate regardless of
    its own much smaller `t`, which is what made the first version of
    this scan blow up: most candidates in a geomspace grid are far
    smaller than the largest, so giving all of them the largest one's
    Nyquist requirement wastes nearly all the work) and concatenated,
    `_vectorized_ctqw_batch` evaluates the union once, then each
    candidate's own mean is a group-sum over its slice."""
    target = _true_diagonal_ensemble(v, source)
    slices = []
    all_times = []
    offset = 0
    for t in t_grid:
        n_steps = min(min_adequate_n_steps(w=w, t_max=float(t)), N_STEPS_SCAN_CAP)
        times = np.linspace(0.0, float(t), n_steps)
        all_times.append(times)
        slices.append((offset, offset + n_steps))
        offset += n_steps
    all_times = np.concatenate(all_times)
    p_all = _vectorized_ctqw_batch(w, v, all_times, source)
    for t, (a, b) in zip(t_grid, slices):
        p_mean = p_all[a:b].mean(axis=0)
        if _tv_distance(p_mean, target) <= TOL:
            return float(t)
    return None


def empirical_min_n_steps(w: np.ndarray, v: np.ndarray, t_max: float, source: int, n_grid: np.ndarray):
    """Same batching trick as `empirical_min_t_max_ctqw`, holding `t_max`
    fixed and scanning `n_steps` instead: the reference is the finest
    `n_steps` in `n_grid` (this scan's own internal reference, not the
    true closed-form limit -- a coarse `n_steps` at fixed `t_max` is a
    *sampling*-adequacy question, distinct from whether `t_max` itself is
    long enough, which `empirical_min_t_max_ctqw` already answers)."""
    n_grid = np.asarray(sorted(set(int(n) for n in n_grid)))
    slices = []
    all_times = []
    offset = 0
    for n in n_grid:
        times = np.linspace(0.0, t_max, int(n))
        all_times.append(times)
        slices.append((offset, offset + int(n)))
        offset += int(n)
    all_times = np.concatenate(all_times)
    p_all = _vectorized_ctqw_batch(w, v, all_times, source)
    means = [p_all[a:b].mean(axis=0) for a, b in slices]
    reference = means[-1]
    for n, p_mean in zip(n_grid, means):
        if _tv_distance(p_mean, reference) <= TOL:
            return int(n)
    return None


def _power_law_fit(x: np.ndarray, y: np.ndarray):
    """log-log linear regression; returns (exponent, intercept, r_squared).
    Callers must check `r_squared` themselves and report plainly if it is
    not close to 1 -- this function does not decide "is this a power law,"
    it only fits one and reports the fit quality."""
    mask = (x > 0) & (y > 0) & np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 2:
        return None, None, None
    log_x, log_y = np.log(x[mask]), np.log(y[mask])
    slope, intercept = np.polyfit(log_x, log_y, 1)
    pred = slope * log_x + intercept
    ss_res = np.sum((log_y - pred) ** 2)
    ss_tot = np.sum((log_y - log_y.mean()) ** 2)
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return float(slope), float(intercept), float(r_squared)


def run_battery(seed: int = 0) -> dict:
    rows = []
    cells = [(N, depth) for N in N_GRID for depth in WELL_DEPTH_GRID]
    total = len(cells)
    cell_durations = []
    for i, (N, depth) in enumerate(cells, start=1):
        cell_start = time.monotonic()
        H = build_gapped_synthetic_network(N, depth, seed=seed)
        w, v = np.linalg.eigh(H)
        gap = float(w[1] - w[0])
        bandwidth = float(w[-1] - w[0])
        gaps_all = np.abs(w[:, None] - w[None, :])
        nonzero = gaps_all[gaps_all > 1e-12]
        min_gap = float(nonzero.min()) if nonzero.size else 0.0
        source = 0

        analytic_t_gsr = min_adequate_t_max(w=w, kind="ground_state_relaxation", tol=TOL)
        t_grid_gsr = np.geomspace(max(analytic_t_gsr / 50.0, 1e-3), analytic_t_gsr * 3.0, 60)
        empirical_t_gsr = empirical_min_t_max_gsr(H, v, source, t_grid_gsr)

        analytic_t_ctqw = min_adequate_t_max(w=w, kind="time_averaged_ctqw", tol=TOL)
        if analytic_t_ctqw > T_MAX_SCAN_CAP:
            empirical_t_ctqw = None
            ctqw_scan_note = (
                f"skipped: analytic prediction {analytic_t_ctqw:.4g} exceeds "
                f"practical scan cap {T_MAX_SCAN_CAP:.0f} (near-degenerate "
                f"min_gap={min_gap:.3g} makes the naive AAKV bound impractically "
                "large here -- see this script's own T_MAX_SCAN_CAP comment)"
            )
        else:
            t_grid_ctqw = np.geomspace(max(analytic_t_ctqw / 50.0, 1e-3), min(analytic_t_ctqw * 3.0, T_MAX_SCAN_CAP), 25)
            empirical_t_ctqw = empirical_min_t_max_ctqw(w, v, source, t_grid_ctqw)
            ctqw_scan_note = None

        analytic_n = min_adequate_n_steps(w=w, t_max=analytic_t_ctqw)
        n_grid_max = min(max(analytic_n * 6, 20), N_STEPS_SCAN_CAP)
        n_grid = np.unique(np.geomspace(2, n_grid_max, 25).astype(int))
        t_max_for_n_scan = min(analytic_t_ctqw, T_MAX_SCAN_CAP)
        empirical_n = empirical_min_n_steps(w, v, t_max_for_n_scan, source, n_grid)

        rows.append({
            "N": N, "well_depth": depth, "gap": gap, "min_gap": min_gap,
            "bandwidth": bandwidth,
            "analytic_t_max_gsr": analytic_t_gsr, "empirical_t_max_gsr": empirical_t_gsr,
            "analytic_t_max_ctqw": analytic_t_ctqw, "empirical_t_max_ctqw": empirical_t_ctqw,
            "ctqw_scan_note": ctqw_scan_note,
            "analytic_n_steps": analytic_n, "empirical_n_steps": empirical_n,
        })

        duration = time.monotonic() - cell_start
        cell_durations.append(duration)
        mean_duration = sum(cell_durations) / len(cell_durations)
        remaining = total - i
        eta = f"{mean_duration * remaining:.1f}s" if remaining else "0s"
        _log(
            f"[{i}/{total}] N={N} depth={depth}: gap={gap:.4g} analytic_t_gsr={analytic_t_gsr:.4g} "
            f"empirical_t_gsr={empirical_t_gsr} | analytic_t_ctqw={analytic_t_ctqw:.4g} "
            f"empirical_t_ctqw={empirical_t_ctqw} | analytic_n={analytic_n} empirical_n={empirical_n} "
            f"-- took {duration:.2f}s, avg {mean_duration:.2f}s/cell, ETA {eta} for {remaining} remaining"
        )

    gaps = np.array([r["gap"] for r in rows])
    emp_t_gsr = np.array([r["empirical_t_max_gsr"] if r["empirical_t_max_gsr"] is not None else np.nan for r in rows])
    slope_gsr, intercept_gsr, r2_gsr = _power_law_fit(1.0 / gaps, emp_t_gsr)

    min_gaps = np.array([r["min_gap"] for r in rows])
    emp_t_ctqw = np.array([r["empirical_t_max_ctqw"] if r["empirical_t_max_ctqw"] is not None else np.nan for r in rows])
    slope_ctqw, intercept_ctqw, r2_ctqw = _power_law_fit(1.0 / min_gaps, emp_t_ctqw)

    bandwidths = np.array([r["bandwidth"] for r in rows])
    emp_n = np.array([r["empirical_n_steps"] if r["empirical_n_steps"] is not None else np.nan for r in rows])
    slope_n, intercept_n, r2_n = _power_law_fit(bandwidths, emp_n)

    return {
        "tol": TOL,
        "rows": rows,
        "fits": {
            "empirical_t_max_gsr_vs_inverse_gap": {"exponent": slope_gsr, "log_intercept": intercept_gsr, "r_squared": r2_gsr},
            "empirical_t_max_ctqw_vs_inverse_min_gap": {"exponent": slope_ctqw, "log_intercept": intercept_ctqw, "r_squared": r2_ctqw},
            "empirical_n_steps_vs_bandwidth": {"exponent": slope_n, "log_intercept": intercept_n, "r_squared": r2_n},
        },
    }


def render_report(result: dict) -> str:
    lines = [
        "# Propagator convergence battery (TASK-0109)",
        "",
        f"Synthetic only, no PDB/network. Tolerance (total-variation distance): {result['tol']}.",
        "",
        "| N | well_depth | gap | min_gap | bandwidth | analytic t_gsr | empirical t_gsr | analytic t_ctqw | empirical t_ctqw | analytic n | empirical n |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in result["rows"]:
        lines.append(
            f"| {r['N']} | {r['well_depth']} | {r['gap']:.4g} | {r['min_gap']:.4g} | "
            f"{r['bandwidth']:.4g} | {r['analytic_t_max_gsr']:.4g} | {r['empirical_t_max_gsr']} | "
            f"{r['analytic_t_max_ctqw']:.4g} | {r['empirical_t_max_ctqw']} | "
            f"{r['analytic_n_steps']} | {r['empirical_n_steps']} |"
        )
    lines.append("")
    lines.append("## Power-law fits (log-log regression, y = intercept * x^exponent)")
    lines.append("")
    for name, fit in result["fits"].items():
        if fit["exponent"] is None:
            lines.append(f"- **{name}**: insufficient valid (positive, finite) data points to fit.")
        else:
            lines.append(
                f"- **{name}**: exponent={fit['exponent']:.3f}, R²={fit['r_squared']:.4f}"
                + (" -- clean power law." if fit["r_squared"] > 0.95 else " -- NOT a clean power law, do not over-interpret the exponent.")
            )
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    _log(f"starting battery: {len(N_GRID)}x{len(WELL_DEPTH_GRID)}={len(N_GRID)*len(WELL_DEPTH_GRID)} cells")
    result = run_battery(seed=args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with open(args.output_dir / "convergence_battery.json", "w") as f:
        json.dump(result, f, indent=2)
    report = render_report(result)
    with open(args.output_dir / "report.md", "w") as f:
        f.write(report)
    _log(f"done, wrote {args.output_dir}/report.md")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
