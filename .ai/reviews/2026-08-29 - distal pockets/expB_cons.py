"""EXPERIMENT B, ARMS 2 & 3 -- conservation, now that EBI egress is live.

The register's existing negative result for conservation was a *residue-level*
AUC via added-last Shapley. The pre-registered arms 2/3 ask a different
question: does conservation work as a *pocket-level* filter -- specifically a
NEGATIVE one, since an allosteric drug site should be less conserved than the
catalytic machinery it is being ranked against.

Both questions are answered here, on the same data, so the contrast is direct.

Truth definition: max-JACCARD candidate (HANDOVER 2026-08-30 section 2), because
max-recall rises mechanically with candidate size. Detection = Jaccard >= 0.3.
Overlaps are reconstructed exactly from cached `_recall` x `n_site` (verified
integral to 0 error).

Nothing is fitted. Every ranker is a single fixed field or a parameter-free
Borda sum.
"""
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import chi2

UP = Path("/mnt/user-data/uploads")
HYD = json.loads((UP / "hyd_cache.json").read_text())
MATCH = json.loads((UP / "matched.json").read_text())
EXPA = json.loads((UP / "expA_fpocket.json").read_text())
CONS = json.loads(Path("/home/claude/conservation.json").read_text())

SETTINGS = ["", "-m_2.8"]


def res_cons(target):
    """auth resnum -> conservation, averaged over the chains this target uses.

    fpocket residue numbers are chain-agnostic in the cached runs, so for
    hetero-oligomers one number can carry two different conservation values.
    That ambiguity is measured and reported, not hidden.
    """
    pdb = EXPA[target]["apo_pdb"].upper()
    chains = EXPA[target]["chains"]
    per = defaultdict(list)
    for ch in chains:
        d = CONS.get(pdb, {}).get(ch)
        if not d:
            continue
        for r, v in d["cons"].items():
            per[int(r)].append(v)
    amb = sum(1 for v in per.values() if len(v) > 1 and max(v) - min(v) > 1e-9)
    return {r: float(np.mean(v)) for r, v in per.items()}, amb, len(per)


def build(target, setting):
    key = f"{target}|apo|{setting}"
    pockets = HYD[key]
    n_site = MATCH[target]["n_site"]
    cmap, amb, n_scored = res_cons(target)

    cands = []
    for p in pockets:
        rn = set(p["resnums"])
        ov = int(round(p["_recall"] * n_site))
        jac = ov / (len(rn) + n_site - ov) if (len(rn) + n_site - ov) else 0.0
        cv = [cmap[r] for r in rn if r in cmap]
        cands.append({
            "id": p["id"], "n": len(rn), "ov": ov, "recall": p["_recall"],
            "jaccard": jac,
            "cons": float(np.mean(cv)) if cv else np.nan,
            "cons_cov": len(cv) / max(1, len(rn)),
            "hyd": float(p.get("mean_local_hydrophobic_density") or 0.0),
            "drug": float(p.get("druggability_score") or 0.0),
            "vol": float(p.get("volume") or 0.0),
        })
    return cands, amb, n_scored


def rank_of(cands, truth, key, descending=True):
    """1-based rank of `truth` under `key`; ties counted against us."""
    tv = truth[key]
    if np.isnan(tv):
        return None
    vals = [c[key] for c in cands if not np.isnan(c[key])]
    if descending:
        return sum(1 for v in vals if v >= tv), len(vals)
    return sum(1 for v in vals if v <= tv), len(vals)


def fisher(ps):
    ps = np.clip(np.asarray(ps, float), 1e-12, 1.0)
    stat = -2 * np.log(ps).sum()
    return float(chi2.sf(stat, 2 * len(ps)))


def main():
    clusters = {t: EXPA[t]["apo_pdb"].upper() for t in MATCH}
    print("=" * 96)
    print("EXPERIMENT B ARMS 2/3 -- CONSERVATION AS A POCKET-LEVEL FILTER")
    print("=" * 96)
    print(f"  {len(MATCH)} targets in {len(set(clusters.values()))} apo-structure "
          f"clusters. Truth = max-Jaccard candidate; detection = Jaccard >= 0.3.\n")

    allrows = {}
    for setting in SETTINGS:
        lab = setting or "default"
        rows = []
        print("-" * 96)
        print(f"CANDIDATE SETTING: {lab}")
        print("-" * 96)
        print(f"  {'target':<20}{'strat':<8}{'n':>4}{'det':>5}{'Jac':>6}"
              f"{'cov':>6}{'r_cons_lo':>10}{'r_cons_hi':>10}{'r_hyd':>7}"
              f"{'r_drug':>8}{'pct_cons':>9}")
        for t in MATCH:
            cands, amb, nsc = build(t, setting)
            scored = [c for c in cands if not np.isnan(c["cons"])]
            truth = max(cands, key=lambda x: x["jaccard"])
            det = truth["jaccard"] >= 0.3
            strat = MATCH[t]["stratum"]
            if np.isnan(truth["cons"]):
                print(f"  {t:<20}{strat:<8}{len(cands):>4}"
                      f"{'yes' if det else 'NO':>5}{truth['jaccard']:>6.2f}"
                      f"{0.0:>6.2f}   true pocket has no conservation coverage")
                continue
            r_lo, n_lo = rank_of(cands, truth, "cons", descending=False)
            r_hi, _ = rank_of(cands, truth, "cons", descending=True)
            r_hyd, _ = rank_of(cands, truth, "hyd")
            r_drug, _ = rank_of(cands, truth, "drug")
            pct = r_lo / n_lo
            rows.append({
                "t": t, "strat": strat, "cluster": clusters[t], "det": det,
                "jac": truth["jaccard"], "n": len(cands), "n_scored": n_lo,
                "r_lo": r_lo, "r_hi": r_hi, "r_hyd": r_hyd, "r_drug": r_drug,
                "pct_lo": pct, "cons_cov": truth["cons_cov"], "amb": amb,
                "cands": cands, "truth": truth,
            })
            print(f"  {t:<20}{strat:<8}{len(cands):>4}{'yes' if det else 'NO':>5}"
                  f"{truth['jaccard']:>6.2f}{truth['cons_cov']:>6.2f}"
                  f"{r_lo:>10}{r_hi:>10}{r_hyd:>7}{r_drug:>8}{pct:>9.3f}")
        allrows[setting] = rows
        summarise(rows, lab)

    Path("/home/claude/expB_cons.json").write_text(json.dumps(
        {k: [{kk: vv for kk, vv in r.items() if kk not in ("cands", "truth")}
             for r in v] for k, v in allrows.items()}, indent=1))
    borda(allrows[""])


def summarise(rows, lab):
    print(f"\n  SUMMARY [{lab}] -- detected targets only (a filter cannot rank a "
          f"pocket that was never generated)")
    print(f"  {'stratum':<10}{'n_det':>6}{'cons_lo #1':>12}{'hyd #1':>9}"
          f"{'drug #1':>9}{'med pct_lo':>12}{'Fisher p (lo)':>15}"
          f"{'Fisher p (hi)':>15}")
    for strat in ("open", "cryptic", "ALL"):
        sub = [r for r in rows if r["det"] and
               (strat == "ALL" or r["strat"] == strat)]
        if not sub:
            continue
        p_lo = [r["r_lo"] / r["n_scored"] for r in sub]
        p_hi = [r["r_hi"] / r["n_scored"] for r in sub]
        print(f"  {strat:<10}{len(sub):>6}"
              f"{sum(r['r_lo'] == 1 for r in sub):>12}"
              f"{sum(r['r_hyd'] == 1 for r in sub):>9}"
              f"{sum(r['r_drug'] == 1 for r in sub):>9}"
              f"{np.median(p_lo):>12.3f}{fisher(p_lo):>15.3g}"
              f"{fisher(p_hi):>15.3g}")

    # cluster-collapsed version: one value per apo structure
    print(f"\n  cluster-collapsed (one mean percentile per apo structure):")
    for strat in ("open", "cryptic", "ALL"):
        sub = [r for r in rows if r["det"] and
               (strat == "ALL" or r["strat"] == strat)]
        if not sub:
            continue
        byc = defaultdict(list)
        for r in sub:
            byc[r["cluster"]].append(r["r_lo"] / r["n_scored"])
        vals = [float(np.mean(v)) for v in byc.values()]
        print(f"    {strat:<10}K={len(vals):<3} median pct_lo={np.median(vals):.3f}"
              f"  Fisher p(lo)={fisher(vals):.3g}"
              f"  Fisher p(hi)={fisher([1 - v for v in vals]):.3g}")
    print()


def borda(rows):
    """Arm 3, parameter-free: does adding conservation as a negative filter
    improve on hydrophobic density alone? Borda = rank_hyd + rank_cons_ascending.
    No weights, no threshold, nothing tuned."""
    print("=" * 96)
    print("ARM 3 -- conservation as a NEGATIVE filter on top of arm 1 (default "
          "candidates)")
    print("=" * 96)
    print(f"  {'target':<20}{'strat':<8}{'r_hyd':>7}{'r_borda':>9}{'delta':>7}")
    hits = {"hyd": 0, "borda": 0, "n": 0}
    for r in rows:
        if not r["det"]:
            continue
        cands = [c for c in r["cands"] if not np.isnan(c["cons"])]
        hyd_order = sorted(cands, key=lambda c: -c["hyd"])
        cons_order = sorted(cands, key=lambda c: c["cons"])
        rh = {id(c): i for i, c in enumerate(hyd_order)}
        rc = {id(c): i for i, c in enumerate(cons_order)}
        borda_score = {id(c): rh[id(c)] + rc[id(c)] for c in cands}
        truth = r["truth"]
        tb = borda_score[id(truth)] if id(truth) in borda_score else None
        if tb is None:
            continue
        r_borda = sum(1 for c in cands if borda_score[id(c)] <= tb)
        hits["n"] += 1
        hits["hyd"] += r["r_hyd"] == 1
        hits["borda"] += r_borda == 1
        print(f"  {r['t']:<20}{r['strat']:<8}{r['r_hyd']:>7}{r_borda:>9}"
              f"{r['r_hyd'] - r_borda:>7:+d}" if False else
              f"  {r['t']:<20}{r['strat']:<8}{r['r_hyd']:>7}{r_borda:>9}"
              f"{r['r_hyd'] - r_borda:>+7d}")
    print(f"\n  rank-1 with hydrophobic density alone : {hits['hyd']}/{hits['n']}")
    print(f"  rank-1 with Borda(hyd, low-conservation): {hits['borda']}/{hits['n']}")


if __name__ == "__main__":
    main()
