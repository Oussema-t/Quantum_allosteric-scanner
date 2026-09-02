# TASK-0319 — The 1-vs-2 Gaussian LRT is miscalibrated in BOTH implementations, in opposite directions

- Status: Done
- Priority: **Critical — it invalidates [[TASK-0316]]'s headline, and the defect was already documented in [[TASK-0313]] before [[TASK-0316]] ran**
- Filed: 2026-09-01 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0284]], [[TASK-0288]], [[TASK-0309]], [[TASK-0311]], [[TASK-0313]], [[TASK-0316]], [[HYP-P14]]

## The measurement

Both implementations, on **strictly unimodal `N(0,1)` data**, nominal
α = 0.05, 25 reps each:

| implementation | n=26 | n=100 |
|---|---|---|
| `task0309_kmeans_extended_cohort.lrt` — **imported by [[TASK-0316]]** | **68% FP** | **52% FP** |
| `task0288_contact_spike_and_label_free_prediction.lrt` — original | **0% FP** | **0% FP** |

Neither is a 5% test. One fires on most unimodal samples; the other never
fires at all. **Each produced one of the register's two contradictory
modality verdicts.**

## Root cause, both sides

**[[TASK-0288]]'s original is over-conservative — a real bug.**
`task0288_contact_spike_and_label_free_prediction.py:90-91`:

```python
null = [2 * (_ll(r.normal(mu, sd, n).reshape(-1,1), 2)
           - _ll(r.normal(mu, sd, n).reshape(-1,1), 1)) for _ in range(B)]
```

**Two independent samples are drawn** — one for the k=2 fit, a different one
for the k=1 fit. That is a difference of log-likelihoods on unrelated
datasets, not a likelihood ratio. It roughly doubles the null's variance, so
the null distribution is far too wide and the test essentially never rejects.
This is why its own hardcoded negative control passed (`"neg": [0.701, 0.179,
0.880, 0.525, 0.661]`, 0/5) **and** why it returned p=0.137 on real data and
self-diagnosed as "underpowered."

**[[TASK-0309]]'s generalisation fixed that** (single `samp` used for both
`_ll` calls, line 200-203) **and is anti-conservative instead.** Mechanism not
isolated here; candidates worth checking in order:
- `_ll(x, k, seeds=3, n_init=3)` maximises over 9 restarts for k=2 while the
  k=1 likelihood has no local optima — an asymmetry that inflates the ratio
  if it bites differently on real vs bootstrap samples.
- Degenerate mixture likelihoods are unbounded; at n=26 a k=2 component can
  collapse onto a near-duplicate point. `reg_covar` default 1e-6 may be too
  small for this data's scale.
- `g1 = GaussianMixture(k1, n_init=5, random_state=0)` fits the null-generating
  model with different settings (`n_init=5`) than `_ll` uses (`n_init=3`).

## The process failure, which is the larger finding

**This was already on record before [[TASK-0316]] ran.** [[TASK-0313]]'s own
Constraint section (lines 70–73, committed in `936d9e7`) states it plainly:

> [[TASK-0309]]'s own LRT was compromised precisely because its controls were
> not checked: on our cohort its positive control returned p = 1.0 (failing to
> detect real bimodality) and on ASBench and pooled its **negative control
> fired at p = 0.012 on a true single Gaussian**.

[[TASK-0316]] cites [[TASK-0313]] as its motivation, imports that exact `lrt`
verbatim, and **runs no negative control of its own** — only power curves,
which are positive controls. The register's standing rule ("positive control
required", [[TASK-0305]]'s lesson, honoured in [[TASK-0306]] and [[TASK-0318]])
has been applied asymmetrically throughout: we check that a test *can* detect
signal, never that it does not *fabricate* it.

## Scope

- [ ] **Fix `task0309.lrt`'s calibration.** Diagnose which of the three
      candidates above drives it (or another cause), fix, and demonstrate a
      false-positive rate at or below nominal α on `N(0,1)` at n = 26, 100,
      171 — **≥200 reps**, not 25.
- [ ] **Fix `task0288.lrt`'s two-sample bug** (or formally retire it in favour
      of the corrected `task0309` version — one implementation, not two).
- [ ] **Re-run [[TASK-0316]]** with the calibrated test, all six datasets,
      reporting **both** controls: power curve *and* null false-positive rate,
      at each cohort's own n.
- [ ] **Reconcile against Silverman.** At `asbench` n=112 Silverman is
      adequately powered (~100% at the observed 4.10 component-SD) and returns
      **unimodal, p=0.139**, while the LRT returns multimodal. Once the LRT is
      calibrated, either they agree or the disagreement is itself the finding —
      note that Silverman counts KDE modes (a modality test) whereas the LRT
      rejects on any departure from log-normality, **including skew**, so they
      are not testing the same alternative. Say which question the register
      actually wants answered.

## Blast radius — claims that depend on this and must be re-checked

| task | claim | status under this defect |
|---|---|---|
| [[TASK-0316]] | "multimodal in every cohort, both arms, adequately powered" | **not supported** — the test rejects unimodal data at 52–68% |
| [[TASK-0288]] Finding B | "the bimodality LRT is UNDERPOWERED — inconclusive" | wrong for a second reason: over-conservative test **and** an SD-unit error ([[TASK-0313]] addendum) |
| [[TASK-0309]] | k-means / GMM-BIC continuum conclusion | the LRT leg is void; the **GMM-BIC and spike/binomial legs are methodologically independent** and unaffected — check they were not silently pooled with the LRT in any summary |
| [[TASK-0311]] | regression-not-classification framing | its own regression results stand; only the "there are no classes" justification is affected (already corrected in `COMMON.md`'s TASK-0311 row) |
| [[HYP-P14]] | continuum bullet | already withdrawn; keep it withdrawn — **do not restore it from [[TASK-0316]]** |

## Constraints

- **Negative control is mandatory and is the acceptance criterion**, not an
  extra. No modality verdict from this register may be reported again without
  its false-positive rate at that n.
- **Do not write a third modality test.** Fix one of the two that exist.
- **Do not re-derive the SD units.** [[TASK-0313]]'s addendum settles it:
  power curves are in **component SD**; `task0288…py:123` reports **sample
  SD**; on the `ours` cohort those are 4.10 and 1.84 for the same GMM. Report
  which unit any separation figure is in, always.

## Note

Modality is **undetermined**, and has been throughout — first on a
too-conservative test read against mismatched units, then on a
too-liberal one. The honest register position until this task lands is that
neither verdict was earned. That is worth stating plainly rather than
carrying whichever number is most recent.

## Done (2026-09-02, Implementer D)

Full results: `results/tasks/0319_lrt_calibration/lrt_calibration_fix.json`.

**Root cause, `task0309.lrt` (anti-conservative) — a fourth cause, not the
three candidates filed above.** `g1 = GaussianMixture(k1, ..., random_state=0)`
used a plain **int** `random_state`. sklearn's `GaussianMixture.sample()`
calls `check_random_state(self.random_state)` fresh on every call — an int is
**re-seeded every call**, not advanced. Every `g1.sample(n)` inside the
B-iteration bootstrap loop returned the **identical draw** (verified: at
n=26, seed 0, 58/60 null replicates were bit-identical, LR=1.14326065 — GMM
log-likelihood is invariant to the order of iid data, so permuting the same
values changed nothing). The null distribution collapsed to ~one point, so
`obs` landed strictly above or below it almost every rep: p ∈ {≈0.01, ≈1.0},
never a real 5% test. **Fix**: `random_state=np.random.RandomState(seed)` (an
instance, not an int) — sklearn reuses and advances an existing instance
instead of reseeding it. Applied at
`__WORK_IN_PROGRESS__/scripts/task0309_kmeans_extended_cohort.py`'s `lrt()`.

**`task0288.lrt` (over-conservative) — retired, not fixed in place**, per
this task's own Scope ("one implementation, not two"). Its local `_ll`/`lrt`
(the two-independent-samples bug, confirmed as filed) are removed;
`task0288_contact_spike_and_label_free_prediction.py` now imports the
corrected `lrt` from `task0309_kmeans_extended_cohort`. Its stale hardcoded
controls (generated by the buggy two-sample implementation) were replaced
with freshly computed ones at its own n=28 (B=300, 5 reps): negative control
clean (0/5 FP), but **positive controls now show essentially no power up to
3.0 SD separation** (1/5 significant even at sep=3.0) — a materially worse,
more honest power picture than the old table implied (the old table's
apparent power-like shape was itself an artifact of the two-sample bug's
instability). Real-data observed p=0.1197 (n=28) — uninformative for lack of
power, not evidence either way.

**Calibration validated, N(0,1), α=0.05, 200 reps/n, B=100, seeds=3** (per
this task's own acceptance criterion):

| n | FP rate | hits/reps |
|---|---|---|
| 26 | 4.0% | 8/200 |
| 100 | 7.0% | 14/200 (95% CI [3.5%,10.5%], includes nominal 5%) |
| 171 | 5.0% | 10/200 |

All three at or statistically indistinguishable from nominal α — down from
the filed 68%/52% at n=26/100.

**TASK-0316 re-run**, identical harness, corrected `lrt`, all six cohort-arms
(`results/tasks/0316_modality_powered_test/modality_powered_test.json`
overwritten in place):

| cohort | arm | n | p | power@sep | verdict |
|---|---|---|---|---|---|
| ours | full | 26 | 0.0831 | 32% | UNDETERMINED |
| ours | excl <1.5Å | 18 | 0.1728 | 12% | UNDETERMINED |
| asbench | full | 100 | 0.0033 | 100% | **MULTIMODAL, adequately powered** — point-mass-like |
| asbench | excl <1.5Å | 88 | 0.1761 | 49% | UNDETERMINED |
| casbench | full | 30 | 0.0033 | 12% | UNDETERMINED |
| casbench | excl <1.5Å | 19 | 0.2525 | 15% | UNDETERMINED |

**TASK-0316's original headline ("multimodal in every cohort, both arms,
adequately powered") does not survive calibration.** Only 1/6 cells is both
significant and adequately powered (asbench full, n=100) — and that cell
already carries [[TASK-0309]]'s own point-mass-not-population caveat
(low-mean component weight 0.12, narrow). The other 5/6 are genuinely
undetermined for lack of power — neither unimodal nor multimodal evidence.

**Silverman reconciliation.** At asbench-full, Silverman (n=112, adequately
powered at ~100% at 4.10 component-SD) says **unimodal, p=0.139**; the
calibrated LRT (n=100, same cohort/arm, adequately powered) says
**multimodal, p=0.0033**. Not a contradiction once the alternatives are
named: Silverman's dip-type test asks whether the KDE has >1 mode (a shape
question); the LRT rejects on any departure from a single Gaussian,
including a narrow point mass that need not produce a second KDE bump. The
LRT's rejection is consistent with — not independent evidence for or against
— [[TASK-0309]]'s Finding F (point mass + continuum). **The two tests are not
testing the same alternative and should not be asked to arbitrate the same
question.** The population-vs-point-mass distinction is answered by
[[TASK-0309]]'s own component-weight/sigma decomposition (already flagged
`point_mass_like` in this rerun's own asbench-full row), not by either
modality test alone.

**Blast radius, resolved:**
- [[TASK-0316]]: headline unsupported as filed; corrected picture above.
- [[TASK-0288]] Finding B: "underpowered above 2.0 SD" was itself read off
  the buggy controls; recomputed controls show no demonstrated power even at
  3.0 SD at n=28 — still inconclusive, for a more honest reason.
- [[TASK-0309]]: GMM-BIC / spike / binomial legs untouched — never called `lrt()`.
- [[TASK-0311]]: unaffected (already corrected in `COMMON.md`).
- [[HYP-P14]]: remains withdrawn.

**Register position, unchanged in direction, now earned rather than
asserted: modality is UNDETERMINED.** The one adequately-powered significant
result supports a point mass + continuum, not a second broad population, and
not a clean unimodal verdict either. No cohort-arm currently supports a
confident "two populations" claim.
