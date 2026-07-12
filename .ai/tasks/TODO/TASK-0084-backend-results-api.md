# TASK-0084 Backend results API

## Context

- ID: TASK-0084
- Title: ADD-only endpoints serving precomputed artifacts
  (`/api/results/{target}`, `/api/connectivity/{target}`,
  `/api/verdict/{target}`) — no science in the request path.
- Status: TODO
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 6, item 6.2 —
  "Respects convention 4 [ADD-only, don't break response shapes] and the
  Render cold-start budget."

## Intent Contract

- Outcome: new `backend/` FastAPI endpoints that read TASK-0083's
  artifact format from disk (or wherever it's stored) and serve it as
  JSON, with no science computation triggered by the request itself.
- In Scope: `/api/results/{target}`, `/api/connectivity/{target}`,
  `/api/verdict/{target}` (or whatever exact routes TASK-0083's contract
  implies) — read, validate against the contract schema, serve.
- Out Of Scope: computing the artifacts (TASK-0079/allostery's job);
  triggering a run (TASK-0086's job — this task assumes artifacts already
  exist on disk).
- Acceptance Scenarios:
  - Given a precomputed artifact for KRAS_G12C exists, when
    `/api/results/KRAS_G12C` is requested, then it returns the artifact's
    contents as JSON without importing or invoking `allostery/`.
  - Given no artifact exists yet for a target, then the endpoint returns a
    clear, documented error (e.g. 404) rather than attempting to compute
    one live.
  - Given CLAUDE.md convention 4 (ADD-only, don't break existing response
    shapes), then no existing `backend/` endpoint's response shape
    changes.
- Constraints And Invariants: no `allostery/` import anywhere in
  `backend/` (TASK-0018's Constraints, unchanged); must validate served
  data against TASK-0083's contract schema so a malformed artifact fails
  loudly rather than serving garbage.
- Planned Validation: endpoint tests analogous to TASK-0021's API test
  baseline; a schema-validation test against a known-good and a
  deliberately-malformed artifact.

## Dependency

- Depends on TASK-0083 (result artifact contract) being decided first.
- Depends on TASK-0021 (backend API test baseline) landing first per
  Phase 4's hard rule (no untested convergence into the live service) —
  though this is new endpoint surface, not a convergence of existing
  code, the same testing discipline should apply.
- Feeds TASK-0085 (frontend research visualization) — the frontend
  consumes these endpoints.

## Open Questions

- Where do artifacts live on disk relative to `backend/`'s deployment
  (same Render instance, a mounted volume, object storage)? Depends on
  TASK-0086's execution/trigger-path decision — check that first if it
  lands before this task starts.

## Done

(not yet)
