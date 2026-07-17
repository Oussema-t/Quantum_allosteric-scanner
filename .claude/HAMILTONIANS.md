# HAMILTONIANS.md — Index

**Scope:** `src/allostery/hamiltonians.py`, `src/allostery/potentials.py`  
**Last updated:** 2026-07-18

---

## Formula

```
H_new = L_norm(α, r_c)  +  λ_B·V_B  +  λ_T·V_T  +  λ_R·V_R  +  λ_C·V_C  +  λ_M·V_M
```

Base: normalised Laplacian of an exponential-decay contact graph (spectrum ∈ [0, 2]).  
V_B…V_M: all **diagonal**. Sign: `+` = penalty (disorder), `−` = reward (rigid hub).

Every V term is z-scored (mean 0, std 1) before weighting (TASK-0121,
2026-07-18) -- see Critical facts below for why.

| Term | Default λ | Sign | Proxy |
|------|-----------|------|-------|
| V_B | 0.08 | + | B-factor → flexibility penalty |
| V_T | 0.16 | + | terminal 5% → disorder penalty |
| V_R | 0.08 | − | degree / b_norm → rigidity |
| V_C | 0.04 | − | invdist contact degree → centrality (**misnamed — not covariance**, see IMP-H2) |
| V_M | 0.04 | − | participation in n_low GNM modes → slow-mode reward |

---

## Critical facts

- **H_new is NOT positive semi-definite.** V_R, V_C, V_M introduce negative diagonal
  entries. Do not use `heat()` with H_new (see IMP-H4).
- **All five potential terms are linearly redundant with each other.** Their sum is
  one diagonal matrix. The decomposition is for interpretability only.
  Off-diagonal extensions (V_pair) are the only way to strictly expand expressive power.
- **λ defaults are unvalidated.** They are pre-optimization guesses (same 1:2:1:
  0.5:0.5 ratio since inception). See IMP-H6.
- **Variance budget (TASK-0121, 2026-07-18): fixed a real normalization bug.**
  Before this fix, V_R's own internal sum-of-3-z-scores had std ~= 1.9 while
  V_C/V_M's max-[-1,0] normalisation gave std ~= 0.06 -- ~30x smaller, so V_R
  alone carried 88.8% of the combined potential's variance regardless of the
  `lam_*` ratio, and `lam_C`/`lam_M` were unreachable knobs
  (`REVIEW-panel-2026-07-16-v2.md` §2.4). All five terms are now individually
  z-scored (std 1 each); combined `sigma(V) <= 0.2*J` is guaranteed for any
  target via the triangle inequality (`J<=2`, the universal bound above).
  Naive per-term variance share is now B=15.4%/T=61.5%/R=15.4%/C=3.8%/M=3.8%
  (structural, from the `lam_*` ratio -- same on every target since each term
  has std 1 by construction). Real-target ablation (KRAS_G12C, BCR_ABL1) shows
  `most_impactful_term` flips from V_R (pre-fix, an artifact of its inflated
  scale) to V_B post-renormalization; V_R is now among the *least* impactful.
  See TASK-0121's Done section for full numbers and caveats.
- **n_low_modes=10 does not scale with protein size.** See IMP-H1.

---

## Where to find details

| Topic | File |
|-------|------|
| Code-level fixes (n_low, V_C rename, caching, PSD guard, V_R burial, λ calibration) | `improvements/hamiltonian_code.md` |
| Physical hypotheses (slow modes, pairwise terms, V_C covariance, base Laplacian ablation, H13) | `hypotheses/physics.md` |
| Ceiling definition and which operator to optimize | `hypotheses/ceiling.md` |
| H1–H13 baseline comparison table | (full table in previous session; preserved below) |

---

## H1–H13 vs H_new at a glance

| Operator | Base | Weights | Diagonal potential |
|----------|------|---------|-------------------|
| H1 | adjacency | binary | none |
| H2 | Laplacian | binary | none |
| H3 | norm. Laplacian | binary | none |
| H5 | Laplacian | Gaussian | none |
| H6 | Laplacian | exp-decay | none |
| H8 (GNM) | Laplacian | binary, 7.5 Å | none |
| H10 | Laplacian (comb.) | binary | V_B + V_T |
| H12 | Laplacian | ANM scalar | none |
| H13 | 3N×3N ANM | orientation-weighted | none — physically richest, not N×N |
| **H_new** | norm. Laplacian | exp-decay | V_B + V_T + V_R + V_C + V_M |

H_new improves on H10: normalised Laplacian + exp-decay weights + three reward terms.  
H_new is less physically rigorous than H13: scalar, isotropic, no bond orientation.

H13 is the physically richest operator. The 3N×3N dimensional mismatch with the
propagators is an implementation constraint, not a fundamental barrier. A data-driven
ceiling comparison (H13 vs H_new) is required before H_new can be declared the correct
operator. See `improvements/hamiltonian_code.md` IMP-H7 and `hypotheses/physics.md` HYP-P5.
