"""TASK-0268 -- single-residue MUTATIONAL frustration (Ferreiro, Parra,
Radusky, Turjanski, Wolynes, Jenik 2012, *Nucleic Acids Research* 40:W348-
W351, doi:10.1093/nar/gks447, "Protein frustratometer" -- citation verified
live via Crossref, not from memory), the direct empirical test of this
project's own [[HYP-P13]]: allostery as stabilisation of an otherwise-
disfavoured local conformation, not signal propagation. If HYP-P13 is
right, cryptic/allosteric loci should sit at high native energetic
frustration -- local interactions worse than a randomised decoy, since a
site whose native packing is already near-optimal has nothing left to
relieve by a conformational shift.

**Not the Frustratometer software itself.** The real, published Python
package (PyPI `frustratometer`, github.com/cabb99/Frustratometer, the
direct lineage of the cited paper) was attempted and found genuinely
uninstallable in this environment: its own `llvmlite` build dependency
requires a system LLVM toolchain not present here (checked directly --
`llvm-config` absent, no `llvm@*` homebrew keg, `pip install` fails at
the `llvmlite` wheel build step, not a version-pin issue). Installing
LLVM system-wide was judged out of scope for a single task (an invasive
environment change, not a Python-only fix) rather than forced through.

**A real, from-scratch, honestly-scoped port of the SAME formalism**,
following this project's own established precedent for exactly this
situation ([[TASK-0229.006]]'s own COREX/EAM build, when the full
Hilser/Freire machinery wasn't practical to import either): single-
RESIDUE mutational frustration (Jenik et al.'s own named variant,
distinct from their "contact" and "configurational" frustration) --
randomise the FOCAL residue's own identity only (keep its structural
contacts and their real identities fixed), compare the native pairwise
energy against the resulting 19-decoy distribution.

**Pairwise potential**: Miyazawa S, Jernigan RL (1996), *J Mol Biol*
256:623-644, doi:10.1006/jmbi.1996.0114 -- citation verified live via
Crossref. The real 20x20 matrix (AAindex accession MIYS960101) was
fetched from the AAindex database directly, not hand-recalled or
estimated -- **bibliographically verified (a real, citable, systematic
database entry) but not independently re-OCR'd against the original
1996 paper's own printed table**, the same disclosure tier this
project's own `corex.py` MAX_ASA table already carries (Tien et al.
2013). Internal sanity-checked before use: diagonal values match the
textbook-expected pattern (Leu-Leu -7.37 and Ile-Ile -6.54 the most
favourable self-contacts, matching known hydrophobic-core-packing
propensity; Cys-Cys -5.44, matching disulfide-forming character).

This is a real simplification of the full AWSEM-based Frustratometer
(which adds burial/local-density and electrostatic terms this
single-potential port does not) -- stated explicitly, not silently
presented as equivalent to the published tool's own output.
"""
from __future__ import annotations

import numpy as np

# AAindex MIYS960101 (Miyazawa & Jernigan 1996), fetched live 2026-08-25,
# lower-triangular, row/column order below -- symmetrised into a full
# 20x20 matrix at import time.
_MJ_ORDER = "ARNDCQEGHILKMFPSTWYV"
_MJ_LOWER = [
    [-2.72],
    [-1.83, -1.55],
    [-1.84, -1.64, -1.68],
    [-1.70, -2.29, -1.68, -1.21],
    [-3.57, -2.57, -2.59, -2.41, -5.44],
    [-1.89, -1.80, -1.71, -1.46, -2.85, -1.54],
    [-1.51, -2.27, -1.51, -1.02, -2.27, -1.42, -0.91],
    [-2.31, -1.72, -1.74, -1.59, -3.16, -1.66, -1.22, -2.24],
    [-2.41, -2.16, -2.08, -2.32, -3.60, -1.98, -2.15, -2.15, -3.05],
    [-4.58, -3.63, -3.24, -3.17, -5.50, -3.67, -3.27, -3.78, -4.14, -6.54],
    [-4.91, -4.03, -3.74, -3.40, -5.83, -4.04, -3.59, -4.16, -4.54, -7.04, -7.37],
    [-1.31, -0.59, -1.21, -1.68, -1.95, -1.29, -1.80, -1.15, -1.35, -3.01, -3.37, -0.12],
    [-3.94, -3.12, -2.95, -2.57, -4.99, -3.30, -2.89, -3.39, -3.98, -6.02, -6.41, -2.48, -5.46],
    [-4.81, -3.98, -3.75, -3.48, -5.80, -4.10, -3.56, -4.13, -4.77, -6.84, -7.28, -3.36, -6.56, -7.26],
    [-2.03, -1.70, -1.53, -1.33, -3.07, -1.73, -1.26, -1.87, -2.25, -3.76, -4.20, -0.97, -3.45, -4.25, -1.75],
    [-2.01, -1.62, -1.58, -1.63, -2.86, -1.49, -1.48, -1.82, -2.11, -3.52, -3.92, -1.05, -3.03, -4.02, -1.57, -1.67],
    [-2.32, -1.90, -1.88, -1.80, -3.11, -1.90, -1.74, -2.08, -2.42, -4.03, -4.34, -1.31, -3.51, -4.28, -1.90, -1.96, -2.12],
    [-3.82, -3.41, -3.07, -2.84, -4.95, -3.11, -2.99, -3.42, -3.98, -5.78, -6.14, -2.69, -5.55, -6.16, -3.73, -2.99, -3.22, -5.06],
    [-3.36, -3.16, -2.76, -2.76, -4.16, -2.97, -2.79, -3.01, -3.52, -5.25, -5.67, -2.60, -4.91, -5.66, -3.19, -2.78, -3.01, -4.66, -4.17],
    [-4.04, -3.07, -2.83, -2.48, -4.96, -3.07, -2.67, -3.38, -3.58, -6.05, -6.48, -2.49, -5.32, -6.29, -3.32, -3.05, -3.46, -5.18, -4.62, -5.52],
]


def _build_mj_matrix() -> np.ndarray:
    n = len(_MJ_ORDER)
    m = np.zeros((n, n))
    for i, row in enumerate(_MJ_LOWER):
        for j, val in enumerate(row):
            m[i, j] = val
            m[j, i] = val
    return m


MJ_MATRIX = _build_mj_matrix()
_AA_INDEX = {aa: i for i, aa in enumerate(_MJ_ORDER)}

_THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
}

CONTACT_CUTOFF = 8.0  # Angstrom, CB-CB -- this project's own established convention (TASK-0204)


def single_residue_frustration(coords: np.ndarray, resnames: list, cutoff: float = CONTACT_CUTOFF):
    """Per-residue mutational frustration Z-score.

    `coords`: (N,3) CB (CA for glycine) coordinates -- caller's own
    responsibility to supply real side-chain-representative positions,
    matching `task0204_packing_hardness._cbeta_coords`'s own convention.
    `resnames`: length-N list of 3-letter residue names, same order as
    `coords`.

    For each residue i with >=1 real contact (CB-CB <= cutoff) whose own
    identity resolves to a standard amino acid: E_native = sum over
    contacts j of MJ(aa_i, aa_j). E_decoy = the same sum recomputed for
    each of the 19 non-native amino acids at position i (neighbours j
    and their identities held fixed -- ONLY the focal residue is
    randomised, the "single-residue" variant Jenik et al. 2012 name
    explicitly). Z = (E_native - mean(E_decoy)) / std(E_decoy).

    Returns (z_scores, n_contacts) -- both (N,) arrays; NaN where a
    residue has zero real contacts or a non-standard resname (HETATM
    that slipped through, etc.) -- caller's own responsibility to handle
    NaN, matching every other per-residue observable in this project.
    """
    n = len(coords)
    d = np.linalg.norm(coords[:, None, :] - coords[None, :, :], axis=-1)
    aa_idx = np.array([_AA_INDEX.get(_THREE_TO_ONE.get(rn, ""), -1) for rn in resnames])

    z = np.full(n, np.nan)
    n_contacts = np.zeros(n, dtype=int)
    for i in range(n):
        if aa_idx[i] < 0:
            continue
        neighbours = np.where((d[i] <= cutoff) & (d[i] > 0) & (aa_idx >= 0))[0]
        if len(neighbours) == 0:
            continue
        neighbour_aa = aa_idx[neighbours]
        n_contacts[i] = len(neighbours)

        e_native = float(MJ_MATRIX[aa_idx[i], neighbour_aa].sum())
        decoys = [aa for aa in range(len(_MJ_ORDER)) if aa != aa_idx[i]]
        e_decoy = np.array([MJ_MATRIX[aa, neighbour_aa].sum() for aa in decoys])
        std = e_decoy.std()
        if std > 0:
            z[i] = (e_native - e_decoy.mean()) / std
    return z, n_contacts
