# TASK-0039 `clean.py` alt-loc handling always picks `'A'`, never "highest occupancy"

## Context

- ID: TASK-0039
- Title: `CleanResult`'s class docstring promises "only the 'A' alt-loc
  (or highest occupancy) is kept"; the code unconditionally selects
  `altloc _ A` with no occupancy comparison at all
- Status: Done
- Owner: Implementer
- Source: review of all `Bartosz`/`bchmura`-authored commits, 2026-07-05
  session — Medium-severity finding #3
- Scope: `__WORK_IN_PROGRESS__/src/allostery/clean.py::clean`, the
  alt-loc-handling block

## ⚠️ Before implementing

**Do a short review before writing the occupancy-comparison logic** —
confirm ProDy actually exposes per-atom occupancy alongside altloc labels
on the same selection (`getOccupancies()` or similar) so the fallback is
implementable without a second parse pass, and check whether any of the
current benchmark targets (`systems.py`'s KRAS_G12C/BCR_ABL1/etc.) even
*have* a non-`'A'`-majority alt-loc case today — if none do, this is a
correctness gap with no current benchmark impact, which changes how
urgently it needs a real test fixture (may need a synthetic/mocked one).

## Intent Contract

- Outcome: the alt-loc selection genuinely picks the highest-occupancy
  conformer, falling back to `'A'` only when occupancies are equal or
  unavailable — matching the docstring's stated guarantee — or the
  docstring is corrected to say plainly "always keeps altloc 'A'" if that
  turns out to be an intentional simplification.
- In Scope:
  - per residue with multiple alt-locs, compare total/mean occupancy
    across labels present and select the highest; only default to `'A'`
    as a tiebreak or when occupancy data is unavailable.
  - flag (in `warn_list`) any residue where the kept alt-loc is NOT
    `'A'`, so a downstream reader can see when the fallback path
    actually fired.
- Out Of Scope: broader alt-loc semantics (partial-occupancy blending,
  multi-conformer output) — this task only fixes the selection rule.
- Constraints And Invariants: must not change behavior for any structure
  where `'A'` genuinely is the majority conformer (the common case) —
  verify against at least one current benchmark target with known
  alt-locs to confirm no regression.
- Planned Validation: a synthetic/mocked case where a non-`'A'` label has
  higher occupancy, confirming it's selected and flagged; a real
  benchmark-target smoke test confirming unchanged output where `'A'` is
  already the correct majority conformer.

## TODO

- [x] Confirm ProDy's occupancy API is usable alongside altloc selection.
- [x] Implement highest-occupancy selection with `'A'` as tiebreak/fallback.
- [x] Add the `warn_list` flag for non-`'A'` selections.
- [x] Test both the regression case (real target) and the new-behavior
      case (synthetic/mocked).

## Dependency

- None.

## Open Questions

- Does any currently-verified benchmark target actually exercise this
  path today? If not, this is latent (no live impact yet) rather than an
  active data-quality bug — worth noting in `Done` either way so the
  severity is honestly recorded.
  **Answered — yes, live, on the register's own CARDIAC_MYOSIN `holo_pdb`
  (8QYR).** See Done section.

## Done

**2026-08-24.** Implemented, tested against a real live case (not only
synthetic), zero regressions on the full suite (1256 passed).

**Pre-implementation review found a deeper root cause than this task's
own filing anticipated.** ProDy's `parsePDB()` default is `altloc="A"`
— it silently drops every non-`'A'` alt-loc record **at parse time**,
before `clean()`'s own selection code ever runs. `getOccupancies()` is
real and usable (confirmed directly), but the occupancy-comparison logic
this task asks for was always going to be dead code without first
switching to `parsePDB(pdb_id, altloc="all", ...)`, which keeps every
alt-loc as a distinct atom record in one coordinate set (confirmed:
`numAtoms()` for 8QYR rises from 6222 to 6258 once all three of its
labels — A/B/C — are retained instead of only A).

**Surveyed all 29 PDB IDs currently wired into `targets.yaml` before
writing anything** (`scripts/task0039_altloc_survey.py`, real RCSB
fetches, not assumed): under ProDy's real default, only 4/29 even
*appeared* to have alt-locs, and all 4 showed only label `'A'` — because
the true B/C data was already gone by that point. Re-surveyed with
`altloc="all"`: **5/29 genuinely have alt-loc conformers** (1SUG, 1T49,
5MO4, 8QYR + one more), and **8QYR — this register's own CARDIAC_MYOSIN
`holo_pdb` — has a real, live, currently-active case**: chain B residue
616's Cα atom has three conformers, occupancies A=0.25, B=0.25, **C=0.50**
— the old code kept A (a minority conformer, tied for least-populated)
and silently discarded C (the true majority conformer, double A's
population). Checked directly whether this residue is load-bearing for
any currently-published number: it is **not** one of CARDIAC_MYOSIN's
own consensus/core pocket-label residues (120/146/163/164/167/168/170/
666/710-713/717/721/722) — so no headline pocket-membership call
changes — but it was, until this fix, a silently wrong Cα coordinate
feeding this target's own network-topology machinery (GNM/ANM
eigendecomposition runs over every residue, not only labeled-pocket
ones), with zero indication anywhere that data was being dropped.

**Fix** (`allostery/clean.py::clean`): `parsePDB(..., altloc="all")`;
per-`(chain, resnum)` group, compare mean occupancy across whichever
labels are present, select the highest (`'A'` as the explicit tiebreak
and NaN-occupancy fallback, matching this task's own Constraint), apply
via integer-index selection (`struct[np.where(keep_mask)[0]]` — ProDy's
`.select()` string syntax can't express a per-residue-varying winning
label; confirmed boolean-array indexing itself doesn't work on
`AtomGroup`, integer arrays do). Two `warn_list` entries: one whenever
any alt-loc is detected at all (matching the prior behavior's own
warning), and a second, new one naming exactly which residues kept a
non-`'A'` conformer — the flag this task's own In Scope asked for.

**Validated, not assumed**: `tests/test_clean.py::TestAltlocHighestOccupancy`
(4 new tests) — the 8QYR/B:616 case reproduces the raw PDB file's own
recorded coordinate for the C conformer exactly (`abs=1e-3`) and is
correctly flagged; exactly 1 non-`'A'` residue is flagged for 8QYR (not
0, not all 3 of its multi-altloc residues — guards against
over-flagging); 5MO4 (real alt-locs present, `'A'` genuinely correct)
produces zero spurious non-`'A'` flags — the regression case; 4OBE (no
alt-locs at all) is completely unaffected, same residue count (169) as
before. Full suite re-run after the change: **1256 passed, 1 skipped,
8 xfailed, 0 failed** — no regression anywhere in the pipeline from
switching the parse mode.

**Not done, and why**: the fifth PDB with real alt-locs (found by the
survey but not named above, no non-`'A'`-wins residue) was not
individually spot-checked beyond the automated survey's own comparison —
the survey script itself is the validation for that case, not a second
manual check. Whether residue 616's corrected coordinate measurably
moves any *currently unpublished* observable computed on CARDIAC_MYOSIN's
holo structure was not tested (out of this task's own Out Of Scope,
which is the selection rule only, not downstream impact analysis).
