# TASK-0098 Amend INVARIANCE_PROTOCOL's SIGNAL class — beat the domain heuristic, not just random

## Context

- ID: TASK-0098
- Title: Amend `.ai/reference/INVARIANCE_PROTOCOL.md`'s SIGNAL
  classification so the null control asks "does it beat the obvious
  domain heuristic (distance-from-seed)?", not just "does it beat
  random?"
- Status: Done
- Resolution: done
- Owner: Architect/Planner
- Claimed By: Implementer C (this thread)
- Claimed At: 2026-07-19 21:36
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

**Classified the fix precisely before writing it**: the review's own "Meta"
section frames the proximity confound as the same class of failure as the
ENM/quantum-channel bugs ("assumed-gauge symmetry never executed"). Checked
this against the actual GAUGE/KNOB/SIGNAL vocabulary before amending: the
first two are GAUGE violations (an invariance assumed to hold, that didn't).
The proximity confound is different — `time_averaged_ctqw` occupation is
*correctly* seed-dependent by design (that's the SIGNAL, not a bug); the gap
is that its **null control** only tested against random noise, never against
the domain's actual strongest trivial predictor (distance-from-seed). Amended
the SIGNAL tier specifically, not the GAUGE tier, to keep the amendment
mechanically correct rather than just rhetorically consistent with the
review's own framing.

**`.ai/reference/INVARIANCE_PROTOCOL.md` amended in 5 places** (deliberately
redundant across the document's own existing structure — opening bug list /
classification table / detailed tier section / rule of engagement — matching
how the GAUGE/rotation example is already repeated across all four, not a
single addition in one spot a reader could miss):
1. Opening "two live bugs" list extended to three, with the proximity
   confound explicitly marked as a different tier (SIGNAL, not GAUGE) than
   the first two, and cross-linked to TASK-0094 (fix) and this task (protocol).
2. The three-way classification table's SIGNAL row: "Test form" now reads
   "assert it does, against the domain's strongest trivial confounder — not
   only random/chance"; "Failure means" extended to "or worse, is scoring the
   confounder."
3. New paragraph directly under the table stating the general rule
   ("enumerate the cheapest non-trivial predictor a skeptic would reach for
   first") with distance-from-seed named as this repo's own worked example,
   per the task's own Acceptance Scenario.
4. New "Tier 3b" section (keeps Tier 3's existing random/shuffled controls
   intact, additive rather than replacing) with the concrete rule
   ("AUC must clear both chance and the proximity floor") and the real
   measured consequence (KRAS_G12C's 0.779 beats chance but not the
   proximity floor).
5. New Rule of Engagement #5, matching the existing numbered-rule style,
   plus updated rule #2/#4's bug counts (two -> three, "both" -> "all three").
   Also annotated the Registry's own illustrative `INV-0001` example: flagged
   that its SIGNAL line predates this amendment rather than inventing a
   confounder for that (different-domain) example just to make it look
   complete — per this task's own Out Of Scope, not a re-audit.

**`.ai/invariants/README.md` amended too** (the task's own In Scope
condition: "if that document enumerates classification criteria
separately" — confirmed it does, duplicating the three-class table and a
"Required fields" checklist independently of `INVARIANCE_PROTOCOL.md`):
SIGNAL row and "Required fields" bullet both updated to state the
confounder requirement, plus a short cross-link paragraph pointing to
`INVARIANCE_PROTOCOL.md`'s Tier 3b for the full rule and worked example —
kept short here since the full rationale belongs in one place, not
duplicated at length in two.

**Acceptance Scenarios, checked directly against the amended text**: (1) a
future reviewer classifying a quantity as SIGNAL now hits an explicit
requirement (table row + Tier 3b) to name the domain's strongest trivial
confounder and show the quantity beats it — "beats chance" alone is
stated as insufficient in four separate places, not implied. (2) The
amended protocol names distance-from-seed as this repo's own worked
example, in both the general-rule paragraph and Tier 3b, cross-linked to
TASK-0094's real fix and real numbers (KRAS_G12C 0.779 vs. proximity
floor 0.798/0.781).

**Planned Validation**: read through the amended text end-to-end as a
future task-filer would encounter it (not just diffed the edits) —
confirms a reviewer following the checklist top-to-bottom would reach the
domain-confounder requirement before reaching a "done" classification,
without needing an external reviewer to catch the gap first, matching
this task's own validation bar.

**Out of Scope, confirmed not done**: did not re-audit any existing real
`.ai/invariants/INV-XXXX` record against the amended criteria (the
Registry's own illustrative example is annotated, not silently left
looking complete, but is not a real record) — that remains a separate
sweep for whoever files it next. No code changed — this was a
documentation/protocol amendment only, per this task's own Constraints.
