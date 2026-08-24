# TASK-0250 — H16.1: does GNM actually reproduce experimental B-factors on our targets?

- Status: TODO
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

- [ ] For each target with a real apo structure, compute GNM predicted MSF and
      correlate against the deposited Cα B-factors (Pearson, the convention in
      the source literature; report Spearman alongside).
- [ ] Report per target, not pooled. This is a per-structure validity check —
      a pooled number would hide exactly the failures it exists to find.
- [ ] Use the same `enm_cutoff` each target is actually scored with, not a
      re-tuned one. The question is whether the model *we use* is valid, not
      whether some GNM could be.
- [ ] State the pass bar **before** looking: the literature convention is
      Pearson ≈ 0.6+ for a good fit, 0.4–0.6 marginal. Pre-register it.
- [ ] Flag targets whose B-factors are unusable (very high resolution refined
      with TLS, NMR ensembles, cryo-EM without per-atom B) rather than scoring
      them — an invalid input is not a model failure.
- [ ] Cross-reference the result against each target's existing GNM-derived
      results, and say plainly which of our published numbers are affected.

## Acceptance

- [ ] One table: target → Pearson → Spearman → verdict vs the pre-registered bar.
- [ ] An explicit list of targets where GNM-derived results should be
      re-qualified, or a statement that none are.
- [ ] `RESULTS.md` section; register STATUS for H16.1 updated to cite this task.

## Constraint

Do not tune the cutoff to make the correlation pass. If the model does not fit
at the cutoff we actually use, that is the finding.
