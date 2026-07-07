# Action plan — next few weeks

**Date:** 2026-07-01 · **Phase 1 (Ideation) deadline:** 2026-09-15 (~10.5 weeks out)
**Companion docs:** PLAN.md · HOLO_DIRECTION_MODULE.md · ALGORITHM_REGISTER.md ·
SYSTEMS_allosteric_corrected_v2.md

**Relationship to `PLAN.md`:** confirmed companion timeline overlay, not a
superseding rewrite — this file schedules `PLAN.md`'s phases (Week 1 ≈
Phase 0, Week 2 ≈ Phase 1/2 gate, …) against the challenge deadline; it does
not redefine the gates. Decided in TASK-0002 (2026-07-04). Whether a new
`PLAN-DD.MM.YY.md` should be authored each week or this stays a one-off
snapshot is unresolved — ask before assuming either.

---

## Where we are (settled conclusions)

1. **The edge is rigor, not algorithms.** Every method in play is standard
   (GNM/ANM/CTQW/ENAQT/two-state ANM/NMFF). The differentiators are: an honest
   per-target competence map, a leakage firewall most teams lack, and a defensible
   negative result. Chasing a bespoke "quantum" primitive is the identified trap.
2. **Leakage was the core flaw.** Fixed by the DEV/FROZEN firewall + ceiling-before-
   LOPO ordering. Any per-target knob touching holo = leakage.
3. **Coherence probably adds ~nothing on these targets** (flat dephasing sweep), but
   this must be re-tested with γ calibrated from vibrational timescales, not a blind
   sweep, before we state it.
4. **GNM is the responsive substrate**; ANM needed for 3D modes but collapses to
   termini if used naively; LMS degenerate.
5. **Data:** KRAS verified (MOV/SII-P); BCR corrected (asciminib, exclude NIL);
   myosin quarantined (5TBY = IHM assembly, 6C1H drug unconfirmed); MYC pocket was
   fabricated, removed. **Pockets are DERIVED from holo ligand contacts, never
   transcribed.** The 11 ASD targets are unverified.
6. **Crystal chains are not pathways.** Crystal structures are minima, not barrier
   waypoints. 4OBE = prediction substrate; 6OIM = validation only. Ensembles must be
   homogeneous (same sequence + nucleotide state) or consensus is meaningless.
7. **The overlap gate is the fork in the road** (see Week 2).

---

## The plan

### Week 1 — Substrate truth (cheap, decisive, unblocks everything)
- [ ] **Programmatic PDB header audit.** Parse polymer name, sequence, mutations,
      nucleotide state, ligands, resolution for every candidate structure into one
      table. Includes the 8-ID KRAS "pathway" — expect to reject the FTase complex
      and the GTP/active mismatches. **Verify `11QE`** — malformed ID, likely a typo.
      No membership decision from memory or chat; the parsed table decides.
- [ ] **Derive pockets from holo contacts** (≤4.5 Å, sequence-mapped) for the
      verified mandatory targets. Resolve biological assembly per target (single-chain
      vs oligomer — inter-subunit allostery dies if cut to one chain).
- [ ] **Physics unit tests**: Bessel line, dimer Rabi, cycle spectrum,
      nullspace==components (doubles as the disconnection detector). Locks operator
      correctness. (ALGORITHM_REGISTER: rating-5 items.)

### Week 2 — The go/no-go gate (this shapes the entire submission)
- [ ] **Apo/holo superposition + cryptic-openness + Tama–Sanejouand cumulative
      overlap**, per mandatory target. The decisive question: does the apo→holo
      direction live in the low modes? Record CO(m) per target. Expect KRAS to fail
      (cryptic) — a publishable finding, not a failure.
- [ ] **Ceiling measurement** on clean-data targets: best supervised fit vs random +
      surface + degree baselines, with block-bootstrap CI. Know the ceiling before
      any blind work.
- [ ] **Decision:** which targets clear the gate → get the holo-direction module;
      which are walls → become the honest competence-map negatives.

### Week 3 — Lock the story, start the submission
- [ ] Write the central claim from Week-2 evidence. Likely shape: *"topology-only
      quantum transport, a rigorous per-target competence map, and an honest bound on
      when cryptic pockets are recoverable from apo — with holo-direction prediction +
      ENAQT-on-predicted-graph as the forward-looking, falsifiable innovation."*
- [ ] **NISQ noise study (design + small demo):** Trotterized e^{-iHt}, N≤~12–16
      qubits, depolarizing + amplitude-damping; ranking degradation vs depth/error;
      test whether ENAQT/QSW is *more* robust than coherent CTQW. This is the
      scoreable secondary objective — at minimum a credible feasibility demo.
- [ ] Draft Phase 1 sections against the rubric (Problem/Impact 25, Technical 25,
      Feasibility 20, Validation 15, Hybrid 5, Team 10).

### Week 4 — Forward-looking module as evidence + write
- [ ] For gate-passing targets only: two-state ANM / NMFF morph (recompute Hessian
      each step; drive on global residual) → edge-opening event sequence → small
      ENAQT-on-predicted-graph run. This is the characterization tool (holo known),
      not the blind predictor.
- [ ] Competence map as the submission centerpiece: per-target, falsifiable, with the
      ceiling and the overlap number attached.

### Weeks 5→deadline (sketch)
Expand to ~10–15 verified targets for a meaningful LOPO (verify ASD entries first —
same RCSB check as the mandatory four). Finalize NISQ noise results. Polish the
submission. Only build blind LOPO for targets whose ceiling clears the baselines.

---

## Open items / risks
- **Myosin**: verify 6C1H contains mavacamten or replace with a clean S1/motor-domain
  structure; otherwise keep quarantined.
- **MYC**: no pocket exists in 1NKP; use p53-Y220C as the learning-base analog (TF
  with a real validated cryptic pocket + apo/holo + drugs).
- **ASD targets**: 11 unverified; each needs the RCSB anchor check before entering
  LOPO. Several are oligomeric — resolve assembly.
- **Reference hygiene**: double-check venue for Plastic Network Model (Maragakis &
  Karplus 2005) and Morph Server (Krebs & Gerstein 2000) before the bibliography.
- **Scope discipline**: no force fields, no mutations-as-refinement in the accuracy
  ladder (rules/scope violations). Solvent-like perturbation is the only sanctioned
  refinement.

## The one thing not to do
Don't over-build the pipeline before the submission, and don't bolt on undefendable
novelty for the judges. Phase 1 is ideation — preliminary evidence + a rigorous,
honest plan wins. The advantage is the honesty; protect it.
```