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
