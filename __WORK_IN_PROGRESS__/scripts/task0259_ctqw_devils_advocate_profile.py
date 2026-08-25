"""TASK-0259 -- Devil's advocate for CTQW, plus a profile of the
large-unexplained cases.

Two questions, one join.

(A) THE PRE-REGISTERED SUBGROUP TEST. The CTQW brief
    (`documentation/CTQW_CONTRIBUTION_BRIEF.html`, section 07 item 4) names
    this as the most promising unexamined analysis we know of, and commits us
    to updating if it fires:

        "If CTQW's marginal is positive specifically on the targets that pass
         B-factor validity and negative on those that fail, that is a real,
         mechanistically sensible result."

    [[TASK-0250]] measured ENM validity on the 15 *register* targets. The
    attribution ([[TASK-0254]]) is on [[TASK-0243]]'s frozen 22. The two sets
    barely overlap, so the subgroup test has never actually been runnable.
    This computes GNM-vs-B-factor validity for the frozen set itself, using
    the same `potentials._gnm_msf` and the same pre-registered bars
    (PASS >= 0.6, MARGINAL >= 0.4), and joins it to the attribution.

    This is played straight as devil's advocate: if a valid ENM is what CTQW
    was always missing, this is where it shows up. CTQW reaches +49% Shapley
    on at least one target and we do not currently know why.

(B) WHAT DO THE LARGE-UNEXPLAINED CASES HAVE IN COMMON? Same join, different
    dependent variable. Profile the unexplained share against every target
    property we have measured: ENM validity, apo crypticity ([[TASK-0254]]
    part B), pocket-to-active-site distance and site category ([[TASK-0258]]),
    protein size, pocket size, seed size.

Nothing here is fitted. Every quantity is measured elsewhere and joined; the
only new computation is the GNM B-factor correlation on the frozen set.

NOTE ON COORDINATES, since it is the obvious objection: every score in the
attribution is computed on the **apo** structure
(`task0242_two_stage_dryrun.prep` returns `apo`). Holo is used only to derive
the pocket label. Scoring on holo would leak the answer, so the ENM validity
computed here is likewise apo-side -- the model CTQW actually ran on.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
from scipy import stats

warnings.filterwarnings("ignore")

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import prody  # noqa: E402
prody.confProDy(verbosity="none")

from task0255_hop_angstrom_calibration import _parsePDB_all_altloc  # noqa: E402
prody.parsePDB = _parsePDB_all_altloc

import yaml  # noqa: E402
from task0242_two_stage_dryrun import prep, CAND  # noqa: E402
from allostery.potentials import _gnm_msf  # noqa: E402

# TASK-0243's frozen set is not in targets.yaml -- prep() resolves through
# CAND, so it must be loaded in or every lookup raises KeyError.
_FROZEN = _ROOT / "config" / "candidate_targets_task0243.yaml"
if _FROZEN.exists():
    CAND.update(yaml.safe_load(_FROZEN.read_text()).get("targets") or {})

PASS_BAR, MARGINAL_BAR = 0.6, 0.4          # TASK-0250's own pre-registered bars
OUT = _ROOT / "results/tasks/0259_ctqw_devils_advocate"

SHAPLEY = _ROOT / "results/tasks/0254_fpocket_variance_and_crypticity/part_a_shapley_attribution.json"
CRYPTIC = _ROOT / "results/tasks/0254_fpocket_variance_and_crypticity/part_b_crypticity.json"
TAXONOMY = _ROOT / "results/tasks/0258_allosteric_distance_taxonomy/pocket_taxonomy.json"


def added_last(subset_aucs: dict, block: str) -> float:
    """Block's marginal contribution when added last, as a share of
    above-chance discrimination -- the decision-relevant statistic."""
    full = subset_aucs["ctqw,fpocket,geometry"]
    without = {
        "ctqw": "fpocket,geometry",
        "fpocket": "ctqw,geometry",
        "geometry": "ctqw,fpocket",
    }[block]
    return (full - subset_aucs[without]) / 0.5


def gnm_validity(target: str) -> dict:
    """GNM predicted MSF vs real apo Ca B-factors, same quantity TASK-0250
    scored on the register targets."""
    cfg, apo, seed, pocket = prep(target)
    b = np.asarray(apo.bfactors, dtype=float)
    finite = np.isfinite(b)
    if finite.sum() < 20 or np.allclose(b[finite], b[finite][0]):
        return {"pearson_r": None, "verdict": "UNUSABLE",
                "reason": "B-factors absent or constant"}
    cutoff = float(cfg.get("enm_cutoff", 8.0))
    msf = np.asarray(_gnm_msf(apo.coords, cutoff), dtype=float)
    ok = finite & np.isfinite(msf)
    r = float(stats.pearsonr(msf[ok], b[ok]).statistic)
    verdict = "PASS" if r >= PASS_BAR else ("MARGINAL" if r >= MARGINAL_BAR else "FAIL")
    return {"pearson_r": r, "verdict": verdict, "n_scored": int(ok.sum()),
            "cutoff": cutoff, "reason": None}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    shap = json.loads(SHAPLEY.read_text())
    cryptic = json.loads(CRYPTIC.read_text()) if CRYPTIC.exists() else {}
    taxo_raw = json.loads(TAXONOMY.read_text()) if TAXONOMY.exists() else []
    taxo = {r["target"]: r for r in taxo_raw if "error" not in r}

    rows = []
    for t, rec in shap.items():
        try:
            val = gnm_validity(t)
        except Exception as exc:                      # noqa: BLE001
            val = {"pearson_r": None, "verdict": "ERROR", "reason": f"{type(exc).__name__}: {exc}"}
        c = cryptic.get(t) or {}
        x = taxo.get(t) or {}
        rows.append({
            "target": t,
            "gnm_r": val["pearson_r"], "enm_verdict": val["verdict"],
            "ctqw_shapley": rec["shapley"]["ctqw"],
            "ctqw_added_last": added_last(rec["subset_aucs"], "ctqw"),
            "geometry_shapley": rec["shapley"]["geometry"],
            "fpocket_shapley": rec["shapley"]["fpocket"],
            "unexplained": rec["unexplained"],
            "full_auc": rec["full_auc"],
            "ctqw_alone_auc": rec["subset_aucs"].get("ctqw"),
            "geom_alone_auc": rec["subset_aucs"].get("geometry"),
            "fpocket_alone_auc": rec["subset_aucs"].get("fpocket"),
            "apo_open_frac": c.get("fraction_open"),
            "already_open": c.get("already_open"),
            "min_A": x.get("min_A"), "category": x.get("category"),
            "n_pocket": x.get("n_pocket"), "n_seed": x.get("n_seed"),
        })

    scored = [r for r in rows if r["gnm_r"] is not None]

    # ---------------- (A) the pre-registered subgroup test ----------------
    print("=" * 78)
    print("(A)  PRE-REGISTERED SUBGROUP TEST -- does CTQW work where the ENM is valid?")
    print("=" * 78)
    from collections import Counter
    print(f"  ENM validity on the frozen set (n={len(scored)}): "
          f"{dict(Counter(r['enm_verdict'] for r in scored))}")

    valid = [r for r in scored if r["enm_verdict"] in ("PASS", "MARGINAL")]
    broken = [r for r in scored if r["enm_verdict"] == "FAIL"]
    print(f"\n  {'group':<28}{'n':>4}{'CTQW added-last':>18}{'CTQW Shapley':>15}")
    for lbl, grp in (("ENM valid (PASS/MARGINAL)", valid), ("ENM invalid (FAIL)", broken)):
        if not grp:
            print(f"  {lbl:<28}{0:>4}{'--':>18}{'--':>15}")
            continue
        al = [r["ctqw_added_last"] for r in grp]
        sh = [r["ctqw_shapley"] for r in grp]
        print(f"  {lbl:<28}{len(grp):>4}{100*np.median(al):>17.2f}%{100*np.median(sh):>14.1f}%")

    if valid and broken:
        u = stats.mannwhitneyu([r["ctqw_added_last"] for r in valid],
                               [r["ctqw_added_last"] for r in broken],
                               alternative="greater")
        print(f"\n  Mann-Whitney (valid > invalid, CTQW added-last): p={u.pvalue:.4f}")
    if len(scored) > 4:
        rp = stats.spearmanr([r["gnm_r"] for r in scored],
                             [r["ctqw_added_last"] for r in scored])
        print(f"  Spearman(ENM validity r, CTQW added-last): rho={rp.statistic:+.3f}  p={rp.pvalue:.4f}")
    if valid:
        al = [r["ctqw_added_last"] for r in valid]
        print(f"  CTQW added-last on ENM-valid targets alone: median {100*np.median(al):+.2f}%  "
              f"Wilcoxon vs 0 p={stats.wilcoxon(al).pvalue:.4f}  positive on {sum(1 for x in al if x>0)}/{len(al)}")

    # ---------------- where CTQW looks best ----------------
    print("\n  Targets where CTQW's Shapley share is highest:")
    print(f"    {'target':<24}{'ctqw_shap':>10}{'added_last':>11}{'geom_shap':>10}"
          f"{'ctqw_solo':>10}{'geom_solo':>10}{'ENM':>10}")
    for r in sorted(scored, key=lambda r: -r["ctqw_shapley"])[:5]:
        print(f"    {r['target']:<24}{100*r['ctqw_shapley']:>9.0f}%{100*r['ctqw_added_last']:>10.1f}%"
              f"{100*r['geometry_shapley']:>9.0f}%{r['ctqw_alone_auc']:>10.3f}"
              f"{r['geom_alone_auc']:>10.3f}{r['enm_verdict']:>10}")

    # ---------------- (B) profile of the unexplained ----------------
    print("\n" + "=" * 78)
    print("(B)  WHAT DO THE LARGE-UNEXPLAINED CASES HAVE IN COMMON?")
    print("=" * 78)
    ranked = sorted(rows, key=lambda r: -r["unexplained"])
    print(f"  {'target':<24}{'unexpl':>8}{'full_auc':>10}{'ENM':>10}{'apo_open':>10}"
          f"{'min_A':>8}  {'category':<20}")
    for r in ranked:
        ao = f"{100*r['apo_open_frac']:.0f}%" if r["apo_open_frac"] is not None else "--"
        mA = f"{r['min_A']:.1f}" if r["min_A"] is not None else "--"
        print(f"  {r['target']:<24}{100*r['unexplained']:>7.0f}%{r['full_auc']:>10.3f}"
              f"{r['enm_verdict']:>10}{ao:>10}{mA:>8}  {(r['category'] or '--'):<20}")

    def corr(field, label):
        pairs = [(r[field], r["unexplained"]) for r in rows
                 if r.get(field) is not None and np.isfinite(r[field])]
        if len(pairs) < 5:
            return
        a, b = zip(*pairs)
        s = stats.spearmanr(a, b)
        flag = "  <-- notable" if s.pvalue < 0.05 else ""
        print(f"    {label:<38} rho={s.statistic:+.3f}  p={s.pvalue:.4f}  n={len(pairs)}{flag}")

    print("\n  Spearman correlation with the UNEXPLAINED share:")
    for f, lbl in (("gnm_r", "ENM validity (GNM-B-factor r)"),
                   ("apo_open_frac", "apo crypticity (fraction open)"),
                   ("min_A", "pocket-to-active-site min distance"),
                   ("n_pocket", "pocket size (residues)"),
                   ("n_seed", "active-site size (residues)"),
                   ):
        # deliberately NOT correlated against full_auc: unexplained is defined
        # as (1 - full_auc)/0.5, so rho = -1.000 by construction, not a finding.
        corr(f, lbl)

    top = ranked[:5]
    print(f"\n  The {len(top)} largest-unexplained targets share:")
    print(f"    ENM verdicts : {dict(Counter(r['enm_verdict'] for r in top))}")
    print(f"    categories   : {dict(Counter(r['category'] or '--' for r in top))}")
    aos = [r["apo_open_frac"] for r in top if r["apo_open_frac"] is not None]
    if aos:
        rest = [r["apo_open_frac"] for r in ranked[5:] if r["apo_open_frac"] is not None]
        print(f"    apo-open     : median {100*np.median(aos):.0f}%"
              + (f"  vs {100*np.median(rest):.0f}% for the rest" if rest else ""))

    (OUT / "profile.json").write_text(json.dumps(rows, indent=1))
    print(f"\n  written: {OUT / 'profile.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
