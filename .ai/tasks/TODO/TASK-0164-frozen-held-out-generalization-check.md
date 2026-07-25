# TASK-0164 Frozen held-out set — resolve 3 unused ASD configs, run once, never again

## Context

- ID: TASK-0164
- Title: `PANEL_REVIEW_2026-07-25.md` W5/V3 — [[TASK-0115]] correctly
  identified repeated-exposure risk and [[TASK-0081]]/[[TASK-0127]]
  mitigated it by extending the generalization set. But PTP1B/CASPASE7
  have now been scored **twice** ([[TASK-0127]], [[TASK-0151]]), and
  PTP1B is now cited as *confirmatory evidence* for `dcc_low`. A held-out
  set that has informed a hypothesis's own framing is no longer held
  out. There are 7 unresolved ASD configs in `config/targets.yaml`
  ([[TASK-0127]]'s own Done section names the ones it did not resolve
  and why) — the review's recommendation: freeze 3 of them now and do
  not look at them again until the final pre-submission check.
- Status: TODO
- Owner: Architect/Planner (the freeze decision + config resolution),
  handoff to Implementer for the single frozen run.
- Claimed By: —
- Claimed At: —
- Source: `PANEL_REVIEW_2026-07-25.md` §2.2/W5, §4 action item, V3.
- Priority: **P1** — the review's own estimate is 1 day; must happen
  *before* any further generalization-set analysis consumes more of the
  already-thin held-out margin.

## Intent Contract

- Outcome: resolve real, runnable configs for 3 of the 7 currently-
  unresolved ASD targets (re-check [[TASK-0127]]'s own Done section for
  exactly which 7 and why each was previously left unresolved — some
  fail for structural reasons that won't change, e.g. missing
  biological-assembly chains; pick 3 where the blocker is a genuinely
  resolvable schema/chain issue, not a missing-ligand or
  already-occupied-apo issue that would make the target unusable
  regardless). **Freeze them**: resolve the config, verify it loads
  cleanly, then do not run any scoring against these 3 targets' labels
  until every other analysis task in flight (including [[TASK-0158]]'s
  null fix) has landed — a single, final, pre-submission run.
- Why required: this is the only mechanism left in the program that can
  produce a genuinely never-seen confirmatory (or disconfirmatory) data
  point before the write-up locks in a claim.
- In Scope:
  - Re-read [[TASK-0127]]'s own Done section; pick 3 of its 7 named
    unresolved targets with a genuinely resolvable blocker.
  - Resolve chain/ligand config fields (same schema-fix pattern
    [[TASK-0127]] already used for GLUCOKINASE's `apo_chains`/
    `holo_chains`).
  - Verify the config loads and produces a non-empty pocket label — do
    **not** score against it yet.
  - Document the freeze explicitly (a dated note in `EXECUTION_PLAN.md`
    or `INVARIANCE_PROTOCOL.md`, cross-linked from [[TASK-0115]]'s own
    Rule #6) naming the 3 targets and stating they are not to be touched
    until the final pre-submission check.
- Out Of Scope:
  - Actually scoring the 3 frozen targets — that is a separate, later
    task, deliberately not filed yet (filing it now would itself be a
    form of repeated exposure to the plan).
  - The other 4 of the 7 unresolved targets, if their blocker is
    structural/permanent (state which and why, don't force a resolution
    where [[TASK-0127]] already found a real substantive reason not to).
- Constraints And Invariants: once frozen, **no scoring, no peeking at
  labels, no informal checks** — the whole value of this task is that
  these 3 targets stay genuinely unseen.
- Planned Validation: 3 configs resolved and confirmed loadable
  (structure fetch + label build succeeds, non-empty pocket), zero
  scoring runs against them, a dated freeze note in the shared docs.

## TODO

- [ ] Re-read [[TASK-0127]]'s own 7-target unresolved list; select 3
      with a genuinely resolvable (not structural) blocker.
- [ ] Resolve chain/ligand config fields per target.
- [ ] Verify config loads cleanly (fetch + label build only — no
      scoring).
- [ ] Dated freeze note in `EXECUTION_PLAN.md`, cross-linked from
      [[TASK-0115]]'s Rule #6, naming the 3 targets explicitly.

## Dependency

- [[TASK-0081]]/[[TASK-0127]] (Done) — the generalization set and its
  own list of unresolved targets, source of the 3 to pick from.
- [[TASK-0115]] (Done) — the repeated-exposure rule this task is a
  direct application of.

## Open Questions

- Which 3 of the 7 — resolve at pickup time by re-reading
  [[TASK-0127]]'s own Done section; do not guess from this task's own
  summary.

## Done

(not yet)
