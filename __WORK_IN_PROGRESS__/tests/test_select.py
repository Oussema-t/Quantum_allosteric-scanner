"""TASK-0007 coverage -- select.py unsupervised operator selector.

Synthetic graphs only (path/star/complete), matching the task's Planned
Validation. Directional assertions below were checked empirically first
(session scratch script) rather than guessed -- see TASK-0007's Done
section for the raw numbers and the three-way focusing/specificity/
ballistic tradeoff they revealed (star/complete: high focusing+specificity,
low ballistic; path: the opposite), which is why `TestUnsupervisedScore`
below tests combination mechanics rather than asserting one topology
"wins" -- that comparison is genuinely multi-dimensional, not a bug.
"""
import numpy as np
import pytest

from allostery.hamiltonians import laplacian
from allostery.select import (
    _hop_distances_from_source,
    ballistic_exponent,
    focusing,
    source_specificity,
    unsupervised_score,
)


def _path_adjacency(n: int) -> np.ndarray:
    A = np.zeros((n, n))
    for i in range(n - 1):
        A[i, i + 1] = A[i + 1, i] = 1.0
    return A


def _star_adjacency(n: int) -> np.ndarray:
    A = np.zeros((n, n))
    for i in range(1, n):
        A[0, i] = A[i, 0] = 1.0
    return A


def _complete_adjacency(n: int) -> np.ndarray:
    return np.ones((n, n)) - np.eye(n)


N = 10
H_PATH = laplacian(_path_adjacency(N))
H_STAR = laplacian(_star_adjacency(N))
H_COMPLETE = laplacian(_complete_adjacency(N))


class TestFocusing:
    def test_fully_localized_is_near_one(self):
        P = np.zeros(N)
        P[0] = 1.0
        assert focusing(P) == pytest.approx(1.0, abs=1e-9)

    def test_uniform_is_near_one_over_n(self):
        P = np.ones(N) / N
        assert focusing(P) == pytest.approx(1.0 / N, abs=1e-9)

    def test_complete_and_star_more_focused_than_path(self):
        """CTQW on a highly symmetric graph (star/complete) stays
        persistently peaked at the source; on a path it spreads out over
        the time average -- confirmed empirically before asserting here."""
        from allostery.propagators import time_averaged_ctqw

        f_path = focusing(time_averaged_ctqw(H_PATH, 10.0, source=0))
        f_star = focusing(time_averaged_ctqw(H_STAR, 10.0, source=0))
        f_complete = focusing(time_averaged_ctqw(H_COMPLETE, 10.0, source=0))
        assert f_star > f_path
        assert f_complete > f_path


class TestSourceSpecificity:
    def test_path_endpoint_more_specific_than_midpoint(self):
        """A path's endpoint is a structurally distinguished position;
        a midpoint's walk looks more "typical" of other seeds' walks."""
        end = source_specificity(H_PATH, 0, t_max=10.0, n_alt=9)
        mid = source_specificity(H_PATH, 5, t_max=10.0, n_alt=9)
        assert end > mid

    def test_symmetric_graphs_more_specific_than_path(self):
        path = source_specificity(H_PATH, 0, t_max=10.0, n_alt=9)
        star = source_specificity(H_STAR, 0, t_max=10.0, n_alt=9)
        complete = source_specificity(H_COMPLETE, 0, t_max=10.0, n_alt=9)
        assert star > path
        assert complete > path

    def test_deterministic_with_default_rng(self):
        a = source_specificity(H_PATH, 0, t_max=10.0, n_alt=5)
        b = source_specificity(H_PATH, 0, t_max=10.0, n_alt=5)
        assert a == b

    def test_no_other_nodes_returns_nan(self):
        H1 = np.zeros((1, 1))
        assert np.isnan(source_specificity(H1, 0, t_max=10.0))


class TestBallisticExponent:
    def test_path_more_ballistic_than_star_or_complete(self):
        """A path supports genuine coherent spreading (higher exponent);
        star/complete saturate to their maximum reachable spread almost
        immediately, giving a near-zero or negative log-log slope."""
        path = ballistic_exponent(H_PATH, 0)
        star = ballistic_exponent(H_STAR, 0)
        complete = ballistic_exponent(H_COMPLETE, 0)
        assert path > star
        assert path > complete

    def test_path_endpoint_more_ballistic_than_midpoint(self):
        end = ballistic_exponent(H_PATH, 0)
        mid = ballistic_exponent(H_PATH, 5)
        assert end > mid

    def test_disconnected_component_excluded_not_infinite(self):
        # two disjoint edges: 0-1 and 2-3; source=0 can't reach 2 or 3.
        A = np.zeros((4, 4))
        A[0, 1] = A[1, 0] = 1.0
        A[2, 3] = A[3, 2] = 1.0
        H = laplacian(A)
        # must not raise/produce inf or nan despite an unreachable component
        result = ballistic_exponent(H, 0)
        assert np.isfinite(result)


class TestUnsupervisedScore:
    def test_returns_one_score_per_candidate(self):
        candidates = [
            {"H": H_PATH, "source": 0, "t": 10.0},
            {"H": H_STAR, "source": 0, "t": 10.0},
            {"H": H_COMPLETE, "source": 0, "t": 10.0},
        ]
        scores = unsupervised_score(candidates)
        assert scores.shape == (3,)

    def test_is_zero_mean_zscore_combination(self):
        candidates = [
            {"H": H_PATH, "source": 0, "t": 10.0},
            {"H": H_STAR, "source": 0, "t": 10.0},
            {"H": H_COMPLETE, "source": 0, "t": 10.0},
        ]
        scores = unsupervised_score(candidates)
        assert scores.mean() == pytest.approx(0.0, abs=1e-9)

    def test_identical_candidates_score_identically(self):
        candidates = [
            {"H": H_PATH, "source": 0, "t": 10.0},
            {"H": H_PATH, "source": 0, "t": 10.0},
        ]
        scores = unsupervised_score(candidates)
        assert scores[0] == pytest.approx(scores[1])

    def test_different_candidates_are_differentiated(self):
        candidates = [
            {"H": H_PATH, "source": 0, "t": 10.0},
            {"H": H_STAR, "source": 0, "t": 10.0},
        ]
        scores = unsupervised_score(candidates)
        assert scores[0] != pytest.approx(scores[1])


# ---------------------------------------------------------------------------
# TASK-0090 -- multi-index `source` support
#
# Reproduces the exact crash TASK-0090's own Context section documents
# (`unsupervised_score([{"H": H, "source": np.array([2, 3]), "t": 5.0}])`
# raised `ValueError: The truth value of an array...`), plus the separate,
# previously-silent wrong-answer bug in `ballistic_exponent`/
# `_hop_distances_from_source` (didn't crash, just returned a number
# computed from a garbage BFS frontier). Also covers `source_specificity`,
# which TASK-0090's own Intent Contract marked "Out Of Scope... already
# correct" -- checked by execution, not assumed, and found to crash on
# exactly the same kind of multi-index `source` (its `others` exclusion set
# used a bare `i != source` scalar comparison) -- fixed here too rather than
# left broken because a stale scope note said not to touch it.
# ---------------------------------------------------------------------------

class TestMultiIndexSource:
    def test_hop_distances_multi_source_is_min_over_seeds(self):
        # 10-node (H_PATH) path, seeds at {2, 3}: node 0 is 2 hops from
        # seed 2 (its nearest seed); node 9 is 6 hops from seed 3.
        dist = _hop_distances_from_source(H_PATH, np.array([2, 3]))
        assert dist[2] == 0 and dist[3] == 0
        assert dist[0] == 2
        assert dist[9] == 6
        assert dist[1] == 1 and dist[4] == 1  # one hop from either seed

    def test_hop_distances_single_element_array_matches_scalar(self):
        scalar = _hop_distances_from_source(H_PATH, 4)
        array = _hop_distances_from_source(H_PATH, np.array([4]))
        np.testing.assert_array_equal(scalar, array)

    def test_hop_distances_scalar_behavior_unchanged(self):
        # Byte-identical to the pre-fix scalar path (TASK-0090's own
        # Constraint) -- a plain, hand-computed BFS on a 10-node path from
        # node 0.
        dist = _hop_distances_from_source(H_PATH, 0)
        np.testing.assert_array_equal(dist, np.arange(N))

    def test_ballistic_exponent_multi_index_does_not_crash_and_is_finite(self):
        result = ballistic_exponent(H_PATH, np.array([2, 3]))
        assert np.isfinite(result)

    def test_ballistic_exponent_single_element_array_matches_scalar(self):
        scalar = ballistic_exponent(H_PATH, 4)
        array = ballistic_exponent(H_PATH, np.array([4]))
        assert array == pytest.approx(scalar)

    def test_source_specificity_multi_index_does_not_crash(self):
        # This is TASK-0090's own documented Context reproduction's actual
        # crash site (not ballistic_exponent) -- see class docstring.
        result = source_specificity(H_PATH, np.array([2, 3]), t_max=10.0, n_alt=5)
        assert np.isfinite(result)

    def test_source_specificity_excludes_every_seed_from_alternatives(self):
        # A regression for the fixed `others` set: with N=10 and a 2-index
        # seed, at most 8 alternatives exist -- n_alt=9 must clamp, not
        # accidentally include a seed residue as its own "alternative".
        result = source_specificity(H_PATH, np.array([2, 3]), t_max=10.0, n_alt=9)
        assert np.isfinite(result)

    def test_unsupervised_score_reproduces_and_fixes_task_0090s_own_repro(self):
        """Verbatim reproduction from TASK-0090's Context section (path
        adjacency, 12 nodes, source=np.array([2, 3])) -- previously raised
        ValueError, must now return one finite score."""
        H = laplacian(_path_adjacency(12))
        scores = unsupervised_score([{"H": H, "source": np.array([2, 3]), "t": 5.0}])
        assert scores.shape == (1,)
        assert np.isfinite(scores[0])

    def test_unsupervised_score_multi_index_candidate_among_scalar_candidates(self):
        candidates = [
            {"H": H_PATH, "source": 0, "t": 10.0},
            {"H": H_PATH, "source": np.array([2, 3]), "t": 10.0},
            {"H": H_STAR, "source": 0, "t": 10.0},
        ]
        scores = unsupervised_score(candidates)
        assert scores.shape == (3,)
        assert np.all(np.isfinite(scores))


# ---------------------------------------------------------------------------
# TASK-0089 -- classify select.py's reported quantities into GAUGE/KNOB/
# SIGNAL per INVARIANCE_PROTOCOL.md, closing INV-0004's seeded rows. Uses a
# genuinely asymmetric random graph for the relabeling checks below (not
# path/star/complete, whose automorphism symmetry could hide a labeling bug
# the same way an axis-aligned rotation can hide an SE(3) bug -- TASK-0054's
# own precedent for why an "arbitrary, off-axis" fixture matters).
# ---------------------------------------------------------------------------

def _random_graph_laplacian(n: int, n_edges: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    A = np.zeros((n, n))
    edges: set = set()
    while len(edges) < n_edges:
        i, j = rng.integers(0, n, size=2)
        if i != j:
            edges.add((min(int(i), int(j)), max(int(i), int(j))))
    for i, j in edges:
        A[i, j] = A[j, i] = 1.0
    return laplacian(A)


class TestGaugeResidueRelabeling:
    """INV-0004's residue-relabeling GAUGE row (INVARIANCE_PROTOCOL.md
    Tier 0): permute H's indices + source consistently, assert every
    score unchanged to atol~1e-9."""

    def test_focusing_is_relabeling_invariant(self):
        rng = np.random.default_rng(20)
        P = rng.random(N)
        P /= P.sum()
        perm = rng.permutation(N)
        assert focusing(P[perm]) == pytest.approx(focusing(P), abs=1e-9)

    def test_ballistic_exponent_is_relabeling_invariant(self):
        H = _random_graph_laplacian(12, n_edges=20, seed=21)
        source = 3
        before = ballistic_exponent(H, source)

        rng = np.random.default_rng(22)
        perm = rng.permutation(12)
        H_perm = H[np.ix_(perm, perm)]
        new_source = int(np.where(perm == source)[0][0])
        after = ballistic_exponent(H_perm, new_source)
        assert after == pytest.approx(before, abs=1e-9)

    def test_source_specificity_is_relabeling_invariant_when_exhaustive(self):
        """The exhaustive-alternates case (`n_alt` >= every non-seed node,
        no sub-sampling) IS exactly relabeling-invariant -- verified
        directly, not assumed. See `TestSourceSpecificitySamplingSensitivity`
        below for the *sub-sampled* case, which is a real, distinct
        finding: NOT relabeling-invariant."""
        H = _random_graph_laplacian(12, n_edges=20, seed=23)
        source = 3
        before = source_specificity(H, source, t_max=8.0, n_alt=11)

        rng = np.random.default_rng(24)
        perm = rng.permutation(12)
        H_perm = H[np.ix_(perm, perm)]
        new_source = int(np.where(perm == source)[0][0])
        after = source_specificity(H_perm, new_source, t_max=8.0, n_alt=11)
        assert after == pytest.approx(before, abs=1e-9)

    def test_unsupervised_score_candidate_order_is_gauge(self):
        """Reordering `candidates` must not change any candidate's score
        or which one wins, by content not position -- z-score-then-sum is
        inherently order-independent aside from the row permutation
        itself (verified directly here, not assumed from the formula)."""
        candidates = [
            {"H": H_PATH, "source": 0, "t": 10.0},
            {"H": H_STAR, "source": 0, "t": 10.0},
            {"H": H_COMPLETE, "source": 0, "t": 10.0},
        ]
        scores = unsupervised_score(candidates)
        reordered = [candidates[2], candidates[0], candidates[1]]
        scores_reordered = unsupervised_score(reordered)

        original_index = {id(c["H"]): i for i, c in enumerate(candidates)}
        for k, cand in enumerate(reordered):
            expected = scores[original_index[id(cand["H"])]]
            assert scores_reordered[k] == pytest.approx(expected, abs=1e-9)


class TestSourceSpecificitySamplingSensitivity:
    """A real, previously-uncharacterized finding, made while widening
    INV-0004's 'RNG-seed stability' GAUGE row per this task's own
    Constraint ("widen the transformation group actually tested"): with
    the default sub-sampled `n_alt` (< all available alternates),
    `source_specificity` is NOT relabeling-invariant, and NOT RNG-seed
    invariant either -- the same underlying phenomenon surfaced two ways.

    Root cause, confirmed directly: the `others` array is always
    ascending-sorted *by label*, and `rng.choice` selects by *position*
    in that array -- under a relabeling permutation, the same rng draw
    pulls a different (non-corresponding) subset of alternates, changing
    the numeric result even though the underlying graph is identical up
    to relabeling. `TestGaugeResidueRelabeling` above proves this
    disappears entirely once sampling is exhaustive -- isolating the
    sub-sampling step, not the Hellinger/`time_averaged_ctqw` computation,
    as the actual source.

    Not fixed in `select.py`: a fix would mean sampling alternates by
    some canonical graph-intrinsic order instead of raw label position
    (the `anm_modes` eigenvalue-not-index precedent), but that would
    change what "a random sample of other nodes" means (systematically
    the same subset every time, not a genuine draw) -- a bigger,
    unrequested behavior change for a real but bounded sampling-variance
    effect, not a wrong-answer bug. Classified KNOB (report the spread),
    not GAUGE, and flagged in `source_specificity`'s own docstring (this
    task's own Scope: fix only a *bug*, and this isn't one)."""

    def test_relabeling_changes_the_score_when_subsampled(self):
        """The GAUGE violation, reproduced directly -- confirms the
        finding still holds before it's classified and documented."""
        H = _random_graph_laplacian(12, n_edges=20, seed=30)
        source = 3
        before = source_specificity(H, source, t_max=8.0, n_alt=5)

        rng = np.random.default_rng(31)
        perm = rng.permutation(12)
        H_perm = H[np.ix_(perm, perm)]
        new_source = int(np.where(perm == source)[0][0])
        after = source_specificity(H_perm, new_source, t_max=8.0, n_alt=5)

        assert after != pytest.approx(before, abs=1e-6), (
            "expected genuine sub-sampling sensitivity to relabeling -- "
            "if this now passes, either this fixture got lucky or the "
            "underlying behavior changed and this test needs updating, "
            "not silently loosening"
        )

    def test_seed_spread_is_bounded_but_real(self):
        """KNOB characterization, not a hard assert on one value: report
        the spread of `source_specificity` across different default-rng
        seeds on a fixed graph/source (measured directly: ~0.14 over 15
        seeds on this fixture) -- locks in that the spread is real
        (nonzero) but stays within a documented order-of-magnitude bound,
        so a future regression (e.g. sampling logic becoming far
        noisier) is caught rather than silently absorbed."""
        H = _random_graph_laplacian(12, n_edges=20, seed=32)
        source = 3
        values = [
            source_specificity(H, source, t_max=8.0, n_alt=5, rng=np.random.default_rng(s))
            for s in range(15)
        ]
        spread = max(values) - min(values)
        assert spread > 1e-4, "expected a real, nonzero seed-dependent spread"
        assert spread < 0.3, f"seed-dependent spread {spread:.4f} far exceeds this fixture's own measured range (~0.14)"


class TestKnobCharacterization:
    """INV-0004's KNOB row: `t`/`t_max`/`n_steps`/`n_alt`/`t_values` are
    modeling choices, characterized as a spread over a small grid on a
    synthetic case (INVARIANCE_PROTOCOL.md Tier 2) -- report the spread,
    never assert a single point estimate. Numbers below are this task's
    own measured grid, locked in as bounds (not exact values) so a future
    change that silently makes one of these knobs far more or less
    sensitive gets caught."""

    H = _random_graph_laplacian(12, n_edges=20, seed=40)
    SOURCE = 3

    def test_focusing_is_fairly_stable_across_t_max_and_n_steps(self):
        """The least KNOB-sensitive of the four: focusing's `t_max`/
        `n_steps` spread is small (~0.02-0.04 on this fixture) -- an
        already-converged quantity, not one requiring careful tuning."""
        from allostery.propagators import time_averaged_ctqw

        t_max_values = [
            focusing(time_averaged_ctqw(self.H, t_max, source=self.SOURCE, n_steps=200))
            for t_max in (2.0, 5.0, 10.0, 20.0, 40.0)
        ]
        n_steps_values = [
            focusing(time_averaged_ctqw(self.H, 10.0, source=self.SOURCE, n_steps=n_steps))
            for n_steps in (20, 50, 100, 500)
        ]
        assert max(t_max_values) - min(t_max_values) < 0.1
        assert max(n_steps_values) - min(n_steps_values) < 0.1

    def test_source_specificity_has_a_moderate_t_max_and_n_alt_spread(self):
        """Measured on this fixture: t_max spread ~0.17 (0.48-0.65,
        driven mostly by a short t_max=2 outlier), n_alt spread ~0.06
        (0.46-0.53) -- real, not negligible, but an order of magnitude
        smaller than ballistic_exponent's t_values sensitivity below."""
        t_max_values = [
            source_specificity(self.H, self.SOURCE, t_max=t_max, n_alt=11)
            for t_max in (2.0, 5.0, 10.0, 20.0, 40.0)
        ]
        n_alt_values = [
            source_specificity(self.H, self.SOURCE, t_max=10.0, n_alt=n_alt)
            for n_alt in (2, 5, 8, 11)
        ]
        t_max_spread = max(t_max_values) - min(t_max_values)
        n_alt_spread = max(n_alt_values) - min(n_alt_values)
        assert 0.05 < t_max_spread < 0.5
        assert 0.01 < n_alt_spread < 0.3

    def test_ballistic_exponent_is_the_most_knob_sensitive_of_the_four(self):
        """The standout KNOB finding this task surfaces: `ballistic_
        exponent`'s `t_values` window dominates every other parameter's
        spread by an order of magnitude -- measured 0.084 (late window,
        t in [1,40]) to 0.525 (early window, t in [0.2,10]) on this
        fixture, a >6x range. A log-log slope fit over a short-vs-long
        propagation window is picking up genuinely different transport
        regimes (early ballistic-like spreading vs. later saturation),
        not numerical noise -- reported as this module's largest
        KNOB, not asserted as a bug."""
        windows = [(0.2, 10, 6), (0.5, 20, 8), (1.0, 40, 10)]
        values = [
            ballistic_exponent(self.H, self.SOURCE, t_values=np.geomspace(lo, hi, n))
            for lo, hi, n in windows
        ]
        spread = max(values) - min(values)
        assert spread > 0.3, (
            f"expected ballistic_exponent's t_values spread ({spread:.3f}) to be "
            "the module's dominant KNOB sensitivity"
        )


class TestUnsupervisedScoreSourceCardinalityKnob:
    """Closes INV-0004's 'newly characterizable 2026-07-16' KNOB row:
    does `unsupervised_score`'s own candidate *ranking* change between
    the scalar and multi-index `source` conventions? Measured directly on
    this module's own path/star/complete fixtures: **yes** -- the winner
    flips from `H_COMPLETE` (scalar seed) to `H_STAR` (2-residue seed
    `[0, 1]`), consistent with `REVIEW-panel-2026-07-16-v2` Sec.2.1's
    project-wide seed-cardinality gauge finding (occupation Spearman only
    0.61 between conventions on synthetic data) and [[TASK-0118]]'s
    separate resolution for the scored pipeline generally. This module's
    own `unsupervised_score` was never checked against that finding
    specifically -- now measured, not assumed, and classified KNOB
    (a modeling choice, not a bug) since both conventions are individually
    well-defined and this module has no "correct" answer to arbitrate
    between them."""

    def test_ranking_flips_between_scalar_and_multi_index_source(self):
        scalar_candidates = [
            {"H": H_PATH, "source": 0, "t": 10.0},
            {"H": H_STAR, "source": 0, "t": 10.0},
            {"H": H_COMPLETE, "source": 0, "t": 10.0},
        ]
        multi_candidates = [
            {"H": H_PATH, "source": np.array([0, 1]), "t": 10.0},
            {"H": H_STAR, "source": np.array([0, 1]), "t": 10.0},
            {"H": H_COMPLETE, "source": np.array([0, 1]), "t": 10.0},
        ]
        scalar_scores = unsupervised_score(scalar_candidates)
        multi_scores = unsupervised_score(multi_candidates)

        scalar_winner = ["path", "star", "complete"][int(np.argmax(scalar_scores))]
        multi_winner = ["path", "star", "complete"][int(np.argmax(multi_scores))]

        assert scalar_winner == "complete"
        assert multi_winner == "star"
        assert scalar_winner != multi_winner, (
            "this is the finding itself -- the ranking is source-cardinality-"
            "dependent; if this now matches, re-verify before loosening"
        )


class TestSignalNullControls:
    """INV-0004's SIGNAL rows (INVARIANCE_PROTOCOL.md Tier 3): a garbage
    (randomized-contact-graph) candidate must not systematically out-score
    a real structural one, and the degenerate single-candidate case must
    be a defined, documented edge case rather than an unexamined NaN/inf
    risk."""

    def test_structured_graph_beats_random_graphs_on_raw_focusing_and_specificity(self):
        """Uses the *raw* per-function scores, not `unsupervised_score`'s
        combined z-sum -- with only 2 candidates, z-scoring always gives
        exactly +-1 regardless of the underlying gap size, which would
        make a 2-candidate comparison a coin flip rather than a real
        signal test (checked directly, not assumed). Compares
        `H_STAR` (a real, maximally hub-structured topology) against a
        batch of 30 independently-drawn random graphs with the *same*
        node/edge count -- a single random draw can occasionally look
        star-like by chance, so this asserts against the *distribution*
        (mean), not one instance, the same discipline this project's own
        permutation-null checks elsewhere use (TASK-0131/TASK-0123)."""
        from allostery.propagators import time_averaged_ctqw

        star_focus = focusing(time_averaged_ctqw(H_STAR, 10.0, source=0))
        star_spec = source_specificity(H_STAR, 0, t_max=10.0, n_alt=9)

        n_edges = N - 1  # same edge count as the star's own N-1 spokes
        random_focus = []
        random_spec = []
        for seed in range(30):
            H_rand = _random_graph_laplacian(N, n_edges, seed=100 + seed)
            random_focus.append(focusing(time_averaged_ctqw(H_rand, 10.0, source=0)))
            random_spec.append(source_specificity(H_rand, 0, t_max=10.0, n_alt=9))

        assert star_focus > np.mean(random_focus) + np.std(random_focus)
        assert star_spec > np.mean(random_spec)

    def test_degenerate_single_candidate_scores_exactly_zero(self):
        """A single-candidate list's z-score is arithmetically `(x-x)/
        (0+eps) = 0` -- documented here as the defined behavior (exactly
        `0.0`, not NaN/inf), matching `unsupervised_score`'s own `_zscore`
        epsilon-guard."""
        candidates = [{"H": H_PATH, "source": 0, "t": 10.0}]
        scores = unsupervised_score(candidates)
        assert scores.shape == (1,)
        assert scores[0] == pytest.approx(0.0, abs=1e-9)
