"""TASK-0204 (reopened) -- regression tests for the criterion-#1 gate.

The 2026-08-06 run's gate was `opt_rate > (1.0 if greedy_hit else 0.0)`.
Since `opt_rate` is a fraction of N trials, it can never exceed 1.0, so on
any target whose greedy baseline hit, the gate could not return `pass` for
any data at all -- and the pre-registered bar required *both* targets to
pass. These tests pin the corrected three-state verdict so a bar that no
data can clear cannot be reintroduced silently.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from task0204_rotamer_repack_baseline import criterion_1_verdict  # noqa: E402


class TestCriterion1Verdict:
    def test_greedy_misses_and_optimized_never_hits_is_a_fail(self):
        assert criterion_1_verdict(0.0, False) == "fail"

    def test_greedy_misses_and_optimized_hits_at_all_is_a_pass(self):
        assert criterion_1_verdict(0.125, False) == "pass"
        assert criterion_1_verdict(1.0, False) == "pass"

    @pytest.mark.parametrize("opt_rate", [0.0, 0.5, 0.875, 1.0])
    def test_greedy_ceiling_is_not_evaluable_never_a_fail(self, opt_rate):
        """The decisive regression. Under the original gate every one of
        these returned `False` (read as "fail") including a perfect 1.0
        sweep, and each such target was charged against a 2-of-2 bar."""
        assert criterion_1_verdict(opt_rate, True) == "not_evaluable_greedy_ceiling"

    def test_missing_data_is_not_evaluable(self):
        assert criterion_1_verdict(None, False) == "not_evaluable_no_data"
        assert criterion_1_verdict(0.5, None) == "not_evaluable_no_data"

    def test_no_attainable_rate_can_pass_a_greedy_ceiling_target(self):
        """States the defect directly: `opt_rate` is a fraction in [0, 1],
        so the original `> 1.0` bar was unreachable by construction. Any
        future rewrite that reintroduces a strictly-greater-than-1.0
        comparison fails here."""
        attainable = [i / 8 for i in range(9)]
        assert max(attainable) == 1.0
        assert all(criterion_1_verdict(r, True) != "fail" for r in attainable)
        assert not any(r > 1.0 for r in attainable)
