"""TASK-0072 -- golden-value cross-tree drift test.

`backend/analysis.py` and `__WORK_IN_PROGRESS__/src/allostery/potentials.py`
each have their own, independently-implemented copy of the shared
Kirchhoff/DCC math (`_kirchhoff_eigh`/`_normalized_dcc`, TASK-0066) --
**ported, not cross-imported**, per TASK-0018's own explicit boundary
decision (different deployment/dependency footprints). "Ported" only stays
true if a future edit to either side that breaks numeric parity is caught
immediately -- this is that regression guard, not itself the dedup.

Runs against a single **fixed, synthetic, network-free reference structure**
(no RCSB fetch -- this must run in CI, fast and deterministically, not
depend on network reachability the way `backend/test_analysis.py`'s own
live-KRAS_G12C regression pin does) at **cutoff = 8.0 A**, the constant
[[TASK-0067]]'s own real benchmark resolved ("no significant difference in
the tested range... backend's live 8.0 A default does not need to change" --
confirmed still backend's own live default by reading `gnm_context`'s own
signature directly before pinning it here, not assumed from that old task's
text).

**Confirmed directly, not merely hoped for**: on this reference structure,
both trees' outputs are **bit-for-bit identical** (`np.array_equal`), not
merely float-close -- both sides construct the identical Kirchhoff matrix
from the identical coordinates via the identical formula and call the
identical LAPACK `eigh` routine, so there is no accumulated floating-point
divergence to tolerate. Exact equality is asserted throughout; a tolerance
fallback would only mask a real, catchable drift.
"""
from __future__ import annotations

import numpy as np
import pytest

from backend.analysis import _kirchhoff_eigh as _kirchhoff_eigh_backend
from backend.analysis import _normalized_dcc as _normalized_dcc_backend

from allostery.potentials import _kirchhoff_eigh as _kirchhoff_eigh_allostery
from allostery.potentials import _normalized_dcc as _normalized_dcc_allostery

GOLDEN_CUTOFF = 8.0  # TASK-0067's own resolved constant -- backend's live default, unchanged


def _reference_structure(n: int = 40, seed: int = 42) -> np.ndarray:
    """A fixed, deterministic, synthetic Ca-like point cloud -- a gently
    curved helical path with per-residue jitter, enough genuine local +
    non-adjacent 3D contact structure (a real protein-like fold, not a
    degenerate line or a bare ring -- see `allostery.chiral`'s own
    documented ring-topology null for why a degenerate fixture would be
    the wrong minimal case) for the Kirchhoff contact graph to be
    non-trivial. Fixed seed -- this literally is "the reference
    structure" the task asks to fix; changing this function's own output
    invalidates every golden value below and must not be done casually."""
    rng = np.random.default_rng(seed)
    t = np.arange(n, dtype=float)
    coords = np.column_stack([
        6.0 * np.cos(t * 0.5) + 0.3 * rng.standard_normal(n),
        6.0 * np.sin(t * 0.5) + 0.3 * rng.standard_normal(n),
        1.8 * t,
    ])
    return coords


class TestKirchhoffEighCrossTreeParity:
    """`_kirchhoff_eigh`'s own shared outputs -- `A` (contact adjacency),
    `w`/`U` (Kirchhoff eigendecomposition), `nz`/`winv` (pseudo-inverse
    ingredients). Backend returns `(A, deg, w, U, nz, winv)` (a 6-tuple,
    `deg` included since `gnm_context` needs it directly for `V_terminal`/
    `V_rigidity`); allostery returns `(A, w, U, nz, winv)` (a 5-tuple, `deg`
    omitted -- trivially `A.sum(1)` at any call site that needs it). This
    is a real, harmless signature difference (not itself a drift bug --
    each side's own return shape is unchanged by this task, per its own
    Out Of Scope), unpacked explicitly below rather than compared
    positionally."""

    def test_contact_adjacency_bit_identical(self):
        coords = _reference_structure()
        A_be, _deg, _w, _U, _nz, _winv = _kirchhoff_eigh_backend(coords, GOLDEN_CUTOFF)
        A_al, _w2, _U2, _nz2, _winv2 = _kirchhoff_eigh_allostery(coords, GOLDEN_CUTOFF)
        assert np.array_equal(A_be, A_al)

    def test_degree_matches_allostery_own_adjacency_sum(self):
        """Confirms the 6-tuple/5-tuple signature difference really is
        just `deg == A.sum(1)`, not a hidden second divergence -- checked
        directly, not assumed from the docstrings alone."""
        coords = _reference_structure()
        A_be, deg_be, _w, _U, _nz, _winv = _kirchhoff_eigh_backend(coords, GOLDEN_CUTOFF)
        A_al, _w2, _U2, _nz2, _winv2 = _kirchhoff_eigh_allostery(coords, GOLDEN_CUTOFF)
        assert np.array_equal(deg_be, A_al.sum(axis=1))

    def test_eigenvalues_bit_identical(self):
        coords = _reference_structure()
        _A, _deg, w_be, _U, _nz, _winv = _kirchhoff_eigh_backend(coords, GOLDEN_CUTOFF)
        _A2, w_al, _U2, _nz2, _winv2 = _kirchhoff_eigh_allostery(coords, GOLDEN_CUTOFF)
        assert np.array_equal(w_be, w_al)

    def test_eigenvectors_bit_identical(self):
        """Not just `allclose` -- eigenvectors from two independent
        `np.linalg.eigh` calls on the identical matrix, same LAPACK
        routine, are expected bit-identical (confirmed directly before
        writing this assertion, not assumed): no sign or ordering
        ambiguity actually manifests here since both sides diagonalize
        the exact same array, not merely a numerically-close one."""
        coords = _reference_structure()
        _A, _deg, _w, U_be, _nz, _winv = _kirchhoff_eigh_backend(coords, GOLDEN_CUTOFF)
        _A2, _w2, U_al, _nz2, _winv2 = _kirchhoff_eigh_allostery(coords, GOLDEN_CUTOFF)
        assert np.array_equal(U_be, U_al)

    def test_nonzero_mask_and_pseudo_inverse_eigenvalues_bit_identical(self):
        coords = _reference_structure()
        _A, _deg, _w, _U, nz_be, winv_be = _kirchhoff_eigh_backend(coords, GOLDEN_CUTOFF)
        _A2, _w2, _U2, nz_al, winv_al = _kirchhoff_eigh_allostery(coords, GOLDEN_CUTOFF)
        assert np.array_equal(nz_be, nz_al)
        assert np.array_equal(winv_be, winv_al)


class TestNormalizedDccCrossTreeParity:
    def test_normalized_dcc_bit_identical(self):
        coords = _reference_structure()
        _A, _deg, _w, U_be, _nz, winv_be = _kirchhoff_eigh_backend(coords, GOLDEN_CUTOFF)
        _A2, _w2, U_al, _nz2, winv_al = _kirchhoff_eigh_allostery(coords, GOLDEN_CUTOFF)
        dcc_be = _normalized_dcc_backend(U_be, winv_be)
        dcc_al = _normalized_dcc_allostery(U_al, winv_al)
        assert np.array_equal(dcc_be, dcc_al)

    def test_normalized_dcc_diagonal_is_self_correlation_one(self):
        """Both docstrings claim the diagonal is left as computed (self-
        correlation = 1, not zeroed) -- checked directly on both sides'
        actual output, not just read off the docstring text."""
        coords = _reference_structure()
        _A, _deg, _w, U_be, _nz, winv_be = _kirchhoff_eigh_backend(coords, GOLDEN_CUTOFF)
        _A2, _w2, U_al, _nz2, winv_al = _kirchhoff_eigh_allostery(coords, GOLDEN_CUTOFF)
        dcc_be = _normalized_dcc_backend(U_be, winv_be)
        dcc_al = _normalized_dcc_allostery(U_al, winv_al)
        np.testing.assert_allclose(np.diag(dcc_be), 1.0, atol=1e-10)
        np.testing.assert_allclose(np.diag(dcc_al), 1.0, atol=1e-10)


class TestGoldenCutoffConstant:
    def test_backend_default_cutoff_is_the_resolved_value(self):
        """TASK-0067's own resolved constant, pinned directly against
        `gnm_context`'s own live default signature -- if a future edit
        changes backend's default without updating this test, that is
        exactly the drift this task exists to catch."""
        import inspect

        from backend.analysis import gnm_context

        sig = inspect.signature(gnm_context)
        assert sig.parameters["cutoff"].default == GOLDEN_CUTOFF


class TestDriftIsActuallyDetected:
    """TASK-0103's own discipline, applied here: a drift detector that has
    never been seen to fire is not a detector. Construct real, deliberate
    one-line divergences and confirm the golden-value comparison above
    would actually catch each one -- not by monkeypatching the shipped
    functions (risking a real behavior change leaking into other tests),
    but by calling each side with an intentionally mismatched input that
    reproduces exactly the class of drift a real one-line edit would
    cause, and asserting the *comparison itself* -- the same `np.array_
    equal` this suite's own passing tests rely on -- returns False."""

    def test_a_different_cutoff_is_detected_as_drift(self):
        """The class of bug TASK-0018 originally found: three different
        cutoff values in live use with nothing to catch a fourth."""
        coords = _reference_structure()
        A_be, _deg, w_be, U_be, _nz, winv_be = _kirchhoff_eigh_backend(coords, GOLDEN_CUTOFF)
        A_al, w_al, U_al, _nz2, winv_al = _kirchhoff_eigh_allostery(coords, GOLDEN_CUTOFF + 1.5)
        assert not np.array_equal(A_be, A_al), "drift test itself is broken: a wrong cutoff went undetected"

    def test_a_one_line_dcc_formula_change_is_detected_as_drift(self):
        """Simulates a real one-line divergence in the DCC step (e.g. an
        accidental sign flip or an un-normalized covariance) without
        touching the shipped function -- computed independently, then
        compared with the same equality check the real tests use."""
        coords = _reference_structure()
        _A, _deg, _w, U_be, _nz, winv_be = _kirchhoff_eigh_backend(coords, GOLDEN_CUTOFF)
        dcc_be = _normalized_dcc_backend(U_be, winv_be)

        # A deliberately-wrong "ported" re-derivation: covariance left
        # un-normalized (the one-line bug this whole task exists to catch
        # -- forgetting the `/ np.outer(d, d)` step).
        Cov_unnormalized = (U_be * winv_be) @ U_be.T
        assert not np.array_equal(dcc_be, Cov_unnormalized), (
            "drift test itself is broken: an unnormalized covariance matched the real DCC"
        )

    def test_reference_structure_is_actually_reused_not_regenerated_differently(self):
        """A subtler drift risk this task's own design must avoid: if the
        two comparison calls above ever used two *different* calls to
        `_reference_structure` with different seeds, every "identical"
        assertion would pass trivially for the wrong reason (both sides
        would fail identically against different inputs, or -- worse --
        coincidentally match). Confirms the fixture itself is
        deterministic and reused, not a source of false confidence."""
        a = _reference_structure()
        b = _reference_structure()
        assert np.array_equal(a, b)
