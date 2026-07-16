# TASK-0119 Fix the clock: per-operator t* from spectral gap, re-run the operator comparison

## Context

- ID: TASK-0119
- Title: Replace the single hardcoded `t_max=15` (applied identically to
  every operator regardless of its own energy scale) with a per-operator
  timescale derived from its spectral gap (or an equivalent hopping-norm
  normalization of `H` before propagation); re-run the 96-cell operator
  sweep ([[TASK-0101]]) and the CTQW-trapping reproduction ([[TASK-0106]])
  under it.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `.ai/reviews/REVIEW-panel-2026-07-16-v2.md` §2.2, §5 P0-2.
- Priority: **P0 — this week.**

## Intent Contract

- Outcome: (1) a per-operator `t*` — the panel's proposal is
  `t* ≈ 1/Δλ` (the graph mixing time from `H`'s spectral gap), or
  equivalently normalizing `H` by its hopping norm before propagation so
  every operator is compared at the same *effective* time, not the same
  *nominal* `t`; (2) the operator comparison ([[TASK-0101]]'s 96-cell
  sweep) re-run under per-operator `t*` instead of the shared
  `t_max=15`; (3) [[TASK-0106]]'s BCR_ABL1 CTQW-trapping reproduction
  re-run the same way.
- **What this task must NOT conclude, per the panel's own executed
  correction (§2.2):** do not treat a shift in the `H10`-vs-`H_new`
  *ranking* under the fixed clock as evidence the original trapping
  finding was "mostly a units artifact." The panel re-ran this exact
  check: after normalizing each operator by its hopping scale, `H_new`
  stays strongly localized (participation ratio 1.3→3.8 across
  t=15→1500) while a clean Laplacian spreads (14.7→83.7) and `H10`
  spreads (23.5→48) — **the localization is gauge-robust and real**,
  driven by `H_new`'s 7-10× disorder/bandwidth ratio (itself a
  gauge-invariant quantity, established in the same review's §2.4).
  Expect the operator *ranking* to shift under the fixed clock; report
  that `H_new`'s localization independently survives it — both facts,
  not one in place of the other.
- **Secondary correction to land in the same pass**: [[TASK-0106]]'s own
  Done section reads a *higher* `H_new` participation-ratio/N (0.299 vs.
  `H10`/`H2`'s 0.056/0.054) as evidence `H_new` "stays markedly closer to
  the seed" — this is backwards. `_transport_participation_ratio` =
  `1/(N·Σp²)`; **high PR means delocalized, low PR means localized**.
  Correct TASK-0106's prose narrative direction (the underlying numbers
  and the localization conclusion are still correct — only the
  PR-value-to-localization-direction mapping in the write-up is wrong).
  Do this as a documentation correction in TASK-0106's own Done section
  (additive note, do not delete the original text), not a silent edit.
- In Scope:
  - Implement the per-operator `t*` (spectral gap of `H`, reusing
    `np.linalg.eigh`'s already-computed eigenvalues where available —
    same reuse discipline as [[TASK-0109]]).
  - Re-run [[TASK-0101]]'s 96-cell sweep and [[TASK-0106]]'s BCR_ABL1
    reproduction under it.
  - Report both the shifted ranking and the surviving-localization
    finding explicitly, per the "must NOT conclude" section above.
- Out Of Scope:
  - Building the general `check_convergence` validity gate — that is
    [[TASK-0109]]'s own scope (Nyquist/spectral-gap checks as a
    reusable function). This task consumes whatever timescale
    convention TASK-0109 lands on if it lands first; if TASK-0109 is
    not yet done, use the panel's `t* ≈ 1/Δλ` formula directly as an
    interim, explicitly flagged as such, rather than blocking.
  - The seed-gauge fix ([[TASK-0118]]) — separate confound.
- Constraints And Invariants:
  - Every re-run number in this task's Done section must state which
    `t*` convention produced it.
- Planned Validation: re-run [[TASK-0101]]/[[TASK-0106]] under the new
  clock; report the delta against the old shared-`t_max=15` numbers
  explicitly, not just the new numbers in isolation.

## In Progress

None

## TODO

- [ ] Implement per-operator `t*` (spectral-gap-derived or hopping-norm
      normalization) — state which, and why, in Done.
- [ ] Re-run [[TASK-0101]]'s 96-cell operator sweep under it.
- [ ] Re-run [[TASK-0106]]'s BCR_ABL1 reproduction under it.
- [ ] Report ranking shift vs. localization-survival as two separate,
      explicit findings — do not merge them into one conclusion.
- [ ] Correct TASK-0106's PR-direction narrative bug (additive note).

## Dependency

- Soft dependency: [[TASK-0109]] (if its `check_convergence` timescale
  convention lands first, use it; otherwise use the panel's `t*≈1/Δλ`
  directly as an interim, flagged as such).
- Should ideally run after [[TASK-0118]]'s seed-convention fix lands, so
  the re-run isn't done twice under two different seed conventions —
  soft ordering, not a hard block.

## Open Questions

- Whether `t* ≈ 1/Δλ` or hopping-norm `H` normalization is the better
  practical choice for this codebase — Implementer's call, state which
  and why in Done; the panel offers both as equivalent options.

## Done

(not yet)
