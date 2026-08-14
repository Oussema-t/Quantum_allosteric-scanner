"""TASK-0177 -- consensus holo-pocket ground truth.

Replaces the single-cutoff ligand-contact label (`labels.holo_pocket_mask`,
one HET group, one 4.5 A cutoff) with a **consensus** built from several
*mutually independent* routes to the same residue set, so the label's own
uncertainty is reported instead of silently assumed away.

Criteria (see TASK-0177's Context table for the full rationale):

  C1  Ligand heavy-atom contact, swept 3.5-6.0 A            (labels.py, incumbent)
  C2  Delta-SASA on ligand removal (Shrake-Rupley/freesasa)  (independent of C1's cutoff)
  C3  Geometric cavity in holo, ligand stripped (fpocket)    (independent of ligand identity)
  C4  Depositor/software SITE records (legacy PDB REMARK 800/SITE)  (independent of all computation)
  C5  Crypticity: apo vs. holo cavity volume ratio (fpocket) (target-level qualifier)
  C6  Distality: Euclidean + spatial-hop + chain-hop to active site (target-level qualifier)

**Consensus** = residues satisfying >=3 of {C1(any cutoff), C2, C3, C4}.
**Core** = residues satisfying *all* of {C1, C2, C3, C4} available.
**Shell** = symmetric difference (consensus XOR core is not quite it -- shell
is "flagged by >=1 but not all", see `assemble_consensus`).
**Resolution** = |shell| / |core| (inf if core is empty -- reported, not
divided-by-zero silently).

Every per-residue criterion mask is computed on APO numbering (mapped via
the same `labels._needleman_wunsch_map` sequence-alignment path C1 already
uses, or `superpose.chain_map_from_config` where a target has a per-role
chain-letter override, TASK-0144) and has `active_site`/`terminal` excluded
before consensus assembly -- same SEAM-0003 invariant `build_labels`
already enforces, so `core`/`consensus`/`shell` never re-admit the active
site through a criterion that doesn't happen to route through
`build_labels` itself.

`frozen_context` per this task's own Constraint: nothing in this module
reads any score, floor, AUC, or observable output. It is pure structural
geometry over apo/holo coordinates and external, non-computed annotations.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from .labels import (
    _THREE_TO_ONE,
    _needleman_wunsch_map,
    _sequence,
    functional_indices,
    holo_pocket_mask,
    terminal_mask,
)
from .superpose import chain_map_from_config

FPOCKET_BIN = Path(__file__).resolve().parent.parent.parent / "tools" / "fpocket" / "bin" / "fpocket"
C1_CUTOFFS = (3.5, 4.0, 4.5, 5.0, 5.5, 6.0)
HOP_CUTOFF = 8.0  # TASK-0067's retained contact-graph scale -- reused, not reinvented.
DSASA_THRESHOLD_A2 = 1.0  # burial floor for C2 -- any measurable burial counts, not tuned.


@dataclass
class CriterionResult:
    name: str
    mask: Optional[np.ndarray]  # (N,) bool on APO numbering; None if unavailable
    available: bool
    detail: dict = field(default_factory=dict)


@dataclass
class ConsensusLabel:
    target: str
    core: Optional[np.ndarray]
    consensus: Optional[np.ndarray]
    shell: Optional[np.ndarray]
    active_site: np.ndarray
    terminal: np.ndarray
    criteria: Dict[str, CriterionResult]
    resolution: float  # |shell| / |core|, inf if core empty, nan if consensus itself empty
    task_validity: dict
    incumbent: Optional[np.ndarray]  # labels.build_labels-equivalent, 4.5 A only -- for continuity


# ---------------------------------------------------------------------------
# Shared holo-fetch helper (ported, not imported, from run_challenge.py's own
# `_load_apo_holo` -- TASK-0186's script made the same choice for the same
# reason: this recipe is a script/module-local convenience, not core library
# surface, and the two existing copies already accept the duplication).
# ---------------------------------------------------------------------------

def load_apo_holo_full(target_name: str, target_config: dict):
    """Fetch+clean apo/holo and attach holo's ligand_groups/heavy-atom data,
    plus the *raw* prody structures (needed here for C2/C3/C4/C5, which all
    need full-atom or whole-entry access `clean()`'s Ca-only CleanResult
    doesn't retain)."""
    import prody

    from .clean import clean_from_config
    from .labels import ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue

    prody.confProDy(verbosity="none")
    apo = clean_from_config(target_name, role="apo")
    holo = clean_from_config(target_name, role="holo")

    holo_chains = target_config.get("holo_chains") or target_config.get("chains") or sorted(set(holo.chain_ids))
    apo_chains = target_config.get("apo_chains") or target_config.get("chains") or sorted(set(apo.chain_ids))

    holo_raw = prody.parsePDB(target_config["holo_pdb"], compressed=False)
    apo_raw = prody.parsePDB(target_config["apo_pdb"], compressed=False)

    holo_chain_sel = " or ".join(f"chain {c}" for c in holo_chains)
    holo_struct = holo_raw.select(holo_chain_sel)
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)
    holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
        holo_struct, holo_chains, holo.resnums
    )
    return apo, holo, apo_raw, holo_raw, apo_chains, holo_chains


def _holo_to_apo_map(apo, holo) -> Dict[int, int]:
    """{holo CleanResult index: apo CleanResult index}, same Needleman-Wunsch
    global alignment `labels.holo_pocket_mask` already uses -- every
    criterion below routes residue identity through this one map so C1-C4
    agree on what "the same residue" means, per this task's own numbering
    Constraint."""
    apo_seq = _sequence(apo.resnames)
    holo_seq = _sequence(holo.resnames)
    return _needleman_wunsch_map(apo_seq, holo_seq)


def _apply_exclusions(mask: np.ndarray, active_site: np.ndarray, terminal: np.ndarray) -> np.ndarray:
    return mask & ~active_site & ~terminal


# ---------------------------------------------------------------------------
# C1 -- ligand heavy-atom contact, swept 3.5-6.0 A
# ---------------------------------------------------------------------------

def criterion_c1_contact_sweep(apo, holo, target_config: dict) -> CriterionResult:
    ligand_code = target_config.get("drug_ligand")
    if not ligand_code:
        return CriterionResult("C1_contact", None, False, {"reason": "no drug_ligand"})

    n = len(apo.resnums)
    union = np.zeros(n, dtype=bool)
    per_cutoff = {}
    any_resolved = False
    for cutoff in C1_CUTOFFS:
        m = holo_pocket_mask(apo, holo, ligand_code, cutoff=cutoff)
        if m is None:
            per_cutoff[cutoff] = None
            continue
        any_resolved = True
        per_cutoff[cutoff] = m
        union |= m
    if not any_resolved:
        return CriterionResult("C1_contact", None, False, {"reason": f"'{ligand_code}' not in holo.ligand_groups"})
    return CriterionResult(
        "C1_contact", union, True,
        {"per_cutoff_n": {c: (int(m.sum()) if m is not None else None) for c, m in per_cutoff.items()}},
    )


# ---------------------------------------------------------------------------
# C2 -- delta-SASA on ligand removal
# ---------------------------------------------------------------------------

def criterion_c2_delta_sasa(apo, holo, apo_raw, holo_raw, holo_chains, holo_to_apo, target_config: dict) -> CriterionResult:
    try:
        import freesasa
    except ImportError:
        return CriterionResult("C2_dsasa", None, False, {"reason": "freesasa not installed"})

    ligand_code = target_config.get("drug_ligand")
    if not ligand_code:
        return CriterionResult("C2_dsasa", None, False, {"reason": "no drug_ligand"})

    import prody

    chain_sel = " or ".join(f"chain {c}" for c in holo_chains)
    sel = holo_raw.select(f"({chain_sel})")
    if sel is None:
        return CriterionResult("C2_dsasa", None, False, {"reason": "chain selection empty"})

    with_ligand = sel.select(f"protein or (hetero and resname {ligand_code})")
    without_ligand = sel.select("protein")
    if with_ligand is None or without_ligand is None:
        return CriterionResult("C2_dsasa", None, False, {"reason": f"'{ligand_code}' not resolvable in holo raw structure"})

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        p_with = tmp / "with_ligand.pdb"
        p_without = tmp / "without_ligand.pdb"
        prody.writePDB(str(p_with), with_ligand)
        prody.writePDB(str(p_without), without_ligand)

        # `hetatm: True` is load-bearing -- freesasa's default options ignore
        # HETATM records entirely, which silently made "with_ligand" and
        # "without_ligand" identical (the ligand's own atoms were never in
        # the SASA calc either way) until caught by a hand-checked case
        # (KRAS_G12C Cys12/His95 real burial, this task's own Constraint).
        s_with = freesasa.Structure(str(p_with), options={"hetatm": True})
        r_with = freesasa.calc(s_with).residueAreas()
        s_without = freesasa.Structure(str(p_without), options={"hetatm": True})
        r_without = freesasa.calc(s_without).residueAreas()

    n = len(apo.resnums)
    mask = np.zeros(n, dtype=bool)
    n_mapped = 0
    delta_max = 0.0
    for chain, resmap in r_without.items():
        if chain not in r_with:
            continue
        for resnum_str, area_free in resmap.items():
            area_bound = r_with[chain].get(resnum_str)
            if area_bound is None:
                continue
            delta = area_free.total - area_bound.total
            delta_max = max(delta_max, delta)
            if delta <= DSASA_THRESHOLD_A2:
                continue
            # Map (chain, resnum) -> holo CleanResult index -> apo index.
            try:
                resnum = int(resnum_str)
            except ValueError:
                continue
            holo_idx = next(
                (i for i, (c, r) in enumerate(zip(holo.chain_ids, holo.resnums))
                 if c == chain and int(r) == resnum),
                None,
            )
            if holo_idx is None:
                continue
            apo_idx = holo_to_apo.get(holo_idx)
            if apo_idx is None:
                continue
            mask[apo_idx] = True
            n_mapped += 1

    return CriterionResult(
        "C2_dsasa", mask, True,
        {"n_residues_buried": n_mapped, "threshold_A2": DSASA_THRESHOLD_A2, "max_delta_A2": round(delta_max, 2)},
    )


# ---------------------------------------------------------------------------
# fpocket runner (local vendored binary) -- shared by C3/C5
# ---------------------------------------------------------------------------

def _run_fpocket_local(pdb_path: Path, work_dir: Path, timeout: float = 180.0) -> dict:
    if not FPOCKET_BIN.exists():
        return {"error": f"fpocket binary not found at {FPOCKET_BIN}"}
    result = subprocess.run(
        [str(FPOCKET_BIN), "-f", str(pdb_path)],
        cwd=work_dir, capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        return {"error": f"fpocket exited {result.returncode}: {result.stderr.strip()[:500]}"}
    out_dir = work_dir / f"{pdb_path.stem}_out"
    info_file = out_dir / f"{pdb_path.stem}_info.txt"
    if not info_file.exists():
        return {"error": f"fpocket produced no info file at {info_file}"}
    pockets = _parse_fpocket_info_full(info_file.read_text())
    pockets_dir = out_dir / "pockets"
    for p in pockets:
        atm_file = pockets_dir / f"pocket{p['id']}_atm.pdb"
        residues = set()
        if atm_file.exists():
            for line in atm_file.read_text().splitlines():
                if line.startswith(("ATOM", "HETATM")):
                    chain = line[21].strip()
                    try:
                        resnum = int(line[22:26])
                    except ValueError:
                        continue
                    residues.add((chain, resnum))
        p["residues"] = residues
    return {"pockets": pockets}


def _parse_fpocket_info_full(text: str) -> list:
    """Same block-split logic as `baselines._parse_fpocket_info`, extended
    to also capture Volume (needed for C5's crypticity ratio -- the shared
    helper only ever needed Score/Druggability Score, so this is a local
    superset rather than a change to that frozen scoring-path function)."""
    pockets = []
    blocks = re.split(r"^Pocket (\d+) :\s*$", text, flags=re.MULTILINE)[1:]
    for pocket_id, body in zip(blocks[0::2], blocks[1::2]):
        score_m = re.search(r"^\s*Score\s*:\s*([-\d.]+)", body, flags=re.MULTILINE)
        drug_m = re.search(r"^\s*Druggability Score\s*:\s*([-\d.]+)", body, flags=re.MULTILINE)
        vol_m = re.search(r"^\s*Volume\s*:\s*([-\d.]+)", body, flags=re.MULTILINE)
        pockets.append({
            "id": int(pocket_id),
            "score": float(score_m.group(1)) if score_m else None,
            "druggability_score": float(drug_m.group(1)) if drug_m else None,
            "volume": float(vol_m.group(1)) if vol_m else None,
        })
    return pockets


def _select_ligand_proximal_pocket(pockets: list, ligand_coords: np.ndarray, apo_or_holo_coords_by_chain_resnum: dict) -> Optional[dict]:
    """Among fpocket's detected cavities, pick the one whose member residues
    sit closest (mean Ca distance) to the real (stripped) ligand's own
    heavy atoms -- the only way to identify "the" cavity once the ligand
    that would otherwise mark it has been removed (C3's whole point)."""
    best, best_dist = None, np.inf
    for p in pockets:
        coords = [apo_or_holo_coords_by_chain_resnum[k] for k in p["residues"] if k in apo_or_holo_coords_by_chain_resnum]
        if not coords:
            continue
        coords = np.array(coords)
        diff = coords[:, None, :] - ligand_coords[None, :, :]
        min_d = np.sqrt((diff ** 2).sum(axis=2)).min(axis=1)
        mean_d = float(min_d.mean())
        if mean_d < best_dist:
            best_dist, best = mean_d, p
    if best is not None:
        best = dict(best)
        best["mean_dist_to_ligand_A"] = best_dist
    return best


# ---------------------------------------------------------------------------
# C3 -- geometric cavity in holo, ligand stripped (fpocket)
# ---------------------------------------------------------------------------

def criterion_c3_fpocket_holo_stripped(apo, holo, holo_raw, holo_chains, holo_to_apo, target_config: dict) -> CriterionResult:
    ligand_code = target_config.get("drug_ligand")
    if not ligand_code:
        return CriterionResult("C3_fpocket_holo", None, False, {"reason": "no drug_ligand"})
    ligand = next((g for g in holo.ligand_groups if g.resname == ligand_code), None)
    if ligand is None:
        return CriterionResult("C3_fpocket_holo", None, False, {"reason": f"'{ligand_code}' not resolvable"})

    chain_sel = " or ".join(f"chain {c}" for c in holo_chains)
    protein_only = holo_raw.select(f"protein and ({chain_sel})")
    if protein_only is None:
        return CriterionResult("C3_fpocket_holo", None, False, {"reason": "chain selection empty"})

    import prody
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        pdb_path = tmp / "holo_stripped.pdb"
        prody.writePDB(str(pdb_path), protein_only)
        result = _run_fpocket_local(pdb_path, tmp)

    if "error" in result:
        return CriterionResult("C3_fpocket_holo", None, False, {"reason": result["error"]})

    coord_lookup = {(c, int(r)): xyz for c, r, xyz in zip(holo.chain_ids, holo.resnums, holo.coords)}
    chosen = _select_ligand_proximal_pocket(result["pockets"], ligand.coords, coord_lookup)
    if chosen is None:
        return CriterionResult("C3_fpocket_holo", None, False, {"reason": "no fpocket cavity found near ligand"})

    n = len(apo.resnums)
    mask = np.zeros(n, dtype=bool)
    holo_idx_lookup = {(c, int(r)): i for i, (c, r) in enumerate(zip(holo.chain_ids, holo.resnums))}
    for key in chosen["residues"]:
        holo_idx = holo_idx_lookup.get(key)
        if holo_idx is None:
            continue
        apo_idx = holo_to_apo.get(holo_idx)
        if apo_idx is not None:
            mask[apo_idx] = True

    return CriterionResult(
        "C3_fpocket_holo", mask, True,
        {
            "n_pockets_detected": len(result["pockets"]),
            "chosen_pocket_id": chosen["id"],
            "chosen_pocket_score": chosen["score"],
            "chosen_pocket_volume": chosen["volume"],
            "mean_dist_to_ligand_A": round(chosen["mean_dist_to_ligand_A"], 2),
        },
    )


# ---------------------------------------------------------------------------
# C4 -- depositor/software SITE records (legacy PDB REMARK 800 + SITE)
# ---------------------------------------------------------------------------

_SITE_ID_RE = re.compile(r"^REMARK 800 SITE_IDENTIFIER:\s*(\S+)", re.MULTILINE)
_SITE_DESC_RE = re.compile(r"^REMARK 800 SITE_DESCRIPTION:\s*(.*)$", re.MULTILINE)


def criterion_c4_depositor_site(holo_pdb_id: str, apo, holo, holo_to_apo, target_config: dict) -> CriterionResult:
    """Parses legacy-format SITE/REMARK 800 records from the raw PDB file
    (auto-generated at deposition by the refining software, independent of
    every computation this module does itself -- C1-C3/C5 all derive from
    coordinates this module fetches and processes; this is the one route
    that reuses someone else's already-computed answer). Finds the SITE
    whose REMARK 800 description names the target's `drug_ligand`, and
    returns its listed protein residues on apo numbering.

    Genuinely unavailable (not approximated) when: the entry has no SITE
    records at all (common for cryo-EM depositions), or none of them
    describe the drug ligand by name.
    """
    import prody

    ligand_code = target_config.get("drug_ligand")
    if not ligand_code:
        return CriterionResult("C4_depositor_site", None, False, {"reason": "no drug_ligand"})

    try:
        pdb_path = prody.fetchPDB(holo_pdb_id, compressed=False)
    except Exception as e:  # noqa: BLE001 -- network/parse failure, report not guess
        return CriterionResult("C4_depositor_site", None, False, {"reason": f"fetch failed: {e}"})
    if pdb_path is None:
        return CriterionResult("C4_depositor_site", None, False, {"reason": "prody.fetchPDB returned None"})

    text = Path(pdb_path).read_text(errors="replace")
    site_ids = _SITE_ID_RE.findall(text)
    site_descs = _SITE_DESC_RE.findall(text)
    if not site_ids:
        return CriterionResult("C4_depositor_site", None, False, {"reason": "no SITE records in entry"})

    target_site_id = None
    for sid, desc in zip(site_ids, site_descs):
        if ligand_code.upper() in desc.upper():
            target_site_id = sid
            break
    if target_site_id is None:
        return CriterionResult(
            "C4_depositor_site", None, False,
            {"reason": f"no SITE record describes ligand '{ligand_code}'", "site_ids_found": site_ids},
        )

    # SITE lines: "SITE     1 AC3 21 VAL A   9  GLY A  10  ..." -- id + up to
    # 4 (resname, chain, resnum) triples per line, continued across lines
    # sharing the same site id.
    protein_resnames = set(_THREE_TO_ONE.keys())
    residues = set()
    for line in text.splitlines():
        if not line.startswith("SITE"):
            continue
        if line[11:14].strip() != target_site_id:
            continue
        rest = line[18:]
        # groups of (resname, chain, resnum) each occupying 11 chars: "XXX C NNNN"
        for i in range(0, len(rest), 11):
            chunk = rest[i:i + 11]
            if len(chunk.strip()) < 5:
                continue
            resname = chunk[0:3].strip()
            chain = chunk[4:5].strip()
            resnum_str = chunk[5:11].strip()
            if resname.upper() not in protein_resnames or not chain or not resnum_str:
                continue
            try:
                residues.add((chain, int(resnum_str)))
            except ValueError:
                continue

    n = len(apo.resnums)
    mask = np.zeros(n, dtype=bool)
    holo_idx_lookup = {(c, int(r)): i for i, (c, r) in enumerate(zip(holo.chain_ids, holo.resnums))}
    n_matched = 0
    for key in residues:
        holo_idx = holo_idx_lookup.get(key)
        if holo_idx is None:
            continue
        apo_idx = holo_to_apo.get(holo_idx)
        if apo_idx is not None:
            mask[apo_idx] = True
            n_matched += 1

    if n_matched == 0:
        return CriterionResult(
            "C4_depositor_site", None, False,
            {"reason": "SITE record found but no listed residue mapped onto apo/holo protein chains", "site_id": target_site_id},
        )

    return CriterionResult(
        "C4_depositor_site", mask, True,
        {"site_id": target_site_id, "n_residues_listed": len(residues), "n_mapped": n_matched},
    )


# ---------------------------------------------------------------------------
# C5 -- crypticity: apo vs. holo cavity volume ratio (fpocket)
# ---------------------------------------------------------------------------

def criterion_c5_crypticity(apo, apo_raw, apo_chains, c3_result: CriterionResult, holo_volume: Optional[float]) -> dict:
    """Target-level qualifier, not a per-residue mask. Runs fpocket on the
    (drug-free by construction) apo structure and looks for a cavity
    overlapping C3's already-identified holo-mapped residue set. Reports
    the volume ratio (apo cavity volume / holo cavity volume) when both
    exist; a target where no apo cavity overlaps the mapped pocket at all
    is reported as "fully cryptic" (ratio 0), not silently skipped.
    """
    if not c3_result.available or c3_result.mask is None or holo_volume is None:
        return {"available": False, "reason": "C3 unavailable or holo volume unknown -- crypticity needs both"}

    chain_sel = " or ".join(f"chain {c}" for c in apo_chains)
    protein_only = apo_raw.select(f"protein and ({chain_sel})")
    if protein_only is None:
        return {"available": False, "reason": "apo chain selection empty"}

    import prody
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        pdb_path = tmp / "apo.pdb"
        prody.writePDB(str(pdb_path), protein_only)
        result = _run_fpocket_local(pdb_path, tmp)

    if "error" in result:
        return {"available": False, "reason": result["error"]}

    target_residues = set((c, int(r)) for c, r in zip(np.asarray(apo.chain_ids)[c3_result.mask], apo.resnums[c3_result.mask]))
    best, best_overlap = None, 0
    for p in result["pockets"]:
        overlap = len(p["residues"] & target_residues)
        if overlap > best_overlap:
            best_overlap, best = overlap, p

    if best is None or best["volume"] is None:
        return {
            "available": True, "apo_cavity_found": False, "apo_volume": 0.0,
            "holo_volume": holo_volume, "volume_ratio_apo_over_holo": 0.0,
            "n_pockets_detected_apo": len(result["pockets"]),
        }
    return {
        "available": True, "apo_cavity_found": True, "apo_volume": best["volume"],
        "holo_volume": holo_volume,
        "volume_ratio_apo_over_holo": round(best["volume"] / holo_volume, 3) if holo_volume else None,
        "overlap_n_residues": best_overlap,
        "n_pockets_detected_apo": len(result["pockets"]),
    }


# ---------------------------------------------------------------------------
# C6 -- distality (Euclidean + spatial-hop + chain-hop), target-level
# ---------------------------------------------------------------------------

def chain_hop_from_seed(chain_ids: list, source: np.ndarray, n: int) -> np.ndarray:
    """Ported verbatim from TASK-0186's
    `scripts/hop_distance_generalization_audit.py::chain_hop_from_seed` --
    same `n+1`-unreachable convention as `baselines.hop_from_seed`. Not
    cross-imported (that file is a script, this is library surface); kept
    identical so this task's own cross-check against TASK-0186's numbers is
    apples-to-apples."""
    chain_arr = np.asarray(chain_ids)
    idx = np.atleast_1d(np.asarray(source, dtype=int))
    dist = np.full(n, float(n + 1))
    positions = np.arange(n)
    for s in idx.tolist():
        same_chain = chain_arr == chain_arr[s]
        d = np.abs(positions - s).astype(float)
        d = np.where(same_chain, d, float(n + 1))
        dist = np.minimum(dist, d)
    return dist


def criterion_c6_distality(apo, active_site: np.ndarray, pocket_mask: np.ndarray) -> dict:
    """Target-level qualifier against a given pocket mask (called once per
    label -- incumbent/core/consensus -- by the caller, never assumed to be
    the same across labels)."""
    from .baselines import hop_from_seed

    if not active_site.any() or not pocket_mask.any():
        return {"available": False, "reason": "empty active_site or pocket mask"}

    n = len(apo.resnums)
    active_idx = np.where(active_site)[0]
    pocket_idx = np.where(pocket_mask)[0]
    unreachable = float(n + 1)

    diff = apo.coords[pocket_idx, None, :] - apo.coords[None, active_idx, :]
    euclid = np.min(np.sqrt((diff ** 2).sum(axis=2)), axis=1)

    neg_hops = hop_from_seed(apo.coords, source=active_idx, cutoff=HOP_CUTOFF)
    spatial_hops = (-neg_hops)[pocket_idx]
    spatial_reachable = spatial_hops < unreachable

    chain_hops_all = chain_hop_from_seed(apo.chain_ids, source=active_idx, n=n)
    chain_hops = chain_hops_all[pocket_idx]
    chain_reachable = chain_hops < unreachable

    def _summ(v, reach):
        vv = v[reach]
        if not reach.any():
            return {"min": None, "mean": None, "median": None}
        return {"min": float(vv.min()), "mean": float(vv.mean()), "median": float(np.median(vv))}

    return {
        "available": True,
        "euclid_min_A": float(euclid.min()),
        "euclid_mean_A": float(euclid.mean()),
        "spatial_hop": _summ(spatial_hops, spatial_reachable),
        "spatial_hop_frac_le_1": float(np.mean(spatial_hops[spatial_reachable] <= 1)) if spatial_reachable.any() else None,
        "chain_hop": _summ(chain_hops, chain_reachable),
        "n_pocket": int(len(pocket_idx)),
    }


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def assemble_consensus(criteria: Dict[str, CriterionResult], n: int, min_votes: int = 3) -> dict:
    """Combines C1-C4 (the four per-residue criteria) by majority vote.
    Unavailable criteria do not vote (do not count toward the >=3 bar as
    absent-equals-no; they are simply excluded from both numerator and
    denominator, i.e. from `n_available`) -- so a target where only 3 of 4
    criteria resolve at all needs all 3 to agree, not silently treated as
    if the 4th voted 'no'.
    """
    per_residue_votes = np.zeros(n, dtype=int)
    available_names = []
    for name in ("C1_contact", "C2_dsasa", "C3_fpocket_holo", "C4_depositor_site"):
        c = criteria.get(name)
        if c is None or not c.available or c.mask is None:
            continue
        available_names.append(name)
        per_residue_votes += c.mask.astype(int)

    n_available = len(available_names)
    if n_available == 0:
        return {
            "core": None, "consensus": None, "shell": None,
            "n_criteria_available": 0, "criteria_available": [],
            "resolution": float("nan"),
        }

    consensus = per_residue_votes >= min(min_votes, n_available)
    core = per_residue_votes == n_available
    shell = consensus & ~core

    n_core = int(core.sum())
    resolution = float("inf") if n_core == 0 else float(shell.sum()) / n_core

    return {
        "core": core, "consensus": consensus, "shell": shell,
        "n_criteria_available": n_available, "criteria_available": available_names,
        "resolution": resolution,
    }


def build_consensus_label(target_name: str, target_config: dict) -> ConsensusLabel:
    """Top-level entry point: builds the full consensus label for one
    target. `frozen_context` per this task's Constraint -- no score is read
    or computed here."""
    apo, holo, apo_raw, holo_raw, apo_chains, holo_chains = load_apo_holo_full(target_name, target_config)
    holo_to_apo = _holo_to_apo_map(apo, holo)

    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", 4.5))
    _heavy_atom_coords = getattr(holo, "heavy_atom_coords", None)
    func_idx, _prov = functional_indices(
        apo.coords, holo.ligand_groups, target_config, cutoff=pocket_cutoff,
        heavy_atom_coords=_heavy_atom_coords,
        heavy_atom_seq_index=getattr(holo, "heavy_atom_seq_index", None),
        heavy_atom_resnames=(holo.resnames if _heavy_atom_coords is not None else None),
        coords_resnames=(apo.resnames if _heavy_atom_coords is not None else None),
        coords_resnums=apo.resnums,
    )
    n = len(apo.resnums)
    active_site = np.zeros(n, dtype=bool)
    active_site[func_idx] = True
    terminal = terminal_mask(n)

    c1 = criterion_c1_contact_sweep(apo, holo, target_config)
    c2 = criterion_c2_delta_sasa(apo, holo, apo_raw, holo_raw, holo_chains, holo_to_apo, target_config)
    c3 = criterion_c3_fpocket_holo_stripped(apo, holo, holo_raw, holo_chains, holo_to_apo, target_config)
    c4 = criterion_c4_depositor_site(target_config["holo_pdb"], apo, holo, holo_to_apo, target_config)

    criteria = {}
    for c in (c1, c2, c3, c4):
        if c.available and c.mask is not None:
            c.mask = _apply_exclusions(c.mask, active_site, terminal)
        criteria[c.name] = c

    assembled = assemble_consensus(criteria, n)

    holo_volume = None
    if c3.available:
        holo_volume = c3.detail.get("chosen_pocket_volume")
    c5 = criterion_c5_crypticity(apo, apo_raw, apo_chains, c3, holo_volume)

    incumbent = None
    if c1.available:
        # 4.5 A only, for continuity with the 226-cell register -- distinct
        # from C1's own union-across-cutoffs mask.
        m = holo_pocket_mask(apo, holo, target_config.get("drug_ligand"), cutoff=4.5)
        if m is not None:
            incumbent = _apply_exclusions(m, active_site, terminal)

    task_validity = {
        "drug_present": c1.available,
        "crypticity": c5,
    }
    if assembled["consensus"] is not None and assembled["consensus"].any():
        task_validity["c6_vs_consensus"] = criterion_c6_distality(apo, active_site, assembled["consensus"])
    if incumbent is not None and incumbent.any():
        task_validity["c6_vs_incumbent"] = criterion_c6_distality(apo, active_site, incumbent)

    return ConsensusLabel(
        target=target_name,
        core=assembled["core"], consensus=assembled["consensus"], shell=assembled["shell"],
        active_site=active_site, terminal=terminal,
        criteria=criteria,
        resolution=assembled["resolution"],
        task_validity=task_validity,
        incumbent=incumbent,
    )
