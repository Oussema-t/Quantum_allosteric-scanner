# Competence Map — TASK-0082

**The submission's central claim, per `EXECUTION_PLAN.md` Phase 5 item 5.2: "We close
X% of the gap knowing the answer would close, on these targets; ~0 on those, and here
is why." A per-target honest NO is a publishable result, not a failure to hide.**

This document synthesizes, per target: **floor** (the strongest trivial baseline the
score must beat — `baselines.degree_centrality`/`euclid_from_seed_centroid`/
`hop_from_seed`, [[TASK-0094]]), **ceiling** (the best AUC a 60-trial random search over
`H_new`'s entire physical-scalar space can reach *with the answer key in hand*,
[[TASK-0046]]), **actual** (the real, frozen-gated, blind-selected pipeline's headline
AUC, [[TASK-0079.005]]), and **headroom** (`(actual − floor) / (ceiling − floor)`, the
fraction of the floor-to-ceiling gap the actual pipeline closes) — for every mandatory
target, plus c-Myc's dedicated no-ground-truth row ([[TASK-0080]]).

**This document does not compute any of these numbers itself** (Out Of Scope, per this
task's own Intent Contract) — every value below is read from an already-real, already-
tested run and cited to its source. Where a number does not exist yet for a target (the
gated tasks below), that gap is stated explicitly, not filled with an estimate.

> **Caveat, added per this task's own Dependency section (2026-07-15,
> `REVIEW-2026-07-15`/`REVIEW-2026-07-15b`, filed the same day this document was first
> written): every number below is a bare point estimate with no confidence interval
> ([[TASK-0112]], open) — no floor-vs-score margin here should be read as a *decided*
> result yet, including the headline "ceiling below floor" finding for KRAS_G12C. That
> finding additionally rests on a 60-trial blind random search over an ~8-dimensional
> space, flagged as weak evidence for a *negative* claim specifically (though adequate
> for a positive one) ([[TASK-0116]], open), and on the same unvalidated
> `t_max=15`/`n_steps=500` every other headline AUC in this project already carries as an
> open question ([[TASK-0117]]/[[TASK-0108]]/[[TASK-0109]]/[[TASK-0110]], open). None of
> this retracts the numbers — it is the difference between "the strongest evidence
> currently gathered says X" and "X is settled." This document states both the finding
> and this caveat together, every time, per the reviewing thread's own explicit
> instruction not to present TASK-0046's number as final while these are open.**

---

## Mandatory targets — floor / ceiling / actual / headroom

| Target | Floor | Ceiling | Actual (AUC) | Diagnosis | Headroom |
|---|---|---|---|---|---|
| KRAS_G12C | 0.798 | 0.524 | 0.779 | `BEATS_CHANCE_NOT_FLOOR` | **undefined — ceiling < floor, see below** |
| BCR_ABL1 | 0.565 | 0.612 | 0.525 | `NO_SIGNAL_IN_APO` | **−85.5%** (actual is *below* its own floor) |
| CARDIAC_MYOSIN | 0.764 | 0.819 | 0.786 | `INSUFFICIENT_RESOLUTION` | 40.7% — **moot**, N=950 flag fires before the floor check matters |

All three columns are CTQW-propagated, `H_new`-family numbers throughout (floor,
ceiling, and actual all use `time_averaged_ctqw`, never a mix with
`ground_state_relaxation`/"heat") — apples-to-apples within each row. Sources:
- **Floor**: `RESULTS.md`'s TASK-0094 section (KRAS/CARDIAC_MYOSIN) and TASK-0106's Done
  section (BCR_ABL1, `0.565`) — real `euclid_from_seed_centroid`/`hop_from_seed`/
  `degree_centrality`, max of the three, same apo data/source/cutoff as Actual.
- **Ceiling**: `results_task0082/<target>/ceiling_trials.jsonl` (this task, 2026-07-15),
  60 real trials each, `ceiling.ceiling_search`/`ceiling_search_batched.py`, seed=7,
  `protocol.ceiling_context()`. KRAS_G12C: two independent real runs gave 0.5250
  ([[TASK-0046]]'s own cross-check) and 0.5239 (this task's checkpointed re-run) — a
  ~0.001 floating-point/BLAS-threading divergence between runs, not a methodology
  difference; both are reported, the table above uses the more recent checkpointed value.
- **Actual**: `results/<target>/verdict.json`'s `AUC_apo_Hnew_optimised`
  ([[TASK-0079.005]]'s real end-to-end run).
- **Diagnosis**: `RESULTS.md`'s post-TASK-0094 per-target sections (the authoritative,
  floor-aware verdict — not `verdict.json`'s own `_diagnosis` field, which predates
  TASK-0094's floor and is stale for KRAS_G12C specifically).

### KRAS_G12C — the ceiling itself does not clear the floor (currently the strongest evidence gathered, not yet a settled claim — see caveat above)

**This is the strongest form of "honest NO" this competence map can report, and it is
stronger than "the actual pipeline result is geometry" (TASK-0093's own finding) --
*if* it survives TASK-0116/TASK-0117 (open).** A 60-trial random search over the entire
`(lam_B, lam_T, lam_R, lam_C, lam_M, alpha, cutoff, n_low_modes)` space, scored against
the real labeled pocket with the answer key in hand the whole time, could not find *any*
point that beats a baseline which only knows Euclidean/graph distance from the seed.
`REVIEW-2026-07-15b` flags this specific claim as needing stronger search coverage
before a *negative* result can rest on it (60 draws over ~8 dimensions is sparse by any
space-filling standard, `TASK-0116`) and notes it shares `t_max=15`/`n_steps=500` with
every other unvalidated headline number in this project (`TASK-0117`). Neither finding
retracts the number — it is not yet a corrected or contradicted result — but this
section's claim should be read as "the best evidence gathered so far," not "proven."
`headroom`'s denominator
(`ceiling − floor = 0.524 − 0.798 = −0.274`) is negative — the formula is not merely
small here, it is meaningless, and reporting a computed fraction through it would be
worse than reporting nothing (see `.ai/memory/shared/pitfalls.md` P-0002, filed
alongside this document; a question about whether this finding should reshape the
floor/ceiling/headroom framing itself for this target is open to the Architect,
`.ai/memory/questions/architect-planner/open/Q-0003-...md`).

**What this does and does not license claiming**: it does not prove no operator family
could ever recover this pocket from apo topology — only that `H_new`'s own physical-
scalar space, under CTQW, cannot, at any point tested. It is consistent with, and
strengthens, `PLAN.md`'s own pre-existing qualitative finding ("optimized AUC_apo on
KRAS ~= 0.53, near chance even with the answer key") — this ceiling search independently
reproduces that number (0.524–0.525) via a different code path (this session's `ceiling.py`
port vs. whatever produced the original notebook-adjacent estimate) and additionally shows
the *entire* searched space clusters there, not just one default point.

### BCR_ABL1 — actual scores below its own floor

Headroom is a well-defined but negative fraction: the shipped pipeline's actual CTQW
result (0.525) is *worse* than the strongest trivial proximity baseline (0.565) for this
target — consistent with `NO_SIGNAL_IN_APO`. Unlike KRAS_G12C, the ceiling here (0.612)
*does* clear the floor, by a modest margin (+0.047) — so there is, in principle, real
headroom in this operator family for this target; the shipped default-parameter
configuration simply does not reach it. **Separately** (not part of this headroom
calculation, a different propagator entirely): `ground_state_relaxation` on the same
`H_new` operator scores 0.7315, clearing the same floor decisively (margin +0.166) — but
per [[TASK-0104]]'s already-corrected framing, that is a structural-prior/cryptic-pocket
signature (the well, not the coupling — [[TASK-0103]]'s dumbbell negative control), not
allosteric communication, and is not folded into this CTQW-based headroom row.

### CARDIAC_MYOSIN — the only positive headroom, invalidated before it can be read

40.7% headroom closure is the largest of the three mandatory targets — and is the one
number in this table that must not be read as a win. `classify_failure`'s own
`INSUFFICIENT_RESOLUTION` flag fires first (apo N=950 exceeds `LARGE_N_THRESHOLD`,
`diagnostics.py`'s own documented computational-scaling ceiling, not a claim the science
is invalid at this size) — the honesty pipeline catching its own stated limitation
automatically, on real data, exactly as designed ([[TASK-0079.005]] Finding 4). This
target's apo structure (5TBY) also carries its own independent, pre-existing data-quality
caveat in `config/targets.yaml` (20 Å cryo-EM IHM assembly). The 40.7% figure is reported
here for completeness, not endorsed.

---

## c-Myc / 1NKP — no ground truth (per [[TASK-0080]])

No floor, ceiling, actual, or headroom exists or is computed for this target — it has no
holo structure (`holo_pdb: null`) and no labeled allosteric pocket
(`allosteric_pocket_exists: false`), both by this target's own `config/targets.yaml`
status, not a scoring gap. Per this project's own convention, this absence is reported
explicitly rather than an empty row.

| Quantity | Value |
|---|---|
| Consensus top hit | residue 943, 3/4 independent operators agree (top-5) |
| Confidence | moderate — best cross-operator agreement is 3/4, not unanimous |
| Theoretical docking viability | unavailable — `fpocket` binary not installed in this environment |

Full narrative: `results_task0080/MYC_MAX/report.txt` (real run, 2026-07-15,
`run_challenge.py --target MYC_MAX`).

---

## Generalization targets (ASD, [[TASK-0081]])

Two targets, real network-gated runs, `config/targets.yaml`'s already-curated ASD
candidate pool (`TASK-0003`) — not the mandatory-set targets this session's ~15 prior
review cycles have already seen (per `REVIEW-2026-07-15`'s TASK-0115 finding: this is
the concrete mitigation for that repeated-exposure risk, not just bonus coverage). No
ceiling search run for either (out of TASK-0081's own scope; `ceiling_search_batched.py`
could extend to these targets cheaply if wanted later).

| Target | N | Pocket size | Actual AUC | Max floor | Diagnosis |
|---|---|---|---|---|---|
| PTP1B | 298 | 14 | **0.2497** (anti-correlated) | 0.4847 | `BEATS_CHANCE_NOT_FLOOR` |
| CASPASE7 | 461 | 7 | 0.7130 | 0.7565 | `BEATS_CHANCE_NOT_FLOOR` |

Neither clears its own floor — the same category as KRAS_G12C's mandatory-set result.
PTP1B is a genuinely distal allosteric site (~20 A from the catalytic residue, the
config's own `objective` field) and scores well below 0.5, not merely near it —
independent, cross-target corroboration of this project's central pattern (adjacent
pockets score artificially high via seed-proximity; distal pockets score at or below
chance) on a target none of this project's prior review history has examined. Full
selection rationale (including two ASD candidates that failed independent RCSB
verification and were not used) in `.ai/tasks/DONE/TASK-0081-generalization-set-asd-
targets.md`.

---

## Cross-target reading

No mandatory target in this table has a clean, floor-clearing, resolution-clean,
headroom-positive result:

- **KRAS_G12C**: ceiling itself fails to clear the floor — the strongest form of
  negative result this framework can express.
- **BCR_ABL1**: actual result is below its own floor; a real (if modest) ceiling-floor
  gap exists but is unclaimed by the shipped default configuration.
- **CARDIAC_MYOSIN**: the one positive-headroom number, invalidated by a resolution flag
  before the floor comparison is even meaningful.

Per `PLAN.md`'s own "gates before build" framing, this is the honest headline **as of the
evidence gathered 2026-07-15**: **`H_new` under CTQW propagation does not, on every real
evaluation run so far across all three mandatory targets and (for KRAS_G12C) the searched
parameter space, recover allosteric pocket information from apo topology beyond trivial
seed-proximity — and one target's only positive result is confounded by data resolution
before that question can even be asked.** This is consistent with, not contradicted by,
BCR_ABL1's separate `ground_state_relaxation` finding (0.7315, floor-clearing), which
[[TASK-0104]] already reframes as a structural-prior signature rather than a
communication signal. **This headline should not be presented as final in a submission
draft while TASK-0112/0116/0117 are open** (per the caveat at the top of this document) —
it is the strongest claim the current evidence supports, and the honest-NO framing this
project already practices means updating it without ceremony if stronger evidence
(bootstrap CIs, denser ceiling search, a validated `t_max`/`n_steps`) changes the picture.

---

## Open items

- **TASK-0112** (open): no confidence interval on any number in this document —
  `metrics.block_bootstrap_ci` exists and is used by `select.py`'s LOPO path but is not
  wired into any headline AUC this document cites. Every margin above (floor-vs-actual,
  floor-vs-ceiling) should be re-read with a CI once this lands.
- **TASK-0116** (open): KRAS_G12C's ceiling-below-floor finding rests on 60 blind random
  draws over an ~8-dimensional space — flagged as weak evidence for a *negative* claim
  specifically. A denser/space-filling search could still find a floor-clearing point
  this run missed.
- **TASK-0117** (open): the ceiling search (and every other headline AUC in this project)
  uses `t_max=15`/`n_steps=500` with no convergence check — depends on TASK-0108/0109/0110.
- **Q-0003** (`.ai/memory/questions/architect-planner/open/`): whether KRAS_G12C's
  ceiling-below-floor finding should change how the floor/ceiling/headroom framing itself
  is presented in the submission's central narrative — itself now also contingent on
  TASK-0116/0117's answers, not decidable from TASK-0046's current evidence alone.
- **TASK-0081**: generalization-set rows, not yet run.
- **TASK-0083** (result artifact contract, not yet started): this document is a plain
  markdown synthesis, not yet expressed in whatever versioned artifact shape TASK-0083
  eventually defines (GO/NO/UNSTABLE + knob-spread, per `EXECUTION_PLAN.md`'s own
  description of that task) — reconcile once TASK-0083 lands, per this task's own Open
  Question ("what document/artifact format... decide when TASK-0083 is scoped").
