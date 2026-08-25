"""TASK-0260 -- does a purpose-built cryptic-pocket predictor close
[[TASK-0259]]'s 29% residual (the share TASK-0254's own 3-block Shapley
attribution -- geometry / fpocket / CTQW -- could not assign)?

**Citation verification (live, before any code was written against these,
per this register's own standing PAPER_CITATION_PROTOCOL.md convention)**:
  - PocketMiner: Meller, Ward, Borowsky, Kshirsagar, Lotthammer, Oviedo,
    Ferres, Bowman (2023), Nature Communications 14:2135,
    DOI 10.1038/s41467-023-36699-3 -- confirmed via Crossref directly.
  - CryptoSite: Cimermancic et al. (2016), J. Mol. Biol. 428:709-719,
    DOI 10.1016/j.jmb.2016.01.029 -- confirmed via Crossref directly.
  - P2Rank: Krivak & Hoksza (2018), J. Cheminform. 10:39,
    DOI 10.1186/s13321-018-0285-8 -- confirmed via Crossref directly.
  - FTMap/FTSite family: Kozakov, Grove, Hall, Bohnuud, Mottarella, Luo,
    Xia, Beglov, Vajda (2015), Nature Protocols 10:733-755,
    DOI 10.1038/nprot.2015.043 -- confirmed via Crossref directly. The
    paper's own title/abstract describe this explicitly as a **web server
    family** (FTMap/FTSite/FTFlex/FTDyn), not a distributable local tool.

**Constraint-3 ruling (settled here, before building; recorded verbatim in
[[TASK-0221]]'s own organiser-question list as item (f), since the closest
of the four calls is genuinely ambiguous, not to be silently assumed)**:
Constraint 3 forbids MD trajectories as INPUTS -- read literally (this
register's own settled precedent, HYP-S7 in `search_complexity.md`) as
governing what THIS pipeline supplies at inference time, not a third-party
tool's own historical training provenance.
  - P2Rank: supervised ML trained on labelled BOUND/holo experimental
    structures (Random Forest over Connolly-surface points) -- no MD
    anywhere, training or inference. LEGAL, unambiguous.
  - FTMap/FTSite: physics-based FFT probe-clustering, not ML at all, no
    training data, no MD anywhere. LEGAL, unambiguous -- but fails the
    SEPARATE installability gate: confirmed web-server-only (see citation
    above), no scriptable local tool for a 20-target batch run.
  - PocketMiner: MD used only to generate the external authors' own
    TRAINING labels; inference takes a single static structure, zero MD
    supplied by us at runtime. Reads LEGAL under the literal rule above --
    but flagged to organisers ([[TASK-0221]] item (f)) since it is a
    closer call than HYP-S7's own settled precedent.
  - CryptoSite (full model): its own most informative single feature is
    "the average pocket score from MD simulations" (AllosMod) -- this
    model runs its OWN internal MD conformational sampling AT INFERENCE
    to score a new target structure. That is MD executing as an
    input-generation step in OUR OWN pipeline, not training-time-only
    provenance -- a qualitatively different case from PocketMiner, not a
    matter of degree. EXCLUDED. The paper's own reported MD-free "faster
    version" (AUC 0.74 on their benchmark) would be legal in principle,
    but is not independently released as runnable software (an ablation
    reported inside the paper, not shipped as a separate tool or the
    actual CryptoSite web server) -- dropped on installability grounds,
    not the constraint question.

**Survivors: P2Rank only.** PocketMiner requires a Python 3.7-3.9 +
TensorFlow<=2.9 environment this repo's own `.venv` (Python 3.13,
TensorFlow 2.16 only available) cannot satisfy without a separate,
substantial environment build -- attempted as a time-boxed side effort
(see this task's own Done section for the outcome), not silently skipped.
FTMap/FTSite excluded on installability alone, as established above.

Reuses, does not re-derive: `task0242_two_stage_dryrun.prep`/`CAND` (via
`task0249_composite_dumb_baseline.target_rows`, imported unmodified) for
the frozen-set apo structures/seeds/labels; `task0254_fpocket_variance_
and_crypticity`'s own `cv_auc`/`z`/`build_blocks`/`crypticity` (imported,
not copied) for the CV-AUC engine and the pre-registered crypticity
definition -- extended to a 4th block via a generalised Shapley routine
(the original `shapley_attribution` hardcodes 3 blocks at module level;
rather than edit that task's own file, a parametrised version is defined
here, sharing the same `cv_auc`/`z` primitives).
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import time
import itertools
from pathlib import Path

import numpy as np
import yaml

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import prody  # noqa: E402
prody.confProDy(verbosity="none")

import task0242_two_stage_dryrun as t0242  # noqa: E402
import task0249_composite_dumb_baseline as t0249  # noqa: E402
import task0254_fpocket_variance_and_crypticity as t0254  # noqa: E402

OUT = _ROOT / "results/tasks/0260_cryptic_predictor_residual"
FROZEN_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"
P2RANK_BIN = _ROOT / "tools/p2rank/p2rank_2.5.1/prank"
BLOCKS4 = ["geometry", "fpocket", "ctqw", "p2rank"]


def run_p2rank(pdb_path: Path, work: Path) -> list[dict]:
    """One `prank predict` call; returns the per-residue rows
    (chain, resnum, probability) from `<pdb>_residues.csv`."""
    r = subprocess.run(
        [str(P2RANK_BIN), "predict", "-f", str(pdb_path), "-o", str(work)],
        capture_output=True, text=True, timeout=180,
    )
    csv_path = work / f"{pdb_path.name}_residues.csv"
    if r.returncode != 0 or not csv_path.exists():
        raise RuntimeError(f"p2rank failed (rc={r.returncode}): {r.stderr[-500:]}")
    rows = []
    with open(csv_path) as fh:
        for row in csv.DictReader(fh, skipinitialspace=True):
            rows.append({
                "chain": row["chain"].strip(),
                "resnum": int(row["residue_label"]),
                "probability": float(row["probability"]),
            })
    return rows


def p2rank_per_residue(t: str, cfg: dict, resn: np.ndarray) -> np.ndarray:
    """P2Rank probability aligned to `resn`'s own order -- matching
    `fpocket_druggability_per_residue`'s own established "plain-int set,
    apo single-chain convention" (resnum lookup only, no chain
    disambiguation) for direct consistency with the existing fpocket
    block on this same frozen set."""
    apo_ch = cfg.get("apo_chains") or cfg.get("chains")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        ag = prody.parsePDB(cfg["apo_pdb"], compressed=False).select(
            "protein and (" + " or ".join(f"chain {c}" for c in apo_ch) + ")"
        )
        pdb = tmp / f"{t.lower()}_apo.pdb"
        prody.writePDB(str(pdb), ag)
        rows = run_p2rank(pdb, tmp)
    lookup = {int(rn): i for i, rn in enumerate(resn)}
    out = np.zeros(len(resn), dtype=np.float64)
    for row in rows:
        i = lookup.get(row["resnum"])
        if i is not None:
            out[i] = max(out[i], row["probability"])
    return out


def shapley_attribution_4(feat: dict, y: np.ndarray, blocks: list[str]) -> dict:
    """Generalised n-block exact Shapley (4! = 24 permutations, still
    cheap to brute-force -- same value(S) = (cv_auc(S)-0.5)/0.5 rule as
    task0254's own 3-block `shapley_attribution`, reusing that module's
    `cv_auc` unmodified)."""
    cache: dict = {}

    def value(subset: tuple) -> float:
        key = tuple(sorted(subset))
        if key in cache:
            return cache[key]
        if not key:
            v = 0.0
        else:
            X = np.column_stack([feat[b] for b in key])
            v = (t0254.cv_auc(X, y) - 0.5) / 0.5
        cache[key] = v
        return v

    shap = {b: [] for b in blocks}
    for perm in itertools.permutations(blocks):
        prefix: list = []
        for b in perm:
            before = value(tuple(prefix))
            prefix = prefix + [b]
            after = value(tuple(prefix))
            shap[b].append(after - before)
    shapley = {b: float(np.mean(shap[b])) for b in blocks}
    full_share = value(tuple(blocks))
    full_auc = 0.5 + 0.5 * full_share
    return dict(shapley=shapley, full_auc=full_auc, full_share=full_share,
                unexplained=1.0 - full_share)


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

    print(f"\n{len(data)}/{len(frozen_targets)} usable (matches TASK-0249's own n=20 filter)\n")

    print("### Running P2Rank on every apo structure ###")
    p2rank_scores = {}
    for t, d in data.items():
        t0 = time.monotonic()
        try:
            raw = p2rank_per_residue(t, new_cand[t], d["resn"])
        except Exception as exc:  # noqa: BLE001
            print(f"{t}: P2RANK FAILED {exc!r}")
            continue
        elapsed = time.monotonic() - t0
        p2rank_scores[t] = raw
        print(f"{t}: p2rank done ({elapsed:.1f}s), mean_prob={raw.mean():.3f}")

    print(f"\n{len(p2rank_scores)}/{len(data)} targets scored by P2Rank\n")

    print("### Four-block Shapley attribution (geometry / fpocket / CTQW / p2rank) ###")
    attribution = {}
    crypt = {}
    for t in p2rank_scores:
        d = data[t]
        seed = d["seed"]
        m = np.ones(len(d["coords"]), dtype=bool)
        m[seed] = False
        blocks = t0254.build_blocks(t, d)
        blocks["p2rank"] = t0254.z(p2rank_scores[t])[m].reshape(-1, 1)
        y = d["y"]
        result = shapley_attribution_4(blocks, y, BLOCKS4)
        attribution[t] = result
        crypt[t] = t0254.crypticity(d)
        sh = result["shapley"]
        print(f"{t:24s} geom={100*sh['geometry']:+5.1f}%  fpocket={100*sh['fpocket']:+5.1f}%  "
              f"ctqw={100*sh['ctqw']:+5.1f}%  p2rank={100*sh['p2rank']:+5.1f}%  "
              f"unexplained={100*result['unexplained']:5.1f}%  "
              f"crypticity={100*crypt[t]['fraction_open']:.0f}%")

    (OUT / "shapley_4block.json").write_text(json.dumps(attribution, indent=1))
    (OUT / "crypticity.json").write_text(json.dumps(crypt, indent=1))

    unexs4 = [a["unexplained"] for a in attribution.values()]
    p2ranks = [a["shapley"]["p2rank"] for a in attribution.values()]
    print(f"\nn={len(attribution)}")
    print(f"  p2rank Shapley share   {100*min(p2ranks):+.0f} to {100*max(p2ranks):+.0f}%  "
          f"(median {100*np.median(p2ranks):+.0f}%)")
    print(f"  unexplained (4-block)  {100*min(unexs4):.0f} to {100*max(unexs4):.0f}%  "
          f"(median {100*np.median(unexs4):.0f}%)")

    already_open = [t for t in attribution if crypt[t]["already_open"]]
    cryptic = [t for t in attribution if crypt[t]["already_open"] is False]
    p2rank_open = [attribution[t]["shapley"]["p2rank"] for t in already_open]
    p2rank_cryptic = [attribution[t]["shapley"]["p2rank"] for t in cryptic]
    print(f"\nCrypticity-stratified p2rank Shapley share:")
    print(f"  already-open (n={len(already_open)}): median {100*np.median(p2rank_open) if p2rank_open else float('nan'):+.1f}%")
    print(f"  cryptic-testing (n={len(cryptic)}): median {100*np.median(p2rank_cryptic) if p2rank_cryptic else float('nan'):+.1f}%")

    print(f"\nWrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
