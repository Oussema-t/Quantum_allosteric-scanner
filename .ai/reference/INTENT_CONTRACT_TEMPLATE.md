# Intent Contract Template

Use this for non-trivial work before exact implementation or exact test detail.
In this scaffold, non-trivial task files should include an Intent Contract section.

Small tasks may embed this as the first section of the owning task file.

## Metadata

- Status:
- Owner:
- Linked Task:
- Requested By:

## Outcome

- What should be true when this work is complete?

## In Scope

-

## Out Of Scope

-

## Acceptance Scenarios

Use BDD-style scenarios.

### Scenario 1

- Given:
- When:
- Then:

### Scenario 2

- Given:
- When:
- Then:

## Constraints And Invariants

-

## Discovery Needs

- What facts still need confirming before implementation is safe or well-bounded?

## Planned Validation

- What is the cheapest focused check that could falsify the intended approach?
- What narrower tests, lint checks, type checks, or manual checks should follow?
- If final verification fails, what is the first discriminating debug probe?
- If this Intent Contract states a pre-registered pass/fail criterion, gate,
  or bar: (1) state the positive control's expected result alongside the
  pass bar — what should a known-true instance score, and has that been
  checked; (2) demonstrate each of the criterion's own possible outcomes is
  actually reachable given the statistic's attainable range and the
  measurement's resolution (e.g. a permutation p-value can never be smaller
  than `1/n_reps` — `allostery.diagnostics.assert_gate_reachable` checks
  this one case mechanically; other constructions need the same reasoning
  stated inline). [[TASK-0217.002]]: four confirmed instances where a
  pre-registered criterion could not return one of its own outcomes, or had
  no control establishing detection was possible at all, each landing as a
  published verdict before anyone noticed.

## Critic Questions

- What could make this intent incomplete, contradictory, or misleading?
- What regression or ownership boundary is easiest to miss?

## Execution Handoff

- Expected implementation surface:
- Expected critic surface:
- Expected learning capture trigger: