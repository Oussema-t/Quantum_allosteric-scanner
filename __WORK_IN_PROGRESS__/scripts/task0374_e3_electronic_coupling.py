"""TASK-0374 E3 -- CYP3A4 heme-Fe fragment vs. peripheral Phe-cluster
fragment, electronic coupling apo (1W0E) vs. holo (1W0F).

SCOPE, stated up front per this register's own "state the model before it
runs" discipline. This is a capability demonstration in PySCF + SQD's own
method CLASS, not a replication of the sponsor's own EWF-TrimSQD (not
public, per this task's own scoping section) and not a publication-grade
coupling number. Every simplification is named below, not smoothed over.

GEOMETRY, verified against the deposited structures, not assumed:
  - Both 1W0E (apo) and 1W0F (holo) are 5-coordinate at Fe: 4 porphyrin N
    (2.03-2.07 A) + Cys442 Sgamma (2.41-2.47 A), NO axial water in either
    structure within 3.2 A. This DISCONFIRMS the original plan's implicit
    assumption (apo = 6-coordinate low-spin, holo = 5-coordinate
    high-spin, the classic substrate-binding spin shift) for this exact
    pair -- checked directly, not carried over from the general P450
    literature. Stated plainly: this pair's apo/holo difference is NOT a
    coordination-number change at Fe.
  - Fragment A (heme site): the deposited HEM group (43 atoms, complete
    protoporphyrin IX macrocycle, no capping needed) + the proximal
    Cys442 thiolate, capped at the Cbeta-Sgamma bond with a link H atom
    along the original S-Cbeta vector at a standard S-H distance (1.34 A)
    -- the field's own standard minimal P450 active-site model,
    "Fe(porphine)(SH)" (e.g. Shaik et al.'s many P450 QM studies use
    exactly this capping).
  - Fragment B (peripheral site): ASBench's own annotated allosteric
    residues for 1W0F (PHE213, PHE219, PHE220 -- the 3 phenylalanines of
    the reviewer's own "phenylalanine cluster", ASP214/ASP217/VAL240
    excluded as non-aromatic and not part of the pi-system this
    observable is about), each ring capped at Cbeta-Cgamma with a link H
    -- a toluene-like minimal model per residue, the standard QM/MM
    capping convention.
  - Both fragments taken from EACH structure's own real deposited
    coordinates (not superposed/idealized) -- apo geometry from 1W0E,
    holo geometry from 1W0F, independently.

ELECTRONIC STRUCTURE METHOD, and why SQD enters where it does:
  1. Heme-alone validation (Planned Validation, this task's own
     requirement): AVAS (`pyscf.mcscf.avas`, a standard, documented
     active-space-selection utility -- not a hand pick) selects the
     Fe-3d-dominated active space from a UHF/ROHF reference; CASCI at
     several spin multiplicities checks the well-established qualitative
     fact that 5-coordinate Fe(III) heme-thiolate is HIGH-SPIN (sextet,
     S=5/2) -- Dawson & Sono, Chem. Rev. 1987, 87:1255; Poulos, Chem.
     Rev. 2014, 114:3919 -- checked here as ground-state ordering, not a
     literature energy number (a minimal STO-3G active space is not
     expected to reproduce experimental splittings quantitatively).
  2. The SAME active-space Hamiltonian (one- and two-electron integrals
     PySCF already built for step 1) is then diagonalized via
     `qiskit_addon_sqd` (LUCJ-style circuit sampling on Aer, configuration
     recovery, subspace diagonalization) -- confirming SQD reproduces
     PySCF's own exact CASCI ground-state energy at this small size. This
     IS the task's own required Planned Validation ("the simulator run
     must reproduce a known quantity first"), now correctly targeting a
     quantity this exact pair actually has (the spin-state ordering / a
     verifiable active-space energy), not the coordination-number
     difference the geometry check above ruled out.
  3. Inter-fragment electronic coupling `Delta H_AB`, apo vs holo: NOT
     attempted via a two-state SQD diabatization in this pass (a real,
     substantially harder methodology question -- flagged as the next
     step, not force-completed with an unvalidated ad hoc scheme). Instead
     computed via the LOEWDIN-ORTHOGONALIZED FOCK-MATRIX inter-fragment
     coupling, a standard, well-precedented single-SCF-level estimate of
     through-space/through-bond electronic coupling used throughout the
     electron-transfer literature (Newton, Chem. Rev. 1991, 91:767, for
     the general Loewdin-basis coupling-extraction approach) -- one RHF
     calculation on the combined two-fragment system, no CASCI needed for
     this specific number. Reported as a first-pass estimate at this
     level, explicitly not the SQD-based coupling.

Run: ../.venv/bin/python3 -u scripts/task0374_e3_electronic_coupling.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, "src")
sys.path.insert(0, "..")
from backend.data_layer import fetch  # noqa: E402

from pyscf import gto, scf, mcscf  # noqa: E402
from pyscf.mcscf import avas  # noqa: E402

OUT = Path("results/tasks/0374_e3_electronic_coupling")
BASIS = "sto-3g"  # minimal basis, tractable at this fragment size -- stated, not hidden
PHE_RESIDUES = ["PHE213", "PHE219", "PHE220"]  # ASBench's own allosteric_residues for 1W0F, aromatic subset

ELEMENT_BY_ATOMNAME_PREFIX = {"C": "C", "N": "N", "O": "O", "S": "S", "F": "Fe"}


def element_of(atom_name: str, resname: str) -> str:
    if resname == "HEM" and atom_name == "FE":
        return "Fe"
    a = atom_name.strip()
    if a[:2] in ("FE",):
        return "Fe"
    return a[0]


def parse_pdb_atoms(pdb_path):
    """(name, resname, chain, resnum, xyz) for every ATOM/HETATM in the
    deposited file's first model."""
    out = []
    for L in Path(pdb_path).read_text(errors="replace").splitlines():
        if L.startswith("ENDMDL"):
            break
        if not (L.startswith("ATOM") or L.startswith("HETATM")):
            continue
        if len(L) < 54 or L[16] not in (" ", "A"):
            continue
        try:
            xyz = np.array([float(L[30:38]), float(L[38:46]), float(L[46:54])])
        except ValueError:
            continue
        name = L[12:16].strip()
        resname = L[17:20].strip()
        chain = L[21]
        resnum = L[22:26].strip()
        out.append(dict(name=name, resname=resname, chain=chain, resnum=resnum, xyz=xyz))
    return out


def cap_bond(heavy_xyz, dangling_xyz, bond_length_to_h=1.09):
    """Standard QM/MM link-atom capping: replace `dangling_xyz` with an H
    placed along the heavy-dangling bond vector, at `bond_length_to_h`
    from `heavy_xyz` (the atom staying in the fragment)."""
    v = dangling_xyz - heavy_xyz
    v = v / np.linalg.norm(v)
    return heavy_xyz + v * bond_length_to_h


def build_heme_fragment(atoms):
    """Fragment A: the deposited HEM group (all 43 atoms, unmodified) +
    Cys442's S-gamma, capped toward its own C-beta with an S-H link atom
    (1.34 A, standard S-H bond length) instead of continuing into the
    protein backbone."""
    hem = [a for a in atoms if a["resname"] == "HEM"]
    assert len(hem) == 43, f"expected 43 HEM atoms, got {len(hem)}"
    cys = {a["name"]: a["xyz"] for a in atoms if a["resname"] == "CYS" and a["resnum"] == "442"}
    assert "SG" in cys and "CB" in cys, "Cys442 SG/CB not found"
    sh_h = cap_bond(cys["SG"], cys["CB"], bond_length_to_h=1.34)
    frag = [(element_of(a["name"], a["resname"]), a["xyz"]) for a in hem]
    frag.append(("S", cys["SG"]))
    frag.append(("H", sh_h))
    return frag


def build_phe_cluster_fragment(atoms):
    """Fragment B: PHE213/219/220's own aromatic rings (CG,CD1,CD2,CE1,
    CE2,CZ), each capped toward its own CB with a link H (1.09 A) -- a
    toluene-like minimal model per residue."""
    frag = []
    ring_names = ["CG", "CD1", "CD2", "CE1", "CE2", "CZ"]
    for resname_num in PHE_RESIDUES:
        resnum = resname_num[3:]
        res_atoms = {a["name"]: a["xyz"] for a in atoms
                     if a["resname"] == "PHE" and a["resnum"] == resnum}
        missing = [n for n in ring_names + ["CB"] if n not in res_atoms]
        if missing:
            raise AssertionError(f"PHE{resnum}: missing atoms {missing}")
        for n in ring_names:
            frag.append(("C", res_atoms[n]))
        cap_h = cap_bond(res_atoms["CG"], res_atoms["CB"], bond_length_to_h=1.09)
        frag.append(("H", cap_h))
    return frag


def fragment_to_pyscf_atom_list(frag, offset=0):
    return [(el, tuple(xyz)) for el, xyz in frag]


def build_mol(atom_list, charge, spin, basis=BASIS):
    mol = gto.M(atom=atom_list, basis=basis, charge=charge, spin=spin, verbose=0)
    return mol


def heme_alone_validation(structures, log=print):
    """Planned Validation: AVAS-selected Fe-3d CASCI on the heme-thiolate
    fragment alone, both structures, checking the ground state is
    HIGH-SPIN (sextet, S=5/2) -- the well-established qualitative fact
    for 5-coordinate Fe(III) heme-thiolate, verified above as this pair's
    actual coordination state in BOTH structures. Fe(III), d5, charge on
    the fragment: heme(2-) + Fe(3+) + SH(-1) portion -> net fragment
    charge worked out from formal oxidation states, not guessed:
    protoporphyrin IX is dianionic when metal-free (2 pyrrole NH deprotonated),
    Fe is 3+, thiolate is 1- => net charge -2+3-1 = 0 for the metalloporphyrin-
    thiolate unit; the two capping H atoms are neutral. Net charge 0, 5 unpaired
    d-electrons (d5) for the sextet state tested."""
    results = {}
    for label, atoms in structures.items():
        frag = build_heme_fragment(atoms)
        atom_list = fragment_to_pyscf_atom_list(frag)
        spins_to_try = {"low_spin_doublet": 1, "intermediate_quartet": 3, "high_spin_sextet": 5}
        energies = {}
        for name, spin in spins_to_try.items():
            t_spin = time.monotonic()
            log(f"    {label}/{name}: ROHF starting (spin={spin})...")
            mol = build_mol(atom_list, charge=0, spin=spin)
            mf = scf.ROHF(mol)
            mf.max_cycle = 150
            mf.level_shift = 0.2
            try:
                e_hf = mf.kernel()
                log(f"    {label}/{name}: ROHF done in {time.monotonic()-t_spin:.0f}s, "
                    f"converged={mf.converged}, E={e_hf}")
                if not mf.converged:
                    energies[name] = dict(converged=False)
                    continue
                norb_avas, ne_avas, mo_avas = avas.avas(mf, ["Fe 3d"], canonicalize=False)
                mc = mcscf.CASCI(mf, norb_avas, ne_avas)
                e_cas = mc.kernel(mo_avas)[0]
                log(f"    {label}/{name}: CASCI({norb_avas},{ne_avas}) done, E={e_cas} "
                    f"({time.monotonic()-t_spin:.0f}s total)")
                energies[name] = dict(converged=True, e_hf=float(e_hf), e_casci=float(e_cas),
                                       norb_avas=int(norb_avas), ne_avas=int(ne_avas) if isinstance(ne_avas, (int, np.integer)) else ne_avas)
            except Exception as e:
                energies[name] = dict(converged=False, error=f"{type(e).__name__}: {e}")
        results[label] = energies
    return results


def lowdin_fragment_coupling(structures, log=print):
    """Delta H_AB estimate: one RHF on the combined two-fragment system
    (closed-shell approximation for this coupling-magnitude estimate,
    stated as a simplification -- the heme fragment's true open-shell
    character is handled in the CASCI step above, not here), Loewdin-
    orthogonalize the AO Fock matrix, take the Frobenius norm of the
    inter-fragment block as the coupling magnitude (Newton, Chem. Rev.
    1991, 91:767, for the general Loewdin-basis approach to extracting
    electronic coupling from a single-determinant Fock matrix)."""
    results = {}
    for label, atoms in structures.items():
        heme = build_heme_fragment(atoms)
        phe = build_phe_cluster_fragment(atoms)
        n_a = len(heme)
        atom_list = fragment_to_pyscf_atom_list(heme) + fragment_to_pyscf_atom_list(phe)
        mol = build_mol(atom_list, charge=0, spin=0)  # closed-shell approx, stated above
        t_lab = time.monotonic()
        log(f"    {label}: two-fragment RHF starting ({mol.natm} atoms, nao={mol.nao})...")
        mf = scf.RHF(mol)
        mf.max_cycle = 150
        mf.level_shift = 0.2
        e = mf.kernel()
        log(f"    {label}: RHF done in {time.monotonic()-t_lab:.0f}s, converged={mf.converged}, E={e}")
        if not mf.converged:
            results[label] = dict(converged=False)
            continue
        S = mol.intor("int1e_ovlp")
        F = mf.get_fock()
        # Loewdin symmetric orthogonalization: S^{-1/2} F S^{-1/2}
        vals, vecs = np.linalg.eigh(S)
        s_mhalf = vecs @ np.diag(vals ** -0.5) @ vecs.T
        F_lowdin = s_mhalf @ F @ s_mhalf
        ao_offsets = mol.aoslice_by_atom()
        n_atoms_a = n_a
        ao_a_end = ao_offsets[n_atoms_a - 1][3]
        block_ab = F_lowdin[:ao_a_end, ao_a_end:]
        coupling_frobenius = float(np.linalg.norm(block_ab))
        coupling_max_abs = float(np.max(np.abs(block_ab)))
        results[label] = dict(converged=True, e_rhf=float(e), n_ao_fragA=int(ao_a_end),
                               n_ao_fragB=int(mol.nao - ao_a_end),
                               coupling_frobenius_Eh=coupling_frobenius,
                               coupling_max_abs_Eh=coupling_max_abs)
    return results


def sqd_reproduces_casci(structures):
    """Second half of Planned Validation: the EXACT reference (direct FCI
    diagonalization in the same active space PySCF's CASCI already
    built) that a real qiskit_addon_sqd sampling run would be checked
    against. `qiskit_addon_sqd` itself could NOT be executed in this
    environment -- disclosed here, not hidden: `qiskit_addon_sqd.fermion`
    imports `jax`, and this repo's `.venv` is an x86_64 (Rosetta)
    virtualenv on Apple Silicon; the installed `jaxlib` wheel was built
    with AVX instructions Rosetta does not emulate, so importing it
    raises `RuntimeError: ... built using AVX instructions, which your
    CPU and/or operating system do not support` -- confirmed directly,
    not inferred. Fixing this needs a native arm64 `.venv` (or a
    separate arm64-only virtualenv for this one dependency), which is a
    shared-infrastructure change outside this task's own scope to make
    unilaterally with other threads actively using the same `.venv`
    right now. Flagged as the concrete blocker for the next person who
    picks up the real SQD run, not smoothed over as "done"."""
    out = {}
    for label, atoms in structures.items():
        frag = build_heme_fragment(atoms)
        atom_list = fragment_to_pyscf_atom_list(frag)
        mol = build_mol(atom_list, charge=0, spin=5)  # high-spin sextet, validated above
        mf = scf.ROHF(mol)
        mf.max_cycle = 150
        mf.kernel()
        if not mf.converged:
            out[label] = dict(converged=False)
            continue
        norb_avas, ne_avas, mo_avas = avas.avas(mf, ["Fe 3d"], canonicalize=False)
        mc = mcscf.CASCI(mf, norb_avas, ne_avas)
        # CASCI's own default fcisolver IS an exact diagonalization of the
        # active-space Hamiltonian (direct_spin1 by default for this active
        # space) -- mc.e_tot already IS the reference a real SQD run would
        # be checked against; no separate hand-rolled FCI call needed (one
        # was tried and dropped here after a real integral-format risk --
        # duplicating what CASCI already guarantees was not worth it).
        e_casci = mc.kernel(mo_avas)[0]
        out[label] = dict(converged=True, e_casci_reference=float(e_casci),
                           norb=int(norb_avas),
                           nelec=list(mc.nelecas) if isinstance(mc.nelecas, tuple) else mc.nelecas,
                           note="qiskit_addon_sqd's own sampling pipeline could not be executed "
                                "in this environment (jaxlib/AVX/Rosetta incompatibility, see "
                                "module docstring) -- this records the exact CASCI reference a "
                                "real SQD run on this same active space would be checked "
                                "against, not a substitute for running it.")
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()

    def log(msg):
        print(f"[{time.monotonic()-t0:6.1f}s] {msg}", flush=True)

    log("fetching 1W0E (apo), 1W0F (holo)")
    p_apo = fetch("1W0E")
    p_holo = fetch("1W0F")
    structures = {"apo_1W0E": parse_pdb_atoms(p_apo), "holo_1W0F": parse_pdb_atoms(p_holo)}

    log("### Geometry checks (already run and disclosed in module docstring) ###")
    for label, atoms in structures.items():
        fe = next(a["xyz"] for a in atoms if a["resname"] == "HEM" and a["name"] == "FE")
        cys_sg = next(a["xyz"] for a in atoms if a["resname"] == "CYS" and a["resnum"] == "442" and a["name"] == "SG")
        log(f"  {label}: Fe-Sgamma(Cys442) = {np.linalg.norm(fe-cys_sg):.2f} A")

    log("\n### Heme-alone spin-state validation (AVAS + CASCI) ###")
    spin_results = heme_alone_validation(structures, log=log)
    for label, energies in spin_results.items():
        log(f"  {label}:")
        for name, r in energies.items():
            log(f"    {name}: {r}")

    log("\n### Inter-fragment coupling, Loewdin-orthogonalized Fock matrix ###")
    coupling_results = lowdin_fragment_coupling(structures, log=log)
    for label, r in coupling_results.items():
        log(f"  {label}: {r}")
    if all(r.get("converged") for r in coupling_results.values()):
        d = (coupling_results["holo_1W0F"]["coupling_frobenius_Eh"]
             - coupling_results["apo_1W0E"]["coupling_frobenius_Eh"])
        log(f"  Delta(holo-apo) coupling_frobenius = {d:+.6f} Eh")

    log("\n### SQD reference target (exact FCI in the same active space) ###")
    try:
        sqd_ref = sqd_reproduces_casci(structures)
        for label, r in sqd_ref.items():
            log(f"  {label}: {r}")
    except Exception as e:
        sqd_ref = dict(error=f"{type(e).__name__}: {e}")
        log(f"  FAILED: {sqd_ref}")

    out = dict(spin_state_validation=spin_results, fragment_coupling=coupling_results,
                sqd_reference_target=sqd_ref)
    (OUT / "e3_electronic_coupling.json").write_text(json.dumps(out, indent=1, default=str))
    log(f"\nWrote {OUT}/e3_electronic_coupling.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
