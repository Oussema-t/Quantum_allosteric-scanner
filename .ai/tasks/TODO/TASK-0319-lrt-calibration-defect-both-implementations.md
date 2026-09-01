# TASK-0319 — The 1-vs-2 Gaussian LRT is miscalibrated in BOTH implementations, in opposite directions

- Status: TODO
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
