# Pipeline design — PASSer-seeded CTQW with a druggability / openability veto

Team AuraQu · specified by O. Turki, written up 2026-09-05. This is the design as *intended*; every
knob is listed with its current default and marked as a choice, not a fact.

## The question
Can a continuous-time quantum walk (CTQW), seeded from the pockets a pocket-finder proposes, put the
**drug (allosteric) pocket at rank 1** — and if the walk puts a non-druggable or closed pocket on top,
does **vetoing** such pockets with fpocket / PocketMiner let the drug pocket rise?

## The pipeline

```
                 apo structure (one chain)
                          │
   ┌──────────────────────▼──────────────────────┐
   │ S1  POCKET SELECTION                        │  fpocket defines pocket geometry (residue sets)
   │     PASSer ranks them (Jaccard ≥ 0.5 match) │  keep PASSer top-15, drop the active-site pocket
   └──────────────────────┬──────────────────────┘  measured coverage: drug pocket present in 90 % of proteins
                          │  ~13 pockets, ~100 seed residues
   ┌──────────────────────▼──────────────────────┐
   │ S2  CTQW, RESIDUE BY RESIDUE                │  seed = each pocket residue (MIN_HOP ∈ {1,2} from active site)
   │     13 Hamiltonians × 8 scores              │  target = active site; scores per residue
   │     → residue AUC, P@5, permutation null    │  report AUC ≥ 0.6 & P@5 ≥ 0.8 / ≥ 0.6, per protein
   └──────────────────────┬──────────────────────┘
                          │  ranked residues (per Hamiltonian × score)
   ┌──────────────────────▼──────────────────────┐
   │ S3  POCKET RANK FROM RESIDUES               │  pocket rank = rank of its BEST residue (residue-first;
   │     is the drug pocket #1?                  │  no averaging over members — averaging is size-biased)
   └──────────────────────┬──────────────────────┘
                          │  ranked pockets
   ┌──────────────────────▼──────────────────────┐
   │ S4  VETO                                    │  walk down the CTQW pocket list, DROP a pocket if
   │     not druggable (fpocket)  → drop         │    fpocket rank is in the worse half            [knob]
   │     likely closed (PocketMiner) → drop      │    pocket-mean PocketMiner score in the worse half [knob]
   │     prediction = first surviving pocket     │  variants: fpocket only · PocketMiner only · both
   └──────────────────────┬──────────────────────┘
                          │
   ┌──────────────────────▼──────────────────────┐
   │ S5  EVALUATION                              │  drug pocket #1 rate: before veto, after each veto
   │     vs three references                     │  (a) chance = 1/n_pockets
   │                                             │  (b) RANDOM residue order through S3–S4 (same veto)
   │                                             │  (c) PASSer #1 alone, no walk
   └─────────────────────────────────────────────┘
```

## Definitions (fixed for the whole study)
| item | definition |
|---|---|
| cohort | 138 `is_distal` proteins (truth pocket ≥ 3 hops from the active site); 1022 later |
| pocket | an fpocket cavity (residue set), chain-restricted |
| drug pocket (truth) | the selected pocket with the most drug-contact / curated-allosteric residues, accepted if ≥ 25 % of its residues are truth (`argmax` rule); strict alternative `drug_frac > 0.5` |
| seed residues | union of residues of the selected pockets, excluding active-site residues and residues < `MIN_HOP` from them |
| Hamiltonians (13) | weight ∈ {binary, exp, gauss, harm} × norm ∈ {adj, comb, sym} + `H_new` (verified port of cell 39) |
| scores (8) | `p_avg` (T→∞ closed form), `p_peak`, `R`, `residLOG`, `residRAW`, Green |G|² at (0,0.05), (0,0.01), (λmax,0.05) |
| residue metrics | AUC and P@5 of the residue ranking vs truth residues; label-permutation null over the 104 cells |
| pocket metric | drug pocket at rank 1 (also rank ≤ 3); averaged over the 104 cells, and "majority of cells" per protein |

## Knobs (choices, with defaults)
| knob | default | alternatives worth testing |
|---|---|---|
| pocket selector | PASSer top-15 | PASSer top-10/20; PASSer ∩ PocketMiner for cryptic sets |
| `MIN_HOP` | 2 (report 1 too) | — |
| pocket rank from residues | best residue | majority pocket of top-5 residues |
| fpocket veto | drop worse half by fpocket rank | drop worst third; absolute druggability < 0.05 |
| PocketMiner veto | drop worse half by pocket-mean score | drop "no-open" state only (percentile vs random pockets, as in 13z) |
| walk time | `p_avg` closed form (no t); `p_peak`/`R` on t ∈ [0, 1/gap] | — (small C_T measured worse) |

## What counts as success (decided before looking)
1. S2: proteins with AUC ≥ 0.6 and P@5 ≥ 0.8 that also beat their permutation null.
2. S4: drug-pocket-#1 rate after veto **above** (a) chance **and** (b) the random-residue + same-veto null.
   Beating (a) but not (b) means the veto works and the walk does not.
3. A protein "works" if the drug pocket is #1 in the majority of the 104 cells after veto.

## Known limits to state with every result
- The veto can delete the drug pocket itself; report the survival fraction (the veto's own ceiling).
- Chance depends on pocket count (1/13 for top-15 vs 1/9 for top-10): compare each run to its own chance.
- 87 % of the benchmark is not distal; on the 1022 the results must be stratified by hop distance.
- Family pseudo-replication (CAS0002 = 28 structures): aggregate by family as well as by protein.

## Files
`pocketsweep.py` (S1–S2, `SELECTOR=passer N_POCKETS=15`), saved rank vectors → S3–S5 offline
(`refilter.py` re-rank variant — *not* this design; veto analysis in `veto_pipeline.py`).
