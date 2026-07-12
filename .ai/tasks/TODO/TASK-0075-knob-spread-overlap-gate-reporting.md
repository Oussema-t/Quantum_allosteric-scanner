# TASK-0075 Knob-spread reporting for the cumulative-overlap go/no-go gate

## Context

- ID: TASK-0075
- Title: Make the cumulative-overlap go/no-go gate emit a spread across
  the (cutoff × variant × k × reference) grid and return `UNSTABLE` when
  modeling choices — not the physics — decide the verdict.
- Status: TODO
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 5, item 5.5 — "Per
  INVARIANCE_PROTOCOL: cutoff / variant / `k` / reference are **KNOBs, not
  gauge**. On a toy case the same motion swung **0.067–0.860** across an
  18-combo grid, flipping go/no-go in 15 of 18. The gate must emit a
  **spread** and return `UNSTABLE` when knobs decide the verdict — never a
  point estimate." Directly ties to INV-0001 (`.ai/invariants/`) which
  already flagged this class of issue.

## Intent Contract

- Outcome: the cumulative-overlap gate (wherever it currently lives —
  check `analysis.py`/`pathways.py`) no longer returns a single GO/NO-GO
  point estimate. It sweeps the named knobs (cutoff, ANM variant, number
  of modes `k`, reference structure choice), reports the resulting score
  spread, and classifies the verdict as `UNSTABLE` whenever the spread
  crosses the go/no-go threshold within the tested grid (i.e. the
  knob choice alone flips the answer).
- In Scope: the gate function itself; its three-way verdict vocabulary
  (GO / NO-GO / UNSTABLE) propagated to every consumer (`diagnostics.py`,
  `report.py`, and eventually TASK-0079's end-to-end run and TASK-0083's
  artifact contract, which must have a slot for `UNSTABLE`).
- Out Of Scope: re-deriving the 18-combo toy-case numbers cited in the
  plan (0.067–0.860 spread, 15/18 flips) — that evidence already exists
  somewhere (locate it, likely `.ai/invariants/INV-0001` or its
  supporting material); this task wires the *reporting mechanism* the
  finding demands.
- Acceptance Scenarios:
  - Given the toy case that previously showed a 0.067–0.860 spread
    flipping 15/18 combos, when the gate runs with knob-spread reporting,
    then it returns `UNSTABLE` rather than a single GO or NO-GO.
  - Given a case where all knob combinations agree, then the gate returns
    a decisive GO/NO-GO plus the (narrow) spread, not just a bare verdict.
- Constraints And Invariants: per the Invariance Protocol (TASK-0051),
  this is exactly the required GAUGE/KNOB/SIGNAL transformation-table
  discipline — "invariant on our test set" is not a green light, widen
  the transformation group. Cross-reference `.ai/invariants/INV-0001`.
- Planned Validation: the toy-case acceptance scenario above; extend to
  at least one real benchmark target.

## Dependency

- Related to TASK-0046 (ceiling coordinate-descent search) and TASK-0015
  (holo-direction module) — both consume or produce cumulative-overlap
  gate output; check whichever lands first for the current call
  signature.
- Feeds TASK-0083 (result artifact contract) — the verdict vocabulary
  (GO/NO-GO/UNSTABLE) must be part of that contract from the start.
- Cross-references `.ai/invariants/INV-0001`.

## Open Questions

- Where does the 18-combo toy-case evidence (0.067–0.860 spread) actually
  live today — is it already in `.ai/invariants/INV-0001` or does it need
  to be re-run to produce citable numbers for this task's Done section?

## Done

(not yet)
