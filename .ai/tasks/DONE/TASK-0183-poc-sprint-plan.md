# TASK-0183 Phase-2 PoC sprint plan — what we would actually build in 3–4 months

## Context

- ID: TASK-0183
- Title: design the 3–4 month Phase-2 proof-of-concept the proposal commits
  to: scope, milestones, resource requirements, stated assumptions, and
  pre-registered success/failure criteria.
- Status: Done
- Owner: Architect/Planner (with Bartosz — this is a commitment, not an
  analysis)
- Claimed By: —
- Claimed At: —
- Source: Phase-1 assessment criteria, **Feasibility (20%)**: *"Can the
  proposed approach realistically be demonstrated within a 3–4 month PoC
  sprint? Are resource requirements (hardware, data, compute) realistic? Are
  assumptions and constraints clearly stated?"*
- **Revised 2026-07-29** (scope decision updated after the
  conformational-search reframing).
- Priority: **P0 for the submission — 20% of the score, and there is
  currently no artifact addressing it. Cheap (~1 day) and entirely
  writing/planning; no computation.**

## Holding assumption, stated explicitly ([[Q-0002]], 2026-08-16)

This task sizes itself against Feasibility = 20% of the Phase-1 score and
the "Phase 1 is scored as ideation" premise, both inherited from
[[TASK-0184]]'s own 25/25/20/15/5/10 weighting. **Neither appears in
`documentation/Cleveland-Clinic-Challenge-Statement-vF-1.md`** — the only
challenge document present in this repo; the two-phase document that
would actually contain them is not in the repository and is requested
from Bartosz in [[TASK-0221]]. Re-check cheaply once it arrives: if Phase
1 is scored as implementation rather than ideation, this task's own
"planning only, no computation" scope (see Out Of Scope, below) needs
revisiting, not just its numbers.

## Why this matters — this is the criterion the register is best-placed to win

Feasibility asks three questions, and this project can answer all three with
evidence rather than assertion — which most Phase-1 submissions cannot:

| Reviewer's question | What we can actually show |
|---|---|
| Realistically demonstrable in 3–4 months? | ~180 tasks executed in ~4 months, with dated task files and a runlog CPU-time convention |
| Resource requirements realistic? | Measured: 12.3 h brute-force integration ([[TASK-0130]]), 8 h transport sweeps, per-target runtimes recorded throughout; `LONG_JOB_CONVENTION.md` exists because jobs were lost and the lesson was written down |
| Assumptions and constraints clearly stated? | Four filed retractions, an invariance protocol, a competence map with explicit `NO_SIGNAL_IN_APO` verdicts, and a benchmark audit ([[TASK-0169]]) stating what the targets cannot certify |

**The distinctive asset is that the negative results make the plan credible.**
A team proposing CTQW-based allosteric scanning is proposing something this
project has already measured and ruled out. A plan that says *"we ruled these
five routes out by measurement, so the sprint targets these two"* is a
stronger feasibility claim than any optimistic roadmap, and it is only
available to a team that did the falsification work.

## Intent Contract

- Outcome: `documentation/POC_SPRINT_PLAN.md` — a 3–4 month plan with
  milestones, resources, risks, and pre-registered success criteria, written
  to be lifted directly into the proposal's Feasibility section.
- Why required, not assumed: 20% of the Phase-1 score with no current
  artifact; and committing to a sprint scope in writing forces the team to
  decide what it actually believes is worth building, which has not been
  decided.

## ⚠️ SCOPE UPDATE 2026-08-16 — the track below is superseded. Read before the section itself.

**The recommendation below (revised 2026-07-29: conformational search
primary, side-chain QUBO as its quantum component) rests on two premises
the register has since measured false, exactly as [[TASK-0184]]'s own
narrative-update note already found for the same reason (that note is the
direct precedent for this one — same two closures, same consequence,
applied here to the sprint plan rather than the narrative framing).**

| Premise below | What was measured since | Task |
|---|---|---|
| Side-chain rotamer QUBO is the quantum component, because packing is NP-hard | **NP-hard in general, trivial at pocket scale.** Treewidth 2-5; exact global optimum in 0.001-0.159 s vs. naive 1e14.1 | [[TASK-0204]] |
| Conformational search is the right reformulation to search over | **Coupled backbone+rotamer search is not hard either**, on the one target where the objective is valid and succeeds (13/65 restarts, KRAS_G12C) | [[TASK-0213]], [[TASK-0216]] leg B, [[TASK-0217]] |

**There is no open quantum-advantage route in the register** — nine
identified routes, all closed by measurement ([[TASK-0217]]'s own closing
synthesis). A sprint plan built around track (2) below would commit the
proposal to building a QUBO for a problem this same team's own register
already solved in milliseconds — precisely what this task's own
Constraint forbids ("Do not promise what the register has already shown
does not work... a reviewer who reads both would notice").

**Superseding scope, matching [[TASK-0184]]'s own already-decided (A′)
narrative** (not a new decision — (A′) was decided 2026-08-13, this is
its mechanical consequence for the sprint plan specifically): the Phase-2
PoC builds **the certifying instrument**, per [[TASK-0184]] §3(a)-(c) —
a scaled certifying benchmark, an apo-only screening criterion for the
hard/easy regime, and the apo-vs-stripped-holo delta against published
external-benchmark numbers. **Not a quantum algorithm sprint.** The
original track (1)-(4) below is kept for the record, not deleted, per
this register's own no-silent-overwrite convention.

## Original scope decision (2026-07-29) — superseded, see above

- In Scope:
  - **Scope decision (the hard part, and Bartosz's call):** the sprint cannot
    be "keep looking for signal." Recommended primary track, **revised
    2026-07-29** after the conformational-search reframing:
    1. **Cryptic-pocket prediction as conformational search**
       ([[TASK-0185]]) — ENM-ensemble generation (closed-form, no MD) with
       fpocket as the *oracle* rather than the competitor. This is the
       biologically motivated track and it reinterprets the whole register:
       a cryptic pocket is absent in apo, so static apo scoring was
       detecting a feature that is not in its input.
    2. **Side-chain rotamer QUBO** ([[TASK-0181]] Phase B) — the quantum
       component, placed where the problem is actually NP-hard. The
       backbone layer is not: measured, pocket opening under ENM soft modes
       is *not* rare (p = 0.24–0.69), and conjunctive druggability
       constraints still leave ~200–600 classical draws.
    3. **Response/coupling observables** ([[TASK-0178]]) — the mechanism
       never properly tested, with an exact closed form and a reciprocity
       gate; supplies the coupling term inside (1)/(2).
    4. **The certifying-benchmark specification** ([[TASK-0169]]/[[TASK-0177]])
       — delivered as a reusable artifact, not just a critique.

    Note the honest sequencing risk: track (1) has a **hard prerequisite**
    that [[TASK-0185]] tests before the freeze — does the known holo pocket
    appear in an ENM ensemble at all? If it does not, track (1) collapses
    and the sprint plan must fall back to (3)+(4). Write the plan so that
    fallback is explicit rather than discovered in month two.
  - Milestones at month boundaries, each with a **falsifiable** exit
    criterion. "Investigate X" is not a milestone; "X clears its floor at
    Bonferroni-corrected α on ≥2 targets, or is reported closed" is.
  - Resource requirements, grounded in measured numbers: compute (cite real
    runtimes), quantum hardware (from [[TASK-0182]]'s table and Braket free
    tier), data (RCSB + ASD — **and state the [[TASK-0164]] exhaustion
    finding honestly**: 0 of 6 remaining configs resolvable, so the sprint
    cannot promise a fresh held-out set from that pool).
  - Risk register with mitigations, drawn from what actually went wrong:
    session-teardown job loss, verdict-flipping knobs, null miscalibration,
    label instability, benchmark non-discriminability.
  - **Team composition and role split** — the Team criterion is a separate
    10%, but the sprint plan is where the split (physics validation /
    implementation) becomes concrete rather than asserted.
  - What we would *not* do, and why. An explicit exclusion list is the
    strongest available signal that the scope is real: no MD (constraint),
    no further observable proliferation ([[TASK-0161]]'s multiplicity budget),
    no deep-ML on ENM data ([[TASK-0150]]: PCA/AE subspace overlap with ANM
    soft modes is 0.9999–1.0000 — provably circular).

- Out Of Scope:
  - New experiments. This is planning only.
  - Promising results. Milestones are gates, not predictions.
  - Overstating hardware access.

- Constraints And Invariants:
  - Every runtime, cost, and capability claim traceable to a measured number
    in the register or a cited external spec. **No invented estimates** — the
    reviewer's question is precisely whether the estimates are real.
  - The plan must survive the project's own standards: pre-registered
    criteria, matched nulls, floors, no label leakage.
  - **Do not promise what the register has already shown does not work.** A
    plan proposing more CTQW variants would contradict this team's own
    published evidence, and a reviewer who reads both would notice.

- Planned Validation:
  - Self-audit: does each milestone have a criterion that could *fail*? Any
    milestone that cannot fail is rewritten.
  - Cross-check every resource number against `runlog` entries or the cited
    device spec.
  - Adversarial read: hand the plan to the panel framing
    (`PANEL_REVIEW_*.md` convention) and ask specifically whether a reviewer
    would call it optimistic.

## In Progress

None

## TODO

- [x] **Bartosz decides the primary sprint track** (the scope decision above).
      **Not re-decided — already decided.** The (A′) narrative Bartosz
      signed off on 2026-08-13 already commits to the certifying-instrument
      track ([[TASK-0184]] §3); this task's own superseded track was a stale
      relic of the pre-(A′) draft. See the SCOPE UPDATE section above.
- [x] Month-boundary milestones with falsifiable exit criteria.
- [x] Resource requirements from measured runtimes + [[TASK-0182]]'s table.
- [x] Risk register from actual failure modes.
- [x] Team/role split.
- [x] Explicit exclusion list.
- [x] Self-audit + adversarial read.
      **Self-audit done inline** (the document's own "Self-audit" section).
      **Adversarial read scoped to a self-check, not a separate
      `PANEL_REVIEW_*.md` dispatch** — consistent with this task's own
      "~1 day, planning only" sizing; a full external panel pass belongs to
      [[TASK-0184]]'s own already-planned adversarial review of the whole
      submission, not duplicated here.
- [x] Hand to [[TASK-0184]] for the Feasibility section.

## Dependency

- [[TASK-0182]] — hardware resource numbers (soft; state as pending if late).
- [[TASK-0181]], [[TASK-0178]] — the proposed tracks. **The plan can be
  written before they land**; it proposes them rather than reporting them.
- [[TASK-0164]], [[TASK-0161]], [[TASK-0150]] (Done) — the honest constraints.

## Open Questions

- Is the primary track the QUBO route or the response/coupling route? [...]
  **Moot, 2026-08-16 — superseded by the SCOPE UPDATE above.** Both the QUBO
  route and the conformational-search route it would sit inside are now
  closed by measurement ([[TASK-0204]], [[TASK-0213]]); there is no
  QUBO-vs-response-coupling primary-track question left to answer, because
  neither is the sprint's own primary track anymore.
- Should the sprint commit to a specific accuracy target? **Resolved as
  recommended** — the sprint plan commits to a detection-limit (LOD) target
  ([[TASK-0167.002]]), not an accuracy target, exactly per this note's own
  reasoning.
- Does the plan address c-Myc? **Resolved as recommended** — given its own
  named sub-deliverable in Month 1, not folded into the mandatory three.

## Done

**2026-08-16/17, Implementer A.**

Found, on picking this task up, that its own "Scope decision" section
(revised 2026-07-29) recommended a primary track — conformational search
with side-chain QUBO as its quantum component — that the register has
since closed by measurement on both counts ([[TASK-0204]]'s complexity
closure, [[TASK-0213]]'s coupled-search closure, [[TASK-0217]]'s own
confirmation that no quantum-advantage route remains open at all).
Proceeding on the literal, stale text would have written a Feasibility
section proposing to build a QUBO for a problem this same register
already solved in milliseconds — the exact failure this task's own
Constraint names ("do not promise what the register has already shown
does not work... a reviewer who reads both would notice"). Corrected via
a dated, superseding SCOPE UPDATE section (kept, not deleted, per this
register's own no-silent-overwrite convention) rather than a silent
rewrite, mirroring the same correction [[TASK-0184]]'s own narrative
update already made for the same underlying reason.

**Not a new decision.** The (A′) narrative framing [[TASK-0184]] already
decided (2026-08-13, Bartosz) already commits to the certifying-instrument
Phase-2 work (§3a-c); this task's own re-scoping is the mechanical
consequence of that decision for the sprint plan specifically, not a
fresh scope call.

**Delivered**: `documentation/POC_SPRINT_PLAN.md` — month-1-through-4
milestones (scale the certifying benchmark; the apo-vs-stripped-holo
delta; the apo-only screening criterion; packaging + adversarial review),
each with a stated, falsifiable exit criterion (none is an "investigate
X" milestone); resource requirements (compute, quantum hardware, data),
every number traced to a specific task, not invented; a risk register
built from 6 real, already-observed failure modes (including this
session's own construct-validity sweep, added as a new, current entry);
a team/role split drawn from the register's own already-proven
Architect/Planner-Implementer-Reviewer split, not aspirational; an
explicit exclusion list (no MD, no observable proliferation, no deep-ML
on ENM data, no quantum hardware execution promised, no accuracy-target
commitment — LOD instead, no unvalidated-target promotion); and a
self-audit confirming every milestone has a real failure mode.

**[[Q-0002]] folded in** (Reviewer thread, 4 facts found after this task
was claimed): rubric weights stated as a holding assumption (both here
and in the plan document's own header, cheap to re-check once
[[TASK-0221]] obtains the real two-phase document); the plan's own
anchor was already correctly the instrument, not the now-dead PTP1B
positive (confirmed, not changed); Braket/Classiq named concretely as
the sprint's target platforms, not left as a vague open item; the one
per-target figure quoted (CARDIAC_MYOSIN's 704-qubit full-resolution
number) annotated with which structure pair it came from, pending
[[TASK-0222]]'s own report on the Table-1-mandated pair.

**Not attempted**: verifying the two-phase document's own actual rubric
weights ([[TASK-0221]]'s own item); obtaining Braket/Classiq account
access ([[TASK-0221]]'s own item); running any part of the plan itself —
this task is planning only, per its own Out-Of-Scope.
