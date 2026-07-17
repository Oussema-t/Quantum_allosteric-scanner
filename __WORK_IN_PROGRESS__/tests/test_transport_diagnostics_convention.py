"""TASK-0119 -- regression guard for a real, previously-undocumented
convention mismatch found while re-checking TASK-0106's "participation
ratio" numbers.

`metrics.ipr(v)` (`sum(v_i^4) / sum(v_i^2)^2`) is documented as "Inverse
Participation Ratio of an eigenvector" and is correctly tested elsewhere
(`test_hamiltonians.py` T-015) on eigenvector-shaped input (`sum(v^2)=1`).
`analysis._transport_participation_ratio(p)` (`1/(N*sum(p^2))`) is a
*different* formula, explicitly documented as "1.0 = fully delocalised...
~1/N = fully localised" for a probability-distribution-shaped input
(`sum(p)=1`).

`ctqw_trapping_reproduction.py` (TASK-0106) calls `metrics.ipr` directly
on a CTQW occupation vector `occ` (a probability distribution, not an
eigenvector) and labels the result "participation_ratio"/"PR/N" in its
own docstring, implying equivalence to `analysis._transport_participation_
ratio`'s convention. This is false -- the two formulas give OPPOSITE
localization directions when applied to the same probability
distribution, verified below. TASK-0119 traced a review panel's claim
that TASK-0106's narrative direction was "backwards" to this exact
conflation: under `ipr`'s own real convention (high=localized, unlike
`_transport_participation_ratio`'s high=delocalized), TASK-0106's
original prose ("higher value = more localized") was directionally
correct for the metric it actually used -- the panel's correction
assumed the wrong metric's convention. See TASK-0106's Done section
addendum and TASK-0119's own Done section for the full account.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.analysis import _transport_participation_ratio  # noqa: E402
from allostery.metrics import ipr  # noqa: E402


class TestIprVsTransportParticipationRatioOppositeConventions:
    """Both formulas applied to the SAME probability distribution (a
    valid input to each -- `ipr` places no normalisation requirement
    beyond being scale-invariant, `_transport_participation_ratio` is
    defined for exactly this shape), on a delta (fully localized) and a
    uniform (fully delocalized) distribution -- the two textbook extremes
    any transport-localization diagnostic must place at opposite ends."""

    N = 100

    def _delta(self):
        p = np.zeros(self.N)
        p[0] = 1.0
        return p

    def _uniform(self):
        return np.full(self.N, 1.0 / self.N)

    def test_ipr_is_high_for_localized_low_for_delocalized(self):
        assert ipr(self._delta()) == 1.0
        assert abs(ipr(self._uniform()) - 1.0 / self.N) < 1e-10
        assert ipr(self._delta()) > ipr(self._uniform())

    def test_transport_pr_is_low_for_localized_high_for_delocalized(self):
        assert abs(_transport_participation_ratio(self._delta()) - 1.0 / self.N) < 1e-10
        assert _transport_participation_ratio(self._uniform()) == 1.0
        assert _transport_participation_ratio(self._delta()) < _transport_participation_ratio(self._uniform())

    def test_the_two_conventions_are_opposite_not_equivalent(self):
        """The actual regression guard: these are NOT the same convention
        under a relabeling (e.g. neither is a constant multiple or simple
        reciprocal of the other in general), and in particular they rank
        a localized vs. a delocalized distribution in OPPOSITE order --
        code that treats `ipr(p)` as if it were `_transport_participation_
        ratio(p)` (or vice versa) will read every localization conclusion
        backwards."""
        localized, delocalized = self._delta(), self._uniform()
        ipr_says_more_localized_is = "localized" if ipr(localized) > ipr(delocalized) else "delocalized"
        pr_says_more_localized_is = "localized" if _transport_participation_ratio(localized) > _transport_participation_ratio(delocalized) else "delocalized"
        assert ipr_says_more_localized_is == "localized"
        assert pr_says_more_localized_is == "delocalized"
        assert ipr_says_more_localized_is != pr_says_more_localized_is
