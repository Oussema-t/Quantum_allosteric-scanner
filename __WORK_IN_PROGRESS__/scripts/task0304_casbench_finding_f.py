"""TASK-0304 -- does [[TASK-0288]] Finding F generalise on CASBench too?

`task0304_asbench_finding_f.py` already showed Finding F (allosteric and
active sites sit at covalent/contact-adjacent distance far more often than
"distal" implies) reproduces on ASBench (113 structures, 22.2% below 1.5 A).
This script runs the identical distance computation on CASBench, using
CASBench's OWN annotations (`casbench_annotations.json`,
`task0304_casbench_annotations.py`) -- not ours, per this task's own
Constraint.

**Protein-level, not structure-level** -- the standing rule this whole
window is built around. CASBench's 314-structure cohort is 33 proteins
(9.5 structures/protein); reporting a structure-level percentage would
repeat [[TASK-0261]]'s own pseudo-replication at ~10x the scale that
already destroyed four selection procedures in this register. Reported
BOTH ways, structure-level clearly labelled as descriptive only, protein-
level (one row per `cas_id`, the median of its own structures) as the
number that counts.

METHOD, identical to the ASBench version: minimum heavy-atom distance
between the annotated allosteric-site residue set and the annotated
catalytic (active) site residue set, on the deposited coordinates. No
fpocket, no active-site detection, no CTQW -- the distance definition
alone is under test, restricted to the 314-PDB / 33-protein subset that
matches Wu et al. (2022)'s own CASBench evaluation cohort (not all 2871
structures CASBench itself hosts).

RESUMABLE, deliberately, not for speed: this machine ran under severe
concurrent load while this task was worked (a second Claude Code session
running TASK-0302's own heavy compute at the same time; load average
>13, swap >80% full). Two earlier full-cohort attempts died partway
through with no output at all -- one from an unbounded `urllib.request.
urlretrieve` call in `backend.data_layer.fetch` (fixed below, see
`fetch()`'s own docstring) and one from the machine's own resource
exhaustion, independent of this script's memory footprint (confirmed:
RSS stayed under 1.2 GB throughout, never near the danger threshold, and
still died). Progress is checkpointed to `casbench_finding_f_checkpoint.
json` after every small batch (default 15 structures) so a kill loses at
most one batch, not five minutes of network fetches.

Run: ../.venv/bin/python3 scripts/task0304_casbench_finding_f.py [batch_size]
"""
import sys, os, json, re, warnings
from pathlib import Path
from collections import defaultdict
import numpy as np
import requests
warnings.filterwarnings("ignore")
sys.path.insert(0, 'src'); sys.path.insert(0, '..')
from backend.data_layer import PDB_CACHE

# `backend.data_layer.fetch` uses bare `urllib.request.urlretrieve` with NO
# timeout -- confirmed the hard way: a run of this script hung indefinitely
# (uninterruptible-sleep, not a memory issue -- RSS stayed low and stable)
# on the first not-yet-cached PDB it hit. A slow/unresponsive RCSB
# connection blocks forever with no way to recover. Not fixed in
# `backend/` itself (shared, live-deployed module, other structures fetch
# fine, and another session was concurrently active on this machine) --
# worked around locally with a bounded-timeout `requests` fetch into the
# SAME cache directory.
def fetch(pdb, timeout=20):
    fp = os.path.join(PDB_CACHE, f"{pdb}.pdb")
    if os.path.exists(fp):
        return fp
    r = requests.get(f"https://files.rcsb.org/download/{pdb}.pdb", timeout=timeout)
    r.raise_for_status()
    with open(fp, "w") as fh:
        fh.write(r.text)
    return fp


MAX_FILE_MB = 20  # see heavy_atoms()'s own docstring for why

OUT = Path("results/tasks/0304_asbench_casbench")
CKPT = OUT / "casbench_finding_f_checkpoint.json"
ANN = json.load(open(OUT / "casbench_annotations.json"))
COHORT = json.load(open(OUT / "cohort_pdb_ids.json"))

_TOK = re.compile(r'^([A-Z]{3})(-?\d+)\s+(\w)$')


def parse_tok(tok):
    m = _TOK.match(tok.strip())
    return (m.group(3), int(m.group(2))) if m else None


def heavy_atoms(pdb_id, wanted):
    """Heavy-atom coords for ONLY the (chain, resnum) keys in `wanted` --
    not the whole structure. A handful of CASBench entries are large
    multimeric assemblies (hundreds of thousands of atoms); building a
    dict of the entire structure when only ~50-100 annotated residues are
    ever used was real, avoidable memory pressure on an already
    swap-constrained machine (confirmed: an earlier full-structure version
    of this function was SIGKILLed, exit 137, partway through this same
    314-structure run). Found the specific mechanism by size-checking every
    cached file after three more unexplained SIGKILLs at the same resume
    point: `4P3R` is a 113 MB PDB (a huge cryo-EM-scale assembly) -- even
    a streaming line-by-line read of a file that size, on a machine with
    well under 1.5 GB genuinely free, appears to trigger OS-level page-
    cache thrashing severe enough for the kernel to SIGKILL the reading
    process outright, independent of this process's own (small, already
    confirmed) RSS. `MAX_FILE_MB` below skips anything past a size this
    machine has shown it cannot safely read right now, rather than risking
    a fourth crash and losing checkpoint progress again."""
    fp = fetch(pdb_id)
    size_mb = os.path.getsize(fp) / 1e6
    if size_mb > MAX_FILE_MB:
        raise ValueError(f"file too large to safely read on this machine right now "
                         f"({size_mb:.0f} MB > {MAX_FILE_MB} MB cap)")
    out = defaultdict(list)
    with open(fp) as fh:
        for line in fh:
            if not line.startswith(("ATOM", "HETATM")):
                continue
            try:
                key = (line[21], int(line[22:26]))
            except ValueError:
                continue
            if key not in wanted:
                continue
            el = line[76:78].strip().upper()
            name = line[12:16].strip()
            if el == "H" or (not el and name.startswith("H")):
                continue
            try:
                out[key].append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
            except ValueError:
                continue
    return {k: np.asarray(v, float) for k, v in out.items()}


def process_one(rec):
    """Returns a result row dict, or a (pdb, reason) skip tuple."""
    pdb = rec["pdb"]
    allo_keys = [k for k in (parse_tok(t) for t in rec["allosteric_residues"]) if k]
    cat_keys = [k for k in (parse_tok(t) for t in rec["catalytic_residues"]) if k]
    wanted = set(allo_keys) | set(cat_keys)
    try:
        ha = heavy_atoms(pdb, wanted)
    except Exception as ex:
        return None, (pdb, f"{type(ex).__name__}: {ex}")
    allo = [k for k in allo_keys if k in ha]
    cat = [k for k in cat_keys if k in ha]
    if not allo or not cat:
        return None, (pdb, f"unresolved allo={len(allo)}/{rec['n_allo']} cat={len(cat)}/{rec['n_cat']}")
    A = np.vstack([ha[k] for k in allo]); B = np.vstack([ha[k] for k in cat])
    dmin = float(np.min(np.linalg.norm(A[:, None, :] - B[None, :, :], axis=-1)))
    return dict(pdb=pdb, cas_id=rec["cas_id"], protein=rec["protein"], min_heavy_A=dmin), None


def load_checkpoint():
    if CKPT.exists():
        d = json.loads(CKPT.read_text())
        return d["rows"], [tuple(s) for s in d["skipped"]]
    return [], []


def save_checkpoint(rows, skipped):
    CKPT.write_text(json.dumps(dict(rows=rows, skipped=skipped), indent=1))


def finalize(rows, skipped, n_cohort):
    d = np.array([r["min_heavy_A"] for r in rows])
    print("\n" + "=" * 74)
    print("CASBench, STRUCTURE-LEVEL (descriptive only -- 314 rows, 33 proteins, DO NOT quote as n=314)")
    print("=" * 74)
    print(f"  resolved {len(rows)} of {n_cohort}   ({len(skipped)} skipped)")
    print(f"  median {np.median(d):.2f} A   min {d.min():.2f}   max {d.max():.2f}")
    bins = [(0, 1.5, "< 1.5 A  (COVALENT / peptide bond)"),
            (1.5, 4.0, "1.5-4.0 A (van der Waals contact)"),
            (4.0, 8.0, "4.0-8.0 A"),
            (8.0, 1e9, "> 8.0 A  (genuinely distal)")]
    for lo, hi, lab in bins:
        c = int(((d >= lo) & (d < hi)).sum())
        print(f"    {lab:<38} {c:>4}/{len(d)} = {c/len(d):>6.1%}")

    by_prot = defaultdict(list)
    for r in rows:
        by_prot[r["cas_id"]].append(r["min_heavy_A"])
    prot_rows = [{"cas_id": c, "protein": next(r["protein"] for r in rows if r["cas_id"] == c),
                  "median_min_heavy_A": float(np.median(v)), "n_structures": len(v)}
                 for c, v in by_prot.items()]
    pd_ = np.array([p["median_min_heavy_A"] for p in prot_rows])
    print("\n" + "=" * 74)
    print(f"CASBench, PROTEIN-LEVEL (n={len(prot_rows)} proteins, the number that counts)")
    print("=" * 74)
    print(f"  median-of-medians {np.median(pd_):.2f} A   min {pd_.min():.2f}   max {pd_.max():.2f}")
    for lo, hi, lab in bins:
        c = int(((pd_ >= lo) & (pd_ < hi)).sum())
        print(f"    {lab:<38} {c:>4}/{len(pd_)} = {c/len(pd_):>6.1%}")

    print(f"\n  cf. our register (TASK-0288/0297, 28 structures/13 clusters): 8/28 = 28.6% below 1.5 A")
    print(f"  cf. ASBench (TASK-0304, 117 structures/112 proteins): 22.2% / 23.2% below 1.5 A")
    if skipped:
        print(f"\n  skipped ({len(skipped)}):")
        for p, why in skipped[:15]:
            print(f"    {p:<10} {why}")

    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(dict(
        rows=rows, skipped=skipped, n_cohort=n_cohort,
        structure_level=dict(n=len(rows), median=float(np.median(d)),
                              frac_below_1p5=float((d < 1.5).mean()),
                              frac_below_4=float((d < 4.0).mean()),
                              frac_above_8=float((d >= 8.0).mean())),
        protein_level=dict(n=len(prot_rows), rows=prot_rows,
                            median=float(np.median(pd_)),
                            frac_below_1p5=float((pd_ < 1.5).mean()),
                            frac_below_4=float((pd_ < 4.0).mean()),
                            frac_above_8=float((pd_ >= 8.0).mean())),
    ), open(OUT / "casbench_finding_f.json", "w"), indent=1)
    print(f"\n  written -> {OUT}/casbench_finding_f.json")


def main():
    batch = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    keep = set(p.upper() for p in COHORT["casbench"])
    recs = [r for r in ANN["records"] if r["pdb"] in keep]
    print(f"CASBench subset (matches Wu et al. 2022's own 314/33 cohort): {len(recs)} structures")

    rows, skipped = load_checkpoint()
    done_pdbs = set(r["pdb"] for r in rows) | set(p for p, _ in skipped)
    todo = [r for r in recs if r["pdb"] not in done_pdbs]
    print(f"  checkpoint: {len(done_pdbs)} already done, {len(todo)} remaining this run "
          f"(processing up to {batch} now)")

    for j, rec in enumerate(todo[:batch]):
        result, skip = process_one(rec)
        if result:
            rows.append(result)
        else:
            skipped.append(skip)
        if (j + 1) % 5 == 0:
            print(f"  ... {j+1}/{min(batch, len(todo))} this batch "
                  f"({len(rows)+len(skipped)}/{len(recs)} total)")
            save_checkpoint(rows, skipped)

    save_checkpoint(rows, skipped)
    remaining = len(recs) - len(rows) - len(skipped)
    print(f"\n  batch done: {len(rows)} resolved, {len(skipped)} skipped, {remaining} still remaining")

    if remaining <= 0:
        finalize(rows, skipped, len(recs))
    else:
        print(f"  re-run the same command to continue ({remaining} left)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
