# TASK-0031 Broaden `data_layer.py::fetch()`'s exception handling

## Context

- ID: TASK-0031
- Title: `fetch()` only catches `urllib.error.HTTPError`, not the broader
  network-failure class — a transient RCSB outage/timeout produces an
  unhandled 500 instead of a clean error
- Status: TODO
- Owner: Implementer
- Source: review of all `Oussema-t`-authored commits, 2026-07-05 session —
  High-severity finding #1
- Scope: `backend/data_layer.py::fetch`

## ⚠️ Before implementing

**This finding came from static reading, not from reproducing the failure
at runtime.** Do a short review first: confirm `urllib.request.urlretrieve`
actually raises `URLError`/`socket.timeout` (not something already caught)
for a DNS failure / connection refused / timeout against a real or
simulated unreachable host, and confirm the exception really does
propagate uncaught through `load_structure` → `build_view` →
`POST /api/load` (`main.py`'s handler only catches `ValueError`) before
writing the fix. Don't skip straight to widening the `except` clause on
the strength of the review alone.

## Intent Contract

- Outcome: any RCSB-fetch failure (HTTP error, network error, timeout)
  degrades to the same clean, user-facing error the rest of the app
  already gives — not an unhandled 500.
- In Scope:
  - widen `fetch()`'s exception handling to cover `urllib.error.URLError`
    (parent of `HTTPError`) and `socket.timeout`/`TimeoutError`, returning
    `None` the same way an `HTTPError` does today.
  - confirm every caller of `fetch()`/`load_structure()` already treats a
    `None` return as the "structure unavailable" signal (per a quick read
    of `pipeline.py::build_view`, `discovery.py::complete_apo`, etc. — they
    appear to already handle `None`, just need the exception to actually
    reach that path instead of escaping uncaught).
- Out Of Scope: adding retry/backoff logic — this task only fixes the
  missing catch, not resiliency policy.
- Constraints And Invariants:
  - CLAUDE.md convention 4: ADD-only, don't change the response shape for
    the success path — only the failure path changes (from "unhandled 500"
    to "existing clean error message").
  - Keep the fix minimal: broaden the `except`, don't restructure the
    function.
- Planned Validation: reproduce the failure first (see the callout above)
  — e.g. temporarily point at an unreachable host or a bad PDB_CACHE
  permission to force a `URLError`, confirm it currently escapes uncaught,
  then confirm the fix catches it and the existing `ValueError`-based
  error path in `main.py` renders correctly.

## TODO

- [ ] Reproduce the uncaught-exception failure mode first (see callout).
- [ ] Widen the `except` clause.
- [ ] Confirm callers already degrade gracefully on `None`.
- [ ] Manual smoke test: force the failure, confirm a clean error response
      instead of a 500.

## Dependency

- None.

## Open Questions

- Is there a *second* instance of this same narrow-catch pattern elsewhere
  in `backend/` worth checking in the same pass, or is `fetch()` the only
  one? (`rcsb.py::_get_json` already uses broad `except Exception`, so it's
  likely just this one function — confirm rather than assume.)

## Done

(not yet)
