"""TASK-0190 coverage -- rg_matched_null_rerun.py's own new logic (the
3-way null dispatcher, the ordering check, and the lowmode/transport null
wrappers' bookkeeping). The underlying scoring machinery (`dcc_low`,
`transmission_from_source`, `compact_patch_matched`, `stratified_auc`) is
already tested elsewhere -- this file covers only what this script adds.
Synthetic data only, no network.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from rg_matched_null_rerun import _draw, _lowmode_null_3way, _ordering_ok, _transport_null_3way  # noqa: E402


def _blob(center, n, spread=1.0, seed=0):
    rng = np.random.default_rng(seed)
    return np.asarray(center, dtype=float) + rng.normal(scale=spread, size=(n, 3))


class TestOrderingOk:
    def test_correct_ordering_passes(self):
        assert _ordering_ok(p_scattered=0.01, p_matched=0.03, p_compact=0.05) is True

    def test_equal_values_pass(self):
        assert _ordering_ok(p_scattered=0.05, p_matched=0.05, p_compact=0.05) is True

    def test_violated_ordering_fails(self):
        assert _ordering_ok(p_scattered=0.05, p_matched=0.01, p_compact=0.02) is False

    def test_tiny_float_noise_at_boundary_tolerated(self):
        assert _ordering_ok(p_scattered=0.05, p_matched=0.05 + 1e-12, p_compact=0.05) is True


class TestDrawDispatcher:
    N, POCKET_SIZE = 40, 6

    def _coords(self):
        return _blob([0, 0, 0], self.N, spread=20.0, seed=1)

    def test_scattered_returns_no_attempts(self):
        coords = self._coords()
        rng = np.random.default_rng(2)
        idx, n_att = _draw("scattered", coords, self.POCKET_SIZE, self.N, rng)
        assert len(idx) == self.POCKET_SIZE
        assert n_att is None

    def test_compact_returns_no_attempts(self):
        coords = self._coords()
        rng = np.random.default_rng(3)
        idx, n_att = _draw("compact", coords, self.POCKET_SIZE, self.N, rng)
        assert len(idx) == self.POCKET_SIZE
        assert n_att is None

    def test_matched_returns_attempt_count(self):
        coords = self._coords()
        rng = np.random.default_rng(4)
        idx, n_att = _draw("matched", coords, self.POCKET_SIZE, self.N, rng, target_rg=10.0)
        assert len(idx) == self.POCKET_SIZE
        assert isinstance(n_att, int) and n_att >= 1

    def test_unknown_null_type_raises(self):
        coords = self._coords()
        rng = np.random.default_rng(5)
        with pytest.raises(ValueError):
            _draw("bogus", coords, self.POCKET_SIZE, self.N, rng)

    def test_matched_infeasibility_propagates(self):
        coords = self._coords()
        rng = np.random.default_rng(6)
        with pytest.raises(RuntimeError):
            _draw("matched", coords, self.POCKET_SIZE, self.N, rng,
                  target_rg=0.0001, max_attempts=50)


class TestLowmodeNull3Way:
    def test_deterministic_and_reports_shape(self):
        n = 50
        coords = _blob([0, 0, 0], n, spread=15.0, seed=7)
        rng = np.random.default_rng(8)
        score = -np.linalg.norm(coords, axis=1)  # smooth field, decreasing with distance from origin
        pocket = np.zeros(n, dtype=int)
        pocket[:6] = 1
        shells = np.zeros(n, dtype=int)  # single shell -- guarantees a well-powered (n_pos=6) cell, no NaN edge case
        prep = {"pocket": pocket, "n_residues": n, "shells": shells, "coords": coords}

        out1 = _lowmode_null_3way(score, prep, "compact", n_reps=50, seed=9)
        out2 = _lowmode_null_3way(score, prep, "compact", n_reps=50, seed=9)
        assert out1 == out2
        assert 0.0 <= out1["p_value"] <= 1.0
        assert out1["n_reps"] <= 50

    def test_matched_reports_attempts_and_draw_rg(self):
        n = 50
        coords = _blob([0, 0, 0], n, spread=15.0, seed=10)
        score = -np.linalg.norm(coords, axis=1)
        pocket = np.zeros(n, dtype=int)
        pocket[:6] = 1
        shells = np.arange(n) % 4
        prep = {"pocket": pocket, "n_residues": n, "shells": shells, "coords": coords}

        out = _lowmode_null_3way(score, prep, "matched", target_rg=8.0, n_reps=30, seed=11)
        assert "mean_attempts" in out
        assert "draw_rg_mean" in out
        assert out["n_infeasible"] >= 0

    def test_scattered_has_no_attempt_fields(self):
        n = 50
        coords = _blob([0, 0, 0], n, spread=15.0, seed=12)
        score = -np.linalg.norm(coords, axis=1)
        pocket = np.zeros(n, dtype=int)
        pocket[:6] = 1
        shells = np.arange(n) % 4
        prep = {"pocket": pocket, "n_residues": n, "shells": shells, "coords": coords}

        out = _lowmode_null_3way(score, prep, "scattered", n_reps=30, seed=13)
        assert "mean_attempts" not in out


class TestTransportNull3Way:
    def test_basic_shape_and_determinism(self):
        n = 40
        coords = _blob([0, 0, 0], n, spread=15.0, seed=14)
        score = -np.linalg.norm(coords, axis=1)
        pocket = np.zeros(n, dtype=int)
        pocket[:5] = 1

        out1 = _transport_null_3way(score, pocket, n, 5, coords, "compact", n_reps=40, seed=15)
        out2 = _transport_null_3way(score, pocket, n, 5, coords, "compact", n_reps=40, seed=15)
        assert out1 == out2
        assert 0.0 <= out1["p_value"] <= 1.0
        assert out1["bonferroni_alpha"] == pytest.approx(0.05 / 3)
