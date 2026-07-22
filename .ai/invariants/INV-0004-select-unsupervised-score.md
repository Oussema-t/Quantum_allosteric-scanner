# INV-0004 `unsupervised_score` and its components — `select.py`

## GAUGE

| Transformation | Test | Status |
|---|---|---|
| Residue relabeling (graph permutation of `H`, `source` remapped consistently) | `tests/test_select.py::TestGaugeResidueRelabeling` — `focusing`, `ballistic_exponent`, and `source_specificity` (when `n_alt` is exhaustive) all confirmed invariant to `atol=1e-9` on a genuinely asymmetric random graph (not the symmetric path/star/complete fixtures, which could hide a labeling bug). | **GAUGE-VERIFIED** (with the sub-sampled-`source_specificity` carve-out below) |
| RNG-seed stability (`source_specificity`'s `rng` param, used to sample `n_alt` alternate sources) | `tests/test_select.py::TestSourceSpecificitySamplingSensitivity` — **real finding**: with the default sub-sampled `n_alt` (< every non-seed node), `source_specificity` is genuinely seed-dependent (measured spread ~0.14 over 15 seeds on a 12-node fixture) *and* not relabeling-invariant (same root cause — see below). Exhaustive `n_alt` is exactly stable (proven, folded into the row above). | **KNOB** (reclassified, not GAUGE — see Provenance) |
| Candidate list order (`unsupervised_score`'s own `candidates` argument) | `tests/test_select.py::TestGaugeResidueRelabeling::test_unsupervised_score_candidate_order_is_gauge` — reordering `candidates` leaves every candidate's own score unchanged (matched by content via `id(H)`, not position); z-score-then-sum is inherently order-independent. | **GAUGE-VERIFIED** |

## KNOB

- `t`/`t_max`/`n_steps` (propagation time and resolution fed to `time_averaged_ctqw`
  inside `focusing`/`source_specificity`) — **characterized**,
  `tests/test_select.py::TestKnobCharacterization::test_focusing_is_fairly_stable_across_t_max_and_n_steps`.
  Small spread on a 12-node synthetic fixture: `t_max` spread ~0.02-0.04, `n_steps`
  spread ~0.02 — `focusing` is the least KNOB-sensitive of this module's four
  reported quantities, already near-converged at the tested grid. Still not
  itself a check of whether `focusing`/`source_specificity`'s call sites use an
  *adequate* value per [[INV-0005]]'s own convergence criteria — that remains open
  if ever needed, but the practical spread is small regardless.
- `n_alt`, `rng` (how many alternate sources `source_specificity` samples, and with
  what randomness) — **characterized**, see the GAUGE table's `source_specificity`
  row above and `TestKnobCharacterization::test_source_specificity_has_a_moderate_t_max_and_n_alt_spread`.
  Measured: `t_max` spread ~0.17 (0.48-0.65, driven by a short `t_max=2` outlier),
  `n_alt` spread ~0.06 (0.46-0.53), seed spread ~0.14 — real, moderate, an order of
  magnitude below `ballistic_exponent`'s own `t_values` sensitivity.
- `t_values` (`ballistic_exponent`'s time grid for the log-log fit) — **characterized,
  and this module's dominant KNOB**:
  `TestKnobCharacterization::test_ballistic_exponent_is_the_most_knob_sensitive_of_the_four`.
  Measured 0.084 (window `t=[1,40]`) to 0.525 (window `t=[0.2,10]`) on the same
  fixture — a >6x range, an order of magnitude larger than every other row here.
  A log-log slope fit over a short-vs-long propagation window genuinely picks up
  different transport regimes (early ballistic-like spreading vs. later
  saturation/crossover to diffusive), not numerical noise. Any caller/reader
  treating a single `ballistic_exponent` value as a stable point estimate should
  read this row first.
- Scalar vs. multi-index `source` (single residue vs. the full active-site
  array) — **closed 2026-07-20 ([[TASK-0089]])**:
  `tests/test_select.py::TestUnsupervisedScoreSourceCardinalityKnob`. Measured
  directly on this module's own path/star/complete fixtures: **the candidate
  ranking flips** between conventions (scalar seed `0` picks `H_COMPLETE`;
  2-residue seed `[0, 1]` picks `H_STAR`) — consistent with
  `REVIEW-panel-2026-07-16-v2` Sec.2.1's project-wide seed-cardinality gauge
  finding (occupation Spearman only 0.61 between conventions) and
  [[TASK-0118]]'s separate resolution for the scored pipeline generally.
  Classified KNOB, not a bug: both conventions are individually well-defined,
  and this module has no privileged answer to arbitrate between them — real
  callers must pick one convention and hold it fixed, not compare across both.

## SIGNAL

- Random/shuffled `H` (a candidate built from a randomized contact graph) must
  score worse than a real structural candidate on the same target —
  **null-controlled**,
  `tests/test_select.py::TestSignalNullControls::test_structured_graph_beats_random_graphs_on_raw_focusing_and_specificity`.
  Uses `H_STAR`'s *raw* `focusing`/`source_specificity` (not `unsupervised_score`'s
  combined z-sum, which is a coin flip with only 2 candidates — checked directly)
  against a batch of 30 independently-drawn random graphs of the same node/edge
  count: `H_STAR`'s focusing clears the random batch's mean+1 std.dev.; its
  specificity clears the random batch's mean. Real, distribution-level separation
  (not a single lucky draw), the same discipline this project's own permutation
  nulls elsewhere use ([[TASK-0131]], [[TASK-0123]]).
- Degenerate single-candidate list (`unsupervised_score([one_candidate])`) —
  **documented**,
  `tests/test_select.py::TestSignalNullControls::test_degenerate_single_candidate_scores_exactly_zero`.
  Confirmed: exactly `0.0` (the `_zscore` epsilon guard's defined behavior), not
  NaN/inf.

## Status

**GAUGE-VERIFIED / KNOB-CHARACTERIZED, 2026-07-20 ([[TASK-0089]]).** Every row
INV-0004 seeded has moved from `OPEN` to a real classification — no row remains
unclassified. One row **reclassified rather than force-passed**: RNG-seed
stability for `source_specificity` was seeded as a GAUGE candidate but is
genuinely KNOB (seed- and relabeling-dependent) whenever `n_alt` sub-samples
rather than exhausts the alternate set — a real, previously-unexamined
sensitivity found by widening the transformation group tested
(`INVARIANCE_PROTOCOL.md` Rule of Engagement #2: "invariant on our test set is
a trigger to widen the group, not a green light"), not silently asserted away.
Not fixed in `select.py` (see Provenance) — flagged in the function's own
docstring instead. No other GAUGE violation was found; `select.py` itself is
otherwise unchanged by this task, per its own Scope.

## Provenance

Seeded 2026-07-12 by [[TASK-0064]] (closing [[SEAM-0009]]), per that task's own
Constraints note: wiring `unsupervised_score` into a real FROZEN-loop consumer
surfaced that this reported quantity has no GAUGE/KNOB/SIGNAL table anywhere,
required by [[TASK-0051]]'s Invariance Protocol before a quantity is reportable.
Filed as its own task ([[TASK-0089]]) rather than completed inline, matching this
task's own Out Of Scope discipline (the connective wiring is this task's job; the
invariance audit is separate, focused work, same split [[TASK-0054]]/[[TASK-0055]]
already use against [[INV-0001]]).

**Updated 2026-07-16 by [[TASK-0090]]:** fixed `select.py`'s multi-index `source`
crash (`_hop_distances_from_source`/`ballistic_exponent`, plus
`source_specificity` -- the actual crash site, previously miscategorized as
"already correct" in that task's own filing). Added the scalar-vs-multi-index
KNOB row above; every other row is unchanged and still owned by [[TASK-0089]].

**Updated 2026-07-20 by [[TASK-0089]] (this task, closing the record):** all
rows classified (see GAUGE/KNOB/SIGNAL tables above). A real GAUGE violation
was found while testing residue relabeling for `source_specificity` with its
*default*, sub-sampled `n_alt` -- traced to `others = [i for i in range(N) if
i not in excluded]` always being ascending-sorted *by label*, with
`rng.choice` then selecting by *position* in that array, so a relabeling
permutation changes which alternates a fixed seed draws even though the
underlying graph is identical up to relabeling. Confirmed (not assumed) that
this disappears entirely once `n_alt` is exhaustive -- isolating the
sub-sampling step, not the Hellinger-distance/`time_averaged_ctqw`
computation, as the actual source. Per this task's own Scope ("fix and
regression-test it" only for a *real GAUGE violation*), this was fixed at the
*classification* level (KNOB, not a false GAUGE pass) and flagged directly in
`source_specificity`'s own docstring, not fixed at the *algorithm* level --
a code fix would require sampling alternates by a canonical graph-intrinsic
order instead of raw label position (the `anm_modes` eigenvalue-not-index
precedent this protocol itself cites), which would change what "a random
sample of other nodes" means (a deterministic subset, not a genuine draw) --
a larger, unrequested behavior change for a real but bounded
(~0.14-spread-on-a-12-node-fixture) sampling-variance effect, not a
wrong-answer bug. `select.py` is otherwise unchanged.
