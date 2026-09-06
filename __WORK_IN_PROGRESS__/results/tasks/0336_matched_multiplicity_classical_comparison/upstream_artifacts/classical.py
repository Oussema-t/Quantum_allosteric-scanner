#!/usr/bin/env python3
"""Classical pocket-ranking baselines, same PASSer-top-10 pockets, same truth, same P@5 metric as the
CTQW. Per protein rank pockets by each classical score; report families cleared. No quantum walk."""
import json,os,glob,time,urllib.request,numpy as np,importlib.util
os.environ["SELECTOR"]="passer_only"
spec=importlib.util.spec_from_file_location("ps","pocketsweep.py"); ps=importlib.util.module_from_spec(spec)
try: spec.loader.exec_module(ps)
except SystemExit: pass
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra, shortest_path
CACHE="cl_pdb"; os.makedirs(CACHE,exist_ok=True)
AA3={"ALA","ARG","ASN","ASP","CYS","GLN","GLU","GLY","HIS","ILE","LEU","LYS","MET","PHE","PRO","SER","THR","TRP","TYR","VAL","MSE"}
def fetch(pid):
    p=os.path.join(CACHE,pid+".pdb")
    if os.path.exists(p) and os.path.getsize(p)>0: return p
    for a in range(3):
        try:
            with urllib.request.urlopen("https://files.rcsb.org/download/%s.pdb"%pid,timeout=25) as r,open(p+".t","wb") as f: f.write(r.read())
            os.replace(p+".t",p); return p
        except Exception: time.sleep(1.3**a)
    return None
def ca(path,chain):
    ch={}; 
    for l in open(path,errors="replace"):
        if l.startswith("ENDMDL"): break
        if l[:6].strip() not in ("ATOM","HETATM"): continue
        if l[:6].strip()=="HETATM" and l[17:20].strip() not in AA3: continue
        if l[12:16].strip()!="CA": continue
        c=l[21]
        try: ch.setdefault(c,[]).append((int(l[22:26]),[float(l[30:38]),float(l[38:46]),float(l[46:54])]))
        except: pass
    if not ch: return None,None
    c=chain if chain in ch else max(ch,key=lambda k:len(ch[k]))
    seen={}; out=[]
    for r,xyz in ch[c]:
        if r not in seen: seen[r]=len(out); out.append((r,xyz))
    return {r:i for i,(r,_) in enumerate(out)}, np.array([x for _,x in out],float)
def main():
    W={w["name"]:w for w in json.load(open("operator_worklist.json"))}
    r1={}
    for f in sorted(glob.glob("full_r1_*.json")): r1.update(json.load(open(f)))
    testable=[n for n,v in r1.items() if "cells" in v]
    res={}; t0=time.time()
    for k,n in enumerate(testable,1):
        w=W[n]
        try:
            p=fetch(w["pdb"]); 
            if not p: continue
            idx,X=ca(p,w["chain"])
            if idx is None: continue
            A=[idx[r] for r in w["active"] if r in idx]; T=set(idx[r] for r in w["truth"] if r in idx)
            if not A or not T: continue
            pk=ps.passer_only_pockets(w["pdb"],w["chain"],10,{r:1 for r in range(1,6000)})
            if len(pk)<4: continue
            act=max(pk,key=lambda q:len({idx[r] for r in q["residues"] if r in idx}&set(A)))["id"]
            P=[q for q in pk if q["id"]!=act]
            mem=[[idx[r] for r in q["residues"] if r in idx] for q in P]
            keep=[i for i,m in enumerate(mem) if m]; P=[P[i] for i in keep]; mem=[mem[i] for i in keep]
            if len(P)<3: continue
            y=np.array([1 if len(set(m)&T)>0 else 0 for m in mem])
            if y.sum()==0 or y.sum()==len(y): continue
            D2=((X[:,None,:]-X[None,:,:])**2).sum(-1); adj=csr_matrix(((D2<100)&(D2>0)).astype(np.int8))
            hop=dijkstra(adj,directed=False,indices=A,unweighted=True,min_only=True)
            deg=np.asarray(((D2<100)&(D2>0)).sum(1)).ravel()
            # classical per-pocket scores (higher = better pocket)
            sc={}
            sc["proximity(-hop)"]=np.array([-np.mean([hop[i] for i in m if np.isfinite(hop[i])] or [1e9]) for m in mem])
            sc["degree"]=np.array([np.mean([deg[i] for i in m]) for m in mem])
            sc["pocket_size"]=np.array([len(m) for m in mem],float)
            sc["fpocket_drug"]=np.array([q["drug"] for q in P])   # PASSer prob stored as 'drug' here (allostery)
            sc["passer_rank"]=np.array([-q["rk_pa"] for q in P],float)
            out={}
            for name,s in sc.items():
                o=np.argsort(-s); out[name]=float(y[o[:5]].sum())/5.0
            res[n]=dict(p5=out,cluster=w["cluster"],is_distal=w["is_distal"])
        except Exception as e: pass
        if k%80==0: json.dump(res,open("classical.json","w")); print("  %d/%d (%.0fs)"%(k,len(testable),time.time()-t0),flush=True)
    json.dump(res,open("classical.json","w")); print("DONE %d proteins (%.0fs)"%(len(res),time.time()-t0),flush=True)
if __name__=="__main__": main()
