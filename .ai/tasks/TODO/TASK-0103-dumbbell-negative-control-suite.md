# TASK-0103 Dumbbell negative-control test suite (well vs. coupling confound)

## Context

- ID: TASK-0103
- Title: Implement the 2×2 control matrix from
  `.ai/reviews/REVIEW-2026-07-13b-operator-falsification-negative-controls.md`
  §2 as a permanent, synthetic (no-PDB, no-network) test module, distinguishing
  operators that measure *coupling* (communication from the active site) from
  operators that measure *well depth* (a structural prior) when the two cues
  are forced to disagree.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer B (this thread)
- Claimed At: 2026-07-13 23:10
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

- [x] Implement the dumbbell network construction (synthetic, seeded).
- [x] Implement the 4-cell matrix (C1-C4) with well/coupling varied
      independently.
- [x] Assert `ground_state_relaxation` follows the well; `ctqw`/CTQW-family
      follows the coupling.
- [x] Run across ≥5 seeds, report mean AUC per cell per operator.
- [x] Register this as the reusable negative-control harness other
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

- New permanent module: `__WORK_IN_PROGRESS__/tests/test_dumbbell_negative_control.py`.
  Public, reusable `build_dumbbell_network(well_lobe, strong_lobe, *,
  well_depth=5.0, seed=0)` and `auc_to_drug(H, propagator, t=20.0)` —
  future falsification tasks (T-D `mode_coparticipation`, T-E register
  sweep) import these directly, not a second copy.
- Construction verified empirically before locking in assertions (per
  this session's own established practice — nothing hardcoded from the
  review without re-derivation):
  - **Found and fixed a real bug in the first prototype**: intra-lobe
    edges and bridge anchors were fully deterministic (a bare clique,
    fixed anchor node 0), so "averaging over 5 seeds" silently averaged
    five identical numbers. Fixed by randomizing intra-lobe edge weights
    (`uniform(0.7, 1.3)`) and each lobe's bridge-anchor node per seed.
    Regression-guarded directly:
    `TestBuildDumbbellNetwork::test_seeds_actually_vary_the_network`.
  - `well_depth=5.0` chosen empirically, not guessed: swept {3, 5, 8} and
    confirmed the C2/C3 double dissociation is robust across all three
    (0.000/1.000 and 1.000/0.000 respectively, exactly). C1 (the review's
    own "uninformative" cell) showed non-monotonic CTQW sensitivity to
    well depth (0.163 -> 0.104 -> 0.758) — a real, resonance-like
    artifact of coherent dynamics interacting with a deep trap, not a
    construction bug; consistent with the review's own framing that C1
    cannot discriminate the confound, so it is asserted only loosely.
- **Reproduced the review's decisive double dissociation cleanly**:
  - C2 (well=DECOY, strong coupling=DRUG): GSR mean AUC(->DRUG) = 0.000,
    CTQW mean AUC(->DRUG) = 1.000 (5 seeds).
  - C3 (well=DRUG, strong coupling=DECOY): GSR mean AUC(->DRUG) = 1.000,
    CTQW mean AUC(->DRUG) = 0.000 (5 seeds).
  - C4 (no well, equal coupling): both propagators land near chance once
    real seed-to-seed variance exists (GSR 0.565, CTQW 0.614 — the review
    itself only claims "all ≈ chance," not a precise value; asserted with
    a loose `|AUC-0.5|<0.3` bound for exactly that reason).
- `metrics.auc` (this repo's own wrapper) used for scoring, not raw
  `sklearn.roc_auc_score`, matching this codebase's "reuse, don't
  reinvent" convention.
- 10 tests, all passing. `ground_state_relaxation`'s `_warn_if_indefinite`
  `UserWarning` fires as expected on every well-bearing cell (confirms
  the test is genuinely exercising the indefinite-H path the review's
  finding is about, not a problem to silence).
- Full local run: `python3 .ai/tools/pytest_local.py wip-all --json` →
  507 passed, 1 xpassed (pre-existing, unrelated), 0 failed.
- **Staging/commit deliberately skipped** — explicit user instruction
  this session ("Do NOT git add or git commit anything — leave the stage
  empty. I'm orchestrating which package ships when").
