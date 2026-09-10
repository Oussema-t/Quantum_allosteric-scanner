# Proximity floor test — does the CTQW beat ranking residues by distance?

> **RETRACTED 2026-09-10 — the distal claim in the original version of this file was inverted.**
> An AUC of 0.227 for `-hop` does not mean the geometric baseline fails. It means the *reversed*
> baseline — rank residues by being FARTHER from the active site — scores **0.773**. That is the
> real floor on the distal subset, and the CTQW's 0.617 loses to it: the walk beats it on only
> **27 of 91** proteins, sign test **p = 1.3e-04 against us**. The original text read the number
> as a decisive win (83/91, p = 5.8e-09). It is a decisive loss.
>
> The floor is also partly tautological here: the distal subset is *defined* as truth ≥ 3 hops
> from the active site, so "farther is better" is true by construction on this subset. It is a
> ceiling on what any distance-free method must beat, not an interesting finding in itself.
>
> Verified against `proximity_floor_results.json` on 2026-09-10. Numbers below are the corrected
> ones; the original commit is 192d499.


**The control the 630-protein benchmark never had.** For every protein the pipeline scored, its
candidate residues are ranked by graph distance (hops) from the active site — no walk, no
Hamiltonian. Same residues, same labels as the CTQW. 8 A Ca contact graph, BFS from the active
site, AUC of `-hop` against the truth labels. `proximity_floor.py` reproduces it; per-protein
numbers in `proximity_floor_results.json`.

| subset | n | families | proximity floor | CTQW fixed (blind) | CTQW best-of-221 | proteins CTQW>floor | families CTQW>floor | sign test |
|---|---|---|---|---|---|---|---|---|
| ALL | 630 | 399 | **0.574** | **0.600** | 0.900 | 325 (52%) | 182/399 | p=0.089 |
| **DISTAL** (truth >=3 hops) | 91 | 53 | **0.773** (reversed) | **0.617** | 0.848 | 27 (30%) | see note | **p=1.3e-04 against** |
| NEAR (0-2 hops) | 539 | 350 | **0.633** | **0.597** | 0.909 | 242 (45%) | 137/350 | p=5.7e-05 |

CTQW fixed = one configuration chosen in advance (gauss/sym + neg_dE), applied to every protein,
no peeking. CTQW best-of-221 = the best cell per protein, i.e. SELECTION, reported only as a ceiling.

## What it shows

**Overall the CTQW does not beat proximity.** 0.600 vs 0.574 across 630 proteins, winning 52% of
proteins (sign test p=0.45) and only 46% of families. On the full set the pipeline is not
distinguishable from ranking by distance from the active site.

**On DISTAL targets it loses decisively.** The floor is 0.773, not 0.227: because the subset is
defined by truth being >= 3 hops away, ranking residues by *distance from* the active site is a
strong predictor there by construction. The CTQW reaches 0.617 and beats that floor on only 27 of
91 proteins (30%), sign test p = 1.3e-04 in the baseline's favour.

**On NEAR targets proximity wins** (0.633 vs 0.597): there the walk is a noisier distance measure.

## Consequence for what we claim

The defensible claim is NOT "the CTQW finds allosteric sites". It is:

> There is no subset on which the CTQW beats the geometric floor. On near sites distance wins
> (0.633 vs 0.597); on distal sites reversed distance wins (0.773 vs 0.617); overall the two are
> indistinguishable (0.574 vs 0.600, sign test p = 0.45).

The earlier "CTQW 19 families vs proximity 1 on distal" result rests on the same one-directional
floor and is subject to the same correction — it must be re-scored against reversed distance
before it is quoted anywhere.

## Not yet done

- distal recount at P@5 with a blind configuration (not best-of-221)
- proximity-MATCHED null with confidence intervals (the stricter form used on the mandatory targets)
- cross-validated choice of the fixed configuration; gauss/sym+neg_dE was picked on this same data
- CAS0002 contributes 28 of the 91 distal structures: always count distal results per FAMILY
