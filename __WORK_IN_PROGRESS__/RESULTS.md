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
- Propagator choice on the *same* H_new operator (CTQW vs heat): gap
  −0.206. `_diagnosis` is computed only from CTQW's occupation vector
  (`run_frozen_verdict` passes `qvc["ctqw"]["occ"]` to
  `classify_failure`, never heat's) — so `NO_SIGNAL_IN_APO` is a
  statement about CTQW specifically, not about BCR_ABL1 as a target.

Precise summary: *on BCR_ABL1's optimized apo operator, classical heat
diffusion produces a real, floor-beating signal while the coherent
quantum walk does not.*

**[HYPOTHESIS — testing, TASK-0091]** This is not already explained by
this repo's existing "coherence adds ~nothing" finding
(`test_kras_g12c_dephasing_flat_survives_kappa_calibration`) — that
result is CTQW vs. *progressively dephased* CTQW (Haken-Strobl,
`gamma: 0 -> large`) on KRAS_G12C. This finding is CTQW vs.
`propagators.heat` — a different classical diffusion process
(`exp(-Ht)`), not proven equivalent anywhere in this codebase to the
`gamma -> large` limit of Haken-Strobl dephasing, on a different target.
**KRAS's flat-sweep result does not predict what a calibrated dephasing
sweep would show for BCR_ABL1.** Testable hypothesis: if AUC rises from
~0.525 toward ~0.731 as `gamma` increases through a calibrated range and
plateaus, that supports PLAN.md's own ENAQT hypothesis (coherent walks
localize on disordered graphs; calibrated dephasing reopens blocked
paths) as a real, target-specific effect worth pursuing. If AUC stays
flat, coherence isn't the lever here either and the KRAS pattern
generalizes. TASK-0091 runs this for real, reusing the KRAS test's exact
calibration recipe (`calibrate_kappa` → `mode_energetics` →
`gamma_scale`).

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

### CARDIAC_MYOSIN

| Quantity | Value |
|---|---|
| `AUC_apo_Hnew_default` / `_optimised` / `AUC_ctqw_mean` | 0.786 |
| `AUC_apo_H10_baseline` | 0.766 |
| `AUC_heat_mean` | 0.790 |
| `most_impactful_term` / `least_impactful_term` | V_B / V_M |
| `_diagnosis` | **`INSUFFICIENT_RESOLUTION`** |
| apo residue count (N) | **950** |

**[OBSERVED]** Unlike BCR_ABL1, CTQW and heat agree closely here
(0.786 vs 0.790, gap −0.003, "noise-level") — both propagators concur,
neither dominates. Hit-list resnums: 706, 89, 88, 704, 87 (two tight
pairs); no independent reference pocket set exists for this target to
cross-check against.

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

---

## Index of open questions from this run

| # | Question | Status | Task |
|---|---|---|---|
| 1 | Why does BCR_ABL1's classical heat kernel (0.731) outperform CTQW (0.525) on the identical operator — and does calibrated dephasing recover it? | untested | [[TASK-0091]] |
| 2 | What do the holo-side diagnostic numbers show for all three targets, and does the tiny apo/holo gap TASK-0067 found for the bare operator hold for the full `H_new` pipeline? | untested | [[TASK-0092]] |
| 3 | Which methodology difference (cutoff / pocket-label definition / source definition) explains KRAS_G12C's 0.779 vs. this repo's own previously-asserted 0.3–0.7 band? | open, but downgraded 2026-07-13 — no longer bears on whether KRAS shows real signal (it does not, either way; see TASK-0094) | [[TASK-0093]] |
| 4 | Does CARDIAC_MYOSIN's or KRAS_G12C's high AUC share a common cause beyond CARDIAC_MYOSIN's already-explained large-N flag? | **resolved 2026-07-13**: yes for KRAS (proximity, TASK-0094); CARDIAC_MYOSIN's floor-clearance is independent of KRAS's (it clears the proximity floor, its issue is purely the large-N flag) | [[TASK-0094]] |
| 5 | Does any mandatory target's apo-only AUC clear a real proximity floor (not just chance/degree)? | **resolved 2026-07-13: no — zero of three** (KRAS fails the floor, BCR_ABL1 fails chance, CARDIAC_MYOSIN's clearance is moot under the large-N flag) | [[TASK-0094]] |

Full process history, run mechanics, and Acceptance-Scenario checklists
for this run live in `.ai/tasks/DONE/TASK-0079.005-run-mandatory-targets.md`
(or `.ai/tasks/TODO/` if not yet closed — check `.ai/COMMON.md`'s registry
for current status). This document is the one to read for the science;
that one is the one to read for what was done and by whom.
