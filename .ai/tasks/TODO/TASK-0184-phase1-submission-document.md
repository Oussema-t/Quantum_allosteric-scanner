# TASK-0184 The Phase-1 submission — analysis freeze, narrative decision, and the six-page document

## Context

- ID: TASK-0184
- Title: freeze the analysis register, make the narrative decision explicitly,
  and write the Phase-1 ideation proposal plus the §5.3 methodological report.
- Status: TODO
- Owner: Bartosz (writing), Architect/Planner (section map, evidence pull)
- Claimed By: —
- Claimed At: —
- Source: challenge §5.3; Phase-1 assessment criteria; deadline 2026-09-15.
- **Revised 2026-07-29** (narrative framing (B) updated).
- Priority: **P0 — this is the submission. Everything else in the register is
  input to it.**

## Why this matters — the register has been treated as a results paper

Phase 1 is scored as **ideation**. The criteria ask what the team *would*
build, whether the framing is credible, and whether the plan is realistic.
The 226 scored cells, four retractions, and falsification apparatus are not
the deliverable — they are the evidence that this team's proposal is credible
and its competitors' are not. That distinction should shape every section.

**The schedule is the binding risk.** Deadline 2026-09-15; analysis freeze
2026-08-08; today is 2026-07-29. That is ~10 days of runway, and results are
still landing daily — [[TASK-0163]]'s fpocket result (a 2009 classical tool
beating every observable here on 2/3 targets) landed the same day as the
external review. **A register that never freezes produces no document.**

## The narrative decision — Bartosz's call, made once, in writing

Three coherent framings. They are mutually exclusive at the level of the
opening paragraph and cannot be blended:

**(A) "Rigorous negative + certifying-benchmark specification."**
Lead with what was falsified and the benchmark audit. Strongest on Validation
(15%) and Problem Relevance (25%); weakest on Technical Approach (25%) unless
paired with a concrete forward method.

**(B) "We were solving the wrong problem, and here is the right one."** ← *recommended, revised 2026-07-29*
Lead with the problem and the enterprise impact. Present the falsification
record as the *reason* for the proposed method rather than as the result.
The argument, which no competing team can make:

> A cryptic pocket is absent in the apo structure by definition. Static apo
> residue-scoring — the approach the challenge's §4.1 specifies, which we
> implemented in full — is therefore detecting a feature that is not in its
> input, and we measured it behaving exactly as that predicts: a proximity
> detector with no coherence dependence, beaten by a 2009 geometric tool on
> the two targets where the pocket is already open. We therefore reformulate
> cryptic-pocket prediction as **conformational search** — ENM ensembles,
> closed-form, no MD — and place the quantum contribution at the **side-chain
> rotamer packing** layer, which is discrete and NP-hard, rather than at the
> backbone layer, which we measured is not.

Strong on all four heavy criteria simultaneously: it is a problem insight
(criterion 1), a differentiated method with a measured justification
(criterion 2), it reuses machinery already built (criterion 3), and the
falsification record is the evidence (criterion 4). Requires [[TASK-0185]]'s
ensemble measurement, and is strengthened by [[TASK-0181]] Phase A.

**Sequencing risk to name honestly:** if [[TASK-0185]]'s prerequisite fails —
the known holo pocket never appears in an ENM ensemble — framing (B)'s first
half survives (the category-error diagnosis stands on [[TASK-0120]]/
[[TASK-0163]] alone) but its forward half weakens, and the proposal falls
back toward (A) with the response-coupling route as the method.

**(C) "Full quantum-advantage claim."** Not available. The register's own
evidence contradicts it and a reviewer checking the numbers would find that
out. Listed only so the decision is on the record as considered and rejected.

**Recommend (B).** It is the only framing where the falsification work becomes
an asset in the 25%-weighted Technical Approach criterion instead of a
liability, and it is honest. But it is a real choice with real trade-offs and
it belongs to Bartosz, not to an implementer or a reviewer.

## Section map to rubric weights

| Criterion | Wt | Section | Primary evidence |
|---|---|---|---|
| Problem Relevance & Impact | 25% | Problem + why current approaches fail | [[TASK-0169]] benchmark audit; [[TASK-0163]] fpocket; Eroom's-law framing from §3 |
| Technical Approach & Innovation | 25% | Method + what was ruled out and why | [[TASK-0185]] conformational search + the measured backbone-rarity negative; [[TASK-0181]] side-chain QUBO; [[TASK-0178]] response coupling; the anchoring theorem; the ruled-out ladder |
| Feasibility | 20% | PoC sprint plan | [[TASK-0183]]; [[TASK-0182]] resource table; measured runtimes |
| Validation Plan | 15% | Floors, nulls, LOD, positive control | [[TASK-0167]] LOD; [[TASK-0177]] consensus label; invariance protocol |
| Hybrid / Cross-Domain | 5% | Architecture diagram | classical ENM → quantum subroutine → classical verification |
| Team Capability | 10% | Roles | [[TASK-0183]]'s split |

Note the arithmetic: **Technical Approach and Problem Relevance together are
50%.** The falsification apparatus, which is this project's best work, sits
under Validation at 15%. Framing (B) is how that work gets counted twice —
once as validation rigor, once as the justification for the method choice.

## Intent Contract

- Outcome: the submitted Phase-1 proposal + §5.3 methodological report + the
  §5.1/§5.2 deliverables, all consistent with each other and with `RESULTS.md`.
- Why required, not assumed: no draft exists, the deadline is fixed, and the
  register is still moving.

- In Scope:
  - **Freeze the analysis register on 2026-08-07.** After that date, no new
    scored cell enters the proposal. Late results go to `RESULTS.md` for the
    record and, if material, to Phase 2.
  - The narrative decision, recorded in this file with reasoning.
  - Draft → adversarial panel review → revision. Reuse the existing
    `PANEL_REVIEW_*.md` convention on the *document*, not the code.
  - **Every number in the document traced to a `RESULTS.md` entry**, checked
    line by line. [[TASK-0169]] caught a stale floor (0.798, superseded by
    0.4818) inside its own filing. That will happen again in a 6-page
    compression; a numbers-audit pass is mandatory, not optional.
  - Reconcile the two branches' claims. `main` currently reports P@5 with no
    floor, on a `bartosz`-falsified operator; measured chance P@5 under its
    own `pocket_pk(tol=6.0)` metric is 0.26 on a KRAS-sized protein and a
    pure distance-to-seed predictor scores 0.66. **A judge who clicks the demo
    and then reads a paper arguing that number is an artifact will conclude
    the team does not read its own work.** Fix before submission.
  - §5.1 connectivity matrix, §5.2 hit list (site-level, [[TASK-0180]]), §5.3
    report — all emitted by one runner, all consistent.
  - The tonal constraint: Cleveland Clinic authored the premise partly being
    falsified. Frame as measurement of benchmark and method, never as
    correction of the sponsor. Lead the audit with the constructive half (the
    certifying-benchmark specification).

- Out Of Scope:
  - New experiments after the freeze.
  - Claiming quantum advantage.
  - Publishing anything not in `RESULTS.md`.

- Constraints And Invariants:
  - **Freeze date is hard.** The single largest risk to this submission is not
    a weak result; it is no document.
  - Page limit respected; overflow goes to appendix or is cut.
  - The document must not contradict `COMPETENCE_MAP.md`. If it does, one of
    them is wrong and that is resolved before submission, not papered over.
  - Negative results stated as findings, not apologised for.

- Planned Validation:
  - Numbers audit: every figure traced to its source entry.
  - Adversarial read against all six criteria, scoring the draft 1–5 on each
    as a reviewer would, and rewriting whatever scores ≤3.
  - Consistency check across proposal / `RESULTS.md` / `COMPETENCE_MAP.md` /
    `main` branch outputs.
  - **Cross-model check** (the established practice) on the *narrative*, not
    just the numbers — specifically probing whether the framing overstates.

## In Progress

None

## TODO

- [ ] **Bartosz: record the narrative decision (A/B/C) in this file.**
- [ ] Announce the 2026-08-07 freeze to the team.
- [ ] Section map → assign evidence owners.
- [ ] Draft §5.3 methodological report first (shortest, most constrained,
      and it forces the metric-justification argument into the open).
- [ ] Full draft by 2026-08-22.
- [ ] Numbers audit.
- [ ] Adversarial panel review of the draft; revise anything scoring ≤3.
- [ ] Reconcile `main` branch outputs.
- [ ] Submit before 2026-09-15.

## Dependency

- [[TASK-0183]] — Feasibility section.
- [[TASK-0182]] — resource table for §4.2/§Constraint 2.
- [[TASK-0180]] — §5.2 site-level hit list.
- [[TASK-0177]] — the label everything is scored against.
- [[TASK-0181]] — Technical Approach's forward method (framing B needs at
  least its classical result).
- [[TASK-0167.002]] — LOD, the strongest single Validation-section number.

## Open Questions

- If [[TASK-0181]]'s classical gate closes, or [[TASK-0185]]'s ensemble
  prerequisite fails, does framing (B) survive? **Partly** — see the
  sequencing-risk note above. "We tested the selection reformulation and it
  did not beat greedy" is itself a credible Technical Approach sentence, and
  the category-error diagnosis does not depend on either. But (B) weakens and
  (A) becomes safer. Decide when they resolve, not before.
- **Carry the honest negative on rare-event search into the document.** The
  1/√p amplitude-amplification argument is the first thing a quantum reviewer
  will reach for, and we measured that it fails at the backbone layer
  ([[TASK-0185]]). Stating that ourselves, with the numbers, is worth more
  than any claim we could make in its place.
- Does c-Myc get its own section? It is in the minimum set with a different
  evaluation basis (consensus + docking viability). Recommend a short
  dedicated subsection so it is visibly not forgotten.
- How much of the retraction history to include? **Recommend: a short
  paragraph, stated plainly, not hidden and not dwelt on.** Four documented
  self-retractions under a no-overwrite policy is unusual evidence of process
  quality, and a reviewer who spots it unmentioned will wonder what else is
  unmentioned.

## Done

(not yet)
