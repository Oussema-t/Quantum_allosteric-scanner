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

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
CLAIM_PY = _HERE / "claim.py"

# TASK-0375: reuse claim.py's own arch-fallback (`_git`) for every git call
# THIS file makes to set up/verify a scratch repo, rather than a second,
# unpatched copy of the same machine-specific workaround -- every one of
# them is just as exposed to the bug (a python-subprocess git call routing
# through this machine's broken x86_64 xcrun) as claim.py's own internals.
sys.path.insert(0, str(_HERE))
import claim as _claim_tool  # noqa: E402  (path insert must precede this import)


def _git(args, cwd, check=True, capture_output=True):
    # type: (list, Path, bool, bool) -> subprocess.CompletedProcess
    return _claim_tool._git(args, check=check, capture_output=capture_output, cwd=str(cwd))


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

    _git(["init", "-q"], repo)
    _git(["config", "user.email", "test@test.com"], repo)
    _git(["config", "user.name", "test"], repo)
    _git(["add", "-A"], repo)
    _git(["commit", "-q", "-m", "initial commit with TASK-9001 in TODO"], repo)
    return repo


def _claim(repo: Path, *args, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(repo / ".ai" / "tools" / "claim.py"), *args],
        cwd=repo, capture_output=True, text=True, env=env,
    )


def _tracked_paths_for(repo: Path, task_id: str) -> list[str]:
    out = _git(["ls-tree", "-r", "HEAD", "--name-only"], repo).stdout
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

        _git(["commit", "-q", "-m", "chained move"], repo)

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

        _git(["commit", "-q", "-m", "move then resolve"], repo)

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
        _git(["add", "-A"], repo)

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

    def test_filename_with_a_digit_is_a_resource_not_a_misread_task_id(self, tmp_path):
        """TASK-0024.001: the earlier `re.search` for a digit anywhere in
        the argument silently mapped a real filename like
        `PHASE1_SUBMISSION_V3.md` to `TASK-0001`. It must be a resource id
        -- the whole string is not a clean task-id shape."""
        repo = _make_scratch_repo(tmp_path)
        result = _claim(repo, "claim", "PHASE1_SUBMISSION_V3.md", "test")
        assert result.returncode == 0
        assert "RESOURCE-PHASE1_SUBMISSION_V3.MD" in result.stdout
        assert "TASK-0001" not in result.stdout

        status = _claim(repo, "status", "PHASE1_SUBMISSION_V3.md")
        assert "RESOURCE-PHASE1_SUBMISSION_V3.MD" in status.stdout
        # and TASK-0001 itself is untouched
        assert _claim(repo, "status", "TASK-0001").stdout.strip().endswith("unclaimed")

    def test_bare_and_prefixed_forms_resolve_to_the_same_task_id(self, tmp_path):
        """The anchored shape must not narrow any documented form: `9001`,
        `TASK-9001`, and `task-9001` all still name the same lock."""
        repo = _make_scratch_repo(tmp_path)
        assert _claim(repo, "claim", "9001", "t").returncode == 0
        for form in ("TASK-9001", "9001", "task-9001"):
            assert "TASK-9001: claimed by 't'" in _claim(repo, "status", form).stdout
        # a second claim via a different surface form is still refused --
        # proves they collapse to one id, not three
        assert _claim(repo, "claim", "TASK-9001", "u").returncode != 0

    def test_dotted_subtask_shape_still_resolves(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        assert _claim(repo, "claim", "9001.2", "t").returncode == 0
        assert "TASK-9001.002: claimed by 't'" in _claim(repo, "status", "TASK-9001.002").stdout

    def test_sync_ignores_a_resource_id_lock(self, tmp_path):
        """Planned Validation: `sync --check` must stay clean when the only
        lock present is a resource-id lock with no registry row -- it must
        not warn 'no task file on disk' for it (that warning is scoped to
        real TASK-XXXX ids)."""
        repo = _make_scratch_repo(tmp_path)
        before = _claim(repo, "sync", "--check")
        assert _claim(repo, "claim", "RESULTS.md", "test").returncode == 0
        after = _claim(repo, "sync", "--check")
        assert after.returncode == before.returncode, (
            "adding a resource-id lock changed sync --check's verdict"
        )
        assert "RESOURCE-RESULTS.MD" not in after.stdout
        assert "RESOURCE-RESULTS.MD" not in after.stderr
        assert "RESULTS.md" not in after.stderr


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
        old_rel = ".ai/tasks/TODO/TASK-9001-scratch.md"  # TASK-0024.002: a
        # rename always splits into two --expect entries now (old path
        # removed, new path added) -- unrelated to this test's own subject
        # (a post-move content edit getting picked up), just the current
        # correct --expect shape for the `move` this test performs.

        # `move` already staged `target` via its own internal `git mv` --
        # the defect is a *second* edit, made after that, being dropped by
        # a *second* `stage --expect` call for the same path.
        target.write_text(target.read_text() + "\nedited after move, before stage\n")

        result = _claim(repo, "stage", "--expect", old_rel, rel)
        assert result.returncode == 0, result.stderr

        staged_blob = _git(["show", f":{rel}"], repo).stdout
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


class TestRenameAlwaysSplitsIntoTwoPaths:
    """TASK-0024.002: real incident, 2026-07-09 -- whether a renamed path
    collapsed to one --expect entry or split into two (old removed, new
    added) depended on git's own content-similarity rename-detection
    threshold, not on anything the caller controlled. `move TASK-9001
    DONE` (small file, plain Status-line rewrite) stayed above the
    threshold and collapsed to one path; the same command on a file with
    a large `## Done` section dropped below it and split into two --
    identical shape of call, opposite --expect requirement, discoverable
    only by having the call fail and reading the error.

    `_staged_paths()` now always passes --no-renames, so both cases below
    must behave identically: a rename is unconditionally two entries."""

    def test_small_edit_rename_requires_both_paths(self, tmp_path):
        """Before this fix, this was the surprising case: a short file's
        Status-line-only rewrite stayed above git's similarity threshold,
        so the rename collapsed to one path and --expect with only the
        new path used to pass. It must now fail, naming the old path as
        unexpectedly staged -- exactly like the large-edit case below."""
        repo = _make_scratch_repo(tmp_path)
        assert _claim(repo, "claim", "TASK-9001", "test").returncode == 0

        moved = _claim(repo, "move", "TASK-9001", "IN_PROGRESS", "--as", "test")
        assert moved.returncode == 0, moved.stderr
        old_path = ".ai/tasks/TODO/TASK-9001-scratch.md"
        new_path = ".ai/tasks/IN_PROGRESS/TASK-9001-scratch.md"

        new_only = _claim(repo, "commit-guard", "--expect", new_path)
        assert new_only.returncode == 1
        assert old_path in new_only.stderr

        both = _claim(repo, "commit-guard", "--expect", old_path, new_path)
        assert both.returncode == 0, both.stderr

    def test_large_edit_rename_requires_both_paths(self, tmp_path):
        """The case that already worked correctly before this fix --
        confirm it still does, so the fix closed the gap rather than
        just relocating which case is the surprising one."""
        repo = _make_scratch_repo(tmp_path)
        assert _claim(repo, "claim", "TASK-9001", "test").returncode == 0
        target = repo / ".ai" / "tasks" / "TODO" / "TASK-9001-scratch.md"
        target.write_text(target.read_text() + ("\nmore content\n" * 50))

        moved = _claim(repo, "move", "TASK-9001", "DONE", "--as", "test")
        assert moved.returncode == 0, moved.stderr
        old_path = ".ai/tasks/TODO/TASK-9001-scratch.md"
        new_path = ".ai/tasks/DONE/TASK-9001-scratch.md"

        new_only = _claim(repo, "commit-guard", "--expect", new_path)
        assert new_only.returncode == 1
        assert old_path in new_only.stderr

        both = _claim(repo, "commit-guard", "--expect", old_path, new_path)
        assert both.returncode == 0, both.stderr

    def test_stage_self_verification_also_requires_both_paths(self, tmp_path):
        """Same rule via `stage`'s own self-verification step (shared
        `_staged_paths()`/`_compare_staged()`), not just `commit-guard`
        called directly."""
        repo = _make_scratch_repo(tmp_path)
        assert _claim(repo, "claim", "TASK-9001", "test").returncode == 0
        assert _claim(repo, "claim", "GIT-COMMIT", "test").returncode == 0

        moved = _claim(repo, "move", "TASK-9001", "IN_PROGRESS", "--as", "test")
        assert moved.returncode == 0, moved.stderr
        old_path = ".ai/tasks/TODO/TASK-9001-scratch.md"
        new_path = ".ai/tasks/IN_PROGRESS/TASK-9001-scratch.md"

        # `move` already staged both paths; re-asserting only the new one
        # via `stage` must fail self-verification, not silently accept a
        # partial --expect.
        new_only = _claim(repo, "stage", "--expect", new_path)
        assert new_only.returncode == 1
        assert old_path in new_only.stderr


class TestExpectEmptyIncompatibleWithMove:
    """TASK-0356: `--expect-empty` cannot pass immediately after `move`,
    which legitimately leaves its own rename staged -- and closing a task
    then committing it is the ordinary order of work, not an edge case.
    Reproduced live twice in one week (TASK-0330, and again inside the
    commit that filed this task). The fix is not to weaken
    `--expect-empty` (it must keep failing here -- that's the correct,
    documented behaviour now) but to route the ordinary post-`move` case
    around it entirely: straight to `stage --expect <paths incl. the
    rename>`, whose own self-verification gives the identical
    contamination check one step later."""

    def test_expect_empty_still_correctly_fails_after_move(self, tmp_path):
        """Confirm the guard is not weakened into tolerating a dirty
        index -- it must still fail here, naming exactly what's staged."""
        repo = _make_scratch_repo(tmp_path)
        assert _claim(repo, "claim", "TASK-9001", "test").returncode == 0
        moved = _claim(repo, "move", "TASK-9001", "IN_PROGRESS", "--as", "test")
        assert moved.returncode == 0, moved.stderr

        result = _claim(repo, "commit-guard", "--expect-empty")
        assert result.returncode == 1
        assert "TASK-9001-scratch.md" in result.stderr

    def test_revised_sequence_skips_expect_empty_and_completes(self, tmp_path):
        """The acceptance bar this task states explicitly: the whole
        *documented* sequence, run after a `move`, must complete -- not
        the guard checked in isolation. No `--expect-empty` step."""
        repo = _make_scratch_repo(tmp_path)
        assert _claim(repo, "claim", "TASK-9001", "test").returncode == 0
        moved = _claim(repo, "move", "TASK-9001", "IN_PROGRESS", "--as", "test")
        assert moved.returncode == 0, moved.stderr
        old_path = ".ai/tasks/TODO/TASK-9001-scratch.md"
        new_path = ".ai/tasks/IN_PROGRESS/TASK-9001-scratch.md"

        assert _claim(repo, "claim", "GIT-COMMIT", "test").returncode == 0

        staged = _claim(repo, "stage", "--expect", old_path, new_path)
        assert staged.returncode == 0, staged.stderr

        msg = tmp_path / "msg.txt"
        msg.write_text("TASK-9001: sequence smoke test\n")
        committed = _claim(
            repo, "commit-guard", "--expect", old_path, new_path,
            "--commit", "--message-file", str(msg),
        )
        assert committed.returncode == 0, committed.stderr

        released = _claim(repo, "release", "GIT-COMMIT")
        assert released.returncode == 0, released.stderr

        log = _git(["log", "--oneline", "-1"], repo).stdout
        assert "sequence smoke test" in log


class TestCommitGuardCommitMode:
    """TASK-0356: `commit-guard --expect ... --commit --message-file PATH`
    fuses the path-list check and the actual `git commit` into one
    process. Real incident this closes: the previously-documented
    two-step boundary (`commit-guard --expect ... | tail -1 && git
    commit ...`) silently committed anyway on a *failing* guard, because
    `pipefail` is off by default in this shell and `&&` after a pipe
    tests `tail`'s exit status, not the guard's -- happened twice,
    including inside the commit that filed this task. There is no
    separate shell step here for that idiom to attach to."""

    def _prep_staged_commit_file(self, repo: Path, tmp_path: Path) -> tuple[str, Path]:
        rel = ".ai/tasks/TODO/TASK-9001-scratch.md"
        (repo / rel).write_text((repo / rel).read_text() + "\nedited for commit test\n")
        assert _claim(repo, "claim", "GIT-COMMIT", "test").returncode == 0
        assert _claim(repo, "stage", "--expect", rel).returncode == 0
        msg = tmp_path / "msg.txt"
        msg.write_text("TASK-9001: commit-guard --commit smoke test\n")
        return rel, msg

    def test_commit_succeeds_when_expect_matches_and_session_is_valid(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        rel, msg = self._prep_staged_commit_file(repo, tmp_path)

        before = _git(["log", "--oneline"], repo).stdout

        result = _claim(repo, "commit-guard", "--expect", rel, "--commit", "--message-file", str(msg))
        assert result.returncode == 0, result.stderr
        assert "committed" in result.stdout

        after = _git(["log", "--oneline"], repo).stdout
        assert after != before
        assert "commit-guard --commit smoke test" in after

        status = _git(["status", "--porcelain"], repo).stdout
        real_changes = [l for l in status.splitlines() if ".locks" not in l]
        assert not real_changes, "expected a clean tree after the atomic commit"

    def test_refuses_and_does_not_commit_on_path_mismatch(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        rel, msg = self._prep_staged_commit_file(repo, tmp_path)

        before = _git(["log", "--oneline"], repo).stdout

        result = _claim(
            repo, "commit-guard", "--expect", ".ai/COMMON.md",  # wrong path
            "--commit", "--message-file", str(msg),
        )
        assert result.returncode == 1
        assert rel in result.stderr

        after = _git(["log", "--oneline"], repo).stdout
        assert after == before, "a mismatched --expect must not commit anything"

    def test_refuses_and_does_not_commit_when_git_commit_unclaimed(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        rel = ".ai/tasks/TODO/TASK-9001-scratch.md"
        (repo / rel).write_text((repo / rel).read_text() + "\nedited, but never claimed GIT-COMMIT\n")
        # Stage directly with plain git (bypassing `stage`'s own
        # claim-required check) to isolate --commit's own re-verification.
        _git(["add", rel], repo)
        msg = tmp_path / "msg.txt"
        msg.write_text("should never land\n")

        before = _git(["log", "--oneline"], repo).stdout

        result = _claim(repo, "commit-guard", "--expect", rel, "--commit", "--message-file", str(msg))
        assert result.returncode == 1
        assert "not currently claimed" in result.stderr

        after = _git(["log", "--oneline"], repo).stdout
        assert after == before

    def test_refuses_and_does_not_commit_on_session_id_mismatch(self, tmp_path):
        """The specific gap this task found and closed: --commit's own
        `git commit` subprocess is invisible to `git_commit_guard_hook.py`
        (that hook only inspects the one literal Bash command the harness
        matched, never a child process it spawns) -- so --commit must
        re-verify GIT-COMMIT session identity itself, in-process, exactly
        as strictly as the hook does for an ordinary `git commit` call."""
        repo = _make_scratch_repo(tmp_path)
        rel = ".ai/tasks/TODO/TASK-9001-scratch.md"
        (repo / rel).write_text((repo / rel).read_text() + "\nedited under a foreign claim\n")

        foreign_env = dict(os.environ)
        foreign_env["CLAUDE_CODE_SESSION_ID"] = "foreign-session-aaaa"
        assert _claim(repo, "claim", "GIT-COMMIT", "test", env=foreign_env).returncode == 0
        assert _claim(repo, "stage", "--expect", rel, env=foreign_env).returncode == 0

        msg = tmp_path / "msg.txt"
        msg.write_text("should never land\n")

        this_session_env = dict(os.environ)
        this_session_env["CLAUDE_CODE_SESSION_ID"] = "this-session-bbbb"

        before = _git(["log", "--oneline"], repo).stdout

        result = _claim(
            repo, "commit-guard", "--expect", rel, "--commit", "--message-file", str(msg),
            env=this_session_env,
        )
        assert result.returncode == 1
        assert "not this session" in result.stderr

        after = _git(["log", "--oneline"], repo).stdout
        assert after == before, "a session_id mismatch must not commit anything"

    def test_refuses_combination_with_expect_empty(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        assert _claim(repo, "claim", "GIT-COMMIT", "test").returncode == 0
        msg = tmp_path / "msg.txt"
        msg.write_text("irrelevant\n")

        result = _claim(repo, "commit-guard", "--expect-empty", "--commit", "--message-file", str(msg))
        assert result.returncode == 1
        assert "--expect-empty" in result.stderr

    def test_refuses_missing_message_file(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        rel, _ = self._prep_staged_commit_file(repo, tmp_path)

        result = _claim(repo, "commit-guard", "--expect", rel, "--commit")
        assert result.returncode == 1
        assert "--message-file" in result.stderr

        missing = tmp_path / "does-not-exist.txt"
        result2 = _claim(repo, "commit-guard", "--expect", rel, "--commit", "--message-file", str(missing))
        assert result2.returncode == 1
        assert "does not exist" in result2.stderr


class TestAddAttributedStageAndAnnotate:
    """TASK-0061: `claim.py add` -- attributed stage-and-annotate, any
    path. Complementary to `stage` (bulk, .ai/.claude-scoped, exact-match
    self-verify), not a replacement: `add` is incremental/per-file and
    deliberately unscoped by directory, since its safety property is
    attribution (a real TASK-ID + a mandatory --purpose, permanently
    recorded in that task's own file), not a path prefix."""

    def test_single_file_add_outside_ai_claude_stages_and_annotates(self, tmp_path):
        """The whole point of this task: `stage`'s own .ai/.claude
        restriction must NOT apply to `add`."""
        repo = _make_scratch_repo(tmp_path)
        (repo / "backend").mkdir()
        (repo / "backend" / "outside.py").write_text("# outside .ai/.claude\n")

        result = _claim(repo, "add", "TASK-9001", "backend/outside.py", "--purpose", "wires up the new thing")
        assert result.returncode == 0, result.stderr

        staged = _git(["diff", "--cached", "--name-only"], repo).stdout.split()
        assert "backend/outside.py" in staged
        assert ".ai/tasks/TODO/TASK-9001-scratch.md" in staged, (
            "the task file's own edit (the new annotation) must be staged too"
        )

        content = (repo / ".ai/tasks/TODO/TASK-9001-scratch.md").read_text()
        assert "## Staged Files" in content
        assert "`backend/outside.py` -- wires up the new thing" in content

    def test_creates_section_immediately_before_done_heading(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        task_path = repo / ".ai/tasks/TODO/TASK-9001-scratch.md"
        task_path.write_text(
            "# TASK-9001 scratch\n\n- Status: TODO\n\n## Context\n\nsome context\n\n## Done\n\n(not yet)\n"
        )
        _git(["add", "-A"], repo)
        _git(["commit", "-q", "-m", "task file with a Done heading"], repo)
        (repo / "backend").mkdir()
        (repo / "backend" / "x.py").write_text("# x\n")

        result = _claim(repo, "add", "TASK-9001", "backend/x.py", "--purpose", "test")
        assert result.returncode == 0, result.stderr

        content = task_path.read_text()
        assert content.index("## Staged Files") < content.index("## Done"), (
            "new section must land before ## Done, not after it or at raw EOF"
        )
        assert "(not yet)" in content, "## Done's own content must be untouched"

    def test_second_add_appends_to_existing_section_in_call_order(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        (repo / "backend").mkdir()
        (repo / "backend" / "a.py").write_text("# a\n")
        (repo / "backend" / "b.py").write_text("# b\n")

        first = _claim(repo, "add", "TASK-9001", "backend/a.py", "--purpose", "first")
        assert first.returncode == 0, first.stderr
        second = _claim(repo, "add", "TASK-9001", "backend/b.py", "--purpose", "second")
        assert second.returncode == 0, second.stderr

        content = (repo / ".ai/tasks/TODO/TASK-9001-scratch.md").read_text()
        assert content.count("## Staged Files") == 1, "must not create a second section"
        assert content.index("`backend/a.py`") < content.index("`backend/b.py`"), "entries must stay in call order"

    def test_batch_manifest_array_form(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        (repo / "backend").mkdir()
        (repo / "backend" / "a.py").write_text("# a\n")
        (repo / "backend" / "b.py").write_text("# b\n")
        manifest = tmp_path / "manifest.json"
        manifest.write_text(json.dumps([
            {"file": "backend/a.py", "purpose": "reason A"},
            {"file": "backend/b.py", "purpose": "reason B"},
        ]))

        result = _claim(repo, "add", "TASK-9001", "--from-file", str(manifest))
        assert result.returncode == 0, result.stderr

        content = (repo / ".ai/tasks/TODO/TASK-9001-scratch.md").read_text()
        assert "`backend/a.py` -- reason A" in content
        assert "`backend/b.py` -- reason B" in content
        staged = _git(["diff", "--cached", "--name-only"], repo).stdout.split()
        assert "backend/a.py" in staged and "backend/b.py" in staged

    def test_batch_manifest_object_form_shared_and_override_purpose(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        (repo / "backend").mkdir()
        (repo / "backend" / "a.py").write_text("# a\n")
        (repo / "backend" / "b.py").write_text("# b\n")
        (repo / "backend" / "c.py").write_text("# c\n")
        manifest = tmp_path / "manifest.json"
        manifest.write_text(json.dumps({
            "purpose": "shared reason",
            "files": ["backend/a.py", "backend/b.py", {"file": "backend/c.py", "purpose": "override reason"}],
        }))

        result = _claim(repo, "add", "TASK-9001", "--from-file", str(manifest))
        assert result.returncode == 0, result.stderr

        content = (repo / ".ai/tasks/TODO/TASK-9001-scratch.md").read_text()
        assert "`backend/a.py` -- shared reason" in content
        assert "`backend/b.py` -- shared reason" in content
        assert "`backend/c.py` -- override reason" in content

    def test_unknown_task_id_refuses(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        result = _claim(repo, "add", "TASK-9999", "some/path.py", "--purpose", "x")
        assert result.returncode != 0
        assert "no task file found" in result.stderr

    def test_malformed_manifest_json_refuses_with_no_side_effects(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        (repo / "backend").mkdir()
        (repo / "backend" / "a.py").write_text("# a\n")
        manifest = tmp_path / "bad.json"
        manifest.write_text("{not valid json")

        before = _git(["diff", "--cached", "--name-only"], repo).stdout
        result = _claim(repo, "add", "TASK-9001", "--from-file", str(manifest))
        assert result.returncode != 0
        assert "malformed manifest" in result.stderr
        after = _git(["diff", "--cached", "--name-only"], repo).stdout
        assert before == after, "a parse error must stage nothing"

    def test_manifest_naming_a_missing_file_refuses_all_or_nothing(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        (repo / "backend").mkdir()
        (repo / "backend" / "a.py").write_text("# a\n")
        manifest = tmp_path / "manifest.json"
        manifest.write_text(json.dumps([
            {"file": "backend/a.py", "purpose": "real"},
            {"file": "backend/does_not_exist.py", "purpose": "missing"},
        ]))

        before = _git(["diff", "--cached", "--name-only"], repo).stdout
        result = _claim(repo, "add", "TASK-9001", "--from-file", str(manifest))
        assert result.returncode != 0
        after = _git(["diff", "--cached", "--name-only"], repo).stdout
        assert before == after, "one missing path must block the whole batch, not stage the rest"

    def test_manifest_entry_with_no_purpose_and_no_shared_purpose_refuses(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        (repo / "backend").mkdir()
        (repo / "backend" / "a.py").write_text("# a\n")
        manifest = tmp_path / "manifest.json"
        manifest.write_text(json.dumps({"files": ["backend/a.py"]}))  # no top-level purpose

        result = _claim(repo, "add", "TASK-9001", "--from-file", str(manifest))
        assert result.returncode != 0
        assert "no purpose" in result.stderr

    def test_from_file_and_positional_path_are_mutually_exclusive(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        manifest = tmp_path / "manifest.json"
        manifest.write_text(json.dumps([{"file": "x", "purpose": "y"}]))
        result = _claim(repo, "add", "TASK-9001", "some/path.py", "--from-file", str(manifest))
        assert result.returncode != 0
        assert "mutually exclusive" in result.stderr

    def test_single_file_form_requires_purpose(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        (repo / "backend").mkdir()
        (repo / "backend" / "a.py").write_text("# a\n")
        result = _claim(repo, "add", "TASK-9001", "backend/a.py")  # no --purpose
        assert result.returncode != 0
        assert "requires both PATH and --purpose" in result.stderr

    def test_path_outside_repository_refuses(self, tmp_path):
        repo = _make_scratch_repo(tmp_path)
        result = _claim(repo, "add", "TASK-9001", "../../etc/passwd", "--purpose", "x")
        assert result.returncode != 0
        assert "outside the repository" in result.stderr

    def test_unchanged_file_identical_to_head_refuses_with_a_clear_message(self, tmp_path):
        """Not gitignored -- genuinely nothing to stage. The error message
        must not claim gitignoring as the only explanation."""
        repo = _make_scratch_repo(tmp_path)
        result = _claim(repo, "add", "TASK-9001", ".ai/tasks/TODO/TASK-9001-scratch.md", "--purpose", "no-op")
        assert result.returncode != 0
        assert "already identical to HEAD" in result.stderr

    def test_stage_and_commit_guard_unaffected_by_add(self, tmp_path):
        """Planned Validation #5: `add` must not change `stage`/
        `commit-guard`'s own behavior at all."""
        repo = _make_scratch_repo(tmp_path)
        (repo / "backend").mkdir()
        (repo / "backend" / "a.py").write_text("# a\n")
        added = _claim(repo, "add", "TASK-9001", "backend/a.py", "--purpose", "x")
        assert added.returncode == 0, added.stderr

        # stage still refuses unclaimed GIT-COMMIT, exactly as TASK-0154 built it
        (repo / ".ai" / "COMMON.md").write_text("# edited\n")
        unclaimed = _claim(repo, "stage", "--expect", ".ai/COMMON.md")
        assert unclaimed.returncode == 1
        assert "not currently claimed" in unclaimed.stderr

        # commit-guard still asserts an exact match, unaffected by add's
        # own earlier staging of backend/a.py and the task file
        guard = _claim(
            repo, "commit-guard", "--expect",
            "backend/a.py", ".ai/tasks/TODO/TASK-9001-scratch.md",
        )
        assert guard.returncode == 0, guard.stderr


class TestGitExecutionErrorDetection:
    """TASK-0375, second occurrence: `_perform_transition`'s `tracked`/
    `final_tracked` checks and `_is_tracked` all read a git subprocess's
    `returncode == 0` alone to answer a yes/no question -- so when git
    itself fails to run at all (this machine's xcrun/CLT breakage, exit 1
    or 128 just like a legitimate negative answer), the failure was
    silently indistinguishable from "no" and `move` reported success while
    its own `git mv` silently never ran. `_run_git_bool_check` is the fix:
    only trust a nonzero exit as a real negative if stderr actually looks
    like git ran and answered.

    Mocked, not scratch-repo-based (unlike every other class in this file)
    -- deliberately: reproducing a genuine git-execution failure needs
    breaking git itself, which isn't something a test should do to the
    environment it runs in. Imports the real `claim.py` directly (no
    scratch copy needed -- `subprocess.run` is mocked out, no actual git
    repo state is touched), same "unit test on an internal is more direct
    than the CLI" precedent `_assert_single_tracked_path`'s own tests use
    elsewhere in this file."""

    @staticmethod
    def _import_claim():
        import importlib
        sys.path.insert(0, str(_HERE))
        import claim as claim_module
        importlib.reload(claim_module)  # pick up this session's file, not a stale cached import
        return claim_module

    def test_returncode_zero_is_true(self, monkeypatch):
        claim = self._import_claim()
        monkeypatch.setattr(claim.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
            args=a, returncode=0, stdout="", stderr=""))
        assert claim._run_git_bool_check(["git", "ls-files", "--error-unmatch", "x"], "did not match any file") is True

    def test_expected_negative_message_is_false(self, monkeypatch):
        claim = self._import_claim()
        monkeypatch.setattr(claim.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
            args=a, returncode=1, stdout="",
            stderr="error: pathspec 'x' did not match any file(s) known to git"))
        assert claim._run_git_bool_check(["git", "ls-files", "--error-unmatch", "x"], "did not match any file") is False

    def test_unexpected_stderr_raises_git_execution_error_not_false(self, monkeypatch):
        """The exact TASK-0375 shape: xcrun's error text, not git's own
        negative-answer text. Must raise, never silently become False."""
        claim = self._import_claim()
        monkeypatch.setattr(claim.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
            args=a, returncode=1, stdout="",
            stderr="xcrun: error: unable to load libxcrun (need x86_64)"))
        with pytest.raises(claim.GitExecutionError, match="xcrun"):
            claim._run_git_bool_check(["git", "ls-files", "--error-unmatch", "x"], "did not match any file")

    def test_is_tracked_raises_on_git_execution_failure(self, monkeypatch):
        claim = self._import_claim()
        monkeypatch.setattr(claim.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
            args=a, returncode=1, stdout="", stderr="xcrun: error: unable to load libxcrun"))
        with pytest.raises(claim.GitExecutionError):
            claim._is_tracked("some/path.md")

    def test_is_tracked_legitimate_negative_still_returns_false(self, monkeypatch):
        claim = self._import_claim()
        monkeypatch.setattr(claim.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
            args=a, returncode=128, stdout="",
            stderr="fatal: path 'some/path.md' does not exist in 'HEAD'"))
        assert claim._is_tracked("some/path.md") is False


class TestGitArchFallback:
    """TASK-0375, third occurrence (2026-09-15): a CLT reinstall fixed
    *direct* shell git calls but left this machine's real bug unchanged --
    a `git` subprocess spawned via Python's `subprocess` module resolves
    the universal binary's x86_64 slice regardless of the parent's own
    architecture (confirmed live: `subprocess.run(["arch"])` reports
    `i386` from inside this exact python; the same command typed in a
    shell reports `arm64`), and that slice's `xcrun` has no x86_64
    support on this Apple-Silicon-only CLT install. `_git` is the fix:
    retry once under `arch -arm64` when the first attempt fails with
    exactly that signature. Mocked, same reasoning as
    `TestGitExecutionErrorDetection` above -- reproducing this for real
    means breaking git itself."""

    @staticmethod
    def _import_claim():
        import importlib
        sys.path.insert(0, str(_HERE))
        import claim as claim_module
        importlib.reload(claim_module)
        return claim_module

    def test_success_on_first_try_does_not_retry(self, monkeypatch):
        claim = self._import_claim()
        calls = []

        def fake_run(args, **kwargs):
            calls.append(args)
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="ok\n", stderr="")

        monkeypatch.setattr(claim.subprocess, "run", fake_run)
        proc = claim._git(["status"], capture_output=True)
        assert proc.returncode == 0 and proc.stdout == "ok\n"
        assert len(calls) == 1, "a healthy first attempt must not trigger a second git process"
        assert calls[0] == ["git", "status"]

    def test_xcrun_failure_retries_once_under_arch_arm64(self, monkeypatch):
        claim = self._import_claim()
        calls = []

        def fake_run(args, **kwargs):
            calls.append(args)
            if args[0] == "git":
                return subprocess.CompletedProcess(
                    args=args, returncode=1, stdout="",
                    stderr="xcrun: error: unable to load libxcrun (need x86_64)")
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="fixed\n", stderr="")

        monkeypatch.setattr(claim.subprocess, "run", fake_run)
        proc = claim._git(["rev-parse", "HEAD"], capture_output=True)
        assert proc.returncode == 0 and proc.stdout == "fixed\n"
        assert calls == [["git", "rev-parse", "HEAD"], ["arch", "-arm64", "git", "rev-parse", "HEAD"]]

    def test_unrelated_failure_does_not_retry(self, monkeypatch):
        """A real git error (not this machine's specific bug) must not
        trigger the arm64 retry -- that would just mask a genuine failure
        behind an extra, pointless process spawn."""
        claim = self._import_claim()
        calls = []

        def fake_run(args, **kwargs):
            calls.append(args)
            return subprocess.CompletedProcess(
                args=args, returncode=128, stdout="", stderr="fatal: not a git repository")

        monkeypatch.setattr(claim.subprocess, "run", fake_run)
        proc = claim._git(["status"], capture_output=True)
        assert proc.returncode == 128
        assert len(calls) == 1

    def test_check_true_raises_after_the_retry_also_fails(self, monkeypatch):
        claim = self._import_claim()
        monkeypatch.setattr(claim.subprocess, "run", lambda args, **k: subprocess.CompletedProcess(
            args=args, returncode=1, stdout="",
            stderr="xcrun: error: unable to load libxcrun (need x86_64)"))
        with pytest.raises(claim.subprocess.CalledProcessError):
            claim._git(["status"], check=True, capture_output=True)

    def test_capture_output_false_writes_through_to_real_streams(self, monkeypatch, capsys):
        """The internal diagnostic run always captures (needed to inspect
        stderr for the retry decision) -- a caller that asked for live
        output must still see it, just replayed rather than streamed."""
        claim = self._import_claim()
        monkeypatch.setattr(claim.subprocess, "run", lambda args, **k: subprocess.CompletedProcess(
            args=args, returncode=0, stdout="hello stdout\n", stderr="hello stderr\n"))
        proc = claim._git(["commit"])
        captured = capsys.readouterr()
        assert "hello stdout" in captured.out
        assert "hello stderr" in captured.err
        assert proc.stdout is None, "capture_output=False must match subprocess.run's own shape"

    def test_input_is_passed_through(self, monkeypatch):
        claim = self._import_claim()
        received = {}

        def fake_run(args, **kwargs):
            received.update(kwargs)
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        monkeypatch.setattr(claim.subprocess, "run", fake_run)
        claim._git(["hash-object", "-w", "--stdin"], capture_output=True, input="some content")
        assert received.get("input") == "some content"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
