#!/usr/bin/env python3
"""TASK-0208 -- decompose the real apo->holo structural change into
backbone (phi/psi) vs. side-chain (chi1-4) components, and measure whether
the required side-chain changes are decomposable (each individually
favourable on the apo background) or frustrated (only jointly favourable).

Gate thresholds are pre-registered in the task file
(.ai/tasks/IN_PROGRESS/TASK-0208-*.md, "Pre-Registered Gate" section,
written before this script ran). This script only measures; it does not
search, sample, or optimize -- two already-deposited structures per target.

Reuses `superpose.kabsch_fit`/`kabsch_apply`/`align_apo_holo` for both the
whole-structure alignment (canceling the arbitrary crystallographic frame
difference) and the per-residue local side-chain transplant (a 3-point
N/CA/C rigid fit -- the standard homology-modeling side-chain-graft
technique: fitting a residue's own N/CA/C frame preserves all its chi
dihedrals, which are defined relative to that same local frame, under any
rigid transform). No new alignment code, per the task's own In-Scope bullet.

Reuses `_run_evoef2`'s vendored-binary invocation conventions from
`task0204_rotamer_repack_baseline.py` (relative "./EvoEF2" argv[0],
cwd=EVOEF2_DIR) for the ComputeStability energy calls, but not that
function itself -- ComputeStability takes no --design_chains and writes no
`_beststruct.pdb` (confirmed directly: `ls -t *.txt` after a live
ComputeStability run shows no new file, only a stdout `Total = ...` energy
breakdown), so it needs its own thin wrapper.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
_SCRIPTS = Path(__file__).resolve().parent
for _p in (_SRC, _SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.labels import build_labels, ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue  # noqa: E402
from allostery.superpose import align_apo_holo, chain_map_from_config, kabsch_apply, kabsch_fit  # noqa: E402

EVOEF2_DIR = Path(__file__).resolve().parent.parent / "tools" / "evoef2"
EVOEF2_BIN = EVOEF2_DIR / "EvoEF2"

WINDOW_MAX_SIZE = 12  # PHASE_B_ROTAMER_QUBO.md's own m=8-15 window size, TASK-0204's own constant, reused not re-picked
MANDATORY_TARGETS = ["KRAS_G12C", "PTP1B", "CASPASE1"]
EXTEND_IF_CHEAP = ["GLUCOKINASE", "CASPASE7"]

# Backbone-attribution gate (pre-registered)
SIDE_CHAIN_DOMINANT_HIGH = 0.70
BACKBONE_SUBSTANTIAL = 0.50

# Coupling/frustration gate (pre-registered)
FRUSTRATION_BAND = 0.30

BACKBONE_ATOMS = ("N", "CA", "C")

# Standard chi1-4 atom definitions (Lovell et al. 2000 / Dunbrack convention).
# ALA/GLY have no side-chain dihedral.
CHI_ATOMS: dict[str, list[tuple[str, str, str, str]]] = {
    "ARG": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "CD"), ("CB", "CG", "CD", "NE"), ("CG", "CD", "NE", "CZ")],
    "ASN": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "OD1")],
    "ASP": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "OD1")],
    "CYS": [("N", "CA", "CB", "SG")],
    "GLN": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "CD"), ("CB", "CG", "CD", "OE1")],
    "GLU": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "CD"), ("CB", "CG", "CD", "OE1")],
    "HIS": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "ND1")],
    "ILE": [("N", "CA", "CB", "CG1"), ("CA", "CB", "CG1", "CD1")],
    "LEU": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "CD1")],
    "LYS": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "CD"), ("CB", "CG", "CD", "CE"), ("CG", "CD", "CE", "NZ")],
    "MET": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "SD"), ("CB", "CG", "SD", "CE")],
    "PHE": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "CD1")],
    "PRO": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "CD")],
    "SER": [("N", "CA", "CB", "OG")],
    "THR": [("N", "CA", "CB", "OG1")],
    "TRP": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "CD1")],
    "TYR": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "CD1")],
    "VAL": [("N", "CA", "CB", "CG1")],
}


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Full-atom structure loading (per-residue atom-name dicts)
# ---------------------------------------------------------------------------

def _load_full_atom(pdb_id: str, chains: list[str]) -> "tuple[dict, dict]":
    """Returns (residues, hierview_source) where `residues` maps
    (chain, resnum) -> {"resname": str, "atoms": {name: xyz}}. Same
    altloc/protein/chain filtering as `task0204_rotamer_repack_baseline.py
    ::_write_full_atom_with_window_chain`, kept as whole chains (not just a
    window) so phi/psi have real neighbor context."""
    import prody

    prody.confProDy(verbosity="none")
    struct = prody.parsePDB(pdb_id, compressed=False)
    alt_locs = struct.getAltlocs()
    if alt_locs is not None and any(a not in ("", " ", "\x00") for a in alt_locs):
        struct = struct.select("altloc _ A") or struct
    chain_part = " and (" + " or ".join(f"chain {c}" for c in chains) + ")"
    struct_clean = struct.select(f"protein{chain_part}").copy()

    residues: dict = {}
    chids = struct_clean.getChids()
    resnums = struct_clean.getResnums()
    resnames = struct_clean.getResnames()
    names = struct_clean.getNames()
    coords = struct_clean.getCoords()
    for i in range(len(names)):
        key = (str(chids[i]), int(resnums[i]))
        entry = residues.setdefault(key, {"resname": str(resnames[i]), "atoms": {}})
        entry["atoms"][str(names[i])] = coords[i]
    return residues, struct_clean


# ---------------------------------------------------------------------------
# Dihedral extraction
# ---------------------------------------------------------------------------

def _dihedral(a, b, c, d) -> float:
    # prody.calcDihedral requires Atomic instances (checked directly via its
    # source -- it type-checks then delegates to the plain-coordinate
    # `getDihedral`); this module only has raw xyz per named atom (from the
    # (chain,resnum)->{name:xyz} dicts, not prody Atom objects), so call the
    # coordinate-level function directly instead of wrapping each lookup in
    # a throwaway Atom selection.
    from prody.measure.measure import getDihedral

    a, b, c, d = (np.asarray(p, dtype=float).reshape(1, 3) for p in (a, b, c, d))
    return float(getDihedral(a, b, c, d))


def backbone_dihedrals(chain_residues: dict, chain: str, resnum: int) -> "tuple[float, float]":
    """(phi, psi) in degrees, NaN if the neighbor residue is missing
    (chain terminus or a numbering gap)."""
    prev_r = chain_residues.get((chain, resnum - 1))
    this_r = chain_residues.get((chain, resnum))
    next_r = chain_residues.get((chain, resnum + 1))
    if this_r is None:
        return float("nan"), float("nan")
    atoms = this_r["atoms"]
    phi = float("nan")
    if prev_r is not None and "C" in prev_r["atoms"] and all(n in atoms for n in ("N", "CA", "C")):
        phi = _dihedral(prev_r["atoms"]["C"], atoms["N"], atoms["CA"], atoms["C"])
    psi = float("nan")
    if next_r is not None and "N" in next_r["atoms"] and all(n in atoms for n in ("N", "CA", "C")):
        psi = _dihedral(atoms["N"], atoms["CA"], atoms["C"], next_r["atoms"]["N"])
    return phi, psi


def chi_dihedrals(resname: str, atoms: dict) -> list:
    """List of chi angles (degrees) for `resname`, NaN for any chi whose
    atoms aren't all present (missing side-chain density)."""
    defs = CHI_ATOMS.get(resname, [])
    out = []
    for quad in defs:
        if all(n in atoms for n in quad):
            out.append(_dihedral(*(atoms[n] for n in quad)))
        else:
            out.append(float("nan"))
    return out


def _angle_diff(a: float, b: float) -> float:
    """Minimum-image difference between two angles in degrees, NaN-safe."""
    if not (np.isfinite(a) and np.isfinite(b)):
        return float("nan")
    d = (a - b + 180.0) % 360.0 - 180.0
    return float(d)


# ---------------------------------------------------------------------------
# Side-chain transplant (local N/CA/C Kabsch fit)
# ---------------------------------------------------------------------------

def local_transplant(donor_atoms: dict, acceptor_atoms: dict) -> "dict | None":
    """Rigid-fits donor's own N/CA/C onto acceptor's N/CA/C, applies that
    transform to donor's side-chain atoms, keeps acceptor's own backbone
    (N/CA/C/O) unchanged. Preserves donor's chi angles exactly (they are
    defined relative to the same local N-CA-C frame the fit matches) while
    placing the side chain on acceptor's own backbone position/orientation
    -- the standard side-chain-graft technique. Returns None if either
    side lacks a full N/CA/C frame."""
    if not all(n in donor_atoms for n in BACKBONE_ATOMS) or not all(n in acceptor_atoms for n in BACKBONE_ATOMS):
        return None
    donor_bb = np.array([donor_atoms[n] for n in BACKBONE_ATOMS])
    acceptor_bb = np.array([acceptor_atoms[n] for n in BACKBONE_ATOMS])
    R, mc, rc = kabsch_fit(donor_bb, acceptor_bb)
    hybrid = {}
    for n in ("N", "CA", "C", "O"):
        if n in acceptor_atoms:
            hybrid[n] = acceptor_atoms[n]
    for n, xyz in donor_atoms.items():
        if n in ("N", "CA", "C"):
            continue
        hybrid[n] = kabsch_apply(xyz.reshape(1, 3), R, mc, rc)[0]
    return hybrid


def displacement_rmsd(struct_a: dict, struct_b: dict, keys, atom_filter=None) -> float:
    """RMSD over named-atom pairs present in both structures at `keys`.
    `atom_filter`, if given, restricts to atom names in that set (used for
    the Ca-only cross-check below -- Q-0001/A1)."""
    diffs = []
    for key in keys:
        a_atoms = struct_a.get(key, {}).get("atoms", struct_a.get(key, {}))
        b_atoms = struct_b.get(key, {}).get("atoms", struct_b.get(key, {}))
        for name, xyz in a_atoms.items():
            if atom_filter is not None and name not in atom_filter:
                continue
            if name in b_atoms:
                diffs.append(xyz - b_atoms[name])
    if not diffs:
        return float("nan")
    diffs = np.array(diffs)
    return float(np.sqrt((diffs ** 2).sum(axis=1).mean()))


# ---------------------------------------------------------------------------
# EvoEF2 ComputeStability wrapper
# ---------------------------------------------------------------------------

_TOTAL_RE = re.compile(r"^Total\s*=\s*([-\d.]+)", re.MULTILINE)


def compute_stability_total(pdb_path: Path):
    if not EVOEF2_BIN.exists():
        return {"error": f"EvoEF2 binary not found at {EVOEF2_BIN}"}
    local_pdb = EVOEF2_DIR / pdb_path.name
    local_pdb.write_bytes(pdb_path.read_bytes())
    result = subprocess.run(
        [f"./{EVOEF2_BIN.name}", "--command=ComputeStability", f"--pdb={local_pdb.name}"],
        cwd=EVOEF2_DIR, capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        return {"error": f"ComputeStability exited {result.returncode}: {result.stderr.strip()[:500]}"}
    m = _TOTAL_RE.search(result.stdout)
    if not m:
        return {"error": "no 'Total = ...' line in ComputeStability stdout"}
    return float(m.group(1))


def write_hybrid_pdb(apo_struct_ag, apo_chids, apo_resnums, apo_names, key_to_atoms: dict, out_path: Path) -> None:
    """Writes `apo_struct_ag` with the atoms named in `key_to_atoms`
    (per (chain, resnum) -> {name: xyz}) overwritten -- everything else
    kept at apo's own native coordinates."""
    import prody

    hybrid = apo_struct_ag.copy()
    coords = hybrid.getCoords()
    for (chain, resnum), atoms in key_to_atoms.items():
        mask = (apo_chids == chain) & (apo_resnums == resnum)
        idxs = np.where(mask)[0]
        for i in idxs:
            nm = apo_names[i]
            if nm in atoms:
                coords[i] = atoms[nm]
    hybrid.setCoords(coords)
    prody.writePDB(str(out_path), hybrid)


# ---------------------------------------------------------------------------
# Per-target pipeline
# ---------------------------------------------------------------------------

def run_target(target_name: str) -> dict:
    _log(f"=== {target_name} ===")
    target_config = load_target_config(target_name)
    apo_ca = clean_from_config(target_name, role="apo")
    holo_ca = clean_from_config(target_name, role="holo")
    chain_map = chain_map_from_config(target_config)

    # build_labels needs holo.ligand_groups/.heavy_atom_coords -- clean_from_config
    # only builds Ca coords, so attach them here (same recipe as
    # task0204_rotamer_repack_baseline.py::_load_apo_holo).
    import prody as _prody

    _prody.confProDy(verbosity="none")
    _holo_chains_for_labels = target_config.get("holo_chains") or target_config.get("chains") or sorted(set(holo_ca.chain_ids))
    _holo_struct = _prody.parsePDB(target_config["holo_pdb"], compressed=False).select(
        " or ".join(f"chain {c}" for c in _holo_chains_for_labels)
    )
    holo_ca.ligand_groups = ligand_groups_from_atomgroup(_holo_struct)
    holo_ca.heavy_atom_coords, holo_ca.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
        _holo_struct, _holo_chains_for_labels, holo_ca.resnums
    )

    alignment = align_apo_holo(apo_ca, holo_ca, chain_map=chain_map)

    apo_chains = target_config.get("apo_chains") or target_config.get("chains") or sorted(set(apo_ca.chain_ids))
    holo_chains = target_config.get("holo_chains") or target_config.get("chains") or sorted(set(holo_ca.chain_ids))

    apo_res, apo_ag = _load_full_atom(target_config["apo_pdb"], apo_chains)
    holo_res, holo_ag = _load_full_atom(target_config["holo_pdb"], holo_chains)

    # Align holo's full-atom coordinates into apo's frame (cancels the
    # arbitrary crystallographic origin/orientation difference -- the same
    # transform `align_apo_holo` already computed from the CA correspondence).
    holo_res_aligned = {}
    for key, entry in holo_res.items():
        aligned_atoms = {
            n: kabsch_apply(xyz.reshape(1, 3), alignment.R, alignment.mobile_centroid, alignment.ref_centroid)[0]
            for n, xyz in entry["atoms"].items()
        }
        holo_res_aligned[key] = {"resname": entry["resname"], "atoms": aligned_atoms}

    # Common (apo_chain, resnum) keys, holo chain letter remapped via chain_map.
    inv_map = {v: k for k, v in (chain_map or {}).items()}  # apo_chain -> holo_chain
    common_keys = []
    for (a_chain, resnum) in apo_res:
        h_chain = inv_map.get(a_chain, a_chain)
        if (h_chain, resnum) in holo_res_aligned:
            common_keys.append((a_chain, resnum, h_chain))
    _log(f"{len(common_keys)} common (chain, resnum) residues, full-atom")

    # Pocket window (reuses build_labels, this register's own pocket definition)
    labels = build_labels(apo_ca, holo_ca, target_config)
    if labels.pocket is None:
        return {"target": target_name, "error": "no resolvable pocket label (drug_ligand not found)"}
    pocket_idx = np.where(labels.pocket)[0]
    apo_chain_arr = np.asarray(apo_ca.chain_ids)
    pocket_keys_all = [(str(apo_chain_arr[i]), int(apo_ca.resnums[i])) for i in pocket_idx]
    common_apo_keys = {(a, r) for (a, r, h) in common_keys}
    pocket_keys = [k for k in pocket_keys_all if k in common_apo_keys]
    if len(pocket_keys) > WINDOW_MAX_SIZE:
        centroid = np.array([apo_res[k]["atoms"]["CA"] for k in pocket_keys]).mean(axis=0)
        d = np.array([np.linalg.norm(apo_res[k]["atoms"]["CA"] - centroid) for k in pocket_keys])
        pocket_keys = [pocket_keys[i] for i in np.argsort(d)[:WINDOW_MAX_SIZE]]
    _log(f"pocket window: {len(pocket_keys)} residues")

    # Distal control: same count, common-set residues farthest from pocket centroid.
    pocket_centroid = np.array([apo_res[k]["atoms"]["CA"] for k in pocket_keys]).mean(axis=0)
    non_pocket_common = [k for k in common_apo_keys if k not in set(pocket_keys) and "CA" in apo_res[k]["atoms"]]
    dists = np.array([np.linalg.norm(apo_res[k]["atoms"]["CA"] - pocket_centroid) for k in non_pocket_common])
    order = np.argsort(dists)[::-1]
    distal_keys = [non_pocket_common[i] for i in order[: len(pocket_keys)]]
    _log(f"distal control: {len(distal_keys)} residues")

    apo_to_holo_key = {(a, r): (h, r) for (a, r, h) in common_keys}

    def region_dihedral_change(keys):
        bb_deltas, chi_deltas = [], []
        for key in keys:
            a_chain, resnum = key
            h_chain, _ = apo_to_holo_key[key]
            a_phi, a_psi = backbone_dihedrals(apo_res, a_chain, resnum)
            h_phi, h_psi = backbone_dihedrals(holo_res, h_chain, resnum)
            d_phi = abs(_angle_diff(a_phi, h_phi))
            d_psi = abs(_angle_diff(a_psi, h_psi))
            if np.isfinite(d_phi) or np.isfinite(d_psi):
                bb_deltas.append(np.nansum([d_phi, d_psi]))

            resname_a = apo_res[key]["resname"]
            a_chi = chi_dihedrals(resname_a, apo_res[key]["atoms"])
            h_chi = chi_dihedrals(resname_a, holo_res[(h_chain, resnum)]["atoms"]) if resname_a == holo_res.get((h_chain, resnum), {}).get("resname") else []
            if a_chi and h_chi:
                d_chi = [abs(_angle_diff(x, y)) for x, y in zip(a_chi, h_chi)]
                if any(np.isfinite(d) for d in d_chi):
                    chi_deltas.append(np.nansum(d_chi))
        return {
            "mean_backbone_change_deg": float(np.mean(bb_deltas)) if bb_deltas else float("nan"),
            "mean_chi_change_deg": float(np.mean(chi_deltas)) if chi_deltas else float("nan"),
            "n": len(keys),
        }

    dihedral_pocket = region_dihedral_change(pocket_keys)
    dihedral_distal = region_dihedral_change(distal_keys)
    _log(f"dihedral change -- pocket: {dihedral_pocket}, distal: {dihedral_distal}")

    # --- Backbone/side-chain attribution (reconstruction) --------------
    window_apo_keys = pocket_keys
    window_holo_keys_aligned = {k: apo_to_holo_key[k] for k in window_apo_keys}

    resname_mismatch = [
        k for k in window_apo_keys
        if apo_res[k]["resname"] != holo_res_aligned[window_holo_keys_aligned[k]]["resname"]
    ]
    if resname_mismatch:
        _log(f"WARNING: {len(resname_mismatch)} window residues have apo/holo resname mismatch, excluded: {resname_mismatch}")
    window_apo_keys = [k for k in window_apo_keys if k not in resname_mismatch]

    true_holo_dict = {k: holo_res_aligned[window_holo_keys_aligned[k]] for k in window_apo_keys}
    apo_dict = {k: apo_res[k] for k in window_apo_keys}

    rmsd_apo_to_holo = displacement_rmsd(apo_dict, true_holo_dict, window_apo_keys)

    # Q-0001/A1 (Reviewer thread, answered in this task's Done section):
    # side-chain rotamer changes cannot move Ca -- Ca position is set
    # entirely by backbone geometry (phi/psi + bond geometry), never by any
    # chi torsion. So pocket-local Ca displacement above coordinate noise
    # is a *necessary*, model-independent proof of backbone change,
    # independent of the chi-reconstruction numbers above -- a structural
    # identity, not a heuristic. Must stay pocket-local (a global RMSD
    # averages a hinge away, per [[TASK-0169]]'s own prior mistake) --
    # computed on the same pocket window and reported against the same
    # window's distal control below, never against a whole-structure RMSD.
    ca_rmsd_pocket = displacement_rmsd(apo_dict, true_holo_dict, window_apo_keys, atom_filter={"CA"})
    distal_apo_dict = {k: apo_res[k] for k in distal_keys if k in apo_to_holo_key}
    distal_true_holo_dict = {k: holo_res_aligned[apo_to_holo_key[k]] for k in distal_apo_dict}
    ca_rmsd_distal = displacement_rmsd(distal_apo_dict, distal_true_holo_dict, list(distal_apo_dict))
    _log(f"Ca-only cross-check (Q-0001/A1): pocket Ca RMSD={ca_rmsd_pocket:.3f} A "
         f"(vs. pocket heavy-atom RMSD={rmsd_apo_to_holo:.3f} A), distal Ca RMSD={ca_rmsd_distal:.3f} A")

    # (ii) apo backbone + holo chi
    hybrid_ii = {}
    for k in window_apo_keys:
        t = local_transplant(donor_atoms=true_holo_dict[k]["atoms"], acceptor_atoms=apo_dict[k]["atoms"])
        if t is not None:
            hybrid_ii[k] = {"atoms": t}
    rmsd_ii = displacement_rmsd(hybrid_ii, true_holo_dict, window_apo_keys)
    side_chain_explained = 1.0 - rmsd_ii / rmsd_apo_to_holo if rmsd_apo_to_holo > 1e-9 else float("nan")

    # (i) holo backbone + apo chi
    hybrid_i = {}
    for k in window_apo_keys:
        t = local_transplant(donor_atoms=apo_dict[k]["atoms"], acceptor_atoms=true_holo_dict[k]["atoms"])
        if t is not None:
            hybrid_i[k] = {"atoms": t}
    rmsd_i = displacement_rmsd(hybrid_i, true_holo_dict, window_apo_keys)
    backbone_explained = 1.0 - rmsd_i / rmsd_apo_to_holo if rmsd_apo_to_holo > 1e-9 else float("nan")

    _log(f"RMSD apo->holo: {rmsd_apo_to_holo:.3f} A; (ii) apo-bb+holo-chi RMSD: {rmsd_ii:.3f} A (side_chain_explained={side_chain_explained:.3f}); "
         f"(i) holo-bb+apo-chi RMSD: {rmsd_i:.3f} A (backbone_explained={backbone_explained:.3f})")

    reconstruction_valid = (
        np.isfinite(rmsd_apo_to_holo) and rmsd_apo_to_holo > 1e-9
        and rmsd_i <= rmsd_apo_to_holo * 1.5 and rmsd_ii <= rmsd_apo_to_holo * 1.5
        and not (rmsd_ii <= 1e-6 and rmsd_i >= rmsd_apo_to_holo * 0.9)
        and not (rmsd_i <= 1e-6 and rmsd_ii >= rmsd_apo_to_holo * 0.9)
    )

    # Correction to the pre-registered formula (task file, "Pre-Registered
    # Gate" section, Correction note): the original prose's second clause
    # ("... OR side_chain_explained < 0.70") is not mutually exclusive with
    # "neither reconstruction is dominant" -- found on GLUCOKINASE
    # (side_chain_explained=0.46, backbone_explained=0.20: neither >= its
    # own bar, yet the literal OR clause still forced "substantially_
    # backbone"). Does not change any mandatory-target verdict (KRAS_G12C/
    # PTP1B/CASPASE1 all clear backbone_explained >= 0.50 directly).
    if side_chain_explained >= SIDE_CHAIN_DOMINANT_HIGH and backbone_explained < BACKBONE_SUBSTANTIAL:
        attribution_verdict = "side_chain_dominant"
    elif backbone_explained >= BACKBONE_SUBSTANTIAL:
        attribution_verdict = "substantially_backbone"
    else:
        attribution_verdict = "ambiguous"

    # --- Coupling/frustration statistic (EvoEF2), pocket window only ---
    apo_ag_chids = apo_ag.getChids()
    apo_ag_resnums = apo_ag.getResnums()
    apo_ag_names = apo_ag.getNames()

    coupling_result: dict = {"attempted": False}
    if EVOEF2_BIN.exists() and window_apo_keys:
        work_dir = EVOEF2_DIR
        baseline_path = work_dir / f"{target_name.lower()}_t208_apo_baseline.pdb"
        import prody
        prody.writePDB(str(baseline_path), apo_ag)
        e_baseline = compute_stability_total(baseline_path)

        singles = {}
        if not isinstance(e_baseline, dict):
            for k in window_apo_keys:
                if k not in hybrid_ii:
                    continue
                out_path = work_dir / f"{target_name.lower()}_t208_single_{k[0]}{k[1]}.pdb"
                write_hybrid_pdb(apo_ag, apo_ag_chids, apo_ag_resnums, apo_ag_names, {k: hybrid_ii[k]["atoms"]}, out_path)
                e = compute_stability_total(out_path)
                singles[f"{k[0]}{k[1]}"] = (e - e_baseline) if not isinstance(e, dict) else e

            joint_atoms = {k: hybrid_ii[k]["atoms"] for k in window_apo_keys if k in hybrid_ii}
            joint_path = work_dir / f"{target_name.lower()}_t208_joint.pdb"
            write_hybrid_pdb(apo_ag, apo_ag_chids, apo_ag_resnums, apo_ag_names, joint_atoms, joint_path)
            e_joint = compute_stability_total(joint_path)
            delta_joint = (e_joint - e_baseline) if not isinstance(e_joint, dict) else e_joint

            valid_singles = [v for v in singles.values() if isinstance(v, (int, float))]
            sum_singles = float(np.sum(valid_singles)) if valid_singles else float("nan")

            if not isinstance(delta_joint, (int, float)) or not np.isfinite(sum_singles):
                coupling_result = {"attempted": True, "error": "EvoEF2 energy call failed", "singles": singles, "joint": delta_joint}
            elif abs(sum_singles) < 1e-6:
                coupling_result = {
                    "attempted": True, "verdict": "not_evaluable", "sum_singles": sum_singles,
                    "joint": delta_joint, "singles": singles,
                }
            else:
                gap = sum_singles - delta_joint
                frustrated = gap >= FRUSTRATION_BAND * abs(sum_singles)
                any_unfavorable_single = any(v > 0 for v in valid_singles)
                coupling_result = {
                    "attempted": True,
                    "sum_singles": sum_singles,
                    "joint": delta_joint,
                    "gap": gap,
                    "frustrated": bool(frustrated),
                    "any_individually_unfavorable_single": bool(any_unfavorable_single),
                    "strong_frustration_signature": bool(frustrated and any_unfavorable_single),
                    "singles": singles,
                }
            _log(f"coupling: sum_singles={sum_singles}, joint={delta_joint}, result={coupling_result.get('verdict', coupling_result.get('frustrated'))}")
    else:
        coupling_result = {"attempted": False, "reason": "EvoEF2 binary missing or empty window"}

    gate_open = (
        attribution_verdict == "substantially_backbone"
        and coupling_result.get("frustrated") is True
    )
    gate_verdict = "OPEN" if gate_open else "CLOSED"
    if not reconstruction_valid:
        gate_verdict = "not_evaluable"

    return {
        "target": target_name,
        "n_common_residues": len(common_keys),
        "pocket_window": [f"{c}{r}" for c, r in pocket_keys],
        "distal_control": [f"{c}{r}" for c, r in distal_keys],
        "dihedral_change_pocket": dihedral_pocket,
        "dihedral_change_distal": dihedral_distal,
        "rmsd_apo_to_holo": rmsd_apo_to_holo,
        "ca_rmsd_pocket": ca_rmsd_pocket,
        "ca_rmsd_distal": ca_rmsd_distal,
        "rmsd_apo_backbone_holo_chi": rmsd_ii,
        "rmsd_holo_backbone_apo_chi": rmsd_i,
        "side_chain_explained": side_chain_explained,
        "backbone_explained": backbone_explained,
        "attribution_verdict": attribution_verdict,
        "reconstruction_valid": reconstruction_valid,
        "resname_mismatches_excluded": [f"{c}{r}" for c, r in resname_mismatch],
        "coupling": coupling_result,
        "gate_verdict": gate_verdict,
    }


def main():
    targets = MANDATORY_TARGETS + EXTEND_IF_CHEAP
    if len(sys.argv) > 1:
        targets = sys.argv[1:]
    results = []
    for t in targets:
        try:
            r = run_target(t)
        except Exception as exc:  # noqa: BLE001
            _log(f"{t} FAILED: {exc!r}")
            r = {"target": t, "error": repr(exc)}
        results.append(r)
        out_dir = Path(__file__).resolve().parent.parent / "results_task0208_apo_holo_decomposition"
        out_dir.mkdir(exist_ok=True)
        (out_dir / "results.json").write_text(json.dumps(results, indent=2, default=str))
    _log("done")
    for r in results:
        _log(f"{r.get('target')}: gate_verdict={r.get('gate_verdict', r.get('error'))}")


if __name__ == "__main__":
    main()
