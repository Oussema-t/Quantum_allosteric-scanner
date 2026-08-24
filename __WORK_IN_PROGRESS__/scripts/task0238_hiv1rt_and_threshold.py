"""TASK-0238 -- HIV1_RT through this register's own pipeline, and the
calibration question: how strict is our threshold?

Leg A: independent run. Our structures, our labels, our floor, our nulls.
Leg B: the same score's p-value under BOTH nulls side by side --
       scattered (label permutation, the other thread's) and compact /
       graph-walk (ours). That single comparison localises the entire
       disagreement to one number, without touching anyone else's code.

Constraint inherited from the task file: a positive here is as reportable as
a negative. Nothing below is tuned after seeing a number.
"""
from __future__ import annotations
import json, sys, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import yaml, prody
prody.confProDy(verbosity="none")

CAND = yaml.safe_load((_ROOT / "config" / "candidate_targets_task0216.yaml").read_text())["targets"]
from allostery import clean as _clean
_orig = _clean.load_target_config
_clean.load_target_config = lambda n, p=None: CAND[n] if n in CAND else _orig(n, p)

from allostery.clean import clean_from_config
from allostery.labels import (build_labels, holo_pocket_mask, terminal_mask,
                              ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue)
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed
from allostery.hamiltonians import build_H_new
from allostery.propagators import time_averaged_ctqw_converged
from allostery.lowmode_predictor import dcc_low
from allostery.metrics import auc
from allostery.nulls import compact_patch, graph_walk_patch, build_adjacency
from backend import active_site as backend_as

N_PERM = 2000
OUT = _ROOT / "results/tasks/0238_hiv1rt"

def prep(name):
    cfg = CAND[name]
    apo = clean_from_config(name, role="apo"); holo = clean_from_config(name, role="holo")
    ch = cfg["holo_chains"]
    st = prody.parsePDB(cfg["holo_pdb"], compressed=False).select(" or ".join(f"chain {c}" for c in ch))
    holo.ligand_groups = ligand_groups_from_atomgroup(st)
    # Heavy atoms are attached UNCONDITIONALLY. `holo_pocket_mask` contacts them
    # against *holo* coords and maps holo->apo by Needleman-Wunsch, so it needs no
    # equal-length precondition. (The same-length guard in
    # scripts/task0216_score_new_pairs.py:110 is required only for
    # `functional_indices`, which contacts holo heavy atoms against *apo* coords.
    # Applying that guard to the pocket too silently drops the label to a
    # Calpha-only approximation -- labels.py's own docstring measures that at
    # 9/21 pocket residues recovered on KRAS_G12C.)
    holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(st, ch, holo.resnums)
    det = backend_as.detect_active_site(cfg["apo_pdb"], chain=cfg["apo_chains"][0])
    resn = np.asarray(apo.resnums)
    seed = np.sort(np.where(np.isin(resn, list(det.get("active_site") or [])))[0])
    praw = holo_pocket_mask(apo, holo, cfg["drug_ligand"], cutoff=cfg["pocket_contact_cutoff"])
    n = len(resn)
    act = np.zeros(n, bool); act[seed] = True
    pocket = (praw & ~act & ~terminal_mask(n, 0.05)) if praw is not None else None
    return cfg, apo, holo, seed, pocket, det

def null_p(score, pocket, coords, mask, y, kind, adjacency=None, rng=None):
    n = len(score); size = int(pocket.sum()); obs = auc(score[mask], y[mask]); hits = 0
    for _ in range(N_PERM):
        if kind == "scattered":
            idx = rng.choice(n, size=size, replace=False)
        elif kind == "compact":
            idx = compact_patch(coords, size, rng)
        else:
            idx = graph_walk_patch(adjacency, size, rng)
        lab = np.zeros(n, int); lab[idx] = 1
        if auc(score[mask], lab[mask]) >= obs: hits += 1
    return float(obs), (1 + hits) / (1 + N_PERM)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    name = "HIV1_RT"
    cfg, apo, holo, seed, pocket, det = prep(name)
    coords, cut, n = apo.coords, float(cfg["enm_cutoff"]), len(apo.resnums)
    print(f"=== {name}: {cfg['apo_pdb']} -> {cfg['holo_pdb']}, drug {cfg['drug_ligand']} ===")
    print(f"  N={n}  seed={len(seed)} (UniProt, {det.get('source')})  pocket={int(pocket.sum())}")
    y = pocket.astype(int); mask = np.ones(n, bool); mask[seed] = False

    floors = {"degree": degree_centrality(coords, cutoff=cut),
              "euclid_from_seed": euclid_from_seed_centroid(coords, seed),
              "hop_from_seed": hop_from_seed(coords, seed, cutoff=cut)}
    fa = {k: float(auc(v[mask], y[mask])) for k, v in floors.items()}
    max_floor = max(fa.values())
    print(f"  FLOOR (max of 3): {max_floor:.4f}   {({k: round(v,3) for k,v in fa.items()})}")

    scores = {}
    H = build_H_new(coords, apo.bfactors, cutoff=cut)
    scores["ctqw_converged"] = time_averaged_ctqw_converged(H, source=seed, coherent=False)
    scores["dcc_low_k10"] = dcc_low(coords, seed, cutoff=cut, k_modes=10)

    adjacency = build_adjacency(coords, 8.0)
    res = {"target": name, "n": n, "n_seed": int(len(seed)), "n_pocket": int(y.sum()),
           "seed_source": det.get("source"), "floor_aucs": fa, "max_floor": max_floor, "scores": {}}
    print(f"\n  {'observable':<18} {'AUC':>7} {'vs floor':>9} | {'p(scattered)':>13} {'p(compact)':>11} {'p(graphwalk)':>13}")
    for sname, sc in scores.items():
        row = {}
        for kind in ("scattered", "compact", "graphwalk"):
            a, p = null_p(sc, pocket, coords, mask, y, kind, adjacency, np.random.default_rng(123))
            row["auc"] = a; row[f"p_{kind}"] = p
        clears = "CLEARS" if row["auc"] > max_floor else "below"
        print(f"  {sname:<18} {row['auc']:>7.4f} {clears:>9} | {row['p_scattered']:>13.4f} "
              f"{row['p_compact']:>11.4f} {row['p_graphwalk']:>13.4f}")
        res["scores"][sname] = row
    (OUT / "results.json").write_text(json.dumps(res, indent=1))
    print(f"\n  written: {OUT/'results.json'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
