"""TASK-0360 -- the detector-agreement cascade: fpocket vs PASSer vs
PocketMiner vs p2rank on the identical structure set, identical truth,
identical overlap rule.

[[TASK-0306]]/[[TASK-0304]] decomposed the field's own "84% recovery"
figure into a disjunction over six noisy statistical tests (99/118 by
>=1, 21/118 by all 6). Nobody has asked the same question of the pocket
DETECTORS this project and the `allosteric` branch actually use. This
script does, on the SAME cohort/truth/overlap rule for every detector,
per TASK-0360's own pre-registration (written before this script ran --
see the task file's own "Pre-registration" section for the full
reasoning, not repeated here).

STRUCTURE SET: the existing 108-structure ASBench KEEP-filtered cohort,
truth restricted to each structure's own PRIMARY CHAIN (majority of
active_residues) -- the common denominator every detector is scored
against, since PocketMiner has an established single-chain-input
convention ([[TASK-0329]]) the other detectors don't share on their own,
and TASK-0336's own lesson is exactly "mismatched candidate sets kill a
comparison." 8/108 structures have zero truth on their own primary chain
and are dropped from ALL arms, not just PocketMiner's.

HIT RULE, identical for every detector: a detector "detects" the site on
a structure if ANY of its own reported candidate pockets/regions overlaps
the (primary-chain) truth by >=1 residue -- coverage, not top-K
precision, matching TASK-0163/TASK-0304's own "recovered by >=1 of N"
framing. PocketMiner (no discrete pockets) uses its own top-10 residues
by predicted probability as the one disclosed adaptation.

Run: ../.venv/bin/python3 -u scripts/task0360_detector_agreement_cascade.py
"""
from __future__ import annotations

import csv
import itertools
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import requests

sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, "src")
sys.path.insert(0, "..")

from backend.data_layer import fetch, PDB_CACHE  # noqa: E402

OUT = Path("results/tasks/0360_detector_agreement_cascade")
CHECKPOINT_PATH = OUT / "checkpoint.jsonl"
ANN = json.load(open("results/tasks/0304_asbench_casbench/asbench_annotations.json"))
KEEP = {r["pdb"] for r in json.load(
    open("results/tasks/0305_asbench_detection/asbench_detection.json"))["rows"]}

FPOCKET_BIN = Path("tools/fpocket/bin/fpocket").resolve()
P2RANK_BIN = Path("tools/p2rank/p2rank_2.5.1/prank").resolve()
PASSER_CACHE_PATH = OUT / "passer_cache_snapshot.json"
POCKETMINER_IMAGE = "qas-pocketminer:pocket_pred"
POCKETMINER_TIME_BUDGET_S = 1800  # 30 minutes, per this task's own pre-registered Budget clause

AA3 = {"ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
       "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL", "MSE"}

_A = re.compile(r'^([A-Z]{2,3})\s*(-?\d+)([A-Za-z]?)\s+(\w)$')


def pa(t):
    """ASBench allosteric_residues token: 'RESNAME NUM CHAIN'."""
    m = _A.match(t.strip())
    if m:
        return (m.group(4), int(m.group(2)))
    m = re.match(r'^([A-Z]{2,3})(-?\d+)\s+(\w)$', t.strip())
    return (m.group(3), int(m.group(2))) if m else None


def pact(t):
    """ASBench active_residues token: 'CHAIN NUM'."""
    m = re.match(r'^(\w)(-?\d+)$', t.strip())
    return (m.group(1), int(m.group(2))) if m else None


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ------------------------------------------------------------- cohort + primary chain + truth
def build_cohort():
    structures = []
    n_dropped_no_primary_truth = 0
    for rec in ANN:
        if rec["pdb"] not in KEEP:
            continue
        pdb = rec["pdb"].split("_")[0]
        act = [x for x in (pact(t) for t in rec["active_residues"]) if x]
        allo = [x for x in (pa(t) for t in rec["allosteric_residues"]) if x]
        if not act or not allo:
            continue
        primary_chain = Counter(c for c, _ in act).most_common(1)[0][0]
        truth = {(c, n) for c, n in allo if c == primary_chain}
        if not truth:
            n_dropped_no_primary_truth += 1
            continue
        structures.append(dict(pdb=pdb, protein=rec.get("protein", pdb),
                                primary_chain=primary_chain, truth=truth))
    _log(f"cohort: {len(structures)}/{sum(1 for r in ANN if r['pdb'] in KEEP)} structures usable "
         f"({n_dropped_no_primary_truth} dropped: zero truth on primary chain)")
    return structures


# ------------------------------------------------------------- fpocket
def run_fpocket(pdb_path: Path, work: Path):
    r = subprocess.run([str(FPOCKET_BIN), "-f", str(pdb_path)],
                        cwd=work, capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        return None, f"exit {r.returncode}: {r.stderr.strip()[:300]}"
    out_dir = work / f"{pdb_path.stem}_out"
    info_file = out_dir / f"{pdb_path.stem}_info.txt"
    if not info_file.exists():
        return None, "no info file"
    blocks = re.split(r"^Pocket (\d+) :\s*$", info_file.read_text(), flags=re.MULTILINE)[1:]
    pockets = []
    for pid, body in zip(blocks[0::2], blocks[1::2]):
        pockets.append({"id": int(pid)})
    pockets_dir = out_dir / "pockets"
    for p in pockets:
        atm_file = pockets_dir / f"pocket{p['id']}_atm.pdb"
        residues = set()
        if atm_file.exists():
            for line in atm_file.read_text().splitlines():
                if line.startswith(("ATOM", "HETATM")):
                    try:
                        residues.add((line[21].strip(), int(line[22:26])))
                    except ValueError:
                        continue
        p["residues"] = residues
    return pockets, None


# ------------------------------------------------------------- p2rank
def run_p2rank(pdb_path: Path, work: Path):
    r = subprocess.run([str(P2RANK_BIN), "predict", "-f", str(pdb_path), "-o", str(work)],
                        capture_output=True, text=True, timeout=180)
    csv_path = work / f"{pdb_path.name}_predictions.csv"
    if r.returncode != 0 or not csv_path.exists():
        return None, f"exit {r.returncode}: {r.stderr.strip()[-300:]}"
    pockets = []
    with open(csv_path) as fh:
        for raw_row in csv.DictReader(fh, skipinitialspace=True):
            row = {k.strip(): v for k, v in raw_row.items()}
            residues = set()
            for tok in row["residue_ids"].split():
                if "_" not in tok:
                    continue
                ch, rn = tok.split("_", 1)
                try:
                    residues.add((ch, int(rn)))
                except ValueError:
                    continue
            pockets.append({"id": row["name"].strip(), "residues": residues})
    return pockets, None


# ------------------------------------------------------------- PASSer
_PASSER_SEG = re.compile(r'chain\s+(\S+)\s+and\s+resid\s+([\d.\s]+)')


def parse_passer_residues(sel: str) -> set:
    out = set()
    for chain, nums in _PASSER_SEG.findall(sel):
        for tok in nums.split():
            if re.fullmatch(r"-?\d+", tok):
                out.add((chain, int(tok)))
    return out


def passer_fetch_one(pdb: str, chain: str, timeout=180):
    d = {"pdb": pdb.lower(), "model": "ensemble", "top": "all", "chain": chain}
    for attempt in range(3):
        try:
            r = requests.post("https://passer.smu.edu/api", data=d, timeout=timeout)
            r.raise_for_status()
            return r.json(), None
        except Exception as e:
            if attempt == 2:
                return None, f"{type(e).__name__}: {e}"
            time.sleep(2 * (attempt + 1))


# ------------------------------------------------------------- PocketMiner
def export_pdb_for_pocketminer(pdb: str, chain: str, out_path: Path) -> bool:
    fp = fetch(pdb)
    lines = []
    seen_model = False
    with open(fp) as fh:
        for line in fh:
            if line.startswith("MODEL"):
                if seen_model:
                    break
                seen_model = True
                continue
            if not line.startswith("ATOM"):
                continue
            if line[21] != chain or line[16] not in (" ", "A"):
                continue
            lines.append(line)
    if len(lines) < 10:
        return False
    lines.append("END\n")
    out_path.write_text("".join(lines))
    return True


def run_pocketminer_docker(input_dir: Path, output_dir: Path, timeout=3600):
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["docker", "run", "--rm", "--platform", "linux/amd64",
           "-v", f"{input_dir.resolve()}:/data/input:ro",
           "-v", f"{output_dir.resolve()}:/data/output",
           POCKETMINER_IMAGE]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout[-2000:], r.stderr[-2000:]


def save_pockets_cache(path: Path, pockets_by_pdb: dict, err_by_pdb: dict) -> None:
    """Per-detector raw pocket data, persisted so a re-run (e.g. after
    fixing a downstream parsing bug in one OTHER detector, as happened
    with PocketMiner's own output-format mismatch here) never re-pays an
    already-successful, expensive Docker pass -- direct application of
    this register's own standing 'never pay the same expensive derivation
    twice' rule."""
    out = {"pockets": {pdb: [{"id": p["id"], "residues": sorted(list(r) for r in p["residues"])}
                              for p in pockets] for pdb, pockets in pockets_by_pdb.items()},
           "errors": err_by_pdb}
    path.write_text(json.dumps(out))


def load_pockets_cache(path: Path):
    if not path.exists():
        return None, None
    d = json.loads(path.read_text())
    pockets_by_pdb = {pdb: [{"id": p["id"], "residues": {tuple(r) for r in p["residues"]}}
                             for p in pockets] for pdb, pockets in d["pockets"].items()}
    return pockets_by_pdb, d["errors"]


def hit(pockets, truth: set) -> bool:
    return any(bool(p["residues"] & truth) for p in pockets)


def jaccard(a: set, b: set) -> float:
    u = a | b
    return len(a & b) / len(u) if u else 1.0


def main() -> int:
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)

    structures = build_cohort()

    # ============================================================ fpocket
    fpocket_cache = OUT / "fpocket_pockets_cache.json"
    fpocket_pockets, fpocket_err = load_pockets_cache(fpocket_cache)
    if fpocket_pockets is not None:
        _log(f"### fpocket: loaded {len(fpocket_pockets)} from cache, not re-run ###")
    else:
        _log("### fpocket ###")
        fpocket_pockets, fpocket_err = {}, {}
        for i, s in enumerate(structures):
            try:
                fp = fetch(s["pdb"])
            except Exception as e:
                fpocket_err[s["pdb"]] = f"fetch: {e}"
                continue
            tmp = Path(tempfile.mkdtemp())
            try:
                local = tmp / f"{s['pdb']}.pdb"
                shutil.copy(fp, local)
                pockets, err = run_fpocket(local, tmp)
                if pockets is not None:
                    fpocket_pockets[s["pdb"]] = pockets
                else:
                    fpocket_err[s["pdb"]] = err
            except Exception as e:
                fpocket_err[s["pdb"]] = f"{type(e).__name__}: {e}"
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
            if (i + 1) % 10 == 0:
                _log(f"  fpocket: {i+1}/{len(structures)}  ({time.time()-t0:.0f}s)  "
                     f"ok={len(fpocket_pockets)} err={len(fpocket_err)}")
        save_pockets_cache(fpocket_cache, fpocket_pockets, fpocket_err)
    _log(f"fpocket coverage: {len(fpocket_pockets)}/{len(structures)} ({time.time()-t0:.0f}s)")

    # ============================================================ p2rank
    p2rank_cache = OUT / "p2rank_pockets_cache.json"
    p2rank_pockets, p2rank_err = load_pockets_cache(p2rank_cache)
    if p2rank_pockets is not None:
        _log(f"### p2rank: loaded {len(p2rank_pockets)} from cache, not re-run ###")
    else:
        _log("### p2rank ###")
        p2rank_pockets, p2rank_err = {}, {}
        for i, s in enumerate(structures):
            try:
                fp = fetch(s["pdb"])
            except Exception as e:
                p2rank_err[s["pdb"]] = f"fetch: {e}"
                continue
            tmp = Path(tempfile.mkdtemp())
            try:
                local = tmp / f"{s['pdb']}.pdb"
                shutil.copy(fp, local)
                pockets, err = run_p2rank(local, tmp / "out")
                if pockets is not None:
                    p2rank_pockets[s["pdb"]] = pockets
                else:
                    p2rank_err[s["pdb"]] = err
            except Exception as e:
                p2rank_err[s["pdb"]] = f"{type(e).__name__}: {e}"
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
            if (i + 1) % 10 == 0:
                _log(f"  p2rank: {i+1}/{len(structures)}  ({time.time()-t0:.0f}s)  "
                     f"ok={len(p2rank_pockets)} err={len(p2rank_err)}")
        save_pockets_cache(p2rank_cache, p2rank_pockets, p2rank_err)
    _log(f"p2rank coverage: {len(p2rank_pockets)}/{len(structures)} ({time.time()-t0:.0f}s)")

    # ============================================================ PASSer
    _log("### PASSer: cache + live fetch for the rest ###")
    cache_text = subprocess.run(
        ["git", "show", "origin/allosteric:allosteric/datasets/passer_cache.json"],
        capture_output=True, text=True, cwd="..",
    )
    passer_cache = json.loads(cache_text.stdout) if cache_text.returncode == 0 else {}
    _log(f"  allosteric branch cache: {len(passer_cache)} entries")
    PASSER_CACHE_PATH.write_text(json.dumps(passer_cache))

    passer_live_cache_path = OUT / "passer_live_fetch_cache.json"
    passer_live_cache = json.loads(passer_live_cache_path.read_text()) if passer_live_cache_path.exists() else {}

    passer_raw, passer_err = {}, {}
    todo = []
    for s in structures:
        key = f"{s['pdb'].lower()}|{s['primary_chain']}|ensemble"
        if key in passer_cache:
            passer_raw[s["pdb"]] = passer_cache[key]
        elif s["pdb"] in passer_live_cache:
            passer_raw[s["pdb"]] = passer_live_cache[s["pdb"]]
        else:
            todo.append(s)
    _log(f"  {len(passer_raw)}/{len(structures)} from cache (branch + this task's own prior live "
         f"fetch, never pay the same expensive derivation twice), {len(todo)} to fetch live")

    from concurrent.futures import ThreadPoolExecutor
    n_done = [0]

    def _fetch(s):
        r, err = passer_fetch_one(s["pdb"], s["primary_chain"])
        n_done[0] += 1
        if n_done[0] % 10 == 0:
            _log(f"  PASSer live: {n_done[0]}/{len(todo)}  ({time.time()-t0:.0f}s)")
        return s["pdb"], r, err

    if todo:
        with ThreadPoolExecutor(4) as ex:
            for pdb, r, err in ex.map(_fetch, todo):
                if r is not None:
                    passer_raw[pdb] = r
                    passer_live_cache[pdb] = r
                else:
                    passer_err[pdb] = err
        passer_live_cache_path.write_text(json.dumps(passer_live_cache))
    _log(f"PASSer coverage: {len(passer_raw)}/{len(structures)} ({time.time()-t0:.0f}s)")

    passer_pockets = {}
    for pdb, raw in passer_raw.items():
        if not isinstance(raw, dict):
            # a live PASSer response occasionally comes back as something
            # other than the {pocket_id: {prob, residues}} shape the cache
            # entries all have (e.g. a plain status/error string on a
            # structure it can't process) -- treated as zero pockets found
            # (a real, disclosed coverage gap for that structure), not a
            # crash, per this task's own "any detector that cannot be run
            # on a structure drops it" convention.
            passer_err[pdb] = f"unexpected response shape: {type(raw).__name__}"
            continue
        pockets = []
        for pid, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            residues = parse_passer_residues(entry.get("residues", ""))
            pockets.append({"id": pid, "residues": residues})
        passer_pockets[pdb] = pockets

    # ============================================================ PocketMiner (time-boxed)
    _log("### PocketMiner: single-structure timing check first ###")
    pm_dir = OUT / "pocketminer_io"
    pm_in, pm_out = pm_dir / "input", pm_dir / "output"
    pm_in.mkdir(parents=True, exist_ok=True)
    exported = {}
    for s in structures:
        p = pm_in / f"{s['pdb']}_{s['primary_chain']}.pdb"
        if export_pdb_for_pocketminer(s["pdb"], s["primary_chain"], p):
            exported[s["pdb"]] = p
    _log(f"  exported {len(exported)}/{len(structures)} primary-chain PDBs for PocketMiner")

    pocketminer_scores, pocketminer_err = {}, {}
    pocketminer_skipped_on_cost = False
    already_run = pm_out.exists() and all(
        (pm_out / f"{p.stem}.txt").exists() or (pm_out / f"{p.stem}.error.txt").exists()
        for p in exported.values())
    def _collect_pocketminer_output():
        """Shared by both the already-run and freshly-run paths -- reading
        `pm_out` is the SAME step either way, and only living in the
        freshly-run branch (an earlier version of this script) silently
        left `pocketminer_scores` empty whenever the skip-docker path was
        taken, reporting 0/100 coverage for a run that had actually
        succeeded. Caught by not accepting a same-input 0-after-a-known-
        fix result at face value."""
        for pdb, path in exported.items():
            err_path = pm_out / f"{path.stem}.error.txt"
            pred_path = pm_out / f"{path.stem}.txt"
            if err_path.exists():
                pocketminer_err[pdb] = err_path.read_text().strip().splitlines()[-1][:200]
            elif pred_path.exists():
                pocketminer_scores[pdb] = np.array(
                    [float(x) for x in pred_path.read_text().split()])
            else:
                pocketminer_err[pdb] = "no prediction file"

    if already_run:
        _log(f"  PocketMiner output already present for all {len(exported)} exported structures "
             "-- not re-invoking docker (never pay the same expensive derivation twice)")
        _collect_pocketminer_output()
    elif exported:
        # single-structure timing probe: run docker on ONE input first, isolated
        probe_dir = OUT / "pocketminer_probe"
        probe_in, probe_out = probe_dir / "input", probe_dir / "output"
        probe_in.mkdir(parents=True, exist_ok=True)
        first_pdb, first_path = next(iter(exported.items()))
        shutil.copy(first_path, probe_in / first_path.name)
        t_probe = time.time()
        try:
            rc, out, err = run_pocketminer_docker(probe_in, probe_out, timeout=300)
            probe_elapsed = time.time() - t_probe
            _log(f"  probe: rc={rc} elapsed={probe_elapsed:.0f}s")
            projected_total = probe_elapsed * len(exported)
            _log(f"  projected total for {len(exported)} structures: {projected_total:.0f}s "
                 f"(budget {POCKETMINER_TIME_BUDGET_S}s)")
            if projected_total > POCKETMINER_TIME_BUDGET_S:
                pocketminer_skipped_on_cost = True
                _log(f"  SKIPPING PocketMiner: projected {projected_total:.0f}s exceeds "
                     f"the {POCKETMINER_TIME_BUDGET_S}s pre-registered budget")
            else:
                _log("  within budget -- running PocketMiner on the full exported set")
                rc2, out2, err2 = run_pocketminer_docker(pm_in, pm_out,
                                                          timeout=int(projected_total * 1.5 + 300))
                _log(f"  full run: rc={rc2} elapsed={time.time()-t_probe:.0f}s")
                # output format: one float (predicted opening probability) per residue per
                # line in `<stem>.txt`, or `<stem>.error.txt` -- the image's own actual
                # output (verified directly against a real run's own output tree, not
                # assumed from a different call site's docstring, which named a
                # `-preds.npy` path this image does not produce)
                _collect_pocketminer_output()
        except subprocess.TimeoutExpired:
            pocketminer_skipped_on_cost = True
            _log("  SKIPPING PocketMiner: probe run itself timed out")
        except Exception as e:
            pocketminer_skipped_on_cost = True
            _log(f"  SKIPPING PocketMiner: {type(e).__name__}: {e}")

    # map PocketMiner scores -> top-10 residue "pockets"
    pocketminer_pockets = {}
    for s in structures:
        pdb = s["pdb"]
        if pdb not in pocketminer_scores:
            continue
        path = exported.get(pdb)
        if path is None:
            continue
        resns, seen = [], set()
        for line in path.read_text().splitlines():
            if line.startswith("ATOM") and line[12:16].strip() == "CA":
                try:
                    rn = int(line[22:26])
                except ValueError:
                    continue
                if rn not in seen:
                    seen.add(rn)
                    resns.append(rn)
        scores = pocketminer_scores[pdb]
        if len(scores) != len(resns):
            pocketminer_err[pdb] = f"length mismatch: {len(scores)} preds vs {len(resns)} residues"
            continue
        top10 = set(np.array(resns)[np.argsort(-scores)[:10]].tolist())
        pocketminer_pockets[pdb] = [{"id": "top10",
                                      "residues": {(s["primary_chain"], rn) for rn in top10}}]
    _log(f"PocketMiner coverage: {len(pocketminer_pockets)}/{len(structures)} "
         f"({'skipped on cost' if pocketminer_skipped_on_cost else 'ran'})")

    # ============================================================ score + cascade
    _log("### scoring ###")
    detectors = {"fpocket": fpocket_pockets, "passer": passer_pockets, "p2rank": p2rank_pockets}
    if pocketminer_pockets:
        detectors["pocketminer"] = pocketminer_pockets

    coverage = {name: len(d) for name, d in detectors.items()}
    _log(f"coverage: {coverage}")

    matched = [s for s in structures if all(s["pdb"] in d for d in detectors.values())]
    _log(f"matched-coverage cohort (all {len(detectors)} detectors ran): {len(matched)}/{len(structures)}")

    hits = {name: {} for name in detectors}
    for s in matched:
        pdb = s["pdb"]
        for name, d in detectors.items():
            hits[name][pdb] = hit(d[pdb], s["truth"])

    n = len(matched)
    per_structure_hits = {s["pdb"]: sum(hits[name][s["pdb"]] for name in detectors) for s in matched}
    cascade = {}
    for k in range(1, len(detectors) + 1):
        c = sum(1 for v in per_structure_hits.values() if v >= k)
        cascade[f">={k}"] = dict(n=c, frac=c / n if n else 0.0)
    all_n = sum(1 for v in per_structure_hits.values() if v == len(detectors))
    exactly_one = sum(1 for v in per_structure_hits.values() if v == 1)

    _log("\n### Cascade (matched-coverage cohort, n=%d) ###" % n)
    for k, v in cascade.items():
        _log(f"  detected by {k} of {len(detectors)}: {v['n']}/{n} = {v['frac']:.1%}")
    _log(f"  exactly one detector fires: {exactly_one}/{n} = {exactly_one/n:.1%}" if n else "  n=0")

    names = sorted(detectors)
    pairwise = {}
    for a, b in itertools.combinations(names, 2):
        sa = {pdb for pdb, v in hits[a].items() if v}
        sb = {pdb for pdb, v in hits[b].items() if v}
        pairwise[f"{a}_vs_{b}"] = dict(jaccard=jaccard(sa, sb), n_a=len(sa), n_b=len(sb), n_both=len(sa & sb))
        _log(f"  pairwise {a} vs {b}: hit-set Jaccard={pairwise[f'{a}_vs_{b}']['jaccard']:.3f} "
             f"({a}={len(sa)}, {b}={len(sb)}, both={len(sa&sb)})")

    per_detector_hit_rate = {name: dict(n_hit=sum(hits[name].values()), n=n,
                                         rate=sum(hits[name].values()) / n if n else 0.0)
                              for name in detectors}
    for name, r in per_detector_hit_rate.items():
        _log(f"  {name} own hit rate (matched cohort): {r['n_hit']}/{n} = {r['rate']:.1%}")

    out = dict(
        n_cohort=len(structures),
        coverage=coverage,
        n_matched=n,
        cascade=cascade,
        exactly_one=dict(n=exactly_one, frac=exactly_one / n if n else 0.0),
        pairwise=pairwise,
        per_detector_hit_rate=per_detector_hit_rate,
        pocketminer_skipped_on_cost=pocketminer_skipped_on_cost,
        errors=dict(fpocket=fpocket_err, p2rank=p2rank_err, passer=passer_err, pocketminer=pocketminer_err),
    )
    (OUT / "detector_agreement_result.json").write_text(json.dumps(out, indent=1, default=str))
    with open(CHECKPOINT_PATH, "w") as f:
        f.write(json.dumps(out, default=str) + "\n")
    _log(f"\nWrote {OUT}/detector_agreement_result.json ({time.time()-t0:.0f}s total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
