# TASK-0213 Re-run the coupled search at adequate n — decide TASK-0210's tentative OPEN

## Context

- ID: TASK-0213
- Title: re-run [[TASK-0210]]'s classical coupled backbone+rotamer search at a
  restart count adequate to distinguish "hard" from "under-searched", on the
  2 targets whose firewall check passes.
- Status: Done
- **Thread: Reviewer thread (Opus).**
- Owner: Implementer
- Claimed By: Reviewer-thread (Opus)
- Claimed At: 2026-08-13
- Source: [[TASK-0210]]'s own verdict — "tentatively OPEN, weakly supported,
  n=2 restarts, deliberately not handed to [[TASK-0183]]" — plus its disclosed
  finding that the real per-call cost is ~10× cheaper than the budget was
  sized for. Orchestrating user, 2026-08-13, extending the compute window.
- Priority: **P0 — the only OPEN item in the register, and its weakness is
  exactly the kind compute fixes.**
- Dependency: [[TASK-0210]] (Done — solver, objective, firewall, bars),
  [[TASK-0209]] (Done — target validity).

## Why this is a separate task and not an extension of TASK-0210

[[TASK-0210]] honored its pre-registered budget after seeing a negative
result, explicitly to avoid outcome-contingent budget inflation. Extending
that run *inside* the same task would be precisely the inflation it refused.
This task re-registers a budget from scratch, sized by a cost calibration on
this task's own candidate files, and commits to it before any outcome is
observed.

## Pre-Registered Protocol (fixed 2026-08-13, before any search run)

**Targets: KRAS_G12C and PTP1B only.** [[TASK-0209]] and [[TASK-0210]]'s own
firewall independently agree these are the only 2 of 7 targets where the
objective prefers the true holo. CASPASE1/GLUCOKINASE invert and no outcome
there is interpretable — running them would add cells, not information.

**Budget sizing — cost calibration, not outcome calibration.** [[TASK-0210]]'s
budget was sized on a stray file from an earlier task and proved ~10×
pessimistic. This task calibrates on its own real candidate structures: run
1 restart × 3 iterations per target, record seconds/iteration, then set

    ITERATIONS_TOTAL = floor(WALL_BUDGET_S / mean_seconds_per_iteration)

with `WALL_BUDGET_S = 7200` (2 h) split evenly across the 2 targets, and
allocate it as **RESTARTS × ITERATIONS with ITERATIONS = 25** (a longer anneal
than [[TASK-0210]]'s 10, since its own traces show the search still improving
at termination), RESTARTS taking the remainder. **Floor: RESTARTS >= 10.** If
the calibration implies fewer than 10 restarts at 25 iterations, reduce
ITERATIONS to 15 before reducing RESTARTS below 10 — restart diversity is what
n=2 lacked, and it is the quantity this task exists to raise.

Timing is not an outcome. The budget is fixed by the formula above and is
**not revised after any score is seen.**

**Success bar: unchanged from [[TASK-0210]], verbatim.** Either window
RMSD-to-holo reduced ≥50% vs. the native apo→holo window RMSD, **or** fpocket
`overlap >= 0.5 AND druggability >= 0.5`. Not re-tuned — a bar changed
alongside a budget increase makes the comparison meaningless.

**Verdict rule, fixed now:**

- **CLOSED** (search is not the bottleneck; the route is not a Phase-2
  candidate) if **either** target reaches the success bar on **≥2 restarts**.
- **OPEN** (search is genuinely hard at this scale) if **neither** target
  reaches the bar on **any** restart, at the full pre-registered budget.
- **INDETERMINATE** if exactly one restart on one target succeeds — a single
  success out of ≥20 is a lottery ticket, not a solved instance, and will be
  reported as such rather than rounded either way.

**Additionally recorded, whichever way it lands** (these cost nothing and are
what a follow-up would need): best-score trajectory per restart, the
distribution of best scores across restarts, and whether best score is still
improving at the final iteration (i.e. whether the anneal length, rather than
the restart count, is the binding constraint).

## Intent Contract

- Outcome: a decided verdict on [[TASK-0210]]'s tentative OPEN, at a restart
  count where "hard" and "under-searched" are distinguishable.
- Why required, not assumed: 0 successes out of 2 restarts is consistent with
  almost any difficulty. 0 out of ≥20 is not.
- Out Of Scope: changing the objective, the bars, the solver, or the targets;
  any quantum formulation; any claim of speedup.
- Constraints And Invariants: holo is the answer key and is never an input to
  the objective — [[TASK-0210]]'s firewall, inherited unchanged. Budget fixed
  before outcomes. Bars unchanged.
- Planned Validation: reproduce [[TASK-0210]]'s own firewall table on both
  targets before searching. If the objective no longer prefers the true holo,
  stop — the harness has drifted.

## TODO

- [x] Reproduce TASK-0210's firewall check on both targets (wiring check) — both pass.
- [x] Cost calibration: 1×3 per target — 2.15/2.26 s/iteration, recorded in `budget.json`.
- [x] Budget fixed by the formula: **65 restarts × 25 iterations/target**, recorded in `budget.json` before searching, not revised after.
- [x] Run the full budget — 130 restarts total, ~42 min/target.
- [x] Verdict by the pre-registered rule: **CLOSED**.
- [x] Trajectory diagnostics recorded (`trajectory_diagnostics.json`) — see below.

## Done

**2026-08-13, Reviewer thread (Opus).** `scripts/task0213_coupled_search_adequate_n.py`,
`results_task0213_coupled_search_adequate_n/{budget,results,verdict}.json`.

**Verdict: CLOSED — search is not the bottleneck. [[TASK-0210]]'s tentative
OPEN does not survive adequate n.**

Cost calibration on this task's own candidate files: **2.15-2.26 s/iteration**
(TASK-0210's 16.3 s/call sizing, measured on a stray file from an earlier
task, was ~7x pessimistic exactly as it suspected). Budget fixed by the
pre-registered formula at **65 restarts x 25 iterations per target**, ~60
min/target, and not revised after any score. Firewall reproduced on both
targets before searching.

| Target | successes / 65 restarts | rate |
|---|---|---|
| **KRAS_G12C** | **13** | **20%** |
| PTP1B | 0 | 0% |

**KRAS_G12C succeeds on 13 of 65 restarts where [[TASK-0210]]'s 2 restarts
found none.** At a 20% per-restart rate, 0/2 has a ~64% chance of occurring —
so TASK-0210's negative was fully consistent with an easy instance, which is
precisely the ambiguity this task existed to remove. Per the pre-registered
rule (CLOSED if either target reaches the bar on >=2 restarts), the route is
**closed**: on the one target where the objective is valid and the search
succeeds, coupled backbone+rotamer search is not hard.

**The per-target split is the more interesting result, and it is honest to
report it as unresolved.** KRAS 20% vs PTP1B 0/65 is a large, clean
difference on the register's only 2 valid targets — they disagree about the
central question. With n=2 valid instances there is no way to adjudicate
whether PTP1B is genuinely harder or merely different (its window, its
smaller active site, its own already-flagged label caveats). This is the
n=2 ceiling [[TASK-0209]] created, arriving in practice.

### Trajectory diagnostics — pre-registered "regardless of verdict", and they matter

| Target | best-score min / median / max | restarts still improving in final 20% | median iteration at which best was reached |
|---|---|---|---|
| KRAS_G12C | 0.333 / 0.555 / **0.882** | 25% | 15 of 25 |
| PTP1B | 0.033 / 0.293 / **0.397** | 12% | 9 of 25 |

Two readings, both load-bearing:

1. **The anneal length was not the binding constraint.** Only 12–25% of
   restarts were still improving in the final 20% of iterations, and the
   median restart reached its own best by iteration 9–15 of 25. The search
   converges inside the budget, so raising `ITERATIONS` further would buy
   little — restart count was the right dimension to increase, which is what
   this task did.
2. **PTP1B does not merely fail to succeed — its entire distribution is
   capped below the bar.** Max best-score across all 65 restarts is 0.397,
   below the 0.5 druggability bar and far below its own true holo value of
   0.757. KRAS_G12C's distribution (0.333–0.882) straddles the bar, exactly
   as a ~20% success rate implies. So PTP1B's 0/65 is not a near-miss and not
   an under-search artifact in either the restart or the iteration dimension.

Whether that reflects genuine difficulty on PTP1B or a mis-specified
objective/window there is **not decidable at n=2 valid targets** — stated as
unresolved rather than resolved in either direction.

**Consequence for the register: there is no OPEN route left.** Every
identified quantum-advantage route is now closed by measurement — single-
particle CTQW, coherence/interference, non-locality, interacting
multi-particle, backbone-only ENM search, residue-selection QUBO, optimal
control, fixed-backbone rotamer packing ([[TASK-0204]], complexity grounds),
and now coupled backbone+rotamer search.

**Consequence for [[TASK-0184]]: narrative framing (B) is no longer
available** — see that task's own narrative-decision record.
