# SEAM-0012 `propagators.check_convergence` exists but the real `t_max=15.0`/`n_steps=500` defaults have never been checked against it

- units: `propagators.check_convergence`/`min_adequate_t_max`/`min_adequate_n_steps`
  (TASK-0109, producer of the convergence *criterion*) -> the real numeric
  literals `t_max=15.0`/`n_steps=500` hardcoded at every call site across
  `analysis.py` (8 functions), `ceiling.py` (2 functions), `protocol.py`
  (`run_frozen_verdict`) (consumers of an implicit, never-verified
  convergence assumption)
- invariant: the real `t_max`/`n_steps` values these consumers actually use,
  on real target data, pass `check_convergence` (or the failure is explicit
  and acknowledged in `RESULTS.md`/the relevant task, not silently ignored)
- owner: [[TASK-0117]] (already hard-blocked on [[TASK-0109]] landing per
  `EXECUTION_PLAN.md`'s own 5.6/5.2 cross-links — that task's job is
  exactly "apply `ceiling.consistency_score`'s `t_max=15`/`n_steps=500`
  literals, TASK-0046's real 60-trial KRAS_G12C run used unchecked, to
  TASK-0109's now-existing check")
- seam-test: `tests/test_seam_0012_convergence_defaults.py::
  test_real_t_max_default_fails_bcr_abl1_spectral_gap_check` — `xfail`
  while `OPEN` (asserts the *currently known* failure explicitly, using
  [[TASK-0102]]'s own already-computed real BCR_ABL1 spectral gap
  (0.1933) rather than a fresh network fetch: `exp(-0.1933*15.0)=0.055 >
  tol=0.01` — `check_convergence` genuinely flags the real default as
  inadequate for `ground_state_relaxation` on this real target).
- status: **OPEN**
- provenance: opened 2026-07-15 while closing [[TASK-0109]] out of an
  abundance of caution against the exact failure mode `SEAM_PROTOCOL.md`'s
  own worked example describes — "every node was green... there was no
  edge to be red." `TASK-0109` built and tested the *criterion* in
  isolation (25 passing tests); nothing yet exercises it against the real
  numeric defaults every real scored verdict in this repo actually uses.
  `REVIEW-panel-2026-07-16-v2.md` section 2.2 independently names this
  exact gap ("t_max=15 is hardcoded and applied to every operator
  regardless of its energy scale... a precondition for the physics, not
  hygiene") and recommends `t* ~ 1/dlambda` per-operator, which
  `min_adequate_t_max` now supplies directly — TASK-0117 (or whichever
  task actually re-runs a real target under a corrected `t_max`) is the
  one that closes this seam, not TASK-0109 itself (explicitly out of its
  own scope, see its Done section).
- update 2026-07-16, [[TASK-0119]]: partial evidence gathered, status
  left OPEN (not VERIFIED) — TASK-0119 re-ran `analysis.py`'s
  `operator_sweep` (the 96-cell sweep) and TASK-0106's BCR_ABL1
  reproduction under `min_adequate_t_max`'s per-operator `t*` via a
  separate script (`scripts/fix_clock_operator_sweep.py`), not by
  changing `operator_sweep`'s own `t_max: float = 15.0` default or wiring
  the check into any production call path — real numbers now exist (most
  of CARDIAC_MYOSIN's `ctqw` floor-clears do not survive the corrected
  clock; `H_new`'s localization does), but every one of `analysis.py`'s 8
  functions, `ceiling.py`'s 2, and `protocol.run_frozen_verdict` still
  silently default to the uncorrected `t_max=15.0`/`n_steps=500` when
  called normally — this seam's invariant is not yet true of the shipped
  code, only demonstrated true of a parallel, offline re-run. TASK-0117
  (`ceiling.py` specifically) remains this seam's owner; whoever
  eventually wires a corrected clock into the real defaults (either task)
  is the one that flips this to VERIFIED.
- update 2026-07-17, [[TASK-0110]]: status remains OPEN, but the failure
  mode this seam names is now confirmed on real data for the *other*
  half of `check_convergence` — TASK-0119 deliberately used
  `min_adequate_t_max(kind="ground_state_relaxation")` (a simple
  2-eigenvalue-gap criterion), explicitly avoiding the
  `kind="time_averaged_ctqw"` AAKV-style all-pairs-min-gap criterion,
  which TASK-0109's own Done section already flagged as fragile on
  near-degenerate spectra. TASK-0110 is the real-data test of exactly
  that avoided criterion, since `time_averaged_ctqw` (not `ground_state_
  relaxation`) is this pipeline's actual headline propagator for every
  reported `AUC_apo_Hnew_*`/`AUC_ctqw_mean`. Result: the fragility is
  real, not hypothetical — required `t_max` is 145,000x (BCR_ABL1) to
  3,950,000x (CARDIAC_MYOSIN) the current default, and the matching
  `n_steps` (millions) makes a single `time_averaged_ctqw` call at the
  prescribed point **not return after 2+ hours** (measured directly, the
  process was confirmed still computing, not hung, before being killed).
  This sharpens this seam's own invariant statement: for the
  `time_averaged_ctqw` criterion specifically, "the failure is explicit
  and acknowledged" is not sufficient by itself — reaching the corrected
  value is not currently *computable* with this module's O(n_steps)
  Python-loop implementation, a stronger claim than "unperformed."
  `optuna_scan.py`'s own `max_n_steps` cap (20,000, vs. TASK-0119's
  independently-chosen 5,000 for the same class of problem on
  `ground_state_relaxation`/`operator_sweep`) is a practical workaround,
  not a resolution — every capped trial is Nyquist-*aliased*, flagged
  per-trial via `n_steps_capped`, never silently substituted for a
  converged answer. Real per-target evidence (closed-form prescription +
  Optuna cross-check + a properly-sampled "practical" ceiling restricted
  to the reachable range) in
  `.ai/tasks/DONE/TASK-0110-optuna-apo-holo-parameter-scan.md` and
  `results_task0110/`. Still does not flip this seam to VERIFIED — no
  production call site's default changed — but the evidence base for
  whoever eventually does (TASK-0117, or a follow-up addressing the
  O(n_steps) algorithmic cost itself, e.g. exploiting that the true
  infinite-time limit has a cheap closed form with no time loop at all)
  is now considerably larger.
