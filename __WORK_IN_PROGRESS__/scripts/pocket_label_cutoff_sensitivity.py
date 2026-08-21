#!/usr/bin/env python3
"""TASK-0114 -- pocket-label ligand-contact cutoff (`holo_pocket_mask`'s
`cutoff`, default 4.5 A) sensitivity sweep.

This is a *different* 4.5 A cutoff from the GNM graph cutoff TASK-0067/
TASK-0113 already characterized -- this one defines the ground-truth
label itself (which residues count as "pocket" at all), not the
operator. TASK-0075 already proved this project's other threshold gate
(cumulative-overlap go/no-go) is knob-unstable (0.067-0.860 across an
18-combo grid, 15/18 verdict flips) -- this task checks whether the
label-definition cutoff has the same property. If it does, every
headline AUC's own denominator (which residues are "true pocket") is
itself an unreported knob choice.

Only the label changes across the grid -- `H_new` and its `time_
averaged_ctqw_converged` occupation (TASK-0130's closed form, the
actual current procedure behind every other headline number in this
repo) are each computed exactly once per target and reused for every
cutoff, per this task's own In Scope ("no need to recompute the
operator itself, only the label/mask"). The proximity-floor baseline
score vectors (`degree_centrality`/`euclid_from_seed_centroid`/
`hop_from_seed`) are cutoff-independent too (they never read the pocket
label) and are likewise computed once and re-scored per cutoff.

No CI/permutation-null layer here -- this task's own question is
whether the label choice itself moves the verdict, a point-estimate
sensitivity sweep; statistical precision on any single cutoff's number
is a separate, already-covered concern (TASK-0112/0131).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
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

from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.diagnostics import classify_failure  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.labels import build_labels, holo_pocket_mask  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo/DEFAULT_CUTOFF

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0114_pocket_cutoff_sensitivity"
TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
CUTOFF_GRID = [4.0, 4.5, 5.0, 5.5]

# TASK-0047's own pinned fixture (test_labels.py's real-target check):
# backend/systems.py SYSTEMS["KRAS_G12C"]["pocket_full"][4.5], the raw
# (pre-exclusion) heavy-atom-contact set at the default 4.5 A cutoff.
KRAS_G12C_PINNED_4_5A = {9, 10, 11, 12, 13, 16, 34, 58, 59, 60, 61, 62, 63,
                          68, 69, 72, 95, 96, 99, 100, 103}


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run_target(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    enm_cutoff = float(target_config.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))

    _log(f"{target_name}: fetching + cleaning apo/holo...")
    apo, holo = run_challenge._load_apo_holo(target_name, target_config)

    # Active site (the CTQW seed) does not depend on the pocket-label
    # cutoff at all (a separate, UniProt-derived definition) -- computed
    # once via a throwaway build_labels call at the default cutoff, then
    # reused unchanged across the whole grid.
    from allostery.labels import build_labels as _bl
    reference_labels = _bl(apo, holo, target_config, cutoff=4.5)
    source = np.sort(np.where(reference_labels.active_site)[0])
    if len(source) == 0:
        raise RuntimeError(f"{target_name}: empty active-site seed")

    _log(f"{target_name}: N={len(apo.resnums)} n_seed={len(source)} -- building H_new + occupation once...")
    H_new = build_H_new(apo.coords, apo.bfactors, cutoff=enm_cutoff)
    occ = time_averaged_ctqw_converged(H_new, source=source, coherent=False)

    floor_candidates = [
        degree_centrality(apo.coords, cutoff=enm_cutoff),
        euclid_from_seed_centroid(apo.coords, source),
        hop_from_seed(apo.coords, source, cutoff=enm_cutoff),
    ]

    rows = []
    raw_pocket_sets = {}
    for cutoff in CUTOFF_GRID:
        labels_obj = build_labels(apo, holo, target_config, cutoff=cutoff)
        if labels_obj.pocket is None or not labels_obj.pocket.any():
            rows.append({"cutoff": cutoff, "error": "no resolvable pocket at this cutoff"})
            continue
        pocket_int = labels_obj.pocket.astype(int)
        n_pocket = int(pocket_int.sum())

        auc_h_new = _auc(occ, pocket_int)
        floor_aucs = [_auc(f, pocket_int) for f in floor_candidates]
        floor = float(max(floor_aucs))
        diagnosis = classify_failure(occ, labels_obj.pocket, H=H_new, bfactors=apo.bfactors, floor_scores=floor_candidates)

        rows.append({
            "cutoff": cutoff,
            "n_pocket_residues": n_pocket,
            "auc_h_new": float(auc_h_new),
            "floor": floor,
            "floor_cleared": bool(not np.isnan(auc_h_new) and auc_h_new > floor),
            "diagnosis": diagnosis,
        })
        _log(
            f"{target_name} cutoff={cutoff}A: n_pocket={n_pocket} auc={auc_h_new:.4f} "
            f"floor={floor:.4f} floor_cleared={not np.isnan(auc_h_new) and auc_h_new > floor} "
            f"diagnosis={diagnosis}"
        )

        # Raw (pre-exclusion) ligand-contact set, for the TASK-0047
        # cliff cross-check below -- KRAS_G12C only, but computed
        # generically in case useful for the other two targets too.
        drug_ligand = target_config.get("drug_ligand")
        if drug_ligand:
            raw_mask = holo_pocket_mask(apo, holo, drug_ligand, cutoff=cutoff)
            if raw_mask is not None:
                raw_pocket_sets[str(cutoff)] = sorted(int(r) for r in apo.resnums[raw_mask])

    verdict_changes = len({r["floor_cleared"] for r in rows if "error" not in r}) > 1
    diag_changes = len({r["diagnosis"] for r in rows if "error" not in r}) > 1

    return {
        "target": target_name,
        "n_residues": len(apo.resnums),
        "rows": rows,
        "raw_pocket_sets_by_cutoff": raw_pocket_sets,
        "floor_cleared_changes_across_grid": verdict_changes,
        "diagnosis_changes_across_grid": diag_changes,
    }


def cross_check_task0047_cliff(kras_result: dict) -> dict:
    raw_sets = kras_result.get("raw_pocket_sets_by_cutoff", {})
    pinned = KRAS_G12C_PINNED_4_5A
    result = {}
    for cutoff_str, resnums in raw_sets.items():
        s = set(resnums)
        result[cutoff_str] = {
            "n_residues": len(s),
            "matches_pinned_4_5a_exactly": s == pinned,
            "missing_vs_4_5a": sorted(pinned - s),
            "extra_vs_4_5a": sorted(s - pinned),
        }
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=TARGETS)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "pocket_label_cutoff_sensitivity.json")
    args = parser.parse_args(argv)

    all_results = {}
    for name in args.target:
        try:
            all_results[name] = run_target(name)
        except Exception as exc:
            all_results[name] = {"error": str(exc)}
            _log(f"{name}: FAILED -- {exc!r}")

    if "KRAS_G12C" in all_results and "error" not in all_results["KRAS_G12C"]:
        cliff_check = cross_check_task0047_cliff(all_results["KRAS_G12C"])
        all_results["KRAS_G12C"]["task0047_cliff_check"] = cliff_check
        for cutoff_str, stats in cliff_check.items():
            _log(f"KRAS_G12C TASK-0047 cliff check @ {cutoff_str}A: {stats}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(all_results, f, indent=2)
    _log(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
