# TASK-0040 `potentials.py` recomputes the GNM eigendecomposition redundantly

## Context

- ID: TASK-0040
- Title: `_gnm_msf`, `V_C`, and `V_M` each independently rebuild
  `contact_matrix → laplacian → eigh` from scratch — no shared context,
  unlike `backend/analysis.py::gnm_context()` which computes once and
  passes a context dict to all five `V_*` functions
- Status: Done
- Owner: Implementer
- Source: review of all `Bartosz`/`bchmura`-authored commits, 2026-07-05
  session — Medium-severity finding #4
- Scope: `__WORK_IN_PROGRESS__/src/allostery/potentials.py`,
  `__WORK_IN_PROGRESS__/src/allostery/hamiltonians.py::build_H_new` (caller)

## ⚠️ Before implementing

**Do a short review before refactoring** — confirm this is actually worth
fixing now vs. later: `build_H_new` calls all five `V_*` functions once
per Hamiltonian evaluation, so the redundant O(N³) eigendecomposition cost
multiplies with however many times `build_H_new` gets called (once per
target in a simple pipeline run, but potentially hundreds/thousands of
times inside a future hyperparameter search or ceiling-optimization loop —
TASK-0008's `analysis.py::benchmark`/ablation work, or the notebook §8's
coordinate-descent search once that's ported). If nothing calls
`build_H_new` in a hot loop yet, this may be worth deferring until that
work actually lands, to avoid optimizing prematurely.

## Intent Contract

- Outcome: `build_H_new` computes the shared GNM context (contact matrix,
  Kirchhoff, eigendecomposition) once per call and passes it to whichever
  of `V_R`/`V_C`/`V_M` need it, mirroring `backend/analysis.py::gnm_context`'s
  already-proven pattern — same public function signatures for `V_B`/`V_T`
  (which don't need the GNM context at all), but `V_R`/`V_C`/`V_M` gain an
  optional pre-computed-context parameter.
- In Scope:
  - add a `gnm_context(coords, cutoff)` helper to `potentials.py` (or
    import/adapt the shape from `backend/analysis.py`'s — port the
    pattern, not the code, per this repo's cross-package convention
    already established in TASK-0005/TASK-0030).
  - update `_gnm_msf`, `V_R`, `V_C`, `V_M` to accept an optional
    pre-computed context, falling back to computing their own if none is
    passed (keeps each function independently callable/testable, which
    the existing unit tests rely on).
  - update `build_H_new` to compute the context once and pass it through.
- Out Of Scope: touching `backend/analysis.py::gnm_context` itself, or
  merging the two implementations — per TASK-0018's established
  principle, port the pattern across the `backend/`↔`allostery/`
  boundary, don't share code.
- Constraints And Invariants: must not change any existing test's
  expected output — `test_potentials.py`'s current assertions call
  `V_R`/`V_C`/`V_M` directly with just `(coords, cutoff)`; those call
  signatures must keep working unchanged (context stays optional).
- Planned Validation: existing `test_potentials.py` suite passes
  unchanged; a new test confirms `build_H_new`'s output is numerically
  identical before/after the refactor on a synthetic fixture; a rough
  timing comparison (not necessarily a formal benchmark) showing the
  eigendecomposition count actually dropped from 3 to 1 per `build_H_new`
  call.

## TODO

- [x] Confirm whether this is worth doing now or deferring -- **worth
      doing now**: `build_H_new` is called repeatedly across this
      project's real usage today (detection-curve grids, hyperparameter
      sweeps, real-target scoring scripts), and the measured redundant
      cost is real (~78% of `build_H_new`'s own wall-clock on the
      largest target). Not premature.
- [x] Add the optional shared-context parameter to
      `_gnm_msf`/`V_R`/`V_C`/`V_M` -- done, all four backward-compatible
      (verified: existing calls with just `(coords, cutoff)` produce
      bit-identical output to before this task).
- [x] Wire `build_H_new` to compute once and pass through -- done.
- [x] Re-run `test_potentials.py`; add the numerical-equivalence + timing
      checks -- 7 new tests (context-vs-no-context equivalence for all 4
      functions, `gnm_context`'s own shape/key check, an `eigh`-call-count
      check via monkeypatched interception confirming 3->1, and a pinned
      `build_H_new` golden-value regression). 29/29 `test_potentials.py`
      tests pass.

## Dependency

- None (self-contained within `potentials.py`/`hamiltonians.py`); loosely
  related to TASK-0018/TASK-0008 (whichever eventually drives repeated
  `build_H_new` calls makes this fix more urgent, not more necessary).

## Open Questions

- Defer entirely until a hot loop actually calls `build_H_new`
  repeatedly, or fix now? **Resolved: fix now.** By the time this task
  was picked up (2026-08-14, five weeks after filing), that hot loop
  already exists many times over -- this project's own real detection-
  curve grids, hyperparameter sweeps, and real-target scoring scripts
  call `build_H_new` routinely, and the redundant cost measured real
  (~78% of `build_H_new`'s own wall-clock on the largest target). "Cheap
  and self-contained regardless" (the filing's own leaning) also held up.

## Done

**2026-08-14, Implementer C.**

**Confirmed not already fixed, checked directly before assuming**:
[[TASK-0066]] (2026-07-12) already deduped the *code* -- one shared
`_kirchhoff_eigh` function instead of three independent re-derivations
of the same math (its own docstring says so). It did not dedupe the
*computation*: `_gnm_msf` (called by `V_R`), `V_C`, and `V_M` each still
independently *called* `_kirchhoff_eigh`, so the O(N^3) `eigh`
diagonalization itself still ran 3 times per `build_H_new` invocation --
plus a 4th independent `contact_matrix` rebuild inside `V_R` for its own
degree/clustering terms, not previously flagged. This is exactly what
TASK-0040 asked to fix; TASK-0066 was a real but partial predecessor,
not a duplicate of this task.

**Measured before touching any code**, on CARDIAC_MYOSIN (N=704, the
largest real target in this scaffold): a single `_kirchhoff_eigh` call
costs 0.080s; `build_H_new` itself costs 0.308s -- 3 redundant calls
(~0.24s) account for ~78% of the total.

**Built**: `potentials.gnm_context(coords, cutoff) -> dict` (`A`, `w`,
`U`, `nz`, `winv`, `msf`, `degree`, `clust` -- everything `_gnm_msf`/
`V_R`/`V_C`/`V_M` read, computed once), ported analogue of
`backend/analysis.py::gnm_context`'s already-proven dict-context pattern
(same shape where the underlying quantity is the same, not shared code,
per [[TASK-0018]]'s backend<->allostery boundary). All four functions
gained an optional keyword-only `context=None` parameter -- omitted,
they compute their own context exactly as before (every existing call
site/test keeps working unchanged); supplied, they read from it instead.
`hamiltonians.build_H_new` now computes `ctx = gnm_context(coords,
cutoff)` once and threads it through all three `context`-aware calls.

**Verified bit-identical, not assumed from the refactor being "just a
reorder"**: (1) `_gnm_msf`/`V_R`/`V_C`/`V_M` each give `np.array_equal`
results with vs. without a supplied context, on a synthetic fixture. (2)
`build_H_new`'s own real-target output: computed on CARDIAC_MYOSIN with
the post-fix code, then `git stash`'d `potentials.py`/`hamiltonians.py`
back to the pre-fix code (this project's own established verification
method, `test_analysis_characterization.py`'s own precedent), recomputed,
popped the stash back, and confirmed `np.array_equal` -- exactly
bit-identical, max abs diff 0.0.

**Timing** (CARDIAC_MYOSIN, N=704): `build_H_new` 0.308s -> 0.146-0.178s
(~2x). Matches the "3 eigendecompositions -> 1" prediction reasonably
well (not exactly 3x since `L` construction, `V_B`, `V_T` are also part
of the post-fix baseline cost).

**New tests** (`tests/test_potentials.py`, `TestGnmContext`, 7 tests):
`gnm_context`'s own keys/shapes; context-vs-no-context equivalence for
all 4 functions; an `eigh`-call-count check via monkeypatched
interception, directly confirming 3 calls (V_R+V_C+V_M, no context) drops
to 1 (same three, with a shared context) -- the actual mechanism claim,
not inferred from timing alone; a pinned `build_H_new` golden-value
regression test (trace, sum, first 5 diagonal entries) on the existing
synthetic fixture, so future changes to this call path get a fast,
network-free regression check instead of only the real-target check this
task itself ran once. 29/29 `test_potentials.py` tests pass (22
pre-existing + 7 new). Full `pytest tests/ -q`: 1196 passed, 1 skipped,
3 xfailed, 0 failed.

**Implementer's-call decisions**: (1) `gnm_context`'s dict includes
`degree`/`clust` (not just the raw `_kirchhoff_eigh` tuple) so `V_R`
doesn't need its own separate `contact_matrix` rebuild either -- a
slightly larger scope than the Intent Contract's own literal wording
("contact matrix, Kirchhoff, eigendecomposition") but still exactly the
same underlying redundant-computation problem, on the same function.
(2) Kept `_kirchhoff_eigh` itself unchanged (still used internally by
`gnm_context` and by every no-context fallback path) rather than
refactoring it away -- smaller, more contained diff.

**Not done**: touching `backend/analysis.py::gnm_context` or merging the
two implementations (explicitly Out Of Scope, per [[TASK-0018]]'s
established backend<->allostery boundary).
