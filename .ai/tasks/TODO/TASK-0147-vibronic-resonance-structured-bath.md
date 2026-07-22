# TASK-0147 Structured-bath / vibronic resonance transport (ANM normal modes as the phonon bath)

## Context

- ID: TASK-0147
- Title: `haken_strobl` (this project's existing ENAQT machinery,
  [[TASK-0041]]/[[TASK-0141]]) implements the simplest possible open-
  system model — Markovian, unstructured, pure dephasing at a single
  rate `gamma`. Real quantum-biology literature on vibronic coherence in
  photosynthetic light-harvesting (e.g. Christensson, Kauffmann,
  Pullerits & Mancal 2012, and the broader vibronic-coupling literature
  this cites) uses a *structured* bath, where specific vibrational modes
  resonantly couple to site-energy gaps and can enhance transport to a
  *specific* site rather than uniformly de-trapping the walker. This
  project already has the natural bath candidate sitting unused: the
  ANM's own normal modes (already computed for the learnability gate,
  [[TASK-0120]]/[[TASK-0133]]).
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: raised by the orchestrating user, 2026-07-20, as an open
  "what's still worth trying" question. This Architect/Planner thread's
  own assessment: the most quantum-biology-grounded of the remaining
  ideas, but also the highest implementation cost — flagged explicitly,
  not hidden, per the user's own explicit "file all 4, it won't hurt to
  try" instruction overriding this thread's own lower initial priority
  call.
- Priority: **P2 — real, but expect this to be the slowest of the four
  in this batch to land.** A Redfield/HEOM-level (or a justified,
  simplified secular/rate-based) open-system treatment is a genuine step
  up in complexity from `haken_strobl`'s existing Lindblad machinery. A
  partial or incomplete result, honestly reported as such, is an
  acceptable outcome given the effort involved — do not let this task
  block [[TASK-0145]]/[[TASK-0146]]/[[TASK-0148]], which are cheaper and
  independent.

## Intent Contract

- Outcome: a mode-resolved (not flat-rate) dephasing/relaxation model
  where each ANM normal mode `k` (frequency `omega_k`, already available
  from the existing ANM/GNM eigendecomposition) contributes a coupling
  term between residues `i`/`j` proportional to that mode's own
  displacement between them (state the exact coupling-strength
  definition chosen — e.g. proportional to the mode eigenvector's
  relative displacement magnitude at `i` vs. `j` — and justify it against
  the cited literature's own vibronic-coupling formulation, not invented
  from scratch without grounding). Build the resulting structured-bath
  master equation (full Redfield, or a stated, justified simplification
  such as a secular/rate-only approximation if full Redfield proves
  intractable in the time available — state which was built and why).
- Why required, not assumed: `haken_strobl`'s existing negative finding
  (ENAQT enhances transport but not discrimination, [[TASK-0141]]) was
  established under the *simplest possible* environment model. Whether a
  physically richer, mode-resolved environment changes that conclusion
  — by creating a resonance condition that favors a *specific* site
  rather than uniformly relaxing toward classical diffusion — is a
  genuinely different physical question, not yet asked.
- In Scope:
  - Define and justify the mode-resolved coupling model, citing the
    literature it's grounded in.
  - Build the structured-bath evolution (full Redfield or a stated,
    justified simplification).
  - Synthetic falsification gate first (does a constructed resonance
    condition actually produce a site-specific transport enhancement on
    a toy case, before trusting real data).
  - If time allows: score against real targets, the proximity floor,
    with CIs and a permutation null, same discipline as every other
    observable in the register.
- Out Of Scope:
  - A full ab initio vibrational treatment (real phonon spectral
    densities from MD or DFT) — explicitly out per this project's own
    no-classical-MD constraint (challenge Constraint 3) and this task's
    own scope; the ANM's own normal modes are the stated, justified
    proxy.
  - Reselecting the submission operator (Tier-2-gated, [[TASK-0100]]).
- Constraints And Invariants: state every modeling simplification
  explicitly in Done, with the reasoning — this task is expected to
  require real judgment calls under time pressure, and this project's
  own convention is to state Implementer's-call decisions with reasoning,
  not just the choice.
- Planned Validation: the synthetic falsification gate is the minimum
  bar; real-target scoring is a stretch goal, not a requirement, given
  this task's own stated effort/priority.

## In Progress

None

## TODO

- [ ] Define and justify the mode-resolved vibronic coupling model,
      citing the literature it's grounded in.
- [ ] Build the structured-bath evolution (full Redfield or a stated,
      justified simplification).
- [ ] Synthetic falsification gate: does a constructed resonance
      condition produce site-specific enhancement on a toy case?
- [ ] If time allows: real-target scoring vs. the proximity floor, CIs,
      permutation null.
- [ ] Report the result — including a partial/incomplete one, honestly
      labeled as such — whichever way it comes out.

## Dependency

- [[TASK-0041]] (Done) — existing Haken-Strobl machinery, reused as the
  starting point.
- [[TASK-0141]] (Done) — the simple-bath negative result this task
  tests against a richer model.
- Reuses ANM mode machinery already built for [[TASK-0120]]/[[TASK-0133]].
- Independent of [[TASK-0145]]/[[TASK-0146]]/[[TASK-0148]] — no shared
  blocking in either direction.

## Open Questions

- Full Redfield vs. a simplified secular/rate-based approximation — not
  pre-decided; Implementer's call under real time constraints, state the
  choice and why in Done.
- Exact vibronic coupling-strength formula — state the choice and its
  literature grounding explicitly.

## Done

(not yet)
