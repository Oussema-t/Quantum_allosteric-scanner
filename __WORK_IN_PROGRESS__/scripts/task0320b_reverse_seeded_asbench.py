"""TASK-0320b -- reverse-seeded CTQW as a pocket-selection method, on ASBench.

[[TASK-0320]] ran this on the 19-target frozen set and could not adjudicate:
proximity itself -- the confound known to dominate every residue-level score in
this register -- scored median rho +0.24 at cluster-p 0.36. A design that cannot
detect proximity cannot rule anything out. This is the same question on ASBench,
which has ~5x the independent units.

WHAT IS BEING TESTED, AND WHY THE DIRECTION IS NOT THE VARIABLE

The proposal is to seed the walk at a candidate pocket and measure how much
amplitude reaches the active site. `H_new` is real symmetric and seed-
independent, so the converged kernel M_ij = sum_B (P_B)^2_ij is exactly
symmetric ([[TASK-0312]], 1.11e-16). Hence, for candidate P and active site A:

    transfer(P->A) = (|A|/|P|) * sum_{i in P} p_A(i) = |A| * mean_{i in P} p_A(i)

|A| is constant within a structure, so ranking candidates by reverse-seeded
transfer is IDENTICALLY ranking them by mean forward occupation. Verified
numerically to machine precision. The reverse direction therefore contributes no
information; what is genuinely untested is the AGGREGATION (mean-per-candidate,
and its size-weighted variant sum-per-candidate) at POCKET level, since this
register scored CTQW per residue.

PRE-REGISTERED PREDICTION, stated before the run: CTQW residualises to proximity
([[TASK-0308]]/[[TASK-0310]]), and [[TASK-0287]] measured that distance-to-seed
does not select the true pocket among fpocket candidates, because every target
has candidates sitting on its own active site. So this should fail the same way.

Run: ../.venv/bin/python3 scripts/task0320b_reverse_seeded_asbench.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import warnings
from collections import defaultdict
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np
from scipy.stats import rankdata, spearmanr, wilcoxon

warnings.filterwarnings("ignore")
sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
sys.path.insert(0, "..")

from backend.data_layer import fetch                                  # noqa: E402
from allostery.hamiltonians import build_H_new                        # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged        # noqa: E402
import task0242_two_stage_dryrun as t0242                             # noqa: E402
from task0308_attribution_scaling import ca, pa, pact                 # noqa: E402

OUT = Path("results/tasks/0320b_reverse_seeded_asbench")
ANN = json.load(open("results/tasks/0304_asbench_casbench/asbench_annotations.json"))
KEEP = {r["pdb"] for r in json.load(
    open("results/tasks/0305_asbench_detection/asbench_detection.json"))["rows"]}

ARMS = ["ctqw_mean", "ctqw_sum", "prox_min", "fpocket_drug", "n_res"]
MAXN = 3000
CUTOFF = 8.0


def _log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def rank_resid(x, z):
    """Rank-residualise x on z (same construction as TASK-0308/0310)."""
    rx, rz = rankdata(x), rankdata(z)
    rz = rz - rz.mean()
    d = float(rz @ rz)
    if d < 1e-12:
        return rx.astype(float)
    b = float((rx - rx.mean()) @ rz) / d
    return (rx - rx.mean()) - b * rz


def candidates_for(pdb: str, keys):
    """fpocket on the deposited structure; candidates as index lists into
    `keys`. Uses the same vendored binary and (chain, resnum) keying as
    task0242.fpocket_candidates -- not a second parser."""
    pos = {k: i for i, k in enumerate(keys)}
    src = Path(fetch(pdb))
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        work = tmp / f"{pdb.lower()}.pdb"
        work.write_text(src.read_text())
        pockets = t0242.fpocket_candidates(work, tmp)
        if isinstance(pockets, dict):
            return None, pockets["error"]
        out = []
        for p in pockets:
            ii = [pos[k] for k in p["resnums"] if k in pos]
            if not ii:
                continue
            out.append({"id": p["id"], "idx": np.asarray(sorted(set(ii)), int),
                        "drug": float(p.get("druggability_score") or 0.0)})
    return (out, None) if out else (None, "no residue-resolvable candidates")


def run_one(rec) -> dict | None:
    pdb = rec["pdb"].split("_")[0]
    keys, xyz, bf = ca(pdb)
    n = len(keys)
    if n == 0 or n > MAXN:
        return None
    pos = {k: i for i, k in enumerate(keys)}
    seed = sorted({pos[k] for k in (pact(t) for t in rec["active_residues"]) if k in pos})
    truth = sorted({pos[k] for k in (pa(t) for t in rec["allosteric_residues"]) if k in pos})
    if not seed or not truth:
        return None

    H = build_H_new(xyz, bf, cutoff=CUTOFF)
    fwd = np.nan_to_num(time_averaged_ctqw_converged(H, source=np.asarray(seed),
                                                     coherent=False))
    # proximity: CA-space distance to the nearest seed residue. CA rather than
    # heavy-atom because the whole pipeline (H_new, CTQW) is CA-based -- mixing
    # resolutions between the score and its own control would be the confound
    # this test exists to remove.
    d_seed = np.linalg.norm(xyz[:, None, :] - xyz[None, seed, :], axis=2).min(axis=1)

    cands, err = candidates_for(pdb, keys)
    if cands is None:
        return {"pdb": rec["pdb"], "error": err}
    if len(cands) < 3:
        return None

    tset = set(truth)
    recall = np.array([len(tset & set(c["idx"].tolist())) / len(tset) for c in cands])
    best = int(np.argmax(recall))
    if recall[best] <= 0:
        return {"pdb": rec["pdb"], "error": "no candidate recalls the annotated site"}

    A = {
        "ctqw_mean": np.array([fwd[c["idx"]].mean() for c in cands]),
        "ctqw_sum": np.array([fwd[c["idx"]].sum() for c in cands]),
        "prox_min": np.array([-d_seed[c["idx"]].min() for c in cands]),
        "fpocket_drug": np.array([c["drug"] for c in cands]),
        "n_res": np.array([float(len(c["idx"])) for c in cands]),
    }
    row = {"pdb": rec["pdb"], "protein": rec.get("protein", rec["pdb"]),
           "N": n, "n_cands": len(cands), "n_seed": len(seed), "n_truth": len(truth),
           "best_recall": float(recall[best])}
    for k in ARMS:
        order = np.argsort(-A[k])
        row[f"{k}__top_is_best"] = bool(order[0] == best)
        row[f"{k}__rank_of_best"] = int(np.where(order == best)[0][0]) + 1
        row[f"{k}__recall_top"] = float(recall[int(order[0])])
        row[f"{k}__rho"] = float(spearmanr(A[k], recall).statistic)
    r = rank_resid(A["ctqw_mean"], A["prox_min"])
    row["ctqw_resid__rho"] = float(spearmanr(r, recall).statistic)
    row["ctqw_resid__rank_of_best"] = int(np.where(np.argsort(-r) == best)[0][0]) + 1
    row["rho_ctqw_prox"] = float(spearmanr(A["ctqw_mean"], A["prox_min"]).statistic)
    row["random_rank"] = (len(cands) + 1) / 2.0
    row["random_recall"] = float(recall.mean())
    # retained for the permuted-label null: the null must be built from the
    # SAME candidate scores, permuting only which candidate carries the truth
    row["_recall"] = recall.tolist()
    row["_ctqw"] = A["ctqw_mean"].tolist()
    row["_resid"] = rank_resid(A["ctqw_mean"], A["prox_min"]).tolist()
    return row


def by_protein(rows, key):
    g = defaultdict(list)
    for r in rows:
        g[r["protein"]].append(r[key])
    return np.array([np.median(v) for v in g.values()])


def main() -> int:
    recs = [r for r in ANN if r["pdb"] in KEEP]
    _log(f"{len(recs)} ASBench structures in the TASK-0305 KEEP set")
    rows, errs = [], []
    for i, rec in enumerate(recs):
        try:
            r = run_one(rec)
        except Exception as e:
            errs.append((rec["pdb"], f"{type(e).__name__}: {str(e)[:50]}")); continue
        if r is None:
            continue
        if "error" in r:
            errs.append((r["pdb"], r["error"])); continue
        rows.append(r)
        if len(rows) % 15 == 0:
            _log(f"  {i+1}/{len(recs)} scanned, {len(rows)} usable")
    _log(f"done: {len(rows)} usable, {len(errs)} excluded")

    if len(rows) < 10:
        _log("too few usable structures"); return 1

    nprot = len({r["protein"] for r in rows})
    print("\n" + "=" * 80)
    print(f"REVERSE-SEEDED POCKET SELECTION -- ASBench")
    print(f"n = {len(rows)} structures / {nprot} proteins")
    print("=" * 80)
    print(f"\n{'arm':<16}{'top-1 hit':>11}{'med rank':>10}{'recall@top':>12}{'med rho':>10}")
    for k in ARMS:
        hit = np.mean([r[f"{k}__top_is_best"] for r in rows])
        rk = np.median([r[f"{k}__rank_of_best"] for r in rows])
        rc = np.mean([r[f"{k}__recall_top"] for r in rows])
        rho = np.median([r[f"{k}__rho"] for r in rows])
        print(f"{k:<16}{hit:>10.1%}{rk:>10.1f}{rc:>12.4f}{rho:>+10.3f}")
    print(f"{'random':<16}{'--':>10}{np.median([r['random_rank'] for r in rows]):>10.1f}"
          f"{np.mean([r['random_recall'] for r in rows]):>12.4f}{0.0:>+10.3f}")

    print("\n--- decisive test, clustered by protein ---")
    for nm, key in (("ctqw raw", "ctqw_mean__rho"),
                    ("ctqw | proximity", "ctqw_resid__rho"),
                    ("proximity (power check)", "prox_min__rho"),
                    ("fpocket druggability", "fpocket_drug__rho")):
        v = by_protein(rows, key)
        p = wilcoxon(v).pvalue if len(v) > 5 else float("nan")
        print(f"  {nm:<26} median={np.median(v):+.4f}  n={len(v):3d}  "
              f"positive {int((v > 0).sum())}/{len(v)}  Wilcoxon p={p:.4g}")

    print(f"\n  median rho(ctqw, proximity) = "
          f"{np.median([r['rho_ctqw_prox'] for r in rows]):+.3f}")

    # ---- negative control: permute which candidate carries the truth ----
    # TASK-0319: this register ran positive controls and omitted negative ones,
    # and that omission invalidated a headline. The null reproduces the whole
    # pipeline (per-structure Spearman -> protein median -> Wilcoxon) with the
    # association destroyed, and must land at ~0.
    print("\n--- negative control: permuted-label null, 200 reps ---")
    rng = np.random.default_rng(0)
    obs = {"ctqw raw": float(np.median(by_protein(rows, "ctqw_mean__rho"))),
           "ctqw | proximity": float(np.median(by_protein(rows, "ctqw_resid__rho")))}
    keyed = {"ctqw raw": "_ctqw", "ctqw | proximity": "_resid"}
    null = {k: [] for k in obs}
    for _ in range(200):
        for k, src in keyed.items():
            g = defaultdict(list)
            for r in rows:
                rc = np.asarray(r["_recall"], float)
                rng.shuffle(rc)
                g[r["protein"]].append(
                    float(spearmanr(np.asarray(r[src], float), rc).statistic))
            null[k].append(float(np.median([np.median(v) for v in g.values()])))
    for k in obs:
        nz = np.asarray(null[k])
        p_emp = (int((nz >= obs[k]).sum()) + 1) / (len(nz) + 1)
        centred = "YES" if abs(float(nz.mean())) < 0.02 else "NO"
        print(f"  {k:<18} observed={obs[k]:+.4f}  null={nz.mean():+.4f} +/- {nz.std(ddof=1):.4f}"
              f"  reps>=obs {int((nz >= obs[k]).sum())}/{len(nz)}  p={p_emp:.4f}")
        print(f"  {'':<18} null centres on zero: {centred}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "reverse_seeded_asbench.json").write_text(
        json.dumps({"n": len(rows), "n_proteins": nprot,
                    "excluded": errs, "rows": rows}, indent=1))
    print(f"\nwritten -> {OUT}/reverse_seeded_asbench.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
