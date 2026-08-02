# TASK-0182 Hardware realization — resource accounting, circuit depth, and an honest near-term feasibility verdict

## Context

- ID: TASK-0182
- Title: produce the per-target qubit / depth / gate-count table the challenge
  requires, re-run the NISQ study under the **corrected** propagation
  convention, and state plainly whether each target is executable on
  near-term hardware — including where the answer is no.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: challenge §4.2 (noise resilience, scalability/coarse-graining),
  §Constraints 1–2 (credible hardware path; *"deep, unoptimized circuits that
  cannot run on near-term hardware will be penalized"*), §Constraint 4
  (Braket/Classiq provided free).
- Priority: **P1 — directly scored under Feasibility (20%) and Technical
  Approach (25%). A proposal with no resource table invites the reviewer to
  assume the worst.**
- Suggested Predecessor: **[[TASK-0188]]**, same thread. No dependency
  (this task's resource/circuit work is unrelated to a hop-distance
  cutoff sweep) -- suggested purely as a sequencing convenience: 0188 is
  small and fast, a reasonable first pick before this task's larger,
  multi-day scope. Recorded 2026-08-01 (Architect).

## Why this matters — the noise result predates the propagator correction

Two concrete gaps, both verified against the repo:

**1. [[TASK-0068]]'s NISQ study is stale.** It ran 2026-07-14 —
*before* [[TASK-0130]]'s converged closed-form propagator and before
[[TASK-0159]] re-pointed the shipped pipeline at it. [[TASK-0110]] documented
the superseded finite-time convention as **orders of magnitude short of
convergence**. So the project's only noise-resilience result characterises
the robustness of a propagation regime it has since abandoned. Its
conclusion (coherent ≥ ENAQT under gate noise) may well survive — but that is
a hypothesis, not a finding, until re-run.

There is a subtlety that makes this genuinely interesting rather than
housekeeping: the converged limit is **provably phase-free** ([[TASK-0130]],
exact to 1e-6 against 12.3 h of brute-force integration). A phase-free
observable should be *unusually* noise-robust — dephasing has nothing to
destroy. If that holds, it is a real and reportable §4.2 result, and it is a
better one than the stale study offers. If it does not hold, that is
diagnostic about the Trotterization rather than the physics.

**2. There is no per-target resource table.** `coarse.py` computes
`n_qubits` / `two_qubit_gates` / `circuit_depth` (l.198–257) and `noise.py`
runs Trotterized Qiskit-Aer circuits with depolarizing + amplitude damping —
the machinery exists. It has never been run across the mandatory targets and
reported as the table the challenge asks for. Braket and Classiq are provided
free under §Constraint 4 and, as far as the register shows, have not been
touched.

**The honest expected answer, stated up front so nobody is tempted to soften
it:** a 1-to-1 mapping is 169 / 451 / 704 qubits, which is beyond useful
near-term execution, and a Trotterized walk deep enough to reach the
converged limit will not survive NISQ coherence. **"Not executable at full
resolution on near-term hardware, executable at N≈20–50 after coarse-graining
with [measured] signal retention" is a perfectly good answer to §Constraint 2
— and a far better one than an optimistic table nobody believes.** The
challenge penalizes deep unoptimized circuits; it does not penalize saying so.

## Intent Contract

- Outcome: a per-target resource table (qubits, 2-qubit gates, depth, Trotter
  steps, estimated fidelity under a stated device error model), at full
  resolution and at ≥2 coarse-graining levels; a re-run noise study under the
  converged propagator; one real small-instance execution on Braket; and an
  explicit near-term feasibility verdict per target.
- Why required, not assumed: the challenge names these as scored objectives;
  the existing noise result is conditioned on a superseded convention.

- In Scope:
  - **Re-run [[TASK-0068]]'s noise sweep under the converged propagator**, with
    the phase-free-robustness hypothesis pre-registered as a prediction before
    running.
  - Resource table across all 3 mandatory targets + c-Myc, at N_full and at
    coarse-grained sizes (couple to [[TASK-0172]]'s retention metric — a
    resource number without a retention number is meaningless).
  - Error model from a *real* published device spec (2-qubit error, T1/T2,
    connectivity), cited, not invented. State the device and date.
  - **One real Braket execution** on a small instance — enough to say the path
    is real rather than asserted. A 6–12 qubit coarse-grained instance is
    sufficient; this is a feasibility demonstration, not a science run.
  - Explicit verdict per target: `EXECUTABLE_NOW` / `EXECUTABLE_COARSE` /
    `FAULT_TOLERANT_ONLY`, with the numbers behind each.
  - If [[TASK-0181]]'s classical gate opens: QAOA resource estimate too. QAOA
    depth scales very differently from Trotterized time evolution and this is
    the one place the resource story might be favourable.

- Out Of Scope:
  - Improving any observable's accuracy.
  - Circuit optimization research. Report depth under a standard
    transpilation; do not build a compiler.
  - Claiming hardware advantage.

- Constraints And Invariants:
  - Resource numbers come from actual transpilation against a real coupling
    map, not analytic formulae, wherever feasible. Report both when they
    disagree — the disagreement is informative.
  - The re-run noise study uses the converged propagator via the same call
    path as `run_challenge.py` ([[TASK-0159]]), not a re-implementation.
  - **A negative feasibility verdict is a valid deliverable.** No target's
    numbers get massaged to reach `EXECUTABLE_NOW`.
  - Braket costs: free under §Constraint 4, but confirm before submitting jobs
    and record actual usage.

- Planned Validation:
  - Noise-free limit: as error rates → 0, the noisy circuit's top-5 must
    converge to the exact converged-propagator result. If it does not, the
    Trotterization is wrong and every noise number is meaningless. **Run this
    first.**
  - Depth-vs-fidelity monotonicity (sanity).
  - Cross-check the analytic depth estimate in `coarse.py` against the
    transpiled circuit's actual depth. A large discrepancy is a bug in the
    estimator and would silently corrupt the resource table.

## In Progress

None

## TODO

- [ ] Noise-free-limit convergence check (**do first** — gates everything).
- [ ] Re-run [[TASK-0068]] noise sweep under the converged propagator, with
      the phase-free-robustness prediction pre-registered.
- [ ] Resource table: 4 targets × ≥3 resolutions, transpiled.
- [ ] Couple resource numbers to [[TASK-0172]]'s retention metric.
- [ ] One real Braket small-instance run; record job id + cost.
- [ ] Per-target feasibility verdict.
- [ ] `RESULTS.md` section + the §4.2 material for the proposal.

## Dependency

- [[TASK-0068]] (Done) — the study being re-run; `noise.py` reused.
- [[TASK-0130]], [[TASK-0159]] (Done) — the converged propagator.
- [[TASK-0172]] — retention metric (soft; report naive Louvain retention if
  0172 has not landed, and say which was used).
- [[TASK-0181]] — conditional QAOA estimate.

## Open Questions

- Which device for the error model? Recommend one superconducting and one
  trapped-ion spec — connectivity differs sharply and a protein contact graph
  is not a heavy-hex lattice. The SWAP overhead on a fixed coupling map may
  dominate the entire depth budget, which would itself be the §Constraint 2
  finding.
- Classiq is provided free and is a synthesis/optimization tool. Worth one
  timeboxed evaluation — if it materially reduces depth, that is directly
  responsive to §Constraint 2. Timebox it; do not let it become a project.
- Does the phase-free converged observable admit a *shallower* circuit than
  Trotterized time evolution — e.g. estimating spectral overlaps directly
  rather than simulating the walk? If yes, this is the most valuable single
  result in this task and possibly the strongest genuinely-quantum sentence in
  the whole submission. Scope it; do not assume it.

## Done

(not yet)
