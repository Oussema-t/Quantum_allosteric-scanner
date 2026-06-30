"""Fetch PDB structures and extract per-residue Cα data."""
from __future__ import annotations

import numpy as np


def fetch_ca(
    pdb_id: str,
    chains: list[str] | None = None,
    keep_nucleic: bool = False,
) -> tuple[np.ndarray, np.ndarray, list[str], list[str]]:
    """Download a PDB entry and return Cα atoms.

    Parameters
    ----------
    pdb_id : str
        Four-letter PDB accession code.
    chains : list of str, optional
        Chain IDs to keep. None keeps all protein chains.
    keep_nucleic : bool
        If True, include nucleic-acid residues (using P atom as representative).

    Returns
    -------
    coords   : (N, 3) float64  – Cα/P coordinates in Ångströms
    resnums  : (N,) int        – residue sequence numbers
    resnames : list[N]         – 3-letter residue names
    chain_ids: list[N]         – chain identifier for each residue
    """
    import prody  # lazy import – not needed for pure physics tests

    prody.confProDy(verbosity="none")
    struct = prody.parsePDB(pdb_id, compressed=False)
    if struct is None:
        raise ValueError(f"Could not parse PDB entry '{pdb_id}'")

    sel_parts = ["protein and name CA"]
    if keep_nucleic:
        sel_parts.append("nucleic and name P")
    sel_str = " or ".join(f"({p})" for p in sel_parts)

    if chains:
        chain_sel = " or ".join(f"chain {c}" for c in chains)
        sel_str = f"({sel_str}) and ({chain_sel})"

    atoms = struct.select(sel_str)
    if atoms is None or len(atoms) == 0:
        raise ValueError(
            f"No Cα/P atoms found in {pdb_id} with selection '{sel_str}'"
        )

    coords = atoms.getCoords().astype(np.float64)
    resnums = atoms.getResnums().astype(np.int32)
    resnames = atoms.getResnames().tolist()
    chain_ids = atoms.getChids().tolist()
    return coords, resnums, resnames, chain_ids


def list_hetero(pdb_id: str) -> list[dict]:
    """Return all HETATM residues in a PDB entry – use to find ligand resnames.

    Returns a list of dicts with keys: resname, chain, resnum, natoms.
    Sorted by natoms descending (largest ligands first).
    """
    import prody

    prody.confProDy(verbosity="none")
    struct = prody.parsePDB(pdb_id, compressed=False)
    if struct is None:
        raise ValueError(f"Could not parse PDB entry '{pdb_id}'")

    het = struct.select("hetatm")
    if het is None:
        return []

    seen: dict[tuple, int] = {}
    for atom in het:
        key = (atom.getResname(), atom.getChid(), atom.getResnum())
        seen[key] = seen.get(key, 0) + 1

    result = [
        {"resname": k[0], "chain": k[1], "resnum": k[2], "natoms": v}
        for k, v in seen.items()
    ]
    return sorted(result, key=lambda d: d["natoms"], reverse=True)


def get_pocket_residues(
    pdb_id: str,
    ligand_resname: str,
    radius: float = 4.5,
    chains: list[str] | None = None,
    exclusions: list[str] | None = None,
) -> np.ndarray:
    """Return Cα residue indices (0-based, within the chain selection) within
    *radius* Ångströms of any atom of the named ligand in the holo structure.

    Parameters
    ----------
    pdb_id : str
        Holo PDB accession code.
    ligand_resname : str
        3-letter het residue name of the allosteric drug.
    radius : float
        Shell radius in Ångströms (default 4.5 Å per challenge spec).
    chains : list[str] | None
        Same chain filter used for the Cα extraction.
    exclusions : list[str] | None
        Additional het residue names to skip (e.g. orthosteric drugs).

    Returns
    -------
    indices : (M,) int array of 0-based indices into the Cα coordinate array
              returned by fetch_ca with the same pdb_id/chains arguments.
    """
    import prody

    prody.confProDy(verbosity="none")
    exclusions = set(exclusions or [])

    struct = prody.parsePDB(pdb_id, compressed=False)
    if struct is None:
        raise ValueError(f"Could not parse PDB entry '{pdb_id}'")

    lig = struct.select(f"resname {ligand_resname} and not water")
    if lig is None:
        het_list = [d["resname"] for d in list_hetero(pdb_id)]
        raise ValueError(
            f"Ligand '{ligand_resname}' not found in {pdb_id}. "
            f"Available HET residues: {het_list}"
        )

    lig_coords = lig.getCoords()

    # Select Cα atoms matching the same chain filter as fetch_ca
    ca_sel = "protein and name CA"
    if chains:
        chain_sel = " or ".join(f"chain {c}" for c in chains)
        ca_sel = f"({ca_sel}) and ({chain_sel})"
    ca_atoms = struct.select(ca_sel)
    if ca_atoms is None:
        raise ValueError(f"No Cα atoms in {pdb_id} matching chain filter {chains}")

    ca_coords = ca_atoms.getCoords()

    # Compute min distance from each Cα to any ligand atom
    diff = ca_coords[:, np.newaxis, :] - lig_coords[np.newaxis, :, :]  # (N, L, 3)
    min_dist = np.sqrt((diff ** 2).sum(axis=2)).min(axis=1)             # (N,)

    pocket_idx = np.where(min_dist <= radius)[0]
    return pocket_idx.astype(np.int32)
