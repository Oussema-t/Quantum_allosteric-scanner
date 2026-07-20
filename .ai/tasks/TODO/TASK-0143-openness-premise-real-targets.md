# TASK-0143 Coordinated-closure graph-openness premise on real targets (HYP-P10)

## Context

- ID: TASK-0143
- **Renumbered 2026-07-20 (Architect/Planner)**: filed by the incoming
  review batch as `TASK-0139`, which collided with an already-existing,
  unrelated, already-committed `TASK-0139` (KRAS_G12C learnability
  reclassification, filed 2026-07-19/20 by this Architect/Planner
  thread). Renumbered to the next free ID; every cross-reference in
  [[TASK-0140]]/[[TASK-0141]]/[[TASK-0142]] updated to match. No content
  changed beyond the ID/title and the cross-references.
- Title: Test whether real holo-defined cryptic pockets carry the
  "near-in-3D-space / far-on-apo-contact-graph" coordinated-closure
  signature — the load-bearing premise behind the entire loop /
  multi-site-closure family ([[HYP-P10]], [[HYP-P9]], [[HYP-P12]]).
- Status: TODO
- Owner: Implementer (Oussama: build + run — no physics judgement needed
  to execute; the acceptance criterion below is fully pre-registered).
- Source: `REVIEW-panel-2026-07-20` (new-observable batch) §"multi-site
  closure". Reference implementation delivered this batch as
  `closure_test.py` (`openness_signature`, `graph_dist_matrix`) — port
  into `src/allostery/` per the port-don't-cross-import convention.
  **Flagged 2026-07-20 (Architect/Planner): `closure_test.py` is not
  actually present anywhere in this repo or the applied review batch**
  (checked directly, `.ai/reviews/2026-07-20/` contains no `.py` files)
  — lowest risk of the four new tasks, since this Intent Contract
  already spells out `openness_signature`'s exact formula (mean pairwise
  apo graph-hop / mean pairwise Euclidean distance among pocket
  residues) in full; buildable directly from this file without the
  reference script.
- Priority: **P0 — highest information-per-hour item in this batch.**
  Classical, no quantum, ~½ day. **Gates [[TASK-0140]]/[[TASK-0142]]**:
  if this premise fails, the chiral and topological observables have no
  non-proximity loop to detect and will collapse to the floor.

## ⚠️ Before implementing — this is NOT the existing openness gate

Do not conflate this with `superpose.cryptic_openness_gate` /
`cumulative_overlap` ([[TASK-0059]], [[TASK-0120]]). That gate asks a
*dynamics* question: is the apo→holo displacement spanned by the soft ANM
modes. **This task asks an orthogonal *structural-graph* question**: are
the pocket residues Euclidean-near but graph-hop-far in the apo contact
graph (i.e. the cleft is open, so the apo graph doesn't "know" they
belong together). These can disagree — a pocket can be soft-mode-spanned
yet graph-adjacent already, or vice versa. Reuse the existing taxonomy
(`classify_failure` verdicts) for the *output*, but this is a distinct
metric, justified as such. Confirm the two are measuring different things
before starting, and cross-link results, don't merge.

## Intent Contract

- Outcome: for every mandatory + ASD target, a single number — the
  pocket's graph-openness percentile against a matched-Euclidean-spread
  random-closure null — plus a Bonferroni-corrected verdict on whether
  real cryptic pockets are structurally special in the way [[HYP-P10]]
  claims. This is a premise test with a **binary, pre-declared outcome**;
  a clean negative is a complete, valuable result, not a failure.
- Why required, not optional: Falsifier A (`REVIEW-panel-2026-07-20`)
  showed the *trivial* loop idea is dead — at an 8 Å Cα cutoff a spatial
  cluster is already a clique, so a single ligand chord adds triangles
  indistinguishable from a decoy, and ambient b1 (~8N) dwarfs any added
  loop. The multi-site reframe survives *only if* real pockets carry the
  near-space/far-graph signature. That is an empirical claim about the
  benchmark, untested. Every downstream observable in this batch inherits
  its fate from this one number.
- In Scope:
  - Port `openness_signature(residues, D_euclid, GD)` = mean pairwise
    apo graph-hop distance / mean pairwise Euclidean distance among the
    holo-defined pocket residues, evaluated on the **apo** contact graph.
  - Build the **matched-spread random-closure null**: >=500 random
    same-size residue sets whose mean pairwise Euclidean spread is within
    +/-35% of the true pocket's, scored identically. Report the true
    pocket's percentile and one-sided p.
  - Apply to all 3 mandatory (KRAS_G12C, BCR_ABL1, CARDIAC_MYOSIN) + all
    4 ASD generalization targets already wired ([[TASK-0081]]).
  - Use the **same** pocket-label definition ([[TASK-0114]]'s cutoff) and
    the **same** apo contact graph (8 Å per `targets.yaml`, `H_new`'s own
    input) as every other headline number — no bespoke graph here.
- Out Of Scope:
  - Any scoring observable (chiral / CTQW / topology) — this task builds
    and tests the *premise*, not a residue-ranking. [[TASK-0140]] et al.
    consume the verdict.
  - Changing which operator ships (Tier-2 gated, [[TASK-0100]]).
  - Tuning the +/-35% spread-match tolerance against the outcome — fix it
    once, up front, report sensitivity only if the verdict is borderline.
- Constraints And Invariants:
  - **No label leakage**: the pocket labels are the only privileged set;
    the null is drawn blind to them. Do not tune the spread tolerance,
    the null size, or the graph cutoff to move any target across the bar.
  - The null must be matched on Euclidean spread so the *only* property
    under test is graph-distance-given-spatial-proximity — an unmatched
    null would just re-detect compactness.
- Planned Validation (**pre-registered — declare before running**):
  - **PASS (premise supported) on target T** iff true pocket openness
    lands **> 95th percentile** of the matched null, **and** survives
    **Bonferroni** across the 7 targets (per-target threshold p < 0.05/7
    ≈ 0.0071).
  - **FAIL (premise refuted) on target T** iff the pocket lands at/below
    the null median (≈50th percentile) — report as "cryptic pockets are
    not graph-open at Cα resolution; the loop/closure family is dead,"
    the analogue of [[TASK-0123]]'s own "observable dead" honest outcome.
  - **INSUFFICIENT** for anything between — suggestive, follow up, not a
    result (the [[TASK-0131]]/[[TASK-0133]] precedent for uncorrected-only
    signal).
  - Synthetic positive-control gate first (falsification apparatus before
    real data): reproduce `closure_test.py`'s constructed open-cleft case
    hitting ~100th percentile, so a null real-data result cannot be a
    silent implementation bug.

## TODO

- [ ] Confirm this metric is distinct from `cumulative_overlap` (callout).
- [ ] Port `openness_signature` + `graph_dist_matrix` into `src/allostery`.
- [ ] Synthetic positive-control gate (constructed open cleft -> ~100th pct).
- [ ] Matched-spread random-closure null (>=500, +/-35% spread, fixed).
- [ ] Run all 3 mandatory + 4 ASD targets; record percentile + p each.
- [ ] Apply Bonferroni (7 targets); emit PASS/FAIL/INSUFFICIENT per target.
- [ ] Write to `results_task0139_openness_premise/` + `RESULTS.md` section
      with the naive reading AND the corrected (Bonferroni) reading, tagged.

## Dependency

- None hard — runs on the existing apo graphs and holo labels immediately.
- Cross-link (do not duplicate): [[TASK-0059]]/[[TASK-0120]] (the *other*
  openness/learnability gate — orthogonal dynamics question).

## Open Questions

- Whether to also report the long-range-closure variant
  (`closure_longrange` in `closure_test.py`, total apo graph-distance the
  closure short-circuits) as a secondary statistic — Implementer's call;
  if reported, it needs its own matched null, not a shared one.

## Done

(not yet)
