# SEAM-0017 A pre-registered criterion's verdict must be reachable given the statistic's own resolution

- units: any pre-registered pass/fail criterion or Bonferroni-style gate
  (producer — a threshold written before data is seen) -> the statistic's
  own actual measurement resolution: `n_reps`/permutation-null replicate
  count, the statistic's numeric range, and the construction's attainable
  sign (consumer — the real computation that must be able to land on either
  side of the threshold)
- invariant: every verdict a criterion can report must be reachable given
  (a) `n_reps` — `alpha/family_size > 1/n_reps`, an unreachable-except-at-
  p=0 bar is not a criterion; and (b) the statistic's own attainable range/
  sign under its construction — a bar demanding a value the statistic
  cannot produce (`rate > 1.0` when the maximum attainable rate is exactly
  `1.0`; `joint < 0` when the construction forces every case positive) is
  not falsifiable in the direction that matters and must report
  `not_evaluable`, not a scored fail
- owner: [[TASK-0189]] (Done) — built the sub-case (a) guard,
  `diagnostics.assert_gate_reachable(alpha, family_size, n_reps)`, raising
  `ValueError` for an unreachable `n_reps`/`alpha` combination; [[TASK-0240]]
  (Done) — built the sub-case (b) guard, `diagnostics.
  assert_criterion_reachable(comparator, threshold, attainable_min,
  attainable_max)`, raising `ValueError` when no value in the statistic's
  own declared attainable range can satisfy the comparator/threshold pair.
  [[TASK-0204]] (its own D1) and [[TASK-0208]] (its own V1) are the two
  real instances that motivated it, explicitly named "same class" as each
  other in TASK-0208's own text.
- seam-test: `tests/test_diagnostics.py::TestAssertGateReachable` covers
  sub-case (a), **VERIFIED**. `tests/test_diagnostics.py::
  TestAssertCriterionReachable` covers sub-case (b) — reconstructs
  TASK-0204's D1 exactly (`opt_rate > 1.0`, attainable range `[0, 1]`,
  raises) and TASK-0208's V1 exactly (`joint < 0`, attainable range
  `[0, inf)` under the construction's own forced-non-negative sign,
  raises), plus the corresponding reachable branches (does not over-fire),
  a strict-vs-inclusive boundary case, and the two caller-error paths
  (invalid range, unsupported comparator) — 7 tests, all passing,
  **VERIFIED**.
- status: **VERIFIED**
- provenance: opened 2026-08-24 by [[TASK-0232]] (Architect/Planner registry
  pass, source: Bartosz, 2026-08-21 — *"So many tests added and no newer
  seams?"*), registered `OPEN` with sub-case (b) named as a gap rather than
  force-closed. Closed 2026-08-24 by [[TASK-0240]]: built the general
  guard, reconstructed both real historical instances (D1, V1) as
  regression tests and confirmed the guard fires on each, confirmed it
  does not over-fire on the corresponding reachable branches. Full suite
  green (1245+7 passed) after landing.
