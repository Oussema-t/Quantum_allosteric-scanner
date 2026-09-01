#!/usr/bin/env python3
"""TASK-0312 -- close H1/H2 on REAL target topologies, not just the
60-node synthetic control already run (see this task's own filing).

Builds the FULL pairwise transfer matrix `M_ij = Sum_B (P_B)_ij^2`
(`P_B = V_r @ V_r.T`, `V_r` = `H_new`'s eigenvectors in degenerate block
`B`, same `degenerate_tol=1e-6` default as
`allostery.propagators.time_averaged_ctqw_converged`) DIRECTLY from
`H_new`'s own spectral decomposition -- not by calling
`time_averaged_ctqw_converged` once per residue (equivalent, but O(N)
calls each doing its own block loop is wasted work when every block's
projector can be built once and reused for every row at once).

Two closed, independently-checkable questions on real topology:

H2 (implementation defect): is `M` symmetric to machine precision on a
real spectrum, which (unlike the synthetic control) has the near-
degenerate structure `degenerate_tol` grouping actually has to handle?

H1 (normalisation artifact): for the real holo-native active-site/pocket
label sets, is the forward/reverse SET-LEVEL SCALAR ratio exactly
`|pocket|/|active|`, as the symmetry of `M` requires algebraically?

Reuses [[TASK-0171]]'s own holo-native loading/labelling exactly
(`run_challenge._load_apo_holo`, `_holo_native_labels`) -- no new label
derivation, per this task's own Out of Scope.

Run: ../.venv/bin/python3 scripts/task0312_ctqw_seed_asymmetry.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
_TESTS = Path(__file__).resolve().parent.parent / "tests"
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from allostery.clean import load_target_config  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.propagators import _group_degenerate_eigenvalues  # noqa: E402

import run_challenge  # noqa: E402
from test_gnm_cutoff_weight_benchmark import _holo_native_labels  # noqa: E402

OUT = Path("results/tasks/0312_ctqw_seed_asymmetry")
TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
DEGENERATE_TOL = 1e-6  # matches time_averaged_ctqw_converged's own default


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def full_transfer_matrix(H: np.ndarray, tol: float = DEGENERATE_TOL) -> np.ndarray:
    """M_ij = Sum_B (P_B)_ij^2, built once from H's own eigendecomposition
    -- the full matrix underlying every single-source call to
    `time_averaged_ctqw_converged(H, source=i, coherent=False)`."""
    w, v = np.linalg.eigh(H)
    bandwidth = float(w[-1] - w[0]) if len(w) > 1 else 0.0
    t = tol * bandwidth if bandwidth > 0 else tol
    blocks = _group_degenerate_eigenvalues(w, t)
    n = v.shape[0]
    M = np.zeros((n, n))
    for block in blocks:
        V_r = v[:, block]
        P_r = V_r @ V_r.T
        M += P_r ** 2
    return M


def run_one(target_name: str) -> dict:
    cfg = load_target_config(target_name)
    cutoff = float(cfg.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    pocket_cutoff = float(cfg.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))

    _apo, holo = run_challenge._load_apo_holo(target_name, cfg)
    holo_pocket, holo_active, _ = _holo_native_labels(holo, cfg, pocket_cutoff)
    active_idx = np.sort(np.where(holo_active)[0])
    pocket_idx = np.sort(np.where(holo_pocket)[0])
    n = len(holo.resnums)
    _log(f"{target_name}: N={n} active_site={len(active_idx)} pocket={len(pocket_idx)} cutoff={cutoff}")

    H_new = build_H_new(holo.coords, holo.bfactors, cutoff=cutoff)
    M = full_transfer_matrix(H_new)

    max_asym = float(np.max(np.abs(M - M.T)))

    # H1: forward = sum_{i in active, j in pocket} M_ij / |active|
    #     reverse = sum_{i in pocket, j in active} M_ij / |pocket|
    sub = M[np.ix_(active_idx, pocket_idx)]  # M[active, pocket]
    fwd = float(sub.sum() / len(active_idx))
    rev = float(sub.T.sum() / len(pocket_idx))  # M[pocket, active] == M[active, pocket].T since M symmetric
    ratio_observed = fwd / rev
    ratio_predicted = len(pocket_idx) / len(active_idx)

    result = dict(
        target=target_name, N=n, n_active=len(active_idx), n_pocket=len(pocket_idx),
        max_abs_M_minus_MT=max_asym,
        set_level_forward=fwd, set_level_reverse=rev,
        ratio_observed=ratio_observed, ratio_predicted_T_over_S=ratio_predicted,
        ratio_matches=bool(np.isclose(ratio_observed, ratio_predicted, rtol=1e-9)),
    )
    _log(f"{target_name}: max|M-M.T|={max_asym:.3e}  "
         f"fwd/rev={ratio_observed:.6f} vs |pocket|/|active|={ratio_predicted:.6f} "
         f"(matches={result['ratio_matches']})")
    return result


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for t in TARGETS:
        try:
            results.append(run_one(t))
        except Exception as exc:
            _log(f"{t}: FAILED -- {exc!r}")
            results.append(dict(target=t, error=str(exc)))

    ok = [r for r in results if "error" not in r]
    _log("\n=== summary ===")
    _log(f"H2 (implementation defect): {'EXCLUDED' if all(r['max_abs_M_minus_MT'] < 1e-8 for r in ok) else 'NOT excluded -- see per-target values'} "
         f"on {len(ok)} real target(s) -- max|M-M.T| = "
         + ", ".join(f"{r['target']}={r['max_abs_M_minus_MT']:.3e}" for r in ok))
    _log(f"H1 (normalisation artifact, exact): "
         f"{'CONFIRMED' if all(r['ratio_matches'] for r in ok) else 'NOT confirmed -- see per-target values'} "
         + ", ".join(f"{r['target']}={r['ratio_matches']}" for r in ok))

    json.dump(dict(results=results), open(OUT / "ctqw_seed_asymmetry.json", "w"), indent=2)
    _log(f"written -> {OUT}/ctqw_seed_asymmetry.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
