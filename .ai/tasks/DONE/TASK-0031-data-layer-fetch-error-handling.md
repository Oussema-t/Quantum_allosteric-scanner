# TASK-0031 Broaden `data_layer.py::fetch()`'s exception handling

## Context

- ID: TASK-0031
- Title: `fetch()` only catches `urllib.error.HTTPError`, not the broader
  network-failure class — a transient RCSB outage/timeout produces an
  unhandled 500 instead of a clean error
- Status: Done
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

- [x] Reproduce the uncaught-exception failure mode first (see callout).
- [x] Widen the `except` clause.
- [x] Confirm callers already degrade gracefully on `None`.
- [x] Manual smoke test: force the failure, confirm a clean error response
      instead of a 500.

## Dependency

- None.

## Open Questions

- Is there a *second* instance of this same narrow-catch pattern elsewhere
  in `backend/` worth checking in the same pass, or is `fetch()` the only
  one? (`rcsb.py::_get_json` already uses broad `except Exception`, so it's
  likely just this one function — confirm rather than assume.)
  **Answered:** confirmed by direct grep of every `fetch(`/`load_structure(`
  call site (21 total, across `pipeline.py`, `compare.py`, `active_site.py`,
  `rcsb.py`, `discovery.py`, `analysis.py`) — every one already checks for
  `None` and degrades gracefully (return `None`/`[]`/`{}`, skip, or raise
  `ValueError`). `fetch()` was the only narrow-catch site; no second instance
  found.

## Done

- Reproduced first, per the callout, with no real network dependency:
  monkeypatched `urllib.request.urlretrieve` to raise
  `urllib.error.URLError(socket.gaierror(...))` and `socket.timeout`; before
  the fix, both propagated uncaught out of `fetch()` (confirmed via
  `except urllib.error.URLError` / `except socket.timeout` around the call —
  they were *not* caught by the old `except urllib.error.HTTPError` clause).
  `HTTPError` (404) was confirmed still returning `None`, as today, as the
  baseline that must keep working.
- Fix (`backend/data_layer.py::fetch`): widened the `except` clause to
  `except (urllib.error.URLError, socket.timeout, TimeoutError):` and added
  `import socket`. `URLError` is `HTTPError`'s parent (one clause now covers
  both HTTP and DNS/connection failures); `socket.timeout`/`TimeoutError`
  listed separately because they're distinct classes on Python 3.9 (unified
  only in 3.10+ — see TASK-0044 on the 3.9-vs-3.11.9 convention gap, not
  resolved here, just accommodated). Confirmed a genuinely unrelated
  exception (`ValueError`) still propagates — the widening is not a bare
  `except Exception`.
- Callers: verified all 21 call sites of `fetch()`/`load_structure()` already
  handle `None` (see Open Questions answer above) — no caller-side changes
  needed.
- End-to-end smoke test: with the same `URLError` monkeypatch,
  `pipeline.build_view(...)` now raises the existing clean
  `ValueError("could not load ZZZZ from RCSB — check the PDB ID")` instead of
  an unhandled exception; `POST /api/load` (via `fastapi.testclient.TestClient`
  against the real `backend.main.app`) returns `422` with that message in the
  body, instead of an unhandled 500. Same class of confirmation as the
  originally-cited High finding, now closed.
- Scope held to the Intent Contract: only the `except` clause (+ the new
  `socket` import) changed in `data_layer.py`; no retry/backoff added, no
  caller code touched, no response-shape change on the success path.
