"""
Active-site auto-detection for any protein.

Resolves a structure's functional residues, in order of reliability:

  1. UniProt curated annotations (`Active site`, `Binding site`) — the authoritative
     source for catalytic/functional residues. UniProt uses canonical-sequence
     numbering, so we recover the offset to the PDB author numbering by locating a
     resolved residue window in the UniProt sequence, then VERIFY each mapped
     residue's name matches before accepting it.
  2. Ligand/drug binding site computed from the structure (or a supplied holo) — a
     strong proxy when no curated active site exists.
  3. PDB `SITE` records — author-annotated sites, used as a last resort.

Returns the residues in PDB author numbering plus the source and a short note, so the
UI can show where the active site came from and how confident we are.
"""
import json
import os
import socket
import time
import urllib.error

from .rcsb import _get_json, fetch, ligands_and_sites
from .discovery import get_uniprot

UNIPROT_API = "https://rest.uniprot.org/uniprotkb"

# TASK-0290: `detect_active_site` was non-determinstic -- a transient
# network failure in the UniProt tier silently fell through to a
# different tier, with no error and no retry, changing the returned
# active site (and everything computed downstream, principally `min_A`)
# from one call to the next. Fixed two ways:
#   1. Resolve once, cache to disk keyed by (pdb_id, chain) -- reused
#      by every later call, network only on a genuine cache miss. Same
#      cache directory `data_layer.fetch` already uses (gitignored).
#   2. `_RETRYABLE` -- network-layer exceptions only, never a bug's own
#      exception -- are retried once, then raised (never silently
#      swallowed into "try the next tier"). "UniProt has no annotation
#      for this entry" (a real negative -- `get_uniprot` returns `[]`,
#      or the UniProt record has no Active/Binding site features) still
#      returns `None` cleanly and falls through to the next tier,
#      unchanged from before -- that path never raised and still doesn't.
_RETRYABLE = (urllib.error.URLError, socket.timeout, TimeoutError, OSError, json.JSONDecodeError)
_CACHE_PATH = os.path.join(os.environ.get("PDB_CACHE", "./pdb_cache"), "active_site_cache.json")


class ActiveSiteNetworkError(RuntimeError):
    """A UniProt/RCSB network call failed and stayed failed after retry --
    raised, never silently absorbed into falling through to a different,
    lower-confidence tier."""


def _retry(fn, attempts=2, delay=1.0):
    last = None
    for i in range(attempts):
        try:
            return fn()
        except _RETRYABLE as e:
            last = e
            if i + 1 < attempts:
                time.sleep(delay)
    raise ActiveSiteNetworkError(f"{type(last).__name__}: {last}") from last


def _load_cache():
    try:
        with open(_CACHE_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_cache(cache):
    os.makedirs(os.path.dirname(_CACHE_PATH), exist_ok=True)
    with open(_CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=1, sort_keys=True)


_THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
    "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
    "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
    "TYR": "Y", "VAL": "V", "MSE": "M", "SEC": "U", "PYL": "O",
}


def _residues_by_num(pdb_id, chain, raise_on_error=False):
    """Ordered {author_resnum: one-letter} for the first requested chain."""
    from Bio.PDB import PDBParser
    fp = fetch(pdb_id, raise_on_error=raise_on_error)
    if fp is None:
        return {}
    s = PDBParser(QUIET=True).get_structure(pdb_id, fp)
    ch = chain.split(",")[0].strip()
    try:
        c = s[0][ch]
    except KeyError:
        c = next(iter(s[0]))
    out = {}
    for res in c:
        if res.id[0] == " ":
            aa = _THREE_TO_ONE.get(res.get_resname().strip().upper())
            if aa:
                out[res.id[1]] = aa
    return out


def _uniprot_features(acc, raise_on_error=False):
    """(sequence, [(uniprot_pos, kind, description)]) for active/binding features."""
    data = _get_json(f"{UNIPROT_API}/{acc}.json", raise_on_error=raise_on_error)
    if not data:
        return None, []
    seq = (data.get("sequence", {}) or {}).get("value", "")
    feats = []
    for f in data.get("features", []) or []:
        t = f.get("type", "")
        if t not in ("Active site", "Binding site"):
            continue
        loc = f.get("location", {}) or {}
        start = (loc.get("start", {}) or {}).get("value")
        end = (loc.get("end", {}) or {}).get("value", start)
        if start is None:
            continue
        for p in range(int(start), int(end) + 1):
            feats.append((p, t, f.get("description", "")))
    return seq, feats


def _find_offset(res_by_num, uniprot_seq):
    """Offset δ such that author_resnum = uniprot_pos + δ, found by locating a
    consecutive resolved window inside the UniProt sequence. None if not found."""
    if not uniprot_seq:
        return None
    nums = sorted(res_by_num)
    for i, n0 in enumerate(nums):
        window = []
        for k in range(40):
            if (n0 + k) in res_by_num:
                window.append(res_by_num[n0 + k])
            else:
                break
        if len(window) >= 12:
            idx = uniprot_seq.find("".join(window))
            if idx != -1 and uniprot_seq.find("".join(window), idx + 1) == -1:
                # unique match -> trustworthy offset
                return n0 - (idx + 1)
    return None


def _from_uniprot(pdb_id, chain, raise_on_error=False):
    accs = get_uniprot(pdb_id, raise_on_error=raise_on_error)
    if not accs:
        return None
    res_by_num = _residues_by_num(pdb_id, chain, raise_on_error=raise_on_error)
    if not res_by_num:
        return None
    seq, feats = _uniprot_features(accs[0], raise_on_error=raise_on_error)
    if not feats:
        return None
    delta = _find_offset(res_by_num, seq)
    if delta is None:
        return None
    active, binding = [], []
    for upos, kind, _desc in feats:
        auth = upos + delta
        aa = res_by_num.get(auth)
        if aa is None:
            continue
        # verify the residue name matches what UniProt expects at that position
        if seq and 1 <= upos <= len(seq) and seq[upos - 1] != aa:
            continue
        (active if kind == "Active site" else binding).append(auth)
    residues = sorted(set(active) | set(binding))
    if not residues:
        return None
    return {
        "active_site": residues,
        "source": "uniprot",
        "detail": f"UniProt {accs[0]} — {len(set(active))} active, "
                  f"{len(set(binding))} binding residues",
        "uniprot": accs[0],
    }


def _from_ligands(pdb_id, chain, holo_pdb=None, raise_on_error=False):
    """Union of drug/ligand binding-site residues (a proxy active site)."""
    src = holo_pdb or pdb_id
    ligs = ligands_and_sites(src, chain, raise_on_error=raise_on_error)
    pick = [l for l in ligs if l["is_drug"]] or [l for l in ligs if l["category"] == "cofactor"]
    residues = sorted(set(r for l in pick for r in l["binding_site"]))
    if not residues:
        return None
    names = ", ".join(sorted(set(l["code"] for l in pick)))
    return {
        "active_site": residues,
        "source": "ligand",
        "detail": f"ligand binding site from {src} ({names}) — no curated active site",
    }


def _from_site_records(pdb_id, chain, raise_on_error=False):
    """Residues listed in PDB SITE records for the requested chain."""
    fp = fetch(pdb_id, raise_on_error=raise_on_error)
    if fp is None:
        return None
    ch = chain.split(",")[0].strip()
    residues = set()
    with open(fp) as fh:
        for line in fh:
            if not line.startswith("SITE"):
                continue
            body = line[18:]
            # repeating fields of (resName chainID seqNum) every 11 cols
            for off in range(0, len(body), 11):
                field = body[off:off + 11]
                if len(field) < 9:
                    continue
                c = field[4:5].strip()
                num = field[5:9].strip()
                if c == ch and num.lstrip("-").isdigit():
                    residues.add(int(num))
    if not residues:
        return None
    return {"active_site": sorted(residues), "source": "pdb_site",
            "detail": f"PDB SITE records in {pdb_id} (author-annotated)"}


def detect_active_site(pdb_id, chain="A", holo_pdb=None):
    """Best-effort active site for any protein, with provenance.

    Deterministic (TASK-0290): resolved once per (pdb_id, chain), then
    cached to disk -- every later call for the same key returns the exact
    cached result, no network touched. On a cache miss, a tier's own
    network call is retried once on a transient failure
    (`ActiveSiteNetworkError`, `_RETRYABLE`) and then RAISES rather than
    silently falling through to a lower-confidence tier -- "the call
    failed" and "this tier genuinely has nothing" are no longer the same
    outcome. A real negative (`get_uniprot` returns `[]`, no Active/Binding
    features, `_find_offset` can't place the sequence) still returns
    `None` cleanly and falls through, exactly as before.
    """
    pdb_id = pdb_id.upper()
    key = f"{pdb_id}:{chain}"
    cache = _load_cache()
    if key in cache:
        return cache[key]

    for fn in (lambda: _from_uniprot(pdb_id, chain, raise_on_error=True),
               lambda: _from_ligands(pdb_id, chain, holo_pdb, raise_on_error=True),
               lambda: _from_site_records(pdb_id, chain, raise_on_error=True)):
        res = _retry(fn)
        if res and res.get("active_site"):
            cache[key] = res
            _save_cache(cache)
            return res
    result = {"active_site": [], "source": "none",
              "detail": "no curated active site, ligand pocket, or SITE records found"}
    cache[key] = result
    _save_cache(cache)
    return result
