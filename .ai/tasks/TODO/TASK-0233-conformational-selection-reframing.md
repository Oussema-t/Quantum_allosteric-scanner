# TASK-0233 Conformational-selection reframing: ANM-harmonic population estimate + a third quantum angle

## Context

- ID: TASK-0233
- Title: reframe pocket "reachability" from a binary energy-minimization
  ceiling question (TASK-0227/0230's own framing) to a population/free-
  energy question, per the conformational-selection (population-shift)
  model of allostery — proposed by Bartosz, 2026-08-22.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: user question this session — "what if allostery is about a drug
  stabilising a specific pre-existing conformer (locking an active/
  inactive state) rather than inducing a new one" — the Monod-Wyman-
  Changeux population-shift model, as opposed to Koshland induced-fit.
- Priority: P1 — directly reframes how to read [[TASK-0230]]'s own
  central finding (Addendum 2: minimization returns the closed state),
  and names a concrete, cheap, buildable next calculation reusing
  existing data.

## Why this is not a tangent — it explains data already in hand

[[TASK-0230]] Addendum 2 found: on KRAS_G12C, a lightly-relaxed structure
reads druggable (0.726) but a genuinely energy-*minimized* one collapses
to closed (0.004) at almost the same clash level. Under an induced-fit/
ceiling framing this reads as a puzzle or a negative. Under conformational
selection it is the **expected** result and not informative on its own:
minimization from a single structure finds the dominant (closed) state by
construction; a rare, higher-energy minor conformer would never be
expected to be the global minimum. The ceiling experiments in [[TASK-0227]]
/[[TASK-0230]] were answering "is the closed state the minimum" (yes,
trivially, under this model) rather than "how rare is the open state" —
the type-correct question conformational selection actually poses.

[[TASK-0227]] §5.1 (static ANM-mode cumulative overlap, 0.58–0.90 on real
targets) is *already* a population-shift-flavored result, not previously
read as one: high overlap between the true apo→holo displacement and the
apo structure's own low-frequency normal modes means the fluctuation
direction toward the holo-like conformer is part of the protein's native
thermal ensemble, not something requiring an external, induced push.

**Grounding already in this project's own register, not newly invented**:
Gunasekaran, Ma & Nussinov 2004 (`REFERENCES.md` [9], cited, status
UNTESTED) is the population-shift-is-general-to-allostery paper. [[TASK-0168]]
explicitly flagged "a third mechanism (population shift between discrete
states)" as out of its own scope, deferred to [[TASK-0015]]'s lineage —
the same `allostery.superpose`/cumulative-overlap machinery [[TASK-0227]]/
[[TASK-0230]] already extended. This task is the next link in that chain,
not a new one.

**Per-target mechanism grounding** (field-standard claims; DOIs NOT
verified in this task's own filing — see Open Questions):
- KRAS_G12C: sotorasib covalently traps the GDP-bound-like, signaling-
  inactive conformer (already cited: Ostrem 2013, `REFERENCES.md` [18]).
- BCR_ABL1: asciminib binds the myristoyl pocket, mimicking the kinase's
  own natural autoinhibitory myristoylation mechanism — locks a
  pre-existing autoinhibited state, doesn't induce a new one.
- CARDIAC_MYOSIN: mavacamten stabilizes the "super-relaxed" (SRX) state,
  a naturally occurring, sparsely-populated autoinhibited myosin
  conformer.

## Intent Contract

- Outcome: a real, quantitative population/free-energy estimate (not a
  binary open/closed judgment) for how "rare" the holo-like conformer
  would be in each target's native apo ensemble, computed from data this
  project has already validated — and an honest assessment of whether
  this estimate is small enough (few kT) to be physically plausible as a
  real, sampled minor state, or too large to support the conformational-
  selection reading.
- Why required, not assumed: [[TASK-0230]]'s own minimization-returns-
  closed result is uninformative without this — it is consistent with
  both "no accessible open state exists" and "an accessible open state
  exists but isn't the global minimum," and only a population estimate
  distinguishes them.
- In Scope:
  - `ΔG_k ≈ ½ λ_k c_k²` per mode (harmonic approximation ANM already
    assumes), summed over the modes needed to reach the true (or
    k=50-truncated) apo→holo displacement, using the eigenvalues and
    projection coefficients [[TASK-0227]]/[[TASK-0230]] already compute
    (`allostery.superpose.anm_modes`, reused not re-derived) — no new
    physics, a direct reuse of already-validated machinery.
  - Report in kT units (need a real ANM force-constant calibration —
    check whether `allostery/superpose.py` or `hamiltonians.py` already
    calibrates against real B-factors, e.g. `calibrate_kappa`, before
    assuming arbitrary/uncalibrated units are physically meaningful).
  - Compute for all 3 real target pairs, both the k=50-truncated and full
    displacement (mirroring [[TASK-0230]]'s own two ceiling passes) so the
    population estimate can be compared against the already-measured
    mode-overlap fractions.
  - State explicitly, per target: is the estimated population plausible
    (few kT, a real minor conformer) or implausible (many kT, effectively
    unreachable even under population-shift)?
  - Name the third quantum-sampling angle (quantum Gibbs/Boltzmann
    sampling or a quantum walk over conformational microstates biased
    toward the Boltzmann distribution) as a hypothesis for the register,
    distinct from QUBO-minimization (mistyped, per the source document's
    own §6.1 and [[TASK-0230]] Addendum 2's own direct confirmation) and
    Montanaro backtracking search ([[TASK-0228]]'s own proposal) — not
    built or costed here, named and scoped only.
- Out Of Scope:
  - Building the quantum-sampling algorithm itself — a hypothesis to add
    to the register, not an implementation in this task.
  - Verifying the per-target mechanism citations (asciminib/myristoyl,
    mavacamten/SRX) against live DOIs — real, separate work, flagged in
    Open Questions, not assumed done by filing this task.
  - Any change to [[TASK-0227]]/[[TASK-0230]]'s own already-committed
    Done sections — this task adds a new, complementary calculation, it
    does not revise or retract those findings.
- Constraints And Invariants: reuse `allostery.superpose`'s own validated
  ANM eigenvalue/eigenvector machinery; no new energy function; state
  the calibration status (arbitrary vs. real-unit force constants)
  explicitly rather than silently presenting an uncalibrated number as
  physical kT.
- Planned Validation: the harmonic approximation itself has a known
  failure mode (large displacements are not well-modeled by a single
  quadratic expansion around the apo minimum) — state this bound
  explicitly per target based on how large the projected displacement is
  relative to where the harmonic approximation is expected to break down,
  rather than reporting a ΔG estimate for a displacement so large the
  method underlying it is no longer trustworthy.

## Open Questions

- **Checked while filing this task, not left speculative**: `allostery.
  superpose.calibrate_kappa` exists and calibrates the ANM spring
  constant against each target's real mean B-factor
  (`CleanResult.b_mean`) — but its own docstring is explicit that "no
  kT / (8π²/3) prefactor is applied... kappa is only meaningful as a
  relative scale within this module, not as a real spring constant."
  **A true kT-unit ΔG is not what this function returns today.** The
  standard path from a B-factor to a physical spring constant is
  well-established (Debye-Waller: `⟨Δr_i²⟩ = (8π²/3)·B_i`; equipartition
  for an isotropic 3D harmonic mode: `⟨Δr²⟩ = 3kT/κ`) and derivable from
  data `calibrate_kappa` already has (`b_mean`) — this task's own In
  Scope should add that one missing conversion step explicitly (and
  state the temperature/units assumed) rather than reuse
  `calibrate_kappa`'s relative-scale number as if it were already kT.
- Do the asciminib/myristoyl-autoinhibition and mavacamten/SRX-state
  mechanism claims actually verify against live DOIs, per
  `.ai/reference/PAPER_CITATION_PROTOCOL.md`? Not checked when this task
  was filed — real citations to add to `REFERENCES.md` if confirmed, not
  to be treated as validated until then.
- Does a small ΔG estimate on any target change [[TASK-0228]]'s own
  priority/sequencing (search-based conformer-graph framing) — an
  Architect-level call, raised alongside this task via
  `.ai/memory/questions/architect-planner/open/`.

## Done

(not yet)
