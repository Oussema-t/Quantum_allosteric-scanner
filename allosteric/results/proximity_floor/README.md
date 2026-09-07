# Proximity floor test — does the CTQW beat ranking residues by distance?

**The control the 630-protein benchmark never had.** For every protein the pipeline scored, its
candidate residues are ranked by graph distance (hops) from the active site — no walk, no
Hamiltonian. Same residues, same labels as the CTQW. 8 A Ca contact graph, BFS from the active
site, AUC of `-hop` against the truth labels. `proximity_floor.py` reproduces it; per-protein
numbers in `proximity_floor_results.json`.

| subset | n | families | proximity floor | CTQW fixed (blind) | CTQW best-of-221 | proteins CTQW>floor | families CTQW>floor | sign test |
|---|---|---|---|---|---|---|---|---|
| ALL | 630 | 399 | **0.574** | **0.600** | 0.900 | 325 (52%) | 182/399 | p=0.089 |
| **DISTAL** (truth >=3 hops) | 91 | 53 | **0.227** | **0.617** | 0.848 | 83 (91%) | 47/53 | p=5.8e-09 |
| NEAR (0-2 hops) | 539 | 350 | **0.633** | **0.597** | 0.909 | 242 (45%) | 137/350 | p=5.7e-05 |

CTQW fixed = one configuration chosen in advance (gauss/sym + neg_dE), applied to every protein,
no peeking. CTQW best-of-221 = the best cell per protein, i.e. SELECTION, reported only as a ceiling.

## What it shows

**Overall the CTQW does not beat proximity.** 0.600 vs 0.574 across 630 proteins, winning 52% of
proteins (sign test p=0.45) and only 46% of families. On the full set the pipeline is not
distinguishable from ranking by distance from the active site.

**On DISTAL targets it wins decisively.** The floor is 0.227 — *below chance*, i.e. proximity
points away from the answer, as it must when the pocket is far from the active site by
definition. The CTQW reaches 0.617 and beats the floor on 83 of 91 proteins (91%).

**On NEAR targets proximity wins** (0.633 vs 0.597): there the walk is a noisier distance measure.

## Consequence for what we claim

The defensible claim is NOT "the CTQW finds allosteric sites". It is:

> On distal allosteric sites — the ones a geometric baseline cannot find, where proximity scores
> 0.227 — the CTQW reaches 0.617 and beats that baseline in 91% of cases. On near sites it adds
> nothing over distance.

This matches the challenge's own definition of success (distal regulatory residues vs background)
and is consistent with the earlier classical-baseline result (CTQW 19 families vs proximity 1 on
distal). It also means the headline 240 proteins / 137 families is inflated by near cases that
proximity would find anyway; the real result lives in the distal subset (91 proteins / 53 families).

## Not yet done

- distal recount at P@5 with a blind configuration (not best-of-221)
- proximity-MATCHED null with confidence intervals (the stricter form used on the mandatory targets)
- cross-validated choice of the fixed configuration; gauss/sym+neg_dE was picked on this same data
- CAS0002 contributes 28 of the 91 distal structures: always count distal results per FAMILY
