#!/usr/bin/env python3
"""TASK-0166 -- real-target scoring for per-residue GNM low-mode
conformational entropy (`allostery.conformational_entropy.
residue_conformational_entropy`), testing the challenge's own reference [4]
(Motlagh & Hilser 2014) ensemble-redistribution mechanism -- no active-site
seed, no propagation step, distinct from every directed-channel observable
in this project's register.

Targets: the 3 mandatory + 4 of the other `status: verified` real targets
in `targets.yaml` (PTP1B, GLUCOKINASE, CASPASE1, CASPASE7) -- the full
pocket-scoreable generalization set actually available (TASK-0164 found
the separate `status: draft` ASD candidate pool exhausted, 0/6 usable; not
touched here). MYC_MAX (also `status: verified`) is deliberately excluded,
not merely skipped on error: its own config states `allosteric_pocket_
exists: false`/`holo_pdb: null` explicitly -- Myc/Max is an IDP heterodimer
with no surface pocket in the folded dimer at all, "score by consensus/
docking viability only, never by predicted-pocket derivation" per its own
`objective` field. There is no pocket label to score AUC against; including
it would not be a 6th data point, it would be a config error caught at
runtime (confirmed directly -- first draft of this script did include it
and it failed exactly this way, `ValueError("... no 'holo_pdb' defined")`,
not a silent bad result).

Methodology, matching the register's current (post-TASK-0158) discipline:
- Whole-graph AUC (context only) + TASK-0123 distance-stratified AUC
  (shells = -hop_from_seed) with a well-powered-shell-max summary -- the
  register's real bar, since whole-graph AUC is mechanically dominated by
  the proximity confound for any smooth score field.
- Permutation null via `nulls.compact_patch` (TASK-0158's corrected,
  spatially compact null) directly -- this task postdates TASK-0158, so
  there is no reason to use the superseded scattered draw even once.
- `diagnostics.classify_failure` against the standard 3-floor pack
  (degree/euclid/hop) for a same-discipline pass/fail read.
- Spearman rho(entropy, -hop_from_seed) and rho(entropy, -euclid_from_seed_
  centroid) -- this task's own Intent Contract requires reporting whether
  the observable is orthogonal to (a genuinely different mechanism) or
  reproduces (the confound that has dominated every other observable) the
  proximity floor.

**Noted explicitly, not hidden**: entropy is `0.5*ln(2*pi*e*sigma^2)`, a
strictly increasing function of the underlying low-mode variance --
`test_conformational_entropy.py::test_strictly_monotonic_in_variance_so_
auc_ranking_is_identical` confirms AUC/rank-based results here are
therefore IDENTICAL to scoring raw `gnm_lowmode_variance` directly; the
entropy transform changes absolute units, not the ranking any AUC/
stratified-AUC/permutation-null number here depends on.
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
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.conformational_entropy import residue_conformational_entropy  # noqa: E402
from allostery.diagnostics import classify_failure  # noqa: E402
from allostery.hamiltonians import contact_matrix, laplacian  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as auc_fn, stratified_auc  # noqa: E402
from allostery.nulls import compact_patch  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo, not re-derived

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "RESULTS" / "results/tasks/0166_ensemble_entropy"

MANDATORY_TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
GENERALIZATION_TARGETS = ["PTP1B", "GLUCOKINASE", "CASPASE1", "CASPASE7"]  # MYC_MAX excluded, see module docstring
TARGETS = MANDATORY_TARGETS + GENERALIZATION_TARGETS

N_MODES = 20  # matches superpose.anm_modes / compute_learnability's own default
N_PERM = 1000
PERM_SEED = 137
ALPHA = 0.05
MIN_POS_WELL_POWERED = 3
BONFERRONI_ALPHA = ALPHA / len(TARGETS)


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _well_powered_max(strat: dict, min_pos: int = MIN_POS_WELL_POWERED):
    cand = {s: v for s, v in strat.items() if v["n_pos"] >= min_pos and np.isfinite(v["auc"])}
    if not cand:
        return None, float("nan")
    best_shell = max(cand, key=lambda s: cand[s]["auc"])
    return best_shell, cand[best_shell]["auc"]


def _permutation_null(score: np.ndarray, coords: np.ndarray, shells: np.ndarray, pocket: np.ndarray,
                       n_reps: int = N_PERM, seed: int = PERM_SEED) -> dict:
    n_residues = len(pocket)
    pocket_size = int(pocket.sum())
    real_shell, real_auc = _well_powered_max(stratified_auc(score, pocket, shells))

    rng = np.random.default_rng(seed)
    null_maxes = []
    for _ in range(n_reps):
        idx = compact_patch(coords, pocket_size, rng)
        lab = np.zeros(n_residues, dtype=int)
        lab[idx] = 1
        _, null_max = _well_powered_max(stratified_auc(score, lab, shells))
        if np.isfinite(null_max):
            null_maxes.append(null_max)
    null_maxes = np.array(null_maxes) if null_maxes else np.array([np.nan])
    p_value = float((null_maxes >= real_auc).mean()) if np.isfinite(real_auc) else float("nan")
    return {
        "real_well_powered_max_auc": real_auc, "real_shell": real_shell,
        "null_median": float(np.median(null_maxes)), "n_reps": len(null_maxes),
        "p_value": p_value, "bonferroni_alpha": BONFERRONI_ALPHA,
        "bonferroni_significant": bool(p_value < BONFERRONI_ALPHA) if np.isfinite(p_value) else False,
    }


def run_one(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))

    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")
    source = np.sort(np.where(labels_obj.active_site)[0])
    if len(source) == 0:
        raise RuntimeError(f"{target_name}: empty active-site seed")

    N = len(apo.resnums)
    pocket = labels_obj.pocket.astype(int)
    coords = apo.coords
    _log(f"{target_name}: N={N} pocket_size={int(pocket.sum())} cutoff={cutoff}")

    t0 = time.monotonic()
    entropy = residue_conformational_entropy(coords, cutoff=cutoff, n_modes=N_MODES)
    elapsed = time.monotonic() - t0

    whole_auc = float(auc_fn(entropy, pocket))
    hop = hop_from_seed(coords, source, cutoff=cutoff)
    euclid = euclid_from_seed_centroid(coords, source)
    shells = -hop
    strat = stratified_auc(entropy, pocket, shells)
    strat_summary_shell, strat_summary_auc = _well_powered_max(strat)

    floor_scores = [
        degree_centrality(coords, cutoff=cutoff),
        euclid,
        hop,
    ]
    A = contact_matrix(coords, cutoff=cutoff, weight="binary")
    H_for_diagnosis = laplacian(A, normalised=False)
    diag = classify_failure(
        entropy, pocket, H=H_for_diagnosis, bfactors=apo.bfactors,
        floor_scores=floor_scores, return_ci=True,
    )

    null = _permutation_null(entropy, coords, shells, pocket)

    rho_hop, p_hop = spearmanr(entropy, -hop)
    rho_euclid, p_euclid = spearmanr(entropy, -euclid)

    _log(
        f"{target_name}: whole_auc={whole_auc:.4f} strat_max={strat_summary_auc:.4f} "
        f"(shell {strat_summary_shell}) null_p={null['p_value']:.4f} "
        f"rho(entropy,-hop)={rho_hop:.3f} rho(entropy,-euclid)={rho_euclid:.3f} "
        f"cat={diag.category} ({elapsed:.2f}s)"
    )

    return {
        "target": target_name, "N": N, "pocket_size": int(pocket.sum()), "cutoff": cutoff,
        "n_modes": N_MODES, "elapsed_s": round(elapsed, 3),
        "whole_graph_auc": whole_auc,
        "stratified": {
            "well_powered_max_auc": strat_summary_auc, "well_powered_max_shell": strat_summary_shell,
            "n_scorable_shells": len(strat),
        },
        "diagnosis": {
            "category": diag.category, "score_ci": diag.score_ci,
            "floor_ci": diag.floor_ci, "ci_overlap": diag.ci_overlap,
        },
        "permutation_null": null,
        "floor_correlation": {
            "rho_entropy_vs_neg_hop": float(rho_hop), "p_entropy_vs_neg_hop": float(p_hop),
            "rho_entropy_vs_neg_euclid": float(rho_euclid), "p_entropy_vs_neg_euclid": float(p_euclid),
        },
    }


def main() -> int:
    results = {}
    for target_name in TARGETS:
        try:
            results[target_name] = run_one(target_name)
        except Exception as exc:
            _log(f"{target_name}: FAILED -- {exc!r}")
            results[target_name] = {"target": target_name, "error": str(exc)}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "ensemble_entropy_real_run.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    _log(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
