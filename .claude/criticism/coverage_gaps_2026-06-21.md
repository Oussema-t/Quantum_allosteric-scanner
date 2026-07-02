# Code Review: Test Coverage Gaps — src/allostery/

**File reviewed:** `tests/test_physics.py` vs `src/allostery/hamiltonians.py`, `propagators.py`, `metrics.py`, `potentials.py`
**Review created:** 2026-06-21
**Review ID:** CRIT-002

---

## GAP-1 — `contact_matrix()` has zero test coverage

`hamiltonians.contact_matrix()` is the bridge between protein 3D coordinates and graph structure. Every H1–H13 and `build_H_new` depend on it, yet no test exercises it. Specific gaps:

- No test that the cutoff mask correctly excludes `dist >= cutoff` and self-loops (`dist == 0`).
- No test of weight schemes: `gaussian`, `exponential`, `harmonic`, `invdist` — formulae and parameters untested.
- No test that the pairwise distance tensor `coords[:, newaxis] - coords[newaxis, :]` is correct (axis ordering is easy to transpose silently).

---

## GAP-2 — H1–H13 operators are never called in any test

All thirteen Hamiltonian variants (the comparison baseline operators) have no test coverage. A sign flip, wrong normalisation, or incorrect Laplacian construction in any of them would be invisible. Minimum needed: for each operator, assert symmetry, correct shape, Laplacian spectral properties (non-negative eigenvalues, nullity = components) using a tiny synthetic coordinate set.

---

## GAP-3 — `build_H_new()` is untested except by a too-loose regression

`build_H_new` is the main submission operator. The only test (`test_eff_rank_kras_regression`) skips without network access and uses a tolerance range of [50, 300] against an expected value of ~117.7. No test checks that the five potential terms (V_B, V_T, V_R, V_C, V_M) are assembled with the correct signs and shapes, or that the result is symmetric and positive-semidefinite.

---

## GAP-4 — `potentials.py` (V_B, V_T, V_R, V_C, V_M) has no tests

The five potential functions composing `build_H_new` are completely untested. Each is a diagonal or structured matrix with a specific physical meaning:
- `V_B`: B-factor weighting — should be diagonal, non-negative.
- `V_T`: Terminal penalty — should be non-zero only at N/C-terminal indices.
- `V_R`: Residue-level regularisation.
- `V_C`: Contact-based correction.
- `V_M`: Low-frequency ANM mode contribution.

None of these properties are asserted anywhere.

---

## GAP-5 — Normalisation inside propagators makes conservation tests circular

`ctqw` ends with `p /= p.sum()` and `haken_strobl` ends with `p / p.sum()`. The tests that assert `p.sum() ≈ 1` (tests 3, 7, 8) will trivially pass even if the underlying physics is wrong (e.g., wrong sign in the Hamiltonian, wrong exponent, wrong commutator). The only non-circular tests are the ones comparing against exact analytical values (Rabi, Bessel, Haken-Strobl steady state). More such value-level tests are needed.

---

## GAP-6 — Utility functions in `metrics.py` and `propagators.py` are untested

The following are imported or exported but never tested:
- `metrics.ipr()` — Inverse Participation Ratio
- `metrics.spectral_gap()` — gap between smallest non-negative eigenvalues
- `metrics.check_degree_correlation()` — guardrail check for degree-driven scores
- `propagators.time_averaged_ctqw()` — time-average used as decoherent baseline
- `metrics.auc()`, `metrics.precision_at_k()`, `metrics.enrichment_at_k()` — evaluation metrics with edge cases (all-zero labels, k > N)

---

## GAP-7 — Tests use toy graphs only; no protein-shaped contact graph ever appears

Every test uses `cycle_graph`, `path_graph`, or `erdos_renyi_graph`. These have degree distributions and clustering properties very different from protein contact networks (sparse, spatially embedded, ~6 contacts per residue on average). Whether `ctqw`, `heat`, or `haken_strobl` behave physically on a real-protein-sized contact matrix is never verified. A single synthetic 50-residue helix-like coordinate array would be sufficient as a smoke test.
