# Code Review: tests/test_physics.py

**File reviewed:** `tests/test_physics.py`
**Review created:** 2026-06-21 (no VCS; file timestamp is authoritative)

---

## 1. Dead code / unused identifiers

- **Line 82:** `rng = np.random.default_rng(0)` is declared but never used — the graph is seeded separately via `seed=42`.
- **Line 194:** `coords_fake = np.zeros((N, 3))` is created but never passed anywhere.
- **Line 30:** `expm` is imported from `scipy.linalg` but never called.
- **Lines 33–38:** `contact_matrix`, `H2_combinatorial_laplacian`, and `H3_normalised_laplacian` are imported but unused.

---

## 2. `test_ctqw_unitarity` doesn't test `ctqw` (lines 74–94)

The test builds `U` manually via eigen-decomposition and asserts `U†U = I`, but this only verifies the math identity — it doesn't compare against the `ctqw` function's output. The `ctqw` function is only tested for `p.sum() ≈ 1`, which is a much weaker check. A better test would assert:

```python
np.testing.assert_allclose(ctqw(A, t, source=s), np.abs(U[:, s])**2, atol=1e-10)
```

---

## 3. Stale docstring in `test_haken_strobl_steady_state` (line 153)

The first sentence of the docstring says "γ=500 (strong dephasing)" but the code uses `gamma = 2.0`. This is a leftover from a prior version and will mislead future readers.

---

## 4. `test_eff_rank_kras_regression` is not a regression test (lines 223–247)

The function name and docstring claim the expected value is ~117.7, but the assertion uses the range `[50, 300]` — a 6× window that catches essentially any plausible output. The comment "Once the number is confirmed… tolerance can be tightened" signals this is a placeholder, not a guard. Either tighten it (e.g., `abs(er - 117.7) < 5`) or mark it `@pytest.mark.xfail` until the oracle value is confirmed.

---

## 5. `test_haken_strobl_trace` docstring contradicts the test (line 173)

The docstring says "Trace(ρ) = 1 must be preserved at every time step," but the test only calls `haken_strobl` once at `t=5.0`. If trace conservation throughout the trajectory is the intent, the propagator would need to be called at multiple time points.

---

## 6. Silent fallback in `test_normalised_laplacian_bounds` (lines 258–259)

When the random graph is disconnected, the test silently substitutes `path_graph(n)`. Some parametrized cases may therefore never exercise the Erdős-Rényi path. The fallback should at minimum emit a `pytest.warns`, or use a fixed seed that guarantees connectivity.

---

## 7. `np.linspace` in `@pytest.mark.parametrize` (line 60)

Passing a numpy array directly produces unstable, float-heavy test IDs (e.g., `t=0.39269908169872414`). Wrapping in `list(...)` or rounding the values gives cleaner IDs and avoids potential serialisation quirks across pytest versions.

---

## 8. Tolerance inconsistency in `test_bessel_line` (line 141)

The comment says "finite-size corrections < 1e-2" but `atol=2e-2` is twice that stated bound. If the correction is genuinely < 1e-2 the tolerance should be tighter; if the bound is empirical, the comment should say so.

---

## 9. Coarse tolerance in `test_haken_strobl_steady_state` (line 164)

`atol=0.05` for a target of `1/N = 0.2` (N=5) allows a 25% relative error. If `t=100, gamma=2.0` are chosen to ensure tight convergence, the tolerance should reflect that (e.g., `1e-3`).
