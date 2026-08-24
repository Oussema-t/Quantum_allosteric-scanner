# TASK-0252 — H6.1, H4.3, H4.4: the three ensemble claims no task addresses

- Status: TODO
- Assignee: unassigned (suggest Explorer first — two of the three may be closable on argument)
- Priority: Medium — lower than [[TASK-0250]]/[[TASK-0251]], but these are the last genuinely-open register entries
- Filed: 2026-08-24 by Reviewer
- Parent: [[TASK-0248]]
- Related: [[TASK-0229.006]] (EAM/COREX), [[TASK-0226]], [[HYP-P13]]

## The three claims

- **H6.1** (Tsai & Nussinov 2014) — all allostery is population redistribution
  on a pre-existing landscape; **"pathways" are high-flux subsets of that
  redistribution, not causal channels**. [[TASK-0248]] confirmed no task
  addresses the unified-mechanism claim itself ([[TASK-0229.003]] tested only
  H6.2, the effector-specificity half).
- **H4.3** (Motlagh et al. 2014) — intrinsic **disorder amplifies** allosteric
  coupling.
- **H4.4** — coupling free energy **does not decompose onto graph edges**.

## Why they are worth an explicit verdict rather than benign neglect

**H6.1 and H4.4 are the theoretical statement of this project's own empirical
result.** Our register has spent months showing that graph-pathway observables
do not beat proximity, and [[TASK-0245]]/[[TASK-0247]] now put numbers on it
(CTQW increment +1% median; its non-distance signal indistinguishable from
degree+euclid). H4.4 says *a priori* that a graph-edge decomposition of
coupling free energy should not be expected to work.

If that is right, our negatives are not a failure of our implementation —
they are a confirmation of a published prediction, and that reframing belongs
in the Phase 1 submission. It converts a pile of negatives into a coherent
result. **This is the highest-value possible outcome of this task and the
reason it is filed.**

**H4.3** is different: it is a testable empirical claim, and it points at
c-Myc/1NKP — the target this register has never been able to score
([[TASK-0080]]: no ground truth). Disorder-amplified coupling is exactly what
would be expected there.

## Scope

- [ ] Verify all citations directly before working against them.
- [ ] **H4.4** — attempt an argument-level resolution first: does the
      partition-function form of coupling free energy in Motlagh et al. admit
      an edge decomposition or provably not? If provably not, this is closable
      without a run, and it becomes an *explanation* for our results rather
      than another open question. If the argument is not clean, state what
      measurement would decide it.
- [ ] **H6.1** — determine whether it is empirically distinguishable from H4.1
      (already TESTED) at all, given our inputs. If it is a reframing of the
      same content, say so and merge the entries rather than carrying a
      permanently-open duplicate.
- [ ] **H4.3** — specify a real test: a disorder predictor (IUPred / metapredict
      / B-factor-derived proxy) against measured coupling on our targets. State
      whether the register's targets have enough disorder variation to have any
      power; if they do not, say so rather than running an underpowered test.
      [[TASK-0242]]'s n=4→n=7 lesson applies.
- [ ] Whatever the outcome, connect it explicitly to [[HYP-P13]] and to
      [[TASK-0245]]/[[TASK-0247]]'s numbers.

## Acceptance

- [ ] Each of the three carries a verdict: TESTED, closed-on-argument, merged
      into another entry, or *undecidable with our inputs* — no plain UNTESTED
      left without a reason.
- [ ] If H4.4/H6.1 resolve in the predicted direction, a paragraph drafted for
      `documentation/PHASE1_SUBMISSION_DRAFT.md` §2 reframing our negatives as
      confirmation of a published prediction.
- [ ] Register STATUS updated for all three, citing this task.

## Constraint

Resist the temptation to run something just to change a status. Two of these
may be closable on argument, and "closed on argument, here is the argument" is
a better outcome than an underpowered run. But do not close on argument what
actually needs a measurement — state which is which.
