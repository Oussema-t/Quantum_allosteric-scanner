# TASK-0099 Wire a genuine coherence-sensitivity metric into the scored verdict path

## Context

- ID: TASK-0099
- Title: Promote `dephasing_sweep` (already implemented, never wired into
  the reported pipeline) into `assemble_verdict_results`/
  `verdict_template`, so at least one reported quantity in `RESULTS.md`
  would actually change if quantum phase/coherence were randomized away
  — and classify whether coherence contributes real signal, per target,
  once the proximity floor is applied.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer A (this thread)
- Claimed At: 2026-07-15 21:06
- Source: user question, 2026-07-13, prompted by auditing TASK-0097's
  finding — "do we now have any algorithms that do rely on phase (truly
  quantum)? Otherwise we are unlikely going towards the Challenge's
  goal." Investigation (this session, evidence-first, traced
  `run_frozen_verdict` end to end) found: **no.** Every AUC currently in
  `RESULTS.md` is built exclusively from `time_averaged_ctqw`
  (phase-averaged by construction) and `ground_state_relaxation` (real
  exponential, no oscillation). `ctqw` (finite-time, phase-carrying) and
  `haken_strobl` (genuine Lindblad coherent→classical interpolation) are
  both correctly implemented and verified against exact analytics (Rabi
  oscillations, Bessel-function CTQW, Lindblad trace conservation) — but
  `dephasing_sweep`, the one function that varies coherence (`γ`) and
  scores AUC at each point, has **zero call sites** in `protocol.py` or
  `report.py`. It exists only in `analysis.py`'s own definition and in
  tests. The one place it *is* tested
  (`test_kras_g12c_dephasing_flat_survives_kappa_calibration`, real
  4OBE/6OIM, physically-calibrated γ) shows AUC range ~0.0035 across the
  full coherent↔classical sweep for KRAS_G12C — flat to noise, but this
  is one target, never reported, and never checked against a proximity
  floor.

### Why this matters beyond a missing feature

Per CLAUDE.md, this is the **Quantum Allosteric Scanner** — a "truly
quantum" claim is load-bearing for the challenge's premise. Right now,
switching off quantum mechanics entirely (setting all off-diagonal
coherences to zero) would not change a single number a judge reads in
`RESULTS.md`. That is a strategic risk to the submission's core story,
not a cosmetic gap TASK-0097's honest-naming fix alone resolves —
TASK-0097 documents the gap; this task is the substantive response.

## Intent Contract

- Outcome: `assemble_verdict_results` (or wherever the per-target verdict
  is assembled, `analysis.py:195-282`) gains a **coherence-sensitivity
  measurement** — run `dephasing_sweep` with a *calibrated* (not blind) γ
  range, using the same recipe as the existing KRAS test
  (`superpose.calibrate_kappa` → `anm_modes` → `mode_energetics`'s
  `relaxation_time` → `gamma_scale = 1 / mean(relaxation_time[:20])`,
  sweep `{0, 0.5, 1, 2} * gamma_scale` at minimum), and report the
  resulting `auc_range` (or equivalent spread statistic) as a formal
  field in the verdict schema, for every mandatory target — not just
  KRAS.
- In Scope:
  - Wire `dephasing_sweep`'s output into the reported schema — a new
    field (e.g. `coherence_auc_range`, `coherence_auc_at_gamma_0`,
    `coherence_auc_at_gamma_inf`) alongside the existing
    `AUC_ctqw_mean`/`AUC_heat_mean` fields.
  - A new verdict category (parallel to `classify_failure`'s existing
    categories): if the calibrated sweep's AUC range is small (matching
    KRAS's ~0.0035 precedent, needs an explicit threshold — don't
    silently reuse 0.0035 as a magic number without justifying it),
    classify as **`COHERENCE_NOT_SIGNIFICANT`**; if the range is large
    enough to matter, classify as **`COHERENCE_DEPENDENT_SIGNAL`** — a
    genuine, reportable ENAQT-relevant finding either way.
  - **Apply TASK-0094's proximity floor to every AUC in the sweep**, not
    just the mean — a coherence-driven AUC change that still never
    clears the proximity floor is not a real finding; report both the
    raw sweep and the floor-cleared status per γ point.
  - Run for all three mandatory targets (KRAS_G12C, BCR_ABL1,
    CARDIAC_MYOSIN), not just KRAS.
- Out Of Scope: re-litigating the retracted TASK-0091 premise (that
  decoherence "recovers" `heat`'s specific 0.731 value on BCR_ABL1 — see
  TASK-0095/TASK-0091's re-file for why that framing is wrong). This task
  asks a different, well-posed question: *does varying coherence change
  the scored, proximity-floor-cleared AUC at all* — regardless of what
  the ground-state/heat computation separately shows. Also out of scope:
  inventing a new phase-dependent algorithm from scratch — `ctqw`/
  `haken_strobl` already exist and are correctly implemented; this task
  is about reporting, not building new physics.
- Acceptance Scenarios:
  - Given all three mandatory targets, when the calibrated dephasing
    sweep runs on each, then `RESULTS.md`'s per-target entry states
    explicitly whether coherence contributes measurable signal
    (`COHERENCE_DEPENDENT_SIGNAL`) or not
    (`COHERENCE_NOT_SIGNIFICANT`), with the actual `auc_range` number —
    not left as an internal-only computation nobody sees.
  - Given a target where the sweep's AUC does change with γ, then that
    change is checked against the proximity floor before being reported
    as signal — a coherence-driven change that's still confounded by
    geometry is reported as such, not oversold as a quantum finding.
  - Given the existing KRAS flat-sweep result, when this task's pipeline
    runs on KRAS_G12C, then it reproduces (or closely matches) the
    ~0.0035 range already established by
    `test_kras_g12c_dephasing_flat_survives_kappa_calibration` — this
    pins the new reporting path to the already-validated computation,
    not a fresh, silently-diverging one.
- Constraints And Invariants: **hard-blocked on TASK-0094** (proximity
  floor must exist before any coherence-driven AUC change can be
  interpreted as real signal rather than geometry). Must not reintroduce
  TASK-0095's corrected propagator-semantics mistake — `haken_strobl`
  and `dephasing_sweep` are already correctly implemented per that
  review; this task only changes what gets *reported*, not the
  computation itself.
- Planned Validation: the three-target sweep results plus the KRAS
  reproduction check above; a `RESULTS.md` update showing the new
  coherence-sensitivity field and classification for all three targets.

## Dependency

- **Hard blocked on TASK-0094** (proximity floor).
- Related to TASK-0091 (re-filed) — complementary, not overlapping:
  TASK-0091 asks whether `H_new`'s ground state localizes on distal
  pockets; this task asks whether coherence itself (independent of which
  operator's ground state you look at) adds scored signal anywhere.
- Related to TASK-0097 (name the metric honestly) — that task documents
  the gap this task fills; do TASK-0097 first or alongside, not as a
  substitute for this task.
- **Resequenced 2026-07-13 behind [[TASK-0105]]**, per
  `REVIEW-2026-07-13b` (§4, §7 T-C): the review reframes the entire
  coherence question from "does dephasing recover a specific AUC" (killed
  as ill-posed — Haken-Strobl's γ→∞ limit is diagonal-vs-off-diagonal
  incommensurate with GSR) to "does dephasing produce a real,
  proximity-floor-clearing interior-γ transport optimum on real targets."
  TASK-0105 answers that question first; this task's own
  `dephasing_sweep` wiring should consume TASK-0105's result (which γ
  range and which target(s) actually show an effect worth wiring) rather
  than proceed on this task's pre-review framing. Do not start this task
  before TASK-0105 lands.
- Reuses `analysis.dephasing_sweep` (TASK-0008, Done, already
  implemented and tested on KRAS) and
  `test_kras_g12c_dephasing_flat_survives_kappa_calibration`'s
  calibration recipe — no new physics code, a reporting/wiring task.

## Open Questions

- What threshold on `auc_range` separates `COHERENCE_NOT_SIGNIFICANT`
  from `COHERENCE_DEPENDENT_SIGNAL`? KRAS's ~0.0035 is one data point;
  don't silently adopt it as a universal threshold without stating the
  reasoning (e.g. relative to the proximity-floor gap, or an effect-size
  convention already used elsewhere in this codebase's verdict logic).

## Clarification (added 2026-07-13, per user question) — this task IS the
ENAQT test; it is NOT a test of TASK-0091's finding

User asked "do we have any meaningful way to inspect whether the ENAQT
approach might be the better one?" — **this task is that test.**
`haken_strobl`'s `γ: 0 → large` sweep is the genuine coherent↔classical-
rate-hopping axis (Lindblad open-system dephasing) that ENAQT claims an
intermediate point on can outperform both extremes. **This is a
mathematically different object from `ground_state_relaxation`
(TASK-0091's finding)** — confirmed by TASK-0095: `haken_strobl`'s
`γ→∞` limit is generated by `H`'s off-diagonals (classical rate-hopping
proportional to `|H_ij|²`), while `ground_state_relaxation` is dominated
by `H`'s diagonal/spectral structure (literal ground-state density) —
the two do not converge to each other, at any `γ`. Concretely: **do not
expect this task's γ-sweep to explain, reproduce, or validate BCR_ABL1's
0.731 ground-state result** — that would repeat the exact conflation
TASK-0095/TASK-0091's re-file already retracted once. This task answers
"does dialing coherence up or down change the CTQW-family score," a
complete, well-posed ENAQT question in its own right, independent of
whatever TASK-0102 finds about `ground_state_relaxation`'s meaningfulness.

## Done

- 2026-07-16, Implementer A. Added `analysis.coherence_sensitivity(H,
  bfactors, source, labels, gamma_scale, *, floor_scores=None, t_max=15.0,
  multipliers=(0.0, 0.5, 1.0, 2.0), flat_threshold=0.05, rtol, atol)`:
  sweeps `dephasing_sweep` at a caller-supplied calibrated `gamma_scale`
  (the exact `calibrate_kappa`/`anm_modes`/`mode_energetics` recipe
  `test_kras_g12c_dephasing_flat_survives_kappa_calibration` already
  validated), with `gamma=0` evaluated via the cheap exact `ctqw` limit
  (reusing TASK-0105's own established optimization) rather than paying
  for `haken_strobl`'s ODE solver at gamma=0. Every swept occupation
  vector is run through `diagnostics.classify_failure` (same call
  convention `operator_sweep` already established: `H`/`bfactors`/
  `floor_scores` passed through) so the classification is gated against
  TASK-0094's proximity floor, not just raw AUC spread.
- Classification: `COHERENCE_NOT_SIGNIFICANT` if the sweep is flat
  (`auc_range < 0.05` — `dephasing_sweep`'s own already-documented
  default, reused rather than inventing a second undocumented threshold,
  resolving this task's own Open Question) **or** if the floor-cleared
  status never changes across the sweep (geometry-confounded, per this
  task's own Acceptance Scenario 2); `COHERENCE_DEPENDENT_SIGNAL` if it's
  non-flat AND the floor-cleared status actually flips somewhere in the
  sweep; `None` (unresolved, not silently assumed insignificant) if the
  sweep is non-flat and no `floor_scores` were supplied.
- Extended `dephasing_sweep` with an opt-in `return_occ=True` (adds an
  `"occ"` key, list of per-gamma occupation vectors) -- backward
  compatible, existing callers/tests unaffected, needed because
  `classify_failure` requires the raw occupation vector, not just the
  scalar AUC `dephasing_sweep` already returned.
- Wired into `assemble_verdict_results` via a new optional `coherence_out`
  argument (same independently-omittable pattern as every other argument)
  -- contributes `coherence_auc_range`, `coherence_auc_at_gamma0`,
  `coherence_classification`. Wired into `verdict_template`: the three
  keys render in the existing headline block (alongside `AUC_ctqw_mean`/
  `AUC_heat_mean`), plus a new 5th decision-support line stating in prose
  whether coherence changes the verdict.
- **Real 3-target run** (`scripts/coherence_sensitivity_scan.py`, active-
  site multi-index source + TASK-0094's degree/euclid/hop floor stack,
  matching TASK-0105's `enaqt_gamma_sweep.py` convention):
  - **KRAS_G12C**: `auc_range=0.0155`, `is_flat=True`, floor=0.482, all
    4 points `NO_SIGNAL_IN_APO` (doesn't even clear chance) →
    `COHERENCE_NOT_SIGNIFICANT`. Cross-checked against the GDP-functional-
    source convention (`test_kras_g12c_coherence_sensitivity_reproduces_
    kappa_calibration`, real network fetch): `auc_range=0.0076`, same
    conclusion under a different, independently-validated source/cutoff
    choice.
  - **BCR_ABL1 / CARDIAC_MYOSIN — blocked, not silently skipped**:
    `superpose.calibrate_kappa`/`anm_modes` require *exactly* 6 near-zero
    rigid-body ANM modes (TASK-0005's own hardening); BCR_ABL1 has 7,
    CARDIAC_MYOSIN has 10, both raise before `gamma_scale` can be
    computed. TASK-0005's own Done section already predicted this exact
    failure mode for a "genuinely multi-chain/floppy-linker target" and
    flagged it as future work — now actually hit. Filed as [[TASK-0128]]
    (root cause -- floppiness vs. real disconnection vs. numerical
    threshold artifact -- is undetermined and out of this task's own
    scope; `calibrate_kappa` is TASK-0005's owned module) rather than
    patched inline. Full detail: `RESULTS.md`'s TASK-0099 section.
- Tests: `test_analysis.py::TestCoherenceSensitivity` (7 cases —
  gamma=0 exactness, one-diagnosis-per-point, flat-without-floor,
  non-flat-without-floor-is-unresolved, and 2 monkeypatched-propagator
  cases forcing the floor-gate's flip/no-flip branches deterministically
  rather than relying on a real interior-optimum reproduction);
  `TestDephasingSweep` +2 (`return_occ` on/off);
  `TestAssembleVerdictResults` +1 dedicated coherence-wiring test, plus
  `_real_outputs`/two existing "no N/A when everything populated" tests
  extended to include `coherence_out` (this task's own field is now part
  of "everything"); real-target `test_kras_g12c_coherence_sensitivity_
  reproduces_kappa_calibration` (Acceptance Scenario 3). All local:
  `.venv/bin/python3 -m pytest -q __WORK_IN_PROGRESS__/tests/
  test_analysis.py` — 50 passed; `test_report.py` — 35 passed (no
  regressions); `test_ground_state_relaxation_guard.py` — 8 passed (no
  new classical/heat co-occurrence introduced by the RESULTS.md addition).
- Not run through the whitelisted `pytest_local.py wip-all` preset in this
  session (already covered by that preset's directory glob, per TASK-0105's
  same note — not re-verified here to avoid re-triggering the
  multi-session-contention hang investigated earlier this session).
- **Post-completion audit against `REVIEW-panel-2026-07-16-v2` (written
  after this task's first pass landed, per the user's explicit request to
  re-check it):** the review flags `t_max` (Sec.2.2 — "unfixed and too
  short... a precondition for the physics, not hygiene," TASK-0108/0109's
  formal convergence check still TODO) and the seed cardinality (Sec.2.1 —
  up to ±0.3 AUC, no registered invariant) as unfixed project-wide gauges.
  The real-target script had used `t_max=8` (copied from the pre-review
  KRAS-only dephasing test, not re-derived). Spot-checked directly:
  `auc_range`/`is_flat`/`classification` all held steady across
  `t_max ∈ {8, 25, 100}` (a 12x range spanning TASK-0105's own
  already-established `t=25` convention) and across both seed conventions
  already cross-checked above — `COHERENCE_NOT_SIGNIFICANT` in every case.
  Updated `scripts/coherence_sensitivity_scan.py`'s default from `t_max=8`
  to `t_max=25` on this basis (the more defensible, TASK-0105-consistent
  choice) and re-ran KRAS_G12C as the primary reported result
  (`auc_range=0.0132`, unchanged conclusion). This task's own narrow claim
  ("does varying γ at a fixed reasonable clock change the outcome") is
  robust to both gauges; the review's broader, project-wide problem
  (absolute AUC-vs-floor comparisons shifting with seed/clock) is real,
  independently confirmed here (per-gamma diagnosis does flip between
  `BEATS_CHANCE_NOT_FLOOR`/`NO_SIGNAL_IN_APO` across `t_max`), and remains
  unresolved — out of this task's scope (TASK-0108/0109's job, plus a
  separate P0 seed-gauge fix neither task owns). No code redo was needed
  beyond the `t_max` default change and this documentation; test suite
  re-run clean after the change (`test_analysis.py` 50 passed).
- Registries updated post-completion: [[SEAM-0008]] (analysis-report schema
  assembly) noted the 3 new keys this task added to that same seam, status
  unchanged VERIFIED; [[INV-0005]] seeded for `coherence_sensitivity`'s
  `coherence_auc_range`/`coherence_classification`, with the `t_max`/seed
  spot-check above as real KNOB rows (not a placeholder); durable lesson
  promoted to `.ai/memory/shared/pitfalls.md` (P-0003) — spot-check a new
  metric's *classification*, not just its value, against the project's
  already-known KNOBs before shipping.
