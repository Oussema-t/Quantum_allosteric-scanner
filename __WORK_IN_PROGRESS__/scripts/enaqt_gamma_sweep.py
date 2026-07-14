#!/usr/bin/env python3
"""TASK-0105 -- ENAQT gamma-sweep on real mandatory targets.

Measures transport efficiency from the active site to the labeled
allosteric pocket, across a Haken-Strobl dephasing-rate sweep
(`propagators.haken_strobl`), on real target topologies. Reports the
**interior-optimum shape and enhancement ratio over the coherent walk**
(REVIEW-2026-07-13b Sec.4/Sec.7 T-C) -- not AUC recovery of any prior
number. This replaces the old (killed) framing of TASK-0091's originally-
considered dephasing question.

Primary output is **transport magnitude** (total occupation probability
landing on the labeled pocket), not AUC -- the review is explicit the
falsifiable signature is the interior-optimum *shape*, not a ranking
metric. A secondary AUC-at-optimum number is also reported, checked
against TASK-0094's proximity floor, since "does transport increase" and
"does that increase actually help distinguish the true pocket from
everything else" are different questions.

Swept across three operators (`H_new` default, `H10_disorder_suppressed`,
`H2_combinatorial_laplacian`), per REVIEW-2026-07-13c's explicit caution:
`H_new`'s diagonal potentials cause Anderson-like transport localization
(the walk never leaves the seed's first contact shell) -- a flat/absent
interior optimum on `H_new` alone could be mistaken for "no ENAQT effect"
when it is actually "no transport to dephase in the first place."

**Computational-feasibility note (found while implementing this task, not
guessed in advance):** `haken_strobl` integrates an N^2-dimensional
Lindblad ODE (the full density matrix), with an O(N^3) matrix multiply
per right-hand-side evaluation. Measured wall-clock per single call
(t=25, one gamma value) on this repo's own real target topologies:
N=169 (KRAS_G12C) ~11s, N=451 (BCR_ABL1) ~161s. Extrapolating (N^3
scaling, consistent with the measured ratio) puts N=950 (CARDIAC_MYOSIN)
at ~30+ minutes *per gamma value*, making a real multi-point sweep on
that target computationally infeasible within a normal working session
with the current dense-matrix implementation. This script therefore runs
a full sweep on KRAS_G12C and a reduced-resolution sweep on BCR_ABL1, and
reports CARDIAC_MYOSIN's infeasibility explicitly (computing only the
free `gamma=0` coherent-CTQW anchor) rather than silently omitting it or
letting it run for an impractical amount of time. This is itself a
finding relevant to TASK-0068 (NISQ/coarse-graining): `coarse.py`'s
coarse-graining is exactly the tool that would make a real sweep on
CARDIAC_MYOSIN's scale tractable.
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

from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import load_target_config  # noqa: E402
from allostery.hamiltonians import H2_combinatorial_laplacian, build_H10, build_H_new  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.propagators import ctqw, haken_strobl  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _load_apo_holo, not re-derived

DEFAULT_CUTOFF = 10.0
DEFAULT_POCKET_CUTOFF = 4.5
T = 25.0  # propagation time; long enough to reach each gamma's long-time regime
DEFAULT_GAMMAS = np.logspace(-4, 2, 8)
ODE_RTOL = 1e-4
ODE_ATOL = 1e-6

# Per-target overrides: (gamma_grid, t, run_full_sweep). CARDIAC_MYOSIN's
# full sweep is computationally infeasible this session (see module
# docstring) -- reported explicitly, not silently skipped.
TARGET_SWEEP_CONFIG = {
    "KRAS_G12C": {"gammas": np.logspace(-4, 2, 8), "t": T, "full_sweep": True},
    "BCR_ABL1": {"gammas": np.logspace(-3, 1, 6), "t": T, "full_sweep": True},
    "CARDIAC_MYOSIN": {"gammas": np.array([]), "t": T, "full_sweep": False},
}

OPERATORS = ("H_new", "H10", "H2")


def transport_to_pocket(occ: np.ndarray, pocket_mask: np.ndarray) -> float:
    """Total occupation probability mass landing on the labeled pocket --
    the review's own 'transport' quantity (REVIEW-2026-07-13b Sec.4), not
    an AUC/ranking metric."""
    return float(np.asarray(occ)[pocket_mask].sum())


def sweep_gamma(H: np.ndarray, source, pocket_mask: np.ndarray, gammas: np.ndarray, t: float) -> dict:
    """Sweep `haken_strobl`'s dephasing rate `gamma`, reporting transport-
    to-pocket at each point plus the `gamma=0` (coherent CTQW) anchor
    (computed directly via `ctqw`, not the ODE solver at gamma=0, since
    that limit is exact and much cheaper).

    Returns a dict with the swept curve, the interior-optimum verdict, the
    enhancement ratio over the coherent limit, and the occupation vector
    at the optimal gamma (for the caller's own AUC-at-optimum check).
    """
    gamma0_occ = ctqw(H, t, source=source)
    gamma0_transport = transport_to_pocket(gamma0_occ, pocket_mask)

    if len(gammas) == 0:
        return {
            "gammas": [], "transport": [], "gamma0_transport": gamma0_transport,
            "gamma_inf_transport": None, "gamma_star": None, "transport_star": None,
            "interior_optimum": None, "enhancement_ratio": None,
            "occ_at_gamma_star": gamma0_occ, "occ_at_gamma0": gamma0_occ,
        }

    transports = []
    occs = []
    for g in gammas:
        occ = haken_strobl(H, t, float(g), source=source, rtol=ODE_RTOL, atol=ODE_ATOL)
        occs.append(occ)
        transports.append(transport_to_pocket(occ, pocket_mask))
    transports = np.asarray(transports)

    best_i = int(np.argmax(transports))
    gamma_star = float(gammas[best_i])
    transport_star = float(transports[best_i])
    occ_star = occs[best_i]

    interior_optimum = bool(
        transport_star > gamma0_transport
        and transport_star > transports[-1]
        and 0 < best_i < len(gammas) - 1
    )
    enhancement_ratio = float(transport_star / (gamma0_transport + 1e-12))

    return {
        "gammas": gammas.tolist(),
        "transport": transports.tolist(),
        "gamma0_transport": gamma0_transport,
        "gamma_inf_transport": float(transports[-1]),
        "gamma_star": gamma_star,
        "transport_star": transport_star,
        "interior_optimum": interior_optimum,
        "enhancement_ratio": enhancement_ratio,
        "occ_at_gamma_star": occ_star,
        "occ_at_gamma0": gamma0_occ,
    }


def _build_operator(name: str, apo, cutoff: float) -> np.ndarray:
    if name == "H_new":
        return build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
    if name == "H10":
        return build_H10(apo.coords, apo.bfactors, cutoff=cutoff)
    if name == "H2":
        return H2_combinatorial_laplacian(apo.coords, cutoff=cutoff)
    raise ValueError(f"unknown operator {name!r}")


def run_target_sweep(target_name: str, operators=OPERATORS) -> dict:
    """Run the full per-operator gamma sweep for one target, using this
    target's own `TARGET_SWEEP_CONFIG` entry (resolution/feasibility
    already decided per-target -- see module docstring)."""
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
    # haken_strobl/ctqw accept a multi-index source natively (unlike
    # select.py's ballistic_exponent, TASK-0090) -- use the full active
    # site, not a single representative index.
    source = active_site_idx

    floor_candidates = [
        degree_centrality(apo.coords, cutoff=cutoff),
        euclid_from_seed_centroid(apo.coords, source),
        hop_from_seed(apo.coords, source, cutoff=cutoff),
    ]
    pocket_int = labels_obj.pocket.astype(int)
    floor = max(_auc(f, pocket_int) for f in floor_candidates)

    cfg = TARGET_SWEEP_CONFIG.get(target_name, {"gammas": DEFAULT_GAMMAS, "t": T, "full_sweep": True})

    results = {}
    for op_name in operators:
        H = _build_operator(op_name, apo, cutoff)
        sweep = sweep_gamma(H, source, labels_obj.pocket, cfg["gammas"], cfg["t"])
        occ_star = sweep.pop("occ_at_gamma_star")
        occ0 = sweep.pop("occ_at_gamma0")
        auc_at_star = _auc(occ_star, pocket_int)
        auc_at_gamma0 = _auc(occ0, pocket_int)
        sweep["auc_at_gamma_star"] = auc_at_star
        sweep["auc_at_gamma0"] = auc_at_gamma0
        sweep["floor"] = floor
        sweep["floor_cleared_at_gamma_star"] = bool(not np.isnan(auc_at_star) and auc_at_star > floor)
        results[op_name] = sweep

    return {
        "target": target_name,
        "n_residues": len(apo.resnums),
        "cutoff": cutoff,
        "t": cfg["t"],
        "full_sweep_run": cfg["full_sweep"],
        "floor": floor,
        "bfactor_std": float(np.std(apo.bfactors)),
        "operators": results,
    }


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
            all_results[name] = run_target_sweep(name)
            r = all_results[name]
            if not r["full_sweep_run"]:
                print(f"{name}: N={r['n_residues']} -- full sweep skipped (infeasible), gamma=0 anchor only")
            else:
                print(f"{name}: N={r['n_residues']} -- OK")
                for op_name, sweep in r["operators"].items():
                    print(
                        f"  {op_name}: interior_optimum={sweep['interior_optimum']} "
                        f"gamma*={sweep['gamma_star']} enhancement={sweep['enhancement_ratio']:.3f} "
                        f"AUC@gamma*={sweep['auc_at_gamma_star']:.3f} floor={sweep['floor']:.3f} "
                        f"cleared={sweep['floor_cleared_at_gamma_star']}"
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
