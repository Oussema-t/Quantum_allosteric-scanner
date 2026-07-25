# TASK-0156 Control-effort scanning (minimum-energy reachability) as a per-residue allostery observable

## Context

- ID: TASK-0156
- **Renumbered 2026-07-25 (Architect/Planner)**: filed as TASK-0153 by
  `REVIEW-2026-07-23-register-hygiene-and-p12-gate.md`; collided with an
  already-committed, already-Done TASK-0153 (holo-diagnostic
  transport/lowmode extension, widely cross-referenced from
  `RESULTS.md`/`COMMON.md`/TASK-0145/TASK-0149's own Done sections).
  Renumbered here rather than the other way — the holo-diagnostic task's
  number had already propagated into 4+ live documents; this task had
  propagated into none (still unclaimed TODO). No content changed.
- Title: rank residues by the *minimum control energy* required to steer
  the CTQW's population from the active-site seed to each candidate
  residue, rather than by where the uncontrolled walk deposits
  probability. The control field is a probe; the readout is its cost.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: raised by the orchestrating collaborator (Oussama), 2026-07,
  as "phase-controlled CTQW to reduce trapping and improve ranking."
  **Re-scoped by this planning thread before filing** — see the
  correction below — from control-as-cure to control-as-ruler, which is
  the only version that is both well-posed and non-circular.
- Priority: **P2.**

## Correction to the original framing — read before implementing

The original framing ("dynamically control phases to eliminate
destructive interference and reduce trapping, then read where the walker
lands") is **not** filed as stated, for two reasons that are theorems,
not opinions:

1. **"Minimise destructive interference" is not a well-defined
   objective.** Interference is not an observable; it is basis- and
   gauge-dependent (a local phase rotation `|j> -> e^{i theta_j}|j>`
   changes per-path phases while leaving every measurable probability
   invariant). No gradient-based optimal-control method (GRAPE/CRAB/
   Krotov) can target a quantity that changes under a transformation
   that changes nothing measurable.
2. **The controllability paradox.** If a control field is strong enough
   to redirect amplitude to a chosen residue, the final state reflects
   the control field, not the protein — and controllability theory
   (Albertini & D'Alessandro 2012, *Math. Control Signals Syst.* 24,
   321-349, DOI 10.1007/s00498-012-0084-0 — verify before building)
   states a sufficiently connected graph can be driven anywhere. Signal
   about the protein -> 0 as control -> success.

**The reformulation that survives both:** do not use control to improve
the walk. Read out the *cost of control itself*. For each residue `i`,
compute the minimum control energy `E_i = min_u integral ||u(t)||^2 dt`
required to transfer population from the active-site seed to `i` at
fidelity >= F within horizon T, under `H(t) = H_0 + sum_m u_m(t) H_m`
(H_0 = this project's existing operator; H_m = local node-potential
shifts and/or real coupling modulations). Low `E_i` = residue strongly
dynamically coupled to the active site = candidate allosteric site.
This is well-posed (standard minimum-energy optimal control, gradient
available via GRAPE — Khaneja et al. 2005, *J. Magn. Reson.* 172,
296-305, DOI 10.1016/j.jmr.2004.11.004 — verify before building),
non-circular (computed identically for every residue; the pocket is
never named), and directional (`E_{a->i} != E_{i->a}` in general, unlike
the symmetric average-mixing matrix). It is the quantum analogue of
Perturbation-Response Scanning (Atilgan & Atilgan 2009, *PLoS Comput.
Biol.* 5, e1000544, DOI 10.1371/journal.pcbi.1000544 — already in the
register's citation set), which is also the classical baseline it must
beat.

## Intent Contract

- Outcome: a per-residue score `E_i` (minimum control energy from the
  active-site seed), computed via GRAPE against the existing `H_new`/
  contact-graph `H_0`, reused converged-limit or a stated finite T.
  Report as a candidate-ranking observable AND its distance-correlation
  diagnostic.
- Why required, not assumed: this is the only proximity-orthogonal-*by-
  construction* control observable that is also non-circular; whether it
  actually separates allosteric residues from distance is untested, and
  the most likely failure mode (below) is cheap to detect.
- In Scope:
  - Verify the three citations directly before implementing against them
    (per `.ai/reference/IMPLEMENTER_SPINUP_BRIEF.md` discipline).
  - Implement minimum-energy GRAPE control on the existing single-
    particle propagator; no new Hamiltonian family.
  - **Pre-registered kill-switch (run FIRST, before any scoring):**
    on KRAS (4OBE), compute `E_i` for all residues and correlate with
    graph-hop and Euclidean distance from seed. If `|rho| > 0.85` ->
    STOP and record as a distance proxy (the whole idea dies cheaply,
    one afternoon). If `|rho| < 0.6` -> proceed.
  - **Primary readout is the TASK-0123 distance-STRATIFIED AUC**, not
    whole-graph AUC — the PRS analogy predicts whole-graph AUC near
    chance even on success (see 2026-07-22 review, Method A: mode-
    filtered PRS collapsed rho 0.71->0.08 but sat at chance whole-graph;
    signal only under the stratified lens). Pre-register stratified AUC
    as primary so the task gives a clean answer either way.
  - Score all 3 mandatory targets vs. the proximity floor, with CIs and
    a permutation null; then ASD unseen set with multiplicity correction
    if the mandatory set clears.
- Out Of Scope:
  - "Minimise destructive interference" as an objective — killed above.
  - Any RL / learned control policy — established as no-advantage in the
    model-known, differentiable regime (Bukov et al. 2018, *PRX* 8,
    031086); adds an overfitting surface to the falsification apparatus.
    A pure gradient (GRAPE) baseline only.
  - Reselecting the submission operator (Tier-2-gated, [[TASK-0100]]).
- Constraints And Invariants: the horizon T, fidelity threshold F, and
  control-operator set are fixed once, stated, and blind to labels.
  Report ranking sensitivity to T and F — a ranking that flips with T is
  not a measurement.
- Planned Validation: synthetic dumbbell gate (does `E_i` track planted
  coupling at equal distance?) BEFORE real data; then the kill-switch;
  then stratified scoring.

## In Progress

None

## TODO

- [ ] Verify the Khaneja/Albertini/Atilgan citations directly.
- [ ] Implement minimum-energy GRAPE control on the existing propagator.
- [ ] Synthetic dumbbell gate: `E_i` tracks coupling at equal distance.
- [ ] Kill-switch: `rho(E_i, distance)` on KRAS; stop if `|rho|>0.85`.
- [ ] Stratified-AUC scoring (primary) on 3 mandatory targets vs floor,
      CIs, permutation null.
- [ ] ASD unseen set with multiplicity correction if mandatory clears.
- [ ] Report whichever way it comes out, incl. the honest caveat that a
      positive is a better OBSERVABLE, not a quantum speedup (single-
      particle, classically simulable).

## Dependency

- [[TASK-0094]] (Done) — proximity floor.
- [[TASK-0112]] (Done) — bootstrap CI.
- [[TASK-0123]] — distance-stratified AUC (the primary lens here).
- [[TASK-0130]] (Done) — converged-limit propagator, reusable.

## Open Questions

- Control-operator set (node potentials only vs. + coupling modulation)
  — Implementer's call, state and justify.
- Score at converged limit vs. finite physically-motivated T — state the
  choice.

## Done

(not yet)
