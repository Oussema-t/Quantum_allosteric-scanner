"""TASK-0198 regression coverage — `claim.py`'s chained-transition
duplicate-tracking defect: `move TASK-X A -> B` immediately followed by
`move TASK-X B -> C` (or `resolve ... DONE`), with no `git commit` in
between, could in principle leave the *original* starting path (`A`)
still tracked once something finally commits, even though the working
tree is correct throughout.

Runs entirely against an isolated, throwaway scratch git repo per test
(never the real project repo) — copies `claim.py` itself into that
scratch tree and invokes it exactly as a real caller would, via
subprocess, not by importing internals, except where a unit test on
`_assert_single_tracked_path` itself is more direct than round-tripping
through the CLI.

Run standalone: python3 test_claim.py
Run under pytest: pytest test_claim.py -q
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
CLAIM_PY = _HERE / "claim.py"


def _make_scratch_repo(tmp_path: Path) -> Path:
    """A throwaway repo with the same `.ai/tasks/{TODO,IN_PROGRESS,DONE,
    .locks}` + `.ai/tools/claim.py` shape the real repo has, with one
    committed task file at `.ai/tasks/TODO/TASK-9001-scratch.md` — the
    "tracked in an earlier commit" precondition both real incidents
    (TASK-0189, TASK-0073) shared."""
    repo = tmp_path / "scratch_repo"
    (repo / ".ai" / "tools").mkdir(parents=True)
    (repo / ".ai" / "tasks" / "TODO").mkdir(parents=True)
    (repo / ".ai" / "tasks" / "IN_PROGRESS").mkdir(parents=True)
    (repo / ".ai" / "tasks" / "DONE").mkdir(parents=True)
    (repo / ".ai" / "tasks" / ".locks").mkdir(parents=True)
    shutil.copy(CLAIM_PY, repo / ".ai" / "tools" / "claim.py")

    (repo / ".ai" / "COMMON.md").write_text(
        "# COMMON.md scratch\n\n"
        "| TASK-ID | Description | Assigned To | Status | Priority | "
        "Last Active | Claimed By | Claimed At | Path |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
        "| TASK-9001 | scratch repro task | Implementer | TODO | P2 | "
        "2026-08-16 | — | — | "
        "`.ai/tasks/TODO/TASK-9001-scratch.md` |\n"
    )
    (repo / ".ai" / "tasks" / "TODO" / "TASK-9001-scratch.md").write_text(
        "# TASK-9001 scratch repro task\n\n"
        "- Status: TODO\n- Claimed By: —\n- Claimed At: —\n\n"
        "original content\n"
    )

    def _git(*args):
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)

    _git("init", "-q")
    _git("config", "user.email", "test@test.com")
    _git("config", "user.name", "test")
    _git("add", "-A")
    _git("commit", "-q", "-m", "initial commit with TASK-9001 in TODO")
    return repo


def _claim(repo: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(repo / ".ai" / "tools" / "claim.py"), *args],
        cwd=repo, capture_output=True, text=True,
    )


def _tracked_paths_for(repo: Path, task_id: str) -> list[str]:
    out = subprocess.run(
        ["git", "ls-tree", "-r", "HEAD", "--name-only"],
        cwd=repo, capture_output=True, text=True, check=True,
    ).stdout
    return [line for line in out.splitlines() if f"{task_id}-" in line and line.endswith(".md")]


class TestChainedTransitionNoDuplicate:
    """The regression test this task's own Planned Validation asks for:
    the exact reproduction sequence, asserting only one path is tracked
    for the task id after the final `move`, once something commits."""

    def test_move_move_no_commit_between(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        assert _claim(repo, "claim", "TASK-9001", "test").returncode == 0
        assert _claim(repo, "move", "TASK-9001", "IN_PROGRESS", "--as", "test").returncode == 0

        (repo / ".ai" / "tasks" / "IN_PROGRESS" / "TASK-9001-scratch.md").write_text(
            "# TASK-9001 scratch repro task\n\n"
            "- Status: In Progress\n- Claimed By: test\n- Claimed At: x\n\n"
            "manually edited content, added between move 1 and move 2\n"
        )

        result = _claim(repo, "move", "TASK-9001", "DONE", "--as", "test")
        assert result.returncode == 0

        subprocess.run(["git", "commit", "-q", "-m", "chained move"], cwd=repo, check=True)

        tracked = _tracked_paths_for(repo, "TASK-9001")
        assert tracked == [".ai/tasks/DONE/TASK-9001-scratch.md"], (
            f"expected exactly one tracked path, got {tracked!r}"
        )

    def test_move_resolve_no_commit_between(self, tmp_path):
        """Same shape, `resolve` instead of a second `move` for the final
        hop -- this project's own more common way to close out a task."""
        repo = _make_scratch_repo(tmp_path)
        assert _claim(repo, "claim", "TASK-9001", "test").returncode == 0
        assert _claim(repo, "move", "TASK-9001", "IN_PROGRESS", "--as", "test").returncode == 0

        (repo / ".ai" / "tasks" / "IN_PROGRESS" / "TASK-9001-scratch.md").write_text(
            "# TASK-9001 scratch repro task\n\n"
            "- Status: In Progress\n- Claimed By: test\n- Claimed At: x\n\n"
            "edited before resolve\n"
        )

        result = _claim(repo, "resolve", "TASK-9001", "done", "--as", "test")
        assert result.returncode == 0

        subprocess.run(["git", "commit", "-q", "-m", "move then resolve"], cwd=repo, check=True)

        tracked = _tracked_paths_for(repo, "TASK-9001")
        assert tracked == [".ai/tasks/DONE/TASK-9001-scratch.md"], (
            f"expected exactly one tracked path, got {tracked!r}"
        )

    def test_warning_printed_if_the_guard_ever_does_fire(self, tmp_path):
        """Not a reproduction (five real variations, documented in
        `_assert_single_tracked_path`'s own docstring, never reproduced
        the natural defect) -- this asserts the *reporting* path itself:
        if a future scenario (or a concurrent-thread race this
        single-process test cannot force) ever does leave a duplicate,
        `move` must say so on stderr, not stay silent. Directly exercises
        `_warn_if_duplicate_tracked` against a synthetic finding, the
        same function `move`/`resolve` call internally."""
        repo = _make_scratch_repo(tmp_path)
        sys.path.insert(0, str(repo / ".ai" / "tools"))
        try:
            import claim as scratch_claim

            import io
            import contextlib

            buf = io.StringIO()
            with contextlib.redirect_stderr(buf):
                scratch_claim._warn_if_duplicate_tracked(
                    "TASK-9001",
                    [".ai/tasks/TODO/TASK-9001-scratch.md", ".ai/tasks/DONE/TASK-9001-scratch.md"],
                )
            assert "MORE THAN ONE path" in buf.getvalue()
            assert "TASK-0198" in buf.getvalue()
        finally:
            sys.path.remove(str(repo / ".ai" / "tools"))
            sys.modules.pop("claim", None)


class TestAssertSingleTrackedPath:
    """Unit coverage on the guard function itself -- proves the detection
    mechanism works against the exact stated symptom (two tracked paths
    for one task id), independent of whether a natural trigger was
    reproducible."""

    def test_healthy_single_path_returns_none(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        sys.path.insert(0, str(repo / ".ai" / "tools"))
        try:
            import claim as scratch_claim

            assert scratch_claim._assert_single_tracked_path("TASK-9001") is None
        finally:
            sys.path.remove(str(repo / ".ai" / "tools"))
            sys.modules.pop("claim", None)

    def test_synthetic_duplicate_is_detected(self, tmp_path):
        """Manually stages a second, stale path for the same task id
        (what the reported defect's *end state* looks like) and confirms
        the guard catches it -- built by staging two real files directly,
        not by trying to force `move`/`resolve` into producing it."""
        repo = _make_scratch_repo(tmp_path)
        (repo / ".ai" / "tasks" / "TODO" / "TASK-9002-scratch.md").write_text("stale\n")
        (repo / ".ai" / "tasks" / "DONE" / "TASK-9002-scratch.md").write_text("real\n")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)

        sys.path.insert(0, str(repo / ".ai" / "tools"))
        try:
            import claim as scratch_claim

            result = scratch_claim._assert_single_tracked_path("TASK-9002")
            assert result is not None
            assert len(result) == 2
            assert any("TODO" in p for p in result)
            assert any("DONE" in p for p in result)
        finally:
            sys.path.remove(str(repo / ".ai" / "tools"))
            sys.modules.pop("claim", None)

    def test_nonexistent_task_id_returns_none(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        sys.path.insert(0, str(repo / ".ai" / "tools"))
        try:
            import claim as scratch_claim

            assert scratch_claim._assert_single_tracked_path("TASK-0000-nope") is None
        finally:
            sys.path.remove(str(repo / ".ai" / "tools"))
            sys.modules.pop("claim", None)


class TestResourceIdSupport:
    """TASK-0195 / TASK-0024.001: `claim.py` must accept a digit-free
    argument (e.g. a bare filename like `RESULTS.md`, or a path with
    slashes) as a literal whole-file/arbitrary resource id instead of
    erroring, while a digit-bearing argument still resolves as a
    `TASK-XXXX[.NNN]` id exactly as before -- both behaviors checked here
    so a future change can't silently narrow or widen which strings take
    which path."""

    def test_digit_free_argument_round_trips_through_claim_status_release(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        assert _claim(repo, "claim", "RESULTS.md", "test").returncode == 0

        status = _claim(repo, "status", "RESULTS.md")
        assert status.returncode == 0
        assert "RESOURCE-RESULTS.MD" in status.stdout
        assert "claimed by 'test'" in status.stdout

        released = _claim(repo, "release", "RESULTS.md", "--claimant", "test")
        assert released.returncode == 0
        assert "RESOURCE-RESULTS.MD" in released.stdout

    def test_second_claim_on_same_resource_id_is_refused(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        assert _claim(repo, "claim", "RESULTS.md", "thread-a").returncode == 0

        blocked = _claim(repo, "claim", "RESULTS.md", "thread-b")
        assert blocked.returncode != 0
        assert "already claimed" in blocked.stderr

    def test_move_refuses_a_resource_id(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        assert _claim(repo, "claim", "RESULTS.md", "test").returncode == 0
        result = _claim(repo, "move", "RESULTS.md", "DONE", "--as", "test")
        assert result.returncode != 0
        assert "only operates on TASK-XXXX" in result.stderr

    def test_resolve_refuses_a_resource_id(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        assert _claim(repo, "claim", "RESULTS.md", "test").returncode == 0
        result = _claim(repo, "resolve", "RESULTS.md", "done", "--as", "test")
        assert result.returncode != 0
        assert "only operates on TASK-XXXX" in result.stderr

    def test_argument_containing_a_digit_still_resolves_as_a_task_id(self, tmp_path):
        """Regression guard: widening the digit-free path must not change
        how a normal TASK-XXXX-shaped (or bare-numeric) argument resolves."""
        repo = _make_scratch_repo(tmp_path)
        assert _claim(repo, "claim", "9001", "test").returncode == 0
        status = _claim(repo, "status", "TASK-9001")
        assert "TASK-9001: claimed by 'test'" in status.stdout


class TestCheckStaleness:
    """TASK-0195: content-hash staleness detection. Deliberately not
    git-ancestry-based -- see this task's own Done section for the replay
    of the real incident (RESULTS.md rows 47-53) that showed an
    ancestry-based check would not have caught it, because every commit
    involved was correctly based on its true immediate git parent; the
    actual collision was between concurrently-active, uncommitted
    working-tree edits, which only a content snapshot can see."""

    def test_reports_clean_immediately_after_claim(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        target = repo / "shared_doc.md"
        target.write_text("v1\n")

        assert _claim(repo, "claim", "shared_doc.md", "test").returncode == 0
        result = _claim(repo, "check-staleness", "shared_doc.md")
        assert result.returncode == 0
        assert "no drift since claim" in result.stdout

    def test_detects_drift_from_a_concurrent_edit(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        target = repo / "shared_doc.md"
        target.write_text("v1\n")

        assert _claim(repo, "claim", "shared_doc.md", "test").returncode == 0
        target.write_text("v2, written by a different thread\n")

        result = _claim(repo, "check-staleness", "shared_doc.md")
        assert result.returncode == 1
        assert "STALE" in result.stderr

    def test_requires_an_active_claim(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        (repo / "shared_doc.md").write_text("v1\n")

        result = _claim(repo, "check-staleness", "shared_doc.md")
        assert result.returncode == 1
        assert "not currently claimed" in result.stderr

    def test_no_snapshot_recorded_for_a_non_path_resource_id(self, tmp_path):
        """A resource id that was never a real path at claim time (the
        ordinary GIT-COMMIT case, or any bare symbolic label) has nothing
        to compare against -- must say so, not crash or false-flag."""
        repo = _make_scratch_repo(tmp_path)
        assert _claim(repo, "claim", "GIT-COMMIT", "test").returncode == 0

        result = _claim(repo, "check-staleness", "GIT-COMMIT")
        assert result.returncode == 0
        assert "no content snapshot was recorded" in result.stdout


class TestStageRestagesEditedContent:
    """TASK-0223: `stage --expect <path>` must pick up an edit made to
    `<path>` *after* an earlier call already staged it (e.g. `move`'s own
    internal `git mv`) -- `_staged_paths()`'s "already staged, skip
    `git add`" optimization (TASK-0197) only checks whether the path
    differs from HEAD, not whether the staged blob still matches the
    current working tree, so a post-move edit was silently dropped from
    the next `stage` call. Reproduced twice this session ([[TASK-0195]],
    [[TASK-0220]]) via the exact sequence here: `move` (auto-stages),
    edit the file again, `stage --expect` the same path a second time."""

    def test_stage_picks_up_an_edit_made_after_an_earlier_stage(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        assert _claim(repo, "claim", "TASK-9001", "test").returncode == 0
        assert _claim(repo, "claim", "GIT-COMMIT", "test").returncode == 0

        moved = _claim(repo, "move", "TASK-9001", "IN_PROGRESS", "--as", "test")
        assert moved.returncode == 0
        target = repo / ".ai" / "tasks" / "IN_PROGRESS" / "TASK-9001-scratch.md"
        rel = ".ai/tasks/IN_PROGRESS/TASK-9001-scratch.md"

        # `move` already staged `target` via its own internal `git mv` --
        # the defect is a *second* edit, made after that, being dropped by
        # a *second* `stage --expect` call for the same path.
        target.write_text(target.read_text() + "\nedited after move, before stage\n")

        result = _claim(repo, "stage", "--expect", rel)
        assert result.returncode == 0, result.stderr

        staged_blob = subprocess.run(
            ["git", "show", f":{rel}"], cwd=repo, capture_output=True, text=True, check=True,
        ).stdout
        assert "edited after move, before stage" in staged_blob, (
            "stage --expect reported success but the staged content is stale "
            "relative to the working tree -- TASK-0223's own regression"
        )

    def test_task0197_deletion_case_still_works(self, tmp_path):
        """Regression guard on the case TASK-0223's fix must not break:
        a path already fully staged as a deletion (gone from both index
        and working tree) must not be re-passed to `git add` (which
        errors: 'pathspec ... did not match any files', TASK-0197's own
        real incident)."""
        repo = _make_scratch_repo(tmp_path)
        assert _claim(repo, "claim", "GIT-COMMIT", "test").returncode == 0
        rel = ".ai/tasks/TODO/TASK-9001-scratch.md"

        (repo / rel).unlink()
        first_delete = _claim(repo, "stage", "--expect", rel)
        assert first_delete.returncode == 0, first_delete.stderr

        second_delete = _claim(repo, "stage", "--expect", rel)
        assert second_delete.returncode == 0, second_delete.stderr


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
