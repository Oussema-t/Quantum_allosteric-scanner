# TASK-0306 — Is *which of the six measures fires* predictable? The meta-classifier, on a cohort that can support one

- Status: Done
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

- [x] Parsed the ●/○ `Summary` column from Tables S3/S4 (ASBench,
      with/without ligand) and S5/S6 (CASBench) into per-structure 6-bit
      vectors — fetched live from Europe PMC's `supplementaryFiles`
      endpoint ([[TASK-0304]]'s own route), not from a pre-existing local
      cache (none existed; "already downloaded" referred to the PDB ID
      cohort, not these tables). Control: reproduced [[TASK-0304]]'s own
      105/118, 99/118, 27/118, 21/118 counts exactly before trusting the
      parse for CASBench.
- [x] Descriptive: 36–48/64 distinct patterns per condition, top-3 cover
      only 35–42% — not dominated by a handful.
- [x] Pairwise phi-coefficient across all 15 measure pairs: mean 0.419
      (ASBench primary), 0.21–0.42 across all 4 conditions. Pre-registered
      gate (mean|phi| < 0.6, stated before computing it): **PASSES** —
      moderate, not the near-total collinearity TASK-0301's 61-rule
      family would produce. No pR-vs-pb block structure either.
- [x] Since the gate passed: predicted which measures fire from N,
      oligomeric state (chain count), and site separation
      ([[TASK-0304]]'s own Finding-F distance), LOPO **by protein**
      (79 clusters, ASBench only — CASBench excluded, its own site
      annotations aren't extracted yet and 314/33 structures-per-protein
      is exactly this task's own Constraint). **Result: no signal** —
      5/6 measures at or below chance (AUC 0.337–0.483), `n_fired`'s
      nominally-significant LOPO rho (−0.220, p=0.017) unsupported by any
      individual univariate correlation (all p>0.28). A positive control
      (predict one measure from the other five's own bits — a relationship
      already known real) gave AUC 0.74–0.88, confirming the harness
      itself works; the null is in the descriptor set, not the pipeline.

## Constraints

- **Protein-level held-out evaluation.** CASBench is 314 structures over
  33 proteins — 9.5 per protein. Structure-level splits would repeat
  [[TASK-0261]]'s pseudo-replication at 10× scale. **Honored**: the
  meta-classifier step ran on ASBench only for exactly this reason.
- Report the redundancy result even if it kills the task. [[TASK-0301]]'s
  value was the *reason* consensus failed, not the failure. **Honored**:
  the redundancy gate passed (this task did not stop there), but the
  meta-classifier itself still returned a negative, reported in full with
  its own positive control, not smoothed into "inconclusive."

## Done (2026-08-31, Implementer A)

**Two distinct outcomes, not one**, exactly as this task's own "Why now"
section anticipated: the redundancy question and the meta-classifier
question are separable, and they came out differently. The six measures
are NOT the 61-rules failure mode (mean|phi|=0.419, well under the
pre-registered 0.6 bar, no pR/pb block collapse) — genuinely more
independent evidence than our own rule family ever was. But the specific,
readily-available protein-level descriptors tried (N, chain count, site
separation) carry no real signal about which measure fires.

**Standing rule honored, not skipped under time pressure**: added a
positive control (predict one measure from the other five) using the
identical `lopo_predict`/`roc_auc_score` code path as the negative result
above -- AUC 0.74-0.88, proving the harness detects real signal when
present. Without this, the below-chance per-measure AUCs (0.337-0.483)
would be genuinely ambiguous between "real negative relationship" and
"broken pipeline"; with it, neither -- most likely LOPO/regression
instability on 3 weak, mutually correlated predictors, stated as such
rather than overclaimed either direction.

**Lane discipline**: per `.ai/COMPUTE_WINDOW_2026-08-31.md`'s own 4-lane
split (Lane A = this task, exclusive owner of `results/tasks/0306_*` and
the S3-S6 parsing), stayed off `config/`, all `task0282` runs, and
CASBench ingestion (Lane B's own territory) -- the CASBench exclusion
from the meta-classifier step was an independent arrival at the same
boundary the coordination doc had already drawn, not a negotiated one.

**What remains, disclosed not silently dropped**: fold class (this
task's own Scope named it) was never tested -- would need an external
SCOP/CATH/Pfam lookup, judged out of this session's scope. If Lane B's
CASBench site annotations land, the meta-classifier step (N, chains, site
separation) can be re-run there directly with this same code, still LOPO
by protein.

**Script:** `scripts/task0306_six_measure_meta_classifier.py` (fetches
live each run, no cached upstream binary committed). **Data:**
`results/tasks/0306_six_measure_meta_classifier/six_measure_analysis.json`.

**Moved TODO/IN_PROGRESS -> DONE.**

---

## Addendum (2026-08-31, Reviewer thread) — fold class tested, and it fails

This task disclosed fold class as its one untested predictor. Closed now,
negatively, in the hour before the collaborator sync.

CATH/SCOP top-level class pulled live from the RCSB Data API
(`polymer_entity_instance` → `rcsb_polymer_instance_annotation`) for
**111 of 113** ASBench structures. Distribution is heavily skewed —
Alpha-Beta 88, Mainly-Alpha 23, everything else too thin to use — so the
test is effectively two classes.

| measure | alpha-beta | mainly-alpha | Fisher p |
|---|---|---|---|
| pR surrogate-CI | 40/88 | 13/23 | 0.360 |
| pb surrogate-CI | 37/88 | 14/23 | 0.158 |
| P(pR>.95) | 33/88 | 10/23 | 0.636 |
| P(pb>.95) | 42/88 | 11/23 | 1.000 |
| ref pR | 52/88 | 16/23 | 0.472 |
| ref pb | 54/88 | 20/23 | 0.025 |

**Bonferroni α = 0.0083. NONE survives.** Number of measures firing does
not differ either: 2.93 vs 3.65, Mann-Whitney **p = 0.140**.

One descriptive curiosity, explicitly **not** a finding at this n:
mainly-alpha proteins almost always get *something* to fire — **1/23**
score zero against **17/88** for alpha-beta.

**Consequence.** Every cheap protein-level predictor is now exhausted:
size, chain count, site separation ([[TASK-0306]] main run) and fold
class (here). The redundancy gate still passes — the six measures *are*
independent evidence, mean |φ| = 0.419 — so the discriminator premise
survives. What fails is predicting which fires from a lookup. It needs a
genuinely new descriptor, or the per-residue propensity fields
themselves. Phase-2 work.

Data: `results/tasks/0306_six_measure_meta_classifier/fold_class_annotations.json`.
