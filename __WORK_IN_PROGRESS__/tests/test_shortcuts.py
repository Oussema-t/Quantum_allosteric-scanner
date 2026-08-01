"""TASK-0187 -- tests for `allostery.shortcuts`. Synthetic fixtures only
(this project's established convention for fast, network-free unit tests,
`tests/test_plant.py`/`tests/test_nulls.py`'s own precedent). Real-target
(PTP1B) verification is run separately via
`scripts/shortcut_hypothesis_measurement.py` and recorded in the task
file's own Done section, not re-run here.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.shortcuts import (  # noqa: E402
    EnsembleResult,
    analytic_msf,
    ensemble_hop_matrix,
    equipartition_ensemble,
    msf_cross_check,
    patch_hop_distance,
    shortcut_rate,
    specificity_test,
)


def _helix_coords(n: int = 80, seed: int = 0) -> np.ndarray:
    """Same fixture as `tests/test_plant.py::_helix_coords` -- genuine 3D
    compactness (turns pack residues `i` and `i+~10` close in space
    despite being far in sequence), enough local + tertiary contact
    structure for `select_distal_patch` to find a real distal patch."""
    rng = np.random.default_rng(seed)
    t = np.arange(n, dtype=float)
    coords = np.column_stack([
        6.0 * np.cos(t * 0.55) + 0.2 * rng.standard_normal(n),
        6.0 * np.sin(t * 0.55) + 0.2 * rng.standard_normal(n),
        1.6 * t,
    ])
    return coords


class TestAnalyticMsfAndCrossCheck:
    def test_empirical_ensemble_matches_analytic_msf(self):
        coords = _helix_coords()
        ensemble = equipartition_ensemble(
            coords, cutoff=8.0, n_modes=15, kT=1.0, n_samples=3000,
            rng=np.random.default_rng(1),
        )
        result = msf_cross_check(ensemble)
        assert result["ok"], result
        assert result["pearson_r"] >= 0.90
        assert result["median_rel_error"] <= 0.25

    def test_cross_check_catches_a_miscalibrated_sampler(self):
        """The gate must also FAIL a sampler whose scale is wrong -- not
        just always pass. Shape (rank order) preserved, magnitude broken
        (3x too large), same as a real amplitude-scaling bug would look."""
        coords = _helix_coords()
        ensemble = equipartition_ensemble(
            coords, cutoff=8.0, n_modes=15, kT=1.0, n_samples=3000,
            rng=np.random.default_rng(1),
        )
        broken = ensemble._replace(displacements=ensemble.displacements * 3.0)
        result = msf_cross_check(broken)
        assert not result["ok"]
        assert result["median_rel_error"] > 0.25
        # shape agreement (rank order) is untouched by a uniform rescale
        assert result["pearson_r"] >= 0.90


class TestPatchHopDistance:
    def test_hop_zero_when_patch_includes_seed(self):
        coords = _helix_coords()
        seed_idx = np.array([0, 1, 2])
        assert patch_hop_distance(coords, seed_idx, np.array([0]), cutoff=8.0) == 0.0

    def test_hop_positive_for_a_genuinely_distal_patch(self):
        coords = _helix_coords()
        seed_idx = np.array([0, 1, 2])
        far_patch = np.array([40, 41, 42])
        d = patch_hop_distance(coords, seed_idx, far_patch, cutoff=8.0)
        assert d > 1.0


class TestShortcutRate:
    def test_zero_displacement_never_shortcuts(self):
        coords = _helix_coords()
        seed_idx = np.array([0, 1, 2])
        patch = np.array([40, 41, 42])
        n_samples = 50
        zero_ensemble = EnsembleResult(
            displacements=np.zeros((n_samples, len(coords), 3)),
            eigvals=np.array([1.0]), eigvecs=np.zeros((3 * len(coords), 1)), kT=1.0,
        )
        hop_matrix = ensemble_hop_matrix(zero_ensemble, coords, seed_idx, cutoff=8.0)
        out = shortcut_rate(hop_matrix, coords, seed_idx, patch, cutoff=8.0)
        assert out["rate"] == 0.0
        assert out["static_hop"] == patch_hop_distance(coords, seed_idx, patch, cutoff=8.0)

    def test_engineered_displacement_toward_seed_produces_shortcuts(self):
        """A displacement that deterministically moves the patch into
        contact range of the seed every sample must be detected as a
        shortcut on (almost) every sample."""
        coords = _helix_coords()
        seed_idx = np.array([0, 1, 2])
        patch = np.array([40, 41, 42])
        n_samples = 50
        n = len(coords)

        target = coords[0]
        disp = np.zeros((n_samples, n, 3))
        for i in range(n_samples):
            for r in patch:
                # move 95% of the way to the seed residue -> guaranteed <8A
                disp[i, r] = 0.95 * (target - coords[r])

        moved_ensemble = EnsembleResult(
            displacements=disp, eigvals=np.array([1.0]), eigvecs=np.zeros((3 * n, 1)), kT=1.0,
        )
        hop_matrix = ensemble_hop_matrix(moved_ensemble, coords, seed_idx, cutoff=8.0)
        out = shortcut_rate(hop_matrix, coords, seed_idx, patch, cutoff=8.0)
        assert out["rate"] == 1.0
        assert out["min_sample_hop"] <= 1.0


class TestSpecificityTest:
    def test_generic_no_effect_ensemble_fails_the_gate(self):
        """Original failure mode: nothing moves -> no shortcut anywhere ->
        must be reported as a negative, not a false positive."""
        coords = _helix_coords()
        seed_idx = np.array([0, 1, 2])
        real_patch = np.array([40, 41, 42, 43, 44, 45, 46, 47])
        n_samples = 40
        zero_ensemble = EnsembleResult(
            displacements=np.zeros((n_samples, len(coords), 3)),
            eigvals=np.array([1.0]), eigvecs=np.zeros((3 * len(coords), 1)), kT=1.0,
        )
        out = specificity_test(
            zero_ensemble, coords, seed_idx, real_patch, cutoff=8.0,
            n_decoy=10, rng=np.random.default_rng(2),
        )
        assert out["passed"] is False
        assert out["real_rate"] == 0.0

    def test_specific_engineered_shortcut_passes_the_gate(self):
        """Legitimate positive case: only the real patch is displaced
        toward the seed every sample; decoys (selected elsewhere by
        `select_distal_patch`, floor-blind and distal) see zero
        displacement and must not pick up a spurious shortcut rate."""
        coords = _helix_coords()
        seed_idx = np.array([0, 1, 2])
        real_patch = np.array([40, 41, 42, 43, 44, 45, 46, 47])
        n_samples = 40
        n = len(coords)

        target = coords[0]
        disp = np.zeros((n_samples, n, 3))
        for i in range(n_samples):
            for r in real_patch:
                disp[i, r] = 0.95 * (target - coords[r])

        moved_ensemble = EnsembleResult(
            displacements=disp, eigvals=np.array([1.0]), eigvecs=np.zeros((3 * n, 1)), kT=1.0,
        )
        out = specificity_test(
            moved_ensemble, coords, seed_idx, real_patch, cutoff=8.0,
            n_decoy=10, rng=np.random.default_rng(2),
        )
        assert out["passed"] is True
        assert out["significant"] is True
        assert out["material"] is True
        assert out["real_rate"] == 1.0
        assert out["decoy_median"] == 0.0
        for patch in out["decoy_patches"]:
            assert not set(patch.tolist()) & set(real_patch.tolist())
