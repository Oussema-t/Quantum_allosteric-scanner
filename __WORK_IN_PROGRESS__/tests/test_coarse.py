"""TASK-0013 coverage -- coarse_grain (Louvain/spectral) and trotter_cost.

Includes GAUGE invariance tests per the Invariance Protocol
(.ai/reference/INVARIANCE_PROTOCOL.md, TASK-0051): residue-relabeling
(graph permutation) must not change the *partition* (as a set of node
sets) or trotter_cost's scalar outputs. SE(3) invariance is not tested
separately -- both functions take only H (no coordinates), so they are
invariant by construction whenever H itself is (same reasoning as
pathways.py's INV-0002, first row) -- see INV-0003 for the registered
classification.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.coarse import (  # noqa: E402
    CoarseGrainResult,
    TrotterCostResult,
    coarse_grain,
    trotter_cost,
)


def _two_community_graph(n1=10, n2=10, intra=0.9, bridge=0.05, seed=0):
    """A symmetric weighted graph with two obvious dense communities and
    one weak bridge edge -- Planned Validation's own fixture shape."""
    rng = np.random.default_rng(seed)
    N = n1 + n2
    W = np.zeros((N, N))
    for block, lo, hi in ((slice(0, n1), 0, n1), (slice(n1, N), n1, N)):
        vals = rng.uniform(intra - 0.1, intra, size=(hi - lo, hi - lo))
        vals = (vals + vals.T) / 2.0
        np.fill_diagonal(vals, 0.0)
        W[lo:hi, lo:hi] = vals
    W[n1 - 1, n1] = W[n1, n1 - 1] = bridge
    return W


def _partition_sets(labels) -> set:
    d: dict = {}
    for i, c in enumerate(np.asarray(labels).tolist()):
        d.setdefault(c, set()).add(i)
    return {frozenset(s) for s in d.values()}


# ---------------------------------------------------------------------------
# coarse_grain -- Planned Validation: two obvious communities recovered
# ---------------------------------------------------------------------------

class TestCoarseGrainCommunityRecovery:
    def test_louvain_recovers_two_communities(self):
        W = _two_community_graph()
        result = coarse_grain(W, method="louvain", n_target=12)
        assert isinstance(result, CoarseGrainResult)
        partitions = _partition_sets(result.labels)
        assert frozenset(range(10)) in partitions
        assert frozenset(range(10, 20)) in partitions

    def test_spectral_recovers_two_communities(self):
        W = _two_community_graph()
        result = coarse_grain(W, method="spectral", n_target=2)
        partitions = _partition_sets(result.labels)
        assert frozenset(range(10)) in partitions
        assert frozenset(range(10, 20)) in partitions

    def test_h_coarse_shape_and_symmetry(self):
        W = _two_community_graph()
        result = coarse_grain(W, method="spectral", n_target=2)
        assert result.H_coarse.shape == (result.n_clusters, result.n_clusters)
        np.testing.assert_allclose(result.H_coarse, result.H_coarse.T)
        assert np.all(np.diag(result.H_coarse) == 0.0)

    def test_h_coarse_captures_bridge_weight(self):
        W = _two_community_graph(bridge=0.37)
        result = coarse_grain(W, method="spectral", n_target=2)
        # only one inter-cluster edge in this fixture -- its weight must
        # survive into H_coarse's single off-diagonal entry.
        off_diag = result.H_coarse[result.H_coarse != np.diag(result.H_coarse)]
        assert result.H_coarse[0, 1] == pytest.approx(0.37) or result.H_coarse[1, 0] == pytest.approx(0.37)


class TestCoarseGrainEdgeCases:
    def test_n_target_at_or_above_n_returns_identity_partition(self):
        W = _two_community_graph()
        result = coarse_grain(W, method="louvain", n_target=100)
        assert result.n_clusters == 20
        np.testing.assert_array_equal(result.labels, np.arange(20))
        np.testing.assert_allclose(result.H_coarse, np.abs(W))

    def test_unknown_method_raises(self):
        W = _two_community_graph()
        with pytest.raises(ValueError):
            coarse_grain(W, method="kmeans", n_target=2)

    def test_louvain_merges_down_to_a_tight_node_budget(self):
        """Force Louvain's natural partition (likely >2 communities on a
        weakly-structured random graph) down via the merge-to-target path."""
        rng = np.random.default_rng(1)
        N = 24
        W = rng.uniform(0.0, 1.0, size=(N, N))
        W = (W + W.T) / 2
        np.fill_diagonal(W, 0.0)
        result = coarse_grain(W, method="louvain", n_target=3)
        assert result.n_clusters <= 3
        assert set(np.unique(result.labels).tolist()) == set(range(result.n_clusters))


# ---------------------------------------------------------------------------
# GAUGE: permutation invariance of the partition (coarse_grain)
# ---------------------------------------------------------------------------

class TestCoarseGrainPermutationInvariance:
    @pytest.mark.parametrize("method,n_target", [("louvain", 12), ("spectral", 2)])
    def test_partition_invariant_under_relabeling(self, method, n_target):
        W = _two_community_graph()
        N = W.shape[0]
        perm = np.random.default_rng(7).permutation(N)
        W_perm = W[np.ix_(perm, perm)]

        result = coarse_grain(W, method=method, n_target=n_target)
        result_perm = coarse_grain(W_perm, method=method, n_target=n_target)

        inv = np.argsort(perm)
        mapped_back = result_perm.labels[inv]
        assert _partition_sets(result.labels) == _partition_sets(mapped_back)


# ---------------------------------------------------------------------------
# trotter_cost -- Planned Validation: tighter error budget -> higher cost
# ---------------------------------------------------------------------------

class TestTrotterCost:
    def test_returns_expected_fields(self):
        W = _two_community_graph()
        result = trotter_cost(W, t=1.0, error_budget=0.1)
        assert isinstance(result, TrotterCostResult)
        assert result.n_qubits == 20
        assert result.n_terms > 0
        assert result.trotter_steps >= 1
        assert result.circuit_depth >= result.trotter_steps
        assert result.two_qubit_gates == result.trotter_steps * result.n_terms

    def test_tighter_error_budget_increases_cost(self):
        W = _two_community_graph()
        loose = trotter_cost(W, t=1.0, error_budget=0.5)
        tight = trotter_cost(W, t=1.0, error_budget=0.001)
        assert tight.trotter_steps > loose.trotter_steps
        assert tight.circuit_depth > loose.circuit_depth
        assert tight.two_qubit_gates > loose.two_qubit_gates

    def test_longer_time_increases_cost(self):
        W = _two_community_graph()
        short = trotter_cost(W, t=1.0, error_budget=0.1)
        long = trotter_cost(W, t=5.0, error_budget=0.1)
        assert long.trotter_steps > short.trotter_steps

    def test_no_edges_gives_trivial_cost(self):
        W = np.zeros((5, 5))
        result = trotter_cost(W, t=1.0, error_budget=0.1)
        assert result.n_terms == 0
        assert result.trotter_steps == 1
        assert result.two_qubit_gates == 0

    def test_rejects_nonpositive_error_budget(self):
        W = _two_community_graph()
        with pytest.raises(ValueError):
            trotter_cost(W, t=1.0, error_budget=0.0)
        with pytest.raises(ValueError):
            trotter_cost(W, t=1.0, error_budget=-0.1)

    def test_rejects_negative_time(self):
        W = _two_community_graph()
        with pytest.raises(ValueError):
            trotter_cost(W, t=-1.0, error_budget=0.1)


# ---------------------------------------------------------------------------
# GAUGE: permutation invariance of trotter_cost's scalar outputs
# ---------------------------------------------------------------------------

class TestTrotterCostPermutationInvariance:
    def test_scalars_invariant_under_relabeling(self):
        W = _two_community_graph()
        N = W.shape[0]
        perm = np.random.default_rng(3).permutation(N)
        W_perm = W[np.ix_(perm, perm)]

        result = trotter_cost(W, t=1.0, error_budget=0.1)
        result_perm = trotter_cost(W_perm, t=1.0, error_budget=0.1)

        assert result.n_qubits == result_perm.n_qubits
        assert result.n_terms == result_perm.n_terms
        assert result.trotter_steps == result_perm.trotter_steps
        assert result.circuit_depth == result_perm.circuit_depth
        assert result.two_qubit_gates == result_perm.two_qubit_gates
        assert result.energy_scale == pytest.approx(result_perm.energy_scale)
