"""TASK-0015 coverage -- holo-direction module Steps 0-2.

Synthetic coordinates only, matching test_superpose.py's own convention
(same helix fixture shape) -- no network fetch. Real-target Step 2 runs
live in scripts/holo_direction_step2_gate.py, not here.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.holo_direction import (  # noqa: E402
    PERTURBATION_PROTOCOL,
    build_deformation_family,
    go_no_go_gate,
)


def _helix_coords(n: int, radius: float = 2.3, rise: float = 1.5, turn_deg: float = 100.0) -> np.ndarray:
    theta = np.arange(n) * (turn_deg * np.pi / 180.0)
    return np.column_stack([
        radius * np.cos(theta),
        radius * np.sin(theta),
        rise * np.arange(n, dtype=float),
    ])


N = 16
COORDS = _helix_coords(N)
B_MEAN = 20.0


class _Struct:
    def __init__(self, coords, resnums=None, chain_ids=None):
        self.coords = coords
        self.resnums = np.asarray(resnums if resnums is not None else np.arange(len(coords)))
        self.chain_ids = list(chain_ids) if chain_ids is not None else ["A"] * len(coords)


# ---------------------------------------------------------------------------
# Step 0 -- protocol is a frozen constant, not a knob a caller can silently
# drift without noticing (a plain equality/shape check, cheap but real: if
# someone edits this dict's shape without updating callers, this fails loudly)
# ---------------------------------------------------------------------------

def test_protocol_is_frozen_and_well_formed():
    assert PERTURBATION_PROTOCOL["n_modes"] == 10
    assert PERTURBATION_PROTOCOL["amplitude_scales"] == (0.5, 1.0, 2.0)
    c = PERTURBATION_PROTOCOL["integrity_constraints"]
    assert c["max_ca_spacing_deviation"] > 0
    assert c["min_ca_ca_nonbonded_distance"] > 0
    assert c["max_global_rmsd_from_apo"] > 0


# ---------------------------------------------------------------------------
# Step 1 -- deformation family
# ---------------------------------------------------------------------------

def test_deformation_family_candidate_count_and_shapes():
    family = build_deformation_family(COORDS, B_MEAN)
    n_modes = PERTURBATION_PROTOCOL["n_modes"]
    n_scales = len(PERTURBATION_PROTOCOL["amplitude_scales"])
    total = n_modes * n_scales * 2  # +/- sign
    assert len(family["admissible"]) + len(family["rejected"]) == total
    for entry in family["admissible"]:
        assert entry["coords"].shape == COORDS.shape
        assert np.isfinite(entry["rmsd"])
        assert np.isfinite(entry["elastic_energy"])


def test_amplitude_unit_gives_exactly_half_unit_energy_at_scale_one():
    """a_k^(1) = sqrt(1/(kappa*lambda_k)) is defined so E_k = 0.5 exactly
    at scale=1.0 -- a direct arithmetic identity, not an empirical claim;
    a future formula regression here should fail loudly."""
    family = build_deformation_family(COORDS, B_MEAN)
    scale_one = [e for e in family["admissible"] + family["rejected"] if e["scale"] == 1.0]
    assert scale_one, "expected at least one scale=1.0 candidate (admissible or rejected)"
    for e in scale_one:
        assert e["elastic_energy"] == pytest.approx(0.5, rel=1e-9)


def test_integrity_rejects_oversized_amplitude():
    """A protocol with a huge amplitude scale must produce real
    integrity-constraint rejections (RMSD/clash/spacing) -- if nothing is
    ever rejected, the integrity check itself is dead code, not just
    generous."""
    big_protocol = dict(PERTURBATION_PROTOCOL)
    big_protocol["amplitude_scales"] = (50.0,)
    family = build_deformation_family(COORDS, B_MEAN, protocol=big_protocol)
    assert len(family["rejected"]) > 0
    reasons = {e["reject_reason"] for e in family["rejected"]}
    assert reasons  # at least one real reason string, not all silently admissible


def test_tiny_amplitude_family_is_fully_admissible():
    """Sanity check in the other direction: a vanishingly small amplitude
    scale should never violate any integrity constraint -- if it does,
    the constraint thresholds themselves are miscalibrated against the
    coordinate scale, not a real structural finding."""
    tiny_protocol = dict(PERTURBATION_PROTOCOL)
    tiny_protocol["amplitude_scales"] = (1e-6,)
    family = build_deformation_family(COORDS, B_MEAN, protocol=tiny_protocol)
    assert len(family["rejected"]) == 0
    assert len(family["admissible"]) == PERTURBATION_PROTOCOL["n_modes"] * 2


# ---------------------------------------------------------------------------
# Step 2 -- go/no-go gate. Edge-detection logic is tested in isolation with
# a hand-built `family` dict (deterministic, known answer) rather than via
# real ANM output, so the assertion is about this module's own logic, not
# about whether a helix happens to produce a particular mode shape.
# ---------------------------------------------------------------------------

def _minimal_family(coords_admissible_list, eigvecs_shape):
    return dict(
        admissible=[dict(mode=i, sign=1.0, scale=1.0, coords=c, rmsd=0.0, elastic_energy=0.0)
                    for i, c in enumerate(coords_admissible_list)],
        rejected=[],
        eigvecs=np.zeros(eigvecs_shape),
        eigvals=np.ones(eigvecs_shape[1]),
        kappa=1.0,
    )


def test_go_no_go_gate_detects_new_active_site_pocket_edge():
    """Two residues (indices 0 and N-1) start far apart (no apo contact at
    cutoff=5.0); one admissible candidate moves them within contact
    range -- the gate must report right_edges_found=True and name that
    exact pair."""
    coords = COORDS.copy()
    coords[-1] = coords[0] + np.array([20.0, 0.0, 0.0])  # push residue N-1 far from residue 0
    apo = _Struct(coords)
    holo = _Struct(coords)  # CO curve irrelevant to this test's own assertion

    active_site_mask = np.zeros(N, dtype=bool)
    active_site_mask[0] = True
    pocket_mask = np.zeros(N, dtype=bool)
    pocket_mask[-1] = True

    coords_deformed = coords.copy()
    coords_deformed[-1] = coords[0] + np.array([2.0, 0.0, 0.0])  # now well within cutoff=5.0
    family = _minimal_family([coords_deformed], eigvecs_shape=(3 * N, 1))

    result = go_no_go_gate(apo, holo, {}, active_site_mask, pocket_mask, family, cutoff=5.0)
    assert result["right_edges_found"] is True
    assert (0, N - 1) in result["new_edge_candidates"][0]["new_edges"]


def test_go_no_go_gate_no_new_edges_when_apo_already_in_contact():
    """Negative control: if the active site and pocket are already in
    apo contact, no candidate should ever count as creating a *new*
    edge, even if the same pair remains in contact after deformation."""
    coords = COORDS.copy()
    apo = _Struct(coords)
    holo = _Struct(coords)

    active_site_mask = np.zeros(N, dtype=bool)
    active_site_mask[0] = True
    pocket_mask = np.zeros(N, dtype=bool)
    pocket_mask[1] = True  # sequential neighbor -- always in contact at any reasonable cutoff

    family = _minimal_family([coords.copy()], eigvecs_shape=(3 * N, 1))
    result = go_no_go_gate(apo, holo, {}, active_site_mask, pocket_mask, family, cutoff=10.0)
    assert result["right_edges_found"] is False
    assert result["n_candidates_with_new_edges"] == 0


def test_go_no_go_gate_verdict_combines_both_components():
    """PARTIAL when the two components disagree -- never silently
    collapsed to GO or NO_GO in either direction."""
    coords = COORDS.copy()
    apo = _Struct(coords)
    holo = _Struct(coords)
    active_site_mask = np.zeros(N, dtype=bool)
    active_site_mask[0] = True
    pocket_mask = np.zeros(N, dtype=bool)
    pocket_mask[-1] = True

    coords[-1] = coords[0] + np.array([20.0, 0.0, 0.0])
    coords_deformed = coords.copy()
    coords_deformed[-1] = coords[0] + np.array([2.0, 0.0, 0.0])
    family = _minimal_family([coords_deformed], eigvecs_shape=(3 * N, 1))

    # co_final will be 0.0 here (holo == pre-shift coords, alignment trivial,
    # delta_r ~ 0) -- co_go False, right_edges_found True -> PARTIAL.
    result = go_no_go_gate(apo, holo, {}, active_site_mask, pocket_mask, family,
                            cutoff=5.0, co_threshold=0.5)
    assert result["verdict"] == "PARTIAL"
    assert result["right_edges_found"] is True
    assert result["co_go"] is False
