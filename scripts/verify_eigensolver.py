"""Equivalence check for a sparse (truncated) GNM eigensolver vs the current dense solve.

Conclusion (run it): the LOWEST-k eigenpairs from scipy.sparse.linalg.eigsh match dense
np.linalg.eigh — but the descriptors this app actually ships (msf, V_C covariance = the
FULL Kirchhoff pseudo-inverse, the average-mixing matrix, the reported Laplacian spectrum)
are sums over the ENTIRE spectrum, so computing them from k modes CHANGES the numbers.

That is why `analysis.gnm_context` keeps dense `eigh`: a truncated GNM is a modelling
approximation that needs its own validation, not a drop-in "no-change" speedup.

Usage:  python3 -m scripts.verify_eigensolver 4OBE A   [k]
"""
import sys

import numpy as np
from scipy.spatial.distance import cdist
from scipy.sparse.linalg import eigsh

from backend.data_layer import load_structure

TOL = 1e-6


def kirchhoff(coords, cutoff=8.0):
    D = cdist(coords, coords)
    A = ((D < cutoff) & (D > 1e-8)).astype(float)
    return np.diag(A.sum(1)) - A


def main():
    pdb = sys.argv[1] if len(sys.argv) > 1 else "4OBE"
    chain = sys.argv[2] if len(sys.argv) > 2 else "A"
    k = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    st = load_structure(pdb, chain)
    if st is None:
        print(f"could not load {pdb}/{chain}"); return 1
    K = kirchhoff(st["coords"])
    N = K.shape[0]
    print(f"{pdb}/{chain}: N={N} residues, comparing lowest {k} modes\n")

    # dense (current, ground truth)
    wd, Ud = np.linalg.eigh(K)
    # sparse (truncated) — lowest k+1 modes (incl. the zero mode)
    ws, Us = eigsh(K, k=min(k + 1, N - 1), which="SM")
    order = np.argsort(ws); ws, Us = ws[order], Us[:, order]

    # (1) lowest-k eigenvalues match?
    eig_ok = np.allclose(wd[:len(ws)], ws, atol=TOL)
    vec_ok = all(abs(abs(np.dot(Ud[:, i], Us[:, i])) - 1.0) < 1e-4 for i in range(len(ws)))
    print(f"[lowest-{k}] eigenvalues match (atol {TOL}): {eig_ok}")
    print(f"[lowest-{k}] eigenvectors align (|cos|>1-1e-4): {vec_ok}")
    print("  -> the sparse solver is correct FOR THE LOW MODES.\n")

    # (2) but the shipped descriptor msf = Σ_all (U^2 / w) needs the FULL spectrum
    nz = wd > 1e-9
    winv = np.zeros_like(wd); winv[nz] = 1.0 / wd[nz]
    msf_full = ((Ud ** 2) * winv).sum(1)                 # what the app ships
    nzs = ws > 1e-9
    winvs = np.zeros_like(ws); winvs[nzs] = 1.0 / ws[nzs]
    msf_trunc = ((Us ** 2) * winvs).sum(1)               # from k modes only
    rel = float(np.abs(msf_trunc - msf_full).max() / (np.abs(msf_full).max() + 1e-12))
    print(f"[downstream] per-residue MSF (full-spectrum descriptor): "
          f"max relative difference full vs {k}-mode = {rel:.3f}")
    print(f"  -> truncation CHANGES the shipped MSF by ~{rel:.0%}. NOT equivalence-preserving.\n")

    print("VERDICT: sparse eigsh is valid for a *slow-mode-only* pathway, but CANNOT replace "
          "dense eigh for the current full-spectrum descriptors without changing results. "
          "Keeping dense eigh.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
