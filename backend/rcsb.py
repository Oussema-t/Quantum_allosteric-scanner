"""
RCSB structure intelligence.

Extracts the biologist-facing facts about a PDB entry directly from the structure
(and the RCSB Data API for human-readable names):

  * chains + residue ranges
  * bound ligands / drugs (HETATM), with full chemical names and the protein
    residues each one contacts (its binding site)
  * missing (unresolved) residues, parsed from REMARK 465
  * entry title, organism, experimental method, resolution

Everything degrades gracefully: if the network is unavailable, the locally parsed
facts (chains, ligands, missing residues, binding sites) still work; only the
human-readable names/title are skipped.
"""
import json
import re
import urllib.request

import numpy as np
from scipy.spatial.distance import cdist

from .data_layer import fetch

DATA_API = "https://data.rcsb.org/rest/v1/core"

# Curated crystallographic-additive blocklist (NOT drugs): solvent, cryoprotectants,
# buffers, ions, detergents, lipids/alkanes. The chem_comp-driven classifier below also
# catches future additives heuristically, but this is the fast, authoritative first pass.
_NON_DRUG = {
    # solvent / cryoprotectants
    "HOH", "DOD", "WAT", "GOL", "EDO", "PEG", "PG4", "PGE", "1PE", "2PE", "P6G",
    "PG0", "PG4", "MPD", "MRD", "BU3", "DMS", "DMSO", "TFA",
    # buffers / small additives
    "ACT", "ACY", "FMT", "TRS", "EPE", "MES", "BME", "IMD", "CAC", "BCT", "CIT",
    "FLC", "TLA", "MLA", "MLI", "BTB", "MPO", "POL", "PO4", "SO4", "NO3", "SCN",
    # ions
    "NA", "CL", "MG", "ZN", "CA", "K", "MN", "FE", "FE2", "FE3", "CU", "CU1",
    "NI", "CO", "CD", "BR", "IOD", "F", "SR", "CS", "BA", "HG", "PT", "AU",
    "LI", "RB", "ZN2", "MN3", "YB", "GD", "EU", "SM", "TB", "W",
    # detergents
    "LDA", "LMT", "BOG", "BNG", "DDM", "C8E", "SDS", "F09", "TRT", "OGA", "HTG",
    "BGL", "2CV", "JEF", "P4C", "PEE", "D10", "DD9",
    # lipids / fatty acids / alkanes (long aliphatic chains)
    "PLM", "MYR", "OLA", "STE", "DAO", "HEX", "OCT", "DKA", "UND", "16C", "R16",
    "PEF", "LHG", "PGV", "PEV", "Y01", "CLR", "OLC",
}
# common biological cofactors worth showing but not the "drug" of interest
_COFACTORS = {"GTP", "GDP", "GNP", "GSP", "GCP", "ATP", "ADP", "AMP", "ANP", "ACP",
              "NAD", "NAI", "NAP", "NDP", "FAD", "FMN", "SAM", "SAH", "COA", "TPP",
              "PLP", "BTN", "B12", "HEM", "HEC", "HEA", "BEF", "ALF", "MG", "MN"}

# drug signals from the RCSB chem_comp record
_DRUG_DB_REFS = {"DrugBank", "Pharos", "BindingDB"}
_DRUG_HEAVY_MIN = 30          # heavy atoms that qualify as drug-sized without a drug-DB ref

_name_cache = {}
_record_cache = {}
_FORMULA_RE = re.compile(r"([A-Z][a-z]?)(\d*)")


# in-memory cache of raw GET responses (RCSB Data API is immutable per PDB id, so
# repeat loads + cutoff/param changes reuse the download instead of re-hitting the
# network). We cache the TEXT and re-parse per call, so callers can't mutate a shared
# dict. None responses are not cached (so transient failures can recover).
_GET_CACHE = {}


def _get_json(url, timeout=8):
    if url in _GET_CACHE:
        try:
            return json.loads(_GET_CACHE[url])
        except Exception:
            return None
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            text = r.read().decode("utf-8")
        _GET_CACHE[url] = text
        return json.loads(text)
    except Exception:
        return None


def _parse_formula(formula):
    """'C34 H67 N O3' -> {'C':34,'H':67,'N':1,'O':3}."""
    out = {}
    for el, num in _FORMULA_RE.findall(formula or ""):
        if not el:
            continue
        out[el] = out.get(el, 0) + (int(num) if num else 1)
    return out


def _chem_comp_record(code):
    """Cached RCSB chem_comp record fields: name, type, formula, heavy-atom count,
    cross-reference resource names, parsed element counts. None if unavailable."""
    code = (code or "").strip().upper()
    if code in _record_cache:
        return _record_cache[code]
    data = _get_json(f"{DATA_API}/chemcomp/{code}")
    rec = None
    if data:
        cc = data.get("chem_comp", {}) or {}
        info = data.get("rcsb_chem_comp_info", {}) or {}
        related = data.get("rcsb_chem_comp_related", []) or []
        formula = cc.get("formula") or ""
        rec = {
            "name": cc.get("name"),
            "type": cc.get("type"),
            "formula": formula,
            "heavy": info.get("atom_count_heavy"),
            "refs": set(r.get("resource_name") for r in related if r.get("resource_name")),
            "elements": _parse_formula(formula),
        }
    _record_cache[code] = rec
    return rec


def chem_comp_name(code):
    """Full chemical name for a ligand 3-letter code (cached, best-effort)."""
    rec = _chem_comp_record(code)
    return rec["name"] if rec else None


def _is_aliphatic_additive(elems):
    """True for long saturated carbon chains (lipids/fatty acids/alkanes/detergents):
    many carbons, few heteroatoms, no halogens, high H:C ratio. Generalizes additives
    like 16C/R16/PLM beyond the curated list."""
    c = elems.get("C", 0)
    h = elems.get("H", 0)
    hetero = sum(n for e, n in elems.items() if e not in ("C", "H"))
    halogens = sum(elems.get(x, 0) for x in ("F", "Cl", "Br", "I"))
    return c >= 10 and hetero <= 4 and halogens == 0 and (h / c) >= 1.8


def classify_ligand(code, n_atoms=None):
    """Return (category, is_drug) for a HET code, driven by the chem_comp record + the
    curated additive blocklist. category ∈ {drug, ligand, cofactor, solvent/ion}.
    - drug: substantial organic, not an additive/cofactor, with a drug-DB cross-reference
      OR a drug-sized heavy-atom count.
    - ligand: real organic ligand with no drug signal (visible, but is_drug=False).
    - cofactor / solvent/ion: biological cofactors / additives, ions, buffers, lipids."""
    code = (code or "").strip().upper()
    if code in _NON_DRUG:
        return "solvent/ion", False
    if code in _COFACTORS:
        return "cofactor", False
    rec = _chem_comp_record(code)
    if rec is None:                                       # data unavailable -> degrade safely
        if n_atoms is not None and n_atoms <= 2:
            return "solvent/ion", False
        return ("drug", True) if (n_atoms or 0) >= _DRUG_HEAVY_MIN else ("ligand", False)
    heavy = rec["heavy"] or (n_atoms or 0)
    elems = rec["elements"]
    if heavy <= 2 or "C" not in elems:                    # monoatomic ions / inorganic
        return "solvent/ion", False
    if _is_aliphatic_additive(elems):                     # lipids / detergents / alkanes
        return "solvent/ion", False
    if _DRUG_DB_REFS & rec["refs"] or heavy >= _DRUG_HEAVY_MIN:
        return "drug", True
    return "ligand", False                                # organic ligand, no drug signal


def entry_summary(pdb_id):
    """Title, method, resolution, organism — best-effort via the Data API."""
    pdb_id = pdb_id.upper()
    data = _get_json(f"{DATA_API}/entry/{pdb_id}")
    if not data:
        return {}
    info = data.get("rcsb_entry_info", {}) or {}
    res = info.get("resolution_combined")
    out = {
        "title": (data.get("struct", {}) or {}).get("title"),
        "method": (info.get("experimental_method")
                   or ",".join(data.get("rcsb_entry_info", {})
                               .get("experimental_method", []) or [])),
        "resolution": (res[0] if isinstance(res, list) and res else None),
        "deposited_residues": info.get("deposited_polymer_monomer_count"),
    }
    return out


def parse_missing_residues(pdb_id, chains=None):
    """Missing (unresolved) residues from REMARK 465. Returns list of dicts
    {chain, resnum, resname}. Optionally filter to `chains` (comma-sep)."""
    fp = fetch(pdb_id)
    if fp is None:
        return []
    want = set(c.strip() for c in chains.split(",")) if chains else None
    out = []
    in_block = False
    # data lines look like: "REMARK 465     GLY A    10 "
    pat = re.compile(r"^REMARK 465\s+([A-Z0-9]{1,3})\s+([A-Za-z0-9])\s+(-?\d+)[A-Za-z]?\s*$")
    with open(fp) as fh:
        for line in fh:
            if not line.startswith("REMARK 465"):
                continue
            m = pat.match(line.rstrip("\n"))
            if m:
                resname, ch, resseq = m.group(1), m.group(2), int(m.group(3))
                if want and ch not in want:
                    continue
                out.append({"chain": ch, "resnum": resseq, "resname": resname})
    return out


def _iter_hetero(model):
    """Yield (chain_id, residue) for every hetero (HETATM) group in a model."""
    for chain in model:
        for res in chain:
            if res.id[0].startswith("H_"):
                yield chain.id, res


def ligands_and_sites(pdb_id, chains=None, contact_cutoff=4.5):
    """Every non-water HETATM group in the entry, with its chemical name and the
    protein residues it contacts (binding site). Returns list of ligand dicts."""
    from Bio.PDB import PDBParser
    fp = fetch(pdb_id)
    if fp is None:
        return []
    s = PDBParser(QUIET=True).get_structure(pdb_id, fp)
    model = s[0]

    # protein CA coords per (chain,resnum) for binding-site detection
    prot = []
    for chain in model:
        for res in chain:
            if res.id[0] == " ":
                for atom in res:
                    prot.append((chain.id, res.id[1], atom.get_coord()))
    prot_chain = np.array([p[0] for p in prot]) if prot else np.array([])
    prot_res = np.array([p[1] for p in prot]) if prot else np.array([])
    prot_xyz = np.array([p[2] for p in prot], float) if prot else np.zeros((0, 3))

    out = []
    for ch_id, res in _iter_hetero(model):
        code = res.get_resname().strip().upper()
        if code in {"HOH", "DOD", "WAT"}:
            continue
        lig_xyz = np.array([a.get_coord() for a in res], float)
        # binding-site residues
        site = []
        if len(prot_xyz) and len(lig_xyz):
            dmin = cdist(prot_xyz, lig_xyz).min(1)
            hit = dmin <= contact_cutoff
            seen = set()
            for c, rn in zip(prot_chain[hit], prot_res[hit]):
                key = (c, int(rn))
                if key not in seen:
                    seen.add(key)
                    site.append({"chain": c, "resnum": int(rn)})
            site.sort(key=lambda x: (x["chain"], x["resnum"]))
        category, is_drug = classify_ligand(code, n_atoms=len(res))
        out.append({
            "code": code,
            "name": chem_comp_name(code),
            "chain": ch_id,
            "resnum": res.id[1],
            "n_atoms": len(res),
            "category": category,
            "is_drug": is_drug,
            "binding_site": [d["resnum"] for d in site],
            "binding_site_full": site,
        })
    # drugs first, then cofactors, then other ligands, then solvent/ions
    order = {"drug": 0, "cofactor": 1, "ligand": 2, "solvent/ion": 3}
    out.sort(key=lambda l: (order.get(l["category"], 4), -l["n_atoms"]))
    return out


def chain_summary(pdb_id, chains=None):
    """Per-chain residue count and numbering range from the resolved structure."""
    from Bio.PDB import PDBParser
    fp = fetch(pdb_id)
    if fp is None:
        return []
    s = PDBParser(QUIET=True).get_structure(pdb_id, fp)
    want = set(c.strip() for c in chains.split(",")) if chains else None
    out = []
    for chain in s[0]:
        nums = [res.id[1] for res in chain if res.id[0] == " "]
        if not nums:
            continue
        if want and chain.id not in want:
            continue
        out.append({"chain": chain.id, "n_residues": len(nums),
                    "first": min(nums), "last": max(nums)})
    return out


def chain_resnums(pdb_id):
    """{chain_id: set(author resnums)} for the first model — for chain matching."""
    from Bio.PDB import PDBParser
    fp = fetch(pdb_id)
    if fp is None:
        return {}
    s = PDBParser(QUIET=True).get_structure(pdb_id, fp)
    out = {}
    for ch in s[0]:
        nums = {res.id[1] for res in ch if res.id[0] == " "}
        if nums:
            out[ch.id] = nums
    return out


def drug_bearing_chain(pdb_id):
    """The protein chain that actually contacts the bound DRUG (most drug contacts).
    Returns (chain_id, drug_code), or (None, None) if no drug is present."""
    from collections import Counter
    drug_ligs = [l for l in ligands_and_sites(pdb_id) if l["is_drug"]]
    if not drug_ligs:
        return None, None
    counts = Counter()
    code_for = {}
    for l in drug_ligs:
        for d in l.get("binding_site_full", []):
            counts[d["chain"]] += 1
            code_for.setdefault(d["chain"], l["code"])
    if not counts:  # drug present but no mapped protein contacts -> use its own chain
        return drug_ligs[0].get("chain"), drug_ligs[0]["code"]
    chain = counts.most_common(1)[0][0]
    return chain, code_for.get(chain, drug_ligs[0]["code"])


def structure_intel(pdb_id, chains=None):
    """One call: chains, ligands/drugs + binding sites, missing residues, summary."""
    pdb_id = pdb_id.upper()
    ligands = ligands_and_sites(pdb_id, chains)
    missing = parse_missing_residues(pdb_id, chains)
    return {
        "pdb_id": pdb_id,
        "summary": entry_summary(pdb_id),
        "chains": chain_summary(pdb_id, chains),
        "ligands": ligands,
        "drugs": [l for l in ligands if l["is_drug"]],
        "missing_residues": missing,
        "n_missing": len(missing),
    }
