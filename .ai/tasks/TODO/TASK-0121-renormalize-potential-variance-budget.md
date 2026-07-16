# TASK-0121 Renormalize H_new's 5-term potential: fix the variance-budget bug

## Context

- ID: TASK-0121
- Title: `V_B/V_T/V_R/V_C/V_M` are not commensurate — `V_R` is a sum of
  three z-scores (σ ≈ 1.9), `V_C`/`V_M` are max-normalized to [-1, 0]
  (σ ≈ 0.06), ~30x smaller. Z-score all five terms, set
  `σ(V) ≲ 0.2·J` (weak, transport-preserving disorder relative to the
  base Laplacian's bandwidth `J`), re-derive `λ` defaults, and report the
  corrected variance budget.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
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

- [ ] Z-score all 5 potential terms individually.
- [ ] Set combined `σ(V) ≲ 0.2·J`; re-derive `λ` defaults.
- [ ] Verify `_warn_if_indefinite` still fires correctly post-renormalization.
- [ ] Re-run `analysis.ablation`; report whether `most_impactful_term` changes.
- [ ] Report the corrected variance budget as a stated finding (not a
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

(not yet)
