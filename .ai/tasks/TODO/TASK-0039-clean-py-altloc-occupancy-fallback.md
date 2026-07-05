# TASK-0039 `clean.py` alt-loc handling always picks `'A'`, never "highest occupancy"

## Context

- ID: TASK-0039
- Title: `CleanResult`'s class docstring promises "only the 'A' alt-loc
  (or highest occupancy) is kept"; the code unconditionally selects
  `altloc _ A` with no occupancy comparison at all
- Status: TODO
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

- [ ] Confirm ProDy's occupancy API is usable alongside altloc selection.
- [ ] Implement highest-occupancy selection with `'A'` as tiebreak/fallback.
- [ ] Add the `warn_list` flag for non-`'A'` selections.
- [ ] Test both the regression case (real target) and the new-behavior
      case (synthetic/mocked).

## Dependency

- None.

## Open Questions

- Does any currently-verified benchmark target actually exercise this
  path today? If not, this is latent (no live impact yet) rather than an
  active data-quality bug — worth noting in `Done` either way so the
  severity is honestly recorded.

## Done

(not yet)
