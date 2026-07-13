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
- Status: Done
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

- ~~All four questions in "The question, concretely" above~~ **Resolved
  below.** One residual open question survives to the follow-up task: see
  TASK-0101's own Open Questions (the floor-clearing significance
  threshold, same open item TASK-0099 already flagged for its own
  `auc_range` threshold — the two should use one shared convention, not
  two independently invented ones).

## Done

**Grounding read before deciding:** `hamiltonians.py` (14 named operators,
`build_H_new`/`build_H10`), `run_challenge.py`'s own docstring (explicitly
disclaims inventing a new operator search space — "A real
coordinate-descent search over more variants is TASK-0046's job, out of
this script's scope"), `protocol.py` (`select_frozen_config`,
`leave_one_protein_out`, `frozen_context` — the existing config-selection
firewall, already wired once for TASK-0064), `test_hamiltonians.py`'s
`_LAPLACIAN_OPS` dict (a test-private name→callable registry — evidence a
real one doesn't exist yet at library level, confirming the Context's own
grep finding), and TASK-0096's Done section (source of the Tier
characterization below).

### 1. Where does the sweep live?

**Library function `analysis.operator_sweep(...)`, executed by a new,
thin `scripts/sweep_operators.py`. `run_challenge.py` is NOT extended.**

`run_challenge.py`'s own docstring already drew this line for TASK-0046
("out of this script's scope") — the same reasoning applies here by the
identical logic: `run_challenge.py` is the *submission* orchestrator, one
command → one verdict for a config that is already decided
(`H_new`/`H10`). It must stay that way; TASK-0083's forthcoming artifact
contract and TASK-0084's backend API both assume the submission pipeline
reports a decision, not a search. Loading a 14-operator research sweep
into it would blur "the artifact the jury sees run" with "the tool we
used to decide what to run." A library function matches the existing
precedent exactly — `analysis.benchmark`/`ablation`/`quantum_vs_classical`/
`gnm_cutoff_weight_sweep` are all library functions that TASK-0067 already
called directly (not through a script) to produce a real, reported
benchmark. `operator_sweep` is the same shape of thing, one more operator
axis. The thin script exists only so the sweep is a durable, rerunnable
command (`python scripts/sweep_operators.py <target>`) rather than a
paste-the-numbers-into-a-task-file one-off REPL session — reproducibility
for a 14-operator table matters more than it did for TASK-0067's 3-cutoff
one.

### 2. What does "rate the results" mean?

**Two explicit tiers — descriptive measurement is not the same act as
config selection, and only the second needs the frozen-config firewall.**

- **Tier 1 (descriptive, no frozen gate):** for every operator, on every
  mandatory target, report (a) whether it clears TASK-0094's proximity
  floor (`euclid_from_seed_centroid`/`hop_from_seed`/`degree_centrality`,
  the max-of-three convention TASK-0094 already established), (b) its raw
  AUC, (c) apo/holo consistency where TASK-0092 makes it available. This
  is pure measurement — nothing is being chosen, so `leave_one_protein_out`
  is not required, exactly as TASK-0067's cutoff/weight-scheme benchmark
  ran outside `frozen_context` and was correctly treated as diagnostic,
  not a selection act (that task's own Out Of Scope: "changing `backend`'s
  live default without a separate, explicit follow-up").
- **Tier 2 (selection, hard-gated):** if Tier 1's table is ever used to
  argue "operator X should replace `H_new`/`H10` as the submission's
  chosen operator," that argument **must** be re-derived inside
  `frozen_context`, via `leave_one_protein_out` across the 3 mandatory
  targets — the same firewall TASK-0064 already wired for exactly this
  class of decision. Mean-AUC-across-3-targets, computed outside the
  frozen gate, is **not sufficient** to justify swapping the submission
  operator — with only 3 mandatory targets, an un-gated pick is a
  three-point multiple-comparisons problem, precisely the overfitting
  shape TASK-0055/TASK-0088 already closed one instance of (freeze-
  provenance). **Explicitly flag N=3 as a thin cross-validation set** in
  any Tier-2 report — a resulting "winner" should be reported with that
  caveat, not oversold as a robust finding.

### 3. Does every operator need this? (Tiering)

**Three tiers, stated as policy so the sweep doesn't run with false
equal weight:**

- **Tier A — submission candidates, eligible for Tier-2 selection:**
  `H_new`, `H10_disorder_suppressed` (current), `H14_anm_pinv_trace`
  (added by TASK-0096 explicitly "for research purposes... let the sweep
  decide"). These three were each deliberately engineered as candidates.
- **Tier B — baseline/ablation family, Tier-1 only:** `H1`–`H9`, `H11`,
  `H12`, `H13`. Per TASK-0096's own characterization, these are notebook
  ablation scaffolding and a genuinely-ported-but-not-submission-intended
  local anisotropic formula (`H11`/`H12`) and the 3N-Hessian building
  block (`H13`) — none were built to be *the* submission operator.
  Included in Tier 1 for context (does `H_new` actually beat the simple
  baselines it's built from?) but **not eligible for Tier-2 selection** —
  promoting one of twelve never-intended-as-candidates operators via an
  un-gated 3-target sweep is the exact multiple-comparisons risk Tier 2's
  gate exists to prevent.
- Every Tier A and Tier B operator gets a Tier-1 row. Only Tier A
  operators can ever appear in a Tier-2 selection report.

### 4. What happens to an operator that doesn't clear the floor?

**Generalizes TASK-0096's own precedent as explicit policy, for every
tier:**

- Documented in the Tier-1 table regardless of outcome — a floor-failing
  operator is a recorded finding ("`H7` never clears the proximity floor
  on any mandatory target"), not silently dropped. Matches this project's
  established "an honest NO is a publishable result" convention
  (TASK-0082's own framing).
- A **Tier A** operator failing the floor on all 3 mandatory targets is
  **disqualified from Tier 2** — cannot become the submission operator,
  regardless of raw AUC, full stop.
- A **Tier B** operator failing is simply recorded as such — supports or
  refutes "the whole baseline family struggles here," useful methodological
  context either way, no disqualification to apply since it was never a
  candidate.
- **No operator is deleted from `hamiltonians.py` for failing the floor**
  — that would be a separate, stronger decision than "not eligible as
  submission operator," and TASK-0096 already made the opposite call
  (implement, don't delete, so the sweep itself can be the informative
  result).

### Resequencing (the question TASK-0100 explicitly asked me to make)

**TASK-0093 and TASK-0099 are NOT blocked by this decision — they are not
operator-selection acts.** TASK-0093 reconciles a cutoff/pocket-label
discrepancy for the *already-chosen* `H_new`; TASK-0099 wires a coherence
metric for the *already-chosen* `H_new`. Neither touches which operator is
"the" submission operator. TASK-0100's own caution ("do not start
implementing either as a workaround for the missing sweep") is satisfied
by this clarification — they were never a workaround for it, and can
proceed independently, in parallel with TASK-0101 below.

### Follow-up filed

**TASK-0101** — implement `analysis.operator_sweep` +
`scripts/sweep_operators.py`, run the **Tier-1 descriptive sweep only**
(all 14 operators × 3 mandatory targets, checked against TASK-0094's
floor) and report the table. Tier-2 selection is explicitly **not**
scoped into TASK-0101 — whether it's ever warranted depends on what
Tier 1 actually shows (if no Tier A operator meaningfully beats `H_new`,
there is nothing to select), so it is left for a future task, filed only
if Tier 1's results justify it.
