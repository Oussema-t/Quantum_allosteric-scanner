# TASK-0067 GNM cutoff + contact-weight-scheme benchmark (resolves T-018/T-021)

## Context

- ID: TASK-0067
- Title: Run the actual benchmark T-018 (GNM contact cutoff, 7-10 Å) and
  T-021 (five contact-weighting schemes) ask for, using target proteins in
  `config/targets.yaml`, and pick (or justify not picking) one cutoff/
  weighting convention.
- Status: TODO
- Owner: Implementer
- Source: TASK-0018's decision doc (Done section, GNM/Kirchhoff row) —
  static comparison found **three different cutoff values in active use**
  with no benchmark backing any of them: `backend/analysis.py::gnm_context`
  uses 8.0 Å; `allostery/hamiltonians.py::H8_gnm` defaults to 7.5 Å;
  `allostery/potentials.py`'s GNM callers (`_gnm_msf`/`V_R`/`V_C`/`V_M`)
  pass 10.0 Å. Wraps closed-ledger `.claude/TASKS.md` **T-018**/**T-021**
  per the Task Ledger Boundary (TASK-0002) — this is the wrapper task, not
  a new `T-NNN` row.

## Intent Contract

- Outcome: an evidence-backed answer to "which GNM cutoff (and which of
  the 5 weighting schemes already implemented in
  `hamiltonians.contact_matrix`: binary/gaussian/exponential/harmonic/
  invdist) best predicts known allosteric/functional sites on the
  benchmark targets" — or an explicit finding that the choice doesn't
  matter within the tested range (also a valid, useful answer).
- In Scope: sweep cutoff over {7.5, 8.0, 10.0} Å (the three values
  currently in live use) plus the 5 weighting schemes, against
  `config/targets.yaml`'s benchmark proteins (KRAS_G12C, BCR_ABL1, PTP1B,
  …), scored against whatever labeled-site ground truth `labels.py`
  already provides.
- Out Of Scope: changing `backend/`'s live default without a separate,
  explicit follow-up — this task produces the evidence; whether to change
  the deployed 8.0 Å default is a decision for whoever reads the result
  (flag it back to TASK-0018-style reconciliation if the answer disagrees
  with backend's current choice).
- Acceptance Scenarios:
  - Given the benchmark run, when complete, then there is a table of
    AUC/precision-at-k (or whatever `metrics.py` already exposes) per
    (cutoff, weight-scheme) pair per target protein.
  - Given that table, then this task states either "cutoff X / scheme Y
    is the clear best on this benchmark set" or "no cutoff/scheme in the
    tested range shows a significant difference" — not left unstated.
- Constraints And Invariants: reuse existing scored-benchmark machinery
  (`labels.py`, `protocol.py`, `metrics.py`, `baselines.py`) rather than
  hand-rolling a new evaluation harness.
- Planned Validation: the benchmark run itself is the validation; results
  written to this task's Done section as a table, plus raw output
  artifacts if the harness produces them.

## Dependency

- TASK-0018 (Done) — found and documented the three-way cutoff divergence
  this task resolves.
- Depends on `labels.py`/`protocol.py`/`metrics.py`/`baselines.py` (all
  Done) for scoring machinery; may depend on `coarse.py` (TASK-0013, TODO)
  if a coarse-grained pass is needed for larger targets — check at
  execution time whether that's actually required or whether existing
  Cα-level machinery suffices.

## Open Questions

- Does the existing benchmark harness (`protocol.py`/`labels.py`) already
  support sweeping a cutoff/weight-scheme parameter, or does this task
  need to add that sweep capability first? Check before estimating scope.

## Done

(not yet)
