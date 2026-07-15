# TASK-0082 Competence map synthesis

## Context

- ID: TASK-0082
- Title: Assemble the per-target floor/ceiling/headroom table into the
  submission's central claim — the honest per-target competence map.
- Status: Done
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 5, item 5.2 —
  "The strategic differentiator. 'We close X% of the gap knowing the
  answer would close, on these targets; ~0 on those, and here is why.' A
  per-target honest NO is a publishable result, not a failure to hide."
  Third link in the critical path (`... → 5.1 → 5.2 → 6.1`).

## Intent Contract

- Outcome: a synthesized table/report, one row per target, showing floor
  score, ceiling score (TASK-0046), actual pipeline score, and headroom
  (how much of the floor-to-ceiling gap the pipeline closes) — with an
  honest narrative for targets where headroom closure is ~0, explaining
  why rather than hiding the result.
- In Scope: consuming TASK-0079's end-to-end run output (all mandatory
  targets), TASK-0080's c-Myc no-ground-truth handling, and TASK-0046's
  ceiling values; producing the synthesized competence map as a document
  or report artifact.
- Out Of Scope: computing the floor/ceiling scores themselves (TASK-0011
  baselines.py, TASK-0046 ceiling search — both inputs, not this task's
  job to (re)implement).
- Acceptance Scenarios:
  - Given TASK-0079's per-target results and TASK-0046's ceiling values,
    when synthesized, then every mandatory target has a stated
    floor/ceiling/actual/headroom row.
  - Given a target where the pipeline's actual score is close to floor
    (near-zero headroom closure), then the synthesis states this
    explicitly with a reason, rather than omitting or burying the target.
- Constraints And Invariants: this is explicitly the "strategic
  differentiator" per the plan — treat honest NOs as first-class content,
  not something to minimize.
- Planned Validation: manual review confirming every mandatory target
  (plus c-Myc's special case) has a row and the low-headroom cases have
  stated reasons.

## Dependency

- Depends on TASK-0079 (end-to-end challenge run), TASK-0080 (c-Myc
  handling), and TASK-0046 (ceiling coordinate-descent search) — all
  three feed this synthesis.
- Feeds TASK-0083 (result artifact contract) and TASK-0085 (frontend
  research visualization, "competence panel: floor / method / ceiling
  bars") — the critical path continues into Phase 6.
- **Added 2026-07-15, `REVIEW-2026-07-15-execution-plan-gap-audit.md`:**
  TASK-0112 (wire `block_bootstrap_ci` into headline AUC reporting) —
  every floor/ceiling/actual number this task synthesizes is currently a
  bare point estimate with no confidence interval. Do not read a
  floor-vs-score margin (e.g. any row where "actual" sits close to
  "floor") as a decided headroom-closure result until TASK-0112 lands;
  report the CI alongside the row instead of a bare number if TASK-0112
  is still open when this task starts.
- **Added 2026-07-15, `REVIEW-2026-07-15b-ceiling-search-methodology.md`:**
  TASK-0046's ceiling column itself has two open follow-ups —
  TASK-0116 (the 60-trial blind random search may be too sparse to
  support "no headroom" as a negative claim) and TASK-0117 (the same
  unvalidated `t_max`/`n_steps` TASK-0108/0109/0110 exist to check).
  If either is still open when this task starts, state the ceiling
  column's caveat explicitly rather than presenting TASK-0046's number
  as final — same posture as the CI caveat above.

## Open Questions

- **Resolved for now**: standalone document, `__WORK_IN_PROGRESS__/COMPETENCE_MAP.md`,
  cross-linked from `RESULTS.md`'s open-questions index (row 9) rather than folded into
  that already-689-line file. Reconcile with whatever artifact shape TASK-0083 eventually
  defines once that task lands (still TODO) — this document's own "Open items" section
  tracks that as unresolved, not silently assumed.

## Done

**Document**: `__WORK_IN_PROGRESS__/COMPETENCE_MAP.md`. One row per mandatory target
(floor/ceiling/actual AUC/diagnosis/headroom) plus c-Myc's dedicated no-ground-truth
row (per [[TASK-0080]]) and a placeholder section for TASK-0081's still-open
generalization set. Computes nothing itself (Out Of Scope) — every number is read from
an already-real run and cited to its source file.

**Ceiling numbers for BCR_ABL1/CARDIAC_MYOSIN, produced as part of assembling this
document** (TASK-0046 itself only cross-checked KRAS_G12C): real, network-gated 60-trial
`ceiling.ceiling_search` runs for both remaining mandatory targets, via a new
checkpointed/resumable runner (`scripts/ceiling_search_batched.py`) built specifically
because a first estimate (extrapolating TASK-0046's real KRAS_G12C wall-clock time,
~44s/trial, by O(N^3) eigendecomposition scaling) put BCR_ABL1 at ~14h and
CARDIAC_MYOSIN at several days — later found to be a large overestimate (this shared
machine was under heavy concurrent-thread CPU load during TASK-0046's original run;
uncontended, both targets' full 60-trial searches completed in under 6 minutes combined,
measured directly, not assumed). The checkpointed runner was kept and used regardless,
per explicit instruction (crash-safety, no accidental recomputation): each trial is
appended to a JSONL checkpoint immediately on completion (success or failure), and a
resumed run fast-forwards the RNG past already-checkpointed trials (verified bit-
identical to a non-batched run of the same seed/trial count, by direct comparison of the
first two trials' sampled parameters before trusting it on real targets). Real results:
BCR_ABL1 ceiling = 0.6118 (60 trials, 15s); CARDIAC_MYOSIN ceiling = 0.8188 (60 trials,
~5.5 min). Both checkpoint files live in `results_task0082/<target>/ceiling_trials.jsonl`.

**Headline finding**: none of the three mandatory targets has a clean, floor-clearing,
resolution-clean, headroom-positive result. KRAS_G12C's ceiling (0.524) is *below* its
own proximity floor (0.798) — the strongest form of negative result this framework can
express, stronger than TASK-0093's already-reported "actual is geometry" finding.
BCR_ABL1's actual result (0.525) sits below its own floor (0.565) though a real
(if modest) ceiling-floor gap exists (0.612 vs 0.565) unclaimed by the shipped
configuration. CARDIAC_MYOSIN's only positive headroom (40.7%) is invalidated by the
pipeline's own `INSUFFICIENT_RESOLUTION` flag before the floor comparison is even
meaningful. Full per-target narrative in the document itself.

**Mid-task discovery, handled per this session's "an implementer surfaces, an
orchestrating thread files" convention**: `headroom = (actual - floor) / (ceiling -
floor)` produces a meaningless negative-denominator fraction for KRAS_G12C when computed
mechanically (ceiling < floor there) — reported as a stated finding in the document
instead of a fraction, per explicit instruction. Filed as a new shared-memory pitfall
(`.ai/memory/shared/pitfalls.md` P-0002) and a question to the Architect
(`.ai/memory/questions/architect-planner/open/Q-0003-...md`) on whether this changes the
floor/ceiling/headroom framing itself for this operator family.

**Discovered mid-task, incorporated before closing**: this task's own Dependency section
was updated the same day (`REVIEW-2026-07-15`/`REVIEW-2026-07-15b`, an independent
Architect/Critic-overlay pass that reached the same ceiling-below-floor finding via a
read-only audit) with two new caveats this document now carries inline, everywhere the
finding is stated: **TASK-0112** (no confidence interval on any number here —
`block_bootstrap_ci` exists, is unused by any headline AUC) and **TASK-0116**/
**TASK-0117** (the ceiling search's 60-trial blind coverage is weak evidence for a
*negative* claim specifically, and shares every other headline AUC's unvalidated
`t_max`/`n_steps`). Per that review's own posture and this task's updated Dependency
section: none of the three retract TASK-0046's number, and this document does not
present it as settled — it states the finding as the strongest currently-gathered
evidence, with the open caveats named at the top of the document and repeated at each
point the finding is used, not buried in one disclaimer paragraph.

**RESULTS.md updated additively**: row 2 of the open-questions index (previously "untested",
stale since TASK-0092 landed) corrected with real findings; new row 9 added citing this
document.

**Acceptance Scenarios**: met — every mandatory target has a stated floor/ceiling/actual/
headroom row (or an explicit reason none applies, c-Myc); every low/negative-headroom
case states why rather than omitting or burying the target.
