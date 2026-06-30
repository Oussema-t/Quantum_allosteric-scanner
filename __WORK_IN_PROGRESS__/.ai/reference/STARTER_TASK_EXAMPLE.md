# Starter Task Example

## Purpose

Show one full example of how a non-trivial task should move from intent through execution, review, verification, learning, and promotion.

This is a reusable example for scaffold adopters, not an active task.

## Example Task

```md
# TASK-0100 shared-auth-helper-refactor

## Context

- ID: TASK-0100
- Title: Consolidate duplicated auth setup into a shared helper
- Status: In Progress
- Owner: Implementer
- Scope: Refactor repeated setup logic without changing intended behavior

## Intent Contract

- Outcome:
  - duplicated auth setup paths are replaced by one shared helper with no behavior regression
- In Scope:
  - the repeated auth setup code
  - the shared helper and its call sites
  - focused verification for the changed slices
- Out Of Scope:
  - unrelated cleanup
  - auth feature redesign
- Acceptance Scenarios:
  - Given a flow that currently performs repeated auth setup, when the helper is applied, then the behavior remains unchanged.
  - Given a new flow that needs the same setup, when it uses the helper, then it does not reintroduce copy-paste logic.
- Constraints And Invariants:
  - keep public behavior unchanged
  - preserve existing environment contracts
- Planned Validation:
  - cheapest focused falsifier: targeted test or narrow runtime check over one migrated flow
  - follow-up checks: affected test file or narrow type, lint, or compile checks

## In Progress

- controlling duplication sites identified
- first helper extraction path selected

## TODO

### Intent Review
- confirm that the task is a refactor, not a behavior change
- check whether any duplicated branches are actually intentional divergence

### Execution Slice
- extract one shared helper
- migrate the smallest safe set of call sites
- keep the first edit reversible and local

### Review Record
- ask critic to confirm that duplication was removed without hiding meaningful differences
- check for missing validation or new abstraction leakage

### Verification Debugging Sub-loop
- if verification fails, preserve failing evidence
- determine whether the defect is in helper design, call-site assumptions, or stale tests
- repair locally or step one hop to the true control point

### Learning Capture
- ask what the refactor taught about when duplication should be consolidated versus preserved
- record any reusable heuristic for future DRY reviews

## Dependency

- shared helper location must remain visible to future flows
- validation environment must match the current auth contract

## Open Questions

- are all duplicated auth branches truly equivalent?
- should the helper remain local or become a wider shared abstraction?

## Done

- note the final helper location
- note the validation that passed
- note any learning promoted into shared guidance
```

## What This Example Demonstrates

- mandatory Intent Contract before implementation detail
- explicit split between intent, execution, review, debugging, and learning
- bounded refactor work instead of a broad cleanup blob
- full path from goal to reusable lesson