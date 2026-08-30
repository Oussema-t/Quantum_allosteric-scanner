"""Step 1 of conservation arms: for each apo structure used by the frozen-20,
pull per-chain (auth_asym_id) canonical entity sequence, the auth-residue-number
ordering, and the UniProt accession, straight from the RCSB data API.

No repo dependency: apo PDB ids and chain selections come from expA_fpocket.json,
which is the same selection the cached fpocket runs used.
"""
import json
import time
import urllib.request
from pathlib import Path

UP = Path("/mnt/user-data/uploads")
OUT = Path("/home/claude/struct_map.json")
API = "https://data.rcsb.org/rest/v1/core"


def get(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=45) as r:
                return json.loads(r.read())
        except Exception as ex:  # noqa: BLE001
            if i == tries - 1:
                raise
            time.sleep(1.5 * (i + 1))
            last = ex  # noqa: F841
    return None


def main():
    expA = json.loads((UP / "expA_fpocket.json").read_text())
    # distinct (pdb, frozenset(chains)) -> targets using it
    structs = {}
    for t, v in expA.items():
        structs.setdefault(v["apo_pdb"].upper(), set()).update(v["chains"])

    out = {}
    for pdb, chains in sorted(structs.items()):
        ent = get(f"{API}/entry/{pdb}")
        eids = ent["rcsb_entry_container_identifiers"]["polymer_entity_ids"]
        rec = {"chains": {}}
        for eid in eids:
            pe = get(f"{API}/polymer_entity/{pdb}/{eid}")
            ci = pe["rcsb_polymer_entity_container_identifiers"]
            seq = pe["entity_poly"]["pdbx_seq_one_letter_code_can"].replace("\n", "")
            unis = [r["database_accession"]
                    for r in ci.get("reference_sequence_identifiers", []) or []
                    if r.get("database_name") == "UniProt"]
            asyms = ci.get("asym_ids", [])
            auths = ci.get("auth_asym_ids", [])
            etype = pe["entity_poly"].get("rcsb_entity_polymer_type")
            for asym, auth in zip(asyms, auths):
                if auth not in chains or etype != "Protein":
                    continue
                inst = get(f"{API}/polymer_entity_instance/{pdb}/{asym}")
                ii = inst["rcsb_polymer_entity_instance_container_identifiers"]
                a2e = ii.get("auth_to_entity_poly_seq_mapping")
                rec["chains"][auth] = {
                    "entity_id": eid, "seq": seq, "uniprot": unis,
                    "auth_to_entity_poly_seq_mapping": a2e,
                    "name": (pe.get("rcsb_polymer_entity", {}) or {}).get(
                        "pdbx_description"),
                }
        missing = sorted(chains - set(rec["chains"]))
        rec["missing_chains"] = missing
        out[pdb] = rec
        print(f"{pdb}: chains={sorted(rec['chains'])} missing={missing}")
        for c, d in sorted(rec["chains"].items()):
            print(f"   {c} ent{d['entity_id']} len={len(d['seq'])} "
                  f"uni={d['uniprot']} {str(d['name'])[:44]}")
    OUT.write_text(json.dumps(out, indent=1))
    print("\nwrote", OUT)


if __name__ == "__main__":
    main()
