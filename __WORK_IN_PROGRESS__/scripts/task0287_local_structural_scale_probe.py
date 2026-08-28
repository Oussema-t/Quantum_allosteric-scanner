"""TASK-0287 -- At what SCALE is an allosteric pocket's location encoded?

Every structural descriptor this register has tested so far ([[TASK-0284]]
Finding B: N, Rg, compactness, helix_fraction, sheet_fraction, gnm_lambda1,
contact_order, mean_degree) is a WHOLE-PROTEIN scalar. All eight came back
null. That null is much weaker than it looks, for two reasons this task
makes explicit and then corrects:

  (1) SCALE MISMATCH. A pocket is a local object; those eight descriptors
      are constant across every pocket of a given protein. The question
      asked was "does this protein's global helix fraction predict where
      its pocket sits" -- which is not the question anyone means.

  (2) NO POSITIVE CONTROL. [[TASK-0284]] Finding B reported eight nulls
      without ever demonstrating the design could detect a descriptor
      that IS known to work. An all-null table from an underpowered
      design is uninterpretable.

PART A -- the scale diagnostic. Variance decomposition (ICC) of min_A
within vs between structures. Where the register carries two ligands for
one apo, min_A is identical to the decimal: the labelled target variable
has (near-)zero within-structure variance, so it is empirically a
PROTEIN-level quantity, and the effective n for ANY between-protein test
is the structure count, not the 33 pocket rows.

PART B -- SS measurement validation BEFORE use. [[TASK-0284]] assigned
helix/sheet by a coarse Ramachandran box (no DSSP available). This task
independently re-derives SS from deposited HELIX/SHEET records and
reports per-target agreement. A descriptor is not used to support a null
until it is shown to measure what it claims.

PART C -- the within-protein design that has power. For each target, every
fpocket candidate on the apo is a row; the candidate with maximal overlap
against the labelled pocket is the positive, the rest are decoys. Local
structural descriptors are computed per candidate. The true pocket's
within-protein PERCENTILE is the statistic, tested against 0.5 by
Wilcoxon signed-rank across targets. Protein identity is absorbed by
construction -- no pseudo-replication, n = targets.

TWO POSITIVE CONTROLS ride along in the same table: min heavy-atom
distance to the seed, and fpocket druggability. Both are known to carry
signal in this register ([[TASK-0282]]). If they do not surface here, the
design is underpowered and every null in the table is void -- that
verdict is printed explicitly rather than left to the reader.

Run: ../.venv/bin/python3 scripts/task0287_local_structural_scale_probe.py
"""
import sys, json, warnings, tempfile, collections
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0, 'src'); sys.path.insert(0, 'scripts')
import prody; prody.confProDy(verbosity="none")
from task0255_hop_angstrom_calibration import _parsePDB_all_altloc
prody.parsePDB = _parsePDB_all_altloc
import yaml
from scipy import stats
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

import task0242_two_stage_dryrun as t0242
from task0242_two_stage_dryrun import prep, CAND
import task0255_hop_angstrom_calibration as t0255
CAND.update(yaml.safe_load(open('config/candidate_targets_task0243.yaml'))['targets'])
from allostery.potentials import gnm_context
from allostery.hamiltonians import contact_matrix
from task0257_r2_sasa_burial_vs_degree import per_residue_sasa

OUT = Path("results/tasks/0287_local_structural_scale")
TAX = json.load(open(
    'results/tasks/0258_allosteric_distance_taxonomy/pocket_taxonomy.json'))
TARGETS = [r['target'] for r in TAX if 'error' not in r]


# --------------------------------------------------------------- PART A
def part_a():
    d = json.load(open(
        'results/tasks/0284_two_populations/bimodality_and_nulls.json'))
    rows = [r for r in d['rows'] if 'N' in r and r.get('min_A') is not None]
    g = collections.defaultdict(list)
    for r in rows:
        g[(r['N'], round(r['Rg'], 2))].append(r['min_A'])
    grand = np.mean([v for vs in g.values() for v in vs])
    ss_within = sum(sum((np.array(vs) - np.mean(vs)) ** 2) for vs in g.values())
    ss_between = sum(len(vs) * (np.mean(vs) - grand) ** 2 for vs in g.values())
    icc = ss_between / (ss_between + ss_within)
    multi = {k: v for k, v in g.items() if len(v) > 1}
    print("=" * 72)
    print("PART A -- at what scale does the TARGET VARIABLE itself vary?")
    print("=" * 72)
    print(f"  pocket rows                     {len(rows)}")
    print(f"  distinct apo structures         {len(g)}")
    print(f"  structures with >1 pocket row   {len(multi)}")
    print(f"  SS_between                      {ss_between:10.3f}")
    print(f"  SS_within                       {ss_within:10.6f}")
    print(f"  ICC (between / total)           {icc:10.6f}")
    for k, v in multi.items():
        print(f"    N={k[0]:<5} min_A spread = {max(v)-min(v):.4f} A  {[round(x,2) for x in v]}")
    print(f"\n  READING: min_A is a PROTEIN-level quantity in this register.")
    print(f"  Effective n for any between-protein descriptor test = {len(g)},")
    print(f"  NOT the {len(rows)} pocket rows [[TASK-0284]] Finding B quoted.")
    return dict(n_rows=len(rows), n_structures=len(g), icc=float(icc),
                ss_within=float(ss_within), ss_between=float(ss_between))


# --------------------------------------------------------------- SS
def ss_from_records(cfg, apo):
    """Per-residue SS from deposited HELIX/SHEET records, aligned to apo."""
    st = prody.parsePDB(cfg["apo_pdb"], compressed=False, secondary=True)
    m = {}
    for ch in st.getHierView().iterChains():
        for r in ch.iterResidues():
            s = r.getSecstrs()
            m[(ch.getChid(), int(r.getResnum()))] = (s[0] if len(s) and s[0] else 'C')
    return np.array([m.get((str(c), int(r)), '?')
                     for c, r in zip(apo.chain_ids, apo.resnums)])


def ss_from_rama(cfg, apo):
    """[[TASK-0284]]'s own coarse Ramachandran-box assignment, per residue."""
    st = prody.parsePDB(cfg["apo_pdb"], compressed=False)
    m = {}
    for ch in st.getHierView().iterChains():
        for res in ch.iterResidues():
            try:
                phi = float(prody.calcPhi(res)); psi = float(prody.calcPsi(res))
            except Exception:
                continue
            if -100 <= phi <= -30 and -67 <= psi <= -7:
                m[(ch.getChid(), int(res.getResnum()))] = 'H'
            elif -180 <= phi <= -45 and (psi >= 90 or psi <= -150):
                m[(ch.getChid(), int(res.getResnum()))] = 'E'
            else:
                m[(ch.getChid(), int(res.getResnum()))] = 'C'
    return np.array([m.get((str(c), int(r)), '?')
                     for c, r in zip(apo.chain_ids, apo.resnums)])


def _seg_id(ss):
    """Contiguous SS-segment index per residue (element identity)."""
    out = np.zeros(len(ss), int); k = 0
    for i in range(1, len(ss)):
        if ss[i] != ss[i - 1]:
            k += 1
        out[i] = k
    return out


# --------------------------------------------------------------- PART C
DESCRIPTORS = [
    # (name, direction-free; percentile tested two-sided)
    "min_euclid_to_seed",     # POSITIVE CONTROL
    "fpocket_drug",           # POSITIVE CONTROL
    "helix_frac", "sheet_frac", "coil_frac",
    "d_helix_vs_protein", "d_sheet_vs_protein",
    "n_ss_segments", "mean_degree", "mean_msf", "mean_sasa",
    "local_contact_order", "n_res",
    "path_helix_frac", "path_sheet_frac", "path_len",
    "shares_ss_element_with_seed",
]
CONTROLS = {"min_euclid_to_seed", "fpocket_drug"}


def build(t):
    cfg, apo, seed, pocket = prep(t)
    if len(seed) == 0 or pocket.sum() == 0:
        return {"error": "no seed or no labelled pocket"}
    coords = apo.coords
    cut = float(cfg.get("enm_cutoff", 8.0))
    resn = np.asarray(apo.resnums)
    idx_of = {int(r): i for i, r in enumerate(resn)}
    apo_ch = cfg.get("apo_chains") or cfg.get("chains")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        ag = prody.parsePDB(cfg["apo_pdb"], compressed=False).select(
            "protein and (" + " or ".join(f"chain {c}" for c in apo_ch) + ")")
        pdb = tmp / f"{t.lower()}_apo.pdb"
        prody.writePDB(str(pdb), ag)
        pockets = t0242.fpocket_candidates(pdb, tmp)
    if isinstance(pockets, dict):
        return {"error": pockets["error"]}

    A = contact_matrix(coords, cutoff=cut, weight="binary")
    ctx = gnm_context(coords, cutoff=cut)
    msf, degree = ctx["msf"], ctx["degree"]
    try:
        sasa = per_residue_sasa(cfg, apo)
    except Exception:
        sasa = np.full(len(resn), np.nan)
    min_euclid = t0255.min_heavy_atom_dist_to_seed(cfg, apo, seed)

    ss_rec = ss_from_records(cfg, apo)
    ss_ram = ss_from_rama(cfg, apo)
    both = (ss_rec != '?') & (ss_ram != '?')
    agree = float(np.mean(ss_rec[both] == ss_ram[both])) if both.sum() else np.nan
    ss = ss_rec
    known = ss != '?'
    seg = _seg_id(ss)
    seed_segs = set(seg[seed].tolist())
    prot_h = float(np.mean(np.isin(ss[known], ['H', 'G', 'I'])))
    prot_e = float(np.mean(np.isin(ss[known], ['E', 'B'])))

    # shortest path from the seed set on the contact graph
    G = csr_matrix(A)
    dist, pred, src = dijkstra(G, unweighted=True, indices=np.asarray(seed),
                               min_only=True, return_predecessors=True)

    def path_from(i):
        p = [i]; g = 0
        while pred[p[-1]] >= 0 and g < 5000:
            p.append(pred[p[-1]]); g += 1
        return np.asarray(p)

    cands = []
    for p in pockets:
        ii = np.asarray([idx_of[r] for r in p["resnums"] if r in idx_of], int)
        if len(ii) == 0:
            continue
        kk = ii[known[ii]]
        h = float(np.mean(np.isin(ss[kk], ['H', 'G', 'I']))) if len(kk) else np.nan
        e = float(np.mean(np.isin(ss[kk], ['E', 'B']))) if len(kk) else np.nan
        sub = A[np.ix_(ii, ii)]
        iu, ju = np.triu_indices(len(ii), 1)
        con = sub[iu, ju] > 0
        lco = (float(np.mean(np.abs(ii[iu][con] - ii[ju][con]))) / len(resn)
               if con.any() else np.nan)
        anchor = ii[int(np.argmin(dist[ii]))]
        pth = path_from(anchor)
        pk = pth[known[pth]]
        cands.append(dict(
            id=p["id"], n_res=int(len(ii)), res_idx=ii.tolist(),
            overlap_count=int(pocket[ii].sum()),
            min_euclid_to_seed=float(np.nanmin(min_euclid[ii])),
            fpocket_drug=float(p.get("druggability_score") or 0.0),
            helix_frac=h, sheet_frac=e,
            coil_frac=(np.nan if not len(kk) else 1.0 - h - e),
            d_helix_vs_protein=(np.nan if np.isnan(h) else h - prot_h),
            d_sheet_vs_protein=(np.nan if np.isnan(e) else e - prot_e),
            n_ss_segments=int(len(set(seg[ii].tolist()))),
            mean_degree=float(np.mean(degree[ii])),
            mean_msf=float(np.mean(msf[ii])),
            mean_sasa=float(np.nanmean(sasa[ii])),
            local_contact_order=lco,
            path_helix_frac=(float(np.mean(np.isin(ss[pk], ['H', 'G', 'I'])))
                             if len(pk) else np.nan),
            path_sheet_frac=(float(np.mean(np.isin(ss[pk], ['E', 'B'])))
                             if len(pk) else np.nan),
            path_len=float(dist[anchor]) if np.isfinite(dist[anchor]) else np.nan,
            shares_ss_element_with_seed=float(
                len(set(seg[ii].tolist()) & seed_segs) > 0),
        ))
    if not cands:
        return {"error": "no residue-resolvable candidates"}
    if max(c["overlap_count"] for c in cands) == 0:
        return {"error": "no candidate overlaps the labelled pocket"}
    return dict(target=t, n_cand=len(cands), cands=cands, ss_agreement=agree,
                n_ss_unknown=int((~known).sum()), N=len(resn),
                prot_helix=prot_h, prot_sheet=prot_e)


def main():
    a = part_a()
    per_target, errs = [], {}
    for t in TARGETS:
        try:
            r = build(t)
        except Exception as ex:
            r = {"error": f"{type(ex).__name__}: {ex}"}
        if "error" in r:
            errs[t] = r["error"]; print(f"  [skip] {t}: {r['error']}")
            continue
        per_target.append(r)
        print(f"  [ok]   {t:<22} {r['n_cand']:>3} candidates  "
              f"SS-agreement {r['ss_agreement']:.2f}")

    print("\n" + "=" * 72)
    print("PART B -- is the SS descriptor measuring what it claims?")
    print("=" * 72)
    ag = [r["ss_agreement"] for r in per_target if np.isfinite(r["ss_agreement"])]
    print(f"  HELIX/SHEET records vs Ramachandran box, per-residue agreement")
    print(f"  n={len(ag)} targets   mean {np.mean(ag):.3f}   "
          f"min {np.min(ag):.3f}   max {np.max(ag):.3f}")
    print(f"  (deposited records used downstream; Ramachandran is the check)")

    print("\n" + "=" * 72)
    print("PART C -- within-protein stratified test (protein absorbed)")
    print("=" * 72)
    print(f"  n = {len(per_target)} targets, each contributing ONE percentile")
    print(f"  {'descriptor':<30}{'mean pct':>10}{'median':>9}{'W p':>9}  verdict")
    res = {}
    for d in DESCRIPTORS:
        pcts = []
        for r in per_target:
            vals = np.array([c[d] for c in r["cands"]], float)
            true_i = int(np.argmax([c["overlap_count"] for c in r["cands"]]))
            v = vals[true_i]
            ok = np.isfinite(vals)
            if not np.isfinite(v) or ok.sum() < 3:
                continue
            others = vals[ok]
            pcts.append(float(np.mean(others < v) + 0.5 * np.mean(others == v)))
        if len(pcts) < 8:
            print(f"  {d:<30}   insufficient ({len(pcts)})"); continue
        p = stats.wilcoxon(np.array(pcts) - 0.5).pvalue
        res[d] = dict(n=len(pcts), mean_pct=float(np.mean(pcts)),
                      median_pct=float(np.median(pcts)), p=float(p))
        tag = "CONTROL" if d in CONTROLS else ""
        print(f"  {d:<30}{np.mean(pcts):>10.3f}{np.median(pcts):>9.3f}"
              f"{p:>9.4f}  {tag}")

    alpha = 0.05 / max(len(res), 1)
    print(f"\n  {len(res)} descriptors -> Bonferroni alpha = {alpha:.5f}")
    ctrl_ok = [d for d in CONTROLS if d in res and res[d]["p"] < alpha]
    sig = [d for d, v in res.items() if v["p"] < alpha and d not in CONTROLS]
    print(f"  positive controls surviving : {ctrl_ok if ctrl_ok else 'NONE'}")
    print(f"  structural descriptors surviving: {sig if sig else 'NONE'}")
    if not ctrl_ok:
        print("\n  *** DESIGN UNDERPOWERED. No positive control survives its own")
        print("  *** correction -- the structural nulls above are VOID, not")
        print("  *** evidence of absence. Do not report them as findings.")
    else:
        print(f"\n  Design demonstrably detects {ctrl_ok} at the same n and the")
        print("  same correction. Structural nulls above are interpretable.")

    OUT.mkdir(parents=True, exist_ok=True)
    for r in per_target:
        for c in r["cands"]:
            c.pop("res_idx", None)
    json.dump(dict(part_a=a, ss_agreement=[r["ss_agreement"] for r in per_target],
                   part_c=res, alpha=alpha, controls_surviving=ctrl_ok,
                   structural_surviving=sig, n_targets=len(per_target),
                   errors=errs, per_target=per_target),
              open(OUT / "local_structural_scale.json", "w"), indent=1)
    print(f"\n  written -> {OUT}/local_structural_scale.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())


# ---------------------------------------------------------------------------
# FOLLOW-UP (same session, run after the main table): the four Bonferroni
# survivors were tested for whether they are one confound wearing four hats.
# Within each protein, each descriptor is regressed on a control across that
# protein's candidates and the true pocket's percentile recomputed on the
# residual. Results committed in local_structural_scale.json under
# "conditioning". See the task file for the reading.
# ---------------------------------------------------------------------------
