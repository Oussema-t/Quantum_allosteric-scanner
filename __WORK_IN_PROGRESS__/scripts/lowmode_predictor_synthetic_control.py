"""Synthetic hinge-protein control for the low-mode predictors.
Ground truth is KNOWN by construction, so 'does the method recover it' is
answerable without any real structure. The seed sits at the far end of
domain A; the TRUE allosteric pocket sits at the far end of domain B,
graph-far from the seed through a thin hinge but coupled to it by the
lowest hinge-bending mode. Success = recover the distal-coupled pocket
above the near residues, i.e. beat the proximity floor.
"""
import numpy as np, sys; sys.path.insert(0,'src')
from allostery import lowmode_predictor as LM
from allostery import baselines, metrics, propagators as P
from scipy.stats import spearmanr
import networkx as nx
from allostery.hamiltonians import contact_matrix

rng = np.random.default_rng(7)

def blob(center, n, r=10.0):
    pts = rng.normal(size=(n,3)); pts /= np.linalg.norm(pts,axis=1,keepdims=True)
    pts *= rng.uniform(0, r, size=(n,1))**(1/3) * r**(2/3)   # ~uniform in ball
    return pts + np.asarray(center)

# Domain A around x=-22, Domain B around x=+22, thin hinge across origin.
A = blob((-22,0,0), 55, r=11)
B = blob((+22,0,0), 55, r=11)
hinge = np.array([[-6,0,0],[-2,0,0],[2,0,0],[6,0,0]], float) + rng.normal(0,0.5,(4,3))
coords = np.vstack([A, hinge, B])
nA, nH, nB = len(A), len(hinge), len(B)
# seed = domain-A residue with most negative x (far end, max hinge-mode amplitude)
seed = int(np.argmin(coords[:nA,0]))
# true pocket = 8 domain-B residues with most positive x (far end of B)
B_x = coords[nA+nH:,0]
pocket_local = np.argsort(B_x)[-8:]
pocket = (nA+nH) + pocket_local
label = np.zeros(len(coords)); label[pocket] = 1

cutoff = 10.0
Adj = contact_matrix(coords, cutoff=cutoff, weight="binary")
G = nx.from_numpy_array(Adj)
if not nx.is_connected(G):
    # keep largest component (hinge should connect; guard anyway)
    cc=max(nx.connected_components(G),key=len); print("WARN disconnected, |cc|=",len(cc))
hop = np.array([nx.shortest_path_length(G, seed).get(j, len(coords)) for j in range(len(coords))])
print(f"N={len(coords)} (A={nA},hinge={nH},B={nB}); seed idx={seed}; pocket size={len(pocket)}")
print(f"pocket graph-hop from seed: min={hop[pocket].min()}, max={hop[pocket].max()} "
      f"(median non-pocket hop={np.median(hop[label==0]):.0f}) -> pocket is graph-FAR\n")

# Build H_new for the confounded CTQW observable (needs b-factors; use uniform)
from allostery.hamiltonians import build_H_new
bf = np.ones(len(coords))
Hnew = build_H_new(coords, bf, cutoff=cutoff)

scores = {
  "CTQW-occ (confounded, full spectrum)": P.time_averaged_ctqw_converged(Hnew, source=seed),
  "proximity floor: -hop_from_seed":      baselines.hop_from_seed(coords, seed, cutoff=cutoff),
  "proximity floor: -euclid_from_seed":   baselines.euclid_from_seed_centroid(coords, seed),
  "PRS-low (k=20)":                       LM.prs_low(coords, seed, cutoff=cutoff, k_modes=20),
  "DCC-low (k=20)":                       LM.dcc_low(coords, seed, cutoff=cutoff, k_modes=20),
  "PRS-low (k=5)":                        LM.prs_low(coords, seed, cutoff=cutoff, k_modes=5),
}
print(f"{'observable':42s} {'AUC(pocket)':>11s} {'rho(score,-hop)':>16s}")
print("-"*72)
for name, sc in scores.items():
    a = metrics.auc(sc, label)
    r,_ = spearmanr(sc, -hop)
    print(f"{name:42s} {a:11.3f} {r:16.3f}")
print("\nRead: proximity floors + confounded CTQW should score the DISTAL pocket")
print("BELOW 0.5 (they reward nearness). A working low-mode observable should")
print("score it ABOVE 0.5 with a LOW |rho(score,-hop)| (proximity-orthogonal).")

print("\n" + "="*72)
print("DIAGNOSTIC 1 — is the planted hinge coupling actually in the low modes?")
w_anm, v_anm = LM.anm_modes(coords, cutoff=cutoff, n_modes=6)
near = (hop <= 2) & (label == 0)          # seed neighborhood
far_uncoupled = (hop >= 6) & (label == 0) # distal, not the pocket
for m in range(3):
    amp = (v_anm[:, m].reshape(-1,3)**2).sum(1)  # per-residue sq amplitude of mode m
    print(f"  mode {m} (w={w_anm[m]:.4f}): amp seed={amp[seed]:.4f}  "
          f"pocket={amp[pocket].mean():.4f}  near={amp[near].mean():.4f}  "
          f"far_uncoupled={amp[far_uncoupled].mean():.4f}")

print("\nDIAGNOSTIC 2 — distance-CONTROLLED test (the repo's stratified lens):")
print("among DISTAL residues only (hop>=6), does each score separate the")
print("coupled pocket from uncoupled distal residues? label=1 pocket vs 0 far-uncoupled")
distal = (hop >= 6)
lab_d = label[distal]
for name, sc in scores.items():
    a = metrics.auc(sc[distal], lab_d)
    print(f"  {name:42s} stratified-AUC={a:.3f}")

print("\nDIAGNOSTIC 3 — near-neighborhood-excluded whole test (exclude hop<=3 from negatives):")
keep = (label == 1) | (hop > 3)
for name, sc in scores.items():
    a = metrics.auc(sc[keep], label[keep])
    print(f"  {name:42s} AUC(excl. near)={a:.3f}")
