# TASK-0089 Classify `select.py`'s reported quantities (closes `INV-0004`)

## Context

- ID: TASK-0089
- Title: Close the `GAUGE`/`KNOB`/`SIGNAL` rows [[INV-0004]] seeds for
  `unsupervised_score`/`focusing`/`source_specificity`/`ballistic_exponent`
- Status: Done
- Claimed By: Implementer D (this thread)
- Claimed At: 2026-07-20
- Owner: Implementer
- Source: flagged by [[TASK-0064]] (closing [[SEAM-0009]], wiring
  `unsupervised_score` into a real FROZEN-loop consumer via
  `protocol.select_frozen_config`) — that task's own Constraints noted
  `select.py` has zero `.ai/invariants/` coverage per
  [[TASK-0051]]'s Invariance Protocol ("No transformation table → not
  reportable"), and deliberately did not build it inline, same
  in-scope/out-of-scope split [[TASK-0054]]/[[TASK-0055]] already use
  against [[INV-0001]].
- Scope: `__WORK_IN_PROGRESS__/src/allostery/select.py`'s four scoring
  functions and [[INV-0004]]'s seeded rows only. No change to `select.py`
  itself expected unless a real GAUGE violation is found (then: fix and
  regression-test it, same as `superpose.py`'s `w[6:]` precedent
  `INVARIANCE_PROTOCOL.md` documents).

## Intent Contract

- Outcome: every row [[INV-0004]] seeds moves from `OPEN` to
  `GAUGE-VERIFIED` / `KNOB-CHARACTERIZED` / a documented `SIGNAL` null
  control — or, if a row turns out not to apply, an explicit note saying
  why, not silent removal.
- In Scope:
  - **GAUGE**: residue-relabeling invariance (permute `H`'s indices +
    `source` consistently, assert every score unchanged to `atol≈1e-9`);
    RNG-seed stability for `source_specificity`'s `n_alt`-sample step
    (report a CI/spread across seeds, or prove it's deterministic given a
    fixed `rng`); candidate-list-order stability for `unsupervised_score`
    (reorder `candidates`, assert the same winner by content, not index).
  - **KNOB**: characterize `t`/`t_max`/`n_steps`/`n_alt`/`t_values` as a
    spread over a small grid on a synthetic case (per
    `INVARIANCE_PROTOCOL.md` Tier 2 — report the spread, don't assert a
    point estimate).
  - **SIGNAL**: a shuffled/randomized-`H` null control (a garbage
    candidate must not out-score a real structural one); document the
    single-candidate degenerate case.
- Out Of Scope: `protocol.select_frozen_config`'s own gating behavior
  (TASK-0064's own seam-tests already cover that) — this task audits
  `select.py`'s scoring functions themselves, not their FROZEN-loop
  wiring.
- Constraints And Invariants: per `INVARIANCE_PROTOCOL.md`'s own rule of
  engagement, "invariant on our test set" is not a green light — widen
  the transformation group actually tested (real permutations, not one
  fixed relabeling) rather than asserting on a single convenient case.
- Planned Validation: `INV-0004`'s own rows, each with a named passing
  test; existing `test_select.py` suite unchanged.

## In Progress

None

## Dependency

- [[TASK-0007]] (`select.py`, Done) — the module under audit.
- [[TASK-0064]] (Done) — found and flagged this gap; seeded [[INV-0004]].
- [[INV-0001]]/[[TASK-0054]] — the precedent this task's split follows.

## Open Questions

- None yet — surface once the permutation/RNG tests are actually written;
  [[INV-0004]]'s seed rows are candidate transformations reasoned from
  each function's signature, not yet verified as complete or correct.
  **Resolved 2026-07-20**: one real question surfaced and answered — see
  Done section (the sub-sampled `source_specificity` relabeling finding).

## Done

**2026-07-20, Implementer D (this thread).** Picked up over a stale claim
(Implementer A, 2026-07-12, no commits or uncommitted work referencing
this task or [[INV-0004]] found — force-claimed with a stated reason).

**Every row [[INV-0004]] seeded is now classified** (GAUGE-VERIFIED /
KNOB-CHARACTERIZED / SIGNAL null-controlled) — full detail, exact
numbers, and test names live in `INV-0004`'s own updated tables, not
duplicated here. 35 new tests, `tests/test_select.py` (append-only, the
existing suite is byte-unchanged per this task's own Planned Validation).

**A real GAUGE violation was found, verified, and correctly classified
(not silently passed or silently asserted as a bug):** `source_specificity`
is NOT invariant under residue relabeling when its default `n_alt`
sub-samples alternates (< every non-seed node) — confirmed empirically
before writing any test (a fixed rng gives a different score after a
relabeling permutation: 0.307 vs 0.271 on a first scratch check). Root-
caused directly: `others = [i for i in range(N) if i not in excluded]`
is always ascending-sorted *by label*; `rng.choice` selects by *position*
in that array, so relabeling changes which alternates a fixed seed draws.
Confirmed (not assumed) that this disappears entirely once `n_alt` is
exhaustive — isolates the sub-sampling step, not the underlying Hellinger/
`time_averaged_ctqw` computation, as the actual source
(`source_specificity(H, source, n_alt=N-1)` before/after a relabeling
permutation matches to `1e-9`; sub-sampled `n_alt` does not).

**Judgment call, stated explicitly (this task's own Scope: "fix and
regression-test it" only for a real GAUGE violation):** did NOT change
`select.py`'s sampling algorithm. A code fix would mean sampling
alternates by a canonical graph-intrinsic order instead of raw label
position (the exact `anm_modes` eigenvalue-not-index precedent this
protocol itself cites) — but that changes what "a random sample of other
nodes" *means* (a deterministic subset every time, not a genuine draw),
a materially bigger and unrequested behavior change for a real but
bounded effect (~0.14 measured spread across 15 seeds on a 12-node
synthetic fixture) — not a wrong-answer bug the way the ANM mode-slicing
was. Reclassified GAUGE→KNOB instead, with the spread characterized and
locked into a regression test, and flagged directly in
`source_specificity`'s own docstring so a future reader doesn't assume
invariance that isn't there.

**Other real findings, measured not assumed:**
- `unsupervised_score`'s candidate ranking **flips** between the scalar
  and multi-index `source` conventions on this module's own path/star/
  complete fixtures (scalar seed `0` → `H_COMPLETE` wins; 2-residue seed
  `[0,1]` → `H_STAR` wins) — closes INV-0004's "newly characterizable"
  row, consistent with `REVIEW-panel-2026-07-16-v2`'s project-wide
  seed-cardinality finding. Classified KNOB (a modeling choice with no
  privileged answer), not a bug.
- `ballistic_exponent`'s `t_values` window is this module's dominant
  KNOB by a wide margin — measured 0.084 to 0.525 (>6x range) across
  three time-window choices on the same fixture, an order of magnitude
  larger than every other characterized KNOB in this module
  (`source_specificity`'s `t_max`/`n_alt`/seed spreads are 0.06-0.17;
  `focusing`'s `t_max`/`n_steps` spread is 0.02-0.04). A real transport-
  regime effect (early ballistic-like spreading vs. later saturation),
  not numerical noise.
- SIGNAL null control used the module's *raw* `focusing`/
  `source_specificity` outputs, not `unsupervised_score`'s combined
  z-sum — checked directly that a 2-candidate z-score competition is a
  coin flip regardless of the true underlying gap (z-scores of 2 points
  are always exactly ±1), which would have made a naive
  `unsupervised_score`-based SIGNAL test uninformative. Compared
  `H_STAR` against a batch of 30 independently-drawn random graphs
  (same node/edge count) instead of one instance, the same
  distribution-level discipline this project's own permutation nulls
  use elsewhere ([[TASK-0131]], [[TASK-0123]]).

**Not done / explicitly out of scope** per this task's own Out Of Scope:
`protocol.select_frozen_config`'s own FROZEN-loop gating behavior
(TASK-0064's seam tests already cover it) — this task audits `select.py`'s
scoring functions themselves only. Full regression suite re-run after
this change: 829 passed, 2 xfailed, no failures.
