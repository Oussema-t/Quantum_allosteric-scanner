# TASK-0050 Adopt the Seam Protocol into the scaffold

## Context

- ID: TASK-0050
- Title: Incorporate `SEAM_PROTOCOL.md` (relocated from `__WORK_IN_PROGRESS__/`
  to `.ai/reference/`) as a real, running practice — a `.ai/seams/` registry,
  the two definition-of-done/green-bar gate additions it specifies, and a
  cross-link from `OPERATION_PROTOCOL.md`
- Status: Done
- Owner: Architect/Planner
- Claimed By: Architect/Planner (this thread)
- Claimed At: 2026-07-11 11:59
- Source: user request, 2026-07-11 session — asked to read
  `SUGGESTION.md`/`SEAM_PROTOCOL.md`/`INVARIANCE_PROTOCOL.md`/
  `test_leakage_gate.py` (which had sat untracked in `__WORK_IN_PROGRESS__/`
  since before this session started) and derive tasks to incorporate them
  properly. This task covers the Seam Protocol half; [[TASK-0051]] covers
  Invariance, [[TASK-0052]] covers the leakage-gate file itself,
  [[TASK-0053]] is the first seam sweep this protocol calls for.
- Crit Ref: the doc's own worked example is not hypothetical — it names a
  gap that independently also surfaced in
  [[TASK-0047]] (Reviewer A's Foundation Review, 2026-07-07, P2 finding on
  `labels.py`) and is seed-listed as `OPEN` in the doc's own seam table
  ("pocket ↔ functional/terminal | assembled pocket excludes both").
  Two independent review passes finding the same real gap is corroborating
  evidence this protocol is worth adopting, not just plausible-sounding.

## Intent Contract

- Outcome: the Seam Protocol is a running practice, not a document nobody
  applies — a seam registry exists with the doc's own 5 seed records, the
  two gates are stated as scaffold rules (not just described in the source
  doc), and a dedicated task exists to actually run the first sweep.
- In Scope:
  - relocate `SEAM_PROTOCOL.md` to `.ai/reference/SEAM_PROTOCOL.md`
    (matches the existing `OPERATION_PROTOCOL.md` naming/location
    convention) — **done, this commit**, ahead of the rest of this task's
    TODO, since it's a pure mechanical move with zero content risk.
  - create `.ai/seams/README.md` (mirrors `.ai/tasks/README.md`'s shape:
    what a seam file/record is, required fields, status vocabulary)
  - create `.ai/seams/SEAM-0001` through `SEAM-0005`, seeded verbatim from
    `SEAM_PROTOCOL.md`'s own table (2 VERIFIED, 3 OPEN) — one file each,
    not one combined file, to match the `.ai/tasks/TASK-XXXX` one-record-
    per-file precedent and let each be independently claimed/updated
  - add the two gates to `.ai/COMMON.md`'s "Current Rules": (1) a task may
    not move to `DONE` if it opens an unregistered seam, (2) the repo is
    not green if an `OPEN` seam has no seam-test (`xfail` allowed at open)
  - add a "Seam Protocol" row to `.ai/COMMON.md`'s Quick Navigation and
    Source Of Truth table (seams are mutable coordination state, same
    bucket as the task registry)
  - cross-link from `.ai/reference/OPERATION_PROTOCOL.md`'s Cycle Steps
    table — the "seam sweep" is a new pass type that doesn't map onto any
    existing step 0-12 (it's explicitly *not* the Critic Review step,
    since seams are cross-unit by definition and a single-unit review
    won't find them per the doc's own "Why this exists" section)
- Out Of Scope:
  - actually running the seam sweep (enumerating current cross-unit data
    flows and registering new seam records beyond the 5 seeds) —
    [[TASK-0053]], a separate task, since sweeping is analysis work with
    its own evidence trail, not a scaffold-plumbing change
  - resolving any of the 3 `OPEN` seeded seams — each becomes its own
    follow-up once a seam-owner is assigned (the doc requires a real
    `TASK-XXXX` owner, not "TBD"); this task registers them, doesn't
    close them
  - retrofitting the gates onto already-`DONE` tasks (TASK-0003–0012) —
    not practical or useful to reopen closed tasks; the gates apply
    going forward from this task landing
- Constraints And Invariants:
  - per the source doc: "A seam with no owner is the defect condition
    this protocol exists to prevent" — every seed record's `owner` field
    must be a real, resolvable `TASK-XXXX`, never a placeholder. Two of
    the three `OPEN` seeds don't have an obvious existing owner yet; for
    those, the owner is *this task* until a dedicated follow-up is filed
    (see Done section for the resolution), not left blank.
  - additive only — no existing `.ai/tasks/README.md` or `COMMON.md`
    section gets rewritten, only extended (matches TASK-0002's bootstrap
    precedent).
- Acceptance Scenarios:
  - Given `.ai/seams/`, when any of the 5 seed records is opened, then it
    has a named owner (a real task), a stated invariant as an assertion
    (not prose), and a status.
  - Given `.ai/COMMON.md`, when a reader checks "can I mark my task Done,"
    then the seam-registration gate is stated as a rule they'd actually
    see, not buried only in `.ai/reference/SEAM_PROTOCOL.md`.
- Planned Validation: not code — validation is "does every seed record in
  the source doc's table have a corresponding `.ai/seams/SEAM-000N` file,"
  checked by direct comparison, not assumed.

## In Progress

None

## TODO

- [x] Relocate `SEAM_PROTOCOL.md` -> `.ai/reference/SEAM_PROTOCOL.md`.
- [x] Write `.ai/seams/README.md`.
- [x] Write `SEAM-0001` through `SEAM-0005` from the source doc's seed
      table, with real owners (see Constraints and Done below).
- [x] Add the two gates + Quick Navigation/Source-Of-Truth entries to
      `.ai/COMMON.md`.
- [x] Cross-link from `.ai/reference/OPERATION_PROTOCOL.md`.
- [x] Register `.ai/seams/` and this task in `.ai/COMMON.md`'s Active
      Work Registry.

## Dependency

- [[TASK-0051]] — sibling task, same relocation pattern, for
  `INVARIANCE_PROTOCOL.md`; not blocking each other.
- [[TASK-0047]] — independent prior evidence for seed seam #3 (pocket ↔
  functional/terminal exclusion).
- [[TASK-0053]] — depends on this task landing (needs `.ai/seams/` to
  exist before it can register new sweep findings there).

## Open Questions

- Resolved: seed seam #3 is owned by [[TASK-0052]] (filed by this task —
  also the leakage-gate reconciliation task, since the missing assembly
  step and the leakage gate's assumed `build_labels` contract are the
  same gap). Seed seam #4 is owned by [[TASK-0055]] (filed by this task).
  Neither had an obvious pre-existing owner, so both are new, narrowly-
  scoped follow-ups rather than speculative reuse of an unrelated task.
- Seed seam #5 ("classify_failure/verdict ↔ baselines") names
  `baselines.py` as the stubbed floor — that's [[TASK-0011]], currently
  claimed and in progress by a parallel Implementer thread at this task's
  filing time; landed Done during this same session. Per `SEAM-0005`'s
  own record, its status should still not be auto-flipped to `VERIFIED`
  on that basis alone — landing `baselines.py` doesn't by itself prove a
  seam-test exists and passes. Left `OPEN` pending [[TASK-0053]]'s sweep.

## Done

- Relocated `SEAM_PROTOCOL.md` to `.ai/reference/SEAM_PROTOCOL.md`.
- Created `.ai/seams/README.md` and 5 seed records (`SEAM-0001`
  through `SEAM-0005`), each with a real task owner: 2 already-Done
  tasks for the `VERIFIED` seeds, and 2 new follow-up tasks filed by this
  task ([[TASK-0052]], [[TASK-0055]]) plus one existing in-flight task
  ([[TASK-0011]], now Done) for the 3 `OPEN` seeds.
- Added both gates (definition-of-done addendum, green-bar addendum) plus
  Quick Navigation and Source-Of-Truth entries to `.ai/COMMON.md`.
- Cross-linked the seam sweep as a distinct pass from `.ai/reference/
  OPERATION_PROTOCOL.md`'s existing Critic Review step.
- Registered this task and `.ai/seams/` in the Active Work Registry.
- Filed [[TASK-0053]] as the first actual seam sweep (not run by this
  task — a distinct, evidence-gathering pass owned by General Critic).
