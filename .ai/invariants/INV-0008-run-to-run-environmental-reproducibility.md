# INV-0008 Run-to-run numerical reproducibility of headline scores under nominally identical inputs — cross-cutting (`propagators.py`, `ceiling.py`, `analysis.py`, and every real-compute script that consumes their output)

## GAUGE

| Transformation | Test | Status |
|---|---|---|
| Environment (BLAS thread count / library, concurrent host load, hardware) applied to a fixed, seeded computation on fixed input data | **Tested directly, 2026-07-19 ([[TASK-0135]]).** Three representative headline computations (eigendecomposition, blind random search, TPE search), each re-run 3x independently (fresh process, fresh RCSB fetch where applicable) — all three reproduced bit-for-bit identically. BLAS thread-count varied `1/2/4/8` on the spectral-gap case specifically: result changed only in the ~14th significant figure (relative magnitude ~1e-14), utterly negligible for any reported purpose. | **CLOSED — GAUGE holds.** |

This is the correct GAUGE to check: per this project's own
`INVARIANCE_PROTOCOL.md`, a quantity is only reportable once its
transformation table is classified — and "does the environment a
computation happens to run in change its numeric output, given
identical logical inputs and a fixed RNG seed" had never been checked
as its own question, only stumbled into once as a side-effect of
[[TASK-0129]]'s own combined re-run, until [[TASK-0135]]'s direct test.

## KNOB

- Intentional sampling (e.g. `ceiling.ceiling_search`'s 60 random draws,
  Optuna's TPE sampler) is already a *known*, *declared* KNOB — re-running
  with a different seed is expected to change the result, and
  [[TASK-0131]]'s permutation null exists specifically to characterize
  that expected spread. **This record is not about that KNOB.** It is
  about the separate, currently-unclassified question of whether the
  *same* seed, on the *same* nominal inputs, produces the *same* output
  across repeated invocations in this environment — a quantity that
  should behave as an invariant (GAUGE, reproducible) but has one
  confirmed counter-example.

## SIGNAL

- **Determined, 2026-07-19: environment is a GAUGE (negligible), not a
  KNOB.** No caveat needed on `COMPETENCE_MAP.md`'s headline numbers on
  reproducibility grounds — a fixed seed on fixed inputs gives the same
  answer in this environment, to 14+ significant figures, regardless of
  BLAS thread-count. The original BCR_ABL1 gap discrepancy this record
  was raised from is a *different* phenomenon (see Status) and does not
  generalize.

## Status

**CLOSED, 2026-07-19 ([[TASK-0135]]).** Real, controlled, multi-repeat
test across three representative headline computations — see that
task's Done section for the full methodology and numbers. Summary:

1. **`H_new`'s spectral gap on BCR_ABL1**: 3 fresh, independent
   computations (separate processes, separate RCSB fetches) all gave
   `gap=0.032949006294881435` exactly. Varying `OMP_NUM_THREADS`/
   `OPENBLAS_NUM_THREADS`/`MKL_NUM_THREADS` across `1/2/4/8` changed the
   result only in the ~14th significant figure (`0.03294900629488051`
   to `0.03294900629488746`, spread ~7e-15) — real, but ~11 orders of
   magnitude too small to be the explanation for the originally-flagged
   0.0374-vs-0.1933 discrepancy.
2. **`ceiling.ceiling_search` on KRAS_G12C, `seed=7`**: 3 independent
   60-trial runs (one 2026-07-18 during [[TASK-0116]], two fresh
   2026-07-19 in separate checkpoint directories) all converged on the
   identical best trial: `S=0.4735`, identical winning `params` dict.
3. **`optuna_scan.apo_floor_scan` on KRAS_G12C, `seed=7`**: 3 fresh
   in-process repeats, `best_value=1895379886243.563` and
   `best_params` identical every time.

**The `REVIEW-panel-2026-07-17.md`-cited "5.2x from BLAS reduction
order" explanation for the original BCR_ABL1 discrepancy is directly
tested and refuted** — it was an inferred/asserted attribution, not
itself a controlled test (no thread-count-variation methodology is
shown in that review), and the real magnitude of BLAS-order sensitivity
measured here (~1e-14 relative) cannot produce a 5.2x swing.

**The original discrepancy's real cause, most likely, not exhaustively
pinned**: `0.1933` traces to [[TASK-0102]]'s Done section (2026-07-13),
which explicitly reused a *cached* `H_new` Python object from
[[TASK-0091]] rather than rebuilding it — a snapshot from 5 days before
[[TASK-0121]] changed `build_H_new`'s `lam_*` defaults (and possibly
other intervening code changes). Tested both the pre- and post-
TASK-0121 `lam_*` defaults directly on fresh BCR_ABL1 data: neither
reproduces `0.1933` exactly (pre-TASK-0121 gives `0.00107`, current
gives `0.0329`) — the exact cause is not fully pinned, but it is now
**conclusively not environmental nondeterminism** (ruled out directly,
above), and most plausibly some other code difference across that
5-day gap in a cached object that was never rebuilt from the same
inputs twice. Not chased further — per this task's own scope, a stale
historical number now moot anyway ([[TASK-0130]] deleted the
gap-based clock entirely in favor of the closed-form limit).

Raised as a general question by the orchestrating user, 2026-07-18,
explicitly framed as an untested hypothesis, not an assumed fact:
"I am at the moment not really sure to what extent we are improving
computations, and to what we are 'sampling'... I would enjoy
statistically stable outputs and proper logs."

**Existing evidence, one data point, not yet generalized:**
[[TASK-0129]]'s own Done section / `COMPETENCE_MAP.md` (lines ~401-405)
already documents this exact class of failure, found incidentally, not
by a dedicated search: BCR_ABL1's `H_new` spectral gap, freshly computed
twice in the current environment via two independent code paths
(`combined_competence_map_rerun.py`, `fix_clock_operator_sweep.py`),
agrees with itself (`gap=0.0374`, `t*=123.1`) but **disagrees with
[[TASK-0119]]'s own recorded value for the identical computation**
(`gap=0.1933`, `t*=23.8`) — `coords`/`bfactors`/`cutoff` confirmed
byte-identical between the two. Plausibly attributed (not confirmed) to
BCR_ABL1's `H_new` ground state sitting in a genuine near-continuum
(lowest 8 eigenvalues packed within a 0.14 span, consecutive gaps only
0.016-0.05 apart), making *which* eigenvalue pair numerically resolves
as "the gap" sensitive to BLAS reduction order — a real, physically
plausible mechanism, but never isolated from the alternative explanation
(different threads/sessions, different BLAS thread-count environment
variables, different concurrent host load) with a controlled test.

**Why this matters beyond one gap value**: if environmental
nondeterminism is real and not confined to this one near-degenerate
case, it directly threatens the interpretability of every "improvement"
this project has reported this week — a fix's before/after AUC
comparison, a ceiling search's "new best trial," an Optuna scan's
"converged optimum" could each be partly or wholly an artifact of
which environment happened to run which side of the comparison, not a
real effect of the fix/search/optimizer. This is a different, more
fundamental risk than [[P-0005]]'s wall-clock-vs-CPU-time gap (which is
about *timing* claims specifically) — this is about whether the
*reported numeric results themselves* are stable.

## Provenance

Opened 2026-07-18 by this Architect/Planner thread, in response to the
orchestrating user's directly-stated hypothesis. Not yet resolved —
[[TASK-0135]] filed to run a real, controlled reproducibility audit
(repeated identical-seed invocations of representative headline
computations) and to build/propose the granular run-logging convention
(compute time per step/sample/run, environment fingerprint) the user
asked for, so this question is answerable from logs in the future
rather than re-derived by accident each time.
