# TASK-0263 — Was the physics right and the propagator wrong? Score `H_new`'s potential terms directly

- Status: TODO
- Assignee: **Implementer A**
- Priority: **Highest — cheapest decisive test remaining, and it answers a question the whole CTQW line rests on**
- Filed: 2026-08-25 by Reviewer
- Related: [[TASK-0254]], [[TASK-0257]], [[TASK-0259]], [[TASK-0247]], `src/allostery/hamiltonians.py`

## The question

`build_H_new` encodes real structural physics in its potential terms — burial,
packing, contact structure, mode content (`V_B`, `V_T`, `V_R`, `V_C`, `V_M`,
weighted by `lam_*`). [[TASK-0257]] R2 replaced `V_R`'s `context["degree"]`
burial proxy with real SASA and the downstream CTQW marginal did not move.

Bartosz's framing, 2026-08-25: *"We tried to introduce these to the
Hamiltonians of the CTQW some time ago. Maybe the route was reasonable, but
simply not because of CTQW at all."*

That is a testable claim and nobody has tested it. **A walk mixes a sharp
local field into a smooth diffusion profile.** If the potential terms carry
real signal that the walk then destroys, the encoding was right and the
propagator was the mistake — which is a completely different conclusion from
"the physics was wrong," and points at a different Phase 2.

## Scope

- [ ] Extract each potential term (`V_B`, `V_T`, `V_R`, `V_C`, `V_M`) as a
      standalone per-residue vector, at the same `lam_*` defaults `build_H_new`
      uses. Do not re-derive them — call the same code paths, or reproduce
      term-for-term the way [[TASK-0257]]'s `task0257_r2_shapley_rerun.py`
      already had to (that function does not expose the terms individually;
      say which route you took).
- [ ] Score each term alone: cross-validated per-residue AUC on
      [[TASK-0243]]'s frozen set, [[TASK-0254]]'s protocol unchanged
      (5-fold stratified, 20 repeats, out-of-fold, seed rows excluded).
- [ ] **The headline comparison**: best single potential term, and the terms
      as a block, versus the CTQW computed from the Hamiltonian they build.
      Same targets, same folds.
- [ ] Add the potential-term block as a **fourth block** in the Shapley
      attribution alongside geometry / fpocket / CTQW, and report its
      contribution **when added last** — the decision statistic.
- [ ] Report whether CTQW retains any added-last contribution once its own
      potential terms are in the model as direct predictors. This is the
      sharpest available version of the question: does the walk add anything
      to its own ingredients?
- [ ] Cluster-robust significance per [[TASK-0261]]'s method (13 clusters,
      exact cluster-level sign-flip permutation) — not row-level Wilcoxon.

## Acceptance

- [ ] Per-term CV AUC table, all five terms, n=20.
- [ ] Terms-block vs CTQW head-to-head with a cluster-robust p-value.
- [ ] Four-block attribution with the terms block's added-last value.
- [ ] An explicit answer to: does CTQW beat its own ingredients?
- [ ] `RESULTS.md`. If the answer is "no", flag it for
      `documentation/CTQW_CONTRIBUTION_BRIEF.html` §04 — but **do not edit
      the brief in this task**, see the parallelisation note below.

## Constraint

If the potential terms beat the CTQW built from them, that is a **positive
result for the project's physics** and a negative for the propagator — report
it as both, with the same prominence. It would mean the register spent its
effort on the wrong half of the construction, which is a useful and
publishable finding, not an embarrassment.

## Parallelisation note

`RESULTS.md` is the contended file in this batch ([[TASK-0244]] and
[[TASK-0260]] both lost rows to collisions). Write your section, but take
`GIT-COMMIT` via the SCQ and commit it in one shot; do not hold a working-tree
copy across another thread's commit.
