# TASK-0022 Frontend/UI tiered test coverage (presence → functionality → intent → process)

## Context

- ID: TASK-0022
- Title: Build `frontend/app.js` test coverage as four explicit tiers —
  element presence, element functionality (isolated), intent functionality
  (small integrated chains), full E2E process — instead of one
  all-or-nothing golden-path suite
- Status: TODO
- Owner: Implementer
- Claimed By: Intent-Inferrer (this thread)
- Claimed At: 2026-07-04 15:10
- Source: user request, 2026-07-04 session — the frontend/UI is the one
  Product surface with "next to no tests of any kind," compounded by a
  "swarm of agents live updating the code" making manual review
  infeasible. User explicitly asked for the tiered breakdown below rather
  than a single flat E2E suite, so that a broken *widget* and a broken
  *user journey* fail at different, individually diagnosable layers —
  and so cheap, fast tiers (1-2) can run on every change while expensive
  ones (3-4) run less often. **Update, 2026-07-04 (same session):** tool
  choice resolved by direct user instruction — Playwright, confirmed (see
  Open Questions, now resolved). Paths below updated to
  `tests/playwright/ui/`, sharing one Playwright project/config with
  TASK-0021's `tests/playwright/api/`.
- Scope: new `tests/playwright/ui/` (repo root); `frontend/index.html`,
  `frontend/app.js` (read-only — test authorship only, see Out Of Scope)

## Intent Contract

- Outcome: four test tiers, each independently runnable, each testing a
  different failure mode:

  | Tier | Question it answers | Needs backend/network? | Failure it catches |
  |---|---|---|---|
  | 1. Element presence | Does the control exist and render? | No (static page load only) | Someone deleted/renamed a DOM hook, a panel silently stopped rendering |
  | 2. Element functionality (no integration) | Does the widget's own JS logic work in isolation? | No (API calls stubbed/intercepted) | A toggle stopped flipping state, a chart-mode switch stopped swapping the visible div, a client-side validation stopped firing |
  | 3. Intent functionality (small integrated chains) | Does a 2-3-step wiring between control and real API work as documented? | Yes, real backend, narrow scope | "Selecting a target populates inputs but does not auto-load" (ARCHITECTURE.md 2026-06-28) breaks; a button fires the wrong endpoint or wrong params |
  | 4. UI process (E2E) | Does the full jury-visible journey work end to end? | Yes, real backend + network | Any cross-cutting break a jury member would actually hit clicking through the app |

- In Scope, per tier (seed list — expand using TASK-0020's inventory once
  it lands, don't wait for it to start Tier 1):
  - **Tier 1 (presence):** toolbar target dropdown, PDB id/chain inputs,
    "Find & visualize" button, 3D viewer container, Structure Intelligence
    panel, GNM panel + its mode selector, Compare/Compute-shift controls,
    Export PDB button. Assert existence + basic visibility after static
    load — no clicks, no network beyond the static asset fetch.
  - **Tier 2 (isolated functionality):** with `backend` calls intercepted
    (Playwright `page.route` returning canned JSON), verify: GNM mode
    selector swaps the visible chart; "Complete apo" toggle flips its own
    state; color-by selector (chain/flexibility/GNM term) changes the
    active option; collapsible "how to read these values" guides
    expand/collapse. Each test supplies its own minimal canned response —
    no real PDB fetch.
  - **Tier 3 (intent / small chains), real backend:** benchmark-target
    selection populates PDB id + chain inputs and confirms **no**
    `POST /api/load` fires until "Find & visualize" is clicked (locks in
    the documented 2026-06-28 fix); clicking "Find & visualize" fires
    exactly one `POST /api/load` with the expected body and the response
    populates the summary fields; "Find holo" populates the holo picker
    from `GET /api/holo-finder`.
  - **Tier 4 (E2E process), real backend + network:** the full golden path
    — pick KRAS_G12C → visualize → confirm 3D viewer/Structure
    Intelligence/GNM panel all populate with non-empty real data → Compare
    against its known holo → Export PDB succeeds.
- Out Of Scope:
  - backend API correctness itself (TASK-0021 covers that independently —
    Tier 3/4 here treat the API as a dependency, not a thing they verify)
  - pixel-perfect / WebGL canvas visual regression (assert DOM/data-model
    state, not rendered 3Dmol.js pixels)
  - fixing any bug uncovered along the way — file a follow-up task instead
  - exhaustively covering every control in ARCHITECTURE.md's change log at
    every tier immediately — start with the seed list above (the controls
    that gate the golden path + the one documented regression-prone
    behavior), let TASK-0020's inventory and TASK-0023's scope-creep
    review decide which additional controls earn a dedicated test versus
    which are low-traffic enough to skip (explicit YAGNI: don't
    combinatorially test every toggle before knowing which ones matter)
- Constraints And Invariants:
  - no framework/build-step added to `frontend/` itself — tests live
    entirely in `tests/playwright/ui/`, driving the shipped vanilla-JS app
    as-is. (Corrected, TASK-0002 follow-up pass, 2026-07-04: this still
    read `tests/frontend/` — a leftover from before the shared-path rename
    with TASK-0021 below; every other path reference in this file already
    used `tests/playwright/ui/`.)
  - Tier 1/2 must not require a running real backend or network access —
    that's the point of the tier split (fast, always-runnable layer).
    Tier 3/4 do require it, same as TASK-0021/the prior single-suite plan.
  - keep the four tiers in separate files/directories
    (`tests/playwright/ui/tier1_presence/`, `tier2_functionality/`,
    `tier3_intent/`, `tier4_process/`) so a failure's tier is obvious from
    the path alone, not just from reading the assertion.
- Planned Validation: each tier green independently; deliberately break one
  thing per tier (rename a DOM id for Tier 1, break a client-side toggle
  handler for Tier 2, change a request param name for Tier 3, break a
  cross-panel dependency for Tier 4) and confirm only the expected tier(s)
  fail — this proves the tiers are actually decoupled, not just four
  folders running the same kind of test.

## In Progress

None

## TODO

- [x] Choose the headless-browser tool: **Playwright**, per direct user
      instruction (2026-07-04) — no build step, native request-interception
      for Tier 2, one tool for all four tiers, and shared with TASK-0021's
      API-request tests.
- [ ] Scaffold `tests/playwright/ui/` with the four-tier directory split,
      reusing the shared `playwright.config` (see TASK-0021 — whichever
      task lands first creates it) and a shared fixture for launching the
      app (Tier 1/2: static file serve is enough; Tier 3/4: real
      `uvicorn backend.main:app`).
- [ ] Implement Tier 1 (presence) for the seed control list — cheapest,
      do first, immediately useful even before Tiers 2-4 exist.
- [ ] Implement Tier 2 (isolated functionality) using route interception
      for the seed behaviors listed.
- [ ] Implement Tier 3 (intent/small chains) against the real backend for
      the seed behaviors listed, including the auto-extraction-on-select
      regression lock.
- [ ] Implement Tier 4 (E2E process) as the full golden path.
- [ ] Run the four deliberate-breakage checks (Planned Validation) and
      confirm tier isolation; revert the breaks.
- [ ] Document how to run each tier locally in `SOFTWARE.md` §9 (append).
- [ ] Cross-check the seed list against TASK-0020's inventory once it
      lands; add tests for anything load-bearing it surfaces that this
      seed list missed.

## Dependency

- TASK-0020 (Product intent inventory) — expands the seed list per tier;
  not a hard blocker, Tier 1 in particular can start immediately.
- Loosely related to TASK-0021 (backend API tests) — Tier 3/4 here treat
  that API as a trusted dependency rather than re-verifying it.

## Open Questions

- Tool choice resolved (Playwright) — see Context update above.
- Does CI exist at all for this repo (only `render.yaml` found, no
  `.github/workflows/` as of this session)? If not, note as a separate,
  larger gap — which tiers run pre-commit vs. only on-demand is a CI
  question this task shouldn't have to solve unilaterally.
- Should Tier 2's canned JSON fixtures be hand-written per test or
  generated once from a real Tier-3/4 run against a benchmark target (a
  "record once, replay for Tier 2" approach)? Recommend hand-written
  minimal fixtures to start — generating from real responses risks
  baking in incidental fields as if they were contractual; revisit only
  if hand-writing becomes a maintenance burden.

## Done

(not yet)
