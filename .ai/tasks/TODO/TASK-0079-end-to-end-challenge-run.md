# TASK-0079 End-to-end challenge run (parent — see subtasks)

## Context

- ID: TASK-0079
- Title: One command producing, per mandatory target, the three required
  deliverables: the N×N connectivity matrix, the top-5 ranked hit list,
  and the methodological report.
- Status: TODO (parent — thin coordinator; Done only once every subtask
  below is Done, per `.ai/tasks/README.md`'s subtask convention)
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 5, item 5.1 —
  "This is what the submission is actually judged on... Currently no
  single command produces them. This is the submission artifact." Second
  link in the critical path (`0.1 → 0.2 → 1.1 → 1.2 → 5.1 → 5.2 → 6.1`).
- Split into subtasks 2026-07-12, per user direction, once Phase 0/1
  dependencies landed and the actual module interfaces were read — the
  single-task version was too large to claim/review/verify as one unit;
  each subtask below is independently claimable and testable.

## Intent Contract (parent-level; each subtask has its own, narrower one)

- Outcome: a single command (script or CLI entry point) that, given a
  target from `config/targets.yaml`, runs the full frozen pipeline
  end-to-end and emits the three required deliverables for the mandatory
  targets: **KRAS_G12C** (4OBE→6OIM), **BCR_ABL1** (1OPL→5MO4), and
  **CARDIAC_MYOSIN** (real `targets.yaml` key — the plan's "Myosin"). See
  [[TASK-0080]] for `MYC_MAX`/c-Myc's special handling (no holo ground
  truth) — deliberately not this task's scope, same orchestration
  machinery reused there.
- In Scope: orchestrating the already-Done pipeline stages (`labels`,
  `protocol`, `select`, `analysis`, `diagnostics`, `report`, `baselines`,
  `pathways`) into one run per target; producing the N×N connectivity
  matrix, top-5 hit list, and methodological report as concrete output
  files. Includes the [[SEAM-0008]] schema-assembly step (reassigned here
  by [[TASK-0056]]'s review — `analysis.py`'s real nested output has no
  translation into `report.verdict_template`'s expected flat dict; that
  translation is part of "orchestrating," not a separate concern). When
  wiring it: build the mapping from `analysis.py`'s real (nested) return
  shapes — `benchmark()` → `{"H_new_default": metric_pack,
  "H10_disorder_suppressed": metric_pack}`, `ablation()` → `{"L_only":
  ..., "B": ..., ...}` per-term packs, `quantum_vs_classical()`,
  `apo_holo_consistency()` — not a shape guessed independently.
- Out Of Scope: the honesty/verdict layer's own correctness (Phase 1 —
  already landed: TASK-0058/0055/0064/0071/0088); the artifact contract
  format itself ([[TASK-0083]], though output here should anticipate
  feeding into it); `coarse.py`/`viz.py` (qubit-cost estimation and
  plotting are not among the three required deliverables — a natural
  follow-up once this lands, not built speculatively here); `MYC_MAX`
  ([[TASK-0080]]) and the generalization set ([[TASK-0081]]).
- Acceptance Scenarios (parent-level; the real assertions live in
  `.005`'s manual inspection):
  - Given KRAS_G12C, BCR_ABL1, and CARDIAC_MYOSIN, when the end-to-end
    command runs for each, then it produces a connectivity matrix file, a
    top-5 hit list, and a methodological report, without manual
    intervention between stages.
- Constraints And Invariants: per the critical path, this depends on
  Phase 0 (TASK-0070/0052/0047/0063) and Phase 1
  (TASK-0058/0055/0064/0071/0088) — **confirmed Done, 2026-07-12** — an
  honest run requires an honest verdict layer, and that claim is now
  structurally true (provenance-stamped), not just checked-off task IDs.
- Planned Validation: `.005`'s manual inspection of the three deliverables
  for all three mandatory targets; downstream, [[TASK-0082]]'s competence
  map consumes this task's output.

## Subtasks

| ID | Title | Depends on | Status |
|---|---|---|---|
| [[TASK-0079.001]] | Schema assembly: `analysis.py` → `report.py`'s flat results dict (closes SEAM-0008) | Phase 0/1 (Done) | Done |
| [[TASK-0079.002]] | Connectivity matrix + hit list assembly (`pathways.py`/`report.hit_list`) | Phase 0/1 (Done) | Done |
| [[TASK-0079.003]] | FROZEN-gated per-target verdict pipeline | `.001` | Done |
| [[TASK-0079.004]] | One-command orchestrator + output files | `.002`, `.003` | TODO — unblocked, both deps now Done |
| [[TASK-0079.005]] | Run end-to-end for KRAS_G12C / BCR_ABL1 / CARDIAC_MYOSIN + manual inspection | `.004` | TODO |

`.001` and `.002` have no dependency on each other — independently
claimable/parallelizable. `.003` needs `.001`'s assembly function to exist
(imports it). `.004` is the glue step, needs both `.002` and `.003`
landed. `.005` is pure execution + inspection once `.004` exists.

## Dependency

- Feeds [[TASK-0082]] (competence map synthesis) and [[TASK-0083]] (result
  artifact contract) directly — the critical path continues
  `5.1 → 5.2 → 6.1`.
- Related to [[TASK-0080]] (c-Myc special handling) and [[TASK-0081]]
  (generalization set) — same orchestration machinery, applied to
  additional targets, once this lands.
- [[SEAM-0008]] — `.001` closes it.

## Open Questions

- Output file format (NPZ/CSV for the matrix, JSON/text for the hit
  list/report) is `.004`'s call — not fixed here, since [[TASK-0083]]
  (the artifact contract) is explicitly out of scope for this task and
  shouldn't be guessed at prematurely. `.004` should pick something
  reasonable and simple, document the choice, not block on `.083`
  landing first.

## Done

(not yet — parent closes once all 5 subtasks are Done)
