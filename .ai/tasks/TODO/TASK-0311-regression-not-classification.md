# TASK-0311 — On a continuum, predict the distance. Stop building classifiers.

- Status: TODO
- Priority: High — reframes every failed discriminator attempt as the wrong problem shape
- Filed: 2026-09-01 by Reviewer thread
- Related: [[TASK-0309]], [[TASK-0300]], [[TASK-0301]], [[TASK-0306]], [[TASK-0288]]

## Why

[[TASK-0309]] settled it on 171 proteins: **there are no discrete
near/far populations.** Silverman's critical-bandwidth test is consistent
with unimodal in every cohort (ours p=0.81, ASBench p=0.14, CASBench
p=0.11; and still unimodal with the covalent spike removed), and the
k-means best-k wanders incoherently across cohorts (3 / 4 / 2 / 5) — the
signature of 1-D k-means splitting a continuum, exactly as [[TASK-0288]]
warned.

**Every discriminator attempt in this register has been a classifier.**
[[TASK-0300]]'s stratified rules needed categories. [[TASK-0306]]'s
meta-classifier predicts which measure fires. [[TASK-0288]]'s descriptor
probes predicted near-vs-far membership. **All of them assume classes
that the data says do not exist.**

On a continuum the well-posed problem is **regression**, and this register
has never once tried it.

## Scope

- [ ] Target: `min_heavy_A` (and the scale-free `min_A / Rg`) as a
      **continuous** response, one row per protein, across the pooled
      171-protein cohort from [[TASK-0309]].
- [ ] Predictors: the descriptors already computed and already shown not
      to *classify* — N, Rg, compactness, chain count, fold class
      ([[TASK-0306]] addendum), site sizes, and the landscape features
      from [[TASK-0300]]. **The point is that a variable can carry
      monotone information without supporting a threshold.**
- [ ] Metric: out-of-sample **Spearman** and MAE, held out **by protein**.
      Report against a permuted-target null, not against R² alone.
- [ ] Explicitly model the mixture: **a point mass at the covalent limit
      plus a continuum.** A two-part model (logistic for "is it at the
      floor" + regression on the remainder) is the honest functional form
      and directly encodes [[TASK-0288]] Finding F.
- [ ] Report whether the covalent-floor half is predictable even if the
      continuous half is not — those are separate questions and only the
      first has ever been implicitly attempted.

## Constraints

- **Held out by protein.** CASBench is 9.5 structures per protein.
- **No new descriptors.** This task tests whether the *existing* ones
  carry monotone information; adding features conflates two questions.
- If regression also fails, that is a real and reportable result: it
  would mean the site position is not merely unclassifiable but
  **unpredictable from apo structure at any resolution** — a stronger and
  cleaner negative than anything currently in the register.

## Note

This is cheap. Every input already exists in
`results/tasks/0309_kmeans_extended_cohort/` and
`results/tasks/0304_asbench_casbench/`. It is a reframing, not a new
measurement campaign.
