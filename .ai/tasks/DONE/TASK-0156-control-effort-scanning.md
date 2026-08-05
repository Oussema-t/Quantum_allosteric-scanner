# TASK-0156 Control-effort scanning (minimum-energy reachability) as a per-residue allostery observable

## Context

- ID: TASK-0156
- **Renumbered 2026-07-25 (Architect/Planner)**: filed as TASK-0153 by
  `REVIEW-2026-07-23-register-hygiene-and-p12-gate.md`; collided with an
  already-committed, already-Done TASK-0153 (holo-diagnostic
  transport/lowmode extension, widely cross-referenced from
  `RESULTS.md`/`COMMON.md`/TASK-0145/TASK-0149's own Done sections).
  Renumbered here rather than the other way — the holo-diagnostic task's
  number had already propagated into 4+ live documents; this task had
  propagated into none (still unclaimed TODO). No content changed.
- Title: rank residues by the *minimum control energy* required to steer
  the CTQW's population from the active-site seed to each candidate
  residue, rather than by where the uncontrolled walk deposits
  probability. The control field is a probe; the readout is its cost.
- Status: Done
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: raised by the orchestrating collaborator (Oussama), 2026-07,
  as "phase-controlled CTQW to reduce trapping and improve ranking."
  **Re-scoped by this planning thread before filing** — see the
  correction below — from control-as-cure to control-as-ruler, which is
  the only version that is both well-posed and non-circular.
- Priority: **P2.**

## Correction to the original framing — read before implementing

The original framing ("dynamically control phases to eliminate
destructive interference and reduce trapping, then read where the walker
lands") is **not** filed as stated, for two reasons that are theorems,
not opinions:

1. **"Minimise destructive interference" is not a well-defined
   objective.** Interference is not an observable; it is basis- and
   gauge-dependent (a local phase rotation `|j> -> e^{i theta_j}|j>`
   changes per-path phases while leaving every measurable probability
   invariant). No gradient-based optimal-control method (GRAPE/CRAB/
   Krotov) can target a quantity that changes under a transformation
   that changes nothing measurable.
2. **The controllability paradox.** If a control field is strong enough
   to redirect amplitude to a chosen residue, the final state reflects
   the control field, not the protein — and controllability theory
   (Albertini & D'Alessandro 2012, *Math. Control Signals Syst.* 24,
   321-349, DOI 10.1007/s00498-012-0084-0 — verify before building)
   states a sufficiently connected graph can be driven anywhere. Signal
   about the protein -> 0 as control -> success.

**The reformulation that survives both:** do not use control to improve
the walk. Read out the *cost of control itself*. For each residue `i`,
compute the minimum control energy `E_i = min_u integral ||u(t)||^2 dt`
required to transfer population from the active-site seed to `i` at
fidelity >= F within horizon T, under `H(t) = H_0 + sum_m u_m(t) H_m`
(H_0 = this project's existing operator; H_m = local node-potential
shifts and/or real coupling modulations). Low `E_i` = residue strongly
dynamically coupled to the active site = candidate allosteric site.
This is well-posed (standard minimum-energy optimal control, gradient
available via GRAPE — Khaneja et al. 2005, *J. Magn. Reson.* 172,
296-305, DOI 10.1016/j.jmr.2004.11.004 — verify before building),
non-circular (computed identically for every residue; the pocket is
never named), and directional (`E_{a->i} != E_{i->a}` in general, unlike
the symmetric average-mixing matrix). It is the quantum analogue of
Perturbation-Response Scanning (Atilgan & Atilgan 2009, *PLoS Comput.
Biol.* 5, e1000544, DOI 10.1371/journal.pcbi.1000544 — already in the
register's citation set), which is also the classical baseline it must
beat.

## Intent Contract

- Outcome: a per-residue score `E_i` (minimum control energy from the
  active-site seed), computed via GRAPE against the existing `H_new`/
  contact-graph `H_0`, reused converged-limit or a stated finite T.
  Report as a candidate-ranking observable AND its distance-correlation
  diagnostic.
- Why required, not assumed: this is the only proximity-orthogonal-*by-
  construction* control observable that is also non-circular; whether it
  actually separates allosteric residues from distance is untested, and
  the most likely failure mode (below) is cheap to detect.
- In Scope:
  - Verify the three citations directly before implementing against them
    (per `.ai/reference/IMPLEMENTER_SPINUP_BRIEF.md` discipline).
  - Implement minimum-energy GRAPE control on the existing single-
    particle propagator; no new Hamiltonian family.
  - **Pre-registered kill-switch (run FIRST, before any scoring):**
    on KRAS (4OBE), compute `E_i` for all residues and correlate with
    graph-hop and Euclidean distance from seed. If `|rho| > 0.85` ->
    STOP and record as a distance proxy (the whole idea dies cheaply,
    one afternoon). If `|rho| < 0.6` -> proceed.
  - **Primary readout is the TASK-0123 distance-STRATIFIED AUC**, not
    whole-graph AUC — the PRS analogy predicts whole-graph AUC near
    chance even on success (see 2026-07-22 review, Method A: mode-
    filtered PRS collapsed rho 0.71->0.08 but sat at chance whole-graph;
    signal only under the stratified lens). Pre-register stratified AUC
    as primary so the task gives a clean answer either way.
  - Score all 3 mandatory targets vs. the proximity floor, with CIs and
    a permutation null; then ASD unseen set with multiplicity correction
    if the mandatory set clears.
- Out Of Scope:
  - "Minimise destructive interference" as an objective — killed above.
  - Any RL / learned control policy — established as no-advantage in the
    model-known, differentiable regime (Bukov et al. 2018, *PRX* 8,
    031086); adds an overfitting surface to the falsification apparatus.
    A pure gradient (GRAPE) baseline only.
  - Reselecting the submission operator (Tier-2-gated, [[TASK-0100]]).
- Constraints And Invariants: the horizon T, fidelity threshold F, and
  control-operator set are fixed once, stated, and blind to labels.
  Report ranking sensitivity to T and F — a ranking that flips with T is
  not a measurement.
- Planned Validation: synthetic dumbbell gate (does `E_i` track planted
  coupling at equal distance?) BEFORE real data; then the kill-switch;
  then stratified scoring.

## In Progress

None

## TODO

- [x] Verify the Khaneja/Albertini/Atilgan citations directly. All 3
      confirmed to exist with the stated journal/pages/DOI. One nuance
      flagged (not a citation error): Albertini & D'Alessandro 2012's own
      scope is discrete-time coined quantum walks, not the continuous-
      time Hamiltonian control this task actually uses -- the qualitative
      claim still transfers via the standard (differently-cited)
      dynamical-Lie-algebra controllability theorem for bilinear quantum
      control systems. See `control_effort.py`'s module docstring.
- [x] Implement minimum-energy GRAPE control on the existing propagator.
      `src/allostery/control_effort.py`. Control channels restricted to
      the active-site seed residues only (Implementer's call, justified
      in the module docstring). Gradient verified against finite
      differences (1e-4) and the Trotterized propagator verified against
      exact `scipy.linalg.expm` (1e-3) before trusting anything built on
      it. Plain gradient descent oscillated rather than converged on a
      real target (KRAS_G12C residue 11) -- caught by instrumenting
      per-iteration fidelity/energy, not assumed to be working; switched
      to Adam, confirmed smooth convergence.
- [x] Synthetic dumbbell gate: `E_i` tracks coupling at equal distance.
      `tests/test_control_effort.py::TestSyntheticDumbbellGate` -- two
      identical-topology, identical-hop-distance chains differing only in
      edge weight; the strongly-coupled chain's end scores lower energy
      (cheaper to reach) than the weakly-coupled twin. Passed.
- [x] Kill-switch: `rho(E_i, distance)` on KRAS; stop if `|rho|>0.85`.
      `scripts/control_effort_kill_switch.py` -- rho=0.56 (hop),
      rho=0.55 (Euclidean), both well under 0.85. **PROCEED.**
- [x] Stratified-AUC scoring (primary) on 3 mandatory targets vs floor,
      CIs, permutation null. `scripts/control_effort_scoring.py`. First
      run used a size-blind fixed T=15, which left BCR_ABL1/
      CARDIAC_MYOSIN's feasible fraction near zero and their stratified
      AUC degenerately pinned at exactly 0.5 in every shell (a scoring
      artifact, caught before trusting it -- see Done section) -- fixed
      via a label-blind `T = 15*(N/169)` scaling rule and re-run. Final:
      chance-level on all 3 targets, permutation p=0.48/0.99/0.71, none
      significant. T/F sensitivity check (own Constraint, below) confirms
      this is a real null, not a hyperparameter artifact.
- [ ] ASD unseen set with multiplicity correction if mandatory clears.
      **Not run** -- mandatory set did not clear, per this task's own
      pre-registered gate.
- [x] Report whichever way it comes out, incl. the honest caveat that a
      positive is a better OBSERVABLE, not a quantum speedup (single-
      particle, classically simulable). See `RESULTS.md` row 61.

## Dependency

- [[TASK-0094]] (Done) — proximity floor.
- [[TASK-0112]] (Done) — bootstrap CI.
- [[TASK-0123]] — distance-stratified AUC (the primary lens here).
- [[TASK-0130]] (Done) — converged-limit propagator, reusable.

## Open Questions

- Control-operator set (node potentials only vs. + coupling modulation)
  — Implementer's call, state and justify. **Resolved**: local
  node-potential shifts restricted to the active-site seed residues only
  (not all N, not coupling modulation) — physically motivated (control at
  the point of stimulation), computationally tractable (n_controls =
  |seed| rather than N, feasible across all N candidate targets), and
  strengthens the controllability-paradox defense (a handful of channels
  concentrated at the seed is a far weaker "can reach anywhere" claim
  than N full-graph channels). Full reasoning in `control_effort.py`'s
  module docstring.
- Score at converged limit vs. finite physically-motivated T — state the
  choice. **Resolved**: finite T, not the converged/infinite-time limit —
  a converged-limit control problem is degenerate here (given unbounded
  time, even an infinitesimal control field can eventually reach any
  connected node, defeating the point of measuring a cost). **T is not a
  derived physical quantity** — it is found per target by a label-blind
  empirical search (does the feasible *fraction* on a subsample land in a
  comparable range across targets, never which residues are labelled
  pocket), not a formula. A single size-blind constant (T=15 for every
  target, the first scoring run's mistake) produced degenerate near-zero
  feasibility on the two larger targets. This project's own established
  gap-based horizon prescription (`propagators.min_adequate_t_max`,
  built for exactly this "one constant regardless of energy scale"
  failure mode, RESULTS.md rows 36/39) was checked directly and found
  **not** to fix it either: KRAS_G12C and BCR_ABL1 have nearly identical
  H_new spectral gaps (0.0364 vs 0.0374), so a `T~1/gap` rule predicts
  nearly the same T for both, reproducing BCR_ABL1's degenerate
  feasibility (2/91 on a subsample, checked) instead of curing it —
  feasibility here evidently depends on something beyond the spectral gap
  alone (plausibly seed/N coverage fraction, which varies far more:
  10.7%/5.8%/2.6%). The empirical, linear-in-N values eventually used
  (`T=15*(N/169)`) are reported as a calibration, not a law.

## Done

**2026-08-04, Implementer D.**

**Citations** (verified directly, per this project's Implementer
discipline, before implementing against any of them):
- Khaneja, Reiss, Kehlet, Schulte-Herbruggen, Glaser (2005), *J. Magn.
  Reson.* 172, 296-305, DOI 10.1016/j.jmr.2004.11.004 — confirmed, this
  is the GRAPE paper.
- Atilgan & Atilgan (2009), *PLoS Comput. Biol.* 5, e1000544 — confirmed,
  "Perturbation-Response Scanning Reveals Ligand Entry-Exit Mechanisms of
  Ferric Binding Protein."
- Albertini & D'Alessandro (2012), *Math. Control Signals Syst.* 24,
  321-349, DOI 10.1007/s00498-012-0084-0 — confirmed to exist with the
  stated title/journal/pages/DOI ("Controllability of quantum walks on
  graphs"). **Flagged nuance, not an error**: that paper's own scope is
  *discrete-time coined* quantum walks (a coin operator that can change
  per vertex per step), not the *continuous-time* Hamiltonian control
  `H(t) = H_0 + sum u_m(t) H_m` this task actually builds. The qualitative
  claim it was cited for ("a sufficiently connected/controllable system
  can be driven to any reachable state") is still correct for
  continuous-time bilinear quantum control via the standard dynamical-
  Lie-algebra controllability theorem (Schirmer/Solomon/Leahy-family
  results) — a different, more standard citation for this exact setting.
  Recorded here rather than silently treated as a scope match, and in
  `control_effort.py`'s own module docstring.

**Implementation**: `src/allostery/control_effort.py`
(`scan_control_effort`/`control_effort_score`), batched across all N
candidate target residues sharing one precomputed free-evolution
propagator (eigendecomposition of `H_0` done once, not per residue/
iteration). Minimum-energy-at-fixed-fidelity solved via a one-sided
(hinge) penalty on fidelity shortfall — not GRAPE's original unconstrained
fidelity-maximization objective, and not a per-target bisection/
continuation search over the penalty weight, since the hinge's own
gradient structure already does the right thing (once feasible, the
penalty term and its gradient vanish, leaving pure energy minimization on
the feasible boundary). **Correctness gated before any real data**:
analytic GRAPE gradient checked against finite differences (agrees to
1e-4, `TestForwardBackwardGradient::test_analytic_gradient_matches_
finite_difference`); the Trotterized split-step propagation checked
against exact `scipy.linalg.expm` in the zero-control limit (agrees to
1e-3). **Optimizer bug caught and fixed before trusting anything
downstream**: plain fixed-learning-rate gradient descent oscillates
rather than converges on this objective's landscape (confirmed directly
by instrumenting per-iteration fidelity/energy on a real KRAS_G12C
residue — energy bounced 60-400 across 2000 iterations, never settling)
— switched to Adam (Kingma & Ba 2015), confirmed smooth monotonic
convergence to a real plateau on the same diagnostic.

**Synthetic dumbbell gate** (required by the task's own Planned
Validation, run before any real data):
`tests/test_control_effort.py::TestSyntheticDumbbellGate` — two chains of
identical length/topology from a shared hub (identical hop-distance by
construction, confirmed via `networkx` in the test itself), one with
3.0-weight edges, one with 0.3-weight edges. `E_i` correctly ranks the
strong chain's end below (cheaper to reach than) the weak chain's end,
at *identical* graph-hop-distance — this observable tracks coupling
strength, not merely distance, unlike a naive proximity floor. 10/10
tests in the new file pass, including the gradient/propagator correctness
checks, feasibility-flagging edge cases, and a chunking-invariance check.

**Pre-registered kill-switch** (`scripts/control_effort_kill_switch.py`,
run on KRAS_G12C, T=15, n_slices=20, F=0.5, penalty_weight=5000, n_iters=
500 — the initial, pre-scaling hyperparameters, valid for this single-
target check): rho(score, hop-distance)=-0.56, rho(score, Euclidean
distance)=-0.55 (sign: higher score/lower energy correlates with lower
distance, as expected). Both well under the 0.85 STOP bar and also under
the 0.6 clean-PROCEED bar. **Verdict: PROCEED.**

**Primary scoring** (`scripts/control_effort_scoring.py`, 3 mandatory
targets, distance-stratified AUC (TASK-0123) as primary, whole-graph AUC
+ block-bootstrap CI (TASK-0112) as secondary, 1000-permutation label
null, `prs_low` — TASK-0122/already-shipped, Atilgan & Atilgan 2009's own
classical analogue — as the comparator baseline):

- **A real bug caught mid-pipeline, not silently absorbed.** The first
  run used a single fixed horizon `T=15` (the value validated on
  KRAS_G12C, N=169) for all 3 targets. BCR_ABL1 (N=451) and CARDIAC_MYOSIN
  (N=704) came back with feasible fractions of 5/451 and 8/704 —
  essentially every residue collapsed to the same "infeasible" sentinel
  score, and the resulting stratified AUC was pinned at *exactly* 0.5 in
  *every single shell* on both targets. Exact 0.5 everywhere is this
  project's own standing red flag for a degenerate/tied scoring artifact,
  not a real finding — checked directly (subsample feasibility-rate scan
  at increasing T) before reporting anything, per the Implementer
  spin-up brief's "any surprising number needs verification" rule.
  Confirmed: a size-blind fixed T under-probes larger targets' much
  larger configuration space. **A "more physical" fix was tried first and
  rejected**: this project's own established gap-based horizon
  prescription (`propagators.min_adequate_t_max`, RESULTS.md rows 36/39,
  built for exactly the "one time constant regardless of energy scale"
  failure mode) predicts `T~1/gap`; KRAS_G12C and BCR_ABL1's H_new
  spectral gaps are nearly identical (0.0364 vs 0.0374), so this rule
  predicts nearly the same T for both and, checked directly, still gives
  BCR_ABL1 only 2/91 feasible on a subsample — the bug survives this
  fix. **Actual fix**: T found per target by a label-blind empirical
  search (feasible *fraction* on a subsample, checking feasibility rate
  never label identity, targeting a comparable range across targets), not
  a formula; `T=15*(N/169)` reports where that search landed, not a
  derived law (feasibility here evidently depends on something beyond
  H_0's spectral gap alone, plausibly seed/N coverage fraction, which
  varies far more across these 3 targets: 10.7%/5.8%/2.6%). `F` lowered
  from 0.5 to 0.4 uniformly across all 3 targets (still above the
  dumbbell gate's own validated F=0.3). Re-ran with the fix: feasible
  fractions became 29/169 (17%), 94/451 (21%), 41/704 (6%) — non-
  degenerate, though CARDIAC_MYOSIN stays lower even after scaling,
  reported as a real limitation, not hidden.
- **Final result: chance-level on all 3 mandatory targets.**
  Distance-stratified mean AUC: KRAS_G12C 0.501, BCR_ABL1 0.404,
  CARDIAC_MYOSIN 0.474. Permutation-null p-values: 0.48, 0.99, 0.71 — none
  significant at any reasonable threshold; BCR_ABL1's result is actually
  *worse* than its own null (p=0.99 means the observed mean is below
  99% of permuted-label draws).
- Classical `prs_low` baseline is itself weak/mixed on this exact
  stratified lens (0.51 / 0.25 / 0.83) — this is not a case of control-
  effort failing to beat a strong classical comparator; the comparator
  itself mostly doesn't clear this bar either (except CARDIAC_MYOSIN,
  where `prs_low` is strong — a genuinely different, non-circular result
  for that baseline, unrelated to this task's own finding).
- Full numbers: `results_task0156_control_effort/scoring_results.json`
  (includes per-shell AUC/n_pos/n_neg, whole-graph AUC+CI, and the full
  permutation-null distribution per target).

**T/F sensitivity check** (task's own Constraint: "a ranking that flips
with T is not a measurement"), `scripts/control_effort_tf_sensitivity.py`,
run on KRAS_G12C only (cheapest target) at 3 (T,F) combinations spanning
both directions from the primary run: residue *rankings* are stable and
reproducible (Spearman rho 0.73-0.89 between every pair of combinations,
all p<1e-28) while distance-stratified mean AUC stays at chance
regardless of which combination is used (0.477-0.501). This is the
evidence that the null result above is a real absence of signal, not an
artifact of one particular hyperparameter choice — the observable itself
is well-defined and reproducible, it simply does not correlate with the
pocket label.

**ASD unseen-set scoring: not run.** Per this task's own pre-registered
gate ("ASD unseen set with multiplicity correction if the mandatory set
clears") — it did not clear, so this step is correctly skipped, not a
gap.

**Honest framing, stated per the task's own Report constraint**: this is
a negative result for a candidate *observable*, evaluated on the
project's existing proximity-floor/stratified-AUC/permutation-null
machinery. It says nothing about quantum speedup either way — the whole
computation is single-excitation-subspace and classically simulable
(confirmed no quantum-hardware-specific claim was made anywhere in this
task's own filing). Tests: 10/10 new (`test_control_effort.py`); full
suite re-run before closing (see commit).

Artifacts: `src/allostery/control_effort.py`, `tests/test_control_effort.
py`, `scripts/control_effort_kill_switch.py`,
`scripts/control_effort_scoring.py`,
`scripts/control_effort_tf_sensitivity.py`,
`results_task0156_control_effort/{kill_switch,scoring_results,
tf_sensitivity}.json`, `RESULTS.md` row 61.
