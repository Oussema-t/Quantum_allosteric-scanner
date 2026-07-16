# TASK-0123 Adopt distance-stratified evaluation (distance-matched decoys)

## Context

- ID: TASK-0123
- Title: Score pocket residues against distance-matched non-pocket
  decoys (same hop-shell from the seed), not against all residues — the
  standard way to evaluate a signal under a known, confirmed
  distance confound, and the only way an occupation-based signal
  *inside* a given shell can become visible at all.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `.ai/reviews/REVIEW-panel-2026-07-16-v2.md` §2.3, §5 P1-7, §6.
- Priority: **P1 — weeks 2-4.**

## Intent Contract

- Outcome: a distance-stratified AUC metric — for each pocket residue,
  match it against non-pocket residues at the same hop-distance (or a
  binned equivalent) from the seed, and compute discrimination *within*
  that shell rather than across the whole residue set. This directly
  answers the panel's own falsification test (§6): "distance-matched-
  decoy AUC on all targets... stratified AUC ≈ 0.5 in every shell →
  observable dead, switch to co-participation/ENAQT."
- Why this is required, not optional, per §2.3: plain whole-graph AUC is
  mechanically dominated by the fact that "occupation of a walk seeded
  at a point is a monotonically-decreasing function of distance from
  that point — for any operator, at any time" (table reproduced in the
  review: ρ(occ,−dist) = +0.83 to +0.97 depending on t, on a bare
  disorder-free Laplacian with zero potential). A whole-graph AUC cannot
  distinguish "this operator found the pocket" from "this operator found
  distance," structurally. Distance-stratification is the fix that lets
  a real signal *inside* the confound become visible, if one exists.
- In Scope:
  - Implement hop-shell (or Euclidean-shell) binning and within-shell
    AUC computation, reusable across every operator/propagator already
    in the register — a metrics-layer addition, not a per-operator patch.
  - Apply to all 3 mandatory targets, current `H_new`/`H10`/other
    register operators, both propagators (`time_averaged_ctqw`/
    `ground_state_relaxation`).
  - Apply to whatever new observable(s) [[TASK-0122]] produces, once
    available — this metric is the intended evaluation lens for
    `mode_coparticipation`, not just a patch for the existing register.
- Out Of Scope:
  - Building new observables — [[TASK-0122]]'s scope; this task builds
    the evaluation method, applicable to any observable.
  - Changing which operator ships — Tier-2 gated, unaffected by this
    task's own findings per [[TASK-0100]].
- Constraints And Invariants: shell binning must be defined once and
  reused identically across every operator comparison in this task — a
  different binning per operator would reintroduce exactly the kind of
  unexamined-knob problem this whole review is about.
- Planned Validation: reproduce the panel's own predicted kill criterion
  directly — if stratified AUC ≈ 0.5 in every shell for the current
  register, report that as the finding (observable dead, per the
  panel's own framing) rather than searching for a shell where it isn't.

## In Progress

None

## TODO

- [ ] Implement hop-shell (or Euclidean-shell) binning in the metrics
      layer.
- [ ] Implement within-shell AUC computation.
- [ ] Apply to all 3 mandatory targets × current register operators ×
      both propagators.
- [ ] Report whether stratified AUC clears 0.5 in any shell, for any
      operator — the panel's own kill/pass criterion.
- [ ] Re-apply once [[TASK-0122]]'s `mode_coparticipation` is available.

## Dependency

- None hard — can start immediately on the existing register.
- Soft: should be re-applied once [[TASK-0121]]/[[TASK-0122]] land, since
  those change what's being evaluated.

## Open Questions

- Exact shell-binning granularity (single-hop bins vs. coarser bands) —
  Implementer's call, state the choice and why in Done; report
  sensitivity to this choice if it materially changes the conclusion.

## Done

(not yet)
