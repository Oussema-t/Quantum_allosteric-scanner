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
- Status: Done
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

- [x] Confirm this metric is distinct from `cumulative_overlap` (callout).
- [x] Port `openness_signature` + `graph_dist_matrix` into `src/allostery`.
- [x] Synthetic positive-control gate (constructed open cleft -> ~100th pct).
- [x] Matched-spread random-closure null (>=500, +/-35% spread, fixed).
- [x] Run all 3 mandatory + 4 ASD targets; record percentile + p each.
- [x] Apply Bonferroni (7 targets); emit PASS/FAIL/INSUFFICIENT per target.
- [x] Write to `results/tasks/0143_openness_premise/` + `RESULTS.md` section
      with the naive reading AND the corrected (Bonferroni) reading, tagged.
      (Renamed from the stale `results/tasks/0139_...` this file's own text
      still carried after the [[TASK-0139]] ID collision/renumbering.)

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

**Headline: HYP-P10's premise is not supported on any of the 7 targets — 0/7 PASS.**
The entire loop/multi-site-closure observable family (HYP-P9, HYP-P12) that this
premise gates has no empirical support from this test. Not a soft negative: one
target actively contradicts the claimed direction (CASPASE7, FAIL), and the
matched-spread null construction itself turned out to be infeasible via unbiased
rejection sampling for 4 of the 7 targets — a real, substantive finding about real
pockets' spatial compactness, reported honestly rather than forced.

### Distinctness confirmed by construction, not just callout

`allostery.closure` never imports `superpose` — `openness_signature`/`graph_dist_matrix`
operate on the apo contact graph and Euclidean coordinates alone; no ANM modes, no
holo displacement, no RMSD enter any computation here. `cryptic_openness_gate`/
`cumulative_overlap` ([[TASK-0059]]/[[TASK-0120]]) is a *dynamics* question (is
apo->holo spanned by soft modes); this is a *structural-graph* question about the apo
state alone. Confirmed orthogonal, not merely asserted.

### Implementation

New `src/allostery/closure.py`: `graph_dist_matrix` (all-pairs BFS hop distance on the
binary apo contact graph, `networkx.all_pairs_shortest_path_length` — O(N(N+E)) on this
graph's sparse ~8-15 neighbors/node, far cheaper than Floyd-Warshall's O(N^3) at
CARDIAC_MYOSIN's scale; raises if the apo graph is disconnected at the given cutoff
rather than silently patching in a penalty value), `euclid_dist_matrix`,
`openness_signature` (mean pairwise apo graph-hop / mean pairwise Euclidean, exactly
HYP-P10's own defining ratio), `matched_spread_null` (rejection-sampling null: >=500
random same-size residue sets within +/-35% of the real pocket's mean pairwise
Euclidean spread, scored identically; raises `RuntimeError` — not a silent short
count — if `max_attempts` is exhausted first). 9 new tests in `tests/test_closure.py`,
including a hand-computed-ratio check and a horseshoe-arc synthetic fixture (residue 0
and residue n-1 on a circular arc spanning `2*pi - gap_angle`, Euclidean-close across
the gap, graph-far around the arc) used for both the positive control (tips) and a
negative control (mid-arc residues, confirming the positive result isn't a fixture
artifact).

New `scripts/openness_premise_test.py`: runs the synthetic positive-control gate first
(constructed open-cleft case, percentile>=95 required or the script aborts before
touching real data), then all 7 targets, writing a per-target checkpoint to the output
JSON after every target (not just at the end — see Errors below).

### Real bug found and fixed: non-reproducible seed derivation

First full run gave KRAS_G12C percentile=100.0 on one invocation and 99.4 on a second,
identical-looking one — traced to `seed = BASE_SEED + (hash(target_name) & 0xFFFF)`:
Python's built-in `hash()` on strings is salted per-process (`PYTHONHASHSEED`,
security feature since Python 3.3), so the derived seed silently differed on every
run. Fixed to `zlib.crc32(target_name.encode())`, a fixed deterministic function of its
input — re-ran, now reproducibly gives percentile=98.4 for KRAS_G12C across repeated
invocations. This is exactly the class of problem [[TASK-0135]]'s reproducibility audit
exists to catch; not caught by that audit because this code didn't exist yet when
TASK-0135 ran.

### Real bug found and fixed: output written only once, at the end

Same design flaw [[TASK-0138]] already hit and fixed in its own null script, reproduced
independently here before that lesson was applied: the first full-batch run was killed
partway through (an unrelated tool-availability interruption, not a script bug) and the
completed KRAS_G12C/BCR_ABL1 results were lost, since nothing had been written to disk
yet. Fixed identically: `main()` now loads and merges any existing output file and
checkpoints after every target.

### Real, substantive finding: the pre-registered null construction is infeasible for
most targets via unbiased rejection sampling

At +/-35% spread tolerance, 4 of 7 targets could not reach 500 matched-spread
replicates even at 20,000,000 rejection-sampling attempts (raised
`MAX_ATTEMPTS`, itself a compute-budget parameter, not a statistical-construction one
per this task's own Constraint — the spread tolerance/null size/graph cutoff were never
touched): BCR_ABL1 (0/500), CARDIAC_MYOSIN (1/500), PTP1B (19/500), GLUCOKINASE (1/500).
Root cause, not assumed: a compact, small same-size residue cluster with the real
pocket's mean pairwise Euclidean spread is intrinsically rare among *uniform* random
draws over a large protein, since most such draws scatter across the whole fold rather
than clustering compactly by chance. This is itself informative (real pockets are
substantially more spatially compact than a typical same-size random subset of the
whole structure) but is a distinct property from HYP-P10's own graph-openness claim,
and the pre-registered methodology (uniform rejection sampling) cannot test the latter
when it cannot even construct the former. **Not fixed here** (would require a smarter,
validated sampling scheme — e.g. spatially-biased proposals with importance
correction — which changes the null's own statistical construction and is explicitly
Out Of Scope for this task to redesign after seeing the outcome); flagged as a concrete
methodological gap for whoever next revisits this premise, not silently worked around.

### Results (all 7 targets)

Added 2026-07-22, after this task's own close-out: the two raw numbers `real_signature`
divides into (`allostery.closure.pairwise_components`, always computable independent of
whether the null itself can be constructed) — mean pairwise apo graph-hop distance and
mean pairwise Euclidean distance among the pocket residues, on their own, not just their
ratio. A same ratio can come from very different underlying magnitudes (e.g. 2.4 hops
over 11.6 Å vs. 8 hops over ~40 Å describe physically different situations), and for the
4 INFEASIBLE targets these are the only real, reportable numbers available at all — no
recomputation of the (unaffected, unchanged) null results was needed, since these
components never touch rejection sampling.

| Target | N | Pocket size | Graph-hop mean | Euclid mean (A) | Real signature | Null result | Percentile | p (uncorrected) | p (Bonferroni x7) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| KRAS_G12C | 169 | 18 | 2.3856 | 11.57 | 0.2062 | 500/500 (305,726 attempts) | 98.4 | 0.0160 | 0.1120 | **INSUFFICIENT** |
| BCR_ABL1 | 451 | 16 | 2.3500 | 10.30 | 0.2281 | 0/500 (20M attempts) | — | — | — | **INFEASIBLE** |
| CARDIAC_MYOSIN | 704 | 13 | 4.5769 | 13.23 | 0.3461 | 1/500 (20M attempts) | — | — | — | **INFEASIBLE** |
| PTP1B | 298 | 14 | 2.2308 | 10.79 | 0.2067 | 19/500 (20M attempts) | — | — | — | **INFEASIBLE** |
| GLUCOKINASE | 448 | 17 | 2.6618 | 11.76 | 0.2263 | 1/500 (20M attempts) | — | — | — | **INFEASIBLE** |
| CASPASE1 | 255 | 6 | 2.1333 | 9.62 | 0.2218 | 500/500 (453,242 attempts) | 90.2 | 0.0980 | 0.6860 | **INSUFFICIENT** |
| CASPASE7 | 461 | 7 | 2.8571 | 14.82 | 0.1927 | 500/500 (37,121 attempts) | 26.8 | 0.7320 | 1.0000 | **FAIL** |

**Read alongside the verdicts, not instead of them**: 6 of 7 targets cluster tightly in
graph-hop terms (2.1-2.9 hops), despite Euclidean spreads ranging 9.6-14.8 Å — CARDIAC_MYOSIN
is the one outlier, at 4.58 hops (roughly double the others), the target with the highest
real signature of all 7. This is consistent with, not a contradiction of, its own
INFEASIBLE verdict: the raw number is the largest in the set, but INFEASIBLE means no
matched-spread null could be built to say whether that raw number is anomalous *for its
own spread* or just reflects CARDIAC_MYOSIN's own larger, more spread-out pocket
(13.23 Å, also the second-largest spread in the set) — the two raw numbers narrow what
"INFEASIBLE" means without resolving it into a verdict.

CARDIAC_MYOSIN's N=704 (not the 950 this file's own earlier drafts and sibling
[[TASK-0126]]/[[TASK-0138]] used) reflects [[TASK-0124]]'s apo re-anchor (5TBY -> 8QYP),
already landed before this task ran — confirmed directly, not a bug in this task's own
loading path (both use the identical `run_challenge._load_apo_holo` call).

**Per this task's own pre-registered criteria**: **zero targets reach PASS** (>95th
percentile AND Bonferroni-significant). KRAS_G12C and CASPASE1 are the two targets
where the null was even constructible and both land as INSUFFICIENT — suggestive
(KRAS_G12C's own uncorrected p=0.016 clears an uncorrected 0.05 bar, same shape as
[[TASK-0131]]'s own KRAS_G12C ceiling-null finding) but not decisive after Bonferroni.
CASPASE7 is a clean FAIL (26.8th percentile — its pocket is *less* graph-far than a
typical matched-spread random cluster, the opposite of HYP-P10's claim). The other 4
targets could not be tested at all under the pre-registered null construction.

### Answer to this task's own central question

**HYP-P10's premise is not supported.** [[TASK-0140]]/[[TASK-0142]] (gated on this
result per their own filing) should treat the multi-site-closure/chiral/topological
observable family as having no confirmed non-proximity loop to detect on real data —
consistent with this project's own recent pattern of headline-looking premises not
surviving scrutiny once actually tested ([[TASK-0131]]'s CARDIAC_MYOSIN ceiling finding,
[[TASK-0138]]'s H14 permutation-null finding). Per this task's own framing, this is a
complete, valuable result, not a failure to hide — the "trivial loop is dead, does the
multi-site reframe survive" question now has a real, checked answer: no, not as
tested, and the null construction's own infeasibility on most targets means even a
more forgiving reading can't be extracted from this exact methodology without touching
parameters this task was explicitly told not to tune after seeing the outcome.

Files touched: `__WORK_IN_PROGRESS__/src/allostery/closure.py` (new),
`__WORK_IN_PROGRESS__/tests/test_closure.py` (new, 9 tests),
`__WORK_IN_PROGRESS__/scripts/openness_premise_test.py` (new). Results:
`__WORK_IN_PROGRESS__/results/tasks/0143_openness_premise/openness_premise.json`.
