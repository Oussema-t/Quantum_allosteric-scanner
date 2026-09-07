# TASK-0334 — Is the pipeline's below-chance pocket pick distance-anti-correlated? Turn a negative into a mechanism

- Status: Done
- Owner: **Implementer A** (built `reference_arms.py`; owns the pocket-level metric)
- Priority: High — it is the difference between "the walk subtracts value" and a publishable mechanism
- Filed: 2026-09-06 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0327]], [[TASK-0320]], [[TASK-0310]], [[TASK-0331]], [[HYP-P9]], [[HYP-P21]]

## Why

[[TASK-0327]] measured the pipeline at **8.9% pre-veto against a random-order
null of 18.4%** on held-out data — below chance — and read it as the CTQW stage
"actively subtracting value". That phrasing treats an anti-correlation as a
defect. It is more likely a **mechanism**, and this register already holds the
pieces: the walk tracks proximity (ρ(ctqw, proximity) = **+0.808** at candidate
level, [[TASK-0320]]), and where the annotated site is genuinely distal a
proximity score must *anti*-predict it.

**Unverified inference, which is exactly why this is a task.** If it holds,
"the walk measures distance, and distance anti-predicts distal truth" is a
result. If it does not, the below-chance number needs a different explanation
and "subtracts value" cannot stand either.

## Intent Contract

- Outcome: for each protein in [[TASK-0327]]'s held-out set, the distance from
  the active site to (a) the pocket the pipeline ranks #1, (b) the true drug
  pocket, (c) a random candidate. Report the correlation between the
  pipeline's pocket rank and pocket-to-active-site distance.
- Prediction, stated before the run: the pipeline's #1 pick is **closer** to
  the active site than the true pocket, and its rank correlates negatively
  with distance. A null result refutes the proximity-mechanism reading.
- In Scope: read-only over stored artifacts — `s14_r{1,2}_k10_h2_*.json` carries
  `ranks`, `seed_resnum`, `seed_pocket`, `pockets`; the `allosteric` branch's
  `pocket_distance.csv` ([[TASK-0331]] already vendored it) carries the
  distances. No walk re-run, no PDB refetch.
- Constraints: use [[TASK-0327]]'s **held-out** cohort definition
  (`LEAKY_SOURCES = {"asbench"}` only) — ASBench is PASSer's training data and
  pooling it back in reintroduces the confound that task corrected for twice.
  Report the full-cohort number alongside, not instead.
- Planned Validation: the *true* pocket's own distance distribution must match
  `pocket_distance.csv`'s `is_distal` flag on the same rows. If it does not,
  the join is wrong and no correlation from it is trustworthy.

## Consequence

Whichever way it lands, [[TASK-0332]] needs the answer before the submission
states anything about why the walk fails. "Subtracts value" is currently in a
Done file and will be quoted.

## Done

**2026-09-06, Implementer A.** Read-only join of TASK-0327's own stored
`s14_r{1,2}_k10_h2_*.json` artifacts (already vendored in this repo by
TASK-0328, no re-fetch needed) against the `allosteric` branch's
`allosteric/datasets/pocket_distance.csv`, extracted via `git show
origin/allosteric:...` rather than a worktree checkout (no writes to
that branch, nothing checked out). Verified the CSV is byte-identical
between commit `f257789` (the version TASK-0331 read) and `8dcc6fa`
(current `origin/allosteric` HEAD at fetch time) via `git diff` — no
output, so no drift to reconcile. Script + full output:
`__WORK_IN_PROGRESS__/results/tasks/0334_ctqw_proximity_anticorrelation/
{distance_anticorrelation.py,distance_anticorrelation_result.json,
pocket_distance.csv}`.

### Planned Validation, run first

Join key = protein id (`ASB_xxxx`/`CAS_xxxx`/`CB_xxxx`/`CS_xxxx`/
`PM_xxxx`), confirmed identical between the s14 JSON records and the
CSV's own `name` column. 100% join coverage both rounds (96/96 round 1,
67/67 round 2, 0 unmatched). The CSV's own asbench/curated_allosteric/
`is_distal` count reproduces TASK-0331's independently-derived 49 PDBs
exactly. Join trusted.

**A finding from the validation step itself, not assumed going in:**
every single scoreable protein in both rounds has `is_distal == True` in
the CSV. This is not a join bug — `PIPELINE_DESIGN.md`'s own S5 cohort
definition already restricts to `is_distal` proteins only ("138
`is_distal` proteins (truth pocket ≥ 3 hops from the active site)").
So this analysis is a **within-distal-cohort** dose-response
(continuous distance, 2-13 hops / ~9-70 Å observed range), not a
distal-vs-proximal comparison — there is no proximal half to compare
against inside this cohort. Stated as a scope fact, not smoothed over.

### Result — the prediction holds, decisively

Per-protein pipeline hit rate (fraction of the 104 cells ranking the
drug pocket #1) vs. the drug pocket's own distance from the active site
(median hop / median Euclidean, from the CSV), Spearman rho:

| | pre-veto, held-out (n=64) | post-veto, held-out (n=44) | pre-veto, full (n=96) | post-veto, full (n=67) |
|---|---|---|---|---|
| pipeline hit-rate vs. distance | **−0.408** (p=8.1e-4) | **−0.614** (p=9.3e-6) | **−0.404** (p=4.4e-5) | **−0.479** (p=4.1e-5) |
| PASSer hit vs. distance (control) | +0.111 (p=0.38) | +0.207 (p=0.18) | +0.028 (p=0.78) | −0.059 (p=0.64) |
| random-arm-2 vs. distance | +0.307 (p=0.014) | +0.306 (p=0.043) | +0.323 (p=0.0013) | +0.425 (p=3.4e-4) |

(`median_euclid` gives the same sign and within 0.03 of every rho above
— full 4-metric table in `distance_anticorrelation_result.json`.)
Negative and significant at all 8 combinations tested (2 rounds × 2
cohorts × 2 metrics). Power stated before interpreting, per this
register's own standing rule since TASK-0313's addendum: minimum
detectable |rho| at p=0.05 is 0.20-0.30 at these n — every pipeline rho
clears that by 1.4-3x, not a borderline call.

**Specificity control clears**: PASSer — the ML-based arm-1 baseline,
with no explicit distance feature — shows no significant correlation
with distance in any of the 8 combinations (all p>0.17). This rules out
"distal truth pockets are just harder for everyone" as the explanation;
whatever is happening is specific to the CTQW-ranked arm, consistent
with that arm's score being the same proximity-tracking construction
TASK-0320 measured directly (rho=+0.808 to candidate-level proximity).
The random-order arm's own *positive* correlation with distance (larger
pockets tend to sit farther out, raising its size-driven hit chance)
runs opposite to the pipeline's — the pipeline is failing more on
distal truth even while its own random floor rises there, which argues
against this being some shared confound rather than a real
distance-specific mechanism failure.

### What this does not answer

TASK-0334's own Outcome asked for the distance from the active site to
(a) the pocket the pipeline actually ranks #1, not just the true
pocket — this would let a miss be characterized ("did it pick something
closer?"), not just counted. `pocket_distance.csv` carries only (active
site, annotated truth pocket) distances; it does not carry per-candidate
fpocket/PASSer-pocket geometry for the other pockets in each protein's
set, and computing that needs the raw PDB structures, ruled out by this
task's own Constraint ("no PDB refetch"). What is measured — hit-rate on
the truth pocket falling as that pocket's distance grows, with a
distance-agnostic baseline showing no such fall — is the operational,
testable form of the same mechanism, not a substitute for the literal
arm (a) measurement. Flagged as the natural next step if PDB-level
pocket coordinates are ever pulled for another reason.

### Landed

**New hypothesis `HYP-P25`** in `physics.md` (not a fold-in — this is a
genuinely different mechanism from [[HYP-P9]]'s "predictor gate does the
discriminating work" finding, which is about a different, reverse-seeded
and gated construction; HYP-P25 is about the forward, gate-independent
CTQW score itself). Cross-referenced from both directions. Ledger row
+ follow-up section added to `TASK_CLASSIFICATION_LEDGER.md`.
`INDEX.md` regenerated; `hyp_register_check.py` re-run clean (18/18
tests pass; new staleness flags on HYP-P8/P9/P21 are this same task's
own citations of hypotheses whose status block predates 2026-09-06 —
the known self-citation blind spot already documented in this ledger's
prior landing note, not a new issue).

**Incidental fix, same file TASK-0327 owns:** `reference_arms.py`'s
console-output string still said "excludes asbench/casbench" from the
pre-correction pass, even though `LEAKY_SOURCES` itself was already
correctly fixed to `{"asbench"}` — a stale print label, not a logic
bug (nothing computed from it), but misleading to read. Corrected to
name `{LEAKY_SOURCES}` directly and state casbench is PASSer's external
test set, not excluded. Flagged here rather than silently patched.

### Not done / out of scope

- Did not touch [[TASK-0332]] (unclaimed, different owner/scope) — this
  status update is the citable source for its submission-corrections
  pass, not an edit to that task file.
- Did not re-verify `pocket_distance.csv`'s own hop/Euclidean computation
  method against the collaborator's methodology — vendored and
  join-checked, not re-derived, consistent with [[TASK-0331]]'s own
  precedent for this file.
- Did not attempt arm (a)'s literal measurement (see above) — would
  require a PDB refetch, out of scope by this task's own Constraint.

## Correction (2026-09-07, [[TASK-0337]], Implementer A)

**Filed by Reviewer thread** (`.ai/reviews/2026-09-07/
REVIEW-2026-09-07-adversarial-submission-audit.md` §3.2), confirmed
independently before acting: `distance_anticorrelation.py` computes
Spearman rho over **structures**, never referencing the `cluster` column
present in `pocket_distance.csv` itself. The `is_distal` cohort this task
scored is concentrated — **`CAS0002` alone contributes 27-28 of the ~50-96
rows per combination** (20%+ of the full 138-row `is_distal` population).
"n=44" was 44 correlated structures, not 44 independent proteins, and
every p-value above is inflated by an unknown factor. [[TASK-0336]], run
the same day by the same owner, states in its own text that family-level
counting is mandatory and names this exact cluster — the trap was named
in one task and stepped into in the other. Not a nitpick: this register's
own stated identity is cluster-robust inference (Appendix A), and this
was the one recent result quoted against that standard.

**Planned Validation, run first**: re-ran `distance_anticorrelation.py`
unmodified — output byte-identical to the stored
`distance_anticorrelation_result.json` (`diff` empty). The row-level
numbers above are not in question, only how they were counted.

**Fix**: `cluster_robust_correction.py` (same directory) collapses each
cluster to its median (distance, pipeline hit-rate) before the Spearman,
then gets a p-value from a **cluster-level permutation test** (shuffle
which cluster's distance pairs with which cluster's hit-rate, B=10000,
[[TASK-0328]]'s own `det_seed` reused for deterministic seeding — its
`draw_pocket_block_null` itself was not reusable here, a different null
object: within-protein residue permutation vs. this task's between-cluster
correlation permutation, stated rather than forced) and a **cluster
bootstrap 95% CI** (resample clusters with replacement, B=10000) as a
second, independent check, since at n_clusters in the 20s-30s neither
alone is fully convincing. Applied to all 4 columns (pre/post-veto x
held-out/full) x 2 distance metrics = 8 combinations, and to both
specificity controls.

**Result — stated exactly as it landed, not rounded to the pre-stated
expectation:**

| combination | n_clusters | cluster rho | permutation p | bootstrap 95% CI |
|---|---|---|---|---|
| round1 pre-veto, full, hop | 55 | −0.363 | 0.0060 | [−0.594, −0.098] |
| round1 pre-veto, held-out, hop | 30 | −0.476 | 0.0105 | [−0.714, −0.145] |
| round1 pre-veto, full, euclid | 55 | −0.384 | 0.0043 | [−0.599, −0.129] |
| round1 pre-veto, held-out, euclid | 30 | −0.382 | 0.0376 | [−0.643, −0.037] |
| round2 post-veto, full, hop | 40 | −0.344 | 0.0314 | [−0.620, −0.002] |
| round2 post-veto, held-out, hop | 22 | −0.501 | 0.0189 | [−0.800, −0.060] |
| round2 post-veto, full, euclid | 40 | −0.412 | 0.0075 | [−0.666, −0.096] |
| **round2 post-veto, held-out, euclid** | **22** | **−0.414** | **0.0577** | **[−0.736, +0.059]** |

**7 of 8 combinations clear p<0.05 and a CI excluding zero. One does
not**: round 2 (post-veto), held-out cohort, `median_euclid` — the
smallest-n corner (22 clusters) on the weaker of the two distance metrics
— sits at p=0.058 with a CI that just crosses zero. Its sibling at the
same round/cohort (`median_hop`, same 22 clusters) clears cleanly
(p=0.019). **Read plainly: the mechanism survives cluster-robust
correction at 7 of 8 pre-registered combinations, including both metrics
on the largest (round 1) and one of two metrics on the smallest (round 2
held-out) cohort. It does not cleanly survive on the single
smallest-n/weakest-metric combination.** This is a real, disclosed
weakening from the row-level numbers (which cleared p<0.002 everywhere),
not a null result — the pre-registered expectation ("ρ≈−0.6 over ~30
clusters is still p≈10⁻³") was optimistic on the exact p-value but
directionally correct for 7/8 cells.

**Specificity controls, re-checked at cluster level**: PASSer-hit vs.
distance stays non-significant everywhere (rho −0.02 to +0.25, permutation
p 0.09-0.99 across all 8 combinations) — the control that matters most
(ruling out "distal proteins are just harder for everyone") is unweakened.
**The random-order arm's own positive correlation is weaker than reported
at row level**: cluster-level rho +0.11 to +0.23 (was +0.31 to +0.45
row-level), now non-significant everywhere at cluster level (permutation p
0.09-0.90). This softens, but does not reverse, the original "random arm
moves opposite to the pipeline" argument — the sign is still consistently
non-negative wherever measured, just not itself a cluster-robust finding.
Stated precisely rather than left as originally overclaimed.

**Files**: `cluster_robust_correction.py`,
`cluster_robust_correction_result.json` (same directory as the original
artifacts).

**Landed**: [[HYP-P25]]'s Status updated in the same commit with a dated
correction (not overwritten) — see that hypothesis's own text.
[[TASK-0332]] should cite the **cluster-collapsed** numbers as the
headline (rho ≈ −0.34 to −0.50, 7/8 combinations p<0.05) with the
held-out/post-veto/median_euclid caveat named, not the original row-level
numbers.
