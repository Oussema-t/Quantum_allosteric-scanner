"""TASK-0195 regression coverage for `check_references.py`'s dangling /
positional-reference check.

Failing-first per the task's own Planned Validation requirement: this
suite pins that a deliberately broken fixture is caught (a dangling
`[[TASK-XXXX]]` citation, and a `row N` reference with no `TASK-XXXX`
token anywhere in its own paragraph) before trusting a clean run against
real content.

Run standalone: python3 test_check_references.py
Run under pytest: pytest test_check_references.py -q
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
CHECK_PY = _HERE / "check_references.py"
CLAIM_PY = _HERE / "claim.py"


def _make_scratch_repo(tmp_path: Path, known_task_ids=("TASK-0001",)) -> Path:
    """Copies both `check_references.py` and `claim.py` into the scratch
    tree's own `.ai/tools/` (mirroring `test_claim.py`'s own pattern) so
    `check_references.py`'s `disk_task_ids()` lookup -- which walks
    `claim.py`'s own `REPO_ROOT`, computed from wherever `claim.py` itself
    was imported from -- resolves against this scratch repo's task files,
    not the real project's. Without this, the dangling-reference check
    would silently validate against the real `.ai/tasks/`, defeating the
    isolation `tmp_path` is supposed to provide."""
    repo = tmp_path / "scratch_repo"
    tools_dir = repo / ".ai" / "tools"
    tools_dir.mkdir(parents=True)
    shutil.copy(CHECK_PY, tools_dir / "check_references.py")
    shutil.copy(CLAIM_PY, tools_dir / "claim.py")

    tasks_todo = repo / ".ai" / "tasks" / "TODO"
    tasks_todo.mkdir(parents=True)
    (repo / ".ai" / "tasks" / "IN_PROGRESS").mkdir(parents=True)
    (repo / ".ai" / "tasks" / "DONE").mkdir(parents=True)
    for task_id in known_task_ids:
        (tasks_todo / ("%s-scratch.md" % task_id)).write_text("# scratch\n")
    return repo


def _run(repo: Path, *paths: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(repo / ".ai" / "tools" / "check_references.py"), *paths],
        cwd=repo, capture_output=True, text=True,
    )


class TestDanglingReference:
    def test_citation_to_a_real_task_is_not_flagged(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        doc = repo / "doc.md"
        doc.write_text("See [[TASK-0001]] for the real finding.\n")

        result = _run(repo, "doc.md")
        assert result.returncode == 0
        assert "dangling" not in result.stdout

    def test_citation_to_a_nonexistent_task_is_flagged(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        doc = repo / "doc.md"
        doc.write_text("See [[TASK-9999]] for the real finding.\n")

        result = _run(repo, "doc.md")
        assert result.returncode == 1
        assert "dangling reference [[TASK-9999]]" in result.stdout

    def test_the_documented_external_id_exception_is_not_flagged(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        doc = repo / "doc.md"
        doc.write_text(
            "see [[TASK-9000]]'s parallel program (a separate branch, "
            "val-9xxx, deliberately outside this register)\n"
        )

        result = _run(repo, "doc.md")
        assert result.returncode == 0


class TestPositionalReference:
    def test_row_reference_paired_with_a_task_id_in_same_paragraph_is_clean(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        doc = repo / "doc.md"
        doc.write_text(
            "This finding ([[TASK-0001]], row 7 above) is well supported.\n"
        )

        result = _run(repo, "doc.md")
        assert result.returncode == 0

    def test_bare_row_reference_with_no_task_id_in_its_paragraph_is_flagged(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        doc = repo / "doc.md"
        doc.write_text(
            "Intro paragraph names [[TASK-0001]].\n"
            "\n"
            "This second paragraph mentions row 5 but names no task id\n"
            "anywhere in its own text, so a reader has no way to\n"
            "re-locate the claim once the table is renumbered.\n"
        )

        result = _run(repo, "doc.md")
        assert result.returncode == 1
        assert "positional reference 'row 5'" in result.stdout

    def test_task_id_anywhere_in_the_same_paragraph_is_sufficient(self, tmp_path):
        """The anchor doesn't have to be adjacent to the word "row" --
        anywhere in the same blank-line-delimited paragraph counts, matching
        the pattern already used throughout the real RESULTS.md document."""
        repo = _make_scratch_repo(tmp_path)
        doc = repo / "doc.md"
        doc.write_text(
            "A long paragraph starts here and eventually gets to row 12,\n"
            "which is discussed at length, before finally citing\n"
            "[[TASK-0001]] several lines later in the same paragraph.\n"
        )

        result = _run(repo, "doc.md")
        assert result.returncode == 0


class TestCleanFixtureBaseline:
    def test_a_fully_clean_file_exits_zero_with_a_summary(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        doc = repo / "doc.md"
        doc.write_text("Nothing to see here. [[TASK-0001]] is real.\n")

        result = _run(repo, "doc.md")
        assert result.returncode == 0
        assert "clean" in result.stdout


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
