"""TASK-0253 -- audit two defects in TASK-0243's own frozen 22-target set
(`config/candidate_targets_task0243.yaml`), surfaced by TASK-0249's real run
but not root-caused there (explicitly out of that task's own scope):

1. TASK-0243's own Done section claims "20/22 resolve to source: uniprot...
   zero fell back to a top-degree proxy" -- but TASK-0249 found
   HIV_INTEGRASE_MUT871/916 (apo 1M9D) have an EMPTY active-site seed on
   every chain. Both cannot be true. Re-verify every target's seed
   provenance directly, the same way the pipeline actually resolves it
   (`backend.active_site.detect_active_site`, TASK-0242's own `prep()`
   call shape), not by re-trusting the config file's own static
   `active_site_source` field.

2. Stage-1 recall is 64-73% across three independent target sets
   (TASK-0242 n=11, TASK-0243 n=22) -- a stable pipeline property, not
   sampling noise. But TASK-0242's own `run()` reports "true drug pocket
   not among surviving fpocket candidates" identically whether fpocket
   never proposed the true pocket at all, or proposed it and MIN_HOP then
   filtered it out. These are different failure modes with different
   implications (a detection gap vs. a parameter-choice cost). Decompose
   them using TASK-0244's own `return_state=True` extension, further
   extended here (additively, opt-in) to expose which case occurred.

Reuses task0242_two_stage_dryrun.py's own prep()/run()/CAND-swap pattern
exactly as task0243_stage1_and_rerun.py already established -- no
candidate-generation or seed-detection logic re-derived.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _ROOT.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _REPO_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import prody  # noqa: E402
import yaml  # noqa: E402

prody.confProDy(verbosity="none")
# Same TASK-0039 altloc fix task0243_stage1_and_rerun.py already applies
# locally to task0242's own script -- reused verbatim, not re-derived.
_orig_parsePDB = prody.parsePDB


def _parsePDB_all_altloc(*a, **kw):
    kw.setdefault("altloc", "all")
    return _orig_parsePDB(*a, **kw)


prody.parsePDB = _parsePDB_all_altloc

import task0242_two_stage_dryrun as t0242  # noqa: E402
from backend import active_site as backend_as  # noqa: E402

OUT = _ROOT / "results/tasks/0253_frozen_set_audit"
CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"


def audit_seed(name: str, cfg: dict) -> dict:
    """Re-run detect_active_site exactly as prep() calls it (first apo
    chain, production behavior), then additionally sweep every apo chain
    to distinguish 'wrong chain requested' from 'genuinely no site
    anywhere on this structure' when the first-chain call comes up empty."""
    apo_chains = cfg.get("apo_chains") or cfg.get("chains")
    apo_pdb = cfg["apo_pdb"]

    prod = backend_as.detect_active_site(apo_pdb, chain=apo_chains[0])
    prod_source = prod.get("source")
    prod_n = len(prod.get("active_site") or [])

    row = {
        "target": name, "apo_pdb": apo_pdb, "apo_chain_used": apo_chains[0],
        "config_claims_source": cfg.get("active_site_source"),
        "live_source": prod_source, "live_n_residues": prod_n,
        "config_matches_live": (cfg.get("active_site_source") == prod_source),
    }

    if prod_n == 0:
        # First-chain call failed -- sweep every apo chain of this target,
        # per this task's own Scope ("re-verify... not just the two that
        # failed"), to tell "wrong chain would have worked" apart from
        # "no chain resolves anything".
        sweep = {}
        for ch in apo_chains:
            r = backend_as.detect_active_site(apo_pdb, chain=ch)
            sweep[ch] = {"source": r.get("source"), "n_residues": len(r.get("active_site") or [])}
        row["all_chains_swept"] = sweep
        row["any_chain_resolves"] = any(v["n_residues"] > 0 for v in sweep.values())

    return row


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cand = yaml.safe_load(CONFIG.read_text())["targets"]
    t0242.CAND = cand
    targets = list(cand.keys())

    print(f"=== Seed re-verification, {len(targets)} targets ===\n")
    seed_rows = []
    for name in targets:
        r = audit_seed(name, cand[name])
        seed_rows.append(r)
        flag = "" if r["config_matches_live"] else "  <-- CONFIG MISMATCH"
        print(f"{name:<24} config={r['config_claims_source']:<8} live={r['live_source']:<8} "
              f"n={r['live_n_residues']:<3}{flag}")

    n_uniprot = sum(1 for r in seed_rows if r["live_source"] == "uniprot")
    n_ligand = sum(1 for r in seed_rows if r["live_source"] == "ligand")
    n_site = sum(1 for r in seed_rows if r["live_source"] == "pdb_site")
    n_none = sum(1 for r in seed_rows if r["live_source"] == "none")
    n_mismatch = sum(1 for r in seed_rows if not r["config_matches_live"])
    print(f"\nLive distribution: uniprot={n_uniprot} ligand={n_ligand} "
          f"pdb_site={n_site} none={n_none} (of {len(targets)})")
    print(f"Config-vs-live mismatches: {n_mismatch}")

    print("\n=== Stage-1 run, with failure-mode decomposition ===\n")
    stage1_rows = []
    for name in targets:
        t0 = time.monotonic()
        try:
            r = t0242.run(name, tuned=False, return_state=True)
        except Exception as exc:  # noqa: BLE001
            r = {"target": name, "error": f"{type(exc).__name__}: {exc}"}
        # Strip non-JSON-serializable return_state fields before saving,
        # keep only what this audit needs.
        for k in ("kept", "coords", "bfactors", "resn"):
            r.pop(k, None)
        elapsed = time.monotonic() - t0
        stage1_rows.append(r)
        if "error" in r:
            reason = r.get("failure_reason", "unclassified")
            print(f"{name:<24} FAIL ({elapsed:.1f}s) reason={reason:<20} {r['error'][:60]}")
        else:
            print(f"{name:<24} OK   ({elapsed:.1f}s) K={r['n_kept']}")

    ok = [r for r in stage1_rows if "error" not in r]
    fail = [r for r in stage1_rows if "error" in r]
    reasons = {}
    for r in fail:
        reasons[r.get("failure_reason", "unclassified")] = reasons.get(r.get("failure_reason", "unclassified"), 0) + 1
    print(f"\nStage-1 recall: {len(ok)}/{len(targets)} = {len(ok)/len(targets):.1%}")
    print(f"Failure decomposition: {reasons}")

    (OUT / "seed_audit.json").write_text(json.dumps(seed_rows, indent=1, default=str))
    (OUT / "stage1_audit.json").write_text(json.dumps(stage1_rows, indent=1, default=str))
    print(f"\nwritten: {OUT/'seed_audit.json'}, {OUT/'stage1_audit.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
