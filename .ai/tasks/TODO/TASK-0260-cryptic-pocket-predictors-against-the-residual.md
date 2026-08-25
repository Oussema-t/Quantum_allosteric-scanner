# TASK-0260 — Does a purpose-built cryptic-pocket predictor close the 29% residual?

- Status: TODO
- Assignee: unassigned (suggest Explorer for the citation/constraint pass, then Implementer)
- Priority: **Highest — this is the direct test of [[TASK-0259]]'s finding and it decides what Phase 2 is about**
- Filed: 2026-08-25 by Reviewer
- Related: [[TASK-0259]], [[TASK-0254]], [[TASK-0163]] (fpocket baseline precedent), [[TASK-0137]] (citation-verification convention)

## Why

[[TASK-0259]] found the unexplained share is **not** mysterious physics. It is
apo crypticity, and almost nothing else:

| correlate of the unexplained share | rho | p (rows) | p (clustered by structure) |
|---|---|---|---|
| **apo crypticity** | −0.771 / −0.646 | **0.0001** | **0.017** |
| ENM validity | +0.002 | 0.99 | — |
| distance to active site | −0.236 | 0.32 | — |
| pocket size | +0.213 | 0.37 | — |

Median unexplained: **55% on cryptic targets vs 24% on already-open ones.**
Mirror confirmation: fpocket's own Shapley share correlates **+0.518
(p=0.019)** with apo-openness — it works when the pocket is already there.

So the residual has a name. The question this task answers is whether it is
**addressable classically**. If a predictor built specifically for cryptic
sites closes it, the residual is a solved problem we simply had not applied,
and any quantum proposal must beat that predictor, not the current baselines.
If it does not close it, there is something genuinely unmodelled — and that is
the strongest possible motivation for Phase 2.

Either answer is decisive. There is no outcome of this task that leaves the
Phase 2 story where it is now.

## Candidate methods

Suggested by an external model; **all four must be citation-verified live
before any implementation**, per this register's standing convention. The
external suggestion dated PocketMiner to 2021, which we believe is wrong — do
not inherit any of these details, check them.

- **PocketMiner** — graph neural network, predicts cryptic-pocket-opening
  probability from a single static structure. Believed Meller et al.,
  *Nature Communications*, ~2023. Expected to be the strongest candidate.
- **CryptoSite** — SVM over static structural/sequence descriptors. Believed
  Cimermancic et al., *J. Mol. Biol.* 2016.
- **P2Rank** — random forest over Connolly surface points; a modern geometric
  peer to fpocket. Believed Krivák & Hoksza, *J. Cheminform.* 2018.
- **FTMap / FTSite** — fragment-based hot-spot mapping via FFT correlation of
  organic probes.

## The constraint question that must be settled first

**PocketMiner is trained on MD trajectories but infers from a static
structure.** The challenge forbids MD as *input*. Does an MD-trained model
whose inference is MD-free violate constraint 3?

- [ ] Settle this **before** building. Document our reading either way. If it
      is genuinely ambiguous, add it to [[TASK-0221]]'s organiser question
      list rather than assuming the favourable interpretation.
- [ ] The same question applies to CryptoSite (trained on a curated cryptic
      set) and P2Rank (trained on bound structures). State a single consistent
      rule and apply it to all four.

## Scope

- [ ] Verify all four citations live (Crossref/publisher record: title,
      authors, journal, volume, DOI) before writing code against them.
- [ ] Settle the MD-training constraint question and record the ruling.
- [ ] Install/run whichever survive both gates on the frozen set's **apo**
      structures. Apo only — holo would leak the label ([[TASK-0259]]).
- [ ] Score each as a **fourth block** in [[TASK-0254]]'s Shapley attribution,
      reusing that script unmodified with the new block's values substituted.
- [ ] Report the decision statistic: **each method's contribution when added
      last**, on top of geometry + fpocket + CTQW. That is the increment it
      supplies that nothing else does.
- [ ] Report how much of the 29% residual survives.
- [ ] Stratify by crypticity. The prediction to test: **the new method's gain
      should be concentrated on the cryptic targets**, mirroring fpocket's
      +0.518 correlation with openness in the opposite direction. If the gain
      is uniform across cryptic and open targets, it is not doing what its
      name says.
- [ ] Cluster by distinct apo structure ([[TASK-0261]]) — 20 rows are only 13
      structures, and apo-side scores are identical within a pair.

## Acceptance

- [ ] Citation-verification record for all four; ruling on the MD constraint.
- [ ] Four-or-more-block attribution table with each method's added-last value.
- [ ] An explicit number: how much of the 29% residual remains.
- [ ] The crypticity-stratified breakdown.
- [ ] `RESULTS.md`, and an update to
      `documentation/CTQW_CONTRIBUTION_BRIEF.html` §08, which currently argues
      for a cryptic-enriched target set on the strength of this residual.

## Constraint

If a classical cryptic predictor closes the residual, that is a negative for
the quantum proposal and must be reported with the same prominence as
everything else in the brief. It would also be genuinely useful science —
"the unexplained majority was a solved classical problem we had not applied"
is a publishable finding and an honest one.
