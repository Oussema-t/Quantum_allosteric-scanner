#!/usr/bin/env python3
"""TASK-0139 -- resolve KRAS_G12C's learnability classification.

TASK-0120's whole-structure `learnability_gate.py` and TASK-0133's
pocket-restricted `learnability_gate_patch_control.py` produced
genuinely conflicting inputs for the same conjunction (whole-structure
CO(20)=0.638 -> LEARNABLE; pocket-restricted CO(20)=0.458 -> the RMSD
half still clears but the CO half flips below `co_threshold=0.5`).
TASK-0139's own resolution (see its Done section for the full
first-principles argument): the pocket-restricted quantity is the
correct one for this conjunction (the RMSD half is already pocket-vs-
background, i.e. region-specific by design -- a whole-structure CO
answers a different, easier question than the panel's own kill
criterion asks), and `co_threshold=0.5` was never itself validated
against any null (whole-structure or restricted) -- once a real
random-patch null exists for a target (TASK-0133), testing against it
directly (`superpose.learnability_verdict`'s new `co_percentile`
parameter) is the more principled criterion than the un-derived bare
threshold.

This script does not recompute anything expensive -- it loads the two
already-real, already-verified JSON results TASK-0120/0133 produced
and reruns them through the corrected `learnability_verdict` call,
confirming programmatically (not by hand-transcription) that:
  (a) KRAS_G12C resolves to AMBIGUOUS under the corrected criterion.
  (b) BCR_ABL1/CARDIAC_MYOSIN are unaffected (RMSD-determined,
      independent of which CO quantity or criterion is used).
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
GATE_PATH = _RESULTS_DIR / "results/tasks/0120" / "learnability_gate.json"
PATCH_CONTROL_PATH = _RESULTS_DIR / "results/tasks/0133" / "learnability_gate_patch_control.json"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "results/tasks/0139_learnability_resolution" / "resolution.json"


def resolve_target(target_name: str, gate: dict, patch: dict) -> dict:
    pocket_rmsd_mean = gate["pocket_rmsd_mean"]
    background_rmsd_mean = gate["background_rmsd_mean"]
    co_restricted = patch["pocket_co20_restricted"]
    co_percentile = patch["pocket_percentile_within_patch_distribution"] / 100.0

    original_whole_structure = learnability_verdict(
        pocket_rmsd_mean=pocket_rmsd_mean,
        background_rmsd_mean=background_rmsd_mean,
        co_final=gate["co_final"],  # whole-structure, TASK-0120's own
    )
    corrected = learnability_verdict(
        pocket_rmsd_mean=pocket_rmsd_mean,
        background_rmsd_mean=background_rmsd_mean,
        co_final=co_restricted,
        co_percentile=co_percentile,
    )

    return {
        "target": target_name,
        "pocket_rmsd_mean": pocket_rmsd_mean,
        "background_rmsd_mean": background_rmsd_mean,
        "rmsd_ratio": corrected["rmsd_ratio"],
        "rmsd_much_greater": corrected["rmsd_much_greater"],
        "whole_structure_co20": gate["co_final"],
        "pocket_restricted_co20": co_restricted,
        "co_percentile_within_random_patch_null": co_percentile,
        "original_verdict_whole_structure_co": original_whole_structure["verdict"],
        "resolved_verdict_pocket_restricted_co_with_null": corrected["verdict"],
        "verdict_changed": original_whole_structure["verdict"] != corrected["verdict"],
        "resolution_depends_on_co_at_all": corrected["rmsd_much_greater"],
    }


def main() -> int:
    gate_all = json.loads(GATE_PATH.read_text())
    patch_all = json.loads(PATCH_CONTROL_PATH.read_text())

    results = {}
    for target_name in ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]:
        results[target_name] = resolve_target(target_name, gate_all[target_name], patch_all[target_name])
        r = results[target_name]
        print(
            f"{target_name}: rmsd_ratio={r['rmsd_ratio']:.2f} rmsd_much_greater={r['rmsd_much_greater']} "
            f"whole_structure_co={r['whole_structure_co20']:.3f} restricted_co={r['pocket_restricted_co20']:.3f} "
            f"percentile={r['co_percentile_within_random_patch_null']*100:.1f}th -- "
            f"original={r['original_verdict_whole_structure_co']} -> resolved={r['resolved_verdict_pocket_restricted_co_with_null']} "
            f"(changed={r['verdict_changed']}, CO-half matters={r['resolution_depends_on_co_at_all']})"
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(results, indent=2))
    print(f"\nwrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
