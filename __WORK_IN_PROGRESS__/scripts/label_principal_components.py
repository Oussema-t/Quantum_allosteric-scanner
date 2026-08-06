#!/usr/bin/env python3
"""TASK-0207 -- label TASK-0199's top-3 principal components (of the
28-real-observable Spearman correlation matrix) by which observable
family dominates each, and locate which axis `-hop`/`-euclid` land
nearest to.

Recomputes nothing scientific: reuses `observable_effective_rank.py`'s
own already-tested `_prepare_target`/`compute_all_observables`/
`align_and_stack`/`correlation_matrix_and_rank`/`confound_projection`
functions directly. The only new computation this script adds is
capturing full eigen*vectors* (not just eigenvalues) for the top-3 PCs of
both the 28x28 real-observable matrix and the 30x30 hop/euclid-extended
matrix -- linear algebra on an already-computed matrix, not a new
measurement.

Family-assignment rule and PC sign convention are fixed in
`.ai/tasks/DONE/TASK-0207-*.md`'s own "In Progress" section, written
before this script existed -- see that file for the full reasoning.
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
from scipy.stats import spearmanr

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from observable_effective_rank import (  # noqa: E402
    TARGETS_EXTRA,
    TARGETS_PRIMARY,
    _prepare_target,
    align_and_stack,
    compute_all_observables,
    confound_projection,
    correlation_matrix_and_rank,
)

from allostery.baselines import euclid_from_seed_centroid, hop_from_seed  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0207_pc_labels"
STORED_JSON = Path(__file__).resolve().parent.parent / "results_task0199_observable_rank" / "observable_effective_rank.json"

# TASK-0207's own pre-registered family-assignment rule -- fixed before
# any loading was computed or seen, see the task file's own record.
FAMILIES = {
    "channel_transport": {"R_eff", "T_E0_on_L", "T_E0_on_Hnew", "transfer_entropy"},
    "ensemble_mode": {"dcc_low", "prs_low", "mode_coparticipation", "conformational_entropy"},
    "hamiltonian_occupancy": {
        "occ_H1", "occ_H2", "occ_H3", "occ_H4", "occ_H5", "occ_H6", "occ_H7",
        "occ_H8", "occ_H9", "occ_H10", "occ_H11", "occ_H12", "occ_H14",
        "occ_H_new", "occ_build_H10",
    },
    "remainder": {"chiral_circulation", "coupling_specificity", "entanglement_entropy", "spectral_coherence", "void_score"},
}
_ASSIGNED = set().union(*FAMILIES.values())


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _fix_sign(vec: np.ndarray) -> np.ndarray:
    """TASK-0207's own sign convention: largest-magnitude loading positive."""
    idx = int(np.argmax(np.abs(vec)))
    return -vec if vec[idx] < 0 else vec.copy()


def _family_of(name: str) -> str:
    for fam, members in FAMILIES.items():
        if name in members:
            return fam
    return "UNASSIGNED"


def _label_pc(vec: np.ndarray, names: list) -> dict:
    fam_scores = {}
    for fam, members in FAMILIES.items():
        vals = [abs(vec[i]) for i, n in enumerate(names) if n in members]
        if vals:
            fam_scores[fam] = float(np.mean(vals))
    dominant = max(fam_scores, key=fam_scores.get) if fam_scores else None
    return dominant, fam_scores


def run_target(target_name: str, stored: dict) -> dict:
    _log(f"{target_name}: preparing + computing 28 observables (reused, not re-derived)...")
    t0 = time.monotonic()
    prep = _prepare_target(target_name)
    observables = compute_all_observables(prep)
    names, matrix = align_and_stack(observables)
    _log(f"{target_name}: done in {time.monotonic() - t0:.1f}s")

    unassigned = [n for n in names if n not in _ASSIGNED]
    if unassigned:
        raise ValueError(f"{target_name}: observables with no family assignment: {unassigned}")

    rank_report = correlation_matrix_and_rank(matrix)

    # -- Wiring check: reproduce TASK-0199's own published numbers exactly --
    stored_t = stored[target_name]
    stored_rank = stored_t["rank_report"]["participation_ratio_rank"]
    my_rank = rank_report["participation_ratio_rank"]
    wiring_ok = abs(stored_rank - my_rank) < 1e-6
    if not wiring_ok:
        _log(f"{target_name}: WIRING CHECK FAILED -- stored rank {stored_rank} vs recomputed {my_rank}")

    # -- Top-3 PCs of the 28x28 real-observable-only matrix (primary object) --
    corr = np.array(rank_report["corr_matrix"])
    eigvals, eigvecs = np.linalg.eigh(corr)  # ascending
    order = np.argsort(eigvals)[::-1]
    total_var = float(eigvals.sum())

    pcs = []
    for rank_i, idx in enumerate(order[:3], start=1):
        vec = _fix_sign(eigvecs[:, idx])
        dominant, fam_scores = _label_pc(vec, names)
        sorted_loadings = sorted(zip(names, vec.tolist()), key=lambda kv: -abs(kv[1]))
        pcs.append({
            "pc": rank_i,
            "eigenvalue": float(eigvals[idx]),
            "variance_fraction": float(eigvals[idx] / total_var),
            "dominant_family": dominant,
            "family_mean_abs_loading": fam_scores,
            "top8_loadings": sorted_loadings[:8],
            "all_loadings": {n: v for n, v in zip(names, vec.tolist())},
        })

    # -- Confound projection: extended 30x30 matrix (28 real + hop + euclid),
    #    same construction TASK-0199's own confound_projection() uses --
    #    reused directly, not re-derived, plus top-3 (not just PC1) captured.
    confound = confound_projection(names, matrix, prep["coords"], prep["source"])
    hop = -hop_from_seed(prep["coords"], prep["source"])
    euclid = -euclid_from_seed_centroid(prep["coords"], prep["source"])
    ext_names = names + ["neg_hop", "neg_euclid"]
    ext_matrix = np.column_stack([matrix, hop, euclid])
    ext_corr, _p = spearmanr(ext_matrix)
    ext_corr = np.atleast_2d(ext_corr)
    ext_eigvals, ext_eigvecs = np.linalg.eigh(ext_corr)
    ext_order = np.argsort(ext_eigvals)[::-1]

    # Wiring check #2: my extended-PC1 must match TASK-0199's own stored PC1.
    my_ext_pc1 = _fix_sign(ext_eigvecs[:, ext_order[0]])
    stored_pc1_dict = stored_t["confound_projection"]["pc1_loadings"]
    stored_pc1_vec = _fix_sign(np.array([stored_pc1_dict[n] for n in ext_names]))
    pc1_match = float(np.max(np.abs(my_ext_pc1 - stored_pc1_vec)))
    pc1_wiring_ok = pc1_match < 1e-6

    confound_axis = {}
    for conf_name in ("neg_hop", "neg_euclid"):
        conf_idx = ext_names.index(conf_name)
        abs_by_pc = [
            abs(_fix_sign(ext_eigvecs[:, ext_order[k]])[conf_idx]) for k in range(3)
        ]
        confound_axis[conf_name] = {
            "abs_loading_by_pc123": abs_by_pc,
            "nearest_pc": int(np.argmax(abs_by_pc)) + 1,
        }

    _log(
        f"{target_name}: PC1={pcs[0]['dominant_family']} ({pcs[0]['variance_fraction']*100:.1f}% var) "
        f"PC2={pcs[1]['dominant_family']} ({pcs[1]['variance_fraction']*100:.1f}%) "
        f"PC3={pcs[2]['dominant_family']} ({pcs[2]['variance_fraction']*100:.1f}%) "
        f"hop->PC{confound_axis['neg_hop']['nearest_pc']} euclid->PC{confound_axis['neg_euclid']['nearest_pc']} "
        f"wiring_ok={wiring_ok and pc1_wiring_ok}"
    )

    return {
        "target": target_name,
        "n_residues": prep["n_residues"],
        "wiring_check": {
            "rank_match": wiring_ok, "stored_rank": stored_rank, "recomputed_rank": my_rank,
            "pc1_match": pc1_wiring_ok, "pc1_max_abs_diff": pc1_match,
        },
        "pcs": pcs,
        "confound_axis": confound_axis,
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stored = json.load(open(STORED_JSON))
    results = {}
    for target in TARGETS_PRIMARY + TARGETS_EXTRA:
        try:
            results[target] = run_target(target, stored)
        except Exception as exc:
            results[target] = {"target": target, "error": str(exc)}
            _log(f"{target}: FAILED -- {exc!r}")
        with open(OUTPUT_DIR / "pc_labels.json", "w") as f:
            json.dump(results, f, indent=2)
    _log(f"wrote {OUTPUT_DIR / 'pc_labels.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
