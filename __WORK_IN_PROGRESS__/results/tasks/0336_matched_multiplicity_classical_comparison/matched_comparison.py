#!/usr/bin/env python3
"""TASK-0336 -- settle Defect 1 (multiplicity: CTQW is max-over-221/884,
classical arms are single rankings) and Defect 2 (metric/object: classical.py
independently re-derives its own un-vetoed pocket set and a "any pocket
touching truth" y-definition, not the same object the veto-pipeline's own
`pockets`/`ranks` describe), then chance-corrects EVERY arm with the SAME
pocket-block null TASK-0328 built for this dataset's own residue-level null,
generalized to pocket level.

Design, stated once so each step below can be checked against it:

1. ONE candidate pocket set for every arm: round 2's own stored `pockets`
   (veto survivors) for all 435 MIN_HOP=2 structures that scored --
   `classical.py`'s own re-derived, un-vetoed PASSer-top-10 pockets are not
   used at all (that was part of Defect 2: different candidate SET, not just
   a different aggregation of the same one). 3 of 5 classical arms need
   nothing but round 2's own stored per-pocket fields (`rk_pa`, `drug`, `n`)
   -- no PDB refetch. The other 2 (proximity, degree) need residue-level
   hop/degree, which round 2's JSON does not store; refetched, SCOPED TO THE
   DISTAL SUBSET ONLY (80 structures) -- the Intent Contract names the distal
   margin as "the number that decides it", and a ~350-structure refetch for
   the near subset is out of this task's time budget. Stated as a scope
   reduction, not hidden.
2. ONE truth-pocket definition for every arm: a pocket counts as truth
   (`y_pocket=1`) iff it contains at least one truth residue (`n_drug>0` in
   the stored `pockets` field) -- this is `classical.py`'s own definition
   (`len(set(m)&T)>0`), adopted here rather than the veto_pipeline/TASK-0327
   single-argmax-drug-pocket convention, because it is the definition already
   built into the stored `n_drug` field and needs no re-derivation.
3. ONE multiplicity for the CTQW arm: two cells, PRE-REGISTERED before this
   script computed anything from them (both are named in this module's own
   first commit, not chosen after seeing which one wins) --
   `hnew|full|p_avg` (the paper's own flagship operator, closed-form T->infinity
   score) and `binary|adj|p_avg` (the simplest possible construction, no
   H_new potential terms) as a robustness check. Pocket order under a cell =
   pockets sorted by their best (minimum) member-seed rank, from the stored
   `ranks` vector -- the same "best member wins" identity TASK-0327 proved.
4. ONE null, applied to every arm: TASK-0328's own `draw_pocket_block_null`
   (whole-pocket blocks, not scattered residues), reused directly by import,
   not re-derived -- draws a permuted positive-seed set of the same size,
   respecting real pocket structure; permuted pocket truth y'_pocket =
   (permuted n_drug' > 0); every arm's own FIXED pocket order (order does not
   depend on labels) is then P@5-scored against y'_pocket, B times.
5. Family-level counting, both observed and chance (mean over the null
   draws), reproducing per_family_full_minhop2.csv's own "any structure in
   the family clears -> family counts" convention -- verified in Planned
   Validation before being reused for arms other than CTQW.

Usage: python3 matched_comparison.py
"""
import gzip
import hashlib
import json
import os
import sys
import time
import urllib.request

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "upstream_artifacts")
TASK0328_DIR = os.path.join(HERE, "..", "..", "..", "scripts")
sys.path.insert(0, os.path.abspath(TASK0328_DIR))
from task0328_pocketsweep_null_recalibration import (  # noqa: E402
    det_seed, pocket_members, draw_pocket_block_null,
)

CACHE = os.path.join(HERE, "pdb_cache")
os.makedirs(CACHE, exist_ok=True)
AA3 = {"ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
       "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL", "MSE"}

CTQW_CELLS = ["hnew|full|p_avg", "binary|adj|p_avg"]
B_NULL = 500  # Monte Carlo draws for the pocket-block null (TASK-0328 used B=200/2000)
P5_THRESHOLD = 0.8


def load_worklist():
    w = json.load(open(os.path.join(ART, "operator_worklist.json")))
    return {x["name"]: x for x in w}


def load_round(fname):
    with gzip.open(os.path.join(ART, fname)) as f:
        return json.load(f)


# --------------------------------------------------------------------------
# Planned Validation -- run first, before any re-derivation is trusted.
# --------------------------------------------------------------------------

def validate_cell_reproduction(recs):
    """Reproduce one published cell's stored P@5 from `ranks`+`y` directly,
    for several structures, before trusting any further derivation from
    those same two fields."""
    checked = 0
    for name, v in recs.items():
        if "cells" not in v or checked >= 5:
            continue
        y = np.array(v["y"])
        for cell in CTQW_CELLS:
            if cell not in v["ranks"]:
                continue
            ranks = np.array(v["ranks"][cell])
            top5 = np.argsort(ranks)[:5]
            my_p5 = float(y[top5].sum()) / 5.0
            stored_p5 = v["cells"][cell][1]
            assert abs(my_p5 - stored_p5) < 1e-9, (name, cell, my_p5, stored_p5)
        checked += 1
    return dict(n_structures_checked=checked, cells_checked=CTQW_CELLS, all_exact_match=True)


def validate_family_aggregation(recs, wmap):
    """Reproduce per_family_full_minhop2.csv's own 'structures_cleared' count
    for a few families, using round 2's stored obs_max_p5 (max over all 221
    cells) at the >=0.8 threshold -- confirms the family rule is 'count of
    structures in the family clearing', and that my (name -> cluster) join
    via operator_worklist.json lines up with the CSV's own family key."""
    import csv
    csv_rows = {}
    with open(os.path.join(ART, "per_family_full_minhop2.csv")) as f:
        for row in csv.DictReader(f):
            csv_rows[row["family"]] = row
    by_family = {}
    for name, v in recs.items():
        if "cells" not in v:
            continue
        fam = wmap[name]["cluster"]
        by_family.setdefault(fam, []).append(v["obs_max_p5"])
    out = {}
    for fam in ("CAS0061", "CAS0050", "CAS0015"):
        if fam not in csv_rows or fam not in by_family:
            out[fam] = "not found in one of the two sources"
            continue
        mine = sum(1 for p5 in by_family[fam] if p5 >= P5_THRESHOLD)
        theirs = int(csv_rows[fam]["structures_cleared"])
        out[fam] = dict(mine=mine, csv=theirs, match=(mine == theirs), n_structures_mine=len(by_family[fam]))
    return out


# --------------------------------------------------------------------------
# Pocket-level scoring machinery, shared by every arm.
# --------------------------------------------------------------------------

def y_pocket_from_ndrug(pockets):
    return {p["id"]: int(p["n_drug"] > 0) for p in pockets}


def ctqw_pocket_order(v, cell):
    """Pockets sorted by best (min) member-seed rank under this cell --
    TASK-0327's 'best member wins' identity, extended from top-1 to a full
    order. seed_pocket[i] is already the pocket id owning seed i."""
    if cell not in v["ranks"]:
        return None
    ranks = v["ranks"][cell]
    seed_pocket = v["seed_pocket"]
    best = {}
    for i, pid in enumerate(seed_pocket):
        if pid is None:
            continue
        r = ranks[i]
        if pid not in best or r < best[pid]:
            best[pid] = r
    return [pid for pid, _ in sorted(best.items(), key=lambda kv: (kv[1], kv[0]))]


def classical_pocket_order_no_refetch(pockets):
    """3 of 5 classical arms, computed directly from round 2's OWN stored
    pocket attributes -- same candidate set as CTQW, zero refetch."""
    orders = {}
    orders["passer_rank"] = [p["id"] for p in sorted(pockets, key=lambda p: (p["rk_pa"] if p["rk_pa"] is not None else 10**9))]
    orders["fpocket_drug"] = [p["id"] for p in sorted(pockets, key=lambda p: -p["drug"])]
    orders["pocket_size"] = [p["id"] for p in sorted(pockets, key=lambda p: -p["n"])]
    return orders


def p5_over_pockets(order, y_pocket):
    if not order:
        return None
    top5 = order[:5]
    return sum(y_pocket.get(pid, 0) for pid in top5) / 5.0


# --------------------------------------------------------------------------
# Refetch-dependent arms (proximity, degree) -- distal subset only.
# --------------------------------------------------------------------------

def fetch(pid):
    p = os.path.join(CACHE, pid + ".pdb")
    if os.path.exists(p) and os.path.getsize(p) > 0:
        return p
    for a in range(3):
        try:
            with urllib.request.urlopen(f"https://files.rcsb.org/download/{pid}.pdb", timeout=25) as r, \
                 open(p + ".t", "wb") as f:
                f.write(r.read())
            os.replace(p + ".t", p)
            return p
        except Exception:
            time.sleep(1.3 ** a)
    return None


def ca(path, chain):
    """Verbatim port of classical.py's own Cα parser -- same cutoff, same
    HETATM/AA3 filtering -- so hop/degree are computed the identical way."""
    ch = {}
    for l in open(path, errors="replace"):
        if l.startswith("ENDMDL"):
            break
        if l[:6].strip() not in ("ATOM", "HETATM"):
            continue
        if l[:6].strip() == "HETATM" and l[17:20].strip() not in AA3:
            continue
        if l[12:16].strip() != "CA":
            continue
        c = l[21]
        try:
            ch.setdefault(c, []).append((int(l[22:26]), [float(l[30:38]), float(l[38:46]), float(l[46:54])]))
        except Exception:
            pass
    if not ch:
        return None, None
    c = chain if chain in ch else max(ch, key=lambda k: len(ch[k]))
    seen, out = {}, []
    for r, xyz in ch[c]:
        if r not in seen:
            seen[r] = len(out)
            out.append((r, xyz))
    return {r: i for i, (r, _) in enumerate(out)}, np.array([x for _, x in out], float)


def classical_pocket_order_refetch(name, wrec, v):
    """proximity(-hop) and degree, on round 2's OWN surviving pockets --
    requires PDB Cα coordinates round 2's stored JSON does not carry."""
    p = fetch(wrec["pdb"])
    if not p:
        return None
    idx, X = ca(p, wrec["chain"])
    if idx is None:
        return None
    A = [idx[r] for r in wrec["active"] if r in idx]
    if not A:
        return None
    D2 = ((X[:, None, :] - X[None, :, :]) ** 2).sum(-1)
    adj = csr_matrix(((D2 < 100) & (D2 > 0)).astype(np.int8))
    hop = dijkstra(adj, directed=False, indices=A, unweighted=True, min_only=True)
    deg = np.asarray(((D2 < 100) & (D2 > 0)).sum(1)).ravel()
    seed_resnum = v["seed_resnum"]
    seed_pocket = v["seed_pocket"]
    pocket_seed_idx = {}
    for i, pid in enumerate(seed_pocket):
        if pid is None:
            continue
        pocket_seed_idx.setdefault(pid, []).append(i)
    prox, degree = {}, {}
    for pid, seed_is in pocket_seed_idx.items():
        ca_idxs = []
        for si in seed_is:
            rn = seed_resnum[si]
            if rn in idx:
                ca_idxs.append(idx[rn])
        if not ca_idxs:
            continue
        hp = [hop[i] for i in ca_idxs if np.isfinite(hop[i])]
        prox[pid] = -np.mean(hp) if hp else -1e9
        degree[pid] = np.mean([deg[i] for i in ca_idxs])
    if not prox:
        return None
    order_prox = [pid for pid, _ in sorted(prox.items(), key=lambda kv: -kv[1])]
    order_deg = [pid for pid, _ in sorted(degree.items(), key=lambda kv: -kv[1])]
    return dict(proximity=order_prox, degree=order_deg)


# --------------------------------------------------------------------------
# Null: permute truth at the seed level, respecting pocket blocks; recompute
# y'_pocket; score every arm's FIXED order against it. Same null draw shared
# by every arm for a given structure/replicate (correct: one randomization,
# many statistics computed from it).
# --------------------------------------------------------------------------

def null_p5_for_arms(v, arm_orders, rng):
    y = np.asarray(v["y"], dtype=float)
    n = len(y)
    kpos = int(y.sum())
    if kpos == 0 or kpos == n:
        return {arm: [] for arm in arm_orders}
    members = pocket_members(v)
    seed_pocket = v["seed_pocket"]
    out = {arm: np.empty(B_NULL) for arm in arm_orders}
    for b in range(B_NULL):
        pos = set(draw_pocket_block_null(rng, n, kpos, members).tolist())
        ndrug_perm = {}
        for i, pid in enumerate(seed_pocket):
            if pid is None:
                continue
            ndrug_perm[pid] = ndrug_perm.get(pid, 0) + (1 if i in pos else 0)
        y_perm = {pid: int(nd > 0) for pid, nd in ndrug_perm.items()}
        for arm, order in arm_orders.items():
            out[arm][b] = p5_over_pockets(order, y_perm) if order else np.nan
    return out


def main():
    wmap = load_worklist()
    recs = load_round("r2_minhop2.json.gz")
    testable = {n: v for n, v in recs.items() if "cells" in v}
    print(f"round 2, MIN_HOP=2: {len(testable)} testable structures")

    val1 = validate_cell_reproduction(testable)
    print("Validation 1 (cell reproduction):", val1)
    val2 = validate_family_aggregation(testable, wmap)
    print("Validation 2 (family aggregation):", val2)
    for fam, r in val2.items():
        if isinstance(r, dict):
            assert r["match"], f"family aggregation mismatch on {fam}: {r}"

    per_structure = {}  # name -> dict(arm -> dict(observed=..., null=[...]))
    n_distal_refetched, n_distal_failed = 0, 0
    t0 = time.time()
    for k, (name, v) in enumerate(testable.items(), 1):
        wrec = wmap[name]
        pockets = v["pockets"]
        if len(pockets) < 2:
            continue
        y_pocket = y_pocket_from_ndrug(pockets)

        arm_orders = {}
        for cell in CTQW_CELLS:
            o = ctqw_pocket_order(v, cell)
            if o:
                arm_orders[f"ctqw:{cell}"] = o
        arm_orders.update(classical_pocket_order_no_refetch(pockets))

        if wrec.get("is_distal"):
            refetched = classical_pocket_order_refetch(name, wrec, v)
            if refetched:
                arm_orders["proximity(-hop)"] = refetched["proximity"]
                arm_orders["degree"] = refetched["degree"]
                n_distal_refetched += 1
            else:
                n_distal_failed += 1

        observed = {arm: p5_over_pockets(order, y_pocket) for arm, order in arm_orders.items()}
        rng = np.random.default_rng(det_seed(name + "|task0336"))
        null = null_p5_for_arms(v, arm_orders, rng)
        per_structure[name] = dict(
            observed=observed,
            null_mean={arm: float(np.mean(vals)) if len(vals) else None for arm, vals in null.items()},
            null_clear_frac={arm: float(np.mean(np.asarray(vals) >= P5_THRESHOLD)) if len(vals) else None
                              for arm, vals in null.items()},
            is_distal=bool(wrec.get("is_distal")),
            cluster=wrec["cluster"],
        )
        if k % 100 == 0:
            print(f"  {k}/{len(testable)} ({time.time()-t0:.0f}s)")

    print(f"Distal refetch: {n_distal_refetched} ok, {n_distal_failed} failed")

    # -------- family-level aggregation: observed and chance-expected --------
    all_arms = sorted({arm for s in per_structure.values() for arm in s["observed"]})
    families_by_split = {"ALL": {}, "near": {}, "distal": {}}
    for name, s in per_structure.items():
        fam = s["cluster"]
        split = "distal" if s["is_distal"] else "near"
        for key in ("ALL", split):
            families_by_split[key].setdefault(fam, []).append(name)

    def family_counts(split, arm):
        obs_clear, chance_clear = 0, 0.0
        n_fam = 0
        for fam, names in families_by_split[split].items():
            vals_obs = [per_structure[n]["observed"].get(arm) for n in names]
            vals_obs = [x for x in vals_obs if x is not None]
            vals_chance = [per_structure[n]["null_clear_frac"].get(arm) for n in names]
            vals_chance = [x for x in vals_chance if x is not None]
            if not vals_obs:
                continue
            n_fam += 1
            if max(vals_obs) >= P5_THRESHOLD:
                obs_clear += 1
            # family "clears by chance" prob, approximated as 1-prod(1-p_i)
            # over structures in the family (independence across structures
            # within a family is an approximation, stated here, not hidden)
            p_none = 1.0
            for p in vals_chance:
                p_none *= (1.0 - p)
            chance_clear += (1.0 - p_none)
        return n_fam, obs_clear, chance_clear

    table = {}
    for arm in all_arms:
        table[arm] = {}
        for split in ("ALL", "near", "distal"):
            n_fam, obs, chance = family_counts(split, arm)
            table[arm][split] = dict(n_families=n_fam, observed_clearing=obs,
                                      chance_expected_clearing=round(chance, 2),
                                      real_excess=round(obs - chance, 2))

    print("\n=== Family-level P@5>=0.8 clearing, matched metric+multiplicity+null ===")
    for arm in all_arms:
        print(f"\n{arm}:")
        for split in ("ALL", "near", "distal"):
            r = table[arm][split]
            print(f"  {split:7s} n_fam={r['n_families']:4d} observed={r['observed_clearing']:4d} "
                  f"chance~{r['chance_expected_clearing']:6.2f} real_excess~{r['real_excess']:6.2f}")

    out = dict(
        validation_cell_reproduction=val1,
        validation_family_aggregation=val2,
        n_testable=len(testable),
        n_distal_refetched=n_distal_refetched,
        n_distal_refetch_failed=n_distal_failed,
        b_null=B_NULL,
        family_table=table,
    )
    out_path = os.path.join(HERE, "matched_comparison_result.json")
    json.dump(out, open(out_path, "w"), indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
