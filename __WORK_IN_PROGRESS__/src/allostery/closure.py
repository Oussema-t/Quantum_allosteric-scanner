"""TASK-0143 -- coordinated-closure graph-openness premise (HYP-P10).

Tests whether real holo-defined cryptic-pocket residues are Euclidean-near
but graph-hop-far on the *apo* contact graph -- the "open cleft" signature
the multi-site-closure observable family (HYP-P9/P10/P12) depends on.

**Distinct from `superpose.cryptic_openness_gate`/`cumulative_overlap`**
([[TASK-0059]]/[[TASK-0120]]): that gate is a *dynamics* question (is the
apo->holo displacement spanned by the soft ANM modes). This module asks an
orthogonal *structural-graph* question about the apo state alone -- no
holo coordinates or ANM modes enter any computation here, only the apo
contact graph and the holo-defined pocket *label* (which residues, not how
they move). Confirmed distinct by construction, not by assumption: this
module never imports `superpose`.
"""
from __future__ import annotations

import numpy as np

from .hamiltonians import contact_matrix


def graph_dist_matrix(coords: np.ndarray, cutoff: float = 8.0) -> np.ndarray:
    """All-pairs shortest-path (hop-count) distance on the binary apo
    contact graph, (N, N), same `cutoff` convention as `H_new`'s own input
    (`targets.yaml`'s `enm_cutoff`, default 8.0 A).

    BFS from every node (`networkx.all_pairs_shortest_path_length`), not
    Floyd-Warshall -- O(N*(N+E)) on this graph's sparse ~8-15 neighbors/
    node is far cheaper than Floyd-Warshall's O(N^3) at CARDIAC_MYOSIN's
    scale (N~950), and both give the exact same unweighted-graph answer.

    Raises `ValueError` if the apo contact graph is disconnected at this
    cutoff -- an undefined "mean pairwise hop distance" for any pair
    spanning components, not something to silently paper over with a
    penalty value (unlike `baselines.hop_from_seed`'s `n+1` convention,
    which has a well-defined single-source use; this function's all-pairs
    output has no such fallback semantics).
    """
    import networkx as nx

    n = len(coords)
    A = contact_matrix(coords, cutoff=cutoff, weight="binary")
    G = nx.from_numpy_array(A)
    if not nx.is_connected(G):
        n_components = nx.number_connected_components(G)
        raise ValueError(
            f"graph_dist_matrix: apo contact graph is disconnected at cutoff={cutoff} "
            f"({n_components} components) -- mean pairwise hop distance is undefined "
            "for residue pairs spanning components"
        )

    GD = np.zeros((n, n), dtype=float)
    for i, lengths in nx.all_pairs_shortest_path_length(G):
        for j, d in lengths.items():
            GD[i, j] = d
    return GD


def euclid_dist_matrix(coords: np.ndarray) -> np.ndarray:
    """All-pairs Euclidean distance, (N, N)."""
    diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
    return np.sqrt((diff ** 2).sum(axis=2))


def _mean_pairwise(idx: np.ndarray, M: np.ndarray) -> float:
    """Mean of `M[i, j]` over all unordered pairs `i < j` within `idx`.
    `idx` must have at least 2 elements -- a single residue has no pairwise
    distance, by construction, not a degenerate 0/0 case to paper over."""
    idx = np.asarray(idx, dtype=int)
    if len(idx) < 2:
        raise ValueError(f"_mean_pairwise: need >=2 residues, got {len(idx)}")
    sub = M[np.ix_(idx, idx)]
    iu = np.triu_indices(len(idx), k=1)
    return float(sub[iu].mean())


def pairwise_components(residues: np.ndarray, D_euclid: np.ndarray, GD: np.ndarray) -> dict:
    """The two raw numbers `openness_signature` divides into a single ratio:
    mean pairwise apo graph-hop distance and mean pairwise Euclidean
    distance among `residues`, each on its own. The ratio alone collapses
    two different-shaped anomalies into one number -- 11.57 A / 2.4 hops
    and 40 A / ~8 hops can land on similar ratios but describe physically
    different situations, and for a target where `matched_spread_null`
    itself is infeasible (no percentile/p available) these are the only
    real, reportable numbers left. Always computable independent of the
    null -- no rejection sampling here."""
    return {
        "graph_hop_mean": _mean_pairwise(residues, GD),
        "euclid_mean": _mean_pairwise(residues, D_euclid),
    }


def openness_signature(residues: np.ndarray, D_euclid: np.ndarray, GD: np.ndarray) -> float:
    """HYP-P10's own defining ratio: mean pairwise apo graph-hop distance
    divided by mean pairwise Euclidean distance, among `residues` (a set
    of residue indices, e.g. the holo-defined pocket). High values mean
    "close in 3D space, far on the apo contact graph" -- the coordinated-
    closure/open-cleft signature this task tests for."""
    c = pairwise_components(residues, D_euclid, GD)
    return c["graph_hop_mean"] / c["euclid_mean"]


def matched_spread_null(
    residues: np.ndarray,
    D_euclid: np.ndarray,
    GD: np.ndarray,
    *,
    n_null: int = 500,
    tol: float = 0.35,
    seed: int = 0,
    max_attempts: int = 200_000,
) -> dict:
    """The matched-Euclidean-spread random-closure null this task's own
    Constraints demand: >= `n_null` random same-size residue sets whose
    mean pairwise Euclidean spread is within `+/- tol` of the real
    pocket's, scored with the same `openness_signature`. Matching on
    spread isolates "far on the graph *given* this much spatial spread"
    from plain compactness (an unmatched null would just re-detect that
    compact clusters tend to be graph-close, unrelated to HYP-P10's claim).

    Rejection sampling, not a closed-form draw -- the space of same-size
    subsets with matching spread has no simple parametrization. Raises
    `RuntimeError` (not a silent short-count return) if `max_attempts` is
    exhausted before `n_null` acceptances -- a real, reportable
    infeasibility (e.g. a target where almost no same-size subset matches
    the real pocket's spread), not something to average over silently.
    """
    residues = np.asarray(residues, dtype=int)
    k = len(residues)
    n = D_euclid.shape[0]
    real_components = pairwise_components(residues, D_euclid, GD)
    real_spread = real_components["euclid_mean"]
    real_signature = real_components["graph_hop_mean"] / real_components["euclid_mean"]
    lo, hi = real_spread * (1.0 - tol), real_spread * (1.0 + tol)

    rng = np.random.default_rng(seed)
    null_signatures = []
    n_attempts = 0
    while len(null_signatures) < n_null and n_attempts < max_attempts:
        n_attempts += 1
        candidate = rng.choice(n, size=k, replace=False)
        spread = _mean_pairwise(candidate, D_euclid)
        if lo <= spread <= hi:
            null_signatures.append(openness_signature(candidate, D_euclid, GD))

    if len(null_signatures) < n_null:
        raise RuntimeError(
            f"matched_spread_null: only {len(null_signatures)}/{n_null} matched-spread "
            f"replicates found in {n_attempts} attempts (spread window [{lo:.2f}, {hi:.2f}] "
            f"A around real_spread={real_spread:.2f} A) -- the null is infeasible at this "
            "tolerance, not silently under-powered"
        )

    null_arr = np.array(null_signatures)
    percentile = float((null_arr < real_signature).sum()) / len(null_arr) * 100.0
    p_one_sided = float((null_arr >= real_signature).sum()) / len(null_arr)
    return {
        "real_signature": real_signature,
        "real_spread": real_spread,
        "real_graph_hop_mean": real_components["graph_hop_mean"],
        "real_euclid_mean": real_components["euclid_mean"],
        "n_null": len(null_signatures),
        "n_attempts": n_attempts,
        "null_signatures": null_signatures,
        "null_median": float(np.median(null_arr)),
        "null_sd": float(np.std(null_arr)),
        "percentile": percentile,
        "p_one_sided": p_one_sided,
    }
