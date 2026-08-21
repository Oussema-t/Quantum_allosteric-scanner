#!/usr/bin/env python3
"""TASK-0129 -- re-run floor/ceiling/actual (the competence-map numbers)
under TASK-0118's seed convention AND TASK-0119's per-operator clock,
combined.

Deliberately a standalone script, not an edit to `run_challenge.py`'s own
live `T_MAX=15.0`/`N_STEPS=500` defaults or `ceiling_search_batched.py`'s
-- TASK-0119's own Done section explicitly treated changing those live
defaults as "a separate, follow-up decision" out of its own scope, and
this task's own Out Of Scope forbids "building any new fix," which
includes silently promoting a research clock into the live submission
pipeline's defaults (a Tier-2-adjacent decision, TASK-0100). This script
calls the same underlying functions the live pipeline calls
(`protocol.run_frozen_verdict`, `ceiling.ceiling_search`) directly, with
the combined-fix parameters, without touching either live script.

**Clock convention for this axis, stated explicitly (a real simplification,
not hidden)**: `H_new`'s own default-config spectral gap determines a
single `t*`/`n*` per target, applied uniformly to both `H_new` and `H10`
candidates and to every one of the ceiling search's 60 trials (each of
which builds a *different* `H_new` parameterization with its own,
different true gap) -- the same "one t* per operator, not a
per-configuration formula" simplification TASK-0119's own Intent Contract
already made for the 96-cell sweep, extended here to "one t* representing
this operator family's own representative (default-config) timescale,"
not re-derived per ceiling trial. `H10`'s own t* is not separately
computed for this axis (a flagged gap, not silently assumed identical to
`H_new`'s) -- see this task's own Done section.
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
from allostery.ceiling import ceiling_search  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.hamiltonians import build_H_new, build_H10  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.propagators import min_adequate_n_steps, min_adequate_t_max, time_averaged_ctqw  # noqa: E402
from allostery.protocol import run_frozen_verdict  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo/DEFAULT_CUTOFF

TOL = 1e-2
N_STEPS_PRACTICAL_CAP = 5000
DEFAULT_CUTOFF = run_challenge.DEFAULT_CUTOFF
DEFAULT_POCKET_CUTOFF = run_challenge.DEFAULT_POCKET_CUTOFF
CEILING_N_TRIALS = 60
CEILING_SEED = 7
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0129_competence"


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


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
    source = np.sort(active_site_idx)  # TASK-0118 full array

    H_new = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
    H10 = build_H10(apo.coords, apo.bfactors, cutoff=cutoff)
    pocket_int = labels_obj.pocket.astype(int)

    w = np.linalg.eigvalsh(H_new)
    t_star = min_adequate_t_max(w=w, kind="ground_state_relaxation", tol=TOL)
    n_star = min_adequate_n_steps(w=w, t_max=t_star)
    n_steps_used = min(n_star, N_STEPS_PRACTICAL_CAP) if np.isfinite(n_star) else 500
    n_steps_capped = n_star > N_STEPS_PRACTICAL_CAP if np.isfinite(n_star) else False
    _log(f"{target_name}: H_new t*={t_star:.4g} n*={n_star} n_used={n_steps_used}{' (capped)' if n_steps_capped else ''}")

    floor_candidates = [
        degree_centrality(apo.coords, cutoff=cutoff),
        euclid_from_seed_centroid(apo.coords, source),
        hop_from_seed(apo.coords, source, cutoff=cutoff),
    ]
    floor = float(max(_auc(f, pocket_int) for f in floor_candidates))

    def build_candidates():
        return [
            {"H": H_new, "source": source, "t": t_star, "name": "H_new_default"},
            {"H": H10, "source": source, "t": t_star, "name": "H10_disorder_suppressed"},
        ]

    t0 = time.monotonic()
    result = run_frozen_verdict(
        target_name, build_candidates,
        apo.coords, apo.bfactors, source, labels_obj.pocket,
        cutoff=cutoff, t_max=t_star, n_steps=n_steps_used,
        floor_scores=floor_candidates, coherent=False,
    )
    actual_auc = result.get("AUC_apo_Hnew_optimised")
    _log(f"{target_name}: actual (combined) AUC={actual_auc} diagnosis={result.get('_diagnosis')} in {time.monotonic()-t0:.1f}s")

    t0 = time.monotonic()
    ceiling_result = ceiling_search(
        target_name, apo.coords, apo.bfactors, source, labels_obj.pocket,
        n_trials=CEILING_N_TRIALS, seed=CEILING_SEED,
        t_max=t_star, n_steps=n_steps_used, coherent=False,
    )
    ceiling_auc = ceiling_result["best"]["auc_apo"]
    _log(f"{target_name}: ceiling (combined) AUC={ceiling_auc:.4f} in {time.monotonic()-t0:.1f}s ({CEILING_N_TRIALS} trials)")

    return {
        "target": target_name,
        "n_residues": len(apo.resnums),
        "n_seed_residues": len(source),
        "t_star_h_new": t_star,
        "n_star_h_new": n_star,
        "n_steps_used": n_steps_used,
        "n_steps_capped": bool(n_steps_capped),
        "floor": floor,
        "actual_auc": actual_auc,
        "actual_diagnosis": result.get("_diagnosis"),
        "ceiling_auc": ceiling_auc,
        "ceiling_best_params": ceiling_result["best"]["params"],
        "ceiling_n_trials_scored": ceiling_result["n_trials_scored"],
        "headroom": (
            (actual_auc - floor) / (ceiling_auc - floor)
            if actual_auc is not None and ceiling_auc != floor else None
        ),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"])
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "combined_competence.json")
    args = parser.parse_args(argv)

    all_results = {}
    for name in args.target:
        try:
            all_results[name] = run_target(name)
            r = all_results[name]
            print(
                f"{name}: floor={r['floor']:.4f} ceiling={r['ceiling_auc']:.4f} "
                f"actual={r['actual_auc']:.4f} diag={r['actual_diagnosis']} "
                f"t*={r['t_star_h_new']:.4g} n_used={r['n_steps_used']}"
            )
        except Exception as exc:
            all_results[name] = {"error": str(exc)}
            print(f"{name}: FAILED -- {exc}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(all_results, f, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
