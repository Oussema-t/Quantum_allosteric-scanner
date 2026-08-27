#!/usr/bin/env python3
"""TASK-0281 -- Docked vs undocked, same site, same protein: does the
`V_C` "capacity to couple" reading (proposed post-hoc after [[TASK-0279]]
found `V_C` HIGHER on the inert myristate pocket than the efficacious
asciminib one) survive a test on data that did not generate it?

The instrument: [[TASK-0280]]'s clustering of [[TASK-0276]]'s own stored
KRAS footprints found KRAS is a 9:1 two-site protein -- nine of ten
verified holo structures dock at Switch-II (consensus residues 9, 58-72,
95-103), `7A1X` alone docks at a different site, the Switch-I/II groove
(footprint 37, 39, 54, 55, 56, 71, 74, 75). Both facts are read directly
from [[TASK-0280]]'s own file, not re-derived -- this task's own job is
the NEW measurement (scoring V_C/V_B/degree/SASA at both site
definitions across all ten structures plus `4LDJ`), not re-clustering.

Pre-registered predictions (fixed before any number below was computed,
per this task's own Constraint -- copied verbatim from the task file):

  P1: V_C at the Switch-I/II residues is HIGHER when undocked (9
      structures + 4LDJ apo, n=10) than when docked (7A1X, n=1).
  P2: The same pattern holds at Switch-II: V_C higher where Switch-II is
      NOT the drug site (7A1X, n=1) than where it is (the other nine,
      n=9).
  P3: fpocket detects NO open cavity at Switch-I/II in most of the nine
      undocked structures.

Reuses, does not re-derive: `task0276_holo_only_structural_signature`'s
`dcc_centrality`/`write_ligand_stripped_pdb`/`ligand_stripped_sasa`/
`KRAS_ENSEMBLE`/`_parse_any`, `allostery.baselines.degree_centrality`,
`allostery.clean.clean`, `allostery.superpose.align_apo_holo`,
`task0242_two_stage_dryrun.fpocket_candidates`.

**Node-set matching (this task's own Scope item 2, non-negotiable,
[[TASK-0279]]'s own established pattern)**: every structure's GRAPH
features (V_C, degree) are computed on coordinates restricted to the
common (chain, resnum) set shared with `4LDJ` (the fixed reference,
itself the register's own verified genuine apo, [[TASK-0270]]), via
`align_apo_holo` run once per structure against that fixed reference --
not an all-pairs alignment across all eleven structures, a simpler and
equally valid design since every comparison in this task is anchored to
one reference frame. V_B/SASA (per-atom/local quantities) are computed on
each structure's own FULL resnums and indexed at the common set
afterward, exactly as [[TASK-0279]] did.
"""
from __future__ import annotations

import json
import sys
import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import prody  # noqa: E402

prody.confProDy(verbosity="none")

import task0255_hop_angstrom_calibration  # noqa: E402,F401 -- side-effect prody.parsePDB fix

from allostery.clean import clean  # noqa: E402
from allostery.superpose import align_apo_holo  # noqa: E402
from allostery.baselines import degree_centrality  # noqa: E402

from task0276_holo_only_structural_signature import (  # noqa: E402
    KRAS_ENSEMBLE, CUTOFF, dcc_centrality, write_ligand_stripped_pdb, ligand_stripped_sasa,
)
import task0242_two_stage_dryrun as t0242  # noqa: E402

OUT = _ROOT / "results/tasks/0281_docked_undocked_capacity"

# Read directly from TASK-0280's own file (verified clustering result,
# quoted, not re-derived): the Switch-I/II footprint 7A1X alone occupies,
# and the Switch-II consensus the other nine occupy.
SWITCH_I_II_RESIDUES = [37, 39, 54, 55, 56, 71, 74, 75]
SWITCH_II_RESIDUES = [9] + list(range(58, 73)) + list(range(95, 104))  # 9, 58-72, 95-103

APO_REFERENCE = "4LDJ"  # TASK-0270's own verified genuine apo KRAS G12C
DOCKED_AT_SWITCH_I_II = "7A1X"  # the one structure whose drug (QWB) sits at Switch-I/II


def _log(msg: str) -> None:
    print(msg, flush=True)


def _point_features_full(pdb_id: str, chains: list, resnums: np.ndarray, bfactors) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        stripped = tmp / f"{pdb_id.lower()}_stripped.pdb"
        write_ligand_stripped_pdb(pdb_id, chains, stripped)
        sasa = ligand_stripped_sasa(stripped, resnums, chains[0])
    return dict(V_B=np.asarray(bfactors, dtype=float), SASA=sasa)


def _fpocket_hits_switch_i_ii(pdb_id: str, chains: list, resnums: np.ndarray) -> dict:
    """P3: does fpocket detect ANY cavity overlapping the Switch-I/II
    residue set, on a ligand-stripped copy of this structure. Returns the
    best overlap fraction + druggability among all detected pockets, and
    the count of pockets touching the site at all -- descriptive, per
    this task's own Scope (no cross-structure significance test)."""
    target_set = {("A", r) for r in SWITCH_I_II_RESIDUES}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        stripped = tmp / f"{pdb_id.lower()}_fpocket_strip.pdb"
        write_ligand_stripped_pdb(pdb_id, chains, stripped)
        pockets = t0242.fpocket_candidates(stripped, tmp)
    if isinstance(pockets, dict):
        return {"error": pockets.get("error", "fpocket failed")}
    best_overlap, best_drug, n_touching = 0.0, None, 0
    for p in pockets:
        res = {("A", r) for r in p.get("resnums", set())}
        overlap = len(res & target_set) / len(target_set)
        if overlap > 0:
            n_touching += 1
        if overlap > best_overlap:
            best_overlap, best_drug = overlap, p.get("druggability_score")
    return {"best_overlap_frac": best_overlap, "best_pocket_druggability": best_drug,
            "n_pockets_touching_site": n_touching, "n_pockets_total": len(pockets)}


def _matched_features(ref, apo_like, pdb_id: str, chains: list) -> dict:
    """V_C/degree on the common-set-restricted coordinates (matched
    against `ref`, the fixed 4LDJ reference); V_B/SASA on the full
    resnums, indexed at the common set afterward. Returns per-feature
    arrays keyed by the REFERENCE's own resnum ordering (so target
    residues can be looked up by their 4LDJ numbering regardless of which
    structure produced the value)."""
    alignment = align_apo_holo(ref, apo_like)
    apo_idx, holo_idx = alignment.apo_idx, alignment.holo_idx  # apo_idx: into ref; holo_idx: into apo_like
    coords_matched = apo_like.coords[holo_idx]

    v_c = dcc_centrality(coords_matched, CUTOFF)
    degree = degree_centrality(coords_matched, cutoff=CUTOFF)
    pf = _point_features_full(pdb_id, chains, apo_like.resnums, apo_like.bfactors)
    v_b = pf["V_B"][holo_idx]
    sasa = pf["SASA"][holo_idx]

    ref_resn = np.asarray(ref.resnums)
    matched_resnums = ref_resn[apo_idx]  # this structure's values, keyed by REFERENCE resnum
    by_resnum = {}
    for i, rn in enumerate(matched_resnums):
        by_resnum[int(rn)] = dict(V_C=float(v_c[i]), degree=float(degree[i]),
                                   V_B=float(v_b[i]), SASA=float(sasa[i]))
    return dict(n_common=int(len(apo_idx)), rmsd=float(alignment.rmsd_overall), by_resnum=by_resnum)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    _log(f"Reference (fixed): {APO_REFERENCE} (verified genuine apo, TASK-0270)")
    ref = clean(APO_REFERENCE, chains=["A"], keep_nucleic=False)
    ref_resn = np.asarray(ref.resnums)

    # --- 4LDJ's own values, directly (it IS the reference frame) ---------
    ref_v_c = dcc_centrality(ref.coords, CUTOFF)
    ref_degree = degree_centrality(ref.coords, cutoff=CUTOFF)
    ref_pf = _point_features_full(APO_REFERENCE, ["A"], ref.resnums, ref.bfactors)
    ref_by_resnum = {}
    for i, rn in enumerate(ref_resn):
        ref_by_resnum[int(rn)] = dict(V_C=float(ref_v_c[i]), degree=float(ref_degree[i]),
                                       V_B=float(ref_pf["V_B"][i]), SASA=float(ref_pf["SASA"][i]))

    structures = {APO_REFERENCE: dict(by_resnum=ref_by_resnum, n_common=len(ref_resn), rmsd=0.0,
                                       drug=None, docked_site="none (verified genuine apo)")}

    for pdb_id, drug_code in KRAS_ENSEMBLE:
        _log(f"\n{pdb_id} ({drug_code}): aligning to {APO_REFERENCE}, computing matched features...")
        apo_like = clean(pdb_id, chains=["A"], keep_nucleic=False)
        feats = _matched_features(ref, apo_like, pdb_id, ["A"])
        docked_site = "switch_I_II" if pdb_id == DOCKED_AT_SWITCH_I_II else "switch_II"
        structures[pdb_id] = dict(**feats, drug=drug_code, docked_site=docked_site)
        _log(f"  n_common={feats['n_common']}  rmsd={feats['rmsd']:.3f} A  docked_site={docked_site}")

    # --- P3: fpocket at Switch-I/II, per structure (descriptive) ---------
    _log("\n### P3: fpocket at Switch-I/II (ligand-stripped) ###")
    p3 = {}
    for pdb_id, drug_code in KRAS_ENSEMBLE:
        apo_like = clean(pdb_id, chains=["A"], keep_nucleic=False)
        r = _fpocket_hits_switch_i_ii(pdb_id, ["A"], apo_like.resnums)
        p3[pdb_id] = r
        _log(f"  {pdb_id} ({'docked' if pdb_id == DOCKED_AT_SWITCH_I_II else 'undocked'} at Switch-I/II): {r}")
    apo_like_ref_fp = ref
    r_apo = _fpocket_hits_switch_i_ii(APO_REFERENCE, ["A"], apo_like_ref_fp.resnums)
    p3[APO_REFERENCE] = r_apo
    _log(f"  {APO_REFERENCE} (apo, undocked at Switch-I/II): {r_apo}")

    # --- P1/P2: per-residue values at each site, grouped by docked status
    def _collect(residues, structures_):
        out = {}
        for pdb_id, s in structures_.items():
            vals = {feat: [] for feat in ("V_C", "degree", "V_B", "SASA")}
            missing = []
            for r in residues:
                row = s["by_resnum"].get(r)
                if row is None:
                    missing.append(r)
                    continue
                for feat in vals:
                    vals[feat].append(row[feat])
            out[pdb_id] = {"n_residues_found": len(residues) - len(missing),
                            "n_residues_total": len(residues), "missing": missing,
                            **{f"median_{feat}": (float(np.median(v)) if v else None) for feat, v in vals.items()}}
        return out

    _log("\n### P1: Switch-I/II residues, per structure ###")
    p1 = _collect(SWITCH_I_II_RESIDUES, structures)
    for pdb_id, r in p1.items():
        tag = "DOCKED" if pdb_id == DOCKED_AT_SWITCH_I_II else "undocked"
        _log(f"  {pdb_id:6s} [{tag:9s}] n={r['n_residues_found']}/{r['n_residues_total']} "
             f"median_V_C={r['median_V_C']}")

    _log("\n### P2: Switch-II residues, per structure ###")
    p2 = _collect(SWITCH_II_RESIDUES, structures)
    for pdb_id, r in p2.items():
        tag = "docked" if pdb_id != DOCKED_AT_SWITCH_I_II and pdb_id != APO_REFERENCE else \
              ("UNDOCKED" if pdb_id == DOCKED_AT_SWITCH_I_II else "apo(excluded)")
        _log(f"  {pdb_id:6s} [{tag:14s}] n={r['n_residues_found']}/{r['n_residues_total']} "
             f"median_V_C={r['median_V_C']}")

    out = dict(
        reference=APO_REFERENCE,
        switch_i_ii_residues=SWITCH_I_II_RESIDUES, switch_ii_residues=SWITCH_II_RESIDUES,
        structures={k: {kk: vv for kk, vv in v.items() if kk != "by_resnum"} for k, v in structures.items()},
        structures_full={k: v for k, v in structures.items()},
        p1_switch_i_ii=p1, p2_switch_ii=p2, p3_fpocket_switch_i_ii=p3,
    )
    (OUT / "docked_undocked_capacity.json").write_text(json.dumps(out, indent=1, default=str))
    _log(f"\nWrote {OUT / 'docked_undocked_capacity.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
