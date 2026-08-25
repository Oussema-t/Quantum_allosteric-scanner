"""TASK-0254 -- Part A: put fpocket in the variance-attribution stack,
order-independent (Shapley/LMG-style). Part B: screen the frozen set for
apo crypticity and cross-tabulate against TASK-0249's own per-target
fpocket_drug AUC.

Reuses, does not re-derive:
  - `task0249_composite_dumb_baseline.target_rows` (imported) for the
    frozen 22-target set's per-residue feature/label rows -- same fpocket
    apo-side candidates, same seed/pocket resolution, same altloc="all"
    monkeypatch, same n=20-usable filter (n_pocket >= 3, real seed).
  - `task0245_cv_attribution`'s own within-target 5-fold stratified CV /
    20-repeat / OLS-lstsq / out-of-fold-AUC protocol, extended from 2
    blocks (geometry, CTQW) to 3 (geometry, fpocket, CTQW) and from
    sequential to Shapley-averaged attribution (this task's own Part A
    requirement: order-independence, since geometry and fpocket are
    correlated and a fixed entry order misassigns shared variance).
  - `allostery.baselines.degree_centrality`/`euclid_from_seed_centroid`/
    `hop_from_seed`, `allostery.metrics.auc` -- this register's own
    established primitives.

Part B's overlap definition, pre-registered here before any number below
was computed (this task's own explicit instruction): a true-pocket
residue counts as "already open in apo" if it is a member of ANY apo-side
fpocket-detected pocket (`target_rows`'s own `pockets` list, all
candidates, not just the top-ranked one) -- residue-level, not
volume-level. Per-target crypticity = |true-pocket residues open in apo|
/ |true-pocket residues|. Pre-registered bar (from this task's own
filing, "suggested, from the external framing"): >80% open in apo means
the target tests static retrieval, not cryptic-site discovery.
"""
from __future__ import annotations

import itertools
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import yaml

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import task0242_two_stage_dryrun as t0242  # noqa: E402
import task0249_composite_dumb_baseline as t0249  # noqa: E402
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.metrics import auc  # noqa: E402
from sklearn.model_selection import StratifiedKFold  # noqa: E402

OUT = _ROOT / "results/tasks/0254_fpocket_variance_and_crypticity"
FROZEN_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"
N_FOLD, N_REP = 5, 20
CRYPTICITY_BAR = 0.80
BLOCKS = ["geometry", "fpocket", "ctqw"]


def z(v):
    v = np.asarray(v, float)
    s = v.std()
    return (v - v.mean()) / (s if s > 1e-12 else 1.0)


def cv_auc(X, y, n_rep: int = N_REP) -> float:
    """TASK-0245's own protocol verbatim: 5-fold stratified CV, N_REP
    repeats, OLS via lstsq per fold, mean out-of-fold AUC."""
    X = np.atleast_2d(X.T).T if X.ndim == 1 else X
    out = []
    for rep in range(n_rep):
        skf = StratifiedKFold(n_splits=N_FOLD, shuffle=True, random_state=rep)
        oof = np.zeros(len(y))
        for tr, te in skf.split(X, y):
            Xb_tr = np.column_stack([X[tr], np.ones(len(tr))])
            b, *_ = np.linalg.lstsq(Xb_tr, y[tr].astype(float), rcond=None)
            oof[te] = np.column_stack([X[te], np.ones(len(te))]) @ b
        out.append(float(auc(oof, y)))
    return float(np.mean(out))


def build_blocks(t: str, d: dict) -> dict:
    """Reconstruct TASK-0245's own geometry block (degree, euclid, hop --
    z-scored, seed rows excluded) plus fpocket and CTQW, from
    `target_rows`'s own returned dict -- recomputed from raw
    coords/seed/cutoff (not from `d`'s own z-scored `x_fpocket`/`x_ctqw`,
    which use the SAME z-scoring convention, so this is a consistency
    check as much as a build step)."""
    coords, seed, cut = d["coords"], d["seed"], d["cut"]
    n = len(coords)
    m = np.ones(n, dtype=bool)
    m[seed] = False
    geometry = np.column_stack([
        z(degree_centrality(coords, cutoff=cut))[m],
        z(euclid_from_seed_centroid(coords, seed))[m],
        z(hop_from_seed(coords, seed, cutoff=cut))[m],
    ])
    return dict(geometry=geometry, fpocket=d["x_fpocket"].reshape(-1, 1), ctqw=d["x_ctqw"].reshape(-1, 1))


def shapley_attribution(feat: dict, y: np.ndarray) -> dict:
    """Exact Shapley value over the 3 blocks (3! = 6 permutations, cheap
    to brute-force -- no sampling approximation needed). value(S) =
    (cv_auc(S) - 0.5)/0.5 for nonempty S, value(empty) = 0."""
    cache: dict = {}

    def value(subset: tuple) -> float:
        key = tuple(sorted(subset))
        if key in cache:
            return cache[key]
        if not key:
            v = 0.0
        else:
            X = np.column_stack([feat[b] for b in key])
            v = (cv_auc(X, y) - 0.5) / 0.5
        cache[key] = v
        return v

    shap = {b: [] for b in BLOCKS}
    for perm in itertools.permutations(BLOCKS):
        prefix: list = []
        for b in perm:
            before = value(tuple(prefix))
            prefix = prefix + [b]
            after = value(tuple(prefix))
            shap[b].append(after - before)
    shapley = {b: float(np.mean(shap[b])) for b in BLOCKS}
    full_share = value(tuple(BLOCKS))
    full_auc = 0.5 + 0.5 * full_share
    seq_gfq = {  # geometry -> fpocket -> ctqw, sequential
        "geometry": value(("geometry",)),
        "fpocket": value(("fpocket", "geometry")) - value(("geometry",)),
        "ctqw": full_share - value(("fpocket", "geometry")),
    }
    seq_fgq = {  # fpocket -> geometry -> ctqw, sequential (swapped order)
        "fpocket": value(("fpocket",)),
        "geometry": value(("fpocket", "geometry")) - value(("fpocket",)),
        "ctqw": full_share - value(("fpocket", "geometry")),
    }
    return dict(
        shapley=shapley, full_auc=full_auc, full_share=full_share,
        unexplained=1.0 - full_share, seq_geom_first=seq_gfq, seq_fpocket_first=seq_fgq,
        subset_aucs={",".join(k) if k else "(none)": 0.5 + 0.5 * v for k, v in cache.items()},
    )


def crypticity(d: dict) -> dict:
    # d["y"] excludes seed rows (masked) -- rebuild the resnum list under
    # the same mask used to build y, so indices line up exactly.
    seed = d["seed"]
    n = len(d["coords"])
    m = np.ones(n, dtype=bool)
    m[seed] = False
    resn_masked = np.asarray(d["resn"])[m]
    true_pocket_resn = set(int(r) for r, is_pocket in zip(resn_masked, d["y"]) if is_pocket)

    apo_open_resn: set = set()
    for p in d["pockets"]:
        apo_open_resn |= set(int(r) for r in p["resnums"])

    n_true = len(true_pocket_resn)
    n_open = len(true_pocket_resn & apo_open_resn)
    frac = n_open / n_true if n_true else float("nan")
    return dict(n_true_pocket=n_true, n_open_in_apo=n_open, fraction_open=frac,
                already_open=bool(frac >= CRYPTICITY_BAR) if n_true else None)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    new_cand = yaml.safe_load(FROZEN_CONFIG.read_text())["targets"]
    t0242.CAND = new_cand
    frozen_targets = list(new_cand.keys())

    data = {}
    for t in frozen_targets:
        try:
            d = t0249.target_rows(t)
        except Exception as exc:  # noqa: BLE001
            print(f"{t}: FAILED {exc!r}")
            continue
        if d is None or d["n_pocket"] < 3:
            print(f"{t}: SKIP (fpocket failure, empty seed, or too few positives)")
            continue
        data[t] = d
        print(f"{t}: n_pocket={d['n_pocket']} n_residues={len(d['y'])}")

    print(f"\n{len(data)}/{len(frozen_targets)} usable (matches TASK-0249's own n=20 filter)\n")

    # --- Part A ---
    print("### Part A: order-independent (Shapley) 4-block attribution ###")
    attribution = {}
    for t, d in data.items():
        feat = build_blocks(t, d)
        y = d["y"]
        result = shapley_attribution(feat, y)
        attribution[t] = result
        sh = result["shapley"]
        print(f"{t:24s} geom={100*sh['geometry']:+5.1f}%  fpocket={100*sh['fpocket']:+5.1f}%  "
              f"ctqw={100*sh['ctqw']:+5.1f}%  unexplained={100*result['unexplained']:5.1f}%  "
              f"(full AUC={result['full_auc']:.3f})")

    (OUT / "part_a_shapley_attribution.json").write_text(json.dumps(attribution, indent=1))

    geoms = [a["shapley"]["geometry"] for a in attribution.values()]
    fpockets = [a["shapley"]["fpocket"] for a in attribution.values()]
    ctqws = [a["shapley"]["ctqw"] for a in attribution.values()]
    unexs = [a["unexplained"] for a in attribution.values()]
    print(f"\nShapley shares (n={len(attribution)}):")
    print(f"  geometry     {100*min(geoms):+.0f} to {100*max(geoms):+.0f}%  (median {100*np.median(geoms):+.0f}%)")
    print(f"  fpocket      {100*min(fpockets):+.0f} to {100*max(fpockets):+.0f}%  (median {100*np.median(fpockets):+.0f}%)")
    print(f"  ctqw         {100*min(ctqws):+.0f} to {100*max(ctqws):+.0f}%  (median {100*np.median(ctqws):+.0f}%)")
    print(f"  unexplained  {100*min(unexs):.0f} to {100*max(unexs):.0f}%  (median {100*np.median(unexs):.0f}%)")

    # --- Part B ---
    print("\n### Part B: apo crypticity screen ###")
    crypt = {}
    for t, d in data.items():
        c = crypticity(d)
        crypt[t] = c
        flag = " *ALREADY-OPEN*" if c["already_open"] else ""
        print(f"{t:24s} {c['n_open_in_apo']:3d}/{c['n_true_pocket']:3d} = "
              f"{100*c['fraction_open']:5.1f}%{flag}")

    (OUT / "part_b_crypticity.json").write_text(json.dumps(crypt, indent=1))

    n_open_targets = sum(1 for c in crypt.values() if c["already_open"])
    print(f"\n{n_open_targets}/{len(crypt)} targets already-open in apo (>={100*CRYPTICITY_BAR:.0f}% overlap)")

    # Cross-tabulate against TASK-0249's own fpocket_drug per-target AUC.
    t0249_path = _ROOT / "results/tasks/0249_composite_dumb_baseline/headline_per_residue.json"
    if t0249_path.exists():
        t0249_aucs = json.loads(t0249_path.read_text())["fpocket_drug"]
        open_aucs = [t0249_aucs[t] for t in crypt if crypt[t]["already_open"] and t in t0249_aucs]
        cryptic_aucs = [t0249_aucs[t] for t in crypt if crypt[t]["already_open"] is False and t in t0249_aucs]
        print(f"\nfpocket_drug AUC (TASK-0249's own numbers), already-open targets "
              f"(n={len(open_aucs)}): median={np.median(open_aucs) if open_aucs else float('nan'):.3f}")
        print(f"fpocket_drug AUC, cryptic-testing targets "
              f"(n={len(cryptic_aucs)}): median={np.median(cryptic_aucs) if cryptic_aucs else float('nan'):.3f}")
        (OUT / "part_b_cross_tabulation.json").write_text(json.dumps(
            dict(already_open_fpocket_drug_auc={t: t0249_aucs[t] for t in crypt
                                                  if crypt[t]["already_open"] and t in t0249_aucs},
                 cryptic_fpocket_drug_auc={t: t0249_aucs[t] for t in crypt
                                            if crypt[t]["already_open"] is False and t in t0249_aucs}),
            indent=1))
    else:
        print(f"\nWARNING: {t0249_path} not found -- cross-tabulation skipped")

    print(f"\nWrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
