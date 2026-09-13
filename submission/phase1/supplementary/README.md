# Per-target connectivity detail (supplementary to the Phase-1 submission)

One PDF per scoreable target, referenced from Appendix B of the submission. Each is
**consistent with Table B.2** and **reproducible from the committed matrices** in
`../../../allosteric/results/connectivity/` (regenerated from those CSVs, not from a
notebook run — the raw notebook runs pick different best/worst cells between runs and
would contradict Table B.2).

## What each `*_detail.pdf` shows (four panels + a results line)

1. **BEST** operator connectivity matrix `C_ij` (full N×N), active site (blue) and the
   allosteric drug pocket (red) marked on both axes; purple = shared.
2. **WORST** operator connectivity matrix, same marking.
3. **BEST − WORST** difference (red = the best operator transports more).
4. **Top-5 predicted × active-site** sub-block (rows = the five predicted residues,
   **red label = residue in the drug pocket**; columns = active-site residues).

`C_ij` is the average-mixing matrix — a **dimensionless transport probability** (each row
sums to 1), operator-only (seeding- and scoring-independent). Ångström enters only the
10 Å contact-graph cutoff, not the matrix values.

## Recorded results (identical to Table B.2)

| target (apo → holo, drug) | N | BEST cell | AUC | P@5 | top-5 predicted (drug in **bold**) | drug/5 | WORST cell | AUC |
|---|---|---|---|---|---|---|---|---|
| KRAS G12C (4LDJ → 6OIM, sotorasib) | 170 | `H_new` / Green resolvent | 0.809 | 0.6 | **60**, 37, **96**, **61**, 7 | 3/5 | `H11_aniso` / residual RAW | 0.184 |
| BCR-ABL1 (1OPL → 5MO4, asciminib) | 451 | `H6_exp` / residual LOG + dX | 0.796 | 1.0 | **521**, **483**, **525**, **512**, **448** | 5/5 | `H5_gauss` / R = p_peak/p_avg | 0.227 |
| Cardiac myosin (8QYP → 8QYR, mavacamten) | 704 | `H1_adj` / dX dip depth | 0.733 | 0.4 | **774**, **721**, 407, 777, 604 | 2/5 | `H12_anmS` / −E[D] final | 0.233 |
| HIV-1 RT (1DLO → 3V81, nevirapine) | 556 | `H14_anmP` / p_peak | 0.963 | 0.8 | **234**, **101**, 102, **227**, **100** | 4/5 | `H9_bfac` (matrix); score-worst `H14_anmP`/Green 0.196 | — |

Active site vs allosteric pocket: KRAS overlaps (switch-II, 4 shared residues); BCR-ABL1
(myristoyl), cardiac (converter, ~30 Å from the P-loop) and HIV-1 RT (NNRTI pocket) are distal.

Selection is **best-of-221 cells by P@5** (13 Hamiltonians × 17 scores), seeded by the
consensus of fpocket druggability and PASSer allostery (top-10; the distal filter is MIN_HOP 1 for KRAS, whose switch-II pocket abuts the active site, and MIN_HOP 2 for BCR-ABL1, cardiac myosin and HIV-1 RT). These are
selection ceilings, not blind performance (see Appendix B.3). **Cardiac's best-operator
label is a near-tie that varies run-to-run** (the 15-residue pocket in 704 residues makes
AUC-based operator selection unstable); what is stable is that the consensus seeding
reproducibly recovers the mavacamten pocket and the top-5 reaches P@5 0.4.

## Not included here

The walk **time-trace** diagnostics (notebook cell 14z: `P(active, t)` and the per-seed
`p_avg` distribution) depend on the specific run's seed set, so they cannot be regenerated
from the committed matrices alone and are omitted to avoid a number that disagrees with
Table B.2. They can be added from a single clean run of all four targets on request.

Source: `allosteric/results/connectivity/*.csv.gz` (matrices) and `*_top5xactive_*.csv`
(sub-blocks); regeneration script kept with the build tooling.
