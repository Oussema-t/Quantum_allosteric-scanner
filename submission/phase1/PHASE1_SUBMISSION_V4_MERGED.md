# Quantum Allosteric Scanner — Phase 1 Concept Proposal

**Team AuraQu** · Unlocking Undruggable Targets: Quantum Simulation of Allosteric Signal Propagation

---

## 1. Problem Framing

Cryptic allosteric sites are the route to targets orthosteric chemistry cannot reach — proteins whose active sites are too polar, too shallow, or too conserved across a family to permit a selective ligand. Asciminib is the existence proof: a myristoyl-site inhibitor that retains activity against the ATP-site resistance mutations that defeated four generations of orthosteric BCR-ABL1 drugs [1,2]. The reason there are not more asciminibs is not that the sites are absent. **It is that nobody can currently tell a real one from a scoring artefact, prospectively, on a protein where the answer is not already known.**

That is a measurement problem before it is a method problem, and it is where we spent Phase 1.

We built the method the challenge specifies — a continuous-time quantum walk on the residue contact network, seeded at the active site, ranking distal residues by transport — and then asked whether the field's benchmarks can certify its answer. **They cannot, and the same limitation applies to every competing method, quantum or classical.** Five measurements, each with a direct consequence:

**Cryptic and allosteric are orthogonal, and the benchmarks conflate them.** We assembled a unified 1233-protein benchmark across five public datasets [4–6] and measured, for every annotated site, its graph distance from the active site. Only 23% of curated allosteric sites and 7% of drug-contact pockets are genuinely distal; the cryptic-pocket datasets have **median hop = 0** — their pockets sit essentially *on* the active site. *Consequence:* a method that searches distally is being scored on pockets that are not distal, so the benchmark rewards proximity. This is why every propagation method, ours included, is beaten by distance-to-the-active-site.

**Most standard targets cannot express the contrast they are used to test.** A blind, pre-registered validity rule — apo closed, holo open, ligand stripped, cavity re-scored — passes **2 of 7** targets — three mandated by the challenge's own Table 1 (KRAS G12C, BCR-ABL1, cardiac myosin) and four we drew from the Allosteric Database, the source the challenge directs participants to. Only KRAS G12C and PTP1B pass. We then ran the identical rule over 63 independent apo/holo pairs, where it passes **49%** — and the failures are not a trivial apo-versus-holo asymmetry: of the 32 that fail, 19 are pairs where no pocket is detected in either structure, 10 have an apo that is already open, and 3 are inverted. *Consequence, stated at the strength the data supports:* about half of apo/holo pairs cannot express the contrast at all, and **the mandated targets are markedly worse than average** — we selected the four database entries but not the three the challenge mandates, and the failure spans both sources. Where the apo structure already has an open pocket, "finding" it demonstrates nothing, and a success rate measured on such targets is not measuring prediction.

**c-Myc (`1NKP`)**, the challenge's separately named fourth target, has no drug-bound structure in the PDB — it cannot carry the apo/holo contrast by construction, so the validity rule does not apply to it at all. No ground truth exists to score it against, which is precisely what the challenge asks for here: a genuinely prospective prediction. We report a four-operator consensus (`results/MYC_MAX/`; the operators agree on residue 943) and label it **unverified** rather than presenting it as a measured result.

**Structures used, and why they deviate from Table 1.** We reported to the organisers that `4OBE`, the mandated KRAS G12C apo structure, is wild-type at residue 12 (GLY, not CYS). Their reply of 2026-08-26 answered three points, and we followed it in each case:

| target | structure | deviation, and the reason |
|-----|-------|------------------------------------------------------|
| KRAS G12C [14] | `4LDJ` (apo) | The organisers suggested `8S8C`. We checked it against the PDB and it is **holo** — MK-1084-bound — so it cannot serve as the apo half of an apo/holo contrast. We searched for a genuine apo G12C structure and verified `4LDJ` (residue 12 is CYS, no ligand at the site). |
| BCR-ABL1 | `1OPL` (apo), retained | Substitution was expressly permitted. We kept `1OPL` deliberately: its myristate occupancy is the finding, not a defect — it is how we established that "apo" depositions are not reliably ligand-free. Substituting it would have removed the evidence. |
| Cardiac myosin [15] | `8QYP` → `8QYR` | Our substitution, **accepted as primary** by the organisers. |
| c-Myc | `1NKP` | Mandated; no drug-bound structure exists, so the validity rule does not apply. |

All three deviations trace to that clarification, and the `8S8C` check is recorded in our configuration alongside the choice it produced.

**"Apo" does not mean ligand-free, and the exceptions are not random.** We assumed apo depositions were empty at the site of interest. They are not: **3 of 7** audited targets have a ligand holding the pocket open, and **40 of 40** ASBench structures we sampled carry a bound ligand at the scored site. One case is mechanistically expected — BCR-ABL1's `1OPL` carries myristate, the physiological autoinhibitory ligand of that exact pocket [3]. Two are unexplained: glucokinase `1V4S`/`MRK` (88% overlap) and PKR `7FS3` (92%). *Consequence:* the contamination correlates with the label — the most interesting targets are the ones most likely to be pre-opened — so it inflates measured performance rather than adding noise.

**And ligand-removed holo is measurably easier than apo — a gap we have found no report of.** The field's leading recovery figures, 89.8% on ASBench [4] and 98.1% on CASBench [5], are obtained on structures where the ligand is deleted from a holo deposition, not on genuine apo structures. Across 63 apo/holo pairs spanning 59 distinct proteins, cavity detection scores **+0.199 higher on the stripped-holo half than on the true apo half** (median +0.184; Wilcoxon p = 2.6e-4; sign-flip permutation p < 1e-4; bootstrap 95% CI [+0.102, +0.296], excluding zero by a wide margin), with the same sign in both source cohorts. *Consequence:* those headline numbers describe a task roughly 0.2 AUC easier than the one they are read as solving, and the difference is not a rounding detail — it is larger than the margin separating most published methods from each other. We report it at n = 63 pairs; the ≥ 100 the instrument should certify remains a Phase-2 target.

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

**Why we report numbers this close to chance, and claim nothing beats them.** Because the alternative is reporting a selection artefact. On any single protein we can find an operator and score that look excellent — with thirteen operators and seventeen scores there are 221 chances per target, and reporting the best of them is ordinary practice in this field. We did exactly that early on and it produced a headline we retracted four days later. Under matched multiplicity across 276 protein families — a *family* groups structures of the same protein, so one protein deposited many times counts once — **no arm clears more than 5 — ours or any classical baseline — and they are statistically indistinguishable from each other** (McNemar p = 1.0). The near-chance numbers above are what survives that correction. The size of that effect is measurable, not rhetorical: selecting the best operator-and-score combination per protein clears **137 families**, and the label-permutation null for the same selection clears **99.8** — roughly three-quarters of the headline is the selecting. A method can be made to fit one protein; **what none of ours does, quantum or classical, is generalise across the ensemble.**



---

## 2. Technical Approach

### Paradigm

**Quantum-inspired, classically simulable.** Single-particle continuous-time quantum walks on a residue contact graph simulate efficiently on classical hardware; we claim no asymptotic speedup. The formalism is a *modelling language* for coherent, interference-carrying transport. We chose it only after looking for a combinatorial core hard enough to be worth a quantum optimiser, and measuring where hardness begins rather than assuming it: side-chain packing at pocket scale is a pairwise Markov random field of treewidth 2–5, solved exactly in 0.001–0.159 s against a naive 10¹⁴ configuration space, so a quantum optimiser there would answer an already-solved problem. Hardness starts at ~50–80 coupled residues — most of a domain, not a pocket. That measured boundary, not a preference, is what sends the remaining quantum candidates toward many-body objects and conformational ensembles rather than single-structure optimisation.

### The physical hypothesis, and what we did to it

A classical random walk sums probabilities over paths; a quantum walk sums amplitudes, so paths can interfere. The hypothesis worth testing is that **interference between propagation paths distinguishes allosterically coupled residue pairs from merely nearby ones** — that coherence carries coupling information distance does not.

We tested it, in the strongest forms we could construct:

| Construction | Why it should have worked | Result, conditioned on proximity |
|---|---|---|
| Converged CTQW on `H_new` | The specified method: contact Laplacian + five chemical/structural potentials | AUC 0.5921 → **0.5184** |
| Chiral walk (Peierls phases) | Broken time-reversal symmetry gives a circulating component **orthogonal to radial flow by construction** — the strongest available prior for a proximity-independent observable | **0.4960 — below chance** |
| Engineered dephasing (ENAQT) | Environment-assisted transport is where coherence demonstrably helps in photosynthetic complexes | Relaxes toward the classical/proximity limit |
| Spectral coherence, entanglement entropy | Direct coherence measures rather than occupation | 0.5226, 0.4903 |

**The mechanism behind the null is measured, not assumed.** The converged walk's transfer matrix has row entropy at 0.86–0.89 of maximum and near-full numerical rank: it has equilibrated. Only 11–14% of the possible seed conditioning survives, and what survives is 0.63–0.79 anti-correlated with hop distance. **It is a distance measure with extra steps** — and we can show this is not a tuning failure, because the pipeline's hit rate anti-correlates with true-pocket distance in 7 of 8 pre-registered cluster-permutation tests (ρ −0.34 to −0.50, 22–55 clusters, p = 0.004–0.038), while a machine-learned pocket predictor [13] scored on the identical pockets shows no such correlation (p = 0.09–0.99). The walk degrades with distance; the classical baseline does not.

We also ran the full ensemble end to end — thirteen operators × seventeen scores, with a cryptic-opening veto [6] — over 1022 proteins. Under matched multiplicity, one candidate set and a matched null, **no arm clears more than 5 of 276 protein families, and quantum and classical arms are statistically indistinguishable** (McNemar p = 1.0). The family labels are inherited from the source datasets rather than imposed by a single clustering rule, so the absolute count depends on that convention; the comparison does not, because McNemar is a paired test over the same families.

**Prior art, and what is actually new here.** A continuous-time quantum walk on a residue interaction network was published in July 2026 [7] — the same construction we use, over ~150 proteins, with a small hardware demonstration. They report their walk-based centrality agrees with classical eigenvector centrality at Spearman ρ ≈ 0.95, and claim no quantum advantage. We ran the mandated ablation on our own cohort (105 structures, 74 proteins): correlation is markedly lower here (median ρ = 0.41, not ≈ 0.95); AUC is mixed, not uniformly null — we beat degree, eigenvector centrality and GNM-alone (p < 0.05) but tie betweenness and closeness (p = 0.50, 0.93). What that paper explicitly defers is the allosteric application, and that is where our contribution sits: active-site-seeded pathway scoring, apo/holo blind validation, and the benchmark-validity audit that occupies §1. The sponsor's own group has separately published a quantum binding-site structure prediction result [8] — VQE-based 3D backbone prediction for short (5–14-residue) fragments at already-located, orthosteric binding sites drawn from PDBbind complexes — so we make no claim that this domain is untouched by quantum methods. It assumes the site's location is already known and does not address pocket detection, apo-state structures, or allosteric (distal) sites. Cryptic-pocket and allosteric-site prediction specifically, as far as we can establish, remain untouched by quantum methods.

**We then closed the question directly.** The converged propagator we use is *provably phase-free* — a result we derived rather than inherited — so we built three observables to reach past it (chiral circulation, frequency-domain coherence, two-boson interference) and finally measured the thing itself: the **same** Hamiltonian, seed, cohort and scoring, run coherently and decoherently. Across 108 structures in 76 protein clusters the difference is **+0.0023 AUC, Wilcoxon p = 0.92, cluster-robust p = 0.83** — a well-powered null, not an underpowered one. Extending the cohort by 54 more distinct proteins (129 clusters, +70%) holds the same verdict: cluster-robust p = 0.42.

One ordering in that experiment is worth reporting, because it is not nothing. Correlation with distance-to-the-active-site falls monotonically across the three arms — classical diffusion **0.953**, decoherent walk **0.735**, coherent walk **0.692**. The walk is measurably less of a distance proxy than classical diffusion is. **What it adds is simply not coherence**, which is consistent with our centrality ablation: the walk beats the seed-blind baselines (degree, eigenvector, GNM alone) and ties the seed-aware ones (betweenness, closeness).

**Our honest position: the phase-free construction is exhausted.** We closed nine candidate advantage routes by measurement, then tested the natural tenth across its full delay range rather than at one point: a finite-delay, phase-sensitive amplitude $2\,\mathrm{Re}\langle r|e^{-iH\tau}|a\rangle$, the one construction that provably retains what the converged limit above discards. Scanned across eleven delays spanning five orders of magnitude — from deep short-delay, where the interference term is fully alive, through convergence, each set as a fraction of the Hamiltonian's own spectral-gap timescale — the signed observable, the one the external claim we are checking reports, carries no significant signal at any point (0/11, cluster-permutation p from 0.24 to 0.98). Its unsigned magnitude clears chance at exactly one of the eleven delays (p = 0.036) with no support at any neighbour, the signature of a selection artifact rather than a real band — confirmed by extending the cohort to 129 protein clusters, where that one point's significance washes out (p = 0.28) exactly as an artifact should and a real signal should not. This closes the tenth route: even a clean positive there would only have been a better observable, not a demonstrated advantage (a 2×2 permanent is exactly as easy as a 2×2 determinant). A remaining quantum route must supply something the static graph does not have. Two survive our own screening and we name them rather than imply a longer list: multi-particle interference, which becomes hard only at particle numbers far above the two that are tractable here, and coupled conformational search at that same 50–80-residue scale. Neither is a claim; both are stated with the hardware cost measured below.

### What we propose to build in Phase 2

**A certifying instrument, with our own method as its first test subject.** The instrument failure described above applies to any method; the deliverable that moves the field is the validated benchmark, built to apply equally to a competing submission.

| Component | What it does | Why it is needed |
|---|---|---|
| **(a) Certifying cryptic-pocket benchmark** | Blind validity rule, endogenous-ligand audit, positive control, measured detection limit, at scale | 5 of 7 standard targets fail the contrast; the field uses them regardless |
| **(b) Screening criterion for the hard regime** | Decides *from apo alone* whether a target needs many-body treatment | Coupled search fires for 20% of KRAS_G12C restarts and 0 of 65 for PTP1B — two valid targets disagree, and n = 2 cannot adjudicate |

A third component — the apo-versus-stripped-holo delta — was part of this instrument when we planned it. We ran it during Phase 1 instead of proposing it, and it is reported above; what remains to build is the certifying benchmark and the hard-regime screening criterion.

---

## 3. Feasibility & Resource Requirements

**Hardware, measured rather than assumed.** At one qubit per residue — the convention behind every number here — the register needs **169–704 qubits and 3.3M–124.9M two-qubit gates**. Coarse-graining to a NISQ-plausible 10–15 qubits destroys the ranking signal (retention Jaccard 0.00–0.18) without reaching usable fidelity. Against a real IBM device calibration snapshot, every mandated target verdicts **`FAULT_TOLERANT_ONLY`** at both resolutions. We checked both hardware routes named in the challenge bibliography; neither changes this. AWS Braket and Classiq access were confirmed with the organisers as a Phase-2 benefit — irrelevant to a verdict set by qubit count and circuit depth, not by cloud provider. **This is why §2 proposes classical-plus-quantum-inspired rather than hardware-targeted work: the resource picture was measured before the framing was chosen.**

**Data, compute and software.** Public apo/holo PDB depositions plus five field benchmarks for cohort scale — no proprietary or synthetic structures, and every cohort's contamination and coverage limits are audited in §1 rather than assumed clean. Compute is classical throughout: ensemble generation, contact-graph construction and the walk's own simulation run on commodity CPUs, the largest single analysis (105-structure feature extraction) completing in under two hours on one machine, containerised and reproducible from a cold clone; the 1022-protein ensemble sweep needed a modest HPC allocation for a day. Software is Python/NumPy/SciPy, `fpocket` [9] for candidate detection — interchangeable with any other detector, and the agreement measurement above is what would decide which — and BioPython/ProDy for parsing. No dependency the field does not already use.

**The binding constraint is benchmark validity, not compute budget.** More hardware does not fix a target that fails the apo/holo contrast by construction.

---

## 4. Expected Impact

**What a successful PoC demonstrates:** that cryptic-pocket method claims in this field are currently uncertifiable, and that a validated instrument changes which published results survive.

The field's headline figure illustrates the gap. "84% recovery" [4] is **99 of 118 structures detected by at least one of six statistical measures**. Requiring three of six drops it to 57.6%; requiring all six, to 17.8%. The number is real and correctly computed — it is simply not what a reader assumes it means. **The same shape reproduces in a second, independent domain**: across four pocket detectors (fpocket, PASSer, p2rank, PocketMiner) on one shared structure set and truth definition, 94.8% of structures are flagged by at least one, 24.0% by all four — driven by PocketMiner alone, whose own design (predicting which residues participate in a pocket that *opens*) answers a different question from the other three's static-cavity geometry, not by measurement noise. A certifying benchmark makes both distinctions automatic rather than archaeological.

| Target | Quantitative goal | Baseline today |
|---|---|---|
| Certified apo/holo pairs | ≥ 40 pairs passing the blind validity rule | **63 audited, 31 pass** (2 of the 7 standard targets) |
| Apo vs stripped-holo delta | Reported for ≥ 100 structures | **Done at n = 63 pairs: +0.199, CI [+0.102, +0.296]** |
| Combined readout | Residual AUC ≥ 0.60, leave-one-protein-out (LOPO), against a matched null | 0.6203 median, null passed |
| Re-audit of published claims | The 84% headline decomposed | Done — a six-way disjunction |

For Cleveland Clinic the value is a go/no-go instrument applied *before* committing chemistry to a predicted site: a prospective ranking that has survived a proximity floor, a spatially matched null and a cluster-robust test is a different object from one that has not, and today the two are reported identically.

---

## 5. Validation Plan

Built and in use, not proposed:

- **Proximity floor.** Every score must beat the strongest trivial baseline — degree, hop distance, Euclidean distance from the seed. This is what demoted our own headline result.
- **Protein-identity floor.** A second floor, which we found because we looked for it: replace every residue's score with its own protein's mean — destroying all information about *where* in the structure anything is — and pool across the cohort as a family-level metric ordinarily does. That constant-per-protein score reaches **AUC 0.65** (p < 5e-5), reproduced independently on 54 proteins added afterwards. Any AUC pooled across proteins must be reported against it. Per-structure metrics are immune by construction — a score that is constant within a structure is a tie inside that structure's own curve. **We audited every AUC in this document against that distinction rather than assuming it: each is computed per structure and averaged, none pooled across proteins.** A pooled figure without this floor is not interpretable, and we have found no report of the check.
- **Spatially matched nulls.** Three generations, each fixing a measured defect in the last. The current pocket-block null [11,12] matches the real positives' own spatial concentration; moving to it changed BH-FDR [10] survivors from 45/110 to **0/110**.
- **Positive control with a measured detection limit.** Planted, confound-orthogonal signal — so a null result can be distinguished from an underpowered test. On a genuinely distal subset our design cannot detect even proximity (p = 0.89), so we report that it cannot adjudicate rather than reporting a false negative.
- **A convergence check on the propagation time.** Not a detail: between a typical finite `T = 15` and the converged limit, **50 of 108 structures flip the sign of their verdict** (41 of 108 in the decoherent arm). A continuous-time walk reported at a fixed finite `T` without a convergence check is reporting a coin flip on roughly 40% of its cohort, and we have found no report of this check in the published lineage.
- **Cluster-robust inference.** Exact cluster-level permutation, adopted after four selection procedures in our own work died of pseudo-replication.
- **A negative control beside every positive one.** Added after we noticed the asymmetry: we had verified that our tests detect signal, never that they refuse noise. That omission produced a false headline, and closing it is what promoted our strongest result from a lead to a finding.

**Success criteria for Phase 2:** the instrument certifies ≥ 40 apo/holo pairs; a combined apo-only readout holds residual AUC ≥ 0.60 under LOPO against a matched null; and at least one published cryptic-pocket claim is confirmed or overturned by re-measurement.

---

## 6. Hybrid / Cross-Domain Architecture

Classical ENM ensemble generation → quantum-inspired transport → classical verification. One runner emits all three required artefacts, so they cannot disagree with each other.

**Pipeline.** Classical ENM ensemble generation → quantum-inspired transport subroutine (continuous-time walk) → classical verification (druggability, proximity floor, matched null). A single runner emits all three required artefacts in one pass — the **connectivity matrix** (residue–residue transport), the **site-level hit list** (five ranked residues, each with its proximity-floor and null verdict), and the **methodological report** (per-target provenance, controls run, and the cohort every claim was measured on) — so a hit list cannot disagree with the matrix it came from.

**Where the AI sits, and what it is worth.** Two random-forest models configure the quantum stage from protein topology alone — nine graph features, leave-one-family-out across 597 proteins in 380 families, each protein scored by a model that never saw its own family. The first predicts *how far from the active site to look*: it separates near from distal targets at AUC **0.793**, and running the walk at its predicted distance beats a single fixed choice across the cohort (**0.924** against 0.901), though it cannot pick the exact best distance among four (0.394 against a commonest-class baseline of 0.412). The second predicts *which operator and score to use*, and does not work: **0.625 against 0.630** for simply applying one fixed operator everywhere, 13 families against 15. We use the first, report the second as a negative, and draw the line where the measurement puts it — topology carries coarse information about where to look and essentially none about how to look.


The rationale for the split is empirical: the classical stages carry the signal we can currently certify, and the quantum-inspired stage is the component under test. Keeping them separable is what allowed us to measure that the transport subroutine adds nothing beyond the classical baseline — a hybrid design that could not isolate its own quantum stage could not have found that. Removing the classical pre-filters entirely makes the same point quantitatively: with every residue a candidate instead of roughly forty, the best classical ranker's strict hit count falls from **48 proteins to 6**, while its AUC *rises* (0.576 to 0.626). The pre-filter, not the ranker, performs the localisation — and AUC conceals that, because it is insensitive to how many candidates were on the table.

---

## 7. Team Capability

| Member | Discipline | Role in this project |
|---|---|---|
| **Oussema Turki** | Quantum algorithms | Operator design, propagator formulation, ensemble sweeps |
| **Berke Turkaydin** | Computational biophysics / structural chemistry | Target selection and mechanistic classification, structural validity auditing, biological interpretation |
| **Bartosz Chmura** | Molecular photophysics; software quality assurance | Verification methodology, scope and reporting decisions |

Full biographies, affiliations and prior quantum-computing experience are in the separate Team Profile.

**One methodological commitment shaped this submission.** We used an AI-assisted workflow, which accelerates work and generates plausible errors at the same rate. So we built the register to catch its own failures: the role that implements is separated from the role that verifies and assigned to a different model, every positive control has a negative one, and every claim carries the cohort it was measured on. It found five of our own errors in seven days, including our headline result. The full task history, including every retraction, is public at `github.com/Oussema-t/Quantum_allosteric-scanner` (branch `bartosz`).

## Appendix B — The walk, the operators, per-target connectivity, and the AI stage

A second pipeline on the `allosteric` track (PASSer detection, 630 proteins in 399 families [4-6]), reported as **replication** of sections 1-7's `bartosz` track (fpocket), not pooled with it. Every AUC is per structure, averaged.

**B.1 The construction.** Residues are C-alpha nodes, edges within a **10 A** C-alpha contact cutoff (`NET_CUTOFF`; drug-pocket truth uses a separate 4.5 A heavy-atom `SITE_CUTOFF`); the walk is `U(t)=exp(-iHt)` seeded at the active site, read as the converged average `p_avg(s->a)=sum_k |v_k(s)|^2 |v_k(a)|^2` -- a sum of squares, hence phase-free. The **connectivity matrix** `C_ij` (first required deliverable) is that average-mixing matrix, `(V o V)(V o V)^T`: symmetric, row-stochastic, operator-only. Thirteen operators (four weightings x three normalisations, plus `H_new = L_sym + diag(0.08 V_B + 0.16 V_T + 0.08 V_R + 0.04 V_C + 0.04 V_M)`) x seventeen scores give the 221 cells. `neg_dE`, the strongest single score, is time-independent and equals `sqrt(sum_j W_ij^2)` to machine precision -- a classical local statistic, so it cannot carry interference.

**B.2 Per-target connectivity.** Best and worst cell per target -- the three mandated (KRAS, BCR-ABL1, cardiac myosin) plus one additional allosteric target (HIV-1 RT, the NNRTI pocket) -- each selected across all 221 cells (13 Hamiltonians x 17 scores) by P@5, all seeded identically (consensus of fpocket druggability and PASSer allostery, top-10, MIN_HOP 2). Connectivity matrices and top-5 x active-site sub-blocks are in `results/connectivity/`.

| target (apo) | cell | operator / score | AUC | P@5 |
|---|---|---|---|---|
| KRAS G12C (`4LDJ`) [14] | best | `H_new` / resolvent | 0.809 | 0.6 |
| KRAS G12C (`4LDJ`) [14] | worst | `H11_aniso` / residual RAW | 0.184 | 0.0 |
| BCR-ABL1 (`1OPL`) [1-3] | best | `H6_exp` / residual+focus | 0.796 | **1.0** |
| BCR-ABL1 (`1OPL`) [1-3] | worst | `H5_gauss` / ratio p_peak/p_avg | 0.227 | 0.0 |
| Cardiac myosin (`8QYP`->`8QYR`) [15] | best | `H3_normL` / dX dip depth | 0.685 | 0.4 |
| Cardiac myosin (`8QYP`->`8QYR`) [15] | worst | `H8_gnm` / -dD mean | 0.068 | 0.0 |
| HIV-1 RT (`1DLO`->`3V81`, NNRTI) | best | `H14_anmP` / p_peak | 0.963 | 0.8 |
| HIV-1 RT (`1DLO`->`3V81`, NNRTI) | worst | `H14_anmP` / Green E=lmax | 0.196 | 0.0 |

*Table B.2 -- best and worst of 221 cells per target, chosen by P@5. `4LDJ` is true G12C (`4OBE` is wild-type at residue 12); `1OPL` has myristate pre-bound; cardiac myosin's and HIV-1 RT's pockets are reached only once seeded by the consensus (their true pocket ranks outside fpocket's top-10 on druggability alone but 3rd on PASSer allostery). Best and worst share the protein, seeding and scoring, so the AUC spread (0.63/0.57/0.62/0.77) is the operator-and-score choice alone -- on HIV-1 RT the same operator (`H14_anmP`) is both best and worst depending on the score. The pre-registered `H_new` cell is an honest near-negative on all four (KRAS 0.479 p=0.57, BCR 0.411 p=0.84, myosin 0.601 p=0.12, HIV-1 RT 0.665 p=0.060).*

**B.3 Seeded-CTQW vs classical baselines, 630 proteins.** Pipeline: PASSer top-10 -> drop the active-site pocket -> distal `MIN_HOP` filter -> CTQW -> PocketMiner veto [6] (apo-ligand protected) -> CTQW **ranks the surviving residues** (P@5 is residue-level; pockets are then ordered by their best residue), one fixed operator+score. Hit-list counts on identical residues (MIN_HOP=1; P@5 with AUC>=0.6):

On identical residues (MIN_HOP=1, P@5 with AUC>=0.6) the seeded-CTQW-pipeline clears **69 proteins / 20 families** at P@5>=0.8 and 101 / 45 at P@5>=0.6 (AUC 0.600) -- more per-protein than any of the thirteen classical baselines, but fewer families than closeness centrality (48 / **29**), which has no active site. Family-weighted AUC confirms the walk never beats closeness (0.585/0.542/0.544/0.543 vs 0.601/0.569/0.575/0.580 at MIN_HOP 1-4, Wilcoxon p=0.001-0.26, non-significant under paired McNemar); a blind leave-one-family-out regression over all 221 scores reaches 0.7216 on the 91 distal proteins against a reversed-distance floor of 0.7219. The protein-identity floor here is pooled AUC 0.771 [10-12], above every method tested.

**Best-of-221 per MIN_HOP (selection, not blind performance).** Picking the best Hamiltonian and score for each protein -- 221 cells per target -- the seeded-CTQW reaches P@5>=0.8 on 200/115, 147/77, 82/49, 47/20 (proteins/families) at MIN_HOP 1/2/3/4, and P@5>=0.6 on 340/215, 238/144, 131/80, 58/28. These are selection ceilings; the single fixed cell in Table B.3 (69/20 at P@5>=0.8) is what survives once the per-protein choice is removed, and the gap between them is the multiplicity this proposal corrects for.

![Connectivity C_ij for the four scoreable targets: best operator (top row), worst operator (middle), and the top-5 predicted-residue x active-site sub-block (bottom; rows = the five predicted residues, columns = active-site residues). N is the residue count per matrix. The first required deliverable. Best and worst share structure and seeding, so their contrast is the operator-and-score choice alone. Cardiac myosin's top-5 depends on a fpocket seeding that does not reproduce headless, so it is omitted here and kept in `results/connectivity/`; c-Myc/Max is connectivity-only (no ground truth) and also in the repo.](connectivity_bestworstdiff.png)

**B.4 The AI stage: one configuration recommender.** A single model sets the quantum stage from topology alone, so the pipeline can be applied to a new apo protein without a sweep. **Architecture:** 9 topology features -> StandardScaler -> Ridge multi-output -> the predicted AUC of all **884 configurations** (221 Hamiltonian x score cells x 4 MIN_HOP) -> rank -> **top-k with softmax weights**. **Input:** 9 graph features (residues, edges, mean/variance/CV of degree, clustering coefficient, diameter, algebraic connectivity, spectral radius). **Output:** the caller picks **k** -- how many (MIN_HOP, Hamiltonian, score) configurations to run -- and may restrict MIN_HOP; the model returns those k with weights summing to one. **Training:** leave-one-family-out over 630 proteins in 399 families, each scored by a model that never saw its family.

What this one model can and cannot learn was measured by the two random-forest diagnostics of section 6 (a MIN_HOP classifier and an operator-score regressor on the same features): topology predicts **MIN_HOP** (near vs distal, AUC 0.793; running at the predicted MIN_HOP beats always-hop-1, 0.924 vs 0.901) but **not the operator and score** (0.625 vs 0.630 for one fixed cell). Those two are the diagnostic; the deliverable is the single recommender above. So the recommender is honest about its limits -- it narrows MIN_HOP well, and reports the operator/score shortlist as selection rather than a confident pick; at k=6 the shortlist's best cell averages AUC 0.724 over 43 families. `results/ml_model/recommender.py`.



## Appendix — References

1. Schoepfer J, et al. Discovery of asciminib (ABL001), an allosteric inhibitor of the tyrosine kinase activity of BCR-ABL1. *J Med Chem.* 2018. doi:10.1021/acs.jmedchem.8b01040
2. Wylie AA, Schoepfer J, Jahnke W, et al. The allosteric inhibitor ABL001 enables dual targeting of BCR-ABL1. *Nature.* 2017;543:733–737. doi:10.1038/nature21702
3. Nagar B, Hantschel O, Young MA, et al. Structural basis for the autoinhibition of c-Abl tyrosine kinase. *Cell.* 2003;112:859–871. doi:10.1016/S0092-8674(03)00194-6
4. Wu N, Strömich L, Yaliraki SN. Prediction of allosteric sites and signaling: insights from benchmarking datasets. *Patterns.* 2022;3:100408. doi:10.1016/j.patter.2021.100408
5. Zlobin AS, Suplatov DA, Kopylov KE, Svedas VK. CASBench: a benchmarking set of proteins with annotated catalytic and allosteric sites. *Acta Naturae.* 2019;11:74–80. doi:10.32607/20758251-2019-11-1-74-80
6. Meller A, Ward M, Borowsky J, et al. Predicting cryptic pocket opening from protein structures using graph neural networks. *Nat Commun.* 2023;14. doi:10.1038/s41467-023-36699-3
7. Mohtashim SI, Sajjan M, Kais S. Continuous-time quantum-walk centrality for protein residue interaction networks. *J Am Chem Soc.* 2026;148:29206–29219. doi:10.1021/jacs.6c08053
8. Zhang Y, et al. A quantum framework for protein binding-site structure prediction on utility-level quantum processors. *Adv Sci.* 2026;13:e13641. doi:10.1002/advs.202513641
9. Le Guilloux V, Schmidtke P, Tuffery P. Fpocket: an open source platform for ligand pocket detection. *BMC Bioinformatics.* 2009;10:168. doi:10.1186/1471-2105-10-168
10. Benjamini Y, Hochberg Y. Controlling the false discovery rate. *J R Stat Soc Series B.* 1995;57:289–300. doi:10.1111/j.2517-6161.1995.tb02031.x
11. Künsch HR. The jackknife and the bootstrap for general stationary observations. *Ann Stat.* 1989;17:1217–1241. doi:10.1214/aos/1176347265
12. Maris E, Oostenveld R. Nonparametric statistical testing of EEG- and MEG-data. *J Neurosci Methods.* 2007;164:177–190. doi:10.1016/j.jneumeth.2007.03.024
13. Tian H, Xiao S, Jiang X, Tao P. PASSer: fast and accurate prediction of protein allosteric sites. *Nucleic Acids Res.* 2023;51:W427–W431. doi:10.1093/nar/gkad303
14. Ostrem JM, Peters U, Sos ML, Wells JA, Shokat KM. K-Ras(G12C) inhibitors allosterically control GTP affinity and effector interactions. *Nature.* 2013;503:548–551. doi:10.1038/nature12796
15. Anderson RL, et al. Deciphering the super-relaxed state of human beta-cardiac myosin and the mode of action of mavacamten. *PNAS.* 2018;115:E8143–E8152. doi:10.1073/pnas.1809540115
