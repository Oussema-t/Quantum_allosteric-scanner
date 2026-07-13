# TASK-0101 Operator sweep Tier-1 harness — `analysis.operator_sweep` + `scripts/sweep_operators.py`

## Context

- ID: TASK-0101
- Title: Implement a library function `analysis.operator_sweep(...)` that
  scores every named Hamiltonian operator (`H1`-`H14`, `build_H_new`,
  `build_H10`) — **through both propagators** — against TASK-0094's
  proximity floor on a real target, plus a thin `scripts/sweep_operators.py`
  that runs it across all 3 mandatory targets (KRAS_G12C, BCR_ABL1,
  CARDIAC_MYOSIN) and writes a reported table. **Tier-1 (descriptive)
  only — no operator selection.**
- Status: TODO
- Owner: Implementer
- Source: TASK-0100's Architect decision (Done, 2026-07-13) — resolves
  where the sweep lives (library function + thin script, not
  `run_challenge.py`) and what "rate the results" means (Tier 1:
  floor-clearing + raw AUC + apo/holo consistency, no frozen-gate needed
  since nothing is being selected).
- **Amended 2026-07-13, per explicit user direction, two changes:**
  (a) score every operator through **both** `time_averaged_ctqw` and
  `ground_state_relaxation`, not `time_averaged_ctqw` alone — TASK-0091
  found the propagator choice, not just the operator choice, was what
  separated BCR_ABL1's chance result (CTQW, 0.525) from its
  floor-clearing one (ground-state, 0.731); a sweep that only varies
  operators through CTQW would miss the axis that actually produced the
  one real result found so far. (b) the harness must support **running
  in parts** — chunked, resumable, parallelizable across machines, and
  able to recompute a single suspicious cell without repaying the whole
  sweep's cost. See the new "Chunking and resumability" subsection below.

## Intent Contract

- Outcome: for every **(operator, propagator, target)** cell — 16
  operators × 2 propagators (`time_averaged_ctqw`, `ground_state_relaxation`)
  × 3 targets = 96 cells — a reported row: operator name, tier (A/B, per
  TASK-0100), propagator, raw AUC, floor-cleared (bool, per TASK-0094's
  max-of-three convention: `degree_centrality`/`euclid_from_seed_centroid`/
  `hop_from_seed`), and apo/holo consistency where TASK-0092 makes it
  available, else `N/A`.
- In Scope:
  - `analysis.operator_sweep(coords, bfactors, source, pocket_label,
    floor_scores, cutoff, operators=None, propagators=("ctqw", "ground_state"))`
    — iterates a name→callable registry (promote/adapt
    `test_hamiltonians.py`'s `_LAPLACIAN_OPS` pattern to library level;
    handle `H1`'s adjacency-not-Laplacian shape and `H10`/`H13`/`H14`'s
    extra-argument signatures explicitly, don't force one signature onto
    all fourteen) **crossed with both propagators** — `time_averaged_ctqw`
    and `ground_state_relaxation`, both already at `t_max=15.0` default,
    both scored via the same `metrics.auc` path every other verdict
    function already uses (this task does not invent a new scoring
    method, just applies the existing one twice per operator).
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

### Chunking and resumability (added 2026-07-13, hard requirement)

96 cells means real wall-clock time (network fetch + eigendecomposition +
AUC per cell) — this must be splittable across parallel processes/machines
and safely re-runnable, not a single monolithic all-or-nothing script:

- `scripts/sweep_operators.py` accepts `--target`, `--operator`, and
  `--propagator` filters (each repeatable / comma-separated), so a single
  invocation can run any subset of the 96-cell grid — e.g. one machine
  runs `--target BCR_ABL1`, another runs `--target KRAS_G12C
  --target CARDIAC_MYOSIN` at the same time, with no shared state or
  coordination required between them beyond each writing its own output.
- Each **(target, operator, propagator)** cell is written to its own
  result file immediately after computing (e.g.
  `__WORK_IN_PROGRESS__/results/<target>/sweep_cells/<operator>__<propagator>.json`),
  not held in memory until the end — a crashed or killed run loses at
  most the one in-flight cell, not the whole sweep.
- The script **skips cells whose output file already exists** by default
  (idempotent re-run — safe to launch the same command twice, or resume
  after an interruption, without repaying already-done work) and takes an
  explicit `--force` (optionally scoped to specific `--target`/
  `--operator`/`--propagator` filters) to recompute a specific cell that
  looks suspicious — this is the "recompute whatever suspicious outcomes"
  requirement: no need to delete files by hand or rerun the entire grid
  to redo one cell.
- A final aggregation step (`--aggregate`, or automatic when no filters
  are passed) reads every per-cell file under `sweep_cells/` and renders
  the combined table — so partial results from several machines can be
  copied into one `results/` tree and aggregated without rerunning any
  computation, only the (cheap) table assembly.
- Real target structures (apo/holo fetches) are cached once per target
  (reuse whatever caching `run_challenge.py`/TASK-0091's session-local
  cache pattern already established) so parallel workers on the same
  target don't each re-fetch/re-clean from RCSB independently.
- Out Of Scope: **Tier-2 selection** — this task does not decide whether
  any operator should replace `H_new`/`H10` as the submission choice, does
  not touch `select_frozen_config`/`leave_one_protein_out`, and does not
  modify `run_challenge.py`. If Tier-1's results suggest a Tier-A operator
  is worth promoting, that is a separate, future task, scoped only after
  seeing what this task's table actually shows.
- Acceptance Scenarios:
  - Given all 3 mandatory targets, when `scripts/sweep_operators.py` runs,
    then it produces one table per target with all 14+2 operators ×
    2 propagators scored, tiered, and floor-checked — no cell silently
    missing or crashing the whole run (an individual cell's failure, e.g.
    a shape mismatch, should be caught and recorded as an error row, not
    abort the sweep for every other cell).
  - Given the existing KRAS_G12C `H_new`/CTQW result (AUC 0.779,
    `BEATS_CHANCE_NOT_FLOOR` per TASK-0094) and BCR_ABL1's `H_new`/
    ground-state result (AUC 0.7315, floor-cleared per TASK-0091), when
    the sweep runs on those targets, then those two specific cells match
    the already-established numbers (pins the new harness to
    already-validated ground truth, not a silently-diverging fresh
    computation).
  - Given a sweep already run to completion, when `--force --target
    BCR_ABL1 --operator H_new --propagator ground_state` is passed, then
    only that one cell recomputes — every other cell's file is untouched
    (mtime-unchanged) and the aggregated table updates only that row.
  - Given two separate invocations on two machines with disjoint
    `--target` filters, when both sets of per-cell files are copied into
    one `results/` tree and `--aggregate` runs, then the combined table
    is identical to what a single, uninterrupted full run would have
    produced.
- Constraints And Invariants: reuse existing scoring machinery
  (`time_averaged_ctqw`, `metrics.auc`, TASK-0094's floor functions) —
  this is a harness/orchestration task, not new physics. Must not modify
  `run_challenge.py` or wire into `select_frozen_config` (Tier-2 is
  explicitly out of scope, per TASK-0100).
- Planned Validation: the KRAS_G12C `H_new` reproduction check above,
  plus a full 3-target run with the resulting tables committed (or
  referenced) as this task's evidence, matching TASK-0079.005's own
  "not mockable, run for real" precedent.
- **Amended 2026-07-13, per `REVIEW-2026-07-13c` (CTQW trapping
  mechanism):** the Tier-1 table must include a **transport diagnostic**
  per operator — ⟨hop from seed⟩ or participation ratio at a fixed t —
  alongside AUC and floor-clearance, not AUC alone. The review found
  `H_new`'s AUC-proximity correlation is caused by disorder-induced
  transport localization (a mechanism, not just a description); a bare
  AUC/floor table cannot distinguish "transports and finds signal" from
  "traps and finds geometry." This is now part of Tier 1's own reporting
  contract, not a separate follow-up.

## Dependency

- Depends on TASK-0100 (Done) — the architecture decision this task
  executes.
- Depends on TASK-0094 (Done, proximity floor) and TASK-0095 (Done,
  correct propagator semantics) — both already landed, unblocked.
- Depends on TASK-0091 (Done) for the ground-state-propagator reproduction
  target (BCR_ABL1/`H_new`/ground-state, AUC 0.7315) used in Acceptance
  Scenarios above.
- Reads TASK-0096's Done section for the Tier A/B operator list.
- Not blocked by, and does not block, TASK-0093 or TASK-0099 (per
  TASK-0100's explicit resequencing note — both are diagnostics on the
  already-chosen `H_new`, not operator-selection acts).
- Related, not blocking: TASK-0102 (ground-state-relaxation seed-invariance
  test, filed alongside this amendment) — if TASK-0102 finds
  `ground_state_relaxation` at `t_max=15` is largely seed-independent
  (converged to `H`'s global ground state regardless of source), that
  would call into question how much this sweep's ground-state column
  actually measures active-site-coupled signal vs. a static per-structure
  feature — worth reading TASK-0102's finding alongside this task's
  results table once both land, though neither blocks the other.

## Open Questions

- **Floor-clearing significance threshold**: TASK-0094's floor check is
  already boolean (clears / doesn't), so this task doesn't need a new
  threshold for that. But if this task's table is later used to eyeball
  "which Tier-A operator looks most promising," avoid inventing an
  ad hoc ranking threshold inline — flag it as a Tier-2 question, not
  something to silently decide here.

## Done

(not yet)
