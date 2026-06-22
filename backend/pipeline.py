"""
Pipeline orchestrator — PDB id -> connectivity matrix + allosteric hit list.

This stitches the ported layers into one call: fetch a structure, build the chosen
Hamiltonian family, propagate the quantum signal from the active-site source residues,
score every residue by connectivity, and return the top-5 predicted allosteric sites
together with everything the frontend needs to render the 3D map and heatmap.
"""
import numpy as np

from .data_layer import load_structure, coarse_grain, sources_from_resnums
from .hamiltonian import build_hamiltonian
from .transport import transport_green, transport_ctqw, transport_heat
from .scoring import score_from_source, predict_residues, evaluate, spherical_labels
from .systems import resolve_systems

# default integration window for the coherent quantum walk
CTQW_TIMES = np.linspace(0.1, 20.0, 40)

PROPAGATORS = {"ctqw", "green", "heat"}


def _propagate(H, propagator, gamma):
    if propagator == "ctqw":
        return transport_ctqw(H, CTQW_TIMES)
    if propagator == "green":
        return transport_green(H, gamma)
    if propagator == "heat":
        return transport_heat(H, gamma)
    raise ValueError(f"unknown propagator: {propagator}")


def run_scan(pdb_id, chains="A", source_residues=None, family="GNM",
             propagator="ctqw", cutoff=8.0, gamma=1.0, coarse_k=1,
             top_k=5, target_name=None, pocket_mode="full"):
    """Run a single-structure allosteric scan.

    Parameters
    ----------
    pdb_id          : RCSB id to fetch (e.g. "4OBE").
    chains          : comma-separated chain ids to include.
    source_residues : list of active-site residue NUMBERS to seed signal from.
                      If None and `target_name` is a known benchmark, its active
                      site is used automatically.
    family          : Hamiltonian family (see hamiltonian.FAMILIES).
    propagator      : "ctqw" | "green" | "heat".
    cutoff          : contact cutoff (Angstrom).
    gamma           : broadening / diffusion time for green / heat.
    coarse_k        : keep every k-th residue (1 = full resolution).
    top_k           : number of predicted sites to return.
    target_name     : optional benchmark key (enables auto source + validation).
    pocket_mode     : "full" | "distal" — which validated pocket to score against.

    Returns a JSON-serializable dict.
    """
    systems = resolve_systems(pocket_mode=pocket_mode)
    cfg = systems.get(target_name) if target_name else None

    st = load_structure(pdb_id, chains)
    if st is None:
        raise ValueError(f"could not load structure {pdb_id} (chains {chains})")
    if coarse_k > 1:
        st = coarse_grain(st, coarse_k)

    # resolve the signal source (active site)
    if source_residues:
        src_resnums = list(source_residues)
    elif cfg is not None:
        src_resnums = list(cfg["catalytic"])
    else:
        src_resnums = []
    src_idx = sources_from_resnums(st, src_resnums) if src_resnums else np.array([], int)
    if len(src_idx) == 0:
        # no active site given: seed from the most-connected residue (degree hub)
        from .hamiltonian import contact_weight
        deg = (contact_weight(st["coords"], cutoff) > 0).sum(1)
        src_idx = np.array([int(np.argmax(deg))])

    # build Hamiltonian and propagate the quantum signal
    p = {"cutoff": cutoff, "power": 1.0}
    H = build_hamiltonian(st["coords"], st["bfac"], family, p)
    C = _propagate(H, propagator, gamma)

    scores = score_from_source(C, src_idx)
    top_res, top_order = predict_residues(st, scores, k=top_k)

    # optional validation against a known pocket
    metrics = None
    pocket_resnums = []
    if cfg is not None and cfg.get("lit_pocket"):
        pocket_resnums = [r for r in cfg["lit_pocket"] if r in set(st["resnums"].tolist())]
        pocket_idx = np.where(np.isin(st["resnums"], pocket_resnums))[0]
        if len(pocket_idx):
            m, _, _ = evaluate(scores, st["coords"], pocket_idx, tol=6.0, k=top_k)
            metrics = {k: (None if not np.isfinite(v) else round(float(v), 4))
                       for k, v in m.items() if k != "top_hit_idx"}

    # assemble per-residue payload (finite scores normalized to 0..1 for coloring)
    finite = scores[np.isfinite(scores)]
    smin, smax = (float(finite.min()), float(finite.max())) if finite.size else (0.0, 1.0)
    span = (smax - smin) or 1.0

    def norm(v):
        return 0.0 if not np.isfinite(v) else round((float(v) - smin) / span, 4)

    src_set = set(int(st["resnums"][i]) for i in src_idx)
    residues = [
        {
            "resnum": int(st["resnums"][i]),
            "chain": str(st["chains"][i]),
            "score": (None if not np.isfinite(scores[i]) else round(float(scores[i]), 6)),
            "norm": norm(scores[i]),
            "bfactor": round(float(st["bfac"][i]), 2),
            "is_source": int(st["resnums"][i]) in src_set,
        }
        for i in range(len(st["resnums"]))
    ]

    return {
        "pdb_id": pdb_id,
        "chains": chains,
        "n_residues": int(len(st["resnums"])),
        "family": family,
        "propagator": propagator,
        "cutoff": cutoff,
        "source_residues": sorted(src_set),
        "top_hits": top_res,
        "residues": residues,
        "connectivity_matrix": np.round(C, 6).tolist(),
        "resnum_axis": [int(r) for r in st["resnums"]],
        "validation": (
            {"target": target_name,
             "site_name": cfg.get("site_name"),
             "known_pocket": pocket_resnums,
             "known_top5": cfg.get("top5_holo"),
             "metrics": metrics}
            if cfg is not None else None
        ),
    }
