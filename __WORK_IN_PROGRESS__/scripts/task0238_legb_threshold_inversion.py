"""TASK-0238 Leg B -- "How strict is our threshold? Is it too strict?"

Three questions, none of which require touching anyone else's code:

  B1 WIRING CHECK. Reproduce a number the register already published
     (KRAS_G12C max_floor = 0.4818) through this exact code path. If it does
     not reproduce, every other number here is void.

  B2 IS THE FLOOR ITSELF SIGNIFICANT? Push the three floor baselines through
     the SAME compact null the observables are judged by. If `hop_from_seed`
     is itself p~0.2, then "below floor" and "null under compact" are not two
     independent failures -- they are one, and the floor gate is not adding
     the strictness we credit it with.

  B3 THRESHOLD INVERSION. Not "does it pass", but "what would have to be true
     for it to pass". A ladder of the four gates, each relaxed one at a time,
     plus a parameter sweep over enm_cutoff / pocket cutoff / k_modes /
     coherence, reporting the LOOSEST setting at which HIV1_RT flips positive
     and whether that setting is defensible or merely permissive.

Pre-registered before any number was seen: the sweep grid below is fixed, and
"positive" means AUC > max_floor AND p_compact < 0.05. No post-hoc grid edits.
"""
from __future__ import annotations
import json, sys, warnings, itertools
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
from allostery.labels import (holo_pocket_mask, terminal_mask, build_labels,
                              ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue)
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed
from allostery.hamiltonians import build_H_new
from allostery.propagators import time_averaged_ctqw_converged
from allostery.lowmode_predictor import dcc_low
from allostery.metrics import auc
from allostery.nulls import compact_patch, build_adjacency, graph_walk_patch
from backend import active_site as backend_as

N_PERM = 2000
OUT = _ROOT / "results/tasks/0238_hiv1rt"

# --- pre-registered sweep grid (fixed before results were seen) -------------
GRID_ENM    = [7.0, 8.0, 9.0, 10.0]
GRID_POCKET = [4.0, 4.5, 5.0, 6.0]
GRID_KMODES = [5, 10, 20]
GRID_COHERENT = [False, True]


def load(name, pocket_cut=None):
    cfg = dict(CAND[name]) if name in CAND else None
    if cfg is None:
        from allostery.clean import load_target_config as ltc
        cfg = dict(ltc(name))
    apo = clean_from_config(name, role="apo"); holo = clean_from_config(name, role="holo")
    ch = cfg.get("holo_chains") or cfg.get("chains")
    st = prody.parsePDB(cfg["holo_pdb"], compressed=False).select(" or ".join(f"chain {c}" for c in ch))
    holo.ligand_groups = ligand_groups_from_atomgroup(st)
    holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(st, ch, holo.resnums)
    return cfg, apo, holo


def seed_pocket(cfg, apo, holo, pocket_cut):
    det = backend_as.detect_active_site(cfg["apo_pdb"], chain=(cfg.get("apo_chains") or cfg["chains"])[0])
    resn = np.asarray(apo.resnums)
    seed = np.sort(np.where(np.isin(resn, list(det.get("active_site") or [])))[0])
    raw = holo_pocket_mask(apo, holo, cfg["drug_ligand"], cutoff=pocket_cut)
    n = len(resn); act = np.zeros(n, bool); act[seed] = True
    return seed, (raw & ~act & ~terminal_mask(n, 0.05)), det


def floors_of(coords, seed, cut, mask, y):
    f = {"degree": degree_centrality(coords, cutoff=cut),
         "euclid_from_seed": euclid_from_seed_centroid(coords, seed),
         "hop_from_seed": hop_from_seed(coords, seed, cutoff=cut)}
    return f, {k: float(auc(v[mask], y[mask])) for k, v in f.items()}


def pval(score, size, coords, mask, y, kind, adjacency=None):
    rng = np.random.default_rng(123); n = len(score); obs = auc(score[mask], y[mask]); hits = 0
    for _ in range(N_PERM):
        idx = (rng.choice(n, size=size, replace=False) if kind == "scattered"
               else compact_patch(coords, size, rng) if kind == "compact"
               else graph_walk_patch(adjacency, size, rng))
        lab = np.zeros(n, int); lab[idx] = 1
        if auc(score[mask], lab[mask]) >= obs: hits += 1
    return float(obs), (1 + hits) / (1 + N_PERM)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    res = {}

    # ---------------- B1 wiring check ----------------
    print("=== B1  WIRING CHECK: KRAS_G12C max_floor, register value 0.4818 ===")
    cfg, apo, holo = load("KRAS_G12C")
    lab = build_labels(apo, holo, cfg, cutoff=float(cfg.get("pocket_contact_cutoff", 4.5)))
    sd = np.where(lab.active_site)[0]; y = lab.pocket.astype(int)
    m = np.ones(len(apo.coords), bool); m[sd] = False
    _, fa = floors_of(apo.coords, sd, float(cfg.get("enm_cutoff", 8.0)), m, y)
    mf = max(fa.values())
    ok = abs(mf - 0.4818) < 0.005
    print(f"  recomputed max_floor = {mf:.4f}   register = 0.4818   "
          f"-> {'MATCH' if ok else 'MISMATCH -- everything below is void'}")
    print(f"  {({k: round(v,4) for k,v in fa.items()})}")
    res["b1_wiring"] = {"kras_max_floor_recomputed": mf, "register": 0.4818,
                        "match": bool(ok), "floors": fa}

    # ---------------- HIV1_RT baseline at standard settings ----------------
    cfg, apo, holo = load("HIV1_RT")
    cut0, pc0 = float(cfg["enm_cutoff"]), float(cfg["pocket_contact_cutoff"])
    seed, pocket, det = seed_pocket(cfg, apo, holo, pc0)
    coords = apo.coords; n = len(coords)
    y = pocket.astype(int); mask = np.ones(n, bool); mask[seed] = False
    fobj, fa = floors_of(coords, seed, cut0, mask, y); mf = max(fa.values())
    adjacency = build_adjacency(coords, 8.0)
    size = int(y.sum())

    # ---------------- B2 are the FLOORS themselves significant? -------------
    print("\n=== B2  THE FLOOR UNDER ITS OWN NULL (HIV1_RT) ===")
    print(f"  {'baseline':<18} {'AUC':>7} {'p(scattered)':>13} {'p(compact)':>11}")
    b2 = {}
    for k, v in fobj.items():
        a, ps = pval(v, size, coords, mask, y, "scattered")
        _, pc = pval(v, size, coords, mask, y, "compact")
        b2[k] = {"auc": a, "p_scattered": ps, "p_compact": pc}
        print(f"  {k:<18} {a:>7.4f} {ps:>13.4f} {pc:>11.4f}")
    res["b2_floor_calibration"] = b2

    # ---------------- B3 threshold inversion ----------------
    H = build_H_new(coords, apo.bfactors, cutoff=cut0)
    sc = time_averaged_ctqw_converged(H, source=seed, coherent=False)
    a0, p_sc = pval(sc, size, coords, mask, y, "scattered")
    _, p_cp = pval(sc, size, coords, mask, y, "compact")
    print(f"\n=== B3  THRESHOLD INVERSION -- CTQW AUC {a0:.4f}, floor {mf:.4f} "
          f"(deficit {mf-a0:+.4f}) ===")
    gates = [
        ("as-published (floor gate + compact null, a=0.05)", a0 > mf and p_cp < 0.05),
        ("relax NULL only -> scattered", a0 > mf and p_sc < 0.05),
        ("relax FLOOR only -> drop floor gate, keep compact", p_cp < 0.05),
        ("relax BOTH -> scattered null, no floor gate", p_sc < 0.05),
        ("relax both + Bonferroni x28 (a=0.0018)", p_sc < 0.05/28),
    ]
    for lbl, verdict in gates:
        print(f"  {'POSITIVE' if verdict else 'negative':>9}  {lbl}")
    res["b3_gates"] = {lbl: bool(v) for lbl, v in gates}
    res["b3_ctqw"] = {"auc": a0, "max_floor": mf, "floor_aucs": fa,
                      "p_scattered": p_sc, "p_compact": p_cp,
                      "floor_deficit": mf - a0}

    # ---------------- B3b parameter permissiveness sweep -------------------
    print(f"\n=== B3b  PARAMETER SWEEP -- does ANY setting give AUC>floor AND p_compact<0.05? ===")
    print(f"  {'enm':>5} {'pkt':>5} {'obs':<16} {'AUC':>7} {'floor':>7} {'p_cmp':>7}  verdict")
    sweep = []
    for pc in GRID_POCKET:
        s2, pk2, _ = seed_pocket(cfg, apo, holo, pc)
        y2 = pk2.astype(int); m2 = np.ones(n, bool); m2[s2] = False
        sz2 = int(y2.sum())
        if sz2 < 3:
            continue
        for enm in GRID_ENM:
            _, fa2 = floors_of(coords, s2, enm, m2, y2); mf2 = max(fa2.values())
            cands = {}
            H2 = build_H_new(coords, apo.bfactors, cutoff=enm)
            for coh in GRID_COHERENT:
                cands[f"ctqw{'_coh' if coh else ''}"] = time_averaged_ctqw_converged(
                    H2, source=s2, coherent=coh)
            for km in GRID_KMODES:
                cands[f"dcc_low_k{km}"] = dcc_low(coords, s2, cutoff=enm, k_modes=km)
            for oname, ov in cands.items():
                a, p = pval(ov, sz2, coords, m2, y2, "compact")
                pos = (a > mf2) and (p < 0.05)
                sweep.append({"pocket_cut": pc, "enm": enm, "obs": oname, "auc": a,
                              "max_floor": mf2, "p_compact": p, "n_pocket": sz2,
                              "positive": bool(pos)})
                if pos or a > mf2 or p < 0.05:
                    print(f"  {enm:>5.1f} {pc:>5.1f} {oname:<16} {a:>7.4f} {mf2:>7.4f} "
                          f"{p:>7.4f}  {'*** POSITIVE ***' if pos else ('beats floor' if a>mf2 else 'p<.05 only')}")
    npos = sum(s["positive"] for s in sweep)
    nbeat = sum(s["auc"] > s["max_floor"] for s in sweep)
    nsig = sum(s["p_compact"] < 0.05 for s in sweep)
    print(f"\n  {len(sweep)} configurations: {npos} positive, {nbeat} beat floor, {nsig} p_compact<0.05")
    best = max(sweep, key=lambda s: s["auc"] - s["max_floor"])
    print(f"  closest to positive: {best['obs']} enm={best['enm']} pkt={best['pocket_cut']} "
          f"AUC {best['auc']:.4f} vs floor {best['max_floor']:.4f} (deficit {best['max_floor']-best['auc']:+.4f}), "
          f"p_compact {best['p_compact']:.4f}")
    res["b3b_sweep"] = {"n_configs": len(sweep), "n_positive": npos,
                        "n_beat_floor": nbeat, "n_p_sig": nsig,
                        "closest": best, "all": sweep}

    (OUT / "legb_threshold_inversion.json").write_text(json.dumps(res, indent=1))
    print(f"\n  written: {OUT/'legb_threshold_inversion.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
