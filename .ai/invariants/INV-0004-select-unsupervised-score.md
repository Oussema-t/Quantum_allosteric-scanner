# INV-0004 `unsupervised_score` and its components — `select.py`

## GAUGE

| Transformation | Test | Status |
|---|---|---|
| Residue relabeling (graph permutation of `H`, `source` remapped consistently) | Not checked. `focusing`/`source_specificity`/`ballistic_exponent` all operate on `H`'s eigenstructure and hop-distances from `source` — a consistent relabeling should leave every score unchanged, but no test asserts it. | **OPEN** |
| RNG-seed stability (`source_specificity`'s `rng` param, used to sample `n_alt` alternate sources) | Not checked. `source_specificity` explicitly accepts an `rng` override — its default behavior across different seeds (or no seed) is unverified as stable within tolerance, only as *runnable*. | **OPEN** |
| Candidate list order (`unsupervised_score`'s own `candidates` argument) | Not checked. `select_frozen_config` (TASK-0064) picks `scores.argmax()`, so a stable ranking under reordering matters for reproducibility — no test reorders `candidates` and re-asserts the same winner. | **OPEN** |

## KNOB

- `t`/`t_max`/`n_steps` (propagation time and resolution fed to `time_averaged_ctqw`
  inside `focusing`/`source_specificity`) — not characterized as a spread over a
  grid. **OPEN.**
- `n_alt`, `rng` (how many alternate sources `source_specificity` samples, and with
  what randomness) — not characterized. **OPEN.**
- `t_values` (`ballistic_exponent`'s time grid for the log-log fit) — not
  characterized. **OPEN.**

## SIGNAL

- Random/shuffled `H` (a candidate built from a randomized contact graph) must
  score worse than a real structural candidate on the same target — not
  null-controlled. **OPEN.**
- Degenerate single-candidate list (`unsupervised_score([one_candidate])`) —
  behavior (a single z-score of one point) is arithmetically defined but not
  asserted as a documented edge case. **OPEN.**

## Status

All OPEN — this is a seed record (mirrors [[INV-0001]]'s own seeding precedent:
"mixed... not a completed audit"), not a completed classification. Rows are the
natural candidate transformations for `focusing`/`source_specificity`/
`ballistic_exponent`/`unsupervised_score` given their actual signatures, not a
verified audit — owner: [[TASK-0089]].

## Provenance

Seeded 2026-07-12 by [[TASK-0064]] (closing [[SEAM-0009]]), per that task's own
Constraints note: wiring `unsupervised_score` into a real FROZEN-loop consumer
surfaced that this reported quantity has no GAUGE/KNOB/SIGNAL table anywhere,
required by [[TASK-0051]]'s Invariance Protocol before a quantity is reportable.
Filed as its own task ([[TASK-0089]]) rather than completed inline, matching this
task's own Out Of Scope discipline (the connective wiring is this task's job; the
invariance audit is separate, focused work, same split [[TASK-0054]]/[[TASK-0055]]
already use against [[INV-0001]]).
