#!/usr/bin/env python3
"""TASK-0243's own Acceptance items 3+4: stage-1 recall + the full 5-ranker
protocol re-run, on THIS task's own frozen 22-pair set
(`config/candidate_targets_task0243.yaml`), reusing [[TASK-0242]]'s own
`prep`/`run`/`fpocket_candidates` machinery UNCHANGED (imported, not
copied) -- only the candidate config and target list differ.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import prody  # noqa: E402
import yaml  # noqa: E402

prody.confProDy(verbosity="none")
# Same root cause TASK-0039 fixed in allostery.clean.clean(): prody's own
# parsePDB() default (altloc="A") silently drops any ligand/atom whose
# ONLY deposited altloc label isn't 'A' -- confirmed directly on this
# run's own data (NAMPT_NPA1R's ligand TIE is altloc='D' in 8DSC, with
# no 'A' conformer at all, so `ligand_groups_from_atomgroup`/
# `holo_pocket_mask` in task0242_two_stage_dryrun.py's own `prep()` saw
# zero TIE atoms and crashed). task0242's own script is another task's
# owned artifact -- patched here, locally, for this run only, not edited
# at its source. TASK-0039's own validated fix (zero regressions on the
# full suite) is reused verbatim: force altloc="all" globally before
# calling into it.
_orig_parsePDB = prody.parsePDB


def _parsePDB_all_altloc(*a, **kw):
    kw.setdefault("altloc", "all")
    return _orig_parsePDB(*a, **kw)


prody.parsePDB = _parsePDB_all_altloc

import task0242_two_stage_dryrun as t0242  # noqa: E402

OUT = _ROOT / "results/tasks/0243_curate_untuned_targets"
NEW_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    new_cand = yaml.safe_load(NEW_CONFIG.read_text())["targets"]
    # Swap task0242's own CAND global -- its `prep()`/module-level
    # `load_target_config` monkeypatch both close over this name looked up
    # at CALL time (a module global, not bound at lambda-definition time),
    # so reassigning it here is sufficient; verified directly before
    # trusting it (see this task's own Done section).
    t0242.CAND = new_cand
    targets = list(new_cand.keys())

    print(f"protocol: MIN_HOP={t0242.MIN_HOP}, operator={t0242.PREREG_OPERATOR}, "
          f"n_targets={len(targets)} (all untuned -- none of this config's own targets "
          "were ever tuned on)\n")

    rows = []
    for t in targets:
        t0 = time.monotonic()
        try:
            r = t0242.run(t, tuned=False)
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            r = {"target": t, "error": f"{type(exc).__name__}: {exc}"}
        rows.append(r)
        elapsed = time.monotonic() - t0
        if "error" in r:
            print(f"{t:<24} SKIP ({elapsed:.1f}s): {r['error'][:80]}")
        else:
            print(f"{t:<24} K={r['n_kept']:<3} ranks={r['ranks']} ({elapsed:.1f}s)")
        (OUT / "stage1_rerun.json").write_text(json.dumps(rows, indent=1, default=str))

    n_attempted = len(rows)
    n_stage1_ok = sum(1 for r in rows if "error" not in r)
    print(f"\nStage-1 recall: {n_stage1_ok}/{n_attempted} = {n_stage1_ok/n_attempted:.1%}")

    survivors = [r for r in rows if "error" not in r]
    if survivors:
        import numpy as np
        from scipy.stats import wilcoxon

        for key in ("ctqw", "fpocket_drug", "fpocket_score", "hop_covariate", "random"):
            ranks = [r["ranks"][key] for r in survivors]
            print(f"{key:<15} mean_rank={np.mean(ranks):.2f} ranks={ranks}")

        ctqw_ranks = np.array([r["ranks"]["ctqw"] for r in survivors])
        fp_ranks = np.array([r["ranks"]["fpocket_drug"] for r in survivors])
        hop_ranks = np.array([r["ranks"]["hop_covariate"] for r in survivors])
        if len(survivors) >= 2:
            try:
                w_fp = wilcoxon(ctqw_ranks, fp_ranks)
                w_hop = wilcoxon(ctqw_ranks, hop_ranks)
                print(f"\nctqw vs fpocket_drug: Wilcoxon p={w_fp.pvalue:.4f}")
                print(f"ctqw vs hop_covariate: Wilcoxon p={w_hop.pvalue:.4f}")
            except Exception as exc:  # noqa: BLE001
                print(f"Wilcoxon failed: {exc!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
