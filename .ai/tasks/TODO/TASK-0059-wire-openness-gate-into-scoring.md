# TASK-0059 Wire the cumulative-overlap go/no-go gate into which targets `analysis.py` actually scores

## Context

- ID: TASK-0059
- Title: close [[SEAM-0007]] — `superpose.run_superpose`'s
  `cumulative_overlap`/`cryptic_openness_gate` verdict is never consumed
  anywhere; `analysis.py`'s six scoring functions have no parameter
  connecting to it at all
- Status: TODO
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

(not yet)
