# TASK-0073 Register cross-tree seams (Kirchhoff/DCC primitive + GNM cutoff)

## Context

- ID: TASK-0073
- Title: File `.ai/seams/` records (owner + seam-test) for the shared
  Kirchhoff/DCC primitive and the GNM cutoff constant, per the adopted
  Seam Protocol (TASK-0050).
- Status: Done
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

**2026-08-03, Architect.** Dependencies re-confirmed Done before starting
(TASK-0066, TASK-0067, TASK-0072 — all three). Filed two new registry
records, both `VERIFIED` at filing time (the seam-tests already existed
and already passed, per TASK-0072's own Done section — this task is the
registry bookkeeping step the Seam Protocol requires, not new test work):

- [[SEAM-0013]] — the two independent `_kirchhoff_eigh`/`_normalized_dcc`
  implementations (`backend/analysis.py` vs. `allostery/potentials.py`,
  TASK-0066) stay bit-identical. Seam-test:
  `TestKirchhoffEighCrossTreeParity`/`TestNormalizedDccCrossTreeParity`
  (7 tests), confirmed to actually fire via `TestDriftIsActuallyDetected`.
- [[SEAM-0014]] — the resolved GNM cutoff constant (8.0 Å, TASK-0067)
  stays the live default at its real GNM-operator-construction call
  sites. Seam-test: `TestGoldenCutoffConstant`. **Scope note recorded in
  the record itself**: this does not cover TASK-0186/TASK-0188's later,
  differently-motivated reuse of the same 8.0 Å value for spatial
  contact-graph hop-distance — a different question (BFS hop-count, not
  eigendecomposition), asked of a superficially similar constant. Flagged
  explicitly so a future reader doesn't assume this seam already covers
  that usage.

Cross-linked back from all three upstream task files (TASK-0066,
TASK-0067, TASK-0072's own Done sections, dated addenda) per this task's
own Acceptance Scenario. No change to `.ai/COMMON.md`'s Quick Navigation
— it references the seam registry generically, not a per-seam count, so
nothing there needed updating.

Format cross-checked against `.ai/seams/README.md`'s required fields
(units, invariant, owner, seam-test, status, provenance) and SEAM-0001's
precedent for citing a `(Done)` task as owner when a seam is registered
retroactively/already-verified — no existing SEAM record renumbered.
