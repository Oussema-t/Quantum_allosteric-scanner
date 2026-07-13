# TASK-0099 Wire a genuine coherence-sensitivity metric into the scored verdict path

## Context

- ID: TASK-0099
- Title: Promote `dephasing_sweep` (already implemented, never wired into
  the reported pipeline) into `assemble_verdict_results`/
  `verdict_template`, so at least one reported quantity in `RESULTS.md`
  would actually change if quantum phase/coherence were randomized away
  — and classify whether coherence contributes real signal, per target,
  once the proximity floor is applied.
- Status: TODO
- Owner: Implementer
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

## Done

(not yet)
