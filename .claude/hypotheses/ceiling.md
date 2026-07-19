# The Ceiling — Definition, Purpose, and How to Reach It

**Type:** Strategic gate — must be established before LOPO  
**Source:** Sonnet discussion thread (ceiling.txt), 2026-06-21  
**Related:** `physics.md` HYP-P4, HYP-P5, HYP-H13; `../improvements/hamiltonian_code.md` IMP-H7

---

## Definition (from the original discussion)

> "The ceiling is the in-sample optimum: full knowledge of the pocket, tune everything
> per protein, with a *strong* optimizer (not coordinate descent — you *want* to overfit
> here, so use the heaviest search you can, this is the one place leakage is the goal)."

**The ceiling is intentional overfitting.** It is NOT a cross-validated estimate of
generalization. It answers: *even with the answer key in hand, can our operator family
recover the pocket at all?*

This makes it a **feasibility gate**, not an evaluation. The ordering is:

```
Phase 0: physics unit tests + data cleaning
Phase 1: apo/holo superposition → learnability gate per target
Phase 2: ceiling (in-sample, heavy optimizer, intentional overfit)
Phase 3: LOPO — only on targets whose ceiling clears the baselines
```

LOPO without an established ceiling assumes the signal exists. The ceiling
proves (or disproves) that assumption first.

---

## What the ceiling must beat

The ceiling number is meaningless without the right baselines. It must exceed:
1. **Random residues** — the null
2. **Non-functional surface pockets** — the challenge's own scoring bar
3. **Plain degree / betweenness centrality** — cheap structural measures

A ceiling of 0.6 that plain node degree also reaches at 0.6 is not a ceiling for
*our method* — it's just structure. The ceiling is only our method's ceiling if it
beats all three baselines.

Label it with a block-bootstrap CI. A 60-trial random search max is an order
statistic, not a point estimate.

---

## What the ceiling result tells you

| Ceiling result | Interpretation | Action |
|---------------|----------------|--------|
| High AUC (> 0.8), beats baselines | Signal exists in apo; operator family is capable; defaults badly tuned | Proceed to LOPO; improve λ defaults (IMP-H6) |
| Moderate AUC (0.65–0.8), beats baselines | Signal partially present; architecture may be limiting | Consider V_pair (HYP-P2) or H13 refactoring (IMP-H7) |
| Low AUC (< 0.65), barely beats baselines | Weak signal in apo topology | Cross-check with ProteinLens; examine apo/holo RMSD at pocket |
| At-chance (≈ 0.5) even with answer key | Signal absent from apo structure | Report as "cryptic pocket not learnable from apo topology" — this is a real finding |

---

## The KRAS warning sign

From the Sonnet discussion: optimized AUC_apo on KRAS was ~0.53. The notebook's
per-protein OPT results (60 random trials) are already the closest we have to a
ceiling — and they hover near chance. Combined with the KRAS Switch-II pocket being
the textbook cryptic case (pocket opens only on binding), this suggests:

> The ceiling may be at the floor for KRAS — the apo contact graph may simply not
> encode the Switch-II pocket, regardless of operator choice.

The apo/holo RMSD measurement at the pocket (Phase 1) will confirm or deny this
before any expensive optimization is run.

---

## Status update, 2026-07-15 — the KRAS warning sign was confirmed, and a scope gap found

This file predicted, on 2026-06-21, that "the ceiling may be at the floor for KRAS." That
is now a measured result, not a warning sign: **TASK-0046** (Done, 2026-07-14) ran the real
ceiling search and found KRAS_G12C's ceiling AUC = 0.5239-0.5250 — **below** that target's
own proximity floor (0.798, TASK-0094). Per `P-0002` (`.ai/memory/shared/pitfalls.md`), this
is the first real case of `ceiling < floor`, a case this file's own framing did not
anticipate (the "What the ceiling result tells you" table above has no row for it — every
row assumes `ceiling >= floor`). Two follow-up tasks now qualify how settled this is:
**TASK-0116** (is 60 random trials over ~8 dimensions enough search density to trust the
negative reading?) and **TASK-0117** (the search used `t_max=15`/`n_steps=500` with no
validity check — the exact gap TASK-0108/0109/0110 exist to close). Until both land, read
KRAS's ceiling number as "below floor, but not yet fully validated as such," not settled.

**Real scope gap found the same day, not previously flagged**: this file's own "Minimum
set" below explicitly names H8, H13 (or its projection), and degree centrality as required
ceiling candidates alongside `H_new`. **TASK-0046 only ever searched `H_new`'s own 8-parameter
DOF** — no other operator was run through the ceiling search. The H13-vs-H_new comparison
this file calls "required for scientific rigor" (HYP-P5, `physics.md`) has still never been
run. No task currently owns closing this gap; TASK-0116 is about search *density* within
`H_new`'s space, not the missing-operators gap described here — the two should not be
conflated when scoping whatever picks this up next.

Separately, a live cross-check (2026-07-15, while preparing that day's task batch) found
`ceiling.py` and `run_challenge.py` seed CTQW from **different conventions for the same
active site** — the former uses the full multi-residue array, the latter reduces to one
representative residue (a TASK-0090 crash workaround, not a physics choice). See
`physics.md`'s new cross-cutting finding on seed cardinality — this affects how comparable
TASK-0046's ceiling number is to `run_challenge.py`'s own reported 0.779 in the first place.

---

## Status update, 2026-07-17 — TASK-0110 cross-checks TASK-0046's ceiling on a second, independent axis

**TASK-0117's own gap is now partly answered from an unexpected direction.** TASK-0110
(Optuna scan of CTQW's *numerical* parameters, `t_max`/`n_steps` — deliberately kept
`H_new`'s physical weights at default, the opposite axis from TASK-0046's own search)
used `ceiling.py`'s exact seed convention (full active-site array) for a clean
cross-check, not TASK-0118's newer `coherent=False` convention — see that task's own
Done section for why. Result: KRAS_G12C's best honestly-sampled (Nyquist-uncapped) AUC
= **0.4750**, closely agreeing with this file's own 0.5239-0.5250. **Two independent
optimizers, two different parameter axes, same seed convention, same conclusion** —
this is real corroborating evidence that KRAS's near-chance ceiling is not an artifact
of under-searching `H_new`'s physical DOF specifically (TASK-0116's own concern); it
also shows up when the numerical propagation parameters are searched instead.

**A genuinely new, unanticipated finding from the same task, relevant to the "Minimum
set" and "Optimizer" sections below**: TASK-0046's `t_max=15`/`n_steps=500` are not
merely unvalidated (TASK-0117's framing) — TASK-0110 found the actual convergence
requirement for `time_averaged_ctqw` on real `H_new` operators is **145,000x-3,950,000x**
larger, and reaching it is currently **computationally infeasible** (a real call did not
return after 2+ hours). Any future ceiling search that tries to "fix" `t_max`/`n_steps`
by simply plugging in the analytically-correct value, rather than working around this
algorithmic cost, will hit the same wall. Full detail:
`.ai/tasks/DONE/TASK-0110-optuna-apo-holo-parameter-scan.md`.

---

## Status update, 2026-07-18/19 — the H13-vs-`H_new` scope gap (flagged above, 2026-07-15) is closed

**TASK-0126** ran H13 (via both projection options) through the ceiling search on all 3
mandatory targets. Started under the TASK-0129 finite-`t_max` convention, then switched
mid-task to TASK-0130's exact closed-form infinite-time limit once that landed
concurrently — the switch also removed the `O(n_steps)` time-stepping cost that had
made a full 3-target Option B run infeasible under the old convention (BCR_ABL1
projected ~31.5 hours/60 trials; CARDIAC_MYOSIN not attempted). Headline results,
checked not assumed, all under `H_new`'s own TASK-0130 closed-form ceiling
(KRAS=0.6288, BCR_ABL1=0.6671, CARDIAC_MYOSIN=0.8297):

- **Literal Option A (scalar `trace`-of-3×3-blocks projection) is degenerate** — proven
  via `np.allclose` (max diff 1.8e-15) to collapse exactly to `H2_combinatorial_
  laplacian` for this repo's real `H13_3N_anm_hessian` construction. It discards *all*
  orientational information, not "some" as this file and `physics.md` HYP-P5 both hedged.
  H2 does not beat `H_new` on any of the 3 targets.
- **Option B (3N×3N-native propagation, orientation-preserving) was implemented as a
  thin wrapper around the existing propagators** — no refactor of `ctqw`/`time_averaged_
  ctqw`/`time_averaged_ctqw_converged` was needed, contrary to what this file's own
  "Minimum set" note below anticipated. Run to completion on all 3 targets under the
  closed form (KRAS: 0.5026, BCR_ABL1: 0.6466, CARDIAC_MYOSIN: 0.8513).
- **The result is genuinely mixed, not a clean win or loss**: Option B does not beat
  `H_new` on KRAS_G12C (worst of the three candidates there) or BCR_ABL1 (close,
  −0.0205), but **does beat `H_new` on CARDIAC_MYOSIN** (+0.0216) — the one target
  where H13's full orientational detail actually helped over the scalar reductions.
  Per IMP-H7's own decision protocol, `H_new` is **not** uniformly confirmed as
  baseline against H13 — this is a target-dependent finding, not a global verdict.
- **`H14_anm_pinv_trace`** (already implemented, already Tier-A, TASK-0096) — the
  codebase's own non-degenerate scalarization of H13's physics (ANM cross-correlation,
  Bahar/Atilgan/Erman 1997) — **beats `H_new`'s ceiling on BCR_ABL1** (+0.0503), not on
  KRAS_G12C or CARDIAC_MYOSIN. Worth a dedicated look at that target specifically, not
  a project-wide reselection signal.

Full detail, including the H13-native rigid-body-nullspace bug found in
`min_adequate_t_max` (and superseded by the closed form's own degenerate-eigenvalue
grouping) along the way: `.ai/tasks/DONE/TASK-0126-h13-ceiling-comparison.md`.

---

## Status update, 2026-07-19 — H14's own margin over `H_new` does not survive scrutiny (TASK-0138)

**TASK-0138** ran a TASK-0131-compatible permutation null against H14's ceiling search
on all 3 targets, plus a trial-density convergence check. Headline: **H14's ceiling-
clears-floor claim is not statistically distinguishable from winner's-curse noise on
either target where a positive margin existed** — KRAS_G12C's margin (0.0914) sits at
the 70th percentile of 200 null replicates (p=0.300 uncorrected); BCR_ABL1's (0.1357,
the target where TASK-0126 found H14 beating `H_new`) sits at the 79th percentile
(p=0.210 uncorrected) — neither reaches conventional significance even before
Bonferroni correction. CARDIAC_MYOSIN's margin is negative (H14's ceiling sits *below*
its own floor) and confirmed, via a reduced 30-replicate null, to sit at the 0th
percentile — worse than every null replicate, not just non-significant. Separately, a
trial-density check found KRAS_G12C's 60-trial convention has **not converged**
(running max still climbs from 0.5732 at n=60 to 0.5949 at n=150) while BCR_ABL1's has
(0.7174 → 0.7213, a much smaller residual gain) — the BCR_ABL1 margin over `H_new` is
therefore not a trial-density artifact, but its own ceiling-clears-floor claim still
does not survive the null either way. Same qualitative pattern this file's own
2026-07-18/19 update above found for H13, and TASK-0131 found for `H_new`'s own
CARDIAC_MYOSIN margin: a headline-looking number that does not survive scrutiny once
applied. Full detail: `.ai/tasks/DONE/TASK-0138-h14-ceiling-validity-characterization.md`.

---

## Which operator to use for the ceiling search

The ceiling should be measured with **every operator candidate** (H_new, H13 projection,
and H_new + V_pair if implemented), because the ceiling comparison *is* the data-driven
basis for choosing an operator. See `physics.md` HYP-P5 and `../improvements/hamiltonian_code.md` IMP-H7.

**Minimum set:**
- H_new with full (λ_B, λ_T, λ_R, λ_C, λ_M, α, r_c, n_low, kernel) search
- H8 (GNM) as a classical reference ceiling (cheap, well-validated)
- H13 projected to N×N — or 3N×3N if propagators are refactored (see IMP-H7) — **done,
  TASK-0126 (2026-07-18/19): both options run on all 3 targets; Option B beats `H_new`
  on CARDIAC_MYOSIN only (mixed, target-dependent), see status update above. H14
  (pinv-trace) beats it on BCR_ABL1 only, was not on this original list — add it.**
- Degree centrality (plain graph degree) as the structural floor

**Optimizer:** Grid + random search is acceptable at this stage. 60 trials from the
notebook is too few for a high-dimensional space. Consider at minimum 500 trials with
a Latin hypercube design, or a brief Bayesian optimization run (scikit-optimize).

---

## Ceiling vs per-protein OPT in the notebook

The notebook Section 8 stores per-protein `OPT` params. These are the closest
current approximation to the ceiling but should not be confused with it:
- They use only 60 random trials (small optimizer)
- They were run on the same targets used to evaluate them (correct for ceiling, not for LOPO)
- n_low and kernel were searched but n_low was not scaled with N (IMP-H1 unfixed)

Once IMP-H1 and IMP-H3 are applied, re-run the ceiling search properly before
promoting any results as a performance bound.

---

## The ceiling-minus-LOPO gap

Once both are established, the gap `ceiling_AUC - LOPO_AUC` is a scientifically
meaningful quantity: it quantifies the cost of not knowing the answer. A large gap
means the operator is capable but generalization is poor (parameter sensitivity,
target diversity). A small gap means the method generalizes well and the ceiling
is actually reachable in a blind setting.
