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
- Status: TODO
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

- [ ] `plant_mode` construction + spectral-effect verification.
- [ ] Dose-match A and B on induced `R_eff`.
- [ ] Run 2 mechanisms × ≥5 observables × ≥2 targets × ≥10 seeds at LOD.
- [ ] Protein-scale reproduction of [[TASK-0103]]'s double dissociation.
- [ ] Pre-plant cross-observable ρ matrix (redundancy measure).
- [ ] Verdict: discriminating or redundant? Feed the answer back into
      [[TASK-0161]]'s effective-multiplicity framing.

## Dependency

- [[TASK-0167.001]], [[TASK-0167.002]] — hard blocks.
- [[TASK-0103]] (Done) — the 44-node result this scales up.
- [[TASK-0145]] (Done) — `R_eff` for dose matching.
- [[TASK-0149]] (Done) — `prs_low`/`dcc_low`.

## Open Questions

- Is a "correlated mode" plant achievable without also creating a channel?
  The two are not fully independent in an ENM — softening a separating
  surface changes path weights too. If they cannot be cleanly separated,
  **that is itself the answer** to the discrimination question and should be
  reported as such rather than forced apart by construction.
- Should `mode_coparticipation` ([[TASK-0122]]) be included? It is the
  observable most directly designed for Plant B; including it is the fairest
  test of the ensemble family. Recommend yes if cost allows.

## Done

(not yet)
