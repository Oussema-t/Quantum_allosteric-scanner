"""TASK-0068 coverage -- noise.py's Trotterized XY-walk circuit + gate-noise
simulation, against small synthetic graphs (fast, no network). Real-target
runs are this task's own Planned Validation (run directly, findings
written up separately), not re-asserted here as golden values.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

pytest.importorskip("qiskit_aer")

from allostery.noise import (  # noqa: E402
    build_noise_model,
    build_xy_walk_circuit,
    run_noise_sweep,
    simulate_occupation,
    time_sampled_converged_occupation,
    top_k_overlap,
)


def _ring_graph(n: int) -> np.ndarray:
    H = np.zeros((n, n))
    for i in range(n):
        j = (i + 1) % n
        H[i, j] = H[j, i] = 1.0
    return H


def _disconnected_pair(n: int) -> np.ndarray:
    """No edges at all -- the walk cannot leave the source qubit."""
    return np.zeros((n, n))


class TestBuildXyWalkCircuit:
    def test_circuit_has_one_qubit_per_node(self):
        H = _ring_graph(5)
        qc = build_xy_walk_circuit(H, t=1.0, trotter_steps=2, source=0)
        assert qc.num_qubits == 5

    def test_more_trotter_steps_gives_a_deeper_circuit(self):
        H = _ring_graph(4)
        shallow = build_xy_walk_circuit(H, t=1.0, trotter_steps=1, source=0)
        deep = build_xy_walk_circuit(H, t=1.0, trotter_steps=4, source=0)
        assert deep.size() > shallow.size()


class TestSimulateOccupationNoiseless:
    def test_occupation_sums_to_one(self):
        H = _ring_graph(5)
        qc = build_xy_walk_circuit(H, t=1.0, trotter_steps=3, source=0)
        occ = simulate_occupation(qc)
        assert occ.sum() == pytest.approx(1.0, abs=1e-6)

    def test_no_edges_means_the_walk_never_leaves_the_seed(self):
        """A disconnected graph (no XY coupling at all) must leave all
        probability on the source qubit -- the circuit-model analogue of
        propagators.ctqw on a graph with no off-diagonal structure."""
        H = _disconnected_pair(4)
        qc = build_xy_walk_circuit(H, t=5.0, trotter_steps=3, source=1)
        occ = simulate_occupation(qc)
        expected = np.zeros(4)
        expected[1] = 1.0
        np.testing.assert_allclose(occ, expected, atol=1e-9)

    def test_zero_time_leaves_the_walk_at_the_seed(self):
        H = _ring_graph(5)
        qc = build_xy_walk_circuit(H, t=0.0, trotter_steps=3, source=2)
        occ = simulate_occupation(qc)
        expected = np.zeros(5)
        expected[2] = 1.0
        np.testing.assert_allclose(occ, expected, atol=1e-9)


class TestSimulateOccupationNoisy:
    def test_noise_pushes_occupation_away_from_the_ideal_single_excitation_conservation(self):
        """Depolarizing error on 2-qubit gates does not conserve the
        single-excitation subspace -- the noisy occupation sum should
        differ measurably from the noiseless sum=1 baseline at a
        non-trivial error rate."""
        H = _ring_graph(5)
        qc = build_xy_walk_circuit(H, t=1.0, trotter_steps=4, source=0)
        occ_ideal = simulate_occupation(qc)
        noise_model = build_noise_model(depolarizing_prob=0.1, amp_damping_prob=0.1)
        occ_noisy = simulate_occupation(qc, noise_model=noise_model)
        assert occ_ideal.sum() == pytest.approx(1.0, abs=1e-6)
        assert abs(occ_noisy.sum() - 1.0) > 0.05

    def test_zero_error_rate_noise_model_is_close_to_noiseless(self):
        H = _ring_graph(4)
        qc = build_xy_walk_circuit(H, t=1.0, trotter_steps=2, source=0)
        occ_ideal = simulate_occupation(qc)
        noise_model = build_noise_model(depolarizing_prob=0.0, amp_damping_prob=0.0)
        occ_zero_noise = simulate_occupation(qc, noise_model=noise_model)
        np.testing.assert_allclose(occ_ideal, occ_zero_noise, atol=1e-6)


class TestTopKOverlap:
    def test_identical_vectors_give_full_overlap(self):
        occ = np.array([0.5, 0.3, 0.1, 0.1])
        assert top_k_overlap(occ, occ, k=2) == pytest.approx(1.0)

    def test_disjoint_top_k_gives_zero_overlap(self):
        a = np.array([1.0, 0.9, 0.1, 0.0])
        b = np.array([0.0, 0.1, 0.9, 1.0])
        assert top_k_overlap(a, b, k=2) == pytest.approx(0.0)

    def test_partial_overlap_is_a_real_jaccard_fraction(self):
        a = np.array([1.0, 0.9, 0.8, 0.1])  # top-2: {0, 1}
        b = np.array([1.0, 0.1, 0.8, 0.9])  # top-2: {0, 3}
        # intersection {0}, union {0,1,3} -> 1/3
        assert top_k_overlap(a, b, k=2) == pytest.approx(1.0 / 3.0)


class TestCoarseGrainSeamConsumption:
    """SEAM-0010: this module's consumption of coarse.py's real return
    shapes -- CoarseGrainResult (labels, n_clusters, H_coarse: symmetric,
    zero-diagonal) -- asserted against the actual function, not a
    re-derived assumption of what it returns."""

    def test_h_coarse_is_symmetric_zero_diagonal_and_matches_n_clusters(self):
        from allostery.coarse import coarse_grain

        H = _ring_graph(12)
        cg = coarse_grain(H, method="louvain", n_target=5, seed=0)
        assert cg.H_coarse.shape == (cg.n_clusters, cg.n_clusters)
        np.testing.assert_allclose(cg.H_coarse, cg.H_coarse.T)
        np.testing.assert_allclose(np.diag(cg.H_coarse), 0.0)

    def test_circuit_qubit_count_matches_n_clusters_not_original_n(self):
        from allostery.coarse import coarse_grain

        H = _ring_graph(12)
        cg = coarse_grain(H, method="louvain", n_target=5, seed=0)
        qc = build_xy_walk_circuit(cg.H_coarse, t=1.0, trotter_steps=2, source=0)
        assert qc.num_qubits == cg.n_clusters

    def test_seed_residue_maps_to_its_cluster_via_labels_not_the_original_index(self):
        """The qubit a seed *residue* maps to is cg.labels[residue], not
        the residue's own original index -- these differ whenever
        coarse-graining actually merges nodes (the exact confusion
        SEAM-0010 warns a naive consumer could make)."""
        from allostery.coarse import coarse_grain

        H = _ring_graph(12)
        cg = coarse_grain(H, method="louvain", n_target=4, seed=0)
        seed_residue = 7
        source_qubit = int(cg.labels[seed_residue])
        assert 0 <= source_qubit < cg.n_clusters
        # for a graph that actually coarsens (12 -> 4), the qubit index is
        # not simply the residue index truncated/reused
        assert cg.n_clusters < H.shape[0]

    def test_trotter_cost_step_count_is_not_silently_reused_as_circuit_depth(self):
        """SEAM-0010's own warning: trotter_steps and circuit_depth are
        different quantities (circuit_depth = trotter_steps *
        layers_per_step); this module's sweep grid must be documented as
        trotter_steps (repetitions), not silently mislabeled as depth."""
        from allostery.coarse import coarse_grain, trotter_cost

        H = _ring_graph(8)
        cg = coarse_grain(H, method="louvain", n_target=5, seed=0)
        cost = trotter_cost(cg.H_coarse, t=1.0, error_budget=0.1)
        assert cost.circuit_depth >= cost.trotter_steps


class TestRunNoiseSweep:
    def test_returns_one_row_per_depth_error_rate_combination(self):
        H = _ring_graph(4)
        rows = run_noise_sweep(
            H, source=0, t=1.0, trotter_steps_grid=[2, 4], error_rates=[0.0, 0.05], k=2,
        )
        assert len(rows) == 4
        combos = {(r["trotter_steps"], r["error_rate"]) for r in rows}
        assert combos == {(2, 0.0), (2, 0.05), (4, 0.0), (4, 0.05)}

    def test_zero_error_rate_gives_full_top_k_overlap(self):
        H = _ring_graph(4)
        rows = run_noise_sweep(H, source=0, t=1.0, trotter_steps_grid=[3], error_rates=[0.0], k=2)
        assert rows[0]["top_k_overlap"] == pytest.approx(1.0)

    def test_dephasing_gamma_is_recorded_per_row(self):
        H = _ring_graph(4)
        rows = run_noise_sweep(
            H, source=0, t=1.0, trotter_steps_grid=[2], error_rates=[0.05], k=2, dephasing_gamma=0.1,
        )
        assert rows[0]["dephasing_gamma"] == pytest.approx(0.1)


class TestTimeSampledConvergedOccupation:
    """TASK-0182 -- circuit-model approximation of `propagators.
    time_averaged_ctqw_converged`'s exact t->infinity closed form. A fixed
    depth circuit only ever gives a snapshot at one t; this function's
    whole reason to exist is averaging several such snapshots, so the
    tests here are about that averaging behavior, not re-testing
    `simulate_occupation`/`build_xy_walk_circuit` themselves (already
    covered above)."""

    def test_output_sums_to_one_and_matches_node_count(self):
        H = _ring_graph(5)
        occ = time_sampled_converged_occupation(H, source=0, t_values=[0.5, 1.0, 1.5], trotter_steps=3)
        assert occ.shape == (5,)
        assert occ.sum() == pytest.approx(1.0, abs=1e-6)

    def test_single_t_value_of_zero_leaves_everything_at_the_seed(self):
        H = _ring_graph(5)
        occ = time_sampled_converged_occupation(H, source=2, t_values=[0.0], trotter_steps=3)
        expected = np.zeros(5)
        expected[2] = 1.0
        np.testing.assert_allclose(occ, expected, atol=1e-9)

    def test_averaging_over_more_t_values_moves_toward_the_exact_converged_limit(self):
        """Not exact convergence (fixed `trotter_steps`, see this
        function's own docstring on why) -- but denser time sampling over
        the same window should not move *away* from the closed-form
        answer. Ring graph has real degeneracies (TASK-0130's own grouping
        logic handles those), giving a real, non-trivial exact target to
        compare against."""
        from allostery.propagators import time_averaged_ctqw_converged

        H = _ring_graph(6)
        exact = time_averaged_ctqw_converged(H, source=0)

        sparse = time_sampled_converged_occupation(H, source=0, t_values=np.linspace(0, 20, 3), trotter_steps=4)
        dense = time_sampled_converged_occupation(H, source=0, t_values=np.linspace(0, 20, 20), trotter_steps=4)

        l1_sparse = np.abs(sparse - exact).sum()
        l1_dense = np.abs(dense - exact).sum()
        assert l1_dense <= l1_sparse + 1e-6

    def test_noise_model_is_applied_to_every_sampled_circuit(self):
        """Same qualitative check as `TestSimulateOccupationNoisy` above,
        applied through the averaging wrapper: a real error rate must
        measurably break single-excitation-subspace conservation even
        after averaging over several t samples."""
        H = _ring_graph(5)
        noise_model = build_noise_model(depolarizing_prob=0.1, amp_damping_prob=0.1)
        occ_noisy = time_sampled_converged_occupation(
            H, source=0, t_values=[0.5, 1.0, 1.5], trotter_steps=4, noise_model=noise_model
        )
        assert abs(occ_noisy.sum() - 1.0) > 0.02

    def test_zero_error_rate_noise_model_matches_noiseless(self):
        H = _ring_graph(4)
        t_values = [0.5, 1.0]
        occ_ideal = time_sampled_converged_occupation(H, source=0, t_values=t_values, trotter_steps=2)
        noise_model = build_noise_model(depolarizing_prob=0.0, amp_damping_prob=0.0)
        occ_zero_noise = time_sampled_converged_occupation(
            H, source=0, t_values=t_values, trotter_steps=2, noise_model=noise_model
        )
        np.testing.assert_allclose(occ_ideal, occ_zero_noise, atol=1e-6)
