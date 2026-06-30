# Operation Protocol

## Purpose

Define the human-readable meta-code layer that turns a request into verified implementation and reusable learning.

General intent is handled here.
It is a protocol and artifact boundary, not a standalone expert.

For non-trivial task files in this scaffold, the Intent Contract is mandatory.

## Core Principle

- BDD belongs to the intent layer.
- TDD and exact validation belong to the execution layer.
- Implementation should realize an approved intent, not invent it mid-flight.

## Core Artifacts

| Artifact | Purpose | Typical Owner |
|----------|---------|---------------|
| Intent Contract | human-readable outcome, scope, scenarios, constraints, critic questions | Architect/Planner |
| Intent Review | early critic pass over ambiguity, contradictions, and missing checks | General Critic |
| Discovery Note | evidence that sharpens or falsifies the current intent | Explorer |
| Execution Slice | bounded implementation and validation plan derived from intent | Implementer |
| Review Record | findings against the implementation and validation evidence | General Critic or Code Reviewer |
| Learning Capture | reusable lessons for agents and the human in the loop | Teacher |
| Promotion Decision | what becomes shared memory, role guidance, or stays local | Knowledge Curator |

## Cycle Steps

| Step | Layer | Primary Owner | Main Artifact | Exit Criteria |
|------|-------|---------------|---------------|---------------|
| 0 | Intake | HITL and Architect/Planner | request framing | objective, constraints, and risk posture are clear enough to draft intent |
| 1 | Intent Formulation | Architect/Planner | Intent Contract | desired outcome, scope, scenarios, constraints, and planned checks are explicit |
| 2 | Intent Critic Review | General Critic | Intent Review | major ambiguity, contradiction, and missing acceptance criteria are resolved |
| 3 | Discovery or Reality Check | Explorer | Discovery Note | unresolved facts are narrowed enough to keep the slice bounded |
| 4 | Execution Derivation | Implementer | Execution Slice | implementation surface, local checks, and stop conditions are explicit |
| 5 | Capability and Tool Selection | Toolsmith or specialist overlay | capability choice | provider, safety, environment contract, and outputs are explicit |
| 6 | Implementation | Implementer | code or doc change | the change realizes the current execution slice |
| 7 | Local Validation | Implementer | validation evidence | the cheapest focused falsifier has been run and interpreted |
| 8 | Critic Review | General Critic or Code Reviewer | Review Record | risk, regression, and missing-validation findings are surfaced |
| 9 | Verification Debugging Sub-loop | Implementer with Explorer or critic as needed | debug note and updated verification evidence | failing or ambiguous verification is reduced to a local repair, a one-hop control move, or an explicit escalation |
| 10 | Final Verification | Implementer plus critic and HITL when needed | final check | the implementation still matches the approved intent |
| 11 | Learning Loop | Teacher | Learning Capture | agents and HITL are asked what was learned and what should be reused |
| 12 | Knowledge Promotion | Knowledge Curator | Promotion Decision | durable lessons are placed in the right source of truth |

## BDD and TDD Split

### Intent Layer

- describe behavior in human terms
- use BDD-style scenarios
- state scope, non-goals, constraints, and acceptance conditions
- ask critic questions before implementation begins

### Execution Layer

- derive tests, probes, checks, and implementation steps from the intent
- use TDD where appropriate, but only after intent is explicit enough
- keep the first validation action narrow and falsifiable

## Loops

- If intent review fails, go back to Intent Formulation.
- If discovery falsifies the intent, go back to Intent Formulation or narrow the scope.
- If local validation fails but the slice is still correct, repair locally and rerun.
- If local validation shows the control point is elsewhere, step one hop and refresh the execution slice.
- If final verification fails or is ambiguous, enter the verification debugging sub-loop before widening scope or rewriting intent.
- If learning capture is weak or speculative, keep it local and do not promote it.

## Verification Debugging Sub-loop

Use this sub-loop inside verification when the implementation exists but the claim that it realizes the intent is still not trustworthy.

### Trigger

- final verification fails
- final verification passes inconsistently
- evidence conflicts across checks
- the implementation works locally but not against the intended acceptance scenario

### Required Output

- preserved failing evidence
- suspected control point or mismatch surface
- one cheapest discriminating debug probe
- decision: local repair, one-hop control move, or escalation back to intent or scope

### Exit Conditions

- a local defect is repaired and verification passes
- the true control point is identified and handed to the correct slice owner
- the original intent or acceptance criteria are shown to be incomplete and must be revised

## HITL Touchpoints

Keep the human in the loop at as few points as practical:

1. objective and constraints
2. approval for destructive actions or major scope expansion
3. final acceptance when the implementation claim matters

## Manual and Automated Orchestration

- Manual orchestration and agent workflows should use the same artifacts.
- Slash commands should bind to capabilities or protocol steps, not directly to raw scripts.
- Overlays such as Commit Packager should consume capability outputs rather than own tool invocations directly.