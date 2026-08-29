"""
Data layer — RCSB PDB fetch and Cα / B-factor extraction (notebook §1).

No classical MD. We extract only the Cα coordinates and B-factors per chain; the
contact topology built from these drives all downstream signal propagation
(the elastic-network hypothesis).
"""
import os
import socket
import urllib.request
import urllib.error

import numpy as np

PDB_CACHE = os.environ.get("PDB_CACHE", "./pdb_cache")
os.makedirs(PDB_CACHE, exist_ok=True)


def fetch(pdb, raise_on_error=False):
    """Download <pdb>.pdb from RCSB into the cache; return local path or None.

    `raise_on_error` (TASK-0290): default False preserves every existing
    caller's silent-None-on-failure behavior unchanged. Opt-in callers that
    need to distinguish "genuinely not found" from "the network call
    failed" (backend.active_site's deterministic-resolution path) pass
    True to have the underlying error propagate instead of being
    swallowed.
    """
    fp = os.path.join(PDB_CACHE, f"{pdb}.pdb")
    if not os.path.exists(fp):
        try:
            urllib.request.urlretrieve(
                f"https://files.rcsb.org/download/{pdb}.pdb", fp)
        except (urllib.error.URLError, socket.timeout, TimeoutError):
            # URLError is HTTPError's parent (covers DNS/connection failures
            # too); socket.timeout/TimeoutError are listed separately since
            # they're distinct classes on Python 3.9 (unified only in 3.10+).
            if raise_on_error:
                raise
            return None
    return fp


def load_structure(pdb, chains):
    """Parse the first model; collect (chain, resnum, CA coord, B-factor) for every
    standard residue with a Cα. `chains` is a comma-separated chain id string."""
    from Bio.PDB import PDBParser
    fp = fetch(pdb)
    if fp is None:
        return None
    s = PDBParser(QUIET=True).get_structure(pdb, fp)
    rows = []
    for ch in chains.split(","):
        ch = ch.strip()
        try:
            chain = s[0][ch]
        except KeyError:
            continue
        for res in chain:
            if res.id[0] == " " and "CA" in res:
                rows.append((ch, res.id[1], res["CA"].get_coord(),
                             res["CA"].get_bfactor()))
    if not rows:
        return None
    return dict(
        coords=np.array([r[2] for r in rows], float),
        resnums=np.array([r[1] for r in rows], int),
        chains=np.array([r[0] for r in rows]),
        bfac=np.array([r[3] for r in rows], float),
        pdb=pdb,
    )


def coarse_grain(st, k):
    """Keep every k-th residue (topology-preserving compression for large targets)."""
    if k <= 1:
        return st
    idx = np.arange(0, len(st["resnums"]), k)
    return {**st,
            "coords": st["coords"][idx], "resnums": st["resnums"][idx],
            "chains": st["chains"][idx], "bfac": st["bfac"][idx]}


def res_indices(st, rns):
    """Array indices of the structure rows whose resnum is in `rns`."""
    return np.where(np.isin(st["resnums"], list(rns)))[0]


def align_by_resnum(A, B):
    """Common residues between two structures + their index arrays in each."""
    common = np.intersect1d(A["resnums"], B["resnums"])
    ia = np.array([np.where(A["resnums"] == r)[0][0] for r in common])
    ib = np.array([np.where(B["resnums"] == r)[0][0] for r in common])
    return common, ia, ib


def sources_from_resnums(st, resnums):
    """Map a list of residue numbers (the active site) to source indices.
    Falls back to the single nearest residue if none are present."""
    src = res_indices(st, resnums)
    if len(src) == 0 and len(resnums):
        src = np.array([int(np.argmin(np.abs(st["resnums"] - resnums[0])))])
    return src
