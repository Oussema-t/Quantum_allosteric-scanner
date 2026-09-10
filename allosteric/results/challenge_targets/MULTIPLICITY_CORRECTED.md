# Challenge targets — results corrected for configuration search

The headline numbers in `README.md` are **best-of-six** over the configurations the recommender
shortlisted. This file records what survives a null matched to that same search budget, so the
numbers can be quoted without a reviewer discounting them.

## The correction

The recommender returns six configurations per target. Reporting the best of six against a
single-ranking null overstates the result, because six draws from a random ranker also produce a
best. The null below draws six independent random rankings on the **same candidate set and the
same truth set**, takes the best, and repeats. Reported p is the fraction of those best-of-six
draws reaching the observed value.

This matters most where the candidate set is small: at MIN_HOP=4 BCR_ABL1 retains only 15
candidate residues with 5 truth (base rate 0.33), so six random rankings average P@5 = 0.55.

## Corrected results

| target | MIN_HOP | candidates / truth | metric | observed | best-of-6 null (mean, 95th) | p | verdict |
|---|---|---|---|---|---|---|---|
| BCR_ABL1 | 4 | 15 / 5 | AUC | **0.900** | 0.707, 0.880 | **0.035** | clears, marginally |
| BCR_ABL1 | 4 | 15 / 5 | P@5 | 0.80 | 0.552, 0.800 | 0.098 | does not clear |
| HIV1_RT | 2 | 43 / 8 | AUC | 0.679 | 0.645, 0.764 | 0.304 | does not clear |
| KRAS_G12C | — | — | — | — | — | — | not run (PASSer server error on every KRAS structure tried) |

Nulls: 2001 draws (BCR_ABL1), 4000 draws (HIV1_RT), seeded, `numpy.random.default_rng`.

## Blind numbers, for contrast

The pre-registered fixed cell `gauss|sym|neg_dE` — chosen before these targets were scored and
used for the whole 630-protein cohort — gives **AUC 0.140** on BCR_ABL1 at MIN_HOP=4. The
recommender's own top-weighted pick (51% weight) is that same cell. The configuration that
reaches 0.900 is rank 4 with 7% weight.

So the model does not select the winner. Reaching 0.900 requires knowing the answer.

## What can honestly be claimed

- **Claimable:** on BCR-ABL1, one of six shortlisted configurations reaches AUC 0.900 against the
  asciminib contact set, p = 0.035 under a search-matched null. Four of its top five residues are
  genuine asciminib contacts in the myristoyl pocket.
- **Not claimable:** that P@5 = 0.80 is above chance here (p = 0.098), that HIV1_RT is a hit
  (p = 0.304), or that the pipeline selects the winning configuration prospectively (it selects a
  configuration scoring 0.140).
- **n = 1.** One target clearing at p = 0.035, out of two scoreable, is a single observation. It
  is reportable as such and not as a performance rate.

Reproduce: `python3 apply_model.py`, then the null in this file's git history.
