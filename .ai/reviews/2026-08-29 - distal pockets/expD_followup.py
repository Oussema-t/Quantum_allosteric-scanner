"""Two follow-ups the register's history makes mandatory before mode shift can
be believed.

1. COMPLEMENTARITY. If mode shift and hydrophobic density rank candidates the
   same way, mode shift is not a second signal and APOP's "combine them" claim
   has nothing to combine. Measured as within-target Spearman rho.

2. VOLUME RESIDUALISATION. kfix fixes the node COUNT but not the node SPREAD, so
   a bigger pocket still reaches more of the network. The strict test is to
   regress mode shift on volume WITHIN each target (on ranks) and score the true
   pocket on the residual. If the signal is really geometry-of-size, it dies
   here -- exactly as volume and SASA died under max-Jaccard truth.
"""
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import chi2, spearmanr

UP = Path("/mnt/user-data/uploads")
MATCH = json.loads((UP / "matched.json").read_text())
EXPA = json.loads((UP / "expA_fpocket.json").read_text())
HYD = json.loads((UP / "hyd_cache.json").read_text())
FP = json.loads(Path("/home/claude/fp_full.json").read_text())
APO = Path("/home/claude/apo")

RC, NMODES, KFIX = 7.3, 10, 8


def ca_coords(t):
    pts = []
    for line in (APO / f"{t}_apo.pdb").read_text().splitlines():
        if line.startswith("ATOM") and line[12:16].strip() == "CA":
            pts.append([float(line[30:38]), float(line[38:46]),
                        float(line[46:54])])
    return np.array(pts)


def soft_eigs(c):
    d = np.linalg.norm(c[:, None, :] - c[None, :, :], axis=-1)
    A = ((d < RC) & (d > 0)).astype(float)
    w = np.linalg.eigvalsh(np.diag(A.sum(1)) - A)
    return w[w > 1e-8][:NMODES]


def kmeans(pts, k, iters=25):
    pts = np.asarray(pts, float)
    if len(pts) <= k:
        return pts
    rng = np.random.default_rng(0)
    c = pts[rng.choice(len(pts), k, replace=False)]
    for _ in range(iters):
        lab = np.linalg.norm(pts[:, None] - c[None], axis=-1).argmin(1)
        new = np.array([pts[lab == j].mean(0) if (lab == j).any() else c[j]
                        for j in range(k)])
        if np.allclose(new, c):
            break
        c = new
    return c


def fisher(ps):
    ps = np.clip(np.asarray(ps, float), 1e-12, 1.0)
    return float(chi2.sf(-2 * np.log(ps).sum(), 2 * len(ps)))


def ranks(x):
    x = np.asarray(x, float)
    return x.argsort().argsort().astype(float)


def main():
    for setting in ("", "-m_2.8"):
        print("=" * 92)
        print(f"MODE SHIFT FOLLOW-UPS  [setting: {setting or 'default'}]")
        print("=" * 92)
        rows = []
        print(f"  {'target':<20}{'strat':<8}{'det':>4}{'rho(mode,hyd)':>15}"
              f"{'pct_kfix':>10}{'pct_resid':>11}{'pct_hyd':>9}")
        for t in MATCH:
            pk = FP[f"{t}|{setting}"]
            cache = HYD[f"{t}|apo|{setting}"]
            rec = {q["id"]: q["_recall"] for q in cache}
            n_site = MATCH[t]["n_site"]
            base = ca_coords(t)
            beig = soft_eigs(base)
            ms, hy, vol, jac = [], [], [], []
            for p in pk:
                v = p["vert"]
                if not v:
                    continue
                allc = np.vstack([base, kmeans(v, KFIX)])
                w = soft_eigs(allc)
                n = min(len(w), len(beig))
                ms.append(float(np.mean((w[:n] - beig[:n]) / beig[:n])))
                hy.append(float(p.get("mean_local_hydrophobic_density") or 0.0))
                vol.append(float(p.get("volume") or 0.0))
                ov = int(round(rec[p["id"]] * n_site))
                rn = len(p["resnums"])
                jac.append(ov / (rn + n_site - ov) if (rn + n_site - ov) else 0.0)
            ms, hy, vol, jac = map(np.array, (ms, hy, vol, jac))
            ti = int(jac.argmax())
            det = jac[ti] >= 0.3
            rho = spearmanr(ms, hy).statistic if len(ms) > 3 else np.nan

            # residualise mode shift on volume, within target, on ranks
            rv, rm = ranks(vol), ranks(ms)
            b = np.polyfit(rv, rm, 1)
            resid = rm - np.polyval(b, rv)

            def pct(a):
                return float((a >= a[ti]).sum() / len(a))

            rows.append({"t": t, "strat": MATCH[t]["stratum"], "det": det,
                         "cluster": EXPA[t]["apo_pdb"].upper(), "rho": rho,
                         "p_kfix": pct(ms), "p_res": pct(resid), "p_hyd": pct(hy)})
            print(f"  {t:<20}{MATCH[t]['stratum']:<8}"
                  f"{'y' if det else 'N':>4}{rho:>15.3f}"
                  f"{pct(ms):>10.3f}{pct(resid):>11.3f}{pct(hy):>9.3f}",
                  flush=True)

        det = [r for r in rows if r["det"]]
        print(f"\n  median within-target rho(mode shift, hyd density) = "
              f"{np.median([r['rho'] for r in rows]):.3f}"
              f"   -> {'largely redundant' if np.median([r['rho'] for r in rows]) > 0.5 else 'largely independent'}")
        print(f"\n  {'stratum':<10}{'K':>3}{'n':>4}{'med kfix':>10}"
              f"{'med resid':>11}{'p kfix':>9}{'p resid':>9}")
        for s in ("open", "cryptic", "ALL"):
            sub = [r for r in det if s == "ALL" or r["strat"] == s]
            if not sub:
                continue
            byc = defaultdict(list)
            for r in sub:
                byc[r["cluster"]].append(r)
            pk_ = [float(np.mean([x["p_kfix"] for x in v])) for v in byc.values()]
            pr_ = [float(np.mean([x["p_res"] for x in v])) for v in byc.values()]
            print(f"  {s:<10}{len(byc):>3}{len(sub):>4}"
                  f"{np.median([r['p_kfix'] for r in sub]):>10.3f}"
                  f"{np.median([r['p_res'] for r in sub]):>11.3f}"
                  f"{fisher(pk_):>9.3g}{fisher(pr_):>9.3g}")
        print()


if __name__ == "__main__":
    main()
