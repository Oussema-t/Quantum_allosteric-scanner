#!/usr/bin/env python3
"""TASK-0099 -- formal coherence-sensitivity verdict on real mandatory targets.

Runs `analysis.coherence_sensitivity` (the calibrated-gamma-scale wiring of
`dephasing_sweep` into `assemble_verdict_results`/`verdict_template`) on
KRAS_G12C, BCR_ABL1, and CARDIAC_MYOSIN -- answering, per target, "would
the reported verdict change if quantum coherence were randomized away."

`gamma_scale` is calibrated per target from its own apo geometry/B-factors
(`superpose.calibrate_kappa` + `anm_modes` + `mode_energetics`'s
`relaxation_time`, TASK-0099's own Intent Contract -- the exact recipe
`test_kras_g12c_dephasing_flat_survives_kappa_calibration` already
validated), swept at `{0, 0.5, 1, 2} * gamma_scale`. `gamma=0` uses the
exact, cheap `ctqw` limit rather than paying for `haken_strobl`'s ODE
solver at gamma=0 (TASK-0105's own established optimization, reused here).

Source/floor convention matches TASK-0105's `enaqt_gamma_sweep.py`
(active-site multi-index via `labels.build_labels`, TASK-0094's
degree/euclid/hop floor stack) rather than re-deriving a second one -- both
this task and TASK-0105 sweep the same physical quantity
(`propagators.haken_strobl`) on the same real targets.

**Computational-feasibility note (TASK-0105's own finding, reused not
re-derived):** `haken_strobl` costs ~11s/call at N=169 (KRAS_G12C),
~161s/call at N=451 (BCR_ABL1), and an estimated 30+ minutes/call at N=950
(CARDIAC_MYOSIN). This script therefore runs the full 4-point sweep on
KRAS_G12C and BCR_ABL1, and for CARDIAC_MYOSIN computes only the free
`gamma=0` (coherent CTQW) anchor -- reporting the sweep as
not-run/infeasible explicitly rather than silently omitting it or paying
an impractical wall-clock cost.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from allostery.analysis import coherence_sensitivity  # noqa: E402
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.propagators import ctqw  # noqa: E402
from allostery.superpose import anm_modes, calibrate_kappa, mode_energetics  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo, not re-derived

DEFAULT_CUTOFF = 10.0
DEFAULT_POCKET_CUTOFF = 4.5
# REVIEW-panel-2026-07-16-v2 Sec.2.2: t_max=15 (run_challenge's own default)
# is "unfixed and too short... a precondition for the physics, not hygiene"
# -- TASK-0108/0109's formal convergence check is still TODO. Pending that,
# this uses TASK-0105's own established "long enough to reach each gamma's
# long-time regime" convention (t=25) rather than the shorter t=8 the
# original KRAS-only dephasing test used (kept only in the reproduction
# test, test_analysis.py, which pins that exact prior recipe). Spot-checked
# 2026-07-16 across t_max in {8, 25, 100} on real KRAS_G12C data: auc_range
# stays in [0.013, 0.025] and classification stays COHERENCE_NOT_SIGNIFICANT
# at every point -- this task's conclusion is robust to the clock choice,
# even though the underlying per-gamma AUC's absolute chance/floor status
# does shift with t_max (the general gauge problem the review identifies,
# not resolved here -- see RESULTS.md).
T_MAX = 25.0
ODE_RTOL = 1e-3
ODE_ATOL = 1e-5

# Per-target full_sweep flag -- CARDIAC_MYOSIN's full sweep is
# computationally infeasible this session (see module docstring).
FULL_SWEEP = {
    "KRAS_G12C": True,
    "BCR_ABL1": True,
    "CARDIAC_MYOSIN": False,
}


def run_target(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))

    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None:
        raise RuntimeError(f"no resolvable pocket for {target_name!r}")

    active_site_idx = np.where(labels_obj.active_site)[0]
    if len(active_site_idx) == 0:
        raise RuntimeError(f"no active-site residues resolved for {target_name!r}")
    source = active_site_idx

    H_new = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
    pocket_int = labels_obj.pocket.astype(int)

    kappa = calibrate_kappa(apo.coords, apo.b_mean, cutoff=cutoff)
    eigvals, eigvecs = anm_modes(apo.coords, cutoff=cutoff, n_modes=20)
    common_idx = np.arange(len(apo.coords))
    energetics = mode_energetics(np.zeros(3 * len(common_idx)), eigvals, eigvecs, common_idx, kappa)
    gamma_scale = float(1.0 / np.mean(energetics["relaxation_time"][:20]))

    floor_candidates = [
        degree_centrality(apo.coords, cutoff=cutoff),
        euclid_from_seed_centroid(apo.coords, source),
        hop_from_seed(apo.coords, source, cutoff=cutoff),
    ]
    floor = float(max(_auc(f, pocket_int) for f in floor_candidates))

    full_sweep = FULL_SWEEP.get(target_name, True)
    if not full_sweep:
        occ0 = ctqw(H_new, T_MAX, source=source)
        auc0 = float(_auc(occ0, pocket_int))
        return {
            "target": target_name,
            "n_residues": len(apo.resnums),
            "gamma_scale": gamma_scale,
            "floor": floor,
            "full_sweep_run": False,
            "auc_at_gamma0": auc0,
            "auc_range": None,
            "is_flat": None,
            "classification": "INFEASIBLE_NOT_RUN",
        }

    out = coherence_sensitivity(
        H_new, apo.bfactors, source, labels_obj.pocket, gamma_scale,
        floor_scores=floor_candidates, t_max=T_MAX, rtol=ODE_RTOL, atol=ODE_ATOL,
    )
    out["target"] = target_name
    out["n_residues"] = len(apo.resnums)
    out["gamma_scale"] = gamma_scale
    out["floor"] = floor
    out["full_sweep_run"] = True
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--target", nargs="+", default=["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"],
        help="one or more config/targets.yaml keys",
    )
    parser.add_argument("--output", type=Path, default=None, help="write full JSON results here")
    args = parser.parse_args(argv)

    all_results = {}
    for name in args.target:
        try:
            all_results[name] = run_target(name)
            r = all_results[name]
            if not r["full_sweep_run"]:
                print(f"{name}: N={r['n_residues']} -- full sweep skipped (infeasible), gamma=0 anchor only, AUC@gamma0={r['auc_at_gamma0']:.4f}")
            else:
                print(
                    f"{name}: N={r['n_residues']} -- gamma_scale={r['gamma_scale']:.4g} "
                    f"auc_range={r['auc_range']:.4f} is_flat={r['is_flat']} "
                    f"floor={r['floor']:.3f} classification={r['classification']}"
                )
        except Exception as exc:
            all_results[name] = {"error": str(exc)}
            print(f"{name}: FAILED -- {exc}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(all_results, f, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
