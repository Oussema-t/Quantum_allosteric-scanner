"""TASK-0136 -- tests for `allostery.percolation` (path-ensemble +
percolation connectivity between two residue sets)."""
from __future__ import annotations

import numpy as np
import pytest

from allostery.percolation import (
    percolation_threshold,
    set_edge_connectivity,
    shortest_path_ensemble,
)


def _chain_coords(n: int, spacing: float = 3.8) -> np.ndarray:
    return np.column_stack([np.arange(n, dtype=float) * spacing, np.zeros(n), np.zeros(n)])


def _dumbbell_coords():
    """Two 4-node lobes (LEFT: 0-3, RIGHT: 8-11) joined by a single 4-node
    bridge (4-7) -- a deliberately narrow bottleneck: exactly one route
    connects the lobes, so edge connectivity must be exactly 1 and the
    percolation merge must occur at the bridge's own weakest link."""
    left = np.column_stack([np.zeros(4), np.arange(4) * 3.0, np.zeros(4)])
    bridge = np.column_stack([np.arange(1, 5) * 3.0, np.full(4, 6.0), np.zeros(4)])
    right = np.column_stack([np.full(4, 15.0), np.arange(4) * 3.0, np.zeros(4)])
    return np.vstack([left, bridge, right])


def _redundant_coords():
    """Two 3-node lobes joined by 3 independent parallel bridges (no
    shared intermediate node) -- edge connectivity must be exactly 3."""
    left = np.array([[0.0, 0.0, 0.0], [0.0, 4.0, 0.0], [0.0, 8.0, 0.0]])
    right = np.array([[10.0, 0.0, 0.0], [10.0, 4.0, 0.0], [10.0, 8.0, 0.0]])
    # One bridge residue per lane, each close to its own lane's left/right
    # endpoint only (>cutoff from the other lanes) so the three routes stay
    # edge-disjoint.
    bridges = np.array([[5.0, 0.0, 0.0], [5.0, 4.0, 0.0], [5.0, 8.0, 0.0]])
    return np.vstack([left, bridges, right])


class TestShortestPathEnsemble:
    def test_chain_shortest_path_is_the_literal_chain(self):
        """The reported path includes both endpoint residues (source and
        target themselves), not just the intermediate channel -- the more
        useful "literal channel, ready to inspect" report this task's own
        Outcome (a) asks for."""
        coords = _chain_coords(8)
        result = shortest_path_ensemble(coords, source=0, target=7, cutoff=5.0, tol=0.0)
        assert result["shortest_path"] == [0, 1, 2, 3, 4, 5, 6, 7]

    def test_overlapping_source_target_raises(self):
        coords = _chain_coords(5)
        with pytest.raises(ValueError, match="overlap"):
            shortest_path_ensemble(coords, source=[0, 1], target=[1, 2], cutoff=5.0)

    def test_disconnected_sets_raise(self):
        left = _chain_coords(3)
        right = _chain_coords(3) + np.array([1000.0, 0.0, 0.0])
        coords = np.vstack([left, right])
        with pytest.raises(ValueError, match="no path"):
            shortest_path_ensemble(coords, source=0, target=5, cutoff=5.0)

    def test_ensemble_includes_only_near_tie_paths(self):
        """On the redundant-lobe fixture, all 3 parallel single-bridge
        routes are exactly the same length -- the ensemble at tol=0 must
        include all 3, not just one arbitrary pick."""
        coords = _redundant_coords()
        result = shortest_path_ensemble(coords, source=[0, 1, 2], target=[6, 7, 8], cutoff=6.0, tol=0.01, max_paths=10)
        assert result["n_ensemble"] == 3


class TestSetEdgeConnectivity:
    def test_single_bottleneck_bridge_gives_connectivity_one(self):
        coords = _dumbbell_coords()
        result = set_edge_connectivity(coords, source=[0, 1, 2, 3], target=[8, 9, 10, 11], cutoff=5.0)
        assert result["edge_connectivity"] == 1
        assert len(result["cut_edges"]) == 1

    def test_three_parallel_bridges_give_connectivity_three(self):
        coords = _redundant_coords()
        result = set_edge_connectivity(coords, source=[0, 1, 2], target=[6, 7, 8], cutoff=6.0)
        assert result["edge_connectivity"] == 3

    def test_cut_edges_exclude_virtual_nodes(self):
        coords = _dumbbell_coords()
        result = set_edge_connectivity(coords, source=[0, 1, 2, 3], target=[8, 9, 10, 11], cutoff=5.0)
        for u, v in result["cut_edges"]:
            assert isinstance(u, int) and isinstance(v, int)

    def test_overlapping_sets_raise(self):
        coords = _chain_coords(5)
        with pytest.raises(ValueError, match="overlap"):
            set_edge_connectivity(coords, source=[0], target=[0, 1], cutoff=5.0)


class TestPercolationThreshold:
    def test_chain_merge_edge_is_the_last_link_closing_the_gap(self):
        coords = _chain_coords(6)
        result = percolation_threshold(coords, source=0, target=5, cutoff=5.0)
        # every consecutive pair is equally strong on a uniform chain --
        # the merge must occur once enough edges are added to bridge 0..5.
        assert result["n_edges_added"] >= 5

    def test_merge_distance_matches_the_actual_edge(self):
        coords = _dumbbell_coords()
        result = percolation_threshold(coords, source=[0, 1, 2, 3], target=[8, 9, 10, 11], cutoff=5.0)
        i, j = result["merge_edge"]
        d = np.linalg.norm(coords[i] - coords[j])
        assert result["merge_distance"] == pytest.approx(d, abs=1e-4)

    def test_overlapping_sets_raise(self):
        coords = _chain_coords(5)
        with pytest.raises(ValueError, match="overlap"):
            percolation_threshold(coords, source=[0], target=[0, 1], cutoff=5.0)

    def test_disconnected_sets_raise(self):
        left = _chain_coords(3)
        right = _chain_coords(3) + np.array([1000.0, 0.0, 0.0])
        coords = np.vstack([left, right])
        with pytest.raises(ValueError, match="disconnected"):
            percolation_threshold(coords, source=0, target=5, cutoff=5.0)
