# Results — real end-to-end runs

Durable scientific record of what this pipeline has actually produced
against real RCSB data, kept **independent of the task-tracking system**.
Task files (`.ai/tasks/`) record *process* — who did what, when, what's
still open — and are archived/moved as work completes. This document
records *outcomes* — the numbers, the findings, and the open scientific
questions they raise — and stays put regardless of what happens to any
task. Whether a given hypothesis below ever gets its own task, gets
picked up later, or never does, is orthogonal to whether it belongs here.

**Status tags used throughout:**
- **[OBSERVED]** — a real, measured fact from a real run. Not in dispute.
- **[HYPOTHESIS — untested]** — a proposed explanation for an observed
  fact, not yet checked. Do not treat as established.
- **[HYPOTHESIS — testing]** — an investigation is filed/in progress.
- **[RESOLVED]** — an investigation concluded; the resolution is stated
  and dated.

Append new runs as new dated sections. Do not overwrite or delete a
prior run's numbers, even if a later run supersedes them — the
methodology delta between two runs of the same target is itself
sometimes the finding (see KRAS_G12C below).

**Reading order (TASK-0127, 2026-07-18): start with the ASD
generalization set, not the 3 mandatory targets.** By this point the
same 3 mandatory-target answer keys (KRAS_G12C, BCR_ABL1,
CARDIAC_MYOSIN) have been looked at across roughly 15 review cycles —
every gauge fix, every renormalization, every re-run in this document
was validated against numbers those same 3 targets produced. No
code-level gate (`frozen_context`/LOPO) catches that kind of repeated
exposure; only genuinely unseen targets can. The **"ASD generalization
set" section below** (4 targets: PTP1B, CASPASE7, CASPASE1, GLUCOKINASE
— none of which any review cycle in this document's history has ever
been shaped by) is this project's actual headline evidence for whether
a real signal exists. The mandatory-3 targets' numbers below remain
useful — they are where every mechanism (proximity confound, seed/clock
gauges, potential renormalization) was *found and diagnosed*, and they
still have to be reported as the challenge's required deliverable — but
read them as **supporting/mechanistic detail with a known repeated-
exposure history stated plainly**, not as the primary claim of whether
this approach generalizes. Per [[TASK-0115]]/[[TASK-0127]].

---

## Run 2026-07-12 — KRAS_G12C / BCR_ABL1 / CARDIAC_MYOSIN

**Mechanics**: `__WORK_IN_PROGRESS__/scripts/run_challenge.py` (TASK-0079.004),
real RCSB fetches, real `protocol.frozen_context`-gated selection and
scoring (TASK-0079.003), real `stamp_provenance` (TASK-0088). First time
the full Phase 0/1 fix set (TASK-0070/0052/0047/0063/0058/0055/0064/0071/0088)
has been exercised together, end-to-end, on live data. Output artifacts
(`connectivity_matrix.npz`, `hit_list.json`, `report.txt`, `verdict.json`)
are permanent files under `__WORK_IN_PROGRESS__/results/<target>/`, not
reproduced verbatim here — this document is the narrative/interpretation
layer over those files, not a replacement for them.

> **Note, 2026-07-20 (folder consolidation)**: `__WORK_IN_PROGRESS__/results/`
> and every `results_task*/`/`results_*/` sibling directory referenced
> throughout this document and in `.ai/tasks/DONE/`'s own historical Done
> sections are now consolidated under `__WORK_IN_PROGRESS__/RESULTS/`
> (e.g. `results_task0094/` → `RESULTS/results_task0094/`) — a repo
> reorganization, not a change to any script's own default output
> location naming. Historical path references elsewhere in this document
> and in already-Done task files are left as originally written (the
> paths were correct at the time), not rewritten in place; new output
> should land under the `RESULTS/` parent going forward. `.gitignore`
> updated to match.

**Methodology note that applies to every number below**: all scoring is
**apo-only**. The operator, the propagation, and the headline AUCs are
computed from the apo structure's topology alone; the holo structure is
used only to derive the ground-truth pocket label (what we're trying to
predict), never as an input to the prediction itself. This is
intentional and load-bearing, not an oversight — a real predictive
setting never has holo in advance (`PLAN.md`: "is the answer even in the
apo topology?"). Where holo-side numbers appear below they are always
explicitly framed as a **diagnostic upper bound**, never as "the real
signal" or a substitute for the apo prediction.

**Second methodology note, same scope [TASK-0097, REVIEW-2026-07-13
finding P2-B]**: every `AUC_ctqw_mean`/`AUC_apo_Hnew_*` number below is
computed via `propagators.time_averaged_ctqw` — the decoherent/infinite-
time-average limit of the walk (`Sum_k |v_k(j)|^2 |v_k(source)|^2`, a
spectral overlap between eigenvector components at the source and each
residue), **not a coherent quantum-walk snapshot**. All phase/coherence
information is averaged out by construction. This is consistent with,
not contradicted by, this repo's own flat-dephasing-sweep finding for
KRAS_G12C, and is a legitimate methodological choice — but it means the
headline "quantum metric" throughout this document is a spectral-overlap
quantity, stated here rather than left for a reader to discover.

### KRAS_G12C

| Quantity | Value |
|---|---|
| `AUC_apo_Hnew_default` / `_optimised` / `AUC_ctqw_mean` | **0.779** |
| `AUC_apo_H10_baseline` | 0.726 |
| `AUC_heat_mean` | 0.423 |
| `most_impactful_term` / `least_impactful_term` | V_R / V_T |
| `_diagnosis` | `NO_FAILURE_DETECTED` (cleared chance check and `degree_centrality` floor) |
| `enm_cutoff` used | 8.0 Å (`targets.yaml`) |

**[OBSERVED]** Top-5 hit-list resnums: 34, 35, 36, 11, 59. Cross-checked
against `backend/systems.py`'s independently-sourced `pocket_full[4.5]`
reference (21 residues, pinned by `test_labels.py`):
`{9,10,11,12,13,16,34,58,59,60,61,62,63,68,69,72,95,96,99,100,103}`.
**3 of 5 hits land directly in it** (34, 11, 59) — a real enrichment
against ~12% baseline prevalence, and not a trivial self-hit, since
`assemble_hit_list` already excludes active-site residues before
ranking.

**[HYPOTHESIS — testing, TASK-0093]** This 0.779 is inconsistent with a
result already documented and asserted elsewhere in this repository:
`test_analysis.py::test_kras_g12c_real_target_near_chance_and_flat_
dephasing` asserts `0.3 < AUC_apo_Hnew_default < 0.7` for this exact
target ("near chance even with the answer key") — this run falls outside
that band. Three real methodology differences exist between that test
and this run, none yet isolated:

1. Cutoff: 8.0 Å here vs. 10.0 Å there.
2. Pocket label: `build_labels`'s assembled `.pocket` (excludes
   active-site + terminal residues, TASK-0070) here vs. the *raw*
   `holo_pocket_mask` output there.
3. Propagation source: apo-native `functional_indices` (via
   `build_labels`) here vs. a holo-computed functional set cross-mapped
   to apo via `align_apo_holo` there.

**Neither number should be treated as "the" KRAS_G12C result until this
is resolved.** 0.779 is corroborated (floor-beating, independent
reference-set overlap), and 0.51–0.53 is corroborated (a real, previously
verified regression test). This is a genuine methodology-sensitivity
question, independent of which number eventually ships.

**[RESOLVED 2026-07-13, TASK-0094 — REVIEW-2026-07-13 finding P1-A
confirmed]** This section's `_diagnosis` above (`NO_FAILURE_DETECTED`,
"cleared... the `degree_centrality` floor") is now **superseded, not
merely re-interpreted**: the review found, and this task confirmed,
that `degree_centrality` was never the confounding variable —
proximity to the propagation seed is. Two proximity baselines
(`baselines.euclid_from_seed_centroid`/`hop_from_seed`) were added and
wired into the floor as "beat the strongest of all three candidates,
not just degree." Recomputed against the identical real data (AUC still
exactly 0.779 — nothing about the scoring itself changed, only the
floor it is checked against):

| Floor candidate | AUC |
|---|---|
| `degree_centrality` | 0.482 |
| `euclid_from_seed_centroid` | **0.798** |
| `hop_from_seed` | 0.781 |

**0.779 does not clear 0.798.** New `_diagnosis`: `BEATS_CHANCE_NOT_FLOOR`.
Per the review's own hard, non-negotiable acceptance criterion, **this
number must now be reported as geometry, not allosteric signal.** The
top-5 hit-list overlap with `pocket_full[4.5]` (above) is real, but is
the expected behavior of a proximity detector on a pocket that happens
to sit near the seed — not evidence the method found anything beyond
that.

This also **resolves** the TASK-0093 discrepancy immediately above, in a
more consequential way than either candidate methodology delta could
have: it no longer matters which of the three deltas (cutoff / pocket-
label definition / source definition) explains 0.779 vs. the previously-
asserted 0.51–0.7 band, because **neither number was ever floor-cleared
signal** once proximity is controlled for — 0.779 fails the real floor,
and 0.51–0.7 was already at chance. TASK-0093 remains open as a
narrower, still-real question (why do the two apo-only numbers differ
at all), but it no longer bears on whether KRAS_G12C shows real
allosteric signal from this pipeline: **it does not, under either
number.**

**[CORRECTED 2026-07-17, TASK-0112]** The 0.779-vs-0.798 margin above
(0.019) was reported as a decided point-estimate verdict with no
uncertainty attached — `diagnostics.classify_failure(return_ci=True)`
(new, `metrics.block_bootstrap_ci`, 1000 resamples, block size 10,
preserves spatial correlation in the residue ordering rather than a
naive i.i.d. bootstrap) now attaches one. Real re-run, same `H_new`
CTQW occupation, same `T_MAX=15.0` (this task does not also apply
TASK-0119's clock fix — conflating the two would make it impossible to
tell which change moved which number):

| Quantity | AUC | 95% CI |
|---|---|---|
| Score (`H_new` CTQW) | 0.779 | [0.594, 0.932] |
| Floor (`euclid_from_seed_centroid`) | 0.798 | [0.637, 0.936] |

**The two intervals overlap.** `BEATS_CHANCE_NOT_FLOOR` remains the
correct point-estimate category (this task does not change category
names or ordering, only annotates them) — but the honest statement is
**"statistically indistinguishable from the floor,"** not "fails the
floor by 0.019." Both readings support the same practical conclusion
already reached above (this is not confirmed signal), but for a
different, more defensible reason: not because 0.779 is decisively below
0.798, but because neither number is pinned down precisely enough, on
this target's ~20-30 real pocket positives, to say which is larger.
Full re-run: `scripts/bootstrap_ci_headline_rerun.py`,
`results_task0112/headline_ci_rerun.json`.

### BCR_ABL1

| Quantity | Value |
|---|---|
| `AUC_apo_Hnew_default` / `_optimised` / `AUC_ctqw_mean` | 0.525 (chance) |
| `AUC_apo_H10_baseline` | 0.558 |
| `AUC_heat_mean` (**same winning H_new operator**) | **0.731** |
| `most_impactful_term` / `least_impactful_term` | V_R / V_M |
| `_diagnosis` | `NO_SIGNAL_IN_APO` |
| `enm_cutoff` used | 8.0 Å |

**[OBSERVED]** Two axes, not to be conflated:
- Operator choice (H_new vs H10), both CTQW-propagated: gap −0.033,
  correctly called "noise-level" by the report itself.
- Propagator choice on the *same* H_new operator (CTQW vs
  `ground_state_relaxation`, formerly `heat`): gap −0.206. `_diagnosis` is
  computed only from CTQW's occupation vector (`run_frozen_verdict` passes
  `qvc["ctqw"]["occ"]` to `classify_failure`, never the other side's) — so
  `NO_SIGNAL_IN_APO` is a statement about CTQW specifically, not about
  BCR_ABL1 as a target.

**[CORRECTED 2026-07-13, TASK-0095 — see REVIEW-2026-07-13-proximity-
confound-and-propagator-semantics.md finding P1-B]** The line below
originally described the 0.731 result as produced by a classical diffusion
process, `propagators.heat`. That is a false physical claim: `H_new` is
indefinite by design (V_R/V_C/V_M contribute negative diagonals), and
`propagators.heat(H_new)` was never diffusing anything on this operator —
executed against real `build_H_new`, `Spearman(heat(H_new, t=20), |ground
state|^2) = 0.998`. The 0.731 number is real; the framing was wrong.

Precise summary (corrected): *on BCR_ABL1's optimized apo operator,
`H_new`'s ground-state density (via `ground_state_relaxation`, formerly
`heat`) produces a real, floor-beating signal while the time-averaged
coherent quantum walk does not. This is not a classical-vs-quantum
comparison — both sides are limits of the same operator's dynamics.*

**[RETRACTED 2026-07-13 — do not run TASK-0091 as originally framed]** The
paragraph below originally proposed testing whether calibrated
Haken-Strobl dephasing (`gamma: 0 -> large`) "recovers" 0.731 from CTQW's
0.525, reasoning that `gamma -> large` gives classical diffusion and 0.731
was already a diffusion-process number. That premise is false (see
above): the Haken-Strobl `gamma -> large` limit is a classical random walk
generated by `H`'s **off-diagonals**; `ground_state_relaxation(H_new)` is
dominated by `H_new`'s **diagonals** (the potential terms). The dephasing
sweep is structurally incapable of converging to `ground_state_relaxation`'s
value — it cannot "recover" 0.731, and a rising AUC under dephasing would
not have supported the ENAQT hypothesis this was meant to test, only an
unrelated coincidence dressed up as one. **TASK-0091 has been re-filed**
(different question: does `H_new`'s ground state localize on BCR_ABL1's
real, genuinely-distal pocket, tested directly and gated on TASK-0094's
proximity floor) rather than run as originally scoped. Original paragraph
kept below, struck through, for the record rather than deleted (this
document's own "do not overwrite or delete a prior run's numbers/findings"
convention):

> ~~**[HYPOTHESIS — testing, TASK-0091]** This is not already explained by~~
> ~~this repo's existing "coherence adds ~nothing" finding~~
> ~~(`test_kras_g12c_dephasing_flat_survives_kappa_calibration`) — that~~
> ~~result is CTQW vs. *progressively dephased* CTQW (Haken-Strobl,~~
> ~~`gamma: 0 -> large`) on KRAS_G12C. This finding is CTQW vs.~~
> ~~`propagators.heat` — a different classical diffusion process~~
> ~~(`exp(-Ht)`), not proven equivalent anywhere in this codebase to the~~
> ~~`gamma -> large` limit of Haken-Strobl dephasing, on a different target.~~
> ~~**KRAS's flat-sweep result does not predict what a calibrated dephasing~~
> ~~sweep would show for BCR_ABL1.** Testable hypothesis: if AUC rises from~~
> ~~approx. 0.525 toward approx. 0.731 as `gamma` increases through a calibrated range and~~
> ~~plateaus, that supports PLAN.md's own ENAQT hypothesis (coherent walks~~
> ~~localize on disordered graphs; calibrated dephasing reopens blocked~~
> ~~paths) as a real, target-specific effect worth pursuing. If AUC stays~~
> ~~flat, coherence isn't the lever here either and the KRAS pattern~~
> ~~generalizes. TASK-0091 runs this for real, reusing the KRAS test's exact~~
> ~~calibration recipe (`calibrate_kappa` → `mode_energetics` →~~
> ~~`gamma_scale`).~~

**[OBSERVED 2026-07-13, TASK-0094]** BCR_ABL1's `_diagnosis` above
(`NO_SIGNAL_IN_APO`) is unchanged by the proximity floor — CTQW's 0.525
never cleared chance, so the floor comparison never runs regardless of
what the floor is. But the floor candidates themselves are informative
here: `degree_centrality`=0.493, `euclid_from_seed_centroid`=0.541,
`hop_from_seed`=0.565 — **all three are also near chance.** This
corroborates (does not merely repeat) the "genuinely distal" framing
already used for this target: unlike KRAS_G12C, where proximity alone
nearly matches the method's score, BCR_ABL1's myristoyl pocket is far
enough from the seed that *even a pure proximity detector* cannot find
it. `ground_state_relaxation`'s 0.731 (above) is the one number on this
target that is not explained by proximity — TASK-0091 (re-filed) tests
it directly against this same floor.

**[RESOLVED 2026-07-13, TASK-0091]** It clears the floor, decisively —
the widest floor-clearing margin measured for any mandatory target this
session — but the localization is diffuse, not sharp, and both halves
must be reported together. Real run (fresh 1OPL/5MO4 fetch, real
`run_frozen_verdict`, not cached): `ground_state_relaxation`=0.7315 vs.
floor candidates `degree_centrality`=0.4933, `euclid_from_seed_centroid`
=0.5412, `hop_from_seed`=0.5652 — clears the strongest by **+0.166**.
Contrast KRAS_G12C above, which *failed* to clear its own floor by
-0.019. This is real, floor-beating signal on a genuinely distal
(~32 A seed-to-pocket) target, not proximity in disguise.

But: the top-5/10/20/30 ranked residues by `ground_state_relaxation`
occupation contain **zero** of the 16 labeled pocket residues — a
top-5 hit-list deliverable built from this score would completely miss
the pocket despite the good AUC. The signal is real but broad: pocket
residues' ranks span the 8.6th-54.8th percentile of the full 451-residue
ranking (median 20.1st percentile vs. 50th under chance), with
enrichment only becoming visible by top-50/top-75 (6%/31% of the pocket
found, vs. ~3.5% expected by chance at either cutoff). The nearest
top-20-occupation residues sit close (5-11 A) to one side of the pocket
(351-363, 448-456) but far (15-19 A) from the other side (481-487) —
consistent with highlighting an approach region adjacent to part of the
myristoyl site, not the full site. **Practical consequence, flagged not
acted on here:** switching the reported top-5 hit list from CTQW's
occupation to `ground_state_relaxation`'s would not improve BCR_ABL1's
hit list (still 0/5) even though it would improve the reported AUC — a
future per-target ranking-metric decision must check hit-list precision
separately from AUC, not assume one implies the other. Full numbers and
methodology: `.ai/tasks/DONE/TASK-0091-bcr-abl1-dephasing-sweep-investigation.md`.

**[CORRECTED 2026-07-17, TASK-0112]** "Clears the floor, decisively" above
was a point-estimate reading with no uncertainty attached. Real re-run
with `diagnostics.classify_failure(return_ci=True)` (`metrics.
block_bootstrap_ci`, same method as KRAS_G12C's correction above, same
`T_MAX=15.0`):

| Quantity | AUC | 95% CI |
|---|---|---|
| Score (`H_new` `ground_state_relaxation`) | 0.731 | [0.556, 0.866] |
| Floor (`hop_from_seed`) | 0.565 | [0.425, 0.697] |

**The two intervals overlap** — score CI's lower bound (0.556) sits below
floor CI's upper bound (0.697). The +0.166 point-estimate margin, the
widest floor-clearing margin measured for any mandatory target, is **not
statistically decisive** on this target's real positive count. This does
not reverse TASK-0102/TASK-0103/TASK-0104's mechanism finding below (GSR
tracks the potential well, not active-site coupling — that conclusion
rests on a controlled negative-control construction, not on this margin's
statistical significance) — it removes a support this section's own
point-estimate language leaned on ("decisively") that the data does not
actually carry. Full re-run: `scripts/bootstrap_ci_headline_rerun.py`,
`results_task0112/headline_ci_rerun.json`. (BCR_ABL1's CTQW-vs-floor
comparison, 0.525 vs 0.565, was already `NO_SIGNAL_IN_APO` pre-CI and
remains overlapping post-CI — no reversal, consistent.)

**[CORRECTED 2026-07-13, TASK-0102 — do not read the paragraphs above as
confirmed allosteric signal]** The finding above is corrected, not
retracted: the 0.7315 number and the floor-clearing margin are real and
unchanged. What changes is whether that margin means what the "not
proximity in disguise" framing above implies. **TASK-0102 tested whether
BCR_ABL1's real active site is actually special**, by rerunning
`ground_state_relaxation` on the same real, cached `H_new` from 40
arbitrary, biologically-uninformed single-residue seeds: **75.0% also
clear the same proximity floor**, 70.0% land within 0.02 of the real
active site's own AUC, and 20.0% score *higher* than the true active site
does. Mechanistically explained by `H_new`'s spectral gap at this run's
`t_max=15.0`: the ground eigenmode carries ~94.5% of the relative weight
(`exp(-gap*t_max)=0.055`), so most seeds' results are dominated by
`H_new`'s fixed ground-state shape rather than by genuine signal
transport from wherever propagation started. **The good AUC is
predominantly a property of the operator's ground state, not evidence of
active-site-to-pocket coupling specific to the true active site** — this
confirms, with real numbers, the "potential minimum has to be somewhere on
the protein" concern raised about this exact result. Full numbers and the
correlation-clustering detail (occupation *shape* does vary meaningfully
by seed, even though the resulting AUC mostly does not — a genuinely
nuanced result, not simple seed-independence): `.ai/tasks/DONE/TASK-0102-ground-state-relaxation-seed-invariance-test.md`.

**[FALSIFIED-AND-REFRAMED 2026-07-14, TASK-0104 — see
`REVIEW-2026-07-13b-operator-falsification-negative-controls.md` and
`.ai/tasks/TODO/TASK-0103-dumbbell-negative-control-suite.md` (the
regression test, passing)]** TASK-0102 (above) showed the 0.731 result is
mostly seed-independent; this correction supplies the **mechanistic
reason why**, via a decisive controlled experiment rather than a
statistical pattern over real-target seeds. A synthetic 2x2 control
matrix (44-node dumbbell: an active-site lobe bridged, by equal-length
paths, to a "true" coupled site and a decoy — well depth and bridge
coupling strength varied *independently*, so the two cues can be forced
to disagree) shows `ground_state_relaxation` **tracks the location of a
potential well, not the strength of coupling from the active site**: when
the well and the strong coupling are on opposite lobes, GSR scores the
*coupled* lobe 0.000 and the *decoy* (well-bearing, weakly-coupled) lobe
1.000 — the opposite of what a communication measure would do.
`time_averaged_ctqw`, tested on the identical synthetic construction,
does the reverse: it tracks the coupling and ignores the well. This is
not a difference of degree — it is a clean double dissociation,
regression-tested and passing (`test_dumbbell_negative_control.py`,
`TestDumbbellNegativeControl::test_c2_c3_is_a_clean_double_dissociation`
and the four single-cell assertions either side of it).

**The number does not change; the claim attached to it does.** The
corrected claim, replacing every prior "allosteric signal propagation" or
"communication from the active site" framing attached to this result:

> Allosteric pockets tend to coincide with soft, low-coordination
> regions. This is an apo-computable structural prior, detectable
> without reference to the active site.

This is a **cryptic-pocket-detection** claim — a legitimate, useful,
independently-defensible finding about *where soft/deep regions of the
apo structure sit* — and it addresses a **different** challenge
objective (structural-prior / pocket-druggability characterization) than
signal propagation does. It should be read and reported as such, in its
own section of any future submission narrative, not folded into the
CTQW/ENAQT communication story. `ground_state_relaxation`'s status in
this project's operator register (per the review's own falsification
template, Sec.5): **RETAINED-NARROWED** — falsified as a communication
detector, retained as a structural-prior detector.

The propagator-naming framing this document already
corrected once (TASK-0095, above — the "vs. quantum CTQW" comparison
against a diffusion-kernel misnomer) remains void for an added reason
beyond that naming/semantics fix: per the review's Sec.3, it was never a
meaningful classical/quantum comparison to begin with, regardless of
what either side is called.

**[OBSERVED 2026-07-14, TASK-0106 — real-data reproduction of
`REVIEW-2026-07-13c-ctqw-trapping-mechanism.md`, its own required gate
before that review's finding can change any claim]** Real BCR_ABL1
(1OPL/5MO4), `time_averaged_ctqw` through `H10_disorder_suppressed`,
`H2_combinatorial_laplacian`, `H_new` at reduced λ=0.25 (a uniform
external scale on `build_H_new`'s own five default per-term coefficients,
matching the review's own `H(λ) = L_norm + λ·ΣV` construction), and
`H_new` default, all seeded identically to this document's own existing
numbers (single, sorted-first, active-site residue — `run_challenge.py`'s
convention, not re-derived):

| Operator | AUC | Floor-cleared? (0.565) | PR/N | ⟨hop from seed⟩ |
|---|---|---|---|---|
| `H_new` default | **0.525** (exact match to this doc's existing number) | No | 0.299 | 0.89 |
| `H_new`, λ=0.25 | 0.463 | No | 0.449 | 1.23 |
| `H10_disorder_suppressed` | **0.558** (exact match) | No | 0.056 | 3.96 |
| `H2_combinatorial_laplacian` | 0.389 | No | 0.054 | 4.46 |

**The trapping *mechanism* reproduces cleanly on real data**: `H_new`'s
participation ratio (0.299) is 5-6× higher than `H10`/`H2`'s (0.056/
0.054) and its mean occupation-weighted hop-from-seed (0.89) is a quarter
of theirs (3.96/4.46) — the walk on `H_new` stays markedly closer to the
seed, exactly the Anderson-like localization the synthetic review found.
This is not seed-choice-dependent: a second run using the full active-site
residue set (not the single-index convention above) shows the same
direction (`H_new` PR/N=0.031 vs `H10`=0.015/`H2`=0.019 — still 1.6-2×
higher), even though the *AUC* values themselves differ substantially
under that seeding (see below).

**The predicted downstream consequence — that less-trapped operators find
the distal pocket better — reproduces only partially, and is sensitive to
a seed-definition choice that does not affect the mechanism above.**
Single-index seed (this document's own established convention): the
*sign* the review predicted holds for `H10` (0.558 > 0.525, the exact gap
already on record above, now confirmed not to be noise) but **not** for
`H2` (0.389 < 0.525 — the reverse) or for reduced-λ `H_new` (0.463 <
0.525 — reducing the trapping potential made this operator *worse*, not
better, at finding this pocket). **None of the four operators clear the
real proximity floor (0.565)** — `H10`'s higher number is real and not
noise, but it is not yet distinguishable from a proximity-driven result
either. Using the full active-site set as source instead (an equally
defensible seed choice, not the document's established one) inverts the
picture further: `H_new` default scores *highest* of the four (0.567),
opposite the review's prediction. **The finding is genuinely mixed, not a
clean reproduction or a clean falsification** — the mechanism (trapping)
is robust; its consequence for pocket-finding on this specific target is
not, and depends on a source-definition choice that has not previously
been treated as a meaningful knob. This is itself worth flagging per
`INVARIANCE_PROTOCOL.md`: "which residue(s) count as the seed" has been
implicitly a GAUGE choice throughout this pipeline and this task is the
first place it visibly changed a sign.
Script + full JSON: `scripts/ctqw_trapping_reproduction.py`,
`results_task0106/BCR_ABL1/reproduction.json`.

**[OBSERVED 2026-07-14, TASK-0105 — ENAQT γ-sweep on real targets, per
`REVIEW-2026-07-13b`'s §7 T-C, "the single highest-value experiment
available before the deadline"]** Measured `haken_strobl` transport
(total occupation probability mass landing on the labeled pocket, *not*
AUC — the review's own falsifiable signature is the interior-optimum
*shape*) across γ ∈ [10⁻⁴, 10²] on `H_new`/`H10`/`H2`, seeded from the
full active-site residue set (this task's own choice, not TASK-0106's
single-index convention — see that section's own note on why this
matters). **Computational-feasibility finding, not anticipated going
in:** `haken_strobl`'s dense N²-state Lindblad ODE costs ~11s/call at
N=169 (KRAS_G12C) and ~161s/call at N=451 (BCR_ABL1) — extrapolating the
measured N³ scaling puts CARDIAC_MYOSIN (N=950) at 30+ minutes *per
γ value*, making a real sweep on that target infeasible within a normal
session with the current dense-matrix implementation. KRAS_G12C ran a
full 8-point sweep; BCR_ABL1 a reduced 6-point sweep; CARDIAC_MYOSIN
computed only the free γ=0 (coherent) anchor. This is itself a finding
relevant to **TASK-0068**: `coarse.py`'s coarse-graining is exactly the
tool that would make a real sweep on CARDIAC_MYOSIN's scale tractable.

| Target | Operator | Interior optimum? | γ* | Enhancement vs γ→0 | AUC@γ* | AUC@γ→0 | Floor | Cleared@γ*? |
|---|---|---|---|---|---|---|---|---|
| KRAS_G12C (N=169) | `H_new` | No (flat) | 0.0001 | 1.00× | 0.465 | 0.466 | 0.482 | No |
| KRAS_G12C | `H10` | No (flat) | 0.0001 | 1.00× | 0.605 | 0.606 | 0.482 | **Yes** |
| KRAS_G12C | `H2` | **Yes** | 0.268 | **1.51×** | 0.337 | 0.384 | 0.482 | No |
| BCR_ABL1 (N=451) | `H_new` | **Yes** | 0.251 | **1.70×** | 0.560 | 0.573 | 0.582¹ | No |
| BCR_ABL1 | `H10` | No (flat) | 0.001 | 1.00× | 0.631 | 0.620 | 0.582¹ | **Yes** |
| BCR_ABL1 | `H2` | **Yes** | 0.251 | **1.24×** | 0.472 | 0.472 | 0.582¹ | No |
| CARDIAC_MYOSIN (N=950) | `H_new` | not swept | — | — | 0.799 | 0.799 | 0.792¹ | **Yes** (γ=0 only) |
| CARDIAC_MYOSIN | `H10` | not swept | — | — | 0.586 | 0.586 | 0.792¹ | No |
| CARDIAC_MYOSIN | `H2` | not swept | — | — | 0.611 | 0.611 | 0.792¹ | No |

¹ Computed with this task's own full-active-site-set seed, not TASK-0106's
single-index convention — not directly comparable to floor values quoted
elsewhere in this document for the same targets.

**Two real findings, reported as measured, not softened either way:**

1. **An interior γ-optimum in raw transport magnitude genuinely appears on
   real target topologies** — not just the review's synthetic
   construction. 3 of the 6 swept (target, operator) cells show a real
   optimum, with enhancement ratios of 1.24-1.70× over the coherent
   (γ→0) walk. This qualitatively reproduces the ENAQT signature the
   review predicted, on real protein contact graphs.
2. **That transport increase does not translate into better pocket
   discrimination.** In every one of the 3 cells with a genuine interior
   optimum, AUC-at-the-optimal-γ is *lower* than AUC-at-γ→0 (KRAS `H2`:
   0.337 vs 0.384; BCR_ABL1 `H_new`: 0.560 vs 0.573; BCR_ABL1 `H2`: 0.472
   vs 0.472, flat). More probability mass reaches the pocket *region*
   under dephasing, but not in a way that discriminates the true pocket
   residues from their non-pocket neighbors any better — if anything,
   slightly worse. **No target/operator cell crosses its proximity floor
   because of dephasing** — `H10`'s floor-clearing cells (KRAS, BCR_ABL1)
   already clear it at γ→0; dephasing does not add or remove a
   floor-crossing anywhere in this data.

γ* vs. structural disorder (`bfactor_std`, a cheap proxy, purely
observational per this task's own Constraints — not a claim, n=3 targets
is far too few for a real correlation): KRAS_G12C (`bfactor_std`=5.35,
γ*=0.268 on `H2`), BCR_ABL1 (`bfactor_std`=33.78, γ*=0.251 on `H_new`/
`H2`) — both interior optima land at a similar order of magnitude despite
a 6× difference in B-factor spread; no pattern worth naming with this
little data.
Script + full JSON: `scripts/enaqt_gamma_sweep.py`,
`results_task0105/<target>/sweep.json`.

### CARDIAC_MYOSIN

| Quantity | Value |
|---|---|
| `AUC_apo_Hnew_default` / `_optimised` / `AUC_ctqw_mean` | 0.786 |
| `AUC_apo_H10_baseline` | 0.766 |
| `AUC_heat_mean` | 0.790 |
| `most_impactful_term` / `least_impactful_term` | V_B / V_M |
| `_diagnosis` | **`INSUFFICIENT_RESOLUTION`** |
| apo residue count (N) | **950** |

**[OBSERVED]** Unlike BCR_ABL1, CTQW and `ground_state_relaxation` agree
closely here (0.786 vs 0.790, gap −0.003, "noise-level") — both
propagators concur, neither dominates. Given the well-vs-coupling
falsification above, agreement here is not itself evidence either
propagator is measuring communication on this target — it means the two
different quantities happen to coincide, which the dumbbell control
matrix's C1 cell ("cues agree") already showed is the *uninformative*
case, not a discriminating one. Hit-list resnums: 706, 89, 88, 704, 87
(two tight pairs); no independent reference pocket set exists for this
target to cross-check against.

**[OBSERVED, not a hypothesis]** `classify_failure` flags this result
`INSUFFICIENT_RESOLUTION` because apo N=950 exceeds `LARGE_N_THRESHOLD=800`
— the pipeline's own documented rationale: above that size, "the
anisotropic ANM channel is expected to dominate a scalar operator." This
is the honesty layer (TASK-0058/0071) catching its own stated limitation
automatically, on real data, for the first time — a positive validation
of the system working as designed, not a bug. Practical consequence:
**CARDIAC_MYOSIN's 0.786 should not be read the same way as KRAS's
flagged-clean 0.779** — it carries a built-in caveat the pipeline itself
attached, whereas KRAS's discrepancy (above) has no such automatic
disqualifier and remains a genuinely open question. `targets.yaml`'s own
data-quality warning about apo 5TBY (a 20 Å cryo-EM multi-chain
assembly, "NOT resolved... trusting the apo Cα graph uncritically" named
as a risk) is corroborated by this independent, code-level signal —
two different mechanisms (a human-written data-quality note and an
automated resolution-threshold check) converging on the same caution
about this target.

**[OBSERVED 2026-07-13, TASK-0094]** `classify_failure` never reaches
the floor check for this target (`INSUFFICIENT_RESOLUTION` short-circuits
first), so its `_diagnosis` is unaffected by the new floor — but the
numbers are worth recording since they were computed anyway:
`degree_centrality`=0.630, `euclid_from_seed_centroid`=0.749,
`hop_from_seed`=0.764. **0.786 would clear all three** if the large-N
flag did not short-circuit first. This does not un-flag the result (the
resolution caveat above is independent and still applies), but it means
CARDIAC_MYOSIN's number, unlike KRAS's, is not *also* explainable by the
proximity confound — its open question remains the large-N/ANM-channel
caveat specifically, not geometry.

**[CORRECTED 2026-07-15]** The `LARGE_N_THRESHOLD=800` claim just above
("above that size, the anisotropic ANM channel is expected to dominate a
scalar operator") was checked directly against its cited source
(`notebooks/H_new_engineering (4) CLEAN.ipynb` cell 56) and found to have
**no derivation anywhere** — that inline comment is the entire
justification given, with no formula, citation, or measurement of
scalar-vs-anisotropic divergence as a function of N in the notebook or
this codebase. It was an unfalsified physics claim, not a derived
threshold, and it disqualified CARDIAC_MYOSIN — a mandatory challenge
target — with no argument for why N=950 specifically breaks the model.
Per explicit user direction (2026-07-14): reframed `diagnostics.py`'s
threshold as what it actually is, a **computational-scaling ceiling**
(dense `eigh`/`eigvalsh` is O(N³); 1000 is chosen only to sit just above
CARDIAC_MYOSIN's real N with headroom, exactly as arbitrary as 800 was,
now documented as such rather than dressed up as principled — see the
constant's own comment in `diagnostics.py` for the full account), not a
claim about model validity at this size. Real data recomputed
end-to-end (`scripts/run_challenge.py --target CARDIAC_MYOSIN`,
`scripts/sweep_operators.py --target CARDIAC_MYOSIN --force`):

- **AUC values are unchanged** (0.786 / 0.766 / 0.790, hit list
  unchanged: 706, 89, 88, 704, 87) — this correction only changed which
  diagnosis check the identical numbers are subjected to.
- `_diagnosis` changes from `INSUFFICIENT_RESOLUTION` to
  **`NO_FAILURE_DETECTED`** — 0.786 genuinely clears the proximity floor
  (max 0.764, already computed above) now that the large-N short-circuit
  no longer fires first.
- **This is what the "Zero of three" headline below now looks like
  corrected** — see that section's own `[CORRECTED 2026-07-15]` note.
- Full 32-cell operator × propagator sweep re-run under the corrected
  threshold (`results/CARDIAC_MYOSIN/operator_sweep.md`): 14 of 30 valid
  cells (H13's 2 cells still error, unrelated 3N-shape issue) now clear
  the floor, **11 of them via `ctqw`** — `H2`, `H3`, `H4`, `H5`, `H6`,
  `H8`, `H10`, `H11`, `H12`, `H_new`, `build_H10`, all `ctqw`, all
  `NO_FAILURE_DETECTED`. This directly contradicts the operator-sweep
  register's previous headline ("zero of 96 cells clear the floor via
  `ctqw`", TASK-0101) — that claim was built on CARDIAC_MYOSIN data that
  was silently disqualified by the same uncited threshold. See
  `.ai/tasks/DONE/TASK-0101-operator-sweep-tier1-harness.md`'s own
  addendum for the corrected register-wide count.

**What this correction does NOT resolve**: the *separate*,
independent 5TBY cryo-EM data-quality caveat two paragraphs above (20 Å
resolution, multi-chain assembly, `targets.yaml`'s own "NOT resolved...
trusting the apo Cα graph uncritically" warning) is untouched by this
fix and remains a real, open concern — this correction retires the
large-N/ANM-channel claim specifically, not every caveat CARDIAC_MYOSIN
carries. Do not read this block as "CARDIAC_MYOSIN is now fully
vindicated."

### Cross-target pattern worth naming, not yet a hypothesis with a test attached

**[OBSERVED]** Two of three targets (KRAS_G12C 0.779, CARDIAC_MYOSIN
0.786) scored well above the "near chance" pattern this project's
existing documentation leads with; only BCR_ABL1 (0.525) matches that
prior expectation. CARDIAC_MYOSIN's high score has its own sufficient,
already-identified explanation (large-N flag, above) and is not evidence
of the same effect driving KRAS's number. Whether KRAS's and
CARDIAC_MYOSIN's high scores share any *other* common cause (e.g. the
`enm_cutoff=8.0` used uniformly by this run, vs. the 10.0 default older
tests used) is exactly what TASK-0093 isolates for KRAS; it has not been
checked for CARDIAC_MYOSIN and is not claimed here.

### Proximity floor applied (TASK-0094, 2026-07-13) — [RESOLVED] the pattern above *is* the confound

**[RESOLVED]** `REVIEW-2026-07-13-proximity-confound-and-propagator-
semantics.md` finding P1-A hypothesized that the cross-target pattern
above ("two good scores, one at chance") was the signature of a
proximity-to-seed detector, not an allosteric one, and set a hard,
non-negotiable acceptance criterion: *a target's AUC may only be
reported as signal if it clears a real proximity floor, not merely
chance and degree.* `baselines.euclid_from_seed_centroid`/`hop_from_seed`
were added, wired into `classify_failure`'s floor (now the max AUC
across `{degree_centrality, euclid_from_seed_centroid, hop_from_seed}`,
not `degree_centrality` alone), and all three mandatory targets were
re-run against the identical apo data (no AUC changed — only the floor
they are checked against did):

| Target | AUC | Floor-cleared? | `_diagnosis` |
|---|---|---|---|
| KRAS_G12C | 0.779 | **No** (max floor 0.798) | `BEATS_CHANCE_NOT_FLOOR` |
| BCR_ABL1 | 0.525 | N/A — never clears chance | `NO_SIGNAL_IN_APO` |
| CARDIAC_MYOSIN | 0.786 | Yes (max floor 0.764) — moot, N=950 flag fires first | `INSUFFICIENT_RESOLUTION` |

**Zero of three mandatory targets currently ship a floor-cleared,
resolution-clean apo-only AUC.** Per the review's acceptance criterion,
this is the honest headline of this pipeline's current state, not a
setback to be minimized: KRAS_G12C's apparent signal is geometry
(proximity to the seed), BCR_ABL1 was already at chance, and
CARDIAC_MYOSIN's favorable floor-clearance is undermined by an
independent, already-flagged data-quality problem. This is exactly the
"gates before build" framing `PLAN.md` calls for — a well-evidenced "our
apo-only pipeline does not yet show real distal signal on the mandatory
set" is the legitimate, reportable result of this run, not a failure to
paper over. It also directly blocks (per TASK-0094's own Dependency
section) every downstream task that would have consumed these AUCs as
established signal — TASK-0082 (competence map), TASK-0068 (NISQ sim),
TASK-0015 (holo-direction), TASK-0046 (ceiling search), TASK-0081
(generalization set) — until a method clears this floor for real.

**[CORRECTED 2026-07-15]** CARDIAC_MYOSIN's "moot, N=950 flag fires
first" row above is superseded — see the CARDIAC_MYOSIN section's own
`[CORRECTED 2026-07-15]` block (`LARGE_N_THRESHOLD` had no derivation,
corrected 800→1000). Re-run against identical apo data:

| Target | AUC | Floor-cleared? | `_diagnosis` |
|---|---|---|---|
| CARDIAC_MYOSIN | 0.786 | **Yes** (max floor 0.764) | `NO_FAILURE_DETECTED` |

**One of three mandatory targets now ships a floor-cleared,
resolution-clean apo-only AUC** — CARDIAC_MYOSIN, via `H_new`, both
propagators (`AUC_ctqw_mean`=0.786, `AUC_heat_mean`=0.790). KRAS_G12C
and BCR_ABL1's rows above are unaffected by this correction (neither
result depended on `LARGE_N_THRESHOLD`) and stand as originally
reported. **This does not retroactively validate every downstream task
this section blocked** — CARDIAC_MYOSIN still carries its independent
5TBY cryo-EM data-quality caveat (unresolved 20 Å structure), and the
tasks named above (TASK-0082/0068/0015/0046/0081) were scoped and, in
several cases, already executed against the *old* "zero of three"
premise — whoever picks those back up should check whether this
correction changes their scope, not assume it does or doesn't.
`.ai/tasks/DONE/TASK-0101-operator-sweep-tier1-harness.md` also needs
its own "zero of 96 cells clear via ctqw" headline corrected (11 of
CARDIAC_MYOSIN's cells now clear via `ctqw` alone) — flagged there, not
fixed here, since that finding fed directly into
`REVIEW-2026-07-13c`'s CTQW-trapping conclusion and correcting it is a
scientific-synthesis decision, not a documentation fix.

### Diagnostic upper bound not yet computed

**[HYPOTHESIS — testing, TASK-0092]** `AUC_holo_Hnew_optimised`,
`mean_rho_apo_holo`, and `mean_jacc20` are `N/A` for all three targets —
`run_frozen_verdict` already supports the holo-side kwargs
(TASK-0079.003), `.004`'s orchestrator just doesn't wire them yet
(deliberate scope cut, not an oversight). `TASK-0067` already ran the
apo-vs-holo comparison once, for the bare GNM-Kirchhoff operator (no
potential terms): the gap was tiny (KRAS +0.009, BCR_ABL1 −0.020),
an order of magnitude smaller than the cutoff/weight-scheme spread being
measured there. That finding has **not** been checked for the full
`H_new` pipeline (potential terms, CTQW, real winning-candidate
selection) used in this run. TASK-0092 is that check. Framing to
preserve: a small apo/holo gap on `H_new` would mean the
propagator/operator is the bottleneck (more apo data wouldn't help); a
large gap would mean these targets have genuinely cryptic pockets apo
cannot see — the more interesting biological story, and a legitimate
"NO" per `PLAN.md`'s own "gates before build" framing, not a failure to
hide.

### NISQ noise-model simulation (TASK-0068, 2026-07-14) — closes SEAM-0010

**[OBSERVED]** `HOLO_DIRECTION_MODULE.md`'s named scoreable NISQ result —
"is dephasing-assisted transport (ENAQT) more noise-robust than coherent
CTQW under realistic gate noise" — measured for real, on a real
coarse-grained target (`coarse.coarse_grain`'s own output, not a
re-derived graph), via a new module (`src/allostery/noise.py`) and script
(`scripts/nisq_noise_simulation.py`).

**Method**: KRAS_G12C's real `H_new` (apo, cutoff 8.0 Å) coarse-grained
(Louvain, seed=0, `coarse.coarse_grain`) to **10 qubits**. One qubit per
node, single-excitation-subspace XY-model encoding of the walk (per-edge
`RXX(w·dt)`+`RYY(w·dt)`, exact — not a Trotter approximation at the
single-edge level, since `[XX, YY] = 0`) — this makes the noiseless
circuit a real gate-model reproduction of `propagators.ctqw` restricted
to `H_coarse`, not an unrelated toy walk. Depolarizing error on every
2-qubit gate + amplitude damping per Trotter layer
(`qiskit_aer.noise.NoiseModel`, `AerSimulator(method="density_matrix")`,
exact — no shot noise). ENAQT realized as an *additional* per-layer
phase-damping channel (γ=0.3), compared against the same gate-noise model
with no added dephasing (the coherent case) — both swept across the
*same* depth/error-rate grid so the comparison is apples-to-apples.

**GAUGE/KNOB/SIGNAL classification (required before any degradation
number is reported, per this task's own Constraint)**: Louvain
coarse-graining seed — KNOB (changes cluster membership, fixed at seed=0,
declared not defaulted-silently); qubit-to-cluster-index labeling —
GAUGE (arbitrary, carries no physical content — `cluster_labels` written
out alongside every result, not implied); `AerSimulator` method
(`density_matrix`, exact) — KNOB; depolarizing/amplitude-damping
probabilities — SIGNAL (the sweep's own x-axis); `dephasing_gamma` — the
second SIGNAL, the coherent-vs-ENAQT comparison itself. Full table in the
script's own module docstring.

**Computational-feasibility finding (found empirically, not
anticipated)**: `coarse.trotter_cost`'s own step-count estimate at
`error_budget=0.01` is **3133 Trotter steps** for this 10-qubit graph —
calibrated for high-fidelity simulation *accuracy*, not a NISQ-realistic
circuit. A first attempt using that literal estimate (and half/double of
it) produced a ~188,000-gate circuit that did not finish in 6m45s/69
CPU-minutes and was killed, not silently waited out. **This gap is itself
informative**: it means the depth genuinely required for accurate
simulation is roughly 2-3 orders of magnitude beyond what any real NISQ
device (or a reasonable local density-matrix simulation) can run — the
noise-robustness question this task asks can only be studied at a
depth far short of "faithful simulation," which is exactly the NISQ
regime the task is about. The sweep actually run uses a small,
NISQ-plausible grid (2/5/10 Trotter steps) instead, with `trotter_cost`'s
real estimate reported alongside it as that gap, not hidden.

**Result — coherent is never worse than ENAQT, across every depth/error-
rate point tested, at two different total-evolution times (t=1.0 and
t=25.0, the latter matching TASK-0105's own timescale where a real
interior-γ transport optimum was found):**

| depth | error rate | coherent top-3 overlap | ENAQT top-3 overlap | more robust |
|---|---|---|---|---|
| 2 | 0.00 | 1.000 | 1.000 | tie |
| 2 | 0.01 | 1.000 | 1.000 | tie |
| 2 | 0.05 | 1.000 | 0.500 | **coherent** |
| 5 | 0.00 | 1.000 | 0.500 | **coherent** |
| 5 | 0.01 | 1.000 | 0.500 | **coherent** |
| 5 | 0.05 | 0.500 | 0.500 | tie |
| 10 | 0.00 | 1.000 | 0.500 | **coherent** |
| 10 | 0.01 | 0.500 | 0.200 | **coherent** |
| 10 | 0.05 | 0.200 | 0.200 | tie |

(t=25.0 spot-check, depths 10/20, same qualitative pattern — coherent
ties or beats ENAQT at every point, never loses.)

**This is a real, honest negative result for this task's own headline
question, reported as such — not the hoped-for NISQ story.** Under this
specific gate-noise model (depolarizing + amplitude damping, per-2-qubit-
gate and per-layer respectively) and this specific encoding (single-
excitation XY-model walk), adding deliberate dephasing on top of already-
present gate noise does not help, and sometimes measurably hurts,
top-k ranking fidelity — the *extra* decoherence from the ENAQT channel
adds to, rather than compensates for, the gate noise already present.
This does not contradict TASK-0105's own real-target finding (a genuine
interior-γ transport-magnitude optimum exists in the noiseless/
Haken-Strobl continuous-time picture) — it says that optimum, measured
against a *different* (already-noisy) baseline in a discrete gate-model
circuit, does not translate into a *noise-robustness* advantage here.
Both are real findings about different questions, not in tension.

**Scope actually run**: one real target (KRAS_G12C, the cheapest of the
three), one operator (`H_new`), one coarse-graining (Louvain, 10 qubits).
Not run: BCR_ABL1/CARDIAC_MYOSIN, `H10`/`H2` coarse-grained comparisons,
a spectral coarse-graining cross-check. The noise-simulation *mechanism*
(`src/allostery/noise.py`, tested on synthetic graphs,
`test_noise.py`, 13 passing) is this task's real deliverable; one real
run demonstrates it end to end and answers the headline question with
real data, matching this project's precedent of not re-deriving a full
3-target sweep inside a single subtask when the tooling itself is the
point.
Script + full JSON: `scripts/nisq_noise_simulation.py`,
`results_task0068/KRAS_G12C/noise_sweep.json`.

---

### Coherence sensitivity wired into the verdict (TASK-0099, 2026-07-16)

**Question**: `dephasing_sweep` (Haken-Strobl AUC-vs-γ) was implemented and
tested (KRAS_G12C only, `test_kras_g12c_dephasing_flat_survives_kappa_
calibration`) but had **zero call sites** in `protocol.py`/`report.py` --
every AUC in every `RESULTS.md` entry above is built exclusively from
`time_averaged_ctqw` (phase-averaged by construction) and
`ground_state_relaxation` (real exponential, no oscillation). Switching
off quantum coherence entirely would not have changed a single reported
number. This task formalizes the answer: `analysis.coherence_sensitivity`
wires a calibrated dephasing sweep (γ from `superpose.calibrate_kappa` +
`anm_modes` + `mode_energetics`'s `relaxation_time`, swept at
`{0, 0.5, 1, 2} × gamma_scale`) into `assemble_verdict_results`/
`verdict_template`, gated against TASK-0094's proximity floor
(`classify_failure`, reused not reinvented) so a raw-AUC wiggle that never
changes the floor-cleared verdict is reported as geometry-confounded, not
oversold as a quantum finding. Classification is `COHERENCE_NOT_SIGNIFICANT`
(auc_range < 0.05, `dephasing_sweep`'s own already-documented flat
threshold, reused rather than inventing a second magic number) or
`COHERENCE_DEPENDENT_SIGNAL` (non-flat AND the floor-cleared status
actually flips somewhere in the sweep).

**KRAS_G12C — real result (active-site multi-index source,
target-config `enm_cutoff`, `H_new`, t_max=25 -- see clock-robustness
note below):**

| γ (rad, calibrated) | AUC | diagnosis |
|---|---|---|
| 0 (coherent) | 0.4658 | NO_SIGNAL_IN_APO |
| 0.00706 | 0.4570 | NO_SIGNAL_IN_APO |
| 0.01412 | 0.4573 | NO_SIGNAL_IN_APO |
| 0.02824 | 0.4525 | NO_SIGNAL_IN_APO |

`auc_range = 0.0132`, `is_flat = True`, floor = 0.482 (max of degree /
euclid-from-seed / hop-from-seed baselines) → **`COHERENCE_NOT_SIGNIFICANT`**.
KRAS_G12C doesn't even clear chance here (all four points
`NO_SIGNAL_IN_APO`), consistent with this target's own already-established
near-chance default-parameter result. A second cross-check using the
GDP-functional-site single/multi-index source (matching
`test_kras_g12c_dephasing_flat_survives_kappa_calibration`'s own
convention exactly, different `gamma_scale=0.0202` from a hardcoded
`cutoff=10.0`, t_max=8) gives `auc_range=0.0076`, same conclusion — the
finding is not an artifact of one particular source convention.

**Clock-robustness check (2026-07-16, prompted by
`REVIEW-panel-2026-07-16-v2` Sec.2.2 -- "`t_max=15` is unfixed and too
short... a precondition for the physics, not hygiene," and TASK-0108/0109's
formal convergence check is still TODO):** the script originally used
`t_max=8` (copied from the pre-review KRAS-only dephasing test, not
re-derived). Spot-checked directly against real KRAS_G12C data at
`t_max ∈ {8, 25, 100}` (25 matches TASK-0105's own already-established
"long enough to reach each gamma's long-time regime" convention for this
same `haken_strobl` sweep; 100 is a 12x-wider control):

| t_max | auc_range | is_flat | classification |
|---|---|---|---|
| 8 | 0.0155 | True | COHERENCE_NOT_SIGNIFICANT |
| 25 | 0.0132 | True | COHERENCE_NOT_SIGNIFICANT |
| 100 | 0.0247 | True | COHERENCE_NOT_SIGNIFICANT |

The **coherence-sensitivity conclusion is robust to the clock choice** —
`t_max=25` was adopted as the script's primary reported value on this
basis (not `t=8`). Note this does *not* resolve the review's broader
point: the *absolute* per-gamma AUC's chance/floor diagnosis does shift
with `t_max` (e.g. some points read `BEATS_CHANCE_NOT_FLOOR` at `t=8` vs.
`NO_SIGNAL_IN_APO` at `t=25`/`100`) — that general AUC-vs-clock gauge
problem is real, applies project-wide, and is explicitly out of this
task's scope (TASK-0108/0109's job). What TASK-0099 can and does claim is
narrower and holds regardless: *varying γ at a fixed, reasonable t_max
never changes the outcome*, at every t_max tested.

**Seed-gauge caveat (`REVIEW-panel-2026-07-16-v2` Sec.2.1):** the review
flags source/seed cardinality (single residue vs. full active-site array)
as an unfixed gauge worth up to ±0.3 AUC project-wide, with no registered
invariant. This task's own cross-check above (active-site array vs.
GDP-functional single/multi-index) used two different, real seed
conventions and got the same `COHERENCE_NOT_SIGNIFICANT` conclusion under
both — reassuring for this specific question, but not a resolution of the
project-wide gauge issue, which remains a separate, unaddressed P0 item
(seed-convention invariant registration + a unified floor/ceiling/actual
re-run) outside this task's scope.

**BCR_ABL1 / CARDIAC_MYOSIN — blocked, not silently skipped:**
`superpose.calibrate_kappa`/`anm_modes` `raise ValueError` unless *exactly*
6 near-zero rigid-body ANM modes are found (TASK-0005's own hardening).
BCR_ABL1 finds 7, CARDIAC_MYOSIN finds 10 — both raise before `gamma_scale`
can be computed, at the target-config `enm_cutoff` for each. TASK-0005's
own Done section already predicted this exact failure mode ("a genuinely
multi-chain/floppy-linker target... might legitimately have more than 6
near-zero-but-not-exactly-zero modes... worth revisiting this strictness
once a multi-chain target is actually run through this module") — filed as
[[TASK-0128]] rather than patched inline here (root cause -- genuine
floppiness vs. an actual disconnected contact graph vs. a numerical
threshold artifact -- is undetermined and `calibrate_kappa` is TASK-0005's
owned module, out of this task's scope to silently loosen). Both targets
report `error: "expected exactly 6 near-zero rigid-body ANM modes, found
7/10..."` (caught, not crashed) rather than any `coherence_classification`
value — an honest "not run", not a guessed or omitted result. See
`scripts/coherence_sensitivity_scan.py`.

**[RESOLVED 2026-07-17, TASK-0128]** Root cause diagnosed directly, not
assumed: both targets' "extra" eigenvalues sit at true machine-precision
zero (~1e-16, indistinguishable from the 6 trivial rigid-body modes),
then jump 5-9 orders of magnitude to the real low-frequency spectrum —
not a smooth continuum blending into the zero cluster (rules out a
`1e-8`-threshold numerical artifact), and the underlying scalar contact
graph is confirmed connected (`operator_diagnostics` on the 3N Hessian:
`n_components=1` for both) — not TASK-0005's original disconnected-graph
bug. The corresponding eigenvectors localize almost entirely onto a
small, compact residue segment (BCR_ABL1: ~10 residues near 198-207,
chain A; CARDIAC_MYOSIN: all 4 extra modes on the same ~17-residue
segment, 819-835, chain B) — the known artifact of a purely central-force
(distance-only) ANM model: a locally under-constrained substructure can
have exact zero-energy internal rotational modes without the structure
being disconnected. `superpose.anm_modes`/`calibrate_kappa`'s assertion
widened from `n_zero != 6` to `n_zero >= 6`, with the disconnected-graph
case still caught explicitly via a connectivity check (not silently
loosened) — TASK-0005's own original regression re-verified directly
against real numbers (a synthetic 2-cluster graph: `n_zero=12`,
`n_components=2`, still raises).

**Both targets now calibrate and, where feasible, run**:

| Target | `gamma_scale` | Sweep | `auc_range` | Classification |
|---|---|---|---|---|
| BCR_ABL1 | 7.41e-4 | full 4-point | 0.0050 | `COHERENCE_NOT_SIGNIFICANT` |
| CARDIAC_MYOSIN | 9.38e-3 | γ=0 anchor only (pre-existing, unrelated `haken_strobl` cost limit — TASK-0105's own ~30+ min/call estimate at N=950, not a TASK-0128 blocker) | N/A | `INFEASIBLE_NOT_RUN` |

**BCR_ABL1's conclusion matches KRAS_G12C's exactly**: flat across all 4
swept γ values (`auc_range=0.0050`, well under the 0.05 flatness bar),
every point floor-cleared (`NO_FAILURE_DETECTED`), `COHERENCE_NOT_
SIGNIFICANT`. **This is now 2 of 3 mandatory targets formally confirming
"coherence adds ~nothing," not 1 of 3** — strengthens, not just repeats,
TASK-0099's own headline finding. (The `gamma=0`/coherent-CTQW AUC here,
0.756, uses this script's own full-active-site-array seed convention and
`t_max=25`, both different from several other numbers reported elsewhere
in this document for BCR_ABL1 under the single-index/`t_max=15`
convention — a real, already-tracked methodology axis (TASK-0118/
TASK-0119/TASK-0129's "combined seed+clock re-run", still outstanding),
not a new discrepancy introduced here.) CARDIAC_MYOSIN's `gamma_scale`
now computes successfully (confirms the calibration blocker specifically
is resolved), but its full sweep remains not-run for the separate,
pre-existing computational-cost reason — an honest "not run" for a
different, already-documented reason, not silently converted into a
result it doesn't have. Full numbers: `.ai/tasks/DONE/TASK-0128-
calibrate-kappa-exact-6-mode-assertion-blocks-multichain-targets.md`.

**Verdict-template rendering**: a new line 5 ("Coherence sensitivity...")
renders whenever `coherence_auc_range`/`coherence_classification` are
present, alongside the existing 4 decision-support lines — visible in the
same report a judge reads, not an internal-only computation.

Script: `scripts/coherence_sensitivity_scan.py`. Tests:
`test_analysis.py::TestCoherenceSensitivity` (7 synthetic cases, including
2 that force the floor-gate's flip/no-flip branches via monkeypatched
propagators) + `test_kras_g12c_coherence_sensitivity_reproduces_kappa_
calibration` (real data, reproduces the ~0.0035-order-of-magnitude flat
finding through the new formal wiring, not a fresh silently-diverging
computation).

---

### Optuna floor/ceiling parameter scan (TASK-0110, 2026-07-17) — the clock is not 100x too short, it is 145,000x-3,950,000x too short, and reaching convergence is currently uncomputable

**[OBSERVED]** An Optuna-based apo-only ("floor," no ground truth,
objective = `propagators.check_convergence`'s convergence-quality
criterion) and holo-informed ("ceiling," objective = real AUC) scan of
`time_averaged_ctqw`'s numerical parameters (`t_max`, `n_steps`), real
compute, all 3 mandatory targets. Seed convention: `ceiling.py`'s own
full active-site array (matches TASK-0046 exactly, for a clean
cross-check — not TASK-0118's newer `coherent=False` incoherent-mixture
convention, flagged explicitly as a caveat, not silently mixed).

**Headline finding 1 — the clock gap, measured not estimated.** The
smallest `t_max` at which `time_averaged_ctqw`'s own decoherent-limit
criterion holds (`tol=1%`, AAKV-style all-pairs-min-gap bound) on real
`H_new`:

| Target | N | Required `t_max` | vs. shipped default (15.0) |
|---|---|---|---|
| KRAS_G12C | 169 | 4.82e6 | **320,000x** |
| BCR_ABL1 | 451 | 2.18e6 | **145,000x** |
| CARDIAC_MYOSIN | 950 | 5.92e7 | **3,950,000x** |

An independent Optuna search (200 trials/target) cross-validates these
closed-form values within 1.3-2.5% on every target — two independent
methods, same answer.

**Headline finding 2 — genuine convergence is not just unperformed, it
is currently uncomputable.** The `n_steps` matching each `t_max` above
is in the millions (KRAS_G12C 1.28e7, BCR_ABL1 7.06e6, CARDIAC_MYOSIN
2.00e8). `time_averaged_ctqw` evaluates its time grid in an explicit
Python loop, O(n_steps) — a single real call at KRAS_G12C's prescribed
point **did not return after 2+ hours** (confirmed still actively
computing, not hung, before being killed). "Fix the clock" (this
project's own stated P0 priority, `REVIEW-panel-2026-07-16-v2.md` §2.2)
is therefore not a parameter change that can simply be applied to the
shipped `t_max=15.0`/`n_steps=500` defaults — it requires either an
algorithmic change to `time_averaged_ctqw` (the decoherent infinite-time
limit this pipeline already treats it as equivalent to, per this
document's own P2-B methodology note above, has a cheap closed form,
`Σ_k|v_k(j)|²|v_k(source)|²`, no time loop at all) or permanently
accepting a `t_max` far short of true convergence.

**Headline finding 3 — per-target practical (honestly, not aliased,
sampled) ceilings**, restricted to the `t_max` range where `n_steps`
stays computationally tractable (a cap of 20,000 steps; every trial
outside this range is flagged `n_steps_capped` and excluded from the
number below, not silently included):

- **KRAS_G12C**: 0.4750 at `t_max=278.8` — near chance. **Cross-checks
  TASK-0046's independent ceiling (0.5239-0.5250)** — same seed
  convention, different parameter axis (physical `H_new` weights vs.
  numerical propagation time), same conclusion: no recoverable ceiling
  for KRAS_G12C under this seed convention, on either axis.
- **BCR_ABL1**: 0.5829 at `t_max=2.39` — notably *smaller*, not larger,
  than the shipped default. A genuine, unexploited-headroom finding, not
  predicted by any prior task in this document — worth a dedicated
  follow-up (Tier-2/operator-selection gated, `TASK-0100`, not decided
  here).
- **CARDIAC_MYOSIN**: 0.8149 at `t_max=7.67` — high, but inherits this
  target's already-documented 5TBY data-quality caveat (20 A cryo-EM
  docked homology model, flagged UNRESOLVED in `targets.yaml`) — not a
  new positive result, a numerical-parameter-axis confirmation of an
  already-known, already-caveated one.

Full detail, trial histories, and the `optuna`-dependency/search-design
notes: `.ai/tasks/DONE/TASK-0110-optuna-apo-holo-parameter-scan.md`,
`results_task0110/<target>/scan.json`, `src/allostery/optuna_scan.py`.

---

## Learnability gate (HYP-P8), 2026-07-17 — TASK-0120

**Is the labeled pocket even present in the apo topology, independent of
any operator or propagator choice?** `REVIEW-panel-2026-07-16-v2.md`
Sec.6 called this "the highest information-per-hour experiment
available" — first real execution of `HYP-P8`
(`.claude/hypotheses/physics.md`, filed 2026-06-21, never run until now;
the "resolved" language in that file's own 2026-07-15 status update was
built entirely from *indirect* evidence — seed-sensitivity/localization
findings on other tasks — not from this direct measurement).

Method: Kabsch-superpose holo onto apo (`superpose.align_apo_holo`),
per-residue apo→holo Cα RMSD at the labeled pocket vs. background
(non-pocket) residues (`superpose.cryptic_openness_gate` +
`background_rmsd`, new), and Tama-Sanejouand cumulative overlap of the
displacement onto the apo ANM's lowest 20 modes
(`superpose.cumulative_overlap`). Classified via the panel's own kill
criterion, made precise (`superpose.learnability_verdict`): pocket RMSD
≥1.5× background RMSD **and** cumulative overlap <0.5 → `UNLEARNABLE_
FROM_APO`; otherwise `LEARNABLE`. Real fetch, all 3 mandatory targets
(`scripts/learnability_gate.py`, `results_task0120/learnability_gate.json`).

**[UPDATED 2026-07-18]** Cumulative overlap for BCR_ABL1/CARDIAC_MYOSIN
was blocked at first run (below); [[TASK-0128]]'s fix to the shared
`anm_modes` helper unblocked both the same day it was filed. Table
below now shows the complete, real numbers for all 3 targets — the
`blocked`/`PARTIAL_RMSD_ONLY` values immediately below this note are the
original, at-first-run numbers, preserved per this document's own no-
overwrite convention, not deleted now that the full picture exists.

| Target | N (common) | Pocket RMSD | Background RMSD | Ratio | CO(20) | Verdict |
|---|---|---|---|---|---|---|
| KRAS_G12C | 169 (166) | 1.863 Å | 0.820 Å | **2.27** | **0.638** | `LEARNABLE` |
| BCR_ABL1 | 451 (429) | 0.362 Å | 0.734 Å | **0.49** | **0.794** | `LEARNABLE` |
| CARDIAC_MYOSIN | 950 (709) | 4.168 Å | 3.161 Å | 1.32 | **0.584** | `LEARNABLE` |

**All 3 mandatory targets now classify `LEARNABLE`** — for BCR_ABL1 and
CARDIAC_MYOSIN this confirms, rather than changes, what the RMSD half
alone already implied (neither cleared the 1.5× ratio bar), since this
task's kill criterion requires *both* conditions. Original at-first-run
table (CO blocked for 2 of 3 targets) preserved below:

| Target | N (common) | Pocket RMSD | Background RMSD | Ratio | CO(20) | Verdict |
|---|---|---|---|---|---|---|
| KRAS_G12C | 169 (166) | 1.863 Å | 0.820 Å | **2.27** | **0.638** | `LEARNABLE` |
| BCR_ABL1 | 451 (429) | 0.362 Å | 0.734 Å | **0.49** | blocked ([[TASK-0128]]) | `PARTIAL_RMSD_ONLY` |
| CARDIAC_MYOSIN | 950 (709) | 4.168 Å | 3.161 Å | 1.32 | blocked ([[TASK-0128]]) | `PARTIAL_RMSD_ONLY` |

**[OBSERVED] KRAS_G12C's result directly contradicts the panel's own
stated expectation, and is reported as such, not softened.** The panel's
§4 biological framing calls KRAS "the textbook cryptic case" and
predicts HYP-P8 should hold ("if HYP-P8 holds for KRAS specifically...
the apo graph does not encode this pocket, a publishable finding").
Measured directly: the pocket **does** displace more than background
(ratio 2.27, clears this task's own 1.5× bar) — consistent with a
cryptic/induced-fit opening — **but the cumulative overlap onto the
apo ANM's soft modes is 0.638, well above the 0.5 "low overlap" bar**,
meaning the apo→holo direction *is* substantially spanned by the
low-frequency mode subspace. Per this task's own kill criterion (both
conditions required), KRAS_G12C classifies `LEARNABLE`, not
`UNLEARNABLE_FROM_APO`. This does not contradict the panel's separate,
independent point (Switch-II is built from the catalytic region, so
active/allosteric sites geometrically overlap on this target) — that is
a labeling/observable-design problem, orthogonal to whether the *apo
structure itself* spans the opening direction. The two explanations are
not mutually exclusive, but only one of them is what this measurement
actually tests, and the direct test says "the direction is there," not
"the direction is absent." Whoever next reframes KRAS's failure (e.g. in
a submission narrative) should cite *this* result for "is it in the apo
topology" and the panel's Sec.4 point separately for "is the label even
well-posed" — they are different claims with different evidence.

**[OBSERVED] BCR_ABL1's pocket moves *less* than background (ratio
0.49) — the opposite direction from a cryptic-opening signature, and
consistent with, not contradicting, this project's own prior finding**
(TASK-0102/TASK-0103/TASK-0104: `ground_state_relaxation`'s BCR_ABL1
signal is an "apo-computable structural prior," not induced conformational
change). A pocket that is already comparatively rigid/pre-formed in the
apo structure is exactly what a low relative pocket RMSD would look
like. Cumulative overlap is blocked (TASK-0128), but the RMSD half of
the kill criterion already fails on its own (ratio <1.5, let alone the
`≪` a cryptic case would need) — `PARTIAL_RMSD_ONLY`, and the available
half points toward learnable/pre-formed, not cryptic.

**[OBSERVED] CARDIAC_MYOSIN's numbers should be read alongside its own
independent 5TBY data-quality caveat, not in place of it** (per this
task's own In Scope note) — background RMSD itself is large (3.16 Å,
vs. KRAS's 0.82 Å and BCR_ABL1's 0.73 Å), consistent with a genuinely
floppier structure or a lower-quality alignment (only 709 of 950
residues have a common apo/holo correspondence, the lowest coverage of
the three targets, and overall alignment RMSD is 3.75 Å vs. KRAS's 1.36
Å and BCR_ABL1's 0.98 Å) — this target's pocket-vs-background ratio
(1.32) should not be read as a clean structural-biology result the way
KRAS/BCR_ABL1's can.

**[RESOLVED 2026-07-17, superseded by the 2026-07-18 update above]**
TASK-0128 blocked cumulative overlap for 2 of 3 targets at this task's
first run, not worked around here. `anm_modes`' exactly-6-near-zero-
rigid-body-mode assertion raised on BCR_ABL1 (n_zero=7) and CARDIAC_
MYOSIN (n_zero=10) — confirmed live, this run. That task's own scope
(determine floppiness vs. genuine disconnection before touching the
assertion) was real diagnostic work this task did not preempt;
`scripts/learnability_gate.py` degraded gracefully (reported the RMSD
half, marked CO `null` with the exact exception,
`verdict="PARTIAL_RMSD_ONLY_CO_BLOCKED"`) rather than silently dropping
the whole target or guessing a widened threshold.

**[RESOLVED 2026-07-18]** TASK-0128 found the root cause (a genuine,
localized central-force-ANM under-constrained-substructure artifact on
both targets, not disconnection or numerical noise) and widened
`anm_modes`' criterion accordingly — since that function is shared code,
this task's own blocked cumulative-overlap computation is unblocked as a
direct consequence, not a separate re-run. Both extra CO values (0.794,
0.584) land above the 0.5 threshold, same qualitative conclusion the
RMSD-only numbers already pointed to.

Full detail: `.ai/tasks/DONE/TASK-0120-learnability-gate-hyp-p8.md`,
`results_task0120/learnability_gate.json` (includes the full CO(m) curve
for KRAS_G12C, not just the final value).

**[UPDATED 2026-07-19, [[TASK-0133]]] The `CO(20)` values in the tables
above are a *whole-structure* quantity, not a pocket-specific one — a
real, load-bearing finding, not a restatement.** Checked directly
against real data: `delta_r`'s length in `learnability_gate.py` equals
`3 * len(alignment.apo_idx)` (166-709, the *entire* common apo/holo
correspondence set), not `3 * n_pocket_residues` (13-18). The reported
`CO(20)` therefore measures how well the apo ANM's low-frequency modes
explain the *whole conformational change*, not specifically the
pocket's own opening direction — a materially different claim than
"the pocket's displacement is spanned by the soft modes," which is what
`learnability_verdict`'s own framing (and the panel's) reads it as.

[[TASK-0133]] built a genuinely pocket-restricted CO(m)
(`superpose.restricted_cumulative_overlap`, zero-pads the residue
subset's displacement into the full 3N ANM space and projects onto the
untouched orthonormal eigenvectors directly — **not** by naively
slicing+renormalizing eigenvectors the way `cumulative_overlap` does,
which was found, mid-task, to silently break `CO(m) <= 1` for a small
subset: real pocket-sized subsets gave values up to 1.64, a
mathematically invalid "overlap fraction," root-caused to a synthetic
3-of-50-residue case before being trusted on real data) and compared it
against 1000 random same-sized patches per target, drawn from the same
common correspondence set:

| Target | Pocket size | Restricted pocket CO(20) | Whole-structure CO(20) (original) | Random-patch CO(20) (mean±std) | Pocket percentile | One-sided p |
|---|---|---|---|---|---|---|
| KRAS_G12C | 18 | **0.458** | 0.638 | 0.341 ± 0.075 | 93.0th | ≈0.07 |
| BCR_ABL1 | 16 | 0.175 | 0.794 | 0.199 ± 0.059 | 37.3th | ≈0.63 |
| CARDIAC_MYOSIN | 13 | 0.044 | 0.584 | 0.074 ± 0.032 | 12.6th | ≈0.87 |

**Headline, stated directly: this control only matters for KRAS_G12C —
the one target whose `learnability_verdict` actually depends on the CO
half of the conjunction** (BCR_ABL1 already fails the RMSD-ratio bar at
0.49<1.5, and CARDIAC_MYOSIN at 1.32<1.5, so their verdicts are
RMSD-determined regardless of CO). For KRAS_G12C, the *properly
pocket-restricted* CO(20) is **0.458 — below `learnability_verdict`'s
own `co_threshold=0.5`**, the opposite side of the threshold from the
whole-structure proxy's 0.638 that produced the original `LEARNABLE`
verdict. Had this task's corrected measurement been used in place of
the whole-structure proxy, KRAS_G12C's `co_low` condition would flip to
`True`, and combined with its already-`True` `rmsd_much_greater`
(ratio 2.27), the conjunction would classify `UNLEARNABLE_FROM_APO` —
reversing TASK-0120's headline verdict for the panel's own "textbook
cryptic case."

**Not silently reclassified — the random-patch control itself says this
isn't a clean flip either way.** KRAS_G12C's pocket CO (0.458) is real
and elevated relative to the random-patch null (93rd percentile, mean
0.341) — the pocket is not indistinguishable from a random same-sized
region — but a one-sided p≈0.07 does not clear this project's own
established significance bar (uncorrected 0.05, let alone
Bonferroni-corrected across targets, [[TASK-0131]]'s own precedent). So
neither the original whole-structure "0.638, comfortably above
threshold, LEARNABLE" reading nor a flipped "0.458, below threshold,
UNLEARNABLE" reading is fully supported without a caveat: the fixed
0.5 threshold applied to either quantity is doing more work than the
underlying statistical evidence decisively supports for this target.
Per this task's own Out Of Scope, `learnability_verdict`'s threshold
logic is not changed here — this is the concrete finding for whoever
next revisits KRAS_G12C's `LEARNABLE` classification to act on.

BCR_ABL1 and CARDIAC_MYOSIN's pockets score *below* their own
random-patch medians (37th and 13th percentile) — the real pocket is
less well explained by the soft-mode subspace than a typical
same-sized random region, the opposite of "broadly expressive/no
discrimination." Their verdicts are unaffected either way (RMSD-
determined), but this is a real, target-specific asymmetry worth
recording: CO does discriminate between regions on these two targets,
just not in the pocket-favoring direction, and not in a way that
changes anything currently reported.

Full detail: `.ai/tasks/DONE/TASK-0133-learnability-gate-random-patch-control.md`,
`results_task0133/learnability_gate_patch_control.json`.

**[RESOLVED 2026-07-20, [[TASK-0139]]] KRAS_G12C's classification decided: `AMBIGUOUS`,
not `LEARNABLE`.** TASK-0133 left the contradiction above "reported, not decided." This
task resolves it on two points, both argued from first principles (not picked for
convenience):

1. **Which CO quantity `learnability_verdict` should use — settled in favor of the
   pocket-restricted one.** The RMSD half of this same conjunction is already
   pocket-vs-background, i.e. region-specific by design (per TASK-0120's own Intent
   Contract: "per-residue apo→holo RMSD... at the labeled pocket vs. background"). A
   whole-structure CO answers a different, easier question than the panel's own kill
   criterion (§6) asks — "does the low-mode subspace span *some* substantial motion
   somewhere," not "does it span *this pocket's* motion" — and would let a large,
   well-explained motion elsewhere in the structure mask a genuinely anharmonic pocket
   opening. Mixing a region-specific RMSD half with a whole-structure CO half within one
   AND-conjunction was never internally consistent; both halves must be about the same
   region. `superpose.learnability_verdict`'s docstring updated to require the restricted
   quantity; both real call sites already compute it (`restricted_cumulative_overlap`,
   TASK-0133).
2. **Whether `co_threshold=0.5` needs recalibration — yes, replaced by a direct null test
   where one is available.** Confirmed directly: `co_threshold=0.5` was never validated
   against *any* real null, whole-structure or restricted (`cumulative_overlap_gate`, its
   only other consumer, also never validates it — TASK-0120's own admission: "not derived
   from literature"). TASK-0133 built exactly the null this threshold was always missing
   (the random-patch distribution). New `superpose.learnability_verdict(..., co_percentile=
   ..., significance_alpha=0.05)` (ADD-only — `None` default is byte-identical to every
   prior call): when a percentile is supplied, the CO half is tested against the null
   directly (two-tailed at `alpha=0.05`, this project's own established bar, TASK-0131's
   precedent) instead of the bare, un-derived threshold. A percentile landing in neither
   tail is the CO evidence being genuinely inconclusive — and when the RMSD half has
   already cleared its own bar (as KRAS_G12C's has), that inconclusiveness is the finding,
   not grounds to force a binary call: verdict is `AMBIGUOUS`, a real third category next
   to `LEARNABLE`/`UNLEARNABLE_FROM_APO`.

**Applied to real data (`scripts/resolve_kras_learnability.py`, reruns the already-real,
already-verified TASK-0120/0133 numbers through the corrected function — no new expensive
computation, same inputs, corrected criterion):**

| Target | RMSD ratio | RMSD clears? | Restricted CO(20) | Percentile in null | Original verdict | **Resolved verdict** |
|---|---|---|---|---|---|---|
| KRAS_G12C | 2.27 | Yes | 0.458 | 93.0th | `LEARNABLE` | **`AMBIGUOUS`** |
| BCR_ABL1 | 0.49 | No | 0.175 | 37.3th | `LEARNABLE` | `LEARNABLE` (unchanged — CO half never reached) |
| CARDIAC_MYOSIN | 1.32 | No | 0.044 | 12.6th | `LEARNABLE` | `LEARNABLE` (unchanged — CO half never reached) |

**KRAS_G12C's headline changes from "contradicts the panel's own textbook-cryptic-case
prediction, LEARNABLE" to "genuinely undetermined by this measurement."** Neither the
panel's own prediction (`UNLEARNABLE_FROM_APO`) nor TASK-0120's original reframe
(`LEARNABLE`) is supported at this project's own evidentiary bar — the RMSD half is real
and decisive (pocket moves 2.27× background), but the CO half's own elevation over a
random-patch null (93rd percentile) falls short of significance (two-tailed p≈0.14,
one-sided p≈0.07) in either direction. This is reported as the honest answer, per this
project's own "an honest don't-know is a publishable result" convention — not as a
retreat from TASK-0120's own real, correctly-computed RMSD measurement, which stands
unchanged.

Full detail: `.ai/tasks/DONE/TASK-0139-kras-learnability-reclassification-decision.md`,
`results_task0139_learnability_resolution/resolution.json`,
`scripts/resolve_kras_learnability.py`.

---

### `H_new`'s 5-term potential variance-budget renormalization (TASK-0121, 2026-07-18)

**[EXECUTED, fixes a real bug]** `REVIEW-panel-2026-07-16-v2.md` §2.4 found
that `potentials.py`'s five diagonal terms (V_B/V_T/V_R/V_C/V_M) were not
commensurately scaled before being combined: `V_R` is a sum of three
z-scores (measured std ~1.9 on real targets), while `V_C`/`V_M` were
max-normalised to `[-1, 0]` (measured std ~0.06) — ~30x smaller. This made
`V_R` alone carry **88.8%** of the combined potential's variance (`V_T`
8.5%, `V_B` 2.5%, `V_C` 0.1%, `V_M` 0.1%) *regardless* of the `lam_*`
weight ratio in `build_H_new` — `lam_C`/`lam_M` were unreachable knobs.

This retro-explains three things this project previously reported as
physics findings, not a normalization artifact: `most_impactful_term =
V_R` in every prior ablation run, the ground state sitting on
low-diagonal (high-degree) residues, and `H_new`'s failure to beat degree
centrality (`V_R` correlates with node degree at ρ=+0.81 by construction).
**This is a distinct confound from the proximity confound in the scored
*output*** (CTQW occupation vs. degree correlates at only ρ=+0.20,
per §2.3) — degree contaminates the diagonal (fixed here), proximity
contaminates the observable (not fixed by this task; see [[TASK-0123]]).

**Fix:** every term in `potentials.py` (`V_B`, `V_T`, `V_R`, `V_C`, `V_M`)
is now z-scored (mean 0, std 1) as its final step. `build_H_new`'s
`lam_*` defaults are re-derived to `lam_B=0.08, lam_T=0.16, lam_R=0.08,
lam_C=0.04, lam_M=0.04` — the same 1:2:1:0.5:0.5 ratio as before, rescaled
so `sigma(V) <= 0.2*J` is a provable guarantee for *any* target: by the
triangle inequality on standard deviations (Minkowski), `sigma(sum lam_i *
V_i) <= sum |lam_i|` when each `V_i` has std 1, and the symmetric
normalized Laplacian's spectral bandwidth satisfies `J <= 2` for any
nonnegative edge weighting — so `sum|lam_i| = 0.4 = 0.2*2` is a
target-independent worst-case bound, not a per-target fit.

**[EXECUTED] Real-data confirmation (KRAS_G12C, N=169; BCR_ABL1, N=451):**

| Target | J (base Laplacian bandwidth) | σ(V) combined | 0.2·J budget | Naive variance share B/T/R/C/M |
|---|---|---|---|---|
| KRAS_G12C | 1.317 | 0.203 | 0.263 | 15.4% / 61.5% / 15.4% / 3.8% / 3.8% |
| BCR_ABL1 | 1.480 | 0.227 | 0.296 | 15.4% / 61.5% / 15.4% / 3.8% / 3.8% |

The variance share is structural (same on every target, since each term
now has std 1 by construction and the share is set entirely by the
`lam_*` ratio) — a **38x** improvement for `V_C`/`V_M` (0.1% → 3.8%) over
the pre-fix budget, from unreachable to actually contributing. `H_new`
remains correctly indefinite on both targets (KRAS min eig -0.101, BCR_ABL1
min eig -0.177) — `_warn_if_indefinite` still fires as designed; this fix
did not accidentally push the operator toward PSD.

**[EXECUTED] Re-ran `analysis.ablation` on both targets** at the pipeline's
current shipped `t_max=15.0`/`n_steps=500` (deliberately *not* also
applying [[TASK-0119]]'s gap-based clock fix here — that is a separate,
independent confound per this task's own scope, and mixing the two fixes
in one measurement would make it impossible to attribute any change in
`most_impactful_term` to renormalization specifically). **Caveat, checked
directly, not assumed:** none of the 6 per-term operators (`L_only`, `B`,
`T`, `R`, `C`, `M`) satisfy `check_convergence`'s AAKV criterion at these
parameters on either target (bound exceeds tol by 2-3 orders of magnitude)
— same pre-existing clock gap [[TASK-0110]] already quantified, unrelated
to this fix.

| Target | most_impactful_term (pre-fix, on record) | most_impactful_term (post-fix) | least_impactful_term (post-fix) |
|---|---|---|---|
| KRAS_G12C | V_R | **V_B** (ΔAUC +0.133) | V_R (ΔAUC +0.017) |
| BCR_ABL1 | V_R | **V_B** (ΔAUC +0.097) | V_T (ΔAUC +0.036) |

`most_impactful_term` flips from `V_R` — the term that was structurally
inflated — to `V_B` on both real targets; `V_R` drops to the *least*
impactful term on KRAS_G12C. This is exactly the retro-explanation
predicted above: the ablation now measures something for the first time,
rather than reproducing an artifact of the old scale mismatch.

**Not solved by this task:** the proximity confound in the CTQW
observable itself (§2.3) — a real-data side-measurement during this task
(the existing `TestProximityConfoundReproduction` regression test) shows
the renormalization *does* substantially weaken it in practice (Spearman
ρ with Euclidean seed-distance: 0.71-0.83 pre-fix → 0.22-0.47 post-fix on
the same 5 synthetic-globule seeds; hop-distance: 0.55-0.64 → 0.03-0.28),
but it remains positive on every seed tested — proximity is weakened, not
eliminated, consistent with the panel's warning not to claim this fix
resolves the observable-side confound. `TASK-0117` (apply the convergence
check to `ceiling.py`'s own literal `t_max=15` defaults) also remains open.

Full detail: `.ai/tasks/DONE/TASK-0121-renormalize-potential-variance-budget.md`.

---

## ASD generalization set — headline evidence (TASK-0081 + TASK-0127, 2026-07-18)

**[EXECUTED] This is the section to read first (see the reading-order
note at the top of this document).** 4 targets from the Allosteric
Database, none of which any prior review cycle in this project's ~15-
cycle history has ever seen or been shaped by, each independently
RCSB-verified (real chain IDs and real hetero-ligand records checked
directly against RCSB, never trusted from either source doc — the same
discipline that caught PTP1B's YAML-unquoted-numeric-ligand bug in
TASK-0081) and run through the **current, fully gauge-fixed pipeline**
([[TASK-0118]] seed convention, [[TASK-0119]] per-operator clock,
[[TASK-0121]] renormalized potential — all landed):

| Target | N | Pocket size | Actual AUC | Max floor (95% CI) | CI overlap | Diagnosis | most_impactful_term |
|---|---|---|---|---|---|---|---|
| PTP1B | 298 | 14 | **0.2050** | 0.4847 [0.242, 0.591] | Yes | `BEATS_CHANCE_NOT_FLOOR` | V_C |
| CASPASE7 | 461 | 7 | 0.6463 | 0.7542 [0.575, 0.959] | Yes | `BEATS_CHANCE_NOT_FLOOR` | V_T |
| CASPASE1 | 255 | 6 | 0.8119 | 0.9070 [0.776, 0.976] | Yes | `BEATS_CHANCE_NOT_FLOOR` | V_B |
| GLUCOKINASE | 448 | 17 | 0.7713 | 0.8531 [0.767, 0.921] | Yes | `BEATS_CHANCE_NOT_FLOOR` | V_C |

All four deliverables (connectivity matrix, top-5 hit list, report,
verdict) verified present and well-formed for all 4 targets — same
acceptance bar as the mandatory set, no lighter-touch standard for this
"headline" set (`results_task0127/<target>/`).

**Headline finding: 4/4 generalization targets land in the same
`BEATS_CHANCE_NOT_FLOOR` category the mandatory set's KRAS_G12C already
occupies, and all 4 CIs overlap their own floor's CI** — none
statistically decisive (same non-decisive pattern [[TASK-0112]] found
for the mandatory set). This is the strongest form of the cross-target
pattern this project has assembled: raw AUC without a proximity floor
overstates apparent signal, on genuinely unseen targets, not just the
3 whose numbers have been repeatedly re-examined. PTP1B remains the
most striking single result — **0.205 is not merely below its floor,
it is anti-correlated with the true pocket** (well below 0.5), on a
genuinely distal allosteric site (~20 A from the catalytic Cys215,
structurally the same category as BCR_ABL1's myristoyl site) — the same
finding TASK-0081 reported, now confirmed under the fully gauge-fixed
pipeline (was 0.2497 pre-fix, now 0.205 post-fix — same direction,
slightly stronger).

**`most_impactful_term` is never `V_R` on any of the 4 targets**
(V_C, V_T, V_B, V_C) — independent cross-validation of
[[TASK-0121]]'s finding on data that fix's own validation never touched:
the pre-TASK-0121 `V_R`-dominance pattern was a normalization artifact,
not something specific to the 3 mandatory targets' own topology.

**CASPASE1 and GLUCOKINASE are new additions this task (TASK-0127),
not carried over from TASK-0081.** Of TASK-0081's 6 remaining draft
candidates (ATCase, CASPASE1, HEMOGLOBIN, TAR_RECEPTOR,
GLYCOGEN_PHOSPHORYLASE, PFK), independently RCSB-verified this task:

- **CASPASE1**: passes. Same dimer-interface-allostery mechanism class
  as CASPASE7 (chains `[A,B]` required); holo (2FQQ) is clean (ligand
  F1G, a real small molecule, confirmed present, chain B). Apo (1ICE)
  carries an unrelated active-site peptide-aldehyde inhibitor
  (Ac-YVAD-CHO, chain T, excluded by the `[A,B]` chain selection) —
  flagged as a caveat (not ligand-free) but does not corrupt the
  allosteric-pocket label, which is derived from holo contacts and
  UniProt active-site annotation, neither of which depends on what apo
  happened to crystallize with.
- **GLUCOKINASE**: passes, but required a real schema fix, not just
  RCSB verification. TASK-0081 already found (2026-07-15) that apo
  (1V4S) uses chain A and holo (3H1V) uses chain X — both source docs
  were individually correct, for different structures — but
  `targets.yaml`'s single `chains` field couldn't express a per-role
  chain mapping, raised as `Q-0001` and left in `draft`. This task adds
  optional `apo_chains`/`holo_chains` override fields to
  `clean_from_config` (additive, falls back to `chains` when absent —
  every other target's config is provably unaffected, see
  `test_clean.py`), resolves `Q-0001`, and graduates GLUCOKINASE to
  `verified`.
- **ATCase, HEMOGLOBIN, GLYCOGEN_PHOSPHORYLASE, PFK**: all fail
  independent verification, each for a *different*, real, substantive
  reason (not the same failure repeated): ATCase's deposited structures
  only have 4 of the full dodecamer's 12 chains, missing the regulatory
  subunits that carry the allosteric site entirely. HEMOGLOBIN's own
  apo/holo pair has no BPG (the target ligand) in either structure, and
  is a T-state/R-state pair rather than an unbound/bound one.
  GLYCOGEN_PHOSPHORYLASE's "apo" (1GPY) already has G6P bound — a
  competing allosteric effector at the *same* regulatory site as the
  intended AMP ligand, so it is not apo for the site of interest. PFK's
  apo (1PFK, ~320 res/chain) and holo (3O8L, ~748 res/chain) differ so
  much in size they may not even be the same protein, and apo already
  has FBP (the intended allosteric ligand) bound regardless. None of
  these are backfilled with a weaker pick to hit a round number — same
  discipline TASK-0081 used ending at 2 targets instead of 4.
  `config/targets.yaml`'s own entries for all 4 now carry these findings
  as warnings, not just this document.

**Ceiling intentionally not computed for any of the 4 targets in this
pass.** `ceiling.py::_PARAM_RANGES` still samples each `lam_*` on the
pre-[[TASK-0121]] range `(0.0, 2.0)` — a combined-potential disorder up
to ~25x this project's own `sigma(V) <= 0.2*J` bound. Running a ceiling
search against that stale range would not measure this operator
family's real ceiling; it would measure how far a search can push
`H_new` back into the disorder regime TASK-0121 just fixed. This is a
known, already-filed gap ([[TASK-0116]], `REVIEW-panel-2026-07-17.md`
P0-4), not a shortcut taken here — fixing `_PARAM_RANGES` is TASK-0116's
explicit scope, and another thread has `ceiling.py` under active
concurrent edit (TASK-0130) as of this writing. Floor + actual only,
matching TASK-0081's own original precedent for this same target set.
Re-run ceiling for all 4 generalization targets once TASK-0116 lands.

Full process detail and the exact commands run:
`.ai/tasks/DONE/TASK-0127-extend-asd-generalization-set-as-headline.md`.

---

## Ceiling search coverage upgrade (TASK-0116, 2026-07-18)

**[EXECUTED]** [[TASK-0046]]'s ceiling search (`ceiling.ceiling_search`,
blind random search, 60 trials over 8 dimensions) drew its
`lam_B/T/R/C/M` weights independently on `(0.0, 2.0)` each — a range
that predates [[TASK-0121]]'s z-scoring of `potentials.py`'s five terms
and permits `sum(lam_i)` up to 10, ~25x [[TASK-0121]]'s own
`sigma(V) <= 0.2*J <= 0.4` bound (`E[sum(lam)] = 5.0` under the old
range — 12.5x the budget *on average*). The old search was therefore
sampling almost entirely from the Anderson-localized regime TASK-0121
exists to escape, making TASK-0046's own "near-chance ceiling, very
little headroom" negative claim weak evidence — it never searched the
physically valid region.

**Fix**: `ceiling.py::sample_params` now draws `lam_*` on the
constrained simplex `sum(lam_i) <= 0.4` — a total budget drawn
uniformly on `[0, 0.4]` (so the search also explores under-using the
budget, not only its boundary), split among the 5 terms via a
`Dirichlet(1,1,1,1,1)` draw (uniform over relative proportions).
`alpha`/`cutoff`/`n_low` unchanged. **Strategy upgrade**: added
`ceiling.ceiling_search_optuna` — TPE (Optuna) search over the same
corrected space, `consistency_score` reused completely unchanged as the
objective (per this task's own Out Of Scope: search coverage, not the
objective or the model).

**[EXECUTED] Real KRAS_G12C re-run** (TASK-0046's own cross-check
target), every delta kept separate and attributable (per this project's
standing "report both, don't silently reconcile" convention), all at
`t_max=15`/`n_steps=500` unchanged (matching TASK-0046's exact original
methodology — deliberately *not* also applying [[TASK-0130]]'s newer
`use_converged_limit` closed-form option, a 4th independent axis, which
would make it impossible to attribute a change to the range/strategy
fixes specifically):

| Search | Range | Seed convention | Best S / AUC_apo | Delta vs. original |
|---|---|---|---|---|
| Original (TASK-0046, 2026-07-15) | stale `(0.0,2.0)` each | `coherent=True` (pre-TASK-0118, implicit) | 0.5250 | — |
| Range-fix only, isolated | corrected `sum<=0.4` | `coherent=True` (byte-identical to original) | **0.4864** | -0.0386 |
| Range-fix only, current convention | corrected `sum<=0.4` | `coherent=False` (TASK-0118) | 0.4735 | -0.0515 |
| Range-fix + TPE, current convention | corrected `sum<=0.4` | `coherent=False` (TASK-0118) | **0.4908** (seed=7, exactly reproduced) / 0.4842 (seed=42, confirmatory) | -0.0342 |

Current floor (re-measured in the same run, `coherent=False`
convention): **0.4818**. The corrected-range TPE result (0.4908) lands
marginally *above* this floor (+0.009) — the first time any of this
project's KRAS_G12C ceiling numbers have crossed it, but the margin is
small enough that it is **not read as a real positive here**: it needs
[[TASK-0131]]'s permutation null (still TODO, unclaimed) or a bootstrap
CI ([[TASK-0112]]'s machinery, not wired into this comparison) before
that claim would be defensible. Flagged explicitly, not silently
claimed as a win.

**Headline finding: fixing the search space does not reveal hidden
ceiling headroom — if anything the original 0.5250 was itself
somewhat inflated by the stale range's access to physically-invalid
extreme disorder.** Under both corrections (valid range, current seed
convention) plus a smarter search strategy (TPE vs. blind random),
KRAS_G12C's ceiling is still, at best, a hair above its own floor, not
decisively above it. TASK-0046's "very little headroom in this operator
family" conclusion is **confirmed, not overturned**, by better search
coverage — now on firmer methodological ground than the original
60-trial run it was drawn from.

**Cross-validates two independent prior findings on different axes**:
[[TASK-0110]]'s Optuna search over CTQW's own numerical `(t_max,
n_steps)` parameters (H_new's physical weights left at default) found
0.4750 for KRAS_G12C; this task's search over H_new's physical weights
(CTQW numerics left at default) finds 0.4908. Three independent
searches over three different parameter axes (TASK-0046's original,
TASK-0110's numerics search, this task's corrected-space search) now
agree KRAS_G12C sits near chance.

**Not done, flagged rather than silently skipped**: BCR_ABL1/
CARDIAC_MYOSIN not re-run (this task's own Out Of Scope: start with
KRAS_G12C, extend only if the result changes the conclusion enough to
warrant it — it did not). `COMPETENCE_MAP.md`'s own KRAS_G12C ceiling
cell (0.524) not updated in place, per this document's and that one's
own "don't overwrite a prior number" convention — read alongside this
section, not instead of it. TASK-0117 (apply a validated CTQW clock to
the ceiling search specifically) remains open, though TASK-0130's
`use_converged_limit` now offers a ready mechanism for whoever picks it
up next.

Full detail: `.ai/tasks/DONE/TASK-0116-ceiling-search-coverage-upgrade.md`,
`results_task0116/KRAS_G12C/`.

---

## Reproducibility audit + run-logging convention (TASK-0135, 2026-07-19)

**[EXECUTED] The hypothesis this task was filed to test — "does this
environment silently corrupt 'before vs. after' comparisons via
run-to-run nondeterminism" ([[INV-0008]]) — is refuted, not confirmed.**
Three representative headline computations, spanning three different
computational patterns, each re-run at least 3 times independently
(fresh process each time, fresh RCSB fetch where applicable, no cached
objects reused):

| Computation | Repeats | Result |
|---|---|---|
| `H_new`'s spectral gap, BCR_ABL1 | 3 | Identical: `gap=0.032949006294881435` every time |
| `ceiling.ceiling_search`, KRAS_G12C, `seed=7` | 3 (1 from [[TASK-0116]] 2026-07-18 + 2 fresh) | Identical: `S=0.4735`, identical winning params, every time |
| `optuna_scan.apo_floor_scan`, KRAS_G12C, `seed=7` | 3 | Identical: `best_value=1895379886243.563` every time |

**BLAS thread-count sensitivity, tested directly** (spectral-gap case,
`OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/`MKL_NUM_THREADS` varied
`1/2/4/8`): real but tiny — result changes only in the ~14th
significant figure (spread ~7e-15, relative). **Conclusion: this
project's headline computations are reproducible given identical code +
seed + inputs, in this environment.** No caveat needed on any existing
headline number on reproducibility grounds.

**The originally-flagged BCR_ABL1 spectral-gap discrepancy
(`0.0374` vs. `0.1933`, [[INV-0008]]) is NOT explained by
environmental nondeterminism** — directly ruled out by the thread-count
test above (real effect ~1e-14 relative, discrepancy is 5.2x, ~11
orders of magnitude too large to be the same mechanism).
`REVIEW-panel-2026-07-17.md`'s "from BLAS reduction order" attribution
for this discrepancy was an inference, not itself a controlled test,
and is now refuted by one. Real, most-likely explanation (not
exhaustively pinned — a stale historical number, now moot):
`0.1933` traces to [[TASK-0102]]'s Done section (2026-07-13), which
explicitly reused a *cached* `H_new` object from [[TASK-0091]] rather
than rebuilding it — a snapshot from 5 days before [[TASK-0121]]
changed `build_H_new`'s `lam_*` defaults (among possibly other
intervening code changes). Tested both the pre- and post-TASK-0121
defaults directly on fresh BCR_ABL1 data: neither reproduces `0.1933`
exactly (`0.00107` and `0.0329` respectively) — some other code
difference across that 5-day gap is the more likely cause, not chased
further per this task's own scope (a stale number [[TASK-0130]] already
made moot by deleting the gap-based clock entirely). `COMPETENCE_MAP.md`
and [[INV-0008]] corrected additively with this finding, not silently
overwritten.

**Run-logging convention (Part 2)**: new `allostery.runlog` module —
`environment_fingerprint()` (BLAS thread env vars, hostname, PID,
python/numpy/scipy/optuna versions, timestamp) and `RunLogger` (JSONL,
one line per step, flushed + fsync'd immediately — same "partial run
still leaves a usable trace" discipline `ceiling_search_batched.py`'s
own checkpoint file already established, generalized). Each step
records both wall-clock and CPU-seconds elapsed
([[P-0005]]/[[TASK-0134]]'s own finding that wall-clock alone cannot
distinguish genuine computation from contention/suspension). Chosen
over a documentation-only convention because a real importable module is
directly reusable and enforceable, not just describable — this
project's own `_log(msg)` helper is independently copy-pasted across
10+ scripts already, exactly the kind of duplication a shared module
fixes. Adopted in a real script: new `scripts/reproducibility_audit.py`
(the tool that produced this section's spectral-gap numbers) uses
`RunLogger` for its own environment fingerprint + per-repeat timing,
not the ad-hoc pattern.

Full detail: `.ai/tasks/DONE/TASK-0135-reproducibility-audit-and-run-logging.md`,
`.ai/invariants/INV-0008-run-to-run-environmental-reproducibility.md`,
`results_task0135/BCR_ABL1/spectral_gap_audit.jsonl`.

---

## Mode co-participation (TASK-0122, 2026-07-19) — a mixed, mostly-negative real result that refutes the panel's own preliminary estimate

**[EXECUTED, all 3 mandatory targets, real code, real data]** `mode_coparticipation`
(REVIEW-2026-07-13b Sec.6, sharpened by `REVIEW-panel-2026-07-17.md` P1-5 into a
per-residue `CP_low(j) = sum_{k<=n_low} |v_k(j)|^2 * mean_{i in source} |v_k(i)|^2`)
was proposed as "the only route back to a defensible positive" — a seed-dependent,
not-distance-monotone observable that should decorrelate from the proximity confound
every propagator in this project's register already carries. Implemented (new
`analysis.mode_coparticipation`), gated through TASK-0103's dumbbell 2x2 matrix (passed
cleanly — tracks coupling like CTQW, not the well like GSR, same double dissociation
`test_dumbbell_negative_control.py::TestModeCoparticipationDumbbellGate` already
established for CTQW), then validated on real KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN data.

**Headline: the panel's own preliminary numbers (measured on a reconstructed 3MHT
surrogate, explicitly flagged there as unverified against this repo's real code) do not
transfer, and not in the direction hoped for.**

| Target | `\|rho(CP,-dist)\|` clean Laplacian | `\|rho\|` `H_new` pre-TASK-0121 | `\|rho\|` `H_new` current (renormalized) | Real-label AUC vs. floor |
|---|---|---|---|---|
| KRAS_G12C | 0.430 | 0.198 | 0.305 | 0.309 vs 0.482 — **fails floor** |
| BCR_ABL1 | 0.237 | 0.425 | 0.451 | 0.758 vs 0.582 — **clears floor** (+0.176) |
| CARDIAC_MYOSIN | 0.621 | 0.239 | 0.358 | 0.577 vs 0.792 — **fails floor** |

Three findings, all real, none matching the panel's own prediction:

1. **The panel's own clean-Laplacian estimate (`\|rho\|`=0.18) does not hold on any real
   target — every real target measures substantially higher (0.24-0.62).** A clean
   Laplacian's own CP is, if anything, *more* distance-confounded on real protein
   geometry than the panel's 3MHT reconstruction suggested, not less.
2. **TASK-0121's potential renormalization made CP's distance-correlation *worse*, not
   better, on all 3 targets** (pre-TASK-0121 `\|rho\|` 0.198/0.425/0.239 -> current
   0.305/0.451/0.358) — the opposite of the panel's own hoped-for effect (they measured
   un-renormalized `H_new` as the *worse* of the two, predicting renormalization would
   help; on real data it consistently hurts instead). The sign also flips between the
   clean Laplacian (positive — high CP near the seed, the ordinary proximity-confound
   direction) and every `H_new` variant (negative — high CP *far* from the seed) on all 3
   targets; the magnitude stays substantial either way, so this is a different confound
   shape, not less of one.
3. **The k-sweep never reliably crosses into a real, directly-measured noise floor**
   (`\|rho(random,-dist)\|` = 0.062/0.039/0.026 +/- ~0.03-0.05 per target, 200 draws each
   — measured fresh here, not copied from the panel's own 3MHT estimate of
   0.044+/-0.036). Across `n_low` in {3, 5, 10, 20, all} on the current renormalized
   `H_new`: KRAS_G12C dips inside the noise floor at `k=10` only (`\|rho\|`=0.114,
   non-monotonic — `k=3`/`5`/`20`/`all` are all outside it: 0.179/0.305/0.498/0.760);
   BCR_ABL1 and CARDIAC_MYOSIN never cross into their own noise floor at any `k` tested
   (BCR_ABL1: 0.488/0.451/0.312/0.483/0.766; CARDIAC_MYOSIN: 0.362/0.358/0.340/0.312/
   0.668). The panel's own "`k=5` decorrelates" specific claim does not reproduce on any
   of the 3 real targets — `k=5`'s own `\|rho\|` is 0.305/0.451/0.358, all well outside
   each target's own noise floor.

**Real-label scoring is genuinely mixed, not uniformly negative**: BCR_ABL1 clears its
own proximity floor by a real margin (+0.176) — the one target where CP finds real
signal beyond what the "necessary but not sufficient" caveat this task was filed with
requires checking. But per finding 2 above, BCR_ABL1's own CP score is *also* the most
strongly distance-correlated of the three (`\|rho\|`=0.451) — its floor-clearing AUC
coexists with, not instead of, a substantial distance confound, which weakens (does not
void) reading this pass as clean evidence of coupling-detection rather than a
differently-shaped proximity effect. KRAS_G12C and CARDIAC_MYOSIN both fail to clear
their own floors.

**Verdict, stated plainly per this project's own honest-NO convention**: `mode_
coparticipation` is correctly implemented (formula verified against an independent
hand-derivation, `TestModeCoparticipation::test_matches_hand_derived_formula_on_a_
tiny_synthetic_case`) and correctly falls on the "tracks coupling" side of the dumbbell
gate — but on this project's real targets and real code, it does **not** deliver the
low-distance-correlation property its entire case for adoption rested on, and clears
the real-label proximity floor on only 1 of 3 mandatory targets. This is not a
recommendation to adopt `mode_coparticipation` as a submission observable in its
current form — it is a real, checked answer to a real, load-bearing question the panel
raised, and the answer is mostly no, not yes. Tier-2 gating (TASK-0100) still applies
unchanged; this task's own scope was measurement, not operator selection.

Full detail: `.ai/tasks/DONE/TASK-0122-mode-coparticipation-observable.md`,
`results_task0122_mode_coparticipation/mode_coparticipation_validation.json`,
`scripts/mode_coparticipation_validation.py`.

---

## GNM transfer-entropy classical baseline (TASK-0132, 2026-07-19)

**[EXECUTED, all 3 mandatory targets, real code, real data]** A published,
classical (no MD, no quantum), seconds-on-a-laptop baseline — directional
transfer entropy over GNM contact topology — implemented and scored the
same way as every other observable in this project's register, per
`REVIEW-panel-2026-07-17.md` §4 P1-6/§6.3#5: *"the published classical
method that does [slow-mode filtering] already. If you can't beat it, you
don't have a result."*

**Citations checked directly before implementing, not assumed from the
review's one-line summary** — both papers are real. Hacisuleyman & Erman,
*Proteins* 85(6):1056-1064 (2017), PMID 28241380, confirms the claimed
method (Schreiber transfer entropy + GNM, directional causal-flow signal
from harmonic interactions alone). **Correction to the filing task's own
citation**: PMID 35644497 (*J Mol Biol* 434(17), 2022, "Subsets of Slow
Dynamic Modes Reveal Global Information Sources as Allosteric Sites") is
real and matches the claimed method (GNM+TE over slow-mode subsets, a
20-protein benchmark) — but its authors are **Altintel, Acar, Erman,
Haliloglu**, not "Kaynak & Bahar" as filed.

**Formulation, stated per this task's own Constraint** (several TE
variants exist in the literature; the review's summary is not a full
method spec): the linear-Gaussian transfer entropy / Granger-causality
closed form (Barnett, Barrett & Seth, *PRL* 103:238701, 2009) —
`T_{Y->X} = 0.5*ln(Sigma_X / Sigma_{X|Y})` — applies exactly, since GNM
fluctuations are multivariate Gaussian by construction (no histogram-
based entropy estimation needed, unlike the MD-trajectory-based
predecessor papers). Lag `tau` set to the GNM's own slowest relaxation
time (`1/gap`, this task's own choice, matching the project's existing
spectral-gap-clock convention from TASK-0109/0119/0130 rather than
inventing an unrelated rule — the cited papers do not specify a single
universal lag).

**A genuine mathematical subtlety worked out and verified, not assumed**:
for the pure (reversible) GNM Langevin process, the lagged cross-
covariance `C_ij(tau)` is provably **symmetric** (`C_ij(tau) = C_ji(tau)`
for any `tau`, confirmed both by derivation and directly on real data) —
the cross-term alone carries no directional information. Directionality
survives anyway because the two directions' formulas use *different
self-prediction baselines* (residue X's own marginal relaxation
properties vs. residue Y's, generally different) — confirmed numerically
via a dedicated regression test and a synthetic hub-vs-periphery sanity
check (a tightly-coupled clique correctly scores as a stronger
information source than a weakly-coupled one, joined by a single bridge
edge) before trusting this on real targets.

**Real run** (`scripts/transfer_entropy_baseline.py`, live fetch,
`results_task0132/transfer_entropy_baseline.json`), compared directly
against `H_new`/CTQW's own current numbers (`COMPETENCE_MAP.md`'s
TASK-0130 closed-form table):

| Target | Floor | Transfer-entropy AUC | `H_new`/CTQW actual AUC | TE diagnosis |
|---|---|---|---|---|
| KRAS_G12C | 0.4818 | 0.4485 | 0.5901 | `BEATS_CHANCE_NOT_FLOOR` |
| BCR_ABL1 | 0.5817 | 0.3497 | 0.5266 | `BEATS_CHANCE_NOT_FLOOR` |
| CARDIAC_MYOSIN | 0.7921 | 0.5335 | 0.7272 | `NO_SIGNAL_IN_APO` |

**Neither of this task's own two anticipated outcomes holds cleanly —
reported as the mixed result it actually is, not forced into either
bucket.** (a) does **not** hold: this classical baseline does not beat
or match `H_new`/CTQW — it scores lower on all 3 targets, decisively so
on BCR_ABL1 and CARDIAC_MYOSIN (the latter not even clearing chance).
(b) holds only partially: the classical method **also** fails to clear
the proximity floor on all 3 targets, which is a real, independent
confirmation that this specific 3-target problem is hard beyond just
this project's own operator choices — but `H_new`/CTQW still does
directionally, sometimes substantially, better than this particular
published classical method, so "the task itself is hard regardless of
method family" is not the full story either. Cross-reference:
[[TASK-0122]]'s mode co-participation (the other independent classical-
ish comparison point landed the same day) clears its own floor on 1 of
3 targets (BCR_ABL1, +0.176) — transfer entropy clears it on 0 of 3,
the more negative of the two comparisons run this session.

**Out of scope, not attempted**: reselecting the submission operator
based on this result (Tier-2-gated per [[TASK-0100]], unchanged); this
task's own scope was measurement, not selection.

Full detail: `.ai/tasks/DONE/TASK-0132-gnm-transfer-entropy-baseline.md`,
`results_task0132/transfer_entropy_baseline.json`,
`src/allostery/transfer_entropy.py`.

---

## Distance-stratified evaluation (TASK-0123, 2026-07-19) — the panel's own kill/pass test, plus a correction the panel's own criterion didn't anticipate

**[EXECUTED, all 3 mandatory targets, real code, real data]**
`REVIEW-panel-2026-07-16-v2.md` Sec.2.3/Sec.6 identified a structural problem with every
whole-graph AUC this project reports: occupation of a walk seeded at a point is
monotonically decreasing in distance from that point, for any operator, at any time — a
whole-graph AUC cannot distinguish "found the pocket" from "found distance." The
prescribed fix and falsification test: score each pocket residue only against non-pocket
residues at the *same* hop-shell from the seed; "stratified AUC ~= 0.5 in every shell ->
observable dead."

New `metrics.stratified_auc`/`stratified_auc_summary` (single-hop-distance bins, computed
once per target and reused identically across every operator — this task's own
Constraint), applied to all 16 operators in `analysis._operator_registry()` x both
propagators (`ctqw` via TASK-0130's closed form, `ground_state` at `t_max=15`) x all 3
mandatory targets (96 cells), plus [[TASK-0122]]'s `mode_coparticipation`.

**Naive reading, easy to overclaim**: 40 (target, operator, propagator) cells with a
well-powered shell (>=3 pocket residues) clear stratified AUC > 0.65 — on every mandatory
target, across nearly every operator in the register. Read naively, this looks like a
striking reversal of nearly every other "no mandatory target's actual clears its own
floor" finding elsewhere in this document.

**That naive reading is wrong, checked directly, not assumed.** `stratified_auc_summary`
takes the *maximum* AUC over several shells per cell — the identical winner's-curse/
look-elsewhere structure [[TASK-0131]] already found for the ceiling search's max-over-60-
trials statistic. A real permutation null (label the same-sized random subset of residues
"pocket," re-score the *same, fixed, already-computed* occupation vector, 1000 replicates)
confirms this directly: the null's own median well-powered-max AUC is **0.56-0.64, not
0.5** — most of the naive ">0.65" list is within or barely above what pure noise produces
under this exact max-over-shells procedure.

**The corrected picture** (3 representative cases per target — `H_new`/`ctqw`, `H_new`/
`ground_state`, `mode_coparticipation` — the two propagators plus TASK-0122's own
observable, 9 tests total):

| Target | Representative | Real well-powered max AUC (shell) | Null median | p-value |
|---|---|---|---|---|
| KRAS_G12C | `H_new`/ctqw | 0.710 (shell 1) | 0.643 | 0.269 |
| KRAS_G12C | `H_new`/ground_state | 0.518 (shell 3) | 0.635 | 0.851 |
| KRAS_G12C | `mode_coparticipation` | 0.405 (shell 3) | 0.640 | 0.982 |
| BCR_ABL1 | `H_new`/ctqw | 0.741 (shell 4) | 0.609 | 0.153 |
| BCR_ABL1 | `H_new`/ground_state | 0.820 (shell 4) | 0.620 | 0.053 |
| BCR_ABL1 | `mode_coparticipation` | 0.906 (shell 2) | 0.619 | **0.012** |
| CARDIAC_MYOSIN | `H_new`/ctqw | 0.581 (shell 1) | 0.560 | 0.451 |
| CARDIAC_MYOSIN | `H_new`/ground_state | 0.890 (shell 1) | 0.569 | **0.010** |
| CARDIAC_MYOSIN | `mode_coparticipation` | 0.604 (shell 2) | 0.570 | 0.400 |

**2 of 9 clear p<0.05 uncorrected** (BCR_ABL1's `mode_coparticipation`, CARDIAC_MYOSIN's
`H_new`/`ground_state`) — **neither survives a Bonferroni correction** for 9 tests
(threshold 0.0056). The panel's own literal kill criterion ("stratified AUC ~= 0.5 in
every shell") does not strictly fire — several real values sit well above 0.5 — but the
panel's own criterion did not anticipate that "stratified AUC" itself, as the maximum over
several shells, carries its own selection bias requiring the same null-distribution
treatment TASK-0131 already established for the ceiling search. Read plainly: this task
finds **real, uncorrected suggestive signal in 2 of 9 tested cells** — candidates for
targeted follow-up (a dedicated look at CARDIAC_MYOSIN's `H_new` ground-state relaxation
within its own hop-shell-1 neighborhood, and at BCR_ABL1's `mode_coparticipation` within
shell 2) — **not a confirmed reversal of this document's other floor/ceiling findings**,
and not the panel's own predicted "observable dead" outcome either. Neither extreme is
supported; the honest middle is what the data shows.

**A secondary, real observation worth naming**: the naive (uncorrected) list shows the
*same* shell (BCR_ABL1's shell 4, `n_pos=3`/`n_neg=76`; CARDIAC_MYOSIN's shells 1/4/12 at
varying power) clearing >0.65 across nearly every operator in the register simultaneously
— consistent with a real, shared structural property of that specific shell (not
independent per-operator discoveries; most register operators are built from similar
structural inputs and would be correlated with each other under any real signal, which is
itself why the naive per-cell count of "40 passes" overstates independent evidence even
before the permutation-null correction above).

Full detail: `.ai/tasks/DONE/TASK-0123-distance-stratified-evaluation.md`,
`results_task0123_distance_stratified/distance_stratified_evaluation.json`,
`results_task0123_distance_stratified/summary.md`,
`scripts/distance_stratified_evaluation.py`.

---
## Pocket-label ligand-contact cutoff sensitivity (TASK-0114, 2026-07-20)

**Is the ground-truth pocket label itself a knob with unreported spread?** `holo_pocket_
mask`'s 4.5 Å ligand-contact cutoff defines which residues count as "true pocket" at
all — a different, upstream cutoff from the GNM graph cutoff TASK-0067/TASK-0113 already
characterized. TASK-0075 already proved this project's *other* threshold gate
(cumulative-overlap go/no-go) is knob-unstable (0.067–0.860 across an 18-combo grid,
15/18 verdict flips) — this task checks whether the label-definition cutoff has the same
property.

Method: sweep `build_labels`' `cutoff` across {4.0, 4.5, 5.0, 5.5} Å on all 3 mandatory
targets, re-scoring the *same*, once-computed `H_new`/`time_averaged_ctqw_converged`
occupation (TASK-0130's closed form) against each cutoff's regenerated label — only the
label changes, the operator is never recomputed (`scripts/pocket_label_cutoff_
sensitivity.py`, `results_task0114_pocket_cutoff_sensitivity/`).

| Target | Cutoff (Å) | n pocket | AUC | Floor | Floor cleared? | `classify_failure` |
|---|---|---|---|---|---|---|
| KRAS_G12C | 4.0 | 15 | 0.581 | 0.505 | Yes | `NO_FAILURE_DETECTED` |
| KRAS_G12C | 4.5 | 18 | 0.590 | 0.482 | Yes | `NO_FAILURE_DETECTED` |
| KRAS_G12C | 5.0 | 18 | 0.574 | 0.476 | Yes | `NO_FAILURE_DETECTED` |
| KRAS_G12C | 5.5 | 17 | 0.522 | 0.444 | Yes | **`NO_SIGNAL_IN_APO`** |
| BCR_ABL1 | 4.0 | 14 | 0.565 | 0.593 | No | **`BEATS_CHANCE_NOT_FLOOR`** |
| BCR_ABL1 | 4.5 | 16 | 0.527 | 0.582 | No | `NO_SIGNAL_IN_APO` |
| BCR_ABL1 | 5.0 | 19 | 0.524 | 0.578 | No | `NO_SIGNAL_IN_APO` |
| BCR_ABL1 | 5.5 | 20 | 0.532 | 0.582 | No | `NO_SIGNAL_IN_APO` |
| CARDIAC_MYOSIN* | 4.0 | 9 | 0.461 | 0.511 | No | `NO_SIGNAL_IN_APO` |
| CARDIAC_MYOSIN* | 4.5 | 13 | 0.518 | 0.568 | No | `NO_SIGNAL_IN_APO` |
| CARDIAC_MYOSIN* | 5.0 | 14 | 0.499 | 0.551 | No | `NO_SIGNAL_IN_APO` |
| CARDIAC_MYOSIN* | 5.5 | 14 | 0.499 | 0.551 | No | `NO_SIGNAL_IN_APO` |

*CARDIAC_MYOSIN's numbers here use [[TASK-0124]]'s new apo structure (8QYP, N=704),
landed the same day as this task and in flight while this sweep ran — **not directly
comparable to this project's other CARDIAC_MYOSIN numbers elsewhere in this document,
almost all computed against the old 5TBY structure (N=950)**, flagged explicitly rather
than silently mixed. A re-run against 8QYP once that task's own numbers are the
document's settled reference is a real, cheap follow-up (rerun the same script), not
redone here.

**Headline, precisely stated — two different granularities give two different answers**:

1. **The coarse question the task's own Outcome asked ("does the cutoff choice flip
   which side of the proximity floor a target lands on") — no, not for any target.**
   `floor_cleared` is stable across the entire grid for all 3 targets (KRAS_G12C always
   clears, BCR_ABL1/CARDIAC_MYOSIN never do).
2. **The finer-grained `classify_failure` diagnosis category is NOT stable — it changes
   for 2 of 3 targets.** KRAS_G12C flips `NO_FAILURE_DETECTED` -> `NO_SIGNAL_IN_APO` at
   5.5 Å (AUC drops to 0.522, inside the ±0.05-of-chance band `classify_failure` checks
   *before* the floor comparison, even though the bare `auc > floor` boolean would still
   read "cleared"). BCR_ABL1 flips the other direction, `BEATS_CHANCE_NOT_FLOOR` ->
   `NO_SIGNAL_IN_APO`, between 4.0 Å and 4.5 Å. Neither swing is remotely as dramatic as
   TASK-0075's CO-gate instability (0.067–0.860, 15/18 flips) — AUC itself only moves
   ~0.04–0.07 across the whole grid for either target — but it is real, reportable
   sensitivity in the reported *diagnosis label*, not just noise in a number nobody reads
   directly.
3. **TASK-0047's pinned 4.5 Å KRAS_G12C fixture (21/21 heavy-atom recovery) is confirmed
   exactly correct** (`matches_pinned_4_5a_exactly=True`) **and sits on a real, still-
   moving slope, not a plateau**: 4.0 Å recovers 17 raw contacts (4 short of the pinned
   set: residues 11, 13, 69, 100 drop out); 5.0 Å recovers 22 (gains residue 92); 5.5 Å
   recovers 24 (gains 35, 64, 92). The recovered set keeps changing in both directions at
   every 0.5 Å step tested — the 4.5 Å choice is not obviously sitting on a stable local
   plateau, though the *downstream* verdict (§1/§2 above) is far less sensitive than the
   raw residue-set churn alone would suggest.

**Reading together with TASK-0075's own finding**: this project now has direct evidence
that its two structurally distinct 4.5 Å-shaped thresholds behave very differently —
the cumulative-overlap go/no-go gate is genuinely knob-unstable (large swings, most
combinations flip), while the pocket-label cutoff is comparatively well-behaved (small
AUC drift, a real but narrow diagnosis-category sensitivity at the grid's edges, no
floor-side flips at all). Per this task's own Out Of Scope, the shipped 4.5 Å default is
not changed here — this is a characterization, the same posture TASK-0067 took for the
GNM cutoff.

Full detail: `.ai/tasks/DONE/TASK-0114-pocket-label-cutoff-sensitivity.md`,
`results_task0114_pocket_cutoff_sensitivity/pocket_label_cutoff_sensitivity.json`,
`scripts/pocket_label_cutoff_sensitivity.py`.

---

## Engineered-dephasing (ENAQT) discrimination sweep (TASK-0141, HYP-P11, 2026-07-20)

Tests the collaborator's Idea #1 (Mohseni/Rebentrost/Lloyd/Aspuru-Guzik 2008, Rebentrost 2009,
Caruso 2014, Viciani 2015) with the *correct scored quantity*: those four references establish
an optimal Haken-Strobl dephasing rate for **transport efficiency to a known trap** — this
project's own objective is **discrimination** of an *unknown* pocket, a different quantity.
`REVIEW-panel-2026-07-20`'s own physics check (`enaqt_sanity.py`, a synthetic sanity script not
present in this repo — flagged by this Architect/Planner thread before this task started)
predicted a clean NEGATIVE: dephasing de-traps the walker from `H_new`'s Anderson localization
by pushing it toward classical diffusion, which *is* this project's own well-documented
proximity confound — synthetic AUC 0.72→0.16, `rho(occ,-dist)` 0.10→0.68→0.92 as gamma: 0→5.

**Two real, load-bearing gaps closed in `propagators.py` before this task's own sweep could be
trusted:**
1. `haken_strobl` had no incoherent-mixture source option — every multi-residue seed used a
   coherent equal-amplitude superposition, violating this project's own established GAUGE
   (TASK-0118/INV-0006: a real multi-residue active site has no biophysical basis for a specific
   relative quantum phase between its residues). New `coherent` kwarg (default `True`, unchanged
   for every existing caller) mirrors `ctqw`'s own split; this task always passes
   `coherent=False`.
2. No time-averaged Haken-Strobl occupation existed — `haken_strobl` only returns one endpoint
   snapshot, but this task's own Intent Contract scores "time-averaged site occupation". New
   `haken_strobl_time_averaged` (one `solve_ivp` call with `t_eval`, not `n_snapshots`
   independent re-solves — effectively free on top of the existing single-endpoint cost).
   Deliberately excludes `t=0` from its own averaging grid (unlike `time_averaged_ctqw`'s
   `linspace(0, t_max, n_steps)`, harmless there at its 500-point default): the initial
   condition is a delta-function-like spike exactly at the seed, and including it as one of only
   `n_snapshots` equally-weighted points would bake a `1/n_snapshots`-weighted proximity
   artifact into the very quantity this task exists to check for a proximity confound in — found
   directly while validating the function (12 new tests, `test_haken_strobl_extensions.py`), not
   assumed.

**Method**: gamma swept over the task's own fixed grid `{0, 0.05, 0.1, 0.2, 0.5, 1, 2, 5} x
H_new's spectral bandwidth` (this repo's established "bandwidth" convention,
`w.max()-w.min()`), `t_max=25` (TASK-0105's own established anchor), `coherent=False`
(TASK-0118 GAUGE), on KRAS_G12C / BCR_ABL1 / PTP1B (the collaborator's chosen third case — its
apo/holo chain wiring was confirmed identical to the 3 mandatory targets, `.ai/tasks/DONE/
TASK-0081...md`, resolving this task's own Open Question with no substitution needed). Scored:
whole-graph AUC vs `diagnostics.classify_failure`'s proximity floor (with block-bootstrap 95%
CIs), TASK-0123's own distance-stratified lens, `metrics.ipr` (participation ratio) and
`rho(occ, -dist)` as the mechanism covariate. Runtime was far below the pre-registered
feasibility estimate (TASK-0105's own N^3-scaling note): 0.06-0.6s/gamma (KRAS_G12C),
0.05-3.0s/gamma (PTP1B), 0.2-9.1s/gamma (BCR_ABL1) — full 3-target, 8-point sweep completed in
~90s wall-clock, not the tens-of-minutes budgeted for.

**Headline result — NEGATIVE on all 3 targets, confirming HYP-P11's own pre-registered
prediction:**

| Target | gamma=0 AUC | Best interior AUC (gamma mult) | Floor | CI non-overlapping? | Beats coherent? | Permutation p (Bonferroni alpha=0.0167) |
|---|---|---|---|---|---|---|
| KRAS_G12C | 0.4489 | 0.4757 (5x) | 0.4818 | No | Yes | 0.649 |
| BCR_ABL1 | 0.5366 | 0.5582 (5x) | 0.5817 | No | Yes | 0.211 |
| PTP1B | 0.2392 | 0.2414 (5x) | 0.4847 | No | Yes | 1.000 |

No gamma clears the proximity floor with non-overlapping CIs on any target, and the best interior
gamma's own permutation-null check (1000 replicates, "which of these 8 fixed points looks best on
real labels" is itself a max-of-K selection getting the same winner's-curse scrutiny TASK-0131/
TASK-0138/TASK-0123 have already established as necessary here) is nowhere near significant even
uncorrected, let alone Bonferroni-corrected across 3 targets. AUC does rise slightly from gamma=0
to gamma=5x on all 3 targets (interior optimum shape echoing TASK-0105's own transport-efficiency
finding, `RESULTS.md` open-question row 7) — but the rise is small, not floor-crossing, and not
distinguishable from noise. PTP1B stays clearly anti-correlated with its own (genuinely distal)
pocket at every gamma (AUC 0.19-0.24), consistent with TASK-0081's independent finding
(AUC 0.2497 at a different, undephased configuration).

**The mandatory classical-limit sanity gate did NOT pass as literally specified, on any target —
a genuine complication, root-caused (not glossed over) before trusting the interior points:**
`rho(occ,-dist)` *fell* from gamma=0 to the gamma=5x endpoint on all 3 targets (KRAS_G12C:
0.721->0.539; BCR_ABL1: 0.619->0.351; PTP1B: 0.470->0.226) — the opposite direction from the
task's own synthetic prior (which predicted a rise to ~0.92). Diagnosed directly (not assumed):
at fixed `t_max=25`, this is **not** an integrator bug and **not** evidence the classical-limit
picture is wrong in general — it is Zeno-regime suppression of the *effective* diffusion
timescale at large gamma (`D_eff ~ ||H||^2/2*gamma` falls as gamma grows past the ENAQT-optimal
point), meaning the classical-diffusion-like proximity signature needs *more* propagation time to
develop as gamma increases, and `t_max=25` (fixed across the whole sweep, matching TASK-0105's
own established anchor) under-samples it at the grid's high end. Confirmed directly on
KRAS_G12C at gamma=5x bandwidth by extending `t` alone (gamma held fixed): `rho(occ,-dist)`
0.584 (t=25) -> 0.730 (t=100) -> 0.863 (t=300) — recovers the expected rising trend once given
enough time, ruling out an implementation error. This does not change the headline verdict (the
AUC-vs-floor numbers above are valid measurements of "what gamma does to discrimination at
t_max=25", the task's own fixed-grid deliverable) but means the sanity gate's own literal pass/
fail bar, as specified, is not met at this `t_max`, and is flagged rather than silently
worked around.

Full detail: `.ai/tasks/DONE/TASK-0141-engineered-dephasing-sweep.md`,
`results_task0141_dephasing/dephasing_discrimination_sweep.json`,
`scripts/dephasing_discrimination_sweep.py`, new `propagators.haken_strobl_time_averaged` /
`haken_strobl(..., coherent=)`, `tests/test_haken_strobl_extensions.py`.

---

## Index of open questions from this run

| # | Question | Status | Task |
|---|---|---|---|
| 1 | Does BCR_ABL1's `ground_state_relaxation` score (0.731) survive TASK-0094's proximity floor, and does clearing it mean anything? | **resolved 2026-07-14: clears the floor (+0.166), is largely seed-independent (TASK-0102), and a controlled negative-control experiment shows the mechanism is well-depth, not active-site coupling (TASK-0103/TASK-0104, `REVIEW-2026-07-13b`)** — the number is real; the causal claim is now "apo-computable structural prior for cryptic pockets," not allosteric signal. See BCR_ABL1 section above for the full picture. | [[TASK-0091]], [[TASK-0102]], [[TASK-0103]], [[TASK-0104]] |
| 2 | What do the holo-side diagnostic numbers show for all three targets, and does the tiny apo/holo gap TASK-0067 found for the bare operator hold for the full `H_new` pipeline? | **resolved 2026-07-14: no, the gap is small for both targets (KRAS: holo 0.698 vs apo 0.779, holo actually lower; BCR_ABL1: holo 0.586 vs apo 0.525, small gap, both near chance) — for BCR_ABL1 this points to the propagator/operator being the bottleneck, not apo's information content; `ground_state_relaxation`'s holo-side AUC (0.7394) is very close to its apo-side (0.7315), the "static artifact" signature per the addendum's own caveat, not independent corroboration** | [[TASK-0092]] |
| 3 | Which methodology difference (cutoff / pocket-label definition / source definition) explains KRAS_G12C's 0.779 vs. this repo's own previously-asserted 0.3–0.7 band? | open, but downgraded 2026-07-13 — no longer bears on whether KRAS shows real signal (it does not, either way; see TASK-0094) | [[TASK-0093]] |
| 4 | Does CARDIAC_MYOSIN's or KRAS_G12C's high AUC share a common cause beyond CARDIAC_MYOSIN's already-explained large-N flag? | **resolved 2026-07-13**: yes for KRAS (proximity, TASK-0094); CARDIAC_MYOSIN's floor-clearance is independent of KRAS's (it clears the proximity floor, its issue is purely the large-N flag) | [[TASK-0094]] |
| 5 | Does any mandatory target's apo-only AUC clear a real proximity floor (not just chance/degree)? | **resolved 2026-07-13: no — zero of three** (KRAS fails the floor, BCR_ABL1 fails chance, CARDIAC_MYOSIN's clearance is moot under the large-N flag) | [[TASK-0094]] |
| 6 | Does `H_new`'s CTQW-trapping mechanism (Anderson-like localization, `REVIEW-2026-07-13c`) reproduce on real BCR_ABL1 data, and does it explain the `H10`>`H_new` gap already on record? | **resolved 2026-07-14: mechanism reproduces (participation ratio 5-6x higher, ⟨hop⟩ a quarter), the `H10` sign reproduces but `H2` doesn't, none of the 4 operators clear the real floor, and the result is sensitive to a seed-definition (single- vs. multi-index) choice not previously treated as meaningful** — mixed result, reported as such, not forced to match the synthetic prediction. | [[TASK-0106]] |
| 7 | Does real-target ENAQT (`haken_strobl` γ-sweep) show the textbook interior-γ transport optimum `REVIEW-2026-07-13b` found on synthetic networks? | **resolved 2026-07-14: yes on 3/6 swept (target, operator) cells (1.24-1.70x enhancement), but the extra transport does not improve — and in every observed case slightly degrades — pocket-discrimination AUC; no floor-crossing is caused by dephasing anywhere in this data. CARDIAC_MYOSIN's full sweep is computationally infeasible with the current dense-matrix `haken_strobl` (N³ scaling, ~30+ min/γ at N=950) — γ=0 anchor only** | [[TASK-0105]] |
| 8 | Is dephasing-assisted transport (ENAQT) more noise-robust than coherent CTQW under a real per-gate NISQ noise model (`HOLO_DIRECTION_MODULE.md`'s named scoreable result)? | **resolved 2026-07-14: no — coherent ties or beats ENAQT at every depth/error-rate point tested (KRAS_G12C, 10-qubit coarse-grained `H_new`, 2 timescales), a real negative result, not the hoped-for story. `coarse.trotter_cost`'s accuracy-calibrated depth estimate (3133 steps) is ~2-3 orders of magnitude beyond NISQ-feasible — found empirically (a literal-estimate run was killed after 69 CPU-minutes), not anticipated** | [[TASK-0068]] |
| 9 | Does a fully-informed ceiling search (answer key in hand, entire `H_new` physical-scalar space) beat each mandatory target's proximity floor — i.e. is there any real headroom in this operator family? | **resolved 2026-07-15: no for KRAS_G12C — the ceiling itself (0.524, 60 real trials) is *below* its own floor (0.798), the strongest form of negative result this framework can express. BCR_ABL1's ceiling (0.612) does clear its floor (0.565) but the shipped actual result (0.525) does not. CARDIAC_MYOSIN's ceiling (0.819) clears its floor (0.764, 40.7% headroom) but this is moot — `INSUFFICIENT_RESOLUTION` fires first. Full synthesis: `COMPETENCE_MAP.md`.** | [[TASK-0046]], [[TASK-0082]] |
| 10 | Would the reported verdict change for any mandatory target if quantum coherence were randomized away — i.e. is `dephasing_sweep`'s "coherence adds ~nothing" finding actually wired into what a judge reads? | **resolved 2026-07-16, extended 2026-07-17: no for 2 of 3 mandatory targets, formally.** KRAS_G12C: `auc_range=0.0132` at t_max=25, flat, `COHERENCE_NOT_SIGNIFICANT`. **BCR_ABL1, newly unblocked by [[TASK-0128]]: `auc_range=0.0050`, flat, every point floor-cleared, `COHERENCE_NOT_SIGNIFICANT`** — matches KRAS's conclusion exactly. CARDIAC_MYOSIN's `calibrate_kappa` blocker is resolved (TASK-0128), but its full sweep remains not-run for a separate, pre-existing `haken_strobl` computational-cost reason (γ=0 anchor only). The project-wide seed/clock gauge problem itself (Sec.2.1/2.2) remains unresolved outside this task's narrower scope.** | [[TASK-0099]], [[TASK-0128]] |
| 11 | How far short is the shipped `t_max=15`/`n_steps=500` of `time_averaged_ctqw`'s own convergence criterion on real targets, and is reaching the corrected value practical? | **resolved 2026-07-17: 145,000x-3,950,000x short (grows with system size), and reaching it is currently uncomputable — a real call at the prescribed point did not return after 2+ hours (O(n_steps) Python loop). A capped, honestly-sampled search found real per-target ceilings instead: KRAS_G12C 0.475 (near chance, cross-checks TASK-0046's 0.525 on an independent axis), BCR_ABL1 0.583 at a *smaller* t_max=2.39 (unexploited headroom, new finding), CARDIAC_MYOSIN 0.815 (inherits that target's 5TBY caveat).** | [[TASK-0110]] |
| 12 | Is the labeled pocket even present in the apo topology (HYP-P8), measured directly rather than inferred from other findings? | **resolved 2026-07-17, extended 2026-07-18 once [[TASK-0128]] unblocked cumulative overlap for all 3 targets — all classify `LEARNABLE`, not the clean "KRAS is cryptic" story the panel expected.** KRAS_G12C: pocket RMSD 2.27x background, but cumulative overlap 0.638 — well above the 0.5 low-overlap bar — meaning the apo→holo direction IS substantially spanned by soft ANM modes, contradicting the panel's own Sec.4 prediction. BCR_ABL1: pocket moves *less* than background (ratio 0.49) and CO=0.794, consistent with its prior "apo-computable structural prior" framing (TASK-0104), not a cryptic opening. CARDIAC_MYOSIN: ratio 1.32, CO=0.584 — also `LEARNABLE`, though confounded by its own 5TBY data-quality issue and should not be read as cleanly as the other two. **Superseded for KRAS_G12C, 2026-07-20 ([[TASK-0139]], via [[TASK-0133]]'s pocket-restricted CO): KRAS_G12C is `AMBIGUOUS`, not `LEARNABLE`** — see row 17 and `RESULTS.md`'s own learnability-gate section for the full resolution. BCR_ABL1/CARDIAC_MYOSIN's `LEARNABLE` verdicts stand unchanged.** | [[TASK-0139]], [[TASK-0120]], [[TASK-0128]] |
| 13 | Was `most_impactful_term = V_R` (reported in every prior ablation run) a real physics finding, or an artifact of `V_R`'s ~30x-larger normalization scale vs. `V_C`/`V_M`? | **resolved 2026-07-18: artifact.** All five terms are now individually z-scored (std 1 each); `V_R`'s variance share drops from 88.8% to a structural 15.4%, and `lam_C`/`lam_M` go from unreachable (0.1% share each) to 3.8% each. Real-target ablation (KRAS_G12C, BCR_ABL1) now gives `most_impactful_term = V_B` on both, with `V_R` among the *least* impactful on KRAS_G12C. Does not by itself fix the separate proximity confound in the CTQW observable (§2.3) — measurably weakens it (ρ_euclid 0.71-0.83 → 0.22-0.47) but does not eliminate it. | [[TASK-0121]] |
| 14 | Does the cross-target pattern (beats chance, not floor; raw AUC overstates signal) hold on targets no review cycle has ever seen, run under the fully gauge-fixed pipeline — the direct mitigation for ~15 cycles of repeated exposure to the same 3 answer keys? | **resolved 2026-07-18: yes, 4/4.** PTP1B, CASPASE7, CASPASE1 (new), GLUCOKINASE (new) all land in `BEATS_CHANCE_NOT_FLOOR` with overlapping score/floor 95% CIs — none statistically decisive, same pattern as the mandatory set. PTP1B remains anti-correlated with its true (genuinely distal) pocket (AUC 0.205). `most_impactful_term` is never `V_R` on any of the 4 — independent cross-check of [[TASK-0121]] on data its own validation never touched. Ceiling intentionally deferred for all 4 (known-stale `ceiling.py::_PARAM_RANGES`, [[TASK-0116]]'s scope, not a shortcut taken here). | [[TASK-0081]], [[TASK-0127]] |
| 15 | Does KRAS_G12C's ceiling search (TASK-0046, 60 blind-random trials, `lam_*` sampled on a range ~25x [[TASK-0121]]'s own budget) actually support "very little headroom," or was the search exploring the wrong (physically invalid) space? | **resolved 2026-07-18: the "no headroom" conclusion is confirmed, not overturned, but the original 0.5250 number was itself somewhat inflated by the invalid range.** Corrected-range random search: 0.4735-0.4864 depending on seed convention (both below the original). Corrected-range + TPE strategy: 0.4908 (reproduced exactly at seed=7), marginally above the re-measured floor (0.4818, +0.009) — too small a margin to claim a real positive without [[TASK-0131]]'s permutation null, flagged not claimed. Cross-validates [[TASK-0110]]'s independent 0.4750 (different parameter axis, same near-chance conclusion). | [[TASK-0046]], [[TASK-0116]] |
| 16 | Is this project's headline output actually reproducible given identical seeded inputs, or has environmental nondeterminism been silently corrupting "before vs. after" comparisons ([[INV-0008]], the BCR_ABL1 gap discrepancy)? | **resolved 2026-07-19: reproducible — the hypothesis is refuted, not confirmed.** 3 independent repeats each of a spectral-gap eigendecomposition, a blind random search, and a TPE search all gave bit-for-bit identical results. BLAS thread-count variation (`1/2/4/8`) produces real but negligible drift (~1e-14 relative). The original 0.0374-vs-0.1933 discrepancy this hypothesis was raised from is directly ruled out as environmental (11 orders of magnitude too small) — traces instead to a stale cached object from 5 days before a later code change, not live nondeterminism. New `allostery.runlog` module (environment fingerprint + incremental wall/CPU-time JSONL logging) adopted in `scripts/reproducibility_audit.py`. | [[TASK-0135]], [[INV-0008]] |
| 17 | Does cumulative overlap onto the apo ANM's lowest 20 modes actually discriminate "spans *this pocket's* displacement" from "spans *any* same-sized displacement" — or does a random patch score just as high ([[TASK-0120]]'s CO half of the learnability conjunction, `REVIEW-panel-2026-07-17.md` §5.2)? | **resolved 2026-07-19, with a real complication found mid-task.** TASK-0120's own reported `CO(20)` turns out to be a *whole-structure* quantity (166-709 residues), not pocket-specific — confirmed directly, not assumed. A properly pocket-restricted CO (new `superpose.restricted_cumulative_overlap`; also fixed a real bug found along the way — naively slicing+renormalizing eigenvectors for a small subset breaks `CO(m)<=1`, up to 1.64 observed) compared against 1000 random same-sized patches/target: **only matters for KRAS_G12C** (the one target whose verdict actually depends on the CO half). KRAS_G12C's restricted CO=0.458 is *below* the 0.5 threshold (vs. 0.638 whole-structure) and would flip the verdict to `UNLEARNABLE_FROM_APO` — but sits at only the 93rd percentile of the random-patch null (p≈0.07, not decisive at this project's own significance bar). BCR_ABL1/CARDIAC_MYOSIN score *below* their random-patch medians (37th/13th percentile) but their verdicts are RMSD-determined regardless. **[[TASK-0139]], 2026-07-20: decided, not left standing — pocket-restricted CO is the correct quantity (RMSD half is already region-specific; a whole-structure CO answers a different question), and `co_threshold=0.5` is replaced by a direct significance test against this exact null once available (new `learnability_verdict(co_percentile=...)`). KRAS_G12C resolves to `AMBIGUOUS` (RMSD clears, CO evidence inconclusive at α=0.05) — not `LEARNABLE`, not `UNLEARNABLE_FROM_APO`. BCR_ABL1/CARDIAC_MYOSIN unchanged (RMSD-determined).** | [[TASK-0139]], [[TASK-0133]], [[TASK-0120]] |
| 18 | Does a published, classical (no MD, no quantum) GNM transfer-entropy method beat or match `H_new`/CTQW on this project's own 3 mandatory targets — "if you can't beat it, you don't have a result" (`REVIEW-panel-2026-07-17.md` §4 P1-6)? | **resolved 2026-07-19: no, on both counts, a mixed result reported as such.** New `transfer_entropy.py` (linear-Gaussian TE / Granger-causality closed form over GNM lagged covariance, verified against 2 real cited papers — one citation's author list was wrong in the filing task, corrected). Scored against all 3 real targets: AUC 0.4485/0.3497/0.5335 vs. floor 0.4818/0.5817/0.7921 — fails to clear the floor anywhere (0/3), and scores *lower* than `H_new`/CTQW's own current numbers (0.5901/0.5266/0.7272) on all 3, decisively so on 2. Neither "classical method already does the job" nor "the task itself is uniformly hard regardless of method" holds cleanly — `H_new` beats this specific classical baseline, which itself doesn't clear the floor. | [[TASK-0132]] |
| 20 | Is the pocket-label ligand-contact cutoff (4.5 Å, `holo_pocket_mask`, defines ground truth itself) knob-unstable the same way TASK-0075 proved the cumulative-overlap gate's own 4.5 Å-shaped threshold is (0.067–0.860 swings, 15/18 verdict flips)? | **resolved 2026-07-20: no, materially more stable — but not fully insensitive either.** Swept {4.0,4.5,5.0,5.5} Å on all 3 mandatory targets, re-scoring the same once-computed `H_new` occupation against each cutoff's regenerated label. `floor_cleared` never flips for any target across the whole grid. `classify_failure`'s finer diagnosis *does* flip for 2/3 targets at the grid's edges (KRAS_G12C `NO_FAILURE_DETECTED`->`NO_SIGNAL_IN_APO` at 5.5 Å; BCR_ABL1 `BEATS_CHANCE_NOT_FLOOR`->`NO_SIGNAL_IN_APO` between 4.0/4.5 Å) — real but narrow, nothing like TASK-0075's own instability. TASK-0047's pinned 4.5 Å KRAS_G12C fixture (21/21) confirmed exactly correct, but sits on a still-moving slope (the raw recovered residue set changes at every 0.5 Å step tested, both directions), not a stable plateau. CARDIAC_MYOSIN run against TASK-0124's new 8QYP structure (landed the same day) — flagged as not comparable to this document's other, 5TBY-era CARDIAC_MYOSIN numbers. | [[TASK-0114]], [[TASK-0075]], [[TASK-0047]] |

| 19 | Does *any* engineered Haken-Strobl dephasing rate gamma improve pocket **discrimination** (not transport efficiency) over the coherent walk, on real targets — HYP-P11, the collaborator's Idea #1 run with the correct scored quantity? | **resolved 2026-07-20: no, on all 3 targets tested (KRAS_G12C, BCR_ABL1, PTP1B), confirming the pre-registered NEGATIVE prediction.** No gamma clears the proximity floor with non-overlapping CIs anywhere; the best-of-8-gamma point's own permutation null is nowhere near significant (p=0.649/0.211/1.000, Bonferroni alpha=0.0167). Closed 2 real gaps in `propagators.haken_strobl` along the way (no incoherent-mixture source option; no time-averaged variant — both now added, `coherent`/`haken_strobl_time_averaged`). The task's own mandatory classical-limit sanity gate did *not* pass as literally specified at `t_max=25` (`rho(occ,-dist)` fell, not rose, with gamma) — root-caused to Zeno-regime suppression of the effective diffusion timescale at large gamma under a fixed `t_max`, confirmed genuine (not an integrator bug) by extending `t` alone at fixed gamma and recovering the expected rising trend. | [[TASK-0141]] |

| 21 | Does CARDIAC_MYOSIN's only surviving positive result rest on a defensible apo structure, or does resolving its 20 Å docked-homology-model caveat (5TBY) change the result itself (`REVIEW-panel-2026-07-16-v2.md` §1.2/§3, "do not build the only positive on a 20 Å docked homology model")? | **resolved 2026-07-20: resolving the structure removes the result.** Apo replaced 5TBY -> 8QYP (real 2.759 Å X-ray, same paper/deposition series and species as the existing 8QYR holo, RCSB-verified directly — resolves [[TASK-0128]]'s floppy-mode workaround for this target as a side effect, n_zero=10->6). Full re-run under the current closed-form convention: N drops 950->704, floor drops 0.7921->0.5679, actual AUC drops from 0.7912 ([[TASK-0129]]'s already-diminished number) to **0.5176**, `NO_SIGNAL_IN_APO` — matching BCR_ABL1's own diagnosis. The relayed 2026-07-20 lead proposing PDB 9GZ1 as a holo replacement was independently verified as real (*Science Advances* 2026-04-29) but not adopted — 8QYR remains the cleaner (higher-resolution, single-domain) structure; 9GZ1 stands as corroboration, not substitution. **No mandatory target now has a decisive positive result under the fully corrected pipeline.** Full detail: `COMPETENCE_MAP.md`'s own CARDIAC_MYOSIN section. | [[TASK-0124]], [[TASK-0129]], [[TASK-0128]] |

Full process history, run mechanics, and Acceptance-Scenario checklists
for this run live in `.ai/tasks/DONE/TASK-0079.005-run-mandatory-targets.md`
(or `.ai/tasks/TODO/` if not yet closed — check `.ai/COMMON.md`'s registry
for current status). This document is the one to read for the science;
that one is the one to read for what was done and by whom.
