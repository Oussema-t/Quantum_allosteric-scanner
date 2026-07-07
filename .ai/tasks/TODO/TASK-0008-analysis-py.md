# TASK-0008 Implement `analysis.py` — quantum-vs-classical, ablation, enrichment

## Context

- ID: TASK-0008
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/analysis.py`
- Status: TODO
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

## TODO

- [ ] Read notebook §7, §9, §10, §11, §12 cells; extract exact output
      values to use as regression oracles.
- [ ] Implement `quantum_vs_classical`, `ablation`, `apo_holo_consistency`,
      `spectral_enrichment`, `dephasing_sweep`, `benchmark`.
- [ ] Regression-pin the AUC_apo≈0.53 (KRAS) and flat-dephasing-AUC findings.
- [ ] Re-run `dephasing_sweep` with κ/γ from TASK-0005's mode-timescale
      calibration once that task lands; note in this task if the finding
      changes under physical calibration (per `PLAN-01.07.26.md`'s explicit
      warning that the blind-sweep version "must be re-tested... before we
      state it").
- [ ] Unit tests.

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

## Done

(not yet)
