"""
Holo discovery + apo completion (Increment 3B).

Given an APO (ligand-free) PDB id, this module:

  1. resolves the protein's UniProt accession from the RCSB Data API,
  2. searches RCSB for ALL ligand-bound (holo) structures of the same protein,
     ranking drug-bound ones first,
  3. completes the apo structure by filling its missing (unresolved) residues —
     using the REAL coordinates from a chosen holo where that residue is resolved,
     and linear interpolation between flanking residues otherwise. Every filled
     residue is flagged as "modeled" and reported.

All network calls are best-effort with timeouts; a benchmark fast-path uses the
validated apo<->holo pairs already stored in systems.py.
"""
import json
import urllib.request

import numpy as np

from .data_layer import load_structure
from .geometry import kabsch_fit, kabsch_apply
from .rcsb import parse_missing_residues, _get_json, DATA_API, _NON_DRUG, _COFACTORS, chem_comp_name
from .systems import resolve_systems

SEARCH_API = "https://search.rcsb.org/rcsbsearch/v2/query"


# ── UniProt resolution ──────────────────────────────────────────────────────

def get_uniprot(pdb_id):
    """UniProt accession(s) for an entry's polymer entities (best-effort)."""
    pdb_id = pdb_id.upper()
    entry = _get_json(f"{DATA_API}/entry/{pdb_id}")
    if not entry:
        return []
    ids = (entry.get("rcsb_entry_container_identifiers", {}) or {}).get("polymer_entity_ids", [])
    accs = []
    for eid in ids:
        pe = _get_json(f"{DATA_API}/polymer_entity/{pdb_id}/{eid}")
        if not pe:
            continue
        cont = pe.get("rcsb_polymer_entity_container_identifiers", {}) or {}
        for ref in (cont.get("reference_sequence_identifiers", []) or []):
            if ref.get("database_name") == "UniProt" and ref.get("database_accession"):
                accs.append(ref["database_accession"])
        for u in (cont.get("uniprot_ids", []) or []):
            accs.append(u)
    # de-dup, preserve order
    seen, out = set(), []
    for a in accs:
        if a not in seen:
            seen.add(a); out.append(a)
    return out


# ── holo search ─────────────────────────────────────────────────────────────

def _search_entries_by_uniprot(uniprot, with_ligand=True, rows=50):
    """RCSB Search API: entries mapped to `uniprot` (optionally requiring ligands)."""
    nodes = [
        {"type": "terminal", "service": "text", "parameters": {
            "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
            "operator": "exact_match", "value": uniprot}},
        {"type": "terminal", "service": "text", "parameters": {
            "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_name",
            "operator": "exact_match", "value": "UniProt"}},
    ]
    if with_ligand:
        nodes.append({"type": "terminal", "service": "text", "parameters": {
            "attribute": "rcsb_entry_info.nonpolymer_entity_count",
            "operator": "greater", "value": 0}})
    query = {
        "query": {"type": "group", "logical_operator": "and", "nodes": nodes},
        "return_type": "entry",
        "request_options": {"results_content_type": ["experimental"],
                            "paginate": {"start": 0, "rows": rows}},
    }
    try:
        req = urllib.request.Request(
            SEARCH_API, data=json.dumps(query).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read().decode("utf-8"))
        return [hit["identifier"] for hit in data.get("result_set", [])]
    except Exception:
        return []


def _entry_drug_info(pdb_id):
    """Quick per-entry summary for ranking: bound ligands, resolution, title."""
    data = _get_json(f"{DATA_API}/entry/{pdb_id}")
    if not data:
        return None
    info = data.get("rcsb_entry_info", {}) or {}
    bound = info.get("nonpolymer_bound_components", []) or []
    drugs = [c for c in bound if c not in _NON_DRUG and c not in _COFACTORS]
    res = info.get("resolution_combined")
    return {
        "pdb_id": pdb_id,
        "title": (data.get("struct", {}) or {}).get("title"),
        "resolution": (res[0] if isinstance(res, list) and res else None),
        "ligands": bound,
        "drugs": drugs,
        "has_drug": bool(drugs),
    }


def same_protein_entries(pdb_id, max_n=40, with_ligand=False):
    """All PDB entries of the same protein as `pdb_id` (via UniProt), excluding it.
    `with_ligand=False` includes apo-like conformers too — used to build morph keyframes."""
    unis = get_uniprot(pdb_id)
    if not unis:
        return []
    up = pdb_id.upper()
    seen, out = set(), []
    for i in _search_entries_by_uniprot(unis[0], with_ligand=with_ligand, rows=max_n):
        iu = i.upper()
        if iu != up and iu not in seen:
            seen.add(iu); out.append(iu)
    return out


def find_holo_candidates(apo_pdb, target_name=None, max_detail=12):
    """All ligand-bound structures of the same protein as `apo_pdb`, drug-bound first.

    Returns {uniprot, benchmark_holo, candidates:[...]} where each candidate has
    pdb_id, title, resolution, drugs, has_drug. `target_name` (a benchmark key)
    short-circuits to the validated holo set."""
    apo_pdb = apo_pdb.upper()
    out = {"apo": apo_pdb, "uniprot": None, "benchmark_holo": None, "candidates": []}

    # benchmark fast-path: known validated holo(s)
    if target_name:
        sysmap = resolve_systems()
        cfg = sysmap.get(target_name)
        if cfg:
            out["benchmark_holo"] = {
                "holo": cfg.get("holo"), "holo_challenge": cfg.get("holo_challenge"),
                "ligand": cfg.get("holo_ligand"), "ligand_name": cfg.get("holo_ligand_name"),
                "chain": cfg.get("chain")}

    unis = get_uniprot(apo_pdb)
    if not unis:
        return out
    out["uniprot"] = unis[0]

    ids = _search_entries_by_uniprot(unis[0], with_ligand=True, rows=50)
    ids = [i for i in ids if i.upper() != apo_pdb][:max_detail]
    cands = []
    for pid in ids:
        info = _entry_drug_info(pid)
        if info:
            # attach human-readable drug names
            info["drug_names"] = {d: chem_comp_name(d) for d in info["drugs"][:5]}
            cands.append(info)
    # drug-bound first, then by best (lowest) resolution
    cands.sort(key=lambda c: (not c["has_drug"], c["resolution"] or 99))
    out["candidates"] = cands
    return out


# ── apo completion ──────────────────────────────────────────────────────────

def complete_apo(apo_pdb, apo_chain, holo_pdb=None, holo_chain=None):
    """Fill the apo structure's missing residues. Returns a completed structure dict
    (coords/resnums/chains/bfac + `modeled` bool array) and a fill report.

    Strategy per missing residue number:
      * if resolved in the holo (same author numbering) -> copy REAL holo Cα coord
      * else -> linear interpolation between the nearest flanking residues that have
        coordinates (resolved or already holo-filled)
    Assumes apo and holo share author residue numbering (true for same-UniProt
    deposits in the benchmark set); flagged in the report if a holo isn't usable.
    """
    apo = load_structure(apo_pdb, apo_chain)
    if apo is None:
        raise ValueError(f"could not load apo {apo_pdb}")

    # resolved residues -> resnum: (coord, bfac)
    resolved = {int(rn): (apo["coords"][i], float(apo["bfac"][i]))
                for i, rn in enumerate(apo["resnums"])}

    missing = [m for m in parse_missing_residues(apo_pdb, apo_chain)]
    missing_nums = sorted(set(int(m["resnum"]) for m in missing))
    resname_of = {int(m["resnum"]): m["resname"] for m in missing}

    # holo coordinates by residue number, SUPERIMPOSED onto the apo frame first
    # (apo and holo are separate crystal structures in different coordinate frames,
    # so we Kabsch-align the holo onto the apo on their shared residues before
    # borrowing any coordinate — otherwise filled atoms land in the wrong place).
    holo_map = {}
    align_rmsd = None
    if holo_pdb:
        holo = load_structure(holo_pdb, holo_chain or apo_chain)
        if holo is not None:
            holo_by_num = {int(rn): holo["coords"][i] for i, rn in enumerate(holo["resnums"])}
            common = sorted(set(resolved) & set(holo_by_num))
            if len(common) >= 3:
                P = np.array([holo_by_num[r] for r in common], float)
                Q = np.array([resolved[r][0] for r in common], float)
                R, Pc, Qc = kabsch_fit(P, Q)
                aligned = kabsch_apply(holo["coords"], R, Pc, Qc)
                holo_map = {int(rn): aligned[i] for i, rn in enumerate(holo["resnums"])}
                ac = kabsch_apply(P, R, Pc, Qc)
                align_rmsd = round(float(np.sqrt(((ac - Q) ** 2).sum(1).mean())), 3)

    filled = {}     # resnum -> (coord, source)
    # pass 1: real coordinates from holo
    for rn in missing_nums:
        if rn in holo_map:
            filled[rn] = (np.asarray(holo_map[rn], float), "holo")

    # combined coordinate map for interpolation lookups
    def coord_at(rn):
        if rn in resolved:
            return resolved[rn][0]
        if rn in filled:
            return filled[rn][0]
        return None

    present_sorted = sorted(set(resolved) | set(filled))

    # pass 2: interpolate the rest between nearest flanking present residues
    for rn in missing_nums:
        if rn in filled:
            continue
        lower = [p for p in present_sorted if p < rn]
        upper = [p for p in present_sorted if p > rn]
        if lower and upper:
            lo, hi = lower[-1], upper[0]
            clo, chi = coord_at(lo), coord_at(hi)
            f = (rn - lo) / (hi - lo)
            filled[rn] = (clo + f * (chi - clo), "interpolated")
        elif lower or upper:
            anchor = (lower[-1] if lower else upper[0])
            filled[rn] = (coord_at(anchor).copy(), "interpolated(terminal)")
        # if neither, residue is unplaceable -> skip (kept in report as 'unplaced')

    # assemble completed structure in residue-number order
    all_nums = sorted(set(resolved) | set(filled))
    coords, resnums, bfac, modeled, chains = [], [], [], [], []
    report = []
    for rn in all_nums:
        if rn in resolved:
            c, b = resolved[rn]
            coords.append(c); bfac.append(b); modeled.append(False)
        else:
            c, src = filled[rn]
            coords.append(c); bfac.append(0.0); modeled.append(True)
            report.append({"resnum": rn, "resname": resname_of.get(rn, "UNK"),
                           "source": src,
                           "coord": [round(float(c[0]), 3), round(float(c[1]), 3),
                                     round(float(c[2]), 3)]})
        resnums.append(rn); chains.append(apo_chain.split(",")[0].strip())

    unplaced = [rn for rn in missing_nums if rn not in filled]
    completed = {
        "coords": np.array(coords, float),
        "resnums": np.array(resnums, int),
        "chains": np.array(chains),
        "bfac": np.array(bfac, float),
        "modeled": np.array(modeled, bool),
        "pdb": apo_pdb,
    }
    summary = {
        "apo": apo_pdb, "holo": holo_pdb,
        "n_missing": len(missing_nums),
        "n_filled_from_holo": sum(1 for r in report if r["source"] == "holo"),
        "n_interpolated": sum(1 for r in report if r["source"].startswith("interpolated")),
        "n_unplaced": len(unplaced),
        "align_rmsd": align_rmsd,
        "filled": report,
        "unplaced": unplaced,
    }
    return completed, summary
