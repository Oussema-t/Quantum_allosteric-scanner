#!/usr/bin/env python3
"""TASK-0229.007(a) -- two-state ANM capture score (ref [15], Das et al.
2014), a graded, continuous instrument for what TASK-0209 measures as a
binary VALID/INVALID verdict. Extends TASK-0227's own whole-structure
cumulative-overlap measurement (which already covered KRAS_G12C, BCR_ABL1,
CARDIAC_MYOSIN with an external harness at cutoff=15A) to all 7 of
TASK-0209's own real-drug-ligand targets, recomputed fresh with THIS
project's own internal, already-validated `superpose.py` machinery
(`anm_modes`/`cumulative_overlap`, cutoff=10.0A, this module's own
established default) so all 7 numbers are on one consistent basis --
mixing TASK-0227's external-harness numbers with new internal-library
numbers would not be a fair graded comparison across the full set.

Planned Validation (this task's own): KRAS_G12C must rank above BCR_ABL1,
reproducing TASK-0209's own VALID/INVALID ordering -- or the instrument
disagrees with the finding it was built to quantify.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    import os
    os.environ.setdefault(_v, "4")

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
_SCRIPTS = Path(__file__).resolve().parent
for _p in (_SRC, _SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from allostery.clean import load_target_config  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.superpose import (  # noqa: E402
    align_apo_holo, anm_modes, chain_map_from_config, cumulative_overlap, restricted_cumulative_overlap,
)

import run_challenge  # noqa: E402

# TASK-0209's own 7 real-drug-ligand targets, VALID/INVALID per its own
# verdict table (reused as the label this instrument is checked against,
# not re-derived).
TASK_0209_VERDICT = {
    "KRAS_G12C": "VALID", "PTP1B": "VALID",
    "BCR_ABL1": "INVALID", "GLUCOKINASE": "INVALID", "CASPASE1": "INVALID",
    "CARDIAC_MYOSIN": "INVALID", "CASPASE7": "INVALID",
}
DEFAULT_ANM_CUTOFF = 10.0
N_MODES = 50


def run_one(name: str) -> dict:
    target_config = load_target_config(name)
    apo, holo = run_challenge._load_apo_holo(name, target_config)
    alignment = align_apo_holo(apo, holo, chain_map=chain_map_from_config(target_config))
    apo_idx, holo_idx = alignment.apo_idx, alignment.holo_idx
    delta_r = (alignment.aligned_holo_coords[holo_idx] - apo.coords[apo_idx]).ravel()

    anm_cutoff = float(target_config.get("enm_cutoff", DEFAULT_ANM_CUTOFF))
    _eigvals, eigvecs = anm_modes(apo.coords, cutoff=anm_cutoff, n_modes=N_MODES)
    co = cumulative_overlap(delta_r, eigvecs, apo_idx)
    co_final = float(co[-1]) if len(co) else float("nan")
    co_k20 = float(co[19]) if len(co) > 19 else float("nan")

    # Pocket-restricted variant, TASK-0209's own window-specific question
    # rather than the whole-structure deformation -- Bessel-valid form,
    # TASK-0133, not the whole-structure cumulative_overlap's own
    # renormalized-slice approach (invalid for a small subset).
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", 4.5))
    co_pocket_final = float("nan")
    try:
        labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
        if labels_obj.pocket is not None and labels_obj.pocket.any():
            in_common = np.zeros(len(labels_obj.pocket), dtype=bool)
            in_common[apo_idx] = True
            pocket_idx = np.where(labels_obj.pocket & in_common)[0]
            if len(pocket_idx):
                co_pocket = restricted_cumulative_overlap(apo, alignment, eigvecs, pocket_idx)
                co_pocket_final = float(co_pocket[-1]) if len(co_pocket) else float("nan")
    except Exception as exc:  # noqa: BLE001
        print(f"  {name}: pocket-restricted CO failed: {exc!r}")

    return {
        "target": name, "n_common_residues": int(len(apo_idx)),
        "co_k20": round(co_k20, 4), "co_k50": round(co_final, 4),
        "co_pocket_restricted_k50": round(co_pocket_final, 4) if np.isfinite(co_pocket_final) else None,
        "task_0209_verdict": TASK_0209_VERDICT[name],
    }


def main() -> int:
    results = {}
    for name in TASK_0209_VERDICT:
        t0 = time.monotonic()
        try:
            results[name] = run_one(name)
            print(f"{name}: CO(20)={results[name]['co_k20']:.4f} CO(50)={results[name]['co_k50']:.4f} "
                  f"pocket-CO(50)={results[name]['co_pocket_restricted_k50']} "
                  f"[{results[name]['task_0209_verdict']}] ({time.monotonic()-t0:.1f}s)")
        except Exception as exc:
            import traceback
            traceback.print_exc()
            results[name] = {"target": name, "error": str(exc), "task_0209_verdict": TASK_0209_VERDICT[name]}

    valid_co = [r["co_k50"] for r in results.values() if "error" not in r and r["task_0209_verdict"] == "VALID"]
    invalid_co = [r["co_k50"] for r in results.values() if "error" not in r and r["task_0209_verdict"] == "INVALID"]
    kras_co = results.get("KRAS_G12C", {}).get("co_k50")
    bcr_co = results.get("BCR_ABL1", {}).get("co_k50")
    planned_validation_pass = bool(kras_co is not None and bcr_co is not None and kras_co > bcr_co)

    kras_pco = results.get("KRAS_G12C", {}).get("co_pocket_restricted_k50")
    bcr_pco = results.get("BCR_ABL1", {}).get("co_pocket_restricted_k50")
    planned_validation_pass_pocket = bool(kras_pco is not None and bcr_pco is not None and kras_pco > bcr_pco)

    print(f"\nVALID targets CO(50): {valid_co}")
    print(f"INVALID targets CO(50): {invalid_co}")
    print(f"Planned Validation, whole-structure (KRAS_G12C CO(50) > BCR_ABL1 CO(50)): {planned_validation_pass}")
    print(f"Planned Validation, pocket-restricted (KRAS_G12C > BCR_ABL1): {planned_validation_pass_pocket}")

    out_dir = Path(__file__).resolve().parent.parent / "results/tasks/0229.007"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "two_state_anm_capture.json", "w") as f:
        json.dump({
            "per_target": results, "planned_validation_pass": planned_validation_pass,
            "planned_validation_pass_pocket_restricted": planned_validation_pass_pocket,
        }, f, indent=2)
    print(f"wrote {out_dir / 'two_state_anm_capture.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
