# TASK-0194 `ARCHITECTURE.md` change log is five weeks behind the backend it documents

## Context

- ID: TASK-0194
- Title: bring `ARCHITECTURE.md`'s change log and directory layout — and
  `SOFTWARE.md` where affected — up to date with every `backend/`/`frontend/`
  commit since 2026-06-28, per `CLAUDE.md` convention #7.
- Status: Done
- Resolution: done
- Resolution Note: 5 retroactive dated changelog lines added; geometry.py/rcsb_extract.py added to §2 diagram + §5 layout; SOFTWARE.md clarified for TASK-0031's widened error coverage; ls backend/*.py vs §5 completeness confirmed both directions; no code changed
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

- [x] Five retroactive, dated, signed change-log lines (marked retroactive).
- [x] `geometry.py` → §5 layout + §2 diagram.
- [x] `rcsb_extract.py` → §5 layout (status preserved).
- [x] `SOFTWARE.md` check for TASK-0031's error-response impact.
- [x] `ls backend/*.py` vs. §5 completeness check, both directions.

## Dependency

- None. Fully parallelizable with everything else.

## Open Questions

- Convention #7 has now been missed five times in a row on the product layer
  while being followed rigorously on the research layer. Is the convention
  wrong for `backend/` (too heavy for small fixes), or is the product layer
  simply getting less attention? Worth one sentence of honest diagnosis in
  this task's Done section — a convention nobody follows is worse than no
  convention. **Diagnosed, not fixed**: all 5 missed commits are single-
  purpose bug/dedup/test fixes with commit messages that already say
  everything a change-log line would (the `git log` table above was
  assembled straight from those messages, near-verbatim) — the convention
  isn't too heavy, it's redundant with an already-good commit message at
  the moment of committing, which is exactly when it's easiest to skip.
  The research layer's own `.ai/tasks/` discipline doesn't have that
  redundancy (a task file's Done section says things a commit message
  doesn't), so it doesn't compete with anything and gets followed. This is
  an attention/incentive gap, not a broken rule — worth raising to the
  team as a candidate for a lighter mechanical check (e.g. a pre-commit
  reminder when `backend/`/`frontend/` changes and `ARCHITECTURE.md`
  doesn't) rather than more manual discipline, but that is a process
  decision for the team, not this task's call.

## Done

**2026-08-03, Implementer B.** Re-derived the commit list independently
before trusting the filing's own table: `git log --format="%H %ad %s"
--date=short -- backend/ frontend/` reproduces the same 5 commits with the
same dates (the filing's two `—` dates for TASK-0066/TASK-0074 resolve to
2026-07-12 for both).

Added 5 retroactive change-log lines to `ARCHITECTURE.md`, each opening
with an explicit `[Retroactive entry, backfilled 2026-08-03 by TASK-0194]`
marker — visibly retroactive, per the Constraint, not backdated to look
like they were written at commit time. One line per commit, not folded
into a summary (TASK-0030/0031/0032/0066/0074).

`§2`'s mermaid dependency diagram: added `geometry` as a new leaf,
consumed by `discovery` and `analysis` — verified by grepping actual
imports (`grep -rn "from .geometry" backend/*.py`) rather than assuming
from the commit message; `compare.py` does NOT import it (checked
directly, it never had its own duplicate to dedupe).

`§5`'s directory layout: added `geometry.py` and `rcsb_extract.py`
(preserving its existing "not yet wired into the API, see TASK-0034"
status verbatim from the change-log prose that already mentioned it).

`SOFTWARE.md`: read TASK-0031's actual diff (`git show e6e442e --
backend/data_layer.py`) rather than inferring from its commit message.
Confirmed the documented `/api/load` 422 message/status code are
byte-identical before and after (`pipeline.py:100`'s `ValueError` message
is unchanged) — the real change is which failures reach that same path
(URLError/timeout now degrade cleanly; previously only HTTPError did,
everything else was an unhandled 500). Added one clarifying sentence to
that message's existing doc line rather than treating it as unchanged
and skipping the update. Checked the one other candidate site
(`/api/structure`'s `could not read structure {pdb_id}: {e}`) and
confirmed it already blanket-catches `Exception`, so TASK-0031 changed
nothing there — not touched.

Completeness check both directions: `ls backend/*.py` (11 non-test
modules: `main, pipeline, data_layer, rcsb, rcsb_extract, discovery,
active_site, analysis, compare, geometry, systems`) now matches `§5`'s
listing exactly, 1:1. Test files (`test_*.py`) and `__init__.py` were
already, consistently, not listed in `§5` before this task and remain
so — not a gap, matching that section's own existing scope.

Sanity-checked the file after editing: fenced code-block count in
`ARCHITECTURE.md` stayed even (balanced), mermaid `flowchart`/`sequenceDiagram`
blocks unchanged in count, no code touched anywhere (Out of Scope,
confirmed via `git diff --stat` before staging — only `ARCHITECTURE.md`
and `SOFTWARE.md` in the diff).
