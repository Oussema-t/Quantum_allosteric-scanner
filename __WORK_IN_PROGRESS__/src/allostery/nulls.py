"""TASK-0158 -- spatially compact null-draw functions for permutation
tests, replacing the uniformly *scattered* `rng.choice(N, size,
replace=False)` draw used throughout this project's register wherever a
permutation null is used to certify a positive result.

**The finding (`scripts/null_audit.py`/`null_audit2.py`, delivered via
`PANEL_REVIEW_2026-07-25.md` §2.3, re-verified running in this repo
before trusting it, not assumed from the review's own claimed numbers --
reproduced exactly: 4.8x inflation at alpha=0.05, rising to 42x at
alpha=0.001, 0x on a spatially-uncorrelated white-noise control).** Real
pockets are spatially *compact* (a contiguous, spatially-clustered set
of residues); every null in this project's register instead draws a
uniformly *scattered* same-size subset. For a *smooth* spatial score
field (any observable whose value varies gradually with position --
true of every propagator-based observable in this register, since
nearby residues share similar coupling to the seed), a compact subset's
scores are spatially autocorrelated and therefore produce a
systematically more extreme rank statistic than a scattered subset of
the same size -- making every p-value computed against a scattered null
anti-conservative for a real (compact) pocket. This is a property of
the *label geometry vs. score-field smoothness* interaction, not of any
one observable or task -- confirmed directly on a spatially-uncorrelated
(white-noise) control field, which shows ~0x inflation, isolating the
mechanism as spatial autocorrelation, not a test-construction artifact.

`compact_patch` is TASK-0158's own direct, unmodified port of
`null_audit.py`'s own reference implementation (not re-derived) --
nearest-Euclidean-neighbours of a random seed residue, the simplest
faithful model of "a real pocket's own geometry." `compact_patch_
matched` adds the review's own suggested extension (radius-of-gyration
matching against a target scale) via rejection sampling, mirroring
`closure.matched_spread_null`'s own established convention (TASK-0143)
for the same kind of matched-null problem.

**TASK-0201 -- `graph_walk_patch`, a second compact-ish family with a
much wider Rg reach.** [[TASK-0190]] measured, directly (20,000
unconstrained draws), that `compact_patch`'s own Rg support has a hard
ceiling for CARDIAC_MYOSIN (7.784) and PTP1B (7.134) that sits BELOW
those targets' own real pocket Rg (9.628, 7.969) -- not a rare tail
event, a structural impossibility (`p99.9 == max` on both). **Why the
ceiling exists**: `compact_patch` always takes the `size` *closest*
points to its seed -- by construction, the tightest possible packing
available in that seed's own local neighbourhood. It can never "reach
past" a near point to include a farther one, so across every possible
seed, its achievable spread is bounded by how anisotropic the densest
local packing in the structure gets -- for a Cα chain with roughly
uniform local density, that ceiling is low and does not vary much with
seed choice. Real pockets, in contrast, often line a surface groove or
cleft -- topologically contiguous (every member residue neighbours
another member) but geometrically elongated, not a tight 3-D ball.
`graph_walk_patch` models this directly: randomized connected growth on
the residue contact graph (an Eden-growth process) rather than
Euclidean-nearest-neighbour selection -- each newly added residue only
needs to be adjacent to something already in the growing patch, not
close to the original seed, so the walk can wander along a curved
surface path and reach much larger spread for the same cardinality.
Verified empirically (not assumed) on both targets TASK-0190 found
infeasible: max Rg over 20,000 draws is 14.6 (CARDIAC_MYOSIN, vs. real
9.628) and 14.0 (PTP1B, vs. real 7.969) -- both real Rg values sit
comfortably inside the support, not at its edge.
"""
from __future__ import annotations

import numpy as np

from .hamiltonians import contact_matrix


def compact_patch(coords: np.ndarray, size: int, rng: np.random.Generator) -> np.ndarray:
    """A spatially contiguous same-size null label: the `size` nearest
    Euclidean neighbours (inclusive of itself) of a uniformly random seed
    residue. `null_audit.py`'s own reference implementation, ported
    verbatim (not re-derived) -- the minimal faithful model of what a
    real pocket's own geometry looks like, as opposed to a uniformly
    scattered same-size subset (`rng.choice(len(coords), size,
    replace=False)`, this project's prior convention everywhere a null
    is used to certify a positive result)."""
    c = rng.integers(len(coords))
    d = np.linalg.norm(coords - coords[c], axis=1)
    return np.argsort(d)[:size]


def compact_patch_from_pool(
    coords: np.ndarray, pool: np.ndarray, size: int, rng: np.random.Generator
) -> np.ndarray:
    """`compact_patch`, restricted to drawing its seed residue and all
    its neighbours from `pool` (a sub-array of eligible original
    indices) -- the pool-restricted equivalent of this project's prior
    `rng.choice(pool, size=size, replace=False)` convention (e.g.
    `persistent_voids_real_run.py`'s/`learnability_gate_patch_control.
    py`'s own null, which excludes the seed/active-site residues from
    the drawable pool). Returns indices into the ORIGINAL `coords` array
    (not into `pool`), matching `rng.choice(pool, ...)`'s own return
    convention exactly, so it drops in as a direct replacement."""
    pool = np.asarray(pool, dtype=int)
    local_idx = compact_patch(coords[pool], size, rng)
    return pool[local_idx]


def radius_of_gyration(coords: np.ndarray, idx) -> float:
    """Standard radius of gyration of the point subset `coords[idx]`:
    the RMS distance from the subset's own centroid."""
    pts = coords[np.asarray(idx, dtype=int)]
    centroid = pts.mean(axis=0)
    return float(np.sqrt(np.mean(np.sum((pts - centroid) ** 2, axis=1))))


def compact_patch_matched(
    coords: np.ndarray,
    size: int,
    rng: np.random.Generator,
    *,
    target_rg: float,
    tol: float = 0.35,
    max_attempts: int = 200_000,
    return_attempts: bool = False,
):
    """`compact_patch`, rejection-sampled to also match a target radius
    of gyration within `+/- tol` (fractional) -- the review's own
    documented extension ("optionally match the real pocket's radius of
    gyration"), for callers who want the null patch's own *shape* (not
    just its size) to resemble a specific real pocket, not merely any
    compact patch. Mirrors `closure.matched_spread_null`'s own
    established rejection-sampling convention (TASK-0143) for the
    analogous matched-null problem on graph/Euclidean spread.

    Raises `RuntimeError` (not a silent fallback to an unmatched draw)
    if no matching patch is found within `max_attempts` -- a real,
    reportable infeasibility, per this project's own established
    discipline for rejection-sampled nulls (`closure.matched_spread_
    null`'s own precedent: TASK-0143 found this genuinely infeasible on
    4/7 real targets, and reported that rather than silently loosening
    the tolerance).

    `return_attempts` (TASK-0190, additive -- default `False`, every
    existing call site's return shape is byte-identical): when `True`,
    returns `(idx, n_attempts)` instead of bare `idx` -- needed to
    report the rejection-sampling acceptance rate when drawing at a
    real (possibly high-percentile, per [[TASK-0167.003]] Part B) target
    Rg, per that task's own "record the rejection-sampling acceptance
    rate" Constraint. Not exposed any other way (the function has no
    other side channel), so this is additive surface, not a workaround."""
    lo, hi = target_rg * (1.0 - tol), target_rg * (1.0 + tol)
    for attempt in range(1, max_attempts + 1):
        idx = compact_patch(coords, size, rng)
        rg = radius_of_gyration(coords, idx)
        if lo <= rg <= hi:
            return (idx, attempt) if return_attempts else idx
    raise RuntimeError(
        f"compact_patch_matched: no compact patch with radius of gyration in "
        f"[{lo:.3f}, {hi:.3f}] (target {target_rg:.3f} +/- {tol:.0%}) found "
        f"within {max_attempts} attempts"
    )


# ---------------------------------------------------------------------------
# TASK-0201 -- graph-walk patch: a second compact-ish family that can
# actually reach real pocket Rg where compact_patch structurally cannot.
# See this module's own docstring for the mechanism.
# ---------------------------------------------------------------------------

def build_adjacency(coords: np.ndarray, cutoff: float = 8.0) -> list:
    """One-time O(N^2) contact-graph neighbour list -- build once, reuse
    across many `graph_walk_patch` draws (a rejection-sampling loop
    calling `graph_walk_patch` thousands of times must not rebuild the
    contact matrix on every attempt). Returns a list of `(deg_i,)`
    int arrays, one per residue, matching `hamiltonians.contact_matrix`'s
    own `cutoff`/`weight="binary"` convention (the same graph
    `baselines.hop_from_seed` and this project's ENM machinery use)."""
    W = contact_matrix(coords, cutoff=cutoff, weight="binary")
    return [np.nonzero(row)[0] for row in W]


def graph_walk_patch(adjacency: list, size: int, rng: np.random.Generator) -> np.ndarray:
    """A spatially contiguous same-size null label grown by randomized
    connected expansion (Eden growth) on the residue contact graph --
    `size` residues, each (after the first) adjacent to something
    already in the growing patch, but with NO requirement of being
    close to the original seed the way `compact_patch`'s Euclidean
    nearest-neighbour selection has. This is what lets it reach a much
    wider radius-of-gyration range for the same patch size (this
    module's own docstring has the full mechanism and the empirical
    numbers that motivated it, TASK-0201).

    `adjacency`: `build_adjacency(coords, cutoff)`'s own output.

    Frontier candidates are drawn from a **sorted** list, not a raw
    Python `set` iterated directly -- `set` iteration order is a CPython
    implementation detail, not part of the language guarantee, and this
    function must be exactly reproducible given a fixed `rng` state
    (the same discipline `compact_patch`'s own `np.argsort` already
    follows).

    Restarts from a fresh random seed if the current connected
    component is exhausted before reaching `size` (possible, if rare,
    for a small isolated component) -- never returns short of `size`.
    """
    n = len(adjacency)
    while True:
        seed = int(rng.integers(n))
        included = {seed}
        frontier = set(adjacency[seed].tolist()) - included
        stalled = False
        while len(included) < size:
            if not frontier:
                stalled = True
                break
            nxt = int(rng.choice(sorted(frontier)))
            included.add(nxt)
            frontier |= set(adjacency[nxt].tolist())
            frontier -= included
        if not stalled:
            return np.array(sorted(included), dtype=int)


def graph_walk_patch_matched(
    coords: np.ndarray,
    adjacency: list,
    size: int,
    rng: np.random.Generator,
    *,
    target_rg: float,
    tol: float = 0.35,
    max_attempts: int = 200_000,
    return_attempts: bool = False,
):
    """`graph_walk_patch`, rejection-sampled to also match a target
    radius of gyration within `+/- tol` (fractional) -- the
    `graph_walk_patch` analogue of `compact_patch_matched`, built
    specifically for targets where `compact_patch_matched` cannot
    genuinely centre on `target_rg` because `compact_patch`'s own
    support does not reach it at all (TASK-0190's own finding on
    CARDIAC_MYOSIN/PTP1B). Same rejection-sampling / `RuntimeError`-on-
    infeasibility / `return_attempts` contract as `compact_patch_
    matched`, for direct drop-in comparison.
    """
    lo, hi = target_rg * (1.0 - tol), target_rg * (1.0 + tol)
    for attempt in range(1, max_attempts + 1):
        idx = graph_walk_patch(adjacency, size, rng)
        rg = radius_of_gyration(coords, idx)
        if lo <= rg <= hi:
            return (idx, attempt) if return_attempts else idx
    raise RuntimeError(
        f"graph_walk_patch_matched: no graph-walk patch with radius of "
        f"gyration in [{lo:.3f}, {hi:.3f}] (target {target_rg:.3f} +/- "
        f"{tol:.0%}) found within {max_attempts} attempts"
    )
