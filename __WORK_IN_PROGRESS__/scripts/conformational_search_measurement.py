#!/usr/bin/env python3
"""TASK-0185 -- the one real-data measurement this task's Intent Contract
asks for: generate closed-form ENM equilibrium ensembles (no MD, no
integrator -- same §Constraint 3 argument as [[TASK-0187]]) for the
mandatory apo structures, run the already-vendored fpocket ([[TASK-0163]])
across each sampled conformation, and report (a) does the known holo
pocket appear in any sampled conformation, (b) at what frequency, and
(c) is that frequency specific to the real pocket vs. a random distal
patch (negative control).

Deliberately a single measurement script, not a new pipeline module --
this task's own Out Of Scope is explicit that building the search
pipeline is not authorized before the freeze. Reuses, does not
re-derive:
  - `allostery.shortcuts.equipartition_ensemble`/`msf_cross_check`
    ([[TASK-0187]]) for the ENM sampler and its blocking MSF gate.
  - `allostery.plant.select_distal_patch` ([[TASK-0167.001]]) for the
    negative-control decoy patch.
  - `_write_full_atom_apo_pdb`/`_run_fpocket`/`FPOCKET_BIN` from
    `scripts/task0163_external_baseline_scoring.py`, ported (not
    reimplemented) -- the one already-tested real fpocket invocation
    recipe in this repo.

New in this script (not elsewhere): `_apply_ca_displacement`, a rigid
per-residue translation that moves every atom of residue (chain, resnum)
by that residue's own Cα ENM displacement vector -- the cheapest
closed-form way to get a full-atom structure fpocket can read from a
Cα-only ENM sample (bond lengths and side-chain conformation held fixed,
only rigid-body position moves). This is an approximation, stated
explicitly in the write-up, not hidden.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
_SCRIPTS = Path(__file__).resolve().parent
for _p in (_SRC, _SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.labels import build_labels, ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue  # noqa: E402
from allostery.plant import select_distal_patch  # noqa: E402
from allostery.hamiltonians import contact_matrix  # noqa: E402
from allostery.runlog import RunLogger  # noqa: E402
from allostery.shortcuts import equipartition_ensemble, msf_cross_check  # noqa: E402
from task0163_external_baseline_scoring import (  # noqa: E402
    FPOCKET_BIN,
    _run_fpocket,
    _write_full_atom_apo_pdb,
)

HOP_CUTOFF = 8.0
N_MODES = 20
KT = 20.0  # matches TASK-0187's own kT choice, TASK-0185's reference prototype's real sweep value
N_ENSEMBLE = 100
N_MODES_SWEEP = (5, 20, 40)
N_ENSEMBLE_SWEEP = 60
POCKET_HIT_OVERLAP = 0.5  # fraction of real pocket residues a single detected fpocket cavity must cover to count as "found"
DEFAULT_POCKET_CUTOFF = 4.5

TARGETS = ["BCR_ABL1", "KRAS_G12C", "CARDIAC_MYOSIN"]  # BCR_ABL1 first -- positive control, run before trusting anything else


def _load_apo_holo(target_name: str, target_config: dict):
    import prody

    apo = clean_from_config(target_name, role="apo")
    holo = clean_from_config(target_name, role="holo")

    prody.confProDy(verbosity="none")
    holo_id = target_config["holo_pdb"]
    chains = target_config.get("chains") or sorted(set(holo.chain_ids))
    chain_sel = " or ".join(f"chain {c}" for c in chains)
    holo_struct = prody.parsePDB(holo_id, compressed=False).select(chain_sel)
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)
    holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
        holo_struct, chains, holo.resnums
    )
    return apo, holo


def _load_full_atom_template(target_config: dict, apo_chains):
    """The same full-atom `struct_clean` `_write_full_atom_apo_pdb` writes
    to disk, kept in memory so displaced copies can be built repeatedly
    without re-parsing the PDB every sample."""
    import prody

    prody.confProDy(verbosity="none")
    struct = prody.parsePDB(target_config["apo_pdb"], compressed=False)
    alt_locs = struct.getAltlocs()
    if alt_locs is not None and any(a not in ("", " ", "\x00") for a in alt_locs):
        struct = struct.select("altloc _ A") or struct
    chain_part = " and (" + " or ".join(f"chain {c}" for c in apo_chains) + ")"
    return struct.select(f"protein{chain_part}")


def _apply_ca_displacement(template, chain_ids, resnums, displacement):
    disp_map = {(c, int(r)): d for c, r, d in zip(chain_ids, resnums, displacement)}
    atom_chains = template.getChids()
    atom_resnums = template.getResnums()
    coords = template.getCoords().copy()
    n_unmatched = 0
    for i in range(len(coords)):
        d = disp_map.get((atom_chains[i], int(atom_resnums[i])))
        if d is not None:
            coords[i] = coords[i] + d
        else:
            n_unmatched += 1
    displaced = template.copy()
    displaced.setCoords(coords)
    return displaced, n_unmatched


def _pockets_overlap_frac(pockets: list, target_set: set) -> float:
    if not target_set or not pockets:
        return 0.0
    best = 0.0
    for p in pockets:
        frac = len(p["residues"] & target_set) / len(target_set)
        best = max(best, frac)
    return best


def _run_ensemble_fpocket(
    template, chain_ids, resnums, ensemble, real_pocket_set, decoy_set, log: RunLogger, label: str,
) -> dict:
    import prody

    n_samples = ensemble.displacements.shape[0]
    real_fracs = np.zeros(n_samples)
    decoy_fracs = np.zeros(n_samples)
    errors = 0
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for i in range(n_samples):
            displaced, n_unmatched = _apply_ca_displacement(template, chain_ids, resnums, ensemble.displacements[i])
            pdb_path = tmp / f"sample_{i}.pdb"
            prody.writePDB(str(pdb_path), displaced)
            pockets = _run_fpocket(pdb_path, tmp)
            if isinstance(pockets, dict) and "error" in pockets:
                errors += 1
                continue
            real_fracs[i] = _pockets_overlap_frac(pockets, real_pocket_set)
            decoy_fracs[i] = _pockets_overlap_frac(pockets, decoy_set)
        log.step(
            f"{label}:ensemble_fpocket_done",
            n_samples=n_samples, errors=errors,
            real_hit_rate=float((real_fracs >= POCKET_HIT_OVERLAP).mean()),
            decoy_hit_rate=float((decoy_fracs >= POCKET_HIT_OVERLAP).mean()),
        )
    return {
        "n_samples": n_samples, "errors": errors,
        "real_fracs": real_fracs, "decoy_fracs": decoy_fracs,
        "real_hit_rate": float((real_fracs >= POCKET_HIT_OVERLAP).mean()),
        "decoy_hit_rate": float((decoy_fracs >= POCKET_HIT_OVERLAP).mean()),
        "real_mean_overlap": float(real_fracs.mean()),
        "decoy_mean_overlap": float(decoy_fracs.mean()),
    }


def run_target(name: str, log: RunLogger, run_sweep: bool) -> dict:
    t0 = time.monotonic()
    target_config = load_target_config(name)
    apo, holo = _load_apo_holo(name, target_config)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)

    if labels_obj.pocket is None or not labels_obj.pocket.any():
        return {"target": name, "ok": False, "reason": "no resolvable pocket label"}
    if not labels_obj.active_site.any():
        return {"target": name, "ok": False, "reason": "no resolvable active site"}

    pocket_idx = np.where(labels_obj.pocket)[0]
    active_idx = np.where(labels_obj.active_site)[0]
    real_pocket_set = {(apo.chain_ids[i], int(apo.resnums[i])) for i in pocket_idx}
    log.step(f"{name}:labels", n_residues=len(apo.resnums), n_active=len(active_idx), n_pocket=len(pocket_idx))

    # negative control: a matched-size distal decoy, same reused primitive as TASK-0187
    W = contact_matrix(apo.coords, cutoff=HOP_CUTOFF, weight="invdist")
    decoy_idx = select_distal_patch(
        apo.coords, W, active_idx, len(pocket_idx), np.random.default_rng(0), cutoff=HOP_CUTOFF,
    )
    decoy_set = {(apo.chain_ids[i], int(apo.resnums[i])) for i in decoy_idx}

    apo_chains = target_config.get("apo_chains") or target_config.get("chains")
    template = _load_full_atom_template(target_config, apo_chains)

    # Step 1 (blocking): ensemble + MSF cross-check at the primary n_modes/kT.
    ensemble = equipartition_ensemble(
        apo.coords, cutoff=HOP_CUTOFF, n_modes=N_MODES, kT=KT, n_samples=N_ENSEMBLE,
        rng=np.random.default_rng(0),
    )
    msf_check = msf_cross_check(ensemble)
    log.step(f"{name}:msf_cross_check", **msf_check)
    if not msf_check["ok"]:
        return {
            "target": name, "ok": False,
            "reason": "MSF cross-check failed -- sampler not trustworthy, stopping before fpocket (blocking constraint)",
            "msf_cross_check": msf_check,
        }

    # sanity: static apo through fpocket (zero perturbation) -- must succeed before the ensemble is worth trusting.
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        pdb_path = tmp / f"{name}_apo_static.pdb"
        _write_full_atom_apo_pdb(target_config, apo_chains, pdb_path)
        static_pockets = _run_fpocket(pdb_path, tmp)
        static_real_frac = _pockets_overlap_frac(static_pockets, real_pocket_set) if isinstance(static_pockets, list) else None
    log.step(f"{name}:static_apo_fpocket", static_real_frac=static_real_frac)

    main = _run_ensemble_fpocket(template, apo.chain_ids, apo.resnums, ensemble, real_pocket_set, decoy_set, log, name)

    sweep = {}
    if run_sweep:
        for nm in N_MODES_SWEEP:
            if nm == N_MODES:
                continue  # N_MODES's own main-run ensemble already covers this point, at N_ENSEMBLE not N_ENSEMBLE_SWEEP -- reported separately below, not duplicated
            ens_nm = equipartition_ensemble(
                apo.coords, cutoff=HOP_CUTOFF, n_modes=nm, kT=KT, n_samples=N_ENSEMBLE_SWEEP,
                rng=np.random.default_rng(nm),
            )
            mc_nm = msf_cross_check(ens_nm)
            if not mc_nm["ok"]:
                sweep[nm] = {"ok": False, "msf_cross_check": mc_nm}
                continue
            res_nm = _run_ensemble_fpocket(
                template, apo.chain_ids, apo.resnums, ens_nm, real_pocket_set, decoy_set, log, f"{name}:sweep_n{nm}",
            )
            sweep[nm] = {"ok": True, "msf_cross_check": mc_nm, **{k: v for k, v in res_nm.items() if not k.endswith("_fracs")}}

    result = {
        "target": name, "ok": True,
        "n_residues": int(len(apo.resnums)), "n_pocket": int(len(pocket_idx)), "n_active": int(len(active_idx)),
        "msf_cross_check": msf_check,
        "static_apo_real_overlap_frac": static_real_frac,
        "n_modes": N_MODES, "kT": KT, "n_ensemble": N_ENSEMBLE,
        "real_hit_rate": main["real_hit_rate"], "decoy_hit_rate": main["decoy_hit_rate"],
        "real_mean_overlap": main["real_mean_overlap"], "decoy_mean_overlap": main["decoy_mean_overlap"],
        "n_errors": main["errors"],
        "n_modes_sweep": sweep,
        "elapsed_s": round(time.monotonic() - t0, 1),
    }
    return result


def main() -> int:
    out_dir = Path(__file__).resolve().parent.parent / "results_task0185_conformational_search"
    out_dir.mkdir(exist_ok=True)
    log = RunLogger(out_dir / "run.jsonl", run_name="task0185_conformational_search")

    if not FPOCKET_BIN.exists():
        print(f"FATAL: fpocket binary not found at {FPOCKET_BIN}", file=sys.stderr)
        return 1

    targets = sys.argv[1:] or TARGETS
    out = []
    for name in targets:
        print(f"{name}: running...", file=sys.stderr)
        try:
            r = run_target(name, log, run_sweep=(name == "BCR_ABL1"))
        except Exception as exc:  # noqa: BLE001 -- diagnostic script, report and continue
            import traceback
            traceback.print_exc()
            r = {"target": name, "ok": False, "reason": f"{type(exc).__name__}: {exc}"}
        print(f"{name}: ok={r.get('ok')} reason={r.get('reason')}", file=sys.stderr)
        out.append(r)

    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    log.finish(n_targets=len(targets))
    print(f"\nWrote {out_path}")

    for r in out:
        if not r.get("ok"):
            print(f"{r['target']:16s} FAILED: {r.get('reason')}")
            continue
        print(
            f"{r['target']:16s} static={r['static_apo_real_overlap_frac']}  "
            f"real_hit_rate={r['real_hit_rate']:.3f}  decoy_hit_rate={r['decoy_hit_rate']:.3f}  "
            f"real_mean_overlap={r['real_mean_overlap']:.3f}  decoy_mean_overlap={r['decoy_mean_overlap']:.3f}  "
            f"errors={r['n_errors']}/{r['n_ensemble']}"
        )
        for nm, s in r["n_modes_sweep"].items():
            if s.get("ok"):
                print(f"    n_modes={nm}: real_hit_rate={s['real_hit_rate']:.3f} decoy_hit_rate={s['decoy_hit_rate']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
