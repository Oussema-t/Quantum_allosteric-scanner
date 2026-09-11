# Claims ledger — every numeric statement already in the proposal

Source: `PHASE1_SUBMISSION_V4.md`, verbatim from `bartosz@9f1d521`.

**Rule.** Before adding anything, check it here. Same quantity -> same number, or state explicitly
that it is a second measurement on a second cohort. Never silently contradict, never restate.


## 1. Problem Framing
- Cryptic and allosteric are orthogonal, and the benchmarks conflate them. We assembled a unified 1233-protein benchmark across five public datasets [4–6] and measured, for
- Only 23% of curated allosteric sites and 7% of drug-contact pockets are genuinely distal;
- the cryptic-pocket datasets have median hop = 0 — their pockets sit essentially on the active site.
- Most standard targets cannot express the contrast they are used to test. A blind, pre-registered validity rule — apo closed, holo open, ligand stripped, cavity re-scored 
- We then ran the identical rule over 63 independent apo/holo pairs, where it passes 49% — and the failures are not a trivial apo-versus-holo asymmetry: of the 32 that fail
- c-Myc (1NKP), the challenge's separately named fourth target, has no drug-bound structure in the PDB — it cannot carry the apo/holo contrast by construction, so the valid
- Structures used, and why they deviate from Table 1. We reported to the organisers that 4OBE, the mandated KRAS G12C apo structure, is wild-type at residue 12 (GLY, not CY
- We searched for a genuine apo G12C structure and verified 4LDJ (residue 12 is CYS, no ligand at the site).
- They are not: 3 of 7 audited targets have a ligand holding the pocket open, and 40 of 40 ASBench structures we sampled carry a bound ligand at the scored site.
- Two are unexplained: glucokinase 1V4S/MRK (88% overlap) and PKR 7FS3 (92%).
- And ligand-removed holo is measurably easier than apo — a gap we have found no report of. The field's leading recovery figures, 89.8% on ASBench [4] and 98.1% on CASBench
- Across 63 apo/holo pairs spanning 59 distinct proteins, cavity detection scores +0.199 higher on the stripped-holo half than on the true apo half (median +0.184;
- Wilcoxon p = 2.6e-4;
- sign-flip permutation p < 1e-4;
- bootstrap 95% CI [+0.102, +0.296], excluding zero by a wide margin), with the same sign in both source cohorts.
- Consequence: those headline numbers describe a task roughly 0.2 AUC easier than the one they are read as solving, and the difference is not a rounding detail — it is larg
- We report it at n = 63 pairs;
- the ≥ 100 the instrument should certify remains a Phase-2 target.
- Our own method fails this instrument, which is the honest test of it. Walk occupation scores AUC 0.5921 across 108 structures.
- Conditioned on distance to the active site it falls to 0.5184, not significant — roughly 80% of the apparent signal was inherited proximity.
- On any single protein we can find an operator and score that look excellent — with thirteen operators and seventeen scores there are 221 chances per target, and reporting
- Under matched multiplicity across 276 protein families — a family groups structures of the same protein, so one protein deposited many times counts once — no arm clears m
- The size of that effect is measurable, not rhetorical: selecting the best operator-and-score combination per protein clears 137 families, and the label-permutation null f

## Paradigm
- We chose it only after looking for a combinatorial core hard enough to be worth a quantum optimiser, and measuring where hardness begins rather than assuming it: side-cha

## The physical hypothesis, and what we did to i
- | Converged CTQW on H_new | The specified method: contact Laplacian + five chemical/structural potentials | AUC 0.5921 → 0.5184 |
- Only 11–14% of the possible seed conditioning survives, and what survives is 0.63–0.79 anti-correlated with hop distance.
- It is a distance measure with extra steps — and we can show this is not a tuning failure, because the pipeline's hit rate anti-correlates with true-pocket distance in 7 o
- We also ran the full ensemble end to end — thirteen operators × seventeen scores, with a cryptic-opening veto [6] — over 1022 proteins.
- Under matched multiplicity, one candidate set and a matched null, no arm clears more than 5 of 276 protein families, and quantum and classical arms are statistically indi
- Prior art, and what is actually new here. A continuous-time quantum walk on a residue interaction network was published in July 2026 [7] — the same construction we use, o
- We ran the mandated ablation on our own cohort (105 structures, 74 proteins): correlation is markedly lower here (median ρ = 0.41, not ≈ 0.95);
- AUC is mixed, not uniformly null — we beat degree, eigenvector centrality and GNM-alone (p < 0.05) but tie betweenness and closeness (p = 0.50, 0.93).
- The sponsor's own group has separately published a quantum binding-site structure prediction result [8] — VQE-based 3D backbone prediction for short (5–14-residue) fragme
- Across 108 structures in 76 protein clusters the difference is +0.0023 AUC, Wilcoxon p = 0.92, cluster-robust p = 0.83 — a well-powered null, not an underpowered one.
- Extending the cohort by 54 more distinct proteins (129 clusters, +70%) holds the same verdict: cluster-robust p = 0.42.
- Scanned across eleven delays spanning five orders of magnitude — from deep short-delay, where the interference term is fully alive, through convergence, each set as a fra
- Its unsigned magnitude clears chance at exactly one of the eleven delays (p = 0.036) with no support at any neighbour, the signature of a selection artifact rather than a

## What we propose to build in Phase 2
- | (a) Certifying cryptic-pocket benchmark | Blind validity rule, endogenous-ligand audit, positive control, measured detection limit, at scale | 5 of 7 standard targets f
- | (b) Screening criterion for the hard regime | Decides from apo alone whether a target needs many-body treatment | Coupled search fires for 20% of KRAS_G12C restarts and

## 3. Feasibility & Resource Requirements
- Hardware, measured rather than assumed. At one qubit per residue — the convention behind every number here — the register needs 169–704 qubits and 3.3M–124.9M two-qubit g
- Coarse-graining to a NISQ-plausible 10–15 qubits destroys the ranking signal (retention Jaccard 0.00–0.18) without reaching usable fidelity.
- AWS Braket and Classiq access were confirmed with the organisers as a Phase-2 benefit — irrelevant to a verdict set by qubit count and circuit depth, not by cloud provide
- This is why §2 proposes classical-plus-quantum-inspired rather than hardware-targeted work: the resource picture was measured before the framing was chosen.
- Data, compute and software. Public apo/holo PDB depositions plus five field benchmarks for cohort scale — no proprietary or synthetic structures, and every cohort's conta
- Compute is classical throughout: ensemble generation, contact-graph construction and the walk's own simulation run on commodity CPUs, the largest single analysis (105-str
- the 1022-protein ensemble sweep needed a modest HPC allocation for a day.

## 4. Expected Impact
- "84% recovery" [4] is 99 of 118 structures detected by at least one of six statistical measures.
- Requiring three of six drops it to 57.6%;
- requiring all six, to 17.8%.
- The same shape reproduces in a second, independent domain: across four pocket detectors (fpocket, PASSer, p2rank, PocketMiner) on one shared structure set and truth defin
- | Certified apo/holo pairs | ≥ 40 pairs passing the blind validity rule | 63 audited, 31 pass (2 of the 7 standard targets) |
- | Apo vs stripped-holo delta | Reported for ≥ 100 structures | Done at n = 63 pairs: +0.199, CI [+0.102, +0.296] |
- | Combined readout | Residual AUC ≥ 0.60, leave-one-protein-out (LOPO), against a matched null | 0.6203 median, null passed |
- | Re-audit of published claims | The 84% headline decomposed | Done — a six-way disjunction |

## 5. Validation Plan
- That constant-per-protein score reaches AUC 0.65 (p < 5e-5), reproduced independently on 54 proteins added afterwards.
- On a genuinely distal subset our design cannot detect even proximity (p = 0.89), so we report that it cannot adjudicate rather than reporting a false negative.
- - A convergence check on the propagation time. Not a detail: between a typical finite T = 15 and the converged limit, 50 of 108 structures flip the sign of their verdict 
- A continuous-time walk reported at a fixed finite T without a convergence check is reporting a coin flip on roughly 40% of its cohort, and we have found no report of this
- Success criteria for Phase 2: the instrument certifies ≥ 40 apo/holo pairs;
- a combined apo-only readout holds residual AUC ≥ 0.60 under LOPO against a matched null;

## 6. Hybrid / Cross-Domain Architecture
- Where the AI sits, and what it is worth. Two random-forest models configure the quantum stage from protein topology alone — nine graph features, leave-one-family-out acro
- The first predicts how far from the active site to look: it separates near from distal targets at AUC 0.793, and running the walk at its predicted distance beats a single
- The second predicts which operator and score to use, and does not work: 0.625 against 0.630 for simply applying one fixed operator everywhere, 13 families against 15.
- Removing the classical pre-filters entirely makes the same point quantitatively: with every residue a candidate instead of roughly forty, the best classical ranker's stri
