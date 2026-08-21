#!/usr/bin/env python3
"""TASK-0120 -- learnability gate (HYP-P8): is the labeled pocket even
present in the apo topology?

`REVIEW-panel-2026-07-16-v2.md` Sec.6: "the highest information-per-hour
experiment available." For each mandatory target: Kabsch-superpose holo
onto apo, per-residue apo->holo Ca RMSD at the labeled pocket vs.
background, and Tama-Sanejouand cumulative overlap of the apo->holo
displacement onto the apo ANM's low-frequency modes -- classified via
`superpose.learnability_verdict`.

**TASK-0150, 2026-07-24: refactored to call `superpose.compute_
learnability` instead of duplicating this composition inline.** Real bug
fixed as a byproduct, not the point of the refactor: this script's own
former inline computation used the whole-structure `cumulative_overlap`
for `CO(20)`, not the pocket-restricted `restricted_cumulative_overlap`
[[TASK-0133]] built specifically because the whole-structure quantity
answers a different, easier question (confirmed directly -- `git log`
shows this file was never touched by TASK-0133 or TASK-0139, and
`restricted_cumulative_overlap`'s own docstring independently states
this file's old `CO(20)` was the whole-structure quantity). KRAS_G12C's
own reported verdict changes as a direct, real consequence -- see
`compute_learnability`'s own docstring and TASK-0150's Done section for
the full before/after numbers and why this differs from
`resolve_kras_learnability.py`'s own fully null-resolved `AMBIGUOUS`.
**Correction**: an earlier version of this docstring claimed the
previous (buggy) JSON output was snapshotted to a `.bak` file before
regenerating -- checked directly and found false (the intended backup
ran against an empty directory and silently no-opped; never verified).
No prior run's output was actually on disk to preserve; the superseded
numbers this refactor corrects are the ones already on record in
`RESULTS.md`'s own TASK-0120/TASK-0144 sections, which this refactor
does not touch.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from allostery.clean import load_target_config  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.superpose import compute_learnability  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo, not re-derived

DEFAULT_TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
DEFAULT_ANM_CUTOFF = 10.0
DEFAULT_N_MODES = 20
DEFAULT_POCKET_CUTOFF = 4.5
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0120"


def run_one(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))
    anm_cutoff = float(target_config.get("enm_cutoff", DEFAULT_ANM_CUTOFF))

    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")

    verdict = compute_learnability(
        apo, holo, target_config, labels_obj.pocket,
        anm_cutoff=anm_cutoff, n_modes=DEFAULT_N_MODES, rmsd_threshold=3.0,
    )

    result = {"target": target_name, "n_residues": len(apo.resnums), **verdict}
    co_final = verdict["co_final"]
    co_str = (
        f"CO({DEFAULT_N_MODES})={co_final:.3f}"
        if verdict["co_blocked_reason"] is None
        else "CO=BLOCKED(TASK-0128)"
    )
    print(
        f"{target_name}: N={result['n_residues']} pocket_rmsd={verdict['pocket_rmsd_mean']:.3f} "
        f"background_rmsd={verdict['background_rmsd_mean']:.3f} ratio={verdict['rmsd_ratio']:.2f} "
        f"{co_str} -> {verdict['verdict']}"
    )
    return result


def main(argv=None) -> int:
    # TASK-0152: --target/--output let a caller extend this gate past the
    # 3 mandatory targets (e.g. GLUCOKINASE, never previously included in
    # DEFAULT_TARGETS/this JSON's own output) without recomputing/
    # overwriting the mandatory-3 record by default -- ADD-only, defaults
    # reproduce this script's original behavior exactly when omitted.
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=DEFAULT_TARGETS)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "learnability_gate.json")
    args = parser.parse_args(argv)

    results = {}
    for target_name in args.target:
        try:
            results[target_name] = run_one(target_name)
        except Exception as exc:
            print(f"{target_name}: FAILED -- {exc!r}")
            results[target_name] = {"target": target_name, "error": str(exc)}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
