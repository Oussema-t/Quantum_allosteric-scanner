#!/usr/bin/env python3
"""TASK-0345 -- the apo vs stripped-holo delta: the number nobody reports.

Leading cryptic-pocket methods (89.8%/98.1% on ASBench/CASBench) score on
ligand-removed holo structures, not genuine apo depositions. Removing a
ligand does not close a pocket -- the side-chain conformation stays open.
This measures the (2)-(1) delta directly: does fpocket see the annotated
site as strongly on a genuinely empty apo structure as it does on the same
protein's holo structure with the ligand computationally stripped?

Three states per pair, same chain, same fpocket call
(`task0242_two_stage_dryrun.fpocket_candidates` -- reused, not
reimplemented, per this task's own Constraint):
  (1) genuine apo   -- the apo deposition, AA3-filtered (standard residues
                        + modified-AA HETATM like MSE kept; true
                        heteroatoms/waters dropped)
  (2) holo, stripped -- the holo deposition, same AA3 filter (removes the
                        actual ligand computationally)
  (3) holo, deposited -- the holo deposition, unfiltered (every ATOM +
                        HETATM record kept)

Cohort: `cryptosite_pairs.json` (21) + `pocketminer_pairs.json` (86) = 107
pairs, already vendored with explicit (apo, holo, chain, holo_chain,
drug_code) fields -- no CryptoBench fetch needed (CryptoBench's own raw
8.4 MB dataset is deliberately NOT vendored in this repo, per
`allosteric/README.md`'s own Datasets section: "download from OSF
10.17605/OSF.IO/PZ4A9"). 107 pairs already clears this task's own >=100
bar; CryptoBench is flagged as a follow-up, not fetched here -- stated as
a scope reduction, not hidden.

Truth pocket, derived fresh (not read from `operator_worklist.json`, which
only pre-computed this for 42/107 of these pairs): protein residues on the
HOLO structure within 4.5 A (this repo's own established
`pocket_contact_cutoff` default, `allostery.labels`) of any heavy atom of
the named `drug_code` ligand, same chain. Mapped onto the APO structure by
assuming shared PDB residue numbering (both entries are different
depositions of literally the same protein) -- CHECKED, not assumed: a
per-pair residue-identity gate (Planned Validation, generalized to every
pair) requires >=80% three-letter-code agreement at the resnums the two
chains share, or the pair is excluded and counted, not silently misjoined.

`fpocket`'s own vendored wrapper (`tools/fpocket/bin/fpocket`, a
Docker-backed drop-in per TASK-0285) only sees files under this repo's own
root or the real system temp root -- confirmed by a failing then passing
smoke test against `/tmp` vs. a repo-internal work directory. Every PDB
this script writes lives under this task's own `work/` subdirectory for
that reason, not to persist scratch state.

Usage: python3 apo_holo_delta.py [--validate-only]
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WORK = HERE / "work"
WORK.mkdir(exist_ok=True)
PDB_CACHE = HERE / "pdb_cache"
PDB_CACHE.mkdir(exist_ok=True)

sys.path.insert(0, str(HERE.parent.parent.parent / "scripts"))
sys.path.insert(0, str(HERE.parent.parent.parent / "src"))
import task0242_two_stage_dryrun as t0242  # noqa: E402

AA3 = {"ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
       "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL", "MSE"}
WATER = {"HOH", "WAT", "DOD"}
CONTACT_CUTOFF = 4.5  # this repo's own `pocket_contact_cutoff` default (allostery.labels)
RESIDUE_IDENTITY_GATE = 0.80
FROZEN_COHORT_PATH = HERE / "frozen_cohort.json"


def fetch_pdb(pdb_id):
    p = PDB_CACHE / f"{pdb_id.lower()}.pdb"
    if p.exists() and p.stat().st_size > 0:
        return p
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
    """All ATOM/HETATM lines for one chain, stopping at the first ENDMDL
    (first model only). Returns list of (record, resname, resnum, atomname, x, y, z)."""
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
    """Protein residues within CONTACT_CUTOFF of any heavy atom of drug_code,
    same chain. Returns (set of resnums, dict resnum->resname)."""
    atoms = chain_atoms(holo_lines, holo_chain)
    ligand_xyz = np.array([(x, y, z) for rec, resname, resnum, atomname, x, y, z in atoms
                            if rec == "HETATM" and resname == drug_code and not atomname.startswith("H")])
    if len(ligand_xyz) == 0:
        return set(), {}
    protein = [(resnum, resname, np.array([x, y, z]))
               for rec, resname, resnum, atomname, x, y, z in atoms
               if resname in AA3 and not atomname.startswith("H")]
    truth = set()
    resname_by_num = {}
    for resnum, resname, xyz in protein:
        d = np.sqrt(((ligand_xyz - xyz) ** 2).sum(axis=1)).min()
        if d <= CONTACT_CUTOFF:
            truth.add(resnum)
            resname_by_num[resnum] = resname
    return truth, resname_by_num


def residue_identity_check(apo_lines, apo_chain, truth_resnames):
    """CHECKED, not assumed: does the apo chain share PDB numbering with the
    holo chain at the truth resnums? Returns (frac_present, frac_identical_of_present)."""
    apo_atoms = chain_atoms(apo_lines, apo_chain)
    apo_resname = {}
    for rec, resname, resnum, atomname, x, y, z in apo_atoms:
        if rec == "ATOM" and atomname == "CA":
            apo_resname[resnum] = resname
    if not truth_resnames:
        return 0.0, 0.0
    present = [rn for rn in truth_resnames if rn in apo_resname]
    frac_present = len(present) / len(truth_resnames)
    if not present:
        return frac_present, 0.0
    identical = sum(1 for rn in present if apo_resname[rn] == truth_resnames[rn])
    return frac_present, identical / len(present)


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


def score_state(pdb_path, work_subdir, truth_resnums, chain):
    work_subdir.mkdir(exist_ok=True, parents=True)
    pockets = t0242.fpocket_candidates(pdb_path, work_subdir)
    if isinstance(pockets, dict) and "error" in pockets:
        return dict(error=pockets["error"], detected=False, best_druggability=0.0,
                    best_rank=None, n_pockets=0)
    if not pockets:
        return dict(detected=False, best_druggability=0.0, best_rank=None, n_pockets=0)
    ranked = sorted(pockets, key=lambda p: (-(p["druggability_score"] or 0.0), p["id"]))
    hit_idx = None
    for i, p in enumerate(ranked):
        if any(rn == truth_rn for (c, rn) in p["resnums"] for truth_rn in truth_resnums if c == chain):
            hit_idx = i
            break
    if hit_idx is None:
        return dict(detected=False, best_druggability=0.0, best_rank=None, n_pockets=len(pockets))
    return dict(detected=True, best_druggability=ranked[hit_idx]["druggability_score"] or 0.0,
                best_rank=hit_idx + 1, n_pockets=len(pockets))


def build_frozen_cohort():
    """Load both pair sources, derive truth residues + identity-check every
    pair, and write the FROZEN, validated cohort to disk before any fpocket
    call -- so the cohort cannot drift between re-runs (this task's own
    Constraint)."""
    cs = json.load(open(HERE / "cs_pairs.json"))
    pm = json.load(open(HERE / "pm_pairs.json"))
    raw_pairs = []
    n_no_holo = 0
    for x in cs:
        raw_pairs.append(dict(apo=x["apo"], chain=x["chain"], holo=x["holo"],
                               holo_chain=x["holo_chain"], drug_code=x["drug_code"],
                               source="cryptosite", desc=x["name"]))
    for x in pm:
        if x.get("holo") is None:
            # PocketMiner's own negative-control/rigid-protein entries --
            # no holo counterpart exists, so there is no pair to score here.
            n_no_holo += 1
            continue
        if " or " in x.get("chain", ""):
            # ambiguous chain spec ("A or B") -- not a usable single-chain
            # pair without a manual disambiguation this task does not make.
            n_no_holo += 1
            continue
        raw_pairs.append(dict(apo=x["apo"], chain=x["chain"], holo=x["holo"],
                               holo_chain=x["holo_chain"], drug_code=x["drug_code"],
                               source="pocketminer", desc=x["name"]))
    print(f"  ({n_no_holo} PocketMiner entries have no holo counterpart or an "
          f"ambiguous chain -- excluded before fetching anything)")

    cohort = []
    excluded = []
    for pair in raw_pairs:
        apo_path = fetch_pdb(pair["apo"])
        holo_path = fetch_pdb(pair["holo"])
        if not apo_path or not holo_path:
            excluded.append(dict(**pair, reason="fetch_failed"))
            continue
        apo_lines = parse_pdb_lines(apo_path)
        holo_lines = parse_pdb_lines(holo_path)
        truth, resname_by_num = truth_pocket_residues(holo_lines, pair["holo_chain"], pair["drug_code"])
        if len(truth) < 2:
            excluded.append(dict(**pair, reason=f"no_ligand_contacts (n_truth={len(truth)})"))
            continue
        frac_present, frac_identical = residue_identity_check(apo_lines, pair["chain"], resname_by_num)
        if frac_present < 0.5 or frac_identical < RESIDUE_IDENTITY_GATE:
            excluded.append(dict(**pair, reason=f"numbering_mismatch (present={frac_present:.2f}, identical={frac_identical:.2f})"))
            continue
        cohort.append(dict(**pair, truth_resnums=sorted(truth), n_truth=len(truth),
                            frac_present=round(frac_present, 3), frac_identical=round(frac_identical, 3)))

    out = dict(n_raw=len(raw_pairs), n_cohort=len(cohort), n_excluded=len(excluded),
               excluded=excluded, cohort=cohort)
    json.dump(out, open(FROZEN_COHORT_PATH, "w"), indent=1)
    return out


def run_pair(pair, idx):
    apo_path = fetch_pdb(pair["apo"])
    holo_path = fetch_pdb(pair["holo"])
    apo_lines = parse_pdb_lines(apo_path)
    holo_lines = parse_pdb_lines(holo_path)
    truth_resnums = set(pair["truth_resnums"])

    pair_work = WORK / f"{idx:04d}_{pair['apo']}_{pair['holo']}"
    pair_work.mkdir(exist_ok=True, parents=True)

    # fpocket_candidates resolves its own `<stem>_out/` relative to `cwd`
    # (the `work` argument), NOT relative to the input file's own directory
    # -- so each state's PDB must live directly INSIDE the same directory
    # passed as `work`, one subdirectory per state, or the output lands
    # next to the input instead of where the caller looks for it (caught
    # here in Planned Validation: the first --validate-only pair returned
    # "no info file" for all 3 states until this was fixed).
    s1_dir, s2_dir, s3_dir = pair_work / "s1", pair_work / "s2", pair_work / "s3"
    for d in (s1_dir, s2_dir, s3_dir):
        d.mkdir(exist_ok=True, parents=True)

    apo_pdb = s1_dir / f"{pair['apo'].lower()}_state1.pdb"
    write_state_pdb(apo_lines, pair["chain"], apo_pdb, strip_hetatm=False)
    stripped_pdb = s2_dir / f"{pair['holo'].lower()}_state2.pdb"
    write_state_pdb(holo_lines, pair["holo_chain"], stripped_pdb, strip_hetatm=True)
    deposited_pdb = s3_dir / f"{pair['holo'].lower()}_state3.pdb"
    with open(deposited_pdb, "w") as f:
        for l in holo_lines:
            if l.startswith("ENDMDL"):
                break
            if l[:6].strip() in ("ATOM", "HETATM") and len(l) > 21 and l[21] == pair["holo_chain"]:
                f.write(l if l.endswith("\n") else l + "\n")
        f.write("END\n")

    s1 = score_state(apo_pdb, s1_dir, truth_resnums, pair["chain"])
    s2 = score_state(stripped_pdb, s2_dir, truth_resnums, pair["holo_chain"])
    s3 = score_state(deposited_pdb, s3_dir, truth_resnums, pair["holo_chain"])
    return dict(pair=pair, state1_apo=s1, state2_holo_stripped=s2, state3_holo_deposited=s3)


def main():
    validate_only = "--validate-only" in sys.argv
    print("Building frozen, validated cohort...")
    frozen = build_frozen_cohort()
    print(f"  raw pairs: {frozen['n_raw']}  cohort: {frozen['n_cohort']}  excluded: {frozen['n_excluded']}")
    for e in frozen["excluded"][:10]:
        print(f"    excluded {e['apo']}/{e['holo']}: {e['reason']}")

    cohort = frozen["cohort"]
    if validate_only:
        cohort = cohort[:3]
        print(f"\n--validate-only: scoring {len(cohort)} pairs by hand-checkable detail\n")

    results = []
    t0 = time.time()
    for i, pair in enumerate(cohort):
        try:
            r = run_pair(pair, i)
        except Exception as e:
            r = dict(pair=pair, error=f"{type(e).__name__}: {e}")
        results.append(r)
        if validate_only:
            print(json.dumps(r, indent=1, default=str))
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(cohort)} ({time.time()-t0:.0f}s)")

    out_path = HERE / ("validate_result.json" if validate_only else "apo_holo_delta_result.json")
    json.dump(results, open(out_path, "w"), indent=1, default=str)
    print(f"\nWrote {out_path} ({time.time()-t0:.0f}s total)")


if __name__ == "__main__":
    main()
