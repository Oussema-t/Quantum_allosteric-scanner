#!/usr/bin/env python3
"""TASK-0189 -- corrected re-analysis of [[TASK-0167.003]]'s Part A
(`zero_plant_specificity.py`'s own collection output), mirroring
[[TASK-0167.002]]'s own precedent (`detection_curve_analysis.py`): a
separate analysis script recomputing certification from stored raw
`p_value` fields, not an edit to the already-run collection script.

**The bug** (finding F1, Reviewer thread 2026-08-03): `zero_plant_
specificity.py:154`'s `bonferroni_alpha = ALPHA / (len(STRENGTHS) *
N_SEEDS)` = `0.05 / (8 * 20)` = `3.125e-4` -- the exact wrong-family
constant `.002`'s own collection script also has (`positive_control_
detection_curve.py:236`) and that `.002`'s analysis script (this
script's own direct model) already corrects. `.003`'s collection script
copied the constant; unlike `.002`, no analysis-stage correction was
ever written, so the bug reached `.003`'s published Part A table.
Compounding: at that alpha, `gate4` needs `p_value < 3.125e-4`, but
`p_value = (null_maxes >= real_max).mean()` over `N_PERM_REPS=1000` (or
`MATCHED_N_PERM_REPS=200`) replicates has a smallest reachable non-zero
value of `1e-3` (`5e-3` for matched) -- both **larger** than the bar, so
`gate4` could only ever fire at `p_value == 0.0` exactly. The corrected
`REAL_BONFERRONI_ALPHA = 0.05/3 = 0.01667` (TASK-0145's own established
"correct across targets, not across a measurement device's own internal
replicate grid" convention, same value `.002`'s analysis script uses) is
comfortably above both reachable floors (1e-3, 5e-3) -- reachability
does not bind at the corrected alpha, confirmed below before trusting
the recomputed numbers, not assumed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.diagnostics import assert_gate_reachable  # noqa: E402

RESULTS_PATH = Path(__file__).resolve().parent.parent / "results/tasks/0167003_specificity" / "zero_plant_specificity_full.json"
NULL_SPECS = ["scattered", "compact", "matched"]

# Matches detection_curve_analysis.py's own REAL_DEPLOYMENT_BONFERRONI_FAMILY/
# REAL_BONFERRONI_ALPHA exactly -- same correction, same value, not re-derived.
REAL_DEPLOYMENT_BONFERRONI_FAMILY = 3
REAL_BONFERRONI_ALPHA = 0.05 / REAL_DEPLOYMENT_BONFERRONI_FAMILY

N_PERM_REPS = 1000
MATCHED_N_PERM_REPS = 200


def load(path: Path = RESULTS_PATH) -> dict:
    with open(path) as f:
        return json.load(f)


def _certified_corrected(cell: dict, null_spec: str) -> bool:
    """Recomputes certification from the cell's own raw gate1/gate2_seq/
    p_value fields under REAL_BONFERRONI_ALPHA -- NOT the collection
    script's own `nulls.<spec>.certified` field (that field used the
    wrong Bonferroni family size)."""
    gate1 = cell["gate1"]
    gate2 = cell["gate2_seq"]
    p_value = cell["nulls"][null_spec]["p_value"]
    gate4 = bool(np.isfinite(p_value) and p_value < REAL_BONFERRONI_ALPHA)
    return bool(gate1 and gate2 and gate4)


def alpha_hat_corrected(cells: list, null_spec: str) -> dict:
    n = len(cells)
    if n == 0:
        return {"n": 0, "k": 0, "p": float("nan"), "lo": float("nan"), "hi": float("nan")}
    k = sum(1 for c in cells if _certified_corrected(c, null_spec))
    result = binomtest(k, n)
    ci = result.proportion_ci(confidence_level=0.95, method="exact")
    return {"n": n, "k": k, "p": k / n, "lo": ci.low, "hi": ci.high}


def check_reachability() -> dict:
    """Explicit, printed confirmation that the corrected alpha is
    reachable given this collection run's own N_PERM_REPS/
    MATCHED_N_PERM_REPS -- per this task's own Planned Validation
    ("check reachability... before spending the compute" on a re-run).
    Uses the same guard `tests/test_diagnostics.py` demonstrates fails
    against the ORIGINAL (buggy) constants."""
    scattered_compact = assert_gate_reachable(
        REAL_BONFERRONI_ALPHA, REAL_DEPLOYMENT_BONFERRONI_FAMILY, N_PERM_REPS,
    )
    matched = assert_gate_reachable(
        REAL_BONFERRONI_ALPHA, REAL_DEPLOYMENT_BONFERRONI_FAMILY, MATCHED_N_PERM_REPS,
    )
    return {"scattered_compact_reachable": scattered_compact, "matched_reachable": matched}


def main() -> int:
    reach = check_reachability()
    print(f"Reachability at corrected alpha={REAL_BONFERRONI_ALPHA:.5f} "
          f"(family={REAL_DEPLOYMENT_BONFERRONI_FAMILY}): "
          f"scattered/compact (n_reps={N_PERM_REPS}) reachable={reach['scattered_compact_reachable']}, "
          f"matched (n_reps={MATCHED_N_PERM_REPS}) reachable={reach['matched_reachable']}")
    print("-> reachable at both n_reps -- no collection re-run needed, per this task's own Out-Of-Scope.\n")

    data = load()
    part_a = data["part_a"]

    corrected = {}
    print(f"{'Target':<16}{'Scattered a-hat (95% CI)':<28}{'Compact a-hat (95% CI)':<28}{'Matched a-hat (95% CI)'}")
    for target, target_data in part_a.items():
        cells = target_data["cells"]
        row = {spec: alpha_hat_corrected(cells, spec) for spec in NULL_SPECS}
        corrected[target] = row
        cols = []
        for spec in NULL_SPECS:
            r = row[spec]
            cols.append(f"{r['p']:.3f} [{r['lo']:.3f}, {r['hi']:.3f}]")
        print(f"{target:<16}{cols[0]:<28}{cols[1]:<28}{cols[2]}")

    out_path = Path(__file__).resolve().parent.parent / "results/tasks/0167003_specificity" / "part_a_corrected.json"
    with open(out_path, "w") as f:
        json.dump({
            "real_bonferroni_alpha": REAL_BONFERRONI_ALPHA,
            "real_deployment_bonferroni_family": REAL_DEPLOYMENT_BONFERRONI_FAMILY,
            "reachability": reach,
            "alpha_measured_corrected": corrected,
        }, f, indent=2)
    print(f"\nWritten: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
