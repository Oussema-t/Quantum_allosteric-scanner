"""TASK-0229.006 -- COREX-style Ensemble Allosteric Model coverage.

Real-structure tests (KRAS_G12C apo, 4OBE) are skipped, not failed, when
network access is unavailable -- matching this project's own established
pattern for any test that needs a live RCSB fetch.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from allostery.corex import (  # noqa: E402
    R_GAS,
    TEMPERATURE,
    apolar_max_asa_fraction,
    build_folding_windows,
    coupling_score,
    corex_ensemble,
    window_free_energy,
)


class TestBuildFoldingWindows:
    def test_generates_every_contiguous_stretch_per_window_size(self):
        resnums = list(range(1, 11))  # 10 residues
        windows = build_folding_windows(resnums, window_sizes=(3, 5))
        # size-3: 8 windows (1-3 .. 8-10); size-5: 6 windows (1-5 .. 6-10)
        assert len(windows) == 8 + 6
        assert (1, 2, 3) in windows
        assert (8, 9, 10) in windows
        assert (1, 2, 3, 4, 5) in windows
        assert (6, 7, 8, 9, 10) in windows

    def test_skips_window_sizes_larger_than_the_sequence(self):
        resnums = list(range(1, 5))  # 4 residues
        windows = build_folding_windows(resnums, window_sizes=(3, 10))
        assert all(len(w) == 3 for w in windows)
        assert len(windows) == 2  # 4-3+1


class TestWindowFreeEnergy:
    def test_more_buried_apolar_surface_raises_dg(self):
        """More apolar surface newly exposed by unfolding -> higher dG_unfold
        (unfolding is *less* favourable, correctly signed: burying
        hydrophobic surface stabilises the folded state)."""
        window = (1, 2, 3)
        low_burial = {1: 90.0, 2: 90.0, 3: 90.0}   # native ASA close to max -> little buried
        high_burial = {1: 10.0, 2: 10.0, 3: 10.0}  # native ASA far below max -> a lot buried
        max_asa = {1: 100.0, 2: 100.0, 3: 100.0}
        dg_low = window_free_energy(window, low_burial, max_asa, n_conf_residues=3)
        dg_high = window_free_energy(window, high_burial, max_asa, n_conf_residues=3)
        assert dg_high > dg_low

    def test_more_conformational_residues_lowers_dg_via_entropy(self):
        """Holding the hydrophobic (ASA) term fixed, crediting more
        residues' worth of conformational entropy to the SAME window
        (n_conf_residues, the entropy term's own independent argument)
        must lower (more favourable) dG_unfold -- isolates the entropy
        term's own sign, independent of the hydrophobic term."""
        window = (1, 2, 3)
        native = {1: 50.0, 2: 50.0, 3: 50.0}
        max_asa = {1: 100.0, 2: 100.0, 3: 100.0}
        dg_few = window_free_energy(window, native, max_asa, n_conf_residues=3)
        dg_many = window_free_energy(window, native, max_asa, n_conf_residues=30)
        assert dg_many < dg_few


class TestApolarMaxAsaFraction:
    def test_fully_buried_residue_falls_back_to_half_max(self):
        frac = apolar_max_asa_fraction("ALA", native_apolar_asa=0.0, native_total_asa=0.0)
        assert frac == pytest.approx(0.5 * 129.0)

    def test_scales_by_native_apolar_fraction(self):
        # 80% of this residue's native surface is apolar -> 80% of MAX_ASA
        frac = apolar_max_asa_fraction("ALA", native_apolar_asa=80.0, native_total_asa=100.0)
        assert frac == pytest.approx(0.8 * 129.0)


def _fetch_kras_apo_model():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    try:
        import Bio.PDB as PDB

        from backend.data_layer import fetch
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"backend/BioPython unavailable: {exc!r}")
    try:
        fp = fetch("4OBE")
    except Exception as exc:
        pytest.skip(f"real-structure fetch unavailable in this environment: {exc!r}")
    if fp is None:
        pytest.skip("real-structure fetch unavailable in this environment (fetch returned None)")
    structure = PDB.PDBParser(QUIET=True).get_structure("4OBE", fp)
    return structure[0]


class TestCorexEnsembleRealStructure:
    """This task's own Planned Validation: kappa_f must reproduce known
    stability behaviour (buried > exposed) on a real structure before any
    coupling number is trusted."""

    def test_buried_residues_more_stable_than_exposed(self):
        model = _fetch_kras_apo_model()
        kf = corex_ensemble(model, "A")

        from allostery.corex import per_atom_asa, per_residue_native_asa

        per_atom_asa(model)
        native_asa = per_residue_native_asa(model["A"])
        resnums = sorted(kf.keys())
        asa = np.array([native_asa.get(rn, np.nan) for rn in resnums])
        kfv = np.array([kf[rn] for rn in resnums])
        finite = np.isfinite(asa) & np.isfinite(kfv) & (kfv > 0)

        from scipy.stats import spearmanr
        rho, p = spearmanr(asa[finite], np.log10(kfv[finite]))
        assert rho < 0
        assert p < 0.01

    def test_coupling_score_runs_and_returns_finite_values_for_most_active_site_residues(self):
        model = _fetch_kras_apo_model()
        active_site = [10, 11, 12, 13, 14, 15, 16, 17, 18, 29, 30, 31, 32, 33, 34, 35, 59, 60, 116, 117, 118, 119]
        pocket = [61, 63, 68, 72, 96, 99, 103]
        result = coupling_score(model, "A", site_resnums=pocket, active_site_resnums=active_site)
        assert set(result["coupling"]).issubset(set(active_site))
        assert len(result["coupling"]) > 0
        assert all(np.isfinite(v) for v in result["coupling"].values())
