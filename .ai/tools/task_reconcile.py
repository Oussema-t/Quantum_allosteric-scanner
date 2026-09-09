#!/usr/bin/env python3
"""Three-way consistency check: locks vs on-disk task files vs the COMMON.md
Active Work Registry. TASK-0352 Part B.

WHY THIS EXISTS, NOT A SEARCH TOOL

Filed after [[TASK-0350]] was claimed and running, its file still under
TODO/, with **no registry row at all** -- nor did [[TASK-0347]] or
[[TASK-0351]]. The lock prevented a collision between agents; nothing told a
fresh session the work existed at all, because nothing checked the three
places that are each supposed to know.

Three sources of truth about live work disagree silently:
  .ai/tasks/.locks/*.lock            who holds what (claim.py)
  .ai/tasks/{TODO,IN_PROGRESS,DONE}/ what state the file itself claims
  .ai/COMMON.md Active Work Registry what a fresh session actually reads

This is a consistency check over STRUCTURED data -- deterministic, no
judgement calls, and (per this task's own design argument) checkable for
completeness in a way a search tool cannot be: every lock, every file, every
registry row is enumerated, nothing is sampled or ranked.

READ-ONLY. Reports drift; never repairs it -- auto-repair of a contended
shared file is exactly how the registry got reverted twice in one session
(COMMON.md's own 2026-07-04 note). No new source of truth: if this tool and
the actual files disagree, the files win and this tool is stale -- rerun it.

FINDINGS (kind -- meaning)
  malformed_registry_row   a COMMON.md line opens like a registry row ("|
                            TASK-XXXX | ...") but does not parse to the
                            header's 9 columns (almost always an unescaped
                            "|" inside a cell) -- claim.py's own _parse_row,
                            reused by move/resolve/sync AND by this tool's
                            own registry scan, silently treats it as if no
                            row existed at all. Found live: 26 real rows in
                            this repo right now. Listed first because it
                            explains a chunk of file_no_registry_row below --
                            some of those tasks do have a row, just not a
                            parseable one, and that distinction matters for
                            what the fix actually is (repair the row's
                            formatting, not write a new one)
  claimed_no_file          locked, but no task file found on disk at all
  claimed_no_registry_row  locked, but COMMON.md has no row for it
  registry_row_no_file     a registry row exists, but no file backs it
  file_no_registry_row     a task file exists, but no registry row names it
                            -- the exact TASK-0347/0350/0351 incident
  duplicate_task_file      the same task id has more than one file on disk
                            (across folders or within one) -- disk_task_ids()
                            in claim.py silently picks one and would hide
                            this; this tool does not reuse that shortcut
  duplicate_registry_row   the same task id has more than one COMMON.md row
  done_with_live_claim     file sits in DONE/ but a lock is still held
  status_folder_mismatch   the file's own "- Status:" line does not contain
                            the word its folder implies (TODO/In Progress/
                            Done) -- a whole-word, case-insensitive CONTAINS
                            check, not equality: real Status lines carry
                            legitimate trailing detail ("Done (2026-07-24) --
                            H2 half: FAIL, see Done section"); requiring
                            exact equality would flood this report with
                            stylistic variation instead of real drift
  registry_status_mismatch same word-contains check, against the registry
                            row's Status cell instead of the file
  registry_path_mismatch   the registry row's Path cell does not match
                            where the file actually is

Never summarises or ranks: every finding is printed, always, in a stable
order. If a future revision ever needs to cap output, it must say explicitly
how many were withheld -- this version has no such cap because withholding a
negative-result-adjacent report is exactly the failure this task exists to
avoid.

Run:   .ai/tools/task_reconcile.py
       .ai/tools/task_reconcile.py --json
Test:  python3 -m pytest .ai/tools/test_task_reconcile.py
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import claim as _claim  # reuse: read_lock, is_task_id, STATE_TO_STATUS, TABLE_ROW_RE, paths

REPO_ROOT = Path(_claim.REPO_ROOT)
TASKS_DIR = Path(_claim.TASKS_DIR)
LOCKS_DIR = Path(_claim.LOCKS_DIR)
COMMON_MD = Path(_claim.COMMON_MD)
TASK_STATE_DIRS = _claim.TASK_STATE_DIRS          # ["TODO", "IN_PROGRESS", "DONE"]
STATE_TO_STATUS = _claim.STATE_TO_STATUS          # {"TODO": "TODO", "IN_PROGRESS": "In Progress", "DONE": "Done"}

_STATUS_LINE_RE = re.compile(r"^-\s*Status:\s*(.*)$", re.MULTILINE)
_TASK_FILE_RE = re.compile(r"^TASK-(\d{4})(\.\d+)?-.*\.md$")


# --------------------------------------------------------------------------
# scan (I/O)  -- pure logic lives in reconcile() below, tested without these
# --------------------------------------------------------------------------

def scan_locks() -> Dict[str, dict]:
    """{TASK-XXXX[.NNN] -> lock dict}, TASK ids only -- SCQ-*/GIT-COMMIT/other
    resource locks are a different registry (repo.commit.scq) and out of
    this task's scope."""
    if not LOCKS_DIR.is_dir():
        return {}
    out = {}
    for p in sorted(LOCKS_DIR.iterdir()):
        if not p.name.endswith(".lock") or p.name.startswith("SCQ-"):
            continue
        task_id = p.name[: -len(".lock")]
        if not _claim.is_task_id(task_id):
            continue
        lock = _claim.read_lock(task_id)
        if lock is not None:
            out[task_id] = lock
    return out


def scan_disk_files() -> Dict[str, List[str]]:
    """{TASK-XXXX[.NNN] -> [repo-relative paths]}, ALL matches kept, not just
    one -- claim.py's own disk_task_ids() silently collapses a duplicate
    (same id filed in two folders) to whichever folder it scans last, which
    would hide exactly the kind of drift this tool exists to surface. Not
    reused here for that reason (find_task_file() does detect a duplicate,
    but only for one id at a time and by raising, not reporting)."""
    out: Dict[str, List[str]] = {}
    for state in TASK_STATE_DIRS:
        d = TASKS_DIR / state
        if not d.is_dir():
            continue
        for p in sorted(d.iterdir()):
            m = _TASK_FILE_RE.match(p.name)
            if not m:
                continue
            task_id = "TASK-%s%s" % (m.group(1), m.group(2) or "")
            rel = str(p.relative_to(REPO_ROOT))
            out.setdefault(task_id, []).append(rel)
    return out


def read_file_status(path: Path) -> Optional[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    m = _STATUS_LINE_RE.search(text)
    return m.group(1).strip() if m else None


def scan_registry_rows() -> Dict[str, List[Dict[str, str]]]:
    """{TASK-XXXX[.NNN] -> [{"status":..., "path":...}, ...]}, ALL rows kept
    (a duplicate row is itself a finding, not something to silently
    dedupe)."""
    out: Dict[str, List[Dict[str, str]]] = {}
    if not COMMON_MD.is_file():
        return out
    for line in COMMON_MD.read_text(encoding="utf-8").splitlines():
        cols = _claim._parse_row(line + "\n")
        if cols is None:
            continue
        task_id, status, path = cols[0], cols[3], cols[8]
        out.setdefault(task_id, []).append({"status": status, "path": path.strip("`")})
    return out


def scan_malformed_registry_rows() -> Dict[str, int]:
    """{task_id -> actual column count} for every COMMON.md line that opens
    like a registry row (matches claim.py's own TABLE_ROW_RE: "| TASK-XXXX |
    ...") but does not parse to the 9 columns the header declares.

    This is not a hypothetical: found live while validating this tool's own
    numbers against `claim.py sync --check` -- 26 real rows in this repo's
    COMMON.md right now, almost all caused by an unescaped literal "|"
    inside a cell's free text breaking the naive split("|"). The
    consequence is worse than a cosmetic table-rendering glitch:
    `claim.py`'s own `_parse_row` is reused unchanged by `move`/`resolve`'s
    registry-sync step, `sync`'s dangling-row warnings, AND this tool's own
    `scan_registry_rows()` above -- ALL of them silently treat a malformed
    row as if no row existed at all, with no warning anywhere. A task whose
    row is malformed looks, to every existing tool, identical to a task
    with no row -- even though a human glancing at the table sees one."""
    out: Dict[str, int] = {}
    if not COMMON_MD.is_file():
        return out
    for line in COMMON_MD.read_text(encoding="utf-8").splitlines():
        if not _claim.TABLE_ROW_RE.match(line):
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) != 9 and cols:
            out[cols[0]] = len(cols)
    return out


# --------------------------------------------------------------------------
# pure logic -- takes plain data structures, no filesystem access, so the
# acceptance-bar test (seed a gap, the check must go red) needs no fixtures
# on disk at all.
# --------------------------------------------------------------------------

@dataclass
class Finding:
    kind: str
    task_id: str
    detail: str


_WORD_RE_CACHE: Dict[str, "re.Pattern"] = {}


def _word_present(word: str, text: str) -> bool:
    """Case-insensitive whole-word containment, not equality -- a Status
    line legitimately carries trailing detail ("Done (2026-07-24) -- H2
    half: FAIL..."); requiring exact equality would flag that as drift, not
    catch it."""
    pat = _WORD_RE_CACHE.get(word)
    if pat is None:
        pat = re.compile(r"\b%s\b" % re.escape(word), re.IGNORECASE)
        _WORD_RE_CACHE[word] = pat
    return bool(pat.search(text))


def _folder_of(path: str) -> Optional[str]:
    parts = path.split("/")
    return parts[2] if len(parts) >= 3 and parts[0] == ".ai" and parts[1] == "tasks" else None


def reconcile(locks: Dict[str, dict],
             disk_files: Dict[str, List[str]],
             registry_rows: Dict[str, List[Dict[str, str]]],
             file_statuses: Dict[str, Optional[str]]) -> List[Finding]:
    """file_statuses: {repo-relative path -> Status line value or None},
    keyed by PATH (not task id) since a duplicate-file task id has one
    status per file."""
    findings: List[Finding] = []
    all_ids = sorted(set(locks) | set(disk_files) | set(registry_rows))

    for task_id in all_ids:
        locked = task_id in locks
        paths = disk_files.get(task_id, [])
        rows = registry_rows.get(task_id, [])

        if locked and not paths:
            findings.append(Finding("claimed_no_file", task_id,
                "locked by %r but no task file found under TODO/IN_PROGRESS/DONE"
                % locks[task_id].get("claimant")))
        if locked and not rows:
            findings.append(Finding("claimed_no_registry_row", task_id,
                "locked by %r but COMMON.md has no registry row for it"
                % locks[task_id].get("claimant")))
        if rows and not paths:
            for row in rows:
                findings.append(Finding("registry_row_no_file", task_id,
                    "registry row claims path %r but no file exists there (or anywhere)"
                    % row["path"]))
        if paths and not rows:
            for p in paths:
                findings.append(Finding("file_no_registry_row", task_id,
                    "task file exists at %r but COMMON.md has no registry row for it" % p))
        if len(paths) > 1:
            findings.append(Finding("duplicate_task_file", task_id,
                "more than one file on disk: %s" % ", ".join(paths)))
        if len(rows) > 1:
            findings.append(Finding("duplicate_registry_row", task_id,
                "more than one COMMON.md row: %s" % ", ".join(r["path"] for r in rows)))

        for p in paths:
            folder = _folder_of(p)
            if folder is None or folder not in STATE_TO_STATUS:
                continue
            if folder == "DONE" and locked:
                findings.append(Finding("done_with_live_claim", task_id,
                    "file is in DONE/ (%s) but still locked by %r"
                    % (p, locks[task_id].get("claimant"))))
            status_line = file_statuses.get(p)
            expected = STATE_TO_STATUS[folder]
            if status_line is not None and not _word_present(expected, status_line):
                findings.append(Finding("status_folder_mismatch", task_id,
                    "file at %s (folder implies Status containing %r) but its own "
                    "Status line reads %r" % (p, expected, status_line)))
            for row in rows:
                if row["path"] and row["path"] != p and len(paths) == 1:
                    findings.append(Finding("registry_path_mismatch", task_id,
                        "registry row Path is %r, actual file is at %r" % (row["path"], p)))
                if row["status"] and not _word_present(expected, row["status"]):
                    findings.append(Finding("registry_status_mismatch", task_id,
                        "file's folder (%s) implies Status containing %r, but the "
                        "registry row says %r" % (folder, expected, row["status"])))

    return findings


# --------------------------------------------------------------------------
# I/O assembly + report
# --------------------------------------------------------------------------

def malformed_row_findings(malformed: Dict[str, int]) -> List[Finding]:
    """Pure wrapper so this is unit-testable the same way as reconcile()."""
    return [
        Finding("malformed_registry_row", task_id,
               "COMMON.md has a row starting '| %s |' with %d columns, not the "
               "header's 9 -- claim.py's own _parse_row (and this tool's "
               "scan_registry_rows) silently treats it as if no row existed "
               "at all" % (task_id, n))
        for task_id, n in sorted(malformed.items())
    ]


def gather() -> List[Finding]:
    locks = scan_locks()
    disk_files = scan_disk_files()
    registry_rows = scan_registry_rows()
    file_statuses: Dict[str, Optional[str]] = {}
    for paths in disk_files.values():
        for p in paths:
            file_statuses[p] = read_file_status(REPO_ROOT / p)
    findings = reconcile(locks, disk_files, registry_rows, file_statuses)
    findings.extend(malformed_row_findings(scan_malformed_registry_rows()))
    return findings


_KIND_ORDER = [
    "malformed_registry_row",
    "claimed_no_file", "claimed_no_registry_row", "registry_row_no_file",
    "file_no_registry_row", "duplicate_task_file", "duplicate_registry_row",
    "done_with_live_claim", "status_folder_mismatch", "registry_status_mismatch",
    "registry_path_mismatch",
]


def render_report(findings: List[Finding]) -> str:
    if not findings:
        return "task_reconcile: no disagreements found across locks / disk / registry."
    by_kind: Dict[str, List[Finding]] = {}
    for f in findings:
        by_kind.setdefault(f.kind, []).append(f)
    lines = ["task_reconcile: %d disagreement(s)" % len(findings), ""]
    for kind in _KIND_ORDER:
        group = by_kind.get(kind, [])
        if not group:
            continue
        lines.append("%s (%d)" % (kind, len(group)))
        for f in group:
            lines.append("  %s: %s" % (f.task_id, f.detail))
        lines.append("")
    return "\n".join(lines).rstrip("\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    findings = gather()

    if a.json:
        print(json.dumps({"count": len(findings),
                          "findings": [vars(f) for f in findings]}, indent=2))
    else:
        print(render_report(findings))

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
