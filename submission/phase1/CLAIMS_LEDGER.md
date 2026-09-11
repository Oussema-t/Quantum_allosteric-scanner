# Claims ledger — numeric statements already in the proposal (bartosz@9f1d521)

Every addition is checked against this list. Same quantity → same number or explicitly a second cohort.


## 1. Problem Framing
- Only 23% of curated allosteric sites and 7% of drug-contact pockets are genuinely distal;
- the cryptic-pocket datasets have median hop = 0 — their pockets sit essentially on the active site.
- Most standard targets cannot express the contrast they are used to test. A blind, pre-registered validity rule — apo closed, holo open, ligand strippe
- They are not: 3 of 7 audited targets have a ligand holding the pocket open, and 40 of 40 ASBench structures we sampled carry a bound ligand at the sco
- Two are unexplained: glucokinase 1V4S/MRK (88% overlap) and PKR 7FS3 (92%).
- Our own method fails this instrument, which is the honest test of it. Walk occupation scores AUC 0.5921 across 108 structures.
- Conditioned on distance to the active site it falls to 0.5184, not significant — roughly 80% of the apparent signal was inherited proximity.
- Under matched multiplicity across 276 protein families, no arm clears more than 5 — ours or any classical baseline — and they are statistically indist

## 2. Technical Approach
- | Converged CTQW on H_new | The specified method: contact Laplacian + five chemical/structural potentials | AUC 0.5921 → 0.5184 |
- Only 11–14% of the possible seed conditioning survives, and what survives is 0.63–0.79 anti-correlated with hop distance.
- It is a distance measure with extra steps — and we can show this is not a tuning failure, because the pipeline's hit rate anti-correlates with true-po
- We also ran the full ensemble end to end — thirteen operators × seventeen scores, with a cryptic-opening veto [6] — over 1022 proteins.
- Under matched multiplicity, one candidate set and a matched null, no arm clears more than 5 of 276 protein families, and quantum and classical arms ar
- Prior art, and what is actually new here. A continuous-time quantum walk on a residue interaction network was published in July 2026 [7] — the same co
- We ran the mandated ablation on our own cohort (105 structures, 74 proteins): correlation is markedly lower here (median ρ = 0.41, not ≈ 0.95);
- AUC is mixed, not uniformly null — we beat degree, eigenvector centrality and GNM-alone (p < 0.05) but tie betweenness and closeness (p = 0.50, 0.93).
- | (a) Certifying cryptic-pocket benchmark | Blind validity rule, endogenous-ligand audit, positive control, measured detection limit, at scale | 5 of 
- | (b) Apo vs stripped-holo delta | Isolates what cryptic-pocket prediction actually depends on | Leading methods report 89.8%/98.1% on ASBench/CASBenc
- | (c) Screening criterion for the hard regime | Decides from apo alone whether a target needs many-body treatment | Coupled search fires for 20% of KR
- Component (b) is ~27 minutes of compute over 100 apo/holo pairs and half a day of scripting against pairs we have already identified.

## 3. Feasibility & Resource Requirements
- Hardware, measured rather than assumed. At one qubit per residue — the convention behind every number here — the register needs 169–704 qubits and 3.3
- Coarse-graining to a NISQ-plausible 10–15 qubits destroys the ranking signal (retention Jaccard 0.00–0.18) without reaching usable fidelity.
- Data, compute and software. Public apo/holo PDB depositions plus five field benchmarks for cohort scale — no proprietary or synthetic structures, and 

## 4. Expected Impact
- "84% recovery" [4] is 99 of 118 structures detected by at least one of six statistical measures.
- Requiring three of six drops it to 57.6%;
- requiring all six, to 17.8%.
- | Certified apo/holo pairs | ≥ 40 pairs passing the blind validity rule | 7 audited, 2 pass |
- | Apo vs stripped-holo delta | Reported for ≥ 100 structures | Not reported in the literature we surveyed |
- | Combined readout | Residual AUC ≥ 0.60, LOPO, against a matched null | 0.6203 median, null passed |
- | Re-audit of published claims | The 84% headline decomposed | Done — a six-way disjunction |

## 5. Validation Plan
- On a genuinely distal subset our design cannot detect even proximity (p = 0.89), so we report that it cannot adjudicate rather than reporting a false 
- Success criteria for Phase 2: the instrument certifies ≥ 40 apo/holo pairs;
- a combined apo-only readout holds residual AUC ≥ 0.60 under LOPO against a matched null;
