# TASK-0275 — Decompose the potential terms: `V_C` alone beats CTQW, and we lumped it

- Status: TODO
- Assignee: unassigned (suggest Implementer A — owns TASK-0263, reuses its cached CV)
- Priority: **High — cheap, and it converts TASK-0263's headline into a much sharper and more credible claim**
- Filed: 2026-08-26 by Reviewer
- Related: [[TASK-0263]], [[TASK-0254]], [[TASK-0257]], [[TASK-0261]]

## What TASK-0263 did, and what it hid

[[TASK-0263]] scored `H_new`'s potential terms as **one lumped block**
(`BLOCKS4 = ["geometry", "fpocket", "ctqw", "terms"]`) and got the register's
best constructive result: terms 0.751 vs CTQW 0.575, cluster-robust p=0.019.

It also computed per-term solo AUCs and stored them
(`per_term_auc.json`) but **never used the terms as separate attribution
categories.** Re-aggregating that file per term across the 20 targets:

| term | what it is | median AUC | >0.7 | max |
|---|---|---|---|---|
| **`V_C`** | **GNM dynamic cross-correlation centrality** — mean abs. normalised DCC, the standard allosteric-coupling measure (Haliloglu & Bahar 1999) | **0.6365** | **8/20** | 0.973 |
| `V_B` | B-factor penalty — raw experimental flexibility, no model | 0.5940 | 6/20 | 0.873 |
| `V_R` | — | 0.5323 | 0/20 | 0.699 |
| `V_M` | — | 0.5295 | 1/20 | 0.715 |
| `V_T` | — | 0.5142 | 0/20 | 0.548 |

**Two things the lumping concealed:**

1. **`V_C` alone (0.6365) already beats the whole CTQW (0.575).** The single
   strongest ingredient is the field's own classical allosteric-coupling
   metric, used directly as a per-residue score. `V_B` — pure deposited
   B-factors — is second. Three of the five terms are near chance.
2. **The terms are not redundant with each other.** All ten cross-term
   Spearman correlations over the 20 targets are weak (|ρ| ≤ 0.45; only
   `V_T`–`V_C` reaches p<0.05). Five distinct signals, not one — so a joint
   decomposition may show genuine complementarity that a single block cannot.

## Why this matters beyond tidiness

"Our potential terms beat our quantum walk" is a decent finding. "**The
standard classical allosteric-coupling measure, scored directly, beats the
quantum walk built on top of it**" is a much sharper, more citable, and more
credible one — and it names the specific physics rather than gesturing at a
bundle. It is also far harder for a reviewer to dismiss.

## Scope

- [ ] Re-run [[TASK-0254]]'s Shapley with the five terms as **separate
      blocks** alongside geometry / fpocket / CTQW. That is 8 blocks — exact
      Shapley is 8! = 40,320 permutations per target, still cheap, but confirm
      the runtime before launching and use the n-block routine [[TASK-0260]]
      generalised rather than rewriting it.
- [ ] If 8 blocks is impractical, run the defensible reduction: `V_C`, `V_B`,
      and a lumped `{V_T, V_R, V_M}` — stated as a decision, not a silent
      simplification.
- [ ] Report **each term's contribution added last**, on top of geometry +
      fpocket + CTQW. The decision statistic, as everywhere in this register.
- [ ] **The headline question**: does CTQW retain any added-last contribution
      once `V_C` specifically is in the model? [[TASK-0263]] found p=0.973
      against the lumped block; test it against `V_C` alone.
- [ ] Reuse [[TASK-0263]]'s cached CV where possible — that task explicitly
      notes the 5-block Shapley cache avoided a second CV run.
- [ ] Cluster-robust significance ([[TASK-0261]]'s exact cluster-level
      permutation, 13 clusters).
- [ ] Crypticity stratification, as every block since [[TASK-0260]].

## Acceptance

- [ ] Per-term added-last values with cluster-robust p-values.
- [ ] An explicit answer to "does CTQW add anything over `V_C` alone?".
- [ ] A statement of whether the terms are complementary or whether `V_C`
      subsumes the rest.
- [ ] `RESULTS.md`. Flag `documentation/CTQW_CONTRIBUTION_BRIEF.html` §04 for
      an update — do not edit it here.

## Constraint

If `V_C` subsumes the other four, say so — a one-term result is a *better*
finding than a five-term one, not a diminished version of it. And if some term
turns out to carry signal only in combination, that is genuine complementarity
and equally worth reporting.
