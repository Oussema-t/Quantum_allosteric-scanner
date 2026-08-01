"""TASK-0180 coverage -- sites.py's spatial clustering, site-hit metrics,
chance level, proximity floor, and knob-spread sweep. Synthetic coordinate
sets only (no network) -- same "control-flow/unit tests here, real-target
integration is a separate, network-backed concern" split
`test_run_challenge.py`'s own module docstring already establishes.
"""
import numpy as np
import pytest

from allostery.sites import (
    DEFAULT_LINKAGE_CUTOFF,
    cluster_sites,
    site_chance_level,
    site_hit_metrics,
    site_knob_sweep,
    site_proximity_floor,
)


def _blob(center, n, spread=1.0, seed=0):
    rng = np.random.default_rng(seed)
    return np.asarray(center, dtype=float) + rng.normal(scale=spread, size=(n, 3))


def _helix_coords(n: int) -> np.ndarray:
    """Same convention as test_labels.py/test_run_challenge.py -- rise
    1.5 A/residue, radius 2.3 A, so adjacent residues sit well inside any
    single-linkage cutoff used here (a spatially smooth chain)."""
    theta = np.arange(n) * (100.0 * np.pi / 180.0)
    return np.column_stack([
        2.3 * np.cos(theta),
        2.3 * np.sin(theta),
        1.5 * np.arange(n, dtype=float),
    ])


class TestClusterSites:
    def test_well_separated_blobs_produce_separate_sites(self):
        # Two blobs 200 A apart, each internally tight (spread=1.0) --
        # single-linkage at the default 8.0 A cutoff must not merge them.
        coords = np.vstack([_blob([0, 0, 0], 6, seed=1), _blob([200, 0, 0], 6, seed=2)])
        scores = np.ones(12) * 5.0  # all top-scoring, m covers everyone
        result = cluster_sites(coords, scores, m=12, min_cluster_size=2)
        assert result["n_clusters_total"] == 2
        assert len(result["top_sites"]) == 2
        idx_a = set(result["top_sites"][0]["member_indices"])
        idx_b = set(result["top_sites"][1]["member_indices"])
        assert idx_a.isdisjoint(idx_b)

    def test_single_tight_blob_produces_one_site(self):
        coords = _blob([0, 0, 0], 10, spread=1.0, seed=3)
        scores = np.arange(10, dtype=float)
        result = cluster_sites(coords, scores, m=10, min_cluster_size=2)
        assert result["n_clusters_total"] == 1
        assert len(result["top_sites"]) == 1
        assert set(result["top_sites"][0]["member_indices"]) == set(range(10))

    def test_min_cluster_size_drops_singletons(self):
        # One tight 4-member blob, one isolated point 200 A away.
        coords = np.vstack([_blob([0, 0, 0], 4, seed=4), [[200.0, 0.0, 0.0]]])
        scores = np.array([1.0, 1.0, 1.0, 1.0, 9.0])  # isolated point scores highest
        result = cluster_sites(coords, scores, m=5, min_cluster_size=2)
        # isolated point forms its own 1-member cluster, dropped by the filter
        assert result["n_dropped_small"] == 1
        assert len(result["top_sites"]) == 1
        assert set(result["top_sites"][0]["member_indices"]) == {0, 1, 2, 3}

    def test_ranking_key_is_mean_not_max(self):
        # Cluster A: one outlier-high score (9.0) among low scores -- high
        # max, low mean. Cluster B: uniformly moderate scores -- lower
        # max, higher mean. Per this task's own "mean-primary" invariant,
        # B must outrank A.
        coords = np.vstack([_blob([0, 0, 0], 4, seed=5), _blob([200, 0, 0], 4, seed=6)])
        scores = np.array([9.0, 0.1, 0.1, 0.1, 3.0, 3.0, 3.0, 3.0])
        result = cluster_sites(coords, scores, m=8, min_cluster_size=2)
        assert len(result["top_sites"]) == 2
        top = result["top_sites"][0]
        assert top["mean_score"] == pytest.approx(3.0)
        assert top["max_score"] == pytest.approx(3.0)
        assert result["top_sites"][1]["max_score"] == pytest.approx(9.0)

    def test_top_n_truncates(self):
        # 3 well-separated blobs, ask for only the top 2 sites.
        coords = np.vstack([
            _blob([0, 0, 0], 3, seed=7), _blob([200, 0, 0], 3, seed=8), _blob([400, 0, 0], 3, seed=9),
        ])
        scores = np.array([1.0] * 3 + [2.0] * 3 + [3.0] * 3)
        result = cluster_sites(coords, scores, m=9, min_cluster_size=2, top_n=2)
        assert len(result["top_sites"]) == 2
        assert len(result["all_sites"]) == 3

    def test_m_frac_default_selects_expected_fraction(self):
        coords = _blob([0, 0, 0], 40, spread=50.0, seed=10)
        scores = np.arange(40, dtype=float)
        result = cluster_sites(coords, scores)  # default m_frac=0.125
        assert result["m"] == round(0.125 * 40)

    def test_resnums_carried_through(self):
        coords = _blob([0, 0, 0], 5, seed=11)
        scores = np.arange(5, dtype=float)
        resnums = np.array([101, 102, 103, 104, 105])
        result = cluster_sites(coords, scores, m=5, min_cluster_size=2, resnums=resnums)
        assert result["top_sites"][0]["member_resnums"] is not None
        assert set(result["top_sites"][0]["member_resnums"]) <= set(resnums.tolist())

    def test_dbscan_method_also_separates_blobs(self):
        coords = np.vstack([_blob([0, 0, 0], 5, seed=12), _blob([200, 0, 0], 5, seed=13)])
        scores = np.ones(10)
        result = cluster_sites(coords, scores, m=10, min_cluster_size=2, method="dbscan")
        assert result["n_clusters_total"] == 2

    def test_unknown_method_raises(self):
        coords = _blob([0, 0, 0], 4, seed=14)
        with pytest.raises(ValueError):
            cluster_sites(coords, np.arange(4.0), m=4, method="bogus")


class TestSiteHitMetrics:
    def _sites(self):
        return [
            {"rank": 1, "member_indices": [0, 1], "centroid": [0.0, 0.0, 0.0]},
            {"rank": 2, "member_indices": [2, 3], "centroid": [10.0, 0.0, 0.0]},
        ]

    def test_overlap_thresholds(self):
        coords = np.array([[0, 0, 0], [1, 0, 0], [10, 0, 0], [11, 0, 0]], dtype=float)
        pocket_mask = np.array([True, True, False, False])  # both members of site 1 in pocket
        out = site_hit_metrics(self._sites(), pocket_mask, coords, overlap_thresholds=(1, 3))
        assert out["per_site"][0]["overlap"] == 2
        assert out["per_site"][0]["hit_at_1"] is True
        assert out["per_site"][0]["hit_at_3"] is False
        assert out["per_site"][1]["overlap"] == 0
        assert out["n_hit_at_1"] == 1
        assert out["n_hit_at_3"] == 0

    def test_centroid_distance_nan_when_pocket_empty(self):
        coords = np.array([[0, 0, 0], [1, 0, 0], [10, 0, 0], [11, 0, 0]], dtype=float)
        pocket_mask = np.zeros(4, dtype=bool)
        out = site_hit_metrics(self._sites(), pocket_mask, coords)
        assert np.isnan(out["per_site"][0]["centroid_distance"])
        assert np.isnan(out["mean_centroid_distance"])


class TestSiteChanceLevel:
    def test_hit_rate_in_unit_interval_and_deterministic(self):
        coords = _blob([0, 0, 0], 30, spread=20.0, seed=15)
        pocket_mask = np.zeros(30, dtype=bool)
        pocket_mask[:3] = True
        rng1 = np.random.default_rng(0)
        rng2 = np.random.default_rng(0)
        out1 = site_chance_level(coords, 30, pocket_mask, n_null=20, rng=rng1)
        out2 = site_chance_level(coords, 30, pocket_mask, n_null=20, rng=rng2)
        assert 0.0 <= out1["hit_rate_at_1"] <= 1.0
        assert out1 == out2  # deterministic under a seeded rng (TASK-0180 Constraint)


class TestSiteProximityFloorDegenerateCase:
    def test_pure_distance_to_seed_yields_one_site_near_seed(self):
        """The direct regression for the defect this task fixes: on a
        smooth, monotonically-decreasing-with-distance score field
        (exactly what `main`'s undeduplicated top-5 produced 5 fragments
        of), site clustering must collapse to exactly one site near the
        seed, not five."""
        n = 60
        coords = _helix_coords(n)
        source = [0]  # seed at residue 0
        pocket_mask = np.zeros(n, dtype=bool)  # not exercised by this assertion
        out = site_proximity_floor(coords, source, pocket_mask)
        sites = out["sites"]["top_sites"]
        assert len(sites) == 1
        # the single site must actually be near the seed (small residue
        # indices, given the helix's rise-with-index geometry), not an
        # arbitrary contiguous stretch elsewhere.
        assert min(sites[0]["member_indices"]) <= 2


class TestSiteKnobSweep:
    def test_grid_size_and_stability_shape(self):
        n = 60
        coords = _helix_coords(n)
        scores = -np.arange(n, dtype=float)  # smooth, seed-proximal field
        pocket_mask = np.zeros(n, dtype=bool)
        out = site_knob_sweep(
            coords, scores, pocket_mask,
            m_fracs=(0.1, 0.15), linkage_cutoffs=(2.0, 8.0), min_cluster_sizes=(2,),
        )
        assert out["n_combos"] == 2 * 2 * 1
        assert out["verdict"] in ("STABLE", "UNSTABLE")
        assert len(out["grid"]) == out["n_combos"]
        for combo in out["grid"]:
            assert combo["n_sites"] >= 0

    def test_smooth_field_is_stable_once_cutoff_exceeds_ca_spacing(self):
        # A single dominant, spatially smooth peak keeps the same top
        # site across knob combos once linkage_cutoff clears this helix's
        # own consecutive-C-alpha spacing (~3.8 A, from rise=1.5 A +
        # radius=2.3 A/100 degree twist) -- STABLE for cutoffs (5.0, 7.5,
        # 8.0, 10.0).
        n = 80
        coords = _helix_coords(n)
        scores = -np.abs(np.arange(n) - 10.0)  # single sharp peak at residue 10
        pocket_mask = np.zeros(n, dtype=bool)
        out = site_knob_sweep(
            coords, scores, pocket_mask,
            linkage_cutoffs=(5.0, 7.5, 8.0, 10.0),
        )
        assert out["verdict"] == "STABLE"

    def test_low_cutoffs_below_ca_spacing_fragment_a_smooth_peak(self):
        # This is the empirical check the plan calls for: TASK-0067 never
        # derived a clustering cutoff, only a contact-graph one. Below
        # this helix's own ~3.8 A consecutive-C-alpha spacing, single-
        # linkage cannot chain even physically adjacent residues, so a
        # smooth single-peak field fragments into clusters too small to
        # survive `min_cluster_size` -- a real, informative, easily-
        # dismissed-as-"too small a scale" result, not a bug.
        n = 80
        coords = _helix_coords(n)
        scores = -np.abs(np.arange(n) - 10.0)
        pocket_mask = np.zeros(n, dtype=bool)
        low = site_knob_sweep(
            coords, scores, pocket_mask,
            m_fracs=(0.125,), linkage_cutoffs=(1.5, 2.0), min_cluster_sizes=(2,),
        )
        high = site_knob_sweep(
            coords, scores, pocket_mask,
            m_fracs=(0.125,), linkage_cutoffs=(8.0,), min_cluster_sizes=(2,),
        )
        low_n_sites = [combo["n_sites"] for combo in low["grid"]]
        high_n_sites = [combo["n_sites"] for combo in high["grid"]]
        assert all(n_sites == 0 for n_sites in low_n_sites)
        assert all(n_sites >= 1 for n_sites in high_n_sites)


class TestNonDegeneracy:
    def test_top_5_sites_mutually_nonoverlapping_and_pairwise_far_apart(self):
        # 5 blobs, each 200 A apart pairwise, well beyond the 8.0 A
        # linkage cutoff -- per this task's own Planned Validation, the
        # top-5 sites on a real target must be mutually non-overlapping
        # and pairwise >= the linkage cutoff apart.
        centers = [[0, 0, 0], [200, 0, 0], [400, 0, 0], [0, 200, 0], [0, 400, 0]]
        coords = np.vstack([_blob(c, 4, spread=1.0, seed=100 + i) for i, c in enumerate(centers)])
        scores = np.tile([4.0, 3.0, 2.0, 1.0], 5) + np.repeat(np.arange(5, 0, -1), 4)
        result = cluster_sites(coords, scores, m=len(coords), min_cluster_size=2, top_n=5)
        sites = result["top_sites"]
        assert len(sites) == 5

        member_sets = [set(s["member_indices"]) for s in sites]
        for i in range(len(member_sets)):
            for j in range(i + 1, len(member_sets)):
                assert member_sets[i].isdisjoint(member_sets[j])

        centroids = [np.asarray(s["centroid"]) for s in sites]
        for i in range(len(centroids)):
            for j in range(i + 1, len(centroids)):
                assert np.linalg.norm(centroids[i] - centroids[j]) >= DEFAULT_LINKAGE_CUTOFF
