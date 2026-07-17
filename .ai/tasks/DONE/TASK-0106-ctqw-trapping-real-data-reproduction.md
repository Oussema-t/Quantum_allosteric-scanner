# TASK-0106 Reproduce the CTQW-trapping finding on real BCR_ABL1 data

## Context

- ID: TASK-0106
- Title: `REVIEW-2026-07-13c` (synthetic-network mechanism test) found that
  `H_new`'s diagonal potentials (V_B/V_T/V_R/V_C/V_M) cause Anderson-like
  transport localization — the walk never leaves the seed's first contact
  shell — and that on a synthetic distal pocket, transport-preserving
  operators (`H10`, `H2`) score 0.58-0.59 AUC where `H_new` scores 0.12
  (anti-correlated) and a pure proximity baseline scores exactly 0. This
  task is the **real-data gate** the review itself requires before that
  finding changes any claim.
- Status: Done
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `.ai/reviews/REVIEW-2026-07-13c-ctqw-trapping-mechanism.md`,
  verifying a colleague's hypothesis (2026-07-13) that CTQW's proximity-
  like scoring is caused by trapping, not merely descriptive of it.
- Crit Ref: makes a specific, falsifiable, cheap prediction: on BCR_ABL1
  (1OPL apo / 5MO4 holo), CTQW through `H10_disorder_suppressed`,
  `H2_combinatorial_laplacian`, and `H_new` at reduced λ should beat
  `H_new`'s recorded 0.525 and should clear that target's proximity floor
  (0.565, per TASK-0094). `RESULTS.md` already records
  `AUC_apo_H10_baseline` = 0.558 vs `H_new` = 0.525 on this exact target —
  previously read as a noise-level gap ([[TASK-0093]]); this task checks
  whether the sign is real and whether it clears the floor properly
  scored (the recorded 0.558 was not evaluated against the floor as its
  own headline number).

## Intent Contract

- Outcome: a real-data answer to whether the synthetic mechanism
  (trapping degrades distal detection) reproduces on BCR_ABL1's actual
  topology and actual labeled pocket — the explicit gate the review
  requires before this changes any reported claim.
- In Scope:
  - fetch real BCR_ABL1 data (1OPL apo / 5MO4 holo, per `config/
    targets.yaml`) — this task requires network access the review's own
    session did not have
  - run `time_averaged_ctqw` through `H10_disorder_suppressed`,
    `H2_combinatorial_laplacian`, and `H_new` at reduced λ (at minimum
    λ=0.25, matching the review's synthetic sweep point), alongside the
    existing `H_new` default for direct comparison
  - report AUC on the real labeled pocket for each, checked against
    TASK-0094's proximity floor for this target (0.565)
  - report the same transport diagnostic the review used (⟨hop from
    seed⟩ or participation ratio at a fixed t) alongside AUC, not AUC
    alone — this is a mechanism claim, not just a leaderboard entry
  - this is **Tier-1 descriptive measurement only** (per TASK-0100's own
    tiering) — it does not select a new submission operator by itself
- Out Of Scope:
  - reselecting the submission operator — that decision is Tier-2-gated
    ([[TASK-0100]]), requires `frozen_context`/`leave_one_protein_out`
    across all 3 mandatory targets, and is explicitly not this task's
    call even if this task's result is strongly suggestive
  - running this on KRAS_G12C/CARDIAC_MYOSIN — BCR_ABL1 only, since it's
    the target both the review and the existing `RESULTS.md` gap concern;
    extending to the other 2 mandatory targets is a natural follow-up but
    not required to answer this task's specific question
  - amending `RESULTS.md`'s claims — that's a follow-up once this task's
    result is known, not this task itself
- Constraints And Invariants:
  - this is diagnostic measurement, not a frozen-config selection act —
    does not need `frozen_context`/LOPO gating (same reasoning already
    applied to TASK-0067/TASK-0100's Tier 1).
  - report the result **whichever way it comes out** — if the synthetic
    finding does NOT reproduce on real BCR_ABL1 topology, that is exactly
    as reportable as if it does (matches this project's "an honest NO is
    a publishable result" convention).
- Planned Validation: the measured AUCs + transport diagnostics
  themselves. Success is "the question is answered with real data," not
  "the synthetic finding is confirmed."

## In Progress

None

## TODO

- [ ] Fetch real BCR_ABL1 (1OPL/5MO4) data.
- [ ] Run `time_averaged_ctqw` through `H10`, `H2`, `H_new`(λ=0.25),
      `H_new`(default) on the real contact graph.
- [ ] Score each against the real labeled pocket; report AUC + transport
      diagnostic (⟨hop⟩ or PR) for each.
- [ ] Check each against TASK-0094's proximity floor for this target
      (0.565).
- [ ] Report whether the synthetic mechanism finding reproduces, and flag
      any deviation (e.g. if the real gap is smaller/larger/absent) as a
      finding in its own right, not a failure to force-match the
      synthetic result.

## Dependency

- `.ai/reviews/REVIEW-2026-07-13c-ctqw-trapping-mechanism.md` — the
  synthetic finding this task reproduces or falsifies on real data.
- [[TASK-0094]] (Done) — the proximity floor this task checks against.
- [[TASK-0093]] — reads this task's result before finalizing its own
  reconciliation; do not close TASK-0093 assuming this task's answer.
- [[TASK-0100]] — governs what this task's result is and isn't allowed
  to justify (Tier-1 measurement only, no operator reselection).

## Open Questions

- None yet — the prediction, targets, and comparison operators are fully
  specified by the review.

## Done

- 2026-07-14, Implementer A. Added `__WORK_IN_PROGRESS__/scripts/
  ctqw_trapping_reproduction.py`: `run_bcr_abl1_reproduction(lam_reduced=
  0.25)` fetches real BCR_ABL1 (1OPL/5MO4), scores `time_averaged_ctqw`
  through `H10_disorder_suppressed`, `H2_combinatorial_laplacian`,
  `H_new` at reduced λ, and `H_new` default, against the real labeled
  pocket, checked against TASK-0094's proximity floor, plus the review's
  own transport diagnostic (`metrics.ipr` as participation-ratio/N — the
  same quantity `select.py::focusing`'s own docstring already establishes
  as valid on an L1-normalised occupation vector, reused rather than a
  new formula invented — and occupation-weighted mean hop-from-seed, via
  `-baselines.hop_from_seed`).
- `H_new` at "λ=0.25" implemented as a uniform external scale on
  `build_H_new`'s own five default per-term coefficients (`lam_B=1.0,
  lam_T=2.0, lam_R=1.0, lam_C=0.5, lam_M=0.5` → all ×0.25), matching the
  review's own `H(λ) = L_norm + λ·ΣV` construction (one multiplier on the
  combined potential block, not a re-tuning of individual terms) —
  verified by test, not just described (`quarter - bare == 0.25*(full -
  bare)` exactly).
- **Seed-convention finding (real, not anticipated when this task was
  filed):** first attempt used the full active-site residue set as
  source (defensible on its own, and `time_averaged_ctqw` supports
  multi-index natively) — this reproduced the trapping *mechanism*
  (`H_new` markedly more localized than `H10`/`H2`) but gave a
  **completely different AUC picture** from `RESULTS.md`'s existing
  0.525/0.558 numbers, including a sign flip (`H_new` scoring *highest*
  of all four operators, 0.567). Switched to the single, sorted-first
  active-site index — `run_challenge.py`'s own established convention,
  the exact seeding those existing numbers were computed with — and
  confirmed this reproduces `AUC_apo_Hnew_default`=0.525 and
  `AUC_apo_H10_baseline`=0.558 **exactly**, byte-for-byte, before trusting
  any of the new numbers. This is the correct, comparable answer to what
  this task asks; the multi-index run is reported as a separate,
  real finding about seed-definition sensitivity, not discarded.
- **Real-data result (full detail in `RESULTS.md`, BCR_ABL1 section,
  dated 2026-07-14):**
  - Trapping mechanism reproduces cleanly: `H_new`'s PR/N (0.299) is
    5-6x `H10`/`H2`'s (0.056/0.054); `H_new`'s ⟨hop⟩ (0.89) is a quarter
    of theirs (3.96/4.46) — confirmed in **both** seed conventions
    (direction unchanged, magnitudes differ).
  - The predicted AUC consequence reproduces **only for `H10`**
    (0.558 > 0.525, the exact existing gap, now confirmed real not
    noise) — **not** for `H2` (0.389, lower) or reduced-λ `H_new`
    (0.463, lower — reducing the trapping potential made this operator
    *worse* here, the opposite of the review's synthetic prediction).
  - **None of the four operators clear the real proximity floor
    (0.565).** `H10`'s edge over `H_new` is real but not yet
    distinguishable from a proximity-driven result.
  - Verdict: **mixed, reported as such** — the mechanism (trapping) is
    robust and real on this target; its consequence for pocket-finding
    is not uniform across operators and is sensitive to a
    seed-definition choice (`INVARIANCE_PROTOCOL.md`: "which residue(s)
    count as the seed" was an implicit, previously-unexamined GAUGE
    choice — this task is the first place it visibly flipped a sign).
    Per this task's own Constraints ("report the result whichever way it
    comes out"), this is not softened toward either the review's
    prediction or a clean falsification.
- **Correction flagged 2026-07-16** (`.ai/reviews/REVIEW-panel-2026-07-16-v2.md`
  §2.2): `_transport_participation_ratio` = `1/(N·Σp²)` — **high PR means
  delocalized, low PR means localized.** This Done section's own numbers
  (`H_new` PR/N=0.299 vs. `H10`/`H2`'s 0.056/0.054 — `H_new` is the
  *higher* value) are reported above alongside language ("markedly more
  localized," line ~133) that reads the higher value as more localized —
  backwards for this metric as defined. The panel's own independent,
  gauge-fixed re-measurement (normalizing each operator by its hopping
  scale) still finds `H_new` genuinely more localized than `H10`/bare
  Laplacian (PR 1.3→3.8 vs. 14.7→83.7 and 23.5→48 across t=15→1500) — so
  the underlying **localization conclusion itself is not in question**,
  only whether *this task's own* PR/N numbers and narrative direction are
  internally consistent with each other. Not resolved here — re-checking
  which of (the reported PR/N values) or (the localized/delocalized
  prose) is the actual error is [[TASK-0119]]'s job, done alongside its
  own clock-gauge re-run, not silently corrected in this file without
  re-deriving the numbers.
- **Resolved 2026-07-16, [[TASK-0119]]**: neither the reported values nor
  this task's narrative direction was the error — **the panel's
  correction was itself mistaken**, based on assuming this task's
  `participation_ratio` field followed `analysis._transport_
  participation_ratio`'s convention. It does not. This script's own
  `transport_diagnostics` calls `metrics.ipr` (`sum(v_i^4)/sum(v_i^2)^2`,
  documented as "Inverse Participation Ratio of an eigenvector"), a
  **different formula with the opposite convention**: `ipr` is HIGH for
  localized, LOW for delocalized (verified numerically,
  `tests/test_transport_diagnostics_convention.py`, on delta/uniform
  extremes: `ipr(delta)=1.0`, `ipr(uniform)=1/N`) — exactly the reverse of
  `_transport_participation_ratio`'s HIGH=delocalized. This script's own
  docstring calling `ipr` "this codebase's own PR/N convention" is the
  actual bug (a mislabeling, not a computation error) — it conflated two
  differently-conventioned metrics that happen to share the phrase
  "participation ratio." Under `ipr`'s real, correct convention, this
  task's original prose (`H_new`'s higher value, 0.299, read as "markedly
  more localized" than `H10`/`H2`'s 0.056/0.054) was **directionally
  correct for the metric actually used** — nothing above needs a sign
  flip. The field is better read as "`ipr` (localization index, high =
  localized)" than "PR/N" going forward; not renamed here (no-silent-edit
  convention), flagged for whoever next touches this script.
- **Re-run under TASK-0119's per-operator clock (`t* = -ln(0.01)/gap`
  instead of the shared `T_MAX=15.0`), same seed convention as this
  task's own canonical run (single sorted-first active-site index — see
  TASK-0119's own caveat about TASK-0118 landing concurrently, below)**:
  `H_new_default` t*=23.8 (ipr 0.299→0.219, hop 0.89→1.08); `H_new_
  λ=0.25` t*=63.6 (ipr 0.449→0.204, hop 1.23→1.84); `H10` t*=29.0 (ipr
  0.056→0.035, hop 3.96→4.73); `H2` t*=57.8 (ipr 0.053→0.020, hop
  4.46→5.51). **The localization conclusion survives the clock fix**:
  even measured at each operator's own, much longer, proper convergence
  time, `H_new`'s ipr (0.22/0.20) remains ~6-10x `H10`/`H2`'s (0.035/
  0.020), and its hop-from-seed stays markedly lower — not a clock
  artifact. **Separately, the AUC ranking shifts**: `H10` now clears the
  real proximity floor (0.5652) at its own `t*` (AUC 0.568 > 0.565,
  `floor_cleared` False→True) where it did not at the shared `t_max=15`
  (0.558 < 0.565) — a real, small crossing, reported as its own finding,
  not merged with the localization result. Full detail, both re-runs:
  [[TASK-0119]]'s own Done section.
- Tests: `test_ctqw_trapping_reproduction.py` (6 cases) — `λ=1` exactly
  matches default `build_H_new`; `λ=0` gives the bare Laplacian; the
  λ-scaling is verified linear on the potential block, not just at the
  endpoints; transport-diagnostic edge cases (fully localized, uniform,
  a 2-node case with a known 1-hop answer).
- Validation: `.venv/bin/python3 -m pytest -q __WORK_IN_PROGRESS__/tests/
  test_ctqw_trapping_reproduction.py` — 6 passed. Real run output saved
  to `__WORK_IN_PROGRESS__/results_task0106/BCR_ABL1/reproduction.json`
  (the final, single-index-seed canonical run).
