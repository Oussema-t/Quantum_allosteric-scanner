#!/usr/bin/env python3
"""TASK-0155 -- apo-structure sensitivity sweep for KRAS_G12C.

Every result in this register is conditioned on a single, arbitrary apo
structural draw ([[TASK-0124]]'s 5TBY->8QYP swap moved CARDIAC_MYOSIN's AUC
by 0.27 and erased its only positive). This sweeps ONLY the apo input --
holo (6OIM), operator family, cutoffs, seed convention, and label
definition are all held fixed at this target's own shipped config -- and
reports the AUC/P@5/floor-clear distribution across independently
RCSB-verified KRAS G12C apo structures, through the *unmodified* existing
`clean -> build_H_new/H10 -> run_frozen_verdict` pipeline
(`run_challenge.py`'s own machinery, reused directly, not re-derived).

Picked up per `.ai/reviews/2026-07-28/REVIEW-panel-2026-07-28-external.md`
("a single apo structure is the ensemble," §2/§5C) naming this task
specifically as filed-but-unrun and cheap before the 2026-08-08 freeze.

**RCSB verification, this task's own required disclosure (not assumed
from the filing text's own candidate list):**

- **4OBE, the CURRENT `apo_pdb` in `targets.yaml`, is NOT a G12C mutant.**
  Its own RCSB title is "Crystal Structure of GDP-bound Human KRas" and its
  deposited sequence has Gly (wild-type) at position 12 -- confirmed two
  independent ways: (a) the entity's own `pdbx_seq_one_letter_code_can`
  has G, not C, at the anchor-relative position-12 offset (sanity-checked
  against position 13, canonically G in every entry, which any offset bug
  would also have broken); (b) `4OBE`'s own `pdbx_database_related` field
  cross-references 4NMM/4LDJ as "G12C KRas inhibitor complex"/"G12C KRas"
  -- i.e. RCSB's own metadata treats 4OBE as the wild-type structure those
  G12C entries are related to, not as a G12C entry itself. Every prior
  KRAS_G12C AUC number in this project's history was therefore computed
  against a wild-type apo structure for a target labeled "G12C" -- a
  genotype/label mismatch independent of (and more consequential than)
  the structural-sensitivity question this task was filed to answer.
  Retained in this sweep for continuity with everything already reported,
  but reported SEPARATELY and flagged, never pooled into the "valid G12C"
  distribution below.
- **4DSN** (task filing's own 2nd candidate): sequence-verified Asp at
  position 12 -- this is a **G12D** structure, wrong oncogenic mutant.
  Excluded.
- **3GFT** (task filing's own 3rd candidate): title is "Human K-Ras (Q61H)
  in complex with a GTP analogue" -- Gly (wild-type) at position 12, and a
  **different** oncogenic hotspot (Q61H) with a GTP analogue (GNP) bound,
  not GDP -- wrong mutant AND wrong nucleotide state (active- vs.
  inactive-like conformation; mixing these would confound "different
  structural draw" with "different conformational state entirely", a
  different variable than this task isolates). Excluded.
- **The valid candidate pool** (this task's own assembled list, not from
  the filing text): RCSB Search API, full-text "KRAS G12C" + organism
  Homo sapiens (123 raw hits) -> filtered to entries whose OWN deposited
  sequence has Cys at the anchor-relative position-12 offset (112 real
  G12C entries; offset computed from the "TEYKLVVVG" motif, tag-length-
  agnostic, sanity-checked against position 13) -> X-ray only (no NMR
  structures exist for KRAS G12C at all -- checked directly, this task's
  own "handle NMR explicitly" requirement is satisfied by confirming the
  case does not arise, not silently skipped; 3 cryo-EM entries also exist
  and are excluded to keep the comparison homogeneous with holo's own
  X-ray method) -> GDP+Mg-only ligand set (excludes ~90 inhibitor-bound
  structures -- necessary: a bound Switch-II drug measurably remodels
  that pocket, which is exactly the geometry this sweep must NOT bake in
  as a structural "feature"; also excludes GNP/GppNHp-bound entries for
  the same reason 3GFT was excluded above) -> 22 clean candidates, 1.04-
  2.41 A. 10 selected spanning that full resolution range (`CANDIDATES`
  below), comfortably inside this task's own ">=5 (target 8-12)" bound.
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
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.clean import clean, clean_from_config, load_target_config  # noqa: E402
from allostery.labels import build_labels, ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue  # noqa: E402
from allostery.metrics import precision_at_k  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from allostery.protocol import run_frozen_verdict  # noqa: E402

import run_challenge  # noqa: E402 -- reuse _make_candidates_builder + selection constants, not re-derived

TARGET_NAME = "KRAS_G12C"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "RESULTS" / "results_task0155_apo_sensitivity"

# Verified G12C, GDP+Mg-only, X-ray, chain-A candidates (this task's own
# assembled + RCSB-verified pool, see module docstring). Spans the full
# resolution range of the 22-candidate clean pool.
CANDIDATES = [
    "8AZX", "4LDJ", "7A1X", "8TXJ", "8QUG",
    "9UOH", "7YCE", "7MDP", "7RP3", "8AFC",
]
# Current shipped apo, run alongside for continuity -- flagged WT, not
# pooled into the G12C distribution (see module docstring).
CURRENT_FLAGGED_WT = "4OBE"


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _load_holo(target_config: dict):
    """Holo loader, held fixed across the whole sweep -- copied from
    `run_challenge._load_apo_holo`'s own holo-loading half unmodified;
    only the apo side varies in this script."""
    import prody

    holo = clean_from_config(TARGET_NAME, role="holo")
    prody.confProDy(verbosity="none")
    holo_id = target_config["holo_pdb"]
    chains = target_config.get("chains") or sorted(set(holo.chain_ids))
    chain_sel = " or ".join(f"chain {c}" for c in chains)
    holo_struct = prody.parsePDB(holo_id, compressed=False).select(chain_sel)
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)
    holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
        holo_struct, chains, holo.resnums
    )
    return holo


def _load_apo_variant(pdb_id: str, target_config: dict):
    """The one varied quantity in this whole sweep: which apo PDB entry is
    fetched+cleaned. Reuses `clean()` directly (the same function
    `clean_from_config` itself calls) with `target_config`'s own
    chains/keep_nucleic -- everything else about the cleaning recipe is
    unchanged from the shipped pipeline."""
    chains = target_config.get("apo_chains", target_config.get("chains"))
    keep_nucleic = target_config.get("keep_nucleic", False)
    return clean(pdb_id, chains=chains, keep_nucleic=keep_nucleic)


def run_one(pdb_id: str, target_config: dict, holo, cutoff: float, pocket_cutoff: float) -> dict:
    t0 = time.monotonic()
    apo = _load_apo_variant(pdb_id, target_config)

    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        raise RuntimeError(f"{pdb_id}: no resolvable pocket label")
    source = np.sort(np.where(labels_obj.active_site)[0])
    if len(source) == 0:
        raise RuntimeError(f"{pdb_id}: empty active-site seed")

    b_all_zero = bool(np.all(apo.bfactors == 0))

    floor_scores = [
        degree_centrality(apo.coords, cutoff=cutoff),
        euclid_from_seed_centroid(apo.coords, source),
        hop_from_seed(apo.coords, source, cutoff=cutoff),
    ]
    candidates_builder = run_challenge._make_candidates_builder(apo, source, cutoff)

    result = run_frozen_verdict(
        TARGET_NAME, candidates_builder,
        apo.coords, apo.bfactors, source, labels_obj.pocket,
        cutoff=cutoff, t_max=run_challenge.SELECTION_GSR_ABLATION_T,
        n_steps=run_challenge.SELECTION_GSR_ABLATION_N_STEPS,
        floor_scores=floor_scores, coherent=False, use_converged_limit=True,
    )

    winner_H = candidates_builder()[result["_winner_index"]]["H"]
    w, v = np.linalg.eigh(winner_H)
    winner_occ = time_averaged_ctqw_converged(source=source, coherent=False, w=w, v=v)
    p_at_5 = float(precision_at_k(winner_occ, labels_obj.pocket, k=5))

    elapsed = time.monotonic() - t0
    auc = result.get("AUC_apo_Hnew_optimised")
    diagnosis = result.get("_diagnosis")
    floor_clear = diagnosis == "NO_FAILURE_DETECTED"
    _log(
        f"{pdb_id}: N={len(apo.resnums)} pocket={int(labels_obj.pocket.sum())} "
        f"AUC={auc} P@5={p_at_5:.3f} diag={diagnosis} floor_clear={floor_clear} "
        f"b_all_zero={b_all_zero} ({elapsed:.1f}s)"
    )
    return {
        "pdb_id": pdb_id, "N": len(apo.resnums), "pocket_size": int(labels_obj.pocket.sum()),
        "b_all_zero": b_all_zero, "auc": auc, "p_at_5": p_at_5,
        "diagnosis": diagnosis, "floor_clear": floor_clear,
        "score_ci": result.get("_diagnosis_score_ci"),
        "floor_ci": result.get("_diagnosis_floor_ci"),
        "ci_overlap": result.get("_diagnosis_ci_overlap"),
        "winner_index": int(result["_winner_index"]),
        "elapsed_s": round(elapsed, 2),
    }


def main() -> int:
    target_config = load_target_config(TARGET_NAME)
    cutoff = float(target_config.get("enm_cutoff", run_challenge.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", run_challenge.DEFAULT_POCKET_CUTOFF))

    _log("loading fixed holo (6OIM)...")
    holo = _load_holo(target_config)

    results = {"current_flagged_wt": {}, "g12c_verified": {}}

    _log(f"running CURRENT/flagged {CURRENT_FLAGGED_WT} (wild-type, not G12C -- see module docstring)...")
    try:
        results["current_flagged_wt"][CURRENT_FLAGGED_WT] = run_one(
            CURRENT_FLAGGED_WT, target_config, holo, cutoff, pocket_cutoff
        )
    except Exception as exc:
        _log(f"{CURRENT_FLAGGED_WT}: FAILED -- {exc!r}")
        results["current_flagged_wt"][CURRENT_FLAGGED_WT] = {"pdb_id": CURRENT_FLAGGED_WT, "error": str(exc)}

    for pdb_id in CANDIDATES:
        _log(f"running {pdb_id}...")
        try:
            results["g12c_verified"][pdb_id] = run_one(pdb_id, target_config, holo, cutoff, pocket_cutoff)
        except Exception as exc:
            _log(f"{pdb_id}: FAILED -- {exc!r}")
            results["g12c_verified"][pdb_id] = {"pdb_id": pdb_id, "error": str(exc)}
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_DIR / "apo_sensitivity_sweep.json", "w") as f:
            json.dump(results, f, indent=2)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "apo_sensitivity_sweep.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    _log(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
