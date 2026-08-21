# TASK-0136 Path-ensemble + percolation connectivity between active site and known allosteric site

## Context

- ID: TASK-0136
- Title: build a purely topological (no propagator, no `t_max`, no seed
  coherence, no clock) family of observables characterizing the
  connectivity structure between the active site and the known
  allosteric pocket on the apo contact graph: (a) a weighted shortest-
  path/sub-optimal-path ensemble between the two known residue sets, and
  (b) percolation/edge-connectivity robustness — how many independent
  routes connect them, and at what edge-weight threshold does that
  connection collapse.
- Status: Done
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: raised directly by the orchestrating user, 2026-07-18 — "would
  it make sense to actually make a 'shortest path' finding algorithm
  between known active/allosteric sites and do any form of percolation
  on the outcome? What would it potentially model?" Explicit instruction
  to file it regardless of outcome: "worst it can get is rejected by
  evidence."
- Priority: **P1.** No dependency on the current P0 gauge-fixing batch
  (TASK-0130/0131/0116) — this observable family shares none of their
  confound axes (seed/clock/coherence) — but should still be checked
  against whatever floor/labels those tasks leave current, per this
  project's standing discipline (no observable is scored against a
  stale label set).

## Intent Contract

- **What this would model, stated precisely (not left implicit)**: a
  single shortest path treats allosteric communication as "is there *a*
  route" — this task's actual question is whether communication is
  carried by a **narrow, fragile bottleneck** (one dominant channel,
  low edge-connectivity, a single suboptimal-path corridor) or a
  **broad, redundant subnetwork** (many independent routes, high
  edge-connectivity, a percolating backbone). This is a real,
  pre-existing distinction in the allostery literature — Chennubhotla &
  Bahar's correlation-network path analysis (cited in the challenge
  statement itself, ref [8]) and Nussinov & Tsai's ensemble-allostery
  framing (ref [4], ditto) both hinge on exactly this bottleneck-vs-
  distributed question — not a method invented for this task in
  isolation.
- Outcome, part (a) — **path ensemble, diagnostic, uses real labels**:
  weighted shortest path (Dijkstra, edge weight = inverse contact
  strength, reusing `potentials.py`'s existing `W_invdist`-style
  weighting rather than inventing a second one) between the active-site
  residue set and the real pocket residue set, on each mandatory
  target's apo contact graph. Report the path itself (the literal
  residue sequence — a concrete, inspectable candidate channel) and a
  **sub-optimal path ensemble** (all paths within a stated tolerance of
  the shortest, not just the single geodesic — ties/near-ties make one
  path an arbitrary pick, per this task's own reasoning above) rather
  than trusting one route. This half is explicitly a mechanism-
  characterization diagnostic (real labels, both endpoints known) — same
  status as TASK-0102's seed-invariance check or the dumbbell negative
  control, not a blind predictor, and does not need `ceiling_context()`
  gating since it makes no scoring/selection claim.
- Outcome, part (b) — **percolation / edge-connectivity, the
  bottleneck-vs-distributed question**: (i) edge connectivity (Menger's
  theorem — the minimum number of edges whose removal disconnects the
  active-site node-set from the pocket node-set, equivalently the
  maximum number of edge-disjoint paths between them) via `networkx`'s
  existing `minimum_cut`/`edge_connectivity` (already a dependency, per
  `betweenness_centrality`'s own use of `networkx` — no new dependency
  needed); (ii) the percolation threshold — thresholding the weighted
  graph from strongest to weakest edge, report the edge-weight at which
  the active-site and pocket components first merge (equivalently,
  disconnect, thresholding the other direction). Report both numbers per
  target, plus whichever residues/edges the min-cut actually passes
  through (the literal bottleneck, if one exists).
- Outcome, part (c) — **promote as a blind, scoreable baseline, not just
  a two-point diagnostic**: generalize (b)'s edge-connectivity idea from
  "active site to the one known pocket" into "active site to every
  residue" — `connectivity_robustness(coords, source, cutoff)`, analogous
  to `baselines.hop_from_seed` but reporting edge-connectivity (path
  redundancy) instead of hop-count (path length) per residue. This *is*
  a legitimate, blind, AUC-scoreable observable — a strictly richer
  generalization of the existing `hop_from_seed` baseline, not
  necessarily a fix for its confound. Score it through the same
  discipline as every other register member: checked against TASK-0094's
  proximity floor, gated through TASK-0103's dumbbell matrix (does it
  track coupling, not the well — same falsification lens every other
  observable in this register got), and read alongside whatever
  TASK-0123 (distance-stratified evaluation) produces once it lands,
  since percolation/connectivity measures are also plausibly
  degree-dominated and should not be assumed exempt from that confound
  just because they aren't propagator-based.
- In Scope:
  - All 3 mandatory targets for part (a)/(b); part (c) run on the same
    targets plus reused wherever `hop_from_seed`/`degree_centrality`
    already run, for direct comparison.
  - Reuse existing contact-graph/weighting machinery
    (`contact_matrix`/`W_invdist`) — do not build a second graph
    construction.
- Out Of Scope:
  - Any propagator/quantum-walk machinery — this task is deliberately
    the topological complement to CTQW/GSR/ENAQT, not a variant of them.
  - Reselecting the submission operator based on part (c)'s result alone
    — Tier-2-gated per [[TASK-0100]], same as every other candidate.
  - `HOLO_DIRECTION_MODULE`'s deformation machinery — orthogonal
    question (structural change vs. static-graph connectivity), not
    conflated here.
- Constraints And Invariants: part (c)'s scored numbers must be reported
  with the same floor/dumbbell/distance-stratification caveats every
  other observable in the register carries — no lighter-touch reporting
  standard for a new, topologically-motivated observable than for CTQW.
- Planned Validation: part (a)/(b) are reported directly (the paths and
  connectivity numbers *are* the finding, whichever way they come out —
  a narrow bottleneck, a redundant network, or no meaningful distinction
  from noise, per this project's own "report the result whichever way it
  comes out" convention). Part (c) requires the dumbbell-matrix gate and
  the proximity-floor check before being read as informative.

## In Progress

None

## TODO

- [x] Implement weighted shortest-path + sub-optimal-path ensemble
      between active site and real pocket, all 3 targets.
- [x] Implement edge-connectivity (min-cut) + percolation-threshold
      between the same two endpoint sets, all 3 targets.
- [x] Report the literal bottleneck (if one exists) — actual residues/
      edges on the min-cut.
- [x] Generalize to `connectivity_robustness(coords, source, cutoff)` as
      a new scoreable baseline, seed-to-every-residue.
- [x] Score part (c) against TASK-0094's floor; gate through TASK-0103's
      dumbbell matrix; cross-read against TASK-0123 once available.
- [x] State the bottleneck-vs-distributed finding per target explicitly,
      whichever way it comes out.

## Dependency

- [[TASK-0094]] (Done) — the proximity floor, reused for part (c)'s check.
- [[TASK-0103]] (Done) — the dumbbell matrix, reused for part (c)'s gate.
- Soft: [[TASK-0123]] (distance-stratified evaluation) — read together
  once both exist, not a hard block on either.
- None on the current P0 gauge-fixing batch (TASK-0130/0131/0116) — this
  observable family is deliberately outside that confound axis.

## Open Questions

- Exact sub-optimal-path tolerance (how far above the geodesic counts as
  "part of the ensemble") — Implementer's call, state the choice and why
  in Done; report sensitivity if it materially changes which residues
  appear on the reported channel.

## Done

**Headline: all 3 mandatory targets show broad, redundant connectivity between the
active site and the known allosteric pocket — no narrow, fragile bottleneck on any
target.** The bottleneck-vs-distributed question this task exists to ask has a clean,
consistent, decisive answer: distributed, not narrow, everywhere tested.

### Correction to this task's own filing

The task text cites "`potentials.py`'s existing `W_invdist`-style weighting" —
`potentials.py` has no such thing (grepped directly, zero matches). The actual existing
invdist weighting is `hamiltonians.contact_matrix(weight="invdist")`, reused from the
correct module.

### Implementation

New `src/allostery/percolation.py`: `shortest_path_ensemble` (Dijkstra + Yen's-algorithm
sub-optimal-path enumeration between two residue sets via a virtual super-source/sink
reduction), `set_edge_connectivity` (Menger's-theorem edge connectivity + the literal
min-cut edges between two sets), `percolation_threshold` (Union-Find sweep, strongest
edge first, reports the exact edge that first connects the two sets). New
`baselines.connectivity_robustness`/`connectivity_robustness_from_adjacency` (part c) —
edge-connectivity from a seed set to every residue, a strict generalization of
`hop_from_seed`'s own shape. 12 new tests (`tests/test_percolation.py`), 3 new tests
(`tests/test_baselines.py`).

### Real bug found and fixed, before trusting any real-target number

First real-target run showed `edge_connectivity` saturating at *exactly*
`min(len(active_site), len(pocket))` on all 3 targets, with an *empty* min-cut — a
suspicious, too-clean pattern, checked rather than accepted. Root cause: the virtual
super-source/sink construction connected each seed member to its virtual node with a
single **unit-capacity** edge, reasoning (in the first-draft docstring) that "a
k-residue set cannot originate more than k edge-disjoint paths." That reasoning is
wrong, confirmed directly with a synthetic check: a single node with 3 real fan-out
edges supports true edge-connectivity 3, not 1 — a set's own cardinality does not bound
route redundancy, its own graph degree does. Unit-capacity virtual edges silently capped
every reported connectivity at the smaller set's size, and the "empty cut" was this
function's own bookkeeping, not real graph structure. **Fixed**: virtual edges get a
large `capacity` attribute; real graph edges get `capacity=1` (Menger's-theorem route
counting is otherwise unweighted, unchanged). Also found while fixing: `networkx.
edge_connectivity`/`minimum_edge_cut` do not accept a `capacity` argument at all
(checked directly, not assumed) — the capacitated equivalents are `maximum_flow_value`/
`minimum_cut`, used instead. Same bug, same fix, independently present in
`connectivity_robustness_from_adjacency`'s own seed-to-single-target construction.
Re-running after the fix changed `set_edge_connectivity`'s numbers dramatically (13-18 →
68-76, see Results); `connectivity_robustness`'s own per-residue AUC was **unaffected**
by the fix (a single target node's own real degree, not the seed-set cardinality, was
already the binding constraint there in every case checked) — confirmed, not assumed,
by direct re-run comparison.

### Results — parts (a)/(b), all 3 mandatory targets

| Target | (a) shortest path length | (a) ensemble size (tol=10%) | (b-i) edge connectivity | (b-i) cut size | (b-ii) merge distance (Å) | (b-ii) edges added to merge |
|---|---|---|---|---|---|---|
| KRAS_G12C | 3.753 | 2 | **73** | 73 edges | 3.75 | 2 |
| BCR_ABL1 | 7.522 | 1 | **76** | 76 edges | 3.82 | 355 |
| CARDIAC_MYOSIN | 3.809 | 1 | **68** | 68 edges | 3.81 | 149 |

**Bottleneck-vs-distributed, stated explicitly per target**: all 3 are decisively
**distributed** — 68-76 edge-disjoint routes connect the active site to the pocket on
every target, an order of magnitude above what a "narrow, fragile bottleneck" (a
handful of chokepoint edges) would look like. There is no single literal bottleneck to
report on any target; the min-cut edge lists (full detail in the JSON results) span
dozens of distinct residue pairs each, confirming the redundancy is structural, not an
artifact of a single dominant path. **Percolation threshold, separately**: on
KRAS_G12C, the active site and pocket merge after only 2 of the strongest edges in the
*entire* apo graph are added (3.75 Å) — consistent with, and a new independent
(topological, not propagator-based) confirmation of, this project's own established
finding that KRAS_G12C's active site and pocket sit unusually close in 3-D space
(the proximity-confound history this whole project has tracked since TASK-0094).
BCR_ABL1/CARDIAC_MYOSIN merge later in the global strength ordering (355/149 edges)
despite similarly short absolute merge distances (3.82/3.81 Å) — both proteins are
larger, with many stronger (shorter) contacts elsewhere in the structure ranked ahead
of the specific edge that happens to bridge these two particular sets.

**Sub-optimal path tolerance (this task's own Open Question, Implementer's call)**:
`tol=0.10` (10% above the geodesic), `max_paths=50`. Never bound in practice (checked
directly): the largest ensemble found was 2 paths (KRAS_G12C); BCR_ABL1/CARDIAC_MYOSIN
each have a unique shortest path with no near-ties at this tolerance.

### Results — part (c), `connectivity_robustness` as a blind, scored baseline

| Target | AUC | Floor | Beats floor? | Stratified mean AUC | Stratified max AUC | n shells |
|---|---|---|---|---|---|---|
| KRAS_G12C | 0.5587 | 0.4818 | **Yes** (+0.0769) | 0.510 | 0.820 | 4 |
| BCR_ABL1 | 0.5272 | 0.5817 | No (−0.0545) | 0.535 | 0.723 | 4 |
| CARDIAC_MYOSIN | 0.4178 | 0.5679 | No (−0.1501, below chance) | 0.372 | 0.581 | 6 |

**Mixed, mostly-negative result, reported as such**: 1/3 targets beats its own floor.
**TASK-0123 cross-read, actually run (not cited by analogy)**: `metrics.stratified_auc`
applied directly to `connectivity_robustness`'s own scores, same hop-distance-shell
construction TASK-0123 used for every other operator. This task's own Constraint's
concern is confirmed: stratified mean AUC sits close to chance on KRAS_G12C/BCR_ABL1
(0.510/0.535) and *below* chance on CARDIAC_MYOSIN (0.372) — most of this baseline's
raw AUC is explained by the same distance/degree confound TASK-0123 already found
pervasive across this project's whole operator register, not an independent topological
signal. Not exempt from that confound just because it is not propagator-based, exactly
as this task's own Constraint anticipated rather than assumed.

**Dumbbell gate (TASK-0103), real result, a clean negative distinct in kind from GSR's
well-following**: `TestConnectivityRobustnessDumbbellGate` (new,
`tests/test_dumbbell_negative_control.py`) — AUC is **exactly 0.500 in every cell**
(C1/C2/C3/C4), not merely weak. Root cause, checked directly: `connectivity_robustness`
is deliberately unweighted (Menger's-theorem route *counting*), and the dumbbell's
DRUG/DECOY bridges are topologically identical (same node/edge count), differing only
in edge *weight* (1.0 vs 0.15) — there is no edge-count signal for an unweighted
measure to find on this specific construction, by design, not by defect. This does not
retract the real-target floor/stratified results above; it is a distinct, honestly
reported finding about this measure's own blind spot (weight-blindness), gated the same
way every other observable in this register already is.

### Answer to this task's own central question

**The active site and known allosteric pocket are broadly, redundantly connected on
apo topology alone, on all 3 mandatory targets — not a narrow communication
bottleneck.** This is a real, decisive, purely topological finding (no propagator, no
clock, no seed coherence), independent from and consistent with this project's own
established proximity-confound history. As a blind scoreable baseline,
`connectivity_robustness` beats the proximity floor on only 1/3 targets and its signal
is mostly explained by the same distance confound already found pervasive elsewhere in
this project's operator register — a real, mostly-negative result for part (c)
specifically, not to be conflated with parts (a)/(b)'s own decisive diagnostic finding.

Files touched: `src/allostery/percolation.py` (new), `src/allostery/baselines.py`
(`connectivity_robustness`/`connectivity_robustness_from_adjacency`, new),
`tests/test_percolation.py` (new, 12 tests), `tests/test_baselines.py` (+3 tests),
`tests/test_dumbbell_negative_control.py` (+2 tests, new gate class),
`scripts/percolation_connectivity_analysis.py` (new). Results:
`results/tasks/0136_percolation/percolation_connectivity.json`.
