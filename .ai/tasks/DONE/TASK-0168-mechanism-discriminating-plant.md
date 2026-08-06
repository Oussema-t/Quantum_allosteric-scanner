# TASK-0168 Mechanism-discriminating plant — does each observable family detect the mechanism it claims to?

## Context

- ID: TASK-0168
- **Renumbered 2026-07-28 (Architect/Planner)**: filed as TASK-0171 by
  `REVIEW-panel-2026-07-28-external.md`, which numbered from a stale count —
  the actual next-free ID at filing time was TASK-0167 ([[TASK-0167]]'s own
  provenance note has the full explanation). No content changed.
- Title: plant two *physically different* allosteric mechanisms (a stiff
  communication channel vs. a correlated low-mode / ensemble coupling) into
  the same real apo topology and test whether each observable family detects
  the mechanism its own justification claims — the protein-scale
  generalization of [[TASK-0103]]'s dumbbell double dissociation.
- Status: Done
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `REVIEW-panel-2026-07-28-external.md` §5B, second rung.
- Priority: **P2 — high scientific value, but [[TASK-0167]] must land first.
  Build only if the schedule allows before 2026-08-08; otherwise describe in
  the forward proposal.**
- Dependency: [[TASK-0167.001]] (planting machinery), [[TASK-0167.002]] (LOD
  — this task is uninterpretable without a detection threshold to compare against).

## Why this matters

[[TASK-0103]] proved, on a 44-node dumbbell, that `ground_state_relaxation`
tracks the *well* and `ctqw` tracks the *coupling*. That result is the
project's cleanest piece of mechanism attribution — and it has never been
reproduced at protein scale, where the operators are 169–704-dimensional and
the confound is live.

More importantly: the project now scores observables from **two different
mechanistic families** and treats their negatives as equivalent evidence.

- **Directed-channel family** — `ctqw`, transport `T(E)`, percolation,
  chiral circulation. Justification: signal propagates from active site to
  pocket along the network.
- **Ensemble/mode family** — `prs_low`, `dcc_low`, `mode_coparticipation`,
  conformational entropy ([[TASK-0166]]). Justification: the pocket is
  encoded in correlated low-frequency motion, not a transmission path.

If a channel plant is detected only by the first family and a mode plant only
by the second, the observable set is *mechanistically discriminating* and each
negative bounds a specific mechanism. If both families detect both plants
equally, they are all measuring the same underlying graph quantity and the
"~40 observables" are ~40 views of one number — which materially weakens
[[TASK-0161]]'s multiplicity framing (the effective number of independent
tests is far below 226) and is a genuinely important finding for the paper.

**Either outcome changes what the negative result means.**

## Intent Contract

- Outcome: a 2×N table (2 planted mechanisms × N observables) of
  detection-at-LOD, on ≥2 real targets, with an explicit verdict on whether
  the observable families are mechanistically discriminating or redundant.
- Why required, not assumed: the project justifies its observable families on
  distinct mechanistic grounds and has never tested that the distinction is
  operative on real topology.

- In Scope:
  - **Plant A — channel** (stiff path in soft matrix): reuse
    `plant.plant_channel` from [[TASK-0167.001]] unmodified.
  - **Plant B — correlated mode** (new): perturb `W` so that a *low* Kirchhoff
    eigenmode acquires large, same-sign amplitude on both the active site and
    the target patch, without creating a path between them. Suggested
    construction: soften ("hinge") the edges of a surface that separates the
    two regions from the rest of the structure, so the slowest mode becomes a
    coordinated motion of {seed ∪ patch} against the remainder. **Verify the
    intended mode structure was actually produced** (check the amplitude of
    modes 1–5 on both regions before and after) — do not assume the
    perturbation had the intended spectral effect. This is the step most
    likely to fail silently.
  - Both plants pass [[TASK-0167.001]]'s `assert_confound_orthogonal` gate.
  - **Both plants must be matched on a common scale** so "detected A but not
    B" is not simply "A was planted harder." Recommended: match on induced
    `R_eff(seed, patch)` change, the monotone dose axis [[TASK-0167.001]]
    settles on. State the matching and show it holds.
  - Observables: at minimum one from each family — `ctqw_converged` /
    `T(E=0)`, and `dcc_low` / `prs_low`. Add `ground_state_relaxation` as the
    dumbbell's own well-tracker, to check the 44-node result survives scale.

- Out Of Scope:
  - Any conclusion about real allostery. Both plants are synthetic
    perturbations of a real graph; this measures the *instrument*, not biology.
  - Reselecting a submission observable (Tier-2-gated, [[TASK-0100]]).
  - A third mechanism (population shift between discrete states) — needs two
    structures, belongs with [[TASK-0015]].

- Constraints And Invariants: pipeline unmodified; both plants gated; dose
  matched; ≥10 seeds per cell.

- Planned Validation:
  - **Mandatory scale-check:** `ground_state_relaxation` must still track the
    well at protein scale. If [[TASK-0103]]'s double dissociation does *not*
    survive N=169–704, that is a first-class finding and this task reports it
    rather than proceeding as if the 44-node result generalizes.
  - Cross-family redundancy is measured directly: Spearman ρ between
    observables' score vectors on the *unplanted* graph, reported alongside
    the detection table. High ρ pre-plant already predicts non-discrimination.

## In Progress

None

## TODO

- [x] `plant_mode` construction + spectral-effect verification -- built
      (`allostery.plant.plant_mode`, mirrors `plant_channel`, softens
      boundary edges instead of strengthening a path). Spectral effect:
      real but weak, does not replicate across targets (KRAS_G12C 1/5→4/5
      same-sign low modes; BCR_ABL1 3/5→3/5, no net improvement).
- [x] Dose-match A and B on induced `R_eff` -- calibrated, reasonably but
      not perfectly matched in log-magnitude at the strengths used (see
      Done).
- [~] Run 2 mechanisms × ≥5 observables × ≥2 targets × ≥10 seeds at LOD --
      run at **4 observables, not 5** (an explicit, stated scope call:
      real `dcc_low`/`prs_low` are structurally unable to see either
      plant at all, no `W` argument exists; a new `dcc_low_from_L` adapter
      substitutes for the ensemble family instead of a 5th unusable
      observable), 2 targets, 10 seeds, 3 strengths -- 480 cells, 0 errors.
- [x] Protein-scale reproduction of [[TASK-0103]]'s double dissociation --
      **passed on both targets** (see Done).
- [x] Pre-plant cross-observable ρ matrix (redundancy measure) -- done,
      both targets (see Done).
- [x] Verdict: discriminating or redundant? Feed the answer back into
      [[TASK-0161]]'s effective-multiplicity framing -- **partially
      discriminating, not simply redundant, weaker/less general than
      hoped, mostly below the formal certification bar** -- see Done and
      RESULTS.md's own dated section.

## Dependency

- [[TASK-0167.001]], [[TASK-0167.002]] — hard blocks.
- [[TASK-0103]] (Done) — the 44-node result this scales up.
- [[TASK-0145]] (Done) — `R_eff` for dose matching.
- [[TASK-0149]] (Done) — `prs_low`/`dcc_low`.

## Open Questions

- Is a "correlated mode" plant achievable without also creating a channel?
  **Resolved, 2026-08-04: partially, and target-dependently.** The
  dose-axis calibration shows Plant B moves conductance in the *opposite*
  direction from Plant A (down, not up) rather than creating a channel by
  another name -- structurally distinct at that level. But the spectral
  verification (does a low mode actually gain same-sign coordinated
  amplitude on seed+patch) is weak and does not replicate: a real, partial
  effect on KRAS_G12C (1/5→4/5 low modes same-sign), no net effect on
  BCR_ABL1 (3/5→3/5). Reported as the mixed, real answer this Open
  Question anticipated might happen, not forced into a cleaner story.
- Should `mode_coparticipation` ([[TASK-0122]]) be included? **Resolved,
  2026-08-04: descoped, explicit judgment call, not silently dropped.**
  Same structural fact as `dcc_low`/`prs_low` in the real pipeline
  (invariant to `H_new`-routed calls) applies to it too; extending it via
  the same `laplacian(W_planted)`-adapter approach used for `dcc_low_from_L`
  was judged lower priority than closing out the 4-observable grid within
  this task's own P2/schedule-conditional time budget. A real gap for a
  follow-up task, not claimed as tested here.

## Done

- 2026-08-04 (Implementer C, this thread): built `allostery.plant.plant_mode`
  (Plant B -- softens the boundary of `{seed} UNION {target}` vs. the rest
  of the structure, mirror image of `plant_channel`'s strengthening), 6 new
  regression tests in `tests/test_plant.py` (identity at strength=0,
  boundary-only edge modification, conductance falls with strength,
  `assert_confound_orthogonal` passes across a strength sweep). New
  `scripts/mechanism_discriminating_plant.py`: `dcc_low_from_L` adapter
  (verified bit-identical to real `dcc_low` on an equivalent unweighted
  graph before trusting it), 4 score functions (`T(E=0)`, `ctqw_converged`,
  `ground_state_relaxation`, `dcc_low_from_L`, all applied directly to
  `laplacian(W_planted)` per [[TASK-0103]]'s own dumbbell-adapter
  convention, not `build_H_new`), `verify_mode_plant_spectral_effect`,
  `calibrate_dose_axis`, `redundancy_matrix`, `well_vs_channel_scale_check`,
  and a checkpointed/resumable grid driver reusing
  `positive_control_detection_curve.py`'s certification pipeline
  (gate1-4) unmodified.

  **Forced re-scope before any grid ran** (Discovery step, not skipped):
  confirmed by direct code read that `ctqw_converged`/`dcc_low`/`prs_low`/
  `ground_state_relaxation`/`mode_coparticipation` as actually called in
  `run_challenge.py` are exactly plant-invariant to ANY weight-only `W`
  perturbation -- not a fact specific to `plant_channel`, applies equally
  to the new `plant_mode`. Real `dcc_low`/`prs_low` have no `W` argument
  at all and cannot participate in a live grid under any construction;
  included only in the pre-plant redundancy matrix, not the detection grid.

  **Mandatory scale-check: PASSED on both targets.** Real diagonal-well
  construction + `plant_channel`, 10 seeds each: GSR tracks the well
  (mean AUC 0.996 KRAS_G12C, 0.719 BCR_ABL1) not the channel (0.559,
  0.508 -- chance); CTQW tracks the channel (0.640, 0.566) not the well
  (0.0, 0.0 on both -- anti-correlated, not just chance).
  [[TASK-0103]]'s 44-node finding survives N=169-451, weaker on BCR_ABL1
  but the qualifying direction holds on both.

  **Main grid: 480 cells (2 targets x 2 mechanisms x 4 observables x 3
  strengths {0,4,16} x 10 seeds), 0 errors, ~90 CPU-minutes, run detached
  per the Long-Running Compute convention.** `T(E=0)`/`ctqw_converged`
  (channel family) show a clean, mechanism-specific point-estimate
  response **replicated on both targets**: rising AUC with channel
  strength (KRAS_G12C 0.21→0.70, BCR_ABL1 0.47→0.65), flat-to-falling
  with mode strength (KRAS_G12C 0.21→0.08, BCR_ABL1 0.47→0.00 -- a
  striking near-total collapse on BCR_ABL1 at s=16). `dcc_low_from_L`
  (the new ensemble-family adapter) shows the hoped-for opposite
  (mode-specific rise) cleanly on KRAS_G12C (0.55→0.75) but **not on
  BCR_ABL1** (falls under both mechanisms, 0.31→0.10 mode vs. 0.31→0.35
  channel) -- reported as a genuine non-replication, not smoothed into a
  single-target success story. `ground_state_relaxation`, run here
  *without* an explicit well (neither named mechanism plants one), behaves
  as a de facto third channel-family member on both targets (rises with
  channel, falls with mode) -- its real well-tracking ability (confirmed
  above) is conditional on an actual planted well, a distinction this
  task's design surfaced rather than assumed.

  **Certification (gate1-4): mostly does not clear.** Under the corrected
  (compact-patch) null, P(certified) exceeds 0.30 in only 2 of 32
  (observable x mechanism x target) curves and the 0.80 LOD bar is never
  reached in the tested strength range (up to ~2.6-2.9x baseline
  conductance for the channel plant, ~0.25-0.32x for the mode plant) --
  the real point-estimate discrimination above mostly does not clear this
  project's own formal detection standard, extending [[TASK-0167.002]]'s
  own headline finding to a second mechanism and a new observable.

  **Redundancy** (Spearman rho, real/unplanted scores): `T(E=0)`/`ctqw`/
  `ground_state_relaxation` (all on the same unplanted `L0`) cluster
  substantially (rho 0.5-0.9) on both targets; `dcc_low_from_L0`/real
  `dcc_low` correlate at rho 0.99-1.00 (expected). **`prs_low` is the one
  genuinely non-redundant observable in the full named set**, rho -0.32
  to 0.12 with everything else on both targets.

  **Verdict**: partially discriminating, not simply redundant, weaker/
  less general than hoped. Real mechanism-specific structure exists
  (channel family, replicated 2/2 targets) arguing against full
  redundancy; but the discrimination mostly doesn't clear the formal
  certification bar, the one candidate ensemble discriminator doesn't
  generalize, and the channel-family trio is itself substantially
  redundant pre-plant -- arguing against full independence too. Fed back
  into [[TASK-0161]]'s framing: effective multiplicity depends on which
  mechanism a real signal would take, not a single flat number.

  **Implementer's-call decisions**: (1) 2 targets not 3 (CARDIAC_MYOSIN
  dropped, explicit time-budget call, not a cost-driven necessity --
  actual per-cell cost turned out ~9-11s regardless of target size,
  dominated by CI/permutation machinery not eigendecomposition, checked
  directly before assuming N^3 scaling would be prohibitive). (2) 10 not
  20 seeds (this task's own Constraint floor). (3) one CI method (spatial)
  + 2 not 3 null specs (scattered+compact) -- both trims cite
  [[TASK-0167.002]]'s own direct finding that the dropped options were
  statistically indistinguishable from the kept ones, not assumed here.
  (4) strength grid {0,4,16}, not TASK-0167.002's finer 8-point grid --
  coarser, explicit scope-narrowing given this task's P2 priority.
  (5) `mode_coparticipation` descoped (Open Questions, above).

  **RESULTS.md**: new dated section + open-questions row 60 (both
  appended). Full `pytest tests/ -q` run before closing out (see commit).

  **Cross-reference, found after this task's own analysis was already
  written (registry check before moving to DONE), not incorporated into
  the numbers above but recorded here**: [[TASK-0199]] (Done, 2026-08-03,
  Implementer A) split its own redundancy measurement out of this task's
  redundancy checkbox and ran a far more thorough version register-wide
  -- 28 real observable types, 5 targets, participation-ratio effective
  rank ~2.6-4.1 of 28 on every target (a ~9x redundancy factor). This
  task's own small 7-observable pre-plant rho matrix (`T(E=0)`/`ctqw`/
  `GSR` clustering at rho 0.5-0.9, `prs_low` standing genuinely apart) is
  a consistent, much narrower special case of TASK-0199's own headline
  finding, not a contradiction of it -- TASK-0199 is the authoritative
  source for the register-wide redundancy question; this task's own
  matrix should be read as a planted-context corroboration on a small
  subset, not re-cited as the primary redundancy result.

- **Cross-reference, 2026-08-06 ([[TASK-0203]], Implementer A)**: this
  task's own 2-mechanism grid was run on PTP1B (the target carrying
  [[TASK-0201]]'s surviving `dcc_low` k=10 positive, not among this
  task's own KRAS_G12C/BCR_ABL1). Result, decisive: at k=10, `dcc_low`
  shows a **channel-type** response (rises with channel strength, falls
  with mode strength) -- the opposite of the mode/ensemble signature this
  task's own `"family": "ensemble"` label for `dcc_low_from_L` implies,
  and opposite to the partial confirmation found on KRAS_G12C. At the
  k=20 this task's own grid uses, PTP1B shows no clean dissociation
  either (both mechanisms raise the AUC). Full account, including the
  additive `dcc_low_from_L_k10` observable this required:
  [[TASK-0203]]'s own Done section.
