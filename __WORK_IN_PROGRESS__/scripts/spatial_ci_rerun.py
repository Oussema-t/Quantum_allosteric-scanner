#!/usr/bin/env python3
"""TASK-0165 -- recompute CIs for the program's currently-surviving/
near-surviving positives under `metrics.spatial_block_bootstrap_ci`,
side by side with the original sequence-block CI (additive; the
original numbers already in `results_task0145_transport/` are not
overwritten).

Scope, per this task's own Out Of Scope ("focus on the currently-
reported positives/near-positives, not the full negative catalogue"):
`grep -rl '"ci_overlap": false' results_task*/*.json` found NO cell
anywhere in the project with a non-overlapping CI already -- every
observable's own bootstrap CI has always overlapped its floor's CI.
The "surviving/near-surviving" set is therefore read as: cells whose
`classify_failure` category is `NO_FAILURE_DETECTED` (point estimate +
permutation-null clear the floor) even though their CI already
overlaps -- TASK-0145's own BCR_ABL1 transport family (the one
Bonferroni-surviving permutation-null result [[TASK-0158]] flagged as
evaluated-but-not-re-run) plus the two other `NO_FAILURE_DETECTED`
transport cells (KRAS_G12C, PTP1B on H_new) for completeness.
"""
from __future__ import annotations

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

from allostery.metrics import auc as _auc
from allostery.metrics import block_bootstrap_ci, spatial_block_bootstrap_ci

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0165_spatial_ci"

CELLS = [
    ("BCR_ABL1", "effective_resistance"),
    ("BCR_ABL1", "transmission_on_L_E0"),
    ("BCR_ABL1", "transmission_on_H_new_E0"),
    ("KRAS_G12C", "transmission_on_H_new_E0"),
    ("PTP1B", "transmission_on_H_new_E0"),
]


def _log(msg: str) -> None:
    print(msg, flush=True)


def main() -> int:
    results = {}

    # `transport_observable_real_run._prepare_target` doesn't return raw
    # apo coords directly (only the L/H_new matrices built from them) --
    # reload the same way it does, since the spatial-block function needs
    # actual 3D coordinates, not just the built operator.
    import run_challenge
    from allostery.clean import load_target_config
    from allostery.labels import build_labels
    from allostery.hamiltonians import H2_combinatorial_laplacian
    from allostery.hamiltonians import build_H_new as _build_H_new
    from allostery.transport import effective_resistance_from_source, transmission_from_source

    for target, cell_name in CELLS:
        target_config = load_target_config(target)
        cutoff = float(target_config.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
        pocket_cutoff = float(target_config.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))
        apo, holo = run_challenge._load_apo_holo(target, target_config)
        labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
        source = np.sort(np.where(labels_obj.active_site)[0])
        labels = labels_obj.pocket.astype(int)
        coords = apo.coords

        L = H2_combinatorial_laplacian(apo.coords, cutoff=cutoff)
        H_new = _build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)

        if cell_name == "effective_resistance":
            score = effective_resistance_from_source(L, source)
        elif cell_name == "transmission_on_L_E0":
            score = transmission_from_source(L, source, E=0.0)
        elif cell_name == "transmission_on_H_new_E0":
            score = transmission_from_source(H_new, source, E=0.0)
        else:
            raise ValueError(cell_name)

        seq_ci = block_bootstrap_ci(score, labels, n_boot=1000, block_size=10, rng=np.random.default_rng(42))
        spatial_ci = spatial_block_bootstrap_ci(
            coords, score, labels, n_boot=1000, block_size=10, rng=np.random.default_rng(42)
        )
        seq_width = seq_ci[2] - seq_ci[1]
        spatial_width = spatial_ci[2] - spatial_ci[1]

        key = f"{target}/{cell_name}"
        results[key] = {
            "target": target, "cell": cell_name, "auc": float(_auc(score, labels)),
            "sequence_block_ci": list(seq_ci), "sequence_block_width": seq_width,
            "spatial_block_ci": list(spatial_ci), "spatial_block_width": spatial_width,
            "width_ratio": spatial_width / seq_width if seq_width else float("nan"),
        }
        _log(
            f"{key}: AUC={_auc(score, labels):.3f} "
            f"seq_CI=[{seq_ci[1]:.3f},{seq_ci[2]:.3f}] (w={seq_width:.3f}) "
            f"spatial_CI=[{spatial_ci[1]:.3f},{spatial_ci[2]:.3f}] (w={spatial_width:.3f}) "
            f"ratio={spatial_width / seq_width if seq_width else float('nan'):.2f}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "spatial_ci_rerun.json", "w") as f:
        json.dump(results, f, indent=2)
    _log(f"wrote {OUTPUT_DIR / 'spatial_ci_rerun.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
