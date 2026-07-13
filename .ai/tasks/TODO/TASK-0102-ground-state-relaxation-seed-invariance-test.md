# TASK-0102 Is `ground_state_relaxation`'s BCR_ABL1 result seed-dependent, or just "the minimum has to be somewhere"?

## Context

- ID: TASK-0102
- Title: Test whether TASK-0091's BCR_ABL1 finding (`ground_state_relaxation`
  clears the proximity floor, AUC 0.7315) reflects genuine active-site→
  pocket coupling, or is an artifact of `H_new`'s ground state being an
  essentially fixed, seed-independent feature of the structure that
  merely happens to sit closer to the pocket than to the active site on
  this one protein.
- Status: TODO
- Owner: Implementer
- Source: user question, 2026-07-13 — "is it possible that the ground
  state relaxation 'accidentally' is localised somewhere near the distal
  pocket... it's not a meaningful physics contribution other than
  'potential minimum has to be SOMEWHERE on the protein'?" Plus: "can we
  build a clear discriminating test where we construct a small enough
  network, where we manipulate the potential to have a minimum away from
  nodes having the characteristics of an active site and those having
  the characteristics of a drug site?"

### Why this concern is concrete, not speculative (checked against real code)

`ground_state_relaxation(H, t, source)` computes `[exp(-Ht) p0]`, `p0`
uniform over `source`. Expand in `H`'s eigenbasis:
`exp(-Ht) p0 = Σ_k exp(-w_k t) <v_k|p0> v_k`. As `t` grows, this is
dominated by the **smallest** `w_k` term — for large enough `t·(gap)`
(gap = difference between the two smallest eigenvalues), the *shape* of
the result converges to the ground eigenvector `v_0` **regardless of
`p0`** (i.e. regardless of `source`/the active site), up to an overall
scalar that normalization removes. Every call site
(`quantum_vs_classical`, `benchmark`, `gnm_cutoff_weight_sweep`) uses the
same default `t_max=15.0`. Whether 15.0 is "converged" or "still
seed-sensitive" for `H_new`'s real spectral gap on BCR_ABL1 has never been
checked — `quantum_vs_classical`'s own docstring only asserts
"representative," it does not demonstrate convergence. If it *is*
converged, TASK-0091's finding carries **zero information** about the
active site at all — it would be identical for literally any seed choice,
and "beats the proximity floor" would just mean "the ground state's fixed
location happens to be farther from the active site than a typical
random point, and the floor's own denominator (distance from seed) is
low in exactly the region the ground state occupies." That is precisely
the accidental-minimum hypothesis, restated in exact linear-algebra terms.

## Intent Contract

- Outcome: a decisive answer, on real data first and (if warranted) on a
  fully-controlled synthetic network second, to whether
  `ground_state_relaxation`'s occupation pattern actually depends on
  which residues are used as the seed — and, separately, whether its
  proximity to a candidate pocket reflects genuine coupling to the seed
  or is explainable purely by the potential landscape's shape, independent
  of any seed.
- In Scope, ordered cheapest/most-decisive first:
  - **(a) Real-data seed-invariance check (do this first, cheap).** On
    BCR_ABL1's real, already-cached `H_new` (TASK-0091's cache), rerun
    `ground_state_relaxation` with the seed moved to several different,
    arbitrary residue sets (not the real active site) — including at
    least one seed on the *opposite* side of the protein from the real
    active site. Compare the resulting occupation vectors (Pearson/
    Spearman correlation, or simpler: does the top-20 occupancy set
    change at all). **If correlation ≈ 1 across seeds, TASK-0091's
    finding is seed-independent — report this plainly, it invalidates
    reading 0.7315 as evidence of active-site-to-pocket coupling,
    regardless of how the floor math came out.** If occupancy changes
    meaningfully with seed, that's evidence of genuine, if partial,
    seed-dependence, and motivates part (b).
  - **(b) Eigenvalue-gap check.** Compute `H_new`'s actual spectral gap
    (`w_1 - w_0`) for BCR_ABL1 and evaluate `exp(-gap · t_max)` — states
    numerically how converged the real computation was, explaining *why*
    (a) came out the way it did rather than leaving it as an unexplained
    empirical fact.
  - **(c) Synthetic discriminating network (build only if (a) is
    ambiguous, or to corroborate a clear (a) result with full ground
    truth).** Construct a small (~20-40 node) synthetic graph with three
    designated, non-overlapping node groups: an "active-site" set `A`, a
    "drug-site" set `B` at a controlled graph-distance from `A` (build
    both a proximal and a distal variant), and filler nodes. Build an
    `H_new`-style composite operator (Laplacian + `V_B`/`V_T`/`V_R` style
    terms) with the potential's true global minimum **deliberately
    engineered at a third location `C`**, disjoint from both `A` and `B`,
    with no designed coupling between `A` and `C`. Run
    `ground_state_relaxation` seeded at `A` and confirm the ground state
    correctly concentrates at `C` (not `B`) — this is the negative
    control proving the pipeline doesn't spuriously credit `B` just for
    being "the candidate pocket." Then build a second variant where the
    minimum is intentionally placed at (or coupled through a designed
    channel toward) `B`, and confirm the same pipeline correctly detects
    it — the positive control. A pipeline that cannot distinguish these
    two constructed cases has no discriminating power at all, independent
    of what any real protein shows.
- Out Of Scope: re-running TASK-0091's full real pipeline from scratch —
  reuse its cached `H_new`/occupancy arrays for part (a); building a full
  benchmark suite of synthetic networks (one clean pair, positive +
  negative control, is sufficient to answer the discriminating-test
  question, not a parameter sweep of synthetic topologies).
- Acceptance Scenarios:
  - Given BCR_ABL1's real `H_new` and at least 3 distinct seed choices
    (including the true active site and at least one antipodal
    arbitrary set), when `ground_state_relaxation` runs on each, then
    this task states explicitly whether the resulting occupancy patterns
    are effectively identical (seed-independent, invalidating the
    active-site-coupling reading) or meaningfully different
    (seed-dependent, supporting it) — a number (correlation), not a
    vibe.
  - Given the synthetic negative-control network (minimum engineered
    away from both `A` and `B`), when the pipeline runs, then it does
    **not** report `B` as floor-clearing/high-occupancy — if it does,
    that is a pipeline bug or a floor-design flaw, not a real finding,
    and must be reported as such.
  - Given the synthetic positive-control network (minimum engineered at/
    coupled to `B`), when the pipeline runs, then it **does** correctly
    identify `B`.
- Constraints And Invariants: this task's job is to determine
  meaningfulness, not to fix anything — if (a) shows seed-independence,
  that finding gets written into `RESULTS.md` as a correction to how
  TASK-0091's result should be read (cross-reference, don't silently
  edit TASK-0091 itself), following this project's established
  no-silent-overwrite convention (TASK-0095's own precedent).
- Planned Validation: the three ordered checks above are themselves the
  validation; report the outcome of (a) before deciding whether (c) is
  needed at all.

## Dependency

- Reuses TASK-0091's cached `H_new`/occupancy data for BCR_ABL1 (part a).
- Directly informs how TASK-0101's ground-state-propagator column (once
  amended, see that task) should be interpreted — read together, not
  blocking each other.
- Related to TASK-0092 (holo diagnostic comparison) — see the user's
  separate question about holo comparisons, addressed there: holo
  comparison is a *different*, complementary check (does the same
  pattern reproduce on an independently-solved structure) and does not
  substitute for the seed-invariance check here (a static ground-state
  artifact would likely reproduce on both apo and holo structures too,
  since both share the same fold — holo agreement alone would not
  distinguish real coupling from a shared static artifact).

## Open Questions

- If part (a) shows *partial* seed-dependence (neither ≈1 nor clearly
  low correlation), what threshold separates "real enough" from
  "mostly artifact"? Don't invent one silently — report the actual
  correlation number and reason about it explicitly in this task's Done
  section, flag for Architect input if genuinely ambiguous.

## Done

(not yet)
