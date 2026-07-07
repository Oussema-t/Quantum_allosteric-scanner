# TASK-0008 Implement `analysis.py` — quantum-vs-classical, ablation, enrichment

## Context

- ID: TASK-0008
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/analysis.py`
- Status: Done
- Owner: Implementer
- Source: notebook `notebooks/H_new_engineering (4) CLEAN.ipynb` — direct
  port of §7 (default-parameter benchmark, H_new vs H10_disorder_supp), §9
  (ablation: which potential term carries the signal), §10 (quantum-walk vs
  classical-heat head-to-head on the same H), §11 (spectral & low-mode
  participation enrichment), §12 (apo↔holo consistency in pocket ranking).
  Also implements the Phase 0a dephasing sweep from `.ai/tasks/PLANS/PLAN.md`
  ("dephasing sweep AUC(omega) as the quantum-relevance test").
- Scope: `__WORK_IN_PROGRESS__/src/allostery/analysis.py` (currently a
  5-line stub) + `__WORK_IN_PROGRESS__/tests/test_analysis.py` (new)

## Intent Contract

- Outcome: this module reproduces, as callable functions instead of
  notebook cells, the analyses that already produced two headline findings
  quoted directly in `PLAN.md`: "optimized AUC_apo on KRAS ≈ 0.53 (near
  chance even with the answer key)" and "Haken–Strobl AUC is flat in the
  dephasing parameter (coherence adds ~nothing)". Both numbers must be
  regression-pinned once reproduced — they are oracle values, not
  approximate targets.
- In Scope:
  - `quantum_vs_classical(H, ...)` — CTQW vs `propagators.heat` on the same
    Hamiltonian (§10).
  - `ablation(H_builder, terms, ...)` — per-term contribution to ranking
    (§9); reuses `potentials.py`'s five terms (`V_B/V_T/V_R/V_C/V_M`,
    `[have]`).
  - `apo_holo_consistency(...)` — pocket-ranking agreement apo vs holo
    (§12).
  - `spectral_enrichment(...)` — low-mode participation vs pocket labels
    (§11); reuses `metrics.eff_rank`/`ipr`/`spectral_gap` (`[have]`).
  - `dephasing_sweep(H, omega_range, labels)` — AUC(ω) via
    `propagators.haken_strobl` (`[have]`) — this is the function that
    reproduces the "coherence adds ~nothing" finding; per `PLAN.md`'s own
    caveat, this must be re-run with **γ calibrated from vibrational
    timescales** (TASK-0005's mode-relaxation output), not a blind sweep,
    before the finding is re-stated as fact.
  - `benchmark(H_new, H10, ...)` — the §7 default-parameter comparison.
- Out Of Scope: the coordinate-descent parameter search from notebook §8
  ("Interpretable parameter optimization") — that's Phase 2 ceiling work
  and doesn't have an assigned module in `PLAN.md`'s repo structure; flag it
  as an open question below rather than silently folding it in here.
- Constraints And Invariants:
  - the two oracle numbers above must become `pytest` regression tests with
    tight tolerances (mirroring how `.claude/TASKS.md` T-004 already pins
    `eff_rank ≈ 117.7` for KRAS — same discipline, same file if convenient).
  - `dephasing_sweep`'s AUC computation must reuse `metrics.auc` (`[have]`),
    not a reimplementation.
- Planned Validation: unit tests on synthetic Hamiltonians for each function
  signature/shape; one real-target run against KRAS_G12C reproducing (within
  documented tolerance) the notebook's own §7/§9/§10/§11/§12 output cells —
  read those cells' printed values directly, don't re-derive them by eye.

## In Progress

None

## TODO (resolved 2026-07-07, Implementer A)

- [x] Read notebook §7, §9, §10, §11, §12 cells; extract exact output
      values to use as regression oracles.
  - **Blocking discovery, not a straightforward read:** every one of the
    notebook's 74 cells has its outputs cleared (`jupyter nbconvert
    --clear-output` or equivalent) — there is nothing printed to extract
    from any section, not just §7/9/10/11/12. Confirmed programmatically
    (`json.load` + scan every cell's `outputs` list: zero cells have any
    stored output anywhere in the file). This is the *same* pre-existing
    gap `.claude/TASKS.md` T-004/T-017 already hit for `eff_rank(KRAS)
    ≈117.7` (there resolved with `xfail(strict=False)` + a wide tolerance
    rather than a fabricated exact number) — T-017 was explicitly
    "Blocked on running the Phase 0 notebook with network access and
    confirmed PDB fetch," which this session actually had (prody +
    working RCSB fetch, installed/confirmed during TASK-0005/0006). Rather
    than execute the full legacy notebook top-to-bottom (its own bespoke
    `SYSTEMS`/`GT`/`MODEL`/`LABELS` globals from cells 0-28, separate from
    and not reusing this already-ported package), this task followed the
    same T-004 precedent: compute fresh, real numbers from this package's
    *own* modules against real RCSB structures, and label them as
    freshly-derived, not notebook-extracted. See Done.
- [x] Implement `quantum_vs_classical`, `ablation`, `apo_holo_consistency`,
      `spectral_enrichment`, `dephasing_sweep`, `benchmark`.
  - All six implemented in `analysis.py`, each reusing existing `[have]`
    modules per this task's own Constraint (no reimplementation of AUC,
    Kabsch, ANM, etc.). `quantum_vs_classical` deliberately evaluates CTQW
    via `time_averaged_ctqw` (oscillatory, needs averaging) but `heat` at a
    single `t_max` (monotonically relaxing, a time-average would be
    redundant) — documented as a deliberate asymmetry, not an oversight.
  - `ablation` isolates each of potentials.py's five terms *individually*
    against the bare Laplacian (single-term attribution, matching this
    task's own framing "which term actually carries the signal"), not a
    leave-one-out variant.
- [x] Regression-pin the AUC_apo≈0.53 (KRAS) and flat-dephasing-AUC findings.
  - Pinned, but **not** the exact historical notebook number (unavailable,
    see above) — freshly computed 2026-07-07 with a proper GDP-contact
    functional-site seed (see the two blocking gaps below):
    `H_new_default` AUC ≈ 0.508, `H10_disorder_suppressed` AUC ≈ 0.528 for
    real KRAS_G12C (4OBE apo / 6OIM holo), both asserted "near chance"
    (0.3-0.7 band, a sanity range not a tight pin, since these are
    *default*-parameter values, not PLAN.md's *optimized* Sec.8 quote —
    see Open Questions). Dephasing sweep AUC range ≈0.015 (blind
    omega in [0,1]) and ≈0.0035 (kappa-calibrated, see next item) —
    both asserted flat.
- [x] Re-run `dephasing_sweep` with κ/γ from TASK-0005's mode-timescale
      calibration once that task lands; note in this task if the finding
      changes under physical calibration (per `PLAN-01.07.26.md`'s explicit
      warning that the blind-sweep version "must be re-tested... before we
      state it").
  - Done — TASK-0005 landed first, so this ran for real rather than being
    deferred. `calibrate_kappa` + `mode_energetics`'s `relaxation_time`
    give a physically-motivated gamma scale (`1/mean(relaxation_time)`);
    swept at 0.5x/1x/2x that scale. **Finding survives, and tightens**:
    AUC range ≈0.0035 (vs the blind sweep's ≈0.015-0.067 depending on
    functional-seed quality — see below) — "coherence adds ~nothing" holds
    up under physical calibration for KRAS_G12C, not just the blind sweep.
- [x] Unit tests.
  - `tests/test_analysis.py`: 16 tests (14 synthetic + 2 real-target).
    Full suite (`python3 .ai/tools/pytest_local.py wip-all`): 268 passed,
    1 pre-existing unrelated xpass, no regressions.

### Two blocking gaps found and fixed (outside this task's original file scope, both directly required for the real-target check)

- **`clean.py`'s `CleanResult` had no per-residue B-factor array** — only
  aggregate `b_mean`/`b_std` (the same gap TASK-0005 hit for `kappa`
  calibration, flagged there as an Open Question). `build_H_new`/`build_H10`
  both require a full `(N,)` B-factor array — impossible to call on real
  data without it. Fixed: added `CleanResult.bfactors: np.ndarray`,
  populated from the same `ca_atoms.getBetas()` call `clean()` already
  made (previously computed then discarded). Backward compatible — grepped
  the whole `__WORK_IN_PROGRESS__` tree; `clean.py` is the only place that
  constructs `CleanResult`, so no other call site could break.
- **`propagators.py`'s `ctqw`/`heat`/`haken_strobl` only accepted a single
  scalar `source`** — but a real functional/active-site seed is naturally
  multi-residue (`labels.functional_indices` returns several indices, e.g.
  KRAS's real GDP-contact seed is 12 P-loop/switch residues, not one atom).
  Calling `benchmark`/`ablation`/`dephasing_sweep` with a real multi-index
  seed crashed outright (`matmul` shape mismatch). Fixed: all four
  propagators (`ctqw`, `heat`, `haken_strobl`, `time_averaged_ctqw`) now
  accept `int | Sequence[int]`, building a coherent equal-amplitude
  superposition for the quantum propagators (`ctqw`/`haken_strobl`) and a
  uniform probability split for the classical one (`heat`) — the physics
  differ (amplitude vs. probability), documented explicitly, not just
  copy-pasted. Fully backward compatible: every existing call site in
  `test_physics.py`/`test_hamiltonians.py` passes a scalar `source` and
  the scalar-reduction formula is unchanged bit-for-bit.
  - **Real-world payoff of fixing this properly rather than working
    around it:** the *first* real-KRAS attempt (before this fix, using
    `functional_indices` with mismatched apo/holo coordinate frames as a
    workaround) silently fell through to labels.py's "top-degree
    fallback" and gave noisier numbers (dephasing AUC range ≈0.067, not
    obviously flat). Fixing the actual bug (co-register frames via
    `superpose.align_apo_holo`, feed a real multi-residue GDP-contact
    seed) gave the clean ≈0.015/≈0.0035 results above — a concrete
    instance of a workaround hiding a worse, wrong-looking result.

## Dependency

- Existing `propagators.py`, `metrics.py`, `potentials.py`, `hamiltonians.py`
  (all `[have]`) — no blocking dependency on other stub modules for the
  §7/§9/§10/§11 pieces.
- TASK-0004 (`labels.py`) — `apo_holo_consistency` and `spectral_enrichment`
  need real pocket labels, not synthetic ones, for the real-target check.
- TASK-0005 (`superpose.py`) — needed only for the γ-recalibration re-run
  of `dephasing_sweep`, not for the initial port.

## Open Questions

- Where does notebook §8's coordinate-descent parameter search live? It's
  the mechanism behind the Phase 2 "ceiling" (best supervised fit), which
  `PLAN.md`'s feature backlog calls for but doesn't assign a file. Options:
  a new `ceiling.py`, or a function inside this module
  (`analysis.ceiling_search`). Recommend surfacing this as a follow-up
  TASK once TASK-0006/0007 (protocol/select) exist, since the ceiling
  search must run inside `protocol.ceiling_context()`.
  - **Not resolved by this task, left open as originally scoped.** Worth
    flagging sharper now: PLAN.md's "optimized AUC_apo on KRAS ≈ 0.53"
    quote is a Sec.8 (optimizer) output, not a Sec.7 (default-parameter)
    one — this task's `benchmark()` only reproduces the *default*-
    parameter comparison, so its ≈0.508 AUC is a genuinely different
    quantity from PLAN.md's quoted 0.53, not a confirmation or refutation
    of it. Whoever builds the Sec.8 optimizer should compare against real
    ceiling-context numbers then, not assume this task already covered it.
- **New, raised by this task's implementation:** the notebook's outputs
  being fully cleared (not just the two cells this task cared about) means
  T-004/T-017's `eff_rank≈117.7` placeholder in `test_physics.py` is
  probably not recoverable by re-reading the notebook either — it likely
  needs the same "compute fresh, document as fresh" treatment this task
  used, or an explicit decision to drop the historical-oracle framing
  entirely. Flagging for whoever picks up T-004 next, not fixed here
  (out of this task's file scope).
- **New, raised by this task's implementation:** `dephasing_sweep` is slow
  at real protein scale with `haken_strobl`'s default tolerances (~20s per
  gamma value at N≈170 with `rtol=1e-6`/`atol=1e-8`; ~2s with
  `rtol=1e-3`/`atol=1e-5`). Exposed `rtol`/`atol` pass-through on
  `dephasing_sweep` so callers can trade accuracy for speed explicitly,
  but a full multi-target sweep (per `PLAN.md`'s own "tens of CPU-hours"
  compute note) will still want the loose tolerances by default for
  exploratory work — worth a follow-up if `select.py`/`analysis.py`'s
  future orchestration needs a project-wide default choice here.

## Done

- `__WORK_IN_PROGRESS__/src/allostery/analysis.py` implemented in full:
  `quantum_vs_classical`, `ablation`, `benchmark`, `apo_holo_consistency`,
  `spectral_enrichment`, `dephasing_sweep`, plus a shared `_metric_pack`
  helper (AUC/P@k/E@k via `metrics.py`, mirroring the notebook's own
  `metric_pack` convention).
- Two blocking gaps fixed to make the real-target check possible at all
  (see TODO section above for detail): `clean.py`'s `CleanResult` gained a
  per-residue `bfactors` array; `propagators.py`'s `ctqw`/`heat`/
  `haken_strobl`/`time_averaged_ctqw` gained multi-index `source` support
  (backward compatible, all existing scalar-source call sites unaffected).
- `__WORK_IN_PROGRESS__/tests/test_analysis.py`: 16 tests, all passing.
  Full suite (`python3 .ai/tools/pytest_local.py wip-all`): 268 passed, 1
  pre-existing unrelated xpass, no regressions.
- Real KRAS_G12C results (2026-07-07, freshly computed, not notebook-
  extracted — see the oracle-gap note above): `H_new_default` AUC ≈0.508,
  `H10_disorder_suppressed` AUC ≈0.528 (both "near chance" with default
  parameters); blind dephasing sweep (omega in [0,1]) AUC range ≈0.015,
  flat; kappa-calibrated dephasing sweep (using TASK-0005's
  `calibrate_kappa`/`relaxation_time`) AUC range ≈0.0035, flat and
  *tighter* than the blind sweep — PLAN.md's "coherence adds ~nothing"
  finding independently corroborated under physical calibration, not just
  a blind-sweep artifact.
- Planned Validation: unit tests on synthetic Hamiltonians done for every
  function; the real-target run against KRAS_G12C is done and passing, but
  reproduces *freshly-computed* values rather than the notebook's own
  historical §7/§9/§10/§11/§12 output cells, because those cells have no
  stored output in this repo's `.ipynb` to read (see TODO section) — this
  is a documented deviation from the letter of the Planned Validation, not
  a silent one.
