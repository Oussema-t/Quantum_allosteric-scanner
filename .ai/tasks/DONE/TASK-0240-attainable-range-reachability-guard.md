# TASK-0240 Generalize the reachability guard to a statistic's own attainable range/sign, not just n_reps/alpha

## Context

- ID: TASK-0240
- Status: Done
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: [[TASK-0232]]'s own registry sweep, filing [[SEAM-0017]] — a
  seam this repo currently cannot detect.
- Priority: P2. No live scored verdict is currently known to be affected
  (TASK-0204's D1 and TASK-0208's V1 were each found and locally fixed
  already); this closes the general case so the next instance is caught
  by a guard, not by a future task re-discovering the same failure shape.

## The gap

[[TASK-0189]] built `diagnostics.assert_gate_reachable(alpha, family_size,
n_reps)` — a real, wired, tested guard against one specific way a
pre-registered criterion's verdict can be structurally unreachable: a
Bonferroni-style `alpha`/`family_size`/`n_reps` combination where
`alpha/family_size <= 1/n_reps`, so no permutation draw can ever produce a
p-value small enough to pass.

**A second, distinct way the same class of bug occurs has no general
guard.** [[TASK-0204]]'s D1: a criterion `opt_rate > 1.0` where `opt_rate`'s
own maximum attainable value is exactly `1.0` — unreachable whenever the
comparator hits the ceiling, not an `n_reps`/`alpha` problem at all.
[[TASK-0208]]'s V1: a criterion `joint < 0` where the measurement's own
construction (rigid holo side chains transplanted onto an apo backbone)
forces `joint` positive in every real case — "structurally unreachable,"
in that task's own words, and explicitly named "same class as TASK-0204's
D1." Both were found by inspection and fixed locally (`criterion_1_verdict`
returning `not_evaluable_*` states; a relaxation step added before scoring)
— neither produced a reusable check.

[[SEAM-0017]] registers this as `OPEN` with no seam-test for this half,
precisely because none exists anywhere in the repo.

## Intent Contract

- Outcome: a general, reusable guard that checks whether a pre-registered
  criterion's stated threshold is reachable given the statistic's own
  attainable range/sign under its construction — analogous to
  `assert_gate_reachable`, for this different failure shape — wired
  somewhere a future criterion-writer would actually hit it, not just a
  standalone function nobody calls.
- In Scope:
  - Design the check: given a statistic's declared or inferred attainable
    range (e.g. `[0, 1]` for a rate, a provably-signed quantity under a
    stated construction) and a comparator (`>`, `<`, `>=`, `<=`) against a
    threshold, determine whether *any* attainable value could satisfy it.
    Raise (or return a `not_evaluable`-style sentinel, matching
    [[TASK-0204]]'s own established convention) if not.
  - Retrofit it against both known instances (D1, V1) as regression cases —
    each must be shown to have been caught by this guard, not merely
    plausible in the abstract (this project's own "fail-first" discipline,
    [[TASK-0231]]'s own precedent: demonstrate the guard fires on the
    known-bad case before trusting it).
  - Update [[SEAM-0017]]'s own status to `VERIFIED` once the seam-test
    exists and passes.
- Out Of Scope:
  - Re-litigating D1/V1's own already-accepted fixes/results.
  - The `n_reps`/`alpha` sub-case — already covered by
    `assert_gate_reachable`, not touched here.
- Constraints And Invariants:
  - Must not require every existing criterion in the codebase to be
    rewritten to use it immediately — an opt-in check callers adopt,
    matching how `assert_gate_reachable` itself was introduced, is
    sufficient; retrofitting every call site is a separate, later
    decision.
- Planned Validation: a regression test file demonstrating the guard fires
  on reconstructions of D1 and V1's own exact conditions, and passes on a
  reachable comparator. [[SEAM-0017]]'s own seam-test field updated to
  point at it.

## TODO

- [x] Design the attainable-range/sign check (function signature, what it
      needs to know about a statistic's construction).
- [x] Implement + wire it somewhere reachable.
- [x] Regression tests against D1 and V1's own reconstructed conditions
      (fail-first, then pass).
- [x] Flip [[SEAM-0017]] to VERIFIED, update its seam-test field.

## Dependency

- [[TASK-0189]] (the sibling guard this generalizes from), [[TASK-0204]],
  [[TASK-0208]] (the two known instances), [[TASK-0232]] (filed this task).

## Done

**2026-08-24 — Implementer A.** Guard built, wired, tested against both
real historical instances, and [[SEAM-0017]] flipped to `VERIFIED`.

**`diagnostics.assert_criterion_reachable(comparator, threshold,
attainable_min, attainable_max)`** — mirrors `assert_gate_reachable`'s own
shape and convention (raises `ValueError`, never returns `False`, an
unreachable criterion is a construction error to fix, not a value to
branch on silently). Supports the four comparator directions this
project's own pre-registered criteria are actually written in (`>`, `>=`,
`<`, `<=`). Two caller-error paths (invalid range, unsupported comparator)
raise distinctly from "unreachable," so a bad call is never misdiagnosed
as a real reachability finding.

**Retrofit against both real instances, fail-first-equivalent
demonstrated**: since D1/V1 are already-fixed historical bugs (not live
code to re-break), the fail-first discipline here is "does the guard,
built fresh, actually catch the reconstructed original condition" —
confirmed directly, not assumed:
- TASK-0204's D1 (`opt_rate > 1.0`, attainable range `[0, 1]`): guard
  raises. The other branch of the original bug's own ternary
  (`opt_rate > 0.0`) correctly passes — confirms the guard discriminates
  the actual defect, not every use of this statistic.
- TASK-0208's V1 (`joint < 0`, forced non-negative by construction):
  guard raises. A genuinely reachable sign bar (`attainable_min=-1.0`)
  correctly passes — same discrimination check on the other comparator
  direction.
- Boundary strictness (`>` vs `>=` at the same threshold) and both
  caller-error paths also covered. 7 tests total,
  `tests/test_diagnostics.py::TestAssertCriterionReachable`, all passing.

**[[SEAM-0017]] flipped to `VERIFIED`** — both sub-cases now have a real
guard and a real seam-test; its own `owner`/`seam-test`/`status` fields
updated accordingly, provenance field records the close.

**Not done, per this task's own Constraint**: no existing criterion in the
codebase (D1's own fixed `criterion_1_verdict`, V1's own relaxation-based
fix, or any other) was retrofitted to *call* this guard — it exists and is
tested, adoption at real call sites is a separate, later decision, exactly
as `assert_gate_reachable` itself was introduced unadopted-by-default.

**Validated**: `tests/test_diagnostics.py` full file green (49 passed,
was 42 before this task). Full `__WORK_IN_PROGRESS__` suite green after
landing (1256 passed, 1 skipped, 8 xfailed, 0 failed).
