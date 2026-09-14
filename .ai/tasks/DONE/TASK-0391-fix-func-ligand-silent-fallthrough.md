# TASK-0391 — Fix `func_ligand`'s silent fall-through on stale/incomplete codes

- Status: Done
- Owner: Implementer D
- Priority: High — Phase-2, explicitly deferred past the Phase-1 deadline
- Filed: 2026-09-13 by Implementer C
- Source: [[TASK-0386]] (naming task — this is its deferred fix)
- Related: [[TASK-0385]] (BCR-ABL1 #5 gatekeeper hit this defect produced), [[TASK-0278]]

## The defect, exactly

`allostery/labels.py::functional_indices` (~line 424) excludes active-site
contacts by looking up each `func_ligand` code against the input structure's own
`ligand_groups`:

```python
for code in (target_config.get("func_ligand") or []):
    ligand = next((g for g in ligand_groups if g.resname == code), None)
    if ligand is None:
        continue
```

If no code matches, the loop falls through silently to tier 2/tier 3 — **by
design**, per this function's own documented convention ("not resolvable is not
a failure"). That convention is correct for a target that legitimately has no
`func_ligand` (`func_ligand: []` is used deliberately elsewhere in
`targets.yaml`). It is wrong for a target that *has* a `func_ligand` entry which
simply doesn't match what's in *this particular* input structure — a data error,
not an absent-by-design case — and the function cannot currently tell the two
apart.

[[TASK-0386]] found two live instances:

| target | `func_ligand` | apo input's actual ligands | result |
|---|---|---|---|
| BCR_ABL1 | `["NIL"]` (holo-only, from 5MO4) | 1OPL: `MYR`, `P16` | zero matches — full fall-through |
| CARDIAC_MYOSIN | `["ADP","ATP"]` | 8QYP: `ADP`, `VO4`, `MG`, `M3L` | `ADP` matches, `VO4` (the transition-state mimic) does not — partial |

## Why this is worth fixing, not just naming

The submission's own audit standard — verify what a metric claims against what it
actually measures — applies to this instrument too. BCR-ABL1's #5 submitted
"allosteric" residue is the gatekeeper threonine (T315-equivalent), 4.2 Å from
the orthosteric ligand, because the exclusion that should have caught it never
ran. This is a mechanistic, fixable defect, not noise.

## Proposed direction (not committed to — pick one at pickup time)

1. **Warn, don't just continue.** When every code in `func_ligand` fails to
   match any `ligand_groups` entry, emit a warning (or a structured field on the
   return value) distinguishing "declared but absent from this structure" from
   "declared empty on purpose." Cheapest fix, changes no labels by itself —
   surfaces the BCR-ABL1 case immediately without changing CARDIAC_MYOSIN's
   partial-match case (still silent).
2. **Audit `func_ligand` against each target's actual apo/holo pair at config
   load time.** A `targets.yaml` linter that flags any `func_ligand` code with
   zero heavy atoms in the declared `apo_pdb` — would have caught both cases in
   [[TASK-0386]] before they shipped. Doesn't fix the runtime silence, but
   prevents the specific data error that triggers it.
3. **Fix the data**: correct `func_ligand` per target (BCR_ABL1 → include
   `MYR`/`P16` or derive from `apo_pdb`'s own ligands rather than the holo
   structure's; CARDIAC_MYOSIN → add `VO4`). Re-run every affected target's hit
   list, AUC, and connectivity matrix. **This is the option [[TASK-0386]]
   explicitly declined for Phase-1** (changes shipped numbers, no time to
   re-audit) — do this first when picking the task up post-deadline.

Options 1 and 2 are diagnostics; option 3 is the actual content fix and is
required before any of TASK-0386's flagged targets can be trusted again.

## Constraint

Do not silently re-run and re-ship new hit lists/matrices without a fresh,
disclosed audit pass — the exact failure mode this task exists to prevent.

## Done when

- `func_ligand` fully or partially failing to match the declared `apo_pdb` is
  detected — at config load, at label-computation time, or both — and surfaced,
  not silently absorbed.
- BCR_ABL1 and CARDIAC_MYOSIN's `func_ligand` entries are corrected (or a
  targets.yaml comment explains why they remain as-is, e.g. if the exclusion
  region is meant to be derived some other way).
- Every hit list / AUC / connectivity matrix touched by the fix is re-run and
  the change is disclosed against the Phase-1 shipped numbers, not silently
  overwritten.

## Done — 2026-09-14, Implementer D

**Scope decided at pickup, per explicit user instruction given this task's
own "Phase-2, explicitly deferred past the Phase-1 deadline" filing and its
Constraint against re-shipping numbers pre-deadline: options 1+2
(diagnostics) only. Option 3 (correct `func_ligand`, re-run, re-ship)
remains fully deferred — nothing here changes any shipped hit list, AUC, or
connectivity matrix.**

### A correction to this task's own premise, found while building the diagnostic

Before writing anything, re-verified [[TASK-0386]]'s root-cause claim
directly against the real pipeline (`allostery.labels.build_labels`) rather
than trusting it on its word — this project's own standing discipline. **The
claim that BCR_ABL1's tier-1 lookup "finds no match... and falls through
silently" is not quite right.** Empirically: `build_labels` on real
BCR_ABL1 data resolves `provenance == "func_ligand-contact:NIL"`, not a
fallback. NIL is present in the HOLO structure (`5MO4`) and reaches apo's
own index space via TASK-0217.001's cross-structure (Needleman-Wunsch)
heavy-atom translation. Tier 1 does not fall through; it succeeds, on
translated geometry. Root cause, confirmed directly: `apo.ligand_groups` is
**unconditionally empty for every target in this pipeline** (checked across
KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN/GLUCOKINASE) — apo cleaning never
extracts ligands at all, so `functional_indices` can never check contacts
against `1OPL`'s own, apo-native second inhibitor (`P16`) directly; P16 is
simply absent from `func_ligand`, so no tier ever considers it. The
**outcome** TASK-0385/0386 measured is unaffected and still real (verified
directly: of the 26 residues NIL's translated contact excludes, 337 and 340
are in, 338 — the shipped #5 hit — is not), but the **mechanism** is "the
declared `func_ligand` list omits a real ligand" (the same shape as
CARDIAC_MYOSIN's already-diagnosed VO4 case), not "declared code fails to
match anything." This matters for scoping a diagnostic correctly: a warning
that only fires "when tier 1 returns nothing" (this task's own original
option-1 framing) would have missed BCR_ABL1 entirely, since tier 1 does
return something. **Not corrected in any shipped submission file** (out of
scope); appended as a dated correction addendum to `targets.yaml`'s own
existing `func_ligand_note` for BCR_ABL1 (internal register documentation,
not a submitted file, changes no `func_ligand` value).

### Option 2 — config-time linter, `scripts/task0391_func_ligand_linter.py`

Reads each target's `apo_pdb`/`holo_pdb` directly via raw HETATM parsing
(not through the pipeline's own `ligand_groups`, which — per the finding
above — is empty for apo; this linter deliberately checks ground truth
independently of the path it audits) and cross-references against declared
`func_ligand` codes. Reports, per code: present in apo directly (OK) /
present in holo only (WARN — the BCR_ABL1 mechanism) / present nowhere
(FAIL — worse than either known case). Separately reports apo's own HETATM
codes not covered by any declared code, after an explicit, conservative
denylist of inert crystallisation additives (`GOL`, `EDO`, PEG variants,
`DMS`, `MPD`, `BME`, buffer ions, etc. — never metals or nucleotide-family
codes, which can be genuinely catalytic and must be judged, not silently
dropped).

**Run across all 15 targets in `targets.yaml`, not just the 2 TASK-0386
checked by hand.** Reproduces both known cases exactly (BCR_ABL1: `NIL`
WARN, `P16` undeclared; CARDIAC_MYOSIN: `VO4` undeclared) and **surfaces one
new, previously undocumented issue in the shipped Phase-1 cohort**:
CARDIAC_MYOSIN's declared `"ATP"` code is not present in either `8QYP` or
`8QYR`'s own HETATM records at all — dead weight in the declared list, a
different defect shape than the VO4 omission (does not change or explain
the VO4 finding). The other flagged targets (`ATCase`, `TAR_RECEPTOR`,
`GLYCOGEN_PHOSPHORYLASE`, `PFK`, `GROEL_SUBUNIT`, `HEMOGLOBIN`,
`CARDIAC_MYOSIN_TABLE1`) are outside [[TASK-0209]]'s own 7-target Phase-1
scoring cohort — reported for completeness since the linter runs
unconditionally, not flagged as submission-relevant. `PTP1B`/`CASPASE1`/
`CASPASE7` correctly report "empty, deliberate" (matches [[TASK-0216]]'s own
documented decision) — the linter does not false-positive on the
legitimate empty case. Read-only: writes only
`results/tasks/0391_func_ligand_linter/result.json`, changes no config.

### Option 1 — runtime warning, `allostery/labels.py::functional_indices`

Added one `warnings.warn(RuntimeWarning, ...)` at the exact point a tier-1
match is about to return via cross-structure-translated geometry
(`heavy_atom_coords is not None and len(heavy_atom_coords)`) — purely
additive: no return value, provenance string, or control flow changed.
Verified empirically it fires for **every** real tier-1 match in this
pipeline (KRAS_G12C's GDP included), not just the 2 known-bad targets —
expected and correct, given `apo.ligand_groups` is confirmed always empty:
every successful tier-1 match in this pipeline relies on holo-translated
geometry by construction, not a per-target anomaly. Two new tests added
(`test_cross_structure_match_warns`, `test_same_structure_match_does_not_
warn` — the latter a negative control using `warnings.simplefilter("error")`
to prove the warning is genuinely conditional on cross-structure
translation, not unconditional noise). Full `tests/test_labels.py`: 37
passed (was 35), 6 warnings (all expected, none new failures).

### Verified before and after

`pytest tests/test_labels.py tests/test_report.py -q` → 76 passed both
before and after the `labels.py` edit (re-run after, not just before, to
confirm the additive change introduced zero regressions). Full `pytest
tests/` run separately as a final check.

### Constraint honored

No `func_ligand` value changed in `targets.yaml`. No hit list, AUC, or
connectivity matrix re-run or re-shipped. The two `func_ligand_note` edits
are dated correction/addition addenda to existing internal documentation,
not changes to any submitted file or scored number.

### Left for the post-deadline pass (option 3, still owned by whoever picks it up next)

- Correct `BCR_ABL1`'s `func_ligand` (add `P16`, or derive exclusion from
  apo's own ligands directly rather than a hand-maintained list) and
  `CARDIAC_MYOSIN`'s (`VO4` in, `ATP` — now confirmed absent from both
  structures — reconsidered).
- The deeper architectural gap this task's diagnostics surfaced but did not
  fix: `apo.ligand_groups` being unconditionally empty means tier-1
  exclusion NEVER uses same-structure geometry for any target, not only the
  two already flagged — worth deciding whether apo cleaning should extract
  ligands at all, a larger design question than a `func_ligand` data fix.
- Re-run every affected hit list/AUC/matrix and disclose the change against
  the Phase-1 shipped numbers, per this task's own Constraint.

**Files**: `src/allostery/labels.py`, `tests/test_labels.py`,
`scripts/task0391_func_ligand_linter.py`, `config/targets.yaml` (two dated
note addenda only).
**Data**: `results/tasks/0391_func_ligand_linter/result.json`.
