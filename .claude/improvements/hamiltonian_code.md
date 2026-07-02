# Hamiltonian Code Improvements

**Scope:** `src/allostery/hamiltonians.py`, `src/allostery/potentials.py`  
**Type:** Concrete, actionable code changes — not scientific hypotheses.  
Cross-reference: scientific motivation for each improvement is in `../hypotheses/physics.md`.

---

## IMP-H1 · Scale `n_low_modes` with protein size

**File:** `potentials.py`, `V_M()`  
**Current:** `n_low_modes=10` hardcoded default.  
**Problem:** 10 modes covers 20% of the non-trivial spectrum for N=50 but only 2%
for N=500. The notebook already uses `min(40, N-1)` for ProDy and searches `n_low`
over `[5,8,10,12,15]` in `sample_params` — the module default is inconsistent with both.  
**Fix:**
```python
n_low = max(5, int(round(len(coords) * 0.05)))
```
Applied as the default inside `V_M` (and propagated through `build_H_new`).  
The 5% heuristic should be validated against `OPT` results once Phase 3 CV runs.

---

## IMP-H2 · Rename V_C and fix its docstring

**File:** `potentials.py`, `V_C()`  
**Problem:** The docstring claims "inverse-distance weighted covariance as a proxy for
dynamic coupling." The implementation is `W_invdist.sum(axis=1)` — a **weighted contact
degree**, not covariance. The name V_C is misleading.  
**Fix:** Rename to `V_D` (degree centrality) or `V_Cent`. Update docstring to say
"inverse-distance weighted contact degree — a structural centrality proxy."  
True dynamic covariance (from GNM pseudo-inverse) is a separate hypothesized
improvement; see HYP-P3 in `../hypotheses/physics.md`.

---

## IMP-H3 · Eliminate redundant intermediate computations in `build_H_new`

**File:** `hamiltonians.py`, `build_H_new()`  
**Problem:** Every call builds the contact matrix three times and runs one full `eigh()`:
- Base Laplacian: `normalised_laplacian_alpha()` calls `contact_matrix()` internally
- `V_R()`: calls `contact_matrix(weight="binary")` internally
- `V_C()`: calls `contact_matrix(weight="invdist")` internally
- `V_M()`: calls `H8_gnm()` (which calls `contact_matrix()`) then `np.linalg.eigh()`

For ceiling search (500+ trials × N proteins) this is prohibitive.  
**Fix:** Compute shared intermediates once, pass as optional arguments:
```python
def build_H_new(coords, bfactors, *, W_bin=None, W_exp=None, W_inv=None, gnm_modes=None, ...):
    if W_bin is None:
        W_bin = contact_matrix(coords, cutoff=cutoff, weight="binary")
    ...
```

---

## IMP-H4 · Document and guard against `heat()` + indefinite H_new

**Files:** `propagators.py` (`heat()`), `hamiltonians.py` (`build_H_new()`)  
**Problem:** `heat()` computes `exp(-w*t)`. If `w < 0` (which H_new produces from
V_R, V_C, V_M reward terms), this grows without bound for large `t`.  
**Fix options:**
1. Add guard in `heat()`: raise `ValueError` if `(w < -1e-8).any()`.
2. Clip: `exp_w = np.exp(-np.clip(w, 0, None) * t)` with a warning.
3. Document in `build_H_new()` docstring: "H_new is indefinite; use `ctqw()` or
   `haken_strobl()`, not `heat()`."

Option 3 is sufficient for now; option 1 is safest long-term.

---

## IMP-H5 · Improve V_R burial proxy

**File:** `potentials.py`, `V_R()`  
**Current:** `degree = W_binary.sum(axis=1)` — binary contact count.  
**Problem:** Binary degree conflates local clustering with burial.  
**Better proxy:** Use the exponential-decay weighted degree instead:
```python
W_exp = contact_matrix(coords, cutoff=cutoff, weight="exponential", alpha=alpha)
degree = W_exp.sum(axis=1)
```
Naturally down-weights peripheral contacts. SASA values are strictly superior if
available from the structure.

---

## IMP-H6 · Promote cross-validated λ defaults into `build_H_new`

**File:** `hamiltonians.py`, `build_H_new()`  
**Current:** `lam_B=1.0, lam_T=2.0, lam_R=1.0, lam_C=0.5, lam_M=0.5` are
pre-optimization guesses (the `DEFAULT_PARAMS` before any search ran in the notebook).  
**Action:** Once Phase 3 LOPO CV is complete, aggregate the per-protein `OPT` params
(median or cross-validated mean) and update these defaults. Document the protein set
and CV conditions in the docstring.

---

## IMP-H7 · H13 comparison and potential refactoring of propagators

**Files:** `hamiltonians.py` (`H13_3N_anm_hessian()`), `propagators.py`  
**Motivation:** H13 is the most physically rigorous operator in the current codebase —
it encodes bond orientation via `r⊗r` outer products. The only thing preventing its
use in the scoring pipeline is the dimensional mismatch (3N×3N vs the N×N operators
that `ctqw()`, `heat()`, and `haken_strobl()` currently accept).  
**This is not a fundamental barrier.** It is an implementation constraint that should
only be maintained if the data justify it.

**Two options for comparison:**

**Option A — Scalar N×N projection (fast, conservative):**  
Project H13 to N×N by taking the trace of each 3×3 block:
```python
H_scalar[i, j] = np.trace(H13[3*i:3*i+3, 3*j:3*j+3])
```
This recovers an N×N matrix usable with current propagators, but discards the
orientational coupling information that makes H13 interesting.

**Option B — 3N×3N-native propagators (thorough, preserves physics):**  
Extend `ctqw()`, `heat()`, and `haken_strobl()` to accept 3N×3N input. After
propagation, sum per-residue occupation over the 3 spatial components:
```python
p_residue[i] = p_3N[3*i] + p_3N[3*i+1] + p_3N[3*i+2]
```
This preserves the anisotropic coupling fully and is the physically correct comparison.

**Decision protocol (data-driven):**
1. Implement Option A first (minimal effort, gives a quick bound)
2. Compare AUC: H13-scalar vs H_new (both at ceiling, same protein set)
3. If H13-scalar beats H_new → implement Option B; re-compare
4. If H13-scalar does not beat H_new → scalar projection discards the relevant physics;
   still implement Option B and compare before concluding H13 is not worth pursuing
5. Only if H13 Option B also does not beat H_new → confirm H_new as the baseline operator

**Do not assume H_new wins without running this comparison.**  
The dimensional mismatch was the only argument for not testing H13, and it is solvable.
The comparison is required for the scientific claim that H_new is the right operator.
