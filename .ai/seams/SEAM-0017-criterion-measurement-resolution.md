# SEAM-0017 A pre-registered criterion's verdict must be reachable given the statistic's own resolution — partially covered, one sub-case still open

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
- owner: [[TASK-0189]] (Done) — built the general sub-case (a) guard,
  `diagnostics.assert_gate_reachable(alpha, family_size, n_reps)`, raising
  `ValueError` for an unreachable `n_reps`/`alpha` combination; sub-case (b)
  has **no general owner yet** — [[TASK-0204]] (Done, its own D1) and
  [[TASK-0208]] (Done, its own V1) each found and locally fixed one
  instance (`criterion_1_verdict`'s `not_evaluable_greedy_ceiling` state;
  the frustration statistic's own relaxation requirement), explicitly
  named "same class" as each other in TASK-0208's own text, but neither
  built a reusable guard the way TASK-0189 did for sub-case (a). **New
  [[TASK-0240]] filed to own generalizing `assert_gate_reachable` (or a
  sibling function) to also check a statistic's attainable range/sign
  before a criterion is allowed to report a scored fail.**
- seam-test: `tests/test_diagnostics.py::TestAssertGateReachable` covers
  sub-case (a) only, **VERIFIED** for that half. Sub-case (b) has **no
  seam-test** — `tests/test_task0204_criterion.py`'s own regression tests
  (including one that fails against the pre-fix expression for every
  attainable rate) pin D1's *specific instance*, not a reusable
  cross-cutting check; nothing plays that role for V1 or for any future
  instance of this class.
- status: **OPEN**
- provenance: opened 2026-08-24 by [[TASK-0232]] (Architect/Planner registry
  pass, source: Bartosz, 2026-08-21 — *"So many tests added and no newer
  seams?"*). **Explicit tension, recorded rather than silently resolved
  either way**: this task's own Out-of-Scope line ("Writing the tests —
  that is [[TASK-0231]]") and this project's `.ai/seams/README.md` ("a
  seam-test... must exist once a seam is registered, xfail counts") pull in
  opposite directions here — TASK-0231's actual scope (config-level
  breakage, `targets.yaml`/`functional_indices`) never covered this seam's
  own subject (pre-registered statistical-criterion construction), so no
  test for sub-case (b) exists anywhere in the repo. Registered `OPEN`
  with the gap named precisely, per this task's own Planned Validation
  ("confirm a detecting artifact would fire, or name the gap. A seam
  nothing can detect is a note, not a seam.") — filing [[TASK-0240]] rather
  than an Architect/Planner-authored test file, consistent with this
  task's own thread scope (registry hygiene, no compute) and the same
  producer/consumer split every other seam in this registry already uses
  (a finding gets a task; the task builds the guard and its test).
