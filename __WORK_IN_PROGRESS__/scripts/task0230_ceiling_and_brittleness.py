#!/usr/bin/env python3
"""TASK-0230 -- TASK-0227's own deferred §5.2 (oracle-supervised reachability
ceiling) and §5.3 (scorer-brittleness interpolation control), now that both
EvoEF2 and fpocket are confirmed vendored and working (TASK-0227's own
"neither is installed" claim was a search error, corrected same-day).

Reuses this project's own validated infrastructure rather than re-deriving:
`allostery.superpose.align_apo_holo`/`chain_map_from_config`/`anm_modes`
(TASK-0005/TASK-0127/TASK-0144/TASK-0133's own Kabsch + ANM + per-role-chain
machinery) for the apo/holo correspondence and mode subspace, and
`task0204_rotamer_repack_baseline.py`'s own `_select_window`/
`_write_full_atom_with_window_chain`/`_run_evoef2`/`score_structure`
(EvoEF2 + fpocket wiring, including its own hard-won chain-interleaving-bug
workaround) for repacking and druggability scoring.

Modeling approximation, stated once, up front, not silently buried: both
experiments move the FULL-ATOM apo structure by a per-residue RIGID
TRANSLATION derived from that residue's own Cα displacement (§5.2: the
apo->holo displacement projected onto the top-k static ANM subspace;
§5.3: a linear fraction of the true displacement). This is a coarse
backbone-placement proxy, not a refined all-atom model -- side chains are
left exactly as in native apo before EvoEF2 repacks them (§5.2 only; §5.3
scores the rigid-translated structure directly, no repacking). Residues
outside the common apo/holo correspondence set are left at their native
apo position (displacement 0), not extrapolated.

Per this task's own Intent Contract, §5.2's repacker is EvoEF2's
`SideChainRepack` (real simulated annealing, TASK-0204's own validated
wiring) -- a strong heuristic, NOT a DEE/A*/ILP/Rosetta global-optimum
guarantee. Reported as a heuristic ceiling, not the oracle ceiling the
source document specified.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
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
from allostery.superpose import align_apo_holo, anm_modes, chain_map_from_config  # noqa: E402

from task0204_rotamer_repack_baseline import (  # noqa: E402
    _run_evoef2,
    _select_window,
    score_structure,
)
from task0163_external_baseline_scoring import _run_fpocket  # noqa: E402

TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
ANM_CUTOFF = 10.0     # allostery.superpose's own established default (compute_learnability)
ANM_K = 50            # matches TASK-0227's own k for the same real targets
POCKET_CUTOFF = 4.5
WINDOW_MAX_SIZE = 12  # matches TASK-0204's own window size convention
N_INTERP_STEPS = 20   # source's own §5.3 spec: "interpolate apo->holo in 20 steps"
DRUGGABILITY_BAR = 0.5  # TASK-0204's own established fpocket druggable/non-druggable cutoff
N_STRONGER_TRIALS = 4    # independent EvoEF2 seeds, matches the robustness check already done for BCR_ABL1


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _load_apo_holo(target_name: str, target_config: dict):
    import prody

    apo = clean_from_config(target_name, role="apo")
    holo = clean_from_config(target_name, role="holo")

    prody.confProDy(verbosity="none")
    holo_id = target_config["holo_pdb"]
    chains = target_config.get("chains") or sorted(set(holo.chain_ids))
    chain_sel = " or ".join(f"chain {c}" for c in chains)
    holo_struct = prody.parsePDB(holo_id, compressed=False).select(chain_sel)
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)
    holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
        holo_struct, chains, holo.resnums
    )
    return apo, holo


def _load_full_atom_apo(target_config: dict, apo_chains):
    """Full-atom apo structure (same altloc/protein/chain filtering as the
    project's own `_write_full_atom_apo_pdb`), as an in-memory prody
    AtomGroup (not written to disk yet -- caller moves atoms first)."""
    import prody

    prody.confProDy(verbosity="none")
    struct = prody.parsePDB(target_config["apo_pdb"], compressed=False)
    alt_locs = struct.getAltlocs()
    if alt_locs is not None and any(a not in ("", " ", "\x00") for a in alt_locs):
        struct = struct.select("altloc _ A") or struct
    chain_part = " and (" + " or ".join(f"chain {c}" for c in apo_chains) + ")"
    return struct.select(f"protein{chain_part}").copy()


def _load_full_atom_holo(target_config: dict, holo_chains):
    import prody

    prody.confProDy(verbosity="none")
    struct = prody.parsePDB(target_config["holo_pdb"], compressed=False)
    alt_locs = struct.getAltlocs()
    if alt_locs is not None and any(a not in ("", " ", "\x00") for a in alt_locs):
        struct = struct.select("altloc _ A") or struct
    chain_part = " and (" + " or ".join(f"chain {c}" for c in holo_chains) + ")"
    return struct.select(f"protein{chain_part}").copy()


def _apply_rigid_residue_displacement(struct, disp_lookup: dict):
    """Translates every atom of each residue by that residue's own
    (chain, resnum) -> (dx,dy,dz) lookup entry; residues absent from the
    lookup (no common apo/holo correspondence) are left untouched. Coarse
    whole-residue rigid-translation approximation -- see module docstring."""
    coords = struct.getCoords().copy()
    chids = struct.getChids()
    resnums = struct.getResnums()
    for i in range(len(coords)):
        d = disp_lookup.get((str(chids[i]), int(resnums[i])))
        if d is not None:
            coords[i] += d
    struct.setCoords(coords)
    return struct


def _write_contiguous_window_chain(struct, window: list, out_path: Path) -> str:
    """Relabels `window` residues to chain 'B', writes atoms as contiguous
    per-chain blocks (not interleaved) -- EvoEF2's own chain-interleaving
    parser bug, documented and worked around identically to TASK-0204's
    own `_write_full_atom_with_window_chain` (reused logic, adapted to
    take an already-in-memory, already-moved AtomGroup instead of
    re-parsing from disk).

    Picks a relabel letter NOT already present in `struct` (checked, not
    hardcoded) -- TASK-0204's own version hardcodes 'B', which silently
    mislabels every atom as "window" when the structure's real chain is
    already 'B' (CARDIAC_MYOSIN's own holo_chains=["B"] hits this
    directly: relabeling window atoms to 'B' is then indistinguishable
    from the untouched rest, `other_idx` comes back empty, and prody's
    `struct[other_idx]` raises `IndexError` on the empty selection --
    confirmed by direct reproduction, not assumed. TASK-0204's own script
    never triggers it, since it only ever calls this on apo structures
    with `apo_chains=["A"]` for its own two targets, but the same defect
    is latent there too -- not fixed there, out of this task's own
    scope, noted in this task's Done section)."""
    import prody

    existing = set(struct.getChids().tolist())
    window_letter = next(c for c in "ZYXWVUTSRQPONMLKJIHGFEDCBA" if c not in existing)

    window_set = set(window)
    chids = struct.getChids()
    resnums = struct.getResnums()
    new_chids = chids.copy()
    for i in range(len(new_chids)):
        if (chids[i], int(resnums[i])) in window_set:
            new_chids[i] = window_letter
    struct.setChids(new_chids)

    is_window = new_chids == window_letter
    other_idx = np.where(~is_window)[0]
    window_idx = np.where(is_window)[0]
    reordered = struct[other_idx] + struct[window_idx]
    prody.writePDB(str(out_path), reordered)
    return window_letter


def _common_set_and_projection(apo, holo, target_config, k=ANM_K):
    """Kabsch alignment + static ANM subspace + top-k-mode-projected
    displacement, all on the common (chain, resnum) Ca set -- reuses
    `align_apo_holo`/`anm_modes` (this project's own validated
    implementations, not re-derived).

    Returns (alignment, disp_lookup_full, disp_lookup_projected_k,
    true_displacement_flat, k_actually_used).
    """
    chain_map = chain_map_from_config(target_config)
    alignment = align_apo_holo(apo, holo, chain_map=chain_map)
    apo_idx = alignment.apo_idx
    common_coords_apo = apo.coords[apo_idx]
    common_coords_holo_aligned = alignment.aligned_holo_coords[alignment.holo_idx]
    delta_r = (common_coords_holo_aligned - common_coords_apo).ravel()

    w, eigvecs = anm_modes(common_coords_apo, cutoff=ANM_CUTOFF, n_modes=k)
    k_used = eigvecs.shape[1]
    c = eigvecs.T @ delta_r
    delta_projected = (eigvecs @ c).reshape(-1, 3)

    apo_chain_ids = np.asarray(apo.chain_ids)[apo_idx]
    apo_resnums = np.asarray(apo.resnums)[apo_idx]
    full_by_res = {}
    proj_by_res = {}
    delta_full = delta_r.reshape(-1, 3)
    for j in range(len(apo_idx)):
        key = (str(apo_chain_ids[j]), int(apo_resnums[j]))
        full_by_res[key] = delta_full[j]
        proj_by_res[key] = delta_projected[j]

    return alignment, full_by_res, proj_by_res, delta_r, k_used


EVOEF2_DIR = Path(__file__).resolve().parent.parent / "tools" / "evoef2"
EVOEF2_BIN = EVOEF2_DIR / "EvoEF2"


def _compute_stability(pdb_path: Path) -> dict:
    """Runs EvoEF2 `ComputeStability` and parses `Total` and
    `interS_vdwrep` (steric repulsion -- the direct clash signal) from its
    stdout. A geometry-sanity check on the rigid-per-residue-translation
    approximation: real backbone motion is torsional, not a bulk shove of
    every atom in a residue, so this checks whether that approximation is
    producing badly clashing (physically implausible) structures rather
    than genuinely closed pockets -- an alternative explanation for a
    ceiling failure that TASK-0230's own first pass did not rule out."""
    import re
    import subprocess

    local_pdb = EVOEF2_DIR / pdb_path.name
    local_pdb.write_bytes(pdb_path.read_bytes())
    result = subprocess.run(
        [f"./{EVOEF2_BIN.name}", "--command=ComputeStability", f"--pdb={local_pdb.name}"],
        cwd=EVOEF2_DIR, capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        return {"error": f"ComputeStability exited {result.returncode}: {result.stderr.strip()[:400]}"}
    total_m = re.search(r"^Total\s*=\s*([-\d.]+)", result.stdout, flags=re.MULTILINE)
    vdwrep_m = re.search(r"^interS_vdwrep\s*=\s*([-\d.]+)", result.stdout, flags=re.MULTILINE)
    return {
        "total": float(total_m.group(1)) if total_m else None,
        "vdwrep": float(vdwrep_m.group(1)) if vdwrep_m else None,
    }


def run_5_2_stronger(name: str, n_trials: int = N_STRONGER_TRIALS) -> dict:
    """The stronger ceiling variant, per the user's own follow-up request:
    use the FULL true apo->holo displacement (not the k=50-mode-truncated
    approximation §5.2 used), still applied as a rigid per-residue
    translation, then EvoEF2 SideChainRepack (multiple independent
    trials, same robustness check already applied to BCR_ABL1) + fpocket
    druggability scoring. Also runs `_compute_stability` at each stage
    (native apo, pre-repack rigid-translated, post-repack) to check
    whether a ceiling failure is a real closed-pocket result or an
    artifact of the rigid-translation approximation producing distorted,
    clashing geometry that EvoEF2/fpocket can't recover from."""
    _log(f"{name}: [5.2-strong] loading target + building pocket label...")
    target_config = load_target_config(name)
    apo, holo = _load_apo_holo(name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=POCKET_CUTOFF)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        return {"target": name, "error": "no resolvable pocket label"}

    window = _select_window(apo, labels_obj.pocket, max_size=WINDOW_MAX_SIZE)
    apo_chains = target_config.get("apo_chains") or target_config.get("chains")
    alignment, full_disp, proj_disp, delta_r, k_used = _common_set_and_projection(apo, holo, target_config)
    _log(f"{name}: [5.2-strong] window={len(window)} common={len(alignment.apo_idx)} "
         f"|delta_r|={np.linalg.norm(delta_r):.3f} A (FULL displacement, no mode truncation)")

    result = {"target": name, "window": window, "n_common_residues": int(len(alignment.apo_idx))}

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        # --- native apo: fpocket score + stability, for reference ---
        native_struct = _load_full_atom_apo(target_config, apo_chains)
        native_pdb = tmp / f"{name.lower()}_native.pdb"
        design_chain = _write_contiguous_window_chain(native_struct, window, native_pdb)
        target_set = {(design_chain, r) for (_c, r) in window}
        result["native_apo"] = score_structure(native_pdb, target_set, tmp)
        result["native_apo_stability"] = _compute_stability(native_pdb)
        _log(f"{name}: [5.2-strong] native apo: {result['native_apo']} "
             f"stability={result['native_apo_stability']}")

        # --- k=50-projected, pre-repack: stability only (druggability already known from run_5_2) ---
        proj_struct = _load_full_atom_apo(target_config, apo_chains)
        proj_struct = _apply_rigid_residue_displacement(proj_struct, proj_disp)
        proj_pdb = tmp / f"{name.lower()}_proj_prerepack.pdb"
        _write_contiguous_window_chain(proj_struct, window, proj_pdb)
        result["k50_projected_prerepack_stability"] = _compute_stability(proj_pdb)
        _log(f"{name}: [5.2-strong] k=50-projected pre-repack stability: "
             f"{result['k50_projected_prerepack_stability']}")

        # --- FULL displacement, pre-repack: fpocket score + stability ---
        full_struct = _load_full_atom_apo(target_config, apo_chains)
        full_struct = _apply_rigid_residue_displacement(full_struct, full_disp)
        full_prerepack_pdb = tmp / f"{name.lower()}_full_prerepack.pdb"
        full_design_chain = _write_contiguous_window_chain(full_struct, window, full_prerepack_pdb)
        full_target_set = {(full_design_chain, r) for (_c, r) in window}
        result["full_displacement_prerepack"] = score_structure(full_prerepack_pdb, full_target_set, tmp)
        result["full_displacement_prerepack_stability"] = _compute_stability(full_prerepack_pdb)
        _log(f"{name}: [5.2-strong] FULL displacement, pre-repack: "
             f"{result['full_displacement_prerepack']} "
             f"stability={result['full_displacement_prerepack_stability']}")

        # --- FULL displacement + EvoEF2 SideChainRepack, N independent trials ---
        trials = []
        for i in range(n_trials):
            time.sleep(1.05)  # EvoEF2 seeds via time(NULL) -- force distinct seeds, matches TASK-0204's own convention
            trial_struct = _load_full_atom_apo(target_config, apo_chains)
            trial_struct = _apply_rigid_residue_displacement(trial_struct, full_disp)
            trial_pdb = tmp / f"{name.lower()}_full_trial{i}.pdb"
            trial_design_chain = _write_contiguous_window_chain(trial_struct, window, trial_pdb)
            repacked = _run_evoef2("SideChainRepack", trial_pdb, trial_design_chain)
            if isinstance(repacked, dict):
                trials.append({"error": repacked["error"]})
                _log(f"{name}: [5.2-strong] trial {i}: ERROR {repacked['error']}")
                continue
            trial_target_set = {(trial_design_chain, r) for (_c, r) in window}
            score = score_structure(repacked, trial_target_set, tmp)
            stability = _compute_stability(repacked)
            trials.append({**score, "stability": stability})
            _log(f"{name}: [5.2-strong] trial {i}: {score} stability={stability}")
        result["full_displacement_repacked_trials"] = trials

    def _d(r):
        return r.get("druggability_score") if isinstance(r, dict) and "error" not in r else None

    d_native = _d(result["native_apo"])
    d_full_prerepack = _d(result["full_displacement_prerepack"])
    d_trials = [t.get("druggability_score") for t in trials if "error" not in t]
    result["summary"] = {
        "druggability_native_apo": d_native,
        "druggability_full_displacement_prerepack": d_full_prerepack,
        "druggability_full_displacement_repacked_trials": d_trials,
        "max_over_trials": max(d_trials) if d_trials else None,
        "any_trial_crosses_bar": any(v is not None and v >= DRUGGABILITY_BAR for v in d_trials) if d_trials else None,
        "native_apo_vdwrep": result["native_apo_stability"].get("vdwrep"),
        "k50_projected_prerepack_vdwrep": result["k50_projected_prerepack_stability"].get("vdwrep"),
        "full_displacement_prerepack_vdwrep": result["full_displacement_prerepack_stability"].get("vdwrep"),
    }
    _log(f"{name}: [5.2-strong] SUMMARY {result['summary']}")
    return result


def run_5_2(name: str) -> dict:
    """Oracle-supervised (heuristic) reachability ceiling: apply the
    top-k-mode-projected apo->holo displacement (rigid per-residue), repack
    the pocket window with EvoEF2 SideChainRepack, score druggability.
    Compare against native apo and true holo at the same window."""
    _log(f"{name}: [5.2] loading target + building pocket label...")
    target_config = load_target_config(name)
    apo, holo = _load_apo_holo(name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=POCKET_CUTOFF)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        return {"target": name, "error": "no resolvable pocket label"}

    window = _select_window(apo, labels_obj.pocket, max_size=WINDOW_MAX_SIZE)
    _log(f"{name}: [5.2] window = {len(window)} residues: {window}")

    apo_chains = target_config.get("apo_chains") or target_config.get("chains")
    holo_chains = target_config.get("holo_chains") or target_config.get("chains")

    alignment, _full_disp, proj_disp, delta_r, k_used = _common_set_and_projection(apo, holo, target_config)
    _log(f"{name}: [5.2] k_used={k_used} common_residues={len(alignment.apo_idx)} "
         f"|delta_r|={np.linalg.norm(delta_r):.3f} A")

    result = {"target": name, "window": window, "k_used": k_used,
              "n_common_residues": int(len(alignment.apo_idx))}

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        # --- native apo, unmoved (baseline floor) ---
        native_struct = _load_full_atom_apo(target_config, apo_chains)
        native_pdb = tmp / f"{name.lower()}_native.pdb"
        design_chain = _write_contiguous_window_chain(native_struct, window, native_pdb)
        target_set = {(design_chain, r) for (_c, r) in window}
        result["native_apo"] = score_structure(native_pdb, target_set, tmp)
        _log(f"{name}: [5.2] native apo: {result['native_apo']}")

        # --- true holo at the corresponding window (ceiling's own reference point) ---
        apo_to_holo_res = {}
        holo_chain_ids = np.asarray(holo.chain_ids)
        holo_resnums = np.asarray(holo.resnums)
        for ai, hi in zip(alignment.apo_idx.tolist(), alignment.holo_idx.tolist()):
            apo_to_holo_res[(str(np.asarray(apo.chain_ids)[ai]), int(np.asarray(apo.resnums)[ai]))] = \
                (str(holo_chain_ids[hi]), int(holo_resnums[hi]))
        holo_window = [apo_to_holo_res[w] for w in window if w in apo_to_holo_res]
        if len(holo_window) < len(window):
            _log(f"{name}: [5.2] WARNING {len(window) - len(holo_window)} window residue(s) "
                 f"have no holo correspondence -- holo comparison uses only {len(holo_window)}")
        holo_struct = _load_full_atom_holo(target_config, holo_chains)
        holo_pdb = tmp / f"{name.lower()}_holo.pdb"
        holo_design_chain = _write_contiguous_window_chain(holo_struct, holo_window, holo_pdb)
        holo_target_set = {(holo_design_chain, r) for (_c, r) in holo_window}
        result["true_holo"] = score_structure(holo_pdb, holo_target_set, tmp)
        _log(f"{name}: [5.2] true holo: {result['true_holo']}")

        # --- projected (k=50) + EvoEF2 SideChainRepack ---
        moved_struct = _load_full_atom_apo(target_config, apo_chains)
        moved_struct = _apply_rigid_residue_displacement(moved_struct, proj_disp)
        moved_pdb = tmp / f"{name.lower()}_projected.pdb"
        moved_design_chain = _write_contiguous_window_chain(moved_struct, window, moved_pdb)
        _log(f"{name}: [5.2] running EvoEF2 SideChainRepack on projected structure...")
        repacked = _run_evoef2("SideChainRepack", moved_pdb, moved_design_chain)
        if isinstance(repacked, dict):
            result["projected_repacked"] = {"error": repacked["error"]}
        else:
            result["projected_repacked"] = score_structure(repacked, target_set, tmp)
        _log(f"{name}: [5.2] projected+repacked: {result['projected_repacked']}")

    def _d(r):
        return r.get("druggability_score") if isinstance(r, dict) and "error" not in r else None

    d_apo, d_holo, d_proj = _d(result["native_apo"]), _d(result["true_holo"]), _d(result["projected_repacked"])
    passes = (
        d_proj is not None and d_proj >= DRUGGABILITY_BAR
        and (d_holo is None or d_apo is None or abs(d_proj - d_holo) <= abs(d_proj - d_apo) or d_proj > d_apo)
    )
    result["summary"] = {
        "druggability_native_apo": d_apo, "druggability_true_holo": d_holo,
        "druggability_projected_repacked": d_proj,
        "ceiling_passes_prereg_rule": bool(passes) if d_proj is not None else None,
    }
    _log(f"{name}: [5.2] SUMMARY {result['summary']}")
    return result


def run_5_3(name: str) -> dict:
    """Scorer-brittleness control: linear apo->holo interpolation (rigid
    per-residue, common set), fpocket druggability at each of 20 steps."""
    _log(f"{name}: [5.3] loading target + building pocket label...")
    target_config = load_target_config(name)
    apo, holo = _load_apo_holo(name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=POCKET_CUTOFF)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        return {"target": name, "error": "no resolvable pocket label"}

    window = _select_window(apo, labels_obj.pocket, max_size=WINDOW_MAX_SIZE)
    apo_chains = target_config.get("apo_chains") or target_config.get("chains")
    alignment, full_disp, _proj_disp, delta_r, _k = _common_set_and_projection(apo, holo, target_config)
    _log(f"{name}: [5.3] window = {len(window)} residues, "
         f"common_residues={len(alignment.apo_idx)}, |delta_r|={np.linalg.norm(delta_r):.3f} A")

    steps = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        design_chain_ref = None
        for i in range(N_INTERP_STEPS):
            t = i / (N_INTERP_STEPS - 1)
            step_disp = {k_: v * t for k_, v in full_disp.items()}
            struct = _load_full_atom_apo(target_config, apo_chains)
            struct = _apply_rigid_residue_displacement(struct, step_disp)
            step_pdb = tmp / f"{name.lower()}_step{i:02d}.pdb"
            design_chain = _write_contiguous_window_chain(struct, window, step_pdb)
            design_chain_ref = design_chain_ref or design_chain
            target_set = {(design_chain, r) for (_c, r) in window}
            score = score_structure(step_pdb, target_set, tmp)
            d = score.get("druggability_score") if "error" not in score else None
            steps.append({"step": i, "t": round(t, 4), "druggability_score": d,
                          "overlap_frac": score.get("overlap_frac"), "error": score.get("error")})
            _log(f"{name}: [5.3] step {i}/{N_INTERP_STEPS - 1} (t={t:.2f}): "
                 f"druggability={d}")

    apo_d = steps[0]["druggability_score"]
    holo_d = steps[-1]["druggability_score"]
    mid_scores = [s["druggability_score"] for s in steps[1:-1] if s["druggability_score"] is not None]
    lo, hi = (min(apo_d, holo_d), max(apo_d, holo_d)) if apo_d is not None and holo_d is not None else (None, None)
    n_strictly_between = 0
    if lo is not None:
        n_strictly_between = sum(1 for v in mid_scores if lo < v < hi)
    classification = None
    if apo_d is not None and holo_d is not None:
        classification = "flat_then_cliff" if n_strictly_between < 3 else "monotone_ish"

    result = {
        "target": name, "window": window, "steps": steps,
        "summary": {
            "apo_druggability": apo_d, "holo_druggability": holo_d,
            "n_mid_steps_strictly_between": n_strictly_between,
            "n_mid_steps_total": len(mid_scores),
            "classification_prereg_rule": classification,
        },
    }
    _log(f"{name}: [5.3] SUMMARY {result['summary']}")
    return result


def main() -> int:
    out = {"5.2_ceiling": {}, "5.3_brittleness": {}}
    for name in TARGETS:
        try:
            out["5.2_ceiling"][name] = run_5_2(name)
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            out["5.2_ceiling"][name] = {"target": name, "error": f"{type(exc).__name__}: {exc}"}
        try:
            out["5.3_brittleness"][name] = run_5_3(name)
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            out["5.3_brittleness"][name] = {"target": name, "error": f"{type(exc).__name__}: {exc}"}

    out_dir = Path(__file__).resolve().parent.parent / "results/tasks/0230_ceiling_and_brittleness"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nWrote {out_path}")

    print("\n=== TASK-0230 summary ===")
    for name in TARGETS:
        r52 = out["5.2_ceiling"].get(name, {})
        r53 = out["5.3_brittleness"].get(name, {})
        print(f"{name}: 5.2={r52.get('summary')}  |  "
              f"5.3={r53.get('summary')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
