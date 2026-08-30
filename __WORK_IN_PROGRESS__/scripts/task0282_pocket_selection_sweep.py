"""TASK-0282 -- pocket-level top-5: sweep distance x druggability against a
pre-registered prior, and compare it to CTQW on the identical apparatus.

The Sec.5 deliverable asks for the top 5 predicted allosteric SITES.
[[TASK-0242]]/[[TASK-0249]] already built the two-stage apparatus (fpocket
candidate pockets on apo + MIN_HOP distality filter); this task sweeps the
SELECTION RULE within that apparatus (distance metric x exclusion cutoff x
combination-with-druggability) and asks whether any point in that grid beats
this register's own residue-level ranking under honest leave-one-target-out
model selection -- not just in-sample.

PRE-REGISTERED PRIOR (task file's own text, before any number below was
seen): on KRAS_G12C and CARDIAC_MYOSIN the correct pocket has fpocket
druggability ~0.001 -- no monotone function of druggability and distance can
select it, because the ranking signal is not there. Prediction: the sweep
works on BCR_ABL1 and fails on the other two mandatory targets, and any rule
that appears to succeed on all three is overfitting.

Reuses, does not re-derive:
  - `task0242_two_stage_dryrun.CAND`/`prep`/`fpocket_candidates` -- apo
    candidate-pocket construction and seed/pocket resolution, unchanged.
  - `task0255_hop_angstrom_calibration.min_heavy_atom_dist_to_seed` -- the
    (chain,resnum)-keyed heavy-atom distance fix (bare-resnum collapse bug,
    already found and fixed there), reused verbatim, not re-derived.
  - `allostery.baselines.euclid_from_seed_centroid`/`hop_from_seed`,
    `allostery.hamiltonians.build_H_new`,
    `allostery.propagators.time_averaged_ctqw_converged`,
    `allostery.metrics.precision_at_k` -- this register's own primitives.
  - `task0261_cluster_robust_stats.CM`/`cluster_sign_flip_test` -- the
    13-cluster structure over the frozen 20 (7 shared-apo pairs + 6
    singletons) and its exact cluster-level sign-flip test, unchanged.
  - `config/candidate_targets_task0243.yaml` -- [[TASK-0243]]'s frozen set,
    with the 2 HIV_INTEGRASE_MUT871/916 rows dropped
    ([[TASK-0253]]'s domain-identity curation-error finding: 1M9D is
    Cyclophilin A + HIV-1 Capsid, not Integrase) -- leaving the 20 rows
    `task0261`'s own `CM` maps.

Import-order discipline (a real, previously-fixed bug in this task family,
[[TASK-0273]]/[[TASK-0276]]): the altloc="all" `prody.parsePDB` patch MUST
be applied before `allostery` is ever imported, so `allostery/__init__.py`'s
own folder-defaulting patch wraps THIS module's patch (composing both
kwargs.setdefault layers) rather than being silently overwritten by it.
Mirrors `task0249`/`task0255`'s own established, correct pattern exactly --
never `prody.parsePDB = <name imported from an allostery-touched module>`.
"""
from __future__ import annotations

import json
import sys
import tempfile
import warnings
from itertools import product
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

_orig_parsePDB = prody.parsePDB


def _parsePDB_all_altloc(*a, **kw):
    kw.setdefault("altloc", "all")
    return _orig_parsePDB(*a, **kw)


prody.parsePDB = _parsePDB_all_altloc

import task0242_two_stage_dryrun as t0242  # noqa: E402
import task0255_hop_angstrom_calibration as t0255  # noqa: E402
from allostery.baselines import euclid_from_seed_centroid, hop_from_seed  # noqa: E402
from allostery.hamiltonians import build_H_new  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from allostery.metrics import precision_at_k  # noqa: E402
from task0261_cluster_robust_stats import CM, cluster_sign_flip_test  # noqa: E402
from task0258_allosteric_distance_taxonomy import measure as t0258_measure  # noqa: E402

OUT = _ROOT / "results/tasks/0282_pocket_level_top5_distance_druggability_sweep"
FROZEN_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"
MANDATORY = ["BCR_ABL1", "KRAS_G12C", "CARDIAC_MYOSIN"]
DROPPED = ["HIV_INTEGRASE_MUT871", "HIV_INTEGRASE_MUT916"]  # TASK-0253 finding
CTQW_WRAPPER_MIN_HOP = 2.0  # TASK-0242's own spec, fixed, not swept

# ---------------------------------------------------------------------------
# Sweep grid. The first 4 combos were pre-registered before any candidate
# was scored. `lex_near_first` was ADDED after the Reviewer's own probe
# (`task0282_prior_lexicographic_probe.py`, filed while this task was
# already IN_PROGRESS) found, in-sample on the 3 mandatory targets, that
# sorting by NEAREST surviving distance stratum first (druggability only as
# a tiebreak within that stratum) recovers KRAS_G12C's true pocket exactly
# at its own oracle ceiling -- the opposite ordering from this script's own
# original `lex_far_first`. The probe's own explicit warning: its 0.267
# in-sample mean is "exactly the overfitting this task's Scope forbids" and
# recommends sweeping BOTH orderings under LOTO, not adopting either from
# the 3-target spot-check. Added as a rule FAMILY here, not as a chosen
# winner -- LOTO model selection below still decides per fold, on N-1
# targets never including the one being scored, so this addition does not
# reintroduce the overfitting the probe itself flagged.
# ---------------------------------------------------------------------------
METRICS = {
    "hop": dict(field="min_hop", cutoffs=[1.0, 2.0, 3.0], unit="hops"),
    "min_euclid": dict(field="min_euclid", cutoffs=[6.0, 8.0, 10.0, 12.0], unit="A"),
    "centroid_euclid": dict(field="centroid_euclid", cutoffs=[10.0, 15.0, 20.0], unit="A"),
}
COMBOS = ["drug_alone", "weighted_sum", "rank_product", "lex_far_first"]
LEX_FAR_MULTIPLIER = 1.5  # "categorise then rank": far bin = metric >= 1.5x cutoff
# lex_near_first's own bin widths, one small pre-registered grid per metric
# (subset of the probe's own tested {1,2,3,5} A for the Euclidean metrics;
# hop is already integer-valued so 1-hop bins are the natural granularity).
LEX_NEAR_BINS = {"hop": [1.0], "min_euclid": [1.0, 2.0, 3.0], "centroid_euclid": [2.0, 5.0]}


def _rule_ids():
    """Deterministic, pre-registered enumeration order (metric, cutoff,
    combo[, bin_width]) -- ties in LOTO model selection break to the FIRST
    rule in this order, never by chance."""
    for metric, spec in METRICS.items():
        for cutoff in spec["cutoffs"]:
            for combo in COMBOS:
                yield (metric, cutoff, combo, None)
            for bin_w in LEX_NEAR_BINS[metric]:
                yield (metric, cutoff, "lex_near_first", bin_w)


RULES = list(_rule_ids())


# ---------------------------------------------------------------------------
# Per-target candidate construction (mirrors task0242/task0255's own
# candidate loop against the same primitives, extended with the 2 new
# distance metrics and the analytic expected-hits score this task's own
# Scope calls for -- not imported whole, per task0255's own precedent, since
# neither upstream function returns everything this task needs).
# ---------------------------------------------------------------------------

def build_target(t: str):
    cfg2, apo, seed, pocket = t0242.prep(t)
    if len(seed) == 0:
        return {"error": "empty active-site seed"}
    coords = apo.coords
    cut = float(cfg2.get("enm_cutoff", 8.0))
    resn = np.asarray(apo.resnums)
    chids = np.asarray(apo.chain_ids)
    # TASK-0298: (chain, resnum) compound key, matching fpocket_candidates'
    # own now-corrected `p["resnums"]` shape -- a resnum-only dict silently
    # kept only the last chain's index per colliding resnum.
    idx_of = {(str(c), int(r)): i for i, (c, r) in enumerate(zip(chids, resn))}
    apo_ch = cfg2.get("apo_chains") or cfg2.get("chains")
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

    hop_full = -hop_from_seed(coords, seed, cutoff=cut)          # true BFS hops
    min_euclid_full = t0255.min_heavy_atom_dist_to_seed(cfg2, apo, seed)
    centroid_full = -euclid_from_seed_centroid(coords, seed)      # true positive distance
    H = build_H_new(coords, apo.bfactors, cutoff=cut)
    ctqw_full = time_averaged_ctqw_converged(H, source=seed, coherent=False)

    cands = []
    for p in pockets:
        ii = [idx_of[r] for r in p["resnums"] if r in idx_of]
        if not ii:
            continue
        ii = np.asarray(ii, dtype=int)
        n_res = int(len(ii))
        overlap_count = int(pocket[ii].sum())
        cands.append({
            "id": p["id"], "n_res": n_res, "res_idx": ii.tolist(),
            "min_hop": float(np.min(hop_full[ii])),
            "min_euclid": float(np.nanmin(min_euclid_full[ii])),
            "centroid_euclid": float(np.mean(centroid_full[ii])),
            "fpocket_drug": float(p.get("druggability_score") or 0.0),
            "ctqw": float(np.mean(ctqw_full[ii])),
            "overlap_count": overlap_count,
            "EH": overlap_count / n_res,
        })
    if not cands:
        return {"error": "fpocket found no residue-resolvable candidates"}
    return {
        "cands": cands, "ctqw_full": ctqw_full, "pocket": pocket, "resn": resn,
        "n_active_site": int(len(seed)), "n_pocket": int(pocket.sum()),
    }


# ---------------------------------------------------------------------------
# Fixed (non-swept) reference arms
# ---------------------------------------------------------------------------

def oracle_and_random(cands: list, n_pocket: int) -> dict:
    """Oracle ceiling = expected hits of the candidate that BEST IDENTIFIES
    the true pocket (max recall = overlap_count/n_pocket), not the
    precision-maximizing candidate over all fpocket cavities -- a small,
    high-precision fragment of the true site is not "finding the site."
    Matches the Reviewer's own pre-registered spot-check numbers exactly
    on all 3 mandatory targets (0.8/0.737/0.279 vs the filed 0.8/0.7/0.3),
    confirmed directly before adopting this definition, not assumed from
    the column header alone.
    Random = mean EH over ALL raw candidates, equal probability per
    pocket -- the bracketing floor."""
    ehs = [c["EH"] for c in cands]
    best_recall = max(cands, key=lambda c: c["overlap_count"] / max(1, n_pocket))
    return {"oracle": float(best_recall["EH"]), "random": float(np.mean(ehs)),
            "n_candidates": len(cands)}


def ctqw_wrapper(cands: list) -> dict:
    survivors = [c for c in cands if c["min_hop"] >= CTQW_WRAPPER_MIN_HOP]
    if not survivors:
        return {"EH": 0.0, "flag": "all_filtered", "n_survivors": 0}
    top = max(survivors, key=lambda c: c["ctqw"])
    return {"EH": float(top["EH"]), "flag": None, "n_survivors": len(survivors)}


def residue_ranking(data: dict) -> float:
    return float(precision_at_k(data["ctqw_full"], data["pocket"], k=5))


# ---------------------------------------------------------------------------
# Swept rule: apply one (metric, cutoff, combo) to one target's candidates
# ---------------------------------------------------------------------------

def apply_rule(cands: list, rule: tuple) -> dict:
    metric, cutoff, combo, bin_w = rule
    field = METRICS[metric]["field"]
    survivors = [c for c in cands if c[field] >= cutoff]
    if not survivors:
        return {"EH": 0.0, "flag": "no_survivors", "n_survivors": 0}

    if combo == "drug_alone":
        top = max(survivors, key=lambda c: c["fpocket_drug"])
    elif combo == "weighted_sum":
        drug = np.array([c["fpocket_drug"] for c in survivors], float)
        dist = np.array([c[field] for c in survivors], float)
        zd = (drug - drug.mean()) / (drug.std() or 1.0)
        zx = (dist - dist.mean()) / (dist.std() or 1.0)
        score = 0.5 * zd + 0.5 * zx
        top = survivors[int(np.argmax(score))]
    elif combo == "rank_product":
        drug = np.array([c["fpocket_drug"] for c in survivors], float)
        dist = np.array([c[field] for c in survivors], float)
        rank_drug = (-drug).argsort().argsort() + 1     # 1 = highest druggability
        rank_dist = (-dist).argsort().argsort() + 1      # 1 = most distal
        prod = rank_drug * rank_dist
        best = int(np.lexsort((-drug, prod))[0])          # min product, tie -> higher drug
        top = survivors[best]
    elif combo == "lex_far_first":
        # Bartosz's original "categorise then rank": most-distal stratum
        # first, druggability as tiebreak.
        far_cut = cutoff * LEX_FAR_MULTIPLIER
        far = [c for c in survivors if c[field] >= far_cut]
        near = [c for c in survivors if c[field] < far_cut]
        pool = far if far else near
        top = max(pool, key=lambda c: c["fpocket_drug"])
    elif combo == "lex_near_first":
        # Reviewer probe's own ordering: NEAREST surviving distance stratum
        # first (distance = signal strength), druggability only a tiebreak
        # within that stratum -- `task0282_prior_lexicographic_probe.py`'s
        # `run()`, same (round(dist/bin), -drug) sort key, reused verbatim.
        top = min(survivors, key=lambda c: (round(c[field] / bin_w), -c["fpocket_drug"]))
    else:
        raise ValueError(combo)
    return {"EH": float(top["EH"]), "flag": None, "n_survivors": len(survivors)}


def rule_repr(rule: tuple) -> str:
    metric, cutoff, combo, bin_w = rule
    unit = METRICS[metric]["unit"]
    tail = f" (bin={bin_w:g}{unit})" if bin_w is not None else ""
    return f"{metric}>={cutoff:g}{unit} + {combo}{tail}"


# ---------------------------------------------------------------------------
# LOTO model selection over the frozen 20
# ---------------------------------------------------------------------------

def loto_sweep(target_cands: dict) -> dict:
    """target_cands: {target: [cands]}, only targets with a resolvable
    candidate list (errored targets are handled by the caller so the
    denominator stays honest). Returns per-target LOTO EH under the rule
    selected on every OTHER target, plus the rule chosen for each fold."""
    names = list(target_cands.keys())
    per_target_eh = {}
    per_target_rule = {}
    for held_out in names:
        train = [t for t in names if t != held_out]
        best_rule, best_mean = None, -np.inf
        for rule in RULES:
            vals = [apply_rule(target_cands[t], rule)["EH"] for t in train]
            m = float(np.mean(vals))
            if m > best_mean:
                best_mean, best_rule = m, rule
        r = apply_rule(target_cands[held_out], best_rule)
        per_target_eh[held_out] = r["EH"]
        per_target_rule[held_out] = rule_repr(best_rule)
    return {"per_target_eh": per_target_eh, "per_target_rule": per_target_rule}


def fit_final_rule(target_cands: dict) -> tuple:
    """Fit on ALL of target_cands (the full frozen 20) -- used only to score
    the mandatory 3, which were never in target_cands at all, so this is
    still a genuine out-of-sample application, not a re-fit on the test
    set."""
    names = list(target_cands.keys())
    best_rule, best_mean = None, -np.inf
    for rule in RULES:
        vals = [apply_rule(target_cands[t], rule)["EH"] for t in names]
        m = float(np.mean(vals))
        if m > best_mean:
            best_mean, best_rule = m, rule
    return best_rule, best_mean


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    new_cand = yaml.safe_load(FROZEN_CONFIG.read_text())["targets"]
    for d in DROPPED:
        new_cand.pop(d, None)
    t0242.CAND = new_cand
    frozen_targets = [t for t in new_cand.keys() if t in CM]
    assert len(frozen_targets) == 20, f"expected 20 frozen targets, got {len(frozen_targets)}"

    print(f"=== Building candidates: {len(frozen_targets)} frozen-set + {len(MANDATORY)} mandatory ===")
    data = {}
    errors = {}
    for t in frozen_targets + MANDATORY:
        try:
            d = build_target(t)
        except Exception as e:  # noqa: BLE001
            d = {"error": f"{type(e).__name__}: {e}"}
        if "error" in d:
            errors[t] = d["error"]
            print(f"  {t:<22} SKIP: {d['error'][:70]}")
            continue
        data[t] = d
        print(f"  {t:<22} n_res={len(d['resn']):5d} n_pocket={d['n_pocket']:3d} "
              f"n_candidates={len(d['cands']):3d}")

    frozen_ok = [t for t in frozen_targets if t in data]
    mand_ok = [t for t in MANDATORY if t in data]
    n_frozen_attempted = len(frozen_targets)
    n_mand_attempted = len(MANDATORY)
    print(f"\nfrozen: {len(frozen_ok)}/{n_frozen_attempted} scoreable; "
          f"mandatory: {len(mand_ok)}/{n_mand_attempted} scoreable")

    target_cands = {t: data[t]["cands"] for t in frozen_ok}

    # --- site-category covariate (TASK-0258's own taxonomy, reused verbatim,
    # not re-derived) -- the probe's own recommendation: report each
    # target's true-pocket category so the ordering-vs-geometry
    # relationship it found on 3 targets can be checked at n=20/23. -------
    print("\n=== Site category (TASK-0258's taxonomy) ===")
    category = {}
    for t in frozen_ok + mand_ok:
        try:
            m = t0258_measure(t)
            category[t] = m.get("category", "error")
            print(f"  {t:<22} {category[t]:<24} min_A={m.get('min_A', float('nan')):.2f}")
        except Exception as e:  # noqa: BLE001
            category[t] = f"error: {type(e).__name__}: {e}"
            print(f"  {t:<22} SKIP: {category[t][:60]}")

    # --- fixed arms, both groups -----------------------------------------
    fixed = {}
    for t in frozen_ok + mand_ok:
        d = data[t]
        orc = oracle_and_random(d["cands"], d["n_pocket"])
        cw = ctqw_wrapper(d["cands"])
        rr = residue_ranking(d)
        fixed[t] = {"oracle": orc["oracle"], "random": orc["random"],
                     "n_candidates": orc["n_candidates"],
                     "ctqw_wrapper": cw["EH"], "ctqw_wrapper_flag": cw["flag"],
                     "residue_ranking": rr}

    # --- swept rule: LOTO over the frozen 20 ------------------------------
    print(f"\n=== LOTO sweep over the frozen 20 ({len(RULES)} rules, {len(COMBOS)} pre-registered "
          f"+ lex_near_first added post-probe) ===")
    loto = loto_sweep(target_cands)
    for t in frozen_ok:
        print(f"  {t:<22} EH={loto['per_target_eh'][t]:.3f}  rule={loto['per_target_rule'][t]}")

    final_rule, final_mean = fit_final_rule(target_cands)
    print(f"\nFinal rule (fit on all 20, applied to mandatory 3 as genuine holdout): "
          f"{rule_repr(final_rule)}  (mean EH on frozen 20 = {final_mean:.3f})")
    mand_swept = {t: apply_rule(data[t]["cands"], final_rule) for t in mand_ok}
    for t in mand_ok:
        print(f"  {t:<22} EH={mand_swept[t]['EH']:.3f}  flag={mand_swept[t]['flag']}")

    # --- headline table -----------------------------------------------------
    print("\n=== Headline table ===")
    header = f"{'target':<22}{'group':<10}{'residue':>9}{'swept':>9}{'ctqw_wrap':>11}{'random':>9}{'oracle':>9}"
    print(header)
    rows = []
    for t in mand_ok:
        f = fixed[t]
        swept = mand_swept[t]["EH"]
        rows.append(dict(target=t, group="mandatory", residue_ranking=f["residue_ranking"],
                          swept_rule=swept, ctqw_wrapper=f["ctqw_wrapper"],
                          random=f["random"], oracle=f["oracle"], n_candidates=f["n_candidates"],
                          category=category.get(t)))
        print(f"{t:<22}{'mandatory':<10}{f['residue_ranking']:>9.3f}{swept:>9.3f}"
              f"{f['ctqw_wrapper']:>11.3f}{f['random']:>9.3f}{f['oracle']:>9.3f}")
    for t in frozen_ok:
        f = fixed[t]
        swept = loto["per_target_eh"][t]
        rows.append(dict(target=t, group="frozen20", residue_ranking=f["residue_ranking"],
                          swept_rule=swept, ctqw_wrapper=f["ctqw_wrapper"],
                          random=f["random"], oracle=f["oracle"], n_candidates=f["n_candidates"],
                          loto_rule=loto["per_target_rule"][t], category=category.get(t)))
        print(f"{t:<22}{'frozen20':<10}{f['residue_ranking']:>9.3f}{swept:>9.3f}"
              f"{f['ctqw_wrapper']:>11.3f}{f['random']:>9.3f}{f['oracle']:>9.3f}")

    def _mean(group, key):
        vals = [r[key] for r in rows if r["group"] == group]
        return float(np.mean(vals)) if vals else float("nan")

    print("\n--- means ---")
    for g in ("mandatory", "frozen20"):
        print(f"  {g:<10} residue={_mean(g,'residue_ranking'):.3f}  swept={_mean(g,'swept_rule'):.3f}  "
              f"ctqw_wrap={_mean(g,'ctqw_wrapper'):.3f}  random={_mean(g,'random'):.3f}  "
              f"oracle={_mean(g,'oracle'):.3f}")

    # --- cluster-robust significance on the frozen 20 ----------------------
    print("\n=== Cluster-robust (13 clusters, exact sign-flip) on the frozen 20 ===")
    diffs_vs_residue = {t: loto["per_target_eh"][t] - fixed[t]["residue_ranking"] for t in frozen_ok}
    diffs_vs_ctqw = {t: loto["per_target_eh"][t] - fixed[t]["ctqw_wrapper"] for t in frozen_ok}
    diffs_vs_random = {t: loto["per_target_eh"][t] - fixed[t]["random"] for t in frozen_ok}
    test_vs_residue = cluster_sign_flip_test(diffs_vs_residue)
    test_vs_ctqw = cluster_sign_flip_test(diffs_vs_ctqw)
    test_vs_random = cluster_sign_flip_test(diffs_vs_random)
    print(f"  swept - residue_ranking : median_diff={test_vs_residue['median']:.3f}  "
          f"p={test_vs_residue['p_value']:.4f}  (n_clusters={test_vs_residue['n_clusters']})")
    print(f"  swept - ctqw_wrapper    : median_diff={test_vs_ctqw['median']:.3f}  "
          f"p={test_vs_ctqw['p_value']:.4f}")
    print(f"  swept - random          : median_diff={test_vs_random['median']:.3f}  "
          f"p={test_vs_random['p_value']:.4f}")

    # --- category-stratified breakdown (probe's own recommendation: test
    # the ordering-vs-geometry relationship at n=20/23, not infer it from 3
    # targets) --------------------------------------------------------------
    print("\n=== Swept EH and LOTO rule family, by TASK-0258 site category ===")
    from collections import Counter
    cats = sorted(set(r["category"] for r in rows if r["category"]))
    for cat in cats:
        sub = [r for r in rows if r["category"] == cat]
        eh_vals = [r["swept_rule"] for r in sub]
        fams = Counter(
            r.get("loto_rule", rule_repr(final_rule)).split(" + ")[1].split(" (")[0] for r in sub
        )
        print(f"  {cat:<24} n={len(sub):2d}  mean_swept_EH={np.mean(eh_vals):.3f}  "
              f"rule_families={dict(fams)}  targets={[r['target'] for r in sub]}")

    # --- pre-registered prior verdict --------------------------------------
    print("\n=== Pre-registered prior verdict ===")
    prior_rows = {t: (fixed[t]["residue_ranking"], mand_swept.get(t, {}).get("EH")) for t in mand_ok}
    for t in mand_ok:
        print(f"  {t:<22} swept_EH={mand_swept[t]['EH']:.3f}  oracle={fixed[t]['oracle']:.3f}")
    bcr = mand_swept.get("BCR_ABL1", {}).get("EH")
    kras = mand_swept.get("KRAS_G12C", {}).get("EH")
    card = mand_swept.get("CARDIAC_MYOSIN", {}).get("EH")
    prior_holds = None
    if all(v is not None for v in (bcr, kras, card)):
        prior_holds = bool(bcr >= 0.4 and kras < 0.4 and card < 0.4)
        print(f"  prior (\"works on BCR-ABL1, fails on the other two\"): "
              f"{'HOLDS' if prior_holds else 'DOES NOT HOLD'} "
              f"(BCR_ABL1={bcr:.3f}, KRAS_G12C={kras:.3f}, CARDIAC_MYOSIN={card:.3f})")

    out = {
        "final_rule": rule_repr(final_rule), "final_rule_mean_eh_frozen20": final_mean,
        "ctqw_wrapper_min_hop": CTQW_WRAPPER_MIN_HOP,
        "rules_swept": [rule_repr(r) for r in RULES],
        "fixed_arms": fixed, "loto": loto, "mandatory_swept": mand_swept,
        "rows": rows, "errors": errors, "category": category,
        "n_frozen_attempted": n_frozen_attempted, "n_mandatory_attempted": n_mand_attempted,
        "cluster_robust": {
            "swept_vs_residue_ranking": test_vs_residue,
            "swept_vs_ctqw_wrapper": test_vs_ctqw,
            "swept_vs_random": test_vs_random,
        },
        "pre_registered_prior_holds": prior_holds,
    }
    (OUT / "pocket_selection_sweep.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwritten: {OUT / 'pocket_selection_sweep.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
