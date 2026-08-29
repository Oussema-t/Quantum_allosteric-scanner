"""TASK-0293 -- does `druggability / size` survive held-out evaluation, or
is it a second instance of the exact overfitting pattern [[TASK-0282]]'s
own `lex_near_first` probe already produced once in this register?

[[TASK-0292]] Part D found `druggability / size` gains +0.100 mean EH over
the published `druggability` rule (0.1649 -> 0.2649) **in-sample on the
frozen 20**, not significant (Wilcoxon p=0.157) -- and flagged, explicitly,
that this register already has one case of an in-sample sweep reporting a
similar-looking number (0.267) whose winning family then never won a
single LOTO fold ([[TASK-0282]]'s own reviewer probe). This task is that
check for `druggability / size` specifically.

ONE PRE-SPECIFIED ARM (this task's own Constraint) -- not a sweep. Both
arms compared here are FULLY SPECIFIED with zero free parameters (the
published rule: MIN_HOP>=1, rank by druggability; the new arm: MIN_HOP>=1,
rank by druggability/size) -- neither is fit to any target's own label, so
there is no held-in / held-out split to construct: every target's own EH
under a parameter-free rule already is the "held-out" number. "LOTO" in
this task's own title is therefore reported as per-target scoring across
all 20 frozen targets (never any label used to choose the rule), not as a
fold-wise model-selection loop -- stated explicitly so this isn't misread
as validating a fitting procedure that doesn't exist here.

DEPENDENCY on [[TASK-0290]] (read before running): the EH metric is not
independent of active-site detection (`pocket = drug_contacts &
~active_site & ~terminal`). TASK-0290's recompute diff is posted (0/33
taxonomy targets moved, including this task's own two dependency targets
DHPS_GC7/NAMPT_NPA1R) -- so this run needs no PROVISIONAL label and no
re-run: the active-site detection this script's own `prep()` call already
uses (via TASK-0290's now-deterministic, cached `detect_active_site`) is
the corrected one.

Reuses, does not re-derive:
  - `task0282_pocket_selection_sweep.build_target` -- candidate
    construction (fpocket on apo, MIN_HOP, EH), unchanged.
  - `task0282_pocket_selection_sweep.apply_rule` -- the published rule
    (`('hop', 1.0, 'drug_alone', None)`), the exact winning LOTO-selected
    configuration from that task, reused verbatim as the comparison arm.
  - `task0261_cluster_robust_stats.CM`/`cluster_sign_flip_test` -- the
    13-cluster structure over the frozen 20 and its exact sign-flip test.
  - `task0292_fpocket_fragmentation_and_the_ceiling`'s own
    `druggability / size` formula (`d / max(n, 1)`), same MIN_HOP>=1
    filter, reused verbatim as the single pre-specified new arm.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import yaml  # noqa: E402
import task0282_pocket_selection_sweep as m  # noqa: E402 -- also composes the prody.parsePDB patch chain
from scipy.stats import wilcoxon  # noqa: E402
from task0261_cluster_robust_stats import CM, cluster_sign_flip_test  # noqa: E402

OUT = _ROOT / "results/tasks/0293_loto_druggability_per_size"
MIN_HOP = 1.0  # the published rule's own cutoff, TASK-0282's LOTO-selected value -- fixed, not swept


def apply_ratio_rule(cands: list) -> dict:
    """`druggability / size`, MIN_HOP>=1 -- TASK-0292 Part D's own formula,
    `d / max(n, 1)`, reused verbatim."""
    survivors = [c for c in cands if c["min_hop"] >= MIN_HOP]
    if not survivors:
        return {"EH": 0.0, "flag": "no_survivors"}
    top = max(survivors, key=lambda c: c["fpocket_drug"] / max(c["n_res"], 1))
    return {"EH": float(top["EH"]), "flag": None}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    new_cand = yaml.safe_load((_ROOT / "config/candidate_targets_task0243.yaml").read_text())["targets"]
    for d in m.DROPPED:
        new_cand.pop(d, None)
    m.t0242.CAND = new_cand
    frozen_targets = [t for t in new_cand.keys() if t in CM]
    assert len(frozen_targets) == 20, f"expected 20 frozen targets, got {len(frozen_targets)}"

    print(f"=== Building candidates: {len(frozen_targets)} frozen-set targets ===")
    published_rule = ("hop", MIN_HOP, "drug_alone", None)
    rows = []
    errors = {}
    for t in frozen_targets:
        try:
            d = m.build_target(t)
        except Exception as e:  # noqa: BLE001
            d = {"error": f"{type(e).__name__}: {e}"}
        if "error" in d:
            errors[t] = d["error"]
            print(f"  {t:<22} SKIP: {d['error'][:70]}")
            continue
        pub = m.apply_rule(d["cands"], published_rule)
        rat = apply_ratio_rule(d["cands"])
        rows.append({"target": t, "published_EH": pub["EH"], "published_flag": pub["flag"],
                      "ratio_EH": rat["EH"], "ratio_flag": rat["flag"],
                      "n_candidates": len(d["cands"])})
        print(f"  {t:<22} published={pub['EH']:.3f}  ratio={rat['EH']:.3f}  "
              f"diff={rat['EH']-pub['EH']:+.3f}")

    n_attempted = len(frozen_targets)
    ok = [r for r in rows]
    print(f"\nscoreable: {len(ok)}/{n_attempted}")

    pub_vals = [r["published_EH"] for r in ok]
    rat_vals = [r["ratio_EH"] for r in ok]
    print(f"\n=== Means (n={len(ok)}) ===")
    print(f"  published (druggability alone) : mean EH = {np.mean(pub_vals):.4f}")
    print(f"  ratio (druggability / size)    : mean EH = {np.mean(rat_vals):.4f}")
    print(f"  delta                          : {np.mean(rat_vals) - np.mean(pub_vals):+.4f}")

    n_wins = sum(1 for r in ok if r["ratio_EH"] > r["published_EH"])
    n_ties = sum(1 for r in ok if r["ratio_EH"] == r["published_EH"])
    n_losses = sum(1 for r in ok if r["ratio_EH"] < r["published_EH"])
    print(f"\n  ratio beats published on {n_wins}/{len(ok)} folds, ties {n_ties}, loses {n_losses}")

    # naive Wilcoxon, matching TASK-0292's own reported statistic for direct comparability
    diffs = np.array(rat_vals) - np.array(pub_vals)
    if np.any(diffs != 0):
        w = wilcoxon(rat_vals, pub_vals)
        print(f"\n  naive Wilcoxon (row-level, matches TASK-0292's own reported stat): "
              f"p={w.pvalue:.4f}")
    else:
        w = None
        print("\n  naive Wilcoxon: undefined (all diffs zero)")

    # cluster-robust, TASK-0261's own exact sign-flip test -- the treatment this task's own Scope requires
    diff_map = {r["target"]: r["ratio_EH"] - r["published_EH"] for r in ok}
    cr = cluster_sign_flip_test(diff_map)
    print(f"\n=== Cluster-robust (TASK-0261, 13 clusters, exact sign-flip) ===")
    print(f"  ratio - published: median_diff={cr['median']:.4f}  p={cr['p_value']:.4f}  "
          f"n_clusters={cr['n_clusters']}")

    verdict = "SURVIVES" if cr["p_value"] < 0.05 else "DOES NOT SURVIVE"
    print(f"\n*** VERDICT: druggability/size {verdict} cluster-robust LOTO "
          f"(p={cr['p_value']:.4f} {'<' if cr['p_value']<0.05 else '>='} 0.05) ***")

    out = {
        "min_hop": MIN_HOP, "rows": rows, "errors": errors,
        "n_attempted": n_attempted, "n_scoreable": len(ok),
        "mean_published_EH": float(np.mean(pub_vals)), "mean_ratio_EH": float(np.mean(rat_vals)),
        "n_wins": n_wins, "n_ties": n_ties, "n_losses": n_losses,
        "naive_wilcoxon_p": float(w.pvalue) if w is not None else None,
        "cluster_robust": cr, "verdict": verdict,
    }
    (OUT / "loto_druggability_per_size.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwritten: {OUT / 'loto_druggability_per_size.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
