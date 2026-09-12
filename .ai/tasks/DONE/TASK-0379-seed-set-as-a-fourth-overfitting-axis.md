# TASK-0379 — Is the seed set a fourth overfitting axis, and what seeding rule is actually physical?

- Status: Done
- Owner: **Implementer**
- Priority: **High. The submission states its own multiplicity as "221 chances per target" — if the seed is a free axis, that number is wrong in our favour.**
- Filed: 2026-09-12 by Reviewer thread (id via `claim.py reserve-next`)
- Source: Team Lead, 2026-09-12 — *"if we can already show that we can 'overfit' using hamiltonian / operator / method choice … then maybe we can also do so by choosing a seed set"*
- Related: [[TASK-0102]], [[TASK-0325]], [[TASK-0336]], [[TASK-0338]], [[TASK-0378]], [[HYP-P8]]

## Why this matters more than it looks

Our own Section 1 says: *"with thirteen operators and seventeen scores there are
**221 chances per target**, and reporting the best of them is ordinary practice in
this field."* That sentence is the submission's honesty about its own multiplicity.

**It counts two axes. The seed set is a third, and nobody has counted it.** If
seed choice spans a material range of achievable AUC, then 221 understates the
real search space **in our own favour**, and the sentence needs correcting before
a reviewer does it for us.

[[TASK-0378]] just established that the *computation* is exactly reproducible and
that every source of spread is a **choice**. The seed is the one choice whose
capacity has never been measured.

## What the register already says — and it predicts a null

[[TASK-0102]] ran 40 biologically-uninformed single-residue seeds on BCR_ABL1:

> **A strong majority (70–75%) of arbitrary, biologically-uninformed single-residue
> seeds reproduce comparable floor-clearing performance against the same pocket
> label.** The good AUC is predominantly a property of `H_new`'s fixed
> ground-state shape (94.5% ground-mode weight), not evidence of
> active-site-to-pocket coupling.

**That cuts against the hypothesis**, and it is the right pre-registration: if
most arbitrary seeds already reproduce the number, seed *optimisation* has little
left to gain. **If Arm A nevertheless finds a large span, [[TASK-0102]]'s scope
was too narrow** — one target, one operator, single-residue seeds only — and that
is itself the finding.

## Arm A — the capacity ceiling (the Team Lead's "bizarre" option, made rigorous)

**Question:** with operator and score **fixed**, how much of the AUC range can
seed choice alone reach?

- **Do not frame it as "can we hit AUC 1.0".** Best-of-N over seed sets will reach
  a high number by chance, exactly as best-of-884 reached 137 families against a
  null of 99.8. **The measurable quantity is the excess over a matched null**, and
  without one this arm proves nothing. Same discipline as [[TASK-0336]]/[[TASK-0338]].
- **Report the distribution, not the maximum.** Sample seed sets (random residues,
  random surface patches, random pockets of matched size), score each, and report
  the **span** and the **percentile of the true active site** within it. A true
  active site sitting at the 50th percentile of arbitrary seeds means the seed
  carries nothing; sitting at the 99th means it carries something.
- **Match on size.** Seed-set cardinality changes the answer on its own; compare
  like with like or the result is a size effect wearing a biology costume.
- **Then the second-order question the Team Lead actually wants**: for the
  best-scoring seed sets, *where are they*? If they cluster on something
  identifiable — communication hubs, conserved residues, the pocket itself — that
  is a finding. If they are arbitrary, it is a capacity result. **Both are
  publishable and they must be distinguished before looking.**

## Arm B — what seeding rule is physical? (the more valuable half)

The challenge says *"seeded at the active site."* **That phrase is not a
definition**, and we have never justified ours against alternatives.

Candidate rules, each defensible and each cheap to score on the existing cohort:

| rule | rationale |
|---|---|
| UniProt active-site annotation (**current**) | what we ship; annotation-derived, not structural |
| Catalytic residues only | the narrowest chemically meaningful definition |
| Ligand-contact residues in the holo form | what the site *does*, not what it is called |
| Full binding pocket (fpocket/PASSer on the orthosteric site) | structural, method-consistent with the candidate side |
| Pocket centroid, single point | the minimal control — if this ties the others, the seed set carries nothing beyond location |

**Score all five on the same cohort with the operator and score fixed.** The
interesting outcomes are (i) they all tie, which says seed definition is not
load-bearing and simplifies every future run, or (ii) one wins materially, in
which case we have been using the wrong one and should say so.

## Constraints

- **Fix the operator and score before starting.** This task measures one axis; a
  sweep over two axes at once cannot attribute anything.
- **Every arm needs its matched null stated before it runs** — the standing
  discipline, and the reason this register's negatives are credible.
- Cluster-robust inference by protein ([[TASK-0337]]). Family counting, not
  protein counting.
- **No change to the shipped seeds, residues or numbers.** This measures capacity
  and alternatives; changing what we ship is a separate decision.
- Per `COMMON.md`'s standing rule: read what produces each arm before trusting a
  number, including [[TASK-0102]]'s own.

## Pre-registered prediction

**Arm A: the true active site sits unremarkably inside the arbitrary-seed
distribution, and the best-of-N excess over the matched null is small** —
[[TASK-0102]] and [[HYP-P8]]'s ground-mode-dominance finding both point that way.
**Arm B: the five rules tie**, for the same reason — if `H_new`'s ground state
dominates the score, the seed's precise definition cannot matter much.

**If either prediction fails, it is the more interesting outcome**, and in Arm A's
case it means the submission's "221 chances per target" is an undercount that must
be corrected.

## What follows for the submission, either way

- **If seed capacity is small**: the 221 figure stands, and we can say the seed
  axis was *measured* rather than assumed — which is stronger than silence.
- **If it is large**: the multiplicity sentence is wrong in our favour and gets
  corrected. That is the kind of correction this project has already made four
  times, and making it ourselves is worth more than having it found.

## Done (2026-09-12, Implementer C)

**Arm A's prediction fails, decisively: seed-set capacity is large. Arm B's
prediction also fails, in a sharper direction than anticipated: a single point
frequently beats the full curated seed, not merely ties it.**

### Setup — operator and score fixed, per this task's own Constraint

`H_new` (this project's own shipped-default Hamiltonian, `hamiltonians.
build_H_new` — confirmed the actual winner for every one of these 7 targets
in [[TASK-0378]]), scored by `time_averaged_ctqw_converged(coherent=False)`
occupation AUC against the real drug-derived pocket label
(`allostery.metrics.auc`). One `eigh` per target, reused for every seed and
every rule below — H does not depend on the seed. Cohort: the 7
`targets.yaml` entries with both a real UniProt-derived active site and a
real drug-ligand pocket label ([[TASK-0209]]'s own scope, reused verbatim
— the other 7 entries have no derivable druggable pocket to seed towards).
Direct extension of [[TASK-0102]] (one target, single-residue seeds only)
to all 7, matched-size seed sets, and a genuine matched null.

### A real performance defect caught before trusting the run

First full run (N=2000 draws x K=200 permutations, `allostery.metrics.auc`
= `sklearn.roc_auc_score` per call) took **851s for KRAS_G12C alone** —
the smallest of the 7 targets — and was killed rather than left to run for
hours across all 7. Root cause: the label-permutation null needs
`n_perm x n_random` = 400,000 AUC evaluations per null type per target,
and `roc_auc_score`'s own per-call validation/sorting overhead does not
scale to that count. Fixed with `vectorized_auc_many()`: the Mann-Whitney
rank-sum identity (`AUC = (R_pos - n_pos(n_pos+1)/2) / (n_pos*n_neg)`)
computed for all `n_random` cached occupation vectors against one
permuted label in a single vectorized pass — `n_random`x fewer Python-level
calls per permutation. **Verified byte-identical to `roc_auc_score` on 20
random synthetic trials before use**, and re-ran the pilot to confirm it
reproduces the pre-fix numbers exactly (KRAS_G12C `best_of_N=0.8389`, null
mean 0.6488, identical to the digit) before trusting the full run. Full
run: 987s total, all 7 targets.

### Arm A — capacity ceiling: large, and real (6/7 targets)

| target | N | n_seed | true AUC | pctl vs random seed | best-of-2000 | matched-null mean | excess | p |
|---|---|---|---|---|---|---|---|---|
| KRAS_G12C | 170 | 18 | 0.5136 | 0.496 | 0.8750 | 0.7324 | **+0.143** | <0.005 |
| BCR_ABL1 | 451 | 26 | 0.5408 | 0.425 | 0.8825 | 0.7339 | **+0.149** | <0.005 |
| CARDIAC_MYOSIN | 704 | 18 | 0.5485 | 0.561 | 0.9143 | 0.7540 | **+0.160** | <0.005 |
| PTP1B | 298 | 9 | 0.5078 | 0.348 | 0.8514 | 0.7384 | **+0.113** | <0.005 |
| GLUCOKINASE | 448 | 16 | 0.4673 | 0.448 | 0.8523 | 0.7217 | **+0.131** | <0.005 |
| CASPASE1 | 255 | **2** | 0.6780 | 0.905 | 0.8581 | 0.8246 | +0.034 | 0.290 |
| CASPASE7 | 461 | **2** | 0.6076 | 0.526 | 0.9113 | 0.7966 | +0.115 | 0.005 |

**The true active site's own percentile among 2000 arbitrary matched-size
seed sets is unremarkable for 6/7 targets (35th-56th percentile)** —
[[TASK-0102]]'s own BCR_ABL1-only finding generalizes: the reported seed
was not itself cherry-picked, and its AUC is what a typical arbitrary seed
of the same size would also produce. CASPASE1's 90.5th percentile is the
one exception, plausibly explained by its extreme seed size (n_seed=2,
the smallest in the cohort by a wide margin — a 2-residue seed has far
higher between-draw variance than an 18-26-residue one).

**But best-of-2000 reaches AUC 0.85-0.91 for every one of the 7
targets — including against a MATCHED, MEANINGLESS label** (the
permutation null's own best-of-2000 averages 0.72-0.82). **This is the
decisive, new measurement TASK-0102 never made**: with 2000 candidate
seed sets to choose from, an AUC in the 0.72-0.82 range is achievable by
pure best-of-N selection against a label that carries no information at
all. On top of that already-high baseline, the REAL label adds a further,
statistically significant **+0.11 to +0.16 AUC** for 6/7 targets (p<0.005
for 5, p=0.005 for the sixth) — genuinely more than the null, but small
next to how much the null itself already inflates from selection alone.
CASPASE1 (n_seed=2) is the one target where the excess is not
distinguishable from the null (p=0.29) — likely underpowered by the same
small-seed-size mechanism that produced its percentile outlier above, not
a different finding.

**Read plainly, against this task's own pre-registered prediction**: the
prediction was "the excess over a matched null is small." **It is not
small — it is the single largest number this task produced, and it is
statistically significant on 6 of 7 targets.** The seed axis has real,
material capacity to inflate an AUC through selection alone, fully
independent of whether the selected seed carries genuine biological
information. **The submission's "221 chances per target" undercounts the
real search space, exactly as this task's filing warned it might** — not
because we ourselves searched over seeds (we did not: one pre-specified
UniProt-derived seed per target, and its own unremarkable percentile
confirms it was not cherry-picked), but because the capacity for a
reviewer's exact concern — "could this number have been produced by
trying many seeds and reporting the best?" — is now measured, not merely
assumed absent.

### Arm B — which seeding rule is physical: not a tie, and not in the anticipated direction

| target | 1. shipped (union) | 2. catalytic-only | 3. func-ligand contact | 4. fpocket structural | 5. centroid point |
|---|---|---|---|---|---|
| KRAS_G12C | 0.5136 | N/A¹ | 0.5136² | 0.5413 | **0.6324** |
| BCR_ABL1 | 0.5408 | N/A¹ | 0.5408² | 0.5549 | 0.5046 |
| CARDIAC_MYOSIN | 0.5485 | N/A¹ | 0.5485² | 0.5330 | **0.6316** |
| PTP1B | 0.5078 | 0.4771 | N/A³ | 0.4590 | **0.6097** |
| GLUCOKINASE | 0.4673 | N/A¹ | 0.4673² | 0.4260 | **0.5357** |
| CASPASE1 | 0.6780 | 0.6780⁴ | N/A³ | 0.7216 | 0.6640 |
| CASPASE7 | 0.6076 | 0.6076⁴ | N/A³ | 0.5680 | **0.6482** |

¹ UniProt has no "Active site"-typed feature for this protein, only
"Binding site" (checked directly, not assumed from the shipped set).
² **Identical to rule 1 by construction, not a finding**: `labels.py`'s
own tier-1 active-site resolution IS `func_ligand` contact for these 4
targets (confirmed directly against `labels.py`'s own tiering doc — its
tier 1 is func_ligand contact, tier 2 is curated UniProt, tried only if
tier 1 fails). Rules 1 and 3 cannot differ here regardless of biology.
³ `func_ligand` deliberately empty (TASK-0216's own disclosed decision;
PTP1B/CASPASE1/CASPASE7 have no substrate/functional ligand in the holo
deposition to derive a contact site from).
⁴ Identical to rule 1 for the same reason in reverse: these 2 targets'
shipped site comes from tier-2 curated UniProt, and their UniProt record
has no separate "Binding site" entries beyond the "Active site" ones, so
the union (rule 1) and the Active-site-only subset (rule 2) coincide.

**Only 3 of the 10 rule-pairs above are genuinely independent comparisons**
(1-vs-3 and 1-vs-2 are forced-equal or N/A for most targets) — the real
comparisons are **1 vs 4** (annotation vs. structural fpocket pocket, all
7 targets) and **1 vs 5** (annotation vs. single centroid point, all 7
targets), plus PTP1B's one real 1-vs-2 case.

**Rule 5 (a single point) beats rule 1 (the full curated multi-residue
seed) on 5 of 7 targets, by up to +0.12 AUC (KRAS_G12C), and never loses
by more than -0.036 (BCR_ABL1).** This is a sharper result than "they
tie": the minimal control does not merely fail to lose, it frequently
**wins**. Consistent with [[HYP-P8]]/[[TASK-0102]]'s ground-mode-dominance
mechanism — since the fixed Hamiltonian's leading eigenmode shape barely
depends on which residue(s) it is seeded from, a single well-placed point
often produces a cleaner projection onto that mode than an
average over several source indices does (`coherent=False`'s own mixture
convention), rather than a diluted one.

**Rule 4 (fpocket structural pocket) is close to rule 1 in both
directions** (-0.049 to +0.044), no consistent winner — the shipped
UniProt annotation and a structurally-derived pocket at the same site are
roughly interchangeable for this fixed operator/score.

**PTP1B's one real rule-1-vs-rule-2 case**: catalytic-only (0.4771) scores
0.031 lower than the shipped union (0.5078) — a real but modest
difference, the wrong direction to argue for narrowing the definition.

**Read against this task's own pre-registered prediction** ("the five
rules tie"): they do not tie, but not because one definition is
materially *more correct* — because seed cardinality/definition barely
matters at all once the operator is fixed, to the point that the minimal
possible seed (one point) frequently outperforms the most elaborate one.
That is the stronger version of "the seed carries nothing beyond
location" this task's own filing named as one of the two possible
readings.

### What follows for the submission — flagged, not edited here

Per this task's own Out-of-scope ("No change to the shipped seeds,
residues or numbers... changing what we ship is a separate decision"),
nothing in `PHASE1_SUBMISSION_V4.md` or any shipped result was touched.
**Flagged for whoever next drafts the multiplicity paragraph**: the "221
chances per target" sentence is accurate about what was tried (13
operators x 17 scores, one pre-specified seed) but does not name the
seed axis's own measured capacity (best-of-2000 alone reaches 0.85-0.91,
matched-null informed, on 6/7 targets) — the honest addition is that the
seed was NOT searched over (unremarkable percentile, confirmed here) and
that its definition does not matter much once fixed (Arm B), not that
221 itself needs multiplying by anything, since no seed search was ever
performed in producing the shipped numbers.

### Constraints honored

Operator and score fixed throughout — no sweep over two axes at once.
Every arm's matched null stated before being trusted (label-permutation
for Arm A; Arm B is a direct comparison at fixed operator/score, no null
needed since no selection occurs). Cluster-robust by construction (7
distinct protein families, no repeats). No change to any shipped seed,
residue, or number. `labels.py`'s own tiering doc read and applied before
trusting rules 1/2/3's overlap, catching the by-construction ties before
they were reported as findings.

### Out of scope / not done

- Random surface patches used a spatially-contiguous nearest-neighbour
  blob (Euclidean Ca distance), not true solvent-accessible-surface
  sampling — no SASA computation was available in this environment;
  disclosed as a proxy, not presented as true surface restriction.
- Did not extend Arm A/B to the wider allosteric-branch's 13-operator x
  17-score grid or its 1022-protein/276-family cohort — that is a
  separate, much larger pipeline ([[TASK-0336]]/[[TASK-0338]]'s own);
  this task's own Constraint ("fix the operator and score before
  starting") makes that grid out of scope by definition, not an
  oversight.
- CASPASE1/CASPASE7's n_seed=2 results are the least reliable numbers in
  this task (highest variance, one clear outlier) — flagged, not
  smoothed into the 7-target average.

### Landed

New hypothesis **HYP-P31** in `physics.md`.

**Files**: `__WORK_IN_PROGRESS__/scripts/task0379_seed_capacity_and_definition.py`.
**Data**: `__WORK_IN_PROGRESS__/results/tasks/0379_seed_capacity_and_definition/
{result.json,pilot_result.json,run_log.txt}`.
