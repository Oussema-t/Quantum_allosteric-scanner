# TASK-0009 Implement `diagnostics.py` — operator diagnostics + failure-mode classifier

## Context

- ID: TASK-0009
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/diagnostics.py`
- Status: TODO
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

- [ ] Read notebook §14; extract failure-mode categories and thresholds.
- [ ] Implement `classify_failure` and `operator_diagnostics`.
- [ ] Unit tests per category using synthetic triggers.

## Dependency

- TASK-0008 (`analysis.py`) — consumes its scoring outputs as input.

## Open Questions

- None yet — this is a fairly direct notebook port; expect open questions
  to surface once §14's actual cell content is read in detail.

## Done

(not yet)
