"""TASK-0320 -- "seed the CTQW at each candidate pocket and measure how much
signal reaches the active site" as a pocket-ranking method.

THE ALGEBRA, VERIFIED BEFORE RUNNING ANYTHING

The proposal is a *reverse-seeded* score: for candidate pocket P and active site
A, transfer(P->A) = sum_{i in P, j in A} M_ij / |P|, where M is the converged
CTQW kernel. `H_new` is real symmetric and seed-independent, so
M_ij = sum_B (P_B)^2_ij is exactly symmetric ([[TASK-0312]], verified to
1.11e-16). Therefore

    transfer(P->A) = (|A|/|P|) * sum_{i in P} p_A(i)  =  |A| * mean_{i in P} p_A(i)

where p_A is the ORDINARY FORWARD occupation seeded at the active site. |A| is
constant across candidates within a target, so **ranking candidate pockets by
reverse-seeded transfer is identically ranking them by MEAN forward CTQW
occupation over the candidate's residues.** Confirmed numerically to machine
precision before this script was written.

So there is no new propagation here. What IS potentially new, and is why this
task exists rather than being closed on the algebra alone:

  1. AGGREGATION. The register scored CTQW at RESIDUE level (P@5, per-residue
     AUC). Mean-per-candidate-pocket is a different statistic, and mean vs sum
     differs by candidate size -- the dominant confound [[TASK-0287]] found in
     fpocket druggability. Both are scored here.
  2. TASK LEVEL. Selecting among fpocket candidates is not the same task as
     ranking residues. [[TASK-0287]] measured that distance-to-seed does NOT
     select the true pocket among candidates (0.393 raw, p=0.065; 0.478
     conditioned, p=0.70) because every target has candidates sitting on its own
     active site. CTQW residualises to proximity ([[TASK-0308]]/[[TASK-0310]]),
     so the PREDICTION is that this fails the same way. Prediction stated here,
     before the run, so the result is a test and not a story.

Reuses `task0282_pocket_selection_sweep.build_target` unchanged -- it already
computes `mean(ctqw_full[ii])` per candidate, so no propagator call is
re-implemented. Adds only the ranking evaluation that task never ran.

Run: ../.venv/bin/python3 scripts/task0320_reverse_seeded_pocket_ranking.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np
from scipy.stats import rankdata, spearmanr, wilcoxon

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "scripts"))

import yaml  # noqa: E402
import task0282_pocket_selection_sweep as t0282  # noqa: E402

OUT = _ROOT / "results/tasks/0320_reverse_seeded_pocket_ranking"

# The candidate-level arms. `ctqw_mean` IS the reverse-seeded transfer, up to
# the constant |A|; `ctqw_sum` is the size-weighted variant.
ARMS = ["ctqw_mean", "ctqw_sum", "prox_min_euclid", "prox_centroid",
        "fpocket_drug", "n_res"]


def _log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def arms_for(c: dict) -> dict:
    """Every arm as 'higher = better candidate', so ranks are comparable."""
    return {
        "ctqw_mean": c["ctqw"],                 # == reverse transfer / |A|
        "ctqw_sum": c["ctqw"] * c["n_res"],
        "prox_min_euclid": -c["min_euclid"],    # nearer the seed = higher
        "prox_centroid": c["centroid_euclid"],  # already negated distance
        "fpocket_drug": c["fpocket_drug"],
        "n_res": float(c["n_res"]),
    }


def rank_resid(x: np.ndarray, z: np.ndarray) -> np.ndarray:
    """Rank-residualise x on z: the part of x's ordering z does not explain.
    Same construction [[TASK-0308]]/[[TASK-0310]] use, at candidate level."""
    if len(x) < 3:
        return x.astype(float)
    rx, rz = rankdata(x), rankdata(z)
    rz = (rz - rz.mean())
    denom = float(rz @ rz)
    if denom < 1e-12:
        return rx.astype(float)
    beta = float((rx - rx.mean()) @ rz) / denom
    return (rx - rx.mean()) - beta * rz


def evaluate(target: str, d: dict) -> dict | None:
    cands = d["cands"]
    if len(cands) < 3:
        return None
    EH = np.array([c["EH"] for c in cands], float)
    overlap = np.array([c["overlap_count"] for c in cands], float)
    n_pocket = d["n_pocket"]
    # truth: the candidate that best RECALLS the true pocket (TASK-0282's own
    # oracle definition, reused rather than re-invented)
    recall = overlap / max(n_pocket, 1)
    best = int(np.argmax(recall))
    if recall[best] <= 0:
        return None  # no candidate touches the true pocket: nothing to select

    A = {k: np.array([arms_for(c)[k] for c in cands], float) for k in ARMS}
    prox = A["prox_min_euclid"]

    row = {"target": target, "n_cands": len(cands), "n_pocket": n_pocket,
           "best_recall": float(recall[best])}
    for k in ARMS:
        order = np.argsort(-A[k])
        top = int(order[0])
        row[f"{k}__top_is_best"] = bool(top == best)
        row[f"{k}__EH_top"] = float(EH[top])
        row[f"{k}__recall_top"] = float(recall[top])
        # rank of the truly-best candidate under this arm (1 = perfect)
        row[f"{k}__rank_of_best"] = int(np.where(order == best)[0][0]) + 1
        row[f"{k}__rho_recall"] = float(spearmanr(A[k], recall).statistic)
    # the decisive one: CTQW's candidate ordering with proximity removed
    r = rank_resid(A["ctqw_mean"], prox)
    row["ctqw_resid__rho_recall"] = float(spearmanr(r, recall).statistic)
    row["ctqw_resid__rank_of_best"] = int(np.where(np.argsort(-r) == best)[0][0]) + 1
    row["rho_ctqw_prox"] = float(spearmanr(A["ctqw_mean"], prox).statistic)
    row["rho_ctqw_size"] = float(spearmanr(A["ctqw_mean"], A["n_res"]).statistic)
    row["random_EH"] = float(EH.mean())
    row["random_rank_of_best"] = (len(cands) + 1) / 2.0
    return row


def main() -> int:
    # t0242.prep resolves targets through its module-level CAND dict; the
    # frozen set must be loaded into it first, exactly as TASK-0282's own
    # main() does (that step is in main, not in build_target).
    cfg = yaml.safe_load(t0282.FROZEN_CONFIG.read_text())["targets"]
    for d in t0282.DROPPED:
        cfg.pop(d, None)
    t0282.t0242.CAND = cfg
    targets = [t for t in cfg if t in t0282.CM]
    _log(f"{len(targets)} frozen-set targets (cluster-mapped)")
    rows = []
    for t in targets:
        try:
            d = t0282.build_target(t)
        except Exception as e:
            _log(f"  {t}: ERROR {type(e).__name__}: {str(e)[:60]}")
            continue
        if "error" in d:
            _log(f"  {t}: skip -- {d['error']}")
            continue
        r = evaluate(t, d)
        if r is None:
            _log(f"  {t}: skip -- no candidate recalls the true pocket")
            continue
        rows.append(r)
        _log(f"  {t}: {r['n_cands']:3d} cands | ctqw rank-of-best "
             f"{r['ctqw_mean__rank_of_best']:3d} | prox {r['prox_min_euclid__rank_of_best']:3d} "
             f"| rho(ctqw,prox)={r['rho_ctqw_prox']:+.2f}")

    if not rows:
        _log("no usable targets")
        return 1

    print("\n" + "=" * 78)
    print(f"REVERSE-SEEDED POCKET RANKING  (n = {len(rows)} targets)")
    print("=" * 78)
    print(f"\n{'arm':<18}{'top-1 hit':>11}{'med rank':>10}{'mean EH':>10}{'med rho':>10}")
    for k in ARMS:
        hit = np.mean([r[f"{k}__top_is_best"] for r in rows])
        rk = np.median([r[f"{k}__rank_of_best"] for r in rows])
        eh = np.mean([r[f"{k}__EH_top"] for r in rows])
        rho = np.median([r[f"{k}__rho_recall"] for r in rows])
        print(f"{k:<18}{hit:>10.1%}{rk:>10.1f}{eh:>10.4f}{rho:>+10.3f}")
    rnd_rk = np.median([r["random_rank_of_best"] for r in rows])
    rnd_eh = np.mean([r["random_EH"] for r in rows])
    print(f"{'random':<18}{'--':>10} {rnd_rk:>9.1f}{rnd_eh:>10.4f}{0.0:>+10.3f}")

    print("\n--- the decisive test: CTQW ordering with proximity removed ---")
    raw = np.array([r["ctqw_mean__rho_recall"] for r in rows])
    res = np.array([r["ctqw_resid__rho_recall"] for r in rows])
    print(f"  median rho(ctqw, recall)              raw {np.median(raw):+.4f}")
    print(f"  median rho(ctqw|proximity, recall)  resid {np.median(res):+.4f}")
    for nm, v in (("raw", raw), ("residualised", res)):
        p = wilcoxon(v).pvalue if len(v) > 5 else float("nan")
        print(f"    {nm:<14} vs 0: Wilcoxon p = {p:.4f}")
    print(f"\n  median rho(ctqw, proximity) = "
          f"{np.median([r['rho_ctqw_prox'] for r in rows]):+.3f}")
    print(f"  median rho(ctqw, size)      = "
          f"{np.median([r['rho_ctqw_size'] for r in rows]):+.3f}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "reverse_seeded_pocket_ranking.json").write_text(
        json.dumps({"n": len(rows), "rows": rows}, indent=1))
    print(f"\nwritten -> {OUT}/reverse_seeded_pocket_ranking.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
