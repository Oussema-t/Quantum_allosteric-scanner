#!/usr/bin/env python3
"""TASK-0133 -- learnability gate control: does a random same-sized patch
also score high on cumulative overlap?

[[TASK-0120]]'s `learnability_verdict` requires pocket RMSD >= 1.5x
background AND CO(20) < 0.5 to call a target `UNLEARNABLE_FROM_APO`. This
script tests whether the CO half of that conjunction actually
discriminates "spans *this pocket's* displacement" from "spans *any*
same-sized displacement" -- by comparing the real pocket's own
region-restricted CO(20) (`superpose.restricted_cumulative_overlap`,
new this task) against a distribution built from many random same-sized
patches drawn from the same common apo/holo correspondence set.

**Real finding, checked directly before writing this script (see
`restricted_cumulative_overlap`'s own docstring)**: TASK-0120's reported
`CO(20)` (0.638/0.794/0.584) is a *whole-structure* quantity -- computed
over the entire common correspondence set (166-709 residues depending on
target), not the pocket specifically. It is reported here too, alongside
the new pocket-restricted number, so both are on record and clearly
distinguished.
"""
from __future__ import annotations

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

from allostery.clean import load_target_config  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.superpose import (  # noqa: E402
    align_apo_holo,
    anm_modes,
    cumulative_overlap,
    restricted_cumulative_overlap,
)

import run_challenge  # noqa: E402 -- reuse _load_apo_holo, not re-derived

DEFAULT_TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
DEFAULT_ANM_CUTOFF = 10.0
DEFAULT_N_MODES = 20
DEFAULT_POCKET_CUTOFF = 4.5
N_REPLICATES = 1000
SEED = 7
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0133"


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run_one(target_name: str, n_replicates: int, seed: int) -> dict:
    target_config = load_target_config(target_name)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))
    anm_cutoff = float(target_config.get("enm_cutoff", DEFAULT_ANM_CUTOFF))

    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")

    alignment = align_apo_holo(apo, holo)
    eigvals, eigvecs = anm_modes(apo.coords, cutoff=anm_cutoff, n_modes=DEFAULT_N_MODES)

    # Real pocket, restricted to residues with a holo correspondence --
    # same "measurable" restriction cryptic_openness_gate/background_rmsd
    # already use (TASK-0120's own convention, reused not reinvented).
    in_common = np.zeros(len(labels_obj.pocket), dtype=bool)
    in_common[alignment.apo_idx] = True
    measurable_pocket = np.where(labels_obj.pocket & in_common)[0]
    n_unmeasurable = int((labels_obj.pocket & ~in_common).sum())
    if len(measurable_pocket) == 0:
        raise RuntimeError(f"{target_name}: no measurable pocket residues in the common set")

    pocket_co_curve = restricted_cumulative_overlap(apo, alignment, eigvecs, measurable_pocket)
    pocket_co20 = float(pocket_co_curve[-1])

    # TASK-0120's own whole-structure CO(20), for direct reference --
    # a *different* quantity (see module docstring), reported not to
    # duplicate this task's own headline but so both are visible together.
    whole_delta_r = (
        alignment.aligned_holo_coords[alignment.holo_idx] - apo.coords[alignment.apo_idx]
    ).ravel()
    whole_co_curve = cumulative_overlap(whole_delta_r, eigvecs, alignment.apo_idx)
    whole_co20 = float(whole_co_curve[-1])

    # Random same-sized patches, drawn from the full common correspondence
    # set (TASK-0133's own Constraint) -- may overlap the real pocket,
    # same permutation-style convention TASK-0131 already established for
    # this project's other null-distribution work.
    rng = np.random.default_rng(seed)
    patch_size = len(measurable_pocket)
    patch_co20 = np.empty(n_replicates)
    for i in range(n_replicates):
        patch = rng.choice(alignment.apo_idx, size=patch_size, replace=False)
        co_curve = restricted_cumulative_overlap(apo, alignment, eigvecs, patch)
        patch_co20[i] = co_curve[-1]

    percentile = float((patch_co20 < pocket_co20).mean() * 100.0)

    result = {
        "target": target_name,
        "n_common_correspondence": int(len(alignment.apo_idx)),
        "n_pocket_residues": int(labels_obj.pocket.sum()),
        "n_pocket_measurable": int(len(measurable_pocket)),
        "n_pocket_unmeasurable": n_unmeasurable,
        "patch_size": int(patch_size),
        "n_replicates": n_replicates,
        "seed": seed,
        "pocket_co20_restricted": pocket_co20,
        "whole_structure_co20_task0120": whole_co20,
        "patch_co20_mean": float(patch_co20.mean()),
        "patch_co20_std": float(patch_co20.std()),
        "patch_co20_min": float(patch_co20.min()),
        "patch_co20_max": float(patch_co20.max()),
        "patch_co20_percentiles": {
            str(p): float(np.percentile(patch_co20, p)) for p in (5, 25, 50, 75, 95)
        },
        "pocket_percentile_within_patch_distribution": percentile,
    }
    _log(
        f"{target_name}: pocket_co20(restricted)={pocket_co20:.3f} "
        f"whole_structure_co20(TASK-0120)={whole_co20:.3f} "
        f"patch_co20={patch_co20.mean():.3f}+/-{patch_co20.std():.3f} "
        f"(n={n_replicates}, patch_size={patch_size}) "
        f"-> pocket at {percentile:.1f}th percentile of random-patch distribution"
    )
    return result


def main() -> int:
    results = {}
    for target_name in DEFAULT_TARGETS:
        try:
            results[target_name] = run_one(target_name, N_REPLICATES, SEED)
        except Exception as exc:
            _log(f"{target_name}: FAILED -- {exc!r}")
            results[target_name] = {"target": target_name, "error": str(exc)}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "learnability_gate_patch_control.json", "w") as f:
        json.dump(results, f, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
