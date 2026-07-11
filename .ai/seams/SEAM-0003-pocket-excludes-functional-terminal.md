# SEAM-0003 assembled pocket excludes functional + terminal residues

- units: `labels.holo_pocket_mask` + `labels.functional_indices` + `labels.terminal_mask` -> *no assembly step* -> scoring pipeline consumer
- invariant: `assembled_pocket ∩ (functional ∪ terminal) == ∅` (per-target)
- owner: [[TASK-0052]]
- seam-test: not yet written — `test_leakage_gate.py::test_labels_allosteric_ligand_only` assumes a `build_labels()` assembly that does not currently exist (confirmed by grepping `labels.py` for `build_labels`/`class Labels` — zero hits)
- status: OPEN
- provenance: seeded from `SEAM_PROTOCOL.md`'s own worked example (this is the doc's motivating
  case, not a hypothetical). Independently corroborated by [[TASK-0047]] (Reviewer A's
  Foundation Review, 2026-07-07, P2 finding: no committed network-gated integration test for
  `labels.py` matching its own Intent Contract). Two independent passes finding the same real
  gap.
