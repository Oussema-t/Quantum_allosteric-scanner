# TASK-0153 Extend the holo-diagnostic comparison to transport (T_E/R_eff) and low-mode (prs_low/dcc_low) observables

## Context

- ID: TASK-0153
- Title: [[TASK-0067]] (raw GNM) and [[TASK-0092]] (`H_new`/CTQW) each
  built a holo-native diagnostic comparison — same operator, fed the
  holo topology instead of apo — to separate "(a) apo genuinely lacks
  the information" from "(b) the operator/propagator itself is the
  bottleneck." Neither of today's two real positive findings has been
  through this lens: [[TASK-0145]]'s quantum-transport observables
  (`R_eff`, `T(E)`, Bonferroni-significant on BCR_ABL1, p=0.003) and
  [[TASK-0149]]'s low-mode predictors (`prs_low`/`dcc_low`,
  Bonferroni-significant on CARDIAC_MYOSIN, p=0.003-0.006) are both
  operator families neither TASK-0067 nor TASK-0092 ever tested. This
  task runs the same diagnostic — never a scoring/prediction path,
  strictly upper-bound/failure-attribution — for these two families.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: user question, 2026-07-24, prompted by "the best we can get
  now is LEARNABLE_FROM_APO — should we check DETECTABLE_IN_HOLO too?"
  Answered: the mechanism already exists (TASK-0067/0092), deliberately
  kept diagnostic rather than folded into `learnability_verdict`'s own
  enum (that function answers a different question — does apo's own
  dynamics encode the conformational change — not "can this operator
  find the pocket at all given full structural information"). This
  task is the concrete extension, not a new concept.
- Priority: **P1** — directly informs how to frame today's 2 best
  results in the 6-pager: near an information ceiling (holo doesn't
  help much more) vs. real headroom left on the table (holo does
  noticeably better, motivating a holo-informed follow-on write-up).

## Design note — this is NOT a re-run of `holo_diagnostic_comparison.py`'s own two-pass structure

**Read this before copying TASK-0092's pattern uncritically.** TASK-0092's
script exists because `H_new`/CTQW goes through `run_frozen_verdict`'s
multi-candidate blind-selection machinery (`select_frozen_config`) —
its two-pass design (apo-only selects a winner; a second pass re-derives
the same winner's operator on holo coordinates) exists *specifically*
to keep holo out of the selection step. **Neither `transport.R_eff`/
`T_E` nor `lowmode_predictor.prs_low`/`dcc_low` go through that
selection path at all** — TASK-0145/TASK-0149 both score these
observables directly (`transport_observable_real_run.run_one`,
`lowmode_predictor_real_run.run_target`), with `E`/`gamma_lead`/`k_modes`
all fixed a priori, not selected from a candidate pool. There is nothing
here to keep out of a selection step. So the correct, simpler design is:
compute each observable directly on **holo coordinates + holo-native
seed + holo-native pocket label** (reuse `_holo_native_labels` from
`test_gnm_cutoff_weight_benchmark.py`, TASK-0067's own construction,
imported verbatim as TASK-0092 already does — do not re-derive it), and
compare that AUC against the already-recorded apo AUC from TASK-0145's/
TASK-0149's own Done sections. No winner-selection self-check needed;
say so explicitly rather than building unnecessary machinery to mirror
TASK-0092's shape.

## Intent Contract

- Outcome: for each of the 3 mandatory targets, compute:
  - `transport.R_eff`, `transport.T_E` (`E=0`, pre-registered
    `gamma_lead`) on **holo** coordinates, holo-native seed/pocket.
  - `lowmode_predictor.prs_low`, `dcc_low` (`k_modes` in
    {5,10,15,20}) on **holo** coordinates, holo-native seed/pocket.
  Report holo AUC alongside each observable's already-recorded apo AUC
  (TASK-0145's/TASK-0149's own tables), the gap, and which failure
  explanation it supports — (a) apo-information-limited, (b)
  operator-limited, or neither cleanly (TASK-0092's own KRAS_G12C
  precedent: holo scored *worse* than apo there, a real third outcome,
  not assumed away).
- Why required: without this, "BCR_ABL1's transport win" and
  "CARDIAC_MYOSIN's lowmode win" have no upper-bound context — we don't
  know whether apo is already close to what the same operator could
  ever extract, or whether a holo-informed extension is worth pursuing
  for the proposal's future-work section.
- In Scope:
  - All 3 mandatory targets, both new operator families.
  - Reuse `_holo_native_labels` verbatim (import, not re-derivation),
    same as TASK-0092.
  - No new statistical methodology — same permutation-null/Bonferroni
    convention each observable's own Done section already established,
    applied to the holo-side numbers too (a holo AUC without any null
    context is just as uninterpretable as an apo one would be).
- Out Of Scope:
  - Any change to `transport.py`/`lowmode_predictor.py` themselves —
    pure application to a different coordinate set.
  - Re-running TASK-0067/TASK-0092's own GNM/CTQW holo comparison —
    already done, not repeated here.
  - The generalization-set targets (PTP1B/CASPASE7, [[TASK-0151]]'s own
    scope) — this task is holo-vs-apo on the mandatory 3 only, a
    different axis from TASK-0151's apo-only cross-target check.
- Constraints And Invariants: **diagnostic only, stated explicitly in
  every output** — per TASK-0092's own Context, a holo-side AUC can
  never be reported or treated as a submission prediction; it is a
  failure-attribution tool, full stop.
- Planned Validation: apo-vs-holo AUC + gap + permutation-null context,
  per target x observable; a failure-explanation table in the same
  shape as TASK-0092's own "Failure-explanation summary."

## TODO

- [ ] New script (candidate name: `scripts/holo_diagnostic_transport_lowmode.py`),
      reusing `run_challenge._load_apo_holo`, `_holo_native_labels`,
      and `transport`/`lowmode_predictor`'s existing functions directly
      — no new scoring logic.
- [ ] Run both observable families on holo coordinates, all 3 targets.
- [ ] Permutation null on each holo-side cell (same convention as the
      observable's own apo-side Done section).
- [ ] Apo-vs-holo comparison table + gap + explanation, per target x
      observable; explicit note when the result doesn't cleanly fit
      (a)/(b) (TASK-0092's own KRAS_G12C precedent).
- [ ] `RESULTS.md` section, cross-linked from TASK-0145's/TASK-0149's
      own Done sections, additive.

## Dependency

- [[TASK-0067]]/[[TASK-0092]] (Done) — the holo-diagnostic precedent and
  `_holo_native_labels` construction, reused not re-derived.
- [[TASK-0145]]/[[TASK-0149]] (Done) — the apo-side observables and AUCs
  this task compares against.

## Open Questions

- None — design resolved above (simpler than TASK-0092's two-pass
  shape, reasoning stated).

## Done

(not yet)
