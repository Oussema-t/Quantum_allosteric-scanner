# TASK-0146 Frequency-domain / spectral coherence observable (un-averaged coherent oscillation between seed and candidate residues)

## Context

- ID: TASK-0146
- Title: every propagator this project has scored on real data
  (`time_averaged_ctqw`, `ground_state_relaxation`, `haken_strobl`'s
  ENAQT sweep) explicitly time-averages away phase information —
  `time_averaged_ctqw_converged` (TASK-0130) is *provably* phase-free at
  the converged limit. This task deliberately does the opposite: analyze
  the *un-averaged* coherent oscillation amplitude
  `c_j(t) = <j| exp(-iHt) |source>` between the seed and each candidate
  residue `j`, in the frequency domain, to test whether the frequency
  content of quantum beating (dominated by Bohr frequencies `w_k - w_l`
  where both source and `j` have amplitude on modes `k` and `l`) carries
  coupling information the time-averaged occupation destroys.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer B (this thread)
- Claimed At: 2026-07-24 14:55
- Source: raised by the orchestrating user, 2026-07-20, as an open
  "what's still worth trying" question.
- Priority: **P2.** Genuinely novel angle (nothing else in the register
  looks at un-averaged phase/frequency content), but this Architect/
  Planner thread's own prior estimate is lower plausibility than
  [[TASK-0145]] — no structural argument for proximity-orthogonality,
  just a different observable built on the same underlying dynamics.

## Intent Contract

- Outcome: for each mandatory target, compute `c_j(t)` over a
  physically-relevant time window (state the window and sampling choice
  — e.g. long enough to resolve the smallest relevant Bohr frequency,
  short enough to stay in a tractable `n_steps`; reuse
  `propagators.min_adequate_n_steps`-style reasoning rather than picking
  an arbitrary window), Fourier-transform it, and define a per-residue
  coupling score from the resulting spectrum — e.g. total spectral power
  at resolved peaks, or the number/strength of distinct resolved
  frequencies shared between source and `j`. State the exact scoring
  definition chosen (this is a real design decision, not obvious from
  the physics alone) and why.
- Why required, not assumed: this is the first observable in the
  register that explicitly preserves phase/frequency information rather
  than averaging or Hodge-decomposing it away. Whether that information
  is informative about pocket location, or just another window onto the
  same graph-distance structure everything else has hit, is untested.
- In Scope:
  - Implement the amplitude computation (reuse the existing `eigh`-based
    propagator machinery — no new Hamiltonian construction needed, this
    is a new *readout*, not a new operator).
  - Define and justify the frequency-domain scoring function.
  - Synthetic falsification gate first (e.g. the dumbbell construction,
    [[TASK-0103]] — does the spectral score track coupling, not the
    well, before trusting real data).
  - Score against all 3 mandatory targets, [[TASK-0094]]'s proximity
    floor, with CIs ([[TASK-0112]]) and a permutation null on any
    max-over-frequency-bins step.
- Out Of Scope:
  - Reselecting the submission operator (Tier-2-gated, [[TASK-0100]]).
  - Any dephasing/open-system extension — this task is about the closed
    (unitary), un-averaged dynamics specifically; ENAQT is already
    covered by [[TASK-0141]].
- Constraints And Invariants: the time window and sampling rate are
  fixed once, stated, and blind to labels — do not tune them per target
  to improve the score.
- Planned Validation: the dumbbell gate first; then real-target scoring,
  reported whichever way it comes out.

## In Progress

None

## TODO

- [x] Implement `c_j(t)` computation over a stated, justified time window.
- [x] Define and justify a frequency-domain coupling score.
- [x] Synthetic falsification gate before real data.
- [x] Score all 3 mandatory targets vs. the proximity floor, with CIs
      and a permutation null.
- [x] Report the result, whichever way it comes out.

## Dependency

- [[TASK-0094]] (Done) — proximity floor.
- [[TASK-0103]] (Done) — dumbbell falsification gate.
- [[TASK-0112]] (Done) — bootstrap CI.

## Open Questions

- Exact frequency-domain scoring definition (total spectral power vs.
  peak-counting vs. something else) — not pre-decided; Implementer's
  call, state the choice and why in Done.
  **Answered**: total AC (non-DC) spectral power of the occupation
  trajectory `p_j(t)=|c_j(t)|^2`, not peak-counting (avoids peak-
  counting's own unjustified detection-threshold parameter) and not the
  raw complex amplitude (whose spectrum has no Bohr-frequency cross
  terms — see Done section). Equals `Var_t[p_j(t)]` exactly by Parseval,
  confirmed as a numerical identity in the test suite.
- Time window / sampling rate — state the choice; report sensitivity if
  it materially changes the verdict.
  **Answered**: `T=5000` (angular-time units, `H_new`'s own scale),
  `n_steps` via the existing `min_adequate_n_steps(H, t_max=T)`. Chosen
  from real Bohr-gap statistics, not arbitrarily; sensitivity checked
  directly and does materially change the verdict at the shipped
  `t_max=15` default (see Done section) — `T=5000` is the reasoned
  choice, `t_max=15` is confirmed inadequate, not merely different.

## Done

**2026-07-24, Implementer B.** Built and executed as scoped: implementation,
synthetic gate, real-target run, all reported per this task's own Planned
Validation ("reported whichever way it comes out").

**New `src/allostery/spectral_coherence.py`**: `amplitude_trajectories`
(coherent `c_j(t)=<j|exp(-iHt)|source>` sampled uniformly on `[0,t_max)`,
reusing the existing `eigh`-based evolution machinery — no new Hamiltonian
construction) and `spectral_coherence_score` (the per-residue coupling
score). 12 new unit tests (`tests/test_spectral_coherence.py`): unitarity,
t=0 delta-state, disconnected-node exact zero, the Parseval `Var_t[p_j(t)]`
identity (a real correctness guard, not just asserted from the derivation
in the module docstring), n_steps-invariance, and a DC-exclusion sanity
check against `time_averaged_ctqw_converged` on the same `H`.

**Two design decisions, made and justified (this task's own explicit
instruction, "state the exact scoring definition chosen... this is a real
design decision")**:
1. Fourier-analyze `p_j(t)=|c_j(t)|^2` (occupation), not the raw complex
   amplitude `c_j(t)` itself — the task's own physics description ("Bohr
   frequencies `w_k-w_l`") only holds for the probability's cross terms;
   the raw amplitude's spectrum has single frequencies `w_k` only, not
   `w_k-w_l` differences.
2. Score = total AC (non-DC) spectral power, not peak-counting. The DC bin
   is exactly `time_averaged_ctqw_converged`'s own already-scored quantity
   (verified: excluding it is the entire point of a genuinely new
   observable). Peak-counting was considered and rejected — it needs an
   extra, unjustified peak-detection threshold this scoring doesn't.

**Time window, real-data-calibrated (not picked arbitrarily)**: the task's
own suggested "resolve the smallest relevant Bohr frequency" criterion is,
taken literally, TASK-0110's own already-documented infeasibility (full
`t_max` 145,000x-3,950,000x the shipped default). Checked real gap
statistics on `H_new` before choosing anything (median gap 0.0015-0.0062
across the 3 mandatory targets, smallest gap 3-4 orders of magnitude
below that). Fixed `T=5000` — `min_adequate_n_steps(H, t_max=5000)` stays
in the low thousands on every target (checked: ~3980 on CARDIAC_MYOSIN,
the densest spectrum). Resolves 94.6%/76.0%/55.8% of real gaps on
KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN — reported honestly, CARDIAC_MYOSIN is
the real limiting case.

**Sensitivity check, real and material**: at the shipped `t_max=15`
default, KRAS_G12C's own floor-clearing verdict *flips* relative to
`T=5000` (0.327 below floor vs. 0.633 above). `T=5000` vs. a 10x-larger
`T=50000` agree closely on all 3 targets (differences <=0.005 AUC) --
`T=5000` has converged, `t_max=15` is confirmed inadequate exactly as the
module's own gap-resolution calibration predicted.

**Synthetic dumbbell falsification gate** (`tests/test_dumbbell_negative_
control.py::TestSpectralCoherenceDumbbellGate`, 5 tests): clean, decisive
double dissociation against GSR on the conflict cells (C2=1.000, C3=0.000,
exact across every seed, n_seeds=20). C1=0.083 -- the same well-agrees-
but-anti-intuitive resonance sensitivity this file's other spectral/mode-
based gates (`mode_coparticipation`, `T(E)`) already documented on this
identical construction, not asserted directionally for the same reason.
C4=0.504, near chance.

**Real-target result: no decisive positive, real negative with a
mechanism** (`scripts/spectral_coherence_real_run.py`, `H_new`, full
active-site array per TASK-0118's GAUGE convention):

| Target | Whole-graph AUC | Floor | CI overlap | Well-powered max AUC | p (uncorrected) | rho(score,-hop) |
|---|---|---|---|---|---|---|
| KRAS_G12C | 0.633 | 0.482 | True | 0.792 | 0.103 | +0.70 |
| BCR_ABL1 | 0.576 | 0.582 | True | 0.851 | 0.034 | +0.72 |
| CARDIAC_MYOSIN | 0.584 | 0.568 | True | 0.752 | 0.106 | +0.68 |

No target reaches a decisive result (CI overlap `True` everywhere; no
well-powered stratified max clears the 3-target Bonferroni bar,
alpha=0.0167 -- BCR_ABL1's own p=0.034 is the closest, uncorrected-
significant only). **Mechanism identified, not just observed**: rho(score,
-hop) is +0.68 to +0.72 on every target -- the same sign and comparable
magnitude to a confounded observable's own reference (CTQW-occ's
synthetic rho~=+0.71 to +1.0, TASK-0149's own table). This task's own
Priority note flagged exactly this risk in advance ("no structural
argument for proximity-orthogonality... just a different observable
built on the same underlying dynamics") -- confirmed empirically, not
merely repeated. The whole-graph "clears floor" readings on KRAS_G12C/
CARDIAC_MYOSIN are best explained by this confirmed proximity
correlation, not genuine distal coupling -- consistent with, not
contradicted by, the stratified lens finding nothing significant.

**Full test suite**: 941 passed, 2 xfailed, 0 failed.

Full detail: `RESULTS.md`'s "Frequency-domain / spectral coherence
observable" section, open-questions row 36,
`results/tasks/0146_spectral_coherence/spectral_coherence_real_run.json`.
