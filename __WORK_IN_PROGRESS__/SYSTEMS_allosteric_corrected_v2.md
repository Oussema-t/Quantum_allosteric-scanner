# SYSTEMS Allosteric Dataset — corrected & verification-gated (v2.0)

**Date:** 2026-06-21
**Supersedes:** v1.2 (15-candidate expanded list).

## Why every `lit_pocket` is now an empty list

The single most important correction: **do not hand-transcribe pocket residues
into this file.** In v1.2 every residue list was one of (a) fabricated
(MYC_MAX `[40,44,48,52,56]` is an arbitrary i,i+4 pattern with no source),
(b) contaminated with active-site residues (KRAS included the P-loop), or
(c) unverifiable literature numbers that "may shift ±5 residues" by the author's
own admission. Transcribed numbers also break across PDB constructs/isoforms
(the ABL1 1a/1b +19 offset is a live hazard here).

**Correct procedure:** `pocket = residues of the APO structure whose Cα maps
(by global sequence alignment, NOT residue-number equality) to a HOLO residue
with any heavy atom within 4.5 Å of the bound ALLOSTERIC ligand.** This is the
job of `labels.py`. The lists below are therefore `[]` by design, with a
per-entry note on which holo ligand to contact and what to watch for.

`confidence` below = confidence in the **structural anchors** (apo/holo/ligand),
not in any residue list. "VERIFIED" = checked against literature this pass.

---

## Verified challenge targets (the 4 that matter)

```python
SYSTEMS = {

 # --- VERIFIED against literature 2026-06-21 ---
 "KRAS_G12C": dict(
     apo="4OBE", holo="6OIM", chain="A", cutoff=8.0,
     objective="Switch-II cryptic pocket (SII-P); sotorasib/AMG510 covalent at Cys12",
     drug_ligand="MOV",            # VERIFIED: 6OIM ligand MOV = AMG510 (sotorasib) + GDP + Mg
     func_ligand=["GDP"],          # nucleotide present in holo; defines active site for exclusion
     allosteric_pocket=[],         # DERIVE from MOV contacts. Key cryptic residues in lit: His95/Tyr96/Gln99
                                   #   plus switch-II loop ~58-72. EXCLUDE Cys12 / P-loop (orthosteric/covalent anchor).
     confidence=0.95),

 "BCR_ABL1": dict(
     apo="1OPL", holo="5MO4", chain="A", cutoff=8.0,
     objective="Myristoyl pocket; asciminib (ABL001) allosteric inhibitor",
     drug_ligand="ASCIMINIB",      # *** CRITICAL FIX *** 5MO4 contains BOTH asciminib (allosteric, myristoyl)
                                   #   AND nilotinib (NIL, ATP-site ORTHOSTERIC). pick_drug() grabbed NIL = WRONG.
                                   #   Select the asciminib component; verify its 3-letter code on RCSB (NOT 'NIL').
     func_ligand=["NIL"],          # nilotinib marks the ATP/active site -> use to EXCLUDE, not predict
     allosteric_pocket=[],         # DERIVE from asciminib contacts ONLY.
     warnings=["5MO4 is mutated (T315I/D363N) and has gaps completed from 1OPL in lit; "
               "ABL1 1a/1b numbering differs by ~19 -> resolve numbering before any mapping."],
     confidence=0.90),

 "CARDIAC_MYOSIN": dict(
     apo="5TBY", holo="6C1H", chain=None, cutoff=8.0,  # chain=None: resolve assembly first
     objective="Mavacamten super-relaxed/IHM stabilization site",
     drug_ligand="MAVACAMTEN?",    # *** UNCONFIRMED *** notebook found no drug in 6C1H (only Mg).
                                   #   VERIFY 6C1H actually contains mavacamten on RCSB before use.
     func_ligand=["ADP","ATP"],
     allosteric_pocket=[],
     warnings=["5TBY is the interacting-heads-motif (IHM) ASSEMBLY: huge (N~954), multi-chain "
               "(2 heads + ELC/RLC + S2), low/no crystallographic resolution -> NOT a clean motor-domain graph. "
               "Consider a clean S1/motor-domain mavacamten crystal as an alternative holo. "
               "QUARANTINE until the apo construct and the 6C1H ligand are both confirmed."],
     confidence=0.40),

 "MYC_MAX": dict(
     apo="1NKP", holo=None, chain="A,B", cutoff=8.0,  # A=Myc, B=Max bHLH-LZ on E-box DNA
     keep_nucleic=True,            # 1NKP includes DNA (DO NOT strip)
     objective="No validated allosteric pocket. Challenge scores by consensus + docking viability only.",
     drug_ligand=None,
     func_ligand=["DNA"],
     allosteric_pocket=[],         # NONE exists. Myc/Max are IDPs with no surface pocket in the folded dimer.
                                   #   v1.2 list [40,44,48,52,56] was fabricated -> removed.
     warnings=["IDP transcription factor; folds on DNA/partner binding. Topology-only ENM on the folded "
               "coiled-coil is a different regime than the globular enzyme targets. Known small-molecule "
               "sites (10058-F4 / 10074-G5) bind the DISORDERED monomer (~Glu363-Ile381), not the 1NKP dimer."],
     confidence=0.75),  # anchor (1NKP) is real; the 'pocket' concept is not applicable

 # --- ASD EXPANSION: anchors NOT re-verified this pass. Treat as DRAFT. ---
 # For each: verify apo/holo/ligand on RCSB, resolve the biological assembly
 # (oligomeric allosteric proteins below LOSE their allostery if cut to one chain),
 # then DERIVE the pocket from the holo allosteric ligand.

 "PTP1B": dict(apo="1SUG", holo="1T49", chain="A", cutoff=8.0,
     objective="Allosteric site ~20 A from catalytic Cys215 (alpha3/alpha7, BB-series)",
     drug_ligand="VERIFY",         # confirm the 1T49 allosteric ligand code on RCSB (v1.2 'BB2' unverified)
     func_ligand=["pTyr/active-site Cys215"],
     allosteric_pocket=[], confidence=0.70),

 "GLUCOKINASE": dict(apo="1V4S", holo="3H1V", chain="A", cutoff=8.0,
     objective="Allosteric activator (GKA) site ~20 A from glucose",
     drug_ligand="VERIFY", func_ligand=["Glucose"], allosteric_pocket=[], confidence=0.60),

 "ATCase": dict(apo="6AT1", holo="4KH1", chain="VERIFY", cutoff=8.0,
     objective="Regulatory-subunit CTP/UTP allosteric site (T->R)",
     drug_ligand="CTP?",
     warnings=["Allostery is INTER-SUBUNIT (regulatory vs catalytic chains). "
               "Single-chain analysis destroys the mechanism. Resolve the assembly."],
     func_ligand=["Asp","carbamoyl-P"], allosteric_pocket=[], confidence=0.55),

 "CASPASE1": dict(apo="1ICE", holo="2FQQ", chain="VERIFY", cutoff=8.0,
     objective="Allosteric thiol site at dimer interface (zymogen reversal)",
     drug_ligand="VERIFY", func_ligand=["substrate"], allosteric_pocket=[], confidence=0.55),

 "CASPASE7": dict(apo="1F1J", holo="1SHL", chain="VERIFY", cutoff=8.0,
     objective="Allosteric dimer-interface site (FICA)",
     drug_ligand="FICA?", func_ligand=["substrate"], allosteric_pocket=[], confidence=0.50),

 "HEMOGLOBIN": dict(apo="2HHB", holo="1HHO", chain="VERIFY", cutoff=8.0,
     objective="2,3-BPG allosteric site (T->R, O2 cooperativity)",
     drug_ligand="BPG?",
     warnings=["BPG binds in the central cavity BETWEEN beta-subunits of the alpha2beta2 tetramer. "
               "Requires the full assembly; meaningless on a single chain. NB 2HHB is deoxy(T), "
               "1HHO is oxy(R) -- this pair is a STATE change, confirm it is the intended apo/holo sense."],
     func_ligand=["O2","heme"], allosteric_pocket=[], confidence=0.55),

 "TAR_RECEPTOR": dict(apo="1LIH", holo="1VLT", chain="A", cutoff=8.0,
     objective="Transmembrane chemotaxis signaling (aspartate)",
     drug_ligand="Asp?",
     warnings=["Periplasmic/TM signaling protein; 'allosteric pocket' is the aspartate site at a dimer "
               "interface. Transmembrane context may not suit a soluble-domain ENM. Lower priority."],
     func_ligand=["Asp"], allosteric_pocket=[], confidence=0.45),

 "GLYCOGEN_PHOSPHORYLASE": dict(apo="1GPY", holo="1A8I", chain="VERIFY", cutoff=8.0,
     objective="AMP allosteric site (T->R)",
     drug_ligand="AMP?",
     warnings=["Functional dimer; AMP site near subunit interface. Resolve assembly."],
     func_ligand=["Pi","G1P"], allosteric_pocket=[], confidence=0.60),

 "PFK": dict(apo="1PFK", holo="3O8L", chain="VERIFY", cutoff=8.0,
     objective="FBP/ADP allosteric site (bacterial PFK, homotetramer)",
     drug_ligand="VERIFY",
     warnings=["Bacterial (E. coli) PFK -- may not transfer to human targets. "
               "Homotetramer; allosteric site at subunit interface. v1.2 pocket was literature-guessed."],
     func_ligand=["F6P","ATP"], allosteric_pocket=[], confidence=0.45),

 "LDH": dict(apo="VERIFY", holo="2LDH", chain="VERIFY", cutoff=8.0,
     objective="Substrate-inhibition / regulatory site (borderline 'allostery')",
     drug_ligand=None,
     warnings=["v1.2 listed apo as BOTH 6LDH and 1LDH in two dicts -- INCONSISTENT, resolve. "
               "LDH 'allostery' is substrate inhibition, a weak/borderline case; consider dropping."],
     func_ligand=["pyruvate","NADH"], allosteric_pocket=[], confidence=0.35),

 "GROEL_SUBUNIT": dict(apo="1GRL", holo="1AON", chain="VERIFY", cutoff=8.0,
     objective="GroES-binding / ATP allosteric site (chaperonin cycle)",
     drug_ligand="GroES (protein, not small molecule)",
     warnings=["1AON is the GroEL-GroES-ADP complex (14+7 mer, huge). The 'ligand' is a PROTEIN "
               "(GroES), not a drug -> drug-contact pocket definition does not apply cleanly. "
               "Allostery is inter-ring/inter-subunit. Hard case; low priority."],
     func_ligand=["ATP"], allosteric_pocket=[], confidence=0.45),
}
```

## Summary of corrections vs v1.2
- **BCR_ABL1**: drug switched from the orthosteric nilotinib (NIL) to **asciminib** (allosteric, myristoyl). 5MO4 holds both; the previous pipeline picked the wrong one. (VERIFIED: 5MO4 = ABL1 + asciminib + nilotinib.)
- **KRAS_G12C**: drug code MOV confirmed (sotorasib); pocket reframed to SII-P (His95/Tyr96/Gln99), Cys12/P-loop flagged for exclusion. (VERIFIED.)
- **CARDIAC_MYOSIN**: confidence dropped to 0.40 and quarantined — 5TBY is the IHM assembly (huge/low-res), 6C1H drug content unconfirmed. (VERIFIED 5TBY=IHM.)
- **MYC_MAX**: fabricated pocket removed; documented as IDP with no folded-dimer pocket; `keep_nucleic` set. (VERIFIED: Myc/Max are IDPs "with no effective pockets on their surfaces".)
- **All entries**: residue lists emptied; pockets to be derived from holo allosteric-ligand contacts.
- **Oligomeric targets** (ATCase, hemoglobin, glycogen phosphorylase, PFK, GroEL): flagged that single-chain analysis destroys inter-subunit allostery — resolve the biological assembly.
- **LDH**: apo PDB inconsistency (6LDH vs 1LDH) flagged; borderline allostery, candidate to drop.

---

## A learning base for MYC_MAX

MYC is the odd one out: an intrinsically disordered transcription factor with
**no classical pocket**, folding only on DNA/partner binding. A topology-only
ENM/CTQW on the folded 1NKP coiled-coil is a different regime from the globular
enzymes above, so a useful learning base must share MYC's *structural class*
(disorder-to-order TF / shallow PPI interface), not just "be a protein."

Three tiers, best first. **Verify all PDB IDs on RCSB before use** — these are
candidates from literature, not anchors I re-derived this pass.

**Tier 1 — undruggable TF WITH a real validated cryptic pocket (best analog).**
- **p53 (Y220C cryptic pocket).** The gold-standard case: an "undruggable"
  transcription factor with a literature-confirmed *cryptic* pocket created by
  the Y220C mutation, clean apo/holo pairs, and actual stabilizer drugs
  (PhiKan083, PK7088, the PC14586/rezatapopt series). This is the closest thing
  to MYC that also has ground truth, so it's the single most valuable addition.
  (Candidate PDBs: apo Y220C ~2J1X/1UOL; holo with PhiKan083 ~2VUK — verify.)

**Tier 2 — same fold/topology (bHLH-LZ / bZIP on DNA), for calibrating what the
method outputs on a coiled-coil TF (mostly no supervised pocket).**
- **Max homodimer** (Myc's own partner; same bHLH-LZ).
- **MAD-MAX / MNT-MAX** heterodimers (same family).
- **USF1**, **SREBP-1a**, **MyoD/E47**, **NeuroD** (bHLH on DNA).
- **GCN4** leucine zipper, **Fos-Jun (AP-1)**, **C/EBP**, **CREB** (bZIP on DNA).
  These let you check whether the method's output on MYC is an artifact of the
  coiled-coil/DNA topology by comparing across the family.

**Tier 3 — shallow PPI-interface targets with known hot-spots (MYC's real
liability is its dimerization/PPI interface, not a cleft).**
- **β-catenin / TCF** interface; **KIX (CBP) / MLL or pKID**; **Bcl-2 / BAK-BH3**;
  **MDM2 / p53 peptide** (nutlin site). These train the "predict a flat
  interface hot-spot" behavior that MYC actually needs.

**Honest caveat.** For MYC itself, the realistic target is not a 1NKP pocket but
either the dimerization/DNA interface or the transient pockets seen in the
*disordered monomer* (the 10058-F4 / 10074-G5 site, ~Glu363-Ile381), which only
appear in MD ensembles of an AlphaFold monomer — not in a single crystal. So
"predicting MYC's pocket" from one static apo structure may be ill-posed by
construction; p53-Y220C is where a topology method can actually be scored.
```
