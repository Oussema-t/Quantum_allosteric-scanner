# TASK-0094 Proximity baselines into the floor — blocks every current headline number

## Context

- ID: TASK-0094
- Title: Add `euclid_from_seed_centroid` and `hop_from_seed` (both negated,
  closer = higher score) to `baselines.py`; wire into `floor_scores` and
  `classify_failure`'s floor; re-run all mandatory targets.
- Status: Done
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

## Done (2026-07-13, Implementer A)

- `baselines.py`: added `euclid_from_seed_centroid(coords, source)` and
  `hop_from_seed(coords, source, cutoff)`, both negated (closer = higher
  score), both accepting this package's standard scalar-or-sequence
  `source` convention. `hop_from_seed`'s BFS ported from (not
  cross-imported — private helper, module-boundary convention) `select.py`
  `_hop_distances_from_source`, adapted to a multi-index seed and to a
  finite `n+1` unreachable-node penalty instead of `-1` (this function has
  no caller that filters unreachable nodes itself, unlike
  `ballistic_exponent`).
- **Acceptance Scenario check (the review's own instruction: verify, don't
  assume correct by construction):** reproduced the review's synthetic-
  globule setup (170 residues, cutoff 8.0 Å, a spatially-contiguous
  6-residue seed, real `build_H_new` + `time_averaged_ctqw`) — not the
  review's exact RNG draw (unspecified), but the same claim, across 5
  independent seeds: `Spearman(CTQW, euclid_from_seed_centroid)` = 0.71–0.83,
  `Spearman(CTQW, hop_from_seed)` = 0.55–0.64. Both strongly positive,
  consistent with (not numerically identical to) the review's own
  +0.853/+0.880. Committed as a permanent regression
  (`tests/test_baselines.py::TestProximityConfoundReproduction`, asserts
  `rho > 0.5`), not left as a one-off scratch check.
- `diagnostics.classify_failure`: `floor_scores` widened to accept either
  a single `(N,)` array (original SEAM-0005 shape, unchanged, tested) or
  several stacked as `(k, N)`/a sequence (TASK-0094) — floor becomes the
  **max** AUC among all candidates, i.e. "beats the single strongest
  trivial baseline", not the first one or an average. This is the actual
  fix: `degree_centrality` alone was never the confounding variable.
- `scripts/run_challenge.py`: floor computation now passes all three
  baselines (`degree_centrality`, `euclid_from_seed_centroid`,
  `hop_from_seed`) as a list to `run_frozen_verdict`'s `floor_scores`.
- **Real three-target re-run** (`results_task0094/`, identical apo data,
  identical AUCs — only the floor changed):

  | Target | AUC | Floor-cleared? | `_diagnosis` |
  |---|---|---|---|
  | KRAS_G12C | 0.779 | **No** (degree 0.482, euclid **0.798**, hop 0.781) | `BEATS_CHANCE_NOT_FLOOR` |
  | BCR_ABL1 | 0.525 | N/A, never clears chance | `NO_SIGNAL_IN_APO` |
  | CARDIAC_MYOSIN | 0.786 | Yes (max floor 0.764) — moot, `INSUFFICIENT_RESOLUTION` fires first (N=950) | `INSUFFICIENT_RESOLUTION` |

  **Hard acceptance criterion enforced, not softened:** KRAS_G12C's 0.779
  — previously reported `NO_FAILURE_DETECTED` against `degree_centrality`
  alone — does **not** clear the real proximity floor and is now reported
  as geometry, exactly as the review's non-negotiable criterion requires.
  **Zero of three mandatory targets currently ship a floor-cleared,
  resolution-clean apo-only AUC.**
- `RESULTS.md`: appended dated 2026-07-13 amendments to the KRAS_G12C,
  BCR_ABL1, and CARDIAC_MYOSIN sections (per that document's own "append,
  don't overwrite" convention — original numbers/prose from the
  2026-07-12 run left intact), a new "Proximity floor applied" summary
  subsection, and two new/updated rows in the open-questions index.
  Written carefully around a concurrent thread's TASK-0095 edits to the
  same file (propagator-rename corrections) — read the file fresh
  immediately before each edit rather than assuming my last read was
  current, per that thread's own tool-reported "modified on disk since
  last read" notice.
- Tests: `tests/test_baselines.py` (+13: 6 hand-computed/edge-case unit
  tests for the two new functions, 1 real-globule reproduction check,
  matching the file's existing `_chain_coords` hand-computable style),
  `tests/test_diagnostics.py` (+4: multi-floor `classify_failure` cases,
  including explicit backward-compatibility with the pre-existing
  single-array shape). Full suite: 458 passed (up from prior baseline),
  no regressions, before the concurrent TASK-0095 landing; re-verified
  green after it landed (see task file's own commit for the exact count).
- **Downstream consequence, not softened:** this confirms TASK-0094's own
  Dependency section — TASK-0082/0068/0015/0046/0081 were all consuming a
  provisionally-confounded headline number and remain blocked until a
  method actually clears this floor.
