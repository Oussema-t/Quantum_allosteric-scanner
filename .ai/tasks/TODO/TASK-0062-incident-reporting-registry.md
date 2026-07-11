# TASK-0062 Incident-reporting registry + tool

## Context

- ID: TASK-0062
- Title: A `.ai/memory/incidents/` registry (one structured file per
  incident, mirroring `.ai/memory/questions/`'s directory-per-concern
  pattern) plus a small `.ai/tools/incident.py` filing/listing tool, so
  "something went wrong" reports are captured as objective structured
  facts an agent or human can later use to *infer* severity/patterns —
  not a self-declared severity label at filing time
- Status: TODO
- Owner: Toolsmith
- Claimed By: —
- Claimed At: —
- Source: direct request, this session, 2026-07-11 — this session alone
  has generated a real incident history (the `.ai/COMMON.md` whole-file
  collisions that motivated TASK-0017/0024, the misattributed-commit
  incident behind TASK-0028, the rename-detection false-mismatch behind
  TASK-0024.002, and Q-0001's `GIT-COMMIT`-doesn't-prevent-concurrent-
  staging finding), every one of them currently recorded only as
  free-text prose scattered across whichever task's `Source`/`Context`
  section happened to be open at the time. Nothing today lets a thread
  ask "how many incidents this session involved a git-staging race" or
  "which mechanism has broken the most times" without re-reading every
  task file's prose by hand.
- Scope: a new `.ai/memory/incidents/` directory (README + template,
  matching `.ai/memory/questions/README.md`'s shape) plus a small
  standalone `.ai/tools/incident.py` (imports/reuses `claim.py`'s id-
  reservation logic directly, same-directory-import style as
  `.ai/tools/task_locate.py`, not a new subcommand bolted onto an already
  eight-subcommand `claim.py`).

## Intent Contract

- Outcome: reporting an incident is one command that writes a structured
  file with a guaranteed-unique id; the fields captured are objective and
  checkable (what happened, how it was detected, blast radius, whether
  data was lost, whether/how it was fixed) rather than a self-declared
  `Severity: High/Medium/Low` guess — severity gets *inferred* later
  (by a human reviewing the structured facts, or by a future aggregation
  pass once enough real incidents exist) from consistent raw material,
  not asserted inconsistently by whichever agent happens to be filing.
- In Scope:
  - **Decided: no self-declared severity field.** Capture instead:
    `Detection` (how/who noticed — self-caught / automated check failure
    / human review / another agent's question), `Blast Radius` (files/
    threads/commits affected, as concrete counts or names, not a
    subjective scale), `Data Loss` (Y/N + what, if any), `Recovery`
    (was a fix applied, link to the commit/task that did it, or "not yet"),
    and `Time To Detect` (if knowable from timestamps — often it won't
    be, that's fine, leave it blank rather than guess). These four/five
    facts are what "infer severity" means here: a reviewer (or a future
    scoring pass) derives severity from them, consistently, across every
    incident, instead of trusting each reporter's own judgment call at
    the moment they're still in the middle of dealing with it.
  - **Decided: generalize `claim.py`'s `reserve-next` id-allocation
    instead of writing a second one.** Incidents need the exact same
    collision-safe "give me the next unused id" guarantee `reserve-next`
    already provides for `TASK-XXXX` (the read-then-write race that
    motivated TASK-0045 applies identically to any global, flat,
    sequential id space — and incidents are flat/global, unlike questions,
    which are numbered per-addressee-folder and don't have this problem).
    Add a namespace/directory parameter to the existing allocation logic
    in `claim.py` rather than reimplementing the highest-plus-one-with-
    retry loop a second time for `INC-XXXX`; `.ai/tools/incident.py`
    calls that generalized function directly (import, not subprocess —
    same pattern `task_locate.py` already uses for `claim.py`'s
    lock-reading functions).
  - `.ai/tools/incident.py file --category TEXT --component TEXT
    --summary TEXT [--detection TEXT] [--blast-radius TEXT]
    [--data-loss yes|no] [--related TASK-XXXX|Q-XXXX|commit ...]` —
    writes a new `.ai/memory/incidents/INC-XXXX-slug.md` from the
    supplied fields plus a freeform `## What Happened` body the caller
    still writes by hand (matching every other tool in this session's
    "bootstrap the skeleton, don't try to mechanize the actual judgment
    content" precedent — `move`/`derive-task` don't write Done sections
    either).
  - `.ai/tools/incident.py list [--category TEXT]` — read-only listing,
    plain text or `--json`, for a thread that wants to check "has this
    kind of thing happened before" before re-diagnosing something from
    scratch.
  - a `.ai/memory/incidents/README.md` (directory purpose, required
    fields, naming) and a starter template, matching
    `.ai/memory/questions/README.md`'s shape and level of detail.
- Out Of Scope:
  - any automatic severity-*scoring* formula (e.g. a weighted
    points-per-incident algorithm) — explicitly deferred. Capture the raw
    structured facts first; build scoring once there's enough real
    incident data to validate a formula against, the same "advisory/
    convention first, harden after real volume" precedent this whole
    scaffold already follows (TASK-0017→TASK-0024, TASK-0025's own
    deferral, TASK-0028→TASK-0042).
  - retroactively back-filling this session's *already-documented*
    incidents (the COMMON.md collisions, the misattributed commit, the
    rename-detection finding, Q-0001) into the new registry as a bulk
    migration — optional future cleanup, not required for this task to
    be Done; new incidents from here forward are the actual goal.
  - any claim/lock mechanism for incident files themselves — a filed
    incident is a append-once historical record, nobody edits someone
    else's incident report the way a task file gets iterated on, so
    there's no contention case to protect against yet (same reasoning
    TASK-0060 used for skipping a lock on questions).
  - linking incidents into `.ai/reference/CAPABILITIES.md` — this is a
    memory/reporting registry, not a capability provider in the
    Commit-Packager sense; don't force it into that catalog's shape.
- Constraints And Invariants:
  - Python stdlib only, no new dependency.
  - reuse `reserve-next`'s existing retry-on-lost-race logic via the
    generalized/parametrized function — do not duplicate it.
  - keep incident files plain, grep-able markdown, matching every other
    registry in this scaffold — no hidden structured format a human can't
    read directly.
- Planned Validation:
  1. File two incidents back-to-back via concurrent calls (mirroring
     TASK-0045's own 5-way concurrent-`reserve-next` validation, scaled
     down); confirm both get distinct ids, no collision.
  2. `incident list` output matches what's actually on disk under
     `.ai/memory/incidents/`.
  3. Confirm `reserve-next`'s generalization doesn't change its existing
     `TASK-XXXX` behavior — re-run TASK-0045's own validation cases
     against the changed function as a regression check.

## Dependency

- [TASK-0045](../DONE/TASK-0045-highest-task-lookup-tool.md) (Done) —
  `reserve-next`'s existing logic, generalized rather than duplicated.
- [TASK-0065](TASK-0065-git-commit-queue.md) (TODO, unclaimed) — the
  *other* pending consumer of the same `reserve-next` generalization
  (ticket numbers for its commit queue, instead of `INC-XXXX` ids).
  Whichever of these two tasks lands first should do the actual
  namespace-parameter generalization; the other just consumes it —
  coordinate rather than each building a separate generalized version.
- `.ai/tools/task_locate.py` — the same-directory-import pattern this
  task's `incident.py` follows for reusing `claim.py` internals.
- `.ai/memory/questions/README.md` — the directory-per-concern,
  structured-file-per-entry shape this task's registry mirrors.

## Open Questions

- Should `incident.py` eventually gain a `report`/`summarize` command
  that aggregates filed incidents by category/component (a first real
  step toward "infer severity" at scale), or is that better left as a
  human skimming `incident list` output until there's enough volume to
  make aggregation worth automating? Recommend the latter for now —
  named explicitly as Out Of Scope above, revisit once real incident
  count is high enough to make manual skimming genuinely tedious.
- Should incidents be allowed to reference *each other* (e.g. "this is
  the same root cause as INC-0001, recurring") as a structured field, or
  is prose cross-referencing in `## What Happened` sufficient? Recommend
  starting with prose — a dedicated `Related Incidents` field is cheap to
  add later if recurrence-tracking turns out to matter once there's
  enough data to need it.

## Done

(not yet)
