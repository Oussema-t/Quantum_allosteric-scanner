"""TASK-0110 -- unit tests for `optuna_scan.py` (Optuna-based CTQW
numerical-parameter scan: apo-only "floor" vs holo-informed "ceiling").
Synthetic H only -- no network, no PDB fetch (matches TASK-0109's own
"synthetic battery" precedent for parameter-validity tests).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.optuna_scan import (  # noqa: E402
    _adaptive_t_max_range,
    apo_floor_scan,
    closed_form_prescription,
    holo_ceiling_scan,
)
from allostery.propagators import check_convergence, min_adequate_n_steps, min_adequate_t_max  # noqa: E402


def _well_conditioned_H(n=16):
    """Unweighted cycle-graph combinatorial Laplacian -- a real, well-
    conditioned spectrum (no near-degenerate eigenvalue pairs beyond the
    cycle's own natural double-degeneracy), so the closed-form-prescribed
    `t_max`/`n_steps` stays small enough for a fast, deterministic test
    budget. Not `build_gapped_synthetic_network` (TASK-0109's own
    battery) -- that construction's near-degenerate spectrum is exactly
    what makes real proteins' convergence requirements large (verified
    directly while building this module); a *well*-conditioned case is
    the right fixture for testing this module's *mechanics*, not its
    behavior on a hard case.
    """
    idx = np.arange(n)
    A = ((np.abs(idx[:, None] - idx[None, :]) == 1) | (np.abs(idx[:, None] - idx[None, :]) == n - 1)).astype(float)
    D = np.diag(A.sum(axis=1))
    return D - A


H_SIMPLE = _well_conditioned_H(16)


class TestAdaptiveTMaxRange:
    def test_brackets_the_closed_form_prescription(self):
        w = np.linalg.eigvalsh(H_SIMPLE)
        t_range = _adaptive_t_max_range(w, kind="time_averaged_ctqw", tol=1e-2)
        t_star = min_adequate_t_max(w=w, kind="time_averaged_ctqw", tol=1e-2)
        assert t_range[0] <= t_star <= t_range[1]

    def test_falls_back_on_degenerate_spectrum(self):
        # A fully disconnected graph (all-zero H) has a zero spectral gap
        # everywhere -- min_adequate_t_max returns inf; must fall back to
        # the fixed range, not propagate inf/nan into Optuna's suggest_*.
        w = np.zeros(10)
        t_range = _adaptive_t_max_range(w, kind="time_averaged_ctqw", tol=1e-2)
        assert np.isfinite(t_range[0]) and np.isfinite(t_range[1])


class TestClosedFormPrescription:
    def test_matches_check_convergence_at_the_boundary(self):
        """The prescribed (t_max, n_steps) should itself pass
        check_convergence -- the two functions must agree, not just both
        exist independently."""
        cf = closed_form_prescription(H_SIMPLE, kind="time_averaged_ctqw", tol=1e-2)
        report = check_convergence(
            H=H_SIMPLE, t_max=cf["t_max"], n_steps=cf["n_steps"],
            kind="time_averaged_ctqw", tol=1e-2,
        )
        assert report.ok

    def test_finite_on_a_well_conditioned_spectrum(self):
        cf = closed_form_prescription(H_SIMPLE)
        assert np.isfinite(cf["t_max"])
        assert cf["n_steps"] is not None
        assert np.isfinite(cf["cost"])


class TestApoFloorScan:
    def test_returns_study_with_expected_structure(self):
        study = apo_floor_scan(H_SIMPLE, n_trials=20, seed=1)
        assert len(study.trials) == 20
        assert "t_max" in study.best_params
        assert "oversample" in study.best_params
        assert "converged" in study.best_trial.user_attrs
        assert "n_steps" in study.best_trial.user_attrs
        assert "t_max_range" in study.user_attrs

    def test_finds_at_least_one_converged_trial_on_a_well_conditioned_case(self):
        study = apo_floor_scan(H_SIMPLE, n_trials=30, seed=1)
        assert any(t.user_attrs.get("converged") for t in study.trials)
        # the best (minimum-cost) trial must itself be a converged one --
        # not just "some trial somewhere converged" (the multiplicative
        # penalty's whole job is to guarantee this ordering)
        assert study.best_trial.user_attrs["converged"] is True

    def test_unconverged_trials_scored_worse_than_converged_ones(self):
        study = apo_floor_scan(H_SIMPLE, n_trials=30, seed=1)
        converged_costs = [t.value for t in study.trials if t.user_attrs.get("converged")]
        unconverged_costs = [t.value for t in study.trials if not t.user_attrs.get("converged")]
        if converged_costs and unconverged_costs:
            assert min(unconverged_costs) > max(converged_costs)

    def test_apo_only_no_labels_in_signature(self):
        import inspect
        params = inspect.signature(apo_floor_scan).parameters
        assert "pocket_labels" not in params
        assert "source" not in params


class TestHoloCeilingScan:
    def test_returns_valid_auc_range(self):
        source = 0
        labels = np.zeros(16, dtype=bool)
        labels[[7, 8]] = True
        study = holo_ceiling_scan(H_SIMPLE, source, labels, n_trials=15, seed=1)
        assert 0.0 <= study.best_value <= 1.0
        assert len(study.trials) == 15

    def test_runs_inside_ceiling_context_and_exits_cleanly(self, monkeypatch):
        from allostery import protocol
        import allostery.propagators as prop_mod

        seen_modes = []
        # holo_ceiling_scan does `from .propagators import time_averaged_ctqw`
        # inside its own function body, so patching the propagators module's
        # attribute is picked up fresh at each call, recording context mode
        # at call time.
        real_fn = prop_mod.time_averaged_ctqw

        def _spy(*args, **kwargs):
            seen_modes.append(protocol.current_context().mode)
            return real_fn(*args, **kwargs)

        monkeypatch.setattr(prop_mod, "time_averaged_ctqw", _spy)
        source = 0
        labels = np.zeros(16, dtype=bool)
        labels[[7, 8]] = True
        assert protocol.current_context().mode == "unguarded"
        holo_ceiling_scan(H_SIMPLE, source, labels, n_trials=3, seed=1)
        assert protocol.current_context().mode == "unguarded"
        assert seen_modes == ["ceiling"] * 3

    def test_n_steps_is_capped_and_flagged_when_the_nyquist_minimum_exceeds_it(self):
        """Found by direct measurement on real KRAS_G12C (module docstring):
        the Nyquist-adequate n_steps at a gap-prescribed t_max can be in
        the millions, making a single time_averaged_ctqw call
        computationally infeasible (O(n_steps) Python loop). A tiny
        max_n_steps forces every trial in a wide t_max range to hit the
        cap -- must run fast (not actually iterate millions of steps) and
        flag every capped trial honestly."""
        import time as _time

        source = 0
        labels = np.zeros(16, dtype=bool)
        labels[[7, 8]] = True
        t0 = _time.monotonic()
        study = holo_ceiling_scan(
            H_SIMPLE, source, labels, n_trials=5, seed=1,
            t_max_range=(1.0, 1000.0), max_n_steps=5,
        )
        elapsed = _time.monotonic() - t0
        assert elapsed < 5.0  # would be minutes+ if the cap didn't apply
        assert all(t.user_attrs["n_steps"] <= 5 for t in study.trials)
        assert any(t.user_attrs["n_steps_capped"] for t in study.trials)
