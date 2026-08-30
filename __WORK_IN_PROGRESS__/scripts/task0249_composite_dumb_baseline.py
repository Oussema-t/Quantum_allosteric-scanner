"""TASK-0249 -- the composite "DUMB" baseline: fpocket druggability +
banded hop shell + degree_centrality + euclid_from_seed_centroid, versus
the collaborating thread's CTQW. Both evaluation designs (per-residue AUC,
this register's own; two-stage candidate ranking, the collaborating
thread's own), LOTO throughout, same footing for every arm.

Reuses, does not re-derive:
  - `task0242_two_stage_dryrun`'s own `CAND`/`prep`/`run`/`fpocket_candidates`
    (the collaborating thread's own apparatus, already validated by
    [[TASK-0243]]/[[TASK-0244]]) for the two-stage design and the frozen
    target set wiring.
  - `task0246_hop_contribution_anatomy.py`'s own one-hot hop-shell
    construction (`(hr==k) for k in range(1,9)`) verbatim -- the banded
    encoding this task's own spec calls for, already measured to beat the
    linear floor on 6/9 targets.
  - `allostery.baselines.degree_centrality`/`euclid_from_seed_centroid`,
    `allostery.hamiltonians.build_H_new`,
    `allostery.propagators.time_averaged_ctqw_converged`,
    `allostery.metrics.auc` -- this register's own established primitives,
    same as [[TASK-0245]].
  - [[TASK-0243]]'s own altloc="all" monkeypatch for `prody.parsePDB`
    (NAMPT_NPA1R's own real defect) when running on the frozen set.

Pre-registered before the first number was seen (this task's own
Constraint): feature list (4, see above), fitting rule (LOTO, pooled
OLS across N-1 targets' residue rows, `np.linalg.lstsq` -- matching
[[TASK-0245]]'s own established convention, not a new classifier), arms
(composite, ctqw, composite+ctqw, fpocket_drug alone, hop alone, random),
both designs, denominator = targets attempted.
"""
from __future__ import annotations

import json
import sys
import tempfile
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import prody  # noqa: E402
import yaml  # noqa: E402

prody.confProDy(verbosity="none")

# TASK-0243's own real, verified fix -- reused verbatim, not re-derived.
_orig_parsePDB = prody.parsePDB


def _parsePDB_all_altloc(*a, **kw):
    kw.setdefault("altloc", "all")
    return _orig_parsePDB(*a, **kw)


prody.parsePDB = _parsePDB_all_altloc

import task0242_two_stage_dryrun as t0242  # noqa: E402
from allostery.baselines import degree_centrality, euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from allostery.metrics import auc  # noqa: E402

OUT = _ROOT / "results/tasks/0249_composite_dumb_baseline"
FROZEN_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"
PRELIM_TARGETS = [  # TASK-0245's own 9-target set -- reported as preliminary only
    "KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "HIV1_RT",
    "PTP1B", "GLUCOKINASE", "CASPASE7", "GLUR2_TRU", "GLUK1_BPAM",
]
K_MAX_SHELL = 8  # task0246's own range(1,9)


def z(v):
    v = np.asarray(v, float)
    s = v.std()
    return (v - v.mean()) / (s if s > 1e-12 else 1.0)


def hop_onehot(hop_true: np.ndarray, k_max: int = K_MAX_SHELL) -> np.ndarray:
    """task0246_hop_contribution_anatomy.py's own encoding, verbatim."""
    return np.column_stack([(hop_true == k).astype(float) for k in range(1, k_max + 1)])


def fpocket_druggability_per_residue(pockets: list, resnums: np.ndarray,
                                     chain_ids: np.ndarray) -> np.ndarray:
    """Max druggability_score over every fpocket pocket a residue belongs
    to (0 if none) -- same aggregation rule as task0163's own
    `_fpocket_per_residue_scores`, adapted to task0242's own `resnums`
    and `druggability_score` (not cavity `score`, per this task's own
    feature-1 spec).

    TASK-0298: `pockets[i]["resnums"]` is now a set of (chain, resnum)
    tuples (was a plain int, which silently collapsed same-numbered
    residues across chains on a multi-chain apo selection -- exactly the
    defect this task exists to fix). `chain_ids` is a required parameter,
    not optional, so every call site must be explicit about which chain
    each `resnums[i]` belongs to rather than silently falling back to a
    bare-resnum lookup that would reintroduce the same bug."""
    lookup = {(str(c), int(rn)): i for i, (c, rn) in enumerate(zip(chain_ids, resnums))}
    out = np.zeros(len(resnums), dtype=np.float64)
    for p in pockets:
        d = p.get("druggability_score")
        if d is None:
            continue
        for c, rn in p["resnums"]:
            i = lookup.get((str(c), int(rn)))
            if i is not None:
                out[i] = max(out[i], d)
    return out


def target_rows(t: str):
    """One target's full residue-level feature/label data, apo-only,
    seed residues excluded (matching TASK-0245's own convention
    throughout). Returns None on any real failure (fetch/fpocket/empty
    seed), not silently zero-filled."""
    cfg, apo, seed, pocket = t0242.prep(t)
    coords = apo.coords
    cut = float(cfg.get("enm_cutoff", 8.0))
    resn = np.asarray(apo.resnums)
    n = len(coords)

    if len(seed) == 0:
        # Real, found-here data-quality gap in TASK-0243's own frozen set,
        # not a bug in this script's own math: `backend.active_site.
        # detect_active_site` returns source=none/active_site=[] for
        # 1M9D (HIV_INTEGRASE_MUT871/MUT916) on every one of its 4 chains
        # -- confirmed directly, not assumed -- contradicting that task's
        # own "zero fell back to a top-degree proxy" claim. An empty seed
        # would silently poison euclid_from_seed_centroid/CTQW with NaN if
        # allowed through (confirmed: this is exactly what crashed the
        # first real run's pooled LOTO fit). Treated as a target-attempted
        # failure, same as an fpocket stage-1 miss below -- not silently
        # excluded from the denominator, flagged in this task's own Done
        # section for whoever owns TASK-0243's curation next.
        print(f"  {t}: SKIP -- empty active-site seed (detect_active_site found nothing)")
        return None

    apo_ch = cfg.get("apo_chains") or cfg.get("chains")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        ag = prody.parsePDB(cfg["apo_pdb"], compressed=False).select(
            "protein and (" + " or ".join(f"chain {c}" for c in apo_ch) + ")"
        )
        pdb = tmp / f"{t.lower()}_apo.pdb"
        prody.writePDB(str(pdb), ag)
        pockets = t0242.fpocket_candidates(pdb, tmp)
    if isinstance(pockets, dict):
        return None

    hop_true = -hop_from_seed(coords, seed, cutoff=cut)  # flip back to true BFS distance
    fpocket_res = fpocket_druggability_per_residue(pockets, resn, apo.chain_ids)
    degree = degree_centrality(coords, cutoff=cut)
    euclid = euclid_from_seed_centroid(coords, seed)
    ctqw = time_averaged_ctqw_converged(build_H_new(coords, apo.bfactors, cutoff=cut), source=seed, coherent=False)

    m = np.ones(n, dtype=bool)
    m[seed] = False
    y = pocket.astype(int)[m]

    onehot = hop_onehot(hop_true)[m]
    X_composite = np.column_stack([z(fpocket_res)[m], onehot, z(degree)[m], z(euclid)[m]])
    X_hop_alone = onehot
    x_fpocket_alone = z(fpocket_res)[m]
    x_ctqw = z(ctqw)[m]

    return dict(
        target=t, y=y, X_composite=X_composite, X_hop=X_hop_alone,
        x_fpocket=x_fpocket_alone, x_ctqw=x_ctqw,
        n_pocket=int(y.sum()), pockets=pockets, resn=resn, seed=seed,
        coords=coords, bfactors=apo.bfactors, cut=cut, hop_true=hop_true,
    )


def _fit_ols(X, y):
    Xb = np.column_stack([X, np.ones(len(y))])
    b, *_ = np.linalg.lstsq(Xb, y.astype(float), rcond=None)
    return b


def _score_ols(X, b):
    Xb = np.column_stack([X, np.ones(len(X))])
    return Xb @ b


def loto_per_residue(data: dict, feature_key_fn) -> dict:
    """Leave-one-target-out: fit on pooled rows from every OTHER target,
    score the held-out target's own rows. `feature_key_fn(d)` returns the
    feature matrix for one target's `target_rows()` dict -- lets the same
    LOTO loop serve composite / hop-alone / composite+ctqw without
    duplicating the pooling logic."""
    names = list(data.keys())
    per_target_auc = {}
    oof_scores = {}
    for held_out in names:
        train = [t for t in names if t != held_out]
        X_train = np.concatenate([feature_key_fn(data[t]) for t in train], axis=0)
        y_train = np.concatenate([data[t]["y"] for t in train], axis=0)
        b = _fit_ols(X_train, y_train)
        X_test = feature_key_fn(data[held_out])
        scores = _score_ols(X_test, b)
        oof_scores[held_out] = scores
        per_target_auc[held_out] = float(auc(scores, data[held_out]["y"]))
    return {"per_target_auc": per_target_auc, "oof_scores": oof_scores}


def run_per_residue_design(data: dict) -> dict:
    arms = {}
    arms["composite"] = loto_per_residue(data, lambda d: d["X_composite"])
    arms["ctqw"] = loto_per_residue(data, lambda d: d["x_ctqw"].reshape(-1, 1))
    arms["composite+ctqw"] = loto_per_residue(
        data, lambda d: np.column_stack([d["X_composite"], d["x_ctqw"]])
    )
    arms["fpocket_drug"] = loto_per_residue(data, lambda d: d["x_fpocket"].reshape(-1, 1))
    arms["hop"] = loto_per_residue(data, lambda d: d["X_hop"])
    rng = np.random.default_rng(0)
    arms["random"] = {
        "per_target_auc": {
            t: float(auc(rng.random(len(d["y"])), d["y"])) for t, d in data.items()
        }
    }
    return arms


def candidate_features(pockets: list, res_idx_by_id: dict, resn: np.ndarray,
                        fpocket_res: np.ndarray, degree: np.ndarray, euclid: np.ndarray,
                        hop_true: np.ndarray) -> dict:
    """Aggregate the SAME 4 per-residue features to per-candidate level
    (mean over the candidate's own residues), for the two-stage design --
    same fitted weights (from the per-residue LOTO fit) apply unchanged."""
    out = {}
    for pid, ii in res_idx_by_id.items():
        if not ii:
            continue
        onehot_mean = hop_onehot(hop_true[ii]).mean(axis=0)
        out[pid] = dict(
            fpocket=float(fpocket_res[ii].mean()),
            onehot=onehot_mean,
            degree=float(degree[ii].mean()),
            euclid=float(euclid[ii].mean()),
        )
    return out


def run_two_stage_design(data: dict, composite_weights: dict, hop_weights: dict,
                          composite_ctqw_weights: dict) -> dict:
    """Rank candidates within each target's own fpocket list under every
    arm's LOTO-fitted weights (held out consistently: the weights used for
    a target here are the ones fit on every OTHER target, matching the
    per-residue design's own LOTO split exactly, not refit at this stage)."""
    zstats = {}  # per-arm feature z-score mean/std, computed on the SAME
    # pooled-training rows the per-residue LOTO fit used, so aggregated
    # candidate features are standardized consistently with what the
    # weights were fit against -- required since z() above is computed
    # per-target for residues but candidate aggregates need the same scale.
    names = list(data.keys())
    for held_out in names:
        train = [t for t in names if t != held_out]
        fpocket_train = np.concatenate([data[t]["_fpocket_raw"] for t in train])
        degree_train = np.concatenate([data[t]["_degree_raw"] for t in train])
        euclid_train = np.concatenate([data[t]["_euclid_raw"] for t in train])
        zstats[held_out] = dict(
            fpocket=(fpocket_train.mean(), fpocket_train.std() or 1.0),
            degree=(degree_train.mean(), degree_train.std() or 1.0),
            euclid=(euclid_train.mean(), euclid_train.std() or 1.0),
        )

    rows = []
    rng = np.random.default_rng(7)
    for t in names:
        d = data[t]
        r = t0242.run(t, tuned=False, return_state=True)
        if "error" in r:
            rows.append({"target": t, "error": r["error"]})
            continue
        kept, true_i = r["kept"], r["true_i"]
        res_idx_by_id = {c["id"]: c["res_idx"] for c in kept}
        cf = candidate_features(
            None, res_idx_by_id, d["resn"], d["_fpocket_raw"], d["_degree_raw"],
            d["_euclid_raw"], d["hop_true"],
        )
        mf, mdg, meu = zstats[t]["fpocket"], zstats[t]["degree"], zstats[t]["euclid"]
        ids = [c["id"] for c in kept]

        def _row(pid):
            f = cf[pid]
            fpz = (f["fpocket"] - mf[0]) / mf[1]
            dgz = (f["degree"] - mdg[0]) / mdg[1]
            euz = (f["euclid"] - meu[0]) / meu[1]
            return fpz, f["onehot"], dgz, euz

        Xc = np.array([np.concatenate([[a], b, [c_], [e]]) for a, b, c_, e in (_row(pid) for pid in ids)])
        Xh = np.array([_row(pid)[1] for pid in ids])
        ctqw_by_id = {c["id"]: c["ctqw"] for c in kept}
        xq = z(np.array([ctqw_by_id[pid] for pid in ids]))

        scores = {
            "composite": _score_ols(Xc, composite_weights[t]),
            "hop": _score_ols(Xh, hop_weights[t]),
            "composite+ctqw": _score_ols(np.column_stack([Xc, xq]), composite_ctqw_weights[t]),
            "fpocket_drug": np.array([c["fpocket_drug"] for c in kept]),
            "ctqw": np.array([c["ctqw"] for c in kept]),
            "random": rng.random(len(kept)),
        }
        ranks = {}
        for key, vals in scores.items():
            order = np.argsort(-np.asarray(vals, float))
            ranks[key] = int(np.where(order == true_i)[0][0]) + 1
        rows.append({"target": t, "n_kept": len(kept), "ranks": ranks})
    return rows


def _fit_all_loto_weights(data: dict, feature_key_fn) -> dict:
    names = list(data.keys())
    weights = {}
    for held_out in names:
        train = [t for t in names if t != held_out]
        X_train = np.concatenate([feature_key_fn(data[t]) for t in train], axis=0)
        y_train = np.concatenate([data[t]["y"] for t in train], axis=0)
        weights[held_out] = _fit_ols(X_train, y_train)
    return weights


def summarize_per_residue(arms: dict) -> None:
    print(f"\n=== Per-residue AUC, LOTO ===")
    for name, r in arms.items():
        vals = list(r["per_target_auc"].values())
        print(f"  {name:<16} median={np.median(vals):.4f}  "
              f"range=[{min(vals):.4f},{max(vals):.4f}]  n={len(vals)}")


def summarize_two_stage(rows: list, n_attempted: int) -> None:
    """`rows` must have exactly `n_attempted` entries -- one per target
    actually attempted, including targets that failed before the
    two-stage design ever ran (e.g. an empty active-site seed) as
    explicit `{"error": ...}` rows. Divides by `n_attempted` directly
    (not `len(rows)`/`np.mean`) so a caller passing a short `rows` list
    fails loudly instead of silently inflating the reported rate."""
    assert len(rows) == n_attempted, (
        f"summarize_two_stage: {len(rows)} rows but n_attempted={n_attempted} -- "
        "every attempted target must have a row (pad with explicit error "
        "rows for targets that failed before this design ran), or this "
        "function's own denominator claim is not actually being honored."
    )
    print(f"\n=== Two-stage candidate ranking, LOTO weights, denominator=targets attempted ({n_attempted}) ===")
    survivors = [r for r in rows if "error" not in r]
    print(f"  stage-1+seed survivors: {len(survivors)}/{n_attempted}")
    for key in ("composite", "ctqw", "composite+ctqw", "fpocket_drug", "hop", "random"):
        # MRR/top-1 over ALL attempted targets: any failure (empty seed,
        # fpocket stage-1 miss) counts as a miss (reciprocal rank 0, never
        # top-1) -- this task's own "denominator = targets attempted"
        # instruction, not the survivor subset alone.
        rr_sum = 0.0
        top1 = 0
        for r in rows:
            if "error" in r:
                continue
            rank = r["ranks"][key]
            rr_sum += 1.0 / rank
            if rank == 1:
                top1 += 1
        mean_rank_survivors = (
            np.mean([r["ranks"][key] for r in survivors]) if survivors else float("nan")
        )
        print(f"  {key:<16} MRR={rr_sum / n_attempted:.4f}  top-1={top1}/{n_attempted}  "
              f"(mean_rank among survivors={mean_rank_survivors:.2f})")


def main(prelim_only: bool = False) -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    print("### Preliminary run, TASK-0245's own 9-target set (not the headline) ###")
    prelim_data = {}
    for t in PRELIM_TARGETS:
        try:
            d = target_rows(t)
        except Exception as exc:  # noqa: BLE001
            print(f"{t}: FAILED {exc!r}")
            continue
        if d is None or d["n_pocket"] < 5:
            print(f"{t}: SKIP (fpocket failure or <5 positives)")
            continue
        prelim_data[t] = d
        print(f"{t}: n_pocket={d['n_pocket']} n_residues={len(d['y'])}")

    prelim_arms = run_per_residue_design(prelim_data)
    summarize_per_residue(prelim_arms)
    (OUT / "preliminary_per_residue.json").write_text(json.dumps(
        {k: v["per_target_auc"] for k, v in prelim_arms.items()}, indent=1))

    if prelim_only:
        return 0

    print("\n\n### Headline run, TASK-0243's own frozen 22-pair untuned set ###")
    new_cand = yaml.safe_load(FROZEN_CONFIG.read_text())["targets"]
    t0242.CAND = new_cand
    frozen_targets = list(new_cand.keys())

    frozen_data = {}
    pre_two_stage_failures = {}  # target -> reason, for targets that never
    # reach run_two_stage_design at all (e.g. empty seed) -- padded into
    # two_stage_rows below so summarize_two_stage's own n_attempted
    # assertion holds, not silently short.
    for t in frozen_targets:
        try:
            d = target_rows(t)
        except Exception as exc:  # noqa: BLE001
            print(f"{t}: FAILED {exc!r}")
            pre_two_stage_failures[t] = f"{type(exc).__name__}: {exc}"
            continue
        if d is None or d["n_pocket"] < 3:
            print(f"{t}: SKIP (fpocket failure, empty seed, or too few positives)")
            pre_two_stage_failures[t] = "fpocket failure, empty seed, or too few positives"
            continue
        # raw (unstandardized) features stashed for the two-stage design's
        # own LOTO-consistent standardization (see run_two_stage_design).
        cfg, apo, seed, pocket = t0242.prep(t)
        cut = float(cfg.get("enm_cutoff", 8.0))
        d["_fpocket_raw"] = fpocket_druggability_per_residue(d["pockets"], d["resn"], apo.chain_ids)
        d["_degree_raw"] = degree_centrality(d["coords"], cutoff=cut)
        d["_euclid_raw"] = euclid_from_seed_centroid(d["coords"], seed)
        frozen_data[t] = d
        print(f"{t}: n_pocket={d['n_pocket']} n_residues={len(d['y'])}")

    n_attempted = len(frozen_targets)
    frozen_arms = run_per_residue_design(frozen_data)
    summarize_per_residue(frozen_arms)

    composite_w = _fit_all_loto_weights(frozen_data, lambda d: d["X_composite"])
    hop_w = _fit_all_loto_weights(frozen_data, lambda d: d["X_hop"])
    composite_ctqw_w = _fit_all_loto_weights(
        frozen_data, lambda d: np.column_stack([d["X_composite"], d["x_ctqw"]])
    )
    two_stage_rows = run_two_stage_design(frozen_data, composite_w, hop_w, composite_ctqw_w)
    two_stage_rows += [{"target": t, "error": reason} for t, reason in pre_two_stage_failures.items()]
    summarize_two_stage(two_stage_rows, n_attempted)

    (OUT / "headline_per_residue.json").write_text(json.dumps(
        {k: v["per_target_auc"] for k, v in frozen_arms.items()}, indent=1))
    (OUT / "headline_two_stage.json").write_text(json.dumps(two_stage_rows, indent=1, default=str))
    print(f"\nWrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
