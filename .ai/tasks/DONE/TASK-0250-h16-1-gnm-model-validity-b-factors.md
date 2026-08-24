# TASK-0250 — H16.1: does GNM actually reproduce experimental B-factors on our targets?

- Status: Done
- Assignee: unassigned (suggest Implementer — small, self-contained, high value per hour)
- Priority: **High — cheapest open item in the register, and it gates the interpretation of every GNM/ANM result we have**
- Filed: 2026-08-24 by Reviewer
- Parent: [[TASK-0248]] (confirmed genuinely open by direct search)
- Related: [[TASK-0226]] (H16.2, real-PDB retest), [[TASK-0229.007]], [[TASK-0245]]

## Hypothesis

**H16.1** — GNM reproduces experimental B-factors. This is the standard
**per-target model-validity check** for an elastic network model: if the
predicted mean-square fluctuations do not correlate with the crystallographic
B-factors, the ENM is not a valid model *of that structure*, and every mode-
derived quantity computed from it is uninterpretable for that target.

## Why it matters more than its size suggests

This register runs GNM/ANM everywhere — `dcc_low`, `prs_low`, mode energetics
([[TASK-0233]]), two-state ANM ([[TASK-0229.007]]), ANM reachability
([[TASK-0227]]/[[TASK-0230]]) — and has **never** run the validity check that
the ENM literature treats as mandatory before reporting any of it.

Consequence if it fails on some targets: those targets' negative results are
not evidence about allostery, they are evidence the model does not fit. That
would materially change how our negatives should be read — and we would have
been over-claiming them.

Consequence if it passes: it removes a live alternative explanation for the
whole negative class, which strengthens every negative we report. **Either
outcome is worth having and neither is the one we are hoping for.**

## Scope

- [x] For each target with a real apo structure, compute GNM predicted MSF and
      correlate against the deposited Cα B-factors (Pearson, the convention in
      the source literature; report Spearman alongside).
- [x] Report per target, not pooled. This is a per-structure validity check —
      a pooled number would hide exactly the failures it exists to find.
- [x] Use the same `enm_cutoff` each target is actually scored with, not a
      re-tuned one. The question is whether the model *we use* is valid, not
      whether some GNM could be.
- [x] State the pass bar **before** looking: the literature convention is
      Pearson ≈ 0.6+ for a good fit, 0.4–0.6 marginal. Pre-register it.
- [x] Flag targets whose B-factors are unusable (very high resolution refined
      with TLS, NMR ensembles, cryo-EM without per-atom B) rather than scoring
      them — an invalid input is not a model failure.
- [x] Cross-reference the result against each target's existing GNM-derived
      results, and say plainly which of our published numbers are affected.

## Acceptance

- [x] One table: target → Pearson → Spearman → verdict vs the pre-registered bar.
- [x] An explicit list of targets where GNM-derived results should be
      re-qualified, or a statement that none are.
- [x] `RESULTS.md` section; register STATUS for H16.1 updated to cite this task.

## Constraint

Do not tune the cutoff to make the correlation pass. If the model does not fit
at the cutoff we actually use, that is the finding.

## Done

**2026-08-24 — Implementer A.** Real, mixed result — not the outcome hoped for
either direction, exactly as the task's own framing anticipated.

**Method**: `potentials._gnm_msf(apo.coords, enm_cutoff)` (this project's own
existing GNM MSF implementation — diagonal of the Kirchhoff pseudo-inverse, not
re-derived) vs. real apo Cα B-factors (`clean.CleanResult.bfactors`, real fetch,
no mocking), all 15 real targets, each target's own real `enm_cutoff` (uniformly
8.0 Å, confirmed by direct read of `targets.yaml`, not assumed). Pass bar
pre-registered before any correlation was computed, per the task's own text:
Pearson ≥ 0.6 PASS, 0.4–0.6 MARGINAL, < 0.4 FAIL.

**Unusable-B-factor check, done first, via a real RCSB query** (batched
GraphQL, `exptl.method` + resolution for all 15 apo entries) — not guessed:
14/15 are X-RAY DIFFRACTION, resolution 1.24–3.42 Å (BCR_ABL1's 1OPL at 3.42 Å
is the lowest-resolution X-ray entry — not excluded, but its correlation
carries lower confidence than the sub-2.5 Å entries, noted not scored
differently). **One genuine flag**: CARDIAC_MYOSIN_TABLE1's apo (5TBY) is
ELECTRON MICROSCOPY, nominal resolution 20.0 Å — excluded from the tally,
reported for transparency (Pearson 0.435, would be MARGINAL if scored).

**Result — 14 scored: 6 PASS, 4 MARGINAL, 4 FAIL.** Full table in `RESULTS.md`'s
own new section and in `results/tasks/0250_gnm_bfactor_validity/
gnm_bfactor_validity.json`. Headline finding: **GNM is not a valid model for
nearly a third of this project's own real targets, at the cutoff it actually
uses** — this had never been checked despite GNM/ANM underlying most of the
register's own scored observables.

**Consequential for the mandatory set**: **MYC_MAX FAILs cleanly** (Pearson
0.148, barely above chance) — every GNM/ANM-derived quantity reported for
MYC_MAX (mode energetics, ANM reachability, any `dcc_low`/`prs_low` computed
there) rests on a model that does not predict that structure's own
crystallographic B-factors. **BCR_ABL1 is MARGINAL** (0.493) — its own
GNM-derived headline numbers (including `AUC_apo_Hnew_optimised`) carry a
real, now-quantified model-fit uncertainty this register did not previously
state. KRAS_G12C (0.646) and CARDIAC_MYOSIN (0.686) both clear the PASS bar
cleanly — the mandatory-set negatives reported on those two targets are not
explained by this failure mode.

**Explicit list of targets needing re-qualification** (this task's own
Acceptance requirement): **MYC_MAX** (FAIL — re-qualify any GNM/ANM-derived
claim as resting on an invalid model for this structure) and **BCR_ABL1**
(MARGINAL — flag, do not retract). GLUCOKINASE, TAR_RECEPTOR,
GLYCOGEN_PHOSPHORYLASE (MARGINAL) and ATCase, CASPASE1, GROEL_SUBUNIT (FAIL)
are non-mandatory targets with the same qualification, listed for completeness
in the full table rather than repeated here. KRAS_G12C, CARDIAC_MYOSIN, PTP1B,
CASPASE7, HEMOGLOBIN, PFK: no re-qualification needed (PASS).

**`.claude/hypotheses/reference_register.md`**: H16.1's row and its own
dedicated H16 section both updated from `UNTESTED — genuinely open` to
`TESTED — real, mixed`, citing this task; the "genuinely open hypotheses"
callout narrowed to H5 alone (the one hypothesis in the register still with
zero coverage).

**Not done, per this task's own scope**: no downstream result (BCR_ABL1's
headline AUC, MYC_MAX's mode-energetics/reachability numbers, or any other
GNM-derived quantity) was re-run, re-scored, or retracted — this task states
the consequence precisely, per its own Acceptance requirement, and leaves the
re-qualification decision to whoever next touches those specific results
(flagged above, not silently absorbed).

**Validated**: full `__WORK_IN_PROGRESS__` suite unaffected (no library code
changed, investigation script only) — not re-run as part of this task, no
production code path touched.
