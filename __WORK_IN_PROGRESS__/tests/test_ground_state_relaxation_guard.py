"""TASK-0095 coverage -- propagators.ground_state_relaxation (formerly
`heat`) and its indefinite-operator guard.

Source: `REVIEW-2026-07-13-proximity-confound-and-propagator-semantics.md`,
finding P1-B, executed against real `build_H_new`: its spectrum is
indefinite (min ~ -1.83, max ~ 10+), `Spearman(old-heat(H_new, t=20),
|ground state|^2) = 0.998` -- the function was returning the operator's
ground-state density, not diffusing anything, and the clip/renormalise step
silently masked a 13-order-of-magnitude L1-norm divergence before that.

Per this task's own Planned Validation: a test asserting the guard fires on
`build_H_new`'s real indefinite spectrum and does not fire on a genuine PSD
Laplacian; a check that no remaining doc/report artifact uses "classical
diffusion" language for the renamed function's output.
"""
from pathlib import Path
import sys
import warnings

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.hamiltonians import H2_combinatorial_laplacian, build_H_new  # noqa: E402
from allostery.propagators import ground_state_relaxation  # noqa: E402


def _helix_coords(n: int) -> np.ndarray:
    theta = np.arange(n) * (100.0 * np.pi / 180.0)
    return np.column_stack([
        2.3 * np.cos(theta),
        2.3 * np.sin(theta),
        1.5 * np.arange(n, dtype=float),
    ])


N = 20
COORDS = _helix_coords(N)
BFACTORS = np.full(N, 25.0)


class TestIndefiniteGuardFires:
    def test_warns_on_build_h_new_real_indefinite_spectrum(self):
        """Sanity precondition, then the actual guard assertion -- confirms
        this test exercises the real bug, not a synthetic stand-in."""
        H = build_H_new(COORDS, BFACTORS)
        w = np.linalg.eigvalsh(H)
        assert w.min() < -1e-6, "fixture must actually be indefinite (precondition for this test)"

        with pytest.warns(UserWarning, match="indefinite"):
            ground_state_relaxation(H, t=5.0, source=0)

    def test_strict_raises_instead_of_warning_on_indefinite_h(self):
        H = build_H_new(COORDS, BFACTORS)
        with pytest.raises(ValueError, match="indefinite"):
            ground_state_relaxation(H, t=5.0, source=0, strict=True)

    def test_warning_message_names_ground_state_not_diffusion(self):
        H = build_H_new(COORDS, BFACTORS)
        with pytest.warns(UserWarning) as record:
            ground_state_relaxation(H, t=5.0, source=0)
        message = str(record[0].message)
        assert "ground-state" in message
        assert "NOT classical diffusion" in message


class TestPsdGuardDoesNotFire:
    def test_no_warning_on_genuine_psd_laplacian(self):
        H = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        w = np.linalg.eigvalsh(H)
        assert w.min() > -1e-9, "fixture must actually be PSD (precondition for this test)"

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            ground_state_relaxation(H, t=5.0, source=0)  # must not raise/warn

    def test_strict_does_not_raise_on_psd_laplacian(self):
        H = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        ground_state_relaxation(H, t=5.0, source=0, strict=True)  # must not raise


class TestGuardIsPurelyDiagnostic:
    """The guard must not change the computed output -- TASK-0095's own
    Constraints And Invariants: no numeric change for the PSD case, and for
    the indefinite case the *fix* is making the divergence visible, not
    altering how it's computed/clipped."""

    def test_output_identical_whether_or_not_warning_is_observed(self):
        H = build_H_new(COORDS, BFACTORS)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            p_ignored = ground_state_relaxation(H, t=5.0, source=0)
        with warnings.catch_warnings():
            warnings.simplefilter("always")
            p_seen = ground_state_relaxation(H, t=5.0, source=0)

        np.testing.assert_array_equal(p_ignored, p_seen)

    def test_psd_output_matches_independent_expm_reference(self):
        """Cross-check against a from-scratch scipy.linalg.expm computation
        (not this module's own eigh-based implementation) -- confirms the
        rename didn't silently change the math for the case that must stay
        numerically identical."""
        from scipy.linalg import expm

        H = H2_combinatorial_laplacian(COORDS, cutoff=10.0)
        t = 3.0
        p0 = np.zeros(N)
        p0[0] = 1.0

        expected = expm(-H * t) @ p0
        expected = np.clip(expected, 0.0, None)
        expected = expected / expected.sum()

        got = ground_state_relaxation(H, t=t, source=0)
        np.testing.assert_allclose(got, expected, atol=1e-8)


class TestNoStaleClassicalDiffusionFraming:
    """Grep-based check (this task's own Planned Validation): no remaining
    doc/report artifact still pairs "classical" with "heat" -- the exact
    false-claim pattern REVIEW-2026-07-13 P1-B found ("classical heat
    kernel"/"classical heat diffusion"/"CTQW vs classical heat")."""

    def _checked_files(self):
        root = Path(__file__).resolve().parent.parent
        return [
            root / "src" / "allostery" / "report.py",
            root / "src" / "allostery" / "analysis.py",
            root / "RESULTS.md",
        ]

    def test_classical_and_heat_do_not_co_occur(self):
        for path in self._checked_files():
            assert path.exists(), f"expected artifact not found: {path}"
            text = path.read_text()
            for line_no, line in enumerate(text.splitlines(), start=1):
                if "~~" in line:
                    continue  # explicitly struck-through/retracted historical text
                lower = line.lower()
                assert not ("classical" in lower and "heat" in lower), (
                    f"{path}:{line_no}: 'classical' and 'heat' co-occur -- "
                    f"likely the false diffusion claim TASK-0095 fixed: {line!r}"
                )
