# TASK-0141 Engineered-dephasing (ENAQT) sweep — discrimination, not transport (HYP-P11)

## Context

- ID: TASK-0141
- Title: Sweep a Haken-Strobl pure-dephasing rate γ (QSW/Lindblad) on
  KRAS_G12C / BCR_ABL1 / PTP1B and test whether *any* γ improves pocket
  **discrimination** vs the proximity floor — the collaborator's Idea #1,
  run with the correct scored quantity and a pre-registered outcome
  ([[HYP-P11]]).
- Status: Done
- Claimed By: Implementer D (this thread)
- Claimed At: 2026-07-20
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

- [x] Implement/reuse Haken-Strobl dephasing integrator; classical-limit
      sanity gate (large-γ occupation → proximity floor correlation).
- [x] Fixed γ grid; run KRAS_G12C / BCR_ABL1 / PTP1B.
- [x] Score discrimination AUC vs floor + block-bootstrap CIs; stratified.
- [x] Localization length / participation ratio vs γ (mechanism covariate).
- [x] Bonferroni; emit POSITIVE/NEGATIVE per target, tagged.
- [x] `results_task0141_dephasing/` + `RESULTS.md` section; note the
      transport-vs-discrimination distinction explicitly for referees.

## Dependency

- Reuses: [[TASK-0041]] (Haken-Strobl solver), [[TASK-0112]] (CI),
  [[TASK-0123]] (stratified AUC). Independent of [[TASK-0143]]/[[TASK-0140]].

## Open Questions

- PTP1B is an ASD target ([[TASK-0081]]) chosen by the collaborator as a
  third case; confirm its apo graph + labels are wired identically to the
  mandatory three before including it, else substitute a mandatory target.
  **Resolved 2026-07-20**: confirmed identical wiring (single `chains`
  field consumed for both apo `1SUG` and holo `1T49`, both resolve to
  chain A, no apo/holo chain-mismatch the way `GLUCOKINASE` had per
  [[TASK-0081]]). Used PTP1B directly, no substitution needed.

## Done

**2026-07-20, Implementer D (this thread).**

**Verdict: NEGATIVE on all 3 targets (KRAS_G12C, BCR_ABL1, PTP1B),
confirming this task's own pre-registered prior.** No γ clears the
proximity floor with non-overlapping 95% CIs anywhere; the best-of-8-γ
point's own permutation null (1000 replicates) is nowhere near
significant on any target (p=0.649/0.211/1.000 vs. Bonferroni
α=0.05/3=0.0167). Full numbers, method, and the two real complications
found along the way: `RESULTS.md`'s "Engineered-dephasing (ENAQT)
discrimination sweep" section (open-questions index row 19) —
summarized here, not duplicated in full.

**Two real gaps in the existing Haken-Strobl machinery closed before
this task's own sweep could be trusted** (`src/allostery/propagators.py`):
1. `haken_strobl` had no incoherent-mixture source option — every
   multi-residue seed used a coherent equal-amplitude superposition,
   which violates this project's own established GAUGE
   (TASK-0118/INV-0006: no biophysical basis for a specific relative
   quantum phase between a real active site's residues). Added a
   `coherent` kwarg (default `True`, byte-identical for every existing
   caller — ADD-only) mirroring `ctqw`'s own `_ctqw_from_eigh`/
   `_ctqw_mixture_from_eigh` split; this task always passes
   `coherent=False`.
2. No time-averaged Haken-Strobl occupation existed (`haken_strobl`
   only returns one endpoint snapshot), but this task's own Intent
   Contract scores "time-averaged site occupation." New
   `haken_strobl_time_averaged`: one `solve_ivp` call with `t_eval` set
   to the snapshot grid, not `n_snapshots` independent re-solves from
   t=0 (RK45's adaptive-step cost is set by `H`'s bandwidth and
   `t_max`, not by how many interpolation points are requested — nearly
   free on top of the existing single-endpoint cost). **Deliberately
   excludes `t=0` from its own snapshot grid**, unlike
   `time_averaged_ctqw`'s own `linspace(0, t_max, n_steps)` (harmless
   there at its 500-point default): found directly while validating this
   function that the initial condition is a delta-function-like spike
   exactly at the seed, and including it as one of only `n_snapshots`
   equally-weighted points bakes a `1/n_snapshots`-weighted proximity
   artifact into the very quantity this task exists to check for a
   proximity confound in.
   12 new tests, `tests/test_haken_strobl_extensions.py`: coherent-kwarg
   default-unchanged / scalar-source-identical / multi-index-genuinely-
   differs / matches-manual-average-of-single-seeds (linearity argument
   checked directly, not just derived); time-averaged trace-conservation,
   matches-manual-average-of-independent-snapshots (cross-checks the
   single-solve-with-`t_eval` implementation against the slow, obviously-
   correct loop), matches `time_averaged_ctqw`'s closed form at γ=0
   (both coherent and incoherent) to `atol=1e-3` on a generous grid (the
   two functions' grids are deliberately offset by the `t=0` exclusion
   above, so an `O(1/n)` discrepancy at small `n` is expected and was
   verified, not assumed, before picking test tolerances), and a
   strong-dephasing-time-average-approaches-uniform sanity anchor
   (parametrized to actually equilibrate within its own `t_max`, unlike
   the accidentally-too-short first draft of this test, caught by
   running it).

**Method**: γ over the task's own fixed grid `{0, 0.05, 0.1, 0.2, 0.5,
1, 2, 5} x H_new's spectral bandwidth` (`w.max()-w.min()`, this repo's
established bandwidth convention), `t_max=25` (TASK-0105's own
established "long enough" anchor), `coherent=False`, `H_new` (this
project's default/submission operator). New
`scripts/dephasing_discrimination_sweep.py`. Runtime came in far under
the pre-registered feasibility estimate (TASK-0105's own N^3-scaling
note): full 3-target x 8-point sweep completed in ~90s wall-clock
(0.06-0.6s/γ KRAS_G12C, 0.2-9.1s/γ BCR_ABL1, 0.05-3.0s/γ PTP1B) — no
target needed a reduced grid.

**The mandatory classical-limit sanity gate did NOT pass as literally
specified, on any target — root-caused, not glossed over.** `ρ(occ,
-dist)` *fell* with γ on all 3 targets (opposite direction from this
task's own synthetic prior), diagnosed as Zeno-regime suppression of
the *effective* diffusion timescale at large γ under the fixed
`t_max=25`: `D_eff ~ ||H||^2/2γ` falls once γ passes the ENAQT-optimal
point, so the classical-diffusion-like proximity signature needs *more*
propagation time to develop as γ grows, and a `t_max` fixed across the
whole sweep under-samples it at the grid's high end. Confirmed directly
(not assumed) on KRAS_G12C at γ=5x bandwidth by extending `t` alone,
γ held fixed: `ρ(occ,-dist)` 0.584 (t=25) -> 0.730 (t=100) -> 0.863
(t=300) — recovers the expected rising trend given enough time, ruling
out an integrator bug. This is a genuine complication with the task's
own literal sanity-gate specification (which implicitly assumed a
single `t_max` reaches the classical limit at every γ in the grid
simultaneously — true on the batch's own smaller synthetic loop, not
verified true at real-protein scale before this task ran it) — it does
NOT undermine the headline AUC-vs-floor numbers above, which are valid,
literal measurements of "what γ does to discrimination at this task's
own fixed `t_max=25`," the actual deliverable.

**AUC trend, precisely**: not strictly "flat-or-declining" as the
Planned Validation's NEGATIVE criterion anticipated — on all 3 targets
AUC dips slightly at low-to-mid γ then rises modestly by γ=5x bandwidth
(echoing TASK-0105's own transport-efficiency interior-optimum shape,
`RESULTS.md` open-question row 7), but never crosses the floor and is
not statistically distinguishable from the best-of-8 permutation null.
The NEGATIVE verdict holds via the Planned Validation's other stated
criteria ("no γ clears the floor" / "the optimum's CI overlaps the
floor"), not via a strictly monotone decline — flagged as a precise
correction to the pre-registered framing's implicit shape assumption,
not silently smoothed over.

**PTP1B** stays clearly anti-correlated with its own (genuinely distal)
pocket at every γ (AUC 0.19-0.24) — consistent with TASK-0081's
independent finding (AUC 0.2497 at a differently-configured run), a
useful cross-check that this task's own pipeline wiring for PTP1B is
correct.

**Not done / explicitly out of scope** per this task's own Intent
Contract: no "best γ" selected for the submission (Tier-2 gated,
[[TASK-0100]]); no initial-phase/chiral component ([[TASK-0140]]'s
scope); no transport-efficiency metric reported anywhere (only
discrimination AUC, stratified AUC, and the localization/proximity
mechanism covariates). Full regression suite re-run after this change:
799 passed, 2 xfailed, no failures.
