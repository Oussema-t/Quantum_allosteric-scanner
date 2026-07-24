"""TASK-0148 coverage -- `allostery.entanglement`'s single-particle
Peschel entanglement-entropy observable.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.entanglement import (  # noqa: E402
    _ctqw_amplitude,
    entanglement_entropy_closed_form,
    entanglement_entropy_mixture,
    hop_radius_neighborhoods,
    natural_coherent_time,
    peschel_entropy,
)


def _random_symmetric_H(n: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    A = rng.normal(size=(n, n))
    return (A + A.T) / 2


class TestPeschelEntropy:
    def test_zero_entropy_when_fully_localized_outside_region(self):
        """A pure state entirely outside region A: P_A=0, S_A=0 exactly."""
        N = 6
        psi = np.zeros(N, dtype=complex)
        psi[4] = 1.0
        region = np.array([0, 1, 2])
        assert peschel_entropy(psi, region) == pytest.approx(0.0, abs=1e-12)

    def test_zero_entropy_when_fully_localized_inside_region(self):
        N = 6
        psi = np.zeros(N, dtype=complex)
        psi[1] = 1.0
        region = np.array([0, 1, 2])
        assert peschel_entropy(psi, region) == pytest.approx(0.0, abs=1e-12)

    def test_maximal_entropy_at_half_occupation(self):
        """P_A=0.5 gives the binary-entropy maximum, ln(2)."""
        N = 4
        psi = np.zeros(N, dtype=complex)
        psi[0] = 1.0 / np.sqrt(2)
        psi[2] = 1.0 / np.sqrt(2)
        region = np.array([0, 1])  # P_A = |psi[0]|^2 = 0.5
        assert peschel_entropy(psi, region) == pytest.approx(np.log(2), abs=1e-10)

    def test_matches_closed_form_for_arbitrary_pure_state(self):
        """The central mathematical claim of this module: for a genuine
        pure single-particle state, Peschel's general matrix
        diagonalization exactly reduces to the binary entropy of the
        region's total occupation probability -- verified directly, not
        assumed from the derivation."""
        rng = np.random.default_rng(2)
        N = 15
        psi = rng.normal(size=N) + 1j * rng.normal(size=N)
        psi /= np.linalg.norm(psi)
        occ = np.abs(psi) ** 2

        for _ in range(5):
            region = rng.choice(N, size=rng.integers(2, 8), replace=False)
            general = peschel_entropy(psi, region)
            closed = entanglement_entropy_closed_form(occ, region)
            assert general == pytest.approx(closed, abs=1e-10)

    def test_correlation_matrix_restricted_to_region_is_exactly_rank_one(self):
        """The structural fact the closed form relies on: C_A for a pure
        state is `psi_A (x) conj(psi_A)`, an outer product -- exactly one
        nonzero eigenvalue, checked directly on the matrix itself, not
        inferred from the entropy value alone."""
        rng = np.random.default_rng(3)
        N = 10
        psi = rng.normal(size=N) + 1j * rng.normal(size=N)
        region = np.array([1, 2, 3, 4, 5])
        psi_A = psi[region]
        C_A = np.outer(np.conj(psi_A), psi_A)
        eigvals = np.linalg.eigvalsh(C_A)
        nonzero = eigvals[np.abs(eigvals) > 1e-9]
        assert len(nonzero) == 1
        assert nonzero[0] == pytest.approx(np.sum(np.abs(psi_A) ** 2), abs=1e-10)


class TestEntanglementEntropyMixture:
    def test_single_source_matches_peschel_entropy_directly(self):
        """k=1 mixture must reduce exactly to a direct Peschel calculation
        on that one source's own coherent amplitude."""
        H = _random_symmetric_H(12, seed=4)
        t = 3.7
        source = 2
        region = np.array([0, 1, 2, 3])

        w, v = np.linalg.eigh(H)
        psi0 = _ctqw_amplitude(w, v, t, source)
        direct = peschel_entropy(psi0, region)
        via_mixture = entanglement_entropy_mixture(H, [source], [region], t)[0]
        assert via_mixture == pytest.approx(direct, abs=1e-10)

    def test_single_source_matches_closed_form(self):
        H = _random_symmetric_H(10, seed=5)
        t = 2.1
        source = 3
        region = np.array([0, 1, 4])

        w, v = np.linalg.eigh(H)
        psi0 = _ctqw_amplitude(w, v, t, source)
        occ0 = np.abs(psi0) ** 2
        closed = entanglement_entropy_closed_form(occ0, region)
        via_mixture = entanglement_entropy_mixture(H, [source], [region], t)[0]
        assert via_mixture == pytest.approx(closed, abs=1e-10)

    def test_multi_source_matches_manual_mixture_construction(self):
        """k=2 mixture, checked against an independent, manually-built
        correlation matrix -- not just trusted from the module's own
        internal consistency."""
        H = _random_symmetric_H(12, seed=6)
        t = 1.9
        sources = np.array([2, 5])
        region = np.array([0, 1, 2, 3])

        w, v = np.linalg.eigh(H)
        psis = np.array([_ctqw_amplitude(w, v, t, int(s)) for s in sources])
        psi_A = psis[:, region]
        C_A = (psi_A.conj().T @ psi_A) / len(sources)
        eigvals = np.clip(np.linalg.eigvalsh(C_A).real, 0.0, 1.0)
        mask = (eigvals > 1e-14) & (eigvals < 1 - 1e-14)
        nu = eigvals[mask]
        manual = float(-np.sum(nu * np.log(nu) + (1 - nu) * np.log(1 - nu)))

        result = entanglement_entropy_mixture(H, sources, [region], t)[0]
        assert result == pytest.approx(manual, abs=1e-10)

    def test_multi_source_correlation_matrix_can_exceed_rank_one(self):
        """Distinct from the single-source case: an incoherent mixture's
        correlation matrix restricted to a region is generically rank>1
        -- checked directly, confirming the closed form genuinely does
        NOT apply here (not merely "not used", actually mathematically
        different)."""
        H = _random_symmetric_H(14, seed=7)
        t = 2.5
        sources = np.array([1, 6, 9])
        region = np.array([0, 1, 2, 3, 4, 5])

        w, v = np.linalg.eigh(H)
        psis = np.array([_ctqw_amplitude(w, v, t, int(s)) for s in sources])
        psi_A = psis[:, region]
        C_A = (psi_A.conj().T @ psi_A) / len(sources)
        eigvals = np.linalg.eigvalsh(C_A)
        nonzero = eigvals[np.abs(eigvals) > 1e-9]
        assert len(nonzero) > 1

    def test_shape_finite_non_negative(self):
        H = _random_symmetric_H(10, seed=8)
        t = natural_coherent_time(H)
        regions = [np.array([0, 1]), np.array([2, 3, 4]), np.array([5])]
        result = entanglement_entropy_mixture(H, [0, 3], regions, t)
        assert result.shape == (3,)
        assert np.all(np.isfinite(result))
        assert np.all(result >= -1e-10)

    def test_single_source_entropy_never_exceeds_ln2(self):
        """The k=1 closed form (binary entropy of a single probability)
        has a hard ceiling of ln(2) at P_A=0.5 -- checked for the
        single-source case specifically (not asserted for k>1, where
        multiple nonzero eigenvalues can push the sum higher)."""
        H = _random_symmetric_H(10, seed=13)
        t = natural_coherent_time(H)
        regions = [np.array([0, 1]), np.array([2, 3, 4]), np.array([5, 6, 7])]
        result = entanglement_entropy_mixture(H, [2], regions, t)
        assert np.all(result <= np.log(2) + 1e-9)

    def test_residue_relabeling_is_gauge(self):
        """INVARIANCE_PROTOCOL.md Tier 0: permuting H's indices + source +
        region consistently must leave the entropy unchanged."""
        H = _random_symmetric_H(12, seed=9)
        t = 2.8
        source = np.array([1, 4])
        region = np.array([0, 1, 2, 5])
        before = entanglement_entropy_mixture(H, source, [region], t)[0]

        rng = np.random.default_rng(10)
        perm = rng.permutation(12)
        H_perm = H[np.ix_(perm, perm)]
        inv_perm = np.argsort(perm)
        new_source = inv_perm[source]
        new_region = inv_perm[region]
        after = entanglement_entropy_mixture(H_perm, new_source, [new_region], t)[0]

        assert after == pytest.approx(before, abs=1e-9)


class TestHopRadiusNeighborhoods:
    def test_radius_zero_is_self_only(self):
        hop_dist = np.array([
            [0, 1, 2],
            [1, 0, 1],
            [2, 1, 0],
        ], dtype=float)
        regions = hop_radius_neighborhoods(hop_dist, radius=0)
        np.testing.assert_array_equal(regions[0], [0])
        np.testing.assert_array_equal(regions[1], [1])
        np.testing.assert_array_equal(regions[2], [2])

    def test_radius_one_on_a_path(self):
        hop_dist = np.array([
            [0, 1, 2, 3],
            [1, 0, 1, 2],
            [2, 1, 0, 1],
            [3, 2, 1, 0],
        ], dtype=float)
        regions = hop_radius_neighborhoods(hop_dist, radius=1)
        np.testing.assert_array_equal(regions[0], [0, 1])
        np.testing.assert_array_equal(regions[1], [0, 1, 2])
        np.testing.assert_array_equal(regions[2], [1, 2, 3])
        np.testing.assert_array_equal(regions[3], [2, 3])


class TestNaturalCoherentTime:
    def test_equals_inverse_of_smallest_nonzero_gap(self):
        H = _random_symmetric_H(8, seed=11)
        w = np.linalg.eigvalsh(H)
        expected = 1.0 / (w[1] - w[0])
        assert natural_coherent_time(H) == pytest.approx(expected)

    def test_positive_and_finite(self):
        H = _random_symmetric_H(10, seed=12)
        t = natural_coherent_time(H)
        assert t > 0
        assert np.isfinite(t)
