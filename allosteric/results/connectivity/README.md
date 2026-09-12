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

## Top-5 predicted residues x all active-site residues

`*_top5xactive_<best|worst>_<operator>.csv` : the 5 x (n_active) sub-block of C, rows = the five
residues the pipeline predicts (ranked by that operator's winning score), cols = every active-site
residue. Row/column residue numbers are in the CSV header. The ranking's AUC reproduces the reported
cell AUC exactly, so the top-5 are the faithful hit list, not a proxy.

| target | operator | score | AUC | drug residues in top-5 |
|---|---|---|---|---|
| KRAS G12C | `H_new` (best) | Green E=lmax eta=0.05 | 0.828 | 2 of 5 (res 61, 95) |
| KRAS G12C | `H7_harm` (worst) | residual LOG | 0.161 | 0 of 5 |
| BCR-ABL1 | `H6_exp` (best) | residual LOG + dX | 0.796 | **5 of 5** |
| BCR-ABL1 | `H5_gauss` (worst) | R = p_peak/p_avg | 0.227 | 0 of 5 |

Source: `Quantum_Allosteric_Scanner_v2.ipynb`, cell 14w.
