"""TASK-0297 -- chain-agnostic residue matching: which committed numbers move?

Raised by the external distal-pockets session (`.ai/reviews/2026-08-29 -
distal pockets`, HANDOVER v3 §5 defects 6 and 7). Both are defects in
THIS repo, not that session's, and both are confirmed here.

DEFECT 1 -- `fpocket_candidates` (`task0242_two_stage_dryrun.py`) parses
pocket residues as `int(line[22:26])`, discarding the chain. Consumers
then build `idx_of = {int(r): i for i, r in enumerate(resn)}`, which for
a multi-chain selection keeps only the LAST chain's index per residue
number.

DEFECT 2 -- the same class, in the SEED. `prep()` builds the active site
with `np.isin(apo.resnums, detected_active_site)`, which spreads the
active site detected for ONE chain onto EVERY configured chain.

Defect 2 is NOT uniformly wrong, and that distinction is the whole point:

  HOMO-oligomer  -- every chain genuinely has its own active site at the
                    same residue numbers. Spreading is CORRECT. Restricting
                    to the detection chain would DISCARD a real active site.
  HETERO-oligomer -- residue 49 of chain A is a different residue from 49
                    of chain B. Spreading is nonsense.

So each affected target is classified by querying the RCSB polymer-entity
descriptions, and only the hetero cases are corrected. Naively "fixing"
all of them would corrupt five targets that are currently right.

Run: ../.venv/bin/python3 scripts/task0297_chain_aware_seed_and_fpocket_audit.py
"""
import sys, json, warnings
from collections import defaultdict
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0, 'src'); sys.path.insert(0, 'scripts'); sys.path.insert(0, '..')
import prody; prody.confProDy(verbosity="none")
from task0255_hop_angstrom_calibration import _parsePDB_all_altloc
prody.parsePDB = _parsePDB_all_altloc
import yaml
from scipy import stats
from task0242_two_stage_dryrun import prep, CAND
import task0255_hop_angstrom_calibration as t0255
from backend.data_layer import fetch
from backend.rcsb import _get_json, DATA_API
CAND.update(yaml.safe_load(open('config/candidate_targets_task0243.yaml'))['targets'])

OUT = Path("results/tasks/0297_chain_aware_audit")
TAX = [r['target'] for r in json.load(open(
    'results/tasks/0258_allosteric_distance_taxonomy/pocket_taxonomy.json'))
    if 'error' not in r]


def cfg_of(t):
    return dict(CAND[t]) if t in CAND else None


def entity_kind(pdb_id, chains):
    """HOMO if every configured chain is the same polymer entity."""
    d = _get_json(f"{DATA_API}/entry/{pdb_id}")
    if not d:
        return "unknown", {}
    ids = (d.get('rcsb_entry_container_identifiers') or {}).get('polymer_entity_ids') or []
    names = {}
    for e in ids:
        ed = _get_json(f"{DATA_API}/polymer_entity/{pdb_id}/{e}")
        if not ed:
            continue
        nm = ((ed.get('rcsb_polymer_entity') or {}).get('pdbx_description') or '?')
        for a in ((ed.get('rcsb_polymer_entity_container_identifiers') or {})
                  .get('auth_asym_ids') or []):
            names[a] = nm
    got = {c: names.get(c, '?') for c in chains}
    present = [v for v in got.values() if v != '?']
    kind = "hetero" if len(set(present)) > 1 else ("homo" if present else "unknown")
    return kind, got


def main():
    print("=" * 74)
    print("STEP 1 -- which targets are exposed to chain-agnostic matching?")
    print("=" * 74)
    exposed = []
    for t in TAX:
        c = cfg_of(t)
        if not c:
            continue
        ach = c.get('apo_chains') or c.get('chains') or []
        if len(ach) < 2:
            continue
        ch = defaultdict(set)
        for line in Path(fetch(c['apo_pdb'])).read_text().splitlines():
            if line.startswith("ATOM"):
                ch[line[21]].add(line[22:27].strip())
        present = [x for x in ach if x in ch]
        missing = [x for x in ach if x not in ch]
        ov = set()
        for i in range(len(present)):
            for j in range(i + 1, len(present)):
                ov |= (ch[present[i]] & ch[present[j]])
        if ov or missing:
            exposed.append(dict(target=t, apo=c['apo_pdb'], chains=ach,
                                collisions=len(ov), missing=missing))
            print(f"  {t:<22}{c['apo_pdb']:<6}{','.join(ach):<10}"
                  f"{len(ov):>6} colliding resnums"
                  + (f"   MISSING CHAIN {','.join(missing)}" if missing else ""))
    print(f"\n  {len(exposed)} of {len(TAX)} targets exposed.")

    print("\n" + "=" * 74)
    print("STEP 2 -- homo or hetero? Spreading is CORRECT for homo-oligomers.")
    print("=" * 74)
    for e in exposed:
        kind, got = entity_kind(e['apo'], e['chains'])
        e['kind'] = kind
        tag = "*** HETERO -- spreading is WRONG" if kind == "hetero" else \
              ("homo -- spreading is CORRECT" if kind == "homo" else "unknown")
        print(f"  {e['target']:<22}{e['apo']:<6}{tag}")
        for c, n in got.items():
            print(f"        chain {c}: {n[:60]}")

    print("\n" + "=" * 74)
    print("STEP 3 -- does the seed defect move min_A? (hetero targets only)")
    print("=" * 74)
    moves = []
    for e in exposed:
        if e['kind'] != 'hetero':
            continue
        t = e['target']
        try:
            cfg, apo, seed, pocket = prep(t)
            ch = np.asarray(apo.chain_ids)
            det = (cfg.get("apo_chains") or cfg.get("chains"))[0]
            pi = np.where(pocket)[0]
            cur = float(np.nanmin(t0255.min_heavy_atom_dist_to_seed(cfg, apo, seed)[pi]))
            keep = np.zeros(len(ch), bool); keep[seed] = True; keep &= (ch == det)
            s2 = np.where(keep)[0]
            if len(s2) == 0:
                print(f"  {t:<22} seed vanishes under chain restriction -- skipped")
                continue
            new = float(np.nanmin(t0255.min_heavy_atom_dist_to_seed(cfg, apo, s2)[pi]))
            e.update(min_A_committed=cur, min_A_corrected=new)
            moves.append(e)
            flag = "  <== MOVES" if abs(new - cur) > 0.05 else ""
            if (cur < 1.5) != (new < 1.5):
                flag += "  *** CROSSES THE SPIKE BOUNDARY"
            print(f"  {t:<22} min_A {cur:6.2f} -> {new:6.2f}"
                  f"   n_seed {len(seed)} -> {len(s2)}{flag}")
        except Exception as ex:
            print(f"  {t:<22} [err] {type(ex).__name__}: {ex}")

    print("\n" + "=" * 74)
    print("STEP 4 -- Finding F, recomputed")
    print("=" * 74)
    d84 = json.load(open('results/tasks/0284_two_populations/bimodality_and_nulls.json'))
    g = {}
    for r in d84['rows']:
        if 'N' in r and r.get('min_A') is not None:
            g.setdefault((r['N'], round(r['Rg'], 2)), r)
    S = list(g.values())
    y = np.array([r['min_A'] for r in S]); names = [r['target'] for r in S]
    corr = {m['target']: m['min_A_corrected'] for m in moves
            if abs(m['min_A_corrected'] - m['min_A_committed']) > 0.05}

    def rep(v, lab):
        vs = np.sort(v); sp = vs[vs < 1.5]
        lo = np.log(vs); mu, sd = lo.mean(), lo.std(ddof=1)
        pw = (stats.norm.cdf(np.log(1.5), mu, sd)
              - stats.norm.cdf(np.log(1.25), mu, sd))
        p = float(stats.binom.sf(len(sp) - 1, len(vs), pw))
        print(f"  {lab:<36} spike {len(sp)}/{len(vs)}  binomial p = {p:.3e}")
        return len(sp), p
    n0, p0 = rep(y, "committed")
    y2 = np.array([corr.get(n, v) for n, v in zip(names, y)])
    n1, p1 = rep(y2, "corrected (hetero targets only)")
    print("\n  spike membership after correction:")
    for n, v in sorted(zip(names, y2), key=lambda x: x[1]):
        if v < 1.5:
            print(f"    {n:<22}{v:6.3f}")

    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(dict(exposed=exposed, seed_moves=moves,
                   finding_f_committed=dict(spike=n0, p=p0),
                   finding_f_corrected=dict(spike=n1, p=p1),
                   corrections=corr),
              open(OUT / "chain_aware_audit.json", "w"), indent=1)
    print(f"\n  written -> {OUT}/chain_aware_audit.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
