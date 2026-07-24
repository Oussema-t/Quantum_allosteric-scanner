# TASK-0152 CARDIAC_MYOSIN(8QYP)/GLUCOKINASE matched-null for the learnability bare-threshold verdict

## Context

- ID: TASK-0152
- Title: [[TASK-0150]] wired the corrected (pocket-restricted CO)
  learnability gate into `run_challenge.py` and `scripts/
  learnability_gate.py`, but explicitly flagged as **not attempted**: a
  fresh 1000-replicate random-patch null against CARDIAC_MYOSIN's new
  (8QYP) apo and GLUCOKINASE (which never had one) — the same rigorous
  check [[TASK-0133]]/[[TASK-0139]] already did for KRAS_G12C's own
  bare-threshold verdict.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: [[TASK-0150]]'s own Done section, "Not attempted, explicitly
  flagged as remaining scope" — filed here as its own task number since
  it is not currently blocking anything in flight but is a real,
  named gap, per this project's own "close all gaps" priority.
- Priority: **P2** — real gap, not urgent; both targets' bare-threshold
  verdicts already carry a reported verdict from the corrected gate,
  this only adds the matched-null rigor KRAS_G12C already has.

## Intent Contract

- Outcome: run the same matched random-patch null
  (`scripts/learnability_gate_patch_control.py`'s own pattern, per
  [[TASK-0133]]/[[TASK-0139]]'s precedent) against CARDIAC_MYOSIN's
  current (8QYP, post-[[TASK-0124]] re-anchor) apo structure and against
  GLUCOKINASE, using the now-correct pocket-restricted
  `restricted_cumulative_overlap` ([[TASK-0150]]'s `compute_learnability`
  helper) rather than the whole-structure quantity the pre-TASK-0150
  gate used.
- Why required: without this, CARDIAC_MYOSIN's and GLUCOKINASE's
  bare-threshold learnability verdicts rest on a single point estimate
  with no null-distribution context — exactly the gap KRAS_G12C had
  before TASK-0133/0139 closed it. Closing it here brings all targets
  with a resolved config to the same evidentiary standard before the
  6-pager cites any of their verdicts as final.
- In Scope:
  - CARDIAC_MYOSIN (8QYP apo) and GLUCOKINASE — 1000-replicate
    random-patch null, same percentile/p convention as
    [[TASK-0133]]/[[TASK-0139]].
  - Use [[TASK-0150]]'s `superpose.compute_learnability` (the corrected,
    pocket-restricted composition) — do not reintroduce the
    whole-structure CO bug that motivated TASK-0150 in the first place.
  - Note GLUCOKINASE's own open chain-schema question ([[TASK-0081]]'s
    Done section) — if it blocks a clean run here too, say so
    explicitly rather than forcing a config guess; that is a separate,
    already-raised issue, not this task's to resolve.
- Out Of Scope: re-deriving the null methodology, re-litigating
  KRAS_G12C's own already-closed verdict, resolving GLUCOKINASE's
  chain-schema question if it turns out to block this task too (flag
  and stop, don't guess).
- Constraints And Invariants: reuse the existing null script's pattern
  as-is; no new statistical method.
- Planned Validation: percentile + p per target, reported alongside the
  existing bare-threshold verdict in `RESULTS.md`/`COMPETENCE_MAP.md`,
  same table shape KRAS_G12C's own null result already uses.

## TODO

- [ ] Confirm GLUCOKINASE's config is actually runnable (check
      [[TASK-0081]]'s open chain-schema flag first — if still
      unresolved, run CARDIAC_MYOSIN alone and report GLUCOKINASE as
      blocked, don't guess the chain).
- [ ] Run the 1000-replicate random-patch null on CARDIAC_MYOSIN (8QYP)
      using `compute_learnability`'s corrected composition.
- [ ] Run the same on GLUCOKINASE if unblocked.
- [ ] Report percentile + p per target; update `RESULTS.md`/
      `COMPETENCE_MAP.md` additively; cross-link from TASK-0150's own
      Done section as the followed-up-on item.

## Dependency

- [[TASK-0150]] (Done) — the corrected `compute_learnability` composition
  this task must use, not the pre-fix whole-structure CO.
- [[TASK-0133]]/[[TASK-0139]] (Done) — the null methodology and
  reporting convention being extended here.
- [[TASK-0124]] (Done) — CARDIAC_MYOSIN's current apo anchor (8QYP).
- [[TASK-0081]] (Done, with one open item) — GLUCOKINASE's chain-schema
  question; check before assuming this target is runnable.

## Open Questions

- Whether GLUCOKINASE's chain-schema question ([[TASK-0081]]) has been
  resolved by the time this task is picked up — if not, this task's own
  scope for that target reduces to "confirmed still blocked," not a
  forced run.

## Done

(not yet)
