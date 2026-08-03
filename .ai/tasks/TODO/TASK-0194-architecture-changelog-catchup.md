# TASK-0194 `ARCHITECTURE.md` change log is five weeks behind the backend it documents

## Context

- ID: TASK-0194
- Title: bring `ARCHITECTURE.md`'s change log and directory layout — and
  `SOFTWARE.md` where affected — up to date with every `backend/`/`frontend/`
  commit since 2026-06-28, per `CLAUDE.md` convention #7.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: Reviewer thread, 2026-08-03, finding F7.
- Priority: **P2 — documentation debt on the product layer, not the research
  layer. But it is a direct, repeated violation of a MUST-follow convention,
  and the product layer is what the jury interacts with.**
- Dependency: none.

## Why this matters

`CLAUDE.md` convention #7 is unambiguous:

> *Keep docs in sync: update `ARCHITECTURE.md` (+ a **dated, signed**
> change-log line) and `SOFTWARE.md` in the **same commit** as any change to
> modules / endpoints / response fields / frontend behavior / conventions.*

`ARCHITECTURE.md`'s newest change-log entry is **2026-06-28**. Since then,
five commits changed `backend/` or `frontend/`:

| Commit | Date | Change |
|---|---|---|
| `c5cd13f` | 2026-07-05 | **new module** `backend/geometry.py` (Kabsch dedup, TASK-0030) |
| `b3e7ef4` | 2026-07-11 | HTML-escape RCSB strings before `innerHTML` (TASK-0032) |
| `e6e442e` | 2026-07-12 | broaden `data_layer.fetch()` error handling (TASK-0031) |
| `1232340` | — | shared Kirchhoff context + DCC helper in `backend/analysis.py` (TASK-0066) |
| `2ea0224` | — | characterization tests for `backend/analysis.py` (TASK-0074) |

None produced a change-log line. Additionally, `ARCHITECTURE.md` §5's
directory layout lists **neither** `backend/geometry.py` (a real module since
July 5) nor `backend/rcsb_extract.py` (mentioned in the change log's prose but
absent from the layout since June 28). §2's module-dependency diagram is
likewise missing `geometry`.

A new agent or teammate onboarding via `CLAUDE.md` → `ARCHITECTURE.md` — which
is exactly what `CLAUDE.md` instructs them to do — gets a module map that is
missing two modules.

## Intent Contract

- Outcome: `ARCHITECTURE.md`'s change log, §2 dependency diagram, and §5
  directory layout reflect the current `backend/`; `SOFTWARE.md` updated where
  any of these changed a documented behaviour.
- Why required, not assumed: convention #7 is listed under "Conventions (MUST
  follow)". Five consecutive violations is a process signal, not an oversight.
- In Scope:
  - One dated, signed change-log line per commit above, back-dated to the
    commit's own date with a note that it is a retroactive entry (do not
    pretend they were written at the time).
  - Add `geometry.py` to §5's layout and §2's dependency diagram.
  - Add `rcsb_extract.py` to §5's layout, with its "not yet wired into the
    API" status preserved.
  - Check whether TASK-0031's error-handling change altered any documented
    error response in `SOFTWARE.md`; update if so.
  - Confirm no other `backend/` module is missing from §5.
- Out Of Scope:
  - Any code change.
  - Resolving [[TASK-0034]] (the `data_layer`/`rcsb_extract` overlap question)
    — that is its own filed task; this one only documents what exists.
- Constraints And Invariants:
  - Retroactive entries must be visibly retroactive. This project's whole
    credibility rests on not backdating.
  - Do not fold five changes into one summary line — convention #7 says one
    line per change.
- Planned Validation:
  - `ls backend/*.py` vs. §5's layout: every file present in both directions.
  - Every module in §2's diagram exists; every existing module appears.

## In Progress

—

## TODO

- [ ] Five retroactive, dated, signed change-log lines (marked retroactive).
- [ ] `geometry.py` → §5 layout + §2 diagram.
- [ ] `rcsb_extract.py` → §5 layout (status preserved).
- [ ] `SOFTWARE.md` check for TASK-0031's error-response impact.
- [ ] `ls backend/*.py` vs. §5 completeness check, both directions.

## Dependency

- None. Fully parallelizable with everything else.

## Open Questions

- Convention #7 has now been missed five times in a row on the product layer
  while being followed rigorously on the research layer. Is the convention
  wrong for `backend/` (too heavy for small fixes), or is the product layer
  simply getting less attention? Worth one sentence of honest diagnosis in
  this task's Done section — a convention nobody follows is worse than no
  convention.

## Done

—
