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
  grid. **OPEN for this call site specifically** — [[TASK-0109]] characterizes
  `propagators.py`'s own `t_max`/`n_steps` KNOBs directly ([[INV-0005]]:
  `check_convergence`/`min_adequate_t_max`/`min_adequate_n_steps`, synthetic
  power-law battery), but does not itself audit whether `focusing`/
  `source_specificity`'s specific call sites use adequate values — that
  remains this row's own open question, now with a tool available to answer it.
- `n_alt`, `rng` (how many alternate sources `source_specificity` samples, and with
  what randomness) — not characterized. **OPEN.**
- `t_values` (`ballistic_exponent`'s time grid for the log-log fit) — not
  characterized. **OPEN.**
- Scalar vs. multi-index `source` (single residue vs. the full active-site
  array) — **newly characterizable 2026-07-16.** Previously uncomputable at
  all: `source_specificity`/`ballistic_exponent` (via
  `_hop_distances_from_source`) both crashed or silently mis-scored on a
  multi-index `source` before [[TASK-0090]]'s fix. Now runs correctly
  (real KRAS_G12C check: 18-residue array through `unsupervised_score`,
  finite differentiated scores), but the *spread* between scalar and array
  conventions on this module's own outputs is not yet measured — directly
  the same seed-cardinality gauge `REVIEW-panel-2026-07-16-v2` Sec.2.1
  flags project-wide (occupation Spearman only 0.61 between conventions on
  synthetic data) and [[TASK-0118]] is filed to resolve for the scored
  pipeline generally. **OPEN** for this module specifically — an
  `unsupervised_score` ranking-stability check across both conventions
  would close this row.

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
verified audit — owner: [[TASK-0089]]. The scalar-vs-multi-index KNOB row above
went from *uncomputable* to *OPEN* on 2026-07-16 ([[TASK-0090]]) — a real state
change, not a re-statement.

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
