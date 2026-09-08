# Centrality ablation — is the quantum layer load-bearing?

The ablation made mandatory by Mohtashim, Sajjan & Kais, *J Am Chem Soc* 148(27):29206-29219
(2026), DOI 10.1021/jacs.6c08053, who report CTQW centrality correlating with classical
eigenvector centrality at rho~0.95 on residue interaction networks.

Our CTQW (gauss/sym + neg_dE, MIN_HOP=1) vs five FREE classical measures, scored on the
identical residues with the identical labels, on our own benchmark.

**Proteins scored: 630** (399 families)

## Does the CTQW beat the free classical baselines?

| measure | mean AUC | CTQW wins | verdict |
|---|---|---|---|
| **CTQW (quantum)** | **0.600** | — | — |
| eigenvector | 0.529 | 362/630 (57%) | CTQW ahead |
| closeness | 0.576 | 279/630 (44%) | CTQW ahead |
| betweenness | 0.575 | 318/630 (50%) | CTQW ahead |
| degree | 0.533 | 408/630 (65%) | CTQW ahead |
| gnm_lowmode | 0.430 | 419/630 (67%) | CTQW ahead |

## How similar is the CTQW to each classical measure?

| measure | Spearman rho vs CTQW |
|---|---|
| eigenvector | 0.689 |
| closeness | 0.694 |
| betweenness | 0.473 |
| degree | 0.599 |
| gnm_lowmode | -0.802 |

## Verdict

JACS reports rho~0.95 between CTQW centrality and eigenvector centrality.
**We measure rho = 0.689.**

**The JACS correlation does NOT replicate here (rho = 0.689).** Our construction differs,
most likely because we seed at the active site and score transport to it, which they do not.
That difference is the defensible novelty and should be stated explicitly.

## Distal subset

- **distal** (n=91): CTQW 0.617 vs eigenvector 0.357 -> CTQW ahead
- **near** (n=539): CTQW 0.597 vs eigenvector 0.558 -> CTQW ahead
