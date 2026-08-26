# TASK-0275 — Decompose the potential terms: `V_C` alone beats CTQW, and we lumped it

- Status: TODO
- Assignee: unassigned (suggest Implementer A — owns TASK-0263, reuses its cached CV)
- Priority: **High — cheap, and it converts TASK-0263's headline into a much sharper and more credible claim**
- Filed: 2026-08-26 by Reviewer
- Related: [[TASK-0263]], [[TASK-0254]], [[TASK-0257]], [[TASK-0259]], [[TASK-0261]], [[TASK-0276]] (the same ceiling logic, at the discrimination level rather than the feature level)

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

## Apo AND holo — both flavours, added 2026-08-26

**Scope correction (Bartosz, 2026-08-26).** As first filed this task was
apo-only, which measures *performance* and says nothing about what these terms
could do given the right conformation. [[TASK-0276]] establishes a ceiling by
looking at holo; the same logic applies here, at the feature level, and is
more actionable because it names which physics is recoverable.

- [ ] Compute every term **twice**: on the apo structure (performance, the
      real prediction task) and on the holo structure (ceiling).
- [ ] Report the **per-term apo→holo gap**. That gap is "the cost of not
      having the bound conformation", resolved per physical term rather than
      as one aggregate.
- [ ] **Pre-registered prediction**: the residual correlates with apo
      crypticity at ρ=−0.771 ([[TASK-0259]]). So the terms should gain most on
      holo **specifically for the cryptic targets** and least for the
      already-open ones ([[TASK-0254]] part B: 9 of 20 are ≥80% open in apo).
      If the gap is uniform across cryptic and open targets, crypticity is not
      what the apo penalty is made of, and [[TASK-0259]]'s correlation needs
      re-reading.
- [ ] Also run the CTQW arm on holo, so the headline comparison exists in both
      flavours: does CTQW beat `V_C` when *both* are given the bound
      conformation? If CTQW's deficit persists on holo, the propagator is the
      problem independent of conformation — which is a stronger version of
      [[TASK-0263]]'s finding than anything currently established.

### Leakage status per feature — not uniform, do not run a blanket holo sweep

| feature | holo arm | why |
|---|---|---|
| `V_C`, `V_B`, `V_R`, `V_M`, `V_T` | **run it** | protein-only quantities; they see the drug's structural imprint but not the drug. Ceiling, not predictor. |
| geometry (degree, euclid, hop) | **run it** | same status. |
| CTQW | **run it** | same status. |
| SASA | **run it**, flagged | burial changes on binding; the imprint is stronger here. |
| **fpocket** | **exclude, or report separately and label maximally leaky** | it is a cavity detector, and the holo cavity is drug-shaped. Scoring it on holo trivially recovers the label and measures nothing. |

**Every number from the holo arm is a ceiling and must be labelled as one in
`RESULTS.md`.** None of it may be reported as predictive performance, and none
of it may be mixed into the apo attribution table without a column heading
saying which flavour it came from.

## Relationship to [[TASK-0276]] — read together, not in isolation

The two are the same ceiling question at different levels:

- **This task** asks, per physical term, *how much performance is lost by
  having to use apo* — an attribution of the apo penalty across `V_C`, `V_B`,
  geometry, CTQW. Actionable: it names which physics is recoverable.
- **[[TASK-0276]]** asks whether the allosteric site is distinguishable **at
  all** in holo — an existence question, and the harder ceiling.

**If this task's holo arm shows large per-term gains while [[TASK-0276]] finds
no allosteric-vs-orthosteric separation, the two results are in tension, and
that tension is itself the finding**: the terms would be tracking *the drug's
structural imprint* rather than anything about allostery. Whichever of the two
runs second must check its result against the other's rather than reporting in
isolation.

[[TASK-0276]] was picked up before this note was written — **pass this
relationship to whoever owns it.**

## Acceptance

- [ ] Per-term added-last values with cluster-robust p-values.
- [ ] An explicit answer to "does CTQW add anything over `V_C` alone?" — in
      **both** the apo and holo flavours.
- [ ] A per-term apo→holo gap table, every number labelled by flavour, with
      the pre-registered crypticity prediction judged.
- [ ] A statement of whether the terms are complementary or whether `V_C`
      subsumes the rest.
- [ ] `RESULTS.md`. Flag `documentation/CTQW_CONTRIBUTION_BRIEF.html` §04 for
      an update — do not edit it here.

## Constraint

If `V_C` subsumes the other four, say so — a one-term result is a *better*
finding than a five-term one, not a diminished version of it. And if some term
turns out to carry signal only in combination, that is genuine complementarity
and equally worth reporting.
