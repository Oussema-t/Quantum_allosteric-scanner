# TASK-0350 — Ask the interference question properly: coherent vs decoherent, matched operator, matched seed

- Status: TODO
- Owner: **Implementer**
- Priority: **Highest experiment remaining before 2026-09-15**
- Filed: 2026-09-08 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0130]], [[TASK-0140]], [[TASK-0146]], [[TASK-0157]], [[TASK-0320]], [[TASK-0348]]

## Why, and what the register already establishes

`time_averaged_ctqw_converged` is **provably phase-free at convergence** — this
register's own finding, recorded in [[TASK-0130]] and cited in [[TASK-0140]],
[[TASK-0145]], [[TASK-0146]], [[TASK-0157]] and [[TASK-0182]]. `coherent=False`
is the established default across `ceiling_search_batched.py`,
`ceiling_permutation_null.py` and `apo_structure_sensitivity_sweep.py`.

**So the observable behind almost every number we report is the decoherent
limit.** That is not an accident and it was not missed — we proved it, and then
built three separate observables specifically to reach past it: chiral
circulation ([[TASK-0140]], FAIL), frequency-domain coherence ([[TASK-0146]]),
and two-boson HOM interference ([[TASK-0157]], filed as *"the ONLY residual that
has not already been ruled out"*).

What has **never** been run is the simplest and most direct version: **the same
operator, same seed, same cohort, coherent vs decoherent.** Every existing
comparison changes the observable as well as the coherence.

An external review of the `allosteric` branch has now independently arrived at
the same point from the other side — its finding that `p_avg` is *"provably free
of cancellation"* is our own phase-free result, found again. The question is
live for both branches and neither has answered it cleanly.

## Intent Contract

- Outcome: AUC (and the register's standard residualised AUC) for
  `time_averaged_ctqw_converged(..., coherent=True)` vs `coherent=False`,
  **identical Hamiltonian, identical seed set, identical cohort, identical
  scoring** — the single-variable comparison.
- Add the operator-matched classical twin alongside it: the heat kernel
  `exp(-Lt)` on the same graph. Three arms, one variable changing at a time —
  classical diffusion → decoherent walk → coherent walk.
- **Pre-registered prediction, stated before running:** the coherent–decoherent
  gap is small and non-significant, consistent with [[TASK-0146]]'s own finding
  that `T=50000` and the converged limit agree to ≤0.005 AUC on all three
  targets. If that holds, it is the cleanest statement we can make: *the
  interference content of this construction is measurably zero, not merely
  unmeasured.*
- Constraints:
  - Family/cluster-level reporting with a cluster-permutation p-value
    ([[TASK-0337]]).
  - Reuse the existing cohort and labels; introduce no new benchmark.
  - Report the finite-t sensitivity alongside — [[TASK-0146]] found KRAS_G12C's
    floor-clearing verdict **flips** between the default and `T=50000`. That
    instability is itself a reportable property and must not be averaged away.
- Planned Validation: `coherent=False` must reproduce the existing published
  numbers exactly before the `coherent=True` arm is trusted.

## Why it matters for the submission

Our §2 states the interference hypothesis and then tests it with a propagator
that provably has none. A referee with a physics background sees that in a
minute. **The fix is not to soften the hypothesis — it is to report that we
identified the phase-free property ourselves and measured what escaping it
buys.** With this run, §2 becomes: we proved the converged limit is phase-free,
built three observables to reach past it, and measured the coherent–decoherent
gap directly. That is a stronger section than the one we have.
