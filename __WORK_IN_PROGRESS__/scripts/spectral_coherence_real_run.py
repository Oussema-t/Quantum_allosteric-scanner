#!/usr/bin/env python3
"""TASK-0146 -- real-target scoring for the frequency-domain / spectral
coherence observable (`allostery.spectral_coherence.spectral_coherence_
score`): total AC (non-DC) spectral power of the un-averaged occupation
trajectory `p_j(t) = |<j|exp(-iHt)|source>|^2`.

Computed on `H_new` (this project's own submission operator, same as
every other headline number in `RESULTS.md`), source = full active-site
array ([[TASK-0118]]/`INV-0006`'s current GAUGE convention -- the
*coherent* superposition, matching `spectral_coherence`'s own amplitude
formula; no incoherent-mixture analogue exists for a genuinely
phase-preserving quantity, unlike `time_averaged_ctqw`'s `coherent=False`
knob).

Reuses, not re-derives: [[TASK-0112]]'s block-bootstrap CI (via
`diagnostics.classify_failure(..., return_ci=True)`, TASK-0145's own
established real-run pattern) for the primary whole-graph-AUC-vs-floor
reading, and [[TASK-0123]]'s stratified-AUC + well-powered-shell +
permutation-null machinery (TASK-0149's own established pattern) as the
secondary lens this project's other new-observable tasks have all needed
to separate real signal from the proximity confound. This task's own
score has no max-over-frequency-bins step (total power is a sum, not a
max -- see `spectral_coherence.py`'s own module docstring for why that
design was chosen), so the permutation null here is due-diligence
scrutiny on the standing statistic, not a multiple-comparisons correction
for an internal search.
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
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.diagnostics import classify_failure  # noqa: E402
from allostery.hamiltonians import build_H_new, contact_matrix, laplacian  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as auc_fn, stratified_auc  # noqa: E402
from allostery.spectral_coherence import DEFAULT_T_MAX, spectral_coherence_score  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo, not re-derived

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0146_spectral_coherence"
TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]

N_PERM = 1000
ALPHA = 0.05
N_TARGETS_FOR_BONFERRONI = len(TARGETS)
MIN_POS_WELL_POWERED = 3  # matches TASK-0123's own established convention


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _prepare_target(target_name: str) -> dict:
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

    H_new = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
    A = contact_matrix(apo.coords, cutoff=cutoff, weight="binary")
    H_for_diagnosis = laplacian(A, normalised=False)

    shells = -hop_from_seed(apo.coords, source, cutoff=cutoff)  # positive integer hop distance
    floor_scores = [
        degree_centrality(apo.coords, cutoff=cutoff),
        euclid_from_seed_centroid(apo.coords, source),
        hop_from_seed(apo.coords, source, cutoff=cutoff),
    ]
    floor = float(max(auc_fn(f, labels_obj.pocket.astype(int)) for f in floor_scores))

    return {
        "target": target_name, "H_new": H_new, "bfactors": apo.bfactors, "source": source,
        "pocket": labels_obj.pocket.astype(int), "n_residues": len(apo.resnums),
        "cutoff": cutoff, "floor_scores": floor_scores, "floor": floor,
        "H_for_diagnosis": H_for_diagnosis, "shells": shells,
    }


def _well_powered_max(strat: dict, min_pos: int = MIN_POS_WELL_POWERED):
    candidates = {s: v for s, v in strat.items() if v["n_pos"] >= min_pos and np.isfinite(v["auc"])}
    if not candidates:
        return None, float("nan")
    best_shell = max(candidates, key=lambda s: candidates[s]["auc"])
    return best_shell, candidates[best_shell]["auc"]


def _stratified_permutation_null(score: np.ndarray, prep: dict, n_reps: int = N_PERM, seed: int = 123) -> dict:
    """TASK-0123's own cheap permutation-null convention (score fixed,
    only pocket relabeling reshuffled -- reused directly, see TASK-0149's
    own `lowmode_predictor_real_run.py` for the identical pattern)."""
    pocket_size = int(prep["pocket"].sum())
    n_residues = prep["n_residues"]
    shells = prep["shells"]

    real_shell, real_auc = _well_powered_max(stratified_auc(score, prep["pocket"], shells))
    rng = np.random.default_rng(seed)
    null_maxes = []
    for _ in range(n_reps):
        perm_idx = rng.choice(n_residues, size=pocket_size, replace=False)
        perm_pocket = np.zeros(n_residues, dtype=int)
        perm_pocket[perm_idx] = 1
        _, null_max = _well_powered_max(stratified_auc(score, perm_pocket, shells))
        if np.isfinite(null_max):
            null_maxes.append(null_max)
    null_maxes = np.array(null_maxes) if null_maxes else np.array([np.nan])
    p_value = float((null_maxes >= real_auc).mean()) if np.isfinite(real_auc) else float("nan")
    return {
        "real_well_powered_max_auc": real_auc, "real_shell": real_shell,
        "null_median": float(np.median(null_maxes)), "n_reps": len(null_maxes),
        "p_value": p_value,
        "bonferroni_alpha": ALPHA / N_TARGETS_FOR_BONFERRONI,
        "bonferroni_significant": bool(p_value < ALPHA / N_TARGETS_FOR_BONFERRONI) if np.isfinite(p_value) else False,
    }


def run_one(target_name: str) -> dict:
    prep = _prepare_target(target_name)
    N = prep["n_residues"]
    _log(f"{target_name}: N={N} n_seed={len(prep['source'])} pocket_size={int(prep['pocket'].sum())} "
         f"cutoff={prep['cutoff']} floor={prep['floor']:.4f}")

    w = np.linalg.eigvalsh(prep["H_new"])
    gaps = np.diff(np.sort(w))
    gaps = gaps[gaps > 1e-12]
    delta_f = 2.0 * np.pi / DEFAULT_T_MAX
    frac_resolved = float((gaps >= delta_f).mean()) if len(gaps) else float("nan")

    t0 = time.monotonic()
    score = spectral_coherence_score(prep["H_new"], prep["source"], t_max=DEFAULT_T_MAX)
    elapsed = time.monotonic() - t0

    auc = float(auc_fn(score, prep["pocket"]))
    diag = classify_failure(
        score, prep["pocket"], H=prep["H_for_diagnosis"], bfactors=prep["bfactors"],
        floor_scores=prep["floor_scores"], return_ci=True,
    )
    strat = stratified_auc(score, prep["pocket"], prep["shells"])
    well_powered_shell, well_powered_auc = _well_powered_max(strat)
    strat_null = _stratified_permutation_null(score, prep)

    _log(
        f"{target_name}: whole_auc={auc:.4f} floor={prep['floor']:.4f} cat={diag.category} "
        f"ci_overlap={diag.ci_overlap} well_powered_max={well_powered_auc:.4f} "
        f"(shell {well_powered_shell}, p={strat_null['p_value']:.4f}) "
        f"gap_resolved_frac={frac_resolved:.3f} ({elapsed:.1f}s)"
    )

    return {
        "target": target_name, "N": N, "pocket_size": int(prep["pocket"].sum()),
        "cutoff": prep["cutoff"], "floor": prep["floor"], "elapsed_s": elapsed,
        "gap_delta_f_at_default_t_max": delta_f, "fraction_of_real_gaps_resolved": frac_resolved,
        "whole_graph_auc": auc, "category": diag.category,
        "score_ci": diag.score_ci, "floor_ci": diag.floor_ci, "ci_overlap": diag.ci_overlap,
        "n_scorable_shells": len(strat),
        "well_powered_shell": well_powered_shell, "well_powered_max_auc": well_powered_auc,
        "stratified_permutation_null": strat_null,
    }


def main() -> int:
    results = {}
    for target_name in TARGETS:
        try:
            results[target_name] = run_one(target_name)
        except Exception as exc:
            results[target_name] = {"target": target_name, "error": str(exc)}
            _log(f"{target_name}: FAILED -- {exc!r}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "spectral_coherence_real_run.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    _log(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
