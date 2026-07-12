# TASK-0081 Generalization set (ASD targets)

## Context

- ID: TASK-0081
- Title: Run the frozen pipeline on 2–4 extra targets pulled from the
  Allosteric Database (ASD) with known sites, to evidence robustness and
  scalability beyond the required minimum set.
- Status: TODO
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 5, item 5.8 —
  "The brief **highly encourages** extra targets to demonstrate
  robustness/scalability. Pull 2–4 from the Allosteric Database with
  known sites. Cheap once 5.1 [TASK-0079] is a one-command run; directly
  feeds 'Technical Approach / Innovation'."

## Intent Contract

- Outcome: 2–4 additional targets from ASD (with known allosteric sites,
  i.e. real ground truth available, unlike TASK-0080's c-Myc case) added
  to `config/targets.yaml` and run through TASK-0079's end-to-end
  pipeline, producing the same three deliverables as the mandatory
  targets.
- In Scope: selecting the 2–4 targets (criteria: known allosteric site,
  reasonable size/complexity for the pipeline's current scope, ideally
  some diversity from the mandatory set's fold/mechanism types),
  `targets.yaml` entries, and the run itself.
- Out Of Scope: this task doesn't build new pipeline capability — it's
  purely additional coverage using what TASK-0079 already produces.
- Acceptance Scenarios:
  - Given 2–4 selected ASD targets, when run through the end-to-end
    pipeline, then each produces the same three deliverables (connectivity
    matrix, top-5 hits, methodological report) as the mandatory targets.
  - Given the results, then they're written up as evidence for the
    "Technical Approach / Innovation" rubric section the plan references.
- Constraints And Invariants: depends on TASK-0079 being a working
  one-command run first — "cheap once 5.1 is a one-command run" per the
  plan; don't start target selection work before that exists.
- Planned Validation: successful end-to-end run for each selected target,
  same acceptance bar as the mandatory-target runs.

## Dependency

- Depends on TASK-0079 (end-to-end challenge run) being Done.
- Feeds the submission's "Technical Approach / Innovation" writeup
  (whatever task or document assembles the final submission — not yet
  filed; flag if one doesn't exist by the time this lands).

## Open Questions

- Which 2–4 specific ASD targets? Not yet selected — this task should
  make and record that selection with its rationale (site-diversity,
  fold-diversity, or whatever criteria are used).

## Done

(not yet)
