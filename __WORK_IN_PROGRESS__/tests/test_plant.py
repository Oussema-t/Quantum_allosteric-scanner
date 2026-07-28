"""TASK-0167.001 -- tests for `allostery.plant`. Synthetic fixtures only
(this project's established convention for fast, network-free unit tests,
`tests/test_nulls.py`/`tests/test_chiral.py`'s own precedent) -- the
"on a real target" verification this task's own Planned Validation asks
for was run interactively against KRAS_G12C (see this task's own Done
section for the real numbers: `dcc_low`/`H_new` exactly invariant,
conductance `1/R_eff` monotonically increasing with strength), not
re-run here to keep this suite fast and RCSB-independent.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.hamiltonians import contact_matrix, laplacian  # noqa: E402
from allostery.plant import (  # noqa: E402
    PlantReport,
    assert_confound_orthogonal,
    plant_channel,
    select_distal_patch,
)
from allostery.transport import effective_resistance_from_source  # noqa: E402


def _helix_coords(n: int = 80, seed: int = 0) -> np.ndarray:
    """A helical chain -- genuine 3D compactness (turns pack residues `i`
    and `i+~10` close in space despite being far in sequence), enough
    local + tertiary contact structure for `select_distal_patch` to find
    a real distal, floor-blind patch, unlike a bare unstructured line."""
    rng = np.random.default_rng(seed)
    t = np.arange(n, dtype=float)
    coords = np.column_stack([
        6.0 * np.cos(t * 0.55) + 0.2 * rng.standard_normal(n),
        6.0 * np.sin(t * 0.55) + 0.2 * rng.standard_normal(n),
        1.6 * t,
    ])
    return coords


class TestSelectDistalPatch:
    def test_returns_requested_size(self):
        coords = _helix_coords()
        W = contact_matrix(coords, cutoff=8.0, weight="invdist")
        seed_idx = np.array([0, 1, 2])
        patch = select_distal_patch(coords, W, seed_idx, size=8, rng=np.random.default_rng(1), cutoff=8.0)
        assert len(patch) == 8
        assert len(set(patch.tolist())) == 8

    def test_patch_excludes_seed(self):
        coords = _helix_coords()
        W = contact_matrix(coords, cutoff=8.0, weight="invdist")
        seed_idx = np.array([0, 1, 2])
        patch = select_distal_patch(coords, W, seed_idx, size=8, rng=np.random.default_rng(1), cutoff=8.0)
        assert not (set(patch.tolist()) & set(seed_idx.tolist()))

    def test_patch_is_genuinely_distal_and_floor_blind(self):
        """Both admission criteria hold on the returned patch -- checked
        directly on the actual return value, not just trusted from the
        function's own internal logic."""
        from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed
        from allostery.metrics import auc as _auc

        coords = _helix_coords()
        W = contact_matrix(coords, cutoff=8.0, weight="invdist")
        seed_idx = np.array([0, 1, 2])
        cutoff = 8.0
        patch = select_distal_patch(coords, W, seed_idx, size=8, rng=np.random.default_rng(1), cutoff=cutoff)

        n = len(coords)
        hops = -hop_from_seed(coords, seed_idx, cutoff=cutoff)
        hop_threshold = np.percentile(hops, 60)
        assert hops[patch].mean() >= hop_threshold

        mask = np.ones(n, dtype=bool)
        mask[seed_idx] = False
        label = np.zeros(n, dtype=int)
        label[patch] = 1
        floor_scores = [
            degree_centrality(coords, cutoff=cutoff),
            hop_from_seed(coords, seed_idx, cutoff=cutoff),
            euclid_from_seed_centroid(coords, seed_idx),
        ]
        max_floor = max(_auc(fs[mask], label[mask]) for fs in floor_scores)
        assert max_floor <= 0.5

    def test_raises_when_infeasible(self):
        """An impossibly strict hop percentile (100th, i.e. only the
        single most-distal residue itself would qualify, likely
        excluded by patch-size >1) makes admission infeasible within a
        small attempt budget -- a real, reportable failure, not a
        silent fallback to a worse patch."""
        coords = _helix_coords(n=30)
        W = contact_matrix(coords, cutoff=8.0, weight="invdist")
        seed_idx = np.array([0])
        with pytest.raises(RuntimeError):
            select_distal_patch(
                coords, W, seed_idx, size=10, rng=np.random.default_rng(1),
                cutoff=8.0, hop_percentile=100.0, max_attempts=50,
            )


class TestPlantChannelIdentity:
    def test_zero_strength_returns_bit_identical_W(self):
        coords = _helix_coords()
        W = contact_matrix(coords, cutoff=8.0, weight="invdist")
        seed_idx = np.array([0, 1, 2])
        target_idx = np.array([40, 41, 42])
        W_planted, report = plant_channel(W, seed_idx, target_idx, strength=0.0, n_paths=10, rng=np.random.default_rng(1))
        assert np.array_equal(W, W_planted)
        assert report.strength == 0.0
        assert report.n_paths_applied == 0
        assert report.edges_modified == []

    def test_zero_strength_is_a_true_copy_not_a_view(self):
        coords = _helix_coords()
        W = contact_matrix(coords, cutoff=8.0, weight="invdist")
        seed_idx = np.array([0, 1, 2])
        target_idx = np.array([40, 41, 42])
        W_planted, _ = plant_channel(W, seed_idx, target_idx, strength=0.0, n_paths=10, rng=np.random.default_rng(1))
        W_planted[0, 1] = -999.0
        assert W[0, 1] != -999.0


class TestPlantChannelReachabilityAndEffect:
    def test_paths_found_between_connected_regions(self):
        coords = _helix_coords()
        W = contact_matrix(coords, cutoff=8.0, weight="invdist")
        seed_idx = np.array([0, 1, 2])
        target_idx = np.array([40, 41, 42])
        _, report = plant_channel(W, seed_idx, target_idx, strength=5.0, n_paths=10, rng=np.random.default_rng(1))
        assert report.n_paths_applied > 0
        assert report.n_paths_applied + report.n_paths_failed == report.n_paths_requested
        assert len(report.edges_modified) > 0

    def test_edges_modified_only_multiply_existing_edges(self):
        """No new edge is ever introduced -- every reweighted (i,j) had
        W[i,j] > 0 before planting."""
        coords = _helix_coords()
        W = contact_matrix(coords, cutoff=8.0, weight="invdist")
        seed_idx = np.array([0, 1, 2])
        target_idx = np.array([40, 41, 42])
        W_planted, report = plant_channel(W, seed_idx, target_idx, strength=5.0, n_paths=10, rng=np.random.default_rng(1))
        for i, j in report.edges_modified:
            assert W[i, j] > 0
            assert W_planted[i, j] == pytest.approx(W[i, j] * 6.0)  # (1 + strength)

    def test_unweighted_adjacency_unchanged(self):
        coords = _helix_coords()
        W = contact_matrix(coords, cutoff=8.0, weight="invdist")
        seed_idx = np.array([0, 1, 2])
        target_idx = np.array([40, 41, 42])
        W_planted, _ = plant_channel(W, seed_idx, target_idx, strength=30.0, n_paths=10, rng=np.random.default_rng(1))
        assert np.array_equal(W > 0, W_planted > 0)

    def test_independent_effect_conductance_rises_with_strength(self):
        """The plant demonstrably changes something: conductance
        (`transport.effective_resistance_from_source`'s own `1/R_eff`
        return convention -- confirmed by reading its docstring, not
        assumed from the function's name) from seed to the planted
        target strictly rises with strength, matching Rayleigh's
        monotonicity law (more/stronger conducting paths -> more
        conductance) -- if this failed, the plant would be inert and
        this whole module useless, per this task's own Planned
        Validation."""
        coords = _helix_coords()
        W = contact_matrix(coords, cutoff=8.0, weight="invdist")
        seed_idx = np.array([0, 1, 2])
        target_idx = np.array([40, 41, 42])

        conductances = []
        for s in (0.0, 1.0, 5.0, 10.0, 30.0):
            W_planted, _ = plant_channel(W, seed_idx, target_idx, strength=s, n_paths=10, rng=np.random.default_rng(1))
            L_planted = laplacian(W_planted, normalised=False)
            cond = effective_resistance_from_source(L_planted, seed_idx)
            conductances.append(float(cond[target_idx].mean()))

        assert conductances == sorted(conductances)
        assert conductances[-1] > conductances[0] * 2  # a real, not marginal, rise

    def test_disconnected_pair_recorded_as_failure_not_fatal(self):
        """Two residues with no path between them (disjoint components)
        must not crash `plant_channel` -- recorded in `n_paths_failed`.
        Two separate small helices, no cross-block edges by construction
        (a fresh all-zero `W`, each block filled independently)."""
        block1 = _helix_coords(n=10, seed=1)
        block2 = _helix_coords(n=10, seed=2) + np.array([1e5, 0.0, 0.0])
        W_block1 = contact_matrix(block1, cutoff=8.0, weight="invdist")
        W_block2 = contact_matrix(block2, cutoff=8.0, weight="invdist")
        W_disjoint = np.zeros((20, 20))
        W_disjoint[:10, :10] = W_block1
        W_disjoint[10:, 10:] = W_block2

        seed_idx = np.array([0])
        target_idx = np.array([10])  # first residue of the disconnected block
        _, report = plant_channel(W_disjoint, seed_idx, target_idx, strength=5.0, n_paths=5, rng=np.random.default_rng(1))
        assert report.n_paths_failed == 5
        assert report.n_paths_applied == 0
        assert report.edges_modified == []


class TestAssertConfoundOrthogonal:
    def test_passes_across_a_strength_sweep(self):
        coords = _helix_coords()
        W = contact_matrix(coords, cutoff=8.0, weight="invdist")
        seed_idx = np.array([0, 1, 2])
        target_idx = np.array([40, 41, 42])
        n = len(coords)
        label = np.zeros(n, dtype=int)
        label[target_idx] = 1

        for s in (0.0, 1.0, 5.0, 10.0, 30.0):
            W_planted, _ = plant_channel(W, seed_idx, target_idx, strength=s, n_paths=10, rng=np.random.default_rng(1))
            pre, post = assert_confound_orthogonal(W, W_planted, coords, seed_idx, label, cutoff=8.0)
            assert pre == post

    def test_fails_on_a_deliberately_contaminated_plant(self):
        """A gate that has never been seen to fire is not a gate
        (TASK-0103's own discipline) -- construct a plant that ADDS a
        new edge (violating 'existing edges only') and confirm the gate
        catches it."""
        coords = _helix_coords()
        W = contact_matrix(coords, cutoff=8.0, weight="invdist")
        seed_idx = np.array([0, 1, 2])
        target_idx = np.array([40, 41, 42])
        n = len(coords)
        label = np.zeros(n, dtype=int)
        label[target_idx] = 1

        W_contaminated = W.copy()
        # Find a pair with exactly zero weight (no existing edge) and add one.
        zero_pairs = np.argwhere((W == 0) & ~np.eye(n, dtype=bool))
        i, j = zero_pairs[0]
        W_contaminated[i, j] = 1.0
        W_contaminated[j, i] = 1.0

        with pytest.raises(AssertionError):
            assert_confound_orthogonal(W, W_contaminated, coords, seed_idx, label, cutoff=8.0)

    def test_returns_pre_post_floor_dicts(self):
        coords = _helix_coords()
        W = contact_matrix(coords, cutoff=8.0, weight="invdist")
        seed_idx = np.array([0, 1, 2])
        target_idx = np.array([40, 41, 42])
        n = len(coords)
        label = np.zeros(n, dtype=int)
        label[target_idx] = 1
        W_planted, _ = plant_channel(W, seed_idx, target_idx, strength=5.0, n_paths=10, rng=np.random.default_rng(1))
        pre, post = assert_confound_orthogonal(W, W_planted, coords, seed_idx, label, cutoff=8.0)
        assert set(pre.keys()) == {"degree", "hop", "euclid"}
        assert set(post.keys()) == {"degree", "hop", "euclid"}


class TestPlantReport:
    def test_is_a_populated_dataclass(self):
        coords = _helix_coords()
        W = contact_matrix(coords, cutoff=8.0, weight="invdist")
        seed_idx = np.array([0, 1, 2])
        target_idx = np.array([40, 41, 42])
        _, report = plant_channel(W, seed_idx, target_idx, strength=5.0, n_paths=7, rng=np.random.default_rng(1))
        assert isinstance(report, PlantReport)
        assert report.strength == 5.0
        assert report.n_paths_requested == 7
        assert report.pre_floor_auc is None  # caller's job to fill from the gate
        assert report.post_floor_auc is None
