# INV-0008 Run-to-run numerical reproducibility of headline scores under nominally identical inputs — cross-cutting (`propagators.py`, `ceiling.py`, `analysis.py`, and every real-compute script that consumes their output)

## GAUGE

| Transformation | Test | Status |
|---|---|---|
| Environment (BLAS thread count / library, concurrent host load, hardware) applied to a fixed, seeded computation on fixed input data | **Not yet characterized systematically.** One confirmed, unresolved instance exists (see Provenance) — not yet generalized to a real test across representative headline computations. | **OPEN** |

This is the correct GAUGE to check: per this project's own
`INVARIANCE_PROTOCOL.md`, a quantity is only reportable once its
transformation table is classified — and "does the environment a
computation happens to run in change its numeric output, given
identical logical inputs and a fixed RNG seed" has never been checked
as its own question, only stumbled into once as a side-effect of
[[TASK-0129]]'s own combined re-run.

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

- Not yet determined — this is exactly what [[TASK-0135]] exists to
  measure. If the environment turns out to be a real KNOB (nonzero,
  non-negligible drift under identical seeded inputs), every headline
  number in `COMPETENCE_MAP.md` needs the same caveat this record is
  raising, not just BCR_ABL1's spectral gap.

## Status

**OPEN — one confirmed instance, root cause not established, no
systematic test yet run.**

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
