# TASK-0030 Extract a shared, unit-tested Kabsch helper in `backend/`

## Context

- ID: TASK-0030
- Title: Deduplicate `backend/discovery.py::_kabsch` and
  `backend/analysis.py::_kabsch_rotate` — two independent, near-identical
  NumPy SVD Kabsch implementations — into one shared, tested helper
- Status: TODO
- Owner: Implementer
- Source: user request, 2026-07-05 session, found while updating TASK-0005
  (`superpose.py`) to point at existing Kabsch prior art instead of
  reimplementing it a fourth time. First concrete instance of the
  "break down the backend spaghetti" goal that motivated TASK-0018.
- Scope: `backend/discovery.py`, `backend/analysis.py`, a new shared
  location (see TODO), plus a new test file. **Not in scope:**
  `backend/compare.py::align_and_compare` — see Constraints below for why.

## Intent Contract

- Outcome: one Kabsch/SVD implementation, unit-tested against a known
  synthetic rotation+translation, used by both current call sites — not
  two copies that can silently drift apart the way `potentials.py`'s
  `V_rigidity`/`V_covariance` already did once against `backend/analysis.py`
  before T-019/T-020 caught it.
- In Scope:
  - Compare `backend/discovery.py::_kabsch(P, Q)` and
    `backend/analysis.py::_kabsch_rotate(mobile, ref)` line-by-line —
    they use the same SVD + `det(Vt.T@U.T)` reflection-correction, but
    different call signatures/return shapes (`_kabsch` returns
    `(R, P_centroid, Q_centroid)` for the caller to apply via
    `_apply_transform`; `_kabsch_rotate` returns the already-aligned array
    directly). Pick one signature (recommend the direct-aligned-array form,
    since both current callers immediately want aligned coordinates, not a
    transform to apply later — confirm by reading both call sites first)
    and update both callers.
  - Unit tests: synthetic point set + a known rotation matrix + translation
    → recover the rotation to floating-point precision; a degenerate/
    reflection case (to exercise the `det` sign-flip branch) so it's
    actually covered, not just implied by the formula.
  - Smoke-test both live call sites after the change: `complete_apo` (used
    by `POST /api/load` with completion) and `morph_frames`/
    `connectivity_change` (used by `GET /api/connectivity-change`,
    `GET /api/morph-frames`) — confirm identical output before/after on at
    least one real benchmark target (e.g. KRAS_G12C), not just that the
    helper's own unit tests pass. Per CLAUDE.md convention 4, this must not
    change any response shape or numeric output the frontend already
    depends on.
- Out Of Scope / explicitly not touching:
  - `backend/compare.py::align_and_compare` — uses Biopython's
    `Superimposer` + `sup.apply()` to transform *all atoms of a full
    Biopython Structure* (needed to emit aligned PDB text for the 3D
    viewer), not just a coordinate array. Unifying it with a plain-NumPy
    helper would mean re-deriving that whole-structure-transform
    convenience Biopython already gives for free — a real design decision,
    not a mechanical dedup. Flag as a follow-up question (see Open
    Questions), don't fold it into this task.
  - `__WORK_IN_PROGRESS__/src/allostery/superpose.py` (TASK-0005) — that
    package should **port** the resulting helper's math (copy, with an
    origin citation), not import across the `backend/`↔`allostery/`
    boundary. Cross-package imports between a live FastAPI service and an
    independent research library are exactly the coupling this repo's
    two-codebase split is meant to avoid (see TASK-0018).
- Constraints And Invariants:
  - Python stdlib/NumPy only — both existing implementations are already
    dependency-free; keep it that way.
  - no API response-shape changes; this is an internal refactor only.
  - the new shared helper's location: a new small `backend/geometry.py`
    (single-concern file, matching this repo's existing module-per-concern
    convention — `active_site.py`, `rcsb.py`, `discovery.py` are all
    domain-scoped, this would be the first purely-mathematical one) is
    recommended over adding it to either existing call site (which would
    just relocate the asymmetry rather than fix it).
- Planned Validation: new unit tests (synthetic rotation + reflection
  case) pass; `complete_apo` and `morph_frames`/`connectivity_change`
  produce byte-identical (or floating-point-tolerance-identical) output on
  a real benchmark target before and after the refactor.

## TODO

- [ ] Read both `_kabsch` and `_kabsch_rotate` call sites fully (not just
      the function bodies already excerpted in TASK-0005/TASK-0018) to
      confirm the safe unification signature.
- [ ] Create `backend/geometry.py` with one `kabsch_align(mobile, ref)` (or
      agreed name) function + docstring citing both original call sites.
- [ ] Update `discovery.py`/`analysis.py` to call the shared helper; delete
      the two originals.
- [ ] Unit tests: known rotation+translation recovery, reflection case.
- [ ] Smoke-test `complete_apo` and `morph_frames`/`connectivity_change` on
      a real target pre/post refactor.
- [ ] Cross-link this task's landed helper from TASK-0005's Dependency
      section (already done pre-emptively; confirm the pointer still
      matches once this lands).

## Dependency

- None (self-contained backend refactor); TASK-0005 has a soft dependency
  on this task's output (see that task's Dependency section) but is not
  blocked by it — it can port from `_kabsch_rotate` directly if this task
  hasn't landed yet.

## Open Questions

- Should `backend/compare.py::align_and_compare` eventually call the same
  shared helper internally (using it for the alignment math, then still
  using Biopython separately for the whole-structure PDB-text export), or
  is keeping it fully independent — since it's solving a superset problem
  (whole-structure transform + text export, not just coordinate alignment)
  — the more honest representation of what it actually does? Recommend
  deciding this only after the two-file dedup lands and is stable, not in
  the same pass — smaller, reviewable step first.
- Worth a `.ai/reference/CAPABILITIES.md` row once this lands (a reusable
  `geometry.kabsch_align` primitive), or is it small/internal enough to
  stay undocumented at that level? Lean toward: not yet, revisit if a third
  internal caller appears.

## Done

(not yet)
