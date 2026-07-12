"""SEAM-0004 seam-test (`.ai/seams/SEAM-0004-optimised-auc-freeze-provenance.md`).

Invariant: a report tagged `provenance == "frozen"` was actually produced
under `protocol.py`'s frozen-config discipline, not just labeled that way.

Cross-boundary test between `protocol.py` (the DEV/FROZEN state machine)
and `report.py` (`verdict_template`, the `provenance` consumer) -- neither
module's own unit tests can catch this in isolation: `report.py`'s tests
only check that it renders the banner correctly *given* a `provenance`
string; `protocol.py`'s tests only check that `frozen_context` gates its
own accessors. The invariant that a *report's* provenance claim is tied to
having actually gone through `frozen_context` lives only in the
composition -- exactly what makes it a seam per `SEAM_PROTOCOL.md`'s own
definition ("If a unit test on either side could catch it, it is not a
seam-test").

xfail(strict=True): confirmed by direct read (TASK-0055) --
`verdict_template(results, *, provenance="dev")` is a plain keyword with
no call to `protocol.current_context()` anywhere in `report.py`, and
`frozen_context` returns nothing `verdict_template` ever consumes. This
test asserts the invariant SEAM-0004 requires; it fails today because no
structural tie exists between the two sides, confirmed empirically here
(not just by code inspection): outside any `frozen_context`
(`protocol.current_context().mode == "unguarded"`), a caller can pass
`provenance="frozen"` and the DEV banner is incorrectly suppressed. This
is exactly the "re-imports the notebook's Sec.8 leak" scenario
`SEAM_PROTOCOL.md`'s own seed table warns about.

Should start passing, unchanged, once a follow-up task makes
`provenance="frozen"` structurally gated by `protocol.py`'s state machine
-- see SEAM-0004 for status and the follow-up task once filed.
"""
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery import protocol  # noqa: E402
from allostery.report import verdict_template  # noqa: E402


@pytest.mark.xfail(
    strict=True,
    reason=(
        "SEAM-0004 (open): verdict_template's provenance parameter is a "
        "free-text caller-supplied string with no read of "
        "protocol.current_context() anywhere in report.py -- a caller "
        "outside any frozen_context can claim provenance='frozen' and "
        "the DEV banner is incorrectly suppressed."
    ),
)
def test_provenance_frozen_claim_requires_having_been_inside_frozen_context():
    # Sanity: no frozen_context is active for this call at all.
    assert protocol.current_context().mode == "unguarded"

    results = {"AUC_apo_Hnew_optimised": 0.9}
    rendered = verdict_template(results, provenance="frozen")

    # Desired invariant: a "frozen" claim made from outside any
    # frozen_context must not render as a clean frozen result -- the DEV
    # banner should still appear (or the call should be rejected
    # outright; this test asserts the observable-output form of the
    # invariant). This assertion is what fails today, making the gap
    # executable instead of a table row.
    assert "DEV/CEILING RESULT" in rendered


def test_provenance_frozen_from_inside_frozen_context_is_the_intended_clean_case():
    """Positive control: this is the shape a genuinely honored contract
    would have -- included so the xfail above isn't the only exercised
    path through this seam-test file."""
    with protocol.frozen_context({"SOME_HELD_OUT_TARGET"}):
        assert protocol.current_context().mode == "frozen"
        results = {"AUC_apo_Hnew_optimised": 0.9}
        rendered = verdict_template(results, provenance="frozen")

    # Currently indistinguishable from the xfail case above -- rendering
    # doesn't consult the context either way. Documents the same gap from
    # the "this should have been fine" side rather than asserting on it,
    # since the real invariant (does report.py *read* the context) is
    # what the xfail test above already pins.
    assert "DEV/CEILING RESULT" not in rendered
