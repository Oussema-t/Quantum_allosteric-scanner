# TASK-0207 Name the ~3 axes — turn an effective-rank statistic into a mechanistic statement

## Context

- ID: TASK-0207
- Title: label [[TASK-0199]]'s ~3 principal components by which observable
  families load on them, and check the labelling against [[TASK-0168]]'s
  independently-measured mechanism assignment.
- Status: Done
- **Thread: Architect/Planner (synthesis / narrative).** Pure re-analysis of
  stored artifacts — no compute window needed, no target runs, does not
  compete with [[TASK-0203]]/[[TASK-0204]] for machine time.
- Owner: Architect/Planner
- Claimed By: —
- Claimed At: —
- Source: Reviewer thread, 2026-08-05, following the user's own question
  ("was it one hypothesis from 40 angles, or multiple hypotheses?").
- Priority: **P1 — cheap, and it converts the register's single best headline
  number from a statistic into a scientific claim.**
- Dependency: [[TASK-0199]] (Done — stored correlation matrices and
  eigen-decompositions), [[TASK-0168]] (Done — the independent mechanism
  assignment to check against).

## Why this matters

[[TASK-0199]] measured that 28 observables collapse to an effective rank of
**2.6–4.1**, stable across 5 targets spanning N=169–704. That is the
program's sharpest single finding and its most quotable sentence.

But "~3" is currently a bare number. **Nobody has asked what the three
*are*** — and the answer is already latent in data that has been computed and
stored.

There is a strong prior, assembled from three independent results, and it has
never been checked:

| Axis (hypothesized) | Evidence it exists | Status |
|---|---|---|
| **Proximity** | `-hop_from_seed` loads at/above the median of all 28 observables on PC1 ([[TASK-0199]]); bare Laplacian correlates ρ=+0.83 with distance-from-seed at any propagation time (`REVIEW-panel-2026-07-16-v2`) | inferred, never confirmed as *the* PC1 |
| **Directed channel / transport** | `T(E=0)`/`ctqw_converged` rise with channel-plant strength, flat-to-falling with mode-plant strength, **replicated 2/2 targets** ([[TASK-0168]]) | mechanism confirmed, PC identity unknown |
| **Ensemble / mode** | `dcc_low_from_L` shows the opposite (mode-specific) signature on KRAS_G12C ([[TASK-0168]]); `dcc_low` carries the program's only surviving positive ([[TASK-0201]]) | mechanism unreplicated, PC identity unknown |

If the loadings confirm this mapping, the program can say something far
stronger than "we tested one thing forty times":

> *We tested three things — proximity, directed transport, and ensemble mode
> structure — thoroughly and from many angles. Two of them are mechanistically
> distinguishable at protein scale. One of them is largely the confound.*

That is a structural characterization of the entire method class, and it is
the sentence that makes the negative result interesting rather than merely
rigorous. If the loadings *don't* confirm it, that is equally worth knowing
before [[TASK-0184]] commits to the framing.

## Intent Contract

- Outcome: for each target, the top-3 principal components' loading profiles,
  each labelled by the observable family that dominates it, plus an explicit
  comparison against [[TASK-0168]]'s channel/ensemble assignment and against
  `-hop`/`-euclid`'s own projections.
- Why required, not assumed: the three-axis reading is currently an inference
  the Reviewer thread drew across three task files. It is directly checkable
  from stored data and should not enter the submission as an inference.
- In Scope:
  - Load [[TASK-0199]]'s stored per-target correlation matrices and
    eigen-decompositions. **Recompute nothing scientific** — if a matrix is
    missing, re-run `scripts/observable_effective_rank.py`, which is ~33s for
    all 5 targets.
  - Per target: top-3 PC loading vectors, each observable's loading, sorted.
  - **Label each PC** by which observable family dominates it (channel:
    `T(E=0)`/`ctqw_converged`/`R_eff`/GSR; ensemble: `dcc_low`/`prs_low`/
    `CP_low`/conformational entropy; the Hamiltonian-operator occupancy
    family; the remainder). Report the labelling rule used.
  - Project `-hop_from_seed`/`-euclid_from_seed_centroid` onto all three and
    report which axis they are. [[TASK-0199]] reported `-hop`'s PC1 loading
    percentile but not *which* PC it most resembles.
  - **Cross-target stability**: is it the same three axes on every target, or
    does the decomposition reorder? An effective rank that is stable at ~3
    while the *content* of the three changes per target is a materially
    different (and weaker) finding, and would need saying.
  - Explicit agreement/disagreement table vs. [[TASK-0168]]'s mechanism
    assignment.
- Out Of Scope:
  - Re-running any observable against any label. Same as [[TASK-0199]]: this
    consumes **zero** multiplicity budget and touches no answer key. State it.
  - Dropping, merging, or re-weighting observables in the register.
  - Any new plant or mechanism experiment — that is [[TASK-0203]].
- Constraints And Invariants:
  - **Fix the family-assignment rule before looking at loadings.** Assigning
    observables to families after seeing which ones cluster is circular and
    would manufacture the hypothesized answer.
  - PC sign is arbitrary — fix a sign convention (e.g. force the largest-
    magnitude loading positive) and state it, or the cross-target comparison
    is meaningless.
  - If the mapping does **not** come out as three clean families, report the
    messy answer. A muddled decomposition is a real finding about the
    register's structure and is more useful than a forced narrative.
- Planned Validation:
  - Reconstruct [[TASK-0199]]'s published participation-ratio numbers from the
    loaded eigen-spectra as a wiring check before interpreting anything.
  - Sanity: PC1's loading profile should be broadly positive across most
    observables if it is a shared/common axis. If PC1 is instead dominated by
    one or two observables, the "common axis" reading is wrong and the
    write-up must say so.
  - Cross-check one target's labelling by hand against its own raw correlation
    matrix — do the observables the PC says cluster actually correlate
    pairwise?

## In Progress

**2026-08-05 (Architect) — family-assignment rule + PC sign convention,
fixed before computing or looking at any PC loadings, per this task's own
Constraint.**

**Data check first**: `results_task0199_observable_rank/observable_
effective_rank.json` stores the 28x28 real-observable correlation matrix
and its eigen*values* per target, plus PC1's loadings on the 30-column
extended (28 real + `neg_hop` + `neg_euclid`) matrix — but not PC1's
eigen*vectors* for the 28x28 matrix, nor PC2/PC3 for either matrix. Not
enough to label 3 axes. Per this task's own allowance ("recompute nothing
scientific... re-run `observable_effective_rank.py` if a matrix is
missing"), a new script imports that module's own
`_prepare_target`/`compute_all_observables`/`align_and_stack`/
`correlation_matrix_and_rank`/`confound_projection` functions directly
(reused, not re-derived) and additionally captures full eigenvectors for
the top-3 PCs of both matrices. The 28x28-real-only decomposition is the
primary object labelled below (it is not contaminated by `hop`/`euclid`
already being columns in it); the 30x30 extended matrix is used only to
locate which axis `hop`/`euclid` land closest to, matching TASK-0199's
own established method for that projection, not a new one.

**Family-assignment rule (4 buckets, fixed from the observable list and
TASK-0168's independent findings, not from any loading seen yet):**

| Family | Members | Basis |
|---|---|---|
| **Channel/transport** | `R_eff`, `T_E0_on_L`, `T_E0_on_Hnew`, `transfer_entropy` | Explicit directed-flow/transmission quantities on a fixed operator (`L` or `H_new`) — matches [[TASK-0168]]'s empirically-confirmed "channel family" (`T(E=0)`/`ctqw_converged`/GSR cluster pre-plant, rho 0.5-0.9, all rise with channel-plant strength). |
| **Ensemble/mode** | `dcc_low`, `prs_low`, `mode_coparticipation`, `conformational_entropy` | Low-mode/normal-mode-ensemble quantities, matches this task's own In-Scope wording ("`dcc_low`/`prs_low`/`CP_low`/conformational entropy"). **Flagged before running**: [[TASK-0168]] found `dcc_low` does not replicate its mode-response across both its targets and `prs_low` is "the one genuinely non-redundant observable in the full named set" (rho −0.32 to 0.12 with everything else) — this bucket may not load together at all, and that would itself be a real, reportable finding, not a labelling failure. |
| **Hamiltonian-operator CTQW occupancy** | `occ_H1`…`occ_H14` (minus H13), `occ_H_new`, `occ_build_H10` (15 columns) | All `time_averaged_ctqw_converged` occupancy on different operator constructions. **Deliberately kept separate from Channel/transport above**, despite both being CTQW-propagation-flavored: lumping 15 highly similar columns into "channel" a priori would presuppose the answer to exactly what this task is measuring (are they the same axis as `R_eff`/`T(E=0)`, or their own). |
| **Remainder** | `chiral_circulation`, `coupling_specificity`, `entanglement_entropy`, `spectral_coherence`, `void_score` | Mechanistically heterogeneous, no shared basis with the above three. |

**Per-PC family score**: mean absolute loading within each family (not
sum) — the 15-member occupancy family would mechanically dominate a
sum-based score purely by column count; mean is fair across the
4-15-member size imbalance. Stated as a real methodological choice, not
hidden.

**PC sign convention**: for each PC's eigenvector, if the loading with
the largest absolute value is negative, flip the sign of the whole
vector. Makes cross-target sign comparison meaningful; otherwise
arbitrary.

**Family-assignment rule for `hop`/`euclid`**: not part of any family
above (external confounds being tested, not register observables) —
reported by which PC they land nearest, never absorbed into a family
score.

## TODO

- [x] Fix the family-assignment rule + PC sign convention in this file. **Before looking at loadings.**
- [x] Load/recompute TASK-0199's matrices; reproduce its published rank numbers
      — `wiring_ok=True` (rank match + PC1-loading match, both to 1e-6) on
      all 5 targets, confirmed before interpreting anything.
- [x] Top-3 PC loading profiles per target.
- [x] Label each PC by dominant family under the fixed rule.
- [x] Project `-hop`/`-euclid`; identify which axis is the confound —
      PC1 in 7/10 (target, confound) pairs, PC2 in 2/10 (PTP1B-hop,
      CASPASE7-hop), PC3 in 1/10 (CASPASE7-euclid).
- [x] Cross-target stability check — **PC1 stable on all 5, PC2 stable on
      4/5, PC3 genuinely unstable (3 different labels across 5 targets)**.
- [x] Agreement table vs. [[TASK-0168]]'s mechanism assignment.
- [x] Hand-verify one target's labelling against its raw correlation
      matrix — KRAS_G12C: `occ_H1`/`occ_H6` (both top-PC1) rho=0.73,
      `occ_H1`/`R_eff` rho=0.80, `occ_H1`/`entanglement_entropy` rho=0.85
      — confirms PC1 is a real shared cluster, not a PCA artifact.
      `prs_low`/`conformational_entropy` (both top-PC2) rho=0.74;
      `prs_low`/`dcc_low` (same nominal family, `dcc_low` has low PC2
      loading) rho=**−0.11** — confirms PC2 is `prs_low`-driven, not a
      uniform "ensemble family" cluster, consistent with [[TASK-0168]]'s
      own finding that `dcc_low`/`prs_low` are not redundant with each
      other.
- [x] Write the verdict sentence for [[TASK-0184]], quotable as-is.

## Dependency

- [[TASK-0199]] (Done) — the decomposition being labelled.
- [[TASK-0168]] (Done) — the independent mechanism assignment to check against.
- [[TASK-0203]] — will add PTP1B mechanism data; this task can run before it
  and should be re-read after, not blocked on it.
- Feeds [[TASK-0184]].

## Open Questions

- Three PCs or however many the 90%-variance threshold gives (8–11 per
  [[TASK-0199]])? Recommendation: label the top 3 as the headline (matching
  the participation-ratio finding), report where the next few sit, and be
  explicit that the tail is real but small.
- If PC identity reorders across targets, does the "~3 axes" sentence survive?
  Probably as "~3 axes per target, not necessarily the same three" — weaker,
  still interesting, and it must be said if true.

## Done

**2026-08-06, Architect.** `scripts/label_principal_components.py` (new,
reuses `observable_effective_rank.py`'s own already-tested pipeline
functions directly, adds only eigenvector capture on top — no observable
recomputed differently). Real run, all 5 targets, wiring-checked against
[[TASK-0199]]'s own stored numbers before interpreting anything (exact
match, both the participation-ratio rank and the extended-matrix PC1
loadings, to 1e-6, on every target). Full output:
`results_task0207_pc_labels/pc_labels.json`.

### Headline: the pre-hypothesis was half right — refined, not confirmed as-is

| Target | PC1 (var%) | PC2 (var%) | PC3 (var%) | hop → | euclid → |
|---|---|---|---|---|---|
| KRAS_G12C | occupancy (54.9%) | ensemble (8.4%) | remainder (7.2%) | PC1 | PC1 |
| BCR_ABL1 | occupancy (60.2%) | ensemble (10.5%) | ensemble (5.6%) | PC1 | PC1 |
| CARDIAC_MYOSIN | occupancy (53.7%) | ensemble (9.5%) | channel (5.2%) | PC1 | PC1 |
| PTP1B | occupancy (60.6%) | ensemble (7.9%) | channel (5.8%) | PC2 | PC1 |
| CASPASE7 | occupancy (46.5%) | channel (11.2%) | ensemble (7.7%) | PC2 | PC3 |

**PC1 is not "proximity" as a distinct label — it is the 15-member
Hamiltonian-occupancy family, and proximity (`hop`/`euclid`) rides on the
same axis** (lands there in 7/10 target×confound pairs). Sanity-checked,
not assumed: PC1's top loadings are broadly shared (7-8 observables all
in the 0.21-0.24 range on KRAS_G12C, not 1-2 dominant ones), and hand-
verified directly against the raw correlation matrix (`occ_H1`/`occ_H6`
rho=0.73, `occ_H1`/`R_eff` rho=0.80, `occ_H1`/`entanglement_entropy`
rho=0.85 — a real cluster, not a PCA artifact). **This single axis alone
carries 46.5-60.6% of total variance on every target** — by far the
dominant driver of the whole "effective rank ~3" finding.

**PC2 is `ensemble_mode`-labelled on 4/5 targets, but within that family
it is driven by `prs_low`/`conformational_entropy`, not `dcc_low`** —
hand-checked: `prs_low`/`conformational_entropy` rho=0.74 (both top-PC2),
`prs_low`/`dcc_low` rho=**−0.11** (`dcc_low` has low PC2 loading despite
nominal family membership). This is not a labelling error — it is a
direct, independent confirmation of [[TASK-0168]]'s own finding
("`prs_low` is the one genuinely non-redundant observable in the full
named set," rho −0.32 to 0.12 with everything else): two unrelated
methods (static cross-observable PCA here; dynamic plant-response there)
agree that `prs_low` does not cluster with `dcc_low`.

**PC3 does not survive as a stable axis** — three different dominant
families across 5 targets (`remainder`, `ensemble_mode` ×2,
`channel_transport` ×2), no majority pattern. The Open Question's own
anticipated fallback ("~3 axes per target, not necessarily the same
three") is correct for PC3 specifically, not for PC1/PC2, which are both
stable.

**`channel_transport` (the pre-hypothesized second axis) does not emerge
as a stable, major component anywhere** — it only reaches PC2 on
CASPASE7 and PC3 on 2/5 targets (5.2-11.2% variance), never PC1. This
directly qualifies the pre-registered hypothesis table's "Directed
channel / transport" row: [[TASK-0168]] confirmed it is a real,
mechanism-specific *response* to active perturbation (plant-strength
manipulation) — but in unperturbed, static observation it is not a major
source of cross-observable variance. A real, if less dramatic,
distinction: **a mechanism can be distinguishable under intervention
without being a dominant axis of passive correlational structure.**
Within that family, `occ_H_new` (=`ctqw_converged`) loads substantially
on PC1 (0.212, near the top-8 range) while `T_E0_on_Hnew` loads almost
not at all (0.012) — [[TASK-0168]]'s own "channel trio" (`T(E=0)`/
`ctqw_converged`/GSR) does not behave as a single unit in the static
data either, only two of the three tested quantities are even present in
this task's 28-observable enumeration (no GSR).

### Agreement table vs. [[TASK-0168]]

| [[TASK-0168]] finding (dynamic, plant-response) | This task's finding (static, unperturbed PCA) | Read |
|---|---|---|
| Channel family (`T(E=0)`/`ctqw_converged`/GSR) clusters pre-plant, rho 0.5-0.9 | `occ_H_new` (`ctqw_converged`) loads on PC1 (0.21) alongside the occupancy family; `T_E0_on_Hnew` does not (0.01) | **Partial agreement** — pre-plant clustering is real for one of the two available quantities, not the other |
| `dcc_low` mode-response replicates on KRAS_G12C only, not BCR_ABL1 | `dcc_low` has low PC2 loading on every target (PC2 is `prs_low`-driven) | **Consistent** — `dcc_low` was never a strong, uniform contributor to the "ensemble" axis in the static data either |
| `prs_low` "genuinely non-redundant," rho −0.32 to 0.12 with everything | `prs_low` dominates PC2 alone, anti-correlated with `dcc_low` (rho −0.11) | **Independently confirmed**, two unrelated methods |
| Channel family is a real, replicated (2/2 targets) mechanism under active plant | Channel-family observables are a minor, unstable axis (PC2/PC3 only, 5-11% var) in passive data | **Not a contradiction** — mechanism-under-intervention and dominant-static-variance are different properties; this task is the first to name that they diverge here |

### Verdict sentence (for [[TASK-0184]]'s narrative, quotable as-is)

*"The register's dominant shared axis (PC1, 46.5-60.6% of cross-observable
variance on every target) is the 15-member Hamiltonian-occupancy family,
not a cleanly separate 'proximity' label — `-hop`/`-euclid` load on this
same axis in 7 of 10 target-confound pairs, confirming it is
substantially the seed-proximity confound. A second, more modest axis
(PC2, 7.9-10.5% of variance, stable on 4 of 5 targets) is driven
specifically by `prs_low`, not the ensemble/mode family as a whole —
independently corroborating a finding from an unrelated method
([[TASK-0168]]'s plant-response experiment) that `prs_low` is the
register's one genuinely non-redundant observable. A third axis does not
survive across targets: no stable family dominates PC3. The
pre-registered hypothesis that a distinguishable 'directed channel'
axis would appear as a major, stable component is not confirmed — that
mechanism is real under active perturbation ([[TASK-0168]]) but does not
show up as a dominant source of variance in unperturbed, static
observation, a genuine and reportable distinction between a mechanism's
detectability under intervention and its footprint in passive data. The
honest three-axis reading is: one large, dominant confound-adjacent
axis; one modest, `prs_low`-specific axis, cross-validated against an
independent method; and no third stable axis — a more precise, and more
defensible, characterization than 'three mechanistically distinguishable
axes.'"*

### Not attempted, per this task's own Out of Scope

Re-running any observable against any answer key (this task, like
[[TASK-0199]], consumes zero multiplicity budget and touches no label —
stated explicitly). Dropping, merging, or re-weighting any register
observable. Any new plant/mechanism experiment (that is [[TASK-0203]]'s
territory, still in progress at the time of this task — per this task's
own Dependency note, flagged for re-reading once that lands, not blocked
on it).

### `RESULTS.md`/`COMPETENCE_MAP.md`

New dated `RESULTS.md` section (this task's own name) plus an
open-questions row, both appended. `COMPETENCE_MAP.md`'s document-level
caveat block ([[TASK-0205]]'s own 2026-08-05 entry, which cited
[[TASK-0199]]'s bare "~3" number) gets a short dated follow-up pointing
to this task's refinement, per the [[TASK-0205]]-adopted standing rule —
this task does not change any per-target floor/actual/verdict number, so
the rule's letter (per-target verdict changes) does not strictly require
an edit there, but the spirit (this document should not carry a number
this task has since refined) does.
