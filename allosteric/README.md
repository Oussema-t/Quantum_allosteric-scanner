# `allosteric` — CTQW allosteric-site prediction

Working branch for Team AuraQu's science notebook and its results.

| file | what it is |
|---|---|
| **`REPORT.md`** | **read this first** — every result with the configuration that produced it, and what is wrong with each |
| `Quantum_Allosteric_Scanner_v2.ipynb` | the pipeline (fpocket → PASSer → PocketMiner → seed selection → CTQW) |
| `AuraQu_score_log.md` | curated run history with caveats |
| `datasets/` | the 5-dataset benchmark, its audit, and the measured outcomes |
| `tools/pocketminer/` | native macOS arm64 PocketMiner recipe (no Docker), port-validated at AUC 0.868 |

## One-paragraph summary

One defensible positive: **HIV1-RT, pre-registered, AUC 0.697, p = 0.0175**. The high scores on
KRAS and BCR-ABL1 are confounded (proximity inflation; a 0.78 base rate from an apo structure
that already has its ligand bound). Across a 1233-protein external benchmark, **only 13% of
targets have an allosteric site far enough from the active site to test propagation at all** —
for the rest, "finding" it demonstrates proximity. No quantum propagator beats a classical
heat-kernel control once distance is removed. The infrastructure — dataset audit, distance
measurement, seed selection with failure diagnostics, a validated PocketMiner port — is solid
and reusable; the scientific claim is currently one target wide.

## Datasets

`datasets/` holds derived data, not third-party payloads. `cryptobench_dataset.json` (8.4 MB) is
omitted — download from OSF `10.17605/OSF.IO/PZ4A9`. `casbench_annotations.json` was scraped from
`biokinet.belozersky.msu.ru/casbench` (Zlobin et al. 2019, *Acta Naturae* 11:74-80).
`cryptosite_pairs.json` is a **partial** 21/93 subset — see its `PROVENANCE.txt`.
