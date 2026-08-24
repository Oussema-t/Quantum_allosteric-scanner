"""TASK-0238 follow-up -- "is it still geometry > CTQW, and how much does each
actually contribute?"

Three separate quantities, kept separate because they answer different things:

  1. R^2(CTQW ~ geometry). How much of the CTQW score VECTOR is a linear
     function of the three geometric baselines. This is redundancy, not skill.
  2. AUC of the CTQW RESIDUAL after the geometric baselines are regressed out.
     This is what CTQW knows that geometry does not. If it collapses to ~0.5,
     CTQW is geometry in a costume.
  3. AUC of geometry+CTQW combined (OLS stack) vs geometry alone. This is the
     incremental discrimination actually delivered.

Unexplained is then reported honestly against two anchors: chance (0.5) and
fpocket (a 2009 classical geometric tool, this register's external upper mark).
"""
from __future__ import annotations
import sys, warnings, json
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path: sys.path.insert(0, str(_p))
import yaml, prody; prody.confProDy(verbosity="none")
CAND = yaml.safe_load((_ROOT/"config"/"candidate_targets_task0216.yaml").read_text())["targets"]
from allostery import clean as _clean
_o = _clean.load_target_config
_clean.load_target_config = lambda n, p=None: CAND[n] if n in CAND else _o(n, p)
from allostery.clean import clean_from_config
from allostery.labels import (build_labels, holo_pocket_mask, terminal_mask,
                              ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue)
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed
from allostery.hamiltonians import build_H_new
from allostery.propagators import time_averaged_ctqw_converged
from allostery.metrics import auc
from backend import active_site as backend_as

FPOCKET = {"KRAS_G12C": 0.8348, "BCR_ABL1": 0.8596, "CARDIAC_MYOSIN": 0.5345, "HIV1_RT": None}

def z(v):
    v = np.asarray(v, float); s = v.std()
    return (v - v.mean()) / (s if s > 1e-12 else 1.0)

def prep(t):
    cfg = dict(CAND[t]) if t in CAND else dict(_o(t))
    apo = clean_from_config(t, role="apo"); holo = clean_from_config(t, role="holo")
    ch = cfg.get("holo_chains") or cfg.get("chains")
    st = prody.parsePDB(cfg["holo_pdb"], compressed=False).select(" or ".join(f"chain {c}" for c in ch))
    holo.ligand_groups = ligand_groups_from_atomgroup(st)
    holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(st, ch, holo.resnums)
    if t in CAND:
        det = backend_as.detect_active_site(cfg["apo_pdb"], chain=(cfg.get("apo_chains") or ch)[0])
        rn = np.asarray(apo.resnums)
        sd = np.sort(np.where(np.isin(rn, list(det.get("active_site") or [])))[0])
        raw = holo_pocket_mask(apo, holo, cfg["drug_ligand"], cutoff=float(cfg["pocket_contact_cutoff"]))
        n = len(rn); a = np.zeros(n, bool); a[sd] = True
        y = (raw & ~a & ~terminal_mask(n, 0.05)).astype(int)
    else:
        lab = build_labels(apo, holo, cfg, cutoff=float(cfg.get("pocket_contact_cutoff", 4.5)))
        sd = np.where(lab.active_site)[0]; y = lab.pocket.astype(int)
    return cfg, apo, sd, y

print(f"{'target':<16}{'geom':>7}{'ctqw':>7}{'resid':>7}{'stack':>7}{'R2':>7}{'dAUC':>7}{'fpocket':>8}")
out = {}
for t in ("KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "HIV1_RT"):
    cfg, apo, sd, y = prep(t)
    c = apo.coords; cut = float(cfg.get("enm_cutoff", 8.0)); n = len(c)
    G = np.column_stack([z(degree_centrality(c, cutoff=cut)),
                         z(euclid_from_seed_centroid(c, sd)),
                         z(hop_from_seed(c, sd, cutoff=cut))])
    q = z(time_averaged_ctqw_converged(build_H_new(c, apo.bfactors, cutoff=cut), source=sd, coherent=False))
    m = np.ones(n, bool); m[sd] = False
    X = np.column_stack([G, np.ones(n)])
    beta, *_ = np.linalg.lstsq(X[m], q[m], rcond=None)
    fit = X[m] @ beta; resid = q[m] - fit
    ss = ((q[m] - q[m].mean())**2).sum()
    r2 = 1.0 - (resid**2).sum() / ss if ss > 1e-12 else 0.0
    geom = max(float(auc(G[m, i], y[m])) for i in range(3))
    a_q = float(auc(q[m], y[m]))
    # orient residual so higher = more pocket-like, then score
    a_r = float(auc(resid, y[m])); a_r = max(a_r, 1 - a_r)
    Xs = np.column_stack([G[m], q[m], np.ones(m.sum())])
    bs, *_ = np.linalg.lstsq(Xs, y[m].astype(float), rcond=None)
    a_s = float(auc(Xs @ bs, y[m]))
    Xg = np.column_stack([G[m], np.ones(m.sum())])
    bg, *_ = np.linalg.lstsq(Xg, y[m].astype(float), rcond=None)
    a_g = float(auc(Xg @ bg, y[m]))
    fp = FPOCKET[t]
    out[t] = {"geom_best": geom, "ctqw": a_q, "ctqw_residual": a_r, "stack": a_s,
              "geom_stack": a_g, "r2_ctqw_on_geom": float(r2), "d_auc_stack": a_s - a_g,
              "fpocket": fp}
    print(f"{t:<16}{geom:>7.4f}{a_q:>7.4f}{a_r:>7.4f}{a_s:>7.4f}{r2:>7.3f}{a_s-a_g:>+7.4f}"
          f"{(f'{fp:.4f}' if fp else '   n/a'):>8}")
(_ROOT/"results/tasks/0238_hiv1rt/geometry_vs_ctqw.json").write_text(json.dumps(out, indent=1))
print("\nlegend: geom=best single geometric baseline | ctqw=raw CTQW | resid=CTQW after")
print("geometry regressed out | stack=OLS(geom+ctqw) | R2=share of CTQW vector linearly")
print("explained by geometry | dAUC=stack minus OLS(geom alone) = CTQW's incremental skill")
