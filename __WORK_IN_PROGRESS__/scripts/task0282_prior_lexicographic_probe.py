"""TASK-0282 PROBE (Reviewer, 2026-08-28) -- motivation only, NOT a result.

Bartosz's refinement: in apo, cryptic pockets are low-druggability BY
DEFINITION, so an absolute druggability criterion is meaningless. Order
pockets by DISTANCE first, and use druggability only to rank WITHIN a
distance stratum (0.002 beats 0.001 among equally-distant pockets).
Distance = signal strength; druggability = thermodynamic accessibility.

THIS OVERTURNS TASK-0282's OWN PRE-REGISTERED PRIOR, which claimed no
monotone function could select KRAS's/CARDIAC's true pockets because their
druggability is ~0.001. That assumed druggability used GLOBALLY. It is wrong.

Measured here (expected hits from a random draw inside the selected pocket):

  rule                                       KRAS  BCR_ABL1  CARDIAC   mean
  our residue-ranking deliverable             0.2      0.0      0.0    0.067
  druggability-first + MIN_HOP>=2             0.1      0.7      0.1    0.30
  distance-first, druggability within band    0.80     0.00     0.00   0.267

At excl=2.0 A, bin=1.0 A the lexicographic rule selects KRAS's true pocket --
druggability 0.001, overlap 8/10, exactly the measured ceiling.

BUT the two rules each break the other's target, for a STRUCTURAL reason:

  target          true-pocket min heavy-atom   category      winning ordering
  KRAS_G12C              1.32 A                contact-adj   distance-first
  BCR_ABL1               7.96 A                proximal      druggability-first
  CARDIAC_MYOSIN        11.81 A                proximal      neither

Distance-first demotes BCR-ABL1's correct pocket (14/16 overlap, drug 0.566,
7.96 A) below a nearer decoy (0/9 overlap, drug 0.029, 3.74 A). The two
targets want OPPOSITE orderings. No single lexicographic rule handles both --
not for want of tuning, but because the benchmark's targets have
qualitatively different site geometries (TASK-0258's taxonomy).

*** WARNING FOR WHOEVER OWNS TASK-0282 ***
The 0.267 above is IN-SAMPLE: 28 configurations swept on 3 targets, best
reported. That is exactly the overfitting TASK-0282's own Scope forbids.
Quoted as motivation only. LOTO on the frozen 20 remains the headline
requirement. Recommended additions to that task's design:
  - sweep BOTH orderings and the interpolations (weighted, rank-product),
    not one family;
  - report per-target, never only the mean -- a mean of 0.267 carried
    entirely by KRAS would misrepresent the result completely;
  - add each target's site category as a reported covariate, so the
    ordering-vs-geometry relationship can be confirmed or refuted at n=20
    rather than inferred from three targets.
"""

import sys, warnings, tempfile
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0,'src'); sys.path.insert(0,'scripts'); sys.path.insert(0,'..')
import prody; prody.confProDy(verbosity="none")
from task0255_hop_angstrom_calibration import _parsePDB_all_altloc, min_heavy_atom_dist_to_seed
prody.parsePDB = _parsePDB_all_altloc
from task0242_two_stage_dryrun import prep, fpocket_candidates
from allostery.baselines import hop_from_seed

TARGETS=("KRAS_G12C","BCR_ABL1","CARDIAC_MYOSIN")
store={}
for t in TARGETS:
    cfg, apo, seed, pocket = prep(t)
    resn=np.asarray(apo.resnums); chids=np.asarray(apo.chain_ids)
    true=set(zip(chids[pocket].tolist(), resn[pocket].tolist()))
    # TASK-0298: (chain, resnum) compound key, matching fpocket_candidates'
    # own now-corrected `p["resnums"]` shape. This probe's own 3 targets
    # (KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN) are single-chain and not among
    # the 9 exposed to the value bug, but the bare-int comparisons below
    # would otherwise silently break once `p["resnums"]` is tuples.
    idx_of={(str(c),int(r)):i for i,(c,r) in enumerate(zip(chids,resn))}
    d=min_heavy_atom_dist_to_seed(cfg, apo, seed)          # per-residue min heavy-atom A
    hops=-hop_from_seed(apo.coords, seed, cutoff=float(cfg.get("enm_cutoff",8.0)))
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp); ch=cfg.get("apo_chains") or cfg.get("chains")
        ag=prody.parsePDB(cfg["apo_pdb"],compressed=False).select("protein and ("+" or ".join(f"chain {c}" for c in ch)+")")
        pdb=tmp/f"{t.lower()}.pdb"; prody.writePDB(str(pdb),ag)
        pk=fpocket_candidates(pdb,tmp)
    cands=[]
    for p in pk:
        ii=[idx_of[r] for r in p["resnums"] if r in idx_of]
        if not ii: continue
        rs=set(p["resnums"])&set(zip(chids.tolist(),resn.tolist()))
        dd=d[ii]; dd=dd[np.isfinite(dd)]
        if len(dd)==0: continue
        cands.append({"drug":p.get("druggability_score") or 0.0,"res":rs,
                      "minA":float(dd.min()),"minhop":float(np.min(hops[ii])),
                      "ov":len(rs&true),"n":len(rs)})
    store[t]=(cands,len(true))

def run(excl_A, bin_A):
    out={}
    for t,(cands,ntrue) in store.items():
        c=[x for x in cands if x["minA"]>=excl_A]
        if not c: out[t]=(None,0.0); continue
        # lexicographic: distance stratum ascending, then druggability descending
        c.sort(key=lambda x:(round(x["minA"]/bin_A), -x["drug"]))
        top=c[0]; out[t]=(top, top["ov"]/top["n"] if top["n"] else 0.0)
    return out

print("orthosteric-exclusion cutoff x distance-stratum width -> expected P@5 per target")
print(f"{'excl_A':>7}{'bin_A':>7} | "+" ".join(f"{t[:9]:>10}" for t in TARGETS)+"   mean")
best=None
for excl in (0.0,2.0,3.0,4.0,5.0,6.0,8.0):
    for binw in (1.0,2.0,3.0,5.0):
        r=run(excl,binw); vals=[r[t][1] for t in TARGETS]
        m=float(np.mean(vals))
        if best is None or m>best[0]: best=(m,excl,binw,r)
        print(f"{excl:>7.1f}{binw:>7.1f} | "+" ".join(f"{v:>10.2f}" for v in vals)+f"   {m:.3f}")
print(f"\nbest: excl={best[1]} A, bin={best[2]} A, mean expected P@5={best[0]:.3f}")
for t in TARGETS:
    top,v=best[3][t]
    if top: print(f"   {t:<16} P@5={v:.2f}  chosen pocket: drug={top['drug']:.3f} minA={top['minA']:.2f} overlap={top['ov']}/{top['n']}")
print("\nfor reference -- our residue-ranking deliverable: 0.2 / 0.0 / 0.0  (mean 0.067)")
