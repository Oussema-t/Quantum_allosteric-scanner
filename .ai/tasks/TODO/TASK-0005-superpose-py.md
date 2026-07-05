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
- Status: TODO
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

## TODO

- [ ] Kabsch/SVD superposition + per-chain RMSD — **port from
      `backend/analysis.py::_kabsch_rotate` (or TASK-0030's deduplicated
      helper, if it lands first), do not rewrite from scratch.**
- [ ] 3D pocket cross-map vs `labels.py`'s sequence-alignment map;
      disagreement handling (log + flag, don't silently pick one).
- [ ] Cryptic-openness gate (per-residue apo→holo RMSD at pocket residues).
- [ ] ANM mode computation (reuse `hamiltonians.H13_3N_anm_hessian`? — audit
      whether that existing function is a legitimate base rather than
      reimplementing ANM from scratch).
- [ ] Cumulative overlap `CO(m)`.
- [ ] κ calibration against B-factors (`clean.py`'s `CleanResult.b_mean`/
      `b_std` already surfaces the inputs this needs).
- [ ] Elastic energy per mode + overdamped relaxation timescale.
- [ ] Unit tests (synthetic rotation, synthetic mode-confined Δr).
- [ ] KRAS_G12C real-target check; document the expected-low-CO result.

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
- Should the cryptic-openness verdict be a hard boolean gate or a continuous
  score that `protocol.py` (TASK-0006) thresholds? `PLAN.md` phrases it as
  "yes/no" but a continuous `CO(m)` is more informative for the competence
  map — recommend storing both.
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

## Done

(not yet)
