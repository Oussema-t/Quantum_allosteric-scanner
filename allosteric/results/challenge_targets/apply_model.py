#!/usr/bin/env python3
"""Apply the trained recommender to KRAS_G12C, BCR_ABL1 and HIV1_RT.
Topology features are computed from each APO structure (8 A Ca contact graph) -- exactly the
9 features the model was trained on. These three targets are NOT in the 630-protein training set,
so this is a genuine held-out application."""
import json,sys,numpy as np,networkx as nx
sys.path.insert(0,"/Users/t/Quantum_allosteric-scanner/allosteric/results/ml_model")
from recommender import Recommender,feasible_min_hops
AA3={"ALA","ARG","ASN","ASP","CYS","GLN","GLU","GLY","HIS","ILE","LEU","LYS","MET","PHE","PRO","SER","THR","TRP","TYR","VAL","MSE"}
def ca(path,chain):
    out={}
    for l in open(path,errors="replace"):
        if l.startswith("ENDMDL"): break
        rec=l[:6].strip(); rn=l[17:20].strip()
        if rec not in ("ATOM","HETATM") or rn not in AA3 or l[21:22]!=chain: continue
        if l[12:16].strip()!="CA": continue
        try: k=int(l[22:26])
        except ValueError: continue
        if k not in out: out[k]=[float(l[30:38]),float(l[38:46]),float(l[46:54])]
    r=sorted(out); return np.array([out[k] for k in r]),r
def topo_features(X,cut=8.0):
    """the 9 features the model expects, computed the same way as topology_features.json"""
    D=np.sqrt(((X[:,None,:]-X[None,:,:])**2).sum(-1)); A=(D<cut)&(D>0)
    G=nx.from_numpy_array(A.astype(int)); n=len(X); deg=A.sum(1).astype(float)
    L=np.diag(deg)-A.astype(float)
    ev=np.linalg.eigvalsh(L); ev.sort()
    cc=max(nx.connected_components(G),key=len)
    return dict(n_residues=float(n),n_edges=float(A.sum()//2),mean_degree=float(deg.mean()),
        degree_var=float(deg.var()),degree_cv=float(deg.std()/(deg.mean()+1e-9)),
        clustering_coefficient=float(nx.average_clustering(G)),
        graph_diameter=float(nx.diameter(G.subgraph(cc))),
        algebraic_connectivity=float(ev[1]),
        spectral_radius=float(np.abs(np.linalg.eigvalsh(A.astype(float))).max()))
T=json.load(open("challenge_targets.json"))
rec=Recommender.load("/Users/t/Quantum_allosteric-scanner/allosteric/results/ml_model/recommender.joblib")
print("Model trained on %d proteins / %d families. These 3 targets are NOT in it.\n"%(rec.meta["n_proteins"],rec.meta["n_families"]))
out={}
for name,t in T.items():
    X,resn=ca("pdb_cache/%s.pdb"%t["pdb"],t["chain"])
    f=topo_features(X)
    idxmap={r:i for i,r in enumerate(resn)}
    A=[idxmap[r] for r in t["active"] if r in idxmap]
    feas=feasible_min_hops(X,A)
    cfg=rec.recommend(f,k=6,feasibility=feas)
    out[name]=dict(topology=f,recommendations=cfg,target=t)
    print("="*74)
    print("%s  (apo %s chain %s, %d residues)"%(name,t["pdb"],t["chain"],len(resn)))
    print("  topology: n_res %.0f | edges %.0f | mean_deg %.1f | diameter %.0f | alg_conn %.4f | spec_rad %.1f"%(
        f["n_residues"],f["n_edges"],f["mean_degree"],f["graph_diameter"],f["algebraic_connectivity"],f["spectral_radius"]))
    print("  MIN_HOP feasibility (from the apo structure + active site, no truth used):")
    for H in (1,2,3,4):
        d=feas[H]
        print("    MIN_HOP=%d  %4d candidates (%2.0f%% of protein)  max_hop=%.0f  -> %-8s %s"%(
            H,d["n_candidates"],100*d["frac"],d["max_hop"],"OK" if d["feasible"] else "REJECTED",
            "" if d["feasible"] else d["reason"]))
    print("  MODEL RECOMMENDS (k=6, infeasible MIN_HOP removed):")
    print("    %-5s %-8s %-14s %-20s %8s"%("rank","MIN_HOP","Hamiltonian","score","weight"))
    for c in cfg:
        print("    %-5d %-8d %-14s %-20s %8.3f"%(c["rank"],c["min_hop"],c["hamiltonian"],c["score"],c["weight"]))
    hops=sorted({c["min_hop"] for c in cfg})
    print("  -> MIN_HOP values to run: %s | distinct Hamiltonians: %d | distinct scores: %d"%(
        hops,len({c["hamiltonian"] for c in cfg}),len({c["score"] for c in cfg})))
json.dump(out,open("target_recommendations.json","w"),indent=1)
print("\nwrote target_recommendations.json")
