"""Phase 3 - unsupervised operator selector (focusing / specificity / ballistic).

Net-new module (no notebook precedent, see TASK-0007): picks which
Hamiltonian/operator variant and propagation parameters to use on a FROZEN
(held-out) target, using only properties observable from the apo structure
and the walk's own dynamics -- never labels. This is what keeps selection
legitimate inside `protocol.py`'s (TASK-0006) FROZEN loop: every function
here is computable from `H` (the Hamiltonian) and a seed index alone.
"""
from __future__ import annotations

from typing import Sequence, Union

import numpy as np

# Mirrors propagators.Source exactly (TASK-0090) -- kept as a local alias
# rather than a cross-module import, matching this codebase's convention of
# each module staying decoupled from the internals of the ones it calls
# (only lazy, function-local `from .propagators import ...` calls elsewhere
# in this file).
Source = Union[int, Sequence[int]]


def focusing(P: np.ndarray) -> float:
    """How concentrated a time-averaged walk distribution is.

    Reuses `metrics.ipr` directly (Sum P_i^4 / (Sum P_i^2)^2) rather than
    reimplementing it -- the formula is scale-invariant (the squared
    denominator normalises for any input scale), so it is exactly as valid
    on an L1-normalised probability vector (`Sum P_i = 1`) as on the
    L2-normalised eigenvector `metrics.ipr` was originally written for.
    High focusing (-> 1) = concentrated/localized; low focusing (-> 1/N for
    a uniform P) = delocalized/spread out.
    """
    from .metrics import ipr

    return ipr(P)


def _hellinger_distance(p: np.ndarray, q: np.ndarray) -> float:
    """Symmetric, bounded ([0, 1]) distance between two probability vectors."""
    return float(np.sqrt(0.5 * np.sum((np.sqrt(p) - np.sqrt(q)) ** 2)))


def source_specificity(
    H: np.ndarray,
    source: Source,
    t_max: float,
    n_steps: int = 500,
    n_alt: int = 20,
    rng: np.random.Generator | None = None,
) -> float:
    """Label-free proxy for "does this seed produce a distinctive walk."

    Runs `propagators.time_averaged_ctqw` from `source` and from a sample of
    `n_alt` alternative seeds (default: a fixed-seed random sample of the
    other nodes, so results are reproducible -- same convention as
    `metrics.block_bootstrap_ci`'s default `rng`), then scores `source` by
    its mean Hellinger distance to the alternatives' distributions.

    High specificity -> the seed's walk is structurally distinguishable from
    a "generic" seed elsewhere on the same graph -- a label-free signal that
    this operator carries seed-dependent information, rather than washing
    every seed out to nearly the same distribution (e.g. on a highly
    symmetric graph, where any single source produces an equivalent
    distribution up to a relabelling).

    Samples rather than exhausting all N-1 alternative seeds by default,
    since each alternative costs a full `time_averaged_ctqw` run
    (`n_steps` eigendecompositions) -- exhaustive is fine for the small
    synthetic graphs in this module's own tests, but would be expensive on a
    real, few-hundred-residue protein Hamiltonian.

    `source` may be a scalar or a multi-index array/sequence (TASK-0090) --
    `time_averaged_ctqw` already handles both natively; this function's own
    `others` exclusion set previously assumed a scalar (`i != source` raises
    `ValueError: The truth value of an array...` for a multi-index `source`,
    the actual crash TASK-0090's own reproduction hits -- despite that
    task's Intent Contract marking this function "already correct", which
    was checked by execution and found false, not assumed).
    """
    from .propagators import time_averaged_ctqw

    if rng is None:
        rng = np.random.default_rng(42)
    N = H.shape[0]
    excluded = set(np.atleast_1d(source).tolist())
    others = np.array([i for i in range(N) if i not in excluded])
    n_alt = min(n_alt, len(others))
    if n_alt == 0:
        return float("nan")
    alt_sources = rng.choice(others, size=n_alt, replace=False)

    P_source = time_averaged_ctqw(H, t_max, source=source, n_steps=n_steps)
    dists = [
        _hellinger_distance(
            P_source, time_averaged_ctqw(H, t_max, source=int(alt), n_steps=n_steps)
        )
        for alt in alt_sources
    ]
    return float(np.mean(dists))


def _hop_distances_from_source(H: np.ndarray, source: Source) -> np.ndarray:
    """BFS hop-distance from `source` over H's off-diagonal sparsity pattern.

    The diagonal potentials in `hamiltonians.build_H_new` (V_B, V_T, V_R,
    V_C, V_M) only ever touch the diagonal -- the off-diagonal structure of
    any H built by this codebase's convention is exactly the underlying
    contact graph's connectivity, regardless of which potential terms were
    added. This recovers hop distance directly from H, so
    `ballistic_exponent` needs no separate coords/adjacency input and stays
    computable from the operator alone.

    `source` may be a scalar or a multi-index array/sequence (TASK-0090) --
    a standard multi-source BFS, frontier seeded from every index at once,
    each node's distance the min hop-count to *any* seed. Previously
    `frontier = [source]` wrapped an entire array `source` as a single list
    element instead of seeding one frontier entry per index -- silently
    wrong (not a crash: `adjacency[node]` on a 2-row fancy-indexed array
    still runs, just computes garbage neighbor indices), the "hidden
    wrong-shape state" this task's own Context section already named.

    Returns an (N,) int array; unreachable nodes (disconnected graph) get -1.
    """
    N = H.shape[0]
    adjacency = np.abs(H - np.diag(np.diag(H))) > 1e-12
    dist = np.full(N, -1, dtype=int)
    source_idx = np.atleast_1d(np.asarray(source, dtype=int))
    dist[source_idx] = 0
    frontier = list(source_idx)
    d = 0
    while frontier:
        d += 1
        next_frontier: list[int] = []
        for node in frontier:
            for nb in np.where(adjacency[node])[0]:
                if dist[nb] == -1:
                    dist[nb] = d
                    next_frontier.append(int(nb))
        frontier = next_frontier
    return dist


def ballistic_exponent(
    H: np.ndarray,
    source: Source,
    t_values: np.ndarray | None = None,
) -> float:
    """Spread-vs-time scaling exponent: fits spread(t) ~ t^alpha.

    `spread(t)` is the walk's RMS graph-distance from the seed at time t:
    sqrt(Sum_j P_j(t) * hop_distance(source, j)^2). `alpha` (the log-log
    linear-regression slope) is a standard quantum-walk transport-regime
    diagnostic: alpha ~= 1 => ballistic (coherent quantum spreading);
    alpha ~= 0.5 => diffusive (classical-like); alpha ~= 0 =>
    localized/trapped (or saturated -- see below).

    Label-free and needs only `H` and the seed: hop distances come from
    `_hop_distances_from_source`, occupation from `propagators.ctqw` (both
    already support a multi-index `source`, TASK-0090).

    Nodes unreachable from `source` (disconnected graph) are excluded from
    the spread calculation, not treated as infinitely far.
    """
    from .propagators import ctqw

    if t_values is None:
        t_values = np.geomspace(0.5, 20.0, 8)

    hop_dist = _hop_distances_from_source(H, source).astype(float)
    reachable = hop_dist >= 0

    spreads = []
    for t in t_values:
        P = ctqw(H, t, source=source)
        spread_sq = np.sum(P[reachable] * hop_dist[reachable] ** 2)
        spreads.append(np.sqrt(max(spread_sq, 1e-300)))

    slope, _ = np.polyfit(np.log(t_values), np.log(spreads), 1)
    return float(slope)


def _zscore(x: np.ndarray) -> np.ndarray:
    """Same z-score convention as potentials._zscore (safe against near-zero std)."""
    x = np.asarray(x, dtype=float)
    std = x.std()
    return (x - x.mean()) / (std + 1e-9)


def unsupervised_score(candidates: list[dict]) -> np.ndarray:
    """Rank candidate operator/parameter configs without ever looking at labels.

    Combines `focusing`, `source_specificity`, and `ballistic_exponent` into
    one z-scored sum per candidate -- same combination convention as
    `potentials.V_R`'s `-(z(degree) + z(clustering) - z(msf))`. Usable
    inside `protocol.leave_one_protein_out`'s FROZEN loop to pick a config
    for a held-out target without touching its holo pocket/labels.

    Each candidate dict must supply:
      H      : (N, N) Hamiltonian for this operator/parameter choice.
      source : seed node index.
      t      : propagation time for `focusing` (via `time_averaged_ctqw`).
    Optional per-candidate overrides: `t_max` (source_specificity's time
    budget, defaults to `t`), `n_steps`, `n_alt`, `rng`, `t_values`
    (ballistic_exponent's time grid).

    Returns an `(n_candidates,)` array of combined scores -- higher is more
    preferred.
    """
    from .propagators import time_averaged_ctqw

    focusing_scores = []
    specificity_scores = []
    ballistic_scores = []
    for cand in candidates:
        H = cand["H"]
        source = cand["source"]
        t = cand["t"]
        n_steps = cand.get("n_steps", 500)

        P = time_averaged_ctqw(H, t, source=source, n_steps=n_steps)
        focusing_scores.append(focusing(P))
        specificity_scores.append(
            source_specificity(
                H,
                source,
                cand.get("t_max", t),
                n_steps=n_steps,
                n_alt=cand.get("n_alt", 20),
                rng=cand.get("rng"),
            )
        )
        ballistic_scores.append(
            ballistic_exponent(H, source, t_values=cand.get("t_values"))
        )

    combined = (
        _zscore(focusing_scores)
        + _zscore(specificity_scores)
        + _zscore(ballistic_scores)
    )
    return combined
