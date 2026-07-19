# TASK-0122 Build `mode_coparticipation`: a less distance-confounded observable

## Context

- ID: TASK-0122
- Title: `mode_coparticipation` was proposed by
  `REVIEW-2026-07-13b-operator-falsification-negative-controls.md` §6
  and never built (confirmed absent by grep). Build it, gate it through
  the dumbbell 2x2 negative-control matrix ([[TASK-0103]]) and real
  labels, and pair it with [[TASK-0121]]'s potential renormalization —
  it does not work as a standalone fix.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer B (this thread)
- Claimed At: 2026-07-19
- Source: `.ai/reviews/REVIEW-panel-2026-07-16-v2.md` §2.5, §5 P1-6.
- Priority: **Escalated — this is now P1-5 in
  `.ai/reviews/REVIEW-panel-2026-07-17.md`** ("the experiment your own
  learnability gate demands... the only route back to a defensible
  positive"), with a sharpened, evidence-backed specification below.
  [[TASK-0121]] (the hard dependency this task was already paired with)
  has landed — this task is now unblocked, not just paired.

## Intent Contract

- **Sharpened target, per the 2026-07-17 review — build this specific
  form, not a generic co-participation function.** [[TASK-0120]]
  measured that the real apo→holo displacement lives 58-79% inside the
  lowest-20 ANM modes (CO(20) = 0.638/0.794/0.584) — but the CTQW
  observable this project scores integrates over **all** N modes
  (169-950), averaging that ~20-dimensional signal against 150-930
  dimensions of pure proximity noise. The review's own reconstruction
  (3MHT, N=327, unverified against this repo's real code — treat as a
  hypothesis to confirm, not a result to inherit) measured a slow-mode-
  filtered form:

  ```
  CP_low(j) = Σ_{k ≤ n_low} |v_k(j)|² · mean_{i ∈ src} |v_k(i)|²
  ```

  at `k=5`: `ρ(CP_low, −dist)` dropped from +0.560 (all 327 modes) to
  **−0.061** — inside their own measured noise floor (`|ρ(random,
  −dist)| = 0.044 ± 0.036`) — while cross-cutoff reproducibility
  (`ρ(CP@7Å, CP@8Å)`) *improved* from 0.542 to **0.940**, the signature
  of real structure rather than noise (per Zheng/Brooks/Thirumalai, PNAS
  103:7664 — citation as given by the review, not independently verified
  by this Architect/Planner thread). `n_low` is already a `build_H_new`
  argument and already swept as a potential ingredient in the ceiling
  search — this task's job is to also expose it as an **observable
  filter**, independent of whether it's used as a Hamiltonian ingredient.
  Sweep `k` (at minimum the review's own 3/5/10/all checkpoints) on real
  targets and report where `ρ(CP_low, −dist)` crosses into the noise
  floor, rather than assuming `k=5` transfers from a 327-residue
  reconstruction to this project's real 169-950-residue targets.

- Outcome: a new observable, `mode_coparticipation` (or equivalent name),
  seed-dependent and **not distance-monotone by construction** — the
  right shape for an allosteric-channel detector, unlike raw CTQW/GSR
  occupation (per §2.3, occupation-of-a-walk-seeded-at-a-point is
  monotonically decreasing in distance from that point, for *any*
  operator, at *any* time — this is why a different observable, not a
  better Hamiltonian, is the fix).
- **Hard, quantified dependency the panel already measured [EXECUTED] —
  do not skip this ordering**: on a **clean** normalized Laplacian
  (no disorder, no potential), co-participation (CP) is the
  *least*-confounded observable in the register (`|ρ|` with distance
  ≈ **0.18**, vs. 0.28 for shipped CTQW in the same geometry). But on
  the **current, un-renormalized `H_new`**, CP inherits the operator's
  own localization and is *worse* than CTQW (`|ρ|` ≈ **0.50**). **Build
  this only after [[TASK-0121]] lands**, or measure CP on both the
  current and renormalized `H_new` and report the difference explicitly
  — do not report a bare CP number without stating which `H_new`
  (renormalized or not) produced it.
- **Necessary but not sufficient — state this explicitly in Done**: low
  distance-correlation is necessary but not sufficient to find a real
  pocket. Whether CP actually *enriches* for true pocket residues (not
  just decorrelates from distance) is untested and must be gated through
  the dumbbell matrix (does it track coupling, not the well — same
  falsification lens as GSR/CTQW got in TASK-0103) and real labels
  (does it beat the proximity floor on real targets) before it is
  claimed as a fix, not just a cleaner metric.
- In Scope:
  - Implement `mode_coparticipation` per REVIEW-13b §6's original
    specification.
  - Measure `|ρ|` with distance on (a) a clean Laplacian, (b) current
    `H_new`, (c) renormalized `H_new` (post-[[TASK-0121]]) — reproduce
    the panel's 0.18/0.50 comparison points as a validation gate before
    trusting any further result.
  - Gate through [[TASK-0103]]'s dumbbell 2x2 matrix (does CP track
    coupling, not the well).
  - Score against real labels on all 3 mandatory targets, checked
    against the proximity floor ([[TASK-0094]]), same discipline as
    every other observable in this register.
- Out Of Scope:
  - The potential renormalization itself — [[TASK-0121]]'s scope, this
    task consumes its output.
  - Reselecting the submission operator/observable based on this task's
    result alone — Tier-2 gating (per [[TASK-0100]]) applies the same
    way it does to every other candidate.
- Constraints And Invariants: report per-observable, per-operator-variant
  distance-correlation numbers explicitly labeled by which `H_new`
  variant produced them — never a bare "CP is less confounded" claim
  without that label, given the panel's own finding that the answer
  flips sign depending on it.
- Planned Validation: the dumbbell-matrix gate + real-target proximity-
  floor check, both required before any claim that CP finds real pockets
  (as opposed to merely decorrelating from distance).

## In Progress

None

## TODO

- [x] Implement `mode_coparticipation`/`CP_low` (the slow-mode-filtered
      form above, per the 2026-07-18 sharpened spec).
- [x] Reproduce the panel's clean-Laplacian (0.18) vs. current-H_new
      (0.50) distance-correlation comparison as a validation gate.
      Found: neither number reproduces on any real target (see Done).
- [x] Re-measure on renormalized `H_new` (post-[[TASK-0121]], now Done).
      Found: renormalization makes distance-correlation worse, not
      better, on all 3 targets.
- [x] Sweep `k` (≤n_low filter) on all 3 real targets; report where
      `ρ(CP_low, −dist)` crosses into a measured noise floor — do not
      assume the review's `k=5`/3MHT result transfers directly. Found:
      it does not reliably cross on any of the 3 real targets.
- [x] Gate through [[TASK-0103]]'s dumbbell matrix. Passed cleanly.
- [x] Score against real labels, all 3 targets, checked against the
      proximity floor. Found: clears floor on 1/3 (BCR_ABL1 only).

## Dependency

- [[TASK-0121]] (Done) — was the hard blocker, now landed; this task is
  unblocked.
- [[TASK-0120]] (Done) — the CO(20) finding this task's slow-mode filter
  directly operationalizes.
- [[TASK-0103]] (dumbbell matrix, Done) — reused, not rebuilt.
- [[TASK-0094]] (proximity floor, Done) — reused for the real-label check.
- Related, not blocking: [[TASK-0133]] (learnability-gate random-patch
  control) — if that task finds CO(20) doesn't discriminate the real
  pocket from a random patch, read this task's own `k`-sweep result
  alongside it before claiming `CP_low` finds the pocket specifically,
  not just "some structure."

## Open Questions

- Exact functional form of `mode_coparticipation` (which modes, what
  co-participation metric) — REVIEW-13b §6 is the cited source spec;
  Implementer's call on any remaining implementation detail, state it
  in Done.

## Done

**2026-07-19, Implementer B.** Implemented, tested, gated through the
dumbbell matrix (passed cleanly), and validated on all 3 real mandatory
targets. **Result: mostly negative, real, and honestly reported** — the
panel's own preliminary numbers (measured on a reconstructed 3MHT
surrogate, explicitly flagged there as unverified) do not transfer to
this project's real code/targets, and not in the hoped-for direction.

### Implementation

New `analysis.mode_coparticipation(H, source, n_low=5)` — the sharpened
per-residue form from the task file's own spec:
`CP_low(j) = sum_{k<=n_low} |v_k(j)|^2 * mean_{i in source} |v_k(i)|^2`,
over `H`'s own `n_low` lowest non-trivial eigenmodes (skips the single
lowest mode via `max(1, searchsorted(w, 1e-8))`, the same convention
`spectral_enrichment`/`potentials.V_M` already use — reused, not
reinvented). Diagonalizes whichever `H` is passed in (an operator-level
observable, matching `ctqw`/`ground_state_relaxation`'s own convention),
since the panel's own finding is that CP's distance-correlation
*depends on which operator variant produced the eigenbasis* — exactly
what this task's own validation gate below checks. `mean` (not `sum`)
over `source`, matching `propagators._quantum_initial_coeffs`'s own
seed-cardinality-normalized convention.

### Tests

- `test_analysis.py::TestModeCoparticipation` (7 tests): shape,
  non-negativity, exact-formula regression pin (independent hand-
  derivation from `H`'s own `eigh`, not calling the function against
  itself), seed-dependence, `mean`-not-`sum` regression pin, `n_low`
  sensitivity, correctness on an indefinite operator (`H_new`).
- `test_dumbbell_negative_control.py::TestModeCoparticipationDumbbellGate`
  (5 tests) — the task's own **mandatory** gate before any target could
  be scored. Measured directly before writing assertions (this project's
  own discipline), not assumed to inherit CTQW's exact thresholds: CP
  tracks coupling not the well, cleanly — C2=1.000, C3=0.000 (vs CTQW's
  own >0.85/<0.15 thresholds, comfortably cleared), a clean double
  dissociation against GSR in both conflict cells. C1 (cues agree) not
  asserted tightly, for the identical reason this file's own existing
  CTQW test already doesn't assert C1 tightly (a deep co-located well
  perturbs the low-mode structure even when coupling agrees — CP shows
  an even stronger instance of the same effect, not a new defect). C4
  (no cues) near chance, loose bound, same convention as GSR/CTQW.

### Real-target validation (new `scripts/mode_coparticipation_validation.py`,
`results_task0122_mode_coparticipation/mode_coparticipation_validation.json`)

**Check 1 — the panel's own 0.18/0.50 validation gate, reproduced or
refuted per target, not assumed**:

| Target | `\|rho\|` clean Laplacian | `\|rho\|` `H_new` pre-TASK-0121 | `\|rho\|` `H_new` current |
|---|---|---|---|
| KRAS_G12C | 0.430 | 0.198 | 0.305 |
| BCR_ABL1 | 0.237 | 0.425 | 0.451 |
| CARDIAC_MYOSIN | 0.621 | 0.239 | 0.358 |

Neither half of the panel's claim holds on any real target: the clean
Laplacian is *more* distance-confounded than their 0.18 estimate on all
3 targets (0.24-0.62), and TASK-0121's renormalization made CP's
distance-correlation *worse*, not better, on all 3 targets (the
opposite of the panel's own hoped-for direction) — though the *sign*
also flips (positive/proximity-confounded on the clean Laplacian,
negative/anti-proximity on every `H_new` variant), a different confound
shape, not evidence of less confound.

**Check 2 — k-sweep against a real, freshly-measured noise floor** (not
copied from the panel's 3MHT estimate of 0.044+/-0.036): `n_low` in
{3,5,10,20,all} on the current renormalized `H_new`. Noise floors:
KRAS 0.063+/-0.045, BCR_ABL1 0.037+/-0.027, CARDIAC_MYOSIN
0.026+/-0.020 (200 random draws/target). Never reliably crosses into
the noise floor: KRAS dips in only at `k=10` (0.114, non-monotonic —
`k=3/5/20/all` are 0.179/0.305/0.498/0.760, all outside); BCR_ABL1 and
CARDIAC_MYOSIN never cross at any `k` tested. The panel's own specific
"`k=5` decorrelates" claim does not reproduce on any real target
(`k=5`'s own `\|rho\|` is 0.305/0.451/0.358, all well outside each
target's noise floor).

**Check 3 — real-label scoring vs. TASK-0094's proximity floor**:

| Target | CP AUC | Floor | Clears? |
|---|---|---|---|
| KRAS_G12C | 0.309 | 0.482 | No (-0.173) |
| BCR_ABL1 | 0.758 | 0.582 | **Yes (+0.176)** |
| CARDIAC_MYOSIN | 0.577 | 0.792 | No (-0.215) |

Genuinely mixed, not uniform: BCR_ABL1 is a real pass, but its own CP
score is also the most distance-correlated of the three (`\|rho\|`=0.451)
— the floor-clearing AUC coexists with, not instead of, a substantial
distance confound, which weakens (does not void) reading it as clean
coupling-detection evidence.

### Verdict

`mode_coparticipation` is correctly implemented (formula independently
verified) and correctly falls on the "tracks coupling, not the well"
side of the mandatory dumbbell gate. On this project's real targets and
real code it does **not** deliver the low-distance-correlation property
its entire case for adoption rested on, and clears the real-label
proximity floor on only 1 of 3 mandatory targets. **Not a recommendation
to adopt it as a submission observable in its current form** — a real,
checked answer to a load-bearing question, and the answer is mostly no.
Tier-2 gating ([[TASK-0100]]) applies unchanged; this task's scope was
measurement, not operator selection (per its own Out Of Scope).

### Not attempted / left for a follow-up task

- Did not sweep the thermal filter (`E_k - E_0 <= kT`) REVIEW-2026-07-13b
  Sec.6 also proposed alongside the mode-count filter — the task's own
  sharpened 2026-07-17 spec named the `n_low`/`k`-sweep form as the
  priority form to build and validate first; the thermal-energy filter
  is a distinct, unbuilt variant, not silently dropped.
- Did not investigate *why* renormalization worsens CP's distance
  correlation (a mechanism question, out of this task's own measurement
  scope) — flagged as a real, reproducible, 3-for-3 finding for whoever
  picks up mechanism work next.
- Did not re-run [[TASK-0133]] (learnability-gate random-patch control)
  alongside this task's own k-sweep, per the Dependency section's own
  "related, not blocking" framing — [[TASK-0133]]'s own status should be
  checked before citing this task's k-sweep as evidence CP finds the
  pocket specifically rather than "some structure."
