# TASK-0115 Name and gate the repeated-exposure risk across the review cycle

## Context

- ID: TASK-0115
- Title: `frozen_context`/LOPO/TASK-0100 gate *code-level* parameter and
  operator selection against true labels. Nothing gates the ~15 human
  review cycles this project has already run, each looking at the same
  3 targets' real AUCs before deciding what to rename, re-scope, or
  re-frame — a researcher-degrees-of-freedom exposure no existing
  protocol document accounts for.
- Status: Done
- Owner: Architect/Planner
- Source: `REVIEW-2026-07-15-execution-plan-gap-audit.md`, finding #4.
- Crit Ref: this is a process/documentation gap, not a code defect —
  every individual review decision this session (heat→
  ground_state_relaxation, the floor definition, SEAM-0008's
  reassignment, the GSR causal-claim correction) was well-evidenced on
  its own terms. The risk is cumulative and structural: the same 3
  proteins' true labels have been visible to every decision-maker
  across every review, and no code-level gate (`frozen_context`
  included) can detect a human choosing which claim to make *based on*
  having seen how it would land on those 3 answers.

## Intent Contract

- Outcome: an explicit, written statement — in
  `INVARIANCE_PROTOCOL.md` or a new short protocol note — that no claim
  in `RESULTS.md` is to be treated as final/submission-ready until it
  has been checked against TASK-0081's generalization set (targets none
  of this project's review history has been exposed to), plus a
  one-line addition to `EXECUTION_PLAN.md`'s critical path making that
  dependency explicit rather than implicit.
- In Scope:
  - add a short section to `INVARIANCE_PROTOCOL.md` (or
    `SEAM_PROTOCOL.md`, whichever fits better — Implementer/Architect's
    call) naming this risk class explicitly, distinct from the
    GAUGE/KNOB/SIGNAL classification (which is about transformations of
    a single measurement, not about repeated human exposure to a fixed
    small answer set).
  - cross-link into TASK-0081 (generalization set) as the concrete
    mitigation already planned, and into TASK-0100 (operator-sweep
    architecture) noting this is a distinct, broader risk than the
    multiple-comparisons gate TASK-0100 already handles at the code
    level.
  - update `EXECUTION_PLAN.md`'s critical path or Phase 5 framing to
    state plainly that TASK-0081 gates *finality* of any claim, not
    just "encouraged extra evidence."
- Out Of Scope:
  - building any new code/gate — there is no code-level fix for a
    human-review-history risk; this task is documentation + explicit
    sequencing, not tooling.
  - re-litigating any specific past review decision named above as an
    example — they stand as independently well-evidenced; this task
    only names the aggregate risk class.
- Constraints And Invariants: do not overstate the finding — every
  named past decision had real, executed evidence behind it
  individually. This task's claim is narrower: the *cumulative* pattern
  of decision-making under repeated exposure to the same answer key is
  a risk category worth naming, not a retraction of any prior finding.
- Planned Validation: none code-executable — validation here is that
  the written statement exists, is cross-linked from the 3 documents
  named above, and that TASK-0081, once it lands, is explicitly checked
  against it before any submission-readiness claim is made.

## In Progress

None

## TODO

- [ ] Draft the protocol-note section naming the repeated-exposure risk.
- [ ] Cross-link into TASK-0081, TASK-0100, `EXECUTION_PLAN.md`.
- [ ] Confirm placement (`INVARIANCE_PROTOCOL.md` vs. a new short doc)
      with whoever owns those files' source-of-truth status.

## Dependency

- TASK-0081 (TODO) — the concrete mitigation this task names as
  mandatory-before-finality, not merely encouraged.
- TASK-0100 (Done) — the code-level multiple-comparisons gate this task
  is explicitly distinct from and complementary to.

## Open Questions

- Best home for the note: `INVARIANCE_PROTOCOL.md` (closest existing
  precedent, per its own gauge-symmetry pattern the 2026-07-13 reviews
  already extended twice) vs. a new `.ai/reference/` doc. Flagged, not
  pre-decided.

## Done

**2026-07-23, Implementer D (this thread).** Checked this task's own
Dependency section against current state before drafting anything
(per this project's own discipline — don't trust a filing task's
one-line summary): [[TASK-0081]] is listed above as "TODO," but is
actually **Done** (2026-07-12), and was further extended by [[TASK-0127]]
(2026-07-18) into "the reported headline, not an appendix." [[TASK-0100]]
is correctly listed as Done. So this task's own precondition — a
generalization set to point to — was already satisfied before this task
was ever picked up; the work here is naming the risk and writing the
rule, not waiting on anything.

**Placement decided** (this task's own Open Question): `INVARIANCE_
PROTOCOL.md`, not a new doc or `SEAM_PROTOCOL.md`. Reasoning, stated
per this task's own Constraints: `SEAM_PROTOCOL.md` is about boundaries
*between parallel task units* (an edge in a decomposition) — this risk
has no decomposition edge, it's a single review process repeatedly
observing one answer key, so it doesn't fit. `INVARIANCE_PROTOCOL.md`
already has precedent for scope broader than pure-physics GAUGE/KNOB/
SIGNAL (its own "Required tests (code / agent output)" section already
covers swarm/process risks like seed- and order-invariance, not just
measurement transformations) and already carries the file's own
established amendment pattern (TASK-0098's Tier 3b) for exactly this
kind of "a new risk class, distinct from the existing three, found
after the fact" addition.

**New section added**: "Repeated-exposure risk (TASK-0115)," placed
before "Rule of engagement" — states the gap precisely (no code-level
gate, including `frozen_context`/TASK-0100's own Tier-2 gate, can catch
a human choosing a claim having seen how it lands on the same 3
targets across ~15 review cycles), states why it doesn't fit GAUGE/
KNOB/SIGNAL (no input transformation to classify — same code, same
honest measurement, repeated exposure alone is the leak), and states
the rule plainly: **no `RESULTS.md` claim about robustness/
generalizability is submission-final without being checked against
[[TASK-0081]]/[[TASK-0127]]'s generalization set** (PTP1B, CASPASE7,
CASPASE1, GLUCOKINASE — targets this project's review history has
never seen), not merely "encouraged extra evidence." Explicitly does
**not** retroactively clear the mandatory 3 targets of this risk (per
this task's own Constraints: this is not a retraction of any prior
finding) — it means *robustness* claims should cite the 4-target set,
not the mandatory 3 alone. New Rule #6 added to "Rule of engagement"
cross-linking the section, matching Rule #5's own cross-link to Tier
3b. New one-line pointer added to `.ai/invariants/README.md` (per
that file's own "See also" precedent for `pitfalls.md`) stating this
risk is deliberately *not* an `INV-XXXX` registry entry — it's
per-claim, not per-quantity, and has no GAUGE/KNOB/SIGNAL table.

**Cross-linked into all 3 places this task's own Intent Contract named**:
- [[TASK-0081]]'s own Done section — new addendum naming it as the
  concrete mitigation, cross-linking `INVARIANCE_PROTOCOL.md`.
- [[TASK-0100]]'s own Done section — already had a 2026-07-15 addendum
  anticipating this task; added a short closing note confirming the
  written rule now exists and that no change to TASK-0100's own Tier-2
  gate was needed (the two remain complementary, as anticipated).
- `EXECUTION_PLAN.md`'s critical-path narrative — new dated entry
  (2026-07-23) stating the rule plainly, distinct from the existing
  Phase 5.8/1C.11 rows and the 2026-07-15 batch-filing line, both of
  which already informally referenced this task but never stated the
  rule as a standing, written policy.

**Not done, per this task's own Out Of Scope**: no code/gate was built
(none exists for this risk); no specific past review decision named in
this task's own Context was re-litigated — they stand as independently
well-evidenced, only the aggregate pattern is named.

**Full test suite**: re-ran per this project's own convention despite
this task's changes being documentation-only. 874 passed, 2 xfailed, 0
failed (`test_chiral.py`'s 4 earlier failures from a concurrent
thread's in-progress work, noted by [[TASK-0137]]'s own Done section,
are now green too — that thread's work landed since).

**First real application, 2026-07-24 ([[TASK-0151]]):** [[TASK-0145]]'s BCR_ABL1
transport positive and [[TASK-0149]]'s CARDIAC_MYOSIN `dcc_low`/`prs_low` positives —
the project's two strongest results as of the day this rule was written — checked
against the PTP1B/CASPASE7 generalization set. Mixed, real result: transport does not
clearly generalize (PTP1B's identical quantity comes back below chance); `dcc_low`
replicates cleanly on PTP1B (Bonferroni-significant on two independent targets now,
the strongest cross-target evidence in the project's register), `prs_low` does not
generalize to either target. Exactly the kind of result this rule exists to surface —
a mixed outcome, not a uniform confirm/kill, changing how each finding should be
framed without retracting either. Full detail: `RESULTS.md`'s own generalization-set
section, open-questions row 33; `.ai/tasks/DONE/TASK-0151-generalization-check-
transport-lowmode-findings.md`.
