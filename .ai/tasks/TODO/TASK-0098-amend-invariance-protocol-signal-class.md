# TASK-0098 Amend INVARIANCE_PROTOCOL's SIGNAL class — beat the domain heuristic, not just random

## Context

- ID: TASK-0098
- Title: Amend `.ai/reference/INVARIANCE_PROTOCOL.md`'s SIGNAL
  classification so the null control asks "does it beat the obvious
  domain heuristic (distance-from-seed)?", not just "does it beat
  random?"
- Status: TODO
- Owner: Architect/Planner
- Source: `__WORK_IN_PROGRESS__/REVIEW-2026-07-13-proximity-confound-and-propagator-semantics.md`,
  task proposal list, item **TASK-0098 (NEW, protocol)**. This is the
  protocol-level generalization of the same failure pattern TASK-0094
  fixes at the code level — see the review's "Meta" section: this is the
  **third** instance of an assumed-gauge symmetry nobody executed (after
  SE(3) rotation over a degenerate null space, and a Clifford-only
  fixed-frame artifact in a quantum-channel object). "The leakage
  firewall guards against *knowing the answer*; nothing guarded against
  the score being *trivially predictable from geometry*. Both are leaks
  — one through labels, one through coordinates."

## Intent Contract

- Outcome: `INVARIANCE_PROTOCOL.md`'s SIGNAL classification criteria are
  amended so that a quantity classified as SIGNAL must be shown to beat
  the strongest known trivial confounder for its domain — not merely
  chance — before it can be reported as a finding. For this repo's
  allostery-detection domain, that confounder is currently
  distance-from-seed (proximity); the amendment should state this
  concretely as a worked example while phrasing the general rule so it
  transfers to future domains/confounders.
- In Scope: `.ai/reference/INVARIANCE_PROTOCOL.md` itself; a cross-link
  from `.ai/invariants/README.md` if that document enumerates
  classification criteria separately; a pointer from this protocol
  amendment to TASK-0094 as the concrete instance that motivated it.
- Out Of Scope: re-auditing every existing `.ai/invariants/INV-XXXX`
  record against the amended criteria — that's a separate sweep (file a
  follow-up if this task's author judges it necessary once the amendment
  lands, don't do it inline here).
- Acceptance Scenarios:
  - Given the amended protocol, when a future reviewer classifies a
    quantity as SIGNAL, then the classification checklist explicitly
    requires stating what the domain's strongest trivial confounder is
    and demonstrating the quantity beats it — "beats chance" alone is
    insufficient per the amended text.
  - Given this repo's own allostery-detection domain, then the amended
    protocol names distance-from-seed as the worked example.
- Constraints And Invariants: this is a documentation/protocol change
  only — no code changes; keep the amendment consistent with the
  existing GAUGE/KNOB/SIGNAL vocabulary rather than introducing new
  terminology.
- Planned Validation: a read-through confirming the amended text is
  unambiguous enough that a future task (like TASK-0094) could have been
  filed directly from the protocol's own checklist, without needing an
  external reviewer to catch the gap first.

## Dependency

- Motivated by TASK-0094 (the concrete code-level fix) — reference it as
  the worked example.
- Can run in parallel with TASK-0097 per the review's sequencing, once
  TASK-0094/0095/0096 land.
- Related: `.ai/reference/INVARIANCE_PROTOCOL.md` (TASK-0051, Done —
  original adoption), `.ai/invariants/README.md`.

## Open Questions

- None — the amendment's content and worked example are specified
  directly by the review's "Meta" section.

## Done

(not yet)
