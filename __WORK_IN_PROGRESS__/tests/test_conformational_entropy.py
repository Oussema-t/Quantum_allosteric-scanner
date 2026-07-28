"""TASK-0166 -- per-residue GNM low-mode conformational entropy coverage."""
import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.conformational_entropy import (  # noqa: E402
    gnm_lowmode_variance,
    residue_conformational_entropy,
)
from allostery.potentials import _gnm_msf  # noqa: E402


def _helix_coords(n: int) -> np.ndarray:
    theta = np.arange(n) * (100.0 * np.pi / 180.0)
    return np.column_stack([
        2.3 * np.cos(theta),
        2.3 * np.sin(theta),
        1.5 * np.arange(n, dtype=float),
    ])


N = 16
COORDS = _helix_coords(N)


class TestGnmLowmodeVariance:
    def test_shape_and_finite_and_positive(self):
        var = gnm_lowmode_variance(COORDS, cutoff=10.0, n_modes=5)
        assert var.shape == (N,)
        assert np.all(np.isfinite(var))
        assert np.all(var > 0.0)

    def test_full_spectrum_matches_existing_gnm_msf(self):
        """n_modes >= N - 1 (every non-trivial mode included) must
        reduce exactly to `potentials._gnm_msf`'s own already-validated
        full-spectrum formula -- confirms this module's truncated sum is
        the SAME quantity, not an independent re-derivation that happens
        to look similar, when the truncation is not actually truncating
        anything."""
        var_full = gnm_lowmode_variance(COORDS, cutoff=10.0, n_modes=N)
        msf = _gnm_msf(COORDS, cutoff=10.0)
        np.testing.assert_allclose(var_full, msf, rtol=1e-10, atol=1e-12)

    def test_more_modes_never_decreases_variance(self):
        """Adding modes to the sum can only add non-negative terms
        (`U_ik^2 / lambda_k >= 0` always) -- a real monotonicity property
        of the construction, checked directly rather than assumed."""
        var_5 = gnm_lowmode_variance(COORDS, cutoff=10.0, n_modes=5)
        var_10 = gnm_lowmode_variance(COORDS, cutoff=10.0, n_modes=10)
        assert np.all(var_10 >= var_5 - 1e-12)

    def test_uses_the_lowest_modes_not_an_arbitrary_subset(self):
        """n_modes=1 must match summing only the single smallest-eigenvalue
        term by hand -- confirms the sort-and-truncate step actually picks
        the SLOWEST modes (smallest lambda, most collective/global motion),
        not e.g. the first `n_modes` columns in whatever order `eigh`
        happened to return them (`eigh` already returns ascending order for
        a symmetric real matrix, but this test does not rely on that
        implementation detail of `_kirchhoff_eigh`'s own return convention)."""
        from allostery.potentials import _kirchhoff_eigh

        _A, w, U, nz, _winv = _kirchhoff_eigh(COORDS, cutoff=10.0)
        w_nz, U_nz = w[nz], U[:, nz]
        slowest = np.argmin(w_nz)
        expected = (U_nz[:, slowest] ** 2) / w_nz[slowest]

        var_1 = gnm_lowmode_variance(COORDS, cutoff=10.0, n_modes=1)
        np.testing.assert_allclose(var_1, expected, rtol=1e-10)


class TestResidueConformationalEntropy:
    def test_shape_and_finite(self):
        h = residue_conformational_entropy(COORDS, cutoff=10.0, n_modes=5)
        assert h.shape == (N,)
        assert np.all(np.isfinite(h))

    def test_matches_gaussian_differential_entropy_formula_by_hand(self):
        """Direct hand-check of `0.5*ln(2*pi*e*sigma^2)` against the
        variance this module itself reports -- catches any accidental
        factor-of-2/log-base slip."""
        var = gnm_lowmode_variance(COORDS, cutoff=10.0, n_modes=8)
        h = residue_conformational_entropy(COORDS, cutoff=10.0, n_modes=8)
        expected = 0.5 * np.log(2.0 * np.pi * np.e * var)
        np.testing.assert_allclose(h, expected, rtol=1e-10)

    def test_strictly_monotonic_in_variance_so_auc_ranking_is_identical(self):
        """log is a strictly increasing function of its (positive)
        argument -- entropy's own rank order across residues must be
        EXACTLY the rank order of the raw low-mode variance, a real
        mathematical property of this construction worth confirming
        directly (it means this observable's AUC is, by construction,
        identical to `gnm_lowmode_variance`'s own AUC -- documented
        explicitly in the real-run script/RESULTS.md, not silently
        left implicit)."""
        var = gnm_lowmode_variance(COORDS, cutoff=10.0, n_modes=6)
        h = residue_conformational_entropy(COORDS, cutoff=10.0, n_modes=6)
        assert np.array_equal(np.argsort(var), np.argsort(h))

    def test_more_flexible_synthetic_residue_gets_higher_entropy(self):
        """A structural control: stretching the helix's pitch for a
        middle stretch of residues (larger inter-residue distances ->
        weaker/fewer contacts under the same cutoff -> a locally floppier
        subnetwork) should raise, not lower, those residues' own low-mode
        variance/entropy relative to the untouched baseline -- a real,
        checked directional property, not merely "runs without crashing.\""""
        base = _helix_coords(N)
        stretched = base.copy()
        mid = slice(N // 2 - 2, N // 2 + 2)
        stretched[mid, 2] *= 2.5  # widen spacing along the helix axis locally

        h_base = residue_conformational_entropy(base, cutoff=10.0, n_modes=10)
        h_stretched = residue_conformational_entropy(stretched, cutoff=10.0, n_modes=10)
        assert h_stretched[mid].mean() > h_base[mid].mean()

    def test_n_modes_one_is_well_defined_and_finite(self):
        h = residue_conformational_entropy(COORDS, cutoff=10.0, n_modes=1)
        assert np.all(np.isfinite(h))
