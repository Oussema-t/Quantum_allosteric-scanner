# TASK-0266 — Is CTQW's cryptic lean just burial detection?

- Status: Done
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

- [x] Add **real per-residue SASA** (`allostery.corex.per_residue_native_asa`
      — the validated Shrake–Rupley wrapper [[TASK-0229.006]] and
      [[TASK-0257]] both use) as its own block in the attribution.
- [x] Re-run [[TASK-0254]]'s Shapley with blocks: geometry / fpocket / SASA /
      CTQW. Report **CTQW's contribution added last** with SASA present.
- [x] Re-run the crypticity stratification with SASA in the model. **The
      test**: does CTQW's cryptic lean survive, shrink, or vanish? **Shrinks
      by more than half; was not significant even before this control.**
- [x] Report SASA's own cryptic lean separately — if SASA leans cryptic the
      same way CTQW does, that is the confound demonstrated directly.
      **It does, same direction, also not itself significant.**
- [x] Cluster-robust significance ([[TASK-0261]]'s exact cluster-level
      permutation, 13 clusters), not row-level Wilcoxon. **A real data
      wrinkle found and handled explicitly, not silently: one apo-structure
      pair (TRP_SYNTHASE_F6F/F19) straddles the 80% crypticity bar on
      opposite sides, which conflicts with cluster-level grouping — excluded
      from the stratified test only (both members), kept everywhere else.**
- [x] State plainly whether [[TASK-0267]] is still worth running. **No.**

## Acceptance

- [x] Four-block attribution including SASA, added-last for every block.
- [x] Crypticity-stratified breakdown with and without SASA, side by side.
- [x] An explicit verdict: lean survives / shrinks / vanishes.
- [x] A recommendation on whether to proceed with [[TASK-0267]].
- [x] `RESULTS.md`.

## Constraint

The Reviewer's stated expectation is that **burial kills the lean**. Do not
let that expectation shape the run — if the lean survives SASA, that is the
first CTQW result in this register to survive a serious control, and it should
be reported with full prominence and escalated immediately.

## Done

**2026-08-25, Implementer D.**

New `scripts/task0266_sasa_burial_control.py`, reusing
`task0249_composite_dumb_baseline.target_rows`/`task0242_two_stage_
dryrun.prep` (imported), `task0254_fpocket_variance_and_crypticity`'s own
`cv_auc`/`build_blocks`/`crypticity`/`z` (imported, unchanged),
`task0257_r2_sasa_burial_vs_degree.per_residue_sasa` (imported, the same
validated `Bio.PDB.SASA.ShrakeRupley` computation R2 already used — SASA
added here as its own independent Shapley block, not substituted into
`H_new`'s own `V_R` term the way R2 did; CTQW is scored exactly as
[[TASK-0254]]'s own baseline computed it, unchanged), and
`task0261_cluster_robust_stats.cluster_sign_flip_test`/
`cluster_permutation_two_group`/`CM` (imported, this task's own Scope:
"TASK-0261's exact cluster-level permutation, not row-level Wilcoxon"). A
generalised n-block exact Shapley routine written locally (4!=24
permutations, cheap), extended beyond [[TASK-0260]]'s own version of the
same pattern to report added-last for *every* block, per this task's own
Acceptance. 20/20 usable targets (matching [[TASK-0249]]'s own filter,
[[TASK-0253]]'s empty-seed guard inherited automatically).

**Overall (n=20, unstratified) — SASA adds essentially nothing on its own,
and does not close the residual either**: Shapley share median geometry
+42.2%, fpocket +7.4%, **SASA −0.4%**, CTQW +3.4%; added-last median
geometry +12.4%, fpocket +3.1%, **SASA −0.0%**, CTQW −0.2%. Unexplained
28.6% (3-block) → 27.2% (4-block, +SASA) — a small movement, matching
[[TASK-0260]]'s own P2Rank finding in magnitude (neither classical
addition tried so far closes the residual). Cluster-robust (13 clusters,
[[TASK-0261]]'s exact permutation): CTQW added-last p=0.217 (no SASA) →
p=0.262 (with SASA); SASA added-last itself p=0.540 — **none of these
were ever significant in aggregate**, consistent with every prior finding
in this register that CTQW's aggregate marginal is noise-level.

**A real methodological wrinkle found and handled, not silently
worked around**: crypticity is defined per-ligand (holo-specific);
clustering is per-apo-structure. `TRP_SYNTHASE_F6F` (87% open) and
`TRP_SYNTHASE_F19` (78%, just under the pre-registered 80% bar) share
one apo structure but land on opposite sides of the threshold —
`cluster_permutation_two_group`'s own assertion correctly refuses to
split one cluster across both groups. Excluded from the crypticity-
stratified test specifically (both members), kept in every other number
above — n=9 vs. 9 rows, 6 vs. 6 clusters for the stratified test.

**The central test, crypticity-stratified, cluster-robust — the verdict
this task exists to deliver: the lean shrinks by more than half and was
never significant to begin with.**

| statistic | cryptic median | open median | cluster-perm p (cryptic > open) |
|---|---|---|---|
| CTQW added-last, **no SASA** | +5.53% | −0.10% | 0.0736 |
| CTQW added-last, **with SASA** | +2.17% | +0.01% | 0.2392 |
| CTQW Shapley share, no SASA | +12.98% | −2.28% | 0.1656 |
| CTQW Shapley share, with SASA | +5.39% | −2.23% | 0.3409 |
| **SASA's own Shapley share** | **+8.39%** | **−3.51%** | 0.3106 |

**SASA itself leans cryptic, the same direction CTQW does** — partial,
direct confirmation of this task's own named confound (buried regions
are closed, closed regions are cryptic), though SASA's own lean is not
itself significant either (p=0.311). Controlling for it: CTQW's own
added-last cryptic-vs-open gap **roughly halves** (5.6 percentage points
→ 2.2 points), and its already-marginal significance weakens further
(p=0.074 → p=0.239). **The gap does not flip sign or vanish to exactly
zero** (a small positive residual remains, +2.17% vs. +0.01%) — so the
honest verdict is **shrinks substantially, not a clean survive/vanish**
— but it is essential context that this was **never a significant
result at any stage**: p=0.0736 without any burial control does not
clear even an uncorrected 0.05 bar, let alone this register's own much
stricter multiplicity-adjusted bar. Framing this as "CTQW's lean
survives" (this task's own filing table's own optimistic framing, before
the control) would overstate a result that was marginal from the start
and is now weaker still.

**Recommendation on [[TASK-0267]] (crypticity-matched null): do not
proceed.** That task exists to build a more expensive matched-null
control for a signal to protect against a *different* confound
(candidate-selection/matching artifacts) — but there is no significant
signal left here to protect. CTQW's own cryptic lean was p=0.074
uncontrolled and p=0.239 once the single most obvious confound (burial)
is controlled for; spending further effort on a second, more elaborate
null construction for an effect that does not clear even the loosest
reasonable bar is not a good use of this register's remaining time. This
directly fulfills this task's own framing as "the cheap control that may
make TASK-0267 unnecessary."

**Per this task's own Constraint** ("if the lean survives SASA... report
with full prominence and escalated immediately" / "do not let \[the
burial\] expectation shape the run"): the run was not shaped by either
expectation — the lean neither cleanly survives (as the filing table's
own framing hoped could be tested) nor cleanly vanishes (as the
Reviewer's own stated expectation predicted). Both directions are
reported with the same numbers, side by side, and the actual, more
nuanced outcome (substantial shrinkage of an already-non-significant
effect) is stated as what it is, not rounded toward either prior
expectation.

**Not done, and why**: `documentation/CTQW_CONTRIBUTION_BRIEF.html` was
not updated — this task's own Acceptance lists only `RESULTS.md`, unlike
[[TASK-0260]]'s explicit brief-update requirement, and the brief's own
§08 does not currently assert a standalone "CTQW leans cryptic"
claim that this finding would contradict (checked directly, not
assumed) — flagged here so whoever next touches §08 knows this
qualification exists if such a claim is ever added. A proper
random-intercept/mixed-model alternative to the permutation test was not
attempted — [[TASK-0261]]'s own module docstring already argues
permutation is the right choice at 13 clusters (7 non-trivial), not
revisited here.

Tests: no `src/` code changed — investigation script only, matching this
project's own established convention for `scripts/`. `task0254_fpocket_
variance_and_crypticity.py`, `task0257_r2_sasa_burial_vs_degree.py`, and
`task0261_cluster_robust_stats.py` all reused unmodified, not edited.

Artifacts: `scripts/task0266_sasa_burial_control.py` (new),
`results/tasks/0266_sasa_burial_control/{shapley_4block_sasa.json,
crypticity.json,cluster_robust_results.json}`, `RESULTS.md` new row.
