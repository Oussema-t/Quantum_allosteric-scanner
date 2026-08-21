# TASK-0142 (H2 half) -- persistent-void real-target run summary

Bonferroni threshold: 0.05 / 3 = 0.01667
Noise floor (synthetic solid-ball negative control): top H2 persistence > 2.5

| Target | top H2 persist. | void detected | AUC (gated) | AUC (ungated) | max floor AUC | patch-null pctile | patch-null p |
|---|---|---|---|---|---|---|---|
| KRAS_G12C | 0.669 | False | 0.500 (NO_SIGNAL_IN_APO) | 0.581 | 0.546 | 77.1 | 0.2290 |
| BCR_ABL1 | 2.404 | False | 0.500 (NO_SIGNAL_IN_APO) | 0.702 | 0.619 | 46.3 | 0.5370 |
| CARDIAC_MYOSIN | 2.829 | True | 0.192 (BEATS_CHANCE_NOT_FLOOR) | 0.192 | 0.583 | 0.0 | 1.0000 |

**FAIL** -- CARDIAC_MYOSIN shows a top H2 persistence above the noise floor, but does not clear the floor/null bar for a real PASS.
