# TASK-0379 — Is the seed set a fourth overfitting axis, and what seeding rule is actually physical?

- Status: TODO
- Owner: **Implementer**
- Priority: **High. The submission states its own multiplicity as "221 chances per target" — if the seed is a free axis, that number is wrong in our favour.**
- Filed: 2026-09-12 by Reviewer thread (id via `claim.py reserve-next`)
- Source: Team Lead, 2026-09-12 — *"if we can already show that we can 'overfit' using hamiltonian / operator / method choice … then maybe we can also do so by choosing a seed set"*
- Related: [[TASK-0102]], [[TASK-0325]], [[TASK-0336]], [[TASK-0338]], [[TASK-0378]], [[HYP-P8]]

## Why this matters more than it looks

Our own Section 1 says: *"with thirteen operators and seventeen scores there are
**221 chances per target**, and reporting the best of them is ordinary practice in
this field."* That sentence is the submission's honesty about its own multiplicity.

**It counts two axes. The seed set is a third, and nobody has counted it.** If
seed choice spans a material range of achievable AUC, then 221 understates the
real search space **in our own favour**, and the sentence needs correcting before
a reviewer does it for us.

[[TASK-0378]] just established that the *computation* is exactly reproducible and
that every source of spread is a **choice**. The seed is the one choice whose
capacity has never been measured.

## What the register already says — and it predicts a null

[[TASK-0102]] ran 40 biologically-uninformed single-residue seeds on BCR_ABL1:

> **A strong majority (70–75%) of arbitrary, biologically-uninformed single-residue
> seeds reproduce comparable floor-clearing performance against the same pocket
> label.** The good AUC is predominantly a property of `H_new`'s fixed
> ground-state shape (94.5% ground-mode weight), not evidence of
> active-site-to-pocket coupling.

**That cuts against the hypothesis**, and it is the right pre-registration: if
most arbitrary seeds already reproduce the number, seed *optimisation* has little
left to gain. **If Arm A nevertheless finds a large span, [[TASK-0102]]'s scope
was too narrow** — one target, one operator, single-residue seeds only — and that
is itself the finding.

## Arm A — the capacity ceiling (the Team Lead's "bizarre" option, made rigorous)

**Question:** with operator and score **fixed**, how much of the AUC range can
seed choice alone reach?

- **Do not frame it as "can we hit AUC 1.0".** Best-of-N over seed sets will reach
  a high number by chance, exactly as best-of-884 reached 137 families against a
  null of 99.8. **The measurable quantity is the excess over a matched null**, and
  without one this arm proves nothing. Same discipline as [[TASK-0336]]/[[TASK-0338]].
- **Report the distribution, not the maximum.** Sample seed sets (random residues,
  random surface patches, random pockets of matched size), score each, and report
  the **span** and the **percentile of the true active site** within it. A true
  active site sitting at the 50th percentile of arbitrary seeds means the seed
  carries nothing; sitting at the 99th means it carries something.
- **Match on size.** Seed-set cardinality changes the answer on its own; compare
  like with like or the result is a size effect wearing a biology costume.
- **Then the second-order question the Team Lead actually wants**: for the
  best-scoring seed sets, *where are they*? If they cluster on something
  identifiable — communication hubs, conserved residues, the pocket itself — that
  is a finding. If they are arbitrary, it is a capacity result. **Both are
  publishable and they must be distinguished before looking.**

## Arm B — what seeding rule is physical? (the more valuable half)

The challenge says *"seeded at the active site."* **That phrase is not a
definition**, and we have never justified ours against alternatives.

Candidate rules, each defensible and each cheap to score on the existing cohort:

| rule | rationale |
|---|---|
| UniProt active-site annotation (**current**) | what we ship; annotation-derived, not structural |
| Catalytic residues only | the narrowest chemically meaningful definition |
| Ligand-contact residues in the holo form | what the site *does*, not what it is called |
| Full binding pocket (fpocket/PASSer on the orthosteric site) | structural, method-consistent with the candidate side |
| Pocket centroid, single point | the minimal control — if this ties the others, the seed set carries nothing beyond location |

**Score all five on the same cohort with the operator and score fixed.** The
interesting outcomes are (i) they all tie, which says seed definition is not
load-bearing and simplifies every future run, or (ii) one wins materially, in
which case we have been using the wrong one and should say so.

## Constraints

- **Fix the operator and score before starting.** This task measures one axis; a
  sweep over two axes at once cannot attribute anything.
- **Every arm needs its matched null stated before it runs** — the standing
  discipline, and the reason this register's negatives are credible.
- Cluster-robust inference by protein ([[TASK-0337]]). Family counting, not
  protein counting.
- **No change to the shipped seeds, residues or numbers.** This measures capacity
  and alternatives; changing what we ship is a separate decision.
- Per `COMMON.md`'s standing rule: read what produces each arm before trusting a
  number, including [[TASK-0102]]'s own.

## Pre-registered prediction

**Arm A: the true active site sits unremarkably inside the arbitrary-seed
distribution, and the best-of-N excess over the matched null is small** —
[[TASK-0102]] and [[HYP-P8]]'s ground-mode-dominance finding both point that way.
**Arm B: the five rules tie**, for the same reason — if `H_new`'s ground state
dominates the score, the seed's precise definition cannot matter much.

**If either prediction fails, it is the more interesting outcome**, and in Arm A's
case it means the submission's "221 chances per target" is an undercount that must
be corrected.

## What follows for the submission, either way

- **If seed capacity is small**: the 221 figure stands, and we can say the seed
  axis was *measured* rather than assumed — which is stronger than silence.
- **If it is large**: the multiplicity sentence is wrong in our favour and gets
  corrected. That is the kind of correction this project has already made four
  times, and making it ourselves is worth more than having it found.
