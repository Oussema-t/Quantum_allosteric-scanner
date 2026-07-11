# TASK-0032 Escape RCSB-sourced strings before injecting into frontend HTML

## Context

- ID: TASK-0032
- Title: `frontend/app.js::renderStructInfo` (and similar) build HTML via
  string interpolation of RCSB-sourced fields (structure titles, ligand
  names/codes, chain ids) without escaping
- Status: Done
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

## In Progress

Call-site enumeration (all 17 `innerHTML` assignments in `frontend/app.js`,
grep-confirmed exhaustive):

- **Escaped** (RCSB-sourced, now wrapped in the new `escapeHtml` helper):
  `renderStructInfo`: `comp.holo`, `comp.filled[].resname`, `intel.pdb_id`,
  `s.method`, `intel.chains[].chain` (both the summary-card join and the
  per-row table), `s.title`, `ligs[].code`/`.category`/`.name`,
  `missing_residues[].resname`/`.chain`. `render3DCompare`'s and
  `render3D`'s `viewcaption`: `d.apo_pdb`/`d.holo_pdb`/`d.apo_chain`/
  `d.holo_chain`/`d.drug_code`, `data.pdb_id`/`data.chains`.
- **Left as-is, confirmed safe** — internal/backend-computed, not
  RCSB-sourced free text: `analysis.labels[k]` (hardcoded in
  `backend/analysis.py::TERMS`), `comp.filled[].source` (fixed vocabulary,
  confirmed in `backend/discovery.py` — `"holo"`/`"interpolated..."`),
  `seedVerdictBadge`'s verdict enum, `sr.mechanism`/`sr.topology` (backend
  classification enums), all `.length`/numeric fields, residue numbers
  (`resnum`, always integer). `structureRole()` always returns one of 3
  hardcoded strings, never echoes its `pdbId` argument — safe by
  construction, confirmed by reading its body.
- **Not innerHTML at all, confirmed already safe**: the target-select and
  holo-select dropdowns (`addOption()` uses `option.textContent`, not
  innerHTML); all `setStatus`/`setCompareStatus`/`setHoloStatus` messages
  (`el.textContent`, not innerHTML) even though several interpolate
  `data.pdb_id`/`d.apo_chain`/etc.
- Resolution (`s.resolution`) left unwrapped — used only in an arithmetic
  string-concat ternary (`s.resolution ? s.resolution + " Å" : "—"`), not
  a free-text field like the others.

## TODO

- [x] Enumerate all `innerHTML` call sites touching API-sourced fields
      (see the review callout above).
- [x] Add `escapeHtml` helper.
- [x] Apply at the confirmed call sites only.
- [x] Manual smoke test on a real benchmark target + one synthetic
      adversarial-string test — see Done.

## Dependency

- None.

## Open Questions

- None yet — surface after the call-site enumeration.

## Done

- `escapeHtml(s)` added to `frontend/app.js` (standard 5-character
  entity-replace: `& < > " '`, null-safe). Applied at every RCSB-sourced
  `innerHTML` interpolation point identified in the `In Progress`
  enumeration above.
- **Validation environment note**: this sandbox has no browser or JS
  runtime (`node`, `chromium`/`chromium-cli` all absent, checked
  directly) and no project `run` skill exists for this app yet — a real
  in-browser visual check was not possible. Validated what was possible
  instead, documented here rather than silently skipped:
  - Started `uvicorn backend.main:app` locally, hit the real endpoints
    `app.js` calls (`/api/load`, `/api/structure`) for KRAS_G12C
    (4OBE/chain A). Confirmed the served `/app.js` is byte-identical to
    the edited source (no stale-cache risk). Confirmed `frontend/app.js`
    has balanced `{}`/`()` and an even backtick count (no template-literal
    corruption from the edits).
  - **Real data already exercises the escape path**: `/api/structure`'s
    ligand name for 4OBE is `GUANOSINE-5'-DIPHOSPHATE` — contains an
    apostrophe, one of the five escaped characters. Confirms the "must
    render identically for normal RCSB data" requirement isn't just
    theoretical: an HTML entity (`&#39;`) and its literal character render
    identically in a browser, so this is a real, non-hypothetical
    same-target regression check, just not one this sandbox could render
    and screenshot.
  - **Adversarial-string check**: ported `escapeHtml`'s exact algorithm
    (same 5 replacements, same order) to Python and ran it against
    `<script>alert(1)</script> & "quoted" 'single'` — fully neutralized
    (`&lt;script&gt;...`), and against `&<>` specifically to confirm
    escaping `&` first doesn't double-escape the entities the later
    replacements produce. Also verified against the real
    `GUANOSINE-5'-DIPHOSPHATE` string. This validates the algorithm, not a
    live DOM render — flagged explicitly, not claimed as a full UI test.
  - Recommend `/run-skill-generator` for this repo per the `run` skill's
    own guidance (no project skill existed to launch/drive this app; a
    real browser check had to be worked around instead of run) — not done
    here, out of this task's scope.
- No visual/response-shape change for any normal (non-adversarial) RCSB
  data — confirmed via the identical-braces/served-file checks and the
  entity-renders-as-character property, not by pixel comparison.
