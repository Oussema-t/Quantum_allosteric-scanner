"""
rcsb_extract.py — clean RCSB extraction for apo→holo (drug-bound) structure work.

Pulls everything needed from the RCSB PDB REST API for a known apo id, holo id and
ligand code: Cα structure (coords / residue numbers / names / chains / B-factors /
one-letter sequence), the bound drug's atoms, an apo-vs-holo identity check, and an
ordered list of user-supplied intermediate structures. General for ANY protein (no
hard-coding), CPU-only / pure Python, and robust — every public function returns a
dict and never raises (failures come back as ``{"error": "..."}``).

Parsing backend: Biotite → gemmi → BioPython (whichever is installed). Download:
requests → urllib. Animation / CTQW are intentionally out of scope here.
"""
import os
import difflib

import numpy as np

# --- optional deps, resolved at runtime (the module degrades gracefully) ------
try:
    import requests  # noqa: F401
    _HAVE_REQUESTS = True
except Exception:
    _HAVE_REQUESTS = False

CACHE_DIR = os.environ.get("PDB_CACHE", "./pdb_cache")
CIF_URL = "https://files.rcsb.org/download/{}.cif"
CHEMCOMP_API = "https://data.rcsb.org/rest/v1/core/chemcomp/{}"

# 20 standard + frequent modified residues → one-letter (unknown → 'X')
_THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
    "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
    "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
    "TYR": "Y", "VAL": "V", "MSE": "M", "SEC": "U", "PYL": "O",
}
_AA3 = set(_THREE_TO_ONE)
# water + common crystallization / cryo additives — never treated as "the drug"
_NON_LIGAND = {
    "HOH", "WAT", "DOD", "GOL", "EDO", "PEG", "PG4", "PGE", "1PE", "MPD", "BME",
    "DMS", "DTT", "TRS", "MES", "EPE", "ACT", "FMT", "ACE", "IMD", "BCT", "CO3",
    "SO4", "PO4", "NO3", "CL", "BR", "IOD", "NA", "K", "MG", "CA", "ZN", "MN",
    "FE", "CU", "NI", "CD", "HG", "CO", "FLC", "CIT", "TLA", "SCN", "AZI", "NH4",
}


# ──────────────────────────────────────────────────────────────────────────
# download + parsing backends
# ──────────────────────────────────────────────────────────────────────────
def _download_cif(pdb_id):
    """Download <pdb_id>.cif into CACHE_DIR (cached); return local path or raise."""
    pdb_id = str(pdb_id).strip().lower()
    if not pdb_id.isalnum() or not (4 <= len(pdb_id) <= 8):
        raise ValueError(f"'{pdb_id}' is not a valid PDB id")
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{pdb_id}.cif")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    url = CIF_URL.format(pdb_id)
    if _HAVE_REQUESTS:
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            raise FileNotFoundError(f"RCSB returned HTTP {r.status_code} for {pdb_id}")
        data = r.content
    else:
        import urllib.request, urllib.error
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                data = resp.read()
        except urllib.error.HTTPError as e:
            raise FileNotFoundError(f"RCSB returned HTTP {e.code} for {pdb_id}")
    with open(path, "wb") as fh:
        fh.write(data)
    return path


def _atoms_biotite(path):
    import biotite.structure.io.pdbx as pdbx
    try:
        cif = pdbx.CIFFile.read(path)
        a = pdbx.get_structure(cif, model=1, extra_fields=["b_factor"], use_author_fields=True)
    except Exception:                                   # older biotite API
        cif = pdbx.PDBxFile.read(path)
        a = pdbx.get_structure(cif, model=1, extra_fields=["b_factor"])
    return dict(chain_id=np.asarray(a.chain_id), res_id=np.asarray(a.res_id, int),
                res_name=np.char.upper(np.asarray(a.res_name).astype(str)),
                atom_name=np.asarray(a.atom_name).astype(str),
                coord=np.asarray(a.coord, float), b_factor=np.asarray(a.b_factor, float),
                hetero=np.asarray(a.hetero, bool))


def _atoms_gemmi(path):
    import gemmi
    st = gemmi.read_structure(path)
    model = st[0]
    ch, ri, rn, an, xyz, bf, het = [], [], [], [], [], [], []
    for chain in model:
        for res in chain:
            is_het = (res.het_flag == "H")
            for atom in res:
                ch.append(chain.name); ri.append(res.seqid.num)
                rn.append(res.name.upper().strip()); an.append(atom.name.strip())
                xyz.append([atom.pos.x, atom.pos.y, atom.pos.z])
                bf.append(atom.b_iso); het.append(is_het)
    return dict(chain_id=np.array(ch), res_id=np.array(ri, int), res_name=np.array(rn),
                atom_name=np.array(an), coord=np.array(xyz, float),
                b_factor=np.array(bf, float), hetero=np.array(het, bool))


def _atoms_biopython(path):
    from Bio.PDB import MMCIFParser
    s = MMCIFParser(QUIET=True).get_structure("x", path)
    model = next(s.get_models())
    ch, ri, rn, an, xyz, bf, het = [], [], [], [], [], [], []
    for chain in model:
        for res in chain:
            is_het = res.id[0] != " "
            for atom in res:
                ch.append(chain.id); ri.append(int(res.id[1]))
                rn.append(res.get_resname().upper().strip()); an.append(atom.get_name().strip())
                c = atom.get_coord(); xyz.append([float(c[0]), float(c[1]), float(c[2])])
                bf.append(float(atom.get_bfactor() or 0.0)); het.append(is_het)
    return dict(chain_id=np.array(ch), res_id=np.array(ri, int), res_name=np.array(rn),
                atom_name=np.array(an), coord=np.array(xyz, float),
                b_factor=np.array(bf, float), hetero=np.array(het, bool))


def _load_atoms(path):
    """Parse a .cif into normalized per-atom numpy arrays via the first available backend."""
    last = None
    for backend in (_atoms_biotite, _atoms_gemmi, _atoms_biopython):
        try:
            A = backend(path)
            if len(A["coord"]):
                return A
        except Exception as e:                          # try the next backend
            last = e
    raise RuntimeError(f"no parser could read {path} ({last})")


# ──────────────────────────────────────────────────────────────────────────
# 1. fetch_structure
# ──────────────────────────────────────────────────────────────────────────
def fetch_structure(pdb_id, chain=None):
    """Download+parse a PDB entry → Cα coords, residue nums/names, chains, B-factors, sequence."""
    try:
        path = _download_cif(pdb_id)
        A = _load_atoms(path)
        is_aa = np.isin(A["res_name"], list(_AA3))
        ca = is_aa & (A["atom_name"] == "CA")
        if not ca.any():
            return {"error": f"{pdb_id}: no protein Cα atoms found"}
        if chain is None:                               # auto-pick the longest protein chain
            chains, counts = np.unique(A["chain_id"][ca], return_counts=True)
            chain = str(chains[int(np.argmax(counts))])
        sel = ca & (A["chain_id"] == chain)
        if not sel.any():
            avail = ", ".join(sorted(set(A["chain_id"][ca].tolist())))
            return {"error": f"{pdb_id}: chain '{chain}' has no protein Cα. Available: {avail}"}
        idx = np.where(sel)[0]
        # dedup altlocs (keep first Cα per residue number), then order by residue number
        seen, keep = set(), []
        for i in idx:
            r = int(A["res_id"][i])
            if r not in seen:
                seen.add(r); keep.append(i)
        keep = np.array(keep, int)
        keep = keep[np.argsort(A["res_id"][keep])]
        resnames = A["res_name"][keep].tolist()
        sequence = "".join(_THREE_TO_ONE.get(rn, "X") for rn in resnames)
        return {
            "pdb_id": str(pdb_id).upper(), "chain": str(chain),
            "coords": A["coord"][keep], "resnums": A["res_id"][keep].astype(int),
            "resnames": resnames, "chain_ids": A["chain_id"][keep].astype(str).tolist(),
            "bfactors": A["b_factor"][keep].astype(float), "sequence": sequence,
            "n_residues": int(len(keep)),
        }
    except Exception as e:
        return {"error": f"fetch_structure({pdb_id}): {e}"}


# ──────────────────────────────────────────────────────────────────────────
# 2. fetch_ligand
# ──────────────────────────────────────────────────────────────────────────
def _ligand_name(code):
    """Best-effort chemical name for a 3-letter ligand code (falls back to the code)."""
    if not _HAVE_REQUESTS:
        return code
    try:
        r = requests.get(CHEMCOMP_API.format(code), timeout=8)
        if r.ok:
            return r.json().get("chem_comp", {}).get("name", code) or code
    except Exception:
        pass
    return code


def fetch_ligand(pdb_id, ligand_code=None):
    """Extract a bound drug's atoms/coords from a holo entry (auto-pick largest non-additive if no code)."""
    try:
        path = _download_cif(pdb_id)
        A = _load_atoms(path)
        het = A["hetero"] & ~np.isin(A["res_name"], list(_AA3))
        if not het.any():
            return {"error": f"{pdb_id}: no heteroatom (ligand) groups found"}
        if ligand_code:
            code = ligand_code.upper().strip()
            sel = het & (A["res_name"] == code)
            if not sel.any():
                found = ", ".join(sorted(set(A["res_name"][het].tolist())))
                return {"error": f"{pdb_id}: ligand '{code}' not present. Heteroatoms: {found}"}
        else:                                           # auto-pick: largest group that isn't water/additive
            cand = het & ~np.isin(A["res_name"], list(_NON_LIGAND))
            if not cand.any():
                return {"error": f"{pdb_id}: only water/additives present, no drug-like ligand"}
            names, counts = np.unique(A["res_name"][cand], return_counts=True)
            code = str(names[int(np.argmax(counts))])
            sel = cand & (A["res_name"] == code)
        coords = A["coord"][sel]
        return {
            "pdb_id": str(pdb_id).upper(), "code": code, "name": _ligand_name(code),
            "n_atoms": int(sel.sum()), "coords": coords,
        }
    except Exception as e:
        return {"error": f"fetch_ligand({pdb_id}): {e}"}


# ──────────────────────────────────────────────────────────────────────────
# 3. fetch_apo_holo
# ──────────────────────────────────────────────────────────────────────────
def _seq_identity(a, b):
    """% sequence similarity between two one-letter strings (difflib; 0 if either empty)."""
    if not a or not b:
        return 0.0
    return round(100.0 * difflib.SequenceMatcher(None, a, b).ratio(), 1)


def fetch_apo_holo(apo_id, holo_id, drug_code=None, chain=None, identity_warn=95.0):
    """One call: apo + holo structure/sequence + the drug, with an apo↔holo identity check."""
    apo = fetch_structure(apo_id, chain)
    holo = fetch_structure(holo_id, chain)
    drug = fetch_ligand(holo_id, drug_code)
    out = {"apo": apo, "holo": holo, "drug": drug, "warnings": []}
    if "error" in apo:
        out["warnings"].append(f"apo: {apo['error']}")
    if "error" in holo:
        out["warnings"].append(f"holo: {holo['error']}")
    if "error" in drug:
        out["warnings"].append(f"drug: {drug['error']}")
    if "error" not in apo and "error" not in holo:
        ident = _seq_identity(apo["sequence"], holo["sequence"])
        out["identity_pct"] = ident
        out["same_protein"] = bool(ident >= identity_warn)
        if not out["same_protein"]:
            out["warnings"].append(
                f"apo/holo sequence identity is only {ident}% (< {identity_warn}%) — "
                f"these may not be the same protein; check before animating.")
    else:
        out["identity_pct"] = None
        out["same_protein"] = None
    return out


# ──────────────────────────────────────────────────────────────────────────
# 4. fetch_intermediates
# ──────────────────────────────────────────────────────────────────────────
def fetch_intermediates(pdb_ids, chain=None):
    """Fetch a user-supplied, arbitrary-length ordered list of intermediate-state structures."""
    try:
        ids = list(pdb_ids or [])
        if not ids:
            return {"error": "fetch_intermediates: empty pdb_ids list", "structures": []}
        structures, errors = [], []
        for pid in ids:
            s = fetch_structure(pid, chain)
            structures.append(s)
            if "error" in s:
                errors.append(s["error"])
        return {
            "n_requested": len(ids), "n_ok": sum("error" not in s for s in structures),
            "structures": structures, "errors": errors,
        }
    except Exception as e:
        return {"error": f"fetch_intermediates: {e}", "structures": []}


# ──────────────────────────────────────────────────────────────────────────
# usage example
# ──────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # apo 4OBE, holo 6OIM (KRAS G12C), drug MOV (Sotorasib) — any protein works.
    bundle = fetch_apo_holo("4OBE", "6OIM", "MOV", chain="A")
    apo, holo, drug = bundle["apo"], bundle["holo"], bundle["drug"]
    print("apo :", apo.get("pdb_id"), apo.get("chain"), apo.get("n_residues"), "res")
    print("holo:", holo.get("pdb_id"), holo.get("chain"), holo.get("n_residues"), "res")
    print("drug:", drug.get("code"), "-", drug.get("name"), f"({drug.get('n_atoms')} atoms)")
    print("apo↔holo identity:", bundle.get("identity_pct"), "% | same protein:", bundle.get("same_protein"))
    for w in bundle["warnings"]:
        print("  [warn]", w)

    # user-chosen intermediates (pass as many or as few as you like)
    inter = fetch_intermediates(["6OIM"], chain="A")
    print("intermediates ok:", inter.get("n_ok"), "/", inter.get("n_requested"))
