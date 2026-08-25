# TASK-0266 — Is CTQW's cryptic lean just burial detection?

- Status: TODO
- Assignee: **Implementer D**
- Priority: **High — it is the cheap control that may make [[TASK-0267]] unnecessary**
- Filed: 2026-08-25 by Reviewer
- Blocks: [[TASK-0267]] (crypticity-matched null) — run this first
- Related: [[TASK-0259]], [[TASK-0260]], [[TASK-0257]], [[TASK-0254]]

## The one CTQW signal that keeps surviving

Three independent looks now point the same way:

| source | cryptic targets | already-open targets | p |
|---|---|---|---|
| [[TASK-0259]] (n=3 vs 9) | +1.91% | −0.10% | 0.30 |
| [[TASK-0260]] 4-block, Reviewer-verified (n=11 vs 9) | **+11.7%** | **−2.3%** | 0.11 |

CTQW is the **only** block leaning toward cryptic targets. Every static method
leans the other way — P2Rank +30.4% open vs +8.3% cryptic (p=0.0185), fpocket
+26.0% vs +5.3% (p=0.0275). Not significant, but consistent, and it is
mechanistically the right place for a dynamics method to help.

## The confound that has to be ruled out first

**Buried regions are closed; closed regions are cryptic.** A score that simply
prefers buried residues would produce exactly this pattern with no dynamics
involved.

The geometry block contains `degree_centrality` as its burial proxy — but
[[TASK-0257]] R2 established that `degree` is a *poor* burial measure (SASA
beats it against B-factors on 11/14 targets) and **SASA is in no block at
all**. So there is an uncontrolled burial channel that could account for the
entire cryptic lean.

## Scope

- [ ] Add **real per-residue SASA** (`allostery.corex.per_residue_native_asa`
      — the validated Shrake–Rupley wrapper [[TASK-0229.006]] and
      [[TASK-0257]] both use) as its own block in the attribution.
- [ ] Re-run [[TASK-0254]]'s Shapley with blocks: geometry / fpocket / SASA /
      CTQW. Report **CTQW's contribution added last** with SASA present.
- [ ] Re-run the crypticity stratification with SASA in the model. **The
      test**: does CTQW's cryptic lean survive, shrink, or vanish?
- [ ] Report SASA's own cryptic lean separately — if SASA leans cryptic the
      same way CTQW does, that is the confound demonstrated directly.
- [ ] Cluster-robust significance ([[TASK-0261]]'s exact cluster-level
      permutation, 13 clusters), not row-level Wilcoxon.
- [ ] State plainly whether [[TASK-0267]] is still worth running.

## Acceptance

- [ ] Four-block attribution including SASA, added-last for every block.
- [ ] Crypticity-stratified breakdown with and without SASA, side by side.
- [ ] An explicit verdict: lean survives / shrinks / vanishes.
- [ ] A recommendation on whether to proceed with [[TASK-0267]].
- [ ] `RESULTS.md`.

## Constraint

The Reviewer's stated expectation is that **burial kills the lean**. Do not
let that expectation shape the run — if the lean survives SASA, that is the
first CTQW result in this register to survive a serious control, and it should
be reported with full prominence and escalated immediately.
