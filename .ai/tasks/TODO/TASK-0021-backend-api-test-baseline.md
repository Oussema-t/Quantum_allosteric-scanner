# TASK-0021 Backend API test-coverage baseline

## Context

- ID: TASK-0021
- Title: Add a **Playwright** API-request test suite exercising `backend/`
  endpoints against real benchmark PDBs, codifying the assertions
  `SOFTWARE.md` §9 already writes in prose but nothing currently checks
- Status: TODO
- Owner: Implementer
- Claimed By: Intent-Inferrer (this thread)
- Claimed At: 2026-07-04 15:10
- Source: user request, 2026-07-04 session — "the Product software part
  (UI especially) has next to no tests of any kind. Making the assertion
  that the desired intent is there actually unfeasible." Confirmed by
  direct check: no `tests/` directory exists anywhere outside
  `__WORK_IN_PROGRESS__/tests/`, and that one is scoped entirely to
  `src/allostery`. **Update, 2026-07-04 (same session):** tool choice
  resolved by direct user instruction — UI tests *and* API tests both run
  under Playwright (its `APIRequestContext`/`request` fixture covers
  HTTP-only endpoint testing with no browser needed); this supersedes the
  earlier pytest+`TestClient` draft below. Plain Python-level unit tests
  (if a future task needs to test `backend/*.py` functions directly rather
  than through HTTP) stay on `pytest` as a separate, distinct layer — not
  this task's concern, this task is HTTP-endpoint testing only.
- Scope: new `tests/playwright/api/` (repo root — shares one Playwright
  project/config with TASK-0022's `tests/playwright/ui/`; whichever of the
  two tasks lands first sets up the shared `playwright.config`, the other
  reuses it) covering `backend/main.py`'s endpoints

## Intent Contract

- Outcome: every concrete expected-behavior example already written in
  `SOFTWARE.md` §9 ("Writing a Claude test prompt") becomes an executable
  Playwright API test, plus baseline coverage for endpoints that section
  doesn't cover yet — so "the API does what the docs claim" is a command
  to run (`npx playwright test tests/playwright/api`), not a belief.
- In Scope:
  - `GET /api/health` (liveness, no auth)
  - `GET /api/targets` (benchmark dropdown shape)
  - `POST /api/load` happy path (KRAS_G12C 4OBE) + the two documented 422s
    (`chain(s) 'B' not found in 1HHP`, active_site includes 25 for chain A)
  - `GET /api/compare` happy path (4OBE vs 6OIM → rmsd≈1.36, n_aligned≈166,
    drug_code=MOV) + both documented 422s (self-compare, no-ligand-found)
  - `GET /api/analysis-shift`, `GET /api/connectivity-change`,
    `GET /api/morph-frames`, `GET /api/drug-site`, `GET /api/structure`,
    `GET /api/holo-finder`, `GET /api/active-site` — at least one happy-path
    smoke assertion per endpoint (status 200, required top-level keys
    present) even where `SOFTWARE.md` §9 gives no worked numeric example
  - basic-auth enforcement: confirm every non-health endpoint 401s without
    `jury:QAS@CC` and 200s with it
- Out Of Scope:
  - frontend/UI testing (TASK-0022)
  - performance/load testing
  - testing the `__WORK_IN_PROGRESS__` research pipeline (separate test
    tree, separate task family — TASK-0004 through TASK-0016)
  - mocking RCSB/UniProt — these tests hit the real network (small,
    cacheable PDB/UniProt calls per CLAUDE.md's existing dev workflow,
    which already recommends curl+python one-liners against real
    structures); tag them (Playwright `test.describe`/annotation, e.g. a
    `@network` tag via `test.info().annotations`) so a fast/offline subset
    can still be filtered out in CI if one exists
- Constraints And Invariants:
  - do not change `backend/` response shapes to make testing easier —
    CLAUDE.md convention 4 ("ADD-only API changes") applies; tests adapt to
    the API, not the reverse.
  - reuse the exact numeric expectations already in `SOFTWARE.md` §9 rather
    than re-deriving new tolerances independently — if a real run disagrees
    with a documented number, that's a doc bug or a regression to report,
    not a silent tolerance widening.
  - Python 3.9 conventions apply (CLAUDE.md convention 1).
- Planned Validation: `npx playwright test tests/playwright/api` green
  locally against a running `uvicorn backend.main:app` (per CLAUDE.md's
  existing run instructions); each documented `SOFTWARE.md` §9 example has
  a 1:1 test.

## In Progress

None

## TODO

- [ ] Stand up `tests/playwright/api/` + shared `playwright.config`
      (`baseURL` pointed at a locally-run `uvicorn backend.main:app`,
      Basic-Auth credentials wired via `APIRequestContext` `httpCredentials`
      or an `Authorization` header helper) — coordinate with TASK-0022 so
      only one config is created, not two competing ones.
- [ ] Port every `SOFTWARE.md` §9 worked example into a test 1:1, using
      Playwright's `request` fixture (`request.post(...)`, `request.get(...)`,
      asserting `.status()` and `.json()`).
- [ ] Add smoke tests for the remaining endpoints listed in Intent Contract
      that §9 doesn't cover.
- [ ] Add basic-auth enforcement tests (401 without creds, 200 with).
- [ ] Wire into whatever CI exists (check `.github/workflows/` — if none
      exists, note that as a gap but don't build CI infra as a side effect
      of this task; that's a separate scope decision).
- [ ] Cross-check the finished test list against TASK-0020's endpoint
      inventory once that lands — confirm no endpoint was missed.

## Dependency

- TASK-0020 (intent inventory) — not a hard blocker (this task can start
  from `SOFTWARE.md` §4 directly), but the finished inventory is the
  completeness cross-check before calling this task done.

## Open Questions

- Test path resolved: `tests/playwright/api/` at repo root, sharing one
  Playwright project with TASK-0022's `tests/playwright/ui/`. Whether a
  future pure-Python (`pytest`) unit-test layer for `backend/*.py`
  functions gets `tests/unit/` or `backend/tests/` is a separate,
  not-yet-needed decision — don't pre-build it (YAGNI).
- Should these tests hit the real RCSB/UniProt network on every run, or is
  a recorded-fixture (VCR-style cassette) approach worth the added
  dependency? Recommend starting with live network calls (small, already
  disk-cached per `rcsb._get_json`, matches existing CLAUDE.md dev-workflow
  advice) and only add cassettes if CI flakiness from network calls becomes
  a real problem — YAGNI cuts against pre-building the recording
  infrastructure before it's needed.

## Done

(not yet)
