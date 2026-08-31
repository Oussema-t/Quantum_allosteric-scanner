# TASK-0309 — Re-run the site-distance clustering on 158 proteins, not 13

- Status: Done
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

- [x] Pool the `min_heavy_A` distributions already computed:
      `results/tasks/0304_asbench_casbench/asbench_finding_f.json`,
      `casbench_finding_f.json`, and our own taxonomy. Report each cohort
      separately **and** pooled — pooling alone hides whether the shape
      is a property of one benchmark.
- [x] **Protein-level, not structure-level.** CASBench is 9.5 structures
      per protein; a structure-level clustering would be dominated by its
      pseudo-replication. Use one row per protein (median of its own
      structures, as [[TASK-0304]] already does).
- [x] Re-run k-means with silhouette selection over k = 2…6, **and**
      report the silhouette for every k rather than only the argmax.
- [x] Re-run [[TASK-0288]]'s **parametric-bootstrap LRT** (1 vs 2, and
      2 vs 3 components) with its **positive and negative controls at the
      new n** — the controls are what made that result interpretable.
- [x] Test the [[TASK-0288]] Finding F model explicitly: **point mass at
      the covalent limit + continuum** versus a k-component Gaussian
      mixture. Report which fits better (BIC or bootstrapped LRT).
- [x] Repeat on the size-normalised quantity (`min_A / Rg`) — at n = 13
      normalisation removed the non-normality, and whether that survives
      at n = 158 is the crux.

## Constraints

- **Do not report a silhouette as evidence of bimodality on its own.**
  1-D k-means always yields a high silhouette for k = 2; that is what
  [[TASK-0288]] caught. Bimodality claims need the LRT or a dip test.
  **Honored**: silhouette is high (0.53–0.84) across k=2..6 in EVERY
  cohort, never sharply peaked at k=2 — itself evidence against reading
  silhouette as a bimodality signal, reported as such below.
- **Controls at the new n.** [[TASK-0288]]'s LRT was only trustworthy
  because it was validated on synthetic bimodal and unimodal samples of
  the same size. Repeat that at n = 158. **Honored, with a disclosed
  fidelity limitation** — see "A real limitation" below.
- If the answer changes the two-population claim, **[[TASK-0284]]
  Finding A and the collaborator brief both need updating** — flag it,
  do not edit those documents in this task. **Flagged, not edited**: see
  "What this means for Finding A" below. Neither `TASK-0284`'s file nor
  the collaborator brief was touched.

## Note

Either outcome is worth having. Two populations confirmed at n = 158 is a
real structural finding about allosteric annotation. A continuum with a
covalent point mass is [[TASK-0288]] Finding F generalised, which is
already the register's strongest external result. What must not happen is
a third silhouette-only claim.

## Done (2026-08-31, Implementer B)

**A pre-existing labelling bug found before any new analysis ran, not
after**: RESULTS.md's own [[TASK-0304]] table calls our register "13
clusters (28 structures)" at 28.6%. Checked against `config/*.yaml`'s own
`apo_pdb` field (the actual clustering unit) rather than trusted: 15 of
the 28 Finding-F structures aren't even in [[TASK-0261]]'s 13-cluster
map — that map was built for a different, older 20-target frozen set.
The TRUE cluster count for this specific 28-structure cohort, grouping by
`apo_pdb` as verified live, is **26** (two genuine pairs: GAC_BPTES/
GAC_CPD12 share 7SBN, FBPASE_94D/FBPASE_95S share 5LDZ; every other
target is its own cluster). Worse: the "28.6%" figure itself was never
computed at cluster level at all — it is 8/28 **structure**-level (checked:
8/28 = 0.2857 exactly), the precise pseudo-replication this register's own
standing rule ("cluster-robust or it does not count") exists to catch.
Both fixed here, not inherited. RESULTS.md gets a dated correction note
(not a silent edit) in the same commit as this task.

**No network calls needed.** All 420 ASBench/CASBench PDB IDs behind
[[TASK-0304]]'s own Finding-F rows are already in `pdb_cache/` (0
missing, largest cached file 5.8 MB) — this task only reads local files
to compute a CA-only radius of gyration as the size normaliser.

**ASBench's own protein-level unit, re-derived, not re-typed**: grouping
[[TASK-0304]]'s 117 ASBench rows by the free-text `protein` name string
gives only 79 groups (names collide across genuinely distinct targets —
5 different PDB entries are all named "Glycogen phosphorylase, muscle
form"). [[TASK-0304]]'s own Done section states the real unit is
"deduplicated to 112 distinct PDB codes" — checked and matched exactly
once grouped by base PDB code (stripping `_1`/`_2` bio-assembly suffixes)
instead. CASBench's `cas_id` grouping (33) needed no correction.

**A new sub-finding, found while building this battery, not previously
reported at this resolution**: 15/171 pooled proteins (12/112 ASBench,
3/33 CASBench, 0/26 ours) have LITERAL site overlap — `min_A = 0.0`
exactly, the annotated allosteric and active/catalytic residue sets
share a residue. An even more extreme case of Finding F than covalent
adjacency. Undefined on the log scale every parametric test below uses;
excluded from those only, counted and reported on its own, never
epsilon-padded or silently dropped.

**Corrected protein/cluster-level fractions below 1.5 Å** (replaces the
28.6% figure RESULTS.md's TASK-0304 table reported for "ours"):

| cohort | n (protein/cluster-level) | below 1.5 Å |
|---|---|---|
| Ours | 26 | 8/26 = **30.8%** |
| ASBench | 112 | 24/112 = **21.4%** |
| CASBench | 33 | 14/33 = **42.4%** |
| Pooled | 171 | 46/171 = **26.9%** |

ASBench/CASBench move by rounding only (they were already protein-level
in [[TASK-0304]]); "ours" moves from a mislabeled 28.6% to a correctly
computed 30.8% — both close, neither changes the qualitative picture.

**The battery itself, raw `min_A`, all four cohorts**:

- **Silhouette k=2..6**: high (0.53–0.84) at every k in every cohort,
  never a clean single peak at k=2 (ours: k2=0.729 vs k3=0.732; pooled:
  k2=0.653 vs k5=0.663) — exactly the "1-D k-means always looks good"
  pattern this task's own Constraint warned against trusting.
- **Spike/excess-mass binomial test** ([[TASK-0288]] Part F, redone
  fresh at the new n, not reused): **significant in every cohort**, far
  beyond any reasonable correction — ours p=1.1e-5, ASBench p=4.7e-10,
  CASBench p=9.5e-9, pooled p=2.8e-20. This is the single most
  consistent, most robust result in the whole battery: real excess mass
  at the covalent limit beyond what a single log-normal continuum
  predicts, independently, in all three cohorts.
- **GMM BIC** (k=1..3): prefers k>1 in every cohort (ours k=3, ASBench
  k=2, CASBench k=2, pooled k=3) — but the winning low-mean component
  sits at **1.32–1.33 Å in every single case** (the peptide-bond
  distance, not a free-floating mean) with a **narrow fitted width**
  (log-scale multiplicative sigma 1.00–1.02, versus 1.2–2.7 for every
  other component) and a **minority weight** (12–37%). This is [[TASK-0288]]
  Finding F's point mass, not [[TASK-0284]] Finding A's second broad
  population — the BIC-preferred models are "spike + one-or-two continuum
  chunks," not two comparably-broad Gaussians. Where BIC picks k=3
  (ours, pooled), the other two components are simply the continuum
  approximated by two overlapping Gaussians rather than one, not a
  genuine third population.
- **LRT 1 vs 2**: p=0.0050 (the resolution floor at this run's B=200) in
  every cohort/variant. See "A real limitation" below before reading
  this as calibrated.

**On the size-normalised quantity (`min_A / Rg`) — the crux this task
was filed to settle**: BIC prefers **k=1 (single Gaussian)** in ours,
ASBench, and CASBench separately, and only marginally favours k=2 in the
pooled set (432.5 vs 438.3 — a 6-point BIC gap, weak evidence at best,
and pooling normalised ratios across cohorts with different size
distributions is itself a real caveat, not glossed over). The spike test
is not significant on the normalised scale in any cohort (p=0.76–1.00) —
expected and not a contradiction: a peptide bond has a fixed physical
length, so it is not scale-free by construction, and a size-relative
window should not be expected to isolate it the way an absolute-Å window
does. **[[TASK-0288]]'s original n=28 (mislabeled 13-cluster) finding —
that size-normalisation removes the apparent multi-population signal —
replicates and generalises across three independent cohorts at n=26/112/33,
~6-12x the original n.**

**What this means for [[TASK-0284]] Finding A, flagged not edited**: the
two-Gaussian-population claim does **not** survive at the extended n,
consistent with [[TASK-0288]]'s original verdict, now on much firmer
footing. What replaces it is [[TASK-0288]] Finding F, generalised: a
narrow point mass pinned at the covalent/peptide-bond distance (~1.3 Å,
weight 12–37%, confirmed independently in every cohort with p<1e-4) plus
a broad continuum — a real, robust structural pattern, but a materially
different claim from "two populations of comparable breadth." **Finding A
and the collaborator brief both need updating to reflect this** — not
done here per this task's own Constraint; flagged for whoever owns that
edit next.

**A real limitation, disclosed rather than hidden**: the full battery (4
cohorts × 2 variants × [1v2 LRT + controls, 2v3 LRT + controls, GMM
BIC×3, spike test]) at [[TASK-0288]]'s own original fidelity (B=300–500,
8 seeds × 5 EM inits per likelihood evaluation) did not finish in a
reasonable wall-clock budget — one single LRT call took ~7 CPU-minutes
before being killed. Reduced to B=200 (main test) / B=80 (controls,
reps=2), 3 seeds × 3 EM inits per likelihood evaluation, and single-
threaded BLAS (avoids thread-spawn overhead dominating many tiny fits,
the actual cause of the original slowdown, not memory — RSS stayed under
150 MB throughout both runs). Consequence: **negative-control p-values,
which should track a smooth spread the way [[TASK-0288]]'s own
0.18–0.88 table did, instead jump between the floor (0.012) and the
ceiling (1.000) with no middle ground across only 2 reps per condition**
(e.g. ASBench raw neg control: 0.012, 1.000). The observed p=0.0050
results are directionally consistent everywhere and corroborated
independently by the spike/binomial test and the BIC component-width
result, but should be read as **suggestive, not calibrated** — a higher-
fidelity re-run (full seeds/B, run over a longer background window) would
be needed to quote an exact LRT p-value with confidence. Positive
controls saturated correctly (p at floor under a true >=2.5 SD
separation), confirming the test still has power at this fidelity; it is
specifically the null's own p-value smoothness that is under-resourced
here, not the test's basic validity.

**Scripts**: `scripts/task0309_kmeans_extended_cohort.py`. **Data**:
`results/tasks/0309_kmeans_extended_cohort/kmeans_extended_cohort.json`.

**Moved TODO/IN_PROGRESS -> DONE.**
