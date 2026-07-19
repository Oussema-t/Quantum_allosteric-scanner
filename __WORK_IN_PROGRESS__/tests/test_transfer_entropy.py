"""TASK-0132 -- GNM-based transfer entropy classical baseline coverage."""
import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.potentials import _kirchhoff_eigh, _normalized_dcc  # noqa: E402
from allostery.transfer_entropy import (  # noqa: E402
    _gnm_lagged_covariance,
    gnm_relaxation_time,
    pairwise_transfer_entropy,
    transfer_entropy_source_score,
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


class TestGnmLaggedCovariance:
    def test_tau_zero_matches_normalized_dcc_up_to_normalization(self):
        """C(0) is the same Kirchhoff-pseudo-inverse covariance
        `_normalized_dcc` already computes (before its own row/col
        normalization) -- confirms this module's C(tau) reduces to the
        existing shared primitive at tau=0, not an independent
        re-derivation that happens to look similar."""
        _A, w, U, nz, winv = _kirchhoff_eigh(COORDS, cutoff=10.0)
        w_nz, U_nz = w[nz], U[:, nz]
        C0 = _gnm_lagged_covariance(w_nz, U_nz, 0.0)

        expected_cov = (U * winv) @ U.T
        np.testing.assert_allclose(C0, expected_cov, atol=1e-10)

        # And matches _normalized_dcc after the same row/col normalization.
        d = np.sqrt(np.clip(np.diag(C0), 1e-12, None))
        normalized = C0 / np.outer(d, d)
        np.testing.assert_allclose(normalized, _normalized_dcc(U, winv), atol=1e-10)

    def test_lagged_covariance_is_symmetric(self):
        """A real, load-bearing finding this module's own docstring
        states and depends on: for the pure (reversible) GNM Langevin
        process, C_ij(tau) == C_ji(tau) for ANY tau, not just tau=0 --
        provable directly (sum of symmetric rank-1 u_k @ u_k.T terms).
        If this ever failed it would mean the eigendecomposition itself
        is broken, not a subtle numerical issue."""
        _A, w, U, nz, _winv = _kirchhoff_eigh(COORDS, cutoff=10.0)
        w_nz, U_nz = w[nz], U[:, nz]
        for tau in (0.1, 1.0, 5.0):
            C = _gnm_lagged_covariance(w_nz, U_nz, tau)
            np.testing.assert_allclose(C, C.T, atol=1e-10)

    def test_covariance_decays_with_increasing_lag(self):
        """C_ii(tau) must be monotonically non-increasing in tau (each
        mode decays as exp(-lambda*tau), lambda > 0) -- a basic physical
        sanity check on the closed form before trusting anything built on
        top of it."""
        _A, w, U, nz, _winv = _kirchhoff_eigh(COORDS, cutoff=10.0)
        w_nz, U_nz = w[nz], U[:, nz]
        taus = [0.0, 0.5, 1.0, 2.0, 5.0]
        diag_over_tau = [np.diag(_gnm_lagged_covariance(w_nz, U_nz, t)) for t in taus]
        for k in range(len(taus) - 1):
            assert np.all(diag_over_tau[k] >= diag_over_tau[k + 1] - 1e-9)


class TestGnmRelaxationTime:
    def test_positive_and_finite_for_a_connected_structure(self):
        tau = gnm_relaxation_time(COORDS, cutoff=10.0)
        assert 0.0 < tau < np.inf

    def test_equals_inverse_of_smallest_nonzero_eigenvalue(self):
        _A, w, _U, nz, _winv = _kirchhoff_eigh(COORDS, cutoff=10.0)
        expected = 1.0 / w[nz].min()
        assert gnm_relaxation_time(COORDS, cutoff=10.0) == pytest.approx(expected)


class TestPairwiseTransferEntropy:
    def test_shape_and_zero_diagonal(self):
        T = pairwise_transfer_entropy(COORDS, cutoff=10.0)
        assert T.shape == (N, N)
        np.testing.assert_array_equal(np.diag(T), np.zeros(N))

    def test_non_negative(self):
        """T_{Y->X} = 0.5*ln(Sigma_X / Sigma_{X|Y}) with Sigma_{X|Y} <=
        Sigma_X always (conditioning cannot increase residual variance) --
        every entry must be >= 0, a direct mathematical guarantee of the
        closed form, not an empirical tendency."""
        T = pairwise_transfer_entropy(COORDS, cutoff=10.0)
        assert (T >= -1e-9).all()

    def test_asymmetric_despite_symmetric_cross_covariance(self):
        """The genuine subtlety this module's docstring works out: the
        lagged cross-covariance C_ij(tau) is symmetric (previous test
        class), yet T_{i->j} != T_{j->i} in general -- the directionality
        survives through each residue's own, generally different,
        self-prediction baseline. Verified directly, not assumed from the
        derivation alone."""
        T = pairwise_transfer_entropy(COORDS, cutoff=10.0)
        off_diag_diff = np.abs(T - T.T)
        assert off_diag_diff.max() > 1e-6, (
            "expected genuine directional asymmetry (T_{i->j} != T_{j->i}) "
            "somewhere in this heterogeneous synthetic structure"
        )

    def test_default_tau_matches_gnm_relaxation_time(self):
        T_default = pairwise_transfer_entropy(COORDS, cutoff=10.0, tau=None)
        tau = gnm_relaxation_time(COORDS, cutoff=10.0)
        T_explicit = pairwise_transfer_entropy(COORDS, cutoff=10.0, tau=tau)
        np.testing.assert_allclose(T_default, T_explicit)


class TestTransferEntropySourceScore:
    def test_shape(self):
        score = transfer_entropy_source_score(COORDS, cutoff=10.0)
        assert score.shape == (N,)

    def test_non_negative(self):
        score = transfer_entropy_source_score(COORDS, cutoff=10.0)
        assert (score >= -1e-9).all()

    def test_a_more_tightly_coupled_hub_scores_as_a_stronger_source(self):
        """Directionality sanity check using an asymmetric synthetic
        network (this task's own Planned Validation: a falsification
        gate before trusting the method on real data). Two 6-node
        cliques joined by a single weak bridge edge -- the clique with
        the STRONGER internal coupling has a shorter internal relaxation
        time (more tightly bound, "faster/more predictable" locally) and
        should be a net information SOURCE relative to the weaker,
        floppier clique."""
        from allostery.hamiltonians import laplacian

        n_a, n_b = 6, 6
        N_total = n_a + n_b
        W = np.zeros((N_total, N_total))

        def _clique(idxs, weight):
            for i in idxs:
                for j in idxs:
                    if i < j:
                        W[i, j] = W[j, i] = weight

        clique_a = list(range(0, n_a))          # strongly coupled
        clique_b = list(range(n_a, N_total))    # weakly coupled
        _clique(clique_a, weight=3.0)
        _clique(clique_b, weight=0.3)
        W[0, n_a] = W[n_a, 0] = 0.2  # single weak bridge edge

        L = laplacian(W, normalised=False)
        w, U = np.linalg.eigh(L)
        nz = w > 1e-9
        w_nz, U_nz = w[nz], U[:, nz]
        tau = 1.0 / w_nz.min()

        # This test builds a hand-made Laplacian directly (not via
        # `coords`/`cutoff`, which `pairwise_transfer_entropy`'s public
        # signature requires) -- exercises the same closed form against
        # this Laplacian's own eigendecomposition instead of going through
        # `_kirchhoff_eigh`'s coordinate-based contact-matrix construction.
        T = np.zeros((N_total, N_total))
        C0 = _gnm_lagged_covariance(w_nz, U_nz, 0.0)
        Ct = _gnm_lagged_covariance(w_nz, U_nz, tau)
        var0 = np.diag(C0)
        for i in range(N_total):
            sigma_x = var0[i] - Ct[i, i] ** 2 / var0[i]
            if sigma_x <= 1e-14:
                continue
            for j in range(N_total):
                if i == j:
                    continue
                pred_cov = np.array([[var0[i], C0[i, j]], [C0[i, j], var0[j]]])
                det = var0[i] * var0[j] - C0[i, j] ** 2
                if det <= 1e-14:
                    continue
                pred_inv = np.array([[var0[j], -C0[i, j]], [-C0[i, j], var0[i]]]) / det
                cross = np.array([Ct[i, i], Ct[i, j]])
                sigma_xy = min(var0[i] - cross @ pred_inv @ cross, sigma_x)
                if sigma_xy <= 1e-14:
                    continue
                T[i, j] = 0.5 * np.log(sigma_x / sigma_xy)

        outgoing = T.copy()
        np.fill_diagonal(outgoing, 0.0)
        score = outgoing.sum(axis=0) / (N_total - 1)

        assert score[clique_a].mean() > score[clique_b].mean(), (
            f"expected the tightly-coupled clique to score as a stronger "
            f"information source: A={score[clique_a].mean():.4f}, "
            f"B={score[clique_b].mean():.4f}"
        )
