# End-to-end test on the challenge targets

The trained recommender applied to targets it has never seen, then the full pipeline run with the
configurations it returns. Targets are NOT in the 630-protein training set.

## Target definitions (derived from structure, no hand-typed residue lists)
`prep_targets.py`: truth = apo residues aligning to holo residues within 4.5 A of the allosteric
drug; active site = residues near the functional ligand (curated for HIV1_RT, which has no
functional-ligand marker in the apo).

| target | apo | holo | drug | truth residues | active |
|---|---|---|---|---|---|
| KRAS_G12C | 4LDJ | 6OIM | MOV (sotorasib) | 21 | 20 |
| BCR_ABL1 | 1OPL | 5MO4 | AY7 (asciminib) | 20 | 26 |
| HIV1_RT | 1DLO | 3V81 | NVP (nevirapine) | 16 | 3 |

KRAS uses 4LDJ, not the challenge's 4OBE: 4OBE is WILD-TYPE KRAS (residue 12 = Gly, verified),
not G12C. 4LDJ is genuinely G12C (residue 12 = Cys, verified). Per the `bartosz` track, reported
to the organisers, who sanctioned an apo re-run.

## Pipeline
PASSer top-10 -> drop active-site pocket + MIN_HOP filter -> CTQW round 1 -> PocketMiner veto
(worse half by accessibility dropped, apo-ligand pockets protected) -> CTQW round 2 -> score
residues against the drug-contact truth. Run once per recommended configuration.
PocketMiner run natively (arm64 TF 2.13); veto in `veto_targets.json`.

## Results

**BCR_ABL1 — a hit.** Best of the six recommended configurations: **AUC 0.900, P@5 0.80**
(harm/adj + neg_dD_mean at MIN_HOP=4) — 4 of the top 5 residues are genuine asciminib contacts in
the myristoyl pocket.

| rank | hop | configuration | weight | AUC | P@5 |
|---|---|---|---|---|---|
| 1 | 4 | gauss/sym + neg_dE | 0.508 | 0.140 | 0.00 |
| 2 | 4 | binary/comb + neg_dD_mean | 0.234 | 0.780 | 0.40 |
| 3 | 4 | binary/sym + neg_dE | 0.118 | 0.000 | 0.00 |
| **4** | 4 | **harm/adj + neg_dD_mean** | 0.074 | **0.900** | **0.80** |
| 5 | 4 | exp/sym + neg_dE | 0.033 | 0.220 | 0.20 |
| 6 | 4 | hnew/full + neg_dE | 0.033 | 0.220 | 0.20 |

**HIV1_RT — moderate ranking, no top-5 hit.** Best AUC 0.679 (gauss/sym + neg_dE, MIN_HOP=2),
P@5 0.00 for the top two. Consistent with the notebook's pre-registered AUC 0.697. The 6th
configuration (MIN_HOP=4) is unscoreable: 27 seeds, 0 truth residues survive that filter.

**KRAS_G12C — blocked.** PASSer's server returns an internal error for 4LDJ and for every other
KRAS structure tried (4OBE, 4LYH, 6P8W) — their service, not our input. No pockets, no run.

## Three findings

1. **The shortlist works, the weighting does not.** On BCR_ABL1 the winning configuration is rank
   4 with 7% weight, while the top-weighted pick (51%) scores AUC 0.140. Scoring by the model's own
   confidence gives AUC 0.335 vs 0.900 for best-of-six.
2. **Merging the shortlist destroys the result**: best-of-shortlist merge 0.570, weighted average
   0.200, against 0.900 for the single best configuration. One good ranking is diluted by five bad
   ones — the same effect seen on the 630-protein set.
3. **The MIN_HOP feasibility gate is necessary but not sufficient.** It correctly rejected MIN_HOP
   3 and 4 for KRAS (which would have kept 2 of 21 truth residues) but passed HIV1_RT MIN_HOP=4,
   which kept 0. Candidate counts cannot reveal how far the unknown pocket is from the active site.

## Honest conclusion
The recommender reduces 884 configurations to 6 and a good one is inside for BCR_ABL1. Choosing
among the 6 still requires the truth or a human; merging them automatically is worse than picking
one. This is a search-reduction tool, not an automatic predictor.
