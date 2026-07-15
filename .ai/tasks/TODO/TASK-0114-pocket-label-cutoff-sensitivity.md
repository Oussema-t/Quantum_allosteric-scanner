# TASK-0114 Pocket-label ligand-contact cutoff (4.5 Å) sensitivity sweep

## Context

- ID: TASK-0114
- Title: `holo_pocket_mask`'s 4.5 Å ligand-contact cutoff defines ground
  truth itself (which residues count as "pocket") and has never been
  sensitivity-tested — a second, distinct cutoff from the GNM graph
  cutoff TASK-0067/TASK-0113 cover.
- Status: TODO
- Owner: Implementer
- Source: `REVIEW-2026-07-15-execution-plan-gap-audit.md`, finding #3.
- Crit Ref: TASK-0075 already proved this project's *other* threshold
  gate (the cumulative-overlap go/no-go) is knob-unstable — the same
  motion swings 0.067–0.860 across an 18-combo grid, flipping verdict
  in 15/18. No task has checked whether the pocket-label cutoff itself
  has the same property. If it does, every headline AUC's denominator
  (which residues are "true pocket") is itself a knob choice with no
  reported spread.

## Intent Contract

- Outcome: a per-target sensitivity curve (AUC and `classify_failure`
  category vs. ligand-contact cutoff, e.g. 4.0/4.5/5.0/5.5 Å) for each
  mandatory target, stating plainly whether the cutoff choice changes
  which side of TASK-0094's proximity floor any headline result lands
  on.
- In Scope:
  - sweep `holo_pocket_mask`'s `cutoff` parameter across a small grid
    (e.g. 4.0/4.5/5.0/5.5 Å) on KRAS_G12C, BCR_ABL1, CARDIAC_MYOSIN.
  - for each cutoff, regenerate labels via `build_labels`, re-score the
    already-computed `H_new` operator outputs (no need to recompute the
    operator itself, only the label/mask), and report AUC +
    `classify_failure` category.
  - report whether TASK-0047's pinned 21/21 KRAS_G12C heavy-atom
    recovery test (fixed at 4.5 Å) is itself near a sensitivity cliff —
    i.e. does 4.0 or 5.0 Å recover a meaningfully different residue set.
- Out Of Scope:
  - changing the default 4.5 Å cutoff anywhere in production code —
    this task characterizes sensitivity, a follow-up decides whether to
    act on it (same posture as TASK-0067 on the GNM cutoff).
  - the GNM graph cutoff (TASK-0067/TASK-0113's territory) — this task
    is the label-definition cutoff only, a different parameter entirely
    despite both being "4.5 Å"-shaped numbers in this codebase.
- Constraints And Invariants: reuse `labels.build_labels`/
  `holo_pocket_mask` as-is; do not fork a second label-construction
  path for this sweep.
- Planned Validation: real re-run against live RCSB data (network-gated,
  matches TASK-0047's own precedent) on all 3 mandatory targets;
  report per-cutoff AUC table, not a single collapsed conclusion.

## In Progress

None

## TODO

- [ ] Sweep `holo_pocket_mask`'s cutoff on KRAS_G12C/BCR_ABL1/
      CARDIAC_MYOSIN (4.0/4.5/5.0/5.5 Å).
- [ ] Re-score existing `H_new` outputs against each cutoff's relabeled
      mask; report AUC + `classify_failure` category per cutoff.
- [ ] State explicitly whether any mandatory target's floor-clearing
      verdict changes across the grid.
- [ ] Cross-check against TASK-0047's pinned 4.5 Å KRAS_G12C recovery
      test — report whether that fixture sits near a sensitivity cliff.

## Dependency

- TASK-0094 (Done) — the proximity floor this task's verdicts are
  checked against.
- TASK-0047 (Done) — the existing 4.5 Å pinned-recovery test this task
  cross-checks.
- TASK-0103's `build_dumbbell_network` helper — not directly reused
  (this task is real-data, not synthetic), noted only as the precedent
  for how a negative-control-style sensitivity result should be
  reported (per-condition table, not a collapsed summary).

## Open Questions

- None — scope fully specified.

## Done

(not yet)
