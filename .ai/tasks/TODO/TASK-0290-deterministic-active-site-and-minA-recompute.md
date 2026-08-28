# TASK-0290 — Make `detect_active_site` deterministic and recompute every `min_A`

- Status: TODO — **scheduled by the repo owner for Sunday 2026-08-30**
- Assignee: unassigned
- Priority: **High — last caveat on [[TASK-0288]] Finding F, which is headed for the Phase 1 write-up**
- Filed: 2026-08-29 by Reviewer thread (user-directed: "let us do the recompute on Sunday")
- Related: [[TASK-0289]], [[TASK-0288]], [[TASK-0258]], [[TASK-0253]], [[TASK-0184]]

## Why

[[TASK-0289]] measured the blast radius of the `detect_active_site`
non-determinism and **rejected** the hypothesis that it manufactured
[[TASK-0288]] Finding F's contact spike. What it did **not** do is
recompute `min_A` under a deterministic active site — every `min_A` in
the register is still the value produced by whichever fallback tier
answered on the run that wrote it.

Finding F (**~32% of the benchmark has its "allosteric" pocket covalently
bonded to the active site**) is the strongest benchmark-validity result
this register holds and is headed for the Phase 1 submission. It should
go in **without an asterisk**.

## Scope

- [ ] **Fix `backend/active_site.py:174-187`.** Two separate defects in
      one block:
      1. **Non-determinism** — resolve once, then cache to disk keyed by
         `(pdb_id, chain)`; network only on a cache miss.
      2. **Silent downgrade** — the bare `except Exception` cannot
         distinguish "UniProt has no annotation for this entry" (a real
         negative; fall through to the next tier) from "the UniProt call
         failed" (an error; retry, then raise). Separate the two.
- [ ] Propagate the returned `source` through
      `task0242_two_stage_dryrun.prep()` — it is currently discarded —
      and into every result JSON, so provenance is auditable after the
      fact rather than re-measured each time someone doubts a number.
- [ ] Recompute `min_A` for all 33 taxonomy targets under the fixed path.
      **Diff against the committed taxonomy and report every target that
      moves, including ones that move in our favour.**
- [ ] Re-run [[TASK-0288]] Finding F on the corrected values: the 9/28
      spike count, the binomial p, and the sequence-gap check.
- [ ] Re-check the three targets [[TASK-0289]] found unstable —
      `DHPS_GC7`, `NAMPT_NPA1R`, `HIV1_RT` — and confirm `HIV1_RT` can no
      longer return an empty active site ([[TASK-0253]]'s failure mode,
      observed live in the [[TASK-0289]] sweep).

## Constraints

- **Do not pin to whichever tier reproduces the currently committed
  numbers.** The deliverable is a defensible recorded provenance per
  target, not agreement with values that may themselves be artifacts.
- If a target's `min_A` moves across the 1.5 Å spike boundary or the
  near/far boundary, that is a **result to report**, not a regression to
  suppress.
- Findings A–E of [[TASK-0288]] are **not** gated on this: they test
  scale-free landscape shape against scale-free position within each
  protein's own geometry and do not depend on the absolute active-site
  definition. Do not re-open them.

## Note

Worth grepping the scientific path for any remaining bare
`except Exception` that can silently substitute one input for another.
This is the second instance of that pattern ([[TASK-0253]] was the
first) and Phase 2 will add more network-backed inputs.
