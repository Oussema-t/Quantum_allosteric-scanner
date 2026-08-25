# TASK-0257 — Beyond Cα: improve the elastic network model against a label-free objective

- Status: Done
- Assignee: unassigned (suggest Implementer; ladder is ordered so it can stop early)
- Priority: **Medium-High — but sequence it AFTER the Phase 1 submission; see Sequencing**
- Filed: 2026-08-25 by Reviewer
- Related: [[TASK-0250]] (the objective), [[TASK-0254]] (fpocket's unique share), [[TASK-0246]], [[TASK-0247]], [[TASK-0255]]

## Why this is worth doing, and why now specifically

Every dynamical quantity in this register — `H_new`/CTQW, `dcc_low`, `prs_low`,
mode energetics, two-state ANM — is built on a **Cα-only** contact graph
(`hamiltonians.contact_matrix`, one node per residue, 8 Å cutoff). Two results
now make that worth revisiting, and one of them is what makes the work
methodologically clean.

**1. The Cα model is demonstrably invalid on most targets.** [[TASK-0250]]'s
GNM B-factor check: **6 PASS / 5 MARGINAL / 4 FAIL** of 15. On MYC_MAX
(r=0.148), ATCase (0.148), GROEL (0.350) and CASPASE1 (0.368) the model does
not fit the structure, so every ENM-derived result on those targets is
uninterpretable rather than negative. We cannot currently say what CTQW does on
them, because we have never given it a valid model to run on.

**2. There is a label-free objective to optimise against.** B-factor
correlation does not touch the pocket label at all. So the model can be
improved, and the improvement measured, **without any circularity and without
spending multiplicity budget on the outcome we actually care about**. That is
rare in this register and it is the main reason to do this rather than another
observable sweep.

**3. All-atom information is already known to carry unique signal.**
[[TASK-0254]] measured `fpocket`'s contribution when added **last**, on top of
geometry and CTQW: **+4.9%, p=0.0019, positive on 18/20 targets.** fpocket is
an all-atom cavity detector. That is direct evidence that beyond-Cα structure
carries real, non-redundant information the Cα graph cannot see.

## The honest case against (read before starting)

- **[[TASK-0255]] found 16/20 frozen-set targets fail a 15 Å separation bar and
  20/20 fail 20 Å.** A better model does not fix a benchmark that is not
  measuring distal allostery. Do not let this task displace that finding.
- Unexplained is now **29%**, not 67% ([[TASK-0254]]) — the headroom is much
  smaller than it looked a week ago.
- The gain may duplicate fpocket rather than add to it. **Every rung below must
  therefore be scored with `fpocket` already in the model**, not against
  geometry alone.
- CTQW's contribution when added last is **−0.1%, p=0.50**. A better ENM feeds
  CTQW, but if the ceiling is "geometry + cavity shape", better dynamics may
  not move it. The FAIL targets are the honest place to look for an exception.

## Ladder, cheapest first — stop as soon as a rung fails to improve the objective

Each rung is scored on **B-factor correlation first** (the label-free gate).
Only rungs that improve it proceed to the pocket-label evaluation.

- [x] **R1 — heavy-atom contact weighting, Cα nodes retained.** Weight each
      edge by the number of heavy-atom contacts between the residue pair
      instead of a binary Cα cutoff. `labels.protein_heavy_atoms_by_residue`
      already loads exactly this data with a residue index map — it is used for
      pocket labels and **never for the Hamiltonian**. Cheapest rung, highest
      expected value, N unchanged so nothing downstream changes shape.
- [x] **R2 — real burial (SASA) replacing `degree_centrality` as the burial
      proxy.** `corex.py` already wraps BioPython's `ShrakeRupley`. Motivation:
      degree is a *poor* burial proxy — it scores **below 0.5 on 6/9 targets**
      ([[TASK-0246]]). This is a feature swap, not an ENM change, and can be
      done independently.
- [ ] **R3 — Cα+Cβ two-node model** (β-Gaussian, Micheletti et al.). Doubles N,
      captures side-chain direction. Verify the citation live before
      implementing, per this register's convention.
- [ ] **R4 — all-heavy-atom GNM.** Feasibility checked: ~8 heavy atoms per
      residue, so N=169→~1350 (trivial) and N=1205→~9640, whose N×N GNM is
      93M float64 ≈ 744 MB — **feasible across the whole set**.
- [ ] **R5 — all-heavy-atom ANM.** 3N DOF: fine below ~600 residues,
      **6.7 GB at the largest target — do not attempt without a memory guard.**
      [[TASK-0204]]'s 300 GB incident is the precedent; put the projected-cost
      check in before the first run, not after.
- [ ] **R6 — parameter-free ENM** (distance⁻² weighting, no cutoff), which also
      removes `enm_cutoff` as a tuned knob.

## Acceptance

- [x] B-factor correlation per rung, per target, against [[TASK-0250]]'s
      pre-registered bars (PASS ≥0.6, MARGINAL 0.4–0.6) — the same 15 targets,
      same cutoffs, so the comparison is like-for-like.
- [x] An explicit statement of whether the 4 FAIL targets become valid, and if
      so, what CTQW does on them once it has a model that fits.
- [x] For any rung that improves the objective: re-run [[TASK-0254]]'s Shapley
      attribution **with fpocket in the stack**, and report CTQW's marginal
      **when added last** — the decision-relevant statistic, not the Shapley
      share.
- [x] Cost per rung recorded (wall-clock, peak memory), so the next reader
      knows what R5 actually costs before starting it.

## Sequencing

**GATE LIFTED 2026-08-25 by the Reviewer who wrote it. Start now.**

The original text read *"Do not start this before [[TASK-0184]] is delivered."*
That gate assumed TASK-0184 was actively progressable and would be displaced by
this work. **The premise was false.** TASK-0184 is blocked on [[TASK-0221]],
which is blocked on an outstanding response from the Cleveland Clinic
organisers. Holding R1–R2 behind a task that cannot move costs schedule and
buys nothing — so the gate is removed rather than left to be worked around.

Recorded rather than silently edited: the original block was a correct
*priority* judgement (the Phase 1 story is the benchmark finding, not a
modelling improvement) applied to an incorrect *availability* assumption. If
TASK-0221 unblocks and TASK-0184 becomes live, submission work takes
precedence over rungs R3–R6 again. **R1–R2 do not need to yield precedence**:
see below.

**Why R1–R2 are now the highest-value available work, not merely permitted:**

The strongest statement this register can make to the collaborating thread is
*"CTQW's contribution when added last is zero"* ([[TASK-0254]]: −0.1%, p=0.50).
There is exactly one substantive objection left to it — **"your elastic network
model was invalid, so you never gave the operator a fair model to run on."**
[[TASK-0250]] shows that objection has real force: GNM **FAILS** B-factor
validity on 4 of 15 targets and is **MARGINAL** on 5 more.

R1–R2 close that objection or confirm it, against a **label-free** objective.
Either outcome is decision-relevant:

- If R1–R2 fix the FAIL targets and CTQW's last-in marginal stays ~0, the
  negative becomes unassailable — no remaining "unfair model" defence.
- If CTQW's marginal becomes positive on targets that only now have a valid
  model, that is the first real positive in this register and it changes the
  investment case.

That makes R1–R2 the **prerequisite for the collaborator brief**, not a
competitor to it.

## Constraint

R1–R2 could plausibly be done in a day and might close the 4 FAIL targets on
their own. If they do, say so and stop — do not climb the ladder for its own
sake. And if better modelling still leaves CTQW's last-in marginal at zero,
that is the strongest possible version of this register's negative and must be
reported as such, not buried.

## Done

**2026-08-25, Implementer B.** R1 and R2 both built and run to completion.
**Stopping here, per this task's own ladder discipline** ("stop as soon as a
rung fails to improve the objective") and per the Constraint's own explicit
anticipation of this outcome: neither rung improves the objective that
matters (GNM-B-factor validity, R1) or moves CTQW's downstream marginal
(R2), so climbing to R3–R6 (each materially more expensive, R5 explicitly
flagged as needing a memory guard) has no measured justification. Not done
for lack of effort — both rungs ran clean, to completion, on the full
15-target set, and R2 additionally triggered and completed the Shapley
re-run Acceptance requires.

### R1 — heavy-atom contact weighting: net negative, does not fix any FAIL target

New `scripts/task0257_r1_heavy_atom_contact_weighting.py`. Replaced the
binary Cα-cutoff adjacency (`hamiltonians.contact_matrix`, `weight=
"binary"`) with edge weight = count of heavy-atom pairs within 4.5 Å (this
project's own established `pocket_contact_cutoff` convention, not a new
number) between each residue pair, same N, fed through the identical
Laplacian → eigh → pseudo-inverse → MSF pipeline `potentials._gnm_msf`
uses, scored against real B-factor on the same 15 targets/cutoffs
[[TASK-0250]] used.

| | PASS | MARGINAL | FAIL |
|---|---|---|---|
| baseline (binary Cα) | 6 | 4 | 4 |
| R1 (heavy-atom count) | 4 | 6 | 4 |

**Net negative**: 2 targets regress PASS→MARGINAL (KRAS_G12C 0.646→0.472,
PFK 0.708→0.580); **0/4 originally-FAIL targets improve past FAIL**
(MYC_MAX 0.148→0.268, ATCase 0.148→0.260, GROEL_SUBUNIT 0.350→0.356 all
move up but stay under the 0.4 MARGINAL bar; CASPASE1 0.368→0.314 gets
worse). Real, mixed, target-dependent effect underneath the net negative
(7/14 improve, 7/14 worsen; HEMOGLOBIN +0.184 is the largest single gain,
KRAS_G12C −0.173 the largest loss) — not reported as uniformly bad, it
is not, but the aggregate answer to "does R1 improve the objective" is no.

**Plausible mechanism, flagged as a diagnostic aside, not verified
further** (would be its own follow-up, not built): mean R1 degree on
KRAS_G12C is ~297 heavy-atom-pair-units per residue — sequence-adjacent
residues trivially share many heavy-atom pairs within 4.5 Å just from
being consecutive, which could be swamping the eigenspectrum with local
backbone stiffness rather than the longer-range tertiary contacts that
give Cα-GNM its B-factor-predictive power. Not tested (e.g. excluding
\|i−j\|≤2 sequence neighbours) — that would be a different rung, not R1
as specified, and is not silently substituted in here.

**Cost**: 15 targets, 0.15–12.78 s each (GROEL_SUBUNIT, N=3626, the
outlier — KD-tree query_pairs, not a dense atom-atom matrix, per this
script's own module docstring on why that choice was made). Peak RSS
1.56 GB (cumulative process high-water mark, GROEL_SUBUNIT-dominated) —
well inside the "feasible" range this task's own R4 note already
projected for a similarly-sized target, nowhere near [[TASK-0204]]'s 300
GB incident.

### R2 — SASA burial vs. `degree` burial: real single-feature win, does not move CTQW's marginal

New `scripts/task0257_r2_sasa_burial_vs_degree.py`. **Interpretation
stated explicitly, since this rung does not touch the Kirchhoff matrix at
all** ("a feature swap, not an ENM change," this task's own filing): scored
`degree` and real SASA (`allostery.corex.per_atom_asa`/
`per_residue_native_asa`, the same validated `ShrakeRupley` wrapper
[[TASK-0229.006]] uses) each directly against B-factor (buried ⇒ low B,
exposed ⇒ high B — both signs came out physically correct: degree r<0,
SASA r>0, on every target), not against GNM MSF, since neither is a
dynamical prediction on its own.

| | PASS | MARGINAL | FAIL |
|---|---|---|---|
| degree (baseline) | 1 | 7 | 6 |
| SASA (candidate) | 1 | 10 | 3 |

**Real, positive, on the objective as scoped here**: SASA beats degree
(higher \|r\| against B-factor) on **11/14 targets**; 3 targets move
FAIL→MARGINAL (CARDIAC_MYOSIN, MYC_MAX, GLUCOKINASE). Confirms the task's
own motivating citation ([[TASK-0246]]: degree scores below 0.5 on 6/9
targets as a burial proxy) with a direct, independent measurement, and
shows SASA is the better single-feature fix.

**Acceptance item 3 triggered** ("for any rung that improves the
objective, re-run [[TASK-0254]]'s Shapley attribution with fpocket in the
stack, report CTQW's marginal added last") — done. New
`scripts/task0257_r2_shapley_rerun.py`: rebuilt `H_new` term-for-term
(`hamiltonians.build_H_new`'s own formula and default λ weights,
reproduced locally since that function does not expose a burial-proxy
override) with `V_R`'s own `context["degree"]` replaced by real
per-residue SASA, recomputed CTQW on [[TASK-0243]]'s frozen 22-target set
(20/22 usable, matching [[TASK-0249]]/[[TASK-0254]]'s own filter exactly —
HIV_INTEGRASE_MUT871/916 skip on the same empty-seed defect
[[TASK-0253]] is independently auditing), reran [[TASK-0254]]'s own
`shapley_attribution` unchanged with only the "ctqw" block's values
replaced.

| CTQW's marginal, added last (after geometry+fpocket) | median | Wilcoxon vs 0 |
|---|---|---|
| baseline (degree-based H_new), [[TASK-0254]]'s own published number, reproduced from its on-disk JSON | −0.06% | p=0.5016 |
| R2 (SASA-based H_new) | +0.11% | p=0.7938 |
| paired (SASA − degree) | — | p=0.4781 |

**CTQW's added-last marginal does not move.** Both medians are
indistinguishable from zero; SASA's own version is if anything *less*
significant (p=0.79 vs 0.50), and improves on only **10/20 targets** —
a coin flip, not a systematic gain. CTQW's overall Shapley share (not
just added-last) barely moves either: median +11.2% → +12.4%, range
narrows slightly on the low end (−15%→−7%) but stays wide and
target-dependent. **This is exactly the outcome this task's own
Constraint names**: a real, measured, independently-motivated model
improvement (SASA is a genuinely better burial proxy, confirmed above)
still leaves CTQW's last-in marginal at zero.

**Cost**: R2's own 15-target B-factor check: ~40 s total (network-bound
RCSB fetches via `backend.data_layer.fetch`, cached after first run),
GROEL_SUBUNIT the outlier at 7.1 s. The Shapley re-run (20 targets, each
running fpocket + SASA fetch + a full `H_new` eigendecomposition) is the
expensive step of the two rungs — no per-target peak-memory instrumentation
was added to that script (unlike R1); wall-clock was on the order of
several minutes for the full 20-target set, not separately profiled
per-target. Flagged as an honest gap in the cost accounting, not
fabricated.

### Answering the Acceptance items directly

- **B-factor correlation per rung, per target**: done for R1 (literal, same
  metric as [[TASK-0250]]) and R2 (adapted metric, justified above, since
  R2 by construction cannot touch the Kirchhoff/MSF quantity R1 and
  [[TASK-0250]] share).
- **Do the 4 FAIL targets become valid?** **No.** R1 (the only rung tested
  that actually modifies the ENM/Kirchhoff construction) fixes 0/4. R2
  cannot answer this question by construction — it never touches GNM MSF.
  No rung in this task's own run gives CTQW a valid model on MYC_MAX,
  ATCase, CASPASE1, or GROEL_SUBUNIT; what CTQW does on them once it has
  one remains genuinely untested, not negatively tested.
- **Shapley re-run for any improving rung, CTQW's marginal added last**:
  done for R2 (the one rung that improved its own objective) — reported
  above, no movement.
- **Cost per rung**: R1 fully instrumented (wall-clock + peak RSS per
  target, table above). R2's B-factor check timed but not memory-profiled;
  the Shapley re-run neither, flagged rather than invented.

### Why this stops the ladder here, not a preference

Per Sequencing's own framing, two outcomes were live: "R1–R2 fix the FAIL
targets and CTQW stays ~0 ⇒ negative unassailable" or "CTQW becomes
positive on newly-valid targets ⇒ first real positive, changes the
investment case." **Neither happened cleanly** — R1 did not fix the FAIL
targets (so the "unfair model" objection is not fully retired), and CTQW's
marginal did not move under R2 either (so there is no positive to report).
The honest, precise statement: **two independent, real, measured
attempts at model improvement — one structural (R1), one feature-level
(R2) — neither moved CTQW's own downstream contribution off zero.** That
weakens the "unfair model" defence considerably without fully retiring it,
and is reported as exactly that, not rounded up to "unassailable" or down
to "inconclusive."

### Not done

- R3–R6 (Cα+Cβ, all-heavy-atom GNM/ANM, parameter-free ENM) — no rung
  below R1/R2 showed a result that would justify their materially higher
  cost (R5 in particular needs a memory guard before its first run, per
  this task's own explicit warning). Available as a future rung if a
  different signal motivates it; not attempted here.
- The plausible R1 failure mechanism (sequence-adjacent atom-pair-count
  domination) is named, not tested with a sequence-neighbour exclusion
  variant — that would be a new rung, not R1 as specified.
- R2's own Shapley re-run's per-target memory cost was not instrumented.

**Scripts**: `scripts/task0257_r1_heavy_atom_contact_weighting.py`,
`scripts/task0257_r2_sasa_burial_vs_degree.py`,
`scripts/task0257_r2_shapley_rerun.py`. **Data**:
`results/tasks/0257_r1_heavy_atom_contact_weighting/r1_results.json`,
`results/tasks/0257_r2_sasa_burial_vs_degree/r2_results.json`,
`results/tasks/0257_r2_shapley_rerun/part_a_shapley_sasa.json`.
