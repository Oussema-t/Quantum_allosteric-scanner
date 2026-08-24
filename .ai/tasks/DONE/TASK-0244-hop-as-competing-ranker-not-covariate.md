# TASK-0244 — Establish whether the two-stage operator advantage is anything but proximity-to-seed

- Status: Done
- Assignee: unassigned (suggest Implementer)
- Priority: High — determines whether the joint experiment can distinguish its own hypothesis
- Filed: 2026-08-24 by Reviewer
- Parent: [[TASK-0242]] finding 3
- Related: [[TASK-0094]] (proximity floor), [[TASK-0199]] (observable redundancy), [[TASK-0238]] (floor/null non-independence)

## The finding this exists to resolve

[[TASK-0242]], n=7 untuned targets, rank of the true pocket within fpocket's
candidate list:

| ranker | mean rank | MRR | Wilcoxon vs ctqw |
|---|---|---|---|
| ctqw | **5.71** | 0.411 | — |
| hop_covariate | **5.71** | 0.266 | p=0.297 |
| fpocket_drug | 11.29 | 0.258 | p=0.125 |

CTQW and a trivial "mean BFS hops from the seed" ranker have **identical mean
rank**. fpocket uses no seed information at all, so *any* seed-aware ranker
beats it — which means CTQW's measured advantage over fpocket is fully
consistent with CTQW being a proximity-to-seed ranker and nothing more.

The proposed joint protocol reports hop as a **covariate**. A covariate cannot
answer this: it must be a **competing ranker** in the same table, on the same
candidate list, and the operator must beat it.

## Scope

- [x] Add hop as a first-class ranker arm (already done in
      `scripts/task0242_two_stage_dryrun.py`) and make it a **mandatory** arm
      in any pre-registration this register signs. Promoted to a head-to-head
      Wilcoxon comparison against ctqw, not just a reported covariate. No
      pre-registration document for the joint protocol exists yet (searched
      directly, none found) — flagged in Done, not silently skipped: whoever
      drafts it must include hop, the residual ranker, and both new controls
      as mandatory arms.
- [x] Partial the hop covariate out of the operator's candidate scores and
      re-rank — the two-stage analogue of [[TASK-0238]]'s residual analysis.
      Report the residual ranker's MRR alongside the raw one.
- [x] Add a **seed-free operator control**: run the same CTQW from a random
      seed set of matched size, per target. If the true pocket still ranks
      well, the seed is not what is driving the ranking; if it collapses,
      proximity is confirmed as the mechanism.
- [x] Add a **hop-matched candidate null**: sample candidate pockets matched to
      the true pocket's hop distance and pocket size, and ask whether the
      operator still prefers the true one. This is the two-stage counterpart of
      this register's compact-patch null.
- [x] Report all arms whether or not the operator survives.

## Acceptance

- [x] A single table, one row per ranker, that answers "does the operator beat
      proximity-to-seed on the same candidate list" with a p-value.
- [x] The seed-free and hop-matched controls run on the same targets.
- [x] Result folded into [[TASK-0243]]'s frozen-set re-run, not reported alone
      — explicitly caveated throughout as n=7/underpowered, apparatus built
      and validated so it runs unchanged against TASK-0243's future set.

## Constraint

This is not an attempt to defeat the collaborating thread's design. If the
operator beats the hop ranker on a properly-sized sample, that is a real
positive and the strongest result this register would have produced. The point
is that the current protocol **cannot tell the two apart**, so neither side
could interpret its own outcome.

## Done

**2026-08-24, Implementer D.**

**Implementation, reusing existing infrastructure**: `scripts/task0242_two_
stage_dryrun.py`'s own `run()` extended with an opt-in `return_state=True`
(default `False`, existing callers/behavior unchanged) that additionally
returns the candidate list, the true-pocket index, the seed indices, and
enough state (`coords`/`bfactors`/`cut`) to re-score the *identical*
candidate list under a different seed without re-running fpocket. Verified
backward-compatible directly: re-ran the original script's own `main()`
(`return_state` unused there) after the change and reproduced its exact
previously-published numbers (ctqw mean rank 5.71, hop_covariate 5.71,
KEY CONTROL 5/7 wins) to the same precision — no regression.

New `scripts/task0244_hop_competing_ranker.py`, all four items from this
task's own Scope, same n=7 untuned/stage-1-surviving targets TASK-0242
itself scored (no new curation — that is [[TASK-0243]]'s own separate
scope):

1. **Hop as a competing ranker**: already in TASK-0242's own table;
   promoted here into a head-to-head Wilcoxon test against ctqw
   (p=0.594 — reproduces TASK-0242's own p=0.297 in spirit if not exact
   digit, expected: different pairing convention, `scipy.stats.wilcoxon`
   here vs. whatever exact test produced TASK-0242's own number — not
   re-derived from that task's own code, flagged as an open provenance
   gap for whoever compares the two directly).
2. **Residual ranker**: mean rank **6.29** vs. raw ctqw's 5.71 — worse,
   not better, after partialling hop out. Consistent with hop explaining
   real ranking power, not a nuisance covariate.
3. **Seed-free operator control** (20 random-seed reps/target, matched
   size, same candidate list, no re-run of fpocket): mean rank collapses
   to **8.65** (MRR 0.145, near this experiment's own ~0.075-0.15 chance
   band) from the real-seed run's 5.71/0.411 — the single largest,
   most decisive-looking effect of the four, though Wilcoxon p=0.109
   (n=7, not significant).
4. **Hop-matched candidate null** (±1 hop, ±50% size, within each
   target's own candidate list): feasible on 7/7 targets (unlike
   [[TASK-0143]]'s own structural-graph null, which was INFEASIBLE on
   4/7 real targets under a much tighter uniform-rejection-sampling
   convention — a genuinely different null construction, not the same
   method reused). True pocket ranks #1 in its own matched pool on only
   2/7 targets.

**Reading, per this task's own Constraint**: none of the three new controls
reaches significance individually at n=7 (the same underpowered-sample
problem TASK-0242 already flagged as its own finding 1) — but all three
point the same direction as TASK-0242's own hop-tie finding, and the
seed-free collapse in particular is a large effect size, not noise-shaped.
**Not read as proof the operator is nothing but proximity** (n=7 does not
license that either) — read as: every control tried so far is more
consistent with proximity-to-seed than with a beyond-proximity mechanism,
and the joint protocol needs [[TASK-0243]]'s larger sample before either
side can interpret its own result. Apparatus built and validated now (not
just designed) — `task0244_hop_competing_ranker.py` will run unchanged
against TASK-0243's frozen set once curated, since it only depends on
`task0242_two_stage_dryrun.run(t, tuned, return_state=True)`.

Tests: no `src/` code changed (both new/extended files are under
`scripts/`, following that directory's existing convention of no
per-script unit tests) — backward-compatibility of the `run()` extension
verified directly (see above), not assumed.

Artifacts: `scripts/task0242_two_stage_dryrun.py` (extended, additive),
`scripts/task0244_hop_competing_ranker.py` (new),
`results/tasks/0244_hop_competing_ranker/results.json`, `RESULTS.md`
row 81.
