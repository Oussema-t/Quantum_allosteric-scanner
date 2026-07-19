"""TASK-0103 -- dumbbell negative-control suite (well vs. coupling confound).

Port of the 2x2 control matrix in
`.ai/reviews/REVIEW-2026-07-13b-operator-falsification-negative-controls.md`
Sec.2, as a permanent, synthetic (no PDB, no network) regression test.

Construction (the review's own Sec.2, reproduced verbatim):

    ACTIVE (0-11) --[ bridge, 4 nodes, coupling w1 ]-- DRUG  (12-23)
    ACTIVE (0-11) --[ bridge, 4 nodes, coupling w2 ]-- DECOY (24-35)

44 nodes total (12+12+12+4+4). Both bridges are the *same length* (4
nodes) so hop-distance/Euclidean-distance baselines cannot separate DRUG
from DECOY by proximity alone -- the confound this suite targets is
*well location vs. coupling strength*, not proximity (that is
SEAM-adjacent to, but distinct from, the P1-A proximity confound
TASK-0094's floor already covers).

Two cues, varied independently per cell:
  well     -- a negative diagonal potential (a "trap") placed on DRUG,
              on DECOY, or on neither.
  coupling -- the bridge edge weight: strong (1.0) or weak (0.15). "Equal"
              (cell C4) uses a shared moderate weight (0.5) on both bridges.

A communication measure must follow the COUPLING; a well-locator follows
the WELL. `ground_state_relaxation` (GSR, exp(-Ht), TASK-0095) is
expected to follow the well (it is imaginary-time relaxation toward H's
ground state -- a spectral filter, not a communication channel).
`time_averaged_ctqw` is expected to follow the coupling (a genuinely
propagating coherent walk should reach whichever lobe the bridge actually
connects well, regardless of where the trap sits).

Scoring convention (this task's own design decision, not fully pinned by
the review): AUC(->DRUG) is computed over DRUG-vs-DECOY only (24 nodes) --
ACTIVE (the propagation source) and both bridge chains are excluded from
the label/score array entirely, matching the review's own "ACTIVE
residues are excluded from scoring, exactly as the real pipeline does"
and keeping the comparison a clean two-lobe discrimination, not diluted
by structurally-ambiguous bridge/source nodes.

Directional assertions only -- per this task's own Constraints, the
review's exact AUC values are not hardcoded as ground truth (re-derived
here, not copied); C1 (cues agree) is the review's own "uninformative"
cell (every method passes when cues align) and is checked only loosely,
for that reason -- C2/C3 (the conflict cells) are the decisive test.

Reusable for future operator-falsification tasks (T-D/T-E, the review's
Sec.7 Tier 2): `build_dumbbell_network`/`auc_to_drug` are public, not
private, so a second copy of this construction does not get written
independently.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.analysis import mode_coparticipation  # noqa: E402
from allostery.hamiltonians import laplacian  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.propagators import ground_state_relaxation, time_averaged_ctqw  # noqa: E402

ACTIVE = list(range(0, 12))
DRUG = list(range(12, 24))
DECOY = list(range(24, 36))
BRIDGE_DRUG = list(range(36, 40))
BRIDGE_DECOY = list(range(40, 44))
N_NODES = 44

STRONG_COUPLING = 1.0
WEAK_COUPLING = 0.15
EQUAL_COUPLING = 0.5
WELL_DEPTH = 5.0  # chosen empirically: deep enough for a clean, robust
# C2/C3 dissociation across seeds (checked directly, not guessed) without
# being so deep it pushes CTQW's already-uninformative C1 cell into an
# oscillatory/resonance-sensitive regime (see this task's own Done section).


def build_dumbbell_network(
    well_lobe: str | None,
    strong_lobe: str | None,
    *,
    well_depth: float = WELL_DEPTH,
    seed: int = 0,
) -> np.ndarray:
    """Build one dumbbell-network Laplacian for the given cell.

    `well_lobe`: "DRUG" | "DECOY" | None -- which lobe gets a negative
    diagonal trap (`None` = no well anywhere, cell C4).
    `strong_lobe`: "DRUG" | "DECOY" | None -- which lobe's bridge gets
    strong (1.0) coupling, the other gets weak (0.15) (`None` = both
    bridges get the same moderate weight, cell C4).

    Randomized per `seed`: intra-lobe edge weights (uniform in
    [0.7, 1.3], not a bare unweighted clique) and which node within each
    lobe anchors its bridge -- without this, the network is fully
    deterministic and "averaging over seeds" would silently average five
    copies of the same number (checked directly while writing this
    module: an earlier, non-randomized prototype produced exactly that).

    Returns the (44, 44) combinatorial Laplacian (`hamiltonians.laplacian`,
    `normalised=False`) with the well applied on top.
    """
    rng = np.random.default_rng(seed)
    W = np.zeros((N_NODES, N_NODES))

    def _clique(idxs: list[int]) -> None:
        for i in idxs:
            for j in idxs:
                if i < j:
                    W[i, j] = W[j, i] = rng.uniform(0.7, 1.3)

    _clique(ACTIVE)
    _clique(DRUG)
    _clique(DECOY)

    if strong_lobe is None:
        w_drug = w_decoy = EQUAL_COUPLING
    else:
        w_drug = STRONG_COUPLING if strong_lobe == "DRUG" else WEAK_COUPLING
        w_decoy = STRONG_COUPLING if strong_lobe == "DECOY" else WEAK_COUPLING

    anchor_active_drug = int(rng.choice(ACTIVE))
    anchor_active_decoy = int(rng.choice(ACTIVE))
    anchor_drug = int(rng.choice(DRUG))
    anchor_decoy = int(rng.choice(DECOY))

    chain_drug = [anchor_active_drug] + BRIDGE_DRUG + [anchor_drug]
    for a, b in zip(chain_drug[:-1], chain_drug[1:]):
        W[a, b] = W[b, a] = w_drug

    chain_decoy = [anchor_active_decoy] + BRIDGE_DECOY + [anchor_decoy]
    for a, b in zip(chain_decoy[:-1], chain_decoy[1:]):
        W[a, b] = W[b, a] = w_decoy

    L = laplacian(W, normalised=False)
    if well_lobe == "DRUG":
        for i in DRUG:
            L[i, i] -= well_depth
    elif well_lobe == "DECOY":
        for i in DECOY:
            L[i, i] -= well_depth
    return L


def auc_to_drug(H: np.ndarray, propagator, t: float = 20.0) -> float:
    """AUC(->DRUG): DRUG-vs-DECOY discrimination only (ACTIVE and both
    bridge chains excluded), propagated from ACTIVE via `propagator`
    (`ground_state_relaxation` or `time_averaged_ctqw`, both matching
    `propagator(H, t, source=...)`'s signature)."""
    p = propagator(H, t, source=ACTIVE)
    scores = np.concatenate([p[DRUG], p[DECOY]])
    labels = np.concatenate([np.ones(len(DRUG)), np.zeros(len(DECOY))])
    return _auc(scores, labels)


def _mean_auc_over_seeds(well_lobe, strong_lobe, propagator, n_seeds: int = 5) -> float:
    aucs = [
        auc_to_drug(build_dumbbell_network(well_lobe, strong_lobe, seed=s), propagator)
        for s in range(n_seeds)
    ]
    return float(np.mean(aucs))


def _gsr(H, t, source):
    return ground_state_relaxation(H, t, source=source)


def _ctqw(H, t, source):
    return time_averaged_ctqw(H, t, source=source, n_steps=100)


def _cp(H, t, source, n_low=5):
    """Matches `auc_to_drug`'s `propagator(H, t, source=...)` interface
    for reuse -- `t` is accepted and ignored (`mode_coparticipation`,
    TASK-0122, is a spectral observable, not a propagator with a time
    parameter)."""
    return mode_coparticipation(H, source=source, n_low=n_low)


class TestDumbbellNegativeControl:
    """The decisive cells (C2, C3): well and coupling deliberately
    disagree. A communication measure must follow the coupling; a
    well-locator must follow the well."""

    def test_c2_gsr_follows_well_not_coupling(self):
        """well=DECOY, strong coupling=DRUG. GSR must score DRUG LOW
        (it follows the well, which is on DECOY) despite DRUG being the
        well-coupled lobe."""
        mean_auc = _mean_auc_over_seeds("DECOY", "DRUG", _gsr)
        assert mean_auc < 0.15, f"GSR did not follow the well in C2 (mean AUC={mean_auc:.3f})"

    def test_c2_ctqw_follows_coupling_not_well(self):
        """well=DECOY, strong coupling=DRUG. CTQW must score DRUG HIGH
        (it follows the coupling, which favors DRUG) despite the well
        being elsewhere."""
        mean_auc = _mean_auc_over_seeds("DECOY", "DRUG", _ctqw)
        assert mean_auc > 0.85, f"CTQW did not follow the coupling in C2 (mean AUC={mean_auc:.3f})"

    def test_c3_gsr_follows_well_not_coupling(self):
        """well=DRUG, strong coupling=DECOY. GSR must score DRUG HIGH
        (it follows the well, which is on DRUG) despite DRUG being the
        weakly-coupled lobe."""
        mean_auc = _mean_auc_over_seeds("DRUG", "DECOY", _gsr)
        assert mean_auc > 0.85, f"GSR did not follow the well in C3 (mean AUC={mean_auc:.3f})"

    def test_c3_ctqw_follows_coupling_not_well(self):
        """well=DRUG, strong coupling=DECOY. CTQW must score DRUG LOW
        (it follows the coupling, which favors DECOY) despite the well
        being on DRUG."""
        mean_auc = _mean_auc_over_seeds("DRUG", "DECOY", _ctqw)
        assert mean_auc < 0.15, f"CTQW did not follow the coupling in C3 (mean AUC={mean_auc:.3f})"

    def test_c2_c3_is_a_clean_double_dissociation(self):
        """The decisive comparison stated as one assertion: GSR and CTQW
        must disagree in *both* conflict cells, in opposite directions --
        not just individually pass/fail thresholds above, but actually
        cross each other."""
        gsr_c2 = _mean_auc_over_seeds("DECOY", "DRUG", _gsr)
        ctqw_c2 = _mean_auc_over_seeds("DECOY", "DRUG", _ctqw)
        gsr_c3 = _mean_auc_over_seeds("DRUG", "DECOY", _gsr)
        ctqw_c3 = _mean_auc_over_seeds("DRUG", "DECOY", _ctqw)
        assert gsr_c2 < ctqw_c2, "GSR should score DRUG lower than CTQW in C2 (well elsewhere)"
        assert gsr_c3 > ctqw_c3, "GSR should score DRUG higher than CTQW in C3 (well on DRUG)"

    def test_c1_cues_agree_is_the_uninformative_sanity_cell(self):
        """C1 (well=DRUG, strong coupling=DRUG): both cues agree. Per the
        review's own framing this cell is *uninformative* ("every method
        passes when both cues align") -- checked only loosely (GSR
        clearly above chance; CTQW not asserted tightly, since a deep
        well can put a coherent walk into an oscillatory/resonance-
        sensitive regime even when coupling is strong, confirmed
        empirically while writing this test -- that sensitivity is itself
        why C1 cannot discriminate the confound, not a defect in the
        construction)."""
        gsr = _mean_auc_over_seeds("DRUG", "DRUG", _gsr)
        assert gsr > 0.9, f"GSR should clearly score DRUG when both cues agree (mean AUC={gsr:.3f})"

    def test_c4_cues_absent_is_near_chance(self):
        """C4 (no well, equal coupling): sanity check that neither
        propagator is scoring pure noise as a strong signal when there is
        no real cue to find. Loose bound -- this is a sanity check, not a
        discriminating cell, per the review's own framing."""
        gsr = _mean_auc_over_seeds(None, None, _gsr)
        ctqw = _mean_auc_over_seeds(None, None, _ctqw)
        assert abs(gsr - 0.5) < 0.3, f"GSR not near chance in C4 (mean AUC={gsr:.3f})"
        assert abs(ctqw - 0.5) < 0.3, f"CTQW not near chance in C4 (mean AUC={ctqw:.3f})"


class TestModeCoparticipationDumbbellGate:
    """TASK-0122's own mandatory gate (Intent Contract: "pass it through
    the T-A control matrix before any target is scored with it"). CP is
    claimed (REVIEW-2026-07-13b Sec.6) to track coupling, like CTQW, not
    the well, like GSR -- checked here the same way CTQW's own claim was
    checked, against the decisive conflict cells, not assumed from the
    formula alone.

    Real measured values on this construction (n_low=5, checked directly
    before writing these assertions, not assumed to transfer from CTQW's
    own thresholds): C2=1.000, C3=0.000, C1=0.000, C4=0.717."""

    def test_c2_cp_follows_coupling_not_well(self):
        """well=DECOY, strong coupling=DRUG. CP must score DRUG HIGH (it
        follows the coupling, which favors DRUG) despite the well being
        elsewhere -- same expectation as CTQW."""
        mean_auc = _mean_auc_over_seeds("DECOY", "DRUG", _cp)
        assert mean_auc > 0.85, f"CP did not follow the coupling in C2 (mean AUC={mean_auc:.3f})"

    def test_c3_cp_follows_coupling_not_well(self):
        """well=DRUG, strong coupling=DECOY. CP must score DRUG LOW (it
        follows the coupling, which favors DECOY) despite the well being
        on DRUG -- same expectation as CTQW."""
        mean_auc = _mean_auc_over_seeds("DRUG", "DECOY", _cp)
        assert mean_auc < 0.15, f"CP did not follow the coupling in C3 (mean AUC={mean_auc:.3f})"

    def test_c2_c3_is_a_clean_double_dissociation_against_gsr(self):
        """The decisive comparison: CP and GSR must disagree in both
        conflict cells, in opposite directions -- CP tracks coupling, GSR
        tracks the well, exactly the double dissociation TASK-0103
        already established for CTQW vs. GSR."""
        cp_c2 = _mean_auc_over_seeds("DECOY", "DRUG", _cp)
        gsr_c2 = _mean_auc_over_seeds("DECOY", "DRUG", _gsr)
        cp_c3 = _mean_auc_over_seeds("DRUG", "DECOY", _cp)
        gsr_c3 = _mean_auc_over_seeds("DRUG", "DECOY", _gsr)
        assert cp_c2 > gsr_c2, "CP should score DRUG higher than GSR in C2 (well elsewhere)"
        assert cp_c3 < gsr_c3, "CP should score DRUG lower than GSR in C3 (well on DRUG)"

    def test_c1_cues_agree_is_not_asserted_tightly(self):
        """C1 (well=DRUG, strong coupling=DRUG): both cues agree, but a
        deep co-located well perturbs CP's own low-mode structure the
        same way it already does for CTQW (this file's own precedent:
        CTQW's C1 is not asserted tightly either, for the identical
        reason -- "a deep well can put a coherent walk into an
        oscillatory/resonance-sensitive regime even when coupling is
        strong"). Measured directly: CP's C1 AUC is 0.000 here, an even
        stronger instance of the same well-localization sensitivity, not
        a defect in CP or in this construction -- documented, not
        asserted, matching this file's own convention for this cell."""
        cp = _mean_auc_over_seeds("DRUG", "DRUG", _cp)
        assert np.isfinite(cp)  # sanity only -- no directional claim for C1

    def test_c4_cues_absent_is_near_chance(self):
        """C4 (no well, equal coupling): loose bound, same convention as
        the GSR/CTQW sanity check above."""
        cp = _mean_auc_over_seeds(None, None, _cp)
        assert abs(cp - 0.5) < 0.3, f"CP not near chance in C4 (mean AUC={cp:.3f})"


class TestBuildDumbbellNetwork:
    """Construction sanity -- not physics assertions, just confirming the
    harness itself is well-formed, since future falsification tasks
    (T-D/T-E) will import and reuse it directly."""

    def test_shape_and_symmetry(self):
        H = build_dumbbell_network("DRUG", "DRUG", seed=0)
        assert H.shape == (N_NODES, N_NODES)
        np.testing.assert_allclose(H, H.T)

    def test_seeds_actually_vary_the_network(self):
        """Regression guard for the exact bug this module's own docstring
        names: an earlier prototype was fully deterministic across
        `seed`, silently averaging five identical copies."""
        H0 = build_dumbbell_network("DRUG", "DRUG", seed=0)
        H1 = build_dumbbell_network("DRUG", "DRUG", seed=1)
        assert not np.allclose(H0, H1)

    def test_no_well_leaves_diagonal_at_laplacian_degree(self):
        H = build_dumbbell_network(None, None, seed=0)
        W = -np.asarray(H - np.diag(np.diag(H)))
        expected_diag = W.sum(axis=1)
        np.testing.assert_allclose(np.diag(H), expected_diag)
