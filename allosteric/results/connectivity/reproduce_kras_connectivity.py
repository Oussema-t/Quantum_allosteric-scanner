#!/usr/bin/env python3
"""Reproduce the KRAS G12C connectivity matrix with the submission's parameters.

Operator  : H_new (the submission's operator)
Structure : 4LDJ chain A (true G12C apo; residue 12 = CYS, GDP+MG only)
Parameters: NET_CUTOFF = 10.0 A, ALPHA = 0.30, lambdas(B,T,R,C,M) = (0.08,0.16,0.08,0.04,0.04),
            term_frac = 0.05, n_low_modes = 10  -- the pre-registered values in the proposal.

C_ij = lim_{T->inf} (1/T) int_0^T |<j|e^{-iHt}|i>|^2 dt = sum_k |v_k(i)|^2 |v_k(j)|^2
     = (V o V)(V o V)^T   for H_new = V diag(w) V^T.

C depends on the OPERATOR only; seeding and scoring do not enter it, so this matrix is
identical whether the pipeline seeds from fpocket, PASSer or a consensus.

Usage: python3 reproduce_kras_connectivity.py [4LDJ.pdb]
"""
import sys, numpy as np

# --- submission parameters (pre-registered) ----------------------------------
NET_CUTOFF   = 10.0
ALPHA        = 0.30
LAMBDAS      = dict(B=0.08, T=0.16, R=0.08, C=0.04, M=0.04)
TERM_FRAC    = 0.05
N_LOW_MODES  = 10


def contact_matrix(coords, cutoff=NET_CUTOFF, weight="binary", sigma=6.0, alpha=ALPHA):
    diff = coords[:, None, :] - coords[None, :, :]
    dist = np.sqrt((diff ** 2).sum(2))
    mask = (dist < cutoff) & (dist > 0)
    if weight == "binary":
        W = mask.astype(float)
    elif weight == "gaussian":
        W = np.exp(-(dist ** 2) / (2 * sigma ** 2)) * mask
    elif weight == "exponential":
        W = np.exp(-alpha * dist) * mask
    else:
        raise ValueError(weight)
    return W

def laplacian(W, normalised=False):
    D = np.diag(W.sum(1))
    L = D - W
    if not normalised:
        return L
    deg = W.sum(1)
    dis = np.where(deg > 0, 1.0 / np.sqrt(deg), 0.0)
    Di = np.diag(dis)
    return Di @ L @ Di

def normalised_laplacian_alpha(coords, cutoff=NET_CUTOFF, alpha=ALPHA):
    return laplacian(contact_matrix(coords, cutoff, "exponential", alpha=alpha), normalised=True)

def _zscore(x):
    return (x - x.mean()) / (x.std() + 1e-9)


def _kirchhoff_eigh(coords, cutoff):
    A = contact_matrix(coords, cutoff, "binary")
    K = laplacian(A)
    w, U = np.linalg.eigh(K)
    nz = w > 1e-9
    winv = np.where(nz, 1.0 / np.where(nz, w, 1.0), 0.0)
    return A, w, U, nz, winv


def _gnm_msf(coords, cutoff):
    _A, _w, U, _nz, winv = _kirchhoff_eigh(coords, cutoff)
    return np.diag((U * winv) @ U.T)

def V_B(bfactors):
    return _zscore(bfactors.astype(float))

def V_T(n, term_frac=TERM_FRAC):
    k = max(1, int(n * term_frac))
    m = np.zeros(n); m[:k] = 1.0; m[-k:] = 1.0
    return _zscore(m)

def V_R(coords, cutoff=NET_CUTOFF):
    A = contact_matrix(coords, cutoff, "binary")
    deg = A.sum(1)
    tri = np.diag(A @ (A @ A))
    clust = tri / np.maximum(deg * (deg - 1), 1.0)
    msf = _gnm_msf(coords, cutoff)
    return _zscore(-(_zscore(deg) + _zscore(clust) - _zscore(msf)))

def V_C(coords, cutoff=NET_CUTOFF):
    _A, _w, U, _nz, winv = _kirchhoff_eigh(coords, cutoff)
    Cov = (U * winv) @ U.T
    d = np.sqrt(np.clip(np.diag(Cov), 1e-12, None))
    nDCC = Cov / np.outer(d, d)
    np.fill_diagonal(nDCC, 0.0)
    return -_zscore(np.abs(nDCC).sum(1))

def V_M(coords, cutoff=NET_CUTOFF, n_modes=N_LOW_MODES):
    _A, w, v, _nz, _winv = _kirchhoff_eigh(coords, cutoff)
    i0 = max(1, int(np.searchsorted(w, 1e-8)))
    low = v[:, i0:i0 + n_modes]
    return -_zscore((low ** 2).mean(1))

def build_H_new(coords, bfactors, cutoff=NET_CUTOFF, alpha=ALPHA, lam=LAMBDAS,
                term_frac=TERM_FRAC, n_low_modes=N_LOW_MODES, apply_VB=True):
    L = normalised_laplacian_alpha(coords, cutoff, alpha)
    vb = lam["B"] * V_B(bfactors) if apply_VB else np.zeros(len(coords))
    diag = (vb + lam["T"] * V_T(len(coords), term_frac) + lam["R"] * V_R(coords, cutoff)
            + lam["C"] * V_C(coords, cutoff) + lam["M"] * V_M(coords, cutoff, n_low_modes))
    return L + np.diag(diag), diag

# --- parse 4LDJ chain A: Ca coords + B-factors, longest chain ----------------
def parse_calpha(path, chain="A"):
    from Bio.PDB import PDBParser
    s = PDBParser(QUIET=True).get_structure("x", path)
    model = next(iter(s))
    ch = model[chain]
    coords, bf, resnums = [], [], []
    for res in ch:
        if res.id[0] != " ":            # skip HETATM (GDP, MG, water)
            continue
        if "CA" not in res:
            continue
        ca = res["CA"]
        coords.append(ca.coord); bf.append(ca.bfactor); resnums.append(res.id[1])
    return np.array(coords, float), np.array(bf, float), resnums

def mixing_matrix(H):
    w, V = np.linalg.eigh(np.asarray(H, float))
    sq = V * V
    return sq @ sq.T

if __name__ == "__main__":
    pdb = sys.argv[1] if len(sys.argv) > 1 else "pdb_cache/4LDJ.pdb"
    X, B, resnums = parse_calpha(pdb, "A")
    print("4LDJ chain A: %d Ca residues, resnum %d..%d" % (len(X), resnums[0], resnums[-1]))
    H, _diag = build_H_new(X, B)
    C = mixing_matrix(H)
    print("H_new: %dx%d | Hermitian %s" % (len(H), len(H), np.allclose(H, H.T)))
    print("C:     %dx%d | symmetric %s | rows->1 %s (max dev %.2e) | all>=0 %s"
          % (len(C), len(C), np.allclose(C, C.T),
             np.allclose(C.sum(1), 1, atol=1e-6), np.abs(C.sum(1)-1).max(), bool((C >= -1e-15).all())))
    np.savetxt("KRAS_G12C_4LDJ_connectivity_Hnew_submission.csv", C, delimiter=",", fmt="%.6e")
    print("saved KRAS_G12C_4LDJ_connectivity_Hnew_submission.csv")
    # verify against the notebook's own H_new matrix if present
    import os
    ref = "KRAS_G12C_4LDJ_connectivity_best_H_new.csv"
    if os.path.exists(ref):
        R = np.loadtxt(ref, delimiter=",")
        if R.shape == C.shape:
            print("VERIFY vs notebook %s: max|diff| = %.3e  -> %s"
                  % (ref, np.abs(R-C).max(), "REPRODUCED (within the CSV 6-sig-fig write precision)" if np.allclose(R, C, atol=2e-5) else "DIFFERS"))
        else:
            print("VERIFY: shape mismatch notebook %s vs reproduced %s (residue selection differs)" % (R.shape, C.shape))
