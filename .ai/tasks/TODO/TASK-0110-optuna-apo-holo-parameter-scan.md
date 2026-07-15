# TASK-0110 Optuna parameter scan on real targets — apo scan (floor) vs. holo scan (ceiling)

## Context

- ID: TASK-0110
- Title: Use Optuna (new dependency) to search CTQW/propagator numerical
  parameters (`t_max`, `n_steps`, and `haken_strobl`'s `gamma` where
  applicable) on the real mandatory targets — an apo-only scan
  establishing a "floor," and a holo/label-informed scan establishing a
  "ceiling," per explicit user request.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: subtask of [[TASK-0108]], per explicit user request ("Optuna
  search for target systems. Apo scan => floor. Holo scan => ceiling.").

## Intent Contract — **interpretation flagged for confirmation before a large run starts**

The user's framing is terser than this task needs to execute safely;
this is my read of it, stated explicitly rather than silently assumed:

- **Apo scan ("floor")**: Optuna searches `t_max`/`n_steps`/`gamma`
  using an objective computed **without any pocket-label ground truth**
  — i.e., [[TASK-0109]]'s convergence-quality criterion (minimize
  numerical error / find the cheapest parameters that still pass
  convergence) rather than AUC. This is safe to run with no leakage
  concern (no label read at all) and establishes the *minimum valid
  parameter regime* usable in a real, undisclosed-answer deployment —
  "floor" in the sense of "the honest, non-cheating baseline parameter
  choice," analogous in spirit to `baselines.py`'s floor (a
  non-optimized-against-the-answer reference point), not identical to it.
- **Holo scan ("ceiling")**: Optuna searches the same parameters using
  real pocket-label AUC as the objective — the same concept as
  [[TASK-0046]]'s `ceiling_search`, but for CTQW's *numerical* parameters
  specifically (as opposed to `H_new`'s physical potential-weight DOF,
  which TASK-0046 already covers), and using a real optimizer (Optuna's
  default TPE sampler) instead of blind random search.
- **If this reading is wrong**, correct it before the real-target run
  starts — this is real compute + a new dependency, worth confirming the
  objective before spending either.

- Status: TODO
- In Scope:
  - add `optuna` as a new dependency for the research package — flagged
    explicitly (per [[TASK-0108]]'s shared Constraints: no dependency
    manifest currently exists for `__WORK_IN_PROGRESS__/src/allostery`;
    `requirements.txt` at repo root is backend-only). Create or extend
    whatever manifest is appropriate; do not rely on an ambient
    `pip install` alone.
  - an apo-only Optuna study per mandatory target (KRAS_G12C, BCR_ABL1,
    CARDIAC_MYOSIN), objective = [[TASK-0109]]'s convergence-quality
    metric, searching over a range informed by TASK-0109's synthetic
    power-law characterization (soft dependency — start with a
    reasonable range if TASK-0109 isn't done yet, but revisit the range
    once it is).
  - a holo-informed Optuna study per mandatory target, objective = real
    AUC against `labels.build_labels(...)`'s pocket, same parameter
    space.
  - report both studies' best trial + the full trial history (Optuna's
    own `study.trials_dataframe()` or equivalent) per target — per this
    project's "an honest NO is a publishable result" convention, a study
    that finds no real headroom (matching [[TASK-0046]]'s KRAS_G12C
    finding) is a valid, reportable outcome, not a failure to hide.
  - reuse `run_challenge.py`'s existing fetch/clean glue and
    `frozen_context`/labeling accessors where the holo scan needs
    ground-truth labels — do not re-derive fetch/label logic.
- Out Of Scope:
  - **this is explicitly Tier-1 diagnostic work, not Tier-2 operator/
    parameter selection** — per [[TASK-0100]]'s architecture decision,
    do not wire either scan's "best" result into `run_challenge.py`'s
    live defaults; that would require the same `frozen_context`/
    `leave_one_protein_out` gating TASK-0100 already mandated for any
    selection act, and is explicitly a separate, future task if the
    scans' results warrant it.
  - `H_new`'s own physical potential-weight parameters — already covered
    by [[TASK-0046]]; this task is CTQW's numerical parameters only.
  - inventing a new convergence criterion — use [[TASK-0109]]'s.
- Constraints And Invariants:
  - N=3 mandatory targets — per [[TASK-0100]], report per-target results
    plainly rather than pooling into one cross-target "best" number; a
    3-point optimization landscape is not a robust generalization claim
    regardless of which objective is used.
  - `ceiling_context()` (per [[TASK-0046]]'s precedent) should wrap the
    holo-informed scan's trials, matching this project's existing
    DEV/FROZEN state-machine discipline even for non-selection diagnostic
    work that reads ground truth.
- Planned Validation: both studies actually run to completion on all 3
  mandatory targets (or documented per-target if one is skipped and
  why), with the full trial history available for inspection — not just
  a single best-value summary.

## In Progress

None

## TODO

- [ ] Confirm the apo=floor/holo=ceiling interpretation above before
      starting the real-target run.
- [ ] Add `optuna` as a flagged, documented new dependency.
- [ ] Implement the apo-only (convergence-objective) Optuna study.
- [ ] Implement the holo-informed (AUC-objective) Optuna study, wrapped
      in `ceiling_context()`.
- [ ] Run both on all 3 mandatory targets; report per-target results +
      full trial history.
- [ ] Cross-check the holo-scan's best result against [[TASK-0046]]'s
      existing KRAS_G12C ceiling finding (0.525, near chance) — same
      target, different parameter axis; report agreement or disagreement
      explicitly rather than silently.

## Dependency

- [[TASK-0109]] — soft dependency (informs search range; not a hard
  block).
- [[TASK-0046]] (Done) — the existing ceiling-search precedent this
  extends to a different parameter axis; its KRAS_G12C real result is
  this task's cross-check target.
- [[TASK-0100]] — governs what this task's results are and aren't
  allowed to justify (Tier-1 only).

## Open Questions

- Exact Optuna sampler/pruner choice (TPE default vs. something else) —
  not pre-decided; Implementer's call, state the choice and why in Done.
- Where the new `optuna` dependency manifest should live — flagged in
  [[TASK-0108]]'s shared Constraints as a real gap (no existing
  research-package manifest), not pre-decided here.

## Done

(not yet)
