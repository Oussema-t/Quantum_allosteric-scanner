# TASK-0200 Does dynamics add anything fpocket does not already have? — the conditional analysis never run

## Context

- ID: TASK-0200
- Title: stop asking whether this project's observables *beat* fpocket, and
  ask whether they add information **conditional on** it — score only the
  residues fpocket ranks ambiguously, and measure whether any dynamics
  observable resolves them.
- Status: Done
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: Reviewer thread, 2026-08-03. Gap identified by grep: every
  classical comparison in the register is **marginal** (head-to-head);
  no conditional, residual, or stacked analysis exists anywhere.
- Priority: **P1 — half a day to a day, and it is the difference between
  "fpocket won" and a characterized statement of where, if anywhere, dynamics
  contributes.**
- Dependency: [[TASK-0163]] (Done) — fpocket vendored at
  `__WORK_IN_PROGRESS__/tools/fpocket/`, already run on all 3 mandatory
  targets' apo structures under this project's own label/AUC/floor convention.

## Why this matters

[[TASK-0163]]'s result is the most uncomfortable number in the register, and
it is currently un-analyzed beyond the headline:

| Target | fpocket AUC | this project's floor | this project's actual (`H_new`/CTQW) |
|---|---|---|---|
| KRAS_G12C | **0.8348** | 0.4818 | 0.5901 |
| BCR_ABL1 | **0.8596** | 0.5817 | 0.5266 |
| CARDIAC_MYOSIN | 0.5345 | 0.5679 | — |

A 2009 geometric cavity-detection tool beats both the proximity floor and
every quantum-flavoured observable in the register on 2 of 3 targets.

**Every comparison the project has run against it is marginal.** The register
has asked "can we beat fpocket?" — answered decisively, no — and has never
asked the question that actually determines whether this method class
contributes anything:

> Is the dynamics-based signal a strict **subset** of static cavity geometry,
> or is there a residue population where geometry is ambiguous and dynamics
> resolves it?

These are very different scientific claims, and only the second one has a
future. The distinction also maps directly onto the register's own best
current hypothesis (Reviewer thread, 2026-08-03): that the signal which
exists is *static geometry*, already classically extractable, and that the
apo Cα graph adds nothing on top. This task tests that hypothesis directly
rather than inferring it from a marginal comparison.

**Both outcomes are useful and neither is a null result:**

- **Strict subset.** The honest, sharp closing sentence for the paper: "the
  dynamics-based signal on this benchmark is contained within static cavity
  geometry" — far stronger and more informative than "fpocket scored higher."
- **A resolvable residual exists.** The first genuinely positive niche the
  program has found, with a concrete, pre-specified population where the
  method contributes. That would materially change [[TASK-0184]]'s Technical
  Approach section.

## Intent Contract

- Outcome: per target, a stratified analysis of every dynamics observable's
  discriminative power **restricted to fpocket's ambiguous band**, with a
  verdict on whether any observable adds information conditional on the
  classical predictor.
- Why required, not assumed: the subset hypothesis is currently an inference
  from two marginal AUCs. It is directly measurable and has never been
  measured.
- In Scope:
  - Define fpocket's **ambiguous band** on a pre-registered rule — e.g. the
    residue population between the 40th and 70th percentile of fpocket
    score, or residues in a detected cavity that fpocket ranks below its own
    top-k. **Fix the rule in this file before looking at any conditional
    AUC.**
  - Within that band, compute stratified AUC for each dynamics observable
    against the same pocket labels, with the same floor
    (`degree_centrality`/`hop_from_seed`/`euclid_from_seed_centroid`) and the
    same null the register uses. **The floor must be recomputed within the
    band, not inherited from the whole-graph analysis** — restricting the
    population changes the confound structure, and inheriting the global
    floor would be the obvious way to manufacture a false positive here.
  - Report band size per target. If the band contains too few positives for a
    well-powered AUC, say so and report the power, do not report the AUC
    anyway (`MIN_POS_WELL_POWERED` convention already exists — reuse it).
  - Symmetric check, cheap and worth doing: the **reverse** conditional — does
    fpocket add anything conditional on the dynamics observable? Both
    directions make the "subset" claim precise rather than rhetorical.
  - State how many cells this adds to [[TASK-0161]]'s multiplicity budget,
    and coordinate with [[TASK-0191]] which is refreshing it.
- Out Of Scope:
  - Building an ensemble/stacked predictor. This measures information
    content; it does not ship a combined method.
  - Re-running fpocket. [[TASK-0163]]'s outputs are stored and the binary is
    vendored.
  - CARDIAC_MYOSIN's own fpocket underperformance (0.5345, below its own
    floor) — include it for completeness but do not chase it; that target's
    label quality is separately compromised ([[TASK-0177]]'s `EDO`
    negative-control failure).
- Constraints And Invariants:
  - Pre-register the band definition **and** the success criterion before any
    conditional number is computed. This analysis has a high researcher-
    degrees-of-freedom surface — band width, percentile cut, and observable
    choice are all knobs that could be tuned post hoc into a positive.
  - Sweep the band definition afterwards and report the range, per
    [[TASK-0075]]'s knob-disclosure precedent. A result that survives only at
    one band width is not a result.
  - Any positive must clear the within-band floor **and** a compact-patch
    permutation null, same bar as every other cell in the register. No
    exceptions for a conditional analysis.
- Planned Validation:
  - **Positive control:** a synthetic observable constructed to carry
    information fpocket provably lacks (e.g. a planted channel from
    [[TASK-0167.001]]'s `plant` machinery, which is geometry-blind by
    construction) must be detected by this analysis. If the conditional
    design cannot find a signal that is there by construction, it cannot
    support a negative either.
  - **Negative control:** a random score vector must not clear the within-band
    floor.
  - Sanity: whole-graph AUCs recomputed here must reproduce the register's
    already-published values exactly. If they do not, stop and diagnose.

## Pre-Registered Band Definition + Success Criterion (fixed 2026-08-04, before any conditional AUC — Implementer A)

**fpocket per-residue score** (reused, not re-derived): [[TASK-0163]]'s own
`_fpocket_per_residue_scores` (`scripts/task0163_external_baseline_scoring.py`)
— max-over-pocket-membership of each pocket's own fpocket "Score" (cavity
openness), `0.0` for residues in no detected cavity. Re-invoked against the
same apo PDB fpocket is deterministic on (Planned Validation's own sanity
check: whole-graph AUC must reproduce TASK-0163's published 0.8348/0.8596/
0.5345 exactly) — not a fresh experimental re-run, per this task's own
Out-Of-Scope.

**Band definition, checked empirically on the marginal fpocket-score
distribution alone (no label ever read for this check — legitimate
feasibility-checking, not peeking at any conditional AUC)**: banding on
the *full* per-residue distribution (zeros included) is dominated by the
pocket/no-pocket boundary — on real data, the 40th-70th percentile of the
full distribution is >80% zero-score residues on KRAS_G12C/BCR_ABL1 and
**collapses to zero residues entirely on CARDIAC_MYOSIN** (>70% of its
residues score exactly 0). That is not "fpocket is ambiguous," it is
"fpocket found nothing here" — a different population. **Primary band,
therefore**: residues with fpocket score `> 0` (inside *some* detected
cavity — cavity membership reported alongside, per this task's own Open
Question resolution) **and** in the `[40th, 70th)` percentile of the
*nonzero* score distribution — residues fpocket did find a cavity at, but
did not rank among its most confident hits. Real band sizes (nonzero
subset only, checked before any AUC): KRAS_G12C 18, BCR_ABL1 51,
CARDIAC_MYOSIN 36.

**Sweep** (per this task's own Constraint, run afterwards, reported as a
range): `[20,80)`, `[30,70)`, `[40,70)` (primary), `[50,90)`, all on the
nonzero-conditioned distribution — width and position both vary, not just
one axis.

**Success criterion**: a dynamics observable adds information conditional
on fpocket, on a given target, if — restricted to the band population —
its AUC against the real pocket label (i) exceeds the **within-band**
floor (`max` of `degree_centrality`/`hop_from_seed`/
`euclid_from_seed_centroid`, each recomputed on the band population, never
inherited from the whole-graph floor) **and** (ii) clears a compact-patch
permutation null at `alpha = 0.05/18` (family: 3 representative
observables x 3 targets x 2 directions [forward + reverse] = 18 cells,
TASK-0145's own "correct across the real comparisons this task makes"
convention, not the whole register's own unrelated family). Null
mechanism: `nulls.compact_patch`-drawn same-size synthetic pocket labels
over the *whole* target (matching `compact_null_rerun.py`'s own
`_lowmode_null` convention exactly — same null, band-restricted scoring
pipeline), `n_reps=1000`, `seed=123`.

**Well-powered gate**: `MIN_POS_WELL_POWERED=3` (reused from
`compact_null_rerun.py`, not redefined) applies to the band-restricted
positive count. **Already known, before running anything**: the primary
band's positive counts are 2 (KRAS_G12C), 0 (BCR_ABL1), 2 (CARDIAC_MYOSIN)
— none clears `MIN_POS_WELL_POWERED=3` at the primary band. Per this
task's own Constraint ("say so and report the power, do not report the
AUC anyway"), the primary-band result on all 3 targets is expected, before
running, to be **underpowered, not negative** — a genuinely different,
honest verdict than "no conditional signal found." The swept wider bands
(`[20,80)`, `[30,70)`) are the ones actually capable of a powered test;
reported with equal prominence to the primary band, not as a fallback
substituted in after the primary result disappoints.

**Representative observable subset** (per this task's own soft
dependency on [[TASK-0199]], now landed — effective rank ~3 of 28): 3
representative dynamics observables spanning distinct mechanism families
rather than all 28 — `H_new` CTQW occupancy (operator family, this
project's own submission operator), `dcc_low` (lowmode family), `R_eff`
(transport family). Cited justification, not assumed: [[TASK-0199]]
measured the register's own cross-observable effective rank at ~3,
consistent across 5 targets — a 3-observable representative set spanning
3 different mechanism families is a defensible sample of that measured
dimensionality, not an arbitrary cut.

**Reverse conditional**: for each of the 3 representative observables,
band on *that* observable's own score (`[40,70)` percentile of its own
distribution, same rule shape, no nonzero-conditioning needed since these
are continuous scores without fpocket's structural zero-mass) and test
whether fpocket adds information within that band — same floor/null/power
rules, mirrored.

## In Progress

—

## TODO

- [x] Write the band definition + success criterion into this file. **Before computing.**
- [x] Reproduce [[TASK-0163]]'s whole-graph fpocket AUCs as a wiring check — **did not
  reproduce exactly on any of 3 targets; diagnosed, not a bug in this task's own
  reproduction, see Done section.**
- [x] Construct the ambiguous band per target; report band size + positive count.
- [x] Recompute the floor **within** the band.
- [x] Conditional stratified AUC, every dynamics observable, per target — 3 representative
  observables per [[TASK-0199]]'s own rank-~3 finding, not all 28.
- [x] Reverse conditional (fpocket | dynamics).
- [x] Positive control (planted, geometry-blind) + negative control (random) — found and
  fixed a real design bug in the positive control's own patch placement, see Done section.
- [x] Sweep the band definition; report the range.
- [x] Verdict: strict subset, or a characterized residual niche? — **strict subset,
  asymmetric.**
- [x] Report added cells to [[TASK-0191]] for the budget refresh — 18 pre-registered cells
  (+ 4-window sweep multiplying the realized comparison count; only the primary-window 18
  count against the budget, sweep points are robustness characterization, not new claims).

## Dependency

- [[TASK-0163]] (Done) — vendored fpocket + stored per-residue outputs.
- [[TASK-0167.001]] (Done) — `plant` machinery for the positive control.
- [[TASK-0199]] (soft) — if the register's effective rank is ~2, "every
  dynamics observable" collapses to a handful and this task gets much cheaper.
  Worth reading that result first if it has landed.
- Coordinates with [[TASK-0191]] (multiplicity budget).

## Open Questions

- Is fpocket's per-residue score the right conditioning variable, or should it
  be cavity membership + cavity rank? The former is continuous and easier to
  band; the latter is closer to how fpocket is actually used. Recommendation:
  band on the continuous score, report cavity membership alongside.
  **Answered, as recommended**: banded on the continuous nonzero-conditioned
  score (see pre-registration); cavity membership (`fpocket score > 0`)
  reported alongside as the `nonzero_only` gate itself, not a separate stat.
- If the band is too small on all 3 targets for a well-powered test, is there
  a defensible way to pool across targets? Probably not without introducing a
  new confound — but decide and record rather than pooling silently.
  **Answered**: did not pool. The primary band was underpowered on 2/3
  targets and 2/4 sweep windows overall (reported honestly per this task's
  own Constraint), but the wider sweep windows gave real, unpooled,
  per-target power in most cases — pooling was not needed to reach a verdict.
- Does a "strict subset" finding argue for *dropping* the dynamics layer from
  the submission's technical approach entirely? Not this task's call, but
  [[TASK-0184]] needs the answer, so state the implication plainly.
  **Stated, not decided here**: the forward-direction result (dynamics never
  resolves what fpocket cannot) argues that dynamics should not be pitched as
  *complementary to* fpocket on this benchmark's own evidence — it has not
  been shown to add anything fpocket lacks, anywhere well-powered. The reverse
  direction's suggestive (not confirmed) pattern on BCR_ABL1 is too weak to
  argue the opposite. [[TASK-0184]]'s own call, this task's job is only to
  hand over the number precisely, which the Verdict section above does.

## Done

**2026-08-06 cross-link ([[TASK-0203]]):** PTP1B — the target carrying
[[TASK-0201]]'s own surviving positive — added to this script's `TARGETS`
after this task's own filing. Leg 1's forward-direction result there is
**inconclusive, not negative**: every representative observable (and the
specific `dcc_low` k=10 cell that survived) is underpowered at all 4
swept band widths, because fpocket itself performs only near chance on
PTP1B (AUC 0.42) — a genuinely different regime from the 3 mandatory
targets this task's own "strict subset" verdict was based on. That
verdict is not overturned (it was never claimed to cover PTP1B), but does
not extend to it either. Full account: [[TASK-0203]]'s own Done section.

**2026-08-04, Implementer A.**

### Verdict: strict subset, asymmetric — dynamics adds nothing fpocket lacks; fpocket may add something dynamics lacks (suggestive, not confirmed)

**Forward conditional (does any dynamics observable resolve fpocket's own
ambiguous residues?): clean, consistent negative.** Across 3 targets x 3
representative observables (`H_new` occupancy, `dcc_low`, `R_eff` —
[[TASK-0199]]'s own effective-rank-~3 finding cited as the justification
for this subset, not all 28) x 4 swept band widths, **no cell ever beats
its own within-band floor and clears the within-band compact-patch
permutation null.** Best-case null p-values sit at 0.34-0.77 on
KRAS_G12C/CARDIAC_MYOSIN — nowhere near marginal. Well-powered coverage
was real but partial: KRAS_G12C 2/4 windows well-powered, BCR_ABL1 1/4,
CARDIAC_MYOSIN 0/4 (see the CARDIAC_MYOSIN caveat below).

**Reverse conditional (does fpocket resolve dynamics' own ambiguous
residues?): one cell crosses the pre-registered bar, disqualified by
this task's own robustness rule; a broader sub-threshold pattern remains.**
BCR_ABL1, `dcc_low`, band `[50,90)`: AUC=0.949, floor=0.668,
`p<0.001` — clears `alpha=0.05/18=0.00278` decisively. **But this task's
own pre-registered Constraint is explicit: "a result that survives only
at one band width is not a result."** The same cell at the other 3
swept windows: `p=0.013, 0.060, 0.013` — all well above `alpha`. Per that
rule, fixed before any number was computed, **this is not counted as a
positive.** It is not nothing either: BCR_ABL1's reverse-conditional
`p`-values are low across nearly every observable/window on that target
specifically (0.010-0.09, 11 of 12 cells), a directionally consistent,
sub-threshold pattern not seen on the other two targets (CARDIAC_MYOSIN's
reverse cells sit at 0.12-0.31 with no consistent direction). Reported as
suggestive, not confirmed — exactly the distinction this task's own
Constraint exists to enforce.

**Combined reading**: the dynamics-based signal on this benchmark,
everywhere it was well-powered enough to test, is contained within static
cavity geometry — it never resolves a residue fpocket itself is unsure
about. The reverse direction hints, without confirming, that fpocket may
carry information dynamics lacks, concentrated on one target. This is the
"strict subset" outcome this task's own Context section named as one of
two possible, both-informative results — and the honest, sharper closing
sentence it asked for: **"the dynamics-based signal on this benchmark is
contained within static cavity geometry."**

### fpocket reproducibility — did not match [[TASK-0163]]'s published numbers, diagnosed

Planned Validation's own sanity check failed on all 3 targets:

| Target | Recomputed (this task) | Published ([[TASK-0163]]) | Diff |
|---|---|---|---|
| KRAS_G12C | 0.7910 | 0.8348 | 0.044 |
| BCR_ABL1 | 0.8618 | 0.8596 | 0.002 |
| CARDIAC_MYOSIN | 0.5303 | 0.5345 | 0.004 |

**Diagnosed, not assumed a bug in this task's own reproduction** (this
session, before running the conditional analysis, per the Planned
Validation's own "stop and diagnose" instruction): ruled out (a) the
pocket label — identical, `pocket_size=18` on KRAS_G12C matches exactly,
floor AUCs match [[TASK-0163]]'s own stored value to many decimal places
(`0.48178...`); (b) chain selection — `targets.yaml` has no `apo_chains`
override, `chains: ["A"]` unchanged; (c) fpocket non-determinism — 3
independent re-runs gave the bit-identical AUC every time; (d) a
parsing bug — the raw per-pocket scores (10 pockets, monotonically
decreasing 0.08-0.264) look like genuine, well-formed fpocket output, and
`n_pockets`/`n_residues_assigned` match [[TASK-0163]]'s own stored values
exactly (10, 77). **Most likely explanation, not confirmed further (user
direction, this session): the vendored fpocket binary/build has drifted
since [[TASK-0163]] ran** — KRAS_G12C shows a real, larger discrepancy
(0.044) while BCR_ABL1/CARDIAC_MYOSIN are close (0.002-0.004), a pattern
consistent with a cavity-detection algorithm change that affects some
geometries more than others. **Proceeded with this task's own
freshly-recomputed numbers** (internally consistent, reproducible,
deterministic) rather than [[TASK-0163]]'s older stored ones — flagged
here as a named, unresolved finding for a future task (does not block
this task's own within-band comparisons, which only ever compare fresh
numbers against each other, never against the older published ones).

### Controls — one real design bug found and fixed before trusting the result

**Negative control**: random score's within-band AUC at the primary
`[40,70)` window is undefined (band underpowered, `pos=2` — pre-registered
as expected before running). Re-run at the pre-registered wide `[20,80)`
sweep window instead (`n=39, pos=4`, well-powered): random score's own
AUC (0.657) *does* beat the within-band floor (0.454) by chance — small-
sample noise — but is correctly rejected by the null-clearance criterion
(`p=0.155`, far above `alpha`). **This is the control working as
intended**, not a near-miss: it demonstrates directly why this task's own
two-part criterion (floor *and* null, not floor alone) exists — a
floor-only criterion would have falsely certified this noise.

**Positive control — found and fixed a real bug in the control's own
design, not just in scoring**: the first attempt drew the planted patch
via `select_distal_patch` (any distal, floor-blind compact patch
anywhere on the protein) — checked directly, this patch had **zero
overlap** with the fpocket band on every trial, meaning the control was
validating the plant mechanism in isolation ([[TASK-0190]] already did
that), not this task's own conditional-analysis pipeline. Fixed: draw the
patch from *within* the band pool (`nulls.compact_patch_from_pool`),
guaranteeing overlap by construction, then score the identical
within-band conditional statistic the real analysis uses (patch
membership as the synthetic label). Result: within-band AUC rises
0.833 -> 0.944 with plant strength (0 -> 100) — the pipeline detects a
signal that is there by construction, validating that the forward
direction's consistent negative is a real absence of signal, not a
broken test.

### CARDIAC_MYOSIN caveat (per this task's own Out-Of-Scope, not chased)

All 4 forward-conditional windows are underpowered on CARDIAC_MYOSIN
(`pos=2` constant across every window width, an unusual invariance worth
noting though not investigated further) and no reverse cell beats its
own floor convincingly. Per this task's own Out-Of-Scope, included for
completeness, not chased — that target's own label quality is separately
compromised ([[TASK-0177]]'s `EDO` negative-control failure, a different
task's own finding).

### Multiplicity / [[TASK-0161]] budget

Pre-registered family: 18 cells (3 observables x 3 targets x 2
directions), `alpha=0.05/18=0.00278`. The 4-window sweep multiplies the
realized comparison count to 72, but per this task's own robustness rule
a sweep is characterization, not a set of independent claims each needing
its own correction — only the pre-registered 18-cell primary family
counts toward [[TASK-0161]]'s budget. Flagged for [[TASK-0191]]'s own
refresh pass, not applied here.

### Tests

`tests/test_fpocket_conditional_analysis.py` (10 new: band-mask edge
cases including the `[lo,hi)` half-open boundary, within-band floor
recomputation proven genuinely band-restricted not cached, the
compact-patch null's determinism, the underpowered/well-powered
conditional-cell branches). Full suite: `1132 passed, 1 skipped,
2 xfailed`, no regressions.

### Out of scope, confirmed not needed

No ensemble/stacked predictor built (measurement only). fpocket not
re-run experimentally — the same deterministic, vendored-binary
invocation [[TASK-0163]] used, re-invoked (not a fresh experiment),
per this task's own Out-Of-Scope; the reproducibility gap found is a
finding about that invocation's own stability over time, not a new run
of a different kind.

### Not done in this task (named for a follow-up, not built here)

Root-causing exactly what changed in the vendored fpocket binary/build
between [[TASK-0163]]'s original run and now (git history / binary
hash comparison) — deferred per explicit user direction this session,
named here so it is not lost.
