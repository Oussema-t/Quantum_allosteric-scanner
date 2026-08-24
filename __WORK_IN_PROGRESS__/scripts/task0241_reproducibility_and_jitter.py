#!/usr/bin/env python3
"""TASK-0241 -- does [[TASK-0235]]'s "BCR_ABL1 4/4 decisive ceiling flip"
survive real replication, a properly quantified jitter floor, and the
register's own strict `_is_hit` (overlap AND druggability) criterion?

Two separable experiments, both reusing task0230/task0204/task0235's own
already-validated wiring (`_load_full_atom_apo`, `_apply_rigid_residue_
displacement`, `local_rigid_reconstruction`, `_run_evoef2`, `score_structure`)
-- nothing re-derived:

(A) PURE TOOL JITTER (this task's own Acceptance item 2): N=20 SideChainRepack
    trials on ONE byte-identical input (no structural perturbation at all),
    BCR_ABL1, both methods -- isolates EvoEF2/fpocket's own stochastic spread
    (real: `srand(time(NULL))`, forced distinct via `time.sleep(1.05)` between
    calls, confirmed in EvoEF2's own C source, `EnergyOptimization.cpp:754`)
    with the backbone held exactly fixed.

(B) REAL RE-RUN WITH STRUCTURAL PERTURBATION (Acceptance items 1+3): N=20
    trials per (target, method), but each trial's apo->holo displacement
    field gets independent small Gaussian noise (sigma=PERTURB_SIGMA,
    per-trial numpy RNG seeded by (target, method, trial_index) for exact
    reproducibility) added BEFORE either reconstruction method is applied --
    "perturb the input", the option this task's own Acceptance item 1 names
    explicitly, since no `--seed` CLI flag exists on the vendored EvoEF2
    binary (checked directly, `tools/evoef2/src/Main.cpp`'s own getopt_long
    table has no such option) and RandomRepack is a materially different,
    non-annealing algorithm this task did not ask to substitute.
    PERTURB_SIGMA=0.15 Angstrom -- an implementer's-call, order-of-magnitude
    match to typical crystallographic coordinate uncertainty, stated as a
    nuisance perturbation to break exact input degeneracy, NOT a physically
    calibrated conformational ensemble. Both methods see the SAME perturbed
    displacement field per trial (a fair, matched comparison), differing
    only in how each turns that field into a full-atom structure.
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
_SCRIPTS = Path(__file__).resolve().parent
for _p in (_SRC, _SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import tempfile  # noqa: E402

from allostery.clean import load_target_config  # noqa: E402
from allostery.labels import build_labels  # noqa: E402

from task0230_ceiling_and_brittleness import (  # noqa: E402
    POCKET_CUTOFF,
    WINDOW_MAX_SIZE,
    _apply_rigid_residue_displacement,
    _common_set_and_projection,
    _load_apo_holo,
    _load_full_atom_apo,
    _log,
    _run_evoef2,
    _select_window,
    _write_contiguous_window_chain,
    score_structure,
)
from task0235_local_rigid_backbone import (  # noqa: E402
    LOCAL_WINDOW,
    _target_ca_dicts,
    local_rigid_reconstruction,
)

TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
METHODS = ["old_rigid", "new_local_kabsch"]
N_TRIALS = 20  # this task's own Acceptance item 2's explicit floor
PERTURB_SIGMA = 0.15  # Angstrom, stated nuisance-perturbation magnitude, see module docstring
OUT_DIR = Path(__file__).resolve().parent.parent / "results/tasks/0241_reproducibility_and_jitter"


def _build_full_disp(name: str):
    target_config = load_target_config(name)
    apo, holo = _load_apo_holo(name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=POCKET_CUTOFF, target_name=name)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{name}: no resolvable pocket label")
    window = _select_window(apo, labels_obj.pocket, max_size=WINDOW_MAX_SIZE)
    apo_chains = target_config.get("apo_chains") or target_config.get("chains")
    alignment, full_disp, _proj_disp, _delta_r, _k_used = _common_set_and_projection(apo, holo, target_config)
    return target_config, apo, alignment, full_disp, window, apo_chains


def _perturb_disp(full_disp: dict, sigma: float, seed: int) -> dict:
    if sigma <= 0:
        return dict(full_disp)
    rng = np.random.default_rng(seed)
    out = {}
    for key, d in full_disp.items():
        out[key] = np.asarray(d) + rng.normal(0.0, sigma, size=3)
    return out


def _run_one_trial(method: str, target_config, apo, alignment, disp: dict, window, apo_chains, tmp: Path, trial_tag: str) -> dict:
    struct = _load_full_atom_apo(target_config, apo_chains)
    if method == "old_rigid":
        struct = _apply_rigid_residue_displacement(struct, disp)
    elif method == "new_local_kabsch":
        apo_ca, target_ca = _target_ca_dicts(apo, alignment, disp)
        struct = local_rigid_reconstruction(struct, apo_ca, target_ca, window=LOCAL_WINDOW)
    else:
        raise ValueError(method)
    pdb = tmp / f"{trial_tag}.pdb"
    design_chain = _write_contiguous_window_chain(struct, window, pdb)
    repacked = _run_evoef2("SideChainRepack", pdb, design_chain)
    if isinstance(repacked, dict):
        return {"error": repacked["error"]}
    target_set = {(design_chain, r) for (_c, r) in window}
    score = score_structure(repacked, target_set, tmp)
    return score


def experiment_a_pure_jitter() -> dict:
    """N=20 repeats on ONE byte-identical input, BCR_ABL1, both methods --
    no perturbation, isolates EvoEF2/fpocket's own stochastic spread alone."""
    name = "BCR_ABL1"
    target_config, apo, alignment, full_disp, window, apo_chains = _build_full_disp(name)
    out = {}
    for method in METHODS:
        trials = []
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            for i in range(N_TRIALS):
                time.sleep(1.05)
                r = _run_one_trial(method, target_config, apo, alignment, full_disp, window, apo_chains, tmp, f"jitterA_{method}_{i}")
                trials.append(r)
                _log(f"[expA] {name}/{method} trial {i}: {r}")
        out[method] = trials
    return {name: out}


def experiment_b_perturbed_rerun() -> dict:
    """N=20 trials per (target, method), independent small structural
    perturbation per trial -- the real re-run this task's own Acceptance
    item 3 asks for."""
    out = {}
    for name in TARGETS:
        target_config, apo, alignment, full_disp, window, apo_chains = _build_full_disp(name)
        out[name] = {}
        for method in METHODS:
            trials = []
            with tempfile.TemporaryDirectory() as tmp:
                tmp = Path(tmp)
                for i in range(N_TRIALS):
                    time.sleep(1.05)
                    seed = hash((name, method, i)) % (2**32)
                    disp = _perturb_disp(full_disp, PERTURB_SIGMA, seed)
                    r = _run_one_trial(method, target_config, apo, alignment, disp, window, apo_chains, tmp, f"expB_{method}_{i}")
                    trials.append(r)
                    _log(f"[expB] {name}/{method} trial {i}: {r}")
            out[name][method] = trials
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    _log("=== Experiment A: pure tool jitter (BCR_ABL1, byte-identical input) ===")
    results["experiment_a_pure_jitter"] = experiment_a_pure_jitter()
    (OUT_DIR / "results.json").write_text(json.dumps(results, indent=2, default=str))

    _log("=== Experiment B: perturbed re-run, all targets, both methods ===")
    results["experiment_b_perturbed_rerun"] = experiment_b_perturbed_rerun()
    (OUT_DIR / "results.json").write_text(json.dumps(results, indent=2, default=str))

    _log(f"done, wrote {OUT_DIR / 'results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
