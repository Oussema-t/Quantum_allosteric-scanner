# TASK-0151 Generalization-set check for TASK-0145/TASK-0149's positive findings (TASK-0115 Rule #6)

## Context

- ID: TASK-0151
- Title: [[TASK-0145]] (quantum transport / effective conductance) found a
  Bonferroni-surviving positive on BCR_ABL1 (`T(E=0)` on the bare
  Laplacian, p=0.003) and [[TASK-0149]] (low-mode PRS/DCC) found a
  Bonferroni-surviving positive on CARDIAC_MYOSIN (`prs_low`/`dcc_low`,
  p=0.003-0.006) — the two strongest positive results in the project to
  date, both found 2026-07-24. Per [[TASK-0115]]'s own new Rule #6
  (`INVARIANCE_PROTOCOL.md`, "repeated-exposure risk"), **no claim about
  robustness/generalizability is submission-final without being checked
  against [[TASK-0081]]/[[TASK-0127]]'s generalization set** — neither
  finding has been checked there yet.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: this Architect/Planner thread, 2026-07-24, applying TASK-0115's
  own rule to the two findings that landed the same day it was written —
  found while verifying current status for a top-10 refresh, not from an
  external review batch.
- Priority: **P1** — the highest-value use of implementer time right
  now is testing whether the project's two best results are real
  effects or artifacts of the same 3-target repeated-exposure risk
  TASK-0115 was written to name.

## Intent Contract

- Outcome: run both observables — `transport.R_eff`/`transport.T_E`
  ([[TASK-0145]]) and `lowmode_predictor.prs_low`/`dcc_low`
  ([[TASK-0149]]) — against the two currently-working generalization
  targets, **PTP1B and CASPASE7** (the only 2 of the 4 named in
  [[TASK-0081]]/[[TASK-0127]] with a resolved, runnable config;
  GLUCOKINASE is blocked on an open chain-schema question, see
  [[TASK-0081]]'s own Done section — do not attempt it here, that's a
  separate schema-level call already raised to Code Reviewer).
  Use the exact same parameters, cutoffs, and evaluation lens
  (TASK-0123 distance-stratified AUC + permutation null, Bonferroni)
  already established for each observable on the mandatory 3 — no new
  methodology, this is a re-application.
- Why required: BCR_ABL1's and CARDIAC_MYOSIN's positive findings are
  exactly the kind of claim TASK-0115 was written to flag — real,
  well-evidenced on their own terms, but produced by the same 3-target
  review cycle that has now looked at these same proteins' true labels
  dozens of times across this project's history. A result that also
  clears (or comes close to) the same bar on PTP1B/CASPASE7 — targets
  this project's review history has never seen — is materially stronger
  6-pager evidence than the mandatory-3 result alone. A result that
  vanishes on the generalization set is not a retraction (TASK-0115's
  own Constraints: this is not grounds to retract the mandatory-3
  finding) but changes how it should be framed in the proposal.
- In Scope:
  - `transport.R_eff`/`T_E` on PTP1B, CASPASE7 — same `E`/`gamma_lead`
    values TASK-0145 pre-registered (no re-selection against these new
    labels; report the same fixed operating point).
  - `lowmode_predictor.prs_low`/`dcc_low` on PTP1B, CASPASE7 — same
    `k_modes` sweep {5,10,15,20} TASK-0149 already ran, same seed
    convention (full active-site array, `coherent=False`).
  - TASK-0123's stratified AUC + permutation null on every cell, same
    Bonferroni discipline (this task adds 2 targets x 2 observables x
    up to 4 k-values = new comparisons; state the correction count
    explicitly, do not silently reuse the mandatory-3's own alpha).
  - Report whichever way it comes out, including "does not generalize."
- Out Of Scope:
  - GLUCOKINASE, CASPASE1, GROEL_SUBUNIT, TAR_RECEPTOR — none has a
    resolved runnable config; not this task's job to resolve the
    schema question (see [[TASK-0081]]'s open item).
  - Any new observable or parameter tuning — pure re-application of two
    already-built, already-validated methods to two already-resolved
    targets.
  - Re-litigating whether BCR_ABL1/CARDIAC_MYOSIN's own mandatory-3
    findings are valid — they stand as reported; this task only adds
    generalization evidence alongside them.
- Constraints And Invariants:
  - No label-informed parameter selection — reuse the pre-registered
    operating points verbatim (this is precisely what makes the check
    meaningful under TASK-0115's own logic).
  - State the Bonferroni correction count explicitly for this task's own
    new comparisons; do not fold them into the mandatory-3's already-
    reported alpha post hoc.
- Planned Validation: PASS/FAIL/AMBIGUOUS per target x observable,
  against the same stratified-AUC + permutation-null bar already
  established; explicit side-by-side comparison table against the
  mandatory-3 numbers already in `RESULTS.md`.

## TODO

- [ ] Confirm PTP1B/CASPASE7 configs still resolve cleanly (re-verify
      against [[TASK-0081]]'s own Done section, don't re-trust from
      memory — chain/ligand fields were hand-corrected there).
- [ ] Run `transport.R_eff`/`T_E` on both targets, pre-registered
      operating point only.
- [ ] Run `lowmode_predictor.prs_low`/`dcc_low` on both targets, full
      `k_modes` sweep.
- [ ] TASK-0123 stratified AUC + permutation null, explicit new
      Bonferroni count for this task's own comparisons.
- [ ] Side-by-side table: mandatory-3 result vs. generalization-set
      result, per observable.
- [ ] `RESULTS.md` section; cross-link from TASK-0145's and TASK-0149's
      own Done sections (additive, per this project's convention) and
      from TASK-0115's own Rule #6 as the first real application of it.

## Dependency

- [[TASK-0145]] (Done) — `transport.R_eff`/`T_E`, reused as-is.
- [[TASK-0149]] (Done) — `lowmode_predictor.prs_low`/`dcc_low`, reused
  as-is.
- [[TASK-0081]]/[[TASK-0127]] (Done) — PTP1B/CASPASE7 configs and the
  established `run_challenge.py --target` invocation.
- [[TASK-0123]] (Done) — stratified AUC + permutation-null methodology.
- [[TASK-0115]] (Done) — the rule this task is the first real
  application of.

## Open Questions

- None — targets, methods, and evaluation lens are all already
  resolved; this is a re-application, not a design decision.

## Done

(not yet)
