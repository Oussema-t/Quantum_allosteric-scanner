# Invariance Protocol

*Unit tests check states. Metamorphic tests check transformations. Every failure this
project has found the hard way — in the physics and in the quantum-channel detour —
was an invariance violation under a group nobody executed.*

## The gap this closes

The existing gates all check **states**: does this function return the right value on
this input (unit), does the pipeline produce the right artifact (integration), does the
label leak (leakage gate), does the boundary hold (seam protocol).

None of them asks: **"what group is this quantity supposed to be invariant under, and
did we execute that group or assume it?"**

That question is not decoration. It has already caught two live bugs:

- **ENM/ANM (this repo).** Cumulative overlap changed **0.34 → 0.90** under a global
  rigid rotation. Root cause: mode selection sliced `w[6:]`, assuming exactly six zero
  modes. The contact graph was rank-deficient (7–63 near-zero modes depending on
  cutoff), so the "softest 5" were *null-space* vectors whose basis is arbitrary and
  rotation-dependent. Selecting by eigenvalue instead of index restored invariance to
  ~1e-9. **No unit test could have found this** — every unit test evaluates one
  structure in one frame.
- **Quantum-channel detour.** A "covariant vector invariant" was invariant only under
  the Clifford subgroup; under generic SU(2) its magnitude moved 4×. Every test channel
  had silently stayed in one Pauli frame. Same failure, different domain: *the test set
  sampled the subgroup you thought of.*

The general shape: **a metric passes because the test suite samples the transformations
you thought of, then breaks under the transformations reality applies.**

## The three-way classification (do this for every reported quantity)

For each quantity the pipeline reports, classify every transformation that could act on
its inputs into exactly one of:

| Class | Meaning | Test form | Failure means |
|---|---|---|---|
| **GAUGE** | must not change the answer at all | hard assert, `atol≈1e-9` | **a bug**, always |
| **KNOB** | a modeling choice; may change the answer | report the **spread**, never a point estimate | verdict is knob-dependent → report `UNSTABLE` |
| **SIGNAL** | must change the answer | assert it *does* (null control) | the metric is inert / scores anything |

The classification is the deliverable. An unclassified transformation is the free axle —
it is where the next bug lives, and prose will not find it.

## Registry

Alongside `.ai/seams/`, keep `.ai/invariants/`, one record per reported quantity:

```
INV-0001  cumulative_overlap(apo, delta, rc, k)
  GAUGE:  SE(3) on (coords, delta) jointly      -> test_inv_se3_overlap        [HARD]
          residue relabeling (graph permutation) -> test_inv_permutation        [HARD]
          zero-mode count == 6 (ANM) / 1 (GNM)   -> test_zero_mode_integrity    [HARD]
  KNOB:   cutoff rc, ENM variant, k, reference conformer
          -> report spread over grid; GO only if decision stable across grid
  SIGNAL: random displacement, shuffled contact graph -> must NOT score
  status: GAUGE-VERIFIED | KNOB-CHARACTERIZED | OPEN
```

## Required tests (physics)

**Tier 0 — GAUGE, hard asserts.** Rotate + translate coordinates *and* the displacement
together; every scalar (cumulative overlap, MSF, GNM/ANM scores, top-5 ranking) must be
stable to ~1e-9. Permute residue indices; scores must permute identically. Any drift is
a bug, never a tolerance to widen.

**Tier 1 — zero-mode integrity (regression test for the bug above).** Assert
`count(|λ| < tol) == 6` for ANM (`== 1` for GNM) and assert graph connectivity. If the
count is wrong, the structure/cutoff is rank-deficient: **raise, do not slice.**
*Never select modes by index — always by eigenvalue with an explicit tolerance.*

**Tier 2 — KNOB characterization (report, don't assert).** Cutoff, ENM variant, `k`,
reference conformer are modeling choices, not gauge. Measured on a 2-domain toy, the
same motion gave cumulative overlap **0.067–0.860** across an 18-combo (rc × variant ×
k) grid — flipping the go/no-go verdict at a 0.5 threshold in **15 of 18** combos. The
gate must therefore emit a *spread over the grid*, and return `GO` only if the decision
is stable across it. A point estimate from one knob setting is scoring your modeling
choice, not the protein.

**Tier 3 — SIGNAL null controls.** Random displacement vs. real apo→holo (must
separate). Shuffled contact graph (signal must die). Catches a metric that scores
anything.

## Required tests (code / agent output)

The same discipline, applied to the swarm's own deliverables — these are the
transformations "obviously" gauge that nobody runs:

- **Refactor invariance**: renaming a module/variable, reordering independent
  functions, or reformatting must not change any numeric output.
- **Seed invariance**: any quantity claimed deterministic must be stable across RNG
  seeds; anything that isn't must report a CI, not a point estimate.
- **Order invariance**: task execution order across parallel agents must not change the
  merged result (the swarm's own SE(3)).
- **Input-permutation invariance**: reordering rows/residues/targets must not change
  aggregate scores.

## Rule of engagement

1. Before a quantity is reported, its transformation table (GAUGE / KNOB / SIGNAL) must
   exist. No table → not reportable.
2. **"Invariant on our test set" is a trigger to widen the group, not a green light.**
   That sentence is exactly what hid both bugs above.
3. The discriminating test is almost never the first one reached for. It is the
   *assumed-gauge* symmetry. Enumerate the largest group that ought to be gauge and
   execute it — especially the one that feels too obvious to check.
4. Multi-turn agreement (human or agent) is **not** verification. Both bugs above
   survived rounds of confident, articulate prose from multiple models and died to
   twelve lines of code.
