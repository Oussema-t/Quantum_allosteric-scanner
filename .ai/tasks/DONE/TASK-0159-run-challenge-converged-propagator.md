# TASK-0159 Re-point `run_challenge.py` at the converged closed-form propagator

## Context

- ID: TASK-0159
- Title: `PANEL_REVIEW_2026-07-25.md` W2 — the shipped end-to-end
  pipeline (`scripts/run_challenge.py`) still hardcodes `T_MAX = 15.0`,
  `N_STEPS = 500` (lines 100–101) and calls `time_averaged_ctqw`, not
  `time_averaged_ctqw_converged` ([[TASK-0130]]'s exact, phase-free,
  infinite-time closed form). [[TASK-0110]]'s own Optuna scan already
  documented this finite-time truncation as 145,000×–3,950,000× too
  short, and [[TASK-0146]] (per the review) showed it flips KRAS's own
  floor-clearing verdict. Every corrected headline number in
  `RESULTS.md` lives in a standalone script that "does not touch live
  pipeline defaults" — meaning the artifact a judge would actually
  receive from running the shipped pipeline is generated under a
  convention the project's own analysis has already shown to be wrong.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer B (this thread)
- Claimed At: 2026-07-25 10:20
- Source: `PANEL_REVIEW_2026-07-25.md` §2.2/W2, §4 action item 2.
- Priority: **P0** — deliverable/science coherence; the review's own
  estimate is ½ day, and it is a prerequisite for the artifacts a judge
  sees matching what the 6-pager claims.

## Intent Contract

- Outcome: `run_challenge.py`'s scoring call site swaps
  `time_averaged_ctqw(H, source, t_max=T_MAX, n_steps=N_STEPS)` for
  `time_averaged_ctqw_converged(H, source)` ([[TASK-0130]]'s closed
  form); the `T_MAX`/`N_STEPS` module constants are deleted, not left
  as dead code.
- Why required: the live pipeline must compute the same quantity the
  project's own corrected science reports — otherwise the shipped
  `verdict.json`/hit-lists a judge would generate do not match the
  6-pager's own claimed numbers.
- In Scope:
  - The single call site (and any other live caller of the finite-time
    `time_averaged_ctqw` still using `T_MAX`/`N_STEPS` — grep to confirm
    there is only the one, don't assume).
  - Re-run all 3 mandatory targets + the generalization set
    (PTP1B/CASPASE7) through the corrected pipeline; confirm the
    verdicts match the already-reported converged-limit numbers
    elsewhere in `RESULTS.md` (a cross-check, not a re-derivation — if
    they disagree, that is itself a real finding to report, matching
    this project's own established convention, e.g. TASK-0150's own
    cross-check discipline).
- Out Of Scope:
  - Any change to `time_averaged_ctqw`/`time_averaged_ctqw_converged`
    themselves — both already correct, reuse as-is.
  - Standalone analysis scripts that already use the converged form
    correctly — this task is about the *live* pipeline only.
- Constraints And Invariants: must not change any existing
  `test_run_challenge.py` test's expected output beyond what the
  propagator swap itself requires — flag any test that needs updating
  explicitly, don't silently adjust an assertion to make it pass.
- Planned Validation: 3-mandatory-target + 2-generalization-target
  re-run; cross-check against `RESULTS.md`'s own already-reported
  converged-limit numbers; full regression suite re-run.

## TODO

- [x] Grep confirm the exact scope of live callers using the finite-time
      form with `T_MAX`/`N_STEPS`.
- [x] Swap to `time_averaged_ctqw_converged`; delete the two constants.
- [x] Re-run all 3 mandatory + PTP1B/CASPASE7; cross-check against
      already-reported converged numbers.
- [x] Update/confirm `test_run_challenge.py`.
- [x] `RESULTS.md`/`EXECUTION_PLAN.md` note: shipped pipeline now matches
      reported science, dated.

## Dependency

- [[TASK-0130]] (Done) — the converged closed form being wired in.
- [[TASK-0110]] (Done) — the original finding this task acts on.

## Open Questions

- None — the fix is a direct function swap; scope confirmed by the
  review's own line-number citation.
  **Confirmed at pickup, and found to be wrong**: re-grepping the full
  repo found `T_MAX`/`N_STEPS` used at 4 real call sites inside
  `run_challenge.py` itself (candidate-selection dict entries,
  `consensus_ranking`, `run_frozen_verdict`, the winner's own
  `time_averaged_ctqw` call), not a single one — see Done section for
  how each was resolved.

## Done

**2026-07-26, Implementer B.** Fixed as scoped, plus a direct numerical
validation of the closed form itself, run at explicit user request
beyond this task's own original Planned Validation.

**Fix** (`scripts/run_challenge.py`): `run_frozen_verdict(...,
use_converged_limit=True)` — already-existing TASK-0130 machinery on
`benchmark`/`quantum_vs_classical`, never previously wired up at this
call site — now drives every reported AUC (`AUC_apo_Hnew_optimised`,
`AUC_apo_Hnew_default`, `AUC_apo_H10_baseline`) via the converged form.
The winner's own occupation (`hit_list.json`'s actual source) swapped
directly: `time_averaged_ctqw_converged(winner_H, source=source,
coherent=False)`. Old `T_MAX=15.0`/`N_STEPS=500` module constants
deleted per the Intent Contract's own explicit requirement; a renamed,
narrowly-scoped pair (`SELECTION_GSR_ABLATION_T`/`_N_STEPS`) remains for
3 uses this task deliberately does not touch, each with a stated reason:
`select_frozen_config`'s own blind candidate-ranking heuristic
(TASK-0118's own established, deliberately untouched scope boundary),
`ground_state_relaxation`'s single-snapshot relaxation time (an
unrelated convergence criterion, still finite by design), and
`ablation()`'s per-term diagnostic (`most_impactful_term` -- a mechanism
finding, not a scored AUC; `ablation()` has no `use_converged_limit`
knob and never feeds a floor-clearing verdict, so extending it is a
real, separate follow-up, not done here). `consensus_ranking`
(TASK-0080's c-Myc/no-ground-truth branch) keeps the old finite-time
convention too, for the same no-AUC-to-flip reason.
`test_run_challenge.py`'s 12 existing tests pass unmodified (synthetic/
mocked, no exact-AUC assertions).

**Real scale check, all 5 targets touched, not just cited**: AAKV
`t_max*` (`min_adequate_t_max`, `tol=1e-2`) vs. the shipped `t_max=15`
-- KRAS_G12C 83,834x, BCR_ABL1 119,323x, CARDIAC_MYOSIN 420,682x, PTP1B
104,147x, CASPASE7 408,565x. Confirms and extends TASK-0110's own
3-target range.

**Real-target re-run, corrected pipeline**: KRAS_G12C 0.5901
(`NO_FAILURE_DETECTED`), BCR_ABL1 0.5266 (`NO_SIGNAL_IN_APO`),
CARDIAC_MYOSIN 0.5176 (`NO_SIGNAL_IN_APO`), PTP1B 0.4859
(`NO_SIGNAL_IN_APO`), CASPASE7 0.5938 (`BEATS_CHANCE_NOT_FLOOR`). Cross-
checked against `RESULTS.md`'s own already-reported converged-limit
numbers: KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN match TASK-0113's own
TASK-0130 cross-validation exactly. **PTP1B disagrees with the ASD
generalization set's own row (0.2050) -- confirmed directly (not
assumed) to be a finite-time-vs-converged discrepancy**: re-running
PTP1B's own `H_new`/ctqw at the literal old `t_max=15, n_steps=500`
reproduces 0.2050 exactly. That table predates or is same-day as
TASK-0130 and never claims the converged form. **PTP1B's verdict flips
from `BEATS_CHANCE_NOT_FLOOR` to `NO_SIGNAL_IN_APO`** under the
corrected convention -- flagged in `RESULTS.md`'s own ASD-generalization-
set section with a dated, additive note (row kept, not deleted, per this
project's own no-overwrite convention), not silently absorbed.
CASPASE7's own diagnosis category is unchanged (`BEATS_CHANCE_NOT_FLOOR`
both ways) though the AUC value itself differs (0.6463 old finite-time
vs 0.5938 converged) -- reported, not flagged as a verdict change since
the category didn't move.

**Direct numerical validation of the closed form itself** (per explicit
user request, beyond this task's own original scope): a genuine
brute-force `time_averaged_ctqw` integration run all the way to each
target's own real AAKV `t_max*` above (877K-4.6M explicit steps, up to
12.3 wall-hours for CARDIAC_MYOSIN), new `scripts/task0159_finite_time_
convergence_check.py` (reuses `propagators._ctqw_mixture_from_eigh`
directly, `runlog.RunLogger`-instrumented per `LONG_JOB_CONVENTION.md`),
compared directly against `time_averaged_ctqw_converged` on the
identical `H`:

| Target | Finite-run AUC | Converged AUC | Max \|occ diff\| | Wall time |
|---|---|---|---|---|
| KRAS_G12C | 0.5901 | 0.5901 | 1.9e-6 | 0.28h |
| BCR_ABL1 | 0.5266 | 0.5266 | 3.7e-6 | 2.93h |
| CARDIAC_MYOSIN | 0.5176 | 0.5176 | 3.7e-7 | 12.33h |
| PTP1B | 0.4859 | 0.4859 | 6.6e-7 | 0.17h |
| CASPASE7 | 0.5938 | 0.5938 | 7.0e-7 | 1.16h |

Every target agrees to 1e-6 to 1e-7 -- floating-point noise, confirming
the closed form exactly, not approximately, on real protein data.

**Two real process failures during this validation, both instructive**:
(1) the first attempt launched all 5 targets as harness-tracked
background jobs -- all 5 were killed simultaneously (~15-18min in,
0/5 complete) when the controlling session process exited, a live
demonstration of `LONG_JOB_CONVENTION.md`'s own explicit warning that
this detachment mechanism does not survive session teardown; (2) that
same first attempt also ran all 5 in full parallel, causing a real
5-26x throughput slowdown from resource contention (worst on the two
largest targets -- CARDIAC_MYOSIN measured at 22 steps/s contended vs.
~2035 steps/s solo). Re-launched OS-detached (`nohup`/`disown`) and
strictly sequentially for the second, successful attempt.

**Full test suite**: 950 passed, 2 xfailed, 0 failed.

Full detail: `RESULTS.md`'s "Re-pointing the shipped pipeline at the
converged closed-form propagator" section, open-questions row 39;
`RESULTS/results_task0159_finite_time_convergence/*.json`.
