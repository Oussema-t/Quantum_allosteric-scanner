#!/usr/bin/env python3
"""TASK-0145 -- real-target scoring for the two new transport observables:
classical effective resistance/conductance (`transport.
effective_resistance_from_source`) and Landauer-Buttiker quantum
transmission (`transport.transmission_from_source`).

Reframes the scoring question from "where does a seeded excitation
spread to over time" (every propagator-based observable already in this
project's register) to "what is the steady-state current/transmission
from the active site to each candidate residue" -- a non-equilibrium
steady-state (NESS) transport calculation.

Both quantities are computed on `hamiltonians.H2_combinatorial_laplacian`
(a genuine graph Laplacian, binary contact weighting) -- `R_eff` requires
this (no proper null space on `H_new`, confirmed while scoping this
task); `T(E)` is additionally run on `H_new` directly as a secondary
check (it has no null-space requirement), since that is this project's
actual submission operator. The primary classical-vs-quantum comparison
(this task's own Intent Contract point 3) uses the shared-Laplacian pair
-- an apples-to-apples "same graph, different formalism" comparison, not
confounded by also changing the operator.

`E=0` (DC/zero-bias limit) and `gamma_lead=0.1*bandwidth` are the
primary, pre-registered choices (blind to labels, stated in the module
docstring). A small E/gamma grid is characterized separately as a KNOB
(reported spread, not a best-of-K selection against labels) -- no
permutation null is needed for either primary score, since neither is
chosen by scanning a grid and keeping the best-scoring point against real
labels (this task's own research, `.ai/tasks/DONE/TASK-0145-...md`).
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
from allostery.diagnostics import classify_failure  # noqa: E402
from allostery.hamiltonians import H2_combinatorial_laplacian, build_H_new, contact_matrix, laplacian  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as auc_fn  # noqa: E402
from allostery.transport import effective_resistance_from_source, transmission_from_source  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo, not re-derived

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0145_transport"
TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]

E_GRID = np.array([0.0, 0.05, 0.1])       # KNOB characterization only, x H_new's bandwidth for the H_new run
GAMMA_MULTIPLIERS = np.array([0.05, 0.1, 0.2])  # KNOB characterization only

N_PERM = 1000
ALPHA = 0.05
N_TARGETS_FOR_BONFERRONI = len(TARGETS)


def _permutation_null(score: np.ndarray, pocket: np.ndarray, n_residues: int, pocket_size: int,
                       n_reps: int = N_PERM, seed: int = 123) -> dict:
    """Cheap re-labeling null (TASK-0131/TASK-0141 precedent) -- run on
    EVERY cell here (not only the ones that clear the floor), since none
    of this task's own scores are selected via a best-of-K sweep against
    labels (E/gamma are fixed a priori, see module docstring) -- this is
    due-diligence scrutiny on each cell's own standing number, not a
    max-of-something correction."""
    rng = np.random.default_rng(seed)
    real_auc = float(auc_fn(score, pocket))
    null_aucs = np.empty(n_reps)
    for i in range(n_reps):
        perm_idx = rng.choice(n_residues, size=pocket_size, replace=False)
        perm_pocket = np.zeros(n_residues, dtype=int)
        perm_pocket[perm_idx] = 1
        null_aucs[i] = auc_fn(score, perm_pocket)
    percentile = float((null_aucs <= real_auc).mean())
    p_value = float((null_aucs >= real_auc).mean())
    return {
        "real_auc": real_auc, "null_median": float(np.median(null_aucs)),
        "null_p95": float(np.percentile(null_aucs, 95)), "percentile": percentile,
        "p_value": p_value, "n_reps": n_reps,
        "bonferroni_alpha": ALPHA / N_TARGETS_FOR_BONFERRONI,
        "bonferroni_significant": bool(p_value < ALPHA / N_TARGETS_FOR_BONFERRONI),
    }


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

    L = H2_combinatorial_laplacian(apo.coords, cutoff=cutoff)
    H_new = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)

    floor_scores = [
        degree_centrality(apo.coords, cutoff=cutoff),
        euclid_from_seed_centroid(apo.coords, source),
        hop_from_seed(apo.coords, source, cutoff=cutoff),
    ]
    A = contact_matrix(apo.coords, cutoff=cutoff, weight="binary")
    H_for_diagnosis = laplacian(A, normalised=False)

    return {
        "target": target_name, "L": L, "H_new": H_new,
        "bfactors": apo.bfactors, "source": source,
        "pocket": labels_obj.pocket.astype(int), "n_residues": len(apo.resnums),
        "cutoff": cutoff, "floor_scores": floor_scores, "H_for_diagnosis": H_for_diagnosis,
    }


def _score(name: str, score: np.ndarray, prep: dict) -> dict:
    auc = float(auc_fn(score, prep["pocket"]))
    diag = classify_failure(
        score, prep["pocket"], H=prep["H_for_diagnosis"], bfactors=prep["bfactors"],
        floor_scores=prep["floor_scores"], return_ci=True,
    )
    null = _permutation_null(score, prep["pocket"], prep["n_residues"], int(prep["pocket"].sum()))
    return {
        "name": name, "auc": auc, "category": diag.category,
        "score_ci": diag.score_ci, "floor_ci": diag.floor_ci, "ci_overlap": diag.ci_overlap,
        "permutation_null": null,
    }


def run_one(target_name: str) -> dict:
    prep = _prepare_target(target_name)
    L, H_new, source = prep["L"], prep["H_new"], prep["source"]
    N = prep["n_residues"]
    _log(f"{target_name}: N={N} pocket_size={int(prep['pocket'].sum())} cutoff={prep['cutoff']}")

    t0 = time.monotonic()
    conductance = effective_resistance_from_source(L, source)
    t_reff = time.monotonic() - t0
    reff_result = _score("effective_resistance", conductance, prep)
    _log(f"{target_name}: R_eff AUC={reff_result['auc']:.4f} cat={reff_result['category']} "
         f"p={reff_result['permutation_null']['p_value']:.4f} ({t_reff:.1f}s)")

    t0 = time.monotonic()
    transmission_L_E0 = transmission_from_source(L, source, E=0.0)
    t_trans_L = time.monotonic() - t0
    trans_L_result = _score("transmission_on_L_E0", transmission_L_E0, prep)
    _log(f"{target_name}: T(E=0) on L AUC={trans_L_result['auc']:.4f} cat={trans_L_result['category']} "
         f"p={trans_L_result['permutation_null']['p_value']:.4f} ({t_trans_L:.1f}s)")

    t0 = time.monotonic()
    transmission_Hnew_E0 = transmission_from_source(H_new, source, E=0.0)
    t_trans_H = time.monotonic() - t0
    trans_Hnew_result = _score("transmission_on_H_new_E0", transmission_Hnew_E0, prep)
    _log(f"{target_name}: T(E=0) on H_new AUC={trans_Hnew_result['auc']:.4f} cat={trans_Hnew_result['category']} "
         f"p={trans_Hnew_result['permutation_null']['p_value']:.4f} ({t_trans_H:.1f}s)")

    # Point 3: classical-vs-quantum comparison, same graph (L), same E=0.
    spearman_rho, spearman_p = spearmanr(conductance, transmission_L_E0)

    # KNOB characterization only -- NOT a best-of-K selection against labels.
    w_L = np.linalg.eigvalsh(L)
    bandwidth_L = float(w_L[-1] - w_L[0])
    e_grid_aucs = []
    for e_mult in E_GRID:
        t_e = transmission_from_source(L, source, E=e_mult * bandwidth_L)
        e_grid_aucs.append({"e_multiplier": float(e_mult), "auc": float(auc_fn(t_e, prep["pocket"]))})
    gamma_grid_aucs = []
    for g_mult in GAMMA_MULTIPLIERS:
        t_g = transmission_from_source(L, source, E=0.0, gamma_lead=g_mult * bandwidth_L)
        gamma_grid_aucs.append({"gamma_multiplier": float(g_mult), "auc": float(auc_fn(t_g, prep["pocket"]))})

    return {
        "target": target_name, "N": N, "pocket_size": int(prep["pocket"].sum()),
        "cutoff": prep["cutoff"], "bandwidth_L": bandwidth_L,
        "effective_resistance": reff_result,
        "transmission_on_L_E0": trans_L_result,
        "transmission_on_H_new_E0": trans_Hnew_result,
        "classical_vs_quantum_spearman": {"rho": float(spearman_rho), "p": float(spearman_p)},
        "E_knob_grid": e_grid_aucs,
        "gamma_knob_grid": gamma_grid_aucs,
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
    with open(OUTPUT_DIR / "transport_observable_real_run.json", "w") as f:
        json.dump(results, f, indent=2)
    _log(f"wrote {OUTPUT_DIR / 'transport_observable_real_run.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
