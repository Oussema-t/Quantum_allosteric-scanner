#!/usr/bin/env python3
"""TASK-0167.002 -- analysis pass over `positive_control_detection_curve.py`'s
own JSON output: P(certified) per (target x null-spec x CI-method x strength)
with a binomial (Clopper-Pearson) CI, LOD extraction (smallest strength with
P(certified) >= 0.80), per-gate failure profile, and the three-null
comparison this task's own Intent Contract asks for.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

RESULTS_PATH = Path(__file__).resolve().parent.parent / "results/tasks/0167002_detection_curve" / "detection_curve.json"
NULL_SPECS = ["scattered", "compact", "matched"]
CI_METHODS = ["sequence_ci", "spatial_ci"]
LOD_POWER = 0.80

# **Real bug, found and fixed here (not in the collection script -- see
# below), before trusting any "certified" number.** The collection
# script's own `gate4_clears_bonferroni`/`certified_*` fields divide
# alpha by `len(STRENGTHS)*N_SEEDS=160`, treating this measurement
# device's own synthetic strength/seed grid as if it were 160
# simultaneous real hypothesis tests. That is not what a real deployment
# does: a real single-target run of this observable corrects across
# TARGETS (TASK-0145's own established convention for `T(E=0)` on `L`,
# `N_TARGETS_FOR_BONFERRONI=3`), not across this script's own internal
# replicate count. Recomputed here from the raw, uncorrected `p_value`
# each cell already stores -- no need to re-run the (expensive) collection
# pass, only the Bonferroni denominator was wrong, not the p-values
# themselves.
REAL_DEPLOYMENT_BONFERRONI_FAMILY = 3  # matches TASK-0145's own convention
REAL_BONFERRONI_ALPHA = 0.05 / REAL_DEPLOYMENT_BONFERRONI_FAMILY


def load(path: Path = RESULTS_PATH) -> dict:
    with open(path) as f:
        return json.load(f)


def cells_by_strength(target_data: dict) -> dict:
    by_strength: dict = {}
    for key, cell in target_data["cells"].items():
        if "error" in cell:
            continue
        strength = cell["strength"]
        by_strength.setdefault(strength, []).append(cell)
    return by_strength


def _certified_corrected(cell: dict, null_spec: str, ci_method: str) -> bool:
    """Recomputes certification from the cell's own raw gate1/gate2/
    p_value fields under `REAL_BONFERRONI_ALPHA`, NOT the collection
    script's own `certified_*` field (see this module's own header note
    -- that field used the wrong Bonferroni family size)."""
    gate1 = cell["gate1_beats_floor"]
    gate2 = cell[f"gate2_{ci_method}"]
    p_value = cell["nulls"][null_spec]["p_value"]
    gate4 = bool(np.isfinite(p_value) and p_value < REAL_BONFERRONI_ALPHA)
    return bool(gate1 and gate2 and gate4)


def p_certified(cells: list, null_spec: str, ci_method: str) -> dict:
    n = len(cells)
    if n == 0:
        return {"n": 0, "p": float("nan"), "lo": float("nan"), "hi": float("nan")}
    k = sum(1 for c in cells if _certified_corrected(c, null_spec, ci_method))
    result = binomtest(k, n)
    ci = result.proportion_ci(confidence_level=0.95, method="exact")
    return {"n": n, "k": k, "p": k / n, "lo": ci.low, "hi": ci.high}


def gate_failure_profile(cells: list) -> dict:
    n = len(cells)
    if n == 0:
        return {}
    gate1_fail = sum(1 for c in cells if not c["gate1_beats_floor"])
    gate2_seq_fail = sum(1 for c in cells if c["gate1_beats_floor"] and not c["gate2_sequence_ci"])
    gate2_sp_fail = sum(1 for c in cells if c["gate1_beats_floor"] and not c["gate2_spatial_ci"])
    return {
        "n": n,
        "gate1_fail_frac": gate1_fail / n,
        "gate2_seq_fail_frac_given_gate1": gate2_seq_fail / max(1, n - gate1_fail),
        "gate2_sp_fail_frac_given_gate1": gate2_sp_fail / max(1, n - gate1_fail),
    }


def extract_lod(by_strength: dict, null_spec: str, ci_method: str) -> float:
    strengths = sorted(by_strength.keys())
    for s in strengths:
        stats = p_certified(by_strength[s], null_spec, ci_method)
        if stats["p"] >= LOD_POWER:
            return s
    return float("inf")


def main() -> int:
    data = load()
    lines = ["# TASK-0167.002 -- detection curve analysis\n"]

    for target_name, target_data in data.items():
        lines.append(f"\n## {target_name}\n")
        inv = target_data.get("invariance_check")
        if inv:
            lines.append(f"Invariance check (H_new/dcc_low/prs_low): {inv}\n")

        by_strength = cells_by_strength(target_data)
        n_cells = sum(len(v) for v in by_strength.values())
        lines.append(f"Cells computed: {n_cells}\n")

        lines.append("\n### Gate failure profile per strength\n")
        lines.append("| Strength | n | gate1 fail | gate2(seq) fail\\|gate1 | gate2(sp) fail\\|gate1 |")
        lines.append("|---|---|---|---|---|")
        for s in sorted(by_strength.keys()):
            prof = gate_failure_profile(by_strength[s])
            if not prof:
                continue
            lines.append(
                f"| {s} | {prof['n']} | {prof['gate1_fail_frac']:.2f} | "
                f"{prof['gate2_seq_fail_frac_given_gate1']:.2f} | {prof['gate2_sp_fail_frac_given_gate1']:.2f} |"
            )

        lines.append("\n### P(certified) per null spec x CI method\n")
        for ci_method in CI_METHODS:
            lines.append(f"\n**CI method: {ci_method}**\n")
            lines.append("| Strength | " + " | ".join(NULL_SPECS) + " |")
            lines.append("|---|" + "---|" * len(NULL_SPECS))
            for s in sorted(by_strength.keys()):
                row = [str(s)]
                for null_spec in NULL_SPECS:
                    stats = p_certified(by_strength[s], null_spec, ci_method)
                    row.append(f"{stats['p']:.2f} [{stats['lo']:.2f},{stats['hi']:.2f}] (n={stats['n']})")
                lines.append("| " + " | ".join(row) + " |")

        lines.append("\n### LOD (smallest strength with P(certified) >= 0.80)\n")
        lines.append("| CI method | " + " | ".join(NULL_SPECS) + " |")
        lines.append("|---|" + "---|" * len(NULL_SPECS))
        for ci_method in CI_METHODS:
            row = [ci_method]
            for null_spec in NULL_SPECS:
                lod = extract_lod(by_strength, null_spec, ci_method)
                row.append(str(lod))
            lines.append("| " + " | ".join(row) + " |")

    out_text = "\n".join(lines)
    out_path = RESULTS_PATH.parent / "analysis_summary.md"
    with open(out_path, "w") as f:
        f.write(out_text)
    print(out_text)
    print(f"\nwrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
