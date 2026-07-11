# SEAM-0001 labels seq-pocket agrees with superpose geom-pocket

- units: `labels.holo_pocket_mask` (sequence-alignment construction) -> `superpose` (geometric construction) -> consumer
- invariant: the two independent pocket constructions agree; disagreement is flagged, not silently resolved
- owner: [[TASK-0005]] (Done)
- seam-test: `test_superpose.py::test_disagreement_is_reported_not_resolved` and `test_geometric_mask_agrees_with_sequence_mask_when_structures_identical`
- status: VERIFIED
- provenance: seeded from `SEAM_PROTOCOL.md`'s own table at adoption ([[TASK-0050]], 2026-07-11). Not independently re-verified beyond confirming the cited tests exist and their names match the claim.
