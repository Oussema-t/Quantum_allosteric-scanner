# TASK-0163 Run external classical baselines (PocketMiner, ProteinLens, fpocket)

## Context

- ID: TASK-0163
- Title: `PANEL_REVIEW_2026-07-25.md` W7/V8 — the challenge explicitly
  scores "comparison to classical analogs." The project has run ~40
  quantum-flavored observables but only **one** external classical
  comparator (GNM transfer entropy, [[TASK-0132]]). `ALGORITHM_REGISTER.md`
  itself rates PocketMiner, ProteinLens, and fpocket at 4 and none was
  ever run. A referee will ask directly why a program with this much
  quantum-side testing volume has one classical baseline.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `PANEL_REVIEW_2026-07-25.md` §2.2/W7, §4 action item 6, V8.
- Priority: **P1** — the review's own estimate is 2 days, mostly waiting
  on external web servers/tools, not analysis time. Either outcome
  strengthens the submission (per the review: if they hit where this
  project misses, the operator is the bottleneck; if they also miss,
  that is independent corroboration of the project's own thesis that
  apo topology may not encode the answer).

## Intent Contract

- Outcome: run PocketMiner, ProteinLens, and `fpocket` (a local,
  installable classical pocket-detection tool — the closest of the
  three to a first attempt, per `ALGORITHM_REGISTER.md`'s own rating)
  against the 3 mandatory targets' apo structures; score each against
  the same holo-defined pocket labels and the same AUC/floor
  methodology already established, so the comparison is apples-to-apples
  with the project's own reported numbers.
- Why required: this is the one comparison the challenge explicitly
  scores and the project has not made at the scale its own testing
  volume would suggest.
- In Scope:
  - `fpocket`: install (document as a new external dependency, same
    disclosure convention as `ripser`/`optuna` — [[TASK-0108]]/
    [[TASK-0110]]'s own precedent), run on the 3 mandatory apo
    structures, score its predicted pockets against the holo labels
    using the project's own AUC/floor convention.
  - PocketMiner / ProteinLens: web-server or downloadable-model based
    (confirm actual access method before starting — if either requires
    an account/API key/institutional access not available, state that
    explicitly as a blocker for that tool specifically, do not silently
    skip without saying so).
  - Report each tool's AUC against the project's own floor and against
    the project's own best surviving observable, same target set.
- Out Of Scope:
  - Any new observable of this project's own — pure external-tool
    benchmarking.
  - Installing/running tools not named in `ALGORITHM_REGISTER.md`'s own
    rated list.
- Constraints And Invariants: score external tools against the exact
  same holo-defined pocket labels this project already uses — no
  bespoke evaluation favoring either side.
- Planned Validation: a comparison table (this project's own best
  observable vs. each external tool vs. the proximity floor), all 3
  mandatory targets, explicit report of which tools were actually
  reachable/runnable and which were blocked.

## TODO

- [ ] Confirm access method for PocketMiner and ProteinLens (web
      server / downloadable / blocked); state findings explicitly.
- [ ] Install `fpocket`; document as new external dependency.
- [ ] Run all reachable tools on the 3 mandatory apo structures.
- [ ] Score against holo pocket labels, project's own AUC/floor
      convention.
- [ ] `RESULTS.md`/`ALGORITHM_REGISTER.md` comparison table; update the
      register's own rating entries to reflect "run," not just "rated."

## Dependency

- [[TASK-0094]] (Done) — proximity floor, reused for comparison.
- `ALGORITHM_REGISTER.md` — the existing rating/candidate list this task
  acts on.

## Open Questions

- Whether PocketMiner/ProteinLens are actually reachable from this
  project's own working environment (web-server access, rate limits,
  account requirements) — resolve at the start of this task, report
  honestly if blocked rather than substituting a different tool
  silently.

## Done

(not yet)
