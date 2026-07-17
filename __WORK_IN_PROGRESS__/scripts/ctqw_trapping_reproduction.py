#!/usr/bin/env python3
"""TASK-0106 -- reproduce the CTQW-trapping finding on real BCR_ABL1 data.

`REVIEW-2026-07-13c` (synthetic-network mechanism test, no network access
at review time) found that `H_new`'s diagonal potentials (V_B/V_T/V_R/
V_C/V_M) cause Anderson-like transport localization in CTQW -- the walk
never leaves the seed's first contact shell -- and that on a synthetic
distal pocket, transport-preserving operators (`H10`, `H2`) score 0.58-
0.59 AUC where `H_new` scores 0.12 (anti-correlated) and a pure proximity
baseline scores exactly 0. This script is the real-data gate that review
itself requires before that finding changes any claim (its own Caveats
section: "Do not report this in RESULTS.md or the submission until it
reproduces on real targets").

Tier-1 descriptive measurement only (TASK-0100's own tiering) -- this
does not select a new submission operator; see TASK-0100 for that gate.

`H_new` at "reduced lambda=0.25" (the review's own synthetic sweep point)
is implemented here as a uniform external scale on `build_H_new`'s own
default per-term coefficients -- i.e. `lam_X_used = 0.25 * lam_X_default`
for every term, preserving each term's relative weight while scaling the
whole diagonal-potential block down, matching the review's own
`H(lambda) = L_norm + lambda*(V_B+V_T+V_R+V_C+V_M)` construction (a single
external multiplier on the combined potential sum, not a re-tuning of the
individual terms).

TASK-0121: `_H_NEW_DEFAULT_LAMBDAS` below mirrors `build_H_new`'s own
`lam_*` defaults and must be kept in sync with them -- it was
(lam_B=1.0, lam_T=2.0, lam_R=1.0, lam_C=0.5, lam_M=0.5) before TASK-0121
z-scored `potentials.py`'s five terms and rescaled the defaults to keep
sigma(V) <= 0.2*J; see that task's Done section for the derivation.
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
from allostery.hamiltonians import H2_combinatorial_laplacian, build_H10, build_H_new  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as _auc, ipr as _ipr  # noqa: E402
from allostery.propagators import time_averaged_ctqw  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo, not re-derived

DEFAULT_CUTOFF = 10.0
DEFAULT_POCKET_CUTOFF = 4.5
T_MAX = 15.0
N_STEPS = 500

# build_H_new's own default per-term coefficients (hamiltonians.py) --
# lambda=0.25 scales this whole set uniformly, per the review's own
# H(lambda) = L_norm + lambda*(sum of V terms) construction.
_H_NEW_DEFAULT_LAMBDAS = dict(lam_B=0.08, lam_T=0.16, lam_R=0.08, lam_C=0.04, lam_M=0.04)


def _build_h_new_scaled(coords, bfactors, cutoff: float, lam: float):
    scaled = {k: lam * v for k, v in _H_NEW_DEFAULT_LAMBDAS.items()}
    return build_H_new(coords, bfactors, cutoff=cutoff, **scaled)


def transport_diagnostics(occ: np.ndarray, coords: np.ndarray, source, cutoff: float) -> dict:
    """The same transport diagnostic REVIEW-2026-07-13c used: participation
    ratio (`metrics.ipr`, this codebase's own PR/N convention -- see
    `select.py::focusing`'s docstring for why `ipr` is valid on an L1-
    normalised occupation vector) and occupation-weighted mean hop
    distance from the seed."""
    hop_dist = -hop_from_seed(coords, source, cutoff=cutoff)  # hop_from_seed is negated; flip back
    mean_hop = float(np.sum(occ * hop_dist))
    return {"participation_ratio": _ipr(occ), "mean_hop_from_seed": mean_hop}


def run_bcr_abl1_reproduction(lam_reduced: float = 0.25) -> dict:
    target_name = "BCR_ABL1"
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
    # Single representative seed index -- matches run_challenge.py's own
    # convention *exactly* (same sorted-first-active-site-index choice),
    # not re-derived. This task is explicitly checking real numbers
    # already in RESULTS.md (AUC_apo_H10_baseline=0.558 vs
    # AUC_apo_Hnew_default=0.525) and TASK-0094's floor (0.565) -- all
    # three were computed with this exact seeding, so reproducing them
    # requires the same seed, not a different (even if arguably more
    # complete) choice. Confirmed empirically: this convention reproduces
    # 0.525/0.558 exactly (see this task's Done section) where an earlier
    # attempt using the full active-site array as a multi-index source
    # did not (and gave a materially different, seed-sensitive picture --
    # reported as its own finding, not silently discarded).
    source = int(np.sort(active_site_idx)[0])

    pocket_int = labels_obj.pocket.astype(int)
    floor_candidates = [
        degree_centrality(apo.coords, cutoff=cutoff),
        euclid_from_seed_centroid(apo.coords, source),
        hop_from_seed(apo.coords, source, cutoff=cutoff),
    ]
    floor_names = ["degree_centrality", "euclid_from_seed_centroid", "hop_from_seed"]
    floor_aucs = {name: _auc(f, pocket_int) for name, f in zip(floor_names, floor_candidates)}
    floor = max(floor_aucs.values())

    operators = {
        "H_new_default": build_H_new(apo.coords, apo.bfactors, cutoff=cutoff),
        f"H_new_lambda={lam_reduced}": _build_h_new_scaled(apo.coords, apo.bfactors, cutoff, lam_reduced),
        "H10_disorder_suppressed": build_H10(apo.coords, apo.bfactors, cutoff=cutoff),
        "H2_combinatorial_laplacian": H2_combinatorial_laplacian(apo.coords, cutoff=cutoff),
    }

    rows = {}
    for name, H in operators.items():
        occ = time_averaged_ctqw(H, T_MAX, source=source, n_steps=N_STEPS)
        auc = _auc(occ, pocket_int)
        diag = transport_diagnostics(occ, apo.coords, source, cutoff)
        rows[name] = {
            "auc": auc,
            "floor_cleared": bool(not np.isnan(auc) and auc > floor),
            **diag,
        }

    return {
        "target": target_name,
        "n_residues": len(apo.resnums),
        "cutoff": cutoff,
        "t_max": T_MAX,
        "floor": floor,
        "floor_candidate_aucs": floor_aucs,
        "operators": rows,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--lambda-reduced", type=float, default=0.25)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    result = run_bcr_abl1_reproduction(args.lambda_reduced)
    print(f"BCR_ABL1: N={result['n_residues']}, floor={result['floor']:.3f}")
    for name, row in result["operators"].items():
        print(
            f"  {name}: AUC={row['auc']:.3f} floor_cleared={row['floor_cleared']} "
            f"PR/N={row['participation_ratio']:.4f} <hop>={row['mean_hop_from_seed']:.2f}"
        )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
