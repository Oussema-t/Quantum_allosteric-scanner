#!/usr/bin/env python3
"""TASK-0092 -- wire the holo-side diagnostic comparison into a real run.

Populates `AUC_holo_Hnew_optimised` / `mean_rho_apo_holo` / `mean_jacc20`
(left `N/A` by `run_challenge.py`, TASK-0079.004's own documented scope
boundary) by supplying `protocol.run_frozen_verdict`'s optional
`holo_H`/`holo_source`/`holo_labels`/`apo_idx`/`holo_idx` kwargs -- this
script composes nothing that function doesn't already do; see its
docstring for the composition itself.

**This is a diagnostic upper bound, never a prediction.** A real
predictive setting never has holo in advance (`PLAN.md`'s "is the answer
even in the apo topology?" framing). Its value here is purely
explanatory: it distinguishes (a) apo genuinely lacks the information
(a real cryptic-pocket finding) from (b) the propagator/operator itself
is the bottleneck (holo wouldn't have helped either) -- see this task's
own Context section for the full argument, and TASK-0067 for the prior,
narrower (bare-Kirchhoff) version of the same check this script extends
to the full H_new/CTQW pipeline.

Two-pass per target, both real `run_frozen_verdict` calls (never
reimplementing `select_frozen_config`'s selection):
  Pass 1 (apo only) -- discovers which candidate wins blind selection,
    exactly as `run_challenge.py::run_target` does.
  Pass 2 (apo + holo) -- builds `holo_H` from the *same* operator recipe
    as pass 1's winner, then supplies the holo kwargs so
    `run_frozen_verdict` computes the full composition in one real,
    frozen-gated call. Pass 2 asserts it re-selects the same winner
    (selection is blind/deterministic -- no RNG in `select.py`'s scoring
    path) as a live self-check, not an assumed shortcut.

Holo-frame pocket/active-site labels use `_holo_native_labels`, reused
verbatim (import, not re-derivation) from TASK-0067's own benchmark
module -- entirely holo-numbered, no apo involved, mirroring
`build_labels`'s exclusion assembly so the holo run is scored against a
label built the same way the apo run's was.

Run: python3 scripts/holo_diagnostic_comparison.py --target KRAS_G12C BCR_ABL1
Output: __WORK_IN_PROGRESS__/results_task0092/<target>/{verdict.json,report.txt}
(results_*/ is gitignored, same convention as TASK-0094's scratch runs.)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_SCRIPTS = Path(__file__).resolve().parent
_SRC = _SCRIPTS.parent / "src"
_TESTS = _SCRIPTS.parent / "tests"
for p in (_SRC, _TESTS, _SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from allostery.clean import load_target_config  # noqa: E402
from allostery.hamiltonians import build_H_new, build_H10  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.protocol import run_frozen_verdict  # noqa: E402
from allostery.report import verdict_template  # noqa: E402
from allostery.superpose import align_apo_holo  # noqa: E402

# Reused, not re-derived (Intent Contract) -- run_challenge.py's own loader
# and candidate builder, TASK-0067's holo-native-label construction.
import run_challenge  # noqa: E402
from test_gnm_cutoff_weight_benchmark import _holo_native_labels  # noqa: E402

T_MAX = 15.0
N_STEPS = 500
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results_task0092"

# Maps a winning candidate's own "name" (candidates_builder's dict key,
# run_challenge.py's _make_candidates_builder) to the builder that
# constructs the *same* operator family on holo's coordinates -- so
# holo_H is genuinely "the same operator recipe as the winning apo
# candidate", not assumed to always be H_new.
_HOLO_BUILDERS = {
    "H_new_default": lambda coords, bfactors, cutoff: build_H_new(coords, bfactors, cutoff=cutoff),
    "H10_disorder_suppressed": lambda coords, bfactors, cutoff: build_H10(coords, bfactors, cutoff=cutoff),
}


def run_target(target_name: str, output_dir: Path) -> dict:
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))

    apo, holo = run_challenge._load_apo_holo(target_name, target_config)

    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None:
        raise RuntimeError(f"{target_name}: no resolvable drug_ligand, cannot score a pocket label")

    active_site_idx = np.where(labels_obj.active_site)[0]
    if len(active_site_idx) == 0:
        raise RuntimeError(f"{target_name}: empty active_site mask")
    source = int(np.sort(active_site_idx)[0])  # same single-seed convention as run_challenge.py (TASK-0090)

    from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed
    floor_scores = [
        degree_centrality(apo.coords, cutoff=cutoff),
        euclid_from_seed_centroid(apo.coords, source),
        hop_from_seed(apo.coords, source, cutoff=cutoff),
    ]
    candidates_builder = run_challenge._make_candidates_builder(apo, source, cutoff)

    # Pass 1: apo-only, discover the real winner for this fresh run.
    pass1 = run_frozen_verdict(
        target_name, candidates_builder,
        apo.coords, apo.bfactors, source, labels_obj.pocket,
        cutoff=cutoff, t_max=T_MAX, n_steps=N_STEPS,
        floor_scores=floor_scores,
    )
    winner_index = pass1["_winner_index"]
    winner_name = candidates_builder()[winner_index]["name"]

    # Holo-native labels/source (TASK-0067's own construction, holo-only numbering).
    holo_pocket, holo_active, _ = _holo_native_labels(holo, target_config, pocket_cutoff)
    if not holo_pocket.any():
        raise RuntimeError(f"{target_name}: holo-native pocket label is empty")
    holo_source_idx = np.where(holo_active)[0]
    if len(holo_source_idx) == 0:
        raise RuntimeError(f"{target_name}: holo-native active_site mask is empty")
    holo_source = int(np.sort(holo_source_idx)[0])

    holo_H = _HOLO_BUILDERS[winner_name](holo.coords, holo.bfactors, cutoff)

    alignment = align_apo_holo(apo, holo)

    # Pass 2: apo + holo together, the real composed run.
    pass2 = run_frozen_verdict(
        target_name, candidates_builder,
        apo.coords, apo.bfactors, source, labels_obj.pocket,
        cutoff=cutoff, t_max=T_MAX, n_steps=N_STEPS,
        floor_scores=floor_scores,
        holo_H=holo_H, holo_source=holo_source, holo_labels=holo_pocket,
        apo_idx=alignment.apo_idx, holo_idx=alignment.holo_idx,
    )
    if pass2["_winner_index"] != winner_index:
        raise RuntimeError(
            f"{target_name}: selection was not deterministic across passes "
            f"({winner_index} -> {pass2['_winner_index']}) -- holo_H was built "
            "for the wrong operator family; do not trust this run's holo numbers."
        )

    result = {
        "target": target_name,
        "winner": winner_name,
        "cutoff": cutoff,
        "verdict": pass2,
    }

    # Addendum (2026-07-13): ground_state_relaxation's holo-side AUC for
    # BCR_ABL1 specifically, per TASK-0092's Addendum section. Computed
    # directly (not through run_frozen_verdict, which only threads the
    # ctqw side of qvc into AUC_holo_Hnew_optimised) -- holo_H/holo_source/
    # holo_labels are already the real, verified pass-2 inputs, so this is
    # extra reporting on already-built data, not a new selection step.
    if target_name == "BCR_ABL1":
        from allostery.analysis import quantum_vs_classical
        holo_qvc = quantum_vs_classical(holo_H, holo_source, holo_pocket, t_max=T_MAX, n_steps=N_STEPS)
        result["gsr_holo_auc"] = float(holo_qvc["heat"]["AUC"])
        result["gsr_holo_matches_ctqw_holo"] = float(holo_qvc["ctqw"]["AUC"])

    target_dir = output_dir / target_name
    target_dir.mkdir(parents=True, exist_ok=True)
    with open(target_dir / "verdict.json", "w") as f:
        json.dump(run_challenge._jsonify(pass2), f, indent=2)
    with open(target_dir / "report.txt", "w") as f:
        f.write(verdict_template(pass2, provenance="frozen"))
        if "gsr_holo_auc" in result:
            f.write(
                f"\n\n[TASK-0092 addendum] ground_state_relaxation, holo-native "
                f"labels: AUC = {result['gsr_holo_auc']:.4f} "
                f"(apo AUC_heat_mean = {pass2.get('AUC_heat_mean', 'N/A')})\n"
            )

    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=["KRAS_G12C", "BCR_ABL1"])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)

    for name in args.target:
        try:
            r = run_target(name, args.output_dir)
        except Exception as exc:
            print(f"{name}: FAILED -- {exc!r}")
            continue

        v = r["verdict"]
        print(f"\n=== {name} (winner={r['winner']}, cutoff={r['cutoff']}) ===")
        print(f"  AUC_apo_Hnew_optimised  = {v.get('AUC_apo_Hnew_optimised', 'N/A')}")
        print(f"  AUC_holo_Hnew_optimised = {v.get('AUC_holo_Hnew_optimised', 'N/A')}")
        print(f"  mean_rho_apo_holo       = {v.get('mean_rho_apo_holo', 'N/A')}")
        print(f"  mean_jacc20             = {v.get('mean_jacc20', 'N/A')}")
        if "gsr_holo_auc" in r:
            print(f"  ground_state_relaxation holo AUC = {r['gsr_holo_auc']:.4f} "
                  f"(apo AUC_heat_mean = {v.get('AUC_heat_mean', 'N/A')})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
