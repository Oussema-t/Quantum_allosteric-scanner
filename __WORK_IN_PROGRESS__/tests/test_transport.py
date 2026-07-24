"""TASK-0145 coverage -- `allostery.transport`'s two new observables:
classical effective resistance/conductance (`effective_resistance_from_
source`) and Landauer-Buttiker quantum transmission
(`transmission_from_source`).
"""
import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.hamiltonians import laplacian  # noqa: E402
from allostery.transport import (  # noqa: E402
    effective_resistance_from_source,
    transmission_from_source,
)


def _path_laplacian(n: int) -> np.ndarray:
    W = np.zeros((n, n))
    for i in range(n - 1):
        W[i, i + 1] = W[i + 1, i] = 1.0
    return laplacian(W, normalised=False)


def _random_graph_laplacian(n: int, n_edges: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    W = np.zeros((n, n))
    edges: set = set()
    while len(edges) < n_edges:
        i, j = rng.integers(0, n, size=2)
        if i != j:
            edges.add((min(int(i), int(j)), max(int(i), int(j))))
    for i, j in edges:
        W[i, j] = W[j, i] = 1.0
    return laplacian(W, normalised=False)


def _random_symmetric_H(n: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    A = rng.normal(size=(n, n))
    return (A + A.T) / 2


class TestEffectiveResistance:
    def test_matches_known_path_graph_series_resistance(self):
        """A textbook result: unit-weight resistors in series on a path
        graph give `R_eff(0, k) = k` exactly -- the standard sanity check
        for any effective-resistance implementation, checked directly
        rather than trusted from the derivation alone."""
        n = 8
        L = _path_laplacian(n)
        conductance = effective_resistance_from_source(L, 0, w_short=1e4)
        r_eff = 1.0 / conductance
        expected = np.arange(n, dtype=float)
        # w_short=1e4 leaves a ~1/w_short residual on every value, including
        # the source's own (otherwise-zero) self-resistance.
        np.testing.assert_allclose(r_eff, expected, atol=2e-4)

    def test_converges_as_w_short_increases(self):
        """Excludes the source's own entry: `R_eff(supernode, source)`
        goes to `1/w_short` by construction (the shorting edge itself
        dominates), so `conductance[source]` scales *linearly* with
        `w_short` and never converges -- expected, not a bug (the same
        degenerate `i==j` edge case the standard `R_eff` formula always
        has). Every other entry (`j != source`) converges as `w_short`
        grows, which is the actual claim under test."""
        L = _random_graph_laplacian(10, 15, seed=1)
        others = np.array([i for i in range(10) if i != 0])
        cond_1e3 = effective_resistance_from_source(L, 0, w_short=1e3)[others]
        cond_1e5 = effective_resistance_from_source(L, 0, w_short=1e5)[others]
        cond_1e7 = effective_resistance_from_source(L, 0, w_short=1e7)[others]
        np.testing.assert_allclose(cond_1e3, cond_1e5, rtol=1e-2)
        np.testing.assert_allclose(cond_1e5, cond_1e7, rtol=1e-3)

    def test_multi_index_source_is_a_parallel_combination(self):
        """Shorting two adjacent path-graph nodes together (0 and 1) into
        one supernode must give a *lower* resistance to every other node
        than seeding from node 0 alone (parallel paths never increase
        resistance) -- checked directly on a simple, hand-verifiable
        case, not assumed from the supernode construction's own docstring
        claim."""
        n = 8
        L = _path_laplacian(n)
        r_eff_single = 1.0 / effective_resistance_from_source(L, 0, w_short=1e5)
        r_eff_multi = 1.0 / effective_resistance_from_source(L, [0, 1], w_short=1e5)
        # node 7 (farthest from the source pair) must see a shorter (or
        # equal) effective resistance once node 1 is also shorted in.
        assert r_eff_multi[7] <= r_eff_single[7] + 1e-6

    def test_shape_finite_non_negative(self):
        L = _random_graph_laplacian(12, 20, seed=2)
        cond = effective_resistance_from_source(L, [1, 3], w_short=1e4)
        assert cond.shape == (12,)
        assert np.all(np.isfinite(cond))
        assert np.all(cond >= 0)

    def test_residue_relabeling_is_gauge(self):
        """INVARIANCE_PROTOCOL.md Tier 0: permuting `L`'s indices +
        `source` consistently must leave every score unchanged to
        `atol=1e-6` (the `w_short=1e4` construction's own residual sets
        the achievable precision here, looser than a pure-linear-algebra
        `1e-9` GAUGE check elsewhere in this project)."""
        L = _random_graph_laplacian(12, 20, seed=3)
        source = 4
        before = effective_resistance_from_source(L, source, w_short=1e4)

        rng = np.random.default_rng(4)
        perm = rng.permutation(12)
        L_perm = L[np.ix_(perm, perm)]
        new_source = int(np.where(perm == source)[0][0])
        after = effective_resistance_from_source(L_perm, new_source, w_short=1e4)

        # after[k] should equal before[original index of perm[k]]
        expected = before[perm]
        np.testing.assert_allclose(after, expected, atol=1e-6)


class TestTransmission:
    def _brute_force_T(self, H, source, j, E, gamma, eta):
        N = H.shape[0]
        idx = np.atleast_1d(source)
        GammaL = np.zeros(N)
        GammaL[idx] = gamma
        GammaR = np.zeros(N)
        GammaR[j] = gamma
        M = (E + 1j * eta) * np.eye(N) - H.astype(complex)
        M[np.arange(N), np.arange(N)] += 1j * (GammaL + GammaR) / 2.0
        G = np.linalg.inv(M)
        T = np.trace(np.diag(GammaL) @ G @ np.diag(GammaR) @ G.conj().T)
        return T

    def test_closed_form_matches_brute_force_per_candidate_inversion(self):
        """The Sherman-Morrison-derived closed form, checked directly
        against the textbook `Tr[Gamma_L G Gamma_R G^dagger]` definition
        evaluated by a separate, independent, brute-force re-inversion
        per candidate -- not trusted from the algebra alone."""
        H = _random_symmetric_H(10, seed=5)
        source = np.array([1, 4])
        E, gamma, eta = 0.3, 0.7, 1e-4
        brute = np.array([
            self._brute_force_T(H, source, j, E, gamma, eta).real for j in range(10)
        ])
        brute_imag = np.array([
            self._brute_force_T(H, source, j, E, gamma, eta).imag for j in range(10)
        ])
        closed = transmission_from_source(H, source, E=E, gamma_lead=gamma, eta_reg=eta)
        np.testing.assert_allclose(closed, brute, atol=1e-10)
        np.testing.assert_allclose(brute_imag, 0.0, atol=1e-10)

    def test_output_is_real_and_non_negative(self):
        H = _random_symmetric_H(9, seed=6)
        T = transmission_from_source(H, [0, 2], E=0.1)
        assert T.shape == (9,)
        assert np.all(np.isfinite(T))
        assert np.all(T >= -1e-10)

    def test_zero_coupling_gives_zero_transmission(self):
        H = _random_symmetric_H(8, seed=7)
        T = transmission_from_source(H, 0, E=0.0, gamma_lead=0.0)
        np.testing.assert_allclose(T, 0.0, atol=1e-12)

    def test_default_gamma_and_eta_scale_with_bandwidth(self):
        H = _random_symmetric_H(8, seed=8)
        w = np.linalg.eigvalsh(H)
        bandwidth = float(w[-1] - w[0])
        T_default = transmission_from_source(H, 0, E=0.0)
        T_explicit = transmission_from_source(
            H, 0, E=0.0, gamma_lead=0.1 * bandwidth, eta_reg=1e-6 * bandwidth,
        )
        np.testing.assert_allclose(T_default, T_explicit, rtol=1e-10)

    def test_residue_relabeling_is_gauge(self):
        H = _random_symmetric_H(10, seed=9)
        source = 3
        before = transmission_from_source(H, source, E=0.2)

        rng = np.random.default_rng(10)
        perm = rng.permutation(10)
        H_perm = H[np.ix_(perm, perm)]
        new_source = int(np.where(perm == source)[0][0])
        after = transmission_from_source(H_perm, new_source, E=0.2)

        expected = before[perm]
        np.testing.assert_allclose(after, expected, atol=1e-9)
