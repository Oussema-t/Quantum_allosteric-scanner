"""TASK-0166 -- per-residue conformational (ensemble/entropic) entropy from
GNM low-mode participation, testing the challenge's own reference [4]
(Motlagh & Hilser, *Nature* 508:331-339, 2014, "Agonism/antagonism switching
in allosteric ensembles") -- the view that allostery is **ensemble
redistribution** (a cryptic pocket exists because the conformational
ensemble contains states where it is open) rather than **signal
transmission** (something propagates from the active site to it). Every
other observable in this project's register seeds at the active site and
asks "where does a signal/walker/correlation go" -- a directed-channel
picture. This module tests a mechanistically different claim: a residue's
own accessible conformational ensemble, with no seed and no propagation
step at all.

**Formalism (this task's own required literature check, resolved -- not
invented):**

1. Bahar, Atilgan & Erman, *Fold. Des.* 2:173-181 (1997) -- the founding
   GNM paper -- establishes that under the network's single-parameter
   harmonic potential, each residue's fluctuation `Delta R_i` is Gaussian-
   distributed with variance `MSF_i = (3kT/gamma) * sum_k (1/lambda_k) *
   U_ik^2` (`U`/`lambda` the Kirchhoff eigenvectors/eigenvalues; the
   diagonal of the Kirchhoff pseudo-inverse -- exactly `potentials.
   _gnm_msf`'s own already-implemented formula, ported here restricted to
   a chosen low-mode subspace rather than the full spectrum, see point 3).
2. The differential (continuous) entropy of a univariate Gaussian is the
   standard information-theory identity (Shannon 1948; Cover & Thomas,
   *Elements of Information Theory*, 2nd ed., Theorem 8.4.1):
   `h(X) = 0.5 * ln(2*pi*e*sigma^2)` for `X ~ N(0, sigma^2)`.
   Combining (1)+(2) gives a per-residue conformational entropy directly
   from the GNM's own harmonic/Gaussian fluctuation model -- no new
   quantity is being invented, only an existing information-theory
   identity applied to an existing, already-validated GNM quantity.
3. **Resolves this task's own filed Open Question** ("differential
   entropy of a Gaussian fluctuation model" vs. "discretized Shannon
   entropy over mode participation weights"): the task's own Intent
   Contract already specifies "the Shannon/differential entropy of each
   residue's fluctuation distribution under the low-mode subspace
   (participation-weighted sum of per-mode variance contributions)" --
   read literally, this IS option 1 (the per-mode variance contributions
   summed under a chosen mode-count restriction are exactly `MSF_i`
   restricted to `n_modes`, which becomes the Gaussian's own variance
   parameter). Option 2 (Shannon entropy over the *normalized*
   distribution of mode weights, ignoring the modes' own absolute
   variance scale) answers a different question (motion "spread across
   modes" vs. motion "amount") and is not what the task's own wording
   describes -- not implemented here to avoid silently answering a
   different question than the one filed.

Restricting to the lowest `n_modes` non-trivial Kirchhoff eigenmodes (not
the full spectrum) matches this project's own established low-mode-
subspace convention (`superpose.anm_modes`/`compute_learnability`'s own
`n_modes=20` default, `lowmode_predictor.py`'s `k_modes` grid) -- the
modes actually resolvable from a single static structure's own topology,
not an arbitrary truncation invented for this task alone.
"""
from __future__ import annotations

import numpy as np


def gnm_lowmode_variance(coords: np.ndarray, cutoff: float = 10.0, n_modes: int = 20) -> np.ndarray:
    """Per-residue GNM mean-square fluctuation restricted to the lowest
    `n_modes` non-trivial Kirchhoff eigenmodes: `sigma_i^2 = sum_{k=1}^
    {n_modes} (1/lambda_k) * U_ik^2` -- module docstring point 1, `potentials.
    _gnm_msf`'s own formula with the sum truncated to the slowest `n_modes`
    modes rather than the full spectrum (this module's own restriction, so
    the entropy below reflects only the collective, resolvable low-frequency
    subspace, consistent with every other mode-based observable in this
    project's register).

    Returns `(N,)`, one variance per residue. Units are arbitrary (GNM's own
    `gamma`/`kT` are never calibrated in this codebase, same caveat as
    `potentials._gnm_msf` -- these are RELATIVE per-residue quantities, valid
    for AUC/ranking purposes, not absolute physical entropies in real units).
    """
    from .potentials import _kirchhoff_eigh

    _A, w, U, nz, _winv = _kirchhoff_eigh(coords, cutoff)
    w_nz = w[nz]
    U_nz = U[:, nz]
    order = np.argsort(w_nz)
    k = min(n_modes, len(order))
    idx = order[:k]
    w_low = w_nz[idx]
    U_low = U_nz[:, idx]
    return (U_low ** 2 / w_low).sum(axis=1)


def residue_conformational_entropy(coords: np.ndarray, cutoff: float = 10.0, n_modes: int = 20) -> np.ndarray:
    """Per-residue differential (Gaussian) conformational entropy: `0.5 *
    ln(2*pi*e*sigma_i^2)`, `sigma_i^2` from `gnm_lowmode_variance` -- module
    docstring point 2. High score = residue's own low-mode-subspace
    fluctuation ensemble is large (many accessible conformational states at
    Cα/GNM resolution); this is the per-residue "ensemble size" proxy the
    ensemble-allostery mechanism (Motlagh & Hilser 2014) predicts should
    correlate with cryptic-pocket residues, tested independently of any
    active-site seed or propagation path.

    Returns `(N,)`. A residue with `sigma_i^2 <= 0` (never occurs for a
    connected network with `n_modes >= 1`, since `w_low > 0` and `U_ik`
    generically nonzero, but guarded defensively) would make the log
    undefined; clipped to a tiny positive floor rather than raising, since
    this is a ranking score, not a certified physical quantity.
    """
    sigma_sq = np.clip(gnm_lowmode_variance(coords, cutoff=cutoff, n_modes=n_modes), 1e-300, None)
    return 0.5 * np.log(2.0 * np.pi * np.e * sigma_sq)
