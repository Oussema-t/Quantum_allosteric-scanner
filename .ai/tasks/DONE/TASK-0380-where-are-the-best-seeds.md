# TASK-0380 — Where are the best seeds? Residualise the seed-axis capacity on distance to the pocket

- Status: Done
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

## Done — 2026-09-13, Implementer D

**Pre-registered prediction confirmed, at the "largely vanishes" reading, not a
clean full vanish: distance to the pocket explains 65–100% of the seed-axis
capacity [[TASK-0379]] measured, and no target's residual survives correction
for the number of comparisons this task itself ran.**

### Recovery — validated exactly before anything was built on it (Scope item 1)

`scripts/task0380_seed_location_residualisation.py` imports
`task0379_seed_capacity_and_definition` directly and replays its exact RNG
call sequence (`det_seed(target)` seeding `np.random.default_rng`; 2000
scattered-residue draws, then 2000 spatial-patch draws, then 200
label-permutation null draws, in that order — no new sampling). **All 7
targets' regenerated best-of-2000 AUCs matched TASK-0379's committed
`result.json` bit-for-bit** (equality, not `np.isclose`), including the
matched-null's own best-of-N means — the script raises before computing
anything further on any target that fails this gate, and none did. No new
`eigh`, no new draws: this is read-only re-analysis of an already-committed
result. Full run: 1004s, all 7 targets (`run_log.txt`).

### Item 2/3 — located and residualised: the decisive test

For every draw, computed the seed set's Cα centroid and its distance to the
**true drug-pocket centroid** (`labels_obj.pocket`, not the seed). Rank-
residualised AUC on that distance ([[TASK-0310]]'s own OLS-on-ranks formula,
`residualise()`, copied verbatim). To keep before/after commensurable in AUC
units (the residual itself lives on a rank scale, not [0,1] — a real
implementation bug caught and fixed before trusting the first pilot run, see
below), the residual is used only to **select** which draw is "best after
controlling for distance" (argmax), and that draw's own raw AUC is reported —
applied identically to each of the 200 null replicates (same distance ranks,
since distance does not depend on the permuted label) to build a null
distribution in the same units as `excess_before`.

| target (n_seed) | dist ρ (res / patch) | excess before → after, **residue** (p) | excess before → after, **patch** (p) |
|---|---|---|---|
| KRAS_G12C (18) | −0.735 / −0.828 | +0.143 → **−0.001** (p=0.505) | +0.287 → **−0.084** (p=0.965) |
| BCR_ABL1 (26) | −0.676 / −0.899 | +0.149 → **+0.052** (p=0.070) | +0.331 → **−0.006** (p=0.530) |
| CARDIAC_MYOSIN (18) | −0.586 / −0.812 | +0.160 → **+0.056** (p=0.050) | +0.313 → **+0.126** (p=0.020) |
| PTP1B (9) | −0.379 / −0.763 | +0.113 → **+0.074** (p=0.055) | +0.218 → **+0.092** (p=0.050) |
| GLUCOKINASE (16) | −0.642 / −0.794 | +0.131 → **+0.064** (p=0.050) | +0.268 → **+0.041** (p=0.205) |
| CASPASE1 (2, flagged) | −0.460 / −0.503 | +0.034 → **−0.044** (p=0.740) | +0.033 → **−0.021** (p=0.585) |
| CASPASE7 (2, flagged) | −0.527 / −0.567 | +0.115 → **+0.043** (p=0.205) | +0.144 → **+0.071** (p=0.125) |

**Averaged over the 5 well-sized targets**: raw excess (before) averages
+0.139 (residue) / +0.283 (patch); residualised excess (after) averages
+0.049 / +0.034 — a **65% (residue) to 88% (patch) reduction**, consistent
with the working hypothesis that the seed behaves substantially as a
location parameter.

**But it is not a clean, uniform vanish.** KRAS_G12C and BCR_ABL1's patch
excess fully vanishes (goes to ≈0 or negative); CARDIAC_MYOSIN's patch excess
survives at nominal p=0.020, and four of the ten residue/patch pairs across
the 5 well-sized targets sit at nominal p≈0.05–0.074. **None of the 10
target×family tests run here would survive Bonferroni correction for those
10 comparisons** (threshold p<0.005; the smallest observed is 0.020) — the
honest reading is that the residual, where nominally present, is not
distinguishable from noise once this task's own multiplicity is accounted
for, the same standing discipline [[TASK-0336]]/[[TASK-0338]]/[[TASK-0379]]
itself applied to best-of-N selection. CASPASE1/CASPASE7 (n_seed=2) are
reported but excluded from this average, per this task's own Scope note on
their reliability — both show the same qualitative before→after collapse.

### Item 5 — the true active site's own distance, in context

`pct_true_dist_closer_than_random`: KRAS_G12C 0.000, BCR_ABL1 0.002 — the
**true active site sits almost exactly at the pocket itself** for these two
targets, which is exactly why residualising on distance removes essentially
all of their seed-capacity excess. CARDIAC_MYOSIN 0.344, PTP1B 0.148,
GLUCOKINASE 0.506 — **GLUCOKINASE's true UniProt active site is at the
median of the random-seed distance distribution**, i.e. its own location
carries no more pocket-proximity information than an arbitrary seed of the
same size, yet TASK-0379 still measured a real excess there before
residualisation. Read together with the table above: targets where the true
site's own location is *not* trivially predictive of the pocket
(CARDIAC_MYOSIN, PTP1B, GLUCOKINASE) are exactly the targets whose
residualised residual sits closest to (nominal) significance — internally
consistent, though none clears the multiplicity bar above.

### Item 4 — candidate list stated before computing, per this task's own requirement

Sequence conservation, betweenness centrality, closeness centrality, burial
(SASA), and a hinge-residue proxy — named in this task's own filing.
Degree centrality added for free alongside betweenness/closeness (same
`allostery.baselines` call), not a substitution. All reused from existing
project code, not reimplemented: `allostery.baselines.{degree,betweenness,
closeness}_centrality`; burial via `allostery.corex.per_atom_asa`/
`per_residue_native_asa` (BioPython ShrakeRupley, `task0257`'s own
convention); hinge via `allostery.potentials.gnm_context`'s shared Kirchhoff
eigendecomposition, negated |lowest non-trivial GNM mode| (`task0226`'s own
`slow1_minima_score` convention); conservation via
`task0274_conservation_chemistry_residual.conservation_array` (live
Pfam-seed alignment — succeeded for 6/7 targets; **CARDIAC_MYOSIN's Pfam
match mapped 0 of 704 residues** (identity 0.353, a weak/wrong domain match)
and is correctly reported as unavailable, not fabricated — this is exactly
the target with the strongest surviving nominal residual, so the one
candidate feature most likely to matter there could not be tested).

**No feature concentrates the top-scoring scattered seeds consistently
across targets.** Spearman(mean member-residue feature, distance-
residualised AUC) for the residue family is weak (|ρ|<0.28 throughout) and
**inconsistent in sign** across targets — e.g. hinge-score is positive for
BCR_ABL1/PTP1B/KRAS_G12C but negative for CARDIAC_MYOSIN/GLUCOKINASE. The
top-5%-of-seeds mean-feature-percentile summary is flat (0.49–0.53 across
every feature for KRAS_G12C, i.e. indistinguishable from the 0.50 expected
under no concentration at all).

**The patch family shows large, highly significant correlations with every
hub/burial feature even after distance-residualisation** (e.g. CARDIAC_
MYOSIN patch: degree ρ=−0.42 p=4e-87, burial ρ=−0.41 p=4e-80). **Flagged,
not over-read as a biological finding**: this project's own repeated lesson
is that degree/burial/centrality are themselves proximity/structure-core
proxies, only loosely linear in straight-line centroid distance — a
spatially-contiguous patch's mean degree/burial carries geometric
information a simple linear regression on centroid distance does not fully
remove. The honest reading is "more location, imperfectly regressed out by
a linear distance term," not "an answer-blind biological rule identified" —
stated explicitly so a future reader does not mistake p=4e-87 for evidence
of biology.

### What follows for the submission — flagged, not edited here

Per this task's own Out-of-scope, nothing in `PHASE1_SUBMISSION_V4.md` or
any shipped result was touched. **Flagged for whoever next drafts the
seed-axis paragraph** (the one [[TASK-0379]] itself flagged): the honest
addition is now sharper than "seed definition doesn't matter much" — it is
"the seed's measured capacity is 65–90% attributable to where it sits
relative to the pocket, not to which residues it names; what nominally
remains after accounting for location does not survive correction for the
number of targets tested." That is the mechanism [[TASK-0379]]'s own filing
asked this task to resolve.

### Constraints honored / Out of scope

Fixed operator and score throughout (inherited from [[TASK-0379]], no new
Hamiltonian/score/cohort). No shipped seed, residue, or number changed —
read-only re-analysis of an already-committed result. CASPASE1/CASPASE7 not
averaged into the 5-target headline. No new sampling: every draw is the
literal TASK-0379 draw, recovered by RNG replay and validated bit-for-bit,
not resampled.

### A real bug caught before trusting the first result, not just the recovery gate

The first pilot run reported "residualised excess" values of magnitude ~15
(e.g. best=38.6, null_mean=54.2) — nonsensical against an AUC scale. Root
cause: reporting the rank-OLS residual's own numeric value as if it were
directly comparable to a [0,1] AUC, when it lives on a rank-residual scale
with no such bound. Fixed by using the residual only to *select* the argmax
draw and reporting that draw's *raw* AUC instead (both for the real run and
for every null replicate) — the fix described under Item 2/3 above. Caught
on a 100-draw pilot before the full 2000-draw/200-permutation run was
trusted or launched.

**Files**: `scripts/task0380_seed_location_residualisation.py`.
**Data**: `results/tasks/0380_seed_location_residualisation/
{result.json,run_log.txt}`.
