# TASK-0300 — The rule-selection criterion is defective, and the rule family nearly contains the answer

- Status: Done
- Priority: **High — reframes the pocket-level negative and identifies the actual missing component**
- Filed: 2026-08-30 by Reviewer thread, on three challenges from the repo owner
- Related: [[TASK-0299]], [[TASK-0298]], [[TASK-0282]], [[TASK-0288]], [[TASK-0261]]

## Challenge 1 — "how is a 0.000-scoring rule selected? Looks like a selection bug." **Correct.**

`hop>=3 + lex_far_first` scores **> 0 on exactly two of twenty rows** —
`HCV_NS5B_VRX` and `HCV_NS5B_VR1`, at **1.000 each**. Mean = 2.0/20 =
**0.100**. Those two rows are **one apo structure**.

`hop>=1 + drug_alone` scores > 0 on **six rows across four distinct
structures** (GAC_CPD12, KSHV×2, TRP_SYNTHASE×2, SMYD3). Mean **0.0899**.

**`fit_final_rule` selects on the raw row mean — no cluster correction, no
breadth term.** So a rule that nails *one structure* beats a rule that
works on *four*. This is the **fourth** pseudo-replication failure in this
register ([[TASK-0282]] `lex_near_first`, [[TASK-0293]]
`druggability/size`, [[TASK-0299]] CTQW, now the selector itself).

### The fix, tested

Selecting by **cluster mean** instead of row mean, under leave-one-
*cluster*-out (stricter than LOTO — removes the sibling row too):

| selection criterion | held-out mean EH | vs random, cluster-robust |
|---|---|---|
| current (row mean) | 0.0000 | p = **0.00024** (worse than random) |
| fixed (cluster mean) | 0.0093 | p = 0.101 |
| random | 0.0273 | — |

**The fix removes the pathology but does not rescue the result.** Real
bug, worth fixing; not the root cause.

## Challenge 2 — "maybe we need two rules and categorisation." **Supported, but the category is the wrong stratifier.**

| category | n rows | n structures | `hop>=1 + drug` | `hop>=3 + lex_far` |
|---|---|---|---|---|
| contact-adjacent | 11 | 9 | **0.088** | 0.000 |
| proximal | 5 | 4 | **0.167** | 0.000 |
| intermediate | 4 | 2 | 0.000 | **0.500** |

Oracle-assisted stratified rule (using the **true** category):
**0.1899** — nearly double the best single rule (0.100), ~7× random.

**But the category does not determine the winning rule.** Per-target best
rule gives **0.3307**, far above category-stratified 0.1899.
Counterexamples: `NAMPT_NPA1R` is contact-adjacent yet its best rule is
`centroid_euclid>=15A + lex_near_first` at **0.889**; `HCV_NS5B_VRX` and
`HCV_NS5B_POO` are **both** intermediate, and score **1.000** and
**0.000** under the same rule. The intermediate stratum is 4 rows / **2
structures**, one of which scores zero — a coin flip, not a finding.

## Challenge 3 — "if fpocket finds them and nothing picks them, we simply need a selector."

| | mean EH | share of achievable |
|---|---|---|
| random | 0.0273 | 7% |
| best single fixed rule | 0.1000 | 25% |
| category-stratified (oracle category) | 0.1899 | 48% |
| **best rule chosen per target (oracle)** | **0.3307** | **83%** |
| fpocket candidate oracle (perfect pocket pick) | 0.3984 | 100% |

**The 61-rule family already captures 83% of what is achievable** — *if*
you could pick the right rule per protein. The entire gap from 0.100 to
0.3307 is **meta-selection**, not ranking power.

**Two hard caveats.**
1. **0.3307 is inflated by multiplicity** — best-of-61 per target on 20
   targets. An optimistic upper bound, not a reachable score.
2. **5 of 20 targets have NO rule in the family scoring > 0**:
   `HCV_NS5B_POO`, `HCV_NS5B_CMF`, `FBPASE_94D`, `FBPASE_95S`,
   `MKK7_IBRUTINIB` — and `MKK7`'s own fpocket oracle is **0.75**. A great
   candidate exists and no rule reaches it.

## Correction to [[TASK-0299]]

That task called `hop>=3 + lex_far_first` "anti-correlated with the truth
by construction". **Too strong.** It is *narrow*, not inverted: right on
one structure, zero on the rest. Negating it does not rescue it —
`lex_near_first` scores 0.055. The `hop>=3` filter does delete the true
pocket for the contact-adjacent majority, but that describes where it
fails, not a usable inverted signal.

## What this reframes

The pocket-level negative is **not** "ranking pockets is hopeless". It is:

> Existing simple rankers would reach **~83% of the achievable ceiling** if
> a per-protein meta-selector chose among them. We have no such selector,
> and [[TASK-0287]]/[[TASK-0288]] measured that no structural descriptor we
> can compute predicts the property it would need.

A sharper, more useful open problem than "nothing works", and a legitimate
Phase-2 framing.
