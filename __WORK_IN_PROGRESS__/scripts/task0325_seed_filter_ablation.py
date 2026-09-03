#!/usr/bin/env python3
"""TASK-0325 -- does filtering the SEED SET before the walk rescue reverse-CTQW?

A collaborator proposed a v2 of [[TASK-0320]]: instead of letting the CTQW rank
all of fpocket's candidates, use a consensus of pocket predictors
(fpocket n PASSer, with PocketMiner as a third signal, 2-of-3 majority) to
choose WHICH pockets the walk is seeded from.

WHY THE WALK CANNOT BE THE THING THAT IMPROVES

[[TASK-0320]] established, and verified to machine precision, that for candidate
P and active site A under the seed-independent real-symmetric `H_new`:

    transfer(P->A) = |A| * mean_{i in P} p_A(i)

Restricting the seed set changes WHICH candidates are scored. It cannot change
any p_A(i), so every surviving candidate keeps a bit-identical CTQW score. Any
gain from the v2 pipeline is therefore attributable to the FILTER, and the
honest comparison is not "v2 vs TASK-0320" but, within the surviving set,

    filter + CTQW   vs   filter + fpocket   vs   filter + proximity   vs
    filter + size   vs   filter + random.

Restriction of range is real, though: correlations can change on a subpopulation
even when no score does. That is an empirical question, and this script answers
it rather than arguing it.

WHAT THE FILTER IS HERE. PASSer was never built (`ALGORITHM_REGISTER.md` sec. F
rates it 3, "lower priority"; still an open box in `PLAN.md`), and PocketMiner
([[TASK-0269]]) ran on 18 crypticity-cohort targets, none of them in ASBench. So
the literal 2-of-3 gate cannot be run on this cohort today. What is simulated is
the CLASS of gate: keep the top-K candidates by fpocket druggability. This is
deliberately GENEROUS to the proposal -- it is a real druggability consensus's
main axis, and it is applied with perfect knowledge of nothing but the filter's
own score.

Run: ../.venv/bin/python3 scripts/task0325_seed_filter_ablation.py
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import rankdata, spearmanr, wilcoxon

_ROOT = Path(__file__).resolve().parents[1]
SRC = _ROOT / "results/tasks/0320b_reverse_seeded_asbench/reverse_seeded_asbench.json"
OUT = _ROOT / "results/tasks/0325_seed_filter_ablation"

ARMS = ["ctqw", "resid", "prox", "drug", "nres"]
RNG = np.random.default_rng(0)


def rank_resid(x, z):
    """Residualise rank(x) on rank(z) by OLS -- TASK-0310's definition."""
    rx, rz = rankdata(x), rankdata(z)
    if np.std(rz) < 1e-12:
        return rx - rx.mean()
    b = np.cov(rx, rz, bias=True)[0, 1] / np.var(rz)
    return rx - b * rz


def survivors(drug: np.ndarray, k) -> np.ndarray:
    """Indices kept by a top-K druggability gate. k='half' -> top 50%."""
    n = len(drug)
    keep = max(1, n // 2) if k == "half" else min(int(k), n)
    return np.argsort(-drug)[:keep]


def cluster_wilcoxon(per_protein: dict) -> tuple:
    v = np.array([np.median(x) for x in per_protein.values()], float)
    v = v[np.isfinite(v)]
    if len(v) < 3 or np.allclose(v, 0):
        return float("nan"), float("nan"), 0, 0
    return (float(np.median(v)), float(wilcoxon(v).pvalue),
            int(np.sum(v > 0)), int(len(v)))


def main() -> int:
    rows = json.load(open(SRC))["rows"]
    need = ("_recall", "_ctqw", "_prox", "_drug")
    missing = [r["pdb"] for r in rows if not all(k in r for k in need)]
    if missing:
        print(f"FATAL: {len(missing)} rows lack per-candidate dumps "
              f"(e.g. {missing[:3]}). Re-run task0320b first.")
        return 1

    print("=" * 78)
    print("SEED-SET FILTER ABLATION -- does the gate or the walk do the work?")
    print(f"n = {len(rows)} structures / "
          f"{len({r['protein'] for r in rows})} proteins")
    print("=" * 78)

    for k in (3, 5, "half", "none"):
        hits = defaultdict(list)
        retained, sizes, rand = [], [], []
        rho_by_prot = {a: defaultdict(list) for a in ARMS}

        for r in rows:
            rec = np.asarray(r["_recall"], float)
            sc = {"ctqw": np.asarray(r["_ctqw"], float),
                  "prox": np.asarray(r["_prox"], float),
                  "drug": np.asarray(r["_drug"], float),
                  "nres": np.asarray(r["_nres"], float)}
            sc["resid"] = rank_resid(sc["ctqw"], sc["prox"])
            best = int(np.argmax(rec))
            if rec[best] <= 0:
                continue

            S = (np.arange(len(rec)) if k == "none"
                 else survivors(sc["drug"], k))
            kept = best in set(S.tolist())
            retained.append(kept)
            sizes.append(len(S))
            # analytic random baseline, conditioned on the same filter
            rand.append((1.0 / len(S)) if kept else 0.0)

            for a in ARMS:
                s = sc[a][S]
                hits[a].append(bool(kept and S[int(np.argmax(s))] == best))
                if len(S) >= 4:
                    rr = spearmanr(s, rec[S]).statistic
                    if np.isfinite(rr):
                        rho_by_prot[a][r["protein"]].append(float(rr))

        n = len(retained)
        tag = "NO FILTER (TASK-0320b)" if k == "none" else f"top-{k} by druggability"
        print(f"\n--- {tag} ---")
        print(f"  candidates kept      : median {np.median(sizes):.0f} "
              f"of median {np.median([len(r['_recall']) for r in rows]):.0f}")
        print(f"  true pocket retained : {100*np.mean(retained):.1f}% "
              f"of {n} structures   <- the filter's own ceiling")
        print(f"  {'arm':<22}{'top-1 hit':>10}{'med rho':>10}"
              f"{'pos':>8}{'cluster p':>12}")
        print(f"  {'random (same gate)':<22}{100*np.mean(rand):>9.1f}%"
              f"{0.0:>+10.3f}{'--':>8}{'--':>12}")
        for a in ARMS:
            m, p, pos, nn = cluster_wilcoxon(rho_by_prot[a])
            print(f"  {a:<22}{100*np.mean(hits[a]):>9.1f}%{m:>+10.3f}"
                  f"{f'{pos}/{nn}':>8}{p:>12.4g}")

    OUT.mkdir(parents=True, exist_ok=True)
    print(f"\n(summary printed only; source data {SRC.name} is the artifact)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
