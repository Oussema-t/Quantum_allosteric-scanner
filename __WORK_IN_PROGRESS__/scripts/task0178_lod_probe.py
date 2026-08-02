#!/usr/bin/env python3
"""TASK-0178 -- lightweight limit-of-detection probe on real KRAS_G12C
topology, reusing [[TASK-0167.001]]'s `plant`/`select_distal_patch`
machinery, at the reference prototype's own strength grid.

**Explicitly scoped down from [[TASK-0167.002]]'s own full protocol**
(that task is still TODO and is the shared, general-purpose infra this
task's own Dependency section calls for -- not duplicated here): one
target (KRAS_G12C only), one observable (`coupling_specificity`), one null
implicit in the AUC-vs-planted-label score itself (no CI/permutation-null/
Bonferroni chain, no scattered-vs-compact-vs-matched null comparison, no
CTQW like-for-like re-run). This gives a real, honestly-scoped "is the
observable sensitive to a planted channel on real protein topology"
answer, not a certified LOD.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import numpy as np  # noqa: E402

from allostery.baselines import hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.consensus_labels import load_apo_holo_full  # noqa: E402
from allostery.hamiltonians import contact_matrix, laplacian  # noqa: E402
from allostery.labels import functional_indices  # noqa: E402
from allostery.metrics import auc  # noqa: E402
from allostery.plant import assert_confound_orthogonal, plant_channel, select_distal_patch  # noqa: E402
from allostery.response import coupling_profile, coupling_specificity  # noqa: E402

TARGET = "KRAS_G12C"
STRENGTHS = (0.0, 1.5, 4.0, 10.0, 30.0)
N_SEEDS = 5
CUTOFF = 8.0
PATCH_SIZE = 8
KAPPA = 1.0


def main() -> int:
    cfg = load_target_config(TARGET)
    apo, holo, apo_raw, holo_raw, apo_chains, holo_chains = load_apo_holo_full(TARGET, cfg)
    func_idx, _ = functional_indices(apo.coords, holo.ligand_groups, cfg, cutoff=4.5)
    active_idx = np.sort(func_idx)
    n = len(apo.resnums)
    W0 = contact_matrix(apo.coords, cutoff=CUTOFF, weight="binary")
    hop = -hop_from_seed(apo.coords, active_idx, cutoff=CUTOFF)
    eligible = np.ones(n, dtype=bool)
    eligible[active_idx] = False

    out = {}
    for strength in STRENGTHS:
        aucs = []
        for seed in range(N_SEEDS):
            rng = np.random.default_rng(seed)
            patch = select_distal_patch(apo.coords, W0, active_idx, size=PATCH_SIZE, rng=rng, cutoff=CUTOFF)
            label = np.zeros(n, dtype=bool)
            label[patch] = True
            W_planted, report = plant_channel(W0, active_idx, patch, strength, n_paths=10, rng=rng)
            assert_confound_orthogonal(W0, W_planted, apo.coords, active_idx, label.astype(int), cutoff=CUTOFF)
            K = laplacian(W_planted)
            profile = coupling_profile(K, active_idx, apo.coords, kappa=KAPPA, patch_size=6)
            score = coupling_specificity(profile, hop)
            aucs.append(float(auc(score[eligible], label[eligible].astype(int))))
        out[strength] = {"aucs": aucs, "mean_auc": float(np.mean(aucs))}
        print(f"strength={strength:6.1f}  mean_auc={out[strength]['mean_auc']:.3f}  aucs={[round(x, 3) for x in aucs]}")

    out_dir = Path(__file__).resolve().parent.parent / "results_task0178_response_coupling"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "lod_probe_kras_g12c.json").write_text(json.dumps(out, indent=2))
    print(f"\nWrote {out_dir / 'lod_probe_kras_g12c.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
