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
- Status: Done
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

**2026-07-24, Implementer D (this thread).**

**(1) GLUCOKINASE runnability confirmed, not re-litigated** — this
task's own Open Question asked whether [[TASK-0081]]'s chain-schema
flag (`Q-0001`) had been resolved by pickup time. It has: [[TASK-0127]]
added the `apo_chains`/`holo_chains` per-role override that fixes it,
and [[TASK-0150]]'s own session already ran GLUCOKINASE cleanly through
`compute_learnability` as direct evidence. Confirmed again here by a
full, clean 1000-replicate real run — no config guess needed.

**(2) `scripts/learnability_gate_patch_control.py` needed no CO-quantity
fix** — checked directly before assuming it did (this task's own
Constraints warned against reintroducing the bug [[TASK-0150]] fixed).
This script already used `restricted_cumulative_overlap` correctly
(the one call site TASK-0139's own claim about "both scripts already
fixed" was actually true for). Only change: added an ADD-only
`--target`/`--output` CLI option (default reproduces the original
3-mandatory-target behavior exactly) so CARDIAC_MYOSIN/GLUCOKINASE
could be run without recomputing KRAS_G12C/BCR_ABL1's own
already-published null. Same minimal CLI addition made to
`scripts/learnability_gate.py` for the same reason (GLUCOKINASE had
never been added to its own `DEFAULT_TARGETS`/output JSON at all).

**(3) Real 1000-replicate run** (`scripts/learnability_gate_patch_
control.py --target CARDIAC_MYOSIN GLUCOKINASE`, live fetch, seed=7,
same convention as TASK-0133's own KRAS_G12C run):

| Target | RMSD ratio | Restricted CO(20) | Percentile in null | One-sided p | Bare-threshold | Null-informed |
|---|---|---|---|---|---|---|
| CARDIAC_MYOSIN (8QYP) | 1.57 | 0.254 | 85.7th | 0.143 | `UNLEARNABLE_FROM_APO` | **`AMBIGUOUS`** |
| GLUCOKINASE | 1.94 | 0.304 | 89.9th | 0.101 | `UNLEARNABLE_FROM_APO` | **`AMBIGUOUS`** |

New `scripts/resolve_cardiac_glucokinase_learnability.py` (mirroring
`resolve_kras_learnability.py`'s own pattern, adapted: this comparison
is bare-threshold-vs-null-informed, not whole-structure-vs-restricted,
since both this task's inputs already use the correct restricted CO)
confirmed both programmatically, not by hand-transcription. A units
bug was caught and fixed *while writing this task*, not shipped:
`learnability_verdict`'s own `co_percentile` parameter expects a 0–1
fraction, not a 0–100 percentage — an initial hand-check passing
`85.7` directly (instead of `0.857`) silently produced the wrong
verdict (`LEARNABLE`, via a spurious `>= 0.95` true on any number above
0.95 on the wrong scale) before the resolution script's own explicit
`/100.0` division was written and re-verified against
`resolve_kras_learnability.py`'s own precedent.

**Headline: both targets soften from `UNLEARNABLE_FROM_APO` to
`AMBIGUOUS`**, the same direction and magnitude as KRAS_G12C's own
93rd-percentile/p≈0.07 result. This is now a recurring pattern on 3 of
the 4 targets this precise analysis has ever been run on (only
BCR_ABL1, RMSD-determined, never reaches the CO half at all) — not a
one-off. Per this task's own Constraints, this does not retract
[[TASK-0150]]'s own bare-threshold reading; it reports the more
rigorous of two legitimate readings alongside it, exactly the
relationship KRAS_G12C's own two numbers already have.

**Docs updated additively**: `RESULTS.md`'s Learnability gate section
(new 2026-07-24 block) and open-questions table (new row 34);
`COMPETENCE_MAP.md`'s CARDIAC_MYOSIN section; [[TASK-0150]]'s own Done
section (closing the gap it flagged, cross-linked both ways).

**Full test suite**: 915 passed, 2 xfailed, 0 failed (no library code
touched — two scripts gained an ADD-only CLI option each, default
behavior byte-identical).

**Not attempted, per this task's own Out Of Scope**: the null
methodology itself was not re-derived or modified; KRAS_G12C's own
already-closed [[TASK-0139]] verdict was not re-litigated; GLUCOKINASE's
chain-schema question was reconfirmed resolved, not independently
re-solved from scratch.
