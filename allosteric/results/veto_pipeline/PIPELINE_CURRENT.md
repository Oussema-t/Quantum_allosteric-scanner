# CURRENT BEST PIPELINE — allosteric-pocket prediction (as of 2026-09-06)

Baseline to improve on. Everything here is measured; caveats are stated with the numbers.

## Stages
1. **Pocket selection — PASSer only.** PASSer's own pocket residue lists, ranked by allostery,
   **top-10** (top-15 also valid: +coverage, −precision). fpocket / PocketMiner as a *selection
   gate* only lose coverage, so they are NOT used to select.
   → after PASSer: **~110 proteins testable** (top-10) / 115 (top-15) — the drug pocket is on the
     candidate list. (NOT 90; the 90/80 is the post-veto survivor count.)
2. Drop the active-site pocket; exclude seeds < `MIN_HOP=2` hops from the active site. hop 2 > hop 1.
3. **CTQW round 1** — walk residue-by-residue to the active site, **13 Hamiltonians × 14 scores**.
   Each (Hamiltonian, score) cell is evaluated separately; a protein "wins" if ≥1 cell clears the bar
   (this best-of-182 selection is the main weakness — see §Improve).
4. **PocketMiner veto** — from the ranked pockets, drop those in the worse half by predicted
   accessibility, **except** any pocket whose residues contact a ligand already bound in the apo file
   (demonstrably open — `apo_bound_ligands.json`). Veto drops POCKETS; a protein whose drug pocket is
   vetoed counts as a FAILURE, it is not removed from the denominator.
   → after veto: ~80 (top-10) / ~90 (top-15) proteins still have ≥2 pockets.
5. **CTQW round 2** — re-run the walk on the surviving pockets, all Hamiltonians × scores; rank pockets
   by their best residue.

## Result (top-10, veto, hop 2, all 14 scores; full honest denominator = 110 proteins / 65 families)
| bar | proteins | families |
|---|---|---|
| AUC ≥ 0.6 & **P@5 ≥ 0.8** | 40 | **19** |
| AUC ≥ 0.6 & **P@5 ≥ 0.6** | 57 | **34** |

Raw counts = best of 182 cells per protein. **Chance-corrected (family-level null): ~+4 families over
chance at P@5 ≥ 0.8 (p ≈ 0.06)** → the defensible signal is ~15 genuine families.

## The 14 scores
8 base: `p_avg` (T→∞ closed form), `p_peak`, `R`, `residLOG`, `residRAW`, Green |G|² ×3.
6 diagnostic (ported verbatim from notebook cell 43, verified to 0.0): `neg_dD_mean`, `neg_ED_final`,
`residLOG_dX`, `residRAW_dX`, `pavg_over_dX`, `QMI`. The new scores ~double the families cleared.

## Which Hamiltonian per family (P@5 ≥ 0.8) — `per_family_winners.csv`
- `H_new` wins the most families (5): androgen receptor, serum albumin, both pyruvate kinases, O32553.
- `binary/adj` (+ Green λmax) wins 4: the small CryptoBench proteins (P33284, P00489, A0QUZ2, Q9H7Z6).
- `binary/comb` + `neg_dD_mean` wins CAS0002 (large family, robust — all 13 operators clear it).
- 13 of 19 families are cleared by ≥2 different Hamiltonians (robust); 6 by only one.
- `H_new` reproduces only `exp/sym` & `binary/sym` (λ=0); the `adj`/`comb`/gauss/harm winners are
  outside its span → expressing them needs a `weight × norm` switch (`build_H_general`).

## To improve (next)
- **Regression instead of best-of-182.** A leave-one-FAMILY-out logistic regression on the 182 per-residue
  scores already beats every single cell (AUC 0.717 vs 0.589; 7 families P@5≥0.8 predicted BLIND). This
  removes the cherry-picking and is the honest headline method. Next: tune regularization with nested CV;
  L1 to find the minimal operator set; compare to PASSer-alone at pocket level.
- Split the benchmark: ~50% of these "apo" structures already have the effector bound (protection list
  partly leaks) — report the truly-empty-site subset separately.
- Extend to the full 1022 (needs PocketMiner on the other ~884 structures first); stratify by hop distance.
- Pin `C_T` for time-grid scores (`R`, `neg_dD_mean`, …); plateau at C_T ≥ 1.

## Reproduce
`pocketsweep.py` runs S1–S5. Round 1: `SELECTOR=passer_only N_POCKETS=10 MIN_HOP=2`.
Round 2: add `VETO_FILE=veto_keep.json`. Data: `s14_r{1,2}_k10_h2_*.json` (per-protein cells + rank
vectors), `veto_keep.json`, `apo_bound_ligands.json`. Cohort: 138 distal proteins.
