"""TASK-0305 -- does OUR detection find ASBench's allosteric sites?

[[TASK-0304]] established that ASBench's own annotations give us, for 118
structures, both the **active site** (a seed) and the **allosteric site**
(ground truth) — the two things our pipeline normally has to derive. That
makes ASBench a *cleaner* test bed than our own benchmark: no apo/holo
pairing, no `detect_active_site` ([[TASK-0289]]), no `holo_pocket_mask`,
no chain-agnostic parsing ([[TASK-0297]]/[[TASK-0298]]). Every labelling
defect this register has found is bypassed, because the labels are theirs.

So this is the fairest available test of the scoring operators themselves,
on a cohort ~9x our independent-cluster count.

ARMS (residue-level, the register's own P@5 metric):
  ctqw          time-averaged CTQW from `build_H_new`, seeded at the
                annotated active site -- our actual quantum arm
  hop_far       farthest-by-BFS-hops from the seed (the "distal" prior)
  hop_near      nearest-by-hops, excluding the seed itself
  msf           GNM mean-square fluctuation (flexibility)
  degree        inverse contact degree (exposed/loose residues first)
  random        expected precision of a random draw = |truth| / |rankable|

Seed residues are excluded from ranking in every arm, matching our own
pipeline's convention.

Run: ../.venv/bin/python3 scripts/task0305_our_detection_on_asbench.py
"""
import sys, json, re, warnings
from pathlib import Path
from collections import defaultdict
import numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0, 'src'); sys.path.insert(0, 'scripts'); sys.path.insert(0, '..')
from backend.data_layer import fetch
from allostery.hamiltonians import build_H_new, contact_matrix
from allostery.propagators import time_averaged_ctqw_converged
from allostery.baselines import hop_from_seed
from allostery.potentials import gnm_context
from allostery.labels import terminal_mask

OUT = Path("results/tasks/0305_asbench_detection")
ANN = json.load(open("results/tasks/0304_asbench_casbench/asbench_annotations.json"))
MAXN = 3000          # residues; guards the O(N^3) eigendecomposition
K = 5

_ALLO = re.compile(r'^([A-Z]{2,3})\s*(-?\d+)([A-Za-z]?)\s+(\w)$')


def parse_allo(t):
    m = _ALLO.match(t.strip())
    if m:
        return (m.group(4), int(m.group(2)))
    m = re.match(r'^([A-Z]{2,3})(-?\d+)\s+(\w)$', t.strip())
    return (m.group(3), int(m.group(2))) if m else None


def parse_act(t):
    m = re.match(r'^(\w)(-?\d+)$', t.strip())
    return (m.group(1), int(m.group(2))) if m else None


def ca_model(pdb_id):
    """Cα coords + B-factors, keyed (chain, resnum), deposited order."""
    keys, xyz, bf = [], [], []
    seen = set()
    for line in Path(fetch(pdb_id)).read_text().splitlines():
        if not line.startswith("ATOM") or line[12:16].strip() != "CA":
            continue
        alt = line[16]
        if alt not in (" ", "A"):
            continue
        try:
            k = (line[21], int(line[22:26]))
            if k in seen:
                continue
            seen.add(k); keys.append(k)
            xyz.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
            bf.append(float(line[60:66]) if line[60:66].strip() else 0.0)
        except ValueError:
            continue
    return keys, np.asarray(xyz, float), np.asarray(bf, float)


def precision_at_k(score, truth_mask, seed_mask, elig, k=K):
    """Fraction of the top-k RANKABLE residues that are true-site residues.
    Rankable excludes the seed AND the terminal 5% at each end -- the same
    eligibility convention `allostery.labels.terminal_mask` enforces in our
    own pipeline. Without it, `msf` and `degree` rank flexible, loosely
    packed termini first and every arm is handicapped against a metric that
    does not exclude them."""
    rankable = elig & ~seed_mask
    idx = np.where(rankable)[0]
    if len(idx) < k or truth_mask[rankable].sum() == 0:
        return None
    order = idx[np.argsort(-score[idx], kind="stable")]
    return float(truth_mask[order[:k]].sum()) / k


def main():
    rows, skipped = [], []
    for i, rec in enumerate(ANN):
        pdb = rec["pdb"].split("_")[0]
        try:
            keys, xyz, bf = ca_model(pdb)
        except Exception as ex:
            skipped.append((rec["pdb"], f"fetch:{type(ex).__name__}")); continue
        n = len(keys)
        if n == 0 or n > MAXN:
            skipped.append((rec["pdb"], f"N={n}")); continue
        pos = {k: j for j, k in enumerate(keys)}
        seed = sorted({pos[k] for k in (parse_act(t) for t in rec["active_residues"])
                       if k in pos})
        truth = sorted({pos[k] for k in (parse_allo(t) for t in rec["allosteric_residues"])
                        if k in pos})
        if len(seed) == 0 or len(truth) == 0:
            skipped.append((rec["pdb"], f"seed={len(seed)} truth={len(truth)}")); continue
        sm = np.zeros(n, bool); sm[seed] = True
        tm = np.zeros(n, bool); tm[truth] = True
        tm_eff = tm & ~sm                      # truth residues that are not the seed
        if tm_eff.sum() == 0:
            skipped.append((rec["pdb"], "truth ⊆ seed")); continue
        try:
            H = build_H_new(xyz, bf, cutoff=8.0)
            ctqw = time_averaged_ctqw_converged(H, source=np.asarray(seed), coherent=False)
            hop = hop_from_seed(xyz, np.asarray(seed), cutoff=8.0)   # negated distance
            ctx = gnm_context(xyz, cutoff=8.0)
        except Exception as ex:
            skipped.append((rec["pdb"], f"score:{type(ex).__name__}")); continue
        elig = ~terminal_mask(n, 0.05)
        arms = {"ctqw": np.nan_to_num(ctqw), "hop_far": -hop, "hop_near": hop,
                "msf": ctx["msf"], "degree": -ctx["degree"]}
        r = dict(pdb=rec["pdb"], protein=rec["protein"], N=n,
                 n_seed=len(seed), n_truth=int(tm_eff.sum()))
        ok = True
        for a, s in arms.items():
            p = precision_at_k(s, tm_eff, sm, elig)
            if p is None:
                ok = False; break
            r[a] = p
        if not ok:
            skipped.append((rec["pdb"], "P@5 undefined")); continue
        rk = elig & ~sm
        r["random"] = float((tm_eff & rk).sum()) / float(rk.sum())
        rows.append(r)
        if (i + 1) % 20 == 0:
            print(f"  ... {i+1}/{len(ANN)}  (kept {len(rows)})", flush=True)

    ARMS = ["ctqw", "hop_far", "hop_near", "msf", "degree", "random"]
    print("\n" + "=" * 70)
    print(f"OUR detection on ASBench — residue-level P@{K}, their annotations")
    print("=" * 70)
    print(f"  scored {len(rows)} structures   ({len(skipped)} skipped)")
    print(f"\n  {'arm':<12}{'mean P@5':>10}{'median':>9}{'>0 on':>10}{'hit rate':>10}")
    summ = {}
    for a in ARMS:
        v = np.array([r[a] for r in rows])
        nz = int((v > 0).sum())
        summ[a] = dict(mean=float(v.mean()), median=float(np.median(v)),
                       n_nonzero=nz, frac_nonzero=nz / len(v))
        print(f"  {a:<12}{v.mean():>10.4f}{np.median(v):>9.3f}{nz:>7}/{len(v)}{nz/len(v):>10.1%}")
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(dict(rows=rows, skipped=skipped, summary=summ, k=K, maxN=MAXN),
              open(OUT / "asbench_detection.json", "w"), indent=1)
    print(f"\n  written -> {OUT}/asbench_detection.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
