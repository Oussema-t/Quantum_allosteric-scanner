# TASK-0228 (re-indexed from the 2026-08-21 external drop's "TASK-0212_conformer_graph_search")

## Context

- ID: TASK-0228
- Status: In Progress
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `.ai/reviews/2026-08-21/TASK-0212_conformer_graph_search.md` — external session, no repo
  access, no rcsb.org egress. **Every numeric in the body below was run on
  bundled non-target structures (prody / MDAnalysisTests). Nothing in it may be
  cited in the submission before a PDB-retest on real challenge targets.**
- **Re-indexed on filing.** The drop numbered this `TASK-0212_conformer_graph_search`, but that ID is
  already taken in this register by unrelated, completed work:
  TASK-0210 (coupled backbone+rotamer search, Done), TASK-0211 (ensemble-graph
  observable independence, Done), TASK-0212 (frustration-rank reproducibility,
  closed as invalidated). Renumbered to TASK-0228 rather than the incumbents,
  per this register's own collision precedent (TASK-0156/0157, TASK-0168).
  **Cross-references inside the body below still use the drop's own numbering**
  and are mapped here: drop 0210 → TASK-0226, drop 0211 → TASK-0227,
  drop 0212 → TASK-0228.

---

## Intent Contract

*(Added on pickup — the re-indexed drop above had no Intent Contract of
its own, only the raw external document. Scoped here to this pickup's
actual outcome, not the full multi-week program the drop sketches.)*

- Outcome: run this document's own named "cheapest path to a decision"
  first step — §2's PDB-RETEST — for the **pocket-restricted** half of
  the question specifically (does an adaptive ANM subspace capture the
  real, labeled druggable-pocket displacement better than a static
  subspace of the same dimension, on real target pairs), and record the
  result honestly against the synthetic-toy claim it corrects.
- Why scoped this narrowly, not the whole document: [[TASK-0227]] (same
  2026-08-21 external-drop batch, a sibling task, picked up in parallel
  this session by a different thread under the same user instruction
  pattern) already ran this document's §2 for the **whole-structure**
  apo→holo displacement, on the same 3 real target pairs, and explicitly
  left the pocket-restricted sub-question — this task's own original §2,
  in the drop's own numbering — for "whoever picks TASK-0228 up next"
  (see that task's own Out Of Scope / Done section). This task now closes
  exactly that gap rather than re-deriving the whole-structure number a
  second time.
- In Scope:
  - `adaptive_anm_modes` in `allostery/superpose.py`: an adaptive
    (per-step-recomputed) ANM subspace union, built on this module's own
    validated `H13_3N_anm_hessian` (TASK-0005) rather than re-deriving a
    second Hessian implementation — re-derives the drop's own
    `adaptive_union` construction, not a novel algorithm.
  - Real-target measurement: static vs. adaptive `restricted_cumulative_
    overlap` (TASK-0133's pocket-restricted quantity — Bessel-inequality-
    valid for a small residue subset, unlike a naive renormalized-slice
    approach) against each mandatory target's own real, labeled pocket
    displacement, at equal dimension, reusing `compute_learnability`'s
    existing fetch/alignment/labeling path (`learnability_gate.py`'s own
    `run_one`), not re-derived.
  - Test coverage for `adaptive_anm_modes` (orthonormality, dimension
    bound, determinism, compatibility with `restricted_cumulative_
    overlap`).
  - Cross-reference into [[TASK-0227]]'s own RESULTS.md section (claimed
    first, per [[TASK-0195]]'s protocol) once that section's held claim
    frees up — not a new section, an addendum to the existing one, since
    both halves answer the same original §5.1/§2 question.
  - Added mid-pickup, on direct user instruction: §6.2's `p` measurement,
    collective-move-layer only (see In Scope amendment / In Progress
    below) — the document's own named next-cheapest step, scoped to what
    existing tooling can actually measure.
- Out Of Scope (this pickup; real, substantial remaining document
  content, not silently dropped):
  - §3's branching-factor/depth reframing itself — this task's own
    nominal subject — not measured here. §2's result (adaptive does not
    reliably beat static on real pocket displacements, see Done) is a
    precondition check on the adaptive-subspace *move set* §3 assumes,
    not the branching/depth measurement itself.
  - §4's move-set/blocked-move-detector/search algorithm — not built.
  - §5's supervised-path ceiling — not run (needs the conformer-graph
    search infrastructure §4 would provide).
  - §6.1/§6.3/§6.4 (path depth, heuristic informativeness, classical
    baseline) — not run. §6.2 (progress probability `p`) — a
    **collective-only partial** version *was* built and run this pickup
    (added after the section below was first written; see In Progress) —
    the full joint version the document specifies remains blocked on a
    missing rotamer packer, filed as [[Q-0004]].
  - §7's Cleveland Clinic constraint-3 question — not filed into a
    question list here (that list's location/owner not confirmed this
    pickup); flagged, not resolved.
- Constraints And Invariants: research-tree only
  (`__WORK_IN_PROGRESS__/`), no `backend/` change; every real-target
  number traced to a real RCSB fetch, no synthetic stand-in cited as if
  real (matching the drop's own explicit warning on its synthetic
  numbers).
- Planned Validation: real fetched structures for all 3 mandatory
  targets; equal-dimension static/adaptive comparison (never omit,
  per both the drop's own and TASK-0227's explicit convention); a
  regression test suite for the new function, run green before and after.

---

## Original document, verbatim

# TASK-0212 — Conformer-graph search: mode mixing, branching/depth, and the quantum type question

**Status:** HYPOTHESIS / spec, with two OBSERVED results on non-target structures.
**Date:** 2026-08-21. External session, no repo access, no rcsb egress.
**Relationship to TASK-0211:** extends it. **Contains a correction to TASK-0211 §3 — see §2.**
**Origin:** proposed by Bartosz (ribbon toy, three cases). Analysis and caveats added here.

---

## 0. One-paragraph statement

Apo→holo transition is reframed as **search over a graph of conformers**, generated by a
move set drawn from an *adaptive* (per-step recomputed) elastic-network basis plus local
relief moves plus rotamer repacking — not as a single deformation, and not as MD. The
proposal is that a designed toy exposes a **branching-factor / path-depth trade-off**, and
that this trade-off, not "is allostery quantum," is the tractable form of the quantum
question. This document specifies the toy, the corrections required to the original
inference chain, and the measurements that would decide it.

---

## 1. The ribbon toy (as proposed)

A ribbon folded in 2D, up/down/up/down, forming a sheet; optional coil adding a rotamer-
(mis)alignment degree of freedom. Three configurations:

- **H (holo):** flat sheet. Target.
- **AH (apo-hinge):** one turn bent 90°. Reachable from H by a single low-frequency mode.
- **AK (apo-kink):** mostly H, but one bend additionally displaced **out of plane**.
  Reachable **either** by one local high-frequency move (flatten the kink directly)
  **or** by ≥2 low-frequency moves (swing the half-sheet to expose the kink, flatten,
  swing back).

### 1.1 What the toy is for
- **PRIMARY:** demonstrate that the same endpoint is reachable by different mode
  compositions → **the move set is a free design parameter**, and low/high mode separation
  is not a property of the target but of the chosen basis.
- **SECONDARY:** debug the blocked-move detector (§4.2) on an instance where ground truth
  is known by construction.

### 1.2 What the toy is NOT
**It is a synthetic GATE TEST, not a result.** Sterics in a 2D ribbon are trivial compared
to a packed protein core; rotamer combinatorics are absent or toy-scale. File under the
same convention as the chiral/Hodge synthetic gate tests. **No number from the toy may be
cited as evidence about proteins.** Passing the gate licenses building the real harness;
it licenses nothing else.

---

## 2. CORRECTION to TASK-0211 §3 — adaptive subspaces reach what static ones cannot

TASK-0211 §3 reported that local pocket-opening deformation has ~0.000 overlap with the
top-k ANM modes at apo, and diagnosed a "scale gap." **That measurement used a STATIC
subspace and was over-read.** The user's AK argument is that a sequence of low-mode steps
in a *rotating* subspace reaches what one step cannot. That is correct.

**OBSERVED (ADK, N=214, 40 surface sites, equal-dimension comparison):**

| subspace, dim = 110 | overlap with local pocket-opening displacement |
|---|---|
| STATIC — top-110 ANM modes at apo | 0.0244 ± 0.0229 |
| **ADAPTIVE — 11 structures × top-10 modes** (apo + steps along ±modes 1–5, Hessian rebuilt) | **0.2294 ± 0.1635** |
| ratio | **9.39×** |

Construction: step amplitude ≈ 6 Å RMSD along each of the first 5 modes, both signs;
Hessian rebuilt at each deformed structure; union QR-orthonormalised; compared against a
static subspace of *identical dimension* so the gain is not a dimension artefact.

**Revised diagnosis.** The Hessian is configuration-dependent, so mode composition is not
additive along a nonlinear path — the reachable set grows with iteration in a way no
fixed-basis span measures. The scale gap in TASK-0211 §3 is **real but ~9× smaller than
reported**, and is a statement about single-step non-adaptive ANM only.

**Residual concern stands, reduced.** 0.229 is still not 1.0. One adaptive step recovers
about a quarter of the required local deformation. This is consistent with the AK
prediction (multiple steps needed) and with a genuine, smaller local-backbone gap.

**PDB-RETEST:** repeat on 4OBE, 1OPL, 5TBY with the true apo→holo displacement replacing
the synthetic opening vector. Script: `anm_mode_overlap.py` (swap the target vector).

---

## 3. The reformulation this yields — branching factor vs depth

The AK case's two routes to the same endpoint are not a curiosity. They expose:

- larger move set (low **+** local/high modes) → **larger branching factor b, smaller depth d**
- restricted move set (low modes only) → **smaller b, larger d**
- search cost ≈ **b^d** (blind), or **b_eff^d** where b_eff reflects heuristic pruning

**This is the tractable form of the quantum question for this program.** Not "is allosteric
propagation quantum" — which the program has already answered negatively at the ENM layer
— but "what are b, d, and b_eff for apo→holo conformer search, and does any quantum
algorithm improve the resulting scaling."

---

## 4. Algorithm sketch

### 4.1 Move set (per node in the conformer graph)
1. **Collective:** step ±α along each of the top-k modes of the **current** structure
   (Hessian rebuilt per node — adaptive, per §2 and ref [15]).
2. **Local relief:** fragment/loop moves at sites flagged by §4.2.
3. **Repack:** EvoEF2 rotamer optimisation, solved to **global** optimum (DEE/A* or ILP),
   not a heuristic — see §6.3.
4. Reject nodes failing a steric/energy admissibility gate.

### 4.2 Blocked-move detector ("which high modes to inspect")
Well-posed and known art (eigenvector-following / mode-following family): after a
collective step, compute the **residual clash force** (gradient of the repulsive term),
project it onto the current mode basis, and rank modes by projection magnitude. Top
contributors are the modes that relieve the obstruction. Cheap; no new theory required.
**Describe it as a member of a known family, not as novel.**

### 4.3 Search
Best-first / backtracking over the conformer graph with an energy-based pruning predicate.
**Not MD.** See §7 for the constraint-3 question.

---

## 5. BROKEN INFERENCE — supervised path ≠ search difficulty

The original proposal states that iteratively improving *current-vs-holo* would "prove that
apo-based exploration is possible" and "say about its difficulty (whether quantum brings
any potential advantage)."

**The first clause holds. The second does not.**

Optimising RMSD-to-holo is **supervised** — the objective is a structure already in hand.
Guided descent to a known target is trivially easier than unguided search. The supervised
run measures **reachability** and **path depth d**. It measures **nothing** about the cost
of finding that path without the answer.

**Consequences:**
- The supervised experiment is a **CEILING**, the multi-step generalisation of
  TASK-0211 §5.2. **File under `ceiling.md` with an explicit label-leakage header.**
  It can never be converted into a predictor.
- Any difficulty claim requires the **unsupervised** objective from TASK-0211 §6.1:
  minimum energy cost to open a druggable pocket at site j, with a pocket-volume
  constraint. Not RMSD to holo.

---

## 6. Measurements that would actually decide it

Run in this order. **Pre-register thresholds before running.**

### 6.1 d — path depth (supervised, ceiling)
Number of admissible moves on the shortest found apo→holo path. Report per target.

### 6.2 p — progress probability. **THE DECISION VARIABLE.**
At each node, the fraction of admissible moves that reduce the objective.
- Prior program finding: p = 0.24–0.69 for ENM pocket opening → **amplitude amplification
  contributes nothing at that layer** (√ of a large p is not a speedup worth having).
- **If joint backbone⊗local⊗rotamer moves have p orders of magnitude smaller, amplitude
  amplification is re-opened at this layer.** If p stays in the 0.1–0.7 band, AA stays dead
  and this document's quantum section should be retired.
- **This is the single cheapest decisive measurement in the proposal. Do it early.**

### 6.3 b_eff — heuristic informativeness
Correlation between the energy objective and true progress, along and off the path.
- Energy a good heuristic → classical best-first search is easy → nothing to win.
- Energy uninformative/rugged → search is hard **for everyone**, see §8.

### 6.4 Typical-case classical baseline
Solve instances with DEE/A*, ILP (OSPREY/SCWRL4-class), and simulated annealing.
**A quantum claim requires beating these on typical instances, not citing worst-case
NP-hardness.** Same failure mode as the soft-mode result — see TASK-0211 §6.3.

---

## 7. Question for the Cleveland Clinic team

Constraint 3 forbids reliance on **"classical MD trajectories as inputs."** A conformer
graph generated by ENM modes plus energy minimisation plus rotamer repacking is not an MD
trajectory — no integrator, no time evolution, no thermostat. **Confirm that
minimisation-based and Monte-Carlo-style conformational sampling is in scope**, since a
broad reading of "no classical MD" could be taken to exclude it. Add to the existing
question list alongside the Section 5 / ref [4][9] tension.

---

## 8. Quantum framing — the best-typed target in the program, with limits

**Move the walk from the residue contact graph to the CONFORMER graph.**

### 8.1 Why this is structurally different
- **The proximity confound cannot exist here.** That confound (TASK-0210) is
  distance-to-seed on a *spatially embedded* graph. A conformer graph has no spatial
  embedding. This is an escape by construction, not a mitigation.
- **It preserves the program's CTQW investment** on an object where a walk is the
  appropriate tool rather than a distance detector.

### 8.2 Correctly-typed algorithms
- **Montanaro, quantum backtracking (quantum walk on the search tree), 2015** —
  Õ(√(Tn)) for backtracking search over a tree of size T. Conformer exploration with
  pruning **is** backtracking search. This is the closest type-match found anywhere in
  this program.
- **Szegedy quantum walk** hitting-time speedups on the same structure.
- **Amplitude amplification** — viability decided entirely by §6.2.

### 8.3 Limits that must be stated, not buried
1. **Quadratic, not exponential.** Do not imply otherwise.
2. **Requires an efficiently evaluable pruning predicate** and coherent oracle access to
   node neighbours. Circuit-depth implications under constraint 2 must be quoted.
3. **Rugged ≠ quantum-advantaged.** Quantum annealing helps with *tall, thin* barriers,
   not general ruggedness; advantage regimes in the literature are narrow. If §6.3 shows a
   rugged landscape, that is **not** by itself an argument for quantum.
4. **Exponentially large implicit graph** — the walk must be over an implicitly defined
   node set. State the oracle construction explicitly or the claim is not credible.

---

## 9. Verdict and disposition

The proposal is **sound in structure, with one broken inference (§5) and one correction it
supplies to prior work (§2)**. It is untested. It is not excluded.

**For the submission:** this belongs in the forward-proposal section as the program's
best-typed surviving quantum direction, stated with §8.3's limits attached and with §6.2
named as the pre-registered falsification. **It must not be presented as validated.**

**Cheapest path to a decision:** §2 PDB-retest (hours) → §6.2 p-measurement (days) →
§5 ceiling (days). If §6.2 returns p in the 0.1–0.7 band and §6.3 shows an informative
energy heuristic, **retire the arm** — that is a clean, reportable negative consistent with
the program's existing frame, and it is a better outcome than carrying an unfalsified
proposal into the submission.

---

## TODO

- [x] Build the adaptive ANM subspace union on this module's own validated
      Hessian, not a re-derivation.
- [x] Real-target measurement: static vs. adaptive pocket-restricted
      cumulative overlap, equal dimension, 3 mandatory targets.
- [x] Regression tests for the new function.
- [ ] RESULTS.md addendum to [[TASK-0227]]'s section (blocked on that
      section's held claim for 7+ hours as of this checkbox — see In
      Progress for the staleness-override plan).
- [x] §6.2 (progress probability `p`) — both collective-only and full
      joint (backbone+rotamer) versions built and run on real targets.
      [[Q-0004]] retracted (premise invalidated, not answered).
- [ ] §3 branching/depth measurement itself, §4 search infrastructure, §5
      ceiling. Not started.

## Dependency

- [[TASK-0227]] — sibling task, same 2026-08-21 external-drop batch,
  already ran this document's §2 for the whole-structure displacement on
  the same 3 real target pairs; this task's own work is the pocket-
  restricted complement TASK-0227's own Done section explicitly left for
  whoever picked TASK-0228 up.
- [[TASK-0195]] — the claim/staleness protocol this task's own RESULTS.md
  addendum follows.
- [[TASK-0133]] — `restricted_cumulative_overlap`, the pocket-restricted
  CO primitive this task's measurement is built on.

## Open Questions

- ~~§6.2 (progress probability `p`) is named by the document itself as
  "the single cheapest decisive measurement in the proposal"~~ — built a
  collective-only partial version this pickup (see In Progress below).
  **Filed as [[Q-0004]] to Architect/Planner**: is the collective-only
  result (p=0.24–0.49, squarely "not rare") sufficient to retire the
  amplitude-amplification argument, or does the full joint
  (backbone⊗local⊗rotamer) version need real build effort (a rotamer
  packer, confirmed absent) before that call can be made? A scope/
  priority decision with direct submission-narrative implications, not
  one this thread should make unilaterally.
- §7's Cleveland Clinic constraint-3 question ("does 'no classical MD'
  exclude minimisation/Monte-Carlo sampling?") — unresolved location: no
  single confirmed owner/list for cross-team questions was found this
  pickup. Needs a human decision on where it's tracked, not a code fix.

## In Progress

**2026-08-21.** §2 PDB-retest, pocket-restricted half: real, decisive,
and — like [[TASK-0227]]'s whole-structure half — reverses rather than
merely corrects the synthetic-toy claim.

**Built**: `adaptive_anm_modes` (`allostery/superpose.py`) — an adaptive
subspace union (apo's own top-k modes, plus modes at structures stepped
±6 Å along each of apo's first 5 modes, Hessian rebuilt per step,
QR-orthonormalized), re-deriving the drop's own `adaptive_union`
construction on this module's validated `H13_3N_anm_hessian` rather than
the drop's independently-reimplemented one — drops straight into the
existing `restricted_cumulative_overlap` machinery with no adapter code,
confirmed by a dedicated compatibility test. New
`__WORK_IN_PROGRESS__/scripts/task0228_adaptive_subspace_pdb_retest.py`
reuses `compute_learnability`'s own real fetch/alignment/pocket-labeling
path (`learnability_gate.py`'s `run_one`) — no new alignment or fetch
code, only the static-vs-adaptive comparison itself.

**Result, all 3 mandatory targets, real RCSB structures, equal dimension
(110, apo's own top-10 modes × (1 + 2×5 stepped directions)), the real
labeled pocket's own apo→holo displacement**:

| target | N | n_pocket | static CO | adaptive CO | ratio |
|---|---|---|---|---|---|
| KRAS_G12C | 169 | 17 | 0.640 | 0.840 | 1.31× |
| BCR_ABL1 | 451 | 16 | 0.481 | 0.353 | **0.73×** |
| CARDIAC_MYOSIN (8QYP→8QYR, this project's own corrected pair) | 704 | 13 | 0.430 | 0.612 | 1.42× |

Sanity check against prior art: static CO(20) (not the 110-dim final
value) on KRAS_G12C measured 0.512 here vs. 0.458 previously recorded in
`compute_learnability`'s own docstring — same order, consistent direction
(current pipeline/label state has drifted slightly since that number was
captured, not a wiring defect; both clear the ~0.5 ballpark this document
and [[TASK-0227]] both treat as "collective part reachable").

**Verdict: mixed, real, target-dependent — not the drop's own reported
9.4× win, and not free.** Adaptive wins on 2/3 targets (1.31×, 1.42×) and
*loses* on the third (0.73× — worse than static at equal dimension).
Geometric-mean ratio ≈1.13×, an order of magnitude below the synthetic
ADK case. Consistent with [[TASK-0227]]'s own whole-structure finding
that both the original ~0.000 and the corrected ~9.4× numbers were
artifacts of the synthetic "adversarially local" deformation type
(flagged as a lower bound by the drop's own §3.1 caveat), not a property
of real apo→holo pocket displacements. **Static pocket-restricted CO on
real targets (0.43–0.64) is already close to the drop's own synthetic
*adaptive*-subspace number for its synthetic deformation (0.229)** — the
real starting point is far better than the synthetic toy suggested,
before any adaptive correction is even applied.

**What this settles, precisely**: together with [[TASK-0227]]'s
whole-structure result, both halves of the original §3/§5.1 concern are
now measured on real data. Whole-structure: reachable (k=50 overlap
0.51–0.67, TASK-0227). Pocket-restricted: also reasonably reachable by a
plain static basis (0.43–0.64 at dim=110), and the adaptive correction
that looked large and uniform on the synthetic toy is **small, real, and
not uniformly positive** on real targets. Building the full adaptive-
subspace move set §3's branching-factor argument assumes is not
disqualified by this result, but its expected benefit on real pocket-
opening is much smaller than the source document's own headline 9.4×
implied, and BCR_ABL1 shows it can actively hurt at equal dimension —
material context for anyone scoping §3-§9's remaining work.

---

**§6.2 — progress probability `p`, collective-only partial version
(added same pickup, after the RESULTS.md claim was found still held).**
The document's own text: "the single cheapest decisive measurement in
the proposal. Do it early." Built it, honestly scoped as partial.

New `__WORK_IN_PROGRESS__/scripts/task0228_progress_probability_p.py`
reuses `holo_direction.build_deformation_family` (TASK-0015, already
validated, steric-clash-gated) for the admissible **collective**
(single-mode ANM) move set at the apo starting node — no local relief
move, no rotamer repacking (§4.1's other two move types; the second
needs a global-optimum repacker, EvoEF2, confirmed absent by
[[TASK-0227]]'s own Done section). Objective = real pocket residues' mean
Cα displacement from their true holo positions (`cryptic_openness_gate`'s
own quantity — cross-checked byte-for-byte against a direct call,
confirmed matching). `p` = fraction of admissible moves that reduce it.

**Real methodological finding, not assumed**: `HOLO_DIRECTION_MODULE.md`'s
own frozen `PERTURBATION_PROTOCOL` (amplitude_scales 0.5/1.0/2.0, pre-
registered for TASK-0015's own *different* purpose — a small curated
family for shortcut-detection) rejects 53–59 of 60 candidates on these
real targets via its own integrity gate — n_admissible=1–7, statistically
unusable for a probability estimate. Checked 4 candidate amplitude grids
directly (not guessed) and used a separate, smaller grid (0.1/0.2/0.3 —
not a mutation of the frozen protocol, a different one for a different
measurement with different statistical requirements) to reach 47–59
admissible moves per target.

**Result, all 3 mandatory targets, real structures**:

| target | admissible moves | moves that reduce pocket-RMSD-to-holo | p |
|---|---|---|---|
| KRAS_G12C | 59 | 29 | 0.492 |
| BCR_ABL1 | 59 | 14 | 0.237 |
| CARDIAC_MYOSIN | 47 | 20 | 0.426 |

**All 3 land inside the document's own cited 0.24–0.69 "not rare" band**
— the same conclusion every other progress-probability-shaped
measurement in this project has reached (TASK-0181/0183's own citation;
TASK-0185's real ensemble-recovery rates 0.200–0.983). Per the document's
own decision rule ("if p stays in the 0.1–0.7 band... retire the arm"),
this is real, decisive evidence for retiring amplitude amplification —
**at the collective move layer specifically.**

**[[Q-0004]] retracted the same day, not answered by Architect/Planner**:
its entire cost framing rested on TASK-0227's own claim that EvoEF2/
fpocket were absent — corrected same-day (commit `fa94316`) as an
inadequate-search artifact, not a real environment gap. Both are real,
vendored, working binaries. With no real build cost left to weigh, the
full joint measurement was simply built next, on direct user instruction
("proceed with building the measurement... super thrilled about the
outcome" — recorded for the record, not part of this section's evidence).

---

**§6.2 — full joint (backbone + rotamer) `p`, same day.** New
`__WORK_IN_PROGRESS__/scripts/task0228_full_joint_p_measurement.py`.
Same admissible collective moves as the collective-only run above
(P_MEASUREMENT_PROTOCOL, 47–59/target), but now extended to real,
full-atom structures via `prody.extendVector` (an existing ProDy utility
— rigidly broadcasts each residue's own Cα displacement to every atom in
that residue; verified directly with a synthetic per-residue check
before use, not assumed correct) and, for the "+repack" condition, side-
chain-repacked at the pocket window with EvoEF2 `SideChainRepack`
(TASK-0204's own already-validated invocation, reused unchanged: relative
argv[0], `cwd=EVOEF2_DIR`, contiguous per-chain PDB blocks). Both
conditions scored on the **same** objective — fpocket's own
`druggability_score` at the window (TASK-0204's `score_structure`) — a
fair ablation; the collective-only run's RMSD-to-holo objective is
Cα-only by construction and blind to rotamer state, so it could not have
been reused here. "Progress" = druggability *increases* over the
unmodified apo baseline (druggability is higher-is-better; the
document's generic "reduces the objective" phrasing assumes a
minimization framing this objective doesn't literally fit).

Real subsample for tractability (EvoEF2+fpocket per candidate is
real wall-clock cost, ~2 s each, unlike the collective-only run's pure
linear algebra): 20 of the 47–59 admissible moves per target, uniform
random, seed 0.

| target | baseline druggability | p (backbone only) | p (backbone + repack) |
|---|---|---|---|
| KRAS_G12C | 0.001 | 0.25 | **1.00** |
| BCR_ABL1 | 0.566 | 0.20 | **0.05** |
| CARDIAC_MYOSIN | 0.001 | 0.50 | 0.65 |

**Real, decisive, and sharply target-dependent — the opposite of a
single verdict.** The direction of the repack effect tracks the apo
baseline's own druggability, not a fixed sign: on the two targets whose
apo pocket is essentially undetectable to begin with (KRAS_G12C,
CARDIAC_MYOSIN — baseline druggability ≈0.001, consistent with both
being genuinely cryptic in apo), adding rotamer moves makes progress
*more* likely, dramatically so for KRAS_G12C (0.25→1.00 — every sampled
repack found more cavity than an already-near-zero baseline, the
"nowhere to go but up" direction). On BCR_ABL1, whose apo baseline is
*already* druggable (0.566, above TASK-0204's own 0.5 druggability bar)
— independently consistent with this project's own repeated finding that
BCR_ABL1's pocket is an "apo-computable structural prior," pre-formed
even without any deformation ([[TASK-0104]]/[[TASK-0091]]) — EvoEF2's
purely energy-based repack (not druggability-aware) is *more* likely to
degrade an already-good pocket than improve it: p drops to **0.05**, the
one number in this whole session's worth of progress-probability
measurements meaningfully below the 0.24–0.69 "not rare" band (though
short of a literal order-of-magnitude drop — ~5–12× smaller, not
~10–1000×). Amplitude amplification is **not** cleanly retired at the
joint layer the way it was at the collective-only layer — it depends on
which kind of target (genuinely cryptic vs. already-open in apo) the
walk is being asked to search from, a real, physically grounded
finding this project's own prior "apo-computable prior" work already
anticipated but had not connected to a search-progress-probability
number before.

**Caveats, stated not buried**: n=20/target (not the full 47–59) —
tractable given real EvoEF2+fpocket cost, real subsample, but noisier
than the collective-only run's own n. The Cα→all-atom extension is a
rigid per-residue broadcast, a real approximation (no local backbone/
side-chain dihedral relaxation) — stated, not hidden. Single starting
node (apo), one repack attempt per candidate (not TASK-0204's own
8-seed SA average) — a point estimate, not a distribution.

---

**Not done, and why** (real, substantial remaining scope, not silently
dropped — see this task's own Intent Contract Out Of Scope): §3's
branching/depth measurement, §4's search infrastructure, §5's ceiling,
and all of §6 (including §6.2's "p", the document's own next-cheapest
step) are unbuilt. The RESULTS.md addendum to [[TASK-0227]]'s section
(cross-referencing this task's pocket-restricted number into the same
place readers already look) is written but not yet landed — that
section's `RESOURCE-*` claim (TASK-0195's mechanism) was held by a
different live session at write time; adding it once free is this task's
one remaining action, tracked in TODO above rather than forced through a
stale-content collision.

**Validated**: new `TestAdaptiveAnmModes` (5 tests: orthonormal basis,
dimension bound, determinism, reduces to the static basis at
`n_modes_stepped=0`, compatible with `restricted_cumulative_overlap`
including Bessel's inequality) — all pass.
`__WORK_IN_PROGRESS__/tests/test_superpose.py`: 75 passed. Full
`__WORK_IN_PROGRESS__` suite: 1202 passed, 1 skipped, 3 xfailed, no
regressions.

**Claim history**: claimed by 'Reviewer-thread (Opus)' at 2026-08-21
11:16, overridden on explicit user instruction ("pick up (and override
claim if needed) on 228") at 2026-08-21 (this session), same pattern and
same original claimant [[TASK-0227]]'s own Done section records for that
sibling task — the two overrides appear to be the same upstream
triage/filing session's claims, released deliberately to parallel
follow-up threads, not a genuine collision.

## Done

(not yet — see In Progress above; the single remaining action is the
RESULTS.md addendum, blocked on that file's held `RESOURCE-*` claim at
write time)
