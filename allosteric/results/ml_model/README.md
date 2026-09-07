# AI models for the best pipeline — predict the CTQW configuration from protein topology

**Goal:** given only a protein's topology, predict which configuration to run the CTQW with
(MIN_HOP, Hamiltonian, score) — so the best pipeline can be applied to a new protein without
trying all 884 configurations.

**Protein set (both models, identical):** 597 proteins / 380 families = round-2 testable set
(after the PocketMiner veto, i.e. the best-pipeline output), with topology features available.
**Input (both models):** 9 topology features — n_residues, n_edges, mean_degree, degree_var,
degree_cv, clustering_coefficient, graph_diameter, algebraic_connectivity, spectral_radius.
**Validation:** leave-one-FAMILY-out GroupKFold(5). Every family held out once; each protein is
scored by a model that never saw its family. Scored by the AUC / P@5 you actually obtain by
RUNNING the predicted configuration on held-out proteins.

## Model 1 — topology → MIN_HOP  (`RandomForestClassifier`)
| metric | value |
|---|---|
| near-vs-distal AUC (sets MIN_HOP 1 vs 3) | **0.793** |
| exact best-MIN_HOP accuracy | 0.394 (commonest-class baseline 0.412) |
| best-cell AUC running at the PREDICTED MIN_HOP | **0.924** |
| best-cell AUC always MIN_HOP=1 / 2 / 3 | 0.901 / 0.915 (n=435) / 0.937 (n=244) |
| oracle (true best MIN_HOP) | 0.964 |

Model 1 predicts near-vs-distal well (0.79) and running at its predicted MIN_HOP beats always
using MIN_HOP=1 on the full set (0.924 vs 0.901). It cannot pick the exact best MIN_HOP among
four (accuracy at baseline) — the useful signal is the coarse near/distal split.

## Model 2 — topology → (Hamiltonian, score)  (`RandomForestRegressor`, 221 outputs)
Regresses the AUC of every one of the 221 Hamiltonian×score cells from topology; the predicted
best cell is then run. Hamiltonian and score are predicted **jointly** because they interact
(rank-1 explains 48% of the 13×17 AUC matrix; main effects explain 1% of variance).

| cell chosen by | mean AUC | fam P@5≥0.8 | fam P@5≥0.6 |
|---|---|---|---|
| random cell | 0.534 | 5 | 0 |
| one FIXED cell for all (hnew/full + Green λmax) | **0.630** | **15** | **44** |
| PREDICTED from topology (Model 2) | 0.625 | 13 | 43 |
| oracle (true best cell per protein) | 0.964 | 68 | 132 |

**Negative result, stated plainly:** Model 2 does NOT beat simply using one fixed cell
(0.625 vs 0.630 AUC; 13 vs 15 families). Topology carries only weak information about which
Hamiltonian×score wins (earlier tests: exact-winner accuracy 0.107 vs 0.137 baseline; predicted-
vs-actual cell-AUC Spearman ≈ 0.23). The gap to the oracle (0.964) is large but is not reachable
from global topology alone.

## Recommendation for the pipeline
Use Model 1 to set MIN_HOP (near→1, distal→3), then run the single fixed cell
**H_new (L_norm exp + site potential) + Green's function at λmax** — it is the best fixed choice
and Model 2 cannot improve on it. Report the oracle numbers (best-of-221) as selection, not as
performance.

## Files
- `config_models.py` — builds, cross-validates, and saves both models (reproduces every number above)
- `config_models.joblib` — both models fit on all 597 proteins + the CV numbers
- `config_predictions.csv` — per-protein held-out predictions (pred MIN_HOP, pred cell, AUC obtained, oracle)
- `prepare_data.py`, `model2_data.npz`, `best_per_protein.csv` — data preparation
- `hpc_search.py`, `search_*.json` — a separate 440-config search for a residue-level allosteric
  classifier (a different model, not the configuration predictor; kept for reference: best CV AUC
  0.654, 35 families P@5≥0.8, cells+stats+topo RandomForest)
