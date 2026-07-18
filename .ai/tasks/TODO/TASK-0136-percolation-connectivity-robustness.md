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
- Status: TODO
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

- [ ] Implement weighted shortest-path + sub-optimal-path ensemble
      between active site and real pocket, all 3 targets.
- [ ] Implement edge-connectivity (min-cut) + percolation-threshold
      between the same two endpoint sets, all 3 targets.
- [ ] Report the literal bottleneck (if one exists) — actual residues/
      edges on the min-cut.
- [ ] Generalize to `connectivity_robustness(coords, source, cutoff)` as
      a new scoreable baseline, seed-to-every-residue.
- [ ] Score part (c) against TASK-0094's floor; gate through TASK-0103's
      dumbbell matrix; cross-read against TASK-0123 once available.
- [ ] State the bottleneck-vs-distributed finding per target explicitly,
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

(not yet)
