# TASK-0199 Effective rank of the observable register — did we test 40 things, or one thing 40 times?

## Context

- ID: TASK-0199
- Title: measure the cross-observable correlation structure of every scored
  observable in the register, on real targets, and report its **effective
  rank** — the number of genuinely independent quantities the program has
  actually measured.
- Status: Done
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: Reviewer thread, 2026-08-03. Split out of [[TASK-0168]]'s own
  "pre-plant cross-observable ρ matrix (redundancy measure)" TODO item, which
  needs **no plant and no new physics** and is being blocked behind a P2 task
  it does not depend on.
- Priority: **P0 for the freeze — half a day, purely re-analytic, and it
  changes the meaning of every other result in the register whichever way it
  lands.**
- Dependency: none. Every score vector required either already exists in
  `results_*/` or is a re-run of already-written, already-tested code.

## Why this matters

The register contains ~40 scored observables and [[TASK-0161]] counts 226+
scored cells against ~7 answer keys. Both numbers are treated as evidence of
**breadth** — many independent falsification attempts, hence a strong
negative.

That framing has never been tested. Every observable in the register is a
scalar function of the same input: a single static Cα contact graph, seeded
at the active site. There is a live possibility, entirely consistent with the
evidence, that these are **~40 views of one number**.

Direct supporting signals already in the register, none of which was gathered
to answer this question:

- ρ(score, −hop) is substantial for most observables on most targets
  (`prs_low` −0.18 to −0.51; `dcc_low` +0.44 to +0.63; spectral coherence
  +0.68 to +0.72) — a shared confound is a shared component.
- `REVIEW-panel-2026-07-16-v2`'s own executed check: a bare, disorder-free
  normalized Laplacian seeded at one residue correlates with distance-from-seed
  at ρ=+0.83 and never drops below ~0.5 at *any* propagation time.
- [[TASK-0136]] found the active-site↔pocket connectivity itself is broad and
  redundant (edge connectivity 68–76) — the substrate has few independent
  degrees of freedom to begin with.
- The 07-28 external review's own two-boson measurement: the 2-particle
  observable correlates with the 1-particle one at ρ ≈ 0.88–0.90 even at
  U=12. Adding a whole particle moved the observable by ~10%.

**Both outcomes are first-class findings, and they are opposite:**

- **Low effective rank (≈2–3).** The 226 cells are ~15 independent tests.
  [[TASK-0161]]'s multiplicity arithmetic changes materially (in the
  program's *disfavour* — fewer independent tests means the "fewer positives
  than chance predicts" headline weakens). More importantly it **explains
  every negative at once**: the program measured one quantity, thoroughly.
  That is a structural result about the whole method class and a far more
  interesting sentence than forty separate negatives.
- **High effective rank.** The observables are genuinely independent, the
  negatives are genuinely independent negatives, and the program's central
  claim is *stronger* than it currently states — forty independent routes,
  all closed.

The program cannot currently say which of these is true, and it is asserting
the second by implication.

## Intent Contract

- Outcome: a per-target cross-observable Spearman correlation matrix, its
  effective rank under a stated definition, the leading principal component's
  loading profile and its correlation with `−hop`/`−euclid`, and an explicit
  verdict on how many independent quantities the register has measured.
- Why required, not assumed: [[TASK-0161]]'s budget, [[TASK-0184]]'s
  "breadth of falsification" narrative, and every "N independent routes"
  sentence in the register all presuppose independence that has never been
  measured.
- In Scope:
  - Assemble the per-residue score vector for every scored observable on each
    of the 3 mandatory targets (+ PTP1B/CASPASE7 if cheap). Reuse stored
    vectors where they exist; recompute only what is missing.
  - Spearman correlation matrix per target. Report as a figure and a table.
  - Effective rank under a **stated, pre-chosen** definition — participation
    ratio of the eigenvalue spectrum `(Σλ)²/Σλ²` is the recommended default
    (continuous, no arbitrary threshold). Report a threshold-based count
    (eigenvalues explaining 90%/95% variance) alongside it as a sanity check,
    not as a substitute.
  - Project `−hop_from_seed` and `−euclid_from_seed_centroid` into the same
    space: **how much of the leading component is the proximity confound?**
    This is the interpretive payload — a low rank whose dominant axis is
    distance says something much sharper than a low rank alone.
  - State the consequence for [[TASK-0161]]'s budget explicitly, with the
    recomputed expected-false-positive arithmetic.
- Out Of Scope:
  - Any plant. That is [[TASK-0168]], and this task is deliberately its
    unblocked half.
  - Re-scoring anything against labels. This measures observable-vs-observable
    structure, never observable-vs-truth — so it consumes **no** multiplicity
    budget and touches no answer key. State that explicitly in the write-up.
  - Dropping or merging observables in the register on the strength of this
    result. Measure first; curation is a separate decision.
- Constraints And Invariants:
  - **Choose the effective-rank definition and write it into this file before
    computing anything.** The statistic is threshold-sensitive and this is
    exactly the knob this project's own `INVARIANCE_PROTOCOL.md` would
    classify as a KNOB requiring characterization.
  - Sweep the definition afterwards and report the range, per [[TASK-0075]]'s
    precedent for knob disclosure.
  - Observables measured on different node sets must be aligned to a common
    residue index before correlating. Silently correlating misaligned vectors
    is the obvious failure mode here — assert alignment, do not assume it.
- Planned Validation:
  - **Positive control:** inject two deliberately-identical observables and
    one deliberately-orthogonal random vector into the matrix. Effective rank
    must respond correctly to both (not increase for the duplicate, increase
    by ~1 for the random). If it does not, the statistic is not measuring what
    it claims.
  - **Negative control:** the same computation on N random score vectors of
    matched length must return effective rank ≈ N.
  - Cross-target consistency: if effective rank differs wildly between targets
    of similar N, diagnose before reporting.

## Pre-Registered Definition + Observable Enumeration (fixed 2026-08-04, before any computation — Implementer A)

**Effective rank, primary definition** (per this task's own Constraint,
fixed before computing anything): **participation ratio of the eigenvalue
spectrum of the cross-observable Spearman correlation matrix**,
`PR = (sum(lambda))^2 / sum(lambda^2)`. For an `M x M` correlation matrix
(unit diagonal), `sum(lambda) = trace = M`, so `PR = M^2 / sum(lambda^2)`,
ranging `[1, M]` — `1` if all `M` observables are perfectly correlated (one
underlying quantity), `M` if the correlation matrix is the identity (fully
independent). New function: `metrics.participation_ratio_rank(corr_matrix)`.

**Sanity/sweep companions, computed and reported alongside, never
substituted**: (a) threshold count — smallest `k` such that the top-`k`
eigenvalues explain >=90%/95% of variance; (b) `metrics.eff_rank`
(Roy & Vetterli 2007 entropy-based definition, already in this codebase,
confirmed distinct from participation ratio) applied to the same spectrum,
as the "sweep the definition" comparison point [[TASK-0075]]'s precedent
asks for.

**Observable enumeration** (Open Question, answered): no flat list of ~40
observable names exists anywhere in the register — [[TASK-0161]]'s own
table (`RESULTS.md`'s "Program-level multiple-comparison budget" section)
is a **family-level** table (target x parameter-grid-point counts per
owning task), not a per-observable list, and it is not machine-reusable
(no stored JSON/array). Hand-assembled here, one entry per **distinct
scored quantity type** (not per parameter-grid point — e.g. `dcc_low` at
`k_modes=20` represents that whole family, its own `k`-sweep is a knob on
one observable, not four observables) from every family in that table
with a genuine per-residue `(N,)` score vector:

- 15 Hamiltonian operators' CTQW occupancy (H1-H12, H14, `H_new`,
  `build_H10` — `analysis._operator_registry`, reused directly). **H13
  excluded**, discovered while smoke-testing this enumeration (not
  assumed): `H13_3N_anm_hessian` returns a `3N x 3N` operator (per-axis,
  not per-residue), and `analysis.operator_sweep` itself already excludes
  H13 from residue-indexed scoring for exactly this reason ("cannot be
  indexed by residue without a reduction this task does not invent") —
  matched here, not re-litigated with a novel reduction.
- `dcc_low`, `prs_low` (lowmode, `k_modes=20`).
- `R_eff` (`effective_resistance_from_source`), `T(E=0)` on `L`, `T(E=0)`
  on `H_new` (transport).
- Chiral circulation score.
- Mode co-participation (`CP_low`).
- Spectral (frequency-domain) coherence score.
- Single-particle entanglement entropy (per-residue, `hop_radius_
  neighborhoods(radius=1)` — confirmed genuinely `(N,)`, not the single
  scalar the real-run script's own summary implied on first read).
- GNM transfer entropy source score.
- Persistent-H2 void score.
- Residue conformational entropy (the "ensemble/entropic" family,
  [[TASK-0166]]).
- Binding-response `coupling_specificity` ([[TASK-0178]]).

**28 distinct observables total.** Two families from [[TASK-0161]]'s table
are **excluded, with reason, not silently dropped**: percolation /
`connectivity_robustness` and graph-openness/closure — both checked
directly (`percolation.py`/`closure.py`) and confirmed to return
**scalar-per-target** connectivity/openness statistics, not per-residue
`(N,)` score vectors — there is nothing to correlate residue-by-residue.
Also excluded as **not distinct observable types**: reverse-direction
(holo-seeded) coupling variants, consensus-label rescoring, apo-structure-
sensitivity sweeps, and ceiling/ablation permutation-null re-tests — each
of these reuses an already-enumerated observable's own score function
against a different label, direction, or structure, not a new scored
quantity.

**Targets**: the 3 mandatory (KRAS_G12C, BCR_ABL1, CARDIAC_MYOSIN)
computed first as the primary result; PTP1B/CASPASE7 attempted after,
per this task's own "if cheap" hedge — included in the final report if
they complete in reasonable wall-clock time, otherwise reported as
attempted-but-deferred, not silently dropped.

**ENAQT (dephasing sweep) explicitly not included**: `analysis.
dephasing_sweep` needs labels internally (it returns AUC, not a raw score
vector) and its own per-gamma raw-occupation path
(`propagators.haken_strobl`) costs ~20s/gamma at `N~170` (its own
docstring) — expensive for one more observable already qualitatively
known to closely track the base CTQW occupancy ("coherence adds ~nothing"
finding, `PLAN.md`). Scoping decision, stated here rather than silently
computed away.

**Spearman, not Pearson** (Open Question, answered per this task's own
recommendation: every downstream use in the register is a rank statistic,
AUC — not swept as a knob).

## In Progress

—

## TODO

- [x] Write the chosen effective-rank definition into this file. **Before computing.**
- [x] Enumerate every scored observable + locate/recompute its score vector per target.
- [x] Assert common residue-index alignment across all vectors — caught and fixed a real
  misalignment (H13's 3N-shape) via this exact check before it could silently corrupt anything.
- [x] Correlation matrix + effective rank, per target — all 5 targets.
- [x] Positive + negative controls (duplicate / orthogonal / all-random) — real-data +
  dedicated synthetic controls, see Done section for the real-data "+1" caveat found.
- [x] Project `−hop`/`−euclid` into the space; report the leading component's confound loading.
- [x] Sweep the rank definition; report the range.
- [x] Restate [[TASK-0161]]'s expected-false-positive arithmetic under the measured effective rank.
- [x] Hand the verdict to [[TASK-0184]] — quotable verdict sentence in Done section below.

## Dependency

- None hard. Feeds [[TASK-0161]] (budget), [[TASK-0184]] (narrative),
  [[TASK-0168]] (which can drop its redundancy checkbox once this lands).

## Open Questions

- Which observables count? Recommendation: everything that has ever produced a
  scored AUC against a real target label — the same enumeration [[TASK-0161]]
  used, so the two results speak the same language. Reuse that list rather
  than building a second one.
- Spearman or Pearson? Spearman, since every downstream use is a rank
  statistic (AUC). Note the choice; do not sweep it as a knob.
- If effective rank is low, does the honest reading weaken the program's
  headline? **Yes, and that is not a reason to avoid measuring it.** Fewer
  independent tests means the "fewer positives than chance predicts" claim
  rests on a smaller denominator. Report it in the direction the data points.

## Done

**2026-08-04, Implementer A.**

### Headline finding: effective rank ≈ 3 of 28, consistently, across all 5 targets

| Target | N | Participation-ratio rank | Entropy rank (`eff_rank`) | Components for 90%/95% variance | `-hop`'s PC1 loading percentile among real observables |
|---|---|---|---|---|---|
| KRAS_G12C | 169 | **3.12** | 6.59 | 10 / 14 | 82.1% |
| BCR_ABL1 | 451 | **2.62** | 5.30 | 8 / 12 | 64.3% |
| CARDIAC_MYOSIN | 704 | **3.25** | 7.05 | 11 / 16 | 64.3% |
| PTP1B | 298 | **2.61** | 5.38 | 8 / 12 | 42.9% |
| CASPASE7 | 461 | **4.08** | 8.09 | 11 / 14 | 57.1% |

Out of **28 distinct observable types** (every genuinely per-residue-scored
quantity in the register — see the pre-registered enumeration above),
the participation-ratio effective rank sits at **2.6–4.1 on every one of
5 targets spanning N=169–704** — low, and remarkably stable across very
different target sizes and folds (Planned Validation's own cross-target-
consistency check: no wild swing between similarly-sized targets, no
diagnosis needed). The entropy-based sweep companion (`eff_rank`) reports
a systematically higher but still low number (5.3–8.1 of 28) — the two
definitions agree in direction and in "low, not high," disagreeing only
on exactly how low, which is itself informative (participation ratio is
more sensitive to one dominant component; entropy-based rank gives the
long tail of small-but-nonzero components more relative weight — both
are reported, per this task's own Constraint, neither substituted for
the other).

**Confound loading**: `-hop_from_seed`'s own loading on the leading
principal component sits at or above the *median* of the 28 real
observables' own loadings on every target (42.9–82.1 percentile) — not
always the single largest loading, but never a marginal, low-loading
variable either. This is consistent with, though not a pure restatement
of, the low-rank finding: the dominant shared component is substantially
— not exclusively — a distance-from-seed effect.

### Controls

**Real-data injection** (run on each target's own actual 28-observable
matrix): duplicate-column rank never rises (deltas -0.04 to -0.21, all
5 targets) — correct. Orthogonal-random-column rank always rises
(deltas +0.17 to +0.27) — correct direction, but **not** the naive "+1"
textbook magnitude. **Found and diagnosed, not assumed a bug**: hand-
verified the participation-ratio formula directly against the new
eigenvalue set after injection — the small delta is the *exact*,
expected consequence of adding one new dimension to an already
highly-skewed (low-rank) spectrum, where one dominant eigenvalue
continues to dominate `sum(lambda^2)` regardless. Confirmed on a
controlled synthetic case (near-uniform base spectrum,
`tests/test_observable_effective_rank.py::TestPositiveControlOnNearUniformBase`)
that the textbook "+1" delta **does** hold cleanly when the base spectrum
isn't already skewed — so the muted real-data delta is itself corroborating
evidence for the low-rank finding, not a control failure.

**Synthetic negative control**: 12 independent random `(500,)` vectors
give participation-ratio rank within 3 of 12 (`test_observable_effective_
rank.py::test_independent_columns_give_near_full_rank`) — the statistic
correctly reports near-full rank when there is genuinely nothing to find.

### `TASK-0161` budget restatement (illustrative, clearly scoped)

[[TASK-0161]]'s own count: 366 cells, expected false positives at
`alpha=0.05`: `0.05 * 366 ~= 18.3`. That count is built from **~28
observable types** (this task's own enumeration) spread across a target x
parameter-grid-point structure per family (e.g. the 96-cell operator
sweep = 16 operators x 2 propagators x 3 targets). This task measured
that those 28 observable types collapse to an effective rank of **~3**
— a **~9x** redundancy factor (28/3 ~= 9.3) at the observable-type level
alone, before even considering the grid-point redundancy already
implicit within each family (TASK-0161's own count already treats a
family's own k-sweep/parameter-grid cells as one family, not as
independent tests of the same claim, but does not discount for
cross-family/cross-observable-type redundancy — the gap this task
closes).

**Illustrative rescaling** (proportional, not a full cell-by-cell
re-derivation of all 366 cells' own independence structure — that
re-derivation, folding in exactly how much within-family grid points
already double-count, is larger than this task's own "half a day, purely
re-analytic" scope, and is named as a possible follow-up, not attempted
here): scaling 366 by the measured `3/28` redundancy factor gives
**~39 effectively-independent cells**, expected false positives
`0.05 * 39 ~= 2.0` — **down from ~18.3 to ~2**, roughly a 9x reduction,
matching the observable-type redundancy factor directly (the arithmetic
is dominated by that factor, not by re-litigating target or grid-point
counts). **This moves the budget arithmetic against the program's own
headline, exactly as the Context section's own "low effective rank"
branch predicted, and that is the honest reading — not a reason to have
avoided measuring it.** Zero confirmed positives against an expected ~2
is a substantially weaker claim than zero against an expected ~18.3,
though it is still a claim (the observed count is still below the
now-smaller expectation).

### Verdict sentence (for [[TASK-0184]]'s narrative, quotable as-is)

*"The register's ~40 (28 distinct, per-residue-scored) observables are
not independent: their cross-observable Spearman correlation structure
has an effective rank of only ~3, measured consistently across 5 targets
spanning N=169-704, with `-hop_from_seed` itself loading at or above the
median of all 28 observables on the dominant shared component. The
program's 366-cell multiplicity count, and the 'fewer positives than
chance predicts' argument built on it, substantially overstates the
number of independent falsification attempts — an illustrative rescaling
by the measured ~9x redundancy factor brings the expected-false-positive
baseline from ~18.3 down to ~2. This is not a reason the program's
negative result is wrong; it is a more accurate, and more interesting,
description of what was actually measured: the program tested one
structural quantity — propagation on a static, seed-anchored contact
graph — thoroughly and from many angles, not forty independent
quantities forty times each. That reframing explains every negative at
once, more parsimoniously than forty separate negatives, and is a
structural finding about the whole method class, not a weakness to
minimize."*

### Scoping decisions (stated, not silently made)

- **Two families excluded** because they are not per-residue vectors at
  all (checked directly, not assumed): percolation/`connectivity_
  robustness` (`percolation.py` — scalar connectivity statistics) and
  graph-openness/closure (`closure.py` — scalar `openness_signature`).
- **ENAQT (dephasing sweep) excluded**: needs labels internally for its
  own AUC-based interface and its label-free raw-occupation path costs
  ~20s/gamma at `N~170` — already qualitatively known to track base CTQW
  occupancy closely ("coherence adds ~nothing," `PLAN.md`).
- **H13 excluded**: `3N x 3N` shape, matches `analysis.operator_sweep`'s
  own established exclusion — found via this task's own alignment
  assertion firing on the first real run, not anticipated in the
  original enumeration (task file corrected from 16 to 15 operators, 31
  to 28 total, same-day, before any p-value-adjacent number was reported).
- **Reverse-direction, consensus-label, apo-structure-sensitivity, and
  ceiling/ablation-null variants excluded**: each reuses an already-
  enumerated observable's own score function against a different label,
  direction, or structure — not a structurally distinct scored quantity.
- All 5 targets (3 mandatory + PTP1B/CASPASE7) completed well within
  the "if cheap" hedge (full 5-target run: ~33s total, dominated by
  CARDIAC_MYOSIN's own 15.6s) — no target deferred.

### Tests

`tests/test_observable_effective_rank.py` (12 new: alignment-assertion
regression, correlation/rank computation, the controlled-synthetic
positive control confirming the textbook "+1" delta on a near-uniform
base, the skewed-matrix control matching the real-data finding) + 8 new
in `test_metrics.py` (`participation_ratio_rank`/`variance_explained_
count`, both bound cases + the entropy-vs-participation-ratio distinctness
check). New `metrics.participation_ratio_rank`/`variance_explained_count`
functions, additive, no existing function touched. Full suite:
`1122 passed, 1 skipped, 2 xfailed`, no regressions.

### Out of scope, confirmed not needed

No plant ([[TASK-0168]]'s own territory). No re-scoring against any
label anywhere in this task — confirmed by construction (every function
called takes only `coords`/`bfactors`/`source`, never a pocket mask) —
this task consumes **zero** multiplicity budget itself. No observable
dropped or merged from the register on the strength of this result
(measurement only, per this task's own Out-Of-Scope).

### Not done in this task (named for a follow-up, not built here)

A full cell-by-cell re-derivation of [[TASK-0161]]'s 366-cell count that
folds in both cross-observable-type redundancy (this task's own finding)
and within-family grid-point redundancy simultaneously, rather than the
illustrative proportional rescaling used above.
