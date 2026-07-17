"""Group B coverage tests — potentials.py diagonal terms.

Sections implemented
--------------------
T-013  Unit tests for V_B, V_T, V_R, V_C, V_M (CRIT-002 GAP-4).
"""
import numpy as np
import pytest

from allostery.potentials import (
    V_B, V_T, V_R, V_C, V_M,
    _gnm_msf, _kirchhoff_eigh, _normalized_dcc,
)


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
    """V_B: B-factor penalty, z-scored (TASK-0121): mean 0, std 1. High-B
    residues score positive (penalised), low-B residues score negative
    (mild reward) as a consequence of z-scoring, not a separate design
    choice."""

    def test_shape_and_diagonal(self):
        _assert_diagonal(V_B(BFACTORS), N)

    def test_zscored(self):
        d = np.diag(V_B(BFACTORS))
        assert abs(d.mean()) < 1e-9
        np.testing.assert_allclose(d.std(), 1.0, atol=1e-6)

    def test_higher_bfactor_scores_higher(self):
        """Monotonic in the raw B-factor ranking, same as the pre-fix
        b/mean(b) normalisation -- only the mean/scale changed."""
        d = np.diag(V_B(BFACTORS))
        order = np.argsort(BFACTORS)
        np.testing.assert_array_equal(np.argsort(d), order)

    def test_uniform_bfactors_normalise_to_zero(self):
        """Uniform input has zero variance; `_zscore`'s `+1e-9` epsilon
        guard against a zero std keeps this exactly zero rather than nan."""
        M = V_B(np.full(N, 42.0))
        np.testing.assert_allclose(np.diag(M), np.zeros(N), atol=1e-6)


class TestVT:
    """V_T: terminal-residue suppression, z-scored (TASK-0121). Termini
    (originally 1.0) score strictly higher than the core (originally 0.0)
    after z-scoring; mean 0 / std 1."""

    def test_shape_and_diagonal(self):
        _assert_diagonal(V_T(N, terminal_fraction=0.2), N)

    def test_zscored(self):
        d = np.diag(V_T(N, terminal_fraction=0.2))
        assert abs(d.mean()) < 1e-9
        np.testing.assert_allclose(d.std(), 1.0, atol=1e-6)

    def test_termini_score_higher_than_core(self):
        """terminal_fraction=0.2 on N=10 → n_term=2: indices 0,1,8,9 are the
        (positive-scoring) termini; the interior 6 residues are the
        (negative-scoring) core."""
        d = np.diag(V_T(N, terminal_fraction=0.2))
        termini = np.r_[d[:2], d[-2:]]
        core = d[2:-2]
        assert termini.min() > core.max()
        np.testing.assert_allclose(termini, termini[0])
        np.testing.assert_allclose(core, core[0])


class TestVR:
    """V_R: rigidity reward = -(z(degree) + z(clustering) - z(msf)),
    re-z-scored to mean 0 / std 1 (TASK-0121 -- the inner sum's own std was
    ~1.9 on real targets, not 1, since the three components are correlated)."""

    def test_shape_and_diagonal(self):
        _assert_diagonal(V_R(COORDS, cutoff=10.0), N)

    def test_zscored(self):
        d = np.diag(V_R(COORDS, cutoff=10.0))
        assert abs(d.mean()) < 1e-9
        np.testing.assert_allclose(d.std(), 1.0, atol=1e-6)

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
    """V_C: covariance-centrality reward via GNM DCC, z-scored (TASK-0121;
    was max-normalised to [-1, 0], std ~= 0.06 on real targets -- a ~30x
    scale mismatch against V_R that made lam_C unreachable)."""

    def test_shape_and_diagonal(self):
        _assert_diagonal(V_C(COORDS, cutoff=10.0), N)

    def test_zscored(self):
        d = np.diag(V_C(COORDS, cutoff=10.0))
        assert abs(d.mean()) < 1e-9
        np.testing.assert_allclose(d.std(), 1.0, atol=1e-6)

    def test_high_centrality_still_rewarded_most_negative(self):
        """Sign convention preserved: higher DCC centrality -> more negative
        score, same ranking direction as the pre-fix -centrality_norm."""
        d = np.diag(V_C(COORDS, cutoff=10.0))
        assert d.argmin() != d.argmax()  # non-degenerate on this fixture


class TestVM:
    """V_M: low-mode participation reward, z-scored (TASK-0121; was
    max-normalised to [-1, 0], std ~= 0.06 on real targets -- a ~30x scale
    mismatch against V_R that made lam_M unreachable)."""

    def test_shape_and_diagonal(self):
        _assert_diagonal(V_M(COORDS, cutoff=10.0, n_modes=3), N)

    def test_zscored(self):
        d = np.diag(V_M(COORDS, cutoff=10.0, n_modes=3))
        assert abs(d.mean()) < 1e-9
        np.testing.assert_allclose(d.std(), 1.0, atol=1e-6)


# ---------------------------------------------------------------------------
# _kirchhoff_eigh / _normalized_dcc -- shared binary-Kirchhoff pseudo-inverse
# helper (TASK-0066), deduplicating _gnm_msf/V_C/V_M's previously-independent
# re-derivations of the same eigendecomposition.
# ---------------------------------------------------------------------------

def _reference_kirchhoff_eigh(coords, cutoff):
    """Independent re-derivation of the pre-TASK-0066 inline formula
    (matches V_C's own old inline block) -- kept deliberately separate
    from _kirchhoff_eigh's own implementation."""
    from allostery.hamiltonians import contact_matrix, laplacian

    A = contact_matrix(coords, cutoff=cutoff, weight="binary")
    K = laplacian(A)
    w, U = np.linalg.eigh(K)
    nz = w > 1e-9
    winv = np.where(nz, 1.0 / np.where(nz, w, 1.0), 0.0)
    return A, w, U, nz, winv


class TestKirchhoffEigh:
    def test_matches_an_independently_rederived_reference(self):
        A, w, U, nz, winv = _kirchhoff_eigh(COORDS, cutoff=10.0)
        A_ref, w_ref, U_ref, nz_ref, winv_ref = _reference_kirchhoff_eigh(COORDS, cutoff=10.0)

        np.testing.assert_array_equal(A, A_ref)
        np.testing.assert_allclose(w, w_ref)
        np.testing.assert_array_equal(nz, nz_ref)
        np.testing.assert_allclose(winv, winv_ref)

    def test_matches_h8_gnm_plus_eigh(self):
        """V_M's pre-TASK-0066 path went through hamiltonians.H8_gnm
        directly -- confirm the shared helper's K construction is
        mathematically identical, not just superficially similar."""
        from allostery.hamiltonians import H8_gnm

        _A, w, U, _nz, _winv = _kirchhoff_eigh(COORDS, cutoff=10.0)
        L = H8_gnm(COORDS, cutoff=10.0)
        w_ref, U_ref = np.linalg.eigh(L)

        np.testing.assert_allclose(w, w_ref)

    def test_smallest_eigenvalue_is_the_zero_mode(self):
        _A, w, _U, _nz, _winv = _kirchhoff_eigh(COORDS, cutoff=10.0)
        assert np.isclose(w.min(), 0.0, atol=1e-8)


class TestNormalizedDcc:
    def test_matches_an_independently_rederived_reference(self):
        _A, _w, U, _nz, winv = _kirchhoff_eigh(COORDS, cutoff=10.0)
        nDCC = _normalized_dcc(U, winv)

        Cov_ref = (U * winv) @ U.T
        d_ref = np.sqrt(np.clip(np.diag(Cov_ref), 1e-12, None))
        nDCC_ref = Cov_ref / np.outer(d_ref, d_ref)

        np.testing.assert_allclose(nDCC, nDCC_ref)

    def test_diagonal_is_self_correlation_one_not_zeroed(self):
        _A, _w, U, _nz, winv = _kirchhoff_eigh(COORDS, cutoff=10.0)
        nDCC = _normalized_dcc(U, winv)
        np.testing.assert_allclose(np.diag(nDCC), 1.0, atol=1e-8)


class TestGnmMsf:
    def test_matches_full_covariance_diagonal(self):
        _A, _w, U, _nz, winv = _kirchhoff_eigh(COORDS, cutoff=10.0)
        Cov = (U * winv) @ U.T
        np.testing.assert_allclose(_gnm_msf(COORDS, cutoff=10.0), np.diag(Cov))
