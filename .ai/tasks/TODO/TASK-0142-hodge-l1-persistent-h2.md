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
- **Flagged 2026-07-20 (Architect/Planner)**: no reference script existed
  at that point for either half. **Update 2026-07-22**: a real H2
  implementation now exists and is delivered — see the gating-correction
  section below. **The L1 half still has no reference script** — request
  one or build from this task's own spec + HYP-P12's description.
  **`ripser` is now a concrete, delivered dependency** (not an open
  GUDHI-or-Ripser choice) — add it to `pyproject.toml` per this
  project's own TASK-0108/0110 dependency-manifest precedent; flag
  explicitly in Done, do not silently `pip install` without recording it.
- Priority: **P1 for the H2 half, escalated 2026-07-22 — the TASK-0143
  gate is corrected below, not removed by fiat.** The L1 half remains
  P2/gated as originally scoped (see the split below).

## Gating correction, 2026-07-22 (Architect/Planner) — H2 is not gated by TASK-0143 after all

**Real, executed, well-argued work delivered** (relayed via
`.ai/reviews/2026-07-22/persistent_voids.py` +
`test_persistent_voids.py` + `persistent_voids_synthetic_control.py`)
makes a specific, now-tested case that this task's own original gating
("run only if TASK-0143 or TASK-0140 shows life") was applying the wrong
premise to the H2 half specifically:

**TASK-0143 tested whether pocket residues are Euclidean-near but
graph-hop-*far*** — the signature of an *open* cleft that the apo contact
graph doesn't yet connect. **A persistent H2 void is a different
geometric object**: a *capped* cavity's lining residues form a closed
2-cycle, which requires them to be graph-*adjacent* (close), not far —
the opposite signature. TASK-0143's 0/7 result falsifies the open-cleft
premise; it says nothing about capped voids, because H2 was never
testing that premise in the first place.

**This is now demonstrated, not just argued**: the delivered
`test_persistent_voids.py::test_void_detected_even_when_lining_is_graph_
adjacent` constructs a cavity whose wall points are deliberately
graph-near and confirms `top_h2_persistence` still fires (>2.5). On a
constructed "carved cryptic cavity" synthetic control: top H2 persistence
4.337 (vs. a solid-ball noise floor of 1.105, and a hollow shell's
never-fills ∞) with `void_score` AUC 0.576 and the cavity's own lining
residues at **mean graph-hop 1.44** — i.e. graph-*adjacent*, exactly the
case TASK-0143's own test would have missed. **Verified directly, not
assumed** — this Architect/Planner thread read the actual test and
confirmed the assertion matches the claim before accepting the argument
and un-gating this half of the task.

**The L1 half's gating is unaffected by this correction** — L1's own
joint-support score is fundamentally a *cycle/loop-flow* quantity
(closely related to H1/b1), the same family TASK-0143's graph-openness
test actually does bear on. **L1 remains gated on TASK-0143/TASK-0140
showing life**, per the task's original scoping; only the H2 half is
escalated.

**Known weak link in the delivered H2 implementation, stated honestly by
its own author and confirmed on reading the code**: residue-level
localization of the void's lining is a crude geometric heuristic (a
grid-free shell-membership search for the void centroid, since `ripser`
does not return H2 cycle representatives by default) — on the synthetic
control, a plain proximity floor scored the cavity *higher* (0.82) than
`void_score` (0.576) in a geometry where seed and cavity happened to sit
on the same side. **This must be resolved or at least characterized
before trusting residue-level AUC on real targets** — the improvement
path already identified: GUDHI's alpha-complex with simplex tracking, or
`ripser`'s `do_cocycles` option, either of which would recover which
residues actually line the void rather than a geometric proxy for it.

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

**H2 half — ungated, implementation delivered, do this first:**
- [ ] Port `persistent_voids.py`/`test_persistent_voids.py`/
      `persistent_voids_synthetic_control.py` into their real homes
      (`src/allostery/`, `tests/`, `scripts/`); add `ripser` to
      `pyproject.toml`; re-verify the 4 delivered tests pass unmodified.
- [ ] Run `void_score`/`top_h2_persistence` on all 3 mandatory targets,
      same 8 Å cutoff as the rest of the register.
- [ ] Matched-spread random-patch null ([[TASK-0133]] precedent);
      percentile + p per target.
- [ ] Characterize (don't just note) the residue-localization weak link
      before trusting real-target AUC — at minimum, report whether
      `void_score`'s crude centroid heuristic or the plain proximity
      floor scores higher on each real target, same comparison the
      synthetic control already surfaced.
- [ ] Bonferroni; PASS/FAIL/INSUFFICIENT per target, tagged;
      `results_task0142_topology/`.

**L1 half — still gated, still unimplemented:**
- [ ] Build apo simplicial complex (same 8 Å cutoff); ∂1, ∂2 (∂3 for H2,
      already covered by the H2 half above).
- [ ] L1 = ∂1ᵀ∂1 + ∂2∂2ᵀ; assert dim ker L1 == E−N+C (validity gate).
- [ ] L1 per-residue score (softest non-harmonic edge-mode joint support).
- [ ] Matched-spread random-patch null; percentile + p.
- [ ] Only attempt if [[TASK-0143]] or [[TASK-0140]] shows life.

- [ ] `RESULTS.md` section covering both halves; state the quantum-Betti
      connection as PROPOSAL framing, not a demonstrated advantage.

## Dependency

- **H2 half: no hard gate** (corrected 2026-07-22, see above) — reuses
  [[TASK-0133]] (random-patch null pattern), [[TASK-0112]] (CI).
- **L1 half: hard gate unchanged** — run only if [[TASK-0143]] or
  [[TASK-0140]] shows life.
- New external dep: `ripser` (H2 half, delivered) — add to
  `pyproject.toml`, flag in Done per [[TASK-0108]]/[[TASK-0110]]'s own
  dependency-manifest precedent. GUDHI remains a possible future
  upgrade path (better cocycle/simplex tracking) but is not required to
  land the H2 half as delivered.

## Open Questions

- **Resolved for the H2 half, 2026-07-22**: the delivered
  `persistence_h2` builds a Vietoris-Rips complex directly on Cα
  coordinates (Euclidean distance), not the contact-graph's clique
  complex — a real, stated choice (`ripser(coords, maxdim=2, thresh=...)`),
  not left open. Still applies to the L1 half, unimplemented.
- Rips complex vs the contact-graph clique complex for the L1 base
  complex — they differ in the filled 2-/3-simplices. State the choice
  and why; report if the H2 verdict is sensitive to it (it may be — this
  is the Falsifier-D spurious-cycle regime).
- Whether N (up to ~950 for CARDIAC_MYOSIN) makes ∂3 / H2 persistence
  computationally heavy; if so, coarse-grain per the challenge's own
  coarse-graining secondary objective and note the compression.

## Done

(not yet)
