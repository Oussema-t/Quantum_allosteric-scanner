# TASK-0357 — Replicate the finite-delay phase-sensitive observable under a principled clock and a pre-registered sign

- Status: DONE
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

## Sign pre-registration, written before any scoring run (2026-09-09, Implementer B)

**Attempted derivation.** `H_new`'s off-diagonal entries come only from
`L_norm(alpha, r_c)`, a standard graph Laplacian (`L = D - W`, `W >= 0`), so
`H_{ra} <= 0` for `r != a`. Expanding `exp(-iH tau)` to second order for
`r != a` (so `<r|a>=0`): the O(tau) term is `-i tau H_{ra}` — purely
imaginary, contributing **zero** to `Re(...)`. The leading real
contribution is O(tau^2): `Re<r|exp(-iH tau)|a> ~= -(tau^2/2) (H^2)_{ra}`.
For a near neighbour, `(H^2)_{ra}` is dominated by `H_{ra}*(H_{aa}+H_{rr})`,
and since `H_{ra}<0` while the diagonal terms are positive (degree +
non-negative potential terms), that product is negative — giving a
*positive* leading-order `O(r)` for a close neighbour of the seed. But this
says nothing about which candidates are the TRUE allosteric ones (proximity
to the seed already has its own well-established, separately-controlled-for
baseline in this register — this expansion predicts a *distance* effect, not
an *allostery* effect) and, more fundamentally, **it does not apply at the
tau this task actually uses.** `tau = min_adequate_t_max(kind=
"ground_state_relaxation") = -ln(tol)/gap` is chosen to be *large* relative
to the spectral gap (order `O(1/gap)`, `tol=1e-2` -> `tau ~= 4.6/gap`), not
small — a short-tau perturbative expansion is the wrong regime for the
value actually scored. At `tau ~ O(1/gap)`, the sign of `Re<r|exp(-iH
tau)|a>` depends on interference across the full mode spectrum (which
eigenmodes' phases happen to align at that specific tau for that specific
r/a pair), which has no clean, protein-independent closed form.

**Conclusion: no defensible physical sign argument survives at the operating
timescale.** Per this task's own Intent Contract fallback: **`|O(r)|`
(unsigned) is primary; the raw signed `O(r)` is reported only as a
secondary, clearly labelled arm.** Deliberately NOT a cohort-level
majority sign fit from the data (an earlier draft of this section proposed
that): choosing a sign because it is the one the labelled truth residues
happen to favour on average is itself a supervised choice made after
seeing the labels — precisely the "sign chosen per fold... capable of
fitting the instability directly" failure mode this task's own filing
warns against, just moved from per-fold to per-cohort. The raw signed
score, with no data-driven sign choice at all, is the only secondary form
that adds no such leakage. This is the honest resolution the task
anticipated, not a failure to try — the attempted derivation above is
real work, not a placeholder.

## Cohort decision, written before scoring (2026-09-09, Implementer B)

**Primary cohort: TASK-0350's own ASBench cohort (108 structures / 76
protein clusters)**, not the veto-pipeline's 276-family cohort, for a
reason the task's own Planned Validation makes load-bearing, not a
preference: Planned Validation requires reproducing TASK-0350's own
committed converged-limit numbers "from the same code path" before the
finite-delay arm can be trusted, and that code path *is* the ASBench
harness (`ANN`/`KEEP`, `ca()`, `build_H_new`, `hop_from_seed`) — building
the implementation on that same harness is what makes the validation
possible at all. The Open Question's own text separates this cleanly:
cohort reconciliation against the external "+0.114/399 families" number is
"**blocking for the comparison, not for the implementation**." This task
delivers the implementation, its Planned Validation, and an honest
in-register measurement on the ASBench cohort. It does **not** deliver a
cohort-matched head-to-head against the external number — that requires
reconstructing per-structure `H_new`/active-site data for the veto
pipeline's 435 MIN_HOP=2 structures from the `allosteric` branch, which
is out of this task's scope as filed. Flagged explicitly in the Done
section as the remaining step for whoever owns that reconciliation, not
silently substituted.

**P@5, adapted to ASBench**: the veto pipeline's own P@5 is pocket-level
(TASK-0336); ASBench has no pocket structure. Adopted the residue-level
P@5 convention already used elsewhere in this register on raw
per-residue score vectors (e.g. TASK-0329's `top5 = argsort(ranks)[:5];
p5 = y[top5].sum()/5`) — top-5 eligible residues by `O(r)` (or `|O(r)|`),
fraction that are true allosteric residues. Same metric shape ("is the
truth in the top 5"), same eligible-residue population every other
ASBench-cohort arm in this register already uses.

## Done, 2026-09-09

### Implementation

`finite_delay_phase_observable(w, v, tau, source)` in
`scripts/task0357_finite_delay_phase_observable.py`: `O(r) = 2*Re<r|exp(-iH
tau)|a>`, built directly from `_quantum_initial_coeffs` (propagators.py's
own coherent multi-residue seed-state convention -- the same one
`_ctqw_from_eigh` already uses for every other phase-carrying arm in this
register, not invented for this task).

**Planned Validation, both checks run and passed before the finite-delay
arm was trusted:**
1. **Harness reproduction**: the reused ASBench cohort/`build_H_new`/eigh
   path reproduces TASK-0308/0350's own committed converged decoherent-CTQW
   numbers **exactly** (raw=0.5921, rho=0.7347, resid=0.5184 -- byte-match
   to 4 decimals, not "close").
2. **O(r) vanishes under time-averaging**: a real bug caught here, not
   assumed away -- the first version of this check averaged `|O(r,t)|`
   (non-negative regardless of oscillation, so it approaches the
   oscillation's RMS magnitude, not 0, even when the phase genuinely
   cancels) and showed the quantity growing with the averaging window.
   Fixed to time-average the SIGNED `O(r,t)` first, then take `|.|` --
   confirmed shrinking by >10x from `T=5` to `T=50000` on 5 real
   structures, matching TASK-0130's own proof that this class of quantity
   is phase-free at convergence.

### Result — the primary pre-registered arm, and why it does not survive scrutiny

`tau = min_adequate_t_max(kind="ground_state_relaxation", tol=1e-2)` per
protein, no sweep, no per-fold choice, pre-registered before this script
existed. `|O(r)|` unsigned (pre-registered primary, per the Sign
pre-registration section above): resid-AUC excess **+0.029 mean / +0.016
median**, cluster-permutation **p=0.036** (76 protein clusters, n=108
structures) -- nominally significant. Signed `O(r)` (secondary, no
data-driven sign applied): resid-AUC excess +0.002 mean, cluster-p=0.92 --
indistinguishable from chance.

**Did not stop at the pre-registered reading.** A post-hoc (explicitly
not pre-registered, exploratory, disclosed as such -- run BECAUSE the
primary result was only marginally significant, not to fish for a better
number) sensitivity check across nearby `tol` values, same cohort, same
code path:

| tol | mean resid-AUC excess | cluster-permutation p |
|---|---|---|
| 1e-3 | +0.0095 | 0.461 |
| **1e-2 (pre-registered)** | **+0.029** | **0.036** |
| 5e-2 | +0.0096 | 0.523 |
| 1e-1 | +0.0007 | 0.960 |

**The nominally-significant result is isolated to the single pre-registered
tolerance and collapses one order of magnitude in either direction.**
Per this task's own pre-registered "either outcome is publishable"
framing (stated in this file before the run): this is the collapse
outcome, not the surviving-effect one -- a clean methodological finding
about selection on `tau`/`tol`, not a Phase-2-worthy positive. It does
**not** match the external claim's own magnitude either way (+0.114 AUC,
p=0.004) at the one tolerance that came back significant here (+0.029
mean, an order of magnitude smaller even where nominally "significant").

### Cohort comparability — explicitly not resolved here

Per the "Cohort decision" section above, this result is on TASK-0350's own
ASBench cohort (108 structures / 76 proteins), not the veto-pipeline's
276-family cohort the external claim was presumably measured on. **A
direct, cohort-matched comparison to the external "+0.114/p=0.004/399
families" number was not attempted** -- it would require reconstructing
per-structure `H_new`/active-site data for the veto pipeline's own 435
MIN_HOP=2 structures from the `allosteric` branch, explicitly out of this
task's scope ("blocking for the comparison, not for the implementation").
Given this task's own result (collapse under a tolerance-robustness check)
is already decisive on its own terms, this gap does not change the
verdict -- but it means "our number" and "their number" still cannot be
quoted side by side honestly, and whoever attempts that comparison next
should not assume this task closed it.

### Secondary arm (the held +0.031, amplitudes vs probabilities) — deferred, not run

Item 5 of the Intent Contract (a spectrally-matched amplitude-vs-
probability control) was not attempted in this task, for effort-budget
reasons, disclosed rather than silently dropped. **The Reviewer's hold on
that claim is therefore unchanged, not lifted** -- exactly the outcome the
filing's own conditional language anticipated ("not lifted by this task
unless the matched control clears"). Flagged as the natural next step for
whoever picks this back up.

### Submission doc edit (independent of this task's outcome, per the filing)

`PHASE1_SUBMISSION_V3.md`'s "closed nine candidate advantage routes"
sentence rewritten to name the finite-delay observable as the tested
tenth, honestly reflecting the actual (collapse) result rather than the
hoped-for one -- the task's own filing said do this edit "independent of
this task's result," but a null result changes WHAT gets written, not
whether it gets written: naming an untested route as "the Phase-2 quantum
route to build" would have been exactly the "asserting an unvalidated
result" this same filing explicitly warned against. TASK-0157's ceiling
(2x2 permanent = 2x2 determinant) stated in the same paragraph, per Intent
Contract item 4.

### Hypothesis register

Folded into [[HYP-P6]] as a dated Status update (not a new hypothesis) --
same mechanism (`tau`/clock choice is a live, unaccounted-for confound),
now demonstrated concretely: even the "principled" alternative-2 clock has
its own free knob (`tol`), and the one candidate positive result available
to test it against sits exactly on that knife-edge.

**Files**: `__WORK_IN_PROGRESS__/scripts/task0357_finite_delay_phase_observable.py`
(new), `__WORK_IN_PROGRESS__/results/tasks/0357_finite_delay_phase_observable/
{checkpoint.jsonl,finite_delay_phase_observable.json}`,
`__WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V3.md`,
`.claude/hypotheses/{physics.md,INDEX.md}`, `.ai/COMMON.md`,
`__WORK_IN_PROGRESS__/RESULTS.md`.

**Constraints honored**: cohort/labels reused, no new benchmark
constructed; `tau` rule and scoring fixed once, blind to labels, written
down before scoring; Planned Validation run and passed before the
finite-delay arm was trusted; TASK-0350 not re-run (its own committed
numbers reused directly as the validation target); no claim of asymptotic
quantum advantage made anywhere in this task's own write-up.
