#!/usr/bin/env python3
"""TASK-0156 -- pre-registered kill-switch (run FIRST, before any scoring).

On KRAS_G12C (this project's standard apo/holo pair, 4OBE/6OIM -- 4OBE is
confirmed wild-type, not literal G12C, a known and already-accepted
caveat, TASK-0155/TASK-0192, kept unchanged): compute `control_effort.
scan_control_effort`'s `E_i` for every residue, correlate with graph-hop
and Euclidean distance from the active-site seed.

Pre-registered rule (task file's own Intent Contract, fixed BEFORE this
script was run):
  |rho| > 0.85 -> STOP, record as a distance proxy, the idea dies here.
  |rho| < 0.6  -> proceed to full scoring.
  (0.6, 0.85]  -> ambiguous, judgment call, state reasoning explicitly.
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
from scipy.stats import spearmanr

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from allostery.baselines import euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.control_effort import control_effort_score, scan_control_effort  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.labels import build_labels  # noqa: E402

from hop_distance_generalization_audit import _load_apo_holo, DEFAULT_POCKET_CUTOFF  # noqa: E402

HOP_CUTOFF = 8.0

# Fixed, stated hyperparameters (Implementer's call, T finite -- see
# control_effort.py's module docstring for why the converged limit is not
# used here) -- same values used for the kill-switch and the primary
# scoring run below, unless the T/F sensitivity check (a separate,
# explicitly-labeled run) varies them on purpose.
T = 15.0
N_SLICES = 20
FIDELITY_TARGET = 0.5
PENALTY_WEIGHT = 5000.0
N_ITERS = 500
LR = 0.05


def main() -> int:
    t0 = time.monotonic()
    name = "KRAS_G12C"
    target_config = load_target_config(name)
    apo, holo = _load_apo_holo(name, target_config)
    cutoff = float(target_config.get("enm_cutoff", 10.0))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)

    source = np.where(labels_obj.active_site)[0]
    print(f"{name}: N={len(apo.resnums)} active_site n={len(source)}", file=sys.stderr)

    H0 = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)

    print(f"{name}: running scan_control_effort on all {len(apo.resnums)} residues...", file=sys.stderr)
    t_scan = time.monotonic()
    result = scan_control_effort(
        H0, source, T=T, n_slices=N_SLICES, fidelity_target=FIDELITY_TARGET,
        penalty_weight=PENALTY_WEIGHT, n_iters=N_ITERS, lr=LR, chunk_size=200,
    )
    scan_elapsed = time.monotonic() - t_scan
    print(f"{name}: scan done in {scan_elapsed:.1f}s, n_feasible={result.feasible.sum()}/{len(result.feasible)}", file=sys.stderr)

    score = control_effort_score(result)
    hop = -hop_from_seed(apo.coords, source, cutoff=HOP_CUTOFF)
    euclid = -euclid_from_seed_centroid(apo.coords, source)

    rho_hop, p_hop = spearmanr(score, hop)
    rho_euclid, p_euclid = spearmanr(score, euclid)

    max_abs_rho = max(abs(rho_hop), abs(rho_euclid))
    if max_abs_rho > 0.85:
        verdict = "STOP -- distance proxy"
    elif max_abs_rho < 0.6:
        verdict = "PROCEED -- not a simple distance proxy"
    else:
        verdict = "AMBIGUOUS -- judgment call needed"

    out = {
        "target": name,
        "n_residues": int(len(apo.resnums)),
        "n_active_site": int(len(source)),
        "n_feasible": int(result.feasible.sum()),
        "hyperparameters": {
            "T": T, "n_slices": N_SLICES, "fidelity_target": FIDELITY_TARGET,
            "penalty_weight": PENALTY_WEIGHT, "n_iters": N_ITERS, "lr": LR,
        },
        "rho_score_vs_neg_hop": float(rho_hop),
        "p_score_vs_neg_hop": float(p_hop),
        "rho_score_vs_neg_euclid": float(rho_euclid),
        "p_score_vs_neg_euclid": float(p_euclid),
        "max_abs_rho": float(max_abs_rho),
        "verdict": verdict,
        "scan_elapsed_s": round(scan_elapsed, 1),
        "total_elapsed_s": round(time.monotonic() - t0, 1),
    }

    out_dir = Path(__file__).resolve().parent.parent / "results_task0156_control_effort"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "kill_switch.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nWrote {out_path}")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
