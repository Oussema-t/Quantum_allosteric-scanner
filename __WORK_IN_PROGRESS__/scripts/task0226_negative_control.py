#!/usr/bin/env python3
"""TASK-0226 -- negative control for the two seed-blind observables that
survived the main confound retest (`dS_vib_global`, `slow1_minima`, see
`task0226_observable_family_confound_pdb_retest.py`).

Per the drop's own Section 5 requirement: "construct a case where the true
allosteric signal and the distance confound make different predictions,
and confirm that dS_vib_global and slow-mode minima track the former.
Without that control, their low rho shows only that they ignore the seed
-- which is trivially true by construction and is not evidence that they
carry allosteric signal."

Method: plant a real stiff channel (`plant.plant_channel`) from KRAS_G12C's
real active site (P-loop GDP contacts) to a genuinely distal, floor-blind
target patch (`plant.select_distal_patch` -- floor-blind AND far-hop by
construction, so a proximity detector would fail here by design; this is
the "different predictions" case the drop's instruction asks for). Recompute
`dS_vib_global`/`slow1_minima` on the planted graph, then test whether the
planted patch's mean score is enriched relative to a **compact-label
(radius-of-gyration-matched) permutation null** (`nulls.graph_walk_patch_
matched`) -- not the scattered/uniform-random null the drop's own Section 5
explicitly says is anti-conservative here.

Scope, stated up front: one target (KRAS_G12C, smallest/cheapest real
target with a resolvable real seed), one strength, one patch -- a
confirmatory check that the escape route is real, not a formal LOD sweep
(that already exists for other observable families,
`scripts/mechanism_discriminating_plant.py`, TASK-0168). If this fails to
detect the plant, that is reported as a real finding, not silently reworked
until it passes.
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
from scipy.linalg import eigh

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.consensus_labels import load_apo_holo_full  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.hamiltonians import contact_matrix, laplacian  # noqa: E402
from allostery.labels import functional_indices  # noqa: E402
from allostery.nulls import build_adjacency, graph_walk_patch_matched, radius_of_gyration  # noqa: E402
from allostery.plant import plant_channel, select_distal_patch  # noqa: E402

TARGET = "KRAS_G12C"
CUT = 8.5
STIFF = 3.0
STRENGTH = 5.0
N_PATHS = 10
PATCH_SIZE = 10
N_NULL = 500
SEED = 42


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def perturbation_sweep(A: np.ndarray) -> tuple:
    """dS_vib_global + the lowest non-trivial GNM mode (slow1), on
    whatever contact matrix `A` is passed -- identical math to the main
    retest script, factored out so it can be re-run on the planted graph
    without importing that script's heavier per-target pipeline."""
    N = A.shape[0]
    Lap = laplacian(A)
    w, V = eigh(Lap)
    nz = w > 1e-8
    base_ld = float(np.sum(np.log(w[nz])))
    dS = np.zeros(N)
    for j in range(N):
        sh = np.append(np.flatnonzero(A[j]), j)
        Ap = A.copy()
        ix = np.ix_(sh, sh)
        Ap[ix] = Ap[ix] * STIFF
        np.fill_diagonal(Ap, 0.0)
        L2 = laplacian(Ap)
        w2, _ = eigh(L2)
        n2 = w2 > 1e-8
        dS[j] = -0.5 * (float(np.sum(np.log(w2[n2]))) - base_ld)
    nz_idx = np.flatnonzero(nz)
    slow1 = -np.abs(V[:, nz_idx[0]])
    return dS, slow1


def main() -> int:
    target_config = load_target_config(TARGET)
    apo, holo, apo_raw, holo_raw, apo_chains, holo_chains = load_apo_holo_full(TARGET, target_config)
    co = apo.coords.astype(float)
    N = len(co)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", 4.5))
    seed_idx, provenance = functional_indices(
        apo.coords, holo.ligand_groups, target_config, cutoff=pocket_cutoff,
        heavy_atom_coords=getattr(holo, "heavy_atom_coords", None),
        heavy_atom_seq_index=getattr(holo, "heavy_atom_seq_index", None),
        heavy_atom_resnames=holo.resnames, coords_resnames=apo.resnames,
        coords_resnums=apo.resnums,
    )
    seed_idx = np.atleast_1d(np.asarray(seed_idx, dtype=int))
    _log(f"{TARGET}: N={N}, seed n={len(seed_idx)} (provenance={provenance!r})")

    A0 = contact_matrix(co, cutoff=CUT, weight="binary")
    for i in range(N - 1):
        A0[i, i + 1] = A0[i + 1, i] = 1.0

    rng = np.random.default_rng(SEED)
    target_patch = select_distal_patch(co, A0, seed_idx, PATCH_SIZE, rng, cutoff=CUT)
    target_rg = radius_of_gyration(co, target_patch)
    _log(f"target_patch (floor-blind, distal): {target_patch.tolist()}, Rg={target_rg:.2f}")

    W_planted, report = plant_channel(A0, seed_idx, target_patch, STRENGTH, N_PATHS, rng)
    _log(f"plant_channel: strength={STRENGTH}, n_paths_applied={report.n_paths_applied}, "
         f"n_paths_failed={report.n_paths_failed}, edges_modified={len(report.edges_modified)}")

    dS_planted, slow1_planted = perturbation_sweep(W_planted)
    dS_unplanted, slow1_unplanted = perturbation_sweep(A0)

    adjacency = build_adjacency(co, cutoff=CUT)
    excluded = set(seed_idx.tolist()) | set(target_patch.tolist())
    null_means = {"dS_vib_global": [], "slow1_minima": []}
    n_attempts_total = 0
    for i in range(N_NULL):
        while True:
            null_idx, n_att = graph_walk_patch_matched(
                co, adjacency, PATCH_SIZE, rng, target_rg=target_rg, tol=0.35, return_attempts=True
            )
            n_attempts_total += n_att
            if not (excluded & set(null_idx.tolist())):
                break
        null_means["dS_vib_global"].append(float(dS_planted[null_idx].mean()))
        null_means["slow1_minima"].append(float(slow1_planted[null_idx].mean()))

    result = {}
    for obs, planted_arr in (("dS_vib_global", dS_planted), ("slow1_minima", slow1_planted)):
        true_mean = float(planted_arr[target_patch].mean())
        null_arr = np.array(null_means[obs])
        p_value = float((np.sum(null_arr >= true_mean) + 1) / (len(null_arr) + 1))
        result[obs] = dict(
            true_mean=true_mean, null_mean=float(null_arr.mean()), null_std=float(null_arr.std()),
            p_value_one_sided=p_value, n_null=len(null_arr),
        )
        _log(f"{obs}: true_mean={true_mean:.4f}, null={null_arr.mean():.4f}+-{null_arr.std():.4f}, "
             f"p(one-sided, patch >= null)={p_value:.4f}")

    out = dict(
        target=TARGET, seed_idx=seed_idx.tolist(), target_patch=target_patch.tolist(),
        target_rg=target_rg, strength=STRENGTH, n_paths_applied=report.n_paths_applied,
        n_paths_failed=report.n_paths_failed, n_null=N_NULL,
        dS_vib_global_unplanted_mean_in_patch=float(dS_unplanted[target_patch].mean()),
        slow1_minima_unplanted_mean_in_patch=float(slow1_unplanted[target_patch].mean()),
        result=result,
    )
    out_dir = Path(__file__).resolve().parent.parent / "results" / "tasks" / "0226_observable_family_confound"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "negative_control.json"
    json.dump(out, open(out_path, "w"), indent=1)
    _log(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
