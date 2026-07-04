# TASK-0027 Whitelisted tool for moving TASK files between lifecycle states

## Context

- ID: TASK-0027
- Title: Encapsulate the TODO → IN_PROGRESS → DONE task-file move (file
  relocation + `Context: Status` field + `.ai/COMMON.md` registry
  `Status`/`Path` columns) into a single whitelisted command that checks
  `.ai/tools/claim.py`'s lock state first, instead of the current
  hand-rolled three-step sequence every thread performs manually
- Status: TODO
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

- [ ] Implement `claim.py move <TASK-ID> <TODO|IN_PROGRESS|DONE> --as
      <label>` per Intent Contract, reusing (not duplicating) `claim.py`'s
      task-ID normalization, lock reading, and `COMMON.md`
      row-parsing/`.synclock` serialization.
- [ ] Add the claim-mismatch refusal + `--force --reason` override path,
      and the `DONE`-move auto-release (+ `--keep-claim`) behavior.
- [ ] Add the subcommand to `.claude/settings.json`'s allowlist.
- [ ] Run Planned Validation, including the concurrent-move case.
- [ ] Update `.ai/COMMON.md`'s "Current Rules" (the claim-before-start
      rule currently only mentions `claim`/`sync`) and
      `.ai/tasks/README.md` to point at this tool for state transitions,
      the same way TASK-0024 updated those rules for claiming.
- [ ] Add a forward pointer in `.ai/tasks/DONE/TASK-0024-claim-lock-tool.md`
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

(not yet)
