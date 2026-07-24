# TASK-0059 Wire the cumulative-overlap go/no-go gate into which targets `analysis.py` actually scores

## Context

- ID: TASK-0059
- Title: close [[SEAM-0007]] — `superpose.run_superpose`'s
  `cumulative_overlap`/`cryptic_openness_gate` verdict is never consumed
  anywhere; `analysis.py`'s six scoring functions have no parameter
  connecting to it at all
- Status: Done
- Owner: Implementer
- Source: found by [[TASK-0053]] (first seam sweep, 2026-07-11) applying
  the newly-adopted Seam Protocol ([[TASK-0050]]) to the TASK-0003–0012
  module chain — see `.ai/seams/SEAM-0007-superpose-gate-analysis-scoring.md`
  for full evidence.
- Scope: `__WORK_IN_PROGRESS__/src/allostery/analysis.py` (or a new thin
  orchestration function, see Open Questions), consuming
  `superpose.run_superpose`'s output

## ⚠️ Before implementing

**Do a short review before picking a design** — this is a genuine design
decision (which of the options below), not a mechanical fix. Re-read
`PLAN.md`'s Phase 1 gate language and `HOLO_DIRECTION_MODULE.md` Step 2
directly (both are cited in `SEAM-0007`'s evidence) to confirm which of
the two enforcement shapes below (hard exclusion vs. tagged-but-scored)
they actually specify, rather than picking whichever is easier to code.

## Intent Contract

- Outcome: a target whose `cumulative_overlap`/`cryptic_openness_gate`
  verdict says the apo→holo direction is cryptic/not-spanned-by-soft-modes
  cannot silently flow through `analysis.py`'s scoring functions as if it
  had cleared the gate — either it's excluded by default, or the result
  carries the gate verdict alongside it so a caller can't miss it.
- In Scope:
  - decide the enforcement shape:
    (a) a wrapper/orchestration function that calls `run_superpose` first,
    checks the gate, and only calls into `analysis.py`'s scoring functions
    for targets that pass — low-CO targets get a `NO_SIGNAL_IN_APO`-style
    result (reusing `diagnostics.classify_failure`'s existing closed-set
    vocabulary, per this package's own "reuse, don't invent a parallel
    taxonomy" convention) instead of being silently skipped; or
    (b) each scoring function gains an optional `gate_verdict` parameter
    that gets threaded through and attached to the returned dict, with no
    hard exclusion — matches `PLAN.md`'s own framing that a low-CO result
    is "a finding, with a figure... rather than dropping the target
    silently," which argues against a hard exclusion.
  - per the callout above, (b) looks like the better fit to what the
    source docs actually say ("report... rather than dropping... silently"
    argues against hard exclusion) — but confirm before committing to it.
  - a seam-test for `SEAM-0007`: a synthetic target constructed with a
    near-zero cumulative overlap (e.g. `delta_r` orthogonal to the low-mode
    subspace by construction) fed through the new wiring, asserting the
    gate verdict is visibly attached to (or excludes, per whichever design)
    the scoring result — not silently dropped either way.
- Out Of Scope: changing `superpose.py`'s gate computation itself, or
  `analysis.py`'s existing per-function scoring logic — this task only
  adds the missing connective layer.
- Constraints And Invariants: must not change any existing test's
  expected output for `analysis.py`'s six functions when called directly
  (without going through the new wiring) — this is additive, not a
  breaking change to the current call signatures.
- Planned Validation: the new seam-test above; re-run existing
  `test_analysis.py`/`test_superpose.py` suites unchanged.

## TODO

- [ ] Re-read `PLAN.md` Phase 1 + `HOLO_DIRECTION_MODULE.md` Step 2 to
      confirm exclude-vs-tag (see callout).
- [ ] Implement the chosen wiring.
- [ ] Add the `SEAM-0007` seam-test.
- [ ] Update `.ai/seams/SEAM-0007-superpose-gate-analysis-scoring.md` to
      `VERIFIED` once the seam-test passes — do not flip it as part of a
      larger unrelated commit.

## Dependency

- [[TASK-0005]] (`superpose.py`, Done) — the gate this task consumes.
- [[TASK-0008]] (`analysis.py`, Done) — the scoring functions this task
  wraps/extends.
- [[TASK-0015]] (holo-direction module) — that task's own Step 2 already
  names this exact gate as its "First action" prerequisite; this task is
  effectively the piece TASK-0015 was implicitly assuming existed.
  Cross-link, don't duplicate — TASK-0015 should read this task's outcome
  before starting its own Step 2.

## Open Questions

- Should the wiring live inside `analysis.py` itself (each function grows
  a parameter) or as a new thin orchestration module/function one layer up
  (e.g. `analysis.run_gated(...)`, leaving the six existing functions
  untouched)? The latter keeps `analysis.py`'s existing functions
  (already reviewed, already tested) stable and adds the gate as a
  composition rather than a modification — recommend this unless the
  review above finds a reason it must live inside each function.

## Done

**2026-07-24, Implementer D (this thread).** Checked this task's own
premise against current state before designing anything — filed
2026-07-11, before the entire seed/clock/proximity-floor/learnability-
gate arc ([[TASK-0094]]→[[TASK-0139]]) landed. `SEAM-0007`'s core
finding (`analysis.py`'s scoring functions have no gate-verdict
parameter) is still true by direct read of the current code — but "the
gate" itself has moved on from the raw `cryptic_openness_gate`/
`cumulative_overlap` this task's Context names to `superpose.
learnability_verdict` ([[TASK-0120]], refined by [[TASK-0133]]/
[[TASK-0139]]), which is *built from* those same primitives, so wiring
it in still closes the seam as originally scoped — targeting the
current, most-refined version of "the gate" rather than a superseded
one, an Implementer's-call decision stated here.

**Design decision resolved per this task's own "before implementing"
callout** — re-read `PLAN.md` Phase 1 directly: "Report as 'pocket
absent from apo topology' — a finding, with a figure — rather than
dropping the target silently." And `HOLO_DIRECTION_MODULE.md` Step 2:
"Low CO... stop for that target and record it" — read carefully, this
is about that module's own Steps 3-5 (a holo-direction-informed
quantum-walk construction, still shelved, never built), not about
`analysis.py`'s six apo-only scoring functions, which don't consume
the holo-direction module at all. **Both sources argue for tag-
alongside (option b), not hard exclusion (option a)** — confirmed
independently by this project's own established practice since
2026-07-17: KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN are all scored via
`run_challenge.py` regardless of their learnability verdict, which is
reported *alongside* AUC in `RESULTS.md`/`COMPETENCE_MAP.md`, never
used to exclude a target. Chose option (b), as the task's own text
already leaned toward.

**Integration point: `protocol.run_frozen_verdict`, not `analysis.py`
itself** — a layer higher than this task's own Open Question
anticipated ("inside `analysis.py`" vs. "a new thin orchestration
function"), and a better fit than either: `analysis.py`'s six
functions stay completely untouched (stronger than this task's own
Constraints required), and `run_frozen_verdict` is the actual
submission-scoring entry point `run_challenge.py` calls, so wiring
there is where the seam's own invariant ("cannot silently flow through
... scoring functions as if it had cleared the gate") is actually
enforced for a real caller, not just theoretically satisfiable.

**Implementation**: new optional `learnability=None` parameter on
`run_frozen_verdict`, unannotated to match the exact local convention
of its sibling `holo_H`/`holo_source`/`holo_labels`/`apo_idx`/
`holo_idx` parameters. Caller-precomputed (a
`superpose.learnability_verdict(...)` result dict, or any dict with at
least a `"verdict"` key) — `protocol.py` does not import anything from
`superpose.py` to compute it itself, deliberately, matching this
function's own documented "never calls a gated accessor itself"
boundary and the same "caller assembles the holo-informed piece" split
already established for `holo_H`/`holo_labels`. When supplied,
`results["_learnability_verdict"]` (bare category string, same
bare-plus-detail-sibling pattern as `_diagnosis`) and
`results["_learnability"]` (the full dict) are attached; omitted
entirely, not `None`-valued, when not supplied — verified `stamp_
provenance` does a shallow copy with no key filtering, so nothing
strips the new keys.

**Seam-test**: `tests/test_protocol.py::TestLearnabilityWiring` (3
tests, using `learnability_verdict`'s own real signature — a pure
function of 3 floats, so a synthetic near-zero-CO/large-RMSD-ratio
scenario is constructed directly, no apo/holo/alignment plumbing
needed, exactly the "synthetic target constructed with a near-zero
cumulative overlap" this task's own Intent Contract asked for):
default-omitted, a real `UNLEARNABLE_FROM_APO` verdict attached and
visible alongside `_diagnosis` in the same dict, a real `LEARNABLE`
verdict attached symmetrically (not special-cased). `SEAM-0007` moved
to `VERIFIED`.

**Real gap found and filed, not fixed inline**: making this wiring
*actually used* by a real caller requires `run_challenge.py` to
compute and pass `learnability=`, which it doesn't yet — filed as
[[TASK-0150]], deliberately split from this task's own scope,
mirroring [[TASK-0092]]'s own precedent (that task split "support the
holo kwargs" from "wire them into the real run" the same way, two
tasks, not one). Until TASK-0150 lands, the capability exists and is
tested but no live run exercises it yet — stated plainly, not implied
otherwise.

**Full test suite**: 901 passed, 2 xfailed, 0 failed — no existing
test's expected output changed (additive only, per this task's own
Constraints).
