# TASK-0309 — Re-run the site-distance clustering on 158 proteins, not 13

- Status: TODO
- Priority: **High — [[TASK-0284]] Finding A is quoted in the collaborator brief and rests on 28 structures; [[TASK-0288]] already found it did not survive a proper bimodality test at that n**
- Filed: 2026-08-31 by Reviewer thread, at the repo owner's direction
- Related: [[TASK-0284]], [[TASK-0288]], [[TASK-0297]], [[TASK-0304]]

## Why

[[TASK-0284]] Finding A reported **two populations** of allosteric-site
distance — k-means silhouette **0.7367**, sizes 24/9, on 33 pocket rows.
[[TASK-0288]] then showed that at the true n (28 structures, 13 clusters)
the evidence is much weaker:

- silhouette survives size-normalisation (0.7220 raw, 0.7518 on `min_A/Rg`)
- but **Shapiro non-normality does not** (p = 0.0067 raw → **0.19** normalised)
- and a **parametric-bootstrap LRT for 1 vs 2 Gaussian components gives
  p = 0.11** — *not distinguishable from unimodal*

[[TASK-0288]] Finding F then found what the distribution is actually made
of: a **point mass at the peptide-bond distance** plus a continuum, which
is a different object from two Gaussian clusters.

**The cohort is now ~12× larger.** [[TASK-0304]] supplies annotated
allosteric-and-catalytic site pairs for **ASBench (117 structures / 112
proteins)** and **CASBench (313 structures / 33 proteins)**, on top of our
own 28/13. That is enough to settle it.

## Scope

- [ ] Pool the `min_heavy_A` distributions already computed:
      `results/tasks/0304_asbench_casbench/asbench_finding_f.json`,
      `casbench_finding_f.json`, and our own taxonomy. Report each cohort
      separately **and** pooled — pooling alone hides whether the shape
      is a property of one benchmark.
- [ ] **Protein-level, not structure-level.** CASBench is 9.5 structures
      per protein; a structure-level clustering would be dominated by its
      pseudo-replication. Use one row per protein (median of its own
      structures, as [[TASK-0304]] already does).
- [ ] Re-run k-means with silhouette selection over k = 2…6, **and**
      report the silhouette for every k rather than only the argmax.
- [ ] Re-run [[TASK-0288]]'s **parametric-bootstrap LRT** (1 vs 2, and
      2 vs 3 components) with its **positive and negative controls at the
      new n** — the controls are what made that result interpretable.
- [ ] Test the [[TASK-0288]] Finding F model explicitly: **point mass at
      the covalent limit + continuum** versus a k-component Gaussian
      mixture. Report which fits better (BIC or bootstrapped LRT).
- [ ] Repeat on the size-normalised quantity (`min_A / Rg`) — at n = 13
      normalisation removed the non-normality, and whether that survives
      at n = 158 is the crux.

## Constraints

- **Do not report a silhouette as evidence of bimodality on its own.**
  1-D k-means always yields a high silhouette for k = 2; that is what
  [[TASK-0288]] caught. Bimodality claims need the LRT or a dip test.
- **Controls at the new n.** [[TASK-0288]]'s LRT was only trustworthy
  because it was validated on synthetic bimodal and unimodal samples of
  the same size. Repeat that at n = 158.
- If the answer changes the two-population claim, **[[TASK-0284]]
  Finding A and the collaborator brief both need updating** — flag it,
  do not edit those documents in this task.

## Note

Either outcome is worth having. Two populations confirmed at n = 158 is a
real structural finding about allosteric annotation. A continuum with a
covalent point mass is [[TASK-0288]] Finding F generalised, which is
already the register's strongest external result. What must not happen is
a third silhouette-only claim.
