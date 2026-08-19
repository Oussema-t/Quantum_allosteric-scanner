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

from .data_layer import load_structure, coarse_grain, sources_from_resnums, fetch
from .systems import resolve_systems


def structure_to_pdb_text(st, pdb_id, completion=None):
    """Serialize the visualized structure (Cα) as PDB text, with MODELED (filled)
    residues flagged distinctly: occupancy=0.00, B-factor=999.00, plus REMARK 470
    lines listing their residue numbers — so they're spottable in PyMOL/3Dmol by
    coloring on the occupancy / B-factor column."""
    from Bio.PDB import PDBParser
    # real residue names for resolved residues, from the source file
    resname = {}
    fp = fetch(pdb_id)
    if fp:
        try:
            s = PDBParser(QUIET=True).get_structure(pdb_id, fp)
            for ch in s[0]:
                for r in ch:
                    if r.id[0] == " ":
                        resname[(ch.id, r.id[1])] = (r.get_resname().strip()[:3] or "UNK")
        except Exception:
            pass
    # names for filled residues come from the completion report
    if completion:
        for f in completion.get("filled", []) or []:
            resname.setdefault((None, int(f["resnum"])), (f.get("resname") or "UNK")[:3])

    modeled = st.get("modeled")
    resnums, coords, chains, bfac = st["resnums"], st["coords"], st["chains"], st["bfac"]
    modeled_nums = [int(resnums[i]) for i in range(len(resnums))
                    if modeled is not None and bool(modeled[i])]

    lines = ["REMARK   1 STRUCTURE AS VISUALIZED BY QUANTUM ALLOSTERIC SCANNER",
             "REMARK   1 MODELED (FILLED) RESIDUES FLAGGED: occupancy=0.00 B-factor=999.00"]
    if modeled_nums:
        ml = ", ".join(str(x) for x in modeled_nums)
        for i in range(0, len(ml), 60):
            lines.append("REMARK 470 MODELED RESIDUES: " + ml[i:i + 60])

    serial = 1
    for i in range(len(resnums)):
        rn, ch = int(resnums[i]), str(chains[i])[:1] or "A"
        x, y, z = float(coords[i][0]), float(coords[i][1]), float(coords[i][2])
        rname = resname.get((ch, rn)) or resname.get((None, rn)) or "UNK"
        is_mod = modeled is not None and bool(modeled[i])
        occ = 0.00 if is_mod else 1.00
        b = 999.00 if is_mod else round(float(bfac[i]), 2)
        lines.append(
            f"ATOM  {serial:>5d}  CA  {rname:>3s} {ch}{rn:>4d}    "
            f"{x:8.3f}{y:8.3f}{z:8.3f}{occ:6.2f}{b:6.2f}           C")
        serial += 1
    lines.append("END")
    return "\n".join(lines) + "\n"


def build_view(pdb_id, chains="A", source_residues=None, target_name=None,
               complete=False, holo_pdb=None, holo_chain=None, coarse_k=1,
               cutoff=8.0, active_site_mode="benchmark"):
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
        use_holo_chain = holo_chain or (cfg.get("holo_chain") if cfg else None) or chains
        if not use_holo:
            raise ValueError("completion requested but no holo structure available")
        st, completion = complete_apo(pdb_id, chains, use_holo, use_holo_chain)
    else:
        st = load_structure(pdb_id, chains)
        if st is None:
            # distinguish "no such chain" (tell the user which chains exist) from
            # "could not fetch the entry at all"
            from .rcsb import chain_summary
            avail = [c["chain"] for c in chain_summary(pdb_id)]
            if avail:
                raise ValueError(
                    f"chain(s) '{chains}' not found in {pdb_id}. "
                    f"Available chains: {', '.join(avail)}")
            raise ValueError(f"could not load {pdb_id} from RCSB — check the PDB ID")
        if coarse_k > 1:
            st = coarse_grain(st, coarse_k)
    modeled = st.get("modeled")

    # resolve the active site: explicit residues > benchmark metadata > auto-detect.
    # active_site_mode="auto" forces UniProt auto-detection even for benchmark targets
    # (so the detector can be validated against the curated values).
    src_source, src_detail = "none", None
    use_benchmark = (cfg is not None and active_site_mode != "auto")
    if source_residues:
        src_resnums = list(source_residues)
        src_source, src_detail = "manual", "entered by user"
    elif use_benchmark:
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
                                       cutoff=cutoff, site_idx=src_idx)
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
        "pdb_text": structure_to_pdb_text(st, pdb_id, completion),
    }
