# TASK-0145 Quantum transport / effective-conductance observable (Landauer-Büttiker transmission + classical effective resistance)

## Context

- ID: TASK-0145
- Title: reframe the scoring question from "where does an excitation
  seeded at the active site spread to over time" (every observable this
  project has tried) to "what is the steady-state current/transmission
  from the active site to each candidate residue" — a non-equilibrium
  steady-state (NESS) transport calculation, the formalism used in
  molecular electronics (Landauer-Büttiker; Nitzan & Ratner's quantum
  transport reviews) rather than a seeded-walk-and-wait one.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: raised by the orchestrating user, 2026-07-20, as an open
  "what's still worth trying" question; this Architect/Planner thread's
  own analysis rated it the highest-plausibility remaining idea
  precisely because it has a structural argument (not just "different
  math") for why it might not inherit the proximity confound — the same
  shape of argument that made chiral circulation (TASK-0140) the one
  idea that escaped it before its own gating premise failed.
- Priority: **P1.** Complements, does not duplicate, [[TASK-0136]]'s
  percolation/edge-connectivity work — that is a discrete, combinatorial
  connectivity measure; this is a continuous conductance/transmission
  measure. Both test "is communication distributed or bottlenecked,"
  from genuinely different mathematical angles.

## Intent Contract

- Outcome: two related quantities, built in order (cheapest, most
  well-established first):
  1. **Classical effective resistance/conductance** between the active
     site and each candidate residue — closed-form, no simulation:
     `R_eff(i,j) = L^+_ii + L^+_jj - 2*L^+_ij`, where `L^+` is the
     Moore-Penrose pseudo-inverse of the graph Laplacian. **This is
     nearly free to compute** — `H14_anm_pinv_trace` already computes
     `L^+`'s trace via `np.linalg.pinv`; this task needs the full matrix,
     not just its trace, reusing the same decomposition. Score
     `1/R_eff(active_site, j)` (conductance, higher = better connected)
     per candidate residue `j`.
  2. **Quantum generalization**: a Landauer-Büttiker-style transmission
     `T(E) = Tr[Gamma_L G(E) Gamma_R G(E)^dagger]` using the retarded
     Green's function `G(E) = (E - H + i*eta)^-1` at a stated energy `E`
     (start with `E=0` and/or the walk's own natural energy scale from
     `H`'s spectrum — state the choice and why), with `Gamma_L`/
     `Gamma_R` as simple broadening/coupling terms at the source and
     candidate sites (state the exact coupling model chosen — a minimal,
     standard choice, e.g. a small imaginary self-energy at the source/
     drain sites, is acceptable; do not invent an elaborate lead model
     without justifying it against the literature cited above).
  3. **Report whether the quantum transmission differs meaningfully from
     the classical effective resistance**, per this project's own
     "effectively decoherent" precedent (`time_averaged_ctqw`'s own
     finding that its converged limit is provably phase-free) — if `T(E)`
     reduces to (or tracks) `1/R_eff` closely, that is itself an honest,
     reportable finding ("the quantum transmission calculation is
     classical here too"), not a failure to hide.
- Why required, not assumed: effective resistance already accounts for
  *all* parallel paths between two nodes, weighted by strength — a
  genuinely different mathematical object from graph-hop distance
  ([[TASK-0136]]) and from CTQW occupation (everything else). Whether
  either quantity is less proximity-confounded than what's already been
  tried is an empirical question this task answers, not assumes.
- In Scope:
  - Implement effective resistance/conductance from `L^+` (reuse
    `H14_anm_pinv_trace`'s existing pseudo-inverse call, do not
    re-decompose).
  - Implement the Green's-function transmission calculation, stating the
    lead/coupling model choice explicitly.
  - Synthetic falsification gate first, per this project's own standing
    discipline (e.g. the dumbbell construction, [[TASK-0103]] — does
    either quantity track coupling strength, not just well-depth or
    proximity, on a constructed case before trusting real data).
  - Score both quantities on all 3 mandatory targets against
    [[TASK-0094]]'s proximity floor, with block-bootstrap CIs
    ([[TASK-0112]]) and a permutation null on any max-over-something
    step (this project's own standing requirement, per
    `.ai/reference/IMPLEMENTER_SPINUP_BRIEF.md`).
- Out Of Scope:
  - Reselecting the submission operator (Tier-2-gated, [[TASK-0100]]).
  - A full multi-lead/multi-terminal transmission network — a two-
    terminal (source, one candidate at a time) calculation is sufficient
    to answer this task's own question.
- Constraints And Invariants: state the energy `E` and lead-coupling
  model explicitly in Done — these are real modeling choices, not
  free parameters to tune against labels.
- Planned Validation: the dumbbell gate first; then real-target scoring
  against the proximity floor, reported whichever way it comes out.

## In Progress

None

## TODO

- [ ] Implement effective resistance/conductance from `L^+` (reuse
      existing pseudo-inverse machinery).
- [ ] Implement Green's-function transmission `T(E)`, stating the lead/
      coupling model and energy choice.
- [ ] Synthetic falsification gate (dumbbell or equivalent) before real
      data.
- [ ] Score both quantities, all 3 mandatory targets, vs. the proximity
      floor, with CIs and a permutation null.
- [ ] Report whether `T(E)` differs meaningfully from classical `1/R_eff`
      — an honest "it's classical here too" is a valid outcome.

## Dependency

- [[TASK-0094]] (Done) — proximity floor.
- [[TASK-0103]] (Done) — dumbbell falsification gate.
- [[TASK-0112]] (Done) — bootstrap CI.
- Reuses `H14_anm_pinv_trace`'s pseudo-inverse computation.

## Open Questions

- Exact lead/coupling model for the Green's-function calculation — not
  pre-decided; Implementer's call, state the choice and why in Done.
- Energy `E` at which to evaluate `T(E)` — state the choice; report
  sensitivity if it materially changes the verdict.

## Done

(not yet)
