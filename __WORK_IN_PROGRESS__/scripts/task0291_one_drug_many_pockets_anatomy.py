"""TASK-0291 -- one drug, several "pockets": sequence strips, distinct
cavities, or fpocket splitting one cavity?

User question, from a collaborator's output showing one drug's contact
residues categorised into several separate pockets. The analogy offered:
a noodle wrapped around a meatball -- one ball, but on unwinding the
noodle you see several separate sauce strips.

Three mechanisms could produce "several pockets around one drug", and
they are NOT the same thing:

  (a) SEQUENCE STRIPS (the noodle analogy). One physical cavity, lined by
      residues from several sequence-distant segments. Universal in
      folded proteins and not an artifact of anything.
  (b) FPOCKET SPLITTING. One physical cavity, cut into several numbered
      pockets by alpha-sphere clustering. A software artifact.
  (c) GENUINELY SEPARATE CAVITIES. An elongated ligand bridging two or
      more real subpockets.

They are separated by two independent measurements per target:
  n_seq_segments      -- contiguous runs of resnums in the drug-contact
                         set (counted per chain).  High => (a).
  n_spatial_components-- connected components of those same residues in
                         the Ca contact graph. 1 => one physical cavity,
                         so (a) or (b); >1 => (c).
  n_fpocket_overlap   -- how many fpocket candidates share >=1 residue
                         with the drug-contact set.  >1 with a single
                         spatial component => (b).

NOTE ON THE ACTIVE-SITE DEFECT ([[TASK-0289]]): this analysis uses the
RAW drug-contact set, BEFORE the active-site subtraction. It therefore
never calls `detect_active_site` and is completely immune to that
non-determinism -- unlike every `min_A`-based result in this register.

Run: ../.venv/bin/python3 scripts/task0291_one_drug_many_pockets_anatomy.py
"""
import sys, json, warnings, tempfile
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0, 'src'); sys.path.insert(0, 'scripts')
import prody; prody.confProDy(verbosity="none")
from task0255_hop_angstrom_calibration import _parsePDB_all_altloc
prody.parsePDB = _parsePDB_all_altloc
import yaml
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
import task0242_two_stage_dryrun as t0242
from task0242_two_stage_dryrun import CAND
from allostery.clean import clean_from_config
from allostery.labels import (holo_pocket_mask, ligand_groups_from_atomgroup,
                              protein_heavy_atoms_by_residue)
from allostery.hamiltonians import contact_matrix
CAND.update(yaml.safe_load(open('config/candidate_targets_task0243.yaml'))['targets'])

OUT = Path("results/tasks/0291_one_drug_many_pockets")
TAX = [r['target'] for r in json.load(open(
    'results/tasks/0258_allosteric_distance_taxonomy/pocket_taxonomy.json'))
    if 'error' not in r]


def drug_contacts(t):
    """The RAW drug-contact residue set on the apo frame. No active-site
    call anywhere in this path."""
    cfg = dict(CAND[t]) if t in CAND else dict(t0242._o(t))
    apo = clean_from_config(t, role="apo")
    holo = clean_from_config(t, role="holo")
    ch = cfg.get("holo_chains") or cfg.get("chains")
    st = prody.parsePDB(cfg["holo_pdb"], compressed=False).select(
        " or ".join(f"chain {c}" for c in ch))
    holo.ligand_groups = ligand_groups_from_atomgroup(st)
    holo.heavy_atom_coords, holo.heavy_atom_seq_index = \
        protein_heavy_atoms_by_residue(st, ch, holo.resnums)
    raw = holo_pocket_mask(apo, holo, cfg["drug_ligand"],
                           cutoff=float(cfg.get("pocket_contact_cutoff", 4.5)))
    return cfg, apo, raw


def n_segments(resnums, chains):
    """Contiguous runs of residue numbers, counted within each chain."""
    n = 0
    for c in sorted(set(chains)):
        rs = sorted(int(r) for r, cc in zip(resnums, chains) if cc == c)
        if not rs:
            continue
        n += 1 + sum(1 for a, b in zip(rs, rs[1:]) if b - a > 1)
    return n


def main():
    rows = []
    print(f"  {'target':<22}{'n_res':>6}{'seq segs':>9}{'spatial':>8}"
          f"{'fpockets':>9}{'best cov':>9}")
    for t in TAX:
        try:
            cfg, apo, raw = drug_contacts(t)
            ii = np.where(raw)[0]
            if len(ii) == 0:
                print(f"  [skip] {t}: empty drug-contact set"); continue
            resn = np.asarray(apo.resnums); chid = np.asarray(apo.chain_ids)
            cut = float(cfg.get("enm_cutoff", 8.0))
            A = contact_matrix(apo.coords, cutoff=cut, weight="binary")
            ncomp, _ = connected_components(csr_matrix(A[np.ix_(ii, ii)]),
                                            directed=False)
            nseg = n_segments(resn[ii], chid[ii])
            # how many fpocket candidates touch this one drug's contact set?
            apo_ch = cfg.get("apo_chains") or cfg.get("chains")
            with tempfile.TemporaryDirectory() as tmp:
                tmp = Path(tmp)
                ag = prody.parsePDB(cfg["apo_pdb"], compressed=False).select(
                    "protein and (" + " or ".join(f"chain {c}" for c in apo_ch) + ")")
                pdb = tmp / f"{t.lower()}.pdb"
                prody.writePDB(str(pdb), ag)
                pk = t0242.fpocket_candidates(pdb, tmp)
            novl, best = np.nan, np.nan
            if not isinstance(pk, dict):
                # TASK-0298: (chain, resnum) compound key, matching
                # fpocket_candidates' own now-corrected `p["resnums"]`
                # shape -- this target set includes several of the 9
                # exposed to the chain-collision bug (GAC_BPTES/CPD12,
                # PKR_MITAPIVAT/AG946, PF_ATCASE, FBPASE_95S, SUMO_E1_FHJ,
                # TRP_SYNTHASE_F6F/F19).
                want = set(zip(chid[ii].tolist(), (int(r) for r in resn[ii])))
                ovl = [len(want & p["resnums"]) for p in pk]
                novl = int(sum(1 for o in ovl if o > 0))
                best = float(max(ovl) / len(want)) if ovl else 0.0
            rows.append(dict(target=t, n_res=int(len(ii)), n_seq_segments=int(nseg),
                             n_spatial_components=int(ncomp),
                             n_fpocket_overlapping=novl, best_fpocket_coverage=best))
            print(f"  {t:<22}{len(ii):>6}{nseg:>9}{ncomp:>8}"
                  f"{novl:>9}{best:>9.2f}")
        except Exception as ex:
            print(f"  [skip] {t}: {type(ex).__name__}: {ex}")

    seg = np.array([r['n_seq_segments'] for r in rows], float)
    comp = np.array([r['n_spatial_components'] for r in rows], float)
    fp = np.array([r['n_fpocket_overlapping'] for r in rows], float)
    cov = np.array([r['best_fpocket_coverage'] for r in rows], float)
    print("\n" + "=" * 66)
    print(f"  n = {len(rows)} targets, one drug each")
    print("=" * 66)
    print(f"  sequence segments per drug site : median {np.median(seg):.0f}"
          f"  range {seg.min():.0f}-{seg.max():.0f}")
    print(f"  spatial components per drug site: median {np.median(comp):.0f}"
          f"  range {comp.min():.0f}-{comp.max():.0f}")
    print(f"    single connected cavity : {int((comp==1).sum())}/{len(rows)}")
    print(f"  fpocket candidates touching one drug site: median "
          f"{np.nanmedian(fp):.0f}  range {np.nanmin(fp):.0f}-{np.nanmax(fp):.0f}")
    print(f"  best single fpocket covers: median {np.nanmedian(cov):.2f}"
          f" of the drug's contacts")
    one_cav_many_fp = int(((comp == 1) & (fp > 1)).sum())
    print(f"\n  (a) sequence strips, one cavity : {int((comp==1).sum())}"
          f"/{len(rows)} targets have exactly ONE spatial component")
    print(f"  (c) genuinely separate cavities : {int((comp>1).sum())}/{len(rows)}")
    print(f"  (b) fpocket splits one cavity   : {one_cav_many_fp}/{len(rows)}"
          f" have 1 cavity but >1 fpocket candidate on it")
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(dict(rows=rows, n=len(rows),
                   single_cavity=int((comp == 1).sum()),
                   multi_cavity=int((comp > 1).sum()),
                   one_cavity_many_fpockets=one_cav_many_fp),
              open(OUT / "one_drug_many_pockets.json", "w"), indent=1)
    print(f"\n  written -> {OUT}/one_drug_many_pockets.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
