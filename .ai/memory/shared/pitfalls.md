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