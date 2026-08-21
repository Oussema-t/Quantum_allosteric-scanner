# TASK-0182 Hardware realization — resource accounting, circuit depth, and an honest near-term feasibility verdict

## Context

- ID: TASK-0182
- Title: produce the per-target qubit / depth / gate-count table the challenge
  requires, re-run the NISQ study under the **corrected** propagation
  convention, and state plainly whether each target is executable on
  near-term hardware — including where the answer is no.
- Status: Done
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

- [x] Noise-free-limit convergence check (**do first** — gates everything).
      Done via new `noise.time_sampled_converged_occupation` +
      `hardware_resource_accounting.py::step1_convergence_check`. Real
      residual found (L1 0.36-0.44, top-5 overlap 0.43-0.67 at NISQ-plausible
      fixed depth) — carried forward as a caveat, not treated as negligible.
- [x] Re-run [[TASK-0068]] noise sweep under the converged propagator, with
      the phase-free-robustness prediction pre-registered. Pre-registered
      before running (see `PRE_REGISTERED_HYPOTHESIS` in the script and
      RESULTS.md row 56) — **falsified on balance** (supported on 2/4
      targets, contradicted on BCR_ABL1, a wash on CARDIAC_MYOSIN).
- [x] Resource table: 4 targets × ≥3 resolutions, transpiled. Full + 2
      coarse resolutions (Louvain-actual N≈9-15), transpiled against a real
      IBM FakeSherbrooke calibration snapshot AND a hand-built IQM Garnet
      topology (see Done section for the qiskit-iqm SDK conflict).
- [x] Couple resource numbers to [[TASK-0172]]'s retention metric.
      TASK-0172 not landed — used the documented naive-fallback (Louvain
      retention), stated as such. Result: near-zero (Jaccard 0.00-0.18) at
      NISQ-plausible coarse sizes.
- [ ] One real Braket small-instance run; record job id + cost. **Blocked**
      — no AWS credentials in this environment. Per direct user instruction
      (2026-08-02), deprioritized behind a portable Qiskit-simulator-first
      path (real IBM calibration snapshot + hand-built IQM topology) rather
      than blocking the whole task on it. Left open for whenever credentials
      are available.
- [x] Per-target feasibility verdict. All 4 targets `FAULT_TOLERANT_ONLY`
      at both full and coarse resolution, under FakeSherbrooke's real
      median 2-qubit gate error — worse than this task's own pre-stated
      "honest expected answer."
- [x] `RESULTS.md` section + the §4.2 material for the proposal. Row 51.

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

- 2026-08-02 (Implementer D). Full pass on the 3 mandatory targets +
  MYC_MAX. Full detail: `RESULTS.md` row 56 (renumbered 2026-08-03 after a
  real row-51 collision with [[TASK-0185]] wiped rows 47-53 of this
  document in a later concurrent commit — see that row's own "Recovery
  note" for the full account; this citation was correct when written).
  Artifacts:
  `scripts/hardware_resource_accounting.py` (Steps 1-3),
  `scripts/hardware_feasibility_verdict.py` (Steps 4-5),
  `noise.time_sampled_converged_occupation` (new, tested, ADD-only),
  `results/tasks/0182_hardware_resource_accounting/{results.json,
  feasibility_verdict.json}`.

  **Environment / scope decisions, made with the user before starting
  (`AskUserQuestion`, 2026-08-02) since neither was decided anywhere in
  this file:**
  - No AWS/Braket credentials in this environment. User's direction:
    prioritize a local-simulator-first path portable toward IQM, then IBM
    hardware, with Braket credentials to be supplied later — not "stop and
    wait," not "drop the deliverable." Implemented as: real transpilation
    against `qiskit_ibm_runtime.fake_provider.FakeSherbrooke` (a genuine
    calibration snapshot of a real 127-qubit IBM Eagle r3 device) for the
    IBM side. The live `qiskit-iqm` SDK could **not** be installed
    alongside this project's `qiskit>=2.0` stack — confirmed via `pip
    install --dry-run` before deciding, not assumed: `qiskit-iqm` pins
    `qiskit~=0.39.1`, a hard, unresolvable conflict with `noise.py`'s
    modern-API circuits (`qc.rxx`/`AerSimulator`). Worked around by
    hand-encoding IQM Garnet's *published* 20-qubit square-lattice
    topology as a plain `qiskit.transpiler.CouplingMap` and transpiling
    against it with vanilla `qiskit.transpile` — real portability evidence
    (a real published device topology, real transpiler) without needing
    the conflicting SDK. Braket itself stays an explicit open item, not
    silently dropped.
  - Circuit realization of the *converged* (t→∞ time-averaged) observable:
    user chose "time-sample and average" over "single large-t snapshot."
    Implemented as `noise.time_sampled_converged_occupation` (new
    function, `dt` implicit via a fixed `trotter_steps` per sample rather
    than scaled per-`t` — TASK-0068's own finding that the high-accuracy
    step-count prescription produces circuits that do not finish in
    NISQ-relevant time, reused as the reason here too). Validated first
    against `time_averaged_ctqw_converged`'s exact closed form (blocking
    Planned Validation) — found a real, non-negligible residual (L1
    0.36-0.44, top-5 overlap 0.43-0.67) at the NISQ-plausible fixed depth
    used throughout this task; **every downstream noise-comparison number
    inherits this approximation error**, disclosed rather than hidden.

  **Real bug found and fixed while building this** (not a result, an
  implementation defect caught before trusting any number downstream):
  a first version called `functional_indices(apo.coords, ligand_groups,
  target_config, cutoff=...)` directly, omitting `heavy_atom_coords`/
  `heavy_atom_seq_index`. Its tier-1 (func_ligand contact) geometry
  silently falls back to a Calpha-only approximation when those are
  omitted — 4.5 A Calpha-to-ligand almost never matches a real contact, so
  *all 4* targets (including the 3 mandatory ones with real, well-known
  func_ligand contacts) fell through to the tier-2 "top-degree fallback."
  Caught by noticing all 4 targets reporting the identical fallback
  provenance in the script's own log, before trusting any downstream
  number — fixed by routing the 3 mandatory targets through
  `build_labels(apo, holo, target_config, cutoff=pocket_cutoff)`
  (the same tested path `run_challenge.py`'s main branch uses), reserving
  the direct `functional_indices(apo.coords, [], ...)` call for MYC_MAX
  only, matching that target's own established c-Myc branch exactly.

  **Headline findings (all real, run against live RCSB data via
  `.venv`, `qiskit`/`qiskit-aer`/`qiskit-ibm-runtime` newly installed
  this task — binary wheels only, `--only-binary=:all:`, no source
  builds; confirmed zero regressions, `pytest_local.py wip-all`: 1054
  passed / 0 failed both before and after)**:
  - Full resolution: 169-704 qubits, 3.3M-124.9M 2-qubit gates — confirms
    the task's own pre-stated prediction, not executable near-term.
  - Coarse-grained to Louvain's actual N~=9-15 (requesting 12/20 rarely
    yields exactly that many clusters — reported as-achieved, not forced):
    transpiled against FakeSherbrooke needs 538-1486 2-qubit gates, depth
    1010-2565 — down from the analytic estimate but still large.
  - IQM-topology-transpiled circuits came out shallower than the
    IBM-Sherbrooke transpile at every single data point tested (e.g.
    KRAS_G12C N=12: depth 965 vs. 1859) — a real, disclosed,
    connectivity-driven difference (Garnet's dense local grid vs. Eagle's
    sparser heavy-hex), not a hardware-superiority claim (the IQM map is a
    public-topology stand-in, not the live SDK's own transpiler/native
    gate calibration).
  - **Feasibility verdict: all 4 targets `FAULT_TOLERANT_ONLY`, at both
    full and coarse resolution** — worse than this task's own pre-stated
    "honest expected answer" ("not executable at full resolution,
    executable at N~=20-50 after coarse-graining"). Even the smallest
    coarse circuit tested (MYC_MAX, 538 2-qubit gates) lands at an
    estimated fidelity of 0.015 against FakeSherbrooke's real median
    2-qubit (ECR) gate error (0.78%), using a disclosed `(1-p)^n_2q >=
    0.5` usability bar (a judgment call, not derived, stated as such).
  - **Retention (naive Louvain fallback, TASK-0172 not landed)**: top-10
    Jaccard/Spearman retention between full-resolution and
    coarse-grained-then-projected-back rankings is close to zero on every
    target (Jaccard 0.00-0.18, Spearman 0.02-0.26) — the coarse-graining
    aggressive enough to be NISQ-plausible also destroys nearly all of the
    fine-resolution ranking signal. Compounds the feasibility problem
    rather than trading it off: even a hypothetical future device that
    cleared the fidelity bar at this qubit count would not be measuring
    much of the original signal.
  - **Pre-registered phase-free-robustness hypothesis: falsified on
    balance.** Supported (time-averaged more noise-robust than a
    finite-time snapshot) on KRAS_G12C/MYC_MAX at higher error rates;
    contradicted on BCR_ABL1 (time-averaged *worse* at every non-zero
    error rate tested); a wash on CARDIAC_MYOSIN. No clean win for the
    corrected propagation convention over TASK-0068's original snapshot
    approach — reported plainly, not softened, per this project's
    all-negatives-are-findings convention.
  - Classiq evaluation and the conditional QAOA estimate (blocked on
    [[TASK-0181]], not yet landed) were **not** run this pass — left as
    genuinely open, not silently dropped.
  - Tests: `tests/test_noise.py` extended with
    `TestTimeSampledConvergedOccupation` (5 new cases: sum-to-one/shape,
    t=0 collapse, denser-sampling-does-not-regress-vs-exact, noise-model
    plumbing, zero-error-rate matches noiseless) — 22/22 passing.

  **Follow-ups, explicitly not this task's own item to resolve**:
  - Braket execution once credentials are available (see above).
  - Classiq timeboxed evaluation (this task's own Open Questions).
  - QAOA resource estimate, conditional on [[TASK-0181]] landing.
  - Whether a shallower, spectral-overlap-based circuit exists for the
    phase-free converged observable instead of Trotterized time evolution
    (this task's own Open Questions) — not scoped here; the noise-study
    results above suggest the Trotterized route alone will not clear a
    real feasibility bar even coarse-grained, which sharpens the case for
    checking this alternative rather than iterating further on Trotter
    step count.
