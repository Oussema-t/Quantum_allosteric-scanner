"""Phase 4 -- current-flow / edge-propensity pathway extraction.

Adapts ProteinLens's bond-to-bond current-flow propensity readout
(`ALGORITHM_REGISTER.md` SS F: "adopt the readout, not the all-atom graph")
onto this package's existing Ca contact graph / transport operator H, not a
new all-atom graph.

`H`'s off-diagonal magnitude is treated as a resistor-network conductance
and a fresh graph Laplacian is rebuilt from it (`hamiltonians.py`'s own
module docstring: PSD operators use the Laplacian convention, indefinite
ones use adjacency -- `abs(H_ij)` is conductance either way). All of
`potentials.py`'s V_B/V_T/V_R/V_C/V_M terms are diagonal-only (confirmed by
reading that module while writing this one), so H_new's off-diagonal
structure is identical to the bare contact graph's -- the potential terms
never distort the conductance network this module builds, whichever H a
caller passes in.

Node potentials are then solved via the Moore-Penrose pseudo-inverse of
that Laplacian -- the standard current-flow-betweenness construction
(Newman 2005), not a new physics model.

Leakage boundary: like `analysis.py`, every function here takes an
already-derived operator H plus plain node indices -- none of them touch a
holo structure directly, so this module carries no FROZEN-path obligation
of its own (this task's Constraints And Invariants).
"""
from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# Shared conductance-network construction
# ---------------------------------------------------------------------------

def _conductance_laplacian(H: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Rebuild a resistor-network graph Laplacian from H's off-diagonal
    structure. Returns (L, W): W is the symmetric non-negative conductance
    matrix (`abs(H_ij)`, i != j), L = diag(W.sum(axis=1)) - W."""
    W = np.abs(np.asarray(H, dtype=float))
    np.fill_diagonal(W, 0.0)
    L = np.diag(W.sum(axis=1)) - W
    return L, W


def _source_indices(source) -> np.ndarray:
    """Normalise a scalar or sequence `source` into a 1-D int index array
    (mirrors propagators.py's convention: a multi-index source is a
    uniform mass split over those nodes, not a scalar reduction of one)."""
    return np.atleast_1d(np.asarray(source, dtype=int))


def _edge_currents(W: np.ndarray, phi: np.ndarray) -> dict[tuple[int, int], float]:
    """Undirected edge-current magnitude |W_ij * (phi_i - phi_j)| for every
    edge (i < j) present in the conductance graph."""
    ii, jj = np.nonzero(np.triu(W, k=1))
    return {
        (int(i), int(j)): float(W[i, j] * abs(phi[i] - phi[j]))
        for i, j in zip(ii.tolist(), jj.tolist())
    }


# ---------------------------------------------------------------------------
# edge_propensity -- single-source current-flow edge importance
# ---------------------------------------------------------------------------

def edge_propensity(H: np.ndarray, source=0) -> dict[tuple[int, int], float]:
    """Current-flow edge importance from `source`.

    One unit of current is injected at `source` (split uniformly across a
    multi-index source) and extracted uniformly across every other node --
    a single linear solve via the Laplacian pseudo-inverse, not one solve
    per possible sink. This is what makes an edge "on the way out of
    source's neighbourhood generally" score high without needing to name a
    target pocket in advance -- exactly the ranking signal a pocket
    predictor needs before it knows which residues are the pocket.

    Returns {(i, j): propensity} for every edge (i < j) in H's conductance
    graph, non-negative. A bridge edge separating `source`'s side of the
    graph from the rest scores highest, since nearly all of the extracted
    current must cross it.
    """
    N = H.shape[0]
    L, W = _conductance_laplacian(H)
    idx = _source_indices(source)

    sinks = np.setdiff1d(np.arange(N), idx)
    if len(sinks) == 0:
        return {}

    b = np.zeros(N)
    b[idx] = 1.0 / len(idx)
    b[sinks] -= 1.0 / len(sinks)

    Lp = np.linalg.pinv(L, hermitian=True)
    phi = Lp @ b
    return _edge_currents(W, phi)


# ---------------------------------------------------------------------------
# extract_pathway -- two-terminal current-flow path trace
# ---------------------------------------------------------------------------

def extract_pathway(H: np.ndarray, source, target: int, max_hops: int | None = None) -> dict:
    """Trace the dominant current-flow path from `source` to `target`.

    One unit of current is injected at `source` and extracted at `target`;
    node potentials come from the same pseudo-inverse construction as
    `edge_propensity`. The path is then a greedy walk that, from the
    current node, always steps to the unvisited neighbour receiving the
    largest positive current (current flows high- to low-potential; ties
    go to the lowest node index for determinism), stopping at `target` or
    when no unvisited outgoing edge remains.

    Returns
    -------
    dict with:
      "nodes"          : the traced node sequence, source first.
      "edges"          : the (i, j) edges walked, in order.
      "reached_target" : whether the walk actually arrived at `target`.
      "propensity"     : {(i, j): float} edge-current magnitudes over the
                          *whole* graph for this source/target pair (same
                          shape as `edge_propensity`'s output) -- for
                          viz.py (TASK-0014) to render the full field
                          alongside the traced path, not just the path
                          itself.
    """
    N = H.shape[0]
    idx = _source_indices(source)
    if target in idx.tolist():
        raise ValueError("target must not coincide with source")

    L, W = _conductance_laplacian(H)

    b = np.zeros(N)
    b[idx] = 1.0 / len(idx)
    b[target] -= 1.0

    Lp = np.linalg.pinv(L, hermitian=True)
    phi = Lp @ b
    propensity = _edge_currents(W, phi)

    max_hops = N if max_hops is None else max_hops
    start = int(idx[0])
    visited = set(idx.tolist())
    nodes = [start]
    edges: list[tuple[int, int]] = []
    current = start
    reached = current == target

    while not reached and len(nodes) <= max_hops:
        neighbours = np.nonzero(W[current])[0]
        best_j, best_flow = None, 0.0
        for j in neighbours.tolist():
            if j in visited:
                continue
            flow = W[current, j] * (phi[current] - phi[j])
            if flow > best_flow:
                best_flow = flow
                best_j = j
        if best_j is None:
            break
        edges.append((current, best_j))
        nodes.append(best_j)
        visited.add(best_j)
        current = best_j
        reached = current == target

    return {
        "nodes": nodes,
        "edges": edges,
        "reached_target": reached,
        "propensity": propensity,
    }


# ---------------------------------------------------------------------------
# TASK-0079.002 -- dense N x N connectivity matrix (submission deliverable)
# ---------------------------------------------------------------------------

def edge_propensity_to_matrix(propensity: dict, n: int) -> np.ndarray:
    """Dense `(n, n)` symmetric connectivity matrix from `edge_propensity`'s
    half-matrix dict -- the "N x N connectivity matrix" submission
    deliverable (`EXECUTION_PLAN.md` Phase 5.1).

    `propensity` must match `edge_propensity`'s own contract exactly
    (`SEAM-0006`, closed `VERIFIED`): `{(i, j): float}` for `i < j` only
    (undirected, half the matrix), both indices `< n`, non-negative.
    Any violation -- `i >= j`, an out-of-range index, a non-integer key, a
    negative value -- raises rather than being silently clipped or
    ignored, matching this codebase's "raise, don't repair" convention
    for structural invariants (`INVARIANCE_PROTOCOL.md` Tier 1: "never
    select by index... raise, do not slice"). Mirrors `viz.py`'s own
    `_validate_edge_propensity` checks (not re-derived independently --
    same contract, checked inline here rather than importing a `viz.py`
    private helper into a lower-layer module).

    Returns an `(n, n)` float array: `M[i, j] == M[j, i]` for every edge
    present, `0.0` elsewhere (including the diagonal) -- absence of an
    edge in the conductance graph, not missing data, so `0.0` rather than
    `NaN` is the correct fill value.
    """
    M = np.zeros((n, n), dtype=float)
    for key, value in propensity.items():
        if not (isinstance(key, tuple) and len(key) == 2):
            raise TypeError(f"edge_propensity key {key!r} is not an (i, j) tuple")
        i, j = key
        if not (isinstance(i, (int, np.integer)) and isinstance(j, (int, np.integer))):
            raise TypeError(f"edge_propensity key {key!r} must be a pair of ints")
        if not (0 <= i < n and 0 <= j < n):
            raise ValueError(f"edge_propensity key {key!r} out of range for n={n}")
        if not (i < j):
            raise ValueError(
                f"edge_propensity key {key!r} violates the i < j (undirected, "
                "half-matrix) convention this module's own docstring specifies"
            )
        if value < 0:
            raise ValueError(f"edge_propensity[{key!r}] = {value} is negative")
        M[i, j] = float(value)
        M[j, i] = float(value)
    return M
