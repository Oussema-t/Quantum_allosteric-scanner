# TASK-0253 — TASK-0243's frozen set: an unresolvable seed, a contradicted claim, and 36% stage-1 loss

- Status: TODO
- Assignee: unassigned (suggest whoever owns [[TASK-0243]]'s curation)
- Priority: **High — the frozen set is now the evidentiary basis for TASK-0249's headline and for the joint experiment**
- Filed: 2026-08-24 by Reviewer
- Parent: [[TASK-0243]], surfaced by [[TASK-0249]]
- Related: [[TASK-0242]], [[TASK-0216]], [[TASK-0217.003]]

## Two defects, one already found and one measured here

**1. Unresolvable active-site seed, contradicting the curation's own claim.**
[[TASK-0249]] found `HIV_INTEGRASE_MUT871` and `HIV_INTEGRASE_MUT916` (apo
`1M9D`) have an **empty active-site seed on all four chains** — confirmed
directly. [[TASK-0243]]'s Done section states "zero fell back to a top-degree
proxy". Both cannot be true. The pair was handled correctly downstream
(counted as attempted-target failures, kept in every denominator), but the
curation's own claim needs correcting at the source.

**2. Stage-1 recall is 64%, and it reproduces exactly.**
In [[TASK-0249]]'s two-stage arm, **14 of 22** attempted targets survived —
fpocket never proposed the true pocket for the other 8. [[TASK-0242]] measured
**7 of 11** on a completely different target set. Two independent sets, same
64%. This is a stable property of the pipeline, not sampling noise.

That matters because a within-candidate ranking metric is **blind to those 36%
by construction**. [[TASK-0249]] handled it correctly (denominator = targets
attempted). Any future run, ours or the collaborating thread's, must do the
same — and the joint pre-registration should name it explicitly.

## Scope

- [ ] Re-verify the seed for every target in the frozen set, not just the two
      that failed. State the method and show the count. Correct
      [[TASK-0243]]'s "zero fell back" claim to whatever is true.
- [ ] For `1M9D` specifically: determine whether a usable apo exists for HIV
      integrase, or whether the pair should be dropped. Do not substitute a
      structure without the [[TASK-0209]] VALID check and a live RCSB
      confirmation ([[TASK-0169]] is the precedent for why).
- [ ] Characterise the 8 stage-1 failures: is fpocket missing the pocket, or
      is `MIN_HOP` filtering it out after fpocket found it? These are very
      different problems and the current pipeline reports them identically.
- [ ] If `MIN_HOP` is removing true pockets, report how often — that would make
      the distality filter itself a source of false negatives, and it is a
      parameter the joint protocol proposes to freeze.
- [ ] Publish stage-1 recall as a standing pipeline metric alongside any
      two-stage result, so it is never implicit again.

## Acceptance

- [ ] Seed provenance table for all 22 targets, with the corrected claim.
- [ ] Verdict on the HIV integrase pair: fixed, replaced, or dropped.
- [ ] Stage-1 failures decomposed into fpocket-miss vs MIN_HOP-removal.
- [ ] [[TASK-0243]]'s Done section amended rather than left contradicted.

## Constraint

[[TASK-0249]]'s headline is not in question here — it handled both defects
correctly. This is about the frozen set being trustworthy for everything that
comes next, including a jointly-signed experiment where a curation error found
later would discredit both threads' result at once.
