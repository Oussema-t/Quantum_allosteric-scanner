# TASK-0292 — Does fpocket's pocket-splitting cost us on the selection ceiling?

- Status: Done
- Assignee: Reviewer thread
- Priority: High — answers a user question about [[TASK-0282]]'s headline ceiling and **diagnoses where its 0.165-vs-0.556 gap comes from**
- Filed: 2026-08-29 by Reviewer thread (user question following [[TASK-0291]])
- Related: [[TASK-0291]], [[TASK-0282]], [[TASK-0287]], [[TASK-0249]]

## The question

[[TASK-0291]] found fpocket puts a median of 4 numbered pockets on a
single drug's contact set, and that in 11/33 targets a provably single
cavity is still split. Does that splitting hurt the "filter by distance,
rank by druggability, draw 5 residues" ceiling?

**Predicted mechanism before running:** [[TASK-0287]] showed fpocket
druggability is largely pocket size. Splitting makes fragments smaller,
which should push a real cavity's fragments *down* a size-driven ranking.

## Findings

**A. Control passed.** A fresh reimplementation reproduces [[TASK-0282]]'s
published rule EH to five decimals: **0.16486 vs 0.16486**. Raw oracle EH
= **0.5563**.

**B. Merging HURTS at every criterion. The prediction was wrong.**

| criterion | mean cavities | rule EH | delta | oracle |
|---|---|---|---|---|
| RAW (no merging) | 39.5 | **0.1649** | — | **0.5563** |
| shared residues | 4.0 | 0.0162 | −0.1487 | 0.1632 |
| min Cα–Cα < 2 Å | 4.0 | 0.0162 | −0.1487 | 0.1632 |
| min Cα–Cα < 3 Å | 4.0 | 0.0162 | −0.1487 | 0.1632 |
| min Cα–Cα < 4 Å | 1.4 | 0.0237 | −0.1412 | 0.0422 |
| min Cα–Cα < 5 Å | 1.3 | 0.0263 | −0.1385 | 0.0419 |
| min Cα–Cα < 6 Å | 1.2 | 0.0289 | −0.1360 | 0.0417 |

**fpocket's splitting is not costing us — it is helping.** fpocket
fragments average **9.6 residues** and the true drug sites average ~12;
they are well matched. Merged cavities are far larger than any real drug
site, so `overlap/size` collapses — the oracle itself falls to 0.163.

> **Recorded failure:** the first merge attempt used min Cα–Cα < 8 Å (the
> standard `enm_cutoff`). On a folded protein that **percolates** — every
> target collapsed from ~40 candidates to exactly ONE cavity. Its numbers
> (rule 0.041, oracle 0.041) say nothing about fpocket and were discarded.
> The sweep above exists because of that failure.

**C. The real cost is size, via a different route than predicted.**

| | residues |
|---|---|
| mean candidate size | 9.6 |
| mean size of **oracle** pick | 10.2 |
| mean size of **rule** pick | **17.6** — 1.7× the oracle's |

- within-target rho(size, druggability) = **+0.239**, Wilcoxon **p=0.0007**
- within-target rho(size, EH) = **+0.116**, Wilcoxon p=0.0057

**rho(size, EH) is POSITIVE** — the metric does *not* reward small
fragments. The rule's loss is simply that druggability tracks size and
therefore selects candidates far larger than any real drug site. The
worst cases are stark: TRP_SYNTHASE oracle picks size 12 (EH 0.583) while
the rule picks size **43** (EH 0.093); PKR oracle 11 (EH 0.727) vs rule
**34** (EH 0.000); HCV_NS5B_VRX oracle 9 (EH 1.000) vs rule **26**
(EH 0.000).

**Nine of twenty targets score exactly 0.000 under the rule with a
non-zero oracle.** That is the entire headroom, and it is a *selection*
failure, not a candidate-availability failure.

**D. A size-corrected rule looks better in-sample but is NOT a result.**

| arm | mean EH | delta | Wilcoxon p |
|---|---|---|---|
| druggability (published) | 0.1649 | — | — |
| **druggability / size** | **0.2649** | **+0.100** | **0.157** |
| druggability residualised on size | 0.1556 | −0.009 | 0.157 |
| smallest candidate | 0.0458 | −0.119 | 0.138 |

`druggability / size` gains +0.100 **in-sample on the frozen 20 and is not
significant**. This register has already been burned once by exactly this
pattern — an in-sample sweep reporting 0.267 that then never won a LOTO
fold. **Nothing in Part D is reportable until LOTO says so.**

## Correction

An earlier statement by this thread — that `EH = overlap/size` "rewards
small pure fragments" and that merging might therefore lower the oracle
for that reason — was **wrong**. rho(size, EH) is positive (+0.116,
p=0.0057). Merging lowers the oracle because merged cavities are far
larger than real drug sites, not because small fragments are favoured.

## Next

- **LOTO on `druggability / size`.** If it survives leave-one-target-out
  it raises the published ceiling from 0.165 to ~0.265 and materially
  strengthens the "simple classical heuristics beat CTQW" framing. If it
  does not, it must be reported as another in-sample mirage. Either
  outcome is worth having before the write-up.
- Do **not** merge fpocket candidates anywhere in the pipeline.
