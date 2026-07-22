"""TASK-0143 -- tests for `allostery.closure` (HYP-P10 openness premise)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.closure import (  # noqa: E402
    euclid_dist_matrix,
    graph_dist_matrix,
    matched_spread_null,
    openness_signature,
    pairwise_components,
)


def _chain_coords(n: int, spacing: float = 3.8) -> np.ndarray:
    """A straight-line chain -- every consecutive pair is `spacing` apart,
    every non-consecutive pair is farther. Simplest possible fixture for
    which graph-hop distance and chain-index distance coincide exactly."""
    return np.column_stack([np.arange(n) * spacing, np.zeros(n), np.zeros(n)])


def _horseshoe_coords(n: int, radius: float, gap_angle: float) -> np.ndarray:
    """TASK-0143's own synthetic open-cleft positive control: `n` residues
    on a circular arc of `radius`, spanning `2*pi - gap_angle` radians --
    a horseshoe whose two open ends (residue 0 and residue n-1) are
    Euclidean-close (chord `2*radius*sin(gap_angle/2)`) but graph-far
    (reachable only by traversing almost the entire arc, since the arc
    does not self-intersect anywhere else)."""
    theta_total = 2 * np.pi - gap_angle
    theta = np.linspace(0, theta_total, n)
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    return np.column_stack([x, y, np.zeros(n)])


class TestGraphDistMatrix:
    def test_chain_hop_distance_equals_index_distance(self):
        coords = _chain_coords(10)
        GD = graph_dist_matrix(coords, cutoff=5.0)
        expected = np.abs(np.subtract.outer(np.arange(10), np.arange(10)))
        np.testing.assert_array_equal(GD, expected)

    def test_disconnected_graph_raises(self):
        # Two chains far apart -- no contact edge between them at this cutoff.
        left = _chain_coords(5)
        right = _chain_coords(5) + np.array([1000.0, 0.0, 0.0])
        coords = np.vstack([left, right])
        with pytest.raises(ValueError, match="disconnected"):
            graph_dist_matrix(coords, cutoff=5.0)


class TestOpennessSignature:
    def test_matches_hand_computed_ratio_on_chain(self):
        coords = _chain_coords(6)
        GD = graph_dist_matrix(coords, cutoff=5.0)
        D = euclid_dist_matrix(coords)
        residues = np.array([0, 2, 4])
        # Pairs (0,2),(0,4),(2,4): hop=2,4,2 -> mean=8/3; euclid=7.6,15.2,7.6 -> mean=30.4/3
        got = openness_signature(residues, D, GD)
        expected = (2 + 4 + 2) / 3 / ((7.6 + 15.2 + 7.6) / 3)
        assert got == pytest.approx(expected, rel=1e-9)

    def test_single_residue_raises(self):
        coords = _chain_coords(4)
        GD = graph_dist_matrix(coords, cutoff=5.0)
        D = euclid_dist_matrix(coords)
        with pytest.raises(ValueError, match=">=2"):
            openness_signature(np.array([0]), D, GD)


class TestPairwiseComponents:
    def test_matches_hand_computed_components_on_chain(self):
        coords = _chain_coords(6)
        GD = graph_dist_matrix(coords, cutoff=5.0)
        D = euclid_dist_matrix(coords)
        residues = np.array([0, 2, 4])
        got = pairwise_components(residues, D, GD)
        assert got["graph_hop_mean"] == pytest.approx((2 + 4 + 2) / 3, rel=1e-9)
        assert got["euclid_mean"] == pytest.approx((7.6 + 15.2 + 7.6) / 3, rel=1e-9)

    def test_ratio_of_components_equals_openness_signature(self):
        """The two raw numbers are not a separate computation from the
        ratio -- `openness_signature` is defined as their quotient, and
        this must hold exactly, not approximately, for any real fixture."""
        coords = _horseshoe_coords(30, radius=18.0, gap_angle=0.4)
        GD = graph_dist_matrix(coords, cutoff=8.0)
        D = euclid_dist_matrix(coords)
        residues = np.array([0, 1, 2, 28, 29])
        components = pairwise_components(residues, D, GD)
        ratio = components["graph_hop_mean"] / components["euclid_mean"]
        assert ratio == openness_signature(residues, D, GD)

    def test_always_computable_independent_of_null_feasibility(self):
        """The whole point of exposing these separately: they must be
        obtainable even for a target where `matched_spread_null` itself
        would be infeasible (no rejection-sampling involved here at all)."""
        coords = _chain_coords(10)
        GD = graph_dist_matrix(coords, cutoff=5.0)
        D = euclid_dist_matrix(coords)
        # The unique max-spread pair (see TestMatchedSpreadNull's own
        # infeasibility test below) -- components are still well-defined.
        got = pairwise_components(np.array([0, 9]), D, GD)
        assert got["graph_hop_mean"] == pytest.approx(9.0)
        assert got["euclid_mean"] == pytest.approx(9 * 3.8)


class TestSyntheticOpenCleftPositiveControl:
    """The falsification-apparatus-before-real-data gate this task's own
    Planned Validation requires: reproduce a constructed open-cleft case
    and confirm it lands at the extreme (~100th percentile) of a
    matched-spread null, so a null real-data result cannot be mistaken
    for a silent implementation bug."""

    def test_horseshoe_tips_hit_extreme_percentile(self):
        n = 60
        coords = _horseshoe_coords(n, radius=25.0, gap_angle=0.3)
        GD = graph_dist_matrix(coords, cutoff=8.0)
        D = euclid_dist_matrix(coords)

        # The two open-end tips: Euclidean-close (small chord across the
        # gap), graph-far (only reachable by going around the arc).
        pocket = np.array([0, 1, n - 2, n - 1])
        real_spread = D[np.ix_(pocket, pocket)][np.triu_indices(4, k=1)].mean()
        assert real_spread < 8.0, "synthetic construction sanity: tips must be Euclidean-close"

        result = matched_spread_null(pocket, D, GD, n_null=200, tol=0.35, seed=1)
        assert result["percentile"] >= 95.0, (
            f"synthetic open-cleft control should land near the 100th percentile, "
            f"got {result['percentile']}"
        )

    def test_middle_of_arc_residues_do_not_show_the_signature(self):
        """Negative control: a same-size cluster from the *middle* of the
        arc (nowhere near the gap) should look like an ordinary
        graph-adjacent cluster, not an open-cleft anomaly -- confirms the
        positive control isn't an artifact of the fixture itself (e.g. a
        general bias in this arc geometry)."""
        n = 60
        coords = _horseshoe_coords(n, radius=25.0, gap_angle=0.3)
        GD = graph_dist_matrix(coords, cutoff=8.0)
        D = euclid_dist_matrix(coords)

        mid = n // 2
        pocket = np.array([mid - 1, mid, mid + 1, mid + 2])
        result = matched_spread_null(pocket, D, GD, n_null=50, tol=0.35, seed=2, max_attempts=2_000_000)
        assert result["percentile"] < 95.0


class TestMatchedSpreadNull:
    def test_null_replicates_are_within_tolerance_of_real_spread(self):
        coords = _horseshoe_coords(40, radius=20.0, gap_angle=0.4)
        GD = graph_dist_matrix(coords, cutoff=8.0)
        D = euclid_dist_matrix(coords)
        pocket = np.array([0, 1, 38, 39])
        real_spread = D[np.ix_(pocket, pocket)][np.triu_indices(4, k=1)].mean()

        result = matched_spread_null(pocket, D, GD, n_null=50, tol=0.35, seed=3)
        assert result["n_null"] == 50
        # The raw components must be present and consistent with the ratio
        # already reported as `real_signature` -- not a separate code path.
        assert result["real_euclid_mean"] == pytest.approx(real_spread)
        assert result["real_graph_hop_mean"] / result["real_euclid_mean"] == pytest.approx(result["real_signature"])
        lo, hi = real_spread * 0.65, real_spread * 1.35
        # Re-derive each accepted replicate's implicit spread bound indirectly:
        # every acceptance was gated at draw time, so this is really testing
        # that the function actually enforces its own stated tolerance --
        # done by re-running the same seeded draw sequence and checking the
        # acceptance predicate directly.
        rng = np.random.default_rng(3)
        n_accepted = 0
        attempts = 0
        while n_accepted < 50:
            attempts += 1
            candidate = rng.choice(40, size=4, replace=False)
            spread = D[np.ix_(candidate, candidate)][np.triu_indices(4, k=1)].mean()
            if lo <= spread <= hi:
                n_accepted += 1
        assert attempts == result["n_attempts"]

    def test_infeasible_tolerance_raises_not_silently_short(self):
        coords = _chain_coords(10)
        GD = graph_dist_matrix(coords, cutoff=5.0)
        D = euclid_dist_matrix(coords)
        # The two chain endpoints: the unique maximum-spread pair in this
        # fixture (no other same-size-2 subset comes close) -- a tight
        # tolerance around it has essentially nothing else to match.
        pocket = np.array([0, 9])
        with pytest.raises(RuntimeError, match="infeasible"):
            matched_spread_null(pocket, D, GD, n_null=10, tol=1e-6, seed=0, max_attempts=50)

    def test_seed_reproducibility(self):
        coords = _horseshoe_coords(30, radius=15.0, gap_angle=0.5)
        GD = graph_dist_matrix(coords, cutoff=8.0)
        D = euclid_dist_matrix(coords)
        pocket = np.array([0, 1, 28, 29])
        r1 = matched_spread_null(pocket, D, GD, n_null=30, tol=0.4, seed=42)
        r2 = matched_spread_null(pocket, D, GD, n_null=30, tol=0.4, seed=42)
        assert r1["null_signatures"] == r2["null_signatures"]
