# TASK-0153 Extend the holo-diagnostic comparison to transport (T_E/R_eff) and low-mode (prs_low/dcc_low) observables

## Context

- ID: TASK-0153
- Title: [[TASK-0067]] (raw GNM) and [[TASK-0092]] (`H_new`/CTQW) each
  built a holo-native diagnostic comparison — same operator, fed the
  holo topology instead of apo — to separate "(a) apo genuinely lacks
  the information" from "(b) the operator/propagator itself is the
  bottleneck." Neither of today's two real positive findings has been
  through this lens: [[TASK-0145]]'s quantum-transport observables
  (`R_eff`, `T(E)`, Bonferroni-significant on BCR_ABL1, p=0.003) and
  [[TASK-0149]]'s low-mode predictors (`prs_low`/`dcc_low`,
  Bonferroni-significant on CARDIAC_MYOSIN, p=0.003-0.006) are both
  operator families neither TASK-0067 nor TASK-0092 ever tested. This
  task runs the same diagnostic — never a scoring/prediction path,
  strictly upper-bound/failure-attribution — for these two families.
- Status: Done (2026-07-24) — mixed: CARDIAC_MYOSIN `prs_low` near an information ceiling (b); `dcc_low` diverges from it on the same target, flagged not resolved
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: user question, 2026-07-24, prompted by "the best we can get
  now is LEARNABLE_FROM_APO — should we check DETECTABLE_IN_HOLO too?"
  Answered: the mechanism already exists (TASK-0067/0092), deliberately
  kept diagnostic rather than folded into `learnability_verdict`'s own
  enum (that function answers a different question — does apo's own
  dynamics encode the conformational change — not "can this operator
  find the pocket at all given full structural information"). This
  task is the concrete extension, not a new concept.
- Priority: **P1** — directly informs how to frame today's 2 best
  results in the 6-pager: near an information ceiling (holo doesn't
  help much more) vs. real headroom left on the table (holo does
  noticeably better, motivating a holo-informed follow-on write-up).

## Design note — this is NOT a re-run of `holo_diagnostic_comparison.py`'s own two-pass structure

**Read this before copying TASK-0092's pattern uncritically.** TASK-0092's
script exists because `H_new`/CTQW goes through `run_frozen_verdict`'s
multi-candidate blind-selection machinery (`select_frozen_config`) —
its two-pass design (apo-only selects a winner; a second pass re-derives
the same winner's operator on holo coordinates) exists *specifically*
to keep holo out of the selection step. **Neither `transport.R_eff`/
`T_E` nor `lowmode_predictor.prs_low`/`dcc_low` go through that
selection path at all** — TASK-0145/TASK-0149 both score these
observables directly (`transport_observable_real_run.run_one`,
`lowmode_predictor_real_run.run_target`), with `E`/`gamma_lead`/`k_modes`
all fixed a priori, not selected from a candidate pool. There is nothing
here to keep out of a selection step. So the correct, simpler design is:
compute each observable directly on **holo coordinates + holo-native
seed + holo-native pocket label** (reuse `_holo_native_labels` from
`test_gnm_cutoff_weight_benchmark.py`, TASK-0067's own construction,
imported verbatim as TASK-0092 already does — do not re-derive it), and
compare that AUC against the already-recorded apo AUC from TASK-0145's/
TASK-0149's own Done sections. No winner-selection self-check needed;
say so explicitly rather than building unnecessary machinery to mirror
TASK-0092's shape.

## Intent Contract

- Outcome: for each of the 3 mandatory targets, compute:
  - `transport.R_eff`, `transport.T_E` (`E=0`, pre-registered
    `gamma_lead`) on **holo** coordinates, holo-native seed/pocket.
  - `lowmode_predictor.prs_low`, `dcc_low` (`k_modes` in
    {5,10,15,20}) on **holo** coordinates, holo-native seed/pocket.
  Report holo AUC alongside each observable's already-recorded apo AUC
  (TASK-0145's/TASK-0149's own tables), the gap, and which failure
  explanation it supports — (a) apo-information-limited, (b)
  operator-limited, or neither cleanly (TASK-0092's own KRAS_G12C
  precedent: holo scored *worse* than apo there, a real third outcome,
  not assumed away).
- Why required: without this, "BCR_ABL1's transport win" and
  "CARDIAC_MYOSIN's lowmode win" have no upper-bound context — we don't
  know whether apo is already close to what the same operator could
  ever extract, or whether a holo-informed extension is worth pursuing
  for the proposal's future-work section.
- In Scope:
  - All 3 mandatory targets, both new operator families.
  - Reuse `_holo_native_labels` verbatim (import, not re-derivation),
    same as TASK-0092.
  - No new statistical methodology — same permutation-null/Bonferroni
    convention each observable's own Done section already established,
    applied to the holo-side numbers too (a holo AUC without any null
    context is just as uninterpretable as an apo one would be).
- Out Of Scope:
  - Any change to `transport.py`/`lowmode_predictor.py` themselves —
    pure application to a different coordinate set.
  - Re-running TASK-0067/TASK-0092's own GNM/CTQW holo comparison —
    already done, not repeated here.
  - The generalization-set targets (PTP1B/CASPASE7, [[TASK-0151]]'s own
    scope) — this task is holo-vs-apo on the mandatory 3 only, a
    different axis from TASK-0151's apo-only cross-target check.
- Constraints And Invariants: **diagnostic only, stated explicitly in
  every output** — per TASK-0092's own Context, a holo-side AUC can
  never be reported or treated as a submission prediction; it is a
  failure-attribution tool, full stop.
- Planned Validation: apo-vs-holo AUC + gap + permutation-null context,
  per target x observable; a failure-explanation table in the same
  shape as TASK-0092's own "Failure-explanation summary."

## TODO

- [x] New script (candidate name: `scripts/holo_diagnostic_transport_lowmode.py`),
      reusing `run_challenge._load_apo_holo`, `_holo_native_labels`,
      and `transport`/`lowmode_predictor`'s existing functions directly
      — no new scoring logic.
- [x] Run both observable families on holo coordinates, all 3 targets.
- [x] Permutation null on each holo-side cell (same convention as the
      observable's own apo-side Done section).
- [x] Apo-vs-holo comparison table + gap + explanation, per target x
      observable; explicit note when the result doesn't cleanly fit
      (a)/(b) (TASK-0092's own KRAS_G12C precedent — confirmed to recur,
      not a fluke, on 2 more cells here).
- [x] `RESULTS.md` section, cross-linked from TASK-0145's/TASK-0149's
      own Done sections, additive.

## Dependency

- [[TASK-0067]]/[[TASK-0092]] (Done) — the holo-diagnostic precedent and
  `_holo_native_labels` construction, reused not re-derived.
- [[TASK-0145]]/[[TASK-0149]] (Done) — the apo-side observables and AUCs
  this task compares against.

## Open Questions

- None — design resolved above (simpler than TASK-0092's two-pass
  shape, reasoning stated).

## Done

**Headline: mixed, real, and genuinely informative — includes a third outcome
(TASK-0092's own KRAS_G12C precedent: holo scores *worse* than apo) on two different
cells, plus one striking within-target divergence between `prs_low` and `dcc_low` on
CARDIAC_MYOSIN that needs its own honest flag, not smoothing over.**

### Simpler design confirmed correct, as this task's own Design note predicted

New `scripts/holo_diagnostic_transport_lowmode.py`. Confirmed directly (not assumed)
that neither `transport_observable_real_run.py` nor `lowmode_predictor_real_run.py`
goes through `run_frozen_verdict`/`select_frozen_config` — both score `transport`/
`lowmode_predictor`'s functions directly, with `E`/`gamma_lead`/`k_modes` fixed a
priori. Built a holo-side `prep` dict matching each apo-side script's own
`_prepare_target` shape (same keys: `pocket`, `H_for_diagnosis`, `bfactors`,
`floor_scores`, `n_residues` for transport; `pocket`, `shells`, `floor` for lowmode)
using `_holo_native_labels` (TASK-0067's own construction, imported verbatim) instead
of `build_labels`, then called `transport_observable_real_run._score`/
`lowmode_predictor_real_run._score_cell` directly, unmodified — zero new scoring
logic, exactly this task's own constraint. Seed: the full holo-native active-site
array (TASK-0118/INV-0006's current GAUGE, matching the apo-side scripts being
compared against), not TASK-0092's own older single-scalar choice.

### Transport apo-vs-holo

| Target | Quantity | Apo AUC (recorded) | Holo AUC | Gap | Holo p | Explanation |
|---|---|---|---|---|---|---|
| KRAS_G12C | `T(E=0)` on H_new | 0.640 | 0.296 | **−0.344** | 0.999 | **Neither (a) nor (b) cleanly** — holo scores *below chance*, the same "unexpected direction" TASK-0092 found for this exact target's CTQW/H_new pair. Not information-starved apo; something about this target's own proximity/geometry structure (TASK-0093/0094's own open question) present in both frames. |
| BCR_ABL1 | `T(E=0)` on L (TASK-0145's headline) | **0.698** (p=0.003) | 0.626 | −0.073 | 0.042 | **(b)** — operator-limited. Small gap, holo itself still nominally elevated (p=0.042) — consistent with the same mechanism carrying over to holo's own topology, not apo lacking information. Matches TASK-0092's own BCR_ABL1 CTQW reading (small gap → operator is the bottleneck). |
| CARDIAC_MYOSIN | `T(E=0)` on L | 0.456 | 0.313 | −0.143 | 0.991 | No apo signal to explain (this target never clears the floor for transport, TASK-0145's own finding) — holo doesn't rescue it either. |

Full 3-quantity × 3-target grid (9 cells) in the JSON; the table above reports each
target's own most informative cell (BCR_ABL1's headline; KRAS_G12C's sharpest
divergence; CARDIAC_MYOSIN's best apo cell, still non-significant).

### Lowmode apo-vs-holo (well-powered max AUC, k=20 — TASK-0149's own headline k;
full `{5,10,15,20}` grid in the JSON)

| Target | Observable | Apo (recorded) | Holo | Gap | Holo p | Explanation |
|---|---|---|---|---|---|---|
| CARDIAC_MYOSIN | `prs_low` (TASK-0149's headline) | **0.922** (p=0.006) | **0.902** | −0.020 | **0.003** | **(b), cleanly — near an information ceiling.** Holo *stays* Bonferroni-worthy-strong at every k (p=0.0000–0.0051 across all 4) with only a small gap — apo is already extracting almost all the signal the same operator could ever get from holo's own true structure. |
| CARDIAC_MYOSIN | `dcc_low` (TASK-0149's other headline) | **0.962** (p<0.001) | 0.659 | **−0.303** | 0.297 (not significant) | **Neither (a) nor (b) — a real, striking divergence from `prs_low`'s own reading on the identical target.** Holo loses significance at every k (p=0.07–0.30). Apo's own signal is *not* explained by "holo would do the same or better" here — if anything apo outperforms holo for this specific observable on this specific target, the opposite of what either failure mode predicts. Flagged, not smoothed into either bucket. |
| KRAS_G12C | `prs_low` | 0.595 (not significant) | 0.718 | +0.122 | 0.256 (not significant) | Holo direction is *positive* (weak evidence apo is mildly information-limited for this observable here) but neither side clears significance — underpowered (pocket_size=17), not decisive either way. |
| BCR_ABL1 | `dcc_low` | 0.518 (not significant) | 0.744 | +0.227 | 0.172 (not significant) | Same direction as KRAS_G12C's `prs_low` — holo consistently higher, closest at k=5 (holo p=0.073) — a real, if inconclusive, hint of headroom `dcc_low` might have on this target's holo structure specifically. |
| BCR_ABL1 | `prs_low` | 0.439 (not significant) | 0.246 | −0.193 | 0.996 | Holo scores markedly worse across every k — the "unexpected direction" pattern again, this time for `prs_low` on BCR_ABL1. |

### Interpretation

**CARDIAC_MYOSIN's `prs_low` result is now the best-attributed finding in the
project**: not only does it survive its own mandatory-3 Bonferroni bar and replicate
directionally in this diagnostic (holo stays strongly significant, small gap), it
also has a clean, textbook (b)-reading — apo is near an information ceiling for this
specific observable/target pair, not leaving obvious headroom a holo-informed
follow-on would recover. **`dcc_low` on the same target tells a different, harder-to-
interpret story**: its own strong apo signal does not carry over to holo at all, the
opposite of a clean information-ceiling reading. This is reported honestly as an open
complication, not resolved here (Out of Scope: no new mechanism investigation) —
candidate factors worth a future look, not concluded: CARDIAC_MYOSIN's own
apo/holo residue-count mismatch (704 apo vs 709 holo, `run_challenge._load_apo_holo`'s
own resolved counts) and this target's documented history of structural-remapping
sensitivity (TASK-0124/TASK-0144/TASK-0150). BCR_ABL1's transport headline gets a
clean (b) reading, corroborating TASK-0092's own established BCR_ABL1 pattern for a
third, independent operator family now. Two "unexpected direction" cells (KRAS_G12C
transport on H_new; BCR_ABL1 `prs_low`) reproduce TASK-0092's own KRAS_G12C precedent
that this is a real, recurring third outcome in this project's register, not a fluke.

**Per this task's own Constraint, restated**: none of these holo numbers are, or were
ever treated as, a submission prediction — purely diagnostic failure-attribution,
exactly as TASK-0067/TASK-0092 established.
