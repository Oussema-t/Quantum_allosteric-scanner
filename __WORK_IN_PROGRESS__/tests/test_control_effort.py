"""TASK-0156 coverage -- minimum control-energy reachability scanning.

Two kinds of check, per this project's own Implementer discipline (verify
the machinery on synthetic data before trusting it on anything real):

1. **Correctness of the GRAPE gradient itself** -- no GRAPE code existed
   anywhere in this codebase before this task, so the analytic gradient
   is checked directly against a finite-difference estimate before
   trusting any optimization result built on it.
2. **The synthetic dumbbell gate** (task file's own Planned Validation,
   required to run BEFORE any real-target scoring): does `E_i` track
   *planted coupling strength* at *equal graph-hop-distance*, not just
   distance itself? Two chains of identical length and identical hop-
   distance from a shared seed, one with strong edge weights and one
   with weak edge weights -- the strong-chain's end residue must show
   lower minimum control energy than the weak-chain's, at identical hop
   count from the seed. This is the one test that distinguishes this
   observable from a repackaged proximity floor.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.control_effort import (  # noqa: E402
    ControlEffortResult,
    _forward_backward,
    _free_propagator,
    _seed_state,
    control_effort_score,
    scan_control_effort,
)


def _random_symmetric(n: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((n, n))
    return (A + A.T) / 2.0


def _dumbbell_chain(n_per_lobe: int, w_strong: float, w_weak: float) -> np.ndarray:
    """Hub (node 0) + two chains of `n_per_lobe` nodes each, identical
    topology/length, different edge weight -- lobe A (nodes 1..n_per_lobe)
    strongly coupled, lobe B (nodes n_per_lobe+1..2*n_per_lobe) weakly
    coupled. Both lobe-ends sit at hop-distance `n_per_lobe` from the hub
    -- identical by construction, only the coupling strength differs."""
    n = 1 + 2 * n_per_lobe
    H = np.zeros((n, n))
    prev = 0
    for i in range(1, n_per_lobe + 1):
        H[prev, i] = H[i, prev] = w_strong
        prev = i
    prev = 0
    for i in range(n_per_lobe + 1, 2 * n_per_lobe + 1):
        H[prev, i] = H[i, prev] = w_weak
        prev = i
    return H


class TestForwardBackwardGradient:
    def test_analytic_gradient_matches_finite_difference(self):
        n = 6
        H0 = _random_symmetric(n, seed=1)
        source = np.array([0])
        target_idx = np.array([3])
        n_slices = 4
        T = 2.0
        dt = T / n_slices
        control_idx = source

        P = _free_propagator(H0, dt)
        psi0 = _seed_state(n, source)

        rng = np.random.default_rng(2)
        u = 0.1 * rng.standard_normal((1, n_slices, len(control_idx)))

        fidelity0, grad = _forward_backward(u, psi0, P, control_idx, target_idx, dt)

        eps = 1e-6
        for k in range(n_slices):
            u_plus = u.copy()
            u_plus[0, k, 0] += eps
            f_plus, _ = _forward_backward(u_plus, psi0, P, control_idx, target_idx, dt)

            u_minus = u.copy()
            u_minus[0, k, 0] -= eps
            f_minus, _ = _forward_backward(u_minus, psi0, P, control_idx, target_idx, dt)

            fd_grad = (f_plus[0] - f_minus[0]) / (2 * eps)
            assert fd_grad == pytest.approx(grad[0, k, 0], abs=1e-4)

    def test_fidelity_matches_direct_matrix_exponential(self):
        """Independent check of the propagation itself (not just the
        gradient): the Trotterized forward pass must reproduce the exact
        (`scipy.linalg.expm`-based) propagator in the zero-control limit."""
        from scipy.linalg import expm

        n = 5
        H0 = _random_symmetric(n, seed=3)
        source = np.array([0])
        target_idx = np.arange(n)
        T = 3.0
        n_slices = 30  # fine enough that Trotter error is small
        dt = T / n_slices

        P = _free_propagator(H0, dt)
        psi0 = _seed_state(n, source)
        u = np.zeros((n, n_slices, len(source)))

        fidelity, _ = _forward_backward(u, psi0, P, source, target_idx, dt)

        exact_U = expm(-1j * H0 * T)
        exact_psi = exact_U @ psi0
        exact_fidelity = np.abs(exact_psi) ** 2

        np.testing.assert_allclose(fidelity, exact_fidelity, atol=1e-3)


class TestSyntheticDumbbellGate:
    """Pre-registered validation, required by the task file to run BEFORE
    any real-target scoring: `scan_control_effort` on a synthetic graph
    with known planted coupling."""

    def test_strong_lobe_end_has_lower_energy_than_weak_lobe_end_at_equal_hop_distance(self):
        n_per_lobe = 4
        H0 = _dumbbell_chain(n_per_lobe, w_strong=3.0, w_weak=0.3)
        source = np.array([0])

        strong_end = n_per_lobe
        weak_end = 2 * n_per_lobe

        result = scan_control_effort(
            H0, source, T=6.0, n_slices=12, fidelity_target=0.3,
            penalty_weight=800.0, n_iters=250, lr=0.05,
            target_indices=np.array([strong_end, weak_end]),
        )

        assert result.feasible[0], "strong-lobe end should be reachable at this (T, F)"
        assert np.isfinite(result.energy[0])
        if result.feasible[1]:
            assert result.energy[0] < result.energy[1]
        # else: weak lobe genuinely infeasible at this (T, F) -- also a
        # valid pass, an even stronger separation than a finite comparison.

    def test_control_effort_score_ranks_strong_above_weak(self):
        n_per_lobe = 4
        H0 = _dumbbell_chain(n_per_lobe, w_strong=3.0, w_weak=0.3)
        source = np.array([0])
        strong_end = n_per_lobe
        weak_end = 2 * n_per_lobe

        result = scan_control_effort(
            H0, source, T=6.0, n_slices=12, fidelity_target=0.3,
            penalty_weight=800.0, n_iters=250, lr=0.05,
            target_indices=np.array([strong_end, weak_end]),
        )
        score = control_effort_score(result)
        assert score[0] > score[1]

    def test_naive_hop_distance_cannot_distinguish_the_two_lobe_ends(self):
        """Sanity check on the test fixture itself: confirms the two
        lobe ends really are at identical hop-distance (so a positive
        result above is attributable to coupling strength, not a
        confounded distance difference the fixture accidentally
        introduced)."""
        n_per_lobe = 4
        H0 = _dumbbell_chain(n_per_lobe, w_strong=3.0, w_weak=0.3)
        A = (H0 != 0).astype(float)
        import networkx as nx

        G = nx.from_numpy_array(A)
        d_strong = nx.shortest_path_length(G, 0, n_per_lobe)
        d_weak = nx.shortest_path_length(G, 0, 2 * n_per_lobe)
        assert d_strong == d_weak == n_per_lobe


class TestScanControlEffort:
    def test_seed_itself_is_cheap_to_reach(self):
        n = 8
        H0 = _random_symmetric(n, seed=5)
        source = np.array([0])
        result = scan_control_effort(
            H0, source, T=4.0, n_slices=10, fidelity_target=0.2,
            penalty_weight=500.0, n_iters=150,
            target_indices=np.array([0]),
        )
        assert result.feasible[0]

    def test_unreachable_target_marked_infeasible_not_silently_wrong(self):
        """An absurdly high fidelity target within a short horizon and a
        tiny iteration budget must be reported as infeasible, not as a
        spuriously low energy."""
        n = 6
        H0 = _random_symmetric(n, seed=6) * 0.01  # very weak coupling
        source = np.array([0])
        result = scan_control_effort(
            H0, source, T=0.5, n_slices=4, fidelity_target=0.999,
            penalty_weight=50.0, n_iters=5,
            target_indices=np.array([5]),
        )
        assert not result.feasible[0]
        assert np.isnan(result.energy[0])

    def test_chunking_gives_identical_results_to_a_single_batch(self):
        n = 10
        H0 = _random_symmetric(n, seed=7)
        source = np.array([0])
        kwargs = dict(
            T=3.0, n_slices=8, fidelity_target=0.2, penalty_weight=300.0,
            n_iters=80, lr=0.05, seed=11,
        )
        result_full = scan_control_effort(H0, source, chunk_size=1000, **kwargs)
        result_chunked = scan_control_effort(H0, source, chunk_size=3, **kwargs)
        np.testing.assert_allclose(result_full.fidelity, result_chunked.fidelity, atol=1e-10)


class TestControlEffortScore:
    def test_infeasible_residues_score_below_every_feasible_one(self):
        result = ControlEffortResult(
            energy=np.array([1.0, 2.0, np.nan]),
            fidelity=np.array([0.6, 0.55, 0.1]),
            feasible=np.array([True, True, False]),
            horizon_T=5.0, n_slices=10, fidelity_target=0.5,
            penalty_weight=100.0, control_indices=np.array([0]),
        )
        score = control_effort_score(result)
        assert score[0] > score[1]  # lower energy -> higher score
        assert score[2] < score[0] and score[2] < score[1]

    def test_all_infeasible_does_not_crash(self):
        result = ControlEffortResult(
            energy=np.array([np.nan, np.nan]),
            fidelity=np.array([0.1, 0.05]),
            feasible=np.array([False, False]),
            horizon_T=5.0, n_slices=10, fidelity_target=0.5,
            penalty_weight=100.0, control_indices=np.array([0]),
        )
        score = control_effort_score(result)
        assert np.all(np.isfinite(score))
