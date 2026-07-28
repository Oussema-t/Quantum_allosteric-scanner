#!/usr/bin/env python3
"""TASK-0163 -- score fpocket + PocketMiner against this project's own
holo-defined pocket labels, same AUC/floor convention `run_challenge.py`
already uses (`labels.build_labels`, `baselines.degree_centrality`/
`euclid_from_seed_centroid`/`hop_from_seed`, `metrics.auc`).

fpocket: run locally (`__WORK_IN_PROGRESS__/tools/fpocket/bin/fpocket`,
built from source this task, see Done section) against a full-atom apo
PDB (same altloc/chain/protein filtering `clean.clean()` uses -- fpocket
needs side-chain atoms for cavity detection, unlike the rest of this
project's Cα-only pipeline). Per-pocket "Score" (cavity openness, not
druggability) is assigned to every residue in that pocket's atom-membership
file (`pocketN_atm.pdb`); a residue in multiple pockets takes the max;
unassigned residues score 0. Mapped onto `apo.resnums` by (chain, resnum)
lookup, not position -- this project's own `clean()` can drop/reorder
residues fpocket's raw-PDB path would not.

PocketMiner: predictions already computed in a separate environment
(`/home/bchmura/PROJECTS/PocketMiner/`, TASK-0163's own separate-repo
approach -- old TF/numpy pins conflict with this repo's Python 3.12
stack). Loaded from the `.npy` files there and mapped onto `apo.resnums`
by resSeq (parsed from the exact chain-A PDB fed to PocketMiner), not
position, for the same reason.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.baselines import (  # noqa: E402
    _parse_fpocket_info,
    degree_centrality,
    euclid_from_seed_centroid,
    hop_from_seed,
)
from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.labels import build_labels, ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue  # noqa: E402
from allostery.metrics import auc  # noqa: E402

FPOCKET_BIN = Path(__file__).resolve().parent.parent / "tools" / "fpocket" / "bin" / "fpocket"
POCKETMINER_DIR = Path("/home/bchmura/PROJECTS/PocketMiner")
POCKETMINER_STRUCS_DIR = POCKETMINER_DIR / "structures"
POCKETMINER_PREDS_DIR = POCKETMINER_DIR / "predictions"
DEFAULT_CUTOFF = 10.0
DEFAULT_POCKET_CUTOFF = 4.5

TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]


def _log(msg: str) -> None:
    print(f"[task0163] {msg}", flush=True)


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


def _write_full_atom_apo_pdb(target_config: dict, apo_chains, out_path: Path) -> None:
    """Same altloc/protein/chain filtering as `clean.clean()`, but keeps
    every atom (not just Cα) -- fpocket needs side-chain geometry."""
    import prody

    prody.confProDy(verbosity="none")
    struct = prody.parsePDB(target_config["apo_pdb"], compressed=False)
    alt_locs = struct.getAltlocs()
    if alt_locs is not None and any(a not in ("", " ", "\x00") for a in alt_locs):
        struct = struct.select("altloc _ A") or struct
    chain_part = " and (" + " or ".join(f"chain {c}" for c in apo_chains) + ")"
    struct_clean = struct.select(f"protein{chain_part}")
    prody.writePDB(str(out_path), struct_clean)


def _run_fpocket(pdb_path: Path, work_dir: Path) -> list:
    result = subprocess.run(
        [str(FPOCKET_BIN), "-f", str(pdb_path)],
        cwd=work_dir, capture_output=True, text=True, timeout=180,
    )
    if result.returncode != 0:
        return {"error": f"fpocket exited {result.returncode}: {result.stderr.strip()[:500]}"}

    out_dir = work_dir / f"{pdb_path.stem}_out"
    info_file = out_dir / f"{pdb_path.stem}_info.txt"
    if not info_file.exists():
        return {"error": f"fpocket produced no info file at {info_file}"}
    pockets = _parse_fpocket_info(info_file.read_text())

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
    return pockets


def _fpocket_per_residue_scores(pockets: list, resnums: np.ndarray, chain_ids: list) -> np.ndarray:
    scores = np.zeros(len(resnums), dtype=np.float64)
    lookup = {}
    for i, (rn, ch) in enumerate(zip(resnums, chain_ids)):
        lookup.setdefault((ch, int(rn)), []).append(i)
    for p in pockets:
        s = p["score"]
        if s is None:
            continue
        for key in p["residues"]:
            for i in lookup.get(key, []):
                scores[i] = max(scores[i], s)
    return scores


def _pocketminer_per_residue_scores(target_name: str, resnums: np.ndarray, chain_ids: list) -> tuple:
    """Loads the PocketMiner prediction + the exact PDB fed to it, aligns
    by resSeq (parsed from that PDB's own CA records, file order == the
    order PocketMiner's mdtraj-loaded residue axis uses), maps onto
    `resnums`/`chain_ids` by (chain, resnum) lookup. Returns
    (scores, n_matched, n_total_apo, n_pred_residues)."""
    preds_path = POCKETMINER_PREDS_DIR / f"{target_name}-preds.npy"
    if not preds_path.exists():
        return None, 0, len(resnums), 0
    preds = np.load(preds_path).flatten()

    struc_map = {"KRAS_G12C": "4OBE_A.pdb", "BCR_ABL1": "1OPL_A.pdb", "CARDIAC_MYOSIN": "8QYP_A.pdb"}
    pdb_path = POCKETMINER_STRUCS_DIR / struc_map[target_name]
    pred_resseq = []
    seen = set()
    for line in pdb_path.read_text().splitlines():
        # HETATM, not just ATOM: modified residues (e.g. 8QYP's M3L,
        # trimethyllysine, renamed to LYS before this file was fed to
        # PocketMiner -- TASK-0163 Done section) are HETATM records even
        # though mdtraj's "protein" selection (and this project's own
        # `clean()`) treats them as ordinary chain members once the name
        # is a canonical residue. Missing this line undercounted by 2 on
        # CARDIAC_MYOSIN (704 parsed vs. 706 actual mdtraj residues).
        if line.startswith(("ATOM", "HETATM")) and line[12:16].strip() == "CA":
            chain = line[21].strip()
            resnum = int(line[22:26])
            key = (chain, resnum)
            if key not in seen:
                seen.add(key)
                pred_resseq.append(key)

    if len(pred_resseq) != len(preds):
        return None, 0, len(resnums), len(preds)

    pred_lookup = dict(zip(pred_resseq, preds))
    scores = np.zeros(len(resnums), dtype=np.float64)
    n_matched = 0
    for i, (rn, ch) in enumerate(zip(resnums, chain_ids)):
        key = (ch, int(rn))
        if key in pred_lookup:
            scores[i] = pred_lookup[key]
            n_matched += 1
    return scores, n_matched, len(resnums), len(preds)


def score_target(target_name: str) -> dict:
    _log(f"{target_name}: loading target config + apo/holo...")
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))

    apo, holo = _load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None:
        return {"target": target_name, "error": "build_labels returned pocket=None"}

    pocket = labels_obj.pocket.astype(int)
    active_site_idx = np.where(labels_obj.active_site)[0]
    source = np.sort(active_site_idx)

    floor_scores = {
        "degree_centrality": degree_centrality(apo.coords, cutoff=cutoff),
        "euclid_from_seed_centroid": euclid_from_seed_centroid(apo.coords, source),
        "hop_from_seed": hop_from_seed(apo.coords, source, cutoff=cutoff),
    }
    floor_aucs = {name: auc(s, pocket) for name, s in floor_scores.items()}
    floor_auc = max(floor_aucs.values())

    # --- fpocket ---
    _log(f"{target_name}: running fpocket...")
    apo_chains = target_config.get("apo_chains") or target_config.get("chains")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        pdb_path = tmp / f"{target_name}_apo.pdb"
        _write_full_atom_apo_pdb(target_config, apo_chains, pdb_path)
        pockets = _run_fpocket(pdb_path, tmp)
        if isinstance(pockets, dict) and "error" in pockets:
            fpocket_result = {"error": pockets["error"]}
        else:
            fp_scores = _fpocket_per_residue_scores(pockets, apo.resnums, apo.chain_ids)
            fpocket_result = {
                "auc": auc(fp_scores, pocket),
                "n_pockets": len(pockets),
                "n_residues_assigned": int((fp_scores != 0).sum()),
            }
    _log(f"{target_name}: fpocket -- {fpocket_result}")

    # --- PocketMiner ---
    pm_scores, n_matched, n_total, n_pred = _pocketminer_per_residue_scores(
        target_name, apo.resnums, apo.chain_ids
    )
    if pm_scores is None:
        pocketminer_result = {
            "error": f"residue-count mismatch or missing prediction file "
                     f"(apo N={n_total}, PocketMiner prediction N={n_pred})"
        }
    else:
        pocketminer_result = {
            "auc": auc(pm_scores, pocket),
            "n_matched": n_matched,
            "n_total_apo": n_total,
        }
    _log(f"{target_name}: PocketMiner -- {pocketminer_result}")

    return {
        "target": target_name,
        "n_residues": len(apo.resnums),
        "pocket_size": int(pocket.sum()),
        "floor_aucs": floor_aucs,
        "floor_auc_max": floor_auc,
        "fpocket": fpocket_result,
        "pocketminer": pocketminer_result,
    }


def main():
    results = {}
    for t in TARGETS:
        try:
            results[t] = score_target(t)
        except Exception as e:
            import traceback
            traceback.print_exc()
            results[t] = {"target": t, "error": repr(e)}

    out_dir = Path(__file__).resolve().parent.parent / "results_task0163_external_baselines"
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / "results.json", "w") as f:
        json.dump(results, f, indent=2, default=float)
    _log(f"wrote {out_dir / 'results.json'}")

    print("\n=== TASK-0163 comparison table ===")
    for t, r in results.items():
        if "error" in r:
            print(f"{t}: ERROR {r['error']}")
            continue
        fp = r["fpocket"]
        pm = r["pocketminer"]
        fp_s = f"{fp['auc']:.4f}" if "auc" in fp else f"ERROR: {fp.get('error')}"
        pm_s = f"{pm['auc']:.4f}" if "auc" in pm else f"ERROR: {pm.get('error')}"
        print(f"{t}: floor={r['floor_auc_max']:.4f}  fpocket={fp_s}  pocketminer={pm_s}")


if __name__ == "__main__":
    main()
