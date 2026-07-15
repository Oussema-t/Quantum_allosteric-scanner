# TASK-0111 `propagators.ctqw`/`time_averaged_ctqw` redundantly recompute `eigh(H)`

## Context

- ID: TASK-0111
- Title: `time_averaged_ctqw(H, t_max, source, n_steps=500)` loops over
  `n_steps` calls to `ctqw(H, t, source)`, and `ctqw` computes
  `np.linalg.eigh(H)` from scratch on **every** call — `H` never changes
  across that loop, so `time_averaged_ctqw` does up to 500x more
  eigendecompositions than it needs to.
- Status: Done
- Owner: Implementer
- Source: found while investigating a `wip-all` test-suite hang
  (user-directed investigation, 2026-07-15). Root-caused to
  `test_ceiling.py::test_kras_g12c_real_target_ceiling_cross_check`
  (TASK-0046, another thread's new module): `ceiling.ceiling_search` runs
  60 optimization trials, each calling `time_averaged_ctqw` once
  (N=169, `n_steps=500`) — up to 60 × 500 = 30,000 redundant `eigh`
  calls. Isolated runtime: 109.31s (not hung, just slow) — the actual
  multi-hour apparent "hangs" were from accidentally running the full
  `wip-all` suite twice concurrently (this thread's own mistake, doubling
  BLAS thread contention on an already-borderline-slow test), not a bug
  in this function by itself. Still a real, worth-fixing inefficiency
  independent of that concurrency mistake.
- Scope: `__WORK_IN_PROGRESS__/src/allostery/propagators.py`'s `ctqw`/
  `time_averaged_ctqw` only.

## Intent Contract

- Outcome: `time_averaged_ctqw` computes `eigh(H)` **once** per call, not
  once per `n_steps` iteration — `ctqw`'s own public signature/behavior
  (a single-snapshot call, still computing its own `eigh` each time,
  since a caller may pass a different `H` each call) stays unchanged.
- In Scope:
  - factor the post-`eigh` evolution formula (`amplitudes = v @
    (exp(-i*w*t) * coeffs); p = |amplitudes|^2 / sum`) out of `ctqw` into
    a small private helper taking `(w, v, t, source)` directly.
  - `ctqw(H, t, source)` calls `eigh(H)` then the helper — behavior and
    signature byte-identical to today.
  - `time_averaged_ctqw(H, t_max, source, n_steps)` calls `eigh(H)`
    **once**, then loops calling the helper directly (not `ctqw`) for
    each `t` in the time grid.
  - regression test: old (redundant) and new implementations must
    produce bit-identical (or float-tolerance-identical) output on a
    real synthetic `H` — this is a pure performance refactor, not a
    behavior change, and must be proven so, not assumed.
  - a timing test/assertion that `time_averaged_ctqw` at a moderate
    `n_steps` is meaningfully faster after the fix (e.g., wall-clock
    comparison on a fixed-size synthetic `H`, generous tolerance — not a
    flaky micro-benchmark).
- Out Of Scope: `select.py::ballistic_exponent`, which has the same
  loop-calls-`ctqw`-repeatedly pattern (looping over `t_values`) — noted
  as a very likely follow-up instance of the same inefficiency, but a
  different module/owner boundary; not fixed here, flagged in Open
  Questions instead. `haken_strobl` (ODE-based, not eigh-based — not
  affected by this pattern at all).
- Constraints And Invariants: pure performance refactor — every existing
  caller of `ctqw`/`time_averaged_ctqw` (and everything built on them:
  `analysis.py`, `select.py`, `baselines.py`, this session's own
  `enaqt_gamma_sweep.py`/`ctqw_trapping_reproduction.py`/
  `nisq_noise_simulation.py` scripts) must see byte-identical output
  before/after. No public signature changes.
- Planned Validation: the bit-identical-output regression test above,
  plus re-running `test_ceiling.py`'s real-target test and confirming its
  wall-clock time drops substantially (target: well under the current
  109s, ideally closer to the ~1 eigh-call cost since 500 redundant ones
  are eliminated) with an unchanged pass/fail result and unchanged
  numeric assertions.

## Dependency

- None blocking — `propagators.py` (TASK-0008, Done) is the module under
  fix; no other task depends on this landing first.

## Open Questions

- `select.py::ballistic_exponent` has the same pattern (loops over
  `t_values` calling `ctqw` per point) — worth its own follow-up task
  once this one lands and the fix pattern is proven, not bundled in here
  (different module, different owner boundary per this session's
  established scope discipline).

## Done

- 2026-07-15, Implementer A. `propagators.py`: extracted `_ctqw_from_eigh
  (w, v, t, source)` — the post-`eigh` evolution formula `ctqw` already
  had, unchanged. `ctqw(H, t, source)` now calls `eigh(H)` then the
  helper (byte-identical behavior/signature to before). `time_averaged_
  ctqw(H, t_max, source, n_steps)` now calls `eigh(H)` **once**, then
  loops calling the helper directly (not `ctqw`) — eliminates
  `n_steps - 1` redundant eigendecompositions per call.
- **Controlled, same-moment A/B measurement** (not a cross-time
  comparison, which this sandbox's other concurrent sessions make
  unreliable — see below): N=169 random symmetric `H`, `t_max=15.0`,
  `n_steps=500` — new (cached eigh) **0.437s**, old (redundant-eigh
  reference, re-derived independently in `test_propagators.py`, not the
  fixed function calling itself) **2.737s** — **6.3x speedup**, output
  `np.allclose` exact (`atol=1e-9`). This is the real, load-bearing
  measurement for this task's own Planned Validation.
- **Real-target re-timing caveat, reported honestly rather than
  cherry-picked**: re-running `test_ceiling.py`'s real-target test
  (60 trials, the original hang-diagnosis case) measured 174.07s post-fix
  vs. the 109.31s pre-fix baseline — *slower*, not faster, on a naive
  before/after wall-clock comparison. Investigated rather than accepted
  at face value: `ps aux` at the time showed **6 other concurrent Claude
  Code sessions** running in this same sandbox (unrelated to this task),
  and `user` CPU-time was also higher on the "slower" run — consistent
  with external contention on a heavily shared multi-tenant environment,
  not a regression. The controlled, same-process, same-moment benchmark
  above is the trustworthy number; wall-clock timing of a real-network
  test in this environment is not reproducible enough to serve as the
  actual measurement, and is not used as one here.
- Tests: `test_propagators.py` (7 cases, new file — none existed for
  `propagators.py` before) — output matches an independently-re-derived
  redundant-eigh reference (scalar and multi-index source, both
  synthetic and a real `H2_combinatorial_laplacian`); output is a valid
  probability vector; the controlled timing assertion (>=3x faster,
  generous tolerance, not a flaky micro-benchmark) passes; `ctqw`'s own
  single-call behavior is unchanged and still correctly recomputes
  `eigh` per call for a genuinely different `H` (proves the helper
  wasn't accidentally wired to cache across distinct Hamiltonians).
- Validation: `.venv/bin/python3 -m pytest -q __WORK_IN_PROGRESS__/tests/
  test_propagators.py` — 7 passed. Full `pytest_local.py wip-all` —
  confirmed clean of regressions from this change specifically (7
  unrelated failures in `test_run_challenge.py` were isolated via a
  scoped `git stash` of `scripts/run_challenge.py` and confirmed to be
  caused by another thread's own in-progress, uncommitted edit to that
  file — not this task's change; all 10 of those tests pass against the
  unmodified `run_challenge.py`).
- Out Of Scope confirmed not touched: `select.py::ballistic_exponent`
  (same pattern, different module) — left as this task's own Open
  Question, not bundled in.
