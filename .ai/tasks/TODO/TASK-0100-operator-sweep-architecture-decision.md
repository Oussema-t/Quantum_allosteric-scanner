# TASK-0100 Decide the shape of a real cross-operator sweep against the proximity floor

## Context

- ID: TASK-0100
- Title: We have 14 named Hamiltonian operators (`H1`-`H14`,
  `__WORK_IN_PROGRESS__/src/allostery/hamiltonians.py`) and a proximity
  floor to score against (`baselines.py`, TASK-0094), but **no runtime
  harness that ever runs more than two of them (`H_new`, `H10`) against a
  real benchmark target and rates the result.** This is a request for an
  Architect-level decision, not a bounded implementation slice — it
  determines what "passing the challenge" is actually allowed to mean.
- Status: TODO
- Owner: Architect/Planner
- Source: explicit user instruction, 2026-07-13 — "Please ask the
  Architect what we should do about the operator sweep. In my
  understanding - if we want to have a meaningful result, we should at
  some place perform a proper sweep and rate the results according to
  some metrics. Otherwise I do not understand how we would possibly pass
  the challenge." Filed by Implementer A per that instruction; this is a
  question routed to the Architect, not an Implementer decision made
  unilaterally.
- Immediate trigger: TASK-0096 (Done) implemented `H11`/`H12` for real
  (ported from `notebooks/H_new_engineering (4) CLEAN.ipynb`) and added a
  new `H14_anm_pinv_trace` research operator, specifically so a future
  sweep could judge them empirically. While closing that out, grep
  confirmed there is no `ALGORITHM_REGISTER`-style enumeration anywhere
  in `src/` or `scripts/` that iterates the H-family by name at runtime —
  see TASK-0096's Done section, "Scope note."

## Why this is bigger than one Implementer task

- `scripts/run_challenge.py` (the only end-to-end entry point that
  produces a scored verdict) hard-codes exactly two operators: `H_new`
  (the submission operator) and `H10_disorder_suppressed` (its one
  baseline comparison). `H1`-`H9`, `H11`-`H14` are exercised only by unit
  tests on synthetic 6-30-residue fixtures (`test_hamiltonians.py`) —
  never against a real PDB structure, never scored against a real pocket
  label, never checked against TASK-0094's proximity floor.
  `notebooks/H_new_engineering (4) CLEAN.ipynb` DOES run a real sweep
  (`build_operators`/`BENCH`/`OPT` in later cells) but that is exploratory
  notebook code, not the shipped pipeline, and predates the proximity
  floor entirely.
- This touches source-of-truth boundaries the Architect owns per
  `.ai/experts/architect-planner.md`: is the sweep's home
  `scripts/run_challenge.py` (extend the shipped pipeline), a new
  `scripts/sweep_operators.py` (separate exploratory tool, notebook-like),
  or does it belong upstream of both as a library function in
  `analysis.py`? Each choice has different implications for what the
  jury sees run and what "the submission" is claimed to be.
- It also sets policy for every currently-open operator-adjacent task
  (TASK-0093's KRAS discrepancy reconciliation, TASK-0099's
  coherence-metric wiring, and this task's own trigger) — those tasks
  keep re-deriving one-off comparisons against one target at a time
  without a shared harness or shared rating convention. Sequencing which
  comes first is an Architect call.

## The question, concretely

1. **Where does a real cross-operator sweep live?** (extend
   `run_challenge.py`, new script, or library-level).
2. **What does "rate the results" mean precisely?** — per TASK-0094, an
   operator must clear the proximity floor (`euclid_from_seed_centroid`,
   `hop_from_seed`, `degree_centrality`) to even be a candidate; beyond
   that, is ranking by mean AUC across the 3 mandatory targets
   (KRAS_G12C, BCR_ABL1, CARDIAC_MYOSIN) sufficient, or does it need the
   apo/holo consistency and cross-validation machinery already built in
   `superpose.py`/`protocol.py` (`leave_one_protein_out`,
   `frozen_context`)?
3. **Does every operator need this, or only submission candidates?** —
   `H14` was added explicitly as a "let the sweep decide" research
   operator (TASK-0096); `H1`-`H9`/`H11`-`H13` are baseline-family
   scaffolding the notebook itself used only for ablation, not as
   submission candidates. Worth stating which tier each operator is in
   before building the harness, so the sweep isn't run against every
   operator with equal weight by default.
4. **What happens to an operator that doesn't clear the floor?** — TASK-
   0096's own Intent Contract already answered this for H11/H12
   specifically ("if the sweep proves the operators to be useless — we
   will document the fact and remove/not use them" — user's words); this
   task should make that the general policy, not a one-off.

## Dependency

- Builds on TASK-0094 (Done — proximity floor exists to score against)
  and TASK-0095 (Done — propagator semantics are correct, so scores are
  trustworthy).
- Motivated by / follows TASK-0096 (Done — H11/H12/H14 exist and need
  somewhere real to be evaluated).
- Related open tasks that a sweep decision would likely resequence:
  TASK-0093 (KRAS AUC reconciliation), TASK-0099 (coherence-metric
  wiring) — do not start implementing either as a workaround for the
  missing sweep; flag the overlap for the Architect instead.

## Open Questions

- All four questions in "The question, concretely" above — this task
  file itself is the question, not a proposed answer. Architect/Planner
  should turn whichever parts are resolved into a follow-up Implementer-
  owned Intent Contract (new task) once the shape is decided, per the
  Operation Protocol's step 0-1 (Intake -> Intent Formulation).

## Done

(not yet)
