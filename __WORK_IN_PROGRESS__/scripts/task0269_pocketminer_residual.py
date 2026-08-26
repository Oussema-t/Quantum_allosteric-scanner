"""TASK-0269 -- unblock and run PocketMiner (Meller et al. 2023, Nat
Commun 14:2135, doi:10.1038/s41467-023-36699-3), the untested half of
[[TASK-0260]]: does the one purpose-built cryptic-*opening* predictor
close the ~27-29% residual [[TASK-0259]]/[[TASK-0260]] left unassigned?

**Environment**: PocketMiner needs Python 3.7-3.9 + TensorFlow<=2.9; this
repo's own toolchain (Python 3.13, TensorFlow 2.16) cannot run it and a
native pyenv 3.9 build fails to compile `_ssl` (CPython 3.9 predates
general OpenSSL 3.x support, Homebrew has removed openssl@1.1). Solved via
a Docker container, `tools/pocketminer/` (Dockerfile + `predict.py`,
`--platform linux/amd64` explicitly -- see that directory's own README for
the full recipe and why amd64 emulation was chosen over a native-arm64
attempt). This script shells out to `docker run` rather than embedding
inference in-process, since the model itself cannot load in this
process's own Python.

**Constraint-3 status, as of this run** (checked directly against
[[TASK-0221]] before running, not assumed): the organiser question this
task's own filing flagged (item (f) / re-sent as Q7, 2026-08-26) is
**STILL OPEN** as of this script's run. Proceeding under this register's
own provisional ruling (MD used only for the external authors' training
labels; our inference supplies zero trajectories -- legal under Constraint
3's literal reading, HYP-S7 precedent) -- any result below that depends on
this ruling must carry that caveat until an organiser answer arrives.

Reuses, does not re-derive: `task0249_composite_dumb_baseline.target_rows`
(apo/seed/label rows), `task0254_fpocket_variance_and_crypticity`'s
`cv_auc`/`z`/`build_blocks`/`crypticity`, `task0260_cryptic_predictor_
residual.shapley_attribution_4` (the already-generalised n-block Shapley
routine, explicitly not rewritten per this task's own Scope),
`task0261_cluster_robust_stats.cluster_sign_flip_test`/`CM` for
cluster-robust significance (this task's own explicit Scope requirement,
absent from TASK-0260's own P2Rank run).
"""
from __future__ import annotations

import itertools
import json
import subprocess
import sys
import tempfile
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import prody
import yaml

prody.confProDy(verbosity="none")

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import task0242_two_stage_dryrun as t0242  # noqa: E402
import task0249_composite_dumb_baseline as t0249  # noqa: E402
import task0254_fpocket_variance_and_crypticity as t0254  # noqa: E402
from task0260_cryptic_predictor_residual import shapley_attribution_4  # noqa: E402
from task0261_cluster_robust_stats import CM, cluster_sign_flip_test  # noqa: E402

OUT = _ROOT / "results/tasks/0269_pocketminer_residual"
FROZEN_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"
DOCKER_IMAGE = "qas-pocketminer:pocket_pred"
BLOCKS4 = ["geometry", "fpocket", "ctqw", "pocketminer"]


def export_apo_pdbs(data: dict, new_cand: dict, work: Path) -> dict:
    """One clean, protein-only, single-model PDB per target, mdtraj-
    parseable (PocketMiner's own `process_strucs` selects `protein and
    (name N or name CA or name C or name O)` -- a standard backbone-only
    read, no exotic requirements, but altloc/hetero records are exactly
    the class of thing that has broken naive `prody.parsePDB` calls
    elsewhere in this batch, TASK-0243's own NAMPT_NPA1R finding -- so
    `altloc='all'` is applied here too, matching that precedent)."""
    paths = {}
    for t, d in data.items():
        cfg = new_cand[t]
        apo_ch = cfg.get("apo_chains") or cfg.get("chains")
        ag = prody.parsePDB(cfg["apo_pdb"], compressed=False, altloc="all").select(
            "protein and (" + " or ".join(f"chain {c}" for c in apo_ch) + ")"
        )
        pdb_path = work / f"{t}.pdb"
        prody.writePDB(str(pdb_path), ag)
        paths[t] = pdb_path
    return paths


def run_pocketminer_docker(input_dir: Path, output_dir: Path, timeout: int = 1800) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "docker", "run", "--rm", "--platform", "linux/amd64",
        "-v", f"{input_dir}:/data/input:ro",
        "-v", f"{output_dir}:/data/output",
        DOCKER_IMAGE,
    ]
    print(f"$ {' '.join(cmd)}", flush=True)
    t0 = time.monotonic()
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    elapsed = time.monotonic() - t0
    print(r.stdout, flush=True)
    # predict.py's own exit code is 1 on ANY per-structure failure (a
    # summary signal, "not every target succeeded"), even though it
    # already wrote a real <stem>.error.txt for each failure and kept
    # going -- matching this task's own "one bad structure must not lose
    # the other 19" design (predict.py's own docstring). Only a genuine
    # crash (no output directory populated at all) is treated as fatal
    # here; a partial-success nonzero exit is expected and handled
    # downstream by `pocketminer_per_residue`'s own .error.txt check.
    if r.returncode != 0 and not any(output_dir.iterdir()):
        print(r.stderr[-4000:], flush=True)
        raise RuntimeError(f"docker run exited {r.returncode} after {elapsed:.0f}s with no output at all")
    if r.returncode != 0:
        print(f"docker run exited {r.returncode} (partial success -- see per-target .error.txt files) "
              f"after {elapsed:.0f}s", flush=True)
    else:
        print(f"docker run completed in {elapsed:.0f}s", flush=True)


def pocketminer_per_residue(t: str, output_dir: Path, resn: np.ndarray) -> np.ndarray | None:
    """PocketMiner's own predictions are already in the input PDB's own
    residue order (no resnum column in its output -- a positional array,
    one float per residue in read order) -- aligned to `resn` by position,
    not by a resnum lookup (unlike fpocket/p2rank's own per-residue
    helpers, which have an explicit resnum column to key on)."""
    txt_path = output_dir / f"{t}.txt"
    err_path = output_dir / f"{t}.error.txt"
    if err_path.exists():
        print(f"{t}: PocketMiner FAILED -- {err_path.read_text()[-300:]}")
        return None
    if not txt_path.exists():
        print(f"{t}: PocketMiner produced no output")
        return None
    arr = np.loadtxt(txt_path)
    if len(arr) != len(resn):
        print(f"{t}: WARNING length mismatch, PocketMiner={len(arr)} vs resn={len(resn)} -- skipped")
        return None
    return arr


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    new_cand = yaml.safe_load(FROZEN_CONFIG.read_text())["targets"]
    t0242.CAND = new_cand
    frozen_targets = list(new_cand.keys())

    data = {}
    for t in frozen_targets:
        try:
            d = t0249.target_rows(t)
        except Exception as exc:  # noqa: BLE001
            print(f"{t}: FAILED {exc!r}")
            continue
        if d is None or d["n_pocket"] < 3:
            print(f"{t}: SKIP (fpocket failure, empty seed, or too few positives)")
            continue
        data[t] = d
        print(f"{t}: n_pocket={d['n_pocket']} n_residues={len(d['y'])}")

    print(f"\n{len(data)}/{len(frozen_targets)} usable\n")

    print("### Exporting apo structures + running PocketMiner (Docker) ###")
    work = Path(tempfile.mkdtemp(prefix="task0269_"))
    in_dir, out_dir = work / "input", work / "output"
    in_dir.mkdir()
    paths = export_apo_pdbs(data, new_cand, in_dir)
    print(f"exported {len(paths)} structures to {in_dir}")
    run_pocketminer_docker(in_dir, out_dir)

    pm_scores = {}
    for t, d in data.items():
        arr = pocketminer_per_residue(t, out_dir, d["resn"])
        if arr is not None:
            pm_scores[t] = arr

    print(f"\n{len(pm_scores)}/{len(data)} targets scored by PocketMiner\n")

    print("### Four-block Shapley attribution (geometry / fpocket / CTQW / pocketminer) ###")
    attribution = {}
    crypt = {}
    for t in pm_scores:
        d = data[t]
        seed = d["seed"]
        m = np.ones(len(d["coords"]), dtype=bool)
        m[seed] = False
        blocks = t0254.build_blocks(t, d)
        blocks["pocketminer"] = t0254.z(pm_scores[t])[m].reshape(-1, 1)
        y = d["y"]
        result = shapley_attribution_4(blocks, y, BLOCKS4)
        # added-last: the decision statistic this task's own Scope names
        # explicitly, not just the averaged Shapley value.
        full_share = result["full_share"]
        without_pm = (t0254.cv_auc(np.column_stack(
            [blocks["geometry"], blocks["fpocket"], blocks["ctqw"]]), y) - 0.5) / 0.5
        result["added_last"] = full_share - without_pm
        attribution[t] = result
        crypt[t] = t0254.crypticity(d)
        sh = result["shapley"]
        print(f"{t:24s} geom={100*sh['geometry']:+5.1f}%  fpocket={100*sh['fpocket']:+5.1f}%  "
              f"ctqw={100*sh['ctqw']:+5.1f}%  pocketminer={100*sh['pocketminer']:+5.1f}%  "
              f"added_last={100*result['added_last']:+5.1f}%  "
              f"unexplained={100*result['unexplained']:5.1f}%  "
              f"crypticity={100*crypt[t]['fraction_open']:.0f}%")

    (OUT / "shapley_4block.json").write_text(json.dumps(attribution, indent=1))
    (OUT / "crypticity.json").write_text(json.dumps(crypt, indent=1))

    unexs4 = [a["unexplained"] for a in attribution.values()]
    pm_shap = [a["shapley"]["pocketminer"] for a in attribution.values()]
    added_last = {t: a["added_last"] for t, a in attribution.items()}
    print(f"\nn={len(attribution)}")
    print(f"  pocketminer Shapley share  {100*min(pm_shap):+.0f} to {100*max(pm_shap):+.0f}%  "
          f"(median {100*np.median(pm_shap):+.0f}%)")
    print(f"  pocketminer added-last     {100*min(added_last.values()):+.0f} to "
          f"{100*max(added_last.values()):+.0f}%  (median {100*np.median(list(added_last.values())):+.0f}%)")
    print(f"  unexplained (4-block)      {100*min(unexs4):.0f} to {100*max(unexs4):.0f}%  "
          f"(median {100*np.median(unexs4):.0f}%)")

    # cluster-robust significance on the added-last statistic
    added_last_cm = {t: v for t, v in added_last.items() if t in CM}
    cluster_result = cluster_sign_flip_test(added_last_cm)
    print(f"\nadded-last, cluster-robust: median={cluster_result['median']:+.4f}, "
          f"n_rows={cluster_result['n_rows']}, n_clusters={cluster_result['n_clusters']}, "
          f"p={cluster_result['p_value']:.4f}")
    (OUT / "added_last_cluster_robust.json").write_text(json.dumps(cluster_result, indent=1))

    already_open = [t for t in attribution if crypt[t]["already_open"]]
    cryptic = [t for t in attribution if crypt[t]["already_open"] is False]
    pm_open = {t: added_last[t] for t in already_open}
    pm_cryptic = {t: added_last[t] for t in cryptic}
    print(f"\nCrypticity-stratified pocketminer added-last:")
    print(f"  already-open (n={len(pm_open)}): median "
          f"{100*np.median(list(pm_open.values())) if pm_open else float('nan'):+.1f}%")
    print(f"  cryptic-testing (n={len(pm_cryptic)}): median "
          f"{100*np.median(list(pm_cryptic.values())) if pm_cryptic else float('nan'):+.1f}%")
    if len(set(pm_open) & set(CM)) >= 2 and len(set(pm_cryptic) & set(CM)) >= 2:
        from task0261_cluster_robust_stats import cluster_permutation_two_group
        try:
            strat_test = cluster_permutation_two_group(
                {t: v for t, v in pm_open.items() if t in CM},
                {t: v for t, v in pm_cryptic.items() if t in CM},
            )
            print(f"  cluster-robust already-open vs cryptic: p={strat_test['p_value']:.4f}")
            (OUT / "crypticity_stratified_cluster_robust.json").write_text(json.dumps(strat_test, indent=1))
        except AssertionError:
            # A real, substantive case, not a bug: crypticity is a
            # property of the (apo, ligand-specific holo pocket) PAIR, not
            # of the apo structure alone -- unlike TASK-0261's own ENM-
            # validity grouping (genuinely cluster-consistent, its own
            # module docstring states so directly), two ligand-variant
            # targets sharing one apo structure can land on opposite sides
            # of the 80% already-open bar. `cluster_permutation_two_group`
            # correctly refuses a cluster split across groups rather than
            # silently double-counting it -- reported as a finding (median
            # comparison above), not forced through a test whose own
            # cluster-integrity assumption this split genuinely violates.
            print("  cluster-robust already-open vs cryptic: SKIPPED -- at least one "
                  "cluster (shared-apo pair) has members on both sides of the crypticity "
                  "bar, violating cluster_permutation_two_group's own cluster-integrity "
                  "assumption. Median comparison above stands; no formal p-value for this split.")

    print(f"\nWrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
