# TASK-0024 Whitelisted claim/free tool for scaffold coordination files

## Context

- ID: TASK-0024
- Title: Replace (or backstop) TASK-0017's soft, prose-table claim
  convention with a small, whitelisted CLI tool that atomically claims and
  releases work items, after that convention was observed to fail under
  real concurrent load within the same session it was introduced
- Status: Done
- Owner: Toolsmith
- Claimed By: Toolsmith (this thread)
- Claimed At: 2026-07-04 16:48
- Handoff note: originally claimed by Intent-Inferrer (this thread) at
  2026-07-04 15:20 (the thread that filed the task after hitting the
  incident). User directed this Toolsmith thread to pick it up directly;
  reclaimed via `claim.py claim TASK-0024 "Toolsmith (this thread)" --force
  --reason "direct human handoff this session"` — the tool's own
  `--force`/`--reason` override path, exercised for real as part of
  building it.
- Source: direct incident, this session, 2026-07-04 ~15:10 — while
  registering TASK-0020–0023, `.ai/COMMON.md`'s Active Work Registry was
  found reverted to a pre-TASK-0017 snapshot: the `Claimed By`/`Claimed At`
  columns, the claim-before-start/staleness rules, and every row from
  TASK-0003 through TASK-0019 were gone, even though all of those task
  files still exist on disk. This is not hypothetical risk — it is the
  exact failure TASK-0017 was written to prevent, happening again within
  hours of TASK-0017 shipping, almost certainly because a whole-file
  `Write` from a thread holding a stale in-memory copy clobbered another
  thread's incremental edits (prose-table edits have no atomicity; two
  concurrent whole-file writes are a last-writer-wins race).
- Crit Ref: directly supersedes/hardens TASK-0017
  (`.ai/tasks/DONE/TASK-0017-registry-claim-lock.md`), which explicitly
  scoped out real enforcement: *"any actual lock enforcement (file
  permissions, a lock server, CI gating) — this is explicitly a soft,
  convention-level lock... deferred until threads reliably commit
  small claim-only commits unattended... by then the challenge will be
  either over or half-done."* That deferral was a reasonable bet against
  a hypothetical failure mode; this task exists because the failure mode
  already happened, which changes the cost-benefit TASK-0017 was weighing.
- Scope: a new small script/CLI (exact location TBD — see Open Questions,
  candidate `.ai/scripts/claim.py`), plus its entry in
  `.claude/settings.json`'s tool allowlist (per the repo's existing
  `update-config` pattern for reducing permission-prompt friction on
  frequent, low-risk, mechanical operations)

## Intent Contract

- Outcome: claiming or releasing a task row is a single, atomic,
  whitelisted command any thread can run without a permission prompt and
  without hand-editing a shared prose table — removing both the race
  (concurrent whole-file writes) and the friction (manual table editing)
  that made the soft convention easy to violate by accident, not malice.
- In Scope:
  - design decision: per-task lock files (e.g.
    `.ai/tasks/.locks/TASK-0020.lock` containing claimant + timestamp) as
    the atomic source of truth, with `.ai/COMMON.md`'s registry table
    regenerated/derived from the lock files (script-writable, not
    hand-edited) — this isolates each claim's blast radius to one small
    file instead of one shared 80+ line table, which is what turned a
    normal race into a multi-task data-loss incident.
  - `claim(task_id, claimant)` — atomic create (fail if lock exists and
    is not stale; `O_EXCL`-style create, not read-modify-write).
  - `release(task_id)` — remove the lock; idempotent if already released.
  - `status([task_id])` — read current claims, single task or all.
  - staleness check ported from TASK-0017's rule (no corresponding file
    activity for longer than one working session) as a `--force` override
    path, keeping the "advisory override, human/agent judgment call"
    philosophy TASK-0017 established — this task hardens the mechanism,
    not the philosophy.
  - a regeneration step: `.ai/COMMON.md`'s Active Work Registry table
    becomes either (a) generated from lock files + task-file frontmatter
    by the tool, or (b) still hand-maintained but the claim
    columns specifically are tool-derived — decide which, don't leave it
    ambiguous (ambiguity here is exactly how this incident happened).
  - add the tool to `.claude/settings.json`'s allowlist so agents can call
    it without a per-invocation permission prompt (it's mechanical and
    low-risk by design — same rationale as the `fewer-permission-prompts`
    skill's general approach).
- Out Of Scope:
  - a distributed lock server, CI gating, or anything requiring
    infrastructure beyond a script + local files — matches TASK-0017's
    original scope ceiling, just moves the enforcement from "convention"
    to "atomic local file op," not all the way to heavyweight tooling.
  - claim-as-commit (still deferred per TASK-0017's original reasoning —
    unattended commits are a separate, bigger trust step).
  - retrofitting every other prose-table convention in the scaffold (task
    ledger boundary, etc.) — scope this to the claim/registry mechanism
    only; widen later only if the same failure mode recurs elsewhere.
- Constraints And Invariants:
  - must not require any new runtime dependency beyond Python stdlib
    (this is a coordination tool for a challenge-deadline project — keep
    it trivially runnable, no install step).
  - must keep `.ai/COMMON.md` human-readable — even if the registry table
    becomes tool-generated, it stays a plain markdown table in that file,
    not moved to a database or hidden format.
  - per TASK-0017's own "keep the registry single-file and grep-able"
    constraint: per-task lock files are a new small directory
    (`.ai/tasks/.locks/`), not a replacement for COMMON.md's role as the
    single human-readable index — the lock files back the mechanism, the
    table stays the reader-facing view.
- Planned Validation: simulate the exact incident — two concurrent
  processes each claim/release different task rows in a tight loop; confirm
  no claim is lost and `.ai/COMMON.md`'s regenerated table matches the lock
  files' state after both finish (this is the regression test for the
  actual failure that motivated this task).

## In Progress

None

## TODO

- [x] Decide the lock-file location and format (see Open Questions).
- [x] Implement `claim` / `release` / `status` as a small CLI.
- [x] Implement the registry-regeneration step (from lock files +
      `.ai/tasks/TODO|IN_PROGRESS|DONE/*.md` frontmatter into the
      `.ai/COMMON.md` table).
- [x] Add the tool to `.claude/settings.json`'s allowlist (use the
      `update-config` pattern already available in this environment).
- [x] Concurrency test per Planned Validation.
- [x] Update `.ai/tasks/README.md` and TASK-0017's own Done section with a
      pointer forward to this task, so a future reader following TASK-0017
      doesn't stop at "soft lock, by design" without finding out it was
      hardened here.
- [x] Re-verify `.ai/COMMON.md`'s registry (restored in this same session,
      see TASK-0020's sibling row additions) matches disk state for
      TASK-0001 through TASK-0024 once the tool exists, as the first real
      exercise of the new mechanism.

## Dependency

- TASK-0017 (done) — this task hardens/extends it; read its Done section
  first so the two don't contradict.
- Informs (but does not block) every other TODO task in this registry —
  all of them are exposed to the same race until this lands.

## Open Questions

- Resolved: lock file location is `.ai/tasks/.locks/<TASK-ID>.lock`
  (per-file, JSON), gitignored — see `.ai/tasks/.locks/README.md`.
- Resolved: registry regeneration is **tool-assisted, not fully
  auto-generated** — option (b) from the original list. `claim.py sync`
  is the *only* writer of the `Claimed By` / `Claimed At` cells (regenerated
  from lock files, targeted per-row line replacement, not a whole-file
  rewrite); every other column (Description/Assigned To/Status/Priority/
  Last Active/Path) stays hand-maintained exactly as before. Full
  auto-generation was rejected because task files don't carry structured
  Priority/Last Active/Description frontmatter (confirmed by inspection —
  only Description-equivalent prose lives in free-text `Title`), and
  retrofitting that onto every existing task file was explicitly out of
  scope. `sync` does cross-check row-vs-disk presence and warns (stderr)
  on mismatches without touching rows it doesn't own, as a lightweight
  detector for the "whole rows went missing" failure mode.
- Resolved: no change to the `.claude/TASKS.md` closed-ledger boundary.

## Done

- Built `.ai/tools/claim.py` (Python stdlib only, no dependency) with four
  subcommands: `claim` (atomic `O_EXCL` lock create; `--force --reason
  TEXT` to override an existing claim, with the prior holder and reason
  recorded in the lock file for audit), `release` (idempotent; `--claimant`
  optionally checked, `--strict` to fail instead of warn on mismatch),
  `status` (single task or full listing; flags dangling locks with no
  matching task file), and `sync` (regenerates only the `Claimed By` /
  `Claimed At` cells of `.ai/COMMON.md`'s registry table from lock files;
  `--dry-run` and `--check` supported; concurrent `sync` writers are
  serialized through a short-lived `.ai/COMMON.md.synclock` file).
- Task IDs accept both plain (`TASK-0024`, `24`) and the dotted-subtask
  form introduced concurrently this same session in
  `.ai/tasks/README.md` (`TASK-0026.001`, `26.1`) — this had to be handled
  live: `.ai/tools/claim.py`'s first ID-parsing draft only matched plain
  IDs, and a concurrent thread (Skills Crafter) introduced the dotted
  convention and TASK-0026's subtasks in `.ai/COMMON.md` while this task
  was being built, so the parser and the table-row regex were both fixed
  to handle `TASK-XXXX.NNN` before this landed.
- Planned Validation, exercised directly: (1) two workers claiming/
  releasing 30 iterations each on two *different* scratch rows concurrently
  — 0 lost claims; (2) two workers hammering **the same** scratch row 50
  iterations each (real mutual-exclusion contention, not just disjoint
  rows) — 52/100 total wins split across both, 0 double-claims, lock file
  never left in a torn/corrupt state; (3) two concurrent `sync` runs against
  the live `.ai/COMMON.md` (with real rows, not scratch ones) after
  importing every pre-existing hand-written claim into lock files first —
  both produced byte-identical output. All scratch artifacts
  (`TASK-9001`-`TASK-9004` locks, a COMMON.md test mutation) were reverted
  via `git checkout` before real use.
- Near-miss caught during Planned Validation, worth recording: running
  `sync` *before* importing the pre-existing hand-written claims (TASK-0017,
  0019–0025) into lock files wiped those real claims from the table back to
  `—`/`—`, because the tool correctly treats lock files as the sole source
  of truth for those two columns and none existed yet for that
  already-claimed work. This is a one-time migration hazard, not a design
  flaw — the fix was importing every existing hand-written claim as a real
  lock file (preserving original claimant/timestamp) before the first real
  `sync`. Anyone adopting this tool on a registry that already has
  hand-written claims must do the same one-time import first.
- Added capability rows (`workflow.task.claim`, `workflow.task.release`,
  `workflow.task.claim-status`, `workflow.registry.sync`) to
  `.ai/reference/CAPABILITIES.md`.
- Added a `Bash(python3 .ai/tools/claim.py *)` allow entry to
  `.claude/settings.json` via the `update-config` skill.
- Rewrote the three TASK-0017-authored rules in `.ai/COMMON.md`'s "Current
  Rules" (claim-before-start, staleness override, "unsafe under concurrent
  whole-file writes") to point at `claim.py` instead of hand-editing the
  `Claimed By`/`Claimed At` cells; added a Quick Navigation line pointing at
  the tool.
- Ran `claim.py sync` for real against `.ai/COMMON.md` after the import
  step above; the only actual content change was this task's own row
  (`Intent-Inferrer (this thread)` → `Toolsmith (this thread)`, reflecting
  the `--force` handoff), confirming the mechanism doesn't disturb rows it
  doesn't own even while another thread was concurrently adding TASK-0025
  and TASK-0026(.001-.004) rows to the same file.
- Added `.ai/tasks/.locks/*.lock` to `.gitignore` (ephemeral coordination
  state, not reviewed history) plus `.ai/tasks/.locks/README.md` explaining
  the mechanism for anyone who lands in that directory.
- Added a pointer-forward note to TASK-0017's Done section (see that file)
  and confirmed `.ai/tasks/README.md`'s required-sections note doesn't need
  a change beyond what the concurrent dotted-subtask edit already added.
- Validation performed: re-ran `claim.py sync --dry-run` after all edits —
  reports "no claim-column changes needed", confirming `.ai/COMMON.md`
  matches lock-file state for every row TASK-0001 through TASK-0026.004.
