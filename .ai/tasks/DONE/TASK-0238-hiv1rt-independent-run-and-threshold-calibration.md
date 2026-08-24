# TASK-0238 HIV1_RT on our own pipeline — and the question that actually matters: how strict are we?

## Context

- ID: TASK-0238
- Status: Done
- **Thread: Reviewer thread (Opus).**
- Owner: Reviewer
- Claimed By: Reviewer-thread (Opus)
- Claimed At: 2026-08-23
- Source: Bartosz, 2026-08-23, reframing a stalled disagreement between two
  threads' agents into a question answerable on our own data.
- Priority: **P0** — it is the only test that examines *our* instrument rather
  than someone else's, and we have never run one.

## Why this task exists, stated honestly

A parallel thread reports a strong result on HIV1_RT (residue-level AUC 0.982,
P@5 = 1.0). This register reports zero surviving positives anywhere. Two agents
with opposite context histories reached opposite readings, and the natural
move — audit the other side's code — is the wrong one: this repository has
spent months auditing and building on its own findings, and switching to
debugging a second codebase weeks before a deadline is a poor trade.

**The reframing (Bartosz's, and it is better than the reviewer's own
proposal): stop asking whether his result is real, and ask how strict we are.**
That is answerable entirely on our own data, requires none of his code, and is
the bias check neither side has run.

### The reviewer's own bias, recorded because it is relevant evidence

The Reviewer thread has reviewed roughly a dozen results in this session and
**found a defect in every one.** It has never returned "this is fine." A
reviewer that never validates anything is not obviously calibrated, and it
pre-discounted the HIV1_RT number using a prior from this register before
seeing the output it was judging.

### And the measured evidence that this register's instrument may be too conservative

[[TASK-0167.002]] planted a known, confound-orthogonal coupling and measured
whether this pipeline detects it:

> Under the corrected (compact) null — the one this register uses as arbiter —
> **no target reached 80% detection power at any planted strength tested, up to
> ~4× background conductance.** Under the older scattered null, LOD was ≈2×
> background on 2/3 targets.

So the two risks are symmetric, and **both are measured in this register**:

| Instrument | Measured risk |
|---|---|
| Label-permutation (scattered) null | anti-conservative **4.8× at α=0.05, ~42× at α=0.001** on spatially compact labels ([[TASK-0158]]) |
| **Compact-patch null (ours)** | **positive control fails to reach 80% power at 4× background** ([[TASK-0167.002]]) |

One instrument manufactures positives. The other may erase real ones. This
task measures the second.

## Intent Contract

- Outcome: (a) a clean, independent verdict on HIV1_RT through this register's
  own pipeline; (b) a quantitative answer to *"how strict is our threshold, and
  is it too strict?"*, expressed as the setting at which our own verdicts flip.
- **Leg A — HIV1_RT, our pipeline, our labels, our structures.**
  - `1DLO` (apo) → `3V81` (holo), drug `NVP` (nevirapine, NNRTI allosteric
    pocket). Fetched independently from RCSB; nothing taken from the other
    thread's notebook.
  - Run [[TASK-0209]]'s VALID rule **first**. If HIV1_RT is not a valid
    apo-closed/holo-open instance, every downstream number is uninterpretable
    and that is the finding.
  - Then: proximity floor, CTQW/`H_new`, `dcc_low`, scored under our standard
    conventions.
- **Leg B — the calibration, which is the point.**
  - Report the same score's p-value under **both** nulls side by side:
    scattered (the other thread's) and compact/graph-walk (ours). **That single
    comparison localises the entire disagreement to one number.**
  - State the inversion explicitly: *what would the threshold have to be for
    this pipeline to report a positive here?* — i.e. at what α, which null, and
    which floor definition does the verdict flip.
  - Decompose the floor: our floor is the **max** of degree / hop / euclid. How
    much of any negative is that choice rather than the signal?
- Out Of Scope:
  - Auditing or debugging the other thread's code. Explicitly excluded.
  - Adopting HIV1_RT into `targets.yaml` — it is not a challenge target.
- Constraints And Invariants:
  - **Pre-register nothing that can be tuned after seeing the number.** The
    VALID rule, floor and null definitions are inherited unchanged.
  - **A positive here is as reportable as a negative.** If HIV1_RT clears our
    own bar, that is the finding and it must be reported with the same
    prominence a negative would get. The reviewer's bias above makes this worth
    stating as a constraint rather than an intention.
- Planned Validation: reproduce a known register number (KRAS_G12C floor
  0.4818) in the same run, as a wiring check, before trusting any HIV1_RT value.

## TODO

- [x] Fetch 1DLO / 3V81; confirm NVP present in holo.
- [x] TASK-0209 VALID rule on the pair.
- [x] Floor + CTQW + dcc_low under standard conventions.
- [x] Both nulls side by side (three nulls run, not two).
- [x] Threshold inversion: at what setting does the verdict flip?
- [x] Wiring check against a known register number.
- [ ] **Follow-up filed, not done here:** refresh the stale floor/actual
      triplets across the five documents that cite them (see TASK-0239).

## Done

**Executed 2026-08-24. Full numbers and tables: `RESULTS.md`, section
"HIV-1 RT independent run, threshold inversion, and a register-wide
stale-number finding ([[TASK-0238]], 2026-08-24)".**

Answers to the two questions the task was filed to settle:

**"How strict is our threshold?"** — Strict in exactly one place. Across a
pre-registered 80-configuration sweep (`enm_cutoff` × `pocket_contact_cutoff`
× 5 observables), 16 configurations beat the floor but **0 reached
p_compact < 0.05**; best p in the whole grid is 0.1374. The floor gate is soft
(a routine cutoff change crosses it); the compact null is not crossed anywhere
in the parameter space the pipeline exposes.

**"Is it too strict?"** — Two findings say partly yes, and neither was sought:

1. The floor gate is **not independent** of the null. On HIV1_RT the binding
   floor (`hop_from_seed`, AUC 0.7773) has the same p-profile as the score it
   gates (0.0005 scattered / 0.2259 compact, vs the CTQW's 0.0005 / 0.1999).
   Failing "below floor" and failing "null under compact" is one fact counted
   twice, so the two-gate design is stricter *on paper* than in substance.
2. The published floors are **stale**, and correcting them flips two of three
   mandatory targets from below-floor to above-floor. BCR_ABL1 and
   CARDIAC_MYOSIN have been reported here as floor failures; under current
   code they are not — their negative diagnoses come from the chance bar. The
   flagship KRAS_G12C margin drops from +0.1083 to +0.0269.

**The task's own constraint honoured:** finding 2 is a correction against this
reviewer's prior reporting, in the permissive direction, and is written up in
`RESULTS.md` with the same prominence as the negatives.

**HIV1_RT verdict: negative under this register's bar** (CTQW AUC 0.7538,
below floor 0.7773, p_compact 0.1999). It is positive — surviving ×28
Bonferroni — only if *both* gates are dropped at once.

**Contextuality / cross-thread relevance:** the CTQW row is the cleanest
localisation of the null disagreement produced so far. Same structure, same
seed, same score vector, same 2000 permutations: p = 0.0005 scattered vs
p ≈ 0.20 compact, a **400× spread attributable to nothing but the null
construction**. Threads disagreeing about this target are not disagreeing
about physics, code, or data.

**Defect found and fixed en route:** the `len(holo.resnums) == len(apo.resnums)`
guard in `scripts/task0216_score_new_pairs.py:110` and
`scripts/task0216_ptp1b_real_seed.py:71` is required only for
`functional_indices`, not for `holo_pocket_mask` (which Needleman-Wunsch-maps
holo→apo). Applying it to the pocket silently degrades the label to Cα-only.
HIV1_RT's pocket went 5 → 16 residues once corrected. Every other script in
`scripts/` attaches heavy atoms unconditionally and is unaffected.
