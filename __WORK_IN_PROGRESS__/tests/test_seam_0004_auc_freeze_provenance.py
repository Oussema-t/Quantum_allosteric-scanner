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

Closed by TASK-0088: `protocol.stamp_provenance`/`verify_frozen_stamp` add
an unforgeable-in-practice token, issued only from inside a real
`frozen_context`, that `verdict_template` now requires (in addition to
`provenance="frozen"`) before rendering unbannered. The first test below
needed no change from its `xfail`-authorship version once the fix landed
(same convention TASK-0058 used for SEAM-0005) -- the failure it encoded
was the seam itself, not the test.
"""
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery import protocol  # noqa: E402
from allostery.report import verdict_template  # noqa: E402


def test_provenance_frozen_claim_requires_having_been_inside_frozen_context():
    # Sanity: no frozen_context is active for this call at all.
    assert protocol.current_context().mode == "unguarded"

    results = {"AUC_apo_Hnew_optimised": 0.9}
    rendered = verdict_template(results, provenance="frozen")

    # A "frozen" claim made from outside any frozen_context, with no
    # stamp, must not render as a clean frozen result.
    assert "DEV/CEILING RESULT" in rendered


def test_provenance_frozen_from_inside_frozen_context_is_the_intended_clean_case():
    """Positive control: a genuinely stamped result -- issued by
    stamp_provenance from inside a real frozen_context -- renders
    unbannered."""
    with protocol.frozen_context({"SOME_HELD_OUT_TARGET"}):
        assert protocol.current_context().mode == "frozen"
        results = protocol.stamp_provenance({"AUC_apo_Hnew_optimised": 0.9})

    # Rendered after the context has already exited -- exactly the
    # "almost always outside the context by render time" case
    # TASK-0088's own "Before implementing" note names; the stamp must
    # still be honored.
    rendered = verdict_template(results, provenance="frozen")
    assert "DEV/CEILING RESULT" not in rendered


def test_forged_stamp_string_is_rejected():
    """Negative control: hand-writing the same dict key report.py checks,
    without ever calling stamp_provenance, must not be trusted -- proves
    the check is a real token lookup, not just "is the key present"."""
    results = {"AUC_apo_Hnew_optimised": 0.9, "_frozen_stamp": "fake-token-i-made-up"}
    rendered = verdict_template(results, provenance="frozen")
    assert "DEV/CEILING RESULT" in rendered
