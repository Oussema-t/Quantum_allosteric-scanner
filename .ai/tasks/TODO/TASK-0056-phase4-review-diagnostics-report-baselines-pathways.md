# TASK-0056 Phase 4 review (TASK-0009 `diagnostics.py` / TASK-0010 `report.py` / TASK-0011 `baselines.py` / TASK-0012 `pathways.py`)

## Context

- ID: TASK-0056
- Title: Code-Reviewer-overlay review of the Phase 4 cluster — the four
  modules that landed via parallel Implementer threads this session, none
  of which has any review coverage yet (checked: `.ai/reviews/` has a
  Foundation Record for TASK-0003–0005 and a filed-but-not-yet-run Phase 3
  task for TASK-0006/0007; nothing for TASK-0009–0012)
- Status: TODO
- Owner: Code Reviewer
- Claimed By: —
- Claimed At: —
- Source: filed while considering, at user request, which Reviewer threads
  should run checks based on this session's newly-adopted Seam/Invariance
  protocols — this gap was found in the course of that consideration, not
  named by the user directly.
- Scope: `__WORK_IN_PROGRESS__/src/allostery/{diagnostics,report,baselines,pathways}.py`
  + their test files. TASK-0008 (`analysis.py`) explicitly excluded — it
  already has an unusually thorough Done section (real KRAS_G12C
  benchmark, 268-test full-suite run) that substitutes for a first review
  pass; re-review it later if a dedicated pass still seems warranted.

## Intent Contract

- Outcome: a Review Record, same shape as
  `REVIEW-2026-07-07-foundation-0003-0005.md`, covering all four modules
  against their own Intent Contracts — same evidence-first method
  (read the module + tests in full, run tests for real including any
  network-gated ones, don't trust a skip).
- In Scope:
  - each module's Intent Contract vs. what actually shipped (same check
    Reviewer A ran for Foundation/is running for Phase 3)
  - **specifically for `baselines.py` (TASK-0011):** this is
    [[SEAM-0005]]'s floor-definition side — check whether `classify_failure`/
    verdict logic anywhere already conflates "beats chance" with "beats
    floor" now that the floor is no longer stubbed; report findings to
    that seam record, don't just note them in prose
  - **specifically for `report.py` (TASK-0010):** cross-check against
    [[SEAM-0004]] (`AUC_*_optimised` provenance) — this review can likely
    answer [[TASK-0055]]'s question directly while already reading the
    file closely, worth doing together rather than two separate reads
  - cross-module: do `diagnostics.py`/`report.py` consume `pathways.py`/
    `baselines.py` output in a way that assumes a specific shape neither
    side's own unit tests would catch (a seam smell per
    `SEAM_PROTOCOL.md`'s own list — "a module returns two things that
    'should' relate... with no test on the relation")
  - **[[SEAM-0008]] (found by [[TASK-0053]]'s sweep, 2026-07-11):**
    `report.verdict_template`'s expected flat keys
    (`AUC_apo_Hnew_default`, `most_impactful_term`, `mean_jacc20`, etc.)
    appear nowhere in real `analysis.py` output — only in
    `test_report.py`'s hand-built fixture. No assembly function converts
    `analysis.py`'s actual (nested) return shapes into what
    `verdict_template` expects. This review should either write that
    assembly function (or confirm it's deliberately the human
    report-writer's job, per `report.py`'s own "does not write the
    competence-map narrative" scope note, in which case say so explicitly
    and flip [[SEAM-0008]] to a documented non-issue rather than leaving
    it open indefinitely) and update the seam record either way.
- Out Of Scope: TASK-0008, already covered above; fixing anything found
  (files follow-ups, same as TASK-0047's pattern).
- Planned Validation: run each module's test file for real; interpret
  against Intent Contracts, not just green/red.

## In Progress

None

## TODO

- [ ] Read all four modules + their tests in full.
- [ ] Check each against its own Intent Contract.
- [ ] Run the tests for real (including any network/optional-dependency
      gated ones).
- [ ] Cross-check `baselines.py` against `SEAM-0005`, `report.py` against
      `SEAM-0004`/`TASK-0055` — report findings to those records directly.
- [ ] Check the diagnostics/report ↔ pathways/baselines cross-module
      consumption for unstated shape assumptions.
- [ ] Write `REVIEW-<date>-phase4-....md` under `.ai/reviews/`; file
      follow-up gap-bridging tasks if findings warrant.

## Dependency

- TASK-0009, TASK-0010, TASK-0011, TASK-0012 (all Done) — the modules
  under review.
- [[TASK-0050]]/[[TASK-0051]] — this review should apply the seam/
  invariance lens, not just ordinary code review, since two of its four
  modules are already named in open seam records.
- Precedent/format: TASK-0047, TASK-0048,
  `REVIEW-2026-07-07-foundation-0003-0005.md`.

## Open Questions

- Should this run before or after [[TASK-0048]] (Phase 3)? No hard
  dependency either way — recommend TASK-0048 first only because it was
  filed first and the user already deferred it once; not a technical
  blocker.

## Done

(not yet)
