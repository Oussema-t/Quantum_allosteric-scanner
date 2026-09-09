# TASK-0358 — Retest the finite-delay phase observable in the phase-alive band: report the tau-curve, not a tau-point

- Status: TODO
- Owner: **Implementer**
- Priority: **Highest — 6 days to 2026-09-15, and it corrects a claim now in the shipping document**
- Filed: 2026-09-09 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0357]], [[TASK-0130]], [[TASK-0119]], [[TASK-0350]], [[TASK-0157]], [[HYP-P6]], [[HYP-P7]]

## Why this exists: [[TASK-0357]] did not test the claim it was filed to test

[[TASK-0357]] was executed correctly — both Planned Validation checks run and
passed, a real bug caught in its own validation logic, every gap disclosed
including the cohort mismatch. **The defect is in the `tau` rule the Reviewer
wrote into that filing, not in the execution.** Recording that attribution here
so the implementer who picks this up does not go looking for an error in the
code.

Two independent reasons the claim remains untested.

### 1. `tau` landed past the coherence lifetime

`min_adequate_t_max(kind="ground_state_relaxation")` = `-ln(tol)/gap` was defined
by [[TASK-0109]]/[[TASK-0119]] as a **convergence window** — the time by which
the ground-state relaxation has settled to `tol`, i.e. by which transients have
*died*. [[TASK-0357]] used it as a **point delay**, which evaluates the
observable precisely where its phase content is smallest. [[TASK-0130]] proves
the converged limit is phase-free, and [[TASK-0357]]'s own check 2 measured the
decay directly (>10x shrinkage in the time-averaged signed `O(r,t)` from `T=5`
to `T=50000`).

The committed artifact confirms we were in the dead band:

```
signed_secondary:    raw AUC 0.5031    rho_prox -0.0157    resid 0.5018
tau:                 min 49.5   median 209.9   max 8024.0   (tol=1e-2, n=108)
```

`raw 0.503` with `rho_prox -0.016` is **no information about anything, not even
distance**. A null there is the *predicted* outcome for a phase-carrying
quantity evaluated at convergence scale — it is not evidence against a
finite-delay claim.

### 2. The robustness sweep spans a factor of three in `tau`, not an order of magnitude

`tau` depends on the **log** of the tolerance, so [[TASK-0357]]'s tolerance sweep
is far narrower in `tau` than it reads:

| tol | `-ln(tol)` | tau relative | median tau |
|---|---|---|---|
| 1e-3 | 6.91 | 1.50x | ~315 |
| **1e-2 (pre-registered)** | 4.61 | **1.00x** | **210** |
| 5e-2 | 3.00 | 0.65x | ~137 |
| 1e-1 | 2.30 | 0.50x | ~105 |

All four points sit in the same regime. "Not significant at any tolerance one
order of magnitude to either side" is true of the *tolerance* and will be read
as a statement about *tau*. The `tau`-selection-artifact reading of the
`p=0.036` spike may still be correct — but this sweep does not establish it.

## What is already settled and must NOT be re-litigated

- **The distance-proxy hypothesis is falsified.** The Reviewer proposed that a
  sign-inverted finite-delay amplitude would be a distance proxy. The signed
  arm's `rho` against proximity is **-0.016**. It is not. Do not re-raise this
  with the external collaborator; it was our hypothesis and our data killed it.
- **Per-fold sign-fishing is off the table.** The external side reports the sign
  inverted in 53/53 folds — unanimous, so the leave-one-family-out sign choice
  consumed no effective degree of freedom. That objection is answered.
- **The unsigned arm is a different observable.** `|O(r)|` carries real proximity
  content (`rho 0.347`, raw 0.580, resid 0.529) and is where the fragile
  `p=0.036` lives. It is not the external claim. Keep the arms separate.

## Intent Contract

- **Outcome:** the behaviour of `O(r) = 2*Re<r|exp(-iH tau)|a>` **as a function
  of `tau`**, from short delay through convergence — not its value at one
  chosen `tau`.
- **In scope:**
  1. **Report the curve, select nothing.** Scan `tau` on a stated grid spanning
     the phase-alive regime through the converged regime (the natural anchor is
     `TASK-0357`'s own check-2 decay curve, which already brackets it). At every
     `tau`, report the register's standard triple — **raw AUC, `rho` against
     proximity, residualised AUC** — plus the cluster-permutation p.
  2. **Signed `O(r)` is the primary arm**, because that is the external claim.
     Unsigned `|O(r)|` reported alongside as a distinct observable, not as a
     substitute.
  3. **Pre-registered reading, stated here before the run:** a **broad** band of
     `tau` where the effect holds is a signal; an **isolated spike** is a
     selection artifact. Neither outcome requires choosing a `tau`, which is the
     point of scanning — nothing is picked, so nothing can be accused of
     knob-picking.
  4. Reuse `scripts/task0357_finite_delay_phase_observable.py` and its cohort
     unchanged. This is a `tau` axis added to an existing, validated script.
- **Out of scope:**
  - **The cohort-matched reconstruction.** Rebuilding per-structure `H_new` /
    active-site data for the veto pipeline's 435 MIN_HOP=2 structures from the
    `allosteric` branch is explicitly not worth it at six days, and the `tau`
    question is cohort-independent: an artifact on our cohort is an artifact on
    theirs.
  - **The held `+0.031`** (amplitudes vs probabilities). The Reviewer's hold
    stands, unchanged, and is not lifted by this task.
  - Reselecting the submission operator (Tier-2-gated, [[TASK-0100]]).
- **Constraints and invariants:** same cohort, same labels, same code path; the
  `tau` grid is fixed and written down before scoring; no new benchmark.
- **Planned Validation:** at `tau = min_adequate_t_max(tol=1e-2)` the new scan
  must reproduce [[TASK-0357]]'s committed numbers **exactly** (signed raw
  0.5031 / `rho` -0.0157 / resid 0.5018; unsigned raw 0.5797 / `rho` 0.3466 /
  resid 0.5287) before any other `tau` is trusted.

## Open Question — one message could collapse this task to a single run

**The external side has never stated its `tau`, or how it was chosen.** If they
supply it, this becomes a confirmatory run at one delay plus a narrow
neighbourhood, not a full scan. Ask before scanning; scan if no answer arrives
within a day, because the deadline does not wait.

## Submission document

`PHASE1_SUBMISSION_V3.md` was narrowed in the same commit that filed this task.
The paragraph no longer claims the finite-delay route was refuted; it states
what was measured (no information at convergence-scale delay), that the
short-delay regime is unmeasured, and names it as the one quantum route we carry
into Phase 2 with [[TASK-0157]]'s ceiling attached. **If this task returns a
result either way, that paragraph must be updated again in the same commit.**

## Dependency

- [[TASK-0357]] (Done) — the script, the cohort, the validated harness, and the
  numbers this task must reproduce at its anchor `tau`.
- [[TASK-0130]] (Done) — why the converged end of the scan must read as null.
- [[TASK-0350]] (Done) — the 46%/38% finite-T instability the scan will traverse.

## Staged Files

- [2026-09-09 17:18] `__WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V3.md` -- narrow the finite-delay paragraph: no longer claims the route was refuted
- [2026-09-09 17:19] `.ai/COMMON.md` -- registry row for TASK-0358
- [2026-09-09 17:19] `.ai/tasks/TODO/TASK-0358-finite-delay-observable-in-the-phase-alive-band.md` -- the task file itself
