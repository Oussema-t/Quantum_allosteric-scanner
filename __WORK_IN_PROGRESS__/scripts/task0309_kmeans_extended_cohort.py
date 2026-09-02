"""TASK-0309 -- does [[TASK-0284]] Finding A's two-population claim survive
at n=158+, or does [[TASK-0288]] Finding F (point mass at the covalent
limit + continuum) explain the extended cohort instead?

[[TASK-0284]] reported k-means silhouette 0.7367 (sizes 24/9) on 33 pocket
ROWS -- not independent units. [[TASK-0288]] retested at the true n=28
structures (13 apo-structure clusters at the time) and found the
silhouette survives but the two things that would actually support two
POPULATIONS do not: Shapiro non-normality collapses under size
normalisation (p=0.0067 -> 0.19) and a parametric-bootstrap LRT (1 vs 2
Gaussian components) gives p=0.11, underpowered but not distinguishing
one population from two. Finding F then showed what the distribution
actually contains: a point mass at the peptide-bond distance plus a
continuum -- a different object from two Gaussian clusters.

[[TASK-0304]] added ASBench (117 structures/112 proteins) and CASBench
(313 structures/33 proteins), using each benchmark's own site
annotations. This task pools all three and re-runs the same battery at
the ~12x larger n.

**A pre-existing labelling bug found and fixed here, not silently
inherited**: RESULTS.md's own TASK-0304 table row calls our register
"13 clusters (28 structures)" and reports 28.6%. Checked against
`config/*.yaml`'s own `apo_pdb` field (the actual clustering unit, not
assumed): [[TASK-0261]]'s 13-cluster map (`CM`) was built for a
DIFFERENT, older 20-target frozen set. Of the 28 structures in the
Finding-F cohort, only 15/28 targets are even IN that map (covering all
13 of its clusters); the other 13 targets are outside it entirely and
each apo_pdb-shares with nothing else in this specific 28-set except two
genuine pairs (GAC_BPTES/GAC_CPD12 -> 7SBN, FBPASE_94D/FBPASE_95S ->
5LDZ). The TRUE cluster count for THIS cohort is **26**, not 13 -- and
the "28.6%" figure itself was never actually computed at cluster level at
all; it is 8/28 STRUCTURE-level (verified: 8/28 = 0.2857), the exact
pseudo-replication this register's own standing rule ("cluster-robust or
it does not count") exists to catch. Both are fixed here: clustering is
by `apo_pdb` (verified against the live config, not re-typed from a
stale map), and every percentage below is computed after taking one row
per cluster/protein (median of its own structures), never before.

**No network calls.** All 420 ASBench/CASBench PDB IDs used by
[[TASK-0304]]'s own Finding-F rows are already in `pdb_cache/` (verified:
0 missing, largest 5.8 MB) -- this task only needs Calpha coordinates for
a size (Rg) normaliser, read locally, once, per structure.

Run: ../.venv/bin/python3 scripts/task0309_kmeans_extended_cohort.py
"""
import sys, os, json, warnings
# single-threaded BLAS -- hundreds of tiny (n<200) 1-D GMM fits pay pure
# thread-spawn overhead under the default multi-threaded BLAS and it
# dominated wall-clock time in an earlier run of this script (~7 CPU-min
# for one cohort's first LRT call alone); set before numpy/sklearn import.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
from pathlib import Path
from collections import defaultdict
import numpy as np
warnings.filterwarnings("ignore")
import yaml
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture

ROOT = Path(".")
R0304 = ROOT / "results/tasks/0304_asbench_casbench"
PDB_CACHE = ROOT / "pdb_cache"
OUT = ROOT / "results/tasks/0309_kmeans_extended_cohort"
MAX_FILE_MB = 20  # matches [[TASK-0304]]'s own guard; nothing here is close


# --------------------------------------------------------------------- Rg
def compute_rg(pdb_id):
    """CA-only radius of gyration, first altloc, local cache only."""
    fp = PDB_CACHE / f"{pdb_id}.pdb"
    if not fp.exists() or fp.stat().st_size / 1e6 > MAX_FILE_MB:
        return None
    coords = []
    with open(fp) as fh:
        for line in fh:
            if not line.startswith("ATOM"):
                continue
            if line[12:16].strip() != "CA":
                continue
            if line[16] not in (" ", "A"):
                continue
            try:
                coords.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
            except ValueError:
                continue
    if len(coords) < 10:
        return None
    c = np.asarray(coords)
    return float(np.sqrt(((c - c.mean(axis=0)) ** 2).sum(axis=1).mean())), len(coords)


# ------------------------------------------------------------- cohort load
def load_ours():
    d = json.load(open("results/tasks/0284_two_populations/bimodality_and_nulls.json"))
    rows = [r for r in d["rows"] if "N" in r and r.get("min_A") is not None]
    seen = {}
    for r in rows:
        seen.setdefault((r["N"], round(r["Rg"], 2)), r)
    S = list(seen.values())

    apo = {}
    for path in ("config/candidate_targets_task0243.yaml", "config/targets.yaml"):
        cfg = yaml.safe_load(open(path))["targets"]
        for t, c in cfg.items():
            if isinstance(c, dict) and c.get("apo_pdb") and t not in apo:
                apo[t] = c["apo_pdb"]
    cfg216 = yaml.safe_load(open("config/candidate_targets_task0216.yaml"))
    cfg216 = cfg216.get("targets", cfg216)
    for t, c in cfg216.items():
        if isinstance(c, dict) and c.get("apo_pdb") and t not in apo:
            apo[t] = c["apo_pdb"]

    by_cluster = defaultdict(list)
    for r in S:
        a = apo.get(r["target"])
        assert a, f"no apo_pdb resolved for {r['target']}"
        by_cluster[a].append(r)

    out = []
    for a, members in by_cluster.items():
        out.append(dict(cohort="ours", protein=a,
                        targets=[m["target"] for m in members],
                        n_structures=len(members),
                        min_A=float(np.median([m["min_A"] for m in members])),
                        Rg=float(np.median([m["Rg"] for m in members]))))
    return out, len(S)


def _rg_group(rows, id_key, rg_cache):
    """rows: list of dicts with `pdb`, `min_heavy_A`, id_key. Returns
    protein/cluster-level rows with median min_A and median Rg."""
    by_id = defaultdict(list)
    for r in rows:
        base_pdb = r["pdb"].split("_")[0]  # ASBench bio-assembly suffixes
        if base_pdb not in rg_cache:
            rg_cache[base_pdb] = compute_rg(base_pdb)
        rg = rg_cache[base_pdb]
        if rg is None:
            continue
        by_id[r[id_key]].append((r["min_heavy_A"], rg[0]))
    out = []
    for pid, vals in by_id.items():
        mins = [v[0] for v in vals]; rgs = [v[1] for v in vals]
        out.append(dict(protein=pid, n_structures=len(vals),
                        min_A=float(np.median(mins)), Rg=float(np.median(rgs))))
    return out


def load_asbench(rg_cache):
    """[[TASK-0304]]'s own established unit for ASBench is the distinct
    PDB CODE (112 of them, after stripping `_1`/`_2` bio-assembly suffixes
    -- "Deduplicated to 112 distinct PDB codes" in its own Done section),
    not the free-text `protein` name string: names collide across
    genuinely distinct targets (e.g. 5 different PDB entries all named
    "Glycogen phosphorylase, muscle form" -- different ligands/mutants,
    not one row to collapse to). Grouping by name here gave only 79 --
    checked directly, not assumed correct, before writing this."""
    a = json.load(open(R0304 / "asbench_finding_f.json"))
    for r in a["rows"]:
        r["_pdb_code"] = r["pdb"].split("_")[0]
    out = _rg_group(a["rows"], "_pdb_code", rg_cache)
    for r in out:
        r["cohort"] = "asbench"
    return out, len(a["rows"])


def load_casbench(rg_cache):
    c = json.load(open(R0304 / "casbench_finding_f.json"))
    out = _rg_group(c["rows"], "cas_id", rg_cache)
    for r in out:
        r["cohort"] = "casbench"
    return out, len(c["rows"])


# ------------------------------------------------------------------ stats
def _ll(x, k, seeds=3, n_init=3):
    best = -np.inf
    for s in range(seeds):
        m = GaussianMixture(k, n_init=n_init, random_state=s).fit(x)
        best = max(best, m.score(x) * len(x))
    return best


def lrt(x, k1, k2, B=200, seed=0, seeds=3):
    """Parametric-bootstrap LRT, k1 vs k2 Gaussian components. Null
    resampled from the fitted k1-component model (generalises
    [[TASK-0288]]'s own 1-vs-2 version, which only ever needed k1=1, to
    the 2-vs-3 test this task also requires).

    [[TASK-0319]] fix: `g1`'s `random_state` was a plain int (0). sklearn's
    `GaussianMixture.sample()` re-derives a *fresh* RandomState from that
    int on every call (`check_random_state`), so `g1.sample(n)` returned
    the SAME draw every single bootstrap iteration (verified: identical up
    to permutation). Since GMM log-likelihood is invariant to the order of
    iid data, all B "null" replicates collapsed to one point (n=26, seed 0:
    58/60 replicates bit-identical at LR=1.14326065). `obs` then landed
    strictly above or below that single point, giving p in {1/(B+1),
    ~1.0} -- never anywhere near a continuous 5% test. Passing a
    `np.random.RandomState` INSTANCE (not an int) makes sklearn reuse and
    advance that same instance across calls instead of reseeding, so each
    `.sample()` call draws fresh data. This was the actual driver of the
    68%/52% false-positive rate on N(0,1) at n=26/100 -- distinct from (but
    compounding) the restart-asymmetry and reg_covar candidates originally
    flagged; see TASK-0319 for the measured before/after."""
    x = np.asarray(x, float).reshape(-1, 1); n = len(x)
    obs = 2 * (_ll(x, k2, seeds) - _ll(x, k1, seeds))
    g1 = GaussianMixture(k1, n_init=5, random_state=np.random.RandomState(seed)).fit(x)
    r = np.random.default_rng(seed)
    null = []
    for i in range(B):
        samp, _ = g1.sample(n)
        rng_perm = r.permutation(n)  # sample() returns component-sorted order
        samp = samp[rng_perm]
        null.append(2 * (_ll(samp, k2, seeds) - _ll(samp, k1, seeds)))
    null = np.array(null)
    p = float((np.sum(null >= obs) + 1) / (B + 1))
    return float(obs), p


def controls(n, k1, k2, seps=(1.0, 2.5), reps=2, B=80, seeds=3, seed0=1000):
    """Fresh positive (synthetic k2-component, given separation in SD
    units) and negative (synthetic k1-component) control p-values AT THIS
    n -- not reused from [[TASK-0288]]'s own n=28 table, which is exactly
    the control-reuse this task's own Constraint rules out."""
    rng = np.random.default_rng(seed0)
    out = {}
    for sep in seps:
        ps = []
        for i in range(reps):
            parts = [rng.normal(sep * j, 1, n // k2 + (1 if j < n % k2 else 0))
                     for j in range(k2)]
            x = np.concatenate(parts).reshape(-1, 1)
            _, p = lrt(x, k1, k2, B=B, seed=seed0 + 17 * i + 3, seeds=seeds)
            ps.append(p)
        out[f"pos_sep{sep}"] = ps
    ps = []
    for i in range(reps):
        parts = [rng.normal(0, 1, n // k1 + (1 if j < n % k1 else 0)) for j in range(k1)]
        x = np.concatenate(parts).reshape(-1, 1)
        _, p = lrt(x, k1, k2, B=B, seed=seed0 + 101 + 17 * i, seeds=seeds)
        ps.append(p)
    out["neg"] = ps
    return out


def spike_binomial(y, lo=1.25, hi=1.5):
    """[[TASK-0288]] Part F: is there excess mass in a narrow window at
    the covalent limit beyond what a single fitted log-normal predicts?"""
    y = np.asarray(y, float)
    n_obs = int(((y >= lo) & (y < hi)).sum())
    lo_, hi_ = np.log(lo), np.log(hi)
    mu, sd = np.log(y).mean(), np.log(y).std(ddof=1)
    pw = stats.norm.cdf(hi_, mu, sd) - stats.norm.cdf(lo_, mu, sd)
    p = float(stats.binom.sf(n_obs - 1, len(y), pw))
    return dict(n_obs=n_obs, n_total=len(y), expected=float(pw * len(y)), binomial_p=p)


def silhouettes(v, kmax=6):
    out = {}
    for k in range(2, kmax + 1):
        x = v.reshape(-1, 1)
        km = KMeans(k, n_init=20, random_state=0).fit(x)
        out[k] = float(silhouette_score(x, km.labels_))
    return out


def gmm_bics(v, kmax=3):
    x = v.reshape(-1, 1)
    out = {}
    for k in range(1, kmax + 1):
        best = None
        for s in range(3):
            m = GaussianMixture(k, n_init=3, random_state=s).fit(x)
            if best is None or m.bic(x) < best.bic(x):
                best = m
        out[k] = dict(bic=float(best.bic(x)),
                      means=sorted(float(np.exp(m_)) for m_ in best.means_.ravel()),
                      weights=[float(w) for w in
                               best.weights_[np.argsort(best.means_.ravel())]],
                      sigmas=[float(np.exp(s_)) for s_ in  # approx, log-scale sd as a multiplicative width
                              np.sqrt(best.covariances_.ravel())[np.argsort(best.means_.ravel())]])
    return out


def battery(name, rows, kmax_sil=6):
    n = len(rows)
    y = np.array([r["min_A"] for r in rows])
    yr = np.array([r["min_A"] / r["Rg"] for r in rows if r["Rg"] > 0])
    print(f"\n{'='*76}\n{name}  (n={n} independent units)\n{'='*76}")
    result = dict(n=n)
    for tag, v in [("raw min_A", y), ("min_A / Rg", yr)]:
        print(f"\n  -- {tag} --")
        # LITERAL site overlap (min_A == 0.0, allo and active/catalytic
        # annotations share a residue -- an even more extreme case of
        # Finding F than covalent adjacency, found while running this
        # exact battery: 12/112 ASBench, 3/33 CASBench, 0/26 ours) breaks
        # every log-scale test below. Excluded from those only, counted
        # and reported on its own, never silently dropped or epsilon-padded.
        n_overlap = int((v <= 0).sum())
        v_log = v[v > 0]
        sil = silhouettes(v)  # raw scale, zeros are ordinary points here
        print(f"  silhouette k=2..{kmax_sil}: " +
              "  ".join(f"k{k}={s:.3f}" for k, s in sil.items()))
        if n_overlap:
            print(f"  literal site-overlap (min_A=0.0, excluded below): {n_overlap}/{n}")
        sh = stats.shapiro(np.log(v_log))
        print(f"  Shapiro(log, n={len(v_log)}) p={sh.pvalue:.4f}")
        o12, p12 = lrt(np.log(v_log), 1, 2, B=200, seed=1, seeds=3)
        print(f"  LRT 1 vs 2: LR={o12:.3f}  p={p12:.4f}")
        ctrl12 = controls(len(v_log), 1, 2)
        for k_, v_ in ctrl12.items():
            print(f"    control {k_:<12} p=" + ", ".join(f"{x:.3f}" for x in v_))
        o23, p23 = lrt(np.log(v_log), 2, 3, B=200, seed=2, seeds=3)
        print(f"  LRT 2 vs 3: LR={o23:.3f}  p={p23:.4f}")
        ctrl23 = controls(len(v_log), 2, 3, seps=(2.5,), reps=2)
        for k_, v_ in ctrl23.items():
            print(f"    control {k_:<12} p=" + ", ".join(f"{x:.3f}" for x in v_))
        bics = gmm_bics(np.log(v_log))
        print(f"  GMM BIC: " + "  ".join(f"k{k}={d['bic']:.1f}" for k, d in bics.items()))
        best_k = min(bics, key=lambda k: bics[k]["bic"])
        print(f"    BIC-best k={best_k}; component means(Å)={bics[best_k]['means']}"
              f" weights={[round(w,3) for w in bics[best_k]['weights']]}")
        spike = spike_binomial(v_log)
        print(f"  spike window [1.25,1.5): {spike['n_obs']}/{spike['n_total']} obs vs "
              f"{spike['expected']:.2f} expected under single log-normal, "
              f"binomial p={spike['binomial_p']:.3e}")
        result[tag] = dict(n_overlap=n_overlap, n_log=len(v_log), silhouette=sil,
                           shapiro_p=float(sh.pvalue),
                           lrt_1v2=dict(LR=o12, p=p12, controls=ctrl12),
                           lrt_2v3=dict(LR=o23, p=p23, controls=ctrl23),
                           gmm_bic=bics, bic_best_k=best_k, spike=spike)
    return result


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ours, n_ours_struct = load_ours()
    rg_cache = {}
    asb, n_asb_struct = load_asbench(rg_cache)
    cas, n_cas_struct = load_casbench(rg_cache)
    print(f"ours: {len(ours)} clusters from {n_ours_struct} structures "
          f"(corrected from a stale '13 clusters' label -- see docstring)")
    print(f"asbench: {len(asb)} proteins from {n_asb_struct} structures")
    print(f"casbench: {len(cas)} proteins from {n_cas_struct} structures")
    pooled = ours + asb + cas
    print(f"pooled: {len(pooled)} independent units")

    results = {}
    for nm, rows in [("OURS", ours), ("ASBENCH", asb), ("CASBENCH", cas), ("POOLED", pooled)]:
        results[nm] = battery(nm, rows)

    # headline <1.5A fractions at the corrected protein/cluster level
    print(f"\n{'='*76}\nPROTEIN-LEVEL <1.5A fractions (corrected unit of analysis)\n{'='*76}")
    frac = {}
    for nm, rows in [("ours", ours), ("asbench", asb), ("casbench", cas), ("pooled", pooled)]:
        y = np.array([r["min_A"] for r in rows])
        f = float((y < 1.5).mean())
        frac[nm] = dict(n=len(rows), frac_below_1p5=f, n_below=int((y < 1.5).sum()))
        print(f"  {nm:<10} {int((y<1.5).sum())}/{len(rows)} = {f:.1%}")

    json.dump(dict(ours=ours, asbench=asb, casbench=cas,
                   n_ours_structures=n_ours_struct, n_asbench_structures=n_asb_struct,
                   n_casbench_structures=n_cas_struct,
                   protein_level_frac_below_1p5=frac, battery=results),
              open(OUT / "kmeans_extended_cohort.json", "w"), indent=1)
    print(f"\nwritten -> {OUT}/kmeans_extended_cohort.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
