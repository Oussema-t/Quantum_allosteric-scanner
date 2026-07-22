"""TASK-0136 -- path-ensemble + percolation connectivity between two
residue sets on the apo contact graph.

Purely topological (no propagator, no `t_max`, no seed coherence, no
clock) -- the deliberate structural complement to CTQW/GSR/ENAQT, per this
task's own Out Of Scope. Models the distinction between a **narrow,
fragile bottleneck** (one dominant channel, low edge-connectivity) and a
**broad, redundant subnetwork** (many independent routes, high edge-
connectivity) between two known residue sets -- the same bottleneck-vs-
distributed question Chennubhotla & Bahar's correlation-network path
analysis and Nussinov & Tsai's ensemble-allostery framing both hinge on
(both cited in the challenge statement itself).

**Correction to this task's own filing, checked not assumed**: the task
text cites "`potentials.py`'s existing `W_invdist`-style weighting" --
`potentials.py` has no such thing (grepped directly, zero matches). The
actual existing invdist-style weighting is `hamiltonians.contact_matrix(
weight="invdist")` (`W[i,j] = 1/(dist+eps)` within `cutoff`, 0 otherwise)
-- reused here, not reinvented, just from the correct module.
"""
from __future__ import annotations

import numpy as np

from .hamiltonians import contact_matrix

_EPS = 1e-6
_SUPER_SOURCE = "__source__"
_SUPER_SINK = "__sink__"


def _source_indices(source) -> np.ndarray:
    return np.atleast_1d(np.asarray(source, dtype=int))


def _weighted_graph(coords: np.ndarray, cutoff: float):
    """The apo contact graph with Dijkstra-ready edge weights: `weight =
    1/W_invdist = dist + eps` on every edge within `cutoff` -- a strong
    (close) contact is *cheap* to traverse, a weak (far, but still within
    cutoff) contact is *costly*, so a weighted shortest path preferentially
    routes through strong contacts rather than treating every edge in the
    binary contact graph as equally traversable."""
    import networkx as nx

    W = contact_matrix(coords, cutoff=cutoff, weight="invdist")
    G = nx.Graph()
    G.add_nodes_from(range(len(coords)))
    rows, cols = np.nonzero(np.triu(W, k=1))
    for i, j in zip(rows.tolist(), cols.tolist()):
        G.add_edge(i, j, weight=1.0 / W[i, j], strength=float(W[i, j]))
    return G


def _with_virtual_endpoints(G, source_idx: np.ndarray, target_idx: np.ndarray):
    """Returns a copy of `G` with two virtual nodes added: `_SUPER_SOURCE`
    connected (zero-weight) to every `source_idx` residue, `_SUPER_SINK`
    connected likewise to every `target_idx` residue -- the standard
    reduction of "shortest path / min-cut between two node SETS" to
    "between two single nodes" (Dijkstra/Menger's theorem both require
    single endpoints).

    **Real bug, found and fixed while validating the first real-target
    run (not assumed correct from the construction alone)**: an earlier
    version gave each virtual edge unit capacity, reasoning that "a
    3-residue active site cannot originate more than 3 edge-disjoint
    paths." That reasoning is wrong -- a *single* residue can itself be
    the fan-out point for several edge-disjoint routes through its own
    distinct real graph edges (confirmed directly: a synthetic 1-hub/
    3-target check gives true edge-connectivity 3 from one source node,
    not the unit-capacity construction's forced 1). Unit-capacity virtual
    edges silently capped every reported connectivity at
    `min(len(source_idx), len(target_idx))` regardless of the real
    graph's own structure -- exactly what the first real KRAS_G12C/
    BCR_ABL1/CARDIAC_MYOSIN run showed (connectivity saturating at the
    smaller set's size on all 3, with an empty min-cut, i.e. the reported
    "bottleneck" was this function's own virtual edges, not real graph
    structure). Fixed: virtual edges get a large `capacity` attribute
    (`len(G)`, comfortably larger than any real max-flow achievable
    through this graph's own bounded-degree structure) so the min-cut is
    always determined by the real, internal contact-graph edges (`capacity
    =1` each, Menger's-theorem route counting) -- never by this
    construction's own bookkeeping."""
    H = G.copy()
    big_capacity = float(len(G) + 1)
    for u, v in H.edges():
        H[u][v]["capacity"] = 1.0
    H.add_node(_SUPER_SOURCE)
    H.add_node(_SUPER_SINK)
    for i in source_idx.tolist():
        H.add_edge(_SUPER_SOURCE, i, weight=0.0, strength=np.inf, capacity=big_capacity)
    for j in target_idx.tolist():
        H.add_edge(_SUPER_SINK, j, weight=0.0, strength=np.inf, capacity=big_capacity)
    return H


def shortest_path_ensemble(
    coords: np.ndarray,
    source,
    target,
    cutoff: float = 10.0,
    *,
    tol: float = 0.10,
    max_paths: int = 50,
) -> dict:
    """Weighted shortest path (Dijkstra, edge weight = inverse contact
    strength) between the `source` residue set and the `target` residue
    set on the apo contact graph, plus a **sub-optimal path ensemble**:
    every path found (via `networkx.shortest_simple_paths`'s Yen's-
    algorithm ordering, cheapest first) whose total weight is within
    `+/- tol` (fractional) of the true shortest path's -- a single geodesic
    is an arbitrary pick among near-ties, per this task's own reasoning.

    `tol=0.10` (10% above the geodesic) and `max_paths=50` are this task's
    own Implementer's-call defaults (Open Question, stated here per this
    project's convention for such calls): 10% is tight enough that the
    ensemble stays a genuine "near-tie" set rather than degenerating into
    most-paths-in-the-graph on a densely-connected contact network, and
    `max_paths` is a safety cap against runaway enumeration on graphs with
    many degenerate-length paths, not expected to bind in practice at this
    tolerance (checked directly per target, see this task's own Done
    section for whether it ever did).

    Raises `ValueError` if `source`/`target` overlap (an undefined "path
    between a set and itself") or if no path exists (disconnected apo
    graph, or the graph is disconnected between just these two sets).
    """
    import networkx as nx

    source_idx = _source_indices(source)
    target_idx = _source_indices(target)
    if set(source_idx.tolist()) & set(target_idx.tolist()):
        raise ValueError("shortest_path_ensemble: source and target sets overlap")

    G = _weighted_graph(coords, cutoff)
    H = _with_virtual_endpoints(G, source_idx, target_idx)
    if not nx.has_path(H, _SUPER_SOURCE, _SUPER_SINK):
        raise ValueError(
            f"shortest_path_ensemble: no path between the two residue sets on the "
            f"apo contact graph at cutoff={cutoff} -- the sets are in different "
            "connected components"
        )

    paths = []
    shortest_length = None
    for path in nx.shortest_simple_paths(H, _SUPER_SOURCE, _SUPER_SINK, weight="weight"):
        # Strips only the two virtual super-nodes -- the real source/target
        # residues that anchor the path stay in `residues`, so the report
        # is the full literal channel (both endpoints included), not just
        # the intermediate bridge.
        residues = path[1:-1]
        length = sum(H[path[k]][path[k + 1]]["weight"] for k in range(len(path) - 1))
        if shortest_length is None:
            shortest_length = length
        if length > shortest_length * (1.0 + tol):
            break
        paths.append({"residues": residues, "length": length})
        if len(paths) >= max_paths:
            break

    return {
        "shortest_path": paths[0]["residues"],
        "shortest_length": shortest_length,
        "ensemble": paths,
        "n_ensemble": len(paths),
        "tol": tol,
        "ensemble_capped": len(paths) >= max_paths,
    }


def set_edge_connectivity(coords: np.ndarray, source, target, cutoff: float = 10.0) -> dict:
    """Menger's-theorem edge connectivity between the `source` and `target`
    residue sets: the minimum number of edges whose removal disconnects
    them, equivalently the maximum number of edge-disjoint paths between
    them -- **unweighted** (each contact edge counts as one route,
    regardless of its strength; this is deliberately the "how many
    independent doors" count, distinct from `percolation_threshold`'s own
    strength-weighted question below). Also reports the literal min-cut
    edges (the real bottleneck, if one exists) as (residue_i, residue_j)
    pairs, with the virtual super-source/sink edges filtered out."""
    import networkx as nx

    source_idx = _source_indices(source)
    target_idx = _source_indices(target)
    if set(source_idx.tolist()) & set(target_idx.tolist()):
        raise ValueError("set_edge_connectivity: source and target sets overlap")

    G = _weighted_graph(coords, cutoff)
    H = _with_virtual_endpoints(G, source_idx, target_idx)
    if not nx.has_path(H, _SUPER_SOURCE, _SUPER_SINK):
        raise ValueError(
            f"set_edge_connectivity: no path between the two residue sets on the "
            f"apo contact graph at cutoff={cutoff}"
        )

    # `nx.edge_connectivity`/`nx.minimum_edge_cut` do not accept a
    # `capacity` argument at all (checked directly, not assumed -- they
    # are purely-topological unit-capacity functions only). The
    # capacitated equivalents are `nx.minimum_cut`/`nx.maximum_flow_value`
    # -- required here specifically because of the large `capacity` this
    # module's own virtual edges carry (`_with_virtual_endpoints`'s own
    # docstring), which `edge_connectivity` would otherwise have no way to
    # honor even if it accepted the keyword.
    connectivity, (S, _T) = nx.minimum_cut(H, _SUPER_SOURCE, _SUPER_SINK, capacity="capacity")
    real_cut_edges = sorted({
        tuple(sorted((u, v)))
        for u in S for v in H.neighbors(u) if v not in S
        if u not in (_SUPER_SOURCE, _SUPER_SINK) and v not in (_SUPER_SOURCE, _SUPER_SINK)
    })
    n_edges_in_cut = sum(
        1 for u in S for v in H.neighbors(u) if v not in S
    )
    return {
        "edge_connectivity": int(connectivity),
        "cut_edges": real_cut_edges,
        "n_virtual_edges_in_cut": n_edges_in_cut - len(real_cut_edges),
    }


def percolation_threshold(coords: np.ndarray, source, target, cutoff: float = 10.0) -> dict:
    """The strength-weighted percolation question: thresholding the
    contact graph from strongest edge to weakest, at what contact strength
    (equivalently, what Euclidean distance) do the `source` and `target`
    residue sets first become connected? Union-Find over edges sorted by
    *decreasing* strength (= increasing distance) -- a single sweep,
    O(E log E), reports the exact edge that causes the merge (the literal
    bridge, if a well-defined single bridge exists) and its distance/
    strength, not just the threshold value in isolation.

    Distinct from `set_edge_connectivity`'s unweighted route *count* --
    this is "how strong does the network need to be, overall, before these
    two sets talk at all," the two halves of this task's own Outcome (b)."""
    source_idx = set(_source_indices(source).tolist())
    target_idx = set(_source_indices(target).tolist())
    if source_idx & target_idx:
        raise ValueError("percolation_threshold: source and target sets overlap")

    n = len(coords)
    W = contact_matrix(coords, cutoff=cutoff, weight="invdist")
    rows, cols = np.nonzero(np.triu(W, k=1))
    strengths = W[rows, cols]
    order = np.argsort(-strengths)  # strongest (highest invdist) first

    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for k in order.tolist():
        i, j = int(rows[k]), int(cols[k])
        union(i, j)
        if any(find(s) == find(t) for s in source_idx for t in target_idx):
            strength = float(strengths[k])
            return {
                "merge_strength": strength,
                "merge_distance": 1.0 / strength - _EPS,
                "merge_edge": tuple(sorted((i, j))),
                "n_edges_added": int(np.where(order == k)[0][0]) + 1,
            }

    raise ValueError(
        f"percolation_threshold: source and target sets never merge even using every "
        f"edge in the apo contact graph at cutoff={cutoff} -- disconnected"
    )
