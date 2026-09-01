# TASK-0313 — Verify the Silverman multimodality implementation before its result ships

- Status: TODO
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

- [ ] Review `/tmp/silverman.py`'s logic (reproduced in the task history)
      — specifically the `bw_method` scaling and the binary-search bounds
      in `hcrit`.
- [ ] **Validate against known cases before trusting any real result:**
      a clean unimodal Gaussian, a well-separated bimodal mixture, and a
      point-mass-plus-continuum sample at n = 26, 112 and 171. The test
      must return unimodal, multimodal and multimodal respectively.
- [ ] Re-run on all four cohorts including pooled, and report whether the
      conclusion survives.
- [ ] If it does not, [[TASK-0309]]'s continuum claim rests on the
      k-means instability alone, which is weaker — flag that explicitly
      rather than letting the stronger wording stand.

## Constraint

Do not repair the implementation and re-run in one step. **Validate the
fixed version on the synthetic controls first**, then run the real data.
[[TASK-0309]]'s own LRT was compromised precisely because its controls
were not checked: on our cohort its positive control returned p = 1.0
(failing to detect real bimodality) and on ASBench and pooled its
negative control fired at p = 0.012 on a true single Gaussian.
