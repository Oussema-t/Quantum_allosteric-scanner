"""TASK-0216 -- score TASK-0215's new VALID pairs, and re-run TASK-0213's
coupled search on them.

Two questions, both created by [[TASK-0215]] raising the usable-instance
count from 2 to ~6:

**A. Do the register's headline observables behave on new valid instances?**
The new pairs were validated as *instances*; nothing has been *measured* on
them. Scored here: the proximity floor (mandatory), `H_new`/CTQW converged
occupancy (the headline quantum observable), and `dcc_low` k=10 (the one
observable with a surviving positive). Deliberately NOT all 28 -- [[TASK-0199]]
measured effective rank ~3, so scoring 28 would be multiplicity abuse for no
information gain.

**B. Does [[TASK-0213]]'s CLOSED verdict generalize?** TASK-0213 found coupled
backbone+rotamer search succeeds on 13/65 restarts on KRAS_G12C and 0/65 on
PTP1B -- the register's only two valid targets *disagree*, and at n=2 that
could not be adjudicated. With ~6 valid instances it can. If search is easy on
most, PTP1B is the outlier and CLOSED generalizes. If it is hard on most,
KRAS_G12C was the outlier and the route reopens.

**Candidates are never promoted.** They live in
`config/candidate_targets_task0216.yaml`, and `load_target_config` is
monkeypatched to fall back to it -- `config/targets.yaml` is untouched. Same
precedent as [[TASK-0209]]'s local fix to a file under another thread's claim.

**Coverage gap, stated not worked around:** TEM-1's two pairs (the two
*cleanest* contrasts, delta 0.985/0.995) have no functional ligand in their
holo entries, so no active site can be derived and no active-site-seeded
observable can be computed for them. They are scored in leg B (which needs no
seed) and reported as N/A in leg A.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import yaml

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

CANDIDATE_YAML = _ROOT / "config" / "candidate_targets_task0216.yaml"
OUT_DIR = _ROOT / "results_task0216_new_pair_scoring"

# ---- monkeypatch config lookup so candidates resolve without promotion ----
from allostery import clean as _clean  # noqa: E402

_orig_load = _clean.load_target_config
_CANDIDATES = yaml.safe_load(CANDIDATE_YAML.read_text())["targets"]


def _load_with_candidates(target_name: str, config_path=None):
    if target_name in _CANDIDATES:
        return _CANDIDATES[target_name]
    return _orig_load(target_name, config_path)


_clean.load_target_config = _load_with_candidates
import allostery.labels as _labels  # noqa: E402,F401
for _mod in ("task0210_coupled_search",):
    pass

from allostery.clean import clean_from_config  # noqa: E402
from allostery.labels import (  # noqa: E402
    build_labels, ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue,
)
from allostery.baselines import (  # noqa: E402
    degree_centrality, euclid_from_seed_centroid, hop_from_seed,
)
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from allostery.lowmode_predictor import dcc_low  # noqa: E402
from allostery.metrics import auc  # noqa: E402

TARGETS = list(_CANDIDATES.keys())


def _log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def _attach_holo_extras(holo, cfg):
    import prody
    prody.confProDy(verbosity="none")
    ch = cfg.get("holo_chains") or cfg.get("chains")
    st = prody.parsePDB(cfg["holo_pdb"], compressed=False).select(
        " or ".join(f"chain {c}" for c in ch))
    holo.ligand_groups = ligand_groups_from_atomgroup(st)
    hac, hasi = protein_heavy_atoms_by_residue(st, ch, holo.resnums)
    # `functional_indices`/`holo_pocket_mask` return indices in the array whose
    # heavy-atom index they were given. The register's incumbent targets have
    # matching apo/holo residue arrays, so passing holo's is harmless there. For
    # a candidate pair whose apo and holo differ in length it is not: holo-space
    # indices overrun the apo-sized mask (observed: GLUR2_TRU, index 258 into a
    # 258-long array). Attach the heavy-atom refinement only when the two arrays
    # correspond; otherwise fall back to the Calpha-only approximation
    # `build_labels` already documents, and record that we did.
    holo._heavy_atom_attached = False
    return holo, hac, hasi


def leg_a(name: str) -> dict:
    """Floor + H_new/CTQW + dcc_low, apo-side, against the pocket label."""
    cfg = _CANDIDATES[name]
    apo = clean_from_config(name, role="apo")
    holo, hac, hasi = _attach_holo_extras(clean_from_config(name, role="holo"), cfg)
    same_len = len(holo.resnums) == len(apo.resnums)
    if same_len:
        holo.heavy_atom_coords, holo.heavy_atom_seq_index = hac, hasi
        holo._heavy_atom_attached = True
    from allostery.labels import functional_indices
    _heavy_atom_coords = getattr(holo, "heavy_atom_coords", None)
    _, provenance = functional_indices(
        apo.coords, holo.ligand_groups, cfg, cutoff=cfg["pocket_contact_cutoff"],
        heavy_atom_coords=_heavy_atom_coords,
        heavy_atom_seq_index=getattr(holo, "heavy_atom_seq_index", None),
        heavy_atom_resnames=(holo.resnames if _heavy_atom_coords is not None else None),
        coords_resnames=(apo.resnames if _heavy_atom_coords is not None else None))
    seed_is_real = "fallback" not in str(provenance).lower()
    labels = build_labels(apo, holo, cfg, cutoff=cfg["pocket_contact_cutoff"])
    if labels.pocket is None or not labels.pocket.any():
        return {"error": "no resolvable pocket label on apo numbering"}
    y = labels.pocket.astype(int)

    seed = np.where(labels.active_site)[0] if labels.active_site is not None else np.array([], dtype=int)
    coords, cut = apo.coords, float(cfg["enm_cutoff"])

    floors = {
        "degree": degree_centrality(coords, cutoff=cut),
        "euclid_from_seed": euclid_from_seed_centroid(coords, seed) if len(seed) else None,
        "hop_from_seed": hop_from_seed(coords, seed, cutoff=cut) if len(seed) else None,
    }
    mask = np.ones(len(coords), dtype=bool)
    if len(seed):
        mask[seed] = False
    floor_aucs = {k: float(auc(v[mask], y[mask])) for k, v in floors.items() if v is not None}
    max_floor = max(floor_aucs.values()) if floor_aucs else float("nan")

    out = {"n_residues": int(len(coords)), "n_pocket": int(y.sum()),
           "n_active_site": int(len(seed)), "active_site_provenance": str(provenance),
           "seed_is_real": bool(seed_is_real), "floor_aucs": floor_aucs,
           "max_floor": max_floor,
           "heavy_atom_refinement": bool(getattr(holo, "_heavy_atom_attached", False)),
           "apo_holo_same_length": bool(same_len)}

    if not seed_is_real:
        out["dcc_low_k10"] = None
        out["ctqw_converged"] = None
        out["seed_note"] = (
            f"active-site provenance = {provenance!r}. No functional ligand in the holo "
            "entry, so `functional_indices` fell back to the top-degree residues -- a "
            "topological proxy, NOT a real active site. Every active-site-seeded "
            "observable is therefore N/A here, and would additionally be circular: the "
            "seed IS the top-degree set, which `degree_centrality` also supplies to the "
            "floor.")
        return out

    try:
        out["dcc_low_k10"] = float(auc(dcc_low(coords, seed, cutoff=cut, k_modes=10)[mask], y[mask]))
    except Exception as exc:  # noqa: BLE001
        out["dcc_low_k10"] = f"error: {exc!r}"

    if len(seed) == 0:
        out["ctqw_converged"] = None
        out["seed_note"] = ("no functional ligand in the holo entry -> no active site derivable; "
                            "active-site-seeded observables are N/A for this target")
    else:
        try:
            H = build_H_new(coords, apo.bfactors, cutoff=cut)
            occ = time_averaged_ctqw_converged(H, source=seed, coherent=False)
            out["ctqw_converged"] = float(auc(occ[mask], y[mask]))
        except Exception as exc:  # noqa: BLE001
            out["ctqw_converged"] = f"error: {exc!r}"
    return out


def leg_b(name: str) -> dict:
    """TASK-0213's budget on TASK-0210's solver, unchanged."""
    import task0210_coupled_search as T210
    T210.load_target_config = _load_with_candidates
    T210.RESTARTS, T210.ITERATIONS = 20, 25
    T210.COOL_RATE = (T210.T_END / T210.T_START) ** (1.0 / 24)
    return T210.run_target(name, {})


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    res = {}
    for n in TARGETS:
        res[n] = {"tier": _CANDIDATES[n].get("tier")}
        if which in ("a", "both"):
            _log(f"{n}: leg A (observables)")
            try:
                res[n]["leg_a"] = leg_a(n)
            except Exception as exc:  # noqa: BLE001
                import traceback; traceback.print_exc()
                res[n]["leg_a"] = {"error": repr(exc)}
        if which in ("b", "both"):
            _log(f"{n}: leg B (coupled search, 20x25)")
            try:
                res[n]["leg_b"] = leg_b(n)
            except Exception as exc:  # noqa: BLE001
                import traceback; traceback.print_exc()
                res[n]["leg_b"] = {"error": repr(exc)}
        (OUT_DIR / "results.json").write_text(json.dumps(res, indent=1, default=str))
    _log("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
