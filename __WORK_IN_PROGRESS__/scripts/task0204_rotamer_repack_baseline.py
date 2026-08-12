#!/usr/bin/env python3
"""TASK-0204 -- Phase B's own falsification criterion #1: does classically-
optimized side-chain rotamer packing open an fpocket-druggable cavity more
often than a naive greedy (lowest-self-energy-per-residue) rotamer choice,
on real candidate windows?

Uses the vendored, minimally-patched EvoEF2 (`tools/evoef2/`, TASK-0204's
own patch -- see that directory's README) for all three packing conditions:

  - "optimized": `SideChainRepack` -- EvoEF2's own shipped simulated-
    annealing rotamer optimizer (real pairwise + self energy, real
    Dunbrack backbone-dependent rotamer library), unmodified.
  - "greedy": `GreedyRepack` (this task's patch) -- EvoEF2's own
    pre-existing `SequenceGenerateInitialSequenceSeed` (lowest self-energy
    per site, ignores pairwise terms), written out without any annealing.
  - "random": `RandomRepack` (this task's patch) -- EvoEF2's own
    pre-existing `SequenceGenerateRandomSeed` (uniform-random rotamer per
    site), written out without any annealing -- the negative control.

Reuses `task0163_external_baseline_scoring.py`'s own `_run_fpocket`/
`FPOCKET_BIN` for druggability scoring (this project's one already-tested
fpocket invocation), not reimplemented.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "4")

import numpy as np

_SRC = Path(__file__).resolve().parent.parent / "src"
_SCRIPTS = Path(__file__).resolve().parent
for _p in (_SRC, _SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from allostery.clean import clean_from_config, load_target_config  # noqa: E402
from allostery.labels import build_labels, ligand_groups_from_atomgroup, protein_heavy_atoms_by_residue  # noqa: E402
from task0163_external_baseline_scoring import _run_fpocket  # noqa: E402

EVOEF2_DIR = Path(__file__).resolve().parent.parent / "tools" / "evoef2"
EVOEF2_BIN = EVOEF2_DIR / "EvoEF2"

POCKET_HIT_OVERLAP = 0.5   # TASK-0185's own established "did fpocket find the pocket" bar, reused not reinvented
DRUGGABILITY_BAR = 0.5     # fpocket's own commonly-cited druggable/non-druggable cutoff
WINDOW_MAX_SIZE = 12        # PHASE_B_ROTAMER_QUBO.md's own m=12 example
N_TRIALS = 8                 # matches TASK-0181 Phase A's own 8-restart precedent
TARGETS = ["KRAS_G12C", "BCR_ABL1"]  # pre-registered -- see task file, not PTP1B (TASK-0203 overlap)


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _load_apo_holo(target_name: str, target_config: dict):
    import prody

    apo = clean_from_config(target_name, role="apo")
    holo = clean_from_config(target_name, role="holo")

    prody.confProDy(verbosity="none")
    holo_id = target_config["holo_pdb"]
    chains = target_config.get("chains") or sorted(set(holo.chain_ids))
    chain_sel = " or ".join(f"chain {c}" for c in chains)
    holo_struct = prody.parsePDB(holo_id, compressed=False).select(chain_sel)
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)
    holo.heavy_atom_coords, holo.heavy_atom_seq_index = protein_heavy_atoms_by_residue(
        holo_struct, chains, holo.resnums
    )
    return apo, holo


def _select_window(apo, pocket_mask: np.ndarray, max_size: int = WINDOW_MAX_SIZE):
    """Pocket residues, capped at `max_size` by nearest-to-pocket-centroid
    -- PHASE_B_ROTAMER_QUBO.md's own m=8-15 window size. Returns a list of
    (chain, resnum) pairs on the apo structure's own numbering."""
    idx = np.where(pocket_mask)[0]
    if len(idx) > max_size:
        centroid = apo.coords[idx].mean(axis=0)
        d = np.linalg.norm(apo.coords[idx] - centroid, axis=1)
        idx = idx[np.argsort(d)[:max_size]]
    chain_ids = np.asarray(apo.chain_ids)
    return [(str(chain_ids[i]), int(apo.resnums[i])) for i in idx]


def _write_full_atom_with_window_chain(target_config: dict, apo_chains, window: list, out_path: Path) -> str:
    """Full-atom apo structure (same altloc/protein/chain filtering as
    `task0163_external_baseline_scoring.py::_write_full_atom_apo_pdb`),
    with `window` residues relabeled to chain 'B' (everything else kept on
    its own original chain) so EvoEF2's `--design_chains=B` restricts
    repacking to exactly the window -- EvoEF2 has no residue-list flag,
    only chain-level selection (checked directly against its own `-h`
    output before choosing this approach). Returns the window's own new
    chain letter ('B') for the caller's `--design_chains`/overlap-checking
    convenience.

    Atoms are written with each chain letter as a single contiguous block
    (all of 'A' together, then all of 'B' together), not interleaved in
    residue-number order. EvoEF2's own PDB chain-parser (`src/Main.cpp`
    `StructureConfig`) mishandles a chain letter that reappears after being
    interrupted by another letter (A-B-A in file order): confirmed by direct
    test that an interleaved A(1-54)/B(55-67)/A(68-169) file gets chain 'B'
    silently expanded to cover 55-169 (merging the second A run into it),
    even though `--design_chains=B` is otherwise parsed correctly (the
    "were selected for design by default" message is a pre-existing
    upstream mislabel -- it actually fires when the CLI value *was* used,
    not when it wasn't). Reordering into contiguous per-letter blocks with a
    `TER` between them sidesteps the bug regardless of its exact cause.
    """
    import prody

    prody.confProDy(verbosity="none")
    struct = prody.parsePDB(target_config["apo_pdb"], compressed=False)
    alt_locs = struct.getAltlocs()
    if alt_locs is not None and any(a not in ("", " ", "\x00") for a in alt_locs):
        struct = struct.select("altloc _ A") or struct
    chain_part = " and (" + " or ".join(f"chain {c}" for c in apo_chains) + ")"
    struct_clean = struct.select(f"protein{chain_part}").copy()

    window_set = set(window)
    chids = struct_clean.getChids()
    resnums = struct_clean.getResnums()
    new_chids = chids.copy()
    for i in range(len(new_chids)):
        if (chids[i], int(resnums[i])) in window_set:
            new_chids[i] = "B"
    struct_clean.setChids(new_chids)

    import numpy as np

    is_window = new_chids == "B"
    other_idx = np.where(~is_window)[0]
    window_idx = np.where(is_window)[0]
    reordered = struct_clean[other_idx] + struct_clean[window_idx]
    prody.writePDB(str(out_path), reordered)
    return "B"


def _run_evoef2(command: str, pdb_path: Path, design_chains: str) -> Path | dict:
    """Runs the vendored EvoEF2 (must be invoked with cwd=EVOEF2_DIR, see
    that directory's own README) and returns the path to
    `<pdbid>_beststruct.pdb`, or an error dict."""
    if not EVOEF2_BIN.exists():
        return {"error": f"EvoEF2 binary not found at {EVOEF2_BIN} -- see tools/evoef2/README.md to build it"}
    local_pdb = EVOEF2_DIR / pdb_path.name
    local_pdb.write_bytes(pdb_path.read_bytes())
    pdbid = pdb_path.stem
    # Default backbone-dependent library (dun2010bb3per, no --bbdep/--rotlib
    # override). An earlier attempt at a scattered (non-sequence-contiguous)
    # window crashed under the default library and was worked around with
    # --bbdep=disable --rotlib=honig984 (backbone-independent) -- but that
    # combination itself turned out to SIGSEGV on real pocket windows
    # (DataNotExistError "cannot find atom parameters of <resn>" for
    # ordinary residue types genuinely present in library/param_charmm19_lk
    # .prm, e.g. MET/TYR/ILE), a pre-existing bug in this EvoEF2 build's own
    # BBindRotamerLibCreate/honig984.lib combination -- confirmed by
    # comparing both arms directly, not assumed. Re-tested after fixing the
    # actual root cause of the original crash (the chain-interleaving bug in
    # `_write_full_atom_with_window_chain`, above): the default
    # backbone-dependent library runs cleanly (exit 0) on a real,
    # non-contiguous pocket window once the window is correctly isolated --
    # the original "0 rotamers"/crash finding was an artifact of the
    # malformed A-B-A input file, not a genuine phi/psi-continuity
    # limitation of the backbone-dependent library.
    #
    # argv[0] must be a RELATIVE path ("./EvoEF2"), not the resolved
    # absolute path -- confirmed directly: the identical binary/PDB/flags
    # SIGSEGV every time when invoked with an absolute argv[0] (5/5) and
    # succeed every time with "./EvoEF2" (5/5), including under the exact
    # same subprocess.run(cwd=..., ...) call shape used here. EvoEF2's own
    # PROGRAM_PATH handling (Main.cpp's ExtractPathAndName -> sprintf into a
    # fixed-size char[]) is the prime suspect -- a longer absolute path
    # plausibly overflows adjacent state, which is consistent with the
    # earlier "cannot find atom parameters" errors naming ordinary residues
    # that ARE present in the parameter file. Not fixed at the source (out
    # of this task's scope); worked around here since cwd is already
    # EVOEF2_DIR.
    result = subprocess.run(
        [f"./{EVOEF2_BIN.name}", f"--command={command}", f"--pdb={local_pdb.name}",
         f"--design_chains={design_chains}"],
        cwd=EVOEF2_DIR, capture_output=True, text=True, timeout=120,
    )
    out_path = EVOEF2_DIR / f"{pdbid}_beststruct.pdb"
    if result.returncode != 0 or not out_path.exists():
        return {"error": f"EvoEF2 {command} exited {result.returncode}: {result.stderr.strip()[:800] or result.stdout.strip()[-800:]}"}
    return out_path


def _pockets_overlap_frac(pockets: list, target_set: set) -> float:
    if not target_set or not pockets:
        return 0.0
    best = 0.0
    for p in pockets:
        frac = len(p["residues"] & target_set) / len(target_set)
        best = max(best, frac)
    return best


def _best_druggability_at_window(pockets: list, target_set: set) -> tuple:
    """Returns (overlap_frac, druggability_score) of the pocket with the
    HIGHEST residue-overlap against the window -- criterion #3's own
    "real druggability, not a geometric proxy" pairing (the overlap check
    identifies WHICH pocket is "the window's own"; its druggability_score,
    not just any pocket's, is what's reported)."""
    if not target_set or not pockets:
        return 0.0, None
    best_p, best_frac = None, -1.0
    for p in pockets:
        frac = len(p["residues"] & target_set) / len(target_set)
        if frac > best_frac:
            best_frac, best_p = frac, p
    return best_frac, (best_p["druggability_score"] if best_p else None)


def _is_hit(overlap_frac: float, druggability) -> bool:
    return bool(overlap_frac >= POCKET_HIT_OVERLAP and druggability is not None and druggability >= DRUGGABILITY_BAR)


def criterion_1_verdict(opt_rate, greedy_hit) -> str:
    """Three-state criterion-#1 verdict for one target.

    **Fixes a real, decisive defect in the 2026-08-06 run** (TASK-0204
    reopened 2026-08-06 by the Reviewer thread). That run's gate was::

        opt_rate > (1.0 if greedy_hit else 0.0)

    `opt_rate` is a fraction of N trials, so its maximum attainable value
    is exactly 1.0. On any target where greedy hits, the gate therefore
    demanded a value that cannot exist -- **it could not return `pass` for
    any data whatsoever**, including a perfect 8/8 optimized sweep. The
    pre-registered bar required 2 of 2 targets, and BCR_ABL1's greedy did
    hit, so criterion #1 was unfalsifiable-in-the-positive-direction for
    the run as a whole before a single trial was scored.

    The original *intent* was sound -- optimization must add something over
    the naive baseline, and a ceiling case must not be read as an automatic
    pass. The error was scoring that case as a **fail** and counting it
    toward a "both targets must pass" bar. A target where the naive
    baseline already succeeds says nothing about whether optimization helps
    where it is actually needed, so it is `not_evaluable`, and the
    denominator must shrink accordingly rather than the numerator being
    charged a loss it could never have avoided.
    """
    if opt_rate is None or greedy_hit is None:
        return "not_evaluable_no_data"
    if greedy_hit:
        return "not_evaluable_greedy_ceiling"
    return "pass" if opt_rate > 0.0 else "fail"


def score_structure(pdb_path: Path, target_set: set, work_dir: Path) -> dict:
    # fpocket writes its "<stem>_out/" output directory next to the INPUT
    # pdb file, not relative to cwd -- confirmed directly (ran it by hand
    # against a file in /tmp with a different cwd, and the output landed
    # beside the input). `_run_fpocket` (task0163_external_baseline_scoring
    # .py) looks for that output under `work_dir`, so `pdb_path` must
    # actually live in `work_dir` -- true for the native sanity check
    # (already written into `work_dir`) but not for EvoEF2's own output
    # (lives in EVOEF2_DIR). Copy it in first so both agree.
    if pdb_path.parent != work_dir:
        local_copy = work_dir / pdb_path.name
        local_copy.write_bytes(pdb_path.read_bytes())
        pdb_path = local_copy
    pockets = _run_fpocket(pdb_path, work_dir)
    if isinstance(pockets, dict) and "error" in pockets:
        return {"error": pockets["error"]}
    overlap, drug = _best_druggability_at_window(pockets, target_set)
    return {"overlap_frac": overlap, "druggability_score": drug, "hit": _is_hit(overlap, drug), "n_pockets": len(pockets)}


def run_target(name: str) -> dict:
    t0 = time.monotonic()
    _log(f"{name}: loading target + building pocket label...")
    target_config = load_target_config(name)
    apo, holo = _load_apo_holo(name, target_config)
    pocket_cutoff = float(target_config.get("pocket_contact_cutoff", 4.5))
    labels_obj = build_labels(apo, holo, target_config, cutoff=pocket_cutoff)
    if labels_obj.pocket is None or not labels_obj.pocket.any():
        return {"target": name, "error": "no resolvable pocket label"}

    window = _select_window(apo, labels_obj.pocket)
    _log(f"{name}: window = {len(window)} residues: {window}")

    apo_chains = target_config.get("apo_chains") or target_config.get("chains")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        base_pdb = tmp / f"{name.lower()}_window.pdb"
        design_chain = _write_full_atom_with_window_chain(target_config, apo_chains, window, base_pdb)
        target_set = {(design_chain, r) for (_c, r) in window}

        # --- Sanity check: native structure, does fpocket recover the known cavity at the window? ---
        _log(f"{name}: sanity check -- native structure vs. fpocket...")
        native_score = score_structure(base_pdb, target_set, tmp)
        _log(f"{name}: native sanity: {native_score}")

        result = {
            "target": name, "window": window, "design_chain": design_chain,
            "native_sanity": native_score,
        }

        # --- Greedy: single deterministic trial ---
        _log(f"{name}: GreedyRepack (1 deterministic trial)...")
        greedy_out = _run_evoef2("GreedyRepack", base_pdb, design_chain)
        if isinstance(greedy_out, dict):
            result["greedy"] = {"error": greedy_out["error"]}
        else:
            result["greedy"] = score_structure(greedy_out, target_set, tmp)
        _log(f"{name}: greedy: {result['greedy']}")

        # --- Optimized: N_TRIALS seeded SA trials ---
        optimized_trials = []
        for i in range(N_TRIALS):
            time.sleep(1.05)  # EvoEF2 seeds via time(NULL), second-resolution -- force distinct seeds
            out = _run_evoef2("SideChainRepack", base_pdb, design_chain)
            if isinstance(out, dict):
                optimized_trials.append({"error": out["error"]})
            else:
                optimized_trials.append(score_structure(out, target_set, tmp))
            _log(f"{name}: optimized trial {i+1}/{N_TRIALS}: {optimized_trials[-1]}")
        result["optimized_trials"] = optimized_trials

        # --- Random: N_TRIALS seeded negative-control trials ---
        random_trials = []
        for i in range(N_TRIALS):
            time.sleep(1.05)
            out = _run_evoef2("RandomRepack", base_pdb, design_chain)
            if isinstance(out, dict):
                random_trials.append({"error": out["error"]})
            else:
                random_trials.append(score_structure(out, target_set, tmp))
            _log(f"{name}: random trial {i+1}/{N_TRIALS}: {random_trials[-1]}")
        result["random_trials"] = random_trials

    def _hit_rate(trials):
        valid = [t for t in trials if "error" not in t]
        if not valid:
            return None, 0
        return sum(t["hit"] for t in valid) / len(valid), len(valid)

    opt_rate, opt_n = _hit_rate(result["optimized_trials"])
    rand_rate, rand_n = _hit_rate(result["random_trials"])
    greedy_hit = result["greedy"].get("hit") if "error" not in result["greedy"] else None

    verdict = criterion_1_verdict(opt_rate, greedy_hit)
    result["summary"] = {
        "optimized_hit_rate": opt_rate, "optimized_n_valid": opt_n,
        "greedy_hit": greedy_hit,
        "random_hit_rate": rand_rate, "random_n_valid": rand_n,
        "criterion_1_verdict": verdict,
        # Kept for continuity with the 2026-08-06 run's own stored artifact.
        # NOTE: that run's value came from an unfalsifiable expression -- see
        # `criterion_1_verdict`'s docstring. `True` still means pass; `False`
        # now means "fail OR not evaluable", so read `criterion_1_verdict`.
        "criterion_1_passes_this_target": verdict == "pass",
    }
    result["elapsed_s"] = round(time.monotonic() - t0, 1)
    _log(f"{name}: SUMMARY {result['summary']}")
    return result


def main() -> int:
    out = {}
    for name in TARGETS:
        try:
            out[name] = run_target(name)
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            out[name] = {"target": name, "error": f"{type(exc).__name__}: {exc}"}

    out_dir = Path(__file__).resolve().parent.parent / "results_task0204_rotamer_repack_baseline"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nWrote {out_path}")

    print("\n=== TASK-0204 criterion #1 summary ===")
    n_pass = 0
    for name, r in out.items():
        if "error" in r:
            print(f"{name}: ERROR {r['error']}")
            continue
        s = r["summary"]
        passed = s["criterion_1_passes_this_target"]
        n_pass += int(passed)
        print(f"{name}: optimized_hit_rate={s['optimized_hit_rate']} greedy_hit={s['greedy_hit']} "
              f"random_hit_rate={s['random_hit_rate']} passes={passed}")
    print(f"\nCriterion #1 overall: {n_pass}/{len(TARGETS)} targets pass (bar: 2/2)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
