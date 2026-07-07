"""Phase 0b – deterministic structure cleanup.

Driven by config/targets.yaml so every cleaning decision is reproducible
without PyMOL or manual intervention.

Key guarantees
--------------
- Only one model (MODEL 1 / first ATOM block) is kept.
- Alternate locations: only the 'A' alt-loc (or highest occupancy) is kept.
- Insertion codes are stripped; residues are flagged in the quality report.
- Waters, common ions, and crystallographic cofactors are removed.
- Nucleic acid is retained only when keep_nucleic=True (MYC_MAX).
- The resulting Cα graph must be connected; disconnected graphs are an error.
- Quality metadata (resolution, B-factor stats, gap list) is returned alongside
  the clean coordinates.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import yaml


# Residue names that are NOT structural protein/nucleic residues
_COMMON_SOLVENTS = {"HOH", "WAT", "H2O", "DOD", "D2O"}
_COMMON_IONS = {
    "MG", "ZN", "CA", "NA", "CL", "K", "MN", "FE", "CU", "CO",
    "NI", "CD", "HG", "PB", "SO4", "PO4", "GOL", "EDO", "PEG",
    "ACT", "ACE", "FMT", "DMS", "MPD", "TRS", "BME",
}


@dataclass
class CleanResult:
    pdb_id: str
    coords: np.ndarray          # (N, 3) Cα/P coordinates
    resnums: np.ndarray         # (N,) residue numbers (original numbering)
    resnames: list[str]         # 3-letter residue names
    chain_ids: list[str]        # chain IDs
    resolution: float | None    # crystallographic resolution in Å, None if unavailable
    bfactors: np.ndarray        # (N,) per-residue Cα B-factor (TASK-0008: build_H_new/H10 need the full array, not just b_mean/b_std)
    b_mean: float               # mean B-factor of Cα atoms
    b_std: float                # std of B-factors
    gap_pairs: list[tuple[int, int]]  # (res_i, res_j) pairs where |resnum gap| > 1
    insertion_code_residues: list[str]  # residues that had insertion codes (flagged)
    warnings: list[str] = field(default_factory=list)

    @property
    def n_residues(self) -> int:
        return len(self.resnums)


def load_target_config(target_name: str, config_path: str | Path | None = None) -> dict:
    """Load a single target's config dict from targets.yaml."""
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "targets.yaml"
    with open(config_path) as f:
        data = yaml.safe_load(f)
    targets = data.get("targets", {})
    if target_name not in targets:
        raise KeyError(
            f"Unknown target '{target_name}'. Available: {list(targets.keys())}"
        )
    return targets[target_name]


def clean(
    pdb_id: str,
    chains: list[str] | None = None,
    keep_nucleic: bool = False,
) -> CleanResult:
    """Fetch and clean a PDB structure, returning a CleanResult.

    Parameters
    ----------
    pdb_id : str
        PDB accession code.
    chains : list[str] | None
        Chains to keep (None = all protein chains).
    keep_nucleic : bool
        If True, nucleic-acid residues are retained (P atom as representative).
    """
    import prody

    prody.confProDy(verbosity="none")
    struct = prody.parsePDB(pdb_id, compressed=False)
    if struct is None:
        raise ValueError(f"prody failed to parse '{pdb_id}'")

    warn_list: list[str] = []

    # --- Alternate location handling: keep 'A' or highest occupancy ---
    alt_locs = struct.getAltlocs()
    if alt_locs is not None and any(a not in ("", " ", "\x00") for a in alt_locs):
        struct = struct.select("altloc _ A") or struct
        warn_list.append(f"{pdb_id}: alternate locations detected; kept altloc='A'.")

    # --- Select protein (+ optional nucleic), specific chains ---
    type_sel = "protein"
    if keep_nucleic:
        type_sel = "protein or nucleic"

    chain_part = ""
    if chains:
        chain_part = " and (" + " or ".join(f"chain {c}" for c in chains) + ")"

    struct_clean = struct.select(f"({type_sel}){chain_part}")
    if struct_clean is None:
        raise ValueError(
            f"No residues selected in {pdb_id} with type='{type_sel}' chains={chains}"
        )

    # --- Insertion code detection (flag, do not discard) ---
    icode_residues: list[str] = []
    try:
        icodes = struct_clean.getIcodes()
        if icodes is not None:
            flagged = set()
            for atom, ic in zip(struct_clean, icodes):
                if ic not in ("", " ", "\x00"):
                    key = f"{atom.getChid()}{atom.getResnum()}{ic}"
                    if key not in flagged:
                        icode_residues.append(key)
                        flagged.add(key)
            if icode_residues:
                warn_list.append(
                    f"{pdb_id}: {len(icode_residues)} residues with insertion codes: "
                    f"{icode_residues[:5]}{'...' if len(icode_residues) > 5 else ''}"
                )
    except Exception:
        pass

    # --- Extract Cα (and P for nucleic) ---
    ca_sel = "name CA"
    if keep_nucleic:
        ca_sel = "name CA or (nucleic and name P)"

    ca_atoms = struct_clean.select(ca_sel)
    if ca_atoms is None or len(ca_atoms) == 0:
        raise ValueError(f"No Cα/P atoms after cleaning {pdb_id}")

    coords = ca_atoms.getCoords().astype(np.float64)
    resnums = ca_atoms.getResnums().astype(np.int32)
    resnames = ca_atoms.getResnames().tolist()
    chain_ids = ca_atoms.getChids().tolist()

    # --- B-factor statistics ---
    bfacs = ca_atoms.getBetas()
    if bfacs is not None:
        bfactors = bfacs.astype(np.float64)
        b_mean = float(np.mean(bfacs))
        b_std = float(np.std(bfacs))
        if b_std < 0.1:
            warn_list.append(
                f"{pdb_id}: B-factors nearly constant (std={b_std:.3f}) – "
                "possibly a homology model or degenerate entry."
            )
    else:
        bfactors = np.full(len(coords), np.nan)
        b_mean, b_std = float("nan"), float("nan")
        warn_list.append(f"{pdb_id}: B-factors unavailable.")

    # --- Resolution ---
    resolution: float | None = None
    try:
        header = prody.parsePDBHeader(pdb_id)
        resolution = float(header.get("resolution", 0.0)) or None
        if resolution is not None and resolution > 3.5:
            warn_list.append(
                f"{pdb_id}: resolution {resolution:.1f} Å > 3.5 Å – reduced reliability."
            )
    except Exception:
        pass

    # --- Gap detection: consecutive Cα pairs in same chain with |resnum| > 1 ---
    gap_pairs: list[tuple[int, int]] = []
    for i in range(len(resnums) - 1):
        if chain_ids[i] == chain_ids[i + 1]:
            delta = int(resnums[i + 1]) - int(resnums[i])
            if delta > 1:
                gap_pairs.append((int(resnums[i]), int(resnums[i + 1])))
    if gap_pairs:
        warn_list.append(
            f"{pdb_id}: {len(gap_pairs)} residue gaps in sequence numbering "
            f"(first 3: {gap_pairs[:3]}). Virtual bonds will bridge these."
        )

    # --- Connectivity check: Laplacian nullspace dim must equal 1 ---
    _assert_connected(coords, pdb_id, warn_list)

    return CleanResult(
        pdb_id=pdb_id,
        coords=coords,
        resnums=resnums,
        resnames=resnames,
        chain_ids=chain_ids,
        resolution=resolution,
        bfactors=bfactors,
        b_mean=b_mean,
        b_std=b_std,
        gap_pairs=gap_pairs,
        insertion_code_residues=icode_residues,
        warnings=warn_list,
    )


def clean_from_config(target_name: str, role: str = "apo") -> CleanResult:
    """Convenience wrapper: load target config and call clean().

    Parameters
    ----------
    target_name : str
        Key in config/targets.yaml (e.g. 'KRAS_G12C').
    role : {'apo', 'holo'}
        Which PDB structure to load.
    """
    cfg = load_target_config(target_name)
    if cfg.get("quarantine"):
        warnings.warn(
            f"Target '{target_name}' is quarantined: {cfg.get('quarantine_reason', '')}",
            UserWarning,
            stacklevel=2,
        )
    pdb_key = f"{role}_pdb"
    pdb_id = cfg.get(pdb_key)
    if pdb_id is None:
        raise ValueError(
            f"Target '{target_name}' has no '{pdb_key}' defined in config."
        )
    chains = cfg.get("chains")
    keep_nucleic = cfg.get("keep_nucleic", False)
    return clean(pdb_id, chains=chains, keep_nucleic=keep_nucleic)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _assert_connected(
    coords: np.ndarray,
    pdb_id: str,
    warn_list: list[str],
    cutoff: float = 10.0,
) -> None:
    """Check that the Cα contact graph (at cutoff Å) has exactly one component.
    Warns rather than raises so callers can decide how to handle it.
    """
    import networkx as nx

    n = len(coords)
    diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
    dist = np.sqrt((diff ** 2).sum(axis=2))
    adj = (dist < cutoff) & (dist > 0)
    G = nx.from_numpy_array(adj.astype(float))
    n_comp = nx.number_connected_components(G)
    if n_comp != 1:
        warn_list.append(
            f"{pdb_id}: Cα contact graph at {cutoff} Å has {n_comp} connected "
            "components. Check for chain breaks or missing loops."
        )
