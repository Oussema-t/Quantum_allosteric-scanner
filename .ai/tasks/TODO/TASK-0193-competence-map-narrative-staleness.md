# TASK-0193 `COMPETENCE_MAP.md`'s per-target narratives contradict its own current table

## Context

- ID: TASK-0193
- Title: mark or refresh the per-target narrative sections, which end at
  [[TASK-0129]] and state verdicts the document's own current
  ([[TASK-0130]]) table reverses.
- Status: TODO
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

- [ ] Banner or refresh `:297` (KRAS_G12C), including the heading.
- [ ] Banner or refresh `:331` (BCR_ABL1).
- [ ] Banner or refresh `:404` (CARDIAC_MYOSIN).
- [ ] Coordinate the KRAS section with [[TASK-0192]].
- [ ] Top-to-bottom read-through as acceptance.

## Dependency

- [[TASK-0192]] — same KRAS section. Sequence, do not parallelize.
- [[TASK-0130]] (Done) — the current state being reconciled to.

## Open Questions

- Banner or refresh? Banner is cheaper and preserves the record; refresh reads
  better for a referee. Recommendation: banner, because [[TASK-0184]] pulls
  evidence from the current table anyway, not from the narratives.

## Done

—
