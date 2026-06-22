"""
apo <-> holo conformational comparison.

Superimposes the holo (drug-bound) structure onto the apo (unbound) structure on
their common Cα atoms (Kabsch / least-squares), then reports how far each residue's
Cα moves when the drug binds. The browser overlays both structures (now in the same
coordinate frame) and colors the holo by per-residue displacement, so a biologist can
literally see the drug pushing the residues around.
"""
import io

import numpy as np

from .data_layer import fetch


def _structure(pdb):
    from Bio.PDB import PDBParser
    fp = fetch(pdb)
    if fp is None:
        raise ValueError(f"could not fetch structure {pdb}")
    return PDBParser(QUIET=True).get_structure(pdb, fp)


def _ca_map(model, chain_id):
    """resnum -> CA atom for the first matching chain."""
    out = {}
    try:
        chain = model[chain_id]
    except KeyError:
        # fall back to the first chain present
        chain = next(iter(model))
    for res in chain:
        if res.id[0] == " " and "CA" in res:
            out[res.id[1]] = res["CA"]
    return out


def align_and_compare(apo_pdb, apo_chain, holo_pdb, holo_chain=None):
    """Align holo onto apo and compute per-residue Cα displacement."""
    from Bio.PDB import Superimposer, PDBIO

    apo_s = _structure(apo_pdb)
    holo_s = _structure(holo_pdb)
    apo_m, holo_m = apo_s[0], holo_s[0]
    ac = apo_chain.split(",")[0].strip()
    hc = (holo_chain or apo_chain).split(",")[0].strip()

    apo_ca = _ca_map(apo_m, ac)
    holo_ca = _ca_map(holo_m, hc)
    common = sorted(set(apo_ca) & set(holo_ca))
    if len(common) < 3:
        raise ValueError(
            f"only {len(common)} common residues between {apo_pdb}/{ac} and "
            f"{holo_pdb}/{hc} — cannot align (different numbering or chains).")

    fixed = [apo_ca[r] for r in common]    # apo stays put
    moving = [holo_ca[r] for r in common]  # holo is rotated/translated onto apo
    sup = Superimposer()
    sup.set_atoms(fixed, moving)
    sup.apply(list(holo_m.get_atoms()))    # transform ALL holo atoms into apo frame

    # per-residue Cα displacement after superposition
    disp = []
    for r in common:
        d = float(np.linalg.norm(apo_ca[r].get_coord() - holo_ca[r].get_coord()))
        disp.append({"resnum": r, "disp": round(d, 3)})
    max_disp = max((d["disp"] for d in disp), default=0.0)

    from Bio.PDB import Select

    class _ChainOnly(Select):
        def __init__(self, ch):
            self.ch = ch

        def accept_chain(self, chain):
            return chain.id == self.ch

    def to_text(structure, keep_chain):
        out = PDBIO()
        out.set_structure(structure)
        buf = io.StringIO()
        out.save(buf, _ChainOnly(keep_chain))
        return buf.getvalue()

    return {
        "apo_pdb": apo_pdb,
        "holo_pdb": holo_pdb,
        "apo_chain": ac,
        "holo_chain": hc,
        "rmsd": round(float(sup.rms), 3),
        "n_aligned": len(common),
        "max_disp": round(max_disp, 3),
        "displacements": disp,
        "apo_text": to_text(apo_s, ac),
        "holo_text_aligned": to_text(holo_s, hc),
    }
