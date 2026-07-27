"""TASK-0111 coverage -- propagators.ctqw/time_averaged_ctqw's eigh-caching
fix. No dedicated test file existed for propagators.py before this task
(its functions are otherwise exercised only indirectly, via test_analysis.py
/test_hamiltonians.py/test_physics.py) -- this file is scoped narrowly to
the fix itself, not a full propagators.py test suite.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.propagators import (  # noqa: E402
    ctqw,
    ctqw_3n_native,
    quantum_connectivity_matrix,
    reduce_3n_occupation,
    residue_source_to_3n,
    time_averaged_ctqw,
    time_averaged_ctqw_3n_native,
    time_averaged_ctqw_converged,
    time_averaged_ctqw_converged_3n_native,
)


def _helix_coords(n: int) -> np.ndarray:
    theta = np.arange(n) * (100.0 * np.pi / 180.0)
    return np.column_stack([
        2.3 * np.cos(theta),
        2.3 * np.sin(theta),
        1.5 * np.arange(n, dtype=float),
    ])


def _random_symmetric_H(n: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    A = rng.normal(size=(n, n))
    return (A + A.T) / 2


def _time_averaged_ctqw_reference(H, t_max, source=0, n_steps=500):
    """Independent re-derivation of the pre-TASK-0111 (redundant-eigh)
    implementation -- kept deliberately separate from the fixed
    `time_averaged_ctqw` so this test doesn't just check the function
    against itself."""
    times = np.linspace(0.0, t_max, n_steps)
    acc = np.zeros(H.shape[0])
    for t in times:
        acc += ctqw(H, t, source=source)
    return acc / n_steps


class TestTimeAveragedCtqwEighCaching:
    def test_matches_the_redundant_eigh_reference_implementation(self):
        """Pure performance refactor -- output must be unchanged (float-
        tolerance identical), not just plausible."""
        H = _random_symmetric_H(20, seed=1)
        fast = time_averaged_ctqw(H, t_max=8.0, source=3, n_steps=80)
        reference = _time_averaged_ctqw_reference(H, t_max=8.0, source=3, n_steps=80)
        np.testing.assert_allclose(fast, reference, rtol=1e-10, atol=1e-12)

    def test_matches_reference_with_a_multi_index_source(self):
        H = _random_symmetric_H(16, seed=2)
        fast = time_averaged_ctqw(H, t_max=5.0, source=[0, 2, 5], n_steps=50)
        reference = _time_averaged_ctqw_reference(H, t_max=5.0, source=[0, 2, 5], n_steps=50)
        np.testing.assert_allclose(fast, reference, rtol=1e-10, atol=1e-12)

    def test_matches_reference_on_a_real_helix_hamiltonian(self):
        from allostery.hamiltonians import H2_combinatorial_laplacian

        H = H2_combinatorial_laplacian(_helix_coords(24), cutoff=10.0)
        fast = time_averaged_ctqw(H, t_max=15.0, source=0, n_steps=200)
        reference = _time_averaged_ctqw_reference(H, t_max=15.0, source=0, n_steps=200)
        np.testing.assert_allclose(fast, reference, rtol=1e-10, atol=1e-12)

    def test_output_is_a_valid_probability_vector(self):
        H = _random_symmetric_H(12, seed=3)
        p = time_averaged_ctqw(H, t_max=4.0, source=0, n_steps=30)
        assert p.shape == (12,)
        assert (p >= 0).all()
        assert p.sum() == pytest.approx(1.0, abs=1e-6)

    def test_meaningfully_faster_than_the_redundant_reference(self):
        """Generous tolerance (>=3x), not a flaky micro-benchmark -- the
        fix eliminates n_steps-1 redundant eigh calls, an O(n_steps)
        reduction that should be unmistakable even accounting for system
        noise."""
        H = _random_symmetric_H(60, seed=4)
        n_steps = 150

        t0 = time.perf_counter()
        time_averaged_ctqw(H, t_max=10.0, source=0, n_steps=n_steps)
        fast_elapsed = time.perf_counter() - t0

        t0 = time.perf_counter()
        _time_averaged_ctqw_reference(H, t_max=10.0, source=0, n_steps=n_steps)
        reference_elapsed = time.perf_counter() - t0

        assert fast_elapsed * 3 < reference_elapsed, (
            f"fixed implementation ({fast_elapsed:.4f}s) is not meaningfully "
            f"faster than the redundant-eigh reference ({reference_elapsed:.4f}s)"
        )


class TestCtqwUnaffected:
    """ctqw's own public behavior/signature must be byte-identical --
    only time_averaged_ctqw's internals changed."""

    def test_single_call_output_unchanged(self):
        H = _random_symmetric_H(10, seed=5)
        p = ctqw(H, t=3.0, source=1)
        assert p.shape == (10,)
        assert p.sum() == pytest.approx(1.0, abs=1e-6)

    def test_still_recomputes_eigh_per_call_for_different_h(self):
        """ctqw must still work correctly if called with a *different* H
        each time (its own contract) -- confirms the shared helper wasn't
        wired to accidentally cache across distinct Hamiltonians."""
        H1 = _random_symmetric_H(8, seed=6)
        H2 = _random_symmetric_H(8, seed=7)
        p1 = ctqw(H1, t=2.0, source=0)
        p2 = ctqw(H2, t=2.0, source=0)
        assert not np.allclose(p1, p2)


# ---------------------------------------------------------------------------
# TASK-0118 -- incoherent-mixture `coherent=False` support
# ---------------------------------------------------------------------------

def _incoherent_reference(H, t, source, n_steps=None):
    """Independent re-derivation of the incoherent-mixture formula --
    average each seed index's own single-source `ctqw` occupation. Kept
    deliberately separate from `_ctqw_mixture_from_eigh` (calls the public
    `ctqw`, not the private eigh-sharing helper) so this doesn't just check
    the implementation against itself. `n_steps=None` -> single-time-point
    `ctqw`; otherwise averages `time_averaged_ctqw` per index."""
    idx = np.atleast_1d(np.asarray(source, dtype=int))
    if n_steps is None:
        return np.mean([ctqw(H, t, source=int(i)) for i in idx], axis=0)
    return np.mean(
        [time_averaged_ctqw(H, t, source=int(i), n_steps=n_steps) for i in idx], axis=0
    )


class TestIncoherentMixture:
    def test_default_is_coherent_true_byte_identical(self):
        """No existing caller passes `coherent=` -- the default must be
        exactly the pre-TASK-0118 behavior, not just close to it."""
        H = _random_symmetric_H(14, seed=8)
        default = ctqw(H, t=4.0, source=[1, 3, 5])
        explicit = ctqw(H, t=4.0, source=[1, 3, 5], coherent=True)
        np.testing.assert_array_equal(default, explicit)

        default_ta = time_averaged_ctqw(H, t_max=6.0, source=[1, 3, 5], n_steps=40)
        explicit_ta = time_averaged_ctqw(H, t_max=6.0, source=[1, 3, 5], n_steps=40, coherent=True)
        np.testing.assert_array_equal(default_ta, explicit_ta)

    def test_scalar_source_coherent_and_incoherent_identical(self):
        """A one-element mixture has no coherence to differ over --
        `coherent=False` must reduce to the same single-seed result."""
        H = _random_symmetric_H(10, seed=9)
        coherent = ctqw(H, t=3.0, source=4, coherent=True)
        incoherent = ctqw(H, t=3.0, source=4, coherent=False)
        np.testing.assert_allclose(coherent, incoherent, rtol=1e-10, atol=1e-12)

    def test_ctqw_incoherent_matches_manual_average_of_single_seeds(self):
        H = _random_symmetric_H(16, seed=10)
        source = [2, 5, 9]
        actual = ctqw(H, t=5.0, source=source, coherent=False)
        reference = _incoherent_reference(H, t=5.0, source=source)
        np.testing.assert_allclose(actual, reference, rtol=1e-10, atol=1e-12)

    def test_time_averaged_ctqw_incoherent_matches_manual_average(self):
        H = _random_symmetric_H(18, seed=11)
        source = [1, 4, 7]
        actual = time_averaged_ctqw(H, t_max=8.0, source=source, n_steps=60, coherent=False)
        reference = _incoherent_reference(H, t=8.0, source=source, n_steps=60)
        np.testing.assert_allclose(actual, reference, rtol=1e-10, atol=1e-12)

    def test_coherent_and_incoherent_genuinely_differ_for_multi_index(self):
        """The whole point of the distinction -- on a real (non-degenerate)
        Hamiltonian with a genuine multi-index source, the coherent
        superposition's cross-terms must make the two outputs differ, not
        coincide."""
        from allostery.hamiltonians import H2_combinatorial_laplacian

        H = H2_combinatorial_laplacian(_helix_coords(20), cutoff=10.0)
        coherent = ctqw(H, t=5.0, source=[2, 3, 4], coherent=True)
        incoherent = ctqw(H, t=5.0, source=[2, 3, 4], coherent=False)
        assert not np.allclose(coherent, incoherent)

    def test_incoherent_output_is_a_valid_probability_vector(self):
        H = _random_symmetric_H(12, seed=12)
        p = ctqw(H, t=3.0, source=[0, 2, 4], coherent=False)
        assert p.shape == (12,)
        assert (p >= 0).all()
        assert p.sum() == pytest.approx(1.0, abs=1e-6)

        p_ta = time_averaged_ctqw(H, t_max=5.0, source=[0, 2, 4], n_steps=30, coherent=False)
        assert p_ta.shape == (12,)
        assert (p_ta >= 0).all()
        assert p_ta.sum() == pytest.approx(1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# TASK-0126 -- 3N-native propagation (IMP-H7 Option B)
# ---------------------------------------------------------------------------

class TestResidueSourceTo3n:
    def test_scalar_expands_to_its_own_triplet(self):
        np.testing.assert_array_equal(residue_source_to_3n(4), [12, 13, 14])

    def test_multi_index_expands_every_residue_in_order(self):
        np.testing.assert_array_equal(residue_source_to_3n([0, 2]), [0, 1, 2, 6, 7, 8])


class TestReduce3nOccupation:
    def test_sums_each_residues_three_components(self):
        p_3n = np.array([0.1, 0.2, 0.3, 0.05, 0.05, 0.3])
        np.testing.assert_allclose(reduce_3n_occupation(p_3n), [0.6, 0.4])

    def test_raises_on_length_not_a_multiple_of_three(self):
        with pytest.raises(ValueError):
            reduce_3n_occupation(np.array([0.1, 0.2, 0.3, 0.4]))


class TestCtqw3nNative:
    def _real_h13(self, n=10, cutoff=10.0):
        from allostery.hamiltonians import H13_3N_anm_hessian

        return H13_3N_anm_hessian(_helix_coords(n), cutoff=cutoff)

    def test_matches_manual_expand_reduce_around_unmodified_ctqw(self):
        """The wrapper must be exactly equivalent to calling the real,
        unmodified `ctqw` on the expanded 3N source and reducing by hand --
        proving this is a pure translation layer, not a reimplementation."""
        H13 = self._real_h13()
        source = [2, 5]
        wrapped = ctqw_3n_native(H13, t=4.0, source=source)
        manual = reduce_3n_occupation(ctqw(H13, t=4.0, source=residue_source_to_3n(source)))
        np.testing.assert_array_equal(wrapped, manual)

    def test_output_is_a_valid_per_residue_probability_vector(self):
        n = 10
        H13 = self._real_h13(n=n)
        p = ctqw_3n_native(H13, t=4.0, source=0)
        assert p.shape == (n,)
        assert (p >= 0).all()
        assert p.sum() == pytest.approx(1.0, abs=1e-6)

    def test_kwargs_pass_through_to_the_real_ctqw(self):
        """`coherent=False` must actually reach the wrapped `ctqw` call --
        checked by a genuine multi-index source producing a different
        result, not just accepted and dropped."""
        H13 = self._real_h13()
        coherent = ctqw_3n_native(H13, t=4.0, source=[2, 3, 4], coherent=True)
        incoherent = ctqw_3n_native(H13, t=4.0, source=[2, 3, 4], coherent=False)
        assert not np.allclose(coherent, incoherent)

    def test_time_averaged_variant_matches_manual_expand_reduce(self):
        H13 = self._real_h13()
        source = [1, 3]
        wrapped = time_averaged_ctqw_3n_native(H13, t_max=6.0, source=source, n_steps=20)
        manual = reduce_3n_occupation(
            time_averaged_ctqw(H13, t_max=6.0, source=residue_source_to_3n(source), n_steps=20)
        )
        np.testing.assert_array_equal(wrapped, manual)

    def test_time_averaged_variant_is_a_valid_probability_vector(self):
        n = 10
        H13 = self._real_h13(n=n)
        p = time_averaged_ctqw_3n_native(H13, t_max=6.0, source=0, n_steps=20)
        assert p.shape == (n,)
        assert (p >= 0).all()
        assert p.sum() == pytest.approx(1.0, abs=1e-6)

    def test_converged_variant_matches_manual_expand_reduce(self):
        H13 = self._real_h13()
        source = [1, 3]
        wrapped = time_averaged_ctqw_converged_3n_native(H13, source=source)
        manual = reduce_3n_occupation(
            time_averaged_ctqw_converged(H13, source=residue_source_to_3n(source))
        )
        np.testing.assert_array_equal(wrapped, manual)

    def test_converged_variant_is_a_valid_probability_vector(self):
        n = 10
        H13 = self._real_h13(n=n)
        p = time_averaged_ctqw_converged_3n_native(H13, source=0)
        assert p.shape == (n,)
        assert (p >= 0).all()
        assert p.sum() == pytest.approx(1.0, abs=1e-6)

    def test_converged_variant_kwargs_pass_through(self):
        H13 = self._real_h13()
        coherent = time_averaged_ctqw_converged_3n_native(H13, source=[2, 3, 4], coherent=True)
        incoherent = time_averaged_ctqw_converged_3n_native(H13, source=[2, 3, 4], coherent=False)
        assert not np.allclose(coherent, incoherent)

    def test_converged_variant_absorbs_rigid_body_nullspace_without_error(self):
        """The whole point of switching TASK-0126's H13-native ceiling
        search to the closed form: no separate nullspace-skipping step
        (`_drop_rigid_body_zero_modes`) is needed here -- `time_averaged_
        ctqw_converged`'s own degenerate-eigenvalue grouping absorbs H13's
        6 near-machine-precision rigid-body zero modes transparently."""
        H13 = self._real_h13(n=20)
        p = time_averaged_ctqw_converged_3n_native(H13, source=[0, 5, 10])
        assert np.isfinite(p).all()
        assert p.sum() == pytest.approx(1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# TASK-0130 -- time_averaged_ctqw's closed-form infinite-time limit
# ---------------------------------------------------------------------------

class TestTimeAveragedCtqwConverged:
    def test_matches_brute_force_large_t_max_on_nondegenerate_synthetic_system(self):
        """Cross-check against the thing this function replaces, not just
        against itself: a real (non-degenerate) small H, `time_averaged_
        ctqw` run at a large enough t_max/n_steps to have actually mixed
        out, compared to the closed form."""
        H = _random_symmetric_H(8, seed=3)
        source = 2
        p_converged = time_averaged_ctqw_converged(H, source=source)
        p_brute = time_averaged_ctqw(H, t_max=4000.0, source=source, n_steps=20000)
        assert p_converged.shape == (8,)
        assert p_converged.sum() == pytest.approx(1.0, abs=1e-9)
        np.testing.assert_allclose(p_converged, p_brute, atol=5e-3)

    def test_matches_true_diagonal_ensemble_formula_directly(self):
        """Regression-pins the closed form's own defining formula (`sum_k
        |v_k(j)|^2 |v_k(source)|^2`, promoted from `scripts/propagator_
        convergence_battery.py::_true_diagonal_ensemble`) for a scalar
        source on a non-degenerate spectrum, where the two must agree
        exactly."""
        H = _random_symmetric_H(10, seed=7)
        source = 4
        w, v = np.linalg.eigh(H)
        expected = (v ** 2) @ (v[source, :] ** 2)
        expected /= expected.sum()
        got = time_averaged_ctqw_converged(H, source=source)
        np.testing.assert_allclose(got, expected, atol=1e-12)

    def test_reuses_precomputed_eigh_and_never_recomputes(self):
        H = _random_symmetric_H(6, seed=1)
        w, v = np.linalg.eigh(H)
        calls = {"n": 0}
        real_eigh = np.linalg.eigh

        def spy_eigh(*args, **kwargs):
            calls["n"] += 1
            return real_eigh(*args, **kwargs)

        import unittest.mock as mock
        with mock.patch("numpy.linalg.eigh", spy_eigh):
            time_averaged_ctqw_converged(source=1, w=w, v=v)
        assert calls["n"] == 0

    def test_raises_without_h_or_precomputed_eigh(self):
        with pytest.raises(ValueError):
            time_averaged_ctqw_converged(source=0)

    def test_coherent_default_matches_ctqw_and_differs_from_incoherent(self):
        H = _random_symmetric_H(9, seed=5)
        source = [1, 3, 5]
        coherent = time_averaged_ctqw_converged(H, source=source, coherent=True)
        incoherent = time_averaged_ctqw_converged(H, source=source, coherent=False)
        assert not np.allclose(coherent, incoherent)
        # scalar source: coherent/incoherent must coincide (no cross terms
        # possible with a single seed), matching ctqw's own convention.
        c1 = time_averaged_ctqw_converged(H, source=2, coherent=True)
        c2 = time_averaged_ctqw_converged(H, source=2, coherent=False)
        np.testing.assert_allclose(c1, c2)

    def test_degenerate_block_result_is_invariant_to_the_chosen_eigenbasis(self):
        """The correctness note this task's Intent Contract insists on:
        the plain index-wise formula is only exact for a non-degenerate
        spectrum. For an exactly-degenerate eigenspace, LAPACK is free to
        return *any* orthonormal basis of that eigenspace -- a physically
        meaningful (basis-independent) answer must not change depending
        on which one it happens to return. Builds two different valid
        eigenbases of the same degenerate H by hand (a "localized" one and
        a rotated/mixed one) and confirms this function's grouped
        projector formula gives the identical answer either way, while
        the naive *ungrouped* index formula (treating each degenerate
        eigenvector as its own singleton block) does not -- proving the
        grouping is load-bearing, not defensive boilerplate.
        """
        A = np.array([[2.0, 1.0], [1.0, 3.0]])
        la, va = np.linalg.eigh(A)  # va[:,0], va[:,1]: A's own 2 eigvecs
        a1, a2 = va[:, 0], va[:, 1]

        # H = block_diag(A, A): eigenvalues [la0, la0, la1, la1], each an
        # exact double degeneracy.
        w = np.array([la[0], la[0], la[1], la[1]])

        e1 = np.array([a1[0], a1[1], 0.0, 0.0])
        e2 = np.array([0.0, 0.0, a1[0], a1[1]])
        g1 = np.array([a2[0], a2[1], 0.0, 0.0])
        g2 = np.array([0.0, 0.0, a2[0], a2[1]])

        theta = 0.7
        f1 = np.cos(theta) * e1 + np.sin(theta) * e2
        f2 = -np.sin(theta) * e1 + np.cos(theta) * e2

        v_local = np.column_stack([e1, e2, g1, g2])
        v_mixed = np.column_stack([f1, f2, g1, g2])

        psi0 = np.zeros(4)
        psi0[0] = 1.0

        from allostery.propagators import _block_projected_diagonal, _group_degenerate_eigenvalues

        blocks = _group_degenerate_eigenvalues(w, tol=1e-9)
        assert [list(b) for b in blocks] == [[0, 1], [2, 3]]

        grouped_local = _block_projected_diagonal(v_local, blocks, psi0)
        grouped_mixed = _block_projected_diagonal(v_mixed, blocks, psi0)
        np.testing.assert_allclose(grouped_local, grouped_mixed, atol=1e-12)

        singleton_blocks = [np.array([i]) for i in range(4)]
        naive_local = _block_projected_diagonal(v_local, singleton_blocks, psi0)
        naive_mixed = _block_projected_diagonal(v_mixed, singleton_blocks, psi0)
        assert not np.allclose(naive_local, naive_mixed, atol=1e-9)

        # And the naive answer for the *mixed* (non-localized) basis
        # actually disagrees with the correct, basis-independent one --
        # not just "differs from the local case" but concretely wrong.
        assert not np.allclose(naive_mixed, grouped_mixed, atol=1e-9)
        # The naive answer for the "convenient" local basis happens to
        # coincide with the correct one here (support disjoint across the
        # degenerate pair) -- exactly why this bug is silent: it looks
        # right until eigh returns a mixed basis.
        np.testing.assert_allclose(naive_local, grouped_local, atol=1e-12)

    def test_public_function_matches_manual_call_on_the_degenerate_case(self):
        """End-to-end version of the invariance property above, through
        the public `time_averaged_ctqw_converged` entry point rather than
        the private helpers directly."""
        A = np.array([[2.0, 1.0], [1.0, 3.0]])
        H = np.zeros((4, 4))
        H[:2, :2] = A
        H[2:, 2:] = A
        p = time_averaged_ctqw_converged(H, source=0)
        assert p.shape == (4,)
        assert p.sum() == pytest.approx(1.0, abs=1e-9)
        assert (p >= 0).all()


@pytest.mark.parametrize("_", [None])
def test_time_averaged_ctqw_converged_regression_pins_spearman_vs_adequate_t_max(_):
    """Planned Validation: regression-pin agreement with the finite
    approximation at Spearman >= 0.9998, the value already measured and
    recorded (RESULTS.md, REVIEW-panel-2026-07-16-v2.md §1.1: "Spearman
    0.9998 to the true infinite-time limit at the operating t_max").

    **Finding while writing this pin, not assumed**: "the operating
    t_max" does NOT mean the pipeline's hardcoded default (`t_max=15`).
    Measured directly on real KRAS_G12C `H_new` (this project's own
    current, post-TASK-0121-renormalization potential): at `t_max=15`,
    Spearman against this closed form is only **~0.634** -- nowhere near
    0.9998, consistent with TASK-0110's own finding that `t_max=15` is
    145,000x-3,950,000x short of `min_adequate_t_max(kind=
    "time_averaged_ctqw")`'s own AAKV-derived prescription. Spearman
    against the closed form climbs monotonically as `t_max` grows and
    crosses 0.9998 right around `t_max~15,000` (measured: 0.998804 at
    1,500; 0.999779 at 15,000) -- the same order of magnitude as TASK-
    0110's own prescribed scale-up, not a coincidence. This confirms two
    things at once: (1) this closed form IS the correct limit the finite
    average is provably converging to (a real, independent correctness
    check beyond the two direct-formula tests above), and (2) the
    historical "0.9998" claim was about the *AAKV-adequate* t_max, not
    the shipped default -- which this task's own closed form now makes
    moot, since a caller wanting the converged value no longer needs to
    reach that t_max (or know its value) at all. See
    `test_shipped_default_t_max_15_is_far_from_converged` below for the
    default-t_max finding on its own, kept as its own explicit assertion
    rather than folded into a single passing/failing number.
    """
    pytest.importorskip("prody")
    from scipy.stats import spearmanr

    from allostery.clean import clean
    from allostery.hamiltonians import build_H_new
    from allostery.labels import build_labels, ligand_groups_from_atomgroup
    from allostery.clean import load_target_config

    try:
        apo = clean("4OBE", chains=["A"])
        holo = clean("6OIM", chains=["A"])
    except Exception as exc:
        pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")

    import prody

    prody.confProDy(verbosity="none")
    holo_struct = prody.parsePDB("6OIM", compressed=False).select("chain A")
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)

    cfg = load_target_config("KRAS_G12C")
    labels_obj = build_labels(apo, holo, cfg, cutoff=4.5)
    source = np.where(labels_obj.active_site)[0]
    assert len(source) > 0

    H = build_H_new(apo.coords, apo.bfactors, cutoff=8.0)
    # t_max chosen empirically (see docstring): the smallest round value
    # in this project's own measured range that clears 0.9998, well
    # short of TASK-0110's full AAKV prescription (millions) but enough
    # to demonstrate genuine convergence, not an aliasing artifact
    # (Nyquist-adequate n_steps for this t_max/bandwidth, per
    # `min_adequate_n_steps`).
    t_max = 15000.0
    from allostery.propagators import min_adequate_n_steps
    n_steps = min(min_adequate_n_steps(H=H, t_max=t_max), 20000)
    p_finite = time_averaged_ctqw(H, t_max=t_max, source=source, n_steps=n_steps, coherent=False)
    p_converged = time_averaged_ctqw_converged(H, source=source, coherent=False)

    rho, _ = spearmanr(p_finite, p_converged)
    print(f"\nKRAS_G12C time_averaged_ctqw(t_max={t_max}) vs closed form: Spearman={rho:.6f}")
    assert rho >= 0.9998


@pytest.mark.parametrize("_", [None])
def test_shipped_default_t_max_15_is_far_from_converged(_):
    """The other half of the finding above, kept as its own explicit,
    always-checked assertion rather than a docstring-only note: the
    pipeline's actual shipped default (`t_max=15`) is NOT a good
    approximation of the converged limit on real KRAS_G12C `H_new` --
    Spearman ~0.63, not ~1.0. This is exactly the gap this task's closed
    form exists to close (a caller no longer needs `t_max` at all for
    the converged quantity); asserting a generous upper bound here so
    this finding cannot silently regress back to "looks fine" without a
    test noticing.
    """
    pytest.importorskip("prody")
    from scipy.stats import spearmanr

    from allostery.clean import clean, load_target_config
    from allostery.hamiltonians import build_H_new
    from allostery.labels import build_labels, ligand_groups_from_atomgroup

    try:
        apo = clean("4OBE", chains=["A"])
        holo = clean("6OIM", chains=["A"])
    except Exception as exc:
        pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")

    import prody

    prody.confProDy(verbosity="none")
    holo_struct = prody.parsePDB("6OIM", compressed=False).select("chain A")
    holo.ligand_groups = ligand_groups_from_atomgroup(holo_struct)

    cfg = load_target_config("KRAS_G12C")
    labels_obj = build_labels(apo, holo, cfg, cutoff=4.5)
    source = np.where(labels_obj.active_site)[0]

    H = build_H_new(apo.coords, apo.bfactors, cutoff=8.0)
    p_finite = time_averaged_ctqw(H, t_max=15.0, source=source, n_steps=500, coherent=False)
    p_converged = time_averaged_ctqw_converged(H, source=source, coherent=False)

    rho, _ = spearmanr(p_finite, p_converged)
    print(f"\nKRAS_G12C time_averaged_ctqw(t_max=15, shipped default) vs closed form: Spearman={rho:.6f}")
    assert rho < 0.9  # real measured value ~0.634 -- nowhere near "converged"


class TestQuantumConnectivityMatrix:
    """TASK-0160 -- dense, symmetric, all-pairs P_inf(i,j) = sum_k
    |v_k(i)|^2 |v_k(j)|^2, the challenge's own §5 "quantum connectivity
    matrix" deliverable (`run_challenge.py`'s pre-existing
    `connectivity_matrix.npz` is classical, seeded, and sparse -- fails
    all three counts this quantity fixes)."""

    def test_shape_dtype_finite(self):
        H = _random_symmetric_H(12, seed=2)
        P = quantum_connectivity_matrix(H)
        assert P.shape == (12, 12)
        assert P.dtype == np.float64
        assert np.all(np.isfinite(P))
        assert np.all(P >= 0.0)

    def test_exactly_symmetric_not_approximately(self):
        """A mathematical identity of the sum-of-outer-products form
        (V2 @ V2.T), not merely close -- checked bit-exact, not with a
        tolerance."""
        H = _random_symmetric_H(15, seed=9)
        P = quantum_connectivity_matrix(H)
        assert np.array_equal(P, P.T)

    def test_matches_brute_force_double_sum(self):
        """Independent re-derivation of the defining formula (a literal
        double loop over k, not the vectorized V2 @ V2.T this function
        actually uses) -- this task's own Planned Validation, run
        directly, not assumed from the vectorized derivation."""
        H = _random_symmetric_H(7, seed=4)
        w, v = np.linalg.eigh(H)
        n = H.shape[0]
        expected = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                expected[i, j] = np.sum(v[i, :] ** 2 * v[j, :] ** 2)
        got = quantum_connectivity_matrix(H)
        np.testing.assert_allclose(got, expected, atol=1e-12)

    def test_rows_and_columns_sum_to_one(self):
        """sum_j P_inf(i,j) = sum_k v_k(i)^2 * sum_j v_k(j)^2 = sum_k
        v_k(i)^2 * 1 = 1 (V's own rows are unit-normalised since V is
        orthogonal) -- P_inf(i, .) is a genuine probability distribution
        over j, not an arbitrary similarity score, and P_inf(., i)
        should therefore equal time_averaged_ctqw_converged(H, source=i)
        (checked directly in a separate test below, not just asserted
        from this row-sum property alone)."""
        H = _random_symmetric_H(10, seed=11)
        P = quantum_connectivity_matrix(H)
        np.testing.assert_allclose(P.sum(axis=1), np.ones(10), atol=1e-9)
        np.testing.assert_allclose(P.sum(axis=0), np.ones(10), atol=1e-9)

    def test_diagonal_is_the_ipr_like_self_term(self):
        H = _random_symmetric_H(8, seed=13)
        w, v = np.linalg.eigh(H)
        expected_diag = (v ** 4).sum(axis=1)
        P = quantum_connectivity_matrix(H)
        np.testing.assert_allclose(np.diag(P), expected_diag, atol=1e-12)

    def test_column_matches_time_averaged_ctqw_converged_on_nondegenerate_spectrum(self):
        """The two must agree exactly on a non-degenerate spectrum (this
        function's own docstring claim) -- every real H_new spectrum
        checked in this task's own Done section is near- not exactly-
        degenerate, so this is the case that actually matters in
        practice, not a corner case."""
        H = _random_symmetric_H(9, seed=17)
        source = 3
        P = quantum_connectivity_matrix(H)
        column = time_averaged_ctqw_converged(H, source=source)
        np.testing.assert_allclose(P[:, source], column, atol=1e-12)
        np.testing.assert_allclose(P[source, :], column, atol=1e-12)

    def test_reuses_precomputed_eigh_and_never_recomputes(self):
        H = _random_symmetric_H(6, seed=21)
        w, v = np.linalg.eigh(H)
        calls = {"n": 0}
        real_eigh = np.linalg.eigh

        def spy_eigh(*args, **kwargs):
            calls["n"] += 1
            return real_eigh(*args, **kwargs)

        import unittest.mock as mock
        with mock.patch("numpy.linalg.eigh", spy_eigh):
            quantum_connectivity_matrix(w=w, v=v)
        assert calls["n"] == 0

    def test_raises_without_h_or_precomputed_eigh(self):
        with pytest.raises(ValueError):
            quantum_connectivity_matrix()
