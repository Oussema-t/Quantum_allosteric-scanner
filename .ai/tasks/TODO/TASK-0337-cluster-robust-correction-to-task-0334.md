# TASK-0337 — TASK-0334's anticorrelation is row-level, not cluster-level: correct it before it leads §2

- Status: TODO
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
