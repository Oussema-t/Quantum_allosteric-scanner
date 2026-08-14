"""TASK-0083 -- produce one real reference artifact for KRAS_G12C from
`run_challenge.py`'s own already-real output (Planned Validation: "a
reference artifact produced by TASK-0079 for one target, validated
against this task's schema"). Does not recompute anything -- reads the
existing `verdict.json`/`hit_list.json`/`connectivity_matrix.npz` a real
`run_target()` call already wrote, and repackages them into
`artifact_v1.json`/`connectivity_v1.npz`, per RESULT_ARTIFACT_CONTRACT.md.

Usage: python3 task0083_write_reference_artifact.py <run_challenge_output_dir> <out_dir>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import numpy as np  # noqa: E402

from allostery.artifact import write_result_artifact  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402

TARGET = "KRAS_G12C"

# COMPETENCE_MAP.md's own current headline table ("Mandatory targets --
# floor / ceiling / actual / headroom", TASK-0130 recompute) -- floor and
# ceiling are NOT part of run_challenge.py's own output (a separate
# ceiling-search process, TASK-0046, never re-run by this script), so
# read directly from that document rather than invented or left blank.
# "actual" below is deliberately THIS run's own fresh AUC_apo_Hnew_
# optimised, not COMPETENCE_MAP.md's own (slightly different, from an
# earlier run) point estimate -- headroom is recomputed from the two
# real numbers actually in hand, not copied, per this project's own
# "cite the source, don't silently reuse a stale point estimate"
# convention.
COMPETENCE_MAP_FLOOR = 0.4818
COMPETENCE_MAP_CEILING = 0.6288


def main() -> int:
    run_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/task0083_reference_run")
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else _ROOT / "results"

    target_dir = run_dir / TARGET
    verdict = json.loads((target_dir / "verdict.json").read_text())
    hits = json.loads((target_dir / "hit_list.json").read_text())
    conn = np.load(target_dir / "connectivity_matrix.npz")

    # Split run_challenge.py's own flat verdict.json into this contract's
    # verdict / diagnosis / metadata sections -- every value read, none
    # recomputed.
    verdict_block = {
        k: v for k, v in verdict.items()
        if not k.startswith("_") and k != "AUC_holo_Hnew_optimised"
    }
    diagnosis_block = {
        "category": verdict.get("_diagnosis"),
        "score_ci": verdict.get("_diagnosis_score_ci"),
        "floor_ci": verdict.get("_diagnosis_floor_ci"),
        "ci_overlap": verdict.get("_diagnosis_ci_overlap"),
    }
    hit_list_block = {
        "indices": hits["indices"],
        "resnums": hits["resnums"],
        "scores": hits["scores"],
    }
    stability_gate_block = {
        "source": "site_knob_sweep",
        **hits["sites"]["knob_spread"],
    }

    actual = verdict_block.get("AUC_apo_Hnew_optimised")
    floor, ceiling = COMPETENCE_MAP_FLOOR, COMPETENCE_MAP_CEILING
    if actual is not None and ceiling > floor:
        headroom, headroom_reason = (actual - floor) / (ceiling - floor), None
    else:
        headroom, headroom_reason = None, "ceiling <= floor or actual unavailable"
    competence_block = {
        "floor": floor, "ceiling": ceiling, "actual": actual,
        "headroom": headroom, "headroom_reason": headroom_reason,
    }

    cfg = load_target_config(TARGET)
    metadata_block = {
        "apo_pdb": cfg.get("apo_pdb"), "holo_pdb": cfg.get("holo_pdb"),
        "n_residues": int(conn["matrix"].shape[0]),
    }

    body = write_result_artifact(
        TARGET,
        out_dir=out_dir,
        verdict=verdict_block,
        diagnosis=diagnosis_block,
        hit_list=hit_list_block,
        connectivity_matrix=conn["matrix"],  # real-output key "matrix" -> contract key "M"
        stability_gate=stability_gate_block,
        competence=competence_block,
        metadata=metadata_block,
        pipeline_mode="frozen",
        frozen_verified=verdict.get("_frozen_stamp") is not None,
    )
    print(f"wrote {out_dir / TARGET / 'artifact_v1.json'}")
    print(json.dumps({k: v for k, v in body.items() if k not in ("verdict", "hit_list")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
