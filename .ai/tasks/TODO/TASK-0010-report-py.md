# TASK-0010 Implement `report.py` — verdict template + hit-list deliverable

## Context

- ID: TASK-0010
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/report.py`
- Status: TODO
- Owner: Implementer
- Source: notebook `notebooks/H_new_engineering (4) CLEAN.ipynb` §15
  "Synthesis & honest verdict", §16 "Final recommendation (decision-support
  template)", §17 "Challenge Submission: The Hit List (Top 5)" incl. §17.1
  "Stability Analysis: Jaccard Similarity (Top 5)" — direct port of all
  four.
- Scope: `__WORK_IN_PROGRESS__/src/allostery/report.py` (currently a 5-line
  stub) + `__WORK_IN_PROGRESS__/tests/test_report.py` (new)

## Intent Contract

- Outcome: "notebook prose → code that fills from frozen-run numbers"
  (quoting `.ai/tasks/PLANS/PLAN.md` Phase 4 directly) — the verdict
  template and hit-list generator become reusable functions instead of
  hand-edited notebook markdown, so the report regenerates correctly every
  time the frozen numbers change instead of drifting out of sync with them.
- In Scope:
  - `verdict_template(results)` — §15/§16's honest-verdict / decision-support
    prose, parameterized by run results rather than hardcoded per-target
    text.
  - `hit_list(scores, k=5)` — §17's top-5 selection.
  - `jaccard_stability(hit_lists_across_runs)` — §17.1's top-5 stability
    metric across repeated/perturbed runs.
- Out Of Scope: the actual competence-map narrative writing for the
  submission — this module produces the numbers/lists the narrative cites,
  not the narrative itself.
- Constraints And Invariants: must only ever be called with FROZEN-path
  results for the actual submission hit-list (dev-path/ceiling numbers are
  fine for the competence-map narrative but must be clearly labeled as such
  wherever `verdict_template` surfaces them — don't let a ceiling number
  get quoted as if it were the frozen result).
- Planned Validation: unit test `jaccard_stability` on synthetic hit-lists
  with known overlap (e.g. two identical top-5 lists → similarity 1.0; two
  disjoint top-5 lists → similarity 0.0); snapshot test of
  `verdict_template`'s output shape (not exact prose) against a synthetic
  results object.

## In Progress

None

## TODO

- [ ] Read notebook §15, §16, §17, §17.1 cells.
- [ ] Implement `verdict_template`, `hit_list`, `jaccard_stability`.
- [ ] Unit tests.
- [ ] Add the DEV-vs-FROZEN labeling safeguard described above.

## Dependency

- TASK-0008 (`analysis.py`) and TASK-0009 (`diagnostics.py`) — this module
  is the final consumer that turns their outputs into the submission
  artifact.
- TASK-0006 (`protocol.py`) — for the DEV/FROZEN provenance tagging on
  whatever `verdict_template` renders.

## Open Questions

- None yet — surface after reading §15-17 in detail.

## Done

(not yet)
