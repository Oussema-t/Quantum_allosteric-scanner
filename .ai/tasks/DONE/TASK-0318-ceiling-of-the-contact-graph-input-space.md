# TASK-0318 — Measure the ceiling of the contact-graph + seed input space before building any tenth observable

- Status: Done
- Assignee: Implementer D
- Priority: High — it is the gate on [[TASK-0147]]/[[TASK-0157]] and on the whole observable programme; cheaper than either build
- Filed: 2026-09-01 by Reviewer thread (id via `claim.py reserve-next`, after the TASK-0313 collision)
- Related: [[TASK-0140]], [[TASK-0147]], [[TASK-0157]], [[TASK-0301]], [[TASK-0308]], [[TASK-0310]], [[HYP-P9]], [[HYP-P14]]

## Why now

[[TASK-0310]] scored 7 runnable observables residualised on proximity.
**Nothing survives.** The lead candidate — chiral circulation, the one that
is proximity-orthogonal *by construction* (Helmholtz–Hodge: the gradient
component **is** the radial proximity flow and is subtracted off) and whose
ρ=0.365 is genuinely half CTQW's 0.735 exactly as predicted — went from raw
0.5560 to residual **0.4960, below chance.**

| observable | raw AUC | ρ(proximity) | residual AUC | cluster-p |
|---|---|---|---|---|
| persistent_h2_void | 0.5927 | 0.4894 | 0.5598 | 0.101 (n=45/108) |
| spectral_coherence | 0.6016 | 0.7004 | 0.5226 | 0.239 |
| transport | 0.5803 | 0.3864 | 0.5200 | 0.330 |
| chiral_circulation | 0.5560 | 0.3646 | **0.4960** | 0.799 |
| entanglement_entropy | 0.5934 | 0.8946 | 0.4903 | 0.623 |
| prs_low | 0.4532 | −0.1847 | 0.4680 | 0.185 |
| dcc_low | 0.4783 | 0.2887 | 0.4445 | 0.036 (negative) |

## The argument this task tests

**[[TASK-0301]]'s lesson, one level up.** The 61 rules failed as an ensemble
not because 61 was too few, but because all 61 were functions of the same two
inputs — *one signal at 61 settings*. **All nine observables are functionals
of the same input: the contact graph derived from Cα coordinates + B-factors,
plus the seed.** Nine observables on one Hamiltonian, one graph, one seed is
not nine independent chances.

What makes [[TASK-0310]] persuasive rather than anecdotal is that the seven
that ran are **wildly different mathematical objects** — persistent homology
(H2 voids), spectral coherence, transport conductance, Helmholtz–Hodge
circulation, entanglement entropy, low-mode PRS/DCC. Functional forms with
almost nothing in common, failing uniformly. **That pattern says the binding
constraint is the input, not the readout.**

This task measures that directly instead of inferring it from seven
anecdotes.

## The measurement

> Can **any** function of the contact graph + seed beat proximity, after
> residualising on proximity?

- [x] Assemble the full residue-level feature set already derivable in this
      repo from (coords, bfactors, seed): contact-graph descriptors, the
      `gnm_context` quantities, the five `potentials` terms, the existing
      observables' outputs. **Reuse, do not invent** — the point is to
      characterise the span of what we already have.
- [x] Fit a **flexible** model (gradient boosting or random forest — this is
      the one place a high-capacity model is the right tool, because the
      question is "what is achievable", not "what is interpretable").
- [x] Rank-residualise on proximity **and** score residualised, exactly as
      [[TASK-0310]] does. Report the achievable residual AUC on the
      108-structure ASBench cohort.
- [x] Report the same ceiling **without** residualising, as a sanity anchor
      against proximity's own 0.6147.

## What each outcome licenses — pre-registered

> **CORRECTED 2026-09-01 by the Reviewer thread that wrote this table.** The
> second row's licensing is **wrong**, and the error is mine, in the
> pre-registration itself — not in [[TASK-0318]]'s execution, which honoured
> the table as written. See "Correction to the outcome table" at the end of
> this file **before acting on the verdict.** Short version: a high ceiling
> **composed of existing features** is an argument *against* building
> [[TASK-0147]], not for it.


| ceiling (residual AUC) | consequence |
|---|---|
| **≈ 0.50** | **The whole observable class is closed**, with an argument rather than seven anecdotes. Do not build [[TASK-0147]] or [[TASK-0157]]; do not propose a tenth. The submission reports a measured limit of the representation, which is a stronger claim than any single negative. |
| **meaningfully > 0.50** | Something in the input *is* reachable and the observables were the wrong readout. **This is the only condition under which building the structured bath ([[TASK-0147]]) becomes rational** — and it should then be built against this ceiling as its target. |

## Constraints

- **LOPO by protein, always.** Five selection procedures in this register
  have died of pseudo-replication ([[TASK-0282]], [[TASK-0293]],
  [[TASK-0299]], [[TASK-0300]], and the [[TASK-0315]] positive-control
  surprise). A high-capacity model on 108 structures is the obvious sixth
  candidate — this constraint is not optional here.
- **Reuse [[TASK-0310]]'s validated harness.** It reproduced
  [[TASK-0308]]'s `ctqw_proximity_partial.json` to 4 decimals from scratch
  and residualised proximity against itself to **0.5000 exactly**. Do not
  write a second residualisation path.
- **Heed [[TASK-0315]]'s positive-control finding**: `euclid` residualised on
  `hop` alone did *not* land at 0.5 on the frozen 20 (0.61) — the two
  proximity measures are correlated but not redundant on heterogeneous
  cohorts. **Residualise on both jointly**, and re-run the self-check.
- A ceiling is an **upper bound, inflated by capacity**. Report it as such;
  it is only decisive in the *negative* direction (a low ceiling is
  conclusive, a high one is a lead, not a result).

## Recommendation this task exists to settle

**Do not build [[TASK-0157]] (two-boson HOM).** [[PANEL_REVIEW_2026-07-25]]
already declined it for a stated reason — "no reason to expect the
two-particle coincidence observable to be proximity-orthogonal" — which
[[TASK-0310]] has now confirmed seven times. For non-interacting bosons the
two-particle amplitudes are permanents of submatrices of **the same
single-particle propagator**: a nonlinear readout of an input with no
residual signal.

**[[TASK-0147]] (vibronic/structured bath) is the stronger of the two and is
the only one [[TASK-0310]] did not refute** — that task tested only
*unstructured* dephasing (n=11, raw 0.4306). The panel's §266 mechanism
argument still stands and correctly predicted [[TASK-0310]]'s results in
advance: unstructured dephasing can only push toward classical diffusion,
which *is* the proximity confound, whereas a structured bath is the only
proposed mechanism that could be site-selective rather than
distance-monotone. **But** the input it would be built from has since been
measured null four times — `dcc_low` (residual −11.1%, anti-predictive),
`prs_low` (−6.4%), `ground_state_relaxation` ([[TASK-0277]], p=0.954), ENM
mode shift ([[TASK-0303]], did not reproduce). The panel did not have those
in July. **Gate it on this task's ceiling.**

## Note

[[HYP-P14]]'s own decisive-test framing said a negative "closes the quantum
route with an argument, rather than leaving it open on an untested null."
That has now happened. "7 of 9 scored under a validated harness; the
remaining 2 were literature proposals a dated panel review explicitly
declined to build" is already honest and complete. This task's value is that
it upgrades *seven anecdotes* into *one measured limit*.

## Done (2026-09-01, Implementer D)

**Answer: ceiling is meaningfully > 0.50, not ≈ 0.50.** Per this task's own
pre-registered table, that licenses building [[TASK-0147]] against this
number as its target — but read the robustness check below before treating
it as settled; the task's own Constraint that a high ceiling is "a lead, not
a result" is honored, not waived, by what follows.

**Features, reused not invented**: `degree_centrality`, `hop_from_seed`,
`euclid_from_seed_centroid`, `gnm_context`'s `msf`/`degree`/`clust`, all five
`V_B`/`V_T`/`V_R`/`V_C`/`V_M` potential terms (sharing one `gnm_context`
eigendecomposition, TASK-0040's own dedup), CTQW occupation, and all 7 of
[[TASK-0310]]'s runnable observables called with its identical parameters —
19 columns, zero new descriptors.

**Harness validated twice before trusting the model**: (1) [[TASK-0310]]'s
own residualisation code reused verbatim, extended to a joint 2-column
design per [[TASK-0315]]'s own finding — self-check confirms `hop`/`euclid`
each residualised on **[hop, euclid] jointly** land at **exactly 0.5000**
(105/105 structures, not one exception). `euclid` residualised on `hop`
**alone** (univariate) lands at 0.5678 on this cohort — non-redundant here
too, though less dramatically than [[TASK-0315]]'s 0.61 on the frozen 20,
confirming (not assuming) the joint design was the right call to keep.
(2) CTQW cross-check: raw AUC 0.5850 (TASK-0310/0308's own 0.5921, close;
n=105 not 108 here, see failures below), residualised jointly 0.5091 — close
to TASK-0310's own hop-only 0.5184, and near-chance either way, exactly the
"CTQW does not survive" result this register already has, reproduced by an
independently-built pipeline.

**3 structures failed cleanly, not silently**: `1NJJ`/`2BXA`/`4CFE` all hit
an existing diagnostic (`operator_diagnostics`) correctly identifying a
disconnected contact graph at the 8 Å cutoff (independent rigid-body pieces,
TASK-0005's own named regression class) — a real structural property of
those PDB entries at this cutoff, not a script bug. **n=105/108**, disclosed.

**LOPO by protein, always, honored**: 93,183 pooled eligible residues over
105 structures / 74 distinct proteins, `HistGradientBoostingClassifier`,
74 folds, every reported number computed from out-of-fold predictions only.

**Headline**: RAW ceiling (sanity anchor against proximity's own 0.6147)
mean **0.6558**, median 0.7005. **RESIDUALISED ceiling (the decision
statistic): mean 0.5949, median 0.6203, Wilcoxon p = 3.3×10⁻⁶,
cluster-robust by protein (74 clusters, Monte Carlo) p = 1×10⁻⁵.** Both
comfortably clear this task's own "meaningfully > 0.50" bar, and clear it
with real statistical power, not a borderline call.

**The obvious objection, tested rather than waived**: the single most
important feature by permutation importance was `euclid_prox` itself
(+0.113, nearly 3× the next feature) — raising the real possibility that a
high-capacity model is simply reconstructing a *nonlinear* function of
proximity that a *linear* rank-residualisation cannot fully strip out. This
is exactly the capacity-inflation risk this task's own Constraint warns
about, so it was tested directly rather than reported past: **refit the
identical LOPO-by-protein model with `hop_prox` and `euclid_prox` REMOVED
from the feature set entirely** (17 columns, no proximity input of any
kind), then residualised the resulting out-of-fold score on both proximity
measures exactly as before.

**Result: the ceiling barely moves.** RAW (no proximity feature) mean
0.6487, median 0.6907. RESIDUALISED mean **0.6017**, median 0.6321,
Wilcoxon p = 2.3×10⁻⁷ — *higher*, not lower, than the with-proximity run.
**The model does not need to see proximity to reach the same ceiling.**
This substantially rules out the nonlinear-reconstruction concern: the
surviving signal is present in the non-proximity features themselves, not
manufactured from `hop`/`euclid` via a route the linear residualisation
missed.

**What is actually driving it, per permutation importance on the
proximity-excluded model (last LOPO fold, descriptive only)**:

| feature | importance |
|---|---|
| `V_C` (GNM dynamic cross-correlation) | **+0.135** |
| `chiral_circulation` | +0.053 |
| `persistent_h2_void` | +0.042 |
| `degree` | +0.032 |
| `spectral_coherence` | +0.022 |
| `V_B` | +0.021 |
| `prs_low` | +0.020 |
| `V_R` | +0.015 |

`V_C` dominates by a wide margin — worth flagging against [[TASK-0315]]'s
own finding that `V_C` **alone**, linearly, does not survive proximity
control on the frozen-20 cohort (residual p=0.31). Not a contradiction: a
high-capacity model combining `V_C` nonlinearly with `chiral_circulation`,
`persistent_h2_void`, and `degree` is a different, richer object than `V_C`
scored by itself, and this task's own cohort (ASBench, 105 structures) is
larger and different from TASK-0315's frozen 20. Recorded as the concrete
lead for whoever builds next, not chased further here (out of this task's
own verify-the-ceiling scope).

**Verdict, per this task's own pre-registered table, held to its own
calibration**: **meaningfully > 0.50, and this time backed by a targeted
robustness check the Constraint anticipated, not just the raw number.**
Building [[TASK-0147]] (structured-bath / vibronic resonance) is rational,
with two concrete, falsifiable targets now on record instead of one vague
one: (1) residual AUC ≈ 0.60 as the number to beat/reach, and (2) `V_C` and
`chiral_circulation` — both already implemented, both cheap — as the
specific existing quantities the structured-bath model should be checked
against before anything new is proposed on top. **[[TASK-0157]] (two-boson
HOM) recommendation is unaffected and stands**: this task's own filing
already argued it from the propagator-permanent structure, not from
[[TASK-0310]]'s empirical result alone, and nothing measured here bears on
that argument.

**Still honestly a lead, not a result**, per the Constraint's own explicit
warning that survives even a passed robustness check: this is an upper
bound from a high-capacity model's out-of-fold predictions, answering "is
there information", not "can we build a clean, interpretable, physically-
motivated observable that reaches it." That is exactly [[TASK-0147]]'s own
job, gated by this number, not pre-answered by it.

**Script**: `scripts/task0318_input_space_ceiling.py` (two phases: Phase A,
expensive, ~7066s / 118 min for the 19-feature build across 105 structures,
resumable per-structure `.npz` cache; Phase B, fast, ~118s LOPO fit,
independently re-runnable via `--phase-b-only` against the cached features).
The proximity-exclusion robustness check was run as a standalone follow-up
against the same cache (not re-paying Phase A), ~71s. **Data**:
`results/tasks/0318_input_space_ceiling/{ceiling_result.json,
no_proximity_feature_check.json}` (gitignored, not committed — every number
above traced to this Done section and `RESULTS.md`).


---

## Correction to the outcome table (2026-09-01, Reviewer thread)

**The execution of this task is not in question.** The proximity-excluded
refit is exactly the right robustness check and it is convincing — removing
`hop_prox`/`euclid_prox` entirely leaves the residualised ceiling essentially
unchanged (0.5949 → **0.6017**, *higher*), which substantially rules out the
nonlinear-reconstruction concern. The positive control (proximity residualised
on itself → **0.5000 exactly, 105/105**) is as clean as this register gets.

**What is wrong is the pre-registered licensing I wrote.** The table said
ceiling > 0.50 is *"the only condition under which building the structured
bath ([[TASK-0147]]) becomes rational."* That inference does not follow, and
this task's own permutation-importance result is what refutes it:

| feature | importance (proximity-excluded model) |
|---|---|
| `V_C` (GNM dynamic cross-correlation) | **+0.135** |
| `chiral_circulation` | +0.053 |
| `persistent_h2_void` | +0.042 |
| `degree` | +0.032 |

**Every one of these already exists.** A ceiling of 0.60 reached by a
gradient-boosted combination of features we already compute says the
information is **already in the current input space** — which licenses
*building a better readout of what we have*, not building a new physical
observable. The cheapest exploitation of this result is to fit that
combination directly. Building a structured-bath master equation to reach a
number that four existing features already reach is the **more** expensive
route to the same place, not the newly-justified one.

**Revised licensing:**

| ceiling (residual AUC) | consequence |
|---|---|
| ≈ 0.50 | observable class closed; do not build [[TASK-0147]]/[[TASK-0157]] *(unchanged)* |
| > 0.50, **composed of existing features** — **the measured case** | The information is reachable from what we already have. **Do not build [[TASK-0147]] or [[TASK-0157]].** Fit and validate the existing combination instead. |
| > 0.50, **and not attributable to existing features** | *would* justify a new observable — **this case did not occur** |

## Open item this task did not cover — the missing null control

The positive control is excellent; there is **no negative control**. A LOPO
gradient-boosting AUC of 0.5949 over 93,183 pooled residues needs a
**permuted-label null**: permute the truth labels *within* each structure,
refit the identical 74-fold LOPO pipeline, and confirm the residualised AUC
returns to ~0.50.

This is not pedantry here — [[TASK-0319]] documents that this register has
systematically run positive controls and omitted negative ones, and that the
omission has already invalidated one headline ([[TASK-0316]]). A
high-capacity model on 105 structures is exactly the shape of thing that
needs it.

- [x] Run the permuted-label null and report it beside the 0.5949.
- [x] Until then, treat the ceiling as **a lead, not a result** — which is
      what this task's own Constraint said, and which the revised table above
      now makes actionable.

**Net: the constructive finding stands and is the strongest in the register
right now** — individually no observable survives residualisation
([[TASK-0310]]), jointly they reach ~0.60. What changes is what it licenses:
exploit the combination, do not build a tenth observable.

## Addendum (2026-09-02, Implementer C) — the negative control, run

**Design, matching this task's own open item exactly**: permute the truth
labels *within* each structure (preserving each structure's own positive
count — a between-structure shuffle would additionally scramble class
balance, a second confound this control was not asking about), refit the
IDENTICAL 74-protein LOPO `HistGradientBoostingClassifier` pipeline (same
19 features, same `max_iter=150, max_depth=6, random_state=0`, same joint
`[hop, euclid]` residualisation), reusing this task's own cached Phase-A
features (`feature_cache/`, all 105 structures, unchanged) — no
re-fetching, no re-deriving any structure.

**Compute budget, disclosed**: one real (unpermuted) run costs ~19s once
`load_cache()` is warm (the committed Done section's own "~118s" figure
included the self-checks and permutation-importance overhead, stripped out
here since neither is needed per null replicate). [[TASK-0319]]'s own
≥200-rep bar is scoped to modality LRT false-positive rates specifically,
not adopted here as a blanket rule — **100 reps** run instead (~1900s,
~32 min), chosen for a decisive result within a reasonable wall-clock, not
because 200 was infeasible; every per-rep value is written to
`negative_control.json` so the p-value can be recomputed at a coarser or
finer resolution directly rather than trusted as a single summary number.

**Result — clean, and this time backed by a proper negative control, not
just the positive one**:

| | value |
|---|---|
| null residual-AUC-mean (100 reps) | **0.4993 ± 0.0110** (expect ~0.5000 under a true null — matches) |
| null raw (non-residualised) mean | 0.4997 ± 0.0109 |
| observed (real labels, committed) | **0.5949** |
| permutation p (one-sided, 100 reps) | **0.0099** — the floor at this rep count: **all 100 null reps landed below the observed value**, none came close |
| z-score (parametric, null's own mean/std) | **8.69** |

**The null centres almost exactly on 0.50** — the harness is correctly
calibrated, matching the already-clean positive control (proximity
residualised on itself → exactly 0.5000, 105/105) from this task's own
main run. The observed 0.5949 sits roughly **8.7 null-standard-deviations**
above the null mean, and the permutation p is at its 100-rep floor with
zero null replicates anywhere near the real value. **The ceiling is not a
harness artifact.**

**Verdict, upgraded per this task's own Constraint's own language**: the
input-space ceiling (~0.60 residualised, composed of `V_C`,
`chiral_circulation`, `persistent_h2_void`, `degree` — all pre-existing
features, per the correction above) now clears **both** controls this
register requires and can be read as **a result, not merely a lead**. The
revised licensing table's "measured case" row stands, now on firmer
ground: do not build [[TASK-0147]] or [[TASK-0157]]; fit and validate the
existing feature combination instead.

**Not done**: extending past 100 reps (the result is already at the
permutation floor and a parametric z=8.69 leaves no real ambiguity to
resolve); a negative control for the *proximity-excluded* refit
specifically (0.6017) — the same conclusion is expected to hold there too
by the same argument, not separately re-verified.

**Script**: `scripts/task0318_negative_control.py` (imports `load_cache`/
`resid_auc_joint`/`FEATURE_NAMES` from this task's own
`task0318_input_space_ceiling.py` verbatim — same task, not a cross-task
import). **Data**: `results/tasks/0318_input_space_ceiling/
negative_control.json` (gitignored, all 100 per-rep values retained).
