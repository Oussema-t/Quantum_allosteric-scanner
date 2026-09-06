# Ablations — where each component belongs (measured, 138 distal proteins, hop 2)

Two questions settled: (1) which selector at stage 1, (2) which veto at stage 3.

## Stage 1 — SELECTION (top-10, drug pocket ranked #1 / top-3, proteins testable)
| selector | pocket set | testable | #1 | top-3 |
|---|---|---|---|---|
| **PASSer only** | PASSer's own pockets | **102** | **32.2%** | **56.8%** |
| PASSer ∩ PocketMiner + apo-ligand protection | PASSer's own | 87 | 31.4% | 60.0% |
| PASSer ∩ PocketMiner (no protection) | PASSer's own | 82 | 14.3% | 49.5% |
| fpocket ∩ PASSer ∩ PocketMiner + protection | fpocket pockets | 84 | 21.2% | 41.5% |
| fpocket ∩ PASSer | fpocket pockets | 94 | 20.6% | 37.4% |
| fpocket only | fpocket pockets | 78 | 11.5% | 26.0% |

**Winner: PASSer only.** Key facts:
- PASSer and fpocket are DIFFERENT pocket finders. PASSer's own pockets rank far better for allostery
  than fpocket pockets ranked by PASSer (32% vs 21% #1) — starting from fpocket geometry loses before
  any walk. fpocket alone is worst (12%).
- Putting PocketMiner (or fpocket) in the SELECTION layer removes proteins up front (102 -> 82-87);
  a fallible ~0.87-AUC predictor must never decide *whether a protein is tested*. The apo-ligand
  protection only recovers PocketMiner to a tie on #1, at the cost of 15 proteins.

## Stage 3 — VETO (after CTQW round 1; families clearing after CTQW round 2, full denominator)
| veto | P@5>=0.8 fam | P@5>=0.6 fam | survivors (>=2 pockets) |
|---|---|---|---|
| none (round 1) | 11 | 31 | 110 |
| **PocketMiner only (protect apo-ligand)** | **19** | **34** | 80 |
| fpocket + PocketMiner (OR-keep druggable) | 14 | 29 | 90 |

**Winner: PocketMiner-only veto.** Adding fpocket druggability as an OR-keep makes the veto GENTLER
(keeps 7.3 vs 5.5 pockets), raising coverage (80 -> 90 survivors) but LOWERING precision (19 -> 14
families). Aggressive pruning is the point — fpocket promotes druggable-but-not-allosteric pockets that
then outrank the true one. Loose bar (P@5>=0.6) barely benefits from any veto (31 no-veto vs 34).

## Score ablation — spectral (energy) variance `dE`  [17 scores]

Added three scores mirroring the `dX` family, from the seed's energy distribution
`|c_k|² = |⟨E_k|seed⟩|²` (**time-independent** — energy is conserved in the closed walk, so no `C_T`):
`dE = sqrt(⟨E²⟩ − ⟨E⟩²)` → `neg_dE`, `residLOG_dE` (= residLOG + focus(dE)), `pavg_over_dE` (= p_avg / dE).
Validated to 0.0 against direct recomputation.

| stage (top-10, hop 2) | 14 scores | +dE (17) | families dE ADDS |
|---|---|---|---|
| round 1, P@5≥0.8 | 11 | 12 | CAS0027 |
| round 1, P@5≥0.6 | 31 | 32 | +1 |
| **round 2 (veto), P@5≥0.8** | **19** | **19** | **none** |
| round 2 (veto), P@5≥0.6 | 34 | 35 | Sulfate adenylyltransferase |

Proteins, round 2: P@5≥0.8 = 40 (unchanged); P@5≥0.6 = 57 → 58.

**Verdict: dE is real but redundant.** On its own it clears 9 families at P@5≥0.8 (round 2) — genuine
signal, spectrally-localized seeds do mark allosteric residues — but it adds **zero** new families to the
best pipeline at the strict bar. `dE` (spread in energy) and `dD` (spread in graph-distance to the active
site) are two windows on the same coherence-vs-diffusion property, so the second is largely redundant.
Kept in the score pool (cheap, parameter-free) but it does not improve the result.

Per-axis spatial variance (`dy`, `dz`) was considered and REJECTED: `dX` is already the full 3D radius of
gyration and is rotation-invariant; per-axis components depend on how the structure is oriented in the
PDB file (frame-dependent) and would not survive review.

## Coverage on the full worklist (1022 proteins), PASSer only top-10
| stage | proteins |
|---|---|
| worklist | 1022 |
| − PASSer returns no pockets for the chain | 78 |
| − fewer than 4 pockets | 6 |
| − drug pocket not in PASSer's top-10 | 90 |
| **TESTABLE** | **848 (83 %) — 548 families** |

Split: distal (hop≥3) 110/138 · near (hop<3) 738/884. Report the two separately — the 738 near proteins
have the allosteric site adjacent to the active site, where proximity alone scores well.
**Blocker for the full run: PocketMiner scores exist only for the 138**; the veto needs them for the rest
(~710 structures, one forward pass each on the native arm64 setup).

## Final pipeline (unchanged by these ablations)
PASSer-only top-10 selection -> CTQW round 1 (13 Ham x 14 scores) -> PocketMiner veto with apo-ligand
protection -> CTQW round 2 -> rank. See PIPELINE_CURRENT.md.

## Files
`cv_k{10,15}_*.json` = combined-veto round-2 output; `veto_combo.json` = the fpocket+PM keep-list.
Selector ablation reproduced by the stage-1 comparison in the session notes (PASSer/fpocket/PocketMiner
minrank on the fpocket dump `fpd_*.json` + `passer_cache.json` + `apo_bound_ligands.json`).
