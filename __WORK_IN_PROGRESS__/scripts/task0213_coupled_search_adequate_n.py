"""TASK-0213 -- re-run TASK-0210's coupled search at adequate restart count.

TASK-0210 returned "tentatively OPEN, weakly supported": 0 of 2 restarts
reached the holo basin on either evaluable target. Zero successes out of two
is consistent with almost any difficulty. This re-runs the *identical* solver,
objective, firewall and success bars at a restart count where "hard" and
"under-searched" are distinguishable.

Nothing about the search is changed. Only `RESTARTS`/`ITERATIONS` are
overridden, and only after a cost calibration on this task's own candidate
files (TASK-0210's budget was sized on a stray file from an earlier task and
proved ~10x pessimistic). Timing is not an outcome; the budget is fixed by the
pre-registered formula and is not revised after any score is seen.

Pre-registration (targets, budget formula, success bar, three-way verdict
rule) lives in `.ai/tasks/IN_PROGRESS/TASK-0213-*.md` and was written before
this script ran.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import task0210_coupled_search as T210  # noqa: E402

TARGETS = ["KRAS_G12C", "PTP1B"]   # the only 2 targets whose firewall passes
WALL_BUDGET_S = 7200               # 2 h total, split evenly across targets
ITERATIONS_PREFERRED = 25
ITERATIONS_FALLBACK = 15
RESTARTS_FLOOR = 10
CALIB_RESTARTS, CALIB_ITERS = 1, 3
OUT_DIR = _ROOT / "results/tasks/0213_coupled_search_adequate_n"


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _rmsd_lookup() -> dict:
    p = _ROOT / "results/tasks/0208_apo_holo_decomposition" / "results.json"
    out = {}
    if p.exists():
        for r in json.loads(p.read_text()):
            if "rmsd_apo_to_holo" in r:
                out[r["target"]] = r["rmsd_apo_to_holo"]
    return out


def _run(target: str, restarts: int, iterations: int, rmsd_lookup: dict) -> dict:
    """Runs TASK-0210's own `run_target` with the budget overridden at module
    scope -- the solver, objective, firewall and bars are untouched."""
    T210.RESTARTS = restarts
    T210.ITERATIONS = iterations
    T210.COOL_RATE = (T210.T_END / T210.T_START) ** (1.0 / max(iterations - 1, 1))
    return T210.run_target(target, rmsd_lookup)


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    rmsd_lookup = _rmsd_lookup()

    # --- Cost calibration (not outcome calibration) ---
    _log(f"calibration: {CALIB_RESTARTS}x{CALIB_ITERS} per target on real candidate files")
    calib = {}
    for t in TARGETS:
        t0 = time.monotonic()
        r = _run(t, CALIB_RESTARTS, CALIB_ITERS, rmsd_lookup)
        dt = time.monotonic() - t0
        per_iter = dt / (CALIB_RESTARTS * CALIB_ITERS)
        calib[t] = {"wall_s": round(dt, 1), "s_per_iteration": round(per_iter, 2),
                    "firewall_ok": (r.get("known_answer_check") or {}).get("objective_prefers_holo")}
        _log(f"  {t}: {dt:.1f}s total, {per_iter:.2f}s/iteration, firewall={calib[t]['firewall_ok']}")

    mean_per_iter = sum(c["s_per_iteration"] for c in calib.values()) / len(calib)
    per_target_budget = WALL_BUDGET_S / len(TARGETS)
    total_iters = int(per_target_budget // mean_per_iter)

    iterations = ITERATIONS_PREFERRED
    restarts = total_iters // iterations
    if restarts < RESTARTS_FLOOR:
        iterations = ITERATIONS_FALLBACK
        restarts = total_iters // iterations
    restarts = max(restarts, RESTARTS_FLOOR)

    budget = {
        "mean_s_per_iteration": round(mean_per_iter, 2),
        "per_target_wall_budget_s": per_target_budget,
        "iterations": iterations, "restarts": restarts,
        "projected_wall_s_per_target": round(restarts * iterations * mean_per_iter, 1),
        "rule": "ITERATIONS=25 preferred, fall back to 15 before dropping RESTARTS below 10",
    }
    _log(f"BUDGET FIXED (not revised after any score): {restarts} restarts x {iterations} "
         f"iterations/target, projected {budget['projected_wall_s_per_target']/60:.1f} min/target")
    (OUT_DIR / "budget.json").write_text(json.dumps({"calibration": calib, "budget": budget}, indent=1))

    # --- Full run at the fixed budget ---
    results = []
    for t in TARGETS:
        _log(f"=== {t}: {restarts}x{iterations} ===")
        t0 = time.monotonic()
        try:
            r = _run(t, restarts, iterations, rmsd_lookup)
        except Exception as exc:  # noqa: BLE001
            import traceback; traceback.print_exc()
            r = {"target": t, "error": repr(exc)}
        r["elapsed_s"] = round(time.monotonic() - t0, 1)
        r["budget"] = budget
        results.append(r)
        (OUT_DIR / "results.json").write_text(json.dumps(results, indent=2, default=str))
        _log(f"{t}: any_restart_success={r.get('any_restart_success', r.get('error'))} "
             f"({r['elapsed_s']/60:.1f} min)")

    # --- Pre-registered three-way verdict ---
    print("\n=== TASK-0213 verdict ===")
    n_success = {}
    for r in results:
        rs = r.get("restarts") or []
        n = sum(1 for x in rs if isinstance(x, dict) and x.get("success"))
        n_success[r["target"]] = n
        print(f"  {r['target']}: {n} successful restarts of {budget['restarts']}")
    total = sum(n_success.values())
    if any(n >= 2 for n in n_success.values()):
        verdict = "CLOSED (search is not the bottleneck)"
    elif total == 0:
        verdict = "OPEN (no restart reached the bar at the full budget)"
    else:
        verdict = "INDETERMINATE (exactly one lone success -- a lottery ticket, not a solved instance)"
    print(f"  VERDICT: {verdict}")
    (OUT_DIR / "verdict.json").write_text(json.dumps(
        {"n_success": n_success, "verdict": verdict, "budget": budget}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
