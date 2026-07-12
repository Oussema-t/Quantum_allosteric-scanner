# SEAM-0003 assembled pocket excludes functional + terminal residues

- units: `labels.holo_pocket_mask` + `labels.functional_indices` + `labels.terminal_mask` -> `labels.build_labels` (TASK-0070) -> `protocol.get_pocket_mask`/`get_labels` (gated consumer)
- invariant: `assembled_pocket ∩ (functional ∪ terminal) == ∅` (per-target)
- owner: [[TASK-0052]]
- seam-test: `tests/test_leakage_gate.py::test_labels_allosteric_ligand_only`
  (network-gated real BCR_ABL1 check: `(lab.pocket & lab.active_site).sum()
  == 0`) plus `tests/test_labels.py::TestBuildLabels::
  test_excludes_functional_overlap_from_pocket` (synthetic, the exact
  overlapping-contact case) and
  `test_kras_g12c_real_cys12_excluded`/`test_bcr_abl1_real_exclusion_invariant_holds`
  (two independent real targets) — all passing, not `xfail`.
  `build_labels` itself also **asserts** the invariant internally
  (`labels.py`, TASK-0070), so a regression here fails loudly at the
  assembly site, not just in a test that could bit-rot unnoticed.
- status: VERIFIED
- provenance: seeded from `SEAM_PROTOCOL.md`'s own worked example (this is the doc's motivating
  case, not a hypothetical). Independently corroborated by [[TASK-0047]] (Reviewer A's
  Foundation Review, 2026-07-07, P2 finding: no committed network-gated integration test for
  `labels.py` matching its own Intent Contract). Two independent passes finding the same real
  gap. Closed 2026-07-12: TASK-0070 added the `build_labels` assembly step
  (`EXECUTION_PLAN.md` Phase 0.1), TASK-0052 bound `test_leakage_gate.py`'s
  CONTRACT tests to the real signature and confirmed the seam-test passes
  for real (not `xfail`), both under `pytest` and this file's own
  standalone `python test_leakage_gate.py` runner.
