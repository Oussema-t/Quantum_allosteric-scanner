#!/usr/bin/env python3
"""TASK-0228 §6.2 -- progress probability `p`, the drop's own "single
cheapest decisive measurement in the proposal."

**Partial, not the full joint measurement the document specifies** -- see
this task's own Q-0001 to Architect/Planner for why, and TASK-0228's Done
section for the honest scope statement. This measures `p` for the
COLLECTIVE move layer only (single-mode +/- ANM excitations, TASK-0015's
already-validated, steric-clash-gated `build_deformation_family`), at the
single starting node (apo) -- not the full joint backbone(x)local(x)rotamer
move set, which needs a global-optimum rotamer packer (EvoEF2, confirmed
absent, TASK-0227's own Done section) and a local-relief move type (never
built, §4.1 item 2).

Definition used (document's own §6.2, "fraction of admissible moves that
reduce the objective"): objective = mean Ca displacement of the real,
labeled pocket residues from their TRUE holo positions (Kabsch-aligned) --
`superpose.cryptic_openness_gate`'s own quantity, computed once at apo
(baseline) and once per admissible candidate. p = fraction of admissible
candidates whose pocket-RMSD-to-holo is lower than the apo baseline's.

Explicit label-leakage header, matching this project's own `ceiling.md`
convention (§5's own instruction): **this measurement sees holo** (the
true pocket positions being approached) -- it characterizes the collective
move set's own progress-making ability, exactly HOLO_DIRECTION_MODULE.md's
own "using holo to characterize the method... is legal; using holo to
parameterize the predictor is not" firewall. Nothing here is a predictor
or a per-target scoring knob.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.holo_direction import PERTURBATION_PROTOCOL, build_deformation_family  # noqa: E402
from allostery.labels import build_labels, ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue  # noqa: E402
from allostery.superpose import align_apo_holo, chain_map_from_config  # noqa: E402

TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN"]
DEFAULT_POCKET_CUTOFF = 4.5

# NOT HOLO_DIRECTION_MODULE.md's own frozen PERTURBATION_PROTOCOL, reused
# only for its integrity-constraint machinery. That protocol's own
# amplitude_scales (0.5, 1.0, 2.0 thermal units) were pre-registered for a
# DIFFERENT purpose -- generating a small, curated family to probe for a
# shortcut (TASK-0015 Step 2) -- and reject 53-59 of 60 candidates on
# these real targets (checked directly, not assumed): n_admissible=1-7
# per target is statistically unusable for a progress-PROBABILITY
# estimate. A `p` measurement needs many admissible samples, not a small
# curated set, so this script uses its own, smaller amplitude grid
# (~2-10x smaller thermal-unit steps) chosen for admissibility yield, not
# reused/mutated from the frozen protocol -- confirmed directly (not
# assumed) that this range keeps a physically real, non-trivial
# displacement per step while lifting the admissible fraction to
# ~78-100% (checked against 4 candidate grids before picking this one).
P_MEASUREMENT_PROTOCOL = dict(PERTURBATION_PROTOCOL, amplitude_scales=(0.1, 0.2, 0.3))


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


def _pocket_rmsd_to_holo(coords: np.ndarray, measurable_apo_idx: np.ndarray,
                          measurable_holo_idx: np.ndarray, aligned_holo_coords: np.ndarray) -> float:
    """Same quantity as `cryptic_openness_gate`'s own `pocket_rmsd_mean`,
    generalized to accept arbitrary coordinates (a deformation candidate),
    not only literal `apo.coords` -- deliberately not modifying that
    function itself, which is already validated and used elsewhere."""
    disp = np.sqrt(((aligned_holo_coords[measurable_holo_idx] - coords[measurable_apo_idx]) ** 2).sum(axis=1))
    return float(disp.mean())


def run_one(target_name: str) -> dict:
    target_config = load_target_config(target_name)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))

    apo, holo = _load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{target_name}: no resolvable pocket label")

    alignment = align_apo_holo(apo, holo, chain_map=chain_map_from_config(target_config))
    apo_idx, holo_idx = alignment.apo_idx, alignment.holo_idx
    in_common = np.zeros(len(labels_obj.pocket), dtype=bool)
    in_common[apo_idx] = True
    measurable = labels_obj.pocket & in_common
    if not measurable.any():
        raise RuntimeError(f"{target_name}: no pocket residue has a holo correspondence")

    apo_to_holo = dict(zip(apo_idx.tolist(), holo_idx.tolist()))
    measurable_apo_idx = np.where(measurable)[0]
    measurable_holo_idx = np.array([apo_to_holo[i] for i in measurable_apo_idx])

    baseline = _pocket_rmsd_to_holo(apo.coords, measurable_apo_idx, measurable_holo_idx,
                                     alignment.aligned_holo_coords)

    family = build_deformation_family(apo.coords, apo.b_mean, protocol=P_MEASUREMENT_PROTOCOL)
    n_admissible = len(family["admissible"])
    n_rejected = len(family["rejected"])
    if n_admissible == 0:
        raise RuntimeError(f"{target_name}: zero admissible collective moves ({n_rejected} rejected)")

    progress = []
    for entry in family["admissible"]:
        rmsd = _pocket_rmsd_to_holo(entry["coords"], measurable_apo_idx, measurable_holo_idx,
                                     alignment.aligned_holo_coords)
        progress.append(rmsd < baseline)
    progress = np.array(progress)
    p = float(progress.mean())

    result = {
        "target": target_name, "n_residues": len(apo.resnums),
        "n_pocket_measurable": int(len(measurable_apo_idx)),
        "baseline_pocket_rmsd_to_holo": round(baseline, 4),
        "n_admissible": n_admissible, "n_rejected": n_rejected,
        "n_progress": int(progress.sum()), "p": round(p, 4),
    }
    print(
        f"{target_name}: N={result['n_residues']} n_pocket={result['n_pocket_measurable']} "
        f"baseline_rmsd={baseline:.3f} admissible={n_admissible} (rejected={n_rejected}) "
        f"progress={result['n_progress']}/{n_admissible}  p={p:.3f}"
    )
    return result


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", nargs="+", default=TARGETS)
    parser.add_argument(
        "--output", type=Path,
        default=Path(__file__).resolve().parent.parent / "results/tasks/0228/progress_probability_p.json",
    )
    args = parser.parse_args(argv)

    results = {}
    for target_name in args.target:
        try:
            results[target_name] = run_one(target_name)
        except Exception as exc:
            print(f"{target_name}: FAILED -- {exc!r}")
            results[target_name] = {"target": target_name, "error": str(exc)}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
