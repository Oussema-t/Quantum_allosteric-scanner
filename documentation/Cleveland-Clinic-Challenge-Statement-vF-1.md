**==> picture [416 x 293] intentionally omitted <==**

## **Global Quantum + AI Challenge 2026** 

**Cleveland Clinic** 

## Enterprise Challenge Statement 

1 

## 1. Challenge Title 

Unlocking undruggable targets: quantum simulation of allosteric signal propagation 

## 2. **Executive Summary** 

Over 85% of disease-causing proteins are currently considered undruggable. These proteins lack deep, obvious active sites where traditional small-molecule drugs can bind. For these intractable targets, the only viable therapeutic strategy is allostery, i.e., identifying hidden distal regulatory pockets on the protein surface [1,2] that, when bound, transmit a signal to shut down the active site from a distance [3–6]. 

Unlocking allosteric targeting would revolutionize drug discovery, enabling therapeutic intervention for historically intractable diseases driving cancer, heart disease, as well as many other therapeutic areas. For the global healthcare industry, this unlocks a new paradigm of drug design, offering hope to patients with currently untreatable conditions. 

Detecting these hidden communication channels classically is computationally prohibitive. It requires months of Molecular Dynamics (MD) simulations to observe the rare fluctuations that transmit signals across a protein structure. Current approximations are often too linear to capture the complex, non-linear dynamics of biological signal propagation, leaving vast areas of the proteome unexplored [7–9]. 

Quantum computers offer a unique advantage in simulating non-local correlations and interference effects, which are analogous to how biological signals propagate through a complex protein network [10,11]. This challenge asks participants to hypothesize and demonstrate that quantum information propagation can identify allosteric pathways more accurately or efficiently than classical diffusive models. 

Participants must develop a quantum algorithm approach that takes a protein structure as input and identifies potential allosteric sites based on structural fluctuations or via dynamic connectivity to an active site. 

2 

## 3. Industrial and Operational Context 

This challenge addresses a critical bottleneck at the very beginning of the pharmaceutical R&D value chain: the target identification and validation phase. Currently, the industry faces the productivity challenge often described as Eroom’s Law [12] (Figure 1), where inflation-adjusted cost of developing a new drug has historically doubled every nine years. A primary driver of this inefficiency is the high attrition rate of clinical candidates that fail because they targeted the wrong mechanism or the target protein is simply undruggable. 

**==> picture [498 x 246] intentionally omitted <==**

**Figure 1:** Eroom’s Law – the declining trend in pharmaceutical R&D efficiency. The cost of developing a new drug has doubled approximately every nine years since the 1950s, a trend known as Eroom’s Law. This inefficiency is largely driven by high attrition rates in clinical trials due to poor target validation. 

In the standard drug discovery workflow, medicinal chemists and structural biologists identify a target protein directly implicated in the pathogenesis of a specific disease. This process typically involves retrieving high-resolution structures from the Protein Data Bank (PDB) [13], obtained through X-ray crystallography, Nuclear Magnetic 

3 

Resonance (NMR), or Cryo-EM. These models serve as a base for structure-based drug design, where classical docking software is often employed to scan for deep, hydrophobic pockets suitable for the binding of small molecules [14]. However, if the protein’s active site is too flat, featureless, involved in Protein-Protein Interfaces (PPIs) or solvent-exposed, which is the case for the majority of the human proteome, the traditional approaches often fail. This leads to the target being deprioritized and categorized as undruggable, leaving vast areas of potentially high-value intellectual property and therapeutic benefit unexplored. 

Even when a target is selected, the subsequent step often involves high-throughput screening, where millions of chemical compounds are physically tested against the protein. This process is prohibitively expensive and inefficient if the screening is performed blindly without knowing where on the protein surface to target. 

The solution proposed in this challenge aims to insert a quantum enable “allosteric scanner” directly upstream from the more expensive classical screening steps. Operationalized within a computational biology unit, this tool would ingest static PDB structures of “failed” targets and output a dynamic probability map of cryptic/allosteric binding sites. This output would serve as a strategic roadmap for medicinal chemists, allowing them to focus their library design efforts on specific regions of the protein surface that are mechanistically connected to disease function. By shifting the paradigm from static pocket detection to a more efficient quantumenabled dynamic signal mapping, this workflow has the potential to rescue thousands of high-value biological targets, drastically reducing the cost of physical screening. Hence, it can ultimately lower the clinical attrition rate by validating the mechanism of action before a screening campaign or drug synthesis. 

## 4. Challenge Objective 

4.1 Primary Objective: The single most important objective is to maximize the predictive accuracy of the quantum algorithm in identifying experimentally validated allosteric sites. Participants must build a quantum circuit that simulates signal propagation through the protein structure, outputting a ranking of residues based on their dynamic connectivity, in most cases, to an active site. Success is defined by the 

4 

algorithm’s ability to assign statistically significantly higher scores to known distal regulatory residues compared to random background residues and non-functional surface pockets. Participants are free to hypothesize and define the specific quantum metric that serves as the proxy for this biological signal. 

4.2 Secondary Objectives: To ensure the solution is practical for real-world deployment, participants should address noise resilience, scalability, and interpretability. The proposed algorithms must be robust against the noise inherent in current quantum processors, demonstrating stability of the signal propagation metric despite gate errors and limited coherence times. Given that many relevant protein targets exceed the qubit capacity of current devices if mapped 1-to-1, participants should also demonstrate a method for coarse-graining the protein structure and prove that this compression retains the essential topological signal. We also aim to lower the entry level, ensuring that medicinal chemists can leverage quantum algorithms without extensive training. The output must be directly actionable, prioritizing 3D visualization of the quantum connectivity maps and a clear logic linking the chosen quantum metric to the biological phenomenon. Comparison to classical analogs, where relevant, should be analyzed. 

## 5. Problem Definition 

Inputs: Participants will be provided with structural data for a set of benchmark proteins obtained from the RCSB Protein Data Bank. 

Outputs: The solution must generate: 

1. The Connectivity Matrix: A 𝑁× 𝑁 matrix where the entry (𝑖, 𝑗) represents the calculated quantum connectivity strength between residue 𝑖 and residue 𝑗. 

2. The Hit List: A ranked list of the top 5 predicted allosteric sites (residue indices) for each target protein. 

3. Methodological Report: A brief explanation of the quantum metric chosen and why it serves as a proxy for biological signal transmission. 

Constraints: 

5 

1. Hardware: Solutions may leverage gate-based quantum, quantum-inspired, or hybrid approaches, provided the proposal demonstrates a credible path to execution on near-term or fault-tolerant quantum hardware. 

2. Circuit Depth: Proposals must demonstrate awareness of coherence time limitations. Deep, unoptimized circuits that cannot run on near-term hardware will be penalized. 

3. No Classical MD: This solution cannot rely on classical MD trajectories as inputs. The goal is to predict the dynamics _ab initio_ from topology. 

4. For this challenge, participants will have access to AWS Braket and Classiq services, provided as part of the challenge infrastructure at no cost. 

Scope and Assumptions: 

- Included: The catalytic domains of the proteins. 

- Excluded: Solvents (water molecules), co-factors, and complex posttranslational modifications (unless modeled as simple nodes). 

- Assumption: We assume the elastic network hypothesis [8,15,16], i.e., that the topology of the contact network is the primary driver of signal propagation, allowing us to abstract away specific atomic force fields. 

## 6. Data and Resources 

The provided protein structures are sourced from the public RCSB PDB (rcsb.org). Participants are encouraged to use open-source frameworks (like Qiskit [17]) to ensure reproducibility. 

To validate the predictive power of the proposed quantum approach, this challenge employs specific targets that were historically considered undruggable until a specific allosteric pocket was characterized. 

Participants must use the unbound structure as input and blind-predict the location of the allosteric pocket known to exist in the drug-bound validation structure. Table 1 reports the list of targets. 

**Target Protein Challenge Objective Input Validation** 

6 

||||||
|---|---|---|---|---|
|**(Disease**<br>**Area)**|**Class**||**Structure**|**Structure**|
|KRAS<br>G12C<br>(Oncology)|GTPase|Identify the cryptic “Switch-II”<br>pocket locked by Sotorasib<br>(AMG 510) [18,19]|4OBE|6OIM|
|BCR-ABL1<br>(Oncology)|Tyrosine<br>Kinase|Identify the distal “Myristoyl”<br>pocket used by Asciminib to<br>bypass resistance [20,21]|1OPL|5MO4|
|Cardiac<br>Myosin<br>(Cardiology)|Motor<br>Protein|Identify the mechanical site<br>where Mavacamten stabilizes<br>the “super-relaxed state”<br>[22,23]|5TBY|6C1H|



**Table 1:** List of targets used to score the predictive accuracy of the quantum algorithms. For each target, the unbound (apo) PDB structure serves as the input, and the drug-bound (holo) PDB structure serves as the ground truth for validating the predicted allosteric site. 

Beyond the validation set, participants are invited to apply their algorithm to c-Myc (1NKP – cMyc/Max heterodimer), a transcription factor dysregulated in >50% of cancers [24]. It is widely considered an undruggable target due to its disordered nature and lack of FDA-approved allosteric inhibitors. 

In this case, results will be evaluated based on consensus across winning teams and theoretical docking viability. 

Please note that c-Myc and the targets listed in Table 1 constitute the minimum set required for submission. However, participants are highly encouraged to test the robustness of their quantum approach on additional targets of their choice to demonstrate generalizability and scalability. For this purpose, participants may refer to the Allosteric Database (ASD) [25] to select other proteins with known allosteric sites. 

7 

## 7. References 

1. Zheng W. Predicting allosteric sites using fast conformational sampling as guided by coarse-grained normal modes. J Chem Phys. 2023;158: 124127. doi:10.1063/5.0141630 

2. Koseki J, Motono C, Yanagisawa K, Kudo G, Yoshino R, Hirokawa T, et al. CrypToth: Cryptic Pocket Detection through Mixed-Solvent Molecular Dynamics Simulations-Based Topological Data Analysis. J Chem Inf Model. 2025;65: 5567–5575. doi:10.1021/acs.jcim.4c02111 

3. Nussinov R, Tsai C-J. Allostery in disease and in drug discovery. Cell. 2013;153: 293–305. doi:10.1016/j.cell.2013.03.034 

4. Motlagh HN, Wrabl JO, Li J, Hilser VJ. The ensemble nature of allostery. Nature. 2014;508: 331–339. doi:10.1038/nature13001 

5. Changeux J-P, Edelstein SJ. Allosteric Mechanisms of Signal Transduction. Science. 2005 [cited 28 Jan 2026]. doi:10.1126/science.1108595 

6. Tsai C-J, Nussinov R. A unified view of “how allostery works.” PLoS Comput Biol. 2014;10: e1003394. doi:10.1371/journal.pcbi.1003394 

7. Stock G, Hamm P. A non-equilibrium approach to allosteric communication. Philos Trans R Soc Lond B Biol Sci. 2018;373. doi:10.1098/rstb.2017.0187 

8. Chennubhotla C, Bahar I. Signal propagation in proteins and relation to equilibrium fluctuations. PLoS Comput Biol. 2007;3: 1716–1726. doi:10.1371/journal.pcbi.0030172 

9. Gunasekaran K, Ma B, Nussinov R. Is allostery an intrinsic property of all dynamic proteins? Proteins: Structure, Function, and Bioinformatics. 2004;57: 433– 443. doi:10.1002/prot.20232 

10. Mitarai K, Fujii K. Overhead for simulating a non-local channel with local channels by quasiprobability sampling. Quantum. 2021;5: 388. doi:10.22331/q-2021-0128-388 

11. Oh EK, Krogmeier TJ, Schlimgen AW, Head-Marsden K. Singular Value Decomposition Quantum Algorithm for Quantum Biology. ACS Phys Chem Au. 2024;4: 393–399. doi:10.1021/acsphyschemau.4c00018 

12. Scannell JW, Blanckley A, Boldon H, Warrington B. Diagnosing the decline in pharmaceutical R&D efficiency. Nature Reviews Drug Discovery. 2012;11: 191–200. doi:10.1038/nrd3681 

8 

13. wwPDB consortium, Burley SK, Berman HM, Bhikadiya C, Bi C, Chen L, et al. Protein Data Bank: the single global archive for 3D macromolecular structure data. Nucleic Acids Res. 2018;47: D520–D528. doi:10.1093/nar/gky949 

14. Lu S, Li S, Zhang J. Harnessing allostery: a novel approach to drug discovery. Med Res Rev. 2014;34: 1242–1285. doi:10.1002/med.21317 

15. Das A, Gur M, Cheng MH, Jo S, Bahar I, Roux B. Exploring the conformational transitions of biomolecular systems using a simple two-state anisotropic network model. PLoS Comput Biol. 2014;10: e1003521. doi:10.1371/journal.pcbi.1003521 

16. Erman B. The gaussian network model: precise prediction of residue fluctuations and application to binding problems. Biophys J. 2006;91: 3589–3599. doi:10.1529/biophysj.106.090803 

17. Javadi-Abhari A, Treinish M, Krsulich K, Wood CJ, Lishman J, Gacon J, et al. Quantum computing with Qiskit. arXiv [quant-ph]. 2024. doi:10.48550/ARXIV.2405.08810 

18. Ostrem JM, Peters U, Sos ML, Wells JA, Shokat KM. K-Ras(G12C) inhibitors allosterically control GTP affinity and effector interactions. Nature. 2013;503: 548–551. doi:10.1038/nature12796 

19. Canon J, Rex K, Saiki AY, Mohr C, Cooke K, Bagal D, et al. The clinical KRAS(G12C) inhibitor AMG 510 drives anti-tumour immunity. Nature. 2019;575: 217–223. doi:10.1038/s41586-019-1694-1 

20. Wylie AA, Schoepfer J, Jahnke W, Cowan-Jacob SW, Loo A, Furet P, et al. The allosteric inhibitor ABL001 enables dual targeting of BCR–ABL1. Nature. 2017;543: 733–737. doi:10.1038/nature21702 

21. Schoepfer J, Jahnke W, Berellini G, Buonamici S, Cotesta S, Cowan-Jacob SW, et al. Discovery of Asciminib (ABL001), an Allosteric Inhibitor of the Tyrosine Kinase Activity of BCR-ABL1. Journal of Medicinal Chemistry. 2018 [cited 30 Jan 2026]. doi:10.1021/acs.jmedchem.8b01040 

22. Green EM, Wakimoto H, Anderson RL, Evanchik MJ, Gorham JM, Harrison BC, et al. A small-molecule inhibitor of sarcomere contractility suppresses hypertrophic cardiomyopathy in mice. Science. 2016 [cited 30 Jan 2026]. doi:10.1126/science.aad3456 

23. Anderson RL, Trivedi DV, Sarkar SS, Henze M, Ma W, Gong H, et al. Deciphering the super relaxed state of human β-cardiac myosin and the mode of action of mavacamten from myosin molecules to muscle fibers. Proceedings of the National Academy of Sciences. 2018;115: E8143–E8152. doi:10.1073/pnas.1809540115 

9 

24. Dang CV, Reddy EP, Shokat KM, Soucek L. Drugging the “undruggable” cancer targets. Nature Reviews Cancer. 2017;17: 502–508. doi:10.1038/nrc.2017.36 

25. Shen Q, Wang G, Li S, Liu X, Lu S, Chen Z, et al. ASD v3.0: unraveling allosteric regulation with structural mechanisms and biological networks. Nucleic Acids Res. 2016;44: D527–35. doi:10.1093/nar/gkv902 

