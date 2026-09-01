# TASK-0310 — Re-score the whole observable family residualised on proximity

- Status: TODO
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
the lower raw AUC.** That is a specific, falsifiable prior — not a hope.

[[TASK-0140]] **failed its own gate** (0/7 targets cleared the floor with
non-overlapping CIs and a Bonferroni-significant null) and was closed.
**The residualised test it needed was never run.**

## Scope

- [ ] Enumerate the observable family and confirm which are still
      runnable: chiral circulation ([[TASK-0140]],
      `src/allostery/chiral.py`, `scripts/chiral_circulation_real_run.py`),
      engineered dephasing ([[TASK-0141]]), Hodge L1 / persistent H2
      ([[TASK-0142]]), quantum transport effective conductance
      ([[TASK-0145]]), frequency-domain coherence ([[TASK-0146]]),
      vibronic resonance ([[TASK-0147]]), single-particle entanglement
      entropy ([[TASK-0148]]), low-mode PRS/DCC ([[TASK-0149]]),
      two-boson HOM interference ([[TASK-0157]]).
- [ ] Score each on the **ASBench cohort** (`task0308_attribution_scaling.py`
      is the template — annotated seed and truth, 108 structures, terminal
      exclusion, per-structure AUC).
- [ ] For each, report **three** numbers: raw AUC, within-structure
      ρ against proximity, and **AUC after rank-residualising on
      proximity**, exactly as `ctqw_proximity_partial` does.
- [ ] Rank the family by **residual**, not raw. Report the full table
      including the ones that get worse.
- [ ] Bonferroni across the family, and cluster-robust by protein.

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
