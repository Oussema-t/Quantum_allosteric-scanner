# TASK-0391 — Fix `func_ligand`'s silent fall-through on stale/incomplete codes

- Status: TODO
- Owner: unassigned
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
