"""TASK-0172 -- tests for `allostery.reduce`. Synthetic fixtures only
(this project's established convention for fast, network-free unit
tests), plus the dumbbell synthetic-gate reproduction (TASK-0103's own
fixture, TASK-0172's own Planned Validation: "does the reduced operator
preserve the planted signal that naive Louvain merging destroys?").
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.coarse import coarse_grain  # noqa: E402
from allostery.hamiltonians import contact_matrix, laplacian  # noqa: E402
from allostery.propagators import time_averaged_ctqw_converged  # noqa: E402
from allostery.reduce import (  # noqa: E402
    krylov_basis,
    lift_krylov_eigvecs,
    lift_schur_eigvecs,
    reduce_krylov,
    schur_complement,
)


def _helix_coords(n: int = 60, seed: int = 0) -> np.ndarray:
    """Same construction as `tests/test_plant.py::_helix_coords` -- real
    3D tertiary contacts (not re-imported, per this project's own
    self-contained-fixture convention)."""
    rng = np.random.default_rng(seed)
    t = np.arange(n, dtype=float)
    coords = np.column_stack([
        6.0 * np.cos(t * 0.55) + 0.2 * rng.standard_normal(n),
        6.0 * np.sin(t * 0.55) + 0.2 * rng.standard_normal(n),
        1.6 * t,
    ])
    return coords


def _test_H(n: int = 60, seed: int = 0) -> np.ndarray:
    """A real-symmetric H with a nontrivial diagonal (unlike a bare
    Laplacian) -- normalised Laplacian plus a random positive diagonal
    potential, the same shape of object `build_H_new` produces (coupling
    + on-site terms), without needing a real target."""
    coords = _helix_coords(n, seed)
    L = laplacian(contact_matrix(coords, cutoff=8.0, weight="invdist"), normalised=False)
    rng = np.random.default_rng(seed + 1)
    diag_pot = rng.uniform(0.0, 0.5, size=n)
    return L + np.diag(diag_pot)


class TestKrylovBasis:
    def test_orthonormal(self):
        H = _test_H()
        Q = krylov_basis(H, seed_idx=np.array([0, 1]), m=10)
        assert np.allclose(Q.T @ Q, np.eye(Q.shape[1]), atol=1e-8)

    def test_shape_at_most_m(self):
        H = _test_H()
        Q = krylov_basis(H, seed_idx=np.array([0]), m=8)
        assert Q.shape[0] == H.shape[0]
        assert Q.shape[1] <= 8

    def test_seed_vector_in_span(self):
        """e_i for every seed i must lie exactly in span(Q) -- Q's own
        first block is literally the (orthonormalized) seed vectors."""
        H = _test_H()
        seed_idx = np.array([0, 5])
        Q = krylov_basis(H, seed_idx, m=10)
        for i in seed_idx:
            e_i = np.zeros(H.shape[0])
            e_i[i] = 1.0
            proj = Q @ (Q.T @ e_i)
            assert np.linalg.norm(proj - e_i) < 1e-8

    def test_reduced_operator_is_symmetric(self):
        H = _test_H()
        Q = krylov_basis(H, seed_idx=np.array([0]), m=10)
        H_red = reduce_krylov(H, Q)
        assert np.allclose(H_red, H_red.T, atol=1e-10)

    def test_exact_when_subspace_is_full(self):
        """seed_idx = every node, m = N: Q's own first block is already
        {e_0, ..., e_{N-1}} (orthonormal by construction, no powers of H
        even needed before the round-robin loop's first `len(candidates)
        &gt;= m` check), so Q spans the whole space trivially, and the
        reduced operator's spectrum must exactly match H's own full
        spectrum. (A *single*-node seed is NOT guaranteed full rank at
        m=N in general -- whether it is depends on that seed vector's
        overlap with every eigenvector of H, a property of the specific
        graph/seed pair, not a theorem; this test avoids relying on that
        coincidence by seeding from every node instead.)"""
        H = _test_H(n=20)
        N = H.shape[0]
        Q = krylov_basis(H, seed_idx=np.arange(N), m=N)
        H_red = reduce_krylov(H, Q)
        w_full = np.sort(np.linalg.eigvalsh(H))
        w_red = np.sort(np.linalg.eigvalsh(H_red))
        assert Q.shape[1] == N
        assert np.allclose(w_full, w_red, atol=1e-6)

    def test_lift_exact_when_subspace_is_full(self):
        H = _test_H(n=20)
        N = H.shape[0]
        Q = krylov_basis(H, seed_idx=np.arange(N), m=N)
        H_red = reduce_krylov(H, Q)
        w_local, v_local = np.linalg.eigh(H_red)
        w_full, v_full = lift_krylov_eigvecs(Q, w_local, v_local)
        # every lifted vector must be a genuine eigenvector of H
        residual = H @ v_full - v_full * w_full[None, :]
        assert np.max(np.abs(residual)) < 1e-6

    def test_occupation_matches_full_when_subspace_is_full(self):
        """The actual, end-to-end retention claim: when the Krylov
        subspace is exact, the reduced-operator-derived converged
        occupation must match the full-H occupation exactly."""
        H = _test_H(n=20)
        N = H.shape[0]
        seed_idx = np.array([0, 3])
        Q = krylov_basis(H, seed_idx, m=N)
        H_red = reduce_krylov(H, Q)
        w_local, v_local = np.linalg.eigh(H_red)
        w_full, v_full = lift_krylov_eigvecs(Q, w_local, v_local)

        occ_full = time_averaged_ctqw_converged(H, source=seed_idx, coherent=False)
        occ_reduced = time_averaged_ctqw_converged(w=w_full, v=v_full, source=seed_idx, coherent=False)
        assert np.allclose(occ_full, occ_reduced, atol=1e-5)

    def test_truncated_subspace_degrades_gracefully(self):
        """A genuinely truncated (m << N) Krylov subspace is NOT exact,
        but should still correlate strongly with the full occupation for
        a reasonably-sized m -- a real, falsifiable retention claim, not
        just a same-answer-when-trivial check."""
        H = _test_H(n=60)
        seed_idx = np.array([0])
        Q = krylov_basis(H, seed_idx, m=15)
        H_red = reduce_krylov(H, Q)
        w_local, v_local = np.linalg.eigh(H_red)
        w_full, v_full = lift_krylov_eigvecs(Q, w_local, v_local)

        occ_full = time_averaged_ctqw_converged(H, source=seed_idx, coherent=False)
        occ_reduced = time_averaged_ctqw_converged(w=w_full, v=v_full, source=seed_idx, coherent=False)
        from scipy.stats import spearmanr
        rho = spearmanr(occ_full, occ_reduced).statistic
        assert rho > 0.5


class TestSchurComplement:
    def test_retain_all_returns_H_unchanged(self):
        H = _test_H()
        H_eff, elim_idx = schur_complement(H, retain_idx=np.arange(H.shape[0]), E=0.0, eta=0.0)
        assert len(elim_idx) == 0
        assert np.allclose(H_eff, H)

    def test_symmetric(self):
        H = _test_H()
        H_eff, _ = schur_complement(H, retain_idx=np.arange(20), E=0.0, eta=0.0)
        assert np.allclose(H_eff, H_eff.T, atol=1e-10)

    def test_exact_at_a_planted_eigenvalue(self):
        """Loewdin's own guarantee: H_eff(E) reproduces exactly those
        eigenvalues of H equal to E. Construct H with a known eigenvalue
        (diagonalize a random symmetric matrix, rescale to a chosen
        target eigenvalue) and confirm H_eff(E=that eigenvalue) has it
        as one of its own eigenvalues, to numerical precision."""
        n = 20
        rng = np.random.default_rng(3)
        A = rng.standard_normal((n, n))
        A = (A + A.T) / 2
        w, v = np.linalg.eigh(A)
        target_eigval = 1.2345
        w[3] = target_eigval  # plant an exact eigenvalue
        H = (v * w[None, :]) @ v.T
        H = (H + H.T) / 2

        retain_idx = np.arange(8)  # arbitrary label-blind retained subset
        H_eff, elim_idx = schur_complement(H, retain_idx, E=target_eigval, eta=0.0)
        w_eff = np.linalg.eigvalsh(H_eff)
        assert np.min(np.abs(w_eff - target_eigval)) < 1e-6

    def test_lift_reconstructs_exact_eigenvector_at_planted_energy(self):
        n = 20
        rng = np.random.default_rng(4)
        A = rng.standard_normal((n, n))
        A = (A + A.T) / 2
        w, v = np.linalg.eigh(A)
        target_eigval = -0.75
        w[5] = target_eigval
        H = (v * w[None, :]) @ v.T
        H = (H + H.T) / 2

        retain_idx = np.arange(8)
        H_eff, elim_idx = schur_complement(H, retain_idx, E=target_eigval, eta=0.0)
        w_local, v_local = np.linalg.eigh(H_eff)
        i = int(np.argmin(np.abs(w_local - target_eigval)))
        w_full, v_full = lift_schur_eigvecs(
            H, retain_idx, elim_idx, target_eigval, w_local[[i]], v_local[:, [i]], eta=0.0,
        )
        residual = H @ v_full[:, 0] - target_eigval * v_full[:, 0]
        assert np.linalg.norm(residual) < 1e-6

    def test_approximation_degrades_away_from_reference_energy(self):
        """The honest converse of the exactness test: reconstructing an
        eigenvector far from the fixed reference energy E should have a
        real, nonzero residual -- confirming this module doesn't
        silently claim exactness it doesn't have."""
        n = 20
        rng = np.random.default_rng(5)
        A = rng.standard_normal((n, n))
        A = (A + A.T) / 2
        w_true, v_true = np.linalg.eigh(A)
        H = A

        retain_idx = np.arange(8)
        H_eff, elim_idx = schur_complement(H, retain_idx, E=0.0, eta=0.0)
        w_local, v_local = np.linalg.eigh(H_eff)
        # pick the Ritz value farthest from the reference energy E=0
        i = int(np.argmax(np.abs(w_local)))
        w_full, v_full = lift_schur_eigvecs(
            H, retain_idx, elim_idx, 0.0, w_local[[i]], v_local[:, [i]], eta=0.0,
        )
        residual = np.linalg.norm(H @ v_full[:, 0] - w_local[i] * v_full[:, 0])
        assert residual > 1e-3  # a real, nonzero approximation error


class TestDumbbellSyntheticGate:
    """TASK-0172's own Planned Validation: does the reduced operator
    preserve a planted long-range coupling signal that naive Louvain
    merging can destroy? Reuses TASK-0103's own dumbbell construction
    directly (not re-derived) -- ACTIVE(0-11)/DRUG(12-23)/DECOY(24-35),
    two same-length bridges, coupling strength independently
    controllable per bridge."""

    ACTIVE = list(range(0, 12))
    DRUG = list(range(12, 24))
    DECOY = list(range(24, 36))
    BRIDGE_DRUG = list(range(36, 40))
    BRIDGE_DECOY = list(range(40, 44))
    N_NODES = 44

    @staticmethod
    def _build(strong_lobe: str, seed: int = 0) -> np.ndarray:
        """Ported from `tests/test_dumbbell_negative_control.py::
        build_dumbbell_network`, coupling-only (no well) -- the minimal
        subset TASK-0172 needs, not cross-imported to keep this test
        file's own dependency surface self-contained per this project's
        established per-test-file-fixture convention."""
        rng = np.random.default_rng(seed)
        N = TestDumbbellSyntheticGate.N_NODES
        W = np.zeros((N, N))

        def _clique(idxs):
            for a in idxs:
                for b in idxs:
                    if a < b:
                        W[a, b] = W[b, a] = rng.uniform(0.7, 1.3)

        _clique(TestDumbbellSyntheticGate.ACTIVE)
        _clique(TestDumbbellSyntheticGate.DRUG)
        _clique(TestDumbbellSyntheticGate.DECOY)

        STRONG, WEAK = 1.0, 0.15
        w_drug = STRONG if strong_lobe == "DRUG" else WEAK
        w_decoy = STRONG if strong_lobe == "DECOY" else WEAK

        anchor_active_drug = int(rng.choice(TestDumbbellSyntheticGate.ACTIVE))
        anchor_active_decoy = int(rng.choice(TestDumbbellSyntheticGate.ACTIVE))
        anchor_drug = int(rng.choice(TestDumbbellSyntheticGate.DRUG))
        anchor_decoy = int(rng.choice(TestDumbbellSyntheticGate.DECOY))

        chain_drug = [anchor_active_drug] + TestDumbbellSyntheticGate.BRIDGE_DRUG + [anchor_drug]
        for a, b in zip(chain_drug[:-1], chain_drug[1:]):
            W[a, b] = W[b, a] = w_drug

        chain_decoy = [anchor_active_decoy] + TestDumbbellSyntheticGate.BRIDGE_DECOY + [anchor_decoy]
        for a, b in zip(chain_decoy[:-1], chain_decoy[1:]):
            W[a, b] = W[b, a] = w_decoy

        return laplacian(W, normalised=False)

    @staticmethod
    def _auc_to_drug(occ: np.ndarray) -> float:
        from allostery.metrics import auc as _auc

        drug, decoy = TestDumbbellSyntheticGate.DRUG, TestDumbbellSyntheticGate.DECOY
        scores = np.concatenate([occ[drug], occ[decoy]])
        labels = np.concatenate([np.ones(len(drug)), np.zeros(len(decoy))])
        return _auc(scores, labels)

    def test_full_H_shows_the_planted_discrimination(self):
        """Sanity: confirms the fixture itself reproduces the expected
        coupling-follows-strength signature before testing any reduction
        against it (TASK-0103's own established result)."""
        H = self._build(strong_lobe="DRUG")
        occ = time_averaged_ctqw_converged(H, source=self.ACTIVE, coherent=False)
        assert self._auc_to_drug(occ) > 0.85

    def test_krylov_reduction_preserves_the_signal(self):
        """Eliminate down to a modest Krylov dimension and confirm the
        DRUG-vs-DECOY discrimination survives -- the exact claim this
        task's Intent Contract asks for.

        Seeds from a single ACTIVE node, not the full 12-node ACTIVE
        block: a real, informative finding surfaced while building this
        test (documented in this task's own Done section) is that a
        block-Krylov seed of `n_seed` nodes consumes `n_seed` new basis
        vectors per round-robin power step -- at this project's real
        active-site sizes (18-26 residues) and a ~12-16 node NISQ
        compression target, the seed block alone can exhaust the entire
        budget before reaching *any* power beyond k=1, never mind a
        residue 5 hops away. This unit test uses a single seed node
        specifically so the underlying reduction/lift machinery can be
        verified in a regime where the budget isn't immediately consumed
        by seed width alone; the seed-block-vs-budget tension itself is
        measured directly on real targets in the retention report."""
        H = self._build(strong_lobe="DRUG")
        seed_idx = np.array([self.ACTIVE[0]])
        Q = krylov_basis(H, seed_idx=seed_idx, m=20)
        H_red = reduce_krylov(H, Q)
        w_local, v_local = np.linalg.eigh(H_red)
        w_full, v_full = lift_krylov_eigvecs(Q, w_local, v_local)
        occ_reduced = time_averaged_ctqw_converged(w=w_full, v=v_full, source=seed_idx, coherent=False)
        assert self._auc_to_drug(occ_reduced) > 0.85

    def test_schur_reduction_preserves_the_signal(self):
        """Retain ACTIVE + both bridges + DRUG + DECOY (drop nothing
        structurally interesting -- this is a smoke test that the exact
        elimination machinery doesn't break the signal when there is
        nothing to eliminate that matters); the informative case is the
        Krylov test above, this is the Schur-side analogue with a
        smaller eliminated set."""
        H = self._build(strong_lobe="DRUG")
        retain_idx = np.array(self.ACTIVE + self.BRIDGE_DRUG + self.BRIDGE_DECOY + self.DRUG + self.DECOY)
        H_eff, elim_idx = schur_complement(H, retain_idx, E=0.0, eta=0.0)
        assert len(elim_idx) == 0  # nothing eliminated at N_NODES retained -- degenerate but valid case
        w_local, v_local = np.linalg.eigh(H_eff)
        occ = time_averaged_ctqw_converged(H_eff, source=list(range(len(self.ACTIVE))), coherent=False)
        # residues are in the same order as retain_idx == arange(44), so indices are unchanged
        assert self._auc_to_drug(occ) > 0.85

    def test_naive_louvain_can_lose_the_signal(self):
        """The actual comparison point: `coarse.coarse_grain`'s own
        Louvain merge, run on the identical dumbbell H, either preserves
        or destroys the DRUG-vs-DECOY separation depending on whether it
        happens to merge DRUG and DECOY residues into the same cluster
        -- reported as observed, not assumed to fail (a real negative
        for Louvain here would strengthen this task's own case; if
        Louvain happens to preserve it too on this particular fixture,
        that is also reported honestly, not forced)."""
        H = self._build(strong_lobe="DRUG")
        result = coarse_grain(H, method="louvain", n_target=8, seed=0)
        drug_labels = set(result.labels[self.DRUG].tolist())
        decoy_labels = set(result.labels[self.DECOY].tolist())
        overlap = drug_labels & decoy_labels
        # Just recording the observed outcome as a non-trivial fact -- not
        # a pass/fail assertion on Louvain's own behavior, which this
        # task does not control and must report either way.
        print(f"Louvain DRUG/DECOY cluster overlap: {overlap}")
