#!/usr/bin/env python3
"""TASK-0199 -- effective rank of the observable register: are the ~40
scored observables genuinely independent, or ~40 views of one underlying
quantity (the distance-from-seed confound)? Never scores against any
label -- observable-vs-observable only, consumes no multiplicity budget.

Definition, enumeration, and scoping decisions are all pre-registered in
`.ai/tasks/DONE/TASK-0199-*.md`'s own "Pre-Registered Definition +
Observable Enumeration" section, written before this script existed --
see that file for the full reasoning, not repeated here. Summary:
participation ratio of the cross-observable Spearman correlation matrix
is primary (`metrics.participation_ratio_rank`); `metrics.eff_rank`
(entropy-based) and a 90%/95%-variance threshold count are sweep
companions, never substitutes.
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

from allostery.analysis import _operator_registry, mode_coparticipation  # noqa: E402
from allostery.baselines import euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.chiral import chiral_circulation_score  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.conformational_entropy import residue_conformational_entropy  # noqa: E402
from allostery.entanglement import entanglement_entropy_mixture, hop_radius_neighborhoods, natural_coherent_time  # noqa: E402
from allostery.hamiltonians import H2_combinatorial_laplacian, contact_matrix, laplacian  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.lowmode_predictor import dcc_low, prs_low  # noqa: E402
from allostery.metrics import eff_rank, participation_ratio_rank, variance_explained_count  # noqa: E402
from allostery.persistent_voids import void_score  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from allostery.response import coupling_profile, coupling_specificity  # noqa: E402
from allostery.spectral_coherence import spectral_coherence_score  # noqa: E402
from allostery.transfer_entropy import transfer_entropy_source_score  # noqa: E402
from allostery.transport import effective_resistance_from_source, transmission_from_source  # noqa: E402

import run_challenge  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0199_observable_rank"
TARGETS_PRIMARY = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
TARGETS_EXTRA = ["PTP1B", "CASPASE7"]
K_MODES = 20  # dcc_low/prs_low headline k, matches TASK-0149's own primary
RESPONSE_KAPPA, RESPONSE_PATCH_SIZE = 1.0, 6


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


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
    return {
        "coords": apo.coords, "bfactors": apo.bfactors, "source": source,
        "cutoff": cutoff, "n_residues": len(apo.resnums),
    }


def compute_all_observables(prep: dict) -> dict:
    """Every observable's own `(N,)` score vector -- one call per
    already-tested function, apo-only inputs, no label ever read here
    (per this task's own Constraint: observable-vs-observable, not
    observable-vs-truth)."""
    coords, bfactors, source, cutoff = prep["coords"], prep["bfactors"], prep["source"], prep["cutoff"]
    out = {}

    # -- Hamiltonian operators (analysis._operator_registry), CTQW occupancy --
    # H13 excluded: `H13_3N_anm_hessian` returns a 3N x 3N operator (per-
    # axis, not per-residue) -- `analysis.operator_sweep` itself already
    # excludes it from residue-indexed scoring for exactly this reason
    # ("cannot be indexed by residue without a reduction this task does
    # not invent"); matched here, not re-litigated. 15 operators, not 16.
    n_residues = len(coords)
    for name, (_tier, build_fn) in _operator_registry().items():
        if name == "H13":
            continue
        H = build_fn(coords, bfactors, cutoff)
        if H.shape != (n_residues, n_residues):
            raise ValueError(f"{name} returned {H.shape}, expected ({n_residues}, {n_residues})")
        w, v = np.linalg.eigh(H)
        out[f"occ_{name}"] = time_averaged_ctqw_converged(source=source, coherent=False, w=w, v=v)
    H_new = _operator_registry()["H_new"][1](coords, bfactors, cutoff)

    # -- lowmode --
    out["dcc_low"] = dcc_low(coords, source, cutoff=cutoff, k_modes=K_MODES)
    out["prs_low"] = prs_low(coords, source, cutoff=cutoff, k_modes=K_MODES)

    # -- transport --
    L = H2_combinatorial_laplacian(coords, cutoff=cutoff)
    out["R_eff"] = effective_resistance_from_source(L, source)
    out["T_E0_on_L"] = transmission_from_source(L, source, E=0.0)
    out["T_E0_on_Hnew"] = transmission_from_source(H_new, source, E=0.0)

    # -- chiral circulation (reuses H_new's own adjacency/weighting) --
    out["chiral_circulation"] = chiral_circulation_score(coords, source, cutoff=cutoff, H_real=H_new)

    # -- mode co-participation --
    out["mode_coparticipation"] = mode_coparticipation(H_new, source, n_low=5)

    # -- spectral (frequency-domain) coherence --
    out["spectral_coherence"] = spectral_coherence_score(H_new, source)

    # -- entanglement entropy (per-residue via hop-radius-1 neighbourhoods) --
    A = contact_matrix(coords, cutoff=cutoff, weight="binary")
    from scipy.sparse.csgraph import shortest_path
    hop_dist = shortest_path(A.astype(float), method="D", unweighted=True, directed=False)
    t_star = natural_coherent_time(H_new)
    neighborhoods_r1 = hop_radius_neighborhoods(hop_dist, radius=1)
    out["entanglement_entropy"] = entanglement_entropy_mixture(H_new, source, neighborhoods_r1, t_star)

    # -- GNM transfer entropy --
    out["transfer_entropy"] = transfer_entropy_source_score(coords, cutoff=cutoff)

    # -- persistent H2 void score --
    out["void_score"] = void_score(coords)

    # -- residue conformational entropy (ensemble/entropic, TASK-0166) --
    out["conformational_entropy"] = residue_conformational_entropy(coords, cutoff=cutoff)

    # -- binding-response coupling specificity (TASK-0178) --
    K = laplacian(contact_matrix(coords, cutoff=cutoff, weight="binary"))
    profile = coupling_profile(K, source, coords, kappa=RESPONSE_KAPPA, patch_size=RESPONSE_PATCH_SIZE)
    hop = -hop_from_seed(coords, source, cutoff=cutoff)
    out["coupling_specificity"] = coupling_specificity(profile, hop)

    return out


def align_and_stack(observables: dict) -> tuple:
    """Assert every vector has the same length (the common residue-index
    alignment this task's own Constraint requires -- every observable
    above is computed on the same `coords`/`N` for one target, so this is
    a real assertion, not a silent assumption)."""
    names = sorted(observables.keys())
    lengths = {name: len(observables[name]) for name in names}
    n_unique = set(lengths.values())
    if len(n_unique) != 1:
        raise ValueError(f"misaligned observable lengths: {lengths}")
    matrix = np.column_stack([observables[name] for name in names])  # (N, M)
    return names, matrix


def correlation_matrix_and_rank(matrix: np.ndarray) -> dict:
    """Spearman correlation matrix across columns (observables), its
    eigenvalue spectrum, and every effective-rank statistic this task's
    own pre-registration names."""
    corr, _p = spearmanr(matrix)
    corr = np.atleast_2d(corr)
    eigenvalues = np.linalg.eigvalsh(corr)
    eigenvalues = np.clip(eigenvalues, 0, None)  # numerical noise guard, correlation matrices are PSD
    return {
        "corr_matrix": corr, "eigenvalues": eigenvalues,
        "participation_ratio_rank": participation_ratio_rank(eigenvalues),
        "eff_rank_entropy": eff_rank(eigenvalues),
        "variance_explained_90": variance_explained_count(eigenvalues, 0.90),
        "variance_explained_95": variance_explained_count(eigenvalues, 0.95),
        "M": matrix.shape[1],
    }


def confound_projection(names: list, matrix: np.ndarray, coords: np.ndarray, source) -> dict:
    """Project -hop/-euclid into the same space: append them as two more
    columns, recompute the correlation matrix + PC1, report where hop/
    euclid land on PC1 relative to the real observables -- the
    interpretive payload this task's own In-Scope names."""
    hop = -hop_from_seed(coords, source)
    euclid = -euclid_from_seed_centroid(coords, source)
    extended_names = names + ["neg_hop", "neg_euclid"]
    extended_matrix = np.column_stack([matrix, hop, euclid])

    corr, _p = spearmanr(extended_matrix)
    corr = np.atleast_2d(corr)
    eigenvalues, eigenvectors = np.linalg.eigh(corr)
    order = np.argsort(eigenvalues)[::-1]
    pc1_loadings = eigenvectors[:, order[0]]

    loadings_by_name = dict(zip(extended_names, pc1_loadings.tolist()))
    real_obs_loadings = np.array([abs(loadings_by_name[n]) for n in names])
    return {
        "pc1_loadings": loadings_by_name,
        "hop_abs_loading": abs(loadings_by_name["neg_hop"]),
        "euclid_abs_loading": abs(loadings_by_name["neg_euclid"]),
        "real_observable_mean_abs_loading": float(real_obs_loadings.mean()),
        "real_observable_max_abs_loading": float(real_obs_loadings.max()),
        "hop_percentile_among_real_observables": float(
            (real_obs_loadings < abs(loadings_by_name["neg_hop"])).mean() * 100
        ),
    }


def run_controls(matrix: np.ndarray) -> dict:
    """Planned Validation: positive control (inject a duplicate + an
    orthogonal random column into THIS target's own real observable
    matrix) and negative control (N random columns -> rank ~= N, a
    separate, controlled synthetic check in
    `tests/test_observable_effective_rank.py`, not repeated here).

    **Real-data caveat, found while running this, not assumed**: the
    textbook "adding one orthogonal dimension raises participation rank
    by ~1" intuition holds cleanly only for a near-uniform base spectrum.
    On this project's own real, highly-skewed matrix (one dominant
    component, per the Headline finding), the exact formula
    `PR = (sum(lambda))^2/sum(lambda^2)` predicts a much smaller marginal
    increase when one huge eigenvalue already dominates `sum(lambda^2)`
    -- verified directly (KRAS_G12C: +0.20, not ~+1, and hand-computing
    the formula with the new eigenvalue set reproduces that number to
    2 decimal places, confirmed not a bug). The control below therefore
    checks **direction and a minimum meaningful magnitude** (rank must
    rise measurably for an orthogonal addition, must not rise for a
    duplicate), not a fixed +1 window -- the strict, textbook-clean +1
    check is run instead on a controlled synthetic (near-uniform) matrix
    in this task's own test file, where the textbook intuition actually
    applies.
    """
    rng = np.random.default_rng(0)
    n = matrix.shape[0]
    base_rank = correlation_matrix_and_rank(matrix)["participation_ratio_rank"]

    duplicate_matrix = np.column_stack([matrix, matrix[:, 0]])
    duplicate_rank = correlation_matrix_and_rank(duplicate_matrix)["participation_ratio_rank"]

    random_col = rng.normal(size=n)
    random_matrix = np.column_stack([matrix, random_col])
    random_rank = correlation_matrix_and_rank(random_matrix)["participation_ratio_rank"]

    return {
        "base_rank": base_rank,
        "duplicate_rank": duplicate_rank,
        "duplicate_delta": duplicate_rank - base_rank,
        "random_rank": random_rank,
        "random_delta": random_rank - base_rank,
        "duplicate_control_ok": duplicate_rank <= base_rank + 0.15,
        "random_control_ok": (random_rank - base_rank) > 0.05,
    }


def run_target(target_name: str) -> dict:
    _log(f"{target_name}: preparing (fetch + clean + labels)...")
    t0 = time.monotonic()
    prep = _prepare_target(target_name)
    _log(f"{target_name}: prepared in {time.monotonic() - t0:.1f}s (N={prep['n_residues']})")

    _log(f"{target_name}: computing all observables...")
    t0 = time.monotonic()
    observables = compute_all_observables(prep)
    _log(f"{target_name}: {len(observables)} observables computed in {time.monotonic() - t0:.1f}s")

    names, matrix = align_and_stack(observables)
    rank_report = correlation_matrix_and_rank(matrix)
    confound = confound_projection(names, matrix, prep["coords"], prep["source"])
    controls = run_controls(matrix)

    _log(
        f"{target_name}: M={rank_report['M']} participation_ratio_rank={rank_report['participation_ratio_rank']:.2f} "
        f"eff_rank_entropy={rank_report['eff_rank_entropy']:.2f} var90={rank_report['variance_explained_90']} "
        f"hop_percentile_on_PC1={confound['hop_percentile_among_real_observables']:.1f}"
    )

    return {
        "target": target_name, "n_residues": prep["n_residues"], "observable_names": names,
        "rank_report": {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in rank_report.items()},
        "confound_projection": confound,
        "controls": controls,
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    for target in TARGETS_PRIMARY + TARGETS_EXTRA:
        try:
            results[target] = run_target(target)
        except Exception as exc:
            results[target] = {"target": target, "error": str(exc)}
            _log(f"{target}: FAILED -- {exc!r}")
        with open(OUTPUT_DIR / "observable_effective_rank.json", "w") as f:
            json.dump(results, f, indent=2)

    _log(f"wrote {OUTPUT_DIR / 'observable_effective_rank.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
