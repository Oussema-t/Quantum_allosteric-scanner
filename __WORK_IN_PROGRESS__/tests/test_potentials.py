"""Group B coverage tests — potentials.py diagonal terms.

Sections implemented
--------------------
T-013  Unit tests for V_B, V_T, V_R, V_C, V_M (CRIT-002 GAP-4).
"""
import numpy as np
import pytest

from allostery.potentials import V_B, V_T, V_R, V_C, V_M


def _helix_coords(n: int) -> np.ndarray:
    theta = np.arange(n) * (100.0 * np.pi / 180.0)
    return np.column_stack([
        2.3 * np.cos(theta),
        2.3 * np.sin(theta),
        1.5 * np.arange(n, dtype=float),
    ])


N = 10
COORDS = _helix_coords(N)
BFACTORS = np.array([30.0, 25.0, 18.0, 22.0, 30.0, 15.0, 40.0, 20.0, 10.0, 35.0])


def _assert_diagonal(M: np.ndarray, n: int):
    assert M.shape == (n, n)
    off_diag = M - np.diag(np.diag(M))
    assert np.allclose(off_diag, 0.0), "matrix has non-zero off-diagonal entries"


class TestVB:
    """V_B: B-factor penalty. Non-negative by construction (b_norm = b/mean(b))."""

    def test_shape_and_diagonal(self):
        _assert_diagonal(V_B(BFACTORS), N)

    def test_non_negative(self):
        assert (np.diag(V_B(BFACTORS)) >= 0).all()

    def test_uniform_bfactors_normalise_to_one(self):
        M = V_B(np.full(N, 42.0))
        np.testing.assert_allclose(np.diag(M), np.ones(N), atol=1e-6)


class TestVT:
    """V_T: terminal-residue suppression. 1.0 on termini, 0.0 elsewhere."""

    def test_shape_and_diagonal(self):
        _assert_diagonal(V_T(N, terminal_fraction=0.2), N)

    def test_non_negative(self):
        assert (np.diag(V_T(N, terminal_fraction=0.2)) >= 0).all()

    def test_zero_outside_terminal_residues(self):
        """terminal_fraction=0.2 on N=10 → n_term=2: only indices 0,1,8,9 are
        penalised; the interior 6 residues must be exactly zero."""
        d = np.diag(V_T(N, terminal_fraction=0.2))
        np.testing.assert_allclose(d[:2], [1.0, 1.0])
        np.testing.assert_allclose(d[-2:], [1.0, 1.0])
        np.testing.assert_allclose(d[2:-2], np.zeros(N - 4))


class TestVR:
    """V_R: rigidity reward = -(z(degree) + z(clustering) - z(msf)).

    Unlike V_B/V_T, this is a signed reward/penalty term (z-scores are centered
    at zero), not a strictly non-negative penalty.
    """

    def test_shape_and_diagonal(self):
        _assert_diagonal(V_R(COORDS, cutoff=10.0), N)

    def test_mixed_sign(self):
        d = np.diag(V_R(COORDS, cutoff=10.0))
        assert d.min() < 0 < d.max(), (
            "V_R is a z-scored reward/penalty and must take both signs on a "
            "heterogeneous chain (termini vs. buried core)"
        )

    def test_termini_score_worse_than_core(self):
        """Chain termini (low degree, low clustering, high MSF) must score
        higher (worse / less rewarded) than the buried core."""
        d = np.diag(V_R(COORDS, cutoff=10.0))
        assert d[0] > d[N // 2]
        assert d[-1] > d[N // 2]


class TestVC:
    """V_C: covariance-centrality reward via GNM DCC. Non-positive by
    construction (returns -centrality_norm, centrality_norm in [0, 1])."""

    def test_shape_and_diagonal(self):
        _assert_diagonal(V_C(COORDS, cutoff=10.0), N)

    def test_non_positive_and_bounded(self):
        d = np.diag(V_C(COORDS, cutoff=10.0))
        assert (d <= 1e-12).all()
        assert (d >= -1.0 - 1e-9).all()


class TestVM:
    """V_M: low-mode participation reward. Non-positive by construction
    (returns -part_norm, part_norm in [0, 1])."""

    def test_shape_and_diagonal(self):
        _assert_diagonal(V_M(COORDS, cutoff=10.0, n_modes=3), N)

    def test_non_positive_and_bounded(self):
        d = np.diag(V_M(COORDS, cutoff=10.0, n_modes=3))
        assert (d <= 1e-12).all()
        assert (d >= -1.0 - 1e-9).all()
