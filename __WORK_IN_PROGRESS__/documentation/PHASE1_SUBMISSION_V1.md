# Quantum Allosteric Scanner — Phase 1 Proposal

**Global Quantum + AI Challenge 2026 · Phase 1 Ideation · Team AuraQu**

> The benchmark cannot certify what the challenge asks. Here is the measurement
> that shows it, and the specification for one that could.

| | |
|---|---|
| **Draft** | v1 |
| **Date** | 2026-09-07 |
| **Deadline** | 2026-09-15 · 8 days |
| **Format** | 6pp + 3pp appendix + repo link |
| **HTML twin** | `documentation/PHASE1_SUBMISSION_V1.html` — published at https://claude.ai/code/artifact/c603f27a-ce03-47d5-b236-97719048263a |

> **Content parity**: `documentation/PHASE1_SUBMISSION_V1.html` and `documentation/PHASE1_SUBMISSION_V1.md` carry the same
> content. Edit both, or regenerate one from the other — two drifting copies of
> a submission is the failure mode that produced TASK-0307. Verified by
> `.ai/tools/doc_parity.py`.

---

## What this document is

This draft is restructured onto the seven-item table of contents mandated by
Guidelines §4.3 — *not* the six assessment criteria the previous draft was
organised around. A reviewer following the Guidelines would have looked for
item 4 in that version and not found it. What is still unfinished is marked as
such — we would rather show visible holes than plausible filler.

---

## 1. Problem Framing

*Guidelines §4.1 — "why quantum or quantum-AI methods offer a credible advantage
**or novel insight**"*

**What is actually quantum here: a real coherent process used as a modelling
language, not an asymptotic advantage.** §4.1's formulation is disjunctive; we
take the **insight** disjunct, not the advantage one. We identified nine
candidate quantum-advantage routes and closed all nine by measurement — our
principal finding, not a result we work around.

**Cryptic and allosteric are orthogonal properties, not conflated here.**
Cryptic = absent from the apo structure, opens only on binding. Allosteric =
distal from the active site. Our three mandated targets combine them
differently:

| Site | Allosteric | Cryptic |
|---|---|---|
| BCR-ABL1 myristoyl pocket | yes | **no** |
| KRAS_G12C switch-II pocket | yes | **yes** |
| Cardiac myosin (mavacamten site) | yes | **no** — not even a single-molecule property (Appendix C) |

The cryptic class is the most valuable unexploited drug-discovery target,
absent from apo structure by definition; the challenge asks for a method that
finds such pockets from apo alone. We implemented it in full — §4.1's own
specification, a continuous-time quantum walk on the residue contact network
seeded at the active site — then **audited whether the benchmark can certify
the answer.** It cannot, for three reasons — plus one finding this audit
surfaced along the way: a collaborator's independent 1233-protein unified
benchmark measured **median hop = 0** for the field's own cryptic-pocket
datasets — cryptic pockets are not, on the whole, distal. **Cryptic ≠ distal,
now measured**, a real finding independent of ours.

### Finding 1 — two of three mandated targets cannot express the challenge's own contrast

A blind, pre-registered validity rule (apo closed, holo open, ligand stripped,
fpocket druggability) applied to every target with a real drug ligand:

| Target set | Source | Valid |
|---|---|---|
| KRAS_G12C, BCR-ABL1, Cardiac Myosin | Table 1, mandated | **1 of 3** |
| PTP1B, glucokinase, caspase-1, caspase-7 | §6's recommended database | **1 of 4** |

**We did not select the failing targets** — Table 1 and §6's own source did.
The mandated gate operates at **1/3 validated coverage**, systemic across both
sources.

**c-Myc (1NKP)**, the challenge's separately-named fourth target, has no
drug-bound structure — cannot carry the contrast by construction. Ran a
4-operator consensus instead (`results/MYC_MAX/`, agreeing on residue 943);
no ground truth to score against, reported plainly.

### Finding 2 — two of the failures are previously unreported

A ligand holds the "apo" pocket open at three sites — one is not unexplained.
BCR-ABL1's `1OPL` carries `MYR` (myristate, **75%** overlap): the physiological
autoinhibitory ligand of that pocket (Nagar et al. 2003), the mechanism we
claim to chase, not a contaminant — asciminib is a myristate mimetic for the
same pocket. GLUCOKINASE's `1V4S`/`MRK` (**88%**) and PKR's `7FS3` (**92%**)
remain genuinely unexplained. None of the three is apo at the site of
interest — one consequence, two causes.

### Finding 3 — the quantum observable's apparent signal is geometry

Walk occupation scores AUC 0.5921 on 108 structures — conditioned on distance
to the active site, it falls to **0.5184, not significant**. ~80% of the
signal was inherited proximity. Published unconditioned, retracted four days
later (Appendix B).

---

## 2. Technical Approach

*Guidelines §4.3 item 2 — the **proposed** method, and the paradigm, stated in terms*

### Paradigm

**Quantum-inspired, classically-simulable.** Single-particle continuous-time
quantum walks on a residue contact graph are efficiently simulable classically;
no asymptotic speedup is claimed. We used the quantum formalism as a
*modelling language* for coherent, interference-carrying transport, then
measured what it can and cannot express — stated plainly, not a hedge.

We are **not** proposing QAOA on a protein: side-chain packing at pocket scale
is a pairwise MRF, treewidth 2–5, solved exactly in 0.001–0.159s against a
naive 10^14 search space. A hard regime exists only at ~50–80 residues, most
of a domain, not a pocket.

### What we propose to build

**A benchmark-and-instrument proposal using a quantum-inspired method as its
first test subject, not a method paper with a benchmark attached.** §1's
instrument-failure applies to any method, quantum or classical — the PoC
that moves the field is the validated instrument, applied first to our own
walk, built to apply equally to any competing submission.

| Component | What it does | Evidence motivating it |
|---|---|---|
| (a) Certifying cryptic-pocket benchmark | Blind validity rule + endogenous-ligand audit + positive control + measured detection limit, at scale | 5 of 7 standard targets fail; the field uses them regardless |
| (b) Screening criterion for the hard regime | Decidable *from apo alone* | Coupled search: 20% of restarts for KRAS_G12C, 0/65 for PTP1B — two valid targets disagree, n=2 cannot adjudicate |
| (c) Apo vs stripped-holo delta | Isolates what cryptic-pocket prediction actually depends on | Published propensity reports 89.8%/98.1% on ASBench/CASBench, but those evaluate *ligand-removed holo*, not apo — never reported to our knowledge |

### What we already have — four positive results

Criterion 1 reads badly for a mostly-negative submission; Criterion 2
(evidence and validity) is our actual strength.

**1. A validated upper bound, within one feature span, on what the apo
contact graph expresses** — not a "ceiling"; that overclaims. Gradient-
boosted fit, 19 scalar functionals, LOPO over 74 clusters: **residualised
AUC 0.5949 mean / 0.6203 median, p=3.3×10⁻⁶**, holding at **0.6017** with
proximity deleted outright — tested, not argued away. Upper bound *within
that span*, not a GNN-foreclosing lower bound. Cold-clone reproducible
byte-for-byte (`0.5948718035160693`) — a direct Criterion-2 asset.

**2. A measured mechanism for why the walk fails.** Hit-rate anti-correlates
with true-pocket distance — cluster-robust: **7/8 pre-registered
combinations clear a cluster-permutation test** (rho −0.34 to −0.50,
22–55 clusters, p=0.004–0.038, one borderline p=0.058). PASSer specificity
control shows no such correlation (p=0.09–0.99) — not "distal is just
harder." A stronger claim than the failure alone.

**3. The evaluation cohort tests the wrong thing — three independent
measurements.** Most ASBench/CASBench "allosteric" pairs are not distal; on
a genuinely distal ~45-structure subset our own design cannot even detect
its own dominant confound (p=0.89) — cannot rule anything in or out.
Separately, ~30% of pairs are covalently adjacent (no signal by
construction), and every one of 40 ASBench structures sampled is
ligand-bound at the scored site. Carries with the ligand-contamination
caveat wherever ASBench is cited.

**4. A stricter null changes which findings survive.** A spatially-compact
pocket-block null (matching the real positives' own 1–3-pocket
concentration) is far stricter than our default uniform null: BH-FDR 5%
survivors fall 45/110→**0/110** primary, 33/80→1/80 veto-corrected — a
reusable methodological contribution independent of any target's biology.

---

## 3. Feasibility & Resource Requirements

At full resolution — one qubit per residue, the convention every number in this
document uses — the register needs **169–704 qubits and 3.3M–124.9M two-qubit
gates**. Louvain coarse-graining to a NISQ-plausible 10–15 qubits destroys most of
the ranking signal (retention Jaccard 0.00–0.18) without reaching hardware-usable
fidelity.

Against a real IBM device calibration snapshot, every mandatory target verdicts
**`FAULT_TOLERANT_ONLY`**, at both resolutions. We checked both hardware routes
named in the challenge's own bibliography; neither changes this picture. AWS
Braket and Classiq access were separately confirmed with the organisers as a
Phase-2-only benefit, not required or available for Phase 1 — irrelevant to
the verdict above either way, which is set by qubit count and circuit depth,
not by choice of NISQ cloud provider.

This is why the proposal in §2 is classical-plus-quantum-inspired rather than
hardware-targeted. The resource picture was measured before the framing was
chosen, not after.

**Data, compute, and software, stated rather than assumed.** Data: public
apo/holo PDB depositions plus two external field benchmarks (ASBench,
CASBench) for cohort scale — no proprietary or synthetic structures, and
every cohort's own contamination and coverage limits are audited in §1 and
Appendix C rather than assumed clean. Compute: classical throughout —
ENM ensemble generation, contact-graph construction, and the quantum-inspired
walk's own classical simulation all run on commodity CPU hardware, the
largest single analysis (105-structure feature extraction) completing in
under two hours on one machine, containerised and reproducible from a cold
clone. Software: Python/NumPy/SciPy for the operator and propagator math,
`fpocket` for candidate pocket detection, and standard structural-biology
tooling (BioPython, ProDy) for parsing — no bespoke or unavailable
dependency the field does not already use. **Constraint carried forward
from §1**: the method's ceiling is set by benchmark validity, not compute
budget — more hardware does not fix a target that fails the apo/holo
contrast by construction.

---

## 4. Expected Impact

*New section — absent from the previous draft, mandated by §4.3*

**What a successful PoC would demonstrate:** that cryptic-pocket method claims
in this field are currently uncertifiable, and that a validated instrument
changes which published results survive.

Cryptic allosteric sites matter clinically as the route to targets orthosteric
chemistry cannot reach — active sites too polar, shallow, or conserved for a
selective ligand. Asciminib is the existence proof: a myristoyl-site inhibitor
(§1, Finding 2) retaining activity against resistance mutations that defeated
four generations of orthosteric BCR-ABL1 inhibitors. The scarcity of more
asciminibs is not absent sites — it is that we cannot tell a real one from a
scoring artefact prospectively, on a protein where the answer is unknown. That
is the capability this instrument certifies.

| Target | Quantitative goal | Baseline today |
|---|---|---|
| Certified apo/holo pairs | ≥ 40 pairs passing the blind validity rule | 7 audited, 2 pass |
| Apo vs stripped-holo delta | Reported for ≥ 100 structures | Never reported |
| Combined readout | Residual AUC ≥ 0.60, LOPO, with a null | 0.6203 median, null passed |
| Re-audit of published claims | The 84% headline decomposed | Done: a six-way disjunction |

The last row is the shape of the impact: the field's leading figure, 84%
recovery, is **99/118 structures detected by *at least one* of six measures**
— ≥3/6 drops it to 57.6%, all 6 to 17.8%. Real and correctly computed; not
what a reader assumes.

---

## 5. Validation Plan

*Guidelines §8 calls this "one of the strongest differentiators"*

Already built and in use, not proposed:

- **Proximity floor** — every score must beat the strongest trivial baseline
  (degree, hop, Euclidean distance from seed).
- **Spatially-correct nulls** — three generations, each fixing a measured
  defect in the last.
- **Positive control with a measured limit of detection** — planted,
  confound-orthogonal; corrected null, no target reaches 80% power to ~4×
  background conductance.
- **Cluster-robust inference by structure** — exact cluster-level permutation,
  after four selection procedures died of pseudo-replication.
- **Program-level multiplicity budget**, with its redundancy correction and
  own limit.
- **Firewall / frozen-context provenance** — an unforgeable stamp against a
  claimed-frozen result rendering unbannered.

**Added asymmetrically applied only after we noticed the gap**: a mandatory
*negative* control alongside every positive one — we had verified tests detect
signal, never that they refuse noise, and that omission produced a false
headline last week. §2's positive result 1 carries a permuted-label null;
running it is what promoted that result from a lead to a finding.

---

## 6. Hybrid / Cross-Domain Architecture

Classical ENM ensemble generation → quantum-inspired transport subroutine →
classical verification (fpocket druggability, proximity floor, null). One
runner emits all three artefacts, so they cannot disagree.

```
 Apo structure                                                Three artefacts,
      │                                                        one runner
      ▼
┌─────────────────┐    ┌──────────────────────┐    ┌───────────────────────┐
│ Classical ENM    │───▶│ Quantum-inspired      │───▶│ Classical verification │
│ ensemble         │    │ transport subroutine  │    │ (fpocket druggability, │
│ generation       │    │ (continuous-time walk)│    │  proximity floor, null)│
└─────────────────┘    └──────────────────────┘    └───────────┬───────────┘
                                                                 │
                                    ┌────────────────┬───────────┴──────────┐
                                    ▼                ▼                      ▼
                           Connectivity matrix   Site-level hit list   This report
```

> **Confirmed, not hypothetical: the shipped demo (`main` branch) reports raw
> occupation P@5 with no proximity floor**, on an observable found to be ~80%
> proximity once conditioned (§1, Finding 3) — checked directly against
> `main`'s deployed code; `keepalive.yml` keeps that demo live, so a judge
> clicking through is not hypothetical. Reconciling it is tracked, not yet
> done — disclosed because finding it unaided would cost more than naming it.

---

## 7. Team Capability

Three people, spanning the disciplines this problem requires.

| Member | Discipline | Role here |
|---|---|---|
| **Oussema Turki** | Quantum algorithms | Operator design, propagator formulation |
| **Berke Turkaydin** | Computational biophysics / structural chemistry | Target selection and mechanistic classification, structural validity auditing, ensemble and free-energy methodology, biological interpretation |
| **Bartosz Chmura** | PhD, molecular photophysics · 14 years software quality assurance | Scope and narrative decisions, verification methodology |

Full biographies, prior work, and quantum-computing experience are in the
separate Team Profile (§4.1) — not part of this 6-page proposal.

**One methodological commitment explains this document**: fourteen years of
software QA applied to a scientific register — separation of the party that
builds from the party that verifies, a negative control alongside every
positive one. Five self-found retractions in seven days (Appendix B) are the
evidence. The register was produced by a role-separated AI workflow, with the
reviewing role deliberately assigned to a different model from the
implementing one — disclosed in full in the Team Profile and the public
repository, not minimised. This is a Quantum *and AI* challenge that permits
AI involvement; the traces of human-in-the-loop decisions there are the
evidence behind every capability claim here.

---

# Appendix A — Claims ledger

Every load-bearing claim, with its current verdict as of 2026-09-02. Compact by
design — full methodology, code, and the surrounding argument for every row are
in the public repository (§7), linked per §4.4.

**Verdict key:** HOLDS · QUALIFIED · RETRACTED · UNDETERMINED

| Claim | Verdict | Evidence |
|---|---|---|
| No single observable survives conditioning on proximity — 7/7 tested | **HOLDS** | Best residual `persistent_h2_void` +12.0%, p=0.107 uncorrected, n=45/108. `dcc_low`'s one nominal hit is **negative** (0.4445). |
| Walk occupation is **80% proximity** | **HOLDS** | +18.4% raw → +3.7% residualised = 80.0% shrinkage. ρ(occupation, proximity)=+0.735, reproduced to 4dp independently. |
| P@5 = 0.000 on all three mandatory targets | **HOLDS** | Deployed operator, re-run after a stale-artifact fix. |
| Nothing we have beats random at P@5 (108 structures) | **HOLDS** | Design has power: field's own propensity beats random at p=5×10⁻⁹. |
| The published 84% is a six-way disjunction | **HOLDS** | 99/118; ≥3/6 → 57.6%; all 6 → 17.8%. |
| 5 of 7 standard targets fail a blind validity audit | **HOLDS** | 1/3 mandated + 1/4 recommended-database targets valid. Separate 29-deposition audit supplies two previously-unreported mechanisms. |
| Instances are not computationally hard | **HOLDS** | Fixed backbone: treewidth 2–5, <0.16s exact. Coupled: median 5, max 7 — below the ~50–80-residue hard regime. |
| Hardware verdict is `FAULT_TOLERANT_ONLY` | **HOLDS** | Both resolutions, real device calibration. |
| No structural descriptor predicts which method suits which protein | **HOLDS** | Size, chains, fold class, site separation all null against a working positive control. |
| Combined readout reaches residual AUC 0.5949 mean / 0.6203 median | **HOLDS** | 105 structures/74 proteins LOPO, cluster-robust p=1×10⁻⁵. Positive control 0.5000 exactly; negative control z=8.69, 0/100. Holds at 0.6017 proximity-excluded, cold-clone reproducible. Upper bound within a 19-feature span, one cohort. |
| Hamiltonian potentials carry residual signal, but do not beat geometry | **QUALIFIED** | Residualised: 0.740→0.660, p=0.027. Head-to-head: loses, 0.751 vs 0.795, p=0.29 (matched-unfitted: 0.599 vs 0.575). |
| The quantum contribution is larger than 5–10% (Shapley) | **RETRACTED** | Withdrawn 2026-09-01 — unconditioned AUC inflated it. |
| The site-distance distribution is a continuum, no discrete classes | **RETRACTED** | Too little power at the relevant separation (~40% at n=26); the SD-unit basis was also wrong. |
| Whether that distribution is multimodal | **UNDETERMINED** | Both available tests were miscalibrated, in opposite directions. |

---

# Appendix B — What we retracted, and how fast

Team-capability evidence for §7: found by our own adversarial review, not a
referee, each committed with a dated message stating the error against ourselves.

| Date | Retraction | Found by |
|---|---|---|
| 2026-08-26 | KRAS_G12C's "apo" structure was drug-bound; 8/10 replacement candidates too. Re-run got worse. | Live re-verification |
| 2026-09-01 | Quantum arm's +18.4% is 80% proximity (residualises to +3.7%, n.s.). Withdrawn same day. | Confound test |
| 2026-09-01 | Best constructive number was never compared against the strongest baseline. Loses to it. | Reviewer audit |
| 2026-09-01 | A directional "quantum" effect was a category error — operator symmetric to machine precision. | Reviewer audit |
| 2026-09-02 | Multimodality headline rested on a test rejecting unimodal data 52–68% of the time. | Negative control |

---

# Appendix C — Known defects, disclosed

Phase-2 criteria explicitly score whether constraints are *"honestly assessed."*
These are findable by any referee reading our repository, so we name them first.

- **No family-wise multiplicity control** across ~50 analyses. No surviving
  claim sits below p=0.019 — a large unrecorded family, not a robust effect.
- **Two incompatible "AUC" definitions** were in simultaneous use; one silently
  flips sign on anti-correlated features. Directional value now reported beside
  every solo figure computed that way.
- **Negative controls were omitted systematically** until two days ago,
  producing one false headline. Applied to §2's positive result 1; being
  retrofitted to the rest, most of which have still never faced one.
- **Modality is undetermined** — two tests, miscalibrated in opposite
  directions, produced our two contradictory verdicts.
- **ProteinLens has no number attached** — confirmed live, browser-only, no
  API. Flagged, not skipped.
- **The apo-ligand veto exception leaks**: the true pocket is **4.2×** more
  likely than an arbitrary candidate to survive *only* through it (13.5% vs
  3.2%, paired within-protein) — the exception uses ligand occupancy, adjacent
  to the label it should be blind to.
- **ASBench is PASSer's own training set, not held out**; CASBench is.
  Any ASBench-based PASSer comparison is contaminated in PASSer's favour.
- **One upstream null seed was not reproducible** (`hash()`,
  `PYTHONHASHSEED` unset). Deterministic-seed patch written, not yet landed.
- **Cardiac myosin's mavacamten site is not even a single-molecule
  property** (§1's taxonomy table) — a single apo chain cannot represent it,
  and it is carried here as a disclosed limitation rather than an ordinary
  benchmark target.

---

*Team AuraQu · Cleveland Clinic Quantum Allosteric Scanner*
*Draft v1 · 2026-09-07 · restructured onto Guidelines §4.3's seven-item ToC*
*Open: reconciling the live `main`-branch demo with §6's own disclosure · multiplicity budget across the register*
