# TASK-0076 WIP graduation part 1: promote the package

## Context

- ID: TASK-0076
- Title: `git mv __WORK_IN_PROGRESS__/src/allostery → allostery/` at the
  repo top level (sibling to `backend/`); update imports and test paths.
  Behaviour-neutral.
- Status: TODO
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 3, item 3.1 —
  "`__WORK_IN_PROGRESS__/` is a *staging* name, not an architecture. The
  package inside it is green (252 tests). ... Graduate it. Three
  mechanical steps, each a separate MR, none changing behaviour."

## Intent Contract

- Outcome: `allostery/` exists at the repo top level as a sibling package
  to `backend/`; every import (`from allostery.x import y` or equivalent
  relative form) and every test path is updated to match; nothing else
  changes.
- In Scope: the `git mv`, import-path updates across `allostery/`'s own
  modules and its test suite, and any doc/reference that points at the
  old `__WORK_IN_PROGRESS__/src/allostery/` path (`.ai/tasks/*`,
  `.claude/TASKS.md`, `ARCHITECTURE.md` if it references the path).
- Out Of Scope: moving anything else out of `__WORK_IN_PROGRESS__/`
  (config, notebooks, planning docs — that's TASK-0078); any behavior
  change whatsoever.
- Acceptance Scenarios:
  - Given the full test suite passes at 252 green before this task starts,
    when the move completes, then the suite still passes at 252 green
    (same count, same tests, new import paths) — a hard equality check,
    not "still passing."
  - Given any doc that references
    `__WORK_IN_PROGRESS__/src/allostery/<file>.py`, then it's updated to
    `allostery/<file>.py`.
- Constraints And Invariants: **no behaviour change** — this is a pure
  structural move. Use `git mv` (not delete+recreate) to preserve file
  history.
- Planned Validation: full test-suite run before and after, comparing
  exact pass count (252) and test names, not just a pass/fail summary.

## Dependency

- Precedes TASK-0077 (single CI) and TASK-0078 (dissolve the folder) —
  do in order, each its own MR per the plan.
- Every task referencing `__WORK_IN_PROGRESS__/src/allostery/*` paths
  (the majority of TASK-0003 through TASK-0069) will have stale path
  references after this lands — not worth mass-editing historical DONE
  task files, but new tasks filed after this lands should use the new
  `allostery/` path.

## Open Questions

- None — mechanical, well-scoped by the plan.

## Done

(not yet)
