#!/usr/bin/env python3
"""TASK-0113 -- re-run TASK-0067's GNM cutoff/weight-scheme sweep against
the actual headline operator (`H_new`), not the bare contact-Laplacian
`gnm_cutoff_weight_sweep` scores.

TASK-0067's own stated scope (its Done section's "Caveat, stated
plainly") already flags that its benchmark "used the raw GNM Kirchhoff
only (no potential terms, single-source classical heat propagation)" --
not `H_new`/`time_averaged_ctqw`, the operator pair that produces every
headline AUC in `RESULTS.md`. That caveat never carried into
`EXECUTION_PLAN.md`'s own progress row ("backend's 8.0 A default does
not need to change"), which reads as covering the headline operator
when it doesn't. This script re-answers the same cutoff question
directly against `H_new`, scored via both propagators (TASK-0101's own
precedent of scoring through both).

**A real, structural finding from reading `hamiltonians.py` before
writing this script, not assumed**: TASK-0067's own sweep varies cutoff
*and* weight scheme via `contact_matrix(coords, cutoff, weight=scheme)`
applied to a bare Laplacian. `H_new`'s own base Laplacian
(`normalised_laplacian_alpha`) hardcodes `weight="exponential"` -- there
is no equivalent weight-scheme knob on `build_H_new` to sweep (per this
task's own Constraints: "reuse `hamiltonians.build_H_new`... this task
is a cutoff/propagator sweep, not an operator-weight sweep" -- adding
one would be exactly the operator-redesign this task's own scope
excludes). This script therefore sweeps `cutoff` only for `H_new`
(the one real, shared knob between the two operators) -- reported
explicitly as a real difference in what's being compared, not silently
matched to TASK-0067's original 2-axis grid shape.
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
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.propagators import ground_state_relaxation, time_averaged_ctqw_converged  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo/DEFAULT_CUTOFF

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0113_h_new_cutoff_sweep"
TARGETS = ["KRAS_G12C", "BCR_ABL1"]  # TASK-0067's own 2 targets; CARDIAC_MYOSIN
# excluded for the same data-quality reason TASK-0067 excluded it -- inherit,
# don't re-litigate, per this task's own Out Of Scope.
CUTOFFS = [7.5, 8.0, 10.0]  # TASK-0067's own grid
GSR_T_MAX = 15.0  # matches TASK-0067's own t_max, and this project's shipped default

# TASK-0067's own real-data aggregate (mean AUC across KRAS_G12C/BCR_ABL1,
# bare GNM Kirchhoff + ground_state_relaxation), per its own Done section --
# not re-derived here, cited directly for the comparison this task asks for.
TASK_0067_BARE_LAPLACIAN_MEAN_AUC = {7.5: 0.4230, 8.0: 0.4198, 10.0: 0.4322}


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run_target(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))

    _log(f"{target_name}: fetching + cleaning apo/holo...")
    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")
    source = np.sort(np.where(labels_obj.active_site)[0])
    if len(source) == 0:
        raise RuntimeError(f"{target_name}: empty active-site seed")
    pocket_int = labels_obj.pocket.astype(int)

    _log(f"{target_name}: N={len(apo.resnums)} n_seed={len(source)}")

    rows = []
    for cutoff in CUTOFFS:
        H_new = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)

        # TASK-0094's own floor baselines are themselves cutoff-dependent
        # (degree_centrality/hop_from_seed read the same GNM contact
        # graph) -- recomputed per cutoff for a fair, consistent
        # comparison, not held at the shipped 8.0 A value while H_new's
        # own cutoff varies.
        floor_candidates = [
            degree_centrality(apo.coords, cutoff=cutoff),
            euclid_from_seed_centroid(apo.coords, source),
            hop_from_seed(apo.coords, source, cutoff=cutoff),
        ]
        floor = float(max(_auc(f, pocket_int) for f in floor_candidates))

        occ_ctqw = time_averaged_ctqw_converged(H_new, source=source, coherent=False)
        auc_ctqw = _auc(occ_ctqw, pocket_int)
        diagnosis_ctqw = classify_failure(occ_ctqw, labels_obj.pocket, H=H_new, bfactors=apo.bfactors, floor_scores=floor_candidates)

        occ_gsr = ground_state_relaxation(H_new, GSR_T_MAX, source=source)
        auc_gsr = _auc(occ_gsr, pocket_int)

        rows.append({
            "cutoff": cutoff, "floor": floor,
            "auc_ctqw": float(auc_ctqw), "ctqw_floor_cleared": bool(auc_ctqw > floor), "ctqw_diagnosis": diagnosis_ctqw,
            "auc_ground_state": float(auc_gsr), "gsr_floor_cleared": bool(auc_gsr > floor),
        })
        _log(
            f"{target_name} cutoff={cutoff}A: floor={floor:.4f} AUC(ctqw)={auc_ctqw:.4f} "
            f"cleared={auc_ctqw > floor} diag={diagnosis_ctqw} AUC(ground_state)={auc_gsr:.4f} cleared={auc_gsr > floor}"
        )

    return {"target": target_name, "n_residues": len(apo.resnums), "rows": rows}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=TARGETS)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "h_new_cutoff_sweep.json")
    args = parser.parse_args(argv)

    all_results = {}
    for name in args.target:
        try:
            all_results[name] = run_target(name)
        except Exception as exc:
            all_results[name] = {"error": str(exc)}
            _log(f"{name}: FAILED -- {exc!r}")

    # Aggregate mean AUC per cutoff, per propagator, across whichever
    # targets succeeded -- mirrors TASK-0067's own aggregation exactly
    # (mean across targets, one row per cutoff) for a direct comparison.
    aggregate = {}
    for cutoff in CUTOFFS:
        ctqw_vals, gsr_vals = [], []
        for result in all_results.values():
            if "error" in result:
                continue
            row = next(r for r in result["rows"] if r["cutoff"] == cutoff)
            ctqw_vals.append(row["auc_ctqw"])
            gsr_vals.append(row["auc_ground_state"])
        aggregate[str(cutoff)] = {
            "mean_auc_ctqw": float(np.mean(ctqw_vals)) if ctqw_vals else None,
            "mean_auc_ground_state": float(np.mean(gsr_vals)) if gsr_vals else None,
            "bare_laplacian_mean_auc_task0067": TASK_0067_BARE_LAPLACIAN_MEAN_AUC[cutoff],
        }
        _log(f"cutoff={cutoff}A aggregate: {aggregate[str(cutoff)]}")

    all_results["_aggregate"] = aggregate

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(all_results, f, indent=2)
    _log(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
