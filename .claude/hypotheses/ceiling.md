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

## Which operator to use for the ceiling search

The ceiling should be measured with **every operator candidate** (H_new, H13 projection,
and H_new + V_pair if implemented), because the ceiling comparison *is* the data-driven
basis for choosing an operator. See `physics.md` HYP-P5 and `../improvements/hamiltonian_code.md` IMP-H7.

**Minimum set:**
- H_new with full (λ_B, λ_T, λ_R, λ_C, λ_M, α, r_c, n_low, kernel) search
- H8 (GNM) as a classical reference ceiling (cheap, well-validated)
- H13 projected to N×N — or 3N×3N if propagators are refactored (see IMP-H7)
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
