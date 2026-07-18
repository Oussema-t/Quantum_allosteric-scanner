# TASK-0133 Learnability gate control: does a random patch also score high on cumulative overlap?

## Context

- ID: TASK-0133
- Title: [[TASK-0120]]'s `learnability_verdict` requires pocket RMSD ≥
  1.5x background **AND** CO(20) < 0.5 to call a target
  `UNLEARNABLE_FROM_APO`. The conjunction is doing real work but is
  untested against a control: does cumulative overlap onto the apo ANM's
  lowest 20 modes discriminate "spans *this pocket's* displacement" from
  "spans *any* displacement" at all? Compute CO(20) for a random
  16-residue patch on each target and compare to the real pocket's own
  CO(20).
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `.ai/reviews/REVIEW-panel-2026-07-17.md` §5.2. Estimated cost:
  half a day.
- Priority: **P1.** Directly qualifies whether TASK-0120's headline
  (`LEARNABLE` on all 3 targets) means what it currently reads as
  meaning.

## Intent Contract

- Outcome: `superpose.background_rmsd`/`cumulative_overlap` (both
  already exist, per TASK-0120's own Done section) applied to a random
  16-residue patch per target (same patch size as this project's own
  real pockets, for comparability — confirm each target's real pocket
  size before choosing 16, per TASK-0120's own table, and use the real
  size if it differs), repeated across multiple random draws to get a
  distribution, not a single patch. Compare the real pocket's CO(20)
  against this random-patch distribution.
- Why this matters, stated precisely (per the review's own framing): if
  a random patch *also* scores 0.58-0.79 (the range TASK-0120 measured
  for the real pockets), then CO(20) is measuring how much of *any*
  displacement the soft-mode subspace spans — a property of the apo
  structure's own flexibility, not of the pocket specifically — and
  TASK-0120's `LEARNABLE` verdict would need to be read as "the soft
  modes are broadly expressive" rather than "the soft modes specifically
  encode this pocket's opening." If the real pocket scores measurably
  higher than the random-patch distribution, that supports the current
  reading as-is.
- **This does not retract TASK-0120's own measurement** (the RMSD/CO
  numbers themselves are unaffected) — it is a control on the
  *interpretation* of the CO half of the conjunction, per this project's
  own discipline of not reading a passing test as validation until the
  discriminating control has actually been run (the exact lesson of
  `pitfalls.md` P-0001).
- In Scope:
  - All 3 mandatory targets, multiple random-patch draws per target
    (report how many and why — enough for a real distribution, not a
    single anecdote).
  - Direct comparison: real-pocket CO(20) vs. random-patch CO(20)
    distribution, reported explicitly (not just "higher" or "lower" —
    the actual numbers and spread).
  - Update [[TASK-0120]]'s own `RESULTS.md` section additively with
    this control's result, per this project's no-silent-overwrite
    convention.
- Out Of Scope:
  - Changing `learnability_verdict`'s own threshold logic — this task
    is a control/measurement, not a redesign; if the control changes how
    the verdict should be read, that's a follow-up decision for whoever
    reads this task's result, not this task's own call.
  - BCR_ABL1's own already-flagged nuance (fails the RMSD half, not
    reached via the CO half at all per TASK-0120's own Done section) —
    unaffected by this control, which is specifically about the CO
    half's discriminating power.
- Constraints And Invariants: random patches must be drawn from the same
  common apo/holo correspondence set TASK-0120 already restricts to (not
  from the full residue set, which could include residues where the
  original measurement itself was unmeasurable).
- Planned Validation: the comparison itself is this task's validation —
  report the real pocket's percentile within the random-patch
  distribution per target, mirroring the same "percentile within a null"
  framing [[TASK-0131]] uses for the ceiling.

## In Progress

None

## TODO

- [ ] Draw multiple random same-size patches per target from the common
      correspondence set; compute CO(20) for each.
- [ ] Compare real-pocket CO(20) against the random-patch distribution,
      per target.
- [ ] Report the real pocket's percentile within that distribution.
- [ ] Update `RESULTS.md`'s learnability-gate section additively.

## Dependency

- [[TASK-0120]] (Done) — reuses its own `background_rmsd`/
  `cumulative_overlap` machinery directly, no new implementation needed
  beyond the patch-sampling loop itself.

## Open Questions

- Number of random-patch replicates needed for a stable distribution —
  Implementer's call, state the choice and why in Done (mirroring
  [[TASK-0131]]'s own replicate-count reasoning for the ceiling null).

## Done

(not yet)
