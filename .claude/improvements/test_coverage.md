# Test Coverage Improvements

**Scope:** All files under `tests/`  
**Type:** Concrete missing tests — what must be added.  
Cross-reference: TASKS.md for task IDs and assignees. `../TESTS.md` for standards each test must meet.

---

## Existing test bugs

All existing test bugs are tracked in TASKS.md (Group A, T-001 through T-008).
Do not restate them here — go to TASKS.md for the canonical list.
One non-obvious correction not in TASKS.md: T-012 asserts H_new is PSD (eigenvalues ≥ -1e-10),
but H_new is **not PSD by design**. That assertion must be dropped or replaced with a
reasonable negative-eigenvalue floor check.

---

## Missing: Hamiltonians (`tests/test_hamiltonians.py` — does not exist)

**T-009 / T-010** — `contact_matrix()` weight schemes and geometry  
**T-011** — Structural/spectral smoke tests for H1–H13  
**T-012** — `build_H_new()` structural invariants (see PSD caveat above)  
**T-013** — Each potential function in `potentials.py`

---

## Missing: Propagators

**T-014** — `time_averaged_ctqw()` on 2-node dimer → long-time average ≈ 0.5  
**T-016** — `ctqw()` and `heat()` spatial decay on 50-node synthetic helix

**Not yet in TASKS.md — must be added:**  
`heat()` called with indefinite H_new output should either raise a clear error or
be documented as unsupported. Add a test that confirms one of these behaviors.
See `../improvements/hamiltonian_code.md` IMP-H4.

---

## Missing: Metrics

**T-015** — `ipr`, `spectral_gap`, `check_degree_correlation` on known-answer graphs

---

## Unconfirmed oracle values

**T-004 / T-017** — `test_eff_rank_kras_regression` oracle (~117.7) not confirmed.
Test must carry `@pytest.mark.xfail(strict=False)` until a reproducible run with
documented conditions pins the oracle. See TASKS.md T-017 for the blocker.
