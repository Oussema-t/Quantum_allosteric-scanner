# TASK-0183 Phase-2 PoC sprint plan — what we would actually build in 3–4 months

## Context

- ID: TASK-0183
- Title: design the 3–4 month Phase-2 proof-of-concept the proposal commits
  to: scope, milestones, resource requirements, stated assumptions, and
  pre-registered success/failure criteria.
- Status: TODO
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

- [ ] **Bartosz decides the primary sprint track** (the scope decision above).
- [ ] Month-boundary milestones with falsifiable exit criteria.
- [ ] Resource requirements from measured runtimes + [[TASK-0182]]'s table.
- [ ] Risk register from actual failure modes.
- [ ] Team/role split.
- [ ] Explicit exclusion list.
- [ ] Self-audit + adversarial read.
- [ ] Hand to [[TASK-0184]] for the Feasibility section.

## Dependency

- [[TASK-0182]] — hardware resource numbers (soft; state as pending if late).
- [[TASK-0181]], [[TASK-0178]] — the proposed tracks. **The plan can be
  written before they land**; it proposes them rather than reporting them.
- [[TASK-0164]], [[TASK-0161]], [[TASK-0150]] (Done) — the honest constraints.

## Open Questions

- Is the primary track the QUBO route or the response/coupling route? They
  are complementary (QUBO's term (c) consumes `ddG`), but the proposal should
  name one as primary. **Revised recommendation: conformational search
  primary ([[TASK-0185]]), side-chain QUBO as its quantum component, response
  coupling as the observable feeding both.** This ordering is biologically
  motivated rather than complexity-motivated, which reads better under
  criterion 1 (25%) while keeping a credible quantum claim under criterion 2
  (25%). The earlier "QUBO on the static graph primary" recommendation is
  superseded — measurement showed the static-graph formulation is not where
  the hardness lives.
- Should the sprint commit to a specific accuracy target? Risky: the register
  says the benchmark may not be able to certify one ([[TASK-0169]]). Safer and
  more honest: commit to a **detection-limit** target (LOD, [[TASK-0167.002]])
  rather than an accuracy target. That is a metric this team can actually
  guarantee movement on.
- Does the plan address c-Myc? It is in the minimum submission set and is
  scored on consensus + docking viability rather than a held-out label — a
  different kind of deliverable. Give it a named milestone rather than
  folding it into the mandatory three.

## Done

(not yet)
