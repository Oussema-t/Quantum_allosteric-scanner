# TASK-0017 Soft-lock claim column on the Active Work Registry

## Context

- ID: TASK-0017
- Title: Add a `Claimed By` / `Claimed At` soft-lock convention to
  `.ai/COMMON.md`'s Active Work Registry, to prevent the concurrent-edit
  collision this task exists to fix
- Status: Done
- Owner: Implementer (picked up 2026-07-04, redirected from the original
  General Critic/hygiene-pass placeholder owner — a bounded schema+doc
  change fits the Implementer brief directly)
- Claimed By: Implementer (this thread)
- Claimed At: 2026-07-04 14:30
- Source: user request, 2026-07-04 session, following a real near-miss:
  two threads (this session and a parallel Implementer/Critic thread)
  both edited `.ai/COMMON.md` and `TASK-0002`/`TASK-0007` concurrently
  in the same working period. It worked out — the edit tool's
  read-before-write staleness check forced a re-read-and-merge instead of
  a silent clobber, and the parallel thread's TASK-0002 pass caught and
  reconciled most of the drift — but that was a tooling coincidence, not a
  mechanism. Discussed three options (registry claim column, dedicated
  lock file, claim-as-commit); user picked the registry-column option as
  the pragmatic default, explicitly deferring claim-as-commit until
  threads are stable/supervised enough to commit unattended — "by then the
  challenge will be either over or half-done."
- Scope: `.ai/COMMON.md` (schema + rule), `.ai/tasks/README.md` (task-file
  convention), `.ai/reference/STARTER_TASK_EXAMPLE.md` (template)

## Intent Contract

- Outcome: before any thread starts or resumes work on a `TASK-XXXX` file
  or edits `.ai/COMMON.md`'s registry itself, it can answer "is someone
  already on this" by reading one table — and claiming a row is a single,
  cheap, visible edit, not a new file format to keep in sync with two
  others.
- In Scope:
  - extend the Active Work Registry table in `.ai/COMMON.md` with two
    columns: `Claimed By` (thread/session label — free text, e.g.
    "Implementer-session-A", "General Critic hygiene pass") and
    `Claimed At` (timestamp, `YYYY-MM-DD HH:MM` local/session time is
    fine — this is advisory, not a distributed clock).
  - a rule in `.ai/COMMON.md`'s "Current Rules" (alongside the existing
    "whoever creates or moves a TASK-XXXX file must update this registry
    in the same edit" rule from TASK-0002): **before starting or resuming
    work on a row, write your claim into that row first, in its own edit,
    before making substantive changes to the task file or its dependents.
    If the row already shows another claim, do not proceed silently** —
    either pick a different unclaimed task, or if the claim looks stale
    (see staleness rule below), note the override in that task file's Open
    Questions and proceed.
  - a staleness rule: a claim with no corresponding file activity (check
    the task file's own mtime / git log) for longer than one working
    session is stale and may be taken over. Don't build a numeric TTL
    enforcement — this is advisory, a human/agent reading the table makes
    the call, same as everything else in this scaffold.
  - update `.ai/tasks/README.md`'s "Required sections" note and
    `.ai/reference/STARTER_TASK_EXAMPLE.md` so new task files' `Context`
    section includes an optional `Claimed By` / `Claimed At` line mirroring
    the registry (belt-and-suspenders: the registry is the fast single-file
    check, the task file's own Context is the detail if the registry
    entry is ambiguous or missing).
- Out Of Scope:
  - any actual lock enforcement (file permissions, a lock server, CI
    gating) — this is explicitly a *soft*, convention-level lock. Nothing
    stops a thread from ignoring it; the point is making the "is this
    claimed" question fast and visible, not unbreakable.
  - claim-as-commit (option #3 from the discussion) — deferred until
    threads reliably commit small claim-only commits unattended. Revisit
    only if unattended/overnight multi-thread runs become common; not
    needed for the current supervised-session workflow.
- Constraints And Invariants:
  - keep the registry table single-file and grep-able — do not split
    claims into a separate `.ai/tasks/LOCKS.md` or per-task lock file; that
    was explicitly considered and rejected (more surface area to drift,
    the exact failure mode this task fixes).
  - this convention itself must be exercised, not just documented: the
    next few task-file claims/moves in this scaffold should actually use
    it, so it's validated against real concurrent work rather than sitting
    unused.
- Planned Validation: manually claim a row, confirm a second read of
  `.ai/COMMON.md` alone (no other file) is enough to tell a fresh thread
  whether to proceed; dry-run the staleness override path on TASK-0001
  (long-running, last active 2026-06-25 — a real example of a claim that
  would look stale under this rule) without actually taking it over.

## TODO

- [x] Add `Claimed By` / `Claimed At` columns to `.ai/COMMON.md`'s Active
      Work Registry table; backfill existing rows with either a real claim
      (if a thread is actually on it) or a blank/dash (unclaimed).
- [x] Add the claim-before-start rule to "Current Rules" in `.ai/COMMON.md`.
- [x] Add the staleness-override rule (advisory, human/agent judgment call,
      no numeric enforcement) next to it.
- [x] Update `.ai/tasks/README.md` to mention the optional `Claimed By`/
      `Claimed At` Context line.
- [x] Update `.ai/reference/STARTER_TASK_EXAMPLE.md`'s template accordingly.
- [x] Note in this file's Done section which existing rows (if any) got a
      real claim during rollout, as a first exercised example for future
      threads to copy.

## Dependency

- TASK-0002 (done) — this task extends the registry-sync rule TASK-0002
  already added; read that task's Done section before editing
  `.ai/COMMON.md` again so the two don't contradict each other.

## Open Questions

- Free-text `Claimed By` (thread/session label) vs. something more
  structured (session ID, timestamp format)? Recommend staying free-text —
  this is a manual-first scaffold per its own adoption guide, and a rigid
  format is exactly the kind of premature structure that tends to rot
  first.
- Resolved: `.ai/COMMON.md` itself does not get a row in its own registry
  (the registry lists `TASK-XXXX` work items, not files) — instead the
  claim-before-start rule text explicitly calls out COMMON.md as "the
  single most contended file in the scaffold" and folds it under the same
  rule rather than adding a special-cased row. See `.ai/COMMON.md` →
  "Current Rules".

## Done

- Added `Claimed By` / `Claimed At` columns to `.ai/COMMON.md`'s Active
  Work Registry. Backfilled: all existing rows got `—`/`—` (no thread was
  actually active on them at edit time) except this row (TASK-0017), which
  got a real claim — `Implementer (this thread)` / `2026-07-04 14:30` — as
  the first exercised example the task asked for. Also reassigned
  TASK-0017's `Assigned To` column from its original `General Critic`
  placeholder to `Implementer`, matching who actually picked it up (see
  Context → Owner above), and updated its `Status`/`Path` columns to track
  the TODO → IN_PROGRESS move made in this same pass.
- Added the claim-before-start rule and the staleness-override rule to
  `.ai/COMMON.md`'s "Current Rules", both scoped as advisory/no-enforcement
  per this task's Out Of Scope. The claim-before-start rule text explicitly
  names `.ai/COMMON.md` as the most-contended file, closing the second
  Open Question without a separate row hack.
- Dry-ran the staleness override on TASK-0001 per Planned Validation:
  Last Active 2026-06-25, no row claim, well past one working session —
  it reads as stale under the new rule and would be a legitimate takeover
  candidate. Documented the dry-run inline in the rule text as a
  worked example; did **not** take the row over (out of this task's scope
  and not this thread's work).
- Updated `.ai/tasks/README.md`'s "Required sections" note and
  `.ai/reference/STARTER_TASK_EXAMPLE.md`'s example `Context` block to
  show the optional `Claimed By` / `Claimed At` lines mirroring the
  registry columns.
- Validation performed: re-read `.ai/COMMON.md` alone after the edits —
  the registry table alone answers "is TASK-0017 claimed, by whom, since
  when" without opening this file, satisfying the Planned Validation
  check. Moved this file `TODO/` → `IN_PROGRESS/` → `DONE/` as part of
  finishing the pass, updating the registry's `Status`/`Path` at each
  move per the existing registry-sync rule (TASK-0002).

- **Forward pointer (2026-07-04, added by TASK-0024):** this task's
  hand-edited `Claimed By` / `Claimed At` convention was clobbered twice by
  concurrent whole-file writes within hours of shipping — the exact
  failure mode this task's Out Of Scope section called "hypothetical."
  `.ai/tasks/DONE/TASK-0024-claim-lock-tool.md` replaced the mechanism (not
  the philosophy) with `.ai/tools/claim.py`: an atomic per-task lock file
  under `.ai/tasks/.locks/`, with `claim.py sync` as the sole writer of
  this registry's two claim columns. **Do not hand-edit `Claimed By` /
  `Claimed At` anymore** — see `.ai/COMMON.md`'s "Current Rules" and
  TASK-0024 for the current mechanism. Everything else this task
  established (advisory staleness override, human/agent judgment call, no
  distributed lock) is unchanged.
