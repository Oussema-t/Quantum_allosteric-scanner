# Two further comparisons: site level, and without the pipeline funnel

Same 630 proteins / 399 families as everything else in this folder. Zero errors in both runs.

## 1. SITE LEVEL — ranking the pocket, not the residues

The pipeline's own rule: a pocket scores as its best residue; rank the pockets; where does the true
drug pocket land? 626 proteins had >1 candidate pocket. Mean 3.9 candidate pockets per protein.

| algorithm | top-1 | top-3 | mean rank |
|---|---|---|---|
| proximity (closer) | **38%** | 81% | 2.21 |
| **Seeded-CTQW-pipeline** | 37% | **86%** | **2.12** |
| closeness (unseeded) | 36% | 81% | 2.23 |
| weighted communicability | 30% | 78% | 2.37 |
| commute time | 29% | 79% | 2.37 |
| eigenvector (unseeded) | 29% | 79% | 2.35 |
| heat kernel (the twin) | 28% | 81% | 2.36 |

The CTQW is best on **top-3 (86%)** and best on **mean rank**, and second on top-1 by one point —
about 6 proteins out of 626, which is noise. With only ~3.9 pockets to choose from, random guessing
gives ~26%, so **every method is barely above chance at picking the single right site.**

## 2. UNCONSTRAINED — no PASSer, no MIN_HOP filter, no veto

Every algorithm ranks ALL residues of the protein (active site excluded). This asks whether the
result comes from the ranking method or from the pipeline's classical selection stages.

**303 candidate residues per protein instead of ~40. Base rate 0.070 instead of 0.33.**

| algorithm | mean AUC | P@5>=0.8 prot/fam | P@5>=0.6 prot/fam |
|---|---|---|---|
| closeness centrality | **0.626** | 6 / 6 | 30 / 30 |
| proximity (closer) | 0.595 | 3 / 3 | 18 / 18 |
| GNM cross-correlation | 0.533 | 9 / 9 | 25 / 25 |
| degree | 0.526 | 0 / 0 | 5 / 5 |
| eigenvector centrality | 0.520 | 2 / 2 | 4 / 4 |
| heat kernel e^{-Lt} | 0.490 | 1 / 1 | 8 / 8 |

### What the funnel is worth

| algorithm | AUC unconstrained | AUC with funnel | change |
|---|---|---|---|
| closeness centrality | 0.626 | 0.576 | **-0.050** |
| proximity (closer) | 0.595 | 0.574 | -0.021 |
| GNM cross-correlation | 0.533 | 0.540 | +0.007 |
| degree | 0.526 | 0.533 | +0.007 |
| eigenvector centrality | 0.520 | 0.529 | +0.008 |
| heat kernel e^{-Lt} | 0.490 | 0.512 | +0.023 |
| Seeded-CTQW-pipeline | n/a | 0.600 | — |

## The three conclusions

**1. The P@5 numbers collapse without the funnel.** Closeness drops from 48 proteins to 6, GNM from
23 to 9. On the full protein essentially nothing puts drug residues in its top five. That is the
honest difficulty of the real problem.

**2. The pipeline's classical selection is doing an enormous amount of work.** PASSer top-10 plus
the PocketMiner veto cuts 303 candidates to 40 and raises the base rate fivefold, from 0.070 to
0.33. Every strong P@5 number in this project — ours and every baseline's — depends on it. PASSer,
fpocket and PocketMiner are all CLASSICAL tools; the quantum walk only ever ranks residues the
classical stages already selected.

**3. Closeness centrality is HURT by the funnel** (0.626 -> 0.576) — the only method that does
better without it. The shortlist is tuned for what the walk needs, not for what closeness needs.

### Consequence for what can be claimed

Not "quantum finds allosteric sites". The defensible statement is: *a classical selection stage
narrows 303 residues to 40 and raises the base rate fivefold; within that shortlist the
active-site-seeded quantum walk ranks residues better than its exact classical diffusion twin
(AUC 0.600 vs 0.512, p=2.3e-12) and delivers the best top-3 pocket accuracy (86%) — while plain
closeness centrality still beats it at family-level P@5, and plain proximity ties it at top-1.*
