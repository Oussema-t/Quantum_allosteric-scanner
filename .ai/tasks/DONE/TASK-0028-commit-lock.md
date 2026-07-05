# TASK-0028 Commit lock — serialize the stage-and-ship critical section

## Context

- ID: TASK-0028
- Title: A whitelisted commit lock (`claim.py`-backed) that serializes the
  `git add` → `git commit` critical section across threads, plus an
  index-hygiene guard that refuses to commit if the staged index contains
  paths the committing thread didn't explicitly declare
- Status: Done
- Owner: Toolsmith
- Claimed By: Toolsmith (this thread)
- Claimed At: 2026-07-05 08:38
- Decisions (user, 2026-07-05): implement now, do not wait on TASK-0024.001
  landing first; use the suggested syntax as-is (`GIT-COMMIT` resource id,
  `commit-guard` subcommand name, `--hitl-override` flag name); one global
  lock (no per-directory scoping).
- Source: direct incident, this session, 2026-07-04 — while committing
  TASK-0025's evidence update, this thread ran a full unscoped freshness
  check before *staging* but only a path-scoped check before *committing*,
  and `git commit` (no path restriction) commits the entire staged index,
  not just the path just `git add`-ed. Another thread had already staged
  four unrelated files (a new task file + three `__WORK_IN_PROGRESS__`
  docs + a `COMMON.md` tweak) earlier and hadn't committed yet; they rode
  along into this thread's commit under an unrelated message. Not
  destructive (nothing lost, just misattributed), but exactly the kind of
  incident TASK-0017/TASK-0024 already exist to prevent for the registry
  table — this is the same failure mode one layer up, at the git
  staging/commit layer instead of the `COMMON.md` prose-table layer. User
  explicitly chose not to rewrite the landed commit (rewriting shared
  history while other threads are actively working off it is its own
  hazard) and asked for a preventive mechanism instead.
- Scope: extend `.ai/tools/claim.py` (do not build a parallel tool —
  same rationale as TASK-0027) with a lock over one well-known resource
  id representing "the stage-and-ship critical section," plus a
  companion guard that checks the actual staged path set against an
  explicit expectation immediately before commit.

## Intent Contract

- Outcome: two independent, complementary protections against the exact
  incident above recurring:
  1. **Time-exclusivity (the lock):** only one thread is ever mid-way
     through "stage files intended for a commit, review, commit" at once.
     A second thread attempting to start that sequence while the lock is
     held is refused, with the current holder and claim age shown, the
     same way `claim.py claim` already refuses on a live task claim.
  2. **Content-exclusivity (the guard):** independent of whether the lock
     was actually held (adoption is gradual, not everyone will remember to
     claim it every time, especially early on), a final safety check
     immediately before `git commit` compares the *actual* staged path set
     against the path set the committing thread explicitly declared, and
     refuses — listing the unexpected extra paths — if they don't match.
     This is what would have caught this session's actual incident even
     if the lock step had been skipped, since the problem was stale
     already-staged content, not two threads racing at the same instant.
- In Scope:
  - **Decided: extend `.ai/tools/claim.py`, not a new tool** — same
    reasoning as TASK-0027: this needs the exact same atomic lock-file
    primitive (`O_EXCL` create under `.ai/tasks/.locks/`) `claim`/`release`
    already implement; a separate tool would just re-derive or import that
    code.
  - **Decided: the lock resource id is a fixed, well-known non-numeric
    name — recommend `GIT-COMMIT`** (not a `TASK-XXXX` id). Today
    `normalize_task_id` raises `SystemExit` on any input without a digit
    (see `.ai/tools/claim.py:41-53`), so this *requires* widening ID
    acceptance the same way TASK-0024.001 already proposes for arbitrary
    whole-file resources. **Reconcile with TASK-0024.001 rather than
    building a second, parallel non-numeric-id path**: if TASK-0024.001
    lands first, this task's `GIT-COMMIT` lock is just one more resource
    id under that generic mechanism; if this task's need is more urgent
    and lands first, implement the minimal non-numeric-id acceptance
    needed for exactly `GIT-COMMIT` in a way TASK-0024.001 can subsume
    later without a breaking change (same lock-file directory and format,
    no separate special-cased storage location).
  - convention: **claim `GIT-COMMIT` before the first `git add` intended
    for a commit, not right before `git commit`** — the incident happened
    between two threads' staging windows, not two simultaneous commit
    calls, so the lock has to cover the whole stage-through-ship window to
    actually prevent it. Release after the commit lands, or explicitly on
    abandoning the staged work.
  - refusal behavior mirrors `claim`: if `GIT-COMMIT` is already locked,
    refuse loudly with the current holder + claim age, exit non-zero — a
    thread must not silently proceed or silently retry-loop.
  - **Decided: the override path is HITL-gated, not agent-self-service.**
    Unlike task-row claims (where any thread can `--force --reason TEXT`
    on its own judgment per TASK-0017's advisory philosophy), overriding a
    held commit lock must not be something an agent decides alone — a
    commit is a harder-to-reverse, shared-history action per this
    project's own "Executing actions with care" guidance. Concretely:
    require a distinct flag (e.g. `--hitl-override`) whose help text and
    the tool's refusal message both say, in effect, "do not pass this
    without an explicit human instruction to do so in the current
    conversation" — the same discipline this thread already followed
    (asking the user directly, via a question or a plan-mode approval,
    before every override-shaped decision this session). This is a
    documentation/convention control, not a cryptographic one — matches
    this scaffold's existing "advisory, human judgment call" philosophy,
    just with a stricter norm for this specific, higher-stakes lock.
  - the index-hygiene guard: a `claim.py commit-guard --expect <path>
    [<path> ...]` (exact subcommand name TBD, see Open Questions) that
    runs `git diff --cached --name-only`, compares against the `--expect`
    list, and exits non-zero with the unexpected extra paths listed if
    they don't match exactly. Intended to run as the last step before
    `git commit`, whether or not the `GIT-COMMIT` lock was held.
  - add both to `.claude/settings.json`'s allowlist (same pattern as
    TASK-0024/0027).
- Out Of Scope:
  - full generic arbitrary-resource locking (`COMMON.md`, or any other
    file) — that ceiling belongs to TASK-0024.001; this task only needs
    the one `GIT-COMMIT` resource id to exist, via whatever the minimal
    path to that is (see the reconciliation note above).
  - a real git hook (`pre-commit`) enforcing the guard automatically —
    worth a future task if the advisory version proves insufficient, but
    this task ships the checkable primitive, not automatic enforcement;
    matches TASK-0017's "advisory first, harden only after a real failure"
    precedent (which is exactly TASK-0024's own origin story).
  - CI gating, distributed locks, or anything beyond a script + local
    files — matches TASK-0024's scope ceiling.
  - rewriting or otherwise fixing the commit that already landed
    misattributed — explicitly declined by the user for this task.
- Constraints And Invariants:
  - Python stdlib only, no new dependency (matches TASK-0024/0027).
  - reuse `.ai/tools/claim.py`'s existing lock-file directory
    (`.ai/tasks/.locks/`) and `O_EXCL` create discipline — do not invent a
    second lock-file location or format for this one resource.
  - the guard must be read-only with respect to the index (it inspects
    `git diff --cached --name-only`, it never stages or unstages
    anything) — keeps its blast radius to "refuse or allow," matching the
    read-only/write-scoped safety split already used elsewhere in
    `CAPABILITIES.md`.
- Planned Validation: (1) thread A claims `GIT-COMMIT`, stages a file;
  thread B attempts to claim `GIT-COMMIT` and is refused with thread A
  named as holder; (2) thread B's `--hitl-override` attempt without the
  flag still refuses; with the flag, succeeds but is clearly logged as an
  override in the lock file (mirroring `claim`'s `forced_from`/
  `override_reason` fields); (3) reproduce this session's actual incident
  on scratch files — stage an "unexpected" file the guard wasn't told
  about, confirm `commit-guard --expect <only the intended path>` refuses
  and names the unexpected one; (4) confirm a clean `--expect` match
  exits 0 and does not itself mutate anything.

## TODO

- [x] Resolve the reconciliation question with TASK-0024.001 (see Open
      Questions) before implementing the non-numeric `GIT-COMMIT` id
      acceptance. — Resolved: implement now (user decision).
- [x] Implement the `GIT-COMMIT` lock via `claim`/`release`/`status`
      (reusing existing code paths, not duplicating them).
- [x] Implement `--hitl-override` on `claim` specifically for non-`TASK-*`
      resource ids (or however scoped per the reconciliation decision),
      distinct in name/messaging from the existing `--force --reason`.
- [x] Implement the index-hygiene guard subcommand.
- [x] Add both to `.claude/settings.json`'s allowlist. — Already covered:
      the existing `Bash(.ai/tools/claim.py *)` / `Bash(python3
      .ai/tools/claim.py *)` wildcard entries match any subcommand/args,
      including `claim GIT-COMMIT ...` and `commit-guard ...`. Verified no
      settings.json change was needed.
- [x] Run Planned Validation, including the scratch-file reproduction of
      this session's actual incident.
- [x] Update `.ai/COMMON.md`'s "Current Rules" to require claiming
      `GIT-COMMIT` before staging commit-bound changes and running the
      guard before `git commit`.

## Dependency

- [TASK-0024](../DONE/TASK-0024-claim-lock-tool.md) (Done) — the lock-file
  primitive this task reuses.
- [TASK-0024.001](TASK-0024.001-whole-file-resource-locks.md) (TODO,
  unclaimed) — closely related generalization; reconcile rather than
  duplicate (see Open Questions).
- [TASK-0019](TASK-0019-scaffold-commit-packaging.md) (TODO) — the
  Commit Packager workflow this lock is meant to protect; once this
  lands, TASK-0019 should require it.

## Open Questions

- **Resolved 2026-07-05 (user decision):** implement now, do not wait on
  TASK-0024.001. Keep the lock-file format identical to `TASK-XXXX.lock`
  so TASK-0024.001 can subsume `GIT-COMMIT` as one more resource id later
  without migration.
- **Resolved 2026-07-05 (user decision):** subcommand name is
  `commit-guard`, as suggested.
- **Resolved 2026-07-05 (user decision):** one global `GIT-COMMIT` lock,
  no per-directory scoping.

## Done

- Extended `.ai/tools/claim.py` (no new tool, no new dependency):
  - `normalize_task_id` now accepts a small fixed `SPECIAL_RESOURCE_IDS`
    set (`{"GIT-COMMIT"}`) checked before the numeric `TASK-XXXX` parsing,
    so `claim`/`release`/`status` all work unchanged on `GIT-COMMIT` —
    same lock-file directory/format as task ids, no separate storage.
    Deliberately scoped to this one literal id, not general
    arbitrary-resource support (that ceiling stays with TASK-0024.001);
    same lock-file format either way, so no migration needed if/when
    TASK-0024.001 lands and wants to subsume it.
  - Added `is_task_id()` and used it to fix a latent bug the new resource
    id would otherwise have hit: `status`'s full-listing dangling-lock
    check (`no task file on disk`) now only applies to actual `TASK-XXXX`
    ids — without this, `GIT-COMMIT` would have been permanently flagged
    as a dangling/orphaned lock, since it never has a task file.
  - `cmd_claim`'s existing `--force --reason` override path now also
    requires `--hitl-override` specifically when the resource being
    overridden is in `SPECIAL_RESOURCE_IDS`. The flag's help text and the
    refusal message both state not to pass it without an explicit human
    instruction in the current conversation — a stricter norm than plain
    task-row overrides, matching the user's "explicitly require HITL
    override" requirement. The override is still recorded in the lock
    file (`forced_from`, `override_reason`, `hitl_override: true`) for
    audit, same as any other forced claim.
  - New `commit-guard --expect PATH [PATH ...]` subcommand: runs `git
    diff --cached --name-only`, refuses (listing the extras) if the
    staged index has more than `--expect`, and separately refuses
    (listing them) if `--expect` names paths that aren't actually staged.
    Read-only with respect to the index — never stages or unstages
    anything.
- Planned Validation, all four cases exercised directly: (1) Thread A
  claims `GIT-COMMIT`; Thread B's plain claim attempt refuses, naming
  Thread A and the claim time. (2) Thread B's `--force --reason` attempt
  without `--hitl-override` still refuses with the dedicated message;
  adding `--hitl-override` succeeds and the resulting lock file records
  `forced_from`/`override_reason`/`hitl_override: true`. (3) Reproduced
  this session's actual incident on two scratch files: staged both,
  `commit-guard --expect <only-the-intended-one>` refused and named the
  unexpected extra — this is the literal failure mode from Context,
  confirmed caught. (4) A matching `--expect` (both scratch files) exited
  0 and left the index untouched; a separately-tested `--expect` naming a
  path that wasn't staged also correctly refused (a different message,
  "not actually staged"). All scratch locks/files cleaned up
  (`GIT-COMMIT` released, scratch files unstaged and removed) before
  finishing.
- Confirmed no `.claude/settings.json` change was needed: the existing
  `Bash(.ai/tools/claim.py *)` and `Bash(python3 .ai/tools/claim.py *)`
  wildcard entries already cover every new subcommand/argument, since
  they match on the base invocation regardless of what follows.
- Added two capability rows to `.ai/reference/CAPABILITIES.md`
  (`repo.commit.lock`, `repo.commit.guard`) and a new "Current Rules"
  bullet in `.ai/COMMON.md` requiring `GIT-COMMIT` to be claimed before
  the first `git add` of commit-bound work (not right before `git
  commit` — the actual incident was an overlapping staging window, not a
  simultaneous commit call) and `commit-guard` to be run immediately
  before every `git commit`.
- **Deliberately not done in this pass:** did not update
  `TASK-0019-scaffold-commit-packaging.md` itself to reference this
  mechanism (one of the original TODO items). While implementing this
  task, `TASK-0019` was found mid-flight — another thread had already
  staged its `TODO/` → `DONE/` rename in the shared index (a real,
  concurrent, live example of exactly the hazard this task addresses).
  Editing that file or its stage state right now would risk colliding
  with that thread's in-progress move; left entirely untouched instead.
  Whoever picks that thread's work back up (or a future pass) should add
  the pointer to this task once TASK-0019 settles.
- Validation performed: `python3 -c "import ast; ast.parse(open('.ai/tools/claim.py').read())"`
  passes; `--help` at top level and for `claim`/`commit-guard` render
  correctly; `sync --check` behavior unaffected by `GIT-COMMIT` lock
  files present or absent (they're outside `sync`'s `TASK-\d{4}` row
  regex and outside `disk_task_ids()`'s task-file scan, by construction).
