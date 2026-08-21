# TASK-0129 Combined re-run: TASK-0118's seed convention + TASK-0119's per-operator clock, together

## Context

- ID: TASK-0129
- Title: [[TASK-0118]] (seed gauge fix: full active-site array,
  incoherent mixture) and [[TASK-0119]] (clock fix: per-operator
  `t* = -ln(tol)/gap`) landed **independently and concurrently** on
  2026-07-16, each fixing a different confound, neither combined with
  the other. Every number either task reports is therefore computed
  under **one** fix at a time, not both — re-run the 96-cell operator
  sweep and the floor/ceiling/actual competence-map numbers under both
  fixes simultaneously.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer A (this thread)
- Claimed At: 2026-07-17 23:11
- Source: explicitly flagged as the necessary next step by both source
  tasks' own Done sections, neither of which filed it (correctly, per
  their own scope discipline — this is "a re-application of two
  already-built tools, not new design work," per TASK-0119's own
  words). Filed by this Architect/Planner thread, 2026-07-16/17, while
  reviewing post-panel-review status.
- Priority: **P0 — the current single highest-value next step.** Every
  number in `COMPETENCE_MAP.md`/`RESULTS.md` right now is still
  gauge-contaminated by whichever of the two confounds its own re-run
  didn't fix.

## Intent Contract

- Outcome: re-run, under **both** the full-array/incoherent-mixture
  seed convention (TASK-0118, already wired as `coherent=False` through
  `analysis.quantum_vs_classical`/`benchmark`, `ceiling.consistency_
  score`/`ceiling_search`, `protocol.run_frozen_verdict`) **and** the
  per-operator `t*` (TASK-0119's `min_adequate_t_max`, already
  implemented in `propagators.py`/exercised by `scripts/
  fix_clock_operator_sweep.py`):
  1. [[TASK-0101]]'s 96-cell operator sweep (all operators × both
     propagators × 3 targets), combining TASK-0119's per-operator `t*`
     computation with TASK-0118's seed convention (currently
     `fix_clock_operator_sweep.py` still uses the pre-TASK-0118 seed,
     per TASK-0119's own explicit caveat).
  2. The floor/ceiling/actual competence-map numbers TASK-0118 already
     recomputed under its own seed fix alone (`results/tasks/0118/`,
     `results/tasks/0118_ceiling/`) — re-run those same three quantities,
     same three targets, now also under TASK-0119's per-operator `t*`
     rather than the shared `t_max=15` TASK-0118's own re-run still
     used.
  3. Report explicitly, per both source tasks' own stated constraint,
     which of any observed change traces to which fix — do not present
     a single combined delta without attribution to seed vs. clock vs.
     their interaction.
- Why this matters beyond tidiness: TASK-0118's KRAS_G12C "ceiling
  clears floor by +0.045" and TASK-0119's "H_new/H10 floor-clears
  survive the clock fix, most of CARDIAC_MYOSIN's `ctqw` clears do not"
  are currently two separate, partial pictures. Until combined, neither
  is the pipeline's actual current state — `COMPETENCE_MAP.md` itself
  already flags this in its Open Items.
- In Scope:
  - Re-run using existing tooling only — `scripts/fix_clock_operator_
    sweep.py` (TASK-0119) updated to consume `coherent=False`/full-array
    seeding (TASK-0118), or `scripts/seed_convention_sweep.py`
    (TASK-0118) updated to consume per-operator `t*` (TASK-0119) —
    Implementer's call on which script is the better base to extend,
    state the choice in Done.
  - Re-run TASK-0110's own flagged BCR_ABL1 short-`t_max` finding
    (practical ceiling 0.5829 at `t_max=2.39`, smaller than the shared
    default) in this combined context — check whether TASK-0119's
    per-operator `t*` for `H_new` on BCR_ABL1 (23.8, per TASK-0119's own
    Done section) is consistent with or in tension with that shorter
    Optuna-found optimum; report the relationship explicitly, don't
    silently reconcile or silently ignore the discrepancy.
  - Full recompute of `COMPETENCE_MAP.md` under the combined state,
    additive per this project's no-silent-overwrite convention.
- Out Of Scope:
  - Building any new fix — this task applies two already-built ones
    together, it does not design a third.
  - `mode_coparticipation`/potential renormalization ([[TASK-0121]]/
    [[TASK-0122]]) — separate confound axis entirely.
- Constraints And Invariants: every reported number must state both its
  seed convention and its clock convention — no bare number without
  both labels, given this exact ambiguity is what this task exists to
  resolve.
- Planned Validation: side-by-side table (old shared-clock/mixed-seed,
  TASK-0118-only, TASK-0119-only, combined) for every headline
  floor/ceiling/actual number, so the incremental effect of each fix
  and their combination is directly readable, not just the final state.

## In Progress

None

## TODO

- [x] Decide which existing script to extend (TASK-0118's or TASK-0119's)
      — state choice and why in Done.
- [x] Re-run the 96-cell operator sweep under both fixes combined.
- [x] Re-run floor/ceiling/actual (competence map) under both fixes
      combined, all 3 mandatory targets.
- [x] Reconcile against TASK-0110's BCR_ABL1 short-`t_max` finding
      (0.5829 at `t_max=2.39`) — report agreement or tension explicitly.
- [x] Full recompute of `COMPETENCE_MAP.md`, additive, citing this task.
- [x] Report a side-by-side table isolating each fix's individual and
      combined effect on every headline number.

## Dependency

- Hard: [[TASK-0118]] (Done) and [[TASK-0119]] (Done) — both landed,
  this task is now unblocked.

## Open Questions

- None — scope is fully specified by the two source tasks' own explicit
  callouts.

## Done

- 2026-07-17/18, Implementer A.

**1. Script choice**: extended [[TASK-0119]]'s `scripts/fix_clock_operator_sweep.py`
in place (not [[TASK-0118]]'s `seed_convention_sweep.py`), since it already had the
harder half built (per-operator `t*`/`n*` from `H`'s own spectrum, `operator_sweep`
per-cell invocation, `N_STEPS_PRACTICAL_CAP` handling) — adding TASK-0118's seed fix
on top was the smaller delta. Added a new local `_prepare_target_combined` (full
active-site array) rather than mutating `sweep_operators.py`'s shared `_prepare_target`
(that function is also TASK-0101's own original-sweep record of truth; changing it in
place would silently redefine what "old" means for future reads). Threaded
`coherent=False` into every `operator_sweep(...)` call. The pre-existing clock-only
comparison columns (`results/tasks/0119/`) are unchanged on disk, loaded as a second
comparison column (`clock_only`) alongside `old` (TASK-0101) and the new `combined`
column — a 3-way per-cell comparison, not just old-vs-new.

**2. Root capability**: added `coherent: bool = True` to `analysis.operator_sweep`
(the one Tier-1 sweep function TASK-0118 had not touched), threaded into its `"ctqw"`
propagator lambda only (`"ground_state"` unaffected, already an incoherent classical
mixture by construction). Default preserves every existing caller byte-identically.
1 new test (`TestOperatorSweep::test_coherent_flag_reaches_ctqw_not_ground_state`,
spy-based — AUC-level comparison hit the same rank-invariance-on-small-fixtures issue
TASK-0118's own tests already worked around).

**3. Real combined runs, all real network fetches, no synthetic substitutes**:
- **96-cell operator sweep** (`results/tasks/0129/combined_sweep.json`/`report.md`) —
  all 3 targets, ~28 min total wall time (CARDIAC_MYOSIN's `ctqw` column dominates,
  per-cell costs pre-estimated from a single worst-case timing probe before committing
  to the full run, per this project's own "check feasibility before a long run"
  precedent).
- **Competence-map re-run** (`results/tasks/0129_competence/combined_competence.json`,
  new standalone script `scripts/combined_competence_map_rerun.py`) — calls
  `protocol.run_frozen_verdict`/`ceiling.ceiling_search` directly with the combined-fix
  parameters, deliberately *not* an edit to `run_challenge.py`'s/
  `ceiling_search_batched.py`'s own live defaults (matches TASK-0119's own precedent of
  treating that as a separate, later decision; this task's own Out Of Scope forbids
  "building a third fix," which promoting a research clock into the live pipeline
  would arguably be). **Stated simplification**: `H_new`'s own default-config `t*`/`n*`
  is applied uniformly to both benchmark candidates and every one of the ceiling
  search's 60 (differently-parameterized) trials — the same "one `t*` per operator, not
  per-configuration" simplification TASK-0119's own Intent Contract already made for
  the 96-cell sweep, extended here one step further and stated explicitly, not hidden.
  `H10`'s own, potentially different, `t*` is not separately computed (flagged in
  `COMPETENCE_MAP.md`'s Open Items).
- **BCR_ABL1 trapping reproduction, combined** (`results/tasks/0129/
  trapping_reproduction_combined.json`) — same 4 operators as TASK-0106/TASK-0119's own
  reproductions, now full-array + per-operator `t*` together.

**4. Headline finding**: **CARDIAC_MYOSIN's "actual clears its own floor, +75.1%
headroom" (TASK-0118 alone) does not survive combining the clock fix.** `H_new`'s true
convergence time for this target is `t*=198` (vs. the shared `t_max=15` TASK-0118's own
re-run still used) — under the correct clock, actual AUC drops from 0.8310 to 0.7912,
landing 0.0009 *below* its own floor (0.7921): headroom flips from +75.1% to −1.4%.
Independently cross-validated via a completely separate code path
(`analysis.operator_sweep`'s own `H_new`/`ctqw` cell in the 96-cell sweep: 0.7912,
matching to 4 decimals) — not a bug in one script. **Under the fully combined fix, no
mandatory target's shipped actual result clears its own floor** — KRAS_G12C and
BCR_ABL1 are chance-indistinguishable/below-floor (unchanged in kind); real ceiling
headroom exists for all three targets (KRAS +0.122, BCR_ABL1 +0.090, CARDIAC_MYOSIN
+0.064) but is reached by none of them. This is the single most load-bearing finding
this task produced — it reverses what had briefly been the submission's only positive
result, for a reason (the clock, not the seed) neither of the two source tasks alone
could have surfaced.

**5. TASK-0110 reconciliation** (per this task's own explicit In Scope item): TASK-0110's
own AUC-optimal `t_max=2.39` for BCR_ABL1 (`coherent=True`, `H_new` default params)
scores 0.5829 — *better* than this task's combined result at the numerically-motivated
convergence time (0.5305 at `t*≈123`, `coherent=False`). **Reported as a real, unresolved
tension, not reconciled**: propagating BCR_ABL1's `H_new` operator toward its true
decoherent limit appears to hurt discrimination here, not help it, and the best-known
discriminating time point is far shorter than any convergence criterion this project has
built would prescribe. Fully reconciling this would require a `coherent=False` re-run of
TASK-0110's own Optuna `t_max`/`n_steps` search — a distinct piece of work ("designing a
third fix"), explicitly out of this task's own scope; flagged in `COMPETENCE_MAP.md`'s
Open Items instead.

**6. Found and flagged, not chased (a numerical-stability question, not a seed/clock
question)**: `H_new`'s BCR_ABL1 spectral gap, freshly computed twice in the current
environment via two independent code paths, is internally consistent (`gap=0.0374`,
`t*=123.1`) but disagrees with [[TASK-0119]]'s own recorded value for the identical
computation (`gap=0.1933`, `t*=23.8`) on confirmed byte-identical `coords`/`bfactors`/
`cutoff` input. Root-caused as far as this task's own scope allows: BCR_ABL1's `H_new`
ground state sits in a genuine near-continuum (lowest 8 eigenvalues packed within a
0.14 span, each consecutive gap only 0.016–0.05 apart), making *which* pair of
eigenvalues numerically resolves as "the gap" plausibly sensitive to environmental
numerical variation (BLAS threading/reduction order) for this specific operator/target
— not investigated further (would require controlling for BLAS thread count/library
version across the two runs, a genuinely separate numerical-stability question).
Reported in `COMPETENCE_MAP.md`'s BCR_ABL1 section and Open Items, not silently smoothed
into a single number. Used my own directly-reproduced value (123.1) for this task's own
combined numbers, since it is the one independently confirmed in the current environment.

**7. `COMPETENCE_MAP.md` fully recomputed**, additive per this project's no-silent-
overwrite convention (TASK-0104's precedent) — a second `SUPERSEDED` banner stacked on
top of TASK-0118's own (which itself stacked on the original), the new combined table
+ sources, per-target addenda (not rewrites) to all three mandatory-target sections, a
rewritten Cross-target Reading with the old TASK-0118-only reading preserved as its own
subsection, and an updated Open Items list. Old numbers at every layer remain readable,
not deleted.

**Tests**: 1 new (`operator_sweep`'s `coherent` wiring). Full `test_analysis.py`
(non-network subset) — 50 passed, no regressions from the `operator_sweep` signature
change. Not run through `pytest_local.py wip-all` this session (targeted files only,
established precedent).

**Not attempted, explicitly out of this task's own scope**: promoting the combined
clock/seed convention into `run_challenge.py`'s/`ceiling_search_batched.py`'s own live
defaults (a Tier-2-adjacent decision, TASK-0100, and "building a third fix"); resolving
the TASK-0110 tension or the BCR_ABL1 gap-reproducibility question (both flagged, not
chased); computing `H10`'s own separate `t*` for the competence-map axis; re-running
TASK-0081's ASD generalization targets under the combined convention.
