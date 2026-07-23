# TASK-0134 CPU-time re-verification of the `time_averaged_ctqw` infeasibility claim, plus a reusable long-job convention

## Context

- ID: TASK-0134
- Title: [[TASK-0110]]'s "a single `time_averaged_ctqw` call did not
  return after 2+ hours" claim (cited downstream by
  `.ai/invariants/INV-0005-propagator-time-parameters.md`, [[SEAM-0012]],
  and [[TASK-0130]]) was corroborated by process state (`R`, "genuinely
  computing, not hung") at the point it was killed, but not by CPU-time
  consumed over the interval. Process state at one checkpoint proves
  active scheduling at that moment; it does not prove continuous
  execution for the full elapsed wall-clock duration. Re-verify with
  real CPU-time instrumentation, and separately, propose a reusable
  convention for how this project's agent threads should run and
  monitor genuinely long compute jobs generally.
- Status: Done
- Owner: Implementer / Toolsmith (two distinct pieces, see In Scope —
  claim both or split, state which in Done)
- Claimed By: Implementer D (this thread)
- Claimed At: 2026-07-22
- Source: raised directly by the orchestrating user, 2026-07-18 — "I am
  unsure if the possibility of a 'computer went to sleep mode, was woken
  up after 1.5hrs, restarted computing' option was ruled out... this kind
  of risk — not properly assuring how much compute IS being consumed —
  is the ether of this project." Filed as [[P-0005]]
  (`.ai/memory/shared/pitfalls.md`) and an update to [[SEAM-0012]].
- Priority: **P2, downgraded 2026-07-19 — Part 1 is now largely moot.**
  [[TASK-0130]] replaced `time_averaged_ctqw`'s finite-time approximation
  with the exact closed form for every headline call path — the specific
  `t_max`/`n_steps` combination that produced the original "2+ hours,
  did not return" observation is no longer how this project computes
  this quantity, so re-verifying that exact historical multiplier has
  materially less value than it did when this task was filed (nobody is
  going to run that code path again in the way that produced the
  original number). **Part 2 (a reusable long-job/background-monitoring
  convention, including the HITL hand-off option) remains fully valid
  and independent of this** — general infrastructure, not tied to the
  specific claim that motivated it. Whoever picks this up should treat
  Part 1 as optional/historical-record-only and Part 2 as the actual
  remaining deliverable.

## Intent Contract

- Outcome, part 1 (re-verification): re-run the specific call TASK-0110
  made (real `time_averaged_ctqw` at the AAKV-prescribed `t_max`/
  `n_steps` on real KRAS_G12C data) with CPU-time logged continuously
  across the interval (`resource.getrusage(RUSAGE_SELF)` sampled
  periodically, or wrap with `/usr/bin/time -v` if invoked as a
  subprocess) — not just a single process-state check at kill time.
  Report wall-clock elapsed *and* CPU-seconds consumed side by side. If
  CPU-time tracks wall-clock closely (no long gaps), the original claim
  is corroborated as stated. If there's a large gap (CPU-time much less
  than wall-clock), that is direct evidence of contention/suspension
  during the run, and the "2+ hours" figure should be corrected
  wherever it's cited (additively, per this project's no-silent-
  overwrite convention) to state the real CPU cost instead.
- Outcome, part 2 (convention): propose and document a reusable pattern
  for this project's agent threads to run compute expected to exceed a
  practical in-session attention span (tens of minutes to hours) —
  default to detached/background execution with periodic CPU-time
  logging to a file the thread (or a later thread, or the orchestrating
  user) can check, rather than either (a) blocking synchronously in one
  session and declaring infeasibility when the session's own patience
  runs out, or (b) not attempting a long job at all because no thread
  considered handing it off. Explicitly include the human-in-the-loop
  option the user raised — a job expected to run past a session's
  practical span can be started and left running with instructions for
  a human to check back, not only auto-monitored by another agent
  thread. Where this belongs (a `.ai/tools/` wrapper, a documented
  pattern in `.ai/reference/OPERATION_PROTOCOL.md`, or elsewhere) is
  this task's own call — state the choice and why in Done.
- In Scope:
  - The CPU-time re-measurement itself (part 1) — real, on real data,
    not a synthetic proxy.
  - Correcting any downstream citation of "2+ hours"/the specific
    multipliers if the re-measurement finds a material gap between
    wall-clock and CPU-time.
  - A documented convention (part 2) — does not need new tooling built
    from scratch if an adequate pattern already exists in this session's
    own history (e.g. this Architect/Planner thread's own use of
    `run_in_background` for a full test-suite run, checked for
    concurrent contention via `ps aux` first) — capturing and
    generalizing an already-demonstrated good practice is in scope, not
    only building something new.
- Out Of Scope:
  - Re-litigating [[TASK-0130]]'s own recommendation (promote the
    closed-form limit) — unaffected by this task's outcome either way.
  - Re-measuring every other timing claim in this project's history
    (TASK-0105's ENAQT per-call costs, TASK-0068's NISQ Trotter-step
    timing, etc.) — flag them as candidates for the same scrutiny in
    Done if this task's own finding suggests they're at risk, but do not
    re-run all of them here.
- Constraints And Invariants: the re-measurement must run long enough to
  either reproduce the original non-completion or reach a real
  conclusion — do not truncate early and call the question re-opened
  rather than answered.
- Planned Validation: the CPU-time-vs-wall-clock comparison itself is
  this task's primary validation artifact; the convention (part 2)
  is validated by being concrete enough that a future thread could
  actually follow it without re-deriving the pattern from scratch.

## In Progress

None

## TODO

- [x] Re-run TASK-0110's specific infeasibility-triggering call with
      continuous CPU-time logging, real data.
- [x] Report wall-clock vs. CPU-time side by side; state whether the
      original "2+ hours" claim is corroborated or was inflated.
- [x] If inflated: correct `INV-0005-propagator-time-parameters.md`,
      `SEAM-0012`, and any task Done sections citing the specific
      multipliers, additively.
- [x] Document a reusable long-job/background-monitoring convention,
      including the HITL hand-off option, in whatever location is the
      right fit (state the choice in Done).
- [x] Flag (not re-run) any other timing-based feasibility claims in
      this project's history that share the same unverified-CPU-time
      risk.

## Dependency

- [[TASK-0110]] (Done) — the specific claim this task re-verifies.
- [[TASK-0111]] (Done) — the prior, independently-confirmed instance of
  the same confound class (contention inflating a different timing
  measurement in this same sandbox) — reuse its own "controlled,
  same-moment" measurement discipline as a template.
- Cross-referenced: [[P-0005]] (`.ai/memory/shared/pitfalls.md`),
  [[SEAM-0012]] (`.ai/seams/`).

## Open Questions

- Whether this environment is even capable of OS-level suspend/sleep at
  all (the user's specific hypothesized mechanism) — genuinely unknown;
  this task's own re-measurement doesn't need to answer that directly
  (CPU-time-vs-wall-clock is diagnostic regardless of which specific
  mechanism, sleep or contention, would explain a gap if one is found).

## Done

**2026-07-22, Implementer D (this thread).** Both pieces claimed and
completed by the same thread (not split).

### Part 1 — CPU-time re-verification: corroborated, not inflated

Re-ran TASK-0110's specific call (real KRAS_G12C, `H_new`, AAKV-prescribed
`t_max`/`n_steps`) with continuous instrumentation instead of a single
process-state check. New `scripts/task0134_cpu_time_reverification.py`,
using `allostery.runlog.RunLogger` (TASK-0135) sampled every 2000 steps,
BLAS threads capped to 4 (matching the original script's own environment).
**Real complication found before the run even started**: the *same* AAKV
formula on the *same* target now prescribes `t_max=1.26e6`/
`n_steps=877,811` — TASK-0110's own original run needed `t_max=4.82e6`/
`n_steps~1.3e7`. `H_new`'s spectrum shifted after [[TASK-0121]]'s potential
renormalization (landed 2026-07-18, one day after TASK-0110's
measurement), so the literal historical scenario is no longer
reproducible — this task ran the full *current* prescription instead
(877,811 steps end to end, not truncated), which is enough to answer the
actual question (does CPU-time track wall-clock).

**Result: completed in 950.2s (~15.8 min), full prescription, not killed
early.** 438 samples across the whole run: `cpu_elapsed_s/wall_elapsed_s`
held at **4.05 ± 0.035** throughout (min 3.958, max 4.157) — matching the
4-thread cap almost exactly, no drops anywhere in the sequence. This is
clean evidence of continuous execution for the *entire* interval, not
just at one checkpoint — directly closes the gap [[P-0005]] named.
Extrapolating this rate to the *original* 1.3e7-step scenario gives ~3.9
CPU-wall-clock hours, consistent with (and if anything longer than)
"still computing after 2+ hours" — **the original claim is corroborated,
not inflated**; no downstream citation needed correcting for accuracy,
only for the separate parameter-drift fact (below).

**A real, independent methodological finding, found live while scoping
the environment**: an uncapped calibration run (before the thread cap
was applied) measured CPU-time at **~16x** wall-clock on this 16-core
machine — multithreaded BLAS parallelism, not contention. This is easy
to get backwards (a naive reading of "CPU-time way more than wall-clock"
looks alarming) — the actual diagnostic for contention/suspension is the
**stability** of the ratio across successive samples, not its absolute
magnitude, which is exactly what the 438-sample trace above checks.
Documented prominently in `LONG_JOB_CONVENTION.md` so this doesn't need
re-deriving next time.

**Downstream citations updated additively** (not corrections — the claim
held; these add the corroboration + the parameter-drift fact as new,
dated layers): `.ai/invariants/INV-0005-propagator-time-parameters.md`,
`.ai/seams/SEAM-0012-propagator-convergence-vs-real-defaults.md`,
`.ai/memory/shared/pitfalls.md`'s `P-0005` entry.

### Part 2 — Long-job convention

New `.ai/reference/LONG_JOB_CONVENTION.md`, cross-linked from
`.ai/reference/IMPLEMENTER_SPINUP_BRIEF.md` (§10, every implementer
thread already reads this before its first commit) and
`.ai/reference/OPERATION_PROTOCOL.md` (its own Implementation/Local
Validation steps). **Implementer's-call on placement**: a `.ai/reference/`
doc, not a new `.ai/tools/` wrapper — no new tooling was needed
(`allostery.runlog.RunLogger` from TASK-0135 and this environment's own
`run_in_background`/`ScheduleWakeup` primitives are already adequate);
this generalizes an already-demonstrated pattern (this Architect/Planner
thread's own prior use of `run_in_background` for a full test-suite run,
checked for concurrent contention via `ps aux` first) into a reusable
convention, per this task's own In Scope allowance to capture existing
good practice rather than build something new.

Covers: the ~10-15 minute threshold for when to stop blocking
synchronously; two distinct detachment mechanisms for two distinct time
horizons (harness-tracked `run_in_background` for session-span jobs vs.
OS-level `nohup`/`disown`/`tmux` for jobs expected to outlast the
session); monitor-by-tail-not-poll; the CPU/wall ratio-stability
diagnostic from Part 1 above; and an explicit HITL hand-off section
(what "done"/"healthy"/"stalled" look like in a `RunLogger` trace, and
where to post checkback instructions durably — `.ai/COMMON.md`'s Active
Work Registry or a `results_taskNNNN/HITL_CHECKBACK.md` file, not only a
chat transcript).

### Other timing-based feasibility claims at similar risk (flagged, not re-run)

Per this task's own Out Of Scope. Both share the exact P-0005 shape
(a wall-clock-only measurement cited as a feasibility/cost claim,
no CPU-time or ratio-stability check):
- **TASK-0105**'s ENAQT per-gamma wall-clock figures (`enaqt_gamma_sweep.py`'s
  own module docstring: "N=169 (KRAS_G12C) ~11s, N=451 (BCR_ABL1) ~161s"
  per `haken_strobl` call at `t=25`) — used to justify running a reduced
  grid on BCR_ABL1 and skipping CARDIAC_MYOSIN's full sweep entirely.
  If contention inflated these, the "infeasible" call on CARDIAC_MYOSIN
  could be reassessed — not verified here.
- **TASK-0068**'s NISQ Trotter-step timing (the "a literal-estimate run
  was killed after 69 CPU-minutes" figure cited in `RESULTS.md`'s open-
  questions row 8) — same shape, a wall-clock kill-point cited as
  evidence of infeasibility, not CPU-time-verified.

Neither re-measured here, per this task's own explicit Out Of Scope
("flag them... do not re-run all of them here").

Full regression suite not re-run as part of this task (no `select.py`/
production-path code was changed — only `.ai/` reference docs and one
new, standalone script/RunLogger consumer); `scripts/
task0134_cpu_time_reverification.py` itself ran to completion
successfully, which is this task's own real validation artifact.
