"""TASK-0238 B1 follow-up -- resolving the KRAS_G12C floor mismatch
(0.6007 recomputed vs 0.4818 published).

Hypothesis under test: the two numbers are the same computation under two
different EVALUATION MASKS.

  register convention (`diagnostics.classify_failure`, diagnostics.py:326):
      `_auc(candidate, labels_arr)` over ALL N residues. The seed residues
      are in the negative pool. `hop_from_seed` scores them 0 hops = top
      rank, and they are labelled non-pocket, so the baseline is charged a
      block of false positives for ranking the residues it was HANDED.

  seed-excluded convention (scripts/task0216_*.py, and this task's Leg A):
      seed rows dropped from the evaluation. A predictor is never asked to
      rank the seed -- the seed is the input.

If the hypothesis holds, unmasked reproduces 0.4818 exactly, and the register's
canonical floor is systematically DEFLATED -- i.e. the floor gate is more
permissive than the register believes, not stricter. That direction matters:
it is the opposite of the bias this task was filed to look for.
"""
from __future__ import annotations
import sys, warnings, json
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path: sys.path.insert(0, str(_p))
import prody; prody.confProDy(verbosity="none")
from allostery.clean import clean_from_config, load_target_config
from allostery.labels import (build_labels, ligand_groups_from_atomgroup,
                              protein_heavy_atoms_by_residue)
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed
from allostery.hamiltonians import build_H_new
from allostery.propagators import time_averaged_ctqw_converged
from allostery.metrics import auc

TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
PUBLISHED_FLOOR = {"KRAS_G12C": 0.4818, "BCR_ABL1": 0.5817, "CARDIAC_MYOSIN": 0.5679}
PUBLISHED_ACTUAL = {"KRAS_G12C": 0.5901, "BCR_ABL1": 0.5266, "CARDIAC_MYOSIN": 0.5176}

print(f"{'target':<16} {'convention':<14} {'floor':>7} {'published':>10} {'ctqw':>7} {'pub':>7} {'clears?':>8}")
out = {}
for t in TARGETS:
    cfg = load_target_config(t)
    apo = clean_from_config(t, role="apo"); holo = clean_from_config(t, role="holo")
    ch = cfg.get("holo_chains") or cfg.get("chains")
    st = prody.parsePDB(cfg["holo_pdb"], compressed=False).select(" or ".join(f"chain {c}" for c in ch))
    holo.ligand_groups = ligand_groups_from_atomgroup(st)
    holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(st, ch, holo.resnums)
    cut = float(cfg.get("enm_cutoff", 8.0))
    lab = build_labels(apo, holo, cfg, cutoff=float(cfg.get("pocket_contact_cutoff", 4.5)))
    sd = np.where(lab.active_site)[0]; y = lab.pocket.astype(int); n = len(apo.coords)
    f = {"degree": degree_centrality(apo.coords, cutoff=cut),
         "euclid": euclid_from_seed_centroid(apo.coords, sd),
         "hop": hop_from_seed(apo.coords, sd, cutoff=cut)}
    ctqw = time_averaged_ctqw_converged(build_H_new(apo.coords, apo.bfactors, cutoff=cut),
                                        source=sd, coherent=False)
    row = {}
    for conv, m in (("unmasked", np.ones(n, bool)),
                    ("seed-excluded", np.array([i not in set(sd.tolist()) for i in range(n)]))):
        fl = max(float(auc(v[m], y[m])) for v in f.values())
        ca = float(auc(ctqw[m], y[m]))
        row[conv] = {"floor": fl, "ctqw": ca, "clears": ca > fl}
        mark = "MATCH" if abs(fl - PUBLISHED_FLOOR[t]) < 0.005 else ""
        print(f"{t:<16} {conv:<14} {fl:>7.4f} {PUBLISHED_FLOOR[t]:>10.4f} {ca:>7.4f} "
              f"{PUBLISHED_ACTUAL[t]:>7.4f} {str(ca>fl):>8}  {mark}")
    row["floor_shift"] = row["seed-excluded"]["floor"] - row["unmasked"]["floor"]
    row["verdict_flips"] = row["unmasked"]["clears"] != row["seed-excluded"]["clears"]
    out[t] = row
    print()
p = _ROOT / "results/tasks/0238_hiv1rt/floor_convention.json"; p.write_text(json.dumps(out, indent=1))
print("floor shift (seed-excluded minus unmasked): " +
      ", ".join(f"{t} {out[t]['floor_shift']:+.4f}" for t in TARGETS))
print("verdict flips: " + ", ".join(f"{t} {out[t]['verdict_flips']}" for t in TARGETS))
print(f"written: {p}")
