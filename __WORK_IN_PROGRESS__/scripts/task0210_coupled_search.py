#!/usr/bin/env python3
"""TASK-0210 -- does a classical, apo-only, trajectory-free coupled
backbone+rotamer search reach the known holo basin?

Pre-registered design (.ai/tasks/IN_PROGRESS/TASK-0210-*.md, "Pre-
Registered Design + Hard Threshold" section, written before this script
ran): simulated annealing over apo-only ANM-mode backbone perturbations at
the pocket window, with EvoEF2 SideChainRepack (vendored, TASK-0204's own
machinery) re-optimizing side chains at every candidate backbone, scored
by fpocket druggability (apo-only-computable objective -- never reads
holo). Holo is used only to score the search's own *output* afterward
(RMSD-reduction + fpocket-hit criteria), never as a search input --
enforced structurally below (the SA loop never touches `holo` at all; only
`score_search_result` does, once, at the end of each restart).

Classical solver only, per this task's own In-Scope bullet ("run this
before any formulation work") -- no quantum formulation here.
"""
from __future__ import annotations

import json
import math
import os
import random
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
from allostery.superpose import anm_modes, chain_map_from_config  # noqa: E402
from task0204_rotamer_repack_baseline import (  # noqa: E402
    EVOEF2_BIN, WINDOW_MAX_SIZE, _run_evoef2, _select_window, score_structure,
)

RESTARTS = 2
ITERATIONS = 10
N_MODES = 20
ANM_CUTOFF = 10.0
STEP_SIGMA_START = 1.2   # Angstrom-scale amplitude on the Ca eigenvector at T_start
T_START = 0.20           # druggability-score units
T_END = 0.01
COOL_RATE = (T_END / T_START) ** (1.0 / max(ITERATIONS - 1, 1))
RMSD_REDUCTION_BAR = 0.50
OVERLAP_BAR = 0.5
DRUGGABILITY_BAR = 0.5

TARGETS = ["KRAS_G12C", "PTP1B", "CASPASE1", "GLUCOKINASE"]


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _write_full_atom_pdb_with_window_chain(pdb_id: str, chains: list, window: list, out_path: Path) -> str:
    """Generalizes `task0204_rotamer_repack_baseline.py
    ::_write_full_atom_with_window_chain` to an arbitrary `pdb_id`/`chains`
    (that function hardcodes `target_config["apo_pdb"]`) -- needed here to
    write the *true holo* window structure for the known-answer check,
    using the exact same recipe (altloc/protein filtering, window residues
    relabeled to a contiguous chain 'B' block -- EvoEF2's PDB parser
    mishandles an interleaved A-B-A chain order, per that function's own
    documented finding)."""
    import prody

    prody.confProDy(verbosity="none")
    struct = prody.parsePDB(pdb_id, compressed=False)
    alt_locs = struct.getAltlocs()
    if alt_locs is not None and any(a not in ("", " ", "\x00") for a in alt_locs):
        struct = struct.select("altloc _ A") or struct
    chain_part = " and (" + " or ".join(f"chain {c}" for c in chains) + ")"
    struct_clean = struct.select(f"protein{chain_part}").copy()

    window_set = set(window)
    chids = struct_clean.getChids()
    resnums = struct_clean.getResnums()
    new_chids = chids.copy()
    for i in range(len(new_chids)):
        if (chids[i], int(resnums[i])) in window_set:
            new_chids[i] = "B"
    struct_clean.setChids(new_chids)

    is_window = new_chids == "B"
    other_idx = np.where(~is_window)[0]
    window_idx = np.where(is_window)[0]
    reordered = struct_clean[other_idx] + struct_clean[window_idx]
    prody.writePDB(str(out_path), reordered)
    return "B"


def known_answer_check(target_name: str, target_config: dict, apo, holo_ca, window: list, work_dir: Path) -> dict:
    """Planned Validation, firewall check: druggability(true holo window)
    must exceed druggability(native apo window) on the identical
    window/target-set definition, before the objective is trusted at all.
    Holo is used here only to construct this one-time sanity structure --
    never inside the SA loop."""
    apo_chains = target_config.get("apo_chains") or target_config.get("chains")
    holo_chains = target_config.get("holo_chains") or target_config.get("chains")
    chain_map = chain_map_from_config(target_config)
    inv_map = {v: k for k, v in (chain_map or {}).items()}

    apo_path = work_dir / f"{target_name.lower()}_t210_kac_apo.pdb"
    design_chain = _write_full_atom_pdb_with_window_chain(target_config["apo_pdb"], apo_chains, window, apo_path)
    apo_target_set = {(design_chain, r) for (_c, r) in window}
    apo_score = score_structure(apo_path, apo_target_set, work_dir)

    holo_window = [(inv_map.get(c, c), r) for (c, r) in window]
    holo_path = work_dir / f"{target_name.lower()}_t210_kac_holo.pdb"
    holo_design_chain = _write_full_atom_pdb_with_window_chain(target_config["holo_pdb"], holo_chains, holo_window, holo_path)
    holo_target_set = {(holo_design_chain, r) for (_c, r) in holo_window}
    holo_score = score_structure(holo_path, holo_target_set, work_dir)

    apo_drug = apo_score.get("druggability_score") or 0.0
    holo_drug = holo_score.get("druggability_score") or 0.0
    return {
        "apo_score": apo_score, "holo_score": holo_score,
        "apo_druggability": apo_drug, "holo_druggability": holo_drug,
        "objective_prefers_holo": bool(holo_drug > apo_drug),
    }


def _druggability_of(pdb_path: Path, target_set: set, work_dir: Path) -> float:
    s = score_structure(pdb_path, target_set, work_dir)
    if isinstance(s, dict) and "error" in s and "druggability_score" not in s:
        return 0.0
    d = s.get("druggability_score")
    return float(d) if d is not None else 0.0


def _repack_and_score(candidate_path: Path, design_chain: str, target_set: set, work_dir: Path):
    """EvoEF2 SideChainRepack at the candidate backbone (apo-only), then
    fpocket-druggability score (apo-only) -- the one inner-loop call this
    whole search spends its time on (~16 s/call on a real target,
    dominates wall-clock, see the task's own Hard-threshold correction)."""
    out = _run_evoef2("SideChainRepack", candidate_path, design_chain)
    if isinstance(out, dict):
        return None, 0.0, out
    score = _druggability_of(out, target_set, work_dir)
    return out, score, None


def run_sa_restart(
    target_name: str, apo_ag, window_keys: list, window_row_idx: list,
    eigvecs: np.ndarray, design_chain: str, target_set: set, work_dir: Path,
    rng: random.Random, restart_idx: int,
) -> dict:
    """One SA restart: propose an ANM-mode-based rigid per-window-residue
    backbone perturbation, repack side chains (EvoEF2), score druggability
    (fpocket) -- both apo-only. Metropolis-accepts on -druggability as
    energy. Never reads holo. Tracks (and returns) the best-scoring
    candidate structure found, by path."""
    chids = apo_ag.getChids()
    resnums = apo_ag.getResnums()
    current_coords = apo_ag.getCoords().copy()
    current_score = 0.0
    best_score, best_path = -1.0, None
    T = T_START
    trace = []

    for it in range(ITERATIONS):
        mode_k = rng.randrange(eigvecs.shape[1])
        amplitude = rng.gauss(0.0, STEP_SIGMA_START * (T / T_START + 0.15))
        proposed = current_coords.copy()
        for (chain, resnum), row in zip(window_keys, window_row_idx):
            disp = eigvecs[3 * row: 3 * row + 3, mode_k] * amplitude
            mask = (chids == chain) & (resnums == resnum)
            proposed[mask] += disp

        cand_ag = apo_ag.copy()
        cand_ag.setCoords(proposed)
        cand_path = work_dir / f"{target_name.lower()}_t210_r{restart_idx}_it{it}.pdb"
        import prody
        prody.writePDB(str(cand_path), cand_ag)

        repacked_path, score, err = _repack_and_score(cand_path, design_chain, target_set, work_dir)
        if err is not None:
            trace.append({"it": it, "mode": mode_k, "amplitude": amplitude, "error": err.get("error")})
            continue

        dE = -score - (-current_score)
        accept = dE < 0 or rng.random() < math.exp(-dE / max(T, 1e-6))
        if accept:
            current_coords = proposed
            current_score = score
        trace.append({"it": it, "mode": mode_k, "amplitude": amplitude, "score": score, "accepted": bool(accept), "T": T})
        if score > best_score:
            best_score, best_path = score, repacked_path
        T *= COOL_RATE

    return {"best_score": best_score, "best_path": str(best_path) if best_path else None, "trace": trace}


def window_rmsd_to_holo(best_path: Path, target_config: dict, window: list) -> float:
    """Heavy-atom RMSD of the SA-found structure's window residues against
    the TRUE holo window, in holo's own frame (Kabsch-superposed via the
    window residues' own backbone N/CA/C -- reuses the technique, not the
    global TASK-0208 alignment, since this is a single-window local
    comparison of a candidate structure that never had a stable global
    frame in the first place). Holo is read here only to *score* the
    search's output -- this function is called once per restart, after
    the SA loop has finished and never again touches the loop."""
    import prody
    from allostery.superpose import kabsch_apply, kabsch_fit

    prody.confProDy(verbosity="none")
    cand = prody.parsePDB(str(best_path))
    cand_window = cand.select(f"chain B")
    if cand_window is None:
        return float("nan")

    holo_chains = target_config.get("holo_chains") or target_config.get("chains")
    chain_map = chain_map_from_config(target_config)
    inv_map = {v: k for k, v in (chain_map or {}).items()}
    holo_window_keys = [(inv_map.get(c, c), r) for (c, r) in window]

    holo_struct = prody.parsePDB(target_config["holo_pdb"], compressed=False)
    chain_part = " and (" + " or ".join(f"chain {c}" for c in holo_chains) + ")"
    holo_clean = holo_struct.select(f"protein{chain_part}")

    cand_by_res: dict = {}
    for atom in cand_window.iterAtoms():
        key = (int(atom.getResnum()), atom.getName())
        cand_by_res[key] = atom.getCoords()

    holo_res_atoms: dict = {}
    if holo_clean is not None:
        for atom in holo_clean.iterAtoms():
            ch, rn, nm = atom.getChid(), int(atom.getResnum()), atom.getName()
            if (ch, rn) in set(holo_window_keys):
                holo_res_atoms.setdefault((ch, rn), {})[nm] = atom.getCoords()

    ca_cand, ca_holo = [], []
    for (apo_c, resnum), (holo_c, _) in zip(window, holo_window_keys):
        c_atoms = {nm: xyz for (rn, nm), xyz in cand_by_res.items() if rn == resnum}
        h_atoms = holo_res_atoms.get((holo_c, resnum), {})
        if "CA" in c_atoms and "CA" in h_atoms:
            ca_cand.append(c_atoms["CA"])
            ca_holo.append(h_atoms["CA"])
    if len(ca_cand) < 3:
        return float("nan")
    ca_cand, ca_holo = np.array(ca_cand), np.array(ca_holo)
    R, mc, rc = kabsch_fit(ca_cand, ca_holo)

    diffs = []
    for (apo_c, resnum), (holo_c, _) in zip(window, holo_window_keys):
        c_atoms = {nm: xyz for (rn, nm), xyz in cand_by_res.items() if rn == resnum}
        h_atoms = holo_res_atoms.get((holo_c, resnum), {})
        for nm, xyz in c_atoms.items():
            if nm in h_atoms:
                aligned = kabsch_apply(xyz.reshape(1, 3), R, mc, rc)[0]
                diffs.append(aligned - h_atoms[nm])
    if not diffs:
        return float("nan")
    diffs = np.array(diffs)
    return float(np.sqrt((diffs ** 2).sum(axis=1).mean()))


def run_target(target_name: str, rmsd_apo_to_holo_lookup: dict) -> dict:
    _log(f"=== {target_name} ===")
    target_config = load_target_config(target_name)
    apo_ca = clean_from_config(target_name, role="apo")
    holo_ca = clean_from_config(target_name, role="holo")

    holo_chains_for_labels = target_config.get("holo_chains") or target_config.get("chains") or sorted(set(holo_ca.chain_ids))
    import prody
    prody.confProDy(verbosity="none")
    holo_struct = prody.parsePDB(target_config["holo_pdb"], compressed=False).select(
        " or ".join(f"chain {c}" for c in holo_chains_for_labels)
    )
    holo_ca.ligand_groups = ligand_groups_from_atomgroup(holo_struct)
    holo_ca.heavy_atom_coords, holo_ca.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
        holo_struct, holo_chains_for_labels, holo_ca.resnums
    )

    labels = build_labels(apo_ca, holo_ca, target_config)
    if labels.pocket is None:
        return {"target": target_name, "error": "no resolvable pocket label"}
    window = _select_window(apo_ca, labels.pocket, max_size=WINDOW_MAX_SIZE)
    _log(f"window: {window}")

    apo_chains = target_config.get("apo_chains") or target_config.get("chains")
    work_dir = EVOEF2_BIN.parent
    base_pdb = work_dir / f"{target_name.lower()}_t210_base.pdb"
    design_chain = _write_full_atom_pdb_with_window_chain(target_config["apo_pdb"], apo_chains, window, base_pdb)
    target_set = {(design_chain, r) for (_c, r) in window}

    _log("known-answer check (firewall)...")
    kac = known_answer_check(target_name, target_config, apo_ca, holo_ca, window, work_dir)
    _log(f"known-answer: apo_druggability={kac['apo_druggability']}, holo_druggability={kac['holo_druggability']}, "
         f"objective_prefers_holo={kac['objective_prefers_holo']}")

    if not EVOEF2_BIN.exists():
        return {"target": target_name, "window": window, "known_answer_check": kac, "error": "EvoEF2 missing"}

    apo_idx = {(c, int(r)): i for i, (c, r) in enumerate(zip(apo_ca.chain_ids, apo_ca.resnums))}
    window_row_idx = [apo_idx[k] for k in window]
    eigvals, eigvecs = anm_modes(apo_ca.coords, cutoff=ANM_CUTOFF, n_modes=N_MODES)

    import prody
    apo_ag = prody.parsePDB(str(base_pdb))

    rmsd_native = rmsd_apo_to_holo_lookup.get(target_name)
    restarts_out = []
    any_hit = False
    for r_idx in range(RESTARTS):
        rng = random.Random(1000 * (r_idx + 1) + hash(target_name) % 997)
        _log(f"restart {r_idx+1}/{RESTARTS}...")
        res = run_sa_restart(target_name, apo_ag, window, window_row_idx, eigvecs, design_chain, target_set, work_dir, rng, r_idx)
        rmsd_reduction = float("nan")
        hit = False
        rmsd_to_holo = float("nan")
        if res["best_path"]:
            rmsd_to_holo = window_rmsd_to_holo(Path(res["best_path"]), target_config, window)
            if rmsd_native and rmsd_native > 1e-9 and np.isfinite(rmsd_to_holo):
                rmsd_reduction = 1.0 - rmsd_to_holo / rmsd_native
            best_score = res["best_score"]
            s = score_structure(Path(res["best_path"]), target_set, work_dir)
            overlap = s.get("overlap_frac", 0.0) or 0.0
            hit = bool(overlap >= OVERLAP_BAR and best_score >= DRUGGABILITY_BAR)
        success = bool((np.isfinite(rmsd_reduction) and rmsd_reduction >= RMSD_REDUCTION_BAR) or hit)
        any_hit = any_hit or success
        _log(f"restart {r_idx+1}: best_score={res['best_score']:.3f}, rmsd_to_holo={rmsd_to_holo}, "
             f"rmsd_reduction={rmsd_reduction}, fpocket_hit={hit}, success={success}")
        restarts_out.append({
            "restart": r_idx, "best_score": res["best_score"], "best_path": res["best_path"],
            "rmsd_to_holo": rmsd_to_holo, "rmsd_native": rmsd_native, "rmsd_reduction": rmsd_reduction,
            "fpocket_hit": hit, "success": success, "trace": res["trace"],
        })

    return {
        "target": target_name, "window": window, "known_answer_check": kac,
        "restarts": restarts_out, "any_restart_success": any_hit,
    }


def main():
    targets = TARGETS
    if len(sys.argv) > 1:
        targets = sys.argv[1:]

    t208_results_path = Path(__file__).resolve().parent.parent / "results/tasks/0208_apo_holo_decomposition" / "results.json"
    rmsd_lookup = {}
    if t208_results_path.exists():
        for r in json.loads(t208_results_path.read_text()):
            if "rmsd_apo_to_holo" in r:
                rmsd_lookup[r["target"]] = r["rmsd_apo_to_holo"]

    results = []
    out_dir = Path(__file__).resolve().parent.parent / "results/tasks/0210_coupled_search"
    out_dir.mkdir(exist_ok=True)
    for t in targets:
        try:
            r = run_target(t, rmsd_lookup)
        except Exception as exc:  # noqa: BLE001
            _log(f"{t} FAILED: {exc!r}")
            import traceback
            traceback.print_exc()
            r = {"target": t, "error": repr(exc)}
        results.append(r)
        (out_dir / "results.json").write_text(json.dumps(results, indent=2, default=str))

    _log("done")
    for r in results:
        _log(f"{r.get('target')}: any_restart_success={r.get('any_restart_success', r.get('error'))}")


if __name__ == "__main__":
    main()
