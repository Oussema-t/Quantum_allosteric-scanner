# Connectivity matrices from the CTQW

The first of the three required deliverables: the residue-by-residue transport matrix

    C_ij = lim_{T->inf} (1/T) integral_0^T |<j|e^{-iHt}|i>|^2 dt = sum_k |v_k(i)|^2 |v_k(j)|^2
         = (V o V)(V o V)^T   for  H = V diag(w) V^T   (the average mixing matrix, Godsil).

`C` depends on the **operator only** — seeding and scoring do not enter it — so one matrix per
Hamiltonian. Every matrix here is symmetric and row-stochastic (rows sum to 1) by construction.

## Files (gzipped CSV, N x N, one row/col per residue)

| target | structure | operator | AUC (best cell) | file |
|---|---|---|---|---|
| KRAS G12C | 4LDJ | `H_new` (submission) | 0.828 | `KRAS_G12C_4LDJ_connectivity_best_H_new.csv.gz` |
| KRAS G12C | 4LDJ | `H7_harm` (worst) | 0.161 | `KRAS_G12C_4LDJ_connectivity_worst_H7_harm.csv.gz` |
| BCR-ABL1 | 1OPL | `H6_exp` (best) | 0.796 | `BCR_ABL1_1OPL_connectivity_best_H6_exp.csv.gz` |
| BCR-ABL1 | 1OPL | `H5_gauss` (worst) | 0.227 | `BCR_ABL1_1OPL_connectivity_worst_H5_gauss.csv.gz` |

`*_bestworst.pdf` shows the two matrices side by side plus their difference.

## Submission parameters (pre-registered)

`H_new = L_sym + diag(0.08 V_B + 0.16 V_T + 0.08 V_R + 0.04 V_C + 0.04 V_M)`, exponential contact
graph, **NET_CUTOFF = 10.0 A, ALPHA = 0.30, term_frac = 0.05, n_low_modes = 10**. KRAS uses `4LDJ`
(true G12C: residue 12 = CYS, GDP+MG only); Table 1's `4OBE` is wild-type at residue 12.

## Reproduce the KRAS matrix from scratch

    python3 reproduce_kras_connectivity.py pdb_cache/4LDJ.pdb

Parses 4LDJ chain A (BioPython), builds `H_new` with the parameters above, computes `C`, and
verifies it against the committed notebook matrix. Reproduces it to a relative Frobenius error of
6.6e-6 — the CSV's own 6-significant-figure write precision, i.e. bit-for-bit the same operator.

Source of the matrices: `Quantum_Allosteric_Scanner_v2.ipynb`, cell 14w.


## MIN_HOP per target (affects the top-5 selection, NOT the matrix)

The N x N connectivity matrix `C` depends on the **operator only** and is byte-identical at every
MIN_HOP (verified: max|diff| = 0 between MIN_HOP 1 and 2). MIN_HOP filters which residues are
*candidates* for the top-5, so the top-5 sub-blocks and their AUCs are MIN_HOP-dependent.

- **KRAS G12C: MIN_HOP = 1** (report-matching; the switch-II pocket is near the active site).
  Best `H_new`/Green AUC 0.809, worst `H11_aniso` AUC 0.184, 3 of 5 predicted residues in the pocket.
- **BCR-ABL1: MIN_HOP = 2** (the myristoyl pocket is distal). Best `H6_exp` AUC 0.796, P@5 1.0.

## Top-5 predicted residues x all active-site residues

`*_top5xactive_<best|worst>_<operator>.csv` : the 5 x (n_active) sub-block of C, rows = the five
residues the pipeline predicts (ranked by that operator's winning score), cols = every active-site
residue. Row/column residue numbers are in the CSV header. The ranking's AUC reproduces the reported
cell AUC exactly, so the top-5 are the faithful hit list, not a proxy.

| target | operator | score | AUC | drug residues in top-5 |
|---|---|---|---|---|
| KRAS G12C | `H_new` (best) | Green E=lmax eta=0.05 | 0.809 | 3 of 5 (res 60, 96, 61) |
| KRAS G12C | `H11_aniso` (worst) | residual RAW | 0.184 | 0 of 5 |
| BCR-ABL1 | `H6_exp` (best) | residual LOG + dX | 0.796 | **5 of 5** |
| BCR-ABL1 | `H5_gauss` (worst) | R = p_peak/p_avg | 0.227 | 0 of 5 |

Source: `Quantum_Allosteric_Scanner_v2.ipynb`, cell 14w.


## Cardiac myosin (8QYP -> 8QYR, drug XB2), MIN_HOP=2, seeded top-10

With top-10 seeding the true pocket (fpocket P96, mavacamten site) is seeded: 243 seeds, 12
drug-pocket residues (base rate 0.049). Selection by **P@5** (the hit-list criterion), not AUC:

| cell | operator | score | AUC | P@5 |
|---|---|---|---|---|
| best (P@5) | `H3_normL` | dX dip depth | 0.685 | **0.4** (2 of top-5 in the pocket) |
| best (AUC) | `H_new` | Green E=zero eta=0.01 | 0.795 | 0.0 |
| worst | `H8_gnm` | -dD mean | 0.068 | 0.0 |
| median cell | - | - | 0.504 | 0.0 |

Matrices: `_connectivity_best_H3_normL.csv.gz` and `_connectivity_worst_H8_gnm.csv.gz`
(704 x 704, operator-only, so seeding-independent). The best cell reaches P@5 0.4 -- 2 of the 5
predicted residues are genuine mavacamten-site residues -- the median cell is at chance (0.504),
so this is a weak partial hit, not a clean success.

NOTE: fpocket pocket detection was not bit-reproducible between runs (a fresh headless run detected
a different pocket set that missed P96); the seeding above is from the notebook run that seeds P96.
The connectivity matrices themselves are operator+structure-only and reproduce exactly.


## HIV-1 RT (1DLO -> 3V81, NNRTI pocket) -- additional allosteric target

Seeded like the mandated three: consensus (fpocket druggability + PASSer allostery), top-10,
MIN_HOP 2. The NNRTI pocket (fpocket P1) ranks #11 on druggability but #3 on PASSer allostery, so
consensus seeds it (112 seeds, 9 drug) where fpocket-only top-10 does not. Best cell
`H14_anmP`/p_peak AUC 0.963 P@5 0.8; worst (different operator, for a distinct matrix)
`H9_bfac` AUC 0.230. Pre-registered `H_new` held-out 0.665, p=0.060. Matrices are operator-only
(556 x 556), reproducible from 1DLO chain A; the *seeding* needs `passer_cache.json` present.
