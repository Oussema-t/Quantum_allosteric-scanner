#!/usr/bin/env python3
"""Content-parity checker for a document kept in two formats (Markdown + HTML).

Filed for the Phase-1 submission, which ships as `documentation/
PHASE1_SUBMISSION_V1.md` and an HTML twin that must carry *identical content*.
Two drifting copies of a submission is the exact failure mode that produced
[[TASK-0307]] (13 Done tasks categorically absent from both shipped documents,
found only by a manual audit). This tool replaces that audit.

WHAT PARITY MEANS HERE -- and what it deliberately does not

Formatting differs between the two by design: HTML has a stylesheet, tables use
different markup, the MD uses `^` where HTML uses <sup>. A raw text diff is
therefore useless. What must NOT differ is the *load-bearing content*:

  numbers      every figure, percentage, p-value and count
  headings     the section set, in the same order
  identifiers  code-styled tokens (PDB codes, function names, verdicts)

Those three are extracted from both sides, normalised, and compared as SETS --
not multisets. A figure legitimately appearing 3 times in one and 5 times in the
other is not drift; a figure present in one and ABSENT from the other is.

NORMALISATION (applied to both sides before extraction)
  - <style>/<script>/<!--comments--> stripped from HTML (CSS hex values and
    pixel sizes are not content and would swamp the comparison)
  - <sup>x</sup> -> ^x, and unicode superscripts likewise, so HTML's
    `10<sup>14</sup>` matches MD's `10^14`
  - URLs stripped (the MD names the artifact URL, whose UUID contains digits
    that exist nowhere in the HTML -- a false positive, not drift)
  - unicode punctuation folded: minus/en-dash/em-dash -> "-", x/times -> "x",
    non-breaking space -> space, curly quotes -> straight
  - markdown emphasis, table pipes and link syntax stripped

EXIT CODES
  0  parity holds
  1  drift found (details on stdout)
  2  usage / unreadable input

Run:  python3 .ai/tools/doc_parity.py <markdown> <html> [--verbose]
Test: python3 -m pytest .ai/tools/test_doc_parity.py
"""
from __future__ import annotations

import argparse
import html as _html
import re
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List, Set, Tuple

# --------------------------------------------------------------------------
# normalisation
# --------------------------------------------------------------------------

_SUPER = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")

_FOLD = {
    "−": "-",   # minus sign
    "–": "-",   # en dash
    "—": "-",   # em dash
    "×": "x",   # multiplication sign
    " ": " ",   # nbsp
    "’": "'",
    "‘": "'",
    "“": '"',
    "”": '"',
    "…": "...",
}


def _fold(s: str) -> str:
    for a, b in _FOLD.items():
        s = s.replace(a, b)
    # unicode superscript run -> ^digits  (e.g. 10⁻⁹ -> 10^-9)
    s = re.sub(r"⁻([⁰¹²³⁴-⁹]+)",
               lambda m: "^-" + m.group(1).translate(_SUPER), s)
    s = re.sub(r"([⁰¹²³⁴-⁹]+)",
               lambda m: "^" + m.group(0).translate(_SUPER), s)
    s = unicodedata.normalize("NFKC", s)
    return s


_URL = re.compile(r"https?://\S+|www\.\S+")


def _strip_urls(s: str) -> str:
    return _URL.sub(" ", s)


def html_to_text(raw: str) -> Tuple[str, List[str], Set[str]]:
    """Return (plain text, headings in order, code-identifier set)."""
    s = re.sub(r"<!--.*?-->", " ", raw, flags=re.S)
    s = re.sub(r"<style\b.*?</style>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<script\b.*?</script>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<link\b[^>]*>", " ", s, flags=re.I)
    s = re.sub(r"<title\b.*?</title>", " ", s, flags=re.S | re.I)

    codes = {_html.unescape(m).strip()
             for m in re.findall(r"<code>(.*?)</code>", s, flags=re.S | re.I)}

    headings = []
    for m in re.finditer(r"<h[1-4]\b[^>]*>(.*?)</h[1-4]>", s, flags=re.S | re.I):
        h = re.sub(r"<span class=\"sub\".*?</span>", " ", m.group(1), flags=re.S)
        h = _html.unescape(re.sub(r"<[^>]+>", " ", h))
        headings.append(_norm_heading(h))

    s = re.sub(r"<sup\b[^>]*>(.*?)</sup>", r"^\1", s, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = _html.unescape(s)
    return _fold(_strip_urls(s)), headings, {_fold(c) for c in codes if c}


def md_to_text(raw: str) -> Tuple[str, List[str], Set[str]]:
    s = raw
    codes = {m.strip() for m in re.findall(r"`([^`\n]+)`", s)}
    # a heading inside a blockquote is still a heading -- strip the marker
    # before extraction, or a callout label goes silently uncompared
    _h = re.sub(r"^\s*>\s?", "", s, flags=re.M)
    headings = [_norm_heading(m.group(1))
                for m in re.finditer(r"^#{1,4}\s+(.+?)\s*$", _h, flags=re.M)]
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)     # links -> text
    s = re.sub(r"^\s*>\s?", " ", s, flags=re.M)        # blockquote markers
    s = s.replace("|", " ")                            # table pipes
    s = re.sub(r"^[ \t]*[-*+]\s+", " ", s, flags=re.M)  # bullets
    s = re.sub(r"[*_`#]", " ", s)                      # emphasis / heading marks
    return _fold(_strip_urls(s)), headings, {_fold(c) for c in codes if c}


def _norm_heading(h: str) -> str:
    h = _fold(_html.unescape(h))
    h = re.sub(r"[*_`#]", "", h)
    h = re.sub(r"^\s*\d+\.\s*", "", h)        # leading section number
    h = re.sub(r"\s+", " ", h).strip().lower()
    return h


# --------------------------------------------------------------------------
# extraction
# --------------------------------------------------------------------------

# a figure: optional sign, digits, optional decimal/thousands, optional % or ^exp
# Trailing lookahead is (?!\w), NOT (?![\w.]): with the latter, "84.0%." 
# backtracks and drops the "%", so "84%" and "84" compare equal. Caught by
# test_percentage_change_is_caught.
_NUM = re.compile(r"(?<![\w.])(-?\d[\d,]*(?:\.\d+)?(?:\^-?\d+)?%?)(?!\w)")

# tokens that are structural noise rather than content
_NOISE = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "1.", "2."}


def numbers(text: str) -> Set[str]:
    out = set()
    for m in _NUM.finditer(text):
        tok = m.group(1).replace(",", "")
        if tok in _NOISE:
            continue
        out.add(tok)
    return out


# --------------------------------------------------------------------------
# comparison
# --------------------------------------------------------------------------

def compare(md_path: Path, html_path: Path) -> Tuple[bool, Dict[str, Dict[str, list]]]:
    md_text, md_head, md_code = md_to_text(md_path.read_text(encoding="utf-8"))
    ht_text, ht_head, ht_code = html_to_text(html_path.read_text(encoding="utf-8"))

    report: Dict[str, Dict[str, list]] = {}

    md_n, ht_n = numbers(md_text), numbers(ht_text)
    report["numbers"] = {
        "md_only": sorted(md_n - ht_n),
        "html_only": sorted(ht_n - md_n),
    }
    report["identifiers"] = {
        "md_only": sorted(md_code - ht_code),
        "html_only": sorted(ht_code - md_code),
    }
    # The document title is compared separately: an HTML <h1> is a design
    # element and legitimately carries a shorter form of the MD H1. Reported as
    # its own check rather than silently dropped from the heading set.
    md_title = md_head[0] if md_head else ""
    ht_title = ht_head[0] if ht_head else ""
    title_ok = bool(md_title) and bool(ht_title) and (
        md_title.startswith(ht_title) or ht_title.startswith(md_title))
    report["title"] = {
        "md_only": [] if title_ok else [md_title],
        "html_only": [] if title_ok else [ht_title],
    }
    md_head, ht_head = md_head[1:], ht_head[1:]

    md_hs, ht_hs = set(md_head), set(ht_head)
    report["headings"] = {
        "md_only": sorted(md_hs - ht_hs),
        "html_only": sorted(ht_hs - md_hs),
    }
    # heading ORDER, over the headings both sides share
    shared = [h for h in md_head if h in ht_hs]
    ht_shared = [h for h in ht_head if h in md_hs]
    report["heading_order"] = {
        "md_only": [] if shared == ht_shared else [" -> ".join(shared[:12])],
        "html_only": [] if shared == ht_shared else [" -> ".join(ht_shared[:12])],
    }

    ok = all(not v["md_only"] and not v["html_only"] for v in report.values())
    return ok, report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Verify a Markdown and an HTML file carry the same content.")
    ap.add_argument("markdown", type=Path)
    ap.add_argument("html", type=Path)
    ap.add_argument("--verbose", action="store_true",
                    help="also print the counts extracted from each side")
    a = ap.parse_args(argv)

    for p in (a.markdown, a.html):
        if not p.is_file():
            print(f"doc_parity: not a file: {p}", file=sys.stderr)
            return 2

    ok, report = compare(a.markdown, a.html)

    label = {"numbers": "figures", "identifiers": "code identifiers",
             "headings": "section headings", "heading_order": "heading ORDER",
             "title": "document title"}
    for key, diff in report.items():
        if not diff["md_only"] and not diff["html_only"]:
            if a.verbose:
                print(f"  ok   {label[key]}")
            continue
        print(f"\nDRIFT -- {label[key]}")
        for side, other in (("md_only", a.html), ("html_only", a.markdown)):
            if diff[side]:
                print(f"  present in {'MD' if side=='md_only' else 'HTML'}, "
                      f"missing from {other.name}:")
                for tok in diff[side]:
                    print(f"      {tok}")

    if ok:
        print(f"parity OK: {a.markdown.name} and {a.html.name} carry the same content")
        return 0
    print("\nparity FAILED -- fix both files, or the drift is real content loss")
    return 1


if __name__ == "__main__":
    sys.exit(main())
