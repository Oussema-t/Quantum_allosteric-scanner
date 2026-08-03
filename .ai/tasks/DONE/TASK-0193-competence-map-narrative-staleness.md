# TASK-0193 `COMPETENCE_MAP.md`'s per-target narratives contradict its own current table

## Context

- ID: TASK-0193
- Title: mark or refresh the per-target narrative sections, which end at
  [[TASK-0129]] and state verdicts the document's own current
  ([[TASK-0130]]) table reverses.
- Status: Done
- Resolution: done
- Resolution Note: 3 narrative sections given supersession banners matching the existing table convention; found+flagged a 4th, more serious staleness point beyond the filing's own scope (the headline table's CARDIAC_MYOSIN row itself predates TASK-0124's apo swap already reflected in the narrative below it); no numbers recomputed
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: Reviewer thread, 2026-08-03, finding F6.
- Priority: **P2 — no number is wrong; the document is internally
  contradictory in a way a careful reader survives and a skimming referee
  does not.**
- Dependency: [[TASK-0192]] (soft — both edit the same KRAS section; do them
  together or sequence them to avoid a collision).

## Why this matters

`COMPETENCE_MAP.md` handles supersession carefully for its **tables**: the
[[TASK-0129]] and [[TASK-0118]] tables both carry explicit headings —
*"superseded above — kept for the old-vs-new record, no longer this
document's current state."* That is the right convention, applied well.

The **per-target narrative sections that follow them** do not carry it:

| Section | Heading claims | Current table (`:147`, TASK-0130) says |
|---|---|---|
| `:297` KRAS_G12C | *"the actual result is still below floor"* | actual 0.5901 **clears** floor 0.4818, `NO_FAILURE_DETECTED` |
| `:331` BCR_ABL1 | narrative ends at TASK-0129 | — |
| `:404` CARDIAC_MYOSIN | narrative ends at TASK-0129 | — |

A reader who reaches `:297` after passing two explicitly-superseded tables has
no signal that this section is also historical. The heading reads as a current
claim and contradicts the document's own headline row.

Low severity, genuinely cheap, and it sits in the document [[TASK-0184]] will
pull most of its per-target evidence from.

## Intent Contract

- Outcome: every per-target narrative section either carries the same dated
  supersession banner the tables above it use, or is refreshed to the current
  [[TASK-0130]] state.
- Why required, not assumed: the document already has the right convention.
  This is applying it consistently, not inventing one.
- In Scope:
  - Add supersession banners (preferred — cheapest, and preserves the
    old-vs-new record this project values) **or** append a dated "current
    state" paragraph to each narrative.
  - Fix the three section **headings** specifically — they are what a skimmer
    reads.
  - Add the [[TASK-0155]] caveat to KRAS's narrative if [[TASK-0192]] has not
    already (coordinate; do not double-edit).
- Out Of Scope:
  - Recomputing anything.
  - Restructuring the document. Chronological-narrative-plus-current-table is
    a deliberate, working design.
- Constraints And Invariants:
  - Preserve the historical text verbatim. The value of these sections is the
    old-vs-new record.
  - Use the exact banner wording the existing superseded tables use, so the
    convention reads as one convention.
- Planned Validation:
  - Read the document top-to-bottom as a first-time reader: is there any point
    at which a stale claim reads as current? That is the acceptance test.

## In Progress

—

## TODO

- [x] Banner or refresh `:297` (KRAS_G12C), including the heading.
- [x] Banner or refresh `:331` (BCR_ABL1).
- [x] Banner or refresh `:404` (CARDIAC_MYOSIN) — see Done section, this one
      was not the simple case the filing anticipated.
- [x] Coordinate the KRAS section with [[TASK-0192]] — TASK-0192 (this thread,
      2026-08-03, same session) already added the genotype caveat; this task
      added the heading/supersession banner alongside it, not a second
      duplicate caveat.
- [x] Top-to-bottom read-through as acceptance — found and fixed 3 more stale
      "reads as current" points beyond the filing's own 3, see Done section.

## Dependency

- [[TASK-0192]] — same KRAS section. Sequence, do not parallelize.
- [[TASK-0130]] (Done) — the current state being reconciled to.

## Open Questions

- Banner or refresh? Banner is cheaper and preserves the record; refresh reads
  better for a referee. Recommendation: banner, because [[TASK-0184]] pulls
  evidence from the current table anyway, not from the narratives.

## Done

**2026-08-03, Implementer B.** Fixed the 3 headings/narrative sections the
filing named, using the exact `SUPERSEDED`/banner convention the tables
above them already use (not a new convention) — historical text preserved
verbatim in all 3, nothing recomputed:

- **KRAS_G12C** (`### ... — "ceiling below floor" is retracted...`): heading
  reworded to state plainly that the narrative ends at TASK-0129 and is
  superseded; a banner points to TASK-0130's current table (actual now
  clears floor). Sequenced after [[TASK-0192]] (same session, same thread)
  — TASK-0192's own genotype caveat is left untouched, this task's banner
  sits directly above it, no duplicate caveat written.
- **BCR_ABL1**: heading reworded + banner added noting the narrative's own
  numbers (floor 0.5817/ceiling 0.6716/actual 0.5305) are pre-TASK-0130 and
  slightly stale, even though the qualitative diagnosis (`NO_SIGNAL_IN_APO`)
  happens to still match the current table.
- **CARDIAC_MYOSIN — the one that wasn't the simple case.** Read the
  section fully before writing a banner, per this task's own acceptance
  test, and found something the filing's own table didn't check for:
  **the headline table above these narratives is itself the stale one for
  this target, not the narrative.** The CARDIAC_MYOSIN section's own
  chronology already runs past TASK-0130 (dated 2026-07-18) to
  [[TASK-0124]] (2026-07-20, apo replaced 5TBY→8QYP, N 950→704) and ends at
  real numbers (floor=0.5679, actual=0.5176, `NO_SIGNAL_IN_APO`, −65.4%)
  that were never propagated up to the headline table, whose own
  CARDIAC_MYOSIN row (floor=0.7921, actual=0.7272,
  `BEATS_CHANCE_NOT_FLOOR`) is still computed on the retired 5TBY
  structure. Confirmed directly (not assumed) via `grep -n "5TBY\|N=950\|
  N=704"` across the file — the "`N drops 950 → 704`" sentence inside the
  CARDIAC_MYOSIN section itself is the confirming evidence. Fixed by: (1)
  reworded the CARDIAC_MYOSIN heading to say plainly that the section's
  OWN ending, not the headline table, is this document's real current
  state for that target; (2) added a caveat directly under the headline
  table's CARDIAC_MYOSIN row pointing down to the section; (3) added a
  third caveat to the "Cross-target reading" section's own CARDIAC_MYOSIN
  permutation-null bullet (ceiling 0.8297), which is the same 5TBY-era
  number carried one level further and would otherwise have read as
  current too. None of these three additions changes a number — flags
  only, per this task's own Constraint and Out of Scope (no recompute).
  Filed as a natural follow-up, not done here: propagating the
  CARDIAC_MYOSIN section's own already-computed TASK-0124 row up into the
  headline table directly (a table edit, arguably still "not a recompute"
  since the number already exists in the document — left to a task that
  explicitly owns table maintenance rather than assumed in scope here).

Top-to-bottom read-through (the task's own acceptance test) surfaced this
CARDIAC_MYOSIN finding — the filing's own table only flagged 3 stale
points; the actual document had (at least) 4, and the 4th was the more
serious one (a "current" table being wrong, not a historical section
being mistaken for current).
