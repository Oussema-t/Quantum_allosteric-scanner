# AuraQu — Phase-1 supplementary (connectivity detail + walk traces)

Supplementary material for Team AuraQu's Phase-1 concept proposal (Cleveland Clinic problem
statement), referenced from Appendix B of the submission. **Everything here comes from one
consistent pipeline run** (fpocket + PASSer consensus seeding, MIN_HOP 1 for KRAS / 2 for the
distal-pocket targets), so the walk-trace AUC/P@5 equal the Table B.2 numbers by construction.

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

## Results (this run = Table B.2)

| target (apo → holo, drug) | N | MIN_HOP | BEST cell | AUC | P@5 | top-5 (drug in **bold**) | drug/5 | WORST cell | AUC |
|---|---|---|---|---|---|---|---|---|---|
| KRAS G12C (4LDJ→6OIM, sotorasib) | 170 | 1 | `H9_bfac` / Green E=median | 0.785 | 0.6 | **99**,**96**,164,**60**,54 | 3/5 | `H11_aniso` / residual RAW | 0.133 |
| BCR-ABL1 (1OPL→5MO4, asciminib) | 451 | 2 | `H6_exp` / p_avg·dX (SNR) | 0.843 | 0.8 | **448**,**521**,**512**,153,**483** | 4/5 | `H14_anmP` / Green E=zero | 0.212 |
| Cardiac myosin (8QYP→8QYR, mavacamten) | 704 | 2 | `H1_adj` / dX dip depth | 0.691 | 0.4 | **774**,**721**,407,777,604 | 2/5 | `H12_anmS` / −E[D] final | 0.262 |
| HIV-1 RT (1DLO→3V81, nevirapine) | 556 | 2 | `H14_anmP` / p_peak | 0.960 | 0.8 | **234**,**101**,102,**227**,**100** | 4/5 | `H3_normL` / residual RAW+dX | 0.127 |

Selection is **best-of-221 cells by P@5** (13 Hamiltonians × 17 scores) — a selection ceiling,
not blind performance (Appendix B.3). KRAS's active and drug sites overlap (switch-II); the other
three pockets are distal.

## Reproducibility caveat (important)

The exact winning **operator** is not bit-stable across runs: the fpocket/consensus seed set
varies slightly run-to-run, so the best-of-221 cell can shift among near-tied operators (e.g. a
prior run gave KRAS `H_new` 0.809 and BCR-ABL1 P@5 1.0). The numbers above and the plots are all
from **one** run so they agree with each other; they should be read as "reproducible from one
run", not as a stable per-operator ranking. The connectivity **matrix for any fixed operator** is
structure+operator-only and reproduces exactly (`reproduce_connectivity.py`).
