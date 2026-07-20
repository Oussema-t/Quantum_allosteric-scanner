# TASK-0142 Hodge-Laplacian L1 + persistent H2 observable; quantum-Betti bridge (HYP-P12)

## Context

- ID: TASK-0142
- Title: Lift the multi-site closure from graph edges to its correct
  topological home — the Hodge Laplacian L1 (native loop-flow operator,
  dim ker L1 = b1) and persistent H2 (the capped void a buried pocket
  actually is) — and characterize whether either localizes real pockets
  that the graph-level observables miss ([[HYP-P12]]).
- Status: TODO
- Owner: Implementer (build + run). The L1 drop-in is small (~dozens of
  lines); the review will provide a reference if requested. H2 requires
  GUDHI/Ripser — not a homemade b1 (see callout).
- Source: `REVIEW-panel-2026-07-20` §"topological ladder" and Falsifier D
  (the homemade single-radius b1 could not separate a real loop from
  sampling noise — real persistence tooling is required).
- **Flagged 2026-07-20 (Architect/Planner)**: no reference script (for
  the L1 drop-in or otherwise) is present in this repo or the applied
  review batch, consistent with this task's own honest "will provide a
  reference if requested" framing above — request it, or build from
  this task's own spec + HYP-P12's description. **Neither GUDHI nor
  Ripser is currently a project dependency** (checked directly,
  `requirements.txt`/`pyproject.toml`) — adding either is a new
  third-party dependency requiring a manifest, per this project's own
  TASK-0108/0110 precedent (the `optuna` dependency-manifest gap) — flag
  explicitly in Done, do not silently `pip install` without recording it.
- Priority: **P2 — gated on [[TASK-0143]] and/or [[TASK-0140]] showing
  life.** If the openness premise and the chiral observable both FAIL,
  the topological rung inherits the same no-signal verdict and should not
  be run before the Sept-15 writing constraint. If either shows life,
  this is the rung that connects to a genuine (regime-dependent) quantum
  advantage argument and belongs in the forward proposal.

## ⚠️ Before implementing — use real persistence tooling; H2 not H1

Falsifier D showed a single-radius Rips b1 is dominated by spurious
short-lived cycles at exactly the intermediate radii a contact graph
lives in — it flagged a filled disk and a contractible bowl as "loops."
**A cavity is an H2 void, not an H1 loop** (which is also why Falsifier D's
grooves were invisible: grooves are contractible). Use GUDHI or Ripser
with proper birth-death persistence and the ∂3 tetrahedra for H2. Do not
ship a homemade Betti count as evidence. This is a hard correctness
constraint, not a preference.

## Intent Contract

- Outcome: two observables, each with a matched-null percentile verdict on
  whether it localizes real holo-defined pockets:
  (1) **Hodge L1**: b1 = dim ker L1 of the apo simplicial complex, plus a
      per-residue score from the softest non-harmonic L1 edge-mode's joint
      support on the active site and candidate residues (the "flow around
      the multi-loop cage" the ligand closes);
  (2) **Persistent H2**: the longest-persistence H2 generator(s) of the
      apo Vietoris-Rips complex, and whether the pocket residues bound a
      persistent void the holo ligand caps.
- Why required: the ligand touching k residues at once is a k-simplex, not
  k edges — a fact the graph Laplacian throws away and L1/H2 keep. This is
  the only rung where the biological object (a capped cavity) and a
  quantum-advantage object (Betti-number / Hodge-Laplacian estimation,
  Lloyd-Garnerone-Zanardi, regime-dependent BQP) coincide. Even a negative
  here is the honest boundary of the advantage argument for the proposal.
- In Scope:
  - Build the apo simplicial complex (Rips or the contact-graph clique
    complex) once, at the same 8 Å cutoff as every other observable.
  - L1 = ∂1ᵀ∂1 + ∂2∂2ᵀ (down- + up-Laplacian). Report b1 = dim ker L1 as
    a cross-check against the graph cyclomatic number (E−N+C), and the
    softest non-harmonic edge-mode's joint active+pocket support as the
    per-residue score.
  - Persistent H2 via GUDHI/Ripser; per-target, does the top-persistence
    void localize on the pocket. Matched-spread random-patch null
    ([[TASK-0133]] precedent) for both observables.
  - Apply to whichever targets [[TASK-0143]]/[[TASK-0140]] flagged as
    live; document explicitly if run on all for completeness.
- Out Of Scope:
  - Any actual quantum-Betti circuit / hardware mapping — this task builds
    and tests the *classical* observable; the quantum-advantage framing is
    a *proposal* item (see the forward-proposal note in EXECUTION_PLAN
    Phase 1D), not a claim to demonstrate here.
  - Multi-particle / interacting walks (Falsifier C near-no; not revived).
  - Operator-selection (Tier-2 gated, [[TASK-0100]]).
- Constraints And Invariants:
  - Real persistence tooling only for H2 (callout). The homemade b1 is
    permitted ONLY as a ker-L1 cross-check against E−N+C, never as pocket
    evidence.
  - Same cutoff / same labels / same seed convention as the rest of the
    register — no bespoke complex tuned to make a pocket appear.
  - Matched-spread null, blind to labels — the [[TASK-0143]] discipline.
- Planned Validation (**pre-registered**):
  - **PASS on target T** iff the L1 joint-support score OR the top-
    persistence H2 generator localizes on the pocket above the 95th
    percentile of the matched random-patch null, surviving Bonferroni.
  - **FAIL** iff both sit at/below the null median — report "the pocket is
    not a topological feature these operators see at Cα resolution,"
    bounding the advantage argument honestly.
  - b1(ker L1) must equal the graph cyclomatic number E−N+C on the apo
    complex (setup-validity gate) before trusting any L1 mode.

## TODO

- [ ] Build apo simplicial complex (same 8 Å cutoff); ∂1, ∂2 (∂3 for H2).
- [ ] L1 = ∂1ᵀ∂1 + ∂2∂2ᵀ; assert dim ker L1 == E−N+C (validity gate).
- [ ] L1 per-residue score (softest non-harmonic edge-mode joint support).
- [ ] Persistent H2 via GUDHI/Ripser; top-generator pocket localization.
- [ ] Matched-spread random-patch null for both; percentile + p.
- [ ] Bonferroni; PASS/FAIL per target, tagged; `results_task0142_topology/`.
- [ ] `RESULTS.md` section; state the quantum-Betti connection as PROPOSAL
      framing, not a demonstrated advantage.

## Dependency

- Hard gate: run only if [[TASK-0143]] or [[TASK-0140]] shows life.
- Reuses: [[TASK-0133]] (random-patch null pattern), [[TASK-0112]] (CI).
- New external dep: GUDHI or Ripser — flag for the environment/venv the
  same way other deps were ([[TASK-0026]] lineage).

## Open Questions

- Rips complex vs the contact-graph clique complex for the base complex —
  they differ in the filled 2-/3-simplices. State the choice and why;
  report if the H2 verdict is sensitive to it (it may be — this is the
  Falsifier-D spurious-cycle regime).
- Whether N (up to ~950 for CARDIAC_MYOSIN) makes ∂3 / H2 persistence
  computationally heavy; if so, coarse-grain per the challenge's own
  coarse-graining secondary objective and note the compression.

## Done

(not yet)
