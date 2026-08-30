# TASK-0299 — After the chain fix, nothing works at pocket level — and CTQW does not win

- Status: Done
- Assignee: Reviewer thread
- Priority: **Critical — invalidates a headline claim in the collaborator brief, hours before the submission sync**
- Filed: 2026-08-30 by Reviewer thread, on [[TASK-0298]]'s corrected numbers
- Related: [[TASK-0298]], [[TASK-0282]], [[TASK-0293]], [[TASK-0261]], [[TASK-0184]]

## Why

[[TASK-0298]] fixed the chain-agnostic fpocket parsing and re-ran
[[TASK-0282]]. The corrected frozen-20 means invert the register's
headline framing at first glance:

| arm | corrected mean EH |
|---|---|
| swept rule (LOTO) | **0.0000** |
| **CTQW wrapper** | **0.0389** |
| random | 0.0273 |
| oracle | 0.3984 |

Read naively this says **CTQW beats the classical ceiling and beats
random** — the exact reverse of what the brief claims and of what the
collaborator has just agreed to. It must not be reported that way, and it
must not be left unexamined before the sync.

## Finding — CTQW's advantage is one structure counted twice

CTQW scores **> 0 on exactly two of twenty rows**: `KSHV_PROTEASE_24Q`
(0.444) and `KSHV_PROTEASE_25G` (0.333). Every other target is 0.000.

Both rows are the **same apo structure** (2PBK) and sit in the **same
cluster** ([[TASK-0261]]'s `pair1`). CTQW's entire mean rests on **1
cluster of 13**.

Cluster-robust sign-flip tests (13 clusters, exact):

| comparison | mean | statistic | p |
|---|---|---|---|
| CTQW vs random | 0.0389 vs 0.0273 | +0.232 | **1.000** |
| CTQW vs swept rule | 0.0389 vs 0.0000 | +0.778 | **1.000** |
| swept rule vs random | 0.0000 vs 0.0273 | −0.546 | **0.000244** |

**CTQW is not distinguishable from random (p=1.000) and not
distinguishable from the classical rule (p=1.000).** Its apparent win is
the same pseudo-replication artifact this register has now caught three
separate times — [[TASK-0282]]'s `lex_near_first`, [[TASK-0293]]'s
`druggability/size` (HCV_NS5B_VRX/VR1), and now CTQW itself.

## The claim that DOES break

The classical rule is **significantly worse than random** (p=0.000244).
That is not a fluke: [[TASK-0298]] traced it. Once 9 of 20 targets' true
achievable ceilings dropped, [[TASK-0282]]'s own sweep-and-select
procedure picked a **different** rule — `MIN_HOP>=3 + lex_far_first`
edging out `MIN_HOP>=1 + drug_alone` by 0.100 vs 0.0899 in-sample — and
that rule scores exactly 0.000 on every held-out target, including
targets never exposed to the bug.

So the brief's framing — *"simple classical heuristics construct a
ceiling that outperforms CTQW"* — **no longer holds as stated.**

## The honest corrected statement

> At pocket level, after the chain-parsing correction, **nothing works.**
> Neither the classical selection rule nor CTQW is distinguishable from
> chance under cluster-robust held-out evaluation. The classical
> rule-selection procedure actually underperforms random, because
> selecting a rule on 20 pseudo-replicated rows over 13 clusters picks a
> degenerate one. Meanwhile the oracle sits at **0.398** — good candidates
> exist in every protein; **no selection procedure we have, classical or
> quantum, can find them.**

This is *stronger* evidence for the benchmark-level conclusion both teams
already converged on, not weaker. It removes a claim we cannot support
and replaces it with one the data does support.

## What must NOT be concluded

- **Not** "CTQW wins." p=1.000 against random, on one cluster.
- **Not** "the classical approach is refuted." A fixed, pre-specified rule
  still scores 0.0899 in-sample; what failed is *selecting* a rule on this
  cohort.
- **Not** that [[TASK-0298]]'s fix is suspect. It is correct, was
  sanity-checked on an unexposed single-chain target
  (`KSHV_PROTEASE_24Q`, EH reproduced bit-for-bit), and the artifact it
  removed was real — `GAC_BPTES`'s oracle of **1.000** came from a chain-B
  candidate mapping onto chain-A ground truth at colliding resnums.

## Action before the sync

- [ ] [[TASK-0184]] and the collaborator brief must drop the
      "classical ceiling beats CTQW" framing and adopt the statement
      above. **Both numbers change; the conclusion about the benchmark
      does not.**
- [ ] Tell the collaborator directly. They agreed to a framing that our
      own correction has since invalidated in their favour on one point
      (CTQW is not beaten by a classical ceiling) and against it on
      another (CTQW still does not beat chance). Presenting only the first
      half would be dishonest; presenting neither would be worse.
