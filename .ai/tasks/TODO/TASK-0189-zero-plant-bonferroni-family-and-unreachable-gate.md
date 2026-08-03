# TASK-0189 `zero_plant_specificity.py` reintroduced TASK-0167.002's own Bonferroni-family bug, under a gate that cannot fire

## Context

- ID: TASK-0189
- Title: fix the Bonferroni family size and the structurally-unreachable
  certification gate in [[TASK-0167.003]]'s collection script, and re-derive
  Part A's measured false-positive rates from the stored raw p-values.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: Reviewer thread, 2026-08-03, finding F1 (read from code, not prose).
- Priority: **P0 — [[TASK-0167.003]]'s Part A table is the evidence cited for
  "the compact and Rg-matched nulls show no anti-conservative bias anywhere,"
  which is in turn the basis for treating [[TASK-0158]]'s null as settled.
  That table does not measure what it says it measures.**
- Dependency: none (the expensive collection pass already ran; its raw
  `p_value` fields are stored).

## Why this matters

Two defects, compounding, in the same line:

`scripts/zero_plant_specificity.py:154`

```python
bonferroni_alpha = ALPHA / (len(STRENGTHS) * N_SEEDS)  # same family bar .002 uses
```

**Defect 1 — the comment is false, and names the exact bug it reintroduces.**
`0.05 / (8 * 20)` = `3.125e-4`. [[TASK-0167.002]] identified this precise
denominator as a real bug and corrected it: `scripts/detection_curve_analysis.py:36`
sets `REAL_DEPLOYMENT_BONFERRONI_FAMILY = 3` (α = 0.0167), with a header note
explaining that a real deployment corrects across **targets**
([[TASK-0145]]'s convention), never across a measurement device's own internal
replicate grid. `.002`'s *collection* script kept the wrong constant and its
*analysis* script fixed it. `.003`, filed three days later, copied the
collection script's constant and wrote **no** analysis-stage correction — so
the bug reaches `.003`'s published numbers, which `.002`'s never did.

**Defect 2 — at that α the gate cannot fire.** `p_value` is
`(null_maxes >= real_max).mean()` over `N_PERM_REPS = 1000` reps
(`MATCHED_N_PERM_REPS = 200` for the matched null). The smallest non-zero
p-value is therefore `1e-3` (or `5e-3`), both **larger** than the `3.125e-4`
bar. `gate4` can only pass when `p_value == 0.0` exactly.

**Consequence.** Part A is reported as a measured false-positive rate
"against a 5% nominal bar." It is not. It measures certification under a bar
~53× stricter than intended *and* unreachable except at p = 0. The
compact/matched α̂ ≤ 0.2% figures are close to guaranteed by construction and
cannot distinguish a correctly-calibrated null from an over-conservative one —
which is exactly the distinction the task was filed to settle. BCR_ABL1's
scattered 18.8% survives *a fortiori* (94/500 patches beat all 1000 draws — a
stronger statement than reported), but the "~3.8× inflation vs. 5% nominal"
arithmetic is not what the code computed.

This is the same failure class the project already names elsewhere: a
correction landed in one place and the next thread re-derived from the
uncorrected upstream. It was not caught by tests because no test asserts that
the certification bar is reachable given `N_PERM_REPS`.

## Intent Contract

- Outcome: a corrected Part A table — measured α̂ per target per null spec at
  a **stated, reachable** α — replacing the current one in
  `.ai/tasks/DONE/TASK-0167.003-*.md`, with the superseded table kept per this
  project's no-silent-overwrite convention; plus a permanent guard that makes
  an unreachable gate a test failure rather than a silent one.
- Why required, not assumed: the current numbers are not wrong in a way that
  changes their sign — they are wrong in a way that makes them **uninformative
  for their stated purpose**, while reading as decisive. That is the more
  dangerous failure.
- In Scope:
  - Recompute Part A from `results_task0167003_specificity/zero_plant_specificity_full.json`'s
    stored raw `p_value` fields at `α/3` (matching `.002`'s corrected
    convention), in a **separate analysis script**, not by editing the
    collection script's already-run output — the exact shape `.002` used.
  - Raise `N_PERM_REPS`/`MATCHED_N_PERM_REPS` so the reachable-p floor is at
    least an order of magnitude below the corrected α, and re-run collection
    **only if** step 1 shows the reachability floor still binds at α/3
    (1e-3 < 0.0167, so it likely does not — check before spending the compute).
  - Add an assertion/regression test: for any (α, family size, `n_reps`)
    triple used by a certification gate, `1/n_reps < alpha/family` must hold.
    This is the guard that would have caught it.
  - Fix the misleading comment on `:154` so it no longer asserts agreement
    with `.002`.
- Out Of Scope:
  - Re-running the 500-patch × 3-target collection pass unless step 1 proves
    it necessary. Only the denominator was wrong, not the p-values.
  - Re-opening [[TASK-0167.002]]'s LOD table — its published numbers already
    use the corrected α and are unaffected.
  - Any change to `nulls.py` itself. That is [[TASK-0190]]'s territory.
- Constraints And Invariants:
  - Do not silently overwrite the current Part A table. Mark it superseded,
    dated, with the reason, per this project's own convention.
  - State plainly whether the corrected numbers change `.003`'s verdict
    sentence. If they do not, say so — a null-effect correction is still worth
    landing, and reporting it as one is the honest outcome.
- Planned Validation:
  - Recomputed BCR_ABL1 scattered α̂ must remain materially above nominal —
    if the correction erases the one real finding in Part A, that is itself a
    result and must be reported, not smoothed.
  - The new reachability test must fail against the current constants
    (demonstrate it, don't assert it) before it passes against the fixed ones.

## In Progress

—

## TODO

- [ ] Recompute Part A at α/3 from stored raw p-values; produce the corrected table.
- [ ] Check reachability at the corrected α; re-run collection only if it still binds.
- [ ] Add the (α, family, `n_reps`) reachability guard + a failing-first test.
- [ ] Fix the `:154` comment.
- [ ] Update `.ai/tasks/DONE/TASK-0167.003-*.md` Part A (superseded-not-overwritten).
- [ ] Feed the corrected verdict sentence to [[TASK-0191]] for the `RESULTS.md` section.

## Dependency

- [[TASK-0167.002]] (Done) — the corrected convention this task restores.
- [[TASK-0167.003]] (Done) — the table being corrected.
- [[TASK-0191]] — consumes this task's corrected verdict sentence.

## Open Questions

- Does any *other* script in `scripts/` carry the `ALPHA / (len(STRENGTHS) *
  N_SEEDS)` pattern, or a certification gate whose α sits below its own
  `1/n_reps` floor? Grep before closing — the reachability guard is only
  worth building if it is applied register-wide.
- Should the reachability check live in `diagnostics.py` (next to
  `classify_failure`) rather than in a test, so every future gate inherits it?

## Done

—
