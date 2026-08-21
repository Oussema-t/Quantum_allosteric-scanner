# TASK-0119 Fix the clock: per-operator t* from spectral gap, re-run the operator comparison

## Context

- ID: TASK-0119
- Title: Replace the single hardcoded `t_max=15` (applied identically to
  every operator regardless of its own energy scale) with a per-operator
  timescale derived from its spectral gap (or an equivalent hopping-norm
  normalization of `H` before propagation); re-run the 96-cell operator
  sweep ([[TASK-0101]]) and the CTQW-trapping reproduction ([[TASK-0106]])
  under it.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer B (this thread)
- Claimed At: 2026-07-16 22:30
- Source: `.ai/reviews/REVIEW-panel-2026-07-16-v2.md` §2.2, §5 P0-2.
- Priority: **P0 — this week.**

## Intent Contract

- Outcome: (1) a per-operator `t*` — the panel's proposal is
  `t* ≈ 1/Δλ` (the graph mixing time from `H`'s spectral gap), or
  equivalently normalizing `H` by its hopping norm before propagation so
  every operator is compared at the same *effective* time, not the same
  *nominal* `t`; (2) the operator comparison ([[TASK-0101]]'s 96-cell
  sweep) re-run under per-operator `t*` instead of the shared
  `t_max=15`; (3) [[TASK-0106]]'s BCR_ABL1 CTQW-trapping reproduction
  re-run the same way.
- **What this task must NOT conclude, per the panel's own executed
  correction (§2.2):** do not treat a shift in the `H10`-vs-`H_new`
  *ranking* under the fixed clock as evidence the original trapping
  finding was "mostly a units artifact." The panel re-ran this exact
  check: after normalizing each operator by its hopping scale, `H_new`
  stays strongly localized (participation ratio 1.3→3.8 across
  t=15→1500) while a clean Laplacian spreads (14.7→83.7) and `H10`
  spreads (23.5→48) — **the localization is gauge-robust and real**,
  driven by `H_new`'s 7-10× disorder/bandwidth ratio (itself a
  gauge-invariant quantity, established in the same review's §2.4).
  Expect the operator *ranking* to shift under the fixed clock; report
  that `H_new`'s localization independently survives it — both facts,
  not one in place of the other.
- **Secondary correction to land in the same pass**: [[TASK-0106]]'s own
  Done section reads a *higher* `H_new` participation-ratio/N (0.299 vs.
  `H10`/`H2`'s 0.056/0.054) as evidence `H_new` "stays markedly closer to
  the seed" — this is backwards. `_transport_participation_ratio` =
  `1/(N·Σp²)`; **high PR means delocalized, low PR means localized**.
  Correct TASK-0106's prose narrative direction (the underlying numbers
  and the localization conclusion are still correct — only the
  PR-value-to-localization-direction mapping in the write-up is wrong).
  Do this as a documentation correction in TASK-0106's own Done section
  (additive note, do not delete the original text), not a silent edit.
- In Scope:
  - Implement the per-operator `t*` (spectral gap of `H`, reusing
    `np.linalg.eigh`'s already-computed eigenvalues where available —
    same reuse discipline as [[TASK-0109]]).
  - Re-run [[TASK-0101]]'s 96-cell sweep and [[TASK-0106]]'s BCR_ABL1
    reproduction under it.
  - Report both the shifted ranking and the surviving-localization
    finding explicitly, per the "must NOT conclude" section above.
- Out Of Scope:
  - Building the general `check_convergence` validity gate — that is
    [[TASK-0109]]'s own scope (Nyquist/spectral-gap checks as a
    reusable function). This task consumes whatever timescale
    convention TASK-0109 lands on if it lands first; if TASK-0109 is
    not yet done, use the panel's `t* ≈ 1/Δλ` formula directly as an
    interim, explicitly flagged as such, rather than blocking.
  - The seed-gauge fix ([[TASK-0118]]) — separate confound.
- Constraints And Invariants:
  - Every re-run number in this task's Done section must state which
    `t*` convention produced it.
- Planned Validation: re-run [[TASK-0101]]/[[TASK-0106]] under the new
  clock; report the delta against the old shared-`t_max=15` numbers
  explicitly, not just the new numbers in isolation.

## In Progress

None

## TODO

- [ ] Implement per-operator `t*` (spectral-gap-derived or hopping-norm
      normalization) — state which, and why, in Done.
- [ ] Re-run [[TASK-0101]]'s 96-cell operator sweep under it.
- [ ] Re-run [[TASK-0106]]'s BCR_ABL1 reproduction under it.
- [ ] Report ranking shift vs. localization-survival as two separate,
      explicit findings — do not merge them into one conclusion.
- [ ] Correct TASK-0106's PR-direction narrative bug (additive note).

## Dependency

- Soft dependency: [[TASK-0109]] (if its `check_convergence` timescale
  convention lands first, use it; otherwise use the panel's `t*≈1/Δλ`
  directly as an interim, flagged as such).
- Should ideally run after [[TASK-0118]]'s seed-convention fix lands, so
  the re-run isn't done twice under two different seed conventions —
  soft ordering, not a hard block.

## Open Questions

- Whether `t* ≈ 1/Δλ` or hopping-norm `H` normalization is the better
  practical choice for this codebase — Implementer's call, state which
  and why in Done; the panel offers both as equivalent options.

## Done

**Choice made (Open Question above): `t* = -ln(tol)/gap`, `gap = w[1]-w[0]`,
`tol=1e-2`** — TASK-0109's own `propagators.min_adequate_t_max(kind=
"ground_state_relaxation")`, not a fresh interim formula (TASK-0109
landed first, per this task's own soft Dependency). Same functional form
as the panel's `t* ~ 1/dlambda`, with the `-ln(tol)` constant made
explicit rather than left as an unstated proportionality. A **single**
`t*` per operator, used for both propagators when scoring that operator
(not a second, propagator-specific formula) — matches this task's own
"every operator compared at the same effective time," and avoids
TASK-0109's own documented fragility (its `time_averaged_ctqw`-specific
AAKV-bound criterion blows up on near-degenerate spectra; not needed
here since a single shared-per-operator `t*` is all this task asks for).
`n_steps` for `ctqw` propagations set from `min_adequate_n_steps(t*)`,
capped at 5000 (found necessary — see bug below).

**(1) Implementation**: `scripts/fix_clock_operator_sweep.py`. Builds
each operator's `H` via `analysis._operator_registry` (same registry
`sweep_operators.py` already uses), computes `gap`/`t*`/`n*` from `H`'s
own `eigvalsh`, and calls `analysis.operator_sweep` per-cell with the
per-operator `t*` — reuses `sweep_operators.py`'s own `_prepare_target`
(fetch/clean/labels) rather than re-deriving it. Loads each cell's OLD
result directly from TASK-0101's already-computed `results/<target>/
sweep_cells/*.json` for a side-by-side comparison (old column not
recomputed).

**Found and fixed a real bug before trusting any CARDIAC_MYOSIN result**:
`CARDIAC_MYOSIN H9`'s tiny gap (0.00776) drives `t*=593`, and its own
bandwidth then drives `min_adequate_n_steps` to **3,095,469,321** —
`MemoryError: Unable to allocate 23.1 GiB` when passed into
`time_averaged_ctqw` (caught gracefully by `operator_sweep`'s existing
per-cell error handling, so it didn't abort the sweep — but wasted the
cell). Same class of fragility TASK-0109's own battery already found and
capped for the identical reason (near-degenerate/small-gap spectra blow
up the Nyquist prediction) — added `N_STEPS_PRACTICAL_CAP=5000` here
too, flagged (`n_steps_capped: true`) in the output whenever hit, not
silently under-sampled without a record of it. Re-ran after the fix: H9
now scores normally (n_steps 3.1B→5000, capped).

**(2) 96-cell sweep re-run** (all 3 mandatory targets, `results/tasks/0119/
clock_fix_sweep.json`/`report.md`) — **two separate, explicit findings,
per this task's own "must NOT conclude" constraint**:

- **Ranking shift, real and target-dependent, not uniform**: KRAS_G12C
  1 floor-status flip (`H14`/ground_state), BCR_ABL1 3 new floor-clears
  (`H10`/`H12`/`build_H10`, all `ctqw`), **CARDIAC_MYOSIN 10 floor-status
  flips, all losses** (`H2`,`H3`,`H4`,`H5`,`H6`,`H8`,`H11`(both),`H12`
  `ctqw` + `H7`/ground_state — all `True→False`). This directly narrows
  TASK-0109's own headline ("20 of 96 cells clear the floor, 11 via
  `ctqw`, all on CARDIAC_MYOSIN"): **most of those 11 `ctqw` clears do
  not survive the clock fix** — `t_max=15` was simply too short for
  those specific operators' large gaps, producing under-converged AUCs
  that happened to clear the floor by coincidence, not by real signal.
  The two Tier-A survivors, `H_new` and `H10`/`build_H10`, keep their
  floor-clearance under the corrected clock (`t*=131`/`9.86` respectively
  vs. the shared `15`) — **the part of TASK-0109's finding that concerns
  this project's actual submission candidates is robust to this fix; the
  part concerning the other 9 Tier-B operators mostly was not.** This is
  a real, load-bearing narrowing of TASK-0109's own headline — flagged
  here and in `RESULTS.md`, not silently left standing.
- **Operator gap/`t*` itself is informative, independent of AUC**:
  `H_new`'s `t*` is consistently far smaller than the bare/weakly-
  disordered operators' at every target (e.g. BCR_ABL1: `H_new` 23.8 vs.
  `H7` 2580, `H11` 14000; CARDIAC_MYOSIN: `H_new` 131 vs. `H7` 11900,
  `H11` 62000) — `H_new`'s trap creates an isolated, well-separated,
  fast-converging ground state (large gap), while the bare/weakly-
  disordered operators have near-degenerate low-lying spectra (tiny gap,
  huge `t*`). This is an independent, mechanistic corroboration of the
  localization finding below, visible in the clock computation itself
  before any AUC is even scored.

**(3) TASK-0106's BCR_ABL1 trapping reproduction, re-run**
(`results/tasks/0119/trapping_reproduction_fixed_clock.json`) — same seed
convention as TASK-0106's own canonical run (single sorted-first
active-site index; see the TASK-0118 caveat below for why this wasn't
switched), same floor (0.5652, confirmed identical — floor doesn't
depend on `t_max`). Full numbers and the resolution of TASK-0106's own
flagged PR-direction question are in **TASK-0106's own Done section**
(additive addendum, this task's "Secondary correction" requirement) —
summary: **the panel's correction was itself mistaken** (conflated
`metrics.ipr` with `analysis._transport_participation_ratio`, opposite
conventions, verified in a new regression test,
`tests/test_transport_diagnostics_convention.py`); TASK-0106's original
narrative was directionally correct for the metric it actually used.
Under the per-operator clock, the localization conclusion survives
(`H_new` ipr 6-10x `H10`/`H2`'s at each operator's own proper
convergence time) and `H10` newly clears the real floor at its own `t*`
— reported as the same two separate findings (ranking shift vs.
localization survival) as (2) above, per this task's own explicit
Constraint not to merge them.

**Caveat, found mid-task, not swept under the rug**: `run_challenge.py`
was updated (uncommitted, another thread's in-progress work, observed
live in this shared working tree) mid-way through this task to
[[TASK-0118]]'s new canonical seed convention (full active-site array,
incoherent statistical mixture, not the single scalar index this task's
re-runs still use) — this task's own Dependency section anticipated
exactly this ("should ideally run after TASK-0118... so the re-run isn't
done twice under two different seed conventions — soft ordering, not a
hard block") and explicitly authorized proceeding without waiting. Every
number in this Done section and TASK-0106's addendum is therefore
computed under the **pre-TASK-0118 seed convention** (single index) —
correct and internally consistent for the old-vs-new clock comparison
this task asks for, but **not yet under both fixes at once**. A further
re-run combining the corrected clock (this task) and the corrected seed
(TASK-0118) is needed before either fix's numbers are read as this
project's final, submission-facing state — flagged here as the explicit
next step, not filed as a new task number since it is squarely a
re-application of two already-built tools, not new design work.

**Not attempted, explicitly out of this task's own scope**: reselecting
any submission operator (Tier-2-gated, TASK-0100); the seed-gauge fix
itself (TASK-0118, separate task); building `check_convergence` (TASK-
0109, already done, consumed here).

**Tests**: `tests/test_transport_diagnostics_convention.py` (3 new,
pinning the `ipr` vs. `_transport_participation_ratio` opposite-
convention finding — the concrete regression guard for (3) above).
Existing suite unaffected (no `src/allostery/*.py` production code
changed by this task — only new scripts/tests/docs).
