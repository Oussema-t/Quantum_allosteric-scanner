#!/usr/bin/env python3
"""One command: build a two-column LaTeX submission PDF, reusing submission_build.py's
compliance/report layer wholesale. TASK-0347.

WHY LATEX (the decision, stated once, here)

[[TASK-0341]]/[[TASK-0342]]/[[TASK-0344]] built a real, tested Chrome/HTML pipeline
and got the single-column submission to a compliant 6+3 pages. [[TASK-0347]] was
filed because that leaves no headroom -- every addition displaces something. Its
own fallback ("CSS multi-column costs one line of CSS on the validated pipeline")
was tried directly in `PHASE1_SUBMISSION_V2.html`'s source and, per that task's
own "Added 2026-09-08" section, produced a PDF whose page count this tool's own
checker could not trust. Separately (found by this thread, while verifying the
same fallback): `column-count` combined with this specific document's real
content also collapsed the dominant body font to ~7.5pt -- reproduced live,
confirmed NOT caused by column-count itself (persists with column-count:1), root
cause not identified after exhausting the obvious hypotheses (grid/columns,
tables, the ASCII diagram). Two independent, serious defects in one "one-line"
fallback is not a one-line fallback. LaTeX pagination is explicit (a `.aux`/page
counter, not CSS reflow an external tool has to reverse-engineer) and Tectonic
(https://tectonic-typesetting.github.io/) needs no multi-GB TeX Live install --
single bottled Homebrew formula, downloads only the packages a document actually
uses into a local cache. Confirmed live: ~105s on the very first compile
(package-cache population, needs network), 0.3s on every compile after --
dramatically faster and more reproducible than this session's repeated
headless-Chrome flakiness (60-120s+ hangs, Mach-port/sandbox errors, an
undiagnosed font bug). TeX Live/MacTeX was rejected for exactly the size/speed
reason the task's own text flagged. pandoc + Tectonic (not a hand-authored .tex)
was chosen over hand-authoring so `PHASE1_SUBMISSION_V2.md` stays the single
authored source -- LaTeX is GENERATED, not a third hand-maintained twin. This
satisfies the task's own explicit requirement ("Either LaTeX is generated from
the Markdown [preferred -- one authored source] ... three hand-maintained copies
... is precisely the failure doc_parity.py was built to prevent").

PIPELINE

    PHASE1_SUBMISSION_V2.md
        --pandoc-->  LaTeX body fragment
        --wrap in a template (twocolumn, A4, 10.5pt floor, table* for every
          table so nothing is squeezed into an 8cm column, an invisible
          appendix-page marker reusing submission_build's own token)-->
        --tectonic--> PDF
        --submission_build.py's own analyze()/evaluate()/render_report()-->
    a numbered PDF + the SAME report shape TASK-0341/0342/0344 already produced.

The compliance/report layer is NOT reimplemented -- `pdf_to_pages`, `analyze`,
`evaluate`, `render_report`, `next_version`, git-context helpers are imported and
called directly from `submission_build.py`. Page-count trust, the 10pt floor, and
the clipping/overflow check ("no horizontal overflow" -- LaTeX doesn't silently
clip like `overflow:hidden`; an overflowing table spills into the margin, which
this check already catches) all come from code already tested under TASK-0341/
0342, not duplicated. Only the CHANGE REPORT is format-specific: it diffs the
Markdown directly (the LaTeX source now) using `doc_parity.md_to_text` -- already
existing, already used by the HTML route's own parity check -- not a new
extractor.

DETERMINISM. `SOURCE_DATE_EPOCH` is set (Tectonic honours it; unset, it still
does not embed wall-clock timestamps the way vanilla pdfTeX does). Verified
directly, not assumed: two back-to-back compiles of the same input produce
byte-identical PDFs (see test_submission_build_latex.py).

TABLES. Every pandoc-emitted table is rewritten from `longtable` (pandoc's
default, which is a single-column-safe multi-page table macro -- exactly the
"squeezed into an 8cm column" risk the task warned about) to `table*` (spans
both columns, full text width) by a small, targeted regex pass -- not a general
LaTeX parser, scoped to the specific shape pandoc's LaTeX writer produces for a
plain pipe-table with no caption (confirmed against this document's own real
tables, not assumed from pandoc's docs).

DIAGRAM. The ASCII pipeline diagram (S6) is kept verbatim, not redrawn in TikZ
(task's own "motivation is density, not typesetting quality" -- a TikZ redraw
buys nothing this deliverable needs) and set full-width via `figure*` +
`verbatim`, matching the tables' own full-width treatment.

EXIT CODES: same contract as submission_build.py --
  0 built, PASS (warnings allowed) / 1 built, FAIL / 2 usage / 3 environment

Run:   .ai/tools/submission_build_latex.py
       .ai/tools/submission_build_latex.py --json
Test:  python3 -m pytest .ai/tools/test_submission_build_latex.py
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import doc_parity as _dp                    # reuse: md_to_text, numbers, _norm_heading
import submission_build as _sb              # reuse: pdf_to_pages/analyze/evaluate/report/git ctx

REPO_ROOT = _sb.REPO_ROOT
DEFAULT_MD = REPO_ROOT / "__WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V2.md"
DEFAULT_OUTDIR = REPO_ROOT / "__WORK_IN_PROGRESS__/documentation/_build_latex"

# Body font: 10.5pt, matching the HTML route's own established convention
# (TASK-0342/0344 -- one consistent size across both pipelines, not two
# different "clears the floor" numbers). `article` only offers 10/11/12pt
# discretely; \normalsize is redefined explicitly rather than relying on a
# class option landing exactly on the target.
BODY_FONT_PT = 10.5
BODY_LEADING_PT = 13.5
MARGIN_MM = 15.0

# Reuse submission_build's own invisible-marker mechanism for the appendix
# split -- same failure mode (searching rendered prose for a heading word) is
# just as possible in a LaTeX-produced PDF as it was in the HTML one
# (TASK-0342's corrected-live lesson). One token, one detector, two renderers.
_APPENDIX_MARKER_TOKEN = _sb._APPENDIX_MARKER_TOKEN

LATEX_PREAMBLE = r"""\documentclass[10pt,a4paper,twocolumn]{article}
%% ===== generated by submission_build_latex.py (TASK-0347) -- not hand-edited =====
%% fontspec, not fontenc/inputenc: Tectonic's engine is XeTeX, which handles
%% Unicode natively. fontenc/inputenc force legacy 8-bit TFM fonts and were
%% confirmed live to be the CAUSE of "Missing character" errors on plain
%% prose Unicode (em/en dash, curly quotes) -- fontspec + Latin Modern's own
%% OTF variant (its XeTeX-native default, no \setmainfont override needed)
%% has full coverage for those. The narrower math-symbol gap (minus sign,
%% >=, etc.) is closed separately in _preprocess_markdown, not by font choice.
\usepackage{fontspec}
\usepackage[margin=%(margin)smm]{geometry}
%% Reviewer thread, 2026-09-08: the mandated seven items already carry their
%% own numbers in the source ("## 1. Problem Framing"), and pandoc maps `#` to
%% \section / `##` to \subsection, so LaTeX's automatic numbering rendered them
%% as "1.1 1. Problem Framing". Suppressing LaTeX numbering keeps the mandated
%% 1--7 exactly as the Guidelines require, rather than renumbering them.
\setcounter{secnumdepth}{0}
\usepackage{booktabs}
\usepackage{array}
\usepackage{calc}
\usepackage{xcolor}
\usepackage{hyperref}
\hypersetup{colorlinks=true,linkcolor=black,urlcolor=black,citecolor=black,
  pdfcreator={},pdfproducer={}}
\usepackage{fancyvrb}
%% pandoc's own default template defines \tightlist for compact list items;
%% this custom preamble doesn't inherit it, so pandoc's output references an
%% undefined control sequence without this -- confirmed by actually
%% compiling, not found by reading pandoc's LaTeX writer source.
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\renewcommand{\normalsize}{\fontsize{%(fontpt)s}{%(leadpt)s}\selectfont}
\normalsize
\setlength{\parskip}{0.35em}
\setlength{\parindent}{0pt}
\pagestyle{empty}
\begin{document}
"""

LATEX_POSTAMBLE = r"""
\end{document}
"""


# --------------------------------------------------------------------------
# environment
# --------------------------------------------------------------------------

def find_pandoc() -> Optional[str]:
    return shutil.which("pandoc")


def find_tectonic() -> Optional[str]:
    return shutil.which("tectonic")


def pandoc_version(pandoc: str) -> str:
    r = subprocess.run([pandoc, "--version"], capture_output=True, text=True)
    return (r.stdout or "").splitlines()[0] if r.stdout else "unknown"


def tectonic_version(tectonic: str) -> str:
    r = subprocess.run([tectonic, "--version"], capture_output=True, text=True)
    return r.stdout.strip() or "unknown"


# --------------------------------------------------------------------------
# markdown -> latex body
# --------------------------------------------------------------------------

# Confirmed by actually compiling (not assumed from a font's advertised
# coverage): plain XeTeX/Latin-Modern text mode is missing these glyphs --
# "Missing character" errors for U+2212/U+2265 etc. Converted to LaTeX math
# macros, which every math font carries, rather than chasing a text font with
# full Unicode symbol coverage. Applied OUTSIDE fenced code blocks only (see
# _preprocess_markdown) -- none of these appear inside this document's PDB
# codes/identifiers, confirmed by the same character census that built this
# table (`grep`+`unicodedata.name` over the real .md, not guessed).
# `$...$` was the first attempt and is WRONG -- confirmed live: pandoc's
# tex_math_dollars extension only treats `$...$` as math when the content
# passes its own "looks like real math, not currency" heuristic, and a bare
# `$-$` fails that heuristic. It came through as four literal, visible
# dollar-sign characters in the rendered PDF ("$-$0.34"), not a minus sign --
# caught by looking at the rendered PDF (this file's own module docstring's
# "verify by rendering" rule, TASK-0342's lesson applied here too), not by
# reading pandoc's output. Fixed with pandoc's raw-attribute inline syntax
# (`` `<latex>`{=latex} ``, part of its default extension set) instead, which
# passes the enclosed LaTeX through completely unescaped regardless of any
# math-content heuristic -- confirmed directly against pandoc's own output.
def _raw_latex(cmd: str) -> str:
    return "`%s`{=latex}" % cmd


_MATH_SUBSTITUTIONS = {
    "−": "-",                                    # MINUS SIGN -- plain text
                                                  # hyphen reads fine in prose,
                                                  # no math wrapping needed
    "≥": _raw_latex("\\ensuremath{\\geq}"),
    "≤": _raw_latex("\\ensuremath{\\leq}"),
    "×": _raw_latex("\\ensuremath{\\times}"),
    "→": _raw_latex("\\ensuremath{\\rightarrow}"),
    "·": _raw_latex("\\ensuremath{\\cdot}"),
    "ρ": _raw_latex("\\ensuremath{\\rho}"),
    "§": _raw_latex("\\S{}"),
    "≈": _raw_latex("\\ensuremath{\\approx}"),   # was MISSING -- rendered as a
                                                # tofu box in V3, silently turning
                                                # "rho ~ 0.95" into "rho [] 0.95"
    # Added 2026-09-09: the finite-delay observable `2·Re⟨r|e^{-iHτ}|a⟩` shipped
    # inside a \texttt{} span, where the mono font has no glyph for any of these
    # three -- caught by check_glyph_coverage as 3 tofu boxes, not by eye.
    "τ": _raw_latex("\\ensuremath{\\tau}"),
    "⟨": _raw_latex("\\ensuremath{\\langle}"),
    "⟩": _raw_latex("\\ensuremath{\\rangle}"),
}
_SUPERSCRIPT_DIGITS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹",
                                    "0123456789")
_SUPERSCRIPT_RUN_RE = re.compile(r"[⁰¹²³⁴-⁹]+")

# The ASCII pipeline diagram (S6) uses Unicode box-drawing, which a monospace
# text font is even less likely to carry than the math symbols above --
# transliterated to plain ASCII instead of chasing a font with box-drawing
# coverage, matching the task's own "motivation is density, not typesetting
# quality": a plain-ASCII box diagram is a normal, portable technical-doc
# convention, not a downgrade that needs excusing.
_BOX_DRAWING_ASCII = {
    "─": "-", "│": "|", "┌": "+", "┐": "+",
    "└": "+", "┘": "+", "┬": "+", "┴": "+",
    "├": "+", "┤": "+", "┼": "+",
    "▼": "v", "▶": ">", "◀": "<", "▲": "^",
}

_FENCE_RE = re.compile(r"(?ms)^```.*?\n(.*?)^```\s*$")


def _preprocess_markdown(md_text: str) -> str:
    """A COPY-only transform (never touches the source file): math-ish
    Unicode -> LaTeX macros in prose, box-drawing Unicode -> plain ASCII
    inside fenced code blocks. Confirmed necessary by actually compiling
    (see _MATH_SUBSTITUTIONS docstring), not assumed from reading pandoc's
    or a font's documentation."""
    def fence_repl(m: "re.Match") -> str:
        block = m.group(0)
        for uni, ascii_ in _BOX_DRAWING_ASCII.items():
            block = block.replace(uni, ascii_)
        return block

    out = _FENCE_RE.sub(fence_repl, md_text)

    # Math substitutions must skip fenced blocks (a diagram legend could
    # contain a literal "-" that's already correct ASCII, but more
    # generally: fence content is verbatim by definition, nothing in it
    # should be rewritten a second time). Split out the fences again --
    # cheap, and keeps this pass independent of the transliteration above
    # rather than threading state through one combined regex.
    parts = re.split(r"(?ms)(^```.*?^```\s*$)", out)
    rebuilt = []
    for part in parts:
        if part.startswith("```"):
            rebuilt.append(part)
            continue
        for uni, repl in _MATH_SUBSTITUTIONS.items():
            part = part.replace(uni, repl)
        # \textsuperscript, not $^{...}$: same raw-attribute reasoning as
        # _MATH_SUBSTITUTIONS above (a bare digit run in $...$ risks the same
        # math-heuristic rejection the minus sign hit), and semantically this
        # is a superscript numeral in running text, not inline math.
        part = _SUPERSCRIPT_RUN_RE.sub(
            lambda m: _raw_latex("\\textsuperscript{%s}"
                                 % m.group(0).translate(_SUPERSCRIPT_DIGITS)),
            part)
        rebuilt.append(part)
    return "".join(rebuilt)


_ALLOWED_NON_ASCII = set(
    "—–‘’“”…·°±×÷−≈≥≤→←↔⁰¹²³⁴⁵⁶⁷⁸⁹§"          # covered by the tables above
    "áàâäãåéèêëíìîïóòôöõúùûüñçšžøåæœÁÀÂÄÉÈÊËÍÎÏÓÔÖÚÜÑÇ"   # Latin-1-ish, XeTeX handles
    "ρσμλαβγδπθΔΣΩτ⟨⟩"                              # greek used in prose
)


def check_citations(md_text: str) -> list:
    """Every inline [n] marker must resolve to a numbered entry in the
    reference list, and every listed reference should be cited. Added
    2026-09-09 at the repo owner's request: the citations were added by hand
    and nothing checked that [7] is the paper the sentence means. This does
    NOT verify a reference is correct -- only that the numbering is
    self-consistent, which is the part a machine can settle."""
    import re as _re
    cited = set()
    for m in _re.finditer(r"\[(\d+(?:\s*,\s*\d+)*)\]", md_text):
        for n in m.group(1).split(","):
            cited.add(int(n.strip()))
    listed = {int(m.group(1))
              for m in _re.finditer(r"^(\d+)\.\s+\S", md_text, _re.M)}
    problems = []
    dangling = sorted(cited - listed)
    if dangling:
        problems.append("cited but not in the reference list: %s"
                        % ", ".join("[%d]" % n for n in dangling))
    uncited = sorted(listed - cited)
    if uncited:
        problems.append("listed but never cited: %s"
                        % ", ".join(str(n) for n in uncited))
    return problems


def check_glyph_coverage(md_text: str) -> list:
    """Every non-ASCII character that would reach LaTeX without a known
    rendering. Added 2026-09-09 after `≈` shipped in V3 as a tofu box: the
    substitution table silently passes through anything it does not know, and
    the failure is invisible in the source and easy to miss in the PDF. This
    turns that class of defect into a build failure naming the character."""
    bad = {}
    for ch in md_text:
        if ord(ch) > 127 and ch not in _ALLOWED_NON_ASCII:
            bad[ch] = bad.get(ch, 0) + 1
    return sorted(bad.items(), key=lambda kv: -kv[1])


def md_to_latex_body(pandoc: str, md_text: str) -> str:
    r = subprocess.run([pandoc, "-f", "markdown", "-t", "latex", "--wrap=preserve"],
                       input=md_text, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("pandoc failed: %s" % (r.stderr or r.stdout))
    return r.stdout


# Matches pandoc's longtable wrapper for a plain, uncaptioned pipe-table:
#   {\def\LTcaptype{none} ... \n\begin{longtable}[]{@{}<colspec>@{}}
#   \toprule\noalign{}
#   <header minipages> \\
#   \midrule\noalign{}
#   \endhead
#   \bottomrule\noalign{}
#   \endlastfoot
#   <body rows>
#   \end{longtable}
#   }
# Confirmed against this document's own real pandoc output (module docstring),
# not written from pandoc's documentation alone.
_LONGTABLE_RE = re.compile(
    r"\{\\def\\LTcaptype\{none\}[^\n]*\n"
    r"\\begin\{longtable\}\[\]\{@\{\}\s*(?P<colspec>.*?)@\{\}\}\n"
    r"\\toprule\\noalign\{\}\n"
    r"(?P<header>.*?)\n"
    r"\\midrule\\noalign\{\}\n"
    r"\\endhead\n"
    r"\\bottomrule\\noalign\{\}\n"
    r"\\endlastfoot\n"
    r"(?P<body>.*?)"
    r"\\end\{longtable\}\n\}",
    re.S)

_MINIPAGE_CELL_RE = re.compile(
    r"\\begin\{minipage\}\[b\]\{\\linewidth\}\\raggedright\n(.*?)\n\\end\{minipage\}",
    re.S)


def _flatten_header(header: str) -> str:
    """Strip pandoc's per-cell minipage wrapper down to plain cell text --
    the table* column spec already carries the width/alignment, a minipage
    per header cell is redundant and just adds vertical padding."""
    return _MINIPAGE_CELL_RE.sub(lambda m: m.group(1).strip(), header)


def widen_tables_to_full_width(tex: str) -> str:
    """Rewrite every pandoc longtable (single-column-safe, exactly the
    "squeezed into an 8cm column" risk TASK-0347 warned about) into a table*
    spanning both columns, full text width -- for every table uniformly, not
    a per-table judgment call, since a narrow column can squeeze any of them."""
    def repl(m: "re.Match") -> str:
        colspec = m.group("colspec").strip()
        header = _flatten_header(m.group("header").strip())
        body = m.group("body").strip()
        # `header` already ends in its own line-break marker (captured
        # verbatim from pandoc's "...\end{minipage} \\" line) -- appending
        # another "\\\\" here double-escapes it into 4 backslashes, a real
        # bug caught by actually compiling, not by reading the regex.
        return (
            # No \small here (first version had it, measured 9pt, FAILED the
            # floor): Guidelines S5's 10pt minimum has no table exemption --
            # TASK-0342 found and fixed the identical mistake in the HTML
            # route. Left at \normalsize (10.5pt) instead.
            "\\begin{table*}[t]\n\\centering\n"
            "\\begin{tabular}{@{}%s@{}}\n\\toprule\n%s\n\\midrule\n%s\n"
            "\\bottomrule\n\\end{tabular}\n\\end{table*}\n"
            % (colspec, header, body)
        )
    out, n = _LONGTABLE_RE.subn(repl, tex)
    return out


_VERBATIM_RE = re.compile(r"\\begin\{verbatim\}\n(.*?)\\end\{verbatim\}", re.S)


def widen_code_blocks(tex: str) -> str:
    """pandoc emits a fenced code block with no language tag as plain
    \\begin{verbatim}...\\end{verbatim} -- this document's ASCII diagram is
    exactly that. verbatim can't cross a column boundary or be resized by a
    wrapping macro; span it full-width via `figure*` (a starred float is the
    native twocolumn-class mechanism, no `multicol` package needed), matching
    TASK-0347's own instruction ("verbatim in a narrow column will not fit").
    Every verbatim block is treated this way, not just the one diagram this
    document happens to have today."""
    def repl(m: "re.Match") -> str:
        # Same floor reasoning as the table fix above: no \small.
        return ("\\begin{figure*}[t]\\centering\n\\begin{verbatim}\n%s"
                "\\end{verbatim}\n\\end{figure*}\n" % m.group(1))
    return _VERBATIM_RE.sub(repl, tex)


def mark_appendix_start(tex: str, appendix_heading_pattern: Optional[str]) -> str:
    """Insert the shared invisible marker right after the LaTeX section
    command matching `appendix_heading_pattern` (a literal substring to find,
    e.g. "Appendix A"). No-op if not found or not requested -- matches
    submission_build.mark_appendix_start's own no-op contract.

    TASK-0349: `_APPENDIX_MARKER_TOKEN` ("SUBMISSION_BUILD_APPENDIX_START_
    7f3a9c") is shared verbatim with the HTML route, where `_` is an
    ordinary character inside a <span>. In raw LaTeX text mode `_` is the
    math-mode subscript operator -- writing the token unescaped here always
    produced "Missing $ inserted" and an unrecoverable XeTeX halt (confirmed
    live, this task's own bisection). This branch had never compiled once
    before this fix -- every prior build reported "no #appendix marker
    found", so the insertion code ran for the first time here. Escaping is
    done in THIS module, not by changing the shared token itself, since the
    HTML route's literal underscores are correct there and must stay that
    way -- the two routes need different escaping of the same logical
    token, not a different token."""
    if not appendix_heading_pattern:
        return tex
    idx = tex.find(appendix_heading_pattern)
    if idx == -1:
        return tex
    line_end = tex.find("\n", idx)
    if line_end == -1:
        return tex
    latex_safe_token = _APPENDIX_MARKER_TOKEN.replace("_", r"\_")
    marker = ("\n{\\color{white}\\fontsize{%s}{%s}\\selectfont %s}\n"
             % (BODY_FONT_PT, BODY_LEADING_PT, latex_safe_token))
    return tex[:line_end + 1] + marker + tex[line_end + 1:]


def build_latex_source(pandoc: str, md_path: Path,
                       appendix_heading_pattern: Optional[str] = None) -> str:
    md_text = _preprocess_markdown(md_path.read_text(encoding="utf-8"))
    body = md_to_latex_body(pandoc, md_text)
    body = widen_tables_to_full_width(body)
    body = widen_code_blocks(body)
    body = mark_appendix_start(body, appendix_heading_pattern)
    preamble = LATEX_PREAMBLE % {"margin": MARGIN_MM, "fontpt": BODY_FONT_PT,
                                 "leadpt": BODY_LEADING_PT}
    return preamble + body + LATEX_POSTAMBLE


# --------------------------------------------------------------------------
# compile
# --------------------------------------------------------------------------

def compile_latex(tectonic: str, tex_path: Path, out_pdf: Path,
                  deadline_s: int = 180) -> Tuple[bool, str]:
    env = dict(os.environ)
    env.setdefault("SOURCE_DATE_EPOCH", "1735689600")  # 2025-01-01 -- fixed, arbitrary, stated
    outdir = out_pdf.parent
    outdir.mkdir(parents=True, exist_ok=True)
    # -Z deterministic-mode: SOURCE_DATE_EPOCH alone removed the
    # CreationDate/ModDate but NOT the xref /ID (confirmed live -- two
    # otherwise-identical compiles differed only in that one field, a random
    # MD5 xdvipdfmx generates per run). This flag closes that gap; its
    # documented cost (SyncTeX's absolute paths) is irrelevant here, SyncTeX
    # is never requested.
    # TASK-0349: `--keep-logs` -- without it, a FAILED compile leaves no
    # `.log` on disk at all (confirmed live: tectonic prints the XeTeX
    # transcript to stdout/stderr but writes no file unless asked, even
    # though it claims "Transcript written to ...log"). The tool's own
    # `.tex` is already retained regardless of outcome (`build()` writes it
    # before calling this function) -- this closes the matching gap on the
    # `.log` side, so a failed compile no longer destroys its own evidence.
    cmd = [tectonic, "-Z", "deterministic-mode", "--keep-logs", "-o", str(outdir), str(tex_path)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=deadline_s, env=env)
    except subprocess.TimeoutExpired:
        return False, "tectonic timed out after %d s" % deadline_s
    produced = outdir / (tex_path.stem + ".pdf")
    if r.returncode != 0 or not produced.is_file():
        tail = (r.stdout or r.stderr or "").strip().splitlines()[-15:]
        log_path = outdir / (tex_path.stem + ".log")
        log_note = (" (full transcript: %s)" % log_path) if log_path.is_file() else \
                   " (no .log produced -- tectonic failed before writing one)"
        return False, "tectonic exited %s: %s%s" % (r.returncode, " | ".join(tail), log_note)
    if produced != out_pdf:
        produced.replace(out_pdf)
    return True, ""


# --------------------------------------------------------------------------
# change report (format-specific: diffs Markdown, reusing doc_parity)
# --------------------------------------------------------------------------

def _sections_md(md_text: str) -> Dict[str, int]:
    """{normalised ## heading -> word count}, mirroring submission_build's
    own _sections() but split on markdown '##' instead of HTML '<h2'."""
    out: Dict[str, int] = {}
    parts = re.split(r"(?m)(?=^##\s)", md_text)
    for chunk in parts:
        m = re.match(r"(?m)^##\s+(.+?)\s*$", chunk)
        if not m:
            continue
        head = _dp._norm_heading(m.group(1))
        text, _, _ = _dp.md_to_text(chunk)
        out[head] = len(text.split())
    return out


def _appendix_headings_md(md_text: str) -> List[str]:
    """Headings from the first one whose normalised text starts with
    'appendix' onward -- mirrors submission_build._appendix_headings, which
    finds the same thing in HTML via the #appendix id. Markdown has no id
    attribute to anchor on, so this uses the heading text itself; unlike
    _first_appendix_page's PDF-search (TASK-0342's corrected lesson), this
    operates on the SOURCE, not rendered prose, so an inline body citation of
    the word "appendix" cannot false-positive it -- only an actual heading can."""
    _, heads, _ = _dp.md_to_text(md_text)
    for i, h in enumerate(heads):
        if h.startswith("appendix"):
            return heads[i:]
    return []


def change_report_md(old_md: str, new_md: str) -> Dict:
    o_text, o_head, o_code = _dp.md_to_text(old_md)
    n_text, n_head, n_code = _dp.md_to_text(new_md)
    o_nums, n_nums = _dp.numbers(o_text), _dp.numbers(n_text)
    o_hset, n_hset = set(o_head), set(n_head)
    o_sec, n_sec = _sections_md(old_md), _sections_md(new_md)
    deltas = {}
    for h in set(o_sec) | set(n_sec):
        d = n_sec.get(h, 0) - o_sec.get(h, 0)
        if d:
            deltas[h] = d
    shared_o = [h for h in o_head if h in n_hset]
    shared_n = [h for h in n_head if h in o_hset]
    return {
        "figures_added": sorted(n_nums - o_nums),
        "figures_removed": sorted(o_nums - n_nums),
        "headings_added": [h for h in n_head if h not in o_hset],
        "headings_removed": [h for h in o_head if h not in n_hset],
        "headings_reordered": shared_o != shared_n,
        "identifiers_added": sorted(n_code - o_code),
        "identifiers_removed": sorted(o_code - n_code),
        "section_word_delta": dict(sorted(deltas.items(), key=lambda kv: -abs(kv[1]))),
        "appendix_split_before": _appendix_headings_md(old_md),
        "appendix_split_after": _appendix_headings_md(new_md),
    }


def _relabel_small_text_check(check: "_sb.Check") -> "_sb.Check":
    """submission_build.evaluate() is reused as-is (page/appendix/font-floor/
    clipping logic all apply unchanged -- see the module docstring), but its
    "small text" explanation names HTML-specific causes (an SVG diagram, a CSS
    floor) that don't exist in a LaTeX render. Re-labelled here rather than
    forking evaluate() itself, which stays the one tested implementation both
    routes share."""
    if check.name != "small text":
        return check
    m = re.match(r"(\d+) characters < ([\d.]+) pt \(sizes: ([^)]+) pt\)", check.detail)
    if not m:
        return check
    count, floor, sizes = m.groups()
    return _sb.Check(
        "small text", check.status,
        "%s characters < %s pt (sizes: %s pt). Nothing in this template is "
        "deliberately shrunk below \\normalsize (%.1fpt) -- re-render and "
        "grep the .tex for \\small/\\footnotesize/\\scriptsize near the "
        "reported sizes to find the source; it is new, not an accepted "
        "residual the way the HTML route's SVG-diagram/superscript case was"
        % (count, floor, sizes, BODY_FONT_PT))


# --------------------------------------------------------------------------
# main build
# --------------------------------------------------------------------------

def build(md_path: Path, outdir: Path, since_ref: str, version: Optional[int],
         want_change: bool, appendix_heading_pattern: Optional[str] = None,
         deadline_s: int = 180) -> Tuple[int, Dict]:
    if not md_path.is_file():
        return 2, {"error": "not a file: %s" % md_path}

    pandoc = find_pandoc()
    if not pandoc:
        return 3, {"error": "pandoc not found (brew install pandoc)"}
    tectonic = find_tectonic()
    if not tectonic:
        return 3, {"error": "tectonic not found (brew install tectonic)"}
    try:
        import pdfplumber  # noqa: F401
    except ImportError:
        return 3, {"error": "pdfplumber not installed (dev-only dep, same as the HTML route): "
                            "%s/.venv/bin/pip install pdfplumber" % REPO_ROOT}

    outdir.mkdir(parents=True, exist_ok=True)
    ver = version if version is not None else _sb.next_version(outdir)
    sha = _sb.git_head_short()
    dirty = _sb.git_path_dirty(md_path)
    stem = "PHASE1_SUBMISSION_LATEX_v%d_%s%s" % (ver, sha, "-dirty" if dirty else "")
    tex_path = outdir / (stem + ".tex")
    out_pdf = outdir / (stem + ".pdf")

    try:
        tex_src = build_latex_source(pandoc, md_path, appendix_heading_pattern)
    except RuntimeError as e:
        return 3, {"error": str(e)}
    tex_path.write_text(tex_src, encoding="utf-8")

    ok, err = compile_latex(tectonic, tex_path, out_pdf, deadline_s=deadline_s)
    if not ok:
        return 3, {"error": "compile failed: %s" % err}

    pages = _sb.pdf_to_pages(out_pdf)
    analysis = _sb.analyze(pages)
    result, checks = _sb.evaluate(analysis)
    checks = [_relabel_small_text_check(c) for c in checks]
    # Glyph coverage (2026-09-09): a character the substitution tables do not
    # know is passed through and renders as a tofu box -- invisible in the
    # source, easy to miss in the PDF, and it shipped once in V3 as
    # "rho [] 0.95". FAIL rather than WARN: it corrupts meaning silently.
    _uncovered = check_glyph_coverage(md_path.read_text(encoding="utf-8"))
    if _uncovered:
        checks.append(_sb.Check(
            status="FAIL", name="glyph coverage",
            detail="%d uncovered non-ASCII character(s) will render as tofu: %s"
                   % (len(_uncovered),
                      ", ".join("%r x%d" % (c, n) for c, n in _uncovered[:6]))))
        result = "FAIL"
    else:
        checks.append(_sb.Check(
            status="PASS", name="glyph coverage",
            detail="every non-ASCII character has a known LaTeX rendering"))
    _cite = check_citations(md_path.read_text(encoding="utf-8"))
    if _cite:
        checks.append(_sb.Check(status="FAIL", name="citations",
                                detail="; ".join(_cite)))
        result = "FAIL"
    else:
        checks.append(_sb.Check(
            status="PASS", name="citations",
            detail="every [n] resolves to a listed reference, and none is orphaned"))

    change = None
    skip_reason = ""
    if want_change:
        old = _sb.git_show(since_ref, md_path)
        if old is None:
            skip_reason = "'%s:%s' not in git history" % (since_ref, _sb.repo_rel(md_path))
        else:
            change = change_report_md(old, md_path.read_text(encoding="utf-8"))

    ctx = {
        "version": ver,
        "engine": "tectonic %s / pandoc %s" % (tectonic_version(tectonic), pandoc_version(pandoc)),
        "built_at": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source_rel": _sb.repo_rel(md_path),
        "git_sha": sha,
        "dirty": dirty,
        "tex_rel": _sb.repo_rel(tex_path),
        "pdf_rel": _sb.repo_rel(out_pdf),
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


def render_report(ctx: Dict, verbose: bool = False) -> str:
    a = ctx["analysis"]
    L: List[str] = []
    L.append("=" * 66)
    L.append("  PHASE1_SUBMISSION_LATEX_v%d      built %s" % (ctx["version"], ctx["built_at"]))
    L.append("=" * 66)
    L.append("  source   %s (LaTeX generated, not hand-authored)" % ctx["source_rel"])
    L.append("  git      %s%s" % (ctx["git_sha"],
                                  "  + uncommitted changes to the .md" if ctx["dirty"] else ""))
    L.append("  engine   %s" % ctx["engine"])
    L.append("  tex      %s" % ctx["tex_rel"])
    L.append("  pdf      %s  (%.2f MB)" % (ctx["pdf_rel"], ctx["pdf_mb"]))
    L.append("")
    L.append("COMPLIANCE  (same checks as the HTML route -- submission_build.py, reused directly)")
    for c in ctx["checks"]:
        L.append("  [%-4s] %-15s %s" % (c.status, c.name, c.detail))
    if a["appendix_starts_on_page"]:
        L.append("  split rule: invisible marker at appendix start; body = pages 1-%d, "
                 "appendix = pages %d-%d" % (a["body_pages"], a["appendix_starts_on_page"], a["total_pages"]))
    L.append("")
    if ctx.get("change") is not None:
        L.append("CHANGE SINCE %s  (diffs the Markdown -- the LaTeX source of truth)" % ctx["since_ref"])
        L.extend(_sb._fmt_change(ctx["change"], verbose))
    else:
        L.append("CHANGE SINCE %s: n/a (%s)" % (ctx["since_ref"], ctx["change_skip_reason"]))
    L.append("")
    warns = sum(1 for c in ctx["checks"] if c.status == "WARN")
    L.append("RESULT: %s%s" % (ctx["result"],
                               "  (%d warning%s)" % (warns, "" if warns == 1 else "s") if warns else ""))
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--md", type=Path, default=DEFAULT_MD)
    ap.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    ap.add_argument("--since", default="HEAD", metavar="GITREF")
    ap.add_argument("--version", type=int, default=None)
    ap.add_argument("--appendix-heading", default=None,
                    help="literal substring marking the appendix's first LaTeX line, "
                         "e.g. 'Appendix A' -- omit if the document has no appendix yet")
    ap.add_argument("--no-change-report", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args(argv)

    code, ctx = build(a.md.resolve(), a.outdir.resolve(), a.since, a.version,
                      not a.no_change_report, a.appendix_heading)

    if "error" in ctx:
        if a.json:
            print(json.dumps({"exit": code, "error": ctx["error"]}, indent=2))
        else:
            print("submission_build_latex: %s" % ctx["error"], file=sys.stderr)
        return code

    report = render_report(ctx, a.verbose)
    report_file = Path(ctx["pdf_path"]).with_suffix(".report.txt")
    report_file.write_text(report + "\n", encoding="utf-8")

    if a.json:
        out = dict(ctx)
        out["checks"] = [vars(c) for c in ctx["checks"]]
        print(json.dumps(out, indent=2, default=str))
    else:
        print(report)
        print("\n  report written to %s" % _sb.repo_rel(report_file))
    return code


if __name__ == "__main__":
    sys.exit(main())
