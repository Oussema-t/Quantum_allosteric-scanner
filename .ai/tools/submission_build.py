#!/usr/bin/env python3
"""One command: build a numbered submission PDF, and certify it as a side effect.

TASK-0341. The Phase-1 concept proposal ships as a PDF with two hard limits from
`documentation/2026-04-06-Phase-1-Submission-Guidelines-VF.md`:

  * concept proposal   <= 6 pages   (A4 or US Letter, >= 10 pt font)
  * appendices          <= 3 pages
  * over-length is not a style deduction -- "returned or assessed only on the
    first 6 pages", i.e. the argument is truncated mid-sentence.

Nobody had ever counted the pages -- every estimate in the register was
words x a words-per-page constant. This renders the real document and counts.

WHAT THIS IS (per the task's revised requirements -- a BUILD, not a checker):

    submission_build.py  ->  _build/PHASE1_SUBMISSION_v<N>_<sha>.pdf
                         +   a screen-sized report (stdout + a .report.txt twin)

The compliance checks run on every build and report themselves: silence is
PASS, a loud line names any rule broken. The human checks the page count at a
glance; margins / paper size / font size / print stylesheet are asserted so
they do not have to be re-checked by eye.

RENDERER -- no toolchain install. `pandoc`/`wkhtmltopdf`/`weasyprint`/`chromium`
are all absent, but `/Applications/Google Chrome.app` is present, and the
project already keeps a CI-parity-enforced HTML twin of the submission
(`.github/workflows/submission-parity.yml` + `doc_parity.py`). So this prints
that existing HTML twin with headless Chrome rather than adding a third
Markdown->PDF artifact nobody validates.

DETERMINISM. Page counts that move with the machine are worse than none because
they get trusted. Pinned explicitly, and stated in the report every run:
  * paper size A4, fixed margins, forced light theme  -- injected as a print
    stylesheet into a COPY of the HTML (the source file is never touched; the
    exact injected CSS is printed in the report)
  * the appendix is forced to a page break, so the body/appendix split is an
    unambiguous page boundary, not a heuristic about which page a heading
    landed on
  * the Chrome version is recorded
  * whether webfonts were fetched online is recorded -- an offline build falls
    back to Georgia/system and paginates differently; the report says so

TASK-0342 -- the first real render silently lost content. The source's
`.tw{overflow-x:auto}` scrolls on screen (correct, deliberate, left alone);
on paper there is nowhere to scroll to, so it just clips, mid-word, with no
signal that anything is missing. Fixed in the injected stylesheet only:
tables reflow (`table-layout:auto`, `white-space:normal`) instead of
overflowing, and the print-only floor below brings every sub-10pt selector
(chips, table headers, eyebrow/meta/foot, and `code` -- found by rendering and
re-measuring: `code{font-size:.855em}` shrinks below the floor even inside an
already-compliant container, which reading the stylesheet alone missed) up to
10.5pt in the same pass, since raising those interacts directly with how much
a reflowed table needs to wrap. Two categories of sub-10pt text are left
alone deliberately, not missed: the S6 SVG diagram's labels (scale with the
vector graphic's own coordinate system -- a CSS floor changes the source
value the SVG then re-scales, not the rendered size) and `<sup>` exponents
(conventionally smaller than body text everywhere; flooring them would look
broken). A "no horizontal overflow" compliance check catches content that,
once allowed to reflow, spills PAST the page margin instead of being
invisibly clipped -- but it cannot see content some *other*, not-yet-found
overflow:hidden/auto box clips to nothing, since that leaves no trace in the
PDF to check. The report says so; open the rendered PDF once per structural
change, don't rely on the checks alone.

CHANGE REPORT. Blindness to re-reading the same document is the real problem a
page count does not touch. This diffs v(N) against a git ref (default HEAD)
using `doc_parity.py`'s own extractors -- numbers added/removed, headings
added/removed/reordered, per-section word delta, appendix-split moves -- so the
owner reads the delta, not the document.

ENVIRONMENT. Chrome is macOS-local; this tool is local-only by design (the
compliance gate's value is pre-upload, and font loading over the network is
flaky in CI). It exits 3 with a clear message when Chrome or pdfplumber is
absent, so if it is ever wired into CI it skips cleanly rather than failing for
the wrong reason. `pdfplumber` is a dev-only dependency (already in `.venv`,
not in `requirements.txt` -- same policy as `pytest` for `pytest_local.py`).

EXIT CODES
  0  built, all compliance checks PASS (warnings allowed)
  1  built, but a compliance check FAILED
  2  usage / unreadable input
  3  environment: Chrome missing, pdfplumber missing, or the render failed

Run:   .ai/tools/submission_build.py
       .ai/tools/submission_build.py --since HEAD~3 --json
Test:  python3 -m pytest .ai/tools/test_submission_build.py
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import shutil
import socket
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import doc_parity as _dp  # same-directory import; reuse its extractors, do not re-derive

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_HTML = REPO_ROOT / "__WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V1.html"
DEFAULT_OUTDIR = REPO_ROOT / "__WORK_IN_PROGRESS__/documentation/_build"

# guideline limits (from the source, not memory -- see module docstring)
MAX_BODY_PAGES = 6
MAX_APPENDIX_PAGES = 3
MIN_FONT_PT = 10.0

# A4 in PostScript points (1/72"); Chrome renders to this when @page size:A4 is set
A4_PT = (595.276, 841.890)
PAGE_SIZE_TOL_PT = 3.0

# @page margins -- named so the clipping check (below) uses the exact same
# numbers as the injected stylesheet, instead of a second hardcoded guess.
MM_TO_PT = 72.0 / 25.4
MARGIN_TOP_MM, MARGIN_RIGHT_MM, MARGIN_BOTTOM_MM, MARGIN_LEFT_MM = 16.0, 15.0, 18.0, 15.0
MARGIN_LEFT_PT = MARGIN_LEFT_MM * MM_TO_PT
MARGIN_RIGHT_PT = MARGIN_RIGHT_MM * MM_TO_PT
CLIP_TOLERANCE_PT = 2.0  # antialiasing / sub-pixel rounding slack, not a real allowance

# TASK-0342: selectors confirmed (by rendering and re-measuring, not by
# reading the source alone) to sit under MIN_FONT_PT in the base stylesheet.
# Floored here rather than left to a generic "shrink to fit" rule -- the task
# explicitly forbids solving anything in this file by going *under* 10pt.
_SMALL_TEXT_SELECTORS = (
    ".eyebrow", ".meta", ".notice h4", "th", ".chip", ".legend .lbl",
    ".attack .k", ".foot", ".open .tag", ".num",
    # code{font-size:.855em} is RELATIVE -- it shrinks below the floor even
    # where its ambient container (table cell, .notice p, .open p) is itself
    # already >=10pt, so auditing only container selectors missed it. Found
    # by rendering and re-measuring (per TASK-0341/0342's own instruction),
    # not by reading the stylesheet -- it accounted for over half of the
    # first re-render's still-outstanding sub-10pt characters.
    "code",
)

CHROME_MACOS = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Injected into a COPY of the HTML before rendering. Reported verbatim each run.
PRINT_CSS = """
/* ===== injected by submission_build.py (TASK-0341/0342) -- NOT in the source file ===== */
@page {{ size: A4; margin: {top}mm {right}mm {bottom}mm {left}mm; }}
@media print {{
  *, *::before, *::after {{
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}
  :root {{
    --paper:#F6F8F7 !important; --surface:#FFFFFF !important; --surface-2:#EEF2F1 !important;
    --ink:#14201E !important; --ink-2:#3B4A47 !important; --ink-3:#6B7B77 !important;
    --rule:#D8E0DE !important; --rule-strong:#B8C5C2 !important;
    --accent:#0E5A55 !important; --accent-soft:#E3EFED !important;
    --holds:#1C6B48 !important; --holds-bg:#E4F0E9 !important;
    --qual:#8A6314 !important; --qual-bg:#F6EEDD !important;
    --dead:#9B2C2C !important; --dead-bg:#F7E6E4 !important;
    --undet:#475569 !important; --undet-bg:#EAEDF1 !important;
  }}
  html, body {{ background:#FFFFFF !important; }}
  .wrap {{ max-width:none !important; padding:0 0 8mm !important; }}
  #appendix {{ break-before: page !important; }}
  .attack, .open, .notice, svg, tr {{ break-inside: avoid; }}
  h1, h2, h3 {{ break-after: avoid; }}

  /* TASK-0342: overflow-x:auto has nothing to scroll to on paper -- it just
     clips, silently, mid-word ("no -- and not even a single-molecule prope...").
     Correct and deliberate for the screen version (kept in the source
     untouched); wrong for print. Let tables reflow to the page width instead
     of overflowing it. */
  .tw {{ overflow: visible !important; break-inside: auto; }}
  table {{ table-layout: auto !important; width: 100% !important; }}
  th, td, td.n, .chip {{
    white-space: normal !important;
    overflow-wrap: anywhere !important;   /* one unbreakable token must not
                                              reopen the same clipping bug */
  }}

  /* TASK-0342: Guidelines S5 says "minimum 10pt", no exemption for table
     furniture. These selectors measured under 10pt in the base stylesheet
     (eyebrow/meta/foot ~9pt, table headers/chips ~7.9pt) -- floored, not
     shrunk; see MIN_FONT_PT and the "small text" compliance check below,
     which is the self-verification that this list is actually complete. */
  {small_text_selector_list} {{
    font-size: 10.5pt !important;
  }}
}}
""".format(top=MARGIN_TOP_MM, right=MARGIN_RIGHT_MM, bottom=MARGIN_BOTTOM_MM,
          left=MARGIN_LEFT_MM, small_text_selector_list=", ".join(_SMALL_TEXT_SELECTORS))

APPENDIX_MARKER = 'id="appendix"'

# TASK-0342 correction: a heading-text regex here (matched "Appendix\s+[a-z]")
# fired on the FIRST substring matching "Appendix" + a letter anywhere in the
# rendered PDF text -- including S1's own body prose, which cites "(Appendix
# C)" inline in its taxonomy table, pages before the real appendix. That is a
# false positive, not a rare edge case: it corrupted the body/appendix page
# split on every run so far (confirmed directly -- v10's report claimed the
# appendix started on page 2; the real "Appendix A" heading is on page 13).
# Fixed by not searching rendered prose for the word "Appendix" at all: an
# invisible, unique literal token is injected as the first thing inside
# #appendix and the PDF is searched for that exact token instead. No wording
# in the document can collide with it by accident.
#
# First attempt used `position:absolute` to add zero layout height. Wrong:
# confirmed live that Chrome's print pagination anchors an absolutely
# positioned element (no positioned ancestor -> initial containing block) to
# its PRE-pagination static position, not to the page its in-flow neighbours
# land on -- the token never showed up in any page's extracted text at all.
# Left in normal flow instead (white-on-white, so still invisible) --
# genuinely part of the flow, so it paginates exactly where "Appendix A"
# itself does, at the cost of one harmless near-zero-height line before it.
_APPENDIX_MARKER_TOKEN = "SUBMISSION_BUILD_APPENDIX_START_7f3a9c"
_APPENDIX_OPEN_TAG_RE = re.compile(r'(<section\b[^>]*\bid="appendix"[^>]*>)', re.I)


def mark_appendix_start(html: str) -> str:
    """Insert the invisible page-detection marker as the first child of
    #appendix. No-op (returns html unchanged) if #appendix isn't found --
    _first_appendix_page then correctly reports "no marker found" rather than
    silently mis-splitting."""
    marker = ('<span style="font-size:10.5pt;color:#FFFFFF">'
             + _APPENDIX_MARKER_TOKEN + "</span>")
    new_html, n = _APPENDIX_OPEN_TAG_RE.subn(r"\1" + marker, html, count=1)
    return new_html if n else html


# --------------------------------------------------------------------------
# git context
# --------------------------------------------------------------------------

def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO_ROOT,
                          capture_output=True, text=True)


def repo_rel(path: Path) -> str:
    """Repo-relative POSIX path, or the absolute path if it lies outside the repo
    (test fixtures and --outdir can both point elsewhere)."""
    p = path.resolve()
    try:
        return p.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(p)


def _in_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


def git_head_short() -> str:
    r = _git("rev-parse", "--short", "HEAD")
    return r.stdout.strip() if r.returncode == 0 else "nogit"


def git_path_dirty(path: Path) -> bool:
    if not _in_repo(path):
        return False
    r = _git("status", "--porcelain", "--", repo_rel(path))
    return r.returncode == 0 and bool(r.stdout.strip())


def git_show(ref: str, path: Path) -> Optional[str]:
    if not _in_repo(path):
        return None
    r = _git("show", "%s:%s" % (ref, repo_rel(path)))
    return r.stdout if r.returncode == 0 else None


# --------------------------------------------------------------------------
# render
# --------------------------------------------------------------------------

def find_chrome() -> Optional[str]:
    if Path(CHROME_MACOS).is_file():
        return CHROME_MACOS
    for name in ("google-chrome", "google-chrome-stable", "chromium",
                 "chromium-browser", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    return None


def chrome_version(chrome: str) -> str:
    r = subprocess.run([chrome, "--version"], capture_output=True, text=True)
    return r.stdout.strip() or "unknown"


def fonts_reachable(host: str = "fonts.gstatic.com", port: int = 443) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2.5):
            return True
    except OSError:
        return False


def inject_print_css(html: str) -> str:
    """Insert the pinned print stylesheet after the document's own <style>."""
    block = "<style>%s</style>\n" % PRINT_CSS
    idx = html.lower().find("</style>")
    if idx == -1:
        return block + html
    idx += len("</style>")
    return html[:idx] + "\n" + block + html[idx:]


def render_pdf(chrome: str, html_path: Path, out_pdf: Path,
               deadline_s: int = 120) -> Tuple[bool, str]:
    """Render via headless Chrome.

    Chrome's --print-to-pdf writes the file within a second or two but the
    process itself frequently does not exit promptly (lingering helper
    processes, and under a restrictive sandbox it can hang on a Mach-port
    rendezvous). So this does NOT wait for exit: it polls for the output file
    to appear and stop growing, then terminates the process. --headless=old is
    used deliberately -- --headless=new deadlocks against an already-running
    Chrome on macOS.
    """
    if out_pdf.exists():
        out_pdf.unlink()
    src = html_path.read_text(encoding="utf-8")
    td = tempfile.mkdtemp(prefix="submission_build.")
    tmp_html = Path(td) / "submission.print.html"
    tmp_html.write_text(inject_print_css(mark_appendix_start(src)), encoding="utf-8")
    log = Path(td) / "chrome.log"
    cmd = [
        chrome,
        "--headless=old",
        "--disable-gpu", "--disable-software-rasterizer",
        "--disable-background-networking", "--disable-component-update",
        "--disable-sync", "--no-first-run", "--no-default-browser-check",
        "--metrics-recording-only", "--mute-audio",
        "--user-data-dir=%s" % (Path(td) / "profile"),
        "--no-pdf-header-footer",
        "--virtual-time-budget=15000",
        "--print-to-pdf=%s" % out_pdf,
        tmp_html.as_uri(),
    ]
    logf = open(log, "wb")
    proc = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT,
                            start_new_session=True)
    try:
        import time
        stable_since = None
        last_size = -1
        start = time.time()
        while time.time() - start < deadline_s:
            if proc.poll() is not None and not out_pdf.exists():
                tail = _tail(log)
                return False, "chrome exited %s with no PDF: %s" % (proc.returncode, tail)
            if out_pdf.exists():
                size = out_pdf.stat().st_size
                if size > 0 and size == last_size:
                    if stable_since and time.time() - stable_since > 1.5:
                        return True, ""
                    stable_since = stable_since or time.time()
                else:
                    stable_since = None
                last_size = size
            time.sleep(0.5)
        return False, "chrome did not finish a stable PDF within %d s: %s" % (
            deadline_s, _tail(log))
    finally:
        logf.close()
        _kill_tree(proc)
        shutil.rmtree(td, ignore_errors=True)


def _tail(path: Path, n: int = 4) -> str:
    try:
        lines = path.read_text(errors="replace").strip().splitlines()
        return " / ".join(lines[-n:]) or "(no output)"
    except OSError:
        return "(no log)"


def _kill_tree(proc: "subprocess.Popen") -> None:
    import os
    import signal
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        try:
            proc.kill()
        except ProcessLookupError:
            pass


# --------------------------------------------------------------------------
# PDF analysis  (only pdf_to_pages() needs pdfplumber)
# --------------------------------------------------------------------------

@dataclass
class RenderedPage:
    width: float
    height: float
    text: str
    char_sizes: List[float] = field(default_factory=list)
    # (x0, x1, word) for every extracted word -- TASK-0342's clipping check.
    # Content genuinely clipped by an overflow:hidden/auto box leaves no trace
    # here (it was never painted); this instead catches the failure mode the
    # fix itself could introduce -- something that, once allowed to reflow
    # instead of being clipped, spills PAST the printable margin instead.
    words: List[Tuple[float, float, str]] = field(default_factory=list)


def pdf_to_pages(pdf_path: Path) -> List[RenderedPage]:
    import logging
    logging.getLogger("pdfminer").setLevel(logging.ERROR)  # silence FontBBox noise
    import pdfplumber  # lazy: dev-only dependency
    pages: List[RenderedPage] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for p in pdf.pages:
            sizes = [round(float(c.get("size", 0.0)), 1)
                     for c in p.chars if c.get("size")]
            words = [(float(w["x0"]), float(w["x1"]), w["text"])
                     for w in p.extract_words()]
            pages.append(RenderedPage(
                width=float(p.width), height=float(p.height),
                text=(p.extract_text() or ""), char_sizes=sizes, words=words))
    return pages


def _first_appendix_page(pages: List[RenderedPage]) -> Optional[int]:
    for i, pg in enumerate(pages, start=1):
        if _APPENDIX_MARKER_TOKEN in pg.text:
            return i
    return None


def _dominant_font(pages: List[RenderedPage]) -> Tuple[Optional[float], int, List[float]]:
    """Return (modal size, count of chars < MIN_FONT_PT, sorted small sizes)."""
    hist: Dict[float, int] = {}
    small = 0
    small_sizes: set = set()
    for pg in pages:
        for s in pg.char_sizes:
            if s <= 0:
                continue
            hist[s] = hist.get(s, 0) + 1
            if s < MIN_FONT_PT - 0.05:
                small += 1
                small_sizes.add(s)
    if not hist:
        return None, 0, []
    modal = max(hist, key=lambda k: hist[k])
    return modal, small, sorted(small_sizes)


def _clipping_violations(pages: List[RenderedPage],
                         max_examples: int = 5) -> Tuple[int, List[str]]:
    """(count, up-to-max_examples "pN: 'word' Xpt past the margin" strings)."""
    right_bound = A4_PT[0] - MARGIN_RIGHT_PT
    left_bound = MARGIN_LEFT_PT
    count = 0
    examples: List[str] = []
    for i, pg in enumerate(pages, start=1):
        for x0, x1, word in pg.words:
            over_right = x1 - (right_bound + CLIP_TOLERANCE_PT)
            over_left = (left_bound - CLIP_TOLERANCE_PT) - x0
            over = max(over_right, over_left)
            if over > 0:
                count += 1
                if len(examples) < max_examples:
                    side = "right" if over_right >= over_left else "left"
                    examples.append("p%d: %r overflows the %s margin by %.1f pt"
                                    % (i, word, side, over))
    return count, examples


@dataclass
class Check:
    name: str
    status: str          # PASS | FAIL | WARN
    detail: str


def analyze(pages: List[RenderedPage]) -> Dict:
    total = len(pages)
    appx_start = _first_appendix_page(pages)
    if appx_start is None:
        body_pages, appx_pages = total, 0
    else:
        body_pages, appx_pages = appx_start - 1, total - (appx_start - 1)
    modal, small_ct, small_sizes = _dominant_font(pages)
    clip_ct, clip_examples = _clipping_violations(pages)
    size_ok = bool(pages) and all(
        abs(p.width - A4_PT[0]) <= PAGE_SIZE_TOL_PT
        and abs(p.height - A4_PT[1]) <= PAGE_SIZE_TOL_PT
        for p in pages)
    return {
        "total_pages": total,
        "body_pages": body_pages,
        "appendix_pages": appx_pages,
        "appendix_starts_on_page": appx_start,
        "page_size_pt": [round(pages[0].width, 1), round(pages[0].height, 1)] if pages else None,
        "page_size_is_a4": size_ok,
        "modal_font_pt": modal,
        "chars_below_min_font": small_ct,
        "small_font_sizes_pt": small_sizes,
        "clipping_violation_count": clip_ct,
        "clipping_examples": clip_examples,
    }


def evaluate(analysis: Dict) -> Tuple[str, List[Check]]:
    checks: List[Check] = []

    checks.append(Check(
        "paper size",
        "PASS" if analysis["page_size_is_a4"] else "FAIL",
        "A4 (%s x %s pt)" % tuple(analysis["page_size_pt"]) if analysis["page_size_pt"]
        else "no pages"))

    b = analysis["body_pages"]
    checks.append(Check(
        "body pages",
        "PASS" if b <= MAX_BODY_PAGES else "FAIL",
        "%d / %d%s" % (b, MAX_BODY_PAGES,
                       "" if analysis["appendix_starts_on_page"]
                       else "  (no #appendix marker found in the render -- whole doc counted as body)")))

    a = analysis["appendix_pages"]
    checks.append(Check(
        "appendix pages",
        "PASS" if a <= MAX_APPENDIX_PAGES else "FAIL",
        "%d / %d" % (a, MAX_APPENDIX_PAGES)))

    modal = analysis["modal_font_pt"]
    if modal is None:
        checks.append(Check("body font", "FAIL", "no text extracted from the PDF"))
    elif modal < MIN_FONT_PT - 0.05:
        checks.append(Check("body font", "FAIL",
                            "dominant body text is %.1f pt (min %.0f pt)" % (modal, MIN_FONT_PT)))
    else:
        checks.append(Check("body font", "PASS",
                            "%.1f pt (min %.0f pt)" % (modal, MIN_FONT_PT)))

    small = analysis["chars_below_min_font"]
    if small:
        sizes = ", ".join("%.1f" % s for s in analysis["small_font_sizes_pt"])
        checks.append(Check(
            "small text", "WARN",
            "%d characters < %.0f pt (sizes: %s pt). Chips/headers/eyebrow/"
            "meta/foot/code are floored to 10.5pt by the injected stylesheet "
            "(TASK-0342). Confirmed residual sources, left alone deliberately: "
            "the S6 SVG pipeline diagram's labels (scale with the vector "
            "graphic's own coordinate system -- a CSS font-size floor changes "
            "the source value the SVG then re-scales, not the rendered size) "
            "and <sup> exponents (conventionally smaller than body text "
            "everywhere, flooring them would look broken, not fixed). If a "
            "size appears here that ISN'T one of those two, the selector "
            "list is incomplete again -- re-measure with pdfplumber, don't "
            "assume" % (small, MIN_FONT_PT, sizes)))

    clip = analysis["clipping_violation_count"]
    checks.append(Check(
        "no horizontal overflow",
        "PASS" if clip == 0 else "FAIL",
        "0 words past the printable margin" if clip == 0 else
        "%d word(s) past the printable margin -- %s%s" % (
            clip, "; ".join(analysis["clipping_examples"]),
            " ..." if clip > len(analysis["clipping_examples"]) else "")))

    if any(c.status == "FAIL" for c in checks):
        return "FAIL", checks
    return "PASS", checks


# --------------------------------------------------------------------------
# change report  (reuses doc_parity's extractors)
# --------------------------------------------------------------------------

def _sections(html: str) -> Dict[str, int]:
    """{normalised h2 heading -> word count of that section's text}."""
    out: Dict[str, int] = {}
    parts = re.split(r"(?i)(?=<h2\b)", html)
    for chunk in parts:
        m = re.match(r"(?is)<h2\b[^>]*>(.*?)</h2>", chunk)
        if not m:
            continue
        raw_head = re.sub(r'(?is)<span class="sub".*?</span>', " ", m.group(1))
        head = _dp._norm_heading(re.sub(r"<[^>]+>", " ", raw_head))
        text, _, _ = _dp.html_to_text(chunk)
        out[head] = len(text.split())
    return out


def _appendix_headings(html: str) -> List[str]:
    idx = html.find(APPENDIX_MARKER)
    if idx == -1:
        return []
    _, heads, _ = _dp.html_to_text(html[idx:])
    return heads


def change_report(old_html: str, new_html: str) -> Dict:
    o_text, o_head, o_code = _dp.html_to_text(old_html)
    n_text, n_head, n_code = _dp.html_to_text(new_html)
    o_nums, n_nums = _dp.numbers(o_text), _dp.numbers(n_text)
    o_hset, n_hset = set(o_head), set(n_head)

    shared_o = [h for h in o_head if h in n_hset]
    shared_n = [h for h in n_head if h in o_hset]

    o_sec, n_sec = _sections(old_html), _sections(new_html)
    deltas = {}
    for h in set(o_sec) | set(n_sec):
        d = n_sec.get(h, 0) - o_sec.get(h, 0)
        if d:
            deltas[h] = d

    return {
        "figures_added": sorted(n_nums - o_nums),
        "figures_removed": sorted(o_nums - n_nums),
        "headings_added": [h for h in n_head if h not in o_hset],
        "headings_removed": [h for h in o_head if h not in n_hset],
        "headings_reordered": shared_o != shared_n,
        "identifiers_added": sorted(n_code - o_code),
        "identifiers_removed": sorted(o_code - n_code),
        "section_word_delta": dict(sorted(deltas.items(), key=lambda kv: -abs(kv[1]))),
        "appendix_split_before": _appendix_headings(old_html),
        "appendix_split_after": _appendix_headings(new_html),
    }


# --------------------------------------------------------------------------
# versioning + report rendering
# --------------------------------------------------------------------------

_VERSION_RE = re.compile(r"PHASE1_SUBMISSION_v(\d+)")


def next_version(outdir: Path) -> int:
    if not outdir.is_dir():
        return 1
    seen = [int(m.group(1)) for p in outdir.iterdir()
            for m in [_VERSION_RE.match(p.name)] if m]
    return (max(seen) + 1) if seen else 1


def _fmt_change(cr: Dict, verbose: bool) -> List[str]:
    lines: List[str] = []
    fa, fr = cr["figures_added"], cr["figures_removed"]
    if fa or fr:
        lines.append("  figures    +%d  -%d" % (len(fa), len(fr)))
        if fa:
            lines.append("    added    " + ", ".join(fa[:12] + (["..."] if len(fa) > 12 else [])))
        if fr:
            lines.append("    removed  " + ", ".join(fr[:12] + (["..."] if len(fr) > 12 else [])))
        lines.append("    (a changed value shows as one removed + one added)")
    ha, hr = cr["headings_added"], cr["headings_removed"]
    if ha:
        lines.append("  headings   +%d" % len(ha))
        for h in ha[:8]:
            lines.append("    added    \"%s\"" % h)
    if hr:
        lines.append("  headings   -%d" % len(hr))
        for h in hr[:8]:
            lines.append("    removed  \"%s\"" % h)
    if cr["headings_reordered"]:
        lines.append("  headings   REORDERED (shared headings appear in a different order)")
    ia, ir = cr["identifiers_added"], cr["identifiers_removed"]
    if ia or ir:
        lines.append("  code ids   +%d  -%d" % (len(ia), len(ir)))
        if verbose and ia:
            lines.append("    added    " + ", ".join(ia[:12]))
        if verbose and ir:
            lines.append("    removed  " + ", ".join(ir[:12]))
    deltas = cr["section_word_delta"]
    shown = [(h, d) for h, d in deltas.items() if verbose or abs(d) >= 5]
    if shown:
        lines.append("  sections (delta words%s)" % ("" if verbose else ", >= 5"))
        for h, d in shown[:12]:
            lines.append("    %+5d  %s" % (d, h))
    if cr["appendix_split_before"] != cr["appendix_split_after"]:
        lines.append("  appendix split  CHANGED")
        lines.append("    before: " + " | ".join(cr["appendix_split_before"]) or "    before: (none)")
        lines.append("    after:  " + " | ".join(cr["appendix_split_after"]) or "    after:  (none)")
    else:
        n = len(cr["appendix_split_after"])
        lines.append("  appendix split  unchanged (%d heading%s)" % (n, "" if n == 1 else "s"))
    if not lines:
        lines.append("  (no content changes detected by the doc_parity extractors)")
    return lines


def render_report(ctx: Dict, verbose: bool = False) -> str:
    a = ctx["analysis"]
    L: List[str] = []
    L.append("=" * 66)
    L.append("  PHASE1_SUBMISSION_v%d      built %s" % (ctx["version"], ctx["built_at"]))
    L.append("=" * 66)
    L.append("  source   %s" % ctx["source_rel"])
    L.append("  git      %s%s" % (ctx["git_sha"],
                                  "  + uncommitted changes to the HTML" if ctx["dirty"] else ""))
    L.append("  chrome   %s" % ctx["chrome_version"])
    L.append("  fonts    %s" % ("fetched online (fonts.gstatic.com reachable)"
                                if ctx["fonts_online"]
                                else "OFFLINE -- Georgia/system fallback, pagination may differ"))
    L.append("  pdf      %s  (%.2f MB)" % (ctx["pdf_rel"], ctx["pdf_mb"]))
    L.append("")
    L.append("COMPLIANCE")
    for c in ctx["checks"]:
        L.append("  [%-4s] %-15s %s" % (c.status, c.name, c.detail))
    if a["appendix_starts_on_page"]:
        L.append("  split rule: '#appendix' forced to a page break; "
                 "body = pages 1-%d, appendix = pages %d-%d"
                 % (a["body_pages"], a["appendix_starts_on_page"], a["total_pages"]))
    L.append("  NOTE (TASK-0342): 'no horizontal overflow' catches content spilling")
    L.append("  PAST the page margin. It cannot see content an overflow:hidden/auto box")
    L.append("  clips to nothing -- that leaves no trace in the PDF to check. Open the")
    L.append("  PDF once per structural change; don't rely on this check alone.")
    L.append("")
    if ctx.get("change") is not None:
        L.append("CHANGE SINCE %s" % ctx["since_ref"])
        L.extend(_fmt_change(ctx["change"], verbose))
    else:
        L.append("CHANGE SINCE %s: n/a (%s)" % (ctx["since_ref"], ctx["change_skip_reason"]))
    L.append("")
    warns = sum(1 for c in ctx["checks"] if c.status == "WARN")
    L.append("RESULT: %s%s" % (ctx["result"],
                               "  (%d warning%s)" % (warns, "" if warns == 1 else "s") if warns else ""))
    L.append("")
    L.append("  print stylesheet injected into a copy of the HTML (source untouched):")
    for line in PRINT_CSS.strip().splitlines():
        L.append("  | " + line)
    return "\n".join(L)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def build(html_path: Path, outdir: Path, since_ref: str,
          version: Optional[int], want_change: bool) -> Tuple[int, Dict]:
    if not html_path.is_file():
        return 2, {"error": "not a file: %s" % html_path}

    chrome = find_chrome()
    if not chrome:
        return 3, {"error": "no Chrome/Chromium found (looked for %s and PATH). "
                            "This tool is macOS-local by design." % CHROME_MACOS}
    try:
        import pdfplumber  # noqa: F401
    except ImportError:
        return 3, {"error": "pdfplumber not installed. Dev-only dependency: "
                            "%s/.venv/bin/pip install pdfplumber" % REPO_ROOT}

    outdir.mkdir(parents=True, exist_ok=True)
    ver = version if version is not None else next_version(outdir)
    sha = git_head_short()
    dirty = git_path_dirty(html_path)
    stem = "PHASE1_SUBMISSION_v%d_%s%s" % (ver, sha, "-dirty" if dirty else "")
    out_pdf = outdir / (stem + ".pdf")

    ok, err = render_pdf(chrome, html_path, out_pdf)
    if not ok:
        return 3, {"error": "render failed: %s" % err}

    pages = pdf_to_pages(out_pdf)
    analysis = analyze(pages)
    result, checks = evaluate(analysis)

    change = None
    skip_reason = ""
    if want_change:
        old = git_show(since_ref, html_path)
        if old is None:
            skip_reason = "'%s:%s' not in git history" % (since_ref, repo_rel(html_path))
        else:
            change = change_report(old, html_path.read_text(encoding="utf-8"))

    ctx = {
        "version": ver,
        "built_at": _dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source_rel": repo_rel(html_path),
        "git_sha": sha,
        "dirty": dirty,
        "chrome_version": chrome_version(chrome),
        "fonts_online": fonts_reachable(),
        "pdf_rel": repo_rel(out_pdf),
        "pdf_path": str(out_pdf),
        "pdf_mb": out_pdf.stat().st_size / 1e6,
        "analysis": analysis,
        "checks": checks,
        "result": result,
        "since_ref": since_ref,
        "change": change,
        "change_skip_reason": skip_reason,
    }
    return (0 if result == "PASS" else 1), ctx


def _json_safe(ctx: Dict) -> Dict:
    out = dict(ctx)
    out["checks"] = [vars(c) for c in ctx["checks"]]
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--html", type=Path, default=DEFAULT_HTML,
                    help="submission HTML twin (default: PHASE1_SUBMISSION_V1.html)")
    ap.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR,
                    help="where numbered PDFs land (default: documentation/_build)")
    ap.add_argument("--since", default="HEAD", metavar="GITREF",
                    help="change report compares against this ref (default: HEAD)")
    ap.add_argument("--version", type=int, default=None,
                    help="force the version number (default: max existing + 1)")
    ap.add_argument("--no-change-report", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args(argv)

    code, ctx = build(a.html.resolve(), a.outdir.resolve(), a.since,
                      a.version, not a.no_change_report)

    if "error" in ctx:
        if a.json:
            print(json.dumps({"exit": code, "error": ctx["error"]}, indent=2))
        else:
            print("submission_build: %s" % ctx["error"], file=sys.stderr)
        return code

    report = render_report(ctx, a.verbose)
    report_file = Path(ctx["pdf_path"]).with_suffix(".report.txt")
    report_file.write_text(report + "\n", encoding="utf-8")

    if a.json:
        print(json.dumps(_json_safe(ctx), indent=2, default=str))
    else:
        print(report)
        print("\n  report written to %s" % repo_rel(report_file))
    return code


if __name__ == "__main__":
    sys.exit(main())
