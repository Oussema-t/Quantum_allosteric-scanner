# Prior art and the sponsor's own quantum work — what the submission must address

Researched 2026-09-07. Every DOI below verified via Crossref, arXiv, PMC or PubMed.
Three findings change what the submission can claim.

---

## 1. CTQW on protein residue networks is ALREADY PUBLISHED (July 2026)

**Mohtashim SI, Sajjan M, Kais S. "Continuous-Time Quantum-Walk Centrality for Protein Residue
Interaction Networks." *J Am Chem Soc* 148(27):29206-29219 (2026). DOI 10.1021/jacs.6c08053.**
Preprint arXiv:2604.17486. Peer-reviewed, in JACS.

Their construction is essentially ours: CTQW on a weighted residue interaction network (Ca < 8 A),
weighted adjacency mapped to a Hamiltonian, residues scored by long-time-averaged occupation
probability, ~150 proteins, plus a 4-qubit hardware proof-of-principle on IBM Kingston.

**Two consequences.**

**(a) The decorative-quantum objection is now PUBLISHED, not hypothetical.** They report CTQW
centrality vs classical eigenvector centrality: Spearman rho median ~0.95, Kendall tau ~0.87,
Overlap@10 typically 0.90-1.00. A reviewer can cite a JACS paper showing the quantum score is 95%
identical to a free classical one.
  -> **MANDATORY ABLATION:** beat eigenvector centrality, closeness, betweenness, and GNM alone,
     on the identical residues and labels. Without it the quantum layer is presumed decorative by
     published precedent.

**(b) Novelty for "CTQW on a protein contact graph" is gone — but the allosteric application is
NOT.** They explicitly defer it: *"Other natural extensions include applying the framework to
allosteric pathway prediction, mutational sensitivity mapping, and ensemble-averaged networks."*
  -> **The defensible novelty claim is the delta:** active-site-seeded pathway scoring, the site
     potentials, apo/holo blind validation, the cryptic-opening veto, and the benchmark-validity
     work. Cite the JACS paper and state the delta explicitly. Do not let a reviewer find it first.

They claim **no quantum advantage** (asymptotic advantage "requires efficient access to sparse
matrix elements", which they do not have).

**Related lineage, all classically simulated, none claiming advantage:**
- Goldsmith et al., "Link Prediction with Continuous-Time Classical and Quantum Walks",
  *Entropy* 25(5):730 (2023), DOI 10.3390/e25050730
- Saarinen et al. (incl. Loscalzo), "Disease gene prioritization with quantum walks",
  *Bioinformatics* 40(8):btae513 (2024), DOI 10.1093/bioinformatics/btae513 — states verbatim
  *"the methods described here are quantum-inspired, since they are implemented classically"*.
  Useful precedent and cover for an honest quantum-inspired framing.
- Dubovitskii et al. (Algorithmiq/IBM), DTQW on PPI networks, 40 qubits on hardware,
  arXiv:2602.24053v2 (2 Sep 2026, preprint). No advantage claimed.

---

## 2. The SPONSOR'S OWN group published a quantum-beats-AlphaFold3 claim

**Zhang Y, ... Nussinov R, Loscalzo J, Guan Q, Cheng F. "A Quantum Framework for Protein
Binding-Site Structure Prediction on Utility-Level Quantum Processors." *Advanced Science*
13(12):e13641 (2026). DOI 10.1002/advs.202513641.** Peer-reviewed. **Feixiong Cheng (Cleveland
Clinic Genome Center) is senior author; Ruth Nussinov is a co-author.**

Reported: 23 PDBbind + 7 therapeutic fragments (5-14 residues), VQE on the IBM-Cleveland Clinic
127-qubit machine, 12-102 qubits. RMSD **3.33 A quantum vs 3.87 A AlphaFold3 vs 6.34 A classical**;
quantum beat AF3 in 18/23.

**CONSEQUENCE FOR THE SUBMISSION: do NOT write "no quantum results exist in this domain."**
The host institution published one. That sentence would read as unaware of the sponsor's own work
to exactly the reviewer pool most likely to see it.

**The defensible position instead** (all of this is our analysis; there is no published rebuttal):
- It is orthosteric fragment **structure** prediction, not pocket **localization**. It predicts the
  conformation of a fragment already known to sit in a pocket. It never mentions allosteric sites
  or cryptic pockets.
- The AF3 baseline is run on isolated 5-14-residue peptide sequences, a regime AF3 is not built
  for and is known to fail in.
- The classical baselines are not named in the methods.
- **No classical exact solver of the same lattice Hamiltonian was run** — the single most important
  missing control.
- No significance testing over n=23; no CIs; the RMSD atom set is never stated.
- A citable critique of the whole lineage exists: **Roget M, Damour C, Cadet F, Wang J, "Assessing
  Cost Hamiltonian Reliability in Quantum Protein Structure Prediction", arXiv:2606.21241
  (19 Jun 2026, preprint)** — the cost Hamiltonian's energy landscape "is not correlated well
  enough to the actual error to provide meaningful predictions" at small-peptide scale.

Same-group follow-ons (same baseline problem, NOT independent replication): QDockBank
(arXiv:2508.00837, SC'25, DOI 10.1145/3712285.3759799); QSAD (arXiv:2607.06971, preprint).

**The other Cleveland Clinic quantum paper**, for completeness: Doga, Raubenolt, ... Blankenberg,
Shehab, *J Chem Theory Comput* 20(9) (2024), DOI 10.1021/acs.jctc.4c00067 — folded a 7-residue
peptide by VQE; quantum 1.781 A vs classical brute-force on the SAME Ising Hamiltonian 1.879 A.
A 0.1 A difference on a 7-mer is noise, not advantage. The authors are honest in the paper
(~4,967 qubits for hemoglobin; "low-depth QAOA is not expected to outperform state-of-the-art
classical algorithms").

---

## 3. No quantum advantage exists here — and one contemporaneous competitor

**The submission's core claim is CORRECT and well-supported.** Quotable, peer-reviewed:

- Gadbail et al., "Quantum computing in drug discovery", *Front Drug Discov* (7 Sep 2026),
  DOI 10.3389/fddsv.2026.1815176: **"no NISQ-based hybrid workflow has yet solved a chemically or
  pharmaceutically industrially relevant problem."**
- Zhou et al., *npj Drug Discovery* (2026), DOI 10.1038/s44386-025-00033-2: **"Systematic
  assessments in digital health find no consistent superiority of QML over strong classical
  baselines to date."**
- Lee, ... Preskill, Chan, *Nat Commun* 14:1952 (2023), DOI 10.1038/s41467-023-37587-6:
  "evidence for such an exponential advantage across chemical space has yet to be found."
- Santagati et al., "Drug design on quantum computers", *Nat Phys* 20:549-557 (2024),
  DOI 10.1038/s41567-024-02411-5 — excludes NISQ from serious analysis.
- Cordier, Sawaya, Guerreschi, McWeeney, *J R Soc Interface* 19(196):20220541 (2022),
  DOI 10.1098/rsif.2022.0541 — the standard framework for what would count as advantage in biology.

**Cryptic pockets have ZERO quantum literature.** Completely open. Classical state of the art:
PocketMiner (Meller et al., *Nat Commun* 14:1177 (2023), DOI 10.1038/s41467-023-36699-3,
ROC-AUC 0.87) and the Bowman-lab benchmark (bioRxiv, Jan 2026).

**Competitor, four days old: Toshiba + AOI Biosciences, 3 September 2026.** Japanese Patent
7908389, allosteric site prediction for undruggable proteins, claiming **">80% accuracy"** against
known allosteric sites (dataset undisclosed). Runs on Toshiba SQBM+ / Simulated Bifurcation —
**quantum-inspired, on conventional hardware**. Patent + press release, no peer review, no
disclosed benchmark. Beatable, but it exists and it is contemporaneous. Flag it rather than claim
first-mover status.

---

## 4. What Cleveland Clinic has and has not done on allostery

**They have NO allosteric site-prediction method, tool, benchmark or server.** No in-house
equivalent of PASSer, Allosite, AlloPred or PocketMiner.

**But they have demonstrated interest, at a low evidentiary bar they set themselves:**
- **Smith IN, Dawson JE, Krieger J, Thacker S, Bahar I, Eng C.** *J Chem Inf Model*
  62(17):4175-4190 (2022), DOI 10.1021/acs.jcim.2c00441 — microsecond MD on PTEN, reports
  **"potential druggable allosteric sites in a previously believed clinically undruggable
  protein."** Co-authored with **Ivet Bahar and James Krieger** (the GNM/ANM/ProDy lineage).
  That sentence is essentially the challenge's thesis, published in-house in 2022.
- Smith et al. (with Cheng), *Am J Hum Genet* 104(5):861-878 (2019), DOI 10.1016/j.ajhg.2019.03.009
- Smith, Dawson, Eng, *J Phys Chem B* 127(3):634-647 (2023), DOI 10.1021/acs.jpcb.2c06776

All single-target, hypothesis-generating, no benchmark, no P@k, no cross-protein validation.

**Ruth Nussinov** (NOT Cleveland Clinic; NCI Frederick + Tel Aviv, 34 co-authored papers with
Cheng) is the field's leading allostery theorist and co-authored the CC quantum binding-site paper.
Her canonical objection to any static-structure method: **Nussinov, Zhang, Liu, Jang, "AlphaFold,
Artificial Intelligence (AI), and Allostery", *J Phys Chem B* 126(34):6372-6383 (2022),
DOI 10.1021/acs.jpcb.2c04346.** Any submission resting on a single static contact graph should
expect that objection and pre-empt it.

**People who may review this:** Lara Jehi (CRIO, Quantum Innovation Catalyzer); Daniel Blankenberg
(lead, quantum workstream); **Kenneth Merz Jr.** (most technically careful; his group's public line
is that quantum advantage in chemistry "remains elusive"); **Bryan Raubenolt** (co-led the JCTC
perspective and published MD work on Zika helicase allostery, DOI 10.1016/j.jmgm.2021.108001 — he
knows allostery and MD); **Feixiong Cheng** (the quantum-beats-AF3 claim). MITRE's quantum science
team are independent technical assessors for the challenge.

---

## The four required changes, in priority order

1. **Cite the JACS CTQW paper and state the delta.** Novelty is the allosteric application they
   deferred, not the walk. Being seen to know this is worth more than the novelty was.
2. **Add the eigenvector-centrality ablation.** rho~0.95 is published; the quantum layer is
   presumed decorative until this is run.
3. **Replace any "no quantum results exist" phrasing** with the specific, respectful critique of
   the sponsor's own *Advanced Science* paper (orthosteric fragment structure != pocket
   localization; strawman AF3 baseline; no same-Hamiltonian control; no statistics).
4. **Flag Toshiba/AOI as prior art** rather than claiming first-mover status.

*Phase 1 closes 15 September 2026. No results from this challenge are published yet.*
