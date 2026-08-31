"""TASK-0308 -- attribution across cohort sizes: what is explained, by what,
and how much headroom remains.

The register's own attribution ([[TASK-0263]]/[[TASK-0275]]) was computed
on 13 clusters with AUC: potential terms 0.751, CTQW 0.575. The obvious
question is whether that ordering is a small-cohort artefact. ASBench
gives 108 structures with the field's own seed and truth annotations.

METRIC. Per-structure ROC AUC for ranking the annotated allosteric
residues above every other eligible residue (seed and terminal residues
excluded, matching this repo's own convention). AUC is used rather than
[[TASK-0305]]'s P@5 because P@5 is almost all zeros at this site size --
too sparse a substrate for attribution.

SHARE OF AVAILABLE SIGNAL. AUC 0.5 is chance and 1.0 is perfect, so
    share = (AUC - 0.5) / 0.5
is the fraction of the available ranking signal an arm captures. The
remainder is headroom: signal that exists in the labels and that nothing
here explains.

Run: ../.venv/bin/python3 scripts/task0308_attribution_scaling.py
"""
import sys, json, re, struct, zlib, urllib.request, warnings
from pathlib import Path
from collections import defaultdict
import numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0, 'src'); sys.path.insert(0, 'scripts'); sys.path.insert(0, '..')
from sklearn.metrics import roc_auc_score
from backend.data_layer import fetch
from allostery.hamiltonians import build_H_new
from allostery.propagators import time_averaged_ctqw_converged
from allostery.baselines import hop_from_seed
from allostery.potentials import gnm_context
from allostery.labels import terminal_mask

OUT = Path("results/tasks/0308_attribution_scaling")
ANN = json.load(open("results/tasks/0304_asbench_casbench/asbench_annotations.json"))
KEEP = {r["pdb"] for r in json.load(
    open("results/tasks/0305_asbench_detection/asbench_detection.json"))["rows"]}

_A = re.compile(r'^([A-Z]{2,3})\s*(-?\d+)([A-Za-z]?)\s+(\w)$')
def pa(t):
    m = _A.match(t.strip())
    if m: return (m.group(4), int(m.group(2)))
    m = re.match(r'^([A-Z]{2,3})(-?\d+)\s+(\w)$', t.strip())
    return (m.group(3), int(m.group(2))) if m else None
def pact(t):
    m = re.match(r'^(\w)(-?\d+)$', t.strip())
    return (m.group(1), int(m.group(2))) if m else None

def ca(pdb):
    keys, xyz, bf, seen = [], [], [], set()
    for L in Path(fetch(pdb)).read_text().splitlines():
        if not L.startswith("ATOM") or L[12:16].strip() != "CA": continue
        if L[16] not in (" ", "A"): continue
        try:
            k = (L[21], int(L[22:26]))
            if k in seen: continue
            seen.add(k); keys.append(k)
            xyz.append((float(L[30:38]), float(L[38:46]), float(L[46:54])))
            bf.append(float(L[60:66]) if L[60:66].strip() else 0.0)
        except ValueError: continue
    return keys, np.asarray(xyz, float), np.asarray(bf, float)

# --- their propensity, from the figshare archive by range request ---
_ZT = Path('/tmp/zt.bin')
if not _ZT.exists():
    _r = urllib.request.Request("https://ndownloader.figshare.com/files/31337710",
                                headers={'Range': 'bytes=-2000000'})
    _ZT.write_bytes(urllib.request.urlopen(_r, timeout=300).read())
_zt = _ZT.read_bytes()
ENTS = {}; _p = 0
while True:
    k = _zt.find(b'PK\x01\x02', _p)
    if k < 0: break
    cs = struct.unpack('<I', _zt[k+20:k+24])[0]; nl = struct.unpack('<H', _zt[k+28:k+30])[0]
    ENTS[_zt[k+46:k+46+nl].decode('utf-8','replace')] = (
        struct.unpack('<I', _zt[k+42:k+46])[0], cs, struct.unpack('<H', _zt[k+10:k+12])[0])
    _p = k + 4
URL = "https://ndownloader.figshare.com/files/31337710"
def their_qs(pdb_row):
    c = [n for n in ENTS if f"/{pdb_row}/" in n
         and n.endswith("_propensity_residue_results.csv")
         and "Without_allosteric_ligands" in n]
    if not c: return None
    off, cs, me = ENTS[c[0]]
    req = urllib.request.Request(URL, headers={'Range': f'bytes={off}-{off+cs+512}'})
    raw = urllib.request.urlopen(req, timeout=180).read()
    nl = struct.unpack('<H', raw[26:28])[0]; el = struct.unpack('<H', raw[28:30])[0]
    txt = (zlib.decompress(raw[30+nl+el:30+nl+el+cs], -15) if me == 8
           else raw[30+nl+el:30+nl+el+cs]).decode('utf-8', 'replace')
    lines = txt.splitlines(); h = lines[0].split(',')
    try: i_r, i_c, i_q = h.index('res_num'), h.index('chain'), h.index('qs')
    except ValueError: return None
    out = {}
    for L in lines[1:]:
        f = L.split(',')
        if len(f) <= max(i_r, i_c, i_q): continue
        try: out[(f[i_c].strip(), int(f[i_r]))] = float(f[i_q])
        except ValueError: continue
    return out

ARMS = ["ctqw", "geometry_hop", "gnm_msf", "packing_degree", "their_propensity"]

def main():
    rows = []
    for i, rec in enumerate(ANN):
        if rec["pdb"] not in KEEP: continue
        pdb = rec["pdb"].split("_")[0]
        try: keys, xyz, bf = ca(pdb)
        except Exception: continue
        n = len(keys)
        if n == 0 or n > 3000: continue
        pos = {k: j for j, k in enumerate(keys)}
        seed = sorted({pos[k] for k in (pact(t) for t in rec["active_residues"]) if k in pos})
        truth = sorted({pos[k] for k in (pa(t) for t in rec["allosteric_residues"]) if k in pos})
        if not seed or not truth: continue
        sm = np.zeros(n, bool); sm[seed] = True
        tm = np.zeros(n, bool); tm[truth] = True
        elig = (~terminal_mask(n, 0.05)) & ~sm
        y = tm[elig]
        if y.sum() == 0 or y.sum() == len(y): continue
        try:
            H = build_H_new(xyz, bf, cutoff=8.0)
            ctqw = np.nan_to_num(time_averaged_ctqw_converged(H, source=np.asarray(seed), coherent=False))
            hop = hop_from_seed(xyz, np.asarray(seed), cutoff=8.0)
            ctx = gnm_context(xyz, cutoff=8.0)
        except Exception: continue
        q = their_qs(rec["pdb"])
        theirs = (np.array([q.get(keys[j], np.nan) for j in range(n)], float)
                  if q else np.full(n, np.nan))
        cand = {"ctqw": ctqw, "geometry_hop": -hop, "gnm_msf": ctx["msf"],
                "packing_degree": -ctx["degree"], "their_propensity": theirs}
        r = {"pdb": rec["pdb"], "N": n, "n_truth": int(y.sum())}
        for a, s in cand.items():
            v = s[elig]
            r[a] = (float(roc_auc_score(y, v))
                    if np.isfinite(v).all() and np.ptp(v) > 0 else None)
        rows.append(r)
        if (i+1) % 20 == 0: print(f"  ... {i+1}/{len(ANN)} (kept {len(rows)})", flush=True)

    print("\n" + "=" * 74)
    print("ATTRIBUTION — share of available ranking signal, ASBench")
    print("=" * 74)
    print(f"  n = {len(rows)} structures\n")
    print(f"  {'arm':<20}{'mean AUC':>10}{'share of signal':>18}{'n':>6}")
    summ = {}
    for a in ARMS:
        v = np.array([r[a] for r in rows if r.get(a) is not None], float)
        share = (v.mean() - 0.5) / 0.5
        summ[a] = dict(mean_auc=float(v.mean()), share=float(share), n=int(len(v)))
        print(f"  {a:<20}{v.mean():>10.4f}{share:>17.1%}{len(v):>6}")
    best = max(ARMS, key=lambda a: summ[a]["mean_auc"])
    print(f"\n  best single arm : {best} at {summ[best]['mean_auc']:.4f}")
    print(f"  EXPLAINED       : {summ[best]['share']:>6.1%} of available signal")
    print(f"  HEADROOM        : {1-summ[best]['share']:>6.1%} unexplained")
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(dict(rows=rows, summary=summ, n=len(rows)),
              open(OUT / "attribution_scaling.json", "w"), indent=1)
    print(f"\n  written -> {OUT}/attribution_scaling.json")
    return 0

if __name__ == "__main__":
    sys.exit(main())
