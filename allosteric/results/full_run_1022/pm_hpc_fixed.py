#!/usr/bin/env python3
"""Run PocketMiner on the todo proteins on a Linux node. Fetch chain PDB, one forward pass,
write <name>.txt (one score per residue) + <name>.resnums.json. Sharded, resumable."""
import os,sys,json,time,urllib.request
sys.path.insert(0,"pocketminer/gvp/src")
import numpy as np, mdtraj as md, tensorflow as tf
from models import MQAModel
from validate_performance_on_xtals import process_strucs, predict_on_xtals
AA3={"ALA","ARG","ASN","ASP","CYS","GLN","GLU","GLY","HIS","ILE","LEU","LYS","MET","PHE","PRO","SER","THR","TRP","TYR","VAL","MSE"}
NN="pocketminer/gvp/models/pocketminer"
SHARD=int(os.environ.get("SHARD","0")); NS=int(os.environ.get("NSHARD","1"))
OUT=os.environ.get("OUT","pm_out"); os.makedirs(OUT,exist_ok=True); os.makedirs("pm_pdb",exist_ok=True)
def chain_pdb(pdb,chain):
    p="pm_pdb/%s_%s.pdb"%(pdb,chain)
    if os.path.exists(p) and os.path.getsize(p)>0: return p
    for a in range(4):
        try:
            with urllib.request.urlopen("https://files.rcsb.org/download/%s.pdb"%pdb,timeout=30) as r: raw=r.read().decode(errors="replace")
            break
        except Exception:
            if a==3: return None
            time.sleep(1.5**a)
    # FIX 1: MSE (selenomethionine) -> MET, SE -> SD, HETATM -> ATOM  (featurizer rejects MSE)
    # FIX 2: keep ONLY residues with a complete backbone N,CA,C,O (featurizer needs exactly 4/residue)
    BB=("N","CA","C","O")
    byres={}; order=[]
    for l in raw.splitlines():
        if l.startswith("ENDMDL"): break
        rec=l[:6].strip(); rn=l[17:20].strip()
        if rec not in ("ATOM","HETATM") or l[21:22]!=chain: continue
        if not (rec=="ATOM" or rn in AA3): continue
        alt=l[16:17]
        if alt not in (" ","A"): continue            # single altloc only
        if rn=="MSE":                                 # selenomethionine -> methionine
            l="ATOM  "+l[6:17]+"MET"+l[20:]
            if l[12:16].strip()=="SE": l=l[:12]+" SD "+l[16:]
        try: k=int(l[22:26])
        except: continue
        at=l[12:16].strip()
        if k not in byres: byres[k]={}; order.append(k)
        if at in BB and at not in byres[k]: byres[k][at]=l
        elif at not in BB: byres[k].setdefault("_side",[]).append(l)
    keep=[]; seen=[]
    for k in order:
        r=byres[k]
        if not all(a in r for a in BB): continue      # drop incomplete-backbone residues
        for a in BB: keep.append(r[a])
        for l in r.get("_side",[]): keep.append(l)
        seen.append(k)
    if not keep: return None
    open(p,"w").write("\n".join(keep)+"\nEND\n"); json.dump(seen,open(p+".rn","w")); return p
_OPT=tf.keras.optimizers.legacy.Adam
def build_model():
    return MQAModel(node_features=(8,50),edge_features=(1,32),hidden_dim=(16,100),num_layers=4,dropout=0.1)
def main():
    todo=json.load(open("pm_todo.json")); todo=[w for i,w in enumerate(todo) if i%NS==SHARD]
    model=build_model()
    t0=time.time(); done=0; err=0
    for k,w in enumerate(todo,1):
        name=w["name"]; out=os.path.join(OUT,name+".txt")
        if os.path.exists(out): continue
        try:
            p=chain_pdb(w["pdb"],w["chain"])
            if not p: err+=1; continue
            rn=json.load(open(p+".rn"))
            strucs=[md.load(p)]
            X,S,mask=process_strucs(strucs)
            pred=predict_on_xtals(model,NN,X,S,mask,opt=_OPT())
            sc=np.asarray(pred)[0].reshape(-1)[:len(rn)]
            if len(sc)!=len(rn): err+=1; continue
            open(out,"w").write("\n".join("%.6f"%x for x in sc))
            json.dump(rn,open(os.path.join(OUT,name+".resnums.json"),"w")); done+=1
        except Exception as e:
            err+=1; sys.stderr.write("%s: %s\n"%(name,e))
        if k%20==0: print("  PM %d/%d done=%d err=%d (%.0fs)"%(k,len(todo),done,err,time.time()-t0),flush=True)
    print("PM DONE shard%d: %d scored, %d err (%.0fs)"%(SHARD,done,err,time.time()-t0),flush=True)
if __name__=="__main__": main()
