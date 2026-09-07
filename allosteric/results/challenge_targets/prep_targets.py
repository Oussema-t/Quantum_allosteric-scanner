#!/usr/bin/env python3
"""Stage 1 — derive the ACTIVE site and the TRUTH allosteric pocket for the challenge targets,
from the structures themselves. No hand-typed residue lists.

truth  : apo residues whose Ca aligns to a holo residue with any heavy atom within 4.5 A of the
         allosteric drug ligand (apo->holo mapping by sequence alignment).
active : apo residues near the functional/orthosteric ligand (or a curated list where the
         functional site is not marked by a ligand, e.g. HIV1_RT)."""
import json,os,urllib.request,numpy as np
from Bio import Align
AA3={"ALA","ARG","ASN","ASP","CYS","GLN","GLU","GLY","HIS","ILE","LEU","LYS","MET","PHE","PRO","SER","THR","TRP","TYR","VAL","MSE"}
THREE2ONE={"ALA":"A","ARG":"R","ASN":"N","ASP":"D","CYS":"C","GLN":"Q","GLU":"E","GLY":"G","HIS":"H","ILE":"I",
 "LEU":"L","LYS":"K","MET":"M","MSE":"M","PHE":"F","PRO":"P","SER":"S","THR":"T","TRP":"W","TYR":"Y","VAL":"V"}
TARGETS={
 "KRAS_G12C":dict(apo="4LDJ",apo_chain="A",holo="6OIM",holo_chain="A",drug="MOV",func=["GDP"]),
 "BCR_ABL1" :dict(apo="1OPL",apo_chain="A",holo="5MO4",holo_chain="A",drug="AY7",func=["NIL"]),
 "HIV1_RT"  :dict(apo="1DLO",apo_chain="A",holo="3V81",holo_chain="A",drug="NVP",func=[],active_curated=[110,185,186]),
}
def fetch(pid):
    p="pdb_cache/%s.pdb"%pid
    if os.path.exists(p) and os.path.getsize(p)>0: return p
    with urllib.request.urlopen("https://files.rcsb.org/download/%s.pdb"%pid,timeout=60) as r:
        open(p,"wb").write(r.read())
    return p
def parse(path,chain):
    """returns resnum->(resname, Ca xyz), and heavy atoms per residue, and hetatm ligands"""
    ca={}; heavy={}; lig={}
    for l in open(path,errors="replace"):
        if l.startswith("ENDMDL"): break
        rec=l[:6].strip(); rn=l[17:20].strip(); c=l[21:22]
        if rec=="HETATM" and rn not in AA3 and rn!="HOH":
            try: lig.setdefault(rn,[]).append([float(l[30:38]),float(l[38:46]),float(l[46:54])])
            except ValueError: pass
            continue
        if c!=chain or rec not in ("ATOM","HETATM") or rn not in AA3: continue
        try: k=int(l[22:26]); xyz=[float(l[30:38]),float(l[38:46]),float(l[46:54])]
        except ValueError: continue
        if l[12:16].strip()=="CA" and k not in ca: ca[k]=(rn,xyz)
        if l[76:78].strip()!="H": heavy.setdefault(k,[]).append(xyz)
    return ca,heavy,lig
def contacts(heavy,ligxyz,cut=4.5):
    if not ligxyz: return set()
    L=np.array(ligxyz); out=set()
    for r,ats in heavy.items():
        A=np.array(ats)
        if (np.sqrt(((A[:,None,:]-L[None,:,:])**2).sum(-1))<cut).any(): out.add(r)
    return out
def seqmap(ca_a,ca_b):
    """map holo resnum -> apo resnum by global sequence alignment of the two Ca chains"""
    ra=sorted(ca_a); rb=sorted(ca_b)
    sa="".join(THREE2ONE.get(ca_a[r][0],"X") for r in ra); sb="".join(THREE2ONE.get(ca_b[r][0],"X") for r in rb)
    al=Align.PairwiseAligner(mode="global",open_gap_score=-10,extend_gap_score=-0.5,substitution_matrix=None,
                             match_score=2,mismatch_score=-1)
    a=al.align(sa,sb)[0]
    m={}
    for (s1,e1),(s2,e2) in zip(a.aligned[0],a.aligned[1]):
        for k in range(e1-s1): m[rb[s2+k]]=ra[s1+k]
    return m
out={}
for name,T in TARGETS.items():
    pa=fetch(T["apo"]); ph=fetch(T["holo"])
    ca_a,hv_a,lig_a=parse(pa,T["apo_chain"]); ca_h,hv_h,lig_h=parse(ph,T["holo_chain"])
    if T["drug"] not in lig_h:
        print("%-10s DRUG %s NOT FOUND in %s. ligands present: %s"%(name,T["drug"],T["holo"],sorted(lig_h)[:12])); continue
    truth_h=contacts(hv_h,lig_h[T["drug"]])
    m=seqmap(ca_a,ca_h)
    truth=sorted({m[r] for r in truth_h if r in m})
    if T.get("active_curated"): active=[r for r in T["active_curated"] if r in ca_a]
    else:
        act=set()
        for f in T["func"]:
            if f in lig_a: act |= contacts(hv_a,lig_a[f])
            elif f in lig_h: act |= {m[r] for r in contacts(hv_h,lig_h[f]) if r in m}
        active=sorted(act)
    print("%-10s apo %s(%s) %d res | holo %s(%s) | drug %s -> %d holo contacts -> %d mapped to apo | active %d"%(
        name,T["apo"],T["apo_chain"],len(ca_a),T["holo"],T["holo_chain"],T["drug"],len(truth_h),len(truth),len(active)))
    out[name]=dict(name=name,pdb=T["apo"],chain=T["apo_chain"],active=active,truth=truth,
                   cluster=name,is_distal=None,holo=T["holo"],drug=T["drug"],n_apo_res=len(ca_a))
json.dump(out,open("challenge_targets.json","w"),indent=1)
print("\nwrote challenge_targets.json")
