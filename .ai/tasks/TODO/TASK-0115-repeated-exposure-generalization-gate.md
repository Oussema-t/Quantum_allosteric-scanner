# TASK-0115 Name and gate the repeated-exposure risk across the review cycle

## Context

- ID: TASK-0115
- Title: `frozen_context`/LOPO/TASK-0100 gate *code-level* parameter and
  operator selection against true labels. Nothing gates the ~15 human
  review cycles this project has already run, each looking at the same
  3 targets' real AUCs before deciding what to rename, re-scope, or
  re-frame — a researcher-degrees-of-freedom exposure no existing
  protocol document accounts for.
- Status: TODO
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

(not yet)
