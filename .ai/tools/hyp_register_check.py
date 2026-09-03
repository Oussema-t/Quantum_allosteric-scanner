#!/usr/bin/env python3
"""Consultation-enforcement checker for the HYP-P*/HYP-S* hypothesis register.

Filed for TASK-0322, pathway A of [[TASK-0321]]'s decision brief. TASK-0321
measured *why* the register goes unread: 9% task-citation rate, and (the
incident that triggered it) a collaborator brief claiming HYP-P9's route was
"open" when the register had recorded a correct, current FAIL. Writing
better hypotheses does not fix non-consultation -- this script is the
mechanical gate, in the shape of `.ai/tools/doc_parity.py` ([[TASK-0319]]'s
standing finding: a checker not proven to fail on a seeded violation is not
verified; see `test_hyp_register_check.py`).

SCOPE. Only `physics.md` (HYP-P1..P14) and `search_complexity.md`
(HYP-S1..S7) define hypothesis ids -- 21 total, matching [[TASK-0321]]'s own
count exactly. `ceiling.md` and `reference_register.md` are deliberately
NOT parsed for ids: `ceiling.md` is strategic narrative with no HYP- ids of
its own, and `reference_register.md` already carries its own self-contained
"Coverage summary" index over a *different* id namespace (H9, H6.1, H4.1,
...) -- building a second index over that file would duplicate, not fix,
an already-solved problem.

TWO VIOLATION CLASSES

  staleness       A hypothesis id has a dated Status line, but a task that
                  cites the id has a later date recorded in its own Done
                  section (or Filed line, if never completed) -- the
                  register said X, a task since then found something newer,
                  the register was never updated.

  uncited-claim   An outward-facing document
                  (`__WORK_IN_PROGRESS__/documentation/*.{md,html}`)
                  contains open/closed/untested-shaped language with no
                  HYP-P*/HYP-S* id anywhere in the same paragraph (md) or
                  block element (html). This is the class that would have
                  caught TASK-0320's actual error -- pattern-matched on
                  claim-shaped language, not just missing citations of ids
                  that ARE named. The pattern list starts narrow
                  (see CLAIM_PATTERNS below) and is meant to be refined
                  against real false positives/negatives, not treated as
                  complete.

Neither class rewrites any hypothesis's content (TASK-0321's own
constraint, inherited by TASK-0322 and honored here).

EXIT CODES
  0  no violations
  1  violations found
  2  usage / unreadable input

Run:    python3 .ai/tools/hyp_register_check.py [--verbose]
        python3 .ai/tools/hyp_register_check.py --build-index   (regenerate INDEX.md)
Test:   python3 -m pytest .ai/tools/test_hyp_register_check.py
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HYP_DIR = REPO_ROOT / ".claude" / "hypotheses"
TASK_DIRS = [
    REPO_ROOT / ".ai" / "tasks" / "TODO",
    REPO_ROOT / ".ai" / "tasks" / "IN_PROGRESS",
    REPO_ROOT / ".ai" / "tasks" / "DONE",
]
DOC_DIR = REPO_ROOT / "__WORK_IN_PROGRESS__" / "documentation"
INDEX_PATH = HYP_DIR / "INDEX.md"

# files that define hypothesis ids -- see SCOPE above for why only these two
HYP_SOURCE_FILES = ["physics.md", "search_complexity.md"]

HYP_ID_RE = re.compile(r"HYP-[PS]\d+")
HEADER_RE = re.compile(r"^## (HYP-[PS]\d+)\s*(?:·\s*(.*))?$", re.M)
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})(?:/\d{2})?")
STATUS_RE = re.compile(r"\*\*(?:Status\w*|Correction|Resolved)\b[^*]*\*\*", re.S)

# --------------------------------------------------------------------------
# hypothesis parsing
# --------------------------------------------------------------------------


class Hypothesis:
    def __init__(self, hyp_id, claim, source_file):
        self.id = hyp_id
        self.claim = claim
        self.source_file = source_file
        self.status_date = None  # type: Optional[str]
        self.status_text = None  # type: Optional[str]
        self.citing_tasks = []  # type: List[Tuple[str, Optional[str]]]  # (task_id, date)

    @property
    def citation_count(self):
        return len(self.citing_tasks)

    @property
    def latest_citing(self):
        dated = [(t, d) for t, d in self.citing_tasks if d]
        if not dated:
            return None
        return max(dated, key=lambda td: td[1])


def parse_hypotheses_from_text(text: str, fname: str) -> Dict[str, Hypothesis]:
    """Pure: extract every `## HYP-Pn ·`/`## HYP-Sn ·` block from one
    file's already-read text. No filesystem access -- this is the half
    the seeded-violation tests exercise directly."""
    hyps = {}
    headers = list(HEADER_RE.finditer(text))
    for i, m in enumerate(headers):
        hyp_id = m.group(1)
        claim = (m.group(2) or "").strip()
        body_start = m.end()
        body_end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        body = text[body_start:body_end]

        h = Hypothesis(hyp_id, claim, fname)
        statuses = []
        for sm in STATUS_RE.finditer(body):
            snippet = sm.group(0)
            dm = DATE_RE.search(snippet)
            if dm:
                statuses.append((dm.group(1), snippet))
        if statuses:
            statuses.sort(key=lambda t: t[0])
            h.status_date, h.status_text = statuses[-1]
        hyps[hyp_id] = h
    return hyps


def parse_hypotheses() -> Dict[str, Hypothesis]:
    hyps = {}
    for fname in HYP_SOURCE_FILES:
        text = (HYP_DIR / fname).read_text(encoding="utf-8")
        hyps.update(parse_hypotheses_from_text(text, fname))
    return hyps


# --------------------------------------------------------------------------
# task-citation scanning (staleness class)
# --------------------------------------------------------------------------

DONE_HEADING_RE = re.compile(r"^## Done\b.{0,300}", re.M | re.S)
FILED_RE = re.compile(r"^- Filed:\s*(\d{4}-\d{2}-\d{2})", re.M)


def _task_date(text: str) -> Optional[str]:
    """Best-known date for a task: first date in its Done section if
    present (either `## Done (YYYY-MM-DD, ...)` or a `## Done` heading
    followed by a `**YYYY-MM-DD, ...**` line -- both conventions are in
    live use), else its Filed date."""
    dm = DONE_HEADING_RE.search(text)
    if dm:
        d2 = DATE_RE.search(dm.group(0))
        if d2:
            return d2.group(1)
    fm = FILED_RE.search(text)
    if fm:
        return fm.group(1)
    return None


def record_task_citation(hyps: Dict[str, Hypothesis], task_id: str, text: str) -> None:
    """Pure: given one task file's text and its id, record its citations
    of any known hypothesis id onto that Hypothesis's citing_tasks list."""
    ids = set(HYP_ID_RE.findall(text))
    if not ids:
        return
    date = _task_date(text)
    for hid in ids:
        if hid in hyps:
            hyps[hid].citing_tasks.append((task_id, date))


def scan_task_citations(hyps: Dict[str, Hypothesis]) -> None:
    for d in TASK_DIRS:
        if not d.exists():
            continue
        for f in sorted(d.glob("TASK-*.md")):
            text = f.read_text(encoding="utf-8", errors="ignore")
            task_id_parts = f.stem.split("-", 2)
            task_id = "-".join(task_id_parts[:2]) if len(task_id_parts) >= 2 else f.stem
            record_task_citation(hyps, task_id, text)


# --------------------------------------------------------------------------
# staleness class
# --------------------------------------------------------------------------


def find_staleness(hyps: Dict[str, Hypothesis]) -> List[dict]:
    findings = []
    for h in hyps.values():
        if not h.status_date:
            continue
        latest = h.latest_citing
        if latest and latest[1] > h.status_date:
            findings.append(
                {
                    "class": "staleness",
                    "id": h.id,
                    "status_date": h.status_date,
                    "citing_task": latest[0],
                    "citing_date": latest[1],
                }
            )
    return findings


# --------------------------------------------------------------------------
# uncited-claim class
# --------------------------------------------------------------------------

# Deliberately narrow -- see module docstring. Refine against real
# false positives/negatives, don't treat as exhaustive.
CLAIM_PATTERNS = [
    r"\bopen route\b",
    r"\bopen lead\b",
    r"\bremains?\s+(?:an\s+)?open\b",
    r"\bstill open\b",
    r"\bremains?\s+untested\b",
    r"\bhas not been ruled out\b",
    r"\bnot yet (?:tested|ruled out)\b",
    r"\bis (?:now )?closed\b(?!-form)",
    r"\bis an open\b",
]
CLAIM_RE = re.compile("|".join(CLAIM_PATTERNS), re.I)

# Known false-positive shapes for "closed"/"open" that are not route/
# mechanism verdicts at all (a mathematical closed-form/closed-set sense,
# or an open *item*/*question* that isn't a hypothesis route). Checked
# against the real corpus (TASK-0322's own Planned Validation run) rather
# than guessed -- documented here instead of silently dropped, since the
# task's own scope says to document gaps rather than over-fit the list.
_FALSE_POSITIVE_CONTEXT_RE = re.compile(
    r"closed-form|closed by definition|closed set|closed under|"
    r"open item\b|open question\b(?!.{0,40}HYP-)",
    re.I,
)

_BLOCK_SPLIT_HTML = re.compile(r"(?i)</?(?:li|p|div|section|tr|td|h[1-6])\b[^>]*>")
_TAG_RE = re.compile(r"<[^>]+>")


def _paragraphs_md(text: str) -> List[str]:
    return re.split(r"\n\s*\n", text)


def _paragraphs_html(text: str) -> List[str]:
    chunks = _BLOCK_SPLIT_HTML.split(text)
    return [_TAG_RE.sub(" ", c) for c in chunks]


def find_uncited_claims_in_text(text: str, suffix: str, label: str) -> List[dict]:
    """Pure: scan one already-read document's text for claim-shaped
    language with no HYP-P*/HYP-S* id in the same paragraph (.md) or
    block element (.html). No filesystem access."""
    findings = []
    paras = _paragraphs_md(text) if suffix == ".md" else _paragraphs_html(text)
    for para in paras:
        # normalise whitespace first -- markdown/HTML line-wraps a
        # phrase like "closed by\n  definition" across a newline,
        # which a literal-space exclusion regex would otherwise miss
        norm = " ".join(para.split())
        m = CLAIM_RE.search(norm)
        if not m:
            continue
        if HYP_ID_RE.search(norm):
            continue
        if _FALSE_POSITIVE_CONTEXT_RE.search(norm):
            continue
        s = max(0, m.start() - 60)
        e = min(len(norm), m.end() + 60)
        findings.append(
            {
                "class": "uncited-claim",
                "file": label,
                "pattern": m.group(0),
                "snippet": norm[s:e],
            }
        )
    return findings


def find_uncited_claims() -> List[dict]:
    findings = []
    if not DOC_DIR.exists():
        return findings
    files = sorted(DOC_DIR.glob("*.md")) + sorted(DOC_DIR.glob("*.html"))
    for f in files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        findings.extend(
            find_uncited_claims_in_text(text, f.suffix, str(f.relative_to(REPO_ROOT)))
        )
    return findings


# --------------------------------------------------------------------------
# index generation
# --------------------------------------------------------------------------


def build_index_text(hyps: Dict[str, Hypothesis]) -> str:
    rows = sorted(hyps.values(), key=lambda h: -h.citation_count)
    lines = [
        "<!-- GENERATED by .ai/tools/hyp_register_check.py --build-index -- do not hand-edit. -->",
        "# Hypothesis register -- status index",
        "",
        "One-screen view of every `HYP-P*`/`HYP-S*` id, sorted by citation",
        "count. Regenerate with `python3 .ai/tools/hyp_register_check.py",
        "--build-index` after any hypothesis is added, cited, or given a",
        "verdict -- the checker's staleness/drift class also validates this",
        "file did not silently fall behind its own source files.",
        "",
        "| id | claim | status | citing tasks |",
        "|---|---|---|---|",
    ]
    for h in rows:
        if h.status_date:
            status = h.status_date
        else:
            status = "no verdict recorded"
        claim = h.claim.replace("|", "\\|")
        if len(claim) > 90:
            claim = claim[:87] + "..."
        lines.append(
            "| [[%s]] | %s | %s | %d |" % (h.id, claim, status, h.citation_count)
        )
    lines.append("")
    return "\n".join(lines)


def write_index(hyps: Dict[str, Hypothesis]) -> None:
    INDEX_PATH.write_text(build_index_text(hyps), encoding="utf-8")


def index_is_stale(hyps: Dict[str, Hypothesis]) -> bool:
    if not INDEX_PATH.exists():
        return True
    return INDEX_PATH.read_text(encoding="utf-8") != build_index_text(hyps)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def run(verbose: bool = False) -> Tuple[int, List[dict]]:
    hyps = parse_hypotheses()
    scan_task_citations(hyps)
    findings = find_staleness(hyps) + find_uncited_claims()
    if index_is_stale(hyps):
        findings.append({"class": "index-drift", "detail": str(INDEX_PATH)})
    return (1 if findings else 0), findings


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--build-index", action="store_true", help="regenerate INDEX.md and exit"
    )
    args = parser.parse_args(argv)

    try:
        hyps = parse_hypotheses()
        scan_task_citations(hyps)
    except OSError as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2

    if args.build_index:
        write_index(hyps)
        print("wrote %s" % INDEX_PATH)
        return 0

    findings = find_staleness(hyps) + find_uncited_claims()
    if index_is_stale(hyps):
        findings.append({"class": "index-drift", "detail": str(INDEX_PATH)})

    if not findings:
        print("OK: no violations (%d hypotheses checked)" % len(hyps))
        return 0

    by_class = {}
    for fnd in findings:
        by_class.setdefault(fnd["class"], []).append(fnd)

    for cls, items in by_class.items():
        print("=== %s (%d) ===" % (cls, len(items)))
        for it in items:
            if cls == "staleness":
                print(
                    "  %s: status dated %s, but %s (dated %s) cites it"
                    % (it["id"], it["status_date"], it["citing_task"], it["citing_date"])
                )
            elif cls == "uncited-claim":
                print("  %s: %r" % (it["file"], it["pattern"]))
                if args.verbose:
                    print("      ...%s..." % it["snippet"])
            elif cls == "index-drift":
                print("  %s is missing or out of date -- run --build-index" % it["detail"])
    return 1


if __name__ == "__main__":
    sys.exit(main())
