# TASK-0015 Build the holo-direction module (predicted-graph transport)

## Context

- ID: TASK-0015
- Title: Implement the holo-direction module per
  `__WORK_IN_PROGRESS__/HOLO_DIRECTION_MODULE.md`
- Status: TODO
- Owner: Implementer
- Source: `HOLO_DIRECTION_MODULE.md` (full spec, Steps 0-5); slots between
  `.ai/tasks/PLANS/PLAN.md` Phase 1 (apo/holo superposition + mode
  projection) and Phase 3 (LOPO) — this is the forward-looking, falsifiable
  enhancement `.ai/tasks/PLANS/PLAN-01.07.26.md` Week 4 names as the
  submission's secondary innovation.
- Scope: net-new capability, likely its own module (e.g.
  `__WORK_IN_PROGRESS__/src/allostery/holo_direction.py` — not yet named in
  `PLAN.md`'s repo-structure table since the table predates this spec doc;
  confirm the filename with whoever owns TASK-0002 before creating it) +
  tests.

## Intent Contract

- Outcome: predict the *direction* of the apo→holo conformational change
  from the apo structure alone, generate a small family of admissible
  deformed graphs, and run CTQW/ENAQT transport on each — recovering
  statically-hidden active-site→pocket edges, scored two ways (consensus
  across perturbations, and headroom recovered vs the apo-only floor).
  Every claim must be falsifiable and gated; this is explicitly "not the
  result, the forward-looking innovation" per the source doc.
- In Scope (mirrors `HOLO_DIRECTION_MODULE.md`'s five steps exactly — do
  not reorder or skip Step 2):
  - **Step 0**: pre-register the fixed perturbation protocol in code
    (site-selection rule, mode count `k`, amplitude range, apo-computable
    objective) *before* looking at any holo data for tuning purposes.
    Iterating the protocol until the competence map looks good is leakage
    through protocol selection — same class of risk `protocol.py`
    (TASK-0006) exists to prevent, one level up.
  - **Step 1**: build the admissible deformation family — lowest `k≈5-20`
    ANM modes (reuse TASK-0005's mode machinery), elastic-energy ceiling
    from κ-calibrated B-factors, integrity constraints (Cα spacing, no
    clash, bounded RMSD).
  - **Step 2 — the mandatory go/no-go gate, run this first, before Steps
    3-5 or any circuit work**: per training target, compute cumulative
    overlap (TASK-0005's `CO(m)`) and check whether any candidate deformed
    graph actually creates the specific active-site↔pocket edges. High
    CO + right edges ⇒ proceed for that target. Low CO ⇒ stop for that
    target and record it as a finding (KRAS Switch-II is the doc's
    expected NO case).
  - **Step 3**: optimize the perturbation against an apo-only objective
    (fpocket cavity-openness from TASK-0011, and/or soft-mode
    participation) — classical basin-hopping/CMA-ES first; QUBO+QAOA is an
    optional second NISQ demo, not the result.
  - **Step 4**: run existing `propagators.ctqw`/`haken_strobl` (`[have]`)
    on each admissible deformed graph.
  - **Step 5**: score with the two leakage-clean headline metrics —
    consensus-across-perturbations (holo-free) and headroom-recovered
    (needs TASK-0011's baselines as floor/ceiling anchors).
- Out Of Scope: anything requiring atomistic force fields or mutations —
  explicitly excluded scope per the source doc's own "Out" list.
- Constraints And Invariants: the leakage firewall in
  `HOLO_DIRECTION_MODULE.md`'s own dedicated section — Step 3's objective
  is apo-computable ONLY; using holo to *characterize* the method
  (success/failure histogram) is legal, using it to *parameterize* the
  predictor (any per-target knob) is not.
- Planned Validation: Step 2's gate result *is* the first validation
  checkpoint — do not write Step 3-5 code before Step 2 runs on all
  training targets and its per-target verdicts are recorded, per the
  source doc's own "First action" instruction.

## In Progress

None

## TODO

- [ ] Confirm module filename/location with TASK-0002's owner (avoid
      guessing a name that conflicts with `PLAN.md`'s existing table).
- [ ] Step 0: pre-register the perturbation protocol in code.
- [ ] Step 1: admissible deformation family generator.
- [ ] **Step 2: run the go/no-go gate on all training targets FIRST.**
      Do not proceed to Step 3 until this is done and recorded.
- [ ] Step 3: perturbation optimizer (classical first).
- [ ] Step 4: transport on predicted graphs.
- [ ] Step 5: consensus + headroom-recovered scoring.

## Dependency

- TASK-0005 (`superpose.py`) — Step 1/2 reuse its mode-projection and
  `CO(m)` machinery directly; hard blocker.
- TASK-0006 (`protocol.py`) — Step 0's pre-registration discipline should
  reuse the same DEV/FROZEN context machinery, not a parallel ad hoc one.
- TASK-0011 (`baselines.py`) — Step 3's fpocket objective and Step 5's
  floor/ceiling anchors both come from there.

## Open Questions

- Given this task's hard dependency chain (0005 → 0006/0011 → this), it is
  **not** a good candidate for early parallelization despite the general
  push (per the user's item 7) to parallelize Implementer work — flag this
  explicitly so it isn't picked up before its dependencies land.

## Done

(not yet)
