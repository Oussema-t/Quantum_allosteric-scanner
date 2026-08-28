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
> (e.g. `results/tasks/0094/` → `RESULTS/results/tasks/0094/`) — a repo
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
`results/tasks/0112/headline_ci_rerun.json`.

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
`results/tasks/0112/headline_ci_rerun.json`. (BCR_ABL1's CTQW-vs-floor
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
`results/tasks/0106/BCR_ABL1/reproduction.json`.

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
`results/tasks/0105/<target>/sweep.json`.

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

**[[TASK-0217.004]], 2026-08-14 — suspicion, not a confirmed defect:**
across the 3 targets with a published 3-leg breakdown (this table; the
BCR_ABL1 and CARDIAC_MYOSIN breakdowns further down this document),
**`degree_centrality` never wins** — `euclid_from_seed_centroid` wins on
KRAS_G12C, `hop_from_seed` wins on BCR_ABL1 and CARDIAC_MYOSIN. Does not
invalidate the floor's own name (all three candidates are genuinely
proximity-flavoured), and no reported verdict changes — flagged because
an empirically-dominated third candidate is exactly the shape this
task's own audit class looks for, and a register-wide check (not done
here, out of that task's own scope) would settle whether this holds
generally or is a 3-target coincidence.

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
`results/tasks/0068/KRAS_G12C/noise_sweep.json`.

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
`results/tasks/0110/<target>/scan.json`, `src/allostery/optuna_scan.py`.

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
(`scripts/learnability_gate.py`, `results/tasks/0120/learnability_gate.json`).

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
`results/tasks/0120/learnability_gate.json` (includes the full CO(m) curve
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
`results/tasks/0133/learnability_gate_patch_control.json`.

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
`results/tasks/0139_learnability_resolution/resolution.json`,
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
`results/tasks/0120/learnability_gate.json` (regenerated). **Correction, same day**:
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
`RESULTS/results/tasks/0152/learnability_gate_patch_control_task0152.json`,
`results/tasks/0152_learnability_resolution/resolution.json`.

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
"headline" set (`results/tasks/0127/<target>/`).

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
`results/tasks/0116/KRAS_G12C/`.

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
`results/tasks/0135/BCR_ABL1/spectral_gap_audit.jsonl`.

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
`results/tasks/0122_mode_coparticipation/mode_coparticipation_validation.json`,
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
`results/tasks/0132/transfer_entropy_baseline.json`), compared directly
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
`results/tasks/0132/transfer_entropy_baseline.json`,
`src/allostery/transfer_entropy.py`.

---

## External classical-pocket-detection baselines (fpocket, PocketMiner) (TASK-0163, 2026-07-28)

**[EXECUTED, all 3 mandatory targets, real code, real data]** `PANEL_REVIEW_2026-07-25.md`
W7/V8: the challenge explicitly scores "comparison to classical analogs," and this
project had run one external classical comparator ([[TASK-0132]]'s GNM transfer
entropy) against ~40 quantum-flavored observables. `ALGORITHM_REGISTER.md` rates
fpocket, PocketMiner, and ProteinLens at 4/4 and none had ever been run. This task
runs the two that are actually runnable in this environment and reports the third
as an explicit, undisguised blocker per its own Intent Contract.

**Access-method confirmation (done first, per this task's own Constraint):**
- **fpocket**: no web server, no account — a local binary. Not preinstalled, no
  root/`sudo` available in this environment. Built from source (`Discngine/fpocket`
  tag `4.2.3`, plain `make`, no cmake/netcdf needed for the core binary despite the
  project's own Docker recipe listing `libnetcdf-dev`) into
  `__WORK_IN_PROGRESS__/tools/fpocket/bin/` — links only against system
  `libm`/`libstdc++`/`libc`/`libgcc_s` (`ldd` confirmed), so this is a permanent,
  repo-local install, not a scratch/session artifact.
- **PocketMiner**: web server (`pocket-miner-ui.azurewebsites.net`, linked from the
  Bowman Lab's own software page) is DNS-dead — confirmed two independent ways
  (`curl`, `WebFetch`), both a hard resolution failure, not a timeout/rate-limit.
  Local install requires `tensorflow==2.6.2`, which only ships wheels for Python
  ≤3.9 — incompatible with this repo's own Python 3.12 environment. Run instead in
  a **separate, isolated repo** (`/home/bchmura/PROJECTS/PocketMiner/`, not this
  one), via a from-source Python 3.9.18 build (no root needed — system OpenSSL/
  bz2/sqlite3 headers obtained via `apt-get download` + `dpkg-deb -x`, no `sudo`).
  No account/API key needed once installed locally — model weights ship in the
  cloned repo.
- **ProteinLens**: web server confirmed live and reachable, **no login/account
  required** — but browser-only interactive UI with no discovered API or batch
  endpoint. This is a different kind of blocker than PocketMiner's (reachable, not
  gated — just not automatable in this environment). **Not run. Explicit blocker,
  not a silent skip**: reported here per this task's own Intent Contract rather
  than substituted or omitted. Manual-interaction instructions can be produced on
  request if a human is available to drive a browser session per target.

**Scoring methodology — same holo-defined pocket labels, same AUC/floor convention
this project's register already uses for every other observable** (`labels.
build_labels`, `baselines.degree_centrality`/`euclid_from_seed_centroid`/
`hop_from_seed`, `metrics.auc`) — no bespoke evaluation favoring either side, per
this task's own Constraint. `scripts/task0163_external_baseline_scoring.py`.

- **fpocket**: run against a full-atom apo PDB filtered the same way `clean.clean()`
  filters its own Cα-only structures (altloc 'A' only, protein only, same target-
  config chain selection) — fpocket needs side-chain geometry for cavity detection,
  unlike the rest of this project's Cα-only pipeline. Per-pocket "Score" (cavity
  openness, `ALGORITHM_REGISTER.md`'s own characterization — not "Druggability
  Score") assigned to every residue in that pocket's own atom-membership file
  (`pocketN_atm.pdb`); a residue belonging to multiple pockets takes the max;
  unassigned residues score 0. Mapped onto `apo.resnums` by `(chain, resnum)`
  lookup, not array position, since `clean()` can drop/reorder residues relative to
  a raw fetch.
- **PocketMiner**: per-residue predictions loaded from the separate repo's output,
  aligned onto `apo.resnums` the same `(chain, resnum)`-lookup way, parsed from the
  exact PDB fed to PocketMiner (not assumed positional order). A real alignment bug
  was caught and fixed here, not silently worked around: CARDIAC_MYOSIN's apo
  (8QYP) carries two trimethyllysine (`M3L`) residues that are `HETATM` records in
  the PDB format — mdtraj's `protein` selection (used by PocketMiner's own
  featurizer) recognizes them once renamed to canonical `LYS` (done before feeding
  the structure to PocketMiner, see below), giving PocketMiner 706 residues, while
  this project's own `clean()` genuinely excludes `M3L` entirely from `apo.resnums`
  (prody's `protein` selector doesn't recognize the non-standard name), giving 704
  — the resSeq-lookup alignment naturally resolves this once the parser scans
  `HETATM` CA records too (an earlier `ATOM`-only parse undercounted PocketMiner's
  own residue axis by exactly these 2 and tripped a length-mismatch guard); the 2
  extra PocketMiner predictions at those positions are simply never queried, since
  this project's own apo/pocket-label definition has no entry there either — an
  honest, not a favorable, resolution.

**A structure-preparation note, stated per this task's own disclosure
convention**: `M3L` (a real, common myosin post-translational modification) was
renamed to `LYS` in the PDB fed to PocketMiner only — backbone N/CA/C/O atoms are
untouched, and PocketMiner's own featurizer (`validate_performance_on_xtals.
process_strucs`) reads only backbone coordinates + residue-identity one-hot, never
side-chain atoms, so this is chemically inert to its prediction and does not
special-case a result in either tool's favor.

**[[TASK-0206]], 2026-08-06: this table's fpocket column is superseded, not
retracted** — a different machine could not reproduce these numbers
(0.7910/0.8618/0.5303, root-caused to an unpinned per-machine binary build).
Kept on record; see this document's own dated "fpocket binary drift" section
below for the authoritative set and the diagnosis.

| Target | Floor | This project's own actual (`H_new`/CTQW) | fpocket AUC | PocketMiner AUC |
|---|---|---|---|---|
| KRAS_G12C | 0.4818 | 0.5901 | **0.8348** | 0.6932 |
| BCR_ABL1 | 0.5817 | 0.5266 | **0.8596** | 0.5603 |
| CARDIAC_MYOSIN | 0.5679 | 0.5176 | 0.5345 | 0.5732 |

(This project's own "actual" column is a fresh `run_challenge.py` run against the
current, `TASK-0124`-corrected 8QYP-era CARDIAC_MYOSIN apo — not the retired
5TBY/N=950 numbers some earlier sections of this document still cite; KRAS_G12C/
BCR_ABL1/CARDIAC_MYOSIN floor and actual values reproduce [[TASK-0132]]'s and
[[TASK-0124]]'s own already-published numbers exactly, cross-validating this task's
own pipeline reconstruction rather than a freshly-invented one.)

**Headline, reported plainly: fpocket — a purely geometric, non-dynamical classical
tool with no propagator, no eigendecomposition, no active-site seed at all — beats
both this project's own proximity floor and its own best quantum observable
(`H_new`/CTQW) by a wide margin on 2 of 3 mandatory targets** (KRAS_G12C +0.245
over actual, +0.353 over floor; BCR_ABL1 +0.333 over actual, +0.278 over floor).
On CARDIAC_MYOSIN fpocket sits just below its own floor (−0.033) but still above
this project's own actual (+0.017). This is exactly the outcome
`PANEL_REVIEW_2026-07-25.md`'s own framing anticipated as informative either way
("if they hit where this project misses, the operator is the bottleneck") — here
the classical geometric method hits decisively where the quantum-walk observable
does not, on the 2 targets where this project's own pipeline reports
`NO_FAILURE_DETECTED`/marginal outcomes.

PocketMiner (a GNN, not classical-geometric, but the other rated external
comparator) beats this project's own actual on KRAS_G12C (+0.103) and
CARDIAC_MYOSIN (+0.056, narrowly clearing its own floor by +0.0053), but falls
short of both floor and actual on BCR_ABL1 (0.5603 vs. floor 0.5817).

**Not attempted, per this task's own Out of Scope**: reselecting the submission
operator based on this result, and any new observable of this project's own —
pure external-tool benchmarking, same boundary [[TASK-0132]]'s own Done section
already established.

Full detail: `.ai/tasks/DONE/TASK-0163-external-classical-baselines.md`,
`__WORK_IN_PROGRESS__/scripts/task0163_external_baseline_scoring.py`,
`__WORK_IN_PROGRESS__/results/tasks/0163_external_baselines/results.json`,
`/home/bchmura/PROJECTS/PocketMiner/` (separate repo, PocketMiner's own
predictions + `Instructions.md`).

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
`results/tasks/0123_distance_stratified/distance_stratified_evaluation.json`,
`results/tasks/0123_distance_stratified/summary.md`,
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
`results/tasks/0141_dephasing/dephasing_discrimination_sweep.json`,
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
sensitivity.py`, `results/tasks/0114_pocket_cutoff_sensitivity/`).

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
`results/tasks/0114_pocket_cutoff_sensitivity/pocket_label_cutoff_sensitivity.json`,
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
`results/tasks/0143_openness_premise/openness_premise.json`, new
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
(`scripts/h_new_cutoff_sweep.py`, `results/tasks/0113_h_new_cutoff_sweep/`).
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
`results/tasks/0113_h_new_cutoff_sweep/h_new_cutoff_sweep.json`,
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
`results/tasks/0136_percolation/percolation_connectivity.json`, new
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
`results/tasks/0144_learnability_rerun/learnability_gate_rerun.json`,
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
`results/tasks/0134_cpu_time/cpu_time_reverification.jsonl`,
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
`results/tasks/0140_chiral/chiral_circulation_real_run.json`.

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
(p=0.67–0.99 throughout). Full per-`k` table: `results/tasks/0149_lowmode_predictor/
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
`results/tasks/0149_lowmode_predictor/lowmode_predictor_real_run.json`.

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
`results/tasks/0142_topology/persistent_voids_real_run.json`.

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
`results/tasks/0145_transport/transport_observable_real_run.json`,
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
`results/tasks/0151_generalization_check/generalization_check.json`.

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
`results/tasks/0153_holo_diagnostic/holo_diagnostic_transport_lowmode.json`.

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
`results/tasks/0146_spectral_coherence/spectral_coherence_real_run.json`,
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
`results/tasks/0148_entanglement/entanglement_entropy_real_run.json`,
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
`results/tasks/0158_compact_null/compact_null_rerun.json`,
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
`RESULTS/results/tasks/0159_finite_time_convergence/*.json`,
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

### Recount, 2026-08-03 ([[TASK-0191]]) — the 226-cell total above is frozen at 2026-07-25; 10 tasks landed real-target scored cells since

**The table above is preserved verbatim, not edited in place** (this
project's no-silent-overwrite convention) — this addendum applies the exact
same method (walk every `.ai/tasks/DONE/*.md` file closed after 2026-07-25
that reports a p-value, permutation-null percentile, Bonferroni comparison,
or AUC-vs-floor result against a **real** target's labels; exclude
synthetic-only positive-controls/negative-controls, the same exclusion the
frozen table above already applies) and shows the per-task increments so a
second person can reproduce the new total mechanically.

| Family (owning task) | Cells | Composition |
|---|---|---|
| Reverse-direction coupling, apo ([[TASK-0162]]) | 25 | 5 observables × 5 targets |
| External classical baselines ([[TASK-0163]]) | 6 | 2 baselines (fpocket, PocketMiner) × 3 mandatory targets |
| Ensemble/entropic observable ([[TASK-0166]]) | 7 | 7 pocket-scoreable targets × 1 observable |
| Reverse-direction coupling, holo ([[TASK-0171]]) | 50 | (forward + reverse) × 5 observables × 5 targets |
| Consensus-label rescoring ([[TASK-0177]]) | 14 | 7 targets × 2 new label variants (`core`, `consensus`; the pre-existing `incumbent` label is not a new cell) |
| Binding-response coupling specificity ([[TASK-0178]]) | 21 | self-stated by the task's own section ("the ~21-cell family this task itself adds") |
| Selection-as-QUBO gate decision ([[TASK-0181]]) | 3 | self-stated by the task's own section (gate-decision cells only; the un-run full 14-target grid does not enter the budget) |
| Conformational-search specificity gate ([[TASK-0185]]) | 3 | 3 mandatory targets × 1 specificity-vs-decoy comparison each |
| ENM connectivity-graph shortcut hypothesis ([[TASK-0187]]) | 1 | PTP1B × 1 comparison (real-pocket shortcut rate vs. 30 matched decoys) |
| Apo-structure sensitivity sweep ([[TASK-0155]]) | 10 | KRAS_G12C × 10 independently RCSB-verified true-G12C apo structures |
| **Subtotal, new since 2026-07-25** | **140** | |
| **New grand total (226 + 140)** | **366** | |

**The budget moves in the project's favour, stated plainly rather than left
to read as a quiet upward revision**: more scored cells at a fixed α makes
"fewer confirmed positives than chance predicts" a *stronger* claim, not a
weaker one. **Expected false positives at α=0.05: 0.05 × 366 ≈ 18.3**
(was ≈11.3). **Observed, corrected-null-surviving positives program-wide:
still zero** — none of the 10 new task families above report a Bonferroni
survivor (TASK-0162/0171's own cited floor-clear fractions are AUC-vs-floor
counts, not corrected-null-surviving significance claims; TASK-0177/0178's
own sections explicitly report no surviving cell; TASK-0163/0166/0181/0185/
0187/0155 report no positive either). **Zero confirmed positives against an
expected ~18.3 is a stronger position than zero against ~11.3.**

> **CAVEAT ([[TASK-0201]], 2026-08-04): this "zero confirmed positives"
> claim no longer holds without qualification.** [[TASK-0190]] found
> `dcc_low`'s previously-reported matched-null test (CARDIAC_MYOSIN, PTP1B)
> ran against a null that could not structurally reach either target's real
> pocket Rg; [[TASK-0201]] built a null that can and re-ran both cells at
> decisive precision (20,000 replicates). **CARDIAC_MYOSIN still fails
> (p=0.025 vs. bar 0.0083); PTP1B's `dcc_low` (k=10) now survives its own
> pre-registered bar (p=0.0027 vs. 0.003125, CI slightly straddling)** — a
> mixed result under TASK-0190's own pre-registered reading rule, not the
> complete negative this section states. See this document's own "A null
> that can actually reach real pocket Rg" section for the full numbers.
> Not corrected in place here (no-silent-overwrite) — flagged for whoever
> next touches this headline number or [[TASK-0184]]'s narrative.

> **CAVEAT ([[TASK-0199]], 2026-08-04): the "~18.3" expectation itself is
> the wrong denominator — the 28 observable types this budget is built
> from are not independent.** Measured directly (cross-observable
> Spearman correlation matrix, participation-ratio effective rank, 5
> targets spanning N=169-704): the 28 types collapse to an effective rank
> of **~3**, a **~9× redundancy factor** (28/3 ≈ 9.3), consistent across
> every target tested (2.6-4.1, no wild swing). Rescaling the 366-cell
> total by that same factor (illustrative, proportional — not a full
> cell-by-cell re-derivation, see that task's own Done section for why)
> gives **~39 effectively-independent cells, expected false positives
> `0.05 × 39 ≈ 2`** — down from ~18.3, not up. **This section's own
> rhetorical move ("more cells makes zero-confirmed-positives a stronger
> claim") runs the wrong direction once redundancy is accounted for: more
> *non-independent* cells do not strengthen the claim.** Not corrected in
> place here (no-silent-overwrite) — flagged for whoever next touches
> this headline number or [[TASK-0184]]'s narrative, same as the caveat
> immediately above.
>
> **Combined, honest reading (both caveats together, [[TASK-0205]],
> 2026-08-05):** the observed count is **no longer zero** (PTP1B's
> `dcc_low` survives its own bar, per the caveat above) **and** the
> expectation it is measured against is **~2, not ~18.3** (per this
> caveat). Read plainly: one observed survivor against an expected ~2 is
> a real, if modest, claim — not the "stronger than the review
> anticipated" position this section's own headline sentence still
> asserts below. Both halves of the original argument moved against the
> program; neither is softened here, both are stated because a referee
> will check this arithmetic.

**Diagnostic-cell counting rule, decided and recorded (this task's own Open
Question)**: cells scored against a **synthetically planted** patch or a
**synthetic decoy** ligand — not the real drug-pocket answer key — do **not**
count toward this budget, matching the frozen table's own precedent for
excluding dumbbell gates and negative controls. On this rule, [[TASK-0167.001]]/
[[TASK-0167.002]]/[[TASK-0167.003]]'s entire positive-control/specificity-
measurement program (planted-channel detection curves, zero-plant
false-positive rates) is excluded — those tasks measure the *apparatus's own
operating characteristics* (its power and its false-positive rate), not
comparisons against real target labels that could themselves be a reported
"finding." Also excluded, with reasons stated so the rule is checkable, not
just asserted:

| Task | Reason excluded |
|---|---|
| [[TASK-0160]] | Engineering deliverable (dense quantum connectivity matrix), no p-value/AUC-vs-floor comparison |
| [[TASK-0164]] | Zero new ASD candidate targets qualified — nothing to score |
| [[TASK-0165]] | Re-checks CI method on already-counted cells (same non-double-counting precedent the frozen table above already applies to [[TASK-0123]]) |
| [[TASK-0167.001]]/[[TASK-0167.002]]/[[TASK-0167.003]] | Synthetic positive-control/specificity measurement — see diagnostic-cell rule above |
| [[TASK-0169]] | Pure re-verification/synthesis, no code touched, no new scoring |
| [[TASK-0180]] | Infrastructure (site-clustering module wired into `run_challenge.py`) + a 2-target linkage-cutoff robustness check; no p-value/Bonferroni family reported |
| [[TASK-0182]] | Hardware/resource accounting (qubit/gate/depth tables, one Braket-style execution) — not AUC-vs-label scoring |
| [[TASK-0186]]/[[TASK-0188]] | Geometric/topological distance diagnostics (Euclidean/graph-hop), not a scored AUC/p-value against labels |
| [[TASK-0190]] | Status: In Progress, not Done — excluded from this recount, included in the next one once it lands |
| [[TASK-0172]]/[[TASK-0176]]/[[TASK-0183]]/[[TASK-0184]] | Status: TODO — not yet run |

**Recount is reproducible by construction**: every increment above is either
the owning task's own self-stated cell count (quoted) or a one-line
arithmetic derivation from its Done section, and every exclusion states its
reason — a second person re-deriving from the same 10 task files should
land on the same 140 and the same 366.

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
`results/tasks/0165_spatial_ci/spatial_ci_rerun.json`,
`src/allostery/metrics.py::spatial_block_bootstrap_ci`, `tests/test_metrics.py`.

---

## Per-residue GNM low-mode conformational entropy — the ensemble/entropic mechanism (TASK-0166, `PANEL_REVIEW_2026-07-25.md` §7.3(1)/V9, 2026-07-28)

**Tests the challenge's own reference [4] (Motlagh & Hilser, *Nature* 2014)
directly for the first time in this program: allostery as ensemble
*redistribution*, not signal *transmission*.** Every other observable in
this register seeds at the active site and asks "where does something
propagate" — a directed-channel picture. This one has no seed and no
propagation step at all: it scores each residue by its own accessible
conformational ensemble under the apo structure's GNM low-mode subspace,
independent of the active site's location.

**Formalism (literature-confirmed, not invented, resolving this task's own
filed Open Question):** the founding GNM paper (Bahar, Atilgan & Erman,
*Fold. Des.* 2:173-181, 1997) establishes that each residue's fluctuation is
Gaussian-distributed with variance `sigma_i^2 = sum_k (1/lambda_k) U_ik^2`
— the standard MSF formula, here restricted to the lowest `n_modes=20`
Kirchhoff eigenmodes (matching the register's own established low-mode-
subspace convention, e.g. `compute_learnability`'s `n_modes=20`). The
differential entropy of a Gaussian, `h = 0.5*ln(2*pi*e*sigma^2)`, is a
textbook information-theory identity (Cover & Thomas, *Elements of
Information Theory*, Thm. 8.4.1). New `allostery.conformational_entropy`
combines these — no new physics, an existing identity applied to an
existing, already-validated GNM quantity. **Noted explicitly**: entropy is
a strictly increasing function of the underlying variance, so every
AUC/ranking result below is, by construction, identical to what raw
`gnm_lowmode_variance` alone would give (confirmed as a direct test,
`test_conformational_entropy.py`) — this observable is a Gaussian-entropy
*reframing* of low-mode flexibility, not an independent ranking.

**Real-target scoring, all 7 pocket-scoreable `status: verified` targets**
(3 mandatory + PTP1B/GLUCOKINASE/CASPASE1/CASPASE7; MYC_MAX excluded — its
own config states `allosteric_pocket_exists: false`, no pocket label
exists to score against). TASK-0123 distance-stratified AUC (well-powered-
shell max) + TASK-0158's corrected compact-patch permutation null
(`nulls.compact_patch` used directly — this task postdates TASK-0158, no
reason to use the superseded scattered draw even once):

| Target | Well-powered max AUC (shell) | Null p-value | Bonferroni (α/7=0.00714) | ρ(entropy, −hop) | ρ(entropy, −euclid) |
|---|---|---|---|---|---|
| KRAS_G12C | 0.730 (shell 2) | 0.241 | no | 0.544 | 0.623 |
| BCR_ABL1 | 0.741 (shell 3) | 0.326 | no | 0.585 | 0.541 |
| CARDIAC_MYOSIN | 0.623 (shell 3) | 0.394 | no | 0.763 | 0.764 |
| PTP1B | 0.356 (shell 3) | 0.712 | no | 0.694 | 0.782 |
| GLUCOKINASE | 0.971 (shell 3) | 0.035 | **no** | 0.651 | 0.610 |
| CASPASE1 | 0.371 (shell 1) | 0.677 | no | 0.390 | 0.505 |
| CASPASE7 | 0.353 (shell 2) | 0.718 | no | 0.559 | 0.759 |

**Headline: a clean negative, consistent with [[TASK-0161]]'s program-wide
finding.** Zero of 7 cells survive Bonferroni correction. GLUCOKINASE's
raw p=0.035 is the closest to significance anywhere in this table but does
not clear the 7-target-corrected bar (0.00714) — reported as the honest
near-miss it is, not rounded up.

**A second, arguably more informative negative: this observable is not
proximity-orthogonal, despite having no seed or propagation step at
all.** ρ(entropy, −hop) is strongly positive on every target (0.39–0.76),
matching the same confound magnitude found pervasively elsewhere in this
register (e.g. [[TASK-0146]]'s +0.68 to +0.72). Unlike [[TASK-0140]]'s
chiral circulation (proximity-orthogonal *by construction*) or
[[TASK-0149]]'s low-mode PRS/DCC (mode-filtered specifically to weaken
this confound), nothing about a Gaussian-entropy reframing of GNM low-mode
flexibility structurally guarantees independence from distance-to-seed —
and empirically it does not deliver any. This task's own Planned
Validation asked exactly this question ("does entropy-based ranking
correlate with, or is orthogonal to, the proximity floor") and the answer
is a clear, direct "correlates," not "orthogonal" — the ensemble mechanism,
at least as operationalized here (a per-residue flexibility magnitude, not
a distributional/mode-diversity measure — see the module's own docstring
for why that narrower reading of the Intent Contract was chosen over the
broader "discretized Shannon entropy over mode-participation weights"
alternative), does not evade the confound that has dominated every
directed-channel observable in this program either.

Scope boundary honored per this task's own Out of Scope: no MD, no full
ensemble reweighting/Boltzmann conformer sampling — a mode-participation
entropy proxy only, stated as such, not silently expanded.

9 new unit tests (`tests/test_conformational_entropy.py`), full suite:
971 passed, 2 xfailed, 0 failed. Full detail:
`.ai/tasks/DONE/TASK-0166-ensemble-entropy-observable.md`,
`RESULTS/results/tasks/0166_ensemble_entropy/ensemble_entropy_real_run.json`,
`src/allostery/conformational_entropy.py`,
`scripts/ensemble_entropy_real_run.py`.

---

## Reverse-direction coupling test — seed at the pocket, score into the active site (TASK-0162, `PANEL_REVIEW_2026-07-25.md` §2.4/V5, 2026-07-28)

**Every observable in this project's register seeds at the active site and
asks where signal goes. Real allosteric experiments measure the reverse
direction — does binding at the candidate site perturb the active site,
the direction that matters therapeutically — and this project has never
computed it.** `labels.build_labels`'s own `pocket`/`active_site` masks
are guaranteed disjoint by construction (`pocket = pocket_raw &
~active_site & ~terminal`), so no special handling was needed to swap
which set is the seed and which is the scored/labeled candidate set —
new `scripts/reverse_direction_coupling_test.py` reuses every scoring
function completely unmodified (this task's own Out of Scope), only the
seed/label assignment swaps: **FORWARD** = source active site, label
pocket (recomputed fresh here, matching every already-published number
exactly — e.g. KRAS_G12C `ctqw_converged` 0.5901, identical to
[[TASK-0130]]/[[TASK-0159]]'s own number, confirming no discrepancy was
introduced); **REVERSE** (new) = source pocket, label active site.

**5 observables ("at minimum" per this task's own Intent Contract) × 5
targets (3 mandatory + PTP1B/CASPASE7 — this task's own Open Question
resolved in favor of running both: compute cost is negligible, all 5
observables are closed-form/direct linear algebra, full run under a
minute)**: `time_averaged_ctqw_converged` ([[TASK-0130]]), `prs_low`/
`dcc_low` at `k_modes=20` ([[TASK-0149]]'s own established default —
not a fresh per-direction k-sweep, a deliberate scope choice: this task
re-applies the existing best-performing observables, it does not
re-characterize their own k-sensitivity a second time), `R_eff` (on
`H2_combinatorial_laplacian`) and `T(E=0)` (on `H_new`) ([[TASK-0145]]).
Each direction scored against [[TASK-0094]]'s own proximity floor,
computed fresh in the *same* direction (i.e. the reverse floor is "how
well do trivial distance/degree baselines *from the pocket* predict
active-site membership," not the forward floor reused backwards).

**Headline: a real, decisive, and target/observable-dependent
asymmetry — reverse clears its own floor far less often than forward.**
Across all 25 target × observable cells: forward clears floor in
**10/25 (40%)**, reverse in only **4/25 (16%)**, both directions in only
**2/25 (8%)** (KRAS_G12C `dcc_low`: fwd 0.522/rev 0.632, both clear, reverse
even stronger; BCR_ABL1 `T(E=0)` on `H_new`: fwd 0.636/rev 0.726, both
clear, reverse also stronger). **The single most striking cell is this
project's own strongest whole-graph result**: CARDIAC_MYOSIN `prs_low`
forward AUC **0.836** (clears floor 0.568) collapses to reverse AUC
**0.321** (anti-correlated, well below its own floor 0.674) — a large,
real, target-specific asymmetry on the project's own headline finding,
reported plainly rather than smoothed over. (This task's own whole-graph
AUC is not directly comparable to [[TASK-0149]]'s own distance-stratified,
well-powered-shell max AUC (0.922) for the same cell — a deliberately
simpler, floor-only lens applied uniformly across all 25 cells here, not
a re-run of that task's own stratified methodology; stated explicitly, not
conflated.)

**Background asymmetry statistic** (Spearman ρ between forward and
reverse score vectors, restricted to residues in *neither* pocket nor
active site — this task's own explicit design choice: correlating the
full N-residue vectors would mostly measure "does each labeled set have
high self-occupancy in its own seeded direction," true by construction
and not a real coupling question; the background restriction isolates
whether residues outside either label respond similarly regardless of
which end perturbs): **mostly strongly positive** (mean ρ=0.61, median
0.73, range −0.44 to 0.95) — the *rest of the protein's* own coupling
structure is largely reciprocal even on cells where the specific
labeled-set AUC differs sharply (e.g. CARDIAC_MYOSIN `prs_low`'s own
ρ=0.90 despite its 0.836-vs-0.321 AUC collapse — the background residues
still respond similarly either direction; the asymmetry is concentrated
in the labeled sets specifically, not the whole graph). Exactly 1/25 cells
(`dcc_low`, BCR_ABL1) shows real background anti-correlation (ρ=−0.44).

**No previously-reported verdict is changed by this task** — forward
numbers reproduce already-published values exactly (a real, if implicit,
consistency check on both this task's own script and the underlying
propagators); reverse is a new measurement, not a correction to an old
one. **Scale effect noted on the generalization targets**: PTP1B/CASPASE7
both have only 5 active-site residues (vs. 14/16/18 pocket-sized sets),
producing a much higher reverse floor (0.90–0.91, vs. 0.56–0.62 on the 3
mandatory targets) — a 5-residue positive-label set is trivially easy for
distance/degree baselines to nail when seeded from a nearby 7-14-residue
region, a real scale effect stated plainly, not a target-specific anomaly.
CASPASE7's `R_eff` reverse (0.906) is the one cell on the generalization
set that clears this elevated bar.

**No permutation-null gate applied to the reverse cells specifically**
(this task's own scope: "pure re-application... only the seed/candidate-set
assignment swaps," no new statistical machinery) — a natural follow-up for
whoever next wants a Bonferroni-corrected verdict on the reverse direction
specifically, not done here.

Full detail: `.ai/tasks/DONE/TASK-0162-reverse-direction-coupling-test.md`,
`RESULTS/results/tasks/0162_reverse_direction/reverse_direction_coupling_test.json`,
`scripts/reverse_direction_coupling_test.py`.

---

## Benchmark discriminability audit — can the mandatory target set certify *any* method? (TASK-0169, `PANEL_REVIEW_2026-07-28-external.md` §6/§7, 2026-07-28)

**The project's current narrative is "we could not find quantum advantage for
allosteric site prediction, and we built a rigorous apparatus that proves we
could not." That is honest and defensible, but modest — a negative result
about one team's approach.** A stronger, evidenced claim is available and is
consolidated here for the first time — until now it was scattered across a
YAML comment, several open-questions rows, and five separate task Done
sections, with no single artifact stating the aggregate:

> **The mandatory benchmark cannot currently certify a working method, and we
> can demonstrate that with our own apparatus.**

Framed as measurement, not criticism, per this task's own Constraint — these
are structural properties of a benchmark assembled from the available PDB
entries at challenge-authoring time, not an accusation that the organizers
erred. All three mandatory targets are still reported in full per the
challenge's own §5; this is context alongside them, not a substitute.

**Every row independently re-verified against RCSB directly by this task
(live REST API / cross-referenced structure entries), not relayed from
memory or a prior task's own text** — per this task's own Constraint, and
because doing so caught one real, stale number (below):

**[[TASK-0206]], 2026-08-06: every fpocket AUC in this table's "All 3" row
(0.8348/0.8596/0.5345) is superseded** — a different machine could not
reproduce them (0.7910/0.8618/0.5303, now the pinned/authoritative set,
`tools/fpocket/PROVENANCE.json`) — root-caused to an unpinned per-machine
binary build, not a code or label bug. No verdict in this row changes
(fpocket still beats floor and actual on 2/3 targets under either number
set). Kept below verbatim, per this document's own no-silent-overwrite
convention; see this document's own dated "fpocket binary drift" section
for the full diagnosis. This one callout covers every `0.8348`/`0.8596`/
`0.5345` mention in this section (5 occurrences below), not edited
individually.

| Target | Established defect | Re-verified |
|---|---|---|
| CARDIAC_MYOSIN | Challenge Table 1's named validation structure **6C1H does not contain mavacamten** | **Re-confirmed live, 2026-07-28**: RCSB REST API, `nonpolymer_bound_components = ['ADP', 'MG']` only; the 3 polymer entities are actin (rabbit), unconventional myosin-Ib (rat), and calmodulin — no myosin motor domain, no XB2. This project's own substituted validation structure (8QYR) *does* contain XB2/mavacamten (RCSB-reconfirmed 2026-07-06, and independently corroborated by a second structure, 9GZ1, TASK-0124) — the challenge's own named structure fails, this project's substitute passes. |
| CARDIAC_MYOSIN | Challenge-specified apo **5TBY is a 20 Å docked homology model**; replacing it with 8QYP erased the target's only positive result | **Re-confirmed live**: 5TBY's own RCSB title reads *"...OBTAINED BY HOMOLOGY MODELING... RIGIDLY FITTED TO... 3D-RECONSTRUCTION"*, method=EM, resolution=20.0 Å exactly. 8QYP confirmed X-ray, 2.759 Å, drug-free (ADP/MG/VO4, no XB2). Actual AUC: **0.7912 (5TBY) → 0.5176 (8QYP)** ([[TASK-0124]]'s own executed re-run) — resolving the structure removed the result. |
| KRAS_G12C | Switch-II pocket **overlaps the active site** — a "distal" prediction task is partly a self-hit task | **Re-verified directly** (fresh geometric check, this task): minimum Cα–Cα distance between an active-site residue and a pocket residue is **3.75 Å** (van der Waals contact range); mean nearest-neighbor distance 9.85 Å. Pocket residues 9–11 sit immediately adjacent to the active-site block (12–19, includes the G12C mutation site and P-loop). **A stale number caught and corrected**: this task's own filing cited the proximity floor as "0.798" — that is TASK-0094's original, pre-[[TASK-0118]]/[[TASK-0121]]/[[TASK-0130]] number; the current, fully-corrected floor (`COMPETENCE_MAP.md`, recomputed under the closed-form propagator) is **0.4818**, not 0.798. Both numbers support the same qualitative point (a trivial baseline scores respectably), but the current one is what should be cited going forward. |
| BCR_ABL1 | Myristoyl pocket is **pre-formed in the apo structure**, not cryptic | **Re-cited from an already-executed measurement**, not re-run: [[TASK-0120]]/[[TASK-0139]]'s own apo→holo pocket-RMSD-vs-background ratio is **0.49** — the pocket moves *less* than background upon ligand binding, the opposite of a cryptic-opening signature, consistent with TASK-0104's independent "apo-computable structural prior, not communication signal" mechanism finding. |
| All 3 | **fpocket, a 2009 classical geometric tool with no dynamics, no eigendecomposition, and no active-site seed, beats this project's own best quantum-flavored observable on 2/3 mandatory targets** | **Re-cited from an already-executed real run** ([[TASK-0163]], this document's own "External classical-pocket-detection baselines" section, real code/real data): KRAS_G12C fpocket **0.8348** vs. this project's actual 0.5901 (floor 0.4818); BCR_ABL1 fpocket **0.8596** vs. actual 0.5266 (floor 0.5817); CARDIAC_MYOSIN fpocket 0.5345 vs. actual 0.5176 (floor 0.5679, fpocket sits just below it). |
| ASD extension | Generalization pool **fully exhausted** — 0 of 6 remaining draft configs are resolvable | **Re-cited from an already-executed audit** ([[TASK-0164]]): 6 real `status: draft` targets remain; 5 already RCSB-verified permanently blocked ([[TASK-0127]]); the 6th (`GROEL_SUBUNIT`), independently RCSB-verified by that task, has two separate permanent blockers of its own (partial biological assembly; a 7-chain-protein ligand `labels.py`'s methodology cannot handle). Zero of 6 qualify. |

**Per-target discriminability verdict, 3 axes stated plainly** ([[TASK-0167.002]]'s
own detection-limit work is still TODO/unclaimed as of this writing — no axis 4,
per this task's own conditional scope):

**KRAS_G12C** — (1) *Ground truth valid?* **Yes**, unambiguously (6OIM
RCSB-reconfirmed to contain MOV/sotorasib, no discrepancy). (2) *Task the
stated task?* **No** — the pocket is 3.75 Å from the active site at closest
approach; "distal allosteric prediction" partially reduces to "predict
something adjacent to the seed," a task every proximity-based method
structurally favors. (3) *Task non-trivial?* **No** — fpocket (0.8348, purely
geometric, no seed) decisively beats both the corrected floor (0.4818) and
this project's own best observable (0.5901, itself not statistically
decided against its own floor — CI overlaps).

**BCR_ABL1** — (1) *Ground truth valid?* **Yes** (5MO4 RCSB-reconfirmed,
no flagged discrepancy). (2) *Task the stated task?* **No** — the myristoyl
pocket is measurably pre-formed in apo (RMSD ratio 0.49, moves less than
background), not cryptic; the "predict the cryptic pocket" framing does not
describe what is actually being measured here. (3) *Task non-trivial?*
**No** — fpocket (0.8596) beats both floor (0.5817) and actual (0.5266) by
a wide margin.

**CARDIAC_MYOSIN** — (1) *Ground truth valid?* **Split, stated precisely, not
averaged away** — the challenge's own named validation structure (6C1H) does
NOT contain the ligand (re-confirmed live, above); this project's own
substituted structure (8QYR) does, independently corroborated by a second,
different-species/different-method structure (9GZ1). A referee checking the
challenge's own Table 1 literally will not find mavacamten in the named
entry. (2) *Task the stated task?* **Unresolved, not evidenced either way**
— no equivalent apo-vs-holo pocket-RMSD measurement has been run for this
target's own current (8QYP/8QYR) structure pair the way KRAS_G12C/BCR_ABL1
have; stated as a real gap, not assumed. (3) *Task non-trivial?* **Weakly
yes** — fpocket (0.5345) does not clear its own floor (0.5679, −0.033),
though it does edge out this project's own actual (0.5176, +0.017); the
weakest evidence for the "non-trivial" reading among the 3 targets, but not
a clean fail either.

**c-Myc/1NKP is deliberately not a table row** (this task's own Open
Question, resolved as recommended): it carries no ground truth by design
(`holo_pdb: null`, scored on cross-operator consensus + fpocket docking
viability only, [[TASK-0080]]) — the discriminability question does not
apply in the same form (there is no label to be trivially or non-trivially
recovered). Nothing in this audit bears on that target's own reporting.

**On how hard to push the fpocket finding** (this task's own second Open
Question, resolved as recommended): reported prominently above, without
editorializing — the numbers (0.8348/0.8596 vs. this project's own 0.5901/
0.5266) are self-explanatory, and any additional framing would only weaken
a comparison that already speaks for itself.

**Specification of a certifying benchmark** (the constructive half — what
would need to be true for the mandatory-target framework to actually
distinguish a working method from a broken one):

1. **Holo structures verified to contain the named ligand** — not assumed
   from a challenge document, checked directly against RCSB before use
   (exactly the gap 6C1H exposes).
2. **Pockets verified both distal *and* absent in apo** — a genuine
   cryptic-pocket criterion (e.g. this project's own apo→holo pocket-RMSD-
   vs-background ratio, [[TASK-0120]]), not a bare drug-contact proxy that
   can silently include a pocket that is pre-formed (BCR_ABL1) or adjacent
   to the seed (KRAS_G12C).
3. **A stated geometric-baseline floor per target**, run and reported
   *before* any dynamical/quantum method is scored — if a 2009 classical
   tool with no dynamics already wins, that is load-bearing information
   about what the benchmark is actually testing, not an afterthought.
4. **At least one target with mechanism-validated, not drug-derived,
   ground truth** — every current label is a drug-contact proxy for
   allostery, not a direct measurement of an allosteric mechanism (see
   [[TASK-0170]]).
5. **A published detection limit for the scoring protocol** — for any
   target where the method's own limit of detection exceeds plausible
   physical coupling strength, a negative result is uninformative about
   that target specifically, and a benchmark should say so rather than let
   a null result read as a method failure ([[TASK-0167]]/[[TASK-0167.002]]).

Full detail: `.ai/tasks/DONE/TASK-0169-benchmark-discriminability-audit.md`,
`COMPETENCE_MAP.md`'s own "Benchmark discriminability audit" section,
open-questions row 46.

---

## Detection curve + limit of detection (TASK-0167.002, 2026-07-28)

**The headline sentence, with real numbers: through the historically-used
(scattered) permutation null, this program detects a planted active-site→
distal-patch coupling at ≥80% power once conductance (`R_eff`) rises to
~1.9–2.1× background, on 2 of 3 mandatory targets. Through the corrected,
spatially-compact null ([[TASK-0158]]) — the statistically correct one — no
target reaches 80% power at any tested strength, up to 4.0–4.7× background
conductance. The apparatus's true detection threshold, under the null this
project now uses, is higher than anything tested here, or the tested strength
range itself needs to extend further — this experiment cannot distinguish
those two readings and says so plainly.**

### Scope, built on [[TASK-0167.001]]'s own decisive finding

Reconfirmed directly on all 3 targets before running anything else:
`time_averaged_ctqw_converged` on `H_new`, `dcc_low`, and `prs_low` are all
**exactly** invariant to this plant mechanism (`np.array_equal`, strength 0 vs.
32, every target) — 3 of this program's 4 headline observables cannot be
tested by a weight-only channel plant at all, confirmed rather than assumed
from [[TASK-0167.001]]'s own single-target check. Their own `NO_SIGNAL_IN_APO`
verdicts throughout this project's history carry **no stated detection bound
from this control** — a mode/ensemble plant ([[TASK-0168]]) would be needed.
The real, informative sweep below covers the one plant-sensitive observable
this program's negative claims rest on: `T(E=0)` on a weighted
`hamiltonians.laplacian(W_planted)` ([[TASK-0145]]'s own unresolved cell).

### Method

3 mandatory targets × 8 log-spaced strengths ({0, 0.5, 1, 2, 4, 8, 16, 32}) ×
20 planting seeds × 3 null specifications, through the **unmodified** verdict
pipeline (floor → CI non-overlap → stratified-AUC permutation null →
Bonferroni), certification requiring all four gates. Checkpointed per cell
(`scripts/positive_control_detection_curve.py`, `results/tasks/0167002_
detection_curve/detection_curve.json`, 480 cells, ~87 CPU-minutes). Both
`block_bootstrap_ci` (sequence) and `spatial_block_bootstrap_ci` (spatial) are
computed and gated on for every cell, per this task's own Constraint —
mid-task, the external review's own claim that the spatial method's 1D-line
regression test is invalid was verified directly (measured 55% mean block
overlap, not the exact coincidence [[TASK-0165]]'s own docstring claimed;
corrected there, not fixed here — see that task's own 2026-07-28 correction
note). **In the event, both CI methods gave identical LOD values on every
target** — the review's real, now-corrected concern did not change this
task's own bottom line.

**Real bug found and fixed before trusting any number**: the collection
script's own `certified`/`gate4_clears_bonferroni` fields divided α by
`len(strengths)×len(seeds)=160`, treating this experiment's own synthetic
replicate grid as 160 simultaneous real hypothesis tests. The correct
Bonferroni family for a real deployment of this observable is **targets**
(matching [[TASK-0145]]'s own established convention, α=0.05/3≈0.0167), not
this script's internal measurement device — recomputed from each cell's own
raw, uncorrected `p_value` in `scripts/detection_curve_analysis.py`, no
re-run needed (only the Bonferroni denominator was wrong, not the p-values).

### LOD (smallest strength with P(certified) ≥ 0.80, both CI methods identical)

| Target | Scattered null (historical) | Compact null ([[TASK-0158]]) | Rg-matched null |
|---|---|---|---|
| KRAS_G12C | **8.0** (P=1.00 [0.83,1.00]) | ∞ (max P=0.35 at s=8) | ∞ (max P=0.35 at s=8) |
| BCR_ABL1 | ∞ (max P=0.60 at s=32) | ∞ (max P=0.00, every strength) | ∞ (max P=0.00, every strength) |
| CARDIAC_MYOSIN | **8.0** (P=0.85 [0.62,0.97]) | ∞ (max P=0.50 at s=8) | ∞ (max P=0.50 at s=8) |

**In induced-coupling units** (mean conductance seed→patch, `R_eff`'s own
`1/R_eff` return convention, [[TASK-0167.001]]'s resolved dose axis): strength
8 corresponds to **2.14× background** on KRAS_G12C (0.728→1.560) and **1.93×**
on CARDIAC_MYOSIN (0.544→1.052); the grid's own top (strength 32) reaches
**4.69×** (KRAS_G12C) and **3.97×** (CARDIAC_MYOSIN) background conductance
without the corrected null ever reaching 80% power on any target. Full table:
`results/tasks/0167002_detection_curve/dose_axis_conductance.json`.

**This is a direct, quantitative, and considerably more severe confirmation
of the external review's own §2.1 "2–2.5× power cost" estimate** — measured
here as "undetectable within the tested range" on the corrected null, not
merely a 2–2.5× SNR reduction, on every target tried.

### Per-gate failure profile — the CI gate and the null gate are BOTH independently binding

Neither gate alone explains the corrected-null LOD failure (this task's own
"as valuable as the LOD itself" instruction, taken literally): on KRAS_G12C at
strength 32, gate 1 (beats floor) passes 100% of the time, yet gate 2 (CI
non-overlap) *fails* 50–55% of the time even then — a real, somewhat
counter-intuitive finding (stronger planted signal does not monotonically
narrow/separate the score's own bootstrap CI from the floor's; a more
concentrated, less-evenly-distributed effect plausibly produces a *noisier*
block-resampled CI, not a tighter one — a plausible mechanism, not
independently verified here). Even restricting to cells where gates 1 and 2
both pass, the compact/matched-null permutation test alone caps P(certified)
at 35–50% at every target's own best strength — both gates are real,
independent bottlenecks, not one dominant cause.

### Non-monotonicity — a real finding, not noise (Planned Validation's own sanity check)

P(certified) for the compact/matched nulls is **not** monotonically
non-decreasing in strength on 2 of 3 targets: KRAS_G12C peaks at strength 8
(P=0.35) and *falls* to 0.05 by strength 32; CARDIAC_MYOSIN peaks at strength
8 (P=0.50) and falls to 0.45 by strength 32. Plausible mechanism, exactly the
one [[TASK-0167.001]]'s own Open Questions flagged as a risk and did not
investigate further: at extreme strength the planted channel's own
intermediate residues (negatives under the patch label) become strongly
scored themselves, and channel leakage depresses within-shell discrimination
enough to counteract the raw AUC gain — consistent with, not contradicting,
[[TASK-0167.001]]'s own prediction. Not chased to a full mechanistic
confirmation here (out of this task's own scope), but the direction and
magnitude match the predicted mechanism closely enough to name it, not just
flag it as unexplained noise.

### Compact vs. Rg-matched null: empirically indistinguishable in this regime

**Every P(certified) value is identical between the `compact` and `matched`
null columns, on every target, at every strength** — verified this is real,
not a bug: `nulls.compact_patch_matched` accepts on its first or second draw
in 19/20 direct trials (±35% Rg tolerance). A fresh `compact_patch` draw of a
fixed size already has a naturally tight Rg distribution across random seed
choices, so it is already within the review's own matching tolerance almost
always — the Rg-matched refinement adds no additional conservatism beyond
plain compactness for a 14-residue patch on these targets. This is itself an
answer to part of the external review's own over-correction question: the
*compact-vs-scattered* gap is real and large (this section's own headline);
the *compact-vs-Rg-matched* gap is not measurable here because the two nulls
are not meaningfully different draws at this patch size.

### BCR_ABL1's own poor showing — a real, target-specific limitation, not smoothed over

BCR_ABL1 never reaches 80% power under **any** null specification, including
the historically-lenient scattered one (max P=0.60 at the top of the grid).
Gate 1 alone fails 60% of the time even at strength 0–4 — this target's own
selected patch sits closer to its own pre-plant floor than KRAS_G12C's or
CARDIAC_MYOSIN's (by construction, `select_distal_patch`'s own admission
bar is ≤0.5, not ≤0, so patches near that boundary are legitimate draws, not
a selection bug), and BCR_ABL1 (N=451, the largest topology after
CARDIAC_MYOSIN) may simply have a more redundant, competitive proximity floor
this channel-reweighting mechanism struggles to overcome. Reported as a real,
target-specific finding, not investigated to a root cause here.

### Interpretation

**Every `NO_SIGNAL_IN_APO`/`BEATS_CHANCE_NOT_FLOOR` verdict this program has
ever reported for `T(E=0)`-family observables should now be read against this
LOD, not as an unqualified negative**: under the null this project currently
uses (compact, [[TASK-0158]]), this apparatus has not been shown to reliably
detect a planted coupling as strong as ~4× background conductance on any of
the 3 mandatory targets. This does not mean weaker real signal is absent —
only that this control has not demonstrated the pipeline *would* have caught
it if present at the strengths tested. Per this task's own Out-Of-Scope, no
gate, threshold, or null is adjusted in response — the corrected null stands,
and this is reported as the honest cost of using it, exactly the framing the
external review itself anticipated ("makes the project's negative conclusions
safer... but makes any positive finding's CI/power less trustworthy than
reported"). A natural follow-up (not attempted here, out of scope) is
extending the strength grid past 32× to find where compact-null detection
actually saturates, if it does before physically implausible coupling
magnitudes.

Full detail: `.ai/tasks/DONE/TASK-0167.002-detection-curve-and-limit-of-detection.md`,
`results/tasks/0167002_detection_curve/detection_curve.json`,
`results/tasks/0167002_detection_curve/analysis_summary.md`,
`results/tasks/0167002_detection_curve/dose_axis_conductance.json`,
`scripts/positive_control_detection_curve.py`, `scripts/detection_curve_analysis.py`.

---

## Zero-plant specificity and null-calibration (TASK-0167.003, 2026-07-31)

> **Recovery note ([[TASK-0191]], 2026-08-03): this section was written on
> 2026-07-31 but deliberately withheld from commit `92aa669` — that commit's
> own message states a concurrent thread's uncommitted [[TASK-0157]] edit
> shared the same working-tree file, and splitting them was "left to a
> follow-up rather than risking either thread's content." No follow-up
> landed; `grep -n "zero-plant\|null-calibration" RESULTS.md` returned zero
> hits until this recovery, even though both `.ai/tasks/DONE/TASK-0167.003-*.md`
> and that commit message cite this section as "Full detail." Reconstructed
> directly from that task file's own Done section (the record survived there
> completely) — same failure class as `Q-0001`/[[TASK-0107]] on `COMMON.md`:
> an unprotected concurrent write to a shared synthesis file lost the
> synthesis, not the underlying record. Part A below carries [[TASK-0189]]'s
> 2026-08-03 correction applied directly, not published as originally run.**

**With `strength=0` (no planted coupling at all, `W` bit-identical to
unplanted — asserted, not assumed), how often does the full verdict
pipeline certify a randomly placed distal compact patch?** The real,
end-to-end false-positive rate, under each of [[TASK-0158]]'s three null
specifications, plus a direct calibration check of each null's own
geometry against the real pocket's.

### Method

Reused [[TASK-0167.002]]'s own `_prepare_target`/`_well_powered_max` helpers
directly (imported, not re-derived) so this task is a genuine second route
to the same false-positive rate, not a duplicate of the first. 500 randomly
placed distal compact patches per (target, observable), same admission
criteria as .002's planted patches (distal, floor-AUC ≤0.5 pre-draw), pushed
through the complete certification chain. **A real, documented optimization
over naively copying .002's per-cell loop**: at `strength=0`, `plant_channel`
returns `W0` bit-identical (re-verified here, not assumed), so the score is
one fixed vector per target; the scattered/compact permutation null is also
patch-independent (depends only on `pocket_size`, fixed at 14) and
precomputed once per target rather than redrawn 500 times — only the
Rg-matched null genuinely depends on the tested patch and is redrawn per
patch (at a documented, reduced 200 replicates rather than 1000).

### Part A — measured false-positive rate, 3 mandatory targets, 500 distal patches each

**Corrected by [[TASK-0189]], 2026-08-03 — the number below supersedes this
task's own original run.** The original collection script certified against
`bonferroni_alpha = ALPHA / (len(STRENGTHS) * N_SEEDS)` = 0.05/160 ≈ 3.125e-4
— copied from [[TASK-0167.002]]'s own *collection*-script constant without
that task's matching *analysis*-stage correction to the real deployment
family (targets, α=0.05/3≈0.0167, [[TASK-0145]]'s convention). At that
denominator the certification gate was also structurally unreachable (the
smallest non-zero p-value, `1/1000` or `1/200` for the matched null, exceeds
3.125e-4), so it could only ever fire at `p_value == 0.0` exactly — the
original table measured certification under a ~53× stricter, partly
unreachable bar, not "against a 5% nominal bar" as originally described.
[[TASK-0189]] recomputed from the same stored raw `p_value` fields at the
corrected, reachable α (confirmed reachable first:
`assert_gate_reachable(0.01667, family_size=3, n_reps=1000/200)` both hold)
— no collection re-run needed, only the denominator was wrong:

| Target | Scattered α̂ (95% CI) | Compact α̂ (95% CI) | Matched α̂ (95% CI) |
|---|---|---|---|
| KRAS_G12C | 0.000 [0.000, 0.007] | 0.000 [0.000, 0.007] | 0.000 [0.000, 0.007] |
| BCR_ABL1 | **0.230** [0.194, 0.269] | 0.000 [0.000, 0.007] | **0.034** [0.020, 0.054] |
| CARDIAC_MYOSIN | 0.030 [0.017, 0.049] | 0.000 [0.000, 0.007] | 0.000 [0.000, 0.007] |

(Nominal α = 0.05/3 ≈ 0.01667, the corrected, reachable bar — TASK-0145's
across-*targets* Bonferroni family, not this measurement device's own
internal replicate grid.) **[[TASK-0189]]'s own verdict sentence, quoted
as-is**: *"The qualitative verdict is unchanged: the compact null remains
uniformly non-anti-conservative (α̂=0.000 on all 3 targets, unchanged), and
the scattered null's BCR_ABL1 anti-conservatism is confirmed, not weakened
(18.8% → 23.0%, if anything a stronger finding). What changes is the matched
null's own previously-reported '≤0.2% on every cell' claim — BCR_ABL1's
corrected matched α̂ is 3.4% (was an artificially tiny, gate-truncated 0.2%),
still comfortably below the 5% nominal single-test bar and still not
anti-conservative, but a materially different number than originally
published, now real and reachable rather than a gate artifact."* This is on
`transmission_from_source(E=0)` on a weighted `hamiltonians.laplacian` — the
one plant-sensitive observable this program's positive-control apparatus can
exercise ([[TASK-0167.001]]'s own finding that `H_new`/`dcc_low`/`ctqw` are
plant-blind); not a re-test of the external review's own `dcc_low`-specific
synthetic audit.

### Part B — the calibration statistic: real pocket Rg vs. each null's own draw distribution, all 7 pocket-scoreable targets

| Target | Real pocket Rg | Scattered null: real-pocket percentile | Compact null: real-pocket percentile |
|---|---|---|---|
| KRAS_G12C | 8.49 | 0.0 | 1.000 |
| BCR_ABL1 | 7.45 | 0.0 | 0.968 |
| CARDIAC_MYOSIN | 9.63 | 0.0 | 1.000 |
| PTP1B | 7.97 | 0.0 | 1.000 |
| GLUCOKINASE | 8.69 | 0.0 | 1.000 |
| CASPASE1 | 6.42 | 0.0 | 0.997 |
| CASPASE7 | 10.84 | 0.0 | 1.000 |

**The decisive, general, observable-independent confirmation of the external
review's over-correction concern — measured directly on real data.** The
scattered null's own draws are, without exception, far less compact than any
real pocket (percentile 0.0 on all 7 — the real pocket sits below the
*minimum* of 2000 scattered draws' own Rg every time). The compact null's
own draws are, almost without exception, *more* compact than the real pocket
(percentile ≥0.97 on all 7, exactly 1.000 on 5/7) — real pockets are
systematically more dispersed than a pure k-NN ball, confirming the external
review's own synthetic finding ("the ball is ~30% more compact than a
surface patch") generalizes to every real target in this project's register.

### Part C — positive control on the calibration statistic itself

Reference Rg = 5.98 (median of compact draws, KRAS_G12C topology). A
deliberately scattered draw registers at percentile 0.0 (correctly
anti-conservative-direction); a deliberately over-compact draw (half-size
k-NN) registers at percentile 1.0 (correctly over-conservative-direction).
The statistic detects both known-bad extremes as designed.

### Concordance with TASK-0167.002's own `strength=0` row — checked, no disagreement

.002's own 20-seed `strength=0` cells: KRAS_G12C 0/20 all 3 nulls, BCR_ABL1
1/20 scattered / 0/20 compact / 0/20 matched, CARDIAC_MYOSIN 0/20 all 3
nulls. Every one is statistically consistent with this task's own 500-patch
measurement at the corrected rate (e.g. BCR_ABL1 scattered: a 20-draw
binomial sample at true rate 0.230 lands at exactly 1/20 with modest but
unremarkable probability — inside a 95% prediction interval). **No bug found
in either measurement** — the two routes agree; this task's own larger
sample simply resolves BCR_ABL1's scattered-null anti-conservatism with
enough precision to be decisive (20 samples cannot distinguish a 5% true
rate from a 23% one; 500 can).

### Verdict on the null-calibration dispute

**Compact and Rg-matched nulls are the calibrated choice on real data — not
because they are conservative in the false-positive-rate sense (Part A), but
because real pockets are measurably more dispersed than either draw's own
geometry (Part B).** Both are true simultaneously: a null built from a
systematically-too-compact patch population produces few false
certifications (conservative in the α sense) *and* is a poor geometric model
of the actual answer key (over-compact in the calibration-statistic sense) —
the same underlying fact read two ways, not a contradiction. **Recommend the
calibration statistic itself (Part B's own percentile check) become
`INVARIANCE_PROTOCOL.md`'s fourth class, CALIBRATION**, per the external
review's own suggestion — validated on real data across all 7 targets, not
just proposed.

Full detail: `.ai/tasks/DONE/TASK-0167.003-zero-plant-specificity-and-null-calibration.md`,
`.ai/tasks/DONE/TASK-0189-zero-plant-bonferroni-family-and-unreachable-gate.md`,
`results/tasks/0167003_specificity/zero_plant_specificity_full.json`,
`results/tasks/0167003_specificity/part_a_corrected.json`,
`scripts/zero_plant_specificity.py`, `scripts/zero_plant_specificity_analysis.py`.

---

## A null that can actually reach real pocket Rg — and one cell's verdict flips (TASK-0190 finding + TASK-0201 fix, 2026-08-03/04)

> **Note on this section's own provenance**: [[TASK-0190]] (Done, 2026-08-03)
> has **no `RESULTS.md` section of its own** — the same synthesis gap
> [[TASK-0191]] fixed for [[TASK-0167.003]] recurred one task later. This
> section covers both: TASK-0190's own finding (recapped, cited to its task
> file for full detail — not claimed as this task's own work) and
> [[TASK-0201]]'s fix + re-run built directly on it. Flagged, not silently
> absorbed: TASK-0190's own section should still be written by whoever owns
> that backfill; this section does not substitute for it.

### TASK-0190's finding: `compact_patch_matched` cannot genuinely reach real pocket Rg for CARDIAC_MYOSIN/PTP1B

The external review's §2.1 P0 ask was to re-test `dcc_low`
(CARDIAC_MYOSIN, PTP1B) and `T(E=0)` (BCR_ABL1) against a null matched to
each target's **real** pocket radius of gyration — not a synthetic patch's
own Rg, which is what `compact_patch_matched`'s only two prior call sites
did (`target_rg` derived from a `select_distal_patch` draw, itself drawn
from `compact_patch` — "matched ≈ compact" true by construction, not a
finding). TASK-0190 ran the real-pocket-Rg version and, per its own Planned
Validation ("verify the matched null's own draw-Rg distribution actually
centres on `target_rg` — do not assume rejection sampling worked"), found a
structural problem:

| Target | Real pocket Rg | `compact_patch`'s own max (20,000 draws) | Matched-null accepted-draw mean Rg |
|---|---|---|---|
| CARDIAC_MYOSIN | 9.628 | **7.784** (hard ceiling, never exceeded) | 6.544 |
| PTP1B | 7.969 | **7.134** (hard ceiling, never exceeded) | 6.024 |
| BCR_ABL1 | 7.448 | 8.287 (within range) | 6.501 |

For CARDIAC_MYOSIN and PTP1B, the real pocket's own Rg is **above the
maximum Rg a contiguous k-NN ball of that pocket's size can ever produce**
on that target's geometry (`p99.9 == max`, a hard support boundary, not a
rare tail event). `tol=0.35`'s wide acceptance window never raised
`RuntimeError` — its lower bound overlaps `compact_patch`'s own natural
upper tail, so it silently accepted draws dominated by that tail instead of
genuinely centring near `target_rg`. Despite this, TASK-0190's own
pre-registered survival evaluation (run before this defect was fully
characterised) found `dcc_low` still failed to clear its bar on both
targets under the miscentred matched null (p=0.033 CARDIAC_MYOSIN,
p=0.019 PTP1B) — reasoned as still defensible because the miscentred draws,
though short of target, were measurably *more* dispersed than plain
`compact` draws (hence more lenient, not less). Full detail:
`.ai/tasks/DONE/TASK-0190-real-pocket-rg-matched-null.md`.

### TASK-0201: why the ceiling exists, and a construction that reaches it

`compact_patch` always takes the `size` Euclidean-*closest* points to a
random seed — by construction the tightest possible packing available in
that seed's own local neighbourhood; it can never "reach past" a near point
to include a farther one. Across every possible seed, its achievable spread
is bounded by how anisotropic the densest local packing gets, and for a Cα
chain at roughly uniform local density, that ceiling is low and does not
vary much with seed choice. Real pockets, per [[TASK-0167.003]] Part B,
sit at the 97th–100th percentile of `compact_patch`'s own Rg distribution
on **every** target tested — real pockets often line a surface groove or
cleft: topologically contiguous, but geometrically elongated, not a tight
3-D ball.

New `nulls.graph_walk_patch`: randomized connected growth (Eden growth) on
the residue contact graph rather than Euclidean-nearest-neighbour
selection — each newly added residue only needs to be adjacent to
something already in the growing patch, not close to the original seed, so
the walk can wander along a curved surface path and reach far greater
spread for the same cardinality. **Verified empirically before trusting
it** (this task's own Constraint, the exact check TASK-0190 itself used to
catch the original defect): 20,000 unconstrained draws on both previously-
infeasible targets —

| Target | Real pocket Rg | `graph_walk_patch` max (20,000 draws) | Real-pocket percentile of unconstrained support |
|---|---|---|---|
| CARDIAC_MYOSIN | 9.628 | **14.152** | 83.8th |
| PTP1B | 7.969 | **14.299** | 17.9th |

Both real Rg values now sit **inside** the support, not at its edge — PTP1B's
real pocket is not even in the upper tail of `graph_walk_patch`'s own
distribution. `graph_walk_patch_matched` (same rejection-sampling/
`RuntimeError`/`return_attempts` contract as `compact_patch_matched`, for
direct comparison) accepted-draw mean Rg came in at 8.613 (CARDIAC_MYOSIN,
target 9.628) and 8.775 (PTP1B, target 7.969) — materially closer to target
than `compact_patch_matched`'s own 6.544/6.024, a real improvement in
centring, though still short of exact (the acceptance window's own
asymmetric proximity to the proposal distribution's mode remains a residual
effect, reported not hidden).

### Re-run, `dcc_low` (CARDIAC_MYOSIN, PTP1B), 20,000 replicates per cell — decisive precision, all three nulls side by side

Reused TASK-0190's own pre-registered survival bars unchanged (TASK-0149's
6-comparison bar for CARDIAC_MYOSIN, TASK-0151's 16-comparison bar for
PTP1B) and its own evaluation logic (point-estimate `p < bar`), per this
task's own Out-Of-Scope ("reuse it, do not re-litigate it"). Replicate
count raised from TASK-0190's own 1,000 to 20,000 once a near-bar p-value
turned up at lower precision — at `p≈0.003`, `n=1,000` gives a Monte Carlo
SE of ≈0.0017, too coarse to read a boundary call; `n=20,000` tightens
that to ≈0.0004.

**Ordering-consistency check passed on all 8 cells** (`p(scattered) ≤
p(matched) ≤ p(compact)`, TASK-0190's own Planned Validation) — no
violations, the strongest available evidence this is a real result, not an
artifact of the new construction.

| Target | k | p(scattered) | p(matched, graph-walk) [95% CI] | p(compact) | AUC | Bar | Survives? |
|---|---|---|---|---|---|---|---|
| CARDIAC_MYOSIN | 5 | 0.0071 | 0.1294 [0.1248, 0.1341] | 0.1356 | 0.903 | 0.00833 | No |
| CARDIAC_MYOSIN | 10 | 0.0024 | 0.0972 [0.0931, 0.1013] | 0.1221 | 0.931 | 0.00833 | No |
| CARDIAC_MYOSIN | 15 | 0.0004 | 0.0254 [0.0232, 0.0276] | 0.0642 | 0.966 | 0.00833 | No |
| CARDIAC_MYOSIN | 20 | 0.0003 | 0.0282 [0.0259, 0.0304] | 0.0606 | 0.962 | 0.00833 | No |
| PTP1B | 5 | 0.2266 | 0.3373 [0.3308, 0.3439] | 0.3897 | 0.704 | 0.003125 | No |
| **PTP1B** | **10** | **0.0003** | **0.0027 [0.0020, 0.0035]** | **0.0160** | **1.000** | **0.003125** | **Yes** |
| PTP1B | 15 | 0.0016 | 0.0238 [0.0217, 0.0260] | 0.0497 | 0.955 | 0.003125 | No |
| PTP1B | 20 | 0.0012 | 0.0279 [0.0257, 0.0302] | 0.0695 | 0.955 | 0.003125 | No |

**CARDIAC_MYOSIN's own verdict is unchanged and decisive**: min p (0.0254,
k=15) sits 3× above its own bar — TASK-0190's own "does not survive"
conclusion holds, now measured against a null that genuinely reaches this
target's real pocket Rg rather than one that could not.

**PTP1B's `dcc_low` (k=10) survives its pre-registered bar under this
null: p=0.0027 < 0.003125.** **[SEED-PROVENANCE ADVISORY, [[TASK-0216]], 2026-08-13: PTP1B's active site — this observable's own `source` argument — is NOT a real active site. `targets.yaml` declared `func_ligand: ['pTyr / active-site Cys215 (descriptive marker, not a ligand code)']`; no ligand matched, and `functional_indices` silently returned the 5 highest-degree residues. The p-value stands (the null shuffles pocket labels, not the seed) but the mechanistic reading — coupling from the catalytic site — is not what was measured. Under the real UniProt catalytic site (Cys215 + P-loop, seed overlap 1 residue of 9) the whole-graph `dcc_low` AUC moves −0.133. TASK-0201's own stratified statistic has NOT yet been recomputed under the corrected seed; that is the outstanding measurement.]** Read exactly, honestly, without overclaiming:
the point estimate clears the bar by TASK-0190's own stated criterion
(`p < bar`, the same comparison that task used throughout), but the 95%
Monte Carlo CI ([0.0020, 0.0035]) slightly straddles it — the upper CI
bound (0.0035) sits just above 0.003125. This is not a clean, CI-decisive
win; it is a real, reproducible point-estimate survival with residual
Monte Carlo uncertainty at the boundary, reported as such. `real_auc=1.000`
at k=10 independently matches [[TASK-0151]]'s own already-published
"well-powered max AUC 1.000 at k=10" number for this exact cell — not a
new or different effect, the same extremely strong separation this project
has measured multiple times, now surviving a correctly-specified null for
the first time.

**Mechanism, stated not just observed**: a genuinely-dispersed null does
not automatically make every cell's p-value larger. `dcc_low` (low-mode
dynamic cross-correlation) plausibly scores tight, spatially compact
patches systematically higher than topologically-elongated ones of the
same size, independent of location — if so, a null drawn from more
branching/dispersed shapes (even though Rg-matched to the real, more-
dispersed pocket) produces a *lower* null-score distribution than
`compact_patch`'s own tight balls, making the real (compact) high-scoring
pocket look *more* extreme relative to it, not less. This is consistent
with, not contradicted by, the ordering check (`p_matched` sits between
`p_scattered` and `p_compact` in *strictness*-of-null terms, not
necessarily in resulting p-value magnitude for every possible score field)
— reported as a plausible mechanism, not independently verified further
here (out of this task's own scope).

### Does TASK-0190's own reasoning hold up, or was it wrong? (this task's own required question, answered directly)

**Partially wrong, on the one cell that mattered.** TASK-0190 argued: *"A
null that could actually reach `target_rg`... could only make the null
more lenient still, not less — so this result is not overturned by fixing
the centring defect."* That reasoning held for CARDIAC_MYOSIN (still fails,
by a wide margin) but not for PTP1B (now survives). The flaw in the
original reasoning: "more dispersed" and "more lenient for this specific
score field" are not the same property — TASK-0190 assumed leniency tracks
dispersion monotonically for any observable, which is false for `dcc_low`
specifically, per the mechanism above. **TASK-0190's own pre-registered
reading rule now applies literally**: *"If exactly one [cell] survives,
§5.3's statement, read literally, does NOT fire — the honest report in
that case is a mixed result... not smoothed into either 'complete negative'
or 'the program has a positive.'"* Per that rule, fixed and pre-registered
by TASK-0190 itself before any of these numbers existed: **the program's
`dcc_low` family is now a mixed result (CARDIAC_MYOSIN falsified, PTP1B
survives), not the complete negative TASK-0190 and [[TASK-0161]]/
[[TASK-0191]]'s "zero confirmed positives program-wide" headline currently
state.**

**This is flagged, not resolved, here** — deciding how PTP1B's survival
should be framed for [[TASK-0184]]'s submission narrative (a genuine
positive result, single-target, CI-boundary-adjacent, under a null built
specifically because the prior one couldn't reach this test) is a
narrative/scope decision for that task's own owner, not this
null-construction fix. What this task owes, and delivers: the corrected
number, checked every way this project's own established discipline
requires (ordering check, replicate-count convergence, independent AUC
cross-reference, CI reported not hidden), handed off cleanly.

### Additive changes

`nulls.graph_walk_patch`/`nulls.graph_walk_patch_matched`/`nulls.
build_adjacency` (new, ADD-only — every existing `nulls.py` function
unchanged). 24 new tests (`tests/test_nulls.py::TestGraphWalkPatch`/
`TestGraphWalkPatchMatched`). Full suite:
`.venv/bin/python3 -m pytest -q tests/` — 1122 passed, 1 skipped, 2 xfailed,
no regressions.

Full detail: `.ai/tasks/DONE/TASK-0190-real-pocket-rg-matched-null.md`,
`.ai/tasks/IN_PROGRESS/TASK-0201-rg-reaching-compact-null-construction.md`,
`results/tasks/0201_graph_walk_matched_null/results.json`,
`scripts/graph_walk_matched_null_rerun.py`.

---

## ENM-induced connectivity-graph shortcut hypothesis — a clean negative on specificity (TASK-0187, 2026-08-01)

**Question**: does undirected ENM ("wobbling") conformational sampling create
new contact-graph edges that shorten the active-site<->pocket hop-distance
below its static-apo value, *specifically* to the real pocket rather than
generically across the whole graph — reframing propagation observables as
walking a dynamically rewiring graph rather than a static one, per the
orchestrating user's own conceptual request (2026-07-31)? Deliberately
undirected (no MD, no target, no direction — same closed-form-equipartition
legality argument as [[TASK-0185]]) and topology-focused (contact-graph
edges, not cavity/volume), to stay clear of [[TASK-0015]]'s directed
deformation and [[TASK-0185]]'s cavity-search territory.

**Positive-control target**: PTP1B, selected from [[TASK-0186]]'s own
numbers — the only one of 7 pocket-scoreable targets with static-apo min
spatial-hop = 2 and 0% of pocket at hop<=1 (median hop 3.5), the most room
for a dynamic shortcut to matter and the lowest static fold-compression
ratio (8.9x) of the set.

**Method**: new `allostery.shortcuts` module. Step 1 — 2000 closed-form
equipartition Gaussian draws in ANM mode space (amplitude_k ~
N(0, sqrt(kT/lambda_k)), kT=20, 20 softest non-rigid-body modes, same
method as [[TASK-0185]]'s reference prototype), reusing
`superpose.anm_modes` (already-confirmed 3N x 3N ANM Hessian) rather than
re-deriving. **Blocking MSF cross-check, run before any downstream step**
(this task's own Constraint — the reference prototype has no such check):
empirical per-residue MSF over the 2000-sample ensemble vs. the analytic
`kT * sum_k ||v_ik||^2 / lambda_k` prediction — Pearson r=0.9998, median
relative error 1.26%, decisively passing the pre-registered gate
(r>=0.90, rel. error<=25%). Step 2 — per-sample hop-distance
recomputation on the real pocket via `baselines.hop_from_seed`, same
8.0 Å contact convention as [[TASK-0067]]/[[TASK-0186]], no new geometric
constant invented. Step 3 — the pre-registered specificity test (fixed in
the task file *before* this step ran): 30 matched decoys via
`plant.select_distal_patch` ([[TASK-0167.001]], same size, genuinely
distal, floor-blind), PASS requires both (a) real-pocket shortcut rate
above the 95th percentile of the 30 decoy rates, and (b) the gap above the
decoy median >= 10 percentage points (added specifically so a large-N
significant-but-trivial gap could not pass alone). Step 4 — real
holo-native contact-graph hop-distance via `_holo_native_labels`
([[TASK-0067]]), for context.

**Result: a clean, decisive negative — real pocket shortcuts *less* than
generic distal decoys, not more.** Real-pocket shortcut rate 1.7% (34/2000
samples) vs. decoy rates ranging 0%-52.5% (median 12.9%, 95th percentile
51.9%) across the 30 matched decoys — real pocket sits below the decoy
*median*, not just short of the 95th-percentile significance bar.
Effect size (real - decoy median) = **-0.112**, the wrong sign entirely;
both the significance leg and the material-effect-size leg of the
pre-registered gate fail. Static apo hop = 2 (matches [[TASK-0186]]
exactly, a direct cross-script sanity check); the real holo-native
contact graph's own active-site<->pocket hop is also 2 (Step 4) — the
real deposited holo structure does not show this particular pocket
having collapsed to hop 1 either, consistent with the dynamic-shortcut
hypothesis not finding purchase here. Full run: 16.2s wall-clock (fast —
no long-job handling needed), `results/tasks/0187_shortcut_hypothesis/results.json`.

**Reading**: for PTP1B specifically, Cα-level undirected ENM wobbling does
not produce a pocket-specific contact-graph shortcut — whatever residual
noise-level shortening the contact graph shows under sampling (the ~13%
median decoy rate is itself non-trivial, worth separate note) is not
concentrated on the real allosteric site any more than on a matched
generic distal patch. Per the task's own pre-registered TODO ordering,
**not extended to CARDIAC_MYOSIN or the remaining targets** — the gate for
doing so ("positive control clears its gate") was not met. Per this
project's own culture (TASK-0185's own backbone-layer negative, TASK-0143's
graph-openness FAIL), this is reported as a legitimate negative, not
softened: if a cryptic-pocket-relevant dynamic effect exists here, this
result's own Open Questions (below) suggest it more plausibly lives at
the side-chain layer a backbone-only Cα ENM cannot reach, matching
[[TASK-0185]]'s own suspicion about its parallel cavity-opening question.

**Open items, not resolved here**: (1) whether the same negative
replicates on CARDIAC_MYOSIN (the secondary candidate TASK-0186 named) —
untested, since the gate closed on PTP1B; (2) whether a side-chain-layer
model (unreachable by Cα ENM) would show a different result, the same
open question TASK-0185's own filing already flagged for its parallel
cavity-opening hypothesis — a shared failure mode across two
forward-proposal tasks, worth a single cross-reference in [[TASK-0184]]'s
narrative rather than repeating in each task's own Done section.

Full detail: `.ai/tasks/DONE/TASK-0187-enm-connectivity-shortcut-hypothesis.md`
(Done section), `__WORK_IN_PROGRESS__/src/allostery/shortcuts.py`,
`__WORK_IN_PROGRESS__/scripts/shortcut_hypothesis_measurement.py`,
`__WORK_IN_PROGRESS__/tests/test_shortcuts.py`.

---

## Consensus holo-pocket ground truth (TASK-0177, 2026-08-02)

**Question**: the pocket label every AUC/floor/CI/null in this project's
226-cell register is computed against (`labels.holo_pocket_mask`, one HET
group, one 4.5 Å contact cutoff) has itself never been validated — only
swept once ([[TASK-0114]], "a still-moving slope, not a stable plateau")
and shown, on 2/3 mandatory targets, to not measure what it claims
([[TASK-0169]]: KRAS_G12C's pocket is 3.75 Å — 1 spatial hop — from the
active site; BCR_ABL1's pocket moves *less* than background, i.e.
pre-formed, not cryptic). Does a **consensus** across mutually independent
routes to the same residue set converge, and what is the honest
uncertainty on the answer?

**Method**: new `allostery.consensus_labels` module, four per-residue
criteria plus two target-level qualifiers, all mapped onto apo numbering
through the same `_needleman_wunsch_map`/`chain_map_from_config`
([[TASK-0144]]) path C1 already used, with `active_site`/`terminal`
excluded from every criterion before assembly (same SEAM-0003 invariant
`labels.build_labels` already enforces):

- **C1** ligand heavy-atom contact, swept 3.5–6.0 Å (union across cutoffs) — the incumbent, generalized.
- **C2** ΔSASA on ligand removal (`freesasa`, hand-checked: KRAS_G12C Cys12 buries 41.2 Å², His95 67.5 Å² — real, not noise). **Real bug caught before trusting any number**: `freesasa.Structure`'s default options silently ignore HETATM records, so the ligand's own atoms were never in the "with-ligand" SASA calc either way — `with`/`without` came back byte-identical until `options={"hetatm": True}` was set.
- **C3** geometric cavity in holo with the ligand stripped (vendored `fpocket`, TASK-0163's binary — rebuilt from source for this session's arm64 macOS host, `ARCH=MACOSXARM64`, the repo's own `makefile` ships a matching but never-wired plugin dir; the checked-in Linux static archive doesn't link on this platform). The correct cavity is identified post-stripping by proximity of its member residues to the (unstripped) ligand's own coordinates.
- **C4** depositor/software SITE records (legacy-PDB `REMARK 800`/`SITE`, auto-generated at deposition — independent of every computation this module does itself, since it reuses someone else's already-computed answer). **Unavailable on 2/7 targets** (CARDIAC_MYOSIN/8QYR, GLUCOKINASE/3H1V — no SITE records in either entry), reported as unavailable, not approximated.
- **C5** crypticity (target-level): apo vs. holo fpocket cavity volume ratio.
- **C6** distality (target-level): Euclidean + spatial contact-graph hop (8.0 Å, [[TASK-0067]]'s convention) to the active site, re-run against `core`/`consensus` alongside the incumbent label per [[TASK-0186]]'s own flagged follow-up.

**Consensus** = ≥3-of-{n criteria available} vote; **core** = all available
criteria agree; **shell** = consensus minus core; **resolution** =
`|shell|/|core|`. Unavailable criteria are excluded from both numerator and
denominator (a target with only 3 available criteria needs unanimous
agreement for *either* core or consensus — this is load-bearing, see the
negative-control finding below).

**Negative control** (Planned Validation's own hard requirement): re-ran the
full machinery with `drug_ligand` swapped to a real buffer/cryoprotectant
HET group confirmed present in the same holo entry (not invented — grepped
live against each target's actual ligand set). KRAS_G12C vs. `MG`: **passes**
cleanly (core=0, consensus=1/18 residues — no convergence). **CARDIAC_MYOSIN
vs. `EDO` (ethylene glycol): fails — core=consensus=7 residues, all 3
available criteria (C1/C2/C3) agree on a cryoprotectant.** Diagnosed, not
hand-waved: this is the direct consequence of C4 being structurally
unavailable for this entry — C1–C3 alone measure "is there a real
burial/contact/cavity here," which is true of *any* molecule sitting in a
real surface groove, cryoprotectant or drug. Only C4 (external annotation)
can distinguish "real binding site" from "crystallization artifact in a
pocket," and it doesn't exist for 8QYR. **Consequence stated explicitly**:
CARDIAC_MYOSIN's and GLUCOKINASE's `resolution=0.0` (core==consensus,
`shell` empty) is not evidence of strong agreement — it is the degenerate
unanimity-of-3 case the negative control just showed can converge on the
wrong answer. Flagged in `targets.yaml`'s own `pocket_label` block for both
targets, not silently shipped as a clean result.

**Per-target summary** (residue counts; `resolution` = |shell|/|core|):

| Target | incumbent (4.5 Å) | core | consensus | shell | resolution | C4 available? |
|---|---|---|---|---|---|---|
| KRAS_G12C | 18 | 3 | 15 | 12 | 4.00 | yes |
| BCR_ABL1 | 16 | 10 | 16 | 6 | 0.60 | yes |
| CARDIAC_MYOSIN | 13 | 15 | 15 | 0 | 0.00 | **no — see caveat** |
| PTP1B | 14 | 6 | 14 | 8 | 1.33 | yes |
| GLUCOKINASE | 17 | 17 | 17 | 0 | 0.00 | **no — see caveat** |
| CASPASE1 | 6 | 3 | 5 | 2 | 0.67 | yes |
| CASPASE7 | 7 | 3 | 6 | 3 | 1.00 | yes |

**Headline: convergence is real but partial, never total, and the two
"perfect" (`resolution=0.0`) results are the two targets whose negative
control cannot be trusted.** KRAS_G12C has the *worst* agreement (core is
only 3/18 of the incumbent set) despite being the most-scrutinized target in
the whole project — the four criteria genuinely disagree about most of its
labelled pocket. No target has an empty `core` (the "not verifiable"
outcome the Intent Contract explicitly allows for) — every target clears
the minimum bar, but usually with a real, now-quantified shell.

**C5/C6 target-level qualifiers**: crypticity ratios (apo cavity vol / holo
cavity vol) are 0.45–2.01 across all 7 targets — every target has *some*
apo-side cavity overlapping the mapped pocket (no target is "fully cryptic"
in this sense; PTP1B is the most cryptic, ratio 0.45, consistent with it
being the one target with real headroom, see below). C6 distality against
`consensus` reproduces [[TASK-0186]]'s own incumbent-label numbers closely
(min spatial-hop = 1 on 6/7 targets, PTP1B the sole exception at min hop 2 —
the two independent runs agree to the residue): the "trivially close"
finding is not an artifact of the old label.

**Re-scoring the headline observable** (`build_H_new` + `time_averaged_ctqw_converged`,
[[TASK-0130]]/[[TASK-0159]]'s shipped convention, `coherent=False`) against
all three labels side by side, **never substituting** — sanity-checked first:
KRAS_G12C's incumbent-label AUC reproduces TASK-0159's published 0.5901
exactly.

| Target | floor (vs. incumbent) | AUC incumbent | AUC core | AUC consensus | verdict flip? |
|---|---|---|---|---|---|
| KRAS_G12C | 0.482 | 0.590 | 0.307 | 0.562 | **yes** — clears floor on incumbent/consensus, falls *below* floor on core |
| BCR_ABL1 | 0.582 | 0.527 | **0.580** | 0.527 | **yes** — core clears the floor (barely), incumbent/consensus don't |
| CARDIAC_MYOSIN | 0.568 | 0.518 | 0.489 | 0.489 | no (all three miss) |
| PTP1B | 0.485 | 0.486 | **0.562** | 0.486 | **yes** — core clears, incumbent/consensus sit at the floor |
| GLUCOKINASE | 0.853 | 0.649 | 0.657 | 0.657 | no (all three miss, large margin) |
| CASPASE1 | 0.907 | 0.663 | 0.525 | 0.598 | no (all three miss, large margin) |
| CASPASE7 | 0.754 | 0.594 | **0.753** | 0.620 | **yes** — core clears the floor, incumbent/consensus don't |

**The flip itself is the finding, per this task's own Intent Contract.**
4/7 targets change floor-clearing verdict depending on which of the three
labels scores them — on 3 of those 4 (BCR_ABL1, PTP1B, CASPASE7) it is the
small, high-confidence `core` set that clears the floor while the larger
incumbent/consensus sets do not, the opposite of "more label agreement is
always better for the observable." No target's overall competence-map
status (none currently clear their floor decisively, per [[TASK-0129]]/
[[TASK-0131]]) changes sign here — this is a resolution/framing result, not
a new positive claim, per this task's own Out-Of-Scope constraint (no
observable/floor/null/CI logic touched).

**Recommendation on the Open Question** (which label is headline): **not
adopted here** — this task reports all three, per its own "never
substitute" constraint, and leaves the choice to [[TASK-0176]]/[[TASK-0184]]'s
narrative decision, now with the flip table above as direct evidence for
that decision rather than an assumption.

Frozen into `config/targets.yaml`'s new `pocket_label` block per target
(`core`/`consensus`/`shell`/`incumbent_4_5A`, all as `[chain, resnum]`
pairs — generated programmatically by
`scripts/task0177_consensus_labels.py`, never hand-transcribed, per this
project's hard rule). Full detail: `allostery/consensus_labels.py`,
`scripts/task0177_consensus_labels.py`,
`results/tasks/0177_consensus_labels/results.json`.

---

## Conformational-search reformulation — one real-data measurement, mixed result (TASK-0185, 2026-08-02)

**Reformulation**: cryptic-pocket prediction reframed from *residue
scoring on a static apo structure* to *search over an ENM-generated
conformational ensemble for structures in which the pocket forms* —
inverting [[TASK-0163]]'s fpocket result from competitor to oracle
("search for the conformation where fpocket fires," not "out-score
fpocket on apo"). Legal under §Constraint 3 (closed-form ANM-mode
Gaussian draws, no integrator, no trajectory — same argument as
[[TASK-0187]]). Full write-up:
`__WORK_IN_PROGRESS__/documentation/CONFORMATIONAL_SEARCH.md`.

**The one real-data measurement** (this task's own Intent Contract,
"not a build"): 100-sample closed-form ANM ensembles (n_modes=20, kT=20,
8.0 Å cutoff) run through the already-vendored fpocket
(`tools/fpocket/bin/fpocket`, [[TASK-0163]]) via a new rigid
per-residue Cα-driven full-atom displacement (stated approximation:
bond lengths/side-chain conformation held fixed, only rigid-body
position moves), on all 3 mandatory targets. MSF cross-check ([[TASK-0187]]'s
gate, reused) passed cleanly on all 3 (r=0.993-1.000). 0 fpocket errors
across 300 samples.

**Positive control (BCR_ABL1, run first per this task's own Planned
Validation) passes convincingly**: static apo alone covers 87.5% of the
real pocket via fpocket; ensemble real-pocket hit rate 80.0% — the
procedure clearly finds an already-open pocket at high frequency,
validating the method before trusting anything else.

**Real-vs-decoy hit rate (>=50% overlap with a single detected fpocket
cavity, matched-size distal decoy via `plant.select_distal_patch`,
[[TASK-0167.001]]), honestly mixed across the 3 mandatory targets:**

| Target | real hit rate | decoy hit rate | reading |
|---|---|---|---|
| BCR_ABL1 | 0.800 | 0.510 | specific, gap 0.29 — but BCR_ABL1 is cavity-rich (37 detected pockets on the static structure alone), so the decoy rate is not small either |
| KRAS_G12C | 0.500 | 0.370 | modest specificity, gap 0.13 — matches this target's own known partial crypticity ([[TASK-0169]]) |
| CARDIAC_MYOSIN | 0.200 | 0.190 | **no specificity** — real and decoy indistinguishable at this sample size, a clean negative for this target |

**The rare-event/quantum-claim measurement — corroborates the original
synthetic-toy-model finding on real data.** n_modes sweep on BCR_ABL1
(N=60/point): real-pocket recovery stays high across the whole tested
range (n_modes=5: 0.983, 20: 0.800, 40: 0.783) — **pocket recovery is not
a rare event on real data either**, matching the synthetic two-lobe
toy model's own p=0.244-0.694 finding
(`conformational_search_prototype_REFERENCE.py`). This is fatal to a
Grover-style backbone-layer rare-event search claim on real targets, not
just the synthetic control: real-pocket recovery here costs on the order
of 1-8 classical draws per hit even on the weakest target, never
approaching a regime where amplitude amplification would matter. The
real-vs-decoy specificity gap is *not* monotonic in n_modes (0.583 / 0.290
/ 0.583 at n_modes=5/20/40) — reported as observed, not smoothed.

**Where the quantum claim moves, not resolved here**: to the side-chain
layer (discrete, NP-hard rotamer packing, Pierce & Winfree 2002) — the
full QUBO formulation (encoding, qubit count, falsification criteria) is
[[TASK-0181]] Phase B's own deliverable, in progress concurrently on
another thread as of this writing, deliberately not duplicated here to
avoid two diverging specs (per this task's own Intent Contract
instruction to cross-reference, not re-derive).

**Boundary recorded, not actioned**: this task's own filing recommends
[[TASK-0015]]/`HOLO_DIRECTION_MODULE.md` be re-scoped or closed since this
task subsumes its motivation (directed single-deformation prediction vs.
this task's undirected full-ensemble search) — not actioned here since
TASK-0015 is claimed elsewhere; flagged for [[TASK-0184]]'s narrative.

Full detail: `.ai/tasks/DONE/TASK-0185-conformational-search-reformulation.md`
(Done section), `documentation/CONFORMATIONAL_SEARCH.md`,
`scripts/conformational_search_measurement.py`,
`results/tasks/0185_conformational_search/results.json`.

---

## Binding-response coupling free energy (TASK-0178, 2026-08-02)

**Question**: every observable in this register has the shape "seed
somewhere, watch where amplitude goes" — a propagating signal. Allosteric
inhibition is not that; it is a *response* to a constraint (a ligand binds,
the accessible ensemble changes, the active site loses propensity). For a
Gaussian network `(1/2) x^T K x`, a ligand at site S is a set of added
cross-links `P_S`, and the coupling free energy between two sites is exact
and closed-form: `ddG(A,B) = F(K+P_A+P_B) - F(K+P_A) - F(K+P_B) + F(K)`,
`F(K) = (kT/2) ln pdet(K)`. **Classical**, not quantum — stated plainly,
per this task's own Open Question.

**Method**: new `allostery.response` (`ligand_stiffness`, `coupling_free_energy`,
`coupling_profile`, `active_site_rigidification`, `coupling_specificity`).
`coupling_profile` uses a matrix-determinant-lemma low-rank shortcut (two
base eigendecompositions instead of `2N`) — **derived and numerically
verified against brute force to <1e-10** (actual: ~4e-14) before use, per
the Constraint. `coupling_free_energy` independently reproduces the
external reference prototype's own real number
(`ddG(active,pocket)=-6.965844e-07` on its 249-node synthetic fold) to
1.6e-13 — validates the whole module against a second, independent
implementation, not just internal self-consistency.

**Four mandatory gates, all pass** (`tests/test_response.py`, 14 tests):
reciprocity (`|ddG(A,B)-ddG(B,A)|` exact to <1e-9 over 21 pairs, 3
topologies); zero-coupling (exactly 0 on a disconnected graph); an
independent entropy cross-check (`ddG` equals the negative of the
analogous double-difference of Gaussian differential entropy, to <1e-8 —
two routes, one number); and the low-rank-shortcut verification above.

**The dumbbell gate found a real, disclosed complication before it found
an answer.** Run first, literally, against [[TASK-0103]]'s own
`build_dumbbell_network` fixture (mandatory, per the Constraint): every
`|ddG|` value returned was within 1-2 orders of magnitude of pure
eigh/log-determinant numerical noise (~1e-12 to 1e-10), regardless of
`kappa` (checked 0.1-1000, no monotonic trend) — **not a code bug**
(independently confirmed via the reference-prototype match above), but a
real finding: that fixture's near-complete 12-node cliques leave a bound
site's added stiffness almost fully redundant with what's already there,
and its own negative-diagonal "well" convention (built for
`ground_state_relaxation`'s `exp(-Ht)` picture) makes `K` indefinite,
outside this module's valid domain. **Neither the pre-registered PASS nor
the pre-registered FAILURE** — a third, disclosed outcome. Resolved with a
geometrically realistic adaptation (the reference prototype's own
well-conditioned two-lobe/plant construction, extended to three lobes,
well modelled as a genuine positive-diagonal rigidification): **on this
fixture, the gate passes cleanly and decisively both ways** (C2: drug
ddG=0.79 vs decoy ddG=0.10; C3: decoy ddG=0.74 vs drug ddG=0.037) — tracks
the coupling, not the well.

**Real-target run, all 7 pocket-scoreable targets, GNM/Kirchhoff (`enm_cutoff`,
same convention as the rest of this register), κ=1.0.** Per the Constraint,
**`rho(score,-hop)` reported before any AUC**:

| Target | rho(raw \|ddG\|, -hop) | rho(specificity, -hop) |
|---|---|---|
| KRAS_G12C | +0.935 | +0.002 |
| BCR_ABL1 | +0.915 | +0.044 |
| CARDIAC_MYOSIN | +0.896 | +0.018 |
| PTP1B | +0.876 | -0.013 |
| GLUCOKINASE | +0.881 | +0.020 |
| CASPASE1 | +0.869 | +0.021 |
| CASPASE7 | +0.713 | -0.006 |

**The raw-magnitude confound is exactly as severe as feared** (+0.71 to
+0.94, matching the +0.61 to +0.97 range this project's other observables
already carry) — confirming raw `|ddG|` must never be reported as a
result, exactly per the Constraint. **The shell-normalisation decisively
removes it on every one of the 7 real targets** (all 7 within ±0.044 of
zero) — a materially *cleaner* real-data transfer than [[TASK-0149]]'s own
precedent (predicted 0.08-0.16, observed -0.51 to +0.63 on real data);
this task's own pre-registered decorrelation claim holds up better on real
data than the project's own most relevant prior case.

**AUC vs. floor, all three of [[TASK-0177]]'s labels, specificity vs. raw
(never substituted)**: no target/label cell decisively clears its own
floor. The one candidate worth naming honestly: PTP1B's `core` label
clears its floor at the point estimate (specificity AUC 0.699 vs. floor
0.618, +0.081) — checked further with a 300-replicate `compact_patch`
permutation null (matched patch size, not scattered): **p=0.132, not
significant even uncorrected**, let alone against the ~21-cell family this
task itself adds to [[TASK-0161]]'s multiplicity budget. No other cell
comes as close. Full table: `results/tasks/0178_response_coupling/results.json`.

**Kappa KNOB, characterised**: swept 0.1-10.0 on KRAS_G12C — `rho`
(+0.040 to +0.023) and AUC (0.396 to 0.363) both drift slightly but
monotonically, no verdict flip anywhere in the swept range ([[TASK-0075]]'s
own precedent for reporting this explicitly).

**Lightweight LOD probe** (explicitly narrower than [[TASK-0167.002]]'s
own full protocol — [[TASK-0167.002]] was Done four days before this
section was written, but its detection-curve/LOD machinery scores
synthetic planted patches, not this task's real per-target specificity
statistic; "narrower," not "duplicated" — one target, one observable, no
CI/null/Bonferroni chain, flagged as such, not presented as a certified
LOD):
reusing [[TASK-0167.001]]'s `plant`/`select_distal_patch` machinery on
real KRAS_G12C topology, the reference prototype's own strength grid,
5 seeds/strength. **A clean, monotonically increasing detection curve on
real protein data** (mean AUC 0.520 → 0.555 → 0.614 → 0.731 → 0.854 at
strengths 0/1.5/4/10/30) — crosses an informal 0.7 "detectable" bar
between strength 4 and 10, comparable to (slightly better than) the
reference prototype's own synthetic-fold estimate (detectable from
strength 1.5, a *different* fold/labelling so not directly comparable
strength-for-strength). Confirms the observable's sensitivity mechanism
transfers to real topology; a certified target/null/observable-matched LOD
vs. CTQW remains [[TASK-0167.002]]'s own deliverable, not duplicated here.

**Pre-registered falsification, resolved**: *"if `rho(score,-hop)` on real
targets stays above ~0.6, or the LOD is no better than CTQW's, this
observable class adds nothing."* **Neither condition holds** — `rho`
drops to ≈0 on every target (decisively below 0.6) and the LOD probe shows
real, monotonic sensitivity on real topology. This is not, however, a
positive result for allosteric detection on the current 7 targets: the
specificity statistic is real, well-behaved, and well-decorrelated from
distance, but no target/label cell shows a real (permutation-null-surviving)
positive once decorrelated. **Recorded as: methodologically validated and
adds a genuinely new, non-proximity-confounded statistic to the register;
tested honestly on real targets and found no exploitable signal there
(one point-estimate candidate, PTP1B/core, explicitly ruled out by its own
null).**

Full detail: `allostery/response.py`, `tests/test_response.py`,
`scripts/task0178_response_coupling.py`, `scripts/task0178_lod_probe.py`,
`results/tasks/0178_response_coupling/results.json`,
`results/tasks/0178_response_coupling/lod_probe_kras_g12c.json`.

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
| 40 | How many scored cells has this program actually run against real target labels, program-wide — and does the number of reported positives exceed what that testing volume alone would produce at α=0.05, per `PANEL_REVIEW_2026-07-25.md`'s own framing? | **resolved 2026-07-25: 226 real-target scored cells, confirming (and modestly exceeding) the review's own "~200+" estimate — expected false positives at α=0.05 ≈ 11.3.** Using [[TASK-0158]]'s corrected-null re-run (not the pre-correction numbers): **zero** confirmed, corrected-null-surviving positives program-wide. `dcc_low`, the one prior Bonferroni survivor, lost significance on both CARDIAC_MYOSIN and PTP1B under the compact-patch null. One cell remains genuinely unresolved rather than confirmed: [[TASK-0145]]'s BCR_ABL1 transport result uses a scattered null TASK-0158 found is *more* anti-conservative than the one that removed `dcc_low`'s significance, and was not itself re-run — treated as unconfirmed, not counted as a survivor. **The project has fewer positives than pure chance predicts, not merely "not clearly in excess of it."** Full enumeration table: this document's own "Program-level multiple-comparison budget" section above. **[[TASK-0191]] recount, 2026-08-03: 10 tasks landed real-target scored cells since this row's own 2026-07-25 freeze — new total 366 cells (140 new), expected false positives ≈18.3. Still zero confirmed positives — a stronger, not weaker, position. See that section's own "Recount" addendum, not this row, for the current number.** **[[TASK-0201]], 2026-08-04: "zero confirmed positives" no longer holds unqualified — a null that can genuinely reach real pocket Rg (the prior one structurally could not) makes PTP1B's `dcc_low` (k=10) survive its own pre-registered bar (p=0.0027 vs. 0.003125); CARDIAC_MYOSIN still fails. See this document's own "A null that can actually reach real pocket Rg" section.** | [[TASK-0161]], [[TASK-0158]], [[TASK-0149]], [[TASK-0151]], [[TASK-0145]], [[TASK-0191]], [[TASK-0201]] |
| 41 | Does the shipped `connectivity_matrix.npz` deliverable actually satisfy the challenge's own §5 "N×N quantum connectivity matrix" requirement — quantum-defined, all-pairs, and dense? | **resolved 2026-07-27: no (before this task) — classical, seeded, and sparse, failing on all 3 counts; now yes, additively.** New `propagators.quantum_connectivity_matrix` (`P_inf(i,j)=sum_k \|v_k(i)\|^2\|v_k(j)\|^2`, one `(N,N)@(N,N)` product from the same eigendecomposition `time_averaged_ctqw_converged` already needs — no second diagonalization). Exact symmetry and row-sum-to-1 both derived and confirmed numerically; real-data check on all 3 mandatory targets shows the new matrix at density 1.000 vs. the old matrix's 0.014-0.057 (falling as N grows) — a decisive, measured confirmation of the "not dense" fix specifically. **Design choice checked, not assumed**: the plain per-eigenvector formula (not TASK-0130's own degenerate-block-corrected form) matches `time_averaged_ctqw_converged`'s independently-computed single-source column to 1e-16 to 1e-17 (machine precision) on every mandatory target — real `H_new` spectra are near- not exactly-degenerate, so the simpler formula this task's own Intent Contract specifies is confirmed exact in practice, not merely assumed safe. Wired additively into both `run_target` and `run_target_no_ground_truth` as `quantum_connectivity_matrix.npz`, the pre-existing classical file untouched and still written. | [[TASK-0160]], [[TASK-0130]] |

| 42 | Does replacing `block_bootstrap_ci`'s sequence-index blocking with a spatially compact k-NN block — matching a real pocket's own geometry, `PANEL_REVIEW_2026-07-25.md` W6/V4 — widen CIs for currently-surviving/near-surviving positives, as the review's own text predicts? | **resolved 2026-07-27: the tool is built and validated correctly, but the real-data direction is mixed, not uniform widening — reported honestly.** New `metrics.spatial_block_bootstrap_ci` (k-NN block, drop-in signature). Regression checks pass: exact convergence to sequence-block behavior on a 1D-line synthetic control, and 1.4x–2.4x widening on a globule control once an accidental sequence/3D correlation in the naive fixture (a random-walk build order) was found and removed. **On real transport data (TASK-0145's BCR_ABL1 family plus KRAS_G12C/PTP1B's own `H_new` cells, [[TASK-0158]]'s own flagged near-survivors): 4/5 cells got *narrower*, not wider** (ratios 0.83–0.98; only KRAS_G12C widened, 1.27x) — plausibly because real secondary structure keeps genuine local sequence stretches spatially coherent too, unlike the idealized synthetic control. Practical bottom line unaffected: no cell anywhere in this project has ever had a non-overlapping CI (confirmed by direct grep before this task started), and every re-checked cell still overlaps its floor's CI under the corrected method — no verdict flips either direction. | [[TASK-0165]], [[TASK-0158]], [[TASK-0145]] |

| 43 | Does the ensemble-redistribution mechanism the challenge's own reference [4] (Motlagh & Hilser 2014) names — a cryptic pocket exists because the conformational *ensemble* contains states where it is open, not because a signal propagates there — show real allosteric signal at Cα/GNM resolution, and is it orthogonal to the proximity confound that dominates every directed-channel observable in this register (`PANEL_REVIEW_2026-07-25.md` §7.3(1)/V9)? | **resolved 2026-07-28: no on both counts, a clean and informative double negative.** New per-residue GNM low-mode conformational entropy (`0.5*ln(2*pi*e*sigma_i^2)`, sigma_i^2 the standard Bahar/Atilgan/Erman 1997 GNM MSF formula restricted to the lowest 20 modes — a textbook differential-entropy identity applied to an existing, already-validated quantity, not invented). Scored against all 7 pocket-scoreable `status: verified` targets (MYC_MAX excluded — no pocket label exists for this IDP target): zero of 7 cells survive Bonferroni correction (α/7=0.00714); GLUCOKINASE's p=0.035 is the closest near-miss. **More informative than the null result alone**: despite having no active-site seed and no propagation step at all, ρ(entropy, −hop-from-seed) is strongly positive on every target (0.39–0.76) — this observable does NOT evade the proximity confound the way [[TASK-0140]]'s chiral circulation (orthogonal by construction) or [[TASK-0149]]'s mode-filtered PRS/DCC do. Entropy is a strictly monotonic transform of the underlying low-mode variance, so this is, in ranking terms, a test of whether raw per-residue flexibility magnitude predicts the pocket — it does not, on this data. | [[TASK-0166]], [[TASK-0161]], [[TASK-0158]], [[TASK-0123]] |
| 44 | Does this project have any real external classical comparator beyond the single GNM transfer-entropy baseline ([[TASK-0132]]) — the challenge's own explicitly-scored "comparison to classical analogs" criterion (`PANEL_REVIEW_2026-07-25.md` §2.2/W7, §4 action item 6, V8) — given ~40 quantum-flavored observables have been run against 1? | **resolved 2026-07-28: fpocket run and decisively beats this project's own headline observable on 2/3 mandatory targets; PocketMiner run, mixed; ProteinLens blocked (browser-only, no API) and explicitly reported as such, not silently skipped.** Full detail: this document's own "External classical-pocket-detection baselines (fpocket, PocketMiner)" section below. | [[TASK-0163]], [[TASK-0132]] |
| 45 | Does allosteric coupling reciprocate — does seeding at the (holo-labeled) pocket and scoring into the active site (the direction real allosteric experiments actually measure) reproduce the forward-direction (active-site-seeded) signal every observable in this register has been scored on so far? | **resolved 2026-07-28: no, decisively — a real, target/observable-dependent asymmetry, not a reciprocal-channel picture.** 5 observables (`time_averaged_ctqw_converged`, `prs_low`/`dcc_low` at k=20, `R_eff`, `T(E=0)` on `H_new`) × 5 targets (3 mandatory + PTP1B/CASPASE7): forward clears its own proximity floor in 10/25 cells (40%), reverse in only 4/25 (16%), both directions in only 2/25 (8%). **The single starkest cell is this project's own strongest whole-graph result**: CARDIAC_MYOSIN `prs_low` forward AUC 0.836 collapses to reverse AUC 0.321 (anti-correlated, below its own floor). Background Spearman ρ (forward vs. reverse score vectors, residues outside both labeled sets) is mostly strongly positive (mean 0.61) — the asymmetry concentrates in the labeled sets specifically, the rest of the protein's own coupling structure is largely reciprocal even on cells with a large labeled-set AUC collapse. Forward numbers reproduce every already-published value exactly (an implicit consistency check); reverse is a new measurement, no prior verdict changes. A real scale effect on PTP1B/CASPASE7 (only 5 active-site residues each) elevates their own reverse floor to 0.90-0.91. | [[TASK-0162]], [[TASK-0130]], [[TASK-0149]], [[TASK-0145]], [[TASK-0094]] |
| 46 | Is the mandatory 3-target benchmark actually capable of certifying a working allosteric-site predictor, as distinct from a broken one — consolidating this project's own already-scattered benchmark-integrity findings into one explicit verdict? | **resolved 2026-07-28: no, on all 3 mandatory targets, on at least one of three axes each — re-verified directly against RCSB, not relayed.** KRAS_G12C: ground truth valid, but the pocket is 3.75 Å from the active site (re-measured directly) and fpocket (0.8348, purely geometric) decisively beats both the corrected floor (0.4818) and this project's own actual (0.5901) — fails "distal" and "non-trivial." BCR_ABL1: ground truth valid, but the pocket is measurably pre-formed in apo (RMSD ratio 0.49, [[TASK-0120]]/[[TASK-0139]]) and fpocket (0.8596) again crushes both floor and actual — fails "cryptic" and "non-trivial." CARDIAC_MYOSIN: the challenge's own named validation structure (6C1H) does **not** contain mavacamten (re-confirmed live: `nonpolymer_bound_components=['ADP','MG']` only) — this project's own substituted structure (8QYR) does — fails "ground truth valid" for the challenge's own literal Table 1 entry. **A stale number caught in the process**: the filing task's own "0.798" KRAS_G12C floor citation is TASK-0094's pre-[[TASK-0118]]/[[TASK-0121]]/[[TASK-0130]] number; the current, fully-corrected floor is 0.4818 — corrected here, not silently propagated. Constructive half: a 5-point specification for a benchmark that *could* certify a method (verified holo ligand content; verified-distal-and-cryptic pockets, not drug-contact proxies; a mandatory geometric-baseline floor per target; ≥1 mechanism-validated ground truth target ([[TASK-0170]]); a published detection limit ([[TASK-0167]])). Framed as measurement, not criticism, per this task's own Constraint. | [[TASK-0169]], [[TASK-0124]], [[TASK-0163]], [[TASK-0164]], [[TASK-0104]], [[TASK-0094]] |
| 47 | Does the apo structure's own low-frequency linear response reach the holo-defined pocket in *any* apo-only-admissible direction — the holo-direction module's own mandatory Step 2 go/no-go gate (`HOLO_DIRECTION_MODULE.md`), run before any Step 3-5 transport/optimization work is built? | **resolved 2026-07-28, corrected same day (user-flagged, two rounds — see this document's own "Holo-direction module Step 2 go/no-go gate" section's correction block for the full account): the original "direct active-site<->pocket edge" test was the wrong quantity (active site and pocket are distal by this project's own definition, so a direct-contact test can never fire regardless of the deformation) — fixed to a graph-hop shortcut test, then cutoff-swept {4.5, 6.0, 8.0, 10.0} Å after a second challenge on robustness. **Final: `shortcut_verdict_across_grid` = `NO_GO` on all 7 targets at every cutoff tested**, including PTP1B/BCR_ABL1, where a real 6-10 hop apo-side gap exists at the strictest cutoff — Step 1's own narrow admissible family (1-10 candidates/target) is too small to bridge even a moderate topological gap, not merely "there is no gap to bridge." No target's CO(10) clears the 0.5 overlap threshold either (max 0.4652, KRAS_G12C). The headline verdict (7/7 `NO_GO`) is unchanged by either correction. Per the spec's own explicit "build the rest only for the targets that clear it" instruction, Steps 3-5 are not built for any target. Two real bugs found+fixed while running this: `go_no_go_gate` initially hardcoded `chain_map=None` instead of `chain_map_from_config` (the TASK-0144 differing-apo/holo-chain-letter issue, broke 2 targets outright until fixed); CASPASE7's labeled pocket has zero holo correspondence in the alignment at all (CO genuinely undefined, reported as NaN not a misleading number, verdict conservatively defaults `NO_GO`). Independent, converging evidence for the same reframe [[TASK-0162]]'s forward/reverse asymmetry and [[TASK-0163]]'s fpocket result already raised. | [[TASK-0015]], [[TASK-0005]], [[TASK-0150]], [[TASK-0152]], [[TASK-0162]], [[TASK-0163]], [[TASK-0067]], [[TASK-0114]] |

| 48 | Does this project's verdict pipeline (floor → CI → permutation null → Bonferroni) actually detect a real, planted, confound-orthogonal allosteric coupling if one is present, and what is the limit of detection (LOD) in interpretable units? | **resolved 2026-07-28: yes, under the historical (scattered) null — LOD ≈2× background conductance on 2/3 targets; no, under the corrected (compact) null — no target reaches 80% power at any strength tested, up to ~4× background.** [[TASK-0167.001]]'s own decisive finding reconfirmed first: `H_new`/`dcc_low`/`prs_low` are exactly plant-invariant, so only `T(E=0)` on a weighted Laplacian could be swept. 3 targets × 8 strengths × 20 seeds × 3 nulls × 2 CI methods, unmodified pipeline, all gates in series. Both CI methods gave identical LODs (the external review's own spatial-CI 1D-line concern, verified real — 55% block overlap, not exact coincidence — did not change the bottom line; corrected in [[TASK-0165]]). Per-gate profile: gate 2 (CI non-overlap) and the permutation-null gate are BOTH independently binding at high strength, neither alone explains the corrected-null failure. Real non-monotonicity found on 2/3 targets (P(certified) peaks then falls at the highest strength), consistent with TASK-0167.001's own predicted channel-leakage mechanism. Compact and Rg-matched nulls proved empirically indistinguishable at this patch size (verified, not assumed). BCR_ABL1 never reaches 80% power under any null. A real Bonferroni-family bug (dividing by the synthetic replicate grid instead of by targets) was found and fixed in analysis, not in the already-expensive collection run. | [[TASK-0167]], [[TASK-0167.001]], [[TASK-0158]], [[TASK-0165]], [[TASK-0145]], [[TASK-0161]] |
| 49 | Is KRAS_G12C's floor-clearing result (this project's one target with a marginal surviving signal) robust to the choice of apo structural draw, or a lucky draw — and is the apo structure it has always been drawn from even the correct genotype (`REVIEW-panel-2026-07-28-external.md` §2/§5C)? | **resolved 2026-07-30: a lucky draw, decisively, AND drawn from the wrong genotype.** `targets.yaml`'s current `apo_pdb: 4OBE` is confirmed wild-type (Gly12), not G12C — RCSB's own title ("GDP-bound Human KRas") and its own `pdbx_database_related` field (cross-referencing true G12C entries as merely *related to* it) both independently confirm this; every prior KRAS_G12C number in this project was computed against the wrong mutant. Swept 10 independently RCSB-verified true-G12C, GDP+Mg-only, X-ray apo structures (1.04–2.41 Å) through the unmodified pipeline, holo/cutoffs/seed fixed: AUC ranges 0.408–0.595 (spread 0.187, matching [[TASK-0124]]'s own 0.27 CARDIAC_MYOSIN swing), median 0.482 (below chance), only 3/10 (30%) floor-clear, and P@5 is exactly 0.000 on all 10 (vs. the mislabeled 4OBE's own 0.200). The number this project has always reported sits at the high end of a distribution centered on chance, drawn from a structure that is not even the target's own claimed mutant. | [[TASK-0155]], [[TASK-0124]], [[TASK-0094]] |
| 50 | Is two-boson Hong-Ou-Mandel path interference (the one genuinely non-reducible multi-particle residual left in this program's search space) worth building before the 2026-08-08 writing freeze, per `PANEL_REVIEW_2026-07-25.md`'s own later deprioritization instruction? | **resolved 2026-08-02: filed, not built, per the review's own explicit instruction.** Precondition Gate satisfied first: the non-reducibility argument is real (the HOM cross-term depends on relative phase, information [[TASK-0130]]'s converged-limit observable provably discards, per [[TASK-0146]]). 3 governing citations independently re-verified (Valiant 1979; Terhal & DiVincenzo 2002; Aaronson & Arkhipov 2011). Honest ceiling: a 2×2 permanent equals a 2×2 determinant in cost — even a clean positive at k=2 would be a better observable, not a demonstrated quantum advantage. Filed as a forward-proposal note, `EXECUTION_PLAN.md`'s Phase 1E. | [[TASK-0157]], [[TASK-0130]], [[TASK-0146]] |
| 51 | Does [[TASK-0162]]'s forward/reverse coupling asymmetry — computed on apo topology throughout — reproduce when the identical 5-observable x 5-target comparison is re-run holo-native end-to-end, matching [[TASK-0067]]'s own established apo-vs-holo diagnostic precedent for a different observable family? | **resolved 2026-08-02: no — a real, materially different result from TASK-0067's own "tiny gap" precedent, not a reproduction.** Forward floor-clear drops from 10/25 (apo, matches TASK-0162 exactly) to 6/25 (holo), with 10/25 individual cells flipping verdict; reverse floor-clear stays 4/25 in aggregate but only 2/25 cells overlap. Mean |apo-vs-holo gap| (0.133 forward / 0.119 reverse) is an order of magnitude larger than TASK-0067's own bare-operator gap (0.081/0.061) — concentrated in `T_E0_Hnew` (transmission on `H_new`, up to -0.40) and `dcc_low` (up to -0.41), extending [[TASK-0153]]'s own already-flagged `dcc_low` apo/holo complication rather than contradicting it. `ctqw_converged`/`R_eff`/`prs_low` stay closer to TASK-0067's "small gap" pattern on most cells but not all (KRAS_G12C's `ctqw_converged` forward verdict itself flips). Diagnostic only, per TASK-0067's own caveat, never a submission-path result. | [[TASK-0171]], [[TASK-0162]], [[TASK-0067]], [[TASK-0153]], [[TASK-0169]] |

**Recovery note, 2026-08-03 (Architect).** Rows 52-59 below, plus the
cross-reference note that follows them, were lost from this document
between commit `f5430de` (TASK-0182) and `38a22f5` (TASK-0171) — a real
concurrent-edit collision, not a hypothetical one: two independent lines of
work both inserted at row 51 (TASK-0182's hardware-feasibility question and
TASK-0185's conformational-search question), and a later sequence of
commits from a separate machine, based on an older snapshot of this file,
overwrote all of rows 47-53 plus the note when applied. **The underlying
science was never lost** — every task file in `.ai/tasks/DONE/` (TASK-0177/
0178/0181/0182/0185/0186/0187/0188) has its own complete Done section
independent of this document — only this synthesis document's copy of the
open-questions index was affected. Reconstructed verbatim from `git show
f5430de:__WORK_IN_PROGRESS__/RESULTS.md`, renumbered 52-59 to continue
after the current row 51 rather than re-collide, with only the internal
row-number cross-references corrected to match (row *content* otherwise
character-for-character identical to what shipped in `f5430de`). Filed
alongside a fix to `.ai/tasks/DONE/TASK-0182-hardware-realization-and-resource-accounting.md`'s
own citation, which pointed at "row 51" — true when written, invalidated by
the same collision.

| 52 | Does TASK-0169's KRAS_G12C finding ("labelled pocket 3.75 Å / 1 spatial hop from the active site — trivial") generalize across the benchmark set, and does spatial contact-graph closeness track primary-sequence closeness or diverge from it? | **resolved 2026-07-31/2026-08-01: generalizes partially and unevenly — not a clean "everything is a hoax," not a clean negative either.** All 7 pocket-scoreable `status: verified` targets have **min spatial-hop = 1** except PTP1B (min 2) — every target except PTP1B has at least one pocket residue that is a direct contact-graph neighbour of the active site, on the same 8.0 Å convention as [[TASK-0067]]. But the *fraction* of the pocket that is trivially close varies enormously: CASPASE1 is the worst case found (median hop 1.0, 83% of its pocket at hop ≤1 — more trivial than KRAS_G12C itself); KRAS_G12C is next (39% at hop ≤1, median 2.0); BCR_ABL1/GLUCOKINASE/CASPASE7 sit in between (6–14% at hop ≤1, median 2.0); CARDIAC_MYOSIN and **PTP1B are the genuinely non-trivial cases** (PTP1B: 0% of its pocket at hop ≤1, median 3.5; CARDIAC_MYOSIN: 8% at hop ≤1, median 4.0). Euclidean distance and spatial hop-distance broadly agree in rank but not in scale (KRAS_G12C's min Euclidean 3.75 Å independently reproduces TASK-0169's own published number to 5 decimal places, confirming the new script's correctness). **Primary-sequence (chain) hop-distance is a completely different picture on every target** — chain-hop medians run 22–181 residues even where spatial-hop is 1–2, and the fold-compression ratio (chain-hop / spatial-hop) is large everywhere (mean 8.9–37.7×, all 7 targets) — the native fold, with no ENM dynamics involved at all, already collapses tens to hundreds of sequence positions into 1–4 contact-graph hops. **Caveat carried forward, not resolved here**: every number above is scored against the *incumbent* 4.5 Å ligand-contact label, which [[TASK-0114]] already showed sits on "a still-moving slope, not a stable plateau" at the residue level — must be re-run against [[TASK-0177]]'s consensus/core label once it lands, all three reported side by side, before this finding is treated as final. | [[TASK-0186]], [[TASK-0169]], [[TASK-0067]], [[TASK-0114]], [[TASK-0177]] |
| 53 | Is TASK-0186's (row 52) spatial-hop finding stable across the contact-graph cutoff, or is it a knob-choice artifact of an 8.0 Å value that was only ever benchmarked (TASK-0067) for a different metric (GNM-eigendecomposition AUC, over 7.5/8.0/10.0 Å) and never for hop-count? | **resolved 2026-08-01: mixed — one headline claim is cutoff-fragile, two are robust.** Swept all 7 pocket-scoreable targets over {6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0} Å. Connectivity holds everywhere (single component, zero isolated nodes, all 7 targets including CARDIAC_MYOSIN N=704 — the low-cutoff fragmentation risk did not materialize in the tested range); the 8.0 Å row of this sweep reproduces row 52's published numbers exactly on all 7 targets (min/mean/median/max/frac≤1/frac≤2, bit-for-bit), confirming both scripts share the same code path. **Not robust:** the "6/7 targets have min spatial-hop = 1" claim only holds at cutoff ≥ 8.0 Å — BCR_ABL1's min hop is 2 (not 1) at every tested cutoff ≤ 7.5 Å, so below 8.0 Å the finding is 5/7, not 6/7. **Not robust (magnitude, but ranking survives):** CASPASE1's specific "83% at hop ≤1" number is a cutoff artifact of the ≥7.5 Å region — it drops to 50% at 6.0 Å and 67% at 6.5–7.0 Å; however CASPASE1 remains the single most-trivial target (highest frac≤1) at every tested cutoff, so the qualitative ranking ("CASPASE1 more trivial than KRAS_G12C") is robust even though the point estimate is not. **Robust:** PTP1B's "0% at hop ≤1" is exactly 0.0 at all 7 tested cutoffs — the strongest non-trivial-target claim in row 52 is also the one that survives the sweep intact. Practical read: report row 52's per-cutoff-dependent numbers (the 6/7 count, CASPASE1's 83%) as `cutoff=8.0Å`-conditional, not as target-intrinsic; PTP1B's non-triviality and CASPASE1's relative-worst-case ranking can be stated unconditionally. | [[TASK-0188]], [[TASK-0186]], [[TASK-0067]], [[TASK-0114]] |
| 54 | Does undirected ENM ("wobbling") conformational sampling create new contact-graph edges that shorten the active-site<->pocket hop-distance *specifically* to the real pocket (not generically, [[TASK-0186]]/row 52's static baseline as the pre-ENM comparison point), and does any such shortening approach the real holo topology's own hop-distance? | **resolved 2026-08-01: no — a clean, decisive negative on the positive-control target.** PTP1B (TASK-0186's only genuinely non-trivial case, min static hop=2, 0% pocket at hop<=1): real-pocket shortcut rate 1.7% over 2000 ANM-equipartition samples (MSF cross-check r=0.9998, passed) vs. 30 matched decoys ranging 0-52.5% (median 12.9%) — real pocket sits *below* the decoy median, effect size -0.112 (wrong sign), fails both legs of the pre-registered specificity gate. Holo-native contact graph's own hop-distance for this pocket is also 2, unchanged from static apo. Not extended past the positive control per the task's own pre-registered gate. | [[TASK-0187]], [[TASK-0186]], [[TASK-0185]], [[TASK-0167.001]], [[TASK-0067]] |
| 55 | Does the incumbent 4.5 Å ligand-contact pocket label converge with independent structural-biology routes to the same residue set (contact-cutoff sweep, ΔSASA burial, ligand-stripped cavity detection, depositor SITE annotation), and does the headline observable's floor-clearing verdict depend on which convergent label is used? | **resolved 2026-08-02: convergence is real but partial on every target (no empty `core`), and 4/7 targets flip floor-clearing status depending on label choice — the flip is the finding, per this task's own Intent Contract.** New `allostery.consensus_labels` (C1 contact sweep 3.5-6.0Å / C2 ΔSASA / C3 fpocket-on-stripped-holo / C4 depositor SITE records), run on all 7 pocket-scoreable targets. KRAS_G12C has the *worst* agreement of any target (core=3/18) despite being the most-scrutinized in the project. **Negative control real finding**: CARDIAC_MYOSIN's consensus procedure converges on `EDO` (a cryoprotectant, not a drug) — root-caused to C4 (the only criterion independent of "is there a real cavity/burial here") being structurally unavailable for that entry (8QYR has no legacy SITE records), which also explains why CARDIAC_MYOSIN/GLUCOKINASE are the only two targets with `resolution=0.0` — a degenerate unanimity-of-3 artifact, not strong evidence, flagged in `targets.yaml` itself. Re-scoring `H_new`+`time_averaged_ctqw_converged` against incumbent/core/consensus side by side (sanity-checked: KRAS_G12C incumbent AUC reproduces TASK-0159's published 0.5901 exactly) flips floor-clearing verdicts on BCR_ABL1/PTP1B/CASPASE7 (small high-confidence `core` clears where the larger sets don't) and KRAS_G12C (incumbent/consensus clear, `core` falls below floor) — no target's overall competence-map status changes sign. Frozen into `targets.yaml`'s new `pocket_label` block, generated programmatically, never hand-transcribed. | [[TASK-0176]], [[TASK-0114]], [[TASK-0169]], [[TASK-0163]], [[TASK-0144]], [[TASK-0186]], [[TASK-0130]], [[TASK-0159]] |
| 56 | Per §Feasibility/§Technical-Approach and §Constraint 2 ("deep, unoptimized circuits ... will be penalized"): what is the real per-target qubit/gate/depth resource cost, is TASK-0068's NISQ noise-robustness finding still valid under the corrected (TASK-0130 converged) propagation convention, and what is an honest near-term feasibility verdict per target? | **resolved 2026-08-02: worse than the task's own pre-stated "honest expected answer" — not just full resolution but even NISQ-plausible coarse-graining fails a real feasibility bar, and the phase-free-robustness hypothesis does not hold cleanly.** Ran on the 3 mandatory targets + MYC_MAX. **Convergence check (blocking, run first):** a fixed-depth circuit cannot realize `time_averaged_ctqw_converged`'s literal t→∞ average — approximated via `noise.time_sampled_converged_occupation` (new, tested function: sample several `t`, average occupations), validated against the exact closed form. Residual is real and non-negligible at NISQ-plausible depth (5 Trotter steps, 6 time samples): L1 distance 0.36–0.44, top-5 overlap only 0.43–0.67 across all 4 targets — this approximation error is carried forward as a caveat on every noise-comparison number below, not glossed over. **Pre-registered phase-free-robustness hypothesis** ("the time-averaged circuit will show less top-5 degradation under gate noise than a single finite-time snapshot, since the converged observable is provably phase-free") — **falsified on balance**: supported on KRAS_G12C/MYC_MAX at higher error rates, contradicted on BCR_ABL1 (time-averaged *worse* at every non-zero error rate tested), a wash on CARDIAC_MYOSIN. No clean win for the corrected convention over TASK-0068's original snapshot approach. **Resource table** (analytic `coarse.trotter_cost` + real transpilation): full resolution is 169–704 qubits / 3.3M–124.9M 2-qubit gates — confirms the task's own prediction, not executable near-term by any measure. Coarse-grained to Louvain's actual N≈9–15 (requesting 12/20 rarely gets exactly that many clusters): analytic 2-qubit-gate counts 36K–518K are themselves NISQ-implausible: transpiled against a **real IBM device calibration snapshot** (`qiskit_ibm_runtime.fake_provider.FakeSherbrooke`, IBM Eagle r3, 127 qubits) the actual circuit needs 538–1486 2-qubit gates, depth 1010–2565 — down from the analytic estimate but still large. **IQM portability** (per direct user instruction, prioritized over Braket): the live `qiskit-iqm` SDK could not be installed — hard dependency conflict, pins `qiskit~=0.39.1` against this project's `qiskit>=2.0` stack (confirmed via `pip install --dry-run` before deciding, not assumed) — worked around with a hand-built `CouplingMap` of IQM Garnet's published 20-qubit square-lattice topology; transpiled circuits against it came out **shallower than the IBM-Sherbrooke transpile at every single data point** (e.g. KRAS_G12C N=12: depth 965 vs. 1859) — a real, disclosed, topology-driven resource difference, not a claim of IQM hardware superiority (the map is a public-topology stand-in, not the live SDK's actual transpiler). **Feasibility verdict, using FakeSherbrooke's real median 2-qubit (ECR) gate error (0.78%) and a disclosed `(1-p)^n_2q >= 0.5` usability bar**: **all 4 targets `FAULT_TOLERANT_ONLY`, at both full and coarse resolution** — even the smallest coarse circuit (MYC_MAX, 538 2-qubit gates) lands at an estimated fidelity of 0.015, nowhere near the bar. **Retention metric** (TASK-0172 not yet landed; naive Louvain fallback used, as that task's own Dependency section allows, and stated here): top-10 Jaccard/Spearman retention between full-resolution and coarse-grained-then-projected-back rankings is close to zero on every target (Jaccard 0.00–0.18, Spearman 0.02–0.26) — the coarse-graining aggressive enough to be NISQ-plausible also destroys nearly all of the fine-resolution ranking signal, compounding the feasibility problem rather than trading it off. **Braket**: not run — no AWS credentials in this environment; per direct user instruction (2026-08-02), deprioritized behind a portable Qiskit-simulator-first path (real IBM calibration snapshot + hand-built IQM topology) rather than blocking on it; left as an explicit open item for whenever credentials are available, not silently dropped. Classiq evaluation and the conditional QAOA estimate (blocked on [[TASK-0181]]) were not run this pass. | [[TASK-0182]], [[TASK-0068]], [[TASK-0130]], [[TASK-0159]], [[TASK-0013]] |
| 57 | Does reframing cryptic-pocket prediction as ENM-ensemble search (fpocket as oracle, not competitor) actually recover the real holo pocket on real apo structures, at what frequency, and does the backbone-layer rare-event quantum-search argument survive measurement on real data (not just the synthetic toy model)? | **resolved 2026-08-02: recovery works but specificity is target-dependent, and the rare-event argument fails on real data too, corroborating the synthetic finding.** Positive control (BCR_ABL1) passes convincingly (80% ensemble hit rate, matches static apo's own 87.5% overlap). Real-vs-decoy specificity: BCR_ABL1 gap 0.29 (0.800 vs 0.510), KRAS_G12C gap 0.13 (0.500 vs 0.370), **CARDIAC_MYOSIN no specificity at all** (0.200 vs 0.190). n_modes sweep on BCR_ABL1 (5/20/40): real-pocket recovery stays high throughout (0.983/0.800/0.783) — not rare, matching the synthetic reference's own p=0.244-0.694 — fatal to a Grover-style backbone rare-event claim on real targets, not just the toy model. Quantum claim moves to the side-chain layer (NP-hard rotamer packing), full formulation deferred to [[TASK-0181]] Phase B (in progress elsewhere) rather than duplicated. | [[TASK-0185]], [[TASK-0163]], [[TASK-0187]], [[TASK-0167.001]], [[TASK-0169]], [[TASK-0181]] |
| 58 | Does the exact Gaussian-network binding-response coupling free energy `ddG` (a *response* to a bound ligand, not a propagating signal — the collaborator's own reframing) find real allosteric signal once its proven proximity confound (rho +0.71 to +0.97, as bad as every propagation observable in this register) is removed by a distance-shell-normalised specificity statistic? | **resolved 2026-08-02: methodologically decisive, empirically negative.** New `allostery.response`; independently reproduces the external reference prototype's own real number to 1.6e-13; reciprocity/zero-coupling/entropy-cross-check/low-rank-shortcut (<1e-10 vs brute force) gates all pass. The mandatory dumbbell gate found a real complication on TASK-0103's native fixture first (signal below numerical noise floor, root-caused not asserted) before passing cleanly on a geometrically realistic adaptation. **On all 7 real targets, `rho(specificity,-hop)` collapses from +0.71/+0.94 (raw) to within ±0.044 of zero** — a cleaner real-data transfer than [[TASK-0149]]'s own precedent. No target/label cell clears its floor with a surviving permutation null (PTP1B/core's point-estimate margin, the only candidate, p=0.132). A lightweight LOD probe (own limited scope, not [[TASK-0167.002]]'s full protocol) shows a clean, monotonic real-topology detection curve (AUC 0.52→0.85, strengths 0-30). Pre-registered falsification did not fire (rho did drop below 0.6; the LOD is real) — but no exploitable real signal was found on the current benchmark set either. Adds ~21 cells to [[TASK-0161]]'s multiplicity budget (not re-run here, flagged for the next full budget pass). | [[TASK-0177]], [[TASK-0103]], [[TASK-0145]], [[TASK-0149]], [[TASK-0167.001]], [[TASK-0123]], [[TASK-0158]], [[TASK-0161]] |
| 59 | Does reframing site identification as constrained *selection* (a k-subset QUBO maximising member quality + spatial cohesion + allosteric coupling − anti-confound proximity − distality, NP-hard via densest-k-subgraph) beat *ranking* (greedy top-k on score alone) classically, on the 3 mandatory targets, at a pre-registered canonical weight point — the cheap gate [[TASK-0181]]'s own Constraint requires before any quantum formulation is attempted? | **resolved 2026-08-02: no — gate CLOSED, 0/3 strict wins, robust to solver noise.** New `allostery.selection` (hand-rolled exact enumeration + swap-based simulated annealing over exactly-k subsets — no `dimod`/QUBO-library dependency added; cardinality enforced structurally, not by penalty). At the canonical weight point `(a,b,c,d,e)=(1,1,1,1,1)`, `k=5`, 8-restart best-by-objective search (a single SA run is noisy — caught directly: one KRAS_G12C run flipped hit/miss between two calls differing only in iteration count): KRAS_G12C QUBO misses (greedy top-k hits), BCR_ABL1 and CARDIAC_MYOSIN both miss. Not a solver-quality artifact — the 3 pre-registered controls (degenerate-case reduces exactly to greedy top-k; anti-confound term measurably repels the seed; SA reaches the exact brute-force optimum on a `C(12,3)=220` instance) all pass, and on KRAS_G12C the QUBO's own best-found set scores higher on its own objective (22.30 vs. greedy's 6.61) yet still misses the labelled pocket — the canonical-weight objective genuinely optimises toward a different region than the true pocket on the one target where it mattered most. Per the pre-registered gate: **Phase A reported closed, no quantum formulation built, full 14-target × weight/k grid not run** (corrected target count — `config/targets.yaml` has 14 usable targets, not 12; `LDH` is deliberately `omitted_targets`, TASK-0003). Phase B (side-chain rotamer-packing QUBO — the layer [[TASK-0185]]/row 57 already deferred its own quantum claim to) shipped as a formulation-only write-up regardless, per this task's own scope. Adds 3 cells to [[TASK-0161]]'s multiplicity budget (gate-decision cells only; the unrun full grid's ~896 potential cells do not enter the budget). | [[TASK-0180]], [[TASK-0163]], [[TASK-0167.001]], [[TASK-0185]], [[TASK-0161]] |
| 60 | Is a structured (mode-resolved) vibronic bath — specific ANM normal modes resonantly coupled to specific site-energy gaps — worth building before the 2026-09-15 forward-proposal deadline, per `PANEL_REVIEW_2026-07-25.md`'s own deprioritization instruction, and can the coupling model at least be defined and literature-grounded now? | **resolved 2026-08-03: filed, not built, per the review's own explicit instruction — the required coupling-model definition and citation verification are done.** 2 citations independently re-verified (Christensson/Kauffmann/Pullerits/Mančal 2012, J. Phys. Chem. B 116:7449; Patra & Tiwari 2022, J. Chem. Phys. 156:184115, more directly on-point for *selective* site-specific enhancement). Standard Holstein-type site-diagonal coupling mapped onto this project's own quantities: site energies = `H_new`'s diagonal, bath modes = `superpose.anm_modes` (reused, not re-derived), coupling strength ∝ mode eigenvector displacement at each residue, resonance condition `ω_k≈\|H_new_ii−H_new_jj\|`. Honest ceiling stated: this is a proposed, literature-grounded mapping, not a validated model — the actual Redfield/structured-bath evolution, synthetic falsifier, and real-target scoring are the deferred, highest-implementation-cost work, not attempted here. | [[TASK-0147]], [[TASK-0041]], [[TASK-0141]], [[TASK-0157]], [[TASK-0120]], [[TASK-0133]] |

| 60 | [[TASK-0190]] found `compact_patch_matched` cannot genuinely reach real pocket Rg for CARDIAC_MYOSIN/PTP1B (a hard support ceiling, not a rare tail event) — does a null construction exist that can, and does fixing the centring defect change `dcc_low`'s already-published "does not survive" verdict on either target? | **resolved 2026-08-04: a construction exists (new `nulls.graph_walk_patch`, randomized connected growth on the contact graph instead of Euclidean-nearest-neighbour selection — verified to reach real pocket Rg on both targets, 20,000 unconstrained draws, real Rg sits at the 83.8th/17.9th percentile of support, not the edge) — and yes, the verdict changes, on exactly one of the two cells.** CARDIAC_MYOSIN's own "does not survive" conclusion holds, decisively (min p=0.0254 vs. bar 0.00833, 20,000 replicates). **PTP1B's `dcc_low` (k=10) now survives its own pre-registered bar: p=0.0027 vs. 0.003125** (95% CI [0.0020,0.0035], point estimate clears, CI slightly straddles — reported exactly, not rounded to a clean win). Ordering check (`p_scattered<=p_matched<=p_compact`) passed on all 8 cells tested — strong evidence this is real, not an artifact. Real, stated mechanism for why TASK-0190's own "a more-reaching null could only be more lenient" reasoning was wrong for this one cell: dispersion and leniency-for-this-specific-score-field are not the same property for `dcc_low`, which plausibly favours geometrically tight patches independent of location. Per TASK-0190's own pre-registered reading rule ("if exactly one survives... a mixed result, not smoothed into complete negative"), this is now a mixed result, not the complete negative [[TASK-0161]]/[[TASK-0191]]'s "zero confirmed positives" headline currently states — flagged in both places, not corrected in place, and handed to whoever owns [[TASK-0184]]'s narrative to decide how it's framed. | [[TASK-0190]], [[TASK-0158]], [[TASK-0149]], [[TASK-0151]], [[TASK-0167.003]], [[TASK-0161]], [[TASK-0191]] |

**Architect cross-reference note, 2026-08-03 (reconstructed; not a new
resolved question — a pattern across rows 55/57/58/59 worth stating once,
connected, rather than independently rediscoverable per-row).** Read
individually, these four rows can look like they pull in different
directions — [[TASK-0177]] (row 55)'s label flips verdicts depending which
residue set scores a target; [[TASK-0178]] (row 58)'s response-coupling
statistic and [[TASK-0181]] (row 59)'s selection QUBO both come back
negative on real data; [[TASK-0185]] (row 57)'s conformational search is
positive on one target, weak-to-absent on the other two. They are not in
tension — each is answering a different, precisely-scoped question, and
each already states its own scope carefully (see each row's own text
above). The connected point worth naming explicitly: **TASK-0178 and
TASK-0181 both independently pass every internal correctness gate they set
for themselves before touching real data** — TASK-0178 reproduces an
external reference implementation to 1.6e-13 and passes reciprocity/
zero-coupling/entropy-cross-check/dumbbell; TASK-0181's SA solver is
confirmed to reach the true combinatorial optimum and its anti-confound/
degenerate-case controls both pass — and **both still find nothing
exploitable on the actual protein benchmark set.** That is a meaningfully
different situation from earlier findings in this register that turned out
to trace back to a broken null or an unvalidated propagator (e.g.
[[TASK-0158]]'s compact-patch null fix). Two independently-built,
independently-validated methods agreeing on "no real signal here" is
better evidence that the negative is about the benchmark/hypothesis than
about broken tooling — though it is not proof of that; see [[TASK-9000]]'s
parallel program (a separate branch, `val-9xxx`, deliberately outside this
register) for the complementary check this project has never had before:
validating the propagator/statistics engine against a system with an
externally, independently known answer, rather than only against
internally-constructed controls.

## Holo-direction module Step 2 go/no-go gate (TASK-0015, 2026-07-28)

**[EXECUTED, real code, real data, 7 targets]** `HOLO_DIRECTION_MODULE.md`'s
own spec (Steps 0-5): predict the apo->holo conformational-change
*direction* from the apo structure alone, generate a small admissible
family of deformed graphs, gate on whether any of them actually reaches
the holo-defined pocket (Step 2), and only then (Step 3-5) run transport
on the survivors. This task builds Steps 0-2 and runs Step 2's own
"First action" — the spec's own explicit instruction to gate before
building anything downstream.

New `src/allostery/holo_direction.py`: `PERTURBATION_PROTOCOL` (Step 0,
frozen before touching any holo data — lowest 10 non-trivial ANM modes,
single-mode +/- excitation at 3 amplitude scales relative to a per-mode
"thermal unit" `a_k^(1)=sqrt(1/(kappa*lambda_k))` derived from
`calibrate_kappa`'s own already-established B-factor-matching convention,
not a newly invented free parameter), `build_deformation_family` (Step 1),
`go_no_go_gate` (Step 2, two independent components: pocket-restricted
CO(m) reusing TASK-0133/TASK-0150's corrected `restricted_cumulative_
overlap`, and a new "does any candidate create a contact-graph edge
between an active-site and pocket residue that apo doesn't already have"
check — never collapsed to a single boolean).

**Real, apo-only finding in Step 1 itself**: 90-98% of the 60 candidates
per target are rejected on `ca_spacing_violated` alone (never clash or
global RMSD) — linear one-shot ANM-mode extrapolation distorts local
backbone bond geometry non-uniformly across modes, even at the smallest
tested amplitude. Only 1-10 candidates survive per target. This
constraint never touches holo data, so this is not label leakage; the
threshold was fixed before any real target ran and left unchanged after
seeing these counts, per Step 0's own discipline.

**Step 2 run on all 7 `status: verified` targets with a real `holo_pdb`**
(MYC_MAX excluded, no ground truth):

| Target | CO(10) | Right edges created? | Admissible/rejected | Verdict |
|---|---|---|---|---|
| KRAS_G12C | 0.4652 | No | 3/57 | `NO_GO` |
| BCR_ABL1 | 0.1330 | No | 7/53 | `NO_GO` |
| CARDIAC_MYOSIN | 0.2378 | No | 1/59 | `NO_GO` |
| PTP1B | 0.2152 | No | 4/56 | `NO_GO` |
| GLUCOKINASE | 0.1423 | No | 10/50 | `NO_GO` |
| CASPASE1 | 0.0714 | No | 2/58 | `NO_GO` |
| CASPASE7 | NaN (blocked) | No | 3/57 | `NO_GO` |

Two real bugs found and fixed while running this: (1) `go_no_go_gate`
initially hardcoded `chain_map=None` instead of
`chain_map_from_config(target_config)` — the exact TASK-0144 apo/holo
differing-chain-letter issue, broke CARDIAC_MYOSIN/GLUCOKINASE outright
until fixed; (2) CASPASE7's own labeled pocket residues have zero holo
correspondence in the alignment's common set at all — CO is genuinely
undefined there (reported as NaN, not a misleading number), verdict
conservatively defaults `NO_GO` rather than silently passing on an
undefined comparison, the same degradation shape `compute_learnability`'s
own `co_blocked_reason` already established.

**Headline: 7/7 `NO_GO`. Across every target, mode, sign, and amplitude
scale tested, no admissible deformed graph ever creates a contact-graph
edge between an active-site residue and a pocket residue that did not
already exist in the apo structure — and no target's CO(10) clears the
0.5 threshold either** (max 0.4652, KRAS_G12C; directionally consistent
with, though not numerically identical to, this project's own already-
published pocket-restricted CO(20) numbers for the same 2 targets where
both exist — KRAS_G12C 0.458, CARDIAC_MYOSIN 0.254, [[TASK-0150]]/
[[TASK-0152]] — different mode count, independently recomputed here at
this module's own `n_modes=10`, not reused).

**Per the spec's own explicit instruction ("build the rest only for the
targets that clear it"), Steps 3-5 are not built for any target — there
is no target that cleared Step 2.** This is the spec's own anticipated,
"publishable" NO case: "cryptic pocket unreachable by the thermal
ensemble of the apo state" beats an unbuilt walk scored at chance. This
is independent, converging evidence for the same reframe [[TASK-0162]]'s
forward/reverse asymmetry and [[TASK-0163]]'s fpocket result already
raised: the apo structure's own low-frequency linear response, alone,
does not reach the holo-defined pocket on any target tested, under any
of the 60 apo-only admissible perturbations tried per target.

8 new unit tests (synthetic, all passing — a direct edge-detection
isolation test with a known answer, plus integrity-constraint sanity
checks in both directions). Full suite: 994 passed, 2 xfailed, 0 failed
(986 pre-existing + 8 new).

Full detail: `.ai/tasks/DONE/TASK-0015-holo-direction-module.md`,
`__WORK_IN_PROGRESS__/scripts/holo_direction_step2_gate.py`,
`__WORK_IN_PROGRESS__/RESULTS/results/tasks/0015_step2_gate/step2_gate.json`.

**Correction, same day, user-flagged, two rounds:** the "right edges
created?" test above required a *direct* active-site↔pocket contact-graph
edge — wrong, since this project's own pocket/active-site labels are
distal by definition (`labels.build_labels`'s own exclusion assembly);
a direct-contact test can never fire on a genuinely distal pair
regardless of what the deformation does. Fixed to a graph-hop *shortcut*
test instead (does any admissible deformation shorten the active-site↔
pocket contact-graph hop distance, via `baselines.hop_from_seed`) — the
right quantity for a distal-by-definition pair. A second challenge (is
this reading robust to the contact-graph cutoff, the same knob
[[TASK-0067]]/[[TASK-0114]] already established as worth sweeping
elsewhere in this register) led to sweeping {4.5, 6.0, 8.0, 10.0} Å.
**Final: `shortcut_verdict_across_grid` = `NO_GO` on all 7 targets at
every cutoff tested**, including PTP1B/BCR_ABL1, where a real 6-10 hop
apo-side gap exists at the strictest (4.5 Å) cutoff — Step 1's own narrow
admissible family (1-10 candidates/target) is too small to bridge even a
moderate topological gap, not merely "there is no gap to bridge." The
headline verdict (7/7 `NO_GO`) is unchanged by either correction; the
mechanism explaining it is now the correct one.

---

## Mechanism-validated allosteric ground truth: PTP1B, Phase 1 (TASK-0170, 2026-07-28)

Every label in this project is a **drug-contact** set (residues within
`pocket_contact_cutoff` of a bound ligand). PTP1B's own label is drawn from
a BB-series *allosteric* inhibitor (ligand `892`) bound at the alpha3/
alpha6/alpha7 site, but it is still a drug-contact definition, not the
literature's own NMR-relaxation-dispersion/multitemperature-crystallography
definition of the allosteric communication network. This task curates that
network from two independent, peer-reviewed sources — Choy/Kern et al.,
*Mol. Cell* 2017 (PMC5325675) and Keedy/Fraser et al., *eLife* 2018;7:e36307
— and scores the register's own existing observables against it, unchanged,
alongside the existing drug-contact label.

**Curation and verification, done before any scoring (label frozen first,
per this task's own Constraint):** 35 literature-cited residues fetched
from both papers; every one checked directly against this project's own
loaded 1SUG structure (resnum → resname), not trusted from either paper's
numbering. **One failed verification**: Glu157 cited in [1]'s L11-loop
list; the real structure has Gln157 at that position — excluded, not
silently corrected. **One residue excluded for a labeling-invariant
conflict**: Arg221 is part of this project's own `active_site`
(functional/catalytic seed) for PTP1B — `build_labels`'s own
pocket/active_site disjointness invariant requires excluding it, asserted
in code (`RuntimeError` if violated), not assumed. **One residue excluded
for low confidence**: Met3 (N-terminal, "L16 site"), a structurally
isolated single citation that does not fit either paper's own description
of "one contiguous face." Final curated network: **31 residues** — WPD
loop (177,178,179,180,181,185,269), L11 loop (105,148,150,152,153), alpha3
(190,191,192,193,196,197,198,200), alpha6/alpha7
(267,270,276,277,280,281,282,290,291,295), plus Tyr176.

**Overlap with the existing drug-contact label (14 residues), measured
before scoring anything, per this task's own Planned Validation:**
Jaccard = 0.286 — 10 residues shared (192,193,196,197,200,276,277,280,
281,282, all in alpha3/alpha6), 21 mechanism-only (the full WPD loop, the
full L11 loop, and 5 more alpha3/alpha6/alpha7 residues the drug-contact
shell does not reach). **Partial overlap, as the design predicted** — not
zero (which would suggest a numbering error) and not complete (which would
make the experiment uninformative).

**The proximity floor is genuinely lower against the dispersed
mechanism-validated label** (max baseline AUC 0.601 vs. 0.768 for the
drug-contact label on the same structure, same seed) — a dispersed
coupling network is harder for distance baselines, exactly as anticipated,
and this is therefore if anything a *fairer* test, not a harder one to
pass.

**Real-run result, all 3 headline observables, same code path scoring both
labels in one run:**

| Observable | AUC (mechanism-validated) | AUC (drug-contact) | Floor (mech.) | CI (seq.-block) | CI overlaps floor? | Scattered-null percentile (p) |
|---|---|---|---|---|---|---|
| `time_averaged_ctqw_converged` | 0.426 | 0.486 | 0.601 | [0.309, 0.534] | **No — below** | 11.1 (p=0.889) |
| `prs_low` (k=20) | 0.429 | 0.437 | 0.601 | [0.303, 0.572] | **No — below** | 9.7 (p=0.903) |
| `dcc_low` (k=20) | 0.529 | 0.505 | 0.601 | [0.360, 0.696] | Yes | 71.7 (p=0.283) |

Permutation null is the **scattered** (`rng.choice`) draw, not
`nulls.compact_patch`/`compact_patch_matched` — this task's own Intent
Contract states the compact-patch draw is "badly wrong" for a genuinely
dispersed label, and TASK-0158's over-conservatism finding (external
review, 2026-07-28) was specific to *compact* labels on smooth score
fields, not dispersed ones.

**Headline: the negative holds, and is if anything sharper, against an
independent, literature-derived ground truth — this is not the reframe
the source review's own framing considered possible.** Two of three
headline observables (`ctqw_converged`, `prs_low`) score
*significantly below* their own proximity floor against the
mechanism-validated network (non-overlapping CI, in the wrong direction —
an active anti-signal, not a null result); `dcc_low` is consistent with
its floor (CI overlaps, null percentile 71.7, not significant). Per this
task's own pre-stated escape clause — *"if they fail against both, the
negative is much stronger than currently claimed"* — that is the outcome
here. The existing drug-contact-label negative was never an artifact of
that label happening to be the wrong answer key.

**Phase 2 (further systems: PDZ3, adenylate kinase, DHFR) — Implementer's
own call, not pursued**: Phase 1's own explicit gate is "only if Phase 1
is informative." Phase 1 *was* informative (a real, load-bearing
overlap measurement and a genuine floor difference), but it reinforced
the existing negative rather than overturning it — the scenario Phase 2
was designed to chase (an observable that fails the drug-contact label
but succeeds against a mechanism-validated one) did not occur for any of
the 3 headline observables tested. Escalating to 2–3 more systems at
multi-day literature-curation cost, per the source review's own binding
constraint (write from 2026-08-08), is not justified by this result.
State the finding and stop, per this project's own "write, don't build"
discipline this late in the schedule.

Full detail: `.ai/tasks/DONE/TASK-0170-mechanism-validated-ground-truth.md`,
`__WORK_IN_PROGRESS__/scripts/mechanism_validated_ptp1b.py`,
`__WORK_IN_PROGRESS__/results/tasks/0170_mechanism_validated/ptp1b_mechanism_validated.json`.

---

## Apo-structure sensitivity sweep — is KRAS_G12C's result a lucky draw? (TASK-0155, `REVIEW-panel-2026-07-28-external.md` §2/§5C, 2026-07-30)

**Yes — decisively, and compounded by a genotype error in the structure
used to produce every KRAS_G12C number this project has ever reported.**
Every result in this register is conditioned on a single, arbitrary apo
structural draw ([[TASK-0124]]'s 5TBY→8QYP swap already moved
CARDIAC_MYOSIN's AUC by 0.27 and erased its only positive); this sweeps
ONLY the apo input for KRAS_G12C (the one target with a marginal
surviving signal) — holo (6OIM), operator family, cutoffs, seed
convention, and label definition all held fixed — through the
*unmodified* existing pipeline.

**A finding that precedes the sensitivity question and is more
consequential: `targets.yaml`'s current `apo_pdb: 4OBE` is NOT a G12C
mutant.** Its own RCSB title is "Crystal Structure of GDP-bound Human
KRas"; its deposited sequence has Gly (wild-type), not Cys, at position
12 — confirmed two independent ways: direct sequence inspection
(anchor-relative offset, sanity-checked against the invariant position-13
residue) and 4OBE's own `pdbx_database_related` metadata, which
cross-references 4NMM/4LDJ as "G12C KRas" entries *related to* 4OBE, i.e.
RCSB itself treats 4OBE as the wild-type parent, not a G12C structure.
Every prior KRAS_G12C AUC in this project's history was computed against
the wrong genotype for a target labeled "G12C." Retained below for
continuity but reported separately, never pooled into the G12C
distribution.

**RCSB verification of the task filing's own two other named candidates**
(both excluded, reasons stated per this task's own requirement):
**4DSN** is a **G12D** structure (Asp at position 12, wrong oncogenic
mutant). **3GFT** is wild-type at position 12 but a **Q61H** mutant with
a GTP analogue (GNP) bound, not GDP — wrong mutant and wrong nucleotide/
conformational state.

**The verified candidate pool** (assembled fresh, not from the filing
text): RCSB Search API full-text "KRAS G12C" + Homo sapiens → 123 raw
hits → sequence-filtered to entries with a real Cys at position 12 (112
true G12C entries) → X-ray only (no NMR structures exist for KRAS G12C at
all — checked directly, satisfying this task's own "handle NMR
explicitly" requirement by confirming the case doesn't arise; 3 cryo-EM
entries excluded to keep the comparison homogeneous with holo's own X-ray
method) → GDP+Mg-only ligand set (excludes ~90 inhibitor- or GNP-bound
structures — a bound Switch-II drug remodels that exact pocket, which
must not be baked in as apo "structure") → 22 clean candidates, 1.04–2.41
Å. 10 selected spanning that full resolution range.

**Result: a clean, decisive "lucky draw."**

| Structure | Resolution | N | AUC (optimised) | P@5 | Diagnosis |
|---|---|---|---|---|---|
| 4OBE (CURRENT, flagged WT) | 1.24 Å | 169 | 0.590 | 0.200 | NO_FAILURE_DETECTED (floor-clears) |
| 8AZX | 1.04 Å | 170 | 0.408 | 0.000 | BEATS_CHANCE_NOT_FLOOR |
| 4LDJ | 1.15 Å | 170 | 0.518 | 0.000 | NO_SIGNAL_IN_APO |
| 7A1X | 1.32 Å | 170 | 0.595 | 0.000 | NO_FAILURE_DETECTED |
| 8TXJ | 1.4 Å | 169 | 0.571 | 0.000 | NO_FAILURE_DETECTED |
| 8QUG | 1.56 Å | 170 | 0.439 | 0.000 | BEATS_CHANCE_NOT_FLOOR |
| 9UOH | 1.75 Å | 169 | 0.446 | 0.000 | BEATS_CHANCE_NOT_FLOOR |
| 7YCE | 1.8 Å | 169 | 0.437 | 0.000 | BEATS_CHANCE_NOT_FLOOR |
| 7MDP | 1.96 Å | 167 | 0.442 | 0.000 | BEATS_CHANCE_NOT_FLOOR |
| 7RP3 | 2.0 Å | 167 | 0.592 | 0.000 | NO_FAILURE_DETECTED |
| 8AFC | 2.41 Å | 169 | 0.549 | 0.000 | NO_SIGNAL_IN_APO |

Across the 10 true-genotype G12C structures: AUC ranges **0.408–0.595**
(spread 0.187, the same scale as [[TASK-0124]]'s 0.27 CARDIAC_MYOSIN
swing), median **0.482** — indistinguishable from chance, *below* 0.5 —
mean 0.500 exactly. Only **3 of 10 (30%)** floor-clear
(`NO_FAILURE_DETECTED`); 2/10 don't even beat chance
(`NO_SIGNAL_IN_APO`); the remaining 5/10 beat chance but not the floor.
**P@5 is exactly 0.000 on all 10** — not one true G12C structure's top-5
ranked residues include a single real pocket residue; only the
mislabeled wild-type 4OBE achieves a nonzero P@5 (0.200). The 4OBE number
this project has reported throughout (AUC 0.590, floor-clearing,
CI-overlapping) sits at the high end of the true distribution, not
merely off it — the "marginal surviving result" the review called out is
both drawn from the wrong genotype and would not have been called a
"surviving" result under most alternative true-genotype draws.

**One-line verdict**: KRAS_G12C's floor-clearing result is **not
structure-robust — it is a lucky draw**, and the structure it was drawn
from is not even the correct mutant. This closes the review's §5C gap
and directly answers this task's own Planned Validation question; no
synthetic gate was needed, the distribution itself is the result.

Not extended to BCR-ABL1/PTP1B per this task's own "optionally, if KRAS
shows large spread" condition — KRAS's spread is already large and
decisive; per the review's own binding 2026-08-08 writing-freeze
constraint, this is reported and stopped rather than repeated on two
more targets whose own headline results are already `NO_SIGNAL_IN_APO`/
mixed and not the register's "marginal surviving" case this task was
filed to stress-test.

Full detail: `.ai/tasks/DONE/TASK-0155-apo-structure-sensitivity-sweep.md`,
`RESULTS/results/tasks/0155_apo_sensitivity/apo_sensitivity_sweep.json`,
`scripts/apo_structure_sensitivity_sweep.py`.

---

## Two-boson Hong-Ou-Mandel path interference (TASK-0157, forward-proposal note, 2026-08-02)

**Filed, not built — per `PANEL_REVIEW_2026-07-25.md`'s own later, dated,
explicit instruction to describe this as the principled next rung in the
forward-proposal section rather than spend implementation time on it
before the deadline.** This supersedes the task's own original Intent
Contract (construct the k=2 symmetrized Hilbert space, a synthetic
falsifier, real-target scoring) — corrected at pickup, not abandoned
mid-execution.

**Precondition Gate satisfied first** (required before any `N²`-cost work
regardless of whether it is ultimately built): the non-reducibility
argument is real, not merely asserted. For two non-interacting bosons
from distinct sources, the coincidence probability `|ψ(i,j;t)|²` expands
into Falsifier C's own already-dead product term plus a genuine
interference cross-term `2·Re[c_i(t)c_j'(t)(c_j(t)c_i'(t))^*]` that
depends on the *relative phase* between two single-particle amplitude
paths — information every converged/time-averaged observable in this
register ([[TASK-0130]]) provably discards ([[TASK-0146]]'s own
phase-free-at-convergence finding). This is the one genuinely
non-reducible multi-particle residual left in this program's search space
(fermions reduce to determinants, in P — Terhal & DiVincenzo 2002; naive
interacting co-occupation is Falsifier C, already near-dead; anyons have
no formalism on a 3D contact graph).

**3 governing citations independently re-verified** via live search
against each paper's own abstract/venue, not relayed from the filing
text: Valiant 1979 (*Theoretical Computer Science* 8:189-201, the
permanent is #P-complete), Terhal & DiVincenzo 2002 (*Phys. Rev. A*
65:032325, noninteracting-fermion/matchgate circuits are classically
simulable), Aaronson & Arkhipov 2011 (STOC 2011, linear-optics hardness
needs many photons across `m=O(n²)` modes). All three confirm the task's
own characterization exactly.

**Honest ceiling, stated from the primary sources directly**: a 2×2
permanent is exactly as easy to compute as a 2×2 determinant — no
complexity separation exists at k=2. Even a clean positive HOM-bunching
finding at this scale would be a *better observable*, not a demonstrated
quantum advantage, which needs the asymptotic photon number this task's
own scope was never going to reach.

**Not built, per the review's own explicit deprioritization, not a
partial result**: no k=2 symmetrized Hilbert space, no synthetic
falsifier, no real-target scoring. Filed as a forward-proposal note in
`EXECUTION_PLAN.md`'s Phase 1E instead.

Full detail: `.ai/tasks/DONE/TASK-0157-two-boson-hom-interference.md`,
`EXECUTION_PLAN.md`'s own Phase 1E forward-proposal note.

---

## Structured-bath vibronic resonance (TASK-0147, forward-proposal note, 2026-08-03)

**Filed, not built — per `PANEL_REVIEW_2026-07-25.md`'s own later, dated,
explicit instruction** ("[[TASK-0147]] (vibronic/structured bath — most
quantum-biology-grounded remaining idea, highest implementation cost)...
describe in the forward-proposal section, do not spend implementation
time before 2026-09-15") — the same treatment [[TASK-0157]] received on
the same day this task was picked up. This supersedes the task's own
original Intent Contract (build the structured-bath master equation, a
synthetic falsifier, real-target scoring) — corrected at pickup, not
abandoned mid-execution.

**This task's own Intent Contract requires one deliverable regardless of
whether the full model is ever built: define and justify a mode-resolved
vibronic coupling model, citing the literature it is grounded in — done
here.** `haken_strobl` (this project's existing ENAQT machinery) is
Markovian, unstructured, single-rate dephasing; the question is whether a
*structured* bath — specific vibrational modes resonantly coupled to
specific site-energy gaps — enhances transport to a specific site rather
than uniformly relaxing toward classical diffusion, the way
[[TASK-0141]]'s already-negative flat-rate sweep found.

**2 governing citations independently re-verified** via live search
against each paper's own abstract/venue, not relayed from the filing
text:
- **Christensson, Kauffmann, Pullerits & Mančal (2012), "Origin of
  Long-Lived Coherences in Light-Harvesting Complexes," J. Phys. Chem. B
  116(25):7449–7454.** Confirmed: a vibronic-exciton model explains
  long-lived 2D-spectral oscillations in the FMO complex via resonance
  between a vibrational mode's frequency and the excitonic energy gap
  between chromophore sites — matches this task's own original citation
  exactly.
- **Patra & Tiwari (2022), "Vibronic Resonance Along Effective Modes
  Mediates Selective Energy Transfer in Excitonically Coupled
  Aggregates," J. Chem. Phys. 156:184115.** Confirmed, and more directly
  on-point than the task's own original citation: vibronic resonance
  along *specific* normal modes produces *selective* (site-specific, not
  uniform) transfer enhancement — the real literature basis for this
  task's own central premise that a structured bath can favor one
  candidate site over another, which the first citation alone
  establishes coherence-longevity for but not site-selectivity as
  sharply.

**Mode-resolved coupling model, defined and justified**: both papers use
Holstein-type, site-diagonal linear vibronic coupling —
`H = H_el + H_vib + H_el-vib`, `H_el-vib = Σ_i Σ_k g_{i,k}(b_k+b_k^†)|i⟩⟨i|`
— gated by the resonance condition `ω_k ≈ |ε_i − ε_j|` (a vibrational
quantum matching the excitonic gap between a specific site pair, not a
generic bath property). Mapping this project's own already-computed
quantities onto that standard form (an explicit Implementer's-call
translation — Cα ANM normal modes are not literally chromophore
vibrations; the formalism is ported, not its physical system):
site energies `ε_i` = `H_new`'s own diagonal; bath modes = the ANM's own
normal modes (`superpose.anm_modes`, `ω_k=√λ_k`, already computed for
the learnability gate, [[TASK-0120]]/[[TASK-0133]], reused not
re-derived); coupling strength `g_{i,k}` ∝ mode `k`'s own eigenvector
displacement magnitude at residue `i`, `|v_k(i)|` — exactly this task's
own suggested definition; resonance condition for a candidate pair
`(i,j)`: `ω_k` close to `|H_new_ii − H_new_jj|`.

**Honest ceiling, stated per this task's own Constraint**: this mapping
is a real, literature-grounded, dimensionally-consistent translation of
a standard coupling form onto existing project quantities — a *proposed*
model, not a validated one. The actual structured-bath evolution (full
Redfield: per-mode system-bath correlation functions, secular-
approximation validity checks, numerical propagation of an `N²×N²`
Liouville-space density matrix — or a justified simplified secular/
rate-based approximation) is genuinely the highest-implementation-cost
item this batch's own filing review already flagged it as, and is
exactly the work explicitly deferred past the submission deadline. No
synthetic falsification gate and no real-target scoring were run.

Full detail: `.ai/tasks/DONE/TASK-0147-vibronic-resonance-structured-bath.md`,
`EXECUTION_PLAN.md`'s own Phase 1E forward-proposal note.

---

## Reverse-direction coupling test on HOLO topology (TASK-0171, comparison to TASK-0162, 2026-08-02)

**The apo-vs-holo gap here is NOT small in [[TASK-0067]]'s own precedent
sense — it is large enough to flip 10 of 25 (40%) forward floor-clearing
verdicts, concentrated in two specific observables.** [[TASK-0162]]'s own
forward/reverse coupling test ran every propagation on **apo** topology
exclusively (`build_H_new(apo.coords, ...)`, confirmed directly from that
script before starting this one) — holo was used there only to derive
labels. This re-runs the identical 5-observable × 5-target (3 mandatory +
PTP1B/CASPASE7) forward/reverse comparison **holo-native end-to-end**:
`H_new`/`H2_combinatorial_laplacian` built from `holo.coords`/
`holo.bfactors`, and `_holo_native_labels` ([[TASK-0067]]'s own holo-frame
label construction, imported verbatim) for the pocket/active-site masks —
not apo-numbered indices ported onto holo's coordinate array. Every
scoring function reused completely unmodified from TASK-0162 (this task's
own Out of Scope: no new observable). **Diagnostic only, never a
submission prediction**, same caveat TASK-0067 stated for its own holo
run.

**Forward direction**: apo floor-clears 10/25 (40%, matches TASK-0162's
own reported number exactly — a consistency check), holo floor-clears
only 6/25 (24%). 10/25 individual cells flip verdict (7 lose clearance
apo→holo, 3 gain). **Reverse direction**: apo and holo floor-clear the
same total count, 4/25 (16%) each — but not the same 4 cells; 2/25 flip
(1 lose, 1 gain), netting to zero aggregate change.

**Gap magnitude, per-cell, stated explicitly per this task's own
requirement**: mean |gap| is 0.133 (forward) / 0.119 (reverse) — an order
of magnitude *larger* than TASK-0067's own "tiny apo/holo gap" finding
for the bare GNM operator (row 2 above: 0.081/0.061), though comparable
to [[TASK-0153]]'s own already-flagged `dcc_low` complication on
CARDIAC_MYOSIN (gap −0.303, "the opposite of a clean ceiling reading").
Two observables account for most of the largest gaps: **`T_E0_Hnew`**
(transmission on `H_new` at E=0) shows the single largest gap in both
directions (PTP1B forward −0.400, KRAS_G12C forward −0.344, CASPASE7
forward −0.292, PTP1B reverse −0.389, KRAS_G12C reverse −0.209) and
**`dcc_low`** (CASPASE7 reverse −0.411, CARDIAC_MYOSIN forward −0.273) —
extending, not contradicting, TASK-0153's own finding that `dcc_low`
specifically does not get a clean apo/holo ceiling reading.
`ctqw_converged`/`R_eff`/`prs_low` are comparatively closer to TASK-0067's
own "small gap" pattern on most cells (11/25 forward and 18/25 reverse
cells overall have a gap smaller than that cell's own floor-vs-actual
margin), but not uniformly — `ctqw_converged` alone causes KRAS_G12C's
forward verdict to flip (apo 0.590 floor-clearing → holo 0.410, well
below its own floor).

**One-line verdict, per this task's own explicit ask**: this observable
family behaves *differently* from TASK-0067's own precedent — the
apo-vs-holo gap is real and large enough to change which cells clear
their floor, not a diagnostic non-event. Forward direction is measurably
less floor-clearing on holo than on apo (24% vs. 40%); reverse direction
is unchanged in aggregate count but not in which cells. Consistent with
[[TASK-0169]]'s own benchmark-discriminability finding and
[[TASK-0015]]'s Step 2 gate: this program's headline observables are
sensitive to exactly the structural details (apo vs. holo topology) a
robust allosteric signal should arguably be less sensitive to.

Full detail: `.ai/tasks/DONE/TASK-0171-reverse-direction-coupling-test-holo.md`,
`RESULTS/results/tasks/0171_reverse_direction_holo/reverse_direction_coupling_test_holo.json`,
`scripts/reverse_direction_coupling_test_holo.py`.

---

## Mechanism-discriminating plant — partial, target-dependent discrimination, mostly below this project's own certification bar (TASK-0168, 2026-08-04)

**Question**: plant two physically different allosteric mechanisms into
real apo topology and test whether the "directed-channel" observable
family (`ctqw`/`T(E)`) and the "ensemble/mode" family (`dcc_low`/
`prs_low`) detect only the mechanism each is justified on — the
protein-scale generalization of [[TASK-0103]]'s 44-node dumbbell double
dissociation.

**A real structural finding, forced this task to re-scope before any
grid ran**: this project's real-pipeline observables (`ctqw_converged`
on `H_new`, `dcc_low`, `prs_low`, `ground_state_relaxation`/
`mode_coparticipation` as actually called in `run_challenge.py`) are
**exactly plant-invariant** to any weight-only perturbation of `W` —
confirmed directly by reading every construction path
([[TASK-0167.001]]/[[TASK-0167.002]]'s own already-established finding,
re-verified before building on it), not merely "not yet wired." Every
one of them rebuilds its own operator fresh from raw `coords` with a
hardcoded unweighted contact matrix. Only `transmission_from_source` on
a directly-built `hamiltonians.laplacian(W_planted)` responds in the
real pipeline. This task's own observable set was built around that
constraint rather than around it: `T(E=0)` and `time_averaged_
ctqw_converged` applied directly to `laplacian(W_planted)` (matching
[[TASK-0103]]'s own dumbbell-test convention, not a deviation from it),
`ground_state_relaxation` the same way (the dumbbell's own well-tracker
control), and a **new** `dcc_low_from_L` adapter — `lowmode_predictor.
dcc_low`'s exact math, parameterized on an externally-given Laplacian
instead of an internal coords-rebuild (verified bit-identical to real
`dcc_low` on the equivalent unweighted graph before trusting it). Real
`dcc_low`/`prs_low` remain structurally unable to see either plant at
all — no `W` argument exists — and are reported as such, included only
in the pre-plant redundancy matrix, not the live grid.

**Plant B, new** (`allostery.plant.plant_mode`): the mirror image of
`plant_channel` — softens (divides by `1+strength`) every edge crossing
the boundary of `{seed} UNION {target patch}` versus the rest of the
structure, rather than strengthening a path between them. Passes
`assert_confound_orthogonal` on both targets across the full strength
sweep (new regression test added to `tests/test_plant.py`, 6 new tests,
mirroring `plant_channel`'s own coverage).

**Mandatory scale-check (Planned Validation): PASSED, on both targets.**
[[TASK-0103]]'s 44-node double dissociation reproduces at protein scale
using a real diagonal-well construction (not either of this task's two
named mechanisms) plus `plant_channel`: GSR tracks the well (mean AUC
0.996 KRAS_G12C / 0.719 BCR_ABL1) but not the channel (0.559 / 0.508,
chance); CTQW tracks the channel (0.640 / 0.566) but not the well (0.0 /
0.0 on both — a clean anti-correlation, not just "no signal"). Weaker on
BCR_ABL1 than KRAS_G12C but the qualifying direction holds on both.

**Main 2-mechanism grid**: 480 cells, 0 errors (2 targets x 2 mechanisms
x 4 observables x 3 strengths {0,4,16} x 10 seeds — explicit,
stated scope-narrowing from TASK-0167.002's own larger grid: CARDIAC_MYOSIN
dropped, 10 not 20 seeds [this task's own Constraint floor], one CI
method [spatial] and 2 not 3 null specs [scattered+compact], both trims
justified directly by TASK-0167.002's own finding that the dropped
options were statistically indistinguishable from the kept ones).
Certification pipeline (gate1 floor / gate2 CI non-overlap / gate3
permutation null / gate4 Bonferroni, N=3 real-deployment family) reused
unmodified from `positive_control_detection_curve.py`.

**Point-estimate discrimination is real and mostly replicates across
targets for the channel family; the one ensemble-family candidate does
not:**

| Observable | Family | KRAS_G12C (channel: s0→s16 / mode: s0→s16) | BCR_ABL1 (channel / mode) |
|---|---|---|---|
| `T(E=0)` | channel | 0.208→0.698 (rises) / 0.208→0.084 (falls) | 0.474→0.653 (rises) / 0.474→0.002 (collapses) |
| `ctqw_converged` | channel | 0.323→0.692 (rises) / 0.323→0.355 (flat) | 0.372→0.597 (rises) / 0.372→0.330 (flat/falls) |
| `dcc_low_from_L` | ensemble | 0.553→0.340 (falls) / 0.553→0.751 (**rises**) | 0.305→0.348 (flat) / 0.305→0.095 (**falls**) |
| `ground_state_relaxation` | control | 0.181→0.672 (rises) / 0.181→0.107 (falls) | 0.326→0.599 (rises) / 0.326→0.140 (falls) |

`T(E=0)`/`ctqw_converged` (channel family) show a clean, mechanism-specific,
**replicated (2/2 targets)** pattern: rising AUC with channel strength,
flat-to-falling with mode strength — exactly the "detects the mechanism
it's justified on" signature this task set out to test, at the
point-estimate level. `dcc_low_from_L` shows the hoped-for **opposite**
signature (mode-specific rise) cleanly on KRAS_G12C but **does not
replicate on BCR_ABL1** (falls under both mechanisms there, less under
channel) — a genuine, reported-not-forced non-generalization, not a
second confirmed discriminator. `ground_state_relaxation`, run here
*without* an explicit diagonal well (neither named mechanism plants one),
behaves like a de facto third channel-family member on both targets —
its well-tracking behavior (confirmed real, above) is conditional on an
actual energy well being present, which is a real and useful distinction
this task's design surfaced, not assumed in advance.

**Certification (gate1-4): mostly does not clear, extending TASK-0167.002's
own headline finding to a second mechanism.** Under the corrected
(compact-patch) null, P(certified) exceeds 0.30 in only 2 of the 32
(observable x mechanism x target) curves tested (`ctqw_converged`/channel
on BCR_ABL1 at s=16, P=0.30; same cell KRAS_G12C at s=4, P=0.20) and
never reaches the 0.80 LOD bar anywhere in the tested strength range (up
to ~2.6-2.9x baseline conductance for the channel plant, down to
~0.25-0.32x for the mode plant, per the dose-axis calibration below) —
**the real, replicated point-estimate discrimination above does not (yet)
rise to this project's own formal certification standard at physically
modest plant strengths.** This is the same corrected-null power gap
TASK-0167.002 found for the channel plant alone, now shown to apply
across both mechanisms and the new ensemble-family adapter too.

**Dose axis** (`transport.effective_resistance_from_source` on
`laplacian(W_planted)`, mean conductance seed→patch, 3-seed average):
channel plant raises conductance to 2.61x (KRAS_G12C)/2.89x (BCR_ABL1)
baseline at strength=16; mode plant lowers it to 0.253x/0.319x —
reasonably but not perfectly matched in log-magnitude (log-ratio 0.96 vs
1.37 for KRAS_G12C, 1.06 vs 1.14 for BCR_ABL1) at the strengths actually
used, not forced to an exact match.

**Pre-plant redundancy** (Spearman rho, real/unplanted scores, both
targets): `T(E=0)`/`ctqw`/`ground_state_relaxation` (all computed on the
same unplanted `L0`) cluster substantially (rho 0.5-0.9) — largely
redundant with each other pre-plant, unsurprising since all three are
different transforms of the same static operator. `dcc_low_from_L0` and
real `dcc_low` correlate at rho 0.99-1.00 (expected, near-identical
math). **`prs_low` is the one genuinely non-redundant observable in the
full named set on both targets** — rho -0.32 to 0.12 with everything
else, including its own GNM-family sibling `dcc_low`.

**Plant B's own spectral-effect verification (this task's own explicit
"most likely to fail silently" check): real but weak, and does not
replicate cleanly across targets.** KRAS_G12C: same-sign seed/target
co-amplitude on the lowest 5 Kirchhoff modes rises from 1/5 pre-plant to
4/5 post-plant, though the co-amplitude *magnitude* mostly shrinks rather
than grows on the modes that flip. BCR_ABL1: no net improvement (3/5
same-sign both pre- and post-plant, with different modes flipping in
each direction) — the intended "one dominant coordinated low mode"
signature was not cleanly produced on this target. Reported plainly per
this task's own Open Questions anticipation that a clean separation might
not be achievable by construction.

**Verdict (feeds back into [[TASK-0161]]'s effective-multiplicity
framing, as this task's own Intent Contract requires): partially
discriminating, not simply redundant, but weaker and less general than
hoped.** The channel family (`T(E=0)`/`ctqw_converged`) genuinely
detects its own named mechanism and not the other, replicated on both
targets, at the point-estimate level — real mechanistic structure exists,
arguing against treating the observable set as one undifferentiated
number. But: (a) that discrimination mostly does not clear this project's
own formal certification bar at the strengths tested: the register's
"zero confirmed positives" framing is not contradicted by this task, it
is reinforced from a second angle; (b) the one candidate ensemble-family
discriminator (`dcc_low_from_L`) does not generalize across targets; (c)
`dcc_low`/`prs_low` as actually deployed cannot see either mechanism at
all, a structural fact independent of this task's own findings; (d)
`T(E=0)`/`ctqw`/`GSR` are substantially redundant with each other
pre-plant. Net effect on TASK-0161's flat multiplicity budget: **do not
treat the ~40-observable register as fully redundant (real
mechanism-specific structure exists) or as fully independent (the
channel-family trio is highly correlated, and the ensemble family is
mostly structurally blind to this entire class of perturbation) — the
effective number of independent tests depends on which mechanism a real
signal would take, a distinction the current flat budget does not
capture.**

**Cross-reference (found after this section was written, not folded in
above)**: [[TASK-0199]] split its own register-wide redundancy
measurement out of this task's own redundancy checkbox and ran a far
more thorough version — 28 real observable types, 5 targets,
participation-ratio effective rank ~2.6-4.1 of 28 on every target. Read
that task as the authoritative source on register-wide redundancy; this
section's own 7-observable pre-plant rho matrix is a consistent, much
narrower, planted-context corroboration, not a competing measurement.

Full detail: `.ai/tasks/DONE/TASK-0168-mechanism-discriminating-plant.md`
(Done section), `src/allostery/plant.py::plant_mode`,
`scripts/mechanism_discriminating_plant.py`,
`results/tasks/0168_mechanism_discriminating_plant/grid.json`.

---

## fpocket binary drift — root-caused to two machines, each with an unpinned build (TASK-0206, 2026-08-06)

**The problem**: [[TASK-0163]]'s published fpocket AUCs (0.8348/0.8596/
0.5345, KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN — this project's single most-cited
classical-comparator figure, quoted throughout `COMPETENCE_MAP.md`'s
discriminability section and this document's own table above) could not be
reproduced by [[TASK-0200]] (0.7910/0.8618/0.5303) — a real, material shift
on KRAS_G12C (Δ0.044), small on the other two. [[TASK-0200]] ruled out the
pocket label, chain selection, non-determinism, and a parsing bug by direct
check before concluding the vendored binary itself had drifted.

**Root cause, found by checking git identity, not assumed**: `tools/
fpocket/bin/` is gitignored — `git ls-files tools/fpocket/` shows only
`README.md` and `bin/.gitignore` ever tracked; the binary itself is a local
build artifact, never committed. The README's own recipe (`git clone
--branch 4.2.3 ...`) is the only thing version-controlled. [[TASK-0163]]'s
commit (`2655a5d`) was authored under git identity `Bartosz
<chmura.quantum@gmail.com>`; [[TASK-0200]]'s commit (`ca4281e`) under a
different machine's git identity — **two machines, each building its own
independently-compiled, never-pinned fpocket binary**, is sufficient by
itself to explain the drift without any code or data bug. (Raised directly
by the orchestrating user, 2026-08-06 — "the two results were obtained on
two different machines... maybe that is in any way involved in the
outcome" — confirmed correct.)

**The candidate root cause named in this task's own filing (a
[[TASK-0177]] arm64 rebuild event) does not hold up**: `git log --oneline
-- tools/fpocket/bin/fpocket` returns nothing (never tracked, so no rebuild
commit exists to find), and the currently-vendored binary is arm64 Mach-O
on this machine regardless — there is no "before/after" binary to diff.
The two-machine explanation supersedes the single-machine-drift-over-time
hypothesis, not an addition to it.

**The binary's own version banner cannot be trusted as a pin**: running it
prints `fpocket 4.0`, but this build exposes `-P`/`--custom_pocket`, a
flag upstream's own release notes attribute to fpocket 4.1 ("Explicit
pocket definition") — the version string is stale/hardcoded across the
whole 4.x release line (checked directly against `github.com/Discngine/
fpocket`'s tags and release notes, not assumed), not evidence of which
exact tag either machine actually built. SHA256 of the binary's own bytes
is the only unambiguous fingerprint available without instrumenting the
build itself.

**Full root cause not chased further, per this task's own explicit
Constraint** ("if the drift cannot be root-caused within a reasonable box,
say so and pin the current build anyway"): whether the remaining gap is a
genuinely different upstream commit (a stale local clone predating the
README's 4.2.3 pin) or a compiler/toolchain-level floating-point
difference from nominally the same source was not resolved. **Recomputing
on the other machine — the user's own suggestion — would settle this, but
is not achievable from this environment** (this session runs on one
machine only); flagged as an open, actionable item for whoever has access
to the other machine, not something completable here.

**What was pinned**: `tools/fpocket/PROVENANCE.json` (SHA256, hostname,
banner, build recipe, both AUC sets with attribution) + new
`allostery.baselines.fpocket_provenance()` (computes the same fingerprint
for any binary, callable by any future script alongside its own run) +
`tests/test_fpocket_pin.py` — a real-target, network-and-binary-gated
golden-value regression test (`backend/test_analysis.py`'s own real-target
pin convention, [[TASK-0072]]'s cross-tree drift test's own spirit): pins
both the binary's SHA256 and KRAS_G12C's fpocket AUC, ran for real in this
environment (not skipped), passed. A synthetic test directly demonstrates
the failure mode Planned Validation required ("must fail against a
deliberately altered invocation before it passes against the pinned one"):
a binary with different bytes produces a different SHA256 than the pinned
record, confirmed.

**Authoritative set, decided per this task's own recommendation**: the
freshly recomputed numbers (0.7910228108903605 / 0.8617816091954023 /
0.5302794166759435) — reproducible on this machine (re-run fresh by this
task, exact match to [[TASK-0200]]'s own numbers, confirming same-machine
determinism), SHA256-pinned, golden-value-tested. [[TASK-0163]]'s original
numbers are kept on record everywhere they were already cited (no
retraction), flagged as superseded via one callout per document/section
(`COMPETENCE_MAP.md`'s top caveat block, this document's own table above
and discriminability section) — not edited at every individual mention,
per this project's own established convention for exactly this situation
([[TASK-0167.002]]'s identical scope call). **No verdict changes**:
fpocket still beats floor and actual on 2/3 mandatory targets under either
number set — this task changes a magnitude, not a finding.

Full detail: `.ai/tasks/DONE/TASK-0206-fpocket-binary-drift.md` (Done
section), `tools/fpocket/PROVENANCE.json`, `tools/fpocket/README.md`,
`tests/test_fpocket_pin.py`.

---

| 60 | Does each observable family (directed-channel: `ctqw`/`T(E)`; ensemble/mode: `dcc_low`/`prs_low`) detect only the mechanism it is justified on — planting a stiff channel vs. a new correlated-mode perturbation into the same real apo topology, the protein-scale generalization of [[TASK-0103]]'s 44-node dumbbell double dissociation? | **resolved 2026-08-04: partially discriminating, not simply redundant, but weaker and less general than hoped, and mostly below this project's own certification bar.** Forced re-scope first: real-pipeline observables (`ctqw_converged` on `H_new`, `dcc_low`, `prs_low`) are exactly plant-invariant to any weight-only perturbation (re-confirmed, [[TASK-0167.001]]/[[TASK-0167.002]]'s own finding) — scored instead on `laplacian(W_planted)` directly, [[TASK-0103]]'s own dumbbell convention. Mandatory scale-check **passed on both targets** (GSR tracks a real well, AUC 0.72-1.00; CTQW does not, AUC 0.0; reciprocal for a channel plant). Main grid (480 cells, 0 errors, 2 targets): `T(E=0)`/`ctqw_converged` (channel family) show a clean, **replicated (2/2 targets)** mechanism-specific point-estimate response (rising with channel strength, flat/falling with mode strength). New `dcc_low_from_L` adapter (ensemble family, `dcc_low`'s exact math on an externally-given Laplacian) shows the hoped-for opposite (mode-specific) signature on KRAS_G12C only — **does not replicate on BCR_ABL1**. Under this project's own corrected-null certification pipeline, almost nothing reaches 80% detection power at the strengths tested — real point-estimate discrimination mostly does not (yet) clear the formal bar, extending [[TASK-0167.002]]'s own finding to a second mechanism. Pre-plant: `T(E=0)`/`ctqw`/`GSR` substantially redundant (rho 0.5-0.9); `prs_low` the one genuinely non-redundant observable measured. Plant B's own spectral verification: real but weak, does not replicate across targets. Feeds back into [[TASK-0161]]: neither "fully redundant" nor "fully independent" — effective multiplicity depends on which mechanism a real signal would take. | [[TASK-0168]], [[TASK-0103]], [[TASK-0167.001]], [[TASK-0167.002]], [[TASK-0161]], [[TASK-0145]], [[TASK-0149]] |
| 61 | Does ranking residues by *minimum control energy* `E_i` to steer the CTQW's population from the active-site seed to each residue (GRAPE optimal control, a proximity-orthogonal-by-construction observable per this task's own re-scoping from "control the walk" to "read the cost of control") separate allosteric residues from distance, beating the classical PRS baseline (Atilgan & Atilgan 2009)? | **resolved 2026-08-04: no — a clean, decisive negative on all 3 mandatory targets, properly powered after catching and fixing a real instrumentation bug mid-run.** New `allostery.control_effort` (GRAPE, Khaneja et al. 2005, citation verified against the live article; control channels restricted to the active-site seed residues only, Implementer's call — see module docstring for the 3-part justification). Correctness gated before any real data: analytic gradient matches finite-difference to 1e-4; Trotterized propagation matches exact `scipy.expm` to 1e-3; plain gradient descent oscillated rather than converged on a real target (caught by instrumenting per-iteration fidelity, not assumed) — switched to Adam, confirmed smooth convergence. **Synthetic dumbbell gate passed**: on two identical-topology, identical-hop-distance chains differing only in edge weight, `E_i` correctly ranks the strongly-coupled chain's end below (cheaper to reach than) the weakly-coupled twin — this observable tracks coupling strength, not just distance, unlike a naive proximity floor. **Pre-registered kill-switch passed** on KRAS_G12C (rho=0.56 vs. distance, well under the 0.85 STOP bar) -- proceeded to full scoring. **Instrumentation bug caught mid-pipeline**: a single fixed horizon `T=15` (calibrated on KRAS_G12C, N=169) left BCR_ABL1/CARDIAC_MYOSIN's feasible fraction near zero (1/451, 1/704) — almost every residue collapsed to the same "infeasible" sentinel score, mechanically forcing stratified AUC to exactly 0.5 in every single shell by ties, a scoring artifact, not a physical result (caught by exactly this project's own "0.5 everywhere is suspicious" convention). **A "more physical" fix was tried and rejected before settling on the actual one**: this project's own established gap-based horizon rule (`propagators.min_adequate_t_max`, rows 36/39, built for exactly the "one time constant regardless of energy scale" failure mode) predicts `T~1/gap`; KRAS_G12C and BCR_ABL1's `H_new` spectral gaps are nearly identical (0.0364 vs 0.0374), so that rule prescribes nearly the same T for both and, checked directly, still leaves BCR_ABL1 at 2/91 feasible on a subsample — the degeneracy survives it. T was instead found per target by a label-blind empirical search (feasible *fraction* on a subsample, blind to which residues are pocket, targeting a comparable range across targets) — `T=15*(N/169)` reports where that search landed, not a derived physical law; feasibility here evidently depends on more than `H_0`'s spectral gap alone (plausibly seed/N coverage fraction, which varies far more across these targets: 10.7%/5.8%/2.6%). `F` lowered from 0.5 to 0.4 uniformly. This restored healthy feasible fractions (17%, 21%, 6%) before re-running. **Final result, properly powered**: distance-stratified mean AUC at chance on all 3 targets (KRAS_G12C 0.501, BCR_ABL1 0.404, CARDIAC_MYOSIN 0.474), permutation-null p-values 0.48/0.99/0.71 (none significant; BCR_ABL1 is actually *worse* than its own null, p=0.99). **T/F sensitivity check** (task's own Constraint): residue *rankings* are stable and reproducible across 3 different (T,F) choices on KRAS_G12C (Spearman rho 0.73-0.89, all p<1e-28) while stratified AUC stays at chance regardless (0.477-0.501) — confirms the null is a real absence of signal, not hyperparameter noise. Classical PRS baseline (`prs_low`, already in the register) is itself weak/mixed on this same stratified lens (0.51/0.25/0.83) — not a case of a strong classical baseline this observable simply failed to beat. **ASD unseen-set scoring not run**, per the task's own pre-registered gate ("if the mandatory set clears") — it did not. Single-excitation-subspace, classically simulable throughout; a negative here is a negative *observable* finding, not evidence against a quantum speedup claim (none was made). | [[TASK-0156]], [[TASK-0094]], [[TASK-0112]], [[TASK-0123]], [[TASK-0130]] |

| 62 | [[TASK-0163]]'s published fpocket AUCs (the register's single most-cited classical comparator) could not be reproduced by [[TASK-0200]] on a different machine — is the vendored binary itself the cause, and can it be pinned? | **resolved 2026-08-06: yes, root-caused to two machines each building their own unpinned local binary — confirmed via git identity, not assumed — and pinned going forward.** `tools/fpocket/bin/` is gitignored, only the build recipe is version-controlled; [[TASK-0163]]'s commit used git identity `chmura.quantum@gmail.com`, [[TASK-0200]]'s a different machine's identity. The binary's own version banner ("fpocket 4.0") is stale/hardcoded across the 4.x line (this build exposes a 4.1-era flag), not a trustworthy pin — SHA256 is. New `tools/fpocket/PROVENANCE.json` + `allostery.baselines.fpocket_provenance()` + `tests/test_fpocket_pin.py` (real-target golden-value test, ran for real, passed). Authoritative set: the freshly recomputed numbers (reproduced twice on this machine). Full root cause (different upstream commit vs. compiler/arch difference) not chased further, per this task's own explicit sanction to pin without full root-cause; recomputing on the other machine, as directly suggested, would settle it but isn't achievable from this environment. No verdict changes on either number set. | [[TASK-0206]], [[TASK-0163]], [[TASK-0200]], [[TASK-0177]], [[TASK-0072]] |

| 63 | [[TASK-0199]] measured the observable register's effective rank at ~3 of 28 — what are the three axes, do they match the pre-hypothesized proximity/channel/ensemble split, and are they stable across targets? | **resolved 2026-08-06: PC1 and PC2 are stable and nameable, PC3 is not; the pre-hypothesis is refined, not confirmed.** `scripts/label_principal_components.py` (new, reuses [[TASK-0199]]'s own tested `observable_effective_rank.py` functions directly, adds only eigenvector capture; wiring-checked against [[TASK-0199]]'s stored numbers to 1e-6 on every target before interpreting anything). **PC1 = the 15-member Hamiltonian-occupancy family on all 5 targets (46.5-60.6% of total variance)** — not a separable "proximity" axis: `-hop`/`-euclid` land on this same axis in 7/10 target-confound pairs, hand-verified against raw correlations (`occ_H1`/`occ_H6` rho=0.73, `occ_H1`/`R_eff` rho=0.80). **PC2 = `ensemble_mode`-labelled on 4/5 targets (7.9-10.5% var), but driven specifically by `prs_low`**, not the family as a whole — `prs_low`/`conformational_entropy` rho=0.74 while `prs_low`/`dcc_low` rho=**-0.11**, independently confirming [[TASK-0168]]'s own finding that `prs_low` is the register's one genuinely non-redundant observable (two unrelated methods, static PCA here vs. dynamic plant-response there, agree). **PC3 does not survive across targets**: 3 different dominant families in 5 targets, no majority. **`channel_transport` (the pre-hypothesized second axis) never reaches PC1 anywhere** and only reaches PC2 on 1/5 targets — real and replicated under active perturbation ([[TASK-0168]]) but not a dominant source of variance in passive, unperturbed data; a mechanism's detectability under intervention and its footprint in static correlational structure are shown to be different properties. Full agreement/disagreement table vs. [[TASK-0168]] and quotable verdict sentence for [[TASK-0184]]: `.ai/tasks/DONE/TASK-0207-label-the-principal-components.md` (Done section). | [[TASK-0199]], [[TASK-0168]], [[TASK-0184]], [[TASK-0161]] |

| 64 | [[TASK-0201]]'s PTP1B `dcc_low` (k=10) positive — the program's one corrected-null survivor — was never tested by [[TASK-0200]]'s conditional-on-fpocket analysis or [[TASK-0168]]'s mechanism-discrimination grid, both of which stopped at the 3 mandatory targets. Does either test explain it? | **resolved 2026-08-06: the strongest possible reading is ruled out; the rest is underdetermined by available power, not resolved.** [[TASK-0168]]'s grid, run on PTP1B (300 cells, 0 errors, wiring-checked against its own stored KRAS_G12C cell bit-for-bit, `dcc_low_from_L` re-confirmed bit-identical to real `dcc_low` at both k=20 and k=10 on PTP1B's own topology): at the exact k=10 that produced the survival, `dcc_low` shows a **channel-type** response to synthetic perturbation (AUC rises 0.337→0.714 with channel-plant strength, falls 0.337→0.176 with mode-plant strength) — the opposite of the mode/ensemble signature the observable is named for and that partially held on KRAS_G12C. This decisively rules out "a real, mechanistically-supported, ensemble-explained positive" (the strongest of 4 pre-registered outcomes). [[TASK-0200]]'s own script, extended to PTP1B (+CASPASE7, `FAMILY_SIZE` 18→30, `alpha=0.05/30`, wiring-checked: KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN fpocket AUCs reproduced byte-identical) is **inconclusive, not negative**, on the conditioning question: every representative observable and the k=10 replication cell is underpowered at all 4 pre-registered band widths (2, 0, 0, 2 positives) — fpocket itself performs only near chance on PTP1B (AUC 0.42, vs. 0.79-0.86 on the mandatory set), so too few real-pocket residues land inside its own detected-cavity population to test at all. Net: whether the positive is real-but-mechanistically-unexplained or a pure statistical survival remains open. Also flagged, not fixed: both legs test this cell under `nulls.compact_patch`, not the `graph_walk_patch_matched` null [[TASK-0201]]'s own survival was actually certified under. | [[TASK-0203]], [[TASK-0201]], [[TASK-0200]], [[TASK-0168]], [[TASK-0199]], [[TASK-0184]] |

| 65 | [[TASK-0181]] Phase B's own pre-stated falsification criterion #1 (classical rotamer packing must open an fpocket-druggable cavity more often than naive greedy choice, on real windows, before any quantum formulation is proposed) — never run. Does it pass or close the route? | **resolved 2026-08-06: closes the route, 0/2 targets pass (bar: 2/2), [[TASK-0204]].** Vendored EvoEF2 (MIT, `tools/evoef2/`, minimally patched to expose greedy/random single-pass rotamer choice alongside its own shipped SA optimizer — no invented energy function, criterion #3). Real candidate windows (12 pocket-proximal residues each, `_select_window`), real full-atom repacking, real `fpocket` druggability scoring (criterion #3, no geometric proxy) on the repacked structures. **KRAS_G12C**: native sanity itself misses the druggability bar at this window (drug=0.001); greedy misses; optimized 0/8; random 0/8. **BCR_ABL1**: native sanity and greedy both hit (drug=0.566/0.537); optimized **0/8**, random 0/8 — SA-optimized repacking scored *worse* than the naive greedy baseline, the pre-registered "ceiling case" rule applying explicitly (greedy already hits, optimized doesn't exceed rate 1.0 → fail, not an automatic pass). Plausible reading, not asserted as proven: minimizing the packing objective (self + pairwise energy across the window and EvoEF2's own automatically-included repack shell) trends toward *tighter* side-chain packing, a different target than opening a cavity fpocket scores independently — nothing in the run points to a mis-executed optimizer. **Per criterion #1's own stated consequence and Phase A's binding precedent, no quantum formulation is built for this objective** — rare-event-rate measurement (gated on criterion #1 passing) does not apply. Three real, unrelated tooling bugs were found and fixed en route (documented in the task's own Done section, not this table): a PDB chain-letter-reentry (A-B-A) parsing bug in EvoEF2's own `StructureConfig`, a prody boolean-mask indexing incompatibility, and an EvoEF2 SIGSEGV specific to invoking the binary via an absolute `argv[0]` path.  **[RETRACTED 2026-08-06, [[TASK-0204]] reopened by the Reviewer thread — the route is UNTESTED, not closed.]** Three independent defects, each sufficient alone. (1) The gate `opt_rate > (1.0 if greedy_hit else 0.0)` demanded a value `opt_rate` cannot attain (it is a fraction of 8 trials, max 1.0), so on any target whose greedy hit — BCR_ABL1 did — it could not return `pass` for ANY data, including a perfect 8/8; the bar required 2/2, so criterion #1 was unfalsifiable in the positive direction before a trial was scored. (2) **There was no positive control**: only the apo structure was ever scored, where a cryptic pocket is closed by definition. Built and run since (`task0204_positive_control.py`): the holo positive control **passes on KRAS_G12C (overlap 1.000, drug 0.886) and FAILS on BCR_ABL1 (drug 0.356 < 0.5 bar, i.e. lower than that target's own apo at 0.566)** — every BCR_ABL1 number above is uninterpretable. (3) The conjunctive criterion is dominated by an overlap leg that **any** repacking destroys: on KRAS_G12C holo, where the cavity is definitively open, repacking drops overlap 1.000 → 0.417 (greedy) / 0.250 (SA median) while druggability stays 0.827–0.941 — refuting this row's own "SA trends toward tighter packing" reading, since the **random** arm minimizes nothing and collapses identically. Supporting: total runtime 73.3 s of which 33.6 s is `sleep()`; no seed control; P(0 of 8) = 0.52/0.83 under the observed per-leg marginals, so 0/8 is the modal outcome under any hypothesis. **REFORMULATED the same day — and the corrected question closes this route far more decisively than the biological proxy could.** Raised by the orchestrating user: even a clean PASS on criterion #1 would not support a quantum route if the instance solves classically in seconds. Side-chain packing on a fixed backbone is a pairwise MRF, so exact minimization costs `O(m*n^(tw+1))` — **treewidth**, not variable count — not the naive `O(n^m)` Phase B's own 180-qubit estimate is built on. Measured on 4 targets, m=8-80, interaction cutoff swept (`task0204_packing_hardness.py`), then **validated by exact solution** (bucket elimination, correctness-gated against brute force on 3 enumerable instances, match to 1e-9; `task0204_exact_solve_validation.py`). At m=12 (a druggable pocket) with n=15: treewidth 2-5, and the **exact global optimum is found in 0.001-0.159 s wall clock** against a naive search space of 1e14.1 — nine to eleven orders of magnitude of headroom, on a laptop. The `1e14` figure is an illusion created by counting variables instead of measuring the interaction graph; the qubit estimate is a faithful encoding size and is not evidence of hardness. **Route closed on complexity grounds at the biologically relevant scale** — same argument shape the register already accepts for Grover/HHL/QML and single-particle CTQW. Honest boundary, stated not buried: treewidth does NOT saturate (9-23 at m=80, exact cost 1e26-1e30), so a genuine hard regime exists — but only at 50-80+ residue windows, i.e. most of a domain, not a pocket. Phase B's own m=8-15 scope sits entirely inside the tractable regime. Full retraction and reformulation record, corrected `criterion_1_verdict()`, and the requirements for a valid rerun: [[TASK-0204]]'s own "Reopened" section. | [[TASK-0181]], [[TASK-0185]], [[TASK-0187]], [[TASK-0163]], [[TASK-0206]] |

| 66 | Every cryptic-pocket experiment in this register has assumed the apo structure's pocket is genuinely *closed* and the holo's genuinely *open* — never checked, until [[TASK-0169]] found BCR_ABL1's apo isn't cryptic at all. Does the assumption hold register-wide? | **resolved 2026-08-07: no — only 2 of 7 real-drug-ligand targets are validated ([[TASK-0209]]).** Scope: of `targets.yaml`'s 14 entries, 7 have a genuine small-molecule `drug_ligand` (the other 6 have none, or (GROEL_SUBUNIT) a protein ligand its own config flags as not applicable — excluded, not scored). Reused [[TASK-0204]] (reopened)'s own positive-control ladder (`holo_native`/`holo_greedy`/`holo_optimized`/`apo_native`, ligand-stripped, `fpocket`-scored) on all 7, pre-registering the VALID rule blind, before running 11 of the 13 targets: `NOT apo_native_hit AND holo_native_hit`, reusing [[TASK-0204]]'s own hit criterion, not a new one. **VALID (2/7)**: KRAS_G12C (apo drug=0.001, holo=0.886), PTP1B (0.046→0.757). **INVALID (5/7)**, in three distinct failure modes: (a) apo scores *more* druggable than holo, an inverted contrast — BCR_ABL1 (explained: `MYR` 3.47 Å from the pocket, [[TASK-0169]]'s own finding, reused as a known-answer check here), GLUCOKINASE (a **new** finding: unexplained `MRK` 2.45 Å from the pocket, same shape as MYR), CASPASE1 (apo hit=0.679, **no** HETATM found nearby — an intrinsically open pocket, not an occupancy artifact); (b) no contrast either direction and the holo positive control itself misses — CARDIAC_MYOSIN, CASPASE7 (window/bar limitation, not chased further). **The construction leg (build a synthetic closed instance from a verified-open holo) could not proceed for any of the 5 INVALID targets**: all 5 have `holo_native_hit=False`, so none has the verified-open reference the method requires to round-trip against — reported as a finding (the construction leg's own precondition fails register-wide, not just for BCR_ABL1), not forced through. **Register-wide exposure**: 2 of the register's 3 *mandatory* targets (BCR_ABL1, CARDIAC_MYOSIN) are INVALID — only KRAS_G12C is a validated cryptic-pocket contrast among the mandatory set. Does not retroactively invalidate individual measured numbers (most observables, e.g. GNM/CTQW-family, don't depend on fpocket-druggability contrast) but means "passes on 2/3 (or 3/3) mandatory targets" cannot be read as "2 (or 3) genuine cryptic-pocket benchmarks" without checking which. Real tooling bug found and fixed en route (in this task's own script, not edited into [[TASK-0204]]'s file, which is under another thread's active claim): `_write_full_atom_with_window_chain`'s hardcoded window-chain-letter 'B' collides with any target whose own chain is already 'B' (CARDIAC_MYOSIN's holo), silently relabeling the entire structure as "window." | [[TASK-0169]], [[TASK-0204]], [[TASK-0210]], [[TASK-0208]] |

| 67 | [[TASK-0199]]'s ~3-axis effective rank was measured over 28 observables that are all functions of a **single static graph**. Is an observable computed across an **ensemble** of realized contact graphs independent of that span, or does it land inside it? | **resolved 2026-08-12: inside the existing span, 5/5 targets — not a new axis.** `ensemble_contact_covariance` (new, `scripts/task0211_ensemble_graph_observable.py`): per-residue \|Pearson\| correlation, across a legal closed-form ANM-equipartition ensemble (`shortcuts.equipartition_ensemble`/`msf_cross_check`, [[TASK-0187]]'s own validated sampler, no trajectory), between the seed's and residue *j*'s per-sample contact-graph **degree** — genuinely rebuilt discrete graphs per sample, not a continuous-displacement reduction, unlike `dcc_low`'s single-Kirchhoff-eigendecomposition construction. MSF gate passed on all 5 targets; split-half reproducibility passed everywhere (rho 0.718-0.786) at 2000 samples (3/5 targets) or 4000 (the 2 largest, N=704/461). Baseline 28-observable rank reproduced [[TASK-0199]]'s own published numbers exactly (wiring check) before adding anything. Pre-registered "new axis" rule: real observable's rank-delta must exceed a matched-variance noise column's own delta, on every target. **It did not, on any of the 5** — delta_real (0.115-0.221) was smaller than delta_noise (0.180-0.273) every time; duplicate/random controls on the 29-column matrix still behaved correctly. Explanation, not just a negative: Spearman rho vs. `dcc_low` alone is 0.257-0.339 on every target, flat across targets (PTP1B not distinguished from the other 4) — real, modest, positive overlap with the register's one closed-form "communication through collective structure" observable, consistent with sharing underlying signal rather than being an independent view. **[[TASK-0199]]'s "~3 axes" headline (refined by [[TASK-0207]] to "~2 stable axes plus noise") is unweakened** — rank does not move from ~3 toward ~4 on any target. Consumes zero multiplicity budget (observable-vs-observable only, no label read), per this task's own Constraint. Closes contact co-variance as a candidate; edge persistence and ensemble-averaged propagation (named alternatives) remain untested, not owed by this task's own scope. [[TASK-0187]]'s hop-distance shortcut is the only other ensemble-graph observable tested to date, also negative — 2 of the class's named candidates are now dead. | [[TASK-0199]], [[TASK-0207]], [[TASK-0187]], [[TASK-0201]], [[TASK-0184]] |
| 68 | [[TASK-0204]] closed fixed-backbone rotamer packing on complexity grounds, but only while the interaction graph is fixed — does the real apo→holo change move the backbone (closure does not transfer) or only side chains (it does)? | **INCONCLUSIVE, 2026-08-07/12 — the original `CLOSED` verdict is retracted.** The compound AND-gate had one leg that could not fire (the frustration signature requires `joint < 0`; every `joint` was large and positive because rigid holo rotamers on an apo backbone always clash) and another that was confounded (the RMSD attribution credits backbone for displacement it merely *carries*). Recompute with post-transplant relaxation removes **~97%** of the measured energy and leaves **3 of 4 targets not evaluable** — including PTP1B's +16.2%, the number [[TASK-0212]] was filed to chase and which is now closed as invalidated. Dihedral-space attribution reverses the verdict on all 4 (pocket backbone-share 0.205–0.374, and *higher* distally on 3/4 — side-chain change is pocket-concentrated). The two metrics together exclude **both** simple closures: the backbone moves little but is load-bearing. | [[TASK-0208]], [[TASK-0204]], [[TASK-0210]], [[TASK-0212]] |

| 69 | [[TASK-0209]] found only 2/7 targets pass its apo-closed/holo-open contrast. Can re-selecting the *apo* deposition alone (Leg A of a two-leg protocol) raise that count, for the 5 INVALID targets? | **resolved 2026-08-13: no — Leg A recovers 0/5; the count stays 2/7. Leg B (new proteins) is now confirmed necessary ([[TASK-0214]]).** Known-answer check passed first (KRAS_G12C incumbent apo re-scored through this task's own pipeline, exact match to [[TASK-0209]]'s number). UniProt-seeded candidate search (`backend.discovery.same_protein_entries`) found 4-32 alternative X-ray depositions (≤2.5 Å) per target; a chem_comp-driven exclusion filter (built and tested against the two known culprits *before* running anything: `classify_ligand("MYR")` returns `("solvent/ion", False)` — the register's own classifier would NOT have caught BCR_ABL1's own myristate, so the filter calls `_is_aliphatic_additive` directly instead of trusting that top-level category) found real, clean candidates whose own native structure is closed for 4/5 targets (BCR_ABL1, CARDIAC_MYOSIN, GLUCOKINASE, CASPASE1); CASPASE7 failed at the window-numbering-match step for every candidate. **A real bug was caught before reporting a result**: the first pass scored candidates as "recovered" from the new apo's own hit status alone and reported 6/7 — wrong, because the pre-registered VALID rule needs `holo_native_hit=True` as well, and checking [[TASK-0209]]'s own stored data directly shows **`holo_native_hit=False` on all 5 INVALID targets, without exception** (including BCR_ABL1/GLUCOKINASE/CASPASE1, which this task's own pre-registration table had implicitly assumed had a working holo side). Leg A only touches the apo side, so it cannot cross a bar the holo side is independently failing. Not a wasted leg: it isolates the real blocker as the holo-side/window/druggability-bar problem ([[TASK-0204]] reopened's own D2 finding, for BCR_ABL1 specifically) rather than "no clean apo exists" — which does exist, for 4 of 5 targets. | [[TASK-0209]], [[TASK-0204]], [[TASK-0169]] |
| 69 | Every cryptic-pocket experiment in this register assumes the apo pocket is closed and the holo pocket open. Does that contrast actually hold, per target? | **resolved 2026-08-12: no — only 2 of 7 targets are VALID (KRAS_G12C, PTP1B), and 2 of the 3 mandatory targets are INVALID.** Blind pre-registered rule, known-answer checks passed. Three distinct failure modes: an unexplained bound HETATM holding the "apo" pocket open (BCR_ABL1 `MYR`; **GLUCOKINASE `MRK`, new**), an inverted contrast with nothing nearby to explain it (CASPASE1 — intrinsically open, not occupied), and no contrast at all because the holo positive control itself misses (CARDIAC_MYOSIN, CASPASE7). The construction leg was blocked for all 5 by its own precondition — `holo_native_hit=False` everywhere, so there is no verified-open reference to build from. For druggability-contrast-dependent claims the mandatory-3 gate has been running at **1/3 validated coverage**. | [[TASK-0209]], [[TASK-0169]], [[TASK-0204]] |
| 70 | Is trajectory-free **coupled** backbone+rotamer apo→holo search hard — the gap between [[TASK-0204]]'s fixed-graph closure, [[TASK-0185]]'s backbone-only closure, and single-particle CTQW? | **tentatively OPEN, weakly supported, 2026-08-12 — deliberately not handed to [[TASK-0183]].** The firewall check (objective must prefer the true holo) passes on only 2/4 targets, independently reproducing [[TASK-0209]]'s verdict from a different direction; CASPASE1/GLUCOKINASE invert and are uninterpretable. On the 2 evaluable targets, 0 of 2 restarts reached the holo basin (best scores 0.47/0.29 vs true holo 0.89/0.76). Reads OPEN by the pre-registered threshold, but n=2 restarts on n=2 targets, and the CLOSED condition ("≥3 of 4 targets") assumed 4 evaluable ones. The budget was honored as pre-registered despite the sizing calibration proving ~10× pessimistic — no outcome-contingent inflation. **SUPERSEDED 2026-08-13 ([[TASK-0213]]): CLOSED at adequate n — 13/65 restarts succeed on KRAS_G12C, 0/65 on PTP1B.** | [[TASK-0210]], [[TASK-0208]], [[TASK-0209]], [[TASK-0204]], [[TASK-0185]] |
| 71 | Is [[TASK-0210]]'s "tentatively OPEN" verdict on coupled backbone+rotamer search real, or an artifact of n=2 restarts? | **resolved 2026-08-13: an artifact — the route is CLOSED.** Re-run at a pre-registered 65 restarts x 25 iterations/target (budget fixed by a cost calibration on this task's own candidate files, not revised after any score; success bar and firewall inherited verbatim from [[TASK-0210]]). **KRAS_G12C succeeds on 13 of 65 restarts (20%)**; at that rate 0/2 occurs ~64% of the time, so TASK-0210's negative was fully consistent with an easy instance. **PTP1B: 0 of 65**, and its entire best-score distribution is capped at 0.397 — below the 0.5 bar and far below its own true holo 0.757, so not a near-miss. Trajectory diagnostics (pre-registered "regardless of verdict") show the anneal was **not** the binding constraint: only 12-25% of restarts were still improving in the final 20% of iterations, median best reached by iteration 9-15 of 25 — restart count was the right dimension to raise. **This closes the last OPEN quantum-advantage route in the register.** Whether PTP1B is genuinely harder or its objective/window is mis-specified is **not decidable at n=2 valid targets** ([[TASK-0209]]) and is stated as unresolved. | [[TASK-0213]], [[TASK-0210]], [[TASK-0209]], [[TASK-0204]] |

| 72 | [[TASK-0214]] confirmed re-selecting the *apo* deposition alone (Leg A) cannot raise TASK-0209's 2/7 valid-instance count — the holo side blocks all 5 INVALID targets regardless. Can sourcing genuinely *new* proteins (Leg B) do better? | **resolved 2026-08-13: yes — 6 new VALID pairs across 4 distinct proteins, revised count 8/13 ([[TASK-0215]]).** RCSB full-text search ("allosteric inhibitor"/"activator"/"modulator", X-ray, ≤2.5 Å) pooled to 188 unique entries across 28 UniProts, this register's existing 14 targets excluded before scoring. Pocket window derived from each holo candidate's own drug-ligand binding site (`rcsb.ligands_and_sites`), not a curated label — sanity-bounded to 6-20 residues. Most candidates were eliminated at the holo-native-hit step itself (a ligand-derived window is not automatically `fpocket`-druggable, e.g. one candidate scored 0.029 despite a geometrically correct window) — real selectivity, not a rubber stamp. **6 pairs survived the full pipeline** (apo closed, holo open, [[TASK-0209]]'s VALID rule verbatim, TASK-0214's own exclusion filter reused unchanged): TEM-1 β-lactamase (2 ligands), farnesyl diphosphate synthase, AMPA receptor GluR2 (2 ligands, one being **aniracetam** — a well-known published AMPA positive allosteric modulator), kainate receptor GluK1. Every recovery's entry title was cross-checked *after* scoring (never used to select candidates) and independently confirms "allosteric" in every case — a precision check on the full-text seed, not a guarantee of recall (systems using different phrasing were not searched). **Honest count**: 2 proteins each contributed 2 pairs (different ligand/apo depositions of the same protein) — reported as 4 new proteins / 6 new pairs, not inflated to "6 new proteins." Candidate additions only: none promoted into `targets.yaml`, no register cell re-run against them — that decision is left open. | [[TASK-0214]], [[TASK-0209]], [[TASK-0169]] |

## Spectrum-preserving Hamiltonian reduction — Schur beats the existing Louvain baseline, Krylov breaks sharply at the active-site size (TASK-0172, 2026-08-14)

**Question**: `coarse.coarse_grain`'s existing Louvain/spectral community
merging is lossy and uncontrolled — it drops every diagonal potential
term before coarse-graining and has no fidelity metric at all. The
challenge statement requires proof that coarse-graining "retains the
essential topological signal." Does a controlled, spectrum-preserving
reduction (Krylov subspace projection; Löwdin/Feshbach-Schur
partitioning) actually do better, and where does the ranking break?

**Citations verified before building** (this task's own explicit
Constraint): Löwdin 1962, *J. Math. Phys.* 3(5), 969-982 — confirmed.
Feshbach 1962, *Ann. Phys.* 19(2), 287-313 — confirmed. Novo, Chakraborty,
Mohseni, Neven & Omar 2015, *Sci. Rep.* 5, 13304 — confirmed, and its own
"invariant Krylov subspace generated from a seed node" construction is
exactly what this task builds.

**New `allostery.reduce`**: `krylov_basis` (direct matrix powers + QR,
not the textbook three-term Lanczos recurrence — the same invariant
subspace, a deliberate simplification justified by scale and verified
empirically, not just asserted equivalent) and `schur_complement`
(Löwdin/Feshbach effective operator at a fixed reference energy E=0.0,
matching `transport.transmission_from_source`'s own DC-limit convention,
with the same `eta_reg`-style regularization). Both diagonal-retaining
(unlike `coarse._graph_weights`). `lift_krylov_eigvecs`/
`lift_schur_eigvecs` embed the reduced operator's own eigenvectors back
into full residue space so `propagators.time_averaged_ctqw_converged`
(already accepting precomputed `(w, v)`, reused unmodified) can score
them exactly like the full system. 17 new tests (`tests/test_reduce.py`):
orthonormality, exactness when the subspace is provably the whole space,
exactness of the Schur lift at a planted eigenvalue, honest degradation
away from the reference energy (a real, nonzero residual, not just an
exactness claim), and the dumbbell synthetic gate (TASK-0103's own
fixture) confirming both methods preserve a planted long-range coupling
signal a naive Louvain merge is not guaranteed to.

**A structural finding surfaced while testing, not assumed going in: a
block-Krylov seed of `n_seed` residues consumes `n_seed` Ritz dimensions
per round-robin power step.** At this project's real active-site sizes
(18-26 residues) and the ~12-16 node NISQ budget `coarse.py`/
`ALGORITHM_REGISTER.md` §H both target, **the seed block alone is at or
above the entire compression budget on all 3 mandatory targets** —
before any distal, potentially pocket-relevant structure can be reached
at all.

**Real-target retention report** (KRAS_G12C N=169/n_active=18, BCR_ABL1
N=451/n_active=26, CARDIAC_MYOSIN N=704/n_active=18; compression targets
m ∈ {10,14,18,24,32,50}, explicitly bracketing each target's own
active-site size; three axes — spectral Ritz error, Bhattacharyya
occupation fidelity, Spearman rho + AUC/P@5 delta against the real
pocket label — all three methods scored identically, Louvain via a
corrected per-member-normalized broadcast, a real bug caught directly:
an early version produced Bhattacharyya coefficients above 1, impossible
for two genuine probability distributions, from copying rather than
dividing a cluster's mass across its members):

| Target | Krylov (block-seed, m≤n_active) | Krylov (m>n_active) | Schur | Louvain (existing baseline) |
|---|---|---|---|---|
| KRAS_G12C (full AUC 0.619) | rho=NaN, ΔAUC=-0.119 (constant, uninformative) | rho 0.36→0.72, ΔAUC mostly negative | ΔAUC **+0.038 to +0.148** (every m) | ΔAUC **-0.307** (constant, worst) |
| BCR_ABL1 (full AUC 0.575) | rho=NaN, ΔAUC=-0.075 | rho 0.30→0.58, ΔAUC still negative | ΔAUC **-0.080 to -0.194** (Schur's one losing target) | ΔAUC -0.415 to **+0.202** (erratic, rho negative at m=10) |
| CARDIAC_MYOSIN (full AUC 0.563) | rho=NaN, ΔAUC=-0.063 | rho 0.23→0.47, ΔAUC still negative | ΔAUC **+0.022 to +0.103** (mostly positive) | ΔAUC -0 to +0.297 (rho negative at m=10,14) |

**Block-seed Krylov breaks sharply, not gradually, at m<=n_active on all
3 targets** — this is the direct, decisive answer to this task's own
"report the compression ratio at which the ranking breaks" ask. Below
that threshold the reduced occupation is exactly constant on every
non-seed residue (Spearman rho undefined, AUC exactly 0.5) because the
seed block's own power-0 vectors already exhaust the requested budget —
not a smooth degradation curve, a hard floor. **Confirmed to be a
block-seed artifact, not a limitation of Krylov subspace projection
itself**: a supplementary check seeding from a single representative
active-site residue (matching Novo et al.'s own single-seed framing)
reaches rho=0.56, AUC=0.612 at the identical m=10 KRAS_G12C's block-seed
version failed completely on — closely tracking that single seed's own
full-system reference (0.662). The project's own established
multi-residue incoherent-mixture seeding convention (TASK-0118) is what
creates the failure at realistic active-site sizes, not the method.

**Schur-complement reduction beats the existing Louvain baseline on
2 of 3 targets, decisively on KRAS_G12C** (positive ΔAUC at every tested
m, vs. Louvain's constant -0.307 — Louvain actively destroys ranking
information there) **and is not universally better** — it loses to the
full system on BCR_ABL1 specifically (ΔAUC consistently negative),
reported as a real, unforced cross-target inconsistency, not smoothed
into a single clean verdict. Schur's spectral error is exact (~0.01) at
low m but grows large (up to 5.05) for Ritz values far from the E=0
reference energy — the same "energy-independent effective Hamiltonian"
approximation limit this task's own module docstring states explicitly,
now measured on real data, not just asserted. Schur's own ranking rho is
**non-monotonic** in compression size on every target (e.g. KRAS_G12C:
0.74 at m=18 falling to 0.38 at m=32) even as ΔAUC generally improves —
overall correlation with the full system's occupation shape and
specific discriminative power for the pocket label are shown to be
different properties, not interchangeable.

**Louvain (the existing baseline) is the least reliable of the three**:
its own natural resolution on these graphs (~10-15 communities) means
most tested `n_target` values above that produce *zero* forced merging
— the same partition is returned regardless of the requested budget
(reported plainly, not hidden), and even at its natural resolution its
ranking is sometimes anti-correlated with the true occupation (rho -0.03
to -0.11 on CARDIAC_MYOSIN/BCR_ABL1 at the smallest cluster counts) and
its AUC swings are the largest and least consistent of the three methods
(-0.415 to +0.297 across the full grid).

**No submission-operator change** (Tier-2-gated, [[TASK-0100]], out of
this task's own scope) — this reports a retention *measurement*, not a
recommendation to swap `run_challenge.py`'s own coarse-graining step.

Full detail: `.ai/tasks/DONE/TASK-0172-spectrum-preserving-reduction.md`
(Done section), `src/allostery/reduce.py`, `tests/test_reduce.py`,
`scripts/spectrum_preserving_reduction.py`,
`results/tasks/0172_spectrum_preserving_reduction/results.json`.

---

| 73 | [[TASK-0217]]'s own diagnosis: six corrections in one week all belonged to one class (construct validity, not statistics) — criterion outcome-reachability + positive-control presence, specifically ([[TASK-0217.002]]). Does a systematic sweep find only the four already-known instances, or more? | **resolved 2026-08-14: retrospective test passes (rediscovers all 4 known instances independently); 1 new latent finding, now fixed; 13/13 criteria audited, 8 clean, 4 pre-existing/already-fixed, 1 new.** Every task file with a literal "Pre-Registered" section header enumerated (13, spanning 2026-08-02 to 2026-08-13). **New finding**: `scripts/fpocket_conditional_analysis.py`'s `ALPHA = 0.05/FAMILY_SIZE` auto-scales with `len(TARGETS)` (guards [[TASK-0189]]'s family-drift defect, per its own comment) but nothing checked the other half of that lesson — as `TARGETS` grows, `ALPHA` shrinks toward `1/N_PERM_REPS`. Currently reachable (`0.05/30=1.667e-3` vs. `1e-3`, confirmed) but at only ~60% of the floor — one more target (this register has grown `TARGETS` once already, and [[TASK-0215]] just found 6 more valid instances to draw from) would silently cross into [[TASK-0189]]'s exact defect. **No past verdict was ever affected** — fixed proactively: `assert_gate_reachable` wired in, matching the existing pattern in `zero_plant_specificity_analysis.py`, verified reachable without re-running the analysis. **Convention amendment landed** in `INTENT_CONTRACT_TEMPLATE.md`'s "Planned Validation" section (state the positive control's expected result alongside the pass bar; demonstrate each outcome is reachable) — checked against all 4 known instances, each would have been caught. 8 criteria clean on first audit, including this thread's own recent work ([[TASK-0209]]/[[TASK-0214]]/[[TASK-0215]]). Not covered: criteria embedded in code without a task-file "Pre-Registered" section, and no general-purpose static check was built for the two non-permutation-floor reachability classes (bar-outside-attainable-range; construction-cannot-produce-required-sign) — flagged as needing case-by-case reasoning, not mechanized, to avoid a false sense of coverage. | [[TASK-0217]], [[TASK-0204]], [[TASK-0208]], [[TASK-0189]] |

| 74 | Does a controlled, spectrum-preserving reduction (Krylov subspace projection; Löwdin/Feshbach-Schur partitioning) beat `coarse.coarse_grain`'s existing lossy, diagonal-dropping Louvain merge, and where does the ranking break under compression — the challenge's own "prove coarse-graining retains the signal" requirement? | **resolved 2026-08-14: Schur beats Louvain on 2/3 targets (decisively on KRAS_G12C, loses on BCR_ABL1); block-Krylov breaks sharply, not gradually, at m<=n_active on all 3 targets.** New `allostery.reduce` (citations verified first: Löwdin 1962, Feshbach 1962, Novo et al. 2015, all confirmed). Real, load-bearing structural finding: a block-Krylov seed of `n_seed` residues consumes `n_seed` Ritz dimensions per power step, so at this project's real active-site sizes (18-26) the seed alone meets or exceeds the ~12-16 node NISQ budget before reaching any distal structure — confirmed a block-seed artifact, not a Krylov limitation, via a single-seed supplementary check reaching rho=0.56 at the identical m where the block-seed version was completely uninformative (rho undefined, constant occupation). Schur's own ranking correlation is non-monotonic in compression size even as its AUC-delta generally improves. Louvain (existing baseline) is the least reliable of the three — sometimes anti-correlated with the true ranking, largest/least consistent AUC swings. No submission-operator change (Tier-2-gated). | [[TASK-0172]], [[TASK-0100]] |

| 75 | Table 1 mandates Cardiac Myosin's pair as 5TBY→6C1H; this register uses 8QYP→8QYR (TASK-0124's substitution, on data-quality grounds it established independently). Run and disclose **both**, apply TASK-0209's VALID rule to the mandated pair too, and verify the 6C1H mavacamten-absence claim live rather than citing the register. | **resolved 2026-08-19: the mandated pair cannot be scored at all — not merely INVALID under TASK-0209's rule, but structurally unable to reach a verdict, confirmed via two independent code paths.** New `config/targets.yaml` entry `CARDIAC_MYOSIN_TABLE1` (5TBY apo chain B / 6C1H holo chain P — additive, incumbent `CARDIAC_MYOSIN` entry untouched, every historical number stays conditioned on 8QYP/8QYR). **Wiring check**: re-ran the incumbent pair fresh — `NO_SIGNAL_IN_APO` reproduces exactly (TASK-0124's own diagnosis); point-estimate AUCs drift slightly (0.548 vs. 0.518 actual) from legitimate intervening pipeline changes (TASK-0177's consensus pocket labels landed after TASK-0124), not a wiring defect. **6C1H verified live** (RCSB REST Data API, entry + polymer_entity endpoints, independent of the existing 2026-07-06 record — corroborates, does not merely repeat it): confirmed no mavacamten (nonpolymer components ADP/MG only) **and a stronger fact than previously on record — 6C1H is not even a beta-cardiac-myosin (MYH7) structure.** Its myosin polymer entity is "Unconventional myosin-Ib" (*Rattus norvegicus*), from an actin-bound myosin-force-sensing mechanism paper, structurally and functionally unrelated to the mavacamten/hypertrophic-cardiomyopathy biology this target is about. 5TBY re-confirmed as the existing record already had it: 20.0 Å docked SWISS-MODEL homology model fitted to an EM reconstruction (EMD-2240), zero ligands. **Mandated pair run twice, through independent methodologies, both fail cleanly**: (1) `run_challenge.py` — `build_labels` returns `pocket=None` (`labels.py::holo_pocket_mask`'s documented "ligand not found" contract), `RuntimeError`, only `error.txt` written (no connectivity matrix, no hit list — nothing to compute); (2) `task0204_positive_control.run_target` (the machinery TASK-0209's VALID rule is built on) — independently returns `{"error": "no resolvable holo-frame pocket label"}` via its own separate `_holo_native_labels` code path. **New finding beyond the mavacamten-absence fact**: even the fallback active-site anchor (`func_ligand: ["ADP","ATP"]`) fails for an independent reason — 6C1H's only ADP/MG sit on the actin chains (A–E), not the myosin-Ib chain (P), so there is no nucleotide-pocket ligand on the myosin component at all in this deposition; both the pocket and the active-site fallback collapse to the same topological (top-5-highest-degree) proxy, which the pipeline's own `pocket & ~active_site` exclusion then correctly empties out (`pocket.sum()==0`) rather than silently reporting a spurious result. **Practical conclusion for [[TASK-0184]]**: report both pairs. Incumbent (8QYP/8QYR) — runs, `NO_SIGNAL_IN_APO`, INVALID under TASK-0209. Mandated (5TBY/6C1H) — cannot be scored under any methodology tried; two independent, unrelated structural defects (wrong drug, wrong myosin isoform) both block it. Neither pair supports Table 1 §6's blind apo→holo mavacamten-pocket prediction — a stronger and more decisive statement than "both invalid," since the mandated pair never reaches a defined contrast to be invalid *about*. | [[TASK-0222]], [[TASK-0124]], [[TASK-0209]], [[TASK-0192]] |

| 76 | Ref [9] (Gunasekaran, Ma & Nussinov 2004, *Proteins* 57:433 — cited by the challenge's own bibliography) argues there is no clean class of "non-allosteric" surface sites, attacking the negative class every AUC in this program assumes. Does this change how the program's own "zero confirmed positives" finding (TASK-0161/TASK-0199) should be read, and do metrics that degrade more gracefully under a contaminated negative class (rank-of-known-site, enrichment-at-k) tell a different story on the headline cells? | **resolved 2026-08-21: citation verified directly (title/journal/volume/pages/PMID/DOI all match); the alternative metrics do not rescue the result — they make it more concrete — but the negative-class concern still forces a real, stated change in how the program's own zero-positives claim may be phrased.** New `metrics.rank_of_known_site` (rank of each labelled-positive residue in the full descending score ordering, average-rank tie handling; `enrichment_at_k` already existed). Recomputed on the 3 mandatory targets' headline cells (H_new, live pipeline, same `run_frozen_verdict` code path the submission's own headline numbers use — a wiring-check cross-validation, not a new scoring method): KRAS_G12C AUC 0.557 (best pocket residue ranks 7/169, median 82), BCR_ABL1 AUC 0.541 (rank 125/451, median 176), CARDIAC_MYOSIN AUC 0.549 (rank 107/704, median 279) — **enrichment@5 = 0.00 on all three: zero of the top-5 residues in this project's own reported hit list are real pocket residues, on every mandatory target.** AUC point estimates drift slightly from the submission draft's previously-cited 0.5901/0.5266/0.5176 (expected — [[TASK-0177]]'s consensus-label refinement landed between the two runs, not a new disagreement). **The consequence for the multiplicity budget is on interpretation, not arithmetic**: TASK-0161/TASK-0199's 226-cell count, ~2 expected false positives after the ~9× redundancy correction, and zero observed are all counting facts, independent of negative-class quality. What ref [9] puts in question is whether that zero may be read as "we have shown there is no signal" — it may not: a contaminated negative class is an equally consistent explanation for the same zero (reduced statistical power from noisy negatives), and this program's methodology cannot currently distinguish the two. Limitations text drafted accordingly: state the result as "no method tested here found a statistically robust signal," not as proof of absence. | [[TASK-0229.001]], [[TASK-0229]], [[TASK-0161]], [[TASK-0199]] |

| 77 | The challenge's own bibliography cites two hardware routes this register never addressed: [10] circuit cutting/quasiprobability simulation of non-local channels, [11] SVD/dilation for open-system dynamics — does either change [[TASK-0182]]'s `FAULT_TOLERANT_ONLY` verdict, and are both consistent with it or does either contradict it? | **resolved 2026-08-22: both citations verified directly; [10] reinforces the existing negative from an independent direction (no contradiction), [11] is the one route in the register that clears the qubit-count bar — honestly caveated as requiring an unbuilt encoding, not a built result.** [10] (Mitarai & Fujii 2021, *Quantum* 5:388): sampling overhead for simulating *n* non-local two-qubit gates via quasiprobability is O(9ⁿ) (O(4ⁿ) with inter-subcircuit classical communication) — the paper's own established scaling, not invented here. Computed a **real, measured cut count**, not an assumed one: each mandatory target's actual `H_new` coupling graph partitioned into NISQ-sized islands via `coarse.coarse_grain`'s existing Louvain machinery ([[TASK-0182]]'s own tool, unmodified), counting genuine boundary-crossing edges. Result: KRAS_G12C *n*=235 (log₁₀ overhead 224/142), BCR_ABL1 *n*=344 (328/207), CARDIAC_MYOSIN *n*=510 (487/307) — every cell exceeds the observable universe's ~10⁸⁰ atoms by 15-400 orders of magnitude even in the cheaper (4ⁿ) regime; the raw float overflowed before switching to log₁₀. Circuit cutting does not change [[TASK-0182]]'s verdict. [11] (Oh, Krogmeier, Schlimgen & Head-Marsden 2024, *ACS Phys Chem Au* 4:393 — directly on-topic, FMO exciton transport, the same physics as this register's own ENAQT work): needs only **1 ancilla qubit regardless of system size** (real advantage over Stinespring dilation, whose ancilla count scales with Kraus rank); gate count O(4^d), *d* = system qubits, their own worked example uses 8 total qubits for a 7-site system via **amplitude/log-scale encoding**, not one qubit per site. **The catch, stated precisely**: [[TASK-0182]]'s entire resource table — and every observable in this register — uses one qubit per residue, not this encoding. Projected under the alternative log-scale encoding (never built or costed here): *d* ≈ ⌈log₂ N⌉ ≈ 9-10 system qubits for N up to 704, +1 ancilla, O(4^d) ≈ 10⁵-10⁶ gates — the first genuinely NISQ-plausible *qubit count* in this register, at a large but non-astronomical gate count. Reconciled, not contradicted: [[TASK-0182]] never costed this encoding, so there is nothing to explain away, only a real, unbuilt option now on record. **Also surfaced**: [[TASK-0182]]'s own resource/feasibility verdict had never been cited anywhere in `documentation/PHASE1_SUBMISSION_DRAFT.md` before this task — corrected in the same pass, not left as a silent gap for a referee to find. | [[TASK-0229.002]], [[TASK-0229]], [[TASK-0182]] |

| 78 | Ref [1] (Zheng 2023, *J Chem Phys* 158:124127 — the challenge's own reference #1: NMA-guided conformational sampling for cryptic-site prediction) has never been implemented as a scored classical baseline in this register, despite this program independently converging on the same conformational-search reframing. Implement it faithfully (per-mode ANM displacement scanning, not a joint ensemble draw) and score it on [[TASK-0209]]'s VALID targets. | **resolved 2026-08-22: implemented faithfully, validated, and it beats this register's own quantum observable on KRAS_G12C by a wide point-estimate margin — reported plainly, per this task's own Constraint.** New `scripts/task0229_004_zheng_nma_baseline.py`: for each of the lowest 20 ANM modes, 6 amplitudes (±1,±2,±3 thermal-scale multiples, an Implementer's-call grid, stated as such — Zheng's own paper is not quoted as specifying this exact grid), reconstructs full-atom structure (`conformational_search_measurement`'s own TASK-0185 `_apply_ca_displacement`) and scores with the already-vendored fpocket (TASK-0163). **Planned Validation passed** on BCR_ABL1 (this register's own known positive control): real-pocket hit rate 92.5% vs. decoy 36.7% — the per-mode sampler reproduces the qualitative claim (specific, not generic, pocket opening) before being trusted on the VALID targets. **KRAS_G12C**: whole-graph AUC **0.728** (floor 0.530, beats it by a wide margin — this register's own quantum-observable AUC on the same target is ~0.557-0.590 depending on label vintage, [[TASK-0229.001]]/[[TASK-0184]] §2.2 — Zheng's classical baseline substantially outperforms it), TASK-0201's corrected compact-patch null p=0.024 (1000 draws) — clears a naive 2-test local Bonferroni bar (0.025) by a hair, but is **three orders of magnitude short of this program's own register-wide multiplicity bar** (~0.05/228≈0.00022, [[TASK-0161]]/[[TASK-0199]]) — **not counted as a new "surviving positive"** under this project's own standing convention, reported as a strong point estimate that does not clear the register's real bar, not oversold as significant. **PTP1B**: whole-graph AUC 0.610 (floor 0.451, beats it), null p=0.088 (not significant even locally) — and a genuine internal discrepancy disclosed, not hidden: Zheng's own preferred statistic (pocket-level ≥50%-overlap hit rate) shows the *opposite* of specificity here (real 12.5% vs. decoy 18.3%) even though the softer residue-level AUC clears the floor — the two readouts disagree on this target, both numbers reported side by side. **Per this task's own Constraint** ("if it outperforms our quantum arm, we report that ourselves"): done, written into `documentation/PHASE1_SUBMISSION_DRAFT.md` as a new Finding, matching Finding 3's own existing "a classical method beats our quantum observable" pattern (fpocket) with a second, independent instance (Zheng's dynamics-based method). Adds 2 real-target scored cells to the register's own running multiplicity count (not itself updated here — flagged for whoever next revises [[TASK-0161]]'s own table). **Correction 2026-08-23 ([[TASK-0229.005]]): the `documentation/PHASE1_SUBMISSION_DRAFT.md` write-up claimed above never actually landed** — a shared-file-collision bug in this task's own commit silently dropped it while absorbing another thread's unrelated in-flight edit; the numbers here and this task's own Done section were unaffected. Recovered and landed in TASK-0229.005's own commit. | [[TASK-0229.004]], [[TASK-0229]], [[TASK-0185]], [[TASK-0163]], [[TASK-0201]], [[TASK-0209]], [[TASK-0161]] |
| 79 | The register's own "highest-value construction" (H2 in `.claude/hypotheses/reference_register.md`): [1] Zheng NMA sampling feeding [2] Koseki et al. 2025 (CrypToth) persistent homology → pocket ranking, zero MD, both halves from the challenge's own bibliography. Does the ensemble version of the H2 persistent-void signature (untested, "H2.2") outperform [[TASK-0142]]'s single-structure result, and does it recover what [[TASK-0143]]'s graph-openness proxy missed? | **resolved 2026-08-23: the observable fails its own cheapest positive control on both VALID targets, before the ensemble question is even reachable — a decisive negative, not an open question.** Citation verified directly (Koseki et al. 2025, DOI 10.1021/acs.jcim.4c02111, resolves). New `allostery.persistent_voids.ensemble_void_score` (factored from the existing single-structure `void_score`, one `ripser` call per conformation, H1 read as a free secondary diagnostic from the same call). **Real bug found and fixed while building this**: a persistence class still alive at the Rips filtration cap `thresh` was treated as having infinite lifetime, corrupting the shell-kernel score with NaN — fixed via right-censoring at `thresh` (a class open at the observation limit is *at least* as persistent as `thresh - birth`, not "no signal"), not exclusion (exclusion was tried first and silently flipped two long-passing synthetic tests, revealing their own `>3.0` checks had been passing on `inf > 3.0` all along). **Checked for retroactive impact on [[TASK-0142]]'s own 3 previously-published real-target numbers: none — all 3 reproduce to full float precision post-fix**, the bug was never actually triggered on those structures. **Planned Validation (void_score on the HOLO structure, no sampling needed) FAILED on both VALID targets**: KRAS_G12C top H2 persistence 0.812 vs. this project's own established noise floor 2.5, AUC 0.557 (near chance); PTP1B top H2 persistence 1.535 (also sub-floor), AUC **0.116 — anti-correlated** with the known pocket. Confirmed not a filtration-cap artifact (identical at thresh=16/20/24/30). **Per this task's own gating** (apo-ensemble scoring conditioned on its own target's positive control), both targets skipped as trusted scores; run anyway as an explicit **ungated diagnostic**: 120-conformation NMA-sampled apo-ensemble AUC 0.521 (KRAS_G12C, does not beat floor 0.530) / 0.487 (PTP1B, nominally beats floor 0.451 but null p=0.63 — not significant); only 5% of sampled conformations on either target ever cross the noise floor at all. **Comparison against [[TASK-0143]]'s proxy** (a genuinely different observable, not a re-reading — graph-hop-vs-Euclidean structural distance there, actual persistent H2 topology here): TASK-0143 found KRAS_G12C INSUFFICIENT (uncorrected p=0.016, not Bonferroni-significant) and PTP1B **INFEASIBLE** (its own matched-spread null could not even be constructed). This task reaches a decisive negative on both — including PTP1B, which TASK-0143's own methodology could never resolve at all. Written up as new Finding 6 in `documentation/PHASE1_SUBMISSION_DRAFT.md`, immediately after row 78's recovered Finding 5 (same commit). | [[TASK-0229.005]], [[TASK-0229]], [[TASK-0229.004]], [[TASK-0142]], [[TASK-0143]], [[TASK-0209]], [[TASK-0201]] |
| 80 | [[TASK-0238]] Leg B1 found that this register's own published floor/actual/margin triplets for the 3 mandatory targets no longer reproduce — commit `1924e5e` ([[TASK-0217.001]]) fixed a live `labels.functional_indices` array-correspondence bug (holo-space heavy-atom indices used as apo-space indices, exposing 10/13 targets) but never refreshed the headline numbers cited as current across `EXECUTION_PLAN.md`, `ALGORITHM_REGISTER.md`, `COMPETENCE_MAP.md`, and — materially — `documentation/PHASE1_SUBMISSION_DRAFT.md:146`, which goes to the challenge organisers. 56 (now 62) citations found across 5 documents; classify each as historical record or live claim, and correct the live ones. Also resolve a second, apparently-unrelated inconsistency: CARDIAC_MYOSIN's floor cited as 0.7921 in one place and 0.5679 in another. | **resolved 2026-08-24: this task's own fresh `run_challenge.py` run (commit `821dbfb`) independently reproduces TASK-0238 Leg B1's triplets to 3-4 decimals — floor/actual/margin now KRAS_G12C 0.5296/0.5565/+0.0269 (was 0.4818/0.5901/+0.1083, margin ~4× weaker), BCR_ABL1 0.5031/0.5408/+0.0377 (was 0.5817/0.5266/−0.0551, **sign flip**), CARDIAC_MYOSIN 0.4538/0.5485/+0.0947 (was 0.5679/0.5176/−0.0503, **sign flip**).** All 62 citations classified: `RESULTS.md`'s own ~55 (this file) are dated historical measurements correctly describing the pipeline's state *at the time each ran* — left as-is, per this file's own no-silent-overwrite preamble (TASK-0238's own Leg B1 section, already in this file, already states the corrected numbers and is not touched here). Live-claim citations corrected via dated CAVEAT/superseding annotations matching each document's own existing convention, not silent rewrites: `documentation/PHASE1_SUBMISSION_DRAFT.md` (Finding 3's triplet corrected in place plus a banner update — this is the one document where the stale numbers were reported as *current*, not historical, so corrected directly rather than annotated; also fixed §2.5's own footnote, which had attributed a since-superseded number gap to [[TASK-0177]]'s label refinement when the dominant cause was this same TASK-0217.001 fix), `COMPETENCE_MAP.md` (3 new CAVEAT blocks in its own established stacked-layer style, covering the headline table, the CARDIAC_MYOSIN section's own declared-current ending, and the discriminability-audit table), `ALGORITHM_REGISTER.md` and `EXECUTION_PLAN.md`'s own most-prominent fpocket-comparison paragraphs (superseding annotations alongside the existing [[TASK-0206]] one). **BCR_ABL1 and CARDIAC_MYOSIN's negative diagnoses (`NO_SIGNAL_IN_APO`, re-confirmed this run) now come from the chance bar (CI-overlap / permutation null), not the floor gate** — every corrected annotation states this explicitly, and no prose elsewhere in the 5 documents was found attributing either negative to the floor gate specifically (checked directly, not assumed). **Second inconsistency resolved: not an error.** 0.7921 (`EXECUTION_PLAN.md:265`, dated 2026-07-19) and 0.5679 (`ALGORITHM_REGISTER.md`, dated 2026-07-27/28) are two legitimate, correctly-dated historical vintages either side of [[TASK-0124]]'s 2026-07-20 CARDIAC_MYOSIN apo re-anchor (5TBY→8QYP) — `COMPETENCE_MAP.md`'s own CARDIAC_MYOSIN section already documents this exact transition ("floor drops 0.7921→0.5679") in prose; confirmed by date, not just by that citation. `ALGORITHM_REGISTER.md`'s 0.5679 is the later, post-re-anchor, pre-TASK-0217.001 vintage — the one actually superseded by this task. **Guard proposed, not built** (per this task's own Acceptance, "not necessarily built"): a pinned-golden regression test over the 3 mandatory targets' floor/actual/margin triplet, run through `scripts/run_challenge.py`'s real path (not a mock), asserting each value matches a checked-in golden JSON to a stated tolerance and failing loudly (not silently) if a future `labels.py`/`analysis.py` change shifts it — mirrors [[TASK-0206]]'s own already-working fpocket-AUC pin (`tools/fpocket/PROVENANCE.json`) and [[TASK-0217.001]]'s post-hoc audit pattern, but pre-hoc: CI-catchable before a numeric-shifting fix lands uncited, not caught weeks later by a reviewer's wiring check. Not implemented here — flagged as the concrete next task. | [[TASK-0239]], [[TASK-0238]], [[TASK-0217.001]], [[TASK-0206]], [[TASK-0124]], [[TASK-0195]], [[TASK-0184]] |

| 81 | Ref [4] (Motlagh, Wrabl, Li & Hilser 2014, Nature 508:331 — the Ensemble Allosteric Model) is the largest previously-untested item in the challenge's own bibliography: does the genuine (binary folded/unfolded, nonlinear) EAM diverge from this register's propagation-based picture, where an already-tested harmonic proxy did not (\|partial ρ\|=0.773, [[TASK-0226]])? | **resolved 2026-08-23: neither clean closure — a genuinely mixed result.** New `allostery/corex.py`, a real COREX-style implementation (sliding-window folding units, ASA via BioPython's validated `Bio.PDB.SASA.ShrakeRupley`, a stated two-term ΔG model — Eisenberg & McLachlan 1986 apolar-burial coefficient + Tien et al. 2013 max-ASA reference, both bibliographically verified). Sanity check passes on both TASK-0209-VALID targets (buried residues significantly more stable than exposed, ρ=−0.365/−0.298, p<2×10⁻⁶ both). Decisive negative control (does EAM ranking disagree with propagation ranking): Spearman ρ=0.542 (KRAS_G12C) / 0.493 (PTP1B) against hop-distance — real, highly significant, substantial agreement, but far short of the ~0.85-0.95 this register's other proximity-confounded observables show, meaning ~70-75% of EAM's own ranking variance is unexplained by hop-distance alone. Independent of the empirical result, the EAM's true object (a partition function over 2^N microstates, which COREX's own tractable approximation exists to avoid computing directly) is named as a type-correct quantum target (Gibbs-state preparation / partition-function estimation) — explicitly not an advantage claim, and not scoped into any Phase-2 milestone. c-Myc/1NKP correctly excluded (unvalidatable, no holo structure). **Written up 2026-08-24, after [[TASK-0183]]/`POC_SPRINT_PLAN.md` had already shipped and closed**: new Finding 7 in `documentation/PHASE1_SUBMISSION_DRAFT.md` (§1, plus a §3(d) cross-reference) and a dated addendum in `POC_SPRINT_PLAN.md` itself, both explicitly marked as added after closing, not a revision of either document's own already-committed content. | [[TASK-0229.006]], [[TASK-0229]], [[TASK-0226]], [[TASK-0183]], [[TASK-0184]] |
| 82 | **Recovered, 2026-08-24 ([[TASK-0253]]): this row (originally numbered 81) was silently deleted from this file by commit `73ea819` (a shared-file collision — a later thread's own edit dropped it while adding its own 198 lines), discovered while this task was auditing an unrelated part of the two-stage joint-experiment work. Restored verbatim below, renumbered (81 is now the EAM/COREX row above); its own findings are still directly relevant context for [[TASK-0253]]'s own row, and are additionally now superseded in scale (not correctness) by [[TASK-0243]]'s own n=22 re-run and [[TASK-0249]]'s own composite-baseline result, both already in this file.** Original question: [[TASK-0242]]'s own two-stage dry-run (n=7 untuned targets) found CTQW and a trivial "mean BFS hops from seed" ranker have **identical mean rank** (5.71, Wilcoxon p=0.297) — hop was reported only as a covariate, which cannot settle whether CTQW does anything beyond proximity-to-seed. Promote hop to a competing ranker in the same table, and add three controls: a residual ranker (hop partialled out of CTQW's own candidate scores), a seed-free operator control (same candidates, random seed of matched size), and a hop-matched candidate null (compete only against size/hop-matched decoys). | **resolved 2026-08-24: all three new controls point the same direction as TASK-0242's own finding — CTQW's two-stage ranking advantage is substantially, and possibly entirely, a proximity-to-seed effect, not evidence of a mechanism beyond it.** New `scripts/task0244_hop_competing_ranker.py`, reusing [[TASK-0242]]'s own `run()` unchanged (extended additively with an opt-in `return_state=True`, backward-compatible — re-ran the original script afterward and reproduced its exact published numbers, confirming no regression) so no fpocket candidate list is regenerated. Same n=7 untuned, stage-1-surviving targets throughout (the same small sample TASK-0242 itself flagged as underpowered; every number below carries that caveat, per this task's own Acceptance — folded into whatever re-run [[TASK-0243]]'s future ≥12-target frozen set produces, not reported alone). **Residual ranker** (CTQW with each target's own hop_cov linearly regressed out, re-ranked by residual): mean rank **6.29** (vs. raw CTQW's 5.71 — *worse*, not better), MRR 0.330 vs. 0.411, Wilcoxon p=0.625 — removing hop's contribution does not help CTQW, consistent with hop explaining a real share of its ranking power. **Seed-free operator control** (same candidate list, CTQW re-run from 20 random seed sets of matched size per target, no re-run of fpocket): mean rank collapses to **8.65** (MRR **0.145**, close to this experiment's own ~0.075-0.15 chance band) from the real-seed run's 5.71/0.411 — a **~2.8× MRR collapse toward chance**, Wilcoxon p=0.109 (not significant at n=7, but the largest, most decisive-looking effect of the four controls; per this task's own Scope, exactly the signature specified as confirming proximity as the mechanism). **Hop-matched candidate null** (compete only against candidates matched to the true pocket's own hop distance ±1 and size ±50%, within each target's own candidate list — feasible on 7/7 targets, not INFEASIBLE like TASK-0143's own structural-graph null): true pocket ranks **#1 in only 2/7** of its own matched pools. **None of the three individually reaches significance at n=7** (the same underpowered-sample problem TASK-0242 itself already flagged, [[TASK-0243]] exists to fix it) — but all three point the same way, and the seed-free collapse in particular is a large, coherent effect size, not noise-shaped. Per this task's own Constraint, this is not read as "the operator is proven to be nothing but proximity" (that claim is not licensed by n=7 either) — it is read as "the current n=7 evidence base is more consistent with proximity-to-seed than with a beyond-proximity mechanism, on every control tried, and the joint protocol needs [[TASK-0243]]'s larger sample before either side can interpret its own result." Apparatus built and validated now, ready to run unchanged against TASK-0243's frozen set once curated. | [[TASK-0244]], [[TASK-0242]], [[TASK-0243]], [[TASK-0094]], [[TASK-0199]], [[TASK-0238]], [[TASK-0143]] |
| 83 | [[TASK-0249]] found `HIV_INTEGRASE_MUT871`/`916` (apo `1M9D`) have an empty active-site seed on every chain, directly contradicting [[TASK-0243]]'s own Done-section claim ("zero fell back to a top-degree proxy... 20/22 uniprot, 2 ligand"). Separately, stage-1 recall (~64%) reproduces across two independent target sets ([[TASK-0242]] n=11, [[TASK-0243]] n=22) — a stable pipeline property. Re-verify the seed for all 22 frozen-set targets, root-cause `1M9D`, and decompose stage-1 failures into fpocket-miss vs. `MIN_HOP`-removal, which the pipeline currently reports identically. | **resolved 2026-08-24: found a real, previously undiscovered correctness bug that was silently corrupting committed results — not just a documentation mismatch.** New `scripts/task0253_seed_and_stage1_audit.py`. **(1) Seed provenance corrected**: live re-run of `detect_active_site` on all 22 targets gives **uniprot=18, ligand=2, none=2** (not TASK-0243's claimed 20/2/0) — the config's own static `active_site_source` field already disagreed with that prose claim (18/4) before any live check. **(2) `1M9D` root-caused, live-RCSB-confirmed**: it is **not an HIV integrase structure** — its two polymer entities are Cyclophilin A (chains A/B, P62937) and **HIV-1 Capsid** (chains C/D, P12497's `pdbx_description`), curated into this pair because Capsid and Integrase are cleavage products of the *same* Gag-Pol UniProt accession (P12497) that the holo structures (`8CBS`/`8CBV`, independently confirmed genuine 233-residue Integrase) also carry. **Verdict: drop the pair** — a domain-identity curation error, not a fixable seed-detection issue; real candidate replacements exist (1IHV, 1IHW, 1K6Y, 5OYM, 1WJF) for whoever curates a proper replacement next. **(3) Real bug found and fixed**: with an empty seed, `hop_from_seed` silently returns a constant sentinel and `time_averaged_ctqw_converged` divides by zero, producing an **all-NaN** score array — neither raised, and `np.argsort` on it still returned *some* rank, which [[TASK-0242]]'s own `run()` then reported as real. **This was already baked into [[TASK-0243]]'s own committed `stage1_rerun.json`** — `HIV_INTEGRASE_MUT871` shows a fabricated `ctqw` rank of **1** (looks like a near-perfect hit), counted as an ordinary stage-1 success in that task's own 16/22 recall and its own head-to-head Wilcoxon tables. Fixed at the source (`task0242_two_stage_dryrun.run()` now raises a clear error on `len(seed)==0`); corrected stage-1 recall is **14/22 = 63.6%**, exactly matching [[TASK-0249]]'s own independently-derived number — a real cross-validation of the fix. Recomputed [[TASK-0243]]'s own head-to-head table on the clean n=14: no qualitative verdict flips (ctqw still trails fpocket_drug, still ties-ish hop_covariate, still beats random — now more decisively, p=0.0032 not 0.0157). **(4) Failure-mode decomposition, the central question, answered plainly: `MIN_HOP`, not fpocket detection, is the dominant failure mode.** Of 6 genuine stage-1 failures, **5 are `MIN_HOP` removing a real fpocket-found candidate** (one, `SMYD3_DIPERODON`, is a 100%-overlap match to the true pocket, removed only because it sits at hop 1 from the seed) — only 1 is a genuine fpocket miss. `MIN_HOP=2` measurably costs true-pocket detections on ~23% of this frozen set — reported as a measured fact for whoever owns the joint protocol's own parameter freeze, not decided here. [[TASK-0243]]'s own Done section amended in place with both corrections (not left contradicted), including a further specific fix (its own claim that `NAMPT_NPA1R` failed via fpocket-miss was itself wrong — it is `MIN_HOP`-removed too). | [[TASK-0253]], [[TASK-0243]], [[TASK-0249]], [[TASK-0242]], [[TASK-0209]], [[TASK-0169]] |
| 84 | **Recovered, 2026-08-25 ([[TASK-0260]]): this row was silently dropped from `RESULTS.md` at commit time** — a bulk `git add` re-staged this file from a working-tree copy that had been deliberately reset to another thread's in-flight content for restoration purposes, overwriting this row's own clean staged version before commit, the same class of shared-file collision that hit [[TASK-0244]]'s own row earlier. Reconstructed from the original commit message, findings unchanged. The collaborating thread already reports `heat_kernel` matching `p_avg`; [[TASK-0210]]/[[TASK-0226]] tested the Markovian random walk classically — but no standing, pre-registered classical-diffusion arm existed in the two-stage apparatus itself, on the identical Hamiltonian, with PSD status honestly reported. | **resolved 2026-08-25: built and wired in — central finding is that a genuine classical-diffusion comparison is not achievable via this construction on real data at all.** New opt-in `include_classical=True` on `task0242_two_stage_dryrun.run()` (default False, verified byte-identical output unaffected): `propagators.ground_state_relaxation` on the same `H_new` the `ctqw` arm builds, plus per-target PSD status. **H_new is indefinite on 14/14 (100%) of TASK-0243's frozen-set scoreable targets** — `ground_state_relaxation` is never classical diffusion here (TASK-0095/P1-B), only ground-state relaxation, reported honestly, never relabelled. New `scripts/task0256_classical_diffusion_parity.py`, both designs: two-stage (ctqw mean rank 9.21/MRR 0.253 vs classical 11.50/0.221, 8/14 wins, p=0.431) and per-residue AUC (median AUC ctqw 0.564 vs classical 0.493, but ctqw wins only 6/14 targets — a disclosed tension, not smoothed over — p=0.778) — neither significant. Candidate-score parity (pre-registered ρ≥0.95 tolerance): median ρ=0.790, 14/14 "separate" beyond tolerance — but since H is never PSD, this is CTQW-vs-ground-state-relaxation divergence (expected), explicitly **not** the "quantum beats classical diffusion" finding the task's own Constraint anticipated — stated plainly, not conflated into a false positive. `haken_strobl`-at-large-gamma (the genuine PSD-independent classical-diffusion limit) checked for feasibility, found genuinely infeasible at this frozen set's real sizes (up to N=1223; 18.1s for gamma=200 at N=228 alone) — a costed, flagged follow-up, not silently skipped. Proposed for the (still-nonexistent) joint pre-registration: both propagators, not either alone. | [[TASK-0256]], [[TASK-0242]], [[TASK-0243]], [[TASK-0249]], [[TASK-0210]], [[TASK-0226]], [[TASK-0095]] |
| 85 | [[TASK-0259]] found the unexplained share in [[TASK-0254]]'s 3-block Shapley attribution (geometry/fpocket/CTQW) correlates almost entirely with apo crypticity (ρ=−0.771, p=0.0001) — median unexplained 55% on cryptic targets vs. 24% on already-open ones. Does a purpose-built cryptic-pocket predictor close this residual, or is there something genuinely unmodelled? Citation-verify 4 candidates (PocketMiner, CryptoSite, P2Rank, FTMap/FTSite) live, settle whether an MD-trained-but-MD-free-inference model violates Constraint 3, install/run whichever survive, and add as a fourth Shapley block. | **resolved 2026-08-25: the strongest classical predictor we could install does not close the residual, and behaves exactly like fpocket, not like a cryptic-opening specialist.** All 4 citations verified live via Crossref: PocketMiner (Meller et al. 2023, Nat. Commun. 14:2135, DOI 10.1038/s41467-023-36699-3), CryptoSite (Cimermancic et al. 2016, JMB 428:709-719, DOI 10.1016/j.jmb.2016.01.029), P2Rank (Krivák & Hoksza 2018, J. Cheminform. 10:39, DOI 10.1186/s13321-018-0285-8), FTMap/FTSite (Kozakov et al. 2015, Nat. Protoc. 10:733-755, DOI 10.1038/nprot.2015.043). **Constraint-3 ruling, one consistent rule applied to all four** (MD as an input this pipeline supplies, not a tool's own training provenance — this register's own settled literal reading, HYP-S7): **P2Rank** — supervised ML on labelled bound structures, no MD anywhere — LEGAL, unambiguous. **FTMap/FTSite** — physics-based FFT probe-clustering, no training data, no MD — LEGAL, but confirmed web-server-only (the paper's own title: "the FTMap family of web servers"), no scriptable local tool — EXCLUDED on installability. **CryptoSite (full model)** — its own most informative feature is "the average pocket score from MD simulations" (AllosMod), run **at inference** to score a new structure — MD executing inside our own pipeline, not training-time-only — EXCLUDED (the paper's own reported MD-free "faster version," AUC 0.74, is not independently released as runnable software — dropped on installability, not the constraint). **PocketMiner** — MD used only for the external authors' own training labels, zero MD supplied by us at runtime — reads LEGAL, but the closest call of the four; **flagged to organisers**, [[TASK-0221]] item (f), rather than silently assumed. **Installed and run: P2Rank** (Java, prebuilt release, ~8-11s/target — real, no MD, unambiguously legal). PocketMiner attempted and found genuinely infeasible this session: needs Python 3.7-3.9 + TensorFlow≤2.9; this environment's own Python 3.13/TensorFlow 2.16-only toolchain requires a from-source Python 3.9 build, which fails against Homebrew's OpenSSL-3-only availability (`openssl@1.1` removed upstream) — tried twice, same documented failure both times, a real costed follow-up (container with an older base image, or a manual OpenSSL 1.1 build), not silently skipped. **P2Rank as a 4th Shapley block** (geometry/fpocket/CTQW/p2rank, generalised 4!=24-permutation exact Shapley, reusing [[TASK-0254]]'s own `cv_auc`/`build_blocks`): p2rank Shapley share median **+9%** (n=20 rows, Wilcoxon-vs-0 p=0.007) / **+10%** (n=13 apo-structure-clustered per [[TASK-0261]]'s own first-pass method, p=0.021) — real and significant, but **unexplained only moves 29%→27%** (rows) / **29%→26%** (clusters). **The decision statistic this task's own Scope actually asks for — p2rank's contribution when added LAST, on top of the already-fitted geometry+fpocket+CTQW model — is smaller still and not significant: median +0.0% (n=20, range −9.4% to +14.9%, Wilcoxon-vs-0 p=0.881).** The Shapley share (+9%) credits p2rank its fair average share of variance it shares with the already-present fpocket block; the added-last number shows that once fpocket is already in the model, p2rank supplies essentially nothing further. Both numbers are honest and both say the same thing from different angles: **does not close the residual.** Crypticity-stratified, exactly the test this task's own Scope pre-specified: p2rank's own gain concentrates on **already-open** targets (median +30% rows / +29% clustered) not the cryptic-testing remainder (median +8% both) — the **same** pattern fpocket already shows (TASK-0254's own +0.518 correlation), not the complementary pattern a genuine cryptic-opening specialist would produce. Read plainly: the modern geometric peer to fpocket we could actually install still behaves like fpocket. The one candidate trained specifically to predict pocket *opening* (PocketMiner) remains untested, for a documented environment reason, not a result. `documentation/CTQW_CONTRIBUTION_BRIEF.html` §08 updated in place with this finding and the environment gap. | [[TASK-0260]], [[TASK-0259]], [[TASK-0254]], [[TASK-0261]], [[TASK-0163]], [[TASK-0137]], [[TASK-0221]] |
| 86 | Three independent looks ([[TASK-0259]], [[TASK-0260]]) show CTQW is the only Shapley block leaning toward cryptic targets rather than already-open ones — not significant, but consistent, and mechanistically the right place for a dynamics method to help. The confound: buried regions are closed, closed regions are cryptic. The geometry block's own burial proxy is `degree_centrality`, but [[TASK-0257]] R2 found real SASA beats it against B-factors on 11/14 targets — and real SASA is in no block at all. Add it as its own block; does CTQW's cryptic lean survive, shrink, or vanish? | **resolved 2026-08-25: shrinks by more than half, and was never significant to begin with — real burial control, not the "does it fully vanish" question the filing implied would settle it either way.** New `scripts/task0266_sasa_burial_control.py`, real per-residue SASA (`Bio.PDB.SASA.ShrakeRupley`, the same validated computation [[TASK-0257]] R2 used) added as an independent 4th Shapley block (geometry/fpocket/SASA/CTQW; CTQW unchanged, standard degree-based `H_new` — SASA is a parallel feature, not substituted into the Hamiltonian the way R2 did). **Overall (n=20): SASA adds essentially nothing on its own** (Shapley median −0.4%, added-last −0.0%); unexplained barely moves, 28.6%→27.2% — matching [[TASK-0260]]'s own P2Rank finding in magnitude. Cluster-robust (13 clusters, [[TASK-0261]]'s exact permutation, not row-level Wilcoxon): CTQW added-last p=0.217 (no SASA) → p=0.262 (with SASA); SASA added-last itself p=0.540 — none of these were ever significant in aggregate. **A real data wrinkle found and handled, not silently worked around**: crypticity is per-ligand, clustering is per-apo-structure — `TRP_SYNTHASE_F6F` (87% open) and `TRP_SYNTHASE_F19` (78%, just under the 80% bar) share one apo structure but land on opposite sides of the threshold, which `cluster_permutation_two_group`'s own assertion correctly refuses to split across groups; excluded from the stratified test only (both members), kept everywhere else (n=9 vs. 9, 6 vs. 6 clusters). **The central, crypticity-stratified, cluster-robust result**: CTQW added-last, no SASA — cryptic median +5.53% vs. open −0.10%, cluster-perm p=**0.0736**. CTQW added-last, with SASA — cryptic +2.17% vs. open +0.01%, p=**0.2392**. **The gap roughly halves (5.6 points → 2.2 points) and the already-marginal significance weakens further.** **SASA's own Shapley share leans cryptic the same direction** (cryptic +8.39% vs. open −3.51%, p=0.311) — partial, direct confirmation of the named confound, though not itself significant. The gap does not flip sign or hit exactly zero, so the honest verdict is **shrinks substantially, not a clean survive-or-vanish** — but the essential context is that p=0.0736 uncontrolled never cleared even an uncorrected 0.05 bar, let alone this register's own multiplicity-adjusted one, so "CTQW's lean survives" would overstate a result that was marginal from the start and is weaker still now. **Recommendation: [[TASK-0267]] (crypticity-matched null) is not worth running** — that task exists to protect a signal against a different confound, and there is no significant signal left here to protect. Per this task's own Constraint, neither the "survives" nor the "burial kills it" prior expectation was allowed to shape the run — both readings are reported side by side with the same numbers. | [[TASK-0266]], [[TASK-0259]], [[TASK-0260]], [[TASK-0257]], [[TASK-0254]], [[TASK-0261]], [[TASK-0267]] |

Full process history, run mechanics, and Acceptance-Scenario checklists
for this run live in `.ai/tasks/DONE/TASK-0079.005-run-mandatory-targets.md`
(or `.ai/tasks/TODO/` if not yet closed — check `.ai/COMMON.md`'s registry
for current status). This document is the one to read for the science;
that one is the one to read for what was done and by whom.

---

## apo→holo change decomposition — the gate that closed, then didn't (TASK-0208, 2026-08-07/12)

**Question**: [[TASK-0204]] closed fixed-backbone rotamer packing on complexity
grounds — but that closure holds only while the interaction graph is *fixed*.
Does the real apo→holo change move the backbone (closure does not transfer) or
only side chains (it does)? Filed as the cheap gate for [[TASK-0210]].

**The original run reported `CLOSED` on all 4 evaluated targets. That verdict
is retracted.** A Reviewer-thread audit found the compound AND-gate
(`substantially backbone` **AND** `frustrated`) had **one leg that could not
fire and another that was confounded**, so it could not have returned `OPEN`
on any data:

1. **The frustration statistic's positive outcome was structurally
   unreachable.** Every `joint` energy was large and positive (+25.4, +29.0,
   +23.5, +114.8); the pre-registered "textbook frustration signature"
   requires `joint < 0`. Transplanting rigid holo rotamers onto an apo
   backbone always clashes (9/12, 10/12, 5/6, 5/12 individual swaps
   destabilizing). The statistic measured *"do rigid holo side chains fit on
   an apo backbone"* — never — not *"are these changes coupled."*
2. **The `not_evaluable` guard keyed off the wrong variable** (`|sum_singles|
   < 1e-6`, dominated by clash energy) so it stayed silent on the very cells
   it was written for.
3. **The attribution metric was structurally biased toward "backbone"**:
   `holo_backbone + apo_chi` moves N/CA/C *and drags every side chain along*,
   while `apo_backbone + holo_chi` moves only atoms beyond Cβ.

**Recompute** (`scripts/task0208_recompute.py`,
`results/tasks/0208_apo_holo_decomposition/results_recompute.json`; original
`results.json` untouched):

| Target | `side_chain_explained` | original coupling verdict | corrected |
|---|---|---|---|
| KRAS_G12C | 0.036 | decomposable (+0.04%) | **not evaluable** |
| PTP1B | 0.078 | decomposable (+16.2%) | **not evaluable** |
| CASPASE1 | 0.043 | anti-frustrated (−10.0%) | **not evaluable** |
| GLUCOKINASE | 0.463 | decomposable (+1.2%) | evaluable, not frustrated (9.2%) |

Adding EvoEF2 `RepairStructure` before `ComputeStability` removes **~97%** of
the measured energy (GLUCOKINASE: sum 116.13→**4.15**, joint 114.75→**3.77**)
— confirming the original numbers were clash energy almost in their entirety.
**Three of four "decomposable" readings were vacuous**, including PTP1B's
+16.2%, the value [[TASK-0212]] was filed to chase (that task is now closed as
invalidated-as-filed).

**Dihedral-space attribution reverses the backbone verdict on every target**
(scale-free per residue, so backbone cannot win by carriage):

| Target | RMSD `backbone_explained` | dihedral bb-share, pocket | distal |
|---|---|---|---|
| KRAS_G12C | 0.733 → "substantially backbone" | **0.374** | 0.561 |
| PTP1B | 0.539 → "substantially backbone" | **0.205** | 0.532 |
| CASPASE1 | 0.524 → "substantially backbone" | **0.356** | 0.247 |
| GLUCOKINASE | 0.204 → "ambiguous" | 0.357 | 0.371 |

Backbone share at the pocket is **below 0.5 on all four**, and the distal
control is *higher* than the pocket on 3/4 — side-chain torsion change is
concentrated **at** the pocket while backbone change is concentrated **away**
from it. The original metric inverted a real, pocket-specific signal.

**The tension is the finding.** `side_chain_explained` ≈ 0.04–0.08 says
rotating side chains on the apo backbone gets you almost nowhere — the
backbone must move. Dihedral bb-share ≈ 0.20–0.37 says most of the *torsional*
change is in χ. Both hold: **the backbone moves little but is load-bearing** —
a small shift repositions the side-chain frames, without which no amount of χ
rotation reaches the holo pocket. That is a description of a **coupled**
regime, and it excludes *both* simple closures.

**Operative verdict: INCONCLUSIVE on all 4.** The coupling question is
unanswered, not answered negatively. [[TASK-0210]] is neither closed nor
opened by it. Full record: [[TASK-0208]]'s own REVIEWER VERDICT and Recompute
sections.

---

## Known-answer cryptic-instance verification — only 2 of 7 targets are valid (TASK-0209, 2026-08-12)

**Question**: every cryptic-pocket experiment in this register assumes the apo
pocket is closed and the holo pocket open. That contrast has never been
checked. Does it hold?

**Verdict: 2/7 VALID (KRAS_G12C, PTP1B). 5/7 INVALID — including 2 of the 3
mandatory targets.**

**Framing correction (2026-08-19)**: the raw 2/7 ratio invites *"why pick five bad targets?"* The honest decomposition is **1 of the 3 challenge-mandated scoreable targets** (only KRAS_G12C, itself validated against a wild-type structure, [[TASK-0155]]) **plus 1 of 4 ASD-extension targets** (only PTP1B). The extension followed the Challenge Statement §6's own instruction to test additional targets and its own named source, the Allosteric Database — `targets.yaml` marks the block "ASD expansion". We did not select the failing targets; the challenge did, and extending into its recommended database recovered only one more. The failure is systemic across two independent sources. Blind pre-registered rule reusing [[TASK-0204]]'s own hit
criterion (`overlap_frac >= 0.5 AND druggability_score >= 0.5`), ligand
stripped, at each target's own 12-residue window:

| Target | apo drug | apo hit | holo drug | holo hit | Δdrug | Verdict |
|---|---|---|---|---|---|---|
| KRAS_G12C | 0.001 | miss | 0.886 | **hit** | +0.885 | **VALID** |
| PTP1B | 0.046 | miss | 0.757 | **hit** | +0.711 | **VALID** |
| BCR_ABL1 | 0.566 | **hit** | 0.356 | miss | −0.210 | INVALID |
| GLUCOKINASE | 0.759 | **hit** | 0.229 | miss | −0.530 | INVALID |
| CASPASE1 | 0.679 | **hit** | 0.030 | miss | −0.649 | INVALID |
| CARDIAC_MYOSIN | 0.001 | miss | 0.166 | miss | +0.165 | INVALID |
| CASPASE7 | 0.582 | miss | 0.010 | miss | −0.572 | INVALID |

Known-answer checks (KRAS_G12C→VALID, BCR_ABL1→INVALID) both matched; the rule
was adopted blind, not fitted.

**Three mechanistically distinct failure modes:**

1. **Inverted contrast with an unexplained bound HETATM in the "apo"** —
   BCR_ABL1 (`MYR`, myristic acid, 3.47 Å from the window, [[TASK-0169]]'s
   finding reused as the known-answer check) and **GLUCOKINASE (`MRK`,
   2.45 Å — a new finding of the same shape).** An endogenous or
   co-crystallized small molecule holds the "apo" pocket open.
2. **Inverted contrast with nothing nearby to explain it** — CASPASE1: apo
   scores 0.679 druggable with no flagged HETATM. Not an occupied pocket, an
   *intrinsically open* one.
3. **No contrast at all — the holo positive control itself misses** —
   CARDIAC_MYOSIN (0.166), CASPASE7 (0.010). The pipeline cannot see either
   state as druggable at this window/bar.

**The construction leg could not run for any INVALID target**, and the reason
is structural rather than incidental: `holo_native_hit=False` on **all 5**, so
there is no verified-open reference to construct a closed instance from or to
round-trip back to. Reported as a blocked precondition rather than forced
through — forcing it would have produced an artifact, not an instrument.

**Register-wide exposure, stated not re-run**: the standing mandatory set is
KRAS_G12C / BCR_ABL1 / CARDIAC_MYOSIN, and **2 of those 3 are INVALID**. For
druggability-contrast-dependent claims specifically, the mandatory-3 gate has
been running at **1/3 validated coverage**. This does not retroactively
invalidate individual measured numbers — most GNM/CTQW-family observables do
not depend on fpocket druggability contrast at all — but "passes on 2/3
mandatory targets" cannot be read as "on 2 genuine cryptic-pocket contrasts"
without naming which.

A real chain-letter-collision bug in the reused positive-control ladder was
found and fixed locally (not in `task0204_positive_control.py`, which was
under another thread's active claim): the window is relabeled to chain 'B',
which is a no-op collision on any target whose own chain is already 'B'
(CARDIAC_MYOSIN's holo). Flagged for that file's owner.

---

## Coupled backbone+rotamer search — classical solver, tentatively OPEN (TASK-0210, 2026-08-12)

**Question**: is trajectory-free coupled backbone+side-chain apo→holo search
actually hard? The route sits precisely in the gap between three existing
closures — [[TASK-0204]] (fixed-backbone packing: exact in ms, but the graph is
fixed), [[TASK-0185]] (backbone-only ENM: recovery in 1–8 draws, but side
chains unmodelled), and single-particle CTQW (an `eigh` call) — and unlike all
of them it has a **known answer**.

**Firewall/known-answer check passes on only 2 of 4 targets**, independently
reproducing [[TASK-0209]]'s verdict from a different direction:

| Target | apo drug | holo drug | objective prefers holo? |
|---|---|---|---|
| KRAS_G12C | 0.001 | 0.886 | **yes** |
| PTP1B | 0.046 | 0.757 | **yes** |
| CASPASE1 | 0.679 | 0.030 | no — inverted |
| GLUCOKINASE | 0.759 | 0.229 | no — inverted |

Per the task's own Planned Validation, CASPASE1/GLUCOKINASE results are **not
interpretable** — the search ran, but no outcome there would be informative.

**Classical solver** (apo-only ANM-mode backbone perturbation + EvoEF2
`SideChainRepack` + fpocket-druggability objective; holo used *only* to score,
never as an input): 2 restarts × 10 iterations per target.

| Target | restart 1 (score / RMSD reduction) | restart 2 | reached the holo basin? |
|---|---|---|---|
| KRAS_G12C | 0.349 / 9.6% | 0.466 / 7.9% | **no** |
| PTP1B | 0.071 / 21.1% | 0.293 / 15.4% | **no** |

Success bar: ≥50% window-RMSD reduction, or overlap ≥0.5 **and** druggability
≥0.5. Neither evaluable target reached either bar on either restart; best
scores (0.47, 0.29) sit well below the true holo values (0.89, 0.76).

**Verdict: tentatively OPEN, weakly supported — deliberately not handed to
[[TASK-0183]] as a Phase-2 candidate.** **[SUPERSEDED 2026-08-13 by [[TASK-0213]]: CLOSED. At 65 restarts x 25 iterations KRAS_G12C succeeds on 13/65 (20%); 0/2 was fully consistent with that rate (~64% chance). Search is not the bottleneck. See this document's own TASK-0213 section.]** n=2 restarts on n=2 evaluable targets,
and the pre-registered CLOSED condition ("≥3 of 4 targets clear the bar")
assumed 4 evaluable targets and cannot be evaluated as written.

**A disclosed budget note, and the discipline is the point**: the per-call cost
calibration that sized the 2×10 budget (16.3 s/call, measured on a stray file
from an earlier task) was unrepresentative — real cost is ~1.6–10 s/call and
the full run took ~6 minutes, not the ~30 it was sized for. **The
pre-registered budget was honored as committed anyway**, with no post-hoc
extension after seeing a negative result. The cheap true cost is reported for
the follow-up rather than used to inflate this run retroactively.

---

## Coupled search re-run at adequate n — the last OPEN route closes (TASK-0213, 2026-08-13)

**Question**: [[TASK-0210]] reported "tentatively OPEN, weakly supported" from
**0 successes in 2 restarts** on each of the 2 evaluable targets. Zero out of
two is consistent with almost any difficulty. Is the route genuinely hard, or
was it under-searched?

**Filed as a separate task rather than an extension of [[TASK-0210]]**, which
honored its own pre-registered budget after seeing a negative result
specifically to avoid outcome-contingent inflation. Extending that run inside
the same task would have been exactly the inflation it refused.

**Method**: [[TASK-0210]]'s solver, objective, firewall and success bars reused
**verbatim** — only `RESTARTS`/`ITERATIONS` overridden. Budget set by a cost
calibration on this task's own candidate files (TASK-0210's 16.3 s/call sizing
came from a stray file left by an earlier task and proved ~7x pessimistic;
real cost 2.15-2.26 s/iteration), then fixed by a pre-registered formula and
**not revised after any score was seen**: **65 restarts x 25 iterations per
target**, ~42 min/target. Firewall reproduced on both targets first.

**Result: CLOSED.**

| Target | successes / 65 | rate | best-score min / median / max | true holo |
|---|---|---|---|---|
| **KRAS_G12C** | **13** | **20%** | 0.333 / 0.555 / **0.882** | 0.886 |
| PTP1B | 0 | 0% | 0.033 / 0.293 / **0.397** | 0.757 |

**KRAS_G12C reaches the holo basin on 13 of 65 restarts.** At a 20% per-restart
rate, observing 0/2 has probability ~0.64 — [[TASK-0210]]'s negative was
entirely consistent with an easy instance, which is precisely the ambiguity
this task existed to remove. Per the pre-registered rule (CLOSED if either
target clears the bar on >=2 restarts), **coupled backbone+rotamer search is
not hard on the one target where the objective is valid and the search
succeeds.**

**Trajectory diagnostics** (pre-registered "regardless of verdict"): only
12-25% of restarts were still improving in the final 20% of iterations, and
the median restart reached its own best by iteration 9-15 of 25. **The anneal
length was not the binding constraint** — the search converges inside budget,
so restart count was the correct dimension to raise and raising `ITERATIONS`
further would buy little.

**PTP1B's 0/65 is not a near-miss.** Its entire best-score distribution is
capped at 0.397 — below the 0.5 druggability bar and far below its own true
holo value of 0.757 — so the search never approaches the answer, in either the
restart or the iteration dimension. KRAS_G12C's distribution (0.333-0.882)
straddles the bar exactly as a 20% rate implies.

**The two valid targets disagree, and at n=2 that cannot be adjudicated.**
Whether PTP1B is genuinely harder, or its objective/window is mis-specified
there, is undecidable with [[TASK-0209]]'s 2 valid instances — reported as
unresolved rather than resolved in either direction. This is the n=2 ceiling
[[TASK-0209]] created, arriving in practice.

**Register-level consequence: there is no OPEN quantum-advantage route left.**
Nine identified routes are now closed by measurement — single-particle CTQW,
coherence/interference, non-locality, interacting multi-particle,
backbone-only ENM search, residue-selection QUBO, optimal control,
fixed-backbone rotamer packing ([[TASK-0204]], complexity grounds), and
coupled backbone+rotamer search (this task).

Full detail: `.ai/tasks/DONE/TASK-0213-strengthen-coupled-search-at-adequate-n.md`,
`results/tasks/0213_coupled_search_adequate_n/{budget,results,verdict,trajectory_diagnostics}.json`,
`scripts/task0213_coupled_search_adequate_n.py`.

---

## Seed provenance — 9 of 13 targets were seeded at graph hubs, not active sites (TASK-0216, 2026-08-13)

**A silent fallback in the core label pipeline, found while scoring
[[TASK-0215]]'s new pairs.** `labels.functional_indices` resolves the active
site by matching `func_ligand` codes against the holo entry's ligand groups.
When nothing matches it returns `np.argsort(-degree)[:5]` — the five
highest-degree residues — tagged `top-degree fallback`, **without warning**.

**Audit of all 13 register targets with a holo structure:**

| Seed resolves | Targets |
|---|---|
| REAL | KRAS_G12C (`GDP`), BCR_ABL1 (`NIL`), CARDIAC_MYOSIN (`ADP`), PFK (`F6P`/`ATP`) |
| **FALLBACK** | **PTP1B**, GLUCOKINASE, ATCase, CASPASE1, CASPASE7, HEMOGLOBIN, TAR_RECEPTOR, GLYCOGEN_PHOSPHORYLASE, GROEL_SUBUNIT |

Cause, visible in `targets.yaml` itself: `func_ligand` held **human-readable
descriptions rather than PDB chem-comp codes** — `'Glucose'` (code `GLC`),
`'substrate'`, `'O2', 'heme'`, `'Pi', 'G1P'`, `'Asp'`. PTP1B's entry is
self-describing: `'pTyr / active-site Cys215 (descriptive marker, not a
ligand code)'`.

**Why it matters twice over.** A degree-derived seed makes any seeded
observable a function of graph degree, so its mechanistic reading is not what
was measured; and `baselines.degree_centrality` is one of the three
proximity-floor baselines, so observable and floor then share a construction
and the comparison is no longer independent.

**Fixes landed:**
1. `targets.yaml` — 6 codes corrected against each holo entry's *actual*
   ligand set (`GLC`, `PAL`, `HEM`+`OXY`, `ASP`, `LLP`, `ADP`), never from
   memory; originals preserved in a new `func_ligand_original` field with a
   `func_ligand_note` explaining each. GLYCOGEN_PHOSPHORYLASE's is flagged a
   judgment call (`LLP` cofactor vs `GLS` inhibitor).
2. **3 targets genuinely have no functional ligand at all** — PTP1B (holo
   1T49 holds only drug 892 + MG), CASPASE1, CASPASE7. Set to `[]` with a
   note; their active sites must come from UniProt.
3. `labels.functional_indices` now emits a `RuntimeWarning` on fallback,
   naming the declared value and both hazards. It can no longer pass silently.

### PTP1B under a real seed — the register's only surviving positive

UniProt gives PTP1B's catalytic site as **[181, 215, 216, 217, 218, 219, 220,
221, 262]** — Cys215 plus the P-loop, identical on apo 1SUG and holo 1T49.

| | seed | pocket | max floor | `dcc_low` k=10 (whole-graph AUC) |
|---|---|---|---|---|
| fallback (what the register used) | [51, 87, 210, 214, 221] | 4 | 0.700 | 0.522 — below floor |
| **real (UniProt catalytic site)** | [181, 215–221, 262] | 4 | 0.701 | **0.389** — below floor |

**Seed overlap: 1 residue of 9.** Δ(whole-graph AUC) = **−0.133**.

**Stated precisely, because the temptation to overclaim is real:** this is
*not* a refutation of [[TASK-0201]]. That result used a **stratified**
well-powered-max AUC with a graph-walk permutation null; this is whole-graph
AUC, a different statistic, and the two are not comparable. What is
established is that the seed correction **materially changes the score
field** (overlap 1/9, Δ −0.133). Recomputing TASK-0201's own statistic under
the corrected seed is the outstanding measurement and has not been done.

### Independent corroboration from the new instances

Scoring [[TASK-0215]]'s pairs (`task0216_score_new_pairs.py`, leg A) — only
2 of 6 have a derivable real seed, the rest hitting the same fallback or an
apo/holo length mismatch:

| Target | floor | CTQW | `dcc_low` k=10 |
|---|---|---|---|
| GLUR2_ANIRACETAM | 0.811 | 0.735 (below) | **0.295** |
| GLUK1_BPAM | 0.761 | 0.796 (clears, +0.035) | **0.323** |

**`dcc_low` scores 0.295 and 0.323 on the first two instances where its seed
is real** — far below floor and below chance. Reached by a different route
from the PTP1B finding, pointing the same way.

### Coupled search on the new instances (leg B) — TASK-0213's verdict weakens

Re-running [[TASK-0213]]'s solver at 20×25 on the new pairs; only the 2 TEM-1
pairs pass the firewall and are interpretable (GLUR2_ANIRACETAM and
FPPS_YF0282 invert; GLUR2_TRU and GLUK1_BPAM error on an apo/holo length
mismatch and a degenerate ANM spectrum respectively):

| Target | successes / 20 | firewall |
|---|---|---|
| TEM1_BLA_CBT | **0/20** | ok |
| TEM1_BLA_FTA | **0/20** | ok |

Combined with [[TASK-0213]] the interpretable tally is now **KRAS_G12C 13/65
(20%), PTP1B 0/65, TEM1_CBT 0/20, TEM1_FTA 0/20 — 1 of 4 easy, 3 of 4 not.**
[[TASK-0213]]'s CLOSED verdict was correctly applied to its own pre-registered
2-target rule, but **KRAS_G12C now looks like the outlier rather than PTP1B**,
and the generalization of "search is not the bottleneck" is materially weaker
than that verdict reads on its own.

Full detail: `scripts/task0216_score_new_pairs.py`,
`scripts/task0216_ptp1b_real_seed.py`,
`results/tasks/0216_new_pair_scoring/{results,ptp1b_real_seed}.json`,
`config/candidate_targets_task0216.yaml`.

---

## Seed provenance closed out — the register's one positive does not survive its own seed correction (TASK-0217.003, 2026-08-14)

**Additive advisory on the section above, per this task's own Constraint —
nothing above is rewritten.** Three things the previous section left open
are now closed.

**1. The fallback count above (9 of 13) is the *pre-fix* number.** After the
6 `targets.yaml` corrections already landed (`GLC`/`PAL`/`HEM`+`OXY`/`ASP`/
`LLP`/`ADP`), **3 of 13 remain** — `PTP1B`, `CASPASE1`, `CASPASE7`, the ones
with no functional/substrate ligand in holo at all. Independently reconfirmed
by direct measurement, not re-cited: [[TASK-0217.001]]'s own construct-
validity sweep found this same 3/13 count from a different angle (its own
array-correspondence audit) before this task cross-referenced it against
`TASK-0216`'s original 9/13 — the two numbers describe different points in
time, not a disagreement.

**2. TASK-0201's own statistic, recomputed under the corrected seed — the
"outstanding measurement" the section above named as not yet done, is now
done, twice.** `scripts/task0216_task0201_rerun_real_seed.py` already
existed with a complete result when this task picked up; **independently
re-derived here from fresh code** (own construction of `source`/`shells`/
`pocket`, feeding the same already-validated `graph_walk_null` — the
statistical machinery itself is out of this task's scope per the parent's
own "leave the statistics, they are clean" boundary, but the *inputs* to it
are exactly what changed and are what this task re-derived independently):

| Seed | k=10 well-powered-max AUC | k=10 p-value | survives 0.05/16 bar |
|---|---|---|---|
| top-degree fallback (published, [[TASK-0201]]) | 1.000 | 0.00275 | yes |
| UniProt catalytic site (corrected) | **0.598** | **0.567** | **no** |

Independent re-derivation: AUC=0.5980392156862745, p=0.56725 — matches the
existing script's own recorded values exactly. **No k in {5, 10, 15, 20}
survives under the corrected seed** (full grid in
`results/tasks/0216_new_pair_scoring/task0201_rerun_real_seed.json`). The
wiring itself is trustworthy: the fallback-seed configuration, run through
the identical harness, reproduces the published p=0.0027 to within re-run
RNG noise (p=0.00275).

**A real discrepancy found and resolved while independently verifying
this**: `task0216_ptp1b_real_seed.py`'s own "real seed" pocket (4 residues)
and `task0216_task0201_rerun_real_seed.py`'s own "real seed" pocket (14
residues) disagree, because the first script only attaches heavy-atom
contact geometry when `len(apo.resnums) == len(holo.resnums)` (PTP1B's
don't: 298 vs 282) and silently falls back to the weaker Cα-only
approximation, while the second (via `run_challenge._load_apo_holo`)
attaches it unconditionally, matching [[TASK-0201]]'s own original
methodology and `labels.py`'s own documented heavy-atom-preferred
convention. The 14-residue/0.598-AUC number is the one comparable to
[[TASK-0201]]'s published result; the 4-residue/0.389 number in the section
above is a different, non-comparable measurement (as that section's own
text already correctly cautioned) and should not be read as a second
confirmation of anything.

**Plain statement, not softened**: **PTP1B `dcc_low` (k=10) was the
register's one surviving positive across ~226+ scored cells. Under the
seed it should have had all along, it does not survive at any tested k.**
The permutation-null machinery was never at fault (it shuffles pocket
labels, not seeds); what changed is what was being scored. Open-Questions
row 33 ([[TASK-0151]], above) ("the strongest cross-target evidence any observable in this
project has") and `documentation/PHASE1_SUBMISSION_DRAFT.md`'s own §2.4
("one surviving positive, reported with its provenance") both rest on the
uncorrected seed and should be read with this advisory attached, not as
still-standing claims — neither is rewritten here, per this task's own
additive-only Constraint; the submission draft is updated separately
(same task, see its own Done section).

**3. The fallback class itself is now closed, not just documented.**
`labels.functional_indices` gained a new tier (TASK-0217.003): a static,
curated `active_site_uniprot` field in `targets.yaml` (populated for
`PTP1B`/`CASPASE1`/`CASPASE7` from `backend/active_site.py::
detect_active_site`'s own UniProt lookup, ported as data rather than
imported as code per [[TASK-0018]]'s backend/allostery independence
boundary), consulted after `func_ligand` contact and before the top-degree
fallback. Confirmed: all 3 targets now resolve `provenance="active_site_
uniprot"` with zero warnings — every future run of `build_labels` on these
3 targets uses the real catalytic site automatically, not a one-off patch.
`CASPASE1`/`CASPASE7`'s own UniProt sites are their Cys/His catalytic
dyads (2 residues each) — real, biologically correct, and far more precise
than a 5-residue topological proxy.

**Not attempted, stated per this task's own scope boundary**: re-scoring
`CASPASE1`/`CASPASE7`'s own other seeded observables under their new,
correct seed (the parent task's own "not a re-run of ~190 tasks" applies;
this section only enumerates PTP1B's headline cell, the one a register-
level conclusion actually rested on). `GLUCOKINASE`/`ATCase`/`HEMOGLOBIN`/
`TAR_RECEPTOR`/`GLYCOGEN_PHOSPHORYLASE`/`GROEL_SUBUNIT` were already fixed
by `TASK-0216`'s own `func_ligand` corrections and are unaffected by this
task's own work beyond the count reconciliation in point 1.

Full detail: `.ai/tasks/DONE/TASK-0217.003-seed-anchor-provenance.md`.

## ANM subspace reachability of real apo→holo motion — PDB-retest reverses the synthetic-toy result ([[TASK-0227]], 2026-08-21)

An external review session (no repo access, no rcsb.org egress) filed [[TASK-0227]]:
static low-mode ANM subspaces looked "essentially orthogonal" (~0.000 overlap) to a
**synthetic** local 10 Å pocket-shell-opening deformation on non-target structures
(ADK, 1R19, 3HSY, 3ENL) — diagnosed as a real actuator/target scale gap. A same-day
follow-up ([[TASK-0228]]) corrected that number ~9× upward (0.024→0.229) using an
**adaptive** (per-step Hessian-rebuilt) subspace on the same synthetic deformation,
but flagged both numbers as untested on real targets and explicitly named the
PDB-retest as the cheapest, most decisive next step.

**Re-run on the real thing** (`__WORK_IN_PROGRESS__/results/tasks/0227_anm_rotamer_reachability/pdb_retest.py`,
harness functions imported unmodified from the drop's own scripts): true Kabsch-
superposed apo→holo Cα displacement, on the residue set resolved in both structures,
against the **static** apo ANM subspace (cutoff 15 Å), for all 3 pairs the task named:

| target | apo/holo | N common | RMSD (Å) | static overlap k=5/10/20/50 | adaptive/static ratio (dim=110) |
|---|---|---|---|---|---|
| KRAS_G12C | 4OBE→6OIM | 166 | 1.36 | 0.254 / 0.404 / 0.467 / **0.667** | 1.03× |
| BCR_ABL1 | 1OPL→5MO4 | 429 | 0.98 | 0.295 / 0.342 / 0.417 / **0.577** | 0.88× |
| CARDIAC_MYOSIN | 8QYP→8QYR (fully corrected**) | 698 | 1.18 | 0.595 / 0.766 / 0.826 / **0.901** | 1.01× |
| CARDIAC_MYOSIN | 5TBY→8QYR (holo-only corrected*) | 709 | 3.75 | 0.275 / 0.298 / 0.368 / 0.511 | 0.77× |
| CARDIAC_MYOSIN | 5TBY→6C1H (task's literal spec) | 366 | 26.80 | 0.043 / 0.087 / 0.192 / 0.386 | 1.46× |

\*`backend/systems.py` already flags 6C1H as an invalid comparison for this target
(Unconventional MYOSIN-Ib, actin-bound cryo-EM, no mavacamten — a different protein/
state, not a real apo/holo pair); its 26.8 Å "displacement" is the mismatch, not a
real conformational change. `holo_validation=8QYR` (real Beta-cardiac myosin,
mavacamten-bound) is this repo's own established correction — used above.
\*\*`__WORK_IN_PROGRESS__/config/targets.yaml` (TASK-0124) goes further: 5TBY itself
is a docked SWISS-MODEL homology model (20.0 Å nominal resolution, EM-fitted, zero
ligands, RCSB-verified 2026-08-19 per TASK-0222), not an experimental apo — `apo_pdb:
8QYP` is the real X-ray apo. The crude homology-model apo was suppressing the
apparent overlap by roughly half (0.51→0.90 at k=50), not changing its direction.

**Reverses the synthetic result, doesn't just correct its magnitude.** All 3 real,
valid target pairs clear TASK-0227's own pre-registered ≳0.5 "collective part
reachable" bar at k=50 (top 50 of several hundred non-rigid modes) — CARDIAC_MYOSIN
clears it by k=5 on the fully-corrected pair — nowhere near the ≲0.05 "model-class
failure" bar either synthetic number implied. **Plain static ANM already captures
more of the real transition (0.58–0.90) than the synthetic toy's own *adaptive*
correction claimed for its synthetic deformation (0.229), on every target.** The
adaptive/static ratio on real targets is 0.77×–1.46× (adaptive sometimes *worse* at
equal dimension) — on the highest-fidelity pair it's a bare 1.01×, essentially no
gain — nothing like the toy's reported 9.4×. Both the original ~0.000 and the
corrected ~9× findings were artifacts of the synthetic "adversarially local"
deformation type (flagged as a lower bound by its own §3.1 caveat), not of the ANM
model class against real collective backbone motion.

**Scope, precisely**: this measures the *whole* apo→holo Cα displacement's overlap
with the collective subspace — exactly TASK-0227 §5.1's own question, and (per that
task's own decision rule) sufficient to retire the "collective part unreachable"
framing. It does **not** re-test whether the *local, pocket-specific* residual
(§3's original narrower concern) is small — TASK-0227's own text already treats that
as the reduced, secondary question once the collective bar clears. §5.2 (oracle-
supervised reachability ceiling, needs a global-optimum side-chain repacker) and §5.3
(scorer-brittleness interpolation, needs a druggability scorer) were not attempted
under this task's own claim, out of "hours" scope — **not** because the tooling is
missing: `EvoEF2` (`__WORK_IN_PROGRESS__/tools/evoef2/bin/EvoEF2`) and `fpocket`
(`__WORK_IN_PROGRESS__/tools/fpocket/bin/fpocket`) are both already vendored in-repo
and working (a same-day re-check found an initial "both absent" claim here was
simply an inadequate search — bare `which` plus a depth-limited `find` that never
reached the repo's own `tools/` directory — corrected in the task's own Done
section). Both experiments are a real, tooling-unblocked option for a follow-up
task. Full detail: `.ai/tasks/DONE/TASK-0227-anm-rotamer-reachability-ceiling.md`.

**Addendum — the local residual this section flagged as untested, plus §6.2's `p`
([[TASK-0228]], 2026-08-21).** Three follow-ups on the same real target pairs above.

**(1) Pocket-restricted CO, the local residual.** Above measures the *whole-structure*
displacement; the labeled pocket's own restricted CO (`restricted_cumulative_overlap`,
[[TASK-0133]]'s Bessel-valid form — a genuinely different, harder-to-capture quantity
than a whole-structure average) at equal static/adaptive dimension (110):

| target | static CO | adaptive CO | ratio |
|---|---|---|---|
| KRAS_G12C | 0.640 | 0.840 | 1.31× |
| BCR_ABL1 | 0.481 | 0.353 | **0.73× (adaptive worse)** |
| CARDIAC_MYOSIN (8QYP→8QYR) | 0.430 | 0.612 | 1.42× |

Real, target-dependent, not the drop's own reported 9.4× win — but static pocket-CO
alone (0.43–0.64) already sits close to the drop's own *adaptive* number for its
synthetic deformation (0.229), before any correction. Consistent with the
whole-structure finding above: the synthetic deformation, not the ANM model class,
drove both original numbers.

**(2) §6.2 progress probability `p` — collective-only.** `holo_direction.build_
deformation_family`'s own admissible single-mode ANM moves (own smaller amplitude
grid, 0.1/0.2/0.3 — the module's frozen 0.5/1.0/2.0 protocol rejects 53–59/60
candidates here, unusably few), objective = does the move reduce the real pocket's
own mean Cα displacement from true holo:

| target | admissible | p |
|---|---|---|
| KRAS_G12C | 59 | 0.492 |
| BCR_ABL1 | 59 | 0.237 |
| CARDIAC_MYOSIN | 47 | 0.426 |

All 3 inside the register's own established 0.24–0.69 "not rare" band ([[TASK-0181]]/
[[TASK-0185]]) — same conclusion as every other progress-probability measurement in
this project.

**(3) §6.2 `p` — full joint (backbone + rotamer), same 47–59 admissible moves, 20
sampled per target, extended to real full-atom structures (`prody.extendVector`,
rigid per-residue broadcast — a real approximation, stated not hidden) and EvoEF2
`SideChainRepack`'d at the pocket window, scored on fpocket `druggability_score`
(the objective a rotamer move can actually change — backbone RMSD-to-holo cannot):**

| target | baseline druggability | p (backbone only) | p (backbone + repack) |
|---|---|---|---|
| KRAS_G12C | 0.001 | 0.25 | **1.00** |
| BCR_ABL1 | 0.566 | 0.20 | **0.05** |
| CARDIAC_MYOSIN | 0.001 | 0.50 | 0.65 |

**Sharply target-dependent, not a single verdict — the repack effect's direction
tracks the apo baseline's own druggability.** On the two genuinely cryptic targets
(baseline ≈0.001), repacking makes progress *more* likely, dramatically for
KRAS_G12C. On BCR_ABL1 (baseline 0.566, already above [[TASK-0204]]'s own 0.5
druggability bar — independently consistent with this project's established
"apo-computable structural prior" finding, [[TASK-0104]]/[[TASK-0091]]), EvoEF2's
energy-only repack more often degrades an already-good pocket than improves it: `p`
drops to 0.05, the one number in this project's progress-probability history
meaningfully below the 0.24–0.69 band. Amplitude amplification is not cleanly
retired at the joint layer the way it is at the collective-only layer.

**Cross-checked against [[TASK-0230]] (same day, independent build): baseline
druggability numbers match exactly** (KRAS_G12C 0.001, BCR_ABL1 0.566, CARDIAC_MYOSIN
0.001 — the same three below) — two independently-written pipelines agreeing is a
real consistency check, not assumed. TASK-0230's own §5.2 ceiling (true holo
displacement, not just a small admissible step, repacked) still fails to clear 0.5 on
any target, and its §5.3 finds fpocket's own score does not reliably track BCR_ABL1's
or CARDIAC_MYOSIN's real pocket at this window *at all* — a real caveat on reading
BCR_ABL1's `p=0.05` above as purely "repacking hurts": part of that number may be
fpocket scoring noise on a window TASK-0230 independently found unreliable for this
specific target, not only a genuine energy-vs-druggability mismatch. Both tasks'
own scripts + full detail: `.ai/tasks/DONE/TASK-0230-anm-ceiling-and-scorer-
brittleness.md`, `.ai/tasks/IN_PROGRESS/TASK-0228-conformer-graph-search-branching-
vs-depth.md`.

## Observable-family proximity confound — PDB-retest replicates the external drop's finding, real seeds/burial ([[TASK-0226]], 2026-08-21)

External drop (`.ai/reviews/2026-08-21/TASK-0210_observable_family_confound.md`, no repo
access, bundled non-target structures) claimed the proximity confound is a property of
seed-referencing scoring on a static contact graph, not of quantumness — CTQW the
*least* confounded of the seed-referencing family, only seed-blind observables escape.
Re-run on all 5 real targets (KRAS_G12C, BCR_ABL1, CARDIAC_MYOSIN, PTP1B, MYC_MAX) with
real annotated active-site seeds (`labels.functional_indices`, not radial-percentile
draws) and real per-residue SASA burial (freesasa, not centroid distance).

**Replicated, on real data**: partial Spearman rho(dist | SASA-burial), 76 real-seed
replicates pooled across 5 targets — `CTQW_adj_T25` **0.677** sits below every
seed-referencing classical observable tested (`GNM_corr_seed` 0.888, `GNM_corr_low10`
0.865, `heat_T5` 0.806, `dMSF_at_seed` 0.795, the challenge's own cited `MRW_commute`
ref[8] 0.755). Only seed-blind observables meaningfully escape: `dS_vib_global` **0.082**
(clean), `slow1_minima` (this task's own ref[16] proxy) 0.496 ± 0.193 (partial, wide
spread — real and less clean than the drop's own non-target-structure number, 0.292).

**Resolves (partially) the drop's own flagged discrepancy**: `prs_low` (0.232) escapes
the confound substantially better than either DCC-style observable tested — this
repo's own canonical `dcc_low` (k=20, 0.384) or a direct port of the drop's own 10-mode
`GNM_corr_low10` (0.865). A real PRS-vs-DCC family asymmetry, though mode-count/seed-
cardinality differ between the two DCC variants and are not cleanly isolated.

**New, not in the drop**: `transmission_E0` (ref[7], Landauer T(E=0) on the GNM
Laplacian) does *not* strengthen the negative result as hoped — one of the most
confounded observables tested (0.795), consistent with this project's own prior
transport/`1/R_eff` correlation finding ([[TASK-0145]]). `chiral_circ` (this project's
own candidate proximity-orthogonal quantity, [[TASK-0140]]) shows a real partial escape
(0.540) — worse than the seed-blind pair, meaningfully better than every other
seed-referencing observable.

**Negative control** (drop's own explicit requirement, corrected Rg-matched null per
`nulls.graph_walk_patch_matched`, not the anti-conservative scattered null): a real
stiff channel planted from KRAS_G12C's P-loop seed to a floor-blind, far-hop distal
patch. `slow1_minima` shows nominal enrichment (p=0.028, does not survive even a
2-comparison Bonferroni bar); `dS_vib_global` shows none at this single tested
strength (p=0.33). **Mixed, not a clean confirmation** — a single-condition check, not
a formal LOD sweep.

65 confound-structure comparison cells (13 observables x 5 targets) + 2 negative-
control cells — not added to this document's own "Program-level multiple-comparison
budget" (that table's scope is real-label AUC/p-value comparisons; confound-structure
correlations and synthetic-signal negative controls are both outside its own stated
definition), logged here per the drop's own request. Full numbers, methodology, and
bug-catches: `.ai/tasks/DONE/TASK-0226-observable-family-proximity-confound-pdb-retest.md`.

## ANM reachability ceiling + scorer-brittleness control — ceiling fails on all 3 real targets, robustly ([[TASK-0230]], 2026-08-21)

[[TASK-0227]]'s own §5.2 (oracle-supervised reachability ceiling) and §5.3
(scorer-brittleness interpolation), deferred there for a tooling reason that turned
out to be wrong (EvoEF2/fpocket are both vendored, `tools/evoef2/`, `tools/fpocket/`) —
run here on the same 3 real target pairs, reusing `allostery.superpose`'s own
Kabsch+ANM machinery and [[TASK-0204]]'s own EvoEF2/fpocket wiring, not re-derived.
Per this task's own Intent Contract, the repacker is EvoEF2's `SideChainRepack`
(real simulated annealing) — a heuristic ceiling, honestly downgraded from the
source's own DEE/A*/Rosetta global-optimum spec, which is not installed here.

**§5.2 — fails on all 3 targets, every trial, robust to EvoEF2's own stochastic
seeding** (fpocket `druggability_score`, [[TASK-0204]]'s own ≥0.5 bar; the true
apo→holo displacement projected onto only the top-50 static ANM modes, applied as a
rigid per-residue Cα translation, pocket window then repacked):

| target | native apo | true holo (same window) | projected + repacked (all independent trials) |
|---|---|---|---|
| KRAS_G12C | 0.001 | 0.886 | 0.0, 0.0, 0.01 |
| BCR_ABL1 | 0.566 | 0.356 | 0.026, 0.335, 0.031, 0.165, 0.159, 0.0 (6 trials, range 0.0–0.335) |
| CARDIAC_MYOSIN | 0.001 | 0.166 | 0.017, 0.095 |

None cross 0.5, on any trial. **Unregistered but directly relevant**: `true_holo`
itself only clears the bar for KRAS_G12C (0.886) — BCR_ABL1 (0.356) and
CARDIAC_MYOSIN (0.166) don't, even at the real crystallized structure, and
BCR_ABL1's untouched native apo (0.566) actually scores *higher* than its own holo.
fpocket's druggability score is not reliably tracking these 2 targets' real pockets
at this window at all, ceiling aside.

**§5.3 — confirmed, richer than the source's own binary framing.** 20-step linear
apo→holo interpolation (same rigid per-residue approximation, no repacking), scored
per step. The pre-registered proxy (`<3 of 19 mid-steps land between apo/holo scores
→ flat-then-cliff`) mislabeled KRAS_G12C's own raw curve — flat at ≈0.001 for 8
steps, then a single-step jump to 0.777, then noisy-high — the textbook cliff shape,
missed because the proxy only checks endpoint bracketing, not transition shape (own
limitation, stated up front in the Intent Contract, confirmed by the data). BCR_ABL1
shows a front-loaded drop (0.566→≈0.2 within 4 steps, noisy-low the rest of the way,
proxy agreed). CARDIAC_MYOSIN never registers a pocket above 0.017 across all 20
steps — apo/holo endpoints (0.001/0.005) are both noise-floor, a third mode
(non-responsiveness) neither label describes; proxy's "pass" here is not meaningful.
**fpocket's druggability score is not a safe optimization objective on any of the 3
real targets, regardless of which shape a given target shows.**

Both results point the same direction as the source document's own §6.1 diagnosis
(local backbone rearrangement, spanned by neither collective ANM modes nor
side-chain repacking, is what's missing) — a second, independent line of evidence,
not a contradiction of [[TASK-0227]]'s own §5.1 (collective motion IS reachable).
Full tables, per-step curves, and the chain-relabeling bug found and fixed en route
(latent in [[TASK-0204]]'s own original function too, not fixed there):
`.ai/tasks/DONE/TASK-0230-anm-ceiling-and-scorer-brittleness.md`.

**Addendum — the stronger (full-displacement) ceiling exposes a real confound, not a
missed positive (2026-08-21).** User's own follow-up: was §5.2 under-powered (only
k=50 modes), and is the rigid-translation approximation itself trustworthy? Both
checked directly. Supplying the FULL true displacement instead of k=50 modes did
**not** flip any target to a clean positive — all 12 repacked trials (4 independent
EvoEF2 seeds × 3 targets) stayed below the 0.5 bar (closest: BCR_ABL1, max 0.432).
But a new geometry-sanity check (EvoEF2 `ComputeStability`'s `interS_vdwrep`, steric
clash) found the pre-repack full-displacement structures sit **3–12× native apo's own
clash energy** (worst on KRAS_G12C, 12.1×) — and KRAS_G12C's one apparent "positive"
(pre-repack druggability 0.79, crosses the bar) is exactly the most clash-distorted
structure, almost certainly a geometric artifact (an overlapping, non-physical cavity
fpocket's detector mistakes for an open pocket), not a real signal. Side-chain-only
repacking (EvoEF2 `SideChainRepack`) recovers some of the clash but never approaches
native apo's own relaxed state on any target. **Conclusion: the rigid-per-residue-
translation backbone-placement method is not trustworthy enough to believe either a
positive or a negative from it** — every ceiling result in this task (both passes) is
confounded by its own structural approximation, not just measuring pocket
reachability. [[TASK-0227]]'s own §5.1 (static, non-adaptive low-mode overlap,
0.58–0.90 on real targets, no rigid-translation step, no repacking) remains the
program's cleanest positive evidence that the *collective* part is reachable; this
task's own data neither closes nor opens the *local* half — "not shown open by any
method tried here, and the method itself isn't yet trustworthy enough to fully
believe that negative." Full tables:
`.ai/tasks/DONE/TASK-0230-anm-ceiling-and-scorer-brittleness.md`'s own Addendum.

**Addendum 2 — a real energy calculation (EvoEF2 `RepairStructure` vs. `SideChainRepack`)
directly reproduces the source document's own §6.1 diagnosis on one real target
(2026-08-22).** On KRAS_G12C only: a lightly-relaxed state (`RepairStructure`, clash
energy down 3.4× from raw but still ~3.5× native apo) stays apparently open
(druggability 0.726); once side chains are genuinely energy-*minimized*
(`SideChainRepack`, real simulated annealing) at essentially the same clash level
(285.7 vs. 297.0 `vdwrep`), the pocket collapses (0.004) — closure tracks which
rotamers get chosen, not overall relaxation amount. Direct, real-target confirmation
of "QUBO returns a minimum; cryptic pockets are excited states... minimising energy
over backbone⊕rotamers returns the apo structure" — previously a theoretical
objection in the source document, now one observed instance. Does not replicate on
BCR_ABL1/CARDIAC_MYOSIN (both stay near-zero at every relaxation level tried,
consistent with their own weak-holo-recognition caveat above, not a new confound).
Bears directly on any QUBO/quantum-optimization formulation for this problem: bare
energy minimization over rotamers will systematically return the closed state
regardless of solver — classical or quantum — unless reformulated as the source's
own proposal (minimum energy cost to *open* a pocket, a constrained objective, not
bare minimization), which remains untested. Full tables:
`.ai/tasks/DONE/TASK-0230-anm-ceiling-and-scorer-brittleness.md`'s Addendum 2.

## Conformational-selection reframing — the collective transition is thermodynamically cheap, not just geometrically aligned ([[TASK-0233]], 2026-08-22)

User's own proposal: what if the drug stabilizes a pre-existing, sparsely-populated
conformer (conformational selection / population shift, Monod-Wyman-Changeux 1965)
rather than inducing a new one? This directly reframes [[TASK-0230]] Addendum 2's own
"minimization returns the closed state" finding from a puzzle into an *expected*
result under this model — minimization from one structure finds the dominant state
by construction, never a rare minor one; that was never evidence against a rare open
state existing.

Reusing [[TASK-0015]]'s own already-validated `allostery.superpose.run_superpose`/
`mode_energetics` unmodified (`E_k = 0.5·κ·λ_k·c_k²`, B-factor-calibrated per target,
this project's own established "kT=1" relative-scale convention): the true apo→holo
displacement, projected onto the top-50 soft ANM modes, costs **0.20–2.32 "thermal
units" total** on all 3 real targets (KRAS_G12C 2.32, BCR_ABL1 0.37, CARDIAC_MYOSIN
0.20) — 1–9% of the naive 25-unit scale 50 equally-excited modes would imply.
`exp(−ΔG)` (Boltzmann weight vs. the apo minimum) is **0.10–0.82 on all 3 targets —
within an order of magnitude of 1, not exponentially suppressed.** The true
displacement is dominated by the softest available modes (90% of the overlap reached
by just 3–28 of 50 modes) — a real, quantitative extension of [[TASK-0227]] §5.1's
own geometric mode-overlap finding (0.58–0.90) to an actual thermodynamic
plausibility read, not just a directional alignment one.

**Lower bound only**: CO(k=50) is 0.766–0.954, not 1.0 — 5–23% of the true
displacement is the *local* residual ANM's coarse network can't represent, exactly
where [[TASK-0230]]'s own real all-atom pipeline found genuine difficulty (severe
clash, minimization returning to closed). Cross-referenced against [[TASK-0228]]'s
own independently-measured progress probability `p` (collective-only: 0.237–0.492 on
all 3 targets, same "not rare" conclusion via a completely different method — real
incremental moves + repack, not a mode-projection ceiling): two independent methods
now agree the collective layer is cheap; the joint (collective+local) layer's own
difficulty ([[TASK-0230]]'s ceiling failing every trial; [[TASK-0228]]'s own joint `p`
sharply target-dependent, KRAS_G12C 0.25→1.00 vs. BCR_ABL1 0.05) looks like a
search-method/path-dependence question at that layer, not a flat "closed" verdict.

Per the Architect's own [[Q-0005]] answer, the graduation condition (calibrated ΔG
plausible, few kT) is met for the collective layer on all 3 targets — [[TASK-0234]]
filed: a third quantum hypothesis (Gibbs/Boltzmann sampling over collective conformer
space via a quantum walk, distinct from QUBO-minimization and Montanaro backtracking
search), named and scoped to the collective layer specifically, not built or costed.
Full numbers: `.ai/tasks/DONE/TASK-0233-conformational-selection-reframing.md`.

## Quantum Gibbs-sampling hypothesis retired — the collective layer is not rare, four independent measurements agree ([[TASK-0234]], 2026-08-23)

[[TASK-0233]]'s own graduation condition (ΔG plausible, few kT) was necessary but not
sufficient — a quantum search/sampling speedup needs the target state to be *rare*,
not merely thermodynamically plausible. Checking the [[TASK-0229]] hypothesis family's
own outcomes on pickup (per instruction) surfaced [[TASK-0185]] (2026-08-02, pre-dating
this whole line of work by three weeks): real ANM Boltzmann-ensemble sampling
(`allostery.shortcuts.equipartition_ensemble`, the actual classical version of what
[[TASK-0234]] proposed accelerating) already recovers the real pocket in **1–8
classical draws** on every real target — *"a Grover-style backbone-layer rare-event
search argument requires a rare target event, and it is not rare on any real target
measured here."*

**Four independent methods, three weeks, one conclusion**: [[TASK-0185]]'s real-
ensemble recovery rate and its own n_modes sweep (p=0.244–0.694, 2026-08-02),
[[TASK-0228]]'s progress probability `p` (0.237–0.492, 2026-08-21/22), and
[[TASK-0233]]'s own harmonic Boltzmann weight (`exp(−ΔG)`=0.10–0.82, 2026-08-22/23) all
agree the collective layer is not rare. **A second, independent disqualifier**: quantum
Gibbs sampling's own value proposition is a mixing-time speedup over a slow-converging
MCMC process — `equipartition_ensemble` is not that, it is a closed-form, exact,
one-shot Gaussian draw (the ANM harmonic ensemble's equilibrium distribution is
analytically known). There is no mixing-time bottleneck to accelerate, independent of
the rarity finding.

**Checked whether this reasoning extends to the joint (collective+side-chain) layer,
not assumed**: [[TASK-0204]]'s own exact rotamer solver (bucket elimination, real
pocket windows, 0.001–0.159s, validated against brute force) already closes that layer
too — an exact solver this cheap leaves nothing for a sampling algorithm, quantum or
classical, to accelerate. **Both layers this program has actually modeled turn out
classically cheap by exact or near-exact methods.** [[TASK-0234]] retired, not
scoped-for-later; its Done section records the correction plainly, and
[[TASK-0233]]'s own Done section carries a matching correction note rather than being
left silently stale.

**What this leaves as the program's real remaining gap**: [[TASK-0230]]'s own
still-open finding (severe steric clash from rigid-per-residue backbone translation)
is a classical structural-modeling-fidelity problem, not a search-cost one — solving it
would let the program's own already-cheap collective sampling and already-exact
rotamer solving be trusted on a physically realistic structure, not create a new
quantum opportunity. Full write-up:
`.ai/tasks/DONE/TASK-0234-quantum-gibbs-sampling-collective-layer.md`.

## HIV-1 RT independent run, threshold inversion, and a register-wide stale-number finding ([[TASK-0238]], 2026-08-24)

**[OBSERVED]** Filed to answer two questions raised against this register from
outside it: *how strict is our threshold*, and *is it too strict*. An
independent target (HIV-1 reverse transcriptase, never previously scored here)
was run end-to-end, then the same score was pushed through every null and every
gate the register uses, one relaxation at a time.

### Leg A — HIV-1 RT, standard settings

`1DLO` (apo, X-ray 2.7 Å, chain A, 556 res, **zero HETATM** — genuinely
unliganded) → `3V81` (holo, 2.85 Å, chain A, contains **NVP**/nevirapine).
Seed is the UniProt-annotated catalytic site `[110, 185, 186, 443, 478, 498,
549]` (D110/D185/D186 triad confirmed as ASP) — a **real seed, not a
top-degree fallback**. `enm_cutoff` 8.0, `pocket_contact_cutoff` 4.5,
pocket = 16 residues after active-site and terminal exclusion.

| observable | AUC | vs floor 0.7773 | p (scattered) | p (compact) | p (graph-walk) |
|---|---|---|---|---|---|
| `ctqw_converged` (`H_new`) | 0.7538 | below (−0.0235) | **0.0005** | 0.1999 | 0.2024 |
| `dcc_low` k=10 | 0.5211 | below | 0.3743 | 0.4778 | 0.4793 |

**The `ctqw` row is the cleanest localisation of the null disagreement this
register has produced.** Same structure, same seed, same score vector, same
2000 permutations. `p = 0.0005` under a scattered (`rng.choice`) label
permutation; `p ≈ 0.20` under a spatially-contiguous one. A **400× spread
attributable to nothing but the null**. Any two threads disagreeing about
whether this target is a hit are not disagreeing about physics, code, or data
— they are disagreeing about one line of null construction, and that is now a
measured quantity rather than an argument.

### Leg B1 — wiring check failed, and the failure was the finding

The check was "reproduce KRAS_G12C's published floor 0.4818 through this code
path." It did not reproduce. Chasing it: the register's **own entry point**
(`scripts/run_challenge.py`, run fresh) now yields floor **0.5296**, CTQW
**0.5565**. The published 0.4818/0.5901 are **stale**.

| target | floor pub | floor now | Δ | AUC pub | AUC now | Δ | margin pub | margin now |
|---|---|---|---|---|---|---|---|---|
| KRAS_G12C | 0.4818 | 0.5296 | +0.0478 | 0.5901 | 0.5565 | −0.0336 | +0.1083 | **+0.0269** |
| BCR_ABL1 | 0.5817 | 0.5031 | −0.0786 | 0.5266 | 0.5408 | +0.0142 | −0.0551 | **+0.0377** |
| CARDIAC_MYOSIN | 0.5679 | 0.4538 | −0.1141 | 0.5176 | 0.5485 | +0.0309 | −0.0503 | **+0.0947** |

Cause identified: commit `1924e5e` ([[TASK-0217.001]]) fixed a live
array-correspondence bug in `labels.functional_indices` — holo-space
heavy-atom contact indices used directly as apo-space indices — exposing 10 of
13 targets. That commit correctly re-pinned fpocket's golden AUC, but the
headline floor/actual triplets were never refreshed. They are still cited as
current in `COMPETENCE_MAP.md`, `EXECUTION_PLAN.md`, `ALGORITHM_REGISTER.md`,
this document, and — materially — in
`documentation/PHASE1_SUBMISSION_DRAFT.md:146`.

**Two consequences point in opposite directions and both must be reported:**

1. `COMPETENCE_MAP.md:240`'s "actual (0.5901) now clears its own floor
   (0.4818)" margin of +0.1083 is actually **+0.0269** — the flagship
   KRAS_G12C claim is ~4× weaker than stated.
2. On BCR_ABL1 and CARDIAC_MYOSIN the point-estimate margin **flips sign**,
   from below-floor to above-floor. The register has been reporting these two
   as floor failures; under current code they are not. Their negative
   diagnoses (`NO_SIGNAL_IN_APO` on both, re-confirmed this run) now come from
   the **chance bar, not the floor gate**.

Neither direction was sought. Point 2 is a correction *against* this
reviewer's own prior reporting and is stated with the same prominence as
point 1.

### Leg B2 — is the floor itself significant? (HIV-1 RT)

| baseline | AUC | p (scattered) | p (compact) |
|---|---|---|---|
| `degree_centrality` | 0.5811 | 0.1419 | 0.4313 |
| `euclid_from_seed_centroid` | 0.3662 | 0.9640 | 0.6712 |
| `hop_from_seed` | **0.7773** | **0.0005** | 0.2259 |

The binding floor, `hop_from_seed`, has **the same p-value profile as the CTQW
score it is gating** (0.0005 scattered / 0.2259 compact vs 0.0005 / 0.1999).
"Below floor" and "null under the compact null" are therefore **not two
independent failures** — they are one fact counted twice. The floor gate is
not contributing the extra strictness the register credits it with; it is a
second reading of the same seed-proximity confound.

### Leg B3 — threshold inversion

CTQW AUC 0.7538, floor 0.7773, deficit +0.0235. Gates relaxed one at a time:

| gate configuration | verdict |
|---|---|
| as-published (floor gate + compact null, α=0.05) | negative |
| relax **null** only → scattered | negative |
| relax **floor** only → drop floor gate, keep compact | negative |
| relax **both** → scattered null, no floor gate | **POSITIVE** |
| relax both + Bonferroni ×28 (α=0.0018) | **POSITIVE** |

Neither relaxation alone flips the verdict; **both together do, and decisively
— it survives a ×28 Bonferroni correction.** This is the honest answer to "is
our threshold too strict": our two gates are individually load-bearing here,
and B2 shows they are not independent of one another.

### Leg B3b — what would the parameter set have to be?

Pre-registered grid, fixed before any number was seen: `enm_cutoff`
{7,8,9,10} × `pocket_contact_cutoff` {4.0,4.5,5.0,6.0} × observables
{`ctqw`, `ctqw` coherent, `dcc_low` k∈{5,10,20}} = **80 configurations**.
Positive ≡ AUC > max_floor **and** p_compact < 0.05.

- **0 of 80 positive.**
- 16 of 80 beat the floor (all `ctqw`; `enm` 7/9/10 — notably **not** 8, the
  configured value).
- **0 of 80 reach p_compact < 0.05.** Not one. The best p across the entire
  grid is 0.1374.
- Closest to positive: `ctqw`, `enm=9.0`, `pocket_cut=6.0`, AUC 0.7822 vs
  floor 0.7178, p_compact 0.1414.

**There is no "slightly more permissive" parameter set that rescues this
target.** The floor gate is soft — a routine cutoff change crosses it — but
the compact null is not: it is not crossed anywhere in an 80-point grid
spanning every knob the pipeline exposes. If the register's threshold is too
strict, the strictness lives entirely in the null, and nowhere in the
parameters.

### Wiring defect found and fixed en route

`scripts/task0216_score_new_pairs.py:110` and
`scripts/task0216_ptp1b_real_seed.py:71` gate heavy-atom attachment on
`len(holo.resnums) == len(apo.resnums)`. That guard is required only for
`functional_indices` (which contacts holo heavy atoms against *apo* coords);
`holo_pocket_mask` maps holo→apo by Needleman-Wunsch and needs no such
precondition. Applying it to the pocket silently degrades the label to a
Cα-only approximation — `labels.py`'s own docstring measures that at **9/21**
pocket residues recovered on KRAS_G12C. On HIV-1 RT the pocket went **5 → 16**
residues once corrected, moving the floor 0.8175 → 0.7773 and the CTQW AUC
0.7129 → 0.7538. Leg A above is the corrected run. Every other script in
`scripts/` attaches heavy atoms unconditionally and is unaffected.

**Scripts:** `scripts/task0238_hiv1rt_and_threshold.py`,
`scripts/task0238_legb_threshold_inversion.py`,
`scripts/task0238_floor_convention.py`.
**Data:** `results/tasks/0238_hiv1rt/`.

## Backbone-placement fidelity fix — BCR_ABL1's ceiling reverses, KRAS_G12C's stays closed for an independently-explained reason ([[TASK-0235]], 2026-08-24)

[[TASK-0230]]/[[TASK-0233]] both named the rigid-per-residue backbone
translation used throughout that line of work as a real confound (native
apo `vdwrep` elevated 3–12× even after the best relaxation tried). This
task built the fix: a local sliding-window Kabsch reconstruction (each
residue's own local rigid transform, fit from sequence-consecutive
neighbor Cα positions, reusing `allostery.superpose.kabsch_fit`/
`kabsch_apply` — no new dependency), chosen over literal phi/psi+NeRF
reconstruction for handling backbone and side chain in one step.

**Real, partial geometry improvement, concentrated where the old method
was worst**: full-displacement pre-repack `vdwrep` ratio to native apo —
KRAS_G12C 12.07×→**6.46×** (nearly halved), BCR_ABL1 2.92×→2.86×,
CARDIAC_MYOSIN 3.02×→2.84× (both near-unchanged). Does not clear this
task's own "close to native apo" bar — reported as partial, not oversold.

**Decisive, target-dependent ceiling result**: re-running [[TASK-0230]]'s
own §5.2-style ceiling (4 EvoEF2 trials/target) with the corrected
backbone — **BCR_ABL1 flips from 0/4 to 4/4 trials clearing the 0.5
druggability bar** (0.656–0.725, old method's own max was 0.432, never
crossed) — consistent with, not independent of, this project's own
repeated "apo-computable structural prior" finding for this target
([[TASK-0104]]/[[TASK-0091]]). CARDIAC_MYOSIN: 0/4→1/4 (real but noisy).
KRAS_G12C: unchanged, 0/4→0/4.

**KRAS_G12C's non-improvement is independently explained, not just
observed**: extending [[TASK-0233]]'s own harmonic ΔG machinery to full
non-rigid mode coverage isolates the *local residual*'s own elastic
cost (`ΔG(all modes) − ΔG(k=50)`) — KRAS_G12C **33.0** additional thermal
units (`exp(−ΔG_all)`≈4.6×10⁻¹⁶, astronomically costly), vs. BCR_ABL1
8.57 (`exp`≈1.3×10⁻⁴) and CARDIAC_MYOSIN 5.04 (`exp`≈5.3×10⁻³) — directly
matching which targets a backbone-placement fix could and couldn't
unlock. [[TASK-0230]]'s own "ceiling fails on all 3 targets" headline is
superseded for BCR_ABL1 and partially for CARDIAC_MYOSIN by this result
— addendum added to that task's own Done section rather than left stale.
Full tables: `.ai/tasks/DONE/TASK-0235-backbone-modeling-fidelity.md`.

## Addendum to TASK-0235 — the BCR_ABL1 ceiling flip does not reproduce ([[TASK-0241]], 2026-08-24)

**[OBSERVED]** Reviewer re-verification of [[TASK-0235]]'s headline. Recorded
here rather than only in the task file because TASK-0235's result **superseded
[[TASK-0230]]'s "ceiling fails on all 3 targets" verdict** for BCR_ABL1, and
that supersession is already carried in this document.

`ceiling_rerun("BCR_ABL1")` re-run unmodified, same commit (`8be3742`), same
machine:

| | trial 0 | trial 1 | trial 2 | trial 3 | ≥0.5 bar |
|---|---|---|---|---|---|
| TASK-0235 as published | 0.675 | 0.719 | 0.656 | 0.725 | 4/4 |
| reproduction | 0.703 | **0.351** | 0.703 | 0.719 | **3/4** |

Trial 1's 0.351 falls **below the old method's own maximum (0.432)** — the
very comparison the "decisive, not a noisy improvement" claim rests on.

**Root cause: the four trials are not four samples.** `ceiling_rerun`'s loop
varies nothing between iterations — same structure reloaded, same deterministic
`local_rigid_reconstruction`, and `_run_evoef2("SideChainRepack", …)` accepts
no seed. Verified directly: all four trial input PDBs are **byte-identical**
(sha256 `af8a9a85e8f1315a…`, 294143 bytes, 4/4). Effective **n = 1**; the
observed spread is EvoEF2/fpocket jitter. Trials 0 and 2 returning *exactly*
0.703 confirms it, as do the exact duplicate pairs in the published run
(`0.23, 0.432, 0.23, 0.432`).

**The jitter exceeds the effect.** On byte-identical input, druggability spans
0.351–0.719 and `overlap_frac` spans 0.25–0.50, against a bar of 0.5. The
verdict sits inside the noise band.

**Under this register's own composite criterion the result is 1/4, not 4/4.**
`_is_hit` (`task0204_rotamer_repack_baseline.py:223`) requires
`overlap_frac ≥ 0.5` **and** `druggability ≥ 0.5` — fpocket must find *the
target cavity*, not merely a druggable one. In the reproduction `hit` was True
in 1 of 4 trials. Note this criterion relaxation originates at [[TASK-0230]]
(`any_trial_crosses_bar`), which TASK-0235 inherited consistently — it affects
both tasks' ceiling verdicts, not just the newer one.

**Mechanism tension, unresolved.** Across targets the geometry improvement
anti-correlates with the ceiling outcome: KRAS_G12C −46% vdwrep → no change
(0/4→0/4); BCR_ABL1 −2.1% → total flip (0/4→4/4). TASK-0235 explains
KRAS_G12C's non-flip via ΔG(residual)=33 thermal units (a sound, separate
measurement) but not BCR_ABL1's flip, and it simultaneously states that
BCR_ABL1's residual excess is "by construction outside what any
per-residue-local method can fix." A testable reconciliation exists —
`vdwrep` scores steric clash while fpocket scores cavity shape, so coherent
side-chain rotation can reshape a cavity at near-constant clash energy — but
it is a different claim from the one made.

**Not in dispute:** the local sliding-window Kabsch method itself; KRAS_G12C's
real 12.07×→6.46× geometry improvement; the ΔG(k=50) vs ΔG(all modes)
residual-cost calculation. The defect is the inferential step from 4 repeats
to "decisive", not the method. **3/4 above the bar on re-run is not nothing** —
[[TASK-0241]] exists to establish it properly, not to discard it.

Until then, **[[TASK-0230]]'s "ceiling fails on all 3 targets" should be read
as still standing**, with BCR_ABL1 flagged as contested rather than reversed.

**Script:** `scripts/task0238_verify0235_trial_independence.py`.

## Resolution — properly powered, real trial variation confirms a modest, unproven trend, not "decisive" ([[TASK-0241]], 2026-08-24)

Two experiments (`scripts/task0241_reproducibility_and_jitter.py`, real
EvoEF2/fpocket calls, N=20/arm — this task's own Acceptance floor):

**(A) Pure repacking jitter, ONE fixed BCR_ABL1 backbone per method** (no
structural variation at all, isolates EvoEF2/fpocket's own stochastic
spread): bare druggability-bar rate **old 4/20 (20%) vs new 15/20
(75%)** — Fisher exact **p=0.0012**, genuinely significant. The originally
published "4/4" is an ordinary draw from this real ~75% process (binomial
P(4 of 4)=0.316); the reproduction's "3/4" (P=0.422) is equally ordinary —
neither run was wrong, n=4 just couldn't distinguish them. **Under this
register's own strict `_is_hit` (overlap≥0.5 AND druggability≥0.5), the
SAME fixed geometry hits only 1/20 (5%) old vs 3/20 (15%) new — Fisher
p=0.605, not significant.** Bare druggability substantially overstates the
effect.

**(B) Real re-run, all 3 targets × both methods, independent σ=0.15Å
per-trial perturbation of the displacement field** (genuine structural
variation, not just repacking-seed jitter): BCR_ABL1 `_is_hit` rate 1/20
(5%) old vs 4/20 (20%) new — 4× higher, same direction as TASK-0235
claimed, **Fisher p=0.342, not significant at n=20**. Druggability medians
(0.516 vs 0.617) don't clear significance either (Mann-Whitney p=0.882).
KRAS_G12C and CARDIAC_MYOSIN: no significant difference, matching their own
already-honest "closed"/"noisy" characterization.

**Mechanism resolved, not left contradictory**: `vdwrep` (clash) and
`overlap_frac` (cavity shape) move independently, confirming the proposed
reconciliation rather than a real contradiction — BCR_ABL1 vdwrep −2.1% vs
overlap_frac **+12.3%**; KRAS_G12C vdwrep **−46.5%** vs overlap_frac only
+11.4%; CARDIAC_MYOSIN vdwrep −6.0% vs overlap_frac **−12.3%** (opposite
sign). A method's effect on one is not evidence of its effect on the other.

**Net verdict**: "decisive... not a noisy improvement" is not supported —
downgraded to a real, same-direction, statistically unproven trend at
n=20/arm. [[TASK-0230]]'s Addendum 4 carries the full numbers; this task's
own Done section has the reproducible scripts. `_is_hit`, not bare
druggability, is recommended as this line of work's primary ceiling
criterion going forward — no prior justification for the relaxed bar exists
in either task's record.

## Properly powered re-run of the collaborating thread's two-stage protocol — the "CTQW leads every control" finding does not survive ([[TASK-0243]], 2026-08-24)

**[OBSERVED]** A prior dry run of the collaborating thread's proposed
protocol ([[TASK-0242]], candidate pockets from fpocket on apo, ONE
pre-registered operator H_new/CTQW converged, hop reported as a covariate)
found CTQW leading every control in direction at n=7 untuned targets, none
significant, and explicitly flagged the fix needed: "n ≥ 12 untuned
targets, not 5" — the effect had already weakened as the sample grew
(Fisher p 0.053 at n=4 → 0.164 at n=7). This task supplied the sample: 22
new untuned pairs, curated live against RCSB
(`config/candidate_targets_task0243.yaml`, full curation-order log in
`results/tasks/0243_curate_untuned_targets/`), 6 of 28 raw automated finds
excluded on direct inspection before freezing (DTT/G3H misclassified as
"drug" by the automated picker; two eIF4E entries where the picker chose
the orthosteric cap-analog cofactor over the real allosteric compound,
re-verified to fail the VALID rule outright under the correct ligand — the
same TASK-0169-style diligence this register requires, not a literature
table trusted blindly).

That dry run's own `prep`/`run` machinery reused unchanged
(`scripts/task0243_stage1_and_rerun.py`). **Real bug found and fixed
along the way**: `prep()`'s direct `prody.parsePDB()` calls carry the
exact same defect [[TASK-0039]] just fixed in `allostery.clean.clean()`
— default `altloc="A"` silently drops a ligand whose only conformer is
labelled otherwise (NAMPT's own ligand, altloc='D', crashed `prep()`
outright). Patched locally in this task's own wrapper (the dry run's own
script itself untouched, another thread's artifact); the other 21
targets' numbers were bit-for-bit unchanged after the patch, confirming
nothing else was silently affected.

**Stage-1 recall 16/22 = 72.7%** (vs the prior dry run's own 64%).

| ranker | mean rank (n=16) | MRR | top-1 |
|---|---|---|---|
| fpocket_drug | **8.12** | **0.483** | 6/16 |
| fpocket_score | 7.56 | 0.342 | 2/16 |
| **ctqw** | 9.50 | 0.286 | 3/16 |
| random | 16.38 | 0.195 | 2/16 |
| hop_covariate | 13.00 | 0.194 | 1/16 |

Head-to-head: **ctqw vs fpocket_drug 5–9–2 (ctqw loses more often now),
Wilcoxon p=0.509** — the direction the n=7 dry run found has reversed,
not merely lost significance. ctqw vs hop_covariate 8–5–3, p=0.248 — a
little more separation than the dry run's own exact tie, still not
significant. **ctqw vs random: 12–1–3, Wilcoxon p=0.0157 — survives
Bonferroni (α=0.05/3) — the one individually significant result**, and
the weakest, least informative of the three: it shows CTQW is not noise,
not that it beats the actual competing baseline (fpocket's own
druggability score) the two-stage design exists to test against.

**Per this task's own pre-registered Constraint ("a positive is as
reportable as a negative")**: reported exactly as it landed, not
softened. The dry run's own optimistic reading does not survive proper
power. Full tables, exclusion diligence, and curation-order log:
`.ai/tasks/DONE/TASK-0243-untuned-target-curation-for-joint-two-stage-experiment.md`.

**Scripts:** `scripts/task0243_curate_untuned_targets.py`,
`scripts/task0243_stage1_and_rerun.py`.
**Data:** `results/tasks/0243_curate_untuned_targets/`.

## Two-stage (fpocket candidates → operator ranks within) dry run — the collaborating thread's protocol, executed on our side ([[TASK-0242]], 2026-08-24)

**[OBSERVED]** A collaborating thread raised a methodological objection this
register had not tested: their pipeline uses fpocket to propose **candidate
pockets** and an operator to rank *within* that candidate set. That is a
different experiment from this register's per-residue AUC, and they are
correct that our compact-patch null does not test it. Rebuilt to their spec
rather than argued with.

**Their spec, adopted verbatim:** candidate pockets from fpocket on apo;
`MIN_HOP = 2` distality filter; **one** pre-registered operator (`H_new` /
converged incoherent CTQW, this register's GAUGE, fixed before any number was
seen); hop reported as a **covariate, not a filter**; targets neither side
tuned on.

**The control their argument omits.** Their supporting statistic — Friedman
p=1.6e-224, W=0.466 across 14 Hamiltonians, modal pocket = true drug pocket —
measures *agreement between operators*, not validity. Operators sharing a
confound agree perfectly and are wrong together; this register measured that
degeneracy directly ([[TASK-0199]]: ~28 observables → effective rank 2.6–4.1).
The question consensus cannot answer is whether the operator ranks the true
pocket better than **fpocket's own druggability score already does, on the
identical candidate list**. Every ranker below is scored on that same list.

### Results — rank of the true drug pocket (1 = best), K = surviving candidates

| target | tuned on | K | **ctqw** | fpocket_drug | fpocket_score | hop | random |
|---|---|---|---|---|---|---|---|
| HIV1_RT | no | 34 | **4** | 33 | 10 | 9 | 19 |
| GLUR2_TRU | no | 12 | **4** | 7 | 6 | 2 | 2 |
| GLUR2_ANIRACETAM | no | 12 | **1** | 7 | 4 | 2 | 11 |
| GLUK1_BPAM | no | 7 | **1** | 1 | 1 | 3 | 4 |
| PTP1B | no | 14 | 9 | 3 | 14 | 12 | 8 |
| GLUCOKINASE | no | 17 | **5** | 10 | 16 | 6 | 8 |
| CASPASE7 | no | 19 | **16** | 18 | 13 | 6 | 17 |
| KRAS_G12C | *yes* | 7 | 1 | 4 | 4 | 2 | 6 |
| BCR_ABL1 | *yes* | 22 | 10 | 1 | 1 | 9 | 9 |
| CARDIAC_MYOSIN | *yes* | 42 | 19 | 40 | 39 | 19 | 7 |

TEM1_BLA_CBT, TEM1_BLA_FTA, FPPS_YF0282, CASPASE1 dropped: **fpocket never
proposed the true pocket at all**. Stage-1 recall **7/11 = 64%**.

| ranker | Fisher p | MRR | top-1 (conditional) | top-1 (end-to-end) |
|---|---|---|---|---|
| **ctqw** | **0.164** | **0.411** | **2/7** | **2/11** |
| fpocket_drug | 0.736 | 0.258 | 1/7 | 1/11 |
| fpocket_score | 0.701 | 0.247 | 1/7 | 1/11 |
| hop_covariate | 0.300 | 0.266 | 0/7 | 0/11 |
| random | 0.838 | 0.172 | 0/7 | 0/11 |

### Three findings, in order of importance

**1. The effect weakened as the sample grew.** At n=4 (the first pass, the
candidate set only) CTQW's Fisher p was **0.053**. At n=7 it is **0.164**.
Direction held, significance did not. This is the signature of a small-sample
fluctuation, and it is the single strongest argument against signing a joint
protocol at the proposed 5-target scale — by either side, in either direction.

**2. CTQW leads every control in direction, none significantly.** Head-to-head
against fpocket's own druggability on the identical candidate list: **5 wins,
1 loss, 1 tie** — sign test p=0.109, Wilcoxon p=0.125. Real and consistent in
sign; not established.

**3. CTQW is not distinguishable from the hop covariate.** Mean rank **5.71
for both**, Wilcoxon p=0.297. fpocket uses no seed information whatsoever, so
*any* seed-aware ranker beats it — and the trivial seed-aware ranker does
exactly as well as the quantum walk on mean rank. **CTQW's apparent edge over
fpocket is fully consistent with it being a proximity-to-seed ranker.** This is
the confound the proposed design does not control: hop as a *covariate* is not
enough, it must appear as a competing *ranker* in the same table.

### Consequence for the proposed joint experiment

The protocol is sound and worth running, with three amendments:

- **Denominator = targets attempted**, not targets where stage 1 succeeded.
  Conditional top-1 2/7 is 2/11 end-to-end; a within-candidate metric cannot
  see the 36% of targets where fpocket never proposes the true pocket.
- **n ≥ 12 untuned targets**, not 5. Finding 1 is the direct evidence.
- **fpocket's own druggability AND the hop ranker as named control arms.**
  Both must be beaten for the operator to be doing work.

**Script:** `scripts/task0242_two_stage_dryrun.py`.
**Data:** `results/tasks/0242_two_stage_dryrun/dryrun.json`.

## Variance attribution, CROSS-VALIDATED — supersedes the in-sample estimate ([[TASK-0245]], 2026-08-24)

[[TASK-0238]]'s attribution was an in-sample OLS stack, flagged there as an
optimistic ceiling with the explicit prediction that cross-validation would
lower the stack AUC and **raise** the unexplained share. That check has now
been run. The prediction held; these numbers supersede it as the estimate of
record. The in-sample section is kept above per this document's
no-silent-overwrite convention.

5-fold stratified CV, 20 repeats, out-of-fold scoring, seed rows excluded,
n = 9 targets (up from 4).

| target | geometry | CTQW | **unexplained** |
|---|---|---|---|
| KRAS_G12C | 58% | 8% | **34%** |
| BCR_ABL1 | 5% | −1% | **96%** |
| CARDIAC_MYOSIN | 0% | 15% | **93%** |
| HIV1_RT | 54% | 0% | **45%** |
| PTP1B | 28% | −1% | **73%** |
| GLUCOKINASE | 30% | 3% | **67%** |
| CASPASE7 | 0% | −4% | **108%** |
| GLUR2_TRU | 46% | 2% | **51%** |
| GLUK1_BPAM | 84% | 1% | **16%** |
| **range (median)** | **0–84% (30%)** | **−4 to +15% (+1%)** | **16–108% (67%)** |

**Estimate of record: unexplained 16–108% (median 67%); geometry 0–84%
(median 30%); CTQW −4% to +15% (median +1%).**

Movement from the in-sample estimate, all in the predicted direction:

| | in-sample (n=4) | cross-validated (n=9) |
|---|---|---|
| unexplained | 27–80%, median ~51% | **16–108%, median 67%** |
| geometry | 19–65%, median ~35% | **0–84%, median 30%** |
| CTQW | 1–13%, median ~5% | **−4 to +15%, median +1%** |

Notes on reading it: a share above 100% (CASPASE7) means the stacked model
scored *below* chance out-of-fold — nothing we have generalises there. CTQW's
increment is **negative on 3 of 9 targets** and its median is +1%, i.e. not
distinguishable from zero. Its two largest values (CARDIAC_MYOSIN +15%,
GLUK1_BPAM +1% over the full block but +17.9% over hop alone) occur where the
geometry block is weakest, so it is partly filling a vacuum rather than adding
orthogonal information.

Corroborated independently by [[TASK-0244]]'s two-stage controls, a different
experimental design: CTQW and a plain hop ranker tie at mean rank 5.71
(Wilcoxon p=0.594 two-sided); partialling hop out of CTQW makes it *worse*
(6.29 vs 5.71); the true pocket beats a hop-matched candidate null on only 2/7
targets (Fisher p=0.50, chance expectation 0.93/7).

**Script:** `scripts/task0245_cv_attribution.py`.
**Data:** `results/tasks/0245_cv_attribution/results.json`.

## Is CTQW just a re-encoded distance score? No — but its non-distance signal duplicates two simpler baselines ([[TASK-0247]], 2026-08-24)

**[OBSERVED]** [[TASK-0245]]/[[TASK-0244]] established that CTQW's incremental
contribution over the geometry block is ~0 (median +1% CV). That is easily
misread as "CTQW is a distance score in disguise." It is **not**, and this
section records the correction with the same prominence as the original claim.

Decisive test: **within-shell AUC.** Stratify residues by BFS hop shell — inside
a shell, distance-from-seed is constant — and ask whether the score still
separates pocket from non-pocket.

| target | ρ(ctqw, hop) | R² on shell indicators | AUC uncond. | **AUC within shell** |
|---|---|---|---|---|
| KRAS_G12C | −0.773 | 0.420 | 0.6190 | 0.5595 |
| BCR_ABL1 | −0.729 | 0.609 | 0.5752 | 0.6499 |
| CARDIAC_MYOSIN | −0.750 | 0.489 | 0.5632 | 0.6690 |
| HIV1_RT | −0.686 | 0.438 | 0.7538 | 0.5466 |
| PTP1B | −0.508 | 0.272 | 0.5244 | 0.6305 |
| GLUCOKINASE | −0.573 | 0.304 | 0.4853 | 0.4019 |
| CASPASE7 | −0.464 | 0.364 | 0.6103 | 0.5816 |
| GLUR2_TRU | −0.384 | 0.270 | 0.7900 | 0.7680 |
| GLUK1_BPAM | −0.601 | 0.390 | 0.8393 | 0.7672 |
| **median** | **0.601** | **0.390** | 0.6103 | **0.6305** |

**CTQW is not a distance score.** Only ~39% of its variance is a pure function
of hop shell. With distance held constant it still discriminates at median AUC
**0.6305** — *higher* than its unconditional AUC — above 0.5 on 8/9 targets,
above 0.55 on 7/9, one-sample Wilcoxon vs 0.5 **p=0.0273**. It computes
something real that proximity does not.

**But that something is already supplied by two much simpler quantities.** The
same within-shell comparison, all features on equal footing:

| target | ctqw | degree | euclid | best geometry | ctqw − best |
|---|---|---|---|---|---|
| KRAS_G12C | 0.5595 | 0.5709 | 0.7940 | 0.7940 | −0.2344 |
| BCR_ABL1 | 0.6499 | 0.5452 | 0.5619 | 0.5619 | +0.0881 |
| CARDIAC_MYOSIN | 0.6690 | 0.5898 | 0.5591 | 0.5898 | +0.0791 |
| HIV1_RT | 0.5466 | 0.5126 | 0.6292 | 0.6292 | −0.0827 |
| PTP1B | 0.6305 | 0.5356 | 0.5910 | 0.5910 | +0.0395 |
| GLUCOKINASE | 0.4019 | 0.5713 | 0.6605 | 0.6605 | −0.2586 |
| CASPASE7 | 0.5816 | 0.5885 | 0.5172 | 0.5885 | −0.0069 |
| GLUR2_TRU | 0.7680 | 0.6324 | 0.6016 | 0.6324 | +0.1355 |
| GLUK1_BPAM | 0.7672 | 0.6663 | 0.9382 | 0.9382 | −0.1710 |
| **median** | **0.6305** | 0.5713 | **0.6292** | **0.6292** | +0.0013 |

CTQW beats the best geometric baseline within-shell on **4/9** targets,
Wilcoxon **p=0.4961**. Statistically indistinguishable.

**Correct statement of the finding, superseding the looser phrasing in
[[TASK-0245]]'s section:** CTQW is not an overcomplicated distance score — it
is an overcomplicated *burial-plus-distance* score. Its non-proximity content
is real and measurable, and it is the same content `degree_centrality` and
`euclid_from_seed_centroid` deliver in two lines of numpy. The correct claim is
"adds nothing over the **full geometry block**", not "adds nothing over
**proximity**". The two are different and this register should not conflate
them.

**Script:** `scripts/task0247_is_ctqw_a_distance_score.py`.

## The composite "DUMB" baseline decisively beats CTQW, both designs, proper power ([[TASK-0249]], 2026-08-24)

Built the strongest simple, classical competitor this register can assemble
(fpocket druggability + banded hop-shell one-hot + degree + euclid, LOTO-fit —
"doing their homework" for the joint two-stage experiment with the
collaborating thread) and gave the operator every chance to beat it, on
[[TASK-0243]]'s own frozen, untuned 22-target set (20/22 usable), reusing
[[TASK-0242]]'s own apparatus and [[TASK-0246]]'s own one-hot encoding
verbatim.

**Headline, per-residue AUC (LOTO, median, n=20)**: `fpocket_drug` alone
**0.756**, `composite+ctqw` 0.730, `composite` 0.710, `ctqw` **0.592**,
random 0.521, `hop` alone 0.431 (see below). **Two-stage candidate ranking
(LOTO, denominator = 22 targets attempted)**: `fpocket_drug` alone MRR
**0.344**/top-1 6, `composite+ctqw` 0.320/5, `composite` 0.304/5, `ctqw`
**0.161**/2, `hop` 0.067/0, random 0.046/0.

**Explicit answer to this task's own central question**: CTQW's own
incremental value over the composite is small and positive (`composite+ctqw
− composite` = +0.020 AUC / +0.016 MRR) — real in direction, not a driver of
the result. **The composite, and even `fpocket_drug` alone (its single
strongest ingredient, no fitting needed), both clearly and substantially
beat CTQW on its own** — 0.710/0.756 vs. 0.592 per-residue; MRR 0.304/0.344
vs. 0.161 two-stage. Reported exactly as it landed, per this task's own
Constraint that a negative is as reportable as a positive: **on this
untuned, frozen, proper-power set, the operator does not beat the honest
classical baselines it should be compared against.**

**Unregistered nuance, load-bearing for how the composite itself should be
read**: `fpocket_drug` alone beats the full 4-feature composite in both
designs — adding banded-hop/degree/euclid does not help under true
cross-target LOTO, even though [[TASK-0246]]'s own within-target CV found
real signal in the banded hop encoding. This register's own strongest
simple baseline for the joint experiment is `fpocket_drug` alone, not the
4-feature composite.

**A real data-quality defect found in [[TASK-0243]]'s own frozen set**:
`HIV_INTEGRASE_MUT871`/`HIV_INTEGRASE_MUT916` (apo `1M9D`) have an empty
active-site seed on every one of 1M9D's 4 chains — confirmed directly,
contradicting that task's own "zero fell back to a top-degree proxy" claim.
Handled as a real target-attempted failure (excluded from the pooled LOTO
fit, counted in every denominator above), flagged for whoever owns that
curation next, not investigated further here.

**`hop` alone scoring below random (0.431 median) under LOTO is real, not a
bug** — checked directly (13/20 targets below 0.5, not a single-target
artifact; the same `hop_from_seed` direction embedded inside `composite`
performs well, confirming no sign-flip). Read as a genuine LOTO-
generalization failure specific to the 8-column one-hot encoding across a
much wider size range (225–1205 residues) than [[TASK-0246]]'s own
within-target-CV set.

Preliminary (labelled as such, [[TASK-0245]]'s own 9-target set, n too
small to trust over the headline): `fpocket_drug` 0.638, `composite+ctqw`
0.622, `ctqw` 0.610, `composite` 0.582 — a different, reversed ranking
between `composite` and `ctqw` than the headline, exactly the
underpowered-sample instability [[TASK-0243]] was filed to resolve.

**Script:** `scripts/task0249_composite_dumb_baseline.py`. **Full tables:**
`.ai/tasks/DONE/TASK-0249-composite-dumb-baseline-vs-ctqw.md`'s Done
section.

## GNM model-validity check (H16.1) — never run before, real and mixed (TASK-0250, 2026-08-24)

GNM/ANM is used everywhere in this register (`dcc_low`, `prs_low`, mode energetics,
two-state ANM, ANM reachability) and the standard per-target model-validity check —
does the model's predicted mean-square fluctuation correlate with deposited
crystallographic B-factors — had never been run. **Pre-registered bar** (stated in the
task filing before any correlation below was computed): Pearson >= 0.6 PASS, 0.4-0.6
MARGINAL, < 0.4 FAIL. GNM MSF via `potentials._gnm_msf` (this project's own existing
implementation, not re-derived) against each target's own real apo Cα B-factors, at
the real `enm_cutoff` each target is actually scored with (uniformly 8.0 Å across all
15 real targets — not re-tuned to make the correlation pass, per the task's own
Constraint).

**One target excluded from the tally, checked directly against RCSB before scoring**:
CARDIAC_MYOSIN_TABLE1's apo (5TBY) is ELECTRON MICROSCOPY at nominal 20.0 Å resolution
— no meaningful per-atom B-factor refinement at that resolution, an invalid input, not
a model failure.

| Target | apo | N | Pearson | Spearman | Verdict |
|---|---|---|---|---|---|
| KRAS_G12C | 4OBE | 169 | 0.646 | 0.636 | PASS |
| BCR_ABL1 | 1OPL | 451 | 0.493 | 0.558 | MARGINAL |
| CARDIAC_MYOSIN | 8QYP | 704 | 0.686 | 0.671 | PASS |
| CARDIAC_MYOSIN_TABLE1 | 5TBY | 950 | 0.435 | 0.693 | *unusable, cryo-EM 20 Å* |
| MYC_MAX | 1NKP | 171 | 0.148 | 0.244 | **FAIL** |
| PTP1B | 1SUG | 298 | 0.663 | 0.753 | PASS |
| GLUCOKINASE | 1V4S | 448 | 0.473 | 0.535 | MARGINAL |
| ATCase | 6AT1 | 912 | 0.148 | 0.051 | **FAIL** |
| CASPASE1 | 1ICE | 255 | 0.368 | 0.521 | **FAIL** |
| CASPASE7 | 1F1J | 461 | 0.695 | 0.631 | PASS |
| HEMOGLOBIN | 2HHB | 574 | 0.602 | 0.636 | PASS |
| TAR_RECEPTOR | 1LIH | 160 | 0.525 | 0.286 | MARGINAL |
| GLYCOGEN_PHOSPHORYLASE | 1GPY | 828 | 0.410 | 0.316 | MARGINAL |
| PFK | 1PFK | 640 | 0.708 | 0.729 | PASS |
| GROEL_SUBUNIT | 1GRL | 3626 | 0.350 | 0.357 | **FAIL** |

**14 scored: 6 PASS, 4 MARGINAL, 4 FAIL — GNM is not a valid model of the structure
for nearly a third of this project's own real targets, at the cutoff it actually
uses.** Consequential for the mandatory set specifically: **MYC_MAX FAILs cleanly**
(0.148 — barely above chance) and **BCR_ABL1 is MARGINAL** (0.493). Every GNM/ANM-
derived quantity this register has reported for MYC_MAX (mode energetics, ANM
reachability, `dcc_low`/`prs_low` where computed) rests on a model that does not
predict that structure's own crystallographic B-factors — read as "the model may not
fit MYC_MAX," not additional evidence about allostery, until re-examined. BCR_ABL1's
own GNM-derived numbers (including this register's `AUC_apo_Hnew_optimised`
headline) carry a real, now-quantified model-fit uncertainty this register did not
previously state. KRAS_G12C and CARDIAC_MYOSIN both clear the PASS bar — the
mandatory-set negatives on those two targets are not explained by this failure mode.

**Not done, per this task's own scope**: no downstream result was re-run, re-qualified,
or re-derived — this task states the consequence, a follow-up decides what (if
anything) to do about MYC_MAX's/BCR_ABL1's existing numbers. **Script:**
`scripts/task0250_gnm_bfactor_validity.py`. **Raw data:**
`results/tasks/0250_gnm_bfactor_validity/gnm_bfactor_validity.json`. **Full detail:**
`.ai/tasks/DONE/TASK-0250-h16-1-gnm-model-validity-b-factors.md`.

## fpocket in the variance stack: the "67% unexplained" headline was missing its strongest predictor — corrected to 29%, order-independent (TASK-0254, 2026-08-24)

[[TASK-0245]]'s own cross-validated attribution (geometry/CTQW/unexplained =
30%/+1%/67% median, n=9) never included `fpocket` — [[TASK-0249]] then found
`fpocket_drug` alone reaches median per-residue AUC **0.756** on the frozen
22-target set, higher than the whole 4-feature composite. This task re-runs the
attribution with fpocket in the stack, **order-independent** (geometry and
fpocket are correlated; a fixed entry order misassigns their shared variance —
exact Shapley value over the 3 blocks, 3! = 6 orderings, cheap to brute-force),
on [[TASK-0243]]'s frozen 22-target set (n=20 usable, matching [[TASK-0249]]'s
own filter exactly). Method: [[TASK-0245]]'s own protocol verbatim (5-fold
stratified CV, 20 repeats, out-of-fold, OLS via `lstsq`, seed rows excluded) —
extended from 2 blocks to 3, sequential attribution replaced with Shapley.

### Part A — order-independent 4-block attribution

| target | geometry | fpocket | CTQW | **unexplained** | full AUC |
|---|---|---|---|---|---|
| GAC_BPTES | 47% | 56% | −6% | **4%** | 0.982 |
| GAC_CPD12 | 53% | 34% | −9% | **22%** | 0.891 |
| DHPS_GC7 | 30% | 1% | 26% | **43%** | 0.784 |
| PF_ATCASE | 54% | 40% | −2% | **9%** | 0.957 |
| KSHV_PROTEASE_24Q | 6% | 12% | 26% | **55%** | 0.724 |
| KSHV_PROTEASE_25G | 17% | 8% | 13% | **62%** | 0.692 |
| SUMO_E1_FHJ | 41% | 8% | 22% | **30%** | 0.852 |
| HCV_NS5B_VRX | 34% | 47% | −6% | **25%** | 0.874 |
| HCV_NS5B_VR1 | 41% | 41% | −6% | **24%** | 0.881 |
| HCV_NS5B_POO | 51% | 8% | 11% | **30%** | 0.852 |
| HCV_NS5B_CMF | 51% | 8% | 11% | **30%** | 0.852 |
| FBPASE_94D | 83% | 0% | −15% | **32%** | 0.840 |
| FBPASE_95S | 70% | −7% | −6% | **43%** | 0.787 |
| TRP_SYNTHASE_F6F | 26% | 45% | 2% | **27%** | 0.864 |
| TRP_SYNTHASE_F19 | 36% | 33% | −2% | **33%** | 0.833 |
| SMYD3_DIPERODON | 19% | 65% | 14% | **2%** | 0.990 |
| PKR_MITAPIVAT | 60% | −7% | 20% | **28%** | 0.862 |
| PKR_AG946 | 63% | −7% | 17% | **27%** | 0.864 |
| MKK7_IBRUTINIB | 39% | 3% | 49% | **9%** | 0.957 |
| NAMPT_NPA1R | 42% | −9% | 25% | **42%** | 0.789 |
| **range (median)** | **6–83% (42%)** | **−9 to +65% (+8%)** | **−15 to +49% (+11%)** | **2–62% (29%)** | — |

**The headline moves materially: unexplained median 67% → 29%.** Most of what
[[TASK-0245]]'s 3-block model called "unexplained" was static pocket geometry
fpocket measures and the three simple baselines don't — exactly this task's own
hypothesis, confirmed. **fpocket's own Shapley share is wide and target-
dependent (−9% to +65%)**, not uniformly large — on some targets it explains
most of the discrimination (SMYD3_DIPERODON 65%, GAC_BPTES 56%), on others
essentially nothing or slightly negative (PKR_MITAPIVAT/PKR_AG946 −7%). **CTQW's
own share also moved, from median +1% to median +11%** — a real, reportable
change from properly partitioning shared variance with Shapley rather than a
fixed-order sequential fit (the old 3-block sequential design could credit a
correlated confound to whichever block entered first; order-independence
removes that artifact in both directions, not just fpocket's). CTQW's range is
still wide and includes clearly negative cases (FBPASE_94D −15%), so "CTQW adds
something now" is not the reading either — read as: once fpocket and geometry's
shared variance is fairly split, CTQW's own real, small, target-dependent
contribution becomes visible instead of buried in whichever block absorbed it
first.

### Part B — apo crypticity screen

No systematic screen existed before this task; the register had exactly one
target (BCR_ABL1, RMSD ratio 0.49, [[TASK-0120]]/[[TASK-0139]]/[[TASK-0169]]).
**Pre-registered overlap definition** (stated before any number below was
computed): a true-pocket residue counts as "already open in apo" if it belongs
to *any* apo-side fpocket-detected pocket (not just the top-ranked candidate),
residue-level. **Pre-registered bar**: ≥80% open ⇒ target tests static
retrieval, not cryptic-site discovery.

| target | open/true | fraction | already-open? |
|---|---|---|---|
| GAC_BPTES | 8/8 | 100.0% | **yes** |
| GAC_CPD12 | 6/6 | 100.0% | **yes** |
| PF_ATCASE | 5/5 | 100.0% | **yes** |
| SMYD3_DIPERODON | 11/11 | 100.0% | **yes** |
| PKR_MITAPIVAT | 11/12 | 91.7% | **yes** |
| HCV_NS5B_VRX | 13/15 | 86.7% | **yes** |
| TRP_SYNTHASE_F6F | 13/15 | 86.7% | **yes** |
| HCV_NS5B_VR1 | 14/17 | 82.4% | **yes** |
| PKR_AG946 | 9/11 | 81.8% | **yes** |
| TRP_SYNTHASE_F19 | 14/18 | 77.8% | no |
| NAMPT_NPA1R | 13/17 | 76.5% | no |
| SUMO_E1_FHJ | 9/13 | 69.2% | no |
| DHPS_GC7 | 5/8 | 62.5% | no |
| MKK7_IBRUTINIB | 6/11 | 54.5% | no |
| HCV_NS5B_POO | 8/16 | 50.0% | no |
| HCV_NS5B_CMF | 8/16 | 50.0% | no |
| FBPASE_95S | 2/4 | 50.0% | no |
| KSHV_PROTEASE_24Q | 6/15 | 40.0% | no |
| KSHV_PROTEASE_25G | 5/13 | 38.5% | no |
| FBPASE_94D | 0/3 | 0.0% | no |

**9/20 (45%) of the frozen set is already-open in apo.** That number belongs
in the submission regardless of which way it came out, per this task's own
instruction — it does, both ways: nearly half the "cryptic-site discovery"
benchmark is not testing cryptic-site discovery at all.

**Cross-tabulation against [[TASK-0249]]'s own per-target `fpocket_drug` AUC —
the prediction tested, confirmed cleanly**: median AUC on already-open targets
**0.854**, median AUC on cryptic-testing targets **0.515** (barely above
chance). `fpocket_drug` scores highest almost exactly where the pocket was
never hidden to begin with. **The benchmark's apparent difficulty is
substantially a mixture of two different tasks** — static retrieval (already-
open, fpocket-solvable) and genuine cryptic-site discovery (closed in apo,
fpocket near chance) — bundled into one reported number throughout this
register's prior work.

**Not done, per this task's own scope**: no existing scored result (TASK-0245's
own 9-target table, TASK-0249's own composite numbers) was re-derived under
this new attribution — this task supersedes the *headline estimate* (the number
cited going forward) while leaving those tasks' own Done sections and original
tables intact, per this document's no-silent-overwrite convention.
`documentation/PHASE1_SUBMISSION_DRAFT.md` §2.3b updated in the same commit,
since the 67% figure moved materially, per this task's own Acceptance
requirement.

**Script:** `scripts/task0254_fpocket_variance_and_crypticity.py`. **Data:**
`results/tasks/0254_fpocket_variance_and_crypticity/`. **Full detail:**
`.ai/tasks/DONE/TASK-0254-fpocket-in-the-variance-stack-and-apo-crypticity-screen.md`.

## `MIN_HOP >= 2` does not mean "genuinely distal" — the answer key itself fails a separation bar on 16/20 targets ([[TASK-0255]], 2026-08-25)

**[OBSERVED]** [[TASK-0246]] found pocket residues concentrate at graph-hop
2-4 from the active site; `MIN_HOP = 2` is the two-stage design's own
operational definition of "distal" ([[TASK-0242]]/[[TASK-0244]]/[[TASK-0249]]).
[[TASK-0169]] had already found one case (KRAS_G12C, min Ca-Ca 3.75 A) where
a nominally-distal pocket sits at van der Waals contact range. This task
calibrated hop against real 3D separation across [[TASK-0243]]'s full frozen
22-target set, using minimum HEAVY-ATOM distance (not Ca-Ca — side chains
reach several A closer than backbone), to find out whether TASK-0169's case
was an outlier or the norm.

**It is the norm, not the outlier.** Per-target true-pocket (the answer key
itself, not a fpocket candidate) minimum heavy-atom distance to the active
site: **20/20 usable targets fail a 20 A genuine-separation bar; 16/20 fail
even 15 A.** Several sit under 1.5 A (DHPS_GC7 1.33, PF_ATCASE 1.36,
TRP_SYNTHASE 1.29, MKK7_IBRUTINIB 1.32, FBPASE_95S 1.35) — spot-checked one
(DHPS_GC7) directly: its closest true-pocket residue is hop **1** from the
active site, an immediate contact-graph neighbour, confirmed not a bug.

**Hop -> Angstrom calibration, pooled across all 20 targets, all residues**
(median [IQR] / **min**): hop1 3.18 [1.38,3.76] / **1.21**; hop2 7.50
[6.35,8.94] / **2.09**; hop3 12.14 [10.66,13.79] / **2.79**; hop4 16.88
[14.96,18.58] / **3.55**; hop5 21.72 [19.23,23.57] / **7.02**; hop6 26.47
[23.85,28.81] / **10.42**; hop7 31.48 [27.39,33.91] / **7.73**; hop8+ 40.96
[36.42,46.54] / **17.63**. Both readings are real at once: the *median*
grows monotonically (hop is a genuine aggregate distance signal), but the
*minimum* stays under 4 A through hop 4 — `MIN_HOP >= 2` guarantees a
graph-contact path of >=2 edges, nothing about any single candidate's real
spatial separation. Candidate-level check: **115/492 (23.4%)** of fpocket
candidates surviving `MIN_HOP >= 2` across the frozen set have a residue
within 8 A of the active site despite passing the filter.

**Cost of a hard 15-20 A floor, measured not assumed**: 15 A removes 8/14
currently-scoreable targets (57%) and 327/407 surviving candidates (80%);
20 A removes 10/14 (71%) and 365/407 (90%).

**Recommendation: not a hard floor.** Two independent reasons: the cost
alone is severe, and more fundamentally the answer key itself fails the bar
in most targets — a hard filter built from it would in those cases exclude
the *correct* candidate from the pool, which is worse than an uninformative
filter. Recommended instead: keep `MIN_HOP >= 2` as the primary gate (its
median trend is real); report minimum heavy-atom distance as a **required
disclosed statistic** alongside every scored candidate and the true pocket,
never again silently read as "genuinely separated"; treat distality as a
covariate/competing feature (as [[TASK-0244]] already does for hop, and
[[TASK-0249]]'s composite baseline already does structurally) rather than a
binary gate, since no single Ångström threshold both excludes noise and
retains the ground truth on this frozen set.

**Real bug found and fixed en route**: `allostery.labels.
protein_heavy_atoms_by_residue`'s own residue-lookup dict is keyed on bare
residue number only, which silently collapses same-numbered residues across
chains in a multi-chain target — confirmed on GAC_BPTES (3 chains, 1223
residues, only 411 unique resnums; the bare-resnum map left 812/1223
residues with zero heavy atoms mapped). Not fixed at the shared helper
(other established callers, out of this task's scope) — re-implemented
locally in this task's own script, keyed on `(chain, resnum)`.

**Note for the collaborating thread**: `MIN_HOP` is a parameter their own
joint protocol proposes to freeze. This calibration is the reason it should
not be frozen as a hard distality gate without disclosure — both threads
would otherwise be freezing a parameter that does not mean what its name
implies for any single candidate, even though it remains a real, useful
aggregate signal in the median.

**Script:** `scripts/task0255_hop_angstrom_calibration.py`. **Data:**
`results/tasks/0255_hop_angstrom_calibration/calibration.json`. **Full
detail:** `.ai/tasks/DONE/TASK-0255-hop-to-angstrom-distality-calibration.md`.

## Two independent attempts to fix the ENM model neither move CTQW off zero ([[TASK-0257]], 2026-08-25)

**[OBSERVED]** [[TASK-0250]] found the Cα-only GNM invalid (B-factor
correlation) on 4/15 targets and MARGINAL on 5 more; [[TASK-0254]] found
CTQW's own marginal contribution when added last (after geometry+fpocket)
is indistinguishable from zero (median −0.06%, Wilcoxon p=0.50). The one
substantive objection left standing: "the model never got a fair run."
This task ran the two cheapest rungs of a pre-registered improvement
ladder against that objection, each scored first on the same label-free
B-factor objective before any pocket-label evaluation.

**R1 (heavy-atom contact weighting, replacing the binary Cα cutoff with a
count of heavy-atom pairs within 4.5 A, same N)**: net **negative** on the
15-target GNM-B-factor check — baseline 6 PASS/4 MARGINAL/4 FAIL becomes
4 PASS/6 MARGINAL/4 FAIL. **0/4 originally-FAIL targets improve past
FAIL.** 2 targets regress from PASS to MARGINAL (KRAS_G12C, PFK). Real,
mixed, target-dependent underneath the net negative (7/14 up, 7/14 down).

**R2 (real SASA replacing `degree` as the burial proxy inside
`potentials.V_R`)**: real, positive, on its own narrower objective —
SASA beats degree as a direct predictor of B-factor on **11/14 targets**
(both signs physically correct: buried/high-degree ⇒ low B, exposed/high-
SASA ⇒ high B), fixing 3 targets from FAIL to MARGINAL. **But rebuilding
`H_new` with SASA-based `V_R` and re-running [[TASK-0254]]'s own Shapley
attribution (fpocket in the stack, 20-target frozen set) shows CTQW's
added-last marginal does not move**: median +0.11% (was −0.06%), Wilcoxon
p=0.79 (was 0.50, so if anything *less* significant), improves on only
10/20 targets — a coin flip. CTQW's overall Shapley share barely moves
either (median +11.2% → +12.4%).

**This is the outcome [[TASK-0257]]'s own Constraint pre-registered as the
strongest possible negative**: a real, independently-motivated model
improvement (SASA genuinely is a better burial proxy, confirmed directly)
still leaves CTQW's downstream marginal at zero. Reported precisely, not
rounded up: the "unfair model" objection is **weakened but not fully
retired** — R1 did not achieve GNM-B-factor validity on the 4 FAIL
targets, so what CTQW does on a model that actually fits those specific
4 targets remains genuinely untested, not negatively tested. Ladder
stopped after R1+R2 per its own "stop as soon as a rung fails to improve
the objective" rule — R3-R6 (Cα+Cβ, all-heavy-atom GNM/ANM,
parameter-free ENM) are materially more expensive and nothing measured so
far motivates climbing to them.

**Scripts:** `scripts/task0257_r1_heavy_atom_contact_weighting.py`,
`scripts/task0257_r2_sasa_burial_vs_degree.py`,
`scripts/task0257_r2_shapley_rerun.py`. **Data:**
`results/tasks/0257_r1_heavy_atom_contact_weighting/r1_results.json`,
`results/tasks/0257_r2_sasa_burial_vs_degree/r2_results.json`,
`results/tasks/0257_r2_shapley_rerun/part_a_shapley_sasa.json`. **Full
detail:** `.ai/tasks/DONE/TASK-0257-beyond-calpha-enm-against-a-label-free-objective.md`.

## 20 rows, 13 structures: every frozen-set p-value was over-counted, self-caught before the collaborating thread found it ([[TASK-0261]], 2026-08-25)

**[OBSERVED]** [[TASK-0243]]'s frozen set has 20 scoreable rows but only 13
distinct apo structures — 7 apo entries each carry a second bound ligand,
a legitimate curation choice, but every apo-side quantity (geometry, CTQW,
ENM validity, hop, fpocket cavities) is computed from the same apo
coordinates for both rows of a pair. Every Wilcoxon/Mann-Whitney/Spearman
test across [[TASK-0249]]/[[TASK-0254]]/[[TASK-0257]]/[[TASK-0259]] treated
all 20 (or every subgroup) as independent.

**Premise checked before fixing it**: the filing's own "every apo-side
score is identical within a pair" is not quite right — checked directly
against the frozen config, 5/7 pairs use an identical apo chain selection
(bit-identical) but 2/7 (GAC_BPTES/GAC_CPD12, FBPASE_94D/FBPASE_95S) use a
different chain *subset* of the same deposited entry (correlated, not
identical — `gnm_r` differs, 0.697 vs 0.811). Doesn't change the clustering
unit, reported precisely rather than repeated unchecked.

**Method: exact cluster-level permutation**, not averaging (ruled out by
the task's own Scope as discarding real information) and not a mixed
model (13 clusters, only 7 non-trivial, is not enough to fit a random-
intercept variance component reliably). One-sample/paired tests use
cluster-level sign-flips (2^13=8,192 patterns, exact — generalises
Wilcoxon's own exact enumeration from rows to clusters); two-group and
correlation tests use cluster-block reassignment (exact via enumeration
where the outcome space is small enough — true for every two-group test
here; Monte Carlo, 40,000 draws, for the two correlation tests).

**Every re-run statistic** (n=20/subgroup p → n=13-cluster p): composite
vs CTQW 0.0137→0.0449 (survives, more narrowly); geometry Shapley/added-
last 0.0001/0.0002→0.0002/0.0002 (unchanged); fpocket Shapley/added-last
0.0032/0.0019→0.0188/0.0042 (survive, more narrowly); CTQW Shapley
0.0333→0.0420 (survives, more narrowly); **CTQW added-last (the headline
null) 0.5016→0.2170 (null either way — pseudo-replication cannot
manufacture a null)**; TASK-0257's R2 paired 0.4781→0.3354 (null either
way); ENM valid>invalid pre-registered direction 0.9674→0.9615
(unchanged); Spearman(ENM validity, CTQW added-last) 0.6171→0.6325
(unchanged); CTQW added-last on ENM-valid-only 0.7820→0.8379 (unchanged);
Spearman(apo crypticity, unexplained) 0.0001→0.0005 (unchanged, still the
strongest correlate). **No pre-registered conclusion flips. Corrections
cut against our own positive claims, not against CTQW** — exactly the
direction the filing's own first-pass measurement anticipated.

**One caught mistake before it shipped**: a first pass compared a
one-sided row-level Mann-Whitney (the pre-registered "valid>invalid"
direction) against a two-sided cluster permutation, manufacturing an
apparent flip that was really just mismatched alternatives. Fixed by
computing both sides identically at both levels. The pre-registered
direction stays solidly non-significant (0.9674→0.9615) — a genuine,
*exploratory, non-pre-registered* finding survives the fix instead: the
reverse-direction/two-sided version moves from p=0.080 (already
borderline at n=20) to p=0.042 (n=13 clusters) — borderline evidence that
CTQW's marginal is *larger*, not smaller, where its own ENM doesn't fit.
Reported as exploratory and post hoc, not a new positive — it further
undercuts, rather than rescues, [[TASK-0257]]'s "give it a valid model"
defence.

**Standing rule, written down once**: a second ligand on an apo structure
already in the set is a new target for label-side questions (pocket
identity, ranking) and not a new target for apo-side questions (ENM
validity, geometry, anything tested against zero or correlated across
targets unconditional on the label) — cluster by apo structure for the
latter, always.

**Independence checks elsewhere, both negative**: the 15 [[TASK-0250]]
register targets each use a distinct apo PDB — no clustering.
CARDIAC_MYOSIN/CARDIAC_MYOSIN_TABLE1, this task's own filing's named
"probable case," is **not** one (8QYP vs 5TBY, different entries) — the
suspicion is corrected, not confirmed. [[TASK-0216]]'s 7-target set
likewise has 7 distinct apo entries. The clustering is isolated to
[[TASK-0243]]'s frozen set.

**`documentation/CTQW_CONTRIBUTION_BRIEF.html` updated** in the same
task: cluster-robust p added to §01's decision-number row and §04's main
table, new §04 subsection with the full corrected table/method/standing
rule/exploratory finding, §05's R2 table gets a cluster-robust column,
§09's "Five places your reproduction will diverge" becomes six, §10 gets
a new self-disclosed-defect bullet — reported to the collaborating thread
before they could find it themselves, per this task's own Constraint.

**Script:** `scripts/task0261_cluster_robust_stats.py`. **Data:**
`results/tasks/0261_cluster_robust_stats/cluster_robust_results.json`.
**Full detail:**
`.ai/tasks/DONE/TASK-0261-pseudo-replication-20-rows-13-structures.md`.

## Was the physics right and the propagator wrong? Yes — `build_H_new`'s own potential terms beat the CTQW built from them, decisively (TASK-0263, 2026-08-25)

Bartosz's framing, 2026-08-25: *"We tried to introduce these to the Hamiltonians of
the CTQW some time ago. Maybe the route was reasonable, but simply not because of
CTQW at all."* A testable claim: `build_H_new`'s five potential terms (`V_B`
B-factor, `V_T` terminal suppression, `V_R` rigidity, `V_C` DCC coupling
centrality, `V_M` low-mode participation) encode real structural physics — but
until now they had only ever been seen mixed into a Hamiltonian a CTQW then
propagates over. A walk mixes a sharp local field into a smooth diffusion
profile; if the terms carry real signal the walk destroys, the encoding was
right and the propagator was the mistake.

**Method**: each term extracted as its own per-residue vector
(`np.diag(potentials.V_X(...))` — all five are already public, individually
callable, individually z-scored functions, the same route [[TASK-0257]]'s own
extraction script already used and validated). Scored with [[TASK-0254]]'s
protocol unchanged (5-fold stratified CV, 20 repeats, out-of-fold, OLS,
seed rows excluded), [[TASK-0243]]'s frozen 22-target set (n=20 usable).
Significance via [[TASK-0261]]'s cluster-robust exact sign-flip test (13
clusters, not row-level Wilcoxon — this set is pseudo-replicated).

**Headline — terms-block (all 5, concatenated) vs. CTQW alone, same targets,
same folds**: median AUC **0.751 vs. 0.575** (range 0.470–0.979 vs.
0.266–0.943). **Cluster-robust p = 0.019** (13 clusters) — the terms block
beats CTQW significantly, not just in the median.

**The sharpest version of the question — does the walk add anything to its own
ingredients?** Four-block Shapley attribution (geometry / fpocket / CTQW /
potential-terms), CTQW's own **added-last** marginal (its contribution once
geometry, fpocket, *and* the potential terms it was itself built from are
already in the model as direct predictors): **median −0.4%, range −4% to
+12%, cluster-robust p = 0.973.** Indistinguishable from zero. **No — CTQW
retains no residual contribution once its own ingredients are given a fair
chance to predict directly.**

| target | best term | best-term AUC | terms-block AUC | CTQW AUC | terms − CTQW | ctqw added-last |
|---|---|---|---|---|---|---|
| GAC_BPTES | V_B | 0.807 | 0.799 | 0.424 | +0.375 | −0.1% |
| GAC_CPD12 | V_C | 0.926 | 0.926 | 0.352 | +0.574 | +0.2% |
| DHPS_GC7 | V_R | 0.513 | 0.596 | 0.739 | −0.143 | −2.1% |
| PF_ATCASE | V_B | 0.812 | 0.880 | 0.432 | +0.448 | +1.4% |
| KSHV_PROTEASE_24Q | V_R | 0.636 | 0.692 | 0.729 | −0.037 | −3.9% |
| KSHV_PROTEASE_25G | V_R | 0.658 | 0.704 | 0.637 | +0.067 | −0.6% |
| SUMO_E1_FHJ | V_M | 0.715 | 0.703 | 0.766 | −0.063 | −1.4% |
| HCV_NS5B_VRX | V_C | 0.870 | 0.850 | 0.413 | +0.437 | −0.7% |
| HCV_NS5B_VR1 | V_C | 0.880 | 0.870 | 0.423 | +0.447 | −0.6% |
| HCV_NS5B_POO | V_B | 0.873 | 0.915 | 0.575 | +0.340 | −2.0% |
| HCV_NS5B_CMF | V_B | 0.873 | 0.915 | 0.575 | +0.340 | −2.0% |
| FBPASE_94D | V_C | 0.483 | 0.546 | 0.266 | +0.280 | +8.7% |
| FBPASE_95S | V_M | 0.539 | 0.470 | 0.338 | +0.132 | +12.2% |
| TRP_SYNTHASE_F6F | V_C | 0.629 | 0.608 | 0.517 | +0.091 | −0.5% |
| TRP_SYNTHASE_F19 | V_C | 0.666 | 0.654 | 0.466 | +0.188 | +0.1% |
| SMYD3_DIPERODON | V_B | 0.561 | 0.572 | 0.717 | −0.145 | +0.2% |
| PKR_MITAPIVAT | V_B | 0.851 | 0.881 | 0.641 | +0.240 | −0.1% |
| PKR_AG946 | V_B | 0.857 | 0.873 | 0.614 | +0.259 | −0.3% |
| MKK7_IBRUTINIB | V_C | 0.973 | 0.979 | 0.943 | +0.036 | −1.5% |
| NAMPT_NPA1R | V_C | 0.644 | 0.618 | 0.711 | −0.093 | +0.6% |

**Best single term is `V_C` (DCC coupling centrality) on 8/20 targets, `V_B`
(B-factor) on 7/20, `V_R` on 3/20, `V_M` on 2/20 — `V_T` (terminal suppression)
never wins, consistent with it being the crudest of the five.** Several single
terms alone (`V_C` on GAC_CPD12/HCV_NS5B_VRX/VR1/MKK7_IBRUTINIB; `V_B` on
GAC_BPTES/PF_ATCASE/HCV_NS5B_POO/CMF/PKR_MITAPIVAT/PKR_AG946) reach AUC
0.81–0.93 with **zero fitting** — stronger than CTQW manages on the same
targets even after fitting.

**One target's full 4-block model scores below chance out-of-fold**
(FBPASE_94D, full AUC 0.445) — its own "terms added-last" figure (−78.9% in
the raw per-target Shapley output, not tabulated above) reflects a model that
does not generalize on this target at all, not a genuine negative
contribution; read per [[TASK-0245]]'s own established convention for
share-outside-[0,1] cases, not taken at face value.

**Answered plainly, per this task's own Constraint** ("if the potential terms
beat the CTQW built from them, that is a positive result for the project's
physics and a negative for the propagator — report it as both, with the same
prominence"): **the physics encoding was right. The propagator was where the
signal was lost.** `build_H_new`'s potential terms, scored directly, beat the
CTQW computed from the Hamiltonian they build — decisively on the headline
comparison (p=0.019) and with the walk's own added-last contribution
statistically null (p=0.973) once those terms are given a fair chance as
direct predictors. This does not mean CTQW is worthless in isolation (it
still beats chance on most targets) — it means whatever the potential terms
know, the walk does not add to it, and the terms alone already know most of
what the whole construction knows.

**Flagged, not edited here** (this task's own parallelisation/scope note):
`documentation/CTQW_CONTRIBUTION_BRIEF.html` §04 should be updated with this
finding — a separate task's job, not touched in this one.

**Script:** `scripts/task0263_potential_terms_direct_predictors.py`. **Data:**
`results/tasks/0263_potential_terms_direct_predictors/`. **Full detail:**
`.ai/tasks/DONE/TASK-0263-potential-terms-as-direct-predictors.md`.

## Is a pocket allosteric partly because of *what* binds it? The label can't say — and label-side independence is worse than TASK-0261 found ([[TASK-0265]], 2026-08-25)

**[OBSERVED]** Mirrors H9 ([[TASK-0229.001]]) from the positive-class side:
maybe the same pocket is allosteric with one ligand and inert with another,
so our positive labels aren't clean either. Measured directly via pocket-
label Jaccard overlap on identical apo coordinates, all 7 same-apo-structure
ligand pairs in [[TASK-0243]]'s frozen set (the Reviewer's own first pass
found 5; 2 more — GAC_BPTES/CPD12, FBPASE_94D/95S — were silently excluded
by a transient script's chain-selection grouping, found and fixed here).

**Real artifact caught before trusting the numbers**: those 2 pairs initially
scored Jaccard=0.000 — turned out to be a homo-oligomer symmetric-copy
artifact (same binding site, same residue numbers, deposited on a different
chain letter across the two structures — e.g. GAC_BPTES's pocket is chain D
317-394, GAC_CPD12's is chain B at the *same numbers*, 321-325/394). Corrected
via a resnum-only Jaccard for these 2 cases: 0.750 and 0.400 respectively,
not 0.000.

**Corrected result, all 7 pairs: median 0.769, min 0.400, 6/7 pairs ≥0.75.**
Higher (i.e. the finding is *stronger*) than the first pass's own median
0.833 on 5 pairs suggested — the two previously-missed pairs don't weaken the
picture, they confirm it. **Two ligands on the same apo structure produce
near-identical pocket labels.** The label is drug-contact geometry; it cannot
express "myristoyl works, myristic acid doesn't" even if that were true —
a construct-validity finding distinct from anything else in the register.

**[[TASK-0261]]'s standing rule revised**: label-side independence now
requires pocket-label Jaccard **< 0.5** between a pair's two labels (only
1/7 pairs, FBPASE at 0.400, clears that bar). Applied to the frozen set:
6 pairs collapse to one label-side observation each (12 rows → 6), FBPASE
stays as 2, the 6 singletons are unaffected — **14 genuinely independent
label-side observations, not 20.** [[TASK-0261]]'s own apo-side clause
(13 independent apo-side observations) is unchanged, unchallenged.

**BCR-ABL1 mechanism, live-verified rather than repeated as fact** (the
originating question, from Bartosz): does covalent tethering of the native
myristoyl-glycine matter for the local "latch" (αI-helix bend enabling SH2
docking), or does simple pocket occupancy suffice? **Established, convergent
across independent structural/NMR groups**: non-covalent, non-tethered
occupancy alone is sufficient — GNF-2 (Zhang et al. 2010, *Nature*
463:501-506) and asciminib (Wylie et al. 2017, already verified
[[TASK-0236]]) both stabilise the same bent conformation Nagar et al. 2006
(*Mol Cell* 21:787-798) defined structurally; Grzesiek et al. 2022 states it
directly via NMR. Tethering's real role is effective concentration/
localisation, not the local bend — a genuine distinction, but not the one
the original framing implied (that the pocket "acts differently"). Honest
gap: no source co-crystallises free myristic acid itself, untethered, to
close this completely — flagged, not filled. BCR_ABL1's own config confirmed
to derive its pocket from AY7 (asciminib) contacts — genuinely the myristoyl
site, not a different one.

**Extended to the rest of the register, both negative**: the 15 register
targets and [[TASK-0216]]'s 7-target set each have zero same-apo pairs.
CARDIAC_MYOSIN/CARDIAC_MYOSIN_TABLE1, flagged a "probable case," is
confirmed not one (8QYP vs 5TBY, different entries).

**`documentation/CTQW_CONTRIBUTION_BRIEF.html`** §10 gains a new
self-disclosed-defect bullet (this task's own brief edit for the batch):
label-side independence revised from 20 to 14, with the bar and its
justification.

**Script:** `scripts/task0265_pocket_label_overlap.py`. **Data:**
`results/tasks/0265_pocket_label_overlap/pocket_label_overlap.json`. **Full
detail:** `.ai/tasks/DONE/TASK-0265-is-allostery-a-property-of-the-ligand-too.md`.

## Cryptic-opening instance hardness, checked before any QUBO — still closed on complexity grounds ([[TASK-0264]], 2026-08-25)

[[TASK-0204]]'s own complexity closure (treewidth 2-5 at m=12, exact solve
in milliseconds) only measured **fixed-backbone** rotamer packing. It left
a real gap: cryptic-pocket *opening* couples backbone displacement to
rotamer choice, and nobody had measured whether that coupled instance is
genuinely harder. This task closes that gap.

**Real instance, real coupling, definition written before measuring**: one
rotamer-choice variable per window residue (domain n=15, TASK-0204's own
value, unchanged) plus ONE shared backbone-choice variable for the whole
window (domain K=11 — apo static plus apo stepped ±6 Å along its own first
5 ANM modes, [[TASK-0228]]'s own already-validated `adaptive_anm_modes`
convention, turned into real full-atom structures via [[TASK-0235]]'s own
`local_rigid_reconstruction`, both reused unchanged). The backbone variable
is a hub node connected to every rotamer variable; the interaction graph is
the CB-CB proximity graph unioned across all K conformations. Measured on
[[TASK-0243]]'s frozen set, prioritising the 11 genuinely-cryptic targets
([[TASK-0254]] Part B, `already_open == False`) plus TASK-0204's own
original 4 mandatory targets.

**Sanity-checked against TASK-0204's own published number first**: this
pipeline's own single-static-backbone treewidth at KRAS_G12C, m=12,
cutoff=8 Å reproduces TASK-0204's own published value exactly (tw=3).
Mixed-domain bucket elimination (a real, necessary generalisation of
TASK-0204's own uniform-domain solver, since the backbone hub's domain,
K=11, differs from the rotamer nodes', n=15) re-validated against brute
force on enumerable synthetic instances before trusting it on real data.

| m (window) | median union tw, 11 cryptic (cutoff 8 Å) | median static (fixed-backbone) tw | max union tw |
|---|---|---|---|
| 12 (this line's own stated typical window) | **5** | 5 | 7 |
| 20 | **8** | 6 | 9 |

**Verdict: formulation exercise only — the same conclusion TASK-0204
already reached, now checked for the coupled case specifically.** Never
crosses 9 at the primary 8 Å cutoff on any tested target/window size; the
pre-registered ≥12 "real quantum target" bar is not reached at realistic
instance size. Coupling is real and measured (union treewidth exceeds
static on every target at every window size, 0-2 higher at m=12, up to
+2-3 at m=20) — not nothing, but a shift in the constant, not a change in
growth regime. **Caveat, reported not hidden**: at looser cutoffs (10-12 Å)
and the largest window tested (m=20, past this line's own stated typical
range), treewidth climbs further, one condition (MKK7_IBRUTINIB, m=20,
cutoff=12 Å) reaching tw=15, over the ≥12 bar.

**Exact-solve wall-clock**: real bucket elimination run wherever projected
cost stayed under TASK-0204's own `MAX_FACTOR_ENTRIES=1e8` guard (reused
verbatim). Median max-feasible window before the guard fires: m=8 on the
11 cryptic targets (vs. m=7 mandatory) — the practical boundary moves down
roughly half relative to fixed-backbone packing (TASK-0204 solved m=12 in
under a second), driven by the added K=11 domain size on the hub node
inflating projected cost faster than treewidth alone would, not by
treewidth exploding. All feasible timings stayed in the tens-to-hundreds
of milliseconds.

**Recommendation: do not build the coupled backbone+rotamer QUBO.** No
quantum formulation is built for this objective either, matching
TASK-0204's own criterion-#1 closure and Phase A's binding precedent.

**Script:** `scripts/task0264_cryptic_opening_hardness.py`. **Data:**
`results/tasks/0264_cryptic_opening_hardness/hardness.json`. **Full
detail:** `.ai/tasks/DONE/TASK-0264-cryptic-opening-instance-hardness-before-qubo.md`;
`src/allostery/PHASE_B_ROTAMER_QUBO.md`'s own new closure section.

## Local energetic frustration — the direct, pre-registered test of HYP-P13, and it fails ([[TASK-0268]], 2026-08-25)

**Pre-registered prediction, written before a single number was computed**:
if HYP-P13 (allostery as stabilisation of an otherwise-disfavoured
conformation, not signal propagation) is right, native energetic
frustration should be elevated at true pocket residues, **more so on
genuinely-cryptic targets than already-open ones**.

**Citations verified live**: Jenik et al. 2012, *Nucleic Acids Research*
40:W348-W351, doi:10.1093/nar/gks447 (Frustratometer formalism); Miyazawa &
Jernigan 1996, *J Mol Biol* 256:623-644, doi:10.1006/jmbi.1996.0114
(pairwise contact potential). **Installability checked directly**: the real
PyPI `frustratometer` package resolves but fails to build — its own
`numba`→`llvmlite` dependency needs a system LLVM toolchain absent here
(confirmed directly, not assumed); installing LLVM system-wide judged out
of scope. A real, honestly-scoped port built instead
(`allostery/frustration.py`) — single-residue mutational frustration, the
real 20×20 Miyazawa-Jernigan matrix (AAindex MIYS960101, not hand-recalled,
sanity-checked before use), matching this project's own established
precedent ([[TASK-0229.006]]'s own COREX/EAM build when the full tool
wasn't practical to import either).

Added as a 5th attribution block (geometry/fpocket/SASA/CTQW/frustration)
on [[TASK-0243]]'s frozen set, [[TASK-0261]]'s exact cluster-permutation
significance, [[TASK-0260]]'s own crypticity stratification — n=20/22 (the
2 known empty-seed HIV-integrase entries, [[TASK-0253]], correctly
skipped).

| block | Shapley share (median) | added-last (median) |
|---|---|---|
| geometry | +39.1% | +13.2% |
| fpocket | +7.0% | +3.3% |
| SASA | −0.4% | −0.4% |
| CTQW | +5.4% | +0.0% |
| **frustration** | **+6.5%** | **+0.1%** |

**Verdict: HYP-P13's own frustration prediction fails — a clean negative,
reported with the same prominence a positive would get.**

| statistic | cryptic (n=10) | open (n=8) | cluster-perm p (cryptic>open) |
|---|---|---|---|
| frustration Shapley share | +6.96% | +0.27% | 0.355 |
| **frustration added-last** | **−0.09%** | **+0.05%** | **0.452** |
| frac. residues highly frustrated (z>0.78) | 36.0% | 35.2% | 0.537 |

Direction predicted (cryptic > open) **does not hold** on the statistic
that matters most — added-last, the unique non-redundant contribution —
cryptic targets show numerically *lower* frustration than open ones, the
opposite of the prediction, though the gap is small and not significant
either way. Frustration's own overall added-last value is indistinguishable
from zero (cluster-p=0.727, 13 clusters) — its real, positive Shapley share
(+6.5%, p=0.128, also not significant) reflects redundant information
already captured by geometry/fpocket/SASA/CTQW, not new signal.

**Read plainly**: this is HYP-P13's own most direct empirical test to date.
It does not disprove the broader population-shift picture (a static-
structure index cannot rule out a genuine ensemble/kinetic effect the way
[[TASK-0229.006]]'s own EAM measurement more directly probes), but the
specific, falsifiable, sharp prediction this task set out to test is not
supported by real data. `.claude/hypotheses/physics.md`'s own HYP-P13
section updated with the same prominence.

**Script:** `scripts/task0268_local_frustration_hyp_p13.py`. **Data:**
`results/tasks/0268_local_frustration_hyp_p13/`. **Full detail:**
`.ai/tasks/DONE/TASK-0268-local-frustration-and-hyp-p13.md`.

## Organiser-sanctioned structure fixes: KRAS_G12C's genotype corrected, and the register's own only clean floor-clear does not survive it ([[TASK-0270]], 2026-08-26)

**[OBSERVED]** The organisers privately confirmed 4OBE is the wrong protein
for KRAS_G12C and suggested `8S8C`; separately granted BCR-ABL1 apo-
substitution latitude with a required rationale
(`documentation/2026-08-26-organiser-clarifications.md`). Neither
suggestion was taken at face value.

**`8S8C`, live-verified, is HOLO** — X-ray 1.90 Å, MK-1084 (a covalent
Switch-II inhibitor) + GDP + MG bound (Ma et al. 2024, *J Med Chem*
67:11024-11052). Genuinely G12C (residue 12 = Cys, confirmed directly),
but not usable as an apo replacement; no companion apo structure exists in
that paper's own deposition. **A real bug found in [[TASK-0155]]'s own
"10 verified true-G12C" candidate pool before trusting it for a
replacement**: 8 of the 10 are actually drug-bound, not apo (checked by
enumerating every non-polymer entity directly, not the misleading RCSB
summary field that only lists metal-coordinated components). Only
**4LDJ** and **8TXJ** are genuinely apo; [[TASK-0155]]'s own file
corrected in place. `4LDJ` (1.15 Å, the better-resolution of the two)
adopted as the new `apo_pdb`, on structural grounds.

**Decisive: KRAS_G12C's flagship result does not survive the genotype
fix.** Old (4OBE, wild-type) vs. new (4LDJ, genuine G12C), same holo
(6OIM), same pipeline: AUC 0.557→0.514; **diagnosis
`NO_FAILURE_DETECTED`→`NO_SIGNAL_IN_APO`** — the register's own only clean
mandatory-target floor-clear does not survive; ENM validity r=0.646
(PASS)→0.496 (MARGINAL). Pocket-to-active-site distance essentially
unchanged (1.32→1.31 Å heavy-atom, still contact-adjacent). Propagated to
the live app and every doc carrying the old flag in the same commit:
`config/targets.yaml`, `backend/systems.py`, `SOFTWARE.md`,
`COMPETENCE_MAP.md` (new dated caveat), `ARCHITECTURE.md` (change-log
entry closing the 2026-08-03 one). Live-app smoke-tested via
`backend.pipeline.build_view` before treating the swap as safe to ship.

**BCR-ABL1: enumerated, scored, declined.** No genuinely apo (fully
ligand-free) kinase-domain-only ABL1 structure exists in RCSB — the
closest family (2G1T/2G2H/2G2I, ~287 residues) all carry an ATP-site
occupant. Scored the best of these (2G1T, 1.8 Å) against 1OPL: ENM
validity improves (0.493 MARGINAL→0.660 PASS) but **AUC collapses to
below chance** (0.541→0.350) — real, measured evidence for exactly the
scope-truncation risk the filing named ("may remove the mechanism from
the model entirely," the [[TASK-0251]] failure mode in a new place).
Coordinated with [[TASK-0265]]'s own live-verified finding (covalent
tethering isn't required for the local mechanism, but the SH3-SH2
regulatory domains being physically present is). **Decision: keep 1OPL**
— on structural grounds (the scored evidence above), not because 1OPL's
own result is flattering (it isn't — `NO_SIGNAL_IN_APO` either way).
Submission-ready rationale written into the task's own Done section.

**Housekeeping**: [[TASK-0222]] marked resolved (8QYP→8QYR confirmed
primary). [[TASK-0221]]'s own §3 update and the organiser-channel
follow-up (re-asking open items (e)/(f)) found already complete by a
concurrent thread — not duplicated.

**Scripts:** `scripts/task0270_kras_g12c_genotype_fix.py`. **Data:**
`results/tasks/0270_kras_g12c_genotype_fix/kras_genotype_fix.json`. **Full
detail:**
`.ai/tasks/DONE/TASK-0270-organiser-sanctioned-structure-substitutions.md`.

## PocketMiner, unblocked — does the one purpose-built cryptic-*opening* predictor close the residual? Not significantly (TASK-0269, 2026-08-26)

[[TASK-0260]] identified PocketMiner (Meller et al. 2023, Nat Commun 14:2135,
doi:10.1038/s41467-023-36699-3) as the one predictor in its comparison set
actually trained to predict pocket *opening* — but it never ran: Python
3.7–3.9 + TensorFlow≤2.9 could not be satisfied by this repo's own toolchain
(Python 3.13 / TensorFlow 2.16), and a native `pyenv install 3.9.18` failed
to compile `_ssl` twice. This task unblocks it via Docker
(`tools/pocketminer/`, full recipe in that directory's own README.md) and
runs the actual comparison.

**Environment, real and working now**: `python:3.9-slim-bullseye` base,
`--platform linux/amd64` (this host is Apple Silicon; TensorFlow 2.6–2.9 has
no `linux/arm64` PyPI wheels for this vintage, confirmed directly, not
assumed), PocketMiner pinned to `Mickdub/gvp`'s `pocket_pred` branch at
commit `187062d` (a SHA, not a branch name). Two real build-environment bugs
found and fixed along the way, not smoothed over: `mdtraj==1.9.7` ships no
Linux wheel for any cpython version and its Cython source fails to compile
under Cython≥3 (fixed: pin `cython<3`, `--no-build-isolation`); TensorFlow
2.6.2's generated protobuf code raises `TypeError: Descriptors cannot be
created directly` under a too-new protobuf (fixed: pin `protobuf==3.18.1`,
upstream's own lock file value). A genuine sandbox-specific finding, not a
PocketMiner issue: `docker build --platform linux/amd64` (cross-arch image
resolution) hung indefinitely on this session's first several attempts
while native-arch pulls completed in seconds — resolved by waiting out a
slow first connection through this environment's own registry proxy
(`http.docker.internal:3128`), not a permanent block.

**Constraint-3 status, unchanged since this task's own filing**: the
organiser question this depends on (`documentation/2026-08-26-organiser-
clarifications.md`'s item (f), re-sent standalone as Q7 the same day) is
**still open** as of this run. Proceeding under this register's own
provisional reading (MD used only for the external authors' *training*
labels; our own inference supplies zero trajectories) — this result is not
organiser-endorsed and must carry that caveat until an answer arrives.

**Run**: 20/22 of [[TASK-0243]]'s frozen set (same 2 excluded as every other
task on this set — HIV_INTEGRASE_MUT871/916's own empty active-site seed,
[[TASK-0249]]'s finding). **2 further targets failed inside PocketMiner
itself** (HCV_NS5B_CMF, HCV_NS5B_POO) — both apo structures contain `CME`
(S-methylcysteine, a modified residue), and PocketMiner's own hardcoded
20-canonical-amino-acid lookup table has no entry for it. A real upstream
limitation, not a pipeline bug — **n=18 usable**.

**Headline — PocketMiner's own added-last contribution** (four-block
Shapley, geometry/fpocket/CTQW/PocketMiner, the marginal value of adding
PocketMiner once the other three are already in the model — this task's own
decision statistic): **median +0.4%, range −20% to +27%, cluster-robust
p = 0.277** ([[TASK-0261]]'s method, 12 clusters over 18 rows). **Not
significant.** Four-block unexplained share: median 27% (2–62%) — barely
moved from [[TASK-0260]]'s own 27–29% baseline. PocketMiner's own Shapley
share (averaged over orderings, not the added-last decision statistic):
median +11%, range −29% to +40% — real per-target signal exists, but does
not survive as a genuine marginal contribution once geometry/fpocket/CTQW
are already accounted for.

**Crypticity-stratified, the pre-registered prediction from [[TASK-0260]]'s
own filing**: a genuine cryptic-opening specialist's gain should concentrate
on the cryptic targets, not the already-open ones — P2Rank failed this
test (gain concentrated on already-open, the wrong direction). PocketMiner's
own split: already-open (n=9) median added-last **+0.0%**, cryptic-testing
(n=9) median added-last **+7.0%** — the *right* direction, unlike P2Rank,
though **not formally significance-tested**: at least one shared-apo cluster
has members on both sides of the 80% crypticity bar (crypticity is a
property of the apo/ligand-specific-holo *pair*, not the apo structure
alone, so it is not guaranteed cluster-consistent the way ENM validity is) —
[[TASK-0261]]'s own cluster-permutation test correctly refuses to run on a
split that violates its cluster-integrity assumption, reported as a
descriptive median comparison instead of forced through.

**Answered per this task's own Constraint** ("both outcomes are decisive and
must be reported with equal prominence"): **PocketMiner does not close the
residual.** Its own added-last contribution is statistically indistinguishable
from zero (p=0.277) and the four-block unexplained share is essentially
unchanged from the pre-PocketMiner baseline. The one purpose-built
cryptic-*opening* predictor tested does not solve this project's residual —
**genuinely unmodelled signal remains in the cryptic regime**, the strongest
available motivation for Phase 2 this project has, per this task's own
framing. The directional nuance (PocketMiner's gain leans toward cryptic
targets, P2Rank's leaned the wrong way) is real but should not be
oversold — it is not a significant result, only a more encouraging shape
than the one confirmed non-starter.

**One target flagged**: FBPASE_95S shows the single largest negative
PocketMiner contribution (Shapley −29%, added-last −20%) — not investigated
further here (a per-target model-fit anomaly, real remaining scope, not
smoothed into the summary).

**Not done, per this task's own scope/parallelisation note**: `documentation/
CTQW_CONTRIBUTION_BRIEF.html` §08 needs this finding — [[TASK-0265]] owns
the brief for this batch, not touched here.

**Script:** `scripts/task0269_pocketminer_residual.py`. **Environment:**
`tools/pocketminer/` (Dockerfile, `predict.py`, README.md). **Data:**
`results/tasks/0269_pocketminer_residual/`. **Full detail:**
`.ai/tasks/DONE/TASK-0269-pocketminer-environment-and-run.md`.

## Finishing the KRAS swap: propagating TASK-0270's fix, plus two flagged-but-unmade brief updates ([[TASK-0272]], 2026-08-26)

Document-propagation task, no new computation — [[TASK-0270]]'s own
already-verified KRAS_G12C genotype-fix numbers (`4OBE`→`4LDJ`,
organiser-sanctioned) were still cited as current in the submission draft
and the CTQW brief; two independently-flagged results
([[TASK-0263]], [[TASK-0269]]) were still missing from the brief.

**`documentation/PHASE1_SUBMISSION_DRAFT.md`**: new dated banner entry
added (matching this document's own established convention of appending a
dated correction rather than rewriting old changelog narration). Finding
5 corrected in place: AUC 0.557-0.590 → **0.514** (floor 0.530, now below
floor), diagnosis `NO_SIGNAL_IN_APO`. **Finding 6 checked, not assumed
stale**: its own "AUC 0.557" citation is a *holo*-structure (6OIM)
measurement per [[TASK-0229.005]]'s own text, unaffected by the apo
swap — correcting the task's own filing, which had assumed it needed the
same fix as Finding 5. A second stale table found by this task's own
grep-check (not in the original filing): §2.5's rank-of-known-site /
enrichment-at-k table carries 4OBE-era N/AUC — flagged inline, not
recomputed (those statistics were never re-run on `4LDJ`).

**`documentation/CTQW_CONTRIBUTION_BRIEF.html`**: §05's ENM-validity
stat-row and R1 table's own *baseline* row recounted (6/5/4→5/6/4;
6/4/4→5/5/4) for KRAS_G12C's PASS→MARGINAL move. **The R1 experimental
row itself was explicitly left unaltered** — that specific
heavy-atom-weighting measurement was never re-run on `4LDJ`; disclosed
inline rather than fabricated. §04 gained [[TASK-0263]]'s own
terms-block-vs-CTQW result (0.751 vs 0.575, cluster-robust p=0.019;
CTQW's own added-last once terms are in the model, p=0.973) — flagged by
that task itself as "the strongest single result in the brief's argument"
and missing until now. §08's PocketMiner paragraph updated from "could
not be run" to [[TASK-0269]]'s own real outcome (added-last median +0.4%,
cluster-p=0.277, not significant; crypticity-stratified the right
direction, +7.0% cryptic vs +0.0% open, not formally tested).

**Historical entries** ([[TASK-0245]], [[TASK-0246]], [[TASK-0247]], and
`task0258_allosteric_distance_taxonomy.py`, which has no task file to
annotate — already independently confirmed missing by another thread):
dated pointers added, kept as historical artifacts per this document's own
no-silent-overwrite convention. **Checked, not assumed**: in both
[[TASK-0245]] and [[TASK-0247]], KRAS_G12C's own row is not the
median-determining value in any cited table (PTP1B occupies that rank
throughout) — the headline conclusions do not turn directly on the KRAS
row, though whether the *exact* median would move under a full recompute
was not tested, stated as a real limit on this check's own confidence.

**Also found and fixed, beyond the task's own named scope**:
`documentation/WORKFLOW.md`'s own "what this pipeline cannot do" section
and KRAS_G12C walkthrough both stated `4OBE`/N=169 as current — corrected
to `4LDJ`/N=170 in three places, with the real re-run numbers. Its own
stale "10 structures, median AUC 0.482" claim was dropped rather than
repeated, since [[TASK-0270]] separately found 8 of those 10 were
actually drug-bound — restating it would have perpetuated a second,
independent error. `documentation/2026-08-26-organiser-clarifications.md`
(the decision record [[TASK-0270]] itself was filed from) gained a short
dated update note, kept as the historical record it is.

**Grep-check** (this task's own explicit Acceptance requirement):
`grep -rn "4OBE"` / `"0.646"` across every live document, re-run after
every edit. Every remaining hit is either the organisers' own Challenge
Statement (not ours to edit), a generic API-example PDB code, or
explicitly dated/historical/disclosed text — no live document presents a
`4OBE` figure as a current KRAS_G12C result.

**Not done**: §2.5's rank-of-known-site/enrichment-at-k table and the
CTQW brief's own R1 heavy-atom-weighting experiment both need a real
re-run on `4LDJ` before their own KRAS_G12C numbers can be stated as
current — new measurements, out of this doc-propagation task's own scope,
disclosed rather than silently absorbed.

**Full detail:**
`.ai/tasks/DONE/TASK-0272-kras-swap-blast-radius-and-pending-doc-updates.md`.

## Two decades-old classical feature families, never tested until now — neither closes the residual ([[TASK-0274]], 2026-08-26)

Every attribution block this register had ever tested was geometric or
dynamical (geometry / fpocket / ctqw / sasa [[TASK-0266]] / p2rank
[[TASK-0260]] / potential terms [[TASK-0263]] / pocketminer [[TASK-0269]]).
Checked directly: no sequence-conservation feature and no residue chemistry
existed anywhere in `src/allostery/`. This task builds both, real, and adds
them to [[TASK-0254]]'s own Shapley attribution, making it a 5-block model
(geometry/fpocket/ctqw/conservation/chemistry).

**Conservation, real, not a placeholder**: for each of the 20 frozen-set
targets, `backend.active_site`'s own UniProt-offset machinery (reused
verbatim — `get_uniprot`/`_residues_by_num`/`_uniprot_features`/
`_find_offset`) places a UniProt accession and offset; InterPro's own API
resolves the largest Pfam domain match; the Pfam **seed** alignment
(curated, not the HMM-derived full alignment) is fetched via InterPro's
alignment endpoint and parsed with `Bio.AlignIO` — no MSA binary is
installed in this environment (checked: no clustalo/mafft/muscle/hmmalign),
so a per-column Shannon-entropy conservation score is computed directly
from the seed, then transferred onto the query's own residues via a
pairwise alignment (BLOSUM62, `Bio.Align.PairwiseAligner`) against the
seed's own best-matching row (nearest-homolog transfer, not a full
profile/HMM alignment — cheap and standard, its own depth reported per
target, not hidden). Citation verified live: Mistry et al. 2021, Nucleic
Acids Research, DOI 10.1093/nar/gkaa913. **20/20 targets got a real Pfam
seed mapping** — n_seed sequences median 32 (range 5-245), best-homolog
identity to the query domain median 97% (range 44-100%; PF_ATCASE, KSHV
protease, MKK7, SMYD3 sit at 44-53%, genuinely shallow homology, flagged
per target in `conservation_depth.json`, not smoothed into the summary).
Multi-chain targets: conservation is chain[0]-scoped only (the same
limitation `detect_active_site` itself already has) — other chains' rows
get NaN, imputed via nanmedian like every other NaN block value in this
register, and true coverage (`cov=n_mapped/n_total`) is reported per target.

**Chemistry, deliberately simple**: hydrophobicity (Kyte & Doolittle 1982,
DOI 10.1016/0022-2836(82)90515-0), charge at physiological pH (D/E=-1,
K/R=+1, H=0), aromaticity (F/W/Y), side-chain volume (Zamyatnin 1972, DOI
10.1016/0079-6107(72)90005-3) — four z-scored columns from residue
identity alone, no structure-derived component.

**Headline — the decision statistic this task's own Scope specified**
(each new block added on top of the geometry+fpocket+CTQW baseline
specifically, not on top of the other new block): **conservation median
-0.08%, chemistry median -0.35%.** Both slightly negative — no measurable
gain, and cluster-robust ([[TASK-0261]]'s exact permutation, 13 clusters):
conservation p=0.6946, chemistry p=0.6492. Full 5-block added-last (on top
of everything else, including each other) confirms it: conservation
median -0.05% (p=0.8423), chemistry median -0.27% (p=0.8318). **Neither is
distinguishable from zero.** The 5-block unexplained share (median 30.7%)
is not lower than the pre-existing 3-block baseline (28.6%) — it is
marginally *higher*, consistent with adding two uninformative dimensions to
a 20-row 5-fold CV rather than any real signal.

**Crypticity-stratified** (this task's own pre-registered prediction:
conservation should help on functional sites regardless of openness — if
its gain concentrates on already-open targets the way fpocket/P2Rank's
does, it is tracking cavity presence, not function): conservation's own
cryptic-vs-open split is -0.66% vs -0.07% (p=0.572) — not significant, and
if anything in the wrong direction. The prediction is not confirmed, but
there is nothing to confirm it *with*: conservation carries no signal here
in either regime.

**Answered per this task's own Constraint** ("if conservation closes a
large share of the residual, say so plainly — that is a more useful
finding than another negative"): it does not close any of it. Two ordinary,
decades-old feature families, real implementations (not placeholders),
tested with the same cluster-robust rigor as every other block in this
register — both come back statistically indistinguishable from noise. This
closes two of the three concretely-named remaining candidate categories in
this task's own filing ([[TASK-0273]] covers the third, label noise);
what is left is "ligand-side properties" (explicitly out of scope — a
different experimental design, per-pocket not per-residue) and
"irreducible." One per-target outlier noted, not chased further here:
DHPS_GC7 shows a real +32.7% conservation Shapley share, the only target
where conservation does anything — a single point, not a pattern (real
remaining scope, if anyone wants it).

`documentation/CTQW_CONTRIBUTION_BRIEF.html` §08 **not flagged** — this
task's own Acceptance only requires flagging it if the residual drops
materially; it did not (28.6% → 30.7%, in the wrong direction).

**Script:** `scripts/task0274_conservation_chemistry_residual.py`. **Data:**
`results/tasks/0274_conservation_chemistry_residual/`. **Full detail:**
`.ai/tasks/DONE/TASK-0274-what-are-the-missing-contribution-categories.md`.

## The pocket label's own noise floor: real crystal replicates measured, and broadening the label makes AUC *worse*, not better ([[TASK-0273]], 2026-08-26)

Every AUC this register has published treats the pocket label as exact
("residues within 4.5 A of the drug in one crystal structure"). This task
measures the noise floor beneath that label directly, using real,
independently-deposited RCSB holo structures — no simulation. Filed same-day
as [[TASK-0274]] as the third of three concretely-named candidate
explanations for the residual; that task closed conservation/chemistry,
this one closes label noise.

**Live re-verification caught real contamination, same pattern [[TASK-0270]]
found in [[TASK-0155]]'s own pool**: searching RCSB for every OTHER
deposition of each of KRAS G12C's 10 already-verified drugs found 23
candidate replicates — after checking each one live (X-ray method, and for
KRAS, the deposited sequence at the anchor-relative position-12 offset),
**13 of 23 were off-genotype or off-method**: BI-2865's other 7 hits are
wild-type or G12D/G12V/G13D KRAS, not G12C; sotorasib's other 5 hits are
cryo-EM, and 4 of those 5 are antibody/MHC-peptide complexes, not the intact
protein-drug pocket at all. **Two drugs (BI-2865, sotorasib) have ZERO
genuine same-drug X-ray G12C replicates anywhere in the PDB** — a real,
useful negative finding on its own. Only GNE-1952 (ligand MKZ, [[TASK-0270]]'s
own "covalently alkylated" 7RP3) has any: 6T5V and 7RP4, both genuine. For
GAC, one of 6 BPTES replicate hits was mouse glutaminase, not human —
excluded. Two real bugs were also caught and fixed mid-task: an
organism-string exact-match check wrongly excluded 10/12 genuine
*S. typhimurium* TRP_SYNTHASE replicates (RCSB's own free-text field returns
4 different capitalizations/strain-suffix variants for the identical
organism — fixed to a case-insensitive keyword match); and prody's legacy
PDB parser cannot read 2 KRAS entries at all (9UOH, 8S8C) because their
5-character extended chemical-component IDs overflow the fixed-width HETATM
columns — fixed with an mmCIF fallback.

**Contact extraction** is self-contained per entry (heavy-atom, 4.5 A,
matching this project's own established convention) — no apo/holo overlay,
no cross-entry alignment. **Jaccard reported both ways** ([[TASK-0265]]'s
own fix, reused): (chain,resnum)-exact and resnum-only, since a
homo-oligomer can deposit the identical physical site under a differently-
lettered symmetric chain across independent depositions.

| protein | same-drug n (pairs) | same-drug Jaccard (resnum-only) | diff-drug Jaccard (resnum-only) |
|---|---|---|---|
| KRAS_G12C (MKZ triplet only) | 3 | median 0.875 [0.840, 0.885] | median 0.591 [0.000, 0.917], n=63 |
| GAC_BPTES (04A, 6 depositions) | 15 | median 0.818 [0.636, 1.000] | median 0.739 [0.636, 1.000], n=6 |
| TRP_SYNTHASE_F6F (13 depositions) | 79 | median 0.500 [0.000, 1.000] | median 0.420 [0.000, 0.857], n=26 |

(chain,resnum)-exact Jaccard is reported in the data but not headlined here:
for KRAS it is artificially deflated for 2 of the 3 same-drug pairs because
7RP4 alone carries two independent ligand copies in its asymmetric unit
(48 contact residues vs. ~21-24 for the single-copy depositions it's
compared against) — a real ASU-copy-count artifact, not evidence of pocket
disagreement; resnum-only correctly absorbs it. For TRP_SYNTHASE, 4 of the
79 same-drug pairs hit Jaccard = 0.000 *exactly* — every one of them
involves 7ME8, whose own deposition captured F6F at the beta site only,
compared against depositions that captured it at the alpha site only. That
is a real binary catalytic-state difference (which active site the crystal
happened to trap the inhibitor in), not stochastic crystallographic noise —
folded into "same-drug reproducibility" here because it is real experimental
variance on the identical ligand, but it means this range is an upper bound
on pure crystallographic noise, not a purified estimate of it.

**Headline, in the same direction for all three proteins**: same-drug
depositions of the identical ligand agree with each other more than
different-drug depositions do (0.875 vs 0.591 for KRAS; 0.818 vs 0.739 for
GAC; 0.500 vs 0.420 for TRP_SYNTHASE) — ligand identity carries real signal,
confirming [[TASK-0265]]'s own qualitative claim. **But the same-drug floor
itself is nowhere near 1.0** — even the *identical* drug on the *identical*
protein, independently solved, reproduces the contact-residue set at only
42-88% Jaccard depending on target. The label is not exact, at a magnitude
large enough to matter.

**Consensus/union labels** (K stated before computing: majority, K =
ceil(N/2)) were built for all three ensembles. **Re-scored for KRAS_G12C
and TRP_SYNTHASE_F6F only** — GAC_BPTES is a genuine homo-oligomer with no
established chain-correspondence across independent depositions;
re-scoring it against a consensus mask built from possibly-mismatched chain
letters would silently launder that ambiguity into a number, so its
consensus/union labels are defined and reported but deliberately NOT used
to re-score.

- **KRAS_G12C** (not in [[TASK-0243]]'s frozen 22-target set — scored on its
  own native metric, the single-operator CTQW AUC [[TASK-0270]]'s own
  numbers use): single label AUC=0.514, consensus (K=6/12, 22 residues)
  AUC=0.509, union (62 residues) AUC=0.510. Flat, and the diagnosis stays
  `NO_SIGNAL_IN_APO` for all three — matches [[TASK-0270]]'s own finding
  that this target's floor-clear does not survive its genotype fix; no
  label definition rescues it.
- **TRP_SYNTHASE_F6F** (in the frozen set — re-scored in the SAME
  cross-validated geometry+fpocket+CTQW composite framework that actually
  produces this register's "X% unexplained" headline, [[TASK-0254]]'s own
  machinery reused unmodified, features held fixed, only `y` swapped):
  single label AUC=**0.8642** (reproduces [[TASK-0254]]'s own published
  0.864 for this target exactly), consensus (41 residues) AUC=**0.7792**,
  union (53 residues) AUC=**0.7974**. **Broadening the label makes the
  cross-validated AUC substantially WORSE, not better** — an 8.5-point drop
  against consensus. On the single-operator metric too (AUC=0.591 single vs.
  0.549 consensus vs. 0.532 union), AUC falls as the label broadens, though
  P@5 rises (0.0 -> 0.2 -> 0.4) — the union label is easier to partially
  hit in the top-5 even as its own ranking-quality score drops, because a
  larger pocket dilutes what counts as a true negative.

**Answered directly, both outcomes reported with equal prominence per this
task's own Constraint**: no, part of what this register calls "unexplained"
is **not** label noise. In the one case where this was tested against the
actual metric that produces the "unexplained" number (TRP_SYNTHASE_F6F,
cross-validated composite AUC), using a more-agreed-upon, majority-vote
label makes the model's performance *worse*, not better — the single
crystal structure's own label was already at or above the achievable
ceiling for this feature stack, not suppressing it. The reproducibility
measurement is itself real and non-trivial (0.42-0.88 same-drug Jaccard,
never 1.0) — the label genuinely is noisy — but that noise is not what is
holding this register's AUC numbers down. This is a different diagnosis
from [[TASK-0259]]'s crypticity finding and from [[TASK-0254]]'s own
fpocket-variance correction: both of those found real missing predictors;
this task finds the ceiling is not the label.

**Feeds back to [[TASK-0265]]'s independence rule** ("a second ligand on an
apo structure already counted is a new target for label-side questions"):
confirmed, more strongly than that task could show with its own n=5-7 same-
apo pairs — same-drug replicates (a *stronger* form of "the same thing")
still disagree at up to 58% dissimilarity, so two different-drug labels on
the same apo structure are certainly independent enough to count separately.

`documentation/CTQW_CONTRIBUTION_BRIEF.html` §08 **not flagged** — per this
task's own Acceptance, only required if AUC rises against consensus; it
fell.

**Script:** `scripts/task0273_holo_ensemble_label_noise.py`. **Data:**
`results/tasks/0273_holo_ensemble_label_noise/holo_ensemble_label_noise.json`.
**Full detail:** `.ai/tasks/DONE/TASK-0273-experimental-holo-ensembles-and-the-label-noise-floor.md`.

## Does a released, repulsor-held-open pocket stay open? Not testable — it never reliably opens in the first place ([[TASK-0271]], 2026-08-26)

Three prior tasks — [[TASK-0230]] (ceiling), [[TASK-0235]] (local-Kabsch +
EvoEF2), [[TASK-0213]] (coupled search) — displaced a backbone toward the
true holo target and repacked side chains, but **none ever released the
displacement and asked whether the opened pocket stays open.** That is a
direct [[HYP-P13]] test (allostery as *stabilisation of an
otherwise-disfavoured conformation* predicts collapse on release) by a
route independent of [[TASK-0268]]'s frustration test.

**Pre-registered before any structure was scored** (task file has the
full text, not duplicated here): "repulsor held open" = the pre-registered
full apo→holo Cα displacement ([[TASK-0230]]/[[TASK-0235]]'s own
`local_rigid_reconstruction`, reused unchanged — this project has no
backbone minimiser or torsion-space machinery to build a literal pinned
steric atom without risking fabricated clash artifacts, disclosed as such,
not silently substituted). A release trajectory t ∈ {1.0, 0.75, 0.5, 0.25,
0.0} applies the **absolute** (never-compounded) transform at each step; at
t=0.0 the transform is the identity — true, unmodified native apo,
independently repacked by EvoEF2 with no memory of the open state. Run on
[[TASK-0243]]'s own 11 genuinely cryptic-testing targets ([[TASK-0254]]
Part B's own pre-registered crypticity screen — "already_open: false"),
N=4 trials at the two decisive points (t=1.0, t=0.0) with independent
coordinate jitter (σ=0.15 Å, [[TASK-0241]]'s own established magnitude)
and forced-distinct EvoEF2 seeds, trial inputs hashed to confirm
distinctness (44/44 unique at t=1.0, 44/44 at t=0.0). Retention criterion,
fixed in advance:
[[TASK-0204]]'s own `_is_hit` (fpocket overlap ≥0.5 AND druggability
≥0.5), majority (≥3/4) of t=0.0 trials.

**Citation check, done before implementation**: Koehl & Delarue 1994 (*J
Mol Biol* 239:249-275) is real and correctly the origin of SCMF
side-chain packing (verified live) — but it is fixed-backbone; the
filing's own equivalence to Rosetta's FastRelax (which does real backbone
minimisation) overstates it. Corrected, this register's third inherited
citation detail requiring a fix after [[TASK-0260]]/[[TASK-0262]].

**Result, and why the literal pre-registered readout is misleading**: by
the letter of the rule, 11/11 targets return COLLAPSES at t=0.0
(0-1 hits of 4). But the SAME rule applied symmetrically to t=1.0 — the
fully displaced, supposedly "held open" state — ALSO fails a majority for
every single target (0/4 for 9 of 11 targets; 1/4 for the remaining 2:
KSHV_PROTEASE_24Q, KSHV_PROTEASE_25G). **The pocket essentially never
opens correctly-located and druggable at once, anywhere along the
trajectory, including full displacement to the true holo target.** This is
floor-to-floor, not open-to-closed — nothing demonstrably collapses
because nothing demonstrably opened. A cluster-permutation test on the raw
hit counts ([[TASK-0261]]'s own exact method, 8 clusters over 11 targets —
KSHV_PROTEASE_24Q/25G share PDB 2PBK, HCV_NS5B_POO/CMF share 2HAI,
FBPASE_94D/95S share 5LDZ) does return p=0.0078, reported for completeness
only — it measures "hit rate below majority" on a near-zero-variance
series, not retention.

**Verdict: NOT EVALUABLE**, not a clean win for HYP-P13 despite what the
raw pass/fail table would suggest at a glance — read with the same
scrutiny a favourable result would get, per this task's own Constraint.
Joins [[TASK-0264]]/[[TASK-0267]]'s "closed on a prerequisite" category,
reasserting [[TASK-0230]]/[[TASK-0235]]'s own long-standing finding that
the strict overlap+druggability bar is rarely cleared by this register's
rigid/local-Kabsch displacement machinery — this time it swamps the new
question entirely rather than merely limiting it. Descriptive side-note,
not part of the formal bar: druggability_score alone (ignoring overlap) is
sometimes *higher* at t=0.0 than t=1.0 for several targets (FBPASE_94D:
0.75 vs ≤0.46; NAMPT_NPA1R: up to 0.93 vs ≤0.10) — independent EvoEF2
repacking of true native apo can open *some* druggable cavity, just not
reliably the correct one, an echo of [[TASK-0230]] §5.3's own
scorer-brittleness theme rather than a retention finding.

**`.claude/hypotheses/physics.md` updated** with the full method, the
floor-problem caveat, and the citation correction, under [[HYP-P13]]'s own
section, same prominence as [[TASK-0268]]'s decisive negative.

**Script:** `scripts/task0271_repulsor_scmf_retention.py`. **Data:**
`results/tasks/0271_repulsor_scmf_retention/results.json`. **Full detail:**
`.ai/tasks/DONE/TASK-0271-repulsor-constrained-scmf-retention-test.md`.

## `V_C` decomposed: it's the strongest of five physical terms, not the strongest predictor overall — and holo does not obviously beat apo ([[TASK-0275]], 2026-08-26)

[[TASK-0263]] scored `build_H_new`'s five potential terms (`V_B`, `V_T`,
`V_R`, `V_C`, `V_M`) as one lumped block and found terms 0.751 vs CTQW
0.575 — a real result, but it hid that `V_C` (GNM dynamic cross-correlation
centrality, the field's own standard allosteric-coupling measure) already
beats CTQW alone in solo AUC, and that CTQW's own added-last marginal
against the lumped block was p=0.973 (nothing). This task decomposes the
block into its five separate terms in a full Shapley attribution, and
extends the question to holo: does the bound conformation actually help?

**Method, up front**: every number below (apo AND holo) is computed on the
**matched common apo/holo (chain, resnum) residue set**
(`allostery.superpose.align_apo_holo`), not apo's own full residue set —
required so both flavours are scored on an identical node set for a fair
gap comparison. Apo-flavour numbers here therefore differ from
[[TASK-0263]]'s own apo numbers (checked directly, e.g. `DHPS_GC7` `V_C`:
0.392 → 0.586) — CTQW and geometry are graph-topology-sensitive, and
restricting to the common set changes the graph. `fpocket` is excluded
from the holo arm entirely (a cavity detector on a drug-shaped-open
cavity trivially recovers the label) — every holo number is a ceiling,
never predictive performance, per this task's own pre-registered leakage
table. 8-block (apo) / 7-block (holo) exact Shapley ran in full — timed
first (~0.042s/`cv_auc` call, ~11 min projected for both flavours) — the
6-block fallback this task's Scope allowed for was not needed.

**Headline: does CTQW add anything once `V_C` alone is in the model?
No, in apo, exactly as `V_C`'s own solo strength predicted.**
AUC(`V_C`+CTQW) − AUC(`V_C` alone): apo median **−0.0047**, cluster-robust
p=0.30 ([[TASK-0261]]'s method, 13 clusters) — CTQW's marginal on top of
`V_C` alone is at or below zero. On holo, a small, real, positive effect
reaches marginal significance (median **+0.0051**, p=0.037) — real but
tiny (half a percentage point of AUC), not the "CTQW recovers value given
the right conformation" result that would have made [[TASK-0263]]'s
finding conformation-dependent rather than propagator-dependent. The full
8/7-block added-last marginal (CTQW against every other block, not just
`V_C`) stays indistinguishable from zero in both flavours (apo median
−0.0005 p=0.21; holo median +0.0016 p=0.69) — confirming [[TASK-0263]]'s
own original finding (p=0.973 there) against `V_C` specifically as well
as the lumped block.

**Complementary, not subsumed.** `V_C` carries the largest median Shapley
share among the five terms (apo +13.3%, holo +14.3%, clearly above
`V_B`/`V_R`/`V_T`/`V_M`), but every other term still contributes a real,
if smaller, positive median share in at least one flavour — none driven
to zero by `V_C`'s presence, consistent with [[TASK-0263]]'s own finding
that all ten cross-term correlations are weak. Geometry (apo +26.5%, holo
+24.6%) and fpocket (apo +10.5%, apo-only) remain the largest single
contributors overall: `V_C` is the strongest of the five *physical* terms,
not the strongest predictor in the full model — a real distinction from
how [[TASK-0263]]'s own lumped framing could be read.

**Per-term apo→holo gap vs. the pre-registered crypticity prediction
(negative correlation, larger gap on cryptic targets): does not hold.**
Cluster-permutation correlation against [[TASK-0254]] Part B's own
`fraction_open`: `V_B` ρ=−0.376 p=0.14 (right direction, not
significant); `V_R` ρ=**+0.464 p=0.025** (significant, **wrong
direction**); `V_C` ρ=+0.166 p=0.57; `V_M` ρ=+0.001 p=0.999; CTQW
ρ=+0.038 p=0.87. `V_T` excluded — a real structural fact, not noise: it
depends only on residue count, not coordinates/B-factors, so on the
matched common set its gap is identically 0.0 for all 20 targets. At the
per-term level, crypticity is not what the apo penalty is made of —
[[TASK-0259]]'s own ρ=−0.771 (a different, aggregate observable) does not
decompose cleanly onto these five physical terms.

**A bigger, unplanned finding underneath that null: holo does not
obviously act as a ceiling above apo at all, on these 7 non-leaky blocks.**
A like-for-like check (apo scored on the identical 7-block set as holo,
fpocket excluded from both) shows apo's own median full AUC (0.896) is
numerically *higher* than holo's (0.834), apo ahead on 14/20 targets — not
statistically significant (cluster-robust p=0.10), so not a claim that
apo beats holo, but a clean absence of the assumed holo advantage for
this feature set.

**Read together with [[TASK-0276]], per this task's own instruction**:
[[TASK-0276]] (completed concurrently) found a real positive signature —
`V_C`, the same term this task centers on, significantly discriminates
allosteric from orthosteric sites within holo structures, in two
independent families (KRAS_G12C, HCV_NS5B). That is not this task's own
"tension" scenario (which required [[TASK-0276]] to find *no* separation
while this task found large holo gains) — instead the two combine: `V_C`'s
signal is real and robust ([[TASK-0276]]), and it does not require the
bound conformation to be present (this task: no significant apo→holo
gain). **The physics `V_C` captures is already available from the unbound
structure** — the actionable, favourable version of the ceiling question
at the feature level.

`documentation/CTQW_CONTRIBUTION_BRIEF.html` §04 **flagged for an update,
not edited here** — needs the sharper `V_C`-vs-CTQW headline (both
flavours) and the apo/holo ceiling-null finding.

**Script:** `scripts/task0275_term_decomposition_apo_holo.py`. **Data:**
`results/tasks/0275_term_decomposition_apo_holo/`. **Full detail:**
`.ai/tasks/DONE/TASK-0275-per-term-decomposition-V_C-carries-it.md`.

## Our "apo" structures are not apo: three are pocket-confounding, one is BCR-ABL1's own mandatory target ([[TASK-0278]], 2026-08-26)

BCR-ABL1's myristoyl pocket is "pre-formed" in our own apo (`1OPL`) —
checked live against RCSB, and worse than a spot-check would suggest:
`1OPL` is doubly ligand-bound (`MYR` myristic acid + `P16`, an ATP-site
inhibitor), and `MYR` sits directly in the pocket the pipeline is asked
to predict. The underlying measurement already existed — [[TASK-0209]]'s
own `hetatm_audit` (2026-08-07) flagged `MYR` as `unexpected_near_pocket`
at the time — but it never had a named, reusable rule, and was never
extended to the rest of the register.

**Method, and a real defect caught in the naive version before trusting
any number**: every non-water HETATM group across all 29 distinct apo
PDB structures in `config/targets.yaml` and `config/candidate_targets_
task0243.yaml` was enumerated directly from the resolved structure
(`backend.rcsb.ligands_and_sites` — not the RCSB Data API's own
`nonpolymer_bound_components`, [[TASK-0270]]'s own already-found blind
spot for silently missing non-coordinating ligands). The first pass
over-flagged 16/29 structures — two correctable defects, both fixed
before reporting a single number:

1. **Covalent in-chain modifications counted as free ligands.** `M3L`
   (N-trimethyllysine, `CARDIAC_MYOSIN`'s own `8QYP`), `ACE`/`GG7`
   (N-terminal caps) are peptide-bonded to their chain neighbours (C–N
   distance ~1.34 Å, checked directly, not assumed) — `Bio.PDB`'s own
   hetero flag does not distinguish "free small molecule" from "covalent
   modified residue," both are HETATM in the PDB format. Excluded via a
   real bond-distance check. 14/29 structures remain flagged after this
   fix.
2. **Cognate substrates/products misread as synthetic.** `backend.rcsb.
   classify_ligand` was built for the live app's "is this worth
   highlighting as a drug" question, not "is this cognate for THIS
   enzyme" — it flags `GLN` (glutaminase's own substrate, `GAC_BPTES`/
   `GAC_CPD12`'s apo `7SBN`, itself deposited as "...with L-Gln, closed
   conformation"), `GLC` (glucose, `GLUCOKINASE`'s own substrate), `FBP`
   (phosphofructokinase's own reaction product — `1PFK` is explicitly
   titled "...WITH ITS REACTION PRODUCTS"), and `NMN` (NAMPT's own
   reaction product) as drug-like. Corrected by hand, each checked
   against the specific enzyme's own biology, not a blanket override.

**The decisive test is not "does the apo structure contain a ligand," it
is whether that ligand overlaps the SPECIFIC pocket window being
scored** — computed directly (binding-site residues vs. each target's own
pocket window), not assumed from presence alone:

| target | apo | occupant | window overlap | verdict |
|---|---|---|---|---|
| **BCR_ABL1** (mandatory) | `1OPL` | `MYR` | **75%** | **pocket-confounding** |
| **GLUCOKINASE** | `1V4S` | `MRK` | **88%** | **pocket-confounding** |
| **PKR_MITAPIVAT** / **PKR_AG946** | `7FS3` | `O9I` | **92% / 91%** | **pocket-confounding — the worst case found, and not in this task's own original filing** |
| CARDIAC_MYOSIN | `8QYP` | `VO4` (vanadate) | **0%** | not pocket-confounding — corrects this task's own filing's "suspect" label |
| HCV_NS5B ×4, KSHV_PROTEASE ×2, SMYD3_DIPERODON, PF_ATCASE | `2GIQ`/`2HAI`/`2PBK`/`6P7Z`/`7ZP2` | real inhibitors (each entry's own RCSB title names it a complex) | 0% each | ligand-bound, not clean apo, but not confounding *this* pocket |

**`PKR_MITAPIVAT`/`PKR_AG946` is a new, real, and worse-than-BCR_ABL1
finding**, surfaced only because this task's own Scope asked for the full
register sweep rather than stopping at BCR-ABL1. `7FS3` — used as "apo"
for both targets — is deposited as "Structure of liver pyruvate kinase in
complex with allosteric modulator 15"; that modulator (`O9I`) covers
91–92% of the very window these two targets are scored on. **Not
remediated here** (PKR is not a mandatory target and this task's own
Scope asks only for a BCR_ABL1 decision) — flagged with full prominence
for a follow-up task.

**BCR_ABL1 decision: keep `1OPL`, report the defect explicitly.**
Finding a genuinely myristoyl-pocket-empty ABL1 structure is foreclosed —
[[TASK-0270]] already searched real candidates (`2G1T`, `2G2H`, `2G2I`)
and found none clean, with scored evidence against substituting (`2G1T`
AUC=0.350, below chance). Computationally stripping `MYR` was run
explicitly, as a **disclosed control, not a silent fix** — and the result
argues decisively against treating it as one:

| | native `1OPL` (`MYR` present) | `MYR` computationally stripped |
|---|---|---|
| window overlap_frac | 0.875 | 0.875 (**unchanged**) |
| window druggability_score | 0.761 | 0.566 (drops, still a hit) |
| residue-level fpocket AUC | 0.8952 | 0.8952 (**bit-identical**) |
| `apo_native_hit` | **True** | **True** (unchanged) |

**Deleting `MYR`'s own atoms does not close the pocket**, because
fpocket's cavity detection is driven by the protein backbone's own
geometry — already in the myristate-stabilised open conformation — and
nothing in this register's toolchain relaxes a backbone after ligand
removal (the same absence of a real minimiser [[TASK-0271]]'s own
repulsor-release test hit from a different angle). This sharpens, not
softens, the finding: the confound is not "an atom happens to be present
in the file," it is that the crystallised conformation itself was
captured with the pocket already held open.

**Why this matters beyond one target**: [[TASK-0120]]/[[TASK-0139]]'s
"pre-formed pocket" (RMSD ratio 0.49) and fpocket's own strong BCR_ABL1
solo score are, at least in significant part, properties of `1OPL`'s own
crystal contents, not a discovery about c-Abl's intrinsic dynamics. It is
also direct, mechanistic, single-target evidence for [[TASK-0265]]'s own
statistical finding: myristic acid occupies the myristoyl pocket without
producing the therapeutic allosteric effect asciminib does — same pocket,
different occupant, different outcome. Allostery is a property of the
protein–ligand complex, not of the cavity.

`.claude/hypotheses/` not touched (this is a benchmark-construction
finding, not a mechanistic hypothesis test). `.ai/tasks/DONE/TASK-0209-
known-answer-cryptic-instance-set.md` carries the reusable classification
rule as a dated addendum. `documentation/PHASE1_SUBMISSION_DRAFT.md`
**flagged for an update, not edited here** — it currently discusses
BCR-ABL1's pre-formed pocket without this cause.

**Scripts:** `scripts/task0278_apo_contents_audit.py`,
`scripts/task0278_bcr_abl1_myr_strip.py`. **Data:** `results/tasks/
0278_apo_contents_audit/`. **Full detail:** `.ai/tasks/DONE/TASK-0278-
our-apo-structures-are-not-apo.md`.

## The ligand-selectivity gate: `V_C` does not survive contact with an inert-vs-efficacious control ([[TASK-0279]], 2026-08-26)

[[TASK-0276]] found `V_C` (GNM dynamic cross-correlation centrality)
significantly separates allosteric from orthosteric sites in two families
— the register's first real holo-side positive. [[TASK-0278]] flagged the
gap it could not close: does `V_C` measure allosteric *efficacy*, or just
that a cavity is occupied and coupled? BCR-ABL1 gives the one controlled
pair in this register where the imprint confound cancels — same protein,
same myristoyl cavity, one inert occupant (`1OPL`/`MYR`, myristic acid, no
therapeutic autoinhibition) and one efficacious modulator
(`5MO4`/`AY7`, asciminib).

**Method**: reuses [[TASK-0276]]'s own ligand-stripping
(`write_ligand_stripped_pdb`/`ligand_stripped_sasa`) unchanged. Node sets
matched via `allostery.superpose.align_apo_holo` (429 common (chain,
resnum) Cα pairs; 16/16 myristoyl-pocket and 26/26 active-site residues
survive), per [[TASK-0275]]'s own established requirement — an unmatched
comparison moved `DHPS_GC7`'s own `V_C` by 0.19 in that task. Graph
features (`V_C`, `degree`, `euclid`, `hop`) computed on coordinates
RESTRICTED to the common set; `V_B`/`SASA` computed on each structure's
own full resnums (a local, all-real-neighbours quantity) and indexed
afterward. Both arms are doubly occupied (`1OPL`: `MYR` + `P16`; `5MO4`:
`AY7` + `NIL`) — stated explicitly, not treated as apo, per [[TASK-0278]]'s
own precedent.

| feature | myristate (`1OPL`) median | asciminib (`5MO4`) median | Δ | frac. favouring asciminib (n=16) | Wilcoxon p |
|---|---|---|---|---|---|
| **`V_C`** | **+57.44** | **+53.63** | **−3.86** | **0/16** | **<0.0001** |
| `degree` | +9.50 | +9.50 | +0.00 | 1/16 | 0.317 |
| `euclid` | −24.88 | −24.72 | +0.15 | 15/16 | 0.0001 |
| `hop` | −3.00 | −3.00 | +0.00 | 1/16 | 0.317 |
| `V_B` | +57.43 | +25.33 | −33.05 | 0/16 | <0.0001 |
| `SASA` | +15.83 | +15.22 | +1.45 | 12/16 | 0.079 |

**`V_C` is HIGHER on the inert myristate pocket than the efficacious
asciminib pocket, 16/16 residues, ~7% relative** — the opposite direction
the efficacy-specific reading of [[TASK-0276]]'s own positive required.
Not the pre-registered "no separation" outcome exactly — a significant
separation in the *wrong* direction, a stronger negative for the efficacy
reading than a null would have been.

**A confound this task cannot rule out, disclosed prominently**: `1OPL`
(myristate) is 3.42 Å resolution; `5MO4` (asciminib) is 2.17 Å. `V_B`'s
own huge, maximally clean gap (0/16, 57.4 vs 25.3) is almost certainly
this artifact — [[TASK-0250]] had already independently flagged `1OPL` as
MARGINAL (r=0.493) on the B-factor-correlation ENM-validity check, itself
consistent with a lower-quality model. `V_C` is coordinate- not
B-factor-derived, so not susceptible to the *same* mechanism, but
coordinate precision at 3.42 Å is coarser regardless — this n=2-structure
gate cannot distinguish "asciminib genuinely produces lower coupling" from
"the coarser model differs regardless of ligand." **[[TASK-0278]] landed
the same day and independently corroborates this**: its own MYR-stripping
control on `1OPL` found the myristoyl pocket does NOT close when the
ligand atoms are computationally removed — "the confound is the
crystallized backbone conformation, not the ligand atoms' mere presence"
— the same open question from a different angle.

**Read plainly**: `V_C` provides no support for the efficacy-specific
reading of [[TASK-0276]]'s own positive, and — subject to the resolution
caveat — points the opposite direction. [[TASK-0276]]'s own positive
should now be read as a real holo-side structural pattern, **not yet
distinguished from an occupancy/cavity-coupling explanation** — recorded
directly in that task's own Done section.

**Extending the design (searched, not found)**: KRAS's ten-drug ensemble
ruled out (all efficacious, per the task's own filing). Checked live —
HCV_NS5B's own thumb/palm allosteric-site literature and glutaminase/GAC's
own BPTES-site literature — no specific inert occupant of the SAME site
as one of this register's own already-curated ligands was identified
within this task's own bounded search; establishing that with confidence
needs a structure-by-structure potency check, a real follow-up not
attempted further here.

**Script:** `scripts/task0279_ligand_selectivity_gate.py`. **Data:**
`results/tasks/0279_ligand_selectivity_gate/ligand_selectivity_gate.json`.
**Full detail:**
`.ai/tasks/DONE/TASK-0279-ligand-selectivity-gate-occupancy-vs-efficacy.md`;
[[TASK-0276]]'s own DONE file carries a dated note recording this reading.
## Holo-only: the allosteric site IS structurally distinguishable from the orthosteric site, even with the answer in hand — a real signature, shared across drugs, in two independent families ([[TASK-0276]], 2026-08-26)

Every negative in this register (nine of them) is of the form "method X
cannot predict the allosteric pocket from apo." Nobody had asked the prior
question: is it distinguishable **in holo**, where every piece of
information — including the drug's own induced-fit imprint — is actually
present? If not even that succeeds, this project's whole task is ill-posed
from structure alone, not merely hard. This is the first time any structural
feature has ever been computed ON a holo structure and compared across them
([[TASK-0273]] only ever compared holo structures via the label itself,
Jaccard of contact sets).

**The leakage trap, and how this was designed around it**: a holo pocket is
open *because* the drug is there, so "find the open cavity" trivially
recovers any ligand-contact label and proves nothing. The comparison run
here is the sharp version instead: within the SAME holo structure, is the
**allosteric** drug's own contact site distinguishable from the
**orthosteric** (catalytic/nucleotide) site? Both are real, independently-
defined ligand-adjacent-or-catalytic sites, both leave an imprint — neither
is "empty space." Every feature is computed on the structure with every
non-protein atom physically removed first (a separate, explicitly-built
ligand-stripped copy for every feature, including SASA, where computing on
a ligand-containing model would show artificially low exposure exactly
where the drug sits — the leakage trap in a different guise).

**Design**: self-referential throughout — every holo structure supplies its
own 5 features (ligand-stripped) AND its own two label groups (from its own,
unstripped coordinates). No apo structure appears anywhere in this task.
Orthosteric definition matched to what each family actually has: KRAS's own
co-bound GDP (present in all 10) via direct ligand-contact; HCV_NS5B has no
co-bound catalytic ligand (`func_ligand: []` in this register's own config)
so orthosteric there is `backend.active_site.detect_active_site`'s live
UniProt call — the SAME machinery `task0242_two_stage_dryrun.prep()` already
uses for every CAND-set target (verified directly: HCV_NS5B_CMF's own seed
= residues 220/318/319, the classic GDD/YGDD catalytic motif of an RNA
polymerase — a real functional site, not a topological proxy).

**5 features**, chosen to be independent of ligand-contact geometry itself:
`V_C` (GNM dynamic cross-correlation centrality — [[TASK-0275]]'s own
strongest single potential term), `V_B` (this holo structure's own raw
B-factor), `degree` (binary contact centrality), `SASA` (BioPython
Shrake-Rupley, ligand-stripped), `fpocket` (per-residue druggability,
ligand-stripped). **Statistic**: per structure, does the feature rank
allosteric residues above orthosteric ones — `metrics.auc` restricted to
only the union of the two labeled groups, matching this register's own
ranking-AUC convention everywhere else, just with a different two-class
target. Aggregated with an exact cluster-level sign-flip test
([[TASK-0261]]'s own algorithm).

**Stage 2 family fixed BEFORE Stage 1 was run** (task's own requirement):
HCV_NS5B, on coverage — 4 distinct allosteric chemotypes already verified in
this register's own frozen config, more diversity than the other candidates
(GAC/PKR/TRP_SYNTHASE/KSHV_PROTEASE each have only 2).

### Two real bugs found and fixed en route

Both `9UOH`/`8S8C` (5-character extended chemical-component IDs, A1L9E and
A1H5U) failed prody's legacy PDB parser — the same limitation [[TASK-0273]]
found, now fixed **at the shared source** this time: `allostery.clean.clean()`
itself falls back to mmCIF on `PDBParseError` (verified: all 12 pre-existing
`test_clean.py` tests still pass; full suite re-run clean, 2 pre-existing
unrelated failures confirmed independent of this change — a stale
`4OBE`-expecting test predating [[TASK-0270]]'s genotype fix, and a
documentation-text linter). A second, subtler bug then surfaced: prody's
mmCIF parser assigns each HETATM group its **own** chain letter, unlike the
legacy parser which keeps it on its neighboring protein chain's letter —
restricting to `chain A` *before* extracting ligand groups silently dropped
GDP and the drug ligand entirely for both affected entries, collapsing their
active-site resolution to the tier-3 topological-proxy fallback and their
pocket to empty. Fixed by extracting ligand groups from the unrestricted
parse. 10/10 KRAS structures usable after both fixes (was 8/10).

### Stage 1 — KRAS_G12C (10 different drugs, GDP orthosteric)

| feature | AUC median (allosteric ranks higher when >0.5) | cluster-p (n=10 independent structures) |
|---|---|---|
| **fpocket** (druggability) | **0.675** | **0.0039** |
| **degree** (contact count) | **0.405** (orthosteric ranks higher) | **0.0020** |
| **V_C** (DCC centrality) | **0.595** | **0.0117** |
| **SASA** | **0.551** | **0.0215** |
| V_B (raw B-factor) | 0.587 | 0.0742 (not significant) |

**4 of 5 features discriminate allosteric from orthosteric significantly,
at the finest cluster resolution this ensemble allows (n=10 independent
depositions).** Not one accidental signal — a coherent pattern: the
allosteric site is more dynamically coupled to the rest of the structure
(`V_C` up), more solvent-exposed (`SASA` up), and scores higher on a pure
geometric druggability heuristic (`fpocket` up) than the orthosteric site —
**but has LOWER raw contact degree**, the opposite direction. That last
point matters: the allosteric site is not simply "the well-connected
residues" — degree, the crudest static-connectivity measure, actively
disagrees with `V_C`, the dynamics-aware one. Whatever distinguishes it is
specifically dynamical/geometric, not raw connectivity.

**Commonality**: a 16-residue consensus (present in ≥6 of the 10 chemically
distinct drugs' own allosteric-contact sets; K stated before computing) —
`A:9/58/60-64/68/69/72/95/96/99/100/102/103`, squarely the Switch-II pocket.
Pairwise allosteric-site Jaccard across all 10 (all different-drug pairs,
since no two of these share an apo): median **0.650** — substantial
consistency in WHICH residues the pocket comprises, across 10 structurally
and chemically unrelated inhibitors.

### Stage 2 — HCV_NS5B (4 drugs, UniProt-catalytic orthosteric)

| feature | AUC median | cluster-p (n_clusters=2 — floor-limited, see below) |
|---|---|---|
| **fpocket** | **0.967** | 0.5000 |
| **V_C** | **1.000** (every one of 4 structures, exactly) | 0.5000 |
| V_B | 0.775 | 1.0000 |
| SASA | 0.411 | 0.5000 |
| degree | 0.211 (orthosteric ranks higher) | 0.5000 |

**Same direction on every feature as KRAS** — `V_C` up, `fpocket` up,
`degree` down — in a protein with a different fold, a different function
(viral RNA polymerase vs. a small GTPase), and an orthosteric site resolved
by a completely different mechanism (UniProt annotation, not a co-bound
ligand). With only 2 independent clusters (`n_clusters=2`), the exact
sign-flip test's own minimum achievable p-value is **0.5** regardless of
effect size — `V_C=1.000` in literally all 4 structures is a maximal,
noise-free effect that the p-value cannot express as significant with this
few clusters; reported honestly as floor-limited, not as "not significant"
in the ordinary sense.

**Commonality, properly stratified — the more interesting finding than a
flat consensus number**: CMF/POO (same apo, 2HAI) have allosteric-site
Jaccard **0.941** — nearly identical. VR1/VRX (same apo, 2GIQ) likewise
share an apo. But CMF/POO **vs.** VR1/VRX: Jaccard **0.000** — zero overlap.
NS5B does not have one common allosteric site the way KRAS does; it has (at
least) two, each individually near-perfectly conserved across its own
chemotype, entirely disjoint from the other. A real, useful, more precise
answer than either "yes, one site" or "no, no site."

### Verdict against the task's own pre-registered outcome table

**Row 2: "A signature exists in holo and is shared across drugs."** Not row
1 (ill-posed) — the most consequential possible negative did not happen.
Not row 3 alone (drug-specific) either, though HCV_NS5B shows drug-specific
*sub*-structure (two disjoint sites) nested inside a family-level signature
that itself replicates KRAS's own direction on every feature. **The task is
well-posed from structure alone, at least in these two families**: a real,
non-circular, coherent structural/dynamical signature separates allosteric
from orthosteric sites, even with the answer already in hand — reproduced
independently in a second protein with nothing else in common with the
first.

**Per row 2's own next question, explicitly NOT attempted here** (this
task's own Constraint: descriptive characterisation and a ceiling
measurement, never a predictor scored circularly against its own label) —
does any trace of this signature (particularly `V_C`, the one feature that
is not itself a druggability/pocket-shape heuristic and therefore the
hardest to dismiss as "of course a drug pocket looks druggable") survive
into **apo**? That is a concrete, separate, later task, and this one's own
finding is what gives it a real target to test.

**One honest caveat, stated so the finding isn't oversold**: `fpocket`'s
own discrimination is the least surprising of the four significant
features — a nucleotide/phosphate-cradling cofactor site and a
small-molecule drug pocket differing on a druggability heuristic tuned
for small-molecule pockets is close to expected. `V_C`'s result is the
sharper claim: it is a pure network-dynamics measure with no notion of
pocket shape or drug-likeness at all, and it still separates the two site
classes significantly in KRAS and perfectly (if underpowered) in HCV_NS5B.

**Script:** `scripts/task0276_holo_only_structural_signature.py`. **Data:**
`results/tasks/0276_holo_only_structural_signature/holo_only_structural_signature.json`.
**Full detail:** `.ai/tasks/DONE/TASK-0276-holo-only-what-does-an-allosteric-site-look-like.md`.

## The apo→holo ceiling sweep, generalized: 8 more features, and the ceiling is a NULL almost everywhere — the same finding as TASK-0275's, now on a disjoint feature set ([[TASK-0277]], 2026-08-26)

[[TASK-0275]] covers the 5 `build_H_new` potential terms plus CTQW.
[[TASK-0276]] asks the discrimination-existence question. Neither covers the
rest of this register's own feature stack. This task sweeps everything else
with a non-severe leakage grade: `degree`/`euclid`/`hop` scored
**individually** (not as one combined geometry block), `dcc_low`/`prs_low`
(`lowmode_predictor.py`), ground-state relaxation on the identical `H_new`
CTQW uses (**not actually classical diffusion** — `H_new` is indefinite on
essentially this whole frozen set per [[TASK-0256]]'s own established
finding, reported that way throughout, never re-labelled), single-residue
mutational frustration ([[TASK-0268]]'s own CA-coordinate convention,
matched exactly rather than task0204's CB variant, to avoid a second,
inconsistent frustration number for the same targets), and SASA (natural,
ligand-**present** holo burial — deliberately not stripped, unlike
[[TASK-0276]]'s design, since this task's own leakage table asks for the
real, flagged-moderate-leakage number, not a controlled one). fpocket/
P2Rank/PocketMiner excluded (severe leakage, unchanged from this task's own
table). Conservation/chemistry have no holo flavour at all — sequence- and
residue-type-derived, identical apo and holo by construction — stated, not
computed; this independently confirms [[TASK-0274]]'s own negative
(conservation −0.08%, chemistry −0.35%, both indistinguishable from zero)
was not a conformation problem, since those features already had every
structural advantage holo could offer and still contributed nothing.

**Method, identical to [[TASK-0275]]'s own established recipe** (both
flavours scored on the matched common apo/holo (chain, resnum) residue
set, `allostery.superpose.align_apo_holo`, never apo's own full set vs.
holo's own reduced one) — and the same **AUC definition**, `task0254`'s own
cross-validated `cv_auc`, even for a single feature, so every "AUC" in this
register's apo/holo tables is one consistent recipe, not two. 20/22
TASK-0243 frozen-set targets usable (HIV_INTEGRASE_MUT871/916 excluded —
this register's own long-standing empty-active-site-seed data gap,
unrelated to this task).

### Consolidated table

| feature | apo AUC | holo AUC | gap (median, cluster-robust) | p |
|---|---|---|---|---|
| degree | 0.541 | 0.484 | −0.033 | 0.096 |
| euclid | 0.706 | 0.713 | −0.001 | 0.687 |
| hop | 0.699 | 0.648 | −0.005 | 0.172 |
| dcc_low | 0.615 | 0.600 | −0.011 | 0.561 |
| prs_low | 0.459 | 0.503 | −0.001 | 0.093 |
| ground-state relaxation | 0.675 | 0.648 | −0.002 | 0.954 |
| frustration | 0.572 | 0.557 | −0.000 | 0.571 |
| SASA (n=18) | 0.449 | 0.525 | −0.019 | 0.528 |

**None of the 8 features shows a significant apo→holo gap.** Several are
numerically negative — holo *slightly worse* than apo, not better — and
none crosses the cluster-robust p<0.05 bar even at its most favorable
reading. `ground_state_relaxation`'s own p=0.954 is about as flat a null
as this register has ever reported for anything.

### Central question: concentrated in the dynamical features, or uniform?

**Uniform — and "uniform" here means uniformly close to zero, not
uniformly large.** Dynamical group (`dcc_low`, `prs_low`,
`ground_state_relaxation`, n=60 target-feature pairs): median gap
**−0.0023**. Static group (`degree`, `euclid`, `hop`, `SASA`, n=78):
median gap **−0.0048**. Mann-Whitney U p=**0.1205** — not distinguishable,
and if anything the STATIC group's gap is numerically larger (more
negative) than the dynamical group's, the opposite of the "dynamics
specifically needs the bound conformation" hypothesis this task's own
filing named as one of the two live possibilities. Neither half of that
hypothesis survives: there is no large gap to be concentrated anywhere.

### Crypticity stratification — the pre-registered prediction, again

Same prediction [[TASK-0275]] tested at the potential-term level (larger
apo→holo gap on cryptic targets) tested again here, independently, on this
disjoint 8-feature set: **does not hold, and where it moves, it moves the
wrong way.** `degree` (open +0.0075 vs. cryptic **−0.0688**), `SASA` (open
−0.0024 vs. cryptic **−0.0920**), `dcc_low` (open +0.0055 vs. cryptic
−0.0195), `ground_state_relaxation` (open **+0.0355** vs. cryptic −0.0146)
all show the gap getting MORE negative — holo doing relatively *worse*, not
better — specifically on the targets where the label says holo's bound
conformation should matter most. `euclid`/`prs_low`/`frustration` are flat
in both regimes. This is the same direction, independently, as
[[TASK-0275]]'s own per-term correlation result (`V_R` significantly wrong-
signed, the rest null) — two disjoint feature sets, same conclusion:
crypticity is not what any measured apo penalty is made of.

### Reconciliation with [[TASK-0275]] and [[TASK-0276]]

**No tension — the three tasks combine into one coherent picture.**
[[TASK-0275]]'s own 7-block composite found the same null (apo median AUC
0.896 numerically *above* holo's 0.834, p=0.10) for the potential terms and
CTQW. This task finds the identical qualitative result — flat-to-negative,
never significant — across a fully disjoint 8-feature set spanning static
geometry, low-mode dynamics, ground-state relaxation, packing frustration,
and burial. **Between the two tasks, essentially this entire register's
feature repertoire has now been checked for a holo advantage, and none of
it shows one.** [[TASK-0276]] is not in tension with this either, despite
initially looking like it should be (this task's own pre-registered "tension"
scenario was large holo gains alongside no allosteric/orthosteric
separation): [[TASK-0276]] found a REAL, significant structural signature
distinguishing allosteric from orthosteric sites in holo (`V_C`, `fpocket`,
`degree`, `SASA`). This task shows that signature is not a holo-only
artifact needing the bound conformation to appear — apo already carries
essentially the same predictive information. Read together: **the
structural signature [[TASK-0276]] found is real, and it is already
available without the drug bound.** That is the favorable resolution of
the ceiling question this whole three-task arc was built to answer, and it
gives [[TASK-0276]]'s own explicitly-deferred next question (does `V_C`
survive into apo?) a strong prior answer before that task is even run:
almost certainly yes.

`documentation/CTQW_CONTRIBUTION_BRIEF.html` §04/§08 **not touched here** —
flagged for whoever owns the brief for this batch, per [[TASK-0275]]'s own
precedent of flagging rather than editing.

**Script:** `scripts/task0277_apo_holo_ceiling_sweep.py`. **Data:**
`results/tasks/0277_apo_holo_ceiling_sweep/summary.json`,
`per_feature_auc_apo_holo.json`. **Full detail:**
`.ai/tasks/DONE/TASK-0277-apo-holo-ceiling-sweep-every-feature.md`.

## The post-hoc "capacity to couple" rescue of `V_C`, tested on data that did not generate it — it dies ([[TASK-0281]], 2026-08-27)

[[TASK-0279]] found `V_C` (GNM dynamic cross-correlation centrality)
**higher on BCR-ABL1's inert myristate pocket than its efficacious
asciminib pocket** — the wrong direction for an efficacy reading. A
reading proposed *after* seeing that result: `V_C` measures a pocket's
**capacity to couple**, not whether coupling is exercised — an
efficacious drug clamps the site and quenches fluctuations; an inert
occupant leaves it intact (the Cooper–Dryden mechanism, arrived at from
this register's own data). Post-hoc and worth nothing until it survives a
test on independent data — this task is that test, pre-registered before
a single new number was computed.

**The instrument**: [[TASK-0280]]'s clustering of [[TASK-0276]]'s stored
KRAS footprints found KRAS is a 9:1 two-site protein — nine of ten
verified holo structures dock at Switch-II (consensus residues 9,
58–72, 95–103); `7A1X` alone docks at a different site, the Switch-I/II
groove (footprint 37, 39, 54, 55, 56, 71, 74, 75). That gives each site
observed both docked and undocked in the same protein — a different site,
different protein, from the pair that generated the hypothesis.

**Pre-registered predictions, fixed in the task file before any number
was computed**: P1, `V_C` at Switch-I/II higher when undocked (9 holo +
`4LDJ` apo, n=10) than docked (`7A1X`, n=1). P2, the same direction at
Switch-II (undocked `7A1X` higher than the nine docked). **Both must hold
for the hypothesis to survive** — "a result that holds at one and not the
other is a null, not a partial success," fixed in advance specifically so
this could not be adjusted after seeing the numbers.

**Method**: every one of the ten holo structures aligned independently
against `4LDJ` (the register's own verified genuine apo) via
`align_apo_holo` — `V_C`/`degree` computed on the common-set-restricted,
matched coordinates (non-negotiable per [[TASK-0275]]/[[TASK-0279]]);
`V_B`/SASA on each structure's full resnums, indexed at the common set
afterward. Ligand stripped throughout ([[TASK-0276]]'s own method).

**P1: weak, direction-consistent, not clean.** 9 of 10 undocked
observations score higher `V_C` than the one docked structure (`7A1X`,
12.684) — median undocked 12.967 vs docked 12.684, the predicted
direction. But separation is not clean: one undocked structure (`6OIM`,
12.604) scores *below* the docked value, and two more sit within 0.05 of
it.

**P2: fails outright, wrong direction.** Predicted: undocked (`7A1X`,
14.966) higher than the nine docked structures. Measured: **the docked
group's own median (15.097) is HIGHER than the undocked value**, and 6 of
9 individual docked structures exceed it. Not merely "no difference" —
this points in the direction the hypothesis explicitly predicts *against*,
the same direction as the original BCR-ABL1 anomaly the capacity reading
was invented to explain away.

**Verdict, per the task's own pre-registered logic: the capacity
hypothesis DIES.** P1's weak trend and P2's outright reversal do not
together support it. Not untestable — both predictions produced clear,
computable answers at the pre-specified sites. Not a partial success —
the task's own Constraint forbids reading P1 alone as a win when P2 was
pre-registered as an equally decisive arm. `V_C`'s BCR-ABL1-derived
direction does not generalise, and no reading proposed so far explains
both the original anomaly and this test.

**P3, answered independently of the verdict above**: fpocket detects a
real cavity overlapping the Switch-I/II window in effectively every
undocked structure (best overlap_frac 0.125–1.00, ≥0.5 in 7 of 10;
`4LDJ` apo itself: 0.875). Per the pre-registered reading rule, this site
is an **unoccupied open groove, not a genuinely cryptic pocket**, in most
of these structures — independently informative for how [[TASK-0259]]'s
own crypticity correlation should be read on a multi-site protein.

[[TASK-0279]]'s own record updated with a dated addendum recording this
outcome, per this register's own cross-task convention. Extending to a
second multi-site protein was not attempted — [[TASK-0280]] had not yet
surfaced one when this task ran — and is flagged, not silently dropped.

**Script:** `scripts/task0281_docked_undocked_capacity.py`. **Data:**
`results/tasks/0281_docked_undocked_capacity/`. **Full detail:**
`.ai/tasks/DONE/TASK-0281-docked-vs-undocked-and-the-capacity-hypothesis.md`.
## KRAS's second site is real and published; the register now has direct structural evidence for H6.2 across 7 proteins ([[TASK-0280]], 2026-08-27)

[[TASK-0276]]'s own stored KRAS footprints, clustered by pairwise Jaccard,
showed a 9:1 split: nine of ten drugs share the Switch-II pocket (consensus
9, 58–72, 95–103; pairwise range **0.43–0.90**), and one (`7A1X`, ligand
`QWB`) sits at **0.00 Jaccard against eight of the nine, 0.04 against the
ninth** — footprint 37, 39, 54, 55, 56, 71, 74, 75. That reading was the
Reviewer's own inference from raw coordinates, not yet a verified citation
— this task closes that gap, live, rather than shipping an unverified site
identification.

**Verified live**: `7A1X`'s own deposited RCSB primary citation is
**Mathieu et al., "KRAS G12C fragment screening renders new binding
pockets," *Small GTPases* 13:225–238 (2022), PMID 34558391, DOI
10.1080/21541248.2021.1979360.** Fetched the full text (PMC8923024): `7A1X`'s
ligand (Cpd1/QWB) occupies what the authors call the **"Switch I/II
pocket," also named the "Tyr71 pocket"** — and the paper states this is "a
known, previously described binding site for indole ligands," not novel to
this 2022 paper itself (which reports two OTHER, genuinely new pockets from
its own fragment screens, validated with a GEF functional assay — a
different, stronger claim than this task needed to establish for `7A1X`).
Their own described lining residues — Tyr71 (the namesake), Tyr64
(switch II), Thr35 (switch I) — line up directly with this register's own
computed footprint (71 exact match; 37/39 adjacent to Thr35; 74/75 adjacent
to Tyr71; 54–56 the interswitch region between). **This is a real,
recognized, published second druggable site, not a fragment-hit artefact
or a numbering error** — the Constraint's own failure mode did not occur.

**Numbering/chain artefact ruled out for KRAS specifically**, live: `8AZX`
(representative of the shared single-chain construct across all 10
ensemble members) is confirmed **monomeric** via RCSB's own assembly
record. Unlike GAC or FBPASE (both flagged below, real homo-oligomer
chain-letter ambiguity — [[TASK-0273]]'s own finding), a monomeric
construct has no symmetric copy for a residue to be mislabeled onto, so
KRAS's chain-exact and resnum-only Jaccard cannot diverge — the 0.00 is a
real site difference, confirmed structurally, not a labelling artefact.

### Per-protein architecture, every frozen-set protein with ≥2 holo structures

| protein | architecture | evidence |
|---|---|---|
| **KRAS_G12C** | **9:1 split** — Switch-II (9 drugs) vs. verified Switch I/II "Tyr71" pocket (1 drug) | [[TASK-0276]], this task |
| **HCV_NS5B** | **2:2 fully disjoint** — within-apo-pair Jaccard 0.882–1.000, across-pair **0.000** (4/4 pairs) | [[TASK-0276]], corroborated by [[TASK-0265]] |
| TRP_SYNTHASE | Nominally single-site (F6F vs. F19 Jaccard 0.833) — but a real bifunctional enzyme: F6F alone shows internal alpha-vs-beta-site heterogeneity (some same-drug pairs at Jaccard 0.000) when scored against its own 13-structure replicate ensemble | [[TASK-0265]], [[TASK-0273]] |
| GAC | Single-site once corrected for a real homo-oligomer chain-letter artefact (chain-exact Jaccard 0.00, resnum-only 0.75–0.82) | [[TASK-0265]], [[TASK-0273]] |
| KSHV_PROTEASE | Single-site (Jaccard 0.750) | [[TASK-0265]] |
| PKR | Single-site (Jaccard 0.769) | [[TASK-0265]] |
| FBPASE | **Ambiguous, not cleanly resolved** — resnum-only Jaccard 0.400 (moderate, neither clearly same nor disjoint), same chain-letter-artefact risk flagged as GAC but not chased further here | [[TASK-0265]] |

**3 of 7 proteins show genuine multi-site character** (KRAS, HCV_NS5B,
TRP_SYNTHASE), one is ambiguous (FBPASE), three are single-site. This is
**direct structural evidence**, not a database lookup — a materially
stronger empirical base than [[TASK-0229.003]]'s own ASD-lookup test (1 of
4 targets, BCR_ABL1). H6.2's own register entry updated accordingly (see
`.claude/hypotheses/reference_register.md`).

**Compounds [[TASK-0265]]'s own conclusion, more strongly than that task
could show on its own**: if a third of the frozen set's proteins have more
than one real, chemically-distinct allosteric site, "the allosteric pocket
of protein X" is not a well-defined single object for several of this
register's own targets — and this benchmark, throughout, assigns exactly
one.

**Submission paragraph, drafted for [[TASK-0184]]** (not inserted into that
document here — that task owns it):

> Structural clustering of independently-solved holo depositions shows that
> "the allosteric site" is not always a single, well-defined object. KRAS
> G12C splits 9:1 across our own ten-drug ensemble — nine inhibitors share
> the well-known Switch-II pocket, but one (Cpd1, a published fragment hit,
> Mathieu et al. 2022) occupies a distinct, independently-verified
> "Switch I/II" pocket with zero residue overlap. HCV NS5B is more extreme:
> its four inhibitors split 2:2 across two fully disjoint sites (Jaccard
> 0.000 between groups). Three of seven frozen-set proteins checked show
> this kind of genuine multi-site architecture. Since our own benchmark
> assigns exactly one ground-truth pocket per target, this is direct,
> structural evidence for effector-specific allostery (H6.2) — and a real
> source of label ambiguity our own published AUC numbers inherit, not just
> a theoretical concern.

**Script:** `scripts/task0280_multi_site_architecture.py`. **Data:**
`results/tasks/0280_multi_site_architecture/architecture_verification.json`.
**Full detail:** `.ai/tasks/DONE/TASK-0280-multi-site-architecture-and-the-second-kras-site.md`.

## Pocket-level top-5 is numerically higher than residue-ranking but not statistically distinguishable from random pocket selection — the winning rule collapses to "druggability alone, minus the active site itself", and the Reviewer's own in-sample refinement does not survive LOTO ([[TASK-0282]], 2026-08-28)

The §5 deliverable asks for the top 5 predicted allosteric **sites**; the
pipeline ranks all N residues and takes the top 5, which is a harder problem
than the one posed. Two numbers for this baseline, disclosed rather than
silently reconciled: this task's own Why section cites the deployed
pipeline's own P@5 as **0.0 / 0.2 / 0.0** (BCR_ABL1/KRAS_G12C/
CARDIAC_MYOSIN, Reviewer, 2026-08-27); an independent recompute here under
this exact task family's own established single GAUGE operator (H_new /
converged incoherent CTQW, [[TASK-0242]]'s own fixed pre-registered choice,
the same operator `CTQW-in-wrapper` below uses) gives **0.0 / 0.0 / 0.0** on
the identical 3 targets — the deployed backend evidently selects a
different Hamiltonian gauge than this family's own simpler fixed one on
KRAS_G12C specifically. **The task file's own cited numbers are used for
the mandatory-3 residue-ranking column below** (they are what the
deliverable actually ships), with this discrepancy flagged rather than
smoothed over; the frozen-20 column has no such citation to reuse and is
this task's own GAUGE-operator recompute, labelled as such. Swept
the alternative Bartosz proposed instead — choose a **pocket** by
druggability and distance (reusing [[TASK-0242]]/[[TASK-0249]]'s two-stage
apparatus wholesale: fpocket candidates on apo, distality filter, rank
within the candidate set), score with expected hits = overlap/pocket_size
(the analytic value of a random 5-residue draw from the chosen candidate,
no Monte-Carlo noise) — under **leave-one-target-out over [[TASK-0243]]'s
frozen 20** (61 configurations of {distance metric x exclusion cutoff x
combination rule} — 4 pre-registered combination families x 10
(metric,cutoff) pairs, plus a probe-informed 5th family with its own small
bin-width grid, see below — chosen on N-1, scored on the held-out target,
never in-sample), plus a genuine out-of-sample check on the 3 mandatory
targets (never in the LOTO training corpus at all).

**Mid-run collision, handled, not smoothed over**: TASK-0282 was filed and
claimed while a Reviewer probe (`task0282_prior_lexicographic_probe.py`)
found, in-sample on the 3 mandatory targets, that reordering the
lexicographic rule — **nearest surviving distance stratum first**,
druggability only as a tiebreak, the opposite of this task's own original
"most-distal-first" reading of "categorise then rank" — recovers KRAS's true
pocket exactly at its oracle ceiling (EH 0.80, druggability 0.001, the exact
pocket the pre-registered prior said no monotone function could select).
The probe's own explicit warning: that number is in-sample (28 configs on 3
targets) and "exactly the overfitting this task's Scope forbids." Folded in
as an added rule family (`lex_near_first`, attributed, dated) inside the
LOTO grid rather than adopted directly — LOTO still decides per fold, so
this does not reintroduce the overfitting the probe itself flagged.

**Result: it doesn't survive.** Every one of the 20 LOTO folds — and the
final fit on all 20 — independently selects the same rule:
**`MIN_HOP >= 1` (median 3.18 A, IQR 1.38-3.76 A — i.e. excludes only the
active site's own immediate contact shell) + rank surviving fpocket
candidates by druggability alone.** `lex_near_first` (the probe's own
family) never wins a single fold; on the full-20 fit its best configuration
ties for 4th place (mean EH 0.1399) behind plain `drug_alone` at the
classic `MIN_HOP>=2` cutoff, itself edged out by the same rule at
`MIN_HOP>=1` (0.1649). The distance *metric* and *cutoff* barely move the
result once druggability is doing the ranking — the top 6 of 61 rules are
all within 0.04 of each other and are all `drug_alone`/`weighted_sum`
variants at a loose cutoff. Consistent with the probe's own hedge: its
finding was real but did not generalise past the 3 targets it was measured
on.

**Headline table** (expected hits out of 5, LOTO throughout for the frozen
20; the swept rule applied to the mandatory 3 is the frozen-20-fit rule,
never refit on them):

| target | group | residue-ranking | **swept rule (LOTO)** | CTQW-in-wrapper | random pocket | oracle ceiling |
|---|---|---|---|---|---|---|
| BCR_ABL1 | mandatory | 0.000 (cited) | **0.737** | 0.000 | 0.051 | 0.737 |
| KRAS_G12C | mandatory | **0.200** (cited; GAUGE recompute: 0.000) | 0.071 | 0.071 | 0.109 | 0.800 |
| CARDIAC_MYOSIN | mandatory | 0.000 (cited) | **0.000** | 0.000 | 0.028 | 0.279 |
| **mean, mandatory 3** | | 0.067 | **0.269** | 0.024 | 0.063 | 0.605 |
| **mean, frozen 20** (GAUGE recompute, no citation exists) | | 0.010 | **0.122** | 0.064 | 0.038 | 0.510 |
| **median, frozen 20** | | 0.000 | **0.000** | 0.000 | 0.038 | 0.472 |

**Read the median row before the mean row.** The swept rule scores **exactly
0.000 on 13 of 20 frozen targets** and beats random pocket selection on only
**7 of 20**; its frozen-20 mean of 0.122 is carried by three targets
(`GAC_CPD12` 0.833, `SMYD3_DIPERODON` 0.500, `KSHV_PROTEASE_24Q` 0.444). It
captures **24% of the oracle ceiling**. A reader taking 0.122 vs. random's
0.038 as a 3x improvement would be reading a mean whose median is zero.

**Nothing here is statistically significant**, including against random:
swept vs. residue-ranking p=0.125, vs. CTQW-in-wrapper p=0.375, **vs. random
pocket selection p=0.247** (cluster-robust, [[TASK-0261]]'s exact
cluster-level permutation, 13 clusters). The correct summary is therefore
*"numerically higher, not distinguishable from chance pocket selection"*, not
*"beats"* — the section title was corrected accordingly (Reviewer,
2026-08-28).

**One structure does survive**, and it is the informative part: by site
category ([[TASK-0258]]), swept mean EH is **proximal 0.295** (n=5),
**contact-adjacent 0.088** (n=11), **intermediate 0.000** (n=4). The rule
works where sites are moderately separated and fails completely on the
genuinely distal ones — the same geometry-dependence every other line of this
register has converged on.

**What is reportable for the submission is the CEILING, not the rule.** The
oracle averages **0.510** across the frozen 20 against residue-ranking's
**0.010**. That gap is real and needs no fitting. But no rule selected without
seeing the label reaches it: the best LOTO-selected member gets 0.122, is
indistinguishable from random, and scores zero on 13 of 20 targets. Reaching
the ceiling from apo is unsolved, and that is the Phase 2 problem statement
stated in numbers.

**KRAS_G12C is the one target where residue-ranking wins**, on the task
file's own cited number (0.200 vs. swept's 0.071) — the swept rule's
aggregate lead over residue-ranking is carried entirely by BCR-ABL1, not a
uniform win. Reported plainly: 1 win (BCR_ABL1, by a wide margin), 1 loss
(KRAS_G12C), 1 tie-at-zero (CARDIAC_MYOSIN) on the mandatory 3, not "beats
residue-ranking on all three."

(Full 20-row frozen-set table, per-target LOTO rule, and the 61-rule sweep
are in the JSON below — every result carries its own oracle ceiling next to
it, per this task's own Constraint; e.g. CARDIAC_MYOSIN's swept 0.000 sits
under an oracle of only 0.279, not 1.0 — a genuinely hard target, not a
failed method.)

**Cluster-robust significance** ([[TASK-0261]]'s exact 13-cluster sign-flip,
frozen 20): swept vs. residue-ranking p=0.125 (largest, most consistent
effect of the three, still short of the conventional 0.05 bar — with only
13 clusters the test's own finest resolution is ~0.0002, so this is real
signal, not noise-shaped, but not independently decisive at this cluster
count); swept vs. CTQW-wrapper p=0.375; swept vs. random p=0.247. Read
plainly, per this task's own Constraint: **the swept rule beats
CTQW-in-wrapper in raw mean (0.122 vs 0.064 frozen-20, 0.269 vs 0.024
mandatory) largely because CTQW-in-wrapper is close to uninformative here**
(consistent with [[TASK-0242]]/[[TASK-0249]]'s own CTQW MRR 0.161 vs
fpocket's 0.344, and [[TASK-0263]]'s added-last p=0.973) — "outperforms
CTQW" and "works" are different claims, and only the residue-ranking
comparison (0/5 -> real, non-zero hits on 7/20 frozen-set targets and 2/3
mandatory) is close to the second one.

**Site-category covariate** ([[TASK-0258]]'s taxonomy, the probe's own
recommendation, tested at n=23 rather than inferred from 3): proximal
(4.5-12 A, n=7) mean swept EH 0.316; contact-adjacent (n=12) 0.086;
intermediate (12-20 A, n=4) 0.000. Directionally consistent with "closer,
already-separated pockets are easiest," but **not clean** — CARDIAC_MYOSIN
and BCR_ABL1 are both "proximal" and score 0.000 vs. 0.737 respectively, so
category alone does not determine success; reported honestly, not smoothed
into a tidier story than the data supports.

**Pre-registered prior verdict: HOLDS**, on the actual LOTO-selected general
rule, not just the probe's own targeted in-sample construction — BCR_ABL1
0.737, KRAS_G12C 0.071, CARDIAC_MYOSIN 0.000. The rule works where the
pocket is already open (BCR-ABL1's, held open by myristic acid,
[[TASK-0278]]) and fails where druggability itself carries no signal
(KRAS_G12C, CARDIAC_MYOSIN, both true-pocket druggability ~0.001) — a fifth
independent route to this register's own recurring finding, not a new one.

**Recommendation to [[TASK-0184]]**: report **both** numbers for the top-5
deliverable, not a silent switch. The swept pocket rule is a large
improvement in aggregate mean (0.067 -> 0.269 on the mandatory 3, 0.010 ->
0.122 on the frozen 20) using only apparatus already in the codebase
(fpocket + a trivial active-site exclusion), driven overwhelmingly by
BCR-ABL1 (0/5 -> 3.5/5) and 7/20 frozen-set targets going from zero to
non-zero — **not a uniform win**: it underperforms the deployed pipeline's
own cited number on KRAS_G12C specifically (0.071 vs 0.200), so the correct
framing for §5 is "a strong pocket-level candidate for some targets," not
"a strictly better method." The improvement is not cluster-robustly
significant at n=13 and the achievable ceiling itself is only 0.8/0.7/0.3 —
state the ceiling beside the number wherever it is quoted, and do not claim
the pocket-level method "solves" the deliverable.

**Script:** `scripts/task0282_pocket_selection_sweep.py` (+ the Reviewer's
own probe, `scripts/task0282_prior_lexicographic_probe.py`, motivation
only, not a result). **Data:**
`results/tasks/0282_pocket_level_top5_distance_druggability_sweep/pocket_selection_sweep.json`.
**Full detail:** `.ai/tasks/DONE/TASK-0282-pocket-level-top5-distance-druggability-sweep.md`.

## Dockerizing the vendored external tools -- fpocket/EvoEF2/P2Rank containerized, PocketMiner validated ([[TASK-0285]], 2026-08-28)

Filed and completed same-session, per Bartosz's own direct request. This
register has four vendored external tools, each installed a different,
host-dependent way. [[TASK-0206]] already caught a real, on-record
cross-machine reproducibility bug for one of them (fpocket: two machines'
own hand-compiled binaries produced different AUCs on the same three
targets); [[TASK-0268]] hit an installability wall a third way
(`frustratometer`'s own missing system LLVM). [[TASK-0269]] had already
proven Docker was the fix for exactly this class of problem (PocketMiner).
This task generalizes that fix to the other three.

**The wrapper pattern, one design, zero call-site changes**:
`tools/{fpocket/bin/fpocket, evoef2/EvoEF2, p2rank/p2rank_2.5.1/prank}`
are now small Python scripts, not binaries, at the *exact* paths
`FPOCKET_BIN`/`EVOEF2_BIN`/`P2RANK_BIN` already pointed to across 12
existing call sites — every one works unmodified. fpocket/P2Rank mount
this repo's own root plus the system temp root 1:1 (no argument
rewriting needed, since every real caller stages I/O under
`tempfile.TemporaryDirectory()`). EvoEF2 preserves a confirmed,
load-bearing quirk (`argv[0]` must be a short relative path or the binary
SIGSEGVs) by having the container exec through a relative symlink
deliberately NOT named `EvoEF2` — that name is the wrapper's own path
inside the same live bind mount, and would overwrite itself.

**A real near-miss, caught before shipping**: the first draft overwrote
the shared, gitignored native `fpocket` binary before the Docker image
had been validated — other concurrent threads could have been calling it
mid-build. Fixed by backing up the native binary first for every
subsequent tool, before replacement, every time.

**All base images pinned by digest, not just tag — load-bearing, not
cosmetic.** The first fpocket build (tag-only pin) produced a **third**,
still-different AUC set from either number already in
`tools/fpocket/PROVENANCE.json`: BCR_ABL1 0.8596/CARDIAC_MYOSIN 0.5345 —
matching [[TASK-0163]]'s own ORIGINAL (superseded) numbers, not
[[TASK-0206]]'s own re-verified native-rebuild numbers (0.8618/0.5303),
on the identical source tag. Real, decisive evidence that Docker alone
does not fix this reproducibility class of bug without a digest pin —
all three AUC sets kept on record, none silently preferred. (KRAS_G12C's
own AUC is no longer a valid comparison point at all — [[TASK-0270]]'s
apo swap changed the input structure independent of the fpocket
question.)

**EvoEF2 — a clean positive, by contrast.** `GreedyRepack` on the
identical real input (KRAS_G12C, `4LDJ`), native macOS binary vs. this
image's own Linux/amd64 binary: **byte-identical output** (107,203 bytes,
both arms). First provenance record for this tool.

**Real end-to-end verification, every tool, on a real target (`4LDJ`),
through the unmodified real calling code**: fpocket 9 real pockets
(druggability 0.682, 18 residues); EvoEF2 `GreedyRepack` real
107,203-byte structure; P2Rank 170 real per-residue probability rows;
PocketMiner (existing image, not rebuilt) real inference,
`n_residues=170, mean=0.4902` — confirmed still functional, not assumed.

**Not done**: a from-scratch multi-machine rebuild test of the
now-digest-pinned fpocket recipe (does it converge to a stable fourth
value, or reproduce one of the three already on record) — a real, flagged
follow-up. `frustratometer` not revisited (a different class of gap — an
already-working from-scratch port exists, per [[TASK-0268]]).

**Files:** `tools/{fpocket,evoef2,p2rank}/Dockerfile` (new),
`tools/fpocket/bin/fpocket`, `tools/evoef2/EvoEF2`,
`tools/p2rank/p2rank_2.5.1/prank` (wrapper scripts, replacing the native
binaries in place), `tools/evoef2/PROVENANCE.json` (new),
`tools/fpocket/PROVENANCE.json` (containerized-build entry added), all
three `.gitignore`s updated to track the new recipe files, all three
`README.md`s updated. **Full detail:**
`.ai/tasks/DONE/TASK-0285-dockerize-vendored-agentic-tools.md`.
## KRAS_G12C's shipped hit list was stale, not a different operator — regenerated, and all three mandatory targets now genuinely score 0/5 ([[TASK-0283]], 2026-08-28)

[[TASK-0282]] flagged, without resolving, that its own residue-ranking
recompute (P@5=0.000 on KRAS_G12C, under this task family's single
pre-registered GAUGE operator) disagreed with this task's own citation of
the shipped `results/KRAS_G12C/hit_list.json` (P@5=0.200). Traced the real
`run_challenge.py` code path — not inferred from the numbers — to settle it.

**Not an operator disagreement.** For all 3 mandatory (ground-truth)
targets, `run_frozen_verdict`/`select_frozen_config` picks among exactly 2
candidates (`H_new_default`, `H10_disorder_suppressed`) via a label-free
score; `_winner_index=0` (`H_new_default`) for all three — the identical
operator this whole task family already uses as its own fixed GAUGE.
`assemble_hit_list` does deliberately exclude active-site/seed residues
before ranking (`report.py`'s own documented design, "so a trivial
self-hit never appears in the list") — a real difference from this task
family's own simpler `precision_at_k(ctqw_full, pocket, k=5)` convention
(also used by `apo_structure_sensitivity_sweep.run_one`, so this is a
second place carrying the same simplification) — but reproducing that
exclusion alone still gives P@5=0.000 on KRAS_G12C, not 0.200. It does not
explain the gap.

**The real cause: a stale deliverable, six days out of date.**
`results/KRAS_G12C/{hit_list,verdict}.json` and both `.npz` connectivity
matrices were generated 2026-08-20 (`4917e17`, TASK-0225) against
`apo_pdb: 4OBE` — the wild-type structure [[TASK-0270]] (2026-08-26) found
was never the G12C mutant at all, and replaced with `4LDJ` in
`config/targets.yaml`. TASK-0270 re-scored the AUC/diagnosis in its own
task-scoped analysis (0.557->0.514, `NO_FAILURE_DETECTED`-
>`NO_SIGNAL_IN_APO`) but never regenerated the shared `results/KRAS_G12C/`
deliverable directory `run_challenge.py` actually writes and Sec.5 quotes
from — a real propagation gap the fix itself left behind, the same class
of defect TASK-0270 itself was filed to catch. Confirmed directly: the
`0.200` hit `results/KRAS_G12C/hit_list.json` reports (resnum 60) traces
to a 169-residue structure; `4LDJ` is 170 residues — the connectivity
matrix shapes disagreed (169x169 vs 170x170) before either JSON was even
read, an unambiguous structural fingerprint, not a numerical coincidence.
`results/RESULTS.md`'s own auto-appended log independently confirms it —
its KRAS_G12C entry read "*From 4OBE alone we predict...*" by name.

**BCR_ABL1 and CARDIAC_MYOSIN are NOT stale** — their `targets.yaml`
entries have not changed since 2026-08-20 (git history checked, not
assumed), and re-running `run_challenge.py` fresh reproduces their shipped
`hit_list.json`/`verdict.json` **byte-for-byte** (identical resnums,
scores, diagnosis, AUC) — confirmed, not inferred from "nothing looks
different."

**Fixed, not just diagnosed**: re-ran `run_challenge.py --target KRAS_G12C`
against the current (correct) config and overwrote the stale deliverables
in place (`hit_list.json`, `verdict.json`, both `.npz` matrices,
`report.txt`, `end_to_end.json`) — `results/RESULTS.md` auto-appended its
own new, correctly-named `4LDJ` block alongside the stale `4OBE` one (left
in place; historical, not deleted).

**Corrected numbers, old vs. new, TASK-0270's own reporting format**:

| target | P@5 (residue, old) | P@5 (new) | diagnosis (old -> new) | AUC (old -> new) |
|---|---|---|---|---|
| KRAS_G12C | 0.200 (**stale, 4OBE**) | **0.000** | NO_FAILURE_DETECTED -> NO_SIGNAL_IN_APO | 0.557 -> 0.514 |
| BCR_ABL1 | 0.000 | 0.000 (confirmed) | NO_SIGNAL_IN_APO (unchanged) | 0.541 (unchanged) |
| CARDIAC_MYOSIN | 0.000 | 0.000 (confirmed) | NO_SIGNAL_IN_APO (unchanged) | 0.548 (unchanged) |

**All three mandatory targets now genuinely score P@5 = 0/5** on the
deployed operator. Note: `sites.site_hit_metrics`' own coarser,
distance-based `hit_at_1` (TASK-0180's clustered-site criterion, a
different metric from residue-level P@5) registers `True` for KRAS_G12C's
top cluster even now — both numbers are real and both are reported;
neither should be quoted as "P@5" for the other.

**Matrix/hit-list operator agreement, for the record**: for all 3
mandatory targets, the connectivity matrix and the hit list are built from
the *same* winning `H`/eigendecomposition (`run_challenge.py:441-450`) —
they agree by construction. This is **not** true for no-ground-truth
targets (e.g. MYC_MAX): there, the matrix uses the single
`H_new`-with-highest-cross-operator-agreement while the hit list is a
genuine 4-operator consensus ranking — a real, deliberate, already-code-
documented asymmetry, flagged here so [[TASK-0184]]'s methodological
report states it rather than implying one uniform operator throughout.

**One number of record per mandatory target, with provenance, for
[[TASK-0184]]**: BCR_ABL1 P@5=0.000 (H_new, `apo=1OPL`, unchanged since
2026-08-20); KRAS_G12C P@5=0.000 (H_new, `apo=4LDJ`, corrected
2026-08-28, supersedes the stale 0.200); CARDIAC_MYOSIN P@5=0.000 (H_new,
`apo=8QYP`, unchanged since 2026-08-20). **All three mandatory targets: 0
hits in fifteen.** Per this task's own Constraint, that is what the
submission says — not the favourable number.

**Script:** `scripts/run_challenge.py` (unmodified; re-run only). **Data:**
`results/KRAS_G12C/{hit_list,verdict}.json` (updated in place),
`results/RESULTS.md` (appended). **Full detail:**
`.ai/tasks/DONE/TASK-0283-shipped-backend-and-research-pipeline-disagree.md`.

## Two structurally distinct populations of allosteric site — and nothing we measured, including domain architecture, predicts which a protein has ([[TASK-0284]], 2026-08-28)

Reviewer-filed Finding A/B independently reproduced as committed code
(`scripts/task0284_bimodality_and_nulls.py`), and Part B's own
pre-registered domain-architecture test run for the first time
(`scripts/task0284_domain_architecture.py`).

**Finding A, reproduced exactly.** 1D k-means (k=2) on min heavy-atom
distance from pocket to active site, across 33 scoreable targets
([[TASK-0258]]'s own measure, re-run fresh against live config, not its
possibly-stale stored artifact): **silhouette 0.737**. **Near cluster:
n=24, 1.29–8.33 Å. Far cluster: n=9, 11.24–19.72 Å. Gap: 2.91 Å** with
nothing in it. Shapiro-Wilk on log(min_A): **p=0.0020** — one lognormal
continuum is rejected. Every number matches the filed finding bit-for-bit.
Re-expressed against [[TASK-0258]]'s own bin edges (min_A≥12.0 Å → far)
side by side, per this task's own Scope: **n_far=5** there vs **n_far=9**
data-derived — the 4-target gap is CARDIAC_MYOSIN (11.81 Å, inside the
data-derived far cluster, outside the old ≥12 Å bin) plus PTP1B/
PKR_MITAPIVAT/PKR_AG946.

**Finding B, independently recomputed.** Eight standard descriptors
(N, Rg, compactness, helix/sheet fraction, GNM λ₁, contact order, mean
degree) against min_A (Spearman) and near-vs-far (Mann-Whitney), both
splits. **Nothing survives Bonferroni (α=0.05/8=0.00625):**

| property | rho vs min_A | p (Spearman) | p (Mann-Whitney, data-split) |
|---|---|---|---|
| N (chain length) | +0.317 | 0.072 | 0.045 |
| Rg | +0.232 | 0.193 | 0.284 |
| compactness (Rg/N^⅓) | −0.021 | 0.910 | 0.505 |
| helix fraction | +0.028 | 0.879 | 0.284 |
| sheet fraction | +0.067 | 0.709 | 0.887 |
| GNM λ₁ (global stiffness) | −0.041 | 0.821 | 0.952 |
| contact order | −0.097 | 0.592 | 0.984 |
| mean degree (packing) | +0.059 | 0.744 | 0.176 |

N/Rg/compactness/mean_degree reproduce the filed rho values to 3 decimal
places; helix/sheet/λ₁ diverge in magnitude (λ₁ also in sign) from the
filed numbers — expected: this environment has **no DSSP binary and no
biotite** (checked directly: `mkdssp`/`dssp` absent from PATH, a pinned
`pip install biotite==0.41.0` fails to build against numpy 2.5/python3.13,
an unpinned install hung resolving dependencies and was killed), so
helix/sheet fraction here is a coarser ProDy `calcPhi`/`calcPsi`
Ramachandran-region classifier, not DSSP. **The substantive conclusion is
identical either way: none of the eight survive correction**, under
either computation.

**Part B: domain architecture — tested for the first time, and it fails,
but only after a coverage-gap false positive was caught.** Source: RCSB
Data API's own Pfam feature per polymer entity, verified live (4LDJ/KRAS
checked directly before trusting the resnum-mapping arithmetic at scale).
CATH was tried first and abandoned — `cathdb.info`'s REST API 404s on a
2024+ deposition (8QYP), its release lags recent PDB entries.

A first pass resolved 24/33 targets and reported **HOLDS at p=0.0184** —
but the 9 unresolved were not random: **all 4 HCV_NS5B rows**, the far
cluster's single largest subgroup, dropped because RCSB's own bundled
Pfam feature list is empty for that entity (also TEM-1 beta-lactamase,
HIV-1 RT, and others). Confirmed live as a genuine RCSB coverage gap, not
a request bug — InterPro's own Pfam-by-UniProt endpoint finds "Viral RNA
dependent RNA polymerase" for HCV NS5B's UniProt P26663 without trouble.
Fixed with an InterPro-by-SIFTS-UniProt fallback plus correct
`auth_asym_id`→`label_asym_id` resolution (4DEM's entity has
`auth_asym_id="F"` but `label_asym_id="A"` — a same-string guess 404s on
the instance endpoint). Resolution went to **32/33** (only `SUMO_E1_FHJ`
stays unresolved — its active site/pocket span the SAE1/UBA2 heterodimer
interface in a way neither Pfam source fully annotates for that chain).

**With the gap fixed, the result flips: FAILS.**

| | cross-domain | same-domain |
|---|---|---|
| far-cluster (n=9) | 3 | 6 |
| near-cluster (n=23) | 2 | 21 |

Fisher exact: odds ratio 5.25, **p=0.1206** (two-sided and one-sided
far→cross alike). Direction agrees with the pre-registered prediction
(33% of far-cluster targets cross-domain vs 9% of near-cluster) but does
not clear significance at this n. The far cluster's own same-domain
majority is driven mainly by HCV_NS5B (4 of 6): its allosteric thumb/palm
site sits inside the SAME "Viral RNA dependent RNA polymerase" Pfam
domain as the active site, 17.9–19.7 Å away in 3D regardless. The near
cluster's two cross-domain counter-examples are HIV1_RT (seed in RNase H,
pocket in the polymerase domain) and GLUCOKINASE (the classic bilobed
Hexokinase_1/Hexokinase_2 fold).

Caveat stated, not hidden: Pfam domains are sequence-family boundaries,
coarser than a structural-domain parser for large multi-lobed proteins —
CARDIAC_MYOSIN's entire ~700-residue motor head is one Pfam entry
("Myosin_head") despite several real structural subdomains. A finer
structural parser might move some same-domain calls to cross-domain; not
chased further — Part B was pre-registered as one source, one test.

**Verdict: the split is real (Finding A) and currently unexplained by
structure alone (Finding B + Part B).** Size, shape, secondary structure,
GNM stiffness, fold topology, packing density, and now Pfam domain
architecture are all silent or non-significant. The remaining candidates
are non-structural: ligand chemotype ([[TASK-0265]]) or functional/
evolutionary history, neither recoverable from an apo backbone.

**Script/data**: `scripts/task0284_bimodality_and_nulls.py`,
`scripts/task0284_domain_architecture.py`; `results/tasks/
0284_two_populations/{bimodality_and_nulls,domain_architecture}.json`.
Full detail: [[TASK-0284]].
