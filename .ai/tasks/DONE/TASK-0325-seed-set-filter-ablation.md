# TASK-0325 — Reverse-CTQW v2: the gate does the work, not the walk

- Status: Done
- Owner: Reviewer thread
- Filed: 2026-09-03 (id via `claim.py reserve-next`)
- Related: [[TASK-0320]], [[TASK-0312]], [[TASK-0287]], [[TASK-0269]], [[TASK-0310]], [[HYP-P9]]

## The proposal under test

A collaborator's v2 of [[TASK-0320]]: rather than let the CTQW rank *all* of
fpocket's candidates, use a predictor consensus (fpocket ∩ PASSer, PocketMiner
as a third signal, **2-of-3 majority — explicitly not an AND**) to choose which
pockets the walk is seeded from, then seed residue-by-residue toward the active
site.

## Their two factual claims, both checked

**"PocketMiner has only ever been used in the TASK-0269 per-residue attribution,
never to select seeds."** Correct. It appears in six scripts (0163, 0260, 0269,
0274, 0277, 0310); in every one it enters as a *scored feature block*, never as
a candidate gate. Coverage is **18 crypticity-cohort targets**
(`results/tasks/0269_pocketminer_residual/`), none of them ASBench, and
BCR-ABL1 is not among them — so their 1OPL/MYR observation is new information
here, not a re-derivation of ours.

**"Don't AND it."** Right, and the cost is now quantified — see the retention
column below.

## The blocker they could not have known

**PASSer was never built.** `ALGORITHM_REGISTER.md` §F rates it 3 ("lower
priority than the three above"); `PLAN.md` still carries it as an open box; only
[[TASK-0011]] mentions it, as a wrapper that was scoped and not written. The
literal `fpocket ∩ PASSer` gate is not runnable today.

## Why the walk cannot be what improves

[[TASK-0320]]'s identity, verified to machine precision (ratio 20.0000 = |A|):

    transfer(P→A) = |A| · mean_{i∈P} p_A(i)

`H_new` is real symmetric and seed-independent, so restricting the seed set
changes **which** candidates are scored and cannot change any `p_A(i)`. Every
surviving candidate keeps a bit-identical CTQW score. Restriction of range is
still real — a correlation can move on a subpopulation — so this was measured,
not argued.

## Method

`scripts/task0325_seed_filter_ablation.py`, over the per-candidate arrays now
dumped by `task0320b_reverse_seeded_asbench.py` (ADD-only: `_prox`, `_drug`,
`_nres`; the re-run reproduced every published number identically). PASSer and
PocketMiner being unavailable on this cohort, the simulated gate is the *class*:
keep the top-K candidates by fpocket druggability — generous to the proposal,
since druggability consensus is a real gate's main axis.

n = 105 ASBench structures / 75 proteins. Median 55 candidates per structure.

## Result

| gate | true pocket retained | random | ctqw | ctqw\|prox | fpocket | size |
|---|---|---|---|---|---|---|
| top-3 | **34.3%** | 11.4% | 13.3% | 12.4% | 16.2% | **17.1%** |
| top-5 | **46.7%** | 9.3% | 12.4% | 6.7% | 16.2% | **18.1%** |
| top-half | **82.9%** | 4.0% | 2.9% | 3.8% | 16.2% | **17.1%** |
| none ([[TASK-0320]]) | 100% | 2.5% | 1.9% | 0.0% | 16.2% | **17.1%** |

Top-1 hit rate. `random` is analytic, conditioned on the same gate.

1. **The gate is the entire effect.** Random-within-gate rises 2.5% → 11.4%,
   a 4.5× gain with no walk involved.
2. **CTQW does not beat random-within-the-same-gate.** +1.9 pts at top-3 (2
   structures of 105); *below* random at top-half and no-filter.
3. **The gate's own score dominates it at every gate.** Paired McNemar,
   ctqw vs fpocket druggability: p=0.629 / 0.503 / **0.000519** / **0.000275**
   — indistinguishable where the gate is tight, significantly worse where it
   is loose.
4. **Raw cavity size is still the best selector at every gate** (17–18%) —
   [[TASK-0287]]'s size confound survives filtering untouched.
5. **Residualised CTQW is at or below random everywhere.** Consistent with
   [[TASK-0310]]; the gate does not unblock it.
6. **The retention column is the proposal's real ceiling.** A top-3 gate throws
   the true pocket away in 65.7% of structures. Their own AND-gate caveat,
   measured: a 2-of-3 majority is milder than an AND but pays the same currency.

## What is *not* excluded

The candidate **generator** was never varied — but it is not the bottleneck
here. Median `best_recall` = 0.875; **zero** of 105 structures have no fpocket
candidate overlapping the true site; 76.2% have one covering ≥ half of it. The
answer is almost always already in the list. Adding predictors as generators
therefore has little room on ASBench; adding them as filters is what the table
above measures.

The untested residue: PocketMiner on a cohort where it *has* coverage, gating a
CTQW that is run there. Given rows 2–5 that is a low-prior run, and it needs
PocketMiner extended to ASBench (Docker recipe exists, `tools/pocketminer/`).

## Artifacts

- `scripts/task0325_seed_filter_ablation.py`
- `scripts/task0320b_reverse_seeded_asbench.py` (ADD-only per-candidate dumps)
- `results/tasks/0320b_reverse_seeded_asbench/` — gitignored, reproducible

## Note

Filed before answering the collaborator, and the register was read first —
[[HYP-P9]], [[TASK-0287]], [[TASK-0310]] — which is the behaviour
[[TASK-0321]] argues is currently absent 91% of the time.
