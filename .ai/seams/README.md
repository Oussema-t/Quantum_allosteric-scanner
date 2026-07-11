# Seams

A seam is a shared boundary between two or more units (tasks, modules, branches)
where an invariant must hold across the boundary for the composition to be
correct. Full rationale and method: [`SEAM_PROTOCOL.md`](../reference/SEAM_PROTOCOL.md)
(TASK-0050).

## One file per seam

`SEAM-0001-slug.md`, permanent id, never reused or renumbered on move — same
convention as `.ai/tasks/`.

## Required fields (every seam file)

- `units` — the units on either side of the boundary (`producer -> assembly -> consumer`).
- `invariant` — stated as an assertion (`X ∩ Y == ∅`, `provenance(a) == "frozen"`),
  never prose alone.
- `owner` — a real, resolvable `TASK-XXXX`. Never `TBD` — an unowned seam is
  the defect condition this registry exists to prevent.
- `seam-test` — an executable check that exercises the invariant *across* the
  units. If a unit test on either side could catch it, it is not a seam-test.
  May be `xfail` while `OPEN`, but must exist once a seam is registered.
- `status` — `OPEN` | `VERIFIED` | `WAIVED(reason, expiry)`. An expired
  waiver fails the green-bar gate below.
- `provenance` — how this seam was found (a review, a sweep, a task filing)
  and any decision still needed.

## Gates

1. **Definition-of-done addendum.** A task may not move to `DONE` if it opens
   a seam (its output is consumed by another unit, or it splits a
   responsibility a previous unit held whole) without registering it here.
2. **Green-bar addendum.** The repo is not green if any `OPEN` seam has no
   seam-test (an `xfail` counts). `WAIVED` requires a reason and expiry;
   an expired waiver fails the bar.

## The sweep

Seams are found by a dedicated edge-discovery pass (owned by General Critic,
per the source protocol — node-execution agents will not find them, a seam
is by definition outside any single task's scope), run at phase boundaries
and before multi-task merges. See [[TASK-0053]] for the first one.
