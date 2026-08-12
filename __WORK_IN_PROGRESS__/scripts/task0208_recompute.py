"""TASK-0208 recompute -- the three fixes from the Reviewer verdict (2026-08-07).

The original run's compound AND-gate could not return `OPEN` on any data.
This script re-runs the two legs that were broken, writes to a **separate**
artifact (`results_recompute.json`), and leaves the original `results.json`
untouched as the record.

## V1 -- relaxation, so the frustration signature can express itself

Every `joint` energy in the original run was large and positive (+25.4,
+29.0, +23.5, +114.8), because transplanting rigid holo rotamers onto an apo
backbone always clashes (9/12, 10/12, 5/6, 5/12 of individual swaps were
destabilizing). The pre-registered "textbook frustration signature" requires
`joint < 0`. It could never occur.

Fix: run EvoEF2 `RepairStructure` (0.3 s/call, measured) on every hybrid
before `ComputeStability`, so each configuration is scored at its own relaxed
local minimum rather than at a rigid-transplant clash. This is what makes the
single-vs-joint comparison a coupling measurement instead of a steric-overlap
measurement.

## V2 -- the `not_evaluable` guard, re-keyed

The original guard fired on `abs(sum_singles) < 1e-6`. On KRAS_G12C
`side_chain_explained = 0.036` (the side-chain component barely exists -- the
exact case the guard was written for) but `sum_singles = 25.45`, dominated by
clash energy, so the guard stayed silent and a vacuous cell was reported as a
real "decomposable" result.

Fix: key the guard off `side_chain_explained`, the quantity that actually
says whether there is a side-chain change to measure.

## V3 -- dihedral-space attribution, which the backbone cannot win by carriage

The RMSD reconstructions are not symmetric: `holo_backbone + apo_chi` moves
N/CA/C **and drags every side chain with it**, while `apo_backbone + holo_chi`
moves only atoms beyond C-beta. Backbone therefore collects credit for
displacement the side chains would have undergone anyway. On PTP1B this
produced `backbone_explained = 0.539` ("substantially backbone") for a pocket
whose backbone moves 21.3 deg while its side chains rotate 149.9 deg.

Fix: report an attribution computed in **dihedral space** --
`backbone_share = |d(phi,psi)| / (|d(phi,psi)| + |d(chi)|)` -- normalised per
residue so neither component can win by mechanical carriage. Reported
**alongside** the RMSD numbers, never replacing them: the two measure
different things and the disagreement is itself the finding.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import task0208_apo_holo_decomposition as T208  # noqa: E402
from task0208_apo_holo_decomposition import (  # noqa: E402
    EVOEF2_BIN, EVOEF2_DIR, WINDOW_MAX_SIZE, _angle_diff, _load_full_atom, _log,
    backbone_dihedrals, chi_dihedrals, displacement_rmsd, local_transplant,
    write_hybrid_pdb,
)

from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.labels import (  # noqa: E402
    build_labels, ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue,
)
from allostery.superpose import align_apo_holo, chain_map_from_config, kabsch_apply  # noqa: E402

TARGETS = ["KRAS_G12C", "PTP1B", "CASPASE1", "GLUCOKINASE"]
FRUSTRATION_BAND = 0.30          # unchanged from the original pre-registration
SIDE_CHAIN_MIN_FOR_COUPLING = 0.10  # V2: below this the coupling statistic is vacuous
OUT_DIR = _ROOT / "results_task0208_apo_holo_decomposition"

_TOTAL_RE = re.compile(r"^Total\s*=\s*([-\d.]+)", re.MULTILINE)


def _evoef2(args: list[str], timeout: int = 300):
    return subprocess.run(
        [f"./{EVOEF2_BIN.name}", *args],
        cwd=EVOEF2_DIR, capture_output=True, text=True, timeout=timeout,
    )


def relaxed_stability_total(pdb_path: Path):
    """`RepairStructure` then `ComputeStability` -- V1.

    Without the repair step every hybrid is scored at a rigid-transplant
    clash and `joint` can never go negative, which makes the frustration
    signature unobservable. Returns `(relaxed_total, raw_total)` so the
    original run's numbers stay directly comparable."""
    if not EVOEF2_BIN.exists():
        return {"error": f"EvoEF2 binary not found at {EVOEF2_BIN}"}
    local = EVOEF2_DIR / pdb_path.name
    local.write_bytes(pdb_path.read_bytes())

    raw = _evoef2(["--command=ComputeStability", f"--pdb={local.name}"])
    raw_total = None
    if raw.returncode == 0:
        m = _TOTAL_RE.search(raw.stdout)
        raw_total = float(m.group(1)) if m else None

    rep = _evoef2(["--command=RepairStructure", f"--pdb={local.name}"])
    if rep.returncode != 0:
        return {"error": f"RepairStructure exited {rep.returncode}: {rep.stderr.strip()[:300]}"}
    repaired = EVOEF2_DIR / f"{local.stem}_Repair.pdb"
    if not repaired.exists():
        return {"error": f"RepairStructure produced no {repaired.name}"}

    out = _evoef2(["--command=ComputeStability", f"--pdb={repaired.name}"])
    if out.returncode != 0:
        return {"error": f"ComputeStability(repaired) exited {out.returncode}: {out.stderr.strip()[:300]}"}
    m = _TOTAL_RE.search(out.stdout)
    if not m:
        return {"error": "no 'Total = ...' line after repair"}
    return {"relaxed": float(m.group(1)), "raw": raw_total}


def dihedral_attribution(apo_res, holo_res, apo_to_holo_key, keys) -> dict:
    """V3: per-residue backbone share of the total dihedral change.

    `backbone_share_i = |d(phi)|+|d(psi)| / (|d(phi)|+|d(psi)|+sum|d(chi)|)`,
    then averaged over residues that have both components defined. Scale-free
    and per-residue, so a backbone move cannot inflate it by carrying side
    chains along -- the exact confound in the RMSD reconstruction."""
    shares, bb_only, chi_only = [], 0, 0
    for key in keys:
        a_chain, resnum = key
        h_chain, _ = apo_to_holo_key[key]
        a_phi, a_psi = backbone_dihedrals(apo_res, a_chain, resnum)
        h_phi, h_psi = backbone_dihedrals(holo_res, h_chain, resnum)
        bb = np.nansum([abs(_angle_diff(a_phi, h_phi)), abs(_angle_diff(a_psi, h_psi))])

        resname_a = apo_res[key]["resname"]
        same_resname = resname_a == holo_res.get((h_chain, resnum), {}).get("resname")
        a_chi = chi_dihedrals(resname_a, apo_res[key]["atoms"]) if same_resname else []
        h_chi = chi_dihedrals(resname_a, holo_res[(h_chain, resnum)]["atoms"]) if same_resname else []
        chi = np.nansum([abs(_angle_diff(x, y)) for x, y in zip(a_chi, h_chi)]) if (a_chi and h_chi) else np.nan

        if not np.isfinite(bb) and not np.isfinite(chi):
            continue
        if not np.isfinite(chi):          # glycine/alanine: no chi to compare
            bb_only += 1
            continue
        if not np.isfinite(bb):
            chi_only += 1
            continue
        total = bb + chi
        if total > 1e-9:
            shares.append(bb / total)

    return {
        "mean_backbone_share": float(np.mean(shares)) if shares else float("nan"),
        "median_backbone_share": float(np.median(shares)) if shares else float("nan"),
        "n_residues_scored": len(shares),
        "n_backbone_only_residues": bb_only,
        "n_chi_only_residues": chi_only,
    }


def run_target(target_name: str) -> dict:
    t0 = time.monotonic()
    _log(f"=== {target_name} (recompute) ===")
    cfg = load_target_config(target_name)
    apo_ca = clean_from_config(target_name, role="apo")
    holo_ca = clean_from_config(target_name, role="holo")
    chain_map = chain_map_from_config(cfg)

    import prody as _prody
    _prody.confProDy(verbosity="none")
    holo_chains_lbl = cfg.get("holo_chains") or cfg.get("chains") or sorted(set(holo_ca.chain_ids))
    holo_struct = _prody.parsePDB(cfg["holo_pdb"], compressed=False).select(
        " or ".join(f"chain {c}" for c in holo_chains_lbl))
    holo_ca.ligand_groups = ligand_groups_from_atomgroup(holo_struct)
    holo_ca.heavy_atom_coords, holo_ca.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
        holo_struct, holo_chains_lbl, holo_ca.resnums)

    alignment = align_apo_holo(apo_ca, holo_ca, chain_map=chain_map)
    apo_chains = cfg.get("apo_chains") or cfg.get("chains") or sorted(set(apo_ca.chain_ids))
    holo_chains = cfg.get("holo_chains") or cfg.get("chains") or sorted(set(holo_ca.chain_ids))
    apo_res, apo_ag = _load_full_atom(cfg["apo_pdb"], apo_chains)
    holo_res, _ = _load_full_atom(cfg["holo_pdb"], holo_chains)

    holo_aligned = {}
    for key, entry in holo_res.items():
        holo_aligned[key] = {"resname": entry["resname"], "atoms": {
            n: kabsch_apply(xyz.reshape(1, 3), alignment.R, alignment.mobile_centroid,
                            alignment.ref_centroid)[0]
            for n, xyz in entry["atoms"].items()}}

    inv_map = {v: k for k, v in (chain_map or {}).items()}
    common = [(a, r, inv_map.get(a, a)) for (a, r) in apo_res
              if (inv_map.get(a, a), r) in holo_aligned]
    common_apo = {(a, r) for (a, r, _h) in common}
    apo_to_holo_key = {(a, r): (h, r) for (a, r, h) in common}

    labels = build_labels(apo_ca, holo_ca, cfg)
    if labels.pocket is None:
        return {"target": target_name, "error": "no resolvable pocket label"}
    chain_arr = np.asarray(apo_ca.chain_ids)
    pocket_keys = [k for k in
                   [(str(chain_arr[i]), int(apo_ca.resnums[i])) for i in np.where(labels.pocket)[0]]
                   if k in common_apo]
    if len(pocket_keys) > WINDOW_MAX_SIZE:
        cen = np.array([apo_res[k]["atoms"]["CA"] for k in pocket_keys]).mean(axis=0)
        d = np.array([np.linalg.norm(apo_res[k]["atoms"]["CA"] - cen) for k in pocket_keys])
        pocket_keys = [pocket_keys[i] for i in np.argsort(d)[:WINDOW_MAX_SIZE]]
    if not pocket_keys:
        return {"target": target_name, "error": "empty pocket window after common-set filter"}

    cen = np.array([apo_res[k]["atoms"]["CA"] for k in pocket_keys]).mean(axis=0)
    non_pocket = [k for k in common_apo if k not in set(pocket_keys) and "CA" in apo_res[k]["atoms"]]
    dd = np.array([np.linalg.norm(apo_res[k]["atoms"]["CA"] - cen) for k in non_pocket])
    distal_keys = [non_pocket[i] for i in np.argsort(dd)[::-1][: len(pocket_keys)]]

    # --- V3: dihedral-space attribution (pocket + distal control) ---
    dih_pocket = dihedral_attribution(apo_res, holo_aligned, apo_to_holo_key, pocket_keys)
    dih_distal = dihedral_attribution(apo_res, holo_aligned, apo_to_holo_key, distal_keys)
    _log(f"dihedral backbone share: pocket={dih_pocket['mean_backbone_share']:.3f} "
         f"distal={dih_distal['mean_backbone_share']:.3f}")

    # --- side_chain_explained, recomputed identically to the original (for the V2 guard) ---
    hybrid_sc = {}
    for k in pocket_keys:
        h_key = apo_to_holo_key[k]
        t = local_transplant(donor_atoms=holo_aligned[h_key]["atoms"], acceptor_atoms=apo_res[k]["atoms"])
        if t is not None:
            hybrid_sc[k] = {"resname": apo_res[k]["resname"], "atoms": t}
    true_holo_at_pocket = {k: holo_aligned[apo_to_holo_key[k]] for k in pocket_keys}
    rmsd_raw = displacement_rmsd(apo_res, true_holo_at_pocket, pocket_keys)
    rmsd_sc = displacement_rmsd(hybrid_sc, true_holo_at_pocket, list(hybrid_sc))
    side_chain_explained = 1.0 - (rmsd_sc / rmsd_raw) if rmsd_raw > 1e-9 else float("nan")

    # --- V1 + V2: relaxed coupling statistic ---
    coupling: dict = {"attempted": False}
    if not np.isfinite(side_chain_explained) or side_chain_explained < SIDE_CHAIN_MIN_FOR_COUPLING:
        coupling = {
            "attempted": False,
            "verdict": "not_evaluable_side_chain_component_negligible",
            "side_chain_explained": side_chain_explained,
            "guard": f"side_chain_explained < {SIDE_CHAIN_MIN_FOR_COUPLING}",
            "note": ("V2: the original run keyed this guard off |sum_singles| < 1e-6, which "
                     "is dominated by clash energy and stayed silent here."),
        }
        _log(f"coupling: NOT EVALUABLE (side_chain_explained={side_chain_explained:.3f})")
    elif EVOEF2_BIN.exists() and hybrid_sc:
        chids, resnums, names = apo_ag.getChids(), apo_ag.getResnums(), apo_ag.getNames()
        base_path = EVOEF2_DIR / f"{target_name.lower()}_t208r_baseline.pdb"
        _prody.writePDB(str(base_path), apo_ag)
        e_base = relaxed_stability_total(base_path)
        if isinstance(e_base, dict) and "error" in e_base:
            coupling = {"attempted": True, "error": e_base["error"]}
        else:
            singles_rel, singles_raw = {}, {}
            for k in hybrid_sc:
                p = EVOEF2_DIR / f"{target_name.lower()}_t208r_single_{k[0]}{k[1]}.pdb"
                write_hybrid_pdb(apo_ag, chids, resnums, names, {k: hybrid_sc[k]["atoms"]}, p)
                e = relaxed_stability_total(p)
                if isinstance(e, dict) and "error" in e:
                    singles_rel[f"{k[0]}{k[1]}"] = e
                else:
                    singles_rel[f"{k[0]}{k[1]}"] = e["relaxed"] - e_base["relaxed"]
                    singles_raw[f"{k[0]}{k[1]}"] = (e["raw"] - e_base["raw"]) if (
                        e["raw"] is not None and e_base["raw"] is not None) else None
            jp = EVOEF2_DIR / f"{target_name.lower()}_t208r_joint.pdb"
            write_hybrid_pdb(apo_ag, chids, resnums, names,
                             {k: hybrid_sc[k]["atoms"] for k in hybrid_sc}, jp)
            e_joint = relaxed_stability_total(jp)

            vals = [v for v in singles_rel.values() if isinstance(v, (int, float))]
            sum_singles = float(np.sum(vals)) if vals else float("nan")
            if isinstance(e_joint, dict) and "error" in e_joint:
                coupling = {"attempted": True, "error": e_joint["error"], "singles_relaxed": singles_rel}
            else:
                joint = e_joint["relaxed"] - e_base["relaxed"]
                gap = sum_singles - joint
                frustrated = bool(gap >= FRUSTRATION_BAND * abs(sum_singles)) if abs(sum_singles) > 1e-9 else False
                coupling = {
                    "attempted": True, "relaxed": True,
                    "sum_singles": sum_singles, "joint": joint, "gap": gap,
                    "gap_pct": float(100 * gap / abs(sum_singles)) if abs(sum_singles) > 1e-9 else float("nan"),
                    "frustrated": frustrated,
                    "any_individually_unfavorable_single": bool(any(v > 0 for v in vals)),
                    "joint_favorable": bool(joint < 0),
                    "strong_frustration_signature": bool(
                        frustrated and any(v > 0 for v in vals) and joint < 0),
                    "singles_relaxed": singles_rel,
                    "singles_raw_unrelaxed": singles_raw,
                }
                _log(f"coupling(relaxed): sum_singles={sum_singles:.2f} joint={joint:.2f} "
                     f"gap={coupling['gap_pct']:.1f}% frustrated={frustrated} joint<0={joint < 0}")

    return {
        "target": target_name,
        "pocket_window": [f"{c}{r}" for c, r in pocket_keys],
        "side_chain_explained": side_chain_explained,
        "dihedral_attribution_pocket": dih_pocket,
        "dihedral_attribution_distal": dih_distal,
        "coupling_relaxed": coupling,
        "elapsed_s": round(time.monotonic() - t0, 1),
    }


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    results = []
    for name in TARGETS:
        try:
            results.append(run_target(name))
        except Exception as exc:  # noqa: BLE001
            _log(f"{name}: ERROR {type(exc).__name__}: {exc}")
            results.append({"target": name, "error": f"{type(exc).__name__}: {exc}"})
        (OUT_DIR / "results_recompute.json").write_text(json.dumps(results, indent=1))

    print("\n=== TASK-0208 recompute ===")
    print(f"{'target':<14} {'sc_expl':>8} {'bb_share_pkt':>13} {'bb_share_dist':>14} "
          f"{'sum_sing':>9} {'joint':>8} {'gap%':>7} {'frustrated':>11}")
    for r in results:
        if "error" in r:
            print(f"{r['target']:<14} ERROR {r['error']}")
            continue
        c = r["coupling_relaxed"]
        dp, dd = r["dihedral_attribution_pocket"], r["dihedral_attribution_distal"]
        if not c.get("attempted"):
            print(f"{r['target']:<14} {r['side_chain_explained']:>8.3f} "
                  f"{dp['mean_backbone_share']:>13.3f} {dd['mean_backbone_share']:>14.3f} "
                  f"{'—':>9} {'—':>8} {'—':>7} {'not evaluable':>11}")
        else:
            print(f"{r['target']:<14} {r['side_chain_explained']:>8.3f} "
                  f"{dp['mean_backbone_share']:>13.3f} {dd['mean_backbone_share']:>14.3f} "
                  f"{c.get('sum_singles', float('nan')):>9.2f} {c.get('joint', float('nan')):>8.2f} "
                  f"{c.get('gap_pct', float('nan')):>7.1f} {str(c.get('frustrated')):>11}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
