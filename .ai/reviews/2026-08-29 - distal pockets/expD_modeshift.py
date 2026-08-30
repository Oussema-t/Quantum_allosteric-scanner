"""EXPERIMENT D -- APOP-style ENM global mode shift, with the size control the
register's history demands.

Handover section 6 item 5: the discrimination review reports 92/104 top-3 for
"global mode frequency shift + local hydrophobicity", and names mode shift as
the component that might work in the CRYPTIC stratum, where hydrophobic density
provably does not.

Method (APOP): fill a candidate pocket with dummy nodes at its fpocket
alpha-sphere centres, rebuild the elastic network, and measure how much the
softest global modes stiffen. A pocket whose occupancy perturbs the global
dynamics is the allosteric candidate.

THE CONFOUND, stated up front: adding nodes always stiffens the network, and a
bigger pocket adds more nodes. That is exactly the failure mode handover
section 2 found in volume/SASA under max-recall truth. So two variants are run:

  raw  -- every alpha-sphere centre becomes a node (APOP as published)
  kfix -- alpha spheres k-means-reduced to a FIXED k nodes for every pocket,
          so pocket size cannot enter through the node count

If only `raw` works, the result is a size artifact and should be discarded.

Truth = max-Jaccard candidate, detection Jaccard >= 0.3, per handover section 2.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import chi2

UP = Path("/mnt/user-data/uploads")
MATCH = json.loads((UP / "matched.json").read_text())
EXPA = json.loads((UP / "expA_fpocket.json").read_text())
HYD = json.loads((UP / "hyd_cache.json").read_text())
FP = json.loads(Path("/home/claude/fp_full.json").read_text())
APO = Path("/home/claude/apo")

RC = 7.3        # standard GNM cutoff, Angstrom
NMODES = 10     # number of softest non-trivial modes compared
KFIX = 8        # fixed dummy-node budget for the size-controlled variant


def ca_coords(target):
    """C-alpha coordinates, in file order, from the regenerated apo PDB."""
    pts = []
    for line in (APO / f"{target}_apo.pdb").read_text().splitlines():
        if line.startswith("ATOM") and line[12:16].strip() == "CA":
            pts.append([float(line[30:38]), float(line[38:46]),
                        float(line[46:54])])
    return np.array(pts)


def kirchhoff(coords, rc=RC):
    d = np.linalg.norm(coords[:, None, :] - coords[None, :, :], axis=-1)
    A = ((d < rc) & (d > 0)).astype(float)
    return np.diag(A.sum(1)) - A


def soft_eigs(coords, m=NMODES):
    g = kirchhoff(coords)
    w = np.linalg.eigvalsh(g)
    w = w[w > 1e-8]
    return w[:m]


def kmeans(pts, k, iters=25, seed=0):
    pts = np.asarray(pts, float)
    if len(pts) <= k:
        return pts
    rng = np.random.default_rng(seed)
    c = pts[rng.choice(len(pts), k, replace=False)]
    for _ in range(iters):
        d = np.linalg.norm(pts[:, None, :] - c[None, :, :], axis=-1)
        lab = d.argmin(1)
        new = np.array([pts[lab == j].mean(0) if (lab == j).any() else c[j]
                        for j in range(k)])
        if np.allclose(new, c):
            break
        c = new
    return c


def mode_shift(base_coords, base_eigs, dummies):
    if len(dummies) == 0:
        return np.nan
    allc = np.vstack([base_coords, np.asarray(dummies, float)])
    w = soft_eigs(allc)
    n = min(len(w), len(base_eigs))
    if n == 0:
        return np.nan
    return float(np.mean((w[:n] - base_eigs[:n]) / base_eigs[:n]))


def fisher(ps):
    ps = np.clip(np.asarray(ps, float), 1e-12, 1.0)
    return float(chi2.sf(-2 * np.log(ps).sum(), 2 * len(ps)))


def main():
    setting = sys.argv[1] if len(sys.argv) > 1 else ""
    rows = []
    print("=" * 100)
    print(f"EXPERIMENT D -- ENM global mode shift  [candidate setting: "
          f"{setting or 'default'}]")
    print("=" * 100)
    print(f"  GNM cutoff {RC} A, {NMODES} softest modes, kfix={KFIX} dummy nodes\n")
    print(f"  {'target':<20}{'strat':<8}{'n':>4}{'det':>5}{'Jac':>6}"
          f"{'pct_raw':>9}{'pct_kfix':>10}{'pct_hyd':>9}{'r_raw':>7}"
          f"{'r_kfix':>8}{'r_hyd':>7}")
    for t in MATCH:
        pk = FP[f"{t}|{setting}"]
        n_site = MATCH[t]["n_site"]
        base = ca_coords(t)
        beig = soft_eigs(base)

        cands = []
        for p in pk:
            rn = set(p["resnums"])
            ov = int(round(HYD[f"{t}|apo|{setting}"][
                [q["id"] for q in HYD[f"{t}|apo|{setting}"]].index(p["id"])
            ]["_recall"] * n_site))
            jac = ov / (len(rn) + n_site - ov) if (len(rn) + n_site - ov) else 0.0
            v = p["vert"]
            cands.append({
                "id": p["id"], "jac": jac, "nvert": len(v),
                "raw": mode_shift(base, beig, v),
                "kfix": mode_shift(base, beig, kmeans(v, KFIX)) if v else np.nan,
                "hyd": float(p.get("mean_local_hydrophobic_density") or 0.0),
                "vol": float(p.get("volume") or 0.0),
            })
        truth = max(cands, key=lambda c: c["jac"])
        det = truth["jac"] >= 0.3

        def pct(key):
            vals = [c[key] for c in cands if not np.isnan(c[key])]
            tv = truth[key]
            if np.isnan(tv) or not vals:
                return np.nan, np.nan
            r = sum(1 for v in vals if v >= tv)
            return r / len(vals), r

        p_raw, r_raw = pct("raw")
        p_kf, r_kf = pct("kfix")
        p_hy, r_hy = pct("hyd")
        rows.append({"t": t, "strat": MATCH[t]["stratum"],
                     "cluster": EXPA[t]["apo_pdb"].upper(), "det": det,
                     "n": len(cands), "p_raw": p_raw, "p_kfix": p_kf,
                     "p_hyd": p_hy, "r_raw": r_raw, "r_kfix": r_kf,
                     "r_hyd": r_hy,
                     "rho_raw_vol": float(np.corrcoef(
                         [c["raw"] for c in cands], [c["vol"] for c in cands])[0, 1]),
                     "rho_kfix_vol": float(np.corrcoef(
                         [c["kfix"] for c in cands], [c["vol"] for c in cands])[0, 1]),
                     "cands": cands})
        print(f"  {t:<20}{MATCH[t]['stratum']:<8}{len(cands):>4}"
              f"{'yes' if det else 'NO':>5}{truth['jac']:>6.2f}"
              f"{p_raw:>9.3f}{p_kf:>10.3f}{p_hy:>9.3f}"
              f"{r_raw:>7.0f}{r_kf:>8.0f}{r_hy:>7.0f}", flush=True)

    print("\n  Correlation of mode shift with pocket volume (the confound):")
    print(f"    raw  : median rho = "
          f"{np.median([r['rho_raw_vol'] for r in rows]):.3f}")
    print(f"    kfix : median rho = "
          f"{np.median([r['rho_kfix_vol'] for r in rows]):.3f}")

    print(f"\n  {'stratum':<10}{'K':>3}{'n_det':>6}{'raw #1':>8}{'kfix #1':>9}"
          f"{'hyd #1':>8}{'med raw':>9}{'med kfix':>10}{'p raw':>9}{'p kfix':>9}")
    for strat in ("open", "cryptic", "ALL"):
        sub = [r for r in rows if r["det"] and
               (strat == "ALL" or r["strat"] == strat)]
        if not sub:
            continue
        byc = defaultdict(list)
        for r in sub:
            byc[r["cluster"]].append(r)
        praw = [float(np.mean([x["p_raw"] for x in v])) for v in byc.values()]
        pkf = [float(np.mean([x["p_kfix"] for x in v])) for v in byc.values()]
        print(f"  {strat:<10}{len(byc):>3}{len(sub):>6}"
              f"{sum(r['r_raw'] == 1 for r in sub):>8}"
              f"{sum(r['r_kfix'] == 1 for r in sub):>9}"
              f"{sum(r['r_hyd'] == 1 for r in sub):>8}"
              f"{np.median([r['p_raw'] for r in sub]):>9.3f}"
              f"{np.median([r['p_kfix'] for r in sub]):>10.3f}"
              f"{fisher(praw):>9.3g}{fisher(pkf):>9.3g}")

    Path(f"/home/claude/expD_{setting or 'default'}.json").write_text(
        json.dumps([{k: v for k, v in r.items() if k != "cands"} for r in rows],
                   indent=1))

    # Parameter-free combination with hydrophobic density
    print("\n  APOP combination, parameter-free Borda(mode shift, hyd density):")
    for variant in ("raw", "kfix"):
        hits = {"hyd": 0, "combo": 0, "n": 0}
        for r in rows:
            if not r["det"]:
                continue
            c = [x for x in r["cands"] if not np.isnan(x[variant])]
            if not c:
                continue
            om = sorted(c, key=lambda x: -x[variant])
            oh = sorted(c, key=lambda x: -x["hyd"])
            rm = {id(x): i for i, x in enumerate(om)}
            rh = {id(x): i for i, x in enumerate(oh)}
            truth = max(c, key=lambda x: x["jac"])
            tb = rm[id(truth)] + rh[id(truth)]
            rank = sum(1 for x in c if rm[id(x)] + rh[id(x)] <= tb)
            hits["n"] += 1
            hits["hyd"] += r["r_hyd"] == 1
            hits["combo"] += rank == 1
        print(f"    {variant:<5} hyd alone {hits['hyd']}/{hits['n']}   "
              f"Borda(mode,hyd) {hits['combo']}/{hits['n']}")


if __name__ == "__main__":
    main()
