#!/usr/bin/env python3
"""TASK-0278 -- BCR-ABL1's own headline numbers, native `1OPL` (MYR present,
the incumbent apo, kept per this task's own decision -- see Done) vs a
computational control with MYR removed, disclosed explicitly as NOT a real
apo structure (per this task's own Constraint: "do not pick (c) silently").

Quantifies Scope item 5: how much of the apo-side fpocket signal survives
once the pocket is not pre-opened by the bound myristate.

Reuses, does not re-derive: `allostery.clean.load_target_config`/
`clean_from_config`, `allostery.labels.build_labels`/
`ligand_groups_from_atomgroup`/`protein_heavy_atoms_by_residue` (the exact
window/label construction [[TASK-0230]] and every downstream task use),
`task0163_external_baseline_scoring._run_fpocket`,
`task0204_rotamer_repack_baseline._best_druggability_at_window`/`_is_hit`,
`task0249_composite_dumb_baseline.fpocket_druggability_per_residue`/`z`
(the per-residue predictor-style AUC, not just the single best-window
score) and `allostery.metrics.auc`.
"""
from __future__ import annotations

import json
import sys
import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import prody

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

prody.confProDy(verbosity="none")

from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.labels import build_labels, ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue  # noqa: E402
from allostery.metrics import auc  # noqa: E402

from task0163_external_baseline_scoring import _run_fpocket  # noqa: E402
from task0204_rotamer_repack_baseline import _best_druggability_at_window, _is_hit  # noqa: E402
from task0249_composite_dumb_baseline import z  # noqa: E402


def _fpocket_druggability_per_residue_by_chain(pockets: list, resnums: np.ndarray, chain: str = "A") -> np.ndarray:
    """Same aggregation rule as `task0249_composite_dumb_baseline.
    fpocket_druggability_per_residue` (max druggability_score over every
    pocket a residue belongs to), adapted to `task0163_external_baseline_
    scoring._run_fpocket`'s own `residues` key -- a set of (chain, resnum)
    tuples, not the plain-resnum-int `resnums` key TASK-0249's own version
    expects (that key comes from a different fpocket wrapper,
    `task0242_two_stage_dryrun.fpocket_candidates`, built for the frozen-22
    single-apo-chain convention). BCR_ABL1 is single-chain 'A' throughout
    this register's own targets.yaml config, so `chain` is fixed, not
    re-derived."""
    out = np.zeros(len(resnums), dtype=np.float64)
    lookup = {int(rn): i for i, rn in enumerate(resnums)}
    for p in pockets:
        d = p.get("druggability_score") or p.get("score")
        if d is None:
            continue
        for ch, rn in p["residues"]:
            if ch != chain:
                continue
            i = lookup.get(int(rn))
            if i is not None:
                out[i] = max(out[i], d)
    return out

TARGET = "BCR_ABL1"
OUT = _ROOT / "results/tasks/0278_apo_contents_audit"


def _load_apo_holo_labels():
    cfg = load_target_config(TARGET)
    apo = clean_from_config(TARGET, role="apo")
    holo = clean_from_config(TARGET, role="holo")
    chains = cfg.get("holo_chains") or cfg.get("chains")
    holo_struct = prody.parsePDB(cfg["holo_pdb"], compressed=False).select(
        " or ".join(f"chain {c}" for c in chains))
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)
    holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
        holo_struct, chains, holo.resnums)
    cutoff = float(cfg.get("pocket_contact_cutoff", 4.5))
    labels_obj = build_labels(apo, holo, cfg, cutoff=cutoff, target_name=TARGET)
    return cfg, apo, labels_obj


def _write_apo_pdb(cfg: dict, out_path: Path, strip_myr: bool) -> None:
    apo_chains = cfg.get("apo_chains") or cfg.get("chains")
    struct = prody.parsePDB(cfg["apo_pdb"], compressed=False)
    alt_locs = struct.getAltlocs()
    if alt_locs is not None and any(a not in ("", " ", "\x00") for a in alt_locs):
        struct = struct.select("altloc _ A") or struct
    chain_part = " and (" + " or ".join(f"chain {c}" for c in apo_chains) + ")"
    sel = f"(protein or hetero){chain_part}"
    if strip_myr:
        sel = f"({sel}) and not (resname MYR)"
    struct_out = struct.select(sel)
    prody.writePDB(str(out_path), struct_out)


def run_variant(cfg: dict, apo, labels_obj, strip_myr: bool) -> dict:
    resn = np.asarray(apo.resnums)
    pocket_resnums = set(int(r) for r in resn[np.asarray(labels_obj.pocket)])
    target_set = {("A", r) for r in pocket_resnums}  # BCR_ABL1 is single-chain 'A' throughout this register

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        pdb_path = tmp / f"bcr_abl1_{'no_myr' if strip_myr else 'native'}.pdb"
        _write_apo_pdb(cfg, pdb_path, strip_myr)
        pockets = _run_fpocket(pdb_path, tmp)
        if isinstance(pockets, dict):
            return {"error": pockets["error"]}
        overlap, drug = _best_druggability_at_window(pockets, target_set)
        window_result = {
            "overlap_frac": overlap, "druggability_score": drug,
            "hit": _is_hit(overlap, drug), "n_pockets": len(pockets),
        }

        # per-residue predictor-style AUC (Scope item 5's own "how much
        # survives" quantity), same aggregation TASK-0249 uses elsewhere
        fpocket_res = _fpocket_druggability_per_residue_by_chain(pockets, resn)
        seed = np.where(np.asarray(labels_obj.active_site))[0] if labels_obj.active_site is not None else np.array([], dtype=int)
        m = np.ones(len(resn), dtype=bool)
        m[seed] = False
        y = np.asarray(labels_obj.pocket).astype(int)[m]
        residue_auc = float(auc(z(fpocket_res)[m], y))

    return {"window_result": window_result, "residue_level_fpocket_auc": residue_auc,
            "n_pocket_positive": int(y.sum()), "n_residues_scored": int(len(y))}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg, apo, labels_obj = _load_apo_holo_labels()
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        print("BCR_ABL1: no resolvable pocket label")
        return 1

    print("=== BCR_ABL1, native 1OPL (MYR present, the incumbent) ===")
    native = run_variant(cfg, apo, labels_obj, strip_myr=False)
    print(json.dumps(native, indent=1))

    print("\n=== BCR_ABL1, MYR computationally stripped (NOT a real apo -- a control) ===")
    no_myr = run_variant(cfg, apo, labels_obj, strip_myr=True)
    print(json.dumps(no_myr, indent=1))

    out = {"target": TARGET, "native_1OPL_with_MYR": native, "MYR_stripped_control": no_myr}
    (OUT / "bcr_abl1_myr_strip.json").write_text(json.dumps(out, indent=2))

    d_native = native.get("window_result", {}).get("druggability_score")
    d_stripped = no_myr.get("window_result", {}).get("druggability_score")
    au_native = native.get("residue_level_fpocket_auc")
    au_stripped = no_myr.get("residue_level_fpocket_auc")
    print(f"\nWindow druggability_score: native={d_native}  MYR-stripped={d_stripped}")
    print(f"Residue-level fpocket AUC: native={au_native}  MYR-stripped={au_stripped}")
    print(f"\nWrote {OUT / 'bcr_abl1_myr_strip.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
