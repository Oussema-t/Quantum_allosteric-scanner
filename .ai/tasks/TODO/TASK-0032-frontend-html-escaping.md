# TASK-0032 Escape RCSB-sourced strings before injecting into frontend HTML

## Context

- ID: TASK-0032
- Title: `frontend/app.js::renderStructInfo` (and similar) build HTML via
  string interpolation of RCSB-sourced fields (structure titles, ligand
  names/codes, chain ids) without escaping
- Status: TODO
- Owner: Implementer
- Source: review of all `Oussema-t`-authored commits, 2026-07-05 session —
  High-severity finding #2
- Scope: `frontend/app.js` — `renderStructInfo`, and any other function
  building `innerHTML` from `intel`/`LAST.view`/API-response fields

## ⚠️ Before implementing

**Do a short review before writing the fix**, specifically: enumerate every
`innerHTML =` / `+=` call site in `app.js` that includes a field sourced
from an API response (not a hardcoded string), and confirm which values
are genuinely externally-controlled (RCSB title/ligand-name/resname
fields) vs. purely internal (numbers, our own labels) — don't blanket-fix
call sites that don't need it, and don't miss one that does.

## Intent Contract

- Outcome: no RCSB-sourced string (structure title, ligand chemical name,
  resname, chain id, etc.) reaches `innerHTML` unescaped.
- In Scope:
  - a small `escapeHtml(s)` helper (standard `textContent`-roundtrip or
    equivalent) applied at each call site identified in the review above.
  - primary targets per the initial read: `renderStructInfo`'s `s.title`,
    `l.name`, `l.code`; chart/legend titles built from `analysis.labels`
    if those ever originate server-side from RCSB data rather than this
    app's own hardcoded label dict (`V_B`/`V_T`/etc. labels are
    hardcoded in `backend/analysis.py::TERMS` — confirm those are safe to
    leave as-is, and don't over-apply escaping to internal-only strings).
- Out Of Scope: a full templating-library migration — this is a targeted
  escaping fix, not a rewrite of the rendering approach.
- Constraints And Invariants:
  - exploitability here is low (RCSB is a curated, non-attacker-controlled
    data source for this app's typical usage) — treat this as
    defense-in-depth, not an active incident; don't let it justify a large
    refactor.
  - must not change what's visually rendered for any current benchmark
    target (KRAS_G12C, BCR_ABL1, etc.) — escaping should be invisible for
    all normal RCSB data, only change behavior for the (currently absent)
    adversarial case.
- Planned Validation: load a benchmark target (e.g. KRAS_G12C) before and
  after the change, confirm the structure-intel panel renders identically;
  construct one synthetic test case with an HTML-special character in a
  mocked title/ligand-name field and confirm it now renders as literal
  text instead of being interpreted as markup.

## TODO

- [ ] Enumerate all `innerHTML` call sites touching API-sourced fields
      (see the review callout above).
- [ ] Add `escapeHtml` helper.
- [ ] Apply at the confirmed call sites only.
- [ ] Manual smoke test on a real benchmark target + one synthetic
      adversarial-string test.

## Dependency

- None.

## Open Questions

- None yet — surface after the call-site enumeration.

## Done

(not yet)
