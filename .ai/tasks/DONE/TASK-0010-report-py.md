# TASK-0010 Implement `report.py` — verdict template + hit-list deliverable

## Context

- ID: TASK-0010
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/report.py`
- Status: Done
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

- [x] Read notebook §15, §16, §17, §17.1 cells.
- [x] Implement `verdict_template`, `hit_list`, `jaccard_stability`.
- [x] Unit tests.
- [x] Add the DEV-vs-FROZEN labeling safeguard described above.

## Dependency

- TASK-0008 (`analysis.py`) and TASK-0009 (`diagnostics.py`) — this module
  is the final consumer that turns their outputs into the submission
  artifact.
- TASK-0006 (`protocol.py`) — for the DEV/FROZEN provenance tagging on
  whatever `verdict_template` renders.

## Open Questions

- None yet — surface after reading §15-17 in detail.
- Resolved: §17.1's markdown header (cell 63, "Stability Analysis: Jaccard
  Similarity (Top 5)") has no corresponding code cell in the notebook —
  cells 64-69 that follow it are unrelated KRAS visualization/exploration
  cells, not the promised computation. `jaccard_stability` was built from
  this task's own Intent Contract spec (pairwise Jaccard over hit-lists)
  using this package's already-ported Jaccard convention
  (`analysis.py::apo_holo_consistency`, itself §12/cell 52's
  `rank_overlap`) rather than a verbatim port of nonexistent code.

## Done

- `hit_list(scores, k=5, resnums=None, exclude_idx=None)`: §17/cell 62's
  top-k selection, with optional source-residue exclusion and resnum
  mapping.
- `jaccard_stability(hit_lists_across_runs)`: pairwise Jaccard over any
  number of hit-lists (mean/min + per-pair detail). Documented divergence
  from notebook cell 52's edge-case handling (empty-union pair scores 1.0
  here, matching `apo_holo_consistency`'s convention, vs. 0.0 there) — see
  Open Questions and the function's own docstring.
- `verdict_template(results, provenance="dev"|"frozen")`: §15/§16's
  headline verdict + the four data-driven recommendation lines from cell
  60 (the fifth, static-prose bullet is out of scope — competence-map
  narrative, not numbers/lists). `provenance != "frozen"` prepends a loud
  DEV/CEILING banner (this task's DEV-vs-FROZEN safeguard); missing
  `results` keys render "N/A" and skip their dependent line instead of
  raising. DEV/FROZEN vocabulary (lowercase strings) matches
  `protocol.py::ProtocolRoster`.
- `__WORK_IN_PROGRESS__/tests/test_report.py`: 21 tests covering all three
  functions' Planned Validation cases (identical/disjoint hit-lists,
  verdict threshold classifications, missing-key handling, DEV banner).
  Full suite green: 301 passed, 4 pre-existing skips (was 280 before this
  task; +21 new).
- No changes to any other module; no API/response-shape changes.
