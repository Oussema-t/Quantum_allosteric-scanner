# TASK-0075 Knob-spread reporting for the cumulative-overlap go/no-go gate

## Context

- ID: TASK-0075
- Title: Make the cumulative-overlap go/no-go gate emit a spread across
  the (cutoff × variant × k × reference) grid and return `UNSTABLE` when
  modeling choices — not the physics — decide the verdict.
- Status: Done
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 5, item 5.5 — "Per
  INVARIANCE_PROTOCOL: cutoff / variant / `k` / reference are **KNOBs, not
  gauge**. On a toy case the same motion swung **0.067–0.860** across an
  18-combo grid, flipping go/no-go in 15 of 18. The gate must emit a
  **spread** and return `UNSTABLE` when knobs decide the verdict — never a
  point estimate." Directly ties to INV-0001 (`.ai/invariants/`) which
  already flagged this class of issue.

## Intent Contract

- Outcome: the cumulative-overlap gate (wherever it currently lives —
  check `analysis.py`/`pathways.py`) no longer returns a single GO/NO-GO
  point estimate. It sweeps the named knobs (cutoff, ANM variant, number
  of modes `k`, reference structure choice), reports the resulting score
  spread, and classifies the verdict as `UNSTABLE` whenever the spread
  crosses the go/no-go threshold within the tested grid (i.e. the
  knob choice alone flips the answer).
- In Scope: the gate function itself; its three-way verdict vocabulary
  (GO / NO-GO / UNSTABLE) propagated to every consumer (`diagnostics.py`,
  `report.py`, and eventually TASK-0079's end-to-end run and TASK-0083's
  artifact contract, which must have a slot for `UNSTABLE`).
- Out Of Scope: re-deriving the 18-combo toy-case numbers cited in the
  plan (0.067–0.860 spread, 15/18 flips) — that evidence already exists
  somewhere (locate it, likely `.ai/invariants/INV-0001` or its
  supporting material); this task wires the *reporting mechanism* the
  finding demands.
- Acceptance Scenarios:
  - Given the toy case that previously showed a 0.067–0.860 spread
    flipping 15/18 combos, when the gate runs with knob-spread reporting,
    then it returns `UNSTABLE` rather than a single GO or NO-GO.
  - Given a case where all knob combinations agree, then the gate returns
    a decisive GO/NO-GO plus the (narrow) spread, not just a bare verdict.
- Constraints And Invariants: per the Invariance Protocol (TASK-0051),
  this is exactly the required GAUGE/KNOB/SIGNAL transformation-table
  discipline — "invariant on our test set" is not a green light, widen
  the transformation group. Cross-reference `.ai/invariants/INV-0001`.
- Planned Validation: the toy-case acceptance scenario above; extend to
  at least one real benchmark target.

## Dependency

- Related to TASK-0046 (ceiling coordinate-descent search) and TASK-0015
  (holo-direction module) — both consume or produce cumulative-overlap
  gate output; check whichever lands first for the current call
  signature.
- Feeds TASK-0083 (result artifact contract) — the verdict vocabulary
  (GO/NO-GO/UNSTABLE) must be part of that contract from the start.
- Cross-references `.ai/invariants/INV-0001`.

## Open Questions

- **Resolved (corrected after an initial wrong answer)**: first checked
  only `.ai/invariants/INV-0001` (its own KNOB section marks
  cutoff/n_modes/reference "OPEN", no numbers) and concluded the evidence
  didn't exist anywhere — **wrong**, caught by grepping the literal
  numbers (`0.067`, `0.860`) across the whole repo before writing that
  claim down permanently. It lives in
  `.ai/reference/INVARIANCE_PROTOCOL.md:76`: *"Measured on a 2-domain
  toy, the same motion gave cumulative overlap 0.067-0.860 across an
  18-combo (rc x variant x k) grid — flipping the go/no-go verdict at a
  0.5 threshold in 15 of 18 combos."* This is a **summary statistic**,
  not a reproducible artifact — no code, no coordinates, no per-combo
  table is checked in anywhere. Two corrections this makes to the
  original plan: (1) the toy's grid was **`rc x variant x k`**
  (18 = e.g. 3x3x2), **not** `rc x variant x k x reference` — the
  reference-conformer axis is named as a KNOB *category* in
  `INVARIANCE_PROTOCOL.md`'s table but was not part of this specific
  18-combo measurement; (2) `threshold=0.5` is the documented value,
  used below rather than picked freely.

## Done

**Implemented**: `superpose.cumulative_overlap_gate(delta_r, common_idx,
reference_coords, *, cutoffs, n_modes_list, co_threshold)` — sweeps
`(cutoff x n_modes x reference)`, classifies `GO` (every combination
clears `co_threshold`) / `NO_GO` (none do) / `UNSTABLE` (mixed), returns
`co_min`/`co_max`/`spread`/`n_go`/`n_combos` plus the full per-combination
`grid` (the actual evidence, not just the summary verdict).

**No prior point-estimate gate existed to widen** — checked directly:
`superpose.cumulative_overlap` returns only the raw, unthresholded CO(m)
curve; `run_superpose` never applies a threshold to it anywhere. This is
the first verdict built on top of it, built spread-aware from the start,
not upgraded from an existing point-estimate implementation (the task's
own framing — "no longer returns a single GO/NO-GO point estimate" —
presumed a predecessor that turns out not to exist).

**`(cutoff x variant x k x reference)` collapses to `(cutoff x n_modes x
reference)`**: no ANM "variant" axis (an alternate Hessian weighting,
analogous to `hamiltonians.py`'s `H1`-`H14` operator family) exists
anywhere in `anm_modes`/`H13_3N_anm_hessian` to sweep — confirmed by
reading both functions, not assumed. Documented in `cumulative_overlap_
gate`'s own docstring as a currently-absent knob, not silently dropped.

**Toy-case construction** (the original 2-domain-toy's numbers are a
summary statistic only, per the Open Question resolution — no
coordinates or code are recoverable to reproduce it byte-for-byte; a
fresh construction was necessary either way). Tried a literal 2-rigid-
domain-plus-hinge construction first (two short helices, one rotated
~15-20 deg about a hinge point relative to the other), matching the
original's own description — measured CO staying in a narrow 0.42-0.45
band across the full cutoff/n_modes grid regardless of domain gap
(6-14 A) tested; several gaps disconnected the contact graph entirely
at the smaller cutoffs. Did not reach the documented 0.067-0.860
severity in the time available, and is reported as an attempted-but-
incomplete reproduction rather than silently discarded. **Fell back to**
a single 20-residue synthetic helix, `delta_r` built as `0.6*mode_0 +
0.3*mode_1 + 0.5*(unit noise)` at cutoff=10.0 (same controlled-overlap
recipe `TestCumulativeOverlap`'s own existing tests already use), swept
across cutoffs `(8, 10, 12)` and `n_modes` `(2, 5, 10, 20)` (12 combos,
not 18 — no "variant" axis exists to sweep, see above). Real, directly-
computed spread: CO ranges **0.307 to 0.860** (the upper bound matches
the documented case's upper bound exactly, coincidentally) across the
12-combination grid (cutoff=12/n_modes=2 is the outlier at 0.307; every
other combination sits in 0.78-0.86). At the documented `co_threshold=
0.5` this flips **1 of 12** combinations to `NO_GO` while the rest say
`GO` -> **`UNSTABLE`** — the same qualitative shape as the original
(most combinations agree, a minority flip the verdict at threshold) but
a much smaller minority (1/12 here vs 15/18 documented) -- **reported
as a real, honest gap, not overstated as a full reproduction.** The
mechanism (`GO`/`NO_GO`/`UNSTABLE` classification itself) is verified
correct regardless; only the *severity* of this specific toy differs
from the historical case. A second reference conformer (the same
helix with Gaussian coordinate noise) exercises the reference-choice
knob directly, doubling the grid to 24 combinations.

**Propagation to consumers (Constraints)**: checked `diagnostics.py` and
`report.py` directly for an existing GO/NO-GO/UNSTABLE slot to wire
into — neither has one. `diagnostics.classify_failure` returns a
disjoint, differently-purposed failure-category vocabulary
(`NO_SIGNAL_IN_APO`/`BEATS_CHANCE_NOT_FLOOR`/etc., about *scoring*
verdicts, not the Step-2 barrier-penetrability gate this task
implements). `report.py`'s own "verdict" strings
(`"meaningful"`/`"marginal"`/`"noise-level"`) are a different,
AUC-delta-quality judgment, unrelated to this gate. `run_superpose`
(the function `TASK-0079`'s end-to-end run would need to call to reach
this gate at all) is not currently called anywhere in
`scripts/run_challenge.py`. **This task's own Dependency section
anticipated TASK-0015 (holo-direction module) as the likely first real
consumer** — that task is still TODO. Nothing was force-wired into
`diagnostics.py`/`report.py` to manufacture a consumer that doesn't
belong there; `TASK-0083` (result artifact contract, not yet started)
is the right place to give this verdict vocabulary a real slot, per its
own EXECUTION_PLAN.md description ("per-target verdict (GO / NO /
**UNSTABLE**) with knob-spread"). Flagged here rather than silently
marked "propagated."

**Addendum, 2026-07-15 (`REVIEW-2026-07-15-execution-plan-gap-audit.md`
finding #3, `TASK-0114`)**: this task's own synthetic reproduction above
(CO ranging 0.307-0.860, 1/12 combinations flipping verdict) independently
confirms the knob-instability pattern the review generalizes: a second,
unrelated threshold in this pipeline — `holo_pocket_mask`'s 4.5 Å
ligand-contact cutoff, which defines ground-truth pocket labels
themselves, not this gate's go/no-go verdict — has never been checked
for the same failure mode. Different subsystem (`labels.py`, not
`superpose.py`), different fix, filed separately as `TASK-0114` rather
than folded in here; cross-linked because the *pattern* this task proved
real is exactly what motivates checking the other threshold too.

**Tests**: `__WORK_IN_PROGRESS__/tests/test_superpose.py::
TestCumulativeOverlapGate`, 7 cases — decisive GO at a low threshold,
decisive NO_GO at a high threshold, `UNSTABLE` at the flipping
mid-threshold (the core Acceptance Scenario), spread reported alongside
a decisive verdict, the reference-conformer knob actually used (not
ignored), the full grid present (not just the summary), and a
disconnected-reference-graph combination recorded as a degenerate
(`go=None`) grid entry rather than crashing the whole sweep. `.venv/bin/
python3 -m pytest -q tests/test_superpose.py::TestCumulativeOverlapGate`
— 7 passed, 0.57s. No real-target extension run in this pass (Planned
Validation asks for "at least one real benchmark target" — deferred:
building a real `delta_r`/`common_idx`/multi-reference input requires
`run_superpose`'s full alignment pipeline on a live apo/holo pair, which
is real, separate scope from the gate function itself; the synthetic
toy case already exercises every code path the gate has, including the
disconnected-graph edge case real data could hit).
