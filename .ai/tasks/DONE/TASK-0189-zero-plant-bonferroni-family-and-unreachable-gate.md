# TASK-0189 `zero_plant_specificity.py` reintroduced TASK-0167.002's own Bonferroni-family bug, under a gate that cannot fire

## Context

- ID: TASK-0189
- Title: fix the Bonferroni family size and the structurally-unreachable
  certification gate in [[TASK-0167.003]]'s collection script, and re-derive
  Part A's measured false-positive rates from the stored raw p-values.
- Status: Done
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
  - Recompute Part A from `results/tasks/0167003_specificity/zero_plant_specificity_full.json`'s
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

- [x] Recompute Part A at α/3 from stored raw p-values; produce the corrected table
  (`scripts/zero_plant_specificity_analysis.py`).
- [x] Check reachability at the corrected α; re-run collection only if it still binds —
  it does not (see Done section): no re-run.
- [x] Add the (α, family, `n_reps`) reachability guard + a failing-first test
  (`diagnostics.assert_gate_reachable`, `tests/test_diagnostics.py::TestAssertGateReachable`).
- [x] Fix the `:154` comment.
- [x] Update `.ai/tasks/DONE/TASK-0167.003-*.md` Part A (superseded-not-overwritten,
  `<details>` block + dated note; also flagged the Concordance section's now-stale
  "0.188" citation without recomputing it in full).
- [x] Feed the corrected verdict sentence to [[TASK-0191]] for the `RESULTS.md` section
  (see Done section below — quotable as-is).

## Dependency

- [[TASK-0167.002]] (Done) — the corrected convention this task restores.
- [[TASK-0167.003]] (Done) — the table being corrected.
- [[TASK-0191]] — consumes this task's corrected verdict sentence.

## Open Questions

- Does any *other* script in `scripts/` carry the `ALPHA / (len(STRENGTHS) *
  N_SEEDS)` pattern, or a certification gate whose α sits below its own
  `1/n_reps` floor? **Answered**: grepped every `bonferroni`/`BONFERRONI`
  site in `scripts/*.py`. `positive_control_detection_curve.py:236` (`.002`'s
  own collection script) has the exact same pattern — but `.002`'s own
  `detection_curve_analysis.py` already recomputes at the corrected family
  (confirmed by reading it directly, this task's own model). Every other
  Bonferroni family in the register (`dephasing_discrimination_sweep.py`,
  `ensemble_entropy_real_run.py`, `entanglement_entropy_real_run.py`,
  `spectral_coherence_real_run.py`, `transport_observable_real_run.py`,
  `generalization_check_transport_lowmode.py`) already uses
  `N_TARGETS_FOR_BONFERRONI = len(TARGETS)` (TASK-0145's own correct
  convention) — `zero_plant_specificity.py` was the only *uncorrected*
  instance found. The guard is general-purpose (`diagnostics.
  assert_gate_reachable`) and available register-wide going forward; not
  retrofitted onto the already-correct scripts above (no bug there to fix).
- Should the reachability check live in `diagnostics.py` (next to
  `classify_failure`) rather than in a test, so every future gate inherits
  it? **Answered: yes** — landed as `diagnostics.assert_gate_reachable`,
  a reusable, importable guard (not just a test-only assertion), wired into
  `zero_plant_specificity_analysis.py`'s own reachability check as a live
  caller, not only demonstrated in isolation.

## Done

**2026-08-03, Implementer A.**

**Corrected Part A table** (`scripts/zero_plant_specificity_analysis.py`,
output `results/tasks/0167003_specificity/part_a_corrected.json`), recomputed
at `REAL_BONFERRONI_ALPHA = 0.05/3 = 0.01667` (TASK-0145's own "correct
across targets, not a measurement device's internal replicate grid"
convention, matching [[TASK-0167.002]]'s own `detection_curve_analysis.py`
exactly) from the already-stored raw `p_value` fields — no collection
re-run:

| Target | Scattered α̂ (95% CI) | Compact α̂ (95% CI) | Matched α̂ (95% CI) |
|---|---|---|---|
| KRAS_G12C | 0.000 [0.000, 0.007] | 0.000 [0.000, 0.007] | 0.000 [0.000, 0.007] |
| BCR_ABL1 | **0.230** [0.194, 0.269] | 0.000 [0.000, 0.007] | **0.034** [0.020, 0.054] |
| CARDIAC_MYOSIN | 0.030 [0.017, 0.049] | 0.000 [0.000, 0.007] | 0.000 [0.000, 0.007] |

**Reachability confirmed before trusting these numbers** (not assumed):
`assert_gate_reachable(0.01667, family_size=3, n_reps=1000)` and
`n_reps=200` (the matched null's own reduced replicate count) both return
`True` — `1e-3` and `5e-3` are comfortably below `0.01667`. Collection
re-run was therefore unnecessary, confirmed rather than skipped by default,
per this task's own Planned Validation.

**Verdict sentence (for [[TASK-0191]]'s `RESULTS.md` section, quotable
as-is):** *"[[TASK-0167.003]]'s Part A table was certified under an
unreachable Bonferroni bar (family=160 instead of TASK-0145's own
across-targets family=3, and below the smallest p-value 1000 permutation
replicates can produce) — corrected here from the same stored p-values, no
re-run needed. The qualitative verdict is unchanged: the compact null
remains uniformly non-anti-conservative (α̂=0.000 on all 3 targets,
unchanged), and the scattered null's BCR_ABL1 anti-conservatism is
confirmed, not weakened (18.8% -> 23.0%, if anything a stronger finding).
What changes is the matched null's own previously-reported '≤0.2% on every
cell' claim -- BCR_ABL1's corrected matched α̂ is 3.4% (was an artificially
tiny, gate-truncated 0.2%), still comfortably below the 5% nominal bar and
still not anti-conservative, but a materially different number than
originally published, now real and reachable rather than a gate artifact."*

**Root cause + fix**: `scripts/zero_plant_specificity.py:154`'s
`bonferroni_alpha = ALPHA / (len(STRENGTHS) * N_SEEDS)` is `.002`'s own
collection-script constant (`positive_control_detection_curve.py:236`),
copied into `.003` without `.002`'s own matching analysis-stage correction
— comment fixed in place (no longer claims agreement with `.002`; explains
the defect and points to the corrected analysis script) rather than
changing the already-run collection script's own stored output.

**Reachability guard**: `allostery.diagnostics.assert_gate_reachable(alpha,
family_size, n_reps)` — raises `ValueError` if `alpha/family_size <=
1/n_reps` (an unreachable gate), returns `True` otherwise. Demonstrated
failing-first against the actual bug (`alpha=0.05, family=160,
n_reps=1000/200` — both raise) before confirming it passes against the
corrected constants (`tests/test_diagnostics.py::TestAssertGateReachable`,
4 tests). Wired as a live caller in `zero_plant_specificity_analysis.py`,
not just demonstrated in a test.

**Register-wide grep** (Open Questions, answered above): only this task's
own script had the uncorrected pattern; every other Bonferroni family in
`scripts/` already uses TASK-0145's correct convention.

**Out of scope, confirmed unnecessary**: no re-run of the 500-patch x
3-target collection pass (reachability holds at the corrected alpha); no
change to `nulls.py` (TASK-0190's territory); TASK-0167.002's own LOD table
untouched (already used the corrected alpha).

**Tests**: `tests/test_diagnostics.py` (+4, `TestAssertGateReachable`). Full
suite: `.venv/bin/python3 -m pytest -q tests/` — pass, no regressions.

**Not done in this task** (explicitly out of scope): writing the actual
`RESULTS.md` section — [[TASK-0191]] owns recovering that section (its own
F3 finding: the section was written but never committed) and will fold this
task's corrected numbers in directly, per this task's own Dependency note
("soft — its corrected Part A numbers should land in the recovered section
rather than requiring a second edit").
—
