#!/usr/bin/env python3
"""TASK-0279 -- The ligand-selectivity gate: does `V_C` measure allosteric
*efficacy*, or just occupancy?

[[TASK-0276]] found `V_C` (GNM dynamic cross-correlation centrality)
significantly separates allosteric from orthosteric sites in two families.
[[TASK-0278]] flagged the gap that positive could not close: `V_C` might be
detecting "this cavity is occupied and coupled", not "this occupant does
something". BCR-ABL1 gives the one controlled pair in this register where
that confound cancels -- same protein, same cavity, one inert occupant, one
efficacious modulator:

    1OPL (our "apo")  -- myristoyl pocket contains MYR (myristic acid),
                          no therapeutic autoinhibition
    5MO4 (our holo)   -- same pocket contains AY7 (asciminib), the real
                          allosteric drug

Both structures are DOUBLY occupied -- 1OPL also carries P16 (ATP-site
inhibitor), 5MO4 carries NIL (nilotinib) -- so the orthosteric site is
controlled too, not empty in either arm. Stated explicitly per this task's
own Scope, not treated as if 1OPL were apo.

**Node-set matching (this task's own Scope item 2, [[TASK-0275]]'s own
established requirement)**: GNM/graph features are global -- an unmatched
residue set changed DHPS_GC7's own `V_C` from 0.392 to 0.586 in that task.
`allostery.superpose.align_apo_holo` gives the common (chain, resnum) index
set between 1OPL and 5MO4; every GRAPH feature (`V_C`, `degree`, `euclid`,
`hop`) is computed on coordinates restricted to that common set, in matched
order, per structure -- not each structure's own full residue set. `V_B`
(a per-atom physical measurement) and `SASA` (a local, all-real-neighbours
quantity that would be un-physical to compute on an artificially-pruned
residue set) are computed on each structure's own FULL resnums and only
INDEXED at the common set afterward -- a deliberately different treatment
for a stated reason, not an oversight.

**Ligand stripping**: reuses [[TASK-0276]]'s own `write_ligand_stripped_pdb`
(strips ALL non-protein atoms, both the myristoyl-pocket AND ATP-site
occupants, from each structure independently before scoring) and
`ligand_stripped_sasa`, not re-derived.

**Statistic (this task's own Scope item 4)**: per-residue PAIRED comparison
within the matched myristoyl-pocket residue set -- for each feature,
median(asciminib) vs median(myristate), median paired delta, fraction of
residues favouring asciminib, and a paired Wilcoxon signed-rank test on the
deltas, reported as a descriptive/exploratory statistic (pocket residues are
spatially correlated, not independent draws -- NOT treated as a
structure-level significance test, which this task's own Scope explicitly
forbids manufacturing with n=2 structures).

Run: ../.venv/bin/python3 scripts/task0279_ligand_selectivity_gate.py
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
from scipy.stats import wilcoxon

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

prody.confProDy(verbosity="none")

# Side-effect-only import, TASK-0258's own fix re-applied by every later
# task that touches prody.parsePDB directly -- do not re-assign
# prody.parsePDB from a name pulled out of this module.
import task0255_hop_angstrom_calibration  # noqa: E402,F401

from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.labels import build_labels, ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue  # noqa: E402
from allostery.superpose import align_apo_holo  # noqa: E402
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402

from task0276_holo_only_structural_signature import (  # noqa: E402
    dcc_centrality, write_ligand_stripped_pdb, ligand_stripped_sasa,
)

TARGET = "BCR_ABL1"
OUT = _ROOT / "results/tasks/0279_ligand_selectivity_gate"
GRAPH_FEATURES = ["V_C", "degree", "euclid", "hop"]     # node-set-sensitive, computed on restricted coords
POINT_FEATURES = ["V_B", "SASA"]                          # per-atom/local, computed full then indexed
ALL_FEATURES = GRAPH_FEATURES + POINT_FEATURES


def _log(msg: str) -> None:
    print(msg, flush=True)


def _load_apo_holo_labels():
    """Same pattern as [[TASK-0278]]'s own `_load_apo_holo_labels` --
    `clean_from_config` for the Ca/bfactor arrays, a direct prody parse of
    holo (unrestricted, then chain-selected) for the ligand-group/heavy-atom
    machinery `build_labels`/`functional_indices` need."""
    cfg = load_target_config(TARGET)
    apo = clean_from_config(TARGET, role="apo")     # 1OPL
    holo = clean_from_config(TARGET, role="holo")   # 5MO4
    chains = cfg.get("holo_chains") or cfg.get("chains")
    holo_struct = prody.parsePDB(cfg["holo_pdb"], compressed=False).select(
        " or ".join(f"chain {c}" for c in chains))
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)
    holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
        holo_struct, chains, holo.resnums)
    cutoff = float(cfg.get("pocket_contact_cutoff", 4.5))
    labels_obj = build_labels(apo, holo, cfg, cutoff=cutoff, target_name=TARGET)
    return cfg, apo, holo, labels_obj


def _point_feature_full(pdb_id: str, chains: list, resnums: np.ndarray, bfactors: np.ndarray) -> dict:
    """V_B (direct) and SASA (ligand-stripped, full resnums) -- both on
    each structure's OWN complete residue set, indexed at the common set
    only after computation, per this script's own module docstring."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        stripped = tmp / f"{pdb_id.lower()}_stripped.pdb"
        write_ligand_stripped_pdb(pdb_id, chains, stripped)
        sasa = ligand_stripped_sasa(stripped, resnums, chains[0])
    return dict(V_B=np.asarray(bfactors, dtype=float), SASA=sasa)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg, apo, holo, labels_obj = _load_apo_holo_labels()
    chains = cfg.get("chains") or ["A"]

    if labels_obj.pocket is None or not labels_obj.pocket.any():
        _log("BCR_ABL1: no resolvable myristoyl-pocket label -- abort")
        return 1

    _log(f"1OPL (myristate + P16, our 'apo' role) resolution={apo.resolution}")
    _log(f"5MO4 (asciminib + nilotinib, our 'holo' role) resolution={holo.resolution}")
    _log(f"Myristoyl pocket (labels.pocket, defined via AY7-contact in 5MO4, mapped to 1OPL numbering): "
         f"{int(labels_obj.pocket.sum())} residues")
    _log(f"Active/orthosteric site (func_ligand=NIL-contact, 5MO4-derived): "
         f"{int(labels_obj.active_site.sum())} residues -- note 1OPL's own equivalent occupant is P16, "
         f"not NIL; both are ATP-competitive BCR-ABL1 inhibitors at the same kinase ATP site, so this "
         f"one NIL-derived seed definition is applied to both structures' own numbering, not re-derived "
         f"per structure.")

    # --- node-set matching -----------------------------------------------
    alignment = align_apo_holo(apo, holo)
    apo_idx, holo_idx = alignment.apo_idx, alignment.holo_idx
    _log(f"align_apo_holo: {len(apo_idx)} common (chain,resnum) Ca pairs "
         f"(1OPL has {len(apo.resnums)}, 5MO4 has {len(holo.resnums)}), "
         f"RMSD={alignment.rmsd_overall:.3f} A")

    pocket_local = np.asarray(labels_obj.pocket)[apo_idx]
    n_pocket = int(pocket_local.sum())
    _log(f"Myristoyl pocket residues surviving the common-set restriction: {n_pocket} / "
         f"{int(labels_obj.pocket.sum())}")
    if n_pocket < 3:
        _log("Fewer than 3 matched pocket residues -- abort, cannot report a distribution")
        return 1

    seed_idx_full = np.where(np.asarray(labels_obj.active_site))[0]
    seed_local = np.where(np.isin(apo_idx, seed_idx_full))[0]
    _log(f"Active-site seed residues surviving the common-set restriction: {len(seed_local)}")

    cutoff = float(cfg.get("enm_cutoff", 8.0))
    coords_1opl = apo.coords[apo_idx]
    coords_5mo4 = holo.coords[holo_idx]

    # --- graph features, on RESTRICTED (matched) coordinates -------------
    feat_1opl = {}
    feat_5mo4 = {}
    feat_1opl["V_C"] = dcc_centrality(coords_1opl, cutoff)
    feat_5mo4["V_C"] = dcc_centrality(coords_5mo4, cutoff)
    feat_1opl["degree"] = degree_centrality(coords_1opl, cutoff=cutoff)
    feat_5mo4["degree"] = degree_centrality(coords_5mo4, cutoff=cutoff)
    if len(seed_local) > 0:
        feat_1opl["euclid"] = euclid_from_seed_centroid(coords_1opl, seed_local)
        feat_5mo4["euclid"] = euclid_from_seed_centroid(coords_5mo4, seed_local)
        feat_1opl["hop"] = hop_from_seed(coords_1opl, seed_local, cutoff=cutoff)
        feat_5mo4["hop"] = hop_from_seed(coords_5mo4, seed_local, cutoff=cutoff)
    else:
        _log("No active-site seed in the common set -- euclid/hop skipped")

    # --- point features, on each structure's FULL resnums, indexed after -
    pf_1opl_full = _point_feature_full(cfg["apo_pdb"], chains, apo.resnums, apo.bfactors)
    pf_5mo4_full = _point_feature_full(cfg["holo_pdb"], chains, holo.resnums, holo.bfactors)
    feat_1opl["V_B"] = pf_1opl_full["V_B"][apo_idx]
    feat_5mo4["V_B"] = pf_5mo4_full["V_B"][holo_idx]
    feat_1opl["SASA"] = pf_1opl_full["SASA"][apo_idx]
    feat_5mo4["SASA"] = pf_5mo4_full["SASA"][holo_idx]

    # --- per-residue paired comparison, restricted to the pocket ---------
    results = {}
    for fname in [f for f in ALL_FEATURES if f in feat_1opl]:
        a = np.asarray(feat_1opl[fname])[pocket_local]   # myristate arm
        b = np.asarray(feat_5mo4[fname])[pocket_local]   # asciminib arm
        ok = np.isfinite(a) & np.isfinite(b)
        a, b = a[ok], b[ok]
        if len(a) < 3:
            results[fname] = dict(error="fewer than 3 finite paired residues", n=int(len(a)))
            continue
        delta = b - a   # asciminib - myristate
        n_favour_asciminib = int((delta > 0).sum())
        try:
            stat, p = wilcoxon(delta)
            p = float(p)
        except ValueError:
            p = float("nan")  # all-zero deltas or similar degenerate case
        results[fname] = dict(
            n=int(len(a)),
            median_myristate_1OPL=float(np.median(a)),
            median_asciminib_5MO4=float(np.median(b)),
            median_delta_asciminib_minus_myristate=float(np.median(delta)),
            frac_residues_favouring_asciminib=n_favour_asciminib / len(a),
            wilcoxon_p_two_sided=p,
        )
        _log(f"{fname:<8} n={len(a):<3} myristate(1OPL) median={np.median(a):+.4f}  "
             f"asciminib(5MO4) median={np.median(b):+.4f}  "
             f"delta median={np.median(delta):+.4f}  "
             f"frac favouring asciminib={n_favour_asciminib}/{len(a)}  "
             f"wilcoxon p={p:.4f}")

    out = dict(
        target=TARGET,
        resolution_1OPL=apo.resolution, resolution_5MO4=holo.resolution,
        n_common_residues=int(len(apo_idx)), n_pocket_matched=n_pocket,
        n_seed_matched=int(len(seed_local)),
        pocket_definition="labels.pocket -- AY7(asciminib)-contact in 5MO4, mapped to 1OPL numbering, "
                           "minus active_site minus terminal (this register's standard build_labels output)",
        active_site_definition="func_ligand=NIL(nilotinib)-contact in 5MO4, mapped to 1OPL numbering; "
                                "1OPL's own ATP-site occupant is P16, a different ATP-competitive inhibitor "
                                "-- NOT independently re-resolved per structure, see module docstring",
        both_arms_doubly_occupied=dict(
            OPL_1_myristoyl_pocket="MYR", OPL_1_atp_site="P16",
            MO4_5_myristoyl_pocket="AY7", MO4_5_atp_site="NIL"),
        per_feature=results,
    )
    (OUT / "ligand_selectivity_gate.json").write_text(json.dumps(out, indent=2))
    _log(f"\nWrote {OUT / 'ligand_selectivity_gate.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
