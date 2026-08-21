#!/usr/bin/env python3
"""TASK-0228 §2 -- PDB-retest: does an adaptive (per-step-recomputed) ANM
subspace capture the real apo->holo pocket-opening displacement better
than a static (apo-only) subspace of the *same dimension*, on real
challenge targets?

External finding this re-derives on real data (session drop
`.ai/reviews/2026-08-21/TASK-0212_conformer_graph_search.md` §2): on ADK
(a non-target structure, synthetic local-opening displacement), adaptive
beat static ~9.4x at equal dimension (110). The drop's own instruction:
"repeat on 4OBE, 1OPL, 5TBY with the TRUE apo->holo displacement replacing
the synthetic opening vector" -- done here against the REAL, labeled
pocket displacement (not a synthetic radial-expansion proxy) via this
module's own validated `restricted_cumulative_overlap` (TASK-0133),
reusing `compute_learnability`'s real apo/holo fetch, chain-mapped
alignment, and pocket-labeling path (`learnability_gate.py`'s own
`run_one`) rather than re-deriving any of it.

CARDIAC_MYOSIN correction: the drop's own suggested "5TBY->6C1H" pair is
`backend/systems.py`'s pairing, already superseded in *this* research
tree by TASK-0124 (5TBY is a homology-model apo; 8QYP is the real X-ray
structure) and TASK-0169 (6C1H is confirmed the wrong protein -- actin-
bound Myosin-Ib, not cardiac myosin; 8QYR is the real validated holo).
`config/targets.yaml` already carries the corrected pair -- this script
uses it via `load_target_config`, not the drop's own stale suggestion.

KRAS_G12C caveat, carried forward not silently dropped: apo 4OBE is
confirmed wild-type (Gly12), not G12C (TASK-0155/TASK-0192) -- this
script measures generic apo-flexibility-vs-pocket-displacement
reachability, not a G12C-specific claim, but the caveat applies to every
KRAS_G12C number this project has ever reported and is repeated here for
the same reason.
"""
from __future__ import annotations

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
from allostery.superpose import (  # noqa: E402
    adaptive_anm_modes,
    align_apo_holo,
    anm_modes,
    chain_map_from_config,
    restricted_cumulative_overlap,
)

import run_challenge  # noqa: E402

DEFAULT_TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
DEFAULT_ANM_CUTOFF = 10.0
DEFAULT_POCKET_CUTOFF = 4.5
DEFAULT_N_MODES = 10          # static apo top-k BEFORE the adaptive union expands it
DEFAULT_N_MODES_STEPPED = 5   # matches the external drop's own ADK run exactly
DEFAULT_AMP = 6.0


def run_one(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))
    anm_cutoff = float(target_config.get("enm_cutoff", DEFAULT_ANM_CUTOFF))

    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")

    alignment = align_apo_holo(apo, holo, chain_map=chain_map_from_config(target_config))
    in_common = np.zeros(len(labels_obj.pocket), dtype=bool)
    in_common[alignment.apo_idx] = True
    pocket_idx = np.where(labels_obj.pocket & in_common)[0]
    if len(pocket_idx) == 0:
        raise RuntimeError(f"{target_name}: no pocket residue has a holo correspondence")

    adaptive_basis = adaptive_anm_modes(
        apo.coords, cutoff=anm_cutoff, n_modes=DEFAULT_N_MODES,
        n_modes_stepped=DEFAULT_N_MODES_STEPPED, amp=DEFAULT_AMP,
    )
    dim = adaptive_basis.shape[1]

    _, static_full = anm_modes(apo.coords, cutoff=anm_cutoff, n_modes=dim)
    if static_full.shape[1] < dim:
        raise RuntimeError(
            f"{target_name}: static basis only has {static_full.shape[1]} modes, "
            f"fewer than the adaptive union's {dim} -- equal-dimension comparison "
            "not possible on this target (too few non-trivial ANM modes)"
        )
    static_basis = static_full[:, :dim]   # equal dimension -- do not omit

    co_static = restricted_cumulative_overlap(apo, alignment, static_basis, pocket_idx)
    co_adaptive = restricted_cumulative_overlap(apo, alignment, adaptive_basis, pocket_idx)
    static_final = float(co_static[-1]) if len(co_static) else float("nan")
    adaptive_final = float(co_adaptive[-1]) if len(co_adaptive) else float("nan")
    ratio = adaptive_final / static_final if static_final > 1e-12 else float("inf")

    result = {
        "target": target_name, "n_residues": len(apo.resnums),
        "n_pocket_residues": int(len(pocket_idx)), "dim": int(dim),
        "co_static_final": round(static_final, 4),
        "co_adaptive_final": round(adaptive_final, 4),
        "ratio": round(ratio, 3),
    }
    print(
        f"{target_name}: N={result['n_residues']} n_pocket={result['n_pocket_residues']} "
        f"dim={dim}  static CO={static_final:.4f}  adaptive CO={adaptive_final:.4f}  "
        f"ratio={ratio:.2f}x"
    )
    return result


def main(argv=None) -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=DEFAULT_TARGETS)
    parser.add_argument(
        "--output", type=Path,
        default=Path(__file__).resolve().parent.parent / "results/tasks/0228/adaptive_subspace_pdb_retest.json",
    )
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
