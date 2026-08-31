# TASK-0303 — Add ENM mode shift to the pocket-ranking family

- Status: TODO
- Priority: High — an independent physical signal that is **not in the rule family at all**
- Filed: 2026-08-30 by Reviewer thread
- Related: [[TASK-0301]], [[TASK-0300]], external Experiment D

## Why

Every one of the 61 rules in [[TASK-0282]]'s family is a function of
distance-to-seed and fpocket druggability ([[TASK-0301]]). **ENM mode
shift is a dynamics signal — independent of both — and it has already
shown effect** in your agents' Experiment D:

- Open stratum: **p = 0.005–0.013**, cluster-collapsed, surviving
  **fixed-node-budget AND volume-residualisation AND both candidate
  settings**. Not a size artifact.
- More robust than hydrophobic density to candidate-set expansion: going
  default → `-m 2.8`, hydrophobic density's open rank-1 falls 6/6 → 3/6
  while mode shift's p is unmoved (0.0052 → 0.0060).
- Cryptic stratum: not significant (p = 0.15–0.65), but median percentile
  0.24–0.28 against a K=6 detection boundary of 0.173 — **on the right
  side of chance**, unlike conservation at 0.66–0.69.

## Scope

- [ ] Port Experiment D's mode-shift computation into this repo's own
      pipeline (`expD_modeshift.py` in
      `.ai/reviews/2026-08-29 - distal pockets/`).
- [ ] **Re-run with this repo's per-target `enm_cutoff`.** Experiment D
      used a uniform GNM 7.3 Å because `build_H_new`'s per-target cutoff
      was unavailable in that container — its own §3 flags this as a
      caveat that must be cleared "before the cryptic conclusion is
      trusted."
- [ ] **AMENDED 2026-08-31 (lane collision):** do **NOT** add mode shift to
      `task0282_pocket_selection_sweep.METRICS` or re-run that sweep this
      window. LANE B owns all `task0282` runs while it re-runs the extended
      cohort, and two implementers editing and running the same script
      produces results on a moving target. Evaluate mode shift **standalone**
      — its own ranker, scored against random, cluster-robust. Integration
      into `METRICS` (with [[TASK-0300]]'s cluster-mean selection fix, not
      the defective row-mean criterion) is a follow-up after Lane B lands.
- [ ] Report whether mode shift is independent of druggability and pocket
      size (partial correlation), since that independence is the entire
      reason for adding it.

## Constraint

Do **not** re-sweep the whole family looking for a new winner.
[[TASK-0300]] showed selection on 13 clusters is what breaks. Add the
metric, report its own standalone performance and its independence, and
leave selection alone.
