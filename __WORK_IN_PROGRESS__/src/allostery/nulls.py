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
"""
from __future__ import annotations

import numpy as np


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
