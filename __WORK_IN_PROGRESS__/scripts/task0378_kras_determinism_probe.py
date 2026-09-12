#!/usr/bin/env python3
"""TASK-0378 -- is KRAS's number stable? Ten re-runs, but varying the thing
that could actually differ (thread count -> BLAS/LAPACK routing), each in
a genuinely fresh process, not ten calls in one interpreter.

Why fresh processes, not a loop: OMP_NUM_THREADS/OPENBLAS_NUM_THREADS/
MKL_NUM_THREADS are read by the BLAS/LAPACK library at process start (via
its own thread-pool init) -- setting them mid-process after numpy is
already imported has no effect. Each run is therefore a real subprocess
(`task0378_kras_determinism_child.py`), which also satisfies this task's
own "at least one run in a separate interpreter invocation" -- every one
of the ten is.

Sweep, 10 runs total covering {1, 2, 4, 8} with repeats so at least one
repeat exists per thread count: [1,2,4,8,1,2,4,8,1,2].

Reports, per this task's own Intent Contract:
  1. Exact reproduction of TASK-0376's committed KRAS numbers on run 1
     (Planned Validation gate -- stops here if it fails).
  2. Max absolute deviation across all 10 runs: score_auc, the full
     winner_occ vector, and top-5 residue Jaccard.
  3. The eigenvalue gap spectrum for 4LDJ's winner Hamiltonian: how many
     gaps fall below degenerate_tol (1e-6 of bandwidth), and the smallest
     few -- stating the degenerate-subspace hazard with a number.
  4. Only if variation is found: re-run with degenerate_tol varied and
     report which observables move. (Not attempted here unless triggered
     -- this task measures, it does not fix anything.)

Run: ../.venv/bin/python3 -u scripts/task0378_kras_determinism_probe.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path("results/tasks/0378_kras_determinism_probe")
CHILD = HERE / "task0378_kras_determinism_child.py"

COMMITTED_SCORE_AUC = 0.5136485966935793
COMMITTED_FLOOR_AUC = 0.5288350634371395
DEGENERATE_TOL_FRACTION = 1e-6  # matches time_averaged_ctqw_converged's own default

THREAD_SWEEP = [1, 2, 4, 8, 1, 2, 4, 8, 1, 2]


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run_one(threads: int, run_idx: int, degenerate_tol: float = None) -> dict:
    env = dict(os.environ)
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
               "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        env[var] = str(threads)
    cmd = [sys.executable, str(CHILD)]
    if degenerate_tol is not None:
        cmd += ["--degenerate-tol", str(degenerate_tol)]
    t0 = time.time()
    proc = subprocess.run(
        cmd, cwd=str(HERE.parent), env=env,
        capture_output=True, text=True, timeout=600,
    )
    dt = time.time() - t0
    if proc.returncode != 0:
        raise RuntimeError(
            f"run {run_idx} (threads={threads}) failed, exit {proc.returncode}:\n"
            f"stdout(tail): {proc.stdout[-2000:]}\nstderr(tail): {proc.stderr[-2000:]}"
        )
    # child prints exactly one JSON line -- the last non-empty stdout line,
    # since some numpy/BLAS combinations emit stray warnings to stdout on
    # certain platforms even though this project's own warnings go to
    # stderr (confirmed by construction of the child script, defensive
    # here rather than assumed).
    lines = [l for l in proc.stdout.splitlines() if l.strip()]
    if not lines:
        raise RuntimeError(f"run {run_idx} (threads={threads}): no stdout from child")
    data = json.loads(lines[-1])
    data["_threads"] = threads
    data["_run_idx"] = run_idx
    data["_wall_s"] = dt
    return data


def jaccard(a, b) -> float:
    a, b = set(a), set(b)
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def eigengap_report(eigenvalues) -> dict:
    import numpy as np
    w = np.asarray(eigenvalues)
    bandwidth = float(w[-1] - w[0])
    tol = DEGENERATE_TOL_FRACTION * bandwidth
    gaps = np.diff(w)
    n_below = int(np.sum(gaps < tol))
    smallest = sorted(gaps.tolist())[:8]
    return dict(bandwidth=bandwidth, degenerate_tol_abs=tol,
               n_gaps_below_tol=n_below, n_gaps_total=len(gaps),
               smallest_gaps=smallest)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    runs = []
    _log(f"Sweep: {THREAD_SWEEP} (10 runs, fresh process each, thread count varied)")
    for i, threads in enumerate(THREAD_SWEEP, 1):
        _log(f"[{i}/10] threads={threads}: spawning fresh child process...")
        data = run_one(threads, i)
        _log(f"  score_auc={data['score_auc']!r} floor_auc={data['floor_auc']!r} "
             f"top5={data['top5']} wall={data['_wall_s']:.1f}s")
        runs.append(data)
        (OUT / f"run_{i:02d}_threads{threads}.json").write_text(json.dumps(data, indent=1))

    # --- Planned Validation gate: run 1 must reproduce the committed values EXACTLY ---
    r1 = runs[0]
    score_match = r1["score_auc"] == COMMITTED_SCORE_AUC
    floor_match = r1["floor_auc"] == COMMITTED_FLOOR_AUC
    _log(f"Planned Validation: score_auc exact match = {score_match} "
        f"({r1['score_auc']!r} vs committed {COMMITTED_SCORE_AUC!r})")
    _log(f"Planned Validation: floor_auc exact match = {floor_match} "
        f"({r1['floor_auc']!r} vs committed {COMMITTED_FLOOR_AUC!r})")
    if not (score_match and floor_match):
        _log("STOPPING per this task's own Planned Validation -- harness does not "
            "exactly reproduce the committed numbers on run 1.")
        summary = dict(stopped=True, reason="planned_validation_failed",
                       run1_score_auc=r1["score_auc"], run1_floor_auc=r1["floor_auc"],
                       committed_score_auc=COMMITTED_SCORE_AUC, committed_floor_auc=COMMITTED_FLOOR_AUC)
        (OUT / "summary.json").write_text(json.dumps(summary, indent=1))
        return 1

    # --- Cross-run comparison ---
    import numpy as np
    score_aucs = [r["score_auc"] for r in runs]
    max_score_dev = max(abs(s - score_aucs[0]) for s in score_aucs)
    floor_aucs = [r["floor_auc"] for r in runs]
    max_floor_dev = max(abs(f - floor_aucs[0]) for f in floor_aucs)

    occ_arrays = [np.asarray(r["winner_occ"]) for r in runs]
    max_occ_dev = max(float(np.max(np.abs(occ - occ_arrays[0]))) for occ in occ_arrays)

    top5_sets = [r["top5"] for r in runs]
    min_jaccard = min(jaccard(top5_sets[0], t) for t in top5_sets)
    all_top5_identical = all(set(t) == set(top5_sets[0]) for t in top5_sets)

    byte_identical_occ = all(occ_arrays[0].tobytes() == occ.tobytes() for occ in occ_arrays)

    _log(f"Cross-run (10 runs, threads {sorted(set(THREAD_SWEEP))}):")
    _log(f"  max |score_auc - run1| = {max_score_dev:.3e}")
    _log(f"  max |floor_auc - run1| = {max_floor_dev:.3e}")
    _log(f"  max |winner_occ - run1| (any element, any run) = {max_occ_dev:.3e}")
    _log(f"  top-5 residue set: identical across all runs = {all_top5_identical} "
        f"(min pairwise Jaccard to run1 = {min_jaccard:.3f})")
    _log(f"  winner_occ byte-identical across all runs = {byte_identical_occ}")

    eiggap = eigengap_report(r1["eigenvalues"])
    _log(f"Eigenvalue gap spectrum (4LDJ winner H, N={r1['N']}): "
        f"bandwidth={eiggap['bandwidth']:.4f}, degenerate_tol(abs)={eiggap['degenerate_tol_abs']:.3e}, "
        f"gaps below tol = {eiggap['n_gaps_below_tol']}/{eiggap['n_gaps_total']}")
    _log(f"  smallest 8 gaps: {[f'{g:.3e}' for g in eiggap['smallest_gaps']]}")

    variation_found = not byte_identical_occ
    summary = dict(
        stopped=False,
        planned_validation="PASSES",
        run1_score_auc=r1["score_auc"], run1_floor_auc=r1["floor_auc"],
        thread_sweep=THREAD_SWEEP,
        max_score_auc_deviation=max_score_dev,
        max_floor_auc_deviation=max_floor_dev,
        max_winner_occ_deviation=max_occ_dev,
        top5_identical_across_runs=all_top5_identical,
        min_pairwise_top5_jaccard=min_jaccard,
        winner_occ_byte_identical_across_runs=byte_identical_occ,
        eigengap=eiggap,
        variation_found=variation_found,
        note_out_of_scope="Not re-measuring apo-draw/structure-swap/clock/seed-set spread "
                          "-- those are TASK-0155/0270/0350/0102's own, already-measured, "
                          "and are not run-to-run noise. This task only tests whether the "
                          "SAME input, same code, varying thread count, reproduces exactly.",
    )
    if variation_found:
        _log("VARIATION FOUND -- running item 4 of the Intent Contract: vary "
            "degenerate_tol at a fixed thread count (1) and report which "
            "observables move.")
        tol_sweep = [0.0, 1e-10, 1e-8, 1e-6, 1e-4, 1e-2]
        tol_runs = []
        for j, tol in enumerate(tol_sweep, 1):
            _log(f"  degenerate_tol={tol:.0e}: spawning child...")
            d = run_one(threads=1, run_idx=100 + j, degenerate_tol=tol)
            tol_runs.append(d)
            (OUT / f"tol_run_{j:02d}_tol{tol:.0e}.json").write_text(json.dumps(d, indent=1))
        base_occ = np.asarray(tol_runs[0]["winner_occ"])
        tol_deltas = []
        for d in tol_runs:
            occ = np.asarray(d["winner_occ"])
            tol_deltas.append(dict(
                degenerate_tol=d["degenerate_tol"],
                score_auc=d["score_auc"],
                max_abs_occ_delta_vs_tol0=float(np.max(np.abs(occ - base_occ))),
                top5=d["top5"],
            ))
            _log(f"    tol={d['degenerate_tol']:.0e}: score_auc={d['score_auc']!r} "
                f"top5={d['top5']}")
        summary["degenerate_tol_sweep"] = tol_deltas
    else:
        _log("No variation found across the 10-run thread sweep -- item 4 ('if and "
            "only if variation is found') does not trigger; not run.")

    (OUT / "summary.json").write_text(json.dumps(summary, indent=1))
    _log(f"Wrote {OUT / 'summary.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
