"""TASK-0012 coverage -- current-flow edge propensity and pathway
extraction, validated on synthetic graphs with a known bottleneck
structure (not real proteins -- this module has no notebook precedent and
no leakage surface of its own, see pathways.py's module docstring).

TestInvariance (TASK-0057) is this module's GAUGE half of INV-0002 (see
.ai/invariants/INV-0002-pathways-edge-propensity.md) -- SE(3) and
permutation invariance of edge_propensity/extract_pathway, run for real
per the Invariance Protocol's own rule that agreement-in-prose is not
verification."""
import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.pathways import edge_propensity, edge_propensity_to_matrix, extract_pathway  # noqa: E402
from allostery.hamiltonians import H2_combinatorial_laplacian  # noqa: E402


def _two_cluster_laplacian() -> np.ndarray:
    """Two 4-node cliques {0,1,2,3} and {4,5,6,7}, joined only by a single
    bridge edge (3, 4). Any current leaving cluster A's source must cross
    that one edge to reach cluster B."""
    N = 8
    W = np.zeros((N, N))
    for cluster in ([0, 1, 2, 3], [4, 5, 6, 7]):
        for i in cluster:
            for j in cluster:
                if i < j:
                    W[i, j] = W[j, i] = 1.0
    W[3, 4] = W[4, 3] = 1.0
    D = np.diag(W.sum(axis=1))
    return D - W


def _disconnected_pair_laplacian() -> np.ndarray:
    """A 0-1-2 path plus an isolated node 3 -- no route from 0 to 3."""
    N = 4
    W = np.zeros((N, N))
    W[0, 1] = W[1, 0] = 1.0
    W[1, 2] = W[2, 1] = 1.0
    D = np.diag(W.sum(axis=1))
    return D - W


# ---------------------------------------------------------------------------
# edge_propensity
# ---------------------------------------------------------------------------

class TestEdgePropensity:
    def test_bridge_edge_ranks_highest(self):
        L = _two_cluster_laplacian()
        prop = edge_propensity(L, source=0)
        bridge = prop[(3, 4)]
        assert bridge == max(prop.values())

    def test_symmetric_clique_edges_within_source_cluster_are_lower(self):
        L = _two_cluster_laplacian()
        prop = edge_propensity(L, source=0)
        assert prop[(3, 4)] > prop[(0, 1)]
        assert prop[(3, 4)] > prop[(0, 2)]

    def test_all_values_non_negative(self):
        L = _two_cluster_laplacian()
        prop = edge_propensity(L, source=0)
        assert all(v >= 0.0 for v in prop.values())

    def test_multi_index_source_does_not_crash_and_bridge_still_dominates(self):
        L = _two_cluster_laplacian()
        prop = edge_propensity(L, source=[0, 1])
        assert prop[(3, 4)] == max(prop.values())

    def test_edge_count_matches_graph(self):
        L = _two_cluster_laplacian()
        prop = edge_propensity(L, source=0)
        # 2 cliques x 6 edges each + 1 bridge = 13 edges
        assert len(prop) == 13


# ---------------------------------------------------------------------------
# extract_pathway
# ---------------------------------------------------------------------------

class TestExtractPathway:
    def test_traces_direct_route_through_bridge(self):
        L = _two_cluster_laplacian()
        result = extract_pathway(L, source=0, target=7)
        assert result["reached_target"] is True
        assert result["nodes"][0] == 0
        assert result["nodes"][-1] == 7
        assert (3, 4) in result["edges"]

    def test_propensity_field_has_same_shape_as_edge_propensity(self):
        L = _two_cluster_laplacian()
        result = extract_pathway(L, source=0, target=7)
        prop_only = edge_propensity(L, source=0)
        assert set(result["propensity"]) == set(prop_only)

    def test_unreachable_target_reports_reached_false(self):
        L = _disconnected_pair_laplacian()
        result = extract_pathway(L, source=0, target=3)
        assert result["reached_target"] is False
        assert 3 not in result["nodes"]

    def test_target_equal_to_source_raises(self):
        L = _two_cluster_laplacian()
        with pytest.raises(ValueError):
            extract_pathway(L, source=0, target=0)

    def test_target_within_multi_index_source_raises(self):
        L = _two_cluster_laplacian()
        with pytest.raises(ValueError):
            extract_pathway(L, source=[0, 7], target=7)


# ---------------------------------------------------------------------------
# TestInvariance -- INV-0002's GAUGE rows (TASK-0057)
# ---------------------------------------------------------------------------

def _helix_coords(n: int) -> np.ndarray:
    theta = np.arange(n) * (100.0 * np.pi / 180.0)
    return np.column_stack([
        2.3 * np.cos(theta),
        2.3 * np.sin(theta),
        1.5 * np.arange(n, dtype=float),
    ])


def _rigid_motion(coords: np.ndarray, theta_z: float, theta_x: float, t: np.ndarray) -> np.ndarray:
    """Apply a fixed rotation (about z then x) plus a translation."""
    cz, sz = np.cos(theta_z), np.sin(theta_z)
    cx, sx = np.cos(theta_x), np.sin(theta_x)
    Rz = np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]])
    Rx = np.array([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]])
    R = Rz @ Rx
    return coords @ R.T + t


def _permute_laplacian(L: np.ndarray, perm: np.ndarray) -> np.ndarray:
    """Relabel nodes: new index perm[i] holds old node i's data."""
    N = L.shape[0]
    P = np.zeros((N, N))
    P[perm, np.arange(N)] = 1.0
    return P @ L @ P.T


class TestInvariance:
    """GAUGE: neither function takes coordinates directly, so SE(3)
    invariance holds by construction whenever the H fed in is itself
    SE(3)-invariant (true of hamiltonians.py's distance-based contact
    graphs) -- verified compositionally here, not just asserted. Same
    empirical standard for permutation invariance (H' = P H P^T)."""

    def test_se3_invariance_composed_with_hamiltonians(self):
        coords = _helix_coords(12)
        H = H2_combinatorial_laplacian(coords, cutoff=10.0)
        prop = edge_propensity(H, source=0)

        moved = _rigid_motion(coords, theta_z=0.7, theta_x=1.1, t=np.array([5.0, -3.0, 2.0]))
        H_moved = H2_combinatorial_laplacian(moved, cutoff=10.0)
        prop_moved = edge_propensity(H_moved, source=0)

        assert set(prop) == set(prop_moved)
        for edge, value in prop.items():
            assert prop_moved[edge] == pytest.approx(value, abs=1e-9)

    def test_permutation_invariance_edge_propensity(self):
        L = _two_cluster_laplacian()
        prop = edge_propensity(L, source=0)

        perm = np.random.default_rng(11).permutation(8)
        L_perm = _permute_laplacian(L, perm)
        prop_perm = edge_propensity(L_perm, source=int(perm[0]))

        for (i, j), value in prop.items():
            i2, j2 = int(perm[i]), int(perm[j])
            key = (min(i2, j2), max(i2, j2))
            assert prop_perm[key] == pytest.approx(value, abs=1e-9)

    def test_permutation_invariance_extract_pathway(self):
        """Caveat (recorded in INV-0002, not swept under the rug): the
        greedy walk's tie-break is node-index order, which is not
        permutation-invariant if two candidate steps tie exactly -- this
        graph/permutation pair has no such tie (checked before writing
        this assertion), so this confirms the common case, not the
        tie-break edge case."""
        L = _two_cluster_laplacian()
        result = extract_pathway(L, source=0, target=7)

        perm = np.random.default_rng(11).permutation(8)
        L_perm = _permute_laplacian(L, perm)
        result_perm = extract_pathway(L_perm, source=int(perm[0]), target=int(perm[7]))

        expected_nodes = [int(perm[n]) for n in result["nodes"]]
        assert result_perm["nodes"] == expected_nodes
        assert result_perm["reached_target"] == result["reached_target"]


# ---------------------------------------------------------------------------
# edge_propensity_to_matrix (TASK-0079.002)
# ---------------------------------------------------------------------------

class TestEdgePropensityToMatrix:
    def test_symmetric_with_zero_diagonal_and_correct_values(self):
        L = _two_cluster_laplacian()
        prop = edge_propensity(L, source=0)
        M = edge_propensity_to_matrix(prop, n=8)

        assert M.shape == (8, 8)
        np.testing.assert_allclose(M, M.T)
        assert np.all(np.diag(M) == 0.0)
        for (i, j), value in prop.items():
            assert M[i, j] == value
            assert M[j, i] == value

    def test_absent_edges_are_zero_not_nan(self):
        M = edge_propensity_to_matrix({(0, 1): 0.5}, n=4)
        assert M[2, 3] == 0.0
        assert not np.isnan(M).any()

    def test_i_greater_equal_j_raises(self):
        with pytest.raises(ValueError):
            edge_propensity_to_matrix({(1, 0): 0.5}, n=4)
        with pytest.raises(ValueError):
            edge_propensity_to_matrix({(2, 2): 0.5}, n=4)

    def test_out_of_range_index_raises(self):
        with pytest.raises(ValueError):
            edge_propensity_to_matrix({(0, 10): 0.5}, n=4)

    def test_negative_value_raises(self):
        with pytest.raises(ValueError):
            edge_propensity_to_matrix({(0, 1): -0.1}, n=4)

    def test_non_tuple_key_raises(self):
        with pytest.raises(TypeError):
            edge_propensity_to_matrix({"01": 0.5}, n=4)

    def test_empty_propensity_gives_all_zero_matrix(self):
        M = edge_propensity_to_matrix({}, n=5)
        assert M.shape == (5, 5)
        assert np.all(M == 0.0)
