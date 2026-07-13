# TASK-0103 Dumbbell negative-control test suite (well vs. coupling confound)

## Context

- ID: TASK-0103
- Title: Implement the 2×2 control matrix from
  `.ai/reviews/REVIEW-2026-07-13b-operator-falsification-negative-controls.md`
  §2 as a permanent, synthetic (no-PDB, no-network) test module, distinguishing
  operators that measure *coupling* (communication from the active site) from
  operators that measure *well depth* (a structural prior) when the two cues
  are forced to disagree.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `REVIEW-2026-07-13b` (Reviewer Opus thread), §7 Tier 1, item **T-A**
  — "do immediately, unblocks everything." Numbering assigned by this
  (Architect/Planner) thread per the review's own instruction.
- Crit Ref: directly falsifies part of [[TASK-0091]]'s Done conclusion
  (BCR_ABL1 GSR=0.731 as a "genuinely distal signal") — that number is real,
  but this task is the regression test that would have shown *why* it's real
  (well depth, not coupling) instead of leaving that conflated. See
  [[TASK-0104]] for the RESULTS.md/report correction itself.

## Intent Contract

- Outcome: a permanent test module implementing the review's dumbbell
  construction (44 nodes, two equal-length bridges to a DRUG lobe and a
  DECOY lobe, well and coupling strength varied independently), asserting
  the review's own measured double dissociation: `ground_state_relaxation`
  follows the well (scores DECOY when the well is on DECOY even though
  coupling favors DRUG); `ctqw`/ENAQT-style transport follows the coupling
  (scores DRUG regardless of where the well is).
- In Scope:
  - port the review's exact construction (§2): ACTIVE (0-11), DRUG (12-23),
    DECOY (24-35), 4-node bridges of equal length, well = negative diagonal
    potential, coupling = bridge edge weight (strong 1.0 / weak 0.15)
  - the 4 cells (C1 cues agree, C2 well-on-DECOY/coupling-to-DRUG, C3
    well-on-DRUG/coupling-to-DECOY, C4 cues absent) — assert the review's
    measured directions, not necessarily its exact AUC values (re-derive,
    don't hardcode the review's own numbers as ground truth without
    re-running them)
  - test at minimum: `ground_state_relaxation` (must follow the well: low
    AUC(→DRUG) in C2, high in C3), `ctqw`/time-averaged CTQW (must follow
    the coupling: high AUC(→DRUG) in C2, low in C3)
  - average over multiple network seeds (review used 5), report the mean,
    per the review's own methodology
- Out Of Scope:
  - re-deriving or fixing GSR/CTQW's own implementations — this task tests
    existing code as-is
  - the RESULTS.md/report correction — [[TASK-0104]]
  - the new `mode_coparticipation` operator (§6) — [[TASK-0105]]-range,
    later tier, not this task
  - running this against real PDB targets — synthetic only, by design (the
    point is ground truth known by construction)
- Constraints And Invariants:
  - no PDB fetch, no network access — must run in seconds, matching the
    review's own "no PDB, no network access; runs in seconds" framing
  - per `SEAM_PROTOCOL.md`'s definition, this is explicitly a **negative
    control**, not a unit test on either operator alone — it must exercise
    the operator against a case constructed so the confound and the true
    signal disagree, not just check "does it run."
- Planned Validation: the test module itself, run under
  `pytest_local.py`. Every cell's directional assertion must pass; if any
  operator's behavior doesn't match the review's characterization, that's
  a finding to report (via a follow-up), not something to force green by
  loosening the assertion.

## In Progress

None

## TODO

- [ ] Implement the dumbbell network construction (synthetic, seeded).
- [ ] Implement the 4-cell matrix (C1-C4) with well/coupling varied
      independently.
- [ ] Assert `ground_state_relaxation` follows the well; `ctqw`/CTQW-family
      follows the coupling.
- [ ] Run across ≥5 seeds, report mean AUC per cell per operator.
- [ ] Register this as the reusable negative-control harness other
      operator falsification tasks (T-D, T-E) will reuse — don't let a
      second copy of the dumbbell construction get written independently.

## Dependency

- None — self-contained, synthetic, no upstream blocker. Explicitly first
  in the review's own ordering ("T-A first, unconditionally").
- Feeds [[TASK-0104]] (RESULTS.md correction cites this as evidence) and
  future operator-register sweep work (review §7 Tier 2, T-E).

## Open Questions

- None yet — construction and assertions are fully specified by the
  review itself.

## Done

(not yet)
