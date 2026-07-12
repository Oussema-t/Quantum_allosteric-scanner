# TASK-0085 Frontend research visualization

## Context

- ID: TASK-0085
- Title: The scored "interpretability / 3D visualization" objective: top-5
  predicted pockets on the 3Dmol structure, the N×N connectivity heatmap,
  the competence panel (floor/method/ceiling bars), and an explicit
  `UNSTABLE` state when the knobs decide the verdict.
- Status: TODO
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 6, item 6.3 —
  "Honesty rendered, not hidden."

## Intent Contract

- Outcome: `frontend/` gains a research-results view rendering: (1) the
  top-5 predicted allosteric pockets highlighted on the existing 3Dmol.js
  structure viewer, (2) an N×N connectivity heatmap (Plotly, consistent
  with existing frontend conventions), (3) a competence panel showing
  floor/method/ceiling bars per TASK-0082's synthesis, and (4) an
  explicit visual `UNSTABLE` state (per TASK-0075) distinct from GO/NO-GO,
  not silently defaulting to one or the other.
- In Scope: new frontend view(s) consuming TASK-0084's backend results
  API; no new backend logic (that's TASK-0084's scope).
- Out Of Scope: computing any of the underlying data — purely
  presentation, consistent with the "backend serves artifacts, frontend
  shows them" architecture the plan establishes.
- Acceptance Scenarios:
  - Given a target with a precomputed artifact, when the results view
    loads, then the top-5 pockets appear highlighted on the 3D structure
    and the connectivity heatmap renders.
  - Given a target whose verdict is `UNSTABLE`, then the UI visibly
    distinguishes this from a GO or NO-GO verdict — not a missing/blank
    state, an explicit one.
  - Given TASK-0032 (already Done) escaped RCSB-sourced strings before
    `innerHTML` injection, then this new view follows the same escaping
    discipline for any target-derived text it renders.
- Constraints And Invariants: frontend assets are no-cache (CLAUDE.md
  convention 5) — remind whoever deploys this to hard-refresh; reuse
  existing 3Dmol.js/Plotly patterns already in `frontend/app.js` rather
  than introducing a new visualization library.
- Planned Validation: manual browser check per this repo's standing
  convention (start the dev server, exercise the golden path — a
  target with a real artifact — and the `UNSTABLE` edge case) before
  calling this done; per TASK-0022 (frontend tiered test coverage),
  align with whatever tiered-test convention that task establishes.

## Dependency

- Depends on TASK-0084 (backend results API) — this view consumes those
  endpoints.
- Depends on TASK-0083 (artifact contract) transitively, for knowing what
  fields exist to render.
- Should follow TASK-0022's frontend test-coverage conventions once that
  task establishes them.

## Open Questions

- None beyond what TASK-0083/0084 need to settle first (exact field
  names/shapes this view will bind to).

## Done

(not yet)
