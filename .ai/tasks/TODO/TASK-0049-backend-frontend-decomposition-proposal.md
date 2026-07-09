# TASK-0049 Target decomposition proposal — `backend/` + `frontend/` into smaller, single-concern, importable modules

## Context

- ID: TASK-0049
- Title: Propose (not yet execute) a target file/module structure that
  splits `backend/`'s largest files and `frontend/app.js` into smaller,
  single-concern, independently testable/importable units — ahead of a
  repository-standards meeting where an external expert thread's review
  of `main`/`bartosz`/`scaffold` will also be discussed
- Status: TODO (this is the proposal; execution is explicitly a separate,
  later task per the user's own framing — "before we DO cut it up into
  pieces")
- Owner: Architect/Planner
- Claimed By: Architect/Planner (this thread)
- Claimed At: 2026-07-09 20:49
- Source: user request, 2026-07-09 session — wants backend/frontend split
  into smaller functions with clear test coverage and proper import
  structure, prepared *before* an upcoming repository-standards meeting so
  it can be checked against an external expert review of all three
  branches. Explicit decision this session: draft now rather than wait for
  that review (can diff against it at the meeting), scope covers both
  `backend/` and `frontend/`.
- Crit Ref: directly extends evidence [[TASK-0018]] already gathered
  (its "Granularity is a real, not superficial, difference" finding —
  `backend/analysis.py` mixes JSON-shaping with physics in one file vs.
  the research scaffold's ~8 single-concern files) and
  [[TASK-0034]] (`rcsb.py`/`rcsb_extract.py` overlap, backend-internal
  instance of the same duplication pattern).

## Intent Contract

- Outcome: a concrete target file tree for `backend/` and `frontend/`,
  with an explicit function-level mapping table (current location ->
  target location) for every function in the files being split, ready to
  (a) compare against the external expert review at the meeting, and (b)
  hand to an Implementer as a mechanical move once approved.
- In Scope:
  - inventory every `backend/*.py` file's current size and top-level
    function list (done below, from the live tree, not guessed)
  - inventory `frontend/app.js`'s ~60 functions and group them by feature
    panel (cross-checked against `.ai/reviews/PRODUCT_INTENT_MAP.md`'s
    existing panel grouping from TASK-0020, not re-derived independently)
  - propose target packages/modules for the files that are actually large
    or actually mixing concerns; explicitly say "leave as-is" for files
    that are already single-concern and modest in size
  - a stated **provenance-comment convention** for whoever executes the
    actual move: each relocated function/block gets a one-line comment at
    its new location, e.g. `# moved from backend/analysis.py:139-236
    (TASK-0049), unchanged` — so the eventual review/cleanup pass can
    trace every piece back to where it came from without re-diffing git
    history
  - confirm the split is achievable with **zero call-site changes** in
    `backend/main.py` (via package `__init__.py` re-exports) and **zero
    build step** in `frontend/` (via native `<script type="module">`)
- Out Of Scope:
  - **actually moving any code.** This task produces the plan only. A
    follow-up task (or several, one per package, so multiple Implementers
    can take them in parallel — matches today's "several parallel
    Implementer agents" capacity) executes the move once the plan is
    approved at the meeting.
  - any behavior change, renaming of public function signatures, or
    "while I'm in there" cleanup — the eventual move should be a
    mechanical relocation first (provenance-commented), with any real
    refactor (dedup, renaming, style fixes) as an explicit separate pass
    after, same split this repo already uses for TASK-0018/TASK-0030-style
    work (decide/record vs. execute are different tasks).
  - resolving TASK-0018's backend-vs-`allostery` convergence question —
    this proposal is orthogonal to it: the new `backend/analysis/` package
    boundaries below work identically whether TASK-0018 eventually
    decides `backend` should call into `allostery`'s physics or keep its
    own — see the note under "backend/analysis/" below.
  - test-coverage additions themselves (the user's stated end goal
    includes "clear test coverage" — that's real, but is naturally scoped
    per-module once each new file exists with a name and boundary; this
    task's job is to give each future test file something coherent to
    target, not write the tests).
- Constraints And Invariants:
  - `main.py`'s existing `from .analysis import (...)`,
    `from .rcsb import (...)`, etc. must keep working unchanged — turning
    a module into a package with an `__init__.py` that re-exports its
    public names is transparent to every caller (verified: `main.py`'s
    imports are all `from .X import name`, never `import X` +
    attribute access, so this pattern is safe).
  - CLAUDE.md convention 4 (ADD-only, don't break response shapes) and
    convention 7 (docs updated in the same commit as the change) apply to
    whoever executes this later, not to this proposal itself.
  - `frontend/`'s no-build-step constraint (CLAUDE.md: "vanilla HTML/CSS/
    JS, no build step") is preserved — the proposal below uses native
    ES modules (`<script type="module">`, `import`/`export`), which every
    evergreen browser supports with zero bundler/tooling.
- Acceptance Scenarios:
  - Given this document, when a reviewer (internal or the external expert
    thread) reads it, then every current top-level function in the files
    being split has a named target location, and every file *not* being
    split has a one-line reason why not.
  - Given the target tree, when `main.py` is re-read against it, then no
    import line in `main.py` needs to change.
- Planned Validation: not applicable in the usual sense (no code changes
  here) — the check is "does the mapping table below account for 100% of
  the functions found by `grep -n '^def |^class ' backend/analysis.py
  backend/rcsb.py backend/rcsb_extract.py` and the ~60 functions in
  `frontend/app.js`" — yes, verified while drafting (see tables below).

## Current-state inventory (from the live tree, 2026-07-09)

```
backend/__init__.py         1 line
backend/geometry.py        30 lines   -- already single-concern (Kabsch), leave as-is
backend/data_layer.py      89 lines   -- already single-concern, leave as-is
backend/compare.py        120 lines   -- already single-concern, leave as-is
backend/pipeline.py       166 lines   -- already single-concern (orchestrator), leave as-is
backend/active_site.py    187 lines   -- already single-concern, leave as-is
backend/systems.py        228 lines   -- already single-concern (targets registry), leave as-is
backend/discovery.py      277 lines   -- mixed: search/discovery + apo-completion, split (below)
backend/rcsb_extract.py   303 lines   -- mixed: 3-backend atom-parsing fallback + fetch orchestration, split (below)
backend/main.py           335 lines   -- FastAPI app + 11 routes inline; noted, not split in this pass (see Open Questions)
backend/rcsb.py           341 lines   -- mixed: ligand classification + structure/site intel, split (below)
backend/analysis.py       646 lines   -- mixed: GNM potentials + CTQW/quantum-seed + connectivity/morph, split (below)

frontend/index.html       271 lines   -- one change needed: <script src="app.js"> -> <script type="module" src="app.js">
frontend/app.js          1359 lines   -- ~60 functions, zero module structure, all implicit globals; split (below)
```

Files not listed above (`backend/test_geometry.py`, `__WORK_IN_PROGRESS__/*`)
are out of scope — this task is `backend/`+`frontend/` only.

## Proposed target structure — `backend/`

### `backend/analysis.py` (646 lines) -> `backend/analysis/` package

Three genuinely distinct physics concerns currently live in one file. The
split below mirrors `SOFTWARE.md`'s own section numbers (§5b, §5f-5h, §8d)
— it does not invent new boundaries, it names the ones already documented.

| Current function (line, `backend/analysis.py`) | Target file |
|---|---|
| `_z`, `_coordination`, `gnm_context`, `V_Bfactor`, `V_terminal`, `V_rigidity`, `V_covariance`, `V_modeparticipation`, `site_potentials` (25-137) | `backend/analysis/gnm.py` (§5b core GNM + site potentials) |
| `_ctqw_build_H`, `_average_mixing_matrix`, `_abs_coupling`, `_slow_participation`, `_site_descriptors_z`, `_site_descriptors_raw`, `_bootstrap_floor`, `_raw_shift`, `quantum_seed_readiness`, `seed_readiness_shift` (139-393) | `backend/analysis/quantum_seed.py` (§5f/§5g/§5h CTQW-flavored quantum-seed readiness) |
| `_dcc`, `connectivity_change`, `_coords_on`, `_auto_intermediates`, `morph_frames`, `site_potential_shift` (394-646) | `backend/analysis/connectivity.py` (§8d connectivity-change, morph, presentation-facing shift) |
| (new) | `backend/analysis/__init__.py` — re-exports every name `main.py` currently imports from `.analysis`, so `from .analysis import (...)` in `main.py` needs zero changes |

**Note on TASK-0018:** this split is orthogonal to that task's convergence
question. If TASK-0018 eventually decides `gnm.py`/`quantum_seed.py`
should call into `__WORK_IN_PROGRESS__/src/allostery`'s `hamiltonians.py`/
`potentials.py` instead of keeping parallel implementations, that becomes
an internal change *inside* these new files — the package boundary
proposed here doesn't need to be redone either way.

### `backend/rcsb.py` (341 lines) -> `backend/rcsb/` package

| Current function | Target file |
|---|---|
| `_get_json` (70-85) | `backend/rcsb/http.py` (shared RCSB HTTP helper) |
| `_parse_formula`, `_chem_comp_record`, `chem_comp_name`, `_is_aliphatic_additive`, `classify_ligand` (86-165) | `backend/rcsb/ligands.py` |
| `entry_summary`, `parse_missing_residues`, `_iter_hetero`, `ligands_and_sites`, `chain_summary`, `chain_resnums`, `drug_bearing_chain`, `structure_intel` (166-341) | `backend/rcsb/structure_intel.py` |
| (new) | `backend/rcsb/__init__.py` — re-exports `structure_intel`, `ligands_and_sites` (the two names `main.py` imports today) |

### `backend/rcsb_extract.py` (303 lines) -> `backend/rcsb_extract/` package

| Current function | Target file |
|---|---|
| `_download_cif`, `_atoms_biotite`, `_atoms_gemmi`, `_atoms_biopython`, `_load_atoms` (50-143) | `backend/rcsb_extract/atom_io.py` (the 3-backend parser fallback chain — cross-link [[TASK-0034]], which already flags this file's overlap with `data_layer.py`'s own fetch logic; resolve that overlap in TASK-0034, not here) |
| `fetch_structure`, `_ligand_name`, `fetch_ligand`, `_seq_identity`, `fetch_apo_holo`, `fetch_intermediates` (144-303) | `backend/rcsb_extract/fetch.py` |
| (new) | `backend/rcsb_extract/__init__.py` — re-exports whatever public names current callers use (confirm exact set at execution time; not all of these may be called from `main.py` directly) |

### `backend/discovery.py` (277 lines) -> `backend/discovery/` package

| Current function | Target file |
|---|---|
| `get_uniprot` (32-59) | `backend/discovery/uniprot.py` |
| `_search_entries_by_uniprot`, `_entry_drug_info`, `same_protein_entries`, `find_holo_candidates` (60-165) | `backend/discovery/holo_search.py` |
| `complete_apo` (166-277) | `backend/discovery/complete_apo.py` (the Kabsch-completion logic — already imports `backend/geometry.py` per TASK-0030, keep that import unchanged) |
| (new) | `backend/discovery/__init__.py` — re-exports `find_holo_candidates` (the name `main.py` imports) |

### Left as-is (already single-concern, modest size)

`geometry.py`, `data_layer.py`, `compare.py`, `pipeline.py`,
`active_site.py`, `systems.py` — no proposed change. Splitting further
would be fragmentation for its own sake, which this scaffold's own
conventions warn against.

### `backend/main.py` — not split in this pass

11 routes + auth middleware in 335 lines. A route-file split (FastAPI
`APIRouter` per concern: data-foundation routes vs. analysis routes vs.
comparison routes) is a reasonable future step but is a *different* axis
(HTTP layer, not physics/data layer) from everything above — left as an
Open Question below rather than folded into this proposal, so this
document stays reviewable as one coherent story.

## Proposed target structure — `frontend/`

`index.html` change (one line): `<script src="app.js"></script>` ->
`<script type="module" src="app.js"></script>`. Native ES modules, no
bundler, no build step — every evergreen browser (any 2026 grading
environment) supports this.

Grouping below reuses `.ai/reviews/PRODUCT_INTENT_MAP.md`'s existing
panel breakdown (TASK-0020) rather than re-deriving one:

| Panel (per PRODUCT_INTENT_MAP.md) | Current functions (`app.js`) | Target file |
|---|---|---|
| Bootstrap / target selection | `init`, `addOption`, `onTargetChange`, `setHoloAvailability`, `currentHolo`, `loadedIsHolo`, `selfCompareError`, `findHolo`, `setHoloStatus`, `loadAndVisualize`, `setStatus` | `frontend/modules/target-select.js` |
| Structure intelligence + 3D viewer | `showActiveSiteNote`, `loadDrugSite`, `loadIntel`, `structureRole`, `render3D`, `flexColor`, `renderStructInfo` | `frontend/modules/structure-intel.js` |
| Compare (apo/holo) | `setCompareStatus`, `compareApoHolo`, `render3DCompare`, `dispColor`, `divergeColor` | `frontend/modules/compare.js` |
| GNM site-potential analysis panel | `renderAnalysis`, `downloadFile`, `exportCSV`, `exportJSON`, `exportPDB`, `exportPNG`, `computeShift`, `applyAnalysisMode`, `renderEnrichmentBar`, `renderSpectrum`, `makeProfileChart`, `renderStructuralCharts`, `renderDrugIntersection`, `setShiftNote` | `frontend/modules/gnm-analysis.js` |
| Connectivity-change panel (core) | `computeConnectivityChange`, `setConnStatus`, `renderConnSummary`, `seedVerdictBadge`, `seedShiftTable`, `renderSeedReadiness`, `landmarkShapes`, `connHeatmap`, `renderConnHeatmaps`, `parseRanges`, `resolveRegion`, `subsetConn`, `applyConnRegion` | `frontend/modules/connectivity.js` |
| Connectivity-change panel (graph/morph animation) | `graphMotionMode`, `subsetFrames`, `setupGraphMorph`, `graphFrameData`, `graphFrame`, `startGraph`, `stopGraph`, `applyGraphMotion`, `matAbsPct`, `couplingMatrix`, `setupMorph`, `morphFrame`, `startMorph`, `stopMorph` | `frontend/modules/graph-morph.js` |
| (new) | — | `app.js` becomes a thin orchestrator: imports from `modules/*`, wires up DOM event listeners, no business logic of its own |

**Side benefit worth flagging:** the graph-morph cluster is exactly what
[[TASK-0023]] flagged as the strongest scope-creep candidate (heaviest
recent engineering effort, no stated rubric link). Isolating it into its
own module now makes it a clean, low-risk deletion later if TASK-0023's
recommendation lands on "remove" — no need to go hunting through a
1359-line file to excise it.

## Provenance-comment convention (for whoever executes this later)

When the actual move happens, each relocated function gets a one-line
header comment at its new location naming where it came from, e.g.:

```python
# moved from backend/analysis.py:139-236 (TASK-0049), unchanged
def _ctqw_build_H(coords, R_c=8.0, r0=7.0):
    ...
```

```js
// moved from frontend/app.js:1161-1198 (TASK-0049), unchanged
function setupGraphMorph(d, activeSet, drugSet) { ... }
```

This is deliberately *not* a `git blame`-replacement — it's a fast, in-file
way for a reviewer to confirm "this code is relocated, not rewritten"
without leaving the editor, which matters most right at the moment of the
split, before any follow-on cleanup commit lands.

## In Progress

None

## TODO

- [x] Inventory every `backend/*.py` file's size and function list from
      the live tree.
- [x] Inventory `frontend/app.js`'s functions, grouped by panel (reused
      TASK-0020's `PRODUCT_INTENT_MAP.md` grouping rather than
      re-deriving one).
- [x] Confirm the package-`__init__.py` re-export pattern requires zero
      `main.py` import changes (checked `main.py`'s actual import lines).
- [x] Confirm the frontend split needs zero build step (native ES
      modules via `type="module"`).
- [ ] Bring this proposal to the repository-standards meeting; diff it
      against the external expert thread's review of `main`/`bartosz`/
      `scaffold`.
- [ ] Once approved (with whatever changes come out of the meeting), file
      the execution task(s) — recommend one task per package/module
      cluster (e.g. `backend/analysis/` split, `backend/rcsb/` split,
      `frontend/modules/` split) so multiple Implementer agents can take
      them in parallel without touching the same files.

## Dependency

- [[TASK-0018]] (TODO, claimed by this thread, not yet started) —
  source of the granularity-gap evidence this proposal extends; not a
  blocking dependency (this proposal doesn't require TASK-0018 to resolve
  first, per the "orthogonal" note above), but the two should be read
  together.
- [[TASK-0034]] (TODO) — owns the `rcsb.py`/`rcsb_extract.py` overlap
  question; this proposal's `rcsb_extract/atom_io.py` boundary should be
  read alongside whatever TASK-0034 decides, not in isolation.
- [[TASK-0023]] (In Progress) — the graph-morph module boundary proposed
  above makes that task's scope-creep recommendation easier to act on
  later, whichever way it concludes.

## Open Questions

- **`main.py`'s route split** — left out of this pass (see "not split in
  this pass" above). Worth its own follow-up proposal if the meeting
  wants HTTP-layer decomposition too, but it's a different axis
  (FastAPI `APIRouter` per concern) from the physics/data-layer splits
  above and would only muddy this document's one story.
- **Test-file layout** — once these modules exist, where do their tests
  live? Recommend mirroring `__WORK_IN_PROGRESS__/tests/`'s existing
  one-file-per-module convention (e.g. `backend/tests/test_gnm.py`) rather
  than inventing a new layout, but this repo currently has no `backend/
  tests/` directory at all (only the one `backend/test_geometry.py` file
  next to its module) — worth deciding at the meeting whether backend
  tests move to a `backend/tests/` directory as part of this same pass.
- **External expert review** — not yet available to this thread; this
  proposal should be treated as a first draft to reconcile against it, not
  a final answer independent of it.

## Done

(not yet)
