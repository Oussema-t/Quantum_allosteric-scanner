# TASK-0140 Chiral (broken-time-reversal) circulation observable, gated eval (HYP-P9)

## Context

- ID: TASK-0140
- Title: Port and benchmark the chiral-walk directed-current observable
  (Peierls flux + Helmholtz-Hodge decomposition), whose circulating part
  is proximity-orthogonal by construction, against the proximity floor
  with CIs and distance-stratification ([[HYP-P9]]).
- Status: Done (2026-07-23) — FAIL against pre-registered bar, see Done section
- Owner: Implementer (build + run). Physics of the observable already
  sanity-checked this batch (two synthetic gates pass — see Source);
  execution needs no new physics judgement.
- Source: `REVIEW-panel-2026-07-20` §"chiral observable" and §"physics
  check of Idea #2". Reference implementation delivered as
  `chiral_observable.py` (`peierls_chiral`, `time_averaged_current`,
  `hodge_circulating`, `chiral_circulation_score`) with GATE 1/GATE 2
  passing on synthetic data — port into `src/allostery/chiral.py`.
  **Flagged 2026-07-20 (Architect/Planner): `chiral_observable.py` is
  not actually present anywhere in this repo or the applied review
  batch** (`.ai/reviews/2026-07-20/` contains only the README, the
  EXECUTION_PLAN insert, and the physics append — no `.py` files).
  Whoever claims this task needs to either obtain the actual reference
  script from wherever it was generated, or reconstruct
  `peierls_chiral`/`hodge_circulating` from HYP-P9's own description
  (`.claude/hypotheses/physics.md`) and the cited literature (Zimborás
  et al. 2013, Sci. Rep. 3, 2361; Lu et al. 2016, PRA 93, 042302) —
  state which, and verify GATE 1/GATE 2 pass on a freshly-built
  implementation before trusting it, not assume the delivered script's
  claimed pass status transfers to a reconstruction.
- Priority: **P1.** The real quantum-flavoured observable of this batch,
  and the disciplined form of the collaborator's "controlled phase"
  Idea #2 (an arbitrary initial phase is an unjustified tunable knob =
  label-leakage risk; the *only* physically-justified phase injection is
  complex hopping / broken time-reversal, which is gauge-invariant and
  acts only on cycles — Zimborás 2013, Lu 2016). **Soft-gated by
  [[TASK-0143]]**: fully meaningful only where the openness premise holds.

## ⚠️ Before implementing — what this observable is and is not

Single-particle. Therefore **classically simulable at N~hundreds** — this
is a *modeling* advantage (directionality + loop-native + proximity-
orthogonal), NOT an asymptotic quantum advantage. Do not let the write-up
imply otherwise; the converged single-particle limit remains phase-free
([[TASK-0130]]) for the *occupation* observable — the chiral current is a
*different* observable (a bond current, odd under time-reversal), which is
why it can carry directional information the occupation cannot. State this
distinction explicitly in `RESULTS.md`.

## Intent Contract

- Outcome: a per-residue chiral-circulation score for every mandatory +
  ASD target, evaluated against the proximity floor with the **same**
  rigor every other operator has had — block-bootstrap CIs ([[TASK-0112]]),
  distance-stratified AUC ([[TASK-0123]]), permutation null on any
  max-over-something statistic ([[TASK-0131]] precedent). A pre-declared
  bar decides whether it clears the floor; not clearing it is a valid,
  reportable negative.
- Why required: it is the first observable in the program that, on
  synthetic data, (i) dissociates coupling from well-depth (GATE 1) and
  (ii) beats the proximity floor on a distal loop pocket with residual
  distance-correlation only ρ≈+0.33 vs CTQW's +0.6..+0.97 (GATE 2). The
  synthetic passes prove the *observable can read a loop signal when one
  exists* — they do NOT prove real pockets carry it. Only the gated real
  run does, and only where [[TASK-0143]] passes.
- In Scope:
  - Port `chiral_circulation_score(H_real, coords, source)` — same call
    shape as `time_averaged_ctqw_converged`, so it slots into
    `analysis.operator_sweep` as one more observable, not a fork.
  - Keep the **Hodge decomposition**: score = magnitude of the
    divergence-free (circulating) current per residue. The gradient part
    is the radial proximity flow and MUST be discarded — this is what
    makes the observable proximity-orthogonal by construction, not by
    tuning. A regression test must assert grad+curl reconstructs J and
    that div(J_circ)≈0.
  - Rotation-robustness: average over >=3 field directions (the delivered
    default). Report sensitivity to field magnitude (`field_scale`).
  - Evaluate on `H_new`'s own apo graph, seeded at the full active-site
    array (incoherent mixture, the fixed seed convention), all targets.
- Out Of Scope:
  - Sweeping an *initial-phase* pattern (the collaborator's raw Idea #2) —
    explicitly rejected as an unjustified label-leaking knob; the flux is
    the justified substitute. Do not add a per-site phase parameter.
  - Multi-field-direction *tuning* against labels — the 3-axis average is
    fixed; do not select a field direction per target by AUC.
  - Operator-selection decisions (Tier-2 gated, [[TASK-0100]]).
- Constraints And Invariants:
  - Field magnitude, number of field directions, and seed convention are
    fixed once, up front, blind to labels. The gauge-invariant content is
    the flux through cycles; a per-target field tuned to labels would
    reintroduce the overfitting this whole program exists to avoid.
  - Fully-decohered / real-symmetric limit sanity: at zero flux the
    circulating score must vanish (no directed current without broken
    time-reversal) — assert as a regression test (the physical guarantee).
- Planned Validation (**pre-registered**):
  - **PASS on target T** iff chiral-circulation AUC clears the proximity
    floor AND the 95% block-bootstrap CIs do not overlap, on >=1 mandatory
    target with generalization-set confirmation, surviving Bonferroni.
    Report Spearman(score, −dist) alongside (expect ≪ 0.6 if honest).
  - **Distance-stratified check**: run [[TASK-0123]]'s `stratified_auc`
    with its permutation null; a whole-graph AUC alone is not sufficient
    evidence (same reason as every other operator).
  - **FAIL**: AUC collapses to the floor / CIs overlap everywhere — report
    "the chiral current finds no real loop signal these pockets carry,"
    consistent with a [[TASK-0143]] FAIL.
  - Synthetic GATE 1 + GATE 2 ported as regression tests first.

## TODO

- [x] Port `chiral.py`; wire `chiral_circulation_score` into `operator_sweep`.
      (Not wired into `operator_sweep` itself -- that function's registry
      builds real `H` operators and applies a *propagator* to them;
      `chiral_circulation_score` needs coords for its own Peierls phase,
      a different call shape. Gained an `H_real` parameter instead,
      matching this task's own explicit `chiral_circulation_score(H_real,
      coords, source)` call shape, and a dedicated real-data script
      (`scripts/chiral_circulation_real_run.py`) -- stated here as a
      deliberate scope choice, not silently dropped.)
- [x] Regression tests: GATE 1 (coupling≠well), GATE 2 (beats floor on
      synthetic loop pocket), Hodge reconstruction, zero-flux → zero curl.
- [x] Real run: all mandatory + ASD, AUC vs floor, block-bootstrap CIs.
- [x] Distance-stratified AUC + permutation null ([[TASK-0123]]/[[TASK-0131]]).
- [x] Bonferroni; emit PASS/FAIL/INSUFFICIENT per target, tagged.
- [x] `results/tasks/0140_chiral/` + `RESULTS.md` section; naive + corrected.

## Dependency

- Soft: [[TASK-0143]] (openness premise) — interpret a FAIL here in light
  of a FAIL there (no loop to circulate in).
- Reuses: [[TASK-0112]] (CI), [[TASK-0123]] (stratified AUC + null),
  [[TASK-0130]] (converged-limit scoring convention / seed).

## Open Questions

- Whether the incoherent full-active-site seed is the right source for a
  *directed* observable, or whether the active-site→pocket direction wants
  a single well-defined source. State the choice; if it materially changes
  the verdict, that sensitivity is itself a finding, not a knob to tune.

## Done

**Headline: FAIL, consistent with TASK-0143's own FAIL on the graph-openness premise.**
No target clears this task's own pre-registered PASS bar (floor + non-overlapping CIs +
Bonferroni-significant stratified-AUC permutation null). Two targets (1 mandatory,
1 ASD) show real, Bonferroni-surviving directional signal on the stratified-AUC
permutation-null statistic alone but fail the primary CI-overlap criterion — reported
as suggestive, not confirmed. The observable's own claimed proximity-orthogonality
(HYP-P9's own "residual rho(score,-dist) much lower than occupation's") **is**
confirmed, consistently, on every target — the observable measures something other
than distance — but that something does not clear the discrimination bar on real data.

### Reference script: confirmed absent, reconstructed from HYP-P9 + cited literature

`chiral_observable.py` is not present anywhere in this repo or the applied review
batch (grepped directly, per the Architect/Planner's own 2026-07-20 flag in this
task's Context) — reconstructed from `.claude/hypotheses/physics.md`'s HYP-P9
description and the cited literature (Zimborás et al. 2013, Sci. Rep. 3, 2361;
Lu et al. 2016, PRA 93, 042302). New `src/allostery/chiral.py`:
`peierls_hamiltonian` (symmetric-gauge Peierls substitution, midpoint line-integral
approximation, complex-Hermitian by construction), `bond_current_converged`
(infinite-time-averaged bond current via projector-dephasing, generalizing
TASK-0130's diagonal/occupation closed form to this off-diagonal bilinear quantity),
`hodge_decompose` (graph Helmholtz-Hodge split via the graph Poisson equation),
`chiral_circulation_score` (multi-field-direction average of circulating-current
magnitude), `circulation_score_from_hamiltonians` (the shared final stage, factored
out for topology-controlled synthetic tests). 35 new tests (`tests/test_chiral.py`).

### Real finding made while building the regression tests: a bare N-cycle ring gives exactly zero converged circulation, at any flux

Not a corner case anyone flagged in advance — discovered directly while building the
first synthetic fixture (a uniform ring, the obvious minimal "topology with something
to circulate in"). Confirmed via direct numerical experiment (not derived from a
textbook result) across idealized rings, randomly-weighted-and-phased rings, and a
ring-plus-bipartite-preserving-chord: **exactly zero** converged circulation from any
diagonal (position-basis or incoherent-mixture) seed, at every flux strength tried,
including a triangle (N=3) under uniform edge weighting. `chiral.py`'s own docstring
§4 documents the two contributing mechanisms isolated (regular-ring circulant symmetry
forcing the dephased density matrix to the trivial maximally-mixed `I/n`; and a
still-unexplained-in-full generality "every node degree exactly 2" effect that
persists even with fully randomized, asymmetric edge weights/phases). **Practical
consequence**: this module's own test suite could not use a bare ring as its "does
chirality produce a signal" fixture — `tests/test_chiral.py`'s
`_triangulated_asymmetric_coords` (an irregular ring widened with next-nearest-
neighbor edges, giving most nodes degree >2) is used instead, with the bare ring
demoted to a documented *null* control (`TestBipartiteAndSymmetryNulls`). Real protein
contact graphs are not bare rings (dense 3-D packing gives every residue degree well
above 2), so this is a synthetic-fixture-design concern, not a real-data validity
concern in general — but it does mean any real region whose local topology happens to
be a single unbranched loop with no shortcuts should be expected to score near zero on
this observable for structural, not biological, reasons.

### `bond_current_converged`'s degeneracy handling: built as an exact projector-dephasing generalization, not a guard

The first draft raised `ValueError` on near-degenerate spectra (mirroring TASK-0130's
own diagonal-case guard). That guard fired immediately and unavoidably on the module's
own ring test fixture (a uniform ring's tight-binding spectrum is *exactly*
doubly-degenerate by symmetry, `E_k = -2cos(2*pi*k/n) = E_{n-k}`) — not a corner case,
the norm for the obvious minimal fixture. Rather than work around it with asymmetric
fixtures only, generalized the formula itself: `_block_projected_density` (reusing
`propagators._group_degenerate_eigenvalues`, not reimplementing it) computes
`rho_inf = sum_r V_r (V_r^dagger rho0 V_r) V_r^dagger` block-by-block, the exact matrix
generalization of TASK-0130's own `_block_projected_diagonal`, reducing to the
original per-mode formula exactly when every block is a singleton (verified directly:
`test_degenerate_spectrum_handled_without_error` confirms an exactly-degenerate
double-copy construction reproduces the single-copy answer for the populated copy's
own edges).

### GATE 1 — dissociates coupling from well-depth (PASS)

TASK-0103's own dumbbell negative-control apparatus (`tests/test_dumbbell_negative_
control.py`) is a **tree** topology (hub — one bridge — lobe); Peierls phases on a
tree are always gaugeable to zero (no cycle to carry flux), so it cannot be reused
unmodified for a circulation observable — this had to be a new construction, not a
literal port. Built a loop-dumbbell (`tests/test_chiral.py`'s `_build_loop_dumbbell`):
a hub connects to each of two lobes (DRUG/DECOY) via **two** disjoint bridge paths, so
each lobe sits on its own genuine cycle; well = a diagonal trap on one lobe's clique,
coupling = the bridge edge weight (strong/weak), varied independently, same
axis-separation logic as the original dumbbell. **Result**: circulation follows
coupling (mean AUC 0.8125 / 0.1875 across 8 seeds, well=DECOY,strong=DRUG and
well=DRUG,strong=DECOY respectively — deterministic across all 8 seeds tried, not an
averaged noisy estimate), while `ground_state_relaxation` on the identical topology
does the opposite (0.0 / 1.0) — confirming the network's own well/coupling axes are
genuinely independent, and that circulation tracks coupling the way `HYP-P9`'s own
text claims. 3 tests, `TestGate1CouplingVsWellDissociation`.

### GATE 2 — beats the proximity floor on a synthetic distal loop pocket (PASS, own numbers — not the original script's unrecoverable 0.33/0.6-0.97)

HYP-P9's own cited numbers (residual rho(score,-dist) ~+0.33 for circulation vs
+0.6..+0.97 for occupation) came from the missing reference script and are not
reproducible by construction (a different, unknown synthetic network) — per this
task's own Context instruction, this reconstruction is verified against the *same
qualitative claim* on an independently-built fixture, with its own actual numbers
reported, not force-fit to the old figures. Construction (`tests/test_chiral.py`'s
`_gate2_coords`): a backbone (natural monotonically-receding background) forks at its
far end into two branches of matched length — a POCKET branch (tight spacing, so a
single fixed global cutoff naturally picks up next-nearest-neighbor edges there,
giving genuine local loop structure) and a DECOY branch (normal spacing, stays
bare/ring-like, near-null by this module's own §4 finding above) — both equidistant
from the seed by construction (TASK-0103's own "same bridge length" principle), so
proximity alone cannot separate them. **Result**: circulation clears
`diagnostics.classify_failure`'s own floor check (the same check every real operator
in this program is held to) with AUC 0.93-0.98 across 6 seeds tried; occupation
(`time_averaged_ctqw_converged`, TASK-0130's convention) does **not** beat the floor on
the identical construction (confirms the pocket's signal genuinely requires reading
loop structure, not "any observable finds it"). Residual distance-correlation:
rho(occ,-dist) approx -0.6 to -0.65 across seeds (matches the *magnitude* of HYP-P9's
own cited 0.6-0.97 range) vs rho(circ,-dist) approx -0.18 to +0.15 (near zero, actually
*better* than HYP-P9's own cited +0.33 — this reconstruction's pocket sits in a
different geometric relationship to distance than the lost original, so the exact
number differing is expected, not a discrepancy to explain away). 6 tests
(`TestGate2BeatsFloorOnSyntheticLoopPocket` + `TestHRealPath`).

### `H_real` call-shape extension (this task's own text: `chiral_circulation_score(H_real, coords, source)`)

`peierls_hamiltonian`/`chiral_circulation_score` gained an optional `H_real` parameter:
when given, Peierls-substitutes that operator's own off-diagonal entries directly
(preserving whatever weighting scheme it used — e.g. `build_H_new`'s normalized-
Laplacian-plus-five-potential-terms — rather than rederiving a fresh binary contact
matrix) and copies its diagonal (on-site potential) through untouched, since Peierls
substitution is a hopping-only transformation in the standard tight-binding formalism.
4 tests confirm Hermiticity, exact diagonal/off-diagonal-magnitude preservation, and
that the `H_real` path reproduces the coords-only path exactly when `H_real` matches
what that path would have built anyway.

### Real run — all 3 mandatory + 4 ASD targets, `H_new`'s own apo graph, full active-site seed (incoherent)

`scripts/chiral_circulation_real_run.py`. `field_scale=0.05`, 3 coordinate-axis field
directions (both fixed up front per this task's own Constraints) — sensitivity to
`field_scale` swept separately (0.02/0.05/0.1/0.2) and reported per target.

| Target | circ AUC | occ AUC | max floor AUC | circ vs floor | CI overlap | rho(circ,-dist) | rho(occ,-dist) | strat-AUC perm p |
|---|---|---|---|---|---|---|---|---|
| KRAS_G12C (mand.) | 0.702 | 0.653 | 0.546 | beats floor | **yes** | -0.259 | -0.700 | **0.0030** |
| BCR_ABL1 (mand.) | 0.419 | 0.560 | 0.619 | below floor | yes | -0.479 | -0.738 | 0.5005 |
| CARDIAC_MYOSIN (mand.) | 0.395 | 0.531 | 0.583 | below floor | yes | -0.223 | -0.712 | 0.6566 |
| PTP1B (ASD) | 0.640 | 0.495 | 0.492 | beats floor | **yes** | -0.286 | -0.695 | **0.0020** |
| GLUCOKINASE (ASD) | 0.677 | 0.657 | 0.863 | below floor | yes | -0.392 | -0.594 | 0.0120 |
| CASPASE1 (ASD) | 0.639 | 0.676 | 0.919 | below floor | yes | -0.374 | -0.581 | 0.4961 |
| CASPASE7 (ASD) | 0.530 | 0.600 | 0.758 | below floor | yes | -0.260 | -0.434 | 0.8434 |

Bonferroni threshold across 7 targets: 0.05/7 = 0.00714.

**Pre-registered verdict: FAIL.** CI overlap is `True` on every single target — the
primary criterion ("clears the floor AND the 95% block-bootstrap CIs do not overlap")
is not met anywhere, so no target reaches even the single-target PASS bar, and the
"generalization-set confirmation" question is therefore moot.

**Distinct, real, consistently-directional finding, reported honestly as suggestive
(not a PASS)**: KRAS_G12C (mandatory) and PTP1B (ASD) both clear the floor on
whole-graph AUC *and* clear the Bonferroni-corrected threshold on the independent
stratified-AUC permutation-null statistic (p=0.0030, p=0.0020, both < 0.00714) — a
real, non-random signal by that specific test, just not one that survives the stricter
CI-overlap bar. GLUCOKINASE clears p<0.05 uncorrected (p=0.0120) but not Bonferroni.
The other 4 targets show no signal by either test.

**The proximity-orthogonality claim itself is confirmed, cleanly, on every target**:
rho(circ,-dist) is smaller in magnitude than rho(occ,-dist) on all 7/7 targets (circ
range -0.22 to -0.48; occ range -0.43 to -0.74) — circulation is consistently, and by
a wide margin, less proximity-confounded than occupation, exactly HYP-P9's own
mechanistic claim. This property holding while the discrimination AUC mostly fails to
clear the floor is itself informative, not a contradiction: being orthogonal to
distance is necessary but not sufficient for beating a floor built from several
distance/degree-flavoured baselines, and TASK-0143's own FAIL (0/7 targets show a
graph-open pocket) already predicts there is often no genuine loop signal to read on
these targets.

**Field-scale sensitivity**: real and non-trivial, most visibly on PTP1B (AUC ranges
0.429 at `field_scale=0.02` to 0.818 at `field_scale=0.2` — crossing the floor in both
directions across the sweep) and KRAS_G12C (0.810 to 0.647, monotonically declining as
`field_scale` grows). This is reported as a genuine, target-dependent sensitivity, not
smoothed over — the pre-registered `field_scale=0.05` default sits in the middle of
this range for both, neither best-case nor worst-case for either target.

### Interpretation

Consistent with TASK-0143's own FAIL: "the chiral current finds no real loop signal
these pockets carry" (this task's own pre-registered FAIL framing) is the honest
read, with two suggestive (not confirmed) exceptions (KRAS_G12C, PTP1B) worth noting
for any future targeted follow-up but not enough to reopen this task's own gate.
Per HYP-P9's own counter-evidence bullet ("if pockets are not graph-open... the score
collapses to the floor") — that is close to, but not exactly, what happened: the score
did not collapse *to* the floor (it is measurably below the floor on 4/7 targets and
only modestly above it on the other 3), and the proximity-orthogonality property held
throughout regardless. TASK-0142's own hard gate ("run only if TASK-0143 or TASK-0140
shows life") remains unmet by this result — no target here clears the pre-registered
PASS bar, so TASK-0140 does not open it either.
