# Pocket-seeded CTQW sweep at scale (138 distal proteins)

The §14 experiment run as a benchmark instead of per-target: seed the walk from
detected **pockets** (not from the active site), walk to the active site, score with
the full §14 battery, and ask whether the drug pocket ranks first.

## Design

| step | setting |
|---|---|
| cohort | 138 `is_distal` proteins of the 1022-protein worklist (86 families) |
| pocket detection | fpocket, per chain, ranked by druggability |
| seed selection | `fpocket` = top 10 by druggability **·** `consensus` = fpocket ∩ PASSer |
| consensus rule | pocket matched to a PASSer pocket at Jaccard ≥ 0.5, then **minrank** = `max(rk_fpocket, rk_PASSer)` — a pocket is only as good as its worse rank, so it must be druggable **and** allosteric simultaneously (notebook 13z, `SEED_SOURCE="consensus"`, `SEED_COMBINE="minrank"`) |
| seed filter | `MIN_HOP` ∈ {1, 2} graph hops from the active site |
| operators | 12 = `weight` ∈ {binary, exp, gauss, harm} × `norm` ∈ {adj, comb, sym}, cutoff 10 Å |
| scores | 8 = `p_avg`, `p_peak`, `R`, `residLOG`, `residRAW`, Green `|G|²` at (E,η) ∈ {(0,0.05), (0,0.01), (λmax,0.05)} |
| cells | 96 per protein (12 × 8) |
| truth | drug-contact / curated allosteric residues among the seeds |
| null | **label permutation against the actual score vectors**, 200 draws, rank-sum AUC — preserves the correlation between the 96 cells |

## Files

| file | contents |
|---|---|
| `fpocket_hop1.json`, `fpocket_hop2.json` | fpocket-only selector, per protein: all 96 cells, observed vs null max, permutation p |
| `consensus_hop1.json`, `consensus_hop2.json` | fpocket ∩ PASSer selector, same fields |
| `consensus13_hop1.json`, `consensus13_hop2.json` | fpocket ∩ PASSer with **`H_new` as a 13th operator** (13 × 8 = 104 cells), same fields |
| `consensus13_hop2_ranks.json` | same run with **per-cell residue rank vectors**, seed→pocket map and labels — input to the §14 consensus analysis |
| `sec14_consensus_per_protein.json` | per protein: how many of the 8 scores elected the TRUE pocket, unanimity, pocket counts |
| `sec14_consensus.py` | the notebook §14 CONSENSUS block (median-rank pocket votes, Kendall's W, "do the scores agree?") applied to every protein |
| `per_protein_summary.csv` | one row per (run, protein): best AUC cell, best P@5 cell, null, permutation p, or why it was not scored |
| `pocketsweep.py` | the sweep (sharded, checkpointed every 10 proteins, resumable) |
| `passerfetch.py` | PASSer API fetch/cache for the cohort |
| `pocketanalyze.py` | aggregation: family-averaged marginals, clearing cells, winner grouping |

## Reproducing

```bash
python3 passerfetch.py                      # fills passer_cache.json
SHARD=0 NSHARD=8 OUT=run_0.json \
  N_POCKETS=10 MIN_HOP=2 SELECTOR=consensus JACCARD=0.5 \
  python3 pocketsweep.py                     # one shard; repeat SHARD=0..7
python3 pocketanalyze.py "run_*.json"
```

Ran on a Hetzner `cx43` (8 vCPU), 8 shards, ~8 min per selector × MIN_HOP pair.
`fpocket` is **not** an Ubuntu package — it must be built from source
(`git clone https://github.com/Discngine/fpocket && make && make install`;
the parallel build silently produces no binary, run `make` twice).
