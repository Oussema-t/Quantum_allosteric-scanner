# TASK-0357 — Replicate the finite-delay phase-sensitive observable under a principled clock and a pre-registered sign

- Status: TODO
- Owner: **Implementer**
- Priority: **High — the only live candidate for a positive quantum measurement before 2026-09-15**
- Filed: 2026-09-09 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0130]], [[TASK-0119]], [[TASK-0146]], [[TASK-0157]], [[TASK-0348]], [[TASK-0350]], [[HYP-P6]], [[HYP-P7]]

## The claim under test (external, `allosteric` branch)

A collaborator reports a finite-delay, phase-sensitive observable

```
    O(r) = 2 * Re < r | exp(-i H tau) | a >
```

(`a` = active site, `r` = candidate residue) scoring **+0.114 AUC, p = 0.004 on
distal residues**, with "configuration and sign chosen blind by leave-one-family-out",
surviving removal of CAS0002. Separately **+0.031, p = 0.020** for amplitudes vs
probabilities on a matched operator across 399 families. **No P@5 gain** is
claimed in either case.

## What this register already establishes — read before implementing

**1. The observable is ours, pre-derived, and it is not a post-hoc fish.**
[[TASK-0157]]'s precondition gate (2026-08-02, Implementer B) required a
*non-reducibility* proof before any `N^2` work, and produced one. For two
non-interacting bosons from distinct sources the coincidence probability expands
into Falsifier C's dead product term **plus** a genuine interference cross-term

```
    2 * Re[ c_i(t) c_j'(t) ( c_j(t) c_i'(t) )* ]
```

which "depends on the *relative phase* between two single-particle amplitude
paths — information every converged/time-averaged observable in this register
([[TASK-0130]]) provably discards." That file's Open Questions section then
states, in advance, that the finite-time form is the one that keeps the term and
that time-averaging "would silently collapse this observable back into Falsifier
C's already-dead product quantity."

**The external result is therefore consistent with this register's own written
prediction, not a contradiction of [[TASK-0350]]'s null.** Say so explicitly in
the write-up. [[TASK-0350]] measured the *converged* propagator, which is
provably phase-free, so its `+0.0023 / p = 0.919` is the expected answer there
and says nothing about finite delay.

**2. The defect is `tau`, and we have already measured how severe it is.**
[[HYP-P6]] exists because propagation time is a free knob: *"The ranking of
residues changes with t. Silently choosing t_max=20 is not scientifically
defensible."* [[TASK-0119]] confirmed the concern is real, not hypothetical —
10 of 11 of CARDIAC_MYOSIN's `ctqw` floor-clears did not survive a corrected
clock. [[TASK-0350]] then quantified it at cohort scale:

> **50/108 (46%) coherent and 41/108 (38%) decoherent structures flip
> resid-AUC sign between T=15 and the converged limit** — a real, large
> finite-T instability, not averaged away.

A finite-delay observable lives entirely inside that unstable band, and `O(r)`
is a **signed** quantity. Two consequences the replication must address:

- Leave-one-family-out protects against leaking the held-out family. It does
  **not** protect against the observable being a `tau`-scan artifact.
- With a ~46% baseline sign-flip rate, a **sign chosen per fold is capable of
  fitting that instability directly.** Choosing the sign roughly doubles the
  hypothesis space, and the reported `p = 0.004` is conditional on a
  configuration that was selected rather than fixed in advance.

**3. The principled clock already exists in this codebase — do not invent one.**
`propagators.min_adequate_t_max(kind="ground_state_relaxation")` = `-ln(tol)/gap`
(`gap` = H's own spectral gap, `tol=1e-2`), built and validated by
[[TASK-0109]]/[[TASK-0119]], is [[HYP-P6]]'s own alternative 2 with the
log-tolerance constant made explicit.

**4. The honest ceiling is already written, and must be carried forward.**
[[TASK-0157]], from the primary citations (Valiant 1979; Terhal & DiVincenzo
2002; Aaronson & Arkhipov 2011): a 2x2 permanent is exactly as easy as a 2x2
determinant, so **even a clean positive is a better observable, not a
demonstrated quantum advantage.** Any write-up of a surviving result states this
in the same paragraph as the number.

## Intent Contract

- **Outcome:** does `O(r) = 2*Re<r|exp(-i H tau)|a>` retain a distal-AUC
  advantage when `tau` is fixed by a principled per-protein rule and the sign is
  pre-registered, on a single agreed cohort?
- **In scope:**
  1. **Fix `tau` per protein** via `min_adequate_t_max(kind="ground_state_relaxation")`.
     No sweep, no per-fold `tau` selection.
  2. **Pre-register the sign** from a stated physical argument, written into this
     file *before* the scoring run. If no such argument can be written, report
     the **unsigned** `|O(r)|` as primary and the signed form as secondary — do
     not let the sign remain a fitted degree of freedom.
  3. Report **both** P@5 and residualised AUC. P@5 is the shipped metric; an AUC
     gain with no P@5 movement is reported as exactly that.
  4. Family/cluster-level reporting with a cluster-permutation p-value
     ([[TASK-0337]]), consistent with every other arm in this register.
  5. **Secondary arm — the held `+0.031`:** amplitudes vs probabilities against a
     **spectrally-matched** control. Amplitudes and probabilities differ in
     normalisation and dynamic range, not only in phase; without the matched
     control the contrast is not attributable to interference. This is the same
     hold the Reviewer placed on the merge and it is not lifted by this task
     unless the matched control clears.
- **Out of scope:**
  - Re-running [[TASK-0350]]. Its null is about the converged propagator and is
    not in dispute.
  - Any claim of asymptotic quantum advantage (see ceiling above).
  - Reselecting the submission operator (Tier-2-gated, [[TASK-0100]]).
- **Constraints and invariants:**
  - **Cohort must be fixed before either side's numbers are quoted.** Ours is 276
    families; the external result is 399. The collaborator has already conceded
    this. Pick one, state which, and score every arm on it.
  - `tau` rule, sign convention and scoring definition are fixed once, written
    down, and blind to labels.
  - Reuse existing cohorts and labels; introduce no new benchmark.
- **Planned Validation:** reproduce [[TASK-0350]]'s converged-limit numbers
  exactly from the same code path before the finite-delay arm is trusted. A
  finite-delay implementation that cannot recover the converged result as
  `tau -> inf` is not yet correct.

## Pre-registered prediction, stated before running

Uncertain, and deliberately recorded as such rather than as a directional
expectation: the cross-term is real and pre-derived, so a genuine effect is
physically possible; but a 46% sign-flip rate across `tau` is exactly the
signature that produces a selected-configuration positive. **The task is
designed so that either outcome is publishable** — a surviving effect is the
Phase-2 route, a collapse under a principled clock is a clean methodological
finding about selection on `tau`.

## Why it matters for the submission

Two separate things, and they must not be conflated:

1. **V3 does not need this number.** The submission's argument is that the
   *credibility* of a quantum advantage here is low, and the rubric asks for
   credibility, not proof of advantage. A positive that later fails is worse for
   Phase 2 than an honest null, because a PoC sprint built on a `tau` artifact is
   a wasted sprint.
2. **V3 does have a real gap the external review identified correctly**: every
   quantum number in it is a null, which leaves a Phase-2 sprint with nothing
   quantum to build. That gap closes at near-zero cost and without asserting an
   unvalidated result — see the doc edit below, which is **not** blocked on this
   task's outcome.

## Doc edit — independent of this task's result, do it now

`PHASE1_SUBMISSION_V3.md` line ~86, *What we propose to build in Phase 2*: name
the finite-delay phase-sensitive observable as the concrete quantum route, with
[[TASK-0157]]'s ceiling stated in the same paragraph (better observable, not
quantum advantage). Line ~80 already lists two-boson interference among the three
observables built to reach past phase-free, so this is continuous with the text,
softens no negative, and pre-empts the referee asking why the null is the whole
story.

## Dependency

- [[TASK-0130]] (Done) — provably phase-free at convergence; why the converged
  arm cannot answer this.
- [[TASK-0119]] (Done) — `min_adequate_t_max`, the principled clock to use.
- [[TASK-0157]] (Done) — the cross-term derivation, the citations, the ceiling.
- [[TASK-0350]] (Done) — the converged null and the 46%/38% finite-T instability.
- Cohort reconciliation (276 vs 399 families) — blocking for the comparison, not
  for the implementation.

## Open Questions

- Can a physical pre-registration of the sign actually be written, or does the
  unsigned form become primary? Answer in this file before scoring.
- Which cohort. Reviewer's recommendation: ours (276 families), because every
  other arm in this register is already scored on it and the external arms are
  cheaper to re-score than our full history is.
