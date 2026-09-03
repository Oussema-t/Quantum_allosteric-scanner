"""Tests for `hyp_register_check.py`.

Per TASK-0319's standing finding (repeated in TASK-0322's own Constraints):
a checker never seen to fail is not verified. Every rule below is paired
with a case that MUST be flagged, not just a case that passes -- mirroring
`.ai/tools/test_doc_parity.py`'s own structure (same precedent this
checker is built in the shape of), which this file matches rather than
inventing a second testing convention.

The uncited-claim seeded-violation test (`test_catches_the_real_incident`)
is deliberately built from TASK-0321's own recorded description of the
actual TASK-0320 incident ("a collaborator brief stated that complex
hopping / a chiral walk was an open route") -- the literal draft text was
never committed to git (confirmed via `git log`, see TASK-0322's own
RESULTS), so this reconstructs the incident's own recorded shape rather
than replaying un-recoverable bytes. This is TASK-0322's own Planned
Validation requirement.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hyp_register_check import (  # noqa: E402
    Hypothesis,
    build_index_text,
    find_staleness,
    find_uncited_claims_in_text,
    parse_hypotheses_from_text,
    record_task_citation,
)

# --------------------------------------------------------------------------
# hypothesis parsing
# --------------------------------------------------------------------------

PHYSICS_SNIPPET = """# physics.md

## HYP-P1 · Low-frequency GNM modes are a reliable proxy

**Claim.** Something testable.

Some discussion, no Status line at all.

---

## HYP-P5 · H13 sets a performance ceiling

**Claim.** Something else testable.

**Status, 2026-07-18/19 (TASK-0126): tested, claim partially supported.**
More text after the status.

---

## HYP-P9 · A chiral walk yields a proximity-orthogonal observable

**Status, 2026-07-23 (TASK-0140): tested, claim not supported -- FAIL.**

**Status, 2026-09-03 (TASK-0310, TASK-0320): re-tested and still FAIL --
CLOSED.**
"""


def test_parses_claim_and_no_status():
    hyps = parse_hypotheses_from_text(PHYSICS_SNIPPET, "physics.md")
    assert set(hyps) == {"HYP-P1", "HYP-P5", "HYP-P9"}
    assert hyps["HYP-P1"].claim.startswith("Low-frequency GNM")
    assert hyps["HYP-P1"].status_date is None


def test_parses_single_dated_status():
    hyps = parse_hypotheses_from_text(PHYSICS_SNIPPET, "physics.md")
    assert hyps["HYP-P5"].status_date == "2026-07-18"


def test_picks_latest_of_multiple_dated_statuses_out_of_file_order():
    # HYP-P9's 2026-09-03 status appears BEFORE its 2026-07-23 status in
    # the source text (the real physics.md does this too) -- the parser
    # must pick the max date, not the first or last occurrence.
    hyps = parse_hypotheses_from_text(PHYSICS_SNIPPET, "physics.md")
    assert hyps["HYP-P9"].status_date == "2026-09-03"


# Seeded-violation test for a real bug found 2026-09-03 (post-TASK-0322):
# STATUS_RE originally matched only "**Status,"/"**Status:" -- missing every
# dated verdict actually phrased "Status update,"/"Status confirmed,"/
# "Correction,"/"Resolved ..." in the real register (HYP-S1/S2/S3/S4/S5/S6/P6
# all use one of these). Undercounted 7 of 21 hypotheses as "no verdict
# recorded" when they had one -- the same class of drift this checker exists
# to catch, in the checker itself.
VERDICT_PHRASING_SNIPPET = """# search_complexity.md

## HYP-S1 · Some claim

**Status update, 2026-08-12 (TASK-0210): re-tested, holds.**

---

## HYP-S2 · Another claim

**Correction, 2026-09-03 (TASK-0323/TASK-0324): the precondition did not hold.**

---

## HYP-S3 · A third claim

**Status confirmed, 2026-08-12 (TASK-0208): confirmed.**

---

## HYP-P6 · A fourth claim

**Resolved 2026-07-16, TASK-0109/TASK-0119 -- alternative implemented and works.**
"""


def test_recognizes_status_update_confirmed_correction_resolved_phrasings():
    hyps = parse_hypotheses_from_text(VERDICT_PHRASING_SNIPPET, "search_complexity.md")
    assert hyps["HYP-S1"].status_date == "2026-08-12"
    assert hyps["HYP-S2"].status_date == "2026-09-03"
    assert hyps["HYP-S3"].status_date == "2026-08-12"
    assert hyps["HYP-P6"].status_date == "2026-07-16"


def test_negative_control_descriptive_bold_with_no_verdict_keyword_not_flagged():
    # "**Status in the literature: ...**" (real HYP-P13 text) must not be
    # mistaken for a dated verdict merely for starting with "Status" -- it
    # is, and stays, undated here because it carries no date at all; this
    # guards against a future over-broadening of STATUS_RE, not the parser
    # picking up a date that isn't there.
    snippet = """## HYP-P13 · Some claim

**Status in the literature: this is mainstream, no date in this sentence.**
"""
    hyps = parse_hypotheses_from_text(snippet, "physics.md")
    assert hyps["HYP-P13"].status_date is None


# --------------------------------------------------------------------------
# staleness class
# --------------------------------------------------------------------------


def _hyp(status_date):
    h = Hypothesis("HYP-P99", "synthetic claim", "physics.md")
    h.status_date = status_date
    return h


def test_staleness_seeded_violation_is_caught():
    hyps = {"HYP-P99": _hyp("2026-07-01")}
    record_task_citation(
        hyps, "TASK-9001",
        "cites [[HYP-P99]] with a fresh finding\n- Filed: 2026-08-01\n\n"
        "## Done (2026-08-15, Implementer)\nnew evidence here.",
    )
    findings = find_staleness(hyps)
    assert len(findings) == 1
    assert findings[0]["id"] == "HYP-P99"
    assert findings[0]["citing_date"] == "2026-08-15"


def test_staleness_negative_control_earlier_citation_not_flagged():
    hyps = {"HYP-P99": _hyp("2026-08-15")}
    record_task_citation(
        hyps, "TASK-9001",
        "cites [[HYP-P99]]\n- Filed: 2026-07-01\n\n"
        "## Done (2026-07-10, Implementer)\nolder evidence.",
    )
    assert find_staleness(hyps) == []


def test_staleness_negative_control_no_dated_status_not_flagged():
    # a hypothesis with NO dated status is "no verdict recorded", not
    # stale -- staleness only applies once a verdict exists to go stale
    hyps = {"HYP-P99": _hyp(None)}
    record_task_citation(
        hyps, "TASK-9001",
        "cites [[HYP-P99]]\n\n## Done (2026-09-01, Implementer)\nfound something.",
    )
    assert find_staleness(hyps) == []


def test_citation_date_prefers_done_over_filed():
    hyps = {"HYP-P99": _hyp("2026-01-01")}
    record_task_citation(
        hyps, "TASK-9001",
        "- Filed: 2026-01-15\n\n[[HYP-P99]]\n\n## Done (2026-09-01, X)\nlater.",
    )
    assert hyps["HYP-P99"].citing_tasks[0][1] == "2026-09-01"


def test_citation_falls_back_to_filed_when_no_done_section():
    hyps = {"HYP-P99": _hyp("2026-01-01")}
    record_task_citation(hyps, "TASK-9001", "- Filed: 2026-02-01\n\n[[HYP-P99]] still open, no Done yet.")
    assert hyps["HYP-P99"].citing_tasks[0][1] == "2026-02-01"


# --------------------------------------------------------------------------
# uncited-claim class
# --------------------------------------------------------------------------


def test_uncited_claim_seeded_violation_md():
    text = (
        "## Some finding\n\n"
        "The chiral-walk route remains untested and worth revisiting.\n"
    )
    findings = find_uncited_claims_in_text(text, ".md", "synthetic.md")
    assert len(findings) == 1
    assert "remains untested" in findings[0]["pattern"] or "remains" in findings[0]["pattern"]


def test_uncited_claim_negative_control_id_present_not_flagged():
    text = (
        "## Some finding\n\n"
        "The chiral-walk route remains untested per [[HYP-P9]], see its own Status line.\n"
    )
    assert find_uncited_claims_in_text(text, ".md", "synthetic.md") == []


def test_uncited_claim_html_block_scoping():
    # the claim and the id sit in DIFFERENT <li> blocks -- must still flag,
    # because "adjacent" means same block, not same document
    text = (
        "<ul>"
        "<li>Complex hopping amplitudes are an open route worth pursuing.</li>"
        "<li>Elsewhere, HYP-P9 covers a related question.</li>"
        "</ul>"
    )
    findings = find_uncited_claims_in_text(text, ".html", "synthetic.html")
    assert len(findings) == 1


def test_uncited_claim_html_same_block_not_flagged():
    text = "<ul><li>HYP-P9 already covers this; it is not an open route.</li></ul>"
    assert find_uncited_claims_in_text(text, ".html", "synthetic.html") == []


def test_false_positive_closed_form_not_flagged():
    text = "The propagator uses the exact closed-form limit, which is closed-form by construction.\n"
    assert find_uncited_claims_in_text(text, ".md", "synthetic.md") == []


def test_false_positive_closed_by_definition_line_wrapped_not_flagged():
    # mirrors the real WORKFLOW.md false positive this checker's own
    # calibration run found: the phrase wraps across a markdown line break
    text = "the target property is closed by\n  definition, not measurement.\n"
    assert find_uncited_claims_in_text(text, ".md", "synthetic.md") == []


def test_catches_the_real_incident():
    """TASK-0322's own Planned Validation: reconstruct TASK-0320's actual
    incident (per TASK-0321's recorded description) and confirm the
    checker would have flagged it."""
    text = (
        "## Candidate improvements not yet tried\n\n"
        "Complex hopping amplitudes -- a chiral walk with a synthetic "
        "gauge phase -- is an open route we have not yet explored.\n"
    )
    findings = find_uncited_claims_in_text(text, ".md", "synthetic-brief.md")
    assert len(findings) == 1, "checker would NOT have caught the real TASK-0320 incident"


# --------------------------------------------------------------------------
# index generation
# --------------------------------------------------------------------------


def test_index_sorted_by_citation_count_and_marks_no_verdict():
    high = Hypothesis("HYP-P1", "claim A", "physics.md")
    high.citing_tasks = [("TASK-1", "2026-01-01"), ("TASK-2", "2026-01-02")]
    low = Hypothesis("HYP-P2", "claim B", "physics.md")
    low.status_date = "2026-05-01"
    low.citing_tasks = [("TASK-3", "2026-01-01")]
    text = build_index_text({"HYP-P1": high, "HYP-P2": low})
    lines = [l for l in text.splitlines() if l.startswith("| [[HYP-")]
    assert lines[0].startswith("| [[HYP-P1]]")  # higher citation count first
    assert "no verdict recorded" in lines[0]
    assert "2026-05-01" in lines[1]


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-v"]))
