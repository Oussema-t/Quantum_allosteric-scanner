"""Synthetic controls for persistent-H2 void detection, ground truth known.
POS: a hollow spherical shell -> one dominant H2 void; shell residues line it,
     AND neighbouring shell residues form a contact clique (graph-NEAR) --
     this is the case the graph-openness premise (TASK-0143) would MISS but
     H2 detects, the exact point of implementing this separately.
NEG: a solid ball (filled) -> no persistent void; method must return ~0.
CRYPTIC: a globular 'protein' with a carved internal cavity; cavity-lining
     residues are the label. Tests recovery of a real capped pocket.
"""
import numpy as np, sys; sys.path.insert(0,'src')
from allostery import persistent_voids as PV
from allostery import metrics, baselines
from allostery.hamiltonians import contact_matrix
import networkx as nx
from scipy.stats import spearmanr
rng = np.random.default_rng(3)

def report(name, coords, label=None, seed=None):
    topp = PV.top_h2_persistence(coords, thresh=18.0)
    print(f"[{name}] N={len(coords)}  top H2 persistence = {topp:.3f}")
    if label is None:
        return
    sc = PV.void_score(coords, thresh=18.0, top_k=1)
    a = metrics.auc(sc, label)
    print(f"    void_score AUC(cavity residues) = {a:.3f}")
    # graph-hop among pocket residues: are they graph-NEAR? (the openness premise's target)
    A = contact_matrix(coords, cutoff=10.0, weight="binary"); G = nx.from_numpy_array(A)
    pk = np.where(label==1)[0]
    if len(pk) > 1 and nx.is_connected(G.subgraph(pk).copy() if nx.is_connected(G) else G):
        try:
            hops = [nx.shortest_path_length(G, int(a_), int(b_))
                    for i,a_ in enumerate(pk) for b_ in pk[i+1:]]
            print(f"    pocket internal mean graph-hop = {np.mean(hops):.2f} "
                  f"(low => graph-NEAR => openness premise would MISS it)")
        except Exception as e:
            print(f"    (hop calc skipped: {e})")
    # compare to proximity floor if a seed is given
    if seed is not None:
        fl = baselines.euclid_from_seed_centroid(coords, seed)
        print(f"    proximity-floor AUC (for contrast) = {metrics.auc(fl, label):.3f}")

# POS: hollow shell, radius 12, dense enough that shell neighbours are in contact
u = rng.normal(size=(160,3)); u /= np.linalg.norm(u,axis=1,keepdims=True)
shell = u*12.0 + rng.normal(0,0.4,(160,3))
report("POS hollow shell", shell)

# NEG: solid ball radius 12
v = rng.normal(size=(320,3)); v /= np.linalg.norm(v,axis=1,keepdims=True)
ball = v * (rng.uniform(0,1,(320,1))**(1/3))*12.0
report("NEG solid ball", ball)

# CRYPTIC: globular protein (solid-ish) with an internal spherical cavity carved out
w = rng.normal(size=(700,3)); w /= np.linalg.norm(w,axis=1,keepdims=True)
prot = w * (rng.uniform(0,1,(700,1))**(1/3))*15.0
cav_center = np.array([4.0,0,0]); cav_r = 5.5
d2c = np.linalg.norm(prot - cav_center, axis=1)
prot = prot[d2c > cav_r]                      # carve the cavity (remove interior points)
d2c = np.linalg.norm(prot - cav_center, axis=1)
label = (d2c < cav_r + 2.2).astype(float)      # lining residues = cavity wall
seed = int(np.argmax(prot[:,0]))               # arbitrary far surface seed
print()
report("CRYPTIC carved cavity", prot, label=label, seed=seed)
print("\nRead: POS shell should show large H2 persistence with pocket graph-NEAR;")
print("NEG ball ~0; CRYPTIC should recover the cavity wall ABOVE the proximity floor.")
