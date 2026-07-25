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
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
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

- [ ] Grep confirm the exact scope of live callers using the finite-time
      form with `T_MAX`/`N_STEPS`.
- [ ] Swap to `time_averaged_ctqw_converged`; delete the two constants.
- [ ] Re-run all 3 mandatory + PTP1B/CASPASE7; cross-check against
      already-reported converged numbers.
- [ ] Update/confirm `test_run_challenge.py`.
- [ ] `RESULTS.md`/`EXECUTION_PLAN.md` note: shipped pipeline now matches
      reported science, dated.

## Dependency

- [[TASK-0130]] (Done) — the converged closed form being wired in.
- [[TASK-0110]] (Done) — the original finding this task acts on.

## Open Questions

- None — the fix is a direct function swap; scope confirmed by the
  review's own line-number citation.

## Done

(not yet)
