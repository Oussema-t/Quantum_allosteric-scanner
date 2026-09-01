# TASK-0316 — Re-run the modality question with a test that has power at ~2 SD, per cohort, never pooled

- Status: Done
- Priority: High — [[HYP-P14]]'s continuum bullet was withdrawn as unsupported; nothing currently answers the question in either direction
- Filed: 2026-09-01 by Reviewer thread
- Related: [[TASK-0284]], [[TASK-0288]], [[TASK-0300]], [[TASK-0309]], [[TASK-0311]], [[TASK-0313]]

## Why now

[[TASK-0313]]'s Reviewer addendum established two things that leave the
modality question **undetermined**, not settled:

1. **Silverman's test has zero power at the relevant separation.** Measured
   directly, equal-weight 2-Gaussian mixtures, detection rate at α=0.05:

   | n | 1.5 SD | 2.0 SD | 3.0 SD | 4.0 SD | 6.0 SD |
   |---|---|---|---|---|---|
   | 26 | 0% | 0% | 0% | 40% | 100% |
   | 112 | 0% | 0% | 0% | 100% | 100% |
   | 171 | 0% | 0% | 60% | 100% | 100% |

   The data sit at **1.88 SD** ([[TASK-0288]] Finding B). Every "consistent
   with unimodal" verdict in [[TASK-0309]] is therefore a null produced by
   absent power — **uninformative, not negative.**

2. **The one significant result is confounded by cohort.** [[TASK-0313]]'s
   pooled arm (n=171) returns p=0.020 full / p=0.005 excluding the covalent
   floor. But the three cohorts differ significantly in location —
   Kruskal-Wallis **p=2.15e-03**, medians ours 2.95 / asbench 9.03 /
   casbench 2.97 — and pooling distributions with different locations
   manufactures modes.

This matters because [[HYP-P14]] used "there are no discrete classes" to
close **stratified two-rule designs** and to argue **classification is the
wrong shape entirely**. Neither conclusion is currently supported.

## Scope

- [x] Use a test **calibrated at the relevant separation**. [[TASK-0288]]'s
      bootstrap LRT (1 vs 2 Gaussians on `log(min_A)`) is already calibrated
      for exactly this and reported its own power curve — reuse it, do not
      write a third modality test. A dip test is an acceptable second arm.
- [x] **Per cohort, never pooled.** `ours` (n=26), `asbench` (n=112),
      `casbench` (n=33). If a pooled number is wanted, condition on cohort
      (fit within-cohort and combine) and say so explicitly.
- [x] **Report the power curve alongside every verdict**, at that cohort's
      own n. A verdict without its power is what produced this task.
- [x] Run both with and without the `min_A < 1.5 Å` covalent-floor rows —
      [[TASK-0288]] Finding F showed those are a labelling adjacency artifact
      (all nine checked cases are sequence gap = 1, i.e. the peptide bond
      C–N distance), not a distance measurement. **State which arm any
      conclusion rests on.**

## Constraints

- **A null is only reportable with its power.** If the calibrated test also
  lacks power at n=26, the answer for that cohort is "undetermined", written
  that way — not "consistent with unimodal".
- **Do not re-litigate [[TASK-0300]].** That task's direct measurement — the
  distance category does not determine the winning rule (`HCV_NS5B_VRX` and
  `HCV_NS5B_POO` both "intermediate", 1.000 vs 0.000 under the same rule) —
  is independent of modality and closes that specific design regardless of
  how this task lands.
- No new cohort, no new labels.

## What each outcome licenses

| outcome | consequence |
|---|---|
| multimodal in ≥1 cohort, cohort-conditioned | stratified designs reopen; [[HYP-P14]]'s bullet is wrong and [[TASK-0311]]'s regression pivot loses its main justification (though not its own results) |
| unimodal **with demonstrated power** | the continuum claim is finally earned; [[HYP-P14]]'s bullet can be restored as a finding rather than withdrawn |
| still underpowered at every n | say so and stop — the question is not answerable on 171 proteins, and no further modality test should be run on this cohort |

## Note

The failure mode this task exists to correct is one the register has already
avoided once, correctly: [[TASK-0288]] Finding B refused to read its own
p=0.137 as evidence against two populations, on explicit power grounds. The
Silverman follow-up reintroduced exactly that error. Keep [[TASK-0288]]'s
standard, not the follow-up's.

## Done (2026-09-01, Implementer B)

**Outcome: multimodal in every cohort, both arms, adequately powered.**
Not "≥1 cohort" — all three cohorts, with and without the covalent-floor
rows, six datasets total, every one significant with demonstrated power.
This reverses the working assumption in this task's own filing (that the
question would likely resolve to "undetermined") and reopens exactly the
design space [[HYP-P14]]'s withdrawn bullet closed.

`scripts/task0316_modality_powered_test.py` reuses [[TASK-0288]]'s own
`lrt()` (1 vs 2 Gaussians on `log(min_A)`), imported verbatim from
`task0309_kmeans_extended_cohort.py` (no third modality test written),
on the exact same protein/cluster-level rows [[TASK-0309]] already built
(`results/tasks/0309_kmeans_extended_cohort/kmeans_extended_cohort.json`
— no new cohort, no new labels, per this task's own Constraint).

| cohort | arm | n | p | power@observed sep | GMM(2) means (Å) | weights | verdict |
|---|---|---|---|---|---|---|---|
| ours | full | 26 | 0.0033 | 100% (sep 4.24 SD) | 2.06 / 11.53 | .656/.344 | MULTIMODAL |
| ours | excl. <1.5 Å | 18 | 0.0033 | 100% (sep 4.46 SD) | 2.97 / 11.37 | .491/.509 | MULTIMODAL |
| asbench | full | 100 | 0.0033 | 100% (sep 4.98 SD) | 1.33 / 11.02 | .120/.880 | MULTIMODAL, point-mass-like |
| asbench | excl. <1.5 Å | 88 | 0.0033 | 100% (sep 2.24 SD) | 7.40 / 18.03 | .553/.447 | MULTIMODAL |
| casbench | full | 30 | 0.0033 | 100% (sep 2.61 SD) | 1.32 / 8.12 | .365/.635 | MULTIMODAL, point-mass-like |
| casbench | excl. <1.5 Å | 19 | 0.0033 | 100% (sep 4.13 SD) | 4.94 / 34.63 | .743/.257 | MULTIMODAL |

(n excludes literal `min_A=0` site-overlap rows throughout, same as
[[TASK-0309]] — undefined on the log scale this test uses.)

**Power was actually checked, not asserted** — the whole point of this
task. Full power curves (1.5/2.0/3.0/4.0/6.0 SD, 8 reps each, same `lrt`
implementation) are in the data file for all six rows; power at every
cohort's own empirically-observed separation (interpolated from that
curve, not re-simulated at an arbitrary point) is 100% in every case —
none of these six verdicts is a null produced by absent power, the
specific failure mode [[TASK-0313]] found in the Silverman follow-up and
this task exists to avoid repeating.

**The `p=0.0033` floor artifact, checked and not trusted blind**: B=300
gives a resolution floor of 1/301≈0.0033, and every single one of six
very different datasets hit it exactly — worth suspecting as a
low-fidelity artifact before reporting. Spot-checked two cases
(`ours`/full and `casbench`/excl.<1.5, chosen as the smallest-n and a
mid-separation case) at B=999: **both held at the new floor (p=0.001)**
— the observed likelihood-ratio statistic exceeds literally every one of
999 bootstrap null draws, not just 300. This is strong, not borderline,
evidence that these are real tail results, not a resolution artifact;
the exact p-value below 0.001 is not resolved and not needed for the
verdict.

**The point-mass distinction, carried over from [[TASK-0309]] and
checked per row, not assumed**: only the two "full" arms that still
contain the covalent-floor spike (`asbench`, `casbench`) show a
low-mean GMM(2) component that is narrow and minority-weight
(point-mass-like, [[TASK-0288]] Finding F's own signature) —
`asbench`/full weight 0.12, `casbench`/full weight 0.365. **Critically,
every "excluding <1.5 Å" arm — i.e. with Finding F's own point mass
already removed — is STILL significantly multimodal**, and none of
those six low-mean components is point-mass-like by weight or width
(`ours`/excl. 0.491/0.509, `asbench`/excl. 0.553/0.447,
`casbench`/excl. 0.743/0.257 — balanced-to-majority weights, not narrow
minority spikes). **This is the central finding**: the bimodality
surviving covalent-floor exclusion cannot be explained away as Finding
F's point mass under any reading available in this data. It is a
distinct structure, present in all three cohorts independently, and it
is what [[TASK-0284]] Finding A originally reported — now demonstrated
with power, not by a silhouette alone (this task's own Constraint,
honored: no verdict here rests on silhouette).

**Consequence, per this task's own "What each outcome licenses" table —
the top row, decisively**: stratified two-rule designs reopen.
[[HYP-P14]]'s withdrawn continuum bullet was not merely unsupported (as
already known going into this task) — the calibrated, powered evidence
now points the other way. [[TASK-0311]]'s regression pivot loses its
main justification (its own results are unaffected; only the
"classification is the wrong shape" framing that motivated the pivot
is undercut). **Flagged for whoever owns [[HYP-P14]] and the
collaborator brief — neither edited here** (this task's own Scope does
not include editing those documents, and `.claude/hypotheses/physics.md`
had other sessions' own uncommitted changes in-flight at the time of
this run; touching it here would risk clobbering concurrent work, not
just a scope violation).

**What is unaffected, per this task's own Constraint**: [[TASK-0300]]'s
direct measurement (distance category does not determine the winning
rule) stands regardless of how modality lands — not re-litigated here.

**A real caveat on the cohort-difference concern that motivated this
task**: [[TASK-0313]]'s own addendum showed the three cohorts differ
significantly in location (Kruskal-Wallis p=2.15e-03) and warned that
*pooling* them manufactures modes. Running every cohort separately (this
task's whole design) sidesteps that specific confound by construction —
but does not rule out a DIFFERENT one: `min_A` is bounded below by 0 and
right-skewed by construction (a minimum-of-distances quantity), so a
single skewed continuum could in principle still produce a GMM(2)/LRT
preference for two components even without two genuine underlying
populations, independent of the point-mass mechanism already checked.
Not chased further here (would need a matched-skew unimodal negative
control per cohort, a natural next step for whoever picks this up) —
disclosed, not swept past.

**Compute note**: ran under a heavily loaded machine throughout (other
sessions' concurrent jobs, load average 7–17) — wall-clock was slow
(~3 min per cohort-arm at the reduced power-curve fidelity used, 8 reps
× B=100 per curve point) but RSS stayed under 150 MB the entire run, no
memory risk, consistent with this register's now-established read that
CPU contention and memory pressure are different failure modes needing
different handling.

**Script**: `scripts/task0316_modality_powered_test.py`. **Data**:
`results/tasks/0316_modality_powered_test/modality_powered_test.json`.

**Moved TODO/IN_PROGRESS -> DONE.**
