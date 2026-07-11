# Invariants

For every reported quantity, classify every transformation that could act on its
inputs into exactly one of GAUGE / KNOB / SIGNAL, before the quantity is
reportable. Full rationale and method: [`INVARIANCE_PROTOCOL.md`](../reference/INVARIANCE_PROTOCOL.md)
(TASK-0051). See also [[pitfalls#P-0001]] (`.ai/memory/shared/pitfalls.md`) for
the two real bugs that motivated this.

## One file per reported quantity

`INV-0001-slug.md`, permanent id, never reused or renumbered — same convention
as `.ai/tasks/` and `.ai/seams/`.

## The three classes

| Class | Meaning | Test form | Failure means |
|---|---|---|---|
| **GAUGE** | must not change the answer at all | hard assert, `atol≈1e-9` | a bug, always |
| **KNOB** | a modeling choice; may change the answer | report the spread, never a point estimate | verdict is knob-dependent → report `UNSTABLE` |
| **SIGNAL** | must change the answer | assert it does (null control) | the metric is inert |

An unclassified transformation is the free axle — it is where the next bug lives.

## Required fields (every invariant file)

- one row per known transformation, each tagged GAUGE/KNOB/SIGNAL
- for GAUGE rows: the test that enforces it (hard assert) and its status
- for KNOB rows: how the spread is reported, and whether the go/no-go decision
  is checked stable across the grid
- for SIGNAL rows: the null control that proves the metric isn't inert
- `status` per row: `GAUGE-VERIFIED` | `KNOB-CHARACTERIZED` | `OPEN`

## Rule of engagement

1. No transformation table → not reportable.
2. "Invariant on our test set" is a trigger to widen the group, not a green
   light — see [[pitfalls#P-0001]].
3. The discriminating test is almost never the first one reached for. It's the
   *assumed-gauge* symmetry — the one that feels too obvious to check.
4. Multi-turn agreement (human or agent) is not verification.
