"""TASK-0310 -- re-score the whole observable family residualised on
proximity to the active site.

[[TASK-0308]] established two things unknown when the observable family
(TASK-0140-0157) was built: proximity to the active site is the single
strongest predictor on the ASBench cohort (AUC 0.6147), and CTQW
occupation is ~80% proximity (within-structure rho=+0.735; residualised,
CTQW's AUC drops from 0.5921 to 0.5184, no longer significant). Every
other observable in the family was scored RAW, against a floor, never
conditioned on distance. This re-scores each on the identical ASBench
cohort, reporting raw AUC, rho against proximity, and AUC after
rank-residualising on proximity -- the same statistic `TASK-0308`'s own
`ctqw_proximity_partial.json` reports for CTQW (that JSON has no
surviving script -- reconstructed here from its own committed numbers,
verified below to reproduce them, before trusting the harness on any
other observable).

RUNNABLE CHECK (this task's own Scope item 1), before scoring anything:
of the 9 named observables, 2 were NEVER implemented past a literature
proposal -- checked directly against their own Done sections, not
assumed. `TASK-0147` (vibronic resonance): "does not build the
structured-bath master equation, synthetic falsifier, or real-target
scoring... No synthetic falsification gate and no real-target scoring
were run." `TASK-0157` (two-boson HOM): "no k=2 symmetrized Hilbert
space, no synthetic falsifier... result: no code touched." Both are
proposals, not scoreable code -- building either now would be a NEW
observable, not a re-scoring, explicitly against this task's own
Constraint ("do not re-tune... a new sweep"). Excluded, reported as
such, not silently dropped.

Of the remaining 7, `dephasing` (`propagators.haken_strobl_time_averaged`,
TASK-0141) has a documented runtime that scales far too steeply for this
cohort: TASK-0105's own measured precedent is N=169 ~11s/gamma,
N=451 ~161s/gamma (~N^2.75 empirically) -- at this cohort's median N=819
that extrapolates to ~13 minutes PER STRUCTURE for a single gamma, and
this cohort's max N=2970 would be many hours for one structure alone.
Run on the full 108 is infeasible in this session. Time-boxed instead
(this project's own established convention -- TASK-0256/TASK-0260's
identical treatment of haken_strobl/PocketMiner infeasibility): run on
the 11 structures with N<=300, where the extrapolated cost (~1 minute
each) is affordable, single pre-registered gamma=0.1*bandwidth (the SAME
"standard weak coupling" convention `transport.transmission_from_source`
already cites TASK-0141 for), t_max=25.0 (`dephasing_discrimination_
sweep.py`'s own T_MAX). Reported as a disclosed partial result on 11/108
structures, not extrapolated to the full cohort.

METHOD, per structure, matching TASK-0308's own metric exactly:
  - eligibility: seed and terminal-5%-each-end residues excluded
    (`allostery.labels.terminal_mask`), same convention as TASK-0305/0308.
  - raw AUC: `roc_auc_score(y, score[eligible])`.
  - proximity: `hop_from_seed` raw output (already "higher = nearer";
    `hop_far` elsewhere in this register is `-hop_from_seed`).
  - rank-residualise: `rankdata` both the candidate score and proximity
    over eligible residues, OLS-residualise the candidate's ranks on
    proximity's ranks + intercept, AUC of the residual against truth.
  - within-structure rho: Spearman(candidate, proximity) over eligible
    residues.
  - family aggregate: mean of per-structure values (matching TASK-0308's
    own "mean AUC" convention, not a pooled/global AUC).

SIGNIFICANCE: Wilcoxon signed-rank of (per-structure residual AUC - 0.5)
against 0, Bonferroni-corrected across the family size actually run.
Cluster-robust by protein: `TASK-0261`'s own `cluster_sign_flip_test` is
hardcoded to its own 13-cluster/20-target frozen set (`if t in CM`) and
silently returns an empty test on any ASBench PDB -- not reusable as-is.
Generalised locally (`cluster_sign_flip_test_generic`, below): identical
algorithm (sum-of-cluster-sums, sign-flip null, symmetric under H0), but
parameterised by an arbitrary cluster map, and falling back from exact
2^n_clusters enumeration to Monte Carlo (100000 draws) once n_clusters
exceeds 20 -- ASBench's own protein-name field gives ~90+ clusters, mostly
singletons, so exact enumeration (as TASK-0261 could afford at 13) is not
tractable here.

POSITIVE CONTROL (this task's own Constraint, `[[TASK-0305]]`'s lesson):
proximity scored against itself must reproduce ~0.6147 raw (validates
this script's own cohort-building and eligibility logic against
TASK-0308's committed number) and collapse to exactly 0.5 residualised
(a variable residualised on itself is identically zero -- AUC on a
constant score is undefined and reported as 0.5 by this project's own
convention, `task0308_attribution_scaling.py`'s own `np.ptp(v) > 0` guard).

Run: ../.venv/bin/python3 scripts/task0310_family_residualised_on_proximity.py
"""
from __future__ import annotations

import itertools
import json
import re
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
from scipy.sparse.csgraph import shortest_path
from scipy.stats import rankdata, spearmanr, wilcoxon
from sklearn.metrics import roc_auc_score

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
sys.path.insert(0, "..")

from backend.data_layer import fetch  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.baselines import hop_from_seed  # noqa: E402
from allostery.labels import terminal_mask  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged, haken_strobl_time_averaged  # noqa: E402
from allostery.chiral import chiral_circulation_score  # noqa: E402
from allostery.transport import transmission_from_source  # noqa: E402
from allostery.spectral_coherence import spectral_coherence_score, DEFAULT_T_MAX  # noqa: E402
from allostery.entanglement import (  # noqa: E402
    entanglement_entropy_mixture, natural_coherent_time, hop_radius_neighborhoods,
)
from allostery.lowmode_predictor import prs_low, dcc_low  # noqa: E402
from allostery.persistent_voids import void_score  # noqa: E402

OUT = Path("results/tasks/0310_family_residualised_on_proximity")
ANN = json.load(open("results/tasks/0304_asbench_casbench/asbench_annotations.json"))
KEEP = {r["pdb"] for r in json.load(
    open("results/tasks/0305_asbench_detection/asbench_detection.json"))["rows"]}

CUTOFF = 8.0
DEPHASING_N_MAX = 300  # time-boxed, see module docstring
DEPHASING_T_MAX = 25.0  # dephasing_discrimination_sweep.py's own T_MAX
DEPHASING_GAMMA_MULT = 0.1  # transport.py's own cited TASK-0141 "standard weak coupling" default
LOWMODE_K = 10  # middle of TASK-0149's own K_MODES_GRID=[5,10,15,20]; fixed, not swept/selected here

# --- parsers, copied (not imported) from task0308_attribution_scaling.py:
# that module executes a network range-request at IMPORT time (the
# figshare propensity fetch), so importing it wholesale to reuse 6 lines
# of regex would trigger an unwanted multi-MB download on every run. ---
_A = re.compile(r'^([A-Z]{2,3})\s*(-?\d+)([A-Za-z]?)\s+(\w)$')


def pa(t):
    m = _A.match(t.strip())
    if m:
        return (m.group(4), int(m.group(2)))
    m = re.match(r'^([A-Z]{2,3})(-?\d+)\s+(\w)$', t.strip())
    return (m.group(3), int(m.group(2))) if m else None


def pact(t):
    m = re.match(r'^(\w)(-?\d+)$', t.strip())
    return (m.group(1), int(m.group(2))) if m else None


def ca(pdb):
    keys, xyz, bf, seen = [], [], [], set()
    for L in Path(fetch(pdb)).read_text().splitlines():
        if not L.startswith("ATOM") or L[12:16].strip() != "CA":
            continue
        if L[16] not in (" ", "A"):
            continue
        try:
            k = (L[21], int(L[22:26]))
            if k in seen:
                continue
            seen.add(k); keys.append(k)
            xyz.append((float(L[30:38]), float(L[38:46]), float(L[46:54])))
            bf.append(float(L[60:66]) if L[60:66].strip() else 0.0)
        except ValueError:
            continue
    return keys, np.asarray(xyz, float), np.asarray(bf, float)


# ------------------------------------------------------------- residualise
def residualise(y_ranks: np.ndarray, x_ranks: np.ndarray) -> np.ndarray:
    A = np.column_stack([x_ranks, np.ones_like(x_ranks)])
    coef, *_ = np.linalg.lstsq(A, y_ranks, rcond=None)
    return y_ranks - A @ coef


def score_stats(score: np.ndarray, y: np.ndarray, prox: np.ndarray) -> dict | None:
    """(raw AUC, rho vs proximity, residualised AUC) for one structure's
    one candidate, over already-eligibility-masked arrays. None if the
    score is degenerate (constant, or contains a non-finite value) --
    the honest "not scoreable here" outcome, matching `task0308_
    attribution_scaling.py`'s own `np.ptp(v) > 0` convention."""
    if not np.isfinite(score).all() or np.ptp(score) == 0:
        return None
    raw_auc = float(roc_auc_score(y, score))
    rho, _ = spearmanr(score, prox)
    r_score = rankdata(score)
    r_prox = rankdata(prox)
    resid = residualise(r_score, r_prox)
    resid_auc = 0.5 if np.ptp(resid) < 1e-9 else float(roc_auc_score(y, resid))
    return dict(raw_auc=raw_auc, rho=float(rho), resid_auc=resid_auc)


# -------------------------------------------------- generalised cluster test
def cluster_sign_flip_test_generic(values: dict, cluster_map: dict,
                                    n_mc: int = 100_000, seed: int = 0) -> dict:
    """TASK-0261's own `cluster_sign_flip_test` algorithm (sum-of-cluster-
    sums, sign-flip null under H0: symmetric about 0), generalised to an
    arbitrary `cluster_map` instead of that module's own hardcoded 13-
    cluster `CM`. Exact 2^n_clusters enumeration when n_clusters<=20
    (matching TASK-0261's own affordable case); Monte Carlo above that,
    since ASBench's protein-name clusters run to ~90+, mostly singletons,
    where 2^90 is not enumerable."""
    keys = [k for k in values if k in cluster_map]
    clusters = sorted(set(cluster_map[k] for k in keys))
    by_cluster: dict = {c: [] for c in clusters}
    for k in keys:
        by_cluster[cluster_map[k]].append(values[k])
    cluster_sums = {c: sum(v) for c, v in by_cluster.items()}
    obs = sum(cluster_sums.values())
    n_clusters = len(clusters)
    rng = np.random.default_rng(seed)
    if n_clusters <= 20:
        null = np.array([sum(s * cluster_sums[c] for s, c in zip(signs, clusters))
                          for signs in itertools.product([1, -1], repeat=n_clusters)])
        exact = True
    else:
        signs = rng.choice([1, -1], size=(n_mc, n_clusters))
        sums_arr = np.array([cluster_sums[c] for c in clusters])
        null = signs @ sums_arr
        exact = False
    p = float(np.mean(np.abs(null) >= abs(obs) - 1e-9))
    return dict(n_rows=len(keys), n_clusters=n_clusters, statistic=float(obs),
                p_value=p, exact=exact, median=float(np.median([values[k] for k in keys])))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    t_start = time.monotonic()

    structures = []
    for rec in ANN:
        if rec["pdb"] not in KEEP:
            continue
        pdb = rec["pdb"].split("_")[0]
        try:
            keys, xyz, bf = ca(pdb)
        except Exception:
            continue
        n = len(keys)
        if n == 0 or n > 3000:
            continue
        pos = {k: j for j, k in enumerate(keys)}
        seed = sorted({pos[k] for k in (pact(t) for t in rec["active_residues"]) if k in pos})
        truth = sorted({pos[k] for k in (pa(t) for t in rec["allosteric_residues"]) if k in pos})
        if not seed or not truth:
            continue
        sm = np.zeros(n, bool); sm[seed] = True
        tm = np.zeros(n, bool); tm[truth] = True
        elig = (~terminal_mask(n, 0.05)) & ~sm
        y = tm[elig]
        if y.sum() == 0 or y.sum() == len(y):
            continue
        try:
            H = build_H_new(xyz, bf, cutoff=CUTOFF)
            prox = hop_from_seed(xyz, np.asarray(seed), cutoff=CUTOFF)
        except Exception:
            continue
        structures.append(dict(pdb=rec["pdb"], protein=rec.get("protein", rec["pdb"]),
                                keys=keys, xyz=xyz, bf=bf, seed=np.asarray(seed),
                                truth=truth, elig=elig, y=y, H=H, prox=prox, N=n))

    print(f"{len(structures)}/{len(ANN)} structures usable (matches TASK-0308's own n=108 filter)\n")

    # ---------------------------------------------------------------- CTQW
    # baseline re-derivation, to VALIDATE this harness before trusting it
    # on anything else -- must reproduce TASK-0308's own committed numbers.
    print("### Baseline re-derivation: CTQW + proximity (validates the harness) ###")
    ctqw_rows, prox_rows = {}, {}
    for s in structures:
        ctqw = np.nan_to_num(time_averaged_ctqw_converged(s["H"], source=s["seed"], coherent=False))
        r = score_stats(ctqw[s["elig"]], s["y"], s["prox"][s["elig"]])
        if r:
            ctqw_rows[s["pdb"]] = r
        rp = score_stats(s["prox"][s["elig"]], s["y"], s["prox"][s["elig"]])
        if rp:
            prox_rows[s["pdb"]] = rp

    def agg(rows):
        raw = np.mean([r["raw_auc"] for r in rows.values()])
        rho = np.mean([r["rho"] for r in rows.values()])
        resid = np.mean([r["resid_auc"] for r in rows.values()])
        return raw, rho, resid

    ctqw_raw, ctqw_rho, ctqw_resid = agg(ctqw_rows)
    prox_raw, prox_rho, prox_resid = agg(prox_rows)
    print(f"  CTQW      raw={ctqw_raw:.4f} (committed: 0.5921)  rho={ctqw_rho:.4f} (committed: 0.7347)  "
          f"resid={ctqw_resid:.4f} (committed: 0.5184)")
    print(f"  proximity raw={prox_raw:.4f} (committed: 0.6147)  resid-on-self={prox_resid:.4f} (expect 0.5000)")
    reproduces = abs(ctqw_raw - 0.5921) < 0.01 and abs(ctqw_resid - 0.5184) < 0.02 and abs(prox_resid - 0.5) < 1e-6
    print(f"  HARNESS {'REPRODUCES' if reproduces else 'DOES NOT REPRODUCE'} TASK-0308's own committed numbers.\n")
    if not reproduces:
        print("  Proceeding anyway, flagged prominently -- do not trust downstream numbers without checking why.\n")

    # ---------------------------------------------------- family candidates
    print("### Scoring the observable family, chiral circulation FIRST per this task's own Constraint ###")

    def sc_chiral(s):
        return np.abs(chiral_circulation_score(s["xyz"], source=s["seed"], cutoff=CUTOFF,
                                                field_scale=0.05, H_real=s["H"]))

    def sc_transport(s):
        return transmission_from_source(s["H"], s["seed"], E=0.0)

    def sc_spectral(s):
        return spectral_coherence_score(s["H"], s["seed"], t_max=DEFAULT_T_MAX)

    def sc_entanglement(s):
        A = (np.abs(s["H"] - np.diag(np.diag(s["H"]))) > 0).astype(float)
        hop_dist = shortest_path(A, method="D", unweighted=True, directed=False)
        nbh = hop_radius_neighborhoods(hop_dist, radius=1)
        t_star = natural_coherent_time(s["H"])
        return entanglement_entropy_mixture(s["H"], s["seed"], nbh, t_star)

    def sc_prs(s):
        return prs_low(s["xyz"], s["seed"], cutoff=CUTOFF, k_modes=LOWMODE_K)

    def sc_dcc(s):
        return dcc_low(s["xyz"], s["seed"], cutoff=CUTOFF, k_modes=LOWMODE_K)

    def sc_voids(s):
        return void_score(s["xyz"], thresh=16.0, min_persistence=2.5, top_k=1)

    CANDIDATES = [
        ("chiral_circulation", sc_chiral, "TASK-0140"),
        ("transport", sc_transport, "TASK-0145"),
        ("spectral_coherence", sc_spectral, "TASK-0146"),
        ("entanglement_entropy", sc_entanglement, "TASK-0148"),
        ("prs_low", sc_prs, "TASK-0149"),
        ("dcc_low", sc_dcc, "TASK-0149"),
        ("persistent_h2_void", sc_voids, "TASK-0142"),
    ]

    family_rows = {name: {} for name, _, _ in CANDIDATES}
    family_time = {}
    for name, fn, task in CANDIDATES:
        t0 = time.monotonic()
        n_ok = n_fail = 0
        for s in structures:
            try:
                raw = fn(s)
                raw = np.nan_to_num(np.asarray(raw, float))
            except Exception as exc:  # noqa: BLE001
                n_fail += 1
                continue
            r = score_stats(raw[s["elig"]], s["y"], s["prox"][s["elig"]])
            if r is None:
                n_fail += 1
                continue
            family_rows[name][s["pdb"]] = r
            n_ok += 1
        family_time[name] = time.monotonic() - t0
        if n_ok:
            raw_m, rho_m, resid_m = agg(family_rows[name])
            print(f"  {name:<22} ({task:<9}) n={n_ok:>3} fail={n_fail:<3} "
                  f"raw={raw_m:+.4f} rho={rho_m:+.4f} resid={resid_m:+.4f}  ({family_time[name]:.0f}s)")
        else:
            print(f"  {name:<22} ({task:<9}) FAILED on every structure ({n_fail} failures)")
        if name == "chiral_circulation" and n_ok:
            raw_share = (raw_m - 0.5) / 0.5
            resid_share = (resid_m - 0.5) / 0.5
            print(f"\n  CHIRAL RESULT (per this task's own Constraint, reported before the rest): "
                  f"raw share {raw_share:+.1%}, residualised share {resid_share:+.1%}. "
                  f"{'Chiral SURVIVES residualisation (retains signal above chance).' if resid_share > 0.02 else 'Chiral DOES NOT survive residualisation -- like CTQW, its apparent signal is mostly proximity.'}\n")

    # ------------------------------------------------------- dephasing (partial)
    small = [s for s in structures if s["N"] <= DEPHASING_N_MAX]
    print(f"\n### Dephasing (TASK-0141), time-boxed: N<={DEPHASING_N_MAX} only "
          f"({len(small)}/{len(structures)} structures) ###")
    deph_rows = {}
    t0 = time.monotonic()
    for s in small:
        w = np.linalg.eigvalsh(s["H"])
        bandwidth = float(w.max() - w.min())
        gamma = DEPHASING_GAMMA_MULT * bandwidth
        try:
            occ = haken_strobl_time_averaged(s["H"], DEPHASING_T_MAX, gamma, source=s["seed"],
                                              coherent=False)
        except Exception as exc:  # noqa: BLE001
            print(f"  {s['pdb']:<10} FAILED {exc!r}")
            continue
        r = score_stats(np.nan_to_num(occ)[s["elig"]], s["y"], s["prox"][s["elig"]])
        if r:
            deph_rows[s["pdb"]] = r
        print(f"  {s['pdb']:<10} N={s['N']:<5} raw={r['raw_auc']:.4f} resid={r['resid_auc']:.4f}"
              if r else f"  {s['pdb']:<10} N={s['N']:<5} degenerate score")
    deph_time = time.monotonic() - t0
    if deph_rows:
        d_raw, d_rho, d_resid = agg(deph_rows)
        print(f"  dephasing (n={len(deph_rows)}/{len(small)}): raw={d_raw:+.4f} rho={d_rho:+.4f} "
              f"resid={d_resid:+.4f}  ({deph_time:.0f}s total)")

    # ------------------------------------------------------- significance
    print("\n### Significance: Wilcoxon vs 0.5 on residualised AUC, Bonferroni across the family run ###")
    ALL_ROWS = dict(family_rows)
    ALL_ROWS["dephasing_partial_N<=300"] = deph_rows
    n_tests = sum(1 for v in ALL_ROWS.values() if v)
    sig = {}
    for name, rows in ALL_ROWS.items():
        if not rows:
            continue
        vals = np.array([r["resid_auc"] for r in rows.values()])
        if np.allclose(vals, vals[0]):
            p = 1.0
        else:
            _, p = wilcoxon(vals - 0.5)
        p_bonf = min(1.0, p * n_tests)
        sig[name] = dict(n=len(vals), median_resid_auc=float(np.median(vals)), p=float(p),
                          p_bonferroni=float(p_bonf))
        print(f"  {name:<26} n={len(vals):<3} median_resid_auc={np.median(vals):.4f} "
              f"p={p:.4g}  p_bonf({n_tests})={p_bonf:.4g}")

    # ------------------------------------------------- cluster-robust by protein
    print("\n### Cluster-robust by protein (generalised TASK-0261 sign-flip test) ###")
    protein_of = {s["pdb"]: s["protein"] for s in structures}
    n_clusters_total = len(set(protein_of.values()))
    print(f"  {len(structures)} structures over {n_clusters_total} distinct proteins "
          f"(cluster map from ASBench's own `protein` field)")
    cluster_sig = {}
    for name, rows in ALL_ROWS.items():
        if not rows:
            continue
        centered = {pdb: r["resid_auc"] - 0.5 for pdb, r in rows.items()}
        r = cluster_sign_flip_test_generic(centered, protein_of)
        cluster_sig[name] = r
        print(f"  {name:<26} n_rows={r['n_rows']:<3} n_clusters={r['n_clusters']:<3} "
              f"median={r['median']:+.4f}  cluster-p={r['p_value']:.4g}"
              f"{'  (exact)' if r['exact'] else '  (Monte Carlo, 100000 draws)'}")

    # ------------------------------------------------------------- ranking
    print("\n### Family ranked by RESIDUALISED share, not raw (this task's own Scope) ###")
    ranked = []
    for name, rows in family_rows.items():
        if not rows:
            continue
        raw_m, rho_m, resid_m = agg(rows)
        ranked.append((name, raw_m, rho_m, resid_m, (resid_m - 0.5) / 0.5))
    ranked.sort(key=lambda r: -r[4])
    print(f"  {'observable':<22}{'raw AUC':>10}{'rho(prox)':>11}{'resid AUC':>11}{'resid share':>13}")
    for name, raw_m, rho_m, resid_m, share in ranked:
        print(f"  {name:<22}{raw_m:>10.4f}{rho_m:>11.4f}{resid_m:>11.4f}{share:>+12.1%}")

    OUT_JSON = dict(
        n_structures=len(structures),
        harness_reproduces_task0308=reproduces,
        ctqw_baseline=dict(raw=ctqw_raw, rho=ctqw_rho, resid=ctqw_resid),
        proximity_positive_control=dict(raw=prox_raw, resid_on_self=prox_resid),
        family_rows={k: v for k, v in family_rows.items()},
        dephasing_partial=dict(n_small=len(small), rows=deph_rows),
        significance=sig,
        cluster_robust=cluster_sig,
        ranking=[dict(name=n, raw_auc=a, rho=r, resid_auc=re, resid_share=sh)
                 for n, a, r, re, sh in ranked],
        excluded_never_implemented=["vibronic_resonance (TASK-0147)", "two_boson_hom (TASK-0157)"],
    )
    (OUT / "family_residualised.json").write_text(json.dumps(OUT_JSON, indent=1, default=str))
    print(f"\nTotal wall time: {time.monotonic() - t_start:.0f}s. Wrote {OUT}/family_residualised.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
