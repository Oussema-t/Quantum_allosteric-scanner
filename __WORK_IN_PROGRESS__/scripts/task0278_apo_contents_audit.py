#!/usr/bin/env python3
"""TASK-0278 -- live audit of every apo structure's OWN bound contents,
across `config/targets.yaml` and `config/candidate_targets_task0243.yaml`,
classifying each ligand as benchmark-legitimate (cognate substrate /
buffer / cryoprotectant / ion) or benchmark-breaking (a synthetic
drug-like molecule, or a lipid/fatty-acid additive occupying a real
pocket -- BCR_ABL1's own MYR is exactly this second case).

Reuses, does not re-derive: `backend.rcsb.ligands_and_sites` (the live
app's own already-validated HETATM enumeration -- parses the real
structure file directly, not the unreliable `nonpolymer_bound_components`
summary field this register's own TASK-0270 already found silently misses
non-coordinating ligands) and `backend.rcsb.classify_ligand`/
`_is_aliphatic_additive` (the same primitives `classify_ligand` itself
uses internally).

**The exact blind spot this task exists to close, found and partially
worked around once already** ([[TASK-0214]]'s own `_is_buffer_or_water`,
scoped only to that task's own apo-reselection candidate filter, never
applied to re-check the INCUMBENT apo structures already in use):
`classify_ligand("MYR")` returns `("solvent/ion", False)` --
BCR_ABL1's own myristic acid, sitting in the pocket the pipeline is asked
to predict, is bucketed by the register's own top-level classifier as a
harmless additive (`_NON_DRUG`'s own "lipids / fatty acids / alkanes"
bucket, a deliberate choice for OTHER purposes -- most fatty acids bound
at a crystal surface really are inert). This script applies the SAME
correction TASK-0214 already built (`_is_aliphatic_additive` checked
directly, overriding `classify_ligand`'s own top-level bucket for this
one purpose), generalised into a reusable `apo_ligand_verdict` function
rather than staying a private helper in one candidate-filtering script.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import yaml

_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _ROOT.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _REPO_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from backend.data_layer import fetch  # noqa: E402
from backend.rcsb import _is_aliphatic_additive, chem_comp_name, classify_ligand, ligands_and_sites  # noqa: E402

OUT = _ROOT / "results/tasks/0278_apo_contents_audit"

# Manual, documented exceptions -- biochemistry `classify_ligand` cannot
# know from a single ligand code alone (a COMBINATION of ordinarily-fine
# cofactors that together mimic a transition state is not a per-ligand
# property). Each entry: code -> (verdict, reason). Checked live before
# writing, not assumed from the task filing alone -- see Done.
MANUAL_OVERRIDES = {
    "VO4": ("suspect_transition_state_mimic",
            "Vanadate; ADP+vanadate together mimic the ATP-hydrolysis "
            "transition state (a chemically trapped state), not a resting "
            "apo, even though ADP alone and vanadate alone would each "
            "individually classify as cofactor/ion. TASK-0278's own filing."),
}


_BOND_MAX = 1.5  # Angstrom -- a real peptide C-N bond is ~1.33 A; any real
# bond is well under 1.5 A, any non-bonded approach is well over it (no
# ambiguous middle ground at this cutoff).


def _covalent_chain_hetero_keys(pdb_id: str) -> set:
    """(chain_id, resnum) for every HETATM residue that is PEPTIDE-BONDED
    to a normal (non-hetero) neighbor immediately before or after it in
    the same chain -- a covalently-modified residue embedded in the
    polymer (e.g. `M3L`/N-trimethyllysine, `ACE`/N-terminal acetyl cap),
    not a free ligand.

    Found necessary directly, not assumed: `Bio.PDB`'s own hetero flag
    (what `ligands_and_sites`' `_iter_hetero` filters on) does NOT
    distinguish "free small molecule" from "covalently in-chain modified
    residue" -- both get recorded as HETATM in the PDB format. Checked
    live for CARDIAC_MYOSIN's own `M3L` (8QYP): its neighbors at resnum-1
    and resnum+1 are ordinary TYR/TRP residues at real peptide-bond
    distance (1.34/1.34 A) -- confirmed covalent, not a bound ligand,
    before writing this filter, not assumed from the code alone.

    A resnum-adjacency check ALONE is not reliable (residue numbering can
    coincidentally place an unrelated free ligand next to a chain
    residue) -- the actual C-N bond DISTANCE is checked, not just
    presence of a neighboring residue at rn+-1.
    """
    from Bio.PDB import PDBParser
    fp = fetch(pdb_id)
    if fp is None:
        return set()
    s = PDBParser(QUIET=True).get_structure(pdb_id, fp)
    model = s[0]
    covalent = set()
    for chain in model:
        by_rn: dict = {}
        for res in chain:
            by_rn.setdefault(res.id[1], []).append(res)
        for rn, residues in by_rn.items():
            het = [r for r in residues if r.id[0] != " "]
            if not het:
                continue
            target = het[0]
            prev = next((r for r in by_rn.get(rn - 1, []) if r.id[0] == " "), None)
            nxt = next((r for r in by_rn.get(rn + 1, []) if r.id[0] == " "), None)

            def _bonded(a, b):
                try:
                    return float(np.linalg.norm(a["C"].get_coord() - b["N"].get_coord())) < _BOND_MAX
                except KeyError:
                    return False

            if (prev is not None and _bonded(prev, target)) or (nxt is not None and _bonded(target, nxt)):
                covalent.add((chain.id, rn))
    return covalent


def apo_ligand_verdict(lig: dict) -> dict:
    """One ligand dict (from `ligands_and_sites`) -> a benchmark verdict.

    fine_cognate_or_buffer: cofactor, or solvent/ion that is NOT a
      lipid/fatty-acid/detergent additive (true buffers, cryoprotectants,
      ions, water-class molecules).
    broken_synthetic: `classify_ligand` itself already calls it a drug or
      an uncategorised organic ligand.
    broken_lipid_pocket_occupant: `classify_ligand` calls it solvent/ion,
      but `_is_aliphatic_additive` (the SAME function `classify_ligand`
      itself uses to make that call) says it is a long aliphatic chain --
      MYR's own exact case. Flagged separately from `broken_synthetic`
      since the mechanism is different (an additive that happens to fill
      a real pocket, not a designed inhibitor).
    manual_override: a documented, code-specific exception (see
      `MANUAL_OVERRIDES`).
    """
    code = lig["code"]
    if code in MANUAL_OVERRIDES:
        verdict, reason = MANUAL_OVERRIDES[code]
        return {"verdict": verdict, "reason": reason}
    category = lig["category"]
    if category == "cofactor":
        return {"verdict": "fine_cognate_or_buffer", "reason": "biological cofactor"}
    if category == "solvent/ion":
        from backend.rcsb import _chem_comp_record
        rec = _chem_comp_record(code)
        elems = rec["elements"] if rec else {}
        if elems and _is_aliphatic_additive(elems):
            return {"verdict": "broken_lipid_pocket_occupant",
                     "reason": "lipid/fatty-acid additive -- classify_ligand's own "
                               "top-level bucket says solvent/ion, but this is the "
                               "exact blind spot TASK-0214 already found for MYR"}
        return {"verdict": "fine_cognate_or_buffer", "reason": "buffer/cryoprotectant/ion"}
    if category in ("drug", "ligand"):
        return {"verdict": "broken_synthetic",
                 "reason": f"classify_ligand category={category}"}
    return {"verdict": "unknown", "reason": f"unrecognised category={category!r}"}


def audit_one(apo_pdb: str) -> dict:
    ligs = ligands_and_sites(apo_pdb)
    covalent_keys = _covalent_chain_hetero_keys(apo_pdb)
    out = []
    covalent = []
    for lig in ligs:
        key = (lig["chain"], lig["resnum"])
        if key in covalent_keys:
            covalent.append({"code": lig["code"], "name": lig["name"],
                              "chain": lig["chain"], "resnum": lig["resnum"]})
            continue
        v = apo_ligand_verdict(lig)
        out.append({
            "code": lig["code"], "name": lig["name"], "n_atoms": lig["n_atoms"],
            "n_binding_site_residues": len(lig["binding_site"]),
            "classify_ligand_category": lig["category"], **v,
        })
    broken = [l for l in out if l["verdict"] not in ("fine_cognate_or_buffer",)]
    return {"apo_pdb": apo_pdb, "ligands": out, "n_ligands": len(out),
             "n_broken": len(broken), "broken_codes": [l["code"] for l in broken],
             "covalent_modified_residues_excluded": covalent}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    targets_yaml = yaml.safe_load((_ROOT / "config/targets.yaml").read_text())["targets"]
    cand_yaml = yaml.safe_load((_ROOT / "config/candidate_targets_task0243.yaml").read_text())["targets"]

    # target name -> apo pdb, both configs, so the report can show which
    # target(s) each apo structure backs (several are shared across ligand
    # pairs, e.g. 2PBK backs both KSHV_PROTEASE_24Q and _25G).
    apo_to_targets: dict = {}
    for cfg_name, cfg in (("targets.yaml", targets_yaml), ("candidate_targets_task0243.yaml", cand_yaml)):
        for target_name, entry in cfg.items():
            apo = entry.get("apo_pdb")
            if not apo:
                continue
            apo_to_targets.setdefault(apo, []).append((cfg_name, target_name))

    print(f"{len(apo_to_targets)} distinct apo PDB structures across both configs\n")

    results = {}
    for apo_pdb, targets in sorted(apo_to_targets.items()):
        try:
            r = audit_one(apo_pdb)
        except Exception as exc:  # noqa: BLE001
            print(f"{apo_pdb}: FAILED {type(exc).__name__}: {exc}")
            results[apo_pdb] = {"apo_pdb": apo_pdb, "error": f"{type(exc).__name__}: {exc}", "targets": targets}
            continue
        r["targets"] = targets
        results[apo_pdb] = r
        flag = "*** BROKEN ***" if r["n_broken"] else "clean"
        n_cov = len(r["covalent_modified_residues_excluded"])
        print(f"{apo_pdb:6s} ({', '.join(f'{c}:{t}' for c, t in targets):50s}) "
              f"{r['n_ligands']} ligand instance(s), {r['n_broken']} broken"
              f"{f', {n_cov} covalent-residue instance(s) excluded' if n_cov else ''}  [{flag}]")
        # de-duplicate by code for the console listing (many entries are the
        # same ligand repeated once per chain/copy) -- the full per-instance
        # detail (including chain/resnum) is still in the written JSON.
        seen_codes: dict = {}
        for lig in r["ligands"]:
            seen_codes.setdefault(lig["code"], []).append(lig)
        for code, insts in seen_codes.items():
            lig = insts[0]
            marker = "  -> " if lig["verdict"] != "fine_cognate_or_buffer" else "     "
            print(f"{marker}{code:5s} x{len(insts):<3d} {lig['name']!s:40.40s} "
                  f"cat={lig['classify_ligand_category']:10s} verdict={lig['verdict']}")
        time.sleep(0.2)  # be polite to the RCSB Data API across ~27 sequential entries

    (OUT / "apo_contents_audit.json").write_text(json.dumps(results, indent=1))

    n_broken_apos = sum(1 for r in results.values() if r.get("n_broken", 0) > 0)
    print(f"\n{n_broken_apos}/{len(results)} apo structures have at least one broken/suspect ligand")
    print(f"Wrote {OUT / 'apo_contents_audit.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
