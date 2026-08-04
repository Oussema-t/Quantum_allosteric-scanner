"""TASK-0158 -- tests for `allostery.nulls` (spatially compact permutation
null). Validates the ported `compact_patch` against `scripts/null_audit.py`/
`null_audit2.py`'s own reproduced numbers (not re-derived from scratch),
and confirms the corrected null actually fixes the calibration problem it
was built to fix: a compact-vs-compact comparison should NOT show the
scattered-vs-compact inflation `null_audit2.py` found.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from allostery.baselines import hop_from_seed
from allostery.lowmode_predictor import dcc_low
from allostery.metrics import stratified_auc
from allostery.nulls import (
    build_adjacency,
    compact_patch,
    compact_patch_from_pool,
    compact_patch_matched,
    graph_walk_patch,
    graph_walk_patch_matched,
    radius_of_gyration,
)
from null_audit import make_globule, scattered_patch, well_powered_max  # noqa: E402


class TestCompactPatch:
    def test_returns_requested_size(self):
        coords = make_globule(200, seed=1)
        rng = np.random.default_rng(0)
        idx = compact_patch(coords, 14, rng)
        assert len(idx) == 14
        assert len(set(idx.tolist())) == 14

    def test_is_spatially_tighter_than_scattered(self):
        """The whole premise: a compact patch has a much smaller radius
        of gyration than a scattered same-size subset, on average."""
        coords = make_globule(300, seed=2)
        rng = np.random.default_rng(1)
        compact_rgs = [radius_of_gyration(coords, compact_patch(coords, 14, rng)) for _ in range(50)]
        scattered_rgs = [radius_of_gyration(coords, scattered_patch(coords, 14, rng)) for _ in range(50)]
        assert np.mean(compact_rgs) < 0.5 * np.mean(scattered_rgs)

    def test_deterministic_given_rng_state(self):
        coords = make_globule(100, seed=3)
        idx1 = compact_patch(coords, 10, np.random.default_rng(42))
        idx2 = compact_patch(coords, 10, np.random.default_rng(42))
        np.testing.assert_array_equal(idx1, idx2)


class TestCompactPatchFromPool:
    def test_returns_indices_within_pool_only(self):
        coords = make_globule(200, seed=8)
        rng = np.random.default_rng(9)
        pool = np.arange(50, 200)  # exclude first 50 (e.g. "seed" residues)
        idx = compact_patch_from_pool(coords, pool, 14, rng)
        assert len(idx) == 14
        assert set(idx.tolist()) <= set(pool.tolist())

    def test_matches_plain_rng_choice_interface(self):
        """Drop-in replacement check: same call shape as `rng.choice(pool,
        size=size, replace=False)` -- returns original-array indices,
        not pool-relative ones."""
        coords = make_globule(150, seed=10)
        rng = np.random.default_rng(11)
        pool = np.array([3, 7, 11, 15, 20, 25, 30, 40, 55, 70, 90, 100, 120, 140, 149])
        idx = compact_patch_from_pool(coords, pool, 5, rng)
        assert idx.max() < 150
        assert set(idx.tolist()) <= set(pool.tolist())


class TestCompactPatchMatched:
    def test_matches_target_radius_of_gyration_within_tolerance(self):
        coords = make_globule(400, seed=4)
        rng = np.random.default_rng(5)
        target_rg = 6.0
        idx = compact_patch_matched(coords, 14, rng, target_rg=target_rg, tol=0.35)
        rg = radius_of_gyration(coords, idx)
        assert 0.65 * target_rg <= rg <= 1.35 * target_rg

    def test_raises_when_infeasible(self):
        coords = make_globule(100, seed=6)
        rng = np.random.default_rng(7)
        with np.testing.assert_raises(RuntimeError):
            compact_patch_matched(coords, 14, rng, target_rg=0.001, tol=0.01, max_attempts=200)

    def test_return_attempts_false_is_byte_identical_default(self):
        """TASK-0190: return_attempts defaults False -- every existing
        call site's return shape (bare idx) is unaffected."""
        coords = make_globule(400, seed=4)
        rng1 = np.random.default_rng(5)
        rng2 = np.random.default_rng(5)
        idx_default = compact_patch_matched(coords, 14, rng1, target_rg=6.0, tol=0.35)
        idx_explicit = compact_patch_matched(coords, 14, rng2, target_rg=6.0, tol=0.35, return_attempts=False)
        assert isinstance(idx_default, np.ndarray)
        np.testing.assert_array_equal(idx_default, idx_explicit)

    def test_return_attempts_true_returns_idx_and_count(self):
        coords = make_globule(400, seed=4)
        rng = np.random.default_rng(5)
        idx, n_attempts = compact_patch_matched(coords, 14, rng, target_rg=6.0, tol=0.35, return_attempts=True)
        rg = radius_of_gyration(coords, idx)
        assert 0.65 * 6.0 <= rg <= 1.35 * 6.0
        assert isinstance(n_attempts, int)
        assert n_attempts >= 1

    def test_return_attempts_count_matches_manual_replay(self):
        """The reported attempt count is exactly the number of
        compact_patch draws consumed -- verified by replaying the same
        seeded rng manually and counting draws until the same acceptance
        condition first holds."""
        coords = make_globule(400, seed=4)
        target_rg, tol = 6.0, 0.35
        lo, hi = target_rg * (1 - tol), target_rg * (1 + tol)

        rng_a = np.random.default_rng(9)
        _, n_attempts = compact_patch_matched(coords, 14, rng_a, target_rg=target_rg, tol=tol, return_attempts=True)

        rng_b = np.random.default_rng(9)
        manual_count = 0
        while True:
            manual_count += 1
            idx = compact_patch(coords, 14, rng_b)
            if lo <= radius_of_gyration(coords, idx) <= hi:
                break
        assert manual_count == n_attempts


class TestGraphWalkPatch:
    """TASK-0201: a second compact-ish family, grown by randomized
    connected expansion on the residue contact graph rather than
    Euclidean-nearest-neighbour selection -- built specifically because
    `compact_patch`'s own Rg support has a hard, real ceiling
    (TASK-0190's finding) that sits below real pocket Rg on 2/3 targets
    tested."""

    def test_returns_requested_size(self):
        coords = make_globule(200, seed=1)
        adjacency = build_adjacency(coords, cutoff=10.0)
        rng = np.random.default_rng(0)
        idx = graph_walk_patch(adjacency, 14, rng)
        assert len(idx) == 14
        assert len(set(idx.tolist())) == 14

    def test_is_contiguous_on_the_contact_graph(self):
        """Every member (after the seed) must be graph-adjacent to at
        least one other member -- 'contiguous', the property that
        distinguishes this from a scattered draw, even though its
        Euclidean footprint is wider than compact_patch's."""
        coords = make_globule(200, seed=1)
        adjacency = build_adjacency(coords, cutoff=10.0)
        rng = np.random.default_rng(2)
        for _ in range(20):
            idx = graph_walk_patch(adjacency, 14, rng)
            idx_set = set(idx.tolist())
            for i in idx_set:
                neighbours = set(adjacency[i].tolist())
                assert neighbours & (idx_set - {i}), (
                    f"residue {i} has no neighbour within the drawn patch -- not contiguous"
                )

    def test_deterministic_given_rng_state(self):
        coords = make_globule(100, seed=3)
        adjacency = build_adjacency(coords, cutoff=10.0)
        idx1 = graph_walk_patch(adjacency, 10, np.random.default_rng(42))
        idx2 = graph_walk_patch(adjacency, 10, np.random.default_rng(42))
        np.testing.assert_array_equal(idx1, idx2)

    def test_reaches_wider_rg_than_compact_patch(self):
        """The whole point: on the same coords/size, graph_walk_patch's
        own max Rg over many draws must exceed compact_patch's own max
        by a real margin -- not just occasionally, reliably."""
        coords = make_globule(300, seed=2)
        adjacency = build_adjacency(coords, cutoff=10.0)
        rng_c = np.random.default_rng(1)
        rng_w = np.random.default_rng(1)
        compact_rgs = [radius_of_gyration(coords, compact_patch(coords, 14, rng_c)) for _ in range(300)]
        walk_rgs = [radius_of_gyration(coords, graph_walk_patch(adjacency, 14, rng_w)) for _ in range(300)]
        assert max(walk_rgs) > 1.3 * max(compact_rgs)


class TestGraphWalkPatchMatched:
    def test_matches_target_radius_of_gyration_within_tolerance(self):
        coords = make_globule(400, seed=4)
        adjacency = build_adjacency(coords, cutoff=10.0)
        rng = np.random.default_rng(5)
        target_rg = 6.0
        idx = graph_walk_patch_matched(coords, adjacency, 14, rng, target_rg=target_rg, tol=0.35)
        rg = radius_of_gyration(coords, idx)
        assert 0.65 * target_rg <= rg <= 1.35 * target_rg

    def test_reaches_a_target_beyond_compact_patchs_own_ceiling(self):
        """The actual fix under test: a target_rg that compact_patch_
        matched cannot reach at all (RuntimeError) must be reachable by
        graph_walk_patch_matched on the identical coords/size."""
        coords = make_globule(300, seed=2)
        adjacency = build_adjacency(coords, cutoff=10.0)

        # Find compact_patch's own empirical ceiling first.
        rng_c = np.random.default_rng(1)
        compact_max = max(
            radius_of_gyration(coords, compact_patch(coords, 14, rng_c)) for _ in range(500)
        )
        beyond_ceiling = compact_max * 1.3

        with np.testing.assert_raises(RuntimeError):
            compact_patch_matched(
                coords, 14, np.random.default_rng(6), target_rg=beyond_ceiling,
                tol=0.05, max_attempts=2000,
            )

        idx = graph_walk_patch_matched(
            coords, adjacency, 14, np.random.default_rng(6), target_rg=beyond_ceiling,
            tol=0.20, max_attempts=20_000,
        )
        rg = radius_of_gyration(coords, idx)
        assert 0.80 * beyond_ceiling <= rg <= 1.20 * beyond_ceiling

    def test_raises_when_infeasible(self):
        coords = make_globule(100, seed=6)
        adjacency = build_adjacency(coords, cutoff=10.0)
        rng = np.random.default_rng(7)
        with np.testing.assert_raises(RuntimeError):
            graph_walk_patch_matched(
                coords, adjacency, 14, rng, target_rg=0.001, tol=0.01, max_attempts=200,
            )

    def test_return_attempts_true_returns_idx_and_count(self):
        coords = make_globule(400, seed=4)
        adjacency = build_adjacency(coords, cutoff=10.0)
        rng = np.random.default_rng(5)
        idx, n_attempts = graph_walk_patch_matched(
            coords, adjacency, 14, rng, target_rg=6.0, tol=0.35, return_attempts=True,
        )
        rg = radius_of_gyration(coords, idx)
        assert 0.65 * 6.0 <= rg <= 1.35 * 6.0
        assert isinstance(n_attempts, int)
        assert n_attempts >= 1


class TestCorrectedNullRestoresCalibration:
    """Reproduces `null_audit2.py`'s own numbers directly (not assumed),
    then confirms the actual fix: scoring a compact real-pocket-like
    label against a COMPACT null (instead of the scattered null the repo
    used everywhere) removes the inflation, on the identical smooth
    (`dcc_low`) score field that showed 4.8x/42x inflation against a
    scattered null."""

    def test_reproduces_known_scattered_vs_compact_inflation(self):
        """Sanity re-check of the audit's own headline number (4.8x at
        alpha=0.05) before trusting the fix below -- confirms this test's
        own fixture/seeds reproduce the cited finding, not a different
        setup that happens to also show *some* inflation."""
        N, POCKET, CUTOFF = 500, 14, 10.0
        coords = make_globule(N, seed=1)
        rng = np.random.default_rng(7)
        c0 = rng.integers(N)
        source = np.argsort(np.linalg.norm(coords - coords[c0], axis=1))[:8]
        shells = -hop_from_seed(coords, source, cutoff=CUTOFF)
        score = dcc_low(coords, source, cutoff=CUTOFF, k_modes=20)

        a = []
        rA = np.random.default_rng(101)
        for _ in range(500):
            lab = np.zeros(N, int)
            lab[scattered_patch(coords, POCKET, rA)] = 1
            v = well_powered_max(stratified_auc(score, lab, shells))
            if np.isfinite(v):
                a.append(v)
        a = np.asarray(a)

        b = []
        rB = np.random.default_rng(202)
        for _ in range(300):
            lab = np.zeros(N, int)
            lab[compact_patch(coords, POCKET, rB)] = 1
            v = well_powered_max(stratified_auc(score, lab, shells))
            if np.isfinite(v):
                b.append(v)
        b = np.asarray(b)

        p_assigned = np.array([(a >= x).mean() for x in b])
        inflation = float((p_assigned <= 0.05).mean()) / 0.05
        assert inflation > 3.0, f"expected clear inflation (audit found 4.8x), got {inflation:.2f}x"

    def test_compact_vs_compact_removes_the_inflation(self):
        """The actual fix under test: score a compact null-pocket against
        a null built from `compact_patch` itself (TASK-0158's own
        production draw) instead of `scattered_patch` -- the resulting
        p-values should be close to nominal, not inflated, on the exact
        same smooth score field that showed 4.8x/42x inflation above."""
        N, POCKET, CUTOFF = 500, 14, 10.0
        coords = make_globule(N, seed=1)
        rng = np.random.default_rng(7)
        c0 = rng.integers(N)
        source = np.argsort(np.linalg.norm(coords - coords[c0], axis=1))[:8]
        shells = -hop_from_seed(coords, source, cutoff=CUTOFF)
        score = dcc_low(coords, source, cutoff=CUTOFF, k_modes=20)

        # Null built from the CORRECTED draw.
        null_vals = []
        r_null = np.random.default_rng(303)
        for _ in range(500):
            lab = np.zeros(N, int)
            lab[compact_patch(coords, POCKET, r_null)] = 1
            v = well_powered_max(stratified_auc(score, lab, shells))
            if np.isfinite(v):
                null_vals.append(v)
        null_vals = np.asarray(null_vals)

        # Independent draw of "pure-null compact pockets" to test against
        # that same corrected null (same construction as the audit's own
        # methodology, just with both legs corrected).
        test_vals = []
        r_test = np.random.default_rng(404)
        for _ in range(300):
            lab = np.zeros(N, int)
            lab[compact_patch(coords, POCKET, r_test)] = 1
            v = well_powered_max(stratified_auc(score, lab, shells))
            if np.isfinite(v):
                test_vals.append(v)
        test_vals = np.asarray(test_vals)

        p_assigned = np.array([(null_vals >= x).mean() for x in test_vals])
        fraction_below_005 = float((p_assigned <= 0.05).mean())
        # Nominal is 0.05; allow generous slack for Monte Carlo noise at
        # these replicate counts (audit's own analogous white-noise
        # control landed at 0.004, i.e. UNDER nominal, not over) -- the
        # only thing this test rules out is the >4x inflation confirmed
        # above, not exact-0.05 calibration to 3 decimal places.
        assert fraction_below_005 < 0.15, (
            f"compact-vs-compact still inflated: {fraction_below_005:.3f} "
            f"called p<=0.05 (nominal 0.05, scattered-null comparison showed 0.242)"
        )
