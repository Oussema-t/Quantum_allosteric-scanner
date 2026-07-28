# External panel review — 2026-07-28

**Scope:** full read of the `bartosz` branch (`EXECUTION_PLAN.md`, `RESULTS.md`,
`COMPETENCE_MAP.md`, `ALGORITHM_REGISTER.md`, `.claude/hypotheses/*`, `.ai/tasks/`,
`src/allostery/*`, `tests/`), plus the `main` branch's Phase-2 additions.
Panel: computational biophysicist · protein-dynamics expert · structural biologist ·
quantum-computing researcher · Hamiltonian-engineering expert · drug-discovery
scientist · Nature/Science referee.

**Method note:** four claims were re-derived by execution rather than read. Where this
review's numbers come from my own runs on synthetic protein-like graphs rather than
your real targets, that is stated. Synthetic models are models — the *direction* of
each effect below is robust; the *magnitude* is not a measurement of your structures.

---

## 0. Headline

The program is a rigorous, multiply-confirmed negative result with a falsification
apparatus that is better than the science it was built to test. That is a defensible
submission. **But the central negative is currently over-stated by one step**, and the
step is cheap to correct.

Specifically: `TASK-0158` replaced an anti-conservative permutation null with an
*over*-conservative one, then let a pre-registered falsification statement fire against
it. `dcc_low` was not shown to be dead; it was shown to be undecided. You already wrote
the code that decides it (`nulls.compact_patch_matched`) and never called it.

---

## 1. Current scientific status

### Established, and I could not break it

| Finding | Evidence quality |
|---|---|
| The entire register lives in a single-particle Hilbert space of dim N; every reported observable is an `eigh` away | **Anchoring theorem. Correct.** Verified against `propagators.py`, `transport.py`, `entanglement.py` |
| Seeded occupation is a proximity detector; the confound is in the *observable*, not the operator | **Established.** Multiple independent routes; survives every operator swap |
| `heat` on `H_new` is imaginary-time ground-state projection, not diffusion | **Established**, correctly retracted (`TASK-0095`) |
| GSR tracks the well, not the coupling (dumbbell 2×2) | **Established.** Cleanest negative control in the repo; reproduced in my run of `test_dumbbell_negative_control.py` (C2/C3 exact) |
| Anderson-like localization in `H_new` is gauge-invariant, not a clock artifact | **Established** (`TASK-0119`) |
| Potential variance budget was broken (V_R 88.8%) and the `most_impactful_term=V_R` finding was its artifact | **Established** (`TASK-0121`) |
| Coherence adds nothing: flat γ-sweeps, coherent ≥ ENAQT under NISQ noise, phase-free converged limit is exact to 1e-6 on real data | **Established**, 3 independent routes |
| Benchmark-integrity findings (6C1H lacks mavacamten; 5TBY was a 20 Å docked model; KRAS Switch-II/active-site overlap; BCR-ABL1 pre-formed) | **Established and under-reported.** See §6 |
| Forward/reverse asymmetry: 10/25 vs 4/25 floor-clears | **Observed**, new, and important — see §3 |

### Speculative, or resting on one leg

- **`dcc_low` is dead.** [RETRACTED by this review — see §2.1.] Not established.
- **The program has zero corrected-null-surviving positives** (`TASK-0161`). Arithmetically
  correct *given* `TASK-0158`'s null. That null is wrong in the other direction.
- **`TASK-0145`'s BCR-ABL1 `T(E=0)` on L (p=0.003)** — correctly flagged as unresolved,
  never re-run. It is the only cell that has never been fairly tested in either direction.
- **The new `quantum_connectivity_matrix` deliverable** — mathematically clean, never
  scored against your own floor. See §2.3.
- **The learnability gate** has now flipped verdicts four times on the same targets
  (`LEARNABLE` → `AMBIGUOUS` → `UNLEARNABLE_FROM_APO` → `AMBIGUOUS`) as CO conventions,
  chain maps, apo structures and nulls changed. Every individual flip is defensible.
  The *sequence* is a warning that this gate's verdicts are knob-determined, not
  data-determined. `TASK-0075`'s `UNSTABLE` reporting is still TODO and now overdue.

---

## 2. Strengths, weaknesses, and four things I found by execution

### 2.1 [P0] The compact-patch null over-corrects, and it killed your strongest result prematurely

**What I ran:** protein-like globule (N=300, 3.2 Å hard-sphere packing), smooth
proximity-confounded score field, 3000 replicates, three label geometries.

```
Radius of gyration of a 16-residue label set:
  k-NN ball   (TASK-0158's fix)  5.47 A
  surface patch (real pocket)    7.85 A     <- ball is 30% MORE compact
  scattered   (the old bug)     14.24 A

Type-I error when the TRUE label is a surface patch (nominal alpha = 0.05):
  null = scattered  (ORIGINAL)  0.259   -> 5.2x inflated   [reproduces your 4.8x]
  null = k-NN ball  (THE FIX)   0.013   -> 0.3x nominal    [~4x OVER-corrected]
  null = matched               0.050   -> 1.0x nominal
```

Power cost, real signal injected at +0.3/0.5/0.7 sd: ball-null power 0.03/0.04/0.07
vs matched-null 0.08/0.12/0.17 — **a 2–2.5× loss of power.**

Robustness (this is the part that matters): the ball null is correctly calibrated
*only in the limit where the real pocket is itself a solid ball*.

| pocket geometry (`surf_frac`) | pocket Rg | actual α under the ball null |
|---|---|---|
| 0.30 (thin surface shell) | 9.1 Å | 0.009 |
| 0.45 | 7.4 Å | 0.021 |
| 0.60 | 6.3 Å | 0.045 |
| 1.00 (solid ball) | 5.2 Å | **0.054 ← nominal** |

Ligand-binding pockets are surface concavities. Real geometry sits in the 0.3–0.6 band.

**Consequence.** `dcc_low`'s corrected p-values were 0.060 (CARDIAC_MYOSIN) and 0.019
(PTP1B). Against a null that is 2–5× too strict, those are not a refutation. The
pre-registered falsification statement in `PANEL_REVIEW_2026-07-25.md` §5.3 fired
against a mis-specified alternative, and `TASK-0161`'s "zero positives, fewer than
chance predicts" headline inherits the error. **"Fewer positives than chance predicts"
is itself the diagnostic** that the null is too conservative — you noted the observation
and read it as strength rather than as a calibration warning.

**The fix costs an afternoon and already exists.** `nulls.compact_patch_matched` is
written, tested, and has **zero call sites outside `test_nulls.py`** (grepped). Measure
each target's real pocket Rg, re-run the `dcc_low` and `T(E=0)` cells with
`target_rg=<measured>`, report all three p-values (scattered / ball / matched) side by
side. That is the honest interval, and it is a *stronger* referee-facing story than
either endpoint alone.

### 2.2 [P2] A real failing test, and its claimed validation is structurally false

`tests/test_metrics.py::TestSpatialBlockBootstrapCi::test_reduces_to_sequence_block_on_a_1d_line_with_matching_order`
**fails** in a clean environment (numpy 2.4.4 / scipy 1.17.1):

```
assert 0.43316412859560066 == 0.5175923810974062 +/- 0.03
```

This is not a tolerance problem. `block_bootstrap_ci` uses a **forward** window
`range(s, s+block_size)`; `spatial_block_bootstrap_ci` uses a **centred** k-NN
neighbourhood. On a 1D line these are offset by ~block_size/2:

```
centre s=50:  sequence window  [50..59]
              k-NN block       [46..55]     index sets coincide? False
mean overlap between the two block definitions across all centres: 0.54
```

The docstring, the test docstring, and `RESULTS.md`'s TASK-0165 entry all assert the
sets *coincide*. They overlap 54%. No verdict depends on this (no CI has ever been
non-overlapping), so it is P2 — but a project whose entire claim is "we execute our
validations" cannot ship a red bar on a validation it says it executed. Either centre
the sequence window or restate the regression property as "same block *size*,
different block *phase*."

*Other 228 tests I ran across 8 modules passed cleanly. The suite is genuinely good.*

### 2.3 [P1] The new challenge deliverable was never scored against your own floor

`TASK-0160`'s `P_inf(i,j) = Σ_k |v_k(i)|²|v_k(j)|²` correctly fixes the three §5
compliance failures. I verified row-sum-to-1 and exact symmetry independently. But it
shipped as a *format* fix and was never put through the floor/null machinery every
other observable in the register had to pass. On my synthetic contact graph (N=200,
bare combinatorial Laplacian — i.e. the *most* favourable case, no `H_new` disorder):

```
rho(P_inf seeded at active site, -hop distance)  = +0.393
rho(P_inf seeded at active site, -euclid)        = +0.421
rho(P_inf[i,j], -hop[i,j]) over ALL pairs        = +0.467
```

A referee will ask what the N×N matrix *predicts* and whether it beats distance. Run
it through `classify_failure` + `compact_patch_matched` before submission. If it fails,
say so in the same breath as delivering it — that is consistent with everything else
in your narrative and costs you nothing.

### 2.4 [confirms your call] The multi-particle exit is dead, for a better reason than you gave

You ruled out interacting multi-particle walks on the argument that "the coincidence
observable reduces to single-particle²." That reduction is exact **only at U=0**, so
the argument does not actually cover the interacting case it was used to rule out. I
built the two-boson Bose–Hubbard sector explicitly (N=53 contact graph, dim 1431, full
bosonic enhancement factors) and tested both the marginal and the genuinely
non-reducible correlated observable:

```
                        rho(2-particle, 1-particle)   rho(score, -hop)
marginal   U=0.0                 0.948                      0.746
           U=4.0                 0.899                      0.797
           U=12.0                0.897                      0.822
G2 (HOM-style, non-reducible)
           U=0.0                 0.901                      0.826
           U=12.0                0.882                      0.821
single-particle baseline            —                       0.727
```

**Interaction does not decouple the observable (ρ stays ≈0.88–0.90) and makes the
proximity confound *worse* (0.73 → 0.82).** On-site repulsion localizes the pair. Your
deprioritization of `TASK-0157` is now supported by measurement, not prior — use the
measurement, it is a stronger sentence in the paper.

### Hidden assumptions still unexamined

1. **The active site is the right seed.** Every observable assumes allostery is a
   directed channel *from* catalysis. `TASK-0162` just showed forward and reverse
   disagree sharply (40% vs 16% floor-clears; CARDIAC_MYOSIN `prs_low` 0.836 → 0.321).
   Your own data now contradicts the seeding premise the whole register is built on.
   This deserves to be a headline, not open-questions row 45.
2. **Cα resolution.** Every negative in this program is a negative *at Cα/GNM
   resolution with an 8 Å cutoff*. `TASK-0142`'s H2 result is explicitly resolution-
   limited. The honest claim is bounded; state the bound.
3. **A single apo structure is the ensemble.** `TASK-0155` (apo-sensitivity sweep) is
   filed, unrun. Motlagh–Hilser says the pocket exists in a *sub-population*. You
   tested one crystal form.
4. **AUC over all non-pocket residues is the right statistic.** It is dominated by
   easy far negatives. `stratified_auc` partly addresses this; the whole-graph AUC is
   still what most tables report.

### Overfitting risk — assessed

Genuinely well-controlled: `frozen_context`, LOPO, `stamp_provenance`, the
`BEATS_CHANCE_NOT_FLOOR` category, and the honest `TASK-0161` enumeration are better
than most published work. The residual exposure is **human**, not code — ~15 review
cycles against 3 answer keys, and `TASK-0164` established the ASD pool is *exhausted*
(0/6 remaining configs resolvable). You cannot get a fresh held-out set from this pool.
Say that explicitly in the paper rather than letting a referee find it.

---

## 3. Scientific assessment

**Biological validity — weak-to-moderate.** The elastic-network premise is the
challenge's own stated assumption, so it is granted. But the operationalization
("allostery = signal propagates from active site to pocket") is one of at least three
mechanisms in the literature, and it is the one your own reverse-direction test now
undercuts. `TASK-0166` tested the ensemble mechanism and found it *also* proximity-
confounded — which is a genuinely interesting result: at Cα/GNM resolution, both the
channel picture and the ensemble picture reduce to "flexible residues near the seed."

**Physical validity — strong, and this is the project's best dimension.** Correct
identification of imaginary-time vs real-time evolution, correct handling of degenerate
eigenspaces in the closed form, correct gauge discipline (SE(3), seed convention, clock,
potential scale), the Peschel reduction verified to 1e-16, the Sherman–Morrison O(N²)
transport speedup verified against brute force. The 12.3-hour brute-force integration to
confirm the closed form to 1e-6 was unnecessary and exactly right.

**Statistical validity — the weakest dimension, and improving fastest.** The trajectory
(no floor → chance floor → proximity floor → CIs → permutation nulls → compact nulls →
program-level multiplicity) is exemplary. The current state has one calibration error
in the conservative direction (§2.1) and one unrun cell (`TASK-0145`). Both fixable
before 2026-08-08.

**Computational validity — strong.** 891 test functions, real negative controls, the
`runlog` CPU-time convention, honest reporting of infeasibility rather than silent
skipping. The `LONG_JOB_CONVENTION.md` lesson (jobs killed by session teardown) is the
kind of thing most projects never write down.

**Referee's summary:** *This would be publishable as a methods/negative-results paper
in a journal that takes them (PLoS Comp Biol, JCIM, Biophysical J). It would not survive
review at Nature/Science, and it does not need to. The falsification apparatus is the
contribution; the allostery result is the demonstration that the apparatus works.*

---

## 4. Next steps, in execution order

The binding constraint is **write from 2026-08-08**, six pages, 2026-09-15. Everything
below is scoped to fit before that date. Items 1–3 are the only ones that can change a
reported claim.

**1. [P0, ~1 day] Rg-matched null re-run.** Measure real pocket Rg per target; re-run
`dcc_low`/`prs_low` (CARDIAC_MYOSIN, PTP1B) and `T(E=0)` on L (BCR-ABL1) through
`compact_patch_matched`. Report scattered / ball / matched side by side.
*Why first:* it is the only experiment that can restore a positive result, and it
decides what the paper's headline sentence is. If matched-null p stays >0.05, your
negative is now *robust to null specification* — a much stronger claim than you can
currently make. Either outcome is a win; not running it is the only losing move.

**2. [P0, ~½ day] Re-run `TASK-0145`'s BCR-ABL1 transport cell under both corrected
nulls.** It is the last unresolved cell in the program and `TASK-0158` explicitly
flagged it as more exposed (7.0×/242×) than the one that was corrected. Leaving it
unresolved through submission is the single most obvious referee target.

**3. [P1, ~½ day] Score `quantum_connectivity_matrix` against the floor.** §2.3. It is
the challenge's own required deliverable.

**4. [P1, ~1 day] Promote the reverse-direction asymmetry to a first-class finding.**
`TASK-0162` is currently framed as a check. It is a *result*: allosteric coupling as
operationalized by every observable in this register is not reciprocal, and the
direction that matters therapeutically is the weaker one. Add a permutation null to the
reverse cells (you noted this was out of scope; it is now in scope).

**5. [P1, ~½ day] Fix or restate the spatial-bootstrap regression property.** §2.2.

**6. [P2, ~1 day] `TASK-0075` knob-spread / `UNSTABLE` reporting for the learnability
gate.** Four verdict flips on the same targets is the evidence that this is needed.

**7. [DO NOT BUILD]** `TASK-0157` (two-boson), `TASK-0147` (vibronic), Hodge-L1. §2.4
now gives you measured grounds to describe the first as closed rather than deferred.

---

## 5. Validation strategy

The falsification apparatus is nearly complete. Three gaps remain, in priority order.

**A. Null calibration is not itself null-controlled.** You now have three null
specifications giving three different answers on the same data. Add a *calibration
check* to the protocol: for any null you adopt, verify that the real label's own
geometry statistic (Rg, compactness, graph spread) lies inside the null draw's
distribution of that statistic. This is one function and it turns null choice from a
judgment call into a measurement. Generalize into `INVARIANCE_PROTOCOL.md` as a fourth
class alongside GAUGE/KNOB/SIGNAL — call it **CALIBRATION**: *a null is only admissible
if the real label is exchangeable with the null draws under the statistic the test
depends on.* This is the single most transferable methodological contribution the
project has produced and it did not exist before this week.

**B. Positive control.** The apparatus has been exercised almost entirely on things
that turned out to be negative. There is no target where you *know* the answer is yes
and confirmed the pipeline finds it. Candidate: inject a synthetic pocket into a real
apo topology (perturb the contact graph to create a genuine distal coupling) and verify
the full pipeline — floor, CI, matched null, Bonferroni — recovers it. If it cannot,
every negative in the program is unfalsifiable rather than false. **This is the
experiment a referee will ask for and you do not currently have it.** Cost: ~1 day,
reuses `build_dumbbell_network` machinery at protein scale.

**C. Apo-ensemble sensitivity (`TASK-0155`).** Cheap for the targets with multiple apo
deposits. Bounds the "one crystal form" assumption.

Explicitly *not* recommended before the deadline: more observables. You have ~40
against 1–3 classical comparators. The marginal observable has near-zero expected value
and adds to a multiplicity budget you have already honestly published.

---

## 6. Executive summary

### Five most important findings

1. **The proximity confound is structural to the observable, not the operator** — and
   `TASK-0166` extended this to the ensemble mechanism, and my §2.4 run extends it to
   interacting two-particle walks. This is now a *general* result about Cα-resolution
   graph observables, which is more interesting than the allostery-specific version.
2. **The permutation-null correction over-shot** (§2.1). `dcc_low` is undecided, not
   dead. "Fewer positives than chance predicts" is a calibration warning, not a strength.
3. **Allosteric coupling is not reciprocal under any observable in the register**
   (`TASK-0162`, 40% vs 16%). This undercuts the seeding premise of the whole program
   and is currently buried.
4. **The benchmark itself is partly broken** — 6C1H lacks mavacamten, 5TBY was a docked
   homology model, KRAS Switch-II overlaps the active site, BCR-ABL1's pocket is
   pre-formed. This is the most defensible and most under-reported content you have.
5. **Everything is single-particle and classically polynomial**, and no route out
   survives contact with the confound (Grover/HHL/QML ruled out on complexity grounds;
   ENAQT, chirality, H2, entanglement entropy, multi-particle all ruled out empirically).

### Five biggest risks

1. **You report a negative that a correctly-calibrated null would not support** (§2.1).
   Highest-severity risk in the project. One day to eliminate.
2. **No positive control** — a referee asks "would your pipeline detect real signal if
   it existed?" and you have no answer at protein scale (§5B).
3. **The learnability gate's verdicts are knob-determined** — four flips, and `TASK-0075`
   is still open. A referee who traces one target's verdict history will find it.
4. **The generalization pool is exhausted** (`TASK-0164`, 0/6). No fresh held-out set
   exists. Must be stated, not discovered.
5. **Writing starts 2026-08-08 and analysis is still landing on 2026-07-28.** The
   `TASK-0163` fpocket result — a classical tool beating your headline observable on
   2/3 targets — landed *today*. Freeze the register.

### Five highest-priority actions

1. Rg-matched null re-run of `dcc_low` + `T(E=0)` — **decides the paper's headline**.
2. Re-run `TASK-0145`'s BCR-ABL1 cell under both corrected nulls.
3. Build the protein-scale positive control.
4. Promote reverse-direction asymmetry + benchmark-integrity findings to headline status.
5. Freeze the analysis register on 2026-08-07 and write.

---

## 7. What remains verifiable — and what the "quantum explains allostery" lead hypothesis still needs

### The challenge's own premise, restated precisely

The Cleveland Clinic statement asserts that *"quantum computers offer a unique advantage
in simulating non-local correlations and interference effects, which are analogous to
how biological signals propagate."* Your program has now falsified the operative half of
this on your benchmark, and the falsification is clean:

- **Interference is measurable but inert.** Coherence sweeps are flat
  (`auc_range` 0.005–0.016); the converged limit is provably phase-free and matches
  brute-force integration to 1e-6; un-averaged spectral content adds nothing
  (`TASK-0146`); coherent beats ENAQT under NISQ noise (`TASK-0068`).
- **Non-locality is absent by construction.** Single-particle dynamics on N sites has
  no entanglement between residues to exploit. `TASK-0148` confirmed this directly —
  the entropy reduces to a binary Shannon entropy of regional occupation.

**The strongest sentence you can write, and it is defensible:** *the challenge's premise
conflates "the mathematics of quantum walks" with "a quantum computational advantage."
The first is a legitimate and interesting modelling choice for graph transport. The
second requires an observable that does not live in a single-particle Hilbert space, and
we tested every candidate we could identify.*

### Untested, in descending order of what a referee would want

| Route | Status | Verdict |
|---|---|---|
| Grover / QML kernels / HHL | ruled out on complexity grounds | correct, keep ruled out |
| Interacting multi-particle (Bose–Hubbard, HOM) | ruled out on an argument valid only at U=0 | **now confirmed empirically** (§2.4) — confound *worsens* with U |
| Quantum Betti / Hodge-Laplacian (LGZ) | H2 half run, FAIL; L1 half gated closed | classical premise falsified at Cα resolution; the *quantum* claim was never the blocker |
| QUBO / densest-k-subgraph pocket selection | **never tested** | see below |
| Vibronic / structured bath (`TASK-0147`) | deprioritized | correctly — highest cost, no proximity-orthogonality prior |
| Non-Hermitian / absorbing-sink CTQW | identified as modelling, not advantage | correct |

**The one genuine gap: QUBO / combinatorial pocket selection.** It is the only route in
your register that (a) has never been tested even classically, (b) is NP-hard in general
so the advantage argument does not immediately collapse, and (c) *changes the question
from scoring residues to selecting a subset* — which is the only reframing that escapes
the seeded-observable confound structurally rather than by construction.

**I am not recommending you build it.** With six weeks to a six-page ideation proposal,
a classically-testable densest-k-subgraph formulation is a 2–3 day experiment with a low
prior, and your own falsification history says the prior should be low. **Recommend
instead: write it up as the forward proposal**, with the honest framing that it is the
one rung you identified, could not close, and can state the falsification criteria for
in advance. A pre-registered next experiment is a *stronger* end to a negative-results
paper than a rushed fortieth observable.

### The three things about "quantum explains allostery" that remain genuinely open

1. **Resolution.** Every negative here is at Cα/GNM/8 Å. All-atom or side-chain-resolved
   networks might carry signal the coarse-graining destroys — and would be the first
   place a proponent of the challenge's premise would point. You cannot test it (no MD
   allowed, and it breaks the qubit-budget story), but you should *name* it as the
   boundary of your claim.
2. **Mechanism plurality.** You have now tested the channel picture and the ensemble
   picture. The third — allostery as *population shift between discrete conformational
   states* — needs two structures, which the no-MD constraint permits and `TASK-0015`
   (LRT/PRS/two-state ANM, still TODO) was filed for. It is the challenge's own ref [15].
   The honest statement is "one of three mechanisms untested," not "allostery does not
   propagate."
3. **Whether the benchmark can discriminate at all.** With 6C1H lacking its ligand, KRAS
   Switch-II overlapping the active site, and BCR-ABL1's pocket pre-formed, **the
   mandatory target set may not be able to distinguish a working method from a broken
   one.** This is your most valuable and least-promoted finding, and it reframes the
   entire submission: not "we failed to find quantum advantage" but "we built the
   apparatus that shows this benchmark cannot currently certify one, and here is what a
   benchmark that could would need."

**That is the paper.**

---

## 8. `main` branch — feedback in light of the `bartosz` findings

`main` adds `backend/quantum.py` (410 LOC), `config.py`, `result_cache.py`,
`rcsb_extract.py`, `verify_eigensolver.py`, `PROFILING.md`, `CHANGES.md`.

### What is good

The engineering is clean and honest. `CHANGES.md`'s "proven no-change" section — the
sparse eigensolver matched dense on low modes but shifted the shipped MSF by 45%, so it
was **not** shipped — is exactly the right instinct and the right disclosure. The
param-keyed cache with SHA-256 over every output-affecting parameter is correct (a
changed cutoff cannot serve a stale result). `quantum.py`'s docstring is unusually
candid: it flags the "trap" terminology mismatch against CTQW literature, corrects a
mis-cited Thouless reference, and states that finite graphs show finite-size
localization rather than a true Anderson transition. The degree baseline and
degree-matched dynamical gate for trap detection show the falsification instinct has
transferred branches.

### Where it contradicts what `bartosz` established — in severity order

**[P0] `/api/allosteric` reports P@5 with no floor, and the metric is far more
permissive than it looks.** `pocket_pk(tol=6.0)` counts a hit if a predicted residue is
within 6 Å of *any* pocket residue. I measured what that dilation does:

```
N=169 pocket=21  (KRAS-like)   | 6A-dilated pocket covers 27.7% of the protein
                               | chance P@5 = 0.26 | pure-distance-to-seed P@5 = 0.66
N=451 pocket=16  (BCR-ABL1)    | covers  9.8% | chance 0.11 | pure-distance 0.47
N=704 pocket=14  (myosin)      | covers  5.9% | chance 0.07 | pure-distance 0.39
```

**A reported P@5 of 0.6 on KRAS is fully explained by distance-to-seed with no quantum
content whatsoever, and P@5 = 0.4 would be *below* the proximity baseline.** This is the
exact confound `bartosz` spent three months establishing, and the live demo — the thing
a judge actually clicks — currently reports the confounded number as a validation
result. Fix: report `euclid_from_seed_centroid` P@5 alongside it in the same JSON field.
It is ~10 lines and it converts the app's weakest claim into a demonstration of the
project's actual strength.

**[P0] `ALLO_FAMILY = "H10_disorder_supp"` is a `bartosz`-falsified operator.** `H10` is
in the operator register and does not clear the proximity floor on any mandatory target
under the corrected gauge. It is labelled `"un-tuned"` in the response payload, which is
true and beside the point — un-tuned does not mean un-falsified.

**[P0] `_average_mixing_matrix` is the phase-free confounded observable.** `main`'s
`occupation` mode is precisely `time_averaged_ctqw`. `bartosz` established (a) that it
is a spectral-overlap quantity with all phase averaged out by construction, (b) that the
shipped finite-time convention is 10⁴–10⁵× short of convergence (`TASK-0159`), and (c)
that `pathway` mode's γ-damped Green's function is a *classical* current-flow object.
Neither mode is quantum in any operative sense. The `docstring` calling it "rigorous
∞-time" is correct about `_average_mixing_matrix` and misleading about what it buys.

**[P1] `min_sep=8.0` and `distal_ang` are unreported verdict-flipping knobs.** These are
post-hoc geometric filters that suppress the proximity confound *without measuring it*.
`TASK-0075` showed an analogous 18-combo grid flipped go/no-go in 15 of 18 cases. If
`distal_ang` is what makes the demo's hit list look plausible, that must be visible in
the UI, not a default argument.

**[P2] Divergences and drift.** `main`'s cutoff is 8.0 Å (matches `targets.yaml`, fine).
`CHANGES.md` is dated 2026-07-04 and does not cover the `quantum.py` addition, whose own
docstring says "fact-checked 2026-07-26" — the changelog has drifted from the code.
`TASK-0072` (golden-value cross-tree drift test) is still TODO and this is exactly the
divergence it was filed to catch.

### Recommendation for `main`

Do **not** rewrite the science layer — there is no time and it is not what is scored.
Do three things, all additive, ~1 day total:

1. **Add the proximity floor to every reported number** in `/api/allosteric`
   (`p_at_k_floor`, `p_at_k_chance`), and render both in the frontend next to the
   prediction. This is the single highest-value change on this branch.
2. **Surface an honest verdict string** from the `bartosz` competence map per target —
   `NO_SIGNAL_IN_APO` / `BEATS_CHANCE_NOT_FLOOR` — so the demo cannot be read as
   claiming a result the research branch has retracted.
3. **Relabel the modes accurately** in the UI: "time-averaged (phase-free) quantum walk"
   and "damped classical current flow," not "quantum" vs "pathway."

A judge who clicks the demo and sees a 3D structure with a *floor bar next to every
prediction* and an explicit `NO_SIGNAL_IN_APO` badge will remember this submission. A
judge who sees P@5 = 0.6 with no denominator, and then reads a six-page paper arguing
that exact number is a proximity artifact, will conclude the team does not read its own
work. **The two branches currently tell contradictory stories, and the research branch
is right.** Reconciling them is a presentation task, not a science task, and it is worth
more rubric points than any remaining experiment.
