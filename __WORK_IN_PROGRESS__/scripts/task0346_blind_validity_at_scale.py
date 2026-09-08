#!/usr/bin/env python3
"""TASK-0346 -- run the pre-registered blind validity rule at scale.

The rule ([[TASK-0209]], pre-registered before scoring): a target's apo/holo
pair is VALID iff `NOT apo_native_hit AND holo_native_hit`, where `hit` is
[[TASK-0204]]'s own `_is_hit` criterion (`overlap_frac >= 0.5 AND
druggability_score >= 0.5`), `overlap_frac` the best-overlap pocket's
fraction of truth residues covered (`_best_druggability_at_window`'s own
selection: the pocket with the HIGHEST overlap, not the highest
druggability). Reused verbatim -- not re-derived, not re-tuned, per this
task's own Constraint ("Do not modify the rule to improve the pass rate").

Two things this script does NOT do, disclosed up front rather than
discovered by a reader:
  1. It does not touch the 1042-pair figure the filing cites. That number
     describes the collaborator's own unified benchmark (CryptoBench +
     CryptoSite + PocketMiner), not what is vendored in this repo --
     [[TASK-0345]] already found and disclosed this: only cryptosite (21)
     + pocketminer (86) are vendored, reducing to 63 validated pairs after
     the same identity/contact gates. This task reuses [[TASK-0345]]'s own
     FROZEN cohort (`frozen_cohort.json`) rather than rebuilding it --
     rebuilding would risk a second, silently-different 63.
  2. It does not re-fetch or re-derive truth pockets for the 7 mandated/
     recommended-database targets from scratch either -- those come from
     `config/targets.yaml`'s own apo_pdb/holo_pdb/chains/drug_ligand
     fields, scored by the exact same pipeline as the 63, as the Planned
     Validation this task's own filing requires ("the seven already-
     audited targets must reproduce their existing verdicts exactly").

Truth pocket: protein residues on the HOLO structure within 4.5 A (this
repo's own `pocket_contact_cutoff` default) of any heavy atom of the named
ligand, same chain -- [[TASK-0345]]'s own method, reused verbatim.

Two states scored per pair, BOTH ligand-stripped -- this task's own filing
text, verbatim: "apo closed, holo open, ligand stripped, cavity re-scored".
The strip applies to holo too, not only to a separate middle state: the
point of stripping is to test whether the CONFORMATION alone presents an
open, druggable cavity, not whether the ligand's own atoms are still
sitting in it inflating the score.
  apo  -- the apo deposition, AA3-filtered (modified-AA HETATM kept,
           true heteroatoms/waters dropped) -- same as [[TASK-0345]] state1.
  holo -- the holo deposition, SAME AA3 filter (ligand computationally
           removed) -- same as [[TASK-0345]] state2, and same as
           [[TASK-0209]]'s own pipeline ("ligand stripped" applied to
           both sides, that task's own Done section, its per-target
           table). A first draft of this script scored holo AS DEPOSITED
           (ligand present, [[TASK-0345]] state3) instead -- caught by
           the Planned Validation reproduction check below (CARDIAC_MYOSIN
           flipped INVALID->VALID purely from the ligand's own atoms
           being present in the score), fixed before the full run.

Second output, same pass: endogenous-ligand occupancy in the apo file
itself (any non-water, non-AA3 HETATM within 4.5 A of a truth residue's
apo-file coordinates), correlated against the apo_native_hit call --
this is what turns [[TASK-0329]]'s "40/40 ASBench structures carry a
ligand" finding from an ASBench-specific observation into a general one,
and tests whether occupancy actually PREDICTS the apo-side failure mode
(bias) or is just incidental (noise).

Usage: python3 task0346_blind_validity_at_scale.py [--validate-only]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent / "results" / "tasks" / "0346_blind_validity_at_scale"
RESULTS.mkdir(parents=True, exist_ok=True)
WORK = RESULTS / "work"
WORK.mkdir(exist_ok=True)
PDB_CACHE = RESULTS / "pdb_cache"
PDB_CACHE.mkdir(exist_ok=True)

TASK0345_DIR = HERE.parent / "results" / "tasks" / "0345_apo_vs_stripped_holo_delta"

sys.path.insert(0, str(HERE.parent.parent / "scripts"))
sys.path.insert(0, str(HERE.parent.parent / "src"))
import task0242_two_stage_dryrun as t0242  # noqa: E402

# [[TASK-0209]]'s own pre-registered rule constants, [[TASK-0204]]'s own
# `_is_hit` bar (task0204_rotamer_repack_baseline.py:52-53) -- reused
# verbatim, not re-picked here.
POCKET_HIT_OVERLAP = 0.5
DRUGGABILITY_BAR = 0.5

AA3 = {"ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
       "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL", "MSE"}
WATER = {"HOH", "WAT", "DOD"}
CONTACT_CUTOFF = 4.5

# The 7 register-mandated / recommended-database targets [[TASK-0209]]
# already scored by hand, from config/targets.yaml's own fields -- not
# hand-typed pocket residues, per that file's own HARD RULE.
REGISTER_TARGETS = {
    "KRAS_G12C":       dict(apo="4LDJ", chain="A", holo="6OIM", holo_chain="A", drug_code="MOV"),
    "BCR_ABL1":        dict(apo="1OPL", chain="A", holo="5MO4", holo_chain="A", drug_code="AY7"),
    "CARDIAC_MYOSIN":  dict(apo="8QYP", chain="A", holo="8QYR", holo_chain="B", drug_code="XB2"),
    "PTP1B":           dict(apo="1SUG", chain="A", holo="1T49", holo_chain="A", drug_code="892"),
    "GLUCOKINASE":     dict(apo="1V4S", chain="A", holo="3H1V", holo_chain="X", drug_code="TK1"),
    "CASPASE1":        dict(apo="1ICE", chain="A", holo="2FQQ", holo_chain="B", drug_code="F1G"),  # F1G sits on chain B in 2FQQ, RCSB-verified live -- not "A"
    "CASPASE7":        dict(apo="1F1J", chain="A", holo="1SHL", holo_chain="A", drug_code="FXN"),
}
# TASK-0209's own recorded verdicts (2/7 VALID: KRAS_G12C, PTP1B), for the
# Planned Validation check -- reproduced here as text, not re-derived from
# a task file at run time, so a change to that file can't silently move
# this script's own pass bar.
TASK0209_VERDICTS = {
    "KRAS_G12C": "VALID", "BCR_ABL1": "INVALID", "CARDIAC_MYOSIN": "INVALID",
    "PTP1B": "VALID", "GLUCOKINASE": "INVALID", "CASPASE1": "INVALID", "CASPASE7": "INVALID",
}


def fetch_pdb(pdb_id):
    # Reuse [[TASK-0345]]'s own cache first -- these are already on disk,
    # no network round-trip needed for the 63-pair cohort.
    shared = TASK0345_DIR / "pdb_cache" / f"{pdb_id.lower()}.pdb"
    if shared.exists() and shared.stat().st_size > 0:
        return shared
    p = PDB_CACHE / f"{pdb_id.lower()}.pdb"
    if p.exists() and p.stat().st_size > 0:
        return p
    import urllib.request
    for attempt in range(4):
        try:
            with urllib.request.urlopen(f"https://files.rcsb.org/download/{pdb_id.upper()}.pdb", timeout=30) as r:
                data = r.read()
            p.write_bytes(data)
            return p
        except Exception:
            time.sleep(1.5 ** attempt)
    return None


def parse_pdb_lines(path):
    return path.read_text(errors="replace").splitlines()


def chain_atoms(lines, chain):
    out = []
    for l in lines:
        if l.startswith("ENDMDL"):
            break
        rec = l[:6].strip()
        if rec not in ("ATOM", "HETATM"):
            continue
        if len(l) < 54 or l[21] != chain:
            continue
        resname = l[17:20].strip()
        try:
            resnum = int(l[22:26])
            x, y, z = float(l[30:38]), float(l[38:46]), float(l[46:54])
        except ValueError:
            continue
        atomname = l[12:16].strip()
        out.append((rec, resname, resnum, atomname, x, y, z))
    return out


def truth_pocket_residues(holo_lines, holo_chain, drug_code):
    atoms = chain_atoms(holo_lines, holo_chain)
    ligand_xyz = np.array([(x, y, z) for rec, resname, resnum, atomname, x, y, z in atoms
                            if rec == "HETATM" and resname == drug_code and not atomname.startswith("H")])
    if len(ligand_xyz) == 0:
        return set(), {}
    protein = [(resnum, resname, np.array([x, y, z]))
               for rec, resname, resnum, atomname, x, y, z in atoms
               if resname in AA3 and not atomname.startswith("H")]
    truth, resname_by_num = set(), {}
    for resnum, resname, xyz in protein:
        d = np.sqrt(((ligand_xyz - xyz) ** 2).sum(axis=1)).min()
        if d <= CONTACT_CUTOFF:
            truth.add(resnum)
            resname_by_num[resnum] = resname
    return truth, resname_by_num


def endogenous_occupancy(apo_lines, apo_chain, truth_resnums):
    """Does the APO file itself carry a non-water, non-AA3 HETATM within
    CONTACT_CUTOFF of any truth residue's OWN apo-file coordinates?
    [[TASK-0329]]'s audit, generalized to this cohort."""
    atoms = chain_atoms(apo_lines, apo_chain)
    truth_xyz = np.array([(x, y, z) for rec, resname, resnum, atomname, x, y, z in atoms
                           if resnum in truth_resnums and resname in AA3 and not atomname.startswith("H")])
    if len(truth_xyz) == 0:
        return None  # truth residues absent from apo chain -- can't judge
    hets = [(resname, np.array([x, y, z])) for rec, resname, resnum, atomname, x, y, z in atoms
            if rec == "HETATM" and resname not in AA3 and resname not in WATER and not atomname.startswith("H")]
    ligands_in_contact = set()
    for resname, xyz in hets:
        d = np.sqrt(((truth_xyz - xyz) ** 2).sum(axis=1)).min()
        if d <= CONTACT_CUTOFF:
            ligands_in_contact.add(resname)
    return sorted(ligands_in_contact)


def write_state_pdb(lines, chain, out_path, strip_hetatm):
    with open(out_path, "w") as f:
        for l in lines:
            if l.startswith("ENDMDL"):
                break
            rec = l[:6].strip()
            if rec not in ("ATOM", "HETATM"):
                continue
            if len(l) < 22 or l[21] != chain:
                continue
            resname = l[17:20].strip()
            if resname in WATER:
                continue
            if rec == "HETATM" and (strip_hetatm or resname not in AA3):
                continue
            f.write(l if l.endswith("\n") else l + "\n")
        f.write("END\n")


def _overlap_frac(pocket_resnums_for_chain, truth_resnums):
    if not truth_resnums:
        return 0.0
    return len(pocket_resnums_for_chain & truth_resnums) / len(truth_resnums)


def score_state(pdb_path, work_subdir, truth_resnums, chain):
    """[[TASK-0204]]'s own `_best_druggability_at_window`/`_is_hit`
    criterion, computed against `task0242.fpocket_candidates` output
    (this repo's Docker-vendored fpocket, [[TASK-0345]]'s own pipeline) --
    NOT the any-single-residue-hit shortcut [[TASK-0345]]'s own
    `score_state` used, which is a different (looser) question."""
    work_subdir.mkdir(exist_ok=True, parents=True)
    pockets = t0242.fpocket_candidates(pdb_path, work_subdir)
    if isinstance(pockets, dict) and "error" in pockets:
        return dict(error=pockets["error"], overlap_frac=0.0, druggability_score=None, hit=False, n_pockets=0)
    if not pockets:
        return dict(overlap_frac=0.0, druggability_score=None, hit=False, n_pockets=0)
    best_frac, best_drug = -1.0, None
    for p in pockets:
        resnums_here = {rn for (c, rn) in p["resnums"] if c == chain}
        frac = _overlap_frac(resnums_here, truth_resnums)
        if frac > best_frac:
            best_frac, best_drug = frac, p["druggability_score"]
    hit = bool(best_frac >= POCKET_HIT_OVERLAP and best_drug is not None and best_drug >= DRUGGABILITY_BAR)
    return dict(overlap_frac=round(best_frac, 3), druggability_score=best_drug, hit=hit, n_pockets=len(pockets))


def run_pair(pair, idx, tag):
    apo_path = fetch_pdb(pair["apo"])
    holo_path = fetch_pdb(pair["holo"])
    if not apo_path or not holo_path:
        return dict(pair=pair, error="fetch_failed")
    apo_lines = parse_pdb_lines(apo_path)
    holo_lines = parse_pdb_lines(holo_path)

    truth, resname_by_num = truth_pocket_residues(holo_lines, pair["holo_chain"], pair["drug_code"])
    if "truth_resnums" in pair:
        truth = set(pair["truth_resnums"])  # frozen cohort already validated this
    if len(truth) < 2:
        return dict(pair=pair, error=f"no_ligand_contacts (n_truth={len(truth)})")

    occ = endogenous_occupancy(apo_lines, pair["chain"], truth)

    pair_work = WORK / f"{tag}_{idx:04d}_{pair['apo']}_{pair['holo']}"
    s1_dir, s2_dir = pair_work / "apo", pair_work / "holo"
    s1_dir.mkdir(exist_ok=True, parents=True)
    s2_dir.mkdir(exist_ok=True, parents=True)

    apo_pdb = s1_dir / f"{pair['apo'].lower()}_apo.pdb"
    write_state_pdb(apo_lines, pair["chain"], apo_pdb, strip_hetatm=False)
    holo_pdb = s2_dir / f"{pair['holo'].lower()}_holo.pdb"
    write_state_pdb(holo_lines, pair["holo_chain"], holo_pdb, strip_hetatm=True)

    apo_score = score_state(apo_pdb, s1_dir, truth, pair["chain"])
    holo_score = score_state(holo_pdb, s2_dir, truth, pair["holo_chain"])
    apo_hit, holo_hit = apo_score["hit"], holo_score["hit"]
    verdict = "VALID" if (not apo_hit and holo_hit) else "INVALID"
    return dict(pair=pair, n_truth=len(truth), endogenous_ligands_in_apo=occ,
                apo=apo_score, holo=holo_score, verdict=verdict)


def main():
    validate_only = "--validate-only" in sys.argv

    print("Loading [[TASK-0345]]'s own frozen cohort (not rebuilt)...")
    frozen = json.load(open(TASK0345_DIR / "frozen_cohort.json"))
    cohort = frozen["cohort"]
    print(f"  {len(cohort)} pairs (cryptosite+pocketminer, TASK-0345's own gates)")

    if validate_only:
        cohort = cohort[:3]

    print(f"\nScoring {len(REGISTER_TARGETS)} register-mandated targets (reproduction check)...")
    register_results = {}
    for name, pair in REGISTER_TARGETS.items():
        r = run_pair(pair, 0, f"reg_{name}")
        register_results[name] = r
        got = r.get("verdict", f"ERROR:{r.get('error')}")
        want = TASK0209_VERDICTS[name]
        match = "OK" if got == want else "MISMATCH"
        print(f"  {name}: got={got} want={want} [{match}]")

    print(f"\nScoring {len(cohort)} cryptosite/pocketminer pairs...")
    t0 = time.time()
    results = []
    for i, pair in enumerate(cohort):
        try:
            r = run_pair(pair, i, "cohort")
        except Exception as e:
            r = dict(pair=pair, error=f"{type(e).__name__}: {e}")
        results.append(r)
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(cohort)} ({time.time()-t0:.0f}s)")

    out = dict(register_targets=register_results, cohort=results,
                n_cohort=len(cohort), rule="NOT apo_hit AND holo_hit",
                pocket_hit_overlap=POCKET_HIT_OVERLAP, druggability_bar=DRUGGABILITY_BAR)
    out_path = RESULTS / ("validate_result.json" if validate_only else "blind_validity_result.json")
    json.dump(out, open(out_path, "w"), indent=1, default=str)
    print(f"\nWrote {out_path} ({time.time()-t0:.0f}s total)")


if __name__ == "__main__":
    main()
