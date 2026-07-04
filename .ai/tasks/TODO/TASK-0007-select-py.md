# TASK-0007 Implement `select.py` — unsupervised operator selector

## Context

- ID: TASK-0007
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/select.py`
- Status: TODO
- Owner: Implementer
- Source: **no notebook precedent — net-new.** `.ai/tasks/PLANS/PLAN.md`
  Phase 3 ("`select.unsupervised_score` (focusing, source-specificity,
  ballistic exponent) — label-free config selection, enforced by
  `protocol.FROZEN`")
- Scope: `__WORK_IN_PROGRESS__/src/allostery/select.py` (currently a 5-line
  stub, despite `PLAN.md`'s repo-structure table marking it `[have]` —
  that annotation is stale, see Open Questions) +
  `__WORK_IN_PROGRESS__/tests/test_select.py` (new)

## Intent Contract

- Outcome: a way to pick which Hamiltonian/operator variant and which
  propagation parameters to use on a FROZEN (held-out) target **without
  ever looking at its labels** — using only properties observable from the
  apo structure and the walk's own dynamics.
- In Scope:
  - `focusing(P)` — how concentrated the time-averaged walk distribution is
    (relates to `metrics.ipr`, already implemented — reuse, don't
    reimplement).
  - `source_specificity(...)` — does the walk from the seed distinguish
    itself from walks seeded elsewhere (label-free proxy for "is this
    operator informative").
  - `ballistic_exponent(...)` — spread-vs-time scaling exponent, a
    label-free coherence/transport-regime diagnostic.
  - `unsupervised_score(candidates)` — combine the above into one ranking
    over candidate operator/parameter configs, usable inside
    `protocol.leave_one_protein_out`'s FROZEN loop.
- Out Of Scope: the DEV/FROZEN enforcement itself (TASK-0006).
- Constraints And Invariants:
  - every function here must be computable from the apo structure and its
    own walk output alone — if a metric needs the holo pocket to compute,
    it belongs in `analysis.py` (TASK-0008), not here. This is the
    line that keeps FROZEN-path selection legitimate.
- Planned Validation: unit tests using `metrics.ipr`/`spectral_gap` outputs
  on synthetic graphs with known localization/delocalization behavior, to
  confirm `focusing`/`ballistic_exponent` move in the expected direction.

## In Progress

None

## TODO

- [ ] Implement `focusing`, `source_specificity`, `ballistic_exponent` as
      label-free functions over `propagators.ctqw`/`time_averaged_ctqw`
      output.
- [ ] Implement `unsupervised_score` combining them.
- [ ] Unit tests on synthetic graphs (path vs star vs complete — should
      give clearly different focusing/ballistic-exponent readings).
- [ ] Confirm and correct `.ai/tasks/PLANS/PLAN.md`'s repo-structure table,
      which currently marks this file `[have]` — file it as a fix in
      TASK-0002 (scaffold hygiene) once this task lands, since that's a
      cross-cutting doc-accuracy issue, not this task's own scope.

## Dependency

- TASK-0006 (`protocol.py`) — this module's output is only meaningful
  inside the FROZEN context that module defines.
- Existing `metrics.py`, `propagators.py` (both `[have]`) supply the raw
  walk/graph statistics this module scores.

## Open Questions

- `PLAN.md`'s repo-structure table lists this file as `[have]` alongside
  `protocol.py`, but both are 5-line stubs on disk. Was `[have]` written
  aspirationally (i.e., "will exist by the time Phase 3 starts") or is it
  simply wrong? Recommend treating every `[have]` tag in that document as
  unverified until spot-checked — TASK-0002 should do a full pass on this.
  **Resolved by TASK-0002 (2026-07-04):** simply wrong, not aspirational —
  full spot-check done, `PLAN.md`'s repo-structure table corrected (`select.py`
  and `protocol.py` now tagged `NEW`; `clean.py` and `potentials.py`, which had
  the opposite drift — tagged `NEW` while fully implemented — corrected to
  `[have]`). See `PLAN.md`'s repo-structure section for the note.

## Done

(not yet)
