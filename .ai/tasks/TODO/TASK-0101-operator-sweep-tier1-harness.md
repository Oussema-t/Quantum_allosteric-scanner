# TASK-0101 Operator sweep Tier-1 harness — `analysis.operator_sweep` + `scripts/sweep_operators.py`

## Context

- ID: TASK-0101
- Title: Implement a library function `analysis.operator_sweep(...)` that
  scores every named Hamiltonian operator (`H1`-`H14`, `build_H_new`,
  `build_H10`) against TASK-0094's proximity floor on a real target, plus
  a thin `scripts/sweep_operators.py` that runs it across all 3 mandatory
  targets (KRAS_G12C, BCR_ABL1, CARDIAC_MYOSIN) and writes a reported
  table. **Tier-1 (descriptive) only — no operator selection.**
- Status: TODO
- Owner: Implementer
- Source: TASK-0100's Architect decision (Done, 2026-07-13) — resolves
  where the sweep lives (library function + thin script, not
  `run_challenge.py`) and what "rate the results" means (Tier 1:
  floor-clearing + raw AUC + apo/holo consistency, no frozen-gate needed
  since nothing is being selected).

## Intent Contract

- Outcome: for every operator in the registry below, on every mandatory
  target, a reported row: operator name, tier (A/B, per TASK-0100),
  raw AUC, floor-cleared (bool, per TASK-0094's max-of-three convention:
  `degree_centrality`/`euclid_from_seed_centroid`/`hop_from_seed`), and
  apo/holo consistency (`mean_rho_apo_holo`/`mean_jacc20` where TASK-0092
  makes them available, else `N/A`).
- In Scope:
  - `analysis.operator_sweep(coords, bfactors, source, pocket_label,
    floor_scores, cutoff, operators=None)` — iterates a name→callable
    registry (promote/adapt `test_hamiltonians.py`'s `_LAPLACIAN_OPS`
    pattern to library level; handle `H1`'s adjacency-not-Laplacian shape
    and `H10`/`H13`/`H14`'s extra-argument signatures explicitly, don't
    force one signature onto all fourteen). Scores each via the existing
    `time_averaged_ctqw` + `metrics.auc` path (same scoring convention
    every other verdict function already uses — this task does not
    invent a new scoring method).
  - `scripts/sweep_operators.py <target_name>` (or a loop over all 3
    mandatory targets by default) — fetches/cleans real structures
    (reuse `run_challenge.py`'s own fetch/clean glue, don't reimplement),
    calls `operator_sweep`, writes a table (CSV or markdown, match this
    repo's existing `RESULTS.md` conventions) to
    `__WORK_IN_PROGRESS__/results/<target>/operator_sweep.{csv,md}`.
  - Tier labels (A: `H_new`/`H10`/`H14`; B: everything else) attached to
    every row per TASK-0100's policy.
  - Floor-failing operators are recorded in the table, not filtered out
    (TASK-0100's "an honest NO is a publishable result" policy).
- Out Of Scope: **Tier-2 selection** — this task does not decide whether
  any operator should replace `H_new`/`H10` as the submission choice, does
  not touch `select_frozen_config`/`leave_one_protein_out`, and does not
  modify `run_challenge.py`. If Tier-1's results suggest a Tier-A operator
  is worth promoting, that is a separate, future task, scoped only after
  seeing what this task's table actually shows.
- Acceptance Scenarios:
  - Given all 3 mandatory targets, when `scripts/sweep_operators.py` runs,
    then it produces one table per target with all 14+2 operators scored,
    tiered, and floor-checked — no operator silently missing or crashing
    the whole run (an individual operator's failure, e.g. a shape
    mismatch, should be caught and recorded as an error row, not abort the
    sweep for every other operator).
  - Given the existing KRAS_G12C `H_new` result (AUC 0.779,
    `BEATS_CHANCE_NOT_FLOOR` per TASK-0094), when the sweep runs on
    KRAS_G12C, then `H_new`'s row in the new table matches that already-
    established number (pins the new harness to already-validated
    ground truth, not a silently-diverging fresh computation).
- Constraints And Invariants: reuse existing scoring machinery
  (`time_averaged_ctqw`, `metrics.auc`, TASK-0094's floor functions) —
  this is a harness/orchestration task, not new physics. Must not modify
  `run_challenge.py` or wire into `select_frozen_config` (Tier-2 is
  explicitly out of scope, per TASK-0100).
- Planned Validation: the KRAS_G12C `H_new` reproduction check above,
  plus a full 3-target run with the resulting tables committed (or
  referenced) as this task's evidence, matching TASK-0079.005's own
  "not mockable, run for real" precedent.

## Dependency

- Depends on TASK-0100 (Done) — the architecture decision this task
  executes.
- Depends on TASK-0094 (Done, proximity floor) and TASK-0095 (Done,
  correct propagator semantics) — both already landed, unblocked.
- Reads TASK-0096's Done section for the Tier A/B operator list.
- Not blocked by, and does not block, TASK-0093 or TASK-0099 (per
  TASK-0100's explicit resequencing note — both are diagnostics on the
  already-chosen `H_new`, not operator-selection acts).

## Open Questions

- **Floor-clearing significance threshold**: TASK-0094's floor check is
  already boolean (clears / doesn't), so this task doesn't need a new
  threshold for that. But if this task's table is later used to eyeball
  "which Tier-A operator looks most promising," avoid inventing an
  ad hoc ranking threshold inline — flag it as a Tier-2 question, not
  something to silently decide here.

## Done

(not yet)
