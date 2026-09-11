# External adversarial review — Phase-1 submission package, 2026-09-11

**Source:** external adversarial reviewer, given copies of the repository (which is
**private**) to review against the current package.
**Reviewed artefact:** `SUBMISSION_PACKAGE/` at the state shipped for review.
**Status:** recorded verbatim. Triage and verification are tracked separately —
nothing below has been accepted or rejected by this file.

---

**Verdict:** the science is the strongest part of this package. The main risks are elsewhere. Several labelling and consistency errors will be hit by any reviewer who checks, and one of them reads as "they ran the scanner on the drug-bound structure." The repository the whole verifiability argument depends on is not publicly reachable. The body overflows the page limit.

## Blockers: fix before sending

1. **The repo is not public.** `github.com/Oussema-t/Quantum_allosteric-scanner` returns 404 to an unauthenticated request, as do both branch URLs. It is not among the 11 public repos on Oussema-t's profile. CP §7, the Team Profile ("checkable by publishing the working repository") and both READMEs all rely on it.

2. **The body is 6 pages plus a spill onto page 7.** The §7 member table and the repo line render on page 7, above "Appendix — References". The README says 6/6. Cheap cuts:
   - §6's first paragraph restates the "Pipeline" paragraph almost word for word (about 5 lines).
   - §1 tells the "retracted four days later" story twice.

3. **`artefacts/README.md` labels `8QYR` as "(apo)".** 8QYR is the beta-cardiac myosin motor domain in the pre-powerstroke state complexed to Mavacamten, and it is Bos taurus. Your register says the apo input is 8QYP with N=704, which matches the shipped matrix, so this is almost certainly a label error. Fix it anyway.
   - The CP's five-guess table omits the cardiac PDB code.
   - The structure table's "8QYP → 8QYR" reads as "Table-1 structure → our substitute."
   - The bovine origin is undisclosed.

4. **The cardiac substitution reason is absent, and the Table-1 pair is never named.** README §D.2 and `03_Problem_Statement_Selection.md` both claim the CP states the reason. It doesn't.
   - Table 1 mandates 5TBY→6C1H. 5TBY is a homology model rigidly fitted to a negatively stained thick-filament reconstruction, at 20.0 Å.
   - 6C1H is rat unconventional myosin-Ib bound to rabbit actin, with ADP ×5 and no mavacamten.
   - Together with 4OBE being wild-type and 1OPL being doubly liganded (item 19), every mandated pair has a verifiable defect. That is the single best piece of evidence for §1's thesis, and it is currently missing.
   - Also add the holo structures (6OIM, 5MO4, 8QYR). The reader can't tell what the AUCs were scored against.

5. **The Team Profile cites "the Concept Proposal's Appendix B" with five retractions.** There is no Appendix B.

6. **Shipped report files contradict the CP.**
   - The KRAS `report.txt` says "CTQW genuinely helps" (ΔAUC +0.171). That rests on one structure with CI width ≈0.35, measured against baselines at 0.346 and 0.342, both below chance.
   - The MYC `report.txt` says "Confidence: high." The CP says "unverified."
   - Four-operator agreement is not confidence. Your own CP shows these operators are all distance detectors, and the register shows observable rank collapse.

## Contradicts your own register

A reviewer is explicitly invited to audit the register, so these matter.

7. **KRAS's "VALID" in the 2/7 rule was computed on 4OBE, the wild-type structure.** Your TASK-0209 framing correction says so. Unless it was re-run on 4LDJ after 25 Aug (my copy of RESULTS ends there), the one passing mandated target passed on the wrong genotype. The fpocket numbers (TASK-0163) are also 4OBE-era.

8. **Coupled conformational search.** Register row 71 (TASK-0213) says "CLOSED … closes the last OPEN quantum-advantage route." CP §2 says it "survives our own screening." Pick one and cite it.

9. **§3 "169–704 qubits".** 169 is 4OBE's N. 4LDJ has N=170.

10. **§3 "neither changes this" (refs [10]/[11]).** Register row 77 found that [11]'s log encoding clears the qubit bar (≈10 system qubits + 1 ancilla), though it still needs 10⁵–10⁶ gates.
    - The fault-tolerant-only verdict survives on gate count.
    - But "one qubit per residue — the convention behind every number" invites the first objection a quantum judge will make: a single-particle walk on N sites needs only ⌈log₂N⌉ qubits.
    - State the binary-encoding cost, and say why unary is kept: the only surviving route, multi-particle interference, needs it.

11. **Apo-draw sensitivity is omitted.**
    - Ten true-G12C apo structures give AUC 0.408–0.595, median 0.482.
    - The cardiac swap 5TBY→8QYP moved AUC by 0.27.
    - Each shipped hit list is one draw. One sentence covers it, and it strengthens §1.

12. **fpocket beats the walk by about 0.3 AUC on KRAS and BCR-ABL1** (0.835 and 0.860, against 0.590 and 0.527 for the walk). The CP omits this, and fpocket is in your own pipeline. Present it as evidence that the benchmark is trivial (TASK-0169's "non-trivial" axis) before a reviewer finds it.

## Statistical claims that break your own standards

13. **`NO_SIGNAL_IN_APO` could not have come out otherwise.**
    - The overlap rule needs score_lo > floor_hi, so a positive verdict would have required scores of roughly 0.80–0.89.
    - The CP's gloss, "carries nothing about that pocket beyond what distance already supplies," is the underpowered-null error your §5 positive-control bullet warns against.
    - CI overlap is also not a test of difference. Bootstrap score−floor paired; they are correlated, so that CI will be narrower. Then relabel as "indistinguishable from floor; detection limit ≈X."

14. **"A well-powered null" (coherent vs decoherent, +0.0023).**
    - No minimum detectable effect is stated.
    - The cohort is about 77% non-distal pockets.
    - §5 says that on the distal subset the design can't detect even proximity (p = 0.89), and the coherence hypothesis is specifically about distal pairs.
    - So the test is powered for the wrong population. Say so; it helps the thesis.

15. **"0.4960 — below chance."** That is at chance.

16. **"No arm clears more than 5 of 276" has no stated criterion.** Uncorrected at α = 0.05 you'd expect about 14 under the null, so the number can't be read without the rule.

17. **Two unreconciled positive-looking numbers.**
    - The combined readout, 0.6203 LOPO with "null passed," appears only in a table cell.
    - A classical ranker reaches AUC 0.626 without the pre-filter (§6).
    - The "strongest result… promoted to a finding" is never named. Next to "none of ours generalises," a reviewer will ask.
    - The Phase-2 criterion "residual AUC ≥ 0.60 LOPO vs matched null" is already met by your own baseline column. The re-audit is marked "Done." So two of three success criteria are pre-achieved.

18. **"Each [AUC] is computed per structure and averaged, none pooled" is too broad.** It cannot apply to the protein-level classifier AUC 0.793. Scope the sentence.

## Hit lists: what a medicinal chemist will see

19. **The BCR-ABL1 five are the ATP site.**
    - 1OPL uses Abl-1b numbering, which is 1a+19. A myristate-site patent lists Glu481, Pro484, Val487, Ile521 in 1OPL numbering; these are the canonical E462/P465/V468/I502 in 1a.
    - That makes 402 the DFG glycine, 338 the hinge, and 301/310/311 the αC region.
    - 1OPL also carries an ATP-site inhibitor, not just myristate: myristic acid and a dichlorophenyl pyridopyrimidinone (P16). "Apo" is wrong twice over, and the CP mentions only the myristate.
    - The KRAS five are also the nucleotide-pocket rim: switch I (29/31/33) and residues next to NKCD (121/122). There are no switch-II residues.
    - State this in one line: "this is what the proximity confound looks like in a deliverable." Have Berke confirm the numbering.

20. **The shipped BCR `hit_list.json` contains a site-level result nobody mentions.** It reports 1 site of 56 residues with zero overlap with the true pocket, centroid 20.4 Å away, and `knob_spread: UNSTABLE` (Jaccard min 0.0). Either mention it or drop it from the file.

21. **The cardiac five are one cluster.** In the shipped matrix, 680–684 couple most strongly to each other and to 127/128/134. The challenge accepts residue indices, but acknowledge that five hits here amount to one site.

22. **c-Myc numbering is not UniProt.** Residue 943 is beyond c-Myc's 439 residues, and 226/243/246 are beyond Max's 160.
    - The CSV has no chain column. Add chain and UniProt numbering.
    - The challenge scores c-Myc on docking viability. The report lists fpocket pockets (all druggability ≤ 0.161, below your own 0.5 bar) without linking any hit to a pocket.
    - The seed used for a protein with no active site is never stated.

## Deliverable files

23. **No shipped file gives the formula for a matrix entry.** I checked the cardiac CSV: 704×704, exactly symmetric, rows sum to 1 ± 1e-6, and the diagonal is the row maximum in 78% of rows. So it is the time-averaged transition probability, and heatmaps will be diagonal-dominated. Say both in the artefacts README.

24. **Seed residues aren't shipped, so the hit list can't be reproduced from the matrix.** §6's "cannot disagree" is unverifiable by a reader. A guessed nucleotide-site seed did not reproduce the cardiac top five.

25. **`report.txt` hygiene.**
    - Three of the four files have no target or PDB header.
    - Seven of 13 metric lines are N/A.
    - TASK/REVIEW references dangle, since the repo is private.
    - V_B, V_R, V_C, V_M and V_T are never defined.
    - `AUC_heat_mean` is not heat diffusion by the file's own note.
    - "optimised" equals "default."
    - §6 promises "provenance, controls run, cohort," and none of it is there.
    - The artefacts README says Section 2 argues "why this metric proxies biological signal transmission." Section 2 argues it doesn't beyond distance. Say that plainly; it is the honest answer to §5's third deliverable.

26. **Smaller file issues.**
    - `*_ci` fields are `[estimate, lo, hi]`.
    - The MYC JSON lacks the verdict fields the README promises.
    - The README gives the package size as 6.3 MB in §B and 8.8 MB in §C. 8.8 MB is consistent with the file sizes.

## Text-level fixes

27. **Structure paragraph.** "We followed it in each case" is wrong, because KRAS rejected the organisers' 8S8C. "All three deviations" should be two deviations plus one retention.

28. **Floats leave three dangling colons:** "each case:", "chance:", "construct:".

29. **Wrong direction or missing referents.**
    - "The agreement measurement above" is in §4, which comes below.
    - "The external claim we are checking" is uncited.
    - "Hardware cost measured below" is never given for either surviving route.

30. **§3 contradicts itself.** It calls the 105-structure extraction the "largest single analysis," then describes the 1022-protein HPC sweep.

31. **Citations and attributions.**
    - 89.8% and 84% are both presented as [4]'s headline.
    - Check whether 98.1% is Wu et al.'s number on CASBench rather than [5]'s.
    - "The sponsor's own group": the paper lists authors from the Cleveland Clinic Genome Center, Lerner Research Institute. Name the group; Cleveland Clinic has more than one quantum effort.
    - "Mandated ablation": mandated by whom?
    - "5 of 7 standard targets": four were your picks.

32. **A build sentinel is in the page-7 text layer.** `SUBMISSION_BUILD_APPENDIX_START_7f3a9c` is invisible when rendered, but it survives copy-paste and any automated screening.

33. **Team Profile.**
    - "Since 2010: 14 years in QA" conflicts with the 2010–2012 postdoc. It should read "since 2012."
    - I can't find a "Gemini 2.6 Pro"; check the version string.
    - "Most of the investigation … are" should be "is."

## Strategic: rubric coverage

- **§4.1 says participants "must build a quantum circuit."** You did transpile against FakeSherbrooke (538–1486 two-qubit gates at coarse resolution, fidelity about 0.015). The CP reports only analytic counts. One clause meets the letter of 4.1.
- **§4.2 noise resilience.** You tested it; the phase-free robustness hypothesis was falsified on balance. It's absent from the CP.
- **§4.2 3D visualisation.** If the main-branch 3Dmol app is public, one clause covers it.
- **Phase 2 contains zero quantum execution.** That is scientifically defensible, but it puts Technical (25%) and Feasibility (20%) at risk.
  - Option: a small, pre-registered Braket/Classiq arm using the challenge's own ref [11] log encoding.
  - Frame it as a hardware noise measurement and an instrument test subject, not an advantage claim.
  - Trade-off: page budget, and it won't find signal.

## Checked and correct

- Five-guess table = CSV = JSON.
- AUCs 0.514/0.541/0.548 match the report files.
- All floor CIs contain the score, and all score CIs contain 0.5.
- The arithmetic holds: 80%, 221, 99/118, 57.6%, 17.8%, 31/32 with 19+10+3, and 99.8/137 ≈ 73%.
- The Kais preprint and the Cleveland Clinic authorship of [8] exist.

## Couldn't check

- The uploads were deduplicated by filename, so only the cardiac matrix, the BCR JSON and the cardiac `report.txt` reached disk. The other three reports and the MYC JSON I saw only as text, and the KRAS/BCR/MYC matrices not at all.
- With the repo inaccessible and RESULTS ending 25 Aug, 0.6203, +0.199, 137/99.8, 1233 and 0.793 are unverified.
