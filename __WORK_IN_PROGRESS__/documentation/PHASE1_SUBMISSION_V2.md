# Quantum Allosteric Scanner — Phase 1 Concept Proposal

**Team AuraQu** · Unlocking Undruggable Targets: Quantum Simulation of Allosteric Signal Propagation

---

## 1. Problem Framing

Cryptic allosteric sites are the route to targets orthosteric chemistry cannot reach — proteins whose active sites are too polar, too shallow, or too conserved across a family to permit a selective ligand. Asciminib is the existence proof: a myristoyl-site inhibitor that retains activity against the ATP-site resistance mutations that defeated four generations of orthosteric BCR-ABL1 drugs. The reason there are not more asciminibs is not that the sites are absent. **It is that nobody can currently tell a real one from a scoring artefact, prospectively, on a protein where the answer is not already known.**

That is a measurement problem before it is a method problem, and it is where we spent Phase 1.

We built the method the challenge specifies — a continuous-time quantum walk on the residue contact network, seeded at the active site, ranking distal residues by transport — and then asked whether the field's benchmarks can certify its answer. **They cannot, and the same limitation applies to every competing method, quantum or classical.** Four measurements, each with a direct consequence:

**Cryptic and allosteric are orthogonal, and the benchmarks conflate them.** We assembled a unified 1233-protein benchmark across five public datasets and measured, for every annotated site, its graph distance from the active site. Only 23% of curated allosteric sites and 7% of drug-contact pockets are genuinely distal; the cryptic-pocket datasets have **median hop = 0** — their pockets sit essentially *on* the active site. *Consequence:* a method that searches distally is being scored on pockets that are not distal, so the benchmark rewards proximity. This is why every propagation method, ours included, is beaten by distance-to-the-active-site.

**Most standard targets cannot express the contrast they are used to test.** A blind, pre-registered validity rule — apo closed, holo open, ligand stripped, cavity re-scored — passes **1 of 3** mandated targets and **1 of 4** from the recommended database. We did not choose the failing targets; the challenge's own Table 1 and source database did. *Consequence:* where the apo structure already has an open pocket, "finding" it demonstrates nothing, and published success rates on those targets do not measure prediction.

**c-Myc (`1NKP`)**, the challenge's separately named fourth target, has no drug-bound structure in the PDB — it cannot carry the apo/holo contrast by construction, so the validity rule does not apply to it at all. We ran a four-operator consensus instead (`results/MYC_MAX/`; the operators agree on residue 943). There is no ground truth to score that consensus against, so we report it together with its lack of validation rather than as a performance number.

**"Apo" does not mean ligand-free, and the exceptions are not random.** We assumed apo depositions were empty at the site of interest. They are not: **3 of 7** audited targets have a ligand holding the pocket open, and **40 of 40** ASBench structures we sampled carry a bound ligand at the scored site. One case is mechanistically expected — BCR-ABL1's `1OPL` carries myristate, the physiological autoinhibitory ligand of that exact pocket. Two are unexplained: glucokinase `1V4S`/`MRK` (88% overlap) and PKR `7FS3` (92%). *Consequence:* the contamination correlates with the label — the most interesting targets are the ones most likely to be pre-opened — so it inflates measured performance rather than adding noise.

**Our own method fails this instrument, which is the honest test of it.** Walk occupation scores AUC 0.5921 across 108 structures. Conditioned on distance to the active site it falls to **0.5184, not significant** — roughly 80% of the apparent signal was inherited proximity. We published the unconditioned number and retracted it four days later.

**Our five guesses per target, and our own verdict on them.** The required hit list is five ranked residues per protein. For the three targets where a drug-bound structure exists to check against, we also report what our own validation says about them — which is that none is distinguishable from chance:

| Target | Top five residues | Residue-level AUC | Our verdict |
|---|---|---|---|
| KRAS_G12C (`4LDJ`) | 31, 122, 33, 121, 29 | 0.514 | `NO_SIGNAL_IN_APO` |
| BCR-ABL1 (`1OPL`) | 402, 311, 310, 301, 338 | 0.541 | `NO_SIGNAL_IN_APO` |
| Cardiac myosin | 682, 683, 681, 680, 133 | 0.548 | `NO_SIGNAL_IN_APO` |
| c-Myc (`1NKP`) | 943, 246, 925, 226, 243 | — | no ground truth; 4-operator consensus |

All three floor confidence intervals include the observed score. **We submit the five as required and state plainly that we cannot certify them** — the conclusion this proposal reaches about the field's published numbers, applied to our own.

**What `NO_SIGNAL_IN_APO` means.** It is our own diagnostic verdict, not a crash: the score's confidence interval overlaps that of the best trivial baseline computed on the same structure. It says the apo contact graph, as we encode it, carries nothing about that pocket beyond what distance already supplies.

**Why we report numbers this close to chance, and claim nothing beats them.** Because the alternative is reporting a selection artefact. On any single protein we can find an operator and score that look excellent — with thirteen operators and seventeen scores there are 221 chances per target, and reporting the best of them is ordinary practice in this field. We did exactly that early on and it produced a headline we retracted four days later. Under matched multiplicity across 276 protein families, **no arm clears more than 5 — ours or any classical baseline — and they are statistically indistinguishable from each other** (McNemar p = 1.0). The near-chance numbers above are what survives that correction. A method can be made to fit one protein; what none of ours does, quantum or classical, is generalise across the ensemble.



---

## 2. Technical Approach

### Paradigm

**Quantum-inspired, classically simulable.** Single-particle continuous-time quantum walks on a residue contact graph simulate efficiently on classical hardware; we claim no asymptotic speedup. The formalism is used as a *modelling language* for coherent, interference-carrying transport. We are explicitly not proposing QAOA on a protein: side-chain packing at pocket scale is a pairwise Markov random field of treewidth 2–5, solved exactly in 0.001–0.159 s against a naive 10¹⁴ configuration space. A genuinely hard regime appears only at ~50–80 coupled residues — most of a domain, not a pocket.

### The physical hypothesis, and what we did to it

A classical random walk sums probabilities over paths; a quantum walk sums amplitudes, so paths can interfere. The hypothesis worth testing is that **interference between propagation paths distinguishes allosterically coupled residue pairs from merely nearby ones** — that coherence carries coupling information distance does not.

We tested it, in the strongest forms we could construct:

| Construction | Why it should have worked | Result, conditioned on proximity |
|---|---|---|
| Converged CTQW on `H_new` | The specified method: contact Laplacian + five chemical/structural potentials | AUC 0.5921 → **0.5184** |
| Chiral walk (Peierls phases) | Broken time-reversal symmetry gives a circulating component **orthogonal to radial flow by construction** — the strongest available prior for a proximity-independent observable | **0.4960 — below chance** |
| Engineered dephasing (ENAQT) | Environment-assisted transport is where coherence demonstrably helps in photosynthetic complexes | Relaxes toward the classical/proximity limit |
| Spectral coherence, entanglement entropy | Direct coherence measures rather than occupation | 0.5226, 0.4903 |

**The mechanism behind the null is measured, not assumed.** The converged walk's transfer matrix has row entropy at 0.86–0.89 of maximum and near-full numerical rank: it has equilibrated. Only 11–14% of the possible seed conditioning survives, and what survives is 0.63–0.79 anti-correlated with hop distance. **It is a distance measure with extra steps** — and we can show this is not a tuning failure, because the pipeline's hit rate anti-correlates with true-pocket distance in 7 of 8 pre-registered cluster-permutation tests (ρ −0.34 to −0.50, 22–55 clusters, p = 0.004–0.038), while a machine-learned pocket predictor scored on the identical pockets shows no such correlation (p = 0.09–0.99). The walk degrades with distance; the classical baseline does not.

We also ran the full ensemble end to end — thirteen operators × seventeen scores, with a cryptic-opening veto — over 1022 proteins. Under matched multiplicity, one candidate set and a matched null, **no arm clears more than 5 of 276 protein families, and quantum and classical arms are statistically indistinguishable** (McNemar p = 1.0).

**Our honest position: single-particle coherent transport on a static contact graph is exhausted.** We closed nine candidate advantage routes by measurement. A remaining quantum route must supply something the static graph does not have — either a true many-body object (conformational search, whose hard regime we have located at 50–80 residues) or dynamics rather than one structure. We would rather state that than propose a tenth variant of a construction we have already falsified four ways.

### What we propose to build in Phase 2

**A certifying instrument, with our own method as its first test subject.** The instrument-failure in §1 applies to any method; the deliverable that moves the field is the validated benchmark, built to apply equally to a competing submission.

| Component | What it does | Why it is needed |
|---|---|---|
| **(a) Certifying cryptic-pocket benchmark** | Blind validity rule, endogenous-ligand audit, positive control, measured detection limit, at scale | 5 of 7 standard targets fail the contrast; the field uses them regardless |
| **(b) Apo vs stripped-holo delta** | Isolates what cryptic-pocket prediction actually depends on | Leading methods report 89.8%/98.1% on ASBench/CASBench, but evaluate *ligand-removed holo*, not apo. We have found no report of the delta |
| **(c) Screening criterion for the hard regime** | Decides *from apo alone* whether a target needs many-body treatment | Coupled search fires for 20% of KRAS_G12C restarts and 0 of 65 for PTP1B — two valid targets disagree, and n = 2 cannot adjudicate |

Component (b) is ~27 minutes of compute over 100 apo/holo pairs and half a day of scripting against pairs we have already identified. We expect to report it before Phase 2 begins rather than propose it.

---

## 3. Feasibility & Resource Requirements

**Hardware, measured rather than assumed.** At one qubit per residue — the convention behind every number here — the register needs **169–704 qubits and 3.3M–124.9M two-qubit gates**. Coarse-graining to a NISQ-plausible 10–15 qubits destroys the ranking signal (retention Jaccard 0.00–0.18) without reaching usable fidelity. Against a real IBM device calibration snapshot, every mandated target verdicts **`FAULT_TOLERANT_ONLY`** at both resolutions. We checked both hardware routes named in the challenge bibliography; neither changes this. AWS Braket and Classiq access were confirmed with the organisers as a Phase-2 benefit — irrelevant to a verdict set by qubit count and circuit depth, not by cloud provider. **This is why §2 proposes classical-plus-quantum-inspired rather than hardware-targeted work: the resource picture was measured before the framing was chosen.**

**Data, compute and software.** Public apo/holo PDB depositions plus five field benchmarks for cohort scale — no proprietary or synthetic structures, and every cohort's contamination and coverage limits are audited in §1 rather than assumed clean. Compute is classical throughout: ensemble generation, contact-graph construction and the walk's own simulation run on commodity CPUs, the largest single analysis (105-structure feature extraction) completing in under two hours on one machine, containerised and reproducible from a cold clone; the 1022-protein ensemble sweep needed a modest HPC allocation for a day. Software is Python/NumPy/SciPy, `fpocket` for candidate detection, and BioPython/ProDy for parsing — no dependency the field does not already use.

**The binding constraint is benchmark validity, not compute budget.** More hardware does not fix a target that fails the apo/holo contrast by construction.

---

## 4. Expected Impact

**What a successful PoC demonstrates:** that cryptic-pocket method claims in this field are currently uncertifiable, and that a validated instrument changes which published results survive.

The field's headline figure illustrates the gap. "84% recovery" is **99 of 118 structures detected by at least one of six statistical measures**. Requiring three of six drops it to 57.6%; requiring all six, to 17.8%. The number is real and correctly computed — it is simply not what a reader assumes it means. A certifying benchmark makes that distinction automatic rather than archaeological.

| Target | Quantitative goal | Baseline today |
|---|---|---|
| Certified apo/holo pairs | ≥ 40 pairs passing the blind validity rule | 7 audited, 2 pass |
| Apo vs stripped-holo delta | Reported for ≥ 100 structures | Not reported in the literature we surveyed |
| Combined readout | Residual AUC ≥ 0.60, LOPO, against a matched null | 0.6203 median, null passed |
| Re-audit of published claims | The 84% headline decomposed | Done — a six-way disjunction |

For Cleveland Clinic the value is a go/no-go instrument applied *before* committing chemistry to a predicted site: a prospective ranking that has survived a proximity floor, a spatially matched null and a cluster-robust test is a different object from one that has not, and today the two are reported identically.

---

## 5. Validation Plan

Built and in use, not proposed:

- **Proximity floor.** Every score must beat the strongest trivial baseline — degree, hop distance, Euclidean distance from the seed. This is what demoted our own headline result.
- **Spatially matched nulls.** Three generations, each fixing a measured defect in the last. The current pocket-block null matches the real positives' own spatial concentration; moving to it changed BH-FDR survivors from 45/110 to **0/110**.
- **Positive control with a measured detection limit.** Planted, confound-orthogonal signal — so a null result can be distinguished from an underpowered test. On a genuinely distal subset our design cannot detect even proximity (p = 0.89), so we report that it cannot adjudicate rather than reporting a false negative.
- **Cluster-robust inference.** Exact cluster-level permutation, adopted after four selection procedures in our own work died of pseudo-replication.
- **A negative control beside every positive one.** Added after we noticed the asymmetry: we had verified that our tests detect signal, never that they refuse noise. That omission produced a false headline, and closing it is what promoted our strongest result from a lead to a finding.

**Success criteria for Phase 2:** the instrument certifies ≥ 40 apo/holo pairs; a combined apo-only readout holds residual AUC ≥ 0.60 under LOPO against a matched null; and at least one published cryptic-pocket claim is confirmed or overturned by re-measurement.

---

## 6. Hybrid / Cross-Domain Architecture

Classical ENM ensemble generation → quantum-inspired transport → classical verification. One runner emits all three required artefacts, so they cannot disagree with each other.

```
 Apo structure                                              Three artefacts,
      │                                                       one runner
      ▼
┌──────────────────┐   ┌───────────────────────┐   ┌────────────────────────┐
│ Classical ENM    │──▶│ Quantum-inspired      │──▶│ Classical verification │
│ ensemble         │   │ transport subroutine  │   │ (druggability,         │
│ generation       │   │ (continuous-time walk)│   │  proximity floor, null)│
└──────────────────┘   └───────────────────────┘   └───────────┬────────────┘
                                                                │
                                   ┌────────────────┬───────────┴──────────┐
                                   ▼                ▼                      ▼
                          Connectivity matrix  Site-level hit list   Methodological
                                                                        report
```

The runner emits the three required deliverables in a single pass: the **connectivity matrix** (residue–residue transport), the **site-level hit list** (ranked candidate pockets, each carrying its proximity-floor and null verdict), and the **methodological report** (per-target provenance, controls run, and the cohort every claim was measured on). Because one pass produces all three, a hit list cannot disagree with the matrix it came from.

The rationale for the split is empirical: the classical stages carry the signal we can currently certify, and the quantum-inspired stage is the component under test. Keeping them separable is what allowed us to measure that the transport subroutine adds nothing beyond the classical baseline — a hybrid design that could not isolate its own quantum stage could not have found that.

---

## 7. Team Capability

| Member | Discipline | Role in this project |
|---|---|---|
| **Oussema Turki** | Quantum algorithms | Operator design, propagator formulation, ensemble sweeps |
| **Berke Turkaydin** | Computational biophysics / structural chemistry | Target selection and mechanistic classification, structural validity auditing, biological interpretation |
| **Bartosz Chmura** | Molecular photophysics; software quality assurance | Verification methodology, scope and reporting decisions |

Full biographies, affiliations and prior quantum-computing experience are in the separate Team Profile.

**One methodological commitment shaped this submission.** We used an AI-assisted workflow, which accelerates work and generates plausible errors at the same rate. So we built the register to catch its own failures: the role that implements is separated from the role that verifies and assigned to a different model, every positive control has a negative one, and every claim carries the cohort it was measured on. It found five of our own errors in seven days, including our headline result. We report that as evidence the method of working is sound, not as a credential — the full task history, including every retraction, is public at `github.com/Oussema-t/Quantum_allosteric-scanner` (branch `bartosz`).
