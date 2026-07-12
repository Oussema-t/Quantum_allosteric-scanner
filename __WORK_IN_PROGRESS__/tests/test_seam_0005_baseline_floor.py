"""SEAM-0005 seam-test (`.ai/seams/SEAM-0005-verdict-signal-vs-baseline-floor.md`).

Invariant: "signal" in a reported verdict means the method beats the
strongest trivial structural baseline (the `baselines.py` floor), not
merely beats chance (AUC > 0.5).

Cross-boundary test between `baselines.py` (floor definition) and
`diagnostics.py` (`classify_failure`, the verdict consumer) -- neither
module's own unit tests can catch this: each is individually correct in
isolation (baselines.py's floor functions are correct; classify_failure's
beats-chance check is correct on its own terms). The invariant lives only
in the composition, which is exactly what makes it a seam per
`SEAM_PROTOCOL.md`'s own definition ("If a unit test on either side could
catch it, it is not a seam-test").

Closed by TASK-0058: `classify_failure` now accepts `floor_scores` and
returns `BEATS_CHANCE_NOT_FLOOR` when the method clears chance but not the
floor. This test needed no changes from its xfail-authorship version --
the failure it encoded was the seam itself, not the test.
"""
import numpy as np
import pytest

from allostery.baselines import surface_baseline
from allostery.diagnostics import NO_FAILURE_DETECTED, classify_failure
from allostery.metrics import auc


def _chain_coords(n: int = 12, spacing: float = 2.0) -> np.ndarray:
    return np.column_stack([
        np.arange(n, dtype=float) * spacing, np.zeros(n), np.zeros(n),
    ])


def test_beating_chance_but_not_the_surface_floor_is_not_no_failure_detected():
    coords = _chain_coords(12, spacing=2.0)
    # Labels concentrated on the two lowest-degree (chain-end) residues --
    # exactly the pattern surface_baseline's floor already predicts
    # perfectly, by construction (surface_baseline = -degree, so the
    # low-degree endpoints score highest; see test_baselines.py's own
    # hand-computed chain-degree case for the same graph).
    labels = np.zeros(12, dtype=int)
    labels[[0, 11]] = 1

    floor_scores = surface_baseline(coords, cutoff=3.0)
    floor_auc = auc(floor_scores, labels)
    assert floor_auc == pytest.approx(1.0)  # sanity: the floor is a perfect predictor here

    # A candidate "method" score that beats chance but is strictly worse
    # than the trivial structural floor above -- exactly the case
    # PLAN.md's "a ceiling that node degree also reaches is structure, not
    # your method" bar exists to catch.
    method_scores = np.array([0.9, 0.5, 0.6, 0.5, 0.4, 0.5, 0.5, 0.4, 0.5, 0.6, 0.5, 0.55])
    method_auc = auc(method_scores, labels)
    assert 0.5 < method_auc < floor_auc  # beats chance, loses to the floor

    result = classify_failure(method_scores, labels, floor_scores=floor_scores)
    assert result != NO_FAILURE_DETECTED, (
        f"method beat chance (AUC={method_auc:.2f}) but not the "
        f"surface-baseline floor (AUC={floor_auc:.2f}) -- must not read as a clean pass"
    )
