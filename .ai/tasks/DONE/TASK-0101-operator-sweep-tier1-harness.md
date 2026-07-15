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
- Status: Done
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

**Implementation, real pinning check, and synthetic tests are Done. The
full 96-cell real-data sweep is running in the background as of
2026-07-14 06:39 (session-local, not yet complete) — this section will
be finalized once it lands; do not treat the sweep as complete from this
section alone, check `results/<target>/operator_sweep.md` on disk.**

- `analysis.operator_sweep(coords, bfactors, source, pocket_label,
  floor_scores, cutoff, operators=None, propagators=("ctqw",
  "ground_state"), t_max=15.0, n_steps=500)` — a uniform three-arg
  `(coords, bfactors, cutoff) -> H` registry (`_operator_registry`) with
  one explicit lambda adapter per operator, not a generic dispatch, per
  this task's own Constraint. Reuses `diagnostics.classify_failure` for
  floor-clearing (no new comparison invented) and
  `REVIEW-2026-07-13c`'s own participation-ratio transport diagnostic
  (`_transport_participation_ratio`, PR/N).
- **16 operators, not 14+1**: `H1`-`H9`, `H10` (=`H10_disorder_suppressed`),
  `H11`-`H14`, `H_new` (=`build_H_new`), `build_H10` — the last two
  entries deliberately duplicate `H_new`/`H10`'s underlying computation
  under their submission-facing names, per this task's own "H1-H14,
  build_H_new, build_H10" enumeration (96 = 16 x 2 x 3 only holds this
  way). Verified `H10`/`build_H10` produce numerically identical AUCs on
  real data (see pinning run below) — a free consistency check that the
  alias is faithful.
- **Tier A = {H10, H14, H_new, build_H10}, Tier B = the other 12** — per
  TASK-0100 Sec.3's three *conceptual* candidates (H_new, H10, H14),
  spread across 4 registry rows because H10 has two names.
- **H13's 3N x 3N shape mismatch is caught explicitly, not left to fail
  silently** — checked directly while implementing: a 3N-length matrix
  indexed by an N-length source/pocket-label array would **not** crash,
  it would silently score against the wrong coordinate-flattened index
  space and produce a shape-valid but physically meaningless number. Added
  an explicit `H.shape[0] != len(coords)` guard that raises before any
  propagator runs, caught by the per-cell `try/except` and recorded as an
  honest error row for both propagators. Regression-tested directly
  (`test_h13_shape_mismatch_is_caught_not_raised`).
- 9 synthetic unit tests in `test_analysis.py::TestOperatorSweep` (all 16
  operators present, tier assignment, H13 error handling, H10/build_H10
  agreement, operator/propagator filters, unknown-operator handling,
  floor-clearing precedence, transport_pr bounds, apo/holo N/A pending
  TASK-0092).
- `scripts/sweep_operators.py` — chunked/resumable per this task's own
  hard requirement: each cell writes to its own
  `results/<target>/sweep_cells/<operator>__<propagator>.json`
  immediately; re-running skips existing cells by default; `--force`
  (composed with `--target`/`--operator`/`--propagator`) recomputes only
  the selected subset; `--aggregate` (or no filters at all) renders
  `results/<target>/operator_sweep.md` from whatever cell files exist,
  computing nothing. Reuses `run_challenge.py`'s own `_load_apo_holo` —
  not reimplemented. Network-fetch caching relies on prody's existing
  local PDB cache (`pdb_cache/`, already gitignored in this repo) rather
  than a new caching layer — a proportionate choice, documented in the
  script's own `_prepare_target` docstring, not a silent omission.
- **Real pinning check (this task's own Acceptance Scenario) — passes
  exactly**: `python scripts/sweep_operators.py --target KRAS_G12C
  --operator H_new H10 --propagator ctqw ground_state` against live
  4OBE/6OIM reproduces `AUC(H_new, ctqw) = 0.7792494481236203` — matches
  the already-established real run's `0.779` to full float precision,
  confirming the new harness is not silently diverging from
  already-validated ground truth.
- Full local run (synthetic suite, before the real sweep was launched):
  `python3 .ai/tools/pytest_local.py wip-all --json` → 524 passed, 1
  xpassed (pre-existing, unrelated), 0 failed.
- **Staging/commit deliberately skipped** — explicit user instruction
  this session ("Do NOT git add or git commit anything — leave the stage
  empty. I'm orchestrating which package ships when").

### Real bug found and fixed while reviewing the first full sweep's own output

Read the completed sweep's real numbers before trusting them (this
session's own established practice) — CARDIAC_MYOSIN's 32 valid cells
all came back `NO_FAILURE_DETECTED`/`BEATS_CHANCE_NOT_FLOOR`, never
`INSUFFICIENT_RESOLUTION`, despite that target's apo N=950 exceeding
`LARGE_N_THRESHOLD=800` — the real submission pipeline (`run_challenge.py`)
correctly flags this same target that way. Root cause: `operator_sweep`'s
`classify_failure` call omitted `H=`/`bfactors=`, which silently disables
*both* `OPERATOR_DEGENERATE` and `INSUFFICIENT_RESOLUTION` (both require
`H` to run `operator_diagnostics` at all) — not a partial bug, those two
checks never ran for any cell, on any target, in the first full sweep.
Fixed (`analysis.py`, one line + the two now-required kwargs), regression
-tested directly (`test_disconnected_operator_is_flagged_operator_
degenerate`, a small disconnected synthetic graph — cheaper than building
an 800+-residue fixture to exercise the large-N path specifically, same
mechanism), and the **entire 96-cell sweep was force-recomputed**
(`--force`, not just CARDIAC_MYOSIN) since the bug could in principle
have affected any target/operator combination, not only the one where it
happened to be visible. KRAS_G12C/BCR_ABL1 AUCs confirmed byte-identical
to the pre-fix run (spot-checked); only CARDIAC_MYOSIN's `diagnosis`
changed, to `INSUFFICIENT_RESOLUTION` across the board, as expected.

Also found and fixed, while re-running the full local suite after this
change: my own new `RESULTS.md` prose (TASK-0104) tripped
`test_ground_state_relaxation_guard.py`'s `TestNoStaleClassicalDiffusion
Framing` regression test (TASK-0095's own guard against "classical" and
"heat" co-occurring on a live line) — rephrased the one offending
sentence, no meaning lost.

### Real sweep results (96 cells, all 3 mandatory targets, force-recomputed post-fix)

Full tables: `results/{KRAS_G12C,BCR_ABL1,CARDIAC_MYOSIN}/operator_sweep.md`.

**The single clearest pattern in the whole register: zero cells clear
the proximity floor via `ctqw`, anywhere, on any target or operator.**
Every floor-clearing cell in this entire 96-cell sweep is a
`ground_state` cell:

| Target | Floor-clearing cells (operator/propagator) | AUC |
|---|---|---|
| KRAS_G12C | `H10`/ground_state, `build_H10`/ground_state (same op, two names) | 0.921 |
| BCR_ABL1 | `H1`/ground_state | 0.571 |
| BCR_ABL1 | `H10`/ground_state, `build_H10`/ground_state | 0.636 |
| BCR_ABL1 | `H_new`/ground_state | 0.731 (the already-known TASK-0091 result) |
| CARDIAC_MYOSIN | none — `INSUFFICIENT_RESOLUTION` short-circuits every cell before the floor check runs | — |

This is new evidence, not previously visible from any single-operator
test: `REVIEW-2026-07-13c`'s CTQW-trapping mechanism (`H_new` specifically)
now looks like a **register-wide property of `ctqw` on this pipeline's
propagation regime**, not an `H_new`-specific defect — worth flagging to
whoever next reads `RESULTS.md`'s open questions, though interpreting it
is out of this Tier-1 harness's own scope (descriptive only, per
TASK-0100).

**Tier-A-specific observation**: `H14` (TASK-0096's "let the sweep
decide" research operator) **never clears the floor on any target,
through either propagator** — a real, recorded negative result per
TASK-0100's own "an honest NO is a publishable result" policy, not
silently dropped. `H10`/`build_H10` clear on 2/3 targets (agreeing with
each other exactly both times, the alias-fidelity check working again on
real, not just synthetic, data); `H_new` clears on 1/3.

**`H13` fails identically and correctly on all 3 targets** (shape
mismatch, caught, recorded, does not abort the sweep) — 6 of the 96
cells, exactly as designed.

No Tier-2 conclusion is drawn from any of this (explicitly out of this
task's own scope) — this table is handed to `RESULTS.md`/whoever picks
up a future Tier-2 task, not acted on here.

Full local run after the fix: `python3 .ai/tools/pytest_local.py
wip-all --json` → 531 passed, 1 xpassed (pre-existing, unrelated), 0
failed.

- **Staging/commit**: the implementation (`analysis.py`, tests,
  `sweep_operators.py`) and this Done writeup are ready; the `classify_
  failure` bug fix and its regression test are new since the last
  commit and not yet staged, per this session's standing "hold until
  told" default — the previous explicit stage/commit instruction covered
  the pre-fix state only.

**Addendum, 2026-07-15 — "zero cells clear via `ctqw`" corrected**: the
headline finding above (line ~279, "the single clearest pattern in the
whole register") rested on CARDIAC_MYOSIN's `INSUFFICIENT_RESOLUTION`
row, which is itself now corrected — `LARGE_N_THRESHOLD=800` (the value
in effect for this task's real 96-cell sweep) had no derivation anywhere
in its cited source, was corrected to `1000` per explicit user direction
2026-07-14 (full account: `diagnostics.py`'s own `LARGE_N_THRESHOLD`
comment; scientific record: `RESULTS.md`'s CARDIAC_MYOSIN section,
`[CORRECTED 2026-07-15]` block). Re-run against identical apo data (AUC
values unchanged throughout — only the diagnosis this task's own
`classify_failure` bug fix now correctly evaluates against changed):
CARDIAC_MYOSIN's 32-cell block goes from "`INSUFFICIENT_RESOLUTION`,
none reach the floor check" to **14 of 30 valid cells clearing the
floor, 11 of them via `ctqw`** (`H2`, `H3`, `H4`, `H5`, `H6`, `H8`,
`H10`, `H11`, `H12`, `H_new`, `build_H10`, all `NO_FAILURE_DETECTED`;
`results/CARDIAC_MYOSIN/operator_sweep.md` has the full table).

**The corrected register-wide count is 20 of 96 cells clear the floor
(not 0), 11 of them via `ctqw` (not 0)**: KRAS_G12C 2 (both
`ground_state`) + BCR_ABL1 4 (all `ground_state`) + CARDIAC_MYOSIN 14
(11 `ctqw` + 3 `ground_state`) = 20 total, 11 `ctqw` + 9 `ground_state`.
See the three target tables directly for the authoritative per-cell
detail. This does **not**
mean `REVIEW-2026-07-13c`'s CTQW-trapping mechanism is wrong — that
review's argument was about *why* `H_new`'s diagonal potentials localize
CTQW transport, a real, separately-verified dynamical claim, not merely
an inference from "the register shows zero ctqw floor-clears." But the
empirical register-wide claim as stated here was false and fed directly
into that review's framing; whether CTQW-trapping still explains
CARDIAC_MYOSIN's *many* ctqw floor-clears (as opposed to KRAS/BCR_ABL1's
zero) is a real, unresolved question this correction surfaces but does
not answer — a scientific-synthesis call for whoever next touches
`REVIEW-2026-07-13c`'s conclusions or files a follow-up, not settled by
this addendum.
