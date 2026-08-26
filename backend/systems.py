"""
Validated benchmark metadata — ported verbatim from the research notebook (§1).

Schema
------
chain          : shared chain letter(s), used for both apo and holo unless overridden.
apo_chain / holo_chain : TASK-0219 -- optional per-role override for targets whose
                 apo and holo structures use different chain letters for the same
                 biological chain; falls back to `chain` when absent (every target
                 that only sets `chain` is unaffected). Mirrors
                 __WORK_IN_PROGRESS__/config/targets.yaml's `apo_chains`/
                 `holo_chains` pattern (TASK-0127).
active_site    : functional/catalytic residues we SEED signal from (no leakage).
pocket_full    : full validated allosteric pocket, per contact cutoff (Angstrom).
pocket_distal  : distal-only subset (blind distal-discovery test).
top5_full / top5_distal : the 5 primary target residues for each scoring mode.
covalent_anchor: covalent attachment residue (None if non-covalent).

For each target, the unbound (apo) PDB is the input; the drug-bound (holo) PDB is
the ground truth for validating the predicted allosteric site.
"""

SYSTEMS = {

    # TASK-0270 (2026-08-26): `apo` fixed from "4OBE" (WILD-TYPE KRAS, not
    # G12C -- chain A residue 12 is GLY, confirmed directly, TASK-0155/
    # TASK-0192) to "4LDJ" (genuinely G12C, confirmed directly). The
    # organisers' 2026-08-26 clarification sanctioned an apo re-run after
    # this defect was reported to them (documentation/
    # 2026-08-26-organiser-clarifications.md item 2); their own suggested
    # structure, 8S8C, RCSB-verified live and found HOLO (MK-1084-bound),
    # not usable as an apo replacement. 4LDJ chosen on structural grounds:
    # genuinely G12C, GDP+MG only, 1.15 A, single chain A -- see TASK-0270's
    # own Done section and __WORK_IN_PROGRESS__/config/targets.yaml's
    # identical fix for the full rationale, including a real bug found in
    # TASK-0155's own "10 verified" candidate pool (8 of 10 were actually
    # drug-bound, not apo -- corrected in that task's own file).
    # DECISIVE CONSEQUENCE: the register's own headline KRAS_G12C
    # floor-clear result does not survive the genotype fix --
    # NO_FAILURE_DETECTED (4OBE) -> NO_SIGNAL_IN_APO (4LDJ); ENM validity
    # r=0.646 (PASS) -> 0.496 (MARGINAL); AUC 0.557 -> 0.514. `covalent_
    # anchor=12`/`top5_full_named`'s "CYS12" below were already correct as
    # the *biological* target-residue description (independent of which
    # apo PDB is loaded) and are unchanged.
    "KRAS_G12C": dict(
        apo="4LDJ", holo="6OIM", chain="A",
        disease="Oncology", target_class="GTPase", site_name="Switch-II pocket",
        holo_ligand="MOV", holo_ligand_name="Sotorasib (AMG 510)",
        covalent_anchor=12,
        active_site=[10, 11, 12, 13, 14, 15, 16, 17, 18, 29, 30, 31, 32, 33, 34, 35,
                     59, 60, 116, 117, 118, 119],
        pocket_full={
            4.0: [9, 10, 12, 16, 34, 59, 60, 61, 63, 68, 72, 96, 99, 103],
            4.5: [9, 10, 11, 12, 13, 16, 34, 58, 59, 60, 61, 62, 63, 68, 69, 72, 95,
                  96, 99, 100, 103],
            8.0: [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 32, 33, 34, 35, 36, 37, 56,
                  57, 58, 59, 60, 61, 62, 63, 64, 65, 68, 69, 72, 73, 78, 79, 80, 88,
                  91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104],
        },
        pocket_distal={
            4.0: [61, 63, 68, 72, 96, 99, 103],
            4.5: [58, 61, 62, 63, 68, 69, 72, 95, 96, 99, 100, 103],
            8.0: [56, 57, 58, 61, 62, 63, 64, 65, 68, 69, 72, 73, 78, 79, 80, 88, 91,
                  92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104],
        },
        top5_full=[12, 16, 59, 60, 68],
        top5_full_named=["CYS12", "LYS16", "ALA59", "GLY60", "ARG68"],
        top5_distal=[68, 63, 96, 72, 99],
        top5_distal_named=["ARG68", "GLU63", "TYR96", "MET72", "GLN99"],
        verified=True,
        notes="OVERLAP CASE: 12 = covalent anchor AND P-loop; 59-60 are both "
              "GTP-binding and Switch-II. Use pocket_full for compliance, "
              "pocket_distal for distal discovery."),

    "BCR_ABL1": dict(
        apo="1OPL", holo="5MO4", chain="A",
        disease="Oncology", target_class="Tyrosine Kinase", site_name="Myristoyl pocket",
        holo_ligand="AY7", holo_ligand_name="Asciminib (ABL001)",
        covalent_anchor=None,
        active_site=[248, 249, 250, 251, 252, 253, 254, 255, 256, 271, 316, 317, 318,
                     319, 320, 321, 322, 363],
        pocket_full={
            4.0: [356, 359, 360, 363, 448, 451, 452, 453, 481, 484, 487, 512, 521, 525],
            4.5: [351, 356, 359, 360, 363, 448, 451, 452, 453, 454, 456, 481, 482, 483,
                  484, 487, 512, 521, 525, 529],
            8.0: [346, 351, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 444,
                  445, 447, 448, 449, 450, 451, 452, 453, 454, 455, 456, 479, 480, 481,
                  482, 483, 484, 485, 486, 487, 488, 490, 491, 512, 515, 516, 521, 522,
                  524, 525, 526, 529],
        },
        pocket_distal={
            4.0: [356, 359, 360, 448, 451, 452, 453, 481, 484, 487, 512, 521, 525],
            4.5: [351, 356, 359, 360, 448, 451, 452, 453, 454, 456, 481, 482, 483, 484,
                  487, 512, 521, 525, 529],
            8.0: [346, 351, 354, 355, 356, 357, 358, 359, 360, 361, 362, 364, 444, 445,
                  447, 448, 449, 450, 451, 452, 453, 454, 455, 456, 479, 480, 481, 482,
                  483, 484, 485, 486, 487, 488, 490, 491, 512, 515, 516, 521, 522, 524,
                  525, 526, 529],
        },
        top5_full=[359, 360, 448, 453, 481],
        top5_full_named=["LEU359", "LEU360", "LEU448", "THR453", "GLU481"],
        top5_distal=[359, 360, 448, 453, 481],
        top5_distal_named=["LEU359", "LEU360", "LEU448", "THR453", "GLU481"],
        verified=True,
        notes="Myristoyl pocket (~351-529) far from ATP/catalytic site -> CLEAN distal "
              "case. active_site is UniProt isoform-1a numbering; align to 5MO4 before "
              "use. Ignore NIL (Nilotinib) at ATP site."),

    "CARDIAC_MYOSIN": dict(
        apo="5TBY", holo="6C1H", chain="B",
        holo_validation="8QYR", holo_validation_chain="B",
        disease="Cardiology", target_class="Motor Protein", site_name="Mavacamten site",
        holo_ligand="XB2", holo_ligand_name="Mavacamten",
        covalent_anchor=None,
        active_site=[179, 180, 181, 182, 183, 184, 185, 186, 233, 234, 235, 236, 237,
                     238, 239, 240],
        pocket_full={
            4.0: [164, 167, 168, 666, 711, 712, 721, 774],
            4.5: [120, 163, 164, 167, 168, 170, 666, 710, 711, 712, 713, 721, 722, 770, 774],
            5.0: "REGEN",
            6.0: "REGEN",
            8.0: [120, 146, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 172,
                  492, 497, 500, 666, 667, 668, 709, 710, 711, 712, 713, 714, 717, 718,
                  720, 721, 722, 762, 763, 764, 765, 770, 771, 774, 777],
        },
        pocket_distal={
            4.0: [164, 167, 168, 666, 711, 712, 721, 774],
            4.5: [120, 163, 164, 167, 168, 170, 666, 710, 711, 712, 713, 721, 722, 770, 774],
            8.0: [120, 146, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 172,
                  492, 497, 500, 666, 667, 668, 709, 710, 711, 712, 713, 714, 717, 718,
                  720, 721, 722, 762, 763, 764, 765, 770, 771, 774, 777],
        },
        top5_full=[168, 666, 711, 712, 774],
        top5_full_named=["ASP168", "HIS666", "ASN711", "ARG712", "GLU774"],
        top5_distal=[168, 666, 711, 712, 774],
        top5_distal_named=["ASP168", "HIS666", "ASN711", "ARG712", "GLU774"],
        verified=True,
        notes="CHALLENGE TABLE 1 lists holo=6C1H -> kept as challenge holo for "
              "compliance. Verified: 6C1H is Unconventional MYOSIN-Ib (rat), actin-bound "
              "cryo-EM, ADP+MG only -> NO mavacamten, so it cannot define the pocket. "
              "holo_validation=8QYR = real Beta-cardiac myosin (Bos taurus MYH7) X-ray "
              "1.80A WITH Mavacamten (XB2). Score the pocket against 8QYR; report 6C1H "
              "as the challenge-listed (but unusable) holo. APO 5TBY is a homology model "
              "-> sequence-align. Pocket lists are in mavacamten-pocket numbering."),

    "MYC_MAX": dict(
        apo="1NKP", holo=None, chain="A",
        disease="Oncology", target_class="Transcription Factor (IDP)", site_name=None,
        holo_ligand=None, holo_ligand_name=None, covalent_anchor=None,
        active_site=[913, 914, 917],
        pocket_full=None, pocket_distal=None,
        top5_full=None, top5_full_named=None, top5_distal=None, top5_distal_named=None,
        verified=False,
        notes="No holo / no validated pocket. 1NKP: cMyc=A,D | Max=B,E | DNA=F,G,H,J. "
              "Use chain='A,D'. Score by consensus/docking only."),

    "PTP1B": dict(
        apo="1SUG", holo="1T49", chain="A",
        disease="Metabolic/Diabetes", target_class="Phosphatase",
        site_name="Allosteric BB site (a7)",
        holo_ligand="892", holo_ligand_name="BB allosteric inhibitor (cmpd 892)",
        covalent_anchor=None,
        active_site=[181, 215, 216, 217, 218, 219, 220, 221, 262],
        pocket_full={
            4.0: [189, 193, 196, 197, 200, 276, 280, 282],
            4.5: [187, 188, 189, 192, 193, 196, 197, 200, 276, 277, 279, 280, 281, 282],
            8.0: [153, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199,
                  200, 232, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282],
        },
        pocket_distal={
            4.0: [189, 193, 196, 197, 200, 276, 280, 282],
            4.5: [187, 188, 189, 192, 193, 196, 197, 200, 276, 277, 279, 280, 281, 282],
            8.0: [153, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199,
                  200, 232, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282],
        },
        top5_full=[193, 200, 276, 280, 282],
        top5_full_named=["ASN193", "GLU200", "GLU276", "PHE280", "MET282"],
        top5_distal=[193, 200, 276, 280, 282],
        top5_distal_named=["ASN193", "GLU200", "GLU276", "PHE280", "MET282"],
        verified=True,
        notes="BB allosteric site ~20 A from catalytic Cys215 -> CLEAN distal case."),

    # TASK-0219: apo (1V4S) and holo (3H1V) disagree on which letter maps to
    # the same biological chain -- verified directly (chain_summary: 1V4S
    # has only chain A, 3H1V has only chain X). `chain="X"` below is
    # holo-correct; `apo_chain` overrides it for the apo role only, mirroring
    # __WORK_IN_PROGRESS__/config/targets.yaml's `apo_chains`/`holo_chains`
    # pattern (TASK-0127, same underlying fact, other tree).
    "GLUCOKINASE": dict(
        apo="1V4S", holo="3H1V", chain="X", apo_chain="A",
        disease="Metabolic/Diabetes", target_class="Kinase",
        site_name="GKA allosteric site",
        holo_ligand="TK1", holo_ligand_name="Glucokinase activator (GKA)",
        covalent_anchor=None,
        active_site=[78, 79, 80, 81, 82, 83, 151, 152, 168, 169, 204, 205, 228, 231,
                     256, 290, 295, 296, 332, 333, 334, 335, 336, 411, 412, 413, 414, 415],
        pocket_full={
            4.0: [61, 63, 98, 210, 214, 215, 452],
            4.5: [61, 62, 63, 64, 65, 96, 97, 98, 159, 210, 211, 214, 215, 218, 220,
                  221, 235, 451, 452, 455, 456],
            8.0: "REGEN",
        },
        pocket_distal={
            4.0: [61, 63, 98, 210, 214, 215, 452],
            4.5: [61, 62, 63, 64, 65, 96, 97, 98, 159, 210, 211, 214, 215, 218, 220,
                  221, 235, 451, 452, 455, 456],
            8.0: "REGEN",
        },
        top5_full=[61, 63, 98, 214, 215],
        top5_full_named=["TYR61", "ARG63", "GLN98", "TYR214", "TYR215"],
        top5_distal=[61, 63, 98, 214, 215],
        top5_distal_named=["TYR61", "ARG63", "GLN98", "TYR214", "TYR215"],
        verified=True,
        notes="GKA site distinct from glucose/ATP catalytic residues -> CLEAN distal "
              "case. Ignore GLC (glucose) at active site. Chain 'X'. 8.0A needs regen."),
}


def _flatten_pocket(pdict, scoring_cutoff):
    """Residue list for the chosen scoring_cutoff -> ONE clean pocket definition.
    Falls back to the nearest available numeric-cutoff list at-or-below the request,
    else the smallest available; [] if nothing usable."""
    if not isinstance(pdict, dict):
        return []
    v = pdict.get(scoring_cutoff)
    if isinstance(v, list):
        return sorted(int(r) for r in v)
    usable = {c: l for c, l in pdict.items()
              if isinstance(c, (int, float)) and isinstance(l, list)}
    if not usable:
        return []
    at_or_below = [c for c in usable if c <= scoring_cutoff]
    pick = max(at_or_below) if at_or_below else min(usable)
    return sorted(int(r) for r in usable[pick])


def resolve_systems(pocket_mode="full", scoring_cutoff=8.0):
    """Derive the legacy keys the pipeline consumes from the new schema.
    Mirrors the notebook's compat adapter. Returns a fresh dict (non-mutating)."""
    out = {}
    for name, cfg in SYSTEMS.items():
        c = dict(cfg)
        pocket = c.get("pocket_distal") if pocket_mode == "distal" else c.get("pocket_full")
        top5 = c.get("top5_distal") if pocket_mode == "distal" else c.get("top5_full")
        c.setdefault("cutoff", scoring_cutoff)
        c["holo_challenge"] = c.get("holo")
        # TASK-0219: per-role chain resolution -- `apo_chain`/`holo_chain`
        # override the shared `chain` field when a target sets them (e.g.
        # GLUCOKINASE), else both fall back to `chain` unchanged (every
        # target that only sets `chain` resolves identically to before).
        c["apo_chain"] = c.get("apo_chain", c.get("chain"))
        c["holo_chain"] = c.get("holo_chain", c.get("chain"))
        if c.get("holo_validation"):
            c["holo"] = c["holo_validation"]
            if c.get("holo_validation_chain"):
                c["holo_chain"] = c["holo_validation_chain"]
                c["chain"] = c["holo_validation_chain"]
        c["catalytic"] = list(c.get("active_site", []))
        anchor = c.get("covalent_anchor")
        c["original_src"] = ([anchor] if anchor is not None
                             else list(c.get("active_site", []))[:3])
        c["lit_pocket"] = _flatten_pocket(pocket, scoring_cutoff)
        c["pockets"] = pocket if pocket else None
        c["top5_holo"] = list(top5) if top5 else None
        c["top5_holo_named"] = (c.get("top5_distal_named") if pocket_mode == "distal"
                                else c.get("top5_full_named"))
        out[name] = c
    return out
