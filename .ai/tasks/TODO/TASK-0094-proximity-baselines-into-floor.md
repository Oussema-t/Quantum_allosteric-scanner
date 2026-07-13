# TASK-0094 Proximity baselines into the floor — blocks every current headline number

## Context

- ID: TASK-0094
- Title: Add `euclid_from_seed_centroid` and `hop_from_seed` (both negated,
  closer = higher score) to `baselines.py`; wire into `floor_scores` and
  `classify_failure`'s floor; re-run all mandatory targets.
- Status: TODO
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/REVIEW-2026-07-13-proximity-confound-and-propagator-semantics.md`,
  finding **P1-A**. Executed against real code on a synthetic 170-residue
  globule (not inferred): `Spearman(time_averaged_ctqw occupation, -Euclidean
  distance from seed) = +0.853`; on a pocket placed adjacent to the seed,
  a pure distance baseline (AUC 0.966) **beats** the CTQW score (0.914); on
  a distal pocket, both collapse (CTQW 0.035, distance 0.000). `baselines.py`
  currently has no proximity/distance baseline at all — `classify_failure`'s
  only floor is `degree_centrality`, which is not the confounding variable.

### Why this is first, and blocks everything downstream

Per the review's cross-target evidence: KRAS_G12C (pocket adjacent to
active site, AUC 0.779) and CARDIAC_MYOSIN (near ADP/converter, AUC 0.786)
both score well; BCR_ABL1 (myristoyl, ~25 Å distal, AUC 0.525) is at
chance. **The one target with a genuinely distal pocket is the one
target at chance** — the signature of a proximity detector, not an
allostery detector, on a challenge whose entire premise is *distal*
regulatory sites. Every headline AUC currently in `RESULTS.md` (from
TASK-0079.005's real run) was produced without this floor and must be
re-evaluated once it exists.

## Intent Contract

- Outcome: two new baseline functions in `baselines.py` —
  `euclid_from_seed_centroid` (negative Euclidean distance from the
  seed-residue centroid) and `hop_from_seed` (negative graph-hop distance
  from the seed set, on the same contact graph the scored operator uses)
  — wired into `floor_scores` and `classify_failure`'s floor logic
  alongside the existing `degree_centrality` check, plus a re-run of all
  three mandatory targets (KRAS_G12C, BCR_ABL1, CARDIAC_MYOSIN) with the
  new floor applied.
- In Scope: `baselines.py` (new functions), `diagnostics.classify_failure`
  (extend the floor check — this already has a `floor_scores` parameter
  and a `BEATS_CHANCE_NOT_FLOOR` category from TASK-0058, extend rather
  than re-architect), the orchestrator (`TASK-0079.004`'s entry point) to
  pass the new baselines through, and a re-run producing updated
  `RESULTS.md` numbers.
- Out Of Scope: fixing the propagator-semantics bug (TASK-0095) or the
  phantom operators (TASK-0096) — those are separate, independently
  actionable findings from the same review; don't conflate scope.
- Acceptance Scenarios:
  - Given the synthetic-globule reproduction in the review, when
    `euclid_from_seed_centroid`/`hop_from_seed` are computed, then they
    reproduce (or closely match) the review's own Spearman/AUC numbers
    (+0.853 Euclidean-Spearman on the reproduction case) — this task's
    implementation must be checked against the review's own evidence, not
    assumed correct by construction.
  - Given the re-run on real KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN data, when
    `classify_failure` runs with the new floor, then each target's
    verdict states explicitly whether its AUC clears the proximity floor
    — not just chance and degree.
- Constraints And Invariants: **hard acceptance criterion (from the
  review, non-negotiable):** a target's AUC may only be reported as
  signal if it clears the proximity floor. If KRAS's 0.779 does not clear
  it, the number is geometry and must be reported as such — do not
  soften this in the implementation or the write-up.
- Planned Validation: the synthetic-globule reproduction check above,
  plus the real three-target re-run with updated `RESULTS.md` entries
  showing pass/fail against the new floor per target.

## Dependency

- Blocks: TASK-0082 (competence map synthesis — floor/ceiling/headroom
  numbers are meaningless until proximity-cleared), TASK-0068 (NISQ noise
  simulation — built on an unconfirmed headline result), TASK-0015
  (holo-direction module), TASK-0046 (ceiling search), TASK-0081
  (generalization set) — all consume or extend the current, provisionally
  confounded headline numbers.
- Blocks TASK-0091 (re-filed below) and TASK-0093 (updated below) — both
  must apply this floor rather than test against chance alone.
- Related: TASK-0058 (`classify_failure`'s existing floor-check
  machinery, Done) — this task extends it, doesn't replace it.

## Open Questions

- None — the two functions and their wiring points are specified exactly
  by the review.

## Done

(not yet)
