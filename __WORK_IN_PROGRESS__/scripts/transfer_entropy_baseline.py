#!/usr/bin/env python3
"""TASK-0132 -- score the GNM transfer-entropy classical baseline
(`transfer_entropy.transfer_entropy_source_score`) against all 3
mandatory targets' real pocket labels, checked against TASK-0094's
proximity floor -- the same discipline every other observable in this
project's register goes through.

Run: python3 scripts/transfer_entropy_baseline.py
Output: __WORK_IN_PROGRESS__/results_task0132/transfer_entropy_baseline.json
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

from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.diagnostics import classify_failure  # noqa: E402
from allostery.hamiltonians import contact_matrix, laplacian  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as auc_fn  # noqa: E402
from allostery.transfer_entropy import gnm_relaxation_time, transfer_entropy_source_score  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo, not re-derived

DEFAULT_TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
DEFAULT_CUTOFF = 10.0
DEFAULT_POCKET_CUTOFF = 4.5
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0132"


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run_one(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))
    cutoff = float(target_config.get("enm_cutoff", DEFAULT_CUTOFF))

    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")

    active_site_idx = np.where(labels_obj.active_site)[0]
    if len(active_site_idx) == 0:
        raise RuntimeError(f"{target_name}: empty active_site mask")
    source = np.sort(active_site_idx)

    t0 = time.monotonic()
    tau = gnm_relaxation_time(apo.coords, cutoff=cutoff)
    score = transfer_entropy_source_score(apo.coords, cutoff=cutoff, tau=tau)
    elapsed = time.monotonic() - t0

    score_auc = auc_fn(score, labels_obj.pocket)

    floor_scores = [
        degree_centrality(apo.coords, cutoff=cutoff),
        euclid_from_seed_centroid(apo.coords, source),
        hop_from_seed(apo.coords, source, cutoff=cutoff),
    ]
    floor_aucs = [auc_fn(f, labels_obj.pocket) for f in floor_scores]

    A = contact_matrix(apo.coords, cutoff=cutoff, weight="binary")
    H_for_diagnosis = laplacian(A, normalised=False)
    diagnosis = classify_failure(
        score, labels_obj.pocket, H=H_for_diagnosis, bfactors=apo.bfactors,
        floor_scores=floor_scores,
    )

    result = {
        "target": target_name,
        "N": len(apo.coords),
        "pocket_size": int(labels_obj.pocket.sum()),
        "cutoff": cutoff,
        "tau": tau,
        "elapsed_s": round(elapsed, 2),
        "auc": float(score_auc),
        "floor_aucs": {"degree": floor_aucs[0], "euclid": floor_aucs[1], "hop": floor_aucs[2]},
        "max_floor": float(max(floor_aucs)),
        "diagnosis": diagnosis,
    }
    _log(
        f"{target_name}: N={result['N']} tau={tau:.3g} AUC={score_auc:.4f} "
        f"max_floor={result['max_floor']:.4f} ({elapsed:.1f}s) -> {diagnosis}"
    )
    return result


def main() -> int:
    results = {}
    for target_name in DEFAULT_TARGETS:
        try:
            results[target_name] = run_one(target_name)
        except Exception as exc:
            _log(f"{target_name}: FAILED -- {exc!r}")
            results[target_name] = {"target": target_name, "error": str(exc)}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "transfer_entropy_baseline.json", "w") as f:
        json.dump(results, f, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
