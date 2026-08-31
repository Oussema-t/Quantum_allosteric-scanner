"""TASK-0303 -- ENM global mode shift, ported from the external review's own
Experiment D (`.ai/reviews/2026-08-29 - distal pockets/expD_modeshift.py`)
into this repo's own pipeline, with two changes that task's own Scope
requires: this register's per-target `enm_cutoff` (Experiment D used a
uniform 7.3 A because `build_H_new`'s own per-target cutoff was unavailable
in that container -- its own handover section 3 flags this as a caveat that
must be cleared "before the cryptic conclusion is trusted"), and evaluation
as a STANDALONE ranker, not folded into `task0282_pocket_selection_sweep.
METRICS` (2026-08-31 lane-collision amendment: Lane B owns all task0282
runs while it re-runs the extended cohort; integrating this metric into
that family is deliberately deferred, not attempted here).

METHOD (APOP, Bagler & Sinha-style / the external review's own port):
fill a candidate pocket with dummy nodes at its fpocket alpha-sphere
centres, rebuild the GNM Kirchhoff, and measure how much the softest
non-trivial global modes stiffen. A pocket whose occupancy perturbs the
global dynamics is the allosteric candidate. THE CONFOUND, carried over
from Experiment D's own docstring: adding nodes always stiffens the
network, and a bigger pocket adds more nodes -- so two variants are
scored: `raw` (every alpha-sphere becomes a node) and `kfix` (k-means-
reduced to a FIXED k=8 nodes for every pocket, so pocket size cannot
enter through the node count). If only `raw` works, the result is a size
artifact.

Reuses, does not re-derive:
  - `task0242_two_stage_dryrun.prep`/`fpocket_candidates` -- apo
    candidate-pocket construction and seed/pocket resolution, matching
    `task0282_pocket_selection_sweep.build_target`'s own call shape
    exactly (not imported from that module -- this task's own Scope
    forbids touching it while Lane B owns it; a duplicate ~15-line
    reimplementation of the SAME upstream primitives, not a fork of its
    logic).
  - `allostery.potentials.gnm_context` -- the register's own shared,
    already-tested Kirchhoff eigendecomposition (TASK-0040), reused for
    both the base structure and the structure-plus-dummy-nodes variant,
    instead of Experiment D's own local from-scratch `kirchhoff`/
    `soft_eigs` reimplementation.
  - `task0254_fpocket_variance_and_crypticity.crypticity` -- the
    already-open/genuinely-cryptic stratum label (>=80% of the true
    pocket already open in apo), matching TASK-0260/0266/0268's own
    established reuse pattern, via `task0249_composite_dumb_baseline.
    target_rows`.
  - `task0261_cluster_robust_stats.CM`/`cluster_sign_flip_test` -- the
    13-cluster structure over the frozen 20 and its exact cluster-level
    sign-flip test, unchanged.
  - `task0249_composite_dumb_baseline.z` -- the register's own standard
    per-target z-score helper, used for the partial-correlation check.

Import-order discipline (TASK-0273/0276's own established fix, repeated
verbatim by every later task that touches prody.parsePDB directly): the
altloc="all" patch is applied before `allostery` is ever imported.

Run: ../.venv/bin/python3 scripts/task0303_enm_mode_shift.py
"""
from __future__ import annotations

import json
import sys
import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
from scipy.stats import spearmanr

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import prody  # noqa: E402
import yaml  # noqa: E402

prody.confProDy(verbosity="none")

_orig_parsePDB = prody.parsePDB


def _parsePDB_all_altloc(*a, **kw):
    kw.setdefault("altloc", "all")
    return _orig_parsePDB(*a, **kw)


prody.parsePDB = _parsePDB_all_altloc

import task0242_two_stage_dryrun as t0242  # noqa: E402
import task0249_composite_dumb_baseline as t0249  # noqa: E402
import task0254_fpocket_variance_and_crypticity as t0254  # noqa: E402
from allostery.potentials import gnm_context  # noqa: E402
from task0261_cluster_robust_stats import CM, cluster_sign_flip_test  # noqa: E402

OUT = _ROOT / "results/tasks/0303_enm_mode_shift"
FROZEN_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"
DROPPED = ["HIV_INTEGRASE_MUT871", "HIV_INTEGRASE_MUT916"]  # TASK-0253 finding, matches CM's own 20

NMODES = 10   # Experiment D's own choice, kept unchanged
KFIX = 8      # Experiment D's own fixed dummy-node budget


# ---------------------------------------------------------------------------
# APOP mode shift, ported -- gnm_context replaces Experiment D's own local
# kirchhoff()/soft_eigs() reimplementation; everything else is the same
# computation.
# ---------------------------------------------------------------------------

def soft_eigs(coords: np.ndarray, cutoff: float, m: int = NMODES) -> np.ndarray:
    ctx = gnm_context(coords, cutoff)
    w = ctx["w"][ctx["nz"]]
    return w[:m]


def mode_shift(base_coords: np.ndarray, base_eigs: np.ndarray, dummies: np.ndarray, cutoff: float) -> float:
    if dummies is None or len(dummies) == 0:
        return float("nan")
    allc = np.vstack([base_coords, np.asarray(dummies, float)])
    w = soft_eigs(allc, cutoff)
    n = min(len(w), len(base_eigs))
    if n == 0:
        return float("nan")
    return float(np.mean((w[:n] - base_eigs[:n]) / base_eigs[:n]))


def kmeans(pts: np.ndarray, k: int, iters: int = 25, seed: int = 0) -> np.ndarray:
    """Ported verbatim from Experiment D -- a small, self-contained k-means,
    not this register's own utility (none exists), used only to reduce a
    pocket's own alpha-sphere cloud to a fixed node budget so pocket size
    cannot re-enter through node count."""
    pts = np.asarray(pts, float)
    if len(pts) <= k:
        return pts
    rng = np.random.default_rng(seed)
    c = pts[rng.choice(len(pts), k, replace=False)]
    for _ in range(iters):
        d = np.linalg.norm(pts[:, None, :] - c[None, :, :], axis=-1)
        lab = d.argmin(1)
        new = np.array([pts[lab == j].mean(0) if (lab == j).any() else c[j] for j in range(k)])
        if np.allclose(new, c):
            break
        c = new
    return c


def _parse_vert_pqr(path: Path) -> np.ndarray:
    """Alpha-sphere centre coordinates fpocket writes per pocket -- not
    exposed by `t0242.fpocket_candidates`'s own return dict (residue-level
    only), so parsed directly here. PQR is whitespace-delimited (not
    fixed-width like PDB); x/y/z are the 3 fields before the trailing
    charge/radius pair."""
    pts = []
    if not path.exists():
        return np.zeros((0, 3))
    for line in path.read_text().splitlines():
        if line.startswith("ATOM"):
            parts = line.split()
            if len(parts) >= 5:
                pts.append([float(parts[-5]), float(parts[-4]), float(parts[-3])])
    return np.asarray(pts, float)


# ---------------------------------------------------------------------------
# Per-target candidate construction -- mirrors task0282_pocket_selection_
# sweep.build_target's own call shape (t0242.prep + t0242.fpocket_candidates
# + the same (chain,resnum)-keyed idx_of, TASK-0298's own fix), NOT
# imported from that module per this task's own lane-collision amendment.
# ---------------------------------------------------------------------------

def build_target(t: str):
    cfg2, apo, seed, pocket = t0242.prep(t)
    if len(seed) == 0:
        return {"error": "empty active-site seed"}
    coords = apo.coords
    cut = float(cfg2.get("enm_cutoff", 8.0))  # per-target cutoff, THE fix this task's Scope requires
    resn = np.asarray(apo.resnums)
    chids = np.asarray(apo.chain_ids)
    idx_of = {(str(c), int(r)): i for i, (c, r) in enumerate(zip(chids, resn))}
    apo_ch = cfg2.get("apo_chains") or cfg2.get("chains")

    base_eigs = soft_eigs(coords, cut)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        ag = prody.parsePDB(cfg2["apo_pdb"], compressed=False).select(
            "protein and (" + " or ".join(f"chain {c}" for c in apo_ch) + ")"
        )
        pdb = tmp / f"{t.lower()}_apo.pdb"
        prody.writePDB(str(pdb), ag)
        pockets = t0242.fpocket_candidates(pdb, tmp)
        if isinstance(pockets, dict):
            return {"error": pockets["error"]}
        outdir = tmp / f"{pdb.stem}_out" / "pockets"

        cands = []
        for p in pockets:
            ii = [idx_of[r] for r in p["resnums"] if r in idx_of]
            if not ii:
                continue
            ii = np.asarray(ii, dtype=int)
            n_res = int(len(ii))
            overlap_count = int(pocket[ii].sum())
            vert = _parse_vert_pqr(outdir / f"pocket{p['id']}_vert.pqr")
            cands.append({
                "id": p["id"], "n_res": n_res, "n_vert": int(len(vert)),
                "overlap_count": overlap_count, "EH": overlap_count / n_res,
                "fpocket_drug": float(p.get("druggability_score") or 0.0),
                "mode_shift_raw": mode_shift(coords, base_eigs, vert, cut),
                "mode_shift_kfix": mode_shift(coords, base_eigs, kmeans(vert, KFIX), cut) if len(vert) else float("nan"),
            })
    if not cands:
        return {"error": "fpocket found no residue-resolvable candidates"}
    return {"cands": cands, "n_pocket": int(pocket.sum())}


# ---------------------------------------------------------------------------
# Standalone ranker evaluation
# ---------------------------------------------------------------------------

def ranker_eh(cands: list, key: str) -> float:
    survivors = [c for c in cands if not np.isnan(c[key])]
    if not survivors:
        return float("nan")
    top = max(survivors, key=lambda c: c[key])
    return float(top["EH"])


def random_eh(cands: list) -> float:
    return float(np.mean([c["EH"] for c in cands]))


def truth_percentile(cands: list, n_pocket: int, key: str) -> float:
    """Experiment D's own exact statistic (not this register's EH-of-
    selected-candidate ranker statistic above) -- added for a genuine
    apples-to-apples check against its own reported open-stratum p-values,
    since `ranker_eh` and this percentile answer different questions (does
    picking the top candidate work, vs where does the TRUE candidate rank
    among all of them). Truth = max-RECALL candidate (this register's own
    `oracle_and_random` convention, `task0282_pocket_selection_sweep`'s
    own definition -- not Experiment D's own max-Jaccard truth, since this
    register's own established oracle definition is reused for
    consistency with every other task in this family, not re-derived).
    Lower = better (fraction of candidates scoring >= the truth
    candidate's own value; 1/n_candidates is a unique top rank)."""
    survivors = [c for c in cands if not np.isnan(c[key])]
    if not survivors:
        return float("nan")
    truth = max(cands, key=lambda c: c["overlap_count"] / max(1, n_pocket))
    if np.isnan(truth[key]):
        return float("nan")
    r = sum(1 for c in survivors if c[key] >= truth[key])
    return r / len(survivors)


def fisher_combine(ps: list) -> float:
    """Experiment D's own combination, ported verbatim."""
    from scipy.stats import chi2
    ps = np.clip(np.asarray(ps, float), 1e-12, 1.0)
    return float(chi2.sf(-2 * np.log(ps).sum(), 2 * len(ps)))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    new_cand = yaml.safe_load(FROZEN_CONFIG.read_text())["targets"]
    t0242.CAND = new_cand
    targets = [t for t in new_cand if t not in DROPPED]
    assert set(targets) == set(CM.keys()), "target set must match task0261's own 20-target CM"

    per_target = {}
    crypt = {}
    print(f"{'target':<20}{'n_cand':>7}{'EH_random':>11}{'EH_raw':>9}{'EH_kfix':>9}{'open?':>7}")
    for t in targets:
        r = build_target(t)
        if "error" in r:
            print(f"{t:<20}  SKIP -- {r['error']}")
            continue
        cands = r["cands"]
        n_pocket = r["n_pocket"]
        eh_rand = random_eh(cands)
        eh_raw = ranker_eh(cands, "mode_shift_raw")
        eh_kfix = ranker_eh(cands, "mode_shift_kfix")
        pct_raw = truth_percentile(cands, n_pocket, "mode_shift_raw")
        pct_kfix = truth_percentile(cands, n_pocket, "mode_shift_kfix")
        try:
            d = t0249.target_rows(t)
            crypt[t] = t0254.crypticity(d)
        except Exception as exc:  # noqa: BLE001
            crypt[t] = {"already_open": None, "fraction_open": float("nan"), "error": str(exc)}
        per_target[t] = {
            "n_cand": len(cands), "n_pocket": n_pocket,
            "eh_random": eh_rand, "eh_raw": eh_raw, "eh_kfix": eh_kfix,
            "pct_raw": pct_raw, "pct_kfix": pct_kfix,
            "already_open": crypt[t]["already_open"], "fraction_open": crypt[t].get("fraction_open"),
            "cands": cands,
        }
        print(f"{t:<20}{len(cands):>7}{eh_rand:>11.4f}{eh_raw:>9.4f}{eh_kfix:>9.4f}"
              f"{str(crypt[t]['already_open']):>7}  pct_raw={pct_raw:.3f} pct_kfix={pct_kfix:.3f}")

    # --- standalone significance: selected EH - random EH, cluster-robust ---
    print("\n### Standalone ranker vs random, cluster-robust (TASK-0261's exact sign-flip test) ###")
    for key, label in [("eh_raw", "raw"), ("eh_kfix", "kfix")]:
        deltas = {t: per_target[t][key] - per_target[t]["eh_random"]
                  for t in per_target if not np.isnan(per_target[t][key])}
        res = cluster_sign_flip_test(deltas)
        print(f"  {label:<6} n={len(deltas):<3} n_clusters={res['n_clusters']:<3} "
              f"mean_delta={np.mean(list(deltas.values())):+.4f}  p={res['p_value']:.4f}")

    # --- stratified by crypticity ---
    print("\n### Crypticity-stratified (already-open vs genuinely-cryptic) ###")
    straddling = {c for c in set(CM.values())
                  if len({per_target[t]["already_open"] for t in per_target
                          if CM.get(t) == c and per_target[t]["already_open"] is not None}) > 1}
    if straddling:
        print(f"  Straddling cluster(s) excluded from this stratification only: {sorted(straddling)}")
    for key, label in [("eh_raw", "raw"), ("eh_kfix", "kfix")]:
        for open_flag, name in [(True, "open"), (False, "cryptic")]:
            sub = {t: per_target[t][key] - per_target[t]["eh_random"] for t in per_target
                   if per_target[t]["already_open"] == open_flag and CM.get(t) not in straddling
                   and not np.isnan(per_target[t][key])}
            if not sub:
                continue
            res = cluster_sign_flip_test(sub)
            print(f"  {label:<6} {name:<8} n={len(sub):<3} n_clusters={res['n_clusters']:<3} "
                  f"mean_delta={np.mean(list(sub.values())):+.4f}  p={res['p_value']:.4f}")

    # --- apples-to-apples check against Experiment D's own exact statistic ---
    print("\n### Truth-percentile + Fisher combination (Experiment D's own exact statistic, for direct comparison) ###")
    for key, label in [("pct_raw", "raw"), ("pct_kfix", "kfix")]:
        for open_flag, name in [(True, "open"), (False, "cryptic"), (None, "ALL")]:
            sub = [t for t in per_target if not np.isnan(per_target[t][key])
                   and (open_flag is None or (per_target[t]["already_open"] == open_flag
                                               and CM.get(t) not in straddling))]
            if not sub:
                continue
            vals = [per_target[t][key] for t in sub]
            p_fisher = fisher_combine(vals)
            n_rank1 = sum(1 for t in sub if per_target[t][key] <= 1.0 / max(1, per_target[t]["n_cand"]) + 1e-9)
            print(f"  {label:<6} {name:<8} n={len(sub):<3} median_pct={np.median(vals):.3f}  "
                  f"rank-1={n_rank1}/{len(sub)}  Fisher_p={p_fisher:.3g}")

    # --- independence check: partial correlation, mode_shift_kfix vs fpocket_drug, controlling n_res ---
    print("\n### Independence: partial correlation of mode_shift_kfix with fpocket_drug, controlling pocket size ###")
    from task0249_composite_dumb_baseline import z as zscore
    ms_all, drug_all, size_all = [], [], []
    for t, d in per_target.items():
        cs = [c for c in d["cands"] if not np.isnan(c["mode_shift_kfix"])]
        if len(cs) < 3:
            continue
        ms_all.append(zscore([c["mode_shift_kfix"] for c in cs]))
        drug_all.append(zscore([c["fpocket_drug"] for c in cs]))
        size_all.append(zscore([c["n_res"] for c in cs]))
    ms_all = np.concatenate(ms_all)
    drug_all = np.concatenate(drug_all)
    size_all = np.concatenate(size_all)

    def residualize(y, x):
        A = np.column_stack([x, np.ones_like(x)])
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        return y - A @ coef

    ms_resid = residualize(ms_all, size_all)
    drug_resid = residualize(drug_all, size_all)
    rho_raw, p_raw = spearmanr(ms_all, drug_all)
    rho_partial, p_partial = spearmanr(ms_resid, drug_resid)
    print(f"  Spearman(mode_shift_kfix, fpocket_drug), pooled per-target-z, n={len(ms_all)}: "
          f"rho={rho_raw:.3f} (p={p_raw:.3g})")
    print(f"  Partial (controlling pocket size n_res via OLS residualisation): "
          f"rho={rho_partial:.3f} (p={p_partial:.3g})")

    out = {"per_target": per_target,
           "independence": {"rho_raw": float(rho_raw), "p_raw": float(p_raw),
                             "rho_partial_controlling_size": float(rho_partial), "p_partial": float(p_partial)}}
    (OUT / "mode_shift.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"\nWrote {OUT / 'mode_shift.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
