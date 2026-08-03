# TASK-0197 `claim.py stage` cannot stage deletions — forces an un-whitelisted bare `git add`

## Context

- ID: TASK-0197
- Title: `stage --expect <path>` refuses outright when `<path>` doesn't
  exist on disk, even when that absence is a legitimate deletion of a
  previously-tracked `.ai/`/`.claude/` file — the only way to stage such a
  deletion today is a bare `git add`/`git rm`, which has no whitelist
  entry and always prompts.
- Status: Done
- Owner: Toolsmith (Architect implementing directly, same session)
- Claimed By: Architect
- Claimed At: 2026-08-03 16:05
- Source: orchestrating collaborator (Bartosz), 2026-08-03 — reported that
  cleaning up a duplicate `TASK-0189` file (tracked in both `TODO/` and
  `DONE/` after another thread's commit) required a raw `git add
  .ai/tasks/TODO/TASK-0189-....md` call, because "no whitelisted path
  allowed deletions."
- Priority: **P2.** Same class of friction as [[TASK-0042]]'s bare-
  `status`/`sync` fix and [[TASK-0196]]'s stale-preset-list fix, same
  session — a real, reproducible gap, not a hypothetical one (the
  `TASK-0189` cleanup is the live case).

## Why this matters

`cmd_stage` in `.ai/tools/claim.py` has, since TASK-0029, an explicit
guard: any `--expect` path that doesn't exist on disk is treated as an
error ("names paths that do not exist on disk"). That guard was written
to catch **typos** — a path that never existed, caught before `git add`
does something surprising. But it fires identically for a **legitimate
deletion** of a file that *was* tracked and has since been intentionally
removed (renamed away, or a duplicate cleaned up) — the exact case this
session hit directly. The tool cannot tell "you mistyped this path" from
"you correctly deleted this path" and currently treats both as the same
error, forcing a fallback to a bare `git add`/`git rm` that has no
`.claude/settings.json` whitelist entry (deliberately — TASK-0029's whole
point was that an unscoped `git add` wrapper would be a whitelist-bypass
in disguise) and therefore always prompts.

## Intent Contract

- Outcome: `stage --expect <path>` succeeds for a path that is absent from
  disk **if and only if** it is still tracked by git (a real deletion to
  stage) — still refuses, with the existing clear message, for a path
  that is absent from disk *and* never tracked (the actual typo case the
  guard was built for).
- Why required, not assumed: the two cases look identical from
  `os.path.exists()` alone; only `git ls-files` distinguishes them.

- In Scope:
  - New `_is_tracked(rel_path)` helper — `git ls-files --error-unmatch`,
    returncode-based, mirrors the existing tracked-check pattern already
    used in `_perform_transition` (don't invent a second way to ask git
    the same question).
  - `cmd_stage`'s missing-on-disk branch splits into two: paths absent
    *and* untracked → existing error, unchanged wording; paths absent
    *but* tracked → allowed through to the `git add --` call below
    (modern git stages a removal for a tracked-but-missing pathspec via
    plain `git add`, confirmed behavior since Git 2.0 — no `git rm`
    needed as a separate code path).
  - Still scoped to `.ai/`/`.claude/` only — this task does not touch
    `_in_scope`'s boundary, only the on-disk-existence assumption.

- Out Of Scope:
  - Any change to `commit-guard`'s own logic — it already compares
    against the staged index via `git diff --cached`, which correctly
    reflects a staged deletion with no change needed there.
  - Extending `stage` to accept out-of-scope (non-`.ai`/`.claude`)
    deletions — same boundary as TASK-0029, unchanged.
  - `move`/`resolve`'s own internal `git mv`/`git add` calls — those
    already handle the move correctly; this task is `stage` specifically.

- Constraints And Invariants:
  - No loosening of `_in_scope`'s path-traversal-safe boundary.
  - Stdlib + existing `subprocess` calls only, matching the tool's
    existing constraints.

- Planned Validation:
  - Real case, not synthetic: the live duplicate `TASK-0189` file
    (tracked in both `TODO/` and `DONE/`, working tree already missing
    the `TODO/` copy — confirmed via `git ls-tree -r HEAD` before this
    task was filed) — `stage --expect
    .ai/tasks/TODO/TASK-0189-....md` must now succeed and correctly stage
    the deletion, self-verified the same way `stage` already
    self-verifies additions.
  - A genuinely never-tracked, nonexistent path must still refuse with
    the existing error message — confirm the fix didn't silently loosen
    this into "anything missing is fine."
  - `commit-guard --expect` immediately after must see the staged
    deletion correctly (it already reads `git diff --cached --name-only`,
    which lists deletions too — confirm, don't assume).

## In Progress

- 2026-08-03 (Architect): implementing directly, filed same session --
  small, reproducible, real live test case already on disk.

## TODO

- [x] `_is_tracked()` helper.
- [x] Split `cmd_stage`'s missing-on-disk check into untracked (error) vs.
      tracked-but-absent (allow).
- [x] Validate against a real deletion — **the live `TASK-0189` duplicate
      resolved itself mid-task** (another thread amended/re-committed it
      between this task being filed and this step running — `HEAD` moved
      `ec8ee88` -> `6f55655`, confirmed via `git log`, and the duplicate
      is gone). Validated instead with a safe synthetic reproduction: a
      real tracked file (`.ai/tasks/.locks/README.md`) backed up, deleted
      from disk, staged via `stage --expect`, confirmed staged correctly,
      then unstaged and restored byte-for-byte (confirmed clean via
      `git status --short` afterward) — no lasting change from the test.
- [x] Confirm a genuine typo/never-tracked path still refuses.
- [x] Confirm `commit-guard --expect` sees the staged deletion correctly.

## Dependency

- [[TASK-0029]] (Done) — the `stage` tool this extends; do not fork a
  parallel staging path.
- [[TASK-0042]], [[TASK-0196]] — same-session precedent for this class of
  fix (identify the exact failing invocation, fix the narrowest thing).

## Open Questions

- None — scope is fully specified by the one real failing case.

## Done

**2026-08-03, Architect.** `_is_tracked(rel_path)` added (`git ls-files
--error-unmatch`, same primitive `_perform_transition` already uses).
`cmd_stage`'s missing-on-disk branch now splits: absent *and* untracked →
original error, unchanged wording; absent *but* tracked → allowed through
to `git add --`, which stages the removal directly (confirmed Git 2.0+
behavior, no separate `git rm` call needed).

**Live test case resolved itself mid-task**: the duplicate `TASK-0189`
file this task was filed against was fixed by another thread's own
commit while this task was in progress (`HEAD` moved from `ec8ee88` to
`6f55655` — confirmed via `git log`; `git ls-tree -r HEAD` no longer
shows the `TODO/` copy). Validated instead with a safe, reversible
synthetic reproduction on a real tracked file
(`.ai/tasks/.locks/README.md`): backed up, deleted from disk, staged the
deletion via `stage --expect` (succeeded, self-verified), confirmed
`commit-guard --expect` sees it correctly, then unstaged and restored the
file byte-for-byte — `git status --short` on that path showed no diff
afterward, confirming zero lasting effect from the test.

Negative case confirmed separately: `stage --expect
.ai/tasks/TODO/TASK-9999-never-existed.md` (a path that was never
tracked) still refuses with the original error message — the fix
narrows the guard, it does not remove it.

No change to `_in_scope`'s path-traversal boundary, no new dependency.
