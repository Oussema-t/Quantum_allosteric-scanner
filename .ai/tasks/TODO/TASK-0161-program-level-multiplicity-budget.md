# TASK-0161 Compute and publish the program-level multiple-comparison budget

## Context

- ID: TASK-0161
- Title: `PANEL_REVIEW_2026-07-25.md` W4/V2 — every task applies
  Bonferroni *within its own family*, but nobody has accounted across
  the whole program. The review's own conservative count: a 96-cell
  operator sweep + 24-cell lowmode grid + 22-cell generalization grid +
  9 transport cells + 7-target chiral + 7-target closure + 3-target
  ENAQT×8γ + H2/spectral/entanglement/transfer-entropy/co-participation/
  percolation cells — **on the order of 200+ scored cells against ~7
  answer keys.** At α=0.05 that predicts ~10 spurious "significant"
  cells; the project currently reports 3–4 surviving positives. The
  review's own framing: *"the number of positives found is not clearly
  in excess of what the testing volume alone would produce"* — an
  uncomfortable but honest reading that the project should state itself
  rather than let a referee compute.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `PANEL_REVIEW_2026-07-25.md` §2.2/W4, §4 action item 4, V2.
- Priority: **P0** — the review's own estimate is ½ day, and stating
  this yourself converts the strongest available criticism into a
  demonstration of rigor rather than something a referee discovers.

## Intent Contract

- Outcome: a single, auditable enumeration of **every scored cell in the
  entire program** (every task that computed a p-value or AUC-vs-null
  comparison against a real target's labels, across every operator,
  target, and parameter-grid point), with a total count, the
  corresponding α=0.05 expected-false-positive count, and an honest
  comparison against the number of positives actually reported.
- Why required: this is exactly the arithmetic a referee will do; doing
  it first and publishing it is stronger than being caught not having
  done it, per the review's own explicit framing.
- In Scope:
  - Walk every Done task under `.ai/tasks/DONE/` that reports a
    p-value/permutation-null/Bonferroni result against real target
    labels; tabulate target × operator × parameter-grid-point count per
    task.
  - Total cell count, compared against the review's own ~200+ estimate
    (confirm or correct it with the actual enumeration — don't just
    assert the review's number is right).
  - Expected false positives at α=0.05 (`0.05 × N_cells`) and at each
    Bonferroni-corrected α actually used in the program.
  - Honest count of actually-reported "surviving" positives (per
    [[TASK-0158]]'s corrected-null re-run, if that has landed by the
    time this runs — coordinate, don't duplicate; if not yet landed,
    report against the pre-correction numbers and flag explicitly that
    this budget will need updating once TASK-0158 lands).
- Out Of Scope:
  - Re-running any analysis — pure enumeration and arithmetic over
    already-reported results.
  - Building a new global correction scheme (e.g., a single program-wide
    Bonferroni threshold applied retroactively) — that is a much larger
    methodological decision than this task's own scope; report the
    numbers and let the write-up phase decide how to frame them.
- Constraints And Invariants: enumerate from the actual Done task files,
  not from memory or the review's own estimate — verify the count
  directly.
- Planned Validation: a reproducible table (task → target(s) → cell
  count), a grand total, and the two comparison numbers (expected vs.
  observed positives) in `RESULTS.md`.

## TODO

- [ ] Enumerate every Done task with a real-target p-value/null
      comparison; tabulate cell counts.
- [ ] Grand total; compare against the review's own ~200+ estimate.
- [ ] Expected-false-positive arithmetic at α=0.05 and at the program's
      actually-used Bonferroni thresholds.
- [ ] Honest observed-positive count (coordinate with [[TASK-0158]]'s
      corrected-null results if available).
- [ ] `RESULTS.md` section stating the budget plainly, written for a
      referee to read directly.

## Dependency

- [[TASK-0158]] (TODO) — if landed first, use the corrected-null
  positive count; if not, report against pre-correction numbers and flag
  this budget as provisional.

## Open Questions

- None — this is enumeration and arithmetic over existing, already-Done
  results.

## Done

(not yet)
