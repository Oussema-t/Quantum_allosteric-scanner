# TASK-0093 Reconcile KRAS_G12C's real end-to-end AUC (0.779) against the previously-documented near-chance finding (~0.51-0.53)

## Context

- ID: TASK-0093
- Title: Determine which real methodology difference — cutoff (8.0 Å vs
  10.0 Å) or pocket-label definition (assembled/excluded vs raw
  ligand-contact) — explains why `TASK-0079.005`'s real KRAS_G12C run
  scored far above this repo's own previously-documented, tested result
  for the same target.
- Status: Done
- Owner: Implementer
- Source: [[TASK-0079.005]]'s first real end-to-end run (2026-07-12).
  This is a genuine discrepancy between two honest, real, network-backed
  numbers for the *same* target — not a hypothesis, a measured fact that
  needs an explanation before either number is trusted as "the" KRAS_G12C
  result.
- **Updated 2026-07-13** per
  `__WORK_IN_PROGRESS__/REVIEW-2026-07-13-proximity-confound-and-propagator-semantics.md`
  (finding P1-A): the review supplies a **candidate mechanism** this task
  did not have when originally filed — the 8.0 Å vs 10.0 Å cutoff changes
  the contact graph, which changes the walk's distance-decay profile
  from the seed. Since KRAS_G12C's pocket sits **adjacent** to the active
  site (SII-P, per the review's cross-target table), a tighter/looser
  cutoff could shift the AUC purely by changing how proximity-correlated
  the score is — independent of any real change in allosteric
  sensitivity. **This task's factorial isolation (cutoff / pocket-label /
  source) must now be run against TASK-0094's proximity floor, not just
  against chance/degree** — a combination that "explains" the AUC gap by
  cutoff alone is not informative if the resulting AUC never clears the
  proximity floor at any cutoff. Hard-blocked on TASK-0094 landing first.

### The discrepancy (the load-bearing fact this task exists to resolve)

| | Existing, documented, tested | New, real run (TASK-0079.005) |
|---|---|---|
| `AUC_apo_Hnew_default` | ~0.51-0.53 ("near chance even with the answer key," asserted `0.3 < AUC < 0.7` in `test_analysis.py::test_kras_g12c_real_target_near_chance_and_flat_dephasing`) | **0.779** (outside that asserted band entirely) |
| `enm_cutoff` | 10.0 Å (that test's own default) | 8.0 Å (`targets.yaml`'s configured `enm_cutoff` for KRAS_G12C, used by `.004`'s orchestrator) |
| Pocket label | raw `holo_pocket_mask(apo, holo, "MOV", cutoff=4.5)`, pre-exclusion | `labels.build_labels(...)`'s assembled `.pocket` — `pocket_raw & ~active_site & ~terminal` (TASK-0070, post-dates the older test) |
| Propagation source | a specific aligned/mapped GDP-contact subset (`functional_indices` on holo, mapped through `align_apo_holo` to apo) | `np.where(labels.active_site)[0]` — `functional_indices` computed **directly on apo**, via `build_labels`, not cross-mapped from holo |

Independent corroborating evidence the new number isn't a fluke or a
leak: `_diagnosis: NO_FAILURE_DETECTED` (cleared both the chance check
*and* the degree-centrality floor via `floor_scores`), and a real,
non-trivial cross-check — 3 of the top-5 hit-list resnums (34, 11, 59)
land directly in `backend/systems.py`'s independently-sourced
`pocket_full[4.5]` reference set (`test_labels.py`'s own pinned KRAS
reference, 21 residues total, ~12% baseline prevalence). The new result
does not look like a leak; it looks like a real, different, better
answer under different conditions — which is exactly why it needs
explaining, not dismissing in either direction.

## Intent Contract

- Outcome: an evidence-backed attribution of the ~0.25 AUC gap to one or
  more of the three identified variables (cutoff, pocket-label
  definition, source definition), each tested independently by holding
  the other two fixed — not a guess, and not "probably the labels."
- In Scope:
  - **Isolate cutoff**: rerun the real KRAS_G12C pipeline at cutoff=10.0
    (matching the old test) with everything else identical to
    TASK-0079.005's real run (assembled `build_labels` pocket,
    apo-derived `active_site` source). If AUC drops back toward ~0.5,
    cutoff is the dominant variable.
  - **Isolate pocket-label definition**: at whichever cutoff isolates
    cleanly, score against the *raw* `holo_pocket_mask` output (like the
    old test) instead of `build_labels`'s assembled `.pocket`, everything
    else held fixed. If AUC drops, the exclusion-assembly is the
    dominant variable (a smaller, cleaner label set could legitimately
    score differently than a noisier raw one — not a bug, but worth
    knowing which one the submission should report).
  - **Isolate source definition**: compare `active_site`-derived source
    (apo-native `functional_indices`) against the old test's
    holo-aligned-then-mapped source, everything else held fixed.
  - Report a small factorial table (which combination gives which AUC),
    not just a single "found it" claim — per this session's own
    Invariance-Protocol-adjacent discipline: report the actual spread
    across the tested combinations, don't collapse to one number
    prematurely.
  - **Added 2026-07-13**: for every combination in the factorial table,
    also report whether that combination's AUC clears TASK-0094's
    proximity floor (`euclid_from_seed_centroid`/`hop_from_seed`), not
    just chance. A combination that raises AUC without clearing the
    proximity floor should be reported as "raises apparent signal by
    making the score more proximity-correlated," not as evidence of real
    allosteric sensitivity.
- Out Of Scope: deciding which methodology is "correct" for the
  submission — that is a downstream decision for whoever owns the
  competence-map/artifact-contract work ([[TASK-0082]]/[[TASK-0083]]),
  informed by this task's factorial evidence, not decided here. Also out
  of scope: re-litigating TASK-0070's exclusion-assembly design itself
  (already reviewed, Done) — this task checks its *AUC consequence* on
  this one target, not its correctness as a leakage boundary.
- Constraints And Invariants: every variant tested must still go through
  the real `frozen_context`/`run_frozen_verdict` gate — this is a
  methodology-sensitivity investigation, not license to bypass the
  leakage firewall for convenience.
- Planned Validation: the factorial table itself, plus a one-paragraph
  attribution statement in this task's Done section.

## Dependency

- [[TASK-0079.005]] — source of the discrepancy.
- [[TASK-0070]] (`build_labels`'s exclusion assembly) and the older
  `test_kras_g12c_real_target_near_chance_and_flat_dephasing`
  (`test_analysis.py`) — the two real, tested reference points being
  reconciled.
- **Hard blocked on TASK-0094** (proximity floor, added 2026-07-13) — the
  factorial table's conclusions are not trustworthy without it.
- [[TASK-0106]] (added 2026-07-13) — `REVIEW-2026-07-13c` gives a
  mechanistic reason to expect `H10`/`H2`-family operators to beat
  `H_new` on distal pockets (transport localization caused by `H_new`'s
  diagonal potentials). This task's own BCR_ABL1 sign (`H10`=0.558 vs
  `H_new`=0.525, previously read as noise) may be the same effect on a
  different target — read TASK-0106's real-data result before finalizing
  this task's own reconciliation.

## Open Questions

- None yet — scope is bounded to attributing one already-measured gap on
  one target.

## Done

**Finalized 2026-07-14** -- [[TASK-0106]] (Thread A / Implementer A) has
landed its Done section (BCR_ABL1 real-data CTQW-trapping reproduction),
so the hold this task's own Dependency section placed is now released.
Everything below is the real, complete factorial measurement, plus the
now-final attribution incorporating TASK-0106's result.

**Script**: `__WORK_IN_PROGRESS__/scripts/kras_auc_reconciliation.py`.
Real network + real compute, KRAS_G12C only (4OBE/6OIM). Both reference
points reproduced **exactly** as a validation gate before trusting the
rest of the grid: real-run combo (cutoff=8.0, assembled pocket,
apo-native scalar source) = 0.7792 (reference 0.7792); old-test combo
(cutoff=10.0, raw pocket, holo-mapped array source) = 0.5076 (reference
~0.51-0.53 band). Two undocumented variables were discovered while
reaching that exact reproduction and are reported explicitly rather than
folded into "source definition" (see script docstring for the full
argument):
- **Cardinality**: the real run's apo-native source is a scalar
  (TASK-0090's workaround), the old test's holo-mapped source is a full
  multi-index array.
- **Heavy-atom vs Calpha-only contact geometry**: the real run's loader
  attaches `holo.heavy_atom_coords` (used by `build_labels`/
  `holo_pocket_mask` via `getattr`), the old test never does.

### Core 2x2x2 factorial (cutoff x pocket-label x source), scored against TASK-0094's proximity floor

| cutoff | pocket-label | source | AUC | floor | clears floor? |
|---|---|---|---|---|---|
| 8.0 | assembled | apo_native_scalar | 0.7792 | 0.7976 | **No** |
| 8.0 | assembled | holo_mapped_array | 0.5018 | 0.5614 | No |
| 8.0 | raw | apo_native_scalar | 0.8187 | 0.8236 | **No** |
| 8.0 | raw | holo_mapped_array | 0.5660 | 0.5837 | No |
| 10.0 | assembled | apo_native_scalar | 0.7833 | 0.7976 | **No** |
| 10.0 | assembled | holo_mapped_array | 0.4974 | 0.5099 | No |
| 10.0 | raw | apo_native_scalar | 0.8007 | 0.8160 | **No** |
| 10.0 | raw | holo_mapped_array | 0.5076 | 0.5128 | No |

**Zero of eight combinations clear the proximity floor** -- including
the real run's own headline 0.7792 (floor 0.7976, margin **-0.018**).
This is the single most important fact this task produces: it is not
that a *better* methodology found a *real* signal the old test missed.
Every methodology combination in the tested grid, including the one
that produced the headline number, is statistically indistinguishable
from (or below) its own strongest trivial proximity baseline.

### Supplementary: cardinality-only check (apo-native source, scalar vs full array, both other variables held fixed)

| cutoff | pocket-label | source | AUC | floor | clears? |
|---|---|---|---|---|---|
| 8.0 | assembled | apo_native_array | 0.4533 | 0.4818 | No |
| 8.0 | raw | apo_native_array | 0.5264 | 0.5094 | **Yes** (margin +0.017) |
| 10.0 | assembled | apo_native_array | 0.4411 | 0.5006 | No |
| 10.0 | raw | apo_native_array | 0.4688 | 0.4812 | No |

**This is the actual dominant driver, and it was not one of the three
variables this task was originally scoped to test.** Holding cutoff,
pocket-label, and frame (apo-native) all fixed, narrowing the source
from the full active-site array (18 residues) to a single scalar seed
(TASK-0090's workaround) moves AUC from ~0.44-0.53 to ~0.78-0.82 --
a bigger swing than cutoff or pocket-label produce on their own -- and
the proximity floor rises by almost exactly the same amount in lockstep
(0.48-0.51 -> 0.80-0.82), so the AUC-vs-floor margin stays negative
throughout. **TASK-0090's single-seed workaround is not a neutral
implementation shortcut for this target: collapsing a spread-out,
multi-residue seed to one point residue makes the walk/geometry more
proximity-concentrated, inflating both the raw score and the proximity
floor together.** This is mechanistically consistent with
REVIEW-2026-07-13c's CTQW-trapping hypothesis (localization near the
seed) and is a live confound in the *actual shipped* end-to-end run
(`run_challenge.py` uses exactly this scalar-seed workaround for every
target, not just KRAS) -- flagged here since it was discovered as a
byproduct of this task, not filed as its own task per this session's
"an implementer surfaces, an orchestrating thread files" convention.

### Supplementary: heavy-atom-vs-Calpha contact geometry (pocket_raw, apo-native scalar source)

| cutoff | geometry | AUC | floor | clears? |
|---|---|---|---|---|
| 8.0 | raw_calpha_only | 0.8187 | 0.8236 | No |
| 8.0 | raw_heavy_atom | 0.8176 | 0.8378 | No |
| 10.0 | raw_calpha_only | 0.8007 | 0.8160 | No |
| 10.0 | raw_heavy_atom | 0.8243 | 0.8378 | No |

Small effect (<=0.02 AUC swing) relative to the cardinality effect above
-- present, but not the dominant variable, and does not change any
floor-clearing verdict.

### Attribution (final)

The ~0.25 AUC gap between the old test (~0.51) and the real run (0.779)
is attributable, in descending order of effect size, to: **(1) source
cardinality** (scalar vs multi-index seed, TASK-0090's workaround --
the largest single lever, not one of the three originally-named
variables), **(2) source frame** (apo-native vs holo-mapped, a real but
smaller contributor once cardinality is held fixed -- compare
apo_native_array 0.45-0.53 against holo_mapped_array 0.50-0.57 at
matched cutoff/label, a much smaller gap than scalar-vs-array), and
**(3) pocket-label definition and cutoff**, both real but the smallest
of the four. **None of these attributions license treating either
number as "the" real KRAS_G12C result** -- per REVIEW-2026-07-13 P1-A's
hard acceptance criterion, that is not decided by which combination
scores highest, but by which combination clears the proximity floor,
and the answer measured here is **none of them, across the full grid
tested**. This reframes the original question ("why does the real run
score higher") into the more load-bearing one this task's Updated
Context anticipated: the real run's higher AUC is explained by the
score becoming *more proximity-correlated*, not more allosterically
informative -- consistent with, and now additionally evidenced beyond,
`TASK-0094`'s own commit-level finding
(`BEATS_CHANCE_NOT_FLOOR`) for this exact target.

### TASK-0106 cross-check (resolves the "held open" question)

TASK-0106's real-data BCR_ABL1 result (its own Done section, 2026-07-14):
transport-preserving operators (`H10`, `H2`) do **not** uniformly beat
`H_new` -- only `H10` does (0.558 > 0.525, confirmed real), `H2` and
reduced-λ `H_new` score *lower*. Critically, **none of the four
operators clear BCR_ABL1's own proximity floor (0.565)** -- `H10`'s
edge is real but "not yet distinguishable from a proximity-driven
result" (TASK-0106's own words). This does not strengthen a claim that
KRAS and BCR_ABL1 share one clean underlying mechanism; it strengthens
a *broader, more load-bearing* pattern this task's own factorial already
showed for KRAS: **raising an operator/methodology's raw AUC is
repeatedly, independently found to not be the same thing as clearing
the proximity floor** -- true here across cutoff/pocket-label/source
(KRAS, this task) and independently true across operator family
(BCR_ABL1, TASK-0106). Two independent threads, two different targets,
converging on the same meta-finding.

**Independent convergent discovery, worth flagging prominently**:
TASK-0106's own Done section separately found that switching BCR_ABL1's
seed from a single scalar index to the full active-site array **flips
the sign of which operator wins** (`H_new` goes from lowest-scoring to
*highest*-scoring, AUC 0.567, under the multi-index convention) --
structurally the same class of finding as this task's own "cardinality
is the dominant lever" result above, discovered independently, on a
different target, by a different implementer, the same day. Neither
task set out to find this; both did. This is now a cross-target,
cross-implementer replicated finding, not a KRAS-specific quirk: **the
scalar/TASK-0090-workaround seed convention `run_challenge.py` uses for
every mandatory target is a live, unexamined GAUGE choice materially
shaping every currently-reported headline AUC**, not a neutral
implementation shortcut. Recommend this be raised to the orchestrating
thread as a candidate for its own task (fixing TASK-0090 properly, or
at minimum running every mandatory target's headline number through
both seed conventions before the submission) -- not filed here, per
this session's "an implementer surfaces, an orchestrating thread files"
convention already used once above in this same document.
