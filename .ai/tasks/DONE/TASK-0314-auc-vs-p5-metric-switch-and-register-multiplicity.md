# TASK-0314 — The AUC/P@5 metric switch on one cohort, and the register has no family-wise error control

- Status: Done
- Priority: High — both defects are in the submission brief
- Filed: 2026-09-01 by Reviewer thread
- Related: [[TASK-0283]], [[TASK-0305]], [[TASK-0308]], [[TASK-0261]], [[TASK-0263]], [[TASK-0275]]

## Part A — two contradictory-sounding headlines on the identical 108 structures

`task0308_attribution_scaling.py:39` loads its `KEEP` set **from
[[TASK-0305]]'s own output**. Same 108 ASBench structures, same arms, same
seed and truth annotations.

| task | metric | CTQW | proximity | random |
|---|---|---|---|---|
| [[TASK-0305]] | mean P@5 | 0.0056 — **"significantly WORSE than random, p<1e-4, anti-correlated"** | `hop_near` 0.0093 / `hop_far` 0.0037 | 0.0171 |
| [[TASK-0308]] | mean AUC | 0.5921 (**+18.4%**) | 0.6147 (**+22.9%**, best arm) | 0.5 |

**Both tables are in the brief. Neither references the other.** Read cold, one
says our operators are anti-correlated with the label and the other says
proximity captures a fifth of the available signal.

They *are* reconcilable, and [[TASK-0305]] already supplies the mechanism —
*"our operators rank extremes... an annotated allosteric site is not an extreme
— it is an ordinary buried pocket that happens to be functionally coupled."* A
score can hold AUC 0.59 across the whole ranking while its top-5 is worse than
random. **That reconciliation is nowhere written down**, and without it the
brief reads as though the AUC table is the result and the P@5 table is a
separate embarrassment.

Why it matters beyond presentation: **the shipped deliverable is a top-5 hit
list.** [[TASK-0283]] established P@5 = 0.000 on all three mandatory targets
under the deployed operator. AUC 0.61 is not that product's metric, and the
register's headline quietly moved to the metric on which the arms look
positive.

### The mechanism, found 2026-09-01 — the register has TWO incompatible "AUC"s

This is not only a top-of-ranking vs whole-ranking difference. The two tasks
use **different AUC functions, and one of them discards direction**:

- `task0254...cv_auc` (the frozen-set definition, used by [[TASK-0263]],
  [[TASK-0275]], [[TASK-0277]] and every Shapley task) fits **OLS per fold**
  and scores the out-of-fold *prediction*. When a feature is anti-correlated
  with the label, the fitted coefficient goes negative and the ranking is
  silently flipped.
- `task0308_attribution_scaling.py` calls `sklearn.roc_auc_score` on the **raw
  score**, which is directional.

Demonstrated (`cv_auc` on a synthetic feature built to be anti-correlated with
the label):

```
raw directional AUC(x, y) : 0.2373    <- strongly anti-correlated
cv_auc(x, y)              : 0.7581    <- OLS silently flips the sign
```

**Consequence: every solo `cv_auc` in this register measures |discriminative
power|, not "ranks pockets high."** "CTQW solo = 0.575" does **not** state that
CTQW ranks pocket residues above non-pocket ones — only that a fitted linear
function of it separates them slightly. [[TASK-0305]]'s "anti-correlated"
finding and [[TASK-0263]]'s 0.575 are therefore not in contradiction at all;
they are different questions, and the register has been reading the second as
if it answered the first.

- [x] Audited every solo-feature `cv_auc` named in this task's own filing
      (`task0277`'s 8-feature battery) plus the two headline single-column
      figures in the brief's "Holds" card (CTQW, `V_C` alone), all frozen
      20, identical arrays to the published numbers. **Correction to this
      task's own filing**: `prs_low` (0.459) is checked, not anti-correlated
      — its raw AUC (0.541) is actually *higher* than its `cv_auc`, the
      opposite of the suspected mechanism. `degree` (raw 0.479) and
      `frustration` (raw 0.414, not named in the filing) genuinely are.
      **The bigger find**: `V_C` alone's own headline 0.6365 ("beats the
      whole walk by itself") drops to **0.5506 raw** — barely above
      chance — because it is strongly anti-correlated with the label on
      5/20 targets (`MKK7_IBRUTINIB` raw=0.018), which `cv_auc`'s per-fold
      sign-fitting silently flips into apparent positive contribution.
- [x] Named the two functions differently: `allostery.metrics.
      auc_directional` (additive alias for the existing signed `auc`) and
      `task0254.cv_auc_fitted` (additive alias for `cv_auc`), both zero
      call-site breakage, plus docstring cross-references on each.

### Scope A

- [x] Wrote the reconciliation into `CTQW_CONTRIBUTION_BRIEF_V2.html`
      itself (a new "Reconciliation" card, append-only per this
      register's own convention, not a rewrite of existing prose) adjacent
      to the AUC attribution table: what AUC measures vs P@5, why a
      mid-ranked label separates them, [[TASK-0305]]'s own mechanism named
      as the reconciling fact.
- [x] [[TASK-0283]]'s P@5 = 0.000 (all 3 mandatory targets) stated in that
      same new card, next to the +22.9%/+18.4% attribution figures.
- [x] Decided and recorded: **P@5 is the submission's headline metric**,
      stated with reason (it is what §5's deliverable is actually scored
      on) in the same card. AUC figures kept, labelled as answering a
      different (whole-ranking) question.

## Part B — no family-wise error control across the register

Bonferroni is applied *within* [[TASK-0284]], [[TASK-0287]] and [[TASK-0288]] —
correctly, and to their credit. **Nothing spans tasks.** From [[TASK-0261]]
onward the cluster-permutation test is the register's standard instrument and
has been run many dozens of times at α = 0.05.

Every claim still standing sits in exactly the band where that matters:

| claim | p |
|---|---|
| [[TASK-0263]] terms-block vs CTQW | **0.019** |
| [[TASK-0275]] holo `V_C`+CTQW vs `V_C` alone | **0.037** |
| [[TASK-0261]] ENM valid-vs-invalid, two-sided, exploratory | **0.042** |

**No survivor is below 0.019.** That is the signature of a family of tests with
no multiplicity accounting, not of a robust effect.

### Scope B

- [x] Counted (not estimated): `wilcoxon(`/`mannwhitneyu(`/
      `cluster_sign_flip_test(`/`cluster_permutation_two_group(`/
      `cluster_permutation_correlation(` call sites, excluding defs/imports/
      comments, across every `task02NN_*.py`/`task03NN_*.py` in
      TASK-0259–TASK-0311: **59 call sites, 21 files**
      (`scripts/task0314_multiplicity_audit.py`, reproducible). Disclosed as
      a floor — binomial/Shapiro/BIC/LRT tests elsewhere are not counted.
- [x] Split the 3 claims this task's own filing named "still standing":
      [[TASK-0275]] (p=0.037) pre-registered; [[TASK-0261]] (p=0.042)
      exploratory by its **own filing's own words**; [[TASK-0263]]'s
      original p=0.019 is **stale** — [[TASK-0315]] (filed and completed
      the same day, after this task) independently reproduced it at
      p=0.049, same conclusion, closer margin — used the current value,
      flagged the discrepancy rather than citing the outdated one.
- [x] Applied Bonferroni at two family sizes: the narrowest defensible one
      (the 2 pre-registered survivors against each other, n=2, bar=0.025)
      and the full counted family (n=59, bar=0.00085). **Neither
      pre-registered survivor clears either bar** — the answer is "none
      survive at α=0.05 family-wise," exactly as expected, and it does not
      depend on the exact pre-registered/exploratory split being right.
- [x] Rule added to `.ai/COMMON.md`'s "Current Rules" (before "Open
      Questions"): a p-value quoted outside its own task must state
      pre-registered-or-exploratory and its test family.

## Constraints

- Part B is bookkeeping over work already done — **no re-running of any
  analysis**, and no re-interpretation of any individual task's own conclusion.
  Each task's finding stands as written; what changes is what may be claimed
  when several are quoted together.
- Part A must not be resolved by dropping the unfavourable table.

## Note

Part B does not overturn anything on its own. Its value is that it stops the
register quoting three independent-looking p ≈ 0.02–0.04 results as
converging evidence, when they are the survivors of a large unrecorded family.

## Done (2026-09-01, Implementer A)

**Part A's headline finding went beyond what the filing predicted.** The
filing's own synthetic demo showed `cv_auc` can flip a strongly
anti-correlated feature's apparent sign; auditing the brief's own two
single-column headline figures against `auc_directional` found a real
instance in the register's own most-cited result: `V_C` alone's
0.6365 ("beats the whole walk by itself") is 0.5506 raw, and the gap is
explained concretely — 5/20 targets where `V_C` is strongly
anti-correlated (not just weak) with the pocket label, silently
sign-flipped by the fitted metric. CTQW's own 0.575, by contrast,
reproduces consistently in both metrics — it was never a sign-flip
artifact, only ever a weak-but-real, correctly-signed positive.

**One prediction in the filing did not hold, checked rather than
assumed**: `prs_low` (named alongside `degree`/`SASA` as an "obvious
candidate" for anti-correlation) is not anti-correlated — its raw AUC
(0.541) exceeds its `cv_auc` (0.459). `degree` and `frustration`
(the latter not named in the filing) are the two that genuinely are.
Reported this correction explicitly rather than silently matching the
filing's own prediction.

**Edited the brief directly, per Scope A's own instruction — append-only,
matching [[TASK-0315]]'s already-established convention for this exact
document**: a new "Reconciliation" card in the attribution section (AUC
vs P@5, [[TASK-0283]]'s P@5=0.000 stated beside the attribution figures,
P@5 declared the submission's headline metric with reason) and a new
paragraph on the existing `V_C` "Corrected" card (the raw-AUC/sign-
instability finding). HTML div-balance checked after editing (39/39).

**Part B's answer matched the filing's own prediction exactly**: 59
counted call sites (a disclosed floor, not the true full family), and
neither pre-registered survivor (0.037, 0.049-corrected-from-0.019)
clears Bonferroni even at the narrowest possible 2-test family (bar
0.025), let alone the full 59. Found and disclosed, not silently
inherited: the task's own cited p=0.019 for the TASK-0263 comparison is
now stale, superseded by [[TASK-0315]]'s independent same-day
recomputation (p=0.049) — used the current number, flagged why it moved.

**Not done**: a full pre-registered/exploratory classification of all 59
call sites individually (the robustness check — both family sizes give
the same "none survive" verdict — makes this unnecessary for the
question actually asked, and Part B's own Constraint is bookkeeping, not
a new audit of each call site's own original intent).

**`backend`/`__WORK_IN_PROGRESS__` test suites**: no regressions (both
code changes are additive aliases only; `pytest tests/test_analysis.py
-k "metric or auc"` and a full `pytest tests/` run both green).

**Scripts**: `scripts/task0314_auc_metric_audit.py` (Part A),
`scripts/task0314_multiplicity_audit.py` (Part B). **Data**:
`results/tasks/0314_auc_metric_audit/{auc_metric_audit,
multiplicity_audit}.json`. **Code**: `src/allostery/metrics.py`
(`auc_directional` alias), `scripts/task0254_fpocket_variance_and_
crypticity.py` (`cv_auc_fitted` alias + docstring). **Docs**:
`documentation/CTQW_CONTRIBUTION_BRIEF_V2.html` (2 new cards/paragraphs),
`.ai/COMMON.md` (new rule).

**Moved TODO/IN_PROGRESS -> DONE.**
