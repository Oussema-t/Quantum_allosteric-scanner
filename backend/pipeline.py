"""
Data-view orchestrator (no quantum — data foundation only).

Loads a protein structure (optionally completing its missing residues from a holo),
tags the active-site residues, and returns the per-residue payload the 3D viewer
needs: coordinates come from the PDB file the browser fetches; here we provide the
residue-level annotations (chain, B-factor, active-site flag, modeled flag).

Quantum allosteric prediction is intentionally NOT part of this layer yet; it will
be reintroduced on top of this data foundation later.
"""
import numpy as np

from .data_layer import load_structure, coarse_grain, sources_from_resnums
from .systems import resolve_systems


def build_view(pdb_id, chains="A", source_residues=None, target_name=None,
               complete=False, holo_pdb=None, holo_chain=None, coarse_k=1):
    """Load a structure for visualization.

    Returns a JSON-serializable dict with the per-residue annotations, the resolved
    active site, and (if completion was requested) a summary of the filled residues.
    """
    systems = resolve_systems()
    cfg = systems.get(target_name) if target_name else None

    # optionally complete the apo (fill missing residues from holo + interpolation)
    completion = None
    if complete:
        from .discovery import complete_apo
        use_holo = holo_pdb or (cfg.get("holo") if cfg else None)
        use_holo_chain = holo_chain or (cfg.get("chain") if cfg else None) or chains
        if not use_holo:
            raise ValueError("completion requested but no holo structure available")
        st, completion = complete_apo(pdb_id, chains, use_holo, use_holo_chain)
    else:
        st = load_structure(pdb_id, chains)
        if st is None:
            raise ValueError(f"could not load structure {pdb_id} (chains {chains})")
        if coarse_k > 1:
            st = coarse_grain(st, coarse_k)
    modeled = st.get("modeled")

    # resolve the active site: explicit residues > benchmark metadata > auto-detect
    src_source, src_detail = "none", None
    if source_residues:
        src_resnums = list(source_residues)
        src_source, src_detail = "manual", "entered by user"
    elif cfg is not None:
        src_resnums = list(cfg["catalytic"])
        src_source = "benchmark"
        src_detail = f"validated literature active site ({cfg.get('site_name') or 'benchmark'})"
    else:
        from .active_site import detect_active_site
        det = detect_active_site(pdb_id, chains,
                                 holo_pdb=(holo_pdb if complete else None))
        src_resnums = det["active_site"]
        src_source, src_detail = det["source"], det["detail"]
    src_idx = sources_from_resnums(st, src_resnums) if src_resnums else np.array([], int)
    src_set = set(int(st["resnums"][i]) for i in src_idx)

    # B-factor normalization (0..1) for the "color by flexibility" view
    b = st["bfac"]
    bmin, bmax = float(b.min()), float(b.max())
    span = (bmax - bmin) or 1.0

    residues = [
        {
            "resnum": int(st["resnums"][i]),
            "chain": str(st["chains"][i]),
            "bfactor": round(float(st["bfac"][i]), 2),
            "bnorm": round((float(st["bfac"][i]) - bmin) / span, 4),
            "is_source": int(st["resnums"][i]) in src_set,
            "modeled": bool(modeled[i]) if modeled is not None else False,
        }
        for i in range(len(st["resnums"]))
    ]

    # GNM site-potential analysis (structure-based descriptors), per protein
    analysis = None
    if len(st["resnums"]) <= 1500:
        try:
            from .analysis import site_potentials
            analysis = site_potentials(st["coords"], st["bfac"], st["resnums"],
                                       cutoff=8.0, site_idx=src_idx)
        except Exception:
            analysis = None

    return {
        "pdb_id": pdb_id,
        "chains": chains,
        "n_residues": int(len(st["resnums"])),
        "active_site": sorted(src_set),
        "active_site_name": (cfg.get("site_name") if cfg else None),
        "active_site_source": src_source,
        "active_site_detail": src_detail,
        "analysis": analysis,
        "residues": residues,
        "completion": completion,
        "bfactor_range": [round(bmin, 2), round(bmax, 2)],
    }
