"""
Validation layer (notebook §7 / frozen-vs-live pocket validator).

The benchmark protocol: the apo (unbound) structure is the blind input; the holo
(drug-bound) structure is ground truth. We re-derive each target's pocket directly
from the real holo PDB every run — the residues actually in contact with the bound
drug — and check predictions against it. This proves the frozen SYSTEMS pocket lists
still match the live structures, and lets us score the apo-only quantum prediction
against an independently re-derived ground truth.
"""
import numpy as np
from scipy.spatial.distance import cdist

from .data_layer import fetch, load_structure
from .scoring import spherical_labels

CONTACT_CUTOFF = 4.5   # Angstrom; matches the frozen pocket_full[4.5] definition


def live_drug_contacts(pdb_id, chain, lig_code, cutoff=CONTACT_CUTOFF):
    """Protein residues with any atom within `cutoff` A of any `lig_code` atom,
    re-derived from the real holo PDB. Returns sorted residue numbers, or None."""
    from Bio.PDB import PDBParser
    if not pdb_id or not lig_code:
        return None
    fp = fetch(pdb_id)
    if fp is None:
        return None
    s = PDBParser(QUIET=True).get_structure(pdb_id, fp)[0]
    lig = [a.get_coord() for ch in s for r in ch
           if r.get_resname().strip() == lig_code and r.id[0] != ' ' for a in r]
    if not lig:
        return None
    lig = np.array(lig, float)
    try:
        prot = s[chain]
    except KeyError:
        prot = next(iter(s))
    hits = []
    for r in prot:
        if r.id[0] != ' ':
            continue
        xyz = np.array([a.get_coord() for a in r], float)
        if len(xyz) and cdist(xyz, lig).min() <= cutoff:
            hits.append(int(r.id[1]))
    return sorted(hits)


def jaccard(a, b):
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / max(1, len(sa | sb))


def validate_target(cfg, scan_result):
    """Compare a completed apo scan against the holo-derived ground-truth pocket.

    cfg          : resolved SYSTEMS entry (has holo, holo_ligand, chain, lit_pocket,
                   top5_holo, pocket_full).
    scan_result  : the dict returned by pipeline.run_scan for the apo structure.

    Returns a JSON-serializable validation report (None if no holo/ligand to score).
    """
    holo = cfg.get("holo")
    lig = cfg.get("holo_ligand")
    chain = cfg.get("chain", "A")
    frozen_top5 = cfg.get("top5_holo") or []
    frozen_pocket = cfg.get("lit_pocket") or []

    report = {
        "holo": holo,
        "holo_challenge": cfg.get("holo_challenge"),
        "holo_ligand": lig,
        "holo_ligand_name": cfg.get("holo_ligand_name"),
        "site_name": cfg.get("site_name"),
        "frozen_pocket": frozen_pocket,
        "frozen_top5": frozen_top5,
        "contact_cutoff": CONTACT_CUTOFF,
    }

    # re-derive the live drug-contact pocket from the real holo structure
    live = live_drug_contacts(holo, chain, lig) if (holo and lig) else None
    report["live_pocket"] = live
    if live is not None and frozen_pocket:
        report["frozen_vs_live_jaccard"] = round(jaccard(frozen_pocket, live), 3)
        report["in_frozen_not_live"] = sorted(set(frozen_pocket) - set(live))
        report["in_live_not_frozen"] = sorted(set(live) - set(frozen_pocket))

    # which predicted hits fall inside each ground-truth pocket
    pred = scan_result.get("top_hits", [])
    gt = set(live) if live else set(frozen_pocket)
    report["predicted_hits"] = pred
    report["hits_in_pocket"] = sorted(set(pred) & gt)
    report["hit_recovery"] = (
        round(len(set(pred) & gt) / len(pred), 3) if pred else None)
    report["top5_recovered"] = sorted(set(pred) & set(frozen_top5))

    # carry through the metrics computed during the scan (AUC / P@5 vs frozen pocket)
    if scan_result.get("validation"):
        report["scan_metrics"] = scan_result["validation"].get("metrics")

    return report


def score_against_live(scan_result, apo_struct, live_pocket, tol=6.0, k=5):
    """Re-score the apo prediction's per-residue scores against the LIVE pocket
    (independent of the frozen lists). Returns AUC / P@k."""
    from sklearn.metrics import roc_auc_score
    resnums = np.array(scan_result["resnum_axis"], int)
    scores = np.array([r["score"] if r["score"] is not None else -np.inf
                       for r in scan_result["residues"]], float)
    coords = apo_struct["coords"]
    pocket_idx = np.where(np.isin(resnums, list(live_pocket)))[0]
    if len(pocket_idx) == 0:
        return None
    lab = spherical_labels(coords, pocket_idx, tol)
    m = np.isfinite(scores)
    order = np.argsort(scores)[::-1]
    auc = (roc_auc_score(lab[m], scores[m])
           if (m.sum() > 1 and len(np.unique(lab[m])) > 1) else 0.5)
    return {
        "auc_vs_live": round(float(auc), 4),
        "p@5_vs_live": round(float(lab[order[:5]].sum() / 5.0), 4),
        "p@10_vs_live": round(float(lab[order[:10]].sum() / 10.0), 4),
    }
