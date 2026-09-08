# The Seeded-CTQW-pipeline vs 13 classical baselines

**Identical conditions throughout**: MIN_HOP=1, the same 630 proteins / 399 families, the same
candidate residues, the same truth labels (residues within 4.5 A of the drug in the holo
structure). The CTQW ranks come from cache (`r2_minhop1.json.gz`), so they are the same numbers
used everywhere else in this repo; only the classical baselines were computed here.

Truth = drug-binding residues. P@5 >= 0.8 means 4 of the top 5 ranked residues genuinely
contact the drug. Counting criterion: P@5 threshold AND AUC >= 0.6, applied to every algorithm.

| algorithm | seeded? | mean AUC | P@5>=0.8 prot/**fam** | P@5>=0.6 prot/**fam** |
|---|---|---|---|---|
| **Seeded-CTQW-pipeline** | seeded | 0.600 | 69 / **20** | 101 / **45** |
| heat kernel e^{-Lt} — *the exact classical twin* | seeded | 0.512 | 23 / **17** | 44 / **34** |
| commute time (v2 notebook) | seeded | 0.549 | 39 / **22** | 69 / **44** |
| weighted communicability (v2, Estrada & Hatano) | seeded | 0.543 | 48 / **23** | 70 / **42** |
| GNM cross-correlation (v2, Bahar) | seeded | 0.540 | 16 / **12** | 49 / **35** |
| GNM perturbation response (v2, Atilgan) | seeded | 0.531 | 41 / **15** | 69 / **33** |
| communicability e^A | seeded | 0.543 | 48 / **23** | 70 / **42** |
| personalised PageRank | seeded | 0.565 | 29 / **19** | 58 / **42** |
| proximity (closer = allosteric) | seeded | 0.574 | 30 / **15** | 63 / **44** |
| proximity (farther = allosteric) | seeded | 0.426 | 37 / **12** | 45 / **19** |
| eigenvector centrality | UNseeded | 0.529 | 61 / **25** | 81 / **44** |
| closeness centrality | UNseeded | 0.576 | 48 / **29** | 83 / **55** |
| degree | UNseeded | 0.533 | 41 / **12** | 78 / **28** |
| GNM low-mode participation | UNseeded | 0.430 | 2 / **2** | 10 / **10** |

## Where the CTQW wins

- **Every per-protein count.** 69 at P@5>=0.8 vs eigenvector's 61 and the twin's 23.
- **AUC against 10 of 13 baselines**, including its exact classical twin at p = 2.3e-12.
- **The classical twin, on both metrics.** Heat kernel: 23 proteins / 17 families vs 69 / 20.
  Same graph, same seed, same time-averaging — only amplitudes vs probabilities.

## Where the classical algorithms win

- **Family-level P@5 >= 0.8**: closeness 29, eigenvector 25, communicability 23, commute time 22
  — all beat the CTQW's 20.
- **Family-level P@5 >= 0.6**: closeness 55 vs the CTQW's 45.
- **AUC ties**: closeness 0.576, betweenness 0.575, proximity 0.574 vs 0.600 (p = 0.12–0.63).

**The pattern**: the CTQW gets more *proteins* right but fewer distinct *families*. Its successes
concentrate in families with many structures. Family-level counting is the standard adopted in
this project (one family contributes 28 structures of a single protein, which inflated an early
result twentyfold), so by that standard plain closeness centrality — unseeded, parameter-free,
one line of code — beats the pipeline.

## Honest limits

- **MIN_HOP=1 only.** All conclusions rest on one seed-filter setting; robustness across
  MIN_HOP 2/3/4 is untested.
- The candidate residues come from the pipeline's own funnel (PASSer top-10, active-site pocket
  dropped, MIN_HOP filter, PocketMiner veto). Classical baselines rank a shortlist the pipeline
  produced; they never performed their own selection.
- The CTQW cell (gauss/sym + neg_dE) was chosen on this data. LOFO cell selection costs only
  +0.002 at family level, so the inflation is negligible but not zero.
- 0.600 is a MEAN: 52%% of proteins reach AUC >= 0.6, and **31%% score below chance**.
- This is NOT a quantum-advantage claim. The walk is classically simulated; no hardware, no
  speedup. Beating a classical baseline at a prediction task is a modelling result.
