# TASK-0148 Single-particle entanglement entropy across a spatial cut (localization-sensitive observable)

## Context

- ID: TASK-0148
- Title: compute the entanglement entropy of the CTQW's single-particle
  state across a spatial bipartition (a candidate residue's local
  neighborhood vs. the rest of the structure), as a per-candidate
  coupling/localization observable distinct from occupation, distance-
  stratified AUC, or anything else currently in the register.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: raised by the orchestrating user, 2026-07-20, as an open
  "what's still worth trying" question (originally framed as "quantum
  mutual information" between the active site and candidate residues).
  **Re-scoped by this Architect/Planner thread, 2026-07-20, to a cheaper,
  better-grounded, more tractable form** — see the correction below —
  rather than filed as originally framed.
- Priority: **P2.**

## Correction to the original framing — read before implementing

The original framing ("quantum mutual information between active site
and candidate residue reduced density matrices") implicitly assumed a
genuine multi-body (2-excitation or explicit density-matrix) construction
would be needed — the same class of machinery [[TASK-0122]]'s
`mode_coparticipation` work and the boson-walk discussion (2026-07-20
conversation, not filed) both required. **That is not actually necessary
here.** Single-particle entanglement entropy across a spatial cut is a
well-established, cheaper quantity in condensed-matter physics — it is
the standard diagnostic for localization vs. delocalization of a single
particle/excitation (area-law vs. volume-law entanglement scaling is
literally how Anderson localization is characterized in that
literature), computable directly from the existing single-particle
propagator amplitudes via a **correlation-matrix eigenvalue method**
(Peschel 2003, *J. Phys. A* 36, L205, "Calculation of reduced density
matrices from correlation functions" — verify this citation directly,
per this project's own citation-verification discipline, before building
against it) — **no new multi-body machinery required.** This directly
connects to, and can be read alongside, this project's own existing
Anderson-localization finding for `H_new`'s CTQW (REVIEW-2026-07-13c,
[[TASK-0106]]) — entanglement entropy across a cut isolating the seed's
own neighborhood is a natural, independent diagnostic of exactly the
localization phenomenon already reported there, now applied per-
candidate rather than globally.

## Intent Contract

- Outcome: for the CTQW's single-particle state at a given time (or the
  converged limit, [[TASK-0130]]), compute the two-point correlation
  matrix `C_ij = <i| rho |j>` restricted to a chosen subset `A`
  (a candidate residue's local neighborhood, defined consistently with
  this project's existing pocket/neighborhood conventions), diagonalize
  it, and compute the von Neumann entropy from its eigenvalues (Peschel's
  method — verify the exact formula against the cited paper directly).
  Report this per-candidate-region entropy as a coupling/localization
  score, and separately as a diagnostic read alongside
  [[TASK-0106]]'s own global localization finding.
- Why required, not assumed: this is a well-defined, real quantity, not
  yet computed anywhere in this project despite the raw ingredients
  (single-particle amplitudes, spatial partitions) already existing —
  whether it's informative about pocket location, or just another
  window onto the same localization/proximity structure already found,
  is untested.
- In Scope:
  - Verify the Peschel citation directly before implementing against it
    (PubMed/WebFetch, per this project's own standing discipline —
    `.ai/reference/IMPLEMENTER_SPINUP_BRIEF.md` §2).
  - Implement the correlation-matrix entanglement-entropy calculation,
    reusing existing propagator amplitudes (no new Hamiltonian, no new
    heavy multi-body machinery).
  - Define the spatial partition consistently (e.g. the candidate
    residue plus its own graph neighborhood at a stated hop radius —
    state the choice).
  - Synthetic falsification gate first (does the entropy actually track
    coupling/delocalization on a constructed case, e.g. the dumbbell or
    a simple two-region toy graph, before trusting real data).
  - Score against all 3 mandatory targets, the proximity floor
    ([[TASK-0094]]), with CIs ([[TASK-0112]]) and a permutation null on
    any max-over-partitions step.
  - Cross-read against [[TASK-0106]]'s own global localization finding —
    does a per-candidate entropy pick out anything [[TASK-0106]]'s
    global participation-ratio measurement didn't?
- Out Of Scope:
  - Genuine multi-particle/bosonic entanglement (the boson-walk idea
    discussed 2026-07-20, not filed) — a different, more expensive
    construction; do not conflate the two.
  - Reselecting the submission operator (Tier-2-gated, [[TASK-0100]]).
- Constraints And Invariants: the spatial-partition definition is fixed
  once, stated, and blind to labels.
- Planned Validation: the synthetic gate first; then real-target scoring,
  reported whichever way it comes out.

## In Progress

None

## TODO

- [ ] Verify the Peschel (2003) citation directly before implementing.
- [ ] Implement the correlation-matrix entanglement-entropy calculation.
- [ ] Define and justify the spatial-partition convention.
- [ ] Synthetic falsification gate before real data.
- [ ] Score all 3 mandatory targets vs. the proximity floor, with CIs
      and a permutation null.
- [ ] Cross-read against TASK-0106's own global localization finding.
- [ ] Report the result, whichever way it comes out.

## Dependency

- [[TASK-0094]] (Done) — proximity floor.
- [[TASK-0112]] (Done) — bootstrap CI.
- [[TASK-0106]] (Done) — the global localization finding this task's
  per-candidate version should be read alongside.
- [[TASK-0130]] (Done) — the converged-limit propagator this task can
  reuse directly.

## Open Questions

- Exact spatial-partition convention (hop radius around each candidate)
  — not pre-decided; Implementer's call, state the choice and why in
  Done.
- Whether to score at the converged limit or a finite, physically-
  motivated time — state the choice.

## Done

(not yet)
