#!/usr/bin/env python3
"""TASK-0229.001 -- recompute the 3 mandatory targets' headline cells with
rank-of-known-site and enrichment-at-k alongside the existing AUC, per
ref [9] (Gunasekaran, Ma & Nussinov 2004, Proteins 57:433 -- verified
directly against the live article before this was written): if there is
no clean class of "non-allosteric" surface sites, ROC-AUC's negative-class
assumption is unsound, but rank-of-known-site/enrichment-at-k degrade more
gracefully (`metrics.rank_of_known_site`'s own module docstring has the
full argument).

Reuses `run_challenge.py`'s exact scoring path (`_load_apo_holo`,
`_make_candidates_builder`, `protocol.run_frozen_verdict`, the same
`time_averaged_ctqw_converged` winner-occupation computation) rather than
re-deriving it -- the AUC computed here is a wiring-check cross-check
against the already-published headline numbers, not a new measurement.
Does not write any of run_challenge.py's own output files; read-only
recompute against the live pipeline.
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
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from allostery.clean import load_target_config  # noqa: E402
from allostery.labels import build_labels, functional_indices  # noqa: E402
from allostery.metrics import auc, enrichment_at_k, rank_of_known_site  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from allostery.protocol import run_frozen_verdict  # noqa: E402

from hop_distance_generalization_audit import _load_apo_holo, DEFAULT_POCKET_CUTOFF  # noqa: E402
from run_challenge import (  # noqa: E402
    DEFAULT_CUTOFF,
    SELECTION_GSR_ABLATION_N_STEPS,
    SELECTION_GSR_ABLATION_T,
    _leak_check_n_perm_for,
    _make_candidates_builder,
)
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402

MANDATORY_TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
K_FOR_ENRICHMENT = 5  # matches this project's own standing top-5 hit-list convention


def _score_one(name: str) -> dict:
    t0 = time.monotonic()
    target_config = load_target_config(name)
    apo, holo = _load_apo_holo(name, target_config)
    cutoff = float(target_config.get("enm_cutoff", DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)

    if labels_obj.pocket is None or not labels_obj.pocket.any():
        return {"target": name, "ok": False, "reason": "no resolvable pocket label"}

    source = np.where(labels_obj.active_site)[0]
    pocket = labels_obj.pocket.astype(int)
    n = len(apo.resnums)

    floor_scores = [
        degree_centrality(apo.coords, cutoff=cutoff),
        euclid_from_seed_centroid(apo.coords, source),
        hop_from_seed(apo.coords, source, cutoff=cutoff),
    ]
    candidates_builder = _make_candidates_builder(apo, source, cutoff)
    leak_n_perm = _leak_check_n_perm_for(n)

    result = run_frozen_verdict(
        name, candidates_builder,
        apo.coords, apo.bfactors, source, labels_obj.pocket,
        cutoff=cutoff, t_max=SELECTION_GSR_ABLATION_T, n_steps=SELECTION_GSR_ABLATION_N_STEPS,
        floor_scores=floor_scores, coherent=False,
        learnability=None, use_converged_limit=True,
        leak_check_n_perm=leak_n_perm,
    )

    winner_name = candidates_builder()[result["_winner_index"]]["name"]
    winner_H = candidates_builder()[result["_winner_index"]]["H"]
    w_winner, v_winner = np.linalg.eigh(winner_H)
    winner_occ = time_averaged_ctqw_converged(source=source, coherent=False, w=w_winner, v=v_winner)

    auc_point = auc(winner_occ, pocket)
    rank_stats = rank_of_known_site(winner_occ, pocket)
    enrich_k = enrichment_at_k(winner_occ, pocket, K_FOR_ENRICHMENT)

    return {
        "target": name,
        "ok": True,
        "n_residues": int(n),
        "n_active_site": int(len(source)),
        "n_pocket": int(pocket.sum()),
        "winner": winner_name,
        "auc": auc_point,
        "auc_ci": [result.get("_diagnosis_score_ci")],
        "diagnosis": result.get("_diagnosis"),
        "rank_of_known_site": rank_stats,
        "enrichment_at_k": {"k": K_FOR_ENRICHMENT, "value": enrich_k},
        "elapsed_s": round(time.monotonic() - t0, 1),
    }


def main() -> int:
    out = []
    for name in MANDATORY_TARGETS:
        print(f"{name}: running...", file=sys.stderr)
        try:
            r = _score_one(name)
        except Exception as exc:  # noqa: BLE001 -- diagnostic script, report and continue
            r = {"target": name, "ok": False, "reason": f"{type(exc).__name__}: {exc}"}
        print(f"{name}: {r}", file=sys.stderr)
        out.append(r)

    out_dir = Path(__file__).resolve().parent.parent / "results/tasks/0229_001_headline_metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nWrote {out_path}")

    print("\n=== summary ===")
    for r in out:
        if not r.get("ok"):
            print(f"{r['target']:16s} FAILED: {r.get('reason')}")
            continue
        rk = r["rank_of_known_site"]
        print(
            f"{r['target']:16s} winner={r['winner']:24s} AUC={r['auc']:.4f}  "
            f"rank_min={rk['min']:.1f} rank_median={rk['median']:.1f} (n_pos={rk['n_positive']}/{rk['n_total']})  "
            f"enrich@{K_FOR_ENRICHMENT}={r['enrichment_at_k']['value']:.2f}  diagnosis={r['diagnosis']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
