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
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
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

- [ ] Implement `c_j(t)` computation over a stated, justified time window.
- [ ] Define and justify a frequency-domain coupling score.
- [ ] Synthetic falsification gate before real data.
- [ ] Score all 3 mandatory targets vs. the proximity floor, with CIs
      and a permutation null.
- [ ] Report the result, whichever way it comes out.

## Dependency

- [[TASK-0094]] (Done) — proximity floor.
- [[TASK-0103]] (Done) — dumbbell falsification gate.
- [[TASK-0112]] (Done) — bootstrap CI.

## Open Questions

- Exact frequency-domain scoring definition (total spectral power vs.
  peak-counting vs. something else) — not pre-decided; Implementer's
  call, state the choice and why in Done.
- Time window / sampling rate — state the choice; report sensitivity if
  it materially changes the verdict.

## Done

(not yet)
