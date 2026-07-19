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

That question is not decoration. It has already caught three live bugs:

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

- **Proximity confound (this repo, `REVIEW-2026-07-13-proximity-confound-and-
  propagator-semantics.md`).** A CTQW occupation score was reported as allosteric
  signal (KRAS_G12C AUC 0.779) with only a chance/degree-centrality floor beneath
  it. Direct check: `Spearman(occupation, -distance from seed) = +0.853` on a
  synthetic reproduction — the "signal" was mostly geometry. Different tier from
  the two bugs above (those were GAUGE violations — an assumed invariance that
  wasn't; this was a **SIGNAL** gap — a null control that only ruled out random
  noise, never the domain's actual strongest trivial predictor). Same root
  pattern though: **"beats chance" was quietly treated as "beats the obvious
  alternative explanation," and nobody had executed the comparison that would
  have told the two apart.** Fixed at the code level by TASK-0094
  (`baselines.euclid_from_seed_centroid`/`hop_from_seed`, wired into the floor);
  fixed at the protocol level below (TASK-0098) so the next domain's equivalent
  gap gets caught by the checklist, not by an external reviewer.

The general shape: **a metric passes because the test suite samples the transformations
you thought of, then breaks under the transformations reality applies.**

## The three-way classification (do this for every reported quantity)

For each quantity the pipeline reports, classify every transformation that could act on
its inputs into exactly one of:

| Class | Meaning | Test form | Failure means |
|---|---|---|---|
| **GAUGE** | must not change the answer at all | hard assert, `atol≈1e-9` | **a bug**, always |
| **KNOB** | a modeling choice; may change the answer | report the **spread**, never a point estimate | verdict is knob-dependent → report `UNSTABLE` |
| **SIGNAL** | must change the answer | assert it *does*, **against the domain's strongest trivial confounder — not only random/chance** (null control) | the metric is inert, or worse, is *scoring the confounder* |

The classification is the deliverable. An unclassified transformation is the free axle —
it is where the next bug lives, and prose will not find it.

**A SIGNAL classification against a random-noise null control alone is
insufficient (TASK-0098, amending TASK-0051's original adoption).** "Beats chance"
and "beats the obvious domain heuristic" are different claims — a metric can
clear the first while being nothing but a re-derivation of the second. Before
reporting a quantity as SIGNAL, name the domain's strongest known trivial
predictor and show the metric beats *that*, not just a shuffled/random baseline.
For this repo's allostery-detection domain, that predictor is **distance from
the propagation seed** (proximity) — a CTQW/heat-kernel occupation score is
mechanically higher near its own seed regardless of any real allosteric
coupling, the same way a cumulative-overlap score can be inflated by an
unexecuted rotation gauge. The general rule, so it transfers to a future
domain/confounder: **enumerate the cheapest non-trivial predictor a skeptic
would reach for first, and put it in the SIGNAL null control, not just noise.**
Worked example, code-level: `baselines.euclid_from_seed_centroid`/
`hop_from_seed`, wired into `diagnostics.classify_failure`'s floor
(TASK-0094) — see `.ai/tasks/DONE/TASK-0094-proximity-baselines-into-floor.md`.

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
          [+ this quantity's own domain-confounder check, Tier 3b -- omitted
          here since this record predates that amendment; not retroactively
          filled in without checking what the real strongest confounder is]
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

**Tier 3b — SIGNAL vs. the domain's strongest trivial confounder (TASK-0098,
amending Tier 3 above — a random/shuffled null alone is not sufficient).**
Random noise proves a metric isn't inert; it does not prove the metric is
measuring what it claims to. For allostery-detection specifically: **a
propagation-based occupation score (CTQW, heat kernel, any seed-centered walk)
must be checked against `-distance-from-seed` (Euclidean and/or graph-hop) as
a floor, not only chance** — `baselines.euclid_from_seed_centroid`/
`hop_from_seed`, `diagnostics.classify_failure`'s multi-baseline floor
(TASK-0094). A target only reports as signal if its AUC clears **both** chance
**and** this proximity floor. Measured real consequence: KRAS_G12C's
apo-only AUC (0.779) beats chance and degree centrality but does **not**
clear the proximity floor (Euclidean 0.798, hop 0.781) — the number is
geometry, reported as such, not softened. Generalizes beyond this repo: before
trusting any SIGNAL classification, ask "what is the cheapest explanation a
skeptical reviewer would reach for first," and put that explanation in the
null control, not just a random shuffle.

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
   That sentence is exactly what hid all three bugs above.
3. The discriminating test is almost never the first one reached for. It is the
   *assumed-gauge* symmetry. Enumerate the largest group that ought to be gauge and
   execute it — especially the one that feels too obvious to check.
4. Multi-turn agreement (human or agent) is **not** verification. All three bugs above
   survived rounds of confident, articulate prose from multiple models and died to a
   handful of lines of code.
5. **"Beats chance" is not "beats the obvious alternative explanation" (TASK-0098).**
   A SIGNAL classification needs a null control against the domain's strongest trivial
   confounder, not only random noise — see Tier 3b above. The leakage firewall guards
   against *knowing the answer*; this guards against the score being *trivially
   predictable from something else entirely* (geometry, in this repo's case). Both are
   leaks — one through labels, one through coordinates.
