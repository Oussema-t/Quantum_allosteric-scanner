# TASK-0020 Product (backend/frontend) intent & feature inventory audit

## Context

- ID: TASK-0020
- Title: Enumerate every `backend/` endpoint and every `frontend/` UI
  control/feature, state its intended purpose and which challenge-rubric
  criterion or roadmap phase it serves, and flag anything without a stated
  purpose
- Status: TODO
- Owner: Architect/Planner
- Claimed By: Intent-Inferrer (this thread)
- Claimed At: 2026-07-04 15:10
- Source: user request, 2026-07-04 session — "we have already had
  mis-communication inside of the team regarding what the software should
  be doing, whether it's clear what it is doing, what the functions are...
  Making the assertion that the desired intent is there actually
  unfeasible." Distinct from TASK-0018 (which compares physics-code
  *architecture* between `backend/` and the research scaffold) — this task
  is about the **Product's own intent legibility**, backend + frontend
  together, independent of the research-scaffold question entirely.
- Crit Ref: none in `.claude/TASKS.md` — confirmed by grep that the closed
  BLUE/RED/ORCH ledger and `.claude/improvements/test_coverage.md` scope
  exclusively to `__WORK_IN_PROGRESS__/src/allostery`; `backend/`/`frontend/`
  have no prior criticism thread at all. This is a new thread, not a resume.
- Scope: every file under `backend/` and `frontend/`; read-only against
  those trees (no code changes here, see Out Of Scope)

## Intent Contract

- Outcome: one document (`SOFTWARE.md` gains a new "Feature intent map"
  section, or a standalone `.ai/reviews/PRODUCT_INTENT_MAP.md` if
  `SOFTWARE.md` is deemed the wrong home — decide which, don't do both)
  listing:
  - every `backend/main.py` endpoint (already partially enumerated in
    `SOFTWARE.md` §4 — this task verifies that list against the actual
    route table, not just the doc, and adds the "why" column that doc
    section currently lacks)
  - every distinct `frontend/app.js` user-facing control/feature (toolbar
    inputs, panel toggles, chart modes, export buttons, the "Motion"
    real-structures-vs-linear toggle, region selector, etc. — read the
    ARCHITECTURE.md change log as the feature census, then verify each
    line against current `app.js`/`index.html`, since some log entries may
    already be superseded or dead)
  - for each item: a one-line stated purpose, which rubric criterion
    (Problem/Impact, Technical, Feasibility, Validation, Hybrid, Team —
    `SOFTWARE.md` doesn't currently cite the rubric at all; pull it from
    wherever the challenge rules actually live, ask the user if not found
    in-repo) or roadmap phase (①/②/③) it serves, and a confidence flag
    (`stated` / `inferred` / `unclear`)
- In Scope:
  - reading `backend/*.py`, `frontend/*`, `ARCHITECTURE.md`,
    `SOFTWARE.md` in full
  - producing the inventory + purpose mapping
  - explicitly flagging every item that cannot be given a `stated` or
    confidently `inferred` purpose — these feed TASK-0023 directly, don't
    pre-judge them as scope-creep here (that's TASK-0023's call), just
    surface them
- Out Of Scope:
  - deciding whether an unclear-purpose item should be removed (TASK-0023)
  - writing any tests (TASK-0021/TASK-0022)
  - touching `backend/`/`frontend/` source at all — this is a documentation
    task, zero behavior risk
- Acceptance Scenarios:
  - Given the finished inventory, when any `backend/main.py` route or any
    `app.js` user-facing control is looked up, then the document states
    its purpose and rubric/phase linkage (or explicitly flags it unclear).
  - Given a reviewer with no prior context, when they read the inventory
    alone, then they can answer "what does this app do and why" without
    reading `app.js` line by line.
- Constraints And Invariants:
  - additive documentation only, per the scaffold's general
    additive/corrective norm (TASK-0002) — do not delete or rewrite
    existing `SOFTWARE.md`/`ARCHITECTURE.md` content to make room, append/
    cross-link instead.
  - do not conflate this with TASK-0018: that task's "why do two
    `analysis.py` files exist" question is about the *physics*
    implementation split; this task's question is "does every Product
    feature have a stated reason to exist," a different axis entirely (a
    feature can have perfectly justified physics and still be scope creep
    relative to the challenge, or vice versa).
- Planned Validation: no code to run — validation is a completeness check
  (every route in `backend/main.py`'s route table appears in the inventory;
  every `id=`/event-listener-bound control in `frontend/app.js` appears or
  is explicitly noted as internal/non-user-facing).

## In Progress

None

## TODO

- [ ] Extract the full `backend/main.py` route table (method + path) and
      diff it against `SOFTWARE.md` §4's documented endpoint list — note
      any drift (undocumented route, or documented route that no longer
      exists).
- [ ] Walk `frontend/app.js` for every user-facing control (toolbar
      inputs, buttons, toggles, chart mode selectors) and cross-reference
      against `ARCHITECTURE.md`'s change log to identify which log entry
      introduced it.
- [ ] For each endpoint/control, write the one-line stated purpose +
      rubric-criterion-or-phase + confidence flag.
- [ ] Locate the actual challenge rubric (Problem/Impact 25, Technical 25,
      Feasibility 20, Validation 15, Hybrid 5, Team 10 is quoted in
      `.ai/tasks/PLANS/PLAN-01.07.26.md` Week 3 — confirm this is the full,
      current rubric and not a paraphrase; ask the user if the authoritative
      rubric document isn't in-repo).
- [ ] Decide + record where the inventory lives (`SOFTWARE.md` new section
      vs standalone `.ai/reviews/` doc) and link it from both
      `ARCHITECTURE.md` and `SOFTWARE.md`.
- [ ] List every `unclear`-purpose item separately at the end, as the
      direct input list for TASK-0023.

## Dependency

- None to start (can begin immediately from `SOFTWARE.md`/`ARCHITECTURE.md`
  + the live source).
- Feeds TASK-0021, TASK-0022 (their test scope should cover this task's
  enumerated surface, not be designed independently of it).
- Feeds TASK-0023 directly (its unclear-purpose list is that task's input).

## Open Questions

- Is the six-criterion rubric quoted in `PLAN-01.07.26.md` the authoritative,
  current version, or a paraphrase from an earlier reading of the challenge
  rules? This task's rubric-linkage column is only as good as that source —
  flag to the user rather than assume.
- Should this inventory be kept live (updated every time a Product feature
  is added, per the user's implied "no more flying blind" goal) or is this
  a one-time snapshot? Recommend live — add "update the intent map" to
  `SOFTWARE.md`'s existing "update in the same commit" maintenance rule
  (CLAUDE.md convention 7 already establishes this pattern for other docs).

## Done

(not yet)
