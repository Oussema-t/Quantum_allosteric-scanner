"""TASK-0181 Phase A -- constrained subset *selection* (QUBO), classically
solved, gated against greedy top-k ranking.

**Not to be confused with `select.py`** (the Phase-3 unsupervised operator/
parameter picker -- `focusing`/`unsupervised_score`, picking which
Hamiltonian/propagation config to run, never touching subset selection).
This module answers a structurally different question: given a per-residue
score, is the *best k-subset* (a set-level objective, NP-hard via
densest-k-subgraph) a better predictor than the *top-k by score alone*
(what every ranking observable in this project's register already is)?

Every other quantum route in this project is complexity-dead (Grover/HHL/
QML, ENAQT, chirality, persistent H2, entanglement entropy, spectral
coherence, multi-particle walks -- see TASK-0181's own "Why this matters").
Selection differs from ranking on three counts the task file states
directly: complexity class (NP-hard), output shape (O(1) readout, not the
challenge's own O(N^2) matrix), and the ability to penalise a *set* for
being collectively confound-adjacent, which an independent per-residue
score cannot express.

**Pre-registered gate** (`.ai/tasks/DONE/TASK-0181-*.md`, written and
timestamped before this module or any run): if the classical QUBO solve
does not beat greedy top-k on `sites.site_hit_metrics`' `hit_at_1`, at
fixed weights, on >=2 of the 3 mandatory targets, Phase A is reported
closed and no quantum formulation is built.

**Objective** (task's own 5-term formula):

    Q(S) =  a * sum_{i in S} score_i           (member quality)
          + b * sum_{i,j in S} A_ij             (spatial cohesion)
          + c * coupling(S, active_site)        (allosteric relevance)
          - d * sum_{i in S} proximity_i        (anti-confound penalty)
          - e * |S intersect active_site|       (distality)

`score`/`proximity`/`coupling` are min-max normalized to [0,1] before
weighting -- their raw scales differ by orders of magnitude (occupation
~1e-2, proximity in Angstrom, coupling whatever `mode_coparticipation`
returns) and un-normalized weights would be meaningless to compare across
a knob grid. `A_ij` (contact matrix) is already binary, left as-is --
Implementer's-call detail, stated here rather than silently assumed.

**Cardinality.** `|S| = k` exactly, enforced *structurally*: every solver
below only ever considers exactly-k subsets (SA moves are member/non-member
swaps), never a penalty term risking constraint violation the way a
generic unconstrained-QUBO encoding would need.

**Solver.** No QUBO library is a dependency of this repo (`dimod` is not
installed -- checked directly, not assumed) and none is added: the
cardinality-constrained search space above needs no generic BQM machinery.
`exact_solve` (brute-force enumeration, small N only) validates
`sa_solve` (swap-based simulated annealing, real targets up to N~704) on
the "solver-quality" control (`tests/test_selection.py`).
"""
from __future__ import annotations

from itertools import combinations
from typing import Callable, Sequence

import numpy as np

MAX_EXACT_COMBINATIONS = 2_000_000  # guards exact_solve from real-target N


def _minmax_normalize(x: np.ndarray) -> np.ndarray:
    """[0,1] min-max normalization; a constant vector (max == min) maps to
    all-zeros -- there is no discriminating information in a flat vector,
    so "no preference" (0 everywhere) is the honest encoding, not a
    divide-by-zero or an arbitrary constant."""
    x = np.asarray(x, dtype=float)
    lo, hi = x.min(), x.max()
    if hi - lo < 1e-300:
        return np.zeros_like(x)
    return (x - lo) / (hi - lo)


def qubo_objective(
    S_idx,
    *,
    score: np.ndarray,
    A: np.ndarray,
    proximity: np.ndarray,
    active_site_mask: np.ndarray,
    coupling: np.ndarray | None,
    weights: Sequence[float],
) -> float:
    """`Q(S)`, the task's own 5-term objective -- see module docstring.
    `score`/`proximity`/`coupling` are the *raw* per-residue vectors;
    normalization happens here (once per call), not by the caller, so
    every solver/control in this module scores identically.

    `coupling=None` (TASK-0178 not yet landed) drops term (c) to zero
    exactly, rather than raising -- `weights[2]` (c) is simply inert,
    matching this package's existing missing-input-degrades-gracefully
    convention (e.g. `report.verdict_template`'s missing-key handling).
    """
    a, b, c, d, e = weights
    S = np.atleast_1d(np.asarray(S_idx, dtype=int))

    score_n = _minmax_normalize(score)
    proximity_n = _minmax_normalize(proximity)
    coupling_n = _minmax_normalize(coupling) if coupling is not None else None

    term_a = a * float(score_n[S].sum())
    A_sub = A[np.ix_(S, S)]
    term_b = b * float(A_sub.sum() - np.trace(A_sub))  # off-diagonal only, i != j
    term_c = c * float(coupling_n[S].sum()) if coupling_n is not None else 0.0
    term_d = -d * float(proximity_n[S].sum())
    term_e = -e * float(np.asarray(active_site_mask, dtype=bool)[S].sum())

    return term_a + term_b + term_c + term_d + term_e


def greedy_topk_indices(score: np.ndarray, k: int) -> np.ndarray:
    """Top-k residues by `score` descending -- both a benchmark in its
    own right and the exact target of the degenerate-case control
    (weights `(a=1, b=c=d=e=0)` must reduce `qubo_objective`'s maximizer
    to this set, since a purely separable sum of `score` is maximized by
    the k highest-scoring elements, ties aside)."""
    score = np.asarray(score, dtype=float)
    k_eff = min(k, len(score))
    return np.argsort(-score)[:k_eff]


def exact_solve(N: int, k: int, objective_fn: Callable[[np.ndarray], float]) -> tuple:
    """Brute-force `C(N, k)` enumeration -- the ground truth `sa_solve`'s
    solver-quality control is checked against. Guarded: raises rather
    than silently running for hours if `C(N, k)` exceeds
    `MAX_EXACT_COMBINATIONS` -- this is a validation tool for small N,
    never a real-target solver (see `sa_solve` for that).

    Returns `(best_S, best_value)`, `best_S` a sorted `(k,)` int array.
    """
    from math import comb

    n_combos = comb(N, k)
    if n_combos > MAX_EXACT_COMBINATIONS:
        raise ValueError(
            f"exact_solve: C({N}, {k}) = {n_combos} exceeds MAX_EXACT_COMBINATIONS "
            f"({MAX_EXACT_COMBINATIONS}) -- this is a small-N validation tool, not a "
            "real-target solver; use sa_solve instead."
        )
    best_S, best_value = None, -np.inf
    for combo in combinations(range(N), k):
        value = objective_fn(np.asarray(combo, dtype=int))
        if value > best_value:
            best_S, best_value = np.asarray(combo, dtype=int), value
    return best_S, float(best_value)


def sa_solve(
    N: int,
    k: int,
    objective_fn: Callable[[np.ndarray], float],
    *,
    rng: np.random.Generator,
    n_iter: int = 2000,
    init: np.ndarray | None = None,
    t_start: float = 1.0,
    t_end: float = 0.01,
) -> tuple:
    """Swap-based simulated annealing over exactly-`k` subsets of
    `range(N)`. Each iteration proposes swapping one current member for
    one non-member (uniformly drawn), accepts the swap if it improves
    the objective, or accepts a worsening swap with Metropolis
    probability `exp(delta / T)` under a geometric cooling schedule from
    `t_start` to `t_end` over `n_iter` steps -- standard combinatorial
    SA, cardinality preserved by construction (a swap can never change
    `|S|`).

    Deterministic under a seeded `rng` (this task's own Constraint,
    mirrors `sites.py`'s identical requirement) -- no other source of
    randomness is used. `init` defaults to `greedy_topk_indices(score, k)`
    read out of the first term's own scale... but this function is
    score-agnostic (works on any `objective_fn`), so the caller supplies
    `init` explicitly; a random `k`-subset is used if omitted.

    Tracks the best `S`/value seen across the whole run (not just the
    final state) -- SA can wander away from its own best point late in
    the schedule; the returned answer is the best ever found, matching
    every other "solver" in this codebase's own "report the winner, not
    the last state" convention (e.g. `select_frozen_config`'s `argmax`).

    Returns `(best_S, best_value)`, `best_S` a sorted `(k,)` int array.
    """
    if init is None:
        S = np.sort(rng.choice(N, size=k, replace=False))
    else:
        S = np.sort(np.asarray(init, dtype=int))

    current_value = objective_fn(S)
    best_S, best_value = S.copy(), current_value

    for step in range(n_iter):
        frac = step / max(n_iter - 1, 1)
        T = t_start * (t_end / t_start) ** frac

        in_S = set(S.tolist())
        out_S = [i for i in range(N) if i not in in_S]
        if not out_S:
            break  # k == N, nothing to swap

        remove_i = int(rng.choice(S))
        add_j = int(rng.choice(out_S))
        candidate = np.sort(np.array([j if j != remove_i else add_j for j in S]))

        candidate_value = objective_fn(candidate)
        delta = candidate_value - current_value
        if delta >= 0 or rng.random() < np.exp(delta / max(T, 1e-12)):
            S, current_value = candidate, candidate_value
            if current_value > best_value:
                best_S, best_value = S.copy(), current_value

    return best_S, float(best_value)


def evaluate_selection(
    S_idx,
    coords: np.ndarray,
    pocket_mask: np.ndarray,
    *,
    resnums: np.ndarray | None = None,
    overlap_thresholds=(1, 3),
) -> dict:
    """Score one selection `S_idx` against `pocket_mask`, reusing
    `sites.site_hit_metrics` rather than inventing a second metric --
    wraps `S_idx` as a single site-shaped dict (`member_indices`,
    `centroid`, `rank=1`) so [[TASK-0180]]'s own hit/overlap/centroid-
    distance logic applies unchanged."""
    from .sites import site_hit_metrics

    coords = np.asarray(coords, dtype=float)
    S = np.atleast_1d(np.asarray(S_idx, dtype=int))
    site = {
        "rank": 1,
        "member_indices": S.tolist(),
        "member_resnums": np.asarray(resnums)[S].tolist() if resnums is not None else None,
        "centroid": coords[S].mean(axis=0).tolist(),
    }
    return site_hit_metrics([site], pocket_mask, coords, overlap_thresholds=overlap_thresholds)


def selection_chance_level(
    N: int,
    k: int,
    coords: np.ndarray,
    pocket_mask: np.ndarray,
    *,
    A: np.ndarray,
    proximity: np.ndarray,
    active_site_mask: np.ndarray,
    coupling: np.ndarray | None,
    weights: Sequence[float],
    n_null: int = 50,
    n_iter: int = 500,
    overlap_thresholds=(1, 3),
    rng: np.random.Generator | None = None,
) -> dict:
    """Null distribution of the selection-pipeline hit rate: `n_null`
    independent random `score` vectors, each pushed through the
    *identical* `sa_solve` + `evaluate_selection` pipeline the real score
    uses -- mirrors `sites.site_chance_level`'s own "re-invoke the whole
    pipeline per replicate" reasoning. `n_iter` defaults lower than
    `sa_solve`'s own default (500 vs. 2000) -- a null run only needs to
    find *a* competitive random-score subset, not this pipeline's own
    best; kept modest so `n_null` replicates stay cheap across a 12-target
    x 64-combination grid.

    Returns `{"n_null", "hit_rate_at_<t>", "hit_rate_at_<t>_ci", ...}`,
    same shape as `sites.site_chance_level`.
    """
    coords = np.asarray(coords, dtype=float)
    rng = rng if rng is not None else np.random.default_rng(42)

    hit_flags = {t: np.empty(n_null, dtype=bool) for t in overlap_thresholds}
    for i in range(n_null):
        null_score = rng.random(N)

        def objective_fn(S, _score=null_score):
            return qubo_objective(
                S, score=_score, A=A, proximity=proximity,
                active_site_mask=active_site_mask, coupling=coupling, weights=weights,
            )

        init = greedy_topk_indices(null_score, k)
        S, _ = sa_solve(N, k, objective_fn, rng=rng, n_iter=n_iter, init=init)
        metrics = evaluate_selection(S, coords, pocket_mask, overlap_thresholds=overlap_thresholds)
        for t in overlap_thresholds:
            hit_flags[t][i] = metrics[f"n_hit_at_{t}"] > 0

    out: dict = {"n_null": n_null}
    for t in overlap_thresholds:
        arr = hit_flags[t].astype(float)
        out[f"hit_rate_at_{t}"] = float(arr.mean())
        lo, hi = np.percentile(arr, [2.5, 97.5])
        out[f"hit_rate_at_{t}_ci"] = (float(lo), float(hi))
    return out
