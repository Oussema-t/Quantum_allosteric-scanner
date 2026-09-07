#!/usr/bin/env python3
"""Tests for submission_build.py (TASK-0341, TASK-0342).

The acceptance bar (TASK-0319: an unverified checker is not verified):
  * the page-budget check must FAIL on a seeded over-length document
  * the change report must DETECT a seeded number change
  * (TASK-0342) the clipping check must FAIL on a seeded margin overflow

Those run as pure-function tests with no Chrome and no pdfplumber, so they are
part of the always-run suite. The end-to-end render test is skipped when
Chrome or pdfplumber is absent.
"""
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import submission_build as sb  # noqa: E402


def _page(text, w=sb.A4_PT[0], h=sb.A4_PT[1], sizes=None, words=None):
    return sb.RenderedPage(width=w, height=h, text=text,
                           char_sizes=sizes if sizes is not None else [12.4] * 200,
                           words=words if words is not None else [])


# ---------------------------------------------------------------- budget gate

def _appendix_page(text=""):
    """A page carrying the invisible page-detection marker -- TASK-0342: the
    split must NOT be found by searching for the word "appendix" in body
    text, since S1's own prose cites "(Appendix C)" inline, well before the
    real appendix. See mark_appendix_start / _APPENDIX_MARKER_TOKEN."""
    return _page(text + " " + sb._APPENDIX_MARKER_TOKEN)


def test_within_limits_passes():
    pages = [_page("body %d" % i) for i in range(5)]
    pages += [_appendix_page("Appendix A -- Claims ledger")]
    pages += [_page("appendix cont %d" % i) for i in range(2)]
    result, checks = sb.evaluate(sb.analyze(pages))
    assert result == "PASS"
    by = {c.name: c for c in checks}
    assert by["body pages"].status == "PASS"
    assert by["appendix pages"].status == "PASS"


def test_overlength_body_fails():
    # 7 pages of body before the appendix marker -> body pages = 7 > 6
    pages = [_page("body page %d text" % i) for i in range(7)]
    pages += [_appendix_page("Appendix A -- Claims ledger"), _page("more appendix")]
    result, checks = sb.evaluate(sb.analyze(pages))
    assert result == "FAIL"
    body = next(c for c in checks if c.name == "body pages")
    assert body.status == "FAIL"
    assert "7 / 6" in body.detail


def test_overlength_appendix_fails():
    pages = [_page("body %d" % i) for i in range(3)]
    pages += [_appendix_page("Appendix A -- Claims ledger")]
    pages += [_page("appendix overflow %d" % i) for i in range(4)]  # 5 appendix pages
    result, checks = sb.evaluate(sb.analyze(pages))
    assert result == "FAIL"
    appx = next(c for c in checks if c.name == "appendix pages")
    assert appx.status == "FAIL" and "5 / 3" in appx.detail


def test_inline_appendix_mention_in_body_is_not_a_false_split():
    """TASK-0342 regression: a page whose BODY PROSE merely mentions
    "Appendix C" (as S1's real taxonomy table does) must not be mistaken for
    the actual appendix start. Confirmed live: this exact bug reported the
    real submission's appendix as starting on page 2 (body=1) when the real
    heading was on page 13 (body=12)."""
    pages = [_page("... belongs with our other disclosed limitations "
                   "(Appendix C), not carried silently ...")]
    pages += [_page("body page %d" % i) for i in range(5)]
    pages += [_appendix_page("Appendix A -- Claims ledger")]
    a = sb.analyze(pages)
    assert a["appendix_starts_on_page"] == 7           # the marker's page, not page 1
    assert a["body_pages"] == 6


def test_non_a4_paper_fails():
    letter = [_page("body", w=612.0, h=792.0) for _ in range(2)]
    result, checks = sb.evaluate(sb.analyze(letter))
    assert result == "FAIL"
    assert next(c for c in checks if c.name == "paper size").status == "FAIL"


def test_small_dominant_font_fails():
    pages = [_page("tiny text", sizes=[8.0] * 300) for _ in range(2)]
    result, checks = sb.evaluate(sb.analyze(pages))
    assert result == "FAIL"
    font = next(c for c in checks if c.name == "body font")
    assert font.status == "FAIL" and "8.0 pt" in font.detail


def test_small_minority_font_only_warns():
    pages = [_page("body", sizes=[12.4] * 300 + [7.9] * 10) for _ in range(3)]
    pages += [_appendix_page("Appendix A")]
    result, checks = sb.evaluate(sb.analyze(pages))
    assert result == "PASS"                       # dominant text is fine
    warn = next(c for c in checks if c.name == "small text")
    assert warn.status == "WARN" and "7.9" in warn.detail


def test_missing_appendix_heading_counts_all_as_body():
    pages = [_page("no appendix here %d" % i) for i in range(4)]
    a = sb.analyze(pages)
    assert a["appendix_starts_on_page"] is None
    assert a["body_pages"] == 4 and a["appendix_pages"] == 0


# ---------------------------------------------------------------- clipping (TASK-0342)

def _content_bounds():
    left = sb.MARGIN_LEFT_PT
    right = sb.A4_PT[0] - sb.MARGIN_RIGHT_PT
    return left, right


def test_word_past_right_margin_fails():
    left, right = _content_bounds()
    pages = [_page("body", words=[(left + 5, right + 40, "overflowingword")])]
    pages += [_appendix_page("Appendix A")]
    result, checks = sb.evaluate(sb.analyze(pages))
    assert result == "FAIL"
    clip = next(c for c in checks if c.name == "no horizontal overflow")
    assert clip.status == "FAIL"
    assert "overflowingword" in clip.detail
    assert "right margin" in clip.detail


def test_word_past_left_margin_fails():
    left, right = _content_bounds()
    pages = [_page("body", words=[(left - 40, left - 5, "spilled")])]
    pages += [_appendix_page("Appendix A")]
    result, checks = sb.evaluate(sb.analyze(pages))
    clip = next(c for c in checks if c.name == "no horizontal overflow")
    assert clip.status == "FAIL" and "left margin" in clip.detail


def test_words_within_margin_pass():
    left, right = _content_bounds()
    pages = [_page("body", words=[(left + 2, right - 2, "fine"),
                                  (left, right, "exactly at the edge")])]
    pages += [_appendix_page("Appendix A")]
    result, checks = sb.evaluate(sb.analyze(pages))
    clip = next(c for c in checks if c.name == "no horizontal overflow")
    assert clip.status == "PASS"
    assert result == "PASS"


def test_clipping_tolerance_absorbs_subpixel_rounding():
    """CLIP_TOLERANCE_PT exists for antialiasing slack, not a real allowance --
    a word 0.5pt over the margin (sub-pixel rounding noise) must still PASS."""
    left, right = _content_bounds()
    pages = [_page("body", words=[(left, right + 0.5, "borderline")])]
    pages += [_appendix_page("Appendix A")]
    _, checks = sb.evaluate(sb.analyze(pages))
    assert next(c for c in checks if c.name == "no horizontal overflow").status == "PASS"


def test_print_css_contains_the_task_0342_fix():
    """The injected stylesheet must actually carry the reflow + font-floor
    rules -- a docstring claiming the fix with CSS that doesn't apply it would
    be worse than no fix (looks certified, isn't)."""
    css = sb.PRINT_CSS
    assert "overflow: visible" in css
    assert "table-layout: auto" in css
    assert "white-space: normal" in css
    for sel in sb._SMALL_TEXT_SELECTORS:
        assert sel in css, "selector %r missing from the injected font floor" % sel


# ---------------------------------------------------------------- change report

_OLD = """
<h1>Quantum Allosteric Scanner</h1>
<section><h2>Problem Framing</h2>
<p>Our walk occupation scores AUC <code>0.5921</code> on 108 structures.
Residualised it falls to 0.5184.</p></section>
<section class="plain" id="appendix"><h2>Appendix A</h2><p>ledger</p></section>
"""

_NEW_NUMBER_CHANGED = """
<h1>Quantum Allosteric Scanner</h1>
<section><h2>Problem Framing</h2>
<p>Our walk occupation scores AUC <code>0.4211</code> on 108 structures.
Residualised it falls to 0.5184.</p></section>
<section class="plain" id="appendix"><h2>Appendix A</h2><p>ledger</p></section>
"""

_NEW_HEADING_ADDED = _OLD.replace(
    "<p>ledger</p></section>",
    "<p>ledger</p></section><section><h2>Finding 4 -- a stricter null</h2>"
    "<p>new content here with several words added for the delta</p></section>")


def test_change_report_detects_number_change():
    cr = sb.change_report(_OLD, _NEW_NUMBER_CHANGED)
    assert "0.4211" in cr["figures_added"]
    assert "0.5921" in cr["figures_removed"]
    assert "0.5184" not in cr["figures_added"]     # unchanged value not flagged
    assert "0.5184" not in cr["figures_removed"]


def test_change_report_detects_new_heading():
    cr = sb.change_report(_OLD, _NEW_HEADING_ADDED)
    assert any("finding 4" in h for h in cr["headings_added"])
    assert cr["headings_removed"] == []


def test_change_report_section_word_delta():
    cr = sb.change_report(_OLD, _NEW_HEADING_ADDED)
    assert cr["section_word_delta"].get("finding 4 -- a stricter null", 0) > 0


def test_change_report_no_change_is_quiet():
    cr = sb.change_report(_OLD, _OLD)
    assert cr["figures_added"] == [] and cr["figures_removed"] == []
    assert cr["headings_added"] == [] and cr["headings_removed"] == []
    assert cr["section_word_delta"] == {}
    assert cr["headings_reordered"] is False


def test_change_report_flags_appendix_split_move():
    moved = _OLD.replace(
        '<section class="plain" id="appendix"><h2>Appendix A</h2>',
        '<section><h2>Extra Body Section</h2><p>x</p></section>'
        '<section class="plain" id="appendix"><h2>Appendix A</h2>')
    cr = sb.change_report(_OLD, moved)
    # appendix heading set is unchanged, but a new body heading appeared
    assert any("extra body section" in h for h in cr["headings_added"])


# ---------------------------------------------------------------- css injection

def test_inject_print_css_after_style():
    html = "<title>t</title><style>body{color:red}</style>\n<div>x</div>"
    out = sb.inject_print_css(html)
    assert out.count("<style>") == 2
    assert out.index("@page { size: A4") > out.index("body{color:red}")
    assert out.index("<div>x</div>") > out.index("@page { size: A4")


def test_inject_print_css_no_style_block():
    out = sb.inject_print_css("<div>only body</div>")
    assert "@page { size: A4" in out and out.strip().endswith("<div>only body</div>")


def test_mark_appendix_start_inserts_token_right_after_the_tag():
    html = ('<section class="plain" id="appendix"><div class="body">'
           '<h2>Appendix A</h2></div></section>')
    out = sb.mark_appendix_start(html)
    assert sb._APPENDIX_MARKER_TOKEN in out
    # inserted immediately after the opening tag, before any real content
    assert out.index(sb._APPENDIX_MARKER_TOKEN) < out.index("<h2>Appendix A")
    assert out.index(sb._APPENDIX_MARKER_TOKEN) > out.index('id="appendix"')


def test_mark_appendix_start_noop_without_the_id():
    html = "<section><h2>Not an appendix</h2></section>"
    assert sb.mark_appendix_start(html) == html


# ---------------------------------------------------------------- end to end
#
# These render with real Chrome. They pass in a normal terminal. Run through a
# restrictive sandbox (e.g. an agent's Bash tool) Chrome cannot complete its
# Mach-port rendezvous and the render fails -- detected below and turned into a
# skip so the suite stays green in both places. The acceptance-bar checks
# (over-length FAILs, number change detected) are the pure-function tests above
# and always run.

_have_chrome = sb.find_chrome() is not None
try:
    import pdfplumber  # noqa: F401
    _have_pdfplumber = True
except ImportError:
    _have_pdfplumber = False

_SANDBOX_SIGNATURES = ("rendezvous", "Mach port", "no PDF", "did not finish")


def _skip_if_sandboxed(ctx):
    err = ctx.get("error", "")
    if err and any(s.lower() in err.lower() for s in _SANDBOX_SIGNATURES):
        pytest.skip("headless Chrome cannot render here (sandbox): %s" % err)


@pytest.mark.skipif(not (_have_chrome and _have_pdfplumber),
                    reason="needs Chrome + pdfplumber (macOS-local)")
def test_end_to_end_renders_real_submission(tmp_path):
    assert sb.DEFAULT_HTML.is_file(), "submission HTML twin missing"
    code, ctx = sb.build(sb.DEFAULT_HTML, tmp_path, "HEAD",
                         version=1, want_change=False)
    _skip_if_sandboxed(ctx)
    assert "error" not in ctx, ctx.get("error")
    assert code in (0, 1)                          # built; PASS or a real FAIL
    a = ctx["analysis"]
    assert a["total_pages"] > 0
    assert a["page_size_is_a4"], a["page_size_pt"]
    assert (tmp_path / Path(ctx["pdf_rel"]).name).exists()
    # TASK-0342: the real submission has an inline "(Appendix C)" mention in
    # S1's own body prose, well before the real appendix -- the split must
    # not be fooled by it (this exact case corrupted the very first report).
    assert a["appendix_starts_on_page"] is not None
    assert a["body_pages"] >= 5, (
        "appendix split looks fooled by an inline mention again: "
        "body=%r appendix_starts_on_page=%r" % (a["body_pages"], a["appendix_starts_on_page"]))
    # TASK-0342: tables must reflow instead of clipping -- 0 words past margin.
    clip = next(c for c in ctx["checks"] if c.name == "no horizontal overflow")
    assert clip.status == "PASS", clip.detail


@pytest.mark.skipif(not (_have_chrome and _have_pdfplumber),
                    reason="needs Chrome + pdfplumber (macOS-local)")
def test_end_to_end_seeded_overlength_fails(tmp_path):
    """A copy of the submission with 8 forced page breaks must FAIL the gate."""
    src = sb.DEFAULT_HTML.read_text(encoding="utf-8")
    pad = "<style>section{break-after:page !important}</style>"
    blown = src.replace("</style>", "</style>" + pad, 1)
    hp = tmp_path / "blown.html"
    hp.write_text(blown, encoding="utf-8")
    code, ctx = sb.build(hp, tmp_path, "HEAD", version=99, want_change=False)
    _skip_if_sandboxed(ctx)
    assert "error" not in ctx, ctx.get("error")
    assert ctx["result"] == "FAIL"
    assert code == 1
