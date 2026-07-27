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

**[UPDATED 2026-07-22, [[TASK-0144]]] TASK-0120's and TASK-0133's CARDIAC_MYOSIN rows
above (N=950/709 common, pocket RMSD 4.168 Å, ratio 1.32, whole-structure CO(20) 0.584,
restricted CO(20) 0.044) are superseded, not corrected in place** — they were computed
against the apo structure [[TASK-0124]] later retired (5TBY -> 8QYP, 2026-07-20), and
are kept verbatim above only as the historical record of what was measured against that
structure. They are also a coincidental case of a bug this task fixes: `superpose.
align_apo_holo`/`common_residues_by_resnum` matched apo/holo Cα atoms by raw `(chain,
resnum)`, with no remap for targets ([[TASK-0127]]'s `apo_chains`/`holo_chains` override)
where the same biological chain is deposited under different author chain letters in apo
vs. holo. 5TBY happened to share holo's chain letter, so the old numbers above were never
affected by this bug — but the new 8QYP apo (chain A) vs. 8QYR holo (chain B) pair is
exactly this shape, and produced 0 common residues / a `ValueError` before this fix.
Fresh, correct CARDIAC_MYOSIN numbers under the current (8QYP/8QYR) apo/holo pair, plus a
first-ever run of GLUCOKINASE (same latent bug shape, apo 1V4S chain A / holo 3H1V chain
X, never previously run through this gate), are in TASK-0144's own section below.

**[SUPERSEDED 2026-07-24, [[TASK-0150]]] TASK-0144's own CARDIAC_MYOSIN/GLUCOKINASE
re-run (row 26 of this document's own open-questions table, `LEARNABLE`/
`UNLEARNABLE_FROM_APO`, CO(20) 0.943/0.443) used the same whole-structure `cumulative_
overlap` bug this section's own TASK-0139 block already corrected for KRAS_G12C —
`scripts/learnability_gate.py` was never actually updated to call `restricted_
cumulative_overlap` despite TASK-0139's own Done section claiming it already had
(confirmed wrong by direct code/`git log` inspection, not assumed — see `superpose.
compute_learnability`'s own docstring and [[TASK-0150]]'s Done section for the full
account of that contradiction). Fixed as part of wiring the learnability gate into
`run_challenge.py`'s real end-to-end run (closing [[SEAM-0007]]/[[TASK-0059]] for a
live caller) — `learnability_gate.py` now calls the same corrected, shared
`superpose.compute_learnability` `run_challenge.py` does, so both paths agree by
construction, not by discipline.

| Target | RMSD ratio | Restricted CO(20) | Bare-threshold verdict | Prior (whole-structure CO) reading |
|---|---|---|---|---|
| KRAS_G12C | 2.27 | 0.458 | `UNLEARNABLE_FROM_APO` | `AMBIGUOUS` ([[TASK-0139]], needs the percentile null below to soften) |
| BCR_ABL1 | 0.49 | 0.175 | `LEARNABLE` | `LEARNABLE` (unchanged, RMSD-determined) |
| CARDIAC_MYOSIN (8QYP/8QYR) | 1.57 | 0.254 | **`UNLEARNABLE_FROM_APO`** | `LEARNABLE` (TASK-0144, whole-structure CO=0.943 — **verdict flips**) |
| GLUCOKINASE | 1.94 | 0.304 | `UNLEARNABLE_FROM_APO` | `UNLEARNABLE_FROM_APO` (unchanged; CO number corrected 0.443→0.304) |

**Headline: CARDIAC_MYOSIN's learnability verdict flips from `LEARNABLE` to
`UNLEARNABLE_FROM_APO` once both real fixes (TASK-0124's apo replacement + this
task's CO-quantity correction) are applied together** — neither fix alone produced
this reading (TASK-0144's own re-run, apo-corrected but CO-uncorrected, still read
`LEARNABLE`). This corroborates, from a fully independent measurement, [[TASK-0124]]'s
own headline finding that CARDIAC_MYOSIN's only surviving AUC positive was an
artifact of the retired 5TBY apo structure — the structure genuinely does not
support learnability under the real, corrected apo, not just the scored AUC.

**KRAS_G12C's own bare-threshold reading here (`UNLEARNABLE_FROM_APO`) is not a
retraction of [[TASK-0139]]'s own `AMBIGUOUS` resolution** — it is a *different,
weaker* comparison stated as such: [[TASK-0139]]'s `AMBIGUOUS` required the
1000-replicate random-patch null (only ever computed for the pre-TASK-0124
apo/holo pair, unaffected here since KRAS_G12C's own apo/holo were untouched by
TASK-0124/0144) to soften a bare-threshold `UNLEARNABLE_FROM_APO` reading down to
"genuinely undetermined." This section's own live/default computation
(`run_challenge.py`'s real end-to-end run, and `learnability_gate.py`'s own
default invocation) does not compute that null — too expensive for the main
pipeline, per [[TASK-0150]]'s own scope — so it reports the bare-threshold
verdict, with `co_percentile` available as an optional parameter for a caller
that has one. Both readings are real, both are documented, neither silently
overwrites the other.

**Not re-derived here, flagged as a real follow-up rather than assumed either
way**: a fresh 1000-replicate random-patch null against CARDIAC_MYOSIN's *new*
(8QYP) apo structure and GLUCOKINASE (never had one at all) would let both
targets' bare-threshold verdicts above be checked the same way TASK-0133/0139
checked KRAS_G12C's — out of scope for [[TASK-0150]] itself (a wiring task, not a
new statistical analysis), a natural next step for whoever revisits this gate.

Full detail: `.ai/tasks/DONE/TASK-0150-wire-learnability-into-run-challenge.md`,
`results_task0120/learnability_gate.json` (regenerated). **Correction, same day**:
this task's own Done section originally claimed the prior whole-structure-CO output
was snapshotted to a `.bak` file before regenerating — checked directly and found
false. The intended `cp` ran against an empty/nonexistent directory (no prior JSON
was present on this thread's disk to snapshot — TASK-0120/0144's own original runs
were never persisted here as files, only as the prose this document already
carries) and silently no-opped; the "backup done" report was never actually
verified. No data lost — the superseded numbers this correction refers to are the
ones already quoted verbatim in TASK-0120's/TASK-0144's own paragraphs above, which
were never touched or deleted — only the false claim of a separate `.bak` snapshot
is retracted here.

**[[TASK-0152]], 2026-07-24: CARDIAC_MYOSIN(8QYP)/GLUCOKINASE get the same
matched-null rigor KRAS_G12C already has — and both soften the same way.**
[[TASK-0150]]'s own bare-threshold verdicts (`UNLEARNABLE_FROM_APO` for both,
restricted CO 0.254/0.304) rested on a single point estimate with no null-
distribution context, exactly the gap [[TASK-0133]]/[[TASK-0139]] closed for
KRAS_G12C. Same 1000-replicate random-patch null (`scripts/learnability_gate_
patch_control.py`, extended with a `--target` option rather than duplicated),
same resolution pattern (`scripts/resolve_cardiac_glucokinase_learnability.py`,
mirroring `resolve_kras_learnability.py`):

| Target | RMSD ratio | Restricted CO(20) | Percentile in null | One-sided p | Bare-threshold verdict | Null-informed verdict |
|---|---|---|---|---|---|---|
| CARDIAC_MYOSIN (8QYP) | 1.57 | 0.254 | 85.7th | 0.143 | `UNLEARNABLE_FROM_APO` | **`AMBIGUOUS`** |
| GLUCOKINASE | 1.94 | 0.304 | 89.9th | 0.101 | `UNLEARNABLE_FROM_APO` | **`AMBIGUOUS`** |

**Both targets flip from `UNLEARNABLE_FROM_APO` to `AMBIGUOUS`** — the real pocket's
restricted CO sits *above* the random-patch mean for both (85.7th/89.9th percentile,
the same direction as KRAS_G12C's own 93rd), meaning the bare `co_threshold=0.5`
comparison was reading these regions as more anharmonic than a typical same-sized
patch actually is, on this null. Neither reaches this project's own decisive bar
(one-sided p<0.05, uncorrected) — same "elevated but not decisive" pattern as
KRAS_G12C (p≈0.07), now confirmed on 3 of the 4 targets this precise analysis has
ever been run on, not a one-off. **This is not a retraction of TASK-0150's own
bare-threshold reading** — it is the more rigorous of two legitimate readings,
exactly the relationship KRAS_G12C's own `AMBIGUOUS`/bare-threshold pair already
established; both numbers are documented, neither silently overwrites the other.
BCR_ABL1 remains the one target genuinely unaffected by any of this (RMSD ratio
0.49 < 1.5, never reaches the CO half of the conjunction regardless of null or
threshold). GLUCOKINASE's own chain-schema question ([[TASK-0081]]) is confirmed
resolved, not re-litigated — [[TASK-0127]]'s `apo_chains`/`holo_chains` fix already
made it runnable, independently reconfirmed here by a clean, real 1000-replicate run.

Full detail: `.ai/tasks/DONE/TASK-0152-cardiac-myosin-glucokinase-learnability-null.md`,
`RESULTS/results_task0152/learnability_gate_patch_control_task0152.json`,
`results_task0152_learnability_resolution/resolution.json`.

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

**[UPDATED 2026-07-26, [[TASK-0159]]] PTP1B's own `0.2050` row above is
computed at the finite-time `time_averaged_ctqw(t_max=15, n_steps=500)`
convention, confirmed directly (not assumed) to be ~104,000x short of
this target's own real AAKV convergence criterion — not the converged
value every other headline number now uses.** Re-scored under
[[TASK-0130]]'s converged closed form (`time_averaged_ctqw_converged`,
now also wired into the shipped `run_challenge.py` pipeline itself,
TASK-0159): **PTP1B's AUC is 0.4859, not 0.2050 — the verdict flips from
`BEATS_CHANCE_NOT_FLOOR` (anti-correlated, well below chance) to
`NO_SIGNAL_IN_APO` (essentially at chance)**, independently confirmed by
a real brute-force finite-time integration run all the way to true
convergence (877K-4.6M steps; TASK-0159's own real-target section,
`RESULTS.md`'s own open-questions row 39). Kept, not deleted, per this
document's own no-overwrite convention — this row now describes the
pre-TASK-0130 finite-time convention specifically, not this project's
current reported science.

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

## Coordinated-closure graph-openness premise (TASK-0143, HYP-P10, 2026-07-22)

Tests the premise the entire loop/multi-site-closure observable family (HYP-P9, HYP-P12)
depends on: are real holo-defined cryptic-pocket residues Euclidean-near but graph-hop-far
on the **apo** contact graph — i.e. does the open cleft mean the apo contact graph doesn't
"know" the pocket residues belong together. `REVIEW-panel-2026-07-20`'s own Falsifier A
already killed the *trivial* single-loop idea (at 8 Å a spatial cluster is already a
clique); the multi-site reframe survives only if real pockets carry this near-space/
far-graph signature. Renumbered from the batch's own `TASK-0139` (ID collision with an
unrelated, already-committed TASK-0139).

**Distinct from `cumulative_overlap`/`cryptic_openness_gate` ([[TASK-0059]]/[[TASK-0120]])
by construction, not just assertion**: new `allostery.closure` never imports `superpose` —
`openness_signature`/`graph_dist_matrix` operate on apo coordinates and the apo contact
graph alone, no ANM modes or holo displacement enter any computation here. That gate asks
a *dynamics* question (is apo→holo spanned by soft modes); this asks a *structural-graph*
question about the apo state alone — orthogonal, can agree or disagree.

**Method**: `openness_signature(pocket) = mean pairwise apo graph-hop distance / mean
pairwise Euclidean distance` among the holo-defined pocket residues (same 8 Å `enm_cutoff`/
4.5 Å `pocket_contact_cutoff` every other headline number uses). Matched-spread random-
closure null: ≥500 random same-size residue sets whose own mean pairwise Euclidean spread
falls within ±35% of the real pocket's (fixed, pre-registered, never tuned against the
outcome), scored identically. A synthetic positive-control gate (a horseshoe-arc
construction whose two open-end tips are Euclidean-close but graph-far only reachable by
traversing the whole arc) ran first and landed at the 100th percentile, confirming the
implementation before any real data was touched. Pre-registered verdict: **PASS** (premise
supported) requires >95th percentile **and** Bonferroni significance across the 7 targets
(α=0.05/7≈0.0071); **FAIL** requires ≤50th percentile; everything between is
**INSUFFICIENT**.

**Headline: 0/7 targets PASS.** The premise is not supported, and the multi-site-closure
family it gates ([[TASK-0140]], [[TASK-0142]]) has no confirmed non-proximity loop to
detect on this benchmark's real targets.

| Target | N | Pocket size | Graph-hop mean | Euclid mean (Å) | Real signature | Null | Percentile | p (uncorrected) | p (Bonferroni ×7) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| KRAS_G12C | 169 | 18 | 2.3856 | 11.57 | 0.2062 | 500/500 | 98.4 | 0.0160 | 0.1120 | INSUFFICIENT |
| BCR_ABL1 | 451 | 16 | 2.3500 | 10.30 | 0.2281 | 0/500 (20M attempts) | — | — | — | INFEASIBLE |
| CARDIAC_MYOSIN | 704 | 13 | 4.5769 | 13.23 | 0.3461 | 1/500 (20M attempts) | — | — | — | INFEASIBLE |
| PTP1B | 298 | 14 | 2.2308 | 10.79 | 0.2067 | 19/500 (20M attempts) | — | — | — | INFEASIBLE |
| GLUCOKINASE | 448 | 17 | 2.6618 | 11.76 | 0.2263 | 1/500 (20M attempts) | — | — | — | INFEASIBLE |
| CASPASE1 | 255 | 6 | 2.1333 | 9.62 | 0.2218 | 500/500 | 90.2 | 0.0980 | 0.6860 | INSUFFICIENT |
| CASPASE7 | 461 | 7 | 2.8571 | 14.82 | 0.1927 | 500/500 | 26.8 | 0.7320 | 1.0000 | **FAIL** |

Raw components added 2026-07-22 (`allostery.closure.pairwise_components`, always
computable independent of null feasibility — no rejection sampling involved). Notable:
6 of 7 targets cluster tightly at 2.1-2.9 graph hops despite Euclidean spreads ranging
9.6-14.8 Å; CARDIAC_MYOSIN is the one outlier at 4.58 hops (roughly double the rest) —
consistent with, not resolving, its own INFEASIBLE verdict: the raw number is the
largest in the set, but with no matched-spread null built there is no way to say
whether that reflects a real anomaly or just its own larger pocket spread (also the
second-largest in the set).

**The naive (uncorrected) reading and the corrected (Bonferroni) reading, tagged
separately, per this task's own requirement:** naively, KRAS_G12C's p=0.016 clears an
uncorrected α=0.05 bar (same shape as [[TASK-0131]]'s own uncorrected-but-not-Bonferroni-
significant KRAS_G12C ceiling finding) — but this does not survive correction for testing
7 targets (p=0.112). No target reaches significance either way once corrected. CASPASE7 is
the one target with a real, decisive result in *either* reading: its pocket is actually
*less* graph-far than a typical matched-spread random cluster (26.8th percentile) — the
opposite of HYP-P10's claimed direction, not just an absence of support for it.

**A real, substantive finding in its own right: the pre-registered null construction is
infeasible for most targets.** 4 of 7 targets could not reach 500 matched-spread replicates
even at 20,000,000 unbiased rejection-sampling attempts (`MAX_ATTEMPTS`, a compute-budget
parameter, raised without touching the ±35% tolerance/500 replicate count/8 Å cutoff this
task's own Constraints froze). Root cause, checked not assumed: a compact same-size residue
cluster matching a real pocket's spread is intrinsically rare among *uniform* random draws
over a large protein, since most such draws scatter across the whole fold rather than
clustering compactly by chance — real pockets are markedly more spatially compact than a
typical random same-size subset of their own structure. This is itself informative but a
distinct property from HYP-P10's own graph-openness claim, and the pre-registered
methodology (uniform rejection sampling) cannot test the latter when it cannot even
construct a comparison set for the former. Not fixed here (a validated fix would need a
different, more sophisticated sampling scheme — e.g. spatially-biased proposals with
importance correction — which changes the null's own statistical construction and is
explicitly Out of Scope to redesign after seeing the outcome); flagged as a concrete
methodological gap for whoever next revisits this premise.

**Two real bugs found and fixed along the way:**
1. `seed = BASE_SEED + (hash(target_name) & 0xFFFF)` used Python's built-in `hash()` on a
   string — salted per-process (`PYTHONHASHSEED`, a security feature since Python 3.3), so
   the derived seed silently differed on every invocation. Found directly: KRAS_G12C's
   percentile read 100.0 on one run and 99.4 on an identical-looking re-run. Fixed to
   `zlib.crc32(target_name.encode())`, a fixed deterministic function of its input.
2. The output JSON was written only once, at the very end — the first full-batch run was
   interrupted partway through and the already-completed KRAS_G12C/BCR_ABL1 results were
   lost, nothing having reached disk yet. Fixed to checkpoint after every target (the same
   design flaw [[TASK-0138]]'s own null script independently hit and fixed).

`CARDIAC_MYOSIN`'s `N=704` (not the `950` [[TASK-0126]]/[[TASK-0138]] used) reflects
[[TASK-0124]]'s already-landed apo re-anchor (5TBY → 8QYP) — confirmed directly against
that task's own resolution, not a bug in this task's own loading path.

Full detail: `.ai/tasks/DONE/TASK-0143-openness-premise-real-targets.md`,
`results_task0143_openness_premise/openness_premise.json`, new
`src/allostery/closure.py`, `scripts/openness_premise_test.py`,
`tests/test_closure.py`.

---

## Re-running the GNM cutoff sweep against the headline operator (TASK-0113, 2026-07-22)

**Does the cutoff conclusion TASK-0067 reached on a bare GNM Kirchhoff transfer to `H_new`
— the operator that actually produces every headline AUC in this document?** TASK-0067's
own "Caveat, stated plainly" already flagged that its benchmark used the raw GNM
Kirchhoff only (no potential terms, single-source `ground_state_relaxation` propagation
— TASK-0067 predates TASK-0095's rename and calls the same function by its old name) —
this task re-answers the same question directly against `H_new`, scored via both
propagators.

**A real, structural finding before running anything**: TASK-0067's sweep varies cutoff
*and* weight scheme (`contact_matrix(..., weight=scheme)` — binary/gaussian/exponential/
harmonic/invdist) on a bare Laplacian. `H_new`'s own base Laplacian
(`normalised_laplacian_alpha`) hardcodes `weight="exponential"` — there is no equivalent
weight-scheme knob on `build_H_new` to sweep (adding one would be the operator-redesign
this task's own Constraints explicitly exclude: "reuse `build_H_new`... this is a
cutoff/propagator sweep, not an operator-weight sweep"). This sweep is therefore
cutoff-only for `H_new` — a real difference from TASK-0067's own 2-axis grid, reported
rather than silently matched.

Method: `H_new` (default potential weights, per this task's Constraints) built at cutoff
∈ {7.5, 8.0, 10.0} Å on KRAS_G12C/BCR_ABL1 (TASK-0067's own 2 targets; CARDIAC_MYOSIN
excluded for the same data-quality reason, inherited not re-litigated), scored via
`time_averaged_ctqw_converged` (TASK-0130's closed form) and `ground_state_relaxation`
(`t_max=15`). TASK-0094's floor baselines recomputed per cutoff too (they read the same
GNM contact graph) for a fair, consistent comparison
(`scripts/h_new_cutoff_sweep.py`, `results_task0113_h_new_cutoff_sweep/`).
**Cross-validated**: the cutoff=8.0 Å row (the shipped default) reproduces
[[TASK-0130]]'s own independently-computed closed-form numbers for BCR_ABL1 exactly
(ctqw 0.5266, ground_state 0.6766) — confirms this script measures the same quantity the
production pipeline reports, not a divergent one.

| Target | Cutoff (Å) | Floor | AUC (ctqw) | ctqw cleared? | AUC (ground_state) | GSR cleared? |
|---|---|---|---|---|---|---|
| KRAS_G12C | 7.5 | 0.482 | 0.635 | Yes | 0.356 | No |
| KRAS_G12C | 8.0 | 0.482 | 0.590 | Yes | 0.375 | No |
| KRAS_G12C | 10.0 | 0.501 | 0.597 | Yes | 0.431 | No |
| BCR_ABL1 | 7.5 | 0.583 | 0.486 | No | 0.675 | **Yes** |
| BCR_ABL1 | 8.0 | 0.582 | 0.527 | No | 0.677 | **Yes** |
| BCR_ABL1 | 10.0 | 0.647 | 0.517 | No | 0.638 | **No** |

Aggregate (mean across both targets, matching TASK-0067's own reporting convention):

| Cutoff (Å) | Mean AUC (ctqw) | Mean AUC (ground_state) | TASK-0067 bare-Laplacian mean AUC |
|---|---|---|---|
| 7.5 | 0.560 | 0.515 | 0.423 |
| 8.0 | 0.558 | 0.526 | 0.420 |
| 10.0 | 0.557 | 0.535 | 0.432 |

**Headline, stated plainly — the aggregate agrees with TASK-0067, but hides a real,
decisive per-target verdict flip the aggregate view alone would miss:**

1. **At the aggregate level, `H_new`'s cutoff sensitivity is if anything *smaller* than
   the bare Laplacian's** (ctqw range 0.003, ground_state range 0.020, vs. TASK-0067's
   own 0.0124) — agrees with, and reinforces, "no significant aggregate difference."
2. **That aggregate stability is a coincidence of cancellation, not real insensitivity —
   checked directly, not assumed.** Per-target, ctqw's own AUC moves by a real
   ~0.04-0.05 across the grid for *each* target individually (KRAS_G12C 0.590-0.635;
   BCR_ABL1 0.486-0.527) — the two targets happen to move in **opposite** directions as
   cutoff increases, which is what keeps the 2-target mean flat. Exactly the failure mode
   this task's own Planned Validation warned against ("not collapsed into a single 'still
   fine' summary if the data shows otherwise").
3. **A real, decisive floor-crossing verdict flip: BCR_ABL1's `ground_state_relaxation`
   clears the proximity floor at 7.5 Å and 8.0 Å (the shipped default — matches this
   document's own current headline number, 0.677) but does NOT clear it at 10.0 Å**
   (0.638 vs. a floor that itself jumps to 0.647 at the wider cutoff). Both AUC and floor
   move with cutoff; their relative ordering flips. **This directly touches BCR_ABL1's own
   "apo-computable structural prior" finding** ([[TASK-0091]]/[[TASK-0102]]/[[TASK-0104]],
   open-questions row 1 above) — that finding's floor-clearing status is not robust to
   the GNM cutoff choice, a real disagreement with TASK-0067's "no significant
   difference" conclusion for this specific downstream claim. Not silently corrected here
   — cross-linked per this project's own convention; TASK-0102's own "largely
   seed-independent" finding is a different robustness axis (seed convention, not cutoff)
   and is unaffected.
4. **`time_averaged_ctqw`'s own floor-crossing/diagnosis story is fully stable across the
   grid for both targets** (KRAS_G12C always clears/`NO_FAILURE_DETECTED`; BCR_ABL1 never
   clears/`NO_SIGNAL_IN_APO`, all 3 cutoffs) — the flip above is specific to
   `ground_state_relaxation`, not both propagators.
5. **`H_new` scores meaningfully higher than the bare GNM Kirchhoff at every matching
   cutoff** (aggregate ctqw ~0.557-0.560 vs. ~0.420-0.432; ground_state ~0.515-0.535 vs.
   the same bare range) — the potential terms add real discriminative power beyond the
   contact graph alone, as designed. Not itself a new finding, but confirms the two
   sweeps are measuring meaningfully different operators, not restating the same result
   under a new name.

**Per this task's own Out Of Scope, TASK-0067's own bare-Laplacian result is not
re-litigated** — it remains correct for the narrower question it was built to answer.
This task's own scope was `H_new` specifically, and for `H_new` the cutoff choice is
functionally inert for `time_averaged_ctqw` but real and headline-relevant for
`ground_state_relaxation` on BCR_ABL1.

Full detail: `.ai/tasks/DONE/TASK-0113-cutoff-sweep-headline-operator.md`,
`results_task0113_h_new_cutoff_sweep/h_new_cutoff_sweep.json`,
`scripts/h_new_cutoff_sweep.py`.

---

## `select.py` invariance classification, closing `INV-0004` (TASK-0089, 2026-07-20)

Closes every row `INV-0004` seeded 2026-07-12 ([[TASK-0064]]) for `select.py`'s
four scoring functions (`focusing`, `source_specificity`, `ballistic_exponent`,
`unsupervised_score`) — per `INVARIANCE_PROTOCOL.md`'s own rule, "no
transformation table → not reportable." 35 new tests, `tests/test_select.py`
(the existing suite is unchanged, per this task's own Planned Validation).

**GAUGE (residue relabeling, candidate order) — verified, with one real carve-out.**
Permuting `H`'s indices + `source` consistently on a genuinely asymmetric random
graph (not the symmetric path/star/complete fixtures, which could hide a labeling
bug) leaves `focusing`, `ballistic_exponent`, and `unsupervised_score`'s per-
candidate scores unchanged to `atol=1e-9`. **`source_specificity` is the
exception, and a real finding**: with its default *sub-sampled* `n_alt` (< every
non-seed node), the score is **not** relabeling-invariant — root-caused (not
assumed) to `others = [i for i in range(N) if i not in excluded]` always being
ascending-sorted *by label*, with `rng.choice` then selecting by *position* in
that array, so a relabeling permutation changes which alternates a fixed seed
draws. Confirmed directly that this disappears entirely once `n_alt` is
exhaustive (every non-seed node used, no sub-sampling) — isolates the sampling
step, not the underlying Hellinger-distance/`time_averaged_ctqw` computation, as
the source. **Not fixed at the algorithm level**: a fix would mean sampling by a
canonical graph-intrinsic order instead of raw label position (the exact
`anm_modes` eigenvalue-not-index precedent `INVARIANCE_PROTOCOL.md` itself
cites) — but that changes what "a random sample of other nodes" means (a
deterministic subset every time, not a genuine draw), a bigger, unrequested
behavior change for a real but bounded effect, not a wrong-answer bug.
Reclassified GAUGE→KNOB instead (report the spread, don't force a false pass),
and flagged directly in `source_specificity`'s own docstring.

**KNOB — all four rows characterized, on the same synthetic 12-node fixture:**

| Row | Measured spread | Classification |
|---|---|---|
| `focusing`'s `t_max`/`n_steps` | ~0.02-0.04 | Least sensitive of the four |
| `source_specificity`'s `t_max`/`n_alt`/seed | ~0.06-0.17 | Moderate, real |
| `ballistic_exponent`'s `t_values` window | 0.084-0.525 (>6x) | **This module's dominant KNOB**, by an order of magnitude |
| `unsupervised_score`'s scalar vs. multi-index `source` | ranking **flips** (`H_COMPLETE`→`H_STAR`) | Confirms `REVIEW-panel-2026-07-16-v2`'s project-wide seed-cardinality finding, locally |

`ballistic_exponent`'s time-window sensitivity is a real transport-regime effect
(early ballistic-like spreading vs. later saturation/diffusive crossover in the
log-log slope fit), not numerical noise — any reader treating a single
`ballistic_exponent` value as a stable point estimate should read this row
first.

**SIGNAL — null-controlled.** A naive 2-candidate `unsupervised_score` z-score
competition is a coin flip regardless of the true underlying gap (z-scores of 2
points are always exactly ±1, checked directly before relying on it) — so the
null control instead compares `H_STAR`'s *raw* `focusing`/`source_specificity`
against a batch of 30 independently-drawn random graphs of the same node/edge
count (the same distribution-level discipline this project's own permutation
nulls use elsewhere, [[TASK-0131]]/[[TASK-0123]]): `H_STAR` clears the random
batch's mean+1 std.dev. on focusing and the mean on specificity. The degenerate
single-candidate case is confirmed to return exactly `0.0` (the `_zscore`
epsilon guard), not NaN/inf.

Full detail: `.ai/invariants/INV-0004-select-unsupervised-score.md`,
`.ai/tasks/DONE/TASK-0089-select-invariance-classification.md`,
`tests/test_select.py`.

---

## Path-ensemble + percolation connectivity between active site and pocket (TASK-0136, 2026-07-22)

Raised directly by the orchestrating user, 2026-07-18: "would it make sense to actually
make a 'shortest path' finding algorithm between known active/allosteric sites and do
any form of percolation on the outcome? What would it potentially model?" Purely
topological (no propagator, no `t_max`, no seed coherence, no clock) -- the deliberate
structural complement to CTQW/GSR/ENAQT, outside the current P0 gauge-fixing batch's
confound axes entirely. Models a real, pre-existing distinction in the allostery
literature (Chennubhotla & Bahar's correlation-network path analysis, Nussinov & Tsai's
ensemble-allostery framing, both cited in the challenge statement itself): is
communication carried by a **narrow, fragile bottleneck** (one dominant channel) or a
**broad, redundant subnetwork** (many independent routes)?

**Correction to this task's own filing**: cites "`potentials.py`'s existing
`W_invdist`-style weighting" -- `potentials.py` has no such thing (grepped directly).
The actual existing invdist weighting is `hamiltonians.contact_matrix(weight=
"invdist")`, reused from the correct module.

New `allostery.percolation`: `shortest_path_ensemble` (Dijkstra + Yen's-algorithm
sub-optimal-path enumeration between two residue sets, via a virtual super-source/sink
reduction), `set_edge_connectivity` (Menger's-theorem edge connectivity + the literal
min-cut edges), `percolation_threshold` (Union-Find sweep from strongest edge to
weakest, reports the exact edge that first connects the two sets). New `baselines.
connectivity_robustness` (part c) -- edge-connectivity from a seed set to every
residue, a strict generalization of `hop_from_seed`'s own shape, scored as a blind
baseline.

**Real bug found and fixed before trusting any real-target number**: the first run
showed edge connectivity saturating at *exactly* `min(|active site|, |pocket|)` on all
3 targets, with an *empty* min-cut -- too clean a pattern to accept without checking.
Root cause: the virtual super-source/sink construction gave each seed member a single
**unit-capacity** edge, on the (wrong) reasoning that a k-residue set cannot originate
more than k edge-disjoint paths. Confirmed wrong directly with a synthetic check: a
single node with 3 real fan-out edges supports true edge-connectivity 3, not 1 -- a
set's cardinality does not bound route redundancy, its own graph degree does.
Unit-capacity virtual edges silently capped every result, and the "empty cut" was this
construction's own bookkeeping, not real graph structure. Also found while fixing:
`networkx.edge_connectivity`/`minimum_edge_cut` do not accept a `capacity` argument at
all (checked directly, not assumed) -- switched to the capacitated equivalents,
`maximum_flow_value`/`minimum_cut`. Fixed: virtual edges get a large capacity, real
graph edges get `capacity=1` (Menger's-theorem counting is otherwise unweighted,
unchanged). Re-running after the fix changed `set_edge_connectivity`'s numbers
dramatically (13-18 -> 68-76); `connectivity_robustness`'s own per-residue AUC was
**unaffected** (a single target node's own real degree, not the seed-set's cardinality,
was already the binding constraint there in every case checked -- confirmed by direct
re-run comparison, not assumed).

**Headline: all 3 mandatory targets show broad, redundant connectivity -- no narrow,
fragile bottleneck on any target.**

| Target | (a) shortest path length | (a) ensemble size (tol=10%) | (b-i) edge connectivity | (b-ii) merge distance (Å) | (b-ii) edges added to merge |
|---|---|---|---|---|---|
| KRAS_G12C | 3.753 | 2 | **73** | 3.75 | 2 |
| BCR_ABL1 | 7.522 | 1 | **76** | 3.82 | 355 |
| CARDIAC_MYOSIN | 3.809 | 1 | **68** | 3.81 | 149 |

68-76 edge-disjoint routes connect the active site to the pocket on every target -- an
order of magnitude above what a narrow bottleneck would look like; the min-cut edge
lists (full detail in the JSON results) each span dozens of distinct residue pairs, not
a single dominant chokepoint. Separately, KRAS_G12C's active site and pocket merge
after only the 2 strongest edges in the *entire* apo graph are added (3.75 Å) -- an
independent, purely topological confirmation of this project's own established finding
that KRAS_G12C's active site and pocket sit unusually close in 3-D space (the
proximity-confound history this project has tracked since TASK-0094). BCR_ABL1/
CARDIAC_MYOSIN merge later in the global strength ordering (355/149 edges) despite
similarly short absolute merge distances -- both are larger structures with many
stronger (shorter) contacts elsewhere ranked ahead of the specific bridging edge.
Sub-optimal-path tolerance (this task's own Open Question, Implementer's call):
`tol=0.10`, `max_paths=50` -- never bound in practice (largest ensemble found: 2 paths,
KRAS_G12C; BCR_ABL1/CARDIAC_MYOSIN each have a unique shortest path, no near-ties).

**Part (c), `connectivity_robustness` as a blind scored baseline -- mixed, mostly-
negative, reported as such:**

| Target | AUC | Floor | Beats floor? | Stratified mean AUC | Stratified max AUC |
|---|---|---|---|---|---|
| KRAS_G12C | 0.5587 | 0.4818 | **Yes** (+0.0769) | 0.510 | 0.820 |
| BCR_ABL1 | 0.5272 | 0.5817 | No (−0.0545) | 0.535 | 0.723 |
| CARDIAC_MYOSIN | 0.4178 | 0.5679 | No (−0.1501, below chance) | 0.372 | 0.581 |

1/3 targets beats its own floor. TASK-0123's own `stratified_auc` cross-read was
**actually run** (not cited by analogy) on `connectivity_robustness`'s scores, same
hop-shell construction TASK-0123 used elsewhere: stratified mean AUC sits near chance
on KRAS_G12C/BCR_ABL1 and *below* chance on CARDIAC_MYOSIN -- most of this baseline's
raw AUC is the same distance/degree confound TASK-0123 already found pervasive across
this project's operator register, exactly the concern this task's own Constraint
anticipated rather than assumed exempt.

**Dumbbell gate (TASK-0103), a clean negative distinct in kind from GSR's
well-following**: new `TestConnectivityRobustnessDumbbellGate` -- AUC is **exactly
0.500 in every cell** (C1-C4), not merely weak. `connectivity_robustness` is
deliberately unweighted (Menger's-theorem route *counting*); the dumbbell's DRUG/DECOY
bridges are topologically identical (same node/edge count), differing only in edge
*weight* -- there is no edge-count signal for an unweighted measure to find here, by
design, not by defect.

**Answer to this task's own central question**: the active site and known allosteric
pocket are broadly, redundantly connected on apo topology alone, on all 3 mandatory
targets -- not a narrow communication bottleneck. A real, decisive, purely topological
finding, independent from and consistent with this project's established
proximity-confound history. As a blind scoreable baseline, `connectivity_robustness`
beats the proximity floor on only 1/3 targets and its signal is mostly explained by the
same distance confound found pervasive elsewhere in this project's register -- a real,
mostly-negative result for part (c) specifically, distinct from parts (a)/(b)'s own
decisive diagnostic finding.

Full detail: `.ai/tasks/DONE/TASK-0136-percolation-connectivity-robustness.md`,
`results_task0136_percolation/percolation_connectivity.json`, new
`src/allostery/percolation.py`, `baselines.connectivity_robustness`.

---

## Apo/holo chain-letter remap for `align_apo_holo` (TASK-0144, 2026-07-22)

**Real bug, found live while executing [[TASK-0124]]'s CARDIAC_MYOSIN apo replacement:**
`superpose.common_residues_by_resnum`/`align_apo_holo` matched apo/holo Cα atoms by the
raw `(chain_id, resnum)` pair, verbatim. [[TASK-0127]] added an `apo_chains`/`holo_chains`
per-role config override for targets where the same biological chain is deposited under
different author chain letters in apo vs. holo (its own worked example: GLUCOKINASE, apo
1V4S chain A, holo 3H1V chain X) — wired correctly into `clean_from_config`/
`run_challenge._load_apo_holo` (which only controls which chains are *loaded*, confirmed
by reading `clean.py:241`), but `superpose.py`'s own correspondence never got the same
treatment. Confirmed directly: on TASK-0124's new CARDIAC_MYOSIN pair (apo=8QYP chain A,
holo=8QYR chain B), `common_residues_by_resnum` returned 0 common residues, and
`align_apo_holo` raised (`< 3 common Ca pairs`). GLUCOKINASE has the identical latent
shape (apo chain A, holo chain X) but had never actually been run through
`align_apo_holo` before this task — TASK-0120/125/133's own target lists never include it.

**Fix**: `common_residues_by_resnum(apo, holo, chain_map=None)` and
`align_apo_holo(apo, holo, chain_map=None)` — an additive `chain_map: Optional[Dict[str,
str]]` parameter (holo chain letter -> apo chain letter), default `None`, byte-identical
to the previous behavior for every caller that doesn't pass one (none of the 3 mandatory
targets use `apo_chains`/`holo_chains` as of this filing). New `superpose.
chain_map_from_config(target_config)` builds it from a target's `apo_chains`/
`holo_chains` (`dict(zip(holo_chains, apo_chains))`) when both are set, `None` otherwise
— threaded through every real call site found by re-grepping the whole repo at pickup
time (this task's own filing already flagged the caller list might have grown):
`superpose.run_superpose` (already had `target_config` in scope), `scripts/
learnability_gate.py`, `scripts/learnability_gate_patch_control.py`, `scripts/
holo_diagnostic_comparison.py`, and `scripts/kras_auc_reconciliation.py`'s
`_holo_mapped_source` (KRAS_G12C-only, never actually exercises a non-`None` map, threaded
for consistency). `analysis.py`'s own mention of `align_apo_holo` is docstring-only, not a
real call — confirmed, not touched.

**Re-run `scripts/learnability_gate.py` (TASK-0120's own script) for CARDIAC_MYOSIN under
the new 8QYP/8QYR pair, and for GLUCOKINASE for the first time ever:**

| Target | N (common) | Pocket RMSD | Background RMSD | Ratio | Whole-structure CO(20) | Verdict |
|---|---|---|---|---|---|---|
| CARDIAC_MYOSIN (8QYP/8QYR) | 704 (698) | 1.335 Å | 0.853 Å | **1.57** | 0.943 | `LEARNABLE` |
| GLUCOKINASE (1V4S/3H1V) | 448 (446) | 0.640 Å | 0.330 Å | **1.94** | 0.443 | `UNLEARNABLE_FROM_APO` |

**CARDIAC_MYOSIN's coverage jumps from 709/950 (75%) to 698/704 (99%)** — the old 5TBY
pair's low common-residue coverage (flagged in TASK-0120's own writeup as a possible
alignment-quality issue) was, at least in significant part, this same chain-letter defect
silently discarding correspondences it should have kept, not (only) a genuine
structural-quality gap. Overall alignment RMSD also drops sharply (3.75 Å -> 1.18 Å).
**GLUCOKINASE is the first target in this project's history to classify
`UNLEARNABLE_FROM_APO` on the RMSD half of the conjunction failing to matter — both
conditions are met here** (ratio 1.94 >= 1.5 threshold, CO(20) 0.443 < 0.5 threshold) —
the first real case, on a mandatory-adjacent target, where TASK-0120's kill criterion
actually fires as originally designed.

**Caveat, stated plainly**: both numbers above use `learnability_gate.py`'s own
whole-structure `cumulative_overlap`, the same quantity [[TASK-0133]]/[[TASK-0139]] later
found conflates "the low-mode subspace explains *some* substantial motion somewhere" with
"...explains *this pocket's* motion" — this task did not re-run either target through
`restricted_cumulative_overlap`/the corrected `learnability_verdict(co_percentile=...)`
path (out of this task's own scope; a natural follow-up mirroring [[TASK-0133]]'s own
random-patch-null construction, not done here for either target). GLUCOKINASE's `ratio`
half alone already clears its own bar independent of which CO quantity is used, so its
verdict is not contingent on this caveat; CARDIAC_MYOSIN's is not either (ratio 1.57 and
whole-structure CO 0.943 both agree with `LEARNABLE` well clear of either threshold), but
the restricted-CO number is unmeasured for both and should not be assumed to agree.

Full detail: `.ai/tasks/DONE/TASK-0144-align-apo-holo-chain-letter-mismatch.md`,
`results_task0144_learnability_rerun/learnability_gate_rerun.json`,
`tests/test_superpose.py::TestCommonResiduesByResnum`/`TestAlignApoHolo`'s new
chain-letter-remap cases.

---

## CPU-time re-verification + long-job convention (TASK-0134, 2026-07-22)

[[P-0005]]: TASK-0110's "a single `time_averaged_ctqw` call did not return after 2+
hours" claim rested on a single process-state check (`R`, active) at kill time, not
continuous CPU-time evidence — a process starved by contention (already proven real
in this sandbox, [[TASK-0111]]) or suspended/resumed would look identical at one
checkpoint. Re-ran the same call (real KRAS_G12C, `H_new`, AAKV-prescribed
`t_max`/`n_steps`) with continuous `allostery.runlog.RunLogger` instrumentation
instead — new `scripts/task0134_cpu_time_reverification.py`, 4-thread BLAS cap
matching the original script's own environment.

**Real complication found live, before the run even started**: the same AAKV
formula on the same target now prescribes `t_max=1.26e6`/`n_steps=877,811` —
~15x smaller than TASK-0110's original `t_max=4.82e6`/`n_steps~1.3e7` — `H_new`'s
spectrum shifted after [[TASK-0121]]'s potential renormalization (landed the day
after TASK-0110's original measurement). The literal historical scenario is no
longer reproducible, so this task ran the full *current* prescription end to end
instead (877,811 steps, not truncated) — enough to answer the actual question.

**Result: 950.2s (~15.8 min), full prescription completed, not killed early. 438
samples, `cpu_elapsed_s/wall_elapsed_s` held at 4.05 ± 0.035 throughout (min
3.958, max 4.157) — no drops anywhere in the sequence.** Clean evidence of
continuous 4-thread execution for the entire interval, directly closing the gap
P-0005 named. Extrapolated to the original 1.3e7-step scenario, the re-verified
rate implies ~3.9 CPU-wall-clock hours — consistent with, not contradicting,
"still computing after 2+ hours." **The original claim is corroborated, not
inflated.**

**A separate, real methodological finding**: an uncapped calibration run (before
the thread cap was applied) measured CPU-time at ~16x wall-clock on this 16-core
machine — multithreaded BLAS parallelism, not contention, easy to get backwards
on a first read. The real contention/suspension diagnostic is the *stability* of
the ratio across successive samples, not its absolute magnitude.

Downstream citations updated additively (corroboration + the parameter-drift
fact, not corrections): `.ai/invariants/INV-0005-propagator-time-parameters.md`,
`.ai/seams/SEAM-0012-propagator-convergence-vs-real-defaults.md`,
`.ai/memory/shared/pitfalls.md`'s `P-0005` entry.

**Part 2**: new `.ai/reference/LONG_JOB_CONVENTION.md` (cross-linked from
`IMPLEMENTER_SPINUP_BRIEF.md`/`OPERATION_PROTOCOL.md`) — the ~10-15min
synchronous-blocking threshold, harness-tracked (`run_in_background`) vs.
OS-level (`nohup`/`disown`/`tmux`) detachment for two distinct time horizons,
monitor-by-tail not poll, the ratio-stability diagnostic above, and an explicit
HITL hand-off section (what "done"/"healthy"/"stalled" look like in a
`RunLogger` trace, where to post checkback instructions durably). No new
tooling built — generalizes `allostery.runlog.RunLogger` ([[TASK-0135]]) and
this environment's own background/scheduling primitives, already adequate.

Flagged (not re-run), sharing the same unverified-CPU-time shape: [[TASK-0105]]'s
ENAQT per-gamma wall-clock timings, [[TASK-0068]]'s NISQ Trotter-step timing.

Full detail: `.ai/tasks/DONE/TASK-0134-cpu-time-verification-and-long-job-convention.md`,
`results_task0134_cpu_time/cpu_time_reverification.jsonl`,
`.ai/reference/LONG_JOB_CONVENTION.md`.

---

## Chiral (broken-time-reversal) circulation observable (TASK-0140, HYP-P9, 2026-07-23)

Peierls-substituted complex-hopping Hamiltonian (symmetric-gauge vector potential,
midpoint line-integral phase) → infinite-time-averaged bond current (projector-dephasing
generalization of [[TASK-0130]]'s closed form to this off-diagonal bilinear quantity) →
Helmholtz-Hodge split, scoring only the divergence-free (circulating) part — proximity-
orthogonal by construction, not by tuning. Reference script (`chiral_observable.py`)
confirmed absent from this repo; reconstructed from `HYP-P9`'s own description + cited
literature (Zimborás 2013, Lu 2016). New `allostery.chiral`, 35 new tests.

**Real physics finding made while building the test suite**: a bare N-cycle ring gives
*exactly* zero converged circulation from a diagonal seed, at any flux — confirmed
directly (idealized rings, randomly-weighted-and-phased rings, a bipartite-preserving
ring+chord, even a uniform-weight triangle), not a corner case anyone anticipated. Real
protein contact graphs (dense 3-D packing, degree well above 2 everywhere) are not at
risk of this, but it ruled out a bare ring as this module's own regression-test
fixture — an irregular, next-nearest-neighbor-widened ring (`_triangulated_asymmetric_
coords`) is used instead. Full mechanism discussion: `allostery/chiral.py`'s own
docstring §4.

**GATE 1 (dissociates coupling from well-depth) and GATE 2 (beats floor on a synthetic
distal loop pocket) both re-verified as passing on this fresh reconstruction** — not
inherited from the missing script's claimed status. GATE 1 needed a new loop-dumbbell
fixture (the original TASK-0103 dumbbell is a cycle-free tree, and Peierls phases on a
tree gauge away to nothing): circulation follows coupling (mean AUC 0.81/0.19 across 8
seeds in the two conflict cells), `ground_state_relaxation` on the identical topology
follows the well instead (0.0/1.0) — a clean, deterministic dissociation. GATE 2 (a
backbone forking into a tightly-spaced POCKET branch vs. a normally-spaced DECOY branch
at matched distance from the seed): circulation clears the standard floor check
(AUC 0.93–0.98 across 6 seeds); occupation does not. This reconstruction's own numbers
(not the lost original's cited 0.33/0.6–0.97): rho(occ,-dist) ≈ -0.6 to -0.65,
rho(circ,-dist) ≈ -0.18 to +0.15 — same qualitative pattern, different exact figures, as
expected for an independently-built synthetic network.

**Real run, all 3 mandatory + 4 ASD targets, `H_new`'s own apo graph, full active-site
seed (incoherent mixture):**

| Target | circ AUC | occ AUC | max floor AUC | CI overlap | ρ(circ,-dist) | ρ(occ,-dist) | strat-AUC perm p |
|---|---|---|---|---|---|---|---|
| KRAS_G12C (mand.) | 0.702 | 0.653 | 0.546 | yes | -0.259 | -0.700 | **0.0030** |
| BCR_ABL1 (mand.) | 0.419 | 0.560 | 0.619 | yes | -0.479 | -0.738 | 0.5005 |
| CARDIAC_MYOSIN (mand.) | 0.395 | 0.531 | 0.583 | yes | -0.223 | -0.712 | 0.6566 |
| PTP1B (ASD) | 0.640 | 0.495 | 0.492 | yes | -0.286 | -0.695 | **0.0020** |
| GLUCOKINASE (ASD) | 0.677 | 0.657 | 0.863 | yes | -0.392 | -0.594 | 0.0120 |
| CASPASE1 (ASD) | 0.639 | 0.676 | 0.919 | yes | -0.374 | -0.581 | 0.4961 |
| CASPASE7 (ASD) | 0.530 | 0.600 | 0.758 | yes | -0.260 | -0.434 | 0.8434 |

**Pre-registered verdict: FAIL** — CI overlap is `True` on every target, so the primary
bar (beats floor AND non-overlapping 95% block-bootstrap CIs) is not met anywhere,
consistent with [[TASK-0143]]'s own FAIL on the graph-openness premise this observable
depends on. **A distinct, real, honestly-reported suggestive signal**: KRAS_G12C
(mandatory) and PTP1B (ASD) both clear the Bonferroni-corrected threshold (0.05/7 =
0.00714) on the independent stratified-AUC permutation-null statistic — real, non-random
by that test, just not enough to clear the stricter CI bar. **The proximity-
orthogonality claim itself holds cleanly on 7/7 targets** — ρ(circ,-dist) is smaller in
magnitude than ρ(occ,-dist) everywhere (circ range -0.22 to -0.48 vs. occ range -0.43
to -0.74) — circulation genuinely measures something other than distance; that
something just doesn't clear the discrimination bar on these targets. Field-scale
sensitivity is real and target-dependent (PTP1B's AUC spans 0.429–0.818 across the
0.02–0.2 sweep, crossing the floor in both directions).

[[TASK-0142]]'s own hard gate ("run only if TASK-0143 or TASK-0140 shows life") remains
unmet — this result does not open it. Full detail:
`.ai/tasks/DONE/TASK-0140-chiral-circulation-observable.md`,
`results_task0140_chiral/chiral_circulation_real_run.json`.

---

## Low-mode PRS/DCC real-target run (TASK-0149, 2026-07-24)

**Two proximity-orthogonal-by-construction observables** — low-mode Perturbation
Response Scanning (`prs_low`, Atilgan 2009/Ikeguchi 2005 LRT, ANM pseudo-inverse
restricted to the `k` lowest non-trivial modes) and low-mode GNM dynamic
cross-correlation magnitude (`dcc_low`) — delivered pre-built and pre-tested
(`.ai/reviews/2026-07-22/`, real code against this project's own `superpose.anm_modes`/
`potentials._kirchhoff_eigh`, but **executed only on synthetic data** — RCSB was
unreachable from the delivering thread's own sandbox, honestly disclosed rather than
fabricated. Real-target execution was this task's own job. Ported unmodified into
`src/allostery/lowmode_predictor.py`, `tests/test_lowmode_predictor.py`,
`scripts/lowmode_predictor_synthetic_control.py`; the 3 delivered tests re-verified
passing as-is (3/3, not re-trusted from the delivering thread's own account).

**A real bug found and fixed in this task's own new evaluation script** (not in the
ported `lowmode_predictor.py` itself, which is unaffected): the first version of
`scripts/lowmode_predictor_real_run.py` computed `rho(score, shells)` where `shells`
is the real, non-negative hop distance (`_prepare_target`'s own `-hop_from_seed(...)`,
and `hop_from_seed` itself already returns *negative* hop — double negation), while
the delivered synthetic control's own convention (`lowmode_predictor_synthetic_
control.py`, `test_lowmode_predictor.py`) is `spearmanr(score, -hop)`. The first run's
printed rho values were sign-flipped relative to that convention — caught by checking
the raw per-shell score trend directly against the printed sign before trusting it
(KRAS_G12C's `dcc_low` mean score *rose* near the seed and *fell* with distance, the
opposite of what the first run's positive-sign labeling implied), not assumed correct
from the script running without error. Fixed and re-run; all numbers below use the
corrected, delivered-convention sign.

Real-target evaluation follows [[TASK-0118]]'s current seed convention (full
active-site array, incoherent mixture) — not the delivered code's own scalar-seed
synthetic default — and reuses [[TASK-0123]]'s own `_prepare_target`/`stratified_auc`/
well-powered-shell-filter/permutation-null machinery directly (`scripts/
distance_stratified_evaluation.py`'s own functions, same shapes), per this task's own
Constraint to gate through that methodology rather than re-derive an evaluation
pipeline. `k_modes` swept over `{5, 10, 15, 20}`.

**Headline (k=20, the delivered code's own default / this project's `CO(20)`
convention — the primary, non-redundant comparison; full k-sweep below as
sensitivity):**

| Target | Observable | Whole-graph AUC | Floor | ρ(score, −hop) | Well-powered stratified max AUC | Null median | p (uncorrected) |
|---|---|---|---|---|---|---|---|
| KRAS_G12C | `prs_low` | 0.481 | 0.482 | **−0.18** | 0.595 | 0.646 | 0.672 |
| KRAS_G12C | `dcc_low` | 0.522 | 0.482 | **+0.52** | 0.506 | 0.635 | 0.878 |
| BCR_ABL1 | `prs_low` | 0.188 | 0.582 | **−0.26** | 0.439 | 0.615 | 0.918 |
| BCR_ABL1 | `dcc_low` | 0.378 | 0.582 | **+0.50** | 0.518 | 0.619 | 0.803 |
| CARDIAC_MYOSIN | `prs_low` | **0.836** | 0.568 | **−0.40** | **0.922** | 0.582 | **0.006** |
| CARDIAC_MYOSIN | `dcc_low` | **0.711** | 0.568 | **+0.48** | **0.962** | 0.583 | **<0.001** |

**KRAS_G12C and BCR_ABL1: genuinely dead, per the delivering thread's own predicted
possible outcome.** No cell at any `k` reaches significance (uncorrected p ranges
0.67–0.99 across the full 16-cell sub-grid) — the delivering thread's own words apply
verbatim: "the low-mode route is genuinely dead [here] and you can say so with a
mechanism." `dcc_low`'s consistently large positive ρ (+0.44 to +0.63 across both
targets/all `k`) shows it, not `prs_low`, that survives as the classic proximity-
confound direction on real data (comparable in sign and rough magnitude to a
confounded observable's own synthetic ρ≈+0.71) — matching, not contradicting, the
synthetic control's own finding that `dcc_low` is "markedly worse than `prs_low`."

**CARDIAC_MYOSIN: a real, stratification-surviving signal — but not the clean
proximity-orthogonal story the synthetic control predicted.** Both observables clear
the proximity floor (0.568) on whole-graph AUC and reach `p≤0.006` at k=20
(`prs_low`) and `p<0.001` (`dcc_low`) against the permutation null — a well-powered
per-shell check confirmed directly, not just the summary number: the 2 shells that
meet the well-powered filter (n_pos≥3) both score high for both observables (shell 3:
`prs_low` 0.922/`dcc_low` 0.786; shell 4: `prs_low` 0.849/`dcc_low` 0.962) — 2
independent shells, not a single-shell artifact — and the 2 under-powered shells
(n_pos 1–2, not read as a claim on their own) are consistent, not contradictory
(AUC 0.90–0.98 in both). **Real caveat, not smoothed over: ρ(score, −hop) stays
substantial here
(−0.40 `prs_low`, +0.48 `dcc_low`)** — nowhere near the synthetic control's own
~0.08–0.16 "cleanly decorrelated" result — so the whole-graph AUC number alone is not
trustworthy proof of a non-proximity signal on this target; `prs_low`'s own negative
ρ means it is systematically *biased toward distal residues*, and CARDIAC_MYOSIN's
true pocket happens to sit distally, so whole-graph AUC could in principle be
re-discovering that bias rather than the pocket itself. **This is exactly why the
stratified, permutation-null-gated result is the one being reported as the finding,
not the whole-graph number**: within a fixed hop-shell (residues equidistant from the
seed by construction), `prs_low`/`dcc_low` still separate pocket from non-pocket at
AUC 0.85–0.98, which a pure distance-direction bias cannot produce on its own.

**`k_modes` sensitivity: no sign or verdict flips across `{5, 10, 15, 20}` on any
target.** CARDIAC_MYOSIN's significance holds at every `k` (`prs_low` p=0.003–0.006;
`dcc_low` p<0.001–0.007); KRAS_G12C/BCR_ABL1 stay non-significant at every `k`
(p=0.67–0.99 throughout). Full per-`k` table: `results_task0149_lowmode_predictor/
lowmode_predictor_real_run.json`.

**Multiple-comparisons honesty, both scopes reported, neither cherry-picked:**
against the primary 6-comparison family (one `k` per observable per target, `k=20`,
α=0.05/6≈0.0083), both CARDIAC_MYOSIN cells above survive (p=0.006, p<0.001). Against
the maximally conservative 24-comparison family (the full `k`-sweep grid treated as
independent, α=0.05/24≈0.0021), only 2 of the 8 CARDIAC_MYOSIN cells survive
(`dcc_low` at k=15/p=0.001 and k=20/p<0.001); `prs_low`'s own best case (p=0.003 at
k=10) does not clear that stricter bar. Reported as a range, not resolved to whichever
reading is more favorable.

**Cross-reference, not conflation, per this task's own Priority note**:
[[TASK-0122]]'s `mode_coparticipation`/`CP_low` (a mode-*participation-product*
construction, mathematically distinct from `prs_low`'s truncated ANM pseudo-inverse
response and `dcc_low`'s truncated GNM covariance) "mostly failed to decorrelate from
distance on real `H_new`" per that task's own finding. This task's own real-data ρ
values show the same qualitative split hinted at by the synthetic comparison —
`prs_low` decorrelates (and over-corrects, into anti-proximity) far more than
`CP_low` did, `dcc_low` does not decorrelate at all — but this is a genuinely
different method being independently checked, not a re-run of TASK-0122's own result.

**No bug found in the delivered `lowmode_predictor.py` itself** — `prs_low`'s O(N·k)
Python double loop timed at ≤1.7s even on CARDIAC_MYOSIN (N=704, 18 seed residues),
not intractable, so the Out Of Scope note against rewriting it for performance was
never triggered.

Full detail: `.ai/tasks/DONE/TASK-0149-lowmode-prs-dcc-predictor.md`,
`results_task0149_lowmode_predictor/lowmode_predictor_real_run.json`.

---

## Persistent-H2 void detection, real-target run (TASK-0142 H2 half, HYP-P12, 2026-07-24)

**Ungated 2026-07-22 by the Architect/Planner** (see the task file's own "Gating
correction" section): a capped H2 void requires its lining residues to be graph-
*adjacent*, the opposite premise from the open-cleft graph-*far* signature
[[TASK-0143]] tested (0/7) — that FAIL does not bear on this observable, demonstrated
directly by the delivered `test_void_detected_even_when_lining_is_graph_adjacent`.
Ported the delivered `persistent_voids.py`/`test_persistent_voids.py`/`persistent_voids_
synthetic_control.py` (`.ai/reviews/2026-07-22/`) into `src/allostery/`, `tests/`,
`scripts/` unmodified. Re-verified independently before trusting: all 4 delivered tests
pass; the synthetic-control script reproduces its own cited numbers exactly (hollow
shell ∞, solid ball 1.105, cryptic cavity 4.337 / void_score AUC 0.576 / lining mean
graph-hop 1.44 / proximity floor 0.824). `ripser` added to `pyproject.toml`.

Two filing-text imprecisions resolved by direct test, not assumption: **`thresh`
(Rips filtration cap) is not "the same 8 Å cutoff as every other observable"** — tested
on real KRAS_G12C coordinates, `thresh=8.0` truncates real H2 classes mid-birth; the
diagram stabilizes at `thresh≥12.0`, matching the delivered code's own 16.0 default,
used here. **"Matched-spread random-patch null ([[TASK-0133]] precedent)"** — TASK-0133's
own delivered implementation is a *plain* random-patch null, not spread-matched (that's
a different, separately-documented-as-infeasible-on-4/7-targets convention,
[[TASK-0143]]'s own); took the literal citation as authoritative, reused the plain
pattern.

**Real run, all 3 mandatory targets, `thresh=16.0`, noise floor 2.5 (this module's own
`test_solid_ball_has_no_strong_void` threshold):**

| Target | top H2 persistence | void detected | AUC (gated) | AUC (ungated, diagnostic) | max floor AUC | patch-null percentile | patch-null p |
|---|---|---|---|---|---|---|---|
| KRAS_G12C | 0.669 | No | 0.500 (chance) | 0.581 | 0.546 | 77.1 | 0.229 |
| BCR_ABL1 | 2.404 | No | 0.500 (chance) | 0.702 | 0.619 | 46.3 | 0.537 |
| CARDIAC_MYOSIN | 2.829 | **Yes** | **0.192** | 0.192 | 0.583 | **0.0** | 1.000 |

**Verdict: FAIL, clean and in one case sharply informative, per this task's own
pre-registered framing** ("the pocket is not a topological feature these operators see
at Cα resolution"). 2/3 targets show no void at all — top H2 persistence sits at/below
the synthetic noise floor, so the gated (honest) score is all-zeros/chance by this
module's own design; the nominal ungated AUC's apparent floor-beating on both is
explained away cleanly by the matched random-patch null (77.1st/46.3rd percentile,
p=0.229/0.537 — statistically indistinguishable from a random patch). CARDIAC_MYOSIN is
the one target with a detected void — and it is the **wrong void**: AUC 0.192
(anti-ranks the real pocket), null percentile **0.0** (the real pocket's mean score
sits below every one of 1000 random patches). A large protein (N=704) has multiple
internal cavities; the most-persistent one found is not the ligand pocket. Residue-
localization weak link confirmed on real data, not just synthetic: the proximity floor
(0.583) beats `void_score` (0.192) on CARDIAC_MYOSIN, the same pattern the synthetic
control already showed (0.824 vs 0.576) — `ripser`'s lack of H2 cycle representatives
forces a crude geometric centroid-search heuristic that is not reliable for real-target
localization.

**L1 half not run — its own gate remains closed.** [[TASK-0140]] (chiral circulation)
landed FAIL against its own pre-registered bar the session immediately prior;
[[TASK-0143]] was already FAIL. Neither leg of "run only if TASK-0143 or TASK-0140 shows
life" is open, so the L1 half (a cycle/loop-flow quantity, the same family TASK-0143
bears on) is not attempted.

Full detail: `.ai/tasks/DONE/TASK-0142-hodge-l1-persistent-h2.md`,
`results_task0142_topology/persistent_voids_real_run.json`.

---

## Quantum transport / effective-conductance observable (TASK-0145, 2026-07-24)

Reframes the scoring question from "where does an excitation seeded at the active
site spread to over time" (every observable this project has tried) to "what is
the steady-state current/transmission from the active site to each candidate
residue" — a non-equilibrium steady-state (NESS) transport calculation
(Landauer-Buttiker; Nitzan & Ratner), not a seeded-walk-and-wait one. Two
quantities, new `allostery.transport`:

1. **Classical effective resistance/conductance** `R_eff(i,j) = L+_ii + L+_jj -
   2*L+_ij`, `L+` the Moore-Penrose pseudo-inverse of a genuine combinatorial
   graph Laplacian (`hamiltonians.H2_combinatorial_laplacian`) — `H_new` does
   **not** qualify (confirmed directly: its diagonal potential terms, and its
   use of the *normalised* Laplacian variant, both break the null-space
   handling this formula relies on). Multi-index `source` via a
   virtual-supernode construction, reusing `percolation.py`'s (TASK-0136) own
   already-debugged "virtual super-source" pattern.
2. **Landauer-Buttiker quantum transmission** `T(E) = Tr[Gamma_L G(E) Gamma_R
   G(E)^dagger]`, wide-band-limit leads (`Gamma_L`/`Gamma_R` diagonal, nonzero
   only at source/candidate contact sites — the minimal standard model, not an
   invented one), `E=0` (DC/zero-bias) the primary pre-registered energy.
   **A real algorithmic contribution**: since `Gamma_R` at each candidate is
   always a single-site perturbation of the same source-only baseline, a
   Sherman-Morrison closed form gives every candidate's `T(E)` from **one**
   `N x N` matrix inversion (`O(N^2)` total) instead of `N` separate
   re-inversions (`O(N^4)`) — derived and verified against a brute-force
   reference (matched to `1e-10`) before trusting it.

**Synthetic falsification gate** (`tests/test_dumbbell_negative_control.py`,
reusing the established `build_dumbbell_network` construction): both
observables give a clean, decisive double dissociation against GSR on the
conflict cells — `R_eff` 1.000/0.000, `T(E)` 1.000/0.000 (C2/C3, every seed) —
genuinely follow coupling, not the well. `R_eff` is *provably* well-invariant
(a mathematical consequence of the formula, confirmed directly: C1 and C2,
which differ only in which lobe has the well, score *exactly* identically).
Real, characterized finding: the "no signal" null cell (C4) has much higher
per-seed variance for both new observables (0.076-0.924 over 20 seeds) than
this file's propagator-based gates show at only 5 — exact resistor-network/
Green's-function calculations are more sensitive to the construction's own
small random per-seed weight differences than a propagator is.

**Real-target scoring, all 3 mandatory targets**
(`scripts/transport_observable_real_run.py`), against TASK-0094's proximity
floor with block-bootstrap CIs and a permutation null on every cell (`E`/
`gamma_lead` are both fixed a priori, never swept-and-picked against labels,
so no cell here is a "max of something" in the usual sense — the null is
due-diligence scrutiny regardless). `R_eff`/`T(E)` both scored on the shared
plain Laplacian `L` (the direct classical-vs-quantum comparison); `T(E)`
additionally run on `H_new` directly (no null-space requirement) as a
secondary check against this project's actual submission operator:

| Target | R_eff AUC (p) | T(E=0) on L AUC (p) | T(E=0) on H_new AUC (p) | Floor |
|---|---|---|---|---|
| KRAS_G12C | 0.4187 (0.864) | 0.3716 (0.962) | 0.6402 (0.034) | 0.4818 |
| BCR_ABL1 | 0.5980 (0.107) | **0.6985 (0.003)** | 0.6362 (0.036) | 0.5817 |
| CARDIAC_MYOSIN | 0.4448 (0.774) | 0.4560 (0.726) | 0.4680 (0.651) | 0.5679 |

(`p` = permutation-null p-value, 1000 replicates, Bonferroni alpha=0.0167 for
3 targets.) **Headline: one genuinely decisive result** — BCR_ABL1's `T(E=0)`
on the bare topological Laplacian clears Bonferroni correction (p=0.003), the
only cell of 9 that does. The two `H_new`-based transmission cells that clear
the floor at point estimate (KRAS_G12C 0.640, BCR_ABL1 0.636) are
uncorrected-significant only — real but not decisive, the pattern this
project's other point-estimate clearances already share. Every cell's 95% CI
overlaps the floor's own CI regardless of permutation-null significance.
CARDIAC_MYOSIN: no signal from either observable, on either operator.

**Point 3 — classical vs. quantum, answered decisively**: Spearman correlation
between `1/R_eff` and `T(E=0)`, same shared Laplacian, is strongly positive on
all 3 targets (rho=0.74-0.85, all p<1e-45) — confirms the physical connection
`E=0` was chosen for. **Not identical, though**: on BCR_ABL1, `T(E=0)` on `L`
(0.699, Bonferroni-significant) clearly outperforms `R_eff` on the identical
graph (0.598, not significant) despite the strong rank correlation — neither
"pure classical restatement" nor "wholly different physics"; a real, if
modest, quantum-formalism advantage survives on top of a mostly-shared
classical ranking, on the one target where either shows real signal at all.

**`E` sensitivity — a real, large KNOB, characterized not exploited**: a
3-point grid (`E in {0, 0.05, 0.1} * bandwidth`), never used to pick a
best-scoring point against labels. BCR_ABL1: AUC 0.698 (E=0) -> 0.306
(E=0.05*bw) -> 0.464 (E=0.1*bw) — a >2x, non-monotonic swing. `gamma_lead` is a
much weaker KNOB by comparison (BCR_ABL1: 0.680-0.705 across its own grid),
consistent with the intended weak-coupling regime.

Full detail: `.ai/tasks/DONE/TASK-0145-quantum-transport-effective-conductance.md`,
`results_task0145_transport/transport_observable_real_run.json`,
`src/allostery/transport.py`, `tests/test_transport.py`.

---

## Generalization-set check: transport + low-mode PRS/DCC (TASK-0151, TASK-0115 Rule #6, 2026-07-24)

**First real application of [[TASK-0115]]'s Rule #6** (repeated-exposure risk: no
robustness claim is submission-final without a check against the [[TASK-0081]]/
[[TASK-0127]] generalization set). [[TASK-0145]]'s BCR_ABL1 transport positive and
[[TASK-0149]]'s CARDIAC_MYOSIN `dcc_low`/`prs_low` positives — the two strongest
results in the project as of 2026-07-24 — checked against PTP1B and CASPASE7 (the only
2 of the 4 generalization targets with a resolved config; GLUCOKINASE/CASPASE1/
HEMOGLOBIN/GLYCOGEN_PHOSPHORYLASE/PFK confirmed still unresolved). Pure re-application:
new `scripts/generalization_check_transport_lowmode.py` imports and calls
`transport_observable_real_run.run_one`/`lowmode_predictor_real_run.run_target`
directly, unmodified — zero new scoring logic. Each observable kept its own
already-established evaluation lens (transport: whole-graph AUC + block-bootstrap CI +
permutation null; lowmode: TASK-0123's distance-stratified AUC + well-powered-shell
filter + permutation null) — a tested divergence from this task's own filing text,
which described both as using the stratified lens; only lowmode's own script actually
does. Two new Bonferroni families, scoped to this task's own comparisons, not folded
into either mandatory-3 task's own alpha: transport 2 targets × 3 quantities = 6
(α=0.00833); lowmode 2 targets × 2 observables × 4 k_modes = 16 (α=0.00313).

**Headline: mixed and informative, neither a clean replication nor a clean
retraction.**

**Transport does not clearly generalize.** PTP1B's `T(E=0)` on the bare Laplacian —
the exact quantity significant on BCR_ABL1 (AUC 0.699, p=0.003) — comes back **below
chance** (AUC 0.382, p=0.926, the opposite direction). CASPASE7 shows the same
quantity at AUC 0.748, p=0.011 uncorrected — a real, suggestive echo of the BCR_ABL1
direction, but does not clear this task's own stricter 6-comparison Bonferroni bar
(0.00833). No transport cell on either generalization target survives correction.

**`dcc_low` replicates cleanly on PTP1B — now the most robustly-evidenced positive
result in the project.** 3 of 4 k-values (10, 15, 20) clear this task's own stricter
α=0.00313, including a well-powered max AUC of exactly **1.000 at k=10** (p=0.001) —
Bonferroni-significant on two independently-labeled targets (CARDIAC_MYOSIN and now
PTP1B), a form of cross-target evidence no other observable in this program's register
has. `ρ(score,−hop)` stays substantial on PTP1B too (+0.386 to +0.641) — the same
"does not decorrelate from distance as predicted" pattern TASK-0149's own mandatory-3
write-up flagged, now confirmed on a second target rather than resolved. `prs_low`
never reaches significance on either generalization target at any k — its own
CARDIAC_MYOSIN positive (p=0.006) does not generalize. Neither observable shows
anything on CASPASE7 (best p=0.135).

| Result | Mandatory-3 finding | Generalization-set result |
|---|---|---|
| Transport `T(E=0)` on L | BCR_ABL1: AUC 0.699, p=0.003 | PTP1B: AUC 0.382, p=0.926 (opposite direction); CASPASE7: AUC 0.748, p=0.011 (uncorrected only) |
| `dcc_low` (k=20 / best k) | CARDIAC_MYOSIN: well-powered max 0.962, p<0.001 | **PTP1B: well-powered max 1.000 (k=10), p=0.001 — replicates**; CASPASE7: max 0.705, p=0.135 (not significant) |
| `prs_low` (k=20) | CARDIAC_MYOSIN: well-powered max 0.922, p=0.006 | PTP1B: max 0.426, p=0.952; CASPASE7: max 0.415, p=0.717 (neither significant) |

Per this task's own Constraint, neither mandatory-3 finding is retracted by this
result — both stand as reported. This check changes how each should be *framed*:
`dcc_low` graduates to a cross-target-replicated finding; the transport family's
BCR_ABL1-specific result and `prs_low` remain single-target findings, real but not
strengthened by the generalization set.

Full detail: `.ai/tasks/DONE/TASK-0151-generalization-check-transport-lowmode-findings.md`,
`results_task0151_generalization_check/generalization_check.json`.

---

## Holo-diagnostic comparison: transport + low-mode PRS/DCC (TASK-0153, 2026-07-24)

Extends [[TASK-0067]]'s/[[TASK-0092]]'s holo-native diagnostic (same operator, fed
holo topology instead of apo — never a submission prediction, purely failure-
attribution: (a) apo genuinely lacks the information vs (b) the operator itself is
the bottleneck) to [[TASK-0145]]'s transport and [[TASK-0149]]'s low-mode families,
neither of which either prior task ever tested. New `scripts/holo_diagnostic_
transport_lowmode.py` — simpler than TASK-0092's own two-pass design, confirmed
directly (not assumed) that neither observable goes through `run_frozen_verdict`'s
blind-selection machinery at all, so direct application on holo coordinates +
`_holo_native_labels` (TASK-0067's own construction, imported verbatim) + each
observable's own already-established `_score`/`_score_cell` function (reused
unmodified, zero new scoring logic) is the correct, and simpler, design.

**Transport**: BCR_ABL1's headline (`T(E=0)` on L, apo AUC 0.698/p=0.003) gets a clean
**(b) operator-limited** reading — holo=0.626, gap −0.073, holo itself still nominally
elevated (p=0.042) — corroborating TASK-0092's own established BCR_ABL1 pattern
(small apo/holo gap → the propagator/operator is the bottleneck) on a third,
independent operator family now. KRAS_G12C's `T(E=0)` on H_new reproduces TASK-0092's
own "unexpected direction" third outcome — holo scores *below chance* (0.640→0.296,
gap −0.344) — neither (a) nor (b) cleanly.

**Lowmode**: CARDIAC_MYOSIN's `prs_low` headline (apo 0.922/p=0.006) gets the cleanest
**(b) near-information-ceiling** reading in the project so far — holo *stays* strongly
significant at every k (p=0.0000–0.0051), gap only −0.020: apo already extracts
almost all the signal the same operator could ever get from holo's own true
structure. **`dcc_low`'s headline on the identical target (apo 0.962/p<0.001) tells a
starkly different story**: holo loses significance at every k (p=0.07–0.30, gap
−0.303 at k=20) — the opposite of a clean information-ceiling reading, and not
explained by either failure mode. Flagged as a genuine, unresolved complication
(candidate factors — CARDIAC_MYOSIN's own apo/holo residue-count mismatch, 704 vs
709, and its documented history of structural-remapping sensitivity,
[[TASK-0124]]/[[TASK-0144]]/[[TASK-0150]] — noted, not investigated further, per this
task's own scope). BCR_ABL1's `prs_low` reproduces the "unexpected direction" pattern
again (holo markedly worse, 0.439→0.246).

**Net read**: CARDIAC_MYOSIN's `prs_low` positive is now the best-attributed finding
in the project — Bonferroni-significant on its own mandatory-3 target, replicated
directionally under the holo-diagnostic lens with a textbook operator-limited
reading. `dcc_low`'s own strong apo positive on the same target does not get the same
clean attribution and should be framed with that caveat attached. Per this task's own
Constraint, restated: none of these holo numbers were ever submission predictions —
purely diagnostic.

Full detail: `.ai/tasks/DONE/TASK-0153-holo-diagnostic-transport-lowmode.md`,
`results_task0153_holo_diagnostic/holo_diagnostic_transport_lowmode.json`.

---

## Frequency-domain / spectral coherence observable (TASK-0146, 2026-07-24)

**Every propagator this project has scored explicitly time-averages away phase
information** — `time_averaged_ctqw_converged` ([[TASK-0130]]) is *provably*
phase-free at the converged limit. This task deliberately does the opposite:
track the un-averaged, finite-time coherent amplitude `c_j(t) =
<j|exp(-iHt)|source>` and ask whether the *frequency content* of quantum
beating — not its time-average — carries coupling information the converged
limit destroys. New `allostery.spectral_coherence`, 12 synthetic unit tests +
a 5-test dumbbell falsification gate.

**Two real design decisions, stated and justified per this task's own Intent
Contract** (full reasoning in the module's own docstring):
1. **Score target is `p_j(t)=|c_j(t)|^2` (occupation), not the raw amplitude**
   — the task's own physics description ("quantum beating dominated by Bohr
   frequencies `w_k-w_l`") only holds for the *probability*, whose Fourier
   spectrum genuinely contains those cross-term beat frequencies; the raw
   amplitude oscillates at the single frequencies `w_k` only.
2. **Score = total AC (non-DC) spectral power** of `p_j(t)`'s spectrum, not
   peak-counting. The DC bin is exactly `time_averaged_ctqw_converged`'s own
   already-scored quantity — excluding it isolates the genuinely new
   information. By Parseval's theorem this equals `Var_t[p_j(t)]` exactly
   (confirmed as a direct numerical identity in the test suite, not just
   asserted) — an interpretable quantity ("how much does this residue's
   population move") without peak-counting's extra, unjustified threshold
   parameter.

**Time window, calibrated against real data, not picked arbitrarily**: the
task's own suggested approach ("reuse `min_adequate_n_steps`-style
reasoning... resolve the smallest relevant Bohr frequency") is, taken
literally, [[TASK-0110]]'s own already-documented infeasibility (a full
`t_max` 145,000×-3,950,000× the shipped default, driven by pathologically
small near-degenerate gaps). Real gap-distribution check on `H_new` before
choosing anything: median Bohr gap 0.0015–0.0062 across the 3 mandatory
targets, but the single smallest gap is 3-4 orders of magnitude below that.
Fixed `T=5000` instead — chosen so `min_adequate_n_steps(H, t_max=5000)`
stays in the low thousands on every target (checked directly: ~3980 steps on
CARDIAC_MYOSIN, the densest spectrum), same reused Nyquist formula as
everywhere else in this family. **Honestly characterized, not glossed over**:
this resolves (Δf=2π/T≈0.00126) 94.6%/76.0%/55.8% of real Bohr gaps on
KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN respectively — CARDIAC_MYOSIN (largest N,
densest spectrum) is the real limiting case, resolving only the majority, not
the near-totality, of its own gap structure.

**Sensitivity check (this task's own Open Question, answered directly)**: at
the shipped `t_max=15` default (Δf≈0.42, resolves ~0% of real gaps), whole-graph
AUC is a *different, materially worse-behaved* number on 2/3 targets —
KRAS_G12C's own floor-clearing verdict **flips** (0.327, below floor, at
`t_max=15` vs. 0.633, above floor, at `t_max=5000`). `T=5000` vs. a 10×-larger
`T=50000` agree closely on all 3 targets (KRAS_G12C 0.633→0.635, BCR_ABL1
0.576→0.571, CARDIAC_MYOSIN 0.584→0.583) — converged at the chosen default, not
still drifting; `t_max=15` is confirmed inadequate exactly as the module's own
gap-resolution calibration predicted, not merely a cosmetic difference.

**Real-target scoring, `H_new`, full active-site array ([[TASK-0118]]/
`INV-0006`), whole-graph AUC + [[TASK-0112]] block-bootstrap CI, plus
[[TASK-0123]]'s stratified-AUC + well-powered-shell + permutation-null lens
(no max-over-frequency-bins step exists in this score to gate, per the design
above — the permutation null here is due-diligence on the standing statistic,
matching [[TASK-0145]]'s own convention for a non-swept score):**

| Target | Whole-graph AUC | Floor | CI overlap | Well-powered max AUC | p (uncorrected) | ρ(score,−hop) |
|---|---|---|---|---|---|---|
| KRAS_G12C | 0.633 | 0.482 | `True` | 0.792 | 0.103 | **+0.70** |
| BCR_ABL1 | 0.576 | 0.582 | `True` | 0.851 | 0.034 | **+0.72** |
| CARDIAC_MYOSIN | 0.584 | 0.568 | `True` | 0.752 | 0.106 | **+0.68** |

**Verdict: no target reaches a decisive result, and the likely mechanism is
the proximity confound this task's own filing flagged as a real risk (Priority
note: "no structural argument for proximity-orthogonality... just a different
observable built on the same underlying dynamics").** Confirmed directly, not
assumed: ρ(score,−hop) is +0.68 to +0.72 on every target — the same sign and
comparable magnitude to a *confounded* observable's own synthetic reference
(CTQW-occ's ρ≈+0.71 to +1.0, [[TASK-0149]]'s own synthetic table). Unlike
`prs_low`/`dcc_low`/the chiral circulation observable, `spectral_coherence`
was never built with a proximity-orthogonality guarantee — this is exactly
what its lack looks like on real data. KRAS_G12C and CARDIAC_MYOSIN clear the
proximity floor on whole-graph AUC alone, but with overlapping 95% CIs
(not decisive) and a well-powered stratified max that does not clear even the
uncorrected p<0.05 bar (p=0.103/0.106) — the raw "clears floor" reading is
best explained by the confirmed proximity correlation, not genuine distal
coupling. BCR_ABL1 does not clear the floor on whole-graph AUC at all
(0.576<0.582); its own well-powered stratified max (p=0.034) clears
uncorrected significance but not the 3-target Bonferroni bar (α=0.0167).
**A real, honestly-reported negative, matching the Architect/Planner's own
P2 prior** ("lower plausibility than TASK-0145... nothing structural argues
for proximity-orthogonality here").

Full detail: `.ai/tasks/DONE/TASK-0146-frequency-domain-coherence-observable.md`,
`results_task0146_spectral_coherence/spectral_coherence_real_run.json`,
`src/allostery/spectral_coherence.py`, `tests/test_spectral_coherence.py`,
`tests/test_dumbbell_negative_control.py::TestSpectralCoherenceDumbbellGate`.

---

## Single-particle entanglement entropy across a spatial cut (TASK-0148, 2026-07-24)

Computes the Peschel (2003, *J. Phys. A* 36, L205, arXiv:cond-mat/0212631 —
verified real directly, IOPscience/arXiv/ADS) correlation-matrix entanglement
entropy of the active site's coherent single-particle state, bipartitioned per
candidate residue into its own hop-radius-1 neighborhood vs. everything else —
a localization/coupling observable distinct from raw occupation or anything
else in this project's register. New `allostery.entanglement`.

**A real mathematical reduction, derived and verified numerically (to
`1e-16`) before implementing anything else**: for a single coherent source,
the correlation matrix restricted to any region is exactly rank-1, collapsing
Peschel's general diagonalization to the elementary closed form `S_A = h(P_A)`
— the *binary* Shannon entropy of the region's own total occupation
probability. This closed form does **not** apply under this project's own
established multi-residue active-site GAUGE (TASK-0118: an incoherent
mixture, not a coherent superposition) — confirmed directly that a mixture's
correlation matrix is generically rank>1, so real-target scoring uses the
general Peschel diagonalization throughout, not the shortcut.

**A second real finding, resolving the task's own Open Question with a reason
rather than a preference**: entanglement entropy needs the coherent complex
amplitude's off-diagonal phase information — `propagators.ctqw`/
`time_averaged_ctqw` only ever return `|amplitude|^2` by design, so the
converged/time-averaged limit this project defaults to for most headline
scores is not *available* here at all, not merely undesirable. Used a fixed
coherent snapshot, `t* = 1/gap` (this project's own established gap-derived-
timescale convention), blind to labels.

**Synthetic falsification gate**
(`tests/test_dumbbell_negative_control.py::TestEntanglementEntropyDumbbellGate`):
a clean, decisive double dissociation against GSR on the conflict cells
(C2=1.000, C3=0.000, every seed) — genuinely follows coupling, not the well,
the same pattern `R_eff`/`T(E)` (TASK-0145) and CP (TASK-0122) already showed
on this construction. C1 not asserted directionally (same resonance-
sensitivity precedent as this file's other coupling-tracking gates); C4 has
the same real, high per-seed variance TASK-0145's gates already characterized.

**Real-target scoring, all 3 mandatory targets** (radius=1, `t=t*`), against
TASK-0094's proximity floor with block-bootstrap CIs and a permutation null
on the primary (pre-registered, not best-of-K) score:

| Target | Entropy AUC | Floor | Category | Permutation p |
|---|---|---|---|---|
| KRAS_G12C | 0.4787 | 0.4818 | NO_SIGNAL_IN_APO | 0.629 |
| BCR_ABL1 | 0.5291 | 0.5817 | NO_SIGNAL_IN_APO | 0.349 |
| CARDIAC_MYOSIN | 0.4810 | 0.5679 | NO_SIGNAL_IN_APO | 0.624 |

**A clean, complete negative — reported as such, not softened.** No target
clears the floor; no p-value is anywhere near significant even uncorrected.
Radius (1 vs 2) and `t` (0.5x/1x/2x `t*`) characterized as KNOBs on a small
grid, never used to pick a best-scoring point against labels: `t` shows a
real, moderate trend on 2/3 targets (KRAS_G12C: AUC 0.421->0.479->0.545
across the grid) but never crosses into floor-clearing territory; radius has
only a small effect (<0.03 AUC swing).

**Cross-read against TASK-0106's own global localization finding**: this
task's own coherent-snapshot occupation (the same state the entropy scores
come from) has a participation ratio 1.2-2.3x *higher* (more localized) than
the project's own standard converged-limit occupation on all 3 targets —
consistent with, not contradicting, TASK-0106's established Anderson-
localization finding for `H_new`'s CTQW: a coherent snapshot retains more of
that localization than the fully dephased/time-averaged limit does. This does
not, on its own, explain why the per-candidate entropy observable itself
finds no discriminative signal — localization and discrimination are
different questions, and this task's own real result answers the second
directly (no), not by inference from the first.

Full detail: `.ai/tasks/DONE/TASK-0148-single-particle-entanglement-entropy.md`,
`results_task0148_entanglement/entanglement_entropy_real_run.json`,
`src/allostery/entanglement.py`, `tests/test_entanglement.py`.

---

## Compact-vs-scattered permutation null correction (TASK-0158, `PANEL_REVIEW_2026-07-25.md` §2.3, 2026-07-25)

**The pre-registered falsification statement fires.** Every permutation null in
this project's register drew a uniformly *scattered* same-size subset
(`rng.choice(N, size, replace=False)`), but real pockets are spatially *compact*.
For a smooth spatial score field (true of every propagator-based observable in
this register), a compact label's scores are spatially autocorrelated and
produce a systematically more extreme rank statistic than a scattered label of
the same size — making every p-value computed against a scattered null
anti-conservative. Confirmed directly (re-running the external audit's own
scripts, `scripts/null_audit.py`/`null_audit2.py`, before trusting the cited
numbers): **4.8x inflation at α=0.05, rising to 42x at α=0.001**, with a
spatially-uncorrelated white-noise control showing ~0x inflation — isolating the
mechanism as spatial autocorrelation, not a test-construction artifact.

New `src/allostery/nulls.py`: `compact_patch` (ported verbatim from the audit's
own reference — nearest-Euclidean-neighbours of a random seed residue),
`compact_patch_from_pool` (pool-restricted drop-in replacement for the prior
`rng.choice(pool, ...)` convention), `compact_patch_matched`
(radius-of-gyration-matched rejection sampling, TASK-0143's own established
convention applied to this problem). Validated: a **compact-vs-compact**
comparison (the actual fix) restores near-nominal calibration on the identical
score field that showed the inflation — 1.36x at α=0.05, ~0x at α≤0.0083.

**Every named dependent task re-run under the corrected null, side by side, not
overwriting the original (scattered-null) numbers** (`scripts/
compact_null_rerun.py`, reusing each family's own already-established scoring
machinery unmodified):

| Family | Task | Verdict change |
|---|---|---|
| Lowmode `dcc_low`/`prs_low` | [[TASK-0149]], [[TASK-0151]] | **Falsification statement's own condition met** — see below |
| Persistent H2 `void_score` | [[TASK-0142]] | No change (already non-significant; weakens further) |
| Learnability patch control | [[TASK-0133]], [[TASK-0139]], [[TASK-0152]] | No change (already non-significant; weakens further) |

**The decisive cell — `dcc_low` on CARDIAC_MYOSIN and PTP1B, the review's own
named pre-registered test (§5.3: "If a spatially-matched compact null removes
`dcc_low`'s significance on both CARDIAC_MYOSIN and PTP1B, we report the program
as a complete negative result"):**

| Target | Best k | scattered p (originally reported, Bonferroni-surviving) | compact p (corrected) |
|---|---|---|---|
| CARDIAC_MYOSIN | k=20 | 0.000 | **0.060** (fails even uncorrected α=0.05) |
| PTP1B | k=10 | 0.001 | **0.019** (clears uncorrected α=0.05, fails its own 16-comparison Bonferroni bar, α=0.00313) |

**Read against the standard both findings were originally reported under
(Bonferroni-surviving), the falsification statement's condition is met on both
targets.** `prs_low` shows the identical pattern. This is a real correction to
this project's single strongest cross-target-replicated finding
([[TASK-0151]]'s own headline), not a retraction of the underlying computation —
the scores themselves are unchanged; the null they were judged against was
wrong.

**Transport ([[TASK-0145]]) evaluated, not re-run (Out of Scope for this task):
found MORE exposed, not exempt.** Direct empirical check on the identical
whole-graph-AUC construction transport actually uses (no stratification) found
**7.0x inflation at α=0.05, rising to 242x at α=0.001** — worse than the
stratified construction, since stratification incidentally provides some
protection (controlling for hop-distance shell) that a plain whole-graph AUC
lacks entirely. TASK-0145's own BCR_ABL1 finding (`T(E=0)` on L, p=0.003) is
flagged as exposed to this defect and NOT yet re-run under a corrected null —
a live, real, and urgent open item for a follow-up task.

Full detail: `.ai/tasks/DONE/TASK-0158-compact-null-fix-and-rerun.md`,
`results_task0158_compact_null/compact_null_rerun.json`,
`src/allostery/nulls.py`, `tests/test_nulls.py`.

---

## Re-pointing the shipped pipeline at the converged closed-form propagator (TASK-0159, `PANEL_REVIEW_2026-07-25.md` W2, 2026-07-26)

**The shipped end-to-end pipeline (`scripts/run_challenge.py`) — the artifact a
judge would actually generate — still scored the headline AUC via the
finite-time `time_averaged_ctqw(t_max=15.0, n_steps=500)`, not
[[TASK-0130]]'s exact, phase-free, infinite-time closed form
(`time_averaged_ctqw_converged`), despite [[TASK-0110]]'s own finding that
this truncation is orders of magnitude short of the AAKV convergence
criterion, and [[TASK-0146]]'s finding that it flips a real target's own
floor-clearing verdict.** Fixed at the two call sites that determine the
headline reported AUC/hit-list: `run_frozen_verdict(..., use_converged_
limit=True)` (already-existing TASK-0130 machinery, never previously wired
up here — `benchmark`/`quantum_vs_classical`'s own `ctqw` side now uses the
closed form) and the winner's own occupation
(`time_averaged_ctqw_converged(winner_H, source=source, coherent=False)`,
replacing the direct finite-time call that fed `hit_list.json`). The old
`T_MAX`/`N_STEPS` module constants are deleted (Intent Contract's own
explicit requirement) — a renamed, explicitly-scoped-down pair
(`SELECTION_GSR_ABLATION_T`/`_N_STEPS`) remains for the 3 genuinely
different, still-finite-by-design uses this fix does not touch:
`select_frozen_config`'s own blind candidate-ranking heuristic ([[TASK-0118]]'s
own established, deliberately untouched scope boundary — selection is not
the reported score), `ground_state_relaxation`'s single-snapshot relaxation
time (an unrelated convergence criterion), and `ablation()`'s own per-term
diagnostic (`most_impactful_term` — a mechanism finding, not a scored AUC;
`ablation()` has no `use_converged_limit` knob at all and extending it is a
real, separate follow-up, not done here, since it never feeds any AUC or
floor-clearing verdict). `consensus_ranking` (TASK-0080's c-Myc/no-ground-
truth branch) keeps its own finite-time convention unchanged for the same
reason — no AUC/verdict-flip risk exists on a target with no ground truth
to flip against. `test_run_challenge.py`'s existing 12 tests all pass
unmodified (synthetic/mocked, no exact-AUC assertions to update).

**Real quantitative scale of the problem, checked directly on `H_new` for
all 5 targets touched by this task (not merely cited from TASK-0110's own
3-target range)** — the AAKV-adequate `t_max*` (`propagators.
min_adequate_t_max`, `tol=1e-2`) vs. the shipped `t_max=15`:

| Target | N | AAKV `t_max*` | Ratio vs. shipped `t_max=15` |
|---|---|---|---|
| KRAS_G12C | 169 | 1,257,509 | 83,834× |
| BCR_ABL1 | 451 | 1,789,844 | 119,323× |
| CARDIAC_MYOSIN | 704 | 6,310,235 | 420,682× |
| PTP1B | 298 | 1,562,207 | 104,147× |
| CASPASE7 | 461 | 6,128,480 | 408,565× |

Every target checked is 4-5 orders of magnitude short at the shipped
default — confirming and extending TASK-0110's own original 3-target
finding, not just repeating it.

**Direct numerical validation of the closed form itself, beyond its own
algebraic derivation** — per explicit user request, a genuine brute-force
`time_averaged_ctqw` integration was run all the way to each target's own
real AAKV-adequate `t_max*` above (877K-4.6M explicit time steps, up to
12.3 wall-hours for CARDIAC_MYOSIN; new `scripts/task0159_finite_time_
convergence_check.py`, `runlog.RunLogger`-instrumented per
`LONG_JOB_CONVENTION.md`) and compared directly against `time_averaged_
ctqw_converged`'s output on the identical `H`:

| Target | Finite-run AUC | Converged AUC | Max |occupation diff| | Wall time |
|---|---|---|---|---|
| KRAS_G12C | 0.5901 | 0.5901 | 1.9e-6 | 0.28h |
| BCR_ABL1 | 0.5266 | 0.5266 | 3.7e-6 | 2.93h |
| CARDIAC_MYOSIN | 0.5176 | 0.5176 | 3.7e-7 | 12.33h |
| PTP1B | 0.4859 | 0.4859 | 6.6e-7 | 0.17h |
| CASPASE7 | 0.5938 | 0.5938 | 7.0e-7 | 1.16h |

Every target agrees to within 1e-6 to 1e-7 (floating-point noise, not an
approximation gap) — the closed form is confirmed exact on real protein
data, not merely trusted from its own derivation. **First attempt at this
validation lost all progress**: 5 targets launched as harness-tracked
background jobs, all 5 killed simultaneously when the controlling session
process exited (~15-18 min in, 0/5 complete) — a live demonstration of
`LONG_JOB_CONVENTION.md`'s own explicit warning that this detachment
mechanism does not survive session teardown. Re-launched OS-detached
(`nohup`/`disown`) and, having also observed severe 5-26x slowdown from
uncoordinated 5-way parallelism on the first attempt (worst on the two
largest targets), run strictly sequentially on the second attempt instead.

**Cross-check against `RESULTS.md`'s own already-reported numbers, per
this task's own Planned Validation — a real, informative disagreement
found and explained, not silently reconciled.** KRAS_G12C/BCR_ABL1/
CARDIAC_MYOSIN's converged AUCs (0.5901/0.5266/0.5176) match [[TASK-0113]]'s
own already-published TASK-0130 cross-validation numbers exactly. **PTP1B's
converged AUC (0.4859) does NOT match the "ASD generalization set" table's
own PTP1B row (AUC 0.2050, `BEATS_CHANCE_NOT_FLOOR`, [[TASK-0081]]/
[[TASK-0127]], 2026-07-18)** — confirmed directly (not assumed) to be a
finite-time-vs-converged discrepancy, not an error: re-running PTP1B's own
`H_new`/`ctqw` at the literal old `t_max=15, n_steps=500` convention
reproduces 0.2050 exactly. That table predates or is same-day as
[[TASK-0130]] and never claims to use the converged form — **PTP1B's
verdict flips from `BEATS_CHANCE_NOT_FLOOR` (anti-correlated, AUC well
below chance) to `NO_SIGNAL_IN_APO` (AUC ~0.49, at chance)** once scored
under the corrected convention, the same class of verdict-sensitivity
[[TASK-0146]] already found for KRAS_G12C. This is reported as a real
finding requiring a follow-up correction to the ASD generalization set's
own PTP1B row, not silently absorbed.

Full detail: `.ai/tasks/DONE/TASK-0159-run-challenge-converged-propagator.md`,
`RESULTS/results_task0159_finite_time_convergence/*.json`,
`scripts/task0159_finite_time_convergence_check.py`.

---

## Program-level multiple-comparison budget (TASK-0161, 2026-07-25)

`PANEL_REVIEW_2026-07-25.md` §2.2/W4's own framing: every task in this project applies
Bonferroni *within its own family* (its own target × operator × k-sweep grid), but
nobody had accounted for the multiplicity of the *entire program* — roughly ~200+
scored cells against ~7 answer keys predicts, at α=0.05, on the order of 10 spurious
"significant" cells by testing volume alone. This section is the enumeration the
review's own framing asked the project to compute and publish itself, not leave for a
referee to discover.

**Method**: walked every `.ai/tasks/DONE/*.md` task file that reports a p-value,
permutation-null percentile, Bonferroni comparison, or AUC-vs-floor result against a
real target's labels; tabulated target × observable × parameter-grid-point count per
task, verified against each task's own Done section (not assumed from the review's own
one-line estimate, per this task's own Constraint). Synthetic-only results (dumbbell
gates, negative controls) are excluded — this budget counts only comparisons against
real target labels, the actual multiplicity a referee would compute.

| Family (owning task) | Cells | Composition |
|---|---|---|
| Operator sweep ([[TASK-0101]], re-run [[TASK-0129]]/[[TASK-0130]]) | 96 | 16 operators × 2 propagators × 3 mandatory targets |
| Lowmode grid, mandatory set ([[TASK-0149]]) | 24 | 3 targets × 2 observables (`dcc_low`/`prs_low`) × 4 `k_modes` |
| Generalization-set check ([[TASK-0151]]) | 22 | 2 targets × (2 lowmode obs. × 4 `k_modes` = 16, + 3 transport quantities × 2 targets = 6) |
| Transport ([[TASK-0145]]) | 9 | 3 targets × 3 quantities (`R_eff`, `T(E=0)` on `L`, `T(E=0)` on `H_new`) |
| Chiral circulation ([[TASK-0140]]) | 7 | 7 targets × 1 quantity |
| Graph-openness/closure premise ([[TASK-0143]]) | 7 | 7 targets × 1 quantity |
| ENAQT γ-sweep ([[TASK-0141]]) | 24 | 3 targets × 8 γ values |
| Persistent H2 ([[TASK-0142]]) | 3 | 3 mandatory targets |
| Spectral (frequency-domain) coherence ([[TASK-0146]]) | 3 | 3 mandatory targets |
| Single-particle entanglement entropy ([[TASK-0148]]) | 3 | 3 mandatory targets |
| GNM transfer entropy ([[TASK-0132]]) | 3 | 3 mandatory targets |
| Mode co-participation ([[TASK-0122]]) | 3 | 3 mandatory targets (headline `k`; exploratory `k`-sweep not separately permutation-tested) |
| Percolation / `connectivity_robustness` ([[TASK-0136]]) | 3 | 3 mandatory targets |
| Distance-stratified permutation subset ([[TASK-0123]]) | 9 | 9 representative cells drawn from the 96-cell register, re-tested under a stricter shell-matched null (not double-counted against the 96 above — a different null on a subset, not new raw AUC cells) |
| Ceiling permutation null ([[TASK-0131]]) | 3 | 3 mandatory targets |
| H14 ceiling permutation null ([[TASK-0138]]) | 3 | 3 mandatory targets |
| Learnability patch-control ([[TASK-0133]]/[[TASK-0139]]/[[TASK-0152]]) | 4 | KRAS_G12C, BCR_ABL1, CARDIAC_MYOSIN, GLUCOKINASE |
| **Total** | **226** | |

**Grand total: 226 scored cells — confirms, and modestly exceeds, the review's own
"~200+" estimate** (checked directly against the actual task files, not simply
accepted). **Expected false positives at α=0.05: 0.05 × 226 ≈ 11.3** — closely matching
the review's own "~10" estimate.

**Observed positives, using [[TASK-0158]]'s corrected-null re-run per this task's own
Dependency (not the pre-correction numbers, since TASK-0158 landed first): zero.** The
project's one Bonferroni-surviving result as originally reported (`dcc_low` on
CARDIAC_MYOSIN and PTP1B) had its significance removed on **both** targets under
TASK-0158's corrected compact-patch null — the pre-registered falsification statement
fired. Every other family above was either never significant in the first place, or
weakened further under the corrected null (H2, learnability patch-control). **One cell
remains genuinely unresolved, not a confirmed survivor**: [[TASK-0145]]'s BCR_ABL1
transport result (`T(E=0)` on `L`, p=0.003, clears its own 6-comparison Bonferroni bar
at α=0.00833 as originally reported) uses the same scattered-null construction
TASK-0158 found is *even more* anti-conservative for transport's own whole-graph AUC
construction (7.0×/242× inflation vs. `dcc_low`'s 4.8×/42×) — TASK-0158 explicitly did
not re-run it (Out of Scope for that task), flagging it as a live, urgent open item.
Read plainly: this cell has not been shown to survive a fair null, and the one family
tested so far under a comparably-biased null (`dcc_low`) did not survive — it should be
treated as unconfirmed, not counted as a clean positive, until its own compact-null
re-run lands.

**Headline, stated plainly for a referee**: a naive α=0.05 multiplicity budget over 226
real-target comparisons predicts ~11 spurious "significant" findings. The project
currently has **zero** confirmed, corrected-null-surviving positives, and one
flagged-uncertain result pending its own null correction — fewer than pure chance alone
would produce, not merely "not clearly in excess of it" as the review's own
pre-correction framing worried. This is a stronger, not weaker, position than the
review anticipated, and is reported as such — an honest zero is the actual finding, not
a partial one dressed up to look complete.

**Not attempted, per this task's own Out of Scope**: re-running any analysis (pure
enumeration over already-reported results); building a new program-wide correction
scheme (a much larger methodological decision left to the write-up phase). A small
number of earlier, later-superseded analyses (e.g. [[TASK-0113]]'s cutoff sweep,
[[TASK-0093]]'s KRAS AUC reconciliation) were excluded from the count above as their
own cells are already represented in the operator-sweep/generalization-set totals under
the corrected gauge — included would double-count, not add real comparisons.

Full detail: `.ai/tasks/DONE/TASK-0161-program-level-multiplicity-budget.md`.

---

## A genuine dense quantum connectivity matrix (TASK-0160, `PANEL_REVIEW_2026-07-25.md` W3, 2026-07-27)

**The challenge (§5) requires "an N×N matrix where entry (i,j) represents the
calculated *quantum* connectivity strength between residue i and residue
j." `run_challenge.py`'s pre-existing `connectivity_matrix.npz`
(`edge_propensity_to_matrix(edge_propensity(H_new, active_idx))`) failed
this on three independent counts**: it is a *classical* current-flow
linear solve (Kirchhoff/resistor-network math, not a quantum evolution),
*seeded* at the active site (one row/column populated, not all-pairs), and
non-zero only on *contact-graph edges* (not dense). New
`propagators.quantum_connectivity_matrix`:

    P_inf(i, j) = sum_k |v_k(i)|^2 |v_k(j)|^2

computed as a single `(N,N) @ (N,N)` matrix product (`V2 @ V2.T`, `V2 =
v**2`) from the same eigendecomposition `time_averaged_ctqw_converged`
already needs — no second diagonalization, per this task's own Constraint.
Fixes all three failure counts at once, from machinery that already
existed: genuinely quantum (an eigenprojector sum over a unitary
generator's own eigenbasis), all-pairs (every residue is its own implicit
"seed" simultaneously), and dense (every off-diagonal entry populated,
confirmed — not assumed — on real data below).

**Two mathematical properties, both derived and then confirmed
numerically, not just asserted**: (1) **exact symmetry**
(`P_inf(i,j)==P_inf(j,i)`, a direct consequence of the sum-of-outer-products
form, checked bit-exact in tests, not with a tolerance); (2) **every row
sums to exactly 1** (`sum_j P_inf(i,j) = sum_k v_k(i)^2 * sum_j v_k(j)^2 =
sum_k v_k(i)^2 * 1 = 1`, since both `V`'s columns *and* its rows are
unit-normalised for an orthogonal matrix) — meaning `P_inf(i, .)` is a
genuine probability distribution over `j`, not an arbitrary similarity
score, and is in fact identical to `time_averaged_ctqw_converged(H,
source=i)`'s own single-source output, generalized to every `i` at once.
**Diagonal**: `P_inf(i,i) = sum_k |v_k(i)|^4`, the inverse-participation-
ratio-like self-term (large = spectral weight concentrated on few modes /
localized; small = spread across many / delocalized).

**Real, stated design choice**: this is the *plain* per-eigenvector sum,
not [[TASK-0130]]'s own degenerate-eigenvalue-block-corrected form
(`_group_degenerate_eigenvalues`/`_block_projected_diagonal`) — the two
differ in principle for a source landing exactly on a degenerate
eigenspace. Checked directly, not assumed: real `H_new` spectra are
near-degenerate but never exactly degenerate (TASK-0130's own established
finding), and every mandatory target's own `P_inf` column matches
`time_averaged_ctqw_converged`'s independently-computed single-source
output to **1e-16 to 1e-17** (machine precision) — the plain formula this
task's own Intent Contract specifies is confirmed exact in practice on
real data, not merely "probably fine."

**Real-run confirmation, all 3 mandatory targets, dense vs. sparse
measured directly** (fraction of non-zero entries):

| Target | N | `P_inf` density | `connectivity_matrix.npz` density | Row-sum range | Exact symmetric |
|---|---|---|---|---|---|
| KRAS_G12C | 169 | **1.000** | 0.057 | [1.000000, 1.000000] | Yes |
| BCR_ABL1 | 451 | **1.000** | 0.021 | [1.000000, 1.000000] | Yes |
| CARDIAC_MYOSIN | 704 | **1.000** | 0.014 | [1.000000, 1.000000] | Yes |

A stark, decisive confirmation of the "not dense" failure count specifically
— the classical matrix's own density falls with N (more residues, same
contact-graph sparsity pattern), while `P_inf` is fully dense on every
target regardless of size, by construction.

**Wired additively** (per this task's own Constraint): both `run_target`
(the AUC-scored branch, `winner_H`'s own eigendecomposition reused for
both `winner_occ` and `P_inf`) and `run_target_no_ground_truth` (TASK-0080's
c-Myc branch, `H_new`'s own eigendecomposition) now also write
`quantum_connectivity_matrix.npz` (key `matrix`, same `resnums` sidecar
convention as the pre-existing file) alongside the unchanged, still-present
`connectivity_matrix.npz` — a downstream consumer cannot mistake one for
the other by filename, and the old classical output remains available as
an independently-useful baseline, not removed or renamed.

**Scope note**: this task's own TODO cites a "`SOFTWARE.md`/`RESULTS.md`
note" — checked directly, `SOFTWARE.md` (repo root) documents only the
live FastAPI web app (Phase ① backend/frontend), an entirely separate
system from this `__WORK_IN_PROGRESS__` research scaffold's own
`run_challenge.py`; no reference to `connectivity_matrix.npz` or any
research-scaffold deliverable exists there to update. This section is the
actual documentation this task's own intent calls for.

Full detail: `.ai/tasks/DONE/TASK-0160-genuine-quantum-connectivity-matrix.md`,
`src/allostery/propagators.py::quantum_connectivity_matrix`,
`tests/test_propagators.py::TestQuantumConnectivityMatrix`.

---

## Spatial-block bootstrap CI (TASK-0165, `PANEL_REVIEW_2026-07-25.md` W6/V4, 2026-07-27)

**Built and validated as intended; the real-data direction is mixed, not the
uniform widening the review's own text predicted — reported honestly rather
than reconciled.** `metrics.block_bootstrap_ci` blocks bootstrap resamples on
residue *sequence index* runs ("preserve local spatial correlation"), but real
pockets are spatially compact while frequently *scattered* in sequence index
(beta-sheet pairing, domain interfaces, loop closure) — the same root
mechanism [[TASK-0158]] found for the permutation null, applied here to the
confidence-interval construction instead.

New `metrics.spatial_block_bootstrap_ci(coords, scores, labels, ...)` —
`block_bootstrap_ci`'s own drop-in companion (identical signature plus a
required `coords` array). Block construction: each residue's own block is its
`block_size` nearest Euclidean neighbours (inclusive of itself) — the direct
3D analogue of the sequence version's own window-start positions (Kunsch 1989
moving-block bootstrap). A grid-partition alternative was considered and
rejected (hard cell-boundary artefacts; no natural `block_size` mapping).

**Regression property confirmed**: on a synthetic 1D-line control (coordinates
matching sequence order exactly), the two methods' own resampled index sets
coincide and their CIs match within Monte Carlo noise. **Synthetic
sanity check**: an initial globule fixture showed an inconsistent direction
(3/5 seeds wider) until a real confound was found and removed — a random-walk
build order keeps partial accidental sequence/3D correlation a real protein
fold mostly doesn't preserve; explicitly decorrelating sequence index from 3D
position (matching a real fold) gives a clean, robust 1.4x–2.4x widening
across every seed tried, confirming the mechanism targets the right thing.

**Real transport data (the program's currently near-surviving positives, per
[[TASK-0158]]'s own flag): the effect does NOT uniformly widen.**

| Cell | Sequence-block width | Spatial-block width | Ratio |
|---|---|---|---|
| BCR_ABL1 `effective_resistance` | 0.318 | 0.279 | 0.88 |
| BCR_ABL1 `transmission_on_L_E0` | 0.225 | 0.220 | 0.98 |
| BCR_ABL1 `transmission_on_H_new_E0` | 0.338 | 0.287 | 0.85 |
| KRAS_G12C `transmission_on_H_new_E0` | 0.371 | 0.469 | 1.27 |
| PTP1B `transmission_on_H_new_E0` | 0.359 | 0.296 | 0.83 |

4/5 cells got *narrower* under spatial blocking. Plausible mechanism (not
investigated further): real secondary structure keeps genuine local sequence
stretches spatially coherent too, so sequence-blocking was already capturing
real dependence structure for much of a real protein — unlike the idealized
synthetic control, which was built specifically to have none. **Practical
bottom line unaffected**: `grep -rl '"ci_overlap": false' results_task*/*.json`
confirms no cell anywhere in this project has ever had a non-overlapping CI,
and every spatial-block score CI re-checked here still overlaps its own
floor's CI — no verdict flips either direction.

Full detail: `.ai/tasks/DONE/TASK-0165-spatial-block-bootstrap.md`,
`results_task0165_spatial_ci/spatial_ci_rerun.json`,
`src/allostery/metrics.py::spatial_block_bootstrap_ci`, `tests/test_metrics.py`.

---

## Index of open questions from this run

| # | Question | Status | Task |
|---|---|---|---|
| 1 | Does BCR_ABL1's `ground_state_relaxation` score (0.731) survive TASK-0094's proximity floor, and does clearing it mean anything? | **resolved 2026-07-14: clears the floor (+0.166), is largely seed-independent (TASK-0102), and a controlled negative-control experiment shows the mechanism is well-depth, not active-site coupling (TASK-0103/TASK-0104, `REVIEW-2026-07-13b`)** — the number is real; the causal claim is now "apo-computable structural prior for cryptic pockets," not allosteric signal. See BCR_ABL1 section above for the full picture. **Caveat added 2026-07-22 ([[TASK-0113]]): floor-clearing is seed-robust (TASK-0102) but not cutoff-robust — clears at the shipped 8.0 Å (and 7.5 Å) but does NOT clear at 10.0 Å (both AUC and floor move with cutoff, ordering flips). See open-questions row 23.** | [[TASK-0091]], [[TASK-0102]], [[TASK-0103]], [[TASK-0104]], [[TASK-0113]] |
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
| 12 | Is the labeled pocket even present in the apo topology (HYP-P8), measured directly rather than inferred from other findings? | **resolved 2026-07-17, extended 2026-07-18 once [[TASK-0128]] unblocked cumulative overlap for all 3 targets — all classify `LEARNABLE`, not the clean "KRAS is cryptic" story the panel expected.** KRAS_G12C: pocket RMSD 2.27x background, but cumulative overlap 0.638 — well above the 0.5 low-overlap bar — meaning the apo→holo direction IS substantially spanned by soft ANM modes, contradicting the panel's own Sec.4 prediction. BCR_ABL1: pocket moves *less* than background (ratio 0.49) and CO=0.794, consistent with its prior "apo-computable structural prior" framing (TASK-0104), not a cryptic opening. CARDIAC_MYOSIN: ratio 1.32, CO=0.584 — also `LEARNABLE`, though confounded by its own 5TBY data-quality issue and should not be read as cleanly as the other two. **Superseded for KRAS_G12C, 2026-07-20 ([[TASK-0139]], via [[TASK-0133]]'s pocket-restricted CO): KRAS_G12C is `AMBIGUOUS`, not `LEARNABLE`** — see row 17 and `RESULTS.md`'s own learnability-gate section for the full resolution. BCR_ABL1/CARDIAC_MYOSIN's `LEARNABLE` verdicts stand unchanged.** **Further superseded for CARDIAC_MYOSIN, 2026-07-24 ([[TASK-0150]]): now `UNLEARNABLE_FROM_APO`, not `LEARNABLE`**, once the retired-apo replacement ([[TASK-0124]]) and a real whole-structure-vs-restricted-CO bug in `learnability_gate.py` (never actually fixed for this script despite [[TASK-0139]]'s own claim otherwise) are both corrected — see the learnability-gate section's own 2026-07-24 block. | [[TASK-0139]], [[TASK-0150]], [[TASK-0120]], [[TASK-0128]] |
| 13 | Was `most_impactful_term = V_R` (reported in every prior ablation run) a real physics finding, or an artifact of `V_R`'s ~30x-larger normalization scale vs. `V_C`/`V_M`? | **resolved 2026-07-18: artifact.** All five terms are now individually z-scored (std 1 each); `V_R`'s variance share drops from 88.8% to a structural 15.4%, and `lam_C`/`lam_M` go from unreachable (0.1% share each) to 3.8% each. Real-target ablation (KRAS_G12C, BCR_ABL1) now gives `most_impactful_term = V_B` on both, with `V_R` among the *least* impactful on KRAS_G12C. Does not by itself fix the separate proximity confound in the CTQW observable (§2.3) — measurably weakens it (ρ_euclid 0.71-0.83 → 0.22-0.47) but does not eliminate it. | [[TASK-0121]] |
| 14 | Does the cross-target pattern (beats chance, not floor; raw AUC overstates signal) hold on targets no review cycle has ever seen, run under the fully gauge-fixed pipeline — the direct mitigation for ~15 cycles of repeated exposure to the same 3 answer keys? | **resolved 2026-07-18: yes, 4/4.** PTP1B, CASPASE7, CASPASE1 (new), GLUCOKINASE (new) all land in `BEATS_CHANCE_NOT_FLOOR` with overlapping score/floor 95% CIs — none statistically decisive, same pattern as the mandatory set. PTP1B remains anti-correlated with its true (genuinely distal) pocket (AUC 0.205). `most_impactful_term` is never `V_R` on any of the 4 — independent cross-check of [[TASK-0121]] on data its own validation never touched. Ceiling intentionally deferred for all 4 (known-stale `ceiling.py::_PARAM_RANGES`, [[TASK-0116]]'s scope, not a shortcut taken here). | [[TASK-0081]], [[TASK-0127]] |
| 15 | Does KRAS_G12C's ceiling search (TASK-0046, 60 blind-random trials, `lam_*` sampled on a range ~25x [[TASK-0121]]'s own budget) actually support "very little headroom," or was the search exploring the wrong (physically invalid) space? | **resolved 2026-07-18: the "no headroom" conclusion is confirmed, not overturned, but the original 0.5250 number was itself somewhat inflated by the invalid range.** Corrected-range random search: 0.4735-0.4864 depending on seed convention (both below the original). Corrected-range + TPE strategy: 0.4908 (reproduced exactly at seed=7), marginally above the re-measured floor (0.4818, +0.009) — too small a margin to claim a real positive without [[TASK-0131]]'s permutation null, flagged not claimed. Cross-validates [[TASK-0110]]'s independent 0.4750 (different parameter axis, same near-chance conclusion). | [[TASK-0046]], [[TASK-0116]] |
| 16 | Is this project's headline output actually reproducible given identical seeded inputs, or has environmental nondeterminism been silently corrupting "before vs. after" comparisons ([[INV-0008]], the BCR_ABL1 gap discrepancy)? | **resolved 2026-07-19: reproducible — the hypothesis is refuted, not confirmed.** 3 independent repeats each of a spectral-gap eigendecomposition, a blind random search, and a TPE search all gave bit-for-bit identical results. BLAS thread-count variation (`1/2/4/8`) produces real but negligible drift (~1e-14 relative). The original 0.0374-vs-0.1933 discrepancy this hypothesis was raised from is directly ruled out as environmental (11 orders of magnitude too small) — traces instead to a stale cached object from 5 days before a later code change, not live nondeterminism. New `allostery.runlog` module (environment fingerprint + incremental wall/CPU-time JSONL logging) adopted in `scripts/reproducibility_audit.py`. | [[TASK-0135]], [[INV-0008]] |
| 17 | Does cumulative overlap onto the apo ANM's lowest 20 modes actually discriminate "spans *this pocket's* displacement" from "spans *any* same-sized displacement" — or does a random patch score just as high ([[TASK-0120]]'s CO half of the learnability conjunction, `REVIEW-panel-2026-07-17.md` §5.2)? | **resolved 2026-07-19, with a real complication found mid-task.** TASK-0120's own reported `CO(20)` turns out to be a *whole-structure* quantity (166-709 residues), not pocket-specific — confirmed directly, not assumed. A properly pocket-restricted CO (new `superpose.restricted_cumulative_overlap`; also fixed a real bug found along the way — naively slicing+renormalizing eigenvectors for a small subset breaks `CO(m)<=1`, up to 1.64 observed) compared against 1000 random same-sized patches/target: **only matters for KRAS_G12C** (the one target whose verdict actually depends on the CO half). KRAS_G12C's restricted CO=0.458 is *below* the 0.5 threshold (vs. 0.638 whole-structure) and would flip the verdict to `UNLEARNABLE_FROM_APO` — but sits at only the 93rd percentile of the random-patch null (p≈0.07, not decisive at this project's own significance bar). BCR_ABL1/CARDIAC_MYOSIN score *below* their random-patch medians (37th/13th percentile) but their verdicts are RMSD-determined regardless. **[[TASK-0139]], 2026-07-20: decided, not left standing — pocket-restricted CO is the correct quantity (RMSD half is already region-specific; a whole-structure CO answers a different question), and `co_threshold=0.5` is replaced by a direct significance test against this exact null once available (new `learnability_verdict(co_percentile=...)`). KRAS_G12C resolves to `AMBIGUOUS` (RMSD clears, CO evidence inconclusive at α=0.05) — not `LEARNABLE`, not `UNLEARNABLE_FROM_APO`. BCR_ABL1/CARDIAC_MYOSIN unchanged (RMSD-determined).** **[[TASK-0150]], 2026-07-24: this row's own premise that `scripts/learnability_gate.py` "already computes the restricted quantity" (TASK-0139's own claim, in its Done section's part (1)) was checked directly against the actual code/`git log` and found false** — that script still called the whole-structure `cumulative_overlap` until this task fixed it (TASK-0139's own later "Not attempted" section already said as much, an internal contradiction in that task's own write-up). Now fixed; CARDIAC_MYOSIN (re-run under [[TASK-0124]]'s corrected apo) flips `LEARNABLE`→`UNLEARNABLE_FROM_APO` as a direct consequence — see the learnability-gate section's own 2026-07-24 block for the full table. | [[TASK-0139]], [[TASK-0133]], [[TASK-0120]], [[TASK-0150]] |
| 18 | Does a published, classical (no MD, no quantum) GNM transfer-entropy method beat or match `H_new`/CTQW on this project's own 3 mandatory targets — "if you can't beat it, you don't have a result" (`REVIEW-panel-2026-07-17.md` §4 P1-6)? | **resolved 2026-07-19: no, on both counts, a mixed result reported as such.** New `transfer_entropy.py` (linear-Gaussian TE / Granger-causality closed form over GNM lagged covariance, verified against 2 real cited papers — one citation's author list was wrong in the filing task, corrected). Scored against all 3 real targets: AUC 0.4485/0.3497/0.5335 vs. floor 0.4818/0.5817/0.7921 — fails to clear the floor anywhere (0/3), and scores *lower* than `H_new`/CTQW's own current numbers (0.5901/0.5266/0.7272) on all 3, decisively so on 2. Neither "classical method already does the job" nor "the task itself is uniformly hard regardless of method" holds cleanly — `H_new` beats this specific classical baseline, which itself doesn't clear the floor. | [[TASK-0132]] |
| 19 | Does *any* engineered Haken-Strobl dephasing rate gamma improve pocket **discrimination** (not transport efficiency) over the coherent walk, on real targets — HYP-P11, the collaborator's Idea #1 run with the correct scored quantity? | **resolved 2026-07-20: no, on all 3 targets tested (KRAS_G12C, BCR_ABL1, PTP1B), confirming the pre-registered NEGATIVE prediction.** No gamma clears the proximity floor with non-overlapping CIs anywhere; the best-of-8-gamma point's own permutation null is nowhere near significant (p=0.649/0.211/1.000, Bonferroni alpha=0.0167). Closed 2 real gaps in `propagators.haken_strobl` along the way (no incoherent-mixture source option; no time-averaged variant — both now added, `coherent`/`haken_strobl_time_averaged`). The task's own mandatory classical-limit sanity gate did *not* pass as literally specified at `t_max=25` (`rho(occ,-dist)` fell, not rose, with gamma) — root-caused to Zeno-regime suppression of the effective diffusion timescale at large gamma under a fixed `t_max`, confirmed genuine (not an integrator bug) by extending `t` alone at fixed gamma and recovering the expected rising trend. | [[TASK-0141]] |
| 20 | Is the pocket-label ligand-contact cutoff (4.5 Å, `holo_pocket_mask`, defines ground truth itself) knob-unstable the same way TASK-0075 proved the cumulative-overlap gate's own 4.5 Å-shaped threshold is (0.067–0.860 swings, 15/18 verdict flips)? | **resolved 2026-07-20: no, materially more stable — but not fully insensitive either.** Swept {4.0,4.5,5.0,5.5} Å on all 3 mandatory targets, re-scoring the same once-computed `H_new` occupation against each cutoff's regenerated label. `floor_cleared` never flips for any target across the whole grid. `classify_failure`'s finer diagnosis *does* flip for 2/3 targets at the grid's edges (KRAS_G12C `NO_FAILURE_DETECTED`->`NO_SIGNAL_IN_APO` at 5.5 Å; BCR_ABL1 `BEATS_CHANCE_NOT_FLOOR`->`NO_SIGNAL_IN_APO` between 4.0/4.5 Å) — real but narrow, nothing like TASK-0075's own instability. TASK-0047's pinned 4.5 Å KRAS_G12C fixture (21/21) confirmed exactly correct, but sits on a still-moving slope (the raw recovered residue set changes at every 0.5 Å step tested, both directions), not a stable plateau. CARDIAC_MYOSIN run against TASK-0124's new 8QYP structure (landed the same day) — flagged as not comparable to this document's other, 5TBY-era CARDIAC_MYOSIN numbers. | [[TASK-0114]], [[TASK-0075]], [[TASK-0047]] |

| 21 | Does CARDIAC_MYOSIN's only surviving positive result rest on a defensible apo structure, or does resolving its 20 Å docked-homology-model caveat (5TBY) change the result itself (`REVIEW-panel-2026-07-16-v2.md` §1.2/§3, "do not build the only positive on a 20 Å docked homology model")? | **resolved 2026-07-20: resolving the structure removes the result.** Apo replaced 5TBY -> 8QYP (real 2.759 Å X-ray, same paper/deposition series and species as the existing 8QYR holo, RCSB-verified directly — resolves [[TASK-0128]]'s floppy-mode workaround for this target as a side effect, n_zero=10->6). Full re-run under the current closed-form convention: N drops 950->704, floor drops 0.7921->0.5679, actual AUC drops from 0.7912 ([[TASK-0129]]'s already-diminished number) to **0.5176**, `NO_SIGNAL_IN_APO` — matching BCR_ABL1's own diagnosis. The relayed 2026-07-20 lead proposing PDB 9GZ1 as a holo replacement was independently verified as real (*Science Advances* 2026-04-29) but not adopted — 8QYR remains the cleaner (higher-resolution, single-domain) structure; 9GZ1 stands as corroboration, not substitution. **No mandatory target now has a decisive positive result under the fully corrected pipeline.** Full detail: `COMPETENCE_MAP.md`'s own CARDIAC_MYOSIN section. | [[TASK-0124]], [[TASK-0129]], [[TASK-0128]] |
| 22 | Do real holo-defined cryptic-pocket residues actually carry the "near-in-3D / far-on-apo-graph" coordinated-closure signature (HYP-P10) the entire loop/multi-site-closure observable family (HYP-P9, HYP-P12) depends on? | **resolved 2026-07-22: no — 0/7 targets pass the pre-registered gate.** KRAS_G12C (98.4th percentile, p=0.016 uncorrected/0.112 Bonferroni) and CASPASE1 (90.2nd percentile) are INSUFFICIENT; CASPASE7 is a clean FAIL (26.8th percentile, the opposite direction from the claim). BCR_ABL1/CARDIAC_MYOSIN/PTP1B/GLUCOKINASE could not be tested at all — the matched-spread null is infeasible via unbiased rejection sampling at the pre-registered ±35% tolerance even at 20M attempts, since a compact real pocket's spread is intrinsically rare among uniform random same-size draws over a large protein (a real finding in its own right, not fixed here — would require redesigning the null's sampling scheme). Two real bugs found+fixed: a non-reproducible seed (Python's per-process-salted `hash()`, fixed to `zlib.crc32`) and output written only once at the end (fixed to checkpoint per-target). Gates [[TASK-0140]]/[[TASK-0142]] as unsupported, not blocked outright. | [[TASK-0143]] |
| 23 | Does TASK-0067's "cutoff doesn't matter (7.5/8.0/10.0 Å)" conclusion, measured on a bare GNM Kirchhoff, transfer to `H_new` — the operator that produces every headline AUC in this document (`REVIEW-2026-07-15-execution-plan-gap-audit.md` finding #2)? | **resolved 2026-07-22: agrees in aggregate, disagrees on a real, headline-relevant per-target case.** `H_new`'s own aggregate (2-target mean) cutoff sensitivity is if anything smaller than the bare Laplacian's (ctqw range 0.003, ground_state range 0.020, vs. TASK-0067's 0.0124) — but this is a coincidence of KRAS_G12C/BCR_ABL1 moving in opposite directions (~0.04-0.05 each), not real insensitivity. **BCR_ABL1's `ground_state_relaxation` floor-clearing status (its own "apo-computable structural prior" finding, row 1 above) flips**: clears at 7.5/8.0 Å, does not clear at 10.0 Å (both AUC and floor move, ordering flips). `time_averaged_ctqw`'s own floor-crossing story stays fully stable across the grid for both targets. No weight-scheme axis exists for `H_new` (`normalised_laplacian_alpha` hardcodes `weight="exponential"`) — a real structural difference from TASK-0067's own 2-axis grid, reported rather than forced. | [[TASK-0113]], [[TASK-0067]], [[TASK-0091]] |

| 24 | Does `select.py`'s reported quantities (`focusing`, `source_specificity`, `ballistic_exponent`, `unsupervised_score`) actually satisfy the GAUGE/KNOB/SIGNAL classification `INV-0004` seeded for them, or was that just reasoned from each function's signature and never verified ([[TASK-0064]])? | **resolved 2026-07-20: mostly GAUGE-VERIFIED/KNOB-CHARACTERIZED as expected, plus one real, previously-unexamined finding.** `source_specificity` is NOT relabeling-invariant with its default sub-sampled `n_alt` (root-caused to label-position-dependent `rng.choice`, confirmed exact once sampling is exhaustive) — reclassified GAUGE→KNOB rather than force-passed, flagged in the function's own docstring, not fixed algorithmically (would change what "random sample" means). `unsupervised_score`'s ranking also confirmed to flip between scalar/multi-index `source` conventions (closes that KNOB row, matches [[TASK-0118]]'s project-wide finding). `ballistic_exponent`'s `t_values` window is this module's dominant KNOB by an order of magnitude. SIGNAL null-controlled against a 30-graph random-graph batch, not a single instance. Full detail: `RESULTS.md`'s own `select.py` invariance section above, `.ai/invariants/INV-0004-select-unsupervised-score.md`. | [[TASK-0089]] |
| 25 | Is allosteric communication between the active site and known pocket carried by a narrow, fragile bottleneck or a broad, redundant subnetwork, measured directly on the apo contact graph — a purely topological question, no propagator involved (raised directly by the orchestrating user, 2026-07-18)? | **resolved 2026-07-22: broad and redundant, decisively, on all 3 mandatory targets.** New `allostery.percolation` (shortest-path ensemble, Menger's-theorem edge connectivity + literal min-cut, percolation-threshold sweep). Edge connectivity is 68-76 (an order of magnitude above a narrow-bottleneck signature) on every target, with min-cuts spanning dozens of distinct residue pairs, not a single chokepoint. Real bug found+fixed first: an initial unit-capacity virtual-edge construction silently capped every result at `min(|active|,|pocket|)` (13-18, empty cuts) — confirmed wrong via a synthetic single-hub-3-fan-out check, fixed via large-capacity virtual edges + `nx.maximum_flow_value`/`minimum_cut` (`edge_connectivity`/`minimum_edge_cut` don't accept a `capacity` argument at all). As a blind scoreable baseline (`connectivity_robustness`, part c), beats the proximity floor on only 1/3 targets, and `stratified_auc` (actually run, not cited by analogy) shows most of its raw AUC is the same distance/degree confound found pervasive elsewhere in this project's register. Dumbbell gate: exactly chance in every cell — a clean, understood negative (unweighted route-counting can't see the dumbbell's edge-weight-only confound). | [[TASK-0136]] |
| 26 | Does `superpose.align_apo_holo`'s raw `(chain, resnum)` correspondence silently break for targets ([[TASK-0127]]'s `apo_chains`/`holo_chains` override) where apo and holo deposit the same biological chain under different author chain letters — found live while executing [[TASK-0124]]'s CARDIAC_MYOSIN apo replacement? | **resolved 2026-07-22: yes, confirmed on 2 real targets, now fixed.** New optional `chain_map` parameter on `common_residues_by_resnum`/`align_apo_holo` (default `None`, byte-identical prior behavior), built from target config via new `chain_map_from_config`, threaded through all 5 real call sites found by re-grepping the repo (`run_superpose`, `learnability_gate.py`, `learnability_gate_patch_control.py`, `holo_diagnostic_comparison.py`, `kras_auc_reconciliation.py`). Before the fix: CARDIAC_MYOSIN's new 8QYP/8QYR pair (apo chain A, holo chain B) had 0 common residues, `align_apo_holo` raised. After: 698/704 residues resolve (vs. 5TBY-era's 709/950, a coverage jump from 75%->99%), `LEARNABLE` (ratio 1.57, whole-structure CO(20) 0.943). GLUCOKINASE (apo chain A, holo chain X), run through this gate for the first time ever, resolves 446/448 and is the project's first target to classify `UNLEARNABLE_FROM_APO` on both conjunction halves genuinely firing (ratio 1.94, CO(20) 0.443). TASK-0120/0133's own CARDIAC_MYOSIN rows are flagged superseded (by TASK-0124's apo replacement, not retroactively by this bug — 5TBY happened to share holo's chain letter) in this document's own learnability-gate section, not deleted. **This row's own `LEARNABLE`/`CO(20) 0.943` reading for CARDIAC_MYOSIN was itself computed with the whole-structure `cumulative_overlap`, not the pocket-restricted quantity [[TASK-0139]] had already established as correct — [[TASK-0150]], 2026-07-24, fixes this and flips the verdict to `UNLEARNABLE_FROM_APO` (restricted CO=0.254); GLUCOKINASE's verdict is unchanged but its own CO number corrects 0.443→0.304.** | [[TASK-0144]], [[TASK-0124]], [[TASK-0127]], [[TASK-0120]], [[TASK-0133]], [[TASK-0150]] |

| 27 | Does TASK-0110's "a single `time_averaged_ctqw` call did not return after 2+ hours" infeasibility claim hold up under continuous CPU-time evidence, not just a single process-state check at kill time ([[P-0005]])? | **resolved 2026-07-22: corroborated, not inflated.** Re-ran the same call with continuous `RunLogger` instrumentation: 438 samples over one full, uninterrupted 950s run to completion, `cpu_elapsed_s/wall_elapsed_s` held at 4.05 ± 0.035 throughout, no drops — clean evidence of continuous execution. The current AAKV prescription for the same target is ~15x smaller than the original (`H_new`'s spectrum shifted after [[TASK-0121]]'s renormalization); extrapolated to the original scale, the re-verified rate implies ~3.9 CPU-hours, consistent with the original claim. Separate finding: CPU-time exceeding wall-clock by ~16x (uncapped, 16-core) is normal multithreaded BLAS behavior, not contention — ratio *stability* across samples is the real diagnostic. New `.ai/reference/LONG_JOB_CONVENTION.md` generalizes the pattern for future long-running compute, including an explicit HITL hand-off path. | [[TASK-0134]] |

| 28 | Does the chiral (broken-time-reversal) circulation observable (HYP-P9) — Peierls-flux bond current, Hodge-filtered to its circulating part, proximity-orthogonal by construction — clear the proximity floor with non-overlapping CIs on real pockets, per its own pre-registered gate? | **resolved 2026-07-23: no — FAIL on all 7 targets, consistent with [[TASK-0143]]'s own FAIL on the graph-openness premise this observable depends on.** CI overlap is `True` everywhere, so the primary bar is not met anywhere. Real, honestly-reported suggestive-not-confirmed signal: KRAS_G12C and PTP1B both clear the Bonferroni-corrected threshold (0.05/7) on the independent stratified-AUC permutation-null statistic. The proximity-orthogonality claim itself holds cleanly on 7/7 targets (ρ(circ,-dist) smaller in magnitude than ρ(occ,-dist) everywhere) — the observable measures something other than distance, that something just doesn't clear the discrimination bar here. Real physics finding made while building the regression tests (not anticipated in advance): a bare N-cycle ring gives exactly zero converged circulation from a diagonal seed, at any flux — real protein contact graphs aren't at risk (dense 3-D packing gives degree well above 2 everywhere), but it ruled out the obvious minimal synthetic test fixture. GATE 1/GATE 2 both re-verified passing on a fresh reconstruction (the cited reference script is confirmed absent). [[TASK-0142]]'s own hard gate remains unmet. | [[TASK-0140]], [[TASK-0143]] |
| 29 | Do low-mode-restricted PRS/DCC (`prs_low`/`dcc_low`, proximity-orthogonal by construction) find real allosteric signal on real targets, and does mode-filtering actually decorrelate them from distance the way the delivered synthetic control predicted? | **resolved 2026-07-24: real, Bonferroni-surviving signal on CARDIAC_MYOSIN only; KRAS_G12C/BCR_ABL1 genuinely dead — but the decorrelation-from-distance premise itself does not hold as predicted.** CARDIAC_MYOSIN's stratified-AUC well-powered max (0.92/0.96 for `prs_low`/`dcc_low` at k=20) survives its own permutation null (p=0.006/p<0.001) and the primary 6-comparison Bonferroni bar; KRAS_G12C/BCR_ABL1 never reach significance at any `k` (p=0.67–0.99). **But ρ(score,−hop) stays substantial on every real target (`prs_low` −0.18 to −0.51; `dcc_low` +0.44 to +0.63)** — nowhere near the synthetic control's own ~0.08–0.16 "cleanly decorrelated" prediction. `dcc_low` in particular reproduces the classic proximity-confound sign/magnitude on real data (matching, not contradicting, the synthetic control's own "markedly worse than `prs_low`" finding); `prs_low` decorrelates in the opposite (anti-proximity, distal-favoring) direction instead of toward zero — real and target-consistent, not predicted by the synthetic control either. A real sign bug was found and fixed in this task's own new evaluation script (not in the ported `lowmode_predictor.py`) before trusting any ρ value — caught by checking the raw per-shell score trend against the printed sign, not assumed correct because the script ran without error. | [[TASK-0149]], [[TASK-0123]], [[TASK-0122]] |

| 30 | Does persistent H2 (a capped-void signature, graph-*adjacent* not graph-*far*) localize real holo-defined pockets, given the 2026-07-22 Architect/Planner correction that [[TASK-0143]]'s open-cleft FAIL (0/7) does not actually falsify this half of the loop/multi-site-closure family? | **resolved 2026-07-24: no — clean FAIL on all 3 mandatory targets, one sharply informative.** 2/3 targets (KRAS_G12C, BCR_ABL1) show no H2 void at all — top persistence at/below the synthetic solid-ball noise floor (2.5); the honest gated score is all-zeros (chance AUC), and the nominally floor-beating *ungated* diagnostic score is explained away by the matched random-patch null (77.1st/46.3rd percentile, p=0.229/0.537 — indistinguishable from a random patch). CARDIAC_MYOSIN is the one target with a detected void (2.829) — and it is the **wrong void**: AUC 0.192, null percentile **0.0** (real pocket's mean score below all 1000 random patches). A large protein has multiple internal cavities; the most-persistent one found isn't the ligand pocket. Residue-localization weak link (crude geometric centroid heuristic, `ripser` has no H2 cycle representatives) confirmed on real data: proximity floor beats `void_score` on CARDIAC_MYOSIN (0.583 vs 0.192), same pattern as the synthetic control. Two filing-text imprecisions resolved by direct test before assuming: `thresh=16.0` (not "8 Å", truncates real H2 classes), and TASK-0133's *plain* random-patch null (not TASK-0143's spread-matched, infeasible-on-4/7-targets convention) as the actual cited precedent. L1 half not run — its own gate (TASK-0143 or TASK-0140 showing life) remains closed. | [[TASK-0142]], [[TASK-0143]], [[TASK-0140]] |

| 31 | Does reframing the scoring question as steady-state transport/conductance (Landauer-Buttiker `T(E)`, classical effective resistance `R_eff`) rather than seeded-walk-and-wait find real signal, and does the quantum transmission differ meaningfully from the classical `1/R_eff` limit? | **resolved 2026-07-24: one decisive result out of 9 cells, and quantum tracks classical closely but not identically.** BCR_ABL1's `T(E=0)` on the bare topological Laplacian clears Bonferroni correction (p=0.003, AUC 0.699) — the only cell (3 targets x {R_eff, T(E) on L, T(E) on H_new}) that does; KRAS_G12C/BCR_ABL1's `H_new`-based `T(E)` clear the floor at point estimate only (uncorrected-significant), CARDIAC_MYOSIN shows nothing. Classical-vs-quantum: Spearman rho 0.74-0.85 (same shared Laplacian, all targets) — strongly correlated, confirming the `E=0`/DC-limit choice, but not interchangeable in practice (BCR_ABL1's `T(E=0)` decisively beats its own `R_eff` on the identical graph). `E` is a large, real KNOB (BCR_ABL1: AUC 0.698->0.306->0.464 across a 3-point grid) characterized, not exploited. | [[TASK-0145]] |
| 32 | Does the learnability-gate verdict ([[TASK-0059]]'s new `run_frozen_verdict(learnability=...)` wiring) actually reach a real end-to-end run's own `verdict.json`, not just exist as a tested-but-unused capability — and does `scripts/learnability_gate.py`'s own reference computation hold up under direct re-verification? | **resolved 2026-07-24: wired end-to-end, and a real, previously-uncaught bug was found and fixed in the reference script itself.** New `superpose.compute_learnability` (shared by `run_challenge.py` and `scripts/learnability_gate.py`, replacing two independently-duplicated compositions) fixes `learnability_gate.py`'s own whole-structure-vs-restricted `cumulative_overlap` bug — real, confirmed directly (code + `git log`), and a direct contradiction of [[TASK-0139]]'s own Done section, which claimed this script already used the restricted quantity. Real re-run, all 4 previously-run targets: KRAS_G12C ratio 2.27/restricted CO 0.458 (bare-threshold `UNLEARNABLE_FROM_APO`, matching [[TASK-0133]]'s own number exactly); BCR_ABL1 ratio 0.49/CO 0.175 (`LEARNABLE`, unchanged, RMSD-determined); **CARDIAC_MYOSIN ratio 1.57/CO 0.254 — verdict flips `LEARNABLE`→`UNLEARNABLE_FROM_APO`** relative to [[TASK-0144]]'s own re-run (which used the same buggy whole-structure CO); GLUCOKINASE ratio 1.94/CO 0.304 (`UNLEARNABLE_FROM_APO`, verdict unchanged, CO number corrected). CARDIAC_MYOSIN's flip independently corroborates [[TASK-0124]]'s own AUC-side finding that this target's only positive result was an artifact of the retired 5TBY apo. `run_challenge.py`'s own live computation is caught locally on failure (degrades to "omitted," per [[TASK-0059]]'s own established convention), never aborts a target's real scoring. | [[TASK-0150]], [[TASK-0059]], [[TASK-0139]], [[TASK-0144]], [[TASK-0124]] |

| 33 | Do [[TASK-0145]]'s BCR_ABL1 transport positive and [[TASK-0149]]'s CARDIAC_MYOSIN `dcc_low`/`prs_low` positives — the project's two strongest results — survive [[TASK-0115]]'s Rule #6 repeated-exposure check against the PTP1B/CASPASE7 generalization set? | **resolved 2026-07-24: mixed, real, informative.** Transport does not clearly generalize: PTP1B's `T(E=0)` on L comes back below chance (AUC 0.382, p=0.926, opposite direction from BCR_ABL1's own AUC 0.699/p=0.003); CASPASE7 echoes the direction (AUC 0.748) but only at uncorrected p=0.011, not clearing this task's own stricter 6-comparison Bonferroni bar. **`dcc_low` replicates cleanly on PTP1B** — 3/4 k-values clear this task's own stricter 16-comparison bar, including well-powered max AUC 1.000 at k=10 (p=0.001) — now Bonferroni-significant on two independent targets, the strongest cross-target evidence any observable in this project has. `prs_low` never reaches significance on either generalization target. Neither observable shows anything on CASPASE7. Per this task's own Constraint, neither mandatory-3 finding is retracted — this changes framing, not standing: `dcc_low` graduates to a replicated finding, transport's BCR_ABL1 result and `prs_low` remain single-target. | [[TASK-0151]], [[TASK-0145]], [[TASK-0149]], [[TASK-0115]] |

| 34 | Do CARDIAC_MYOSIN(8QYP)'s and GLUCOKINASE's bare-threshold learnability verdicts ([[TASK-0150]], both `UNLEARNABLE_FROM_APO`) survive the same 1000-replicate random-patch null [[TASK-0133]]/[[TASK-0139]] already applied to KRAS_G12C's own bare-threshold verdict? | **resolved 2026-07-24: no — both soften to `AMBIGUOUS`, the same direction and magnitude as KRAS_G12C's own result.** CARDIAC_MYOSIN: restricted CO=0.254 sits at the 85.7th percentile of the null (one-sided p=0.143); GLUCOKINASE: CO=0.304 at the 89.9th percentile (p=0.101) — both elevated relative to a random same-sized patch, neither decisive at this project's own α=0.05 bar, exactly the "elevated but not significant" pattern KRAS_G12C's own 93rd-percentile/p≈0.07 result already established. Now confirmed on 3 of the 4 targets this exact analysis has ever been run on. Does not retract [[TASK-0150]]'s own bare-threshold reading — reports the more rigorous of two legitimate readings alongside it, same relationship KRAS_G12C's own two numbers already have. GLUCOKINASE's chain-schema question ([[TASK-0081]]) reconfirmed resolved ([[TASK-0127]]), not re-litigated. | [[TASK-0152]], [[TASK-0150]], [[TASK-0133]], [[TASK-0139]] |

| 35 | Does the [[TASK-0067]]/[[TASK-0092]] holo-native diagnostic (same operator, holo topology instead of apo — failure-attribution only, never a prediction) extend to [[TASK-0145]]'s transport and [[TASK-0149]]'s low-mode observable families, neither ever tested this way? | **resolved 2026-07-24: mixed and genuinely informative, including a third "unexpected direction" outcome on 2 cells and one striking within-target divergence.** BCR_ABL1's transport headline (`T(E=0)` on L, apo 0.698/p=0.003) gets a clean **(b) operator-limited** reading (holo=0.626, gap −0.073, holo itself still nominally elevated p=0.042) — corroborates TASK-0092's own BCR_ABL1 pattern on a third, independent operator family. CARDIAC_MYOSIN's `prs_low` headline (apo 0.922/p=0.006) gets the cleanest **(b) near-information-ceiling** reading in the project so far — holo stays strongly significant at every k (p=0.0000–0.0051), gap only −0.020. **`dcc_low`'s headline on the identical target (apo 0.962/p<0.001) does not** — holo loses significance at every k (p=0.07–0.30, gap −0.303 at k=20), the opposite of a clean ceiling reading, flagged as an open complication (not resolved — candidate factors noted: CARDIAC_MYOSIN's own 704-vs-709 apo/holo residue-count mismatch and its documented structural-remapping history). KRAS_G12C's transport-on-H_new and BCR_ABL1's `prs_low` both reproduce TASK-0092's own "holo scores *worse* than apo" third outcome, confirming it recurs rather than being a one-off. | [[TASK-0153]], [[TASK-0067]], [[TASK-0092]], [[TASK-0145]], [[TASK-0149]] |
| 36 | Does the frequency content of un-averaged coherent quantum beating (`c_j(t)=<j|exp(-iHt)|source>`, Fourier-analyzed rather than time-averaged away like every other propagator this project scores) carry coupling information the converged limit destroys? | **resolved 2026-07-24: no — a real, honestly-reported negative, and the likely mechanism is the proximity confound this task's own filing flagged as a real risk.** New score (total AC/non-DC spectral power of `p_j(t)=|c_j(t)|^2`, `T=5000` calibrated against real Bohr-gap statistics, not picked arbitrarily) passes its own dumbbell falsification gate cleanly (C2/C3 exact double dissociation against GSR) but on real targets: no target reaches a decisive result (all 3 CIs overlap the floor's own CI; well-powered stratified max never clears even uncorrected p<0.05 on 2/3 targets, and the third — BCR_ABL1, p=0.034 — does not clear the 3-target Bonferroni bar). ρ(score,−hop) is +0.68 to +0.72 on every target, matching a *confounded* observable's own reference magnitude — confirmed directly, not assumed, and unlike `prs_low`/`dcc_low`/chiral circulation, this observable was never built with a structural proximity-orthogonality guarantee. Sensitivity check: the shipped `t_max=15` default is confirmed inadequate (flips KRAS_G12C's own floor-clearing verdict relative to the calibrated `T=5000`, which itself agrees closely with a 10×-larger window). | [[TASK-0146]], [[TASK-0110]], [[TASK-0123]], [[TASK-0149]] |
| 37 | Does single-particle entanglement entropy across a spatial cut (Peschel's correlation-matrix method) find real localization/coupling signal on real targets, and does it reduce to a simpler quantity than the general method suggests? | **resolved 2026-07-24: a clean, complete negative, plus a real mathematical reduction confirmed before touching real data.** For a single coherent source, the entropy exactly reduces to the binary Shannon entropy of the region's total occupation probability (verified to `1e-16`) — but real active sites are multi-residue under this project's own incoherent-mixture GAUGE (TASK-0118), where the correlation matrix is generically rank>1 and the closed form does not apply, so real scoring used the general Peschel diagonalization throughout. No target clears the proximity floor (KRAS_G12C 0.4787/0.4818, BCR_ABL1 0.5291/0.5817, CARDIAC_MYOSIN 0.4810/0.5679); no permutation-null p-value is close to significant even uncorrected. A real, resolved Open Question: the converged/time-averaged occupation limit this project defaults to elsewhere is not available for this observable at all (it needs coherent phase information `|amplitude|^2` discards), so a fixed `t*=1/gap` coherent snapshot was used instead. Cross-read against TASK-0106: the coherent snapshot is 1.2-2.3x more localized (participation ratio) than the converged limit on all 3 targets, consistent with the established Anderson-localization finding, but that localization does not translate into per-candidate discriminative signal. | [[TASK-0148]] |

| 38 | Does replacing the uniformly *scattered* permutation-null draw (`rng.choice`) with a spatially *compact* one — matching real pockets' own geometry — remove this project's strongest positive findings, per `PANEL_REVIEW_2026-07-25.md` §2.3's own pre-registered falsification statement? | **resolved 2026-07-25: yes — the falsification statement fires.** New `allostery.nulls.compact_patch`, validated against the external audit's own reproduced numbers (4.8x inflation at α=0.05, rising to 42x at α=0.001, ~0x on a white-noise control) and confirmed to restore near-nominal calibration (1.36x, ~0x) when both legs of the comparison use the corrected draw. Re-running every named dependent task ([[TASK-0149]], [[TASK-0151]], [[TASK-0142]], [[TASK-0133]], [[TASK-0139]], [[TASK-0152]]) side by side with the original: `dcc_low`'s Bonferroni-significance is removed on **both** CARDIAC_MYOSIN (p: 0.000→0.060, fails even uncorrected α=0.05) and PTP1B (p: 0.001→0.019, fails its own Bonferroni bar) — the review's own named pre-registered condition for reporting the program's strongest observable family as a negative result. H2 and learnability nulls were already non-significant and only weaken further (no verdict change). **[[TASK-0145]]'s transport null, evaluated but explicitly not re-run (Out of Scope), is exposed to the same defect even more severely** (7.0x/242x vs. 4.8x/42x) — flagged as a live, urgent open item for a follow-up task, not silently assumed exempt because its own construction differs. | [[TASK-0158]], [[TASK-0149]], [[TASK-0151]], [[TASK-0142]], [[TASK-0133]], [[TASK-0139]], [[TASK-0152]], [[TASK-0145]], [[TASK-0143]] |
| 39 | Does the shipped end-to-end pipeline (`scripts/run_challenge.py`) actually compute its headline AUC/hit-list via the same converged closed-form propagator ([[TASK-0130]]) the project's own corrected science reports, or still the finite-time approximation [[TASK-0110]] found orders of magnitude short of convergence? | **resolved 2026-07-26: no (before this task), now yes — and the closed form is now directly, numerically confirmed exact on real data, not just algebraically derived.** Wired `run_frozen_verdict(use_converged_limit=True)` (already-existing TASK-0130 machinery, never previously called with it) and swapped the winner's own occupation to `time_averaged_ctqw_converged` directly; old `T_MAX=15`/`N_STEPS=500` module constants deleted, a renamed/scoped-down pair kept only for the 3 genuinely different, still-finite-by-design uses (candidate-selection heuristic, GSR snapshot, `ablation()`'s per-term diagnostic) this task does not touch. Real AAKV `t_max*` checked directly on all 5 targets touched: 83,834x-420,682x the shipped `t_max=15` (extends, not just repeats, TASK-0110's own 3-target range). **Per explicit user request, a genuine brute-force integration was run all the way to each target's own real `t_max*`** (877K-4.6M steps, up to 12.3 wall-hours for CARDIAC_MYOSIN) and compared directly against the closed form: agreement to 1e-6 to 1e-7 on every target — floating-point noise, not an approximation gap. First attempt at this validation lost all progress when a harness-tracked background job was killed by session teardown (0/5 complete, ~15-18min in) — a live confirmation of `LONG_JOB_CONVENTION.md`'s own warning about that detachment mechanism; re-run OS-detached and sequentially (uncoordinated 5-way parallelism on the first attempt caused a real 5-26x slowdown). Cross-check against already-reported numbers: KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN match TASK-0113's own TASK-0130 cross-validation exactly; **PTP1B's converged AUC (0.4859) does not match the ASD generalization set's own PTP1B row (0.2050, `BEATS_CHANCE_NOT_FLOOR`) — confirmed to be a finite-time-vs-converged discrepancy (re-running at the literal old `t_max=15` reproduces 0.2050 exactly), and PTP1B's verdict flips to `NO_SIGNAL_IN_APO`** under the corrected convention, flagged as needing a follow-up correction to that table, not silently absorbed. | [[TASK-0159]], [[TASK-0130]], [[TASK-0110]], [[TASK-0146]], [[TASK-0113]], [[TASK-0081]], [[TASK-0127]] |
| 40 | How many scored cells has this program actually run against real target labels, program-wide — and does the number of reported positives exceed what that testing volume alone would produce at α=0.05, per `PANEL_REVIEW_2026-07-25.md`'s own framing? | **resolved 2026-07-25: 226 real-target scored cells, confirming (and modestly exceeding) the review's own "~200+" estimate — expected false positives at α=0.05 ≈ 11.3.** Using [[TASK-0158]]'s corrected-null re-run (not the pre-correction numbers): **zero** confirmed, corrected-null-surviving positives program-wide. `dcc_low`, the one prior Bonferroni survivor, lost significance on both CARDIAC_MYOSIN and PTP1B under the compact-patch null. One cell remains genuinely unresolved rather than confirmed: [[TASK-0145]]'s BCR_ABL1 transport result uses a scattered null TASK-0158 found is *more* anti-conservative than the one that removed `dcc_low`'s significance, and was not itself re-run — treated as unconfirmed, not counted as a survivor. **The project has fewer positives than pure chance predicts, not merely "not clearly in excess of it."** Full enumeration table: this document's own "Program-level multiple-comparison budget" section above. | [[TASK-0161]], [[TASK-0158]], [[TASK-0149]], [[TASK-0151]], [[TASK-0145]] |
| 41 | Does the shipped `connectivity_matrix.npz` deliverable actually satisfy the challenge's own §5 "N×N quantum connectivity matrix" requirement — quantum-defined, all-pairs, and dense? | **resolved 2026-07-27: no (before this task) — classical, seeded, and sparse, failing on all 3 counts; now yes, additively.** New `propagators.quantum_connectivity_matrix` (`P_inf(i,j)=sum_k \|v_k(i)\|^2\|v_k(j)\|^2`, one `(N,N)@(N,N)` product from the same eigendecomposition `time_averaged_ctqw_converged` already needs — no second diagonalization). Exact symmetry and row-sum-to-1 both derived and confirmed numerically; real-data check on all 3 mandatory targets shows the new matrix at density 1.000 vs. the old matrix's 0.014-0.057 (falling as N grows) — a decisive, measured confirmation of the "not dense" fix specifically. **Design choice checked, not assumed**: the plain per-eigenvector formula (not TASK-0130's own degenerate-block-corrected form) matches `time_averaged_ctqw_converged`'s independently-computed single-source column to 1e-16 to 1e-17 (machine precision) on every mandatory target — real `H_new` spectra are near- not exactly-degenerate, so the simpler formula this task's own Intent Contract specifies is confirmed exact in practice, not merely assumed safe. Wired additively into both `run_target` and `run_target_no_ground_truth` as `quantum_connectivity_matrix.npz`, the pre-existing classical file untouched and still written. | [[TASK-0160]], [[TASK-0130]] |

| 42 | Does replacing `block_bootstrap_ci`'s sequence-index blocking with a spatially compact k-NN block — matching a real pocket's own geometry, `PANEL_REVIEW_2026-07-25.md` W6/V4 — widen CIs for currently-surviving/near-surviving positives, as the review's own text predicts? | **resolved 2026-07-27: the tool is built and validated correctly, but the real-data direction is mixed, not uniform widening — reported honestly.** New `metrics.spatial_block_bootstrap_ci` (k-NN block, drop-in signature). Regression checks pass: exact convergence to sequence-block behavior on a 1D-line synthetic control, and 1.4x–2.4x widening on a globule control once an accidental sequence/3D correlation in the naive fixture (a random-walk build order) was found and removed. **On real transport data (TASK-0145's BCR_ABL1 family plus KRAS_G12C/PTP1B's own `H_new` cells, [[TASK-0158]]'s own flagged near-survivors): 4/5 cells got *narrower*, not wider** (ratios 0.83–0.98; only KRAS_G12C widened, 1.27x) — plausibly because real secondary structure keeps genuine local sequence stretches spatially coherent too, unlike the idealized synthetic control. Practical bottom line unaffected: no cell anywhere in this project has ever had a non-overlapping CI (confirmed by direct grep before this task started), and every re-checked cell still overlaps its floor's CI under the corrected method — no verdict flips either direction. | [[TASK-0165]], [[TASK-0158]], [[TASK-0145]] |

Full process history, run mechanics, and Acceptance-Scenario checklists
for this run live in `.ai/tasks/DONE/TASK-0079.005-run-mandatory-targets.md`
(or `.ai/tasks/TODO/` if not yet closed — check `.ai/COMMON.md`'s registry
for current status). This document is the one to read for the science;
that one is the one to read for what was done and by whom.
