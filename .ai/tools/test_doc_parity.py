"""Tests for `doc_parity.py`.

The point of most of these is the NEGATIVE direction. A parity checker that has
only ever been seen to pass is not verified -- that is the exact failure this
register documented in TASK-0319 (positive controls run, negative controls
omitted, and a headline invalidated as a result). So every normalisation rule
below is paired with a case that MUST be reported as drift.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from doc_parity import compare, html_to_text, md_to_text, numbers  # noqa: E402

MD_BASE = """# Doc Title

## 1. First Section

The value is **0.5949** and p = 5×10⁻⁹ against 10^14 states.
See `1OPL` for the confound.

## 2. Second Section

Ninety-nine of 118, or 83.9%.
"""

HTML_BASE = """<title>Doc Title</title>
<style>.x{color:#F6F8F7;padding:11px 14px;font-size:16.5px}</style>
<h1>Doc Title</h1>
<h2>First Section</h2>
<p>The value is <strong>0.5949</strong> and p = 5&times;10<sup>&minus;9</sup>
against 10<sup>14</sup> states. See <code>1OPL</code> for the confound.</p>
<h2>Second Section</h2>
<p>Ninety-nine of 118, or 83.9%.</p>
"""


def _write(tmp_path, md=MD_BASE, html=HTML_BASE):
    m = tmp_path / "d.md"
    h = tmp_path / "d.html"
    m.write_text(md, encoding="utf-8")
    h.write_text(html, encoding="utf-8")
    return m, h


# --------------------------------------------------------------- passes

def test_identical_content_passes(tmp_path):
    ok, report = compare(*_write(tmp_path))
    assert ok, report


def test_css_is_not_treated_as_content(tmp_path):
    """CSS hex values and pixel sizes must not leak into the figure set --
    otherwise every stylesheet edit reads as content drift."""
    text, _, _ = html_to_text(HTML_BASE)
    assert "11" not in numbers(text)
    assert "16.5" not in numbers(text)


def test_superscripts_and_unicode_are_folded(tmp_path):
    """MD `10^14` / `5×10⁻⁹` must match HTML `10<sup>14</sup>` / `&minus;9`."""
    md_text, _, _ = md_to_text(MD_BASE)
    ht_text, _, _ = html_to_text(HTML_BASE)
    assert numbers(md_text) == numbers(ht_text)


def test_urls_do_not_create_false_drift(tmp_path):
    """The MD names the artifact URL; its UUID digits exist in no HTML."""
    md = MD_BASE + "\nSee https://example.com/a/9f3c27a1-4d5e-11ee-8888\n"
    ok, report = compare(*_write(tmp_path, md=md))
    assert ok, report


def test_count_differences_are_not_drift(tmp_path):
    """A figure appearing 3x in one file and 5x in the other is fine."""
    md = MD_BASE + "\n0.5949 again, and 0.5949 once more.\n"
    ok, report = compare(*_write(tmp_path, md=md))
    assert ok, report


def test_heading_inside_blockquote_is_still_a_heading(tmp_path):
    md = MD_BASE + "\n> #### Callout Label\n>\n> body\n"
    html = HTML_BASE + "<h4>Callout Label</h4><p>body</p>"
    ok, report = compare(*_write(tmp_path, md=md, html=html))
    assert ok, report


def test_short_html_title_is_allowed(tmp_path):
    """An <h1> is a design element and may carry a shorter form of the MD H1."""
    md = MD_BASE.replace("# Doc Title", "# Doc Title — Phase 1 Proposal")
    ok, report = compare(*_write(tmp_path, md=md))
    assert ok, report
    assert not report["title"]["md_only"]


# --------------------------------------------------------------- MUST fail

def test_drifted_figure_is_caught(tmp_path):
    """The real defect this tool was built for: a number updated in one file
    only. This is exactly the ~320-vs-~338 task count it caught on first run."""
    ok, report = compare(*_write(tmp_path, html=HTML_BASE.replace("118", "112")))
    assert not ok
    assert "118" in report["numbers"]["md_only"]
    assert "112" in report["numbers"]["html_only"]


def test_missing_section_is_caught(tmp_path):
    ok, report = compare(*_write(tmp_path, md=MD_BASE.split("## 2.")[0]))
    assert not ok
    assert "second section" in report["headings"]["html_only"]


def test_reordered_sections_are_caught(tmp_path):
    swapped = ("<h1>Doc Title</h1>\n<h2>Second Section</h2><p>Ninety-nine of 118, or 83.9%.</p>"
               "\n<h2>First Section</h2>"
               "<p>The value is 0.5949 and p = 5&times;10<sup>&minus;9</sup> "
               "against 10<sup>14</sup> states. See <code>1OPL</code>.</p>")
    ok, report = compare(*_write(tmp_path, html=swapped))
    assert not ok
    assert report["heading_order"]["md_only"], report


def test_dropped_identifier_is_caught(tmp_path):
    ok, report = compare(*_write(tmp_path, html=HTML_BASE.replace("<code>1OPL</code>", "that entry")))
    assert not ok
    assert "1OPL" in report["identifiers"]["md_only"]


def test_percentage_change_is_caught(tmp_path):
    ok, report = compare(*_write(tmp_path, md=MD_BASE.replace("83.9%", "84.0%")))
    assert not ok
    assert "84.0%" in report["numbers"]["md_only"]


def test_wrong_title_is_caught(tmp_path):
    ok, report = compare(*_write(tmp_path, html=HTML_BASE.replace("<h1>Doc Title</h1>",
                                                                  "<h1>Other Paper</h1>")))
    assert not ok
    assert report["title"]["md_only"]


# --------------------------------------------------------------- live pair

def test_the_real_submission_pair_is_in_parity():
    """Both halves of the submission are IN THE REPO, so this must FAIL when
    either is missing -- never skip.

    It skipped originally, because the HTML twin lived only in a session
    scratch directory. That silent skip is precisely what let the omission go
    unnoticed: the tool's most important case never ran. Same failure shape as
    TASK-0319 (a control that cannot fire is not a control)."""
    # parents: [0]=.ai/tools  [1]=.ai  [2]=repo root
    doc = Path(__file__).resolve().parents[2] / "__WORK_IN_PROGRESS__/documentation"
    md = doc / "PHASE1_SUBMISSION_V1.md"
    html = doc / "PHASE1_SUBMISSION_V1.html"
    assert md.is_file(), f"submission markdown missing: {md}"
    assert html.is_file(), (
        f"HTML twin missing from the repo: {html}. It must be committed "
        "alongside the markdown -- a twin that exists only in a scratch "
        "directory cannot be reviewed, published, or parity-checked by anyone else.")
    ok, report = compare(md, html)
    assert ok, report
