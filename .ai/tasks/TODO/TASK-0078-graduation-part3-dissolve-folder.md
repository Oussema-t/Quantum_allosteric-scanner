# TASK-0078 WIP graduation part 3: dissolve the folder

## Context

- ID: TASK-0078
- Title: Move remaining `__WORK_IN_PROGRESS__` contents to permanent
  homes (`config/targets.yaml` → `config/`, notebooks → `notebooks/`,
  planning docs → `documentation/`), then delete the folder.
- Status: TODO
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 3, item 3.3 —
  "Nothing 'dangling' remains." End state: `backend/` (service) ·
  `allostery/` (research) · `config/` · `tests/` · one CI.

## Intent Contract

- Outcome: `__WORK_IN_PROGRESS__/` no longer exists. Its remaining
  contents (after TASK-0076 already moved the `allostery/` package) live
  in permanent, purpose-named locations: `config/targets.yaml` → `config/`,
  notebooks → `notebooks/`, planning docs (including this task's own
  source, `EXECUTION_PLAN.md`) → `documentation/`.
- In Scope: every remaining file under `__WORK_IN_PROGRESS__/` after
  TASK-0076's package move — enumerate at execution time, don't assume
  this list is exhaustive.
- Out Of Scope: the package move itself (TASK-0076, must be done first)
  and CI unification (TASK-0077, should also be done first so the new
  paths are already what CI targets).
- Acceptance Scenarios:
  - Given TASK-0076 and TASK-0077 are both Done, when this task completes,
    then `__WORK_IN_PROGRESS__/` is deleted and every file that was inside
    it resolves to a new, sensible top-level location with no broken
    references (grep the repo for `__WORK_IN_PROGRESS__` — zero hits
    after this task, except historical mentions inside already-DONE task
    files, which are not rewritten).
  - Given `config/targets.yaml` moves, then every consumer (`allostery/`
    modules, any test fixtures) is updated to the new path and the test
    suite stays green.
- Constraints And Invariants: do last, after TASK-0076/0077 — moving the
  folder before the package promotion or CI unification would break both
  of those tasks' assumptions about paths.
- Planned Validation: full test-suite green after the move; a repo-wide
  grep for `__WORK_IN_PROGRESS__` returning only historical references
  inside already-DONE task files (not live code/config paths).

## Dependency

- Depends on TASK-0076 (package promotion) and TASK-0077 (CI unification)
  landing first, in that order.

## Open Questions

- Exact destination for `EXECUTION_PLAN.md` itself and other planning
  docs currently in `__WORK_IN_PROGRESS__/` — confirm `documentation/`
  is the intended top-level name (doesn't exist yet as of this task's
  filing) before creating it.

## Done

(not yet)
