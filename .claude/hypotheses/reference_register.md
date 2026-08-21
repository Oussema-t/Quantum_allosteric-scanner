# REFERENCE_HYPOTHESIS_REGISTER.md

Systematic extraction of testable hypotheses from the Cleveland Clinic challenge
statement's own reference list [1]–[25], with tested/untested status and open venues.

**Provenance:** produced in an external chat session, 2026-08-21, without repo access.
Status labels reflect what that session could infer about repo state. **Repo agents must
verify each `STATUS` line against actual task files before acting.** Where this document
reports a measured number, it comes from `TASK-0210_observable_family_confound.md` in the
same drop — run on bundled non-target PDB structures, never on challenge targets.

**Tagging:** OBSERVED / HYPOTHESIS / UNTESTED / PARTIAL / CONTESTED.
**`PDB-RETEST`** = must be re-run on real challenge targets before any claim is written.

---

## Tier A — hypotheses that attack current results

### H9 — Allostery is intrinsic to all dynamic proteins
*Ref [9] Gunasekaran, Ma & Nussinov 2004, Proteins 57:433.*

- **H9.1** Nearly every dynamic protein possesses latent allosteric capability; there is
  no clean class of "non-allosteric" surface sites.
- **STATUS:** UNTESTED. Not registered anywhere in the repo as far as this session could tell.
- **WHY IT MATTERS:** This attacks the **negative class of every AUC in the program.**
  Matched-decoy nulls, setup-validity gates and all ROC framing presuppose that
  non-functional surface pockets are true negatives. [9] argues that premise is unsound.
  It cuts both ways: it inflates apparent false positives *and* it means a chance-level
  AUC is not evidence of no signal.
- **OPEN VENUE:** (a) Limitations section — mandatory, regardless of testing.
  (b) Consider reporting **rank-of-known-site** and enrichment-at-k alongside AUC, since
  those degrade more gracefully under a contaminated negative class.
  (c) Re-examine whether the ~200-cell multiple-comparison budget is even the right
  frame if negatives are not negatives.
- **PDB-RETEST:** n/a (conceptual), but the metric change is a real deliverable.

### H6 — Population shift is the unified mechanism; effects are effector-specific
*Ref [6] Tsai & Nussinov 2014, PLoS Comput Biol 10:e1003394.*

- **H6.1** All allostery is population redistribution on a pre-existing landscape;
  "pathways" are high-flux subsets of that redistribution, not causal channels.
- **H6.2** The allosteric site is **effector-specific** — one protein has different
  allosteric sites for different effectors.
- **STATUS:** UNTESTED.
- **WHY IT MATTERS:** H6.2 attacks the **answer-key design.** A single ground-truth
  pocket per target assumes site uniqueness. A residue scoring high may be a genuine
  allosteric site for a different effector and is being counted as a false positive.
- **OPEN VENUE:** Cross-reference each target against ASD [25] for *all* annotated
  allosteric sites, not just the drug-bound one. If ASD lists additional sites, the
  answer key is under-specified and the false-positive rate is overstated.
- **PDB-RETEST:** **YES** — ASD lookup for KRAS_G12C, BCR-ABL1, Cardiac Myosin, PTP1B.

### H4 — Ensemble Allosteric Model (EAM)
*Ref [4] Motlagh, Wrabl, Li & Hilser 2014, Nature 508:331.*

- **H4.1** Allosteric coupling is a partition-function quantity over folded/unfolded
  segment microstates (2^N), **not** a pathway on a contact graph.
- **H4.2** Allostery can occur with **zero mean structural change** — purely entropic
  (Cooper–Dryden dynamic allostery).
- **H4.3** Intrinsic **disorder amplifies** allosteric coupling.
- **H4.4** Coupling free energy does **not decompose onto graph edges.**
- **STATUS:** PARTIAL / mostly UNTESTED.
  - A **harmonic proxy** of H4.1 was tested 2026-08-21 (see TASK-0210): the
    seed-referencing entropic coupling observable `dMSF_at_seed` is proximity-confounded
    at |partial ρ| = 0.773 ± 0.162 on real PDB structures. **OBSERVED: the harmonic /
    linear-response version of ensemble coupling offers no escape from the proximity
    confound.**
  - The **genuine EAM** — binary folded/unfolded units, nonlinear, non-Gaussian — is
    **UNTESTED.** Harmonic stiffening is not unfolding. This is the live residual.
- **WHY IT MATTERS:** This was the program's largest reference-level blind spot. It is
  **not** an exit the program walked past — the harmonic test above shows it lands in the
  same confounded room. But it is the only route to c-Myc/Max (1NKP) via H4.3, and it is
  the **type-correct quantum target**: partition-function estimation / Gibbs state
  preparation over 2^N, which converges independently on the program's existing
  conclusion that hardness lives at the combinatorial packing layer, not the propagator.
- **OPEN VENUE:**
  1. **COREX-style ensemble is MD-free and therefore constraint-3 compliant.** Sliding-window
     folding units, ASA-parameterised ΔG per microstate, residue stability constants κ_f.
     Computable from a static PDB. Run on KRAS_G12C + PTP1B (the two TASK-0209-valid targets).
  2. Score = response of κ_f at the active site to perturbation at candidate site j.
  3. **Decisive negative control:** construct the case where EAM ranking and
     propagation ranking disagree. If they agree everywhere, EAM adds nothing here.
  4. Forward-proposal framing: quantum resource = estimating Z, not propagating a walk.
     **Do not claim advantage** — quantum speedups for classical partition functions are
     at best quadratic and conditional. Claim *type-correctness* only.
- **PDB-RETEST:** **YES, MANDATORY.**

### H5 — MWC / conformational selection; concerted transitions
*Ref [5] Changeux & Edelstein 2005, Science.*

- **H5.1** Pre-existing equilibrium between states; ligand selects rather than induces.
- **H5.2** Allosteric transitions are concerted across subunits in oligomers.
- **STATUS:** UNTESTED.
- **WHY IT MATTERS:** H5.2 interacts with the challenge's own Scope ("Included: the
  catalytic domains"). For any target whose mechanism is inter-subunit or inter-domain,
  **scope truncation removes the coupling from the model by construction** — a
  setup-validity failure orthogonal to, and possibly deeper than, the apo/holo contrast
  finding in TASK-0209.
- **HYPOTHESIS (needs verification, not asserted):** Cardiac Myosin may be exactly this
  case — mavacamten stabilises the super-relaxed state, and SRX is associated with the
  interacting-heads motif, a **two-head** arrangement. If so, a single catalytic-domain
  contact graph cannot represent the mechanism at all. **Verify against refs [22][23]
  and the 6C1H entity composition before writing this.**
- **OPEN VENUE:** Add an explicit "mechanism-in-scope?" gate per target, upstream of the
  apo/holo contrast gate. This strengthens TASK-0209 rather than duplicating it.
- **PDB-RETEST:** **YES** — check oligomeric/multi-domain state of 5TBY, 6C1H, 1OPL, 5MO4.

---

## Tier B — untested methods the challenge explicitly road-signs

### H1 — NMA-guided conformational sampling finds cryptic sites
*Ref [1] Zheng 2023, J Chem Phys 158:124127. **Reference number one in the document.***

- **H1.1** Cryptic sites are found by **sampling conformations** along coarse-grained
  normal modes and detecting pockets in the generated conformers — not by scoring
  residues on the apo structure.
- **H1.2** A small number of low-frequency modes spans the pocket-opening deformations.
- **STATUS:** PARTIAL. The program independently arrived at the conformational-search
  reframing and measured ENM soft-mode pocket-opening probability p = 0.24–0.69.
  **Zheng's actual pipeline (NMA sampling → pocket detection → ranking) is not
  implemented as a baseline.**
- **WHY IT MATTERS:** This is the canonical classical method for the *reframed* problem
  the program itself converged on, it is MD-free, and it is the first citation in the
  challenge statement. Its absence is the most conspicuous gap in the baseline set.
- **OPEN VENUE:** Implement as a scored classical baseline. **If it outperforms the
  quantum arm, that must be reported** — objective 4.2 requires classical comparison.
- **PDB-RETEST:** **YES.**

### H2 — Cryptic pockets have a persistent-homology signature
*Ref [2] Koseki et al. 2025, J Chem Inf Model 65:5567 (CrypToth).*

- **H2.1** Cryptic pockets carry a topological signature (persistent cavities)
  separable from noise.
- **H2.2** TDA over an **ensemble** outperforms TDA on a single structure.
- **STATUS:** PARTIAL. The H₂ persistent-void arm exists (ripser). TASK-0143's 0/7 result
  used an inappropriate graph-openness proxy and therefore **did not kill this family.**
  The ensemble version (H2.2) is UNTESTED.
- **WHY IT MATTERS:** CrypToth uses mixed-solvent MD, which constraint 3 forbids as
  *input* — but the **TDA layer is transferable** to an ENM-generated ensemble.
- **OPEN VENUE (highest-value construction in this document):**
  **[1] + [2] stitched — NMA-guided conformational sampling feeding persistent homology
  → pocket ranking. Zero MD. Both halves cited by the organisers' own reference list.**
  This is the strongest available structural argument for a forward proposal, because it
  is built entirely from the challenge's own bibliography.
- **PDB-RETEST:** **YES.**

### H7 — Allosteric communication is non-equilibrium energy transport
*Ref [7] Stock & Hamm 2018, Phil Trans R Soc B 373.*

- **H7.1** Allosteric communication is a **non-equilibrium** vibrational energy-transport
  process (T-jump / impulse response), not an equilibrium correlation.
- **H7.2** Energy-transport pathways ≠ equilibrium correlation pathways.
- **STATUS:** UNTESTED. The entire pipeline is equilibrium.
- **WHY IT MATTERS — REFRAMING OPPORTUNITY:** The program has been benchmarking the CTQW
  against *equilibrium* classical observables (DCC, PRS, GNM covariance). [7] says the
  correct comparison class is **non-equilibrium impulse transport** — and a CTQW *is*
  an impulse propagator. This gives the quantum arm a physically principled, cited home
  and makes the ballistic front a feature of the model class rather than an artefact.
  It also road-signs the Markovian / memory-kernel question directly.
- **OPEN VENUE:** ENM impulse-response energy transport is closed-form and MD-free.
  Deposit an impulse at the seed, track energy arrival per residue, compare against the
  CTQW front. **Predicted (HYPOTHESIS, untested): also distance-dominated** — but if so,
  that is a stronger negative result, because it shows the confound survives the change
  of physical framework.
- **PDB-RETEST:** **YES.**

### H15 — Two-state ANM captures apo↔holo transitions
*Ref [15] Das, Gur, Cheng, Jo, Bahar & Roux 2014, PLoS Comput Biol 10:e1003521.*

- **H15.1** Transitions between two known endpoint structures are modelled by a simple
  two-state ANM.
- **H15.2** The transition is dominated by a few soft modes.
- **STATUS:** UNTESTED as such.
- **WHY IT MATTERS:** This is the **principled instrument for TASK-0209.** The 2-of-7
  conformational-contrast finding is currently asserted from structural inspection; a
  two-state ANM would let it be *quantified* per target with a defensible metric, turning
  a judgement call into a measurement. It uses the apo/holo pairs already in hand and
  requires no MD.
- **PDB-RETEST:** **YES, MANDATORY** — 4OBE→6OIM, 1OPL→5MO4, 5TBY→6C1H.

### H8 — Markovian random walk on the residue network
*Ref [8] Chennubhotla & Bahar 2007, PLoS Comput Biol 3:1716.*

- **H8.1** Signal propagation is approximated by a Markov random walk on the residue
  affinity network.
- **H8.2** Hitting/commute times identify communication hubs and pathways.
- **STATUS:** **TESTED 2026-08-21** (TASK-0210) as the classical analogue.
  **OBSERVED: commute time is itself a distance detector**, |partial ρ(distance | burial)|
  = 0.711 ± 0.125 on real PDB, and additionally burial-loaded (ρ = 0.561).
- **WHY IT MATTERS:** [8] is one of the three references the challenge cites in Section 5
  when it *mandates* the elastic-network assumption. Showing that the mandated classical
  baseline carries the same confound converts the program's proximity finding from
  "our observable is broken" into "the observable class the challenge specifies is
  broken" — and it directly discharges objective 4.2 (comparison to classical analogs).
- **PDB-RETEST:** **YES** — bundled structures are not challenge targets.

### H16 — GNM slow-mode minima mark functional/binding sites
*Ref [16] Erman 2006, Biophys J 91:3589.*

- **H16.1** GNM reproduces experimental B-factors (per-target model-validity check).
- **H16.2** Binding sites sit at **minima of the slowest modes**.
- **STATUS:** H16.1 likely partially covered; H16.2 **TESTED 2026-08-21** as a confound
  probe. **OBSERVED: slow-mode-1 minima are only weakly proximity-confounded**,
  |partial ρ| = 0.292 ± 0.218 — far below the seed-referencing family.
- **WHY IT MATTERS:** It is a near-free classical baseline that the program appears not
  to report, and it is one of only two observables found so far that escape the proximity
  confound. Like `dS_vib_global`, it is **seed-blind** — it cannot answer "connectivity
  to the active site," so it addresses objective 4.1 only under the "in most cases"
  qualifier in the challenge text.
- **PDB-RETEST:** **YES**, and add B-factor correlation as a per-target model-validity gate.

---

## Tier C — quantum-side road signs

### H10 — Non-local channels via quasiprobability / circuit cutting
*Ref [10] Mitarai & Fujii 2021, Quantum 5:388.*

- **H10.1** Non-local operations are simulable by local channels at sampling overhead
  exponential in the number of cuts (γ-factor).
- **STATUS:** UNTESTED, and this session found no sign it is registered.
- **WHY IT MATTERS:** This is the organisers' road sign for secondary objective 4.2 —
  "demonstrate a method for coarse-graining the protein structure and prove that this
  compression retains the essential topological signal." Circuit cutting is the
  *named* tool for mapping proteins that exceed qubit count.
- **OPEN VENUE:** Paper-level treatment is cheap and scores under Feasibility: partition
  the contact graph at minimum-cut boundaries, report the γ-factor overhead as a function
  of cut size, and state the qubit/depth budget implied. Ties to constraint 2.

### H11 — Open-system dynamics on quantum hardware via SVD/dilation
*Ref [11] Oh, Krogmeier, Schlimgen & Head-Marsden 2024, ACS Phys Chem Au 4:393.*

- **H11.1** Non-unitary (open-system) dynamics can be implemented on a gate-based device
  via singular-value decomposition / dilation.
- **STATUS:** UNTESTED.
- **WHY IT MATTERS:** This is the **cited hardware implementation path for the ENAQT arm.**
  Without it, the interior-γ dephasing optimum is a classical Lindblad solve with no
  quantum execution story, and constraint 1 ("credible path to execution on near-term or
  fault-tolerant hardware") is not discharged. ENAQT is currently the program's most
  defensible surviving quantum-mechanism claim; this is what makes it a *quantum* claim.
- **OPEN VENUE:** Cite as the implementation route; state resulting circuit depth against
  constraint 2. Pairs naturally with the structured-bath work in TASK-0147.

---

## Tier D — context and target-specific

- **[3] Nussinov & Tsai 2013** — allosteric drugs are more selective; allosteric sites are
  less conserved. **UNTESTED.** *Open venue:* a conservation-only baseline is a strong
  null — if sequence conservation alone predicts as well as the quantum score, the
  quantum arm adds nothing. Also a **label-leakage risk** if conservation enters features.
  Requires MSA; not runnable offline.
- **[14] Lu, Li & Zhang 2014** — allosteric sites are shallower/more polar than orthosteric.
  *Open venue:* a shape/physicochemical-prior baseline, and a possible confound generator.
- **[18][19] Ostrem 2013 / Canon 2019 (KRAS)** — **H18.1:** the switch-II pocket is
  *induced* by covalent ligand and does not pre-exist in apo. **This directly supports
  the TASK-0209 reasoning and the conformational-search reframing, and should be cited
  where that argument is made.**
- **[20][21] Wylie 2017 / Schoepfer 2018 (BCR-ABL1)** — **HYPOTHESIS, verify:** the
  myristoyl pocket is a *physiological* autoinhibitory site normally occupied by the
  N-terminal myristate, i.e. it may not be "cryptic" in the sense the challenge assumes.
  1OPL is the autoinhibited structure. **Check occupancy state before relying on the
  cryptic framing for this target** — this bears directly on TASK-0209's validity call.
- **[22][23] Green 2016 / Anderson 2018 (myosin)** — see H5.2 above.
- **[24] Dang 2017** — c-Myc undruggability; disorder. Connects to H4.3 as the only
  principled handle on 1NKP.
- **[25] ASD v3.0** — already registered. See H6.2 for the multi-site audit.
- **[12] Scannell, [13] wwPDB, [17] Qiskit** — context/tooling, no testable hypothesis.

---

## Question for the Cleveland Clinic team

The challenge statement contains an **internal tension** worth putting on record before
the submission is written:

> **Section 5 (Scope and Assumptions) mandates the elastic-network hypothesis — "the
> topology of the contact network is the primary driver of signal propagation" — citing
> [8][15][16]. Section 2 cites [4] and [9], which respectively hold that coupling is an
> ensemble/partition-function quantity that does not decompose onto graph edges, and that
> clean non-allosteric negatives may not exist. Which governs for scoring?**

Their answer determines whether a topology-level negative result reads as a failed
submission or as a finding about the problem statement. Get it in writing.
