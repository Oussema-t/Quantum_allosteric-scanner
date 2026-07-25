# TASK-0165 Block the bootstrap CI on 3D spatial neighbourhoods, not sequence index

## Context

- ID: TASK-0165
- Title: `PANEL_REVIEW_2026-07-25.md` W6/V4 — `metrics.block_bootstrap_ci`
  blocks along residue **sequence index** order (`block_size=10`) to
  "preserve local spatial correlation." But pockets are spatially
  compact while being **sequence-scattered** — the dependence structure
  that actually matters is 3D-spatial, not sequence-adjacent. The
  current CIs therefore do not capture the real correlation structure.
  Same root mechanism as [[TASK-0158]]'s null defect (§2.3) — spatial
  autocorrelation the current construction doesn't model.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `PANEL_REVIEW_2026-07-25.md` §2.2/W6, §4/V4.
- Priority: **P1** — the review's own estimate is 1 day. Per the
  review's own honest framing: this makes the project's *negative*
  conclusions *safer* (real CIs would be wider, so "CI overlaps floor"
  findings are, if anything, understated), but makes any *positive*
  finding's CI less trustworthy than reported — directly relevant to
  whatever survives [[TASK-0158]]'s null fix.

## Intent Contract

- Outcome: a spatial-block variant of `block_bootstrap_ci` that blocks
  on 3D neighbourhoods (e.g., k-nearest-neighbour clusters by Euclidean
  distance, or a spatial grid partition — Implementer's own call
  between the two, state reasoning) rather than sequence-index runs of
  `block_size` consecutive residues.
- Why required: the current CI construction assumes the wrong
  dependence axis; a referee who checks this will find the same
  mismatch the null-defect audit already demonstrated for permutation
  nulls.
- In Scope:
  - New spatial-block bootstrap function, same call signature/return
    shape as the existing `block_bootstrap_ci` (drop-in, so existing
    callers can switch with a one-line change) — Implementer's own call
    on exact block-construction method, state reasoning.
  - Re-compute CIs for the program's **currently-surviving or
    near-surviving** positives (coordinate with [[TASK-0158]] — use
    whichever set of results is current after that task's null fix
    lands) under the spatial-block method; report old vs. new CI width
    side by side.
  - Confirm the expected direction: spatial blocking should widen CIs
    relative to sequence blocking for spatially-compact-scoring
    observables (a sanity check the fix targets the right mechanism,
    mirroring [[TASK-0158]]'s own white-noise-control validation step).
- Out Of Scope:
  - Re-computing every CI in the project — focus on the
    currently-reported positives/near-positives, not the full negative
    catalogue (negatives get *safer*, not *less safe*, under the
    correct method — lower priority to re-run).
  - Any change to the point-estimate scoring itself — CI construction
    only.
- Constraints And Invariants: must reduce to (approximately) the
  existing sequence-block behavior on a synthetic control with no real
  3D spatial structure (e.g., residues placed on a 1D line) — a
  regression sanity check that the new method isn't just "always wider."
- Planned Validation: side-by-side CI widths (sequence-block vs.
  spatial-block) for the surviving-positive set; a synthetic no-spatial-
  structure control confirming the methods converge when there's nothing
  spatial to capture.

## TODO

- [ ] Build spatial-block bootstrap, drop-in signature.
- [ ] Synthetic-control regression check (1D line case).
- [ ] Re-compute CIs for currently-surviving/near-surviving positives
      (post-[[TASK-0158]]).
- [ ] `RESULTS.md` section: old vs. new CI width, per affected cell.

## Dependency

- [[TASK-0158]] (TODO) — determines which results are still "surviving
  positives" worth re-computing CIs for; coordinate ordering.

## Open Questions

- Exact spatial-block construction (k-NN cluster vs. grid partition) —
  Implementer's own call, state reasoning at pickup.

## Done

(not yet)
