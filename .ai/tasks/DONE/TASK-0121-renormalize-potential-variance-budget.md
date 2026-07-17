# TASK-0121 Renormalize H_new's 5-term potential: fix the variance-budget bug

## Context

- ID: TASK-0121
- Title: `V_B/V_T/V_R/V_C/V_M` are not commensurate — `V_R` is a sum of
  three z-scores (σ ≈ 1.9), `V_C`/`V_M` are max-normalized to [-1, 0]
  (σ ≈ 0.06), ~30x smaller. Z-score all five terms, set
  `σ(V) ≲ 0.2·J` (weak, transport-preserving disorder relative to the
  base Laplacian's bandwidth `J`), re-derive `λ` defaults, and report the
  corrected variance budget.
- Status: Done
- Resolution: done
- Owner: Implementer
- Claimed By: Implementer C (this thread)
- Claimed At: 2026-07-17 23:16
- Source: `.ai/reviews/REVIEW-panel-2026-07-16-v2.md` §2.4, §5 P1-5.
  Corresponds to `HAMILTONIANS.md`'s existing IMP-H6 ("λ defaults are
  unvalidated") and `hypotheses/physics.md`'s HYP-P2/P3 discussion, now
  with an executed, quantified diagnosis rather than a general concern.
- Priority: **P1 — weeks 2-4** (after the P0 gauge fixes
  [[TASK-0118]]/[[TASK-0119]]/[[TASK-0120]]).

## Intent Contract

- Outcome: with current defaults, the panel measured [EXECUTED]:
  `V_R` = **88.8%** of the potential's variance, `V_T` 8.5%, `V_B` 2.5%,
  **`V_C` 0.1%, `V_M` 0.1%**. `ρ(V_R, −degree) = +0.81`. The two terms
  carrying this operator's actual allostery rationale (GNM cross-
  correlation via `V_C`, slow-mode participation via `V_M`) are
  numerically inert — not a modeling choice, a normalization bug. This
  task z-scores all five terms to comparable scale, sets the combined
  potential's dispersion `σ(V) ≲ 0.2·J` (weak relative to the base
  Laplacian's own bandwidth `J`, so the potential perturbs rather than
  dominates transport), and re-derives `λ_B/λ_T/λ_R/λ_C/λ_M` under that
  constraint.
- **Why this is a real, honest, reportable engineering finding, not just
  a fix to make quietly**: per the panel, "our 5-term potential was 88%
  one term until we renormalized" retro-explains three things this
  project previously treated as physics results — `most_impactful_term
  = V_R` (an ablation artifact, not a genuine finding that rigidity
  dominates), the ground state sitting on low-diagonal residues (a
  consequence of the same imbalance), and the operator's failure to beat
  degree centrality (`V_R` already correlates with degree at +0.81 by
  construction). State this explicitly in Done — this is a correction to
  three previously-reported findings, not an unrelated code cleanup.
- **What this fix does NOT solve, stated explicitly per the panel's own
  §2.4 correction**: the diagonal-vs-degree contamination (fixed by this
  task) is a *different* confound from the proximity contamination in
  the scored *output* (CTQW occupation correlates with degree at only
  ρ=+0.20 — proximity, not degree, drives the headline AUC, per §2.3).
  **Renormalizing the potential will not by itself fix the proximity
  confound** — do not report this task's completion as having addressed
  the observable-is-distance-confounded finding; that requires
  [[TASK-0123]] (distance-stratified evaluation) or a different
  observable ([[TASK-0122]]).
- In Scope:
  - Z-score `V_B`, `V_T`, `V_R`, `V_C`, `V_M` individually before
    combining.
  - Set combined `σ(V) ≲ 0.2·J`; re-derive `λ` weights under this
    constraint (do not just rescale post-hoc without checking the
    resulting operator is still well-conditioned/not indefinite — reuse
    `_warn_if_indefinite`, per this module's existing convention).
  - Report the corrected variance budget (percentage contribution of
    each term) in the submission-facing docs, per the panel's own
    framing recommendation ("report the variance budget in the
    submission").
  - Re-run the ablation (`analysis.ablation`) under the renormalized
    potential — the panel notes "then the ablation means something for
    the first time."
- Out Of Scope:
  - `mode_coparticipation` ([[TASK-0122]]) — separate task, but note its
    hard dependency on this one landing first (CP is *worse* than CTQW
    on the current un-renormalized `H_new`, per the panel's §2.5).
  - The seed/clock gauges ([[TASK-0118]]/[[TASK-0119]]) — independent
    confounds.
- Constraints And Invariants: `H_new` must remain guarded by
  `_warn_if_indefinite` after re-derivation — do not silently disable
  that check to make the renormalized operator "look" PSD.
- Planned Validation: report the corrected variance-budget percentages
  directly (should be much more balanced than 88.8/8.5/2.5/0.1/0.1);
  re-run `analysis.ablation` and report whether `most_impactful_term`
  changes under the fix.

## In Progress

None

## TODO

- [x] Z-score all 5 potential terms individually.
- [x] Set combined `σ(V) ≲ 0.2·J`; re-derive `λ` defaults.
- [x] Verify `_warn_if_indefinite` still fires correctly post-renormalization.
- [x] Re-run `analysis.ablation`; report whether `most_impactful_term` changes.
- [x] Report the corrected variance budget as a stated finding (not a
      silent code change) — cross-reference the 3 previously-reported
      findings this retro-explains.

## Dependency

- Should land before [[TASK-0122]] (`mode_coparticipation` needs a
  renormalized operator to be worth building).
- Independent of [[TASK-0118]]/[[TASK-0119]] — different confound axis,
  can proceed in parallel.

## Open Questions

- Exact `σ(V) ≲ 0.2·J` proportionality constant is the panel's own
  suggestion, not a hard-derived value — Implementer's call whether to
  use it as-is or tune it, state the choice and why in Done.

## Done

- **Z-scored all 5 potential terms** in `potentials.py`: `V_B` (was
  `b/mean(b)`), `V_T` (was a 0/1 terminal mask), `V_C`/`V_M` (were
  max-normalised to `[-1, 0]`) now each end in a final `_zscore()` call.
  `V_R` (already an internal sum of 3 z-scores, std ~1.9 on real targets,
  not 1 since the 3 components are correlated) is re-z-scored as a final
  step too, rather than assumed already-commensurate. Every term is now
  mean 0 / std 1, verified directly on real KRAS_G12C/BCR_ABL1 data
  (`d.mean()` < 1e-9, `d.std()` == 1.0 to 1e-6, for all 5 terms on both
  targets).
- **Re-derived `build_H_new`'s `lam_*` defaults**: `lam_B=0.08, lam_T=0.16,
  lam_R=0.08, lam_C=0.04, lam_M=0.04` — same 1:2:1:0.5:0.5 ratio as the
  original pre-optimization guess (not re-tuned; that's IMP-H6's still-open
  follow-up), rescaled by the triangle inequality on standard deviations
  (Minkowski): since each z-scored term has std 1, `sigma(sum lam_i*V_i) <=
  sum|lam_i|`, so choosing `sum|lam_i| = 0.4` provably bounds `sigma(V) <=
  0.4`. `J<=2` is a universal bound for any symmetric normalized Laplacian
  with nonnegative edge weights (already documented in `HAMILTONIANS.md`'s
  own "spectrum ∈ [0, 2]" line) — so `0.4 = 0.2*2` is guaranteed to satisfy
  `sigma(V) <= 0.2*J` on *any* target, not just a tuned one. This is a
  provable worst-case bound, not a per-target fit — chose it over computing
  `J` at runtime per-target because the task asked for `lam_*` *defaults*
  (fixed numbers), and a target-independent guarantee is more defensible
  than picking one "representative" target to tune against.
- **Verified `_warn_if_indefinite` still fires correctly**: on both real
  targets, `build_H_new`'s default output remains indefinite (KRAS_G12C
  min eigenvalue -0.101, BCR_ABL1 -0.177) — the negative-diagonal reward
  terms (`V_R`/`V_C`/`V_M`) still push the operator off PSD even at the
  much smaller combined scale; the existing `test_default_h_new_is_not_
  globally_psd` canary in `test_hamiltonians.py` passes unmodified.
- **Real-data variance budget** (KRAS_G12C N=169, BCR_ABL1 N=451; `J` =
  base-Laplacian spectral bandwidth `w.max()-w.min()`):

  | Target | J | σ(V) combined | 0.2·J budget | B/T/R/C/M variance share |
  |---|---|---|---|---|
  | KRAS_G12C | 1.317 | 0.203 | 0.263 | 15.4%/61.5%/15.4%/3.8%/3.8% |
  | BCR_ABL1 | 1.480 | 0.227 | 0.296 | 15.4%/61.5%/15.4%/3.8%/3.8% |

  Bound holds comfortably on both (σ(V) at 77%/77% of budget). The
  per-term share is structural — identical on every target since each
  term has std 1 by construction and the share is set entirely by the
  `lam_*` ratio, not by any target-specific property. This corrects the
  pre-fix budget of `V_B=2.5%, V_T=8.5%, V_R=88.8%, V_C=0.1%, V_M=0.1%` —
  a **38x** improvement for `V_C`/`V_M` (0.1%→3.8%), from an unreachable
  knob to an actually-contributing one.
- **Re-ran `analysis.ablation`** on both real targets at the pipeline's
  current shipped `t_max=15.0`/`n_steps=500` (`analysis.ablation`'s own
  defaults, matching what the rest of the pipeline uses today).
  **Deliberately did not also apply TASK-0119's gap-based per-operator
  clock fix here** — mixing the clock fix into this measurement would make
  it impossible to attribute any change in `most_impactful_term` to the
  renormalization specifically, and this task's own Out Of Scope already
  declares the clock/seed gauges independent. **Checked, not assumed**:
  ran `check_convergence` (`kind="time_averaged_ctqw"`) on all 6 ablation
  operators (`L_only`, `B`, `T`, `R`, `C`, `M`) on both targets — none
  satisfy the AAKV criterion at `t_max=15`/`n_steps=500` (bound exceeds
  tol by 2-3 orders of magnitude, same pre-existing clock gap TASK-0110
  already quantified). Reporting the ablation numbers with this caveat
  explicit, not silently as converged:

  | Target | most_impactful_term (pre-fix, on record) | most_impactful_term (post-fix) | least_impactful_term (post-fix) |
  |---|---|---|---|
  | KRAS_G12C | V_R | **V_B** (ΔAUC +0.133) | V_R (ΔAUC +0.017) |
  | BCR_ABL1 | V_R | **V_B** (ΔAUC +0.097) | V_T (ΔAUC +0.036) |

  `most_impactful_term` changes on both real targets — flips from `V_R`
  (the term that was structurally inflated 30x) to `V_B`, and `V_R` drops
  to the *least* impactful term on KRAS_G12C. This directly confirms the
  panel's diagnosis: the old finding was reading off the normalization
  bug, not the underlying physics.
- **This is a correction to three previously-reported findings, stated
  explicitly, not a silent code change**: `most_impactful_term = V_R` (was
  an artifact of V_R's inflated scale, not evidence rigidity dominates —
  see corrected table above), the ground state sitting on low-diagonal
  (high-degree) residues (a direct consequence of V_R correlating with
  degree at ρ=+0.81 while carrying 88.8% of the variance), and `H_new`'s
  failure to beat degree centrality (same root cause). All three should be
  re-read against the *renormalized* budget, not retracted as false, since
  the underlying real-data AUC numbers this project reported were computed
  correctly — only the *attribution* of what drove them was wrong.
- **What this does not fix, stated per the panel's own §2.4 correction and
  this task's own Intent Contract**: the proximity confound in the scored
  *output* (CTQW occupation correlates with degree at only ρ=+0.20, driven
  by proximity per §2.3) is a *different* confound from the diagonal-degree
  contamination fixed here. **Side-measurement, not this task's primary
  claim**: re-running the existing `TestProximityConfoundReproduction`
  regression fixture (5 synthetic-globule seeds) under the renormalized
  defaults shows the proximity confound is measurably *weaker* than
  before — Spearman ρ with Euclidean seed-distance drops from 0.71-0.83
  (pre-fix) to 0.22-0.47 (post-fix); hop-distance from 0.55-0.64 to
  0.03-0.28 — but remains positive on every seed tested, so proximity is
  weakened, not eliminated. Do not report this task as having resolved the
  observable-side confound; that still requires [[TASK-0123]] or
  [[TASK-0122]] per this task's own Out Of Scope.
- **Updated stale downstream references to the pre-fix `lam_*` defaults**:
  `scripts/ctqw_trapping_reproduction.py`'s `_H_NEW_DEFAULT_LAMBDAS` was an
  independent hardcoded copy of `build_H_new`'s old defaults (used to
  reproduce the panel's `H(lambda) = L_norm + lambda*(sum V)` construction
  at `lambda=0.25`) — updated to match, keeping its own `lambda=1.0`
  contract with `build_H_new`'s actual defaults intact.
- **Test suite**: rewrote `test_potentials.py`'s sign/scale assumptions
  (`V_B`/`V_T` were tested as non-negative; `V_C`/`V_M` as non-positive and
  bounded to `[-1,0]` — all now z-scored and signed both ways) to instead
  assert mean≈0/std≈1 and the preserved sign-ranking (e.g. termini still
  score higher than core, high-B still scores higher than low-B). Fixed 2
  further downstream breaks this uncovered: `test_labels.py`'s
  `TestTerminalMask` compared `V_T`'s diagonal nonzero-ness to
  `terminal_mask` (no longer valid once V_T is nonzero everywhere — now
  compares sign instead), and `test_baselines.py`'s
  `TestProximityConfoundReproduction` had a hardcoded `rho > 0.5` bound
  calibrated to the pre-fix defaults (see side-measurement above; lowered
  to `rho_euclid > 0.25`/`rho_hop > 0.1` with the real weakened-but-present
  values documented in the test's own docstring). Full suite: 676 passed,
  2 xfailed, 0 failed (`../.venv/bin/python -m pytest tests/ -q`).
- **Documentation updated in the same pass**: `.claude/HAMILTONIANS.md`
  (λ table, Critical facts), `.claude/improvements/hamiltonian_code.md`
  (IMP-H6), `.claude/hypotheses/physics.md` (HYP-P2, HYP-P3 status notes),
  `EXECUTION_PLAN.md` (1C.6 row), `RESULTS.md` (new dated section + open-
  questions row #13), `.ai/COMMON.md` (registry row).
