# TASK-0301 — Consensus among the rule family fails, and the reason narrows what a meta-selector could be

- Status: Done
- Priority: Medium — a measured negative that constrains the [[TASK-0300]] meta-selector question
- Filed: 2026-08-30 by Reviewer thread
- Related: [[TASK-0300]], [[TASK-0299]], [[TASK-0288]], [[TASK-0261]]

## Two parameter-free meta-selectors, both tested

[[TASK-0300]] showed the 61-rule family reaches **0.3307** if a per-protein
meta-selector picks the right rule (fpocket oracle 0.3984). The two
cheapest meta-selectors need no fitting at all, so they cannot overfit
13 clusters. Both were run.

### Idea 1 — consensus: take the candidate the most rules vote for

| | mean EH |
|---|---|
| consensus of 61 rules | **0.0482** |
| best single fixed rule (`hop>=1 + drug`) | 0.0899 |
| random | 0.0273 |

Cluster-robust: consensus vs random **p = 0.909**; consensus vs the single
best rule **p = 0.500**. **Consensus is worse than just using one good
rule, and not distinguishable from chance.**

### Idea 2 — vote margin as a confidence signal

Spearman(vote margin, consensus EH) = **−0.424** (p = 0.063). **Negative.**
The targets where the rules agree *most* strongly — `HCV_NS5B` ×4 (margin
0.51–0.56) and `DHPS_GC7` (0.52) — all score **0.000**.

## Why, and this is the useful part

**All 61 rules are functions of the same two inputs: distance-to-seed and
fpocket druggability.** They are not 61 independent opinions; they are one
opinion at 61 parameter settings. So when they agree it is because a
shared bias dominates, not because the answer is clear — which is exactly
what a *negative* margin correlation looks like.

**Consequence for any meta-selector:** ensembling, voting, stacking or
confidence-weighting over this family cannot work, no matter how it is
built. The family carries one signal. A meta-selector needs **genuinely
independent** evidence, not more combinations of the same two features.

## What that leaves (not tested here — candidates, ranked by independence)

1. **Sibling-conformer persistence.** Every target has siblings at >=95%
   identity (median 53, minimum 10 — external handover §4). Whether a
   cavity persists across independently solved structures is evidence of
   a completely different kind from distance or druggability. Fully
   unblocked: no MD, no Docker. **Requires the holo filter** — scoring
   persistence over structures solved *with the drug bound* is circular.
2. **ENM mode shift.** External Experiment D: p = 0.005–0.013 in the open
   stratum, survives fixed-node-budget and volume-residualisation. A
   dynamics signal, independent of geometry and size. **Not currently in
   the rule family at all.**
3. **Hydrophobic density.** External Experiment A: 6/6 open. Partially
   redundant with fpocket druggability, which already includes a
   hydrophobicity term — independence needs checking before use.

## The constraint that dominates all of them

**13 clusters.** Four selection procedures in this register have now been
destroyed by pseudo-replication ([[TASK-0282]], [[TASK-0293]],
[[TASK-0299]], [[TASK-0300]]). Any meta-selector with free parameters will
be the fifth. The external handover reached the same conclusion
independently (§6 item 6: *"Stop testing new pocket-level rankers on this
cohort. The binding constraint is 13 clusters, not the feature set."*).

**The meta-selector question is not answerable on this cohort.** It is
answerable on **ASBench/CASBench** — 118 structures, the benchmark the
collaborator's own cited paper (Wu, Strömich & Yaliraki 2022) uses, which
also supplies a published classical baseline (84% recovery) to measure
against. That is a Phase-2 proposal with a real cohort and a real target,
not another sweep on 13.

**2026-08-31 note ([[TASK-0302]]):** item 1 above, sibling-conformer
persistence, run with the required holo filter (both a minimum-bar and a
strict apo-only variant, per that task's own Constraint). **Does not
reproduce a standalone benefit either**: cluster-robust p=0.969
(min-bar) / 0.856 (strict apo-only) vs random, and exactly zero effect
as a druggability tie-break (mean Δ=+0.0000, p=1.000 — continuous
druggability essentially never ties, so persistence had almost no real
chance to act as a tie-breaker regardless). Independence is mixed:
persistence correlates more with pocket size (ρ=0.190) than with
druggability (ρ=0.129 raw, ρ=0.061 partial, controlling size) —
partially, not fully, "just size again." Full detail: [[TASK-0302]]'s
own Done section.

**2026-08-31 note ([[TASK-0303]]):** item 2 above, ENM mode shift,
ported into this repo's own real per-target `enm_cutoff` pipeline and
evaluated standalone. **Does not reproduce** — not on this register's own
ranker-vs-random statistic (p=0.20–0.56 everywhere) and not on Experiment
D's own exact percentile/Fisher statistic either (open stratum p=0.306/
0.319, vs. that experiment's own claimed 0.005–0.013). The independence
premise itself holds (partial correlation with druggability, controlling
pocket size: ρ=−0.044, p=0.212 — genuinely independent), but independence
alone does not translate into ranking power on this cohort. Full detail:
[[TASK-0303]]'s own Done section.
