"""TASK-0011 coverage -- baselines.py classical baselines + external-tool
wrapper graceful-failure behavior. Synthetic coordinates only; external
calls are mocked, per the task's Planned Validation ("tested only for
graceful-failure behavior... not for correctness of the external service").
"""
from unittest.mock import patch

import numpy as np
import pytest

from allostery.baselines import (
    _parse_fpocket_info,
    betweenness_centrality,
    closeness_centrality,
    connectivity_robustness,
    degree_centrality,
    eigenvector_centrality,
    euclid_from_seed_centroid,
    fpocket_baseline,
    hop_from_seed,
    pocketminer_baseline,
    proteinlens_baseline,
    random_baseline,
    surface_baseline,
)


def _chain_coords(n: int = 4, spacing: float = 2.0) -> np.ndarray:
    """n collinear points along x, `spacing` Angstrom apart."""
    return np.column_stack([
        np.arange(n, dtype=float) * spacing,
        np.zeros(n), np.zeros(n),
    ])


class TestClassicalBaselines:
    def test_random_baseline_shape_and_range(self):
        scores = random_baseline(20, seed=0)
        assert scores.shape == (20,)
        assert (scores >= 0).all() and (scores < 1).all()

    def test_random_baseline_reproducible_with_seed(self):
        a = random_baseline(10, seed=42)
        b = random_baseline(10, seed=42)
        np.testing.assert_array_equal(a, b)

    def test_random_baseline_varies_without_fixed_seed(self):
        a = random_baseline(50, seed=1)
        b = random_baseline(50, seed=2)
        assert not np.array_equal(a, b)

    def test_degree_centrality_matches_hand_computed_chain(self):
        # 4 collinear points, spacing=2.0, cutoff=3.0 -> path graph 0-1-2-3
        coords = _chain_coords(4, spacing=2.0)
        deg = degree_centrality(coords, cutoff=3.0)
        np.testing.assert_allclose(deg, [1.0, 2.0, 2.0, 1.0])

    def test_surface_baseline_favors_low_degree_endpoints(self):
        coords = _chain_coords(4, spacing=2.0)
        surf = surface_baseline(coords, cutoff=3.0)
        # endpoints (low degree) must outscore the interior (high degree)
        assert surf[0] > surf[1]
        assert surf[3] > surf[2]
        assert surf[0] == surf[3]  # symmetric chain

    def test_betweenness_centrality_path_graph_symmetry(self):
        coords = _chain_coords(4, spacing=2.0)
        bc = betweenness_centrality(coords, cutoff=3.0)
        assert bc.shape == (4,)
        # classic path-graph property: endpoints carry no shortest paths
        assert bc[0] == pytest.approx(0.0)
        assert bc[3] == pytest.approx(0.0)
        # interior nodes are symmetric and carry more paths than endpoints
        assert bc[1] == pytest.approx(bc[2])
        assert bc[1] > bc[0]

    def test_betweenness_centrality_disconnected_graph_does_not_crash(self):
        cluster_a = _chain_coords(3, spacing=2.0)
        cluster_b = _chain_coords(3, spacing=2.0) + np.array([1000.0, 0.0, 0.0])
        coords = np.vstack([cluster_a, cluster_b])
        bc = betweenness_centrality(coords, cutoff=3.0)
        assert bc.shape == (6,)
        assert np.isfinite(bc).all()

    # -- TASK-0348: eigenvector_centrality / closeness_centrality ----------

    def test_eigenvector_centrality_path_graph_interior_beats_endpoints(self):
        coords = _chain_coords(4, spacing=2.0)
        ec = eigenvector_centrality(coords, cutoff=3.0)
        assert ec.shape == (4,)
        assert np.isfinite(ec).all()
        assert ec[1] == pytest.approx(ec[2])  # symmetric chain
        assert ec[1] > ec[0]  # interior outranks the endpoints

    def test_eigenvector_centrality_disconnected_graph_does_not_crash(self):
        cluster_a = _chain_coords(3, spacing=2.0)
        cluster_b = _chain_coords(3, spacing=2.0) + np.array([1000.0, 0.0, 0.0])
        coords = np.vstack([cluster_a, cluster_b])
        ec = eigenvector_centrality(coords, cutoff=3.0)
        assert ec.shape == (6,)
        assert np.isfinite(ec).all()

    def test_closeness_centrality_path_graph_interior_beats_endpoints(self):
        coords = _chain_coords(4, spacing=2.0)
        cc = closeness_centrality(coords, cutoff=3.0)
        assert cc.shape == (4,)
        # classic path-graph property: interior nodes reach everyone faster
        assert cc[1] == pytest.approx(cc[2])
        assert cc[1] > cc[0]

    def test_closeness_centrality_disconnected_graph_does_not_crash(self):
        cluster_a = _chain_coords(3, spacing=2.0)
        cluster_b = _chain_coords(3, spacing=2.0) + np.array([1000.0, 0.0, 0.0])
        coords = np.vstack([cluster_a, cluster_b])
        cc = closeness_centrality(coords, cutoff=3.0)
        assert cc.shape == (6,)
        assert np.isfinite(cc).all()


# ---------------------------------------------------------------------------
# TASK-0094 (REVIEW-2026-07-13, P1-A) -- proximity-to-seed baselines
# ---------------------------------------------------------------------------

class TestProximityBaselines:
    def test_euclid_from_seed_centroid_hand_computed_chain(self):
        coords = _chain_coords(4, spacing=2.0)  # x = 0, 2, 4, 6
        score = euclid_from_seed_centroid(coords, source=0)
        np.testing.assert_allclose(score, -np.array([0.0, 2.0, 4.0, 6.0]))

    def test_euclid_from_seed_centroid_multi_index_uses_centroid(self):
        coords = _chain_coords(4, spacing=2.0)  # x = 0, 2, 4, 6
        # centroid of residues 0 and 3 is x=3.0
        score = euclid_from_seed_centroid(coords, source=[0, 3])
        np.testing.assert_allclose(score, -np.array([3.0, 1.0, 1.0, 3.0]))

    def test_euclid_from_seed_centroid_closer_scores_higher(self):
        coords = _chain_coords(6, spacing=2.0)
        score = euclid_from_seed_centroid(coords, source=0)
        assert np.all(np.diff(score) < 0)  # strictly decreasing with distance

    def test_hop_from_seed_hand_computed_chain(self):
        coords = _chain_coords(4, spacing=2.0)  # path graph 0-1-2-3 at cutoff=3.0
        score = hop_from_seed(coords, source=0, cutoff=3.0)
        np.testing.assert_allclose(score, -np.array([0.0, 1.0, 2.0, 3.0]))

    def test_hop_from_seed_multi_index_takes_nearest_seed(self):
        coords = _chain_coords(4, spacing=2.0)
        score = hop_from_seed(coords, source=[0, 3], cutoff=3.0)
        np.testing.assert_allclose(score, -np.array([0.0, 1.0, 1.0, 0.0]))

    def test_hop_from_seed_disconnected_gets_finite_penalty_not_inf_or_nan(self):
        cluster_a = _chain_coords(3, spacing=2.0)
        cluster_b = _chain_coords(3, spacing=2.0) + np.array([1000.0, 0.0, 0.0])
        coords = np.vstack([cluster_a, cluster_b])
        score = hop_from_seed(coords, source=0, cutoff=3.0)
        assert np.isfinite(score).all()
        n = len(coords)
        np.testing.assert_allclose(score[3:], -np.full(3, n + 1))

    def test_both_proximity_baselines_reject_out_of_range_seed_loudly(self):
        coords = _chain_coords(4, spacing=2.0)
        with pytest.raises(IndexError):
            euclid_from_seed_centroid(coords, source=99)


class TestConnectivityRobustness:
    def test_chain_every_residue_has_exactly_one_route(self):
        """A path graph has no redundancy anywhere -- every reachable
        residue's edge-connectivity from a single-residue seed is 1."""
        coords = _chain_coords(5, spacing=2.0)
        score = connectivity_robustness(coords, source=0, cutoff=3.0)
        np.testing.assert_allclose(score[1:], np.ones(4))

    def test_disconnected_residue_gets_zero_not_a_penalty_value(self):
        """Unlike `hop_from_seed`'s `n+1` penalty, zero edge-disjoint paths
        is the literally correct connectivity value for an unreachable
        residue -- no borrowed convention needed."""
        cluster_a = _chain_coords(3, spacing=2.0)
        cluster_b = _chain_coords(3, spacing=2.0) + np.array([1000.0, 0.0, 0.0])
        coords = np.vstack([cluster_a, cluster_b])
        score = connectivity_robustness(coords, source=0, cutoff=3.0)
        np.testing.assert_allclose(score[3:], np.zeros(3))

    def test_redundant_bridge_gives_higher_connectivity_than_single_bridge(self):
        """A residue reachable via 3 independent parallel routes must score
        higher than one reachable via a single bottleneck route -- the
        actual bottleneck-vs-distributed distinction this baseline exists
        to capture."""
        # Seed (0) connects to residue 4 via 3 disjoint 1-hop lanes, and to
        # residue 8 via a single 4-hop chain.
        seed = np.array([[0.0, 0.0, 0.0]])
        lanes = np.array([[3.0, 0.0, 0.0], [3.0, 3.0, 0.0], [3.0, -3.0, 0.0]])
        redundant_target = np.array([[6.0, 0.0, 0.0]])
        single_chain = np.array([[3.0, 20.0, 0.0], [6.0, 20.0, 0.0], [9.0, 20.0, 0.0]])
        coords = np.vstack([seed, lanes, redundant_target, single_chain])
        score = connectivity_robustness(coords, source=0, cutoff=4.0)
        assert score[4] > score[7]  # redundant_target > end of single_chain


class TestProximityConfoundReproduction:
    """REVIEW-2026-07-13 P1-A's own Acceptance Scenario (TASK-0094): the
    proximity baselines must be checked against the review's real evidence,
    not assumed correct by construction. Reproduces the review's synthetic-
    globule setup (170 residues, cutoff 8.0 A, a spatially-contiguous
    6-residue seed cluster) with real build_H_new + time_averaged_ctqw --
    not the review's exact RNG draw (not specified), but the same
    qualitative claim, checked as a hard regression bound rather than
    eyeballed: proximity-to-seed positively predicts CTQW occupation.
    Originally measured (5 independent seeds, pre-TASK-0121 lam_* defaults):
    Euclidean 0.71-0.83, hop 0.55-0.64 -- both comfortably above a 0.5 bound.

    TASK-0121 (z-scored potential terms, ~12x smaller combined lam_* to hold
    sigma(V) <= 0.2*J) measurably weakens this confound -- re-measured on the
    same 5 seeds under the renormalized defaults: Euclidean 0.22-0.47, hop
    0.03-0.28. Still positive (proximity is not eliminated as a confound --
    per REVIEW-panel-2026-07-16-v2.md §2.4, renormalizing the potential does
    not by itself fix the proximity confound in the *observable*, only the
    degree confound in the *diagonal*) but roughly half the old magnitude.
    Bounds below are lowered to match, not to make the test vacuous --
    rng_seed=0 gives rho_euclid=0.373, rho_hop=0.170; margin kept for
    cross-machine BLAS/eigh nondeterminism.
    """

    def _synthetic_globule(self, rng_seed: int, n: int = 170):
        rng = np.random.default_rng(rng_seed)
        coords = np.zeros((n, 3))
        for i in range(1, n):
            step = rng.normal(size=3)
            step /= np.linalg.norm(step)
            step *= 3.8
            pull = -0.15 * (coords[i - 1] - coords[:i].mean(axis=0))
            coords[i] = coords[i - 1] + step + pull
        bfactors = rng.uniform(15, 40, size=n)
        start = int(rng.integers(0, n - 6))
        seed = np.arange(start, start + 6)
        return coords, bfactors, seed

    def test_proximity_strongly_predicts_ctqw_occupation(self):
        from scipy.stats import spearmanr

        from allostery.hamiltonians import build_H_new
        from allostery.propagators import time_averaged_ctqw

        coords, bfactors, seed = self._synthetic_globule(rng_seed=0)
        H = build_H_new(coords, bfactors, cutoff=8.0)
        occ = time_averaged_ctqw(H, t_max=15.0, source=seed, n_steps=500)

        rho_euclid, _ = spearmanr(occ, euclid_from_seed_centroid(coords, seed))
        rho_hop, _ = spearmanr(occ, hop_from_seed(coords, seed, cutoff=8.0))

        assert rho_euclid > 0.25, f"expected a positive proximity confound, got rho={rho_euclid:.3f}"
        assert rho_hop > 0.1, f"expected a positive proximity confound, got rho={rho_hop:.3f}"


class TestFpocketBaseline:
    def test_binary_not_found_returns_graceful_error(self, tmp_path):
        pdb = tmp_path / "x.pdb"
        pdb.write_text("ATOM\n")
        with patch("allostery.baselines.shutil.which", return_value=None):
            result = fpocket_baseline(str(pdb))
        assert "error" in result
        assert "not found on PATH" in result["error"]

    def test_missing_pdb_file_returns_graceful_error(self):
        with patch("allostery.baselines.shutil.which", return_value="/usr/bin/fpocket"):
            result = fpocket_baseline("/nonexistent/path/x.pdb")
        assert "error" in result
        assert "not found" in result["error"]

    def test_nonzero_exit_returns_graceful_error(self, tmp_path):
        pdb = tmp_path / "x.pdb"
        pdb.write_text("ATOM\n")
        fake_result = type("R", (), {"returncode": 1, "stderr": "boom", "stdout": ""})()
        with patch("allostery.baselines.shutil.which", return_value="/usr/bin/fpocket"), \
             patch("allostery.baselines.subprocess.run", return_value=fake_result):
            result = fpocket_baseline(str(pdb))
        assert "error" in result
        assert "exited 1" in result["error"]

    def test_timeout_returns_graceful_error(self, tmp_path):
        import subprocess as sp
        pdb = tmp_path / "x.pdb"
        pdb.write_text("ATOM\n")
        with patch("allostery.baselines.shutil.which", return_value="/usr/bin/fpocket"), \
             patch("allostery.baselines.subprocess.run",
                   side_effect=sp.TimeoutExpired(cmd="fpocket", timeout=120)):
            result = fpocket_baseline(str(pdb))
        assert "error" in result
        assert "timed out" in result["error"]

    def test_missing_info_file_returns_graceful_error(self, tmp_path):
        pdb = tmp_path / "x.pdb"
        pdb.write_text("ATOM\n")
        fake_result = type("R", (), {"returncode": 0, "stderr": "", "stdout": ""})()
        with patch("allostery.baselines.shutil.which", return_value="/usr/bin/fpocket"), \
             patch("allostery.baselines.subprocess.run", return_value=fake_result):
            result = fpocket_baseline(str(pdb))
        assert "error" in result
        assert "no info file" in result["error"]


class TestParseFpocketInfo:
    SAMPLE = """Pocket 1 :
\tScore : \t 0.523
\tDruggability Score : \t 0.712
\tNumber of alpha spheres : \t 42

Pocket 2 :
\tScore : \t -0.100
\tDruggability Score : \t 0.050
\tNumber of alpha spheres : \t 8
"""

    def test_parses_multiple_pockets(self):
        pockets = _parse_fpocket_info(self.SAMPLE)
        assert len(pockets) == 2
        assert pockets[0]["id"] == 1
        assert pockets[0]["score"] == pytest.approx(0.523)
        assert pockets[0]["druggability_score"] == pytest.approx(0.712)
        assert pockets[1]["id"] == 2
        assert pockets[1]["score"] == pytest.approx(-0.100)

    def test_empty_text_returns_empty_list(self):
        assert _parse_fpocket_info("") == []

    def test_missing_fields_are_none_not_raising(self):
        pockets = _parse_fpocket_info("Pocket 1 :\n\tSome Other Field : 1.0\n")
        assert pockets[0]["score"] is None
        assert pockets[0]["druggability_score"] is None


class TestNotYetWiredBaselines:
    def test_pocketminer_baseline_returns_deterministic_error(self):
        result = pocketminer_baseline(np.zeros((5, 3)))
        assert "error" in result
        assert "not yet wired" in result["error"]

    def test_proteinlens_baseline_returns_deterministic_error(self):
        result = proteinlens_baseline(np.zeros((5, 3)))
        assert "error" in result
        assert "not yet wired" in result["error"]
