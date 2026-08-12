# TASK-0210 Is apo→holo coupled backbone+rotamer search actually hard? — the Phase-2 candidate, or the last closure

## Context

- ID: TASK-0210
- Title: measure the computational hardness of finding the holo conformation
  from the apo structure by trajectory-free coupled backbone+side-chain
  search, on known-answer instances, using the treewidth/frustration
  machinery [[TASK-0204]] built.
- Status: Done
- **Thread: Implementer A (science), after [[TASK-0208]].** Same thread as the
  gate — the gate's result determines whether this runs at all, and splitting
  them risks building on a gate nobody read.
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: Orchestrating user, 2026-08-06: *"ask ourselves what exactly would
  need to be done to transform any of the APO into the HOLO structures…
  if we can show that THAT is a prohibitively complicated computation…
  then we may have a candidate for phase 2."*
- Priority: **P1, hard-gated on [[TASK-0208]].** If the route is open it is
  the strongest Phase-2 candidate the program has. If it closes, it closes
  the last one.
- Dependency: [[TASK-0208]] (hard gate), [[TASK-0209]] (valid instances),
  [[TASK-0204]] (the treewidth/exact-solve machinery, built and validated).

## Why this matters

The register's routes are closed by measurement, one after another. The
closures share a shape: **the problem turned out not to be hard.** Single-
particle CTQW is an `eigh` call. Backbone ENM sampling recovers pockets in
1–8 draws ([[TASK-0185]]). Fixed-backbone rotamer packing solves exactly in
milliseconds ([[TASK-0204]], m=12: 0.001–0.159 s against a naive `1e14.1`).

Each closure has a boundary, and they all point the same way:

| Closed | Why it closed | Boundary |
|---|---|---|
| Fixed-backbone packing | treewidth 2–5, exact in ms | **graph is fixed** |
| Backbone-only ENM search | recovery not rare | side chains not modelled |
| Single-particle CTQW | `eigh` at N≤704 | single particle |

**The coupled problem sits exactly in the gap.** Move the backbone and the
interaction graph becomes a variable — bucket elimination's order is invalid
and [[TASK-0204]]'s tractability result provably does not transfer. Model
side chains and [[TASK-0185]]'s "not rare" result no longer covers it. Nobody
has measured this regime.

And unlike every previous route, it has a **known answer**: the holo
structure exists. That makes it a benchmark instance, not just a problem
statement.

## The formulation — and the trap it must avoid

**The objective must be apo-only computable. Holo is the answer key, never
an input.** "Minimize RMSD to holo" is not a search problem — it is
reconstruction, trivially solved by copying the answer, and any hardness
measured on it is meaningless. The objective is a physical one (packing
energy, cavity druggability); holo is used **only** to score whether the
search found it.

This is the same firewall discipline `protocol.frozen_context` already
enforces elsewhere in this register, and it must be enforced here too.

## Intent Contract

- Outcome: a hardness characterization of trajectory-free coupled
  backbone+rotamer search on known-answer apo→holo instances — treewidth or
  frustration where those apply, empirical scaling where they do not — with
  an explicit verdict: **open** (a Phase-2 candidate, with a stated
  formulation and falsification criteria) or **closed** (and why).
- Why required, not assumed: "protein conformational search is hard" is
  folklore at folding scale. At *pocket* scale, on *these* instances, with
  *this* objective, it is an open empirical question — and the register's
  history is that these problems keep turning out easy when measured.
- In Scope:
  - **Legality, stated up front**: §Constraint 3 forbids *"classical MD
    trajectories as inputs"*, **not** conformational sampling — established
    by [[TASK-0185]], whose closed-form ANM equipartition draws are the
    precedent, and the challenge's own reference [1] (Zheng 2023) is a
    conformational-sampling method. Discrete/continuous search over
    (φ, ψ, χ) with no integrator is legal. Say so explicitly; a reviewer
    will check.
  - Formulate coupled search as an optimization problem over a discrete
    backbone move set (from [[TASK-0208]]'s measured backbone change) ×
    rotamer assignments.
  - **Measure hardness the way [[TASK-0204]] did, not by assertion**: where
    the problem admits a fixed interaction graph per backbone state, reuse
    `task0204_packing_hardness.py`'s treewidth machinery directly. Where it
    does not, measure empirically: time-to-optimum vs. instance size, gap
    between heuristic and exact/best-known, and whether the frustration
    [[TASK-0208]] measured actually produces search difficulty.
  - **The decisive comparison**: does a *classical* solver find the holo
    basin? If simulated annealing or a basin-hopping heuristic reaches it
    reliably in minutes, the route closes on the same grounds as every
    predecessor. Run this before any formulation work.
  - If open: state the quantum formulation (encoding, variable count,
    connectivity), and pre-register falsification criteria in Phase B's own
    style.
- Out Of Scope:
  - **Any speedup claim.** NP-hardness licenses *trying* QAOA/annealing; it
    never licenses a proven advantage, and QAOA has no general performance
    guarantee on any NP-hard instance class. This is Phase B criterion #2,
    binding here verbatim.
  - Running quantum hardware or a QAOA simulation. This task decides whether
    that is worth proposing.
  - MD, in any form.
  - Folding-scale search. The scope is pocket-local coupled search on
    known-answer instances, and the boundary must be stated, not blurred.
- Constraints And Invariants:
  - Holo is the answer key. The objective never reads it. Enforce
    structurally, not by intention.
  - **Pre-register what "hard" means before measuring** — a wall-clock
    threshold, a scaling exponent, or a heuristic-vs-exact gap. Without it,
    "prohibitively complicated" is unfalsifiable, and the register has just
    spent two tasks recovering from an unfalsifiable bar ([[TASK-0204]] D1).
  - A negative result closes the last route and is reported in the same voice
    as every other closure here.
- Planned Validation:
  - Known-answer check: the holo conformation, evaluated under the objective,
    must score better than the apo. If the objective does not prefer the true
    answer, it is the wrong objective and nothing downstream means anything.
  - Reuse [[TASK-0204]]'s correctness gate pattern: any exact solver must
    agree with brute force on instances small enough to enumerate.
  - Report the classical-solver result **before** any quantum formulation is
    written, so the formulation cannot be motivated by a result it did not
    earn.

## Pre-Registered Design + Hard Threshold (written before any measurement — 2026-08-12, Implementer A)

**Gate check (TODO item 1) — does not auto-close.** [[TASK-0208]]'s
reconciled, operative verdict (2026-08-12) is **INCONCLUSIVE**, not
side-chain-dominant: `side_chain_explained` is 0.036-0.078 on 3/4 targets
(rotating side chains alone on the fixed apo backbone gets nowhere — the
backbone must move), while dihedral-space backbone share is 0.20-0.37 at
the pocket on all 4 (most torsional change is in χ). Its own reading: "the
backbone moves little but is load-bearing... neither the pure-backbone nor
the pure-side-chain regime — the description of a coupled one." That is
not a closure signal for this task. Proceeding.

**Legality.** Simulated annealing over (a) discrete backbone-mode
amplitude choices and (b) EvoEF2 `SideChainRepack`'s own rotamer
optimizer at each candidate backbone is stochastic coordinate/
combinatorial optimization with no integrator, no velocity propagation, no
trajectory — the same legality argument [[TASK-0185]] already established
for closed-form ANM equipartition draws, applied here to a search
procedure instead of a single draw. §Constraint 3 forbids MD trajectories
as inputs; this produces none and consumes none.

**Backbone move set — the leakage decision (Open Question 1, resolved).**
Apo-only ANM modes (`superpose.anm_modes(apo.coords, cutoff=10.0,
n_modes=20)`, [[TASK-0185]]'s own established apo-only precedent), *not*
[[TASK-0208]]'s measured real φ/ψ deltas (those are holo-derived — using
them as the move set would put the answer inside the search space
definition, exactly the leakage this task's own "trap" section forbids).
At each SA step: pick a random mode (or a random small combination of the
top-K), draw an amplitude from a temperature-scaled step size, and apply
the resulting per-residue Cα displacement as a **rigid translation of that
window residue's whole backbone (N, CA, C, O)** — a stated approximation
(true ANM motion is not a rigid per-residue translation; this is the
cheapest apo-only-computable proxy for "the mode moved this residue's
frame this far, this direction"), not full internal-coordinate
propagation. Restricted to the pocket window (the residues [[TASK-0204]]/
[[TASK-0208]] already isolate) — the rest of the structure is held fixed,
matching every prior task's own window-scoping convention.

**Side-chain layer.** At each candidate backbone state, EvoEF2
`SideChainRepack` (vendored, already validated in [[TASK-0204]]) restricted
to the window's design chain — reused verbatim, not reimplemented.

**Objective (apo-only, drives SA acceptance — never reads holo).** fpocket
`druggability_score` at the window, via `task0204_rotamer_repack_baseline
.py::score_structure` (already-vendored, already-tested machinery, reused
directly). No pocket detected overlapping the window → treated as `0.0`
(a stated floor, not silently dropped or treated as missing data).
Metropolis acceptance maximizing this score, geometric cooling schedule
([[TASK-0181]]'s own SA precedent for a comparable combinatorial space,
adapted).

**Known-answer / apo-only-preference validation (Planned Validation, run
*before* any SA — the firewall check).** Confirm
`druggability_score(true holo window) > druggability_score(native apo
window)` on the same window/target-set definition, per target, before
trusting the objective at all. [[TASK-0209]] already established this
holds for KRAS_G12C (apo 0.001 → holo 0.886); computed fresh for the
others below.

**Success / "reached the holo basin" criterion (holo used only to score
the search's *output*, never as a search input).** Report both, per this
task's own Open Question 2:
1. Window heavy-atom RMSD (search result → true holo, reusing
   [[TASK-0208]]'s own local-superposition machinery) reduced by **>=50%**
   relative to the native apo→holo window RMSD already measured in
   [[TASK-0208]]'s `results.json` (`rmsd_apo_to_holo`) for that target.
2. The search result clears fpocket's own established hit bar
   (`overlap_frac >= 0.5` AND `druggability_score >= 0.5`,
   [[TASK-0185]]'s own convention, `_is_hit` reused verbatim).

**Hard threshold (pre-registered before measuring).** Budget: **2 restarts
x 10 outer SA iterations per target** (each iteration = one backbone
perturbation + one `SideChainRepack` call + one fpocket score) —
**revised down from an initial 3x40 draft** after directly timing
`SideChainRepack` on a real target (KRAS_G12C, 4OBE, whole-structure load
even though only the window's design chain is optimized): **16.3 s/call**,
against fpocket's 0.5 s/call — 3x40 would cost roughly two hours across
4 targets. This correction is made *before* any SA run, per this
register's own convention (measure feasibility, then commit the number,
not the reverse). 20 calls/target is still a genuine, real search — not a
token gesture — sized to keep wall-clock to roughly 20-30 min for the full
target set.
- **CLOSED (not hard)**: >=1 of 2 restarts clears *either* success
  criterion, on a majority (>=3 of the targets evaluated).
- **OPEN (apparent hardness, not a proof)**: 0 of 2 restarts on *any*
  evaluated target clears either criterion within budget. Reported with an
  explicit caveat every time it is used: **SA failing at a modest budget is
  evidence of difficulty for this heuristic at this budget, not a
  complexity proof** — this task's own Out-Of-Scope bullet already forbids
  claiming a speedup or a hardness proof, and that discipline applies to
  the classical-negative-result side of the ledger too, not only the
  quantum side. Where the search fails, attempt the treewidth
  characterization [[TASK-0204]]'s own machinery supports on the
  side-chain sub-problem *at the best backbone state found* (showing that
  piece stays easy, consistent with [[TASK-0204]]) and report SA's own
  empirical scaling (success rate / iterations-to-hit vs. window size) as
  the actual hardness evidence for the coupled/outer piece — per this
  task's own "measure the way TASK-0204 did, not by assertion."

## In Progress

Implementing `scripts/task0210_coupled_search.py`. Known-answer objective
validation first, then the SA solver on KRAS_G12C.

## TODO

- [x] Read [[TASK-0208]]'s gate verdict. If side-chain-dominant → close here, cite, stop.
      **INCONCLUSIVE, not side-chain-dominant — proceeding, see Pre-Registered Design.**
- [x] Write the legality paragraph (§Constraint 3, TASK-0185 precedent, ref [1]).
- [x] Pre-register the "hard" threshold. **Before measuring.**
- [x] Formulate coupled search; verify the objective prefers the true holo answer.
      **Verified on 2/4 targets only — see Done, "known-answer/firewall check."**
- [x] Classical solver first: does SA/basin-hopping reach the holo basin?
- [x] Hardness measurement (treewidth where applicable, empirical scaling where not).
      **Empirical only — see Done. Treewidth-at-best-backbone not attempted (scoped out, disclosed).**
- [x] Verdict: open (formulation + falsification criteria) or closed (and why).
      **Tentatively OPEN, weakly supported — see Done for the full hedge.**
- [ ] If open: hand to [[TASK-0183]] as the Phase-2 PoC scope.
      **Not done — verdict too weak to hand off as-is; see Done's recommended next step.**

## Dependency

- [[TASK-0208]] — **hard gate**.
- [[TASK-0209]] — valid known-answer instances.
- [[TASK-0204]] — treewidth + exact-solve machinery, validated.
- [[TASK-0185]] — the legality precedent and the backbone-only result.
- Feeds [[TASK-0183]] (Phase-2 scope) and [[TASK-0184]].

## Open Questions

- What backbone move set? Options: [[TASK-0208]]'s measured real φ/ψ changes
  (realistic, but derived from holo — a leakage risk that must be firewalled
  or replaced by an apo-only move set), ANM-mode displacements ([[TASK-0185]]'s
  precedent, apo-only, but continuous), or a Ramachandran-binned discrete set.
  **Decide with the leakage question explicit** — the holo-derived option is
  the most realistic and the most dangerous.
- Is "reach the holo basin" the right success criterion, or "open a cavity
  fpocket scores druggable"? The first is stricter and has a known answer; the
  second is what the biology cares about. Report both.
- If hardness is real but only on 1 of 4 targets, is that a Phase-2 candidate?
  Probably yes — but say so explicitly rather than generalizing from one target,
  which is the error [[TASK-0201]]/[[TASK-0168]] are still untangling.

## Done

**2026-08-12, Implementer A.** `scripts/task0210_coupled_search.py` (new).
Ran the pre-registered classical solver (ANM-mode backbone perturbation +
EvoEF2 `SideChainRepack` + fpocket-druggability objective, 2 restarts x 10
iterations/target) on all 4 targets [[TASK-0208]] evaluated.
Results: `results_task0210_coupled_search/results.json`.

### Known-answer/firewall check — passes on 2/4 targets, not 4/4

| Target | apo druggability | holo druggability | objective prefers holo? |
|---|---|---|---|
| KRAS_G12C | 0.001 | 0.886 | **yes** |
| PTP1B | 0.046 | 0.757 | **yes** |
| CASPASE1 | 0.679 | 0.030 | **no — inverted** |
| GLUCOKINASE | 0.759 | 0.229 | **no — inverted** |

Per this task's own Planned Validation ("if the objective does not prefer
the true answer, it is the wrong objective and nothing downstream means
anything"), **CASPASE1 and GLUCOKINASE's SA results below are not
interpretable as evidence about search difficulty** — the search ran (see
table below for completeness) but any outcome, success or failure, would
be uninformative there. Only KRAS_G12C and PTP1B are treated as evaluable.

Plausible cause, CASPASE1 (documented, not new): `targets.yaml`'s own
warning on this target states apo (1ICE) is "not ligand-free: the
catalytic/orthosteric site is covalently occupied by an unrelated
active-site inhibitor (Ac-YVAD-CHO)" — a covalently-modified "apo" is not
a clean unliganded baseline, and could plausibly stabilize the dimer-
interface allosteric window into an artificially druggable-looking
geometry independent of the true holo state. GLUCOKINASE's inversion is
**unexplained** — its own pocket label already carries a pre-existing
lower-confidence flag (`resolution_shell_over_core: 0.0`,
`core==consensus` is degenerate unanimity of only 3 criteria, not strong
agreement), a plausible contributing factor, not a demonstrated one.
Flagged as an open question, not resolved here.

### Classical solver results

| Target | evaluable? | restart 1 best score / rmsd_reduction / hit | restart 2 | any success? |
|---|---|---|---|---|
| KRAS_G12C | yes | 0.349 / 9.6% / no | 0.466 / 7.9% / no | **no** |
| PTP1B | yes | 0.071 / 21.1% / no | 0.293 / 15.4% / no | **no** |
| CASPASE1 | **no (firewall failed)** | 0.592 / 17.6% / no | 0.592 / 18.5% / no | n/a |
| GLUCOKINASE | **no (firewall failed)** | 0.879 / -5.3% / no | 0.933 / -3.7% / no | n/a |

Success bar (either): window RMSD-to-holo reduced >=50% vs. native
apo->holo window RMSD, or fpocket overlap>=0.5 AND druggability>=0.5.
Neither evaluable target reached either bar on either restart. Best
scores found (KRAS_G12C 0.47, PTP1B 0.29) are well below the true holo
values (0.89, 0.76) — the search explored but did not converge toward the
known answer within budget.

**A methodology note discovered mid-run, disclosed rather than
silently absorbed**: the per-call cost calibration used to set the
2x10 budget (16.3 s/`SideChainRepack` call, measured on a stray file
left in `tools/evoef2/` from an earlier task) turned out **not
representative of this task's own candidate files** — real cost was
~1.6-10 s/call depending on target size, and the full 2x10x4-target run
completed in about 6 minutes, not the ~30 min the budget was sized for.
**The pre-registered budget was honored as committed regardless** — no
extension was run after seeing a negative result, to avoid outcome-
contingent budget inflation. The cheap true cost is reported here as a
finding for whoever runs the follow-up (below), not used to retroactively
inflate this run.

### Verdict: **Tentatively OPEN, weakly supported — not a Phase-2 handoff yet**

Applying the pre-registered threshold in good faith: the CLOSED condition
("majority, >=3 of 4 targets, clear the bar") assumed 4 evaluable
targets and cannot be literally applied with only 2 legitimately
evaluable. On those 2 (KRAS_G12C, PTP1B), 0 of 2 restarts reached the
known basin on either — which is exactly the pre-registered OPEN
condition ("0 of 2 restarts on any evaluated target"). That is reported
honestly as the applicable reading, **with every caveat this task's own
pre-registration required attached, not dropped now that the outcome is
known**:

- **SA failing at a modest budget is evidence of difficulty for this
  heuristic at this budget, not a complexity proof.** This task's own
  Out-Of-Scope bullet forbids a speedup/hardness *proof* claim, and that
  discipline binds the negative-result side of the ledger exactly as much
  as a positive one would have been bound.
- **The budget was under-sized relative to its own true cost** (the
  methodology note above) — a properly-tuned rerun (larger iteration
  count, possibly a wider mode set, better annealing schedule) is cheap
  and has not been tried. Zero evidence exists yet that a bigger budget
  wouldn't close this route the way every prior route in this register
  closed once actually measured properly.
- **n=2 legitimately-evaluable targets** is a thin base for "the last
  route in the program is open." [[TASK-0201]]/[[TASK-0168]] are still
  untangling exactly this generalize-from-one-or-two-targets error
  elsewhere in the register; the same caution applies here.
- **The move set is one specific, stated approximation** (ANM-mode
  Cα-displacement applied as a rigid per-residue backbone translation,
  not full internal-coordinate propagation) — a different, more
  physically faithful move set might search the right space more
  effectively and is not ruled out by this result.

**Not handed to [[TASK-0183]] as-is.** A tentative, small-n, under-tuned
negative result is not the same evidentiary weight as [[TASK-0204]]'s
millisecond-scale exact-solve closure or [[TASK-0185]]'s 1-8-draw
recovery-rate closure, and treating it as equivalent would repeat exactly
the unfalsifiable/overclaimed-criterion failure mode this register has
already had to walk back twice ([[TASK-0204]]'s D1, its criterion #1, and
[[TASK-0208]]'s own compound gate). The honest state: **this route remains
the only one not yet closed, but it has not been measured well enough
to call it open either.**

### Recommended next step (not run here — a real follow-up, not silently expanded scope)

1. A properly-budgeted rerun (the true ~2-10 s/call cost supports a much
   larger iteration count / restart count than 2x10) on KRAS_G12C and
   PTP1B specifically — the two firewall-valid targets.
2. Diagnose and fix (or explicitly exclude with cause) CASPASE1 and
   GLUCOKINASE's firewall failures before trusting any result on them.
3. If a larger budget still fails to reach the basin on both targets,
   *that* result would carry real weight and could support handing this
   to [[TASK-0183]].

### Legality (§Constraint 3, TASK-0185 precedent)

Restated for the record: SA over discrete backbone-mode-amplitude
proposals and EvoEF2's own rotamer SA is stochastic coordinate/
combinatorial optimization, no integrator, no trajectory — the same
argument [[TASK-0185]]'s closed-form ANM equipartition draws already
established, applied to a search procedure. No MD in any form was run.

### Not attempted

- Treewidth measurement at the best-found backbone state (this task's own
  fallback for "where the empirical search result is negative, also try
  the structural argument") — scoped out under this turn's effort budget,
  disclosed rather than silently skipped. A real gap for the follow-up.
- Any quantum formulation — correctly out of scope until a real OPEN
  verdict exists to formulate against.
- Diagnosing GLUCOKINASE's firewall inversion beyond noting its
  pre-existing lower pocket-label confidence.
