#!/usr/bin/env python3
"""TASK-0380 -- where are the best seeds? Residualise the seed-axis
capacity on distance to the pocket.

[[TASK-0379]] measured that seed-set choice alone reaches best-of-2000
AUC 0.85-0.96, with a statistically significant excess of +0.11 to +0.16
over a matched label-permutation null on 6/7 targets -- but never asked
WHERE the winning seeds are. Spatially-contiguous patches beat scattered
subsets roughly two-to-one (patch excess +0.22 to +0.33 vs scattered
+0.11 to +0.16), which is the shape of a location effect, not a
biological one. This task tests that directly.

RECOVERY, not new sampling (this task's own Scope item 1). TASK-0379's
`result.json` persisted summary statistics only, not the 2000+2000 draws
themselves. But `run_target` seeds `np.random.default_rng(det_seed(name))`
and draws deterministically in a fixed order (2000 scattered residue
draws, THEN 2000 spatial-patch draws, THEN 200 label-permutation null
draws) -- replaying that exact call sequence, with the exact same
`H_new`/`eigh` (itself deterministic given the same apo coords/bfactors/
cutoff), reproduces the identical 2000+2000 seed sets bit-for-bit. This
script imports `task0379_seed_capacity_and_definition` directly and
reuses its `det_seed`/`spatial_patch`/`occ_auc`/`vectorized_auc_many`/
`load_target_config` rather than re-deriving any of them, so there is no
second implementation to drift from the first.

VALIDATION GATE (this task's own Constraint): before anything is built
on the recovered draws, this script asserts the regenerated
best-of-2000 AUCs equal TASK-0379's own committed `result.json` values
EXACTLY (bit-for-bit, not `np.isclose`) for every one of the 7 targets,
both seed families, AND the matched-null's best-of-N mean. If any
target fails this, the script raises before computing anything else --
the recovery would be wrong, not merely imprecise.

THE DECISIVE TEST (item 3, `residualise` below): for each of the 2000
scattered draws and, separately, each of the 2000 patch draws, compute
the seed set's Ca centroid and its Euclidean distance to the TRUE
drug-pocket centroid (`labels_obj.pocket`'s own residues, not the seed).
Rank-residualise seed-set AUC on that distance -- TASK-0310's own
rank-OLS convention (`residualise()` below is that function's exact
formula, reused verbatim, not reimplemented), the standard this
register has applied to every other axis since TASK-0308. Recompute
best-of-N and its excess over a matched null BOTH before (raw AUC,
already validated against TASK-0379's own numbers) and after
residualisation, using the SAME null machinery: the label-permutation
null's own per-draw AUCs are rank-residualised on the SAME (label-
independent) distance ranks, then best-of-N is taken of THAT, giving a
null distribution for the residualised statistic exactly as TASK-0379's
own null was a distribution for the raw statistic. If the excess
vanishes after residualisation, the seed axis carries nothing but
location, exactly as nine other observables in this register have died
at this step (per this task's own pre-registered prediction).

ITEM 4 -- candidate list, stated BEFORE computing (this task's own
requirement, so a post-hoc match cannot be reported as a prediction):
sequence conservation (`task0274_conservation_chemistry_residual`'s own
Pfam-seed-alignment machinery, reused, not reimplemented), betweenness
centrality, closeness centrality (`allostery.baselines`, reused),
burial (BioPython ShrakeRupley SASA via `allostery.corex.per_atom_asa`/
`per_residue_native_asa`, reused -- same convention `task0257_r2_sasa_
burial_vs_degree.py::per_residue_sasa` already established), and a
hinge-residue proxy (negated |lowest non-trivial GNM eigenvector
component| -- `task0226_observable_family_confound_pdb_retest.py::
slow1_minima_score`'s own convention, reused, built here from
`allostery.potentials.gnm_context`'s shared Kirchhoff eigendecomposition
rather than re-deriving it a third time). Degree centrality is added
alongside betweenness/closeness for free (same `allostery.baselines`
call, same cost) though it is not in the task's own named list --
reported as a bonus, not substituted for anything on the list.
For each candidate feature and each seed family, Spearman-correlate the
per-draw mean member-residue feature value against (a) raw AUC and (b)
distance-residualised AUC across the 2000 draws -- (b) asks whether the
feature explains anything raw AUC does not already get from location.

Item 5: the true active site's own centroid-to-pocket distance, reported
against the same distributions used above.

OUT OF SCOPE (this task's own Constraints): no new sampling, no new
operator/score, no cohort change -- inherits TASK-0379's fixed H_new /
time_averaged_ctqw_converged(coherent=False) exactly. No shipped seed,
residue or number changes; this is a read-only re-analysis of an
existing, already-committed result. CASPASE1/CASPASE7 (n_seed=2) are
recovered and reported but flagged, not averaged into the 5-target
headline, per TASK-0379's own note on their reliability.

Run: ../.venv/bin/python3 -u scripts/task0380_seed_location_residualisation.py [--pilot]
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
from scipy.stats import rankdata, spearmanr

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
RESULTS = HERE.parent / "results" / "tasks" / "0380_seed_location_residualisation"
RESULTS.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(REPO_ROOT))

import task0379_seed_capacity_and_definition as t0379  # noqa: E402
import task0274_conservation_chemistry_residual as t0274  # noqa: E402
from allostery.baselines import (  # noqa: E402
    degree_centrality, betweenness_centrality, closeness_centrality,
)
from allostery.potentials import gnm_context  # noqa: E402
from allostery.corex import per_atom_asa, per_residue_native_asa  # noqa: E402
from backend.data_layer import fetch as fetch_pdb_file  # noqa: E402
import Bio.PDB as PDB  # noqa: E402

TARGETS = t0379.TARGETS
N_RANDOM = 2000
N_PERM = 200


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# --------------------------------------------------------------- residualise
def residualise(y_ranks: np.ndarray, x_ranks: np.ndarray) -> np.ndarray:
    """TASK-0310's own rank-OLS-residualisation formula
    (`task0310_family_residualised_on_proximity.py::residualise`), copied
    verbatim (4 lines, not worth a cross-module import with that script's
    own heavy module-level globals) rather than re-derived."""
    A = np.column_stack([x_ranks, np.ones_like(x_ranks)])
    coef, *_ = np.linalg.lstsq(A, y_ranks, rcond=None)
    return y_ranks - A @ coef


def hinge_score(coords: np.ndarray, cutoff: float) -> np.ndarray:
    """Negated |lowest non-trivial GNM eigenvector component| -- higher =
    closer to that mode's hinge/node. `task0226_observable_family_
    confound_pdb_retest.py::slow1_minima_score`'s own convention, built
    from `allostery.potentials.gnm_context`'s shared Kirchhoff
    eigendecomposition (reused, not re-derived a third time in this
    register)."""
    ctx = gnm_context(coords, cutoff)
    nz_idx = np.flatnonzero(ctx["nz"])
    m1 = ctx["U"][:, nz_idx[0]]
    return -np.abs(m1)


def burial_score(apo) -> np.ndarray:
    """Higher = more buried (negated SASA). Same BioPython ShrakeRupley
    route as `task0257_r2_sasa_burial_vs_degree.py::per_residue_sasa`,
    reused via `allostery.corex`'s own helpers, computed on the full
    deposited model (every chain) then indexed to `apo`'s own kept
    residues -- identical convention, independent call site."""
    fp = fetch_pdb_file(apo.pdb_id)
    structure = PDB.PDBParser(QUIET=True).get_structure(apo.pdb_id, fp)
    model = structure[0]
    per_atom_asa(model)
    asa_by_key: dict[tuple[str, int], float] = {}
    for chain in model:
        for resnum, asa in per_residue_native_asa(chain).items():
            asa_by_key[(chain.id, int(resnum))] = asa
    sasa = np.full(len(apo.resnums), np.nan)
    for i, (c, r) in enumerate(zip(apo.chain_ids, apo.resnums)):
        sasa[i] = asa_by_key.get((str(c), int(r)), np.nan)
    if np.isnan(sasa).any():
        sasa[np.isnan(sasa)] = np.nanmedian(sasa)
    return -sasa


def best_of_n_and_null(auc_matrix_row: np.ndarray, null_matrix: np.ndarray) -> tuple[float, float, float, float]:
    """(best, null_mean, excess, p) for one family's real draws vs its
    null replicates -- `null_matrix` is (n_perm, n_random)."""
    best = float(np.max(auc_matrix_row))
    null_best = null_matrix.max(axis=1)
    return best, float(null_best.mean()), best - float(null_best.mean()), float(np.mean(null_best >= best))


def recover_target(target_name: str, n_random: int, n_perm: int, rng_seed: int, committed: dict, validate: bool = True) -> dict:
    _log(f"{target_name}: recovering draws (rng_seed={rng_seed})...")
    target_config = t0379.load_target_config(target_name)
    cutoff = float(target_config.get("enm_cutoff", t0379.rc.DEFAULT_CUTOFF))
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", t0379.rc.DEFAULT_POCKET_CUTOFF))

    apo, holo = t0379.rc._load_apo_holo(target_name, target_config)
    labels_obj = t0379.build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    pocket_label = np.asarray(labels_obj.pocket).astype(int)
    N = len(apo.resnums)
    true_source = np.where(labels_obj.active_site)[0]
    H = t0379.build_H_new(apo.coords, apo.bfactors, cutoff=cutoff)
    w, v = np.linalg.eigh(H)
    true_auc, _ = t0379.occ_auc(true_source, w, v, pocket_label)
    n_seed = len(true_source)

    rng = np.random.default_rng(rng_seed)

    seeds_residue = np.empty((n_random, n_seed), dtype=int)
    random_residue_aucs = np.empty(n_random)
    random_residue_occ = np.empty((n_random, N))
    for i in range(n_random):
        seed = rng.choice(N, size=n_seed, replace=False)
        seeds_residue[i] = seed
        a, occ = t0379.occ_auc(seed, w, v, pocket_label)
        random_residue_aucs[i] = a
        random_residue_occ[i] = occ

    patch_centers = np.empty(n_random, dtype=int)
    seeds_patch = np.empty((n_random, n_seed), dtype=int)
    random_patch_aucs = np.empty(n_random)
    random_patch_occ = np.empty((n_random, N))
    for i in range(n_random):
        center = rng.integers(0, N)
        patch = t0379.spatial_patch(apo.coords, center, n_seed)
        patch_centers[i] = center
        seeds_patch[i] = patch
        a, occ = t0379.occ_auc(patch, w, v, pocket_label)
        random_patch_aucs[i] = a
        random_patch_occ[i] = occ

    # ---------------- VALIDATION GATE (this task's own Constraint) ----------------
    # Only meaningful at n_random=2000/n_perm=200 -- TASK-0379's own committed
    # numbers were produced at that exact size, and a different n_random walks
    # the RNG stream to different draws by construction. --pilot (reduced N,
    # for wiring smoke-tests only) skips this gate rather than reporting a
    # false mismatch.
    best_residue = float(np.max(random_residue_aucs))
    best_patch = float(np.max(random_patch_aucs))
    c = committed[target_name]["arm_a"]
    if validate:
        if best_residue != c["best_of_n_random_residue"] or best_patch != c["best_of_n_random_patch"]:
            raise RuntimeError(
                f"{target_name}: RECOVERY MISMATCH -- residue {best_residue!r} vs committed "
                f"{c['best_of_n_random_residue']!r}; patch {best_patch!r} vs committed "
                f"{c['best_of_n_random_patch']!r}. Stopping per this task's own gate."
            )
        _log(f"  validated: best_of_n residue={best_residue!r} patch={best_patch!r} match TASK-0379 exactly")
    else:
        _log(f"  --pilot: skipping exact-match gate (n_random={n_random} != 2000)")

    n_pocket = int(pocket_label.sum())
    null_vals_r = np.empty((n_perm, n_random))
    null_vals_p = np.empty((n_perm, n_random))
    for k in range(n_perm):
        perm_idx = rng.permutation(N)[:n_pocket]
        perm_label = np.zeros(N, dtype=int)
        perm_label[perm_idx] = 1
        null_vals_r[k] = t0379.vectorized_auc_many(random_residue_occ, perm_label)
        null_vals_p[k] = t0379.vectorized_auc_many(random_patch_occ, perm_label)

    null_best_residue_mean = float(null_vals_r.max(axis=1).mean())
    null_best_patch_mean = float(null_vals_p.max(axis=1).mean())
    if validate:
        if null_best_residue_mean != c["null_best_of_n_residue_mean"] or null_best_patch_mean != c["null_best_of_n_patch_mean"]:
            raise RuntimeError(
                f"{target_name}: NULL RECOVERY MISMATCH -- residue null mean {null_best_residue_mean!r} vs "
                f"committed {c['null_best_of_n_residue_mean']!r}; patch {null_best_patch_mean!r} vs "
                f"committed {c['null_best_of_n_patch_mean']!r}."
            )
        _log("  validated: matched-null best-of-N means match TASK-0379 exactly")

    # ---------------- LOCATE (item 2) ----------------
    pocket_idx = np.flatnonzero(pocket_label)
    pocket_centroid = apo.coords[pocket_idx].mean(axis=0)
    dist_residue = np.linalg.norm(apo.coords[seeds_residue].mean(axis=1) - pocket_centroid, axis=1)
    dist_patch = np.linalg.norm(apo.coords[seeds_patch].mean(axis=1) - pocket_centroid, axis=1)
    true_centroid = apo.coords[true_source].mean(axis=0)
    true_dist = float(np.linalg.norm(true_centroid - pocket_centroid))
    pct_true_dist_vs_residue = float(np.mean(dist_residue >= true_dist))
    pct_true_dist_vs_patch = float(np.mean(dist_patch >= true_dist))
    rho_auc_dist_residue, _ = spearmanr(random_residue_aucs, dist_residue)
    rho_auc_dist_patch, _ = spearmanr(random_patch_aucs, dist_patch)

    before_residue = best_of_n_and_null(random_residue_aucs, null_vals_r)
    before_patch = best_of_n_and_null(random_patch_aucs, null_vals_p)

    # ---------------- RESIDUALISE (item 3, the decisive test) ----------------
    # Rank-residualise AUC on distance (TASK-0310's own formula, reused
    # verbatim via `residualise()` above) to get a per-draw statistic with
    # the distance effect regressed out. That statistic lives on a rank-
    # residual scale, not the [0,1] AUC scale `excess_before_*` is reported
    # in -- reporting its own magnitude as an "AUC" would silently compare
    # two different units. Instead: use the residual only to SELECT which
    # draw is "best after controlling for distance" (argmax), then report
    # that draw's own RAW AUC -- the same unit as `excess_before_*`, so
    # before/after are directly comparable. Applied identically to every
    # null replicate (same distance ranks, since distance does not depend
    # on the permuted label) to build a null distribution in the same units.
    r_dist_res = rankdata(dist_residue)
    r_auc_res = rankdata(random_residue_aucs)
    resid_auc_res = residualise(r_auc_res, r_dist_res)
    best_idx_res = int(np.argmax(resid_auc_res))
    best_auc_after_res = float(random_residue_aucs[best_idx_res])
    null_auc_after_res = np.empty(n_perm)
    for k in range(n_perm):
        resid_k = residualise(rankdata(null_vals_r[k]), r_dist_res)
        null_auc_after_res[k] = null_vals_r[k, int(np.argmax(resid_k))]
    after_residue = (best_auc_after_res, float(null_auc_after_res.mean()),
                      best_auc_after_res - float(null_auc_after_res.mean()),
                      float(np.mean(null_auc_after_res >= best_auc_after_res)))

    r_dist_patch = rankdata(dist_patch)
    r_auc_patch = rankdata(random_patch_aucs)
    resid_auc_patch = residualise(r_auc_patch, r_dist_patch)
    best_idx_patch = int(np.argmax(resid_auc_patch))
    best_auc_after_patch = float(random_patch_aucs[best_idx_patch])
    null_auc_after_patch = np.empty(n_perm)
    for k in range(n_perm):
        resid_k = residualise(rankdata(null_vals_p[k]), r_dist_patch)
        null_auc_after_patch[k] = null_vals_p[k, int(np.argmax(resid_k))]
    after_patch = (best_auc_after_patch, float(null_auc_after_patch.mean()),
                   best_auc_after_patch - float(null_auc_after_patch.mean()),
                   float(np.mean(null_auc_after_patch >= best_auc_after_patch)))

    # ---------------- ITEM 4 -- candidate hub/burial/conservation features ----------------
    deg = degree_centrality(apo.coords, cutoff=cutoff)
    bet = betweenness_centrality(apo.coords, cutoff=cutoff)
    clo = closeness_centrality(apo.coords, cutoff=cutoff)
    hinge = hinge_score(apo.coords, cutoff=cutoff)
    burial = burial_score(apo)
    try:
        cons_arr, cons_info = t0274.conservation_array(apo.pdb_id, apo.chain_ids[0], apo.chain_ids, apo.resnums)
        cons_available = bool(np.isfinite(cons_arr).sum() >= max(10, 0.5 * N))
    except Exception as e:
        cons_arr = np.full(N, np.nan)
        cons_info = {"reason": f"{type(e).__name__}: {e}"}
        cons_available = False

    features = {"degree": deg, "betweenness": bet, "closeness": clo,
                "hinge_score": hinge, "burial": burial}
    if cons_available:
        features["conservation"] = cons_arr

    feature_corr = {}
    for fname, fvals in features.items():
        mask = np.isfinite(fvals)
        if mask.sum() < N:
            fvals = np.where(mask, fvals, np.nanmedian(fvals[mask]) if mask.any() else 0.0)
        mean_feat_residue = fvals[seeds_residue].mean(axis=1)
        mean_feat_patch = fvals[seeds_patch].mean(axis=1)
        rho_raw_res, p_raw_res = spearmanr(mean_feat_residue, random_residue_aucs)
        rho_resid_res, p_resid_res = spearmanr(mean_feat_residue, resid_auc_res)
        rho_raw_patch, p_raw_patch = spearmanr(mean_feat_patch, random_patch_aucs)
        rho_resid_patch, p_resid_patch = spearmanr(mean_feat_patch, resid_auc_patch)
        feature_corr[fname] = dict(
            residue_vs_raw_auc=[float(rho_raw_res), float(p_raw_res)],
            residue_vs_distance_residualised_auc=[float(rho_resid_res), float(p_resid_res)],
            patch_vs_raw_auc=[float(rho_raw_patch), float(p_raw_patch)],
            patch_vs_distance_residualised_auc=[float(rho_resid_patch), float(p_resid_patch)],
        )

    top_k = max(1, n_random // 20)  # top 5%
    top_res_idx = np.argsort(random_residue_aucs)[-top_k:]
    top_res_members = np.unique(seeds_residue[top_res_idx])
    top_summary = {}
    for fname, fvals in features.items():
        mask = np.isfinite(fvals)
        if mask.sum() < N:
            fvals = np.where(mask, fvals, np.nanmedian(fvals[mask]) if mask.any() else 0.0)
        pct_rank = rankdata(fvals) / N
        top_summary[fname] = dict(
            mean_percentile_in_top5pct_seeds=float(pct_rank[top_res_members].mean()),
            n_members=int(len(top_res_members)),
        )

    _log(f"  Arm A recovered/validated. dist rho(res)={rho_auc_dist_residue:.3f} "
         f"rho(patch)={rho_auc_dist_patch:.3f}. Excess before/after "
         f"res={before_residue[2]:.3f}/{after_residue[2]:.3f} "
         f"patch={before_patch[2]:.3f}/{after_patch[2]:.3f}")

    return dict(
        target=target_name, N=N, n_seed=n_seed, true_auc=true_auc, true_dist_to_pocket_centroid=true_dist,
        pct_true_dist_closer_than_random_residue=pct_true_dist_vs_residue,
        pct_true_dist_closer_than_random_patch=pct_true_dist_vs_patch,
        rho_auc_vs_distance_residue=float(rho_auc_dist_residue),
        rho_auc_vs_distance_patch=float(rho_auc_dist_patch),
        excess_before_residue=dict(best=before_residue[0], null_mean=before_residue[1], excess=before_residue[2], p=before_residue[3]),
        excess_after_residue=dict(best=after_residue[0], null_mean=after_residue[1], excess=after_residue[2], p=after_residue[3]),
        excess_before_patch=dict(best=before_patch[0], null_mean=before_patch[1], excess=before_patch[2], p=before_patch[3]),
        excess_after_patch=dict(best=after_patch[0], null_mean=after_patch[1], excess=after_patch[2], p=after_patch[3]),
        feature_correlations=feature_corr,
        top5pct_seed_feature_summary=top_summary,
        conservation_info=cons_info,
    )


def main() -> int:
    pilot = "--pilot" in sys.argv
    n_random = 100 if pilot else N_RANDOM
    n_perm = 20 if pilot else N_PERM
    _log(f"{'PILOT' if pilot else 'FULL'} run: n_random={n_random} n_perm={n_perm}")

    committed = json.load(open(t0379.RESULTS / "result.json"))

    out = {}
    t0 = time.time()
    for target in TARGETS:
        try:
            out[target] = recover_target(target, n_random, n_perm, t0379.det_seed(target), committed, validate=not pilot)
        except Exception as e:
            import traceback
            out[target] = dict(error=f"{type(e).__name__}: {e}", traceback=traceback.format_exc())
            _log(f"{target}: FAILED -- {e}")
        _log(f"  ({time.time()-t0:.0f}s elapsed)")

    out_path = RESULTS / ("pilot_result.json" if pilot else "result.json")
    out_path.write_text(json.dumps(out, indent=1, default=str))
    _log(f"Wrote {out_path} ({time.time()-t0:.0f}s total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
