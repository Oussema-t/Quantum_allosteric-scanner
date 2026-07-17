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
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
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
     recomputed under its own seed fix alone (`results_task0118/`,
     `results_task0118_ceiling/`) — re-run those same three quantities,
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

- [ ] Decide which existing script to extend (TASK-0118's or TASK-0119's)
      — state choice and why in Done.
- [ ] Re-run the 96-cell operator sweep under both fixes combined.
- [ ] Re-run floor/ceiling/actual (competence map) under both fixes
      combined, all 3 mandatory targets.
- [ ] Reconcile against TASK-0110's BCR_ABL1 short-`t_max` finding
      (0.5829 at `t_max=2.39`) — report agreement or tension explicitly.
- [ ] Full recompute of `COMPETENCE_MAP.md`, additive, citing this task.
- [ ] Report a side-by-side table isolating each fix's individual and
      combined effect on every headline number.

## Dependency

- Hard: [[TASK-0118]] (Done) and [[TASK-0119]] (Done) — both landed,
  this task is now unblocked.

## Open Questions

- None — scope is fully specified by the two source tasks' own explicit
  callouts.

## Done

(not yet)
