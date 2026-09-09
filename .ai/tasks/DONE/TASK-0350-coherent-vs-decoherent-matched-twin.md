# TASK-0350 — Ask the interference question properly: coherent vs decoherent, matched operator, matched seed

- Status: Done
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

## Done

**2026-09-08/09, Implementer A.** No blocker found before pickup (TASK-0348
and all 5 named Related tasks Done; `time_averaged_ctqw_converged`,
`ceiling_search_batched.py`, `ceiling_permutation_null.py`,
`apo_structure_sensitivity_sweep.py` all present and importable). Script:
`task0350_coherent_vs_decoherent.py`, `__WORK_IN_PROGRESS__/scripts/`
(results in `results/tasks/0350_coherent_vs_decoherent_matched_twin/`).

### Cohort and scoring — reused, not re-derived

Per this task's own Constraint: cohort/labels copied (not imported, same
reason [[TASK-0310]] itself gives — avoiding another module's import-time
side effects) from `task0310_family_residualised_on_proximity.py`: the
108-structure ASBench cohort (`asbench_annotations.json` + TASK-0305's
`KEEP` filter), `build_H_new(xyz, bf, cutoff=8.0)`, `hop_from_seed`
proximity, eligibility masking, `score_stats` (raw AUC / rho / rank-
residualised AUC), and `cluster_sign_flip_test_generic` (by-protein,
76 clusters, Monte Carlo sign-flip). No new benchmark introduced.

**Matched classical twin**: `ground_state_relaxation(L, T, source)` where
`L = normalised_laplacian_alpha(xyz, cutoff, alpha)` — this is exactly
`H_new`'s own graph term before any potential is added
(`H_new = L_norm(α,r_c) + V_B+V_T+V_R+V_C+V_M`), genuinely
positive-semidefinite (unlike `H_new` itself), so this really is
classical diffusion on the same graph, not a ground-state-density
artifact — resolves [[HYP-P7]]'s own long-standing "provided H_new is
PSD (which it currently is not)" caveat rather than sidestepping it.

### A real 10+ hour bug, caught and fixed before trusting any result

The first version of this script called `time_averaged_ctqw` (finite-T)
directly for the 4 (coherent × T) combinations per structure, each
redoing a full O(N³) `eigh(H)` — on top of the one already needed for
the converged-limit arms, that is 5 separate decompositions per
structure at this cohort's max N≈3000. Launched in the background,
checked ~10 hours later on a status-update request: still running, no
output (Python's own stdout buffering meant nothing would print until
completion), 0 new PDB fetches (ruled out network stalls), ~21% average
CPU utilization over the elapsed period (consistent with genuine,
if wasteful, compute — not a hang). **Killed rather than left running.**
Fixed by sharing one `eigh(H)` per structure across every arm (the
private `_ctqw_from_eigh`/`_ctqw_mixture_from_eigh` helpers
`time_averaged_ctqw` itself calls, reused directly — numerically
verified identical output on a 5-structure smoke test before and after
the fix) and adding `flush=True` progress logging every 15 structures
so a future stall is diagnosable in minutes, not hours. Real run: 108
structures, full pipeline, **4152s (~69 min)**.

### Planned Validation

`coherent=False` reproduces [[TASK-0308]]'s committed numbers exactly:
raw=0.5921 (committed 0.5921), rho=0.7347 (committed 0.7347),
resid=0.5184 (committed 0.5184).

### Result — the decisive test

| arm | raw AUC | rho(proximity) | resid AUC |
|---|---|---|---|
| classical diffusion (T=15, matched graph Laplacian) | 0.6012 | 0.9531 | 0.4567 |
| decoherent CTQW (converged) | 0.5921 | 0.7347 | 0.5184 |
| coherent CTQW (converged) | 0.5997 | 0.6924 | 0.5207 |

**Per-structure (coherent − decoherent) resid-AUC delta, n=108: mean
+0.0023, median −0.0029, Wilcoxon p=0.919, cluster-robust (76 protein
clusters, Monte Carlo sign-flip) p=0.834.** Pre-registered prediction
("gap is small and non-significant, ≤0.005 AUC") **HOLDS** — decisively,
not marginally; the row-level and cluster-robust p-values are both
indistinguishable from the null. (An earlier 5-structure smoke test had
shown the opposite — small-sample noise, superseded by the full run.)

**Finite-T sensitivity (Constraint, not averaged away): 50/108 (46%)
coherent-arm structures and 41/108 (38%) decoherent-arm structures flip
residualised-AUC sign between T=15 and the converged limit.** Close to
even odds of disagreement — a real, large instability, reported as a
property of the finite-T construction, not smoothed into a mean. This
generalizes TASK-0119's own 3-target finding (10/11 CARDIAC_MYOSIN
floor-clears did not survive a corrected clock) to the full cohort with
an exact per-structure criterion.

### Landed

Folded into two existing hypotheses, both by dated status update (no new
id — same register, same standing rule):
- **[[HYP-P7]]** ("Coherence adds no signal") — the decisive
  coherent-vs-decoherent result, directly confirming and completing that
  hypothesis's own "To formalize" request, and resolving its own stated
  PSD caveat on the classical twin.
- **[[HYP-P6]]** ("Propagation time t is unprincipled") — the finite-T
  instability finding, the same underlying claim as TASK-0119's own
  3-target result, now shown at ~35x the scale.

`INDEX.md` regenerated; `hyp_register_check.py` 18/18 tests pass.

### Not done / explicitly out of scope

- Did not sweep t_max continuously (only T=15 and T=50000 vs. converged)
  — the two points already establish the instability; a continuous sweep
  would refine the picture, not change the verdict.
- Did not re-run the 3-mandatory-target cohort separately — the
  108-structure ASBench cohort is a superset of the same question with
  far more statistical power, per this task's own Constraint to reuse
  the existing cohort.
- Did not update `PHASE1_SUBMISSION_V2` — feeding this into §2 is for
  whoever owns that document's drafting pass.

**Files**: `__WORK_IN_PROGRESS__/scripts/task0350_coherent_vs_decoherent.py`,
`__WORK_IN_PROGRESS__/results/tasks/0350_coherent_vs_decoherent_matched_twin/
{coherent_vs_decoherent.json,run_log.txt}`.
