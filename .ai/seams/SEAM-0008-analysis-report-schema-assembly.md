# SEAM-0008 no assembly step converts `analysis.py`'s real output into `report.verdict_template`'s expected schema

- units: `analysis.py` (`benchmark`, `ablation`, `quantum_vs_classical`, `apo_holo_consistency`) -> *no assembly step exists* -> `report.verdict_template` (expects a flat `results` dict: `AUC_apo_Hnew_default`, `AUC_apo_H10_baseline`, `AUC_apo_Hnew_optimised`, `AUC_holo_Hnew_optimised`, `AUC_ctqw_mean`, `AUC_heat_mean`, `most_impactful_term`, `least_impactful_term`, `mean_rho_apo_holo`, `mean_jacc20`)
- invariant: the `results` dict `verdict_template` renders is actually assembled from
  real `analysis.py` output, not a shape that merely happens to satisfy the tests
- owner: [[TASK-0056]] (existing Phase 4 review task, covers `report.py`; cross-linked
  here rather than filing a duplicate — see note below)
- seam-test: not yet written
- status: OPEN
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
