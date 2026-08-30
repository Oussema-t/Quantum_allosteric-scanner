"""TASK-0074: characterization tests for backend/analysis.py.

Golden-output tests pinning the *current* live public surface of
`gnm_context`, `site_potentials`, `quantum_seed_readiness`, and
`connectivity_change` on a fixed benchmark target (KRAS_G12C, apo 4LDJ /
holo 6OIM, per `backend/systems.py::SYSTEMS`). This is characterization,
not validation -- it does not assert the physics is *correct*, only that
it doesn't silently change. Per EXECUTION_PLAN.md Phase 4's hard rule
("4.1 and 4.2 land BEFORE any Phase-2 code touches backend/"), this file
is the safety net TASK-0066's dedup refactor is checked against.

Values below were captured 2026-07-12 against live RCSB data (real
network fetch, not mocked) and cross-checked by an independent git-stash
pre/post diff of TASK-0066's own refactor (byte-identical) before being
pinned here -- not guessed, not copied from a docstring claim.

**PIN PROVENANCE (keep current -- the next structure change must update
this line and re-run this file's own regeneration, TASK-0296's own
Constraint: from the live code path, never hand-edited):**
KRAS_G12C goldens regenerated **2026-08-30, TASK-0296**, against
`apo=4LDJ` -- the structure [[TASK-0270]] (2026-08-26) adopted, replacing
`4OBE` (confirmed wild-type, not the G12C mutant). The original
2026-07-12 capture above predates that fix; these 6 tests went stale for
6 days (TASK-0270 -> TASK-0296) before being caught by an unrelated
task's own `pytest backend/` run ([[TASK-0290]]) and promoted into its
own fix here. Holo-side-only numbers (`active_shift["holo"]`,
`reach_shift` is not holo-only -- see below) are confirmed **unchanged**
from the original 2026-07-12 capture, a real cross-check that only the
apo-touching computations moved, not everything: `holo=6OIM` never
changed.
"""
import numpy as np
import pytest

from backend.analysis import (
    connectivity_change,
    gnm_context,
    quantum_seed_readiness,
    seed_readiness_shift,
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

        # TASK-0296, regenerated against 4LDJ (170 residues, was 169 on 4OBE)
        assert c["N"] == 170
        assert float(c["deg"].sum()) == 1624.0
        assert round(float(c["msf"].sum()), 6) == 30.678006
        assert round(float(c["clust"].sum()), 6) == 93.998033
        assert [round(float(x), 6) for x in c["eigs"][:3]] == [0.0, 0.402556, 0.478177]


class TestSitePotentialsCharacterization:
    def test_kras_g12c_apo_pinned_term_sums(self):
        apo, _sysinfo = _load_kras_apo()
        sp = site_potentials(apo["coords"], apo["bfac"], apo["resnums"], cutoff=8.0)

        assert set(sp) == {"cutoff", "l_eigs", "labels", "resnums", "terms"}
        assert sp["cutoff"] == 8.0
        # TASK-0296, regenerated against 4LDJ (170 residues, was 169 on 4OBE)
        assert len(sp["resnums"]) == 170
        term_sums = {k: round(float(sum(v)), 6) for k, v in sp["terms"].items()}
        assert term_sums == {
            "V_B": -0.0, "V_T": -0.0011, "V_R": 0.0005, "V_C": 0.0004, "V_M": 0.0006,
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

        # TASK-0296, regenerated against 4LDJ -- the verdict itself moved,
        # PARTIAL (4OBE) -> RISKY (4LDJ), not just the numbers underneath
        # it (n_good 8->7, frac_good 0.36->0.32). Reported as a finding,
        # not silently absorbed into the fixture per this task's own
        # Constraint: consistent with the same G12C-vs-wild-type direction
        # every other re-scored KRAS_G12C number in this register has
        # moved since TASK-0270 (e.g. TASK-0283's NO_FAILURE_DETECTED ->
        # NO_SIGNAL_IN_APO), not an isolated anomaly in this one function.
        assert qsr["verdict"] == "RISKY"
        assert qsr["n_total"] == 22
        assert qsr["n_good"] == 7
        assert qsr["frac_good"] == 0.32
        assert round(qsr["distal_reach"], 3) == 0.429
        assert round(qsr["distal_enrich"], 3) == 0.934
        assert qsr["recommend_seed"] == [14, 15, 18, 29, 116, 117, 118]

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


def _build_dumbbell_seed_case(n_lobe=4, n_distal_lobe=4, lobe_jitter=1.96,
                               distal_jitter=2.2, gap=14.6, bridge_spacing=3.16,
                               seed=7149):
    """TASK-0220: synthetic positive control -- two tight residue clusters
    ("lobes") joined by a short percolating chain of relay points, the
    same dumbbell shape `__WORK_IN_PROGRESS__/tests/test_dumbbell_negative_
    control.py` (TASK-0103) uses to force genuine seed<->distal coupling in
    a CTQW-style operator, adapted here to real 3D coordinates so it drives
    the actual `_ctqw_build_H`/`_average_mixing_matrix` code path rather
    than a hand-substituted Hamiltonian. The seed lobe (`site_idx`) sits at
    the origin; the second lobe sits `gap` Å away (comfortably past
    `distal_ang=12`); relay points every `bridge_spacing` Å connect them
    (each hop within `R_c=8`) since a single direct edge cannot span both
    "distal" and "in range" simultaneously with the shipped 8/12 pair.
    Deterministic (fixed seed) -- found by a ~2500-trial random search over
    lobe size/jitter/gap/bridge spacing for the combination that clears
    the SAFE bar with the widest margin on both axes jointly, not
    hand-tuned to a specific target."""
    rng = np.random.default_rng(seed)
    seed_lobe = rng.normal(0, lobe_jitter, size=(n_lobe, 3))
    distal_lobe = rng.normal(0, distal_jitter, size=(n_distal_lobe, 3)) + np.array([gap, 0, 0])
    n_bridge = max(1, int(round(gap / bridge_spacing)) - 1)
    bridge = np.array([[x, 0, 0] for x in np.linspace(bridge_spacing, gap - bridge_spacing, n_bridge)])
    coords = np.vstack([seed_lobe, bridge, distal_lobe])
    site_idx = np.arange(n_lobe)
    return coords, site_idx


class TestQuantumSeedReadinessSafeReachability:
    """TASK-0220: is `quantum_seed_readiness`'s SAFE verdict reachable at
    all, or dead code? All 6 currently-loadable `systems.py` targets land
    PARTIAL/RISKY (see this task's own Done section for the full table) --
    `distal_enrich` never even reaches the 1.0 uniform-baseline mark on
    real data, let alone the 1.2 SAFE bar. This synthetic dumbbell case is
    the "hand-built ... seed known to genuinely concentrate distally" this
    task's own Planned Validation calls for: it reaches SAFE, proving the
    verdict is reachable in principle under the shipped thresholds and
    formula -- not a dead branch -- even though no real benchmark target
    tested so far comes close. A future accidental change to the SAFE
    thresholds or the `distal_enrich`/`frac` formulas that makes this case
    stop landing SAFE is exactly the silent regression this test exists to
    catch."""

    def test_dumbbell_positive_control_reaches_safe(self):
        coords, site_idx = _build_dumbbell_seed_case()
        N = len(coords)
        qsr = quantum_seed_readiness(coords, np.zeros(N), np.arange(N), site_idx,
                                      cutoff=8.0, R_c=8.0, r0=7.0, distal_ang=12.0)

        assert qsr["verdict"] == "SAFE"
        assert qsr["n_total"] == 4
        assert qsr["n_good"] == 3
        assert qsr["frac_good"] == 0.75
        assert round(qsr["distal_reach"], 3) == 0.313
        assert round(qsr["distal_enrich"], 3) == 1.25


class TestSeedReadinessShiftCharacterization:
    """TASK-0035: pins `seed_readiness_shift`'s own bootstrap-derived
    numbers (`_bootstrap_floor`/`_raw_shift`, not covered by any existing
    characterization test before this task) -- captured against live
    RCSB data *before* `_bootstrap_floor`'s redundant-`_abs_coupling`
    perf fix landed, and confirmed bit-identical against 3 independent
    dict equality checks (this test's own assertions) *after* it, not
    just re-captured and trusted. Same rng seed (0), same
    `rng.choice(N, n_seed, replace=False)` call sequence -- the fix only
    removed redundant recomputation of whole-structure arrays that don't
    depend on which residues got sampled."""

    def test_kras_g12c_apo_holo_pinned_shift(self):
        apo, sysinfo = _load_kras_apo()
        r = seed_readiness_shift(
            sysinfo["apo"], sysinfo["chain"], sysinfo["holo"], sysinfo["chain"],
            site_resnums=sysinfo["active_site"], drug_resnums=sysinfo["pocket_full"][4.5], cutoff=8.0,
        )

        # TASK-0296, regenerated against 4LDJ. `holo` is unchanged from the
        # original 2026-07-12 (4OBE) capture -- confirmed, not assumed: a
        # real cross-check that only the apo-touching computations moved
        # (holo=6OIM never changed), not a wholesale re-capture.
        assert r["mechanism"] == "AMBIGUOUS"
        assert r["topology"] == "orthosteric"
        assert r["n_pocket"] == 21
        assert r["drug_active_sep"] == 0.0
        assert r["reach_shift"] == 0.009
        assert r["active_shift"]["apo"] == {"coupling": 11.563, "msf": 0.17, "slow": 0.014}
        assert r["active_shift"]["holo"] == {"coupling": 11.656, "msf": 0.172, "slow": 0.01}
        assert r["active_shift"]["delta"] == {"coupling": 0.093, "msf": 0.002, "slow": -0.003}
        assert r["active_shift"]["thr"] == {"coupling": 1.521, "msf": 0.047, "slow": 0.011}
        assert r["active_shift"]["sig"] == {"coupling": False, "msf": False, "slow": False}

    def test_returns_none_for_empty_site_resnums(self):
        sysinfo = SYSTEMS["KRAS_G12C"]
        assert seed_readiness_shift(
            sysinfo["apo"], sysinfo["chain"], sysinfo["holo"], sysinfo["chain"],
            site_resnums=[], drug_resnums=sysinfo["pocket_full"][4.5], cutoff=8.0,
        ) is None


class TestConnectivityChangeCharacterization:
    def test_kras_g12c_apo_holo_pinned_summary(self):
        _apo, sysinfo = _load_kras_apo()
        cc = connectivity_change(sysinfo["apo"], sysinfo["chain"], sysinfo["holo"], sysinfo["chain"], cutoff=8.0)

        # TASK-0296, regenerated against 4LDJ (169->170-residue apo shifts
        # every shared-residue-set count here too).
        assert cc["summary"] == {
            "n_shared": 167,
            "ddm_max": 8.35,
            "contacts_formed": 27,
            "contacts_broken": 27,
            "mean_abs_ddcc": 0.009,
            "most_reorganized": [63, 64, 0, 60, 62],
        }

    def test_kras_g12c_ddcc_sample_pinned(self):
        _apo, sysinfo = _load_kras_apo()
        cc = connectivity_change(sysinfo["apo"], sysinfo["chain"], sysinfo["holo"], sysinfo["chain"], cutoff=8.0)

        # TASK-0296, regenerated against 4LDJ
        assert cc["ddcc"][0][:5] == pytest.approx([0.0, 0.024, 0.028, 0.036, 0.036], abs=1e-3)
        assert cc["cutoff"] == 8.0
        assert cc["downsampled"] is False
