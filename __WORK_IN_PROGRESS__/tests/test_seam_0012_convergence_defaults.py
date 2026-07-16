"""SEAM-0012 -- `propagators.check_convergence` (TASK-0109) exists, but the
real `t_max=15.0`/`n_steps=500` defaults hardcoded across `analysis.py`/
`ceiling.py`/`protocol.py` have never been checked against it. This is a
seam, not either side's own unit test's job (TASK-0109's own tests only
exercise the criterion in isolation; `analysis.py`/`ceiling.py`'s own tests
never call `check_convergence` at all) -- per `SEAM_PROTOCOL.md`'s own
worked example, this is exactly the shape of edge that stays green on both
sides while the composition is wrong.

`xfail` while OPEN (SEAM-0012's own status) -- this asserts the *currently
known* failure explicitly, not a hoped-for pass. Owner: TASK-0117.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.propagators import check_convergence  # noqa: E402

REAL_T_MAX_DEFAULT = 15.0  # analysis.py/ceiling.py/protocol.py's own literal,
# hardcoded at every one of ~11 call sites (see SEAM-0012's own file for the
# full list) -- not re-derived here, this is the actual constant in use.


@pytest.mark.xfail(reason="SEAM-0012 OPEN: real t_max=15.0 default not yet reconciled with check_convergence", strict=True)
def test_real_t_max_default_fails_bcr_abl1_spectral_gap_check():
    """TASK-0102's own already-computed real number for BCR_ABL1's `H_new`
    (no fresh network fetch needed -- this is that task's own cached
    finding, reused directly, matching this project's "reuse eigh where
    already computed" convention in spirit): spectral gap `w[1]-w[0] =
    0.1933`. `exp(-0.1933 * 15.0) = 0.055`, which fails `check_convergence`'s
    default `tol=0.01` -- the real, hardcoded `t_max=15.0` this pipeline
    ships with genuinely does not clear its own newly-built adequacy bar on
    real target data. This is the seam: the check exists (TASK-0109) but no
    consumer has been updated to either pass it or explicitly accept/
    document the shortfall (TASK-0117's job)."""
    w = np.array([0.0, 0.1933, 5.0, 8.0])  # BCR_ABL1 H_new's real gap, TASK-0102
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        report = check_convergence(w=w, t_max=REAL_T_MAX_DEFAULT, kind="ground_state_relaxation", tol=0.01)
    assert report.ok, (
        "expected to fail (SEAM-0012 OPEN) -- if this now passes, TASK-0117 "
        "has closed the seam and this test's xfail should be removed, not "
        "loosened"
    )
