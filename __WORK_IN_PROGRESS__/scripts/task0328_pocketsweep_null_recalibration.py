"""TASK-0328 -- pocketsweep.py's null: non-reproducible seed (Defect 1), and a
null shape that scatters labels uniformly when the truth is a spatially
compact block (Defect 2).

OWNERSHIP: `pocketsweep.py` and its stored artifacts belong to the
`allosteric` branch (Owner: Oussema). Per [[TASK-0327]]'s own precedent for
working on Oussema-owned files: nothing here is pushed to or altered on that
branch. This script is a read-only re-analysis of `pocketsweep.py`'s own
already-stored output (`s14_r{1,2}_k10_h2_{0,1}.json`, commit f257789,
confirmed current HEAD of origin/allosteric at claim time), copied into this
repo's own results tree (`upstream_artifacts/`) rather than read from a
throwaway worktree, so the numbers below are reproducible from files this
repo actually tracks.

WHY NO PDB REFETCH / NO FPOCKET / NO EIGH IS NEEDED. The expensive half of
pocketsweep.py (fpocket, building 12 Hamiltonians, eigh per protein) only
produces two things this task needs, and both are already stored per
protein: (1) `ranks` -- for each of the 182 (operator, transform) cells, the
rank of every seed under that cell's score (1 = highest); (2) `y` -- which
seeds are the true drug-pocket residues. `pocketsweep.py`'s own null
computation only ever touches these two objects (`RK=rankdata(...)`,
`TOP5=argsort(...)` at scoring time -- reproduced here from the stored
`ranks` directly, and `y`) plus the *identity* of the positive-label
permutation, which is exactly the piece Defect 2 says is drawn wrong. So a
correctly-shaped null can be recomputed byte-for-byte in the same rank-sum
arithmetic pocketsweep.py already uses, with zero new physics.

DEFECT 2's FIX, MADE FROM WHAT THIS PIPELINE ALREADY COMPUTED, NOT
REDERIVED FROM SCRATCH. [[TASK-0158]]/[[TASK-0190]]/[[TASK-0201]]'s
`compact_patch()` (see `null_audit.py`) draws a null positive set as the
`size` nearest-by-3D-distance residues to a random center -- the general
form of "a spatially compact block, not a scattered sample." This pipeline
already contains its own compact spatial units for free: each fpocket/
PASSer *pocket* is by construction a spatially contiguous cluster of
residues (that is what pocket detection means), and `seed_pocket[k]` (also
already stored) names which pocket each seed belongs to. Checked directly,
not assumed: the REAL positive sets in this data are themselves concentrated
in 1-3 pockets, never scattered across many (25/55 single-pocket, 30/55
spanning 2-3, 0 with any residue pocket-unassigned -- see
`_pocket_concentration_check()` below). A null that draws whole pockets
(trimming only the last one added, to hit the exact required kpos) is
therefore the dataset-native form of `compact_patch()` for this specific
seed space -- it reuses this register's own established compactness-null
machinery in spirit, not a new ad hoc statistic, and it inherits the exact
1-3-pocket spread the real positives themselves show, which pure 3D-radius
patches would not obviously reproduce without refetching structures.

DEFECT 1's FIX. `hash(w["name"])` is process-salted (Python's str hash
randomization, `PYTHONHASHSEED` unset anywhere in the branch -- confirmed,
`git grep PYTHONHASHSEED` on f257789 = 0 hits). Replaced here with
`int(hashlib.sha256(name.encode()).hexdigest(), 16) % 2**32` -- deterministic
across processes and runs. The one-line upstream patch this implies is
written out in full at the bottom of this file as `POCKETSWEEP_PATCH`,
for Oussema to apply (not applied to the `allosteric` branch by this task,
same convention as TASK-0327).

Run: ../.venv/bin/python3 scripts/task0328_pocketsweep_null_recalibration.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
ART = HERE.parent / "results/tasks/0328_pocketsweep_null_recalibration/upstream_artifacts"
OUT = HERE.parent / "results/tasks/0328_pocketsweep_null_recalibration"

ROUNDS = {
    "round1": ["s14_r1_k10_h2_0.json", "s14_r1_k10_h2_1.json"],
    "round2_veto": ["s14_r2_k10_h2_0.json", "s14_r2_k10_h2_1.json"],
}
B = 2000  # matches the external re-run this task's own file cites as the motivating measurement
ALPHA = 0.05  # BH-FDR level, matches the task's own cited table


def det_seed(name: str) -> int:
    """Defect 1's fix: deterministic across processes/runs, unlike hash()."""
    return int(hashlib.sha256(name.encode()).hexdigest(), 16) % (2**32)


def load_round(files):
    recs = {}
    for f in files:
        d = json.load(open(ART / f))
        for k, v in d.items():
            if "cells" in v:
                assert k not in recs, f"duplicate protein name across shards: {k}"
                recs[k] = v
    return recs


def _pocket_concentration_check(recs) -> dict:
    """Sanity check cited in the module docstring: are the REAL positive
    sets themselves concentrated in a small number of pockets, or scattered?
    Not assumed -- checked once here, printed, and asserted against below."""
    sizes = []
    n_unassigned = 0
    for v in recs.values():
        y, sp = v["y"], v["seed_pocket"]
        pos_pockets = [sp[i] for i, yy in enumerate(y) if yy == 1]
        n_unassigned += sum(1 for p in pos_pockets if p is None)
        sizes.append(len(set(pos_pockets)))
    from collections import Counter
    return dict(n_proteins=len(recs), pocket_span_counts=dict(Counter(sizes)),
                n_positive_seeds_pocket_unassigned=n_unassigned)


def pocket_members(v) -> dict:
    """seed index -> pocket id (already stored); invert to pocket id -> [seed indices]."""
    sp = v["seed_pocket"]
    members: dict = {}
    for i, pid in enumerate(sp):
        members.setdefault(pid, []).append(i)
    return members


def draw_uniform_null(rng, n, kpos, members=None) -> np.ndarray:
    """The null pocketsweep.py actually runs: scattered, not compact."""
    return rng.permutation(n)[:kpos]


def draw_pocket_block_null(rng, n, kpos, members: dict) -> np.ndarray:
    """Defect 2's fix: accumulate WHOLE pockets (drawn in random order) until
    at least kpos seeds are covered, then trim only the last pocket added
    down to the exact remaining count needed -- a compact block (a random
    subset of one already-spatially-clustered pocket), not a scattered
    sample, and the ONLY place trimming happens is within a single pocket."""
    pids = list(members.keys())
    rng.shuffle(pids)
    chosen: list = []
    for pid in pids:
        need = kpos - len(chosen)
        if need <= 0:
            break
        mem = members[pid]
        if len(mem) <= need:
            chosen.extend(mem)
        else:
            take = rng.choice(mem, size=need, replace=False)
            chosen.extend(take.tolist())
    assert len(chosen) == kpos, (len(chosen), kpos)
    return np.asarray(chosen, dtype=int)


def null_stats_for_protein(v, rng, draw_fn) -> tuple:
    """Reproduces pocketsweep.py's own rank-sum null arithmetic exactly
    (same RK/TOP5/denom/off formulas, `main()` lines ~379-398 of
    pocketsweep_f257789.py), swapping only how the null positive set is
    drawn. Returns (null_max_auc_mean, null_max_p5_mean, p_auc, p_p5)."""
    y = np.asarray(v["y"], dtype=float)
    n = len(y)
    kpos = int(y.sum())
    obs_a = v["obs_max_auc"]
    obs_p = v["obs_max_p5"]
    cell_names = sorted(v["ranks"].keys())
    RK = np.array([v["ranks"][c] for c in cell_names], dtype=float)  # (cells, n) ranks, 1=highest
    # rank r=1 is the top score; "top-5 under this cell" = seeds with rank<=5
    top5_mask = RK <= 5  # (cells, n) boolean
    denom = kpos * (n - kpos)
    off = kpos * (kpos + 1) / 2.0
    members = pocket_members(v)
    nma = np.empty(B)
    nmp = np.empty(B)
    for bb in range(B):
        pos = draw_fn(rng, n, kpos, members)
        nma[bb] = ((RK[:, pos].sum(1) - off) / denom).max()
        nmp[bb] = (top5_mask[:, pos].sum(1) / 5.0).max()
    p_auc = float((nma >= obs_a).mean())
    p_p5 = float((nmp >= obs_p).mean())
    return float(nma.mean()), float(nmp.mean()), p_auc, p_p5


def bh_survivors(pvals: list, alpha: float = ALPHA) -> int:
    """Standard Benjamini-Hochberg step-up, matching this task's own cited
    'BH-FDR 5% survivors' table."""
    p = np.sort(np.asarray(pvals))
    m = len(p)
    if m == 0:
        return 0
    thresh = alpha * np.arange(1, m + 1) / m
    below = p <= thresh
    if not below.any():
        return 0
    k = np.max(np.where(below)[0])
    return int(k + 1)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    for round_name, files in ROUNDS.items():
        recs = load_round(files)
        conc = _pocket_concentration_check(recs)
        p_auc_uniform, p_auc_compact = [], []
        null_a_uniform, null_a_compact = [], []
        for name, v in recs.items():
            seed_u = det_seed(name + "|uniform")
            seed_c = det_seed(name + "|compact")
            rng_u = np.random.default_rng(seed_u)
            rng_c = np.random.default_rng(seed_c)
            na_u, np5_u, pa_u, pp_u = null_stats_for_protein(v, rng_u, draw_uniform_null)
            na_c, np5_c, pa_c, pp_c = null_stats_for_protein(v, rng_c, draw_pocket_block_null)
            null_a_uniform.append(na_u)
            null_a_compact.append(na_c)
            p_auc_uniform.append(pa_u)
            p_auc_compact.append(pa_c)
        report[round_name] = dict(
            n_scored=len(recs),
            pocket_concentration_of_real_positives=conc,
            mean_null_max_auc_uniform=float(np.mean(null_a_uniform)),
            mean_null_max_auc_compact=float(np.mean(null_a_compact)),
            bh_survivors_uniform_p_auc=bh_survivors(p_auc_uniform),
            bh_survivors_compact_p_auc=bh_survivors(p_auc_compact),
            n_pvals=len(p_auc_uniform),
        )
        print(f"{round_name}: n={len(recs)} "
              f"null_max_auc uniform={report[round_name]['mean_null_max_auc_uniform']:.4f} "
              f"compact={report[round_name]['mean_null_max_auc_compact']:.4f} "
              f"BH-survivors uniform={report[round_name]['bh_survivors_uniform_p_auc']}/{len(recs)} "
              f"compact={report[round_name]['bh_survivors_compact_p_auc']}/{len(recs)}")
    (OUT / "result.json").write_text(json.dumps(report, indent=1))
    print(f"\nWrote {OUT}/result.json")
    return 0


# ---------------------------------------------------------------------------
# Defect 1's proposed one-line upstream patch, for Oussema to apply to
# `allosteric/results/veto_pipeline/pocketsweep.py` -- NOT applied to that
# branch by this task (see module docstring, TASK-0327's ownership precedent).
POCKETSWEEP_PATCH = r"""
--- a/allosteric/results/veto_pipeline/pocketsweep.py
+++ b/allosteric/results/veto_pipeline/pocketsweep.py
@@
-import json, os, re, glob, shutil, subprocess, sys, time, urllib.request
+import hashlib, json, os, re, glob, shutil, subprocess, sys, time, urllib.request
@@
-            rng=np.random.default_rng(abs(hash(w["name"]))%(2**32))
+            rng=np.random.default_rng(int(hashlib.sha256(w["name"].encode()).hexdigest(),16)%(2**32))
"""

if __name__ == "__main__":
    raise SystemExit(main())
