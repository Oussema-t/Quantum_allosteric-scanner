# TASK-0313 — Verify the Silverman multimodality implementation before its result ships

- Status: Done
- Priority: **High — it underpins [[TASK-0309]]'s continuum conclusion, which is headed for the submission, and its author does not trust one detail of it**
- Filed: 2026-09-01 by Reviewer thread (self-flagged)
- Related: [[TASK-0309]], [[TASK-0288]]

## Why

The Silverman critical-bandwidth test run on 2026-09-01 reported every
cohort as consistent with unimodal, which is the basis for saying the
site-distance distribution is a **continuum** rather than k clusters.
That conclusion agrees independently with the k-means best-k instability
(3 / 4 / 2 / 5 across cohorts), so it is probably right.

**But one detail does not look right.** `h_crit` came out *identical*
for the full distribution and the spike-excluded remainder within each
cohort:

| cohort | full | excluding < 1.5 Å |
|---|---|---|
| ours | 2.206 | 2.206 |
| ASBench | 3.865 | 3.864 |
| CASBench | 11.939 | 11.939 |

Removing 8 of 26 points (ours) should not leave the critical bandwidth
unchanged to three decimals. Suspected cause: the bandwidth is passed as
`bw_method = h / x.std(ddof=1)`, so `h_crit` may be tracking the sample
standard deviation rather than the density's actual mode structure.

The pooled arm also never completed.

## Scope

- [x] Reviewed `/tmp/silverman.py`'s logic in full, reproduced verbatim
      (not re-derived) in `scripts/task0313_verify_silverman.py`. The
      suspected `bw_method` scaling bug is **refuted algebraically and
      empirically**: `covariance = x.var(ddof=1) * (h/x.std(ddof=1))**2
      == h**2` exactly, independent of `x`. `hcrit`'s binary search
      traced step-by-step on real data and confirmed correct/monotonic.
- [x] **Validated against the three known cases.** Unimodal Gaussian
      (n=26) and well-separated bimodal mixture (n=112): **PASS**.
      Point-mass-plus-continuum (n=171, extreme/unambiguous construction):
      **FAILS** — p=0.38–0.43, stable across B=200/400/800 and re-seeding.
      Root-caused, not just observed: Silverman's own smoothed-bootstrap
      null reference resamples from the same data whose spike is under
      test, so it inherits the spike and cannot flag it as surprising —
      a documented limitation of the classical (1981) calibration for
      point-mass alternatives, not a fixable implementation defect.
- [x] Re-ran on all four cohorts **including pooled** (the arm that never
      completed before). 3/4 (ours, ASBench, CASBench) read "consistent
      with unimodal" — now known to mean "underpowered," not "confirmed."
      **Pooled is MULTIMODAL, both full (p=0.020) and excluding the
      sub-1.5 Å spike (p=0.005)** — a genuine result (power limitations
      only produce false negatives, not false positives) that was not
      available before this task, since the pooled arm never finished.
- [x] The conclusion does not survive as "Silverman confirms the
      continuum" — flagged explicitly, per this Scope item, plus a
      stronger correction: the completed pooled run actively points
      away from a clean continuum, not merely "weaker support."
      [[TASK-0309]]'s continuum claim still stands, but on its own
      independent GMM-BIC and spike/binomial evidence (unaffected by
      this test's blind spot) plus the k-means instability — not on
      Silverman, which should not be cited alongside it.

## Constraint

Do not repair the implementation and re-run in one step. **Validate the
fixed version on the synthetic controls first**, then run the real data.
[[TASK-0309]]'s own LRT was compromised precisely because its controls
were not checked: on our cohort its positive control returned p = 1.0
(failing to detect real bimodality) and on ASBench and pooled its
negative control fired at p = 0.012 on a true single Gaussian.

**Honored, with a finding this task's own framing didn't anticipate**:
there was nothing to repair (no code bug existed) — the implementation
itself is correct. What failed validation is the TEST DESIGN's power
against one specific alternative. Real data was still only run after the
full validation battery (controls + robustness checks) completed, per
this Constraint's own ordering.

## Done (2026-09-01, Implementer A)

**The suspected bug does not exist.** Traced `bw_method = h/x.std(ddof=1)`
through `gaussian_kde`'s own covariance formula and confirmed directly
(two samples 50× apart in scale, same `h`, identical resulting
covariance=9.0000): the construction makes the KDE bandwidth exactly `h`,
in absolute units, by design — the standard idiom for forcing an absolute
bandwidth onto `gaussian_kde`, not a std-tracking defect. `hcrit`'s binary
search was independently traced and converges correctly.

**Root-caused the real limitation, not just documented the symptom**:
the point-mass-plus-continuum synthetic control fails validation (p=0.38,
should reject at p<0.05) because Silverman's smoothed-bootstrap null
reference resamples with replacement from the SAME data whose spike is
under test — most bootstrap replicates reconstitute a similar spike, so
the same smoothing needed to erase the real one also erases theirs, and
the null distribution of bootstrap `h_crit` centers near the observed
value regardless of true separation. Confirmed this is stable (not
sampling noise in my own check) across B=200/400/800 and independent
re-seeding, and even under an extreme, near-delta (std=0.01) spike.

**Completed the never-finished pooled arm — and it changes the
evidentiary picture, not just the methodology critique**: pooled (n=171)
is MULTIMODAL both full (p=0.020) and excluding the sub-1.5 Å spike
(p=0.005, n=125). Since the demonstrated power gap only produces false
negatives (failing to flag real multimodality), a positive result here is
not undermined by it — if anything it is notable that multimodality
survives spike-exclusion in the pooled set, suggesting real structure
beyond a single point-mass-plus-continuum. Not chased further (out of
this task's own scope: verify and report, not build a new test), flagged
as a natural follow-up for whoever picks up the pooled-cohort question
next.

**Net effect on [[TASK-0309]]**: does not gain support from the Silverman
follow-up as the filing hoped it might, and the completed pooled result
argues mildly against a clean-continuum reading rather than for one. The
continuum conclusion is unaffected in its OWN right (GMM-BIC and
spike/binomial evidence are methodologically independent of Silverman's
blind spot) but should be reported without citing Silverman as
corroboration — flagged for [[TASK-0184]]/the collaborator brief, not
edited here.

**Script**: `scripts/task0313_verify_silverman.py`. **Data**:
`results/tasks/0313_verify_silverman/silverman_verification.json`.

**Moved TODO/IN_PROGRESS -> DONE.**

---

## Addendum (2026-09-01, Reviewer thread) — the verification was right and did not go far enough; and the one significant result is a cohort artifact

> ### Self-correction, same day, BEFORE this addendum was ever committed
>
> Two of this addendum's own claims are wrong or overstated. They are left in
> place below (append-don't-silently-edit) and corrected here.
>
> **(1) The "1.88 SD" figure is in the wrong units, and I propagated it.**
> [[TASK-0288]]'s `task0288_...py:123` computes
> `sep = (srt[22:].mean() - srt[:22].mean()) / lo.std()` — the **overall
> sample SD**. Every power curve in this register (mine below, and
> [[TASK-0316]]'s) is parameterised as unit-variance components separated by
> *k* — **component SD**. Same GMM, same `ours` cohort, recomputed directly:
>
> ```
> separation, overall-sample SD : 1.84   <- TASK-0288's "1.88"
> separation, component SD      : 4.10   <- TASK-0316's "4.24"
> ```
>
> Reading a sample-SD observation against a component-SD power curve is what
> made the data look underpowered. **[[TASK-0288]] Finding B made this error
> first; I repeated it here, and it propagated into [[HYP-P14]],
> `COMMON.md`'s TASK-0311 row, and [[TASK-0316]]'s own filing.**
>
> **(2) "Zero power" is therefore too strong.** At the correct 4.10
> component-SD, the table below gives Silverman **~40% power at n=26 and
> ~100% at n=112** — low, not absent. The consequence is *sharper*, not
> softer: at `asbench` n=112 Silverman is **adequately powered and returns
> unimodal (p=0.139)**, so it now genuinely **disagrees** with
> [[TASK-0316]]'s LRT rather than being dismissable on power.
>
> **(3) And the test that disagrees with it is miscalibrated.** Measured
> after [[TASK-0316]] landed, on strictly unimodal `N(0,1)` data, nominal
> α=0.05, 25 reps:
>
> ```
> task0309.lrt  (imported by TASK-0316)   n=26: 68% FP    n=100: 52% FP
> task0288.lrt  (original)                n=26:  0% FP    n=100:  0% FP
> ```
>
> [[TASK-0288]]'s original draws **two independent samples** for the null —
> one for the k=2 fit, another for the k=1 fit (`task0288_...py:90-91`) —
> which is not a likelihood ratio and makes it over-conservative.
> [[TASK-0309]]'s generalisation fixed that and is anti-conservative instead.
> **Both are miscalibrated, in opposite directions, and each produced one of
> the register's two contradictory modality verdicts.**
>
> **This was already on record and was overlooked.** *This task's own
> Constraint section* (lines 70–73, committed in `936d9e7`) states it
> plainly: *"[[TASK-0309]]'s own LRT was compromised precisely because its
> controls were not checked: on our cohort its positive control returned
> p = 1.0 (failing to detect real bimodality) and on ASBench and pooled its
> **negative control fired at p = 0.012 on a true single Gaussian**."*
> [[TASK-0316]] imported that exact `lrt` from
> `task0309_kmeans_extended_cohort.py` and ran no negative control of its
> own. The measurement above is therefore an independent **confirmation** of
> a known defect, not a new discovery — which makes the process failure the
> more important finding: the defect was documented in the very task
> [[TASK-0316]] cites as its motivation.
>
> **Net, superseding this addendum's own closing "Next" list: modality is
> still undetermined, and [[TASK-0316]]'s "multimodal in every cohort" does
> not settle it either.** Tracked for a null-calibrated re-run. The parts of
> this addendum that stand unchanged: the implementation is correct (the
> `bw_method` bug is genuinely refuted), Silverman's power *is* poor at small
> n, and the pooled arm's significance is confounded by cohort
> (Kruskal-Wallis p=2.15e-03).

Reviewed by re-running this task's own script and adding two checks it did
not make. **Both of this task's own conclusions stand** (implementation
correct; low power for the point-mass alternative). Two things it missed:

### 1. The bimodal positive control is far too easy, so "2/3 PASS" overstates the validation

`build_controls`'s `bimodal` arm is `N(5,1)` vs `N(25,1)` — a **20 SD**
separation. [[TASK-0288]] Finding B measured that the real distribution sits
at **1.88 SD**. A control 10× beyond the alternative of interest cannot
calibrate the test.

Power measured directly — equal-weight 2-Gaussian mixtures, detection rate at
α=0.05, 5 reps, B=99, this task's own `silverman()`:

| n | 1.5 SD | 2.0 SD | 3.0 SD | 4.0 SD | 6.0 SD |
|---|---|---|---|---|---|
| 26 | 0% | 0% | 0% | 40% | 100% |
| 112 | 0% | 0% | 0% | 100% | 100% |
| 171 | 0% | 0% | **60%** | 100% | 100% |

**Zero power below 3 SD at every cohort size this register has.** The failure
is therefore not specific to the point-mass alternative as this task
concluded — the test is blind to the *ordinary* two-Gaussian alternative too,
at the separation the data actually exhibits.

**Consequence, stronger than this task's own:** every "consistent with
unimodal" verdict in [[TASK-0309]] and in [[HYP-P14]] is **uninformative, not
negative** — a null produced by absent power. This is precisely the error
[[TASK-0288]] Finding B correctly avoided for the bootstrap LRT ("p=0.137
must not be reported as evidence against two populations"); the Silverman
follow-up reintroduced it.

### 2. The pooled arm IS significant — and it is very likely a cohort-mixture artifact

This task's Part 3 completed the pooled arm for the first time:

```
pooled  full              171   h_crit=10.447  p=0.020  MULTIMODAL
pooled  excluding <1.5 A  125   h_crit=10.447  p=0.005  MULTIMODAL
```

**That contradicts [[HYP-P14]]'s "no support for any k > 1 in any cohort".**
Before treating it as evidence for two populations: the three pooled cohorts
have significantly different locations.

| cohort | n | median min_A | mean | std |
|---|---|---|---|---|
| ours | 26 | 2.95 | 5.72 | 5.55 |
| asbench | 112 | **9.03** | 10.38 | 8.34 |
| casbench | 33 | 2.97 | 8.47 | 14.35 |

Kruskal-Wallis across cohorts **H=12.28, p=2.15e-03**; `ours` vs `asbench`
p=0.013, `asbench` vs `casbench` p=0.004. **Pooling three distributions with
significantly different locations is a standard way to manufacture
multimodality.** The pooled p=0.020 should not be read as a biological
finding until the cohort mixture is ruled out — the cohorts also use
different label-scoping conventions ([[TASK-0311]]'s own disclosure: single
functional chain vs whole ASU).

### Net effect on [[HYP-P14]]

Its counter-evidence bullet — *"no support for any k > 1 in any cohort... so
stratified two-rule designs are dead and classification may be the wrong
shape entirely"* — **is not supported by the Silverman evidence.** Neither
direction is established: the unimodal verdicts have no power behind them,
and the one multimodal verdict is confounded by cohort.

**What is unaffected:** [[TASK-0300]]'s *direct* measurement that the
category does not determine the winning rule (`HCV_NS5B_VRX` and
`HCV_NS5B_POO` both "intermediate", scoring 1.000 and 0.000 under the same
rule; category-stratified oracle 0.1899 vs per-target oracle 0.3307). That
finding is independent of any modality test and still closes the specific
"stratify by distance category" design.

### Next

- [ ] Re-run the modality question with a test that has power at ~2 SD — the
      bootstrap LRT [[TASK-0288]] already calibrated, or a dip test — on each
      cohort separately, never pooled.
- [ ] If the pooled arm is kept, condition on cohort (or fit within-cohort
      and combine) before any k>1 claim.
- [ ] Correct [[HYP-P14]]'s counter-evidence bullet.
