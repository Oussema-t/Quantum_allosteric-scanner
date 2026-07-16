# TASK-0126 Run H13 (or its N×N projection) through the ceiling search

## Context

- ID: TASK-0126
- Title: `.claude/hypotheses/ceiling.md`'s own "minimum set" names H13
  (alongside H8 and degree centrality) as a required ceiling-search
  candidate. [[TASK-0046]]'s real ceiling search only ever searched
  `H_new`'s own 8-parameter DOF — H13 was never included. Run it (or its
  N×N projection, per HYP-P5 in `hypotheses/physics.md`) through the
  same ceiling-search methodology.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: independently flagged twice — by this Architect/Planner
  thread on 2026-07-16 (before this review landed) and confirmed by
  `.ai/reviews/REVIEW-panel-2026-07-16-v2.md` §5 P2-9 ("your own docs
  call this required").
- Priority: **P2 — weeks 4-6.**

## Intent Contract

- Outcome: H13 (the full 3N×3N ANM Hessian, "the physically richest
  operator" per `HAMILTONIANS.md`) is run through [[TASK-0046]]'s ceiling
  search methodology — either via a documented scalar N×N projection
  (fast, may discard orientational information) or by extending the
  propagators to accept 3N×3N and post-summing to per-residue occupation
  (preserves orientational coupling) — per HYP-P5's own two options.
  Compared against `H_new`'s already-established ceiling on all 3
  mandatory targets.
- Why this matters: `ceiling.md` calls this comparison "required for
  scientific rigor" — without it, choosing `H_new` over H13 remains an
  untested assumption, not a result, regardless of how the seed/clock/
  potential gauge fixes ([[TASK-0118]]/[[TASK-0119]]/[[TASK-0121]])
  resolve `H_new`'s own numbers.
- In Scope:
  - Implement whichever H13 projection option is chosen (Option A:
    scalar trace-of-3x3-blocks projection; Option B: 3N×3N propagator
    extension) — state the choice and why, per HYP-P5's own guidance
    (if H13 beats H_new, Option B — the orientation-preserving one — is
    the defensible choice going forward; if not, Option A's cheaper
    approximation is sufficient and should be documented as a confirmed
    finding, not just an assumption).
  - Run through the same ceiling-search methodology as [[TASK-0046]]/
    [[TASK-0082]] (same DOF-search discipline, same `ceiling_context()`
    gating), on all 3 mandatory targets.
  - Use whatever seed/clock convention [[TASK-0118]]/[[TASK-0119]] have
    settled by the time this task runs — do not reintroduce the seed-
    cardinality confound by seeding H13 differently from `H_new`.
- Out Of Scope:
  - Reselecting the submission operator based on this result alone —
    Tier-2 gated per [[TASK-0100]], same as every other operator-family
    result in this register.
- Constraints And Invariants: report H13's ceiling number with the same
  caveats [[TASK-0116]]/[[TASK-0117]] already attached to `H_new`'s
  (search density, parameter validity) — do not present H13's number as
  more settled than `H_new`'s own, which is still under active
  reconciliation.
- Planned Validation: direct AUC comparison, H13 vs. `H_new`, same
  targets, same seed/clock convention, same search methodology.

## In Progress

None

## TODO

- [ ] Decide projection option (A: scalar N×N; B: 3N×3N propagator
      extension) — state why in Done.
- [ ] Implement chosen option.
- [ ] Run through TASK-0046/0082's ceiling-search methodology, all 3
      mandatory targets.
- [ ] Compare against `H_new`'s established ceiling; report the result
      whichever way it comes out.

## Dependency

- Should use whatever seed/clock convention [[TASK-0118]]/[[TASK-0119]]
  settle — soft ordering, not a hard block if this task starts first
  (in which case, flag which convention was used and re-check later).
- [[TASK-0046]]/[[TASK-0082]] (Done) — reuses their methodology directly.

## Open Questions

- Option A vs. B (scalar projection vs. 3N×3N propagator extension) —
  not pre-decided; Implementer's call per HYP-P5's own guidance, state
  the choice and why in Done.

## Done

(not yet)
