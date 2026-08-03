# TASK-0190 The real-pocket-Rg-matched null — the external review's actual P0, never executed

## Context

- ID: TASK-0190
- Title: run `nulls.compact_patch_matched` with `target_rg` set to each
  target's **measured real pocket** radius of gyration, and re-run `dcc_low`
  (CARDIAC_MYOSIN, PTP1B) and `T(E=0)` (BCR_ABL1) against it, reporting
  scattered / ball / matched side by side.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `REVIEW-panel-2026-07-28-external.md` §2.1 (verbatim ask, still
  outstanding); Reviewer thread, 2026-08-03, finding F2.
- Priority: **P0 — this decides whether the submission's central sentence is
  "a rigorous negative" or "a rigorous negative with one undecided cell." It
  is the single highest-leverage open item before the 2026-08-08 freeze.**
- Dependency: none. Every piece of machinery required already exists and is
  tested.

## Why this matters

The external review's §2.1 ask was explicit:

> *"Measure each target's real pocket Rg, re-run the `dcc_low` and `T(E=0)`
> cells with `target_rg=<measured>`, report all three p-values (scattered /
> ball / matched) side by side. That is the honest interval."*

`compact_patch_matched` has exactly two non-test call sites. **Both** set:

```python
target_rg = radius_of_gyration(coords, patch)   # detection_curve:182, zero_plant:161
```

…where `patch = select_distal_patch(...)`, which draws its candidates from
`nulls.compact_patch` itself (`plant.py:244`). The null is therefore matched
to a compact ball. **"Matched ≈ compact" is true by construction, not a
finding** — yet `RESULTS.md`'s "Compact vs. Rg-matched null: empirically
indistinguishable in this regime" presents it as "an answer to part of the
external review's own over-correction question," and commit `92aa669`'s
subject line reads "dispute settled."

Meanwhile [[TASK-0167.003]] Part B measured the number that shows the review
was right **on real data**: every real pocket sits at the **97th–100th
percentile** of the compact null's own Rg distribution.

| Target | Real pocket Rg (Å) | Compact-null percentile |
|---|---|---|
| KRAS_G12C | 8.49 | 1.000 |
| BCR_ABL1 | 7.45 | 0.968 |
| CARDIAC_MYOSIN | 9.63 | 1.000 |
| PTP1B | 7.97 | 1.000 |
| GLUCOKINASE | 8.69 | 1.000 |
| CASPASE1 | 6.42 | 0.997 |
| CASPASE7 | 10.84 | 1.000 |

Real pockets are systematically **more dispersed** than the null they are
tested against. A null matched to `target_rg = 9.63` is a materially looser
draw than a k-NN ball — which is the entire content of the review's
over-correction claim, now confirmed on this project's own targets.

**So `dcc_low`'s corrected p-values — 0.060 (CARDIAC_MYOSIN) and 0.019
(PTP1B) — remain exactly where the review left them: undecided, not dead.**
[[TASK-0161]]'s "zero corrected-null-surviving positives program-wide"
headline, and [[TASK-0184]]'s narrative, both currently inherit an unresolved
null. The measurement that resolves it costs an afternoon.

## Intent Contract

- Outcome: a three-column p-value table (scattered / ball / **real-pocket-Rg
  matched**) for `dcc_low` on CARDIAC_MYOSIN and PTP1B and `T(E=0)` on
  BCR_ABL1, with an explicit verdict on whether
  `PANEL_REVIEW_2026-07-25.md` §5.3's pre-registered falsification statement
  still fires under a correctly-specified null.
- Why required, not assumed: the falsification statement fired against
  [[TASK-0158]]'s ball null. If that null is 2–5× too strict for the label
  geometry it is applied to — which Part B now shows on real data — the
  statement fired against a mis-specified alternative, and the program's
  headline is wrong in the *safe* direction, which is still wrong.
- In Scope:
  - Per target, take `target_rg` from the **real pocket** (`build_labels(...)
    .pocket`), not from a synthetic patch. Part B already computed these;
    recompute rather than copy, as a cross-check.
  - Re-run `dcc_low` at [[TASK-0149]]'s established `k_modes` grid on
    CARDIAC_MYOSIN + PTP1B; re-run `T(E=0)` on `L` on BCR_ABL1
    ([[TASK-0145]]'s unresolved cell, never re-tested under any corrected
    null — the review calls it "the only cell that has never been fairly
    tested in either direction").
  - Report all three nulls side by side for every cell. Never substitute one
    for another, never report only the most favourable.
  - Record the rejection-sampling acceptance rate and any `RuntimeError`
    infeasibility per target — at `target_rg` ≈ the 100th percentile of the
    compact distribution, `compact_patch_matched` may reject heavily or fail.
    **If it cannot draw at the real Rg, that is a first-class finding**: it
    means no compact-family null can model these pockets and the null
    specification itself needs rethinking. Report it, do not widen `tol`
    silently to make it succeed.
- Out Of Scope:
  - Changing [[TASK-0158]]'s default null anywhere in the register. This task
    measures; a convention change is a separate, later decision.
  - Re-running the full 226-cell register. Three cells decide the question.
  - The multiplicity budget refresh — that is [[TASK-0191]].
- Constraints And Invariants:
  - `tol` stays at the established 0.35 unless a documented, justified reason
    to change it is recorded **before** seeing any p-value.
  - Pre-register, in this file, before running: *what result would count as
    `dcc_low` surviving.* Write it down first.
  - Under no circumstance may the matched null be reported alone.
- Planned Validation:
  - Sanity: the matched null's own draw-Rg distribution must actually centre
    on `target_rg`. Verify directly, do not assume rejection sampling worked.
  - Ordering check: p(scattered) ≤ p(matched) ≤ p(ball) is the expected
    ordering given Part B's geometry. If the observed ordering violates it,
    stop and diagnose — that would indicate a bug, not a finding.

## In Progress

—

## TODO

- [ ] Write the pre-registered survival criterion into this file. **Before running anything.**
- [ ] Measure real pocket Rg for CARDIAC_MYOSIN, PTP1B, BCR_ABL1 (cross-check vs. Part B).
- [ ] Verify `compact_patch_matched` can draw at those Rg values; record acceptance rates.
- [ ] Re-run `dcc_low` (CARDIAC_MYOSIN, PTP1B) — three nulls, side by side.
- [ ] Re-run `T(E=0)` on `L` (BCR_ABL1) — three nulls, side by side.
- [ ] Verdict on §5.3's falsification statement under a correctly-specified null.
- [ ] Hand the verdict to [[TASK-0184]] — it changes the opening paragraph either way.

## Dependency

- [[TASK-0158]] (Done) — `nulls.compact_patch`/`compact_patch_matched`.
- [[TASK-0167.003]] (Done) — Part B's real-pocket Rg measurements.
- [[TASK-0149]], [[TASK-0151]] (Done) — the `dcc_low` cells.
- [[TASK-0145]] (Done) — the BCR_ABL1 `T(E=0)` cell.
- Feeds: [[TASK-0161]] (budget headline), [[TASK-0184]] (narrative).

## Open Questions

- If `dcc_low` survives on one target and not the other, what is the honest
  report? The pre-registered statement named **both**. Decide the reading
  rule before seeing the numbers, not after.
- Real pockets sit at the 97th–100th percentile of the compact null. Is a
  compact-family null the right family **at all**, or does the right null
  need to model surface concavity directly (the review's `surf_frac` axis)?
  Out of scope here; name it for the forward proposal if the matched null
  turns out to be infeasible at real Rg.

## Done

—
