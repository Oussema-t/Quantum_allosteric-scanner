# Quantum-Walk Allosteric Site Prediction at Benchmark Scale

**Phase 1 Concept Proposal — Team AuraQu**
**Cleveland Clinic Challenge: Unlocking Undruggable Targets — Quantum Simulation of Allosteric Signal Propagation**
**2026 Global Quantum + AI Challenge**

---

## 1. Problem Framing

Over 85% of disease-causing proteins are considered undruggable because they lack accessible orthosteric pockets; for these targets, allosteric targeting is the only viable therapeutic route. Identifying allosteric sites requires understanding how a perturbation at a distal pocket propagates through the protein to the active site — a fundamentally *dynamic*, non-local process. Classical diffusive models capture this only approximately, and full molecular dynamics is computationally prohibitive at proteome scale.

We propose that a **continuous-time quantum walk (CTQW)** on the residue contact graph is a natural model for this propagation: its unitary evolution captures interference and non-local correlations that classical random walks cannot, while the challenge's elastic-network hypothesis lets us abstract away atomic force fields. Our central question is empirical and honestly posed: **does quantum information propagation identify allosteric pathways more accurately than classical diffusion — and, critically, on which class of targets?**

## 2. Technical Approach

Our method is a **hybrid quantum-classical pipeline**. The quantum core is a continuous-time walk, executable on near-term or simulated hardware.

**Stage 1 — Classical candidate generation.** fpocket (cavity geometry / druggability) and PASSer (supervised allostery classifier) nominate candidate pockets; a graph-distance filter (MIN_HOP ≥ 2) enforces distality, so the method is tested on propagation rather than proximity.

**Stage 2 — Quantum propagation.** A CTQW propagator *e*^(−*iHt*) runs on the contact-graph Hamiltonian across 13 operator families and 17 observables (time-averaged occupation, Green's functions, quantum mutual information). Our engineered operator **H_new** fuses a quantum normalized Laplacian (off-diagonal) with a classical elastic-network site potential (diagonal terms: B-factors, rigidity, GNM cross-correlation, low-mode participation).

**Stage 3 — Classical accessibility veto.** PocketMiner — ported and validated to pooled AUC 0.868 against its own held-out set — removes non-cryptic pockets, with apo-ligand pockets protected.

**Stage 4 — Quantum re-ranking** of the survivors produces the two required deliverables.

The **connectivity-matrix deliverable** is the CTQW average mixing matrix,

> *M*(*i*,*j*) = lim(*T*→∞) (1/*T*) ∫₀ᵀ |⟨*i*| *e*^(−*iHt*) |*j*⟩|² d*t*

a parameter-free, genuinely quantum object computed in closed form from the Hamiltonian spectrum. The **hit list** is the top-5 residues ranked from the active-site rows of *M*.

## 3. Feasibility and Resource Requirements

The approach is exceptionally lightweight and **already demonstrated at scale**. We built and ran the complete pipeline across **1,233 proteins from five benchmark datasets** (ASBench, CASBench, CryptoBench, CryptoSite, PocketMiner) — computing topology features, active-site/pocket geometry, and the full quantum score battery — for a **total compute cost of approximately €0.26** on commodity CPU nodes. The CTQW pipeline is ~50 MB, CPU-only, needs no GPU, and runs in seconds per protein. The method therefore scales to the full proteome without specialized hardware, and the €0.26 / 1,233-protein figure is direct evidence of feasibility.

**Honest constraints, stated up front:**
- The CTQW average-mixing observable is the decoherence-surviving limit and is spectrally computable, so a genuine hardware quantum-advantage claim rests on the coherence-bearing observables (finite-time occupation, Green's function, QMI), not the time-averaged score.
- Pocket detectors fail to propose the true pocket in **22–30%** of proteins — a detector-limited ceiling that precedes any physics.
- Multiplicity across operator × score cells is real; every headline number must be pre-registered or chance-corrected against a permutation null.

## 4. Expected Impact

A successful PoC delivers a validated, proteome-scale allosteric-site scanner that operates upstream of expensive experimental screening, prioritizing surface regions mechanistically connected to disease function and thereby lowering clinical attrition from mis-targeted mechanisms.

Preliminary results already establish three concrete, defensible contributions:

- **(a) A pre-registered, held-out positive on HIV1-RT:** AUC 0.697, *p* = 0.0175 (operator, score, and null fixed in advance; 2000× label permutation; n = 281 seeds).
- **(b) A validated physics result:** the engineered elastic-network site potential is load-bearing — H_new beats its own potential-free base operator on ~100 proteins (Wilcoxon *p* ≤ 0.026), and is the single best operator of 13.
- **(c) A benchmark-composition finding of independent value:** only **13% of curated allosteric sites are genuinely distal** (hop ≥ 2 and > 12 Å); for the remaining 87% the target sits on or beside the active site. This explains why the field's headline "recovery" metrics (e.g. 84% enrichment for bond-to-bond propensity) coexist with the absence of a working *distal* pocket-finder — the standard benchmarks largely cannot test propagation.

## 5. Validation Plan

Our validation methodology is the strongest component of the proposal and is already implemented in code.

- **Metric:** P@5 and AUC, reported at the **family (cluster) level** to remove the ~4× inflation from multi-structure PDB deposition, and **chance-corrected** against a correlation-preserving label-permutation null (the raw "best-of-N-cells" maximum is treated as selection, not a result).
- **Honest denominator:** the score is over targets *attempted*; stage-1 detector failures are scored as failures, not silently dropped.
- **Distality control:** headline results are computed on the genuinely distal subset, where propagation rather than proximity is under test.
- **Named baselines the quantum method must beat:** fpocket druggability, PASSer rank, hop-distance, and the **classical heat-kernel twin** of the CTQW (same operator, no coherence).
- **Pre-registration:** operator, score, and null fixed before scoring, as demonstrated in the HIV1-RT test.

**Phase 2 success criterion.** A single fixed, cross-validated predictor — a leave-one-family-out regression over the 221 quantum + classical features — that **beats a classical-features-only model on held-out families**. This converts best-of-N selection into one validated model and directly answers whether the quantum observables add value beyond geometry. An early version already beat every single cell blind (AUC 0.717 vs 0.589).

## 6. Hybrid / Cross-Domain Integration

The pipeline is hybrid at two levels. **Architecturally**, classical detectors (fpocket, PASSer) and a classical ML accessibility model (PocketMiner) bracket two rounds of quantum propagation. **Physically**, the H_new Hamiltonian fuses quantum graph dynamics (normalized Laplacian) with classical elastic-network descriptors (rigidity, cross-correlation, mode participation) in its diagonal. The division of labor is deliberate: classical methods constrain the search space cheaply; the quantum walk supplies the non-local ranking signal that geometry and distance cannot. This is the natural way to apply near-term quantum resources to a problem far too large for quantum hardware alone.

## 7. Team Capability

Team AuraQu has executed the full pipeline end-to-end at benchmark scale (1,233 proteins, ≈ €0.26), ported and validated third-party ML tooling (PocketMiner, AUC 0.868), and built a rigorous permutation-null evaluation framework. Critically, the team subjected its own most promising results to adversarial internal review and **retracted confounded claims before submission** — proximity-inflated KRAS scores, high-base-rate BCR-ABL1 hits, and best-of-N selection artifacts were all identified and corrected internally. This combination of engineering throughput, methodological rigor, and intellectual honesty is precisely what a credible allosteric-discovery program requires and what distinguishes a durable Phase 2 result from an inflated Phase 1 claim.

---

### Appendix A — Per-target results (latest run)

| Target | Best AUC | P@5 | Configuration | Honest status |
|---|---|---|---|---|
| **HIV1-RT** | **0.697** | — | H_new fixed, closed-form p_avg, pre-registered, 2000× permutation, n = 281 | ✅ **Pre-registered, held-out positive (p = 0.0175)** |
| KRAS-G12C | 0.828 | 1.0 | H3_normL, p_avg, MIN_HOP = 1 | ⚠️ Proximity-inflated — P@5 → 0.2 at MIN_HOP ≥ 2 |
| KRAS-G12C | 0.762 | 0.6 | H_new, consensus seeding, MIN_HOP = 2 | Honest reference run |
| BCR-ABL1 | 0.767 | 1.0 | H2_combL, MIN_HOP = 2, 23 seeds | ⚠️ Base rate 0.78; effector bound in apo (1OPL has MYR) |
| CARDIAC-MYOSIN | 0.713 | 0.0 | H6_exp, residual LOG, 243 seeds | ❌ fpocket control (0.747) beats it |

### Appendix B — Benchmark composition

| Group | Families | Median hop | Median Å | Distal |
|---|---|---|---|---|
| Curated allosteric | 106 | 2.0 | 10.1 | 23% |
| Drug-contact | 582 | 0.0 | 0.0 | 7% |
| **All (1020 measured)** | **~688** | — | — | **13% (138 proteins)** |

Topology partly predicts distality: algebraic connectivity (Fiedler value) partial ρ = −0.477 (*p* = 0.0014) after controlling for size — loosely connected proteins have more distant allosteric sites.

### Appendix C — Benchmark-scale signal (138 distal proteins, chance-corrected)

| Run | Best-of-96 AUC | Null | Δ | *p* | Proteins *p* < 0.05 |
|---|---|---|---|---|---|
| fpocket, hop 2 | 0.799 | 0.765 | +0.034 | 2.9e-05 | 19 / 106 |
| consensus, hop 2 | 0.777 | 0.745 | +0.032 | 1.3e-04 | 16 / 96 |

Against the correlation-preserving null the real gain is **+0.03 AUC**, concentrated in ~15–19 proteins (≈ 6 distinct proteins after family de-duplication); P@5 gains nothing at the pocket level. At the pocket level, PASSer-rank (43.5% top-1) and largest-pocket (40%) baselines exceed the whole-pocket walk (10.7%) — reported honestly as the current limit and the motivation for the Phase 2 regression.

---

*Compute: Hetzner CPU nodes, cumulative ≈ €0.26, all instances deleted after results were retrieved. Full methods, scripts, and raw outputs: repository branch `allosteric` (`REPORT.md`, `results/`).*
