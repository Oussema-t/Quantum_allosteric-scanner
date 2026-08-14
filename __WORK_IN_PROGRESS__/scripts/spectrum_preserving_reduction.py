#!/usr/bin/env python3
"""TASK-0172 -- retention report: Krylov (`allostery.reduce.krylov_basis`)
and Schur-complement (`allostery.reduce.schur_complement`) reduction of
real `H_new`, versus the existing lossy Louvain baseline
(`allostery.coarse.coarse_grain`), at several compression ratios.

Three retention axes, all versus the full-system reference:
  (a) spectral   : Ritz-value error (Krylov/Schur) vs full H's own
                    spectrum -- max/mean over the reduced operator's own
                    eigenvalues, nearest-true-eigenvalue matching.
  (b) dynamical   : Bhattacharyya coefficient between the full-system
                    converged occupation (`time_averaged_ctqw_converged`)
                    and the reduced-then-lifted one -- a standard
                    fidelity-like measure for two probability
                    distributions (1.0 = identical, 0.0 = disjoint
                    support), used here rather than a coherent-state
                    overlap because this project's own shipped observable
                    is the decoherent/time-averaged occupation, not a
                    coherent snapshot (`coherent=False` throughout,
                    matching `positive_control_detection_curve.py`'s own
                    convention).
  (c) ranking     : Spearman rho (full vs reduced occupation, all
                    residues), and the AUC/P@5 delta against the real
                    pocket label, each computed independently on the full
                    and reduced occupation vectors.

Louvain's own occupation is scored by broadcasting each cluster's
computed occupation to every member residue -- the natural residue-level
readout for a method that only ever produces a cluster-level operator.

Real, load-bearing finding surfaced while building this (`tests/
test_reduce.py`'s own docstrings record the synthetic version): a
block-Krylov seed of `n_seed` residues consumes `n_seed` Ritz dimensions
per round-robin power step, and a Schur reduction that must retain the
seed's own dynamics (to seed the reduced system the same way the full
one is seeded) needs the seed in the retained set P -- so **both methods
have a compression floor at or above the active-site size itself** when
exact seed representation is required. This script sweeps compression
targets that explicitly bracket each target's own active-site size to
measure this directly, not just assert it.
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

from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.coarse import coarse_grain  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.labels import build_labels, ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.metrics import precision_at_k  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from allostery.reduce import (  # noqa: E402
    krylov_basis,
    lift_krylov_eigvecs,
    lift_schur_eigvecs,
    reduce_krylov,
    schur_complement,
)
from allostery.runlog import RunLogger  # noqa: E402

DEFAULT_CUTOFF = 10.0
DEFAULT_POCKET_CUTOFF = 4.5
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0172_spectrum_preserving_reduction"


def _load_apo_holo(target_name: str, target_config: dict):
    import prody

    apo = clean_from_config(target_name, role="apo")
    holo = clean_from_config(target_name, role="holo")

    prody.confProDy(verbosity="none")
    holo_id = target_config["holo_pdb"]
    chains = target_config.get("chains") or sorted(set(holo.chain_ids))
    chain_sel = " or ".join(f"chain {c}" for c in chains)
    holo_struct = prody.parsePDB(holo_id, compressed=False).select(chain_sel)
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)
    holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
        holo_struct, chains, holo.resnums
    )
    return apo, holo


def _bhattacharyya(p: np.ndarray, q: np.ndarray) -> float:
    return float(np.sum(np.sqrt(np.clip(p, 0, None) * np.clip(q, 0, None))))


def _spectral_error(w_true: np.ndarray, w_ritz: np.ndarray) -> dict:
    errs = [float(np.min(np.abs(w_true - wr))) for wr in w_ritz]
    return {"max": float(np.max(errs)), "mean": float(np.mean(errs))}


def _rank_metrics(occ_full: np.ndarray, occ_reduced: np.ndarray, pocket: np.ndarray, mask: np.ndarray) -> dict:
    rho = float(spearmanr(occ_full[mask], occ_reduced[mask]).statistic)
    auc_full = _auc(occ_full[mask], pocket[mask])
    auc_reduced = _auc(occ_reduced[mask], pocket[mask])
    p5_full = precision_at_k(occ_full[mask], pocket[mask], 5)
    p5_reduced = precision_at_k(occ_reduced[mask], pocket[mask], 5)
    return {
        "spearman_rho": rho,
        "auc_full": auc_full, "auc_reduced": auc_reduced, "auc_delta": auc_reduced - auc_full,
        "p5_full": p5_full, "p5_reduced": p5_reduced, "p5_delta": p5_reduced - p5_full,
    }


def _louvain_broadcast_occupation(H: np.ndarray, active_idx: np.ndarray, n_target: int) -> tuple:
    result = coarse_grain(H, method="louvain", n_target=n_target, seed=0)
    labels = result.labels
    cluster_active = sorted(set(labels[active_idx].tolist()))
    occ_coarse = time_averaged_ctqw_converged(result.H_coarse, source=cluster_active, coherent=False)
    # Broadcast each cluster's TOTAL probability mass evenly across its own
    # member residues (divide by cluster size), not copy the same value to
    # every member -- copying would inflate the "distribution"'s total sum
    # by each cluster's size, breaking the sum-to-1 property `_bhattacharyya`
    # assumes (caught directly: an early version of this function produced
    # Bhattacharyya coefficients > 1, which is impossible for two genuine
    # probability distributions -- Cauchy-Schwarz caps it at 1).
    cluster_sizes = np.bincount(labels, minlength=result.n_clusters)
    occ_full_space = occ_coarse[labels] / cluster_sizes[labels]
    return occ_full_space, result.n_clusters


def run_target(target_name: str, m_values: list, log: RunLogger) -> dict:
    t0 = time.monotonic()
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))
    apo, holo = _load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)

    if labels_obj.pocket is None or not labels_obj.pocket.any():
        return {"target": target_name, "ok": False, "reason": "no resolvable pocket label"}

    active_idx = np.sort(np.where(labels_obj.active_site)[0])
    pocket = labels_obj.pocket.astype(int)
    n = len(apo.resnums)
    mask = np.ones(n, dtype=bool)
    mask[active_idx] = False

    H = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
    w_true = np.linalg.eigvalsh(H)
    occ_full = time_averaged_ctqw_converged(H, source=active_idx, coherent=False)
    log.step(f"{target_name}:prepared", n=n, n_active=len(active_idx), n_pocket=int(pocket.sum()))

    cells = []
    for m in m_values:
        cell = {"m": m}

        # --- Krylov ---
        Q = krylov_basis(H, seed_idx=active_idx, m=m)
        t_start = time.monotonic()
        H_red = reduce_krylov(H, Q)
        w_local, v_local = np.linalg.eigh(H_red)
        w_full_k, v_full_k = lift_krylov_eigvecs(Q, w_local, v_local)
        occ_krylov = time_averaged_ctqw_converged(w=w_full_k, v=v_full_k, source=active_idx, coherent=False)
        cell["krylov"] = {
            "m_requested": m, "m_actual": int(Q.shape[1]),
            "seed_fraction_of_budget": float(len(active_idx) / Q.shape[1]) if Q.shape[1] else float("nan"),
            "spectral_error": _spectral_error(w_true, w_local),
            "bhattacharyya": _bhattacharyya(occ_full, occ_krylov),
            **_rank_metrics(occ_full, occ_krylov, pocket, mask),
            "elapsed_s": round(time.monotonic() - t_start, 2),
        }

        # --- Schur: retain active site + top-degree residues by |H| up to m total ---
        t_start = time.monotonic()
        degree = np.abs(H).sum(axis=1) - np.abs(np.diag(H))
        order = np.argsort(-degree)
        retain = list(active_idx)
        for idx in order:
            if len(retain) >= m:
                break
            if idx not in retain:
                retain.append(int(idx))
        retain_idx = np.sort(np.array(retain[:max(m, len(active_idx))]))
        H_eff, elim_idx = schur_complement(H, retain_idx, E=0.0)
        w_local_s, v_local_s = np.linalg.eigh(H_eff.real if np.iscomplexobj(H_eff) else H_eff)
        w_full_s, v_full_s = lift_schur_eigvecs(H, retain_idx, elim_idx, 0.0, w_local_s, v_local_s)
        active_local = np.searchsorted(retain_idx, active_idx)
        occ_schur = time_averaged_ctqw_converged(w=w_full_s, v=v_full_s, source=active_idx, coherent=False)
        cell["schur"] = {
            "m_requested": m, "n_retained": int(len(retain_idx)),
            "spectral_error": _spectral_error(w_true, w_local_s),
            "bhattacharyya": _bhattacharyya(occ_full, occ_schur),
            **_rank_metrics(occ_full, occ_schur, pocket, mask),
            "elapsed_s": round(time.monotonic() - t_start, 2),
        }

        # --- Louvain baseline ---
        t_start = time.monotonic()
        occ_louvain, n_clusters = _louvain_broadcast_occupation(H, active_idx, m)
        cell["louvain"] = {
            "n_target": m, "n_clusters_actual": n_clusters,
            "bhattacharyya": _bhattacharyya(occ_full, occ_louvain),
            **_rank_metrics(occ_full, occ_louvain, pocket, mask),
            "elapsed_s": round(time.monotonic() - t_start, 2),
        }

        log.step(
            f"{target_name}:m={m}",
            krylov_auc_delta=cell["krylov"]["auc_delta"], krylov_rho=cell["krylov"]["spearman_rho"],
            schur_auc_delta=cell["schur"]["auc_delta"], schur_rho=cell["schur"]["spearman_rho"],
            louvain_auc_delta=cell["louvain"]["auc_delta"], louvain_rho=cell["louvain"]["spearman_rho"],
        )
        cells.append(cell)

    return {
        "target": target_name, "ok": True, "n": n, "n_active": int(len(active_idx)),
        "auc_full": _auc(occ_full[mask], pocket[mask]),
        "p5_full": precision_at_k(occ_full[mask], pocket[mask], 5),
        "cells": cells,
        "elapsed_s": round(time.monotonic() - t0, 1),
    }


def main() -> int:
    OUTPUT_DIR.mkdir(exist_ok=True)
    log = RunLogger(OUTPUT_DIR / "run.jsonl", run_name="task0172_spectrum_preserving_reduction")

    targets = sys.argv[1:] or ["KRAS_G12C"]
    m_values = [10, 14, 18, 24, 32, 50]
    out = []
    for name in targets:
        print(f"{name}: running...", file=sys.stderr)
        try:
            r = run_target(name, m_values, log)
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            r = {"target": name, "ok": False, "reason": f"{type(exc).__name__}: {exc}"}
        print(f"{name}: ok={r.get('ok')} reason={r.get('reason')}", file=sys.stderr)
        out.append(r)

    out_path = OUTPUT_DIR / "results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    log.finish()
    print(f"\nWrote {out_path}")

    for r in out:
        if not r.get("ok"):
            print(f"{r['target']:16s} FAILED: {r.get('reason')}")
            continue
        print(f"\n{r['target']} (N={r['n']}, n_active={r['n_active']}, full AUC={r['auc_full']:.3f}, full P@5={r['p5_full']:.2f})")
        for cell in r["cells"]:
            k, s, lo = cell["krylov"], cell["schur"], cell["louvain"]
            print(
                f"  m={cell['m']:3d}  "
                f"Krylov(m_actual={k['m_actual']:3d} seed_frac={k['seed_fraction_of_budget']:.2f} "
                f"rho={k['spearman_rho']:.2f} dAUC={k['auc_delta']:+.3f} BC={k['bhattacharyya']:.3f})  "
                f"Schur(n_ret={s['n_retained']:3d} rho={s['spearman_rho']:.2f} dAUC={s['auc_delta']:+.3f} BC={s['bhattacharyya']:.3f})  "
                f"Louvain(n_clu={lo['n_clusters_actual']:3d} rho={lo['spearman_rho']:.2f} dAUC={lo['auc_delta']:+.3f} BC={lo['bhattacharyya']:.3f})"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
