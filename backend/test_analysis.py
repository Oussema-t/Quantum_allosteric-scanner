"""Unit tests for backend/analysis.py's shared Kirchhoff/DCC helper
(TASK-0066) -- _kirchhoff_eigh + _normalized_dcc, deduplicating gnm_context/
_dcc/_abs_coupling's previously-independent re-derivations of the same
binary-Kirchhoff-pseudo-inverse math.
"""
import numpy as np
import pytest

from backend.analysis import (
    _abs_coupling,
    _dcc,
    _kirchhoff_eigh,
    _normalized_dcc,
    _z,
    V_covariance,
    connectivity_change,
    gnm_context,
    site_potentials,
)


def _helix_coords(n: int) -> np.ndarray:
    theta = np.arange(n) * (100.0 * np.pi / 180.0)
    return np.column_stack([
        2.3 * np.cos(theta),
        2.3 * np.sin(theta),
        1.5 * np.arange(n, dtype=float),
    ])


N = 12
COORDS = _helix_coords(N)
CUTOFF = 8.0


def _reference_kirchhoff_eigh(coords, cutoff):
    """Independent re-derivation of the pre-TASK-0066 inline formula --
    kept deliberately separate from _kirchhoff_eigh's own implementation
    so this test doesn't just check the function against itself."""
    from scipy.spatial.distance import cdist

    D = cdist(coords, coords)
    A = ((D < cutoff) & (D > 1e-8)).astype(float)
    deg = A.sum(1)
    K = np.diag(deg) - A
    w, U = np.linalg.eigh(K)
    nz = w > 1e-9
    winv = np.zeros_like(w)
    winv[nz] = 1.0 / w[nz]
    return A, deg, w, U, nz, winv


class TestKirchhoffEigh:
    def test_matches_an_independently_rederived_reference(self):
        A, deg, w, U, nz, winv = _kirchhoff_eigh(COORDS, CUTOFF)
        A_ref, deg_ref, w_ref, U_ref, nz_ref, winv_ref = _reference_kirchhoff_eigh(COORDS, CUTOFF)

        np.testing.assert_array_equal(A, A_ref)
        np.testing.assert_array_equal(deg, deg_ref)
        np.testing.assert_allclose(w, w_ref)
        np.testing.assert_array_equal(nz, nz_ref)
        np.testing.assert_allclose(winv, winv_ref)
        # eigenvectors of a degenerate spectrum aren't unique up to sign/basis
        # in general, but the *pseudo-inverse quantities built from them*
        # (winv, and downstream Cov = (U*winv)@U.T) are -- checked below via
        # _normalized_dcc rather than comparing U directly.

    def test_k_is_symmetric_and_rows_sum_to_zero(self):
        A, deg, w, U, nz, winv = _kirchhoff_eigh(COORDS, CUTOFF)
        K = np.diag(deg) - A
        np.testing.assert_allclose(K, K.T)
        np.testing.assert_allclose(K.sum(axis=1), 0.0, atol=1e-10)

    def test_smallest_eigenvalue_is_the_zero_mode(self):
        _A, _deg, w, _U, _nz, _winv = _kirchhoff_eigh(COORDS, CUTOFF)
        assert np.isclose(w.min(), 0.0, atol=1e-8)


class TestNormalizedDcc:
    def test_matches_an_independently_rederived_reference(self):
        _A, _deg, _w, U, _nz, winv = _kirchhoff_eigh(COORDS, CUTOFF)
        nDCC = _normalized_dcc(U, winv)

        Cov_ref = (U * winv) @ U.T
        d_ref = np.sqrt(np.clip(np.diag(Cov_ref), 1e-12, None))
        nDCC_ref = Cov_ref / np.outer(d_ref, d_ref)

        np.testing.assert_allclose(nDCC, nDCC_ref)

    def test_diagonal_is_self_correlation_one_not_zeroed(self):
        _A, _deg, _w, U, _nz, winv = _kirchhoff_eigh(COORDS, CUTOFF)
        nDCC = _normalized_dcc(U, winv)
        np.testing.assert_allclose(np.diag(nDCC), 1.0, atol=1e-8)

    def test_is_symmetric(self):
        _A, _deg, _w, U, _nz, winv = _kirchhoff_eigh(COORDS, CUTOFF)
        nDCC = _normalized_dcc(U, winv)
        np.testing.assert_allclose(nDCC, nDCC.T)


class TestDcc:
    def test_matches_an_independently_rederived_reference(self):
        """Acceptance Scenario: the shared helper's raw DCC matrix must be
        float-tolerance identical to what the pre-refactor inline
        computation produced."""
        from scipy.spatial.distance import cdist

        D = cdist(COORDS, COORDS)
        A = ((D < CUTOFF) & (D > 1e-8)).astype(float)
        K = np.diag(A.sum(1)) - A
        w, U = np.linalg.eigh(K)
        nz = w > 1e-9
        winv = np.zeros_like(w)
        winv[nz] = 1.0 / w[nz]
        Cov = (U * winv) @ U.T
        s = np.sqrt(np.clip(np.diag(Cov), 1e-12, None))
        expected = Cov / np.outer(s, s)

        np.testing.assert_allclose(_dcc(COORDS, CUTOFF), expected)


class TestGnmContext:
    def test_returns_expected_keys_and_shapes(self):
        c = gnm_context(COORDS, np.full(N, 20.0), cutoff=CUTOFF)
        assert set(c) == {"N", "A", "deg", "U", "nz", "winv", "msf", "clust", "beta", "eigs"}
        assert c["N"] == N
        assert c["A"].shape == (N, N)
        assert c["msf"].shape == (N,)

    def test_msf_matches_the_full_covariance_diagonal(self):
        """gnm_context's msf uses the cheap ((U**2)*winv).sum(1) shortcut,
        mathematically identical to diag((U*winv)@U.T) -- confirmed here,
        not just asserted in a comment."""
        c = gnm_context(COORDS, np.full(N, 20.0), cutoff=CUTOFF)
        Cov = (c["U"] * c["winv"]) @ c["U"].T
        np.testing.assert_allclose(c["msf"], np.diag(Cov))


class TestAbsCouplingMatchesVCovariance:
    def test_abs_coupling_is_the_pre_zscore_form_of_v_covariance(self):
        c = gnm_context(COORDS, np.full(N, 20.0), cutoff=CUTOFF)
        np.testing.assert_allclose(_z(_abs_coupling(c)), V_covariance(c))


# ---------------------------------------------------------------------------
# Real-target regression pin (KRAS_G12C) -- skipped where network is
# unavailable. Values pinned from a manual pre/post-refactor diff
# (2026-07-12: byte-identical before/after this task's dedup, via
# git stash / git stash pop on backend/analysis.py), not guessed.
# ---------------------------------------------------------------------------

def test_kras_g12c_real_target_site_potentials_and_connectivity_change_pin():
    from backend.data_layer import load_structure

    try:
        apo = load_structure("4OBE", "A")
    except Exception as exc:
        pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")
    if apo is None:
        pytest.skip("real-structure fetch unavailable in this environment (load_structure returned None)")

    sp = site_potentials(apo["coords"], apo["bfac"], apo["resnums"], cutoff=8.0)
    term_sums = {k: round(float(sum(v)), 6) for k, v in sp["terms"].items()}
    assert term_sums == {
        "V_B": -0.001, "V_T": 0.0001, "V_R": 0.0004, "V_C": -0.0002, "V_M": 0.0001,
    }

    cc = connectivity_change("4OBE", "A", "6OIM", "A", cutoff=8.0)
    assert cc["summary"] == {
        "n_shared": 166,
        "ddm_max": 8.84,
        "contacts_formed": 24,
        "contacts_broken": 26,
        "mean_abs_ddcc": 0.01,
        "most_reorganized": [63, 64, 60, 62, 68],
    }
    assert cc["ddcc"][0][:5] == pytest.approx([0.0, 0.029, 0.005, 0.002, -0.001], abs=1e-3)
