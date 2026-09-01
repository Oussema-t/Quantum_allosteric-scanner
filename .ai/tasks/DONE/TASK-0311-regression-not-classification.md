# TASK-0311 — On a continuum, predict the distance. Stop building classifiers.

- Status: Done
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

- [x] Target: `min_heavy_A` (and the scale-free `min_A / Rg`) as a
      **continuous** response, one row per protein, across the pooled
      171-protein cohort from [[TASK-0309]].
- [x] Predictors: the descriptors already computed and already shown not
      to *classify* — N, Rg, compactness, chain count, fold class
      ([[TASK-0306]] addendum), site sizes, and the landscape features
      (Scope named [[TASK-0300]]; that task never computed any —
      [[TASK-0288]]'s own were used instead, see Done). **The point is
      that a variable can carry monotone information without supporting
      a threshold.**
- [x] Metric: out-of-sample **Spearman** and MAE, held out **by protein**.
      Report against a permuted-target null, not against R² alone.
- [x] Explicitly model the mixture: **a point mass at the covalent limit
      plus a continuum.** A two-part model (logistic for "is it at the
      floor" + regression on the remainder) is the honest functional form
      and directly encodes [[TASK-0288]] Finding F.
- [x] Report whether the covalent-floor half is predictable even if the
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

## Done (2026-09-01, Implementer C)

**One Scope correction, found before building anything, not silently
worked around**: this task's own Scope names "the landscape features
from [[TASK-0300]]" — [[TASK-0300]] never computed any (it is the
rule-selection-defect task). The fpocket-derived landscape descriptors
(candidate-pocket spread, druggability gap, distance-to-seed) are
[[TASK-0288]]'s own (`results/tasks/0288_contact_spike/`), reused
instead, which is clearly what was meant — [[TASK-0288]] is in this
task's own Related list and Why section, TASK-0300 is not connected to
landscape features anywhere in the register.

**Data build**: pooled 171-protein table (26 ours / 112 ASBench / 33
CASBench, 0 skipped in every cohort — all 420 PDB IDs were already
cached, confirmed by [[TASK-0309]]). N/Rg/compactness use each cohort's
own already-established scoping convention rather than a new one:
"ours" reuses [[TASK-0284]]'s `t0242.prep`-scoped N/Rg (restricted to
each target's configured functional chain(s)); ASBench/CASBench reuse
[[TASK-0306]]'s `structure_descriptors()` (the whole deposited
asymmetric unit). **Checked, not assumed, before choosing this**:
restricting ASBench/CASBench to the chains named in the site
annotations was tried first and abandoned — citrate synthase (1NXE,
CASBench) names allosteric-site chains 'C'/'F' that do not exist in the
raw ASU file (symmetry-generated copies), so that path would silently
undercount N for exactly the multimeric proteins where site geometry
matters most. The disclosed consequence: N/Rg's absolute scale differs
by cohort (single functional chain vs whole ASU) — `compactness`
(Rg/N^(1/3)) is more robust to this than either alone since both use the
same per-cohort convention, and Part 3 below tests for the confound
directly by refitting within each cohort alone.

**Literal site overlap** ([[TASK-0309]]'s own finding: `min_A = 0.0`
exactly for 15/171 — 12 ASBench, 3 CASBench, 0 ours) is undefined on
every log-scale test below and excluded from those only, same convention
[[TASK-0309]] established — never epsilon-padded, always counted.

**Method note**: the binary "at the covalent floor" (`min_A < 1.5`,
[[TASK-0309]]'s own threshold) target is scored with a linear-
probability-model + `roc_auc_score`, not a true logistic fit — this
register's own established way to LOPO-score a binary target
([[TASK-0306]]'s `meta_classifier`, reused verbatim). Permutation nulls
throughout use the empirical null distribution (two-sided, not
symmetric-around-zero/0.5) since LOPO-OLS null distributions run
asymmetric at small n (`null_rho_mean` as low as −0.5 in the n=25 arms
below) and no per-feature direction is pre-registered for Part 5's
univariate scan.

### Part 1 — the two-part model (pooled, N/Rg/compactness/n_chains/site_size)

| test | n | metric | value | p (perm) |
|---|---|---|---|---|
| floor logistic (at/not at 1.5Å) | 171 | AUC | **0.657** | **0.004** |
| continuum, non-floor subset | 125 | Spearman | 0.127 | 0.096 |
| continuum, ALL log-defined rows (no split) | 156 | Spearman | 0.311 | 0.004 |

**The floor half is predictable; the continuous half, pooled, is not** —
exactly the asymmetric outcome this task's own Scope anticipated as
worth reporting on its own. The unsplit fit (row 3) looks strong, but
that is a floor-vs-continuum artifact, not real continuous signal: the
floor cases cluster tightly near a fixed log-value, so a model that
merely separates floor from non-floor scores well on the full range
without saying anything about position *within* the continuum — which
is exactly what row 2 tests directly, and row 2 is not significant.
**The two-part decomposition this task's Scope required is what caught
this; the unsplit number alone would have been reported as a positive
result and been wrong about why.**

### Part 2 — scale-free target (`min_A / Rg`, N/compactness/n_chains/site_size, Rg dropped to avoid denominator circularity)

| subset | n | Spearman | p |
|---|---|---|---|
| all 171 | 171 | 0.035 | 0.359 |
| non-floor | 125 | 0.171 | **0.020** |

Scale-free, restricted to the non-floor continuum, is the one pooled
continuous-target result that clears p<0.05 — but on a different
predictor set (no Rg) than Part 1's row 2, so the two are not directly
comparable, and it does not survive the per-cohort check below.

### Part 3 — per-cohort robustness check (does the pooled signal replicate within one cohort?)

| cohort | n | Spearman | p |
|---|---|---|---|
| ours | 26 (0 excluded) | 0.344 | 0.098 |
| asbench | 100 (12 excluded) | 0.085 | 0.258 |
| casbench | 30 (3 excluded) | 0.340 | 0.074 |

**None individually significant.** This is the test the disclosed N/Rg
scoping mismatch (Part "Data build" above) demanded: if the pooled
non-floor/scale-free signal were a real cross-protein relationship it
should show up, even weakly, within at least one cohort on its own. It
does not — "ours" and "casbench" trend the same direction as the pooled
fit (rho 0.34 each) but neither clears significance at these n, and
ASBench alone is flat. **Consistent with "no real standalone continuous
signal from this predictor set," not with a cohort-scoping artifact
manufacturing a false positive** (a scoping artifact would predict the
per-cohort numbers to be null while the pooled number stays strong,
which is roughly what is seen — but the honest reading is "underpowered
everywhere," not "positive pooled, therefore real.")

### Part 4 — ASBench-only, fold class added ([[TASK-0306]] addendum's own Alpha-Beta vs Mainly-Alpha)

| predictors | n | Spearman | p |
|---|---|---|---|
| N/Rg/compactness/n_chains/site_size | 92 | 0.116 | 0.194 |
| + fold class | 92 | **0.215** | **0.028** |

**The one clean positive result in the pooled/cross-cohort half of this
task.** Adding the fold-class dummy moves the fit from non-significant
to significant, on the same 92 rows. Effect size is modest (rho 0.12 →
0.22) and this is ASBench-only (fold class is not available for
"ours"/CASBench, [[TASK-0306]] addendum's own limitation, inherited
here). Not independently replicated on another cohort — flagged as a
genuine but single-cohort finding, not over-claimed as general.

### Part 5 — "ours"-only, [[TASK-0288]]'s own 13 fpocket landscape features (univariate LOPO, n=25 protein clusters)

| feature | Spearman | p | |
|---|---|---|---|
| max_d | 0.654 | **0.002** | |
| median_d | 0.576 | **0.004** | |
| n_cand_far | 0.563 | **0.004** | |
| size_wtd_d | 0.507 | **0.004** | |
| frac_cand_far | 0.478 | 0.012 | |
| d_biggest | −0.563 | 0.843 | |
| max_drug_all | −0.646 | 0.657 | |
| (7 others) | 0.01–0.25 | 0.08–0.58 | not significant |

**Five features are individually significant — but they are one signal,
not five**, exactly [[TASK-0301]]'s own warning about this rule family
("functions of the same two-or-so raw inputs"): pairwise Pearson among
`{max_d, median_d, n_cand_far, size_wtd_d, frac_cand_far}` is 0.64–0.95
(checked, not assumed). All five are variants of "how spread out / how
many candidate pockets sit far from the seed" — this is [[TASK-0288]]'s
own "landscape spread" finding (that task's in-sample Spearman was
+0.568, p=0.0025), **now confirmed under genuine leave-one-out
out-of-sample prediction with a permutation null**, a strictly stronger
test than the in-sample correlation TASK-0288 originally ran. `d_biggest`
and `max_drug_all` run in the opposite direction (negative, not
significant) — a large or highly druggable single top candidate does
NOT itself predict distance; it is specifically the *number/spread of
candidates far from the seed* that does.

**Caveat, stated plainly**: n=25. Bonferroni across 13 tests would need
p<0.0038; `max_d` (0.002) clears it, `median_d`/`n_cand_far`/`size_wtd_d`
(0.004 each) sit right at that line — and Bonferroni over 5 near-
duplicate tests of one construct is itself the wrong correction (too
strict for correlated tests, too lax for one). Read this as **one
corroborated finding**, not five. Extending it to ASBench/CASBench needs
fresh fpocket runs on ~145 more structures — explicitly out of this
task's own "No new descriptors" Constraint, left for whoever picks that
up next.

### Verdict

**Regression is not the clean win the task's framing might have hoped
for, but it is not the flat failure either — it is exactly the mixed,
honest result the Note said either outcome would be worth having.**

1. **The floor/continuum split itself is real and predictable** (AUC
   0.657, p=0.004): whether a protein's site pair sits at the covalent
   limit is inferable from cheap structural descriptors.
2. **The continuous remainder is not predictable from N, Rg,
   compactness, chain count, or site size, pooled or per-cohort** — the
   one nominally-significant pooled number (Part 1c) is an artifact of
   not splitting the floor out, and does not survive the per-cohort
   check (Part 3).
3. **Fold class adds a small, real, ASBench-only signal** (Part 4) —
   the first descriptor in this whole register to move a continuum fit
   from null to significant, albeit modestly and on one cohort only.
4. **The strongest real result is [[TASK-0288]]'s own landscape-spread
   signal, now validated out-of-sample** (Part 5) — but it is "ours"-
   only (n=25), one construct at five parameter settings, and not yet
   testable cross-cohort without new fpocket computation.

**Net**: this register's own N/Rg/compactness/chain-count/site-size
family — the cheapest, most-already-computed predictors — carries at
most a small, cohort-specific continuous signal (fold class) beyond the
floor/continuum split itself. The fpocket landscape family is the one
descriptor type that clearly works, on the one cohort it has been
computed for.

**Not done**: cross-cohort landscape features (ruled out by this task's
own Constraint); a single combined multivariate model spanning all
predictor families (fold class and landscape are each available on only
one cohort/subset, so a common design matrix across all three cohorts
does not exist without imputation, which was not attempted); regularised
(ridge/lasso) multivariate fits — plain LOPO-OLS was used throughout for
consistency with this register's own established convention
([[TASK-0249]]/[[TASK-0282]]/[[TASK-0306]]'s own `_fit_ols`/
`lopo_predict`).

**Script**: `scripts/task0311_regression_not_classification.py`. **Data**:
`results/tasks/0311_regression_not_classification/regression_not_classification.json`.

**Moved TODO/IN_PROGRESS -> DONE.**
