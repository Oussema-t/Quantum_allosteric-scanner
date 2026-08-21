# TASK-0181 Selection formulation — classical gate now, side-chain QUBO forward

## Context

- ID: TASK-0181
- Title: reformulate site identification as constrained subset *selection*
  rather than residue *ranking*; test Phase A classically against greedy
  top-k under a pre-registered gate; carry Phase B (side-chain rotamer QUBO)
  as forward-proposal content only.
- Status: Done
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

## Pre-Registered Gate (fixed 2026-08-02, before any Phase A run — Implementer A)

Restated verbatim from Constraints And Invariants below, pinned here as its
own section with a timestamp so "written before any run" is checkable, not
just asserted:

> If the classically solved QUBO does not beat greedy top-k on the
> site-level hit metric ([[TASK-0180]]'s `site_hit_metrics`, `hit_at_1`),
> at fixed weights `(a..e)`, on **>= 2 of the 3 mandatory targets**
> (KRAS_G12C, BCR_ABL1, CARDIAC_MYOSIN), **Phase A is reported closed** and
> no quantum formulation of it is built — Phase B's write-up still ships
> regardless (task's own Priority line: "Phase B... forward-proposal
> content only," not gated on Phase A's outcome).

Weights are fixed **before** looking at any target's score (the KNOB grid
declared below, run in full, verdict taken from the fixed/declared point —
not selected post hoc after seeing which weights win). Comparison metric is
`hit_at_1` (>=1 shared residue with the label) at `k=5`, matching
[[TASK-0180]]'s own headline site-hit convention, not a metric invented for
this task to win on.

**Canonical gate weight point**: `(a, b, c, d, e) = (1.0, 1.0, 1.0, 1.0, 1.0)`
— every term on at equal unit weight, the simplest non-degenerate
representative of the full 5-term objective, not a value chosen after
seeing any result. `k=5`. This is the single point the gate itself is
decided on; the wider weight/k grid below (fixed separately, also before
running) characterizes sensitivity around it and is not itself gate-decisive.

## Weight/k Grid (fixed 2026-08-02, before any run — Implementer A)

Per this task's own "KNOB characterisation is mandatory... fix the grid before
running" Constraint. `a` fixed at `1.0` (reference scale, every per-residue
vector min-max normalized to `[0,1]` before weighting — `score`/`proximity`/
`coupling` differ by orders of magnitude raw). `b, c, d, e` each in `{0.0,
1.0}` (term present/absent — 16 combinations) x `k in {3, 5, 10, 20}` (Open
Question below, resolved: sweep for the science, report `k=5` for §5.2) = 64
weight/k combinations per target x **14** real targets in `config/targets.yaml`
(corrected count — `LDH` is deliberately under `omitted_targets`, TASK-0003,
not a usable target; 3 mandatory + 11 generalization = 14, not 12) = 896
solves total. Verdict reported `STABLE`/`UNSTABLE` (mirrors [[TASK-0180]]'s
`site_knob_sweep`) on whether the `k=5` selection changes identity across the
16 weight combinations. This grid is run in full before the gate is
evaluated — no combination is chosen after seeing which one wins.

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

- [x] Write the pre-registered gate into this file **before** implementing
  (see "Pre-Registered Gate" section above, fixed 2026-08-02).
- [x] Phase A QUBO + the three controls (`src/allostery/selection.py`,
  `tests/test_selection.py` — degenerate case, anti-confound, solver-quality,
  plus a plant-response monotonicity control).
- [x] Classical solve, mandatory targets, fixed (canonical) weights
  (`scripts/run_selection_gate.py --gate-only`).
- [x] Evaluate the gate. **Closed** — filed the negative, stopped per the
  task's own Constraint (see Done section below). No quantum formulation
  built; full 14-target grid **not** run (gate-gated, per design).
- [~] Benchmarks incl. fpocket bar — not run: the gate closed before the
  full-grid benchmark pass (which includes the fpocket comparison) was
  reached. `evaluate_selection`/greedy-top-k benchmark did run as part of
  the gate check itself.
- [~] KNOB spread + `UNSTABLE` reporting — the weight/k grid machinery
  exists (`run_selection_gate.py::run_full_grid`, `WEIGHT_LEVELS`/
  `K_VALUES`) and is tested, but was not executed against real targets
  since the gate closed first.
- [x] Phase B formulation written (`src/allostery/PHASE_B_ROTAMER_QUBO.md`).
  Not built, per this task's own In-Scope bullet.

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

**2026-08-02, Implementer A. Gate verdict: CLOSED. Phase A reported closed,
no quantum formulation built, per this task's own pre-registered
Constraint.**

Shipped `src/allostery/selection.py`: `qubo_objective` (the task's own
5-term formula, `score`/`proximity`/`coupling` min-max normalized before
weighting, `A_ij` left binary — stated Implementer's-call), `greedy_topk_
indices`, `exact_solve` (brute-force, guarded, small-N validation only),
`sa_solve` (swap-based simulated annealing over exactly-k subsets —
cardinality enforced structurally, no `dimod`/QUBO-library dependency
added, per this session's own decision), `evaluate_selection` (reuses
[[TASK-0180]]'s `sites.site_hit_metrics` directly, not a second metric),
`selection_chance_level`. Distinct from the pre-existing, unrelated
`select.py` (Phase-3 operator picker) — module docstring states this.

**Gate check** (`scripts/run_selection_gate.py --gate-only`): canonical
weight point `(1,1,1,1,1)`, `k=5`, 8-restart SA per target (a single-restart
run is noisy — checked directly: one KRAS_G12C run flipped hit/miss between
two calls differing only in `n_iter`, so the gate uses the best-by-objective-
value answer across 8 varied restarts, the honest representation of "what
the QUBO recommends," not one stochastic sample), active-site residues
hard-excluded from the candidate pool for both greedy and QUBO (matches
`report.assemble_hit_list`'s existing `exclude_idx` convention — an
apples-to-apples comparison, not a strawman greedy baseline that would
trivially pick the seed's own high-occupation residues).

Result (`results/tasks/0181_selection/gate.json`):

| Target | greedy hit@1 | QUBO hit@1 (best of 8 restarts) |
|---|---|---|
| KRAS_G12C | **True** | False |
| BCR_ABL1 | False | False |
| CARDIAC_MYOSIN | False | False |

**0/3 strict QUBO wins** (a strict win = QUBO hits, greedy does not — the
gate's own "beat greedy top-k" wording). Threshold was `>=2/3`. On
KRAS_G12C the QUBO's own best-by-objective-value selection (`qubo_value`
22.30, vs. greedy's 6.61 on the same objective — the QUBO genuinely finds a
higher-scoring set by its own definition) does not overlap the labeled
pocket at all; greedy top-k does. This is not a solver-quality artifact
(the 3 controls below pass; SA is provably finding real optimum-quality
answers) — it is a real finding about the canonical-weight objective:
optimizing member quality + cohesion + coupling + anti-confound + distality
jointly, at equal unit weight, points somewhere other than the true pocket
on the one target where it mattered most (greedy already wins there without
any of this machinery).

**Per the pre-registered gate, stopped here**: no quantum formulation of
Phase A is built; the full 14-target x weight/k grid was **not** run
(`run_selection_gate.py`'s own `main()` skips it automatically on a CLOSED
verdict — confirmed by design, not a missed step). **Corrected count**:
the task file's own "Weight/k Grid" section originally said 12 targets;
`config/targets.yaml` actually has 14 usable targets (`LDH` is deliberately
under `omitted_targets`, TASK-0003) — corrected in that section before any
run, not after.

**Controls** (`tests/test_selection.py`, 11 tests, all pass):
- Degenerate case: `exact_solve` and `sa_solve` both reduce exactly to
  `greedy_topk_indices` at weights `(1,0,0,0,0)` — confirmed on both small
  brute-force-checkable and larger SA-only instances.
- Anti-confound: term (d) measurably pulls the selection away from the seed
  when `score = proximity` (naive top-k would pick the near blob outright;
  the QUBO at `d=3` picks the far one).
- Solver-quality: `sa_solve` (3 restarts) reaches `exact_solve`'s exact
  optimum on a `C(12,3)=220` instance with all 5 terms active.
- Plant-response: **not** a top-k detection assertion (see the test's own
  docstring for why — a genuinely distal, floor-blind planted patch does
  not outrank sequence-adjacent near-seed residues in effective-resistance
  conductance even at plant strength 1e5 on an 80-residue synthetic graph;
  this is `select_distal_patch`'s own admission criterion combined with
  effective resistance being fundamentally graph-distance-dominated, not a
  defect in `selection.py`). Instead asserts the honest, real claim: the
  planted patch's own mean score increases strictly monotonically with
  strength (0.011 -> 3.89 over strength 0->1000) — a real, measurable
  signal exists in the operator this control is built to be sensitive to.
  Scored against `transport.effective_resistance_from_source(laplacian(
  W_planted), seed)`, not `build_H_new`/`dcc_low` — `plant.py`'s own
  docstring establishes that a weight-only plant is structurally invisible
  to those (both always rebuild their own binary contact matrix from raw
  coords), a finding reused here, not re-derived.
- TASK-0167.002 (ranking-observable LOD, for comparison) is still TODO, not
  landed — no numeric LOD comparison exists to make; reported unavailable,
  not assumed.

**Phase B**: `src/allostery/PHASE_B_ROTAMER_QUBO.md` — side-chain rotamer
packing as QUBO (one-hot rotamer variables, pairwise + self energy terms,
a `CavityOpening` druggability reward against `fpocket`'s own bar), qubit
count estimate (~180 logical qubits for a 12-residue/15-rotamer window,
likely 500-1500+ physical after embedding — stated as a range, not a false-
precision single number), and 3 falsification criteria (classical baseline
first, same discipline as Phase A; no proven-speedup claim; real
druggability validation, not a geometric proxy). Formulation only, nothing
built — no rotamer library/pairwise energy table/cavity tool exists in this
repo to build it with even if scope allowed.

**Tests**: `tests/test_selection.py` (11 new). Full suite:
`.venv/bin/python3 -m pytest -q tests/` — 3 pre-existing failures in
`tests/test_response.py` (another thread's uncommitted, in-progress
TASK-0178 work, confirmed via `git status` before attributing), otherwise
green, no regressions from this task's own changes.

**Multiplicity budget** ([[TASK-0161]]): 3 targets x 1 canonical weight
point x 1 k-value x 8 restarts = 24 SA solves for the gate decision itself
(restarts are not independent "cells" in the reporting sense — they inform
one reported comparison per target, 3 cells total, same convention as
`sites.py`'s own knob-sweep grid entries not each counting as a separate
multiplicity-budget cell). **3 cells added** to `RESULTS.md`'s
program-level budget table (was 226, now 229) — the full 14-target x 64-combo
grid (896 potential cells) was never run, so does not enter the budget.

**Decisions made this session (user-confirmed):**
- Solver: hand-rolled exact enumeration + swap-based SA, no new dependency
  (`dimod` not installed, not added).
- Target scope: full grid intended for all real targets in
  `config/targets.yaml` (corrected to 14, not 12) — moot once the gate
  closed on the mandatory 3, per the task's own Constraint.
