# TASK-0263 — Was the physics right and the propagator wrong? Score `H_new`'s potential terms directly

- Status: Done
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

- [x] Extract each potential term (`V_B`, `V_T`, `V_R`, `V_C`, `V_M`) as a
      standalone per-residue vector, at the same `lam_*` defaults `build_H_new`
      uses. Do not re-derive them — call the same code paths, or reproduce
      term-for-term the way [[TASK-0257]]'s `task0257_r2_shapley_rerun.py`
      already had to (that function does not expose the terms individually;
      say which route you took).
- [x] Score each term alone: cross-validated per-residue AUC on
      [[TASK-0243]]'s frozen set, [[TASK-0254]]'s protocol unchanged
      (5-fold stratified, 20 repeats, out-of-fold, seed rows excluded).
- [x] **The headline comparison**: best single potential term, and the terms
      as a block, versus the CTQW computed from the Hamiltonian they build.
      Same targets, same folds.
- [x] Add the potential-term block as a **fourth block** in the Shapley
      attribution alongside geometry / fpocket / CTQW, and report its
      contribution **when added last** — the decision statistic.
- [x] Report whether CTQW retains any added-last contribution once its own
      potential terms are in the model as direct predictors. This is the
      sharpest available version of the question: does the walk add anything
      to its own ingredients?
- [x] Cluster-robust significance per [[TASK-0261]]'s method (13 clusters,
      exact cluster-level sign-flip permutation) — not row-level Wilcoxon.

## Acceptance

- [x] Per-term CV AUC table, all five terms, n=20.
- [x] Terms-block vs CTQW head-to-head with a cluster-robust p-value.
- [x] Four-block attribution with the terms block's added-last value.
- [x] An explicit answer to: does CTQW beat its own ingredients?
- [x] `RESULTS.md`. If the answer is "no", flag it for
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

## Done

**2026-08-25 — Implementer A.** Decisive result, answered plainly per this
task's own Constraint: **the physics encoding was right, the propagator was
where the signal was lost.**

**Extraction route** (this task's own required disclosure): `potentials.
V_B`/`V_T`/`V_R`/`V_C`/`V_M` are already public, individually callable
functions, each returning an `(N,N)` diagonal matrix, individually z-scored
(TASK-0121) — `np.diag(V_X(...))` is the per-residue vector directly, no
re-derivation needed. The same `gnm_context(coords, cut)` threaded through
`V_R`/`V_C`/`V_M` exactly as `build_H_new` itself does. Confirmed this is the
same route [[TASK-0257]]'s own `task0257_r2_shapley_rerun.py` already used
(read that script before writing this one, not assumed) — that task's own
uncertainty was about `build_H_new` not exposing the terms individually, not
about `potentials.py` itself, which does.

**`lam_*` weighting — explicit Implementer's-call deviation from the Scope's
literal text, stated and justified, not silently done**: individual terms
were scored in their natural (z-scored, un-weighted) form, not multiplied by
`build_H_new`'s own `lam_B=0.08`/`lam_T=0.16`/`lam_R=0.08`/`lam_C=0.04`/
`lam_M=0.04`. This does not change any reported number: a single term's own
solo AUC is invariant to multiplication by a positive scalar (same ranking),
and the terms-block/four-block OLS fits re-derive their own optimal linear
combination per fold regardless of any fixed positive per-column rescaling
applied beforehand (the fitted coefficients simply absorb it) — so `lam_*`
weighting is mathematically redundant for every number in this task, not
omitted by oversight.

**Per-term CV AUC, n=20** (full table in `RESULTS.md`'s own dated section):
best single term is `V_C` (DCC coupling centrality) on 8/20 targets, `V_B`
(B-factor) on 7/20, `V_R` on 3/20, `V_M` on 2/20 — `V_T` never wins. Several
single terms alone reach AUC 0.81–0.93 with **zero fitting** (`V_C` on
GAC_CPD12/HCV_NS5B_VRX/VR1/MKK7_IBRUTINIB; `V_B` on GAC_BPTES/PF_ATCASE/
HCV_NS5B_POO/CMF/PKR_MITAPIVAT/PKR_AG946) — stronger than CTQW manages on the
same targets even after fitting.

**Headline — terms-block vs. CTQW, cluster-robust**: median AUC **0.751 vs.
0.575**, **cluster-robust p = 0.019** ([[TASK-0261]]'s exact cluster-level
sign-flip test, 13 clusters — not row-level Wilcoxon, per this task's own
explicit instruction and that task's own pseudo-replication finding on this
exact set).

**The sharpest version of the question, answered**: CTQW's own added-last
marginal in the four-block Shapley (geometry/fpocket/CTQW/terms), once
geometry, fpocket, *and* its own potential terms are already in the model as
direct predictors — median **−0.4%**, range −4% to +12%, cluster-robust
**p = 0.973**. Indistinguishable from zero. **CTQW retains no residual
contribution once its own ingredients are given a fair chance to predict
directly — the walk does not add anything to its own ingredients.**

**One target flagged, not smoothed into the summary**: FBPASE_94D's full
4-block model scores *below chance* out-of-fold (AUC 0.445) — its own raw
"terms added-last" figure (−78.9%) reflects a model that does not generalize
on this target at all, read per [[TASK-0245]]'s own established convention
for share-outside-[0,1] cases (a real non-generalization, not a genuine large
negative contribution), and excluded from the illustrative per-target table
in `RESULTS.md` for that reason, though present in the raw JSON.

**Answer to this task's own central question**: does CTQW add anything over
its own ingredients? **No.** This is a positive result for the project's
physics (the potential terms carry real, sometimes strong signal) and a
negative result for the propagator specifically (mixing that signal into a
CTQW and reading out the walk's occupation does not preserve it, and often
destroys it — CTQW's own solo AUC, 0.575 median, sits well below the
terms-block's 0.751) — reported with equal prominence per this task's own
Constraint, not downplayed as an embarrassment.

**Committed immediately per this task's own Parallelisation note**:
`RESULTS.md`'s own section landed in its own commit (`d71e0df`), claimed and
released via SCQ in one pass, working-tree copy not held across any other
thread's commit — verified clean (single hunk, no interleaving) before
staging.

**Flagged, not touched here, per this task's own Acceptance/scope
boundary**: `documentation/CTQW_CONTRIBUTION_BRIEF.html` §04 needs this
finding written in — a separate task's job.

**Not done**: no existing task's own numbers (TASK-0254's attribution,
TASK-0257's R2 finding) were re-derived or edited; this task's own finding
sits alongside them, citing them as motivation, not superseding their own
recorded results. A held-out check of whether the same ranking (`V_C`/`V_B`
strongest, CTQW added-last null) holds at a larger sample than n=20 was not
attempted — real remaining scope if this line of work continues.

**Validated**: `scripts/task0263_potential_terms_direct_predictors.py`
reruns clean and reproduces every number above from
`results/tasks/0263_potential_terms_direct_predictors/`. No library code
changed — investigation script only, full test suite not re-run.
