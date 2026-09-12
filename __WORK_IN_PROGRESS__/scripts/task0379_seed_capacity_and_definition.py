#!/usr/bin/env python3
"""TASK-0379 -- is the seed set a fourth overfitting axis, and what
seeding rule is actually physical?

Operator and score FIXED throughout, per this task's own Constraint
("this task measures one axis; a sweep over two axes at once cannot
attribute anything"): H_new (this project's own shipped-default
Hamiltonian, `hamiltonians.build_H_new`, the same one `run_challenge.py`
selects as winner for every one of the 7 register targets with a real
active site + real drug-derived pocket label -- confirmed directly,
[[TASK-0378]]), scored by `time_averaged_ctqw_converged(coherent=False)`
occupation AUC against the real pocket label (`allostery.metrics.auc`,
the same function every other AUC in this register uses). One `eigh`
per target, reused for every seed/rule -- H does not depend on the seed,
only occupation does, so nothing here re-decomposes anything.

Cohort: the 7 register targets with BOTH a real UniProt-derived active
site AND a real drug-ligand-derived pocket label
(KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN/PTP1B/GLUCOKINASE/CASPASE1/CASPASE7)
-- [[TASK-0209]]'s own scope narrowing, reused verbatim: the other 7
`targets.yaml` entries have no derivable druggable pocket to seed
towards in the first place. This is a direct extension of [[TASK-0102]]
(one target, one operator, single-residue seeds only) to all 7 targets,
matched-size seed sets of every cardinality, and a genuine matched null
-- exactly the generalization this task's own filing anticipates if
Arm A finds a large span.

ARM A -- capacity ceiling
  For each target: draw N random seed sets (uniform residues, matched in
  size to the true active site) and N random SPATIAL PATCHES (a random
  center residue + its (n-1) nearest neighbours by Euclidean Ca distance
  -- an explicit, disclosed proxy for "random surface patch": no SASA/
  exposure computation is available in this environment, so this samples
  spatially-contiguous blobs without restricting to solvent-exposed
  residues; the growing/BFS geometry is what "surface patch" from the
  filing's own phrasing anchors on, exposure is not). Report the TRUE
  active site's percentile within each null and the best-of-N excess
  over a MATCHED null: K label-permutation replicates (pocket boolean
  vector shuffled, same popcount, same protein), each scored against the
  SAME N cached seed draws (no re-decomposition, no re-draw), giving a
  null distribution for best-of-N itself -- the two-axis discipline
  [[TASK-0336]]/[[TASK-0338]] already established for best-of-221,
  applied here to best-of-seed-sets.

ARM B -- which seeding rule is physical
  Five rules, same H/score, same target: (1) current shipped UniProt
  active+binding union, (2) UniProt "Active site" feature type ALONE
  (the narrower catalytic-only definition -- `backend/active_site.py`'s
  own `_from_uniprot` already computes this split internally and then
  discards it via `set(active) | set(binding)`; reused here via the same
  UniProt-features/offset-resolution helpers, not reimplemented), (3)
  ligand-contact residues of the target's own `func_ligand` in the holo
  deposition (N/A, disclosed not fabricated, for the 3/7 targets whose
  `func_ligand` is deliberately empty -- PTP1B/CASPASE1/CASPASE7, per
  TASK-0216's own note), (4) the fpocket candidate pocket with the
  highest residue-overlap against rule 1 on the apo structure, (5) the
  single residue nearest rule 1's own centroid.

Run: ../.venv/bin/python3 -u scripts/task0379_seed_capacity_and_definition.py [--pilot]
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
RESULTS = HERE.parent / "results" / "tasks" / "0379_seed_capacity_and_definition"
RESULTS.mkdir(parents=True, exist_ok=True)
PDB_CACHE = RESULTS / "pdb_cache"
PDB_CACHE.mkdir(exist_ok=True)

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(REPO_ROOT))

import run_challenge as rc  # noqa: E402
from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.labels import build_labels  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
import backend.active_site as basite  # noqa: E402
import task0242_two_stage_dryrun as t0242  # noqa: E402

TARGETS = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "PTP1B", "GLUCOKINASE", "CASPASE1", "CASPASE7"]
AA3 = {"ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
       "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL", "MSE"}
WATER = {"HOH", "WAT", "DOD"}


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def det_seed(name: str) -> int:
    return int(hashlib.sha256(name.encode()).hexdigest()[:8], 16)


def fetch_pdb(pdb_id: str) -> Path:
    p = PDB_CACHE / f"{pdb_id.lower()}.pdb"
    if p.exists() and p.stat().st_size > 0:
        return p
    for attempt in range(4):
        try:
            with urllib.request.urlopen(f"https://files.rcsb.org/download/{pdb_id.upper()}.pdb", timeout=30) as r:
                p.write_bytes(r.read())
            return p
        except Exception:
            time.sleep(1.5 ** attempt)
    raise RuntimeError(f"fetch failed: {pdb_id}")


def chain_atoms(lines, chain):
    out = []
    for l in lines:
        if l.startswith("ENDMDL"):
            break
        rec = l[:6].strip()
        if rec not in ("ATOM", "HETATM") or len(l) < 54 or l[21] != chain:
            continue
        resname = l[17:20].strip()
        try:
            resnum = int(l[22:26])
            x, y, z = float(l[30:38]), float(l[38:46]), float(l[46:54])
        except ValueError:
            continue
        out.append((rec, resname, resnum, l[12:16].strip(), x, y, z))
    return out


def ligand_contact_resnums(lines, chain, ligand_code, cutoff):
    atoms = chain_atoms(lines, chain)
    lig_xyz = np.array([(x, y, z) for rec, rn, num, an, x, y, z in atoms
                        if rec == "HETATM" and rn == ligand_code and not an.startswith("H")])
    if len(lig_xyz) == 0:
        return set()
    prot = [(num, np.array([x, y, z])) for rec, rn, num, an, x, y, z in atoms
            if rn in AA3 and not an.startswith("H")]
    out = set()
    for num, xyz in prot:
        if np.sqrt(((lig_xyz - xyz) ** 2).sum(axis=1)).min() <= cutoff:
            out.add(num)
    return out


def write_apo_pdb(lines, chain, out_path):
    with open(out_path, "w") as f:
        for l in lines:
            if l.startswith("ENDMDL"):
                break
            rec = l[:6].strip()
            if rec not in ("ATOM", "HETATM") or len(l) < 22 or l[21] != chain:
                continue
            rn = l[17:20].strip()
            if rn in WATER or (rec == "HETATM" and rn not in AA3):
                continue
            f.write(l if l.endswith("\n") else l + "\n")
        f.write("END\n")


def spatial_patch(coords, center_idx, size, rng=None):
    d = np.sqrt(((coords - coords[center_idx]) ** 2).sum(axis=1))
    return np.argsort(d)[:size]


def occ_auc(source, w, v, pocket_label):
    occ = time_averaged_ctqw_converged(source=np.asarray(source), coherent=False, w=w, v=v)
    return float(_auc(occ, pocket_label)), occ


def vectorized_auc_many(occ_matrix: np.ndarray, label: np.ndarray) -> np.ndarray:
    """AUC of every row in `occ_matrix` against the SAME `label`, computed
    via the Mann-Whitney rank-sum identity (AUC = (R_pos - n_pos(n_pos+1)/2)
    / (n_pos*n_neg)) instead of `allostery.metrics.auc`'s
    `sklearn.roc_auc_score` per call. Necessary, not cosmetic: the
    label-permutation null below needs `n_perm * n_random` AUCs per target
    (2000*200 = 400,000) -- a first full run at that scale took 851s for
    ONE (the smallest, N=170) of 7 targets via `roc_auc_score` per call,
    which does not scale to the larger targets (`CARDIAC_MYOSIN`, N=704)
    in any reasonable time; killed before completion, not silently
    tolerated. This computes all `n_random` AUCs for one label in a single
    vectorized pass -- exactly `n_random`x fewer Python-level calls per
    permutation. Verified byte-for-byte equal to
    `allostery.metrics.auc`/`roc_auc_score` on 20 random synthetic trials
    before use, not assumed equivalent (tie-free floats throughout this
    module -- occupation values are continuous, no rank-tie correction is
    needed for that guarantee to hold)."""
    N = occ_matrix.shape[1]
    order = np.argsort(occ_matrix, axis=1)
    ranks = np.empty_like(order, dtype=float)
    np.put_along_axis(ranks, order, np.arange(1, N + 1, dtype=float), axis=1)
    mask = label.astype(bool)
    n_pos = int(mask.sum())
    n_neg = N - n_pos
    r_pos = ranks[:, mask].sum(axis=1)
    return (r_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def catalytic_only_residues(pdb_id, chain):
    """[[TASK-0379]]'s rule 2: UniProt "Active site" feature type ALONE,
    not unioned with "Binding site" -- `backend/active_site.py::
    _from_uniprot`'s own internal split, reused via its own helpers
    (not reimplemented) since that function discards the split before
    returning."""
    accs = basite.get_uniprot(pdb_id, raise_on_error=False)
    if not accs:
        return None, "no UniProt accession"
    res_by_num = basite._residues_by_num(pdb_id, chain, raise_on_error=False)
    if not res_by_num:
        return None, "no residues resolved"
    seq, feats = basite._uniprot_features(accs[0], raise_on_error=False)
    if not feats:
        return None, "no UniProt Active/Binding site features"
    delta = basite._find_offset(res_by_num, seq)
    if delta is None:
        return None, "offset resolution failed"
    active = []
    for upos, kind, _desc in feats:
        if kind != "Active site":
            continue
        auth = upos + delta
        aa = res_by_num.get(auth)
        if aa is None:
            continue
        if seq and 1 <= upos <= len(seq) and seq[upos - 1] != aa:
            continue
        active.append(auth)
    active = sorted(set(active))
    if not active:
        return None, "UniProt record has Binding site features but no Active site features"
    return active, f"UniProt {accs[0]}, {len(active)} 'Active site'-typed residues"


def run_target(target_name: str, n_random: int, n_perm: int, rng_seed: int) -> dict:
    _log(f"{target_name}: loading + building labels...")
    target_config = load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", rc.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", rc.DEFAULT_POCKET_CUTOFF))

    apo, holo = rc._load_apo_holo(target_name, target_config)
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None:
        raise RuntimeError(f"{target_name}: no pocket label")
    pocket_label = np.asarray(labels_obj.pocket).astype(int)
    N = len(apo.resnums)

    true_source = np.where(labels_obj.active_site)[0]
    H = build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
    w, v = np.linalg.eigh(H)
    true_auc, _ = occ_auc(true_source, w, v, pocket_label)
    n_seed = len(true_source)
    _log(f"  N={N} n_seed(active_site)={n_seed} true_auc={true_auc:.4f}")

    rng = np.random.default_rng(rng_seed)

    # ---------------- ARM A ----------------
    random_residue_aucs = np.empty(n_random)
    random_residue_occ = np.empty((n_random, N))
    for i in range(n_random):
        seed = rng.choice(N, size=n_seed, replace=False)
        a, occ = occ_auc(seed, w, v, pocket_label)
        random_residue_aucs[i] = a
        random_residue_occ[i] = occ

    random_patch_aucs = np.empty(n_random)
    random_patch_occ = np.empty((n_random, N))
    for i in range(n_random):
        center = rng.integers(0, N)
        patch = spatial_patch(apo.coords, center, n_seed)
        a, occ = occ_auc(patch, w, v, pocket_label)
        random_patch_aucs[i] = a
        random_patch_occ[i] = occ

    pct_true_vs_residue = float(np.mean(random_residue_aucs <= true_auc))
    pct_true_vs_patch = float(np.mean(random_patch_aucs <= true_auc))
    best_of_n_residue = float(np.max(random_residue_aucs))
    best_of_n_patch = float(np.max(random_patch_aucs))

    # matched label-permutation null for best-of-N (residue draws): same
    # cached occupation vectors, permuted labels, no re-decomposition,
    # no re-draw of seeds.
    null_best_residue = np.empty(n_perm)
    null_best_patch = np.empty(n_perm)
    n_pocket = int(pocket_label.sum())
    for k in range(n_perm):
        perm_idx = rng.permutation(N)[:n_pocket]
        perm_label = np.zeros(N, dtype=int)
        perm_label[perm_idx] = 1
        vals_r = vectorized_auc_many(random_residue_occ, perm_label)
        vals_p = vectorized_auc_many(random_patch_occ, perm_label)
        null_best_residue[k] = np.max(vals_r)
        null_best_patch[k] = np.max(vals_p)

    p_residue = float(np.mean(null_best_residue >= best_of_n_residue))
    p_patch = float(np.mean(null_best_patch >= best_of_n_patch))

    arm_a = dict(
        n_seed=n_seed, N=N, true_auc=true_auc, n_random=n_random, n_perm=n_perm,
        percentile_true_vs_random_residue=pct_true_vs_residue,
        percentile_true_vs_random_patch=pct_true_vs_patch,
        best_of_n_random_residue=best_of_n_residue,
        best_of_n_random_patch=best_of_n_patch,
        null_best_of_n_residue_mean=float(null_best_residue.mean()),
        null_best_of_n_residue_ci=[float(np.percentile(null_best_residue, 2.5)), float(np.percentile(null_best_residue, 97.5))],
        null_best_of_n_patch_mean=float(null_best_patch.mean()),
        null_best_of_n_patch_ci=[float(np.percentile(null_best_patch, 2.5)), float(np.percentile(null_best_patch, 97.5))],
        p_best_of_n_residue_vs_null=p_residue,
        p_best_of_n_patch_vs_null=p_patch,
        random_residue_auc_min=float(random_residue_aucs.min()),
        random_residue_auc_max=float(random_residue_aucs.max()),
        random_residue_auc_median=float(np.median(random_residue_aucs)),
    )
    _log(f"  Arm A: true_auc percentile(vs random-residue)={pct_true_vs_residue:.3f} "
        f"percentile(vs patch)={pct_true_vs_patch:.3f} "
        f"best_of_N={best_of_n_residue:.4f} (null mean {null_best_residue.mean():.4f}, "
        f"p={p_residue:.3f})")

    # ---------------- ARM B ----------------
    apo_path = fetch_pdb(apo.pdb_id)
    apo_chain = apo.chain_ids[0]
    apo_lines = apo_path.read_text(errors="replace").splitlines()
    apo_resnum_to_idx = {int(rn): i for i, rn in enumerate(apo.resnums)}

    rules = {}

    # Rule 1: shipped active site (union), already computed
    a1, _ = occ_auc(true_source, w, v, pocket_label)
    rules["1_shipped_union"] = dict(n=len(true_source), auc=a1, detail="UniProt active+binding union (shipped)")

    # Rule 2: catalytic-only (UniProt "Active site" feature type alone)
    try:
        cat_resnums, detail = catalytic_only_residues(apo.pdb_id, apo_chain)
        if cat_resnums is None:
            rules["2_catalytic_only"] = dict(n=0, auc=None, detail=f"N/A -- {detail}")
        else:
            idx = [apo_resnum_to_idx[r] for r in cat_resnums if r in apo_resnum_to_idx]
            if not idx:
                rules["2_catalytic_only"] = dict(n=0, auc=None, detail=f"N/A -- none of {len(cat_resnums)} resnums map onto apo chain")
            else:
                a2, _ = occ_auc(idx, w, v, pocket_label)
                identical_to_rule1 = set(idx) == set(true_source)
                note = (" -- identical to rule 1: this target's shipped site has no "
                        "'Binding site'-typed residues beyond the 'Active site'-typed "
                        "ones, so the union (rule 1) and the Active-site-only subset "
                        "(rule 2) coincide" if identical_to_rule1 else "")
                rules["2_catalytic_only"] = dict(n=len(idx), auc=a2, identical_to_rule1=identical_to_rule1,
                                                 detail=detail + note)
    except Exception as e:
        rules["2_catalytic_only"] = dict(n=0, auc=None, detail=f"N/A -- {type(e).__name__}: {e}")

    # Rule 3: ligand-contact residues of func_ligand in holo
    func_ligand = target_config.get("func_ligand") or []
    if not func_ligand:
        rules["3_func_ligand_contact"] = dict(n=0, auc=None,
                                              detail="N/A -- func_ligand deliberately empty (TASK-0216)")
    else:
        holo_id = target_config["holo_pdb"]
        holo_chains = target_config.get("holo_chains") or target_config.get("chains") or [apo_chain]
        holo_lines = fetch_pdb(holo_id).read_text(errors="replace").splitlines()
        contact = set()
        for lig in func_ligand:
            for hc in holo_chains:
                contact |= ligand_contact_resnums(holo_lines, hc, lig, pocket_cutoff)
        idx = [apo_resnum_to_idx[r] for r in contact if r in apo_resnum_to_idx]
        if not idx:
            rules["3_func_ligand_contact"] = dict(n=0, auc=None,
                                                  detail=f"N/A -- {func_ligand} found no contacts mapping onto apo numbering")
        else:
            a3, _ = occ_auc(idx, w, v, pocket_label)
            true_resnum_set_r1 = set(int(apo.resnums[i]) for i in true_source)
            identical_to_rule1 = set(idx) == set(true_source)
            note = (" -- IDENTICAL TO RULE 1 BY CONSTRUCTION: labels.py's own tier 1 "
                    "(build_labels) IS func_ligand contact for this target, so rule 1 "
                    "and rule 3 cannot differ, not a biological finding"
                    if identical_to_rule1 else "")
            rules["3_func_ligand_contact"] = dict(
                n=len(idx), auc=a3, identical_to_rule1=identical_to_rule1,
                detail=f"{func_ligand} contact in {holo_id}, {len(contact)} raw / {len(idx)} mapped{note}")

    # Rule 4: fpocket candidate overlapping rule 1 most, on the apo structure
    try:
        work = RESULTS / "work" / target_name / "fpocket"
        work.mkdir(parents=True, exist_ok=True)
        apo_only_pdb = work / f"{apo.pdb_id.lower()}_apo.pdb"
        write_apo_pdb(apo_lines, apo_chain, apo_only_pdb)
        pockets = t0242.fpocket_candidates(apo_only_pdb, work)
        if isinstance(pockets, dict) and "error" in pockets:
            rules["4_fpocket_active_site_pocket"] = dict(n=0, auc=None, detail=f"N/A -- fpocket error: {pockets['error']}")
        elif not pockets:
            rules["4_fpocket_active_site_pocket"] = dict(n=0, auc=None, detail="N/A -- fpocket found no pockets")
        else:
            true_resnum_set = set(int(apo.resnums[i]) for i in true_source)
            best_p, best_frac = None, -1.0
            for p in pockets:
                resnums_here = {rn for (c, rn) in p["resnums"] if c == apo_chain}
                frac = len(resnums_here & true_resnum_set) / max(1, len(true_resnum_set))
                if frac > best_frac:
                    best_frac, best_p = frac, p
            resnums_here = {rn for (c, rn) in best_p["resnums"] if c == apo_chain}
            idx = [apo_resnum_to_idx[r] for r in resnums_here if r in apo_resnum_to_idx]
            a4, _ = occ_auc(idx, w, v, pocket_label)
            rules["4_fpocket_active_site_pocket"] = dict(
                n=len(idx), auc=a4,
                detail=f"best-overlap fpocket candidate ({best_frac:.2f} overlap with rule-1), "
                       f"druggability={best_p.get('druggability_score')}")
    except Exception as e:
        rules["4_fpocket_active_site_pocket"] = dict(n=0, auc=None, detail=f"N/A -- {type(e).__name__}: {e}")

    # Rule 5: single residue nearest rule-1's centroid
    centroid = apo.coords[true_source].mean(axis=0)
    d = np.sqrt(((apo.coords - centroid) ** 2).sum(axis=1))
    nearest_idx = int(np.argmin(d))
    a5, _ = occ_auc([nearest_idx], w, v, pocket_label)
    rules["5_pocket_centroid_point"] = dict(n=1, auc=a5, detail=f"apo resnum {int(apo.resnums[nearest_idx])}")

    _log(f"  Arm B: " + ", ".join(f"{k}={v['auc']}" for k, v in rules.items()))

    return dict(target=target_name, N=N, n_seed=n_seed, true_auc=true_auc,
               arm_a=arm_a, arm_b=rules)


def main() -> int:
    pilot = "--pilot" in sys.argv
    n_random = 50 if pilot else 2000
    n_perm = 10 if pilot else 200
    _log(f"{'PILOT' if pilot else 'FULL'} run: n_random={n_random} n_perm={n_perm}")

    out = {}
    t0 = time.time()
    for target in TARGETS:
        try:
            out[target] = run_target(target, n_random, n_perm, det_seed(target))
        except Exception as e:
            import traceback
            out[target] = dict(error=f"{type(e).__name__}: {e}", traceback=traceback.format_exc())
            _log(f"{target}: FAILED -- {e}")
        _log(f"  ({time.time()-t0:.0f}s elapsed)")

    out_path = RESULTS / ("pilot_result.json" if pilot else "result.json")
    out_path.write_text(json.dumps(out, indent=1, default=str))
    _log(f"Wrote {out_path} ({time.time()-t0:.0f}s total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
