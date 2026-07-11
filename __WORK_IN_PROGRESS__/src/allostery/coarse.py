"""Phase 4 -- coarse-graining (community detection) and Trotter/qubit cost
estimation, feeding the NISQ noise study (`ALGORITHM_REGISTER.md` SS H:
"the actual scoreable NISQ result").

Shrinks a ~150-300 residue contact graph down to the N <= ~12-16 node
budget that study needs, while preserving transport-relevant structure,
then estimates the circuit depth / 2-qubit gate count for Trotterizing
`e^{-iHt}` on the result at a target error tolerance -- the "Feasibility"
half of the challenge rubric (`PLAN-01.07.26.md`).

Apo-computable boundary: like `pathways.py`/`analysis.py`, every function
here takes an already-derived operator `H` plus plain arrays -- none of
them touch a holo structure or a pocket label. `H`'s off-diagonal
magnitude is treated as the graph weight (same `abs(H_ij)`, i != j
convention as `pathways.py::_conductance_laplacian` -- ported locally
here rather than cross-importing that module's private helper, same
"port, don't couple to another module's internals" convention TASK-0005
used for `backend/geometry.py`). This means coarse-graining is
structurally incapable of using holo information *as long as the caller
passes an apo-derived H* -- this module cannot itself verify that
precondition (this task's own Constraint), so it stays the caller's
obligation, same as every other H-consuming module in this package.

No new dependency: Louvain community detection is networkx's own
`algorithms.community.louvain_communities` (built in since networkx>=3.x,
confirmed present in this venv), and spectral clustering is
`sklearn.cluster.SpectralClustering` (sklearn is already a dependency --
`metrics.py::auc` uses `sklearn.metrics.roc_auc_score`).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


# ---------------------------------------------------------------------------
# Shared graph-weight extraction (see module docstring for the convention)
# ---------------------------------------------------------------------------

def _graph_weights(H: np.ndarray) -> np.ndarray:
    """Symmetric non-negative edge-weight matrix from H's off-diagonal
    magnitude -- ignores whatever's on the diagonal (potential terms,
    degree, ...), since community structure and gate count are properties
    of the *coupling* graph, not the on-site energy."""
    W = np.abs(np.asarray(H, dtype=float))
    np.fill_diagonal(W, 0.0)
    return W


def _relabel_contiguous(labels: np.ndarray) -> np.ndarray:
    """Remap arbitrary cluster ids to a contiguous 0..n_clusters-1 range,
    in order of first appearance (deterministic given `labels`' order)."""
    remap: dict[int, int] = {}
    out = np.empty(len(labels), dtype=int)
    for i, c in enumerate(labels.tolist()):
        if c not in remap:
            remap[c] = len(remap)
        out[i] = remap[c]
    return out


# ---------------------------------------------------------------------------
# coarse_grain -- Louvain / spectral community detection to a node budget
# ---------------------------------------------------------------------------

@dataclass
class CoarseGrainResult:
    labels: np.ndarray       # (N,) cluster id per original node, 0..n_clusters-1
    n_clusters: int
    H_coarse: np.ndarray     # (n_clusters, n_clusters) coarse-grained weighted graph


def coarse_grain(
    H: np.ndarray,
    method: str = "louvain",
    n_target: int = 12,
    seed: int | None = 0,
) -> CoarseGrainResult:
    """Partition H's N nodes down to (at most) `n_target` clusters.

    method="louvain" runs modularity-maximizing community detection, then
    -- since Louvain has no direct node-count knob -- greedily merges the
    two most strongly-coupled clusters (by total inter-cluster edge
    weight) until the count is at or below `n_target`, if Louvain's
    natural partition has more communities than that. This is a
    best-effort node budget for Louvain, not an exact one; `n_clusters` in
    the result is always the true final count, which may be below
    `n_target` if Louvain found fewer communities natively.

    method="spectral" uses `sklearn.cluster.SpectralClustering` with
    `n_clusters=n_target` directly -- exact for this method.

    `H_coarse` is the coarse-grained weighted graph: `H_coarse[a, b]` is
    the summed original edge weight crossing from cluster a to cluster b
    (0 on the diagonal -- gate-count estimation cares about inter-cluster
    coupling terms, not an intra-cluster self-energy convention this task
    doesn't need to pick).
    """
    W = _graph_weights(H)
    N = W.shape[0]

    if n_target >= N:
        labels = np.arange(N)
        return CoarseGrainResult(labels=labels, n_clusters=N, H_coarse=W.copy())

    if method == "louvain":
        labels = _louvain_partition(W, n_target, seed=seed)
    elif method == "spectral":
        labels = _spectral_partition(W, n_target, seed=seed)
    else:
        raise ValueError(f"Unknown method '{method}', expected 'louvain' or 'spectral'")

    n_clusters = int(labels.max()) + 1 if len(labels) else 0
    H_coarse = _coarsen_graph(W, labels, n_clusters)
    return CoarseGrainResult(labels=labels, n_clusters=n_clusters, H_coarse=H_coarse)


def _louvain_partition(W: np.ndarray, n_target: int, seed: int | None) -> np.ndarray:
    import networkx as nx
    from networkx.algorithms.community import louvain_communities

    G = nx.from_numpy_array(W)
    communities = louvain_communities(G, weight="weight", seed=seed)

    labels = np.empty(W.shape[0], dtype=int)
    for cid, community in enumerate(communities):
        for node in community:
            labels[node] = cid

    if len(communities) > n_target:
        labels = _merge_to_target(W, labels, len(communities), n_target)
    return _relabel_contiguous(labels)


def _spectral_partition(W: np.ndarray, n_target: int, seed: int | None) -> np.ndarray:
    from sklearn.cluster import SpectralClustering

    model = SpectralClustering(
        n_clusters=n_target,
        affinity="precomputed",
        random_state=seed,
        assign_labels="kmeans",
    )
    return _relabel_contiguous(model.fit_predict(W))


def _merge_to_target(W: np.ndarray, labels: np.ndarray, n_current: int, n_target: int) -> np.ndarray:
    """Greedily merge the two clusters joined by the largest total
    inter-cluster edge weight, repeatedly, until `n_current == n_target`."""
    labels = labels.copy()
    N = W.shape[0]
    while n_current > n_target:
        ids = np.unique(labels)
        idx_map = {int(c): i for i, c in enumerate(ids)}
        M = len(ids)
        C = np.zeros((M, M))
        for i in range(N):
            for j in range(i + 1, N):
                if W[i, j] > 0 and labels[i] != labels[j]:
                    a, b = idx_map[int(labels[i])], idx_map[int(labels[j])]
                    C[a, b] += W[i, j]
                    C[b, a] += W[i, j]

        np.fill_diagonal(C, -1.0)
        a, b = np.unravel_index(np.argmax(C), C.shape)
        if C[a, b] <= 0:
            # no inter-cluster edge at all left (a disconnected remainder)
            # -- merge the two smallest clusters instead, so the node
            # budget is still honoured even for a disconnected graph.
            sizes = [int((labels == c).sum()) for c in ids]
            order = np.argsort(sizes)
            a, b = int(order[0]), int(order[1])

        labels[labels == ids[b]] = ids[a]
        n_current -= 1
    return labels


def _coarsen_graph(W: np.ndarray, labels: np.ndarray, n_clusters: int) -> np.ndarray:
    H_coarse = np.zeros((n_clusters, n_clusters))
    N = W.shape[0]
    for i in range(N):
        for j in range(i + 1, N):
            if W[i, j] > 0 and labels[i] != labels[j]:
                a, b = int(labels[i]), int(labels[j])
                H_coarse[a, b] += W[i, j]
                H_coarse[b, a] += W[i, j]
    return H_coarse


# ---------------------------------------------------------------------------
# trotter_cost -- first-order Trotter-Suzuki circuit-cost estimate
# ---------------------------------------------------------------------------

@dataclass
class TrotterCostResult:
    n_qubits: int
    n_terms: int
    trotter_steps: int
    circuit_depth: int
    two_qubit_gates: int
    energy_scale: float


def trotter_cost(H: np.ndarray, t: float = 1.0, error_budget: float = 0.01) -> TrotterCostResult:
    """Estimated first-order Trotter-Suzuki cost for `e^{-iHt}` on a
    graph-encoded qubit register (one qubit per node, one 2-qubit gate per
    coupling edge), at a target error tolerance `error_budget`.

    Uses the standard first-order Trotter error bound
    `epsilon <~ (t^2 / (2r)) * sum_{i<j} ||[H_i, H_j]||` (Trotter 1959 /
    Suzuki), approximating each pairwise commutator norm by
    `energy_scale^2` (the largest coupling magnitude in the graph) rather
    than computing exact operator commutators -- an estimate, documented
    as such, not an exact bound. Solving for the step count `r` at the
    given `error_budget`:

        r ~= ceil(t^2 * n_terms * energy_scale^2 / (2 * error_budget))

    `circuit_depth` further multiplies by `max_degree + 1` -- an upper
    bound (Vizing's theorem) on how many parallel gate layers a single
    Trotter step needs to schedule every coupling edge without two gates
    sharing a qubit.

    Monotonicity (this task's own Planned Validation): smaller
    `error_budget` -> larger `r` -> larger `circuit_depth`/
    `two_qubit_gates`, strictly, whenever the graph has at least one edge.
    """
    if error_budget <= 0:
        raise ValueError("error_budget must be positive")
    if t < 0:
        raise ValueError("t must be non-negative")

    W = _graph_weights(H)
    N = W.shape[0]
    ii, jj = np.nonzero(np.triu(W, k=1))
    n_terms = len(ii)
    energy_scale = float(W.max()) if n_terms else 0.0

    if n_terms == 0 or energy_scale == 0.0 or t == 0.0:
        trotter_steps = 1
    else:
        trotter_steps = max(
            1,
            int(np.ceil((t ** 2) * n_terms * energy_scale ** 2 / (2.0 * error_budget))),
        )

    degree = (W > 0).sum(axis=1)
    max_degree = int(degree.max()) if N else 0
    layers_per_step = max(1, max_degree + 1) if n_terms else 1

    return TrotterCostResult(
        n_qubits=N,
        n_terms=n_terms,
        trotter_steps=trotter_steps,
        circuit_depth=trotter_steps * layers_per_step,
        two_qubit_gates=trotter_steps * n_terms,
        energy_scale=energy_scale,
    )
