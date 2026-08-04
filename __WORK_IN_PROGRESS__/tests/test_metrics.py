"""TASK-0123 -- unit tests for `metrics.stratified_auc`/`stratified_auc_
summary`. No dedicated `test_metrics.py` existed before this task (`auc`/
`precision_at_k`/etc. are exercised indirectly through other modules'
tests) -- scoped to the two new functions this task adds, not a
retroactive full-module test file.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.metrics import (  # noqa: E402
    auc,
    block_bootstrap_ci,
    eff_rank,
    participation_ratio_rank,
    spatial_block_bootstrap_ci,
    stratified_auc,
    stratified_auc_summary,
    variance_explained_count,
)


class TestStratifiedAuc:
    def test_isolates_the_pocket_from_a_pure_distance_confound(self):
        """The core case this task exists for: scores are *exactly* a
        function of shell (mimicking real occupation-decays-with-distance
        propagator behavior) and labels happen to cluster in the nearest
        shell -- whole-graph AUC is inflated by pure distance, but no
        real within-shell signal exists (every residue in a shell has an
        identical score), so every scorable shell's stratified AUC must
        be exactly 0.5 (no discrimination possible from tied scores),
        the panel's own "observable dead" signature."""
        shells = np.array([0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2])
        scores = -shells.astype(float)  # occupation decays with distance
        labels = np.array([1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0])  # cluster near shell 0

        whole_graph_auc = auc(scores, labels)
        assert whole_graph_auc > 0.8, "fixture must actually show the confound"

        result = stratified_auc(scores, labels, shells)
        assert set(result) == {0.0, 1.0}  # shell 2 has zero positives -- excluded
        for shell_stats in result.values():
            assert shell_stats["auc"] == pytest.approx(0.5)

    def test_reveals_a_real_within_shell_signal(self):
        """Same shell/label structure as above, but this time a real,
        shell-independent signal is added on top of the distance
        baseline (positive residues score slightly higher *within their
        own shell*) -- stratified AUC in the shells that contain both
        labels must now clear 0.5, proving the metric can see real
        signal the confound would otherwise mask entirely."""
        shells = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        labels = np.array([1, 1, 0, 0, 1, 1, 0, 0])
        # distance baseline + a real within-shell bump for positives
        scores = -shells.astype(float) + 0.5 * labels

        result = stratified_auc(scores, labels, shells)
        assert set(result) == {0.0, 1.0}
        for shell_stats in result.values():
            assert shell_stats["auc"] == pytest.approx(1.0)

    def test_excludes_shells_with_no_positives_or_no_negatives(self):
        shells = np.array([0, 0, 1, 1, 1])
        labels = np.array([1, 1, 0, 0, 0])  # shell 0 all-positive, shell 1 all-negative
        scores = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        result = stratified_auc(scores, labels, shells)
        assert result == {}

    def test_respects_min_pos_min_neg_thresholds(self):
        shells = np.array([0, 0, 0, 1, 1, 1])
        labels = np.array([1, 0, 0, 1, 1, 0])
        scores = np.array([0.9, 0.1, 0.2, 0.8, 0.7, 0.1])
        # shell 0: 1 pos / 2 neg -- scorable at defaults
        # shell 1: 2 pos / 1 neg -- scorable at defaults
        default = stratified_auc(scores, labels, shells)
        assert set(default) == {0.0, 1.0}
        # requiring 2 positives excludes shell 0 (only 1 positive)
        strict = stratified_auc(scores, labels, shells, min_pos=2)
        assert set(strict) == {1.0}

    def test_n_pos_n_neg_reported_correctly(self):
        shells = np.array([0, 0, 0, 0])
        labels = np.array([1, 1, 0, 0])
        scores = np.array([0.9, 0.8, 0.2, 0.1])
        result = stratified_auc(scores, labels, shells)
        assert result[0.0]["n_pos"] == 2
        assert result[0.0]["n_neg"] == 2

    def test_returns_empty_dict_when_no_shell_is_scorable(self):
        shells = np.array([0, 0, 1, 1])
        labels = np.array([1, 1, 1, 1])  # no negatives anywhere
        scores = np.array([0.1, 0.2, 0.3, 0.4])
        assert stratified_auc(scores, labels, shells) == {}


class TestStratifiedAucSummary:
    def test_empty_input_gives_nan_not_a_crash(self):
        summary = stratified_auc_summary({})
        assert summary["n_scorable_shells"] == 0
        assert np.isnan(summary["mean_auc"])
        assert np.isnan(summary["max_auc"])
        assert summary["max_shell"] is None

    def test_picks_the_max_shell_correctly(self):
        stratified = {
            0.0: {"auc": 0.5, "n_pos": 2, "n_neg": 2},
            1.0: {"auc": 0.9, "n_pos": 2, "n_neg": 2},
            2.0: {"auc": 0.6, "n_pos": 2, "n_neg": 2},
        }
        summary = stratified_auc_summary(stratified)
        assert summary["n_scorable_shells"] == 3
        assert summary["max_auc"] == pytest.approx(0.9)
        assert summary["max_shell"] == 1.0
        assert summary["mean_auc"] == pytest.approx((0.5 + 0.9 + 0.6) / 3)

    def test_ignores_nan_shell_aucs_in_the_summary(self):
        """A shell's own AUC can itself be NaN in principle (degenerate
        within-shell labels slipping through a caller-supplied `shells`
        array that wasn't built via `stratified_auc` itself) -- the
        summary must not let a stray NaN poison mean/max."""
        stratified = {
            0.0: {"auc": float("nan"), "n_pos": 2, "n_neg": 0},
            1.0: {"auc": 0.7, "n_pos": 2, "n_neg": 2},
        }
        summary = stratified_auc_summary(stratified)
        assert summary["mean_auc"] == pytest.approx(0.7)
        assert summary["max_auc"] == pytest.approx(0.7)
        assert summary["max_shell"] == 1.0


def _globule(n=200, seed=0):
    """`scripts/null_audit.py`'s own compact-globule fixture, reused
    (not re-derived) -- TASK-0158's established synthetic control for
    spatial-autocorrelation questions."""
    rng = np.random.default_rng(seed)
    pts = [np.zeros(3)]
    for _ in range(n - 1):
        for _try in range(200):
            step = rng.normal(size=3)
            step /= np.linalg.norm(step)
            cand = pts[-1] + 3.8 * step
            if np.linalg.norm(cand) < 2.2 * n ** (1 / 3) * 1.6:
                d = np.linalg.norm(np.asarray(pts) - cand, axis=1)
                if d.min() > 3.2:
                    break
        pts.append(cand)
    return np.asarray(pts)


class TestSpatialBlockBootstrapCi:
    """TASK-0165 -- `spatial_block_bootstrap_ci`, `block_bootstrap_ci`'s
    own spatial-neighbourhood-blocked companion."""

    def test_matches_return_shape_of_sequence_block_version(self):
        rng = np.random.default_rng(1)
        n = 50
        coords = _globule(n, seed=1)
        scores = rng.normal(size=n)
        labels = np.zeros(n, dtype=int)
        labels[:10] = 1
        result = spatial_block_bootstrap_ci(coords, scores, labels, n_boot=50, rng=rng)
        assert len(result) == 3
        point, lo, hi = result
        assert lo <= point <= hi

    def test_close_to_sequence_block_on_a_1d_line_with_matching_order(self):
        """**Corrected claim (TASK-0167.002, external review §2.2)**: this
        does NOT test that the two functions' own resampled index sets
        coincide -- they don't (~55% mean overlap, measured directly), since
        `block_bootstrap_ci`'s window is asymmetric/forward-only from its
        start index while this function's own k-NN block is symmetric/
        centred, even on a 1D line matching sequence order. This test only
        checks that the two methods' aggregate CI *widths* land close to
        each other on this control (a weaker property than index-set
        coincidence, and the only one asserted here) -- kept as a
        regression guard on that weaker property, not evidence for the
        stronger claim this test's own name previously implied."""
        n = 200
        coords = np.column_stack([np.arange(n, dtype=float), np.zeros(n), np.zeros(n)])
        rng_state = np.random.default_rng(7)
        scores = rng_state.normal(size=n) + 0.3 * np.sin(np.arange(n) / 5.0)
        labels = np.zeros(n, dtype=int)
        labels[20:30] = 1  # a sequence-contiguous (= spatially contiguous here) pocket

        seq_result = block_bootstrap_ci(scores, labels, n_boot=2000, block_size=10, rng=np.random.default_rng(99))
        spatial_result = spatial_block_bootstrap_ci(
            coords, scores, labels, n_boot=2000, block_size=10, rng=np.random.default_rng(99)
        )
        assert seq_result[0] == pytest.approx(spatial_result[0])  # point estimate always matches exactly
        assert spatial_result[1] == pytest.approx(seq_result[1], abs=0.03)
        assert spatial_result[2] == pytest.approx(seq_result[2], abs=0.03)

    def test_widens_ci_for_a_sequence_scattered_spatially_compact_pocket(self):
        """The whole motivating case: a pocket that is spatially compact
        but scattered in sequence index. Sequence-blocking treats its
        residues as independent (they're far apart in the array); spatial
        blocking correctly identifies them as correlated -- the spatial CI
        should be markedly wider.

        `_globule`'s own random-walk build order keeps *some* accidental
        correlation between sequence index and 3D position (consecutive
        build steps are 3.8 A apart), which real protein sequence/fold
        relationships mostly don't preserve beyond local secondary
        structure -- explicitly permuting sequence index against 3D
        position removes that accident and gives a clean, realistic
        "compact in space, scattered in sequence" fixture (checked
        directly: without this shuffle, the widening was inconsistent
        across seeds; with it, it is robust across every seed tried)."""
        n = 300
        coords = _globule(n, seed=2)
        coords = coords[np.random.default_rng(102).permutation(n)]
        rng = np.random.default_rng(3)
        # A smooth score field correlated with distance from a fixed point
        # (a stand-in for any propagator-based observable's own spatial
        # smoothness) plus noise.
        centre = coords[rng.integers(n)]
        scores = -np.linalg.norm(coords - centre, axis=1) + 0.3 * rng.normal(size=n)

        # Pocket: spatially compact (nearest neighbours of a random point),
        # scattered in sequence index (the shuffle above).
        c = rng.integers(n)
        pocket_idx = np.argsort(np.linalg.norm(coords - coords[c], axis=1))[:14]
        labels = np.zeros(n, dtype=int)
        labels[pocket_idx] = 1

        seq_point, seq_lo, seq_hi = block_bootstrap_ci(
            scores, labels, n_boot=1000, block_size=10, rng=np.random.default_rng(11)
        )
        sp_point, sp_lo, sp_hi = spatial_block_bootstrap_ci(
            coords, scores, labels, n_boot=1000, block_size=10, rng=np.random.default_rng(11)
        )
        assert sp_point == pytest.approx(seq_point)
        seq_width = seq_hi - seq_lo
        sp_width = sp_hi - sp_lo
        assert sp_width > seq_width, (
            f"spatial CI ({sp_width:.4f}) was not wider than sequence CI ({seq_width:.4f}) "
            f"for a spatially-compact, sequence-scattered pocket"
        )


class TestParticipationRatioRank:
    """TASK-0199 -- the primary effective-rank statistic for the
    cross-observable correlation matrix. Both controls are the ones this
    task's own Planned Validation specifies: identity (fully independent)
    -> rank ~= M; single-dominant-component -> rank ~= 1.
    """

    def test_identity_spectrum_gives_full_rank(self):
        """A correlation matrix of M mutually orthogonal variables has
        eigenvalues all equal to 1 -- participation ratio = M exactly."""
        M = 10
        eigenvalues = np.ones(M)
        assert participation_ratio_rank(eigenvalues) == pytest.approx(M)

    def test_single_dominant_component_gives_rank_one(self):
        """All variance in one eigenvalue (M-1 exactly-zero eigenvalues,
        the rest summing to trace=M) -- participation ratio = 1."""
        M = 10
        eigenvalues = np.zeros(M)
        eigenvalues[0] = M
        assert participation_ratio_rank(eigenvalues) == pytest.approx(1.0)

    def test_intermediate_case_between_bounds(self):
        """Two equal dominant components, rest zero -- rank should land
        at exactly 2 (participation ratio of two equal eigenvalues)."""
        M = 10
        eigenvalues = np.zeros(M)
        eigenvalues[:2] = M / 2
        assert participation_ratio_rank(eigenvalues) == pytest.approx(2.0)

    def test_matches_eff_rank_direction_but_is_a_different_statistic(self):
        """eff_rank (entropy-based) and participation_ratio_rank both
        drop for a more concentrated spectrum and both rise for a flatter
        one -- but are not numerically identical, confirming they are
        genuinely two different definitions, not a duplicate."""
        concentrated = np.array([8.0, 1.0, 0.5, 0.5])
        flat = np.array([2.5, 2.5, 2.5, 2.5])
        assert participation_ratio_rank(concentrated) < participation_ratio_rank(flat)
        assert eff_rank(concentrated) < eff_rank(flat)
        # Both correctly converge to exactly M on a perfectly flat spectrum
        # (degenerate case for either formula) -- the two definitions only
        # diverge numerically on a genuinely non-uniform one.
        assert participation_ratio_rank(concentrated) != pytest.approx(eff_rank(concentrated))


class TestVarianceExplainedCount:
    def test_needs_all_components_when_flat(self):
        eigenvalues = np.array([1.0, 1.0, 1.0, 1.0])
        assert variance_explained_count(eigenvalues, threshold=0.90) == 4

    def test_one_component_suffices_when_dominant(self):
        eigenvalues = np.array([100.0, 0.01, 0.01, 0.01])
        assert variance_explained_count(eigenvalues, threshold=0.90) == 1

    def test_threshold_90_le_threshold_95(self):
        rng = np.random.default_rng(0)
        eigenvalues = np.abs(rng.normal(size=8)) + 0.1
        k90 = variance_explained_count(eigenvalues, threshold=0.90)
        k95 = variance_explained_count(eigenvalues, threshold=0.95)
        assert k90 <= k95
