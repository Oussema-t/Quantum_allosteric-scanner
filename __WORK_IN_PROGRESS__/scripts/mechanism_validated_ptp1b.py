#!/usr/bin/env python3
"""TASK-0170 Phase 1 -- PTP1B scored against a mechanism-validated allosteric
network instead of (alongside) its existing drug-contact label.

Every label in this project is a drug-contact set (residues within
pocket_contact_cutoff of a bound ligand). PTP1B's existing label happens to
be a BB-series *allosteric* inhibitor (892) bound at the alpha3/alpha6/alpha7
site -- but it is still a drug-contact definition, not the literature's own
NMR/crystallographic allosteric-communication-network definition. This
script curates that network from two independent, peer-reviewed sources,
verifies every residue number against the real 1SUG structure (not trusted
from either paper's own numbering), measures its overlap with the existing
label, and re-scores the register's own existing observables against it
side by side. No new machinery; no new observable.

Sources (both fetched and cross-checked 2026-07-28):
  [1] Choy, Karplus, Kern et al., "Conformational Rigidity and Protein
      Dynamics at Distinct Timescales Regulate PTP1B Activity and
      Allostery", Cell / Mol. Cell 2017 (PMC5325675).
  [2] Keedy, Fraser et al., "An expanded allosteric network in PTP1B by
      multitemperature crystallography, fragment screening, and covalent
      tethering", eLife 2018;7:e36307.

Every residue below was checked against this project's own loaded 1SUG
structure (resnum -> resname) before inclusion -- see the verification
table in this task's own Done section. One literature-cited residue
(E157) FAILED verification (actual structure has Q157) and is excluded,
not silently corrected. One residue (R221) is excluded because it is
already this target's `active_site` (functional/catalytic seed) under
this project's own build_labels convention (pocket and active_site are
disjoint by construction) -- including it would violate that invariant.
One residue (M3, N-terminal, "L16 site") is excluded as a low-confidence,
structurally isolated single citation that does not fit the "one
contiguous face" the source paper itself describes.

Run: python3 scripts/mechanism_validated_ptp1b.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from allostery.clean import load_target_config  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.lowmode_predictor import dcc_low, prs_low  # noqa: E402
from allostery.metrics import auc, block_bootstrap_ci, spatial_block_bootstrap_ci  # noqa: E402
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
import run_challenge  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0170_mechanism_validated"

# -- mechanism-validated network, literature-cited residue numbers ---------
# (structural element: [resnums]) -- see module docstring for verification.
MECHANISM_NETWORK = {
    "WPD_loop": [177, 178, 179, 180, 181, 185, 269],       # 221 excluded: active_site
    "L11_loop": [105, 148, 150, 152, 153],                 # 157 excluded: verification mismatch
    "alpha3": [190, 191, 192, 193, 196, 197, 198, 200],
    "alpha6_alpha7": [267, 270, 276, 277, 280, 281, 282, 290, 291, 295],
    "other": [176],
}


def main() -> None:
    target_name = "PTP1B"
    cfg = load_target_config(target_name)
    cutoff = float(cfg["enm_cutoff"])
    apo, holo = run_challenge._load_apo_holo(target_name, cfg)
    labels_obj = build_labels(apo, holo, cfg, cutoff=cfg["pocket_contact_cutoff"])

    resnum_to_idx = {int(rn): i for i, rn in enumerate(apo.resnums)}
    active_idx = np.where(labels_obj.active_site)[0]
    source = active_idx  # full active-site array, incoherent mixture (TASK-0118/INV-0006)

    drug_pocket_idx = np.where(labels_obj.pocket)[0]
    drug_pocket_resnums = sorted(int(apo.resnums[i]) for i in drug_pocket_idx)

    all_lit_resnums = sorted({r for grp in MECHANISM_NETWORK.values() for r in grp})
    missing = [r for r in all_lit_resnums if r not in resnum_to_idx]
    if missing:
        raise RuntimeError(f"curated resnums not present in structure: {missing}")

    mech_idx = np.array(sorted(resnum_to_idx[r] for r in all_lit_resnums))
    # Disjointness invariant with active_site, asserted not assumed.
    overlap_with_active = np.intersect1d(mech_idx, active_idx)
    if len(overlap_with_active) > 0:
        raise RuntimeError(
            f"mechanism-validated label overlaps active_site at indices {overlap_with_active} "
            f"(resnums {apo.resnums[overlap_with_active].tolist()}) -- exclude before scoring"
        )

    n = len(apo.resnums)
    mech_label = np.zeros(n, dtype=bool)
    mech_label[mech_idx] = True
    drug_label = labels_obj.pocket

    # --- overlap measurement (must happen before any scoring) -------------
    jaccard = float(np.logical_and(mech_label, drug_label).sum()) / float(
        np.logical_or(mech_label, drug_label).sum()
    )
    shared_resnums = sorted(int(apo.resnums[i]) for i in np.where(mech_label & drug_label)[0])
    mech_only_resnums = sorted(int(apo.resnums[i]) for i in np.where(mech_label & ~drug_label)[0])

    print(f"{target_name}: mechanism-validated label n={mech_label.sum()}, "
          f"drug-contact label n={drug_label.sum()}, "
          f"shared={len(shared_resnums)}, mech-only={len(mech_only_resnums)}, "
          f"Jaccard={jaccard:.3f}")
    print(f"  shared resnums: {shared_resnums}")
    print(f"  mechanism-only resnums: {mech_only_resnums}")

    # --- proximity floor, recomputed against the NEW label -----------------
    def floor_for(label):
        deg = auc(degree_centrality(apo.coords, cutoff=cutoff), label)
        euc = auc(-euclid_from_seed_centroid(apo.coords, source), label)
        hop = auc(-hop_from_seed(apo.coords, source, cutoff=cutoff), label)
        return {"degree": deg, "euclid": euc, "hop": hop, "max": max(deg, euc, hop)}

    floor_mech = floor_for(mech_label)
    floor_drug = floor_for(drug_label)
    print(f"\nproximity floor -- drug-contact label: {floor_drug}")
    print(f"proximity floor -- mechanism-validated label: {floor_mech}")

    # --- score existing observables, both labels, side by side -------------
    H_new = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
    occ = time_averaged_ctqw_converged(H_new, source=source, coherent=False)
    prs = prs_low(apo.coords, source, cutoff=cutoff, k_modes=20)
    dcc = dcc_low(apo.coords, source, cutoff=cutoff, k_modes=20)

    results = {}
    for obs_name, score in (("ctqw_converged", occ), ("prs_low_k20", prs), ("dcc_low_k20", dcc)):
        a_mech = auc(score, mech_label)
        a_drug = auc(score, drug_label)
        # sequence-block CI (existing convention) + spatial-block CI (TASK-0165)
        _, lo_s, hi_s = block_bootstrap_ci(score, mech_label, rng=np.random.default_rng(42))
        _, lo_sp, hi_sp = spatial_block_bootstrap_ci(
            apo.coords, score, mech_label, rng=np.random.default_rng(42)
        )
        results[obs_name] = {
            "auc_mechanism_validated": a_mech,
            "auc_drug_contact": a_drug,
            "mech_floor_max": floor_mech["max"],
            "mech_ci_seq": [lo_s, hi_s],
            "mech_ci_spatial": [lo_sp, hi_sp],
            "mech_ci_overlaps_floor": not (lo_s > floor_mech["max"] or hi_s < floor_mech["max"]),
        }
        print(f"\n{obs_name}: AUC(mechanism-validated)={a_mech:.3f} "
              f"AUC(drug-contact)={a_drug:.3f}  floor(mech)={floor_mech['max']:.3f}  "
              f"CI(seq)=[{lo_s:.3f},{hi_s:.3f}]  CI(spatial)=[{lo_sp:.3f},{hi_sp:.3f}]")

    # --- permutation null: SCATTERED, not compact-patch ---------------------
    # The mechanism-validated label is genuinely dispersed (WPD loop ~176-185,
    # L11 loop 105-153, alpha3/6/7 190-295) -- TASK-0170's own Intent Contract
    # explicitly calls the compact-patch draw "badly wrong" for a dispersed
    # label. A scattered rng.choice draw is the geometrically appropriate
    # comparison here (TASK-0158's finding was specific to COMPACT labels).
    rng = np.random.default_rng(7)
    pocket_size = int(mech_label.sum())
    n_perm = 1000
    null_aucs = {name: [] for name in results}
    pool = np.setdiff1d(np.arange(n), active_idx)  # never draw the seed itself
    for _ in range(n_perm):
        draw = rng.choice(pool, size=pocket_size, replace=False)
        lab = np.zeros(n, dtype=bool)
        lab[draw] = True
        for obs_name, score in (("ctqw_converged", occ), ("prs_low_k20", prs), ("dcc_low_k20", dcc)):
            null_aucs[obs_name].append(auc(score, lab))

    for obs_name in results:
        arr = np.array(null_aucs[obs_name])
        real = results[obs_name]["auc_mechanism_validated"]
        pctl = float((arr <= real).mean())
        p = float((arr >= real).mean())
        results[obs_name]["scattered_null_percentile"] = pctl
        results[obs_name]["scattered_null_p"] = p
        print(f"{obs_name}: scattered-null percentile={pctl*100:.1f}  p={p:.3f}")

    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(OUTPUT_DIR / "ptp1b_mechanism_validated.json", "w") as f:
        json.dump({
            "target": target_name,
            "mechanism_network_resnums": all_lit_resnums,
            "drug_pocket_resnums": drug_pocket_resnums,
            "jaccard": jaccard,
            "shared_resnums": shared_resnums,
            "mechanism_only_resnums": mech_only_resnums,
            "floor_mechanism_validated": floor_mech,
            "floor_drug_contact": floor_drug,
            "results": results,
        }, f, indent=2)
    print(f"\nWrote {OUTPUT_DIR / 'ptp1b_mechanism_validated.json'}")


if __name__ == "__main__":
    main()
