"""
Transport propagators (notebook §3) — the quantum metric.

These turn the Hamiltonian H into an N×N connectivity matrix C, where C[i, j] is the
propagated signal between residues i and j.

  green : partially-coherent broadened response (time-integrated, dephased CTQW)
  ctqw  : coherent continuous-time quantum walk, time-averaged |U(t)|^2 (keeps
          interference — the genuine quantum signature)
  heat  : classical diffusion baseline exp(-tH) (for quantum-vs-classical comparison)

The quantum walk propagates as a superposition along all network paths simultaneously,
so non-local interference lets distal allosteric residues accumulate connectivity that a
purely diffusive (classical) model misses.
"""
import numpy as np


def transport_green(H, gamma):
    """Partially-coherent broadened response (= time-integrated, dephased CTQW).
    Returns a symmetric residue-residue Green's map."""
    w, V = np.linalg.eigh(H)
    dE = w[:, None] - w[None, :]
    wt = gamma / (gamma ** 2 + dE ** 2)
    Vs = np.abs(V) ** 2
    return (Vs @ wt @ Vs.T) * gamma


def transport_ctqw(H, times):
    """Coherent CTQW; time-averaged |U(t)|^2 over a finite window (keeps interference)."""
    w, V = np.linalg.eigh(H)
    N = H.shape[0]
    P = np.zeros((N, N))
    for t in times:
        U = (V * np.exp(-1j * w * t)) @ V.conj().T
        P += np.abs(U) ** 2
    return P / len(times)


def transport_heat(H, t):
    """Classical diffusion baseline exp(-tH)."""
    w, V = np.linalg.eigh(H)
    w = w - w.min()
    return (V * np.exp(-t * w)) @ V.T


# ---- quantum signatures (used for quantum-vs-classical analysis) ----

def ipr(row):
    """Inverse participation ratio of a connectivity row (low = localized)."""
    p = np.abs(row)
    p = p / (p.sum() + 1e-12)
    return 1.0 / np.sum(p ** 2)


def spread_variance(H, src, times):
    """Position variance vs t from a source set: ~t^2 ballistic (coherent quantum),
    ~t diffusive (classical). The ballistic signature is the quantum advantage."""
    w, V = np.linalg.eigh(H)
    N = H.shape[0]
    pos = np.arange(N)
    out = []
    for t in times:
        amp = np.zeros(N, dtype=complex)
        for s in src:
            amp += (V * np.exp(-1j * w * t)) @ V.conj().T[:, s]
        p = np.abs(amp) ** 2
        p /= p.sum() + 1e-12
        m = (pos * p).sum()
        out.append(((pos - m) ** 2 * p).sum())
    return np.array(out)


def transport_entropy(row):
    """Shannon entropy of a connectivity row."""
    p = np.abs(row)
    p = p / (p.sum() + 1e-12)
    p = p[p > 0]
    return -np.sum(p * np.log(p))
