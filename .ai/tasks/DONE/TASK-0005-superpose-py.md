# TASK-0005 Implement `superpose.py` — apo/holo alignment, cryptic-openness gate, and ANM mode-projection (Phase 1b)

**Naming note (2026-07-05):** the task title previously read "Kabsch
superposition + cryptic-openness gate," which undersold the module's
second half (mode-projection/κ-calibration/relaxation-timescale, Phase 1b)
— retitled here to cover both. The *file* stays `superpose.py` per
`PLAN.md`'s repo-structure table (not renamed unilaterally — see Open
Questions for why and what would be involved in changing it).

## Context

- ID: TASK-0005
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/superpose.py`
- Status: Done
- Owner: Implementer
- Source: **no notebook precedent — this is a net-new build.**
  `ALGORITHM_REGISTER.md` §A (Two-state ANM — rating 5, NMFF — rating 5,
  Tama–Sanejouand cumulative overlap — rating 5); `.ai/tasks/PLANS/PLAN.md`
  Phase 1 + Phase 1b; `HOLO_DIRECTION_MODULE.md` Step 1-2 reuses this
  module's mode machinery.
- Scope: `__WORK_IN_PROGRESS__/src/allostery/superpose.py` (currently a
  5-line stub) + `__WORK_IN_PROGRESS__/tests/test_superpose.py` (new)

## Intent Contract

- Outcome: the single most important physical gate in the whole pipeline —
  "is the apo→holo pocket-opening direction even present in the apo
  structure's low-frequency modes." Everything downstream (ceiling, LOPO,
  holo-direction module) is conditioned on this module's per-target verdict.
- In Scope:
  - Kabsch/SVD superposition of holo onto apo on the common Cα set; report
    per-chain RMSD (catches register/numbering errors independently of the
    sequence-alignment label mapping in `labels.py`, TASK-0004).
  - 3D-position pocket cross-map: does the holo pocket (from `labels.py`)
    land on the same residues when mapped by 3D coincidence instead of
    sequence alignment? Disagreement = a label bug caught geometrically,
    not a modeling failure.
  - cryptic-openness gate: per-residue apo→holo RMSD at the pocket. Large
    rearrangement (KRAS SII-P is the textbook case per
    `ALGORITHM_REGISTER.md`) ⇒ report "pocket absent from apo topology" as a
    finding, don't drop the target silently.
  - mode-projection (Phase 1b): apo ANM modes, cumulative overlap
    `CO(m) = ||proj_{k≤m} Δr|| / ||Δr||` (Tama–Sanejouand 2001) — the
    number `HOLO_DIRECTION_MODULE.md` Step 2 reuses directly as its go/no-go
    threshold.
  - spring-constant κ calibration against crystallographic B-factors; per-mode
    elastic energy; overdamped relaxation timescale
    `τ_k ~ ζ/(κ λ_k)` to calibrate the CTQW propagation time `t` downstream
    (consumed by `analysis.py`, TASK-0008).
- Out Of Scope: the perturbation/deformation search itself (that's the
  holo-direction module, TASK-0015 — this module only produces the gate
  verdict and the mode basis it needs).
- Constraints And Invariants:
  - this module is allowed to see holo (it's characterizing known
    apo→holo pairs) — this is legal per `HOLO_DIRECTION_MODULE.md`'s
    leakage firewall ("using holo to characterize the method... is legal;
    using holo to parameterize the predictor is not"). Nothing computed
    here may leak into a per-target scoring knob later — cite this
    boundary in the docstring the same way TASK-0004 does.
  - report the **relaxation time**, not the underdamped period, per
    `.ai/tasks/PLANS/PLAN.md`'s explicit correction ("underdamped period is
    a lower bound only").
  - **do not reimplement Kabsch/SVD from scratch (2026-07-05 finding):**
    the identical algorithm already exists, live, three times over in
    `backend/` — `backend/analysis.py::_kabsch_rotate` (plain NumPy,
    coordinate arrays, closest match to this package's own
    dependency-light convention), `backend/discovery.py::_kabsch` (same
    math, different call signature, used by `complete_apo`), and
    `backend/compare.py::align_and_compare` (Biopython `Superimposer`,
    whole-structure atom transforms, powers the live `GET /api/compare`
    endpoint — confirmed core/stated in `.ai/reviews/PRODUCT_INTENT_MAP.md`
    row 26). Port the math from `analysis.py::_kabsch_rotate`'s form
    (mobile/ref (N,3) arrays in, aligned array out) rather than deriving it
    independently — same formula, same reflection-correction
    (`det(Vt.T@U.T)` sign flip), no reason for a fourth copy to diverge.
    **Port, don't import across packages:** `allostery/` should not import
    from `backend/` (a live FastAPI service) or vice versa — copy the
    function with a comment citing its origin, the same way this repo
    already ports notebook math with a section citation. See TASK-0030,
    which deduplicates `backend/`'s own two internal NumPy copies into one
    shared, unit-tested helper — read that task's landed helper first once
    it exists; it may be the cleanest single thing to port from.
- Planned Validation: unit test the Kabsch fit against a known synthetic
  rotation+translation (should recover it to floating-point precision);
  unit test `CO(m)` on a toy system where Δr is constructed to lie exactly
  in the first 2 modes (should read CO(2) ≈ 1.0); one real-target check on
  KRAS_G12C expecting a **low** overlap (SII-P is the literature cryptic
  case — a low CO(m) here is the expected/correct result, not a test
  failure).

## In Progress

None

## TODO (resolved 2026-07-06, Implementer A)

- [x] Kabsch/SVD superposition + per-chain RMSD — **port from
      `backend/analysis.py::_kabsch_rotate` (or TASK-0030's deduplicated
      helper, if it lands first), do not rewrite from scratch.**
  - Ported `kabsch_fit`/`kabsch_apply`/`kabsch_align` verbatim from
    TASK-0030's landed `backend/geometry.py` (origin cited in the module
    docstring). `align_apo_holo()` builds the common (chain, resnum) set
    via `common_residues_by_resnum()` — deliberately resnum-based, **not**
    sequence alignment, so it's an independent check against `labels.py`'s
    method (see Intent Contract) — fits Kabsch on that subset, applies the
    transform to all of holo, and reports overall + per-chain RMSD.
- [x] 3D pocket cross-map vs `labels.py`'s sequence-alignment map;
      disagreement handling (log + flag, don't silently pick one).
  - `geometric_pocket_mask()` transforms the holo ligand's own coordinates
    into apo's frame via the Kabsch fit, then flags apo Cα atoms within
    cutoff by pure 3D distance — no sequence alignment anywhere in that
    function. `pocket_cross_map(seq_mask, geo_mask)` reports a Jaccard
    agreement score plus the exact `only_in_sequence`/`only_in_geometric`
    residue indices; disagreement is returned as data, never resolved by
    picking a side.
- [x] Cryptic-openness gate (per-residue apo→holo RMSD at pocket residues).
  - `cryptic_openness_gate()` — restricted to pocket residues with a common
    (chain, resnum) correspondence; residues in the mask with no
    correspondence are counted (`n_unmeasurable`) rather than silently
    dropped or zeroed. Returns **both** the continuous score
    (`pocket_rmsd_mean`/`_max`) and the hard boolean verdict
    (`pocket_open_in_apo`), per this task's own Open Question below.
- [x] ANM mode computation (reuse `hamiltonians.H13_3N_anm_hessian`? — audit
      whether that existing function is a legitimate base rather than
      reimplementing ANM from scratch).
  - Confirmed legitimate (see Open Questions below) and reused as-is.
    `anm_modes()` eigendecomposes it and discards the rigid-body nullspace
    — **hardened to require exactly 6 near-zero modes**, not "≥6": a bug
    was caught in this task's own test suite where a disconnected two-
    cluster synthetic graph (12 real zero modes) silently passed an
    `n_zero < 6` check instead of raising. Fixed to `n_zero != 6`.
- [x] Cumulative overlap `CO(m)`.
  - `cumulative_overlap()` (Tama–Sanejouand 2001), built on a shared
    `_projection_coefficients()` helper (also used by `mode_energetics`).
    Handles the apo/holo numbering-gap case by slicing + renormalizing each
    eigenvector to the common residue subset before projecting (documented
    as the standard practical approximation ProDy's `calcOverlap` also
    uses).
- [x] κ calibration against B-factors (`clean.py`'s `CleanResult.b_mean`/
      `b_std` already surfaces the inputs this needs).
  - `calibrate_kappa()` — a single global scalar (`mean(unit-κ ANM MSF) /
    b_mean`), **not** a per-residue regression, because `CleanResult` only
    exposes aggregate `b_mean`/`b_std`, not a per-residue B-factor array.
    Documented explicitly as unitless/relative (no kT/8π²/3 physical
    prefactor) rather than silently implying an absolute physical
    calibration. See Open Questions below for the follow-up this surfaces.
- [x] Elastic energy per mode + overdamped relaxation timescale.
  - `mode_energetics()`: `E_k = ½ κ λ_k c_k²`, `τ_k = ζ/(κ λ_k)` — the
    **relaxation time**, not the underdamped oscillation period, per
    `PLAN.md`'s explicit correction. `ζ` defaults to an arbitrary
    friction-coefficient unit (documented as relative-only, no absolute
    time calibration exists in this package).
- [x] Unit tests (synthetic rotation, synthetic mode-confined Δr).
  - `tests/test_superpose.py`: 32 tests (31 synthetic + 1 real-target),
    all passing via `python3 .ai/tools/pytest_local.py wip-all` (211
    passed total across the whole `__WORK_IN_PROGRESS__/tests/` suite, no
    regressions). Covers: Kabsch recovery to floating-point precision +
    the reflection/det-sign-flip branch; common-residue correspondence;
    full alignment (identical structures, known rigid transform, too-few-
    points error, per-chain RMSD); pocket cross-map agreement and
    disagreement; the openness gate's small/large-displacement/
    unmeasurable/no-measurable-residues branches; ANM mode shape/ordering/
    the disconnected-graph regression above; `CO(m)` confined-to-first-
    two-modes (the Planned Validation's core numeric requirement, CO(2) ≈
    1.0 to 1e-8), monotonicity, zero-Δr, and wrong-length-input error
    handling; κ's positivity and inverse-proportionality to `b_mean`; mode
    energetics' exact formula match; and an end-to-end `run_superpose()`
    smoke test (with and without a configured drug ligand).
- [x] KRAS_G12C real-target check; document the expected-low-CO result.
  - `prody` turned out to already be installed in the scaffold venv this
    session (by the concurrent TASK-0004 thread) and RCSB network fetch
    worked from this sandbox, so the real check ran for real rather than
    skipping: apo `4OBE` vs. holo `6OIM`, chain A, 20 ANM modes —
    **CO(20) ≈ 0.699** (full curve 0.424 → 0.699 across modes 1–20),
    comfortably confirming the literature expectation that KRAS_G12C's
    Switch-II cryptic pocket is *not* well-spanned by the soft apo modes.
    The test still guards with `pytest.importorskip("prody")` +
    a try/except-skip around the fetch, so it degrades gracefully to a
    skip (not a failure) on a machine without `prody`/network access.

## Dependency

- TASK-0003 (`targets.yaml`) for apo/holo ids.
- TASK-0004 (`labels.py`) for the pocket mask this gate is measured against.
- `hamiltonians.H13_3N_anm_hessian` (`[have]`) — check whether it's directly
  reusable for the ANM mode step before writing a parallel implementation.
- TASK-0030 (new, `backend/` Kabsch dedup) — soft dependency, not
  blocking: read its landed helper first if it's already done, since it's
  the cleanest single porting target; if TASK-0030 hasn't landed yet, port
  from `backend/analysis.py::_kabsch_rotate` directly instead of waiting.

## Open Questions

- Is `H13_3N_anm_hessian` in `hamiltonians.py` already the right ANM
  Hessian for this module's mode computation, or was it built for a
  different purpose (physics unit-test coverage per `.claude/TASKS.md`
  T-011 mentions it's 3N×3N with nullity ≥ 3 checked — that's consistent
  with an ANM Hessian, worth confirming before reimplementing)?
  - **Resolved:** yes, confirmed legitimate. Verified empirically this
    session on the synthetic helix fixture: exactly 6 near-zero eigenvalues
    (3 translation + 3 rotation), matching the theoretical ANM nullspace.
    Reused directly in `anm_modes()`/`calibrate_kappa()`.
- Should the cryptic-openness verdict be a hard boolean gate or a continuous
  score that `protocol.py` (TASK-0006) thresholds? `PLAN.md` phrases it as
  "yes/no" but a continuous `CO(m)` is more informative for the competence
  map — recommend storing both.
  - **Resolved in favor of "both":** `cryptic_openness_gate()` returns
    `pocket_open_in_apo` (bool) alongside `pocket_rmsd_mean`/`_max`
    (continuous); `run_superpose()`'s `cumulative_overlap` array is the
    continuous CO(m) curve, with no separate hard gate imposed on it here —
    `protocol.py` (TASK-0006) is left to pick its own threshold(s) against
    either signal.
- **Should this module eventually split in two** (e.g. `superpose.py` for
  Kabsch/RMSD/cryptic-openness-gate, a separate `modes.py` or `elastic.py`
  for ANM mode-projection/κ-calibration/relaxation-timescale), matching
  the one-concern-per-file convention every other landed file in this
  package already follows (`hamiltonians.py`, `potentials.py`,
  `propagators.py`, `metrics.py`)? `PLAN.md`'s repo-structure table bundles
  both into one `superpose.py` entry, which is why the file isn't renamed
  here unilaterally — but the two halves are conceptually distinct enough
  that a split is a reasonable question, not a hygiene overreach. Recommend
  deciding this as part of TASK-0002-style scaffold hygiene (a `PLAN.md`
  repo-structure edit, not a decision this task should make alone by
  writing the file one way and hoping it sticks) — flag there before
  implementation starts, since splitting after the fact means redoing the
  module boundary and every doc that names `superpose.py` (this task,
  TASK-0006, TASK-0015/`HOLO_DIRECTION_MODULE.md`).
  - **Not resolved by this task, left open as originally scoped** — still
    one `superpose.py` file (now ~370 lines across both halves), per
    `PLAN.md`'s repo-structure table. Flag for a future scaffold-hygiene
    pass, not decided unilaterally here.
- **New, raised by this task's implementation:** `calibrate_kappa()` can
  only do a single global mean-matching calibration (`mean(unit-κ ANM MSF)
  / b_mean`), not a proper per-residue regression against real B-factors,
  because `clean.py`'s `CleanResult` only exposes aggregate `b_mean`/
  `b_std`, not a per-residue B-factor array. A future task could extend
  `CleanResult` with a `bfactors: np.ndarray` field (the raw per-residue
  values are already computed inside `clean()`, just not retained) — out
  of this task's declared scope (`superpose.py` + its test file only), so
  not done here, but worth filing if a real per-residue κ fit is ever
  needed.
- **New, raised by this task's implementation:** `anm_modes()`/
  `calibrate_kappa()` now `raise ValueError` on anything other than
  *exactly* 6 near-zero modes (tightened from the original "≥6" TODO
  wording during test-writing — a disconnected synthetic graph silently
  passed the looser `<6` check). This is correct for the single-chain
  targets this task validated against (KRAS_G12C), but a genuinely
  multi-chain/floppy-linker target (e.g. MYC_MAX's cMyc+Max+DNA assembly)
  might legitimately have more than 6 near-zero-but-not-exactly-zero modes
  without being "disconnected" in the error sense — worth revisiting this
  strictness once a multi-chain target is actually run through this
  module.

## Done

- `__WORK_IN_PROGRESS__/src/allostery/superpose.py` implemented in full:
  Kabsch alignment (ported from `backend/geometry.py`, TASK-0030),
  resnum-based common-residue correspondence, the 3D geometric pocket
  cross-map against `labels.py`'s sequence-alignment mask, the cryptic-
  openness gate (continuous + boolean), ANM mode computation on
  `hamiltonians.H13_3N_anm_hessian`, Tama–Sanejouand cumulative overlap,
  global κ calibration, per-mode elastic energy + relaxation timescale,
  and a `run_superpose()` one-call orchestrator for `protocol.py`
  (TASK-0006) to consume.
- `__WORK_IN_PROGRESS__/tests/test_superpose.py`: 32 tests, all passing
  (211 passed across the whole suite via
  `python3 .ai/tools/pytest_local.py wip-all`, no regressions). Includes a
  real bug caught and fixed during test-writing (the `n_zero < 6` →
  `!= 6` disconnected-graph fix above) and a real, non-skipped KRAS_G12C
  check: **CO(20) ≈ 0.699**, confirming the expected-low-overlap literature
  result for the Switch-II cryptic pocket.
- All three Planned Validation items met: Kabsch recovers a synthetic
  rotation+translation to floating-point precision; `CO(2) ≈ 1.0` (to
  1e-8) for Δr confined to the first two modes; KRAS_G12C's real CO(20) is
  low, as expected/correct, not a test failure.
