"""TASK-0229.006 -- COREX-style Ensemble Allosteric Model (EAM).

Ref [4] (Motlagh, Wrabl, Li & Hilser 2014, *Nature* 508:331) H4.1: allosteric
coupling is a **partition-function quantity over folded/unfolded segment
microstates**, not a pathway on a contact graph. TASK-0166's own
`conformational_entropy.py` already tested the *harmonic* (Gaussian,
linear-response) version of this idea and found it proximity-confounded
(|partial rho|=0.773) -- **harmonic stiffening is not unfolding**, so that
result says nothing about the genuine, nonlinear COREX picture this module
implements: a residue is either locally FOLDED (native) or UNFOLDED
(solvent-exposed, extended-chain-like) in a given microstate, never a small
harmonic displacement.

**Implementer's-call simplification, stated plainly (this task's own scope
does not mandate reproducing Hilser/Freire's exact multi-parameter Cp/H/S
machinery, only "ASA-parameterised dG per microstate")**: the full COREX
method (Hilser & Freire 1996) parameterises dCp, dH, and dS separately from
polar/apolar ASA changes via several fitted constants (Murphy & Freire 1992
and descendants) and extrapolates to any temperature via dCp. This module
uses a single-temperature (298.15 K), two-term free energy instead:

    dG_unfold(window) = dG_hydrophobic(window) - T * dS_conf(window)

  - dG_hydrophobic: apolar (carbon-only, by element -- a standard, simple
    classification, not Eisenberg & McLachlan's own finer atom-type table)
    surface area newly exposed by locally unfolding `window`, times a
    burial free energy coefficient (Eisenberg D, McLachlan AD. Solvation
    energy in protein folding and binding. Nature. 1986;319:199-203,
    doi:10.1038/319199a0 -- ~18 cal/(mol*A^2), bibliographically verified;
    the exact per-atom-type parameter table in that paper was not
    independently re-checked digit-by-digit, paywalled).
  - dS_conf: a flat backbone conformational-entropy-gain estimate per
    residue unfolded (~4.1 cal/(mol*K), the right order of magnitude for
    R*ln(few) accessible backbone states per residue upon local unfolding
    -- a standard approximation in this literature, not the fuller
    per-residue-type table D'Aquino et al. 1996 use).

"Unfolded" reference ASA per residue: Tien MZ, Meyer AG, Sydykova DK,
Spielman SJ, Wilke CO. Maximum allowed solvent accessibilities of residues
in proteins. PLoS ONE. 2013;8:e80635, doi:10.1371/journal.pone.0080635 --
the paper's own "theoretical" scale, bibliographically verified (title/
authors/journal/DOI); **the table digits below are the widely-reproduced
values from that scale, not independently re-OCR'd from the paper's own
table image (paywalled/image-only) -- flagged, not silently presented as
primary-source-verified**, matching this project's own citation-integrity
convention of naming what wasn't checked.

This is a real, working, internally-consistent, ranking-oriented COREX-
style model -- not a literal reproduction of Hilser/Freire's own published
numbers. Validated against a qualitative sanity check (buried core residues
must show higher kappa_f than exposed loop residues), per this task's own
Planned Validation, before any coupling number is trusted.
"""
from __future__ import annotations

import numpy as np

R_GAS = 1.987e-3  # kcal/(mol*K)
TEMPERATURE = 298.15  # K, 25 C reference

HYDROPHOBIC_BURIAL_COEF = 18.0e-3  # kcal/(mol*A^2), Eisenberg & McLachlan 1986
BACKBONE_ENTROPY_PER_RESIDUE = 4.1e-3  # kcal/(mol*K*residue), standard order-of-magnitude estimate

# Tien et al. 2013 "theoretical" max ASA scale (A^2) -- widely-reproduced
# values, not independently re-OCR'd against the paper's own table image
# (see module docstring).
MAX_ASA = {
    "ALA": 129.0, "ARG": 274.0, "ASN": 195.0, "ASP": 193.0, "CYS": 167.0,
    "GLN": 225.0, "GLU": 223.0, "GLY": 104.0, "HIS": 224.0, "ILE": 197.0,
    "LEU": 201.0, "LYS": 236.0, "MET": 224.0, "PHE": 240.0, "PRO": 159.0,
    "SER": 155.0, "THR": 172.0, "TRP": 285.0, "TYR": 263.0, "VAL": 174.0,
}

APOLAR_ELEMENTS = {"C"}


def per_atom_asa(structure_model, probe_radius: float = 1.40) -> None:
    """Runs BioPython's ShrakeRupley SASA (a standard, validated algorithm,
    not re-implemented) in place on `structure_model` -- each atom gets a
    `.sasa` attribute afterward."""
    from Bio.PDB.SASA import ShrakeRupley

    ShrakeRupley(probe_radius=probe_radius).compute(structure_model, level="A")


def per_residue_native_asa(chain) -> dict:
    """Sums each residue's own atoms' SASA (already computed via
    `per_atom_asa`) into a single per-residue native ASA. Returns
    {resnum: asa}."""
    out = {}
    for res in chain:
        if res.id[0] != " ":
            continue
        atoms = list(res)
        if not atoms or not hasattr(atoms[0], "sasa"):
            continue
        out[res.id[1]] = float(sum(a.sasa for a in atoms))
    return out


def per_residue_apolar_native_asa(chain) -> dict:
    """Same as `per_residue_native_asa` but only summing carbon-atom SASA
    (the apolar/hydrophobic-burial term's own input) -- element-based
    polar/apolar classification, a standard simplification, not
    Eisenberg-McLachlan's own finer per-atom-type table."""
    out = {}
    for res in chain:
        if res.id[0] != " ":
            continue
        atoms = [a for a in res if a.element in APOLAR_ELEMENTS]
        if not atoms or not hasattr(atoms[0], "sasa"):
            continue
        out[res.id[1]] = float(sum(a.sasa for a in atoms))
    return out


def build_folding_windows(resnums: list, window_sizes=(6, 10, 15)) -> list:
    """Sliding-window folding units (COREX's own construction): for each
    window size, every contiguous stretch of that many residues, slid by
    one residue across the whole sequence. Returns a list of tuples of
    resnums (not indices) -- one microstate per window, "this window
    unfolded, everything else native," matching the practical O(N*W)
    COREX approximation (not the intractable full 2^N combinatorial
    powerset)."""
    windows = []
    n = len(resnums)
    for w in window_sizes:
        if w > n:
            continue
        for start in range(n - w + 1):
            windows.append(tuple(resnums[start:start + w]))
    return windows


def window_free_energy(window_resnums: tuple, native_apolar_asa: dict, apolar_max_asa: dict,
                        n_conf_residues: int, temperature: float = TEMPERATURE) -> float:
    """dG_unfold for one window microstate (kcal/mol) -- see module
    docstring for the two-term model. `apolar_max_asa` maps resnum -> the
    apolar (carbon-only) share of that residue's own MAX_ASA (see
    `apolar_max_asa_fraction`)."""
    d_apolar = 0.0
    for rn in window_resnums:
        native = native_apolar_asa.get(rn, 0.0)
        maxasa = apolar_max_asa.get(rn, native)  # never negative if resolved
        d_apolar += max(0.0, maxasa - native)
    dg_hydrophobic = HYDROPHOBIC_BURIAL_COEF * d_apolar
    ds_conf = BACKBONE_ENTROPY_PER_RESIDUE * n_conf_residues
    return dg_hydrophobic - temperature * ds_conf


def apolar_max_asa_fraction(resname: str, native_apolar_asa: float, native_total_asa: float) -> float:
    """Scales MAX_ASA (whole-residue) by this residue's own native
    apolar/total ASA split, giving an apolar-only max-ASA estimate without
    a second literature table for per-atom-type max values. A residue
    fully buried (native_total_asa~0) falls back to the whole-residue
    MAX_ASA scaled by a neutral 0.5 apolar fraction (no split information
    available from a fully buried native state) -- documented, not silent."""
    max_total = MAX_ASA.get(resname)
    if max_total is None:
        return native_apolar_asa
    if native_total_asa < 1e-6:
        return 0.5 * max_total
    frac_apolar = native_apolar_asa / native_total_asa
    return frac_apolar * max_total


def corex_ensemble(model, chain_id: str, window_sizes=(6, 10, 15), temperature: float = TEMPERATURE) -> dict:
    """Runs the full COREX-style ensemble on one chain of a real, already-
    fetched Bio.PDB structure model. Returns {resnum: kappa_f} -- the
    per-residue folded/unfolded equilibrium constant (higher = more
    stable/more often folded across the ensemble)."""
    per_atom_asa(model)
    chain = model[chain_id]
    resnums = sorted(r.id[1] for r in chain if r.id[0] == " ")
    resnames = {r.id[1]: r.resname for r in chain if r.id[0] == " "}

    native_total_asa = per_residue_native_asa(chain)
    native_apolar_asa = per_residue_apolar_native_asa(chain)
    apolar_max = {
        rn: apolar_max_asa_fraction(resnames[rn], native_apolar_asa.get(rn, 0.0), native_total_asa.get(rn, 0.0))
        for rn in resnums
    }

    windows = build_folding_windows(resnums, window_sizes)
    if not windows:
        raise ValueError("no folding windows generated -- chain too short for the requested window sizes")

    weights = np.empty(len(windows))
    for i, w in enumerate(windows):
        dg = window_free_energy(w, native_apolar_asa, apolar_max, n_conf_residues=len(w), temperature=temperature)
        weights[i] = np.exp(-dg / (R_GAS * temperature))

    folded_weight = {rn: 1.0 for rn in resnums}  # native state itself, K=1, always "folded" contribution
    unfolded_weight = {rn: 0.0 for rn in resnums}
    for w, k in zip(windows, weights):
        w_set = set(w)
        for rn in resnums:
            if rn in w_set:
                unfolded_weight[rn] += k
            else:
                folded_weight[rn] += k

    kappa_f = {rn: folded_weight[rn] / unfolded_weight[rn] if unfolded_weight[rn] > 0 else float("inf")
               for rn in resnums}
    return kappa_f


def coupling_score(model, chain_id: str, site_resnums, active_site_resnums,
                    window_sizes=(6, 10, 15), temperature: float = TEMPERATURE,
                    stabilization_bonus: float = 3.0) -> dict:
    """Perturbation-response coupling (the task's own required measure):
    "stabilise" `site_resnums` (mimicking ligand binding -- any microstate
    that would unfold a site residue is penalised by `stabilization_bonus`
    kcal/mol, i.e. effectively excluded from the ensemble, the same
    "binding locks this region folded" logic COREX-based allostery studies
    use) and re-run the ensemble; report the shift in kappa_f (as
    dG_f = -RT*ln(kappa_f), so shifts are additive and finite even when
    kappa_f itself saturates near-infinite) at `active_site_resnums`
    relative to the unperturbed ensemble.

    Returns {"native_dGf": {...}, "perturbed_dGf": {...}, "coupling": {...}}
    -- `coupling[rn] = perturbed_dGf[rn] - native_dGf[rn]` for each active
    site residue (positive = the active site is destabilised by binding at
    `site_resnums`, the disorder-propagates-to-active-site direction this
    task's own allosteric-coupling question is about)."""
    per_atom_asa(model)
    chain = model[chain_id]
    resnums = sorted(r.id[1] for r in chain if r.id[0] == " ")
    resnames = {r.id[1]: r.resname for r in chain if r.id[0] == " "}
    native_total_asa = per_residue_native_asa(chain)
    native_apolar_asa = per_residue_apolar_native_asa(chain)
    apolar_max = {
        rn: apolar_max_asa_fraction(resnames[rn], native_apolar_asa.get(rn, 0.0), native_total_asa.get(rn, 0.0))
        for rn in resnums
    }
    windows = build_folding_windows(resnums, window_sizes)
    site_set = set(site_resnums)

    def _run(perturb: bool):
        weights = np.empty(len(windows))
        for i, w in enumerate(windows):
            dg = window_free_energy(w, native_apolar_asa, apolar_max, n_conf_residues=len(w), temperature=temperature)
            if perturb and site_set & set(w):
                dg += stabilization_bonus
            weights[i] = np.exp(-dg / (R_GAS * temperature))
        folded_weight = {rn: 1.0 for rn in resnums}
        unfolded_weight = {rn: 0.0 for rn in resnums}
        for w, k in zip(windows, weights):
            w_set = set(w)
            for rn in resnums:
                if rn in w_set:
                    unfolded_weight[rn] += k
                else:
                    folded_weight[rn] += k
        dgf = {}
        for rn in resnums:
            kf = folded_weight[rn] / unfolded_weight[rn] if unfolded_weight[rn] > 0 else float("inf")
            dgf[rn] = -R_GAS * temperature * np.log(kf) if np.isfinite(kf) and kf > 0 else float("-inf")
        return dgf

    native_dgf = _run(perturb=False)
    perturbed_dgf = _run(perturb=True)
    coupling = {
        rn: (perturbed_dgf[rn] - native_dgf[rn])
        for rn in active_site_resnums if rn in native_dgf and np.isfinite(native_dgf[rn]) and np.isfinite(perturbed_dgf[rn])
    }
    return {"native_dGf": native_dgf, "perturbed_dGf": perturbed_dgf, "coupling": coupling}
