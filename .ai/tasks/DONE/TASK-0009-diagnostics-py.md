# TASK-0009 Implement `diagnostics.py` — operator diagnostics + failure-mode classifier

## Context

- ID: TASK-0009
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/diagnostics.py`
- Status: Done
- Owner: Implementer
- Source: notebook `notebooks/H_new_engineering (4) CLEAN.ipynb` §14
  "Failure-mode analysis" — direct port.
- Scope: `__WORK_IN_PROGRESS__/src/allostery/diagnostics.py` (currently a
  5-line stub) + `__WORK_IN_PROGRESS__/tests/test_diagnostics.py` (new)

## Intent Contract

- Outcome: for a target where the method scored poorly, classify *why* —
  distinguish "the answer isn't in the apo topology" (a legitimate,
  reportable negative result per `PLAN.md`'s "gates before build" framing)
  from "the operator is misconfigured" (a bug) from "the label itself is
  wrong" (a `labels.py` upstream problem).
- In Scope:
  - port §14's failure-mode categories and decision logic verbatim.
  - an `operator_diagnostics(H, ...)` check for the kind of thing
    `.claude/TASKS.md` T-012 already found by hand (e.g. `build_H_new` not
    being globally PSD by design) — surface these as diagnosable properties
    instead of one-off manual notebook observations.
  - a `classify_failure(target, scores, labels)` function returning one of
    a small closed set of categories (e.g. `NO_SIGNAL_IN_APO`,
    `LABEL_SUSPECT`, `OPERATOR_DEGENERATE`, `INSUFFICIENT_RESOLUTION`).
- Out Of Scope: fixing whatever the classifier flags — this module reports,
  it doesn't repair.
- Constraints And Invariants: the classifier must be able to run on a
  FROZEN-context result without needing to re-open the label it's
  diagnosing beyond what `analysis.py` already exposed to it — don't
  reintroduce a leakage path here in the name of diagnostics.
- Planned Validation: unit tests with synthetic score/label pairs
  constructed to trigger each failure category deliberately (e.g. random
  scores → `NO_SIGNAL_IN_APO`; a disconnected/degenerate graph →
  `OPERATOR_DEGENERATE`).

## In Progress

None

## TODO

- [x] Read notebook §14; extract failure-mode categories and thresholds.
- [x] Implement `classify_failure` and `operator_diagnostics`.
- [x] Unit tests per category using synthetic triggers.

## Dependency

- TASK-0008 (`analysis.py`) — consumes its scoring outputs as input.

## Open Questions

- None yet — this is a fairly direct notebook port; expect open questions
  to surface once §14's actual cell content is read in detail.
- Resolved: notebook cell 56 has no named `classify_failure` function or
  closed category set — it's an inline per-target loop printing free-text
  notes. The four categories in this task's own Outcome/Planned-Validation
  text (`NO_SIGNAL_IN_APO`, `LABEL_SUSPECT`, `OPERATOR_DEGENERATE`,
  `INSUFFICIENT_RESOLUTION`) are this task's organizing taxonomy over that
  cell's actual signals, not a verbatim notebook name — the underlying
  *decision logic* (thresholds: N>800, diag/offdiag>3.0, B≡0, no pocket
  label) is ported verbatim; the category *names* and priority order
  (operator bug > bad label > data-quality > legitimate negative) are new,
  documented in `classify_failure`'s own docstring. Added a 5th category,
  `NO_FAILURE_DETECTED`, not in the task text, so the function is total
  over well-scoring inputs too.

## Done

- `operator_diagnostics(H, bfactors=None, ...)`: N, spec_min/max, eff_rank
  (reuses `metrics.eff_rank`), diag/offdiag ratio, connected-component
  count, `is_psd`, `b_all_zero`, and a `notes` list mirroring cell 56's
  printed notes verbatim (V_B disabled, large N, diagonal-dominant,
  disconnected, not-PSD/T-012).
- Off-diagonal introspection reuses the invariant `select.py`'s
  `_hop_distances_from_source` already established (diagonal potentials
  never touch H's off-diagonal) — no need to thread `build_H_new`'s
  internal components through a new return value; `build_H_new`'s
  signature is untouched.
- `classify_failure(scores, labels, H=None, bfactors=None, ...)`: closed 5-
  category verdict, priority order documented above and in the docstring.
- `__WORK_IN_PROGRESS__/tests/test_diagnostics.py`: 15 tests, one per
  triggered note/category (disconnected graph via two far-apart helices,
  B≡0, large-N via a lowered threshold, diagonal dominance via a hand-built
  matrix, T-012 PSD canary, each of the 5 `classify_failure` categories
  including priority-ordering checks). `.venv/bin/python3 -m pytest -q
  __WORK_IN_PROGRESS__/tests/test_diagnostics.py` — 15 passed. Full suite
  (`__WORK_IN_PROGRESS__/tests/` + `backend/test_geometry.py`) still green:
  280 passed, 4 pre-existing skips.
- No changes to any other module; no API/response-shape changes.
