# TASK-0097 Name the "quantum metric" honestly (decoherent spectral overlap, not a coherent walk)

## Context

- ID: TASK-0097
- Title: State plainly, in the methodological report and `RESULTS.md`,
  that `time_averaged_ctqw` is the decoherent/infinite-time-average limit
  — a spectral overlap quantity — not a coherent quantum walk metric.
- Status: TODO
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/REVIEW-2026-07-13-proximity-confound-and-propagator-semantics.md`,
  finding **P2-B**. `time_averaged_ctqw` returns
  Σₖ |v_k(j)|² |v_k(s)|² — by construction, all phase information is
  averaged out. This is consistent with this repo's own existing
  flat-dephasing-sweep finding (KRAS_G12C) and is a legitimate
  methodological choice, but it means the challenge deliverable's
  headline "quantum metric" is a spectral-overlap quantity, not a
  coherent quantum walk — something a judge should be told, not left to
  discover.

## Intent Contract

- Outcome: the methodological report template and `RESULTS.md` both state
  explicitly, near wherever `time_averaged_ctqw`'s numbers are first
  presented, that this quantity is the decoherent/time-averaged limit of
  the CTQW — a spectral overlap between eigenvector components at the
  source and target residues — and that all phase/coherence information
  is averaged out by construction.
- In Scope: `RESULTS.md`, `report.py`'s template output (`report.txt` or
  equivalent), the methodological report deliverable (TASK-0079's
  artifact).
- Out Of Scope: changing `time_averaged_ctqw`'s computation itself — this
  is a documentation-honesty task, not a code change. Also out of scope:
  deciding whether a genuinely coherent (non-time-averaged) metric should
  be added as an alternative — flag as a possible future task if it comes
  up, don't scope-creep this one.
- Acceptance Scenarios:
  - Given `RESULTS.md`'s current AUC tables (which use
    `time_averaged_ctqw` under the hood), when this task lands, then a
    reader encounters the decoherent-limit disclosure before or alongside
    the numbers, not buried in a code comment only.
  - Given the methodological report deliverable, then it contains the
    same disclosure in report-appropriate language (not just internal
    task-file prose).
- Constraints And Invariants: this is exactly `ALGORITHM_REGISTER`'s
  honest-capability posture (per the review) applied to the headline
  metric — match that document's existing tone/format rather than
  inventing a new disclosure style.
- Planned Validation: manual review confirming the disclosure appears in
  both `RESULTS.md` and the methodological report output.

## Dependency

- Can run in parallel with TASK-0098 (per the review's sequencing) once
  TASK-0094/0095/0096 land.
- Related: TASK-0082 (competence map synthesis) — should incorporate this
  disclosure when it assembles the final submission-facing numbers.

## Open Questions

- None — the disclosure content is specified directly by the review.

## Done

(not yet)
