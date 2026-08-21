#!/usr/bin/env python3
"""TASK-0148 -- real-target scoring for single-particle entanglement
entropy across a spatial cut (`allostery.entanglement`), a localization/
coupling observable distinct from raw occupation, distance-stratified
AUC, or anything else currently in this project's register.

Score per candidate residue `j`: the Peschel entanglement entropy of the
active site's coherent single-particle state, bipartitioned into `j`'s
own hop-radius-1 neighborhood (region A) vs. everything else (region B).
Computed via `entanglement_entropy_mixture` (this project's own
established TASK-0118 incoherent-mixture GAUGE over the active-site
residue set -- NOT the coherent-superposition convention).

`t = natural_coherent_time(H)` (`1/gap`, blind to labels) is the primary,
pre-registered time -- entanglement entropy needs a genuinely coherent
amplitude, so the converged/time-averaged limit is not an option (see
`allostery.entanglement`'s own module docstring). A small time grid is
characterized separately as a KNOB, not used to pick a best-scoring
point against labels.

Cross-read against TASK-0106's own global CTQW localization finding:
reports `metrics.ipr` (participation ratio) of the same coherent
snapshot's occupation, and of the project's own standard converged-limit
occupation, alongside the per-candidate entropy scores.
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
from scipy.sparse.csgraph import shortest_path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.diagnostics import classify_failure  # noqa: E402
from allostery.entanglement import (  # noqa: E402
    entanglement_entropy_mixture,
    hop_radius_neighborhoods,
    natural_coherent_time,
)
from allostery.hamiltonians import build_H_new, contact_matrix, laplacian  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as auc_fn, ipr  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo, not re-derived

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0148_entanglement"
TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]

T_MULTIPLIERS = np.array([0.5, 1.0, 2.0])  # KNOB characterization only, x natural_coherent_time
RADII = [1, 2]  # KNOB characterization only

N_PERM = 1000
ALPHA = 0.05
N_TARGETS_FOR_BONFERRONI = len(TARGETS)


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _permutation_null(score: np.ndarray, pocket: np.ndarray, n_residues: int, pocket_size: int,
                       n_reps: int = N_PERM, seed: int = 123) -> dict:
    """Cheap re-labeling null (TASK-0131/0141/0145 precedent). Applied to
    the primary score (radius=1, t=natural_coherent_time) -- fixed a
    priori, not selected from the KNOB grids below, so this is
    due-diligence scrutiny on the standing number, not a max-of-K
    correction."""
    rng = np.random.default_rng(seed)
    real_auc = float(auc_fn(score, pocket))
    null_aucs = np.empty(n_reps)
    for i in range(n_reps):
        perm_idx = rng.choice(n_residues, size=pocket_size, replace=False)
        perm_pocket = np.zeros(n_residues, dtype=int)
        perm_pocket[perm_idx] = 1
        null_aucs[i] = auc_fn(score, perm_pocket)
    p_value = float((null_aucs >= real_auc).mean())
    return {
        "real_auc": real_auc, "null_median": float(np.median(null_aucs)),
        "null_p95": float(np.percentile(null_aucs, 95)), "p_value": p_value,
        "n_reps": n_reps, "bonferroni_alpha": ALPHA / N_TARGETS_FOR_BONFERRONI,
        "bonferroni_significant": bool(p_value < ALPHA / N_TARGETS_FOR_BONFERRONI),
    }


def _prepare_target(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))

    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")
    source = np.sort(np.where(labels_obj.active_site)[0])
    if len(source) == 0:
        raise RuntimeError(f"{target_name}: empty active-site seed")

    H_new = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
    A = contact_matrix(apo.coords, cutoff=cutoff, weight="binary")
    hop_dist = shortest_path(A.astype(float), method="D", unweighted=True, directed=False)

    floor_scores = [
        degree_centrality(apo.coords, cutoff=cutoff),
        euclid_from_seed_centroid(apo.coords, source),
        hop_from_seed(apo.coords, source, cutoff=cutoff),
    ]
    H_for_diagnosis = laplacian(A, normalised=False)

    return {
        "target": target_name, "H_new": H_new, "hop_dist": hop_dist,
        "bfactors": apo.bfactors, "source": source,
        "pocket": labels_obj.pocket.astype(int), "n_residues": len(apo.resnums),
        "cutoff": cutoff, "floor_scores": floor_scores, "H_for_diagnosis": H_for_diagnosis,
    }


def run_one(target_name: str) -> dict:
    prep = _prepare_target(target_name)
    H_new, hop_dist, source = prep["H_new"], prep["hop_dist"], prep["source"]
    N = prep["n_residues"]
    _log(f"{target_name}: N={N} pocket_size={int(prep['pocket'].sum())} cutoff={prep['cutoff']}")

    t_star = natural_coherent_time(H_new)
    neighborhoods_r1 = hop_radius_neighborhoods(hop_dist, radius=1)

    t0 = time.monotonic()
    entropy = entanglement_entropy_mixture(H_new, source, neighborhoods_r1, t_star)
    elapsed = time.monotonic() - t0

    auc = float(auc_fn(entropy, prep["pocket"]))
    diag = classify_failure(
        entropy, prep["pocket"], H=prep["H_for_diagnosis"], bfactors=prep["bfactors"],
        floor_scores=prep["floor_scores"], return_ci=True,
    )
    null = _permutation_null(entropy, prep["pocket"], N, int(prep["pocket"].sum()))
    _log(f"{target_name}: entanglement entropy AUC={auc:.4f} cat={diag.category} "
         f"p={null['p_value']:.4f} t*={t_star:.4g} ({elapsed:.1f}s)")

    # Cross-read against TASK-0106's own global CTQW localization finding.
    occ_coherent_mixture = np.mean(
        [np.abs(_amp) ** 2 for _amp in [
            _coherent_amplitude(H_new, s, t_star) for s in source
        ]], axis=0,
    )
    pr_coherent_snapshot = float(ipr(occ_coherent_mixture))
    occ_converged = time_averaged_ctqw_converged(H_new, source=source, coherent=False)
    pr_converged = float(ipr(occ_converged))

    # KNOB characterizations -- NOT best-of-K selections against labels.
    t_grid_aucs = []
    for t_mult in T_MULTIPLIERS:
        e_t = entanglement_entropy_mixture(H_new, source, neighborhoods_r1, float(t_mult) * t_star)
        t_grid_aucs.append({"t_multiplier": float(t_mult), "auc": float(auc_fn(e_t, prep["pocket"]))})
    radius_grid_aucs = []
    for r in RADII:
        neighborhoods_r = hop_radius_neighborhoods(hop_dist, radius=r)
        e_r = entanglement_entropy_mixture(H_new, source, neighborhoods_r, t_star)
        radius_grid_aucs.append({"radius": r, "auc": float(auc_fn(e_r, prep["pocket"]))})

    return {
        "target": target_name, "N": N, "pocket_size": int(prep["pocket"].sum()),
        "cutoff": prep["cutoff"], "t_star": t_star,
        "entanglement_entropy": {
            "auc": auc, "category": diag.category, "score_ci": diag.score_ci,
            "floor_ci": diag.floor_ci, "ci_overlap": diag.ci_overlap, "permutation_null": null,
        },
        "cross_read_task_0106": {
            "participation_ratio_coherent_snapshot": pr_coherent_snapshot,
            "participation_ratio_converged_limit": pr_converged,
        },
        "t_knob_grid": t_grid_aucs,
        "radius_knob_grid": radius_grid_aucs,
    }


def _coherent_amplitude(H: np.ndarray, source_idx: int, t: float) -> np.ndarray:
    w, v = np.linalg.eigh(H)
    coeffs = v[int(source_idx), :]
    return v @ (np.exp(-1j * w * t) * coeffs)


def main() -> int:
    results = {}
    for target_name in TARGETS:
        try:
            results[target_name] = run_one(target_name)
        except Exception as exc:
            _log(f"{target_name}: FAILED -- {exc!r}")
            results[target_name] = {"target": target_name, "error": str(exc)}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "entanglement_entropy_real_run.json", "w") as f:
        json.dump(results, f, indent=2)
    _log(f"wrote {OUTPUT_DIR / 'entanglement_entropy_real_run.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
