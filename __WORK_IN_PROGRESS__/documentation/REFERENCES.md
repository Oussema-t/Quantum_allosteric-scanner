# References — the project's scientific bibliography

**What this is.** A tracked index of external scientific sources this project
cites or should cite: the challenge's own bibliography [1]–[25]
(`documentation/Cleveland-Clinic-Challenge-Statement-vF-1.md` §7, verbatim),
plus method/tool papers cited elsewhere in the register. Each entry: the
citation, a link, a one-line takeaway, and (where one exists) which task
tested it against real data.

**What this is not.** Not the papers themselves. PDFs, notebook exports, or
any other local copy of a source belong in `__WORK_IN_PROGRESS__/documentation/
references/` (gitignored — regeneratable/re-downloadable, not project output).
This file is the durable, tracked pointer; that folder is scratch.

**How to use this** — read `.ai/reference/PAPER_CITATION_PROTOCOL.md` first.
Short version: check here before citing anything from memory, verify the DOI
resolves before adding a new entry, and never present an externally-produced
number as validated until it has cleared this project's own PDB-retest
convention (see the standing caveat below — it exists because of a real
incident, not as a formality).

---

## Standing caveat — read before citing anything from the reference register below

**`.claude/hypotheses/reference_register.md`** (285 lines, dropped into the
repo 2026-08-21 by an external chat session with no repo access) is the
source of most status tags and takeaways below. Its own header states this
plainly: *"Repo agents must verify each STATUS line against actual task files
before acting."* Every measured number in it was produced **on bundled
non-target PDB structures, never on real challenge targets** — [[TASK-0229]]'s
own inherited standing caveat: **nothing from that register may be cited in
the submission before a PDB-retest on the actual challenge targets.**
`PDB-RETEST: YES` below flags exactly which entries that applies to. Treat
every "OBSERVED" tag on a `PDB-RETEST: YES` row as a hypothesis with a
number attached, not a result.

---

## Challenge bibliography [1]–[25]

Full citations verbatim from the challenge statement §7 (DOIs are the
authoritative link — resolve at `https://doi.org/<doi>`). Status/takeaway
columns are this project's own reading, via
`.claude/hypotheses/reference_register.md` and [[TASK-0229]]'s subtask family
(`.001`–`.007`), not the papers' own abstracts.

| # | Citation | DOI | Status | Takeaway | Task |
|---|---|---|---|---|---|
| 1 | Zheng W. Predicting allosteric sites using fast conformational sampling as guided by coarse-grained normal modes. J Chem Phys. 2023;158:124127. | [10.1063/5.0141630](https://doi.org/10.1063/5.0141630) | PARTIAL | Reference #1 in the challenge's own list. The program independently converged on the same conformational-search reframing (ENM soft-mode pocket-opening, p=0.24-0.69), but Zheng's actual pipeline (NMA sampling → pocket detection → ranking) is **not implemented as a scored baseline** — the most conspicuous gap in the current baseline set. | [[TASK-0229.004]] |
| 2 | Koseki J, et al. CrypToth: Cryptic Pocket Detection through Mixed-Solvent MD-Based Topological Data Analysis. J Chem Inf Model. 2025;65:5567-5575. | [10.1021/acs.jcim.4c02111](https://doi.org/10.1021/acs.jcim.4c02111) | PARTIAL | Uses mixed-solvent MD as *input*, which §Constraint 3 forbids — but the TDA/persistent-homology layer is transferable to an ENM-generated (MD-free) ensemble. [[TASK-0143]]'s 0/7 persistent-void result used an inappropriate graph-openness proxy and did **not** kill this family; the ensemble version is untested. Stitched with [1] this is flagged the register's own "highest-value construction" — both halves cited by the organisers. | [[TASK-0229.005]] |
| 3 | Nussinov R, Tsai C-J. Allostery in disease and in drug discovery. Cell. 2013;153:293-305. | [10.1016/j.cell.2013.03.034](https://doi.org/10.1016/j.cell.2013.03.034) | UNTESTED | Allosteric drugs are more selective; allosteric sites are less conserved than orthosteric ones. Open venue: a conservation-only baseline is a strong null (needs an MSA, not runnable offline) — and a label-leakage risk if conservation ever entered a feature set. | — |
| 4 | Motlagh HN, Wrabl JO, Li J, Hilser VJ. The ensemble nature of allostery. Nature. 2014;508:331-339. | [10.1038/nature13001](https://doi.org/10.1038/nature13001) | PARTIAL | The Ensemble Allosteric Model: coupling is a partition-function quantity over folded/unfolded microstates (2^N), not a contact-graph pathway; can occur with zero mean structural change (Cooper-Dryden dynamic allostery); coupling free energy does not decompose onto graph edges. A harmonic proxy (`dMSF_at_seed`) was tested 2026-08-21 and found proximity-confounded (\|partial ρ\|=0.773±0.162) — harmonic stiffening is not unfolding, so the genuine (nonlinear, COREX-style) EAM remains untested and is the only principled route to c-Myc/1NKP. Flagged as the program's largest reference-level blind spot before this register existed. | [[TASK-0229.006]] |
| 5 | Changeux J-P, Edelstein SJ. Allosteric Mechanisms of Signal Transduction. Science. 2005. | [10.1126/science.1108595](https://doi.org/10.1126/science.1108595) | UNTESTED | MWC/conformational selection: pre-existing equilibrium between states, ligand selects rather than induces; transitions are concerted across subunits in oligomers. The oligomer-concertedness claim interacts with the challenge's own scope note ("catalytic domains only") — if a target's real mechanism is inter-subunit, scope truncation may remove the coupling from the model by construction, independent of the apo/holo contrast finding. Cardiac Myosin is flagged (not confirmed) as a candidate case via mavacamten/SRX/interacting-heads biology. | [[TASK-0229.007]] (via ref 15) |
| 6 | Tsai C-J, Nussinov R. A unified view of "how allostery works." PLoS Comput Biol. 2014;10:e1003394. | [10.1371/journal.pcbi.1003394](https://doi.org/10.1371/journal.pcbi.1003394) | UNTESTED | Allostery is population redistribution on a pre-existing landscape; the allosteric site is **effector-specific** — one protein can have different allosteric sites for different effectors. Attacks the answer-key design directly: a single ground-truth pocket per target assumes site uniqueness, so a genuine site for a different effector could be counted as a false positive. | [[TASK-0229.003]] |
| 7 | Stock G, Hamm P. A non-equilibrium approach to allosteric communication. Philos Trans R Soc Lond B Biol Sci. 2018;373. | [10.1098/rstb.2017.0187](https://doi.org/10.1098/rstb.2017.0187) | UNTESTED | Allosteric communication is a non-equilibrium vibrational energy-transport process (T-jump/impulse response), not an equilibrium correlation — and this pipeline's entire propagation layer is equilibrium. Reframing opportunity: a CTQW *is* an impulse propagator, so the correct classical comparison class may be non-equilibrium impulse transport, not equilibrium DCC/PRS/GNM covariance. | [[TASK-0229.007]] |
| 8 | Chennubhotla C, Bahar I. Signal propagation in proteins and relation to equilibrium fluctuations. PLoS Comput Biol. 2007;3:1716-1726. | [10.1371/journal.pcbi.0030172](https://doi.org/10.1371/journal.pcbi.0030172) | OBSERVED | One of three references the challenge cites in §5 when it *mandates* the elastic-network assumption. Markov random walk on the residue affinity network; hitting/commute times identify hubs/pathways. **Tested 2026-08-21**: commute time is itself a distance detector on real PDB structures (\|partial ρ(distance\|burial)\|=0.711±0.125, additionally burial-loaded ρ=0.561) — if this replicates on real challenge targets, it converts the proximity finding from "our observable is broken" to "the observable class the challenge itself specifies is broken." **PDB-RETEST: YES** — bundled structures are not challenge targets. | — |
| 9 | Gunasekaran K, Ma B, Nussinov R. Is allostery an intrinsic property of all dynamic proteins? Proteins. 2004;57:433-443. | [10.1002/prot.20232](https://doi.org/10.1002/prot.20232) | UNTESTED | Nearly every dynamic protein may possess latent allosteric capability — there may be no clean class of "non-allosteric" surface sites. **Attacks the negative class of every AUC in the program**: matched-decoy nulls and all ROC framing presuppose non-functional surface pockets are true negatives. Cuts both ways (inflates apparent false positives, but also means a chance-level AUC is not evidence of *no* signal). Mandatory in the Limitations section regardless of whether it is ever formally tested. | [[TASK-0229.001]] |
| 10 | Mitarai K, Fujii K. Overhead for simulating a non-local channel with local channels by quasiprobability sampling. Quantum. 2021;5:388. | [10.22331/q-2021-0128-388](https://doi.org/10.22331/q-2021-0128-388) | UNTESTED | The organisers' road sign for objective §4.2's coarse-graining/compression half — circuit cutting is the *named* tool for mapping a protein that exceeds qubit count. Paper-level treatment (partition the contact graph at minimum-cut boundaries, report the γ-factor sampling overhead as a function of cut size) is cheap and scores under Feasibility. | [[TASK-0229.002]] |
| 11 | Oh EK, Krogmeier TJ, Schlimgen AW, Head-Marsden K. Singular Value Decomposition Quantum Algorithm for Quantum Biology. ACS Phys Chem Au. 2024;4:393-399. | [10.1021/acsphyschemau.4c00018](https://doi.org/10.1021/acsphyschemau.4c00018) | UNTESTED | The cited hardware-implementation route for the ENAQT arm: non-unitary (open-system) dynamics via SVD/dilation on a gate-based device. Without this, the interior-γ dephasing optimum is a classical Lindblad solve with no quantum execution story — this is what makes ENAQT a *quantum* claim rather than a classical one dressed up. | [[TASK-0229.002]] |
| 12 | Scannell JW, Blanckley A, Boldon H, Warrington B. Diagnosing the decline in pharmaceutical R&D efficiency. Nat Rev Drug Discov. 2012;11:191-200. | [10.1038/nrd3681](https://doi.org/10.1038/nrd3681) | context | Context/motivation citation, no testable hypothesis for this pipeline. | — |
| 13 | wwPDB consortium, et al. Protein Data Bank: the single global archive for 3D macromolecular structure data. Nucleic Acids Res. 2018;47:D520-D528. | [10.1093/nar/gky949](https://doi.org/10.1093/nar/gky949) | context | The data source this entire project fetches from (`backend/data_layer.py`, `allostery/clean.py`). No testable hypothesis beyond "use PDB structures," which the pipeline already does. | — |
| 14 | Lu S, Li S, Zhang J. Harnessing allostery: a novel approach to drug discovery. Med Res Rev. 2014;34:1242-1285. | [10.1002/med.21317](https://doi.org/10.1002/med.21317) | UNTESTED | Allosteric sites tend to be shallower and more polar than orthosteric sites. Open venue: a shape/physicochemical-prior baseline, and a possible confound generator worth checking against existing scored observables. | — |
| 15 | Das A, Gur M, Cheng MH, Jo S, Bahar I, Roux B. Exploring the conformational transitions of biomolecular systems using a simple two-state anisotropic network model. PLoS Comput Biol. 2014;10:e1003521. | [10.1371/journal.pcbi.1003521](https://doi.org/10.1371/journal.pcbi.1003521) | UNTESTED | One of three references the challenge cites in §5 for the mandated elastic-network assumption. A simple two-state ANM, dominated by a few soft modes, models the transition between two known endpoint structures. This is the **principled instrument to quantify [[TASK-0209]]'s 2/7 apo-closed/holo-open finding** — currently asserted from structural inspection — using the apo/holo pairs already in hand, no MD required. | [[TASK-0229.007]] |
| 16 | Erman B. The Gaussian network model: precise prediction of residue fluctuations and application to binding problems. Biophys J. 2006;91:3589-3599. | [10.1529/biophysj.106.090803](https://doi.org/10.1529/biophysj.106.090803) | PARTIAL / OBSERVED | Third of the three references the challenge cites in §5 for the elastic-network assumption. GNM reproduces experimental B-factors (a per-target model-validity check, likely partially already covered); binding sites sit at minima of the slowest modes. **Tested 2026-08-21** as a confound probe: slow-mode-1 minima are only weakly proximity-confounded (\|partial ρ\|=0.292±0.218) — one of only two observables found so far to escape the seed-proximity confound family, though it is seed-blind (cannot answer "connectivity to the active site" specifically). **PDB-RETEST: YES.** | — |
| 17 | Javadi-Abhari A, et al. Quantum computing with Qiskit. arXiv:2405.08810. 2024. | [10.48550/ARXIV.2405.08810](https://doi.org/10.48550/ARXIV.2405.08810) | context | Tooling citation (the framework any hardware-realization work would target), no testable hypothesis. | — |
| 18 | Ostrem JM, Peters U, Sos ML, Wells JA, Shokat KM. K-Ras(G12C) inhibitors allosterically control GTP affinity and effector interactions. Nature. 2013;503:548-551. | [10.1038/nature12796](https://doi.org/10.1038/nature12796) | context | The KRAS switch-II pocket is *induced* by the covalent ligand and does not pre-exist in the apo state — directly supports the [[TASK-0209]] cryptic-pocket-validity reasoning and the conformational-search reframing; cite where that argument is made. | — |
| 19 | Canon J, et al. The clinical KRAS(G12C) inhibitor AMG 510 drives anti-tumour immunity. Nature. 2019;575:217-223. | [10.1038/s41586-019-1694-1](https://doi.org/10.1038/s41586-019-1694-1) | context | Companion citation to [18] — clinical validation of the switch-II covalent-inhibitor mechanism. | — |
| 20 | Wylie AA, et al. The allosteric inhibitor ABL001 enables dual targeting of BCR-ABL1. Nature. 2017;543:733-737. | [10.1038/nature21702](https://doi.org/10.1038/nature21702) | HYPOTHESIS | With [21]: the myristoyl pocket may be a *physiological* autoinhibitory site normally occupied by the N-terminal myristate — i.e. possibly not "cryptic" in the sense the challenge assumes. 1OPL is the autoinhibited structure. **Bears directly on [[TASK-0209]]'s validity call for BCR-ABL1** — check occupancy state before relying on the cryptic framing for this target (verify, not yet confirmed from this citation alone). | — |
| 21 | Schoepfer J, et al. Discovery of Asciminib (ABL001), an Allosteric Inhibitor of the Tyrosine Kinase Activity of BCR-ABL1. J Med Chem. 2018. | [10.1021/acs.jmedchem.8b01040](https://doi.org/10.1021/acs.jmedchem.8b01040) | HYPOTHESIS | See [20]. | — |
| 22 | Green EM, et al. A small-molecule inhibitor of sarcomere contractility suppresses hypertrophic cardiomyopathy in mice. Science. 2016. | [10.1126/science.aad3456](https://doi.org/10.1126/science.aad3456) | context | With [23]: relevant to whether Cardiac Myosin's real mechanism is representable by a single catalytic-domain contact graph — see ref [5]'s takeaway (oligomer/interacting-heads concern). Not yet checked against this citation directly. | [[TASK-0229.007]] (indirect) |
| 23 | Anderson RL, et al. Deciphering the super relaxed state of human β-cardiac myosin and the mode of action of mavacamten from myosin molecules to muscle fibers. PNAS. 2018;115:E8143-E8152. | [10.1073/pnas.1809540115](https://doi.org/10.1073/pnas.1809540115) | context | See [22]. | [[TASK-0229.007]] (indirect) |
| 24 | Dang CV, Reddy EP, Shokat KM, Soucek L. Drugging the "undruggable" cancer targets. Nat Rev Cancer. 2017;17:502-508. | [10.1038/nrc.2017.36](https://doi.org/10.1038/nrc.2017.36) | context | c-Myc undruggability and intrinsic disorder — connects to ref [4]'s H4.3 (disorder amplifies allosteric coupling) as the only principled handle on the c-Myc/1NKP no-ground-truth target. | — |
| 25 | Shen Q, et al. ASD v3.0: unraveling allosteric regulation with structural mechanisms and biological networks. Nucleic Acids Res. 2016;44:D527-35. | [10.1093/nar/gkv902](https://doi.org/10.1093/nar/gkv902) | in use | The Allosteric Database — already registered/used elsewhere in the register (e.g. [[TASK-0081]]'s generalization set). See ref [6]'s takeaway for the proposed multi-site answer-key audit against it. | [[TASK-0229.003]] |

---

## Method/tool papers (non-challenge-bibliography)

Cited by name in code or `RESULTS.md` but not part of the challenge's own
[1]-[25] list. Seeded with what this session already knows to be load-bearing;
add to this table as new ones get cited — see the protocol doc for the exact
process.

| Citation | DOI/URL | Where used | Takeaway |
|---|---|---|---|
| Khaneja N, Reiss T, Kehlet C, Schulte-Herbrüggen T, Glaser SJ. Optimal control of coupled spin dynamics: design of NMR pulse sequences by gradient ascent algorithms. J Magn Reson. 2005;172:296-305. | [10.1016/j.jmr.2004.11.004](https://doi.org/10.1016/j.jmr.2004.11.004) | `allostery/control_effort.py` (GRAPE optimal control) | Source of the GRAPE algorithm used for [[TASK-0156]]'s minimum-control-energy observable. Citation verified against the live article at the time ([[TASK-0156]]'s Done section). |
| Atilgan AR, Atilgan C. Perturbation-response scanning reveals ligand entry-exit mechanisms of ferric binding protein. PLoS Comput Biol. 2009;5:e1000544. | [10.1371/journal.pcbi.1000544](https://doi.org/10.1371/journal.pcbi.1000544) | `allostery/lowmode_predictor.py` (`prs_low`) | Perturbation Response Scanning — the classical baseline `prs_low`/GRAPE control-effort work is checked against. |
| Pierce NA, Winfree E. Protein Design is NP-hard. Protein Eng. 2002;15:779-782. | [10.1093/protein/15.10.779](https://doi.org/10.1093/protein/15.10.779) | [[TASK-0204]] | Side-chain rotamer packing complexity-class citation for the fixed-backbone packing MRF treewidth argument. |
| Chmura B, Lan Z, Rode MF, Sobolewski AL. Photodetachment and excited state dynamics of the water dimer anion. J Chem Phys. 2009;131:134307. | [10.1063/1.3244567](https://doi.org/10.1063/1.3244567) | `.ai/tasks/DONE/TASK-9000-9005-*.md` (methodology-validation branch `val-9xxx`) | An externally-validated "known system" used to sanity-check this project's own propagator/statistics pipeline against a real, published result (the orchestrating user's own prior work). |

---

## Not yet reviewed

Papers/sources referenced somewhere in `RESULTS.md`/task files but not yet
pulled into this table (found while building this file, not chased down
further — add as encountered, per the protocol doc):

- EvoEF2's own methods reference (Huang X, Pearce R, Zhang Y. `tools/evoef2/README.md` cites the tool; the underlying EvoEF2 paper itself has not been pulled in here).
- Any citation inside `notebooks/H_new_engineering (4) CLEAN.ipynb` not already surfaced via a task file.
