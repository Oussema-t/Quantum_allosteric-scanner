"""TASK-0216 step 3 -- re-run PTP1B's `dcc_low` with a REAL active site.

PTP1B carries the register's only surviving positive (`dcc_low` k=10,
p=0.0027 vs bar 0.003125, [[TASK-0201]]). TASK-0216's provenance audit found
its seed is the **top-5 highest-degree residues**, not an active site:
`targets.yaml` declared `func_ligand: ['pTyr / active-site Cys215
(descriptive marker, not a ligand code)']`, no ligand matched, and
`functional_indices` silently fell back.

Holo 1T49 contains only the allosteric drug (892) and MG -- there is no
substrate ligand to derive an active site from at all. The catalytic site is
UniProt-annotated, so it is taken from there
(`backend/active_site.py::detect_active_site`, source='uniprot'):
**[181, 215, 216, 217, 218, 219, 220, 221, 262]** -- Cys215 plus the P-loop,
identical on apo 1SUG and holo 1T49.

This computes `dcc_low` under BOTH seeds and reports them side by side. The
p-value is not recomputed here: the permutation null shuffles *pocket labels*,
not the seed, so [[TASK-0201]]'s p=0.0027 remains a valid test of "is this
score field associated with this pocket". What changes is what the score field
*is*. The question this answers is whether the association survives when the
seed is the actual catalytic site.

Both the seed AND the pocket label change: `build_labels` assembles
`pocket_raw & ~active_site & ~terminal`, so a different active site excludes
different residues. Both configurations are therefore reported in full rather
than swapping one number for another.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import prody  # noqa: E402
prody.confProDy(verbosity="none")

from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.labels import (  # noqa: E402
    build_labels, holo_pocket_mask, ligand_groups_from_atomgroup,
    protein_heavy_atoms_by_residue, terminal_mask,
)
from allostery.baselines import (  # noqa: E402
    degree_centrality, euclid_from_seed_centroid, hop_from_seed,
)
from allostery.lowmode_predictor import dcc_low  # noqa: E402
from allostery.metrics import auc  # noqa: E402
from backend import active_site as backend_active_site  # noqa: E402

TARGET = "PTP1B"
K_MODES = 10          # TASK-0201's own surviving cell
OUT = _ROOT / "results/tasks/0216_new_pair_scoring" / "ptp1b_real_seed.json"


def main() -> int:
    cfg = load_target_config(TARGET)
    apo = clean_from_config(TARGET, role="apo")
    holo = clean_from_config(TARGET, role="holo")
    ch = cfg.get("holo_chains") or cfg.get("chains")
    st = prody.parsePDB(cfg["holo_pdb"], compressed=False).select(
        " or ".join(f"chain {c}" for c in ch))
    holo.ligand_groups = ligand_groups_from_atomgroup(st)
    if len(holo.resnums) == len(apo.resnums):
        holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
            st, ch, holo.resnums)

    coords = apo.coords
    cut = float(cfg.get("enm_cutoff", 8.0))
    pocket_cut = float(cfg.get("pocket_contact_cutoff", 4.5))
    n = len(coords)

    # --- seed A: the fallback the register has actually been using ---
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        labels_fb = build_labels(apo, holo, cfg, cutoff=pocket_cut)
    seed_fb = np.where(labels_fb.active_site)[0]

    # --- seed B: the real, UniProt-annotated catalytic site ---
    det = backend_active_site.detect_active_site(cfg["apo_pdb"], chain=ch[0])
    uniprot_resnums = set(det.get("active_site") or [])
    apo_resnums = np.asarray(apo.resnums)
    seed_real = np.where(np.isin(apo_resnums, list(uniprot_resnums)))[0]

    # pocket under the real active site: same assembly build_labels performs
    pocket_raw = holo_pocket_mask(apo, holo, cfg["drug_ligand"], cutoff=pocket_cut)
    if pocket_raw is None:
        raise RuntimeError(f"holo_pocket_mask returned None for drug_ligand={cfg['drug_ligand']!r}")
    active_real = np.zeros(n, dtype=bool)
    active_real[seed_real] = True
    pocket_real = pocket_raw & ~active_real & ~terminal_mask(n, 0.05)

    def evaluate(seed, pocket, tag):
        y = pocket.astype(int)
        mask = np.ones(n, dtype=bool)
        mask[seed] = False
        floors = {
            "degree": degree_centrality(coords, cutoff=cut),
            "euclid_from_seed": euclid_from_seed_centroid(coords, seed),
            "hop_from_seed": hop_from_seed(coords, seed, cutoff=cut),
        }
        fa = {k: float(auc(v[mask], y[mask])) for k, v in floors.items()}
        score = dcc_low(coords, seed, cutoff=cut, k_modes=K_MODES)
        return {
            "tag": tag,
            "n_seed": int(len(seed)),
            "seed_resnums": [int(x) for x in apo_resnums[seed]],
            "n_pocket": int(y.sum()),
            "floor_aucs": fa,
            "max_floor": max(fa.values()),
            "dcc_low_auc": float(auc(score[mask], y[mask])),
        }

    res = {
        "target": TARGET, "apo": cfg["apo_pdb"], "holo": cfg["holo_pdb"],
        "k_modes": K_MODES,
        "uniprot_active_site_source": det.get("source"),
        "uniprot_active_site_resnums": sorted(uniprot_resnums),
        "fallback": evaluate(seed_fb, labels_fb.pocket, "top-degree fallback (what the register used)"),
        "real": evaluate(seed_real, pocket_real, "UniProt catalytic site (Cys215 + P-loop)"),
    }
    res["delta_dcc_low_auc"] = res["real"]["dcc_low_auc"] - res["fallback"]["dcc_low_auc"]
    res["seed_overlap"] = int(len(set(seed_fb.tolist()) & set(seed_real.tolist())))

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))

    print(f"=== PTP1B dcc_low (k={K_MODES}) under two seeds ===")
    for key in ("fallback", "real"):
        r = res[key]
        print(f"\n{r['tag']}")
        print(f"  seed ({r['n_seed']} res): {r['seed_resnums']}")
        print(f"  pocket size: {r['n_pocket']}")
        print(f"  floor (max of 3): {r['max_floor']:.4f}   {r['floor_aucs']}")
        print(f"  dcc_low AUC:     {r['dcc_low_auc']:.4f}"
              f"   -> {'CLEARS' if r['dcc_low_auc'] > r['max_floor'] else 'BELOW'} floor")
    print(f"\nseed overlap between the two: {res['seed_overlap']} residues")
    print(f"delta dcc_low AUC (real - fallback): {res['delta_dcc_low_auc']:+.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
