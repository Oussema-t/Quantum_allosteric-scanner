# TASK-0293 — LOTO the `druggability / size` ranking before it is believed

- Status: TODO
- Assignee: unassigned
- Priority: High — could raise [[TASK-0282]]'s published ceiling from 0.165 to ~0.265, or expose another in-sample mirage
- Filed: 2026-08-29 by Reviewer thread (follow-up to [[TASK-0292]] Part D)
- Related: [[TASK-0292]], [[TASK-0282]], [[TASK-0287]], [[TASK-0249]]

## Why

[[TASK-0292]] Part C established that [[TASK-0282]]'s ceiling rule loses
because fpocket druggability tracks pocket size (within-target
rho=+0.239, p=0.0007) and so selects candidates **1.7× larger** than the
oracle's pick (17.6 vs 10.2 residues). Nine of twenty frozen targets score
exactly 0.000 under the rule while having a non-zero oracle.

Ranking by `druggability / size` instead gains **+0.100 mean EH
(0.1649 → 0.2649)** — but **in-sample on the frozen 20, and not
significant (Wilcoxon p=0.157)**.

## The specific trap this task exists to avoid

This register has already produced exactly this pattern once: an
in-sample sweep over 28 configurations reported a best of **0.267**, and
the subsequent LOTO run showed the winning family **never won a single
fold**. The in-sample number here (0.2649) is suspiciously close to that
one. Treat it as a mirage until proven otherwise.

## Scope

- [ ] Run leave-one-target-out over the frozen set with
      `druggability / size` as a **pre-specified single arm** — not as one
      entry in a fresh sweep. The point is to test one hypothesis, not to
      find a winner.
- [ ] Report per-fold EH, not just the mean, and state in how many folds
      it beats the published `druggability` rule.
- [ ] Apply the same cluster-robust treatment [[TASK-0261]] established
      (the 20 frozen rows are not 20 independent structures).
- [ ] Also LOTO the published rule on the same folds so the comparison is
      like-for-like.

## Constraints

- **One arm.** Do not sweep a family of `druggability / size^k` or add
  variants mid-run. If `druggability / size` fails, report that it failed.
- Do not merge fpocket candidates ([[TASK-0292]] Part B: merging hurts at
  every criterion tested).
- If it wins, the [[TASK-0282]] ceiling figure and every downstream claim
  quoting 0.165 must be updated together, including the collaborator
  brief and [[TASK-0184]].

## Note

Either outcome is publishable. A confirmed 0.265 strengthens the "simple
classical heuristics construct a ceiling above CTQW" framing. A failure
is a second, independent demonstration that this register's in-sample
pocket-selection gains do not survive held-out evaluation — which is
itself a finding worth stating plainly in the write-up.
