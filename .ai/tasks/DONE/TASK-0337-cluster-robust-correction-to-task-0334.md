# TASK-0337 — TASK-0334's anticorrelation is row-level, not cluster-level: correct it before it leads §2

- Status: Done
- Owner: **Implementer A** (owns [[TASK-0334]])
- Priority: **BLOCKER — gates the v2 writeup; [[TASK-0332]] wants this as §2's second positive**
- Filed: 2026-09-07 by Reviewer thread (id via `claim.py reserve-next`)
- Source: `.ai/reviews/2026-09-07/REVIEW-2026-09-07-adversarial-submission-audit.md` §3.2
- Related: [[TASK-0334]], [[TASK-0336]], [[TASK-0332]], [[HYP-P25]], [[TASK-0301]]

## Confirmed, independently, before filing

- `distance_anticorrelation.py` contains **zero** references to `cluster` —
  `grep -c cluster` returns 0. The column is present in the very CSV it reads.
- The `is_distal` cohort is **138 rows across 86 clusters**.
- Concentration is severe: **`CAS0002` alone contributes 28 rows — 20% of the
  cohort in one protein family**; `CAS0001` adds 8, `CAS0040` 6.

So ρ = −0.614, p = 9.3×10⁻⁶ "at n = 44" is over 44 **correlated structures**, not
44 independent proteins. The effective n is materially smaller and the p-value is
inflated by an unknown factor.

## Why this is a blocker and not a nitpick

This register's stated identity is cluster-robust inference — Appendix A:
*"exact cluster-level permutation, after four selection procedures in our own
register died of pseudo-replication."* [[TASK-0336]], **run the same day by the
same owner**, states in its own text that family-level counting is mandatory and
names `CAS0002 = 28` explicitly. The trap was named in one task and stepped into
in the other.

§7 invites a referee to read this register. A §2 headline that violates the
discipline §5 is built on costs more than the claim earns.

## Intent Contract

- Outcome: cluster-collapsed ρ and a cluster-level p-value (cluster bootstrap or
  cluster permutation — reuse [[TASK-0328]]'s machinery rather than writing a
  third one). **Report the cluster-collapsed number as the headline and the
  row-level one as a footnote**, not the reverse.
- Apply to all four columns [[TASK-0334]] reports (pre/post-veto × held-out/full),
  and to both specificity controls — the PASSer control and the random arm are
  only meaningful if computed the same way as the thing they control for.
- Expected to survive: ρ ≈ −0.6 over ~30 clusters is still p ≈ 10⁻³. **State the
  expectation before running it**, and report the result whichever way it lands.
- Constraints And Invariants:
  - Append to [[TASK-0334]] under a dated `## Correction` heading — no silent
    overwrite, per this register's own convention.
  - `HYP-P25` was minted on the row-level number; update its Status line in the
    same commit or it becomes a second write-mostly entry ([[TASK-0321]]).
  - If the effect does **not** survive, [[TASK-0332]]'s §2 plan loses its second
    positive and the brief must be updated before drafting — say so immediately
    rather than at the end of the task.
- Planned Validation: reproduce [[TASK-0334]]'s own row-level ρ first, from the
  same join, before trusting any cluster-collapsed number derived from it.

## Note

The mechanism is very likely real — the specificity controls (PASSer flat at
p > 0.17 across 8 combinations, random arm correlating *positively*) are what
make it persuasive, and neither is affected by the clustering error. This task
fixes how the evidence is counted, not whether it exists.

## Done

**2026-09-07, Implementer A.** Full correction appended to
[[TASK-0334]]'s own file under a dated `## Correction` heading (see that
task for the complete method, table, and result — not duplicated here per
this register's own "append, don't fork the record" convention). Summary:

- **Planned Validation passed first**: re-ran `distance_anticorrelation.py`
  unmodified — byte-identical to its stored result. The row-level numbers
  were never in question, only the counting.
- **Fix**: `cluster_robust_correction.py` (same directory as TASK-0334's
  artifacts) collapses each cluster to its median before the Spearman,
  reports a cluster-permutation p (B=10000, [[TASK-0328]]'s `det_seed`
  reused for the seeding discipline — its `draw_pocket_block_null` itself
  is a different null object, a within-protein residue permutation, not
  reusable for this between-cluster correlation test; stated rather than
  forced) and a cluster-bootstrap 95% CI (B=10000), for all 4 columns × 2
  distance metrics, plus both specificity controls.
- **Result**: 7 of 8 pre-registered combinations survive (cluster rho
  −0.34 to −0.50, n_clusters 22-55, permutation p 0.004-0.038, CI
  excluding zero). One — round 2 (post-veto), held-out cohort,
  `median_euclid`, the smallest-n (22 clusters) and weaker-of-two-metrics
  corner — is borderline (p=0.0577, CI [−0.736, +0.059]); its `median_hop`
  sibling at the identical n=22 clusters clears (p=0.019). Reported
  exactly as it landed, not rounded toward the pre-stated expectation.
- **PASSer specificity control unweakened** (non-significant everywhere,
  p=0.09-0.99). **Random-arm control weakens** from row-level-significant
  to cluster-level-non-significant (rho +0.11 to +0.23, p=0.09-0.90) —
  softened, not reversed; stated precisely rather than left overclaimed.
- **[[HYP-P25]]'s Status updated in the same commit** with a dated
  correction paragraph (not overwritten, per this register's own
  convention) — see that hypothesis's own text.
- **Consequence for [[TASK-0332]]**: cite the cluster-collapsed numbers
  (7/8 combinations clear, one borderline) as the headline, not the
  original row-level "every one of 8 combinations" claim. The mechanism
  is not lost — it survives at the primary (round-1, both metrics; round-2
  full-cohort) combinations decisively — but the strongest possible
  framing ("clears everywhere") is no longer accurate and should not be
  used in the §2 draft.

### Not done / explicitly out of scope

- Did not re-verify the review's own reported full-138-row concentration
  figures (`CAS0002=28` etc.) against the actual per-combination joined
  subsets from scratch beyond what the correction script itself reports
  (`top3_cluster_sizes`, which independently confirms `CAS0002` as the
  dominant cluster in every combination, 21-27 rows depending on
  round/cohort) — consistent with, not identical to, the review's
  full-population count, as expected since this task's subsets are
  strictly smaller than the full 138-row `is_distal` population.
- Did not attempt a third, more exact method (e.g. an exact permutation
  enumeration rather than Monte Carlo) — B=10000 Monte Carlo permutation/
  bootstrap is judged sufficient precision at n_clusters in the 20s-50s;
  not pursued further given the borderline case's own p (0.058) is not
  close enough to a Monte Carlo B=10000 resolution boundary to be an
  artifact of the sampling itself.

**Files**: `__WORK_IN_PROGRESS__/results/tasks/0334_ctqw_proximity_anticorrelation/
{cluster_robust_correction.py,cluster_robust_correction_result.json}`.
