# TASK-0083 Result artifact contract ⚠️ decide EARLY

## Context

- ID: TASK-0083
- Title: Define the versioned artifact `allostery` emits and `backend`
  consumes — the seam between research and delivery.
- Status: TODO
- Owner: Architect/Planner
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md`'s Architectural premise
  (top of the plan) and Phase 6, item 6.1 — "This one decision keeps
  `backend` free of `allostery` imports and unblocks frontend work **in
  parallel** with the science. Filed early even though 6.2–6.4 are late."
  Final link in the critical path (`... → 5.2 → 6.1`). Keystone decision:
  **"The research package emits versioned result artifacts. The backend
  serves artifacts; it never recomputes science in the request path."**
  This corrects/extends TASK-0018's "port, don't cross-import" verdict —
  `backend/` still imports nothing from `allostery/`, but now reads a
  JSON/NPZ contract instead of having no relationship to the research
  results at all.

## Intent Contract

- Outcome: a documented, versioned artifact format that `allostery/`'s
  pipeline (via TASK-0079's end-to-end run) writes and `backend/` (via
  TASK-0084's results API) reads — with no code import in either
  direction across the `backend/`↔`allostery/` boundary, consistent with
  TASK-0018's Constraints.
- In Scope: the artifact schema, covering (per the plan): the N×N
  connectivity matrix (NPZ), ranked residues + scores, per-target verdict
  (GO / NO / **UNSTABLE**, per TASK-0075) with knob-spread, floor/ceiling/
  headroom (TASK-0082's competence map), a frozen-config **hash**
  (provenance that the result came from the actual frozen pipeline state,
  not a stale or hand-edited run), and general provenance metadata
  (target ID, structure versions, timestamp, pipeline version).
- Out Of Scope: implementing the producer (TASK-0079 already does the
  computation; this task defines what it writes) or consumer (TASK-0084)
  — this task is the contract/schema decision itself, plus perhaps a
  reference writer/reader stub, not the full API.
- Acceptance Scenarios:
  - Given the contract is defined, when `allostery/`'s pipeline finishes
    a target run, then it can write one artifact file/bundle satisfying
    the schema, self-contained (no live recomputation needed to interpret
    it).
  - Given the same artifact, when `backend/` reads it, then it can serve
    every field the frontend (TASK-0085) needs without importing
    `allostery/` or recomputing anything.
  - Given a stale or hand-edited artifact, when its frozen-config hash is
    checked, then a mismatch is detectable (provenance integrity).
- Constraints And Invariants: **decide this early, before 6.2–6.4** per
  the plan's explicit flag — it unblocks frontend work in parallel with
  ongoing science work. Must accommodate TASK-0075's `UNSTABLE` verdict
  state and TASK-0082's floor/ceiling/headroom fields from day one, not
  as a later add-on. No science recomputation in `backend/`'s request
  path (Render cold-start budget, per TASK-0018's Constraints, still
  applies).
- Planned Validation: a reference artifact produced by TASK-0079 for one
  target, validated against this task's schema; a stub reader confirming
  `backend/` could parse it without importing `allostery/`.

## Dependency

- Should be decided **before** TASK-0084 (backend results API) and
  TASK-0085 (frontend research visualization) start, per the plan's
  explicit "decide EARLY" flag — but can be scoped in parallel with
  TASK-0079/5.1-5.2 rather than strictly after them, since the schema
  design doesn't require the actual run to complete first (though
  validating against a real artifact does).
- Must incorporate TASK-0075's verdict vocabulary (GO/NO-GO/UNSTABLE) and
  TASK-0082's competence-map fields (floor/ceiling/headroom).
- Feeds TASK-0084 (backend results API) and TASK-0086 (execution/trigger
  path — how the artifact actually gets produced/refreshed).

## Open Questions

- NPZ vs JSON vs a hybrid (NPZ for the dense connectivity matrix, JSON
  for everything else) — the plan mentions both formats without
  specifying which field uses which; this task should decide and record.

## Done

(not yet)
