# TASK-0026 capability-runner-recovery (parent/coordinator)

## Context

- ID: TASK-0026
- Title: Recover `agents-tools/capability-runner.sh` — the capability
  dispatcher `.ai/reference/CAPABILITIES.md` documents 16 times as the
  "Current Provider" for the entire Commit Packager capability set, but
  which does not exist anywhere on disk in this repo
- Status: TODO
- Owner: Toolsmith
- Claimed By: Skills Crafter (this thread)
- Claimed At: 2026-07-04 16:45
- Source: gap surfaced in TASK-0025's Constraints And Invariants (this
  session, 2026-07-04); user confirmed the script existed in the source
  AI-Scaffolding repo this project's `.ai/` scaffold was adapted from, and
  was not carried over during that adaptation — this repo has the
  capability *documentation* but not the *provider*.
- Scope: this file is a parent/coordinator only (see
  `.ai/tasks/README.md`'s dotted-subtask convention, introduced this same
  session for exactly this case) — it holds the locked decisions and a
  subtask table; implementation detail lives in the subtask files so no
  single thread has to claim one giant task.

## Decisions (locked this session — do not re-litigate without new evidence)

- No access to the original source scaffold's `agents-tools/`
  implementation is assumed — **re-derive the runner and its subcommands
  directly from `.ai/reference/CAPABILITIES.md`'s documented behavior**,
  not from a port. If a source copy does turn up later, reconcile against
  it then; don't block on it now.
- `agents-tools/` becomes a **real, git-tracked directory at repo root**
  (it is not `.gitignore`d — it simply has never been created). Its
  contents are committed like any other repo-local tooling, not a
  scratch/local-only location.

## Subtasks

| Task | Scope | Status |
|------|-------|--------|
| [TASK-0026.001](../DONE/TASK-0026.001-vcs-core.md) | Dispatcher entry point + `repo.vcs.*` read-only primitives + `repo.packaging.snapshot` composite | Done (2026-07-09, Toolsmith thread) |
| [TASK-0026.002](TASK-0026.002-packaging-remainder.md) | Remaining `repo.packaging.*` rows + `repo.maintenance.behavior-contract-capture` + `repo.test.playwright-local` | TODO (blocked on .001) |
| [TASK-0026.003](TASK-0026.003-capabilities-doc-correction.md) | `CAPABILITIES.md` honesty pass (correct any row not actually implemented) + draft `.claude/settings.json` allowlist entry | TODO (blocked on .001, .002) |
| [TASK-0026.004](TASK-0026.004-test-execution-self-verification.md) | Named request-file presets for `repo.test.playwright-local` (tied to TASK-0021/0022) + sibling `repo.test.pytest-local` capability, so any thread can self-verify Product changes via a whitelisted preset | TODO (filed by a concurrent thread this session; depends on TASK-0026.002's base wrapper) |

This task (TASK-0026) is Done only when all four subtasks are Done — see
`Done` section below for the rollup check.

## Intent Contract

- Outcome: every capability row in `.ai/reference/CAPABILITIES.md` whose
  "Current Provider" names `agents-tools/capability-runner.sh` either has a
  real, runnable, git-tracked backing implementation, or the row honestly
  says it doesn't yet.
- In Scope: the two locked decisions above and the subtask split.
  Implementation detail lives in TASK-0026.001/.002; correction-pass detail
  lives in TASK-0026.003.
- Out Of Scope: `.ai/tools/claim.py` / TASK-0024 — sibling effort, separate
  task, not folded in here even though both are repo-local tool recoveries
  landing around the same time.
- Constraints And Invariants (apply to all three subtasks):
  - Python stdlib or POSIX shell only, no new runtime dependency.
  - every subcommand implements `--json` wherever `CAPABILITIES.md` already
    promises it.
  - deterministic, sorted output wherever `CAPABILITIES.md` already claims
    determinism — a correctness requirement, since Commit Packager work
    depends on stable repeated output.
- Planned Validation: each subtask validates its own slice (see each
  subtask file); TASK-0026.003 re-validates the full `CAPABILITIES.md`
  table against what actually landed.

## In Progress

None

## TODO

- [ ] Track subtask completion (see table above); update this file's
      `Done` section once all three land.
- [ ] Confirm no fourth subtask is needed once .001/.002 are underway (e.g.
      if a capability turns out not to decompose cleanly into either
      slice).

## Dependency

- `.ai/reference/CAPABILITIES.md` — the spec every subtask must satisfy or
  correct.
- `.github/instructions/tooling/capability-selection.instructions.md` —
  provider-order rule.
- `.ai/tasks/README.md` — now documents the dotted-subtask convention this
  task introduces.

## Open Questions

- Should `agents-tools/` vs `.ai/tools/` be reconciled as "the" repo-local
  script home going forward, now that both will hold real tracked files
  (`agents-tools/capability-runner.sh` here, `.ai/tools/claim.py` under
  TASK-0024)? Flagged, not decided — a future task should address this once
  both exist, rather than guessing now.
- **Added 2026-07-05 (Toolsmith thread + Reviewer, via TASK-0029 —
  contributed evidence, this task remains claimed by Skills Crafter, not a
  claim override):** should `.ai/tools/claim.py` eventually register under
  a structurally-validated capability-runner dispatch model (whatever
  `agents-tools/capability-runner.sh` ends up being) instead of being
  whitelisted via enumerated `.claude/settings.json` entries per
  subcommand? Context: TASK-0029 needed to scope a new `stage` subcommand
  so claim.py's own blanket wildcard allowlist couldn't silently imply
  unconstrained `git add`. The near-term fix landed was enumerating each
  of claim.py's subcommands explicitly in `.claude/settings.json` (no new
  code, closes the same "silent future-subcommand creep" gap for every
  subcommand, not just `stage`) — a Reviewer note on that work flagged the
  heavier dispatch-model alternative as a better fit for this task's own
  scope rather than deciding it ad hoc in TASK-0029, since this task
  already defers the parallel `agents-tools/` vs `.ai/tools/` "one script
  home" question above. Recommend resolving both questions together once
  a subtask here actually builds the dispatcher, rather than separately.

## Done

(not yet — waiting on TASK-0026.001, TASK-0026.002, TASK-0026.003,
TASK-0026.004)
