#!/usr/bin/env python3
"""Tests for submission_build_latex.py (TASK-0347).

Page-budget/font-floor/clipping LOGIC is submission_build.py's own
analyze()/evaluate() (reused, not reforked -- see that module's own tests for
its acceptance bar). What's specific to this file and needs its own coverage:
  * the pandoc longtable -> table* rewrite (a real bug -- doubled backslashes
    -- was caught only by actually compiling, not by reading the regex)
  * Unicode math/box-drawing substitution (confirmed necessary by actually
    compiling: XeTeX + fontspec does not carry U+2212/U+2265/etc in a text
    font, "Missing character" errors)
  * the Markdown-native change report (doc_parity.md_to_text reused directly)
  * (TASK-0319's standing rule) the page-budget gate FAILS on a seeded
    over-length document, end to end through this file's own pipeline, not
    only through submission_build.py's already-tested logic

Pure-function tests need neither pandoc nor tectonic. The end-to-end tests
skip (not fail) when either is missing, or when a first-run package download
needs network that isn't available.
"""
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import submission_build_latex as sbl  # noqa: E402
import submission_build as sb          # noqa: E402


# ---------------------------------------------------------------- table rewrite

_LONGTABLE_SAMPLE = r"""Some prose before the table.

{\def\LTcaptype{none} % do not increment counter
\begin{longtable}[]{@{}
  >{\raggedright\arraybackslash}p{(\linewidth - 6\tabcolsep) * \real{0.5000}}
  >{\raggedright\arraybackslash}p{(\linewidth - 6\tabcolsep) * \real{0.5000}}@{}}
\toprule\noalign{}
\begin{minipage}[b]{\linewidth}\raggedright
Col A
\end{minipage} & \begin{minipage}[b]{\linewidth}\raggedright
Col B
\end{minipage} \\
\midrule\noalign{}
\endhead
\bottomrule\noalign{}
\endlastfoot
1 & 2 \\
3 & 4 \\
\end{longtable}
}

Prose after.
"""


def test_widen_tables_produces_table_star():
    out = sbl.widen_tables_to_full_width(_LONGTABLE_SAMPLE)
    assert "\\begin{table*}" in out and "\\end{table*}" in out
    assert "\\begin{longtable}" not in out
    assert "Some prose before" in out and "Prose after" in out


def test_widen_tables_header_has_no_doubled_backslash():
    """Real bug, caught by compiling: the header capture already ends in its
    own line-break marker; appending another produced 4 backslashes and a
    'Missing number' TeX error. Guards the fix directly on the string."""
    out = sbl.widen_tables_to_full_width(_LONGTABLE_SAMPLE)
    assert "\\\\\\\\" not in out
    assert "Col A & Col B \\\\" in out or "Col A & Col B \\" in out


def test_widen_tables_strips_minipage_wrapper():
    out = sbl.widen_tables_to_full_width(_LONGTABLE_SAMPLE)
    assert "\\begin{minipage}" not in out
    assert "Col A" in out and "Col B" in out


def test_widen_tables_preserves_body_rows():
    out = sbl.widen_tables_to_full_width(_LONGTABLE_SAMPLE)
    assert "1 & 2 \\\\" in out
    assert "3 & 4 \\\\" in out


def test_widen_tables_noop_without_a_longtable():
    src = "Just prose, no table.\n"
    assert sbl.widen_tables_to_full_width(src) == src


# ---------------------------------------------------------------- verbatim widen

def test_widen_code_blocks_wraps_figure_star():
    src = "before\n\\begin{verbatim}\nline one\nline two\n\\end{verbatim}\nafter\n"
    out = sbl.widen_code_blocks(src)
    assert "\\begin{figure*}" in out and "\\end{figure*}" in out
    assert "line one" in out and "line two" in out
    assert "\\small" not in out          # TASK-0347 fix: no floor violation


# ---------------------------------------------------------------- unicode handling

def test_preprocess_converts_math_symbols_outside_fences():
    """Uses pandoc's raw-attribute inline syntax, not bare `$...$` -- the
    first attempt used `$-$` and it came through pandoc as four LITERAL
    dollar-sign characters in the rendered PDF, because `$-$` fails pandoc's
    own "is this really math" heuristic. Caught by rendering and looking,
    not by reading the regex (this file's own module docstring)."""
    src = "AUC \u2265 0.60 and p \u2212 value, rate \u00d7 2, \u03c1 = 0.5\n"
    out = sbl._preprocess_markdown(src)
    assert sbl._raw_latex("\\ensuremath{\\geq}") in out
    assert "-" in out                     # minus -> plain hyphen, no math needed
    assert sbl._raw_latex("\\ensuremath{\\times}") in out
    assert sbl._raw_latex("\\ensuremath{\\rho}") in out
    assert "\u2265" not in out and "\u2212" not in out
    assert "$" not in out                 # no bare-$ math left in the output at all


def test_preprocess_leaves_fenced_code_prose_substitutions_alone():
    """Math substitution must not touch fence content -- box-drawing
    transliteration owns that region instead."""
    src = "```\n\u2500\u2500\u2192 x \u2265 1\n```\n"
    out = sbl._preprocess_markdown(src)
    # the arrow/geq INSIDE the fence must NOT be converted -- box-drawing
    # chars transliterate, but stray math glyphs inside a fence are left as
    # literal Unicode (fontspec's default font can render them in a
    # monospace context reasonably, and rewriting verbatim content would
    # misrepresent what the diagram actually says)
    assert sbl._raw_latex("\\ensuremath{\\rightarrow}") not in out
    assert sbl._raw_latex("\\ensuremath{\\geq}") not in out


def test_preprocess_transliterates_box_drawing_in_fences():
    src = "```\n\u250c\u2500\u2500\u2510\n\u2502  \u2502\n\u2514\u2500\u2500\u2518\n```\n"
    out = sbl._preprocess_markdown(src)
    assert "\u250c" not in out and "\u2500" not in out and "\u2502" not in out
    assert "+--+" in out.replace("\n", "") or "+" in out  # ASCII box chars present


def test_preprocess_combines_superscript_digit_runs():
    src = "a naive 10\u00b9\u2074 search space\n"
    out = sbl._preprocess_markdown(src)
    assert sbl._raw_latex("\\textsuperscript{14}") in out


# ---------------------------------------------------------- appendix split (TASK-0367)
#
# TASK-0347/0349's invisible-marker mechanism (`mark_appendix_start`,
# `_APPENDIX_MARKER_TOKEN`) is retired -- see submission_build_latex.py's own
# module docstring and submission_build.py's `_locate_appendix_by_heading`
# for why (Defect 1: the marker's own page was always counted as 100%
# appendix even when real body content shared it; Defect 2: the marker text
# survived, merely colour-hidden, into the shipped PDF's extractable text).
# Coverage for the two defects TASK-0367 found:

def _sized_page(text, heading_word=None, heading_size=None):
    """A submission_build.RenderedPage fixture carrying word_sizes, for the
    heading+font-size locator and the shared-page check -- both operate on
    that field, not on `words`/`char_sizes` (TASK-0342's/TASK-0344's own
    clipping/font-floor checks)."""
    word_sizes = [(heading_word, heading_size)] if heading_word is not None else []
    return sb.RenderedPage(width=sb.A4_PT[0], height=sb.A4_PT[1], text=text,
                           word_sizes=word_sizes)


def test_locate_appendix_by_heading_ignores_body_sized_mention():
    """TASK-0342's own false-positive class, generalized to the new
    locator: an inline "(Appendix C)" citation renders at body size and
    must not be mistaken for the real heading."""
    pages = [
        _sized_page("... our other disclosed limitations (Appendix C) ...",
                    heading_word="Appendix", heading_size=10.5),
        _sized_page("Appendix -- References", heading_word="Appendix",
                    heading_size=11.96),
    ]
    assert sb._locate_appendix_by_heading(pages, "Appendix") == 2


def test_locate_appendix_by_heading_returns_none_when_absent():
    pages = [_sized_page("no appendix mention here", heading_word="Body", heading_size=10.5)]
    assert sb._locate_appendix_by_heading(pages, "Appendix") is None


def test_analyze_detects_a_page_shared_between_body_and_appendix():
    """TASK-0367 Defect 1: real body content precedes the heading on the
    SAME page the heading itself is found on -- the exact shape the real
    shipped PDF had (Team Capability table + reference list before
    'Appendix -- References', all on page 7)."""
    real_body_text = "Member Discipline Role\nOussema Turki Quantum algorithms ...\n"
    pages = [sb.RenderedPage(width=sb.A4_PT[0], height=sb.A4_PT[1], text="body page %d" % i)
            for i in range(6)]
    pages.append(sb.RenderedPage(
        width=sb.A4_PT[0], height=sb.A4_PT[1],
        text=real_body_text + "Appendix -- References\nsome appendix content",
        word_sizes=[("Appendix", 11.96)]))
    appendix_page = sb._locate_appendix_by_heading(pages, "Appendix")
    a = sb.analyze(pages, appendix_page=appendix_page, appendix_heading_pattern="Appendix")
    assert a["appendix_starts_on_page"] == 7
    assert a["shared_page"] == 7
    assert a["body_pages"] == 7        # NOT 6 -- this is the bug this task fixes
    assert a["appendix_pages"] == 1    # page 7 counted in both totals
    # TASK-0367's own required regression test: a fixture whose body spills
    # onto the appendix's first page must FAIL the page check (6-page limit).
    result, checks = sb.evaluate(a)
    assert result == "FAIL"
    body_check = next(c for c in checks if c.name == "body pages")
    assert body_check.status == "FAIL" and "7 / 6" in body_check.detail


def test_analyze_clean_break_reports_no_shared_page():
    """The heading is the first thing on its own page (nothing precedes it
    but its own heading line) -- must NOT be flagged as shared; the
    pre-TASK-0367 math (`appendix_start - 1`) is still correct here."""
    pages = [sb.RenderedPage(width=sb.A4_PT[0], height=sb.A4_PT[1], text="body page %d" % i)
            for i in range(6)]
    pages.append(sb.RenderedPage(
        width=sb.A4_PT[0], height=sb.A4_PT[1],
        text="Appendix -- References\nsome appendix content",
        word_sizes=[("Appendix", 11.96)]))
    appendix_page = sb._locate_appendix_by_heading(pages, "Appendix")
    a = sb.analyze(pages, appendix_page=appendix_page, appendix_heading_pattern="Appendix")
    assert a["shared_page"] is None
    assert a["body_pages"] == 6
    assert a["appendix_pages"] == 1


def test_build_latex_source_never_emits_the_retired_marker_string():
    """TASK-0367 Defect 2, checked at the SOURCE level (no compile needed):
    the (former) marker string must never appear in build_latex_source's
    output for any input -- the mechanism that used to emit it is gone,
    not merely unused for this particular fixture."""
    assert "SUBMISSION_BUILD" not in sbl.LATEX_PREAMBLE
    assert "SUBMISSION_BUILD" not in sbl.LATEX_POSTAMBLE
    assert not hasattr(sbl, "mark_appendix_start")
    assert not hasattr(sbl, "_APPENDIX_MARKER_TOKEN")


# ---------------------------------------------------------------- change report (markdown)

_OLD_MD = """## Problem Framing

AUC 0.5921 on 108 structures. Residualises to 0.5184.

## Appendix A

ledger content
"""

_NEW_MD_NUMBER_CHANGED = """## Problem Framing

AUC 0.4211 on 108 structures. Residualises to 0.5184.

## Appendix A

ledger content
"""

_NEW_MD_HEADING_ADDED = _OLD_MD.replace(
    "## Appendix A",
    "## Finding 4 -- a stricter null\n\nnew content here with several words "
    "added for the delta test to register\n\n## Appendix A")


def test_change_report_md_detects_number_change():
    cr = sbl.change_report_md(_OLD_MD, _NEW_MD_NUMBER_CHANGED)
    assert "0.4211" in cr["figures_added"]
    assert "0.5921" in cr["figures_removed"]
    assert "0.5184" not in cr["figures_added"]
    assert "0.5184" not in cr["figures_removed"]


def test_change_report_md_detects_new_heading():
    cr = sbl.change_report_md(_OLD_MD, _NEW_MD_HEADING_ADDED)
    assert any("finding 4" in h for h in cr["headings_added"])


def test_change_report_md_appendix_split_unchanged_when_appendix_untouched():
    cr = sbl.change_report_md(_OLD_MD, _NEW_MD_HEADING_ADDED)
    assert cr["appendix_split_before"] == cr["appendix_split_after"]


def test_change_report_md_no_change_is_quiet():
    cr = sbl.change_report_md(_OLD_MD, _OLD_MD)
    assert cr["figures_added"] == [] and cr["figures_removed"] == []
    assert cr["headings_added"] == [] and cr["headings_removed"] == []
    assert cr["section_word_delta"] == {}


# ---------------------------------------------------------------- small-text relabel

def test_relabel_small_text_rewrites_html_specific_wording():
    check = sb.Check("small text", "WARN", "3 characters < 10.0 pt (sizes: 7.0 pt)")
    out = sbl._relabel_small_text_check(check)
    # the OLD message claims an SVG diagram / CSS floor caused it -- neither
    # exists in a LaTeX render, so that specific (now-wrong) causal claim
    # must be gone, not just the bare substring "SVG" (this file's own
    # replacement message legitimately contrasts itself with that case).
    assert "scale with the vector graphic's own coordinate system" not in out.detail
    assert "CSS font-size floor" not in out.detail
    assert "3 characters" in out.detail and "7.0 pt" in out.detail


def test_relabel_leaves_other_checks_alone():
    check = sb.Check("body pages", "PASS", "5 / 6")
    assert sbl._relabel_small_text_check(check) is check


# ---------------------------------------------------------------- end to end

_have_pandoc = sbl.find_pandoc() is not None
_have_tectonic = sbl.find_tectonic() is not None
try:
    import pdfplumber  # noqa: F401
    _have_pdfplumber = True
except ImportError:
    _have_pdfplumber = False

_e2e_ready = _have_pandoc and _have_tectonic and _have_pdfplumber


def _skip_if_environment_failure(ctx):
    err = ctx.get("error", "")
    if err and ("timed out" in err.lower() or "network" in err.lower()
               or "downloading" in err.lower()):
        pytest.skip("tectonic package cache unavailable/network issue: %s" % err)


@pytest.mark.skipif(not _e2e_ready, reason="needs pandoc + tectonic + pdfplumber")
def test_end_to_end_real_submission_compiles_and_passes(tmp_path):
    assert sbl.DEFAULT_MD.is_file(), "submission markdown source missing"
    code, ctx = sbl.build(sbl.DEFAULT_MD, tmp_path, "HEAD", version=1,
                         want_change=False)
    _skip_if_environment_failure(ctx)
    assert "error" not in ctx, ctx.get("error")
    a = ctx["analysis"]
    assert a["page_size_is_a4"], a["page_size_pt"]
    assert a["total_pages"] > 0
    modal = a["modal_font_pt"]
    assert modal is not None and modal >= sb.MIN_FONT_PT - 0.05, modal
    clip = next(c for c in ctx["checks"] if c.name == "no horizontal overflow")
    assert clip.status == "PASS", clip.detail


@pytest.mark.skipif(not _e2e_ready, reason="needs pandoc + tectonic + pdfplumber")
def test_end_to_end_appendix_heading_split_compiles_and_lands_correctly(tmp_path):
    """Real pandoc+tectonic compile, real heading-size detection (TASK-0367
    retired the injected-marker mechanism TASK-0349 fixed a compile bug in --
    that bug is moot now, the marker is never emitted): a document with real
    body content (>=1 full page) followed by an "Appendix" heading with its
    own content, asserting both that the split lands on the body's last real
    page (not page 1 or page 0) and that no build-internal string reaches
    the shipped PDF's extractable text (Defect 2, checked against a REAL
    compiled PDF here, not just the .tex source)."""
    filler = ("This is a long filler sentence written to occupy real "
             "vertical space on the page so the body genuinely spans "
             "multiple pages before the appendix begins. " * 20)
    body = "\n\n".join("## Section %d\n\n%s" % (i, filler) for i in range(6))
    md = ("# Split fixture\n\n" + body +
         "\n\n## Appendix\n\nThis is the appendix content, after the split.\n")
    md_path = tmp_path / "appendix_split.md"
    md_path.write_text(md, encoding="utf-8")
    code, ctx = sbl.build(md_path, tmp_path, "HEAD", version=98, want_change=False,
                         appendix_heading_pattern="Appendix")
    _skip_if_environment_failure(ctx)
    assert "error" not in ctx, ctx.get("error")
    a = ctx["analysis"]
    assert a["appendix_starts_on_page"] is not None, \
        "appendix heading not found in the rendered PDF -- detection regressed"
    assert 1 <= a["appendix_starts_on_page"] <= a["total_pages"], a
    # Real two-column layout: whether the appendix heading lands cleanly on
    # its own page or shares one with the last of the body is a real
    # property of how the content flows, not something this fixture
    # controls precisely -- assert the RELATIONSHIP holds either way
    # (TASK-0367's own two cases), not one hardcoded shape.
    if a["shared_page"]:
        assert a["body_pages"] == a["appendix_starts_on_page"] == a["shared_page"], a
    else:
        assert a["body_pages"] == a["appendix_starts_on_page"] - 1, a

    pages = sb.pdf_to_pages(Path(ctx["pdf_path"]))
    for i, pg in enumerate(pages, start=1):
        assert "SUBMISSION_BUILD" not in pg.text, \
            "build-internal marker string leaked into the shipped PDF's text layer, page %d" % i


@pytest.mark.skipif(not _e2e_ready, reason="needs pandoc + tectonic + pdfplumber")
def test_end_to_end_seeded_overlength_fails(tmp_path):
    """TASK-0319's standing rule: the gate must FAIL on a document seeded to
    exceed the page budget. A markdown fixture with 12 verbose sections
    (well past 6pp even at two-column density) must trip 'body pages FAIL'."""
    filler = ("This is a long filler sentence written to occupy real "
             "vertical space on the page so that many repetitions of it "
             "will reliably exceed the six page body budget even under a "
             "dense two column layout. " * 20)
    section = "\n\n## Section %d\n\n" + filler + "\n\n" + filler + "\n\n" + filler
    md = "# Overlength fixture\n" + "".join(section % i for i in range(30))
    md_path = tmp_path / "overlength.md"
    md_path.write_text(md, encoding="utf-8")
    code, ctx = sbl.build(md_path, tmp_path, "HEAD", version=99, want_change=False)
    _skip_if_environment_failure(ctx)
    assert "error" not in ctx, ctx.get("error")
    assert ctx["result"] == "FAIL"
    assert code == 1
    body = next(c for c in ctx["checks"] if c.name == "body pages")
    assert body.status == "FAIL"


@pytest.mark.skipif(not _e2e_ready, reason="needs pandoc + tectonic + pdfplumber")
def test_end_to_end_determinism_content_is_byte_identical_except_trailer_id(tmp_path):
    """TASK-0347's own constraint: 'same input, byte-identical PDF.' Confirmed
    live (module docstring): -Z deterministic-mode + SOURCE_DATE_EPOCH remove
    every timestamp but xdvipdfmx's own random xref /ID trailer field still
    varies. This test pins that down precisely rather than leaving it as a
    vague caveat: everything BEFORE the trailer must be byte-identical across
    two independent compiles of the same source."""
    assert sbl.DEFAULT_MD.is_file()
    _, ctx1 = sbl.build(sbl.DEFAULT_MD, tmp_path, "HEAD", version=1, want_change=False)
    _skip_if_environment_failure(ctx1)
    assert "error" not in ctx1, ctx1.get("error")
    _, ctx2 = sbl.build(sbl.DEFAULT_MD, tmp_path, "HEAD", version=2, want_change=False)
    _skip_if_environment_failure(ctx2)
    assert "error" not in ctx2, ctx2.get("error")
    b1 = Path(ctx1["pdf_path"]).read_bytes()
    b2 = Path(ctx2["pdf_path"]).read_bytes()
    assert len(b1) == len(b2)
    diffs = [i for i in range(len(b1)) if b1[i] != b2[i]]
    if diffs:
        # every differing byte must be in the final ~1% of the file (the
        # xref trailer's /ID field) -- not scattered through actual content.
        # A fixed byte count would be brittle across document-size changes;
        # this scales with the file the same way the trailer itself does.
        boundary = len(b1) - max(300, len(b1) // 100)
        assert min(diffs) > boundary, (
            "content bytes differ, not just the trailer /ID: first diff at "
            "offset %d of %d (expected only after %d)"
            % (min(diffs), len(b1), boundary))
