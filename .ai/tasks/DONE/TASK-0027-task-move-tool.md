# TASK-0027 Whitelisted tool for moving TASK files between lifecycle states

## Context

- ID: TASK-0027
- Title: Encapsulate the TODO → IN_PROGRESS → DONE task-file move (file
  relocation + `Context: Status` field + `.ai/COMMON.md` registry
  `Status`/`Path` columns) into a single whitelisted command that checks
  `.ai/tools/claim.py`'s lock state first, instead of the current
  hand-rolled three-step sequence every thread performs manually
- Status: Done
- Owner: Toolsmith
- Claimed By: —
- Claimed At: —
- Source: direct request, this session, 2026-07-04 — while landing
  TASK-0024, this thread moved that task's own file `TODO/` →
  `IN_PROGRESS/` → `DONE/` by hand three separate times (a `mv`, a
  `Context: Status` edit, and a registry `Status`/`Path` edit, each as its
  own tool call, each a chance to update one and forget another). The user
  asked for this to become its own tool, and specifically to have it call
  `claim.py` to verify there's no competing claim before performing a
  move. Decided directly by the user: extend `claim.py` (don't build a
  standalone script), default a `DONE` move to auto-release the claim
  (with an opt-out), and always require an explicit claimant label.
- Scope: a new `move`/`transition` subcommand on the existing
  `.ai/tools/claim.py`, gated by a claim check, replacing the manual
  file-move + Status-edit + registry-edit sequence with one command.

## Intent Contract

- Outcome: moving a task file between `TODO/`/`IN_PROGRESS/`/`DONE/` is one
  whitelisted command that (a) refuses if another thread holds a live,
  non-stale claim on that task ID and the caller isn't that claimant, (b)
  otherwise performs the folder move, the file's own `Context: Status`
  line update, and `.ai/COMMON.md`'s registry `Status`/`Path` cell update
  for that row, together — removing the "moved the file but forgot the
  registry row" and "edited Status in the file but not the folder" classes
  of drift this scaffold's rules already warn about by convention alone.
- In Scope:
  - **Decided: a new subcommand on `.ai/tools/claim.py`** (e.g.
    `claim.py move TASK-0027 IN_PROGRESS --as "Toolsmith (this thread)"`),
    not a standalone script — the move operation's core precondition *is*
    a claim-status check, so it needs the same lock-reading code either
    way; reuse `claim.py`'s existing task-ID normalization (including
    dotted subtask IDs) and its lock-file read path directly, do not
    duplicate it.
  - **Decided: `--as <label>` is always required** (not conditional on
    whether the task is currently claimed) — every move needs an
    attributable actor for the refusal-on-mismatch check and for the audit
    trail, so there is no "unclaimed, therefore no label needed" shortcut.
  - claim check before moving: if a lock file exists for the task ID and
    its `claimant` doesn't match the required `--as <label>`, refuse with
    the same loud "claimed by X since Y" style `claim` already uses, with
    the same `--force --reason TEXT` override escape hatch — mirror
    TASK-0024's existing pattern rather than inventing a new one. If no
    lock exists at all, warn (don't block) and proceed — matches this
    scaffold's "advisory, not enforced" philosophy; claiming before every
    routine move is not itself mandated.
  - three effects performed together as one command, not three manual
    steps: (1) relocate the file (`git mv` if tracked, falling back to
    `mv` for not-yet-tracked files, mirroring what this thread did by hand
    for TASK-0024), (2) rewrite that file's `Context: Status:` line in
    place (targeted single-line replacement, not a whole-file rewrite —
    same discipline `sync` already uses for `COMMON.md`), (3) update
    `.ai/COMMON.md`'s registry row for that Task ID: `Status` and `Path`
    columns only, via the same targeted per-row replacement and
    `.synclock` serialization `sync` already implements — reuse that
    machinery rather than re-deriving it.
  - **Decided: moving to `DONE` auto-releases the claim by default**
    (`--keep-claim` to opt out) — this is what this thread did by hand for
    TASK-0024 (moved to `DONE/`, then released), and forgetting the manual
    release step is exactly the kind of drift this tool exists to prevent.
    Moves to `TODO`/`IN_PROGRESS` never auto-release.
  - idempotency: moving a task to the state it's already in (file already
    in that folder, `Status` already matching) is a safe no-op, not an
    error.
  - add the subcommand to `.claude/settings.json`'s allowlist (same
    `update-config` pattern TASK-0024 used).
- Out Of Scope:
  - moving `PLANS/` docs — those don't move through TODO/IN_PROGRESS/DONE
    per `.ai/tasks/README.md`.
  - writing the actual `Done` section content — that's the real work
    output, a human/agent judgment call, not mechanizable.
  - creating new task files (`workflow.task.create`, a separate
    capability) or dotted-subtask parent/child status rollup (e.g.
    auto-marking a parent Done when every subtask is Done) — flag as a
    possible future follow-on, don't build it speculatively here.
  - a distributed lock or CI gate — matches TASK-0024's own scope ceiling;
    this is still a local, advisory-backed atomic file op.
- Constraints And Invariants:
  - Python stdlib only, no new dependency (matches TASK-0024).
  - must not regress or duplicate `.ai/tools/claim.py`'s existing
    `claim`/`release`/`status`/`sync` behavior — reuse its lock-reading and
    `COMMON.md` row-parsing code paths directly.
  - keep `.ai/COMMON.md` a plain hand-readable markdown table — this only
    ever touches the `Status`/`Path` cells it owns, same discipline as
    `sync` touching only the claim cells.
- Planned Validation: mirror TASK-0024's own validation approach — (1) a
  move refuses when a mismatched claim lock is present, (2) a move
  proceeds with a warning when the task is unclaimed, (3) after a move the
  file's folder, its own `Context: Status` line, and the registry row's
  `Status`/`Path` cell all agree, (4) a `DONE` move releases the claim
  unless `--keep-claim` is passed, (5) two concurrent move attempts on the
  same task ID don't corrupt the file, the registry, or leave the task in
  two folders at once.

## In Progress

None

## TODO

- [x] Implement `claim.py move <TASK-ID> <TODO|IN_PROGRESS|DONE> --as
      <label>` per Intent Contract, reusing (not duplicating) `claim.py`'s
      task-ID normalization, lock reading, and `COMMON.md`
      row-parsing/`.synclock` serialization.
- [x] Add the claim-mismatch refusal + `--force --reason` override path,
      and the `DONE`-move auto-release (+ `--keep-claim`) behavior.
- [x] Add the subcommand to `.claude/settings.json`'s allowlist. — Already
      covered: the existing `Bash(.ai/tools/claim.py *)` / `Bash(python3
      .ai/tools/claim.py *)` wildcard entries match any subcommand/args,
      no new entry needed (same finding as TASK-0028).
- [x] Run Planned Validation, including the concurrent-move case.
- [x] Update `.ai/COMMON.md`'s "Current Rules" (the claim-before-start
      rule currently only mentions `claim`/`sync`) to point at this tool
      for state transitions, the same way TASK-0024 updated those rules
      for claiming. (`.ai/tasks/README.md` needed no change — it documents
      the folder/Status convention itself, not the mechanism that edits it.)
- [x] Add a forward pointer in `.ai/tasks/DONE/TASK-0024-claim-lock-tool.md`
      noting that task-state transitions now have their own subcommand,
      mirroring how TASK-0024 pointed forward from TASK-0017.

## Dependency

- [TASK-0024](../DONE/TASK-0024-claim-lock-tool.md) (Done) — this builds
  directly on its lock-file format and `COMMON.md` row-editing machinery;
  read its Done section (lock format, `sync`'s targeted-replacement
  approach, the migration hazard it documents) before implementing.
- Loosely related to
  [TASK-0024.001](TASK-0024.001-whole-file-resource-locks.md) (extends
  `claim.py` to whole-file resource locks) — both extend the same tool;
  not blocking each other, but implement with awareness of one another so
  the CLI surface doesn't grow inconsistent argument conventions between
  the two extensions.

## Open Questions

(none outstanding — the design questions raised while drafting this task
were resolved directly by the user; see the "Decided" notes in Context and
Intent Contract above.)

## Done

- Extended `.ai/tools/claim.py` (no new tool, no new dependency):
  - `find_task_file(task_id)`: scans TODO/IN_PROGRESS/DONE for the file,
    raising a clear error on zero matches (not found) or more than one
    (real on-disk drift) rather than silently picking one.
  - `update_registry_row(task_id, new_status, new_path)`: reuses the
    existing `_parse_row`/`_common_md_lock` from `sync` — touches only the
    `Status` (index 3) and `Path` (index 8) cells for that row, same
    targeted-replacement discipline as `sync`'s claim-column writes.
  - `cmd_move`: claim check (refuse on mismatch unless `--force --reason`,
    warn-and-proceed if unclaimed — same philosophy as `claim`) → locate
    the file → rewrite its `- Status:` line in place → `git mv` (falling
    back to `os.replace` if not yet tracked) → update the registry row →
    auto-release the claim on a `DONE` move unless `--keep-claim`.
    Idempotent: if the folder, Status line, and registry row all already
    match the target state, reports a no-op instead of doing anything.
  - `move` is restricted to `TASK-XXXX[.NNN]` ids (`is_task_id` check) —
    refuses on `GIT-COMMIT` or other special resources, since "moving" a
    non-task resource is meaningless.
- Planned Validation, all five cases exercised on a scratch task
  (`TASK-9500`, cleaned up afterward — file, lock, and registry row all
  removed): (1) unclaimed move proceeds with a warning; (2) a mismatched
  `--as` refuses, naming the actual claimant; (2b) a matching `--as` move
  to `DONE` succeeds, updates the registry row, and auto-releases the
  claim; (3) moving to the state it's already in reports a no-op; (4) two
  concurrent `move` calls on the same task to different target states —
  one succeeded, the other got a clear "may have already been moved by
  another thread" error (not a crash/traceback) via a caught
  `FileNotFoundError`/`CalledProcessError`, and the file ended up in
  exactly one folder with the registry row correctly matching it — no
  corruption, matching the concurrency-safety bar `find_task_file`'s
  atomic `os.replace`/`git mv` gives for free on same-filesystem renames.
- Confirmed no `.claude/settings.json` change was needed, same as
  TASK-0028's finding: the existing wildcard allow entries already cover
  `move` and any future subcommand on this tool.
- Updated `.ai/COMMON.md`: Quick Navigation line lists `move` alongside
  the other subcommands; added a new "Current Rules" bullet describing
  the convention (run `move` instead of hand `mv` + two edits).
- Registered `workflow.task.move` in `.ai/reference/CAPABILITIES.md`.
- Added a forward pointer in `.ai/tasks/DONE/TASK-0024-claim-lock-tool.md`
  covering both this task and TASK-0028 together, since both extend the
  same tool and landed in the same session.
- Dogfooded on itself: this file's own TODO/IN_PROGRESS → DONE transition
  (this move) was performed via `claim.py move TASK-0027 DONE --as
  "Toolsmith (this thread)"` rather than by hand, as the first real
  (non-scratch) exercise of the tool.
