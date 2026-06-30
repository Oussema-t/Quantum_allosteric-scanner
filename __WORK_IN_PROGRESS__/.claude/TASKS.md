# TASKS.md — Clinic Cleveland Challenge

**Created:** 2026-06-21  
**Last updated:** 2026-06-26  
**Threads:** BLUE = Code generator | RED = Reviewer/Critic | ORCH = Orchestrator

**Criticism files (source of truth for task rationale):**
- `CRIT-001` → `.claude/criticism/test_physics_criticism.md` (test file quality)
- `CRIT-002` → `.claude/criticism/coverage_gaps_2026-06-21.md` (missing coverage)
- `CRIT-003` → `.claude/criticism/hamiltonian_physics_2026-06-25.md` (physics divergence vs QAS reference)

---

## Legend

| Field    | Values |
|----------|--------|
| Assignee | BLUE / RED / ORCH |
| State    | TODO / In Progress / Blocked / DONE / Rejected |
| Crit Ref | CRIT-001 §N or CRIT-002 GAP-N |

---

## Group A — Test file quality fixes (source: CRIT-001)

### T-001 · Remove dead code in test_physics.py
| Field    | Value |
|----------|-------|
| Assignee | BLUE |
| Crit Ref | CRIT-001 §1 |
| State    | DONE |

Removed: `rng = np.random.default_rng(0)`, `coords_fake = np.zeros((N, 3))`,
`from scipy.linalg import expm`, and the three unused hamiltonian imports
(`contact_matrix`, `H2_combinatorial_laplacian`, `H3_normalised_laplacian`).
Also moved `sys.path.insert` from the test file into `conftest.py`; added
`pyrightconfig.json` so Pylance resolves `src/allostery` without warnings.

---

### T-002 · Fix stale docstring in `test_haken_strobl_steady_state`
| Field    | Value |
|----------|-------|
| Assignee | BLUE |
| Crit Ref | CRIT-001 §3 |
| State    | DONE |

Docstring rewritten to explain the three tested regimes (low γ=0.5, mid γ=2.0,
high/Zeno γ=20.0) and why each `t_run` value guarantees >8 equilibration times.
CRIT-001 §9 (coarse atol) was also addressed in the same edit: `atol` tightened
from 0.05 to 1e-3, which is analytically supported by exp(−8) ≈ 3e-4 residual.

---

### T-003 · Make `test_ctqw_unitarity` actually verify `ctqw()` output
| Field    | Value |
|----------|-------|
| Assignee | BLUE |
| Crit Ref | CRIT-001 §2 |
| State    | DONE |

Added `np.testing.assert_allclose(ctqw(A, t, source=s), np.abs(U[:, s])**2, atol=1e-10)`
for all 15 source nodes. The manual U construction is now a documented
"reference" to make the comparison explicit.

---

### T-004 · Tighten `test_eff_rank_kras_regression` or mark it as a placeholder
| Field    | Value |
|----------|-------|
| Assignee | BLUE |
| Crit Ref | CRIT-001 §4 |
| State    | DONE |

Added `@pytest.mark.xfail(strict=False, reason="Oracle value ≈117.7 not yet
confirmed from notebook…")`. Narrowed the assertion from the meaningless
[50, 300] range to `abs(er - 117.7) < 30`. Switched from uniform placeholder
B-factors to real B-factors fetched from 4OBE via `prody` so the value matches
the notebook calculation. The test currently XPASS (confirming the oracle is in
range); final tightening to `< 5` is blocked on T-017.

---

### T-005 · Fix `test_haken_strobl_trace` to sample multiple time points
| Field    | Value |
|----------|-------|
| Assignee | BLUE |
| Crit Ref | CRIT-001 §5 |
| State    | DONE |

Now calls `haken_strobl` at `t ∈ {0.5, 2.0, 10.0}` × `γ ∈ {0.0, 1.0, 10.0}` =
9 total (t, γ) combinations, asserting `p.sum() ≈ 1` and `p ≥ 0` at each.

---

### T-006 · Fix silent fallback in `test_normalised_laplacian_bounds`
| Field    | Value |
|----------|-------|
| Assignee | BLUE |
| Crit Ref | CRIT-001 §6 |
| State    | DONE |

Replaced the random Erdős-Rényi graph + silent `path_graph` fallback with four
deterministic, always-connected graphs parametrized by topology label:
`path` (sparse), `cycle` (regular degree-2), `scale_free` (BA with seed=7),
`complete` (dense; max eigenvalue exercises the λ=2 bound).

---

### T-007 · Replace `np.linspace` with `list()` in `@pytest.mark.parametrize`
| Field    | Value |
|----------|-------|
| Assignee | BLUE |
| Crit Ref | CRIT-001 §7 |
| State    | DONE |

Changed to `list(np.round(np.linspace(0, 2*np.pi, 16), 4))`. Test IDs now read
`t=0.4189` instead of `t=0.41887902047863906`.

---

### T-008 · Align `atol` and inline comment in `test_bessel_line`
| Field    | Value |
|----------|-------|
| Assignee | BLUE |
| Crit Ref | CRIT-001 §8 |
| State    | DONE |

Changed `atol=2e-2` → `atol=1e-2`. Comment updated to state the empirical
tolerance, note that finite-chain boundary corrections are ~exp(−N²/8t) ≈ 1e-11
at the test parameters, and that the dominant error is floating-point.

---

## Group B — Missing test coverage (source: CRIT-002)

### T-009 · Add unit tests for `contact_matrix()` — weight schemes
| Field    | Value |
|----------|-------|
| Assignee | BLUE |
| Crit Ref | CRIT-002 GAP-1 |
| State    | TODO |

Create `tests/test_hamiltonians.py`. For a small synthetic coordinate array (e.g., 4 points in a line), assert the exact expected values for each weight scheme: `binary`, `gaussian`, `exponential`, `harmonic`, `invdist`. Verify symmetry and zero diagonal.

---

### T-010 · Add unit tests for `contact_matrix()` — cutoff and distance geometry
| Field    | Value |
|----------|-------|
| Assignee | BLUE |
| Crit Ref | CRIT-002 GAP-1 |
| State    | TODO |

Test that:
- Pairs with `dist >= cutoff` produce zero weight.
- Self-loops (diagonal) are always zero.
- The pairwise distances are computed correctly (compare against `scipy.spatial.distance.cdist` as a reference).

---

### T-011 · Add structural/spectral smoke tests for H1–H13
| Field    | Value |
|----------|-------|
| Assignee | BLUE |
| Crit Ref | CRIT-002 GAP-2 |
| State    | TODO |

For a fixed 6-point synthetic coordinate array, assert for each operator:
- Output shape is `(N, N)`.
- Matrix is symmetric.
- For Laplacian-based operators: all eigenvalues ≥ −1e-10, nullity ≥ 1.
- For adjacency-based operators (H1): matrix equals expected binary contact matrix.

A single parametrized test over `[H1, H2, ..., H13]` is sufficient.

---

### T-012 · Add unit tests for `build_H_new()`
| Field    | Value |
|----------|-------|
| Assignee | BLUE |
| Crit Ref | CRIT-002 GAP-3 |
| State    | TODO |

Using a synthetic 10-residue coordinate array and uniform B-factors, assert:
- Output is `(N, N)` and symmetric.
- All eigenvalues ≥ −1e-10 (positive semidefinite).
- Setting `lam_B=lam_T=lam_R=lam_C=lam_M=0` recovers `normalised_laplacian_alpha()` exactly.

---

### T-013 · Add unit tests for each potential function in `potentials.py`
| Field    | Value |
|----------|-------|
| Assignee | BLUE |
| Crit Ref | CRIT-002 GAP-4 |
| State    | TODO |

For each of V_B, V_T, V_R, V_C, V_M:
- Assert output shape `(N, N)`.
- Assert matrix is diagonal where physically expected (V_B, V_T).
- Assert non-negativity on the diagonal.
- For V_T: assert the penalty is zero outside terminal-residue indices.

---

### T-014 · Add tests for `time_averaged_ctqw()`
| Field    | Value |
|----------|-------|
| Assignee | BLUE |
| Crit Ref | CRIT-002 GAP-6 |
| State    | DONE |

On the 2-node dimer, the time average of `cos²(t)` over `[0, T]` → 0.5 as T → ∞. Assert `time_averaged_ctqw(H, t_max=200, source=0)[0] ≈ 0.5` within `atol=0.02`.

---

### T-015 · Add tests for `ipr`, `spectral_gap`, `check_degree_correlation`
| Field    | Value |
|----------|-------|
| Assignee | BLUE |
| Crit Ref | CRIT-002 GAP-6 |
| State    | DONE |

- `ipr`: a uniform eigenvector (all entries = 1/√N) should give IPR = 1/N; a localised vector (one entry = 1, rest 0) should give IPR = 1.
- `spectral_gap`: on `path_graph(5)` Laplacian, the gap equals the known second eigenvalue (≈ 0.382).
- `check_degree_correlation`: for a path graph with uniform scores, correlation should be near 0.

---

### T-016 · Add value-level CTQW and heat-kernel tests on a protein-like graph
| Field    | Value |
|----------|-------|
| Assignee | BLUE |
| Crit Ref | CRIT-002 GAP-5, GAP-7 |
| State    | DONE |

Create a synthetic 50-node coordinate array (e.g., a helical backbone at 3.8 Å spacing). Build its contact matrix with `cutoff=10.0, weight="binary"`. For `ctqw` and `heat`, assert:
- At `t=0`, probability is 1 at source and 0 elsewhere (before normalisation masks it).
- Probability decreases monotonically with graph distance at short times.
- `heat` converges to uniform distribution at large t.

These tests are immune to the normalisation-masking problem (GAP-5) because they check spatial structure, not just sums.

---

## Backlog / Deferred

### T-017 · Confirm `test_eff_rank_kras_regression` oracle from notebook
| Field    | Value |
|----------|-------|
| Assignee | ORCH |
| Crit Ref | CRIT-001 §4 |
| State    | Blocked |

Blocked on running the Phase 0 notebook with network access and confirmed PDB fetch. Once the eff_rank value is stable, hand to BLUE to implement T-004.  
**Note:** T-004 is now DONE (xfail + narrowed range); this task only unblocks the final tightening of `abs(er - ORACLE) < 5`.

---

## Group C — Hamiltonian physics alignment (source: CRIT-003)

*Goal: bring CCC's potential functions and contact-graph conventions to a physically
justified and internally consistent state, cross-validated against the QAS reference
implementation. No code is being sent to QAS at this stage.*

---

### T-018 · Benchmark GNM contact cutoff (7–10 Å) against crystallographic B-factors
| Field    | Value |
|----------|-------|
| Assignee | BLUE |
| Crit Ref | CRIT-003 PHY-1 |
| State    | TODO |

CCC defaults to `cutoff=10.0 Å`; QAS uses `cutoff=8.0 Å` (GNM literature standard).
The two values produce different contact networks, different spectra, and different CTQW
rankings — making cross-validation between repos impossible.

**Implementation:**
Using the 6 benchmark proteins (KRAS_G12C/4OBE, BCR-ABL1/1OPL, CARDIAC_MYOSIN/5TBY,
PTP1B/1SUG, GLUCOKINASE/1V4S, and one with available B-factors), compute:
- GNM Kirchhoff matrix at cutoffs 7.0, 7.5, 8.0, 9.0, 10.0 Å
- Predicted MSF = diagonal of Kirchhoff pseudo-inverse
- Pearson correlation between predicted MSF and experimental B-factors

Report the correlation table. Update `contact_matrix()` and all `cutoff` defaults in
`hamiltonians.py` and `potentials.py` to the value with the highest mean correlation.
Add the table as a comment block in `hamiltonians.py` near the `contact_matrix` signature.

**Acceptance:** a small benchmark script in `scripts/` or a new test fixture that records
the winning cutoff; the default in `hamiltonians.contact_matrix` updated accordingly.

---

### T-019 · Replace `V_C` invdist proxy with proper GNM dynamic cross-correlation (DCC)
| Field    | Value |
|----------|-------|
| Assignee | BLUE |
| Crit Ref | CRIT-003 PHY-2 |
| State    | DONE |

CCC's `potentials.V_C` computes an invdist row-sum (a static centrality heuristic).
QAS `analysis.V_covariance` computes the GNM pseudo-inverse covariance and normalises
it to obtain the dynamic cross-correlation (DCC) — the physically correct measure of
collective coupling.

**Implementation:**
Replace the body of `V_C` in `src/allostery/potentials.py`:

```python
# Current (wrong):
W = contact_matrix(coords, cutoff=cutoff, weight="invdist")
centrality = W.sum(axis=1)

# Target (GNM DCC):
from .hamiltonians import laplacian, contact_matrix
A = contact_matrix(coords, cutoff=cutoff, weight="binary")
K = laplacian(A)                                   # Kirchhoff
w, U = np.linalg.eigh(K)
nz = w > 1e-9
winv = np.where(nz, 1.0 / np.where(nz, w, 1.0), 0.0)
Cov = (U * winv) @ U.T                            # pseudo-inverse
d = np.sqrt(np.clip(np.diag(Cov), 1e-12, None))
nDCC = Cov / np.outer(d, d)
np.fill_diagonal(nDCC, 0.0)
centrality = np.abs(nDCC).sum(axis=1)             # mean absolute coupling
```

Output convention is unchanged: return `np.diag(-centrality_norm)`.

**Acceptance:** existing test T-015 (`check_degree_correlation`) should still pass.
Add a new assertion in `tests/test_hamiltonians.py` (T-013 scope): `V_C` diagonal values
must have Pearson r > 0.5 with the node's mean absolute DCC computed independently.

---

### T-020 · Extend `V_R` to include the MSF term (match QAS three-term formulation)
| Field    | Value |
|----------|-------|
| Assignee | BLUE |
| Crit Ref | CRIT-003 PHY-3 |
| State    | DONE |

CCC's `V_R` = `-(degree_norm / (b_norm + 0.1))` — degree and B-factor only.
QAS `V_rigidity` = `z(degree) + z(clustering) − z(MSF)` — adds the clustering
coefficient and the GNM mean-square fluctuation. The MSF term is essential: high-degree
loop residues are incorrectly rewarded by the CCC formula. MSF from GNM captures
dynamical flexibility directly.

**Implementation in `src/allostery/potentials.py`:**

1. Extract `gnm_msf(coords, cutoff)` as a small private helper that returns the diagonal
   of the Kirchhoff pseudo-inverse (reusable in V_M as well).
2. Compute clustering coefficient using `A @ A` diagonal / `deg * (deg-1)` (matching
   QAS `gnm_context`).
3. Combine: `score = -(z(degree) + z(clustering) - z(msf))` where z-scoring is done
   within the function (not across the protein — the calling convention stays the same).
4. Return `np.diag(score)` as before.

Note: the B-factor term is intentionally dropped from V_R because it is already captured
by the separate `V_B` term in `build_H_new`. Mixing it into V_R creates double-counting.

**Acceptance:** on a helical test coordinate array (synthetic, from T-016 fixture),
assert that residues at chain termini (high MSF, low clustering) receive a lower V_R
score than buried core residues.

---

### T-021 · Benchmark and document the five contact-weighting schemes
| Field    | Value |
|----------|-------|
| Assignee | BLUE |
| Crit Ref | CRIT-003 PHY-4 |
| State    | TODO |

CCC implements `binary`, `gaussian`, `exponential`, `harmonic`, `invdist` in
`contact_matrix()`. QAS uses `binary` only. No benchmark exists to justify the others.

**Implementation:**
1. For each of the 6 benchmark proteins, build the contact matrix at the cutoff chosen
   in T-018, using each of the five weight schemes.
2. Derive the GNM MSF (diagonal of Kirchhoff pseudo-inverse) for each.
3. Compute Pearson(MSF, B-factor) and rank the schemes.
4. Add a docstring table to `contact_matrix()` reporting the mean correlation across
   benchmarks for each scheme.
5. Update `build_H_new` to use the best-performing scheme for its base Laplacian
   (currently `exponential` via `normalised_laplacian_alpha`). If `binary` wins,
   change the default and note the reason.

**Acceptance:** the docstring table is present; `build_H_new`'s base scheme is
explicitly justified in a comment citing the benchmark result.
