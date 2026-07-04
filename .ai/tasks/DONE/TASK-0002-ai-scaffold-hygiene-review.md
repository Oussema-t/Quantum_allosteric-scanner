# TASK-0002 AI-Scaffold Hygiene & Engineering Review

## Context

- ID: TASK-0002
- Title: Thorough hygiene review of the `.ai/` + `.github/` scaffold after the
  repo-root relocation (commit `255b72e`) and the TODO/IN_PROGRESS/DONE/PLANS
  restructure (this task's own prerequisite work, already applied)
- Status: Done
- Owner: General Critic (dedicated review thread — user starts this thread)
- Source: user request, 2026-07-04 session
- Scope: `.ai/`, `.github/`, `.claude/` — coordination layer only, not
  `__WORK_IN_PROGRESS__` module content (see TASK-0003+ for that)

## Intent Contract

- Outcome: the scaffold is internally consistent — one authoritative plan,
  no dangling references, every active task registered, every stated
  convention actually followed by the files that exist.
- In Scope:
  - reconcile `.ai/tasks/PLANS/PLAN.md` (phase-gated pipeline plan) against
    `.ai/tasks/PLANS/PLAN-01.07.26.md` (week-by-week action plan, written one
    week later by a thread with no repo access). They overlap ~70% in content
    (both describe Phase 0/1/2 gates) but were never merged. Decide: is
    PLAN-01.07.26.md a superseding rewrite, a companion timeline overlay, or
    stale and should be marked historical? Record the decision in both files'
    headers.
  - audit every `[[link]]`-style and backtick-path cross-reference under
    `.ai/` and `.claude/` for files that moved or don't exist (the
    TODO/IN_PROGRESS/DONE/PLANS restructure already fixed the 12 known
    `TASK-0001` references — verify no others were missed, and re-run this
    check after every future scaffold move).
  - confirm `.ai/COMMON.md`'s Active Work Registry lists every file currently
    in `TODO/`, `IN_PROGRESS/`, and `PLANS/` — it must not silently drift out
    of sync the way it did before this session (it only tracked TASK-0001
    while PLAN-01.07.26.md sat untracked in the same folder).
  - explicitly document, in `.ai/README.md` or `.ai/COMMON.md`, why
    `__WORK_IN_PROGRESS__/src/allostery/`, `__WORK_IN_PROGRESS__/tests/`, and
    (once created) `__WORK_IN_PROGRESS__/config/` stay under
    `__WORK_IN_PROGRESS__/` rather than moving to repo root alongside
    `backend/`/`frontend/` — commit `255b72e`'s message implies this was
    deliberate ("challenge sandbox" vs repo-wide scaffold) but no doc states
    it outright; a future agent will otherwise "fix" this as an oversight.
  - review `.claude/TASKS.md`, `.claude/HAMILTONIANS.md`, and
    `.claude/criticism/*` for overlap with the new `.ai/tasks/` structure —
    `.claude/TASKS.md` already runs its own BLUE/RED/ORCH task ledger
    (T-001…T-021) for the same `__WORK_IN_PROGRESS__` codebase. Decide
    whether `.claude/TASKS.md` and `.ai/tasks/TODO|IN_PROGRESS|DONE/` are two
    parallel systems that need a stated boundary, or whether one should
    fold into the other. Do not silently merge them without a decision
    recorded here first.
  - spot-check `.github/prompts/*` slash-command surfaces against what
    `.ai/reference/SLASH_COMMAND_CANDIDATES.md` claims exists — the ripeness
    review (`.ai/reviews/REVIEW-2026-06-25-scaffold-ripeness.md`, 88/100)
    flagged some delegate surfaces as "more documented than operational";
    confirm current status.
- Out Of Scope: writing new module code, touching `backend/`/`frontend/`.
- Acceptance Scenarios:
  - Given `.ai/tasks/PLANS/`, when both plan docs are read together, then a
    single "authoritative for X" statement resolves every overlapping claim.
  - Given any cross-reference under `.ai/`/`.claude/`, when followed, then
    the target file exists at that path.
  - Given `.ai/COMMON.md`'s registry, when compared against `ls .ai/tasks/TODO
    .ai/tasks/IN_PROGRESS`, then every file is represented.
- Constraints And Invariants:
  - additive/corrective only — don't delete history, mark superseded docs
    superseded rather than removing them.
  - this task itself must end up filed as DONE with a short changelog of what
    was reconciled, not just closed silently.
- Planned Validation: manual read-through + link grep
  (`grep -rn '\.ai/\|\.claude/' .ai .claude .github --include="*.md"` and
  verify each hit resolves).

## In Progress

Closed out in one pass, 2026-07-04 — see Done below.

## TODO

(none remaining — all six items closed, see Done)

## Dependency

- None (this is the top-level hygiene pass); TASK-0003 through TASK-0015 are
  downstream module tasks whose registry entries this task must keep synced.

## Open Questions

- Partially resolved: `.claude/TASKS.md` does not fold into `.ai/tasks/` —
  it's closed to new entries and stays as historical record; new work
  (regardless of which codebase area it touches) files as `TASK-XXXX`
  going forward. See `.ai/COMMON.md` → "Task Ledger Boundary". Still open:
  whether `.claude/HAMILTONIANS.md`, `.claude/hypotheses/*`,
  `.claude/discussions/*`, and `.claude/improvements/*` should get a
  similar explicit boundary statement, or are fine as free-form working
  notes with no lifecycle — out of this pass's time budget, flag for a
  follow-up task if they start drifting.
- Still open: is `PLAN-01.07.26.md` meant to be regenerated periodically (a
  new dated `PLAN-DD.MM.YY.md` each week) or was this a one-off snapshot?
  Noted in both plan files' headers; needs a human call, not an agent
  guess — ask before authoring a second dated plan file.

## Done

- Reconciled `PLAN.md` vs `PLAN-01.07.26.md`: companion, not superseding —
  `PLAN.md` is the phase-gated technical plan, `PLAN-01.07.26.md` is a
  weekly timeline overlay against the 2026-09-15 deadline. Decision
  recorded in both files' headers.
- Full cross-reference audit under `.ai/`, `.claude/`, `.github/`
  (`*.md`, backtick-path and markdown-link styles): 83 unique path
  references checked. The 6 that initially resolved as "missing" are
  false positives — one is a hypothetical example ID in
  `SECOND_EXPERT_THREAD_WALKTHROUGH.md` (`TASK-0101`), five are
  runtime-generated artifact paths in `.github/prompts/*` and
  `CAPABILITIES.md` (created when the capability runs, not checked in).
  No stale `TASK-0001` or flat (pre-restructure) `PLAN.md`/
  `PLAN-01.07.26.md` references remain from the TODO/IN_PROGRESS/
  DONE/PLANS restructure.
- Synced `.ai/COMMON.md`'s Active Work Registry: it tracked only TASK-0001
  at the start of this pass. A parallel Implementer thread spawned
  TASK-0003 through TASK-0012 (the full `PLAN.md` module backlog —
  `labels.py`, `superpose.py`, `protocol.py`, `select.py`, `analysis.py`,
  `diagnostics.py`, `report.py`, `baselines.py`, `pathways.py`, plus
  `targets.yaml`) **while this review was in progress**, none pre-registered
  — a live demonstration of exactly the drift risk this task exists to
  close, at higher volume than expected. All were added in this pass.
  **Caveat:** that thread may still be spawning more task files after this
  snapshot (`labels.py`→`pathways.py` covers most but not all of `PLAN.md`'s
  module list — `clean.py`, `coarse.py`, `viz.py` had no TASK file as of
  this writing); re-run `ls .ai/tasks/TODO .ai/tasks/IN_PROGRESS` against
  the registry table before trusting it stale-free. Added a rule that
  whoever creates/moves a `TASK-XXXX` file updates the registry in the same
  edit, specifically to stop relying on a reviewer to catch up after the
  fact.
- Documented the `__WORK_IN_PROGRESS__` boundary in `.ai/README.md`:
  `.ai/`/`.claude/`/`.github/` are repo-wide scaffold tooling (why they
  moved to root in `255b72e`); `__WORK_IN_PROGRESS__/src|tests|config`
  stay put because that directory is the CCC quantum-walk research
  sandbox, distinct from the production `backend/`/`frontend/` app, and
  graduates out only via deliberate promotion after a phase gate passes.
- Decided the `.claude/TASKS.md` vs `.ai/tasks/` boundary: not merged.
  `.claude/TASKS.md` is closed to new entries and stays as the historical
  T-001…T-021 ledger; all new work items file as `.ai/tasks/TASK-XXXX`.
  Recorded in `.ai/COMMON.md` ("Task Ledger Boundary") and mirrored at the
  top of `.claude/TASKS.md`.
- Verified `.github/prompts/*` against `SLASH_COMMAND_CANDIDATES.md`:
  26 live prompt files vs. 24 documented — `learn.prompt.md`
  (`/learn`, capability `workflow.learn.manage`) existed but was
  undocumented; added its row. All other files and table rows matched
  1:1, no dangling table entries. The ripeness review's flag that
  implementer/toolsmith delegate surfaces remain "more documented than
  operational" is still accurate as of this pass — only
  `delegate-critic.prompt.md` is live; no code or doc change made there,
  since promoting a new delegate surface is scope creep beyond a hygiene
  review.

### Follow-up pass (same day, 2026-07-04, after this task's own Done was first filed)

User asked to (1) review whether other in-flight task changes affect this
review, (2) check for standalone unit-test tasks (not TODO lines inside
bigger tasks) anywhere in the repo, (3) reconcile any further drift like the
`/learn` finding above, or file a dedicated task for it.

- Reviewed TASK-0003 through TASK-0017, all created by parallel threads
  during/after this task's first pass. TASK-0013/0014/0015
  (`coarse.py`/`viz.py`/holo-direction module) don't conflict with anything
  decided above and were already self-registered in `COMMON.md` by their
  creating thread — the registry-sync rule this task added is visibly
  working. TASK-0017 (soft-lock claim column on the registry) directly
  extends this task's registry-sync rule and explicitly lists this task as
  its dependency; no contradiction found, left for its own thread to
  execute — not implemented here since it wasn't what was asked this turn
  and it's a distinct, non-trivial scope (registry schema change).
- **TASK-0007 explicitly asked this task to do a full spot-check of every
  `[have]` tag in `PLAN.md`** (its own Open Questions section). Did the
  check: `data.py`, `hamiltonians.py`, `propagators.py`, `metrics.py`, and
  `tests/` were correctly tagged. `select.py` and `protocol.py` were tagged
  `[have]` but are 6-line stubs — retagged `NEW`. `clean.py` and
  `potentials.py` were tagged `NEW` but are fully implemented (260 and 173
  lines, zero `NotImplementedError`) — retagged `[have]`. Fixed in
  `PLAN.md`'s repo-structure section with a dated note; answered back in
  TASK-0007's Open Questions.
- Searched for standalone unit-test tasks (not a TODO line inside a bigger
  task): `.claude/TASKS.md` Group B (T-009…T-016) are all already `DONE`.
  T-017/T-018/T-021 remain open but are already tracked with IDs — not a
  gap. Found one genuine orphan: `.claude/improvements/test_coverage.md`
  said a test for `heat()` on indefinite `H_new` output (IMP-H4) was "not
  yet in TASKS.md — must be added," but it never got any task ID anywhere
  and had been sitting dangling since at least 2026-06-21. Filed as
  `.ai/tasks/TODO/TASK-0016-heat-indefinite-hnew-test.md` (per this task's
  own Task Ledger Boundary decision — `TASK-XXXX`, not a new `T-022`) and
  updated the source note in `test_coverage.md` to point at it instead of
  dangling. Registered in `COMMON.md`.
- Re-ran the cross-reference audit; no new dangling links. The one
  borderline case (`.ai/tasks/LOCKS.md`, referenced in TASK-0017) is a
  rejected-alternative mention in backticks, not a claimed-to-exist path —
  correctly never created.
