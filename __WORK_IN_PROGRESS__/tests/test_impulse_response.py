"""TASK-0229.007(b) -- ENM impulse-response transport coverage."""
import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.impulse_response import gnm_impulse_response_peak_time  # noqa: E402


def _helix_coords(n: int) -> np.ndarray:
    theta = np.arange(n) * (100.0 * np.pi / 180.0)
    return np.column_stack([
        2.3 * np.cos(theta),
        2.3 * np.sin(theta),
        1.5 * np.arange(n, dtype=float),
    ])


N = 24
COORDS = _helix_coords(N)
SOURCE = np.array([0, 1, 2])


class TestGnmImpulseResponsePeakTime:
    def test_shapes_and_finite(self):
        r = gnm_impulse_response_peak_time(COORDS, cutoff=10.0, source=SOURCE)
        assert r["peak_time"].shape == (N,)
        assert r["integrated_response"].shape == (N,)
        assert r["C"].shape == (N, len(r["t_grid_reduced"]))
        assert np.all(np.isfinite(r["peak_time"]))
        assert np.all(np.isfinite(r["integrated_response"]))
        assert r["lambda1"] > 0

    def test_t0_matches_static_gnm_covariance(self):
        """C(t=0) must equal the register's own already-existing static
        GNM covariance (`_normalized_dcc`'s own unnormalized numerator) --
        this observable's t=0 limit is not a new quantity, only t>0 is."""
        from allostery.potentials import gnm_context

        r = gnm_impulse_response_peak_time(COORDS, cutoff=10.0, source=SOURCE)
        ctx = gnm_context(COORDS, cutoff=10.0)
        w, U, nz = ctx["w"], ctx["U"], ctx["nz"]
        cov_static = (U[:, nz] * (1.0 / w[nz])) @ U[:, nz].T
        c0_expected = cov_static[SOURCE].mean(axis=0)
        assert r["C"][:, 0] == pytest.approx(c0_expected, abs=1e-8)

    def test_integrated_response_is_nonnegative(self):
        r = gnm_impulse_response_peak_time(COORDS, cutoff=10.0, source=SOURCE)
        assert np.all(r["integrated_response"] >= 0.0)

    def test_seed_residues_have_zero_or_near_zero_peak_time(self):
        """A residue at the seed itself should already be at (or very near)
        its own maximum response at t=0 -- it does not take time for the
        impulse to "arrive" at its own source."""
        r = gnm_impulse_response_peak_time(COORDS, cutoff=10.0, source=SOURCE)
        assert r["peak_time"][SOURCE].max() <= r["t_grid_reduced"][2]

    def test_disconnected_structure_does_not_crash(self):
        """A disconnected graph still has non-trivial modes per component
        (only the fully-degenerate/zero-nonzero-mode case would raise) --
        confirms this function handles disconnected input gracefully,
        matching this project's own GNM edge-case convention (TASK-0128)."""
        cluster_a = _helix_coords(6)
        cluster_b = _helix_coords(6) + np.array([1000.0, 1000.0, 1000.0])
        coords = np.vstack([cluster_a, cluster_b])
        r = gnm_impulse_response_peak_time(coords, cutoff=10.0, source=np.array([0]))
        assert r["peak_time"].shape == (12,)
