# TASK-0073 Register cross-tree seams (Kirchhoff/DCC primitive + GNM cutoff)

## Context

- ID: TASK-0073
- Title: File `.ai/seams/` records (owner + seam-test) for the shared
  Kirchhoff/DCC primitive and the GNM cutoff constant, per the adopted
  Seam Protocol (TASK-0050).
- Status: TODO
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 2, item 2.5 —
  "so the green bar remembers the boundary — mechanism, not discipline."

## Intent Contract

- Outcome: two new `.ai/seams/SEAM-XXXX` records: one for the shared
  Kirchhoff-context/DCC primitive (TASK-0066/TASK-0072's territory), one
  for the GNM cutoff constant now pinned by TASK-0067. Each with a named
  owner and a seam-test reference (TASK-0072's drift test satisfies both).
- In Scope: `.ai/seams/` registry entries only, following the existing
  format (see `SEAM-0003` through `SEAM-0010` for the template).
- Out Of Scope: writing the seam-tests themselves — that's TASK-0072;
  this task registers them once they exist (or as `xfail`-referencing
  placeholders if filed before TASK-0072 lands, per the Seam Protocol's
  allowance for `OPEN` seams with an `xfail` test).
- Acceptance Scenarios:
  - Given TASK-0066/0067/0072 land, then a `.ai/seams/SEAM-XXXX` record
    exists for each of the two boundaries, cross-linked from those task
    files and from `.ai/COMMON.md`'s Quick Navigation if warranted.
- Constraints And Invariants: follow `.ai/reference/SEAM_PROTOCOL.md`'s
  format exactly; don't renumber existing SEAM records.
- Planned Validation: `.ai/seams/README.md`'s own checklist for a
  well-formed seam record.

## Dependency

- Depends on TASK-0066 (shared helper), TASK-0067 (cutoff constant),
  TASK-0072 (the drift test that becomes the seam-test) landing first —
  this task is the registry bookkeeping step after those.

## Open Questions

- None — mechanical registration once the upstream tasks land.

## Done

(not yet)
