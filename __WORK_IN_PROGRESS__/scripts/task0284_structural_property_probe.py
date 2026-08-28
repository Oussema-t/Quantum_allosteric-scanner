"""What distinguishes proteins whose allosteric pocket is DISTAL from those
whose pocket is contact-adjacent? Exploratory, multiple-comparison corrected.

Candidate structural properties, all computable from the apo structure alone:
  N              chain length
  Rg             radius of gyration
  compactness    Rg / N^(1/3)   (deviation from ideal globular scaling)
  helix_frac     fraction of residues in HELIX records
  sheet_frac     fraction in SHEET records
  lambda1        first non-trivial GNM eigenvalue -- global stiffness
  contact_order  mean |i-j| over contacts / N -- fold topology
  mean_degree    mean contacts per residue -- packing density
"""
import sys, json, warnings
import numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0,'src'); sys.path.insert(0,'scripts'); sys.path.insert(0,'..')
import prody; prody.confProDy(verbosity="none")
from task0255_hop_angstrom_calibration import _parsePDB_all_altloc
prody.parsePDB = _parsePDB_all_altloc
import yaml
from task0242_two_stage_dryrun import prep, CAND
CAND.update(yaml.safe_load(open('config/candidate_targets_task0243.yaml'))['targets'])
from allostery.hamiltonians import contact_matrix
from scipy import stats

tax={r['target']:r for r in json.load(open('results/tasks/0258_allosteric_distance_taxonomy/pocket_taxonomy.json')) if 'error' not in r}

rows=[]
for t,rec in tax.items():
    try:
        cfg,apo,seed,pocket=prep(t)
    except Exception:
        continue
    c=apo.coords; N=len(c); cut=float(cfg.get("enm_cutoff",8.0))
    A=contact_matrix(c,cutoff=cut,weight="binary")
    deg=A.sum(1)
    # Kirchhoff -> first non-trivial eigenvalue (global stiffness)
    K=np.diag(deg)-A
    ev=np.linalg.eigvalsh(K)
    lam1=float(ev[1]) if len(ev)>1 else np.nan
    # contact order
    ii,jj=np.nonzero(np.triu(A,1))
    co=float(np.mean(np.abs(ii-jj))/N) if len(ii) else np.nan
    Rg=float(np.sqrt(((c-c.mean(0))**2).sum(1).mean()))
    # secondary structure from PDB HELIX/SHEET header records
    hf=sf=np.nan
    try:
        ag=prody.parsePDB(cfg["apo_pdb"],compressed=False,secondary=True)
        ss=ag.select("name CA").getSecstrs()
        ss=np.array([s if s else 'C' for s in ss])
        hf=float(np.mean(np.isin(ss,['H','G','I']))); sf=float(np.mean(np.isin(ss,['E','B'])))
    except Exception:
        pass
    rows.append(dict(target=t,minA=rec['min_A'],cat=rec['category'],N=N,Rg=Rg,
                     compactness=Rg/N**(1/3),helix=hf,sheet=sf,lam1=lam1,
                     contact_order=co,mean_degree=float(deg.mean())))
json.dump(rows,open('/tmp/props.json','w'),indent=1)

props=['N','Rg','compactness','helix','sheet','lam1','contact_order','mean_degree']
ok=[r for r in rows if np.isfinite(r['minA'])]
print(f"n={len(ok)} targets\n")
print(f"{'property':<16}{'rho vs min_A':>14}{'p':>9}   {'distal mean':>12}{'adj mean':>10}{'MWU p':>9}")
res=[]
for pr in props:
    v=[r[pr] for r in ok]; a=[r['minA'] for r in ok]
    m=[i for i,x in enumerate(v) if np.isfinite(x)]
    if len(m)<8: print(f"{pr:<16}  insufficient data"); continue
    vv=[v[i] for i in m]; aa=[a[i] for i in m]
    s=stats.spearmanr(vv,aa)
    dis=[r[pr] for r in ok if r['cat'] in ('intermediate','remote') and np.isfinite(r[pr])]
    adj=[r[pr] for r in ok if r['cat']=='contact-adjacent' and np.isfinite(r[pr])]
    u=stats.mannwhitneyu(dis,adj).pvalue if dis and adj else np.nan
    res.append((pr,s.pvalue,u))
    print(f"{pr:<16}{s.statistic:>+14.3f}{s.pvalue:>9.4f}   {np.mean(dis):>12.3f}{np.mean(adj):>10.3f}{u:>9.4f}")
print(f"\n  {len(props)} properties tested -> Bonferroni alpha = {0.05/len(props):.4f}")
sig=[r for r in res if min(r[1],r[2])<0.05/len(props)]
print(f"  surviving correction: {[r[0] for r in sig] if sig else 'NONE'}")
