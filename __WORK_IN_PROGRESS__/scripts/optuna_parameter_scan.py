#!/usr/bin/env python3
"""TASK-0110 -- Optuna apo-floor / holo-ceiling scan of CTQW's numerical
parameters (t_max, n_steps) on real mandatory targets.

Reuses `run_challenge.py`'s fetch/clean glue (`_load_apo_holo`) and
`labels.build_labels` -- does not re-derive fetch/label logic, per this
task's own Intent Contract.

Seed convention (explicit, not silently assumed): the holo-informed
ceiling scan seeds `time_averaged_ctqw` from the FULL active-site array
(`labels.Labels.active_site`), not `run_challenge.py`'s single-scalar
TASK-0090 workaround (this script never calls `select.py`, so that
crash-avoidance workaround does not apply here -- same reasoning
`TASK-0105`/`TASK-0046`'s own real-target cross-check already used).
Per `REVIEW-panel-2026-07-16-v2.md` (2026-07-16) §2.1/Hidden Assumptions:
even this "full array" convention is itself an unfixed gauge (a coherent
equal-amplitude superposition, not the panel's recommended incoherent
mixture) -- flagged here explicitly, not fixed by this task (out of
TASK-0110's own scope, which is t_max/n_steps, not source/seed choice).
Any AUC number this script reports inherits that caveat.

The apo-only floor scan has NO seed-gauge exposure at all: `propagators.
check_convergence`'s criteria are pure functions of H's own eigenvalue
spectrum, never a propagation source.

Run: python3 scripts/optuna_parameter_scan.py --target KRAS_G12C BCR_ABL1 CARDIAC_MYOSIN
Output: __WORK_IN_PROGRESS__/results_task0110/<target>/scan.json
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

_SCRIPTS = Path(__file__).resolve().parent
_SRC = _SCRIPTS.parent / "src"
for p in (_SRC, _SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.optuna_scan import apo_floor_scan, closed_form_prescription, holo_ceiling_scan  # noqa: E402

import run_challenge  # noqa: E402

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0110"


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _study_summary(study) -> dict:
    return {
        "best_value": study.best_value,
        "best_params": study.best_params,
        "best_trial_user_attrs": dict(study.best_trial.user_attrs),
        "n_trials": len(study.trials),
        "n_converged": sum(1 for t in study.trials if t.user_attrs.get("converged")) if any(
            "converged" in t.user_attrs for t in study.trials
        ) else None,
        "search_range": dict(study.user_attrs),
        "trials": [
            {"params": t.params, "value": t.value, "user_attrs": dict(t.user_attrs)}
            for t in study.trials
        ],
    }


def run_target(target_name: str, output_dir: Path, *, n_trials_floor: int, n_trials_ceiling: int, seed: int) -> dict:
    target_dir = output_dir / target_name
    target_dir.mkdir(parents=True, exist_ok=True)
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))

    result = {"target": target_name, "cutoff": cutoff}

    if target_config.get("holo_pdb") is None:
        # c-Myc/1NKP (TASK-0080): no holo -- floor scan only, no ceiling
        # is possible (matches this project's own no-ground-truth
        # handling convention, not a special case invented here).
        _log(f"{target_name}: no holo_pdb -- floor scan only (TASK-0080 target)")
        apo = clean_from_config(target_name, role="apo")
        H = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
        result["N"] = len(apo.resnums)
        result["closed_form"] = closed_form_prescription(H)
        _log(f"{target_name}: closed-form prescription t_max={result['closed_form']['t_max']:.4g}, "
             f"n_steps={result['closed_form']['n_steps']}")
        t0 = time.monotonic()
        floor_study = apo_floor_scan(H, n_trials=n_trials_floor, seed=seed)
        _log(f"{target_name}: floor scan done in {time.monotonic() - t0:.1f}s "
             f"({sum(1 for t in floor_study.trials if t.user_attrs.get('converged'))}/{n_trials_floor} converged)")
        result["floor"] = _study_summary(floor_study)
        result["ceiling"] = None
        result["ceiling_skip_reason"] = "no holo_pdb -- no labeled pocket to score AUC against"
        with open(target_dir / "scan.json", "w") as f:
            json.dump(result, f, indent=2, default=float)
        return result

    _log(f"{target_name}: fetching + cleaning apo/holo...")
    t0 = time.monotonic()
    apo, holo = run_challenge._load_apo_holo(target_name, target_config)
    _log(f"{target_name}: apo/holo ready in {time.monotonic() - t0:.1f}s (N={len(apo.resnums)})")
    result["N"] = len(apo.resnums)

    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")
    active_idx = np.where(labels_obj.active_site)[0]  # full array -- see module docstring's seed-convention note
    if len(active_idx) == 0:
        raise RuntimeError(f"{target_name}: empty active_site mask")

    H = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)

    cf = closed_form_prescription(H)
    result["closed_form"] = cf
    _log(f"{target_name}: closed-form prescription t_max={cf['t_max']:.4g}, n_steps={cf['n_steps']}, "
         f"cost={cf['cost']:.4g} (current pipeline default: t_max=15.0, n_steps=500)")

    _log(f"{target_name}: apo floor scan ({n_trials_floor} trials)...")
    t0 = time.monotonic()
    floor_study = apo_floor_scan(H, n_trials=n_trials_floor, seed=seed)
    n_conv = sum(1 for t in floor_study.trials if t.user_attrs.get("converged"))
    _log(f"{target_name}: floor scan done in {time.monotonic() - t0:.1f}s ({n_conv}/{n_trials_floor} converged, "
         f"best cost={floor_study.best_value:.4g})")
    result["floor"] = _study_summary(floor_study)

    _log(f"{target_name}: holo ceiling scan, aspirational range ({n_trials_ceiling} trials, "
         f"propagation source = {len(active_idx)}-residue full active-site array)...")
    t0 = time.monotonic()
    ceiling_study = holo_ceiling_scan(H, active_idx, labels_obj.pocket, n_trials=n_trials_ceiling, seed=seed)
    n_capped = sum(1 for t in ceiling_study.trials if t.user_attrs.get("n_steps_capped"))
    _log(f"{target_name}: aspirational ceiling scan done in {time.monotonic() - t0:.1f}s "
         f"(best AUC={ceiling_study.best_value:.4f} at t_max={ceiling_study.best_params['t_max']:.4g}, "
         f"{n_capped}/{n_trials_ceiling} trials hit the n_steps cap)")
    result["ceiling_aspirational"] = _study_summary(ceiling_study)
    if n_capped == n_trials_ceiling:
        _log(f"{target_name}: EVERY aspirational trial was n_steps-capped -- every explored "
             f"occupation is Nyquist-aliased, not genuinely converged; that AUC is not a real "
             f"ceiling. Running a second, practical scan restricted to the uncapped-reachable "
             f"t_max range.")

    # Practical/uncapped ceiling: restrict t_max to the range where the
    # Nyquist-adequate n_steps (at oversample=1) never exceeds max_n_steps
    # -- i.e. every trial in this second scan is genuinely, not aliased,
    # sampled. Complements (does not replace) the aspirational scan above:
    # the aspirational range answers "what would the ceiling be if we
    # could afford true convergence" (currently: we can't, see above); this
    # answers "what is the best AUC actually achievable within real
    # compute constraints, honestly sampled."
    from allostery.optuna_scan import _DEFAULT_MAX_N_STEPS
    w = np.linalg.eigvalsh(H)
    bandwidth = float(w[-1] - w[0])
    practical_t_max_max = (_DEFAULT_MAX_N_STEPS - 1) * np.pi / bandwidth if bandwidth > 0 else 60.0
    # Lower bound anchored at a small constant (not a fraction of
    # practical_t_max_max), so this range always includes the *current*
    # pipeline default (t_max=15) regardless of how large the uncapped
    # ceiling happens to be -- otherwise a scan whose range starts well
    # above 15 could never discover whether the existing default is
    # already near-optimal within the honestly-sampled region (found by
    # inspection: the first version of this range started at 150 for
    # KRAS_G12C, silently excluding 15 from the search entirely).
    practical_range = (min(1.0, practical_t_max_max * 0.5), practical_t_max_max)
    _log(f"{target_name}: holo ceiling scan, practical/uncapped range "
         f"[{practical_range[0]:.4g}, {practical_range[1]:.4g}] ({n_trials_ceiling} trials)...")
    t0 = time.monotonic()
    practical_study = holo_ceiling_scan(
        H, active_idx, labels_obj.pocket, n_trials=n_trials_ceiling, seed=seed,
        t_max_range=practical_range,
    )
    n_capped_practical = sum(1 for t in practical_study.trials if t.user_attrs.get("n_steps_capped"))
    _log(f"{target_name}: practical ceiling scan done in {time.monotonic() - t0:.1f}s "
         f"(best AUC={practical_study.best_value:.4f} at t_max={practical_study.best_params['t_max']:.4g}, "
         f"{n_capped_practical}/{n_trials_ceiling} trials hit the cap [should be 0])")
    result["ceiling_practical"] = _study_summary(practical_study)
    result["ceiling"] = result["ceiling_practical"]  # the trustworthy one, for any downstream consumer

    with open(target_dir / "scan.json", "w") as f:
        json.dump(result, f, indent=2, default=float)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--n-trials-floor", type=int, default=200)
    parser.add_argument("--n-trials-ceiling", type=int, default=50)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args(argv)

    for name in args.target:
        try:
            run_target(name, args.output_dir, n_trials_floor=args.n_trials_floor,
                       n_trials_ceiling=args.n_trials_ceiling, seed=args.seed)
        except Exception as exc:
            _log(f"{name}: FAILED -- {exc!r}")
            import traceback
            traceback.print_exc()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
