#!/usr/bin/env python3
"""TASK-0093 -- factorial isolation of KRAS_G12C's AUC discrepancy.

Reconciles two real, tested numbers for the same target:
  - TASK-0079.005's real end-to-end run: AUC_apo_Hnew_default = 0.779
    (enm_cutoff=8.0, build_labels' assembled `.pocket`, apo-native
    `active_site` source, narrowed to a single scalar seed -- TASK-0090's
    documented select.py limitation, which the real run's own
    `run_frozen_verdict`/`benchmark()` call inherits since it reuses the
    same scalar `source` throughout).
  - test_analysis.py::test_kras_g12c_real_target_near_chance_and_flat_dephasing
    (pre-dates TASK-0070's exclusion assembly): AUC in (0.3, 0.7), a
    freshly-computed ~0.51-0.53 (enm_cutoff=10.0, raw `holo_pocket_mask`
    pre-exclusion, holo-computed GDP-contact source cross-mapped to apo
    via `superpose.align_apo_holo`, a full multi-index array).

Three named variables, each isolated by holding the other two fixed
(Intent Contract): cutoff (8.0 vs 10.0), pocket-label definition
(assembled vs raw), source definition (apo-native vs holo-mapped).

Two more variables were discovered while reproducing the two reference
points exactly (neither originally named in the task; both reported
explicitly per this session's own "don't collapse the spread
prematurely" discipline, not folded silently into the named axes):

- **Cardinality.** The real run's apo-native source is a SCALAR
  (TASK-0090's workaround narrows it before `benchmark()` ever sees it),
  while the old test's holo-mapped source is the FULL multi-index array.
  "Source definition" as named in this task's Context bundles two
  effects (frame: apo vs holo; cardinality: scalar vs array). A
  supplementary cardinality-only check (apo-native, scalar vs array,
  both other variables held fixed) isolates this.
- **Heavy-atom vs Calpha-only contact geometry.** `run_challenge.py`'s
  `_load_apo_holo` attaches `holo.heavy_atom_coords`/
  `heavy_atom_seq_index` (`labels.protein_heavy_atoms_by_residue`)
  before calling `build_labels` -- `build_labels`/`holo_pocket_mask`
  use these via `getattr(holo, ...)` when present (labels.py:448-451),
  materially changing the contact set (labels.py's own docstring: a
  Calpha-only approximation recovered only 9/21 of the KRAS reference
  pocket). The old near-chance test never attaches these fields, so its
  `holo_pocket_mask`/`functional_indices` calls are Calpha-only by
  omission, not by an explicit "raw" design choice. This script
  therefore builds two `holo` variants -- `holo_bare` (matches the old
  test exactly) and `holo_heavy` (matches the real run exactly) -- and
  keeps this axis explicit rather than silently picking one geometry
  for both "assembled" and "raw".

Every combination is scored against TASK-0094's proximity floor
(`baselines.euclid_from_seed_centroid`/`hop_from_seed`, plus
`degree_centrality`) at the SAME cutoff/source used for that row --
REVIEW-2026-07-13 P1-A's hard acceptance criterion: an AUC that rises
without clearing the floor is "raises apparent signal by making the
score more proximity-correlated", not evidence of real allosteric
sensitivity.

Real network + real compute (KRAS_G12C only, small target, cheap to
re-run the full grid) -- not mockable, same precedent as TASK-0079.005/
TASK-0067.

Run: python3 scripts/kras_auc_reconciliation.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import copy

from allostery.analysis import benchmark  # noqa: E402
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import clean, load_target_config  # noqa: E402
from allostery.labels import (  # noqa: E402
    build_labels,
    functional_indices,
    holo_pocket_mask,
    ligand_groups_from_atomgroup,
    protein_heavy_atoms_by_residue,
)
from allostery.metrics import auc as auc_fn  # noqa: E402
from allostery.superpose import align_apo_holo  # noqa: E402

TARGET = "KRAS_G12C"
APO_PDB = "4OBE"
HOLO_PDB = "6OIM"
CHAINS = ["A"]
DRUG_LIGAND = "MOV"
FUNC_LIGAND = ["GDP"]
POCKET_CUTOFF = 4.5
T_MAX = 15.0
N_STEPS = 500


def _load():
    """Returns (apo, holo_bare, holo_heavy). `holo_bare`/`holo_heavy` share
    the same coords/ligand_groups -- `holo_heavy` additionally carries
    `.heavy_atom_coords`/`.heavy_atom_seq_index` (matching
    `run_challenge.py::_load_apo_holo`'s real-run recipe exactly);
    `holo_bare` matches the old near-chance test's recipe exactly (it
    never attaches these fields)."""
    import prody

    apo = clean(APO_PDB, chains=CHAINS)
    holo_bare = clean(HOLO_PDB, chains=CHAINS)
    prody.confProDy(verbosity="none")
    holo_struct = prody.parsePDB(HOLO_PDB, compressed=False).select("chain A")
    holo_bare.ligand_groups = ligand_groups_from_atomgroup(holo_struct)

    holo_heavy = copy.copy(holo_bare)
    holo_heavy.heavy_atom_coords, holo_heavy.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
        holo_struct, CHAINS, holo_bare.resnums
    )
    return apo, holo_bare, holo_heavy


def _holo_mapped_source(apo, holo):
    """Old test's recipe verbatim: GDP contacts computed in holo's own
    frame, cross-mapped to apo via align_apo_holo's common-residue
    correspondence -- a full multi-index array, not narrowed."""
    holo_src_idx, provenance = functional_indices(
        holo.coords, holo.ligand_groups, {"func_ligand": FUNC_LIGAND}
    )
    assert provenance == "func_ligand-contact:GDP"
    alignment = align_apo_holo(apo, holo)
    holo_to_apo = dict(zip(alignment.holo_idx.tolist(), alignment.apo_idx.tolist()))
    apo_src_idx = np.array([holo_to_apo[i] for i in holo_src_idx if i in holo_to_apo])
    return apo_src_idx


def _floor_auc(coords, source, labels, cutoff):
    scores = [
        degree_centrality(coords, cutoff=cutoff),
        euclid_from_seed_centroid(coords, source),
        hop_from_seed(coords, source, cutoff=cutoff),
    ]
    aucs = [auc_fn(s, labels.astype(int)) for s in scores]
    finite = [a for a in aucs if not np.isnan(a)]
    return max(finite) if finite else float("nan")


def main() -> int:
    apo, holo_bare, holo_heavy = _load()
    cfg = load_target_config(TARGET)

    # -- Pocket-label definition -- "assembled" and "apo-native source" use
    # holo_heavy (real run's actual recipe); "raw"/"holo-mapped source" use
    # holo_bare (old test's actual recipe) -- see module docstring's
    # "Heavy-atom vs Calpha-only" note for why these aren't mixed.
    labels_assembled_obj = build_labels(apo, holo_heavy, cfg, cutoff=POCKET_CUTOFF)
    pocket_assembled = labels_assembled_obj.pocket
    pocket_raw = holo_pocket_mask(apo, holo_bare, DRUG_LIGAND, cutoff=POCKET_CUTOFF)
    assert pocket_assembled is not None and pocket_assembled.any()
    assert pocket_raw is not None and pocket_raw.any()

    # -- Source definition --
    apo_active_idx = np.where(labels_assembled_obj.active_site)[0]
    source_apo_scalar = int(np.sort(apo_active_idx)[0])   # TASK-0090 workaround, real run's actual mechanism
    source_apo_array = apo_active_idx                      # full apo-native active_site, no narrowing
    source_holo_mapped = _holo_mapped_source(apo, holo_bare)  # old test's recipe, full array, Calpha-only

    print(f"pocket_assembled: {pocket_assembled.sum()} residues; pocket_raw: {pocket_raw.sum()} residues")
    print(f"source_apo_scalar: {source_apo_scalar}; source_apo_array: {len(source_apo_array)} residues; "
          f"source_holo_mapped: {len(source_holo_mapped)} residues")

    label_variants = [("assembled", pocket_assembled), ("raw", pocket_raw)]
    source_variants = [("apo_native_scalar", source_apo_scalar), ("holo_mapped_array", source_holo_mapped)]
    cutoffs = (8.0, 10.0)

    print("\n=== Core 2x2x2 factorial (cutoff x pocket-label x source) ===")
    header = f"{'cutoff':>7} {'label':>10} {'source':>19} {'AUC':>8} {'floor':>8} {'clears':>7}"
    print(header)
    rows = []
    for cutoff in cutoffs:
        for label_name, labels in label_variants:
            for source_name, source in source_variants:
                bench = benchmark(apo.coords, apo.bfactors, source, labels, cutoff=cutoff, t_max=T_MAX, n_steps=N_STEPS)
                score = bench["H_new_default"]["AUC"]
                floor = _floor_auc(apo.coords, source, labels, cutoff)
                clears = score > floor if not (np.isnan(score) or np.isnan(floor)) else False
                rows.append((cutoff, label_name, source_name, score, floor, clears))
                print(f"{cutoff:>7.1f} {label_name:>10} {source_name:>19} {score:>8.4f} {floor:>8.4f} {str(clears):>7}")

    print("\n=== Supplementary: cardinality-only check (apo-native source, scalar vs full array) ===")
    print(header)
    for cutoff in cutoffs:
        for label_name, labels in label_variants:
            bench = benchmark(apo.coords, apo.bfactors, source_apo_array, labels, cutoff=cutoff, t_max=T_MAX, n_steps=N_STEPS)
            score = bench["H_new_default"]["AUC"]
            floor = _floor_auc(apo.coords, source_apo_array, labels, cutoff)
            clears = score > floor if not (np.isnan(score) or np.isnan(floor)) else False
            print(f"{cutoff:>7.1f} {label_name:>10} {'apo_native_array':>19} {score:>8.4f} {floor:>8.4f} {str(clears):>7}")

    print("\n=== Supplementary: heavy-atom-vs-Calpha contact geometry (pocket_raw, apo_native_scalar source) ===")
    print(header)
    pocket_raw_heavy = holo_pocket_mask(apo, holo_heavy, DRUG_LIGAND, cutoff=POCKET_CUTOFF)
    for cutoff in cutoffs:
        for geom_name, labels in (("raw_calpha_only", pocket_raw), ("raw_heavy_atom", pocket_raw_heavy)):
            bench = benchmark(apo.coords, apo.bfactors, source_apo_scalar, labels, cutoff=cutoff, t_max=T_MAX, n_steps=N_STEPS)
            score = bench["H_new_default"]["AUC"]
            floor = _floor_auc(apo.coords, source_apo_scalar, labels, cutoff)
            clears = score > floor if not (np.isnan(score) or np.isnan(floor)) else False
            print(f"{cutoff:>7.1f} {geom_name:>10} {'apo_native_scalar':>19} {score:>8.4f} {floor:>8.4f} {str(clears):>7}")

    print("\n=== Reference-point reproduction check ===")
    real_run_row = next(r for r in rows if r[0] == 8.0 and r[1] == "assembled" and r[2] == "apo_native_scalar")
    old_test_row = next(r for r in rows if r[0] == 10.0 and r[1] == "raw" and r[2] == "holo_mapped_array")
    print(f"Real run combo  (cutoff=8.0, assembled, apo_native_scalar): AUC={real_run_row[3]:.4f} "
          f"(reference: 0.7792)")
    print(f"Old test combo  (cutoff=10.0, raw, holo_mapped_array):      AUC={old_test_row[3]:.4f} "
          f"(reference: 0.3-0.7 band, ~0.51-0.53)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
