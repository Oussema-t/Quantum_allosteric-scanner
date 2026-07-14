"""TASK-0106 coverage -- ctqw_trapping_reproduction.py's pure diagnostic
logic, against synthetic data (no network fetch). The real BCR_ABL1
reproduction itself is this task's own Planned Validation (run directly,
findings written up separately), not re-asserted here as a golden value.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
for _p in (_SRC, _SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from allostery.hamiltonians import build_H_new  # noqa: E402

import ctqw_trapping_reproduction as repro_mod  # noqa: E402


def _helix_coords(n: int) -> np.ndarray:
    theta = np.arange(n) * (100.0 * np.pi / 180.0)
    return np.column_stack([
        2.3 * np.cos(theta),
        2.3 * np.sin(theta),
        1.5 * np.arange(n, dtype=float),
    ])


N = 16
COORDS = _helix_coords(N)
BFACTORS = np.full(N, 20.0)


class TestBuildHNewScaled:
    def test_lambda_one_matches_default_build_h_new(self):
        scaled = repro_mod._build_h_new_scaled(COORDS, BFACTORS, cutoff=10.0, lam=1.0)
        default = build_H_new(COORDS, BFACTORS, cutoff=10.0)
        np.testing.assert_allclose(scaled, default)

    def test_lambda_zero_gives_the_bare_laplacian(self):
        from allostery.hamiltonians import normalised_laplacian_alpha

        scaled = repro_mod._build_h_new_scaled(COORDS, BFACTORS, cutoff=10.0, lam=0.0)
        bare = normalised_laplacian_alpha(COORDS, cutoff=10.0, alpha=0.3)
        np.testing.assert_allclose(scaled, bare)

    def test_lambda_scales_the_potential_block_uniformly(self):
        """H(lambda) - L_norm must equal lambda * (H(1) - L_norm) -- the
        review's own H(lambda) = L_norm + lambda*(sum V) construction."""
        from allostery.hamiltonians import normalised_laplacian_alpha

        bare = normalised_laplacian_alpha(COORDS, cutoff=10.0, alpha=0.3)
        full = repro_mod._build_h_new_scaled(COORDS, BFACTORS, cutoff=10.0, lam=1.0)
        quarter = repro_mod._build_h_new_scaled(COORDS, BFACTORS, cutoff=10.0, lam=0.25)

        np.testing.assert_allclose(quarter - bare, 0.25 * (full - bare), atol=1e-10)


class TestTransportDiagnostics:
    def test_fully_localized_occupation_has_pr_of_one(self):
        occ = np.zeros(N)
        occ[0] = 1.0
        diag = repro_mod.transport_diagnostics(occ, COORDS, source=0, cutoff=10.0)
        assert diag["participation_ratio"] == pytest.approx(1.0, abs=1e-9)
        assert diag["mean_hop_from_seed"] == pytest.approx(0.0, abs=1e-9)

    def test_uniform_occupation_has_pr_near_one_over_n(self):
        occ = np.full(N, 1.0 / N)
        diag = repro_mod.transport_diagnostics(occ, COORDS, source=0, cutoff=10.0)
        assert diag["participation_ratio"] == pytest.approx(1.0 / N, rel=1e-6)

    def test_mean_hop_is_nonnegative_and_zero_at_the_seed_only_when_fully_localized(self):
        occ = np.zeros(N)
        occ[5] = 0.5
        occ[6] = 0.5
        diag = repro_mod.transport_diagnostics(occ, COORDS, source=5, cutoff=10.0)
        assert diag["mean_hop_from_seed"] >= 0.0
        assert diag["mean_hop_from_seed"] < 2.0  # residue 6 is 1 hop from residue 5 on this helix
