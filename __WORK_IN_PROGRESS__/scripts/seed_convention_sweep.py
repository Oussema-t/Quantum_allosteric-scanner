#!/usr/bin/env python3
"""TASK-0118 -- real-data seed-convention sweep.

Answers the panel review's own validation-strategy row (REVIEW-panel-
2026-07-16-v2 Sec.6): "Sweep source = {1, k-subset, full, incoherent
mixture} x 3 targets. AUC spread > 0.1 -> it is a SIGNAL, not a gauge, the
pipeline has no defined initial condition (current evidence: ~0.3 ->
already failed)." That "current evidence" was a synthetic estimate
(occupation Spearman 0.61 between single- and array-seeding) -- this
script confirms (or refutes) it on the real mandatory targets, per this
task's own In Scope: "do not assume the synthetic estimate transfers."

Four source conventions, all derived from the same real active-site
residue set (`labels.Labels.active_site`), not four independently-chosen
seeds:
  - "single"      : run_challenge.py's own crash-workaround convention,
                     `int(np.sort(active_site_idx)[0])` (TASK-0090).
  - "k_subset"     : the first half (ceil(n/2)) of the sorted active-site
                     indices -- an intermediate cardinality point between
                     "single" and "full", not the panel's own specific
                     choice (unspecified in the review) but a documented,
                     reproducible one.
  - "full_coherent": every active-site residue, coherent equal-amplitude
                     superposition (`propagators.ctqw`'s pre-TASK-0118
                     default, `coherent=True`) -- TASK-0105/0106/
                     ceiling_search_batched.py's existing convention.
  - "full_incoherent": every active-site residue, incoherent statistical
                     mixture (`coherent=False`, TASK-0118's new
                     capability) -- the panel's own recommended
                     convention.

For each (target, convention), computes the floor (TASK-0094's
degree/euclid/hop baseline stack, re-derived under that convention's own
source since euclid/hop are themselves source-dependent) and the actual
AUC (`time_averaged_ctqw` on `H_new` at the target's default/optimised
physical-scalar config -- the same operator config `run_challenge.py`
ships, not a re-run of the optimizer for each convention, which is a
separate, heavier step this script does not attempt).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.propagators import time_averaged_ctqw  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo, not re-derived

DEFAULT_CUTOFF = 10.0
DEFAULT_POCKET_CUTOFF = 4.5
T_MAX = 15.0  # matches run_challenge.py's own live default -- this sweep
N_STEPS = 500  # is about the seed gauge, not re-litigating the clock (TASK-0119's job)


def _conventions(active_site_idx: np.ndarray) -> dict:
    sorted_idx = np.sort(active_site_idx)
    k = int(np.ceil(len(sorted_idx) / 2))
    return {
        "single": (int(sorted_idx[0]), True),
        "k_subset": (sorted_idx[:k], True),
        "full_coherent": (sorted_idx, True),
        "full_incoherent": (sorted_idx, False),
    }


def run_target(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))

    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None:
        raise RuntimeError(f"no resolvable pocket for {target_name!r}")

    active_site_idx = np.where(labels_obj.active_site)[0]
    if len(active_site_idx) == 0:
        raise RuntimeError(f"no active-site residues resolved for {target_name!r}")

    H_new = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
    pocket_int = labels_obj.pocket.astype(int)

    results = {}
    for name, (source, coherent) in _conventions(active_site_idx).items():
        occ = time_averaged_ctqw(H_new, T_MAX, source=source, n_steps=N_STEPS, coherent=coherent)
        auc_val = float(_auc(occ, pocket_int))

        floor_candidates = [
            degree_centrality(apo.coords, cutoff=cutoff),
            euclid_from_seed_centroid(apo.coords, source),
            hop_from_seed(apo.coords, source, cutoff=cutoff),
        ]
        floor = float(max(_auc(f, pocket_int) for f in floor_candidates))

        results[name] = {
            "n_seed_residues": int(len(np.atleast_1d(source))),
            "auc": auc_val,
            "floor": floor,
            "clears_floor": bool(auc_val > floor),
        }

    aucs = np.array([r["auc"] for r in results.values()])
    return {
        "target": target_name,
        "n_residues": len(apo.resnums),
        "n_active_site": len(active_site_idx),
        "conventions": results,
        "auc_spread": float(aucs.max() - aucs.min()),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--target", nargs="+", default=["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"],
        help="one or more config/targets.yaml keys",
    )
    parser.add_argument("--output", type=Path, default=None, help="write full JSON results here")
    args = parser.parse_args(argv)

    all_results = {}
    for name in args.target:
        try:
            all_results[name] = run_target(name)
            r = all_results[name]
            print(f"{name}: N={r['n_residues']} active_site={r['n_active_site']} auc_spread={r['auc_spread']:.4f}")
            for conv, row in r["conventions"].items():
                print(
                    f"  {conv:18s} n_seed={row['n_seed_residues']:3d} "
                    f"AUC={row['auc']:.4f} floor={row['floor']:.4f} clears={row['clears_floor']}"
                )
        except Exception as exc:
            all_results[name] = {"error": str(exc)}
            print(f"{name}: FAILED -- {exc}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(all_results, f, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
