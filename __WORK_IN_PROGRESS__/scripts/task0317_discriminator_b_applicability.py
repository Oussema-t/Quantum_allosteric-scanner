"""TASK-0317 -- Discriminator B: is WHICH of Wu/Stromich/Yaliraki (2022)'s
six measures fires predictable from the PAPER'S OWN STATED applicability
conditions for those tests, rather than from generic global protein
descriptors (N, chain count, site separation, fold class -- all already
tried and null, [[TASK-0306]])?

APPLICABILITY CONDITIONS, read from the paper (PMC8767309), not recalled:

  1. Surrogate-CI test: 1,000 surrogate sites are generated per protein,
     matched to the true allosteric site on "(1) the number of residues...
     and (2) the diameter (maximum distance between any two atoms in the
     site) is smaller than that of the allosteric site." The test's OWN
     discriminative power therefore depends on how much a local structural
     property varies among same-size, compact (small-diameter) surrogate
     windows elsewhere in the structure -- a homogeneous protein gives
     surrogates that all look like the true site (test underpowered); a
     heterogeneous one does not.
     -> Descriptor A: `surrogate_spread` -- std of mean GNM MSF across
        many same-size, spatially-compact random windows (a direct,
        cheap proxy for the achievable surrogate ensemble's own spread,
        reusing `allostery.potentials.gnm_context`, not re-deriving their
        1,000-surrogate machinery).

  2. High-propensity-proportion test P(p>0.95): "This is because QS is
     uniformly distributed, and the bonds with QS greater than 0.95
     belong to the top 5%..." -- an explicit uniformity ASSUMPTION on
     their propensity score, which this repo does not reproduce (QS
     itself is not available; only the six binary Summary verdicts are).
     Not directly testable without their own propensity values -- flagged,
     not silently dropped; see "Not done" below.

  3. Explicit caveat, stated directly: "More detailed analysis would be
     usually required in cases where the allosteric site and the
     orthosteric site are in very close proximity, to elucidate the
     effect of cooperativity in large and complex multimeric proteins or
     the role of structural water molecules." Three concrete, computable
     conditions in one sentence:
     -> site proximity: already tried as a GLOBAL scalar ([[TASK-0306]],
        null) -- reproduced here for completeness only, not counted as new.
     -> "large and complex multimeric proteins": not raw chain count
        (already tried, null) but a LOCAL, site-specific version --
        Descriptor B: `interface_frac` -- fraction of the site's OWN
        residues in direct cross-chain contact, from the contact graph.
     -> "structural water molecules": Descriptor C: `water_density` --
        count of crystallographic waters (HETATM HOH) within 5A of any
        site residue, normalised by site size.

Data: [[TASK-0306]]'s own already-fetched, already-verified `Summary` bits
(`results/tasks/0306_six_measure_meta_classifier/six_measure_analysis.json`,
condition `asbench_without_ligand` -- the SAME primary condition
[[TASK-0306]]'s own `meta_classifier` used, 118 structures) -- no new
Europe PMC fetch. Site residues from [[TASK-0304]]'s own
`asbench_annotations.json`. Structures from `pdb_cache/` (already fully
cached, [[TASK-0309]]'s own finding).

Reuses, does not re-derive:
  - `task0306_six_measure_meta_classifier.lopo_predict` (verbatim,
    duplicated per this register's own cross-script convention) and its
    exact positive-control design (predict one measure from the other
    five), carried unchanged per this task's own Constraint.
  - `allostery.potentials.gnm_context` for MSF/degree.

Bonferroni across the descriptor family (this task's own Constraint,
[[TASK-0314]]'s standing multiplicity concern): 3 descriptors x 6 measures
= 18 tests, alpha = 0.05/18 = 0.00278. Permutation p-values throughout
(not just point-estimate AUCs), since a per-measure AUC alone carries no
significance without one.

Run: ../.venv/bin/python3 scripts/task0317_discriminator_b_applicability.py
"""
from __future__ import annotations

import json
import re
import sys
import warnings
from pathlib import Path
from collections import defaultdict

warnings.filterwarnings("ignore")

import numpy as np
from sklearn.metrics import roc_auc_score

sys.path.insert(0, "src")
sys.path.insert(0, "..")
from backend.data_layer import fetch  # noqa: E402
from allostery.potentials import gnm_context  # noqa: E402

R0304 = Path("results/tasks/0304_asbench_casbench")
R0306 = Path("results/tasks/0306_six_measure_meta_classifier")
OUT = Path("results/tasks/0317_discriminator_b_applicability")
MEASURE_NAMES = ["surrCI_pR", "surrCI_pb", "highProp_pR", "highProp_pb", "refQ_pR", "refQ_pb"]
CUTOFF = 8.0  # this repo's own standard GNM/contact-graph cutoff (task0308's ASBench convention)
N_WINDOWS = 50
WATER_CUTOFF = 5.0
N_PERM = 500
SEED = 0

_ALLO_RE = re.compile(r"^[A-Z]{3}(-?\d+)\s+(\S+)$")
_ACT_RE = re.compile(r"^([A-Za-z]+)(-?\d+)$")


def parse_allo(tok: str):
    m = _ALLO_RE.match(tok.strip())
    return (m.group(2), int(m.group(1))) if m else None


def parse_act(tok: str):
    m = _ACT_RE.match(tok.strip())
    return (m.group(1), int(m.group(2))) if m else None


def parse_structure(pdb_id: str):
    """CA coords (first altloc) + chain/resnum keys, plus water oxygen
    coords, from the cached PDB file. Returns None if unusable."""
    fp = fetch(pdb_id)
    if fp is None:
        return None
    keys, xyz = [], []
    waters = []
    seen = set()
    for line in Path(fp).read_text().splitlines():
        rec = line[:6].strip()
        if rec == "ATOM" and line[12:16].strip() == "CA" and line[16] in (" ", "A"):
            k = (line[21], int(line[22:26]))
            if k in seen:
                continue
            seen.add(k)
            keys.append(k)
            xyz.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
        elif rec == "HETATM" and line[17:20].strip() == "HOH" and line[12:16].strip() in ("O", "OW"):
            waters.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
    if len(keys) < 10:
        return None
    return dict(keys=keys, xyz=np.asarray(xyz, float),
                waters=np.asarray(waters, float) if waters else np.zeros((0, 3)))


def compute_descriptors(struct: dict, site_pos: list, rng: np.random.Generator):
    keys, xyz, waters = struct["keys"], struct["xyz"], struct["waters"]
    n = len(keys)
    n_site = len(site_pos)
    if n_site == 0 or n_site >= n:
        return None

    ctx = gnm_context(xyz, cutoff=CUTOFF)
    msf = ctx["msf"]

    # --- Descriptor A: surrogate_spread -- std of mean MSF across N_WINDOWS
    # same-size, spatially-compact (nearest-neighbour) random windows.
    dmat = np.linalg.norm(xyz[:, None, :] - xyz[None, :, :], axis=-1)
    window_means = []
    seeds = rng.choice(n, size=min(N_WINDOWS, n), replace=False)
    for s in seeds:
        nearest = np.argsort(dmat[s])[:n_site]
        window_means.append(float(msf[nearest].mean()))
    surrogate_spread = float(np.std(window_means))

    # --- Descriptor B: interface_frac -- fraction of site residues with
    # >=1 cross-chain contact within CUTOFF.
    chain_ids = np.array([k[0] for k in keys])
    n_interface = 0
    for p in site_pos:
        own_chain = chain_ids[p]
        d = dmat[p]
        if np.any((d <= CUTOFF) & (d > 0) & (chain_ids != own_chain)):
            n_interface += 1
    interface_frac = n_interface / n_site

    # --- Descriptor C: water_density -- crystallographic waters within
    # WATER_CUTOFF of any site residue, normalised by site size.
    if len(waters):
        site_xyz = xyz[site_pos]
        wd = np.linalg.norm(waters[:, None, :] - site_xyz[None, :, :], axis=-1)
        n_waters_near = int((wd.min(axis=1) <= WATER_CUTOFF).sum())
    else:
        n_waters_near = 0
    water_density = n_waters_near / n_site

    return dict(surrogate_spread=surrogate_spread, interface_frac=interface_frac,
                water_density=water_density, n_waters_near=n_waters_near, N=n)


def lopo_predict(X, y, groups):
    """[[TASK-0306]]'s own `lopo_predict`, duplicated verbatim."""
    groups = np.asarray(groups)
    preds = np.full(len(y), np.nan)
    for g in sorted(set(groups)):
        train = groups != g
        test = groups == g
        if train.sum() < 4:
            continue
        Xb = np.column_stack([X[train], np.ones(train.sum())])
        b, *_ = np.linalg.lstsq(Xb, y[train].astype(float), rcond=None)
        Xt = np.column_stack([X[test], np.ones(test.sum())])
        preds[test] = Xt @ b
    return preds


def z(v):
    v = np.asarray(v, float)
    s = v.std()
    return (v - v.mean()) / (s if s > 1e-12 else 1.0)


def perm_p(obs, null):
    upper = (np.sum(null >= obs) + 1) / (len(null) + 1)
    lower = (np.sum(null <= obs) + 1) / (len(null) + 1)
    return float(min(1.0, 2 * min(upper, lower)))


def lopo_auc_with_p(X, y, groups, rng, n_perm=N_PERM):
    y = np.asarray(y, float)
    if y.sum() < 5 or y.sum() > len(y) - 5:
        return dict(skipped="too few positives/negatives", n_pos=int(y.sum()), n=len(y))
    pred = lopo_predict(X, y, groups)
    v = ~np.isnan(pred)
    obs = float(roc_auc_score(y[v], pred[v]))
    null = []
    for _ in range(n_perm):
        yp = rng.permutation(y)
        if yp.sum() < 5 or yp.sum() > len(yp) - 5:
            continue
        predp = lopo_predict(X, yp, groups)
        vp = ~np.isnan(predp)
        null.append(roc_auc_score(yp[vp], predp[vp]))
    null = np.array(null)
    p = perm_p(obs, null) if len(null) > 10 else float("nan")
    return dict(lopo_auc=obs, n_pos=int(y.sum()), n=int(v.sum()), p_perm=p, n_null=int(len(null)))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    six = json.load(open(R0306 / "six_measure_analysis.json"))
    rows = six["rows"]["asbench_without_ligand"]
    print(f"Loaded {len(rows)} Summary rows (asbench_without_ligand, TASK-0306's own primary condition)")

    ann = {r["pdb"]: r for r in json.load(open(R0304 / "asbench_annotations.json"))}

    joined = []
    skipped = []
    for r in rows:
        a = ann.get(r["pdb"])
        if a is None:
            skipped.append((r["pdb"], "no annotation record")); continue
        struct = parse_structure(r["pdb"].split("_")[0])
        if struct is None:
            skipped.append((r["pdb"], "no/unusable structure")); continue
        pos_by_key = {k: i for i, k in enumerate(struct["keys"])}
        site_pos = []
        for tok in a["allosteric_residues"]:
            k = parse_allo(tok)
            if k and k in pos_by_key:
                site_pos.append(pos_by_key[k])
        site_pos = sorted(set(site_pos))
        desc = compute_descriptors(struct, site_pos, rng)
        if desc is None:
            skipped.append((r["pdb"], "empty/degenerate site")); continue
        joined.append(dict(pdb=r["pdb"], protein=r["protein"], bits=r["bits"],
                            n_fired=r["n_fired"], n_site_resolved=len(site_pos), **desc))
        print(f"  {r['pdb']:<10} n_site={len(site_pos):>3} N={desc['N']:>5} "
              f"spread={desc['surrogate_spread']:.4f} iface={desc['interface_frac']:.3f} "
              f"water={desc['water_density']:.3f}")

    print(f"\n{len(joined)}/{len(rows)} joined ({len(skipped)} skipped)")
    if skipped:
        print("  skipped:", skipped[:10], "..." if len(skipped) > 10 else "")

    proteins = [j["protein"] for j in joined]
    RAW = {
        "surrogate_spread": [j["surrogate_spread"] for j in joined],
        "interface_frac": [j["interface_frac"] for j in joined],
        "water_density": [j["water_density"] for j in joined],
    }
    DESCRIPTORS = {k: z(v) for k, v in RAW.items()}

    results = {"n_joined": len(joined), "n_proteins": len(set(proteins)), "skipped": skipped,
               "per_descriptor": {},
               "raw_values": {"protein": proteins, "n_fired": [j["n_fired"] for j in joined], **RAW}}

    print(f"\n=== Per-measure LOPO AUC per descriptor (protein-held-out, n={len(joined)}, "
          f"{len(set(proteins))} protein clusters) ===")
    for dname, X in DESCRIPTORS.items():
        print(f"\n  -- {dname} --")
        per_measure = {}
        for k, name in enumerate(MEASURE_NAMES):
            y = np.array([j["bits"][k] for j in joined], float)
            res = lopo_auc_with_p(X.reshape(-1, 1), y, proteins, rng)
            per_measure[name] = res
            if "skipped" in res:
                print(f"    {name:<14} skipped ({res['skipped']}, n_pos={res['n_pos']})")
            else:
                print(f"    {name:<14} AUC={res['lopo_auc']:.3f}  p={res['p_perm']:.4f}  "
                      f"(n_pos={res['n_pos']}/{res['n']})")
        n_fired = np.array([j["n_fired"] for j in joined], float)
        pred_nf = lopo_predict(X.reshape(-1, 1), n_fired, proteins)
        v = ~np.isnan(pred_nf)
        from scipy.stats import spearmanr
        rho = spearmanr(pred_nf[v], n_fired[v])
        raw_rho = spearmanr(X, n_fired)
        n_distinct = len(set(np.round(X, 8).tolist()))
        # TIE-BREAKING ARTIFACT, found and diagnosed 2026-09-01 (this task's
        # own run): a heavily-tied raw feature (few distinct values -- here,
        # `interface_frac`/`water_density`, small-integer ratios) can produce
        # a LARGE LOPO Spearman rho against a target it has essentially ZERO
        # raw/pooled correlation with. Mechanism, confirmed directly: the
        # per-fold OLS slope is stable (verified: 77/79 folds same sign,
        # fold b1 std=0.025 vs mean=-0.057 for `interface_frac`), so this is
        # NOT ordinary LOPO overfitting instability -- it is TIE-BREAKING:
        # many rows share the exact same raw X value (71/117 rows have
        # `interface_frac`=0.0 exactly), and tiny fold-to-fold intercept
        # jitter (a different single cluster excluded each fold) arbitrarily
        # reorders those tied rows in `pred`, and if that arbitrary
        # reordering happens to align with `n_fired` even slightly, Spearman
        # -- which is highly sensitive to how ties resolve -- inflates it
        # into an apparent large correlation with NO underlying signal.
        # `surrogate_spread` (104/117 distinct values, few ties) shows no
        # such gap (LOPO rho matches raw rho almost exactly): the artifact
        # requires both a heavily-tied feature AND LOPO-with-Spearman: this
        # register's own established `lopo_predict`+`roc_auc_score`/
        # `spearmanr` idiom ([[TASK-0306]]'s own convention, reused here) is
        # not safe for the former without checking `n_distinct` first.
        # THE RAW/POOLED SPEARMAN (`raw_rho_nfired` below), NOT the LOPO one,
        # is the trustworthy number whenever `n_distinct` is small relative
        # to n -- reported explicitly, not silently substituted.
        results["per_descriptor"][dname] = dict(
            per_measure=per_measure, n_distinct=n_distinct,
            rho_nfired_LOPO=float(rho.statistic), p_nfired_LOPO=float(rho.pvalue),
            rho_nfired_raw=float(raw_rho.statistic), p_nfired_raw=float(raw_rho.pvalue))
        tie_flag = " ** TIE-BREAKING ARTIFACT RISK (n_distinct << n) -- trust raw, not LOPO **" \
            if n_distinct < len(X) * 0.6 else ""
        print(f"    n_fired: LOPO rho={rho.statistic:+.3f} (p={rho.pvalue:.4f})  "
              f"raw/pooled rho={raw_rho.statistic:+.3f} (p={raw_rho.pvalue:.4f})  "
              f"n_distinct={n_distinct}/{len(X)}{tie_flag}")

    # --- Bonferroni gate, pre-stated ---
    n_tests = len(DESCRIPTORS) * len(MEASURE_NAMES)
    alpha_bonf = 0.05 / n_tests
    print(f"\n=== Bonferroni gate: {n_tests} tests, alpha={alpha_bonf:.5f} ===")
    survivors = []
    for dname, d in results["per_descriptor"].items():
        for name, r in d["per_measure"].items():
            if "skipped" in r:
                continue
            if r["p_perm"] < alpha_bonf:
                survivors.append((dname, name, r["lopo_auc"], r["p_perm"]))
    if survivors:
        print("  SURVIVORS:")
        for s in survivors:
            print(f"    {s}")
    else:
        print("  NONE survive Bonferroni correction.")
    results["bonferroni"] = dict(n_tests=n_tests, alpha=alpha_bonf, survivors=survivors)

    # --- positive control, carried unchanged (TASK-0306's own design) ---
    print("\n=== Positive control: predict one measure from the other five's own bits ===")
    Ball = np.array([j["bits"] for j in joined], float)
    control = {}
    for k, name in enumerate(MEASURE_NAMES):
        y = Ball[:, k]
        Xc = np.delete(Ball, k, axis=1)
        pred = lopo_predict(Xc, y, proteins)
        v = ~np.isnan(pred)
        auc = float(roc_auc_score(y[v], pred[v]))
        control[name] = auc
        print(f"    {name:<14} AUC={auc:.3f}")
    results["positive_control_auc"] = control
    pc_ok = all(0.6 <= v <= 1.0 for v in control.values())
    print(f"\n  positive control {'PASS' if pc_ok else 'FAIL'} "
          f"(expect ~0.74-0.88, TASK-0306's own reference range)")
    results["positive_control_pass"] = pc_ok

    with open(OUT / "discriminator_b_applicability.json", "w") as fh:
        json.dump(results, fh, indent=1)
    print(f"\nWrote {OUT / 'discriminator_b_applicability.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
