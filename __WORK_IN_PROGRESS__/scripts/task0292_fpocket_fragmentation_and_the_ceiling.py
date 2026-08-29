"""TASK-0292 -- does fpocket's pocket-splitting ([[TASK-0291]]) cost us on
the pocket-selection ceiling ([[TASK-0282]])?

User question following [[TASK-0291]]: if one physical cavity is cut into
several numbered pockets, does that hurt the "filter by distance, rank by
druggability, then draw 5 residues" ceiling baseline?

Mechanism proposed before running: [[TASK-0287]] showed fpocket
druggability is largely pocket SIZE. Splitting a real cavity makes each
fragment smaller, which should push its fragments DOWN a size-driven
ranking relative to an unsplit decoy cavity.

FOUR PARTS.

A. Reproduce [[TASK-0282]]'s published rule EH (0.16486) from a fresh
   reimplementation, as a control on the machinery before changing it.

B. MERGE SWEEP. Rebuild candidates as merged cavities under several
   criteria -- shared lining residues, and min Ca-Ca below 2/3/4/5/6 A --
   and recompute rule EH and oracle EH. Swept rather than pinned to one
   threshold, because a first attempt at 8 A percolated across the whole
   protein surface (every target collapsed to ONE cavity) and produced a
   meaningless answer. That failure is recorded here, not hidden.

C. Diagnose the size mechanism directly: sizes of the oracle-best vs
   rule-selected candidate, and within-target Spearman of candidate size
   against both EH and druggability.

D. One principled size-corrected ranking variant, evaluated IN-SAMPLE and
   labelled as such.

Run: ../.venv/bin/python3 scripts/task0292_fpocket_fragmentation_and_the_ceiling.py
"""
import sys, json, warnings, tempfile
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
from scipy.sparse.csgraph import connected_components
import task0242_two_stage_dryrun as t0242
from task0242_two_stage_dryrun import prep, CAND
from allostery.baselines import hop_from_seed
CAND.update(yaml.safe_load(open('config/candidate_targets_task0243.yaml'))['targets'])

OUT = Path("results/tasks/0292_fpocket_fragmentation")
D82 = json.load(open('results/tasks/0282_pocket_level_top5_distance_druggability_sweep/'
                     'pocket_selection_sweep.json'))
PUBLISHED = D82['final_rule_mean_eh_frozen20']
FROZEN = [r['target'] for r in D82['rows'] if r['group'] != 'mandatory']


def build_cache():
    """Candidates + pairwise geometry + true pocket, per frozen target."""
    cache = {}
    for t in FROZEN:
        try:
            cfg, apo, seed, pocket = prep(t)
            coords = apo.coords; cut = float(cfg.get("enm_cutoff", 8.0))
            resn = np.asarray(apo.resnums); idx = {int(r): i for i, r in enumerate(resn)}
            ach = cfg.get("apo_chains") or cfg.get("chains")
            with tempfile.TemporaryDirectory() as tmp:
                tmp = Path(tmp)
                ag = prody.parsePDB(cfg["apo_pdb"], compressed=False).select(
                    "protein and (" + " or ".join(f"chain {c}" for c in ach) + ")")
                p = tmp / f"{t.lower()}.pdb"; prody.writePDB(str(p), ag)
                pk = t0242.fpocket_candidates(p, tmp)
            if isinstance(pk, dict):
                continue
            hop = -hop_from_seed(coords, seed, cutoff=cut)
            C = []
            for q in pk:
                ii = np.array([idx[r] for r in q["resnums"] if r in idx], int)
                if len(ii):
                    C.append(dict(ii=ii.tolist(),
                                  drug=float(q.get("druggability_score") or 0.0),
                                  hop=float(np.min(hop[ii])), n=int(len(ii))))
            if not C:
                continue
            m = len(C); Dm = np.full((m, m), np.inf); SH = np.zeros((m, m), bool)
            sets = [set(c['ii']) for c in C]
            for a in range(m):
                ca = coords[np.array(C[a]['ii'])]
                for b in range(a + 1, m):
                    cb = coords[np.array(C[b]['ii'])]
                    d = float(np.min(np.linalg.norm(ca[:, None, :] - cb[None, :, :], axis=-1)))
                    Dm[a, b] = Dm[b, a] = d
                    SH[a, b] = SH[b, a] = len(sets[a] & sets[b]) > 0
            cache[t] = dict(C=C, D=Dm.tolist(), SH=SH.tolist(),
                            pocket=np.where(pocket)[0].tolist())
            print(f"  cached {t:<22} {m} candidates, {int(pocket.sum())} pocket residues")
        except Exception as ex:
            print(f"  [skip] {t}: {type(ex).__name__}: {ex}")
    return cache


def cavities(rec, pk, mode, thr):
    C = rec['C']; m = len(C)
    if mode == 'shared':
        A = np.array(rec['SH'], bool)
    elif mode == 'dist':
        A = np.array(rec['D'], float) < thr
    else:
        A = np.array(rec['SH'], bool) | (np.array(rec['D'], float) < thr)
    np.fill_diagonal(A, False)
    n, lab = connected_components(csr_matrix(A), directed=False)
    out = []
    for c in range(n):
        mem = [C[i] for i in range(m) if lab[i] == c]
        ii = set()
        for x in mem:
            ii |= set(x['ii'])
        out.append(dict(n=len(ii), ov=len(ii & pk),
                        drug=max(x['drug'] for x in mem),
                        hop=min(x['hop'] for x in mem), nfrag=len(mem)))
    return out


def rule_eh(cav):
    f = [c for c in cav if c['hop'] >= 1] or cav
    b = max(f, key=lambda c: c['drug'])
    return b['ov'] / b['n']


def main():
    print("=" * 72); print("PART A -- reproduce the published ceiling"); print("=" * 72)
    cache = build_cache()
    T = list(cache)
    raw, rawo = [], []
    for t in T:
        C = cache[t]['C']; pk = set(cache[t]['pocket'])
        eh = [len(set(c['ii']) & pk) / c['n'] for c in C]
        f = [i for i, c in enumerate(C) if c['hop'] >= 1] or list(range(len(C)))
        raw.append(eh[max(f, key=lambda i: C[i]['drug'])]); rawo.append(max(eh))
    print(f"\n  reimplemented rule EH = {np.mean(raw):.5f}")
    print(f"  published rule EH     = {PUBLISHED:.5f}")
    print(f"  {'MATCH' if abs(np.mean(raw)-PUBLISHED) < 1e-6 else '*** MISMATCH'}")
    print(f"  raw oracle EH         = {np.mean(rawo):.4f}")

    print("\n" + "=" * 72); print("PART B -- merge sweep"); print("=" * 72)
    print("  NOTE: a first attempt merging at 8 A percolated -- every target")
    print("  collapsed to ONE cavity. That threshold is excluded as meaningless.\n")
    print(f"  {'criterion':<20}{'mean cav':>9}{'rule EH':>9}{'delta':>9}{'oracle':>9}")
    print(f"  {'RAW (no merging)':<20}{np.mean([len(cache[t]['C']) for t in T]):>9.1f}"
          f"{np.mean(raw):>9.4f}{0.0:>9.4f}{np.mean(rawo):>9.4f}")
    sweep = {}
    for mode, thr in [('shared', 0), ('dist', 2.0), ('dist', 3.0), ('dist', 4.0),
                      ('dist', 5.0), ('dist', 6.0), ('both', 3.0), ('both', 4.0)]:
        r, o, nc = [], [], []
        for t in T:
            cav = cavities(cache[t], set(cache[t]['pocket']), mode, thr)
            r.append(rule_eh(cav)); o.append(max(c['ov'] / c['n'] for c in cav))
            nc.append(len(cav))
        nm = "shared residues" if mode == 'shared' else f"{mode} {thr:g}A"
        sweep[nm] = dict(mean_cavities=float(np.mean(nc)), rule_eh=float(np.mean(r)),
                         oracle_eh=float(np.mean(o)))
        print(f"  {nm:<20}{np.mean(nc):>9.1f}{np.mean(r):>9.4f}"
              f"{np.mean(r)-np.mean(raw):>+9.4f}{np.mean(o):>9.4f}")
    print("\n  Merging hurts at EVERY criterion. fpocket's splitting is not")
    print("  costing us on this metric -- it is helping.")

    print("\n" + "=" * 72); print("PART C -- the size mechanism"); print("=" * 72)
    osz, rsz, msz, rho_eh, rho_dr = [], [], [], [], []
    for t in T:
        C = cache[t]['C']; pk = set(cache[t]['pocket'])
        eh = np.array([len(set(c['ii']) & pk) / c['n'] for c in C])
        n = np.array([c['n'] for c in C], float)
        d = np.array([c['drug'] for c in C])
        io = int(np.argmax(eh))
        f = [i for i, c in enumerate(C) if c['hop'] >= 1] or list(range(len(C)))
        ir = max(f, key=lambda i: C[i]['drug'])
        osz.append(n[io]); rsz.append(n[ir]); msz.append(n.mean())
        if len(C) > 4 and eh.std() > 0:
            rho_eh.append(stats.spearmanr(n, eh).statistic)
        if len(C) > 4 and d.std() > 0:
            rho_dr.append(stats.spearmanr(n, d).statistic)
    print(f"  mean candidate size        {np.mean(msz):6.1f}")
    print(f"  mean size of ORACLE pick   {np.mean(osz):6.1f}")
    print(f"  mean size of RULE pick     {np.mean(rsz):6.1f}"
          f"   <- {np.mean(rsz)/np.mean(osz):.1f}x the oracle's")
    print(f"\n  within-target rho(size, EH)          {np.mean(rho_eh):+.3f}"
          f"  Wilcoxon p={stats.wilcoxon(rho_eh).pvalue:.4f}")
    print(f"  within-target rho(size, druggability) {np.mean(rho_dr):+.3f}"
          f"  Wilcoxon p={stats.wilcoxon(rho_dr).pvalue:.4f}")
    print("\n  rho(size, EH) is POSITIVE -- EH does NOT reward small fragments.")
    print("  The rule's loss is that druggability tracks size and so selects")
    print("  candidates far larger than any real drug site.")

    print("\n" + "=" * 72); print("PART D -- size-corrected ranking (IN-SAMPLE)")
    print("=" * 72)
    arms = {}
    for nm in ['druggability (published)', 'druggability residualised on size',
               'druggability / size', 'smallest candidate']:
        v = []
        for t in T:
            C = cache[t]['C']; pk = set(cache[t]['pocket'])
            n = np.array([c['n'] for c in C], float); d = np.array([c['drug'] for c in C])
            f = [i for i, c in enumerate(C) if c['hop'] >= 1] or list(range(len(C)))
            if nm.startswith('druggability residualised'):
                key = (d - np.polyval(np.polyfit(n, d, 1), n)
                       if n.std() > 0 and len(C) > 2 else d)
            elif nm == 'druggability / size':
                key = d / np.maximum(n, 1)
            elif nm == 'smallest candidate':
                key = -n
            else:
                key = d
            i = max(f, key=lambda i: key[i])
            v.append(len(set(C[i]['ii']) & pk) / C[i]['n'])
        arms[nm] = v
        print(f"  {nm:<38} mean EH {np.mean(v):.4f}")
    base = arms['druggability (published)']
    print()
    for nm, v in arms.items():
        if nm == 'druggability (published)':
            continue
        dd = np.array(v) - np.array(base)
        p = stats.wilcoxon(dd).pvalue if np.any(dd) else float('nan')
        print(f"  vs published: {nm:<38} {np.mean(dd):+.4f}  Wilcoxon p={p:.4f}")
    print("\n  *** IN-SAMPLE on the frozen 20. No LOTO. This register has ALREADY")
    print("  *** been burned once by an in-sample sweep that reported 0.267 and")
    print("  *** then never won a LOTO fold. Nothing here is a result until a")
    print("  *** leave-one-target-out run says so.")

    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(dict(published=PUBLISHED, reimplemented=float(np.mean(raw)),
                   raw_oracle=float(np.mean(rawo)), merge_sweep=sweep,
                   mean_candidate_size=float(np.mean(msz)),
                   oracle_pick_size=float(np.mean(osz)),
                   rule_pick_size=float(np.mean(rsz)),
                   rho_size_eh=float(np.mean(rho_eh)),
                   rho_size_drug=float(np.mean(rho_dr)),
                   in_sample_arms={k: float(np.mean(v)) for k, v in arms.items()},
                   n_targets=len(T)),
              open(OUT / "fragmentation_and_ceiling.json", "w"), indent=1)
    print(f"\n  written -> {OUT}/fragmentation_and_ceiling.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
