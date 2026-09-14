# AuraQu — Phase-1 supplementary (connectivity detail + walk traces)

Supplementary material for Team AuraQu's Phase-1 concept proposal (Cleveland Clinic problem
statement), referenced from Appendix B of the submission. **Each target's files come from one
pipeline run** (fpocket + PASSer consensus seeding; the seed-pocket cut and MIN_HOP are per-target
choices listed in the table), so the walk-trace AUC/P@5 equal the Table B.2 numbers by construction.

The predictor is a seeded continuous-time quantum walk (CTQW) on the residue contact network.
Its first required deliverable is the residue–residue **connectivity matrix** `C_ij` — the
average-mixing matrix `C_ij = Σ_k |v_k(i)|²|v_k(j)|²`: a dimensionless transport probability
(each row sums to 1), depending on the **operator only**.

## Contents (per target: two PDFs)

- `<TARGET>_detail.pdf` — **connectivity** (cell 14w): best-operator matrix, worst-operator
  matrix, their difference, and the top-5 predicted × active-site sub-block. Active site (blue)
  and allosteric drug pocket (red) are marked on both axes.
- `<TARGET>_14z_walktrace.pdf` — **walk dynamics** (cell 14z): `P(active, t)` over time for
  drug-pocket seeds vs. other seeds, and — in panel B — the **winning score behind Table B.2**
  ranked over the seeds, so the AUC/P@5 on the plot match the table.
- `connectivity_sites.png` — the 4-target summary figure (best/worst + top-5 row).

## Results (= Table B.2; best cell chosen by P@5, AUC breaks ties)

| target (apo → holo, drug) | N | seeding (consensus pockets) | MIN_HOP | seeds (drug) | BEST cell | AUC | P@5 | top-5 (drug in **bold**) | drug/5 | WORST cell | AUC |
|---|---|---|---|---|---|---|---|---|---|---|---|
| KRAS G12C (4LDJ→6OIM, sotorasib) | 170 | top-5, min-rank (druggability + allostery) | 1 | 44 (8) | `H9_bfac` / Green E=median | 0.806 | 0.8 | **99**,**96**,**60**,**54**,72 | 4/5 | `H11_aniso` / residual RAW | 0.184 |
| BCR-ABL1 (1OPL→5MO4, asciminib) | 451 | top-5, min-rank (druggability + allostery) | 2 | 43 (18) | `H6_exp` / residual LOG+dX | 0.796 | 1.0 | **521**,**483**,**525**,**512**,**448** | 5/5 | `H5_gauss` / R=p_peak/p_avg | 0.227 |
| Cardiac myosin (8QYP→8QYR, mavacamten) | 704 | top-10, PASSer allostery rank only | 1 | 151 (14) | `H1_adj` / dX dip depth | 0.733 | 0.4 | **774**,**721**,407,777,604 | 2/5 | `H12_anmS` / −E[D] final | 0.233 |
| HIV-1 RT (1DLO→3V81, nevirapine) | 556 | top-10, rank fusion (druggability + allostery) | 2 | 112 (9) | `H14_anmP` / p_peak | 0.963 | 0.8 | **234**,**101**,102,**227**,**100** | 4/5 | `H9_bfac` / Green E=zero | 0.230 |

Selection is **best-of-221 cells by P@5** (13 Hamiltonians × 17 scores) — a selection ceiling,
not blind performance (Appendix B.3). KRAS's active and drug sites overlap (switch-II); the other
three pockets are distal.

## Reproducibility (important)

fpocket output and the PASSer cache are committed, so a fixed seeding setting reproduces the seed set,
the scores and every number above exactly. What is **not** fixed by the data is the seeding setting
itself: the seed-pocket cut (top-5 vs top-10, min-rank vs rank fusion vs allostery-only) and MIN_HOP are
per-target choices, and changing them moves the winning cell (e.g. top-10 allostery-only seeding for all
four gives KRAS `H9_bfac` 0.785 / 0.6 and BCR-ABL1 `H6_exp` 0.843 / P@5 0.8). Those choices are therefore
declared in the table and counted as part of the best-of-221 selection ceiling. On KRAS the pre-registered
`H_new` cell is the best by AUC (0.809, Green E=λmax) but only P@5 0.6, so the P@5 rule picks `H9_bfac`.
The connectivity **matrix for any fixed operator** is structure+operator-only and reproduces exactly
(`reproduce_connectivity.py`).
