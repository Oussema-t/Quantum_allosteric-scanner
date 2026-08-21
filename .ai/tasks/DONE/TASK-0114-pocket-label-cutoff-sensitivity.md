# TASK-0114 Pocket-label ligand-contact cutoff (4.5 Å) sensitivity sweep

## Context

- ID: TASK-0114
- Title: `holo_pocket_mask`'s 4.5 Å ligand-contact cutoff defines ground
  truth itself (which residues count as "pocket") and has never been
  sensitivity-tested — a second, distinct cutoff from the GNM graph
  cutoff TASK-0067/TASK-0113 cover.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer B (this thread)
- Claimed At: 2026-07-20
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

- [x] Sweep `holo_pocket_mask`'s cutoff on KRAS_G12C/BCR_ABL1/
      CARDIAC_MYOSIN (4.0/4.5/5.0/5.5 Å).
- [x] Re-score existing `H_new` outputs against each cutoff's relabeled
      mask; report AUC + `classify_failure` category per cutoff.
- [x] State explicitly whether any mandatory target's floor-clearing
      verdict changes across the grid. It does not, for any target.
- [x] Cross-check against TASK-0047's pinned 4.5 Å KRAS_G12C recovery
      test — report whether that fixture sits near a sensitivity cliff.
      It does: the raw recovered set moves at every 0.5 Å step tested.

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

**2026-07-20, Implementer B.** Swept `build_labels`'/`holo_pocket_mask`'s
`cutoff` across {4.0, 4.5, 5.0, 5.5} Å on all 3 mandatory targets,
re-scoring the same, once-computed `H_new`/`time_averaged_ctqw_
converged` occupation (TASK-0130's closed form) against each cutoff's
regenerated label — no operator recomputation, per this task's own In
Scope (`scripts/pocket_label_cutoff_sensitivity.py`,
`results/tasks/0114_pocket_cutoff_sensitivity/`).

### Results

| Target | Cutoff (Å) | n pocket | AUC | Floor | Floor cleared? | `classify_failure` |
|---|---|---|---|---|---|---|
| KRAS_G12C | 4.0 | 15 | 0.581 | 0.505 | Yes | `NO_FAILURE_DETECTED` |
| KRAS_G12C | 4.5 | 18 | 0.590 | 0.482 | Yes | `NO_FAILURE_DETECTED` |
| KRAS_G12C | 5.0 | 18 | 0.574 | 0.476 | Yes | `NO_FAILURE_DETECTED` |
| KRAS_G12C | 5.5 | 17 | 0.522 | 0.444 | Yes | **`NO_SIGNAL_IN_APO`** |
| BCR_ABL1 | 4.0 | 14 | 0.565 | 0.593 | No | **`BEATS_CHANCE_NOT_FLOOR`** |
| BCR_ABL1 | 4.5 | 16 | 0.527 | 0.582 | No | `NO_SIGNAL_IN_APO` |
| BCR_ABL1 | 5.0 | 19 | 0.524 | 0.578 | No | `NO_SIGNAL_IN_APO` |
| BCR_ABL1 | 5.5 | 20 | 0.532 | 0.582 | No | `NO_SIGNAL_IN_APO` |
| CARDIAC_MYOSIN* | 4.0 | 9 | 0.461 | 0.511 | No | `NO_SIGNAL_IN_APO` |
| CARDIAC_MYOSIN* | 4.5 | 13 | 0.518 | 0.568 | No | `NO_SIGNAL_IN_APO` |
| CARDIAC_MYOSIN* | 5.0 | 14 | 0.499 | 0.551 | No | `NO_SIGNAL_IN_APO` |
| CARDIAC_MYOSIN* | 5.5 | 14 | 0.499 | 0.551 | No | `NO_SIGNAL_IN_APO` |

*CARDIAC_MYOSIN's numbers here use [[TASK-0124]]'s new apo structure
(8QYP, N=704), landed the same day and in flight while this sweep ran
(discovered mid-task, not assumed — cross-checked directly against the
live `targets.yaml` when this run's N=704 didn't match every other
CARDIAC_MYOSIN reference in this project's own history, N=950/5TBY).
**Not directly comparable to this project's other CARDIAC_MYOSIN
numbers**, flagged explicitly rather than silently mixed. Re-running
once 8QYP is the document's settled reference is a real, cheap
follow-up (same script, no code change), not done here.

### Headline — two different granularities, two different answers

1. **The coarse question this task's own Outcome asked ("does the
   cutoff choice flip which side of the proximity floor a target lands
   on") — no, not for any target.** `floor_cleared` is stable across
   the entire grid for all 3 targets.
2. **The finer `classify_failure` diagnosis category is NOT stable —
   it flips for 2 of 3 targets.** KRAS_G12C: `NO_FAILURE_DETECTED` ->
   `NO_SIGNAL_IN_APO` at 5.5 Å (AUC drops to 0.522, inside the
   ±0.05-of-chance band `classify_failure` checks *before* the floor
   comparison, even though the bare `auc > floor` boolean still reads
   "cleared"). BCR_ABL1: `BEATS_CHANCE_NOT_FLOOR` -> `NO_SIGNAL_IN_APO`
   between 4.0 Å and 4.5 Å. Neither swing is remotely TASK-0075's own
   scale (0.067-0.860, 15/18 flips) — AUC itself only moves ~0.04-0.07
   across the whole grid — but it is real, reportable sensitivity in
   the *label a reader sees*, not noise in an unread number.
3. **TASK-0047's pinned 4.5 Å KRAS_G12C fixture (21/21 heavy-atom
   recovery) is confirmed exactly correct** (`matches_pinned_4_5a_
   exactly=True`) **and sits on a real, still-moving slope, not a
   plateau**: 4.0 Å recovers 17 raw contacts (residues 11, 13, 69, 100
   drop out); 5.0 Å recovers 22 (gains 92); 5.5 Å recovers 24 (gains
   35, 64, 92 also). The raw recovered set keeps changing at every
   0.5 Å step tested, in both directions — the 4.5 Å choice is not
   obviously sitting on a stable local plateau, even though the
   downstream verdict (§1/§2 above) is far less sensitive than the raw
   residue-set churn alone would suggest.

**Cross-read against TASK-0075**: this project's two structurally
distinct 4.5 Å-shaped thresholds behave very differently. The
cumulative-overlap go/no-go gate is genuinely knob-unstable; the
pocket-label cutoff is comparatively well-behaved (no floor-side flips
at all, a narrow diagnosis-category sensitivity only at the grid's
edges). TASK-0075's own `UNSTABLE`-reporting fix for *that* gate
remains open and is not diminished by this contrast.

### Docs updated additively

`RESULTS.md`: new "Pocket-label ligand-contact cutoff sensitivity"
section + open-questions row 20. `EXECUTION_PLAN.md`: bullet for this
task (already filed under Phase 0/pre-Phase-1 notes) updated in place
with the Done result; TASK-0075's own row (5.5) gets a dated update
noting the contrast.

### Not attempted / left for a follow-up task

- Shipped 4.5 Å default is unchanged anywhere in production code, per
  this task's own Out Of Scope — characterization only, same posture
  TASK-0067 took for the GNM cutoff.
- No dedicated unit tests added — this task reuses `build_labels`/
  `holo_pocket_mask`/`classify_failure` exactly as they already are
  (all independently tested elsewhere); no new library code was
  written, only a real-data sweep script.
- CARDIAC_MYOSIN not re-run against the old 5TBY structure for a
  same-structure comparison — TASK-0124's own structure swap is a
  real, independent fix (5TBY's data-quality issues are documented
  elsewhere in this project); re-deriving 5TBY-era numbers just for
  this comparison was judged not worth reintroducing a structure this
  project is actively moving away from.
