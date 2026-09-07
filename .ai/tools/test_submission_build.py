#!/usr/bin/env python3
"""Tests for submission_build.py (TASK-0341).

The acceptance bar (TASK-0319: an unverified checker is not verified):
  * the page-budget check must FAIL on a seeded over-length document
  * the change report must DETECT a seeded number change

Those two run as pure-function tests with no Chrome and no pdfplumber, so they
are part of the always-run suite. The end-to-end render test is skipped when
Chrome or pdfplumber is absent.
"""
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import submission_build as sb  # noqa: E402


def _page(text, w=sb.A4_PT[0], h=sb.A4_PT[1], sizes=None):
    return sb.RenderedPage(width=w, height=h, text=text,
                           char_sizes=sizes if sizes is not None else [12.4] * 200)


# ---------------------------------------------------------------- budget gate

def test_within_limits_passes():
    pages = [_page("body %d" % i) for i in range(5)]
    pages += [_page("Appendix A -- Claims ledger")]
    pages += [_page("appendix cont %d" % i) for i in range(2)]
    result, checks = sb.evaluate(sb.analyze(pages))
    assert result == "PASS"
    by = {c.name: c for c in checks}
    assert by["body pages"].status == "PASS"
    assert by["appendix pages"].status == "PASS"


def test_overlength_body_fails():
    # 7 pages of body before the appendix heading -> body pages = 7 > 6
    pages = [_page("body page %d text" % i) for i in range(7)]
    pages += [_page("Appendix A -- Claims ledger"), _page("more appendix")]
    result, checks = sb.evaluate(sb.analyze(pages))
    assert result == "FAIL"
    body = next(c for c in checks if c.name == "body pages")
    assert body.status == "FAIL"
    assert "7 / 6" in body.detail


def test_overlength_appendix_fails():
    pages = [_page("body %d" % i) for i in range(3)]
    pages += [_page("Appendix A -- Claims ledger")]
    pages += [_page("appendix overflow %d" % i) for i in range(4)]  # 5 appendix pages
    result, checks = sb.evaluate(sb.analyze(pages))
    assert result == "FAIL"
    appx = next(c for c in checks if c.name == "appendix pages")
    assert appx.status == "FAIL" and "5 / 3" in appx.detail


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
    pages += [_page("Appendix A")]
    result, checks = sb.evaluate(sb.analyze(pages))
    assert result == "PASS"                       # dominant text is fine
    warn = next(c for c in checks if c.name == "small text")
    assert warn.status == "WARN" and "7.9" in warn.detail


def test_missing_appendix_heading_counts_all_as_body():
    pages = [_page("no appendix here %d" % i) for i in range(4)]
    a = sb.analyze(pages)
    assert a["appendix_starts_on_page"] is None
    assert a["body_pages"] == 4 and a["appendix_pages"] == 0


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
