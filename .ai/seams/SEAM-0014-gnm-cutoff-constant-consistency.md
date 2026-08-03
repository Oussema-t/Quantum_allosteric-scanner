# SEAM-0014 The resolved GNM cutoff constant (8.0 Å) stays the live default at its real call sites

- units: [[TASK-0067]]'s benchmark resolution (swept 7.5/8.0/10.0 Å, found
  "no significant difference in the tested range," retained the pre-existing
  8.0 Å default rather than changing it) -> the real numeric default at each
  GNM-operator-construction call site this benchmark was about:
  `backend/analysis.py::gnm_context`'s `cutoff=8.0` default,
  `allostery/hamiltonians.py::H8_gnm`'s default, and `allostery/potentials.py`'s
  GNM builders (all now routed through [[TASK-0066]]'s shared
  `_kirchhoff_eigh`, see [[SEAM-0013]])
- invariant: the live default cutoff at every GNM-operator-construction call
  site named above equals TASK-0067's resolved value (8.0 Å) unless a later
  task explicitly changes it *and* documents why, with its own benchmark
  evidence — never silently drifts back to one of the two rejected values
  (7.5, 10.0) or a new unbenchmarked one
- owner: [[TASK-0072]] (Done) — built and validated the seam-test this
  record formalizes; [[TASK-0067]] (Done) — resolved the constant itself
- seam-test: `test_golden_value_cross_tree_drift.py::
  TestGoldenCutoffConstant::test_backend_default_cutoff_is_the_resolved_value`
  — pins `gnm_context`'s live default directly (not a copy of the literal
  written elsewhere) against the resolved value, so a future edit to the
  default is caught by the pin itself, not by re-deriving the benchmark.
- status: **VERIFIED**
- provenance: opened and closed together, [[TASK-0073]], 2026-08-03 — same
  filing as [[SEAM-0013]], per `EXECUTION_PLAN.md` Phase 2.5. **Scope note,
  read before extending this seam**: this covers only the GNM-*operator*-
  construction cutoff TASK-0067 benchmarked. It does not cover the separate,
  differently-motivated 8.0 Å value TASK-0186/TASK-0188 later reused for
  spatial contact-graph *hop-distance* — that is a different question
  (BFS hop-count, not eigendecomposition-based scoring) asked of a
  superficially similar constant, and TASK-0188's own filing found that
  reuse had never actually been benchmarked for its own purpose. Conflating
  the two would misstate what this seam actually guarantees; if that
  hop-distance usage needs its own seam record, file it separately rather
  than folding it in here.
