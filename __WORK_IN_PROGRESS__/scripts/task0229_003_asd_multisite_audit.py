#!/usr/bin/env python3
"""TASK-0229.003 -- ref [6] (Tsai & Nussinov 2014, effector-specificity):
does the Allosteric Database (ASD) list additional annotated allosteric
sites for our 4 targets beyond the single incumbent site each carries in
`backend/systems.py`/`targets.yaml`?

Real, non-obvious environment finding, documented here rather than
silently worked around and forgotten: ASD's own HTTPS endpoint
(https://mdl.shsmu.edu.cn/ASD) has an EXPIRED TLS CERTIFICATE -- `WebFetch`
fails outright ("certificate has expired"), and there is no HTTP fallback
(WebFetch force-upgrades http:// to https://). `requests`/`urllib` hit the
same wall. Worked around here with `curl -k` (skip cert verification) --
acceptable for reading public scientific data, not for anything credential-
bearing. If this environment's CA bundle or the site's own cert is fixed
later, `verify=True` should work again and this workaround can be dropped.

Second finding: ASD's own AJAX API (an old Ext.js/JBoss app, `ProteinTextSearch`
and `BrowseSite` servlets) requires POST, not GET (a bare GET 500s with a
NullPointerException), and its JSON responses have an unquoted `data:` key
(valid as a JS object literal, not as strict JSON -- `json.loads` needs a
one-line regex fix first, see `_load_asd_json` below). `BrowseSite` ignores
its own `limit`/filter params entirely and always returns the full table
(3102 rows at the time this ran) -- client-side filtering by `target_domain`
prefix (matching the protein's own `db_serial`) is what actually works.

Usage: this script is a *record* of the queries already run (results saved
to `results/tasks/0229.003/asd_lookup_raw.json`) -- re-running network calls
requires `curl` with the same `-k` workaround; not re-implemented as a
Python `requests` call here since `curl -k` was what was actually verified
working, and switching HTTP clients silently is exactly the kind of
unverified substitution this project's own conventions warn against.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ASD_BASE = "https://mdl.shsmu.edu.cn/ASD"

# Full ExtJS extraParams set ProteinTextSearch expects (POST; a GET or a
# partial param set both 500 -- confirmed directly, not assumed).
_PROTEIN_SEARCH_PARAMS = (
    "search_protein_asd_id=&search_protein_name=&search_protein_uniprot_id=&"
    "search_protein_genbank=&search_protein_gene_name={gene}&search_protein_organism=&"
    "search_protein_cell=&search_protein_tissue=&search_protein_structure=&"
    "search_protein_allosteric_mode=&search_protein_allosteric_desr=&search_protein_scop=&"
    "search_protein_cath=&search_protein_ptm=&search_protein_disease=&"
    "search_protein_seq_len_from=&search_protein_seq_len_to=&search_protein_mol_weight_from=&"
    "search_protein_mol_weight_to=&search_protein_mutation_from=&search_protein_mutation_to=&"
    "page=1&start=0&limit=25"
)


def _load_asd_json(text: str) -> dict:
    """Fixes ASD's own unquoted `data:` key (valid JS, invalid strict JSON)."""
    return json.loads(re.sub(r'(?<!")\bdata:', '"data":', text, count=1))


def _curl_post(url: str, data: str) -> dict:
    result = subprocess.run(
        ["curl", "-k", "-s", "-m", "20", "-A", "Mozilla/5.0", "-X", "POST", "--data", data, url],
        capture_output=True, text=True, check=True,
    )
    return _load_asd_json(result.stdout)


def search_protein(gene_name: str) -> dict:
    """Live re-query, matches the queries this task's own Done section
    numbers were captured from (2026-08-22)."""
    return _curl_post(f"{ASD_BASE}/ProteinTextSearch", _PROTEIN_SEARCH_PARAMS.format(gene=gene_name))


def browse_all_sites() -> list:
    """BrowseSite ignores `limit`/filter params -- always returns the
    full table; filter client-side by `target_domain` prefix instead."""
    return _curl_post(f"{ASD_BASE}/BrowseSite", "page=1&start=0&limit=5000")["data"]


TARGETS = {
    "KRAS_G12C": ("KRAS", "ASD06390000"),
    "BCR_ABL1": ("ABL1", "ASD03320000"),
    "CARDIAC_MYOSIN": ("MYH7", "ASD08190000"),
    "PTP1B": ("PTPN1", "ASD02440000"),
}


def sh2_kinase_interface_residues(cutoff: float = 4.5) -> list:
    """BCR_ABL1's real second site (PDB 5DC4, a monobody bound at the
    SH2-kinase interface, ASD domain `_1` alongside the myristoyl-pocket
    entries -- the `_1`/`_2` split in ASD's own data is human-vs-mouse
    ortholog structures, NOT a site-cluster split, confirmed by checking
    every record's own `organism` field, not assumed from the domain
    suffix alone). Computes real heavy-atom contact residues on chain A
    (ABL1's SH2 domain, resolved range 140-239) against chain B (the
    monobody, resolved range 4-95) -- both ranges confirmed directly from
    the fetched structure, not guessed from the paper's own domain
    boundaries."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    import numpy as np
    import Bio.PDB as PDB

    from backend.data_layer import fetch

    fp = fetch("5DC4")
    structure = PDB.PDBParser(QUIET=True).get_structure("5DC4", fp)
    model = structure[0]
    chain_a = [r for r in model["A"] if r.id[0] == " "]
    chain_b = [r for r in model["B"] if r.id[0] == " "]

    def heavy_atoms(res):
        return [a.coord for a in res if a.element != "H"]

    coords_b = np.vstack([heavy_atoms(r) for r in chain_b])
    contacts = []
    for r in chain_a:
        ca = heavy_atoms(r)
        if not ca:
            continue
        ca = np.array(ca)
        d = np.sqrt(((ca[:, None, :] - coords_b[None, :, :]) ** 2).sum(-1))
        if d.min() < cutoff:
            contacts.append(int(r.id[1]))
    return sorted(contacts)


def main() -> int:
    all_sites = browse_all_sites()
    out = {}
    for name, (gene, serial) in TARGETS.items():
        protein = search_protein(gene)
        rec = next(r for r in protein["data"] if r.get("db_serial") == serial)
        matches = [r for r in all_sites if str(r.get("target_domain", "")).startswith(serial)]
        out[name] = {
            "asd_serial": rec["db_serial"], "mol_name": rec["mol_name"], "uniprot": rec["swissprot_id"],
            "reported_site_count": rec.get("allosteric_site_count"),
            "pdb_linked_site_records": matches,
        }
        print(f"{name}: {rec['mol_name']} ({rec['swissprot_id']}) -- "
              f"{len(matches)} PDB-linked site record(s), "
              f"{len(set(r['target_domain'] for r in matches))} distinct ASD domain(s)")

    sh2_residues = sh2_kinase_interface_residues()
    out["BCR_ABL1"]["second_site_sh2_kinase_interface"] = {
        "pdb": "5DC4", "chain": "A", "cutoff_angstrom": 4.5, "residues": sh2_residues,
        "note": "Real, computed heavy-atom contact residues (ABL1 chain A vs. the "
                "monobody, chain B), not the paper's own reported footprint.",
    }
    print(f"BCR_ABL1 second site (SH2-kinase interface, 5DC4): {len(sh2_residues)} contact residues")

    out_path = Path(__file__).resolve().parent.parent / "results/tasks/0229.003/asd_lookup_raw.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
