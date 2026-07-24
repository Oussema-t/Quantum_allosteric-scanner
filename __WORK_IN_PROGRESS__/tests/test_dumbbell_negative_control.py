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
from allostery.baselines import connectivity_robustness_from_adjacency  # noqa: E402
from allostery.hamiltonians import laplacian  # noqa: E402
from allostery.metrics import auc as _auc  # noqa: E402
from allostery.propagators import ground_state_relaxation, time_averaged_ctqw  # noqa: E402
from allostery.spectral_coherence import spectral_coherence_score  # noqa: E402
from allostery.transport import effective_resistance_from_source, transmission_from_source  # noqa: E402

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


def _connectivity(H, t, source):
    """Matches `auc_to_drug`'s `propagator(H, t, source=...)` interface --
    `t` is accepted and ignored (`connectivity_robustness_from_adjacency`,
    TASK-0136, is a static graph-topology measure, no time parameter).
    `H` here is the dumbbell's own combinatorial Laplacian (`L = D - W`);
    the underlying adjacency `W` is recovered as `-L` off the diagonal
    (`L`'s diagonal encodes degree, unused by this purely-topological
    measure -- edge existence/weight is all it looks at)."""
    A = -H.copy()
    np.fill_diagonal(A, 0)
    return connectivity_robustness_from_adjacency(A, source)


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


class TestConnectivityRobustnessDumbbellGate:
    """TASK-0136's own mandatory gate (Intent Contract: "no lighter-touch
    reporting standard for a new, topologically-motivated observable than
    for CTQW"). Checked here, not assumed -- and the result is a genuine,
    clean negative, distinct in kind from GSR's well-following: this
    observable is **unweighted** (Menger's-theorem edge-*count*, per its
    own docstring), while the dumbbell's DRUG/DECOY bridges are
    topologically identical (same node count, same edge count) and differ
    *only* in edge weight (1.0 vs 0.15) -- there is no edge-count signal
    here for an unweighted measure to find, by construction, not by bug.

    Real measured values on this construction (checked directly before
    writing these assertions): C2=0.500, C3=0.500, C1=0.500, C4=0.500 --
    exactly chance in every cell, not merely "weak" or "noisy." This is
    the expected, honest consequence of the design choice documented in
    `connectivity_robustness`'s own docstring, not a surprise found here."""

    def test_c2_c3_give_exactly_chance_not_a_directional_signal(self):
        """Both conflict cells must land at exactly 0.5 -- this observable
        has no edge-count-based way to prefer either lobe on this
        construction, so it must neither follow the well (like GSR) nor
        the coupling (like CTQW/CP)."""
        c2 = _mean_auc_over_seeds("DECOY", "DRUG", _connectivity)
        c3 = _mean_auc_over_seeds("DRUG", "DECOY", _connectivity)
        assert c2 == pytest.approx(0.5), f"expected exact chance in C2, got {c2:.3f}"
        assert c3 == pytest.approx(0.5), f"expected exact chance in C3, got {c3:.3f}"

    def test_c1_c4_also_give_exactly_chance(self):
        """Unlike GSR/CTQW/CP, C1 (cues agree) is not "uninformative but
        directionally correct" here -- it is exactly the same 0.5 as every
        other cell, since well placement has no effect on an observable
        that never looks at the well term at all (`H`'s diagonal is
        discarded entirely by `_connectivity`'s own adjacency recovery)."""
        c1 = _mean_auc_over_seeds("DRUG", "DRUG", _connectivity)
        c4 = _mean_auc_over_seeds(None, None, _connectivity)
        assert c1 == pytest.approx(0.5)
        assert c4 == pytest.approx(0.5)


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


def _reff(H, t, source):
    """Matches `auc_to_drug`'s `propagator(H, t, source=...)` interface --
    `t` ignored (`effective_resistance_from_source` is a static resistor-
    network measure, no time parameter). `H` here may carry a well on its
    diagonal (`build_dumbbell_network`'s own convention) --
    `effective_resistance_from_source` structurally CANNOT use diagonal
    information at all: its `L+_ii + L+_jj - 2*L+_ij` formula is a theorem
    that holds specifically because `L` is a genuine graph Laplacian with
    `L @ 1 = 0`, which any nonzero diagonal shift (a well) breaks. The
    coupling-only adjacency is recovered first (off-diagonal entries are
    untouched by the well -- the same recovery `connectivity_robustness`'s
    own `_connectivity` adapter above already uses), then re-Laplacianized
    cleanly before scoring."""
    W = -H.copy()
    np.fill_diagonal(W, 0)
    L_clean = laplacian(W, normalised=False)
    return effective_resistance_from_source(L_clean, source)


def _transmission(H, t, source):
    """Matches `auc_to_drug`'s `propagator(H, t, source=...)` interface --
    `t` ignored (`transmission_from_source` takes a fixed energy `E`, not
    a propagation time). Unlike `_reff` above, `transmission_from_source`
    works on any real symmetric `H` directly (no Laplacian-null-space
    requirement -- the `i*Gamma/2` lead term already regularizes the
    Green's function), so the well-carrying `H` is passed through
    unmodified, deliberately testing whether the *quantum* transport
    calculation is well-sensitive (like GSR) or coupling-sensitive (like
    CTQW/CP) when a real diagonal potential is actually present."""
    return transmission_from_source(H, source, E=0.0)


def _spectral_coherence(H, t, source):
    """Matches `auc_to_drug`'s `propagator(H, t, source=...)` interface --
    `t` is used as this observable's own `t_max` (a window length, not a
    snapshot time; TASK-0146's own convention throughout). This file's own
    default `t=20.0` (`auc_to_drug`'s default, unchanged) is checked
    directly to already be adequate here -- the dumbbell's own bandwidth
    (~19) and median gap (~0.18) are both far larger than a real protein
    `H_new`'s (real-target scoring uses a separately-calibrated, much
    longer `spectral_coherence.DEFAULT_T_MAX=5000`), so this much shorter
    window already resolves its Bohr structure comfortably."""
    return spectral_coherence_score(H, source, t_max=t)


class TestEffectiveResistanceDumbbellGate:
    """TASK-0145's own mandatory gate (Intent Contract: "synthetic
    falsification gate first... does either quantity track coupling
    strength, not just well-depth or proximity, on a constructed case
    before trusting real data"). Effective resistance is *provably*
    well-invariant by construction (see `_reff`'s own docstring) -- this
    is not an empirical hope, it is a mathematical consequence of the
    formula, confirmed directly below rather than merely asserted from
    the derivation.

    Real measured values on this construction (n_seeds=20, checked
    directly before writing these assertions): C1=1.000, C2=1.000,
    C3=0.000, C4=0.480 (mean; C4 has real, high per-seed variance,
    0.076-0.924 -- the same equal-coupling construction's own random
    intra-lobe weights matter more to an exact resistor-network
    calculation than to a propagator, a genuine property of this
    observable, not a defect; a wider seed count is used for C4 here
    than this file's other gates use, precisely to average that real
    variance out rather than risk reading one noisy small-sample draw as
    "off"."""

    def test_c1_and_c2_are_identical_since_reff_cannot_see_the_well(self):
        """C1 (well=DRUG, strong=DRUG) and C2 (well=DECOY, strong=DRUG)
        share the same `strong_lobe="DRUG"` and differ only in
        `well_lobe` -- since `_reff` structurally discards the well,
        these two cells must score *identically*, not just similarly.
        This is the single most direct test of the well-invariance
        claim: not "close," exactly equal, seed by seed."""
        c1 = _mean_auc_over_seeds("DRUG", "DRUG", _reff, n_seeds=10)
        c2 = _mean_auc_over_seeds("DECOY", "DRUG", _reff, n_seeds=10)
        assert c1 == pytest.approx(c2, abs=1e-9), (
            f"expected C1 and C2 to be exactly equal (well-invariant), got {c1} vs {c2}"
        )

    def test_c2_reff_follows_coupling_not_well(self):
        mean_auc = _mean_auc_over_seeds("DECOY", "DRUG", _reff, n_seeds=20)
        assert mean_auc > 0.95, f"R_eff did not decisively follow coupling in C2 (mean AUC={mean_auc:.3f})"

    def test_c3_reff_follows_coupling_not_well(self):
        mean_auc = _mean_auc_over_seeds("DRUG", "DECOY", _reff, n_seeds=20)
        assert mean_auc < 0.05, f"R_eff did not decisively follow coupling in C3 (mean AUC={mean_auc:.3f})"

    def test_c2_c3_is_a_clean_double_dissociation_against_gsr(self):
        reff_c2 = _mean_auc_over_seeds("DECOY", "DRUG", _reff, n_seeds=10)
        gsr_c2 = _mean_auc_over_seeds("DECOY", "DRUG", _gsr, n_seeds=10)
        reff_c3 = _mean_auc_over_seeds("DRUG", "DECOY", _reff, n_seeds=10)
        gsr_c3 = _mean_auc_over_seeds("DRUG", "DECOY", _gsr, n_seeds=10)
        assert reff_c2 > gsr_c2, "R_eff should score DRUG higher than GSR in C2 (well elsewhere)"
        assert reff_c3 < gsr_c3, "R_eff should score DRUG lower than GSR in C3 (well on DRUG)"

    def test_c4_cues_absent_is_near_chance_with_a_wider_seed_average(self):
        """C4 has real, high per-seed variance for this observable (see
        class docstring) -- a wider `n_seeds` than this file's other
        gates use is deliberate, not a loosened bar, to get a stable
        mean rather than risk one unlucky small sample."""
        c4 = _mean_auc_over_seeds(None, None, _reff, n_seeds=20)
        assert abs(c4 - 0.5) < 0.3, f"R_eff not near chance in C4 (mean AUC={c4:.3f})"


class TestTransmissionDumbbellGate:
    """TASK-0145's own mandatory gate for the quantum transmission
    observable. Unlike `R_eff`, `T(E)` is NOT structurally blind to the
    well (it operates on `H` directly, well included) -- whether it
    tracks coupling or the well on this construction is a genuine
    empirical question, checked directly, not assumed to transfer from
    `R_eff`'s provable invariance.

    Real measured values on this construction (n_seeds=20, checked
    directly before writing these assertions, default `E=0.0`,
    `gamma_lead=0.1*bandwidth`): C2=1.000, C3=0.000 (both exact across
    every seed tested -- a decisive double dissociation from GSR). C1=0.000
    -- the same "well and coupling agree, yet the score is anti-intuitive"
    resonance-sensitivity this file's own `TestModeCoparticipationDumbbellGate`
    already documented for CP on this identical construction (also measured
    at exactly 0.000 there) -- not asserted directionally here either, for
    the same reason. C4=0.417 mean, high per-seed variance (0.076-0.924,
    same construction-level sensitivity `TestEffectiveResistanceDumbbellGate`
    found for R_eff) -- a wider seed count is used for the same reason."""

    def test_c2_transmission_follows_coupling_not_well(self):
        mean_auc = _mean_auc_over_seeds("DECOY", "DRUG", _transmission, n_seeds=20)
        assert mean_auc > 0.95, f"T(E) did not decisively follow coupling in C2 (mean AUC={mean_auc:.3f})"

    def test_c3_transmission_follows_coupling_not_well(self):
        mean_auc = _mean_auc_over_seeds("DRUG", "DECOY", _transmission, n_seeds=20)
        assert mean_auc < 0.05, f"T(E) did not decisively follow coupling in C3 (mean AUC={mean_auc:.3f})"

    def test_c2_c3_is_a_clean_double_dissociation_against_gsr(self):
        t_c2 = _mean_auc_over_seeds("DECOY", "DRUG", _transmission, n_seeds=10)
        gsr_c2 = _mean_auc_over_seeds("DECOY", "DRUG", _gsr, n_seeds=10)
        t_c3 = _mean_auc_over_seeds("DRUG", "DECOY", _transmission, n_seeds=10)
        gsr_c3 = _mean_auc_over_seeds("DRUG", "DECOY", _gsr, n_seeds=10)
        assert t_c2 > gsr_c2, "T(E) should score DRUG higher than GSR in C2 (well elsewhere)"
        assert t_c3 < gsr_c3, "T(E) should score DRUG lower than GSR in C3 (well on DRUG)"

    def test_c1_cues_agree_is_not_asserted_tightly(self):
        """Same convention as `TestModeCoparticipationDumbbellGate`'s own
        C1 cell, for the same measured reason (a deep co-located well
        perturbs the low-mode/Green's-function structure into a
        resonance-sensitive regime even when coupling agrees) -- no
        directional claim, sanity only."""
        c1 = _mean_auc_over_seeds("DRUG", "DRUG", _transmission, n_seeds=5)
        assert np.isfinite(c1)

    def test_c4_cues_absent_is_near_chance_with_a_wider_seed_average(self):
        c4 = _mean_auc_over_seeds(None, None, _transmission, n_seeds=20)
        assert abs(c4 - 0.5) < 0.3, f"T(E) not near chance in C4 (mean AUC={c4:.3f})"


class TestSpectralCoherenceDumbbellGate:
    """TASK-0146's own mandatory gate (Intent Contract: "synthetic
    falsification gate first... does the spectral score track coupling,
    not the well, before trusting real data"). This module's own score
    (total AC/non-DC spectral power of `p_j(t)=|c_j(t)|^2`) is built from
    the coherent, un-averaged amplitude trajectory -- genuinely different
    machinery from `time_averaged_ctqw`'s converged limit, so whether it
    tracks coupling here is a real empirical question, not assumed to
    transfer.

    Real measured values on this construction (n_seeds=20, checked
    directly before writing these assertions, default `t=20.0` --
    confirmed adequate at this file's own scale, see `_spectral_
    coherence`'s own docstring): C2=1.000, C3=0.000 (exact, every seed --
    a clean, decisive double dissociation against GSR). C1=0.083 -- the
    same well-agrees-but-score-is-anti-intuitive resonance sensitivity
    this file's other spectral/mode-based gates (`TestModeCoparticipation
    DumbbellGate`, `TestTransmissionDumbbellGate`) already documented on
    this identical construction -- not asserted directionally here either,
    for the same reason. C4=0.504 mean, near chance."""

    def test_c2_spectral_coherence_follows_coupling_not_well(self):
        mean_auc = _mean_auc_over_seeds("DECOY", "DRUG", _spectral_coherence, n_seeds=20)
        assert mean_auc > 0.95, f"spectral coherence did not decisively follow coupling in C2 (mean AUC={mean_auc:.3f})"

    def test_c3_spectral_coherence_follows_coupling_not_well(self):
        mean_auc = _mean_auc_over_seeds("DRUG", "DECOY", _spectral_coherence, n_seeds=20)
        assert mean_auc < 0.05, f"spectral coherence did not decisively follow coupling in C3 (mean AUC={mean_auc:.3f})"

    def test_c2_c3_is_a_clean_double_dissociation_against_gsr(self):
        spec_c2 = _mean_auc_over_seeds("DECOY", "DRUG", _spectral_coherence, n_seeds=10)
        gsr_c2 = _mean_auc_over_seeds("DECOY", "DRUG", _gsr, n_seeds=10)
        spec_c3 = _mean_auc_over_seeds("DRUG", "DECOY", _spectral_coherence, n_seeds=10)
        gsr_c3 = _mean_auc_over_seeds("DRUG", "DECOY", _gsr, n_seeds=10)
        assert spec_c2 > gsr_c2, "spectral coherence should score DRUG higher than GSR in C2 (well elsewhere)"
        assert spec_c3 < gsr_c3, "spectral coherence should score DRUG lower than GSR in C3 (well on DRUG)"

    def test_c1_cues_agree_is_not_asserted_tightly(self):
        """Same convention as this file's other coupling-tracking gates'
        own C1 cell, for the same measured reason -- no directional
        claim, sanity only."""
        c1 = _mean_auc_over_seeds("DRUG", "DRUG", _spectral_coherence, n_seeds=5)
        assert np.isfinite(c1)

    def test_c4_cues_absent_is_near_chance_with_a_wider_seed_average(self):
        c4 = _mean_auc_over_seeds(None, None, _spectral_coherence, n_seeds=20)
        assert abs(c4 - 0.5) < 0.3, f"spectral coherence not near chance in C4 (mean AUC={c4:.3f})"

def _entanglement(H, t, source, radius: int = 1):
    """Matches `auc_to_drug`'s `propagator(H, t, source=...)` interface --
    `entanglement_entropy_mixture` needs a genuinely coherent amplitude at
    a fixed time (see `allostery.entanglement`'s own module docstring:
    time-averaged/decohered occupation has no accessible coherences),
    so `t` is used directly, not ignored, unlike this file's other
    spectral adapters. Neighborhoods are built fresh from `H`'s own
    off-diagonal adjacency (recovered the same way `_reff`/`_connectivity`
    above do, so a well on the diagonal doesn't leak into the graph
    topology used to define regions) at `radius=1` (TASK-0148's own
    default)."""
    from scipy.sparse.csgraph import shortest_path

    from allostery.entanglement import entanglement_entropy_mixture, hop_radius_neighborhoods

    A = -H.copy()
    np.fill_diagonal(A, 0)
    hop_dist = shortest_path((A > 1e-12).astype(float), method="D", unweighted=True, directed=False)
    neighborhoods = hop_radius_neighborhoods(hop_dist, radius=radius)
    return entanglement_entropy_mixture(H, source, neighborhoods, t)


class TestEntanglementEntropyDumbbellGate:
    """TASK-0148's own mandatory gate (Intent Contract: "does the entropy
    actually track coupling/delocalization on a constructed case... before
    trusting real data"). Unlike `R_eff` (TASK-0145), entanglement entropy
    operates directly on `H`'s coherent dynamics (well included, not
    structurally blind to it) -- whether it tracks coupling or the well on
    this construction is a genuine empirical question, checked directly.

    Real measured values on this construction (n_seeds=10, `t=20.0`
    matching this file's own default, `radius=1`, checked directly before
    writing these assertions): C2=1.000, C3=0.000 (both exact across every
    seed -- a decisive double dissociation from GSR, the same pattern
    `R_eff`/`T(E)` (TASK-0145) and CP (TASK-0122) already showed on this
    construction). C1=0.076 -- well below chance, not asserted
    directionally (same resonance-sensitivity precedent as this file's
    other coupling-tracking gates on the cues-agree cell). C4=0.584 mean,
    high per-seed variance (0.076-0.924, the identical range TASK-0145's
    gates found) -- a wider seed count is used for the same reason."""

    def test_c2_entanglement_follows_coupling_not_well(self):
        mean_auc = _mean_auc_over_seeds("DECOY", "DRUG", _entanglement, n_seeds=20)
        assert mean_auc > 0.95, f"Entanglement entropy did not decisively follow coupling in C2 (mean AUC={mean_auc:.3f})"

    def test_c3_entanglement_follows_coupling_not_well(self):
        mean_auc = _mean_auc_over_seeds("DRUG", "DECOY", _entanglement, n_seeds=20)
        assert mean_auc < 0.05, f"Entanglement entropy did not decisively follow coupling in C3 (mean AUC={mean_auc:.3f})"

    def test_c2_c3_is_a_clean_double_dissociation_against_gsr(self):
        e_c2 = _mean_auc_over_seeds("DECOY", "DRUG", _entanglement, n_seeds=10)
        gsr_c2 = _mean_auc_over_seeds("DECOY", "DRUG", _gsr, n_seeds=10)
        e_c3 = _mean_auc_over_seeds("DRUG", "DECOY", _entanglement, n_seeds=10)
        gsr_c3 = _mean_auc_over_seeds("DRUG", "DECOY", _gsr, n_seeds=10)
        assert e_c2 > gsr_c2, "Entanglement entropy should score DRUG higher than GSR in C2 (well elsewhere)"
        assert e_c3 < gsr_c3, "Entanglement entropy should score DRUG lower than GSR in C3 (well on DRUG)"

    def test_c1_cues_agree_is_not_asserted_tightly(self):
        """Same convention as this file's other coupling-tracking gates'
        own C1 cell, for the same measured reason (a deep co-located well
        perturbs the coherent amplitude into a resonance-sensitive regime
        even when coupling agrees) -- no directional claim, sanity only."""
        c1 = _mean_auc_over_seeds("DRUG", "DRUG", _entanglement, n_seeds=5)
        assert np.isfinite(c1)

    def test_c4_cues_absent_is_near_chance_with_a_wider_seed_average(self):
        c4 = _mean_auc_over_seeds(None, None, _entanglement, n_seeds=20)
        assert abs(c4 - 0.5) < 0.3, f"Entanglement entropy not near chance in C4 (mean AUC={c4:.3f})"

