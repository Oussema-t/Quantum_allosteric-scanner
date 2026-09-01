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
