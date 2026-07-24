"""TASK-0148 -- single-particle entanglement entropy across a spatial cut,
a localization/coupling observable distinct from raw occupation, distance-
stratified AUC, or anything else currently in this project's register.

Citation verified directly before implementing (not assumed from the
task's own one-line description): Peschel, I. (2003), "Calculation of
reduced density matrices from correlation functions", J. Phys. A: Math.
Gen. 36, L205 (arXiv:cond-mat/0212631) -- real, confirmed via IOPscience/
arXiv/ADS. For a free-fermion (or single-particle) system, the
entanglement entropy of a subsystem A is computable directly from the
two-point correlation matrix `C_ij` restricted to A, without ever
constructing the full many-body reduced density matrix: diagonalize
`C_A`, and

    S_A = -sum_k [ nu_k ln(nu_k) + (1-nu_k) ln(1-nu_k) ]

over `C_A`'s eigenvalues `nu_k` (each in [0, 1]) -- confirmed against
this exact formula independently in the literature (Peschel's own
follow-up reviews), not just derived here.

**A genuine mathematical reduction worked out and numerically verified
here, not assumed**: for a single COHERENT source residue (`k=1`), the
correlation matrix restricted to any region A is exactly RANK ONE
(`C_A = psi_A @ psi_A^dagger`, an outer product), so it has exactly one
nonzero eigenvalue, `nu = P_A = sum_{i in A} |psi_i|^2` (the total
occupation probability in region A) -- collapsing Peschel's general
matrix-diagonalization formula to the elementary closed form
`S_A = h(P_A)`, the *binary* Shannon entropy of the region's own total
occupation probability. Verified numerically to machine precision
against the general matrix method before trusting it
(`tests/test_entanglement.py`). This closed form does **not** apply to
this project's own established multi-residue active-site GAUGE
(TASK-0118: an incoherent statistical mixture over source residues, not
a coherent superposition) -- an incoherent mixture's correlation matrix
is a sum of `k` rank-1 terms (generically rank up to `k`, not 1), so the
general Peschel diagonalization is required for any real multi-residue
source, and is what this module actually uses for real-target scoring.

**Needs a genuinely coherent quantum amplitude, not a probability**:
`propagators.ctqw`/`time_averaged_ctqw` only ever return `|amplitude|^2`
(occupation probabilities), by design -- Peschel's correlation matrix
needs the complex amplitude itself (the off-diagonal coherences
`psi_i* psi_j` are exactly what the entanglement calculation depends
on). A *time-averaged* occupation is the diagonal of a decohered mixed
state with no accessible coherences at all, so it cannot be used here --
this module computes its own genuinely coherent, single-time-snapshot
amplitude directly (real finding, resolves this task's own Open
Question: the converged/time-averaged limit is not an option for this
observable, a fixed coherent time is the only choice that is even
well-defined).
"""
from __future__ import annotations

from typing import Sequence, Union

import numpy as np

Source = Union[int, Sequence[int]]


def _source_indices(source: Source) -> np.ndarray:
    return np.atleast_1d(np.asarray(source, dtype=int))


def natural_coherent_time(H: np.ndarray) -> float:
    """`t* = 1 / gap`, `gap = w[1] - w[0]` (the smallest nonzero
    eigenvalue gap) -- this module's own default coherent-snapshot time,
    matching this project's established gap-derived-timescale convention
    (`propagators.check_convergence`'s own `ground_state_relaxation`
    criterion uses the identical `w[1]-w[0]` gap). A blind, label-free
    choice: the natural period of `H`'s own slowest collective
    oscillation, not tuned to any target's labels."""
    w = np.linalg.eigvalsh(H)
    if len(w) < 2:
        return 1.0
    gap = float(w[1] - w[0])
    return 1.0 / gap if gap > 0 else float(1.0 / 1e-12)


def _binary_entropy_from_eigvals(eigvals: np.ndarray) -> float:
    nu = np.clip(eigvals.real, 0.0, 1.0)
    mask = (nu > 1e-14) & (nu < 1 - 1e-14)
    nu = nu[mask]
    return float(-np.sum(nu * np.log(nu) + (1 - nu) * np.log(1 - nu)))


def peschel_entropy(psi: np.ndarray, region_idx: np.ndarray) -> float:
    """General Peschel correlation-matrix entanglement entropy for a
    single PURE coherent amplitude vector `psi` (complex, `(N,)`), across
    the bipartition `region_idx` (A) vs. everything else (B). Literal
    implementation of the cited formula (build `C_A`, diagonalize, sum
    binary entropies of its eigenvalues) -- kept as the reference
    against which `entanglement_entropy_closed_form`'s `k=1` shortcut and
    `entanglement_entropy_mixture`'s multi-source construction are both
    verified, not assumed correct from the algebra alone."""
    region_idx = np.asarray(region_idx, dtype=int)
    psi_A = psi[region_idx]
    C_A = np.outer(np.conj(psi_A), psi_A)
    eigvals = np.linalg.eigvalsh(C_A)
    return _binary_entropy_from_eigvals(eigvals)


def entanglement_entropy_closed_form(occ: np.ndarray, region_idx: np.ndarray) -> float:
    """`S_A = h(P_A)`, the single-source (`k=1`) closed form -- see module
    docstring for the derivation. Takes an already-computed occupation
    probability vector (real, `(N,)`), not a complex amplitude -- only
    the total probability in `region_idx` matters for this special case.
    O(1) given `occ`, not a matrix diagonalization."""
    region_idx = np.asarray(region_idx, dtype=int)
    P_A = float(occ[region_idx].sum())
    return _binary_entropy_from_eigvals(np.array([P_A]))


def _ctqw_amplitude(w: np.ndarray, v: np.ndarray, t: float, source_idx: int) -> np.ndarray:
    """Complex CTQW amplitude psi(t) for a single scalar source residue,
    given `H`'s already-computed eigendecomposition -- the coherent
    quantity `propagators.ctqw`'s own public API discards (it returns
    only `|amplitude|^2`)."""
    coeffs = v[source_idx, :]
    return v @ (np.exp(-1j * w * t) * coeffs)


def entanglement_entropy_mixture(
    H: np.ndarray,
    source: Source,
    neighborhoods: Sequence[np.ndarray],
    t: float,
) -> np.ndarray:
    """Per-candidate-region Peschel entanglement entropy for a (possibly
    multi-index) `source`, under this project's own established
    incoherent-mixture GAUGE (TASK-0118: `rho0 = (1/k) * sum_s |s><s|`,
    matching `propagators._ctqw_mixture_from_eigh`'s own convention --
    NOT a coherent multi-index superposition, which has no biophysical
    basis for a real multi-residue active site).

    For each source residue `s`, computes its own genuinely coherent
    amplitude `psi_s(t)` (real phase information retained); the mixture's
    correlation matrix restricted to region A is
    `C_A = (1/k) * sum_s conj(psi_s[A]) (x) psi_s[A]` -- a sum of `k`
    rank-1 terms, generically rank up to `k` (not 1), diagonalized
    directly (region sizes are small, this is cheap even for many
    candidates). Reduces exactly to `entanglement_entropy_closed_form`
    when `k=1` -- verified in `tests/test_entanglement.py`, not assumed.

    Returns `(len(neighborhoods),)`.
    """
    idx = _source_indices(source)
    w, v = np.linalg.eigh(H)
    psis = np.array([_ctqw_amplitude(w, v, t, int(s)) for s in idx])  # (k, N)
    k = len(idx)

    entropies = np.empty(len(neighborhoods))
    for i, region in enumerate(neighborhoods):
        region = np.asarray(region, dtype=int)
        psi_A = psis[:, region]  # (k, |A|)
        C_A = (psi_A.conj().T @ psi_A) / k  # (|A|, |A|)
        eigvals = np.linalg.eigvalsh(C_A)
        entropies[i] = _binary_entropy_from_eigvals(eigvals)
    return entropies


def hop_radius_neighborhoods(hop_dist: np.ndarray, radius: int = 1) -> list:
    """Per-candidate spatial partition: candidate `j`'s own neighborhood
    is every residue within `radius` hops of `j` on the contact graph
    (including `j` itself) -- this task's own stated convention ("the
    candidate residue plus its own graph neighborhood at a stated hop
    radius"). `hop_dist` is the full `(N, N)` all-pairs hop-distance
    matrix (e.g. `scipy.sparse.csgraph.shortest_path` on the binary
    contact adjacency, unweighted). `radius=1` (immediate contacts) is
    this module's own default -- the minimal, well-defined "local
    neighborhood" at this project's own standard contact-graph
    resolution; not tuned to any target's labels."""
    N = hop_dist.shape[0]
    return [np.where(hop_dist[j] <= radius)[0] for j in range(N)]
