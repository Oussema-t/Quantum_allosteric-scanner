"""TASK-0007 coverage -- select.py unsupervised operator selector.

Synthetic graphs only (path/star/complete), matching the task's Planned
Validation. Directional assertions below were checked empirically first
(session scratch script) rather than guessed -- see TASK-0007's Done
section for the raw numbers and the three-way focusing/specificity/
ballistic tradeoff they revealed (star/complete: high focusing+specificity,
low ballistic; path: the opposite), which is why `TestUnsupervisedScore`
below tests combination mechanics rather than asserting one topology
"wins" -- that comparison is genuinely multi-dimensional, not a bug.
"""
import numpy as np
import pytest

from allostery.hamiltonians import laplacian
from allostery.select import (
    ballistic_exponent,
    focusing,
    source_specificity,
    unsupervised_score,
)


def _path_adjacency(n: int) -> np.ndarray:
    A = np.zeros((n, n))
    for i in range(n - 1):
        A[i, i + 1] = A[i + 1, i] = 1.0
    return A


def _star_adjacency(n: int) -> np.ndarray:
    A = np.zeros((n, n))
    for i in range(1, n):
        A[0, i] = A[i, 0] = 1.0
    return A


def _complete_adjacency(n: int) -> np.ndarray:
    return np.ones((n, n)) - np.eye(n)


N = 10
H_PATH = laplacian(_path_adjacency(N))
H_STAR = laplacian(_star_adjacency(N))
H_COMPLETE = laplacian(_complete_adjacency(N))


class TestFocusing:
    def test_fully_localized_is_near_one(self):
        P = np.zeros(N)
        P[0] = 1.0
        assert focusing(P) == pytest.approx(1.0, abs=1e-9)

    def test_uniform_is_near_one_over_n(self):
        P = np.ones(N) / N
        assert focusing(P) == pytest.approx(1.0 / N, abs=1e-9)

    def test_complete_and_star_more_focused_than_path(self):
        """CTQW on a highly symmetric graph (star/complete) stays
        persistently peaked at the source; on a path it spreads out over
        the time average -- confirmed empirically before asserting here."""
        from allostery.propagators import time_averaged_ctqw

        f_path = focusing(time_averaged_ctqw(H_PATH, 10.0, source=0))
        f_star = focusing(time_averaged_ctqw(H_STAR, 10.0, source=0))
        f_complete = focusing(time_averaged_ctqw(H_COMPLETE, 10.0, source=0))
        assert f_star > f_path
        assert f_complete > f_path


class TestSourceSpecificity:
    def test_path_endpoint_more_specific_than_midpoint(self):
        """A path's endpoint is a structurally distinguished position;
        a midpoint's walk looks more "typical" of other seeds' walks."""
        end = source_specificity(H_PATH, 0, t_max=10.0, n_alt=9)
        mid = source_specificity(H_PATH, 5, t_max=10.0, n_alt=9)
        assert end > mid

    def test_symmetric_graphs_more_specific_than_path(self):
        path = source_specificity(H_PATH, 0, t_max=10.0, n_alt=9)
        star = source_specificity(H_STAR, 0, t_max=10.0, n_alt=9)
        complete = source_specificity(H_COMPLETE, 0, t_max=10.0, n_alt=9)
        assert star > path
        assert complete > path

    def test_deterministic_with_default_rng(self):
        a = source_specificity(H_PATH, 0, t_max=10.0, n_alt=5)
        b = source_specificity(H_PATH, 0, t_max=10.0, n_alt=5)
        assert a == b

    def test_no_other_nodes_returns_nan(self):
        H1 = np.zeros((1, 1))
        assert np.isnan(source_specificity(H1, 0, t_max=10.0))


class TestBallisticExponent:
    def test_path_more_ballistic_than_star_or_complete(self):
        """A path supports genuine coherent spreading (higher exponent);
        star/complete saturate to their maximum reachable spread almost
        immediately, giving a near-zero or negative log-log slope."""
        path = ballistic_exponent(H_PATH, 0)
        star = ballistic_exponent(H_STAR, 0)
        complete = ballistic_exponent(H_COMPLETE, 0)
        assert path > star
        assert path > complete

    def test_path_endpoint_more_ballistic_than_midpoint(self):
        end = ballistic_exponent(H_PATH, 0)
        mid = ballistic_exponent(H_PATH, 5)
        assert end > mid

    def test_disconnected_component_excluded_not_infinite(self):
        # two disjoint edges: 0-1 and 2-3; source=0 can't reach 2 or 3.
        A = np.zeros((4, 4))
        A[0, 1] = A[1, 0] = 1.0
        A[2, 3] = A[3, 2] = 1.0
        H = laplacian(A)
        # must not raise/produce inf or nan despite an unreachable component
        result = ballistic_exponent(H, 0)
        assert np.isfinite(result)


class TestUnsupervisedScore:
    def test_returns_one_score_per_candidate(self):
        candidates = [
            {"H": H_PATH, "source": 0, "t": 10.0},
            {"H": H_STAR, "source": 0, "t": 10.0},
            {"H": H_COMPLETE, "source": 0, "t": 10.0},
        ]
        scores = unsupervised_score(candidates)
        assert scores.shape == (3,)

    def test_is_zero_mean_zscore_combination(self):
        candidates = [
            {"H": H_PATH, "source": 0, "t": 10.0},
            {"H": H_STAR, "source": 0, "t": 10.0},
            {"H": H_COMPLETE, "source": 0, "t": 10.0},
        ]
        scores = unsupervised_score(candidates)
        assert scores.mean() == pytest.approx(0.0, abs=1e-9)

    def test_identical_candidates_score_identically(self):
        candidates = [
            {"H": H_PATH, "source": 0, "t": 10.0},
            {"H": H_PATH, "source": 0, "t": 10.0},
        ]
        scores = unsupervised_score(candidates)
        assert scores[0] == pytest.approx(scores[1])

    def test_different_candidates_are_differentiated(self):
        candidates = [
            {"H": H_PATH, "source": 0, "t": 10.0},
            {"H": H_STAR, "source": 0, "t": 10.0},
        ]
        scores = unsupervised_score(candidates)
        assert scores[0] != pytest.approx(scores[1])
