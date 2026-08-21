# TASK-0140 -- chiral circulation observable, real-data run summary

Bonferroni-corrected threshold: 0.05 / 7 = 0.00714

| Target | circ AUC | occ AUC | max floor AUC | circ category | CI overlap | rho(circ,-dist) | rho(occ,-dist) | perm p-value |
|---|---|---|---|---|---|---|---|---|
| KRAS_G12C | 0.702 | 0.653 | 0.546 | NO_FAILURE_DETECTED | True | -0.259 | -0.700 | 0.0030 |
| BCR_ABL1 | 0.419 | 0.560 | 0.619 | BEATS_CHANCE_NOT_FLOOR | True | -0.479 | -0.738 | 0.5005 |
| CARDIAC_MYOSIN | 0.395 | 0.531 | 0.583 | BEATS_CHANCE_NOT_FLOOR | True | -0.223 | -0.712 | 0.6566 |
| PTP1B | 0.640 | 0.495 | 0.492 | NO_FAILURE_DETECTED | True | -0.286 | -0.695 | 0.0020 |
| GLUCOKINASE | 0.677 | 0.657 | 0.863 | BEATS_CHANCE_NOT_FLOOR | True | -0.392 | -0.594 | 0.0120 |
| CASPASE1 | 0.639 | 0.676 | 0.919 | BEATS_CHANCE_NOT_FLOOR | True | -0.374 | -0.581 | 0.4961 |
| CASPASE7 | 0.530 | 0.600 | 0.758 | NO_SIGNAL_IN_APO | True | -0.260 | -0.434 | 0.8434 |

**FAIL**: no target clears the floor with non-overlapping CIs and Bonferroni-significant permutation null (0/7 candidate cells before the CI+null requirement).
