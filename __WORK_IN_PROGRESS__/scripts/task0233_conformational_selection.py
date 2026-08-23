#!/usr/bin/env python3
"""TASK-0233 -- conformational-selection (population-shift) reframing:
does the apo ensemble's own harmonic normal modes already put the real
apo->holo displacement within thermal reach, or does it cost so much
elastic energy that even a rare, sampled minor conformer is implausible?

Reuses `allostery.superpose.run_superpose` (TASK-0015's own already-
validated orchestrator) UNMODIFIED -- alignment, cumulative overlap
(Tama-Sanejouand CO(m)), B-factor-calibrated kappa, and per-mode elastic
energy (`mode_energetics`: E_k = 0.5*kappa*lambda_k*c_k^2) are all
already built. No new physics, no new energy function -- this script is
data plumbing (real apo/holo fetch, per-target config) plus a sum and an
honest read of an already-computed quantity.

Units, stated once, per this project's own established precedent
(`allostery/holo_direction.py`'s own PERTURBATION_PROTOCOL comment,
TASK-0015): `calibrate_kappa` matches the unit-kappa ANM MSF to each
target's real mean B-factor WITHOUT a Debye-Waller (8*pi^2/3) correction
or an explicit real-kelvin kT -- this project's own already-adopted
convention treats the resulting energy scale as "kT=1" directly, not as
an absolute physical free energy. E_k is therefore reported in these
project-relative "thermal units" (one unit ~ kT), not real kcal/mol --
consistent with every other energetics number this codebase has ever
reported (`mode_energetics`'s own docstring: relaxation time is "only
meaningful relative to other modes of the same target," same caveat
applies here to elastic energy). Absolute-unit calibration was
considered and deliberately not built for this task (see Done section).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
_SCRIPTS = Path(__file__).resolve().parent
for _p in (_SRC, _SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from allostery.clean import load_target_config  # noqa: E402
from allostery.superpose import run_superpose  # noqa: E402

from task0230_ceiling_and_brittleness import _load_apo_holo  # noqa: E402

TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
ANM_CUTOFF = 10.0   # allostery.superpose's own established default
N_MODES = 50        # matches TASK-0227/TASK-0230's own k for the same real targets

# Per holo_direction.py's own PERTURBATION_PROTOCOL: at this project's
# established "kT=1" scale, a single mode carries kT/2 = 0.5 (unitless) of
# elastic energy on average -- the natural per-mode thermal reference this
# task's own plausibility read is measured against, not an invented bar.
THERMAL_UNIT_PER_MODE = 0.5


def run_one(name: str) -> dict:
    target_config = load_target_config(name)
    apo, holo = _load_apo_holo(name, target_config)

    report = run_superpose(apo, holo, target_config, n_modes=N_MODES, cutoff=ANM_CUTOFF)

    energetics = report["mode_energetics"]
    elastic_energy = energetics["elastic_energy"]  # (N_MODES,)
    co = report["cumulative_overlap"]               # (N_MODES,) cumulative overlap CO(m)
    kappa = report["kappa"]

    total_dG = float(elastic_energy.sum())
    cum_dG = np.cumsum(elastic_energy)
    # smallest m achieving 90% of the total k=50 displacement's own overlap,
    # and its own cumulative elastic cost -- "how much does the *bulk* of
    # this displacement cost," not just the full 50-mode total.
    co_final = float(co[-1])
    idx_90pct_co = int(np.searchsorted(co, 0.9 * co_final)) if co_final > 0 else len(co) - 1
    idx_90pct_co = min(idx_90pct_co, len(cum_dG) - 1)

    result = {
        "target": name,
        "n_common_residues": int(len(report["alignment"].apo_idx)),
        "kappa": kappa,
        "co_at_k50": co_final,
        "elastic_energy_per_mode_first10": [round(float(e), 4) for e in elastic_energy[:10]],
        "total_dG_k50_thermal_units": round(total_dG, 3),
        "total_dG_k50_over_natural_scale": round(total_dG / (N_MODES * THERMAL_UNIT_PER_MODE), 3),
        "dG_at_90pct_of_co_thermal_units": round(float(cum_dG[idx_90pct_co]), 3),
        "n_modes_for_90pct_co": idx_90pct_co + 1,
        "boltzmann_factor_exp_minus_dG_k50": float(np.exp(-total_dG)) if total_dG < 700 else 0.0,
    }
    print(f"{name}: N_common={result['n_common_residues']} kappa={kappa:.5f} "
          f"CO(k=50)={co_final:.4f}")
    print(f"  total elastic energy (k=50, 'thermal units'): {total_dG:.2f} "
          f"({result['total_dG_k50_over_natural_scale']:.2f}x the {N_MODES}-mode "
          f"natural scale of {N_MODES * THERMAL_UNIT_PER_MODE:.1f})")
    print(f"  90% of CO(50) reached by {result['n_modes_for_90pct_co']} modes, "
          f"costing {result['dG_at_90pct_of_co_thermal_units']:.2f} thermal units")
    print(f"  exp(-dG) at k=50 (relative Boltzmann weight vs. apo minimum): "
          f"{result['boltzmann_factor_exp_minus_dG_k50']:.3e}")
    print()
    return result


def main() -> int:
    out = {}
    for name in TARGETS:
        try:
            out[name] = run_one(name)
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            out[name] = {"target": name, "error": f"{type(exc).__name__}: {exc}"}

    out_dir = Path(__file__).resolve().parent.parent / "results/tasks/0233_conformational_selection"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
