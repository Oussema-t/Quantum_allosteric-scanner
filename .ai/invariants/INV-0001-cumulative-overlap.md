# INV-0001 `cumulative_overlap(apo, delta, rc, k)` — `superpose.py`

## GAUGE

| Transformation | Test | Status |
|---|---|---|
| Zero-mode count == 6 (ANM) | `anm_modes` (`superpose.py:258-283`) counts `n < 1e-8` eigenvalues, asserts `== 6`, **raises** on mismatch — never selects by index. Covered by `test_superpose.py::test_drops_at_least_six_rigid_body_modes`, `test_raises_on_disconnected_graph`. | **GAUGE-VERIFIED** |
| SE(3) (rotation+translation) on `(coords, delta)` jointly | No test rotates+translates both jointly and asserts `cumulative_overlap` output stable to `atol≈1e-9`. `test_recovers_synthetic_rotation_translation` tests Kabsch alignment recovery — a different claim. Owner: [[TASK-0054]]. | **OPEN** |
| Residue relabeling (graph permutation) | Not checked for this quantity. | **OPEN** (not yet owned — file if [[TASK-0054]]'s scope doesn't absorb it) |

## KNOB

- ANM `cutoff` (`anm_modes` default `10.0`), `n_modes` — not yet characterized as a
  spread over a grid. **OPEN.**
- Reference conformer choice — not yet characterized. **OPEN.**

## SIGNAL

- Random displacement vs. real apo→holo delta — not yet null-controlled for this
  specific quantity. **OPEN.**
- Shuffled contact graph — not yet null-controlled. **OPEN.**

## Status

Mixed: one row `GAUGE-VERIFIED` by direct code inspection (not assumed), the rest
`OPEN`. This is the protocol's first seeded record, not a completed audit — see
[[TASK-0051]] for what was and wasn't checked at seeding time.

## Provenance

Seeded 2026-07-11 by [[TASK-0051]] (Invariance Protocol adoption), directly from
reading `superpose.py` against `INVARIANCE_PROTOCOL.md`'s own ANM worked example
(cumulative overlap moved 0.34→0.90 under rotation before its root-cause fix — the
fix is confirmed live here; the regression test for it is not, hence the one OPEN
GAUGE row).
