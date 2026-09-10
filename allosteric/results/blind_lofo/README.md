# The blind LOFO model — replicated, and measured against the correct floor

The AUC 0.717 recorded in `full_run_1022/README.md` and `veto_pipeline/PIPELINE_CURRENT.md` was
filed under "Next steps" rather than reported as a result. It is real. It also ties the trivial
geometric baseline exactly.

## Method

A logistic regression over the 221 per-residue score vectors (13 Hamiltonians x 17 scores),
**true leave-one-family-out** (53 folds, the fold's model never sees its own family), scored per
protein and averaged **per family**. No configuration selection anywhere.

## Replication on the distal cohort (91 proteins / 53 families)

| predictor | family-weighted AUC |
|---|---|
| blind LOFO model, C=0.01 | **0.7216** |
| blind LOFO model, C=0.05 / 0.2 / 1.0 | 0.7121 / 0.7058 / 0.7016 |
| best single cell, selected on the same data | 0.5405 |
| fixed pre-registered cell `gauss/sym + neg_dE` | 0.5072 |

Stable across regularisation. The original 0.717 replicates.

## Against the correct floor

The distal subset's floor is **reversed** distance — rank residues by being FAR from the active
site — because the subset is defined as truth >= 3 hops. Same residues, family-paired:

| predictor | family-weighted AUC |
|---|---|
| blind LOFO model | 0.7216 |
| reversed-distance floor | **0.7219** |

Difference **-0.0003**. Beats the floor in 28 of 53 families. Wilcoxon p = 0.899, sign test
p = 0.784.

## On the full cohort (630 proteins / 399 families, MIN_HOP=1)

| predictor | family-weighted AUC |
|---|---|
| blind LOFO model | 0.5847 |
| fixed cell | 0.5854 |

Wilcoxon p = 0.985. The distal gain does not extend to the full set.

## What can be claimed

- **Claimable:** a single blind, cross-validated model over the 221 score vectors reaches
  family-weighted AUC 0.722 on distal targets, against 0.541 for the best single cell chosen on
  the same data. It replaces best-of-221 selection with one fixed predictor.
- **Not claimable:** that it beats geometry. It ties the reversed-distance floor to within
  0.0003, and that floor is partly tautological on a subset defined by hop distance.

Reproduce: `lofo_distal.py`, `lofo_vs_floor.py`, `lofo630.py`.
