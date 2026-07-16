# TASK-0128 `calibrate_kappa`'s exactly-6-near-zero-mode assertion blocks 2/3 mandatory targets

## Context

- ID: TASK-0128
- Title: `superpose.calibrate_kappa`/`anm_modes` `raise ValueError` unless
  exactly 6 near-zero rigid-body ANM modes are found (TASK-0005's own
  hardening, `n_zero < 6` -> `n_zero != 6`). Discovered while running
  [[TASK-0099]]'s calibrated coherence-sensitivity sweep on all three
  mandatory targets: KRAS_G12C calibrates cleanly (`n_zero=6`), but
  BCR_ABL1 finds `n_zero=7` and CARDIAC_MYOSIN finds `n_zero=10` --
  both raise instead of calibrating, blocking any analysis that needs
  `gamma_scale`/`kappa` on those two targets.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: TASK-0099's real 3-target run, 2026-07-16 (Implementer A).
- Crit Ref: TASK-0005's own Done section already anticipated exactly this
  failure mode and flagged it as future work, not a surprise: *"This is
  correct for the single-chain targets this task validated against
  (KRAS_G12C), but a genuinely multi-chain/floppy-linker target (e.g.
  MYC_MAX's cMyc+Max+DNA assembly) might legitimately have more than 6
  near-zero-but-not-exactly-zero modes without being 'disconnected' in the
  error sense -- worth revisiting this strictness once a multi-chain
  target is actually run through this module."* That target has now
  actually been run (twice: BCR_ABL1, CARDIAC_MYOSIN), confirming the
  prediction.

## Intent Contract

- Outcome: determine *why* BCR_ABL1/CARDIAC_MYOSIN have 7/10 near-zero ANM
  modes instead of 6 (genuine multi-domain/floppy-linker softness vs. an
  actual disconnected contact graph at the configured `cutoff` vs. a
  numerical near-degeneracy at the `1e-8` threshold), then either (a) widen
  `calibrate_kappa`/`anm_modes`'s acceptance criterion appropriately (e.g.
  accept `n_zero >= 6` again but only after confirming the graph is
  actually connected via `operator_diagnostics`, restoring the original
  "≥6" intent without reintroducing the disconnected-graph false pass
  TASK-0005 fixed), or (b) confirm the strict check is catching a real bug
  on these targets and fix the actual root cause instead.
- In Scope:
  - Diagnose BCR_ABL1 (N=451, `n_zero=7`) and CARDIAC_MYOSIN (N=950,
    `n_zero=10`) directly -- print/inspect the extra near-zero eigenvalues'
    magnitudes and the corresponding mode shapes; check
    `diagnostics.operator_diagnostics(H13_3N_anm_hessian(...))`'s
    `n_components` for a real disconnection before assuming floppiness.
  - Decide and implement the fix (widened criterion, or a real bug fix),
    with a regression test per target case (synthetic disconnected graph
    must still raise; a synthetic multi-domain/floppy-linker construction
    with >6 legitimate near-zero modes must not).
  - Re-run [[TASK-0099]]'s coherence-sensitivity sweep on BCR_ABL1 and
    CARDIAC_MYOSIN once unblocked, and update `RESULTS.md`'s TASK-0099
    section from "blocked" to a real result.
- Out Of Scope: any other `superpose.py` functionality; TASK-0099's own
  classification logic (already correct and tested independently of this
  blocker).
- Planned Validation: the new regression tests above, plus a real re-run
  of TASK-0099's sweep on both previously-blocked targets.

## Dependency

- [[TASK-0005]] -- owns `calibrate_kappa`/`anm_modes`, source of the
  original `!= 6` hardening this task revisits.
- [[TASK-0099]] -- the consumer that discovered this; blocked on it for
  BCR_ABL1/CARDIAC_MYOSIN's own calibrated-gamma-scale result.

## Open Questions

- None yet -- root cause (floppiness vs. disconnection vs. numerical
  threshold) is this task's own first step to determine, not pre-decided
  here.

## Done

(not yet)
