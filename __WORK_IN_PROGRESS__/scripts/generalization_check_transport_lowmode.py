#!/usr/bin/env python3
"""TASK-0151 -- generalization-set check for TASK-0145's (quantum
transport) and TASK-0149's (low-mode PRS/DCC) Bonferroni-surviving
mandatory-3 positives, per TASK-0115's Rule #6 (repeated-exposure risk):
no robustness/generalizability claim is submission-final without being
checked against the TASK-0081/TASK-0127 generalization set.

Pure re-application, no new methodology: imports `transport_observable_
real_run.run_one` and `lowmode_predictor_real_run.run_target` directly
(both already fully parameterized by target name, no target-list
hardcoding inside the function bodies themselves) and calls them on
PTP1B and CASPASE7 -- the only 2 of the 4 named generalization targets
with a resolved, runnable config (GLUCOKINASE is blocked on an open
chain-schema question per TASK-0081's own Done section, CASPASE1/
HEMOGLOBIN/GLYCOGEN_PHOSPHORYLASE/PFK were never resolved at all --
confirmed directly by re-checking `config/targets.yaml`, not assumed
from memory).

Each observable keeps its OWN already-established evaluation lens
(a real, tested divergence from this task's own filing text, which
describes both as using "TASK-0123 distance-stratified AUC" -- true for
lowmode, not for transport, confirmed by reading both scripts directly
before assuming): `transport_observable_real_run.py` uses whole-graph
AUC + `diagnostics.classify_failure` (block-bootstrap CI) + a whole-
graph permutation null; `lowmode_predictor_real_run.py` uses TASK-0123's
own distance-stratified AUC + well-powered-shell filter + permutation
null. Re-deriving a uniform lens neither script actually uses would not
be "the exact same... evaluation lens already established," it would be
a third, new one.

Bonferroni: this task's own new comparisons, NOT folded into the
mandatory-3's own already-reported alpha (explicit per this task's own
Constraint). Two separate families, matching each observable's own
scope: transport = 2 targets x 3 quantities (R_eff, T(E=0) on L, T(E=0)
on H_new) = 6; lowmode = 2 targets x 2 observables x 4 k_modes = 16.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "4")

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import transport_observable_real_run as transport_run  # noqa: E402
import lowmode_predictor_real_run as lowmode_run  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0151_generalization_check"
GEN_TARGETS = ["PTP1B", "CASPASE7"]

ALPHA = 0.05
TRANSPORT_N_COMPARISONS = len(GEN_TARGETS) * 3  # R_eff, T(E=0) on L, T(E=0) on H_new
LOWMODE_N_COMPARISONS = len(GEN_TARGETS) * 2 * len(lowmode_run.K_MODES_GRID)  # 2 observables x k-grid
TRANSPORT_ALPHA = ALPHA / TRANSPORT_N_COMPARISONS
LOWMODE_ALPHA = ALPHA / LOWMODE_N_COMPARISONS


def _log(msg: str) -> None:
    print(msg, flush=True)


def run_transport() -> dict:
    results = {}
    for target in GEN_TARGETS:
        _log(f"[transport] {target}: running (reusing transport_observable_real_run.run_one verbatim)...")
        try:
            results[target] = transport_run.run_one(target)
        except Exception as exc:
            results[target] = {"target": target, "error": str(exc)}
            _log(f"[transport] {target}: FAILED -- {exc!r}")
    return results


def run_lowmode() -> dict:
    results = {}
    for target in GEN_TARGETS:
        _log(f"[lowmode] {target}: running (reusing lowmode_predictor_real_run.run_target verbatim)...")
        try:
            results[target] = lowmode_run.run_target(target)
        except Exception as exc:
            results[target] = {"target": target, "error": str(exc)}
            _log(f"[lowmode] {target}: FAILED -- {exc!r}")
    return results


def summarize_transport(results: dict) -> list:
    """Per-cell verdicts against THIS task's own Bonferroni family
    (transport_alpha), not TASK-0145's own (which used a 3-target,
    not 3-target-x-3-quantity, divisor -- a different family; see this
    task's own Done section)."""
    rows = []
    for target, r in results.items():
        if "error" in r:
            rows.append({"target": target, "error": r["error"]})
            continue
        for name in ("effective_resistance", "transmission_on_L_E0", "transmission_on_H_new_E0"):
            cell = r[name]
            p = cell["permutation_null"]["p_value"]
            rows.append({
                "target": target, "observable": name, "auc": cell["auc"],
                "category": cell["category"], "ci_overlap": cell["ci_overlap"],
                "p_value": p, "bonferroni_alpha": TRANSPORT_ALPHA,
                "significant": bool(p < TRANSPORT_ALPHA),
            })
    return rows


def summarize_lowmode(results: dict) -> list:
    rows = []
    for target, r in results.items():
        if "error" in r:
            rows.append({"target": target, "error": r["error"]})
            continue
        for cell in r["cells"]:
            p = cell["permutation_null"]["p_value"]
            rows.append({
                "target": target, "observable": cell["observable"], "k_modes": cell["k_modes"],
                "whole_graph_auc": cell["whole_graph_auc"], "floor_cleared": cell["floor_cleared"],
                "well_powered_max_auc": cell["well_powered_max_auc"],
                "rho_score_neg_hop": cell["rho_score_neg_hop"],
                "p_value": p, "bonferroni_alpha": LOWMODE_ALPHA,
                "significant": bool(p < LOWMODE_ALPHA),
            })
    return rows


def main() -> int:
    transport_results = run_transport()
    lowmode_results = run_lowmode()

    transport_summary = summarize_transport(transport_results)
    lowmode_summary = summarize_lowmode(lowmode_results)

    _log("\n=== Transport generalization check ===")
    _log(f"Bonferroni: 0.05 / {TRANSPORT_N_COMPARISONS} = {TRANSPORT_ALPHA:.5f}")
    for row in transport_summary:
        if "error" in row:
            _log(f"  {row['target']}: ERROR {row['error']}")
            continue
        _log(
            f"  {row['target']} / {row['observable']}: AUC={row['auc']:.3f} ({row['category']}) "
            f"ci_overlap={row['ci_overlap']} p={row['p_value']:.4f} significant={row['significant']}"
        )

    _log("\n=== Lowmode generalization check ===")
    _log(f"Bonferroni: 0.05 / {LOWMODE_N_COMPARISONS} = {LOWMODE_ALPHA:.5f}")
    for row in lowmode_summary:
        if "error" in row:
            _log(f"  {row['target']}: ERROR {row['error']}")
            continue
        _log(
            f"  {row['target']} / {row['observable']} k={row['k_modes']}: "
            f"whole_auc={row['whole_graph_auc']:.3f} well_powered_max={row['well_powered_max_auc']:.3f} "
            f"rho={row['rho_score_neg_hop']:.3f} p={row['p_value']:.4f} significant={row['significant']}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "transport": {
            "raw": transport_results, "summary": transport_summary,
            "n_comparisons": TRANSPORT_N_COMPARISONS, "bonferroni_alpha": TRANSPORT_ALPHA,
        },
        "lowmode": {
            "raw": lowmode_results, "summary": lowmode_summary,
            "n_comparisons": LOWMODE_N_COMPARISONS, "bonferroni_alpha": LOWMODE_ALPHA,
        },
    }
    with open(OUTPUT_DIR / "generalization_check.json", "w") as f:
        json.dump(out, f, indent=2)
    _log(f"\nwrote {OUTPUT_DIR / 'generalization_check.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
