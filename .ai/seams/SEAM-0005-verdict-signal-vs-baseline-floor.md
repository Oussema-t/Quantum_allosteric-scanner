# SEAM-0005 classify_failure/verdict "signal" means beats-floor, not beats-chance

- units: `baselines` (floor definition) -> `analysis`/report `classify_failure`/verdict consumer
- invariant: "signal" in a reported verdict means the method beats the strongest trivial
  structural baseline (floor), not merely beats chance (AUC > 0.5) or beats one specific
  comparison method (H10)
- owner: [[TASK-0011]] (in progress — claimed by a parallel Implementer thread as of this
  seam's seeding)
- seam-test: not yet written — depends on `baselines.py` landing first
- status: OPEN
- provenance: seeded from `SEAM_PROTOCOL.md`'s own table at adoption ([[TASK-0050]],
  2026-07-11). Floor is currently stubbed (`baselines.py` not yet implemented), so this seam
  cannot be closed yet by construction, not by oversight. **Do not auto-flip to VERIFIED when
  TASK-0011 lands** — landing the floor doesn't by itself prove a seam-test exists and passes
  across the `baselines` -> verdict boundary; that check is separate follow-up work once
  TASK-0011 is Done (not yet filed as its own task — file one at that point rather than
  assuming this record's existence is enough).
