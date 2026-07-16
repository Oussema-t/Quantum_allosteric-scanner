# TASK-0118 Fix the seed gauge: one convention, registered invariant, re-run floor/ceiling/actual

## Context

- ID: TASK-0118
- Title: Declare and enforce a single CTQW/GSR seed convention across
  `run_challenge.py`, `ceiling.py`/`ceiling_search_batched.py`, and every
  other scoring call site; register it as an invariant; re-run
  floor/ceiling/actual for all 3 mandatory targets under that one
  convention; correct `COMPETENCE_MAP.md`'s "ceiling below floor" claim.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `.ai/reviews/REVIEW-panel-2026-07-16-v2.md` §2.1, §5 P0-1 — the
  panel's single highest-priority item ("reverses the central claim").
- Priority: **P0 — this week.** Blocks every floor/ceiling/actual number
  currently in `COMPETENCE_MAP.md`/`RESULTS.md`.
- **Dependency status, 2026-07-16: [[TASK-0090]] landed.** `select.py`'s
  `_hop_distances_from_source`/`ballistic_exponent` (multi-source BFS) and
  `source_specificity` (the actual crash site -- not `ballistic_exponent`
  as first assumed, checked by execution) are fixed and validated against
  real KRAS_G12C data (full 18-residue active-site array through
  `unsupervised_score`, finite differentiated scores, no crash). This task
  is now **unblocked and ready to start** -- the "claim TASK-0090 as this
  task's own first step" fallback in In Scope below no longer applies.

## Intent Contract

- Outcome: (1) `run_challenge.py`'s single-residue seed workaround
  (`source = int(np.sort(active_site_idx)[0])`, a TASK-0090 crash
  workaround, not a physics choice) is replaced by real multi-index
  seeding, unblocked by [[TASK-0090]]'s fix to `select.py`; (2) one
  seed convention is chosen and used everywhere — the panel recommends
  an **incoherent mixture over the active-site residues** (a coherent
  18-residue superposition asserts a specific relative phase with no
  biophysical basis; an incoherent mixture is the defensible object);
  (3) an `.ai/invariants/INV-XXXX` record is filed classifying seed
  definition as a GAUGE, closing the gap both `[[Q-0003]]` and
  `EXECUTION_PLAN.md`'s 5bbcdc4 note flagged and left unresolved; (4)
  floor (TASK-0094's baselines), ceiling (TASK-0046/TASK-0082), and
  actual (`run_challenge.py`'s live run) are all re-computed for
  KRAS_G12C, BCR_ABL1, and CARDIAC_MYOSIN under this one convention —
  not compared across the old mixed conventions again; (5)
  `COMPETENCE_MAP.md` is corrected from "ceiling below floor" /
  "the strongest evidence gathered" to **undetermined→recomputed**,
  citing this task, not silently overwritten (this project's standing
  no-silent-overwrite convention, per TASK-0104's precedent).
- In Scope:
  - Hard dependency: [[TASK-0090]] must land first (`select.py`'s
    multi-index crash) — do not route the seed convention around that
    bug again; if TASK-0090 is not yet claimed, claim it as this task's
    own first step rather than waiting idle.
  - The panel's own validation-strategy row (§6): sweep
    `source = {1, k-subset, full-array, incoherent-mixture}` × all 3
    targets: "AUC spread > 0.1 → it is a SIGNAL, not a gauge, the
    pipeline has no defined initial condition (current evidence: ≈0.3 →
    already failed)." Run this sweep explicitly as part of choosing and
    justifying the final convention, not skip it because the panel
    already flagged the likely answer — confirm on the real targets,
    do not assume the synthetic estimate transfers.
  - Explicitly reject the framing that fixing the seed produces a new
    *positive* claim. Per the review (§2.1): the other thread's
    "ceiling 0.524 clears the array floor 0.482 by +0.042" splices
    TASK-0046 (ceiling) with TASK-0093 (floor) — two different runs,
    different cutoff/label context. Report whatever the single-convention
    re-run actually finds — do not pre-decide it is a positive or a
    negative before running it.
- Out Of Scope:
  - The clock fix ([[TASK-0119]]) — separate gauge, separate task, do
    not conflate a seed-convention re-run with a t_max re-run in the
    same pass; if both land around the same time, the final headline
    re-run should use both fixes together and say so explicitly, not
    silently attribute a combined effect to only one.
  - The potential renormalization ([[TASK-0121]]) — different confound
    (diagonal contamination vs. observable contamination per §2.4),
    separate task.
- Constraints And Invariants:
  - Every floor/ceiling/actual number this task reports must cite which
    seed convention produced it — no bare number without that label,
    per this project's own GAUGE/KNOB/SIGNAL discipline.
  - `ceiling_context()`/`frozen_context()` gating (per TASK-0046/TASK-0100
    precedent) applies to the ceiling/actual re-runs the same as before —
    this task does not relax any existing leakage discipline.
- Planned Validation: the sweep in "In Scope" above, plus a full re-run
  of floor/ceiling/actual for all 3 targets under the chosen convention,
  reported with the seed-convention label attached to every number.

## In Progress

None

## TODO

- [ ] Claim/verify [[TASK-0090]] is landed (multi-index `select.py` fix)
      before starting — hard dependency, do not route around it.
- [ ] Run the seed-convention sweep (`{1, k-subset, full, incoherent
      mixture}` × 3 targets) on real data; report the AUC spread.
- [ ] Decide the final convention (panel recommends incoherent mixture);
      state the decision and why in Done.
- [ ] File `.ai/invariants/INV-XXXX` classifying seed definition as GAUGE.
- [ ] Re-run floor (TASK-0094 baselines), ceiling (TASK-0046/0082 methodology),
      and actual (`run_challenge.py`) for KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN
      under the one chosen convention.
- [ ] Correct `COMPETENCE_MAP.md`: replace "ceiling below floor"/"strongest
      evidence gathered" with the honest re-run result, framed as
      undetermined→recomputed, additive per the no-silent-overwrite
      convention (cite this task by ID).

## Dependency

- [[TASK-0090]] — hard blocker, must land first.
- Feeds [[TASK-0119]] (the clock fix should ideally use this task's
  chosen seed convention in its own re-run, not the old mixed one).
- Feeds [[TASK-0126]] (H13 ceiling comparison should also use the
  post-fix convention, not restart the confusion).

## Open Questions

- Whether the incoherent-mixture seed changes `select.py`'s own scoring
  formulas (uniform mass split, per `propagators.py`'s existing
  convention) or needs a distinct implementation — Implementer's call,
  state the choice and why in Done.

## Done

(not yet)
