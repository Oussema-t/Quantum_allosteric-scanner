#!/usr/bin/env python3
"""TASK-0122 -- real-target validation of `analysis.mode_coparticipation`
(mode co-participation, REVIEW-2026-07-13b Sec.6 / REVIEW-panel-2026-07-
17.md P1-5's sharpened `CP_low` form).

Three real-data checks, all required before this observable is trusted
beyond the dumbbell gate (test_dumbbell_negative_control.py's own
TestModeCoparticipationDumbbellGate, which it already passed):

1. **The panel's own validation gate**: `|rho(CP, -dist)|` on (a) a clean
   normalised Laplacian (no disorder, no potential), (b) `H_new` at its
   pre-TASK-0121 lambdas (the "current, un-renormalized" operator the
   panel actually measured, reconstructed explicitly since TASK-0121
   already changed `build_H_new`'s own shipped defaults), (c) `H_new` at
   its current (post-TASK-0121, renormalized) defaults. The panel's own
   reconstruction (3MHT, unverified against this repo's real code)
   measured 0.18 / 0.50 for (a)/(b) -- this script reproduces or refutes
   that pattern on this project's own real targets and real code, not a
   surrogate.
2. **k-sweep**: `rho(CP_low, -dist)` for `n_low` in {3, 5, 10, 20, all}
   on the renormalized `H_new`, against a real, directly-measured noise
   floor (`|rho(random scores, -dist)|`, 200 random draws per target --
   not copied from the panel's own 3MHT estimate).
3. **Real-label scoring**: AUC(CP_low, real pocket label) on all 3
   mandatory targets, checked against TASK-0094's proximity floor -- does
   CP_low actually enrich for the true pocket, not just decorrelate from
   distance (the task's own "necessary but not sufficient" caveat).

`-dist` is Euclidean distance from the seed centroid
(`baselines.euclid_from_seed_centroid`, this project's own existing
proximity-confound reference); `rho` is Spearman (this project's
existing convention for this class of correlation, e.g.
`ceiling.consistency_score`'s own `rho`).
"""
from __future__ import annotations

import argparse
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

from allostery.analysis import mode_coparticipation  # noqa: E402
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.hamiltonians import H2_combinatorial_laplacian, build_H_new  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo/DEFAULT_CUTOFF

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0122_mode_coparticipation"
TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]

# TASK-0106/TASK-0130's own record of build_H_new's pre-TASK-0121 defaults
# (ctqw_trapping_reproduction.py's _H_NEW_DEFAULT_LAMBDAS, before that
# task's z-scoring rescale) -- kept here explicitly so "current, un-
# renormalized H_new" can be reconstructed even though TASK-0121 already
# overwrote the shipped defaults in place.
_H_NEW_PRE_TASK0121_LAMBDAS = dict(lam_B=1.0, lam_T=2.0, lam_R=1.0, lam_C=0.5, lam_M=0.5)


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _prepare_target(target_name: str):
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

    return {
        "coords": apo.coords, "bfactors": apo.bfactors, "source": source,
        "pocket": labels_obj.pocket, "cutoff": cutoff,
        "n_residues": len(apo.resnums),
    }


def _rho_cp_dist(cp: np.ndarray, dist: np.ndarray) -> float:
    rho, _ = spearmanr(cp, -dist)
    return float(rho)


def _noise_floor(dist: np.ndarray, n_residues: int, n_draws: int = 200, seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    rhos = [abs(_rho_cp_dist(rng.uniform(size=n_residues), dist)) for _ in range(n_draws)]
    return {"mean": float(np.mean(rhos)), "sd": float(np.std(rhos)), "n_draws": n_draws}


def run_validation_gate(target_name: str, prep: dict, n_low: int = 5) -> dict:
    """Check 1: clean Laplacian vs. current (un-renormalized) H_new vs.
    renormalized H_new -- reproduces or refutes the panel's 0.18/0.50
    comparison points on this project's real code and real data."""
    coords, bfactors, source, cutoff = prep["coords"], prep["bfactors"], prep["source"], prep["cutoff"]
    dist = euclid_from_seed_centroid(coords, source)

    operators = {
        "clean_laplacian": H2_combinatorial_laplacian(coords, cutoff=cutoff),
        "H_new_pre_task0121": build_H_new(coords, bfactors, cutoff=cutoff, **_H_NEW_PRE_TASK0121_LAMBDAS),
        "H_new_renormalized_current": build_H_new(coords, bfactors, cutoff=cutoff),
    }

    result = {}
    for name, H in operators.items():
        cp = mode_coparticipation(H, source=source, n_low=n_low)
        rho = _rho_cp_dist(cp, dist)
        result[name] = {"rho_cp_dist": rho, "abs_rho": abs(rho)}
        _log(f"{target_name} [{name}]: rho(CP,-dist)={rho:.4f}")
    return result


def run_k_sweep(target_name: str, prep: dict, ks=(3, 5, 10, 20)) -> dict:
    """Check 2: does rho(CP_low, -dist) cross into the noise floor as
    n_low grows, and at what k, on this project's real 169-950-residue
    targets (not assumed to match the panel's own k=5/327-residue
    result)."""
    coords, bfactors, source, cutoff = prep["coords"], prep["bfactors"], prep["source"], prep["cutoff"]
    n_residues = prep["n_residues"]
    dist = euclid_from_seed_centroid(coords, source)
    H_new = build_H_new(coords, bfactors, cutoff=cutoff)  # current, renormalized

    noise = _noise_floor(dist, n_residues, seed=hash(target_name) & 0xFFFFFFFF)
    _log(f"{target_name}: noise floor |rho(random,-dist)| = {noise['mean']:.4f} +/- {noise['sd']:.4f} ({noise['n_draws']} draws)")

    sweep = {}
    all_k = list(ks) + [n_residues]
    for k in all_k:
        k_eff = min(k, n_residues)
        cp = mode_coparticipation(H_new, source=source, n_low=k_eff)
        rho = _rho_cp_dist(cp, dist)
        within_noise_floor = abs(rho) <= noise["mean"] + 2 * noise["sd"]
        sweep[str(k) if k != n_residues else "all"] = {
            "n_low_effective": k_eff, "rho_cp_dist": rho, "abs_rho": abs(rho),
            "within_noise_floor_2sd": bool(within_noise_floor),
        }
        _log(f"{target_name} k={k if k != n_residues else 'all'}: rho(CP,-dist)={rho:.4f} "
             f"within_noise_floor={within_noise_floor}")

    return {"noise_floor": noise, "sweep": sweep}


def run_real_label_scoring(target_name: str, prep: dict, n_low: int = 5) -> dict:
    """Check 3: does CP_low enrich for the *real* pocket label, checked
    against TASK-0094's proximity floor -- the "necessary but not
    sufficient" gate this task's own Intent Contract names."""
    coords, bfactors, source, cutoff = prep["coords"], prep["bfactors"], prep["source"], prep["cutoff"]
    pocket_int = prep["pocket"].astype(int)
    H_new = build_H_new(coords, bfactors, cutoff=cutoff)  # current, renormalized

    cp = mode_coparticipation(H_new, source=source, n_low=n_low)
    cp_auc = _auc(cp, pocket_int)

    floor_candidates = [
        degree_centrality(coords, cutoff=cutoff),
        euclid_from_seed_centroid(coords, source),
        hop_from_seed(coords, source, cutoff=cutoff),
    ]
    floor = float(max(_auc(f, pocket_int) for f in floor_candidates))

    result = {
        "cp_auc": float(cp_auc), "floor": floor,
        "clears_floor": bool(not np.isnan(cp_auc) and cp_auc > floor),
        "margin": float(cp_auc - floor) if not np.isnan(cp_auc) else None,
    }
    _log(f"{target_name}: CP AUC={cp_auc:.4f} floor={floor:.4f} clears_floor={result['clears_floor']}")
    return result


def run_target(target_name: str) -> dict:
    _log(f"{target_name}: preparing (fetch + clean + labels)...")
    prep = _prepare_target(target_name)
    _log(f"{target_name}: N={prep['n_residues']} n_seed={len(prep['source'])} pocket_size={int(prep['pocket'].sum())}")

    return {
        "target": target_name,
        "n_residues": prep["n_residues"],
        "validation_gate": run_validation_gate(target_name, prep),
        "k_sweep": run_k_sweep(target_name, prep),
        "real_label_scoring": run_real_label_scoring(target_name, prep),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=TARGETS)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "mode_coparticipation_validation.json")
    args = parser.parse_args(argv)

    all_results = {}
    for name in args.target:
        try:
            all_results[name] = run_target(name)
        except Exception as exc:
            all_results[name] = {"error": str(exc)}
            _log(f"{name}: FAILED -- {exc!r}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(all_results, f, indent=2)
    _log(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
