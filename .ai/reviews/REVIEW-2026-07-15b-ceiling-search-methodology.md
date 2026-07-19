# Ceiling-search methodology audit (follow-up to REVIEW-2026-07-15)

## Reviewer

Architect/Planner thread (Critic overlay), 2026-07-15, same day, per
explicit user direction to continue the gap audit against newly-landed
concurrent work. Read `ceiling.py`, `scripts/ceiling_search_batched.py`,
`test_ceiling.py`, and TASK-0046's Done record in full; ran no new code
(read-only pass, consistent with the first audit's method).

## Linked Docs

- `.ai/reviews/REVIEW-2026-07-15-execution-plan-gap-audit.md` (part 1)
- `.ai/tasks/DONE/TASK-0046-ceiling-coordinate-descent-search.md`
- `__WORK_IN_PROGRESS__/src/allostery/ceiling.py`
- `__WORK_IN_PROGRESS__/scripts/ceiling_search_batched.py`

## Scope

TASK-0046 (Done) and its batched-runner follow-up landed since the first
audit pass. Its real KRAS_G12C finding — "even with 60 trials of the
answer key, actively optimizing for pocket AUC, the ceiling does not
clear chance... very little headroom in this operator family" — is
flagged by TASK-0046's own Done section as the number TASK-0082
(competence map, the submission's central claim) should read directly.
A negative/null claim this load-bearing warrants the same scrutiny
Phase 1B already applied to the positive claims.

## Findings

### New — not tracked anywhere before this pass

**1. Ceiling search coverage is too sparse to support a "no headroom" claim. (High)**

`ceiling.sample_params` draws over 7 continuous dimensions
(`lam_B, lam_T, lam_R, lam_C, lam_M, alpha, cutoff`) plus one 5-way
categorical (`n_low`) — an ~8-dimensional space — via **N=60 blind
random draws** (`ceiling.py:175-249`, `n_trials: int = 60`). TASK-0046's
own Done section confirms this is genuinely blind random search, not
coordinate descent despite the notebook's section title. 60 samples in
an 8-dimensional continuous space is sparse coverage by any space-filling
standard — even a coarse 2-level grid over 8 dimensions needs 256 points
to touch every corner once. A **negative** claim ("there is very little
headroom... floor-clearing or not") requires *strong* evidence of having
searched the space; N=60 blind random search is weak evidence for a null
result, though it would be perfectly adequate evidence for a *positive*
finding (a single lucky trial clearing the floor is real regardless of
how the rest of the space looks).

**Correction, 2026-07-18/19 ([[TASK-0131]])**: the last clause above
("a single lucky trial clearing the floor is real regardless of how the
rest of the space looks") is right for an *existence* claim — does any
point in the search space score highly against the real label — but
wrong for the statistic this project actually reports. `COMPETENCE_MAP.md`
does not report "does any of the 60 trials clear the floor" as a yes/no
existence check; it reports the **maximum** AUC over those 60 trials as
"the ceiling," and reads `ceiling − floor > 0` as evidence of real
headroom. A maximum over K noisy draws is upward-biased by construction
(the winner's curse / look-elsewhere effect) — a single trial "clearing
the floor" is exactly what pure noise, given 60 independent tries,
produces some of the time even with zero real signal in the operator
family. TASK-0131 measured this directly: a 200-replicate permutation
null (identical 60-trial search protocol, permuted pocket labels, same
pocket size) on all 3 mandatory targets — see that task's own Done
section and `COMPETENCE_MAP.md`'s newest SUPERSEDED layer for the real
null distributions and where each target's real margin falls within
them. This correction does not retract Finding 1's own headline claim
(sparse 8-D coverage is still weak evidence either direction) — it
retracts only the specific "a lucky positive trial needs no further
scrutiny" argument, which turns out to need exactly the scrutiny this
finding already argued for on the negative side, just applied
symmetrically.

Compounding this: `TASK-0110` (filed same day, TODO) brings a real
optimizer (Optuna/TPE) into this pipeline — but explicitly scoped to
CTQW's *numerical* parameters (`t_max`/`n_steps`/`gamma`), with
`H_new`'s physical potential-weight parameters named as **out of scope**
("already covered by TASK-0046"). Nobody is currently applying a
real optimizer, or even a space-filling design (Sobol/Latin hypercube),
to the exact parameter space TASK-0046's near-chance conclusion rests
on. Filed as **TASK-0116**.

**2. The ceiling number itself uses the same unvalidated `t_max`/`n_steps`. (High)**

`ceiling.consistency_score` defaults to `t_max=15.0, n_steps=500`
(`ceiling.py:97-98`), identical to every other call site TASK-0108's
Crit Ref already names as unvalidated. TASK-0046's real KRAS_G12C
cross-check ran all 60 trials at these fixed values on N=169 residues.
If TASK-0109's forthcoming convergence check finds `t_max=15`/
`n_steps=500` inadequate at this system size, the ceiling claim itself
is undermined, not just the already-flagged default/optimized headline
AUCs — a converged evaluation might surface headroom the current run
structurally cannot see. TASK-0046's own record and `TASK-0082`'s
planned consumption of this number both currently treat "0.5250,
near-chance" as settled; it is a point estimate (no CI either — same
gap as `TASK-0112`) computed on physics of unconfirmed validity. Filed
as **TASK-0117**, explicitly cross-linked as a consumer of TASK-0109's
convergence check once it lands.

## Notable good practice observed

- `ceiling_search_batched.py`'s RNG fast-forward (replaying
  `sample_params(rng)` draws for already-checkpointed trials without
  recomputing physics) is a careful, correct way to keep a resumed run
  bit-identical to a single non-batched call — verified by reading the
  logic, not just trusting the docstring's claim.
- TASK-0046's Done section already distinguishes its own finding from
  TASK-0093's ("this task shows the *ceiling*... is itself near chance;
  TASK-0093 showed the *default*-parameter AUC is proximity-correlated")
  — the kind of precise claim-scoping this audit keeps finding well
  done elsewhere in the project, which is why the two gaps above are
  worth closing rather than a symptom of sloppiness.

## Status

Two new High-severity gaps filed (TASK-0116, TASK-0117), both attached
to an already-Done task whose negative finding is scheduled to anchor
the submission's central competence-map claim (TASK-0082). Neither
finding retracts TASK-0046's number — same posture as the first audit
pass: the claim needs stronger evidence before TASK-0082 treats it as
final, not a correction to the work already done.
