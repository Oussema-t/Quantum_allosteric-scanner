#!/usr/bin/env python3
"""TASK-0186 -- active-site <-> pocket distance generalization audit, on
THREE independent axes.

Question this answers: TASK-0169 found KRAS_G12C's labelled pocket comes
within 3.75 A (Euclidean) of the active site and called that "trivial" for
that one target. This script checks whether that is a KRAS-specific
artifact or a property of the benchmark set as a whole, and separates two
distinct notions of "close" that a single Euclidean number conflates:

  1. **Euclidean** Ca-Ca distance -- straight-line 3-D distance, TASK-0169's
     original metric.
  2. **Spatial contact-graph hop-distance** -- BFS hop-count on the same
     8.0 A contact-graph convention used everywhere else in this codebase
     (TASK-0067). This is what actually matters for a propagation observable
     (CTQW/H_new): it "detects" a 1-hop pocket for free regardless of 3-D
     distance, as long as it is a direct graph neighbour.
  3. **Primary-sequence ("chain") hop-distance** -- BFS hop-count on a
     backbone-only graph (edges only between consecutive residues of the
     SAME chain, no spatial contacts at all). This is the number of
     residues apart along the polypeptide chain. Distinguishing it from (2)
     matters: if active-site and pocket residues are close in BOTH sequence
     and space, that is the most trivial case (near-contiguous backbone,
     no tertiary fold required). If they are close in space (2) but FAR
     apart in sequence (3), that is a genuine tertiary-fold-mediated
     shortcut -- the ratio (3)/(2) is a *static*, ENM-free "fold
     compression factor": how much the native fold alone, with no
     conformational sampling, already collapses sequence separation into
     few contact-hops. That ratio is the natural pre-ENM baseline for
     TASK-0187's dynamic shortcut hypothesis -- if the static fold already
     compresses heavily, ENM wobbling only needs to add a little on top;
     if it doesn't, TASK-0187's dynamic effect is carrying more weight.

Read-only diagnostic. Does not touch scoring, does not modify any label,
does not write to config/targets.yaml. Reuses already-`Done`, already-
committed machinery for (1)/(2): `clean.clean_from_config`/
`load_target_config`, `labels.build_labels`, `baselines.hop_from_seed`. (3)
is new (no existing backbone-only graph builder was found in this codebase
-- grepped for one before writing this), built here as a simple per-chain
BFS on `CleanResult.chain_ids`, same `n+1`-unreachable convention as
`hop_from_seed` for cross-chain pairs.

Run against the INCUMBENT 4.5 A contact label only (TASK-0177's consensus
label does not exist yet at the time this script was written) -- every
result below is explicitly flagged `label=incumbent` for that reason and
must be re-run against TASK-0177's `core`/`consensus` labels once available,
per that task's own "never substitute, always report side by side"
convention.
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

from allostery.baselines import hop_from_seed  # noqa: E402
from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.labels import build_labels, ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue  # noqa: E402

DEFAULT_POCKET_CUTOFF = 4.5
HOP_CUTOFF = 8.0  # TASK-0067's retained contact scale -- do not invent a new one.


def _load_apo_holo(target_name: str, target_config: dict):
    """Fetch + clean apo/holo, attach holo's ligand_groups/heavy-atom data.

    `build_labels` needs `holo.ligand_groups`/`heavy_atom_coords`, which
    `clean_from_config` alone does not attach -- ported verbatim from
    `run_challenge.py::_load_apo_holo` (not cross-imported, this is a
    separate script) rather than re-derived, since that is the one place
    this exact recipe is already tested against live RCSB data.
    """
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

# The 7 pocket-scoreable status:verified targets (MYC_MAX excluded: no
# folded-state pocket, `allosteric_pocket_exists: false`).
TARGETS = [
    "KRAS_G12C",
    "BCR_ABL1",
    "CARDIAC_MYOSIN",
    "PTP1B",
    "GLUCOKINASE",
    "CASPASE1",
    "CASPASE7",
]


def chain_hop_from_seed(chain_ids: list[str], source: np.ndarray, n: int) -> np.ndarray:
    """Backbone-only (primary-sequence) hop-distance from the seed set.

    Edges only between array-adjacent residues (i, i+1) of the SAME chain
    -- no spatial contacts at all. Since this graph is a disjoint union of
    simple paths (one per chain), shortest-path distance on it reduces to
    plain index arithmetic: for same-chain pairs it's |i - j|; cross-chain
    pairs are unreachable. No networkx needed, but same `n+1`-unreachable
    convention as `baselines.hop_from_seed` so callers can treat the two
    outputs identically.
    """
    chain_arr = np.asarray(chain_ids)
    idx = np.atleast_1d(np.asarray(source, dtype=int))
    dist = np.full(n, float(n + 1))
    positions = np.arange(n)
    for s in idx.tolist():
        same_chain = chain_arr == chain_arr[s]
        d = np.abs(positions - s).astype(float)
        d = np.where(same_chain, d, float(n + 1))
        dist = np.minimum(dist, d)
    return dist


def _summ(values: np.ndarray, reachable: np.ndarray, thresholds=(1, 2, 3)) -> dict:
    v = values[reachable]
    if not reachable.any():
        out = {"min": None, "mean": None, "median": None, "max": None}
        out.update({f"frac_le_{t}": None for t in thresholds})
        return out
    out = {
        "min": float(np.min(v)),
        "mean": float(np.mean(v)),
        "median": float(np.median(v)),
        "max": float(np.max(v)),
    }
    out.update({f"frac_le_{t}": float(np.mean(v <= t)) for t in thresholds})
    return out


def audit_one(name: str) -> dict:
    t0 = time.monotonic()
    target_config = load_target_config(name)
    apo, holo = _load_apo_holo(name, target_config)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", DEFAULT_POCKET_CUTOFF))
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)

    if labels_obj.pocket is None or not labels_obj.pocket.any():
        return {"target": name, "ok": False, "reason": "no resolvable pocket label"}
    if not labels_obj.active_site.any():
        return {"target": name, "ok": False, "reason": "no resolvable active site"}

    active_idx = np.where(labels_obj.active_site)[0]
    pocket_idx = np.where(labels_obj.pocket)[0]
    n = len(apo.resnums)
    unreachable_penalty = float(n + 1)

    # (1) Euclidean: min Ca-Ca distance from each pocket residue to the
    # nearest active-site residue -- TASK-0169's original metric.
    diff = apo.coords[pocket_idx, None, :] - apo.coords[None, active_idx, :]
    euclid_pocket = np.min(np.sqrt((diff ** 2).sum(axis=2)), axis=1)

    # (2) Spatial contact-graph hop-distance.
    neg_hops = hop_from_seed(apo.coords, source=active_idx, cutoff=HOP_CUTOFF)
    spatial_hops = (-neg_hops)[pocket_idx]

    # (3) Primary-sequence (chain/backbone) hop-distance.
    chain_hops_all = chain_hop_from_seed(apo.chain_ids, source=active_idx, n=n)
    chain_hops = chain_hops_all[pocket_idx]

    spatial_reachable = spatial_hops < unreachable_penalty
    chain_reachable = chain_hops < unreachable_penalty

    # Static, ENM-free "fold compression factor": how much the native fold
    # alone already compresses sequence separation into contact-hops. Only
    # defined where both axes are reachable and spatial_hops > 0 (an active
    # site residue itself, hop 0, has no meaningful ratio).
    both_reachable = spatial_reachable & chain_reachable & (spatial_hops > 0)
    compression = np.divide(
        chain_hops, spatial_hops,
        out=np.full_like(spatial_hops, np.nan), where=both_reachable,
    )

    result = {
        "target": name,
        "ok": True,
        "label": "incumbent",
        "pocket_contact_cutoff_A": pocket_cutoff,
        "hop_graph_cutoff_A": HOP_CUTOFF,
        "n_residues": int(n),
        "n_active_site": int(len(active_idx)),
        "n_pocket": int(len(pocket_idx)),
        "n_pocket_spatially_unreachable": int((~spatial_reachable).sum()),
        "n_pocket_chain_unreachable": int((~chain_reachable).sum()),
        "euclid_min_A": _summ(euclid_pocket, np.ones_like(euclid_pocket, dtype=bool)),
        "spatial_hop": _summ(spatial_hops, spatial_reachable),
        "chain_hop": _summ(chain_hops, chain_reachable),
        "fold_compression_ratio_chain_over_spatial": (
            {
                "mean": float(np.nanmean(compression)) if both_reachable.any() else None,
                "median": float(np.nanmedian(compression)) if both_reachable.any() else None,
                "n": int(both_reachable.sum()),
            }
        ),
        "elapsed_s": round(time.monotonic() - t0, 1),
    }
    return result


def main() -> int:
    out = []
    for name in TARGETS:
        print(f"{name}: running...", file=sys.stderr)
        try:
            r = audit_one(name)
        except Exception as exc:  # noqa: BLE001 -- diagnostic script, report and continue
            r = {"target": name, "ok": False, "reason": f"{type(exc).__name__}: {exc}"}
        print(f"{name}: {r}", file=sys.stderr)
        out.append(r)

    out_dir = Path(__file__).resolve().parent.parent / "results/tasks/0186_hop_distance_audit"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nWrote {out_path}")

    print("\n=== summary (incumbent 4.5A label, hop graph cutoff 8.0A) ===")
    for r in out:
        if not r.get("ok"):
            print(f"{r['target']:16s} FAILED: {r.get('reason')}")
            continue
        eu, sh, ch, fc = r["euclid_min_A"], r["spatial_hop"], r["chain_hop"], r["fold_compression_ratio_chain_over_spatial"]
        print(
            f"{r['target']:16s} n_pocket={r['n_pocket']:3d}  "
            f"euclid_min(A) min/med={eu['min']:.1f}/{eu['median']:.1f}  "
            f"spatial_hop min/med={sh['min']:.1f}/{sh['median']:.1f} (<=1:{sh['frac_le_1']:.2f} <=2:{sh['frac_le_2']:.2f})  "
            f"chain_hop min/med={ch['min']:.1f}/{ch['median']:.1f}  "
            f"fold_compression(chain/spatial) mean={fc['mean']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
