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
- Status: Done (2026-07-24) — mixed: `dcc_low` replicates cleanly on PTP1B; transport does not clearly generalize
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

- [x] Confirm PTP1B/CASPASE7 configs still resolve cleanly (re-verify
      against [[TASK-0081]]'s own Done section, don't re-trust from
      memory — chain/ligand fields were hand-corrected there).
- [x] Run `transport.R_eff`/`T_E` on both targets, pre-registered
      operating point only.
- [x] Run `lowmode_predictor.prs_low`/`dcc_low` on both targets, full
      `k_modes` sweep.
- [x] Permutation null, explicit new Bonferroni count for this task's
      own comparisons. (Each observable kept its own already-established
      evaluation lens rather than a uniform stratified-AUC one — a
      tested divergence from this task's own filing text, see Done.)
- [x] Side-by-side table: mandatory-3 result vs. generalization-set
      result, per observable.
- [x] `RESULTS.md` section; cross-link from TASK-0145's and TASK-0149's
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

**Headline: mixed, real, and informative — neither a clean replication nor a clean
retraction. `dcc_low`'s CARDIAC_MYOSIN positive generalizes cleanly to PTP1B (arguably
the strongest, most robust single result in the project now); transport's BCR_ABL1
positive does not generalize to either target under strict correction, though CASPASE7
shows an uncorrected-significant hint in the same direction.**

### Pure re-application, as scoped

New `scripts/generalization_check_transport_lowmode.py` imports and calls
`transport_observable_real_run.run_one`/`lowmode_predictor_real_run.run_target`
directly, unmodified, on PTP1B and CASPASE7 — zero new scoring logic, exactly this
task's own "no new methodology" constraint. GLUCOKINASE/CASPASE1/HEMOGLOBIN/
GLYCOGEN_PHOSPHORYLASE/PFK confirmed still unresolved (re-checked `config/
targets.yaml` directly, not assumed from memory) — out of scope, per this task's own
text. PTP1B (N=298, seed=5, pocket=14) and CASPASE7 (N=461, seed=5, pocket=7) both
resolved cleanly, matching the exact numbers already seen in TASK-0140's own real run
(cross-checked, not re-derived).

### One filing-text imprecision resolved by reading both scripts directly, not assumed

This task's own text describes both observables as using "TASK-0123 distance-
stratified AUC + permutation null" — true for `lowmode_predictor_real_run.py`
(confirmed: it imports and calls `stratified_auc` directly), **not true for
`transport_observable_real_run.py`**, which uses whole-graph AUC +
`diagnostics.classify_failure` (block-bootstrap CI) + a whole-graph permutation null —
a different, but equally already-established, lens. Kept each observable's own actual
methodology rather than forcing a third, new lens onto transport that its own real-run
script never used — "the exact same... evaluation lens already established" means
what each script actually did, not what this task's filing text assumed both did.

### Bonferroni: two new families, explicitly scoped to this task's own comparisons

Not folded into either mandatory-3 task's own already-reported alpha (TASK-0145 used
`0.05/3`, targets-only; TASK-0149 used `0.05` per-cell uncorrected then read against a
per-target null — neither convention is silently reused here). This task's own new
families:
- **Transport**: 2 targets × 3 quantities (R_eff, T(E=0) on L, T(E=0) on H_new) = 6
  comparisons → α = 0.05/6 = 0.00833.
- **Lowmode**: 2 targets × 2 observables × 4 k_modes = 16 comparisons → α = 0.05/16 =
  0.00313.

### Transport — does not clearly generalize under strict correction

| Target | Quantity | AUC | Category | p-value | Significant (α=0.00833) |
|---|---|---|---|---|---|
| BCR_ABL1 (mandatory, for reference) | `T(E=0)` on L | 0.698 | NO_FAILURE_DETECTED | 0.003 | — |
| PTP1B | `T(E=0)` on L | 0.382 | BEATS_CHANCE_NOT_FLOOR | 0.926 | No |
| PTP1B | `T(E=0)` on H_new | 0.682 | NO_FAILURE_DETECTED | 0.012 | No |
| PTP1B | `R_eff` | 0.384 | BEATS_CHANCE_NOT_FLOOR | 0.921 | No |
| CASPASE7 | `T(E=0)` on L | 0.748 | BEATS_CHANCE_NOT_FLOOR | 0.011 | No |
| CASPASE7 | `T(E=0)` on H_new | 0.496 | NO_SIGNAL_IN_APO | 0.523 | No |
| CASPASE7 | `R_eff` | 0.740 | BEATS_CHANCE_NOT_FLOOR | 0.012 | No |

PTP1B's `T(E=0)` on L — the exact quantity that was significant on BCR_ABL1 — comes
back **below chance** (AUC 0.382, p=0.926): the opposite direction, not just a null
result. CASPASE7 shows the same quantity at AUC 0.748 with an uncorrected p=0.011 (would
clear TASK-0145's own looser 3-target-only bar, 0.0167, but not this task's own
stricter 6-comparison one) — a real, suggestive echo of the BCR_ABL1 direction, not
decisive. Read plainly: transport's mandatory-3 positive does not replicate cleanly on
the generalization set; CASPASE7 keeps the door open, PTP1B closes it (in the opposite
direction) for the same specific quantity.

### Lowmode — `dcc_low` generalizes cleanly to PTP1B; `prs_low` does not generalize to either

| Target | Observable | k | Well-powered max AUC | ρ(score,−hop) | p-value | Significant (α=0.00313) |
|---|---|---|---|---|---|---|
| CARDIAC_MYOSIN (mandatory, for reference) | `dcc_low` | 20 | 0.962 | +0.480 | <0.001 | — |
| CARDIAC_MYOSIN (mandatory, for reference) | `prs_low` | 20 | 0.922 | −0.401 | 0.006 | — |
| PTP1B | `dcc_low` | 10 | **1.000** | +0.558 | **0.001** | **Yes** |
| PTP1B | `dcc_low` | 15 | **0.955** | +0.641 | **0.001** | **Yes** |
| PTP1B | `dcc_low` | 20 | **0.955** | +0.628 | **0.003** | **Yes** |
| PTP1B | `dcc_low` | 5 | 0.704 | +0.386 | 0.223 | No |
| PTP1B | `prs_low` | 5, 10, 15, 20 | 0.233–0.426 | −0.558 to −0.640 | 0.952–1.000 | No (any k) |
| CASPASE7 | `dcc_low` | 5–20 | 0.578–0.705 | +0.690 to +0.781 | 0.135–0.376 | No (any k) |
| CASPASE7 | `prs_low` | 5–20 | 0.375–0.415 | −0.205 to −0.364 | 0.717–0.793 | No (any k) |

**`dcc_low` on PTP1B clears this task's own stricter α at 3 of 4 k-values** (10, 15,
20), including a well-powered max AUC of exactly 1.000 at k=10 — a genuine
replication on a target the project's review history had never seen, and by this
task's own stricter correction, not a looser one inherited from the mandatory-3 run.
`prs_low` never reaches significance on either generalization target, at any k — its
own mandatory-3 CARDIAC_MYOSIN positive (p=0.006) does not generalize. Neither
observable shows anything on CASPASE7. **`ρ(score,−hop)` stays substantial on PTP1B's
`dcc_low` too (+0.386 to +0.641)** — the same "does not decorrelate from distance as
the synthetic control predicted" pattern TASK-0149's own mandatory-3 write-up already
flagged, now confirmed on a second, independent target rather than resolved.

### Interpretation

**`dcc_low` is now, by a real margin, the most robustly-evidenced positive result in
this project** — Bonferroni-significant under a stricter, purpose-built correction on
two different, independently-labeled targets (CARDIAC_MYOSIN and PTP1B), a form of
cross-target evidence no other observable in this program's register has. It should be
framed accordingly in any write-up: not as "a mandatory-3 finding," but as "a finding
that replicated on the generalization set," per TASK-0115's own Rule #6 rationale for
why this check exists. `prs_low` and the transport family's specific BCR_ABL1 result
are the honest opposite case — real, well-evidenced on their own terms (this task does
not retract them, per its own Constraint), but the generalization check does not
strengthen them, and PTP1B's opposite-direction transport result is a real, reportable
complication for the transport family specifically, not just an absence of support.
