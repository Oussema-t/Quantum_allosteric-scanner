# TESTS.md — Testing Standards and Index

**Scope:** All files under `tests/`  
**Last updated:** 2026-06-21

---

## Where to find things

| Topic | File |
|-------|------|
| Existing test bugs (T-001–T-008) | `TASKS.md` Group A — canonical, do not restate here |
| Missing test coverage (T-009–T-016) | `improvements/test_coverage.md` |
| Unconfirmed oracle values | `improvements/test_coverage.md` + TASKS.md T-017 |

**One non-obvious correction not in TASKS.md:** T-012 asserts H_new is PSD
(eigenvalues ≥ −1e-10). H_new is **not PSD by design** (see HAMILTONIANS.md).
That assertion must be dropped or replaced with a reasonable negative-floor check.

---

## Core Principles

### Transparency
Every test must state **what physical or mathematical property it is verifying**,
not just that the function runs. A test without a meaningful invariant creates
false confidence.

### Reproducibility
- No test depends on network access or external PDB fetches without an explicit
  `pytest.mark.network` marker and a skip guard when unavailable.
- Random state must be seeded explicitly. Never use numpy's global RNG state.
- Float tolerances must be explained inline: state the theoretical error bound,
  then add modest headroom. Do not use round numbers (`atol=2e-2`) without a comment.

### Absolute clarity
- Oracle values in regression tests must come from a confirmed, reproducible run
  documented with: protein, PDB ID, cutoff, λ values, propagation time.
- Parametrized test IDs must be human-readable — wrap `np.linspace(...)` in `list()`
  or round to 4 d.p. before passing to `@pytest.mark.parametrize`.

---

## Standards for every new test

### Hamiltonian tests (minimum required for any new H_X)
1. Shape is `(N, N)`
2. Symmetric: `np.testing.assert_allclose(H, H.T, atol=1e-12)`
3. For Laplacian-based: row sums ≈ 0, `np.allclose(H.sum(axis=1), 0)`
4. Eigenvalue sign documented: PSD → `min(eig) ≥ -1e-10`; indefinite → state it explicitly
5. Limiting case: e.g., all λ → 0 recovers the base Laplacian

### Propagator tests (minimum required for any new propagator)
1. Normalization: `p.sum() ≈ 1`
2. Non-negativity: `(p >= 0).all()`
3. Initial condition: at `t=0`, `p[source] ≈ 1`
4. At least one non-trivial **spatial** assertion — not just sum-to-one

### Synthetic data preference
Use small, deterministic synthetic coordinate arrays (4-point collinear, 6-point
helix, 10-residue chain) over real PDB files wherever possible. Synthetic data has
known analytical properties, requires no network access, and runs fast.

When a real protein is required (regression tests), document: PDB ID, chain,
resolution, and all parameters used to generate the reference value.
