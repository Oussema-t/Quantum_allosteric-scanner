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

**Note (2026-07-04, this thread):** this table was found reverted twice in
one session — first to a pre-TASK-0017 snapshot (missing the claim
columns and every row from TASK-0003 through TASK-0019), then, mid-repair,
to a partial state missing most of TASK-0003–0019 again — even though all
of those task files exist on disk the whole time (`ls .ai/tasks/TODO
IN_PROGRESS DONE` re-checked immediately before this write). Reconstructed
directly from that file listing rather than from another prose read, to
stop chasing a moving target. TASK-0024 (new, below) builds an atomic
claim/free tool so this stops happening. **If you were mid-edit on this
table when it was overwritten, your intended change is not lost** — the
task file itself is the source of truth; re-apply your registry row from
it once you read this note, and treat concurrent whole-file writes to
this table as unsafe until TASK-0024 lands.

Before starting or resuming a row, read `Claimed By` / `Claimed At` first —
see the claim-before-start rule under "Current Rules" below.

| Task ID | Description | Assigned To | Status | Priority | Last Active | Claimed By | Claimed At | Path |
|---------|-------------|-------------|--------|----------|-------------|------------|------------|------|
| TASK-0001 | Bootstrap repo-local agent scaffold under `.github` + `.ai` | Architect/Planner | In Progress | P0 | 2026-06-25 | — | — | `.ai/tasks/IN_PROGRESS/TASK-0001-agent-scaffold-bootstrap.md` |
| TASK-0002 | AI-scaffold hygiene & engineering review (this reconciliation pass) | General Critic | Done | P0 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0002-ai-scaffold-hygiene-review.md` |
| TASK-0003 | Reconcile and author `__WORK_IN_PROGRESS__/config/targets.yaml` | Implementer | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0003-targets-yaml-reconciliation.md` |
| TASK-0004 | Implement `__WORK_IN_PROGRESS__/src/allostery/labels.py` | Implementer | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0004-labels-py.md` |
| TASK-0005 | Implement `__WORK_IN_PROGRESS__/src/allostery/superpose.py` | Implementer | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0005-superpose-py.md` |
| TASK-0006 | Implement `__WORK_IN_PROGRESS__/src/allostery/protocol.py` | Implementer | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0006-protocol-py.md` |
| TASK-0007 | Implement `__WORK_IN_PROGRESS__/src/allostery/select.py` | Implementer | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0007-select-py.md` |
| TASK-0008 | Implement `__WORK_IN_PROGRESS__/src/allostery/analysis.py` | Implementer | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0008-analysis-py.md` |
| TASK-0009 | Implement `__WORK_IN_PROGRESS__/src/allostery/diagnostics.py` | Implementer | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0009-diagnostics-py.md` |
| TASK-0010 | Implement `__WORK_IN_PROGRESS__/src/allostery/report.py` | Implementer | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0010-report-py.md` |
| TASK-0011 | Implement `__WORK_IN_PROGRESS__/src/allostery/baselines.py` | Implementer | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0011-baselines-py.md` |
| TASK-0012 | Implement `__WORK_IN_PROGRESS__/src/allostery/pathways.py` | Implementer | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0012-pathways-py.md` |
| TASK-0013 | Implement `__WORK_IN_PROGRESS__/src/allostery/coarse.py` | Implementer | TODO | P2 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0013-coarse-py.md` |
| TASK-0014 | Implement `__WORK_IN_PROGRESS__/src/allostery/viz.py` | Implementer | TODO | P3 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0014-viz-py.md` |
| TASK-0015 | Build the holo-direction module (`HOLO_DIRECTION_MODULE.md`) | Implementer | TODO | P2 (blocked on 0005/0006/0011) | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0015-holo-direction-module.md` |
| TASK-0016 | Add test for `heat()` behavior on indefinite `H_new` output (orphaned gap, see IMP-H4) | Implementer | TODO | P2 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0016-heat-indefinite-hnew-test.md` |
| TASK-0017 | Soft-lock claim column on this registry (fixes the concurrent-edit near-miss between this session and a parallel thread on TASK-0002/COMMON.md/TASK-0007) | Implementer | Done | P0 | 2026-07-04 | Implementer (this thread) | 2026-07-04 14:30 | `.ai/tasks/DONE/TASK-0017-registry-claim-lock.md` |
| TASK-0018 | Reconcile `backend/` (QAS) vs `__WORK_IN_PROGRESS__/src/allostery` (CCC) architecture — granularity/design-pattern gap confirmed, wraps closed-ledger T-018/T-021 | Architect/Planner | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0018-backend-vs-allostery-architecture-reconciliation.md` |
| TASK-0019 | Package accumulated `.ai`/`.claude` scaffold changes on `bartosz` into ordered, reviewable commits (Commit Packager overlay) | Commit Packager | TODO | P1 | 2026-07-04 | Implementer (this thread) | 2026-07-04 14:58 | `.ai/tasks/TODO/TASK-0019-scaffold-commit-packaging.md` |
| TASK-0020 | Product (backend/frontend) intent & feature inventory audit — endpoint/UI-control census mapped to rubric/roadmap | Architect/Planner | TODO | P0 | 2026-07-04 | Intent-Inferrer (this thread) | 2026-07-04 15:10 | `.ai/tasks/TODO/TASK-0020-product-intent-inventory.md` |
| TASK-0021 | Backend API test-coverage baseline — codify `SOFTWARE.md` §9 examples as `pytest` | Implementer | TODO | P0 | 2026-07-04 | Intent-Inferrer (this thread) | 2026-07-04 15:10 | `.ai/tasks/TODO/TASK-0021-backend-api-test-baseline.md` |
| TASK-0022 | Frontend/UI tiered test coverage — presence / isolated functionality / intent chains / E2E process | Implementer | TODO | P0 | 2026-07-04 | Intent-Inferrer (this thread) | 2026-07-04 15:10 | `.ai/tasks/TODO/TASK-0022-frontend-ui-tiered-test-coverage.md` |
| TASK-0023 | YAGNI / scope-creep review of Product feature backlog vs. challenge rubric | General Critic | TODO | P1 | 2026-07-04 | Intent-Inferrer (this thread) | 2026-07-04 15:10 | `.ai/tasks/TODO/TASK-0023-product-yagni-scope-review.md` |
| TASK-0024 | Whitelisted claim/free tool for scaffold coordination files — hardens TASK-0017 after two real collisions this session | Toolsmith | TODO | P0 | 2026-07-04 | Intent-Inferrer (this thread) | 2026-07-04 15:20 | `.ai/tasks/TODO/TASK-0024-claim-lock-tool.md` |
| TASK-0025 | Single-command preference + reusable-script convention for `.ai/` scaffold threads, delivered as a policy doc + Claude Skill | Skills Crafter | TODO | P2 | 2026-07-04 | Skills Crafter (this thread) | 2026-07-04 16:30 | `.ai/tasks/TODO/TASK-0025-command-hygiene-skill.md` |
| TASK-0026 | Recover `agents-tools/capability-runner.sh` (parent/coordinator — see subtasks below) | Toolsmith | TODO | P1 | 2026-07-04 | Skills Crafter (this thread) | 2026-07-04 16:45 | `.ai/tasks/TODO/TASK-0026-capability-runner-recovery.md` |
| TASK-0026.001 | Dispatcher entry point + `repo.vcs.*` primitives + `repo.packaging.snapshot` | Toolsmith | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0026.001-vcs-core.md` |
| TASK-0026.002 | Remaining `repo.packaging.*` + `repo.maintenance.behavior-contract-capture` + `repo.test.playwright-local` (blocked on .001) | Toolsmith | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0026.002-packaging-remainder.md` |
| TASK-0026.003 | `CAPABILITIES.md` honesty pass + draft allowlist entry (blocked on .001, .002) | Toolsmith | TODO | P2 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0026.003-capabilities-doc-correction.md` |

## Current Rules

- Additive bootstrap only. Do not rewrite `.claude` broadly in this phase.
- Stable policy belongs in `.github/`.
- Live execution belongs in `.ai/tasks/`.
- Named capabilities belong in `.ai/reference/CAPABILITIES.md`.
- Durable scaffold learnings belong in `.ai/memory/shared/*` after review.
- Whoever creates or moves a `TASK-XXXX` file must update this registry in
  the same edit — it must not silently drift out of sync (see Task Ledger
  Boundary above for the `.claude/TASKS.md` split).
- **Claim before you start (TASK-0017).** Before starting or resuming work
  on a registry row — or editing this registry itself, the single most
  contended file in the scaffold — write your claim into that row's
  `Claimed By` / `Claimed At` columns first, as its own edit, before making
  substantive changes to the task file or its dependents. If the row already
  shows another claim, do not proceed silently: either pick a different
  unclaimed task, or if the claim looks stale (see the staleness rule
  below), note the override in that task file's Open Questions and proceed.
  Free-text claim labels are fine (e.g. "Implementer (this thread)",
  "General Critic hygiene pass") — this is advisory, not a distributed
  lock, and nothing enforces it beyond a reader checking the table.
- **Staleness override (TASK-0017).** A claim with no corresponding file
  activity (check the task file's own mtime / `git log -- <path>`) for
  longer than one working session is stale and may be taken over. No
  numeric TTL is enforced — a human or agent reading the table makes the
  call, same as everything else in this scaffold. Example: TASK-0001's
  claim (if it had one) would already read as stale under this rule, since
  its Last Active is 2026-06-25 with no row claim — that's a real
  candidate for override, not a hypothetical, but nobody has taken it over
  as of this writing.
- **This table is unsafe under concurrent whole-file writes (until
  TASK-0024 lands).** Two such collisions happened in this single session.
  If you're about to write this file, `ls .ai/tasks/TODO IN_PROGRESS DONE`
  immediately first and reconcile against that, not against a prose read
  that may already be stale by the time your write lands.

## Open Questions

- When should root-level expert briefs be introduced instead of staying reference-first?
- Which existing `agents-tools` providers should be wrapped first behind generic capability contracts?
- What should be the first post-bootstrap pilot after commit packaging?
