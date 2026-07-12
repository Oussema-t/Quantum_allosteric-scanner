# TASK-0079 End-to-end challenge run

## Context

- ID: TASK-0079
- Title: One command producing, per mandatory target, the three required
  deliverables: the N×N connectivity matrix, the top-5 ranked hit list,
  and the methodological report.
- Status: TODO
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 5, item 5.1 —
  "This is what the submission is actually judged on... Currently no
  single command produces them. This is the submission artifact." Second
  link in the critical path (`0.1 → 0.2 → 1.1 → 1.2 → 5.1 → 5.2 → 6.1`).

## Intent Contract

- Outcome: a single command (script or CLI entry point) that, given a
  target from `config/targets.yaml`, runs the full frozen pipeline
  end-to-end and emits the three required deliverables for the mandatory
  targets: **KRAS** (4OBE→6OIM), **BCR-ABL1** (1OPL→5MO4), **Myosin**, and
  **c-Myc** (see TASK-0080 for c-Myc's special handling — no holo ground
  truth).
- In Scope: orchestrating the already-Done pipeline stages (`labels`,
  `protocol`, `select`, `analysis`, `diagnostics`, `report`, `baselines`,
  `pathways`, `coarse`, `viz`) into one run per target; producing the N×N
  connectivity matrix, top-5 hit list, and methodological report as
  concrete output files.
- Out Of Scope: the honesty/verdict layer's correctness (Phase 1 items —
  TASK-0058/0055/0064/0071 — must land first per the critical path, since
  this task should not emit dishonest verdicts); the artifact contract
  format itself (TASK-0083, though this task's output should anticipate
  feeding into it).
- Acceptance Scenarios:
  - Given KRAS_G12C (4OBE→6OIM), when the end-to-end command runs, then
    it produces a connectivity matrix file, a top-5 hit list, and a
    methodological report, without manual intervention between stages.
  - Given BCR-ABL1 (1OPL→5MO4) and Myosin, then the same command produces
    the same three deliverables for each.
- Constraints And Invariants: per the critical path, this task depends on
  Phase 0 (TASK-0070/0052/0047/0063) and Phase 1 (TASK-0058/0055/0064)
  landing first — an honest run requires an honest verdict layer.
- Planned Validation: manual inspection of the three deliverables for at
  least KRAS_G12C against the plan's stated requirements; downstream,
  TASK-0082's competence map consumes this task's output.

## Dependency

- Depends on Phase 0 (TASK-0070, TASK-0052, TASK-0047, TASK-0063) and
  Phase 1 (TASK-0058, TASK-0055, TASK-0064, TASK-0071) per the critical
  path — do not start until those are Done.
- Feeds TASK-0082 (competence map synthesis) and TASK-0083 (result
  artifact contract) directly — the critical path continues
  `5.1 → 5.2 → 6.1`.
- Related to TASK-0080 (c-Myc special handling, no holo ground truth) and
  TASK-0081 (generalization set) — same orchestration machinery, applied
  to additional targets.

## Open Questions

- None — targets and deliverables are named explicitly in the plan;
  scope is otherwise determined by whatever Phase 0/1 land with.

**Cross-link added by TASK-0056's review (2026-07-12), additive only —
does not touch this task's claim/TODO:** [[SEAM-0008]] (`report.py`'s
`verdict_template` expects a flat results schema — `AUC_apo_Hnew_default`
etc. — that nothing in `analysis.py` currently produces; only
`test_report.py`'s hand-built fixture has ever exercised it) was reassigned
here, since this task's own "orchestrating the already-Done pipeline
stages... into one run" is the actual assembly step the seam is waiting
on. When wiring `analysis.py`'s output into `report.verdict_template`,
build the mapping from `analysis.py`'s real (nested) return shapes —
`benchmark()` → `{"H_new_default": metric_pack, "H10_disorder_suppressed":
metric_pack}`, `ablation()` → `{"L_only": ..., "B": ..., ...}` per-term
packs, `quantum_vs_classical()`, `apo_holo_consistency()` — not a shape
guessed independently; add the seam-test there once real, and flip
`SEAM-0008` to `VERIFIED`.

## Done

(not yet)
