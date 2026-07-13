# TASK-0097 Name the "quantum metric" honestly (decoherent spectral overlap, not a coherent walk)

## Context

- ID: TASK-0097
- Title: State plainly, in the methodological report and `RESULTS.md`,
  that `time_averaged_ctqw` is the decoherent/infinite-time-average limit
  — a spectral overlap quantity — not a coherent quantum walk metric.
- Status: Done
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
  TASK-0094/0095/0096 land. **Note:** TASK-0096 (phantom H11/H12 operators)
  was still `TODO`/claimed (Implementer A, in progress on `test_hamiltonians.py`)
  when this task started — proceeded anyway since TASK-0097's actual scope
  (report/RESULTS.md disclosure text) has no code overlap with H11/H12; the
  review's "once ... land" sequencing is about avoiding simultaneous churn
  in the same area, not a hard code dependency here.
- Related: TASK-0082 (competence map synthesis) — should incorporate this
  disclosure when it assembles the final submission-facing numbers.

## Open Questions

- None — the disclosure content is specified directly by the review.

## Done

- **`report.py`'s `verdict_template`**: a `[NOTE]` disclosure line added
  immediately after the "HEADLINE VERDICT" banner, before any AUC value is
  rendered — unconditional (renders even with an empty `results` dict,
  since it's a statement about what the metric *is*, not about which keys
  happen to be populated). States the quantity is the decoherent/time-
  averaged CTQW limit (spectral overlap between source/residue eigenvector
  components), not a coherent snapshot, and that phase information is
  averaged out by construction — matches `ALGORITHM_REGISTER.md`'s terse,
  direct, caveat-next-to-the-number tone rather than inventing a new style.
- **`RESULTS.md`**: a second "methodology note" paragraph added directly
  after the existing apo-only note (same spot, same scope — applies to
  every AUC number in the document), before the first target's table
  (KRAS_G12C), with the same content plus the flat-dephasing-sweep
  consistency note from the review's own P2-B section.
- **Tests**: `test_report.py` gained 3 new tests —
  `test_decoherent_limit_disclosure_present_before_the_auc_values` (checks
  ordering: banner < disclosure < first value, and that "decoherent"/"not
  a coherent quantum-walk snapshot" are both present),
  `test_decoherent_limit_disclosure_present_even_with_no_results` (renders
  unconditionally), and `TestResultsMdDecoherentDisclosure` (reads
  `RESULTS.md` directly, confirms the disclosure appears before the first
  `### KRAS_G12C` table) — turns this task's own "manual review" Planned
  Validation into a durable, automated check, same practice as TASK-0095's
  grep-based framing test. Verified the new prose doesn't reintroduce
  TASK-0095's banned "classical"+"heat" co-occurrence
  (`test_ground_state_relaxation_guard.py`'s existing check still passes).
- Full WIP suite run directly against `__WORK_IN_PROGRESS__/.venv` (not
  the whitelisted `pytest_local.py` wrapper — still broken per TASK-0069,
  unrelated, unclaimed as of this task): **494 passed, 1 xpassed**
  (pre-existing, unrelated `test_superpose.py` order flake), 0 failures.
- Per user instruction this session: **no staging/commit performed** — all
  files (`report.py`, `RESULTS.md`, `test_report.py`, this task file,
  `COMMON.md`) are on disk, uncommitted, pending this thread's turn in the
  commit queue.
