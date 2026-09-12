#!/usr/bin/env python3
"""TASK-0378 child process -- one KRAS_G12C scoring run, in a fresh
interpreter, with whatever thread-count env vars the parent already set
in THIS process's environment before Python (and therefore numpy/BLAS)
was ever imported. Thread-count env vars only take effect at process
start, which is exactly why this has to be a subprocess sweep and not a
loop inside one long-lived interpreter -- the parent
(task0378_kras_determinism_probe.py) spawns one of these per run.

Reuses task0376_paired_bootstrap_no_signal.py's own `build_target_arrays`
reconstruction verbatim (import, not reimplementation) -- the identical
code path `run_challenge.py::run_target` uses for KRAS_G12C's real,
shipped number.

Prints one JSON object to stdout: score_auc, floor_auc, floor_name, the
full winner_occ vector, the top-5 residue indices by winner_occ, and the
winner Hamiltonian's own eigenvalue spectrum (so the parent can check the
degenerate-subspace hazard without re-running anything).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

import numpy as np  # noqa: E402

import run_challenge as rc  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.protocol import run_frozen_verdict  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402

TARGET = "KRAS_G12C"


def main() -> int:
    # Optional: --degenerate-tol <float> overrides time_averaged_ctqw_converged's
    # own default (1e-6), only used by the parent's item-4 follow-up ("if and
    # only if variation is found, re-run with degenerate_tol varied"). Absent
    # this flag, behavior is byte-identical to the pre-existing default path.
    degenerate_tol = 1e-6
    if "--degenerate-tol" in sys.argv:
        degenerate_tol = float(sys.argv[sys.argv.index("--degenerate-tol") + 1])
    target_config = load_target_config(TARGET)
    cutoff = float(target_config.get("enm_cutoff", rc.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", rc.DEFAULT_POCKET_CUTOFF))

    apo, holo = rc._load_apo_holo(TARGET, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None:
        raise RuntimeError(f"{TARGET}: build_labels returned pocket=None")

    active_site_idx = np.where(labels_obj.active_site)[0]
    source = np.sort(active_site_idx)

    floor_names = ["degree_centrality", "euclid_from_seed_centroid", "hop_from_seed"]
    floor_scores = [
        degree_centrality(apo.coords, cutoff=cutoff),
        euclid_from_seed_centroid(apo.coords, source),
        hop_from_seed(apo.coords, source, cutoff=cutoff),
    ]

    candidates_builder = rc._make_candidates_builder(apo, source, cutoff)
    leak_n_perm = rc._leak_check_n_perm_for(len(apo.resnums))
    result = run_frozen_verdict(
        TARGET, candidates_builder,
        apo.coords, apo.bfactors, source, labels_obj.pocket,
        cutoff=cutoff, t_max=rc.SELECTION_GSR_ABLATION_T, n_steps=rc.SELECTION_GSR_ABLATION_N_STEPS,
        floor_scores=floor_scores, coherent=False,
        learnability=None, use_converged_limit=True,
        leak_check_n_perm=leak_n_perm,
    )
    leak_check = result.get("_leak_check")
    if leak_check is not None and leak_check.get("leak_detected"):
        raise RuntimeError(f"{TARGET}: GATE-B4 leak check fired -- not trustworthy")

    winner_H = candidates_builder()[result["_winner_index"]]["H"]
    w_winner, v_winner = np.linalg.eigh(winner_H)
    winner_occ = time_averaged_ctqw_converged(source=source, coherent=False, w=w_winner, v=v_winner,
                                              degenerate_tol=degenerate_tol)

    labels_arr = np.asarray(labels_obj.pocket).astype(int)
    floor_aucs = [_auc(np.asarray(f), labels_arr) for f in floor_scores]
    win_i = int(np.nanargmax(floor_aucs))
    floor_auc = float(floor_aucs[win_i])
    floor_name = floor_names[win_i]

    score_auc = float(_auc(winner_occ, labels_arr))
    top5 = [int(i) for i in np.argsort(-winner_occ)[:5]]

    w_sorted = np.sort(w_winner)
    gaps = np.diff(w_sorted).tolist()
    bandwidth = float(w_sorted[-1] - w_sorted[0]) if len(w_sorted) > 1 else 0.0

    out = dict(
        target=TARGET,
        N=len(apo.resnums),
        score_auc=score_auc,
        floor_auc=floor_auc,
        floor_name=floor_name,
        winner_occ=winner_occ.tolist(),
        top5=top5,
        eigenvalues=w_sorted.tolist(),
        bandwidth=bandwidth,
        winner_index=int(result["_winner_index"]),
        degenerate_tol=degenerate_tol,
    )
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
