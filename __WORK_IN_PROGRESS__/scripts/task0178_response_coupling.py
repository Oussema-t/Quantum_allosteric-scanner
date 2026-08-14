#!/usr/bin/env python3
"""TASK-0178 -- binding-response coupling (Phase B): real-target run.

Per this task's own Constraint: **report rho(score, -hop) BEFORE any AUC**.
If the shell-normalisation did not materially remove the proximity trend on
real data, that is the result -- reported honestly either way.

Scores `coupling_specificity` (and, separately, raw |ddG| for the
proximity-confound comparison) against all three of [[TASK-0177]]'s labels
(incumbent/core/consensus, read directly from `targets.yaml`'s frozen
`pocket_label` block -- not recomputed).
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import numpy as np  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.consensus_labels import load_apo_holo_full  # noqa: E402
from allostery.hamiltonians import contact_matrix, laplacian  # noqa: E402
from allostery.labels import functional_indices  # noqa: E402
from allostery.metrics import auc  # noqa: E402
from allostery.response import coupling_free_energy, coupling_profile, coupling_specificity  # noqa: E402

TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "PTP1B", "GLUCOKINASE", "CASPASE1", "CASPASE7"]
KAPPA = 1.0
PATCH_SIZE = 6


def _label_mask_from_pairs(pairs, apo) -> np.ndarray:
    n = len(apo.resnums)
    mask = np.zeros(n, dtype=bool)
    lookup = {(c, int(r)): i for i, (c, r) in enumerate(zip(apo.chain_ids, apo.resnums))}
    for c, r in pairs:
        i = lookup.get((c, int(r)))
        if i is not None:
            mask[i] = True
    return mask


def _to_jsonable(obj):
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    return obj


def run_target(name: str) -> dict:
    t0 = time.monotonic()
    print(f"[task0178] {name}: loading...", file=sys.stderr)
    cfg = load_target_config(name)
    cutoff = float(cfg.get("enm_cutoff", 8.0))

    apo, holo, apo_raw, holo_raw, apo_chains, holo_chains = load_apo_holo_full(name, cfg)
    _heavy_atom_coords = getattr(holo, "heavy_atom_coords", None)
    func_idx, _prov = functional_indices(
        apo.coords, holo.ligand_groups, cfg, cutoff=float(cfg.get("pocket_contact_cutoff", 4.5)),
        heavy_atom_coords=_heavy_atom_coords,
        heavy_atom_seq_index=getattr(holo, "heavy_atom_seq_index", None),
        heavy_atom_resnames=(holo.resnames if _heavy_atom_coords is not None else None),
        coords_resnames=(apo.resnames if _heavy_atom_coords is not None else None),
    )
    active_idx = np.sort(func_idx)

    K = laplacian(contact_matrix(apo.coords, cutoff=cutoff, weight="binary"))
    print(f"[task0178] {name}: N={len(apo.resnums)}, computing coupling profile...", file=sys.stderr)
    profile = coupling_profile(K, active_idx, apo.coords, kappa=KAPPA, patch_size=PATCH_SIZE)

    hop = -hop_from_seed(apo.coords, active_idx, cutoff=cutoff)
    score = coupling_specificity(profile, hop)

    # --- report rho(score,-hop) BEFORE any AUC, per the Constraint ---
    rho_raw = float(spearmanr(np.abs(profile), -hop).statistic)
    rho_specificity = float(spearmanr(score, -hop).statistic)

    pocket_label = cfg.get("pocket_label", {})
    labels = {}
    for key, yaml_key in (("incumbent", "incumbent_4_5A"), ("core", "core"), ("consensus", "consensus")):
        pairs = pocket_label.get(yaml_key)
        labels[key] = _label_mask_from_pairs(pairs, apo) if pairs else None

    result = {
        "target": name,
        "n_residues": len(apo.resnums),
        "n_active_site": int(len(active_idx)),
        "kappa": KAPPA,
        "patch_size": PATCH_SIZE,
        "rho_raw_abs_ddg_vs_neg_hop": rho_raw,
        "rho_specificity_vs_neg_hop": rho_specificity,
        "scoring": {},
    }

    for label_name, mask in labels.items():
        if mask is None or not mask.any():
            result["scoring"][label_name] = {"available": False}
            continue
        eligible = ~active_idx_mask(len(apo.resnums), active_idx)
        floor_scores = {
            "degree_centrality": degree_centrality(apo.coords, cutoff=cutoff),
            "euclid_from_seed_centroid": euclid_from_seed_centroid(apo.coords, active_idx),
            "hop_from_seed": hop_from_seed(apo.coords, active_idx, cutoff=cutoff),
        }
        floor_auc = max(auc(s[eligible], mask[eligible].astype(int)) for s in floor_scores.values())
        result["scoring"][label_name] = {
            "available": True,
            "n_pocket": int(mask.sum()),
            "floor_auc": floor_auc,
            "auc_raw_abs_ddg": auc(np.abs(profile)[eligible], mask[eligible].astype(int)),
            "auc_specificity": auc(score[eligible], mask[eligible].astype(int)),
        }

    result["elapsed_s"] = round(time.monotonic() - t0, 1)
    print(f"[task0178] {name}: rho_raw={rho_raw:.3f} rho_specificity={rho_specificity:.3f} "
          f"done in {result['elapsed_s']}s", file=sys.stderr)
    return result


def active_idx_mask(n, active_idx):
    m = np.zeros(n, dtype=bool)
    m[active_idx] = True
    return m


def main() -> int:
    out = {}
    for name in TARGETS:
        try:
            out[name] = run_target(name)
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            out[name] = {"target": name, "error": f"{type(exc).__name__}: {exc}"}

    out_dir = Path(__file__).resolve().parent.parent / "results_task0178_response_coupling"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(_to_jsonable(out), indent=2, default=str))
    print(f"\nWrote {out_path}")

    print("\n=== TASK-0178 rho(score,-hop) BEFORE any AUC ===")
    for name, r in out.items():
        if "error" in r:
            print(f"{name:16s} ERROR: {r['error']}")
            continue
        print(f"{name:16s} rho_raw={r['rho_raw_abs_ddg_vs_neg_hop']:+.3f}  rho_specificity={r['rho_specificity_vs_neg_hop']:+.3f}")

    print("\n=== AUC vs floor, per label ===")
    for name, r in out.items():
        if "error" in r:
            continue
        for label_name, s in r["scoring"].items():
            if not s.get("available"):
                continue
            print(f"{name:16s} {label_name:10s} floor={s['floor_auc']:.3f}  raw|ddG|={s['auc_raw_abs_ddg']:.3f}  specificity={s['auc_specificity']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
