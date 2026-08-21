#!/usr/bin/env python3
"""TASK-0187 -- ENM-induced connectivity-graph shortcut hypothesis, Steps
1-4, run on the positive-control target (PTP1B, chosen from TASK-0186's
own numbers -- see the task file's Design section).

Step 1: closed-form ANM equipartition ensemble + blocking MSF cross-check.
Step 2: per-sample hop-distance recomputation for the real pocket.
Step 3: pre-registered specificity test vs. 30 matched decoys
        (`plant.select_distal_patch`) -- the task file's own criterion,
        fixed before this script was written.
Step 4: comparison to the real holo-native contact-graph hop-distance.

Loading pattern (config/apo/holo/labels) ported from
`scripts/hop_distance_generalization_audit.py::_load_apo_holo`/`audit_one`
-- not re-derived, same already-tested recipe against live RCSB data.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
_TESTS = Path(__file__).resolve().parent.parent / "tests"
for _p in (_SRC, _TESTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.labels import build_labels, ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue  # noqa: E402
from allostery.runlog import RunLogger  # noqa: E402
from allostery.shortcuts import (  # noqa: E402
    ensemble_hop_matrix,
    equipartition_ensemble,
    msf_cross_check,
    patch_hop_distance,
    shortcut_rate,
    specificity_test,
)
from test_gnm_cutoff_weight_benchmark import _holo_native_labels  # noqa: E402

HOP_CUTOFF = 8.0  # TASK-0067's retained contact scale -- do not invent a new one.
N_ENSEMBLE = 2000
N_MODES = 20
KT = 20.0  # matches TASK-0185 reference prototype's actual sweep value, not its kT=1.0 default.
N_DECOY = 30
DECOY_HOP_PERCENTILE = 60.0
DECOY_MAX_FLOOR_AUC = 0.5
EFFECT_SIZE_FLOOR = 0.10
DEFAULT_POCKET_CUTOFF = 4.5


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


def run_target(name: str, log: RunLogger) -> dict:
    t0 = time.monotonic()
    target_config = load_target_config(name)
    apo, holo = _load_apo_holo(name, target_config)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)

    if labels_obj.pocket is None or not labels_obj.pocket.any():
        return {"target": name, "ok": False, "reason": "no resolvable pocket label"}
    if not labels_obj.active_site.any():
        return {"target": name, "ok": False, "reason": "no resolvable active site"}

    active_idx = np.where(labels_obj.active_site)[0]
    pocket_idx = np.where(labels_obj.pocket)[0]
    log.step(f"{name}:labels", n_residues=len(apo.resnums), n_active=len(active_idx), n_pocket=len(pocket_idx))

    # Step 1 -- ensemble + blocking MSF cross-check.
    ensemble = equipartition_ensemble(
        apo.coords, cutoff=HOP_CUTOFF, n_modes=N_MODES, kT=KT, n_samples=N_ENSEMBLE,
        rng=np.random.default_rng(0),
    )
    msf_check = msf_cross_check(ensemble)
    log.step(f"{name}:msf_cross_check", **{k: v for k, v in msf_check.items()})
    if not msf_check["ok"]:
        return {
            "target": name, "ok": False,
            "reason": "MSF cross-check failed -- sampler not trustworthy, stopping before Step 2 (blocking constraint)",
            "msf_cross_check": msf_check,
        }

    # Step 2 -- real-pocket shortcut rate.
    hop_matrix = ensemble_hop_matrix(ensemble, apo.coords, active_idx, cutoff=HOP_CUTOFF)
    real_shortcut = shortcut_rate(hop_matrix, apo.coords, active_idx, pocket_idx, cutoff=HOP_CUTOFF)
    log.step(f"{name}:step2_real_pocket", static_hop=real_shortcut["static_hop"], rate=real_shortcut["rate"], min_sample_hop=real_shortcut["min_sample_hop"])

    # Step 3 -- pre-registered specificity test vs. matched decoys.
    spec = specificity_test(
        ensemble, apo.coords, active_idx, pocket_idx, cutoff=HOP_CUTOFF,
        n_decoy=N_DECOY, decoy_hop_percentile=DECOY_HOP_PERCENTILE,
        decoy_max_floor_auc=DECOY_MAX_FLOOR_AUC, effect_size_floor=EFFECT_SIZE_FLOOR,
        rng=np.random.default_rng(1), hop_matrix=hop_matrix,
    )
    log.step(
        f"{name}:step3_specificity",
        passed=spec["passed"], significant=spec["significant"], material=spec["material"],
        real_rate=spec["real_rate"], decoy_p95=spec["decoy_p95"], decoy_median=spec["decoy_median"],
        effect_size=spec["effect_size"],
    )

    # Step 4 -- comparison to real holo-native topology.
    holo_pocket_mask, holo_active_mask, _ = _holo_native_labels(holo, target_config, pocket_cutoff)
    holo_target_hop = None
    if holo_pocket_mask.any() and holo_active_mask.any():
        holo_active_idx = np.where(holo_active_mask)[0]
        holo_pocket_idx = np.where(holo_pocket_mask)[0]
        holo_target_hop = patch_hop_distance(holo.coords, holo_active_idx, holo_pocket_idx, cutoff=HOP_CUTOFF)
    log.step(f"{name}:step4_holo_native", holo_target_hop=holo_target_hop)

    result = {
        "target": name, "ok": True,
        "n_residues": int(len(apo.resnums)),
        "n_active_site": int(len(active_idx)),
        "n_pocket": int(len(pocket_idx)),
        "hop_cutoff_A": HOP_CUTOFF,
        "n_ensemble": N_ENSEMBLE, "n_modes": N_MODES, "kT": KT,
        "msf_cross_check": msf_check,
        "step2_real_pocket": {k: v for k, v in real_shortcut.items() if k != "sample_hops"},
        "step3_specificity": {k: (v.tolist() if isinstance(v, np.ndarray) else [p.tolist() for p in v] if k == "decoy_patches" else v) for k, v in spec.items()},
        "step4_holo_native_target_hop": holo_target_hop,
        "elapsed_s": round(time.monotonic() - t0, 1),
    }
    return result


def main() -> int:
    out_dir = Path(__file__).resolve().parent.parent / "results/tasks/0187_shortcut_hypothesis"
    out_dir.mkdir(exist_ok=True)
    log = RunLogger(out_dir / "run.jsonl", run_name="task0187_shortcut_hypothesis")

    targets = sys.argv[1:] or ["PTP1B"]
    out = []
    for name in targets:
        print(f"{name}: running...", file=sys.stderr)
        try:
            r = run_target(name, log)
        except Exception as exc:  # noqa: BLE001 -- diagnostic script, report and continue
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
        s2, s3 = r["step2_real_pocket"], r["step3_specificity"]
        print(
            f"{r['target']:16s} static_hop={s2['static_hop']:.0f}  real_rate={s2['rate']:.3f}  "
            f"decoy_median={s3['decoy_median']:.3f} decoy_p95={s3['decoy_p95']:.3f}  "
            f"effect_size={s3['effect_size']:.3f}  PASSED={s3['passed']}  "
            f"holo_target_hop={r['step4_holo_native_target_hop']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
