# Shared Pitfalls

Add repeated failure patterns, false assumptions, or tool traps that should not be rediscovered.

## P-0001 — "Invariant on our test set" is a trigger, not a green light

- Pattern: a metric/scorer passes every test in the suite, and that gets read as
  verification. It only proves the suite didn't sample the transformation that breaks it.
- Evidence (this repo): two real bugs — ANM cumulative overlap moving 0.34→0.90 under a
  global rigid rotation (mode selection by index `w[6:]` instead of by eigenvalue, silently
  wrong when the contact graph was rank-deficient), and a "covariant vector invariant" that
  was only invariant under the Clifford subgroup, not generic SU(2) (4× drift). Both were
  invisible to every per-structure/per-frame unit test that existed at the time; both died
  to a ~12-line metamorphic test once someone ran the group instead of assuming it.
- Corollary: the discriminating test is almost never the first one you reach for — it's the
  symmetry that feels too obvious to check. And multi-turn agreement (human or agent, many
  rounds of confident prose) is not verification; neither bug above was caught by discussion,
  only by execution.
- How to apply: see [[INVARIANCE_PROTOCOL]] (`.ai/reference/INVARIANCE_PROTOCOL.md`) — every
  reported quantity needs its GAUGE/KNOB/SIGNAL transformation table classified *before* it's
  reportable, not after a bug is found the hard way.
- Source: `__WORK_IN_PROGRESS__/SUGGESTION.md` (absorbed here, [[TASK-0051]] — file removed
  as a freestanding doc since its content is now this entry plus `INVARIANCE_PROTOCOL.md`'s
  own "Rule of engagement" section, not a separate thing to keep in sync).

## P-0002 — A computed "ceiling" is not automatically above the floor

- Pattern: a floor/ceiling/headroom framing (`ceiling = best score reachable with the
  labels in hand`) is set up assuming `ceiling >= floor` by construction — that a
  fully-informed, label-using search can always at least match a trivial baseline it has
  no special access to. This is not guaranteed, and was not checked before being assumed.
- Evidence (this repo, [[TASK-0046]]/[[TASK-0082]], 2026-07-14): a real 60-trial random
  search over `H_new`'s entire physical-scalar space (`ceiling.ceiling_search`, CTQW
  propagation, the answer key in hand throughout) produced KRAS_G12C's ceiling AUC =
  0.5239–0.5250 — **below** that same target's proximity floor (0.798,
  `euclid_from_seed_centroid`/`hop_from_seed`/`degree_centrality`, [[TASK-0094]]). Every
  point in the searched 8-dimensional parameter space, evaluated against the real labeled
  pocket, scored worse than a baseline that only knows Euclidean/graph distance from the
  seed. The operator family's best case does not clear geometry, not just its default
  case.
- Corollary: `headroom = (actual - floor) / (ceiling - floor)` silently produces a
  meaningless (here, negative-denominator) number when this happens — the formula does
  not fail loudly, it just outputs a fraction nobody should read as "% of the gap closed."
  Check `ceiling > floor` explicitly, per target, before computing or reporting headroom
  — do not assume the ceiling search's access to labels made this check unnecessary.
- How to apply: any target's floor/ceiling/headroom row must state whether `ceiling >
  floor` held *before* a headroom percentage is computed; if not, report that fact as the
  finding (a stronger, more informative "honest NO" than a degenerate fraction would be),
  per [[TASK-0082]]'s own competence-map framing.
- Cross-reference: [[Q-0003]] (`.ai/memory/questions/architect-planner/open/`) — raised to
  the Architect/Planner: does this finding call into question whether a floor/ceiling/
  headroom framing is the right lens for this operator family at all, or is it scoped to
  this one target?
- **Note, same day**: an independent Architect/Critic-overlay pass
  (`REVIEW-2026-07-15b-ceiling-search-methodology.md`) reached this same finding and
  filed [[TASK-0116]] (60 blind random draws over ~8 dimensions is weak evidence for a
  *negative* claim specifically) and [[TASK-0117]] (unvalidated `t_max`/`n_steps`,
  shared with every other headline AUC in this project). This pitfall's "check `ceiling
  > floor` before reporting headroom" lesson stands regardless; whether *this specific
  instance* (`ceiling < floor` for KRAS_G12C) survives denser search / validated
  propagator parameters is now separately tracked by those two tasks, not yet resolved.