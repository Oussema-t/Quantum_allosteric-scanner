#!/usr/bin/env python3
"""On the node: from PocketMiner outputs (pm_out/) + apo-ligand contacts, build veto_keep for the
750 new proteins, MERGED with the existing veto_keep.json (138). PASSer pockets + median PM split +
apo-ligand protection. Writes veto_full.json (protein -> {'10':[kept ids]})."""
import os,json,glob,numpy as np,importlib.util
os.environ["SELECTOR"]="passer_only"
spec=importlib.util.spec_from_file_location("ps","pocketsweep.py"); ps=importlib.util.module_from_spec(spec)
try: spec.loader.exec_module(ps)
except SystemExit: pass
AA3={"ALA","ARG","ASN","ASP","CYS","GLN","GLU","GLY","HIS","ILE","LEU","LYS","MET","PHE","PRO","SER","THR","TRP","TYR","VAL","MSE"}
JUNK=set("HOH SO4 PO4 GOL EDO PEG PGE MPD ACT CL NA K MG CA ZN MN FE NI CD CU TRS EPE IMD DMS FMT ACY BME NO3 CIT TLA MES BTB IOD BR CO SR CS NH4 AZI 1PE P6G PE4 PGO BOG LDA OCT SIN MLI SCN F UNX UNL".split())
def pm(name):
    t="pm_out/%s.txt"%name; j="pm_out/%s.resnums.json"%name
    if not(os.path.exists(t) and os.path.exists(j)): return None
    sc=[float(x) for x in open(t).read().split()]; rn=json.load(open(j))
    return dict(zip(rn,sc)) if len(sc)==len(rn) else None
def lig(pdb,chain,cut=4.5):
    p="pm_pdb/%s_%s.pdb"%(pdb,chain)
    if not os.path.exists(p): return set()
    P=[];L=[]
    for l in open(p,errors="replace"):
        rec=l[:6].strip(); rn=l[17:20].strip()
        try:
            if (rec=="ATOM" or (rec=="HETATM" and rn in AA3)): P.append((int(l[22:26]),float(l[30:38]),float(l[38:46]),float(l[46:54])))
            elif rec=="HETATM" and rn not in JUNK: L.append((float(l[30:38]),float(l[38:46]),float(l[46:54])))
        except: pass
    if not P or not L: return set()
    Pa=np.array([[a,b,c] for _,a,b,c in P]); La=np.array(L); rid=np.array([r for r,_,_,_ in P])
    return set(rid[(np.sqrt(((Pa[:,None,:]-La[None,:,:])**2).sum(-1))<cut).any(1)].tolist())
W=[w for w in json.load(open("pm_todo.json"))]
V=json.load(open("veto_keep.json")) if os.path.exists("veto_keep.json") else {}
for w in W:
    p=pm(w["name"])
    if p is None: continue
    lc=lig(w["pdb"],w["chain"])
    for K in (10,):
        pk=ps.passer_only_pockets(w["pdb"],w["chain"],K,{r:1 for r in range(1,6000)})
        if len(pk)<4: continue
        A=set(w["active"]); act=max(pk,key=lambda q:len(set(q["residues"])&A))["id"]
        pk=[q for q in pk if q["id"]!=act]
        acc=np.array([np.mean([p[r] for r in q["residues"] if r in p]) if any(r in p for r in q["residues"]) else -1e9 for q in pk])
        keep=(acc>=np.median(acc)) | np.array([len(set(q["residues"])&lc)>0 for q in pk])
        V.setdefault(w["name"],{})[str(K)]=[q["id"] for q,k in zip(pk,keep) if k]
json.dump(V,open("veto_full.json","w"))
print("veto_full.json: %d proteins"%len(V))
