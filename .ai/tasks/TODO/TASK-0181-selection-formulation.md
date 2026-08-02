# TASK-0181 Selection formulation — classical gate now, side-chain QUBO forward

## Context

- ID: TASK-0181
- Title: reformulate site identification as constrained subset *selection*
  rather than residue *ranking*; test Phase A classically against greedy
  top-k under a pre-registered gate; carry Phase B (side-chain rotamer QUBO)
  as forward-proposal content only.
- Status: TODO
- Owner: Implementer (Phase A), Architect/Planner (gate + Phase B write-up)
- Claimed By: —
- Claimed At: —
- Source: `REVIEW-panel-2026-07-28-external.md` §7; escalated 2026-07-29 on
  the reframing *the phenomenon need not be quantum for the algorithm to be*.
- Priority: **P1. Phase A only before the 2026-08-07 freeze.**
- **Revised 2026-07-29.** The original filing proposed QUBO on the static
  contact graph as the headline quantum claim. Measurement since (see
  [[TASK-0185]]) shows the *backbone* layer is not where the hardness is.
  Phase A survives as a cheap falsifiable probe; the defensible quantum claim
  moves to Phase B.
- Suggested Predecessor: **[[TASK-0180]]**, same thread. Not a hard
  dependency (this task's QUBO construction doesn't need 0180's code to
  exist), but its own benchmark list includes 0180's site-level clustering
  and chance-level metric directly — start this only once 0180 has landed,
  or expect to re-run the comparison once it does. Recorded 2026-08-01
  (Architect).

## Why this matters — and what changed

Every other quantum route is complexity-dead. Ruled out on evidence:
Grover/HHL/QML (complexity), ENAQT ([[TASK-0068]]/[[TASK-0083]]), chirality,
persistent H₂ ([[TASK-0143]]), entanglement entropy ([[TASK-0148]]), spectral
coherence ([[TASK-0146]]), interacting multi-particle walks (argument valid
only at U=0, then confirmed empirically 2026-07-28: both the marginal and the
non-reducible G2 stay ρ≈0.88–0.90 with single-particle, and the proximity
confound *worsens*, 0.73→0.82). The anchoring theorem stands.

Selection remains structurally different from ranking on three counts:

1. **Complexity class.** Densest-k-subgraph is NP-hard.
2. **Output shape.** Five sites — O(1) readout. Contrast the challenge's own
   §5.1 N×N matrix, whose O(N²) readout structurally forecloses any quantum
   linear-algebra speedup (measured 2026-07-29).
3. **It can express set-level constraints a ranking cannot.** A ranking scores
   residues independently; it cannot penalise a *set* for being collectively
   near the seed. `main`'s `min_sep`/`distal_ang` are post-hoc versions of
   exactly that, and [[TASK-0075]] showed that class of knob flips go/no-go in
   15 of 18 combinations.

**What changed:** the assumption that the search itself is hard does not
survive measurement at the backbone layer. Under ENM-mode sampling, pocket
opening is *not* rare (p = 0.24–0.69), and even conjunctive druggability
constraints give joint p ≈ 0.0017–0.005 — ~200–600 classical draws. **Side-chain
rotamer packing, by contrast, is discrete and NP-hard** (Pierce & Winfree
2002) and is where cryptic pockets actually open. That is Phase B.

## Phase A — the classical probe (before freeze)

Select `S`, `|S| = k`, maximising

```
  Q(S) =  a * Σ_{i∈S} score_i              (member quality)
        + b * Σ_{i,j∈S} A_ij               (spatial cohesion -> a real pocket)
        + c * coupling(S, active_site)     (allosteric relevance; [[TASK-0178]]'s ddG if landed)
        - d * Σ_{i∈S} proximity_i          (set-level anti-confound penalty)
        - e * |S ∩ active_site|            (distality)
```

Binary `x_i`, cardinality by penalty — standard QUBO, directly expressible for
annealers and QAOA. **Solved classically at N ≤ 704.** The point is that if
this does not beat greedy top-k *classically*, there is nothing for a quantum
solver to accelerate and the route closes cheaply.

## Intent Contract

- Outcome: `allostery.selection` with the QUBO objective solved classically,
  benchmarked against greedy top-k, [[TASK-0180]]'s clustering, fpocket, and a
  proximity-only selection floor — plus a written Phase-B formulation for the
  proposal.
- Why required, not assumed: no selection-based formulation has been tested
  here, classically or otherwise; the register's entire negative rests on
  ranking observables.

- In Scope — **Phase A:**
  - QUBO construction, all five terms; weights `(a..e)` as a declared KNOB
    family.
  - Classical solve on all mandatory + generalization targets.
  - Benchmarks: greedy top-k, [[TASK-0180]] clustering, **fpocket
    (0.8348/0.8596 — the bar that actually matters)**, proximity-only floor.
  - Scored against [[TASK-0177]]'s label with [[TASK-0180]]'s site-level hit
    metric and its chance level.
  - **KNOB characterisation is mandatory.** Five weights is a large tuning
    surface and fitting them to the answer key is the single biggest threat to
    this task's credibility. Fix the grid before running; report spread; emit
    `UNSTABLE` if weights decide the top-5. `frozen_context` throughout.

- In Scope — **Phase B (write-up only before freeze):**
  - Formulate side-chain rotamer packing as QUBO: given apo backbone plus a
    candidate ENM deformation, find the rotamer assignment minimising packing
    energy subject to opening a cavity meeting fpocket's druggability
    criteria. State the encoding (one-hot rotamer variables, pairwise energy
    terms, constraint penalties), the qubit count, and the falsification
    criteria. **Do not build it.**

- Out Of Scope:
  - Any claim of quantum speedup. NP-hardness permits a heuristic claim, not a
    proven one; QAOA has no general performance guarantee and the proposal
    must say so.
  - Replacing the §5.2 hit list unless Phase A wins its gate.
  - Tuning weights against the holo label.
  - Building Phase B before the freeze.

- Constraints And Invariants:
  - **Pre-registered gate, written before any run:** *if the classically
    solved QUBO does not beat greedy top-k on the site-level hit metric, at
    fixed weights, on ≥2 of 3 mandatory targets, Phase A is reported closed
    and no quantum formulation of it is built.* A quantum solver for an
    objective that loses classically is precisely the "superficial quantum
    framing" criterion 2 names.
  - Apo-only inputs; label for scoring only.
  - Adds cells to the multiplicity budget — update [[TASK-0161]].

- Planned Validation:
  - **Degenerate-case control:** with `b=c=d=e=0` the QUBO must reduce exactly
    to greedy top-k. Asserted. If not, the encoding is wrong.
  - **Anti-confound control:** on a pure distance-to-seed score field, term (d)
    must actively pull the selection away from the seed. If it cannot, the
    formulation's main claimed advantage is not real.
  - **Solver-quality control:** for small N, compare heuristic solve to
    exhaustive enumeration. A result that is a solver artifact is worse than
    none.
  - Plant response: QUBO selection should recover the planted patch at a lower
    strength than the ranking observables' LOD ([[TASK-0167.002]]). If not,
    its advantage is formulation-only — still worth reporting, but say so.

## In Progress

None

## TODO

- [ ] Write the pre-registered gate into this file **before** implementing.
- [ ] Phase A QUBO + the three controls.
- [ ] Classical solve, all targets, fixed weights.
- [ ] Benchmarks incl. fpocket bar.
- [ ] KNOB spread + `UNSTABLE` reporting.
- [ ] Evaluate the gate. If closed: file the negative and stop.
- [ ] Phase B formulation written for [[TASK-0184]] / [[TASK-0185]]. Not built.

## Dependency

- [[TASK-0180]] — site-level hit metric and chance level.
- [[TASK-0177]] — consensus label (incumbent usable meanwhile).
- [[TASK-0163]] (Done) — fpocket bar.
- [[TASK-0167.001]] (Done) — `plant.py`.
- [[TASK-0178]] — supplies term (c) if landed; incumbent observable otherwise.
- [[TASK-0185]] — the conformational-search framing Phase B belongs to.

## Open Questions

- `k` fixed at 5 (the deliverable) or swept? Sweep 3–20 for the science,
  report k=5 for §5.2.
- Classical solver: `dimod` exact for N ≤ ~30 after coarse-graining, simulated
  annealing above. Declare under the usual dependency-disclosure convention.
- Does selection on the *coarse-grained* graph ([[TASK-0172]]) lose the residue
  resolution §5.2 needs? Likely — the natural pipeline is coarse-select then
  refine at full resolution. Flag; v2.

## Done

(not yet)
