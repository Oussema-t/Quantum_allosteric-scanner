# Full-run benchmark — all 1022 proteins, best pipeline + CTQW MIN_HOP sweep

Best pipeline: **PASSer-only top-10 → CTQW round 1 (13 Hamiltonians × 17 scores) → PocketMiner veto
(apo-ligand protected) → CTQW round 2 → rank pockets.** Run over the whole 1022-protein worklist, at
four CTQW MIN_HOP seed-filter settings. PocketMiner ran on a Linux HPC node (TF 2.13, py3.10) for all
proteins; veto lists in `veto_full.json`.

## Files
| file | contents |
|---|---|
| `r1_minhopH.json.gz` | CTQW **round 1** (all PASSer pockets), MIN_HOP=H∈{1,2,3,4}. Per protein: `cells` (AUC,P@5 for each of 221 Ham×score), `ranks` (per-seed rank vector per cell), `y` (per-seed truth), `seed_resnum`, `seed_pocket`, `pockets`, `cluster` |
| `r2_minhopH.json.gz` | CTQW **round 2** (veto survivors), same fields — the pipeline output |
| `veto_full.json` | pockets surviving the PocketMiner veto per protein (apo-ligand protected) |
| `classical.json` | classical baselines per protein (proximity, degree, size, PASSer rank, fpocket) |
| `per_family_full_minhop2.csv` | per family: every winning Hamiltonian + score, family size (MIN_HOP=2) |
| `load_features.py` | loads the 221-feature per-residue matrix + family groups for the regression |
| `pocketsweep.py` `pm_hpc.py` `build_veto_hpc.py` `classical.py` | the pipeline / PocketMiner / veto / baseline code |

## Results — families / proteins clearing AUC≥0.6 & P@5≥threshold (round 2 = best pipeline)

| CTQW MIN_HOP | testable (prot/fam) | P@5≥0.8 (prot/fam) | P@5≥0.6 (prot/fam) |
|---|---|---|---|
| 1 | 829 / 529 | 183 / 106 | 313 / 202 |
| 2 | 643 / 383 | 132 / 69 | 218 / 136 |
| 3 | 348 / 211 | 71 / 44 | 119 / 74 |
| 4 | 121 / 84 | 40 / 19 | 52 / 28 |
| **union (best MIN_HOP per protein)** | 829 / 529 | **226 / 131** | 347 / 216 |

Higher MIN_HOP → fewer testable, because the filter excludes seeds < H hops from the active site, and for
a **near** pocket that deletes the pocket's own truth residues (at MIN_HOP=3, 572 proteins lose their
truth entirely). So the seed filter must be matched to the pocket's distance:

| protein distance | best MIN_HOP | families P@5≥0.8 |
|---|---|---|
| near (truth 0–2 hops) | **1** | 92 (of 469) |
| distal (truth ≥3 hops) | **3** | 25 (of 66) |

Principled per-distance rule (chosen in advance, not per-protein cherry-pick): ~117 families. The union
(131) is an optimistic upper bound (best-of-4-settings selection).

## Classical comparison (families, P@5≥0.8, same pockets/metric) — MIN_HOP=2
| method | ALL | distal | near |
|---|---|---|---|
| **CTQW (quantum walk)** | **69** | **19** | **50** |
| proximity (−hop) | 25 | 1 | 24 |
| PASSer rank | 17 | 2 | 15 |
| pocket size | 14 | 1 | 13 |
| fpocket druggability | 17 | 2 | 15 |
| degree | 11 | 2 | 9 |

~~The walk beats every classical descriptor, decisively on distal (19 vs 1)~~ **[CORRECTED 2026-09-11: scored against the one-directional proximity floor; the distal subset's real floor is REVERSED distance (0.773 family-weighted), which the walk loses to — see proximity_floor/README.md, commit f23fae6. Do not quote.]** — where proximity/size/
centrality collapse. That distal margin is the quantum-connectivity contribution.

## Honest caveats
- Raw counts are best-of-221-cells. Chance-corrected (family-level label-permutation null, MIN_HOP=2):
  P@5≥0.8 = 69 observed vs ~51 chance → **+18 real** (distal +3.4, near +14).
- Family-level counting is mandatory: e.g. CAS0061 = 33 structures, CAS0002 = 28 — one protein each.
- `H_new` is the most frequent winning operator (20/69 families) and the most frequent SOLE winner;
  Green(λmax) and the dispersion/energy scores (neg_dD_mean, neg_dE, residLOG_dX, QMI) are the winning
  scores in ~half the families. 50/69 families are cleared by ≥2 Hamiltonians (robust).
- ~50% of "apo" structures already have the effector bound (protection partly leaks); the honest test
  is the distal, truly-empty subset.

## Next: regression
`load_features.py` gives the 221-feature per-residue matrix + family groups. A leave-one-FAMILY-out
logistic regression on these already beat every single cell blind on the 138 (AUC 0.717 vs 0.589);
with 383–529 families here the cross-validation is far more robust. That replaces best-of-221 selection
with one fixed, validated predictor.
