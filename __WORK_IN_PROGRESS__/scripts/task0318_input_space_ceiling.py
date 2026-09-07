"""TASK-0318 -- can ANY function of the contact graph + seed beat
proximity, after residualising on proximity?

[[TASK-0310]] scored 7 runnable observables residualised on proximity.
Nothing survived, including chiral circulation (the lead candidate,
proximity-orthogonal by Helmholtz-Hodge construction). [[TASK-0301]]'s
lesson one level up: those 7 are all functionals of the SAME input --
the contact graph derived from (coords, bfactors) plus the seed. Seven
failures on one input is not seven independent chances. This task fits
a high-capacity model (the one place that tool is right, per this
task's own Scope: the question is "what is achievable", not "what is
interpretable") on the FULL span of what this repo already derives from
that input, and reports the ceiling.

Two phases, run independently (Phase A is the expensive one --
re-running every TASK-0310 observable plus new cheap features on 108
ASBench structures; Phase B, the LOPO-by-protein model fit, is fast and
can be re-run alone against a cached Phase-A feature file without
re-paying that cost).

FEATURES (this task's own Scope: "reuse, do not invent" -- every column
below is an EXISTING function already in this repo, called with its own
established defaults, never a new descriptor):
  - contact-graph baselines: `degree_centrality`, `hop_from_seed`,
    `euclid_from_seed_centroid` (`allostery.baselines`)
  - `gnm_context`'s own `msf`/`degree`/`clust` (`allostery.potentials`)
  - the five diagonal potential terms `V_B`/`V_T`/`V_R`/`V_C`/`V_M`
    (`allostery.potentials`), reusing the shared `gnm_context` (TASK-0040's
    own dedup) rather than rebuilding the Kirchhoff eigendecomposition
    five times
  - CTQW occupation (`propagators.time_averaged_ctqw_converged`)
  - all 7 of [[TASK-0310]]'s own runnable observables: chiral circulation,
    quantum transport, spectral coherence, entanglement entropy, low-mode
    PRS/DCC, persistent H2 void -- called with the IDENTICAL parameters
    [[TASK-0310]] used (no re-tuning, matching that task's own Constraint,
    which this task inherits)

RESIDUALISATION. [[TASK-0310]]'s own harness (validated there by
reproducing [[TASK-0308]]'s committed numbers to 4 decimals) is reused,
not rewritten -- this task's own Constraint. Extended per [[TASK-0315]]'s
positive-control finding ("euclid residualised on hop alone did NOT land
at 0.5 on the frozen 20 -- the two proximity measures are correlated but
not redundant"): residualise jointly on BOTH `hop` and `euclid_centroid`
proximity (rank-OLS on a 2-column design, not 1), and the self-check
below verifies this lands at exactly 0.5 for each proximity measure
residualised on the pair that includes itself, before trusting anything
downstream.

MODEL AND VALIDATION. `HistGradientBoostingClassifier` (fast, handles
~75k pooled residue-rows in seconds per fit), **LOPO by protein, always**
(this task's own Constraint -- five prior selection procedures in this
register died of pseudo-replication on far milder violations than a
high-capacity model would commit on 108 structures). For each of the
~76 distinct proteins in the ASBench cohort: train on every OTHER
protein's own rows, predict out-of-fold on the held-out protein's own
structures, reassemble per-structure OOF scores. The reported ceiling is
computed ONLY from out-of-fold predictions -- never in-sample.

Run: ../.venv/bin/python3 scripts/task0318_input_space_ceiling.py [--phase-b-only]

TASK-0338 addendum, 2026-09-07: `no_proximity_feature_check.json` (the number
promoted into the draft as "0.6017 with proximity features deleted outright")
was committed with no script that produces it. Added `--exclude-proximity`:
drops `hop_prox`/`euclid_prox` from the LOPO design matrix (the two features
of 19 that ARE proximity, not a re-derivation) and writes that same JSON,
leaving the default `ceiling_result.json` path/content untouched (ADD-only).
Run: ../.venv/bin/python3 scripts/task0318_input_space_ceiling.py --phase-b-only --exclude-proximity
"""
from __future__ import annotations

import argparse
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
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
sys.path.insert(0, "..")

from backend.data_layer import fetch  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.labels import terminal_mask  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from allostery.potentials import gnm_context, V_B, V_T, V_R, V_C, V_M  # noqa: E402
from allostery.chiral import chiral_circulation_score  # noqa: E402
from allostery.transport import transmission_from_source  # noqa: E402
from allostery.spectral_coherence import spectral_coherence_score, DEFAULT_T_MAX  # noqa: E402
from allostery.entanglement import (  # noqa: E402
    entanglement_entropy_mixture, natural_coherent_time, hop_radius_neighborhoods,
)
from allostery.lowmode_predictor import prs_low, dcc_low  # noqa: E402
from allostery.persistent_voids import void_score  # noqa: E402

OUT = Path("results/tasks/0318_input_space_ceiling")
CACHE = OUT / "feature_cache"
ANN = json.load(open("results/tasks/0304_asbench_casbench/asbench_annotations.json"))
KEEP = {r["pdb"] for r in json.load(
    open("results/tasks/0305_asbench_detection/asbench_detection.json"))["rows"]}

CUTOFF = 8.0
LOWMODE_K = 10  # matches TASK-0310's own fixed choice, not re-tuned

FEATURE_NAMES = [
    "degree", "hop_prox", "euclid_prox", "gnm_msf", "gnm_degree", "gnm_clust",
    "V_B", "V_T", "V_R", "V_C", "V_M", "ctqw",
    "chiral_circulation", "transport", "spectral_coherence", "entanglement_entropy",
    "prs_low", "dcc_low", "persistent_h2_void",
]

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
def residualise(y_ranks: np.ndarray, X_ranks: np.ndarray) -> np.ndarray:
    """`y_ranks` residualised on the design `X_ranks` (n, k) + intercept."""
    A = np.column_stack([X_ranks, np.ones(len(y_ranks))])
    coef, *_ = np.linalg.lstsq(A, y_ranks, rcond=None)
    return y_ranks - A @ coef


def resid_auc_joint(score: np.ndarray, y: np.ndarray, hop: np.ndarray, euclid: np.ndarray) -> float | None:
    if not np.isfinite(score).all() or np.ptp(score) == 0:
        return None
    r_score = rankdata(score)
    X = np.column_stack([rankdata(hop), rankdata(euclid)])
    resid = residualise(r_score, X)
    return 0.5 if np.ptp(resid) < 1e-9 else float(roc_auc_score(y, resid))


# ---------------------------------------------------------------- Phase A
def build_structures():
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
        structures.append(dict(pdb=rec["pdb"], protein=rec.get("protein", rec["pdb"]),
                                keys=keys, xyz=xyz, bf=bf, seed=np.asarray(seed), elig=elig, y=y, N=n))
    return structures


def compute_features_one(s: dict) -> dict:
    xyz, bf, seed = s["xyz"], s["bf"], s["seed"]
    H = build_H_new(xyz, bf, cutoff=CUTOFF)
    ctx = gnm_context(xyz, cutoff=CUTOFF)
    hop = hop_from_seed(xyz, seed, cutoff=CUTOFF)
    euclid = euclid_from_seed_centroid(xyz, seed)
    A_bin = (np.abs(H - np.diag(np.diag(H))) > 0).astype(float)
    hop_dist = shortest_path(A_bin, method="D", unweighted=True, directed=False)
    nbh = hop_radius_neighborhoods(hop_dist, radius=1)
    t_star = natural_coherent_time(H)

    cols = {
        "degree": degree_centrality(xyz, cutoff=CUTOFF),
        "hop_prox": hop,
        "euclid_prox": euclid,
        "gnm_msf": ctx["msf"],
        "gnm_degree": ctx["degree"],
        "gnm_clust": ctx["clust"],
        "V_B": np.diag(V_B(bf)),
        "V_T": np.diag(V_T(len(xyz))),
        "V_R": np.diag(V_R(xyz, cutoff=CUTOFF, context=ctx)),
        "V_C": np.diag(V_C(xyz, cutoff=CUTOFF, context=ctx)),
        "V_M": np.diag(V_M(xyz, cutoff=CUTOFF, context=ctx)),
        "ctqw": np.nan_to_num(time_averaged_ctqw_converged(H, source=seed, coherent=False)),
        "chiral_circulation": np.abs(chiral_circulation_score(
            xyz, source=seed, cutoff=CUTOFF, field_scale=0.05, H_real=H)),
        "transport": transmission_from_source(H, seed, E=0.0),
        "spectral_coherence": spectral_coherence_score(H, seed, t_max=DEFAULT_T_MAX),
        "entanglement_entropy": entanglement_entropy_mixture(H, seed, nbh, t_star),
        "prs_low": prs_low(xyz, seed, cutoff=CUTOFF, k_modes=LOWMODE_K),
        "dcc_low": dcc_low(xyz, seed, cutoff=CUTOFF, k_modes=LOWMODE_K),
        "persistent_h2_void": void_score(xyz, thresh=16.0, min_persistence=2.5, top_k=1),
    }
    X = np.column_stack([np.nan_to_num(np.asarray(cols[f], float)) for f in FEATURE_NAMES])
    return dict(X=X, hop=hop, euclid=euclid, y=s["y"], elig=s["elig"], pdb=s["pdb"], protein=s["protein"])


def phase_a():
    CACHE.mkdir(parents=True, exist_ok=True)
    structures = build_structures()
    print(f"{len(structures)}/{len(ANN)} structures usable\n")
    n_done = n_new = 0
    t0 = time.monotonic()
    for i, s in enumerate(structures):
        f = CACHE / f"{s['pdb'].replace('/', '_')}.npz"
        if f.exists():
            n_done += 1
            continue
        try:
            feats = compute_features_one(s)
        except Exception as exc:  # noqa: BLE001
            print(f"  [{i+1}/{len(structures)}] {s['pdb']:<10} FAILED {exc!r}")
            continue
        np.savez_compressed(
            f, X=feats["X"][s["elig"]], hop=feats["hop"][s["elig"]], euclid=feats["euclid"][s["elig"]],
            y=feats["y"], protein=feats["protein"], pdb=feats["pdb"], N=s["N"],
        )
        n_new += 1
        if (i + 1) % 5 == 0:
            print(f"  [{i+1}/{len(structures)}] cached={n_done} new={n_new} "
                  f"elapsed={time.monotonic()-t0:.0f}s")
    print(f"\nPhase A done: {n_done} already cached, {n_new} newly computed "
          f"({time.monotonic()-t0:.0f}s)")


# ---------------------------------------------------------------- Phase B
def load_cache():
    rows = []
    for f in sorted(CACHE.glob("*.npz")):
        d = np.load(f, allow_pickle=True)
        rows.append(dict(X=d["X"], hop=d["hop"], euclid=d["euclid"], y=d["y"],
                          protein=str(d["protein"]), pdb=str(d["pdb"]), N=int(d["N"])))
    return rows


def phase_b(exclude_proximity: bool = False):
    rows = load_cache()
    print(f"Loaded {len(rows)} cached structures for Phase B\n")
    kept_features = [f for f in FEATURE_NAMES if not exclude_proximity or f not in ("hop_prox", "euclid_prox")]
    kept_idx = [FEATURE_NAMES.index(f) for f in kept_features]
    if exclude_proximity:
        print(f"--exclude-proximity: fitting on {len(kept_idx)}/{len(FEATURE_NAMES)} features "
              f"(dropped hop_prox, euclid_prox)\n")

    # ---- self-checks (this task's own Constraint: re-run TASK-0315's check) ----
    print("### Self-checks: joint residualisation on [hop, euclid] ###")
    hop_on_joint, euclid_on_joint, euclid_on_hop_only = [], [], []
    for r in rows:
        a = resid_auc_joint(r["hop"], r["y"], r["hop"], r["euclid"])
        b = resid_auc_joint(r["euclid"], r["y"], r["hop"], r["euclid"])
        if a is not None:
            hop_on_joint.append(a)
        if b is not None:
            euclid_on_joint.append(b)
        rh = rankdata(r["euclid"]); rp = rankdata(r["hop"])
        resid_uni = residualise(rh, rp.reshape(-1, 1))
        if np.ptp(resid_uni) > 1e-9:
            euclid_on_hop_only.append(float(roc_auc_score(r["y"], resid_uni)))
    print(f"  hop residualised on [hop,euclid] jointly:    mean={np.mean(hop_on_joint):.6f} (expect 0.5000 exactly)")
    print(f"  euclid residualised on [hop,euclid] jointly: mean={np.mean(euclid_on_joint):.6f} (expect 0.5000 exactly)")
    print(f"  euclid residualised on hop ALONE (univariate): mean={np.mean(euclid_on_hop_only):.4f} "
          f"(TASK-0315 found 0.61 on the frozen 20 -- checking if ASBench shows the same non-redundancy)")
    ok = abs(np.mean(hop_on_joint) - 0.5) < 1e-6 and abs(np.mean(euclid_on_joint) - 0.5) < 1e-6
    print(f"  Joint self-check {'PASSES' if ok else 'FAILS -- STOP, do not trust anything below'}.\n")
    if not ok:
        return 1

    # ---- reproduce TASK-0310's own CTQW/proximity numbers as a second harness check ----
    ctqw_idx = FEATURE_NAMES.index("ctqw")
    ctqw_raw = np.mean([roc_auc_score(r["y"], r["X"][:, ctqw_idx]) for r in rows
                         if np.ptp(r["X"][:, ctqw_idx]) > 0])
    ctqw_resid_joint = np.mean([v for v in (
        resid_auc_joint(r["X"][:, ctqw_idx], r["y"], r["hop"], r["euclid"]) for r in rows) if v is not None])
    print(f"### CTQW cross-check against TASK-0310 ###")
    print(f"  raw={ctqw_raw:.4f} (TASK-0310/0308 committed: 0.5921/0.5921)")
    print(f"  residualised jointly on [hop,euclid]: {ctqw_resid_joint:.4f} "
          f"(TASK-0310's hop-only residual was 0.5184 -- some difference from adding euclid is expected, not an error)\n")

    # ---- pool for LOPO-by-protein ----
    print("### Pooling residues across structures for LOPO-by-protein fit ###")
    X_all, y_all, prot_all, struct_all = [], [], [], []
    for si, r in enumerate(rows):
        X_all.append(r["X"][:, kept_idx]); y_all.append(r["y"])
        prot_all.extend([r["protein"]] * len(r["y"]))
        struct_all.extend([si] * len(r["y"]))
    X_all = np.vstack(X_all); y_all = np.concatenate(y_all)
    prot_all = np.array(prot_all); struct_all = np.array(struct_all)
    proteins = sorted(set(prot_all))
    print(f"  {X_all.shape[0]} pooled residue-rows, {X_all.shape[1]} features, "
          f"{len(proteins)} distinct proteins, {len(rows)} structures\n")

    print("### LOPO-by-protein: HistGradientBoostingClassifier, out-of-fold only ###")
    oof_score = np.full(len(y_all), np.nan)
    t0 = time.monotonic()
    for pi, prot in enumerate(proteins):
        test_mask = prot_all == prot
        train_mask = ~test_mask
        if y_all[train_mask].sum() == 0 or y_all[train_mask].sum() == train_mask.sum():
            continue
        clf = HistGradientBoostingClassifier(max_iter=150, max_depth=6, random_state=0)
        clf.fit(X_all[train_mask], y_all[train_mask])
        oof_score[test_mask] = clf.predict_proba(X_all[test_mask])[:, 1]
        if (pi + 1) % 20 == 0:
            print(f"  ... {pi+1}/{len(proteins)} proteins done ({time.monotonic()-t0:.0f}s)")
    print(f"  LOPO complete: {len(proteins)} folds, {time.monotonic()-t0:.0f}s\n")

    # ---- per-structure raw + residualised AUC on OOF scores ----
    print("### Ceiling: per-structure AUC on out-of-fold GBM scores ###")
    raw_aucs, resid_aucs = [], []
    for si, r in enumerate(rows):
        m = struct_all == si
        sc = oof_score[m]
        if not np.isfinite(sc).all() or np.ptp(sc) == 0:
            continue
        raw_aucs.append(float(roc_auc_score(r["y"], sc)))
        ra = resid_auc_joint(sc, r["y"], r["hop"], r["euclid"])
        if ra is not None:
            resid_aucs.append(ra)
    raw_aucs = np.array(raw_aucs); resid_aucs = np.array(resid_aucs)
    print(f"  n={len(raw_aucs)} structures scored")
    print(f"  RAW ceiling (no residualisation, sanity anchor vs proximity's own 0.6147): "
          f"mean={raw_aucs.mean():.4f} median={np.median(raw_aucs):.4f}")
    print(f"  RESIDUALISED ceiling (the decision statistic): "
          f"mean={resid_aucs.mean():.4f} median={np.median(resid_aucs):.4f}")
    _, p_wil = wilcoxon(resid_aucs - 0.5)
    print(f"  Wilcoxon vs 0.5: p={p_wil:.4g}")

    # ---- cluster-robust by protein (TASK-0310's own generalised sign-flip test) ----
    def cluster_sign_flip_test_generic(values, cluster_map, n_mc=100_000, seed=0):
        import itertools
        keys = [k for k in values if k in cluster_map]
        clusters = sorted(set(cluster_map[k] for k in keys))
        by_cluster = {c: [] for c in clusters}
        for k in keys:
            by_cluster[cluster_map[k]].append(values[k])
        cluster_sums = {c: sum(v) for c, v in by_cluster.items()}
        obs = sum(cluster_sums.values())
        n_clusters = len(clusters)
        rng = np.random.default_rng(seed)
        if n_clusters <= 20:
            null = np.array([sum(sg * cluster_sums[c] for sg, c in zip(signs, clusters))
                              for signs in itertools.product([1, -1], repeat=n_clusters)])
            exact = True
        else:
            signs = rng.choice([1, -1], size=(n_mc, n_clusters))
            sums_arr = np.array([cluster_sums[c] for c in clusters])
            null = signs @ sums_arr
            exact = False
        p = float(np.mean(np.abs(null) >= abs(obs) - 1e-9))
        return dict(n_rows=len(keys), n_clusters=n_clusters, p_value=p, exact=exact,
                    median=float(np.median([values[k] for k in keys])))

    protein_of = {r["pdb"]: r["protein"] for r in rows}
    resid_by_pdb = {}
    ri = 0
    for si, r in enumerate(rows):
        m = struct_all == si
        sc = oof_score[m]
        if not np.isfinite(sc).all() or np.ptp(sc) == 0:
            continue
        ra = resid_auc_joint(sc, r["y"], r["hop"], r["euclid"])
        if ra is not None:
            resid_by_pdb[r["pdb"]] = ra - 0.5
    cluster_result = cluster_sign_flip_test_generic(resid_by_pdb, protein_of)
    print(f"\n### Cluster-robust by protein ###")
    print(f"  n_rows={cluster_result['n_rows']} n_clusters={cluster_result['n_clusters']} "
          f"median={cluster_result['median']:+.4f} cluster-p={cluster_result['p_value']:.4g} "
          f"{'(exact)' if cluster_result['exact'] else '(Monte Carlo)'}")

    print("\n### Feature importance (permutation, last fold's held-out protein, "
          "descriptive only -- not the decision statistic) ###")
    from sklearn.inspection import permutation_importance
    last_test_mask = prot_all == proteins[-1]
    imp = None
    if last_test_mask.sum() > 10:
        pr = permutation_importance(clf, X_all[last_test_mask], y_all[last_test_mask],
                                     n_repeats=5, random_state=0, scoring="roc_auc")
        imp = pr.importances_mean
        for name, v in sorted(zip(kept_features, imp), key=lambda t: -t[1])[:8]:
            print(f"  {name:<22} {v:+.4f}")

    print("\n### Verdict, per this task's own pre-registered table ###")
    if resid_aucs.mean() < 0.53:
        print("  Residual ceiling ~0.50 -> the whole observable class is closed with an argument.")
        print("  Do NOT build TASK-0147 or TASK-0157; do not propose a tenth observable.")
    else:
        print("  Residual ceiling meaningfully > 0.50 -> something in the input IS reachable.")
        print("  TASK-0147 (structured bath) becomes rational, targeted against this ceiling.")

    OUT.mkdir(parents=True, exist_ok=True)
    if exclude_proximity:
        # TASK-0338 Part B: reproduce the committed no_proximity_feature_check.json
        # (same field set that file already has) rather than touching ceiling_result.json.
        out_path = OUT / "no_proximity_feature_check.json"
        out_path.write_text(json.dumps(dict(
            kept_features=kept_features,
            n=len(raw_aucs),
            raw_mean=float(raw_aucs.mean()), raw_median=float(np.median(raw_aucs)),
            resid_mean=float(resid_aucs.mean()), resid_median=float(np.median(resid_aucs)),
            wilcoxon_p=float(p_wil),
        ), indent=1))
        print(f"\nWrote {out_path}")
        return 0
    (OUT / "ceiling_result.json").write_text(json.dumps(dict(
        n_structures=len(rows), n_proteins=len(proteins),
        self_check=dict(hop_on_joint=float(np.mean(hop_on_joint)),
                         euclid_on_joint=float(np.mean(euclid_on_joint)),
                         euclid_on_hop_only=float(np.mean(euclid_on_hop_only))),
        ctqw_cross_check=dict(raw=float(ctqw_raw), resid_joint=float(ctqw_resid_joint)),
        raw_ceiling=dict(mean=float(raw_aucs.mean()), median=float(np.median(raw_aucs))),
        residual_ceiling=dict(mean=float(resid_aucs.mean()), median=float(np.median(resid_aucs)),
                               wilcoxon_p=float(p_wil)),
        cluster_robust=cluster_result,
        feature_importance_last_fold=dict(zip(kept_features, [float(x) for x in imp])) if imp is not None else None,
    ), indent=1))
    print(f"\nWrote {OUT}/ceiling_result.json")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase-b-only", action="store_true")
    ap.add_argument("--exclude-proximity", action="store_true",
                     help="TASK-0338: drop hop_prox/euclid_prox from the LOPO design matrix "
                          "and write no_proximity_feature_check.json instead of ceiling_result.json")
    args = ap.parse_args()
    if not args.phase_b_only:
        phase_a()
    return phase_b(exclude_proximity=args.exclude_proximity)


if __name__ == "__main__":
    sys.exit(main())
