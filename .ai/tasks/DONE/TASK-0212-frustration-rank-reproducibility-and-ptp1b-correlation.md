# TASK-0212 Frustration-statistic reproducibility, then the PTP1B rank-correlation hypothesis (HYP-S6)

## Context

- ID: TASK-0212
- Title: gate the frustration statistic's reproducibility before ranking
  targets by it, then test HYP-S6 (frustration rank correlates with
  apo-only correlation-observable rank, PTP1B highest on both).
- Status: Done
- Owner: unclaimed
- Source: [[Q-0001]] (implementer/answered), amendment A3, declined for
  direct inclusion in [[TASK-0208]] and filed here instead — 2026-08-07.
- Priority: P2 — real scientific value (would give the register's one
  positive, `dcc_low` on PTP1B, a mechanism), but explicitly thin evidence
  at current N and gated on a robustness check that doesn't exist yet.
- Dependency: [[TASK-0208]] (Done) — supplies the raw per-target frustration
  numbers this task ranks.

## Why this matters

[[TASK-0208]] measured a coupling/frustration statistic
(single-vs-joint EvoEF2 ΔE of swapping a pocket window to its holo
rotamers) on 4 targets. The raw gap-over-sum-of-singles values were small
and mixed-sign on all 4 (KRAS_G12C ≈0.04%, CASPASE1 ≈-10% [anti-
frustration], PTP1B ≈16%, GLUCOKINASE ≈1.2% — see that task's Done
section for exact numbers) — none cleared the pre-registered 30%
frustration band, but the *relative ranking* (PTP1B highest) is exactly
what HYP-S6 predicts, since PTP1B is the one target where `dcc_low`
survives a corrected null ([[TASK-0201]], p=0.0027).

That ranking is suggestive but is exactly the kind of thin, easily-noisy
finding [[Q-0001]]'s own caveat warned about: at n=4 targets a rank
correlation is weak evidence on its own, and it is *worthless* if the
frustration statistic itself isn't stable under resampling — a rank built
from noise correlated against another rank built from noise is not a
finding, it's two coin flips agreeing once.

## Intent Contract

- Outcome: (a) a reproducibility measurement of [[TASK-0208]]'s
  single-vs-joint ΔE statistic (window resampling / leave-one-out /
  window-split, report variance across replicates), and, only if that
  passes a pre-registered stability bar, (b) the HYP-S6 rank-correlation
  test itself (frustration rank vs. `dcc_low`/mode-coparticipation/
  conformational-entropy rank, PTP1B predicted highest on both, direction
  fixed **before** this step runs).
- In Scope:
  - Design and pre-register the reproducibility bar **before** measuring
    it (this register's standing convention — do not skip it here either).
  - Extend [[TASK-0208]]'s target set if needed for a meaningful rank (n=4
    is thin; more usable apo/holo pairs from `targets.yaml` may exist).
  - If the reproducibility bar fails: report that as the finding and stop
    — do not run the rank correlation on a statistic shown to be unstable.
- Out Of Scope:
  - Re-deriving [[TASK-0208]]'s own attribution/reconstruction machinery —
    reuse it directly.
  - HYP-S4 (endpoint-vs-path coupling) and HYP-S5 (instance enrichment) —
    named in [[Q-0001]]'s Background as deliberately separate, larger
    proposals, not folded in here either.

## TODO

- [ ] Pre-register the reproducibility bar.
- [ ] Measure frustration-statistic stability across resampled windows.
- [ ] If stable: pre-register HYP-S6's rank-correlation test, then run it.
- [ ] If unstable: report and stop.

## Done

**2026-08-12, Architect — invalidated as filed, not executed.**
[[TASK-0208]]'s own recompute (Reviewer thread, 2026-08-07 — see that
task's "Recompute" section) re-keyed the `not_evaluable` guard this
task's premise depended on, and PTP1B's frustration gap — the +16.2%
this task exists to rank — was computed on `side_chain_explained =
0.078`, exactly the regime the corrected guard marks `not_evaluable`.
**There is no PTP1B frustration number left to test HYP-S6 against.**
Every other target has the same problem (KRAS_G12C 0.036, CASPASE1
0.043) — only GLUCOKINASE (0.463) still has an evaluable frustration
statistic, and it is a single point, not a rank.

Not re-scoped here — re-scoping requires a coupling statistic that works
when `side_chain_explained` is small, which [[TASK-0208]]'s own recompute
flags as **missing entirely** (its follow-up #2: "every construction
tried so far needs a meaningful side-chain component to compare against;
on these targets there isn't one... likely requires moving backbone and
side chain together"). That is new method development, not a
reproducibility check on an existing statistic — a different task, if
pursued. This task is closed without action rather than left open on a
premise that no longer exists.
