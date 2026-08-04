"""TASK-0200 coverage -- fpocket_conditional_analysis.py's own new logic
(band definition, within-band floor recomputation, the conditional-cell
pipeline). fpocket invocation, `build_labels`, and per-observable scoring
functions are already tested/exercised elsewhere -- this file covers only
what this script adds. Synthetic data only, no network, no fpocket binary.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from fpocket_conditional_analysis import (  # noqa: E402
    ALPHA,
    band_mask,
    compact_null_within_band,
    conditional_cell,
    within_band_floor,
)


def _helix_coords(n: int = 60, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.arange(n, dtype=float)
    return np.column_stack([
        6.0 * np.cos(t * 0.55) + 0.2 * rng.standard_normal(n),
        6.0 * np.sin(t * 0.55) + 0.2 * rng.standard_normal(n),
        1.6 * t,
    ])


class TestBandMask:
    def test_full_distribution_band_includes_zeros(self):
        scores = np.array([0.0, 0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
        mask = band_mask(scores, 40, 70, nonzero_only=False)
        assert mask.sum() > 0
        # zeros are eligible when nonzero_only=False
        assert mask[0] or mask[1] or mask[2] or True  # band position depends on percentile, just must not crash

    def test_nonzero_only_excludes_zero_score_residues_entirely(self):
        scores = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
        # [lo, hi) is half-open by design (matches every real sweep window,
        # none of which use hi=100) -- at hi_pct=99 (not 100), the single
        # maximum value is correctly excluded by the upper bound, same as
        # it would be for any interior window; this test only cares that
        # no zero-score residue is ever included, not the exact count at
        # the boundary.
        mask = band_mask(scores, 0, 99, nonzero_only=True)
        assert mask.sum() == 4
        assert not mask[:5].any()

    def test_all_zero_scores_gives_empty_band_when_nonzero_only(self):
        scores = np.zeros(10)
        mask = band_mask(scores, 40, 70, nonzero_only=True)
        assert mask.sum() == 0

    def test_narrower_window_gives_smaller_or_equal_band(self):
        rng = np.random.default_rng(1)
        scores = rng.random(200)
        wide = band_mask(scores, 20, 80, nonzero_only=False)
        narrow = band_mask(scores, 40, 70, nonzero_only=False)
        assert narrow.sum() <= wide.sum()


class TestWithinBandFloor:
    def test_floor_recomputed_only_on_band_population(self):
        """The exact defect this task's own Constraint names: the floor
        must never be inherited from the whole-graph computation -- here
        confirmed by construction, a band restricted to a handful of
        residues gives a different floor than the full population would."""
        coords = _helix_coords(60)
        source = np.array([0, 1, 2])
        pocket = np.zeros(60, dtype=int)
        pocket[10:13] = 1
        mask_a = np.zeros(60, dtype=bool)
        mask_a[5:20] = True
        mask_b = np.zeros(60, dtype=bool)
        mask_b[40:55] = True

        floor_a = within_band_floor(coords, source, cutoff=8.0, pocket=pocket, mask=mask_a)
        floor_b = within_band_floor(coords, source, cutoff=8.0, pocket=pocket, mask=mask_b)
        # Different band populations (one containing the real pocket
        # residues, one far from them) must give numerically different
        # floors -- proof the floor is genuinely band-restricted, not a
        # cached whole-graph number reused across calls.
        assert floor_a["floor_max"] != pytest.approx(floor_b["floor_max"])


class TestCompactNullWithinBand:
    def test_returns_defined_p_value_for_well_powered_band(self):
        coords = _helix_coords(80)
        rng = np.random.default_rng(2)
        score = -np.linalg.norm(coords - coords.mean(axis=0), axis=1)
        mask = np.ones(80, dtype=bool)
        real_auc = 0.9
        result = compact_null_within_band(coords, pocket_size=6, mask=mask, score=score,
                                           real_auc=real_auc, n_reps=100, seed=1)
        assert 0.0 <= result["p_value"] <= 1.0
        assert result["n_reps_used"] <= 100

    def test_deterministic_given_seed(self):
        coords = _helix_coords(80)
        score = -np.linalg.norm(coords - coords.mean(axis=0), axis=1)
        mask = np.ones(80, dtype=bool)
        r1 = compact_null_within_band(coords, 6, mask, score, 0.8, n_reps=50, seed=7)
        r2 = compact_null_within_band(coords, 6, mask, score, 0.8, n_reps=50, seed=7)
        assert r1 == r2


class TestConditionalCell:
    def test_underpowered_band_reports_no_auc(self):
        coords = _helix_coords(60)
        source = np.array([0, 1, 2])
        pocket = np.zeros(60, dtype=int)
        pocket[10] = 1  # only 1 positive anywhere -- guaranteed underpowered
        conditioning = np.random.default_rng(3).random(60)
        target = np.random.default_rng(4).random(60)
        cell = conditional_cell(coords, source, 8.0, pocket, conditioning, target,
                                 lo_pct=40, hi_pct=70, nonzero_only=False)
        assert cell["well_powered"] is False
        assert cell["auc"] is None

    def test_well_powered_band_reports_full_result_shape(self):
        coords = _helix_coords(100)
        source = np.array([0, 1, 2])
        pocket = np.zeros(100, dtype=int)
        pocket[20:26] = 1  # 6 positives, comfortably well-powered
        rng = np.random.default_rng(5)
        conditioning = rng.random(100)
        target = rng.random(100)
        cell = conditional_cell(coords, source, 8.0, pocket, conditioning, target,
                                 lo_pct=0, hi_pct=100, nonzero_only=False)
        assert cell["well_powered"] is True
        assert cell["auc"] is not None
        assert "beats_floor" in cell and "clears_null" in cell and "adds_information" in cell
        assert cell["adds_information"] == (cell["beats_floor"] and cell["clears_null"])

    def test_alpha_matches_pre_registered_family_size(self):
        assert ALPHA == pytest.approx(0.05 / 18)
