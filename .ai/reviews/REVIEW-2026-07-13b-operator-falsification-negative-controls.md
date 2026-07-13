# REVIEW 2026-07-13(b) — Operator falsification via negative controls: what GSR actually measures, and the ENAQT opening

**Scope**: `propagators.{ground_state_relaxation, time_averaged_ctqw, haken_strobl}`,
`H_new` semantics, `RESULTS.md` BCR_ABL1 finding (heat/GSR 0.731), open TASK-0091/0092/0093.
**Method**: all numbers below were **executed** against this repo's own `propagators.py` and
`hamiltonians.laplacian` on constructed synthetic networks where the ground truth is known
*by construction*. Nothing is inferred from reading.
**Status**: supersedes the "GSR is a pure well-locator" claim in the previous review —
that was **over-stated** and is corrected here (see §2, Case A).

---

## 0. Executive summary

1. **`ground_state_relaxation` (GSR) is not a measure of communication from the active site.**
   It is seed-free in the limit, and when *well location* and *communication coupling*
   disagree, **it follows the well**. It is falsified as an allostery detector and
   **retained, with a narrower and honest claim**, as a *structural-prior / cryptic-pocket*
   detector.
2. **BCR_ABL1's 0.731 is therefore real but mis-framed.** It is evidence that the myristoyl
   pocket is a soft, deep, well-coupled region — an apo-computable structural prior — **not**
   evidence of allosteric signal propagation.
3. **ENAQT is the one surviving line of genuine quantum-transport inquiry**, it is
   seed-dependent, it tracks coupling (not wells), and it exhibits the textbook
   **interior-γ optimum** on constructed networks. This is the highest-value experiment
   available before the deadline.
4. **A new candidate operator — mode co-participation — is proposed.** It is the correct
   formalisation of the "reachability" intuition, it is cheap (one `eigh`), seed-dependent,
   and it discriminates coupling from wells by a factor of ~490×.
5. **A general protocol is proposed** (§5): every operator must be paired with a negative
   control that constructs the case where it and its confound make *different* predictions.

---

## 1. What GSR mechanically is (settled, read from the code)

- `ground_state_relaxation(H, t, source)` computes `exp(−Ht) p₀`, where `p₀` is a **real,
  non-negative probability vector** uniform over `source`, then clips and renormalises.
- **There are no complex phases anywhere.** This is *not* a wavefunction evolution and
  *not* a coherent quantum process. It is **imaginary-time** evolution.
- The output is an **amplitude**, not a squared amplitude. (Spearman(output, |ground
  state|²) = 0.998 because the ground state of this operator is elementwise non-negative,
  so amplitude and squared-amplitude are rank-identical. The correlation is not evidence
  of a probability interpretation.)
- **There is no tunnelling.** `exp(−Ht)p₀ = Σₖ cₖ e^{−Eₖt} vₖ`. Nothing traverses a
  barrier; the operator is a **spectral filter** that exponentially suppresses all modes
  except the lowest. Any narrative about "the wavefunction must tunnel through barriers,
  and failing to do so is information" is **mechanically incorrect** and must not enter
  the report.

**[OBSERVED] Seed-dependence decays spectrally.** On a 170-residue synthetic globule with
real `build_H_new` (cutoff 8.0 Å):

| t | Spearman(GSR output, \|ground state\|²) |
|---|---|
| 1 | 0.641 |
| 5 | 0.844 |
| 10 | 0.953 |
| 20 | **0.998** |
| 80 | 0.999 |

Spectral gap E₁−E₀ = 0.430 ⇒ seed memory decays as exp(−gap·t) ≈ 1.9×10⁻⁴ at t=20.
**At the operating point used in the run (t=20), the seed is essentially irrelevant.**
A quantity that does not depend on the active site cannot be measuring communication
*from* the active site.

**[OBSERVED] It is largely the diagonal potential.** 81% of ground-state mass sits on the
10 lowest-diagonal residues; Spearman(|gs|², −diag(H_new)) = 0.739. The diagonal is built
from `V_R`/`V_C`/`V_M` (B-factors, coordination) — none of which reference the active site.

---

## 2. The decisive experiment: the 2×2 control matrix

**Construction.** A dumbbell network (44 nodes), built so that ground truth is known:

```
ACTIVE (0–11) ──[ bridge, 4 nodes, coupling w₁ ]── DRUG  (12–23)   ← the "true" allosteric site
ACTIVE (0–11) ──[ bridge, 4 nodes, coupling w₂ ]── DECOY (24–35)   ← a distractor
```

Both bridges are **the same length** (so hop-distance and Euclidean-distance baselines
cannot separate DRUG from DECOY — the proximity confound is *controlled out by
construction*). We then vary **two cues independently**:

- **well**: a negative diagonal potential placed on DRUG, or on DECOY, or neither.
- **coupling**: bridge weight strong (1.0) or weak (0.15).

ACTIVE residues are excluded from scoring, exactly as the real pipeline does.

**Result — mean AUC(→DRUG) over 5 network seeds. A communication measure must follow the
COUPLING; a well-locator follows the WELL.**

| cell | GSR | CTQW | ENAQT (γ=0.5) | co-participation ratio |
|---|---|---|---|---|
| **C1** cues AGREE (well + coupling on DRUG) | 1.000 | 0.587 | 0.791 | — |
| **C2** CONFLICT — well on DECOY, coupling to DRUG | **0.000** | **0.631** | **0.799** | **489.9×** |
| **C3** CONFLICT — well on DRUG, coupling to DECOY | **1.000** | **0.000** | **0.000** | — |
| **C4** cues ABSENT (flat, equal coupling) | 0.333 | 0.307 | 0.357 | 1.0× |

**Interpretation — a clean double dissociation:**

- **C1 is uninformative.** Every method "passes" when both cues align. *This is the cell
  the real targets sit in, and it is why the confound went unnoticed.*
- **C2 and C3 are the entire test.** GSR scores 0.000 on the coupled site when the well is
  elsewhere (C2), and 1.000 on the uncoupled site when the well is there (C3). **GSR tracks
  the well and is blind to coupling.** CTQW and ENAQT do the opposite: they follow the
  coupling and ignore the well.
- **C4 confirms no method is scoring noise** (all ≈ chance).

**Correction to the prior review.** GSR is *not* a **pure** well-locator: with **identical**
wells on both lobes and only the coupling differing, GSR still scored DRUG 1.000 vs DECOY
0.200 — so coupling *does* shape the ground state. But **C3 shows the well dominates when
the two cues conflict.** The precise, defensible statement is:

> **GSR detects soft, deep, well-connected regions, with well-depth winning ties.**
> It is a *structural-prior* detector, not a *communication* detector.

---

## 3. Consequences for the reported results

**[OBSERVED] BCR_ABL1 GSR = 0.731 must be re-framed, not retracted.** The myristoyl pocket
is a deep hydrophobic cleft in a flexible region — precisely what a `H_new` diagonal well
looks like. The number is real; the *claim* attached to it was wrong. The honest claim is:

> *"Allosteric pockets tend to coincide with soft, low-coordination regions. This is an
> apo-computable structural prior, detectable without reference to the active site."*

That is a legitimate, modest, defensible finding — and note it is a **cryptic-pocket-detection
claim, addressing a different challenge objective than signal propagation.** It should be
reported as such, in its own section, not as evidence of allosteric communication.

**[OBSERVED] The "classical heat vs quantum CTQW" comparison remains void** (prior review,
P1-B). It was never a classical/quantum comparison. The correct classical comparator for
CTQW is the Haken–Strobl γ→∞ limit, not GSR.

**[HYPOTHESIS — untested] APO/HOLO well migration.** GSR requires no active site, so an
apo↔holo comparison asks a well-posed mechanistic question: *does the drug bind where the
well already is (structural prior), or does the well move upon binding (induced fit)?*
This is **holo-requiring ⇒ diagnostic/ceiling only** (`ceiling_context`), **never** in the
prediction path. Testing whether well-migration correlates with soft modes / B-factors /
rigidity would, if positive, be the first result that *justifies the `H_new` construction
itself*.

---

## 4. The ENAQT opening — [OBSERVED], and the best remaining shot

ENAQT's signature is unambiguous and falsifiable: **transport efficiency must be
non-monotonic in the dephasing rate γ** (an interior optimum — noise *helps*). Measured with
this repo's own `haken_strobl` on a network with energy disorder on the bridge (so the
coherent walk Anderson-localises):

| bridge disorder | transport at γ→0 | **peak** | transport at γ→∞ | interior optimum? |
|---|---|---|---|---|
| 0.0 | 0.056 | **0.160 @ γ = 0.5** | 0.000 | **YES** |
| 2.0 | 0.000 | **0.016 @ γ = 2.0** | 0.000 | **YES** |
| 5.0 | 0.000 | **0.001 @ γ = 5.0** | 0.000 | **YES** |

**A ~3× transport enhancement at intermediate dephasing over the coherent walk**, with the
optimal γ tracking the disorder strength (the classic Plenio–Huelga / Rebentrost scaling).
The coherent limit is *bad* at reaching the distal lobe; the Zeno limit is worse.

**Why this matters more than anything else in the repo:**
- It is **seed-dependent** (unlike GSR) — it genuinely measures transport *from* the active site.
- It **tracks coupling, not wells** (C2/C3 above) — it is not the proximity confound and not
  the well confound.
- It is **genuinely quantum** and maps **directly onto the challenge's stated "noise
  resilience" secondary objective**.
- It has a **falsifiable signature** (the interior optimum) that does not depend on AUC at all.

**Reframing TASK-0091.** The old framing ("does dephasing recover 0.731?") was killed for the
right reason — Haken–Strobl's γ→∞ limit is driven by *off-diagonals* while GSR is dominated
by *diagonals*, so they cannot converge. **The right question was hiding underneath:**

> *Does dephasing improve transport from the active site to the distal pocket, relative to
> the coherent walk, with an interior γ optimum?*

Measured on real target topologies, with the proximity floor applied. **This is the single
highest-value experiment available before the deadline.**

---

## 5. The generic lesson — the negative-control protocol

The project has now hit the same failure mode four times: **a metric passes because the test
set only contains the cell where all cues agree.**

| Domain | The confound nobody controlled |
|---|---|
| ENM mode selection | SE(3) rotation (→ index-slicing over a degenerate null space) |
| Quantum-channel object | SU(2) conjugation (→ a Clifford-only fixed-frame artifact) |
| CTQW AUC | translation away from the seed (→ score ≈ distance) |
| **GSR / BCR_ABL1** | **well location vs. coupling** (→ score = where the well is) |

A single negative control is **not sufficient**. The requirement is a **control matrix** that
varies the true signal and its confound **independently**:

|  | confound present on target | confound present elsewhere |
|---|---|---|
| **signal present on target** | cues agree — *uninformative* | **← discriminating cell** |
| **signal absent on target** | **← discriminating cell** | cues absent — *sanity check only* |

**The diagonal proves nothing. The off-diagonal is the entire test.**

**Mandatory template — every operator/propagator in the register must carry one:**

```
OPERATOR:      <name>
CLAIM:         O measures <X> (e.g. communication from the active site)
CONFOUND:      the other thing that would produce the same number (e.g. well depth,
               distance from seed, node degree)
CONSTRUCTION:  a network where <X> and <confound> make DIFFERENT predictions
VERIFICATION:  O must follow <X>, not <confound>
RESULT:        [OBSERVED] ...
VERDICT:       RETAINED (claim <X>) | RETAINED-NARROWED (claim <Y>) | FALSIFIED
```

Worked example, for the register:

```
OPERATOR:      ground_state_relaxation
CLAIM:         measures communication from the active site
CONFOUND:      location of the diagonal potential minimum
CONSTRUCTION:  dumbbell, equal bridge lengths, well on DECOY, strong coupling to DRUG
VERIFICATION:  must score DRUG > DECOY
RESULT:        [OBSERVED] AUC(→DRUG) = 0.000, AUC(→DECOY) = 1.000 (5 seeds)
VERDICT:       FALSIFIED as a communication measure.
               RETAINED-NARROWED as a structural-prior / cryptic-pocket detector.
```

**The question is never "does it work?" It is "what else would produce this exact number?"**

---

## 6. Proposed new operator — mode co-participation

The correct formalisation of the "is the minimum reachable from the active site?" intuition.
Not tunnelling (which does not occur) but **joint amplitude in the same low-energy modes** —
the textbook definition of a communication channel: a soft collective mode spanning both
sites.

```
CP(target) = Σ_{k ∈ low modes}  ( Σ_{i ∈ active} v_k(i)² ) · ( Σ_{j ∈ target} v_k(j)² )
```

- **Seed-dependent** (it references the active site explicitly).
- **Tracks coupling, not wells**: DRUG/DECOY ratio **489.9×** in the conflict cell C2, where
  GSR scores 0.000.
- **Cheap**: one `eigh`, already computed.
- **Naturally thermally filterable**: restrict the mode sum to E_k − E_0 ≲ kT — this is the
  correct home for the "which modes are thermally operational" idea, and it is a real filter.

**Note on "buckshot seeding" (considered, and recommended against).** Because GSR converges
to a seed-free answer, seeding it from many sites merely re-derives the ground state N times.
The only seed-dependent content is c₀ = ⟨v₀|p₀⟩, and mapping c₀ over all seeds simply
reconstructs v₀ — which one diagonalisation already gives for free. **The
co-participation matrix is the cheap, correct version of the "map the energy-surface
connectivity" instinct: spectral, not stochastic, and O(one eigh).**

---

## 7. Task breakdown and ordering

Numbering to be assigned by the Architect thread. Ordered by **time-to-result**, because the
deadline rewards a defensible number over a complete one.

### Tier 1 — do immediately (unblocks everything; ~1–2 days)

- **T-A · Dumbbell negative-control test suite.** Implement the 2×2 control matrix (§2) as a
  permanent test module. Ground truth is by construction; no PDB, no network access; runs in
  seconds. Assert: GSR follows the well (C2 → AUC ≈ 0 on the coupled lobe); CTQW/ENAQT follow
  the coupling. *This is the regression test that would have caught the finding, and it is
  the negative control for every future operator.* **Dependency: none. Start here.**
- **T-B · Re-frame GSR / BCR_ABL1 in `RESULTS.md` and the methodological report.** Change the
  claim from "allosteric signal propagation" to "apo-computable structural prior for cryptic
  pockets," with the falsification evidence cited. Remove the classical-vs-quantum framing.
  **Cheap, and it stops a false claim entering the submission.**
- **T-C · ENAQT γ-sweep on real targets.** Replaces the killed TASK-0091. Measure transport
  from the active site to the labelled pocket vs γ ∈ [10⁻⁴, 10²]; report the **interior
  optimum and the enhancement ratio over the coherent walk (γ→0)**, *not* AUC recovery.
  Apply the proximity floor. **Highest scientific upside in the repo.**

### Tier 2 — the new science (~2–4 days, runs after T-A lands)

- **T-D · Implement `mode_coparticipation` as a first-class operator** (§6), with the thermal
  filter (E_k − E_0 ≲ kT). Register it, and — mandatorily — pass it through the T-A control
  matrix before any target is scored with it.
- **T-E · Falsification-template sweep of the existing register.** Apply the §5 template to
  **every** operator/propagator already in `ALGORITHM_REGISTER`: name the confound, construct
  the disagreement case, record RETAINED / RETAINED-NARROWED / FALSIFIED. Expect casualties;
  that is the point. *An honest register with three surviving operators beats a register of
  thirteen unfalsified ones.*
- **T-F · ENAQT noise-robustness → the NISQ story.** Connect T-C's interior optimum to the
  challenge's "noise resilience" objective: coarse-grain (`coarse.py`) to a NISQ-feasible
  node count, Trotterise, and show the ENAQT advantage survives gate noise. This is the
  hardware narrative, now backed by measurement rather than framing.

### Tier 3 — mechanism (valuable, not on the critical path)

- **T-G · APO/HOLO well-migration diagnostic.** Does the well move on ligand binding? Strictly
  `ceiling_context` (holo-requiring ⇒ never predictive). Correlate migration with soft modes /
  B-factors / rigidity. If positive, this is the result that justifies the `H_new` construction.
- **T-H · Intermediate-deformation trajectory.** Morph apo→holo and track well migration
  against the ENM mode coordinates. Follows T-G.

### Ordering rationale

**T-A first, unconditionally** — it is fast, it has no dependencies, and until it exists every
subsequent operator claim is unfalsifiable. **T-B is nearly free** and removes a false claim
from the submission. **T-C is the bet**: it is the only surviving genuinely-quantum,
genuinely-communication-measuring line, and it maps onto a scored objective. Tier 2 broadens
the science; Tier 3 explains it.

If time collapses to a single week: **T-A → T-B → T-C**, and report the honest competence map.
A well-evidenced *"our GSR result is a structural prior, our CTQW result is proximity, and our
one genuine quantum-transport effect is ENAQT with a measured interior optimum"* is a stronger
submission than an unfalsified 0.779.
