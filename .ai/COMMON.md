# .ai Common Hub

Last Updated: 2026-06-25
Status: Active

## Purpose

Central coordination hub for the repo-local agent scaffold.

## Quick Navigation

- scaffold overview: `.ai/README.md`
- architecture overview: `.ai/ARCHITECTURE_OVERVIEW.md`
- active bootstrap task: `.ai/tasks/TASK-0001-agent-scaffold-bootstrap.md`
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

## Source Of Truth

| Scope | Authoritative Location | Notes |
|------|------------------------|-------|
| Stable repo-local runtime policy | `.github/` | Keep durable and short |
| Mutable scaffold coordination | `.ai/` | Active status, backlog, open questions |
| Reviewed scaffold learnings | `.ai/memory/shared/*` | Team truth for the scaffold |
| Capability contracts | `.ai/reference/CAPABILITIES.md` | Behavior-first catalog |
| Workflow backend selection | `.ai/reference/BACKEND_SELECTION.md` | Current task, test, and delegation backend defaults |

## Active Work Registry

| Task ID | Description | Assigned To | Status | Priority | Last Active | Path |
|---------|-------------|-------------|--------|----------|-------------|------|
| TASK-0001 | Bootstrap repo-local agent scaffold under `.github` + `.ai` | Architect/Planner | In Progress | P0 | 2026-06-25 | `.ai/tasks/TASK-0001-agent-scaffold-bootstrap.md` |

## Current Rules

- Additive bootstrap only. Do not rewrite `.claude` broadly in this phase.
- Stable policy belongs in `.github/`.
- Live execution belongs in `.ai/tasks/`.
- Named capabilities belong in `.ai/reference/CAPABILITIES.md`.
- Durable scaffold learnings belong in `.ai/memory/shared/*` after review.

## Open Questions

- When should root-level expert briefs be introduced instead of staying reference-first?
- Which existing `agents-tools` providers should be wrapped first behind generic capability contracts?
- What should be the first post-bootstrap pilot after commit packaging?