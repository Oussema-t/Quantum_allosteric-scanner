#!/usr/bin/env python3
"""TASK-0156 -- T/F sensitivity check (task file's own Constraint:
"Report ranking sensitivity to T and F -- a ranking that flips with T is
not a measurement"). Run on KRAS_G12C only (cheapest target) -- the
primary scoring run already found chance-level, non-significant results
on all 3 mandatory targets, so this check's job is to confirm that null
result is not an artifact of one particular (T, F) choice, not to hunt
for a combination that "works" (that would be exactly the kind of
post-hoc knob search this project's own conventions prohibit).
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

from allostery.clean import load_target_config  # noqa: E402
from allostery.control_effort import control_effort_score, scan_control_effort  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import stratified_auc, stratified_auc_summary  # noqa: E402
from allostery.baselines import hop_from_seed  # noqa: E402

from hop_distance_generalization_audit import _load_apo_holo, DEFAULT_POCKET_CUTOFF  # noqa: E402

HOP_CUTOFF = 8.0
N_SLICES = 20
PENALTY_WEIGHT = 5000.0
N_ITERS = 500
LR = 0.05

# Primary run used (T=15.0, F=0.4). Two off-primary combinations,
# spanning both directions on each axis.
COMBOS = [
    ("primary", 15.0, 0.4),
    ("shorter_T_lower_F", 8.0, 0.3),
    ("longer_T_higher_F", 25.0, 0.5),
]


def main() -> int:
    name = "KRAS_G12C"
    target_config = load_target_config(name)
    apo, holo = _load_apo_holo(name, target_config)
    cutoff = float(target_config.get("enm_cutoff", 10.0))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    source = np.where(labels_obj.active_site)[0]
    pocket = labels_obj.pocket.astype(int)
    H0 = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
    shells = -hop_from_seed(apo.coords, source, cutoff=HOP_CUTOFF)

    scores = {}
    summary_rows = []
    for tag, T, F in COMBOS:
        t0 = time.monotonic()
        result = scan_control_effort(
            H0, source, T=T, n_slices=N_SLICES, fidelity_target=F,
            penalty_weight=PENALTY_WEIGHT, n_iters=N_ITERS, lr=LR, chunk_size=200,
        )
        score = control_effort_score(result)
        scores[tag] = score
        strat = stratified_auc(score, pocket, shells)
        strat_summary = stratified_auc_summary(strat)
        elapsed = time.monotonic() - t0
        print(f"{tag} (T={T}, F={F}): n_feasible={result.feasible.sum()}/{len(result.feasible)} "
              f"mean_auc={strat_summary['mean_auc']:.3f} elapsed={elapsed:.1f}s", file=sys.stderr)
        summary_rows.append({
            "tag": tag, "T": T, "fidelity_target": F,
            "n_feasible": int(result.feasible.sum()),
            "stratified_summary": strat_summary,
        })

    rank_corr = {}
    tags = [c[0] for c in COMBOS]
    for i in range(len(tags)):
        for j in range(i + 1, len(tags)):
            rho, p = spearmanr(scores[tags[i]], scores[tags[j]])
            rank_corr[f"{tags[i]}_vs_{tags[j]}"] = {"rho": float(rho), "p": float(p)}
            print(f"rank corr {tags[i]} vs {tags[j]}: rho={rho:.3f} p={p:.2e}", file=sys.stderr)

    out = {"target": name, "combos": summary_rows, "rank_correlations": rank_corr}
    out_dir = Path(__file__).resolve().parent.parent / "results_task0156_control_effort"
    out_path = out_dir / "tf_sensitivity.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
