# TASK-0140 Chiral (broken-time-reversal) circulation observable, gated eval (HYP-P9)

## Context

- ID: TASK-0140
- Title: Port and benchmark the chiral-walk directed-current observable
  (Peierls flux + Helmholtz-Hodge decomposition), whose circulating part
  is proximity-orthogonal by construction, against the proximity floor
  with CIs and distance-stratification ([[HYP-P9]]).
- Status: TODO
- Owner: Implementer (build + run). Physics of the observable already
  sanity-checked this batch (two synthetic gates pass — see Source);
  execution needs no new physics judgement.
- Source: `REVIEW-panel-2026-07-20` §"chiral observable" and §"physics
  check of Idea #2". Reference implementation delivered as
  `chiral_observable.py` (`peierls_chiral`, `time_averaged_current`,
  `hodge_circulating`, `chiral_circulation_score`) with GATE 1/GATE 2
  passing on synthetic data — port into `src/allostery/chiral.py`.
  **Flagged 2026-07-20 (Architect/Planner): `chiral_observable.py` is
  not actually present anywhere in this repo or the applied review
  batch** (`.ai/reviews/2026-07-20/` contains only the README, the
  EXECUTION_PLAN insert, and the physics append — no `.py` files).
  Whoever claims this task needs to either obtain the actual reference
  script from wherever it was generated, or reconstruct
  `peierls_chiral`/`hodge_circulating` from HYP-P9's own description
  (`.claude/hypotheses/physics.md`) and the cited literature (Zimborás
  et al. 2013, Sci. Rep. 3, 2361; Lu et al. 2016, PRA 93, 042302) —
  state which, and verify GATE 1/GATE 2 pass on a freshly-built
  implementation before trusting it, not assume the delivered script's
  claimed pass status transfers to a reconstruction.
- Priority: **P1.** The real quantum-flavoured observable of this batch,
  and the disciplined form of the collaborator's "controlled phase"
  Idea #2 (an arbitrary initial phase is an unjustified tunable knob =
  label-leakage risk; the *only* physically-justified phase injection is
  complex hopping / broken time-reversal, which is gauge-invariant and
  acts only on cycles — Zimborás 2013, Lu 2016). **Soft-gated by
  [[TASK-0143]]**: fully meaningful only where the openness premise holds.

## ⚠️ Before implementing — what this observable is and is not

Single-particle. Therefore **classically simulable at N~hundreds** — this
is a *modeling* advantage (directionality + loop-native + proximity-
orthogonal), NOT an asymptotic quantum advantage. Do not let the write-up
imply otherwise; the converged single-particle limit remains phase-free
([[TASK-0130]]) for the *occupation* observable — the chiral current is a
*different* observable (a bond current, odd under time-reversal), which is
why it can carry directional information the occupation cannot. State this
distinction explicitly in `RESULTS.md`.

## Intent Contract

- Outcome: a per-residue chiral-circulation score for every mandatory +
  ASD target, evaluated against the proximity floor with the **same**
  rigor every other operator has had — block-bootstrap CIs ([[TASK-0112]]),
  distance-stratified AUC ([[TASK-0123]]), permutation null on any
  max-over-something statistic ([[TASK-0131]] precedent). A pre-declared
  bar decides whether it clears the floor; not clearing it is a valid,
  reportable negative.
- Why required: it is the first observable in the program that, on
  synthetic data, (i) dissociates coupling from well-depth (GATE 1) and
  (ii) beats the proximity floor on a distal loop pocket with residual
  distance-correlation only ρ≈+0.33 vs CTQW's +0.6..+0.97 (GATE 2). The
  synthetic passes prove the *observable can read a loop signal when one
  exists* — they do NOT prove real pockets carry it. Only the gated real
  run does, and only where [[TASK-0143]] passes.
- In Scope:
  - Port `chiral_circulation_score(H_real, coords, source)` — same call
    shape as `time_averaged_ctqw_converged`, so it slots into
    `analysis.operator_sweep` as one more observable, not a fork.
  - Keep the **Hodge decomposition**: score = magnitude of the
    divergence-free (circulating) current per residue. The gradient part
    is the radial proximity flow and MUST be discarded — this is what
    makes the observable proximity-orthogonal by construction, not by
    tuning. A regression test must assert grad+curl reconstructs J and
    that div(J_circ)≈0.
  - Rotation-robustness: average over >=3 field directions (the delivered
    default). Report sensitivity to field magnitude (`field_scale`).
  - Evaluate on `H_new`'s own apo graph, seeded at the full active-site
    array (incoherent mixture, the fixed seed convention), all targets.
- Out Of Scope:
  - Sweeping an *initial-phase* pattern (the collaborator's raw Idea #2) —
    explicitly rejected as an unjustified label-leaking knob; the flux is
    the justified substitute. Do not add a per-site phase parameter.
  - Multi-field-direction *tuning* against labels — the 3-axis average is
    fixed; do not select a field direction per target by AUC.
  - Operator-selection decisions (Tier-2 gated, [[TASK-0100]]).
- Constraints And Invariants:
  - Field magnitude, number of field directions, and seed convention are
    fixed once, up front, blind to labels. The gauge-invariant content is
    the flux through cycles; a per-target field tuned to labels would
    reintroduce the overfitting this whole program exists to avoid.
  - Fully-decohered / real-symmetric limit sanity: at zero flux the
    circulating score must vanish (no directed current without broken
    time-reversal) — assert as a regression test (the physical guarantee).
- Planned Validation (**pre-registered**):
  - **PASS on target T** iff chiral-circulation AUC clears the proximity
    floor AND the 95% block-bootstrap CIs do not overlap, on >=1 mandatory
    target with generalization-set confirmation, surviving Bonferroni.
    Report Spearman(score, −dist) alongside (expect ≪ 0.6 if honest).
  - **Distance-stratified check**: run [[TASK-0123]]'s `stratified_auc`
    with its permutation null; a whole-graph AUC alone is not sufficient
    evidence (same reason as every other operator).
  - **FAIL**: AUC collapses to the floor / CIs overlap everywhere — report
    "the chiral current finds no real loop signal these pockets carry,"
    consistent with a [[TASK-0143]] FAIL.
  - Synthetic GATE 1 + GATE 2 ported as regression tests first.

## TODO

- [ ] Port `chiral.py`; wire `chiral_circulation_score` into `operator_sweep`.
- [ ] Regression tests: GATE 1 (coupling≠well), GATE 2 (beats floor on
      synthetic loop pocket), Hodge reconstruction, zero-flux → zero curl.
- [ ] Real run: all mandatory + ASD, AUC vs floor, block-bootstrap CIs.
- [ ] Distance-stratified AUC + permutation null ([[TASK-0123]]/[[TASK-0131]]).
- [ ] Bonferroni; emit PASS/FAIL/INSUFFICIENT per target, tagged.
- [ ] `results_task0140_chiral/` + `RESULTS.md` section; naive + corrected.

## Dependency

- Soft: [[TASK-0143]] (openness premise) — interpret a FAIL here in light
  of a FAIL there (no loop to circulate in).
- Reuses: [[TASK-0112]] (CI), [[TASK-0123]] (stratified AUC + null),
  [[TASK-0130]] (converged-limit scoring convention / seed).

## Open Questions

- Whether the incoherent full-active-site seed is the right source for a
  *directed* observable, or whether the active-site→pocket direction wants
  a single well-defined source. State the choice; if it materially changes
  the verdict, that sensitivity is itself a finding, not a knob to tune.

## Done

(not yet)
