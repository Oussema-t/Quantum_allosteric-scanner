# SEAM-0013 Kirchhoff-context/DCC primitive stays bit-identical across the two independently-implemented trees

- units: `backend/analysis.py::_kirchhoff_eigh`/`_normalized_dcc` (TASK-0066)
  <-> `allostery/potentials.py::_kirchhoff_eigh`/`_normalized_dcc` (TASK-0066,
  independent port, deliberately no cross-import per TASK-0018's backend/
  allostery boundary) -> each tree's own downstream consumers (`gnm_context`,
  `_dcc`, `V_covariance`, `_abs_coupling` on the `backend/` side; `_gnm_msf`,
  `V_C`, `V_M` on the `allostery/` side)
- invariant: given identical coordinates and cutoff, both independent
  implementations produce bit-identical `A`, `w` (eigenvalues), `U`
  (eigenvectors), `nz` (nonzero mask), `winv`, and the resulting normalized
  DCC matrix (`np.array_equal`, not tolerance-close — both sides build the
  same Kirchhoff matrix via the same formula and the same LAPACK `eigh`
  routine, so there is no floating-point path difference to tolerate)
- owner: [[TASK-0072]] (Done) — built and validated the seam-test this record
  formalizes; [[TASK-0066]] (Done) — built the two primitives it protects
- seam-test: `test_golden_value_cross_tree_drift.py::
  TestKirchhoffEighCrossTreeParity` (5 tests: contact adjacency, degree,
  eigenvalues, eigenvectors, nonzero mask + pseudo-inverse eigenvalues) and
  `::TestNormalizedDccCrossTreeParity` (2 tests) — 7 tests total, all passing
  on a fixed deterministic 40-residue synthetic reference structure
  (`np.random.default_rng(42)`, no network fetch). **Confirmed to actually
  fire**, not merely asserted to: `::TestDriftIsActuallyDetected` constructs
  two real divergence classes without touching the shipped functions (a
  mismatched cutoff — the exact bug class TASK-0018 originally found three
  live instances of — and an unnormalized-covariance DCC, a one-line
  "forgot to divide by `np.outer(d,d)`" bug) and confirms the parity checks
  above correctly return `False` for both.
- status: **VERIFIED**
- provenance: opened and closed together, [[TASK-0073]], 2026-08-03 — filed
  per `EXECUTION_PLAN.md` Phase 2.5 ("so the green bar remembers the
  boundary — mechanism, not discipline") to register this seam once its
  upstream dependencies ([[TASK-0066]] built the shared logic, [[TASK-0072]]
  built and validated the drift test) had landed. The test already existed
  and already passed at filing time (`pytest_local.py cross-tree`, 11
  passed, 0 failed, per TASK-0072's own Done section) — this record is the
  registry bookkeeping step the Seam Protocol requires, not new test work.
