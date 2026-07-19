# INV-0001 `cumulative_overlap(apo, delta, rc, k)` — `superpose.py`

## GAUGE

| Transformation | Test | Status |
|---|---|---|
| Zero-mode count >= 6 (ANM) | `anm_modes` (`superpose.py`) counts `n < 1e-8` eigenvalues, asserts `>= 6` (widened from an original `== 6` by [[TASK-0128]] — a connected structure can legitimately have more than 6 near-zero modes; `< 6` still always raises, and a disconnected graph with `> 6` still raises via a connectivity check), **raises** rather than silently slicing by index in every case. Covered by `test_superpose.py::test_drops_at_least_six_rigid_body_modes`, `test_raises_on_disconnected_graph`, `test_connected_structure_with_more_than_six_zero_modes_does_not_raise`. | **GAUGE-VERIFIED** |
| SE(3) (rotation+translation) on `(coords, delta)` jointly | `test_superpose.py::TestCumulativeOverlapSE3Invariance::test_rotation_and_translation_leave_cumulative_overlap_unchanged` — arbitrary off-axis rotation (not 90/180°) + nonzero translation applied jointly to `coords` and `delta_r`, `anm_modes`+`cumulative_overlap` recomputed, full output array matches pre-transform to `atol=1e-9` at every `m`. Eigenvalues (mode energies) also asserted SE(3)-invariant as a fixture sanity check. `test_translation_alone_is_gauge_trivial_for_the_displacement` isolates the translation half specifically. **Passes** — the historical bug's root-cause fix (select-by-eigenvalue, above) generalizes correctly; this task confirmed it rather than assuming it from the fix already being in place. Landed [[TASK-0054]]. | **GAUGE-VERIFIED** |
| Residue relabeling (graph permutation) | `test_superpose.py::TestCumulativeOverlapSE3Invariance::test_residue_relabeling_leaves_cumulative_overlap_unchanged` — coords/delta_r permuted together (consistently, both by the same random permutation), `cumulative_overlap` output stable to `atol=1e-9`. Absorbed into [[TASK-0054]] as a cheap sibling test, per that task's own Out Of Scope allowance. **Passes.** | **GAUGE-VERIFIED** |

## KNOB

- ANM `cutoff` (`anm_modes` default `10.0`), `n_modes` — not yet characterized as a
  spread over a grid. **OPEN.**
- Reference conformer choice — not yet characterized. **OPEN.**

## SIGNAL

- Random displacement vs. real apo→holo delta — not yet null-controlled for this
  specific quantity. **OPEN.**
- Shuffled contact graph — not yet null-controlled. **OPEN.**

## Status

**All 3 GAUGE rows now `GAUGE-VERIFIED`** (2026-07-19, [[TASK-0054]]) — the
SE(3) and permutation rows were the protocol's own named `OPEN` defect
condition ("a seam/invariant with no owner is the defect condition this
protocol exists to prevent") until this task landed real, passing regression
tests for both, not just confirmed the underlying code fix by inspection.
KNOB/SIGNAL rows remain `OPEN` — explicitly out of this task's own scope
(Tier 2 characterization and Tier 3 null controls for this quantity are
separate, not-yet-filed follow-ups). This is still not a fully completed
audit of every transformation this quantity could face — see [[TASK-0051]]
for what was and wasn't checked at seeding time.

## Provenance

Seeded 2026-07-11 by [[TASK-0051]] (Invariance Protocol adoption), directly from
reading `superpose.py` against `INVARIANCE_PROTOCOL.md`'s own ANM worked example
(cumulative overlap moved 0.34→0.90 under rotation before its root-cause fix — the
fix is confirmed live here; the regression test for it is not, hence the one OPEN
GAUGE row).
