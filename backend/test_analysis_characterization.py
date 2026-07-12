"""TASK-0074: characterization tests for backend/analysis.py.

Golden-output tests pinning the *current* live public surface of
`gnm_context`, `site_potentials`, `quantum_seed_readiness`, and
`connectivity_change` on a fixed benchmark target (KRAS_G12C, apo 4OBE /
holo 6OIM, per `backend/systems.py::SYSTEMS`). This is characterization,
not validation -- it does not assert the physics is *correct*, only that
it doesn't silently change. Per EXECUTION_PLAN.md Phase 4's hard rule
("4.1 and 4.2 land BEFORE any Phase-2 code touches backend/"), this file
is the safety net TASK-0066's dedup refactor is checked against.

Values below were captured 2026-07-12 against live RCSB data (real
network fetch, not mocked) and cross-checked by an independent git-stash
pre/post diff of TASK-0066's own refactor (byte-identical) before being
pinned here -- not guessed, not copied from a docstring claim.
"""
import numpy as np
import pytest

from backend.analysis import (
    connectivity_change,
    gnm_context,
    quantum_seed_readiness,
    site_potentials,
)
from backend.data_layer import load_structure, res_indices
from backend.systems import SYSTEMS


def _load_kras_apo():
    sysinfo = SYSTEMS["KRAS_G12C"]
    try:
        apo = load_structure(sysinfo["apo"], sysinfo["chain"])
    except Exception as exc:
        pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")
    if apo is None:
        pytest.skip("real-structure fetch unavailable in this environment (load_structure returned None)")
    return apo, sysinfo


class TestGnmContextCharacterization:
    def test_kras_g12c_apo_pinned_values(self):
        apo, _sysinfo = _load_kras_apo()
        c = gnm_context(apo["coords"], apo["bfac"], cutoff=8.0)

        assert c["N"] == 169
        assert float(c["deg"].sum()) == 1618.0
        assert round(float(c["msf"].sum()), 6) == 29.80022
        assert round(float(c["clust"].sum()), 6) == 93.788795
        assert [round(float(x), 6) for x in c["eigs"][:3]] == [0.0, 0.442318, 0.493155]


class TestSitePotentialsCharacterization:
    def test_kras_g12c_apo_pinned_term_sums(self):
        apo, _sysinfo = _load_kras_apo()
        sp = site_potentials(apo["coords"], apo["bfac"], apo["resnums"], cutoff=8.0)

        assert set(sp) == {"cutoff", "l_eigs", "labels", "resnums", "terms"}
        assert sp["cutoff"] == 8.0
        assert len(sp["resnums"]) == 169
        term_sums = {k: round(float(sum(v)), 6) for k, v in sp["terms"].items()}
        assert term_sums == {
            "V_B": -0.001, "V_T": 0.0001, "V_R": 0.0004, "V_C": -0.0002, "V_M": 0.0001,
        }

    def test_kras_g12c_with_active_site_enrichment_pinned(self):
        apo, sysinfo = _load_kras_apo()
        site_idx = res_indices(apo, sysinfo["active_site"])
        sp = site_potentials(apo["coords"], apo["bfac"], apo["resnums"], cutoff=8.0, site_idx=site_idx)

        assert "enrichment" in sp and "enrichment_sig" in sp
        assert set(sp["enrichment"]) == {"V_B", "V_T", "V_R", "V_C", "V_M"}


class TestQuantumSeedReadinessCharacterization:
    def test_kras_g12c_apo_pinned_verdict(self):
        apo, sysinfo = _load_kras_apo()
        site_idx = res_indices(apo, sysinfo["active_site"])
        qsr = quantum_seed_readiness(apo["coords"], apo["bfac"], apo["resnums"], site_idx, cutoff=8.0)

        assert qsr["verdict"] == "PARTIAL"
        assert qsr["n_total"] == 22
        assert qsr["n_good"] == 8
        assert qsr["frac_good"] == 0.36
        assert round(qsr["distal_reach"], 3) == 0.429
        assert round(qsr["distal_enrich"], 3) == 0.941
        assert qsr["recommend_seed"] == [15, 17, 18, 29, 32, 116, 117, 118]

    def test_kras_g12c_per_residue_row_shape_and_first_row_pinned(self):
        apo, sysinfo = _load_kras_apo()
        site_idx = res_indices(apo, sysinfo["active_site"])
        qsr = quantum_seed_readiness(apo["coords"], apo["bfac"], apo["resnums"], site_idx, cutoff=8.0)

        assert len(qsr["per_residue"]) == 22
        first = qsr["per_residue"][0]
        assert first["resnum"] == 10
        assert first["degree"] == 13
        assert first["status"] == "weak"
        assert first["reasons"] == "weak dynamic coupling"

    def test_returns_none_for_empty_site_idx(self):
        apo, _sysinfo = _load_kras_apo()
        assert quantum_seed_readiness(apo["coords"], apo["bfac"], apo["resnums"], np.array([], dtype=int)) is None


class TestConnectivityChangeCharacterization:
    def test_kras_g12c_apo_holo_pinned_summary(self):
        _apo, sysinfo = _load_kras_apo()
        cc = connectivity_change(sysinfo["apo"], sysinfo["chain"], sysinfo["holo"], sysinfo["chain"], cutoff=8.0)

        assert cc["summary"] == {
            "n_shared": 166,
            "ddm_max": 8.84,
            "contacts_formed": 24,
            "contacts_broken": 26,
            "mean_abs_ddcc": 0.01,
            "most_reorganized": [63, 64, 60, 62, 68],
        }

    def test_kras_g12c_ddcc_sample_pinned(self):
        _apo, sysinfo = _load_kras_apo()
        cc = connectivity_change(sysinfo["apo"], sysinfo["chain"], sysinfo["holo"], sysinfo["chain"], cutoff=8.0)

        assert cc["ddcc"][0][:5] == pytest.approx([0.0, 0.029, 0.005, 0.002, -0.001], abs=1e-3)
        assert cc["cutoff"] == 8.0
        assert cc["downsampled"] is False
