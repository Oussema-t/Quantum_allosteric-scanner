# TASK-0310 — Re-score the whole observable family residualised on proximity

- Status: Done
- Assignee: Implementer D
- Priority: **Critical — the register's nine quantum observables were all scored raw, before we knew proximity was the dominant confound. None has ever been residualised.**
- Filed: 2026-09-01 by Reviewer thread
- Related: [[TASK-0140]], [[TASK-0141]], [[TASK-0142]], [[TASK-0145]], [[TASK-0146]], [[TASK-0147]], [[TASK-0148]], [[TASK-0157]], [[TASK-0308]], [[TASK-0309]]

## Why now

[[TASK-0308]] established two things that were not known when the
observable family was built:

1. **Proximity to the active site is the strongest single predictor**
   (AUC 0.6147 on 108 ASBench structures) — the best arm we have.
2. **CTQW occupation is ~80% proximity.** Within-structure
   ρ(occupation, proximity) = **+0.735**; residualised, occupation drops
   from AUC 0.5921 to **0.5184**, no longer significant (p = 0.29).

Every observable in `TASK-0140`–`0157` was scored as **raw AUC against a
floor**. None was conditioned on distance. That was reasonable in 2026 —
the confound had not been identified — but it means **the family was
evaluated on the wrong statistic**, and an observable could have been
discarded for a low raw AUC while carrying more *independent* signal than
the one we kept.

## The lead candidate, and why this is not a fishing expedition

[[TASK-0140]]'s own results table already contains the decisive column,
unremarked at the time:

| observable | mean AUC (7 targets) | mean ρ(observable, −distance) |
|---|---|---|
| CTQW occupation | 0.596 | **−0.636** |
| **chiral circulation** | 0.572 | **−0.325** |

**Chiral circulation carries 49% less distance contamination at
essentially the same raw AUC.** [[TASK-0140]]'s −0.636 for occupation
independently reproduces [[TASK-0308]]'s +0.735 on a different cohort
three months later, which is a good sign the ρ column is measuring what
it appears to.

Projecting the shrinkage by ρ² (the variance the confound explains):

| observable | ρ² | raw excess | projected surviving |
|---|---|---|---|
| occupation | 0.405 | +0.096 | ~+0.057 |
| **circulation** | **0.105** | +0.072 | **~+0.064** |

**Circulation would retain more independent signal than occupation despite
the lower raw AUC.**

> ### Amendment, 2026-09-01, Reviewer thread — the projection above is wrong; the task is not
>
> The line "that is a specific, falsifiable prior — not a hope" was mine, and
> the projection it referred to **fails its only calibration check.** The law
> used is `projected = raw_excess × (1 − ρ²)`. Tested against the one case
> where the residualised answer is already known ([[TASK-0308]], CTQW):
>
> ```
> law:       0.0921 × (1 − 0.735²) = 0.0423  → AUC 0.5423
> measured:                           0.0184  → AUC 0.5184
> overprediction:                      2.30×
> surviving fraction:  law 0.460   vs   empirical 0.200
> ```
>
> Three separate problems:
> 1. **Uncalibrated and falsified.** It overpredicts surviving signal by 2.3×
>    on the only case with ground truth, always in the flattering direction.
> 2. **`(1 − ρ²)` is not the shrinkage law.** The partial correlation is
>    `ρ(X,y|Z) = (ρ_Xy − ρ_Xz ρ_Zy) / sqrt((1 − ρ_Xz²)(1 − ρ_Zy²))` — the
>    denominator **inflates**. `(1 − ρ²)` is neither that nor the residualised
>    AUC.
> 3. **The two rows come from different cohorts.** Occupation's ρ = −0.636 is
>    [[TASK-0140]]'s 7 targets; the residualised result it is being calibrated
>    against is [[TASK-0308]]'s 108 ASBench structures, where the same
>    quantity measured +0.735. Circulation has no ASBench measurement at all.
>
> **What survives:** circulation's ρ is genuinely about half occupation's on
> the same cohort under the same measurement ([[TASK-0140]]'s own table). That
> is a real reason to run it first. It is **not** a quantitative prediction
> that circulation retains more signal, and the ρ² table must not be quoted as
> one.
>
> **Added to Scope:** compute the residualised AUC directly for every
> observable. Do not project it. If a projection is wanted for triage, fit the
> shrinkage empirically on the observables whose residual is measured, and
> report it as a fitted heuristic with its residuals, never as a prior.

[[TASK-0140]] **failed its own gate** (0/7 targets cleared the floor with
non-overlapping CIs and a Bonferroni-significant null) and was closed.
**The residualised test it needed was never run.**

## Scope

- [x] Enumerate the observable family and confirm which are still
      runnable: chiral circulation ([[TASK-0140]],
      `src/allostery/chiral.py`, `scripts/chiral_circulation_real_run.py`),
      engineered dephasing ([[TASK-0141]]), Hodge L1 / persistent H2
      ([[TASK-0142]]), quantum transport effective conductance
      ([[TASK-0145]]), frequency-domain coherence ([[TASK-0146]]),
      vibronic resonance ([[TASK-0147]]), single-particle entanglement
      entropy ([[TASK-0148]]), low-mode PRS/DCC ([[TASK-0149]]),
      two-boson HOM interference ([[TASK-0157]]).
- [x] Score each on the **ASBench cohort** (`task0308_attribution_scaling.py`
      is the template — annotated seed and truth, 108 structures, terminal
      exclusion, per-structure AUC).
- [x] For each, report **three** numbers: raw AUC, within-structure
      ρ against proximity, and **AUC after rank-residualising on
      proximity**, exactly as `ctqw_proximity_partial` does.
- [x] Rank the family by **residual**, not raw. Report the full table
      including the ones that get worse.
- [x] Bonferroni across the family, and cluster-robust by protein.

## Constraints

- **Chiral first.** It has the strongest prior and existing code. If it
  fails residualised, say so before running the other eight — a negative
  on the best candidate is more informative than eight ambiguous ones.
- **Do not re-tune any observable.** These are re-scorings of existing
  implementations under a corrected statistic, not a new sweep. Changing
  an observable's parameters and its scoring metric in the same run makes
  the result uninterpretable.
- **Positive control required** ([[TASK-0305]]'s lesson): include
  proximity itself, and confirm it scores ~0.61 raw and ~0.5 residualised
  on itself. A harness that cannot reproduce that is broken.
- Report the number that moves against us.

## Why this is the register's best remaining shot

Proximity is a ceiling everything else has collapsed into: fpocket
druggability was mostly pocket size ([[TASK-0287]]), the 61-rule family
was one signal at 61 settings ([[TASK-0301]]), CTQW occupation is
geometry from its own seeding ([[TASK-0308]]). **An observable that is
genuinely orthogonal to distance is the only thing that can add
anything** — and chiral circulation is the one measurement in this
register that already looks like it might be.

It is also the only route that would give the quantum arm something
structurally unavailable classically: `H_new` is real symmetric, so
`U_ij = U_ji` exactly and directional transport is impossible by
construction. Complex hoppings break that.

## Done (2026-09-01, Implementer D)

**Per the same-day Amendment above (compute directly, do not project):
every number below is a direct measurement**, never the falsified
`(1-ρ²)` shrinkage law — the amendment landed while this task's own
computation was already underway and is fully consistent with the method
already chosen; no rework needed.

**Runnable check (Scope item 1), done before scoring anything**: of the
9 named observables, 2 were never implemented past a literature proposal
— checked directly against their own Done sections, not assumed.
[[TASK-0147]] (vibronic resonance): "does not build the structured-bath
master equation, synthetic falsifier, or real-target scoring... No
synthetic falsification gate and no real-target scoring were run."
[[TASK-0157]] (two-boson HOM): "no k=2 symmetrized Hilbert space, no
synthetic falsifier... no code touched." Both excluded — building either
now would be a new observable, against this task's own Constraint
("re-scorings of existing implementations... not a new sweep"). **7
runnable**: chiral circulation, dephasing, persistent H2 void, transport,
spectral coherence, entanglement entropy, low-mode PRS/DCC (2 outputs).

**Harness validated before trusting it on anything new** (this task's
own positive-control Constraint): re-derived CTQW's own numbers from
scratch on the full 108-structure cohort and reproduced
[[TASK-0308]]'s committed `ctqw_proximity_partial.json` exactly — raw
0.5921, ρ 0.7347, residualised 0.5184, all to 4 decimal places (that
JSON's own generating script did not survive, so this is a from-scratch
reconstruction, not a re-run of existing code, and this exact match is
the evidence it is faithful). Proximity scored against itself: raw
0.6147 (also exact), residualised **0.5000 exactly**, as required.

**Chiral circulation, reported first and prominently, per this task's
own Constraint**: raw AUC 0.5560 (+11.2% share), **residualised AUC
0.4960 (-0.8% share) — DOES NOT survive residualisation.** Its ρ against
proximity (0.3646) is indeed roughly half CTQW's (0.7347), confirming
the one thing the Amendment left standing ("circulation's ρ is genuinely
about half occupation's... a real reason to run it first") — but lower
contamination did not translate into surviving signal. Essentially all
of chiral's raw AUC was proximity, same conclusion as CTQW, on a
candidate that entered this task with the strongest prior of the nine.

**Full family, all 7 runnable observables scored, ranked by residualised
share (not raw), including the ones that get worse**:

| observable | raw AUC | ρ(proximity) | residual AUC | residual share | Bonferroni p | cluster-p (protein, n=76) |
|---|---|---|---|---|---|---|
| persistent_h2_void | 0.5927 | 0.4894 | 0.5598 | **+12.0%** | 0.856 | 0.101 |
| spectral_coherence | 0.6016 | 0.7004 | 0.5226 | +4.5% | 1.0 | 0.239 |
| transport | 0.5803 | 0.3864 | 0.5200 | +4.0% | 1.0 | 0.330 |
| chiral_circulation | 0.5560 | 0.3646 | 0.4960 | -0.8% | 1.0 | 0.799 |
| entanglement_entropy | 0.5934 | 0.8946 | 0.4903 | -1.9% | 1.0 | 0.623 |
| prs_low | 0.4532 | -0.1847 | 0.4680 | -6.4% | 1.0 | 0.185 |
| dcc_low | 0.4783 | 0.2887 | 0.4445 | **-11.1%** | 0.188 | 0.036 |

**Nothing survives.** The best candidate (persistent H2 void) is +12.0%
but not significant either way (Wilcoxon p=0.107 uncorrected, p=0.856
after Bonferroni across the 8 tests run, cluster-robust p=0.101 by
protein) — and carries real missing data: `void_score` legitimately
detects no H2 class on 63/108 structures (its own documented "no void
detected" honest zero, not a bug; n=45/108 usable). `dcc_low` is the
only nominally significant cell (uncorrected p=0.0235) and it is
**negative** — low-mode dynamic cross-correlation becomes
*anti*-predictive once proximity is removed — and even that does not
survive Bonferroni (p=0.188) or hold up cluster-robust (p=0.036, itself
not below a corrected bar, and via Monte Carlo not exact enumeration at
76 mostly-singleton clusters).

**Dephasing, time-boxed per this task's own docstring reasoning**
(N<=300 only, 11/108 structures — the documented ~N^2.75 cost of
`haken_strobl_time_averaged` makes the full cohort infeasible in-session,
same treatment [[TASK-0256]] gave this identical function): raw AUC
**0.4306** (below chance), residualised 0.4441 — not promising, n too
small to weight heavily, not chased further.

**Cluster-robust by protein**: [[TASK-0261]]'s own `cluster_sign_flip_
test` is hardcoded to its own 13-cluster/20-target `CM` and silently
returns an empty test on any ASBench PDB — not reusable as-is.
Generalised locally (`cluster_sign_flip_test_generic`, same
sum-of-cluster-sums sign-flip algorithm, parameterised cluster map,
exact enumeration up to 20 clusters else 100000-draw Monte Carlo) — 108
structures cluster into 76 distinct proteins (ASBench's own `protein`
field), mostly singletons, so Monte Carlo is used throughout except the
11-row dephasing subset (7 clusters, exact).

**Answered, per this task's own "why this is the register's best
remaining shot"**: it was not. **Every one of the 7 runnable observables
in this family — including chiral circulation, which entered with the
strongest, most specific prior of the nine — loses its apparent signal
once proximity to the active site is accounted for.** None is
distinguishable from chance after Bonferroni correction; none holds up
cluster-robust by protein. Combined with [[TASK-0308]] (CTQW itself),
this is now 8 of 9 nameable observables (2 never built) tested against
the single confound this register's own central hope depended on being
absent, and none survives it. The register does not currently have an
observable that is "genuinely orthogonal to distance" — the premise this
task was filed to test.

**Script**: `scripts/task0310_family_residualised_on_proximity.py`.
Total wall time 6650s (~111 min), dominated by chiral circulation
(4787s/108 structures — the Peierls-Hamiltonian-per-field-direction
construction is the costly step, not flagged as infeasible since it
completed, but noted for anyone re-running this). **Data**:
`results/tasks/0310_family_residualised_on_proximity/family_residualised.json`
(gitignored, not committed — every number above traced to this Done
section and `RESULTS.md` directly).

**Not done, disclosed**: dephasing on the full 108 (infeasible,
time-boxed as stated); vibronic resonance and two-boson HOM (never
implemented, out of this re-scoring task's own scope to build).
