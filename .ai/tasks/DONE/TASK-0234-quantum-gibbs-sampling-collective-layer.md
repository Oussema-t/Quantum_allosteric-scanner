# TASK-0234 Quantum Gibbs/Boltzmann sampling over collective conformer space — named and scoped, not built

## Context

- ID: TASK-0234
- Title: a third quantum-algorithm hypothesis for this program, distinct
  from QUBO energy minimization and Montanaro backtracking search —
  quantum-enhanced sampling of the Boltzmann distribution over
  *collective* (low-ANM-mode) conformer space.
- Status: Done
- Resolution: done
- Resolution Note: Retired, not built: TASK-0185 (2026-08-02, pre-existing) already found real ANM Boltzmann-ensemble sampling recovers the pocket in 1-8 classical draws -- not rare, fatal to any Grover/sampling-speedup claim, independently reconfirmed by TASK-0228's p and TASK-0233's own Boltzmann weight. Second disqualifier: equipartition_ensemble is closed-form exact Gaussian sampling, no MCMC mixing-time to accelerate. TASK-0204's exact rotamer solver closes the joint layer the same way. Real remaining gap is backbone-modeling fidelity (TASK-0230), not search cost, classical or quantum.
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

**Retiring this hypothesis, not naming/scoping it for later — correcting
this task's own filing.** User's instruction on pickup: check the
[[TASK-0229]] family's own outcomes first. That check surfaced
[[TASK-0185]] (2026-08-02, three weeks before this task was filed) —
already-decisive, already-real-target evidence this task's own filing
did not have in hand. Recording the correction plainly rather than
quietly abandoning the task.

**[[TASK-0185]]'s own already-existing finding disqualifies this
hypothesis at the collective layer, for the exact mechanism it proposed
accelerating.** Real ANM Boltzmann-ensemble sampling
(`allostery.shortcuts.equipartition_ensemble` — the actual classical
version of what this task proposed giving a quantum speedup) on all 3
real targets: real-pocket recovery costs **1–8 classical draws per hit**,
stated in that task's own words: *"a Grover-style backbone-layer
rare-event search argument requires a rare target event, and it is not
rare on any real target measured here."* An n_modes sweep on the
synthetic prototype found the same thing quantitatively (p=0.244–0.694
across n_modes=5/20/40) before it was ever tested on real structures.
**This is now the fourth independent measurement reaching the same
conclusion** — [[TASK-0185]]'s real-ensemble recovery rate (2026-08-02),
its own n_modes sweep, [[TASK-0228]]'s progress probability `p`
(0.237–0.492, 2026-08-21/22), and [[TASK-0233]]'s own harmonic
Boltzmann weight (`exp(−ΔG)`=0.10–0.82, 2026-08-22/23) — four different
methods, spanning three weeks, all agreeing the collective layer is not
rare. This task's own graduation condition ("plausible, few kT") was a
necessary check but not a sufficient one — plausible *and rare* would
motivate a quantum search/sampling speedup; plausible *and common*
(what was actually found, repeatedly) does not, regardless of which
quantum primitive is proposed.

**A second, independent reason this hypothesis fails, found while
correcting the first**: the premise "quantum Gibbs sampling gives a
mixing-time speedup" assumes the classical sampler has a mixing-time
problem to begin with — an iterative, correlated MCMC process with slow
convergence. `equipartition_ensemble` is not that: it is a **closed-form,
exact, one-shot multivariate Gaussian draw** in ANM mode space (the
harmonic approximation's own equilibrium distribution is analytically
known — no burn-in, no autocorrelation, no chain to mix). There is no
mixing-time bottleneck at the collective layer for a quantum algorithm to
accelerate, independent of the rarity question above — a type mismatch
this task's own original filing did not catch, because it did not check
what the actual classical baseline's own sampling process looks like.

**Does this reasoning reach the joint (collective + side-chain) layer
too, or only the collective one this task named?** Checked, not assumed:
[[TASK-0204]] already found the side-chain/rotamer sub-problem **exactly**
solvable (bucket elimination, real pocket windows, 0.001–0.159s,
validated against brute force) — faster than any sampling-based method,
classical or quantum, could be. Once an exact solver this cheap exists,
a sampling algorithm (quantum or classical) has nothing left to
accelerate there either. **Both layers this program has actually
modeled — collective (ANM-harmonic) and local (rotamer-discrete) — turn
out classically cheap by exact or near-exact methods, not merely "not
proven hard."** No remaining sub-problem in the register's own current
decomposition has the shape (genuinely rare event, or genuinely
slow-mixing landscape) that would make a search/sampling quantum
algorithm relevant.

**What this leaves as the program's real remaining gap — not a
complexity question, a modeling-fidelity one.** [[TASK-0230]]'s own
still-open finding (severe steric clash from rigid-per-residue backbone
translation, `vdwrep` 3–12× native apo even after the best relaxation
tried) is not a search-cost problem either layer's own quantum framing
was built to address — it is a classical structural-modeling accuracy
problem (a better backbone-placement method: torsion-based or
energy-minimized, not rigid translation). Solving it would not create a
quantum opportunity; it would let the program's own already-built exact
solvers ([[TASK-0204]]) and already-cheap collective sampling
([[TASK-0185]]/this task) be trusted on a physically realistic structure
instead of an artificially distorted one.

**Correction to [[TASK-0233]]'s own graduation-condition application,
recorded here rather than silently left standing**: [[TASK-0233]]'s Done
section filed this task on the stated ΔG-plausibility bar being met,
without cross-checking [[TASK-0229]]'s own family (specifically
[[TASK-0185]], not itself a TASK-0229.xxx file but adjacent prior work)
first. The ΔG number itself is correct and stands; the decision to file
a *quantum-sampling* hypothesis subtask on it was premature — a
plausible-and-common state (the real finding) does not clear the bar a
plausible-and-rare state would have. Filing this task at all was useful:
it forced the check that surfaced [[TASK-0185]] and produced the
doubly-disqualifying finding above, now on record instead of latent.

**Not retried, real remaining scope, not assumed closed**: whether a
*different* quantum primitive (not search/sampling-shaped) could apply
to the backbone-modeling-fidelity gap itself — not evaluated here, no
candidate identified, genuinely open rather than quietly folded into
this retirement.
