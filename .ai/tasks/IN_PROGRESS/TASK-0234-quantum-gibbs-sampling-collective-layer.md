# TASK-0234 Quantum Gibbs/Boltzmann sampling over collective conformer space — named and scoped, not built

## Context

- ID: TASK-0234
- Title: a third quantum-algorithm hypothesis for this program, distinct
  from QUBO energy minimization and Montanaro backtracking search —
  quantum-enhanced sampling of the Boltzmann distribution over
  *collective* (low-ANM-mode) conformer space.
- Status: In Progress
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: [[TASK-0233]]'s own graduation condition (per Architect's
  [[Q-0005]] answer): file this subtask only once a calibrated ΔG
  estimate shows the target quantity is plausible (few kT) — met, for
  the collective layer, on all 3 real targets ([[TASK-0233]]'s own Done
  section: 0.20–2.32 "thermal units," `exp(−ΔG)`=0.10–0.82).
- Priority: P2 — a hypothesis to record and scope, matching
  [[TASK-0229]]'s own family pattern; explicitly not to build or cost
  until further notice, per this task's own In Scope.

## Why this is scoped to the collective layer only, not the whole problem

[[TASK-0233]]'s own ΔG estimate is a **lower bound** — it covers only the
k=50 soft-mode-projected part of the true apo→holo displacement (77–95%
of it, target-dependent), not the local/side-chain residual [[TASK-0230]]'s
own real all-atom pipeline found genuinely difficult (severe steric
clash under naive placement, energy minimization returning to the closed
state). This task's own hypothesis is scoped to exactly what the
evidence supports — the collective/global component — not a claim that
the full local+collective transition is now shown affordable. Filing a
register-wide "this solves cryptic pocket discovery" claim on partial
evidence would repeat the failure mode the Architect's own answer warned
against (`REFERENCES.md` ref [4]'s takeaway, [[TASK-0229.006]]'s own
"do not claim advantage" constraint) — this task deliberately does not
do that.

## Intent Contract

- Outcome: the hypothesis is stated precisely enough that a future
  session can evaluate or build it without re-deriving the physical
  grounding, and its own limits are stated up front, not discovered
  later.
- Why required, not assumed: two independent, real-target lines of
  evidence now support treating the collective layer as "not rare" —
  [[TASK-0233]]'s own ΔG/Boltzmann estimate (this task's own direct
  source) and [[TASK-0228]]'s own independently-measured progress
  probability `p` (0.237–0.492 on all 3 targets, a different method,
  same conclusion) — worth recording as a real forward proposal, not
  worth building blind.
- In Scope:
  - State the hypothesis: a continuous-time or discrete-time quantum
    walk over collective-conformer microstates (points in the low-ANM-
    mode subspace), biased toward the Boltzmann distribution
    `exp(-E(x)/kT)` this task's own harmonic energy already defines,
    could offer a quadratically faster *mixing time* to reach/sample a
    holo-like minor conformer than classical Metropolis/Gibbs sampling
    — citing the real, existing quantum-Gibbs-sampling literature (not
    yet DOI-verified, see Open Questions) rather than an invented
    mechanism.
  - State why it is better-typed than the register's other two quantum
    proposals for this specific sub-problem: QUBO minimization
    (mistyped per the source document's own §6.1, now directly
    confirmed real-target by [[TASK-0230]] Addendum 2 — minimizing
    finds the closed state, not the rare open one) asks for the wrong
    extremum; Montanaro backtracking search ([[TASK-0228]]'s own
    proposal) assumes a tree/graph search structure rather than an
    equilibrium-sampling one — sampling is the type-correct operation
    for "how rare is this state," which is literally the question
    [[TASK-0233]] answers.
  - State the connection to this program's own existing CTQW investment
    (a walk is already this program's central quantum primitive) as a
    reason this is worth naming even before building.
  - State limits as sharply as the register's other quantum sections do
    (matching e.g. [[TASK-0228]] §8.3's own pattern): quadratic, not
    exponential, speedup at best; requires an efficiently preparable/
    queryable oracle over the collective-mode microstate space; only
    covers the collective layer, per this task's own scope note above;
    mixing-time speedups for Gibbs sampling are themselves an active,
    not fully settled, area — cite real limitations, not just promise.
- Out Of Scope:
  - Building or simulating the walk. Costing qubit/gate counts. Any
    claim of quantum advantage. All explicitly deferred — this task
    names and scopes only.
  - The local-residual cost estimate ([[TASK-0233]]'s own flagged next
    step) — a prerequisite for ever extending this hypothesis beyond the
    collective layer, not part of this task's own claim.
- Constraints And Invariants: every physical claim here must cite either
  this project's own already-computed numbers ([[TASK-0227]]/[[TASK-0230]]/
  [[TASK-0233]]/[[TASK-0228]]) or a DOI-verified paper, per
  `.ai/reference/PAPER_CITATION_PROTOCOL.md` — no claim from memory
  presented as checked.
- Planned Validation: N/A for a naming/scoping task — the real
  falsification test is downstream, once/if this is ever built:
  measured mixing-time advantage against a real classical Gibbs/
  Metropolis baseline on the same collective-mode energy landscape.

## Open Questions

- Real citations for quantum Gibbs/Boltzmann sampling / quantum walks on
  Markov chains (e.g. the Temme et al. quantum Metropolis line, or more
  recent quantum Gibbs-sampler results) are not yet DOI-verified against
  this project's own citation protocol — required before this task's own
  In Scope items can be written up with real references rather than
  recalled ones.
- Does [[TASK-0233]]'s own local-residual follow-up (if it happens) change
  whether this hypothesis should stay collective-only-scoped, or could it
  extend to the joint layer once that number exists?

## Done

(not yet)
