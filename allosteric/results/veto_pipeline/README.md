# Two-round veto pipeline — PASSer seeding + CTQW + PocketMiner veto

Predict the allosteric pocket by seeding a continuous-time quantum walk from PASSer's candidate
pockets, then vetoing pockets a cryptic-site predictor calls closed, then walking again.

## Pipeline
1. **PASSer only** ranks the pockets (its own residue lists); keep top-10 (or top-15). Best selector
   measured — drug pocket on the list in ~90% of proteins; adding fpocket/PocketMiner as a *gate* only
   loses coverage.
2. Drop the active-site pocket; exclude seeds < `MIN_HOP=2` from the active site.
3. **CTQW round 1** — residue-by-residue to the active site, **13 Hamiltonians × 14 scores**.
4. **Veto** — drop pockets in the worse half by PocketMiner accessibility, **except** pockets whose
   residues contact a ligand already bound in the apo file (those are demonstrably open —
   `apo_bound_ligands.json`).
5. **CTQW round 2** — re-run the walk on the surviving pockets, all Hamiltonians × scores.
6. Rank pockets by their best residue → best allosteric pockets.

## Scores (14)
8 base: `p_avg` (T→∞ closed form), `p_peak`, `R`, `residLOG`, `residRAW`, Green `|G|²` ×3.
6 section-14 diagnostics (ported verbatim from cell 43, verified to 0.0):
`neg_dD_mean`, `neg_ED_final` (walker distance-distribution moments), `residLOG_dX`, `residRAW_dX`,
`pavg_over_dX` (spatial-spread corrected), `QMI` (single-excitation mutual information).

## Result — distinct FAMILIES clearing AUC≥0.6 & P@5≥threshold (full denominator; a family the veto
over-prunes counts as a failure, not a dropout)

| config | P@5≥0.8 | P@5≥0.6 | families tested |
|---|---|---|---|
| top-15, no veto | 8 | 28 | 68 |
| **top-15, veto** | **16** | **32** | 68 |
| top-10, no veto | 11 | 31 | 65 |
| **top-10, veto** | **19** | **34** | 65 |

Both the new scores and the veto roughly double the families cleared. **Chance-corrected** (family-level
label-permutation null): the excess is ~**+4 families** over chance at P@5≥0.8 (p≈0.06) — real but modest;
the defensible reading is ~15 genuine families, not the raw count.

## Which Hamiltonian per family (top-10, veto, P@5≥0.8) — `per_family_winners.csv`
No universal operator; three consistent groups:
- `binary/comb` + `neg_dD_mean` → CAS0002 (large family)
- **`H_new`** → the regulated enzymes: androgen receptor, serum albumin, both pyruvate kinases, O32553
- `binary/adj` + `Green(λmax)` → the small CryptoBench proteins (P33284, P00489, A0QUZ2, Q9H7Z6)

## Caveats
- `H_new` reproduces only `exp/sym` and `binary/sym` (λ=0); `binary/comb`, `binary/adj`, `gauss`/`harm`
  kernels are outside its span — expressing the winners needs a `weight × norm` switch (`build_H_general`).
- The apo-ligand protection partly leaks: ~50% of these "apo" structures already have the effector bound.
  On truly empty sites the veto gain will be smaller.
- Scores using the time grid (`R`, `p_peak`, `neg_dD_mean`, …) depend on `C_T`; the C_T sweep put the
  plateau at `C_T ≥ 1` (small t = proximity, worse). `p_avg` is the parameter-free T→∞ closed form.
- Family-level aggregation is mandatory: CAS0002 is 28 structures of one protein.

## Files
`pocketsweep.py` (S1–S5; `SELECTOR=passer_only`, `VETO_FILE=veto_keep.json` for round 2),
`veto_keep.json` (surviving pocket ids per protein), `apo_bound_ligands.json` (protection list),
`s14_r{1,2}_k10_h2_*.json` (per-protein cells + rank vectors, round 1 and round 2),
`benchmark_summary.json`, `per_family_winners.csv`, `PIPELINE_DESIGN.md`.
