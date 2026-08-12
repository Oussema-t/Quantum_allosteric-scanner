# TASK-0211 An observable computed across an ensemble of graphs — is it a fourth axis, or axis #1 again?

## Context

- ID: TASK-0211
- Title: build a propagation observable over an **ensemble** of realized
  contact graphs (not one static graph) and test, first, whether it is
  independent of the ~3 axes [[TASK-0199]] measured.
- Status: Done
- **Thread: Architect/Planner (synthesis).** Re-analysis plus one cheap new
  observable; no compute window, does not compete with [[TASK-0208]]/
  [[TASK-0210]].
- Owner: Architect/Planner
- Claimed By: —
- Claimed At: —
- Source: Orchestrating user, 2026-08-06 — *"having a multitude of structures
  and their graphs… might provide a hypothetical mechanism for allosteric
  signal propagation — not just finding potential pockets."*
- Priority: **P1 — cheap, and it is the only identified route to escaping
  "the program tested three things."**
- Dependency: [[TASK-0199]] (the correlation matrix and its enumeration),
  [[TASK-0185]]/[[TASK-0187]] (ensemble generation, already built).

## Why this matters — the ~3 axes were measured on single-graph observables

[[TASK-0199]] found the register's 28 per-residue observables collapse to a
participation-ratio effective rank of **2.6–4.1**, stable across 5 targets
spanning N=169–704. Reading its own enumeration: **every one of those 28 is a
function of a single static contact graph.** Some encode fluctuation
structure through GNM/ANM modes, but all take one conformation as input.

**An observable computed across an ensemble of *realized* graphs is not in
that span.** Whether it is genuinely independent is directly testable — drop
it into the same correlation matrix and re-measure the effective rank. If the
rank moves from ~3 to ~4, the program has a genuinely new axis and the
"we tested three things" framing changes. If it lands inside the existing
span, the signal question is moot and the register saves the expensive
follow-up.

This also connects to the program's **one surviving positive**:
[[TASK-0201]]'s PTP1B `dcc_low` (k=10, p=0.0027). `dcc_low` is a *correlation*
quantity — the ensemble generalization is the same family done properly, and
if the new observable behaves like `dcc_low` on PTP1B specifically, that is a
mechanistic thread rather than a coincidence.

**What is already closed, so it is not repeated**: [[TASK-0187]] tested one
ensemble-graph observable — does ENM wobbling shorten the active-site↔pocket
hop distance *specifically* to the real pocket — and returned a clean
negative on PTP1B (real pocket shortcuts **less** than matched decoys,
effect −0.112, wrong sign). That closes hop-distance shortcuts. It does not
close contact co-variance, edge persistence, graph-reorganization spectra, or
ensemble-averaged propagation. The class is open; one member is dead, and the
dead one should not be rebuilt.

## Intent Contract

- Outcome: at least one ensemble-derived per-residue observable, its Spearman
  correlation against all 28 existing observables, and the re-measured
  effective rank with it included — plus a verdict on whether it is a new
  axis.
- Why required, not assumed: the register's headline structural finding is
  "~3 axes." Whether that is a property of the *method class* or only of the
  *single-graph* method class has never been distinguished, and the
  distinction is what decides whether there is anywhere left to look.
- In Scope:
  - Generate the ensemble with the **existing, legal** machinery: closed-form
    ANM equipartition Gaussian draws (`shortcuts.py`/[[TASK-0185]]'s
    prototype), no integrator, no trajectory — §Constraint 3 permits
    conformational sampling and forbids only MD trajectories as inputs.
    Reuse the MSF cross-check gate [[TASK-0187]] already established
    (empirical vs. analytic MSF, r ≥ 0.90) before trusting any ensemble.
  - Build ≥1 ensemble observable that is **not** a hop-distance shortcut.
    Candidates, in order of prior: per-residue **contact-persistence** (what
    fraction of the ensemble retains each edge); **contact co-variance**
    (which residue pairs' contacts co-vary — the direct ensemble analogue of
    `dcc_low`); ensemble-averaged propagation (run an existing propagator per
    frame and average the score, rather than propagating on one graph).
  - **Independence test first**: add to [[TASK-0199]]'s matrix, recompute
    participation-ratio and entropy rank, report the delta. Reuse
    `scripts/observable_effective_rank.py` and its controls unchanged.
  - Only if independent: state what a signal test would require, and hand it
    to a follow-up. Do **not** score it against labels in this task.
- Out Of Scope:
  - **Scoring against pocket labels.** This task measures observable-vs-
    observable structure only, so it consumes **zero** multiplicity budget —
    the same discipline [[TASK-0199]] held, and it must be stated in the
    write-up.
  - Rebuilding [[TASK-0187]]'s hop-shortcut observable.
  - Any plant/mechanism experiment ([[TASK-0168]]'s territory).
- Constraints And Invariants:
  - **Fix the observable definition before computing its correlations.** An
    ensemble observable tuned until it decorrelates is a manufactured axis.
  - Reuse [[TASK-0199]]'s controls verbatim: a duplicate column must not raise
    the rank, an orthogonal random column must raise it, N random columns must
    give near-full rank. A new observable that raises the rank is only
    interesting if those still behave.
  - Report the ensemble size and the MSF gate result. An under-sampled
    ensemble produces a noisy vector that will look independent for the
    wrong reason — this is the single most likely false positive here and
    must be controlled explicitly (e.g. split-half reproducibility of the
    observable itself).
- Planned Validation:
  - **Split-half**: compute the observable on two disjoint halves of the
    ensemble; they must correlate strongly with each other. If they do not,
    any apparent independence is sampling noise, not a new axis.
  - Reproduce [[TASK-0199]]'s published rank numbers on the unmodified 28
    before adding anything.
  - A pure-noise column of matched variance must not raise the rank the same
    way the real observable does — otherwise the "new axis" is noise.

## In Progress

**Pre-registration (2026-08-12, Architect, before any computation) —
observable definition, split-half bar, and "new axis" rule.**

**Observable chosen: `ensemble_contact_covariance`** (the Open Question's
own recommendation — direct analogue of `dcc_low`, and a null there is
informative rather than another dead observable). Defined to be
genuinely different in *kind* from `dcc_low`, not just a resample of it:
`dcc_low` is a closed-form projection of ONE Kirchhoff eigendecomposition
(a single static graph's normal modes); this observable is measured
empirically from many independently-**rebuilt, discrete** contact graphs
— edges genuinely appear/disappear per sample, a combinatorial quantity
no single-graph mode projection computes directly.

Construction, using only existing/legal machinery
(`shortcuts.equipartition_ensemble`, `hamiltonians.contact_matrix`):

1. Draw `n_samples` displaced coordinate sets via
   `equipartition_ensemble` (closed-form ANM Gaussian draws, no
   trajectory — same sampler [[TASK-0187]] already validated).
2. Gate: `msf_cross_check` must pass (Pearson r >= 0.90) before anything
   below is trusted, unchanged from [[TASK-0187]]'s own bar.
3. Per sample, rebuild the binary contact graph
   (`contact_matrix(coords0 + displacement_i, cutoff, weight="binary")`)
   and take each residue's **contact degree** (row sum) — a per-residue
   scalar that changes only when edges actually form/break, unlike a
   continuous displacement magnitude.
4. Seed time-series: `seed_series[sample] = mean_i(degree[sample, seed_i])`.
5. Per-residue score: `ensemble_contact_covariance[j] =
   |Pearson(seed_series, degree[:, j])|` across samples — magnitude only
   (`dcc_low`'s own convention: an anti-correlated partner is as much a
   communication partner as a co-moving one).

**Split-half reproducibility bar (Planned Validation, fixed before
running)**: split the ensemble into first-half/second-half (deterministic,
not reshuffled — reproducible across reruns), compute the score
separately on each half, Spearman-correlate the two per-residue score
vectors. **Pass bar: rho >= 0.70.** Lower than `msf_cross_check`'s 0.90
because this is a derived per-residue statistic over half the samples
(noisier by construction), but still "correlate strongly" per this
task's own Planned Validation wording. `n_samples` starts at 2000
([[TASK-0187]]'s own precedent) and is raised, per target, until this bar
passes or a compute-budget ceiling is hit (reported either way — this
task's own instruction is to report the requirement, not assume a round
number is enough).

**"New axis" rule (fixed before computing any rank delta)**: reuses
[[TASK-0199]]'s own established convention (direction + minimum
meaningful magnitude, not a fixed +1 — that task's own real-data finding
that the textbook +1 intuition does not hold on this project's
skewed spectrum). The real observable's participation-rank delta must
(a) exceed the matched-variance noise-column's own delta on the same
target, **and** (b) itself be `>= 0.10` (double [[TASK-0199]]'s own
`random_control_ok` bar of `>0.05`, since this is the bar for *interesting*,
not merely *nonzero*). Both conditions on **all evaluated targets**, not
a majority vote — a route that opens on one target and closes on the
rest is reported as exactly that, not averaged away.

Target set: [[TASK-0199]]'s own five (`TARGETS_PRIMARY` + `TARGETS_EXTRA`
from `observable_effective_rank.py`), for direct comparability against
its published baseline rank numbers (reproduced as a wiring check before
adding anything, per this task's own Planned Validation).

Implementing `scripts/task0211_ensemble_graph_observable.py`.

## TODO

- [x] Fix the observable definition(s) in this file. **Before computing.**
      See "In Progress" pre-registration above.
- [x] Generate ensembles; pass the MSF gate; record ensemble size. MSF gate
      passed on all 5 targets (r>=0.90); 2000 samples sufficed on 3/5,
      4000 needed on CARDIAC_MYOSIN/CASPASE7 (split-half bar).
- [x] Compute the observable; split-half reproducibility check. Passed on
      all 5 (rho 0.718-0.786) after the doubling.
- [x] Reproduce TASK-0199's baseline rank on the unmodified 28. Exact
      match on all 5 targets (KRAS_G12C 3.116, BCR_ABL1 2.621,
      CARDIAC_MYOSIN 3.249, PTP1B 2.609, CASPASE7 4.084).
- [x] Add the observable; recompute rank; report the delta. delta_real
      0.115-0.221 across the 5 targets — see Done table.
- [x] Noise-column control (matched variance) — must not mimic the effect.
      **It did**: delta_noise (0.180-0.273) exceeded delta_real on every
      target. Reported as the actual finding, not discarded.
- [x] Verdict: new axis or inside the existing span? **Inside the existing
      span, all 5/5 targets** — see Done.
- [x] If new: check its behaviour on PTP1B against [[TASK-0201]]'s
      `dcc_low` cell. **Not gated on "if new"** — computed for all 5
      targets regardless (cheap, already in hand): rho vs. `dcc_low` =
      0.257-0.339, modest positive everywhere, PTP1B not distinguished
      from the other 4. This is itself part of the explanation for why
      the observable isn't independent (see Done).

## Dependency

- [[TASK-0199]] (Done) — matrix, enumeration, controls, script.
- [[TASK-0185]]/[[TASK-0187]] (Done) — legal ensemble generation + MSF gate.
- [[TASK-0201]] (Done) — the `dcc_low` cell to compare against.
- Feeds [[TASK-0184]].

## Open Questions

- Which observable first? Recommendation: **contact co-variance**, because it
  is the direct ensemble analogue of `dcc_low` — the one quantity in this
  register that has ever survived a corrected null — so a null result there
  is informative rather than merely another dead observable.
- How large an ensemble? [[TASK-0187]] used 2000 samples for a hop statistic.
  A pairwise co-variance over N residues needs more; state the requirement
  from the split-half check rather than picking a round number.
- If the rank rises from ~3 to ~4, does that weaken [[TASK-0199]]'s headline?
  Slightly, and honestly — report it in that direction, as [[TASK-0199]] itself
  did when its result moved the multiplicity budget against the program.

## Done

**2026-08-12, Architect.** `scripts/task0211_ensemble_graph_observable.py`
(new). Ran on all 5 of [[TASK-0199]]'s own targets. Results:
`results_task0211_ensemble_graph_observable/results.json`.

### Per-target results

| Target | N | n_samples | split-half rho | rank (28) | rank (29) | delta_real | delta_noise | new axis? | rho vs `dcc_low` |
|---|---|---|---|---|---|---|---|---|---|
| KRAS_G12C | 169 | 2000 | 0.786 | 3.116 | 3.231 | 0.115 | 0.212 | **no** | 0.319 |
| BCR_ABL1 | 451 | 2000 | 0.718 | 2.621 | 2.739 | 0.118 | 0.181 | **no** | 0.305 |
| CARDIAC_MYOSIN | 704 | 4000 | 0.742 | 3.249 | 3.380 | 0.131 | 0.221 | **no** | 0.339 |
| PTP1B | 298 | 2000 | 0.719 | 2.609 | 2.751 | 0.142 | 0.180 | **no** | 0.257 |
| CASPASE7 | 461 | 4000 | 0.726 | 4.084 | 4.305 | 0.221 | 0.273 | **no** | 0.283 |

Baseline (28-observable) rank reproduces [[TASK-0199]]'s own published
numbers exactly on all 5 targets (wiring check). MSF gate passed
everywhere (r>=0.90); split-half reproducibility passed everywhere, at
2000 samples on 3/5 targets and 4000 on the other 2 (CARDIAC_MYOSIN,
CASPASE7 — the two largest, N=704/461, consistent with a larger residue
count needing more samples for a per-residue statistic to stabilize).
Duplicate/random controls on the 29-column matrix behaved correctly on
every target (duplicate does not raise rank, orthogonal random column
does) — the register's existing controls are not disturbed by adding
this column.

### Verdict: **inside the existing span, 5/5 targets — not a new axis**

`ensemble_contact_covariance` does move the rank up a little on every
target (+0.115 to +0.221) — it is not a duplicate or a null observable.
But the pre-registered rule requires the real observable's delta to
*exceed* a matched-variance noise column's own delta, and on **every
single target the noise column raised the rank more** (+0.180 to
+0.273). An observable that raises effective rank *less* than pure noise
does is, by construction, more correlated with the existing 28 than
random chance would be — the opposite of an independent axis.

**Why, and it is informative, not just a negative**: `rho` against
`dcc_low` alone is 0.257-0.339 on every target — modest, real, positive,
and essentially flat across targets (PTP1B is not distinguished from the
other 4, contrary to the Open Question's hope that a PTP1B-specific
echo of the register's one surviving positive might appear here). The
ensemble-realized-graph observable and the single-graph closed-form
`dcc_low` are measuring correlated but not identical things — both
respond to "how much a residue's local structural state co-varies with
the seed's," one through discrete contact-graph reorganization, the
other through continuous-mode projection. That overlap, replicated
across 5 targets, is consistent with them sharing real underlying
structure rather than being independent views, and is the direct
answer to why this observable lands inside [[TASK-0199]]'s existing
span rather than outside it.

### Answering the pre-registered Open Questions

- **Which observable first?** `ensemble_contact_covariance`, as
  recommended — and the result is informative precisely because it is
  the `dcc_low` analogue: a null here says something about the specific
  hypothesis (ensemble contact reorganization ≈ another view of
  low-mode collective communication), not just "one more failed
  observable."
- **How large an ensemble?** 2000 sufficed on 3/5 targets; the two
  largest needed 4000. No target needed the 8000 ceiling. Reported per
  target rather than picked as one round number, as instructed.
- **Does the rank rise from ~3 to ~4?** **No, on any target** —
  [[TASK-0199]]'s headline ("~3 axes," refined by [[TASK-0207]] to "~2
  stable, nameable axes plus noise") is unweakened by this result. This
  route does not reopen it.

### What this does and does not close

**Closes**: contact co-variance (the Open Question's own top
recommendation) as an independent axis, on all 5 targets, with controls
intact — a real, checked answer, not a shortcut left untested.
**Does not close**: edge persistence or ensemble-averaged propagation
(named In Scope as alternative candidates, not attempted — one member of
the class tested is enough to answer this task's own Intent Contract, but
does not exhaust it). [[TASK-0187]]'s hop-distance shortcut remains the
only other member of this class tested, also negative (wrong sign). Two
of at least four named candidates are now dead; edge persistence and
ensemble-averaged propagation are still open if this route is pursued
further — not filed as a new task here, since this task's own Outcome
(independence test on ≥1 observable) is satisfied and further candidates
are a new, separate compute window, not owed by this task's own scope.

### Not attempted

- Scoring against pocket labels — explicitly out of scope, zero
  multiplicity budget consumed, as required.
- Edge persistence, ensemble-averaged propagation (see above).
- [[TASK-0184]] hand-off write-up — this task's own finding (route
  tested, closed, "~3 axes" unweakened) is ready to feed it; not written
  here, per this task's own scope (measurement, not the downstream
  narrative document).
