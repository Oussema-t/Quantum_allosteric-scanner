#!/usr/bin/env python3
"""TASK-0265 -- same apo structure, two different ligands: is "the pocket"
one thing? Re-implements the transient `/tmp/pairtest.py` (Reviewer,
2026-08-25) as a proper script, and extends it: that script grouped by
`(apo_pdb, chains)`, which silently EXCLUDED 2 of [[TASK-0261]]'s own 7
apo-shared pairs (GAC_BPTES/GAC_CPD12, FBPASE_94D/FBPASE_95S) because they
use a different chain SUBSET of the same apo entry, so their pocket masks
have different length and a positional set-difference doesn't apply. This
version keys pocket-label sets on (chain, resnum) identity instead of
positional index, so it covers all 7 pairs, not 5.

Motivation ([[TASK-0261]]'s own standing rule, filed the same day this
task questions it): "a second ligand on an apo structure already counted
is a new target for label-side questions." That rule implies the labels
differ *enough* to be informative as separate observations. This measures
exactly how much they differ -- Jaccard overlap of the two pocket-label
residue sets, same apo structure.

Reuses, does not re-derive: `task0242_two_stage_dryrun.prep` (seed/pocket
resolution, unchanged), [[TASK-0243]]'s frozen config, [[TASK-0255]]'s own
altloc="all" monkeypatch.

Run: ../.venv/bin/python3 scripts/task0265_pocket_label_overlap.py
"""
from __future__ import annotations

import json
import sys
import warnings
from collections import defaultdict
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import prody  # noqa: E402
import yaml  # noqa: E402

prody.confProDy(verbosity="none")

from task0255_hop_angstrom_calibration import _parsePDB_all_altloc  # noqa: E402

prody.parsePDB = _parsePDB_all_altloc

from task0242_two_stage_dryrun import prep, CAND  # noqa: E402

OUT = _ROOT / "results/tasks/0265_pocket_label_overlap"
FROZEN_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"


def pocket_label_set(target: str) -> tuple[set[tuple[str, int]], dict]:
    """(chain, resnum) identity set for the target's own true-pocket
    residues, plus a small info dict (n_res, apo_pdb, chains, drug)."""
    cfg, apo, seed, pocket = prep(target)
    chids = np.asarray(apo.chain_ids)
    resn = np.asarray(apo.resnums)
    idx = np.where(pocket)[0]
    keys = set((str(chids[i]), int(resn[i])) for i in idx)
    info = dict(n_res=len(resn), apo_pdb=cfg["apo_pdb"],
                chains=cfg.get("apo_chains") or cfg.get("chains"),
                drug=cfg["drug_ligand"])
    return keys, info


def jaccard_for_config(config_path: Path, group_by_chains: bool = False) -> list[dict]:
    """All same-apo-structure target pairs in `config_path`. `group_by_chains`
    reproduces the transient script's own (apo_pdb, chains)-exact grouping
    when True; when False (this task's own extension), groups by apo_pdb
    alone, matching [[TASK-0261]]'s own clustering unit."""
    cfg_all = yaml.safe_load(config_path.read_text())["targets"]
    CAND.update(cfg_all)  # t0242.prep() resolves through this module-level dict
    by_apo: dict = defaultdict(list)
    for t, c in cfg_all.items():
        apo_pdb = c.get("apo_pdb")
        if not apo_pdb:
            continue
        key = apo_pdb if not group_by_chains else (
            apo_pdb, tuple(c.get("apo_chains") or c.get("chains") or []))
        by_apo[key].append(t)
    pairs = {k: v for k, v in by_apo.items() if len(v) > 1}

    rows = []
    for key, ts in sorted(pairs.items()):
        apo_pdb = key if not group_by_chains else key[0]
        for i in range(len(ts)):
            for j in range(i + 1, len(ts)):
                a, b = ts[i], ts[j]
                try:
                    keys_a, info_a = pocket_label_set(a)
                    keys_b, info_b = pocket_label_set(b)
                except Exception as exc:  # noqa: BLE001
                    print(f"{apo_pdb:<8}{a:<22}{b:<22}  SKIP {type(exc).__name__}: {exc}")
                    continue
                inter, uni = len(keys_a & keys_b), len(keys_a | keys_b)
                jac = inter / uni if uni else float("nan")
                same_chains = info_a["chains"] == info_b["chains"]
                # Chain-identity-blind version: a homo-oligomer can deposit
                # the ligand on a different (but sequence-equivalent)
                # symmetric copy across two depositions -- (chain, resnum)
                # then reports zero overlap for what is the same site on a
                # different subunit. Resnum-only Jaccard catches that case;
                # both are reported, never only the flattering one.
                resn_a = set(r for _, r in keys_a)
                resn_b = set(r for _, r in keys_b)
                inter_r, uni_r = len(resn_a & resn_b), len(resn_a | resn_b)
                jac_resnum = inter_r / uni_r if uni_r else float("nan")
                rows.append(dict(
                    apo=apo_pdb, a=a, b=b, nA=len(keys_a), nB=len(keys_b),
                    shared=inter, union=uni, jaccard=jac,
                    jaccard_resnum_only=jac_resnum,
                    chains_a=info_a["chains"], chains_b=info_b["chains"],
                    same_chain_selection=same_chains,
                    drugA=info_a["drug"], drugB=info_b["drug"],
                ))
                flag = "" if same_chains else f"  (different chain subset -- resnum-only Jaccard {jac_resnum:.3f})"
                print(f"{apo_pdb:<8}{a:<22}{b:<22}{len(keys_a):>5}{len(keys_b):>5}"
                      f"{inter:>8}{jac:>9.3f}{flag}")
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    print("=== TASK-0243 frozen set: all 7 apo-shared pairs (grouped by apo_pdb alone) ===")
    print(f"{'apo':<8}{'ligand A':<22}{'ligand B':<22}{'|A|':>5}{'|B|':>5}{'shared':>8}{'Jaccard':>9}")
    rows = jaccard_for_config(FROZEN_CONFIG, group_by_chains=False)

    if rows:
        js = [r["jaccard"] for r in rows]
        print(f"\n  n={len(rows)} same-structure ligand pairs")
        print(f"  Jaccard: median {np.median(js):.3f}  min {min(js):.3f}  max {max(js):.3f}")
        for bar in (0.75, 0.50, 0.25):
            print(f"  pairs below {bar:.2f}: {sum(1 for x in js if x < bar)}/{len(js)}")

    print("\n=== 15 register targets (targets.yaml) ===")
    targets_yaml = _ROOT / "config" / "targets.yaml"
    rows_reg = jaccard_for_config(targets_yaml, group_by_chains=False)
    if not rows_reg:
        print("  no same-apo pairs found (matches [[TASK-0261]]'s own independence check)")

    print("\n=== TASK-0216 candidate set ===")
    t0216 = _ROOT / "config" / "candidate_targets_task0216.yaml"
    rows_216 = jaccard_for_config(t0216, group_by_chains=False) if t0216.exists() else []
    if not rows_216:
        print("  no same-apo pairs found (matches [[TASK-0261]]'s own independence check)")

    (OUT / "pocket_label_overlap.json").write_text(json.dumps(
        dict(frozen_set=rows, register_15=rows_reg, task0216=rows_216), indent=1))
    print(f"\nwritten: {OUT / 'pocket_label_overlap.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
