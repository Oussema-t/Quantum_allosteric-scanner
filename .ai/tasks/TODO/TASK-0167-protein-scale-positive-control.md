# TASK-0167 Protein-scale positive control — does the apparatus detect signal that IS there?

## Context

- ID: TASK-0167 (parent coordinator — see subtask table below)
- **Renumbered 2026-07-28 (Architect/Planner)**: filed as TASK-0170 by
  `REVIEW-panel-2026-07-28-external.md` (`.ai/reviews/2026-07-28/`), which
  numbered from a stale count — the actual next-free ID at filing time was
  TASK-0167. Renumbered here and in all 3 subtasks; no content changed.
- Title: establish, by construction, that this project's full verdict
  pipeline (floor → CI → matched permutation null → Bonferroni) recovers a
  *planted*, confound-orthogonal, genuinely distal allosteric coupling on a
  real apo topology — and report the **limit of detection (LOD)**: the
  smallest planted coupling the apparatus can certify.
- Status: TODO
- Owner: Architect/Planner (this file) — subtasks to Implementer
- Claimed By: —
- Claimed At: —
- Source: external panel review, `REVIEW-panel-2026-07-28-external.md` §5B,
  raised as *"the experiment a referee will ask for and you do not
  currently have it."*
- Priority: **P0 — the single highest-value experiment remaining before the
  2026-08-08 writing start. Blocks the paper's central claim.**

## Why this matters — the whole program is currently unfalsifiable

Every negative result in this register is of the form *"observable X does
not clear the floor / null on target Y."* Not one of them is accompanied by
evidence that the pipeline **would** have cleared the floor had the signal
been present. Without that, every negative in `RESULTS.md` admits two
readings that the data cannot separate:

1. **The signal is not in the apo topology** (the reading the project takes).
2. **The apparatus cannot detect signal of this kind at all** (never tested).

Reading 2 is not a hypothetical concern. This project's own gates have
accumulated: whole-graph AUC → proximity floor (max of 3 baselines) →
distance-stratified shells → block-bootstrap CI non-overlap → permutation
null → Bonferroni across 3–16 comparisons → program-level multiplicity
budget of 226 cells. **Each addition was individually correct and each one
removed power.** [[TASK-0161]] concluded the program has *fewer* positives
than α=0.05 chance alone predicts (0 observed vs ~11.3 expected). The
project read that as strength. **It is at least as consistent with a
pipeline whose combined gates cannot pass anything** — and the external
review's §2.1 finding (the compact-patch null is ~4× over-conservative for
surface-lining pocket geometry, costing 2–2.5× power) gives a concrete,
measured mechanism for exactly that.

A negative result is only publishable if it is falsifiable. Right now it
is not. This task makes it so.

The mirror image already exists and works: [[TASK-0103]]'s dumbbell 2×2 is
a **negative** control (it proves an observable follows the *wrong* cue when
cues conflict). There is no **positive** control (proving an observable
follows the *right* cue when one exists) anywhere in the register, at
protein scale, through the real verdict machinery.

## What the deliverable actually is

Not a pass/fail. A **detection curve and an LOD in interpretable units**:

> *"Through the full corrected pipeline, we detect planted active-site→pocket
> coupling at ≥80% power once the induced GNM cross-correlation between the
> two regions exceeds R× background. Experimentally characterized allosteric
> proteins show R in the range [literature value]. Our mandatory targets show
> R = [measured]. We therefore [can / cannot] exclude that real coupling of
> the magnitude reported in the literature exists in these apo structures
> below our detection threshold."*

That sentence, with real numbers in it, converts the program from *"we found
nothing"* to *"we found nothing, here is exactly what we could have found,
and here is what that bounds."* It is the difference between an unfalsifiable
negative and a measurement.

## Design (pre-verified by the source review — reproduce, do not assume)

The plant must be **confound-orthogonal by construction**, or the control
tests proximity detection rather than coupling detection.

**Mechanism: channel reweighting.** Multiply edge *weights* along several
shortest paths from active site to a planted distal patch by `(1+s)`. This
adds no edges, moves no atoms, and creates no new contacts — so
`hop_from_seed` (unweighted BFS), `euclid_from_seed_centroid` (3D distance),
and unweighted `degree_centrality` are **provably invariant**. Physically it
is the ENM picture of a stiff communication channel embedded in a softer
matrix.

The source review prototyped this on a synthetic 249-residue two-lobe fold
(hop diameter 12, planted patch at mean hop 7.4 from the seed):

```
strength  DCC ratio   CTQW AUC   hop AUC   euclid AUC   clears floor?
0.0       1.27        0.195      0.101     0.059        no
0.5       1.29        0.136      0.101     0.059        no
1.5       1.20        0.352      0.101     0.059        no
4.0       0.68        0.406      0.101     0.059        no
10.0      1.55        0.701      0.101     0.059        YES
30.0      2.34        0.740      0.101     0.059        YES
```

Three things to carry forward, and one warning:

1. **The confound baselines are bit-identical at every strength** (0.101 /
   0.059 throughout). The design property holds exactly, not approximately.
2. **A real detection threshold exists** between s=4 and s=10 — so an LOD is
   measurable, not merely notional.
3. **The unplanted baseline is 0.195, strongly ANTI-correlated** with the
   distal label — the proximity confound actively fights the plant. This is
   the honest hard case and must not be softened by planting somewhere easy.
4. **⚠ `|DCC| ratio` is NOT monotone in `s`** (0.68 at s=4, below the s=0
   value of 1.27). Do not use it as the dose axis without checking. Report
   the LOD against the *raw plant strength* as the primary axis and against
   an induced-coupling measure as a secondary one, and pick that measure by
   measurement — see [[TASK-0167.001]]'s Open Questions.

**Caveat on the prototype, stated so it is not over-trusted:** it used a
bare combinatorial Laplacian and a plain converged CTQW on a *synthetic*
two-lobe fold — not `H_new`, not a real structure, not the verdict pipeline.
It establishes that the design is sound and an LOD exists. It does not
establish the LOD's value.

## Subtasks

| ID | Slice | Priority | Est. |
|---|---|---|---|
| [[TASK-0167.001]] | `allostery.plant` — planting machinery + confound-orthogonality gate | P0 | ~1 day |
| [[TASK-0167.002]] | Detection curve + LOD through the full verdict pipeline | P0 | ~1.5 days |
| [[TASK-0167.003]] | Specificity at zero plant — false-positive rate, closes the null-calibration loop | P0 | ~0.5 day |

Parent is Done only when all three are Done.

**Related, filed separately (not subtasks — different questions):**
[[TASK-0168]] (mechanism-discriminating plant), [[TASK-0169]] (benchmark
discriminability audit), [[TASK-0170]] (literature-validated ground truth).

## Intent Contract

- Outcome: a detection curve and LOD per headline observable, measured on
  real apo topology, through the unmodified verdict pipeline, plus a
  one-paragraph statement of what the program's negatives do and do not
  exclude given that LOD.
- Why required, not assumed: no positive control exists at any scale above
  the 44-node dumbbell; the combined gates have never been shown to pass
  anything; [[TASK-0161]]'s zero-positives finding is consistent with both
  a true negative and a dead apparatus, and the project currently asserts
  the first without evidence against the second.
- In Scope: subtasks .001–.003 (see each file).
- Out Of Scope:
  - Changing any gate, threshold, or null in response to the LOD. **This
    task measures the apparatus; it does not tune it.** If the LOD is
    embarrassingly high, that is the finding, and it is reported.
  - Re-running or retracting any existing real-target result.
  - Any new observable.
- Constraints And Invariants:
  - The pipeline runs **unmodified**. If a gate must be bypassed to make the
    control work, the control has failed and that is the result.
  - The plant is applied to the graph/operator only. Coordinates, contact
    topology (unweighted adjacency), and residue identity are untouched, and
    this is asserted, not assumed — see [[TASK-0167.001]]'s gate.
  - The planted patch must be genuinely distal (mean hop from seed ≥ 60th
    percentile of the hop distribution) and must have a *sub-chance*
    proximity-floor AUC before planting. Planting somewhere the floor
    already favours is a null experiment.
  - Multiple planting seeds (≥ 20) per strength — a single planted patch is
    one draw, and the LOD is a property of the distribution.
- Planned Validation: [[TASK-0167.003]] is this task's own control — at
  `s=0` the pipeline must certify the planted patch at ≤ the nominal rate.
  If it does not, the LOD from .002 is meaningless and .003 blocks it.

## In Progress

None

## TODO

- [ ] Dispatch [[TASK-0167.001]] (blocks .002 and .003).
- [ ] Dispatch [[TASK-0167.002]] and [[TASK-0167.003]] in parallel once .001 lands.
- [ ] Write the LOD paragraph into `RESULTS.md` as a top-level section, not
      an open-questions row — it is a headline result either way.
- [ ] Cross-link from `COMPETENCE_MAP.md`: every "no signal" verdict there
      should carry the LOD as its stated detection bound.

## Dependency

- [[TASK-0094]] (Done) — proximity floor.
- [[TASK-0103]] (Done) — the negative control this mirrors; reuse its
  `auc_to_drug` harness conventions.
- [[TASK-0112]] (Done) / [[TASK-0165]] (Done) — CIs.
- [[TASK-0123]] (Done) — stratified AUC.
- [[TASK-0130]] (Done) — converged closed-form propagator.
- [[TASK-0158]] (Done) — compact-patch null. **Note: the external review
  found this null over-conservative; [[TASK-0167.003]] measures that
  directly, so this task is also the empirical resolution of that dispute.**

## Open Questions

- Should the LOD be reported per-target or pooled? Per-target is more
  honest (topologies differ); pooled is what a referee will want as a
  single number. Recommend both, per-target primary.
- Does the LOD depend on pocket size? Plausibly yes (16 vs 21 residues).
  Sweep if cheap, state as unmeasured if not.

## Done

(not yet)
