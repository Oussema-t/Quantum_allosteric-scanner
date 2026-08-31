# TASK-0306 — Is *which of the six measures fires* predictable? The meta-classifier, on a cohort that can support one

- Status: TODO
- Priority: High — the first version of the meta-selector question with enough data to answer it
- Filed: 2026-08-31 by Reviewer thread
- Related: [[TASK-0305]], [[TASK-0301]], [[TASK-0300]], [[TASK-0304]]

## Why now

[[TASK-0301]] closed the meta-selector on our own cohort for two reasons.
Both are now lifted:

1. **13 clusters could not validate a selector.** ASBench + CASBench give
   **432 structures across 146 proteins**.
2. **Our 61 rules were one signal at 61 settings**, so ensembling was
   provably futile. Their six measures are **not** that: `pR` vs `pb` is
   residue- vs bond-level, and the surrogate-CI, high-propensity-proportion
   and reference-quantile tests ask structurally different questions.

## The observation this is built on

From [[TASK-0304]]'s decomposition of their own `Summary` column
(ASBench, without allosteric ligand):

| detected by | count |
|---|---|
| ≥ 1 of 6 | 99/118 = 83.9% |
| all 6 | 21/118 = 17.8% |

**78 structures sit in between** — some measures fire, others do not. If
which-measure-fires is predictable from protein properties, that is a real
meta-classifier with 118 (+314) labelled examples. If it is not, the 84%
is a disjunction over six noisy tests and the honest figure is nearer
17.8%.

**Both outcomes are worth reporting.**

## Scope

- [ ] Parse the ●/○ `Summary` column from Tables S3/S4 (ASBench,
      with/without ligand) and S5/S6 (CASBench) into a per-structure
      6-bit outcome vector. Already downloaded to
      `results/tasks/0304_asbench_casbench/`.
- [ ] Descriptive first: how many distinct 6-bit patterns occur, and how
      concentrated are they? If a handful dominate, the measures are
      redundant and the meta-classifier premise is weak.
- [ ] Pairwise agreement / correlation between the six measures. **This is
      the [[TASK-0301]] test applied to their family** — if the six are as
      correlated as our 61 were, the same verdict follows and this task
      stops here.
- [ ] Only if they are genuinely independent: predict which measures fire
      from protein-level descriptors (N, fold class, oligomeric state,
      site separation from [[TASK-0304]]'s own distance computation),
      held out by **protein**, not structure.

## Constraints

- **Protein-level held-out evaluation.** CASBench is 314 structures over
  33 proteins — 9.5 per protein. Structure-level splits would repeat
  [[TASK-0261]]'s pseudo-replication at 10× scale.
- Report the redundancy result even if it kills the task. [[TASK-0301]]'s
  value was the *reason* consensus failed, not the failure.
