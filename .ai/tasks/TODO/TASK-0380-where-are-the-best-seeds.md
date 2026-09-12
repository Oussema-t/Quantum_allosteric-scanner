# TASK-0380 — Where are the best seeds? Residualise the seed-axis capacity on distance to the pocket

- Status: TODO
- Owner: **Implementer**
- Priority: **High. One script, no new compute, and it decides whether [[TASK-0379]]'s capacity finding is mechanism or circularity.**
- Filed: 2026-09-13 by Reviewer thread (id via `claim.py reserve-next`)
- Source: Team Lead, 2026-09-12 — *"Are the best performing seeds located on particular residues, or is it just the proximity confound in disguise?"*
- Related: [[TASK-0379]], [[TASK-0310]], [[TASK-0102]], [[HYP-P8]], [[HYP-P31]], [[HYP-P13]]

## The question [[TASK-0379]] raised and did not answer

[[TASK-0379]] established that **seed choice alone reaches AUC 0.85–0.96**, with
excess over a matched label-permutation null of +0.11 to +0.16 (scattered seeds),
p<0.005 on 6/7 targets. It also found the true active site sits at an unremarkable
35th–56th percentile, so the shipped seed was *not* cherry-picked.

**What it did not ask is where the winning seeds are.** That is the difference
between a mechanism and a capacity number.

## The artifact already hints at the answer, and nobody drew the comparison

Both seed families were run and only the scattered one was discussed. Side by
side, from `results/tasks/0379_seed_capacity_and_definition/result.json`:

| target | scattered excess | **patch excess** |
|---|---|---|
| KRAS_G12C | +0.143 | **+0.287** |
| BCR_ABL1 | +0.149 | **+0.331** |
| CARDIAC_MYOSIN | +0.160 | **+0.313** |
| GLUCOKINASE | +0.131 | **+0.268** |
| PTP1B | +0.113 | **+0.218** |

**Spatially contiguous blobs beat scattered subsets roughly two-to-one on all five
well-sized targets** — and their null is *lower* (0.63–0.65 against 0.72–0.75), so
this is a real gap and not a shifted baseline.

A contiguous blob is essentially **a location**; a scattered subset averages over
many locations and washes out. That is consistent with [[TASK-0379]]'s own Arm B,
where **a single centroid point beat the full curated seed on 5 of 7 targets**.

**Working hypothesis: the seed behaves as a location parameter, not a biological
one — the proximity confound appearing in a third axis.** This task tests that
directly instead of inferring it.

## The data is recoverable for free

The winning seed sets were **not persisted** — `result.json` carries summary
statistics only. But `run_target` takes an explicit `rng_seed` and uses
`np.random.default_rng`, so **re-running regenerates the identical 2000 draws
deterministically.** No new sampling, no new `eigh`; the occupation vectors can be
recomputed or cached from the same path.

## In scope

1. **Recover the draws** for all 7 targets, both families, at the same `rng_seed`.
   **Validate first**: the regenerated best-of-N AUCs must equal
   [[TASK-0379]]'s committed values exactly (KRAS scattered 0.8750480584390619,
   patch 0.9250288350634372) before anything is built on them. If they do not
   match, the recovery is wrong and the task stops.
2. **Locate every seed.** For each draw, compute its Cα centroid and the
   **distance from that centroid to the true drug-pocket centroid**.
3. **The decisive test — residualise.** Regress seed-set AUC on
   centroid-to-pocket distance (rank residualisation, the register's own
   convention since [[TASK-0310]]) and report **the excess over the matched null
   before and after**. If the excess vanishes, the seed axis carries nothing but
   location.
4. **Then look for the thing that would make it usable.** For the top-scoring
   seeds, report whether they concentrate on anything identifiable **without
   knowing the answer**: sequence conservation, betweenness/closeness hubs, hinge
   residues, burial. **State the candidate list before computing it**, so a
   post-hoc match cannot be reported as a prediction.
5. Report the **true active site's** own centroid-to-pocket distance against that
   same distribution — it contextualises the 35th–56th percentile finding.

## Out of scope

- New sampling, new operators, new scores, new cohorts. [[TASK-0379]] fixed the
  operator and score deliberately; this task inherits that.
- Changing any shipped seed, residue, or number.
- The `n_seed=2` targets (CASPASE1/CASPASE7) are reported but **flagged as the
  least reliable**, per [[TASK-0379]]'s own note — do not average them in.

## Pre-registered prediction

**The excess largely vanishes under distance residualisation**, and the best seeds
are simply those closest to the pocket. Nine observables in this register have
died at exactly this step, and the patch-vs-scattered asymmetry already points
that way.

**If that holds, the honest reading is that the seed-axis capacity is
circular** — you would have to know the pocket to choose the seed — and it is a
capacity result, not a usable signal. **That is still worth having**: it is
"best-of-N is not a score" demonstrated on ourselves, in a third axis.

**If a residual survives, or the top seeds concentrate on something answer-blind,
that is the most interesting result this project has produced**, and it would be
the first observable to survive residualisation here.

## Why it matters beyond curiosity

The submission's own multiplicity sentence was examined in [[TASK-0379]] and found
accurate — the seed was never searched over. **This task decides what the seed
axis *is*, not whether we used it.** A location parameter and a biological
parameter have different consequences for what Phase 2 should build, and the
answer costs one script and no compute.
