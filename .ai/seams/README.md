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

## A failure mode found the hard way: scope selection, not absence ([[TASK-0232]], 2026-08-24)

Three real cross-unit invariants ([[SEAM-0015]], [[SEAM-0016]], [[SEAM-0017]])
went unregistered through a three-week window with no new seam filed at all
(SEAM-0013/0014 dates to 2026-08-05) — despite the sweep producing an
invariant record for the *exact* quantity one of them broke
([[INV-0006]], seed definition). Reading `INV-0006` before this task would
not have caught it: the record swept *how many* residues the seed contains
(a real KNOB, correctly characterized) and never asked *whether the seed was
an active site at all* — the axis the actual defect lived on
([[TASK-0216]], 9 of 13 targets).

**The lesson, stated so it doesn't recur**: when auditing an invariant
record for coverage, checking "does a record exist for this quantity" is
not sufficient — a record can exist, be correct about the axis it measured,
and still miss the defect because the defect lives on a *different axis of
the same quantity*. The audit question has to be "does an existing record's
own scope actually cover the failure being checked for," not just "is there
a record with this name." A GAUGE/KNOB/SIGNAL table with zero rows on the
provenance axis is not evidence provenance is fine — it is evidence no one
has classified it yet, which is the free-axle warning this registry's own
README already states, just easier to miss when a same-named record for a
*different* axis of the same quantity is sitting right there looking like
coverage.
