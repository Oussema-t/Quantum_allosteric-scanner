# Apply batch 2026-07-20 (new-observable falsification battery)

Generated to repo standards (matches TASK-0123/TASK-0059 task format,
physics.md HYP-P format, EXECUTION_PLAN phase-table format). Everything is
pre-registered so agents pick up the verification tasks unbiased: each task
declares PASS/FAIL/INSUFFICIENT criteria BEFORE running, requires a matched-
decoy null, forbids tuning any knob against pocket labels, and frames a clean
negative as a complete result.

## Where each file goes

1. `.ai/tasks/TODO/TASK-0139..0142-*.md`
   -> copy into `<repo>/.ai/tasks/TODO/` verbatim.

2. `.claude/hypotheses/physics-APPEND-HYP-P9-P12.md`
   -> append its body (everything after the HTML comments) to the end of
      `<repo>/.claude/hypotheses/physics.md`. Do not renumber HYP-P1..P8.

3. `EXECUTION_PLAN-INSERT-Phase-1D-2026-07-20.md`
   -> three insertion blocks (A/B/C), each marked with where it goes in
      `<repo>/__WORK_IN_PROGRESS__/EXECUTION_PLAN.md`. Do not renumber IDs.

## Reference implementations (port, don't cross-import)

- `chiral_observable.py`  -> port to `src/allostery/chiral.py`  (TASK-0140)
- `closure_test.py`       -> port to `src/allostery/closure.py` (TASK-0139)
- `enaqt_sanity.py`       -> physics-check reference for TASK-0141
- `run_new_observables_on_benchmark.py` -> harness skeleton (TASK-0139/0140)
(all delivered in the prior turn's outputs)

## Not generated (offer)

- `REVIEW-panel-2026-07-20.md` — the source review these tasks cite. The
  task/hypothesis/plan files reference it; generate it too if you want the
  citation chain closed the way the other batches have it.

## Task dependency graph

TASK-0139 (P0, classical, gating) --gates--> TASK-0140 (P1) --gates--> TASK-0142 (P2)
TASK-0141 (P1, independent, expected-negative, noise-resilience objective)
