# TASK-0141 Engineered-dephasing (ENAQT) sweep — discrimination, not transport (HYP-P11)

## Context

- ID: TASK-0141
- Title: Sweep a Haken-Strobl pure-dephasing rate γ (QSW/Lindblad) on
  KRAS_G12C / BCR_ABL1 / PTP1B and test whether *any* γ improves pocket
  **discrimination** vs the proximity floor — the collaborator's Idea #1,
  run with the correct scored quantity and a pre-registered outcome
  ([[HYP-P11]]).
- Status: TODO
- Owner: Implementer (Oussama: build + run, as proposed in-thread).
  **Physics already sanity-checked this batch** (`enaqt_sanity.py`);
  the check's finding is recorded below as a *prior*, not a verdict to
  confirm — the agent runs the honest sweep and reports whatever occurs.
- Source: `REVIEW-panel-2026-07-20` §"physics check of Idea #1", and the
  collaborator's message (Mohseni-Rebentrost-Lloyd-Aspuru-Guzik 2008;
  Rebentrost 2009; Caruso 2014; Viciani 2015). Reuses the existing
  Haken-Strobl machinery ([[TASK-0041]]) and the coherence/ENAQT work
  already in the register.
- Priority: **P1.** Even a negative directly discharges the challenge's
  **noise-resilience** secondary objective and engages the ENAQT
  literature honestly. Independent of [[TASK-0143]]/[[TASK-0140]].
- **Flagged 2026-07-20 (Architect/Planner)**: `enaqt_sanity.py` (the
  synthetic sanity-check script cited above) is not present in this repo
  or the applied review batch — lower risk than [[TASK-0140]]'s missing
  script, since this task reuses `haken_strobl` (already real, built,
  and tested via [[TASK-0041]]) rather than porting a new function; the
  sweep itself can be built directly against that existing machinery.
  The *prior* recorded below (0.72→0.16 AUC collapse) is this batch's
  own synthetic finding, not yet reproduced by this Architect/Planner
  thread — treat as a stated expectation to test, not a confirmed fact,
  per this task's own framing.

## ⚠️ Before implementing — the scored quantity is DISCRIMINATION, not transport

The four cited references establish an *optimal dephasing rate for
transport efficiency* — excitation transfer to a *known* trap/sink in
light-harvesting. This project's objective is **discrimination**: ranking
*unknown* pockets above background. These are different quantities. The
physics prior (`enaqt_sanity.py`, this batch, synthetic distal loop
pocket): dephasing de-traps the walker from Anderson localization but does
so by pushing it toward **classical diffusion**, which *is* the proximity
confound — AUC stayed flat then collapsed (0.72→0.16 as γ: 0→5), while
ρ(occ,−dist) rose from +0.10 to +0.68, reaching +0.92 at the classical
limit. So the prior is: **no γ improves discrimination; the ENAQT
"optimum" optimizes the wrong metric.** Run it anyway — the prior is a
synthetic; real data may differ, and a rigorous, literature-anchored
negative is the deliverable either way. **Do NOT score transport
efficiency.** **Do NOT tune γ against known pockets.**

## Intent Contract

- Outcome: for each of KRAS_G12C / BCR_ABL1 / PTP1B, a γ-sweep curve of
  **discrimination AUC vs the proximity floor** (with CIs), plus the
  γ→∞ classical-limit sanity endpoint, and a pre-declared verdict on
  whether any γ delivers a real, floor-clearing discrimination gain over
  the coherent (γ=0) walk.
- Why required: [[HYP-P11]] is a clean, cheap, falsifiable claim that
  closes the "did you actually try engineered dephasing?" question the
  ENAQT literature invites, and it discharges the noise-resilience
  objective with a mechanism (relaxation-to-classical) rather than an
  assertion. The prior predicts a negative; the task exists to test it,
  not to confirm it.
- In Scope:
  - QSW/Lindblad Haken-Strobl pure dephasing (site-basis L_n=|n><n|):
    dρ/dt = −i[H,ρ] − γ(ρ − diag(ρ)). Operator-split integrator is fine
    (`enaqt_sanity.py` reference); reuse [[TASK-0041]]'s solver if it is
    numerically adequate for N~target sizes.
  - Sweep γ over >=8 points spanning the coherent limit, the ENAQT regime,
    and deep into the classical limit (e.g. {0, 0.05, 0.1, 0.2, 0.5, 1, 2,
    5} in units of H's bandwidth), on all three targets.
  - Score DISCRIMINATION: time-averaged site occupation → AUC vs the
    proximity floor, with block-bootstrap CIs ([[TASK-0112]]) and the
    distance-stratified lens ([[TASK-0123]]).
  - Report the localization length / participation ratio vs γ as the
    mechanistic covariate (ties the result to the confirmed Anderson
    localization in `H_new`), so a negative has an explanation.
- Out Of Scope:
  - Transport-efficiency metrics of any kind (trap-population,
    transfer time) — not the objective; explicitly excluded.
  - Any initial-phase / chiral component — that is [[TASK-0140]].
  - Selecting a "best γ" to ship (Tier-2 gated, [[TASK-0100]]); a γ that
    won on labels would be pure leakage.
- Constraints And Invariants:
  - **γ is never tuned against pocket labels.** The sweep grid is fixed up
    front; the reported optimum (if any) is read off the floor-relative
    AUC curve, and only counts if it clears the pre-registered bar.
  - **Classical-limit sanity check is mandatory**: at the largest γ the
    occupation must reproduce the classical-diffusion proximity signal
    (ρ(occ,−dist) → the classical floor's correlation, ≈+0.9 on the
    synthetic). If it does not, the integrator is wrong — this is the
    setup-validity gate, assert it before trusting any interior point.
  - Watch the Zeno regime (γ→∞ freezes coherent transport) but note the
    prior: discrimination dies at the *classical-diffusion* crossover,
    well before Zeno freezing — report which mechanism dominates.
- Planned Validation (**pre-registered**):
  - **POSITIVE (overturns the prior)** iff some interior γ yields an AUC
    that clears the proximity floor with non-overlapping 95% CIs AND beats
    the coherent γ=0 point, on >=1 target, surviving Bonferroni across the
    three. This would be a genuine, submission-folding result.
  - **NEGATIVE (confirms [[HYP-P11]])** iff no γ clears the floor / the
    AUC is flat-or-declining in γ / the optimum's CI overlaps the floor —
    report as "engineered dephasing does not aid discrimination; it
    relaxes the walk to the proximity-confounded classical limit," with
    the localization-length curve as mechanism. A complete result.
  - The classical-limit sanity endpoint must pass regardless of verdict.

## TODO

- [ ] Implement/reuse Haken-Strobl dephasing integrator; classical-limit
      sanity gate (large-γ occupation → proximity floor correlation).
- [ ] Fixed γ grid; run KRAS_G12C / BCR_ABL1 / PTP1B.
- [ ] Score discrimination AUC vs floor + block-bootstrap CIs; stratified.
- [ ] Localization length / participation ratio vs γ (mechanism covariate).
- [ ] Bonferroni; emit POSITIVE/NEGATIVE per target, tagged.
- [ ] `results_task0141_dephasing/` + `RESULTS.md` section; note the
      transport-vs-discrimination distinction explicitly for referees.

## Dependency

- Reuses: [[TASK-0041]] (Haken-Strobl solver), [[TASK-0112]] (CI),
  [[TASK-0123]] (stratified AUC). Independent of [[TASK-0143]]/[[TASK-0140]].

## Open Questions

- PTP1B is an ASD target ([[TASK-0081]]) chosen by the collaborator as a
  third case; confirm its apo graph + labels are wired identically to the
  mandatory three before including it, else substitute a mandatory target.

## Done

(not yet)
