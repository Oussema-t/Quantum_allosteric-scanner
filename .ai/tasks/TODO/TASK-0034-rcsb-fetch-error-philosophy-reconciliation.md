# TASK-0034 Reconcile RCSB-fetch error-handling philosophy + `data_layer`/`rcsb_extract` overlap

## Context

- ID: TASK-0034
- Title: three backend modules that all fetch-from-RCSB use three
  different reliability contracts, and `rcsb_extract.py` appears to
  duplicate `data_layer.py`'s core responsibility
- Status: TODO
- Owner: Architect/Planner
- Source: review of all `Oussema-t`-authored commits, 2026-07-05 session —
  Medium-severity finding #4
- Scope: `backend/data_layer.py`, `backend/rcsb.py`, `backend/rcsb_extract.py`

## ⚠️ Before implementing

**Do a short review before proposing a merge/refactor.** Confirm
`rcsb_extract.py` is actually live/wired into any endpoint or is dead code
awaiting integration (a quick grep of `main.py`/`pipeline.py`/`discovery.py`
imports will show this) — if it's not yet wired in anywhere, the "overlap"
may be intentional forward-looking work (a cleaner rewrite in progress),
not accidental duplication, and the right move is different (finish the
migration) rather than reconciling two live paths.

## Intent Contract

- Outcome: one stated reliability contract for "fetch a structure from
  RCSB" across the backend, and a decision on whether `rcsb_extract.py`
  replaces, complements, or should be merged with `data_layer.py`/`rcsb.py`.
- In Scope:
  - confirm `rcsb_extract.py`'s actual call-site status (see callout
    above) — this determines whether this is a live inconsistency or
    unfinished migration.
  - if `rcsb_extract.py` is unused: either wire it in (if it's meant to
    replace the older fetch path — it has a more robust multi-backend
    parser fallback: Biotite → gemmi → BioPython, vs. `data_layer.py`'s
    BioPython-only path) and retire the older path, or document it as
    deliberately parked/experimental if there's a reason it isn't live.
  - if it's already live somewhere: reconcile `data_layer.fetch`'s narrow
    exception handling (TASK-0031) against `rcsb_extract.py`'s explicit
    "never raises" contract — pick one philosophy and apply it consistently.
- Out Of Scope: the actual code change to unify them (this task is a
  decision + audit; a follow-up task executes it once the decision is
  made, matching TASK-0018's own "decide, then a separate task executes"
  pattern).
- Constraints And Invariants: CLAUDE.md convention 4 — no response-shape
  changes to any live endpoint without a separate, explicit follow-up.
- Planned Validation: this task's output is a decision (which module owns
  RCSB fetching going forward, and why) — validation is "is every current
  caller's behavior accounted for," not a test suite.

## TODO

- [ ] Grep all callers of `rcsb_extract.py`'s functions — confirm live vs.
      unused.
- [ ] Compare the three modules' fetch/cache/parse strategies side by side.
- [ ] Record a decision: retire, merge, or document the split as
      intentional.
- [ ] If retiring/merging is chosen, open a follow-up implementation task.

## Dependency

- TASK-0031 (data_layer.py exception handling) — read together; this task
  may change which module owns the fix.
- TASK-0018 (backend vs. allostery architecture) — same "granularity /
  duplication" theme, one level down (within `backend/` itself rather than
  across `backend/`↔`allostery/`); cross-link, don't duplicate scope.

## Open Questions

- Is `rcsb_extract.py`'s multi-backend parser fallback (Biotite/gemmi/
  BioPython) worth adopting as the one true fetch path even if
  `data_layer.py`/`rcsb.py` are otherwise kept, purely for its
  robustness — independent of whatever the merge/retire decision turns
  out to be?

## Done

(not yet)
