#!/usr/bin/env python3
"""TASK-0270, item 1 -- KRAS_G12C's apo structure is genuinely G12C mutant,
re-scored old (4OBE, wild-type) vs new (4LDJ, real G12C) side by side.

**A real, load-bearing correctness bug found in [[TASK-0155]]'s own
candidate pool, before trusting anything else here**: that task's own
docstring claims its 10-candidate pool is "GDP+Mg-only ligand set (excludes
~90 inhibitor-bound structures)". Directly re-checked via the RCSB Data API,
enumerating every non-polymer entity per structure (not the summary
`nonpolymer_bound_components` field, which only lists metal-COORDINATED
components and silently misses non-coordinating small-molecule inhibitors --
almost certainly the root cause of the original filter's own false negative):
**8 of the 10 "verified apo" candidates are actually drug-bound**
(8AZX/BI-2865, 7A1X/QWB, 8QUG/WYU, 9UOH/ASP2453, 7YCE/IQN, 7MDP/Z07,
7RP3/MKZ [covalently alkylated], 8AFC/LXK). Only **4LDJ** and **8TXJ** are
genuinely apo (GDP+MG exactly, confirmed by enumerating all non-polymer
entities directly). [[TASK-0155]]'s own file needs a superseding note (see
this task's own Done section) -- its "10 true-genotype structures, median
AUC 0.482" distribution claim is not valid as stated; only 2 of its 10 rows
are actually apo-vs-apo comparable.

Structural grounds for the choice (this task's own Constraint: pick on
structural grounds, not for a flattering result): **4LDJ**, 1.15 A, over
**8TXJ**, 1.4 A -- both genuinely apo G12C (residue 12 = Cys, independently
re-verified here via the same anchor-relative sequence check [[TASK-0155]]
established), both single chain A.

Reuses, does not re-derive:
  - `apo_structure_sensitivity_sweep.run_one` ([[TASK-0155]]'s own pipeline
    call: `clean` -> `build_labels` -> `run_frozen_verdict`, the exact same
    machinery `run_challenge.py` uses) for AUC/P@5/diagnosis, imported
    directly.
  - `potentials._gnm_msf` for ENM-vs-B-factor validity, [[TASK-0250]]'s
    exact method and pass bars (PASS>=0.6, MARGINAL>=0.4).
  - The (chain, resnum)-keyed heavy-atom distance approach from
    [[TASK-0255]]/[[TASK-0265]] for the pocket-to-active-site minimum
    heavy-atom distance ([[TASK-0169]]'s own metric, [[TASK-0258]]'s own
    taxonomy input).

Run: ../.venv/bin/python3 scripts/task0270_kras_g12c_genotype_fix.py
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
from scipy.stats import pearsonr

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import prody  # noqa: E402

prody.confProDy(verbosity="none")

from allostery.clean import clean, load_target_config  # noqa: E402
from allostery.labels import build_labels, ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue  # noqa: E402
from allostery.potentials import _gnm_msf  # noqa: E402
from apo_structure_sensitivity_sweep import _load_holo, run_one  # noqa: E402

OUT = _ROOT / "results/tasks/0270_kras_g12c_genotype_fix"
TARGET_NAME = "KRAS_G12C"
OLD_APO = "4OBE"
NEW_APO = "4LDJ"
PASS_BAR, MARGINAL_BAR = 0.6, 0.4


def verdict(r: float) -> str:
    if r >= PASS_BAR:
        return "PASS"
    if r >= MARGINAL_BAR:
        return "MARGINAL"
    return "FAIL"


def enm_validity(pdb_id: str, target_config: dict) -> dict:
    chains = target_config.get("apo_chains", target_config.get("chains"))
    apo = clean(pdb_id, chains=chains, keep_nucleic=target_config.get("keep_nucleic", False))
    cutoff = float(target_config.get("enm_cutoff", 8.0))
    b = np.asarray(apo.bfactors, dtype=float)
    finite = np.isfinite(b)
    msf = np.asarray(_gnm_msf(apo.coords, cutoff), dtype=float)
    ok = finite & np.isfinite(msf)
    r, p = pearsonr(msf[ok], b[ok])
    return dict(pdb_id=pdb_id, pearson_r=float(r), pearson_p=float(p),
                verdict=verdict(float(r)), n=int(ok.sum()))


def min_heavy_atom_distance(pdb_id: str, target_config: dict, holo) -> dict:
    """Pocket-to-active-site minimum heavy-atom distance, [[TASK-0169]]'s
    own metric -- (chain, resnum)-keyed, [[TASK-0255]]/[[TASK-0265]]'s own
    fix for the multi-chain resnum-collision bug (not relevant for this
    single-chain-A target, applied anyway for consistency)."""
    chains = target_config.get("apo_chains", target_config.get("chains"))
    apo = clean(pdb_id, chains=chains, keep_nucleic=target_config.get("keep_nucleic", False))
    labels_obj = build_labels(apo, holo, target_config,
                               cutoff=float(target_config.get("pocket_contact_cutoff", 4.5)))
    seed = np.where(labels_obj.active_site)[0]
    pocket = labels_obj.pocket
    if len(seed) == 0 or pocket is None or not pocket.any():
        return dict(pdb_id=pdb_id, error="empty seed or pocket")

    resn = np.asarray(apo.resnums)
    chids = np.asarray(apo.chain_ids)
    ag = prody.parsePDB(pdb_id, compressed=False).select(
        "protein and (" + " or ".join(f"chain {c}" for c in chains) + ")")
    key_to_seq = {(str(c), int(r)): i for i, (c, r) in enumerate(zip(chids, resn))}
    heavy_seq = np.array(
        [key_to_seq.get((str(c), int(r)), -1) for c, r in zip(ag.getChids(), ag.getResnums())], dtype=int)
    keep = heavy_seq >= 0
    heavy_coords = ag.getCoords()[keep]
    heavy_seq = heavy_seq[keep]

    seed_atoms = heavy_coords[np.isin(heavy_seq, seed)]
    d = np.sqrt(((heavy_coords[:, None, :] - seed_atoms[None, :, :]) ** 2).sum(-1))
    per_atom_min = d.min(axis=1)
    min_dist = np.full(len(resn), np.inf)
    np.minimum.at(min_dist, heavy_seq, per_atom_min)
    min_dist[np.isinf(min_dist)] = np.nan

    pocket_min = float(np.nanmin(min_dist[pocket]))
    return dict(pdb_id=pdb_id, min_heavy_atom_A=pocket_min, n_pocket=int(pocket.sum()))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    target_config = load_target_config(TARGET_NAME)
    cutoff = float(target_config.get("enm_cutoff", 8.0))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", 4.5))

    print("=== Loading fixed holo (6OIM) ===")
    holo = _load_holo(target_config)

    out = {}
    for pdb_id, label in ((OLD_APO, "OLD (wild-type, flagged)"), (NEW_APO, "NEW (genuine G12C)")):
        print(f"\n=== {label}: {pdb_id} ===")
        pipeline = run_one(pdb_id, target_config, holo, cutoff, pocket_cutoff)
        enm = enm_validity(pdb_id, target_config)
        dist = min_heavy_atom_distance(pdb_id, target_config, holo)
        print(f"  AUC={pipeline['auc']:.3f}  P@5={pipeline['p_at_5']:.3f}  "
              f"diagnosis={pipeline['diagnosis']}")
        print(f"  ENM validity: r={enm['pearson_r']:.3f} ({enm['verdict']})")
        print(f"  Pocket-to-active-site min heavy-atom distance: "
              f"{dist.get('min_heavy_atom_A', float('nan')):.2f} A")
        out[pdb_id] = dict(label=label, pipeline=pipeline, enm=enm, distance=dist)

    (OUT / "kras_genotype_fix.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwritten: {OUT / 'kras_genotype_fix.json'}")

    print("\n=== Side by side ===")
    o, n = out[OLD_APO], out[NEW_APO]
    print(f"{'metric':<40}{'OLD 4OBE (WT)':>18}{'NEW 4LDJ (G12C)':>18}")
    print(f"{'AUC':<40}{o['pipeline']['auc']:>18.3f}{n['pipeline']['auc']:>18.3f}")
    print(f"{'P@5':<40}{o['pipeline']['p_at_5']:>18.3f}{n['pipeline']['p_at_5']:>18.3f}")
    print(f"{'ENM validity r':<40}{o['enm']['pearson_r']:>18.3f}{n['enm']['pearson_r']:>18.3f}")
    print(f"{'ENM verdict':<40}{o['enm']['verdict']:>18}{n['enm']['verdict']:>18}")
    print(f"{'min heavy-atom distance (A)':<40}"
          f"{o['distance'].get('min_heavy_atom_A', float('nan')):>18.2f}"
          f"{n['distance'].get('min_heavy_atom_A', float('nan')):>18.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
