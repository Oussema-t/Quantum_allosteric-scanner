"""Unit tests for backend/geometry.py (TASK-0030)."""
import numpy as np

from backend.geometry import kabsch_align, kabsch_apply, kabsch_fit


def _rotation_matrix(axis, angle):
    axis = axis / np.linalg.norm(axis)
    x, y, z = axis
    c, s = np.cos(angle), np.sin(angle)
    C = 1 - c
    return np.array([
        [x * x * C + c,     x * y * C - z * s, x * z * C + y * s],
        [y * x * C + z * s, y * y * C + c,     y * z * C - x * s],
        [z * x * C - y * s, z * y * C + x * s, z * z * C + c],
    ])


def test_recovers_known_rotation_and_translation():
    rng = np.random.default_rng(0)
    ref = rng.normal(size=(12, 3))
    R_true = _rotation_matrix(np.array([0.2, 1.0, 0.3]), 0.7)
    t_true = np.array([5.0, -2.0, 1.5])
    mobile = ref @ R_true.T + t_true

    aligned = kabsch_align(mobile, ref)

    assert np.allclose(aligned, ref, atol=1e-8)


def test_reflection_case_is_corrected_to_a_proper_rotation():
    rng = np.random.default_rng(1)
    ref = rng.normal(size=(10, 3))
    # a reflection (det = -1) composed with a rotation still has to be
    # recovered as the best proper (det = +1) rotation, not mirrored.
    reflect = np.diag([1.0, 1.0, -1.0])
    R_true = _rotation_matrix(np.array([1.0, 0.0, 0.0]), 1.1)
    mobile = ref @ (R_true @ reflect).T

    R, mc, rc = kabsch_fit(mobile, ref)

    assert np.isclose(np.linalg.det(R), 1.0, atol=1e-8)


def test_apply_reuses_a_fit_on_a_different_point_set():
    rng = np.random.default_rng(2)
    ref = rng.normal(size=(8, 3))
    R_true = _rotation_matrix(np.array([0.0, 0.0, 1.0]), 0.4)
    t_true = np.array([1.0, 2.0, 3.0])
    mobile = ref @ R_true.T + t_true

    extra = rng.normal(size=(5, 3))
    extra_in_mobile_frame = extra @ R_true.T + t_true

    R, mc, rc = kabsch_fit(mobile, ref)
    recovered_extra = kabsch_apply(extra_in_mobile_frame, R, mc, rc)

    assert np.allclose(recovered_extra, extra, atol=1e-8)
