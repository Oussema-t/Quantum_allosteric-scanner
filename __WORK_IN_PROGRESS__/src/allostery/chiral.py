"""TASK-0140 -- chiral (broken-time-reversal) circulation observable (HYP-P9).

**No reference script existed** (`chiral_observable.py` was cited by the
filing review batch but is not present anywhere in this repo or the
applied batch, confirmed directly, not assumed -- flagged by this task's
own Context). Reconstructed from `HYP-P9`'s own description
(`.claude/hypotheses/physics.md`) and the cited literature (Zimboras et
al. 2013, Sci. Rep. 3, 2361; Lu et al. 2016, PRA 93, 042302): a chiral
quantum walk breaks time-reversal symmetry only on cyclic topologies via
a Peierls-substituted complex hopping Hamiltonian, and the resulting bond
current's Helmholtz-Hodge *circulating* component is orthogonal to the
radial proximity flow by construction.

**Physics, spelled out (not left implicit, since no reference to check
against exists)**:

1. **Peierls substitution.** For a uniform effective field `B` = `field_
   scale * field_direction`, the symmetric-gauge vector potential is
   `A(r) = 0.5 * (B x r)`. Each contact-graph edge `(i, j)` picks up a
   phase `theta_ij = A((r_i+r_j)/2) . (r_j - r_i)` (midpoint line-integral
   approximation) -- `theta_ji = -theta_ij` exactly, by antisymmetry of
   the cross product, so `H[i,j] = -W[i,j] * exp(i*theta_ij)` is complex-
   Hermitian by construction, no extra symmetrization needed.

2. **Converged bond current.** The instantaneous quantum-walk bond
   current is `J_{a->b}(t) = 2*Im(H[a,b] * conj(psi_a(t)) * psi_b(t))`
   (the standard tight-binding continuity-equation current, derived
   directly from `d|psi_a|^2/dt = sum_b J_{b->a}(t)`). Its infinite-time
   average -- reusing TASK-0130's own closed-form convergence discipline,
   generalized from a diagonal quantity (occupation) to this off-diagonal
   bilinear form -- is `J_{a->b}^inf = 2*Im(H[a,b] * <rho>_inf[b,a])`,
   where `<rho>_inf` is the initial density matrix dephased onto `H`'s
   eigenbasis (`sum_r P_r rho0 P_r`, projector dephasing -- the standard,
   exactly basis-independent result for infinite-time averaging under
   unitary evolution with degenerate eigenspaces). **Exact degeneracy is
   not a corner case here, unlike TASK-0130's real-target spectra**: a
   uniform-hopping ring (the minimal topology with anything to circulate
   in, and this module's own regression-test fixture) has an exactly
   doubly-degenerate tight-binding spectrum by symmetry
   (`E_k=-2cos(2*pi*k/n)`, `E_k=E_{n-k}`) -- confirmed directly by running
   the naive non-degenerate formula against it, not assumed. So
   `bond_current_converged` groups (near-)degenerate eigenvalues via
   `propagators._group_degenerate_eigenvalues` (reused, not
   reimplemented) and projects the *density matrix* (not a scalar
   occupation) block-by-block, `rho_inf = sum_r V_r (V_r^dagger rho0 V_r)
   V_r^dagger` -- the exact matrix generalization of TASK-0130's
   `_block_projected_diagonal`, reducing to the plain per-mode formula
   when every block is a singleton.

3. **Hodge decomposition.** The antisymmetric edge-flow `J` splits into a
   gradient part `J_grad[i,j] = phi[i] - phi[j]` (a node potential `phi`
   solving the graph Poisson equation `L @ phi = div(J)`) and a
   circulating part `J_circ = J - J_grad`, divergence-free by
   construction (`div(J_circ) = div(J) - div(J_grad) = 0`, asserted as a
   regression test, not just claimed). `J_grad` is exactly the radial
   proximity flow (a potential-driven, curl-free current); `J_circ` is
   what this observable actually scores -- proximity-orthogonal by
   construction, not by tuning.

4. **A bare N-cycle ring gives exactly zero converged current from a
   diagonal seed, at any flux -- discovered and verified directly during
   test-fixture design, not a corner case anyone flagged in advance.**
   Confirmed for idealized uniform rings, randomly-weighted-and-phased
   rings, and a bipartite ring-plus-diagonal-chord -- always exactly zero
   to floating-point precision, at every flux strength tried, for both
   single-site and multi-site incoherent seeds. Two contributing
   mechanisms were isolated (both empirical, confirmed by direct
   numerical experiment, not derived from a textbook result): (a) an
   *exactly regular* ring is circulant, so every eigenvector has uniform
   site-modulus (`|v_k(j)|^2=1/n`, Bloch's theorem for any circulant
   matrix) and a diagonal seed's dephased density matrix collapses to the
   trivial maximally-mixed `I/n`, current-free by construction regardless
   of flux; (b) even an *irregularly weighted* ring (no residual
   symmetry) still gives zero -- confirmed for every flux value tried on
   a fully random-weight-and-phase 6-node ring -- pointing to something
   about the "every node has degree exactly 2" ring topology itself, not
   fully characterized here. **The module's actual production/test
   topology is not a bare ring**: `tests/test_chiral.py`'s
   `_triangulated_asymmetric_coords` fixture (an irregular ring widened
   with next-nearest-neighbor edges, so most nodes have degree >2 and
   triangles exist) gives robustly nonzero circulation under the
   identical construction -- confirmed directly, used as this module's
   actual "does chirality produce a signal" fixture, with the bare ring
   demoted to a documented *null* control (`TestBipartiteAndSymmetryNulls`
   in the test suite). Real protein contact graphs, being densely
   3D-packed, are not degree-2 rings, so this null is a synthetic-
   fixture-design concern to route around, not a real-data validity
   concern -- but any real target whose local topology happens to be
   ring-like (a single unbranched loop with no shortcuts) should be
   expected to score near zero on this observable for structural, not
   biological, reasons.
"""
from __future__ import annotations

import numpy as np

from .hamiltonians import contact_matrix, laplacian
from .propagators import _group_degenerate_eigenvalues

# Fraction of H's own spectral bandwidth -- same convention and same
# default as TASK-0130's own `time_averaged_ctqw_converged(degenerate_
# tol=...)`, reused here for the analogous off-diagonal quantity.
_DEGENERACY_TOL = 1e-6


def _source_indices(source) -> np.ndarray:
    return np.atleast_1d(np.asarray(source, dtype=int))


def _block_projected_density(v: np.ndarray, blocks, rho0: np.ndarray) -> np.ndarray:
    """`sum_r V_r @ (V_r^dagger @ rho0 @ V_r) @ V_r^dagger`, the exact
    matrix generalization of `propagators._block_projected_diagonal` to a
    general (not necessarily diagonal or rank-1) real initial density
    matrix `rho0` -- reduces to `sum_r <v_r|rho0|v_r> |v_r><v_r|` when
    every block `r` is a singleton, matching this module's original
    per-mode formula exactly in the non-degenerate limit."""
    n = v.shape[0]
    rho_inf = np.zeros((n, n), dtype=complex)
    for block in blocks:
        V_r = v[:, block]
        M_r = np.conj(V_r).T @ rho0 @ V_r
        rho_inf += V_r @ M_r @ np.conj(V_r).T
    return rho_inf


def peierls_hamiltonian(
    coords: np.ndarray,
    cutoff: float,
    field_direction,
    field_scale: float,
    *,
    weight: str = "binary",
    H_real: np.ndarray = None,
) -> np.ndarray:
    """Complex-Hermitian Peierls-substituted Hamiltonian. `field_direction`
    is normalized internally (only its direction matters; magnitude is
    `field_scale`'s job) -- a zero vector raises.

    `H_real=None` (default): builds `H = -W*exp(i*theta)` from a fresh
    binary/weighted contact matrix (`weight`, `cutoff`), the standalone
    synthetic-test path this module's own regression suite uses.

    `H_real` (TASK-0140's own real-data call shape,
    `chiral_circulation_score(H_real, coords, source)` per the task
    file): an already-built real symmetric operator (e.g.
    `hamiltonians.build_H_new`'s own `L_norm + V_B+V_T+V_R+V_C+V_M`) to
    Peierls-substitute directly -- its off-diagonal entries are
    multiplied in place by `exp(i*theta_ij)` (not rederived from a fresh
    contact matrix, so whatever weighting scheme `H_real` actually uses
    -- normalized-Laplacian, potential-augmented, or otherwise -- is
    preserved exactly), and its diagonal (the on-site potential terms)
    is copied over untouched: Peierls substitution is a hopping-only
    (off-diagonal) transformation in the standard tight-binding
    formalism, it does not touch on-site energy. `H_real`'s own nonzero
    off-diagonal pattern (not `cutoff`) determines which edges exist."""
    field_direction = np.asarray(field_direction, dtype=float)
    norm = np.linalg.norm(field_direction)
    if norm == 0:
        raise ValueError("peierls_hamiltonian: field_direction must be nonzero")
    field_direction = field_direction / norm

    n = len(coords)
    if H_real is None:
        W = contact_matrix(coords, cutoff=cutoff, weight=weight)
        H = np.zeros((n, n), dtype=complex)
        rows, cols = np.nonzero(np.triu(W, k=1))
        for i, j in zip(rows.tolist(), cols.tolist()):
            r_mid = 0.5 * (coords[i] + coords[j])
            A_mid = 0.5 * np.cross(field_direction, r_mid)
            theta = field_scale * float(np.dot(A_mid, coords[j] - coords[i]))
            H[i, j] = -W[i, j] * np.exp(1j * theta)
            H[j, i] = np.conj(H[i, j])
        return H

    H = H_real.astype(complex).copy()
    np.fill_diagonal(H, 0.0)
    rows, cols = np.nonzero(np.triu(H_real, k=1))
    for i, j in zip(rows.tolist(), cols.tolist()):
        r_mid = 0.5 * (coords[i] + coords[j])
        A_mid = 0.5 * np.cross(field_direction, r_mid)
        theta = field_scale * float(np.dot(A_mid, coords[j] - coords[i]))
        H[i, j] = H_real[i, j] * np.exp(1j * theta)
        H[j, i] = np.conj(H[i, j])
    np.fill_diagonal(H, np.diag(H_real))
    return H


def bond_current_converged(H: np.ndarray, source, *, coherent: bool = False) -> np.ndarray:
    """Infinite-time-averaged bond-current matrix `J` (antisymmetric,
    `J[b,a] = -J[a,b]`) for the complex-Hermitian `H`, seeded at `source`.

    `coherent=False` (default -- this project's established multi-residue
    seed convention, TASK-0118/INV-0006): incoherent mixture `rho0 = (1/k)
    sum_i |i><i|`. `coherent=True`: coherent superposition `rho0 = |psi0>
    <psi0|`, `psi0 = (1/sqrt(k)) sum_i |i>`. Identical either way for a
    scalar `source`.

    Groups (near-)degenerate eigenvalues (within `_DEGENERACY_TOL` of
    `H`'s own spectral bandwidth, same convention as TASK-0130's
    `time_averaged_ctqw_converged`) and applies the exact block
    projector-dephasing formula rather than the plain per-mode sum --
    required in practice, not merely a defensive guard: a uniform ring
    (the minimal circulation-capable topology, and this module's own
    regression-test fixture) has an exactly doubly-degenerate spectrum by
    symmetry (confirmed directly, see this module's own docstring)."""
    idx = _source_indices(source)
    n = H.shape[0]
    w, V = np.linalg.eigh(H)

    bandwidth = float(w[-1] - w[0]) if n > 1 else 0.0
    tol = _DEGENERACY_TOL * bandwidth if bandwidth > 0 else _DEGENERACY_TOL
    blocks = _group_degenerate_eigenvalues(w, tol)

    if coherent:
        psi0 = np.zeros(n, dtype=complex)
        psi0[idx] = 1.0 / np.sqrt(len(idx))
        rho0 = np.outer(psi0, np.conj(psi0))
    else:
        # Incoherent mixture rho0 = (1/k) sum_i |i><i| -- diagonal, real.
        rho0 = np.zeros((n, n), dtype=complex)
        for i in idx.tolist():
            rho0[i, i] = 1.0 / len(idx)

    rho_inf = _block_projected_density(V, blocks, rho0)  # rho_inf[b, a]

    J = 2.0 * np.imag(H * rho_inf.T)  # J[a,b] = 2*Im(H[a,b] * rho_inf[b,a])
    return J


def hodge_decompose(J: np.ndarray, A_binary: np.ndarray) -> tuple:
    """Graph Helmholtz-Hodge decomposition of the antisymmetric edge-flow
    `J` into a gradient part `J_grad` (irrotational -- the radial
    proximity-flow component, `J_grad[i,j] = phi[i] - phi[j]` for a node
    potential `phi` solving the graph Poisson equation `L @ phi =
    div(J)`) and a circulating part `J_circ = J - J_grad`
    (divergence-free by construction -- `div(J_grad) = L @ phi = div(J)`
    exactly, so `div(J_circ) = 0` identically, asserted as a regression
    test in `tests/test_chiral.py`, not just claimed here).

    `L` (the combinatorial graph Laplacian on `A_binary`) is singular --
    one zero mode per connected component, the arbitrary potential-
    reference gauge freedom -- handled correctly by `pinv`'s minimum-norm
    solution (any valid `phi` differing by a per-component constant gives
    the identical `J_grad`, since only differences `phi[i]-phi[j]` within
    a component ever appear)."""
    L = laplacian(A_binary.astype(float), normalised=False)
    div_J = J.sum(axis=1)
    phi = np.linalg.pinv(L) @ div_J

    J_grad = np.zeros_like(J)
    rows, cols = np.nonzero(A_binary)
    J_grad[rows, cols] = phi[rows] - phi[cols]
    J_circ = J - J_grad
    return J_grad, J_circ


_DEFAULT_FIELD_DIRECTIONS = (
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
)


def circulation_score_from_hamiltonians(
    hamiltonians, source, A_binary: np.ndarray, *, coherent: bool = False
) -> np.ndarray:
    """Average per-residue circulating-current magnitude
    (`sum_j |J_circ[i,j]|`) across a list of already-built (Peierls-
    substituted or otherwise) Hamiltonians, against a shared binary
    adjacency `A_binary` for the Hodge split. The shared final stage of
    `chiral_circulation_score` -- factored out so synthetic
    topology-controlled tests (e.g. a hand-built loop network needing
    explicit per-edge coupling weights that a distance-cutoff contact
    graph cannot express, `tests/test_chiral.py`'s own GATE-1 fixture)
    can reach it without fabricating coordinates."""
    n = A_binary.shape[0]
    scores = np.zeros((len(hamiltonians), n))
    for k, H in enumerate(hamiltonians):
        J = bond_current_converged(H, source, coherent=coherent)
        _, J_circ = hodge_decompose(J, A_binary)
        scores[k] = np.abs(J_circ).sum(axis=1)
    return scores.mean(axis=0)


def chiral_circulation_score(
    coords: np.ndarray,
    source,
    cutoff: float = 10.0,
    *,
    field_directions=_DEFAULT_FIELD_DIRECTIONS,
    field_scale: float = 0.05,
    coherent: bool = False,
    weight: str = "binary",
    H_real: np.ndarray = None,
) -> np.ndarray:
    """Per-residue chiral-circulation score: build a Peierls Hamiltonian
    for each of `field_directions` (default 3, the coordinate axes --
    rotation-robustness, per this task's own Constraint that the field
    grid is fixed once, blind to labels, never tuned per target), then
    delegate the current/Hodge/averaging stage to
    `circulation_score_from_hamiltonians`.

    `H_real=None` (default): builds each direction's Hamiltonian from a
    fresh `weight`/`cutoff` contact matrix (this module's own synthetic-
    test path). `H_real` (TASK-0140's own real-data call shape): reuse
    `H_real`'s own off-diagonal weighting and nonzero pattern for every
    field direction (see `peierls_hamiltonian`'s own docstring) -- the
    binary adjacency for the Hodge split is then `H_real`'s own nonzero
    off-diagonal pattern, not a separately-computed contact matrix (so a
    caller passing `H_real=build_H_new(...)` gets a graph consistent with
    that operator's own, possibly non-cutoff-derived, connectivity).

    `field_scale=0.05` is this task's own Implementer's-call default
    (Open Question analogue -- stated here, sensitivity checked directly
    in this task's own Done section, not assumed adequate)."""
    if H_real is None:
        A_binary = (contact_matrix(coords, cutoff=cutoff, weight="binary") > 0).astype(float)
    else:
        A_binary = (np.abs(H_real - np.diag(np.diag(H_real))) > 0).astype(float)
    hamiltonians = [
        peierls_hamiltonian(coords, cutoff, direction, field_scale, weight=weight, H_real=H_real)
        for direction in field_directions
    ]
    return circulation_score_from_hamiltonians(hamiltonians, source, A_binary, coherent=coherent)
