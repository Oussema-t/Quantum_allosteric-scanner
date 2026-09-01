# TASK-0317 — Discriminator B: the failure is the feature *kind*, not the feature count — test per-measure applicability descriptors

- Status: Done
- Priority: Medium-High — [[HYP-P14]]'s secondary route, the only discriminator line whose premise passed its own gate
- Filed: 2026-09-01 by Reviewer thread
- Related: [[TASK-0300]], [[TASK-0301]], [[TASK-0305]], [[TASK-0306]], [[TASK-0287]], [[HYP-P14]]

## The premise that passed, and the one that keeps failing

[[TASK-0306]]'s redundancy gate **passed**: the six bond-to-bond statistical
measures have mean pairwise |φ| = **0.419**, well under the pre-registered
0.6 bar — genuinely six independent opinions, unlike our own 61-rule family
([[TASK-0301]] showed those were one signal at 61 settings). **78 of 118**
ASBench structures sit strictly between "one measure fires" and "all six
fire", which is the signature of different measures suiting different
proteins. The field's headline 84% is a six-way disjunction ([[TASK-0305]]:
99/118; ≥3 of 6 = 57.6%; all 6 = 17.8%) — a working selector would convert
that disjunction into a method.

**Every predictor tried has failed, and they are all the same kind of thing:**

| predictor | result | source |
|---|---|---|
| N (chain length) | per-measure AUC 0.337–0.483 | [[TASK-0306]] |
| chain count | same | [[TASK-0306]] |
| site separation | same | [[TASK-0306]] |
| fold class | fails | [[TASK-0306]] addendum |
| positive control (predict one measure from the other five) | **AUC 0.74–0.88** | [[TASK-0306]] |

The positive control is the important row: **the harness detects real signal
when it is present.** The negative results are about the inputs, not the
apparatus.

## The hypothesis this task tests

**Inference, not measured — stated as a hypothesis, per this register's own
convention.** Every predictor tried is a **global protein descriptor**.
Nothing tried describes either:

- **(a) the local structural environment** the measure operates in, or
- **(b) the applicability preconditions of each individual measure.**

The six are bond-to-bond propensity statistics. Each is well-posed only under
certain structural conditions. Those conditions are computable **from
machinery already in this repo** — `allostery.potentials.gnm_context`, the
contact graph, the fpocket candidate landscape — with no new data, no MD, no
external tool, no new cohort.

**Why recombining existing features cannot be the answer, and why this is not
that:** [[TASK-0301]]'s lesson generalises — any combination of features stays
inside the span of those features, which is why voting/stacking over the 61
rules was dead on arrival. [[HYP-P14]]'s collapse table shows our span is
essentially proximity-to-seed, pocket size, and druggability (itself largely
size, [[TASK-0287]]).

**But that collapse was measured for features used as *rankers of residues
and pockets*. Discriminator B has a different target — predict which measure
fires for this protein. A feature can be useless as a ranker and informative
as a selector.** The collapse table does not rule this out, and no task has
tested it. That distinction is the whole reason this task is worth running
and is stated here so a future reader can reject it explicitly if wrong.

## Scope

- [x] Enumerate, for each of the six measures, its **stated applicability
      condition**, from the source paper (Wu, Strömich & Yaliraki 2022) —
      read, not recalled, and cited. This is the design step; do not skip to
      feature engineering.
- [x] Derive a computable descriptor per condition, **reusing existing
      machinery** (`gnm_context`, contact graph, fpocket landscape). Record
      which repo function each descriptor comes from.
- [x] Score with [[TASK-0306]]'s **identical** `lopo_predict`/`roc_auc_score`
      path — same code, so the new numbers are directly comparable to the
      0.337–0.483 already on record.
- [x] **Carry [[TASK-0306]]'s positive control unchanged** (predict one
      measure from the other five, expect AUC 0.74–0.88). A run without it is
      not reportable.
- [x] Report every descriptor, including the ones that fail. Rank by LOPO AUC.

## Constraints

- **LOPO by protein, always.** Four selection procedures in this register
  have died of pseudo-replication ([[TASK-0282]], [[TASK-0293]],
  [[TASK-0299]], [[TASK-0300]]). This is the obvious fifth candidate.
- **No neural net, and no free-parameter model, on the first pass.** The open
  question is whether *any* predictive feature exists; a flexible model on
  118 structures answers that question less clearly than a linear one, and
  cannot explain the causal link even if it succeeds. If a linear model on
  good features finds nothing, a NN on the same features is not the fix.
- **Do not re-tune the six measures.** They are the target, not the model.
- Bonferroni across the descriptor family, per [[TASK-0314]]'s standing
  multiplicity concern.

## What a negative licenses

If per-measure applicability descriptors also fail with the positive control
passing, that is a strong, publishable negative: **the six measures' firing
pattern is not predictable from structure at this cohort size** — which
closes Discriminator B properly, with an argument, rather than leaving it
open on an untested feature set. Report it with the same prominence as a
positive.

## Done (2026-09-01, Implementer C)

**Applicability conditions, read from the paper (PMC8767309), not
recalled**: (1) the surrogate-CI test matches 1,000 surrogate sites to the
true allosteric site on residue count and diameter — its own discriminative
power hinges on how much a local structural property varies among
same-size, compact surrogate windows elsewhere in the structure; (2) the
high-propensity-proportion test P(p>0.95) assumes "QS is uniformly
distributed" — not testable here, `QS` itself is the paper's own propensity
score and is not reproduced in this repo, only the six binary verdicts are
(flagged, not silently skipped); (3) an explicit stated caveat: "more
detailed analysis would be usually required... where the allosteric site
and the orthosteric site are in very close proximity... large and complex
multimeric proteins... or the role of structural water molecules" — three
concrete, computable conditions in one sentence.

**Three descriptors derived, reusing existing machinery, none re-deriving
[[TASK-0306]]'s already-failed global scalars**: `surrogate_spread` (std of
mean GNM MSF across 50 same-size, spatially-compact random windows —
`allostery.potentials.gnm_context`, a direct proxy for condition 1, cheaper
than reimplementing their 1,000-surrogate machinery); `interface_frac`
(fraction of the site's OWN residues in cross-chain contact — a LOCAL,
site-specific version of condition 3's "multimeric" clause, not raw chain
count, which [[TASK-0306]] already tried and killed); `water_density`
(crystallographic HOH atoms within 5Å of the site, normalised by site size —
condition 3's water clause, directly). fpocket-landscape-based descriptor
(also named as available machinery) was not attempted this pass — disclosed,
not silently dropped; see "Not done."

**Cohort**: ASBench, `asbench_without_ligand` (118 structures) — the SAME
primary condition [[TASK-0306]]'s own `meta_classifier` used, not the
`with_ligand` variant. 117/118 joined (1 skipped: 3BCR, unusable structure).
79 protein clusters, LOPO throughout.

**Bonferroni gate: 18 tests (3 descriptors × 6 measures), α=0.00278 — NONE
survive.** Every per-measure LOPO AUC sits in the same 0.05–0.57 band
[[TASK-0306]]'s own global descriptors already occupied (0.337–0.483) — no
better, several worse. Positive control **passes** (predict one measure from
the other five: AUC 0.742–0.877, matching TASK-0306's own 0.74–0.88
reference range) — the harness itself works; the negative is in these three
descriptors, not the apparatus.

**A genuine methodological finding, found and root-caused before trusting
any downstream number, not glossed over**: the `n_fired` (0–6) LOPO Spearman
regression — this task's own secondary check, mirroring [[TASK-0306]]'s own
`rho_nfired` — initially showed a startling result for two of the three
descriptors: `interface_frac` rho=−0.612 (p=2.2×10⁻¹³), `water_density`
rho=−0.727 (p=1.7×10⁻²⁰). Both would have been the strongest results in this
entire discriminator line. **Neither is real.** Root-caused directly, not
assumed: the RAW/pooled (un-fitted) Spearman correlation between each
descriptor and `n_fired` is ≈0 for both (`interface_frac` +0.015, p=0.87;
`water_density` +0.057, p=0.54) — the complete opposite of the LOPO number.
Traced to **heavy ties in the raw feature**: `interface_frac` has only 34
distinct values across 117 rows (71 rows are exactly 0.0); `water_density`
has 66. `surrogate_spread` (117/117 distinct — genuinely no ties) shows a
much smaller LOPO-vs-raw gap (LOPO rho=+0.015, p=0.87; raw rho=−0.151,
p=0.11) — both non-significant either way, so ties are not the *only*
source of LOPO/raw divergence (ordinary regression instability on a weak
signal produces some gap regardless), but they are what turns an ordinary,
harmless gap into a spurious result that clears p<10⁻¹² — the two tied
descriptors are roughly two orders of magnitude more extreme than the
untied one. Mechanism confirmed by inspecting the per-fold OLS
coefficients directly: the fitted slope is **stable** across all 79 LOPO
folds (77/79 same sign, fold-to-fold std=0.025 around a mean of −0.057 for
`interface_frac`) — this is *not* ordinary LOPO overfitting instability.
It is **tie-breaking**: dozens of rows share the exact same raw feature
value, and the tiny per-fold intercept jitter (a different single cluster
excluded each time) arbitrarily reorders those tied rows in the LOPO output —
and Spearman, being purely rank-based, is acutely sensitive to how ties
resolve. That arbitrary reordering happened to align with `n_fired` enough
to manufacture an apparently enormous, highly "significant" correlation out
of a genuinely null relationship. **This is a real, disclosable risk in this
register's own established `lopo_predict` + Spearman/AUC idiom
([[TASK-0306]]'s own convention, reused verbatim here and elsewhere) whenever
the input feature is low-cardinality/heavily tied** — worth carrying forward
to [[TASK-0314]]'s own standing metric-choice concern. The script now
computes and reports both the LOPO and raw/pooled `n_fired` correlation plus
an `n_distinct` diagnostic on every future run, flagging the risk explicitly
rather than requiring a reader to rediscover it.

**Corrected verdict: `n_fired` is not predictable by any of the three
descriptors either**, once the artifact is stripped out and the raw/pooled
correlation is read instead (`interface_frac` +0.015, p=0.87;
`water_density` +0.057, p=0.54; `surrogate_spread` −0.151, p=0.11 — all
null, none remotely close to significance at any reasonable threshold,
Bonferroni or not).

## Overall verdict

**The hypothesis this task tested does not survive.** Per-measure
applicability descriptors, grounded directly in the paper's own stated
conditions and reusing this repo's own GNM/contact-graph/water machinery,
predict neither which of the six measures fires (Bonferroni gate: 0/18) nor
how many fire (`n_fired`, all three null once the LOPO-tie artifact is
corrected) — with the positive control passing throughout, so this is a
real negative about the inputs, not a broken harness. Combined with
[[TASK-0306]]'s own global-descriptor negative (N, chain count, site
separation, fold class), **every predictor tried against these six measures
so far has failed** — the two-part hypothesis this task's own framing
offered ("a feature can be useless as a ranker and informative as a
selector") is not supported by anything tested to date. Per this task's own
"What a negative licenses" section, reported with the same prominence a
positive would have received.

**Not done**: a fpocket-candidate-landscape descriptor (named as available
machinery, not attempted — the paper's own explicit caveat sentence mapped
cleanly onto GNM/contact-graph/water, not onto pocket detection, and this
task's own effort budget did not extend to inventing a fourth, less
paper-grounded descriptor); condition 2 (the high-propensity-proportion
test's uniform-`QS` assumption) — not testable without the paper's own raw
propensity values, which this repo does not reproduce; CASBench (excluded
for the same reason [[TASK-0306]] excluded it — no independent site
annotations at the needed resolution yet).

**Script**: `scripts/task0317_discriminator_b_applicability.py`. **Data**:
`results/tasks/0317_discriminator_b_applicability/discriminator_b_applicability.json`.

**Moved TODO/IN_PROGRESS -> DONE.**
