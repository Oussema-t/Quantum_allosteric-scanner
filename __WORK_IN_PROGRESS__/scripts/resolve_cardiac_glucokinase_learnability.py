#!/usr/bin/env python3
"""TASK-0152 -- resolve CARDIAC_MYOSIN(8QYP)/GLUCOKINASE's learnability
classification with the same matched-null rigor [[TASK-0133]]/[[TASK-0139]]
already applied to KRAS_G12C.

Unlike `resolve_kras_learnability.py` (which compared a whole-structure CO
against a pocket-restricted one -- a real bug [[TASK-0150]] fixed), both
inputs here already use the correct, pocket-restricted `restricted_
cumulative_overlap` (`scripts/learnability_gate.py` post-TASK-0150 for the
bare-threshold verdict; `scripts/learnability_gate_patch_control.py`,
never buggy, for the null). The comparison this script makes is therefore
narrower and more direct: bare-threshold verdict (no null) vs.
null-informed verdict (`co_percentile` supplied) -- does not recompute
anything expensive, loads the two already-real JSON results and reruns
`learnability_verdict` on them.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.superpose import learnability_verdict  # noqa: E402

_RESULTS_DIR = Path(__file__).resolve().parent.parent / "RESULTS"
GATE_PATH = _RESULTS_DIR / "results_task0120" / "learnability_gate.json"
PATCH_CONTROL_PATH = _RESULTS_DIR / "results_task0152" / "learnability_gate_patch_control_task0152.json"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "results_task0152_learnability_resolution" / "resolution.json"

TARGETS = ["CARDIAC_MYOSIN", "GLUCOKINASE"]


def resolve_target(target_name: str, gate: dict, patch: dict) -> dict:
    pocket_rmsd_mean = gate["pocket_rmsd_mean"]
    background_rmsd_mean = gate["background_rmsd_mean"]
    co_restricted = gate["co_final"]  # already pocket-restricted, post-TASK-0150
    co_percentile = patch["pocket_percentile_within_patch_distribution"] / 100.0

    bare_threshold = learnability_verdict(
        pocket_rmsd_mean=pocket_rmsd_mean,
        background_rmsd_mean=background_rmsd_mean,
        co_final=co_restricted,
    )
    null_informed = learnability_verdict(
        pocket_rmsd_mean=pocket_rmsd_mean,
        background_rmsd_mean=background_rmsd_mean,
        co_final=co_restricted,
        co_percentile=co_percentile,
    )
    one_sided_p = min(co_percentile, 1.0 - co_percentile)

    return {
        "target": target_name,
        "pocket_rmsd_mean": pocket_rmsd_mean,
        "background_rmsd_mean": background_rmsd_mean,
        "rmsd_ratio": bare_threshold["rmsd_ratio"],
        "rmsd_much_greater": bare_threshold["rmsd_much_greater"],
        "pocket_restricted_co20": co_restricted,
        "co_percentile_within_random_patch_null": co_percentile,
        "one_sided_p": one_sided_p,
        "bare_threshold_verdict": bare_threshold["verdict"],
        "null_informed_verdict": null_informed["verdict"],
        "verdict_changed": bare_threshold["verdict"] != null_informed["verdict"],
        "resolution_depends_on_co_at_all": bare_threshold["rmsd_much_greater"],
    }


def main() -> int:
    gate_all = json.loads(GATE_PATH.read_text())
    patch_all = json.loads(PATCH_CONTROL_PATH.read_text())

    results = {}
    for target_name in TARGETS:
        results[target_name] = resolve_target(target_name, gate_all[target_name], patch_all[target_name])
        r = results[target_name]
        print(
            f"{target_name}: rmsd_ratio={r['rmsd_ratio']:.2f} rmsd_much_greater={r['rmsd_much_greater']} "
            f"restricted_co={r['pocket_restricted_co20']:.3f} "
            f"percentile={r['co_percentile_within_random_patch_null']*100:.1f}th "
            f"(one-sided p={r['one_sided_p']:.3f}) -- "
            f"bare-threshold={r['bare_threshold_verdict']} -> null-informed={r['null_informed_verdict']} "
            f"(changed={r['verdict_changed']}, CO-half matters={r['resolution_depends_on_co_at_all']})"
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(results, indent=2))
    print(f"\nwrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
