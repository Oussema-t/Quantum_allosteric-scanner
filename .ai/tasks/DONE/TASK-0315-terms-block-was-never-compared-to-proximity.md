# TASK-0315 — The terms-block result was never compared to proximity, and the exemption from TASK-0308 was asserted, not measured

- Status: Done
- Priority: **Critical — this is the register's only surviving positive claim and it is in the submission brief as "the strongest constructive number either of us has."**
- Filed: 2026-09-01 by Reviewer thread
- Related: [[TASK-0263]], [[TASK-0275]], [[TASK-0277]], [[TASK-0287]], [[TASK-0303]], [[TASK-0308]], [[TASK-0310]]
- **Renumbered from TASK-0313 to TASK-0315** (Implementer C, 2026-09-01):
  Reviewer thread filed this under TASK-0313 without `reserve-next`, on the
  same day another thread's own TASK-0313 ("Verify the Silverman
  multimodality implementation") was in flight — a genuine id collision,
  the exact failure mode [[TASK-0045]] was built to prevent. The
  Silverman task was already Done (untouched, kept its id — first claim
  wins); this file was still unstarted TODO, so it moved instead. No
  in-repo reference to this task existed under the old id (checked live,
  not assumed) — the only `TASK-0313` hits outside the two task files
  themselves belong unambiguously to the Silverman task.

## The defect

`CTQW_CONTRIBUTION_BRIEF_V2.html`'s own "Holds" table reads:

| Arm | AUC |
|---|---|
| Potential terms of `H_new` | **0.751** (cluster-robust p = 0.019) |
| `V_C` alone | 0.6365 — "beats the whole walk by itself" |
| CTQW | 0.575 |

**The row that belongs in that table and is missing:**

| `euclid_from_seed_centroid` (distance to the active site) | **0.706** |

[[TASK-0277]]'s own consolidated sweep, `euclid` apo = **0.706**. Same
20-target [[TASK-0243]] frozen set. Same metric — that task explicitly adopts
`task0254`'s `cv_auc` as "the ONE AUC definition for every feature (even solo
ones)", which is the identical function [[TASK-0263]] calls for both
`terms_block_auc` and `ctqw_auc`. **Directly comparable, already on disk, never
placed side by side.**

Consequences:

1. Plain distance-to-seed beats `V_C` alone (0.706 vs 0.6365). The brief's
   "beats the whole walk by itself" is true and unimpressive — so does a
   distance.
2. The five-term fitted block's margin over plain distance is **+0.045**, and
   **no significance test for that gap exists anywhere in the register.** The
   p=0.019 is against CTQW (0.575), the weakest of the three arms.
3. The brief lists proximity as the **top** contributor (0.6147, +22.9%) in its
   own attribution table four sections earlier. The confound is named in one
   table and absent from the one carrying the constructive claim.

## The test is already run — the comparator was on disk all along

**2026-09-01, Reviewer thread.** No new computation was needed.
`results/tasks/0254_fpocket_variance_and_crypticity/part_a_shapley_attribution
.json` already stores `subset_aucs` for every subset of the 3 blocks, per
target, computed by the **same `cv_auc`** [[TASK-0263]] calls. Median over the
same 20 targets:

| subset (all via `cv_auc`, frozen 20, seed rows excluded) | median AUC |
|---|---|
| `fpocket, geometry` | **0.8612** |
| `ctqw, fpocket, geometry` (full model) | 0.8568 |
| `ctqw, geometry` | 0.8168 |
| **`geometry`** (degree + euclid + hop) | **0.7953** |
| **terms block** (V_B,V_T,V_R,V_C,V_M) — [[TASK-0263]]'s headline | **0.7513** |
| `ctqw, fpocket` | 0.7572 |
| `ctqw` | 0.5751 |
| `fpocket` | 0.5655 |

Paired per-target, [[TASK-0261]]'s own `cluster_sign_flip_test`, 13 clusters:

```
terms - ctqw     : median +0.2136   p = 0.0188   <- reproduces the published headline
terms - geometry : median -0.0101   p = 0.3359   <- geometry wins on 10/20 targets
```

**The terms block does not beat the geometry block. It is 0.044 below it, and
the difference is not significant in either direction.** The brief's "strongest
constructive number" (0.751) sits *below* a three-column baseline of
degree + distance-to-seed + hops-to-seed (0.795) — a baseline this register
computed in [[TASK-0254]] and has been carrying in its own results directory
ever since.

Note also **`ctqw, fpocket, geometry` (0.8568) is BELOW `fpocket, geometry`
(0.8612)** — adding the walk to the model makes it worse, which is the same
fact the register already reports as "CTQW added-last median −0.2%", visible
here directly.

This converts the Scope below from "run the test" to "the test is run; act on
it." The remaining open question is the residualised version, not the
head-to-head.

## The exemption, and why it does not hold

[[TASK-0308]]'s own commit message exempts this result:

> Unaffected: the Hamiltonian potential-terms result (0.751 vs 0.575,
> cluster-robust p=0.019) is a different analysis on different quantities —
> V_C is a GNM cross-correlation, not a walk — and does not depend on this.

That argues from **how the quantity is constructed** (not seeded). The confound
is about **what it correlates with**. Seed-independence does not imply
proximity-independence: `V_C` is a centrality, the active site tends to be
central, and centrality is high near the centre whether or not a seed was ever
supplied.

**Measured directly, 2026-09-01, Reviewer thread** — each term against
`-hop_from_seed`, seed rows excluded, 14 targets of `config/targets.yaml`:

```
median rho:   V_C -0.237   V_B +0.192   V_R +0.369   V_M -0.400
extremes:     V_C -0.546 (CARDIAC_MYOSIN)      V_M -0.846 (CARDIAC_MYOSIN_TABLE1)
              V_R +0.613 (GLUCOKINASE)         V_B +0.667 (CARDIAC_MYOSIN)
```

Far cleaner than CTQW's +0.735 — the exemption's instinct was directionally
right. But it is **not zero**, and this register's own standing rule
([[TASK-0287]] conditioned druggability on size and found it was mostly size;
[[TASK-0303]] conditioned mode shift on size and found it independent) is
*condition on the confound, do not eyeball it*. This is the one place that rule
was waived, on the one claim that survived.

## Scope

- [x] **DONE above** — `terms_block − geometry` = −0.0101, p = 0.336, from
      already-stored `subset_aucs`. The claim does not survive as stated.
- [x] Commit the comparison as a small script so it is reproducible rather than
      a Reviewer-thread one-off, and add `euclid`/`hop` **solo** columns
      (0.706 / 0.699 from [[TASK-0277]]) to the same table.
- [x] Residualise the terms block on proximity rank-wise per structure
      (`ctqw_proximity_partial`'s own method, [[TASK-0308]]) and report the
      residual AUC. Do the same for `V_C` alone.
- [x] Re-measure the per-term ρ(term, proximity) table above on the **frozen
      20**, not `targets.yaml`'s 14 — the Reviewer's numbers are the right
      test on the wrong cohort.
- [x] Correct the brief's "Holds" table: add the proximity row whatever the
      outcome, and restate the p=0.019 as *against CTQW*, not against the best
      baseline.

## A second, smaller defect in the same claim

[[TASK-0263]]'s conclusion — *"the physics encoding was right, the propagator
was where the signal was lost"*, repeated in the brief as *"What fails is the
propagation step layered on top of it"* — does not follow from the comparison
made. Read the code: `terms_block_auc[t] = cv_auc(terms_X, y)` is a
**five-column OLS model fitted per CV fold**; `ctqw_auc[t] = cv_auc(x_ctqw
.reshape(-1,1), y)` is **one unfitted column**. A scalar summary of a
five-dimensional input loses dimensions by construction — that is arithmetic,
true of *any* scalar, and cannot localise the loss to the propagator
specifically.

- [x] Either restate the conclusion at the size the evidence supports ("five
      fitted features beat one unfitted score, and most of that is available
      from distance alone"), or add the comparison that would actually support
      it: a **1-column** summary of the terms (e.g. the fitted linear
      combination, or `V_C` alone) against CTQW's 1 column.
- [x] Also restate "several single terms alone reach AUC 0.81–0.93 with zero
      fitting" — that is a maximum selected over ~100 term×target cells,
      reported as if it were a typical value.

## Constraints

- **Do not re-tune anything.** This is a re-scoring against a comparator that
  should always have been there, not a new sweep.
- **Report the number that moves against us** — if the terms block does not
  clear `euclid` significantly, that is the finding, and the brief's "Holds"
  section becomes a "Does not hold" section.
- Positive control ([[TASK-0305]]'s lesson): `euclid` residualised on
  proximity must land at ~0.5. A harness that cannot reproduce that is broken.

## Note

This is the same error [[TASK-0308]] corrected for CTQW, one layer up: a
headline scored against a weak comparator rather than against the dominant
confound. That commit's instinct to quarantine the terms result is
understandable one day after withdrawing the CTQW number — but it quarantined
the claim most load-bearing for the submission.

## Done (2026-09-01, Implementer C)

**Fresh recomputation, not a re-read of the old JSONs**, on the frozen 20
(20/22 usable, same two HIV_INTEGRASE targets skipped for the same
documented reason — empty active-site seed): `terms_block=0.7513`,
`geometry=0.7953`, `euclid=0.7057`, `hop=0.7069`, `ctqw=0.5751`,
`V_C=0.6365` — every one of these reproduces the Reviewer thread's own
cited value to 3-4 decimal places, confirming the comparator was correctly
identified.

**One reproducibility gap found and disclosed, not chased down**:
`terms_block − geometry` reproduces at p=0.292 (cited p=0.336 — same
conclusion, close enough), but `terms_block − ctqw` reproduces at
**p=0.049, not the previously-published p=0.019**. Root cause isolated to
one target: `DHPS_GC7`'s own `terms_block`/`ctqw` values differ materially
between [[TASK-0263]]'s original run and this one (0.596→0.363 and
0.739→0.846 respectively) — reproducible across two independent reruns of
this script, so not run-to-run noise. Not chased further (out of this
task's own Constraint — re-score against a comparator, not audit pipeline
drift) but flagged for whoever owns it next. **Both p-values are still
below 0.05; the qualitative headline is unchanged, its margin is not.**

**Positive control did not pass cleanly, root-caused before trusting
anything downstream, not ignored**: `euclid` residualised on `hop`-only
proximity lands at 0.61, not ~0.5 as the Constraint expected. A synthetic
self-check (redundant predictor → 0.509, independent predictor preserved:
0.830→0.814, both built into the committed script so this reruns
automatically) confirms `rank_residualize` itself is correct — this is a
real cohort finding, not a harness bug: hop-distance and Euclidean
seed-distance are correlated (checked both directions) but **not fully
redundant** on this register's own 20 targets, which — unlike ASBench's
more proximal-skewed population — include several genuinely distal-labelled
cases (FBPASE_95S: raw euclid AUC 0.036, i.e. strongly anti-proximal).
Fixed by residualising on **both proximity measures jointly** for the main
test (a more complete "closeness to seed" control than either alone), and
by reporting the cross-check honestly: `euclid`-on-`hop` residual is not
cluster-robustly distinguishable from chance either (p=0.121, likely
underpowered at 13 clusters rather than a clean pass).

**Per-term ρ(term, proximity), frozen 20** (rho against `-hop_from_seed`,
matching the preliminary table's own sign convention so the two are
directly comparable): `V_B +0.335, V_T +0.128, V_R +0.366, V_C −0.074,
V_M −0.468` (ranges available in the script's own JSON output). Same sign
throughout as the preliminary 14-target table (`V_C −0.237, V_B +0.192,
V_R +0.369, V_M −0.400`), `V_R` and `V_M` close in magnitude too — the
14-target result generalises to the frozen 20, `V_C`'s own weaker
magnitude here (−0.074 vs −0.237) is itself informative for what follows.

**Per-term cell distribution** (Scope's own ask: restate "0.81–0.93 with
zero fitting" honestly): n=100 cells (5 terms × 20 targets), **median 0.543,
mean 0.562, max 0.973**. The cited range sits at the extreme max, not a
typical cell — most single terms on most targets are barely above chance.

**The residualised headline, jointly on hop AND euclid** (the core new
result):

| arm | raw mean AUC | residual mean AUC | vs chance (cluster-robust) |
|---|---|---|---|
| terms block (fitted, 5-column) | 0.740 | **0.660** | **p = 0.027 — survives** |
| `V_C` alone | 0.650 | 0.566 | p = 0.31 — not distinguishable from chance |
| CTQW | 0.548 | 0.476 | p = 0.68 — not distinguishable from chance |
| terms, unfitted equal-weight sum | 0.582 | 0.572 | p = 0.31 — not distinguishable from chance |

**Mixed result, reported as measured, not rounded toward either extreme.**
The fitted potential-terms combination retains a real, cluster-robustly
significant signal beyond geometry AND both proximity measures jointly
controlled for — the constructive claim is not fabricated, and this is a
materially stronger check than existed before (proximity had never been
tested against it at all). But three specific over-claims on the brief's
own card do not survive: (1) it does not beat the geometry baseline
(0.751 < 0.795, non-significant either direction); (2) `V_C` alone — the
card's own "beats the whole walk by itself" line — does not survive
proximity-residualisation, while CTQW's own residual (reproduced
independently here, on our own 20-target cohort and labels, not just
ASBench) also does not, so `V_C` is not shown to be meaningfully different
from CTQW on the one axis the card used to distinguish them; (3) the
0.751-vs-CTQW comparison is fitted-5-column vs unfitted-1-column — the
matched unfitted-vs-unfitted comparison (terms-sum 0.599 vs CTQW 0.575)
shows most of the raw margin is the fitting itself, not the physics
encoding specifically, which is exactly [[TASK-0263]]'s own "second, smaller
defect" this task's Scope named.

**Brief corrected in the same commit** (`CTQW_CONTRIBUTION_BRIEF_V2.html`):
a new "Corrected" card added immediately after the original "Holds" card
(original left in place, per this register's own append-don't-silently-edit
convention) with both tables above, the fitted-vs-unfitted defect explained
in the collaborator's own terms, and the "Credit where it is due" bullet
restated at the corrected size (residual gain over geometry-and-proximity,
not raw 0.751; `V_C`-alone framing dropped).

**Not done**: the DHPS_GC7 reproducibility discrepancy (disclosed, not
root-caused — a separate data-pipeline question, not this task's own
Constraint); a third, independent proximity measure to fully validate the
positive control beyond the two-way hop/euclid cross-check (none is
currently established in this codebase).

**Script**: `scripts/task0315_terms_block_vs_proximity.py`. **Data**:
`results/tasks/0315_terms_block_vs_proximity/terms_block_vs_proximity.json`.

**Moved TODO/IN_PROGRESS -> DONE.**
