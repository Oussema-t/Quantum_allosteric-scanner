# .ai Common Hub

Last Updated: 2026-07-04
Status: Active

## Purpose

Central coordination hub for the repo-local agent scaffold.

## Quick Navigation

- scaffold overview: `.ai/README.md`
- architecture overview: `.ai/ARCHITECTURE_OVERVIEW.md`
- active bootstrap task: `.ai/tasks/IN_PROGRESS/TASK-0001-agent-scaffold-bootstrap.md`
- first agent bootstrap guide: `.ai/reference/FIRST_AGENT_BOOTSTRAP.md`
- second expert handoff walkthrough: `.ai/reference/SECOND_EXPERT_THREAD_WALKTHROUGH.md`
- local automation guidance: `.ai/reference/LOCAL_AUTOMATION_MANUAL_ENVIRONMENTS.md`
- capability catalog: `.ai/reference/CAPABILITIES.md`
- traceability model: `.ai/reference/TRACEABILITY_MODEL.md`
- resolution vocabulary: `.ai/reference/RESOLUTION_VOCABULARY.md`
- adoption guide: `.ai/reference/ADOPTION_GUIDE.md`
- minimum copy bundle: `.ai/reference/MINIMUM_COPY_BUNDLE.md`
- issue backend contract: `.ai/reference/ISSUE_BACKEND_PLACEHOLDER_CONTRACT.md`
- memory policy: `.ai/memory/README.md`
- backend selection: `.ai/reference/BACKEND_SELECTION.md`
- roadmap / phase-gated plan: `.ai/tasks/PLANS/PLAN.md`
- weekly timeline overlay: `.ai/tasks/PLANS/PLAN-01.07.26.md`

## Source Of Truth

| Scope | Authoritative Location | Notes |
|------|------------------------|-------|
| Stable repo-local runtime policy | `.github/` | Keep durable and short |
| Mutable scaffold coordination | `.ai/` | Active status, backlog, open questions |
| Reviewed scaffold learnings | `.ai/memory/shared/*` | Team truth for the scaffold |
| Capability contracts | `.ai/reference/CAPABILITIES.md` | Behavior-first catalog |
| Workflow backend selection | `.ai/reference/BACKEND_SELECTION.md` | Current task, test, and delegation backend defaults |
| New work touching `__WORK_IN_PROGRESS__` module code | `.ai/tasks/TASK-XXXX` | See "Task ledger boundary" below — `.claude/TASKS.md` is closed to new entries |

## Task Ledger Boundary

`.claude/TASKS.md` and `.ai/tasks/TODO\|IN_PROGRESS\|DONE/` are two systems
covering overlapping ground (both can describe work on
`__WORK_IN_PROGRESS__/src/allostery/`). Decision (TASK-0002, 2026-07-04):
they do **not** get merged.

- `.claude/TASKS.md` stays as the closed historical ledger for its own
  BLUE/RED/ORCH review-remediation cycle (T-001…T-021, sourced from
  `.claude/criticism/*`). Do not delete or renumber it.
- **No new `T-NNN` entries get added.** Any new work item — including work
  on the same `__WORK_IN_PROGRESS__` codebase — is filed as a
  `.ai/tasks/TASK-XXXX` file going forward (TASK-0003 already establishes
  this pattern for module-content work).
- If `.claude/TASKS.md`'s remaining `TODO`/`Blocked` rows (T-017, T-018,
  T-021) are picked up again, wrap them in a `TASK-XXXX` file that links
  back to the `T-NNN` row rather than resuming the old ledger in place.

## Active Work Registry

| Task ID | Description | Assigned To | Status | Priority | Last Active | Path |
|---------|-------------|-------------|--------|----------|-------------|------|
| TASK-0001 | Bootstrap repo-local agent scaffold under `.github` + `.ai` | Architect/Planner | In Progress | P0 | 2026-06-25 | `.ai/tasks/IN_PROGRESS/TASK-0001-agent-scaffold-bootstrap.md` |
| TASK-0002 | AI-scaffold hygiene & engineering review (this reconciliation pass) | General Critic | Done | P0 | 2026-07-04 | `.ai/tasks/DONE/TASK-0002-ai-scaffold-hygiene-review.md` |

## Current Rules

- Additive bootstrap only. Do not rewrite `.claude` broadly in this phase.
- Stable policy belongs in `.github/`.
- Live execution belongs in `.ai/tasks/`.
- Named capabilities belong in `.ai/reference/CAPABILITIES.md`.
- Durable scaffold learnings belong in `.ai/memory/shared/*` after review.
- Whoever creates or moves a `TASK-XXXX` file must update this registry in
  the same edit — it must not silently drift out of sync (see Task Ledger
  Boundary above for the `.claude/TASKS.md` split).

## Open Questions

- When should root-level expert briefs be introduced instead of staying reference-first?
- Which existing `agents-tools` providers should be wrapped first behind generic capability contracts?
- What should be the first post-bootstrap pilot after commit packaging?