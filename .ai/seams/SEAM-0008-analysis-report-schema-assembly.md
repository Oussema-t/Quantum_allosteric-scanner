# SEAM-0008 no assembly step converts `analysis.py`'s real output into `report.verdict_template`'s expected schema

- units: `analysis.py` (`benchmark`, `ablation`, `quantum_vs_classical`, `apo_holo_consistency`) -> `analysis.assemble_verdict_results` -> `report.verdict_template` (expects a flat `results` dict: `AUC_apo_Hnew_default`, `AUC_apo_H10_baseline`, `AUC_apo_Hnew_optimised`, `AUC_holo_Hnew_optimised`, `AUC_ctqw_mean`, `AUC_heat_mean`, `most_impactful_term`, `least_impactful_term`, `mean_rho_apo_holo`, `mean_jacc20`)
- invariant: the `results` dict `verdict_template` renders is actually assembled from
  real `analysis.py` output, not a shape that merely happens to satisfy the tests
- owner: [[TASK-0079.001]] (subtask of [[TASK-0079]], split 2026-07-12)
- seam-test: `__WORK_IN_PROGRESS__/tests/test_analysis.py::TestAssembleVerdictResults`
  — calls the real `benchmark`/`ablation`/`quantum_vs_classical`/`apo_holo_consistency`
  on synthetic fixtures, feeds the real (nested) output into
  `analysis.assemble_verdict_results`, asserts every `verdict_template`-expected key
  is present with a real value, and confirms the rendered report has no `"N/A"` and
  no literal `"nan"` text. Also covers per-key omittability and the
  `auc_*_optimised` direct-passthrough (not derived from `benchmark`).
- status: VERIFIED (2026-07-12, Implementer A — 440 passed via
  `.ai/tools/pytest_local.py wip-all`)
- provenance: found by [[TASK-0053]]'s sweep (2026-07-11). Grepped every one of
  `verdict_template`'s expected keys (`AUC_apo_Hnew_default`, `AUC_apo_H10_baseline`,
  `AUC_apo_Hnew_optimised`, `most_impactful_term`, `mean_jacc20`) across
  `__WORK_IN_PROGRESS__/src` and `__WORK_IN_PROGRESS__/tests`: every hit is inside
  `test_report.py`'s own hand-built fixture dict (lines 70-79) — zero hits in any
  real production code. `analysis.py`'s actual functions return differently-shaped,
  nested dicts (`benchmark` -> `{"H_new_default": metric_pack, ...}`, `ablation` ->
  `{"L_only": ..., "B": ..., ...}`, each `metric_pack` itself a nested dict with an
  `"AUC"` key, not a flat `"AUC_apo_Hnew_default"` string). `report.verdict_template`
  has, as of this sweep, never once been exercised against real `analysis.py` output
  — only against a dict a human wrote to match its docstring's promise. This is the
  Seam Protocol's own "smell" #3 verbatim ("a module returns two things that 'should'
  relate... with no test on the relation") one level up: two *modules* whose schemas
  should relate, with no assembly code and no test on the relation between them.
  **Not filing a new owner task**: [[TASK-0056]] already exists, is unclaimed, and is
  explicitly scoped as a review of `report.py` (among others) that would need to
  answer this exact question to do its job — pre-loading this finding there so
  whoever picks it up doesn't have to rediscover it, per this task's own "cite
  evidence, don't silently reconcile" rule.

  **Resolved by [[TASK-0056]]'s review (2026-07-12): this is not a `report.py` bug,
  and the fix does not belong in `report.py`.** `report.py`'s own module docstring
  already states, correctly and deliberately: "renders prose/lists from an
  already-assembled results dict; it does not compute the underlying numbers
  (that's `analysis.py`'s job)." Writing an assembly function inside `report.py`
  itself (or inside `analysis.py`, out of this review's scope) risks guessing at a
  shape disconnected from how the real pipeline will actually be orchestrated.
  The genuine owner is **[[TASK-0079]]** (end-to-end challenge run, Phase 5.1) —
  its own Intent Contract already states "In Scope: orchestrating the already-Done
  pipeline stages (`labels`, `protocol`, `select`, `analysis`, `diagnostics`,
  `report`, `baselines`, `pathways`, `coarse`, `viz`) into one run per target" —
  which *is* the assembly step this seam is waiting on. Currently claimed and
  in-progress (Implementer A, 2026-07-12 13:43) — cross-linked directly into that
  task's own file so this isn't missed. Status stays **OPEN**, not flipped to a
  documented non-issue, since the invariant genuinely isn't satisfied yet — it's
  correctly re-scoped, not resolved.
