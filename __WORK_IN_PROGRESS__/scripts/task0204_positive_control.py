"""TASK-0204 (reopened) -- the positive control the original run never had.

The original TASK-0204 run concluded "criterion #1 fails, 0/2 targets,
route closed" from 34 trials, all of which were misses. This script asks
the question that must be answered before any of those misses can be
interpreted:

    Can this pipeline (EvoEF2 repack -> fpocket -> hit criterion) detect a
    druggable cavity that is KNOWN to be present?

The original run scored only the **apo** structure. For a genuinely
cryptic pocket the apo cavity is closed by definition, so "miss" is the
expected result there and carries no information about whether repacking
could ever open it. The holo structure -- where the drug demonstrably
binds -- is the one place we know a druggable cavity exists. It was
loaded by the original script (`_load_apo_holo`) but only ever used to
build labels; it was never scored.

## The ladder

Per target, at that structure's own pocket window, ligand stripped:

  1. `holo_native`     -- deposited holo, unmodified.  THE POSITIVE CONTROL.
  2. `holo_greedy`     -- holo, EvoEF2 GreedyRepack (single-pass, deterministic).
  3. `holo_optimized`  -- holo, EvoEF2 SideChainRepack (SA), N trials.
  4. `apo_native`      -- deposited apo, unmodified.  Reproduces the original
                          run's own `native_sanity` as a wiring check.

## How to read it

  - `holo_native` MISSES
        -> fpocket + this hit criterion cannot see the cavity even when it
           is open. Every number in the original run is uninterpretable and
           the route is untested, not closed.
  - `holo_native` hits, `holo_greedy`/`holo_optimized` MISS
        -> repacking itself destroys the cavity signal, independent of
           optimization. The original 0/8 measures a repacking artifact,
           not the hypothesis. Route untested, and we have the mechanism.
  - all three hit
        -> the pipeline is sound and the original apo-side result stands
           on its own terms.

Continuous legs (`overlap_frac`, `druggability_score`) are reported for
every arm, never collapsed to the conjunctive boolean alone -- the
original run's 32-trial negative discarded exactly the information needed
to tell a near miss from a far one.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
_SCRIPTS = _ROOT / "scripts"
_TESTS = _ROOT / "tests"
for _p in (_SRC, _SCRIPTS, _TESTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.labels import ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue  # noqa: E402
from task0163_external_baseline_scoring import _run_fpocket  # noqa: E402
from task0204_rotamer_repack_baseline import (  # noqa: E402
    EVOEF2_BIN, EVOEF2_DIR, WINDOW_MAX_SIZE, _best_druggability_at_window, _is_hit,
)
from test_gnm_cutoff_weight_benchmark import _holo_native_labels  # noqa: E402

N_TRIALS = 8
TARGETS = ["KRAS_G12C", "BCR_ABL1"]
OUT_DIR = _ROOT / "results_task0204_positive_control"


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _load_role(target_name: str, cfg: dict, role: str):
    """`clean_from_config` for either role, with the ligand-group and
    heavy-atom attributes `_holo_native_labels`/`functional_indices` need
    -- the same assembly `task0204_rotamer_repack_baseline._load_apo_holo`
    does for holo, generalized to either role rather than re-derived."""
    import prody

    prody.confProDy(verbosity="none")
    struct_obj = clean_from_config(target_name, role=role)
    pdb_id = cfg["holo_pdb"] if role == "holo" else cfg["apo_pdb"]
    chains = cfg.get("chains") or sorted(set(struct_obj.chain_ids))
    chain_sel = " or ".join(f"chain {c}" for c in chains)
    raw = prody.parsePDB(pdb_id, compressed=False).select(chain_sel)
    struct_obj.ligand_groups = ligand_groups_from_atomgroup(raw)
    struct_obj.heavy_atom_coords, struct_obj.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
        raw, chains, struct_obj.resnums
    )
    return struct_obj


def _select_window(struct_obj, pocket_mask: np.ndarray, max_size: int = WINDOW_MAX_SIZE):
    """Identical rule to the original run's `_select_window` (pocket
    residues, capped at `max_size` by nearest-to-pocket-centroid), applied
    to whichever structure's own frame is passed in."""
    idx = np.where(pocket_mask)[0]
    if len(idx) > max_size:
        centroid = struct_obj.coords[idx].mean(axis=0)
        d = np.linalg.norm(struct_obj.coords[idx] - centroid, axis=1)
        idx = idx[np.argsort(d)[:max_size]]
    chain_ids = np.asarray(struct_obj.chain_ids)
    return [(str(chain_ids[i]), int(struct_obj.resnums[i])) for i in idx]


def _write_full_atom_with_window_chain(pdb_id: str, keep_chains, window: list, out_path: Path) -> str:
    """`task0204_rotamer_repack_baseline._write_full_atom_with_window_chain`,
    generalized from its hardcoded `target_config["apo_pdb"]` to an
    arbitrary PDB id so the holo arm can use it. Every other behaviour is
    preserved verbatim, including the contiguous-per-chain-block write
    order that sidesteps EvoEF2's A-B-A chain-parser bug (see that
    function's own docstring for the full diagnosis).

    `select("protein")` also strips the drug ligand, which is required
    here and not incidental: fpocket must find the cavity as a cavity, not
    be handed the molecule that fills it.
    """
    import prody

    prody.confProDy(verbosity="none")
    struct = prody.parsePDB(pdb_id, compressed=False)
    alt_locs = struct.getAltlocs()
    if alt_locs is not None and any(a not in ("", " ", "\x00") for a in alt_locs):
        struct = struct.select("altloc _ A") or struct
    chain_part = " and (" + " or ".join(f"chain {c}" for c in keep_chains) + ")"
    struct_clean = struct.select(f"protein{chain_part}").copy()

    window_set = set(window)
    chids = struct_clean.getChids()
    resnums = struct_clean.getResnums()
    new_chids = chids.copy()
    for i in range(len(new_chids)):
        if (chids[i], int(resnums[i])) in window_set:
            new_chids[i] = "B"
    struct_clean.setChids(new_chids)

    is_window = new_chids == "B"
    reordered = struct_clean[np.where(~is_window)[0]] + struct_clean[np.where(is_window)[0]]
    prody.writePDB(str(out_path), reordered)
    return "B"


def _run_evoef2(command: str, pdb_path: Path, design_chains: str):
    """Vendored EvoEF2. Must be invoked with a RELATIVE argv[0] and
    `cwd=EVOEF2_DIR` -- an absolute argv[0] SIGSEGVs reproducibly (the
    original run isolated this 5/5 vs 5/5; see its own docstring)."""
    if not EVOEF2_BIN.exists():
        return {"error": f"EvoEF2 binary not found at {EVOEF2_BIN}"}
    local_pdb = EVOEF2_DIR / pdb_path.name
    local_pdb.write_bytes(pdb_path.read_bytes())
    result = subprocess.run(
        [f"./{EVOEF2_BIN.name}", f"--command={command}", f"--pdb={local_pdb.name}",
         f"--design_chains={design_chains}"],
        cwd=EVOEF2_DIR, capture_output=True, text=True, timeout=300,
    )
    out_path = EVOEF2_DIR / f"{pdb_path.stem}_beststruct.pdb"
    if result.returncode != 0 or not out_path.exists():
        tail = result.stderr.strip()[:500] or result.stdout.strip()[-500:]
        return {"error": f"EvoEF2 {command} exited {result.returncode}: {tail}"}
    return out_path


def score_structure(pdb_path: Path, target_set: set, work_dir: Path) -> dict:
    """fpocket writes `<stem>_out/` next to its INPUT file, so the input
    must live in `work_dir` for `_run_fpocket` to find the output (the
    original run's own bug #4). Each call also gets a unique stem so a
    stale `<stem>_out/` from a previous trial can never be read back --
    the original script reused one stem (`<target>_window`) for every
    trial in the loop."""
    stem = f"{pdb_path.stem}_{time.monotonic_ns()}"
    local_copy = work_dir / f"{stem}.pdb"
    local_copy.write_bytes(pdb_path.read_bytes())
    pockets = _run_fpocket(local_copy, work_dir)
    if isinstance(pockets, dict) and "error" in pockets:
        return {"error": pockets["error"]}
    overlap, drug = _best_druggability_at_window(pockets, target_set)
    return {
        "overlap_frac": overlap,
        "druggability_score": drug,
        "hit": _is_hit(overlap, drug),
        "n_pockets": len(pockets),
    }


def _repack_arm(command: str, base_pdb: Path, design_chain: str, target_set: set,
                work_dir: Path, n_trials: int, label: str) -> list:
    trials = []
    for i in range(n_trials):
        if i:
            time.sleep(1.05)  # EvoEF2 seeds from time(NULL), second resolution
        out = _run_evoef2(command, base_pdb, design_chain)
        trials.append({"error": out["error"]} if isinstance(out, dict)
                      else score_structure(out, target_set, work_dir))
        _log(f"  {label} trial {i+1}/{n_trials}: {trials[-1]}")
    return trials


def run_target(name: str) -> dict:
    t0 = time.monotonic()
    cfg = load_target_config(name)
    pocket_cutoff = float(cfg.get("pocket_contact_cutoff", 4.5))
    out: dict = {"target": name}

    # ---------------- holo arm: the positive control ----------------
    _log(f"{name}: loading holo + building holo-frame pocket label...")
    holo = _load_role(name, cfg, "holo")
    holo_pocket, _holo_active, _ = _holo_native_labels(holo, cfg, pocket_cutoff)
    if holo_pocket is None or not holo_pocket.any():
        return {"target": name, "error": "no resolvable holo-frame pocket label"}
    holo_window = _select_window(holo, holo_pocket)
    out["holo_window"] = holo_window
    _log(f"{name}: holo window = {len(holo_window)} residues: {holo_window}")

    holo_chains = cfg.get("chains") or sorted(set(holo.chain_ids))
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        holo_pdb = tmp / f"{name.lower()}_holo_window.pdb"
        design_chain = _write_full_atom_with_window_chain(
            cfg["holo_pdb"], holo_chains, holo_window, holo_pdb
        )
        holo_set = {(design_chain, r) for (_c, r) in holo_window}

        _log(f"{name}: POSITIVE CONTROL -- native holo, ligand stripped...")
        out["holo_native"] = score_structure(holo_pdb, holo_set, tmp)
        _log(f"{name}: holo_native = {out['holo_native']}")

        _log(f"{name}: holo GreedyRepack...")
        g = _run_evoef2("GreedyRepack", holo_pdb, design_chain)
        out["holo_greedy"] = {"error": g["error"]} if isinstance(g, dict) else score_structure(g, holo_set, tmp)
        _log(f"{name}: holo_greedy = {out['holo_greedy']}")

        _log(f"{name}: holo SideChainRepack x{N_TRIALS}...")
        out["holo_optimized_trials"] = _repack_arm(
            "SideChainRepack", holo_pdb, design_chain, holo_set, tmp, N_TRIALS, "holo_optimized"
        )

    # ---------------- apo arm: wiring check against the original run ----------------
    _log(f"{name}: apo native (reproduces the original run's own native_sanity)...")
    apo = _load_role(name, cfg, "apo")
    holo_for_labels = _load_role(name, cfg, "holo")
    from allostery.labels import build_labels

    labels_obj = build_labels(apo, holo_for_labels, cfg, cutoff=pocket_cutoff)
    apo_window = _select_window(apo, labels_obj.pocket)
    out["apo_window"] = apo_window
    apo_chains = cfg.get("apo_chains") or cfg.get("chains")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        apo_pdb = tmp / f"{name.lower()}_apo_window.pdb"
        dc = _write_full_atom_with_window_chain(cfg["apo_pdb"], apo_chains, apo_window, apo_pdb)
        out["apo_native"] = score_structure(apo_pdb, {(dc, r) for (_c, r) in apo_window}, tmp)
    _log(f"{name}: apo_native = {out['apo_native']} (original run reported this as `native_sanity`)")

    valid = [t for t in out["holo_optimized_trials"] if "error" not in t]
    out["summary"] = {
        "holo_native_hit": out["holo_native"].get("hit"),
        "holo_greedy_hit": out["holo_greedy"].get("hit"),
        "holo_optimized_hit_rate": (sum(t["hit"] for t in valid) / len(valid)) if valid else None,
        "holo_optimized_n_valid": len(valid),
        "apo_native_hit": out["apo_native"].get("hit"),
        "positive_control_passes": bool(out["holo_native"].get("hit")),
    }
    out["elapsed_s"] = round(time.monotonic() - t0, 1)
    _log(f"{name}: SUMMARY {out['summary']}")
    return out


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    results = {}
    for name in TARGETS:
        try:
            results[name] = run_target(name)
        except Exception as exc:  # noqa: BLE001 -- one target must not kill the run
            _log(f"{name}: ERROR {type(exc).__name__}: {exc}")
            results[name] = {"target": name, "error": f"{type(exc).__name__}: {exc}"}
        (OUT_DIR / "positive_control.json").write_text(json.dumps(results, indent=1))

    print("\n=== TASK-0204 positive control ===")
    for name, r in results.items():
        if "error" in r:
            print(f"{name}: ERROR {r['error']}")
            continue
        s = r["summary"]
        print(f"{name}: holo_native_hit={s['holo_native_hit']} "
              f"holo_greedy_hit={s['holo_greedy_hit']} "
              f"holo_optimized_rate={s['holo_optimized_hit_rate']} "
              f"apo_native_hit={s['apo_native_hit']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
