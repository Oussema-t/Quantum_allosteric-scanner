#!/usr/bin/env python3
"""Tests for task_reconcile.py (TASK-0352 Part B).

All tests operate on synthetic locks/disk_files/registry_rows/file_statuses
passed directly to reconcile() -- no filesystem fixtures, so these are fast
and do not depend on this repo's own (real, moving-target) drift state.

Acceptance bar (TASK-0319's standing rule, and this task's own explicit
constraint): "ships with a test that fails on a seeded gap -- remove a
registry row, the check must go red." See test_seeded_missing_registry_row_*
below.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import task_reconcile as tr  # noqa: E402


def _lock(claimant="Someone"):
    return {"claimant": claimant, "claimed_at": "2026-09-09 10:00"}


def _kinds(findings):
    return {f.kind for f in findings}


def _for(findings, task_id):
    return [f for f in findings if f.task_id == task_id]


# ---------------------------------------------------------------- clean state

def test_fully_consistent_task_has_no_findings():
    locks = {}
    disk = {"TASK-0001": [".ai/tasks/DONE/TASK-0001-thing.md"]}
    registry = {"TASK-0001": [{"status": "Done", "path": ".ai/tasks/DONE/TASK-0001-thing.md"}]}
    statuses = {".ai/tasks/DONE/TASK-0001-thing.md": "Done"}
    findings = tr.reconcile(locks, disk, registry, statuses)
    assert findings == []


def test_status_line_with_trailing_detail_is_not_flagged():
    """A Status line carrying real detail past the bare word must not be
    treated as drift -- equality would flood this report with normal
    stylistic variation, exactly what the module docstring says to avoid."""
    disk = {"TASK-0002": [".ai/tasks/DONE/TASK-0002-thing.md"]}
    registry = {"TASK-0002": [{"status": "Done", "path": ".ai/tasks/DONE/TASK-0002-thing.md"}]}
    statuses = {".ai/tasks/DONE/TASK-0002-thing.md":
               "Done (2026-07-24) -- H2 half: FAIL, see Done section"}
    findings = tr.reconcile({}, disk, registry, statuses)
    assert findings == []


# ---------------------------------------------------------------- acceptance bar

def test_seeded_missing_registry_row_is_caught():
    """The exact TASK-0347/0350/0351 incident this task was filed over: a
    real task file, claimed, with NO registry row at all. Seed it, confirm
    the check goes red -- this is the acceptance bar."""
    locks = {"TASK-0350": _lock("Implementer B")}
    disk = {"TASK-0350": [".ai/tasks/IN_PROGRESS/TASK-0350-something.md"]}
    registry = {}  # <-- the seeded gap: no row at all
    statuses = {".ai/tasks/IN_PROGRESS/TASK-0350-something.md": "In Progress"}
    findings = tr.reconcile(locks, disk, registry, statuses)
    assert "file_no_registry_row" in _kinds(findings)
    hit = [f for f in findings if f.kind == "file_no_registry_row"]
    assert hit and hit[0].task_id == "TASK-0350"


def test_removing_the_registry_row_flips_a_clean_case_to_red():
    """Same assertion, phrased as the task's own words: start from a clean,
    fully-consistent state (first test above) and REMOVE the registry row --
    the check must go red where it was silent before."""
    locks, disk = {}, {"TASK-0001": [".ai/tasks/DONE/TASK-0001-thing.md"]}
    statuses = {".ai/tasks/DONE/TASK-0001-thing.md": "Done"}
    before = tr.reconcile(locks, disk,
                          {"TASK-0001": [{"status": "Done",
                                         "path": ".ai/tasks/DONE/TASK-0001-thing.md"}]},
                          statuses)
    after = tr.reconcile(locks, disk, {}, statuses)   # registry row removed
    assert before == []
    assert any(f.kind == "file_no_registry_row" for f in after)


# ---------------------------------------------------------------- individual kinds

def test_claimed_but_no_file_anywhere():
    locks = {"TASK-0099": _lock()}
    findings = tr.reconcile(locks, {}, {}, {})
    kinds = _kinds(_for(findings, "TASK-0099"))
    assert "claimed_no_file" in kinds
    assert "claimed_no_registry_row" in kinds


def test_registry_row_but_no_file():
    registry = {"TASK-0005": [{"status": "TODO", "path": ".ai/tasks/TODO/TASK-0005-x.md"}]}
    findings = tr.reconcile({}, {}, registry, {})
    assert any(f.kind == "registry_row_no_file" and f.task_id == "TASK-0005"
              for f in findings)


def test_duplicate_task_file_across_folders():
    disk = {"TASK-0189": [".ai/tasks/TODO/TASK-0189-x.md",
                          ".ai/tasks/DONE/TASK-0189-x.md"]}
    registry = {"TASK-0189": [{"status": "Done", "path": ".ai/tasks/DONE/TASK-0189-x.md"}]}
    findings = tr.reconcile({}, disk, registry, {})
    dup = [f for f in findings if f.kind == "duplicate_task_file"]
    assert len(dup) == 1 and "TODO/TASK-0189-x.md" in dup[0].detail
    assert "DONE/TASK-0189-x.md" in dup[0].detail
    # a duplicate must not also fire the unrelated path-mismatch check --
    # which path would even be "correct" is ambiguous while duplicated
    assert not any(f.kind == "registry_path_mismatch" for f in findings)


def test_duplicate_registry_row():
    disk = {"TASK-0010": [".ai/tasks/DONE/TASK-0010-x.md"]}
    registry = {"TASK-0010": [
        {"status": "Done", "path": ".ai/tasks/DONE/TASK-0010-x.md"},
        {"status": "In Progress", "path": ".ai/tasks/IN_PROGRESS/TASK-0010-x.md"},
    ]}
    findings = tr.reconcile({}, disk, registry, {".ai/tasks/DONE/TASK-0010-x.md": "Done"})
    assert any(f.kind == "duplicate_registry_row" and f.task_id == "TASK-0010"
              for f in findings)


def test_done_folder_with_live_claim():
    locks = {"TASK-0258": _lock("reviewer-opus")}
    disk = {"TASK-0258": [".ai/tasks/DONE/TASK-0258-x.md"]}
    registry = {"TASK-0258": [{"status": "Done", "path": ".ai/tasks/DONE/TASK-0258-x.md"}]}
    statuses = {".ai/tasks/DONE/TASK-0258-x.md": "Done"}
    findings = tr.reconcile(locks, disk, registry, statuses)
    assert any(f.kind == "done_with_live_claim" and f.task_id == "TASK-0258"
              for f in findings)


def test_status_line_disagrees_with_folder():
    disk = {"TASK-0020": [".ai/tasks/DONE/TASK-0020-x.md"]}
    registry = {"TASK-0020": [{"status": "Done", "path": ".ai/tasks/DONE/TASK-0020-x.md"}]}
    statuses = {".ai/tasks/DONE/TASK-0020-x.md": "TODO"}   # moved folder, forgot the line
    findings = tr.reconcile({}, disk, registry, statuses)
    hit = [f for f in findings if f.kind == "status_folder_mismatch"]
    assert hit and hit[0].task_id == "TASK-0020"
    assert "TODO" in hit[0].detail and "Done" in hit[0].detail


def test_registry_status_disagrees_with_folder():
    disk = {"TASK-0021": [".ai/tasks/IN_PROGRESS/TASK-0021-x.md"]}
    registry = {"TASK-0021": [{"status": "Done", "path": ".ai/tasks/IN_PROGRESS/TASK-0021-x.md"}]}
    statuses = {".ai/tasks/IN_PROGRESS/TASK-0021-x.md": "In Progress"}
    findings = tr.reconcile({}, disk, registry, statuses)
    assert any(f.kind == "registry_status_mismatch" and f.task_id == "TASK-0021"
              for f in findings)


def test_registry_path_disagrees_with_actual_file():
    disk = {"TASK-0022": [".ai/tasks/DONE/TASK-0022-x.md"]}
    registry = {"TASK-0022": [{"status": "Done", "path": ".ai/tasks/IN_PROGRESS/TASK-0022-x.md"}]}
    statuses = {".ai/tasks/DONE/TASK-0022-x.md": "Done"}
    findings = tr.reconcile({}, disk, registry, statuses)
    assert any(f.kind == "registry_path_mismatch" and f.task_id == "TASK-0022"
              for f in findings)


# ---------------------------------------------------------------- malformed rows

def test_malformed_row_findings_reports_column_count():
    """TASK-0355-adjacent finding, found live: 26 real COMMON.md rows in
    this repo right now open like a registry row but don't parse to 9
    columns -- claim.py's own _parse_row silently drops them, identically
    to a genuinely absent row. This must be surfaced as its own kind, not
    silently folded into file_no_registry_row, because the fix is
    different (repair formatting vs. write a new row)."""
    findings = tr.malformed_row_findings({"TASK-0347": 10, "TASK-0136": 13})
    by_id = {f.task_id: f for f in findings}
    assert by_id["TASK-0347"].kind == "malformed_registry_row"
    assert "10" in by_id["TASK-0347"].detail and "9" in by_id["TASK-0347"].detail
    assert "13" in by_id["TASK-0136"].detail


def test_malformed_row_findings_empty_when_nothing_malformed():
    assert tr.malformed_row_findings({}) == []


def test_scan_malformed_registry_rows_detects_extra_column(tmp_path, monkeypatch):
    common = tmp_path / "COMMON.md"
    common.write_text(
        "| Task ID | Description | Assigned To | Status | Priority | "
        "Last Active | Claimed By | Claimed At | Path |\n"
        "| TASK-0001 | fine | Someone | Done | High | 2026-09-09 | "
        "— | — | `path.md` |\n"
        "| TASK-0002 | has an extra | Someone | Done | High | 2026-09-09 | "
        "— | — | `path.md` | — |\n",   # 10 columns -- malformed
        encoding="utf-8")
    monkeypatch.setattr(tr, "COMMON_MD", common)
    malformed = tr.scan_malformed_registry_rows()
    assert malformed == {"TASK-0002": 10}


# ---------------------------------------------------------------- word-boundary helper

def test_word_present_is_case_insensitive_whole_word():
    assert tr._word_present("Done", "Done (2026-07-24) -- H2 half: FAIL")
    assert tr._word_present("done", "DONE as a DEFECT RECORD")
    assert not tr._word_present("Done", "Undone")            # not a whole word
    assert tr._word_present("TODO", "TODO (blocked on TASK-0026.001)")


# ---------------------------------------------------------------- report rendering

def test_render_report_says_so_when_clean():
    assert "no disagreements" in tr.render_report([])


def test_render_report_never_truncates():
    findings = [tr.Finding("file_no_registry_row", "TASK-%04d" % i, "detail %d" % i)
               for i in range(50)]
    report = tr.render_report(findings)
    for i in range(50):
        assert "TASK-%04d" % i in report
    assert "50 disagreement" in report


def test_main_exit_code_reflects_findings(tmp_path, monkeypatch):
    """Exit 0 clean, 1 dirty -- the CLI contract, exercised without touching
    the real repo's own locks/COMMON.md by pointing every path constant at
    an empty scratch directory."""
    empty_tasks = tmp_path / "tasks"
    empty_tasks.mkdir()
    monkeypatch.setattr(tr, "TASKS_DIR", empty_tasks)
    monkeypatch.setattr(tr, "LOCKS_DIR", empty_tasks / ".locks")
    monkeypatch.setattr(tr, "COMMON_MD", tmp_path / "COMMON.md")
    assert tr.main([]) == 0
