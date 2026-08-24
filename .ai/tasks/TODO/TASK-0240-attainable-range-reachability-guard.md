# TASK-0240 Generalize the reachability guard to a statistic's own attainable range/sign, not just n_reps/alpha

## Context

- ID: TASK-0240
- Status: TODO
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

- [ ] Design the attainable-range/sign check (function signature, what it
      needs to know about a statistic's construction).
- [ ] Implement + wire it somewhere reachable.
- [ ] Regression tests against D1 and V1's own reconstructed conditions
      (fail-first, then pass).
- [ ] Flip [[SEAM-0017]] to VERIFIED, update its seam-test field.

## Dependency

- [[TASK-0189]] (the sibling guard this generalizes from), [[TASK-0204]],
  [[TASK-0208]] (the two known instances), [[TASK-0232]] (filed this task).

## Done

—
